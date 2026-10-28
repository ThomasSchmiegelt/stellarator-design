"""varianten_vergleich.py — Kuehlsegment-Varianten bewerten: Pareto-Front, Gewichte per Paarvergleich (AHP), Rangfolge.

    .venv/bin/python -m stellarator.varianten_vergleich [--varianten f1,f2,f5,f10,f11,f12]
                                                        [--kriterien "temperatur>streuung=3,temperatur>druck=5,..."]
                                                        [--urteile "f12>f11,f11>f5"]

Kriterien je Variante (aus cfd/auswertung.json und auslegung.json, ohne neue Rechnung):
  temperatur  Temperaturanstieg Wasser -> Plasmaseite bei 0,5 MW/m2: Leitung Innenhaut + Uebergang bei v Plasmaseite
              (gleiche Formeln wie kuehlung_waerme.py, ohne Rippen)                                   kleiner besser
  streuung    Ungleichverteilung ueber den Umfang im Gyroid-Kern                                      kleiner besser
  druck       Druckverlust Ein -> Aus                                                                  kleiner besser
  totwasser   Geschwindigkeit, unter der 10 % der Plasmaseite liegen                                   groesser besser
1) Pareto: eine Variante faellt heraus, wenn eine andere in keinem Kriterium schlechter und in einem besser ist.
2) AHP: Kriterien paarweise, "a>b=3" heisst a ist 3-mal so wichtig wie b (Saaty-Skala 1..9). Gewichte aus dem
   Eigenvektor, Konsistenz CR < 0,1 gilt als widerspruchsfrei. Fehlende Paare zaehlen als gleich wichtig.
3) Rang: gewichtete Summe der auf 0..1 normierten Kriterien (1 = beste Variante im Vergleich).
4) --urteile: Paarvergleiche ganzer Varianten durch den Nutzer; das Programm meldet, ob die Gewichte sie bestaetigen.
5) Festigkeit als Ausschluss (nicht gewichtet): Spannung in der Innenhaut beim Kuehlmitteldruck --druck aus
   haut_festigkeit.py (Elmer, Platte ueber Gyroid-Zellen; Hautdicke log-log interpoliert, Spannweite a/2 - w
   quadratisch skaliert). Ueber der zulaessigen Spannung -> Variante unzulaessig.
f6-f9 sind ungueltig (Sperrschicht im Rechengitter, siehe README) und standardmaessig nicht dabei.
Ausgabe sim/kuehlung_segment/vergleich/: vergleich.json, vergleich.png.
"""
import argparse, json
import numpy as np

from .kuehlung_segment import WURZEL
from .kuehlung_waerme import h_dittus, K_STAHL

KRIT = {"temperatur": ("Temperaturanstieg Plasmaseite [K]", -1), "streuung": ("Streuung Umfang [%]", -1),
        "druck": ("Druckverlust [kPa]", -1), "totwasser": ("v unterste 10 % Plasmaseite [mm/s]", +1)}
Q = 0.5e6
WAND_VORN = 0.010                     # Gyroid-Wand an der Haut (2 x halbdicke_vorn)
RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32}       # Zufallsindex nach Saaty


def kennzahlen(name):
    o = WURZEL / name
    p = json.loads((o / "auslegung.json").read_text())["parameter"]
    w = json.loads((o / "cfd" / "auswertung.json").read_text())
    zelle = p.get("zelle_vorn") or p.get("zelle", 0.3)
    d_h = 4 * 0.82 / (2 * 3.09 / zelle)
    h, _ = h_dittus(w["plasmaseite"]["v_mittel_m_s"], d_h)
    return {"temperatur": Q * p["haut_innen"] / K_STAHL + Q / h, "streuung": 100 * w["kern_umfang"]["streuung_rel"],
            "druck": w["druckverlust_kPa"], "totwasser": 1000 * w["plasmaseite"]["v_p10_m_s"]}


def hautspannung(p, druck):
    """Vergleichsspannung [MPa] in der Innenhaut aus sim/haut_festigkeit/gyroid/ergebnis.json."""
    e = json.loads((WURZEL.parent / "haut_festigkeit" / "gyroid" / "ergebnis.json").read_text())
    t = np.array([float(k.split()[0]) for k in e["faelle"]]) / 1000
    k = np.array([f["sigma_max_Pa_je_MPa"] for f in e["faelle"].values()])
    s, i = np.log(p["haut_innen"]), np.argsort(t)
    k_t = np.exp(np.interp(s, np.log(t[i]), np.log(k[i]), left=np.nan, right=np.nan))
    if np.isnan(k_t):                                           # ausserhalb: Steigung der beiden aeussersten Punkte
        j = i[:2] if s < np.log(t).min() else i[-2:]
        m = np.diff(np.log(k[j])) / np.diff(np.log(t[j]))
        k_t = np.exp(np.log(k[j[0]]) + m[0] * (s - np.log(t[j[0]])))
    a0, w0 = e["parameter"]["zelle"] / 1000, e["parameter"]["wand"] / 1000
    a = p.get("zelle_vorn") or p.get("zelle", 0.3)
    return k_t * ((a / 2 - WAND_VORN) / (a0 / 2 - w0)) ** 2 * druck / 1e6, e["sigma_zul_MPa"]


