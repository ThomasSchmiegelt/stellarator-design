"""zufall_gegen_pi.py: Wählt PI besser als der Zufall? Auswertung nach Erwartung F-313 (2026-11-10).

KI-generiert (Claude Opus, 2026-11-12).
Daten: sim/spulenfreundlich/results.tsv (alle 361 Poolformen, feste Bewertung), verlauf.log (Zeilen „REST fertig <id>“ = Zufallsreihe).
PI-Wahl = alle bewerteten Formen, die nicht aus der Zufallsreihe stammen (Ralph-Loop 9.11.).
Bootstrap: 10 000 Ziehungen ohne Zurücklegen aus allen 361, Größe = Anzahl PI-Formen; Kennzahlen Bestwert und Median.
Ausgabe: sim/spulenfreundlich/vergleich/zufall_gegen_pi.json und .png (mit Zielband aus F-313).
"""
import csv, json, re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

W = Path(__file__).resolve().parent.parent / "sim/spulenfreundlich"
zeilen = {z["id"]: z for z in csv.DictReader(open(W / "results.tsv"), delimiter="\t")}
zufall = []
for l in open(W / "verlauf.log", errors="replace"):
    m = re.search(r"REST fertig (\w+)", l)
    if m and m.group(1) in zeilen and m.group(1) not in zufall:
        zufall.append(m.group(1))
pi = [i for i in zeilen if i not in set(zufall)]


def ff(i):
    try:
        return float(zeilen[i]["ziel_Bn_mittel"])
    except ValueError:
        return np.nan


def kenn(ids):
    f = np.array([ff(i) for i in ids]); f = f[np.isfinite(f)]
    ok = [zeilen[i]["regeln_ok"] == "True" for i in ids]
    nfp = {k: sum(zeilen[i]["nfp"] == k for i in ids) for k in "2345"}
    med_nfp2 = float(np.median([ff(i) for i in ids if zeilen[i]["nfp"] == "2" and np.isfinite(ff(i))]))
    return dict(n=len(ids), best=float(f.min()), median=float(np.median(f)), anteil_regeln=float(np.mean(ok)),
                nfp=nfp, median_nfp2=med_nfp2)


alle = list(zeilen)
ka, kp, kz = kenn(alle), kenn(pi), kenn(zufall)
pi_best = kp["best"]
besser = sorted([i for i in zufall if ff(i) < pi_best], key=ff)

rng = np.random.default_rng(20261112)
farr = np.array([ff(i) for i in alle])
B = 10000
bs_best = np.empty(B); bs_med = np.empty(B)
for b in range(B):
    s = farr[rng.choice(len(alle), size=len(pi), replace=False)]
    s = s[np.isfinite(s)]
    bs_best[b] = s.min(); bs_med[b] = np.median(s)
# Anteil der Zufallsziehungen, deren Bestwert schlechter (größer) ist als der PI-Bestwert = „Perzentil“ von PI
p_best = float(np.mean(bs_best > pi_best))
p_med = float(np.mean(bs_med > kp["median"]))

# Rang der besten PI-Form unter allen
rang = sorted(alle, key=lambda i: ff(i) if np.isfinite(ff(i)) else 9)
pi_rang = 1 + rang.index(min(pi, key=lambda i: ff(i) if np.isfinite(ff(i)) else 9))

erg = dict(hinweis="KI-generiert; Erwartung F-313", alle=ka, pi=kp, zufall=kz,
           zufall_besser_als_pi_best=[(i[:8], ff(i), zeilen[i]["nfp"], zeilen[i]["regeln_ok"]) for i in besser],
           pi_best_rang_unter_allen=pi_rang,
           bootstrap=dict(ziehungen=B, groesse=len(pi), anteil_zufall_best_schlechter_als_pi=p_best,
                          anteil_zufall_median_schlechter_als_pi=p_med,
                          best_p10_p50_p90=[float(np.percentile(bs_best, q)) for q in (10, 50, 90)],
                          median_p10_p50_p90=[float(np.percentile(bs_med, q)) for q in (10, 50, 90)]))
(W / "vergleich/zufall_gegen_pi.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))

T = {"de": dict(band="Zielbereich: besser als 80 % der Zufallsziehungen\n(Schwelle aus Erwartung F-313)", pi="PI-Wahl ({n} Formen)",
                x="{t} Feldfehler je Ziehung [1e-4]  (kleiner = besser)", y="Anzahl Ziehungen", tit="{t}: {B} Zufallsziehungen à {n} aus 361",
                box="PI besser als\n{p:.0f} % der Ziehungen", sup="Wählt der lokale Agent bessere Formen als der Zufall?   KI-generiert",
                t=("Bestwert", "Median"), datei="zufall_gegen_pi.png"),
     "en": dict(band="target: better than 80 % of random draws\n(threshold from expectation F-313)", pi="PI choice ({n} shapes)",
                x="{t} field error per draw [1e-4]  (smaller = better)", y="number of draws", tit="{t}: {B} random draws of {n} from 361",
                box="PI better than\n{p:.0f} % of draws", sup="Does the local agent pick better shapes than chance?   AI-generated",
                t=("Best", "Median"), datei="zufall_gegen_pi_en.png")}
for sp, L in T.items():
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for a, d, x, t in ((ax[0], bs_best, pi_best, L["t"][0]), (ax[1], bs_med, kp["median"], L["t"][1])):
        a.hist(d * 1e4, bins=50, color="#9aa7b8")
        lo = np.percentile(d, 20) * 1e4
        x0 = a.get_xlim()[0]
        a.axvspan(x0, lo, color="#2e8b57", alpha=0.15, label=L["band"])
        a.axvline(lo, color="#2e8b57", ls="--", lw=1)
        a.set_xlim(x0, None)
        a.axvline(x * 1e4, color="#c0392b", lw=2, label=L["pi"].format(n=len(pi)))
        a.text(0.98, 0.55, L["box"].format(p=np.mean(d > x) * 100), transform=a.transAxes, ha="right", fontsize=9,
               bbox=dict(fc="white", ec="#c0392b"))
        a.set_xlabel(L["x"].format(t=t)); a.set_ylabel(L["y"]); a.legend(fontsize=8)
        a.set_title(L["tit"].format(t=t, B=B, n=len(pi)))
    fig.suptitle(L["sup"], fontsize=11)
    fig.tight_layout(); fig.savefig(W / "vergleich" / L["datei"], dpi=130); plt.close(fig)
print(json.dumps(erg, indent=1, ensure_ascii=False))
