"""kuehlung_schnittbild.py — Querschnitt durch ein FluidX3D-Stroemungsfeld des Kuehlsegments (Bild fuer den Bericht).

    .venv/bin/python -m stellarator.kuehlung_schnittbild <name> <bild.png> <phi_grad>

Alle Wasserzellen in der Ebene phi = phi_grad (eine Zelle dick) als Punkte, Farbe = |v| logarithmisch;
rechts ein Ausschnitt der plasmanahen Gyroid-Schicht.
"""
import json, numpy as np, sys
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from stellarator.kuehlung_cfd import lese_feld
from stellarator.kuehlung_segment import WURZEL
o = WURZEL / sys.argv[1]; F = lese_feld(o); x, u = F["x"], F["u"]; dx = F["fall"]["dx_m"]
phi_m = np.radians(float(sys.argv[3]))
n = np.array([-np.sin(phi_m), np.cos(phi_m)])            # Normale der Ebene phi = phi_m
d = x[:, 0] * n[0] + x[:, 1] * n[1]
m = (np.abs(d) < dx / 2) & (x[:, 0] * np.cos(phi_m) + x[:, 1] * np.sin(phi_m) > 0)
R = x[m, 0] * np.cos(phi_m) + x[m, 1] * np.sin(phi_m); z = x[m, 2]; v = np.linalg.norm(u[m], axis=1)
print(m.sum(), "Zellen")
fig, ax = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw={"width_ratios": [1.1, 1]})
for a, (xl, zl) in zip(ax, (((3.8, 13.4), (-3.1, 3.1)), ((9.7, 10.9), (-2.25, -1.75)))):
    sc = a.scatter(R, z, c=np.clip(v, 1e-3, None), s=(2.0 if a is ax[0] else 22), marker="s", lw=0,
                   cmap="turbo", norm=LogNorm(1e-3, 1.0), rasterized=True)
    a.set_xlim(*xl); a.set_ylim(*zl); a.set_aspect("equal"); a.set_xlabel("R [m]"); a.set_ylabel("z [m]")
    a.set_facecolor("#d9dce2")
ax[0].add_patch(plt.Rectangle((9.7, -2.25), 1.2, 0.5, fill=False, ec="k", lw=1.2))
ax[0].set_title(f"{sys.argv[1]}: Querschnitt bei φ = {sys.argv[3]}° (Wasserzellen, grau = Stahl/außen)", fontsize=11)
ax[1].set_title("Ausschnitt (Rahmen): Gyroid-Schicht an der Plasmaseite", fontsize=11)
fig.colorbar(sc, ax=ax, label="Geschwindigkeit |v| [m/s]", shrink=0.85)
plt.savefig(sys.argv[2], dpi=110, bbox_inches="tight")
