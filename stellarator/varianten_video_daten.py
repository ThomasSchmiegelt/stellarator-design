"""varianten_video_daten.py — Daten fuer das Variantenvideo (Blender): PicoGK-Netze ausduennen, Varianten einordnen.

  .venv/bin/python -m stellarator.varianten_video_daten        # vorhandene Modelle; erneut aufrufen, wenn der Katalog waechst
  .venv/bin/python -m stellarator.varianten_video_daten --neu  # vorhandene Netze ueberschreiben (statt loeschen)

Quelle: Katalog (Liste 2, alle geometrisch darstellbaren doe1-Entwuerfe, PicoGK 80 mm) und modell3d/0169 (Liste 1).
Einordnung aus daten/doe1_auswertung.json (bereinigt): zulaessig (alle acht Grenzen), knapp (kleinste Reserve > -15 %),
ausfall (sonst). "Wild" = die 18 Entwuerfe mit der kleinsten Reserve (am weitesten von den Grenzen entfernt).
Ausgabe (zweite Platte, Verweis sim/video_varianten): netze/<nr>_raster.npz (stark ausgeduennt, fuer das Feld aller
Entwuerfe), netze/<nr>_voll.npz (wilde + zulaessige, fein), netze/0169_schnitt.npz (Treppenschnitt), varianten.json.
Je Teil: v (float32, m), f (int32). Pausierbar ueber ~/bin/rechnung (im Scope starten), Fertiges wird uebersprungen.
"""
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KATALOG = Path(os.environ.get("FUSION_KATALOG", ROOT / "sim" / "kopplung" / "katalog3d"))
LISTE1 = ROOT / "sim" / "kopplung" / "modell3d"
KOP = ROOT / "sim" / "kopplung"
ORDNER = ROOT / "sim" / "video_varianten"
NETZE = ORDNER / "netze"
N_WILD = 15
NEU = False
RASTER = {"gehaeuse": 14000, "verbinder": 8000, "plasma": 2000}       # Lager nur im Schnitt (verdeckt sonst)       # Dreiecke im Feld
VOLL = {"gehaeuse": 400000, "verbinder": 150000, "plasma": 40000, "package_vakuumgefaess": 60000}
SCHNITT = {"plasma": 40000, "package_erstwand_blanket": 80000, "package_abschirmung": 80000,
           "package_vakuumgefaess": 80000, "wickelpaket": 200000, "gehaeuse": 500000, "verbinder": 200000, "lager": 40000}


def lade(pfad: Path, ziel: int):
    import pyvista as pv
    import fast_simplification
    m = pv.read(pfad).triangulate().clean()
    v = np.asarray(m.points, np.float32); f = m.faces.reshape(-1, 4)[:, 1:].astype(np.int32)
    if len(f) > ziel * 1.1:
        v, f = fast_simplification.simplify(v, f, target_reduction=1 - ziel / len(f))
    return (v / 1000.0).astype(np.float32), f.astype(np.int32)        # mm -> m


FE_MAT = {"wickelpaket": [1], "gehaeuse": [3], "verbinder": [4]}


def fe_flaeche(vtu: Path, teil: str):
    """Exakte Oberflaeche eines Teils aus dem Rechenmodell (Hex-Netz, Meter). Das ist dieselbe Geometrie, die die
    Kette an PicoGK uebergibt; die PicoGK-Netze (80 mm Voxel, auf 150 k Dreiecke ausgeduennt) sind fuer
    Nahaufnahmen zu grob (Knitter, Treppen)."""
    import pyvista as pv
    g = pv.read(vtu)
    m = g.extract_cells(np.where(np.isin(np.asarray(g.cell_data["material"]), FE_MAT[teil]))[0])
    m = m.extract_surface(algorithm="dataset_surface").triangulate().clean()
    return np.asarray(m.points, np.float32), m.faces.reshape(-1, 4)[:, 1:].astype(np.int32)


def speichere(name: str, quelle: Path, teile: dict, keil=None, fe: Path | None = None) -> bool:
    """fe: struktur.vtu des Rechenmodells -> Gehaeuse, Verbinder, Wickelpaket daraus (glatt); Plasma, Package und
    Lager aus PicoGK."""
    ziel = NETZE / f"{name}.npz"
    if ziel.exists() and not NEU:
        return True
    d = {}
    for t, n in teile.items():
        p = quelle / f"{t}.stl"
        if fe is not None and fe.exists() and t in FE_MAT:
            v, f = fe_flaeche(fe, t)
        elif not p.exists():
            return False
        else:
            v, f = lade(p, n)
        if keil is not None and keil.get(t) is not None:
            v, f = ohne_keil(v, f, -100.0, keil[t])
        d[f"{t}_v"], d[f"{t}_f"] = v, f
    np.savez_compressed(ziel, **d)
    return True


def ohne_keil(v, f, phi_a, phi_b):
    """Keil phi_a..phi_b (Grad um z) genau abschneiden (Ebenenschnitt wie in den Berichtsbildern, keine Zacken)."""
    import pyvista as pv
    from .picogk_modell import ohne_keil as keil_pv
    m = keil_pv(pv.PolyData(v.astype(float), np.c_[np.full(len(f), 3), f].ravel()), phi_a, phi_b)
    m = m.extract_surface().triangulate().clean()
    return np.asarray(m.points, np.float32), m.faces.reshape(-1, 4)[:, 1:].astype(np.int32)


