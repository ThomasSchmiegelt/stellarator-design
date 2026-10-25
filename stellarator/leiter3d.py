"""leiter3d.py — ein Stueck CICC-Leiter (W7-X-artig) in 3D: wo der Strom fliesst.

  .venv/bin/python -m stellarator.leiter3d [--laenge 0.10] [--oeffnen]

Anschauungsmodell, schematisch, Masse angelehnt an die W7-X-Angaben (vor Veroeffentlichung pruefen):
  Aluminiummantel 16 x 16 mm mit runder Bohrung | 243 Straenge Durchmesser 0,57 mm, verdrillt |
  Hohlraum ~37 % (ueberkritisches Helium) | je Strang NbTi-Filamente in Kupfermatrix (Cu : NbTi ~ 2,6).
Strom: im Betrieb fast vollstaendig im NbTi (widerstandslos); Kupfer nur beim Quench (Stabilisator);
Aluminium und Helium tragen keinen Strom (Mantel: Form, Kraft, Heliumdichtung).
Darstellung: Mantel und Kabel zur Haelfte aufgeschnitten; an der Stirnseite jeder Strang mit
NbTi-Bereich (tuerkis) in Kupfer; daneben ein Strang stark vergroessert mit einzelnen Filamenten.
Ausgabe sim/stellarator/leiter3d/: leiter3d.png, leiter3d.glb (Farben, fuer Blender), leiter3d.vtm.
"""
from __future__ import annotations
import argparse, subprocess
from pathlib import Path
import numpy as np
import pyvista as pv

from .lauf import PROJEKT

MM = 1e-3
FARBEN = {"Aluminiummantel": "#c9ced6", "Kupfermatrix (Stabilisator)": "#c46f2e", "NbTi-Supraleiter": "#1fa3a3",
          }


def strangpositionen(n: int, r_max: float) -> np.ndarray:
    """n Punkte gleichmaessig in einem Kreis (Vogel-Spirale)."""
    k = np.arange(n) + 0.5
    r = r_max * np.sqrt(k / n); w = k * np.pi * (3 - np.sqrt(5))
    return np.c_[r * np.cos(w), r * np.sin(w)]


def mantel(kante: float, r_bohrung: float, laenge: float, offen: bool) -> pv.PolyData:
    """Quadratrohr mit runder Bohrung, entlang z; offen=True: Viertel herausgeschnitten (x > 0, y > 0)."""
    quad = pv.Box((-kante / 2, kante / 2, -kante / 2, kante / 2, 0, laenge)).triangulate()
    loch = pv.Cylinder(center=(0, 0, laenge / 2), direction=(0, 0, 1), radius=r_bohrung,
                       height=laenge * 1.2, resolution=96).triangulate()
    m = quad.boolean_difference(loch)
    if offen:
        keil = pv.Box((0, kante, 0, kante, laenge * 0.35, laenge * 1.1)).triangulate()
        m = m.boolean_difference(keil)
    return m


