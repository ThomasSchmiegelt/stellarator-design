"""ansicht.py — 3D-Ansicht: Feldlinien (gefaerbt nach |B|), magnetische Achse, Wickelpakete.

  .venv/bin/python -m stellarator.ansicht stellarator/faelle/w7x_standard.json [--setze ...] [--name ...]
      [--linien 4] [--umlaeufe 6] [--oeffnen]

Ausgabe sim/stellarator/bewertung/<name>/: feldlinien.vtm (Multiblock: feldlinien, achse,
wickelpakete -> ParaView), feldlinien_3d.png. Startpunkte: Achse + n Linien auf intakten
Flussflaechen (aus bewerte, falls kennzahlen.json da ist, sonst gleichmaessig bis 0,5 m).
"""
from __future__ import annotations
import argparse, copy, json, subprocess
from pathlib import Path
import numpy as np
import pyvista as pv

from . import spulen as sp
from .feldlinien import ZylinderGitter, _rhs
from .bewerte import finde_achse
from .lauf import setze, PROJEKT


def verfolge_3d(G, R0, Z0, umlaeufe: float, schritte_pro_umlauf: int = 360):
    """RK4 in phi, jeder Schritt gespeichert -> (n_linien, n_schritte+1, 3) kartesisch."""
    n = int(umlaeufe * schritte_pro_umlauf); h = 2 * np.pi / schritte_pro_umlauf
    R, Z = np.array(R0, float), np.array(Z0, float)
    out = np.empty((len(R), n + 1, 3)); phi = 0.0
    out[:, 0] = np.column_stack([R, np.zeros_like(R), Z])
    for i in range(n):
        k1 = _rhs(G, R, Z, phi)
        k2 = _rhs(G, R + h / 2 * k1[0], Z + h / 2 * k1[1], phi + h / 2)
        k3 = _rhs(G, R + h / 2 * k2[0], Z + h / 2 * k2[1], phi + h / 2)
        k4 = _rhs(G, R + h * k3[0], Z + h * k3[1], phi + h)
        R = R + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        Z = Z + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        phi += h
        out[:, i + 1] = np.column_stack([R * np.cos(phi), R * np.sin(phi), Z])
    return out


def ansicht(fall: dict, ordner: Path, n_linien: int = 4, umlaeufe: float = 6) -> Path:
    c = fall["spulen"]
    spulen, geo = sp.lade_spulensatz(c)
    seg = sp.segmente(spulen)
    G = ZylinderGitter(lambda x: sp.biot_savart(x, seg), R=geo["R_gitter"], Z=geo["Z_gitter"], nfp=geo["nfp"])
    Ra, Za = finde_achse(G, geo["achse_start"], nfp=geo["nfp"])
    # Startpunkte: Startradius (dR bei phi=0, NICHT r_eff) der aeussersten intakten Linie
    dR_max = 0.2
    kz = ordner / "kennzahlen.json"
    if kz.exists():
        prof = json.loads(kz.read_text())["iota"]["profil"]
        n_ok = next((i for i, p in enumerate(prof) if not p["flussflaeche_intakt"]), len(prof))
        if n_ok:
            dR_max = prof[n_ok - 1]["R0_m"] - Ra
    R0 = Ra + np.linspace(0, dR_max, n_linien + 1)
    L = verfolge_3d(G, R0, np.full_like(R0, Za), umlaeufe)
    # ausserhalb des Interpolationsgitters ist G extrapoliert -> Linie dort abschneiden
    Rl = np.hypot(L[..., 0], L[..., 1])
    raus = (Rl < G.R[0]) | (Rl > G.R[-1]) | (np.abs(L[..., 2]) > G.Z[-1])
    ende = np.where(raus.any(1), raus.argmax(1), L.shape[1])
    # |B| kalibriert wie bewerte (Mittel auf der Achse = B0)
    B = np.linalg.norm(sp.biot_savart(L.reshape(-1, 3), seg), axis=1).reshape(L.shape[:2])
    if c.get("B0_achse_T"):
        B *= c["B0_achse_T"] / B[0].mean()
    linien = pv.MultiBlock()
    for i in range(len(R0)):
        poly = pv.lines_from_points(L[i, :ende[i]]); poly["B_T"] = B[i, :ende[i]]
        linien.append(poly, "achse" if i == 0 else f"linie_{i}")
    tri = np.concatenate([sp.rohr_dreiecke(s, c["wickel_breite_m"], c["wickel_hoehe_m"]) for s in spulen])
    pts, inv = np.unique(tri.reshape(-1, 3).round(7), axis=0, return_inverse=True)
    spule_netz = pv.PolyData(pts, np.column_stack([np.full(len(tri), 3), inv.reshape(-1, 3)]).ravel())
    mb = pv.MultiBlock({"feldlinien": linien, "wickelpakete": spule_netz})
    ordner.mkdir(parents=True, exist_ok=True)
    mb.save(ordner / "feldlinien.vtm")
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1000)); pl.set_background("white")
    pl.add_mesh(spule_netz, color="#c87533", opacity=0.35)
    for i in range(len(R0)):
        pl.add_mesh(linien[i].tube(radius=(0.03 if i == 0 else 0.015) * Ra / 6), scalars="B_T", cmap="viridis",
                    clim=[min(B[i, :ende[i]].min() for i in range(len(R0))),
                          max(B[i, :ende[i]].max() for i in range(len(R0)))], scalar_bar_args={"title": "|B| [T]", "color": "black"},
                    show_scalar_bar=(i == 0))
    pl.add_text(f"{fall.get('name')}: Achse + {n_linien} Feldlinien auf intakten Flussflaechen, "
                f"{umlaeufe} Umlaeufe" + (f" ({int((ende < L.shape[1]).sum())} verlassen das Gebiet)" if (ende < L.shape[1]).any() else ""),
                font_size=10, color="black")
    pl.camera_position = [tuple(np.array([13, -13, 10]) * Ra / 6), (0, 0, 0), (0, 0, 1)]
    pl.reset_camera(); pl.camera.zoom(1.6)
    pl.screenshot(ordner / "feldlinien_3d.png"); pl.close()
    return ordner / "feldlinien.vtm"


def main(argv=None):
    ap = argparse.ArgumentParser(description="3D-Feldlinien + Spulen fuer ParaView")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--setze", action="append", default=[])
    ap.add_argument("--name")
    ap.add_argument("--linien", type=int, default=4)
    ap.add_argument("--umlaeufe", type=float, default=6)
    ap.add_argument("--oeffnen", action="store_true", help="ParaView starten")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text())
    for z in a.setze:
        setze(fall, z)
    if a.name:
        fall["name"] = a.name
    vtm = ansicht(copy.deepcopy(fall), PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"],
                  a.linien, a.umlaeufe)
    print("FERTIG", vtm)
    if a.oeffnen:
        subprocess.Popen(["paraview", str(vtm)], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
