"""Nahansicht eine Feldperiode: Plasma + Spulen dieser Periode (Matplotlib, Spulen als Linien, Plasma halbtransparent).
Aufruf: python spulen_3d_nah.py <bild.png> <titel> <satz_ordner>                 -> drei Blickrichtungen
        python spulen_3d_nah.py <bild.png> <titel> <name=satz> <name=satz> ...   -> ein Blick, Sätze nebeneinander"""
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import flaeche, lade_satz  # noqa: E402
from simsopt.field import Current, coils_via_symmetries  # noqa: E402

bild, titel = sys.argv[1:3]; args = sys.argv[3:]
if len(args) == 1 and "=" not in args[0]:
    panels = [(f"Blick: Höhe {el}°, Drehung {az}°", args[0], el, az) for el, az in [(30, 20), (5, 22), (75, 22)]]
else:
    panels = [(a.split("=", 1)[0], a.split("=", 1)[1], 30, 20) for a in args]
ordner = panels[0][1]
basis, I, nfp = lade_satz(ordner); s = flaeche(Path(ordner) / "boundary.json", nphi=240, ntheta=48)
a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0))))); k = 1.8 / a
g = s.gamma() * k; ph = np.arctan2(g[..., 1], g[..., 0]) % (2 * np.pi)
breite = 2 * np.pi / nfp; maske = ph < breite


def kurven_von(o):
    b, I, nfp = lade_satz(o); out = []
    for c in coils_via_symmetries(b, [Current(float(x)) for x in I], nfp, True):
        p = c.curve.gamma() * k; m = np.arctan2(p[:, 1].mean(), p[:, 0].mean()) % (2 * np.pi)
        if m < breite:
            out.append(np.vstack([p, p[:1]]))
    return out


fig = plt.figure(figsize=(5.4 * len(panels), 5.6))
for j, (name, o, el, az) in enumerate(panels):
    ax = fig.add_subplot(1, len(panels), j + 1, projection="3d")
    gg = np.where(maske[..., None], g, np.nan)
    ax.plot_surface(gg[..., 0], gg[..., 1], gg[..., 2], color="#e8662f", alpha=0.35, linewidth=0)
    for i, p in enumerate(kurven_von(o)):
        ax.plot(p[:, 0], p[:, 1], p[:, 2], lw=1.6, color=plt.cm.tab10(i % 10))
    ax.view_init(el, az); ax.set_box_aspect((1, 1, 0.5)); ax.set_axis_off(); ax.set_title(name, fontsize=9)
fig.suptitle(titel, fontsize=11); fig.tight_layout(); fig.savefig(bild, dpi=100)
