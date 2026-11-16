"""k2b_bilder.py -- Bilder und Tabellendaten K2b (DE/EN).  KI-generiert (Claude Sonnet 5.5, 2026-11-13).
Quelle: sim/kette_k2b/<id8>/<j40|j25>/runde_<n>.json (Schleife stellarator/k2b_schleife.py). Ausgabe sim/kette_k2b/bilder/ und tabelle.json."""
import json, glob, time
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = Path(__file__).resolve().parents[1]
O = P / "sim/kette_k2b"; B = O / "bilder"; B.mkdir(exist_ok=True)
ORDER = ["DK8s6qwo", "DfXvrph2", "DZrUR4dA", "DGMtrTL2", "DGozX5fj", "DmC2qkhi", "DHTy2o9U", "DBszvkku", "DDWJg4NB", "D799qKH8"]
HOCH = ["DGozX5fj", "DmC2qkhi", "D799qKH8", "DBszvkku"]
datum = time.strftime("%Y-%m-%d")


def runden(i8, tag):
    return [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(O / i8 / tag / "runde_[0-9].json")))]


def vorher(i8):
    n = "dk8_1GW" if i8 == "DK8s6qwo" else f"{i8.lower()}_1GW"
    return json.loads((P / "sim/invers" / n / "bilanz.json").read_text())["auslegung"]["HTS"]


tab = {}
for i8 in ORDER:
    for tag in ("j40", "j25"):
        rs = runden(i8, tag)
        if rs:
            tab[f"{i8}/{tag}"] = rs
json.dump({k: [{x: v for x, v in r.items() if x not in ("auslastung",)} for r in rs] for k, rs in tab.items()},
          open(O / "tabelle.json", "w"), indent=1, ensure_ascii=False)

T = {"de": dict(kg="KI-generiert (Claude Sonnet 5.5) · Entwurf", fuss="KI-generiert · Entwurf · {d} · Quelle: sim/kette_k2b/<Form>/<Variante>/runde_<n>.json, sim/invers/<Form>_1GW/bilanz.json",
                 vor="B-078 (Start, f_I 1, k_B 2)", r2="nach 1 Korrektur (Runde 2)", last="letzte machbare Runde (nicht konvergiert)",
                 nm="danach nicht machbar (R0 > 45 m)", R0="großer Radius R0 [m]", f1t="K2b: R0 je Form, vorher gegen korrigiert (HTS, j 40 A/mm²)",
                 band_hi="Erwartung hohes iota: 15–22 m", band_dk="Erwartung DK8s6qwo: 24–30 m", raster="Raster-Grenze Stufe 0 (30 m)",
                 lf="max. Feld am Leiter, stärkste Spule, bei B0 der Bilanz [T]", lim="Grenze HTS 20 T (Annahme des Werkzeugs)",
                 f2t="K2b: Konvergenz je Form (j 40 A/mm²)", rd="Runde", kb="k_B echt = B_Leiter,max / B0", band_kb="Erwartung k_B DK8s6qwo: 2,8–3,2",
                 f3t="K2b: Variante j 25 A/mm² gegen 40 A/mm² (Annahme)", j40="j 40", j25="j 25", band_j="Erwartung j25: R0 10–20 % kleiner",
                 dR="ΔR0 zur Vorrunde [m]", tol="Konvergenzkriterium |ΔR0| < 0,2 m", rr="Runde"),
     "en": dict(kg="AI-generated (Claude Sonnet 5.5) · draft", fuss="AI-generated · draft · {d} · source: sim/kette_k2b/<shape>/<variant>/runde_<n>.json, sim/invers/<shape>_1GW/bilanz.json",
                 vor="B-078 (start, f_I 1, k_B 2)", r2="after 1 correction (round 2)", last="last feasible round (not converged)",
                 nm="infeasible afterwards (R0 > 45 m)", R0="major radius R0 [m]", f1t="K2b: R0 per shape, before vs corrected (HTS, j 40 A/mm²)",
                 band_hi="expectation high iota: 15–22 m", band_dk="expectation DK8s6qwo: 24–30 m", raster="stage-0 grid limit (30 m)",
                 lf="peak field at conductor, strongest coil, at B0 of the balance [T]", lim="HTS limit 20 T (tool assumption)",
                 f2t="K2b: convergence per shape (j 40 A/mm²)", rd="round", kb="k_B actual = B_conductor,max / B0", band_kb="expectation k_B DK8s6qwo: 2.8–3.2",
                 f3t="K2b: variant j 25 A/mm² vs 40 A/mm² (assumption)", j40="j 40", j25="j 25", band_j="expectation j25: R0 10–20 % smaller",
                 dR="ΔR0 to previous round [m]", tol="convergence criterion |ΔR0| < 0.2 m", rr="round")}


