"""Bild zu spulen_spline: links Feldfehler über größter Verschiebung je Methode, rechts Seitenansicht einer Grundspule (CAD-Weg).
Aufruf: python spline_bild.py <spline.json> <bild.png> [spule]"""
import json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

e = json.load(open(sys.argv[1])); i = int(sys.argv[3]) if len(sys.argv) > 3 else 1
fig = plt.figure(figsize=(15, 5.6)); a1 = fig.add_subplot(1, 3, 1)
namen = {"cad": "CAD-Weg: N Punkte + Spline", "splprep": "Glättungsspline", "taubin": "Taubin", "fourier": "Fourier (Bogenlänge)", "savgol": "Savitzky-Golay"}
for j, art in enumerate(namen):
    ms = [m for m in e["methoden"] if m["methode"].startswith(art)]
    a1.plot([m["abweichung_max_m"] for m in ms], [m["Bn_mittel"] for m in ms], "o-", color=f"C{j}", label=namen[art])
    for m in ms:
        a1.annotate(m["methode"].split("_")[1], (m["abweichung_max_m"], m["Bn_mittel"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
a1.axhline(e["original"]["Bn_mittel"], color="k", ls=":", label="Original 1,05e-3")
a1.axhspan(1e-4, 2.512e-3, color="#2ca02c", alpha=.10, zorder=0, label="Zielbereich ≤ 2,5e-3 (Annahme: Bezug DATJ5FC)")   # Nutzer 2026-11-10
a1.axhline(2.512e-3, color="#2ca02c", lw=1, ls="--")
a1.set_ylim(8e-4, 7e-2)
a1.set_xscale("log"); a1.set_yscale("log"); a1.set_xlabel("größte Verschiebung der Spule durch das Glätten, m")
a1.set_ylabel("Feldfehler (kleiner ist besser)"); a1.legend(fontsize=7); a1.grid(alpha=.3, which="both")
a1.set_title("Alle Methoden liegen auf einer Linie:\nwie weit die Spule wandert, bestimmt den Feldfehler", fontsize=9)
g0 = np.asarray(e["original"]["punkte_m"][i]); m0 = g0.mean(0); _, _, vt = np.linalg.svd(g0 - m0)
for k, (idx, titel) in enumerate([((0, 1), "Blick auf die Spulenebene"), ((0, 2), "Seitenansicht (hier die „8“)")]):
    ax = fig.add_subplot(1, 3, 2 + k)
    p = (g0 - m0) @ vt.T; p = np.vstack([p, p[:1]]); ax.plot(p[:, idx[0]], p[:, idx[1]], "k", lw=2.2, label="Original")
    for n, col in zip([32, 16, 8], ["C1", "C2", "C3"]):
        mm = next(m for m in e["methoden"] if m["methode"] == f"cad_{n}")
        q = (np.asarray(mm["punkte_m"][i]) - m0) @ vt.T; q = np.vstack([q, q[:1]])
        ax.plot(q[:, idx[0]], q[:, idx[1]], color=col, lw=1.2, label=f"{n} Punkte, Feldfehler {mm['Bn_mittel']:.1e}")
    ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(f"Grundspule {i+1}: {titel}", fontsize=9); ax.set_xlabel("m")
    if k == 0: ax.legend(fontsize=7)
fig.suptitle("Glätten nach der Rechnung, DATJ5FC (DATENSATZ-Form, unverändert) mit EIGENEN Spulen d100_n5", fontsize=11)
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=110)
