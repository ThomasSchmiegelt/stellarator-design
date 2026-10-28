"""rohr_durchfuehrung.py — Passen die Kuehlwasserleitungen durch die Spalte zwischen den Spulen?

    .venv/bin/python -m stellarator.rohr_durchfuehrung [--wand 1.05] [--abstand 0.15] [--v 10] [--Q 26.4]

Von jedem Punkt der Gefaess-Aussenseite (Plasmarand + wand entlang der Normalen, 1-GW-Form R0 10,4 m) laeuft ein
gerades Rohr weiter entlang der Normalen 4 m nach aussen. Der kleinste Abstand dieses Weges zu den Spulen
(Surrogat-Modell sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu: Wickelpaket, Verguss, Gehaeuse, Verbinder) gibt
den groessten Rohr-Aussendurchmesser D = 2 (Abstand - abstand). abstand: Luft + Waermeschild zwischen heissem Rohr
(300 C) und kalter Spule. Wanddicke des Rohrs aus der Kesselformel s = p r_i / sigma (16 MPa, 150 MPa).
Bedarf: Volumenstrom Q (Blanket + Erstwand, waermebilanz.py) je Richtung (hin und zurueck), Geschwindigkeit v.
Zaehlung: je Nennweite gierig die freien Stellen belegen, Rohre nicht naeher als D + 0,2 m zueinander.
Naeherungen: nur gerade Rohre entlang der Normalen (Boegen koennten mehr Platz finden), Kryostat, Ports fuer Heizung,
Diagnostik und Pumpen nicht beruecksichtigt. Ausgabe sim/rohr_durchfuehrung/: ergebnis.json, durchfuehrung.png.
"""
import argparse, json
import numpy as np

from .gyroid_gefaess import randflaeche
from .lauf import PROJEKT

ZIEL = PROJEKT / "sim" / "rohr_durchfuehrung"
P_WASSER, SIGMA = 16.0, 150.0          # MPa
NENNWEITEN = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)   # Innendurchmesser [m]


def normalen(X):
    dth = np.roll(X, -1, 0) - np.roll(X, 1, 0); dph = np.roll(X, -1, 1) - np.roll(X, 1, 1)
    n = np.cross(dph, dth); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    mitte = X.mean(0, keepdims=True)                             # Schwerpunkt je Querschnitt
    return n * np.sign(np.sum(n * (X - mitte), -1, keepdims=True))


