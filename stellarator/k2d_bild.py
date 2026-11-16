"""k2d_bild.py -- K2d: Leiterfeld (K2, echte Spulen) gegen Anlagengroesse je Stromdichte, Grenze 20 T.  KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
import json, time
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
P = Path(__file__).resolve().parents[1]; G = P / "sim/kette_dgoz/groesse"; out = P / "sim/kette_dgoz/bilder"; out.mkdir(exist_ok=True)
pts = {}
for j in (30, 25, 20, 15):
    R = json.loads((G / f"j{j}/runden.json").read_text())["runden"]
    s = json.loads((G / f"j{j}/start/k2/P3.json").read_text())["leiterfeld"]["B_leiter_bei_B0_bilanz_T"]
    pts[j] = [(R[0]["R0_in_m"], s, "Start (K2c-Größe)")] + [(r["R0_in_m"], r["B_leiter_K2_T"], f"Runde {r['runde']}") for r in R[1:] if r["B_leiter_K2_T"]]
d = time.strftime("%Y-%m-%d")
for sp in ("de", "en"):
    de = sp == "de"; fig, a = plt.subplots(figsize=(8.5, 5.6))
    a.axhspan(20, 30, color="tab:red", alpha=0.18, label="über Grenze HTS 20 T (Annahme des Werkzeugs)" if de else "above HTS limit 20 T (tool assumption)")
    a.axhline(20, color="r", ls="--")
    for (j, v), c in zip(pts.items(), ["tab:blue", "tab:orange", "tab:green", "tab:purple"]):
        a.plot([x[0] for x in v], [x[1] for x in v], "o-", color=c, label=f"j = {j} A/mm²")
        for x in v:
            a.annotate(f"{x[1]:.1f} T", (x[0], x[1]), xytext=(4, 5), textcoords="offset points", fontsize=8)
    a.set_xlabel("R0 [m]" if de else "R0 [m]"); a.set_ylabel("Spitzenfeld am Leiter, K2 [T]" if de else "peak field at conductor, K2 [T]"); a.set_ylim(14, 28); a.grid(alpha=.3); a.legend(fontsize=8, loc="upper right")
    fig.suptitle(("Leiterfeld in K2 gegen Größe (DGozX5fj, kreuzungsfreie Spulen)" if de else "Conductor field in K2 vs size (DGozX5fj, crossing-free coils)") + "\n" + ("KI-generiert (Claude Sonnet 5.5) · Entwurf" if de else "AI-generated (Claude Sonnet 5.5) · draft"), fontsize=10)
    fig.text(0.5, 0.005, ("KI-generiert · Entwurf · %s · Quelle: sim/kette_dgoz/groesse/j*/runden.json, start/k2/P3.json" if de else "AI-generated · draft · %s · source: sim/kette_dgoz/groesse/j*/runden.json, start/k2/P3.json") % d, ha="center", fontsize=7, color="0.4")
    fig.tight_layout(rect=(0, 0.02, 1, 0.92)); fig.savefig(out / f"k2d_leiterfeld_gegen_R0_{sp}.png", dpi=130); plt.close(fig)
print(pts)
