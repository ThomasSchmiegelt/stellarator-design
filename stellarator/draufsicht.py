"""draufsicht.py — Kuehlsegment von oben (aussen links, Torusmitte rechts) als Bild draufsicht.png.

    .venv/bin/python -m stellarator.draufsicht f4
"""
import json, sys, numpy as np, pyvista as pv
from .kuehlung_segment import WURZEL
o = WURZEL / sys.argv[1]
s = pv.read(o / "stahl.stl").scale(1e-3); w = pv.read(o / "wasser.stl").scale(1e-3)
lage = json.loads((o / "auslegung.json").read_text())["lage"]
pl = pv.Plotter(off_screen=True, window_size=(2000, 900)); pl.set_background("white")
pl.add_mesh(s, color="#b8bec6", opacity=0.3); pl.add_mesh(w, color="#2a7fd4", smooth_shading=True)
for k, f in (("ein", "green"), ("aus", "red")):
    pl.add_mesh(pv.Sphere(radius=0.15, center=lage["rohre"][k]["ende_m"]), color=f)
c = np.array(w.center); e_r = c * [1, 1, 0] / np.hypot(c[0], c[1])
pl.camera.focal_point = c.tolist(); pl.camera.position = (c + [0, 0, 25]).tolist()
e_phi = np.cross([0, 0, 1], e_r); pl.camera.up = (-e_phi).tolist(); pl.camera.parallel_projection = True; pl.reset_camera(); pl.camera.zoom(1.3)
pl.add_text("Draufsicht von oben: aussen links, innen (Torusmitte) rechts; Eintritt gruen, Austritt rot", font_size=11, color="black")
pl.screenshot(o / "draufsicht.png")
