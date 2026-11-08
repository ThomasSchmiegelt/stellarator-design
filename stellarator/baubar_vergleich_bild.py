"""Vergleich Grundspulen (Ordnung 7) mehrerer Sätze: Draufsicht auf beste Ebene und Seitenansicht.
Aufruf: python baubar_vergleich_bild.py <bild.png> <titel> <name=glaettung.json> ..."""
import json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

saetze = [(a.split("=")[0], json.load(open(a.split("=")[1]))["stufen"][0]) for a in sys.argv[3:]]
n = len(saetze[0][1]["punkte_m"]); fig, ax = plt.subplots(2, n, figsize=(3.3 * n, 6.6))
for i in range(n):
    for (name, st), col in zip(saetze, ["k", "C1", "C0", "C3"]):
        g = np.asarray(st["punkte_m"][i]); m = g.mean(0); _, _, vt = np.linalg.svd(g - m)
        p = (g - m) @ vt.T; p = np.vstack([p, p[:1]]); b = st["spulen"][i]
        ax[0, i].plot(p[:, 0], p[:, 1], color=col, lw=1.2, label=f"{name}: Achter Seite {b['achter_seite']}, Höhe {b['aus_ebene_m']:.1f} m")
        ax[1, i].plot(p[:, 0], p[:, 2], color=col, lw=1.2)
    ax[0, i].set_title(f"Grundspule {i+1}", fontsize=9); ax[0, i].legend(fontsize=6, loc="lower center")
    for a in ax[:, i]: a.set_aspect("equal"); a.grid(alpha=.3)
    ax[1, i].set_xlabel("m")
ax[0, 0].set_ylabel("Blick auf die Spulenebene, m"); ax[1, 0].set_ylabel("Seitenansicht, m")
fig.suptitle(sys.argv[2], fontsize=10); fig.tight_layout(); fig.savefig(sys.argv[1], dpi=110)
