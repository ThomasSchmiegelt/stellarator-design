"""formen_vergleich.py — Plasmaformen mit eigenen Spulen vergleichen: Ausschluss, Pareto, Gewichte per Paarvergleich (AHP), Rang.

KI-generiert (Claude Opus, 2026-11-11). Gegenstück zu varianten_vergleich.py (Kühlung), gleiche Methode.
Nutzer 2026-11-11: „wir müssen dann am ende eh eine paarbewertung machen“; Bauhöhe als Kriterium (Vorschlag 3, freigegeben).

    .venv-opt/bin/python -m stellarator.formen_vergleich [--top 10 | --formen ID1,ID2,...]
                                                       [--kriterien "feldfehler>bauhoehe=3,feldfehler>qi=2,..."]
                                                       [--urteile "DZrUR4dA>DmC2qkhi"] [--max-hoehe 40]

Daten: sim/spulenfreundlich (feste Bewertung, results.tsv, ergebnis/<id>.json, faelle/<id>/satz_*), keine neue Stage-2-Rechnung.
Kriterien je Form (alle: kleiner besser):
  feldfehler  mittlerer Feldfehler Bn der eigenen Spulen
  qi          Abweichung von Quasi-Isodynamik der Plasmaform (Pool)
  achter      Summe der Seiten-Achter aller Spulen (Baubarkeit)
  kreuzend    kreuzende Nachbarpaare in der Abwicklung (Montage)
  bauhoehe    Höhe des Spulensatzes, oberste bis unterste Spule [m] bei a = 1,8 m (Gebäude, Kran, Wartung)
  turbulenz   --turbulenz gx (Vorgabe, Nutzer 2026-11-11 „GX bitte in den Paarvergleich“): turbulenter Ionen-Wärmefluss Q_i/Q_GB
              aus GX (sim/gx_pilot/gx_werte.json, B-074; eine Flussröhre, adiabatische Elektronen, gleiche Gradienten).
              Fehlt GX für eine Form: Liste + Befehl, Abbruch. Nie mit dem Ersatzmaß gemischt.
              --turbulenz ersatz: geometrisches Ersatzmaß aus dem ConStellaration-Datensatz
              („flux compression in regions of bad curvature“, Grenze dort ≤ 0,9), B-073
Ausschluss (nicht gewichtet): Bauregeln verletzt (regeln_ok False). Optional --max-hoehe [m]: ANNAHME, keine belegte Grenze.
1) Pareto: Form fällt heraus, wenn eine andere in keinem Kriterium schlechter und in einem besser ist.
2) AHP: "a>b=3" heißt a ist 3-mal so wichtig wie b (Saaty 1..9). Fehlende Paare gleich wichtig. CR < 0,1 widerspruchsfrei.
3) Rang: gewichtete Summe der auf 0..1 normierten Kriterien (1 = beste Form im Vergleich). Feldfehler und qi logarithmisch normiert.
4) --urteile: Bauchurteile des Nutzers über ganze Formen (ID-Anfang reicht); das Programm meldet, ob die Gewichte sie bestätigen.
Die Wahl bleibt beim Menschen. Ausgabe sim/spulenfreundlich/vergleich/: formen_vergleich.json, formen_vergleich.png, hoehen.json (Zwischenspeicher).
"""
import argparse, csv, json, sys
from pathlib import Path
import numpy as np

WURZEL = Path(__file__).resolve().parent.parent / "sim" / "spulenfreundlich"
KRIT = {"feldfehler": "Feldfehler Bn (Mittel)", "qi": "QI-Abweichung Plasma", "achter": "Seiten-Achter (Summe)",
        "kreuzend": "kreuzende Nachbarpaare", "bauhoehe": "Bauhöhe Spulensatz [m]",
        "turbulenz": "Turbulenz-Ersatzmaß (ConStellaration)"}
LOG = {"feldfehler", "qi"}
RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32}
RICHTWERT_BN = 1e-3                    # ANNAHME: Richtwert aus der Spulensuche (Deutungsschwelle B-072), nicht belegt


