"""kraft_analyse.py — Woher kommt die Kraft auf die Spulen, und wie muss das Gehaeuse sie tragen?

  .venv-opt/bin/python -m stellarator.kraft_analyse <ordner mit biot_savart.json> [<weitere ...>] [--name x]

Je Basisspule entlang der Bogenlaenge (Anlagengroesse, B0 = 6,5 T, Massstab L wie stellarator.kopplung):
- Lorentzkraft je Laenge f = I t x (B_fremd + B_eigen); B_eigen regularisiert fuer den quadratischen Wickelpaket-
  querschnitt (simsopt B_regularized_pure, regularization_rect), B_fremd = Biot-Savart der anderen Spulen.
- Zerlegung im Frenet-Dreibein (t, N zum Kruemmungsmittelpunkt, B = t x N):
    f_N  in der Schmiegebene: wird wie in einem Seil als Zug getragen, wenn T = -f_N / kappa entlang der Spule
         konstant ist (Kreisring unter Innendruck). Schwankt T, muss das Gehaeuse den Rest durch Biegung tragen.
    f_B  senkrecht zur Schmiegebene: kann durch Zug ueberhaupt nicht getragen werden -> Biegung/Torsion, Tragwerk.
- Nettokraft je Spule (Zentrierkraft zur Torusachse, vertikale Kraft) und Anteil Eigenfeld.
Abschaetzung Spannung: Zug sigma_T = T / A_stahl, Biegung eines Balkens zwischen Stuetzstellen
  M ~ q l^2 / 8 (q = Querlast, l = Abstand der Stuetzen), sigma_B = M / W.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np

from stellarator.kopplung import L, B0, WP_M, WOUT

MU0 = 4e-7 * np.pi
ROOT = Path(__file__).resolve().parents[1]


def kalibrierung(bs):
    """Strom so, dass das mittlere |B| auf der VMEC-Achse B0 ist (wie kopplung.geometrie)."""
    from scipy.io import netcdf_file
    with netcdf_file(str(WOUT), mmap=False) as w:
        rax, zax, nfp = w.variables["raxis_cc"][:].copy(), w.variables["zaxis_cs"][:].copy(), int(w.variables["nfp"].data)
    ph = np.linspace(0, 2 * np.pi, 400, endpoint=False); n = np.arange(len(rax))
    Ra = (rax[None] * np.cos(nfp * n[None] * ph[:, None])).sum(1)
    Za = (-zax[None] * np.sin(nfp * n[None] * ph[:, None])).sum(1)
    bs.set_points(np.c_[Ra * np.cos(ph), Ra * np.sin(ph), Za])
    Bu = np.linalg.norm(bs.B(), axis=1).mean()
    return B0 / Bu * L                     # Faktor auf die Einheitsstroeme (B ~ I / L)


def analyse(ordner: Path) -> dict:
    from simsopt import load
    from simsopt.field import BiotSavart
    from simsopt.field.selffield import B_regularized_pure, regularization_rect
    bs = load(str(ordner / "biot_savart.json"))
    coils = bs.coils
    fak = kalibrierung(bs)
    n_basis = len(coils) // 4                                  # nfp = 2, stellsym -> 4 Kopien je Basisspule
    out = []
    for k in range(n_basis):
        c = coils[k]; cu = c.curve
        I = c.current.get_value() * fak                         # A an der Anlage
        wp = WP_M * np.sqrt(abs(I) / 22.11e6)                   # gleiche Stromdichte wie 16 Spulen (Stufe 0)
        reg = regularization_rect(wp / L, wp / L)               # Querschnitt in Einheitsgeometrie
        g = cu.gamma(); gd = cu.gammadash(); gdd = cu.gammadashdash()
        andere = BiotSavart([cc for j, cc in enumerate(coils) if j != k]); andere.set_points(g)
        # Felder in Einheitsgeometrie mit Einheitsstrom -> an die Anlage: B ~ I / L
        Bf = andere.B() * fak / L
        Be = np.asarray(B_regularized_pure(g, gd, gdd, cu.quadpoints, c.current.get_value(), reg)) * fak / L
        ds = np.linalg.norm(gd, axis=1) / len(g) * L            # m je Punkt
        t = gd / np.linalg.norm(gd, axis=1)[:, None]
        f_f = I * np.cross(t, Bf); f_e = I * np.cross(t, Be); f = f_f + f_e      # N/m
        # Frenet-Dreibein an der Anlage
        kv = np.cross(gd, gdd); kap = np.linalg.norm(kv, axis=1) / np.linalg.norm(gd, axis=1) ** 3 / L
        Bn = kv / np.linalg.norm(kv, axis=1)[:, None]; N = np.cross(Bn, t)
        # stabiles Bezugssystem (wie spulen.rahmen): n = vom Spulenschwerpunkt weg, b = t x n (seitlich)
        X = g * L; r = X - X.mean(0); nv = r - (r * t).sum(1)[:, None] * t; nv /= np.linalg.norm(nv, axis=1)[:, None]
        bv = np.cross(t, nv)
        fN, fB, fT = (f * nv).sum(1), (f * bv).sum(1), (f * t).sum(1)          # fN > 0: nach aussen
        # Seilkraft: Anteil der Kraft gegen die Kruemmungsrichtung / kappa (nur wo die Spule deutlich gekruemmt ist)
        T = np.where(kap > 0.08, -(f * N).sum(1) / kap, np.nan)
        R = np.hypot(X[:, 0], X[:, 1])
        eR = np.c_[X[:, 0] / R, X[:, 1] / R, 0 * R]
        F = (f * ds[:, None]).sum(0); FR = float(((f * eR).sum(1) * ds).sum())
        s = np.r_[0, np.cumsum(ds)[:-1]]
        out.append({"spule": k, "I_MA": I / 1e6, "wp_m": wp, "laenge_m": float(ds.sum()), "s": s, "f": np.linalg.norm(f, axis=1),
                    "fN": fN, "fB": fB, "fT": fT, "T": T, "kappa": kap, "R": R, "Z": X[:, 2],
                    "f_eigen_anteil": float(np.linalg.norm(f_e, axis=1).mean() / np.linalg.norm(f, axis=1).mean()),
                    "F_netto_MN": (F / 1e6).tolist(), "F_radial_MN": FR / 1e6,
                    "F_betrag_integral_MN": float((np.linalg.norm(f, axis=1) * ds).sum() / 1e6),
                    "B_fremd_max_T": float(np.linalg.norm(Bf, axis=1).max())})
    return {"ordner": str(ordner.relative_to(ROOT)), "n_spulen": len(coils), "spulen": out}


def kennzahlen(a: dict) -> dict:
    zs = []
    for sp in a["spulen"]:
        f, fB, T = sp["f"], sp["fB"], sp["T"]
        ok = np.isfinite(T)                                       # fast gerade Stuecke: T undefiniert
        zs.append({"spule": sp["spule"] + 1, "I_MA": round(sp["I_MA"], 2), "wp_m": round(sp["wp_m"], 3), "laenge_m": round(sp["laenge_m"], 1),
                   "f_max_MN_m": round(f.max() / 1e6, 1), "f_mittel_MN_m": round(f.mean() / 1e6, 1),
                   "quer_anteil": round(float(np.sqrt((fB ** 2).mean() / (f ** 2).mean())), 2),
                   "T_min_MN": round(float(np.percentile(T[ok], 5)) / 1e6), "T_max_MN": round(float(np.percentile(T[ok], 95)) / 1e6),
                   "eigenfeld_anteil": round(sp["f_eigen_anteil"], 2),
                   "F_netto_MN": [round(x) for x in sp["F_netto_MN"]], "F_radial_MN": round(sp["F_radial_MN"]),
                   "F_integral_MN": round(sp["F_betrag_integral_MN"])})
    return {"ordner": a["ordner"], "n_spulen": a["n_spulen"], "basisspulen": zs}


def bild(a: dict, ziel: Path, en: bool = False):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tr = (lambda d, e: e) if en else (lambda d, e: d)
    nb = len(a["spulen"])
    fig, ax = plt.subplots(3, nb, figsize=(4.2 * nb, 9), sharex="col", sharey="row")
    for k, sp in enumerate(a["spulen"]):
        s = sp["s"]
        ax[0, k].plot(s, sp["f"] / 1e6, "k", lw=1.6, label=tr("Betrag", "magnitude"))
        ax[0, k].plot(s, sp["fN"] / 1e6, "C0", lw=1.2, label=tr("nach außen (Spule weitet sich)", "outward (coil expands)"))
        ax[0, k].plot(s, sp["fB"] / 1e6, "C3", lw=1.2, label=tr("seitlich (quer zur Spule)", "sideways (out of coil plane)"))
        ax[0, k].set_title(tr(f"Spule {k+1}", f"Coil {k+1}") + f"  ({sp['I_MA']:.1f} MA)")
        T = sp["T"]
        ax[1, k].plot(s, T / 1e6, "C2", lw=1.4)
        ax[1, k].axhline(np.nanmedian(T) / 1e6, color="C2", ls=":", lw=1)
        ax[2, k].plot(s, sp["kappa"], "C1", lw=1.4)
        ax[2, k].set_xlabel(tr("Weg entlang der Spule [m]", "distance along coil [m]"))
        for r in range(3):
            ax[r, k].grid(alpha=0.3)
    ax[0, 0].set_ylabel(tr("Kraft je Meter [MN/m]", "force per metre [MN/m]"))
    ax[1, 0].set_ylabel(tr("nötige Seilkraft T [MN]", "required rope tension T [MN]"))
    ax[2, 0].set_ylabel(tr("Krümmung [1/m]", "curvature [1/m]"))
    ax[0, 0].legend(fontsize=8, loc="upper right")
    ax[1, 0].set_ylim(-500, 1500)
    fig.suptitle(tr(f"Kraft entlang der Spulen ({a['n_spulen']} Spulen, B₀ = 6,5 T, R₀ = 10,4 m)",
                    f"Force along the coils ({a['n_spulen']} coils, B₀ = 6.5 T, R₀ = 10.4 m)"))
    fig.text(0.99, 0.005, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", ha="right", fontsize=7, color="0.5")
    fig.tight_layout(rect=(0, 0.01, 1, 0.97)); fig.savefig(ziel, dpi=130); plt.close(fig)


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else "kraft_analyse"
    if "--name" in sys.argv:
        args.remove(name)
    alle = []
    for o in args:
        a = analyse(ROOT / o); k = kennzahlen(a); alle.append(k)
        tag = f"{name}_{a['n_spulen']}"
        bild(a, ROOT / "docs" / "bilder" / f"{tag}.png"); bild(a, ROOT / "docs" / "bilder" / f"{tag}_en.png", en=True)
        print(json.dumps(k, indent=1, ensure_ascii=False))
    (ROOT / "daten").mkdir(exist_ok=True)
    (ROOT / "daten" / f"{name}.json").write_text(json.dumps(alle, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
