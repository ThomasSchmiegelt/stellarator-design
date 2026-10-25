"""thorus_schnitt.py — Plasmagefaess der 1-GW-Anlage allein, in Einbaulage (Torusachse senkrecht), mit
herausgeschnittenem Tortenstueck: die beiden Schnittflaechen zeigen den Gyroid-Kern (PicoGK-Sektoren).
Keine Spulen, keine Verbinder.

    .venv/bin/python -m stellarator.thorus_schnitt [--proben 64]

Voraussetzung: PicoGK-Sektoren sim/gyroid_gefaess/dick (0..40 Grad) und dick2 (100..140 Grad), gleiche Parameter.
Ausschnitt 40..100 Grad offen; Rest des Rings (140..360 Grad) als glatte Schale (Innen-/Aussenhaut).
Ausgabe sim/thorus_schnitt/: PLY-Teile, thorus.blend, blender_<ansicht>.png.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
import numpy as np
import pyvista as pv

from .lauf import PROJEKT
from .gyroid_gefaess import randflaeche, WURZEL as GG
from .gesamtszene import normalen, flaeche, farben, feldlinien, legende, SPANNUNG_MAX
from .speicherwaechter import starte_begrenzt

O = PROJEKT / "sim" / "thorus_schnitt"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--teile", default="dick,dick2", help="Gyroid-Ordner unter sim/gyroid_gefaess")
    ap.add_argument("--spalt", type=float, default=0.15)
    ap.add_argument("--proben", type=int, default=64)
    ap.add_argument("--ansicht", default="alle")
    ap.add_argument("--spulen", action="store_true", help="Spulengehaeuse mit Spannung + Feldlinien dazu, ohne Verbinder")
    ap.add_argument("--linien", type=int, default=8)
    ap.add_argument("--ebene", action="store_true", help="senkrechter Schnitt durch ein Segment (--teile ebene)")
    ap.add_argument("--horizontal", action="store_true", help="waagrechter Schnitt z=0 mit Band-Sektoren (--teile band)")
    a = ap.parse_args(argv)
    if a.horizontal:
        return horizontal(a)
    if a.ebene:
        return segment_ebene(a)
    o = O / "spulen" if a.spulen else O
    o.mkdir(parents=True, exist_ok=True)
    ordner = [GG / n for n in a.teile.split(",")]
    par = json.loads((ordner[0] / "ergebnis.json").read_text())["parameter"]
    sek = sorted(p for o in ordner for p in o.glob("sektor_*"))
    grad = sorted(float(p.name.split("_")[1]) for p in sek)
    lo1, hi2 = grad[0], grad[-1] + par["teil"]          # 0 .. 140
    luecke = [g for g in grad if g + par["teil"] not in grad and g + par["teil"] < hi2]
    hi1 = luecke[0] + par["teil"]; lo2 = min(g for g in grad if g > hi1)    # offener Ausschnitt hi1 .. lo2 (40 .. 100)
    X = randflaeche(n_th=128, n_ph=720)
    N = normalen(X)
    wand = par["wand"]
    teile = {
        "schale_aussen": flaeche(X + (a.spalt + wand) * N, hi2, 360 - 1e-6),
        "schale_innen": flaeche(X + a.spalt * N, hi2, 360 - 1e-6),
        "plasma_teil": flaeche(X, hi1 - 2, lo2 + 2),                # Plasma im offenen Ausschnitt
    }
    gy = [pv.read(p / "gefaess.stl").scale(1e-3) for p in sek]
    gy = gy[0].merge(gy[1:]).clean().compute_normals(cell_normals=True, point_normals=False)
    # Schnittflaechen (Ebenen phi = 40 / 100 Grad) als eigenes Teil -> eigene Farbe wie in einer Schnittzeichnung
    c = gy.cell_centers().points; n = gy.cell_data["Normals"]
    auf = np.zeros(gy.n_cells, bool)
    for ph in (hi1, lo2):
        e = np.array([-np.sin(np.radians(ph)), np.cos(np.radians(ph)), 0])
        auf |= (np.abs(c @ e) < 0.02) & (np.abs(n @ e) > 0.95)
    teile["schnitt"] = gy.extract_cells(np.where(auf)[0]).extract_surface()
    teile["gyroid"] = gy.extract_cells(np.where(~auf)[0]).extract_surface()
    for k, t in teile.items():
        t.save(o / f"{k}.ply", texture="RGB" if "RGB" in t.point_data else None)
    z_min = float((X + (a.spalt + wand) * N)[..., 2].min())
    sk = {"z_boden": z_min - 0.8, "sektoren_grad": grad, "offen_grad": [hi1, lo2]}
    if a.spulen:
        sk |= spulen_feld(o, hi1, lo2, a.linien)
    (o / "skala.json").write_text(json.dumps(sk))
    rendern(o, a)
    if a.spulen:
        for k in ("uebersicht", "detail"):
            if (o / f"blender_{k}.png").exists():
                legende(o / f"blender_{k}.png", o / f"thorus_{k}.png", o,
                        [("#d98a2e", "Schnitt Gyroid-Wand"), ("#a6abb2", "Plasmagefaess (Stahl)"),
                         ("#c050ff", "Plasma"), ("#3b5bd6", "Spulengehaeuse (Spannung)")])
    print("Gyroid", teile["gyroid"].n_cells, "Dreiecke, Schnitt", teile["schnitt"].n_cells, "Dreiecke; Boden", z_min - 0.8, flush=True)


def spulen_feld(o: Path, lo_weg: float, hi_weg: float, n_linien: int) -> dict:
    """Spulengehaeuse (Surrogat 1000 MW, von Mises als Vertexfarbe) ohne Verbinder; Spulen ueber dem offenen
    Ausschnitt lo_weg..hi_weg weggelassen. Feldlinien (Biot-Savart) als Roehren, Farbe |B|. Schreibt PLYs."""
    g = pv.read(PROJEKT / "sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu")
    st = g.extract_cells(np.where(np.round(g.cell_data["material"]) == 3)[0]).extract_surface(algorithm="dataset_surface")
    c = st.cell_centers().points
    phc = np.degrees(np.arctan2(c[:, 1], c[:, 0])) % 360
    sp_id = np.round(st.cell_data["spule"]).astype(int)
    weg = [int(s) for s in np.unique(sp_id)
           if lo_weg - 8 < np.degrees(np.angle(np.mean(np.exp(1j * np.radians(phc[sp_id == s]))))) % 360 < hi_weg + 8]
    st = st.extract_cells(np.where(~np.isin(sp_id, weg))[0]).extract_surface(algorithm="dataset_surface")
    st = st.cell_data_to_point_data(pass_cell_data=True)
    st.point_data["RGB"] = farben(st.point_data["vonmises_MPa"], 0, SPANNUNG_MAX, "turbo")
    st.save(o / "spulen.ply", texture="RGB")
    lin = feldlinien(n_linien)
    bmax = max(b.max() for _, b in lin); bmin = min(b.min() for _, b in lin)
    tubes = []
    for pts, b in lin:
        l = pv.lines_from_points(pts); l.point_data["B_T"] = b
        t = l.tube(radius=0.07, n_sides=12)
        t.point_data["RGB"] = farben(t.point_data["B_T"], bmin, bmax, "plasma")
        tubes.append(t)
    tubes[0].merge(tubes[1:]).save(o / "feldlinien.ply", texture="RGB")
    print("Spulen weggelassen ueber dem Ausschnitt:", weg, f"; |B| {bmin:.1f}..{bmax:.1f} T", flush=True)
    return {"spannung_MPa": [0, SPANNUNG_MAX], "B_T": [float(bmin), float(bmax)]}


def rendern(o: Path, a) -> None:
    blender = subprocess.run(["which", "blender"], capture_output=True, text=True).stdout.strip()
    r = starte_begrenzt([blender, "-b", "-P", str(PROJEKT / "stellarator" / "blender_thorus.py"), "--", str(o),
                         "--proben", str(a.proben), "--ansicht", a.ansicht], o / "blender.log", 6)
    print(r)


def horizontal(a) -> None:
    """Torus waagrecht auf Mittelhoehe (z=0) aufgeschnitten, obere Haelfte weg. Gyroid nur im Band unter der
    Schnittebene (PicoGK --z_band), darunter glatte Innen-/Aussenhaut; Schnittflaeche orange."""
    o = O / "horizontal"; o.mkdir(parents=True, exist_ok=True)
    g_o = GG / a.teile
    par = json.loads((g_o / "ergebnis.json").read_text())["parameter"]
    z_lo = float(par["z_band"].split(":")[0])
    X = randflaeche(n_th=128, n_ph=720)
    N = normalen(X)
    unter = lambda m, z: m.clip(normal="z", origin=(0, 0, z), invert=True)
    teile = {"schale_aussen": unter(flaeche(X + (a.spalt + par["wand"]) * N, 0, 360), z_lo + 0.02),
             "schale_innen": unter(flaeche(X + a.spalt * N, 0, 360), z_lo + 0.02),
             "plasma_teil": unter(flaeche(X, 0, 360), 0.0)}
    gy = [pv.read(p / "gefaess.stl").scale(1e-3) for p in sorted(g_o.glob("sektor_*"))]
    gy = gy[0].merge(gy[1:]).clean().compute_normals(cell_normals=True, point_normals=False)
    c = gy.cell_centers().points; n = gy.cell_data["Normals"]
    auf = (np.abs(c[:, 2]) < 0.02) & (np.abs(n[:, 2]) > 0.95)          # Schnittebene z = 0
    teile["schnitt"] = gy.extract_cells(np.where(auf)[0]).extract_surface()
    teile["gyroid"] = gy.extract_cells(np.where(~auf)[0]).extract_surface()
    for k, t in teile.items():
        t.save(o / f"{k}.ply")
    z_min = float((X + (a.spalt + par["wand"]) * N)[..., 2].min())
    ansichten = {"uebersicht": [[30 * np.cos(np.radians(-60)), 30 * np.sin(np.radians(-60)), 19], [0, 0, -2.5], 35, 0],
                 "detail": [[16 * np.cos(np.radians(-25)), 16 * np.sin(np.radians(-25)), 7], [11 * np.cos(0), 0, -0.5], 40, 6000]}
    (o / "skala.json").write_text(json.dumps({"z_boden": z_min - 0.8, "ansichten": ansichten}))
    print("Gyroid", teile["gyroid"].n_cells, "Dreiecke, Schnitt", teile["schnitt"].n_cells, "Dreiecke", flush=True)
    rendern(o, a)



def segment_ebene(a) -> None:
    """Torus waagrecht, geschlossen; nur ein Segment senkrecht geschnitten (Ebene laengs zum Ring, Aussenteil weg,
    PicoGK --ebene phi:R). Laengsschnitt zeigt die Filamente in Ober- und Unterwand, Plasma im offenen Segment."""
    o = O / "ebene"; o.mkdir(parents=True, exist_ok=True)
    g_o = GG / a.teile
    par = json.loads((g_o / "ergebnis.json").read_text())["parameter"]
    phi_e, R_e = map(float, par["ebene"].split(":"))
    sek = sorted(g_o.glob("sektor_*"))
    lo = float(sek[0].name.split("_")[1]); hi = float(sek[-1].name.split("_")[1]) + par["teil"]
    e = np.array([np.cos(np.radians(phi_e)), np.sin(np.radians(phi_e)), 0.0])
    X = randflaeche(n_th=128, n_ph=720)
    N = normalen(X)
    teile = {"schale_aussen": flaeche(X + (a.spalt + par["wand"]) * N, hi, 360 - 1e-6),
             "schale_innen": flaeche(X + a.spalt * N, hi, 360 - 1e-6),
             "plasma_teil": flaeche(X, lo, hi).clip(normal=e, origin=R_e * e, invert=True)}
    gy = [pv.read(p / "gefaess.stl").scale(1e-3) for p in sek]
    gy = gy[0].merge(gy[1:]).clean().compute_normals(cell_normals=True, point_normals=False)
    c = gy.cell_centers().points; n = gy.cell_data["Normals"]
    auf = (np.abs(c @ e - R_e) < 0.02) & (np.abs(n @ e) > 0.95)
    teile["schnitt"] = gy.extract_cells(np.where(auf)[0]).extract_surface()
    teile["gyroid"] = gy.extract_cells(np.where(~auf)[0]).extract_surface()
    for k, t in teile.items():
        t.save(o / f"{k}.ply")
    z_min = float((X + (a.spalt + par["wand"]) * N)[..., 2].min())
    pol = lambda r, ph, z: [r * np.cos(np.radians(ph)), r * np.sin(np.radians(ph)), z]
    ansichten = {"uebersicht": [pol(34, 0, 15), pol(4, 20, -2), 35, 0],
                 "detail": [pol(22, 30, 3.5), pol(10.8, 20, -0.4), 35, 6000]}
    (o / "skala.json").write_text(json.dumps({"z_boden": z_min - 0.8, "ansichten": ansichten}))
    print("Gyroid", teile["gyroid"].n_cells, "Dreiecke, Schnitt", teile["schnitt"].n_cells, "Dreiecke", flush=True)
    rendern(o, a)


if __name__ == "__main__":
    main()
