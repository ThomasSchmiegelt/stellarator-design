"""wissensnetz_obsidian.py -- erzeugt aus pm/plan/wissensnetz.json Obsidian-Notizen unter wissen/ (Marker wissen/.erzeugt, Einstieg wissen/Start.md).

KI-generiert (Claude Sonnet im Auftrag von Opus). Vault-Wurzel ist das Projektverzeichnis; erzeugt wird nur wissen/.
    python3 pm/plan/wissensnetz_obsidian.py
Notizarten: Phase, Vorgang, Anforderung, Befund, Entscheidung, Datei (Farben je Art über Frontmatter typ und Tags).
"""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; W = ROOT / "wissen"
KOPF = "> KI-generiert, erzeugt aus pm/plan/wissensnetz.json – nicht von Hand bearbeiten. Phasen sind rekonstruiert."
D = json.loads((ROOT / "pm/plan/wissensnetz.json").read_text())
PH = {p["id"]: p for p in D["phasen"]}; VG = {v["id"]: v for v in D["vorgaenge"]}
notes = {}


def safe(s): return re.sub(r"[^\w.\-]+", "_", s).strip("_")
def kl(i): return f"[[wissen/{'Phase' if i in PH else 'Vorgang'}/{i}|{i}]]"
def fm(typ, **kw):
    z = ["---", f"typ: {typ}"]
    for k, v in kw.items():
        z.append(f"{k}: [" + ", ".join(json.dumps(x, ensure_ascii=False) for x in v) + "]" if isinstance(v, list) else f"{k}: {json.dumps(v, ensure_ascii=False)}")
    return "\n".join(z + ["---", ""])
def lst(a): return "\n".join(a) or "- –"
def docl(p): return f"[[{p[:-3]}]]" if p.endswith(".md") and (ROOT / p).exists() else f"`{p}`"


for p in D["phasen"]:
    t = fm("phase", status=p["status"], von=p["von"], bis=p["bis"], tags=["phase", "rekonstruiert"]) + f"# {p['id']} – {p['name']}\n\n{KOPF}\n\n"
    t += f"- Zeitraum: {p['von']} bis {p['bis']}\n- Wer: {', '.join(p['wer'])}\n- Commits: {', '.join(p['commits'])}\n\n## Ergebnis (rekonstruiert)\n{p['ergebnis']}\n\n## Beleg\n{p['beleg']}\n\n"
    t += "## Anforderungen\n" + lst([f"- [[wissen/Anforderung/{r}|{r}]]" for r in p["req"]]) + "\n\n"
    t += "## Befunde\n" + lst([f"- [[wissen/Befund/{b}|{b}]]" for b in p["befunde"]]) + "\n\n"
    t += "## Entscheidungen\n" + lst([f"- [[wissen/Entscheidung/{e['id']}|{e['id']}]] – {e['text']}" for e in D["entscheidungen"] if e["phase"] == p["id"]]) + "\n\n"
    t += "## Dateien\n" + lst([f"- [[wissen/Datei/{safe(d['pfad'])}|{d['pfad']}]]" for d in p["dateien"]]) + "\n"
    notes[f"Phase/{p['id']}"] = t
for v in D["vorgaenge"]:
    t = fm("vorgang", status=v["status"], kritisch=v["kritisch"], tags=["vorgang", "status/" + v["status"]]) + f"# {v['id']} – {v['name']}\n\n{KOPF}\n\n"
    t += f"- Status: {v['status']}; Dauer {v['dauer']} AT (Annahme); {v['von']} bis {v['bis']}; Puffer {v['puffer']}{' (kritischer Pfad)' if v['kritisch'] else ''}\n"
    t += f"- Wer: {', '.join(v['wer'])}\n- Notiz: {v['notiz']}\n- Vorgänger: {', '.join(kl(x) for x in v['vorgaenger']) or '–'}\n- Nachfolger: {', '.join(kl(x) for x in v['nachfolger']) or '–'}\n\n"
    t += "## Anforderungen\n" + lst([f"- [[wissen/Anforderung/{r}|{r}]]" for r in v["req"]]) + "\n\n## Ausgabedateien\n" + lst([f"- {'✓' if a['vorhanden'] else '✗'} {docl(a['pfad'])}" for a in v["aus"]]) + "\n"
    notes[f"Vorgang/{v['id']}"] = t
