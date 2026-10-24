"""gehaeuse.py — Spulengehaeuse als "Variable Section Sweep" in FreeCAD (parametrisch).

  .venv/bin/python -m stellarator.gehaeuse stellarator/faelle/qa_nfp2_A45_1GW_HTS.json
      [--stationen 40] [--verteilung gleich|kruemmung] [--wand_innen 0.1] [--wand_seite 0.1] [--t_min 0.15] [--t_max 0.5]
      [--name ...] [--oeffnen]

Idee (User): geschlossene 3D-Kurve durch Punkte = INNENSEITE des Gehaeuses (plasmaseitig),
m Skizzen (Standard 40) normal zur Kurve, Loft hindurch. Alles waechst nur nach aussen -> keine Faltung wie bei
den Versatzflaechen der Stuetzschale (Skill stellarator-flaechen).
Die Aussenwand ist variabel: t_min + (t_max - t_min) * f, f = |dF/dl| / max (Lorentzkraft je
Laenge, Biot-Savart, Feld gemittelt ueber 4 Punkte im Wickelpaket).
Nur die Basisspulen werden modelliert, die anderen sind Symmetrie-Klone.
Ausgabe sim/stellarator/gehaeuse/<name>/: gehaeuse.FCStd (parametrisch), gehaeuse.step, *.stl,
pruefung.json, gehaeuse.png, gehaeuse_freecad.png (Screenshot aus FreeCAD).
Braucht DISPLAY (z.B. DISPLAY=:1) fuer den Ansichtsschritt, sonst ist in der GUI alles ausgeblendet.
"""
from __future__ import annotations
import argparse, json, os, subprocess
from pathlib import Path
import numpy as np

from . import spulen as sp
from .lauf import PROJEKT

FREECAD = Path.home() / "Applications" / "FreeCAD_1.1.4.AppImage"
SKRIPT = Path(__file__).with_name("freecad_vss.py")
ANSICHT = Path(__file__).with_name("freecad_ansicht.py")     # GUI-Ansicht nachtragen (sonst alles ausgeblendet)


def kraft_je_laenge(spulen, s, breite, hoehe, seg) -> np.ndarray:
    """|I t x B| [N/m] entlang der Spule; B gemittelt ueber 4 Punkte im Wickelpaket (Eigenfeld endlich)."""
    t, n, b = sp.rahmen(s)
    B = np.mean([sp.biot_savart(s.punkte + 0.25 * (en * breite * n + eb * hoehe * b), seg)
                 for en in (-1, 1) for eb in (-1, 1)], axis=0)
    return np.linalg.norm(s.strom * np.cross(t, B), axis=1)


def stationen(Q, m: int, verteilung: str) -> np.ndarray:
    """Indizes der Skizzen-Stationen auf der Innenkurve. gleich: gleiche Bogenlaenge;
    kruemmung: Bogenlaenge gewichtet mit (1 + kappa*L/2pi). A45: 40 gleich -> Loft weicht
    <= 15 mm von der Spule ab, 20 nach Kruemmung bis 360 mm (Verdrillung, nicht Kruemmung)."""
    d = np.linalg.norm(np.roll(Q, -1, 0) - Q, axis=1)
    if verteilung == "kruemmung":
        t = (np.roll(Q, -1, 0) - np.roll(Q, 1, 0)); t /= np.linalg.norm(t, axis=1, keepdims=True)
        kappa = np.linalg.norm(np.roll(t, -1, 0) - t, axis=1) / d
        d = d * (1 + kappa * d.sum() / (2 * np.pi))
    s = np.r_[0, np.cumsum(d)[:-1]]
    ziel = np.linspace(0, d.sum(), m, endpoint=False)
    idx = np.searchsorted(s, ziel).clip(0, len(Q) - 1)
    return np.unique(idx)


def symmetrie(spulen, nfp: int, n_basis: int) -> list[dict]:
    """Je Nicht-Basisspule: Basisspule + Drehmatrix (Rz(2 pi j/nfp) [* diag(1,-1,-1)])."""
    from scipy.spatial import cKDTree
    kand = []
    for j in range(nfp):
        c, s_ = np.cos(2 * np.pi * j / nfp), np.sin(2 * np.pi * j / nfp)
        Rz = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
        kand += [Rz, Rz @ np.diag([1.0, -1.0, -1.0])]
    klone = []
    for i, s in enumerate(spulen[n_basis:], n_basis):
        baum = cKDTree(s.punkte)
        best = min(((baum.query(spulen[k].punkte @ M.T)[0].max(), k, M) for k in range(n_basis) for M in kand),
                   key=lambda x: x[0])
        if best[0] > 0.02 * np.ptp(s.punkte, axis=0).max():
            raise ValueError(f"{s.name}: keine Symmetrie-Abbildung gefunden ({best[0]:.3f} m)")
        klone.append({"name": s.name, "basis": best[1], "matrix": best[2].tolist()})
    return klone


