"""modell_ansicht.py — Kuehlsegment interaktiv ansehen (PyVista-Fenster: Maus drehen, Rad zoomen, r = zuruecksetzen).

    .venv/bin/python -m stellarator.modell_ansicht e1

Stahl halbtransparent, Wasserraum blau, Rohrenden markiert (Eintritt gruen, Austritt rot).
Taste 's' blendet den Stahl ein/aus.
"""
import json, sys
import numpy as np
import pyvista as pv
from .kuehlung_segment import WURZEL

o = WURZEL / (sys.argv[1] if len(sys.argv) > 1 else "e1")
s = pv.read(o / "stahl.stl").scale(1e-3); w = pv.read(o / "wasser.stl").scale(1e-3)
lage = json.loads((o / "auslegung.json").read_text())["lage"]
pl = pv.Plotter(title=f"Kuehlsegment {o.name}: Stahl grau, Wasser blau", window_size=(1600, 1000))
pl.set_background("white")
a_s = pl.add_mesh(s, color="#b8bec6", opacity=0.3, smooth_shading=True)
pl.add_mesh(w, color="#2a7fd4", smooth_shading=True, specular=0.4)
for k, f in (("ein", "green"), ("aus", "red")):
    pl.add_mesh(pv.Sphere(radius=0.15, center=lage["rohre"][k]["ende_m"]), color=f)
pl.add_text("Maus: drehen | Rad: zoomen | s: Stahl an/aus | Eintritt gruen, Austritt rot", font_size=10, color="black")
pl.add_key_event("s", lambda: (a_s.SetVisibility(not a_s.GetVisibility()), pl.render()))
c = np.array(w.center); e_r = c * np.array([1, 1, 0]) / np.hypot(c[0], c[1])
pl.camera.focal_point = c.tolist(); pl.camera.position = (c + 14 * e_r + [0, 0, 6] + 5 * np.cross([0, 0, 1], e_r)).tolist()
pl.camera.up = (0, 0, 1)
pl.show()