def voxel(name: str, quelle: Path, teile, h: float = 0.3) -> None:
    """Voxelfeld fuer den PicoGK-Vorspann: Oberflaeche dicht abtasten, auf ein Gitter der Kantenlaenge h runden
    (so sieht man, dass PicoGK mit Voxeln rechnet). Je Teil die Gitterindizes (int16)."""
    ziel = NETZE / f"{name}.npz"
    if ziel.exists() and not NEU:
        return
    rng = np.random.default_rng(1); d = {"h": np.float32(h)}
    for t in teile:
        v, f = lade(quelle / f"{t}.stl", 200000)
        tri = v[f]; fl = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
        n = int(fl.sum() / (h * h) * 20)
        k = rng.choice(len(f), n, p=fl / fl.sum()); r = rng.random((n, 2)); m = r.sum(1) > 1; r[m] = 1 - r[m]
        p = tri[k, 0] + r[:, :1] * (tri[k, 1] - tri[k, 0]) + r[:, 1:] * (tri[k, 2] - tri[k, 0])
        d[t] = schliessen(np.unique(np.floor(p / h).astype(np.int16), axis=0))
    belegt = set()                      # jedes Voxel nur einem Teil geben: doppelte Wuerfel flimmern schwarz
    for t in teile:
        neu = [i for i, x in enumerate(map(tuple, d[t])) if x not in belegt]
        belegt.update(map(tuple, d[t][neu])); d[t] = d[t][neu]
    np.savez_compressed(ziel, **d)


def schliessen(idx, n: int = 2):
    """Loecher in der Voxelschale schliessen (morphologisches Schliessen), sonst sieht man durch Luecken ins dunkle
    Innere (schwarze Flecken im Film). Die Wand wird dabei nicht dicker."""
    from scipy import ndimage
    o = idx.min(0) - n - 1; g = np.zeros(tuple(idx.max(0) - o + n + 2), bool); g[tuple((idx - o).T)] = True
    g = ndimage.binary_closing(g, ndimage.generate_binary_structure(3, 1), iterations=n, border_value=0)
    return (np.argwhere(g) + o).astype(np.int16)


def main():
    global NEU
    import sys
    NEU = "--neu" in sys.argv
    from .picogk_modell import KEIL_BIS
    NETZE.mkdir(parents=True, exist_ok=True)
    erg = json.loads((ROOT / "daten" / "doe1_auswertung.json").read_text()); Z = erg["zeilen"]
    da = sorted(p.parent.name for p in KATALOG.glob("*/gehaeuse.stl") if (p.parent / "pruefung.json").exists())
    def status(nr):
        z = Z[nr]
        return "zulaessig" if z["alle_ok"] else ("knapp" if z["robust"] > -0.15 else "ausfall")
    wild = sorted([nr for nr in da if not Z[nr]["alle_ok"]], key=lambda nr: Z[nr]["robust"])[:N_WILD]
    zul = [nr for nr in erg["zulaessig"] if nr in da]
    eintraege = []
    for i, nr in enumerate(da):
        fe = KOP / Z[nr]["quelle"] / "punkte" / nr / "struktur.vtu"
        ok = speichere(f"{nr}_raster", KATALOG / nr, RASTER)
        if ok and (nr in wild or nr in zul):
            ok = speichere(f"{nr}_voll", KATALOG / nr, VOLL, fe=fe)
        if ok:
            z = Z[nr]
            eintraege.append({"nr": nr, "status": status(nr), "wild": nr in wild, "robust": z["robust"],
                              "sigma99": z["wert_stahl"], "spulen": z["spulen"], "engpass": z["engpass"]})
        print(f"{i + 1}/{len(da)} {nr} {'ok' if ok else 'fehlt'}", flush=True)
    fe169 = KOP / Z["0169"]["quelle"] / "punkte" / "0169" / "struktur.vtu"
    speichere("0169_schnitt", LISTE1 / "0169", SCHNITT, keil=KEIL_BIS, fe=fe169)
    speichere("0169_glatt", LISTE1 / "0169", VOLL, fe=fe169)
    speichere("0169_picogk", LISTE1 / "0169", {"gehaeuse": 150000, "verbinder": 150000, "plasma": 150000})   # echtes PicoGK-Netz (80 mm)
    voxel("0169_voxel", LISTE1 / "0169", ("gehaeuse", "verbinder", "plasma"))
    rang = {nr: k for k, nr in enumerate(erg["zulaessig"])}
    (ORDNER / "varianten.json").write_text(json.dumps({
        "varianten": eintraege, "wild": [nr for nr in wild if any(e["nr"] == nr for e in eintraege)],
        "zulaessig": sorted(zul, key=rang.get), "anzahl_katalog_soll": sum(1 for z in Z.values() if z["durchdringung"] == 0)},
        indent=1))
    print("Varianten:", len(eintraege), "wild:", len(wild), "zulaessig:", zul, flush=True)


if __name__ == "__main__":
    main()
