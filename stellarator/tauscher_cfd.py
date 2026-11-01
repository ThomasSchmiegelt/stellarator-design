"""tauscher_cfd.py — Waermeuebergang und Druckverlust einer Tauscherseite mit FluidX3D (Validierung, Fahrplan Schritt 3).

Ausgebildete Stroemung in einem kurzen, in allen Richtungen periodischen Stueck (wie Renon & Jeanningros 2024):
Gyroid, Diamond (TPMS, Wand 0,5 mm) oder Platten (glatt oder gewellt wie stellarator/freecad_platten.py). Nur eine
Fluidseite wird gerechnet, die andere ist fest. Antrieb: Volumenkraft fz. Waerme: gleichmaessige Quelle q in allen
Fluidzellen, Wand T = 0 halbwegs zwischen Fluid- und Festzelle wie die hydraulische Wand (Anti-Bounce-Back, eigene
Kernaenderung; erster Ansatz mit TYPE_T-Fluidzellen legte die thermische Wand eine Zelle nach innen -> Nu 3x zu hoch).
    f (Fanning) = fz d_h / (2 u^2),   h = q V_f / (A T_m),   Nu = h d_h / D,   Re = u d_h / nu
u = mittlere Geschwindigkeit in z ueber alle Fluidzellen, T_m = Summe(uz T)/Summe(uz), A und d_h = 4 V_f / A aus der
glatten Geometrie (Marching Cubes auf feinem Gitter). FluidX3D: D = alpha_eingestellt / 2 (D3Q7 mit c_s^2 = 1/4,
Diffusionstest), deshalb wird alpha doppelt eingestellt.
Pruefung der Methode: laminarer glatter Spalt, f = 24/Re und Nu = 10 (isotherme Waende, gleichmaessige Quelle:
T = q y (b-y) / 2D, mit Parabelprofil T_m = q b^2 / 10 D, h = q b / (2 T_m) = 5 D / b, d_h = 2 b).
Erster Ansatz mit Ein- und Austritt verworfen: fuer Re 3000 braeuchte der Kanal > 25 % Dichteunterschied.

  .venv/bin/python -m stellarator.tauscher_cfd --typ gyroid --re 3000 [--n_dh 24] [--pr 1.5]
Ausgabe: sim/tauscher/cfd/<typ>_re<Re>_n<n_dh>/ (geometrie.bin, fall.txt, stat.txt, feld.bin, ergebnis.json)
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np

WURZEL = Path(__file__).resolve().parent.parent
FX = Path.home() / "fluidx3d_tauscher"
SIM = WURZEL / "sim" / "tauscher" / "cfd"
STANDARD = {"gyroid": dict(a=4.33), "diamond": dict(a=5.37), "platte": dict(a=1.0, A=0.0),
            "chevron": dict(a=1.0, A=0.5, lam=4.0, beta=60.0)}


def s_tpms(typ, X, Y, Z, k):
    """Abstand zur Mittelflaeche mit Vorzeichen, s = g / |grad g| (wie picogk/GyroidTauscher)."""
    sx, cx, sy, cy, sz, cz = np.sin(X), np.cos(X), np.sin(Y), np.cos(Y), np.sin(Z), np.cos(Z)
    if typ == "gyroid":
        g = sx * cy + sy * cz + sz * cx
        gx, gy, gz = cx * cy - sz * sx, -sx * sy + cy * cz, -sy * sz + cz * cx
    else:
        g = sx * sy * sz + sx * cy * cz + cx * sy * cz + cx * cy * sz
        gx = cx * sy * sz + cx * cy * cz - sx * sy * cz - sx * cy * sz
        gy = sx * cy * sz - sx * sy * cz + cx * cy * cz - cx * sy * sz
        gz = sx * sy * cz - sx * cy * sz - cx * sy * sz + cx * cy * cz
    return g / (k * np.maximum(np.sqrt(gx ** 2 + gy ** 2 + gz ** 2), 0.3))


def perioden(typ, P, t):
    """Periodenlaengen (x, y, z) [mm] des Rechengebiets."""
    if typ in ("gyroid", "diamond"):
        return P["a"], P["a"], P["a"]
    p = P["a"] + t
    if typ == "platte":
        return 2 * P["a"], p, 2 * P["a"]
    b = np.radians(P["beta"])
    return P["lam"] / np.cos(b), 2 * p, P["lam"] / np.sin(b)


def feld(typ, P, t, X, Y, Z):
    """Vorzeichenbehaftetes Feld: > 0 in der gerechneten Fluidseite (Nullstelle = Wandoberflaeche)."""
    if typ in ("gyroid", "diamond"):
        k = 2 * np.pi / P["a"]
        return s_tpms(typ, X * k, Y * k, Z * k, k) - t / 2
    p = P["a"] + t
    if typ == "platte":
        yy = np.mod(Y, p)
        return np.minimum(yy - t, p - yy) * 1.0                  # Platte bei y in [0, t]
    b = np.radians(P["beta"]); A, lam = P["A"], P["lam"]
    y1 = t / 2 + A * np.sin(2 * np.pi * (X * np.cos(b) - Z * np.sin(b)) / lam)        # Platte 1 (+beta)
    y2 = t / 2 + p + A * np.sin(2 * np.pi * (X * np.cos(-b) - Z * np.sin(-b)) / lam)  # Platte 2 (-beta)
    yy = np.mod(Y, 2 * p)
    return np.minimum(yy - y1 - t / 2, y2 - t / 2 - yy)          # Spalt zwischen Platte 1 und 2


def glatt_kennwerte(typ, P, t, n=120):
    """Wandflaeche je Volumen (eine Seite), Fluidanteil und d_h der glatten Geometrie (eine Periode)."""
    import pyvista as pv
    Lx, Ly, Lz = perioden(typ, P, t)
    nx, ny, nz = (max(int(n * L / max(Lx, Ly, Lz)), 24) for L in (Lx, Ly, Lz))
    x, y, z = ((np.arange(m) + 0.5) * L / m for m, L in ((nx, Lx), (ny, Ly), (nz, Lz)))
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    F = feld(typ, P, t, X, Y, Z)
    F = np.pad(F, 1, mode="wrap")                                 # periodisch, damit die Flaeche am Rand stimmt
    g = pv.ImageData(dimensions=F.shape, spacing=(Lx / nx, Ly / ny, Lz / nz),
                     origin=(-Lx / nx * 1.5, -Ly / ny * 1.5, -Lz / nz * 1.5))
    g.point_data["f"] = F.ravel(order="F")
    m = g.contour([0.0], scalars="f").clip_box([0, Lx, 0, Ly, 0, Lz], invert=False)
    A = m.area / (Lx * Ly * Lz)
    phi = float(np.mean(F[1:-1, 1:-1, 1:-1] > 0))
    return A, phi, 4 * phi / A


def geometrie(typ, P, t, dx, kacheln):
    """Belegung [z, y, x]: 0 fest, 1 Fluid, 2 Fluid an der Wand; periodisch, kacheln = (kx, ky, kz) Perioden."""
    L = perioden(typ, P, t)
    n = [max(int(round(Li / dx)), 4) for Li in L]
    d = [Li / ni for Li, ni in zip(L, n)]
    x, y, z = ((np.arange(ni * k) + 0.5) * di for ni, k, di in zip(n, kacheln, d))
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")
    occ = (feld(typ, P, t, X, Y, Z) > 0).astype(np.uint8)
    fest = occ == 0
    nb = np.zeros_like(fest)
    for ax in (0, 1, 2):
        nb |= np.roll(fest, 1, ax) | np.roll(fest, -1, ax)
    occ[(occ == 1) & nb] = 2
    return occ, float(np.mean(d))


def renon_f(re, typ):
    return 1.850 * re ** -0.17 * (1.145 if typ == "gyroid" else 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--typ", default="gyroid", choices=list(STANDARD))
    ap.add_argument("--a", type=float, default=None, help="Zelle [mm] (Platten: Spalt)")
    ap.add_argument("--t", type=float, default=0.5)
    ap.add_argument("--re", type=float, default=3000)
    ap.add_argument("--pr", type=float, default=1.5)
    ap.add_argument("--n_dh", type=int, default=24, help="Gitterzellen je hydraulischem Durchmesser")
    ap.add_argument("--u", type=float, default=0.05, help="mittlere Geschwindigkeit [Gittereinheiten]")
    ap.add_argument("--kacheln", default="2,2,2", help="Perioden in x, y, z")
    ap.add_argument("--durchlaeufe", type=float, default=40, help="Laufzeit in Durchstroemungen des Gebiets")
    ap.add_argument("--quelle", default="gleich", choices=["gleich", "u"],
                    help="Waermequelle: gleich in jeder Fluidzelle oder proportional u_z (Patankar 1977, H1-Randbedingung)")
    ap.add_argument("--tag", default="", help="Zusatz zum Ordnernamen (Surrogat-Punkte)")
    ap.add_argument("--fz_dh", type=float, default=None, help="Antrieb fz*d_h/u^2 aus einem frueheren Lauf (spart Nachregeln)")
    a_ = ap.parse_args()
    P = dict(STANDARD[a_.typ]); P["a"] = a_.a or P["a"]
    A_v, phi, dh = glatt_kennwerte(a_.typ, P, a_.t)
    kach = tuple(int(v) for v in a_.kacheln.split(","))
    occ, dx = geometrie(a_.typ, P, a_.t, dh / a_.n_dh, kach)
    Nz, Ny, Nx = occ.shape
    dh_c = dh / dx
    nfl = int((occ > 0).sum()); phi_c = nfl / occ.size
    nq = nfl                                                       # Quelle in allen Fluidzellen (Wand: Festzellen TYPE_S|TYPE_T)
    nu = a_.u * dh_c / a_.re; D = nu / a_.pr
    fz = renon_f(a_.re, a_.typ) * 2 * a_.u ** 2 / dh_c             # Schaetzwert aus der Korrelation
    if a_.typ == "platte":
        fz = 24 / a_.re * 2 * a_.u ** 2 / dh_c
    if a_.fz_dh:
        fz = a_.fz_dh * a_.u ** 2 / dh_c
    Nu0 = 0.2644 * a_.re ** 0.69 * a_.pr ** (1 / 3) if a_.typ != "platte" else 10.0
    q = Nu0 * D / dh_c * 4 / dh_c                                  # ergibt T_m ~ 1
    schritte = int(a_.durchlaeufe * Nz / a_.u)
    aus = SIM / (f"{a_.typ}_re{int(a_.re)}_n{a_.n_dh}" + ("_qu" if a_.quelle == "u" else "") + (f"_{a_.tag}" if a_.tag else "")); aus.mkdir(parents=True, exist_ok=True)
    occ.tofile(aus / "geometrie.bin")
    print(f"{a_.typ}: a {P['a']} mm, d_h {dh:.3f} mm, Fluidanteil {phi:.3f} (Gitter {phi_c:.3f}), Gitter {Nx}x{Ny}x{Nz} = "
          f"{occ.size/1e6:.2f} Mio, nu {nu:.2e}, D {D:.2e}, Schritte {schritte}", flush=True)
    for versuch in range(2):
        (aus / "fall.txt").write_text(f"{aus}/geometrie.bin {aus} {Nx} {Ny} {Nz} {nu:.6g} {2*D:.6g} {fz:.6g} {a_.u:.6g} {schritte} 500\n")
        r = subprocess.run([str(FX / "bin" / "FluidX3D")], cwd=FX, capture_output=True, text=True,
                           env=dict(os.environ, TAUSCHER_FALL=str(aus / "fall.txt"), FX_Q_T=f"{q:.6e}", FX_Q_U0=f"{a_.u if a_.quelle == 'u' else 0:.6e}"))
        (aus / "fluidx3d.log").write_text(r.stdout[-20000:] + r.stderr[-5000:])
        d = np.loadtxt(aus / "stat.txt", comments="#")
        m = d[int(0.6 * len(d)):]
        u, Tm = m[:, 1].mean(), m[:, 2].mean()
        re = u * dh_c / nu
        print(f"  Versuch {versuch}: fz {fz:.3e} -> Re {re:.0f}", flush=True)
        if abs(re / a_.re - 1) < 0.15 or not np.isfinite(re):   # Korrelationen werden beim tatsaechlichen Re verglichen
            break
        fz *= (a_.re / re) ** 1.8 if a_.typ != "platte" else a_.re / re
    f = fz * dh_c / (2 * u ** 2)
    if a_.quelle == "u":
        nq = nfl * u / a_.u                                        # Quelle q u_z/u0: Summe = q nfl u/u0
    h = q * nq / (A_v * dx * occ.size * Tm)                       # A in Zellen^2 = A_v dx * Gittervolumen
    Nu = h * dh_c / D
    j = Nu / (re * a_.pr ** (1 / 3))
    schwank = float(m[:, 2].std() / Tm)
    from stellarator.vorwaermer import renon, li2020, li2022
    ref = {"Renon": renon(re, a_.pr), "Li 2020": li2020(re, a_.pr), "Li 2022": li2022(re, a_.pr)}
    if a_.typ == "gyroid":
        ref["Renon"] = (ref["Renon"][0], ref["Renon"][1] * 1.145)
    if a_.typ == "platte":
        ref = {"laminar Spalt (Quelle, isotherm)": (10.0, 24 / re)} if a_.quelle == "gleich" else {"laminar Spalt H1 (q ~ u)": (8.235, 24 / re)}
    erg = dict(typ=a_.typ, P=P, t=a_.t, d_h=dh, phi=phi, A_v=A_v, n_dh=a_.n_dh, gitter=[Nx, Ny, Nz], Re=float(re), Pr=a_.pr,
               f=float(f), Nu=float(Nu), j=float(j), j_f13=float(j / f ** (1 / 3)), T_m_schwankung=schwank,
               ref={k: dict(Nu=float(v[0]), f=float(v[1])) for k, v in ref.items()})
    (aus / "ergebnis.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))
    print(f"  Re {re:.0f}, f {f:.4f}, Nu {Nu:.1f}, j/f^1/3 {j/f**(1/3):.4f}, Schwankung T_m {schwank:.3f}")
    for k, v in ref.items():
        print(f"  {k:32s} Nu {v[0]:.1f}  f {v[1]:.4f}")


if __name__ == "__main__":
    main()
