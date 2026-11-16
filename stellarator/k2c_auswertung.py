"""k2c_auswertung.py -- K2c: Tabellen (Markdown) + Bilder DE/EN aus sim/kette_k2c/<ID8>/*.json. KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
P = Path(__file__).resolve().parents[1]
IDS = ["DK8s6qwo","DfXvrph2","DZrUR4dA","DBszvkku","D799qKH8","DmC2qkhi","DGozX5fj","DHTy2o9U","DGMtrTL2","DDWJg4NB"]
D = {i: json.loads((P/f"sim/kette_k2c/{i}/stufe0_modell.json").read_text())["auslegung_modell"] for i in IDS}
N = {i: json.loads((P/f"sim/kette_k2c/{i}/spulenzahl.json").read_text()) for i in IDS}
def best(i, L):
    c = [v for v in D[i][L].values() if v["machbar"]]
    return min(c, key=lambda v: (v["R0_m"], v["B0_T"])) if c else None
out = []
out.append("| Form | Leiter | R0 [m] | B0 [T] | j [A/mm²] | I max [MA] | Leiterfeld [T] (Grenze) | Spalt [m] | Energie [GJ] | bindend (Definition unten) |\n|---|---|---|---|---|---|---|---|---|---|")
for i in IDS:
    for L in ("HTS", "Nb3Sn"):
        b = best(i, L)
        out.append(f"| {i} | {L} | " + (f"{b['R0_m']:.1f} | {b['B0_T']:.2f} | {b['j_A_mm2']:.0f} | {b['I_max_MA']:.1f} | {b['leiterfeld_T']:.1f} ({b['leiterfeld_grenze_T']:.0f}) | {b['spalt_m']:.2f} | {b['energie_GJ']:.0f} | {', '.join(b['bindend'])} |" if b else "nicht machbar bis R0 45 m | | | | | | | |"))
out.append("\n| Form | R0 HTS j 40 | j 30 | j 25 | j 20 | j 15 | R0 Nb3Sn j 15 | j 10 |\n|---|---|---|---|---|---|---|---|")
f = lambda x: f"{x['R0_m']:.1f}" if x["machbar"] else "–"
for i in IDS:
    out.append(f"| {i} | " + " | ".join(f(D[i]["HTS"][j]) for j in ("40","30","25","20","15")) + " | " + " | ".join(f(D[i]["Nb3Sn"][j]) for j in ("15","10")) + " |")
out.append("\n| Form | N=40 | 50 | 60 | 70 | 80 | 90 | 100 | 120 | 140 | 160 | kleinstes N (Raster) mit R0 ≤ 25 m |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
nmin = {}
for i in IDS:
    row = N[i]; ok = [int(n) for n, x in row.items() if x["machbar"] and x["R0_m"] <= 25.0]
    nmin[i] = min(ok) if ok else None
    out.append(f"| {i} | " + " | ".join(f(row[str(n)]) for n in (40,50,60,70,80,90,100,120,140,160)) + f" | {nmin[i]} |")
(P/"sim/kette_k2c/tabellen.md").write_text("\n".join(out)); print("\n".join(out))
T = {"de": dict(t1="K2c: kleinste Anlage je Form und Leiter, Leiterfeld als Modell", y="R0 [m]", band="Erwartung 25–40 m", g25="Ziel 25 m", L1="HTS (j frei)", L2="Nb3Sn (j frei)",
               foot="KI-generiert (Claude Sonnet 5.5), Entwurf – sim/kette_k2c", t2="K2c: R0 gegen j (HTS)", x2="technische Stromdichte j [A/mm²]", t3="K2c: R0 gegen Spulenzahl N (HTS j 40, Annahme I ∝ 1/N)", x3="Spulenzahl N", nm="nicht machbar bis 45 m", rast="Raster-Grenze 45 m"),
     "en": dict(t1="K2c: smallest plant per shape and conductor, conductor field as model", y="R0 [m]", band="expectation 25–40 m", g25="target 25 m", L1="HTS (j free)", L2="Nb3Sn (j free)",
               foot="AI-generated (Claude Sonnet 5.5), draft – sim/kette_k2c", t2="K2c: R0 versus j (HTS)", x2="engineering current density j [A/mm²]", t3="K2c: R0 versus coil count N (HTS j 40, assumption I ∝ 1/N)", x3="coil count N", nm="infeasible up to 45 m", rast="grid limit 45 m"),}
for lg, t in T.items():
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=110)
    ax.axhspan(25, 40, color="#c7e9c0", alpha=.6, label=t["band"]); ax.axhline(25, color="g", ls="--", label=t["g25"]); ax.axhline(45, color="r", ls=":", label=t["rast"])
    for k, i in enumerate(IDS):
        b = best(i, "HTS"); n = best(i, "Nb3Sn")
        if b: ax.bar(k-.2, b["R0_m"], .38, color="#1f77b4", label=t["L1"] if k == 0 else None); ax.text(k-.2, b["R0_m"]+.5, f"j{b['j_A_mm2']:.0f}", ha="center", fontsize=7)
        else: ax.text(k-.2, 1, "✕", ha="center", color="#1f77b4")
        if n: ax.bar(k+.2, n["R0_m"], .38, color="#ff7f0e", label=t["L2"] if k == 3 else None); ax.text(k+.2, n["R0_m"]+.5, f"j{n['j_A_mm2']:.0f}", ha="center", fontsize=7)
        else: ax.text(k+.2, 1, "✕", ha="center", color="#ff7f0e")
    ax.set_xticks(range(10)); ax.set_xticklabels(IDS, rotation=35, fontsize=8); ax.set(ylabel=t["y"], title=t["t1"], ylim=(0, 58)); ax.legend(fontsize=8, loc="upper left", ncol=3)
    fig.text(.5, .01, t["foot"] + f" · ✕ = {t['nm']}", ha="center", fontsize=8); fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(P/f"sim/kette_k2c/bilder/k2c_R0_je_form_{lg}.png"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=110)
    js = [40, 30, 25, 20, 15]
    for i in IDS:
        ax.plot([j for j in js if D[i]["HTS"][str(j)]["machbar"]], [D[i]["HTS"][str(j)]["R0_m"] for j in js if D[i]["HTS"][str(j)]["machbar"]], "o-", label=i)
    ax.axhspan(25, 40, color="#c7e9c0", alpha=.5, label=t["band"]); ax.axhline(25, color="g", ls="--", label=t["g25"]); ax.invert_xaxis()
    ax.set(xlabel=t["x2"], ylabel=t["y"], title=t["t2"]); ax.legend(fontsize=7, ncol=2); ax.grid(alpha=.3)
    fig.text(.5, .01, t["foot"], ha="center", fontsize=8); fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(P/f"sim/kette_k2c/bilder/k2c_R0_gegen_j_{lg}.png"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=110)
    ns = [40,50,60,70,80,90,100,120,140,160]
    for i in IDS:
        ok = [n for n in ns if N[i][str(n)]["machbar"]]
        ax.plot(ok, [N[i][str(n)]["R0_m"] for n in ok], "o-", label=i)
    ax.axhline(25, color="g", ls="--", label=t["g25"]); ax.axhspan(0, 25, color="#c7e9c0", alpha=.5)
    ax.set(xlabel=t["x3"], ylabel=t["y"], title=t["t3"]); ax.legend(fontsize=7, ncol=2); ax.grid(alpha=.3)
    fig.text(.5, .01, t["foot"], ha="center", fontsize=8); fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(P/f"sim/kette_k2c/bilder/k2c_R0_gegen_N_{lg}.png"); plt.close(fig)
