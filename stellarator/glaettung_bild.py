"""Bild zu spulen_glaetten: je Grundspule Ansicht auf die beste Ebene und Seitenansicht, Original gegen gekappte Ordnungen.
Aufruf: python glaettung_bild.py <glaettung.json> <bild.png> [ordnungen, z.B. 7,6,5]"""
import json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

e = json.load(open(sys.argv[1])); ords = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "7,6,5").split(",")]
st = {s["ordnung"]: s for s in e["stufen"]}; n = len(st[7]["punkte_m"])
fig, ax = plt.subplots(2, n, figsize=(3.3 * n, 6.6))
for i in range(n):
    g0 = np.asarray(st[7]["punkte_m"][i]); m = g0.mean(0); _, _, vt = np.linalg.svd(g0 - m)
    for o, col in zip(ords, ["k", "C3", "C0", "C2"]):
        g = np.asarray(st[o]["punkte_m"][i]) - m; p = g @ vt.T; g = np.vstack([p, p[:1]])
        lab = f"Ordnung {o}" + (" (Original)" if o == 7 else "")
        ax[0, i].plot(g[:, 0], g[:, 1], color=col, lw=1.6 if o == 7 else 1, label=lab)
        ax[1, i].plot(g[:, 0], g[:, 2], color=col, lw=1.6 if o == 7 else 1)
    b = st[7]["spulen"][i]
    ax[0, i].set_title(f"Grundspule {i+1}\nR_min {b['biegeradius_min_m']:.2f} m, Höhe {b['aus_ebene_m']:.1f} m", fontsize=9)
    for a in ax[:, i]: a.set_aspect("equal"); a.grid(alpha=.3)
    ax[1, i].set_xlabel("m")
ax[0, 0].set_ylabel("Blick auf die Spulenebene, m"); ax[1, 0].set_ylabel("Seitenansicht (Höhe aus der Ebene), m")
ax[0, 0].legend(fontsize=7)
fig.suptitle("Spulen d100_n5 (EIGENE Spulen) für DATJ5FC (DATENSATZ-Form, unverändert): Fourier-Ordnung kappen", fontsize=11)
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=110)
