"""zeitleiste.py -- Zeitleiste Stellarator-Projekt: Phasen H01-H13 (rekonstruiert) und Zukunft (Annahme).

KI-generiert (Claude Sonnet im Auftrag von Opus, 2026-11-12). Liest historie.json und plan_fusion.py (Liste A).
    python3 pm/plan/zeitleiste.py   ->  pm/plan/zeitleiste.png
"""
import json, math, sys
from datetime import date, timedelta
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER)); import plan_fusion as PF


def addwd(d, n):
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5: n -= 1
    return d


def zukunft_daten():
    """Arbeitstage ab PF.START -> Kalenderdaten (Start-/Endtag je Vorgang)."""
    s0 = date.fromisoformat(PF.START); es, ef, *_ = PF.cpm(PF.A); out = {}
    for i, n, dur, *_ in PF.A:
        a = addwd(s0, math.floor(es[i])); b = addwd(s0, max(math.floor(es[i]), math.ceil(ef[i]) - 1))
        out[i] = (a, b)
    return out


def main():
    h = json.loads((HIER / "historie.json").read_text())["phasen"]; z = zukunft_daten()
    zeilen = [("H", p["id"], p["name"], date.fromisoformat(p["von"]), date.fromisoformat(p["bis"]) + timedelta(days=1), "") for p in h]
    for i, n, dur, *_ in PF.A: zeilen.append(("Z", i, n, z[i][0], z[i][1] + timedelta(days=1), f"{dur:g} AT"))
    fig, ax = plt.subplots(figsize=(17, 12.5))
    for r, (art, i, n, a, b, lab) in enumerate(zeilen):
        farbe = "#1f6fb5" if art == "H" else "#e08a1e"
        ax.barh(r, (b - a).days, left=mdates.date2num(a), height=0.62, color=farbe, edgecolor="black", linewidth=0.6, hatch="" if art == "H" else "//", alpha=0.9 if art == "H" else 0.6)
        x_text = mdates.date2num(b) + 0.3
        ax.text(x_text, r, (n[:70] + ("…" if len(n) > 70 else "")) + (f"  [{lab}, Annahme]" if lab else ""), va="center", fontsize=8)
    ax.set_yticks(range(len(zeilen))); ax.set_yticklabels([f"{i}" for _, i, *_ in zeilen], fontsize=8)
    ax.invert_yaxis(); ax.xaxis_date(); ax.xaxis.set_major_locator(mdates.DayLocator(interval=7)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m."))
    ax.xaxis.set_minor_locator(mdates.DayLocator()); ax.grid(axis="x", which="major", color="#bbb", lw=0.6)
    heute = mdates.date2num(date(2026, 11, 13)); ax.axvline(heute, color="red", lw=1.5); ax.text(heute, -0.9, "Start Zukunft 2026-11-13", color="red", fontsize=8, ha="center")
    ax.set_xlim(mdates.date2num(date(2026, 10, 20)), mdates.date2num(date(2026, 12, 10)))
    ax.set_title("KI-generiert: Zeitleiste Stellarator-Projekt, Vergangenheit 22.10.–12.11.2026 rekonstruiert, Zukunft ab 13.11.2026 geplant", fontsize=12, fontweight="bold")
    ax.legend(handles=[Patch(facecolor="#1f6fb5", edgecolor="black", label="rekonstruiert (aus BEFUNDE, ERINNERUNGEN, Git; Phasen überlappen)"),
                       Patch(facecolor="#e08a1e", edgecolor="black", hatch="//", alpha=0.6, label="geplant (Annahme: Dauern in Arbeitstagen von Opus geschätzt, nicht belegt)")], loc="lower right", fontsize=9)
    fig.text(0.01, 0.005, "KI-generiert (Claude Sonnet, Auftrag Claude Opus, 2026-11-12). Daten: pm/plan/historie.json, pm/plan/plan_fusion.py. Nicht vom Autor freigegeben.", fontsize=8)
    fig.tight_layout(rect=(0, 0.015, 1, 1)); fig.savefig(HIER / "zeitleiste.png", dpi=110); print("geschrieben: pm/plan/zeitleiste.png")


if __name__ == "__main__":
    main()
