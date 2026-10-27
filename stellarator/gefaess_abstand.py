"""gefaess_abstand.py — Platz fuer die Gefaesswand: Abstand Plasmarand -> Spulengehaeuse/Verbinder ueber den ganzen Torus.

    .venv/bin/python -m stellarator.gefaess_abstand [--wand 1.05] [--rand 0.05]

Fuer jeden Punkt des Plasmarands (1-GW-Form, R0 10,4 m) der kleinste Abstand zu den Gehaeusen und Verbindern aus dem
Surrogat-Modell (sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu, Material 3 = Gehaeuse, 4 = Verbinder).
Das ist der Bauraum fuer Spalt + Wand. Abgewickelte Karte (theta ueber phi) mit der Linie "Wand passt gerade"
(Abstand = wand + rand). Ausgabe sim/gefaess_abstand/abstand.png + abstand.json.
"""
import argparse, json
import numpy as np

from .gyroid_gefaess import randflaeche
from .lauf import PROJEKT

ZIEL = PROJEKT / "sim" / "gefaess_abstand"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--wand", type=float, default=1.05, help="Spalt + Wanddicke ab Plasmarand [m]")
    ap.add_argument("--rand", type=float, default=0.05, help="Sicherheitsabstand [m]")
    a = ap.parse_args(argv)
    import pyvista as pv
    from scipy.spatial import cKDTree
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ZIEL.mkdir(parents=True, exist_ok=True)
    g = pv.read(PROJEKT / "sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu")
    n_th, n_ph = 180, 720
    X = randflaeche(n_th=n_th, n_ph=n_ph)                          # (n_th, n_ph, 3), phi 0..360
    erg, karten = {}, {}
    for mat, name in ((3, "gehaeuse"), (4, "verbinder")):
        st = g.extract_cells(np.where(np.round(g.cell_data["material"]) == mat)[0]).extract_surface(algorithm="dataset_surface")
        st = st.triangulate().subdivide_adaptive(max_edge_len=0.05)   # Punkte dicht genug fuer den Abstand
        d, _ = cKDTree(st.points).query(X.reshape(-1, 3))
        karten[name] = d.reshape(n_th, n_ph)
        i = np.unravel_index(np.argmin(karten[name]), karten[name].shape)
        erg[name] = {"min_m": float(karten[name].min()), "theta_grad": float(i[0] * 360 / n_th),
                     "phi_grad": float(i[1] * 360 / n_ph)}
    D = np.minimum(karten["gehaeuse"], karten["verbinder"])
    ph = np.arange(n_ph) * 360 / n_ph; th = np.arange(n_th) * 360 / n_th
    seg = (ph >= 85) & (ph <= 95)
    erg["segment_85_95_min_m"] = float(D[:, seg].min())
    erg["anteil_zu_eng"] = float((D < a.wand + a.rand).mean())
    erg["wand_m"], erg["rand_m"] = a.wand, a.rand
    fig, ax = plt.subplots(figsize=(13, 5.2))
    im = ax.pcolormesh(ph, th, D, cmap="viridis", shading="auto", vmin=max(0.5, D.min()), vmax=min(3.0, D.max()))
    cs = ax.contour(ph, th, D, levels=[a.wand + a.rand], colors="#e2483d", linewidths=1.6)
    ax.clabel(cs, fmt={a.wand + a.rand: f"{a.wand + a.rand:.2f} m"}, fontsize=9)
    ax.axvspan(85, 95, color="white", alpha=0.25); ax.text(90, 350, "Segment\n85–95°", ha="center", va="top", fontsize=9, color="w")
    fig.colorbar(im, ax=ax, label="Abstand Plasmarand → Gehäuse/Verbinder [m]")
    ax.set_xlabel("φ toroidal [°]"); ax.set_ylabel("θ poloidal [°]")
    ax.set_title(f"Bauraum für Spalt + Wand: min {D.min():.2f} m (Gehäuse {erg['gehaeuse']['min_m']:.2f} m, "
                 f"Verbinder {erg['verbinder']['min_m']:.2f} m); rot: Wand {a.wand:.2f} m + {a.rand * 100:.0f} cm Rand, "
                 f"zu eng auf {erg['anteil_zu_eng'] * 100:.1f} % der Fläche", fontsize=10)
    fig.tight_layout(); fig.savefig(ZIEL / "abstand.png", dpi=110)
    np.save(ZIEL / "abstand.npy", D)
    (ZIEL / "abstand.json").write_text(json.dumps(erg, indent=1))
    print(json.dumps(erg, indent=1))


if __name__ == "__main__":
    main()
