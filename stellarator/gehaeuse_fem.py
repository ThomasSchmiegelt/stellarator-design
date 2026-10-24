"""gehaeuse_fem.py — Spulengehaeuse + Verbinder (FreeCAD-STEP) -> gmsh -> Elmer: Lorentzkraft -> Spannung.

  .venv/bin/python -m stellarator.gehaeuse_fem stellarator/faelle/qa_nfp2_A45_1GW_HTS.json
      [--h_stahl 0.2 --h_wp 0.3 --h_luft 3 --wachstum 0.3 --rand 15] [--name X] [--nur_netz] [--nur_auswerten]

Voraussetzungen: bewerte (Kalibrierfaktor) und gehaeuse (stahl.step, wp.step) auf denselben Fall.
Netz: OCC-Import (mm -> m), Fragment mit dem Luftquader -> konform. Body 1..n Wickelpakete
(Zuordnung ueber den Schwerpunkt zur Spule), n+1 Stahl (Gehaeuse + Verbinder), n+2 Luft,
Boundary 1 = Quader. Netzweite: konstant je Bereich, in der Luft wachsend mit dem Abstand zur
Wicklungsflaeche (Torus R_w, a_w aus den Spulenpunkten).
Elmer-Lauf und Auswertung wie stellarator/struktur.py (ein Lauf, 3-2-1-Lagerung im Stahl).
Ausgabe sim/stellarator/gehaeuse_fem/<fall>/.
"""
from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path
import numpy as np
import gmsh

from . import spulen as sp, elmer, struktur
from .lauf import PROJEKT


