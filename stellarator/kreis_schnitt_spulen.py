"""kreis_schnitt_spulen.py — Querschnitte von Plasma UND Spulen (Spulen als Rohrquerschnitt, 0,85 m bei a = 1,80 m, ANNAHME).
Aufruf: .venv-opt/bin/python -m stellarator.kreis_schnitt_spulen   -> docs/recherche/spulen_suche/kreis/schnitt_spulen.png"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from stellarator.spulen_satz import lade_satz

R = Path(__file__).resolve().parents[1]
K = R / "sim" / "kette_k3"
SAETZE = [("Kandidat 3 halb: EIGENE Form\n(aus Datensatzform Do3Qy, halber Schritt)\nSpulen Durchlauf 1, Feldfehler 2,1e-4", K / "stage2" / "satz_d100_n10_lr_s56", "#2a78d6"),
          ("DjLe3eL6: DATENSATZ-Form, unverändert\n(ConStellaration, auch von Proxima genutzt)\neigene Spulen A085, Feldfehler 6,6e-4", K / "satz_A085", "#1baf7a"),
          ("DATJ5FC: DATENSATZ-Form, unverändert\n(ConStellaration)\nalter Satz Plan B, Feldfehler 5,1e-3", K / "planb" / "stage2" / "satz_d085_n5", "#eb6834")]
A_M, ROHR_M = 1.80, 0.852


def rand(f, phi, th):
    rc, zs, nfp = np.array(f["r_cos"]), np.array(f["z_sin"]), f["n_field_periods"]
    nt = (rc.shape[1] - 1) // 2; Rr = np.zeros_like(th); Z = np.zeros_like(th)
    for m in range(rc.shape[0]):
        for j in range(rc.shape[1]):
            a = m * th - (j - nt) * nfp * phi; Rr += rc[m, j] * np.cos(a); Z += zs[m, j] * np.sin(a)
    return Rr, Z


def kleiner_radius(f):
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False); fl = []
    for phi in np.linspace(0, 2 * np.pi / f["n_field_periods"], 32, endpoint=False):
        Rr, Z = rand(f, phi, th); fl.append(0.5 * abs(np.sum(Rr * np.roll(Z, -1) - np.roll(Rr, -1) * Z)))
    return float(np.sqrt(np.mean(fl) / np.pi))


def schnittpunkte(kurven, phi0):
    out = []
    for X in kurven:
        ph = np.arctan2(X[:, 1], X[:, 0]); d = np.angle(np.exp(1j * (ph - phi0)))
        for i in range(len(X)):
            j = (i + 1) % len(X)
            if d[i] * d[j] < 0 and abs(d[i] - d[j]) < 1.0:
                t = d[i] / (d[i] - d[j]); P = X[i] + t * (X[j] - X[i]); out.append((np.hypot(P[0], P[1]), P[2]))
    return out


def main():
    """Je Basisspule: Spule in Zylinderkoordinaten (R, z) als Schleife, dazu der Plasmaquerschnitt an der mittleren Lage der Spule."""
    th = np.linspace(0, 2 * np.pi, 400)
    fig, ax = plt.subplots(len(SAETZE), 5, figsize=(15, 12.5), facecolor="#fcfcfb")
    for i, (name, o, c) in enumerate(SAETZE):
        f = json.loads((o / "boundary.json").read_text()); nfp = f["n_field_periods"]
        R00 = f["r_cos"][0][(len(f["r_cos"][0]) - 1) // 2]; a = kleiner_radius(f); r_rohr = ROHR_M / 2 * a / A_M
        basis, I, nfp_s = lade_satz(o); assert nfp_s == nfp
        wahl = np.linspace(0, len(basis) - 1, 5).round().astype(int)
        for k, b in enumerate(wahl):
            G = np.asarray(basis[b].gamma()); A = ax[i, k]
            phi = float(np.angle(np.mean(np.exp(1j * np.arctan2(G[:, 1], G[:, 0])))))
            Rc, Zc = np.hypot(G[:, 0], G[:, 1]), G[:, 2]
            Rr, Z = rand(f, phi, th)
            A.fill(Rr / R00, Z / R00, color=c, alpha=0.3, lw=0); A.plot(Rr / R00, Z / R00, color=c, lw=1.6)
            lw_pt = 2 * r_rohr / R00 * 72 * (A.get_window_extent().height / fig.dpi) / 2.35   # Rohrdurchmesser in Punkten (Achse 2,35 hoch)
            A.plot(np.r_[Rc, Rc[:1]] / R00, np.r_[Zc, Zc[:1]] / R00, color="#52514e", lw=max(lw_pt, 1), alpha=0.55, solid_capstyle="round")
            A.plot(np.r_[Rc, Rc[:1]] / R00, np.r_[Zc, Zc[:1]] / R00, color="#0b0b0b", lw=0.6)
            A.set_aspect("equal"); A.set_xlim(0.3, 1.8); A.set_ylim(-0.95, 1.4); A.grid(color="#e6e5e0", lw=0.6); A.set_facecolor("#fcfcfb")
            A.axhline(0, color="#52514e", lw=0.5, ls=":"); A.axvline(1, color="#52514e", lw=0.5, ls=":")
            A.text(0.33, 1.3, f"Spule {b + 1}, um {np.degrees(phi):.1f}°", fontsize=8, color="#52514e")
            if k == 0:
                A.set_ylabel(name + f"\nnfp {nfp}", fontsize=8)
    fig.suptitle("Spulen (grau, Breite = Rohr 0,85 m bei a = 1,80 m) um den Plasmaquerschnitt an ihrer Lage; Spule seitlich auf (R, z) projiziert. Maßstab: Hauptradius = 1",
                 fontsize=11, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(R / "docs/recherche/spulen_suche/kreis/schnitt_spulen.png", dpi=115)


if __name__ == "__main__":
    main()
