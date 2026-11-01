"""mhd_kanal.py — MHD Stufe 2: Rechteckkanal mit Seitenwänden, Lorentzkraft mit elektrischem Potential in FluidX3D.

  .venv/bin/python -m stellarator.mhd_kanal

Physik (induktionsfrei, kleine magnetische Reynoldszahl): j = sigma(-grad phi + u x B), div j = 0
  ->  Laplace phi = div(u x B),  f = j x B / rho.
In einem Kanal mit Seitenwänden schließen sich die Ströme über die Wände bzw. die Randschichten; ohne phi
(Stufe 1) würde die Bremskraft stark überschätzt. FluidX3D-Kopie mit Schalter MHD_POT (Diffs in fluidx3d/):
phi wird mit Jacobi-Schritten auf der GPU parallel zur Strömung gelöst (FX_MHD_JACOBI Doppelschritte je Zeitschritt).

Vergleich: eigener, unabhängiger 2D-Löser für die ausgebildete Kanalströmung in der Formulierung mit dem
induzierten Magnetfeld b (Shercliff 1953, Hunt 1965), dimensionslos mit Länge a (halbe Weite in B-Richtung):
    lap u + Ha db/dy = -1,    lap b + Ha du/dy = 0,    u = 0 an allen Wänden
    isolierende Wand: b = 0;   ideal leitende Hartmann-Wand (Normale parallel B): db/dn = 0  (Hunt)
FluidX3D: u = fx a^2/nu * U(y/a, z/a).
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

ROOT = Path(__file__).resolve().parents[1]
FX = Path(os.environ.get("FLUIDX3D_MHD", "fluidx3d_mhd"))   # Ordner der gepatchten FluidX3D-Kopie
AUS = ROOT / "sim" / "mhd" / "kanal"
NU = 0.1
U_ZIEL = 0.03


def referenz(Ha, r=1.0, wand=0, n=120):
    """Ausgebildete Strömung im Kanal |y|<=1 (B in y), |z|<=r. Zellmittelpunkte, Wände auf den Zellrändern."""
    ny, nz = 2 * n, int(round(2 * n * r))
    h = 2.0 / ny
    N = ny * nz
    idx = lambda i, k: i + ny * k
    rows, cols, vals = [], [], []
    rhs = np.zeros(2 * N)

    def add(r_, c_, v):
        rows.append(r_); cols.append(c_); vals.append(v)

    for k in range(nz):
        for i in range(ny):
            p = idx(i, k)
            for feld in (0, 1):            # 0: u, 1: b
                zeile = feld * N + p
                diag = 0.0
                for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ii, kk = i + di, k + dk
                    if 0 <= ii < ny and 0 <= kk < nz:
                        add(zeile, feld * N + idx(ii, kk), 1 / h ** 2); diag -= 1 / h ** 2
                    else:                   # Geisterzelle: Dirichlet -> -wert, Neumann -> +wert
                        neumann = feld == 1 and wand == 1 and di != 0
                        diag += ((1 if neumann else -1) - 1) / h ** 2
                add(zeile, zeile, diag)
                # Kopplung Ha d(anderes Feld)/dy, zentrale Differenz mit denselben Geisterzellen
                anders = 1 - feld
                for di, s in ((1, 1), (-1, -1)):
                    ii = i + di
                    if 0 <= ii < ny:
                        add(zeile, anders * N + idx(ii, k), s * Ha / (2 * h))
                    else:
                        neumann = anders == 1 and wand == 1
                        add(zeile, anders * N + p, (1 if neumann else -1) * s * Ha / (2 * h))
                if feld == 0:
                    rhs[zeile] = -1.0
    A = sp.csr_matrix((vals, (rows, cols)), shape=(2 * N, 2 * N))
    x = spl.spsolve(A.tocsc(), rhs)
    U = x[:N].reshape(nz, ny).T            # U[i(y), k(z)]
    y = -1 + h * (np.arange(ny) + 0.5); z = -r + h * (np.arange(nz) + 0.5)
    return y, z, U


def ref_auf(Ha, r, wand, eta, zeta, n=120):
    from scipy.interpolate import RegularGridInterpolator
    y, z, U = referenz(Ha, r, wand, n)
    # Wandwerte (U = 0) ergänzen, damit auch randnahe Punkte interpoliert werden
    yy = np.concatenate(([-1], y, [1])); zz = np.concatenate(([-r], z, [r]))
    UU = np.zeros((len(yy), len(zz))); UU[1:-1, 1:-1] = U
    f = RegularGridInterpolator((yy, zz), UU)
    return f(np.column_stack([eta.ravel(), zeta.ravel()])).reshape(eta.shape), U.max(), U.mean()


def lauf(Ha, a, wand=0, r=1.0, jacobi=20, faktor=12):
    b = int(round(a * r))
    Ny, Nz = 2 * a + 2, 2 * b + 2
    K = Ha ** 2 * NU / a ** 2
    _, umax_ref, _ = ref_auf(Ha, r, wand, np.zeros(1), np.zeros(1), n=60)
    fx = U_ZIEL * NU / (a ** 2 * umax_ref)
    schritte = int(faktor * a ** 2 / NU) + 2000
    ordner = AUS / f"ha{Ha}_a{a}_w{wand}_r{r:g}"; ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "fall.txt").write_text(f"{ordner} {Ny} {NU} {fx:.9e} {schritte} {max(schritte // 40, 100)} {Nz} 1\n")
    env = dict(os.environ, MHD_FALL=str(ordner / "fall.txt"), FX_MHD_K=f"{K:.9e}", FX_MHD_B="0.0f, 1.0f, 0.0f",
               FX_MHD_WAND=str(wand), FX_MHD_JACOBI=str(jacobi))
    if not (os.environ.get("MHD_NUR_BILD") and (ordner / "profil2d.txt").exists()):   # nur neu zeichnen
        r_ = subprocess.run([str(FX / "bin" / "FluidX3D")], cwd=FX, env=env, capture_output=True, text=True, timeout=7200)
        (ordner / "fluidx3d.log").write_text(r_.stdout + r_.stderr)
    d = np.loadtxt(ordner / "profil2d.txt")
    yi, zi, ux = d[:, 0].astype(int), d[:, 1].astype(int), d[:, 2]
    F = np.zeros((Ny, Nz)); F[yi, zi] = ux
    F = F[1:-1, 1:-1]                                     # nur Fluidzellen
    eta = ((np.arange(1, Ny - 1) - (Ny - 1) / 2) / a)[:, None] * np.ones((1, Nz - 2))
    zeta = np.ones((Ny - 2, 1)) * ((np.arange(1, Nz - 1) - (Nz - 1) / 2) / a)[None, :]
    Ur, umax_ref, umean_ref = ref_auf(Ha, r, wand, eta, zeta)
    ua = fx * a ** 2 / NU * Ur
    fehler = float(np.sqrt(np.mean((F - ua) ** 2)) / ua.max())
    q_lbm = float(F.mean()); q_ref = float(ua.mean())
    stat = np.loadtxt(ordner / "stat.txt")
    konv = float(abs(stat[-1, 1] - stat[-2, 1]) / abs(stat[-1, 1]))
    return dict(Ha=Ha, a=a, wand=wand, r=r, K=K, fx=fx, schritte=schritte, fehler=fehler, q_lbm=q_lbm, q_ref=q_ref,
                q_fehler=q_lbm / q_ref - 1, konv=konv, F=F, ua=ua, eta=eta, zeta=zeta)


def bild(erg, gitter, sprache):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    de = sprache == "de"
    fig = plt.figure(figsize=(14, 9.5), dpi=120)
    gs = fig.add_gridspec(2, 3)
    farben = ["#52514e", "#2a78d6", "#1baf7a", "#eda100", "#eb6834"]
    # oben links / mitte: Profile entlang B (z = 0) und quer (y = 0), isolierende Wände
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    iso = [e for e in erg if e["wand"] == 0]
    for e, c in zip(iso, farben):
        F, ua = e["F"], e["ua"]; s = ua.max()
        kz = F.shape[1] // 2; ky = F.shape[0] // 2
        ax1.plot(e["eta"][:, kz], ua[:, kz] / s, color=c, lw=1.4)
        ax1.plot(e["eta"][::3, kz], F[::3, kz] / s, "o", ms=3, color=c,
                 label=f"Ha = {e['Ha']}: {100*e['fehler']:.1f} %")
        ax2.plot(e["zeta"][ky, :], ua[ky, :] / s, color=c, lw=1.4)
        ax2.plot(e["zeta"][ky, ::3], F[ky, ::3] / s, "o", ms=3, color=c)
    ax1.set_xlabel(("y/a (entlang B, Hartmann-Wände bei ±1)" if de else "y/a (along B, Hartmann walls at ±1)"))
    ax2.set_xlabel(("z/a (quer zu B, Seitenwände bei ±1)" if de else "z/a (across B, side walls at ±1)"))
    ax1.set_ylabel("u / u_max")
    ax1.set_title(("Isolierende Wände (Shercliff): Profil entlang B" if de else "Insulating walls (Shercliff): profile along B"), fontsize=10)
    ax2.set_title(("… und quer zu B (Seitenschichten)" if de else "… and across B (side layers)"), fontsize=10)
    ax1.legend(frameon=False, fontsize=8, title=("Punkte FluidX3D, Linien Referenz" if de else "dots FluidX3D, lines reference"),
               title_fontsize=8)
    # oben rechts: Hunt
    ax3 = fig.add_subplot(gs[0, 2])
    hunt = [e for e in erg if e["wand"] == 1]
    for e, c in zip(hunt, farben[1:]):
        F, ua = e["F"], e["ua"]; s = ua.max(); ky = F.shape[0] // 2
        ax3.plot(e["zeta"][ky, :], ua[ky, :] / s, color=c, lw=1.4)
        ax3.plot(e["zeta"][ky, ::3], F[ky, ::3] / s, "o", ms=3, color=c, label=f"Ha = {e['Ha']}: {100*e['fehler']:.1f} %")
    ax3.set_xlabel("z/a"); ax3.set_ylabel("u / u_max")
    ax3.set_title(("Leitende Hartmann-Wände (Hunt): Seitenstrahlen" if de else "Conducting Hartmann walls (Hunt): side jets"), fontsize=10)
    ax3.legend(frameon=False, fontsize=8)
    # unten links/mitte: Feld als Farbe (Hunt, höchstes Ha) FluidX3D und Referenz
    if hunt:
        e = hunt[-1]
        for j, (feld, tit) in enumerate(((e["F"], "FluidX3D"), (e["ua"], ("Referenz" if de else "reference")))):
            ax = fig.add_subplot(gs[1, j])
            m = ax.pcolormesh(e["zeta"], e["eta"], feld / e["ua"].max(), cmap="viridis", vmin=0, shading="auto")
            ax.set_aspect("equal"); ax.set_xlabel("z/a"); ax.set_ylabel(("y/a (B ↑)" if de else "y/a (B ↑)"))
            ax.set_title(f"Hunt, Ha = {e['Ha']}: {tit}", fontsize=10)
            fig.colorbar(m, ax=ax, shrink=0.8, label="u / u_max")
    # unten rechts: Gitterstudie
    ax4 = fig.add_subplot(gs[1, 2])
    if gitter:
        a_ = np.array([g["a"] for g in gitter]); f_ = np.array([g["fehler"] for g in gitter])
        ax4.loglog(a_, f_, "o-", color="#eb6834", label=f"Shercliff Ha = {gitter[0]['Ha']}")
        ax4.loglog(a_, f_[0] * (a_ / a_[0]) ** -2, ls="--", color="#52514e", label=("Ordnung 2" if de else "order 2"))
        ax4.set_xlabel(("Halbe Kanalweite a [Zellen]" if de else "half duct width a [cells]"))
        ax4.set_ylabel(("RMS-Fehler / u_max" if de else "RMS error / u_max"))
        ax4.set_title(("Gitterstudie" if de else "Grid study"), fontsize=10); ax4.legend(frameon=False, fontsize=8)
    for ax in fig.axes:
        if ax.get_label() != "<colorbar>":
            ax.grid(True, which="both", color="#e5e4e0", lw=0.6)
    fig.text(0.99, 0.005, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e", ha="right")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    name = "mhd_kanal.png" if de else "mhd_kanal_en.png"
    fig.savefig(ROOT / "docs" / "bilder" / name); plt.close(fig)
    shutil.copy(ROOT / "docs" / "bilder" / name, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return ROOT / "docs" / "bilder" / name


def main():
    import sys
    erg = ([lauf(Ha, 32, 0) for Ha in (0, 5, 10, 15)] + [lauf(30, 64, 0)]
           + [lauf(Ha, 32, 1) for Ha in (5, 10, 15)] + [lauf(30, 64, 1)])
    gitter = [lauf(10, a, 0) for a in (16, 32, 64)] if "--ohne-gitter" not in sys.argv else []
    for e in erg + gitter:
        print(f"Ha {e['Ha']:3d}  a {e['a']:3d}  Wand {e['wand']}  Fehler {100*e['fehler']:.2f} %  Durchsatz {100*e['q_fehler']:+.2f} %"
              f"  Konvergenz {e['konv']:.1e}  Schritte {e['schritte']}", flush=True)
    (ROOT / "stellarator" / "daten" / "mhd_kanal.json").write_text(json.dumps(
        [{k: v for k, v in e.items() if np.isscalar(v)} for e in erg + gitter], indent=1))
    for s in ("de", "en"):
        print(bild(erg, gitter, s))


if __name__ == "__main__":
    main()