for a in D["anforderungen"]:
    notes[f"Anforderung/{a['id']}"] = (fm("anforderung", tags=["anforderung"]) + f"# {a['id']}\n\n{KOPF}\n\n{a['text']}\n\nStatus laut Lastenheft: {a['status_lastenheft']}\nLastenheft: [[docs/projekt/01_lastenheft]]\n\n"
        "## Phasen\n" + lst([f"- {kl(i)} – {PH[i]['name']}" for i in a["phasen"]]) + "\n\n## Vorgänge\n" + lst([f"- {kl(i)} – {VG[i]['name']}" for i in a["vorgaenge"]]) + "\n\n## Befunde\n" + lst([f"- [[wissen/Befund/{b}|{b}]]" for b in a["befunde"]]) + "\n")
for b in D["befunde"]:
    notes[f"Befund/{b['id']}"] = (fm("befund", tags=["befund"]) + f"# {b['id']}\n\n{KOPF}\n\n{b['titel']}\n\nQuelle: [[BEFUNDE]]\n\n## Phase\n- {kl(b['phase']) if b['phase'] else 'fehlt'}\n")
for e in D["entscheidungen"]:
    notes[f"Entscheidung/{e['id']}"] = (fm("entscheidung", datum=e["datum"], tags=["entscheidung"]) + f"# {e['id']} – {e['text']}\n\n{KOPF}\n\n- Datum: {e['datum']}\n- Beleg: {e['beleg']}\n- Phase: {kl(e['phase'])}\n")
for d in D["dateien"]:
    notes[f"Datei/{safe(d['pfad'])}"] = (fm("datei", vorhanden=d["vorhanden"], tags=["datei"]) + f"# {d['pfad']}\n\n{KOPF}\n\n- vorhanden: {'ja' if d['vorhanden'] else 'nein'}\n- Datei: {docl(d['pfad'])}\n\n## Phasen\n" + lst([f"- {kl(i)} – {PH[i]['name']}" for i in d["phasen"]]) + "\n")
P = D["pruefung"]
s = fm("start", tags=["start"]) + f"# Wissensnetz Stellarator\n\n{KOPF}\n\nPhasen (rekonstruiert): {P['phasen']}; Vorgänge (Zukunft, Dauern Annahme): {P['vorgaenge']}; Befunde zugeordnet {P['befunde_zugeordnet']}/{P['befunde_gesamt']}; Anforderungen {P['req_gesamt']}.\n\n"
s += "Weiter: [[BEFUNDE]] · [[ERINNERUNGEN]] · [[docs/projekt/01_lastenheft]] · [[docs/projekt/03_anforderungsverfolgung]] · Ansicht: `pm/plan/wissensnetz.html`, Zeitleiste: `pm/plan/zeitleiste.png`\n\n"
s += "## Phasen (erledigt, rekonstruiert)\n\n| Phase | Zeitraum | Name |\n|---|---|---|\n" + "".join(f"| [[wissen/Phase/{p['id']}\\|{p['id']}]] | {p['von']} bis {p['bis']} | {p['name']} |\n" for p in D["phasen"])
s += "\n## Vorgänge der Zukunft\n\n| Vorgang | Name | Status | Dauer AT (Annahme) |\n|---|---|---|---|\n" + "".join(f"| [[wissen/Vorgang/{v['id']}\\|{v['id']}]] | {v['name'].replace('|', '/')} | {v['status']} | {v['dauer']} |\n" for v in D["vorgaenge"])
s += "\n## Entscheidungen\n\n" + "\n".join(f"- [[wissen/Entscheidung/{e['id']}|{e['id']}]] {e['datum']}: {e['text']}" for e in D["entscheidungen"]) + "\n"
notes["Start"] = s

if W.exists():
    if not (W / ".erzeugt").exists(): raise SystemExit("wissen/ existiert ohne Markerdatei .erzeugt – abgebrochen")
    shutil.rmtree(W)
for rel, t in notes.items():
    p = W / f"{rel}.md"; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
(W / ".erzeugt").write_text("Von pm/plan/wissensnetz_obsidian.py erzeugt; Ordner wird beim Lauf geleert.\n")
fehl = []; n = 0
for p in W.rglob("*.md"):
    for m in re.finditer(r"\[\[([^\]]+)\]\]", p.read_text()):
        n += 1; z = m.group(1).replace("\\|", "|").split("|")[0].split("#")[0]
        if not (ROOT / (z + ".md")).exists(): fehl.append(f"{p.relative_to(ROOT)}: [[{z}]]")
zaehl = {}
for rel in notes: zaehl[rel.split("/")[0]] = zaehl.get(rel.split("/")[0], 0) + 1
print("Obsidian-Notizen:", zaehl, "gesamt", len(notes)); print(f"Links geprüft: {n}; fehlende Ziele: {len(fehl)}"); [print("  ", f) for f in fehl[:20]]