def main(argv=None):
    ap = argparse.ArgumentParser(description="CICC-Leiterstueck in 3D (Strompfad)")
    ap.add_argument("--laenge", type=float, default=0.10)
    ap.add_argument("--schlag", type=float, default=0.15, help="Schlaglaenge der Verdrillung [m] (schematisch)")
    ap.add_argument("--oeffnen", action="store_true")
    a = ap.parse_args(argv)
    ordner = PROJEKT / "sim" / "stellarator" / "leiter3d"; ordner.mkdir(parents=True, exist_ok=True)
    kante, d_s, n_s, hohl = 16 * MM, 0.57 * MM, 243, 0.37
    r_s = d_s / 2
    r_b = np.sqrt(n_s * r_s ** 2 / (1 - hohl))                  # Bohrung aus Strangflaeche und Hohlraumanteil
    L = a.laenge
    teile = {k: [] for k in FARBEN}
    teile["Aluminiummantel"].append(mantel(kante, r_b, L, offen=True))
    # Helium: kein eigener Koerper -> die Zwischenraeume zwischen den Straengen (~37 %)
    pos = strangpositionen(n_s, r_b - r_s * 1.05)
    z = np.linspace(0, L, 60)
    for i, (x0, y0) in enumerate(pos):
        w = 2 * np.pi * z / a.schlag                               # verdrillt um die Leiterachse
        pfad = np.c_[x0 * np.cos(w) - y0 * np.sin(w), x0 * np.sin(w) + y0 * np.cos(w), z]
        # vorderer Teil (z < 0,35 L) ganz, hinten nur ausserhalb des aufgeschnittenen Viertels
        sichtbar = (pfad[:, 2] < 0.36 * L) | ~((pfad[:, 0] > 0) & (pfad[:, 1] > 0))
        weg = np.where(~sichtbar)[0]
        if len(weg):                                               # Strang endet am aufgeschnittenen Viertel
            pfad = pfad[: max(2, weg[0] + 1)]
        teile["Kupfermatrix (Stabilisator)"].append(pv.Spline(pfad, len(pfad)).tube(radius=r_s, n_sides=14, capping=True))
        # Stirnseite z = 0: NbTi-Bereich (Flaechenanteil 1/(1+2,6)) als Scheibe knapp vor dem Strang
        teile["NbTi-Supraleiter"].append(pv.Disc(center=(pfad[0, 0], pfad[0, 1], -0.02 * MM), inner=0,
                                                  outer=r_s * np.sqrt(1 / 3.6) * 1.0, normal=(0, 0, -1), c_res=16))
    # Vergroesserter Strang (Faktor 12) neben dem Leiter: Filamente einzeln (Anzahl symbolisch)
    f = 12.0; R = r_s * f; c0 = np.array([kante * 1.6, -kante * 0.2, 0.0])
    teile["Kupfermatrix (Stabilisator)"].append(pv.Cylinder(center=c0 + [0, 0, 0.03], direction=(0, 0, 1),
                                                            radius=R, height=0.06, resolution=96))
    for p in strangpositionen(61, R * 0.72):
        teile["NbTi-Supraleiter"].append(pv.Cylinder(center=c0 + [p[0], p[1], 0.03 - 0.0004], direction=(0, 0, 1),
                                                     radius=R * 0.055, height=0.06, resolution=16))
    mb = pv.MultiBlock()
    for k, v in teile.items():
        mb[k] = pv.merge(v) if len(v) > 1 else v[0]
    mb.save(ordner / "leiter3d.vtm")

    pl = pv.Plotter(off_screen=True, window_size=(1800, 1100)); pl.set_background("white")
    for k, m in zip(mb.keys(), mb):
        pl.add_mesh(m, color=FARBEN[k], smooth_shading=not k.startswith("Alu"), label=k)
    pl.add_legend(bcolor="#3a3a3a", face="rectangle", size=(0.3, 0.2), loc="upper right")
    pl.add_text("CICC-Leiter (W7-X-artig, schematisch): Strom fliesst im NbTi (tuerkis); Kupfer = Stabilisator beim Quench;\n"
                "Aluminiummantel und Helium (Zwischenraeume) tragen keinen Strom.  Daneben: ein Strang 12-fach vergroessert (Filamente symbolisch)",
                font_size=11, color="black")
    pl.camera_position = [(0.05, 0.045, -0.055), (0.006, 0.002, 0.035), (0, 0, 1)]
    pl.reset_camera(); pl.camera.zoom(0.95); pl.reset_camera_clipping_range()
    pl.screenshot(ordner / "leiter3d.png")
    pl.export_gltf(str(ordner / "leiter3d.glb"))
    pl.close()
    print("FERTIG", ordner, f"Bohrung r = {r_b / MM:.2f} mm")
    if a.oeffnen:
        subprocess.Popen(["eog", str(ordner / "leiter3d.png")], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