def pareto(X, s):
    """X Varianten x Kriterien, s Vorzeichen (+1 groesser besser). True = nicht dominiert."""
    G = X * s
    return np.array([not any(np.all(G[j] >= G[i]) and np.any(G[j] > G[i]) for j in range(len(G)) if j != i)
                     for i in range(len(G))])


def ahp(text):
    k = list(KRIT); n = len(k); A = np.ones((n, n))
    for teil in filter(None, (t.strip() for t in (text or "").split(","))):
        paar, wert = teil.split("=") if "=" in teil else (teil, "1")
        a, b = paar.split(">"); i, j = k.index(a.strip()), k.index(b.strip())
        A[i, j], A[j, i] = float(wert), 1 / float(wert)
    ew, ev = np.linalg.eig(A); m = np.argmax(ew.real)
    g = np.abs(ev[:, m].real); g /= g.sum()
    cr = max((ew[m].real - n) / (n - 1) / RI[n], 0.0) if RI[n] else 0.0
    return dict(zip(k, g)), cr


def bild(namen, X, front, punkte, datei):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    sc = ax[0].scatter(X[:, 1], X[:, 0], c=X[:, 2], s=140, cmap="viridis", edgecolors=np.where(front, "red", "none"), linewidths=2.5)
    for n, x, y in zip(namen, X[:, 1], X[:, 0]):
        ax[0].annotate(n, (x, y), (6, 6), textcoords="offset points")
    ax[0].set_xlabel(KRIT["streuung"][0]); ax[0].set_ylabel(KRIT["temperatur"][0]); ax[0].set_xscale("log")
    fig.colorbar(sc, ax=ax[0], label=KRIT["druck"][0]); ax[0].set_title("Varianten (rot umrandet = Pareto-Front)")
    r = np.argsort(punkte)
    ax[1].barh([namen[i] for i in r], punkte[r], color=["#c0392b" if front[i] else "#95a5a6" for i in r])
    ax[1].set_xlabel("gewichtete Punkte (0..1)"); ax[1].set_title("Rangfolge mit den Gewichten aus dem Paarvergleich")
    fig.tight_layout(); fig.savefig(datei, dpi=110); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--varianten", default="f1,f2,f5,f10,f11,f12")
    ap.add_argument("--kriterien", default="")
    ap.add_argument("--urteile", default="")
    ap.add_argument("--druck", type=float, default=4.0, help="Kuehlmitteldruck [MPa] fuer die Festigkeit")
    a = ap.parse_args(argv)
    namen = a.varianten.split(",")
    K = [kennzahlen(n) for n in namen]
    X = np.array([[k[c] for c in KRIT] for k in K]); s = np.array([v[1] for v in KRIT.values()])
    front = pareto(X, s)
    P = [json.loads((WURZEL / n / "auslegung.json").read_text())["parameter"] for n in namen]
    sig = np.array([hautspannung(p, a.druck)[0] for p in P]); zul = hautspannung(P[0], a.druck)[1]
    g, cr = ahp(a.kriterien)
    G = X * s; N = (G - G.min(0)) / np.where(np.ptp(G, 0) > 0, np.ptp(G, 0), 1)
    punkte = N @ np.array(list(g.values()))
    print(f"Variante  " + "  ".join(f"{c:>11}" for c in KRIT) + f"   Front  Punkte  Haut[MPa] bei {a.druck:g} MPa")
    for i in np.argsort(-punkte):
        print(f"{namen[i]:<9} " + "  ".join(f"{v:11.1f}" for v in X[i]) + f"   {'ja' if front[i] else '-':>5}  {punkte[i]:.2f}"
              f"  {sig[i]:7.0f} {'ok' if sig[i] <= zul else 'UNZULAESSIG'}")
    print("Gewichte: " + ", ".join(f"{k} {v:.2f}" for k, v in g.items()) + f"   Konsistenz CR = {cr:.2f}"
          + ("  (WIDERSPRUECHLICH, > 0,1)" if cr > 0.1 else ""))
    pruef = []
    for u in filter(None, (t.strip() for t in a.urteile.split(","))):
        sieger, verlierer = u.split(">"); ok = punkte[namen.index(sieger)] > punkte[namen.index(verlierer)]
        pruef.append({"urteil": u, "bestaetigt": bool(ok)})
        print(f"Urteil {u}: {'bestaetigt' if ok else 'NICHT bestaetigt -> Gewichte passen nicht zum Urteil'}")
    o = WURZEL / "vergleich"; o.mkdir(exist_ok=True)
    (o / "vergleich.json").write_text(json.dumps({"varianten": {n: k for n, k in zip(namen, K)}, "front": [n for n, f in zip(namen, front) if f],
                                                  "gewichte": g, "konsistenz_CR": cr, "punkte": dict(zip(namen, punkte.round(3).tolist())),
                                                  "urteile": pruef, "kriterien_eingabe": a.kriterien,
                                                  "druck_MPa": a.druck, "haut_spannung_MPa": dict(zip(namen, sig.round(0).tolist())), "sigma_zul_MPa": zul}, indent=1, ensure_ascii=False))
    bild(namen, X, front, punkte, o / "vergleich.png")


if __name__ == "__main__":
    main()