def rahmen(fig, sp, titel):
    fig.suptitle(titel + "\n" + T[sp]["kg"], fontsize=11)
    fig.text(0.5, 0.005, T[sp]["fuss"].format(d=datum), ha="center", fontsize=6.5, color="0.4")


cm = plt.cm.tab10(np.arange(10))
for sp in ("de", "en"):
    t = T[sp]
    # ---- Bild 1
    fig, ax = plt.subplots(1, 2, figsize=(16, 6.4), gridspec_kw=dict(width_ratios=[1.35, 1]))
    a = ax[0]; x = np.arange(len(ORDER)); w = 0.27
    for k_, i8 in enumerate(ORDER):
        rs = runden(i8, "j40"); v = vorher(i8)["R0_m"]
        a.bar(k_ - w, v, w, color="0.65")
        if len(rs) >= 2 and rs[1].get("machbar"):
            a.bar(k_, rs[1]["R0_m"], w, color="tab:blue")
        else:
            a.text(k_, 1, "n.m." if sp == "de" else "n.f.", ha="center", fontsize=7, color="tab:blue")
        feas = [r for r in rs if r.get("machbar")]
        lastr = feas[-1]
        if lastr["runde"] > 2 or len(rs) < 2 or not rs[1].get("machbar"):
            a.bar(k_ + w, lastr["R0_m"], w, color="tab:red")
            a.text(k_ + w, lastr["R0_m"] + 0.4, f"{lastr['R0_m']:.0f}", ha="center", fontsize=6.5, rotation=90)
        elif lastr["runde"] == 2:
            a.text(k_, rs[1]["R0_m"] + 0.4, f"{rs[1]['R0_m']:.0f}", ha="center", fontsize=6.5, rotation=90)
        a.text(k_ - w, v + 0.4, f"{v:.0f}", ha="center", fontsize=6.5, rotation=90)
        if not rs[-1].get("machbar"):
            a.text(k_ + w, 47.5, "✕", ha="center", color="k", fontsize=9)
    from matplotlib.patches import Patch
    a.axhspan(15, 22, xmin=0.3, xmax=1, color="tab:green", alpha=0.18)
    a.text(len(ORDER) - 0.5, 12.5, t["band_hi"], ha="right", fontsize=8, color="tab:green")
    a.axhspan(24, 30, xmin=0, xmax=0.1, color="tab:orange", alpha=0.3); a.text(-0.45, 30.4, t["band_dk"], fontsize=8, color="tab:orange")
    a.axhline(30, color="k", ls="--", lw=1); a.text(len(ORDER) - 0.5, 31, t["raster"], ha="right", fontsize=8)
    a.set_xticks(x); a.set_xticklabels(ORDER, rotation=35, ha="right", fontsize=8); a.set_ylabel(t["R0"]); a.set_ylim(0, 50); a.grid(alpha=0.3, axis="y")
    a.legend(handles=[Patch(color="0.65", label=t["vor"]), Patch(color="tab:blue", label=t["r2"]), Patch(color="tab:red", label=t["last"]),
                      plt.Line2D([], [], color="k", marker="x", ls="", label=t["nm"])], fontsize=7.5, loc="upper right", bbox_to_anchor=(1.0, 0.88)); a.set_title(t["f1t"], fontsize=10)
    a = ax[1]
    for k_, i8 in enumerate(ORDER):
        rs = [r for r in runden(i8, "j40") if r.get("machbar")]
        a.bar(k_ - 0.2, rs[0]["B_leiter_bei_B0_bilanz_T"], 0.38, color="0.65")
        a.bar(k_ + 0.2, rs[-1]["B_leiter_bei_B0_bilanz_T"], 0.38, color="tab:red" if len(rs) > 1 else "0.65")
    a.axhline(20, color="r", ls="--"); a.text(len(ORDER) - 0.5, 20.4, t["lim"], ha="right", color="r", fontsize=8)
    a.axhspan(20, 45, color="r", alpha=0.08)
    a.set_xticks(x); a.set_xticklabels(ORDER, rotation=35, ha="right", fontsize=8); a.set_ylim(0, 45); a.set_ylabel(t["lf"], fontsize=8); a.grid(alpha=0.3, axis="y")
    a.set_title(("grau: B-078-Größe, rot: letzte machbare Runde" if sp == "de" else "grey: B-078 size, red: last feasible round"), fontsize=9)
    rahmen(fig, sp, t["f1t"]); fig.tight_layout(rect=(0, 0.025, 1, 0.92)); fig.savefig(B / f"k2b_R0_vorher_nachher_{sp}.png", dpi=130); plt.close(fig)
    # ---- Bild 2
    fig, ax = plt.subplots(1, 3, figsize=(17, 5.8))
    for k_, i8 in enumerate(ORDER):
        rs = runden(i8, "j40"); fe = [r for r in rs if r.get("machbar")]
        ax[0].plot([r["runde"] for r in fe], [r["R0_m"] for r in fe], "o-", color=cm[k_], label=i8, ms=4)
        ax[1].plot([r["runde"] for r in fe], [r["k_B_echt"] for r in fe], "o-", color=cm[k_], ms=4)
        d = [(r["runde"], r["dR0_zur_vorrunde_m"]) for r in fe if r.get("dR0_zur_vorrunde_m") is not None]
        if d:
            ax[2].plot(*zip(*d), "o-", color=cm[k_], ms=4)
        if not rs[-1].get("machbar"):
            ax[0].plot(rs[-1]["runde"], 47, "x", color=cm[k_])
    ax[0].axhline(30, color="k", ls="--", lw=1); ax[0].text(1.0, 30.6, t["raster"], fontsize=8)
    ax[0].axhspan(15, 22, color="tab:green", alpha=0.15); ax[0].text(1.0, 15.3, t["band_hi"], fontsize=8, color="tab:green")
    ax[0].set_ylabel(t["R0"]); ax[0].legend(fontsize=6.5, ncol=2, loc="upper left", bbox_to_anchor=(0, 0.92))
    ax[1].axhspan(2.8, 3.2, color="tab:orange", alpha=0.3); ax[1].text(1.0, 3.25, t["band_kb"], fontsize=8, color="tab:orange"); ax[1].set_ylabel(t["kb"])
    ax[2].axhspan(-0.2, 0.2, color="tab:green", alpha=0.35); ax[2].text(2.0, 0.6, t["tol"], fontsize=8, color="tab:green"); ax[2].set_ylabel(t["dR"])
    for q in ax:
        q.set_xlabel(t["rd"]); q.grid(alpha=0.3); q.set_xticks(range(1, 7))
    ax[0].set_title(t["R0"], fontsize=9); ax[1].set_title("k_B", fontsize=9); ax[2].set_title("ΔR0", fontsize=9)
    rahmen(fig, sp, t["f2t"]); fig.tight_layout(rect=(0, 0.025, 1, 0.9)); fig.savefig(B / f"k2b_konvergenz_{sp}.png", dpi=130); plt.close(fig)
    # ---- Bild 3
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.6))
    for q, rn in zip(ax, (1, 2)):
        for k_, i8 in enumerate(["DK8s6qwo", "DZrUR4dA", "DGozX5fj"]):
            r40 = [r for r in runden(i8, "j40") if r["runde"] == rn and r.get("machbar")]
            r25 = [r for r in runden(i8, "j25") if r["runde"] == rn and r.get("machbar")]
            if r40:
                q.bar(k_ - 0.2, r40[0]["R0_m"], 0.38, color="tab:blue", label=t["j40"] if k_ == 0 else None)
                q.plot([k_ - 0.2 + 0.0], [r40[0]["R0_m"]], alpha=0)
                q.fill_between([k_ + 0.0, k_ + 0.4], 0.8 * r40[0]["R0_m"], 0.9 * r40[0]["R0_m"], color="tab:green", alpha=0.3,
                               label=t["band_j"] if k_ == 0 else None)
            if r25:
                q.bar(k_ + 0.2, r25[0]["R0_m"], 0.38, color="tab:red", alpha=0.0 if False else 0.9, label=t["j25"] if k_ == 0 else None)
                q.text(k_ + 0.2, r25[0]["R0_m"] + 0.5, f"{r25[0]['R0_m']:.1f}", ha="center", fontsize=8)
            if r40:
                q.text(k_ - 0.2, r40[0]["R0_m"] + 0.5, f"{r40[0]['R0_m']:.1f}", ha="center", fontsize=8)
        q.set_xticks(range(3)); q.set_xticklabels(["DK8s6qwo", "DZrUR4dA", "DGozX5fj"]); q.set_ylabel(t["R0"]); q.grid(alpha=0.3, axis="y")
        q.set_title(f"{t['rr']} {rn}" + (" (j25: Start f_I 1, k_B 2)" if rn == 1 and False else ""), fontsize=9); q.legend(fontsize=8)
    fig.text(0.5, 0.93, ("DK8s6qwo: j40 Runde 1 startet mit f_I 1,164 / k_B 3,31 (K2-Werte, Raster bis 45 m), j25 mit 1 / 2 — nicht gleich" if sp == "de" else "DK8s6qwo: j40 round 1 starts with f_I 1.164 / k_B 3.31 (K2 values, grid to 45 m), j25 with 1 / 2 — not equal"), ha="center", fontsize=8, color="0.3")
    rahmen(fig, sp, t["f3t"]); fig.tight_layout(rect=(0, 0.025, 1, 0.9)); fig.savefig(B / f"k2b_j25_{sp}.png", dpi=130); plt.close(fig)
print("fertig", sorted(p.name for p in B.glob("*.png")))
