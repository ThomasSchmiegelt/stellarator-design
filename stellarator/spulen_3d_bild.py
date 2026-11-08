"""Standbild 3D: Plasma + alle Spulen, mehrere Sätze nebeneinander. Aufruf: python spulen_3d_bild.py <bild.png> <name=satz> ..."""
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import flaeche, lade_satz  # noqa: E402
from simsopt.field import Current, coils_via_symmetries  # noqa: E402

saetze = [a.split("=", 1) for a in sys.argv[2:]]
s = flaeche(Path(saetze[0][1]) / "boundary.json", nphi=120, ntheta=40)
a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0))))); k = 1.8 / a; g = s.gamma() * k
fig = plt.figure(figsize=(6.5 * len(saetze), 6.5))
for j, (name, ordner) in enumerate(saetze):
    ax = fig.add_subplot(1, len(saetze), j + 1, projection="3d")
    ax.plot_surface(g[..., 0], g[..., 1], g[..., 2], color="#e8662f", alpha=0.85, linewidth=0, shade=True)
    basis, I, nfp = lade_satz(ordner)
    for c in coils_via_symmetries(basis, [Current(float(x)) for x in I], nfp, True):
        p = c.curve.gamma() * k; p = np.vstack([p, p[:1]]); ax.plot(p[:, 0], p[:, 1], p[:, 2], color="#1f3b73", lw=1.2)
    ax.set_title(name, fontsize=11); ax.set_box_aspect((1, 1, 0.35)); ax.view_init(35, 30); ax.set_axis_off()
fig.suptitle("Plasma DATJ5FC (DATENSATZ-Form, unverändert, orange) mit EIGENEN Spulen (blau)", fontsize=12)
fig.tight_layout(); fig.savefig(sys.argv[1], dpi=100)
