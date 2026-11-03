"""qi_vergleich_bild.py — Bild: unser QA-Plasma (0169) neben Proximas QI-Plasma (Rangliste, nfp 3), mit Spulen.

  .venv/bin/python -m stellarator.qi_vergleich_bild [punkt_qi]     # -> docs/bilder/qa_qi_vergleich.png

Gleicher Maßstab (Meter), gleiches Plasmavolumen (1096 m3). Oben: Anlage schräg von oben, Plasma farbig nach Höhe z
nicht nötig -> einfarbig, Spulen als Rohre. Unten: Querschnitte des Plasmas an drei Stellen einer Periode.
Plasmarand direkt aus der VMEC-Datei (rmnc/zmns, s = 1), Spulen aus spulen.json (Einheitslänge x L).
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
L = 10.102932590386631
QA = {"titel": "Unser Plasma (QA, 2 Perioden, A = 4,5)", "wout": ROOT / "sim/invers/qa_nfp2_A45/wout_qa_nfp2_A45.nc",
      "spulen": ROOT / "sim/kopplung/netz_normal/punkte/0169/spulen.json"}
QI = {"titel": "QI-Plasma aus Proximas Rangliste (3 Perioden, A = 10)",
      "warnung": "Spulen: erster Versuch unserer Kette, UNBRAUCHBAR (schneiden das Plasma, Bn = 0,11)",
      "wout": ROOT / "sim/constellaration/qi/nfp3_s068/wout_nfp3_s068_skaliert.nc",
      "spulen": ROOT / "sim/kopplung/qi_nfp3_s068/punkte" / (sys.argv[1] if len(sys.argv) > 1 else "0001") / "spulen.json"}


if len(sys.argv) > 2 and sys.argv[2] == "b36":                      # Proximas Spulensatz (CoilStellaration)
    QI = {"titel": "QI-Plasma + Spulen von Proxima (CoilStellaration, 3 Perioden, A = 9,2)",
          "wout": ROOT / "sim/constellaration/qi/proxima_spulen_b36/wout_skaliert.nc",
          "spulen": ROOT / "sim/kopplung/qi_proxima_b36/punkte/0000/spulen.json", "aus": "qa_qi_proxima_spulen.png",
          "fuss": "Links Spulen aus unserer Kette (simsopt), rechts Spulen von Proxima (CoilStellaration, MIT; Feldfehler 9,3e-4 nachgerechnet)"}


def rand(wout, nphi=240, nth=120):
    from scipy.io import netcdf_file
    with netcdf_file(str(wout), "r", mmap=False) as f:
        xm, xn = f.variables["xm"][:], f.variables["xn"][:]
        rc, zs = f.variables["rmnc"][-1].copy(), f.variables["zmns"][-1].copy(); nfp = int(f.variables["nfp"][()])
    ph = np.linspace(0, 2 * np.pi, nphi); th = np.linspace(0, 2 * np.pi, nth)
    P, T = np.meshgrid(ph, th, indexing="ij")
    w = xm[None, None] * T[..., None] - xn[None, None] * P[..., None]
    R = (rc * np.cos(w)).sum(-1) * L; Z = (zs * np.sin(w)).sum(-1) * L
    return R, Z, P, nfp


def schnitt(wout, phi):
    from scipy.io import netcdf_file
    with netcdf_file(str(wout), "r", mmap=False) as f:
        xm, xn = f.variables["xm"][:], f.variables["xn"][:]
        rc, zs = f.variables["rmnc"][-1].copy(), f.variables["zmns"][-1].copy()
    th = np.linspace(0, 2 * np.pi, 300); w = xm[None] * th[:, None] - xn[None] * phi
    return (rc * np.cos(w)).sum(-1) * L, (zs * np.sin(w)).sum(-1) * L


def ansicht(d, datei):
    import pyvista as pv
    R, Z, P, nfp = rand(d["wout"])
    g = pv.StructuredGrid(R * np.cos(P), R * np.sin(P), Z)
    pl = pv.Plotter(off_screen=True, window_size=(1400, 1000)); pl.set_background("white")
    pl.add_mesh(g, color="#e88aa8", smooth_shading=True, specular=0.3)
    s = json.loads(Path(d["spulen"]).read_text())
    for sp in s["spulen"]:
        p = np.asarray(sp["punkte_m"]) * L; p = np.vstack([p, p[:1]])
        pl.add_mesh(pv.Spline(p, 400).tube(radius=0.38), color="#d08a2a" if sp["strom_A"] > 0 else "#b0702a",
                    smooth_shading=True, specular=0.4)
    pl.camera_position = [(0, -74, 50), (0, 0, -2), (0, 0, 1)]; pl.camera.view_angle = 30
    pl.screenshot(datei); pl.close()
    return len(s["spulen"]), nfp, float(R.max()), float(R.min())


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    tmp = ROOT / "sim" / "constellaration"
    info = [ansicht(d, tmp / f"_ansicht_{i}.png") for i, d in enumerate((QA, QI))]
    fig = plt.figure(figsize=(14, 10.5), dpi=130)
    for i, (d, (n, nfp, rmax, rmin)) in enumerate(zip((QA, QI), info)):
        ax = fig.add_axes([0.01 + 0.5 * i, 0.40, 0.48, 0.52]); ax.axis("off")
        im = np.asarray(Image.open(tmp / f"_ansicht_{i}.png")); ax.imshow(im[60:-60, 60:-60])
        ax.set_title(f"{d['titel']}\n{n} Spulen, Plasma-Durchmesser außen ≈ {2 * rmax:.0f} m", fontsize=12)
        if d.get("warnung"):
            ax.text(0.5, -0.04, d["warnung"], transform=ax.transAxes, ha="center", fontsize=10, color="#b00020")
        ax2 = fig.add_axes([0.06 + 0.5 * i, 0.06, 0.40, 0.30])
        rm = 0.0
        for j, (frac, farbe) in enumerate(((0, "#7a1f45"), (0.25, "#c2577f"), (0.5, "#e8a0b8"))):
            r, z = schnitt(d["wout"], 2 * np.pi * frac / nfp)
            rm += r.mean() / 3
            ax2.plot(r, z, color=farbe, lw=2, label=["Anfang", "Viertel", "Mitte"][j] + " der Periode")
        ax2.set_aspect("equal"); ax2.set_xlim(rm - 8.5, rm + 8.5); ax2.set_ylim(-8, 8)
        ax2.set_xlabel("Abstand von der Anlagenmitte R (m)"); ax2.set_ylabel("Höhe z (m)")
        ax2.grid(color="#dddddd", lw=0.6); ax2.legend(fontsize=8, loc="lower left", frameon=True, framealpha=0.9)
        ax2.set_title("Querschnitte des Plasmas", fontsize=10)
    fig.text(0.5, 0.005, "Gleiches Plasmavolumen (1096 m³). " + QI.get("fuss", "Spulenbahnen aus unserer Kette (simsopt)") + ", Plasmarand aus VMEC. "
             "Thomas Schmiegelt", ha="center", fontsize=8, color="#555555")
    aus = ROOT / "docs" / "bilder" / QI.get("aus", "qa_qi_vergleich.png"); fig.savefig(aus); print(aus)
    for i in (0, 1):
        (tmp / f"_ansicht_{i}.png").unlink()


if __name__ == "__main__":
    main()
