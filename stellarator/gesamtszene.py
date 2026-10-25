"""gesamtszene.py — 1-GW-Anlage komplett: Plasma, Gyroid-Gefaess (Detailsektor), Gefaessschale, Spulengehaeuse mit
Spannung, Magnetfeldlinien. Export als PLY mit Vertexfarben -> Blender (blender_gesamt.py) bzw. ParaView (gesamt.vtm).

    .venv/bin/python -m stellarator.gesamtszene [--gyroid dick] [--linien 6] [--blender --proben 48]

Spannung: Surrogat-Vorhersage (sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu, 1000 MW), Farbskala turbo.
Feldlinien: Biot-Savart der 16 Spulen (Stroeme wie im Surrogat), RK4 entlang B/|B|, Startpunkte im Plasma bei phi=0,
Farbe |B| (plasma-Skala). Spulen ueber dem Detailsektor werden weggelassen, damit die Gyroide sichtbar sind.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
import numpy as np
import pyvista as pv
import matplotlib

from .lauf import PROJEKT
from .gyroid_gefaess import randflaeche, WURZEL as GG
from . import spulen as sp

O = PROJEKT / "sim" / "gesamtszene"
SPANNUNG_MAX = 4000.0     # MPa, Ende der Farbskala


def farben(werte, lo, hi, cmap) -> np.ndarray:
    c = matplotlib.colormaps[cmap](np.clip((werte - lo) / (hi - lo), 0, 1))[:, :3]
    return (c * 255).astype(np.uint8)


def normalen(X):
    dth = np.roll(X, -1, 0) - np.roll(X, 1, 0); dph = np.roll(X, -1, 1) - np.roll(X, 1, 1)
    N = np.cross(dph, dth); N /= np.linalg.norm(N, axis=-1, keepdims=True)
    c = X.mean(axis=0, keepdims=True)                     # Mittelpunkt je Querschnitt
    if np.mean(np.einsum("ijk,ijk->ij", N, X - c)) < 0:
        N = -N
    return N


def flaeche(P, ph0, ph1):
    ph = np.degrees(np.arctan2(P[0, :, 1], P[0, :, 0])) % 360
    j = np.where((ph >= ph0) & (ph <= ph1))[0]
    j = j[np.argsort(ph[j])]
    S = P[:, j]; nt, k = S.shape[:2]
    q = [[4, i * k + jj, ((i + 1) % nt) * k + jj, ((i + 1) % nt) * k + jj + 1, i * k + jj + 1]
         for i in range(nt) for jj in range(k - 1)]
    return pv.PolyData(S.reshape(-1, 3), np.array(q).ravel()).triangulate()


def feldlinien(n_linien: int, umlaeufe: float = 2.5, ds: float = 0.08):
    from .surrogat import modell
    from .surrogat_auswertung import mitte
    import pickle
    meta = pickle.load(open(PROJEKT / "sim/surrogat/qa_1gw/modell.pkl", "rb"))["meta"]
    spulen, *_ = modell("qa_1gw", mitte(meta) | {"P_netz": 1000.0})
    seg = sp.segmente(spulen)
    X = randflaeche(n_th=64, n_ph=8)
    ach = X[:, 0].mean(0)                                  # grob: Mitte des Querschnitts bei phi=0
    rand = X[np.argmax(X[:, 0, 0]), 0]                     # aussen
    starts = [ach + f * (rand - ach) for f in np.linspace(0.15, 0.85, n_linien)]
    B = lambda x: sp.biot_savart(x, seg)
    linien = []
    n = int(umlaeufe * 2 * np.pi * 10.4 / ds)
    P = np.array(starts, float)
    bahn = [P.copy()]
    for _ in range(n):                                     # RK4, alle Linien zugleich
        f = lambda x: (lambda b: b / np.linalg.norm(b, axis=1, keepdims=True))(B(x))
        k1 = f(P); k2 = f(P + ds / 2 * k1); k3 = f(P + ds / 2 * k2); k4 = f(P + ds * k3)
        P = P + ds / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        bahn.append(P.copy())
    bahn = np.array(bahn)                                  # (n, L, 3)
    for l in range(bahn.shape[1]):
        pts = bahn[::2, l]
        b = np.linalg.norm(B(pts), axis=1)
        linien.append((pts, b))
    return linien


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gyroid", default="dick")
    ap.add_argument("--spalt", type=float, default=0.15)
    ap.add_argument("--linien", type=int, default=8)
    ap.add_argument("--blender", action="store_true")
    ap.add_argument("--proben", type=int, default=48)
    a = ap.parse_args(argv)
    O.mkdir(parents=True, exist_ok=True)
    g_o = GG / a.gyroid
    par = json.loads((g_o / "ergebnis.json").read_text())["parameter"]
    wand = par["wand"]
    sek = sorted(g_o.glob("sektor_*"))
    lo_d = float(sek[0].name.split("_")[1]); hi_d = float(sek[-1].name.split("_")[1]) + par["teil"]

    X = randflaeche(n_th=128, n_ph=720)
    N = normalen(X)
    teile = {}
    teile["plasma"] = flaeche(X, 0, 360)
    teile["schale_aussen"] = flaeche(X + (a.spalt + wand) * N, hi_d + 25, 360 - 1e-6)    # Fenster neben dem Detail offen
    teile["schale_innen"] = flaeche(X + a.spalt * N, hi_d + 25, 360 - 1e-6)
    # erste Haelfte geschlossen (Gefaess mit Haeuten), zweite Haelfte ohne Aussenhaut: Gyroid-Kern + Innenhaut sichtbar
    teile["plasma_teil"] = flaeche(X, lo_d - 30, hi_d)                 # fuer Detailansichten: Plasma endet an der Schnittflaeche
    halb = len(sek) // 2
    gy = [pv.read(p / "gefaess.stl").scale(1e-3) for p in sek[:halb]] + [pv.read(p / "kern.stl").scale(1e-3) for p in sek[halb:]]
    teile["gyroid"] = gy[0].merge(gy[1:]).clean()
    ph_offen = float(sek[halb].name.split("_")[1])
    teile["innenhaut"] = flaeche(X + (a.spalt + par["haut_innen"]) * N, ph_offen, hi_d)
    print("Gyroid", teile["gyroid"].n_cells, "Dreiecke")

    g = pv.read(PROJEKT / "sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu")
    st = g.extract_cells(np.where(g.cell_data["material"] >= 3)[0]).extract_surface(algorithm="dataset_surface")
    c = st.cell_centers().points
    phc = np.degrees(np.arctan2(c[:, 1], c[:, 0])) % 360
    sp_id = np.round(st.cell_data["spule"]).astype(int)
    weg = []
    for s in np.unique(sp_id[sp_id >= 0]):                 # Verbinder (spule < 0) bleiben
        m = np.degrees(np.angle(np.mean(np.exp(1j * np.radians(phc[sp_id == s]))))) % 360
        if (m - lo_d + 15) % 360 < (hi_d - lo_d) + 30:
            weg.append(int(s))
    fenster = (phc - lo_d + 15) % 360 < (hi_d - lo_d) + 30
    st = st.extract_cells(np.where(~np.isin(sp_id, weg) & ~((sp_id < 0) & fenster))[0]).extract_surface(algorithm="dataset_surface")
    st = st.cell_data_to_point_data(pass_cell_data=True)
    mat = np.round(st.cell_data["material"]).astype(int)
    stuetze = st.extract_cells(np.where(mat == 4)[0]).extract_surface(algorithm="dataset_surface")   # Verbinder
    st = st.extract_cells(np.where(mat == 3)[0]).extract_surface(algorithm="dataset_surface")         # Spulengehaeuse
    st.point_data["RGB"] = farben(st.point_data["vonmises_MPa"], 0, SPANNUNG_MAX, "turbo")
    teile["spulen"] = st
    teile["stuetze"] = stuetze
    print("Spulen ausgeblendet ueber dem Sektor:", [int(s) for s in weg])

    lin = feldlinien(a.linien)
    bmax = max(b.max() for _, b in lin); bmin = min(b.min() for _, b in lin)
    tubes = []
    for pts, b in lin:
        pl = pv.lines_from_points(pts); pl.point_data["B_T"] = b
        t = pl.tube(radius=0.07, n_sides=12)
        t.point_data["RGB"] = farben(t.point_data["B_T"], bmin, bmax, "plasma")
        tubes.append(t)
    teile["feldlinien"] = tubes[0].merge(tubes[1:])
    print(f"Feldlinien |B| {bmin:.1f} .. {bmax:.1f} T")

    for k, v in teile.items():
        v.save(O / f"{k}.ply", texture="RGB" if "RGB" in v.point_data else None)
    pv.MultiBlock(teile).save(O / "gesamt.vtm")
    (O / "skala.json").write_text(json.dumps({"spannung_MPa": [0, SPANNUNG_MAX], "B_T": [bmin, bmax],
                                               "sektor_grad": [lo_d, hi_d]}))
    # Vorschau pyvista
    pl = pv.Plotter(off_screen=True, window_size=(1900, 1200)); pl.set_background("white")
    pl.add_mesh(teile["plasma"], color="#c050ff", opacity=0.35, smooth_shading=True)
    pl.add_mesh(teile["schale_aussen"], color="#8a949d", opacity=0.5, smooth_shading=True)
    pl.add_mesh(teile["gyroid"], color="#e8a33a", smooth_shading=True)
    pl.add_mesh(teile["innenhaut"], color="#d0d4d8", smooth_shading=True)
    pl.add_mesh(teile["spulen"], scalars="RGB", rgb=True)
    pl.add_mesh(teile["stuetze"], color="#c8ccd0", smooth_shading=True)
    pl.add_mesh(teile["feldlinien"], scalars="RGB", rgb=True)
    pl.view_isometric(); pl.camera.azimuth = -60; pl.camera.elevation = 10; pl.camera.zoom(1.3)
    pl.screenshot(O / "vorschau.png"); pl.close()
    if a.blender:
        r = subprocess.run(["blender", "-b", "-P", str(PROJEKT / "stellarator/blender_gesamt.py"), "--", str(O),
                            "--proben", str(a.proben)], capture_output=True, text=True)
        print(r.stdout[-600:], r.stderr[-600:])
    return O


if __name__ == "__main__":
    main()


def legende(bild: Path, ziel: Path, ordner: Path = O, teile: list | None = None) -> None:
    """Farbskalen und Bauteil-Legende unten in das Blender-Bild einsetzen. teile: [(Farbe, Text), ...]"""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from PIL import Image
    sk = json.loads((ordner / "skala.json").read_text())
    fig = plt.figure(figsize=(19.2, 1.6), dpi=100); fig.patch.set_facecolor("#262b38")
    for i, (titel, (lo, hi), cmap) in enumerate((("von Mises Spulengehaeuse [MPa] (Surrogat, 1000 MW)", sk["spannung_MPa"], "turbo"),
                                                 ("|B| auf den Feldlinien [T]", sk["B_T"], "plasma"))):
        ax = fig.add_axes([0.03 + 0.33 * i, 0.45, 0.29, 0.22])
        ax.imshow(np.linspace(0, 1, 256)[None], cmap=cmap, aspect="auto", extent=[lo, hi, 0, 1])
        ax.set_yticks([]); ax.tick_params(colors="white", labelsize=11)
        ax.set_title(titel, color="white", fontsize=12)
    ax = fig.add_axes([0.69, 0.05, 0.3, 0.9]); ax.axis("off")
    teile = teile or [("#c8ccd0", "Stuetzstruktur (Verbinder, Stahl)"), ("#d98a2e", "Gefaesswand mit Gyroid-Kuehlkern"),
                      ("#c050ff", "Plasma"), ("#8a949d", "Gefaessschale (vereinfacht)")]
    ax.legend(handles=[Patch(color=f, label=t) for f, t in teile],
              loc="center", ncol=2, fontsize=11, facecolor="#262b38", labelcolor="white", edgecolor="#262b38")
    fig.savefig(ordner / "legende.png", facecolor=fig.get_facecolor()); plt.close(fig)
    a = Image.open(bild).convert("RGB"); b = Image.open(ordner / "legende.png").convert("RGB").resize((a.width, int(a.width * 1.6 / 19.2)))
    c = Image.new("RGB", (a.width, a.height + b.height)); c.paste(a, (0, 0)); c.paste(b, (0, a.height)); c.save(ziel)
