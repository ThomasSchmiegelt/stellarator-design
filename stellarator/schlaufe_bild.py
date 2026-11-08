"""Bild zu spulen_schlaufe: je Grundspule Seitenansicht (fester Rahmen) Original, weglassen, ausdünnen + Stützpunkte.
Aufruf: python schlaufe_bild.py <schlaufe.json> <bild.png>"""
import json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

e = json.load(open(sys.argv[1])); n = len(e["original"]["punkte_m"])
fig, ax = plt.subplots(2, n, figsize=(3.4 * n, 6.4))
for i in range(n):
    g0 = np.asarray(e["original"]["punkte_m"][i]); m = g0.mean(0); _, _, vt = np.linalg.svd(g0 - m)
    for r, (idx, ttl) in enumerate([((0, 1), "Draufsicht"), ((0, 2), "Seitenansicht")]):
        p = (g0 - m) @ vt.T; p = np.vstack([p, p[:1]])
        ax[r, i].plot(p[:, idx[0]], p[:, idx[1]], "k", lw=2, label=f"Original {e['original']['Bn_mittel']:.1e}")
        for mo, col in zip(e["modi"], ["C3", "C0"]):
            q = (np.asarray(mo["punkte_m"][i]) - m) @ vt.T; q = np.vstack([q, q[:1]])
            st = (np.asarray(mo["stuetz_m"][i]) - m) @ vt.T
            ax[r, i].plot(q[:, idx[0]], q[:, idx[1]], color=col, lw=1.1, label=f"{mo['modus']} {mo['Bn_mittel']:.1e}")
            ax[r, i].plot(st[:, idx[0]], st[:, idx[1]], ".", color=col, ms=3)
        ax[r, i].set_aspect("equal"); ax[r, i].grid(alpha=.3); ax[r, i].set_title(f"Grundspule {i+1}: {ttl}", fontsize=9)
ax[0, 0].legend(fontsize=6)
fig.suptitle("Schlaufe weglassen / ausdünnen (CAD-Weg), DATJ5FC (DATENSATZ-Form, unverändert), EIGENE Spulen d100_n5; Punkte = Stützpunkte", fontsize=10)
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=105)
