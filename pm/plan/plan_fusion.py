"""plan_fusion.py -- Netzplan Stellarator: Vergangenheit (rekonstruiert) und Zukunft (DK8s6qwo durch die Kette, Präsentationsvideo).

KI-generiert (Claude Opus, 2026-11-12). Dauern der Zukunft in Arbeitstagen sind ANNAHMEN (Schätzung Opus).
Vergangenheit: pm/plan/historie.json (Phasen H.., aus BEFUNDE, Git und ERINNERUNGEN rekonstruiert), wenn vorhanden.

    python3 pm/plan/plan_fusion.py
Ausgabe: pm/plan/plan_fusion.json (Planer-Format AI_Framework), plan_fusion.csv, kritischer_pfad.txt
"""
import csv, json, time
from pathlib import Path

HIER = Path(__file__).resolve().parent
START = "2026-11-13"
RES = {"Mensch": "human", "Opus": "software", "Sonnet": "software", "Haiku": "software", "PI": "software", "Maschine": "hardware"}

# Zukunft: id, Name, Dauer [AT], Vorgänger, Ressourcen, Notiz.  Jede Rechnung braucht vorher ERWARTUNG.md (REQ-D02).
A = [
    ("D1", "Dokumentation nachholen: Lastenheft, Netzplan mit Vergangenheit, Wissensnetz, Obsidian", 0.5, [], ["Opus", "Sonnet"], "REQ-D08, läuft 2026-11-12"),
    ("D2", "Vortragsseite: Abschnitt KI im Projektmanagement (Stellarator)", 0.5, ["D1"], ["Opus", "Sonnet"], "Termin Mo 16.11."),
    ("K0", "Kandidat festlegen: DK8s6qwo (B-076), Herkunft und Ausgangsdaten sammeln", 0.25, ["D1"], ["Opus"], "Datensatzform unverändert"),
    ("K1", "Stufe 0 für DK8s6qwo: Größe auf 1 GW netto (R0, B0, Supraleiter), Gleichgewicht VMEC++ in voller Größe", 1, ["K0"], ["Opus", "Maschine"], "REQ-F01, Szene 2"),
    ("K2", "Spulen in voller Größe: Feld, Feldlinien, Poincaré, Kräfte, Bauregeln", 1, ["K1"], ["Sonnet", "Maschine"], "REQ-F04, F05, Szene 1"),
    ("K3", "Alphateilchen im Spulenfeld: Verlust, Wandtreffer", 1, ["K2"], ["Sonnet", "Maschine"], "REQ-F09, Szene 1"),
    ("K4", "Turbulenz (GX) in voller Größe einordnen", 0.5, ["K1"], ["Opus", "Maschine"], "REQ-F11, Szene 2; GPU nicht zugleich mit PI"),
    ("K5", "Plasma-Wand-Abstand klären: Platz für Wand, Blanket, Abschirmung gegen Spulenabstand", 1, ["K2"], ["Opus", "PI"], "REQ-F08, Torfrage für die Absprungbasis"),
    ("K6", "Wärmebilanz und Wandlast für DK8s6qwo", 1, ["K1", "K5"], ["Opus", "Maschine"], "REQ-F10, Szene 3"),
    ("K7", "Kühlung: Gefäß/Erstwand an die neue Form anschließen (Gyroid-Segment, FluidX3D), Temperaturfeld", 3, ["K6"], ["Sonnet", "Maschine"], "REQ-F10, Szene 3; randflaeche bisher fest auf QA-Form"),
    ("K8", "Tragwerk: Gehäuse, Verbinder, Elmer-FEM; Spannung p99 heißeste Spule, Dehnung, Auslenkung", 3, ["K2", "K5"], ["Sonnet", "Opus", "Maschine"], "REQ-F06, F07, Szene 4"),
    ("K9", "Was fehlt noch? Recherche Bauteilliste (Divertor, Kryostat, Zugänge, Vakuum, Montage), grobe Maße", 1, ["K5"], ["PI", "Opus"], "Szene 5"),
    ("K10", "Gesamtanlage: alle Schichten als Geometrie zusammenführen (CAD/Voxel), Kollisionsprüfung", 2, ["K7", "K8", "K9"], ["Sonnet", "Maschine"], "Szene 6"),
    ("K11", "Absprungbasis prüfen: alle Grenzen zugleich? Anforderungsverfolgung, Befund", 0.5, ["K3", "K4", "K10"], ["Opus"], "REQ-F13"),
    ("V1", "Storyboard Präsentationsvideo festlegen (FUS-DOC-14), mit Autor abstimmen", 0.5, ["K0"], ["Opus", "Mensch"], "REQ-D09"),
    ("V2", "Szenen rendern (PyVista/ParaView → Blender)", 3, ["V1", "K11"], ["Sonnet", "Maschine"], "Einzelbilder erst nach Freigabe löschen"),
    ("V3", "Schnitt, Begleittext DE/EN aus Ergebnisdateien", 1, ["V2"], ["Sonnet", "Opus"], "nur Name im Bild"),
    ("B1", "Berichtskapitel DE/EN, README, Prozessdoku", 2, ["K11"], ["Sonnet", "Opus"], "REQ-D10"),
    ("B2", "Freigabe und Veröffentlichung durch Autor", 0.5, ["V3", "B1"], ["Mensch"], "nur Mensch"),
]


