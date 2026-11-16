"""k10_anlage.py — Schritt K10: Gesamtanlage als Geometrie (Schichten, Spulen, Gehaeuse, Kryostat) + Kollisionspruefung.
KI-generiert (Claude Sonnet 5.5, 2026-11-13). Erwartung: sim/kandidat/erwartung/K10.md (Opus, vor der Rechnung).

    .venv/bin/python -m stellarator.k10_anlage [--test]

Eingaben (fehlen sie: Meldung + Rueckgabewert 2/3, im --test Platzhalter, deutlich gekennzeichnet):
  sim/kandidat/K5/ergebnis.json   {"aufbau_m": {"erste_wand":x,"blanket":x,"abschirmung":x,"vakuumgefaess":x,"spalt":x,"gehaeuse":x}}  (Dicken in m, aus K5)
  sim/kandidat/K5/ERGEBNIS.md, K8/ERGEBNIS.md, K9/ERGEBNIS.md  muessen existieren und duerfen nicht mit HALT beginnen
  sim/kandidat/K8/lauf/ergebnis.json (letzte Variante -> param.json: wand_seite_m = Gehaeusewand um das Wickelpaket)
  sim/kandidat/K10/platzhalter.json  {"kryostat_abstand_m": x, "teile": [{"name","typ":"box|zylinder","mitte":[x,y,z],"mass":[..]}]}  (aus K9, von Opus)
  sim/kandidat/kandidat.json, video/bausteine/K2/spulen_40.vtk (Spulenlinien, m), Plasmarand der Form (wie k7: FUSION_RAND_*)
Ausgabe sim/kandidat/K10/lauf/: <schicht>.stl, anlage.gltf (je Schicht ein Mesh), kollision.json, anlage_{de,en}.png; ERGEBNIS.md am Ende.
Pruefungen: (1) Schichten: Abstand der Aussenflaeche zur Plasmaflaeche >= 0,98 x Summe der Dicken (sonst Selbstdurchdringung der Versatzflaeche);
(2) Gehaeuse (Wickelpaket-Halbdiagonale + Wand) gegen Aussenflaeche Vakuumgefaess + Spalt + Gehaeuse: Abstand der Spulenmitte >= Aufbau + Halbmass;
(3) Spule-Spule: Mittellinienabstand >= Summe der Halbmasse. Durchdringungen werden mit Ursache gemeldet, nichts wird verschoben.
"""
from __future__ import annotations
import argparse, base64, json, os, struct, sys, time
from pathlib import Path
import numpy as np

from .kandidat_hilfe import PROJEKT, KAND, kandidat, pfad, eingabe_oder_abbruch, ergebnis_halt_pruefen, jetzt, aus_wurzel

K10 = KAND / "K10"
SCHICHTEN = ["erste_wand", "blanket", "abschirmung", "vakuumgefaess", "spalt", "gehaeuse"]
FARBE = {"plasma": [1, .2, .8, 1], "erste_wand": [.9, .5, .1, 1], "blanket": [.3, .7, .3, 1], "abschirmung": [.5, .5, .5, 1], "vakuumgefaess": [.3, .5, .9, 1],
         "spulen": [.8, .1, .1, 1], "gehaeuse": [.6, .6, .7, 1], "kryostat": [.8, .8, .8, .3], "schild": [.5, .5, .45, .2]}
PLATZ_TEST = {"kryostat_abstand_m": 3.0, "schild_abstand_m": 2.0, "teile": [], "hinweis": "Platzhalter nur fuer --test (Annahme, nicht belegt)"}
AUFBAU_TEST = {"aufbau_m": {"erste_wand": 0.03, "blanket": 0.7, "abschirmung": 0.6, "vakuumgefaess": 0.3, "spalt": 0.2, "gehaeuse": 0.1}}


def lies_vtk_linien(p: Path) -> list[np.ndarray]:
    import pyvista as pv
    m = pv.read(p); P = np.asarray(m.points); out = []
    ln = m.lines; i = 0
    while i < len(ln):
        n = ln[i]; out.append(P[ln[i + 1:i + 1 + n]]); i += n + 1
    return out