def hoehen(ids):
    """Bauhöhe und Spulengröße je Form (Zwischenspeicher hoehen.json)."""
    datei = WURZEL / "vergleich" / "hoehen.json"; datei.parent.mkdir(exist_ok=True)
    h = json.loads(datei.read_text()) if datei.exists() else {}
    neu = [i for i in ids if i not in h]
    if neu:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from spulen_satz import flaeche, lade_satz
        from simsopt.field import Current, coils_via_symmetries
        for i in neu:
            o = next((WURZEL / "faelle" / i).glob("satz_*"))
            s = flaeche(o / "boundary.json", nphi=60, ntheta=30)
            k = 1.8 / float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0)))))
            b, I, nfp = lade_satz(o)
            z = np.concatenate([c.curve.gamma()[:, 2] for c in coils_via_symmetries(b, [Current(float(x)) for x in I], nfp, True)]) * k
            gr = max(float(np.linalg.norm(p[:, None] - p[None], axis=-1).max()) for p in (c.gamma() * k for c in b))
            g = s.gamma() * k
            h[i] = {"bauhoehe_m": round(float(np.ptp(z)), 2), "plasmahoehe_m": round(float(np.ptp(g[..., 2])), 2),
                    "spule_max_m": round(gr, 2), "aussen_d_m": round(float(2 * np.hypot(g[..., 0], g[..., 1]).max()), 2)}
            print(f"  Höhe {i[:8]}: {h[i]}", flush=True)
        datei.write_text(json.dumps(h, indent=1))
    return h


def ahp(text):
    k = list(KRIT); n = len(k); A = np.ones((n, n))
    for teil in filter(None, (t.strip() for t in (text or "").split(","))):
        paar, wert = teil.split("=") if "=" in teil else (teil, "1")
        a, b = paar.split(">"); i, j = k.index(a.strip()), k.index(b.strip())
        A[i, j], A[j, i] = float(wert), 1 / float(wert)
    ew, ev = np.linalg.eig(A); m = np.argmax(ew.real)
    g = np.abs(ev[:, m].real); g /= g.sum()
    return dict(zip(k, g)), max((ew[m].real - n) / (n - 1) / RI[n], 0.0)


def pareto(X):
    return np.array([not any(np.all(X[j] <= X[i]) and np.any(X[j] < X[i]) for j in range(len(X)) if j != i) for i in range(len(X))])


