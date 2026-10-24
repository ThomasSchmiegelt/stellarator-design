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


def wp_rand(s, br: float, ho: float) -> np.ndarray:
    """Randpunkte des Wickelpakets: 4 Ecken + 4 Kantenmitten je Mittellinienpunkt (N*8, 3)."""
    t, n, b = sp.rahmen(s)
    q = [(en, eb) for en in (-1, 0, 1) for eb in (-1, 0, 1) if (en, eb) != (0, 0)]
    return np.vstack([s.punkte + 0.5 * (en * br * n + eb * ho * b) for en, eb in q])


def freiraum(spulen, k: int, idx, br: float, ho: float, spiel: float, fenster: float) -> dict:
    """Halber freier Platz [m] zur naechsten fremden Spule je Station: links (-b), rechts (+b), aussen (+n).

    Fremde Wickelpakete als Randpunkte (wp_rand); beruecksichtigt im Fenster |dt| < fenster (Bereich
    zwischen den Stationen, wo der Loft interpoliert), seitlich nur im Band der eigenen Pakettiefe.
    Ergebnis: (Abstand - eigene Halbbreite - spiel) / 2, jede Spule bekommt die Haelfte des Spalts."""
    t, n, b = sp.rahmen(spulen[k])
    P = spulen[k].punkte
    Q = np.vstack([wp_rand(s, br, ho) for i, s in enumerate(spulen) if i != k])
    out = {"links": [], "rechts": [], "aussen": []}
    for i in idx:
        d = Q - P[i]
        dt, dn, db = d @ t[i], d @ n[i], d @ b[i]
        nah = np.abs(dt) < fenster
        seitlich = nah & (np.abs(dn) < 0.5 * br)
        oben = nah & (np.abs(db) < 0.5 * ho)
        def frei(sel, a, halb):
            return float(((a[sel].min() if sel.any() else 99.0) - halb - spiel) / 2)
        out["rechts"].append(frei(seitlich & (db > 0), db, 0.5 * ho))
        out["links"].append(frei(seitlich & (db < 0), -db, 0.5 * ho))
        out["aussen"].append(frei(oben & (dn > 0), dn, 0.5 * br))
    return out


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


def kandidaten(nfp: int) -> list[np.ndarray]:
    """Symmetrie-Abbildungen: Rz(2 pi j/nfp) und Rz * diag(1,-1,-1) (Stellaratorsymmetrie)."""
    kand = []
    for j in range(nfp):
        c, s_ = np.cos(2 * np.pi * j / nfp), np.sin(2 * np.pi * j / nfp)
        Rz = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
        kand += [Rz, Rz @ np.diag([1.0, -1.0, -1.0])]
    return kand


def symmetrie(spulen, nfp: int, n_basis: int) -> list[dict]:
    """Je Nicht-Basisspule: Basisspule + Drehmatrix aus kandidaten()."""
    from scipy.spatial import cKDTree
    kand = kandidaten(nfp)
    klone = []
    for i, s in enumerate(spulen[n_basis:], n_basis):
        baum = cKDTree(s.punkte)
        best = min(((baum.query(spulen[k].punkte @ M.T)[0].max(), k, M) for k in range(n_basis) for M in kand),
                   key=lambda x: x[0])
        if best[0] > 0.02 * np.ptp(s.punkte, axis=0).max():
            raise ValueError(f"{s.name}: keine Symmetrie-Abbildung gefunden ({best[0]:.3f} m)")
        klone.append({"name": s.name, "basis": best[1], "matrix": best[2].tolist()})
    return klone


def permutationen(spulen, kand) -> list[list[int]]:
    """Je Abbildung M: perm[i] = j mit M P_i = P_j (Spule i wird auf Spule j abgebildet)."""
    from scipy.spatial import cKDTree
    S = [s.punkte.mean(0) for s in spulen]
    baum = cKDTree(np.array(S))
    return [[int(baum.query(M @ c)[1]) for c in S] for M in kand]


def keil_bereich(dmin: np.ndarray, spanne: float) -> np.ndarray:
    """Indizes (zyklisch zusammenhaengend) um den engsten Abstand mit dmin <= dmin.min() + spanne."""
    i0 = int(np.argmin(dmin)); N = len(dmin); ok = dmin <= dmin.min() + spanne
    lo = hi = i0
    while ok[(lo - 1) % N] and (i0 - lo) < N // 2:
        lo -= 1
    while ok[(hi + 1) % N] and (hi - i0) < N // 2:
        hi += 1
    return np.arange(lo, hi + 1) % N