def netz(spulen, quelle: Path, ordner: Path, h_stahl: float, h_wp: float, h_luft: float,
         wachstum: float, rand_m: float) -> dict:
    ordner.mkdir(parents=True, exist_ok=True)
    n = len(spulen)
    P = np.vstack([s.punkte for s in spulen])
    R_w = np.hypot(P[:, 0], P[:, 1]).mean()
    a_w = np.hypot(np.hypot(P[:, 0], P[:, 1]) - R_w, P[:, 2]).mean()
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 2)
    try:
        t0 = time.time(); m = gmsh.model; occ = m.occ
        gmsh.option.setString("Geometry.OCCTargetUnit", "M")
        # fast deckungsgleiche Flaechen (Keil- und Gehaeuseschnitt am selben Wickelpaket) zusammenfuehren
        gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-4)
        wp = occ.importShapes(str(quelle / "wp.step"))
        stahl = occ.importShapes(str(quelle / "stahl.step"))
        wp = [x for x in wp if x[0] == 3]; stahl = [x for x in stahl if x[0] == 3]
        # Stahl vorab vereinigen: Gehaeuse, Verbinder und Keile ueberlappen -> sonst Doppelflaechen
        if len(stahl) > 1:
            stahl, _ = occ.fuse(stahl[:1], stahl[1:])
            stahl = [x for x in stahl if x[0] == 3]
        lo, hi = P.min(0) - rand_m, P.max(0) + rand_m
        box = occ.addBox(*lo, *(hi - lo))
        occ.synchronize()
        # Wickelpaket-Volumen der Spule zuordnen (Schwerpunkt), vor dem Fragment
        sw = np.array([occ.getCenterOfMass(3, t) for _, t in wp])
        sc = np.array([s.punkte.mean(0) for s in spulen])
        zu = [int(np.argmin(np.linalg.norm(sw - c, axis=1))) for c in sc]
        if len(set(zu)) != n:
            raise SystemExit(f"Zuordnung Wickelpaket -> Spule nicht eindeutig: {zu}")
        eingabe = wp + stahl + [(3, box)]
        _, karte = occ.fragment(eingabe, [], removeObject=True, removeTool=True)
        occ.synchronize()
        teile_wp = [{t for _, t in karte[k]} for k in range(len(wp))]
        teile_stahl = set().union(*({t for _, t in karte[len(wp) + k]} for k in range(len(stahl))))
        alle = {t for _, t in m.getEntities(3)}
        belegt = set().union(*teile_wp)
        teile_stahl -= belegt
        teile_luft = alle - belegt - teile_stahl
        for i in range(n):
            m.addPhysicalGroup(3, sorted(teile_wp[zu[i]]), i + 1)
        m.addPhysicalGroup(3, sorted(teile_stahl), n + 1)
        m.addPhysicalGroup(3, sorted(teile_luft), n + 2)
        aussen = [t for d, t in m.getBoundary([(3, t) for t in teile_luft], oriented=False) if d == 2]
        quader = [t for t in aussen if any(abs(v - g) < 1e-3 for v, g in
                                           zip(occ.getCenterOfMass(2, t), lo)) or any(
            abs(v - g) < 1e-3 for v, g in zip(occ.getCenterOfMass(2, t), hi))]
        m.addPhysicalGroup(2, quader, 1)
        # Netzweite: Stahl / Wickelpaket konstant, Luft waechst mit dem Abstand zur Wicklungsflaeche
        f = m.mesh.field
        fs = f.add("Constant"); f.setNumber(fs, "VIn", h_stahl); f.setNumber(fs, "VOut", 1e9)
        f.setNumbers(fs, "VolumesList", sorted(teile_stahl)); f.setNumber(fs, "IncludeBoundary", 1)
        fw = f.add("Constant"); f.setNumber(fw, "VIn", h_wp); f.setNumber(fw, "VOut", 1e9)
        f.setNumbers(fw, "VolumesList", sorted(belegt))
        fl = f.add("MathEval")
        f.setString(fl, "F", f"Min({h_luft}, {h_stahl} + {wachstum}*Fabs(Sqrt((Sqrt(x*x+y*y)-{R_w:.4f})^2+z*z)-{a_w:.4f}))")
        fmin = f.add("Min"); f.setNumbers(fmin, "FieldsList", [fs, fw, fl]); f.setAsBackgroundMesh(fmin)
        for k in ("MeshSizeExtendFromBoundary", "MeshSizeFromPoints", "MeshSizeFromCurvature"):
            gmsh.option.setNumber(f"Mesh.{k}", 0)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.option.setNumber("Mesh.AngleToleranceFacetOverlap", 0.01)   # Standard 0,1 Grad: zu streng bei Splittern
        t_geo = time.time() - t0
        m.mesh.generate(3)
        n_tet = sum(len(x) for x in m.mesh.getElements(3)[1])
        gmsh.write(str(ordner / "netz.msh"))
        t_netz = time.time() - t0
    finally:
        gmsh.finalize()
    subprocess.run(["ElmerGrid", "14", "2", "netz.msh", "-autoclean"], cwd=ordner, check=True, capture_output=True)
    (ordner / "netz.msh").unlink()
    return {"n_tet": n_tet, "t_geometrie_s": t_geo, "t_netz_s": t_netz, "n_stahl_volumen": len(teile_stahl),
            "wicklungstorus_m": [R_w, a_w], "bodies": {"wickelpakete": [1, n], "stahl": n + 1, "luft": n + 2}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Spulengehaeuse + Verbinder: Lorentzkraft -> Spannung (Elmer)")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--h_stahl", type=float, default=0.2)
    ap.add_argument("--h_wp", type=float, default=0.3)
    ap.add_argument("--h_luft", type=float, default=3.0)
    ap.add_argument("--wachstum", type=float, default=0.3, help="Zunahme der Netzweite je m Abstand in der Luft")
    ap.add_argument("--rand", type=float, default=15.0)
    ap.add_argument("--mit_swap", action="store_true", help="halben freien Swap zum RAM zaehlen (Elmer wird langsamer)")
    ap.add_argument("--name")
    ap.add_argument("--nur_netz", action="store_true")
    ap.add_argument("--nur_auswerten", action="store_true")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text()); c = fall["spulen"]
    kz_pfad = PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"] / "kennzahlen.json"
    quelle = PROJEKT / "sim" / "stellarator" / "gehaeuse" / fall["name"]
    if not kz_pfad.exists():
        raise SystemExit(f"zuerst: .venv/bin/python -m stellarator.bewerte {a.fall}")
    if not (quelle / "stahl.step").exists():
        raise SystemExit(f"zuerst: .venv/bin/python -m stellarator.gehaeuse {a.fall}")
    kz = json.loads(kz_pfad.read_text())
    spulen, _ = sp.lade_spulensatz(c)
    for s in spulen:
        s.strom *= kz["strom"]["kalibrierfaktor"]
    b, h = c["wickel_breite_m"], c["wickel_hoehe_m"]
    ordner = PROJEKT / "sim" / "stellarator" / "gehaeuse_fem" / (a.name or fall["name"]); ordner.mkdir(parents=True, exist_ok=True)
    erg_pfad = ordner / "ergebnis.json"
    erg = json.loads(erg_pfad.read_text()) if erg_pfad.exists() else {}
    erg |= {"fall": fall["name"], "parameter": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()},
            "material": {"stahl": struktur.STAHL, "wickelpaket": struktur.WP},
            "geometrie": json.loads((quelle / "pruefung.json").read_text()) | {"quelle": str(quelle)}}
    erg["geometrie"].pop("spulen", None)
    n = len(spulen)
    if not a.nur_auswerten:
        erg["netz"] = netz(spulen, quelle, ordner, a.h_stahl, a.h_wp, a.h_luft, a.wachstum, a.rand)
        lager = struktur.lagerknoten(ordner, n + 1)
        struktur.schreibe_sif(spulen, b, h, ordner, lager, luft=("luft",))
        erg["lagerknoten"] = lager
        bedarf = erg["netz"]["n_tet"] * elmer.KB_PRO_TET * 1.3 / 1e6
        mi = {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}
        frei = mi["MemAvailable"] + (0.5 * mi["SwapFree"] if a.mit_swap else 0.0)   # Swap: langsam, aber geht
        erg["ram_schaetzung_GB"] = {"bedarf": bedarf, "frei": frei}
        erg_pfad.write_text(json.dumps(erg, indent=2, ensure_ascii=False))
        print("NETZ", json.dumps(erg["netz"]), erg["ram_schaetzung_GB"], flush=True)
        if a.nur_netz:
            return
        if bedarf > 0.85 * frei:
            raise SystemExit(f"ABBRUCH: Elmer braucht ~{bedarf:.1f} GB, frei {frei:.1f} GB -> h_* groesser")
        t0 = time.time()
        with open(ordner / "solve.log", "w") as f:
            subprocess.run(["ElmerSolver", "case.sif"], cwd=ordner, stdout=f, stderr=subprocess.STDOUT, check=True)
        erg["t_elmer_s"] = time.time() - t0
    erg["ergebnis"] = struktur.auswerten(ordner, spulen, b, h, kz)
    erg["ergebnis"]["schale"]["bauteil"] = "Gehaeuse + Verbinder"
    erg_pfad.write_text(json.dumps(erg, indent=2, ensure_ascii=False))
    struktur.bild(ordner, n, erg["ergebnis"], titel="Gehaeuse + Verbinder")
    print("FERTIG", ordner, json.dumps({k: erg["ergebnis"][k] for k in ("wickelpakete", "schale", "kraft_summe_MN")}))


if __name__ == "__main__":
    main()