def cpm(a):
    d = {t[0]: t for t in a}; es, ef = {}, {}
    for i, n, dur, vor, *_ in a:
        es[i] = max((ef[v] for v in vor), default=0); ef[i] = es[i] + dur
    ende = max(ef.values()); nach = {i: [t[0] for t in a if i in t[3]] for i in d}
    lf, ls = {}, {}
    for i, n, dur, *_ in reversed(a):
        lf[i] = min((ls[s] for s in nach[i]), default=ende); ls[i] = lf[i] - dur
    return es, ef, ls, lf, nach, ende


def main():
    hist = json.loads((HIER / "historie.json").read_text()) if (HIER / "historie.json").exists() else {"phasen": []}
    ids = [t[0] for t in A]
    for t in A:
        assert all(v in ids[:ids.index(t[0])] for v in t[3]), f"Vorgänger fehlt/Reihenfolge: {t[0]}"
    es, ef, ls, lf, nach, ende = cpm(A)
    tasks = [{"id": h["id"], "name": h["name"], "duration": 0, "predecessors": [], "successors": [],
              "resources": ", ".join(h.get("wer", [])), "resource_list": [{"kind": RES.get(x, "software"), "name": x, "qty": 1, "rate": 0} for x in h.get("wer", [])],
              "notes": f"ERLEDIGT {h['von']}–{h['bis']} (rekonstruiert); Befunde {h.get('befunde', '')}", "is_start": False, "is_end": False}
             for h in hist["phasen"]]
    tasks += [{"id": i, "name": n, "duration": dur, "predecessors": vor, "successors": nach[i],
               "resources": ", ".join(r), "resource_list": [{"kind": RES[x], "name": x, "qty": 1, "rate": 0} for x in r],
               "notes": notiz, "is_start": not vor, "is_end": not nach[i]} for i, n, dur, vor, r, notiz in A]
    plan = {"id": "fusion0001", "name": "Stellarator (KI-generiert)", "created_at": time.time(), "updated_at": time.time(), "tasks": tasks,
            "description": "KI-generiert (Claude Opus, 2026-11-12). Vergangenheit 22.10.–12.11.2026 rekonstruiert (Phasen H..), Zukunft: "
            "DK8s6qwo durch die Kette und Präsentationsvideo. Dauern der Zukunft sind Annahmen.",
            "system_prompt": "", "resource_catalog": [{"kind": k, "name": n, "rate": 0} for n, k in RES.items()],
            "resource_mode": "catalog", "start_date": START, "workdays": True, "project_id": ""}
    (HIER / "plan_fusion.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    with open(HIER / "plan_fusion.csv", "w", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["ID", "Name", "Dauer_AT", "Vorgaenger", "Ressourcen", "ES", "EF", "Puffer", "Notiz"])
        for h in hist["phasen"]:
            w.writerow([h["id"], h["name"], "", "", ",".join(h.get("wer", [])), h["von"], h["bis"], "", "erledigt (rekonstruiert)"])
        for i, n, dur, vor, r, notiz in A:
            w.writerow([i, n, dur, ",".join(vor), ",".join(r), es[i], ef[i], round(lf[i] - ef[i], 2), notiz])
    krit = [i for i in ids if abs(lf[i] - ef[i]) < 1e-9]
    txt = (f"KI-generiert. Vergangenheit: {len(hist['phasen'])} Phasen (rekonstruiert). Zukunft: {ende:g} Arbeitstage (Annahme), Start {START}.\n"
           f"Kritischer Pfad: {' -> '.join(krit)}\n")
    (HIER / "kritischer_pfad.txt").write_text(txt); print(txt)


if __name__ == "__main__":
    main()
