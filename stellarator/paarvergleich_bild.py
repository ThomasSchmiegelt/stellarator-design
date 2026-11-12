"""paarvergleich_bild.py -- Vortragsbild: Keine Plasmaform ist in allen Kriterien vorn; der Sieger hängt von der Gewichtung ab.

KI-generiert (Claude Opus, 2026-11-11). Liest sim/spulenfreundlich/vergleich/formen_vergleich.json (formen_vergleich.py --top 10 --turbulenz gx),
gleiche Normierung wie dort (feldfehler, qi logarithmisch; 1 = beste Form im Vergleich).

  .venv-constellaration/bin/python -m stellarator.paarvergleich_bild
Ausgabe: sim/spulenfreundlich/vergleich/paarvergleich_kriterien.png und .json
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "sim" / "spulenfreundlich" / "vergleich"
KRIT = ["feldfehler", "qi", "achter", "kreuzend", "bauhoehe", "turbulenz"]
LOG = {"feldfehler", "qi"}
TITEL = {"feldfehler": "Feldfehler\nder Spulen", "qi": "Teilchen-\neinschluss (QI)", "achter": "Seiten-Achter\n(Biegung)",
         "kreuzend": "kreuzende\nNachbarspulen", "bauhoehe": "Bauhöhe\n[m]", "turbulenz": "Wärmeverlust\nTurbulenz (GX)"}
KURZ = {"feldfehler": "Feldfehler", "qi": "QI", "achter": "Seiten-Achter", "kreuzend": "kreuzende Spulen", "bauhoehe": "Bauhöhe", "turbulenz": "Turbulenz (GX)"}
FMT = {"feldfehler": "{:.1e}", "qi": "{:.1e}", "achter": "{:.0f}", "kreuzend": "{:.0f}", "bauhoehe": "{:.1f}", "turbulenz": "{:.2f}"}


def main():
    d = json.loads((V / "formen_vergleich.json").read_text())
    namen = list(d["formen"]); X = np.array([[d["formen"][n][k] for k in KRIT] for n in namen], float)
    T = X.copy(); li = [j for j, c in enumerate(KRIT) if c in LOG]; T[:, li] = np.log10(T[:, li])
    N = (T.max(0) - T) / np.where(np.ptp(T, 0) > 0, np.ptp(T, 0), 1)
    gleich = N.mean(1); ordnung = np.argsort(-gleich)
    from scipy.stats import rankdata
    rang = np.column_stack([rankdata(X[:, j], method="min") for j in range(X.shape[1])]).astype(int)   # 1 = bester, gleiche Werte gleicher Rang
    sieger = {}
    for j, k in enumerate(KRIT):                                        # Sieger, wenn ein Kriterium dreifach zählt
        g = np.ones(len(KRIT)); g[j] = 3; g /= g.sum(); sieger[k] = namen[int(np.argmax(N @ g))]
    sieger["gleich"] = namen[int(np.argmax(gleich))]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(16, 6.6), gridspec_kw={"width_ratios": [2.2, 1]})
    R = rang[ordnung]
    ax.imshow(R, cmap="RdYlGn_r", vmin=1, vmax=len(namen), aspect="auto")
    for i, n in enumerate(ordnung):
        for j, k in enumerate(KRIT):
            ax.text(j, i, FMT[k].format(X[n, j]) + f"\nRang {R[i, j]}", ha="center", va="center", fontsize=7.5,
                    fontweight="bold" if R[i, j] == 1 else "normal")
    ax.set_xticks(range(len(KRIT)), [TITEL[k] for k in KRIT], fontsize=9)
    ax.set_yticks(range(len(namen)), [f"{namen[n][:8]}  ({gleich[n]:.2f})" for n in ordnung], fontsize=9)
    ax.set_title("Zehn Plasmaformen, sechs Kriterien (alle: kleiner besser). Farbe = Rang, grün = Rang 1\n"
                 "Ziel „Rang 1 in jeder Spalte“ erreicht keine Form; alle 10 liegen auf der Pareto-Front", fontsize=10)
    ax.set_ylabel("Form (Punkte bei gleichen Gewichten)")
    beste = {k: namen[int(np.argmin(X[:, j]))] for j, k in enumerate(KRIT)}
    zeilen = [[KURZ[k], beste[k][:8], sieger[k][:8]] for k in KRIT] + [["alle gleich", "–", sieger["gleich"][:8]]]
    ax2.axis("off")
    tb = ax2.table(cellText=zeilen, colLabels=["Kriterium", "Beste allein", "Sieger, wenn\n3-fach gewichtet"], loc="center",
                   cellLoc="left", colWidths=[0.46, 0.25, 0.29])
    tb.auto_set_font_size(False); tb.set_fontsize(10); tb.scale(1, 2.3)
    ax2.set_title(f"Nur ein Kriterium: {len(set(beste.values()))} verschiedene Beste.\n"
                  f"Alle zusammen: die ausgewogene Form\ngewinnt {sum(v == sieger['gleich'] for v in sieger.values())} von 7 Gewichtungen", fontsize=10)
    fig.suptitle("Eine gute Anlage braucht viele Parameter: Paarvergleich der Top 10 (Datensatzformen unverändert, eigene Spulen)  —  KI-generiert", fontsize=11)
    fig.tight_layout()
    fig.savefig(V / "paarvergleich_kriterien.png", dpi=130)
    out = {"hinweis": "KI-generiert", "sieger_bei_dreifachgewicht": sieger, "verschiedene_sieger": len(set(sieger.values())),
           "rang_1_je_kriterium": {k: namen[int(np.argmin(X[:, j]))] for j, k in enumerate(KRIT)},
           "punkte_gleich": {n: round(float(gleich[i]), 3) for i, n in enumerate(namen)}}
    (V / "paarvergleich_kriterien.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