def flaeche_aus_gitter(X: np.ndarray):
    """X (n_th, n_ph, 3) periodisch -> geschlossene PyVista-Flaeche."""
    import pyvista as pv
    Xc = np.concatenate([X, X[:, :1]], 1); Xc = np.concatenate([Xc, Xc[:1]], 0)
    g = pv.StructuredGrid(Xc[..., 0], Xc[..., 1], Xc[..., 2])
    return g.extract_surface().triangulate().clean()


def schreibe_gltf(pfad_: Path, netze: dict) -> None:
    buf = bytearray(); bv, acc, meshes, mats, nodes = [], [], [], [], []
    for i, (name, m) in enumerate(netze.items()):
        P = np.asarray(m.points, np.float32); F = np.asarray(m.faces).reshape(-1, 4)[:, 1:].astype(np.uint32)
        for arr, tgt in ((P, 34962), (F, 34963)):
            off = len(buf); buf += arr.tobytes(); buf += b"\0" * (-len(buf) % 4)
            bv.append({"buffer": 0, "byteOffset": off, "byteLength": arr.nbytes, "target": tgt})
        acc.append({"bufferView": len(bv) - 2, "componentType": 5126, "count": len(P), "type": "VEC3", "min": P.min(0).tolist(), "max": P.max(0).tolist()})
        acc.append({"bufferView": len(bv) - 1, "componentType": 5125, "count": F.size, "type": "SCALAR"})
        c = FARBE.get(name, [.7, .7, .7, 1])
        mats.append({"name": name, "pbrMetallicRoughness": {"baseColorFactor": c, "metallicFactor": 0.1}, "alphaMode": "BLEND" if c[3] < 1 else "OPAQUE", "doubleSided": True})
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": len(acc) - 2}, "indices": len(acc) - 1, "material": i}]})
        nodes.append({"name": name, "mesh": i})
    g = {"asset": {"version": "2.0", "generator": "k10_anlage.py (KI-generiert, Claude Sonnet 5.5); Einheit m, z = Torusachse"}, "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
         "nodes": nodes, "meshes": meshes, "materials": mats, "accessors": acc, "bufferViews": bv,
         "buffers": [{"byteLength": len(buf), "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(buf)).decode()}]}
    pfad_.write_text(json.dumps(g))


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--test", action="store_true")
    ap.add_argument("--k8", default=None, help="studie/punkt (z. B. k8_dgoz/0001): Wand je Spule aus dessen param.json + wand_je_spule.json (Opus-Auftrag 2026-11-15)")
    ap.add_argument("--aus", default=None, help="Ausgabeordner (statt sim/kandidat/K10/lauf); dann kein Schreiben nach K10/ERGEBNIS.md und video/bausteine")
    ap.add_argument("--k5", default=None, help="Pfad zu K5 ergebnis.json (Standard sim/kandidat/K5/ergebnis.json)")
    ap.add_argument("--wp", type=float, default=None, help="Wickelpaket-Kante [m] statt kandidat.json (nur Sensitivitaet; z. B. K8 struktur.wickelpaket_m)")
    a = ap.parse_args(argv)
    import pyvista as pv
    from scipy.spatial import cKDTree
    from .gesamtszene import normalen
    from .gyroid_gefaess import randflaeche
    t0 = time.time(); start = jetzt(); k = kandidat()
    AUS = aus_wurzel(); variante = bool(a.aus or AUS)
    o = (PROJEKT / a.aus) if a.aus else ((AUS / "K10" / "lauf") if AUS else K10 / ("test" if a.test else "lauf")); o.mkdir(parents=True, exist_ok=True)
    if not a.test:
        for rel, von in (("K5/ERGEBNIS.md", "K5"), ("K8/ERGEBNIS.md", "K8")):   # K9 optional (Opus 2026-11-13): fehlt es, entfallen die Teile ohne Abbruch
            if variante or a.k8:                                              # Variantenlauf: Vorgaenger liegen woanders, K8 aus --k8
                continue
            ergebnis_halt_pruefen(rel, von)
    if a.k5 or (AUS and (AUS / "K5" / "ergebnis.json").exists()):
        p5 = PROJEKT / (a.k5 or str((AUS / "K5" / "ergebnis.json").relative_to(PROJEKT))); aufd = json.loads(p5.read_text()); quelle5 = str(p5.relative_to(PROJEKT))
        if "aufbau_m" not in aufd:
            print(f"ABBRUCH: {p5} ohne aufbau_m", file=sys.stderr); sys.exit(2)
        auf = aufd["aufbau_m"]
    else:
        auf = eingabe_oder_abbruch("K5/ergebnis.json", ["aufbau_m"], "K5", a.test, AUFBAU_TEST)["aufbau_m"]; quelle5 = "sim/kandidat/K5/ergebnis.json"
    if isinstance(auf, list):   # Opus 2026-11-15: K5 schreibt eine Liste {name, dicke_m, ...} mit deutschen Namen
        NAMEN = {"Erste Wand": "erste_wand", "Blanket": "blanket", "Abschirmung": "abschirmung", "Vakuumgefäß": "vakuumgefaess",
                 "Spalt": "spalt", "Gehäuse": "gehaeuse"}
        auf = {NAMEN.get(z["name"], z["name"]): float(z["dicke_m"]) for z in auf}
    pl = eingabe_oder_abbruch("K10/platzhalter.json", ["kryostat_abstand_m", "teile"], "Opus (Annahmen)", a.test, PLATZ_TEST)
    miss = [s for s in SCHICHTEN if s not in auf]
    if miss:
        print(f"ABBRUCH: K5/ergebnis.json aufbau_m ohne {miss}", file=sys.stderr); sys.exit(2)
    # K8: Gehaeusewand je Spule (Opus 2026-11-15): Seitenmass quer = wp/2 + wand_seite*f_k, zum Plasma wp/2 + wand_innen*f_k
    wp = float(a.wp or k["wickelpaket_m"])
    if a.test:
        pdir = None; prm = {"wand_seite_m": 0.3, "wand_innen_m": 0.3}
    else:
        if a.k8:
            st_, nr_ = a.k8.split("/"); pdir = PROJEKT / "sim" / "kopplung" / st_ / "punkte" / f"{int(nr_):04d}"
        else:
            ek8 = (AUS / "K8" if AUS else KAND / "K8") / "lauf" / "ergebnis.json"
            e8 = json.loads(ek8.read_text())["varianten"][-1]; pdir = PROJEKT / Path(e8["quelle"]).parent
        if not (pdir / "ergebnis.json").exists():
            print(f"ABBRUCH: K8-Punkt {pdir} ohne ergebnis.json", file=sys.stderr); sys.exit(2)
        prm = json.loads((pdir / "param.json").read_text())
    wand = float(prm["wand_seite_m"]); wand_in = float(prm["wand_innen_m"])
    # Plasmarand in Metern (Form des Kandidaten unveraendert), Versatzflaechen
    P1 = json.loads(pfad(k["k2"] + "/P1.json").read_text())
    os.environ["FUSION_RAND_WOUT"] = str(pfad(k["wout"])); os.environ["FUSION_RAND_FAKTOR"] = str(P1["faktor_k"])
    n_th, n_ph = (64, 180) if a.test else (160, 720)
    X = randflaeche(n_th=n_th, n_ph=n_ph); N = normalen(X)
    netze = {"plasma": flaeche_aus_gitter(X)}; summe = 0.0; aussen = {}
    for s in SCHICHTEN[:5]:                                                  # ohne gehaeuse: das ist das Spulengehaeuse, keine Schicht am Plasma
        summe += float(auf[s]); aussen[s] = summe
        if s != "spalt":
            netze[s] = flaeche_aus_gitter(X + summe * N)
    aufbau_summe = summe                                                      # Plasma -> Aussenflaeche Vakuumgefaess + Spalt
    # Selbstdurchdringung der Versatzflaechen
    base = cKDTree(np.asarray(netze["plasma"].points)); schicht_pruef = {}
    for s in ("erste_wand", "blanket", "abschirmung", "vakuumgefaess"):
        d, _ = base.query(np.asarray(netze[s].points)); schicht_pruef[s] = {"dicke_kumuliert_m": aussen[s], "abstand_min_m": float(d.min()), "verhaeltnis": float(d.min() / aussen[s])}
    # Spulen
    vtk_rel = k.get("spulen_vtk") or (str(Path(k["k2"]).parent / "baustein_k2" / "spulen_40.vtk") if k.get("k2") else "video/bausteine/K2/spulen_40.vtk")   # ohne Eintrag: wie bei C (k2_end/../baustein_k2)
    L = lies_vtk_linien(pfad(vtk_rel))
    # Faktoren je Spule aus K8 (wand_je_spule.json = Faktoren des letzten Laufs); Seitenwand nur skaliert, wenn wand_adapt_seiten nicht 0
    fak = np.ones(len(L))
    if pdir is not None and prm.get("wand_adapt") and (pdir / "wand_je_spule.json").exists():
        fak = np.asarray(json.loads((pdir / "wand_je_spule.json").read_text())["faktoren"], float)
    if len(fak) != len(L):
        print(f"ABBRUCH: {len(fak)} Wandfaktoren, aber {len(L)} Spulen im vtk", file=sys.stderr); sys.exit(2)
    if pdir is not None and (pdir / "spulen.json").exists():                 # Reihenfolge vtk = K8-Spulen pruefen (Schwerpunkte)
        sj = json.loads((pdir / "spulen.json").read_text()); Lk = json.loads((pdir.parent.parent / "plasma.json").read_text())["L"]
        Sc = np.array([np.mean(np.asarray(q["punkte_m"]), 0) * Lk for q in sj["spulen"]]); Vc = np.array([c.mean(0) for c in L])
        zuordnung = [int(np.linalg.norm(Sc - v, axis=1).argmin()) for v in Vc]
        if zuordnung != list(range(len(L))):
            print(f"ABBRUCH: Spulenreihenfolge vtk passt nicht zu K8 spulen.json: {zuordnung}", file=sys.stderr); sys.exit(2)
    fs = fak if float(prm.get("wand_adapt_seiten", 1)) else np.ones(len(L))
    halb_q = wp / 2 + wand * fs                                               # Halbmass quer je Spule
    halb_in = wp / 2 + wand_in * fak                                          # Halbmass zum Plasma je Spule
    halb_diag = float(max(halb_q.max(), halb_in.max()))                       # nur Kryostat-Ausdehnung (grosse Seite)
    sp_netz = pv.PolyData(); geh_netz = pv.PolyData()
    for c, hq in zip(L, halb_q):
        sp_netz += pv.Spline(c, 400).tube(radius=wp / 2, n_sides=4, capping=True)
        geh_netz += pv.Spline(c, 400).tube(radius=float(hq), n_sides=4, capping=True)
    netze["spulen"] = sp_netz; netze["gehaeuse"] = geh_netz
    # (2) Spule gegen Aussenflaeche (Plasma + Aufbau inkl. Spalt)
    aussen_flaeche = flaeche_aus_gitter(X + aufbau_summe * N)
    allpts = np.vstack(L); sd = pv.PolyData(allpts).compute_implicit_distance(aussen_flaeche)["implicit_distance"]
    halb_in_pt = np.concatenate([np.full(len(c), h) for c, h in zip(L, halb_in)])
    frei = -sd - halb_in_pt - float(auf["gehaeuse"])                         # Spulenmitte ausserhalb der Aussenflaeche, abzgl. wp/2 + wand_innen*f_k + Gehaeuse (K5)
    durch = int((frei < 0).sum())
    # (3) Spule-Spule
    tr = [cKDTree(c) for c in L]; dmin = np.inf; paar = None; dpaar = None
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            d = float(tr[i].query(L[j])[0].min())
            if d - halb_q[i] - halb_q[j] < dmin:
                dmin = d - halb_q[i] - halb_q[j]; paar = (i, j); dpaar = d
    # Kryostat: Zylinder um alle Spulengehaeuse
    R_c = float(np.hypot(allpts[:, 0], allpts[:, 1]).max() + halb_diag + pl["kryostat_abstand_m"]); z_c = float(np.abs(allpts[:, 2]).max() + halb_diag + pl["kryostat_abstand_m"])
    netze["kryostat"] = pv.Cylinder(center=(0, 0, 0), direction=(0, 0, 1), radius=R_c, height=2 * z_c, resolution=96).triangulate()
    sch = float(pl.get("schild_abstand_m", 0))
    if sch > 0:                                                              # Biologischer Schild (Beton), Annahme aus platzhalter.json
        netze["schild"] = pv.Cylinder(center=(0, 0, 0), direction=(0, 0, 1), radius=R_c + sch, height=2 * (z_c + sch), resolution=96).triangulate()
    k9 = KAND / "K9" / "lauf" / "liste.md"                                   # nur Namen der Bauteile aus K9 (Text, keine Geometrie), wenn vorhanden
    k9_namen = [l.split("|")[1].strip() for l in k9.read_text(encoding="utf-8").splitlines()[2:] if l.startswith("| ")] if (k9.exists() and (KAND / "K9" / "ERGEBNIS.md").exists()) else []
    for t in pl["teile"]:
        m = pv.Box(bounds=(t["mitte"][0] - t["mass"][0] / 2, t["mitte"][0] + t["mass"][0] / 2, t["mitte"][1] - t["mass"][1] / 2, t["mitte"][1] + t["mass"][1] / 2,
                           t["mitte"][2] - t["mass"][2] / 2, t["mitte"][2] + t["mass"][2] / 2)) if t["typ"] == "box" else pv.Cylinder(center=t["mitte"], radius=t["mass"][0], height=t["mass"][1])
        netze[t["name"]] = m.triangulate()
    for n, m in netze.items():
        m.save(o / f"{n}.stl")
    schreibe_gltf(o / "anlage.gltf", netze)
    kol = {"schichten": schicht_pruef, "aufbau_plasma_bis_aussen_m": aufbau_summe, "spule_gehaeuse_frei_min_m": float(frei.min()), "durchdringungen_spule_huelle_punkte": durch,
           "spule_spule_frei_min_m": float(dmin), "spule_spule_paar": paar, "halbmass_quer_min_max_m": [float(halb_q.min()), float(halb_q.max())], "halbmass_plasma_min_max_m": [float(halb_in.min()), float(halb_in.max())], "halbmass_quer_je_spule_m": halb_q.tolist(), "halbmass_plasma_je_spule_m": halb_in.tolist(), "wandfaktoren_je_spule": fak.tolist(), "wand_seite_m": wand, "wand_innen_m": wand_in, "wand_adapt_seiten": float(prm.get("wand_adapt_seiten", 1)), "mittellinienabstand_paar_min_m": dpaar, "spule_gehaeuse_frei_min_spule": int(np.repeat(np.arange(len(L)), [len(c) for c in L])[int(frei.argmin())]), "spulen_vtk": vtk_rel, "k8_punkt": (str(pdir.relative_to(PROJEKT)) if pdir is not None else None), "wickelpaket_m": wp, "kandidat_id": k["id"], "n_spulen": len(L),
           "kryostat_R_m": R_c, "kryostat_durchmesser_m": 2 * R_c, "kryostat_hoehe_m": 2 * z_c, "spulen_R_max_m": float(np.hypot(allpts[:, 0], allpts[:, 1]).max()),
           "spulen_z_max_m": float(np.abs(allpts[:, 2]).max()), "platzhalter_teile": [t["name"] for t in pl["teile"]], "k9_bauteile_ohne_geometrie": k9_namen, "schild_abstand_m": sch, "test": a.test,
           "quelle_aufbau": quelle5 if not a.test else "Platzhalter (Test)", "quelle_wand": (str(pdir.relative_to(PROJEKT)) + "/param.json + wand_je_spule.json") if pdir is not None else "Platzhalter (Test)"}
    (o / "kollision.json").write_text(json.dumps(kol, indent=1))
    bilder(o, L, kol, X, auf, R_c, z_c, halb_diag)
    if a.test:
        (o / "TEST_OK.txt").write_text(f"{jetzt()} gelaufen ({(time.time() - t0):.0f} s, Platzhalterwerte, nichts davon ist Ergebnis)\n"); print((o / "TEST_OK.txt").read_text()); return
    halt = ""
    if durch > 0 or dmin < 0 or any(v["verhaeltnis"] < 0.98 for v in schicht_pruef.values()):
        halt = f"HALT: Durchdringung: Spule-Huelle {durch} Punkte (frei min {frei.min():.2f} m), Spule-Spule frei min {dmin:.2f} m, Schichtverhaeltnis min {min(v['verhaeltnis'] for v in schicht_pruef.values()):.3f} (Ursache: Schichtdicke oder Spulenlage; nichts verschoben)\n\n"
    md = f"""{halt}# ERGEBNIS K10 · Gesamtanlage, Kollisionspruefung
KI-generiert (Claude Sonnet 5.5, Skript stellarator/k10_anlage.py). Status Entwurf, ungeprueft. Start {start}, Ende {jetzt()}.

| Groesse | Wert | Quelle |
|---|---|---|
| Aufbau Plasma bis Aussenflaeche Vakuumgefaess + Spalt | {aufbau_summe:.2f} m | sim/kandidat/K5/ergebnis.json |
| Durchdringungen Spule/Gehaeuse gegen Aufbau (Punkte) | {durch} | {(o / 'kollision.json').relative_to(PROJEKT)} |
| kleinster freier Abstand Spule-Aufbau | {frei.min():.2f} m | dito |
| kleinster freier Abstand Spule-Spule (Gehaeuse) | {dmin:.2f} m | dito |
| Kryostat Durchmesser / Hoehe | {2 * R_c:.1f} m / {2 * z_c:.1f} m (Erwartung: 110-125 m / ca. 90 m) | dito |
| Gehaeusewand Seite / Plasmaseite (K8, Faktoren je Spule {fak.min():.2f}-{fak.max():.2f}) | {wand} m / {wand_in} m | {kol['quelle_wand']} |
| Halbmass quer min-max / zum Plasma min-max | {halb_q.min():.2f}-{halb_q.max():.2f} m / {halb_in.min():.2f}-{halb_in.max():.2f} m | dito |
| Spule-Spule engstes Paar (Mittellinienabstand) | {paar} ({dpaar:.2f} m) | dito |

Bilder: sim/kandidat/K10/lauf/anlage_de.png, anlage_en.png (Zielband beschriftet). Geometrie: STL je Schicht + anlage.gltf (Einheit m).
Platzhalter-Geometrie: Kryostat (3 m, Annahme), Biologischer Schild Beton 2 m ausserhalb Kryostat (Annahme); K9-Bauteile ohne Geometrie: {', '.join(kol['k9_bauteile_ohne_geometrie']) or 'keine (K9 fehlt)'}.

---
*KI-generiert. Status Entwurf.*
"""
    if variante:                                                              # Variantenlauf: nichts in die Standardablage schreiben
        (o / "ERGEBNIS_K10.md").write_text(md); return
    (K10 / "ERGEBNIS.md").write_text(md)
    bs = PROJEKT / "video" / "bausteine" / "K10"; bs.mkdir(parents=True, exist_ok=True)
    for f in list(o.glob("*.stl")) + [o / "anlage.gltf", o / "kollision.json", o / "anlage_de.png", o / "anlage_en.png"]:
        (bs / f.name).write_bytes(f.read_bytes())
    (bs / "baustein.md").write_text(f"""| Dok.-Nr. | FUS-VID-K10 | Version | 0.1 | Status | Entwurf |
|---|---|---|---|---|---|
| Titel | Szenenbaustein K10 · Gesamtanlage | Ersteller | Claude Sonnet 5.5 (KI) | Prüfer | – (Opus/Mensch offen) |

> **KI-generiert.** Szene 6. Im Bild nur "Thomas Schmiegelt"; Erklaerungen im Begleittext. Dateien: STL je Schicht, anlage.gltf (m, z = Achse).

Begleittext DE: Die Anlage besteht aus Plasma, Erster Wand, Blanket, Abschirmung und Vakuumgefaess ({aufbau_summe:.2f} m Aufbau), {len(L)} Spulen mit Gehaeuse und dem Kryostaten ({2 * R_c:.0f} m Durchmesser, {2 * z_c:.0f} m hoch). Quelle: sim/kandidat/K10/lauf/kollision.json.
Begleittext EN: The plant consists of plasma, first wall, blanket, shield and vacuum vessel ({aufbau_summe:.2f} m build), {len(L)} coils with casing and the cryostat ({2 * R_c:.0f} m diameter, {2 * z_c:.0f} m high). Source: sim/kandidat/K10/lauf/kollision.json.
Kamera (Annahme): Rundflug, dann Explosionsdarstellung der Schichten.

---
*KI-generiert (Claude Sonnet 5.5). Status Entwurf.*
""")


def bilder(o: Path, L, kol, X, auf, R_c, z_c, halb):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    txt = {"de": ("Draufsicht (x-y)", "Seitenansicht (x-z)", "Zielband Erwartung K7/K10: Durchmesser 110–125 m (Annahme von Opus, vor der Rechnung)",
                  "Kryostat (Platzhalter)", "KI-generiert (Claude Sonnet 5.5) · Entwurf", "Spulen", "Plasmarand", "Hoehe ca. 90 m"),
           "en": ("Top view (x-y)", "Side view (x-z)", "Target band expectation K7/K10: diameter 110–125 m (assumption by Opus, set before the run)",
                  "Cryostat (placeholder)", "AI-generated (Claude Sonnet 5.5) · draft", "Coils", "Plasma edge", "height approx. 90 m")}
    for sp_, t in txt.items():
        fig, ax = plt.subplots(1, 2, figsize=(14, 7.5))
        for i, (c, (u, v)) in enumerate([(0, (0, 1)), (1, (0, 2))]):
            for l in L:
                ax[i].plot(l[:, u], l[:, v], color="tab:red", lw=0.6, label=t[5] if l is L[0] else None)
            ax[i].plot(X[:, ::6, u].ravel(), X[:, ::6, v].ravel(), ".", ms=0.3, color="m", label=t[6])
            ax[i].set_aspect("equal"); ax[i].set_xlabel("x [m]"); ax[i].set_ylabel("y [m]" if i == 0 else "z [m]"); ax[i].set_title(t[i])
        th = np.linspace(0, 2 * np.pi, 400)
        ax[0].plot(R_c * np.cos(th), R_c * np.sin(th), "k--", lw=1, label=t[3])
        ax[1].plot([-R_c, R_c, R_c, -R_c, -R_c], [-z_c, -z_c, z_c, z_c, -z_c], "k--", lw=1)
        for Rb in (55.0, 62.5):                                              # Zielband Erwartung: Durchmesser 110-125 m -> Radius 55-62,5 m
            ax[0].plot(Rb * np.cos(th), Rb * np.sin(th), color="g", lw=0.8, ls=":")
        ax[0].plot([], [], color="g", ls=":", label=t[2].split(":")[1].strip().split("(")[0])
        ax[1].axhspan(-45, 45, color="g", alpha=0.10); ax[1].text(-R_c, -52, t[7] + " (Band ±45 m)", fontsize=8, color="g")
        ax[0].legend(fontsize=7, loc="upper left")
        fig.suptitle(f"K10 · {t[2]}\n{t[4]}", fontsize=9)
        fig.text(0.5, 0.01, f"{t[4]}", ha="center", fontsize=7)
        fig.savefig(o / f"anlage_{sp_}.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