def eingabe(fall: dict, a, ordner: Path) -> Path:
    c = fall["spulen"]
    spulen, geo = sp.lade_spulensatz(c)
    kz = PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"] / "kennzahlen.json"
    faktor = json.loads(kz.read_text())["strom"]["kalibrierfaktor"] if kz.exists() else 1.0   # nur fuer MN/m
    for s in spulen:
        s.strom *= faktor
    br, ho = c["wickel_breite_m"], c["wickel_hoehe_m"]
    nb = geo["n_basis"]; seg = sp.segmente(spulen)
    f = [kraft_je_laenge(spulen, s, br, ho, seg) for s in spulen[:nb]]
    fmax = max(x.max() for x in f)
    mm = 1e3
    basis = []
    for k, s in enumerate(spulen[:nb]):
        t, n, b = sp.rahmen(s)
        Q = s.punkte - (0.5 * br + a.wand_innen) * n             # Innenseite (plasmaseitig)
        idx = stationen(Q, a.stationen, a.verteilung)
        fs = np.convolve(np.r_[f[k][-4:], f[k], f[k][:4]], np.ones(9) / 9, "valid") / fmax  # geglaettet
        basis.append({"name": s.name, "typ": s.typ, "kurve": (Q * mm).tolist(), "mitte": (s.punkte * mm).tolist(),
                      "stationen": [{"punkt": (Q[i] * mm).tolist(), "n": n[i].tolist(), "b": b[i].tolist(),
                                     "t": t[i].tolist(), "f": float(fs[i])} for i in idx]})
    d = {"name": fall["name"], "ausgabe": str(ordner),
         "parameter": {"wand_innen": a.wand_innen * mm, "wand_seite": a.wand_seite * mm, "wp_breite": br * mm,
                       "wp_hoehe": ho * mm, "t_min": a.t_min * mm, "t_max": a.t_max * mm},
         "basis": basis, "klone": symmetrie(spulen, geo["nfp"], nb),
         "kraft_max_MN_m": fmax / 1e6}
    ordner.mkdir(parents=True, exist_ok=True)
    p = ordner / "vss_eingabe.json"; p.write_text(json.dumps(d))
    return p


def bild(ordner: Path, titel: str) -> Path:
    import pyvista as pv
    pr = json.loads((ordner / "pruefung.json").read_text())
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1000)); pl.set_background("white")
    ueber = {x["a"] for x in pr["ueberlappung"]} | {x["b"] for x in pr["ueberlappung"]}
    for st in sorted(ordner.glob("gehaeuse_*.stl")):
        pl.add_mesh(pv.read(st), color="#8a9bb0", smooth_shading=True)
    for st in sorted(ordner.glob("wp_*.stl")):
        pl.add_mesh(pv.read(st), color="#c87533", opacity=0.6)
    pl.add_text(f"{titel}: Spulengehaeuse (Variable Section Sweep, FreeCAD)  |  "
                f"Ueberlappungen: {len(pr['ueberlappung'])}", font_size=11, color="black")
    pl.reset_camera(); r = pl.bounds[1]                     # Kamera fest auf Abstand (sonst Nahebene)
    pl.camera_position = [(2.2 * r, -2.2 * r, 1.8 * r), (0, 0, 0), (0, 0, 1)]
    pl.reset_camera_clipping_range()
    p = ordner / "gehaeuse.png"; pl.screenshot(p); pl.close()
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Spulengehaeuse als Variable Section Sweep (FreeCAD)")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--stationen", type=int, default=40)
    ap.add_argument("--verteilung", choices=["gleich", "kruemmung"], default="gleich")
    ap.add_argument("--wand_innen", type=float, default=0.10, help="m, plasmaseitige Wand")
    ap.add_argument("--wand_seite", type=float, default=0.10, help="m, Seitenwand")
    ap.add_argument("--t_min", type=float, default=0.15, help="m, Aussenwand bei kleiner Kraft")
    ap.add_argument("--t_max", type=float, default=0.50, help="m, Aussenwand bei max. Kraft")
    ap.add_argument("--name")
    ap.add_argument("--oeffnen", action="store_true", help="FreeCAD-GUI mit dem Modell starten")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text())
    name = a.name or fall["name"]
    ordner = PROJEKT / "sim" / "stellarator" / "gehaeuse" / name
    p = eingabe(fall, a, ordner)
    r = subprocess.run([str(FREECAD), "freecadcmd", str(SKRIPT)], env={**os.environ, "VSS_EINGABE": str(p)},
                       capture_output=True, text=True)
    zeilen = [z for z in r.stdout.splitlines() if "VSS_FERTIG" in z]
    if not zeilen:
        print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit("FreeCAD fehlgeschlagen")
    print(zeilen[-1])
    print(json.dumps(json.loads((ordner / "pruefung.json").read_text())["spulen"], indent=1))
    print("BILD", bild(ordner, name))
    # freecadcmd speichert keine Ansicht -> in der GUI waere nur der Baum zu sehen; einmal per GUI nachtragen
    if os.environ.get("DISPLAY"):
        subprocess.run([str(FREECAD), str(ANSICHT)], env={**os.environ, "VSS_FCSTD": str(ordner / "gehaeuse.FCStd")},
                       capture_output=True, timeout=600)
        print("BILD", ordner / "gehaeuse_freecad.png")
    else:
        print("WARNUNG: kein DISPLAY -> Ansicht nicht gesetzt; spaeter: VSS_FCSTD=... <AppImage> stellarator/freecad_ansicht.py")
    if a.oeffnen:
        subprocess.Popen([str(FREECAD), str(ordner / "gehaeuse.FCStd")], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