def bild(namen, X, front, punkte, max_h, datei):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    k = list(KRIT); f, b = k.index("feldfehler"), k.index("bauhoehe")
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.5))
    ax[0].axvspan(0, RICHTWERT_BN, color="#2ecc71", alpha=0.12, label=f"Feldfehler ≤ {RICHTWERT_BN:g} (Richtwert, Annahme)")
    if max_h:
        ax[0].axhspan(0, max_h, color="#3498db", alpha=0.10, label=f"Bauhöhe ≤ {max_h:g} m (Annahme)")
    sc = ax[0].scatter(X[:, f], X[:, b], c=X[:, k.index("achter")], s=120, cmap="viridis",
                       edgecolors=np.where(front, "red", "none"), linewidths=2.2)
    for n, x, y in zip(namen, X[:, f], X[:, b]):
        ax[0].annotate(n[:8], (x, y), (5, 5), textcoords="offset points", fontsize=8)
    ax[0].set_xscale("log"); ax[0].set_xlabel(KRIT["feldfehler"] + ", kleiner besser"); ax[0].set_ylabel(KRIT["bauhoehe"] + ", kleiner besser")
    fig.colorbar(sc, ax=ax[0], label=KRIT["achter"]); ax[0].legend(fontsize=8, loc="upper right")
    ax[0].set_title("Formen (rot umrandet = Pareto-Front über alle 6 Kriterien)", fontsize=10)
    r = np.argsort(punkte)
    ax[1].barh([namen[i][:8] for i in r], punkte[r], color=["#c0392b" if front[i] else "#95a5a6" for i in r])
    ax[1].set_xlim(0, 1); ax[1].set_xlabel("gewichtete Punkte (0..1, 1 = beste Form im Vergleich)")
    ax[1].set_title("Rang mit den Gewichten aus dem Paarvergleich (Wahl bleibt beim Menschen)", fontsize=10)
    fig.suptitle("Formenvergleich, feste Bewertung sim/spulenfreundlich · KI-generiert", fontsize=10)
    fig.tight_layout(); fig.savefig(datei, dpi=110); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10, help="die N Formen mit kleinstem Feldfehler (nach Ausschluss)")
    ap.add_argument("--formen", default="", help="feste Liste (ID-Anfang reicht), statt --top")
    ap.add_argument("--kriterien", default="")
    ap.add_argument("--urteile", default="")
    ap.add_argument("--turbulenz", choices=["gx", "ersatz"], default="gx", help="Quelle Kriterium turbulenz (B-074)")
    ap.add_argument("--max-hoehe", type=float, default=None, help="ANNAHME: Bauhöhe [m] darüber -> Ausschluss")
    a = ap.parse_args(argv)
    zeilen = {z["id"]: z for z in csv.DictReader(open(WURZEL / "results.tsv"), delimiter="\t")}
    ok = [i for i, z in zeilen.items() if z["regeln_ok"] == "True"]
    if a.formen:
        ids = [next(i for i in zeilen if i.startswith(t.strip())) for t in a.formen.split(",")]
    else:
        ids = sorted(ok, key=lambda i: float(zeilen[i]["ziel_Bn_mittel"]))[:a.top]
    H = hoehen(ids)
    if a.turbulenz == "gx":
        gw = json.loads((WURZEL.parent / "gx_pilot" / "gx_werte.json").read_text())["werte"]
        TU = {i: v["Q_i"] for i, v in gw.items()}
        KRIT["turbulenz"] = "Turbulenz GX Q_i/Q_GB"
    else:
        TU = json.loads((WURZEL / "vergleich" / "turbulenz_ersatz.json").read_text())
    aus = {i: ("Bauregeln verletzt" if zeilen[i]["regeln_ok"] != "True" else
               f"Bauhöhe {H[i]['bauhoehe_m']} m > {a.max_hoehe:g} m (Annahme)" if a.max_hoehe and H[i]["bauhoehe_m"] > a.max_hoehe else "")
           for i in ids}
    namen = [i for i in ids if not aus[i]]
    fehlt = [i for i in namen if i not in TU]
    if fehlt:
        print(f"GX-Wert fehlt für {len(fehlt)} Form(en): " + ", ".join(i[:8] for i in fehlt))
        print("Rechnen (etwa 20 min je Form, GPU, pausierbar):  bash sim/gx_pilot/gx_rechnen.sh " + " ".join(fehlt))
        print("Oder ohne GX:  --turbulenz ersatz")
        sys.exit(2)
    X = np.array([[float(zeilen[i]["ziel_Bn_mittel"]), float(zeilen[i]["qi"]), float(zeilen[i]["achter_seite"]),
                   float(zeilen[i]["kreuzend"]), H[i]["bauhoehe_m"], TU[i]] for i in namen])
    front = pareto(X); g, cr = ahp(a.kriterien)
    T = X.copy(); li = [j for j, c in enumerate(KRIT) if c in LOG]; T[:, li] = np.log10(T[:, li])
    N = (T.max(0) - T) / np.where(np.ptp(T, 0) > 0, np.ptp(T, 0), 1)
    punkte = N @ np.array(list(g.values()))
    print(f"{'Form':<10}" + "".join(f"{c:>12}" for c in KRIT) + "   Front  Punkte")
    for i in np.argsort(-punkte):
        print(f"{namen[i][:8]:<10}{X[i,0]:12.2e}{X[i,1]:12.2e}{X[i,2]:12.0f}{X[i,3]:12.0f}{X[i,4]:12.1f}{X[i,5]:12.2f}   {'ja' if front[i] else '-':>5}  {punkte[i]:.2f}")
    for i, grund in aus.items():
        if grund:
            print(f"ausgeschlossen {i[:8]}: {grund}")
    print("Gewichte: " + ", ".join(f"{k} {v:.2f}" for k, v in g.items()) + f"   Konsistenz CR = {cr:.2f}"
          + ("  (WIDERSPRÜCHLICH, > 0,1)" if cr > 0.1 else ""))
    pruef = []
    for u in filter(None, (t.strip() for t in a.urteile.split(","))):
        s, v = (next(j for j, n in enumerate(namen) if n.startswith(t.strip())) for t in u.split(">"))
        pruef.append({"urteil": u, "bestaetigt": bool(punkte[s] > punkte[v])})
        print(f"Urteil {u}: {'bestätigt' if punkte[s] > punkte[v] else 'NICHT bestätigt -> Gewichte passen nicht zum Urteil'}")
    o = WURZEL / "vergleich"
    (o / "formen_vergleich.json").write_text(json.dumps({
        "hinweis": "KI-generiert; Wahl bleibt beim Menschen", "formen": {n: dict(zip(KRIT, map(float, x)), **H[n]) for n, x in zip(namen, X)},
        "ausgeschlossen": {i: g_ for i, g_ in aus.items() if g_}, "front": [n for n, f in zip(namen, front) if f],
        "gewichte": g, "konsistenz_CR": cr, "punkte": dict(zip(namen, punkte.round(3).tolist())), "urteile": pruef,
        "kriterien_eingabe": a.kriterien, "turbulenz_quelle": a.turbulenz, "max_hoehe_annahme_m": a.max_hoehe}, indent=1, ensure_ascii=False))
    bild(namen, X, front, punkte, a.max_hoehe, o / "formen_vergleich.png")
    print("->", o / "formen_vergleich.png")


if __name__ == "__main__":
    main()