def zaehle(starts, d_max, D, abstand_rohre):
    """Gierig: freie Stellen mit d_max >= D belegen, Mindestabstand D + abstand_rohre."""
    ok = np.where(d_max >= D)[0]
    ok = ok[np.argsort(-d_max[ok])]
    gewaehlt = []
    for i in ok:
        if all(np.linalg.norm(starts[i] - starts[j]) >= D + abstand_rohre for j in gewaehlt):
            gewaehlt.append(i)
    return gewaehlt


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--wand", type=float, default=1.05, help="Spalt + Gefaesswand ab Plasmarand [m]")
    ap.add_argument("--abstand", type=float, default=0.15, help="Luft + Waermeschild Rohr-Spule [m]")
    ap.add_argument("--v", type=float, default=10.0, help="Geschwindigkeit im Rohr [m/s]")
    ap.add_argument("--Q", type=float, default=26.4, help="Volumenstrom je Richtung [m3/s]")
    ap.add_argument("--laenge", type=float, default=4.0, help="Rohrweg nach aussen [m]")
    a = ap.parse_args(argv)
    import pyvista as pv
    from scipy.spatial import cKDTree
    ZIEL.mkdir(parents=True, exist_ok=True)
    g = pv.read(PROJEKT / "sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu")
    st = g.extract_surface(algorithm="dataset_surface").triangulate().subdivide_adaptive(max_edge_len=0.05)
    baum = cKDTree(st.points)
    n_th, n_ph = 90, 360
    X = randflaeche(n_th=n_th, n_ph=n_ph); N = normalen(X)
    starts = (X + a.wand * N).reshape(-1, 3); Nr = N.reshape(-1, 3)
    s = np.arange(0, a.laenge + 1e-9, 0.05)
    frei = np.full(len(starts), np.inf)
    for k in range(0, len(starts), 4000):                       # Speicher schonen
        P = starts[k:k + 4000, None, :] + s[None, :, None] * Nr[k:k + 4000, None, :]
        d, _ = baum.query(P.reshape(-1, 3))
        frei[k:k + 4000] = d.reshape(len(P), len(s)).min(1)
    D_aussen = np.maximum(2 * (frei - a.abstand), 0)
    d_innen = D_aussen / (1 + P_WASSER / SIGMA)                  # D = d_i + 2 s, s = p d_i / (2 sigma)
    tab = []
    for di in NENNWEITEN:
        D = di * (1 + P_WASSER / SIGMA)
        n = len(zaehle(starts, d_innen, di, 0.2))
        Q_kap = n * np.pi * di ** 2 / 4 * a.v
        tab.append({"d_innen_m": di, "D_aussen_m": D, "rohre_moeglich": n, "Q_kapazitaet_m3_s": Q_kap,
                    "rohre_noetig_hin_und_zurueck": int(np.ceil(2 * a.Q / (np.pi * di ** 2 / 4 * a.v)))})
    erg = {"parameter": vars(a), "anteil_flaeche_mit_d_innen": {f"{di:g} m": float((d_innen >= di).mean()) for di in NENNWEITEN},
           "d_innen_max_m": float(d_innen.max()), "nennweiten": tab,
           "hinweis": "Rohre nur gerade entlang der Normalen; Ports fuer Heizung/Diagnostik/Pumpen nicht abgezogen"}
    (ZIEL / "ergebnis.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))
    for t in tab:
        print(f"d_i {t['d_innen_m']:.1f} m (D {t['D_aussen_m']:.2f}): moeglich {t['rohre_moeglich']:4d}, noetig "
              f"{t['rohre_noetig_hin_und_zurueck']:4d}  -> {'reicht' if t['rohre_moeglich'] >= t['rohre_noetig_hin_und_zurueck'] else 'reicht NICHT'}")
    print(f"groesster Innendurchmesser {d_innen.max():.2f} m; Flaechenanteile: {erg['anteil_flaeche_mit_d_innen']}")
    bild(a, d_innen.reshape(n_th, n_ph), tab, ZIEL / "durchfuehrung.png")


def bild(a, karte, tab, datei):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.5), gridspec_kw={"width_ratios": [1.7, 1]})
    im = ax[0].imshow(karte, origin="lower", extent=[0, 360, 0, 360], aspect="auto", cmap="viridis", vmin=0)
    cs = ax[0].contour(np.linspace(0, 360, karte.shape[1]), np.linspace(0, 360, karte.shape[0]), karte, [0.3, 0.5],
                       colors=["white", "red"], linewidths=1)
    ax[0].clabel(cs, fmt=lambda v: f"{v:g} m")
    ax[0].set_xlabel("toroidaler Winkel φ [°]"); ax[0].set_ylabel("poloidaler Winkel θ [°]")
    ax[0].set_title("größter Rohr-Innendurchmesser durch die Spulenspalte (gerade nach außen)")
    fig.colorbar(im, ax=ax[0], label="d_innen [m]")
    x = np.arange(len(tab))
    ax[1].bar(x - 0.2, [t["rohre_moeglich"] for t in tab], 0.4, label="möglich", color="#27ae60")
    ax[1].bar(x + 0.2, [t["rohre_noetig_hin_und_zurueck"] for t in tab], 0.4, label="nötig (hin + zurück)", color="#c0392b")
    ax[1].set_xticks(x, [f"{t['d_innen_m']:g}" for t in tab]); ax[1].set_xlabel("Innendurchmesser [m]")
    ax[1].set_ylabel("Anzahl Rohre"); ax[1].set_yscale("log"); ax[1].legend()
    ax[1].set_title(f"{a.Q:g} m³/s je Richtung bei {a.v:g} m/s, 16 MPa")
    fig.tight_layout(); fig.savefig(datei, dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
