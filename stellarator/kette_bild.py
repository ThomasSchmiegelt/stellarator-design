"""Bild der Kette Plasma -> Maschine mit Stand je Glied (2026-11-07). Aufruf: python -m stellarator.kette_bild"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FARBE = {"belegt": "#2a7ab0", "teilweise": "#e6a000", "fehlt": "#c0392b"}
G = [
    ("1 Plasmaform", "80 Koeffizienten\n(Wellen der Fläche)", "belegt"),
    ("2 Feld, iota, QI", "VMEC++ rechnet\naus der Form", "belegt"),
    ("3 Spulenform", "Werkzeuge da, eigene Spulen\nnur für DjLe3eL6 (A085)", "teilweise"),
    ("4 Ströme S1–S5", "Verhältnis ändert QI\n(nur ±5 % geprüft)", "teilweise"),
    ("5 Freie Grenze", "Plasma im Spulenfeld\n(konvergiert kaum)", "teilweise"),
    ("6 Tragwerk, Spannung", "nur für den\nvorhandenen Spulensatz", "teilweise"),
    ("7 Kühlung, Verguss", "Kühlsegment bearbeitet,\nVerguss geplant", "teilweise"),
]
fig, ax = plt.subplots(figsize=(13, 5.2)); ax.set_xlim(0, 14); ax.set_ylim(0, 6); ax.axis("off")
pos = [(0.4, 3.6), (3.9, 3.6), (7.4, 3.6), (10.9, 3.6), (2.2, 0.7), (5.9, 0.7), (9.6, 0.7)]
for (t, s, st), (x, y) in zip(G, pos):
    ax.add_patch(FancyBboxPatch((x, y), 3.0, 1.7, boxstyle="round,pad=0.05", fc="white", ec=FARBE[st], lw=3))
    ax.text(x + 1.5, y + 1.25, t, ha="center", va="center", fontsize=11, weight="bold")
    ax.text(x + 1.5, y + 0.65, s, ha="center", va="center", fontsize=9)
    ax.text(x + 1.5, y + 0.12, {"belegt": "belegt", "teilweise": "teilweise", "fehlt": "FEHLT"}[st], ha="center", fontsize=9, color=FARBE[st], weight="bold")
pf = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
for a, b in pf:
    xa, ya = pos[a]; xb, yb = pos[b]
    if ya == yb:
        ax.annotate("", xy=(xb, yb + 0.85), xytext=(xa + 3.0, ya + 0.85), arrowprops=dict(arrowstyle="->", lw=2))
    else:
        ax.annotate("", xy=(xb + 1.5, yb + 1.75), xytext=(xa + 1.5, ya - 0.05), arrowprops=dict(arrowstyle="->", lw=2, connectionstyle="arc3,rad=0.1"))
ax.text(7, 5.75, "Von der Plasmaform zur Maschine: Stand je Glied", ha="center", fontsize=14, weight="bold")
ax.text(0.2, 0.05, "Rahmen blau = belegt, orange = teilweise, rot = fehlt. Die Wertung der Challenge misst nur Glied 1–2.", fontsize=8.5)
fig.savefig("docs/recherche/spulen_suche/kette_plasma_maschine.png", dpi=130, bbox_inches="tight")
