"""kuehlsegment.py — geschlossenes Gyroid-Kuehlsegment der ersten Wand mit Wasser-Ein-/Austritt (PicoGK) + Kennzahlen + Bild.

    .venv/bin/python -m stellarator.kuehlsegment [--name standard] [--zelle 100 --halbdicke 4 --voxel 2]

Masse in mm. Ergebnis sim/kuehlsegment/<name>/: segment.stl (Stahl), wasser.stl (Fluidraum fuer FluidX3D),
ergebnis.json (Volumina, benetzte Flaeche, S_v, hydraulischer Durchmesser, freie Querschnitte), segment.png.
PicoGK laeuft ueber den Speicherwaechter (eigene systemd-Einheit, siehe speicherwaechter.py).
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import numpy as np

from .lauf import PROJEKT
from .speicherwaechter import starte_begrenzt

BIN = PROJEKT / "picogk" / "KuehlSegment" / "bin" / "Release" / "net9.0" / "KuehlSegment"
WURZEL = PROJEKT / "sim" / "kuehlsegment"


def kennzahlen(o: Path, a) -> dict:
    import pyvista as pv
    e = json.loads((o / "ergebnis.json").read_text())
    w = pv.read(o / "wasser.stl")
    # benetzte Flaeche im Kern: Wasseroberflaeche ohne die ebenen Begrenzungen ~ Gesamtflaeche Wasser
    A = w.area * 1e-6                                     # m2
    V = e["volumen_wasser_l"] * 1e-3                       # m3
    # freier Querschnitt in Kernmitte (Schnitt x = L/2)
    s = w.slice(normal="x", origin=(a.laenge / 2, a.breite / 2, a.kern / 2))
    A_frei = s.delaunay_2d().area * 1e-6 if s.n_points else float("nan")
    A_rohr = np.pi * (a.rohr_d / 2000) ** 2
    e |= {"benetzte_flaeche_m2": A, "S_v_m2_m3": A / V, "D_h_mm": 4 * V / A * 1e3,
          "freier_querschnitt_kern_m2": A_frei, "querschnitt_rohr_m2": A_rohr,
          "geschwindigkeit_kern_je_rohr_m_s": A_rohr / A_frei if A_frei == A_frei else None}
    (o / "ergebnis.json").write_text(json.dumps(e, indent=1))
    return e


def bild(o: Path, a) -> Path:
    import pyvista as pv
    s = pv.read(o / "segment.stl"); w = pv.read(o / "wasser.stl")
    pl = pv.Plotter(off_screen=True, window_size=(1900, 1100), shape=(1, 2)); pl.set_background("white")
    # links: Stahl, Rueckseite (Haut hinten) aufgeschnitten
    s_auf = s.clip(normal="z", origin=(0, 0, a.kern * 0.75), invert=True)
    pl.add_mesh(s_auf, color="#b8bec6", smooth_shading=True, specular=0.4)
    pl.add_text("Stahl: Haeute + Gyroid-Kern (hintere Haut aufgeschnitten)", font_size=11, color="black")
    pl.view_isometric(); pl.camera.zoom(1.25)
    pl.subplot(0, 1)
    pl.add_mesh(w, color="#2a7fd4", smooth_shading=True, specular=0.5)
    pl.add_text("Wasserraum (Fluidgebiet fuer FluidX3D)\nEintritt links, Austritt rechts", font_size=11, color="black")
    pl.view_isometric(); pl.camera.zoom(1.25)
    pl.link_views()
    p = o / "segment.png"; pl.screenshot(p); pl.close()
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="standard")
    ap.add_argument("--laenge", type=float, default=1000)
    ap.add_argument("--breite", type=float, default=400)
    ap.add_argument("--kern", type=float, default=200)
    ap.add_argument("--haut_plasma", type=float, default=10)
    ap.add_argument("--haut_hinten", type=float, default=15)
    ap.add_argument("--haut_seite", type=float, default=15)
    ap.add_argument("--zelle", type=float, default=100)
    ap.add_argument("--halbdicke", type=float, default=4)
    ap.add_argument("--kammer", type=float, default=60)
    ap.add_argument("--rohr_d", type=float, default=100)
    ap.add_argument("--rohr_wand", type=float, default=8)
    ap.add_argument("--rohr_l", type=float, default=150)
    ap.add_argument("--voxel", type=float, default=2)
    ap.add_argument("--max_gb", type=float, default=10)
    a = ap.parse_args(argv)
    o = WURZEL / a.name; o.mkdir(parents=True, exist_ok=True)
    auftrag = {k: v for k, v in vars(a).items() if k not in ("name", "max_gb")} | {"ausgabe": str(o)}
    (o / "auftrag.json").write_text(json.dumps(auftrag, indent=1))
    r = starte_begrenzt([str(BIN), str(o / "auftrag.json")], o / "picogk.log", a.max_gb,
                        env={"DOTNET_ROOT": str(Path.home() / ".dotnet")})
    if not r["ok"]:
        raise SystemExit(f"PicoGK abgebrochen: {r['grund']} (Spitze {r['spitze_gb']:.1f} GB)")
    e = kennzahlen(o, a)
    print(f"Stahl {e['volumen_stahl_l']:.0f} l, Wasser {e['volumen_wasser_l']:.0f} l, Kerndichte {e['kerndichte']:.0%}, "
          f"benetzt {e['benetzte_flaeche_m2']:.1f} m2, S_v {e['S_v_m2_m3']:.0f} m2/m3, D_h {e['D_h_mm']:.0f} mm, "
          f"v_Kern/v_Rohr {e['geschwindigkeit_kern_je_rohr_m_s']:.2f}; {r['zeit_s']:.0f} s, Spitze {r['spitze_gb']:.1f} GB")
    print(bild(o, a))


if __name__ == "__main__":
    main()
