"""modell_bilder.py — Bilder der Stellarator-Modelle (pyvista offscreen, gleicher Massstab).
  .venv-opt/bin/python stellarator/modell_bilder.py <modell_dir_k3> <modell_dir_datj> <bild_dir>"""
import sys, json
from pathlib import Path
import numpy as np, pyvista as pv
pv.OFF_SCREEN = True

TITEL = {"k3_halb": "Kandidat 3 halb (eigene Form, nfp 2)", "datj5fc": "DATJ5FC (Datensatzform, unveraendert, nfp 4)"}
HERKUNFT = "Gefaess 0,15 bis 0,25 m ueber Plasma: ANNAHME | Rohr d = 0,852 m, a = 1,80 m | Thomas Schmiegelt"


def lade(d):
    d = Path(d); return [pv.read(str(d / f)) for f in ("plasma.stl", "gefaess.stl", "spulen.stl")]


def szene(pl, m, schnitt=False, vessel_op=0.35):
    plasma, gef, sp = m
    if schnitt:
        # Viertel (x>0,y>0 -> Quadrant) herausnehmen: Clip mit zwei Ebenen
        def viertel(mesh, cap=True):
            f = (lambda m, n, inv: m.clip_closed_surface(normal=n, origin=(0, 0, 0))) if cap else None
            if cap:
                a = mesh.clip_closed_surface(normal=(-1, 0, 0), origin=(0, 0, 0))            # x<0 bleibt
                c = mesh.clip_closed_surface(normal=(1, 0, 0), origin=(0, 0, 0)).clip_closed_surface(normal=(0, -1, 0), origin=(0, 0, 0))  # x>0,y<0
            else:
                a = mesh.clip(normal=(1, 0, 0), origin=(0, 0, 0), invert=False)
                c = mesh.clip(normal=(1, 0, 0), origin=(0, 0, 0), invert=True).clip(normal=(0, 1, 0), origin=(0, 0, 0), invert=False)
            return a + c
        gef, plasma, sp = viertel(gef), viertel(plasma), viertel(sp, cap=False)
    pl.add_mesh(sp, color="#b87333", smooth_shading=True, opacity=0.35 if schnitt else 0.45)
    pl.add_mesh(gef, color="#9a9a9a", opacity=0.5 if not schnitt else 0.8, smooth_shading=True)
    pl.add_mesh(plasma, color="#ff5a2a", opacity=0.55 if not schnitt else 0.9, smooth_shading=True)


def bild(m, name, pfad, schnitt, rng, cam):
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1100)); pl.set_background("white")
    szene(pl, m, schnitt)
    c = np.array(rng["c"]); r = rng["r"]
    v = np.array(cam) / np.linalg.norm(cam)
    pl.camera_position = [tuple(c + v * r * 6), tuple(c), (0, 0, 1)]
    pl.camera.parallel_projection = True; pl.camera.parallel_scale = r * 1.05
    pl.add_axes() if False else None
    pl.show_grid(bounds=(-r, r, -r, r, -r, r), color="lightgray", font_size=8, xtitle="x [m]", ytitle="y [m]", ztitle="z [m]") if False else None
    pl.add_text(TITEL[name] + (" - Viertel aufgeschnitten" if schnitt else ""), position="upper_left", font_size=13, color="black")
    pl.add_text(HERKUNFT, position="lower_left", font_size=8, color="dimgray")
    pl.add_text("orange-rot: Plasma | grau: Gefaess | kupfer: Spulenrohre | Parallelprojektion, gleicher Massstab", position="lower_right", font_size=8, color="dimgray")
    pl.screenshot(str(pfad)); pl.close()


if __name__ == "__main__":
    dk, dd, out = sys.argv[1:4]; out = Path(out); out.mkdir(parents=True, exist_ok=True)
    M = {"k3_halb": lade(dk), "datj5fc": lade(dd)}
    rmax = max(np.abs(M[k][2].points).max() for k in M)
    rng = {"c": (0, 0, 0), "r": rmax}
    for k, m in M.items():
        bild(m, k, out / f"{k}_ring.png", False, rng, (0.55, -0.75, 0.55))
        bild(m, k, out / f"{k}_viertel.png", True, rng, (0.7, 0.7, 0.55))
    # Vergleich
    pl = pv.Plotter(shape=(1, 2), off_screen=True, window_size=(2400, 1100)); pl.set_background("white")
    for i, k in enumerate(M):
        pl.subplot(0, i); szene(pl, M[k], False)
        v = np.array((0.55, -0.75, 0.55)); v /= np.linalg.norm(v)
        pl.camera_position = [tuple(v * rmax * 6), (0, 0, 0), (0, 0, 1)]
        pl.camera.parallel_projection = True; pl.camera.parallel_scale = rmax * 1.12
        pl.add_text(TITEL[k], position="upper_left", font_size=12, color="black")
        pl.add_text("gleicher Massstab (beide Bilder gleiche Kamera)", position="lower_left", font_size=8, color="dimgray")
    pl.subplot(0, 1); pl.add_text(HERKUNFT, position="lower_right", font_size=7, color="dimgray")
    pl.screenshot(str(out / "vergleich_beide.png")); pl.close()
