"""torus3d.py — Stellarator vollstaendig in 3D: Spulen mit Gehaeuse, Verguss, Isolation und Supraleitern.

  .venv/bin/python -m stellarator.torus3d stellarator/faelle/w7x_standard.json
      [--wand_innen 0.05 --wand_seite 0.05 --t_min 0.05 --t_max 0.15] [--h 0.04] [--oeffnen]

Anschauungsmodell (keine Rechnung) aus denselben Spulenbahnen und Gehaeusewaenden wie stellarator.gehaeuse_netz.
Jede Schicht ist ein Volumen (Profil entlang der exakten Bahn gezogen: Hexaeder/Keile), von aussen nach innen:
  7 Gehaeuse (Stahl, Waende nach Kraft und Freiraum) | 6 Verguss (Quarzsand-Epoxid) | 4 Grundisolierung
  | Wickelpaket: 12 Lagen x 9 Windungen = 108 Leiter, je 3 Windungsisolation, 2 Aluminiummantel,
    1 Supraleiterkabel (NbTi/Cu-Straenge + Helium, als ein Koerper).
Die einzelnen Leiter entstehen nur nahe der Schnittflaeche (dort sichtbar); sonst ist das Wickelpaket ein
homogener Block (5), der im geschlossenen Gehaeuse ohnehin verdeckt ist.
Schnitt: obere Haelfte (z > 0) ueber dem Halbtorus y < 0 entfernt -> Querschnitte bei z = 0.
Masse der Isolation/Leiter sind ANNAHMEN (schematisch): Leiter quadratisch, an den Wickelquerschnitt angepasst.
Ausgabe sim/stellarator/torus3d/<fall>/: torus3d.vtm (Bloecke je Schicht, Zellfeld "schicht") + Bilder.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
import numpy as np
import pyvista as pv

from . import spulen as sp, cad
from .gehaeuse_netz import waende, entflechten
from .lauf import PROJEKT

SCHICHTEN = {1: ("Kabel: NbTi-Supraleiter in Cu + Helium", "#1fa3a3"), 2: ("Aluminiummantel", "#d4d8de"),
             3: ("Windungsisolation", "#a8d08d"), 4: ("Grundisolierung", "#4f8f3a"),
             5: ("Wickelpaket (homogen dargestellt)", "#8a5a44"), 6: ("Verguss (Quarzsand-Epoxid)", "#efe2bd"),
             7: ("Gehaeuse (Stahl)", "#8b939e")}
NL, NW = 12, 9                       # Lagen (entlang n) x Windungen (entlang b) = 108
NK = 16                              # Punkte auf dem Kabelkreis


def rechteck(n0, n1, b0, b1) -> np.ndarray:
    """4 Ecken gegen den Uhrzeigersinn (..., 4, 2); Argumente skalar oder je Station."""
    return np.stack([np.stack([n0, b0], -1), np.stack([n1, b0], -1), np.stack([n1, b1], -1), np.stack([n0, b1], -1)], -2)


def ring(aussen, innen) -> tuple[np.ndarray, np.ndarray]:
    """Rechteckring zwischen zwei Viereck-Polygonen gleicher Punktzahl -> (Punkte (..., 2m, 2), Vierecke)."""
    m = aussen.shape[-2]
    pts = np.concatenate([aussen, innen], -2)
    q = np.array([[k, (k + 1) % m, m + (k + 1) % m, m + k] for k in range(m)])
    return pts, q


def ziehen(P, n, b, xs, zellen, stationen) -> pv.UnstructuredGrid | None:
    """Querschnitt xs (N, M, 2) bzw. (M, 2) entlang der Bahn ziehen, nur fuer die Segmente i -> i+1 in stationen.
    zellen (K, 4) Vierecke -> Hexaeder, (K, 3) Dreiecke -> Keile."""
    N = len(P)
    seg = np.asarray(sorted(set(int(i) % N for i in stationen)))
    if not len(seg):
        return None
    st = np.unique(np.r_[seg, (seg + 1) % N])                  # benoetigte Stationen
    idx = {s: k for k, s in enumerate(st)}
    X = xs if xs.ndim == 3 else np.broadcast_to(xs, (N,) + xs.shape)
    M = X.shape[1]
    pts = (P[st, None] + X[st, :, :1] * n[st, None] + X[st, :, 1:] * b[st, None]).reshape(-1, 3)
    a = np.array([idx[s] for s in seg]) * M; c = np.array([idx[(s + 1) % N] for s in seg]) * M
    z = (np.concatenate([a[:, None, None] + zellen[None], c[:, None, None] + zellen[None]], -1)
                        .reshape(-1, 2 * zellen.shape[1]))
    k = zellen.shape[1]
    typ = pv.CellType.HEXAHEDRON if k == 4 else pv.CellType.WEDGE
    return pv.UnstructuredGrid(np.c_[np.full(len(z), 2 * k), z].ravel(), np.full(len(z), typ), pts)


def leiter_querschnitt(br, ho, g, iso) -> dict:
    """Querschnitte eines Leiters (2D, mittig) und Mittelpunkte aller 108 Leiter im Wickelpaket."""
    pn, pb = (br - 2 * g) / NL, (ho - 2 * g) / NW              # Teilung
    c = min(pn, pb) - 2 * iso                                  # Leiterkante (quadratisch)
    r = 0.38 * c                                               # Kabelradius; Mantelwand ~0,12 c
    zelle = rechteck(-pn / 2, pn / 2, -pb / 2, pb / 2)
    quad = rechteck(-c / 2, c / 2, -c / 2, c / 2)
    # Quadrat mit NK Punkten (je Seite NK/4) und Kreis mit NK Punkten -> Mantelring
    t = np.linspace(0, 1, NK // 4, endpoint=False)[:, None]
    qk = np.concatenate([quad[k] + t * (quad[(k + 1) % 4] - quad[k]) for k in range(4)])
    w = np.arctan2(qk[:, 1], qk[:, 0])
    kreis = r * np.c_[np.cos(w), np.sin(w)]
    mitten = np.array([(-br / 2 + g + (i + 0.5) * pn, -ho / 2 + g + (j + 0.5) * pb) for i in range(NL) for j in range(NW)])
    fan_p = np.vstack([[0, 0], kreis]); fan = np.array([[0, 1 + k, 1 + (k + 1) % NK] for k in range(NK)])
    return {"iso": ring(zelle, quad), "mantel": ring(qk, kreis), "kabel": (fan_p, fan), "mitten": mitten,
            "teilung_mm": (pn * 1e3, pb * 1e3), "leiter_mm": c * 1e3, "kabel_r_mm": r * 1e3}


def spule_bloecke(s, w, br, ho, a, Lq, detail) -> dict[int, list]:
    t, n, b = sp.rahmen(s); P = s.punkte; N = len(P)
    g, vmax = a.grundiso, a.verguss
    v = {q: np.minimum(vmax, 0.5 * w[q]) for q in ("innen", "aussen", "links", "rechts")}   # Verguss <= halbe Wand
    wp = rechteck(-br / 2, br / 2, -ho / 2, ho / 2)
    vg = rechteck(-br / 2 - v["innen"], br / 2 + v["aussen"], -ho / 2 - v["links"], ho / 2 + v["rechts"])
    ge = rechteck(-br / 2 - w["innen"], br / 2 + w["aussen"], -ho / 2 - w["links"], ho / 2 + w["rechts"])
    kern = rechteck(-br / 2 + g, br / 2 - g, -ho / 2 + g, ho / 2 - g)
    alle = np.arange(N)
    seg_det = np.where(detail | np.roll(detail, -1))[0]          # Segment i -> i+1 beruehrt Detailbereich
    seg_hom = np.setdiff1d(alle, seg_det)
    out = {k: [] for k in SCHICHTEN}
    for nr, (x, q) in ((7, ring(ge, vg)), (6, ring(vg, np.broadcast_to(wp, vg.shape))), (4, ring(wp, kern))):
        out[nr].append(ziehen(P, n, b, x, q, alle))
    out[5].append(ziehen(P, n, b, kern, np.array([[0, 1, 2, 3]]), seg_hom))
    if len(seg_det):
        for m in Lq["mitten"]:
            for nr, (x, q) in ((3, Lq["iso"]), (2, Lq["mantel"]), (1, Lq["kabel"])):
                out[nr].append(ziehen(P, n, b, x + m, q, seg_det))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stellarator in 3D mit Gehaeuse, Verguss, Isolation, Supraleitern")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--wand_innen", type=float, default=0.05)
    ap.add_argument("--wand_seite", type=float, default=0.05)
    ap.add_argument("--t_min", type=float, default=0.05)
    ap.add_argument("--t_max", type=float, default=0.15)
    ap.add_argument("--spiel", type=float, default=0.01)
    ap.add_argument("--wand_min", type=float, default=0.003)
    ap.add_argument("--h", type=float, default=0.04, help="Stationsabstand entlang der Bahn [m]")
    ap.add_argument("--verguss", type=float, default=0.010, help="m, hoechstens halbe Gehaeusewand")
    ap.add_argument("--grundiso", type=float, default=0.003, help="m, Grundisolierung innerhalb des Wickelquerschnitts")
    ap.add_argument("--windungsiso", type=float, default=0.001, help="m je Seite um jeden Leiter")
    ap.add_argument("--detail_z", type=float, default=0.15, help="Leiter einzeln bis |z| < detail_z unter dem Schnitt")
    ap.add_argument("--oeffnen", action="store_true")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text()); c = fall["spulen"]
    spulen, _ = sp.lade_spulensatz(c)
    kz = PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"] / "kennzahlen.json"
    if kz.exists():
        for s in spulen:
            s.strom *= json.loads(kz.read_text())["strom"]["kalibrierfaktor"]
    for s in spulen:
        s.punkte = cad.neu_abtasten(s.punkte, max(60, int(np.ceil(s.laenge() / a.h))))
    br, ho = c["wickel_breite_m"], c["wickel_hoehe_m"]
    ordner = PROJEKT / "sim" / "stellarator" / "torus3d" / fall["name"]; ordner.mkdir(parents=True, exist_ok=True)
    cache = ordner / f"waende_h{a.h:.3f}.npz"
    if cache.exists():
        d = np.load(cache); W = [{q: d[f"{k}_{q}"] for q in ("innen", "aussen", "links", "rechts")} for k in range(len(spulen))]
    else:
        W = waende(spulen, br, ho, a)
        print("ENTFLECHTEN", entflechten(spulen, W, br, ho, a.h, a.spiel, a.wand_min), flush=True)
        np.savez(cache, **{f"{k}_{q}": w[q] for k, w in enumerate(W) for q in ("innen", "aussen", "links", "rechts")})
    Lq = leiter_querschnitt(br, ho, a.grundiso, a.windungsiso)
    print("LEITER", f"Teilung {Lq['teilung_mm'][0]:.1f} x {Lq['teilung_mm'][1]:.1f} mm, Leiter {Lq['leiter_mm']:.1f} mm, "
          f"Kabel r {Lq['kabel_r_mm']:.1f} mm", flush=True)
    bloecke = {k: [] for k in SCHICHTEN}
    for s, w in zip(spulen, W):
        P = s.punkte
        detail = (P[:, 2] < 0.02) & (P[:, 2] > -a.detail_z) & (P[:, 1] < 0.3)   # unter dem Schnitt z = 0, y < 0
        for k, v in spule_bloecke(s, w, br, ho, a, Lq, detail).items():
            bloecke[k] += [x for x in v if x is not None]
    mb = pv.MultiBlock()
    for k, (name, _) in SCHICHTEN.items():
        g = pv.merge(bloecke[k]) if len(bloecke[k]) > 1 else bloecke[k][0]
        g.cell_data["schicht"] = np.full(g.n_cells, k, dtype=np.int32)
        mb[name] = g
        print("SCHICHT", k, name, g.n_cells, "Zellen", flush=True)
    mb.save(ordner / "torus3d.vtm")
    bilder(mb, ordner, fall["name"])
    print("FERTIG", ordner)
    if a.oeffnen:
        for f in ("torus3d_schnitt.png", "torus3d_sektor.png", "torus3d_detail.png", "torus3d_geschlossen.png"):
            subprocess.Popen(["eog", str(ordner / f)], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def schnitt(g: pv.UnstructuredGrid) -> pv.PolyData:
    """Oberflaeche nach Entfernen von z > 0 im Halbtorus y < 0 (Schnittflaechen geschlossen)."""
    f = np.minimum(g.points[:, 2], -g.points[:, 1])            # > 0 = entfernen
    g = g.copy(); g.point_data["f"] = f
    return g.clip_scalar(scalars="f", value=0.0, invert=True).extract_surface(algorithm="dataset_surface")


def bilder(mb, ordner: Path, titel: str) -> None:
    fl_pfad = PROJEKT / "sim" / "stellarator" / "bewertung" / titel / "feldlinien.vtm"
    fl = pv.read(fl_pfad)["feldlinien"] if fl_pfad.exists() else None
    teile = {k: schnitt(mb[name]) for k, (name, _) in SCHICHTEN.items()}
    # glTF mit Farben fuer Blender (stellarator/blender_szene.py): Schnittmodell + Feldlinien
    pl = pv.Plotter(off_screen=True)
    for k, m in teile.items():
        if m.n_points:
            pl.add_mesh(m.triangulate(), color=SCHICHTEN[k][1])
    if fl is not None:
        for key in fl.keys():
            if fl[key] is not None and fl[key].n_points > 1:
                pl.add_mesh(fl[key].tube(radius=0.012, n_sides=8).triangulate(), color="#7b2cbf")
    pl.export_gltf(str(ordner / "torus3d.glb")); pl.close()
    ganz = {k: mb[name].extract_surface(algorithm="dataset_surface") for k, (name, _) in SCHICHTEN.items() if k == 7}

    def szene(datei, oberfl, kamera, zoom, text, legende=True, linien=True, einpassen=True):
        pl = pv.Plotter(off_screen=True, window_size=(1800, 1100)); pl.set_background("white")
        for k, m in oberfl.items():
            if m.n_points:
                pl.add_mesh(m, color=SCHICHTEN[k][1], smooth_shading=False, label=SCHICHTEN[k][0])
        if linien and fl is not None:
            for key in fl.keys():
                if fl[key] is not None and fl[key].n_points > 1:
                    pl.add_mesh(fl[key].tube(radius=0.012), color="#7b2cbf")
        if legende:
            pl.add_legend(bcolor="#3a3a3a", face="rectangle", size=(0.24, 0.27), loc="lower left")
        pl.add_text(text, font_size=12, color="black")
        pl.camera_position = kamera
        if einpassen:
            pl.reset_camera()
        pl.camera.zoom(zoom); pl.reset_camera_clipping_range()
        pl.screenshot(ordner / datei); pl.close()

    szene("torus3d_schnitt.png", teile, [(9, -16, 10), (0, 0, 0), (0, 0, 1)], 1.45,
          f"{titel}: Spulen mit Gehaeuse, Verguss, Isolation und Supraleitern (obere Haelfte teilweise entfernt), violett: Feldlinien")
    # Nahaufnahme: Querschnitt einer Spule aussen bei z = 0 (y < 0)
    sk = teile[7]
    pz = sk.points[(np.abs(sk.points[:, 2]) < 0.01) & (sk.points[:, 1] < -1)]
    if len(pz):
        R = np.hypot(pz[:, 0], pz[:, 1]); p0 = pz[np.argmax(R)]
        r = p0 / np.linalg.norm(p0)
        mitte = p0 - 0.15 * r                                   # Mitte des Querschnitts (Gehaeuse aussen -> innen)
        szene("torus3d_sektor.png", teile, [tuple(mitte + 2.2 * r + np.array([0, 0, 2.6])), tuple(mitte - 0.6 * r), (0, 0, 1)], 1.0,
              "Sektor: Querschnitte bei z = 0 mit allen Schichten, violett: Magnetfeldlinien", einpassen=False)
        szene("torus3d_detail.png", teile, [tuple(mitte + 0.55 * r + np.array([0, 0, 0.85])), tuple(mitte), (0, 0, 1)], 1.0,
              "Querschnitt bei z = 0: Gehaeuse, Verguss, Grundisolierung, 108 Leiter (Windungsisolation, Al-Mantel, Kabel)",
              linien=False, einpassen=False)
    szene("torus3d_geschlossen.png", ganz, [(9, -16, 10), (0, 0, 0), (0, 0, 1)], 1.45,
          f"{titel}: geschlossene Spulengehaeuse", legende=False, linien=False)


if __name__ == "__main__":
    main()
