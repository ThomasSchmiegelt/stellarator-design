"""kreis_bilder.py — Vergleichsbild der Kreis-Durchläufe: Nettokraft je Spule. Aufruf: python -m stellarator.kreis_bilder"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = Path(__file__).resolve().parents[1]
S = [("Kandidat 3 halb, Satz ohne Bauraum (d085_n10_lr)", R / "sim/kette_k3/stage2/satz_d085_n10_lr/kraefte.json", "#1baf7a"),
     ("Durchlauf 1: Kandidat 3 halb, im Bauraum", R / "sim/kette_k3/stage2/satz_d100_n10_lr_s56/kraefte.json", "#2a78d6"),
     ("Durchlauf 2: flachere Form, im Bauraum", R / "sim/kette_k3/kreis2/stage2/satz_d100_n10_lr_s56/kraefte.json", "#eb6834")]
fig, ax = plt.subplots(figsize=(10, 4.6), facecolor="#fcfcfb"); ax.set_facecolor("#fcfcfb")
b = 0.25; x = np.arange(1, 11)
for i, (n, p, c) in enumerate(S):
    v = [math.hypot(*z["F_netto_MN"]) for z in json.loads(p.read_text())["basisspulen"]]
    ax.bar(x + (i - 1) * b, v, b * 0.88, color=c, label=n)
    k = int(np.argmax(v)); ax.text(x[k] + (i - 1) * b, v[k] + 25, f"{v[k]:.0f}", ha="center", fontsize=9, color="#0b0b0b")
ax.axhline(792, color="#52514e", lw=1, ls="--"); ax.text(10.45, 810, "DPrcxq66: 792 MN (Vergleichswert, keine Grenze)", ha="right", fontsize=9, color="#52514e")
ax.set_xticks(x); ax.set_xlabel("Basisspule (1 bis 10 je halbe Periode)", color="#52514e"); ax.set_ylabel("Nettokraft je Spule in MN", color="#52514e")
ax.set_title("Nettokraft je Spule: Der Spulensatz wirkt so stark wie die Plasmaform", loc="left", fontsize=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e6e5e0", lw=0.7); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 0.98))
ax.set_ylim(0, 1950)
fig.tight_layout(); fig.savefig(R / "docs/recherche/spulen_suche/kreis/nettokraft.png", dpi=130)
