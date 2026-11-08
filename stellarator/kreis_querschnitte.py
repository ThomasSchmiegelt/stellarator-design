"""kreis_querschnitte.py — Querschnitte von Kandidat 3 halb, der flacheren Form (Kreis Durchlauf 2) und DjLe3eL6, wie eine technische Zeichnung.
Aufruf: python -m stellarator.kreis_querschnitte   -> docs/recherche/spulen_suche/kreis/querschnitte.png"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = Path(__file__).resolve().parents[1]
FORMEN = [("Kandidat 3 halb (Durchlauf 1)", R / "sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json", "#2a78d6"),
          ("flachere Form (Durchlauf 2)", R / "sim/kette_k3/kreis2/form_misch91.json", "#eb6834"),
          ("DjLe3eL6 (Proxima, mit Spulen)", R / "sim/kette_k3/satz_A085/boundary.json", "#1baf7a")]


def rz(f, phi, th):
    rc, zs, nfp = np.array(f["r_cos"]), np.array(f["z_sin"]), f["n_field_periods"]
    nt = (rc.shape[1] - 1) // 2; Rr = np.zeros_like(th); Z = np.zeros_like(th)
    for m in range(rc.shape[0]):
        for j in range(rc.shape[1]):
            n = j - nt; a = m * th - n * nfp * phi
            Rr += rc[m, j] * np.cos(a); Z += zs[m, j] * np.sin(a)
    return Rr, Z


th = np.linspace(0, 2 * np.pi, 400)
fig, ax = plt.subplots(len(FORMEN), 7, figsize=(15, 12), facecolor="#fcfcfb")
for i, (name, p, c) in enumerate(FORMEN):
    f = json.loads(p.read_text()); nfp = f["n_field_periods"]; R00 = f["r_cos"][0][(len(f["r_cos"][0]) - 1) // 2]
    for k, t in enumerate(np.linspace(0, 0.5, 7)):              # halbe Periode: von der Mitte des Bandes bis zur Symmetrieebene
        phi = t * 2 * np.pi / nfp; Rr, Z = rz(f, phi, th); A = ax[i, k]
        A.fill(Rr / R00, Z / R00, color=c, alpha=0.25, lw=0); A.plot(Rr / R00, Z / R00, color=c, lw=2)
        A.set_aspect("equal"); A.set_xlim(0.6, 1.4); A.set_ylim(-1.0, 1.0); A.axhline(0, color="#52514e", lw=0.6, ls=":"); A.grid(color="#e6e5e0", lw=0.6)
        A.axvline(1, color="#52514e", lw=0.6, ls=":"); A.set_facecolor("#fcfcfb")
        if i == 0:
            A.set_title(f"Schnitt {k + 1}", fontsize=9)
        A.text(0.62, 0.9, f"{t * 360 / nfp:.1f}°", fontsize=8, color="#52514e")
        if k == 0:
            A.set_ylabel(name + f"\nnfp {nfp}", fontsize=9)
fig.suptitle("Querschnitte über eine halbe Periode (R und z geteilt durch den Hauptradius, gleicher Maßstab)", fontsize=12, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(R / "docs/recherche/spulen_suche/kreis/querschnitte.png", dpi=120)