def verbinder(spulen, nfp: int, br: float, ho: float, a) -> tuple[list[dict], list[dict]]:
    """Verbindungsstuecke zwischen toroidal benachbarten Gehaeusen.

    Je Paar (a, b) a.verbinder Stationen gleichmaessig entlang Spule a; Partner = naechster Punkt
    auf Spule b. Skizze A/B: Rechteck (x = n "nach aussen", y = t entlang der Spule) mittig auf
    Hoehe des Wickelpakets, um wand_seite/2 in die Seitenwand eingelassen (Verschmelzen, ohne das
    Wickelpaket zu beruehren). Gleichwertige Paare werden Symmetrie-Klone des ersten.
    Rueckgabe: kanonische Paare (mit Skizzenlagen in mm) und Klone (Paar-Index + Matrix)."""
    phi = [np.arctan2(*s.punkte.mean(0)[1::-1]) for s in spulen]
    reihe = list(np.argsort(phi))
    paare = [(int(reihe[i]), int(reihe[(i + 1) % len(reihe)])) for i in range(len(reihe))]
    kand = kandidaten(nfp); perm = permutationen(spulen, kand)
    rahmen = [sp.rahmen(s) for s in spulen]
    versatz = 0.5 * ho + 0.5 * a.wand_seite                  # Mitte der Seitenwand
    kanon, klone = [], []
    for pa, pb in paare:
        treffer = next(((k, M) for k, kp in enumerate(kanon) for M, pm in zip(kand, perm)
                        if {pm[kp["a"]], pm[kp["b"]]} == {pa, pb}), None)
        if treffer:
            klone.append({"name": f"V_{spulen[pa].name}_{spulen[pb].name}", "kanon": treffer[0],
                          "matrix": treffer[1].tolist(), "a": spulen[pa].name, "b": spulen[pb].name})
            continue
        Pa, Pb = spulen[pa].punkte, spulen[pb].punkte
        ta, na, ba = rahmen[pa]; tb, nb_, bb = rahmen[pb]
        # Keil (Bachmann 2024: Gewoelbe innen): zusammenhaengender Bereich um den engsten Abstand
        dmin = np.array([np.linalg.norm(Pb - p, axis=1).min() for p in Pa])
        bereich = keil_bereich(dmin, a.keil_spanne) if a.keil else np.array([], int)
        keil = []
        for i in bereich[np.linspace(0, len(bereich) - 1, a.keil).astype(int)] if len(bereich) else []:
            j = int(np.argmin(np.linalg.norm(Pb - Pa[i], axis=1)))
            d = Pb[j] - Pa[i]
            ca = Pa[i] + np.sign(ba[i] @ d) * versatz * ba[i]; cb = Pb[j] + np.sign(bb[j] @ -d) * versatz * bb[j]
            y = (cb - ca) / np.linalg.norm(cb - ca)
            x = na[i] + nb_[j]; x -= (x @ y) * y; x /= np.linalg.norm(x)
            keil.append({"c": (0.5 * (ca + cb) * 1e3).tolist(), "x": x.tolist(), "y": y.tolist(),
                         "L": float(np.linalg.norm(cb - ca) * 1e3)})
        st = []
        for i in np.linspace(0, len(Pa), a.verbinder, endpoint=False).astype(int):
            j = int(np.argmin(np.linalg.norm(Pb - Pa[i], axis=1)))
            d = Pb[j] - Pa[i]
            sa, sb = np.sign(ba[i] @ d), np.sign(bb[j] @ -d)
            ya = ta[i]; yb = tb[j] * np.sign(tb[j] @ ta[i])      # gleiche Laufrichtung -> kein Verdrehen
            ca = Pa[i] + sa * versatz * ba[i]; cb = Pb[j] + sb * versatz * bb[j]
            st.append({"A": {"c": (ca * 1e3).tolist(), "x": na[i].tolist(), "y": ya.tolist()},
                       "B": {"c": (cb * 1e3).tolist(), "x": nb_[j].tolist(), "y": yb.tolist()},
                       "laenge_m": float(np.linalg.norm(cb - ca)),
                       "im_keil": bool(len(keil)) and i in set(bereich.tolist())})   # nur Ersatz, falls der Keil scheitert
        kanon.append({"name": f"V_{spulen[pa].name}_{spulen[pb].name}", "a": pa, "b": pb, "stationen": st,
                      "keil": keil})
    return kanon, klone


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
    korr = json.loads(Path(a.korrektur).read_text()) if a.korrektur else {}   # aus freecad_reparatur (mm)
    for k, s in enumerate(spulen[:nb]):
        t, n, b = sp.rahmen(s)
        Q = s.punkte - (0.5 * br + a.wand_innen) * n             # Innenseite (plasmaseitig)
        idx = stationen(Q, a.stationen, a.verteilung)
        fs = np.convolve(np.r_[f[k][-4:], f[k], f[k][:4]], np.ones(9) / 9, "valid") / fmax  # geglaettet
        fenster = 0.5 * s.laenge() / len(idx) + 0.5 * np.hypot(br, ho)
        fr = freiraum(spulen, k, idx, br, ho, a.spiel, fenster)
        basis.append({"name": s.name, "typ": s.typ, "kurve": (Q * mm).tolist(), "mitte": (s.punkte * mm).tolist(),
                      "stationen": [{"punkt": (Q[i] * mm).tolist(), "n": n[i].tolist(), "b": b[i].tolist(),
                                     "t": t[i].tolist(), "f": float(fs[i]),
                                     **{f"frei_{q}": min(max(a.wand_min, fr[q][j]) * mm,
                                                         korr.get(f"{q[0]}_{k}_{j}", 1e9)) for q in fr},
                                     # Innenwand: nur ueber die Reparatur (i_<k>_<j>), sonst wand_innen
                                     "frei_innen": max(a.wand_min * mm, korr.get(f"i_{k}_{j}", a.wand_innen * mm))}
                                    for j, i in enumerate(idx)]})
    d = {"name": fall["name"], "ausgabe": str(ordner),
         "parameter": {"wand_innen": a.wand_innen * mm, "wand_seite": a.wand_seite * mm, "wp_breite": br * mm,
                       "wp_hoehe": ho * mm, "t_min": a.t_min * mm, "t_max": a.t_max * mm},
         "basis": basis, "klone": symmetrie(spulen, geo["nfp"], nb),
         "kraft_max_MN_m": fmax / 1e6, "spulen_namen": [s.name for s in spulen]}
    if a.verbinder:
        d["verbinder"], d["verbinder_klone"] = verbinder(spulen, geo["nfp"], br, ho, a)
        d["parameter"] |= {"verb_breite": a.verb_breite * mm, "verb_tiefe": a.verb_tiefe * mm,
                           "keil_tiefe": a.keil_tiefe * mm, "keil_versatz": a.keil_versatz * mm}
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
    for st in sorted(ordner.glob("verbinder_*.stl")):
        pl.add_mesh(pv.read(st), color="#4a5866", smooth_shading=True)
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
    ap.add_argument("--spiel", type=float, default=0.005, help="m, Mindestspalt zwischen Nachbargehaeusen")
    ap.add_argument("--wand_min", type=float, default=0.005, help="m, duennste zulaessige Wand (Skizze bleibt gueltig)")
    ap.add_argument("--korrektur", help="korrektur.json aus stellarator.aufbau --reparieren (Freimasse je Station, mm)")
    ap.add_argument("--verbinder", type=int, default=10, help="Verbindungsstuecke je Nachbarpaar (0 = keine)")
    ap.add_argument("--verb_breite", type=float, default=0.6, help="m, entlang der Spule")
    ap.add_argument("--verb_tiefe", type=float, default=0.6, help="m, quer (Richtung n)")
    ap.add_argument("--keil", type=int, default=0,
                    help="Skizzen im Keil auf der Torus-Innenseite (0 = kein Keil; Standard aus, B-024: gmsh scheitert)")
    ap.add_argument("--keil_spanne", type=float, default=1.0, help="m, Keil wo Abstand <= min + spanne")
    ap.add_argument("--keil_versatz", type=float, default=0.005,
                    help="m, Keil wird mit Wickelpaket + Versatz geschnitten -> ueberlappt die Gehaeusewand sauber")
    ap.add_argument("--keil_tiefe", type=float, default=0.755, help="m, Tiefe des Keils (Richtung n)")
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
