"""wissensnetz.py -- Netzplan als Rückgrat für Wissensmanagement und Projektdokumentation (Stellarator).

KI-generiert (Claude Sonnet im Auftrag von Opus, 2026-11-12), nach der Vorlage des Batterieprojekts, für Fusion angepasst.
Knoten: Phasen H.. (erledigt, rekonstruiert, aus historie.json) und Vorgänge der Zukunft (plan_fusion.A);
verknüpft mit Anforderungen (docs/projekt/01_lastenheft.md), Befunden (BEFUNDE.md B-nnn), Dateien und Entscheidungen.

    python3 pm/plan/wissensnetz.py
Ausgabe: pm/plan/wissensnetz.json, docs/projekt/03_anforderungsverfolgung.md, pm/plan/zeitleiste.png,
         danach wissensnetz.html (wissensnetz_ansicht.py) und Obsidian-Notizen wissen/ (wissensnetz_obsidian.py).
Status: Phase = "erledigt (rekonstruiert)"; Zukunft = "fertig" nur wenn alle Ausgabedateien (aus) existieren, sonst "offen".
Prüfung: jede REQ hat mindestens eine Phase oder einen Vorgang; jeder Befund B-001..B-076 hängt an genau einer Phase.
"""
import json, re, subprocess, sys
from datetime import date, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent; ROOT = HIER.parents[1]
sys.path.insert(0, str(HIER)); import plan_fusion as PF
import zeitleiste as ZL

BEFUND_MAX = 76
# Ausgabedateien der Zukunft (nur wo festgelegt; sonst bleibt der Vorgang "offen")
AUS = {"D1": ["pm/plan/historie.json", "pm/plan/zeitleiste.png", "pm/plan/wissensnetz.py", "docs/projekt/01_lastenheft.md"]}


def expand(s):
    """'B-015…B-019, B-024' -> [15,16,17,18,19,24]"""
    out = []
    for teil in re.split(r"\s*,\s*", s.strip()):
        if not teil: continue
        m = re.fullmatch(r"B-(\d+)\s*…\s*B-(\d+)", teil)
        if m: out += list(range(int(m.group(1)), int(m.group(2)) + 1))
        else:
            m = re.fullmatch(r"B-(\d+)", teil); assert m, f"unlesbar: {teil}"; out.append(int(m.group(1)))
    return out


def kompakt(ids):
    n = sorted(set(ids)); out = []; i = 0
    while i < len(n):
        j = i
        while j + 1 < len(n) and n[j + 1] == n[j] + 1: j += 1
        out.append(f"B-{n[i]:03d}" if j == i else f"B-{n[i]:03d}…B-{n[j]:03d}"); i = j + 1
    return ", ".join(out)


def lese_req():
    t = (ROOT / "docs/projekt/01_lastenheft.md").read_text(); out = {}
    for m in re.finditer(r"^\| (REQ-[FD]\d+) \| ([^|]+)\|(.*)$", t, re.M):
        zellen = [c.strip() for c in m.group(3).split("|") if c.strip() or True]
        out[m.group(1)] = dict(text=m.group(2).strip(), status=zellen[-2].strip() if len(zellen) >= 2 else "")
    return out


def lese_befunde():
    t = (ROOT / "BEFUNDE.md").read_text(); out = {}
    for m in re.finditer(r"^#{2,3} (B-(\d{3}))[ |]+(.*)$", t, re.M): out[int(m.group(2))] = m.group(3).strip()
    return out


def req_aus_notiz(notiz):
    out = []
    for m in re.finditer(r"REQ-([FD]\d{2})((?:,\s*[FD]\d{2})*)", notiz):
        out += ["REQ-" + m.group(1)] + ["REQ-" + x for x in re.findall(r"[FD]\d{2}", m.group(2))]
    return out


def main():
    subprocess.run([sys.executable, str(HIER / "zeitleiste.py")], check=True, capture_output=True)
    hist = json.loads((HIER / "historie.json").read_text())
    req = lese_req(); bef = lese_befunde(); fehler = []
    es, ef, ls, lf, nach, ende = PF.cpm(PF.A); s0 = date.fromisoformat(PF.START)
    # --- Phasen
    phasen = []
    for p in hist["phasen"]:
        ids = expand(p["befunde"]) if p["befunde"] else []
        dat = [dict(pfad=d, vorhanden=(ROOT / d).exists()) for d in p["dateien"]]
        for d in dat:
            if not d["vorhanden"]: fehler.append(f"{p['id']}: Datei fehlt {d['pfad']}")
        for r in p["req"]:
            if r not in req: fehler.append(f"{p['id']}: unbekannte Anforderung {r}")
        phasen.append(dict(art="Phase", id=p["id"], name=p["name"], von=p["von"], bis=p["bis"], status="erledigt (rekonstruiert)", wer=p["wer"],
                           req=p["req"], befunde=[f"B-{i:03d}" for i in ids], commits=p["commits"], dateien=dat, ergebnis=p["ergebnis"], beleg=p["beleg"]))
    # --- Befunde je Phase
    zuordnung = {}
    for p in phasen:
        for b in p["befunde"]: zuordnung.setdefault(int(b[2:]), []).append(p["id"])
    fehlend = [f"B-{i:03d}" for i in range(1, BEFUND_MAX + 1) if i not in zuordnung]
    doppelt = {f"B-{i:03d}": v for i, v in zuordnung.items() if len(v) > 1}
    unbekannt = [f"B-{i:03d}" for i in zuordnung if i not in bef]
    # --- Vorgänge der Zukunft
    vorgaenge = []
    for i, n, dur, vor, res, notiz in PF.A:
        aus = AUS.get(i, []); da = [(ROOT / a).exists() for a in aus]
        status = "fertig" if aus and all(da) else "offen"
        a, b = ZL.zukunft_daten()[i]
        vorgaenge.append(dict(art="Vorgang", id=i, name=n, dauer=dur, vorgaenger=vor, nachfolger=nach[i], wer=res, notiz=notiz, es=es[i], ef=ef[i],
                              puffer=round(lf[i] - ef[i], 2), kritisch=abs(lf[i] - ef[i]) < 1e-9, von=a.isoformat(), bis=b.isoformat(), status=status,
                              req=req_aus_notiz(notiz), aus=[dict(pfad=x, vorhanden=y) for x, y in zip(aus, da)]))
    # --- Anforderungen
    anf = []
    for r, v in req.items():
        ph = [p["id"] for p in phasen if r in p["req"]]; vg = [x["id"] for x in vorgaenge if r in x["req"]]
        bs = sorted({int(b[2:]) for p in phasen if p["id"] in ph for b in p["befunde"]})
        if not ph and not vg: fehler.append(f"{r}: weder Phase noch Vorgang")
        anf.append(dict(id=r, text=v["text"], status_lastenheft=v["status"], phasen=ph, vorgaenge=vg, befunde=[f"B-{i:03d}" for i in bs]))
    # --- Entscheidungen
    ent = [dict(id=f"E{k + 1:02d}", **e) for k, e in enumerate(hist.get("entscheidungen", []))]
    # --- Dateien (Gegenrichtung)
    dateien = {}
    for p in phasen:
        for d in p["dateien"]: dateien.setdefault(d["pfad"], dict(pfad=d["pfad"], vorhanden=d["vorhanden"], phasen=[]))["phasen"].append(p["id"])
    pruef = dict(phasen=len(phasen), vorgaenge=len(vorgaenge), befunde_gesamt=BEFUND_MAX, befunde_zugeordnet=len(zuordnung), befunde_fehlend=fehlend,
                 befunde_doppelt=doppelt, befunde_ohne_titel=unbekannt, req_gesamt=len(req), req_ohne_knoten=[a["id"] for a in anf if not a["phasen"] and not a["vorgaenge"]],
                 fehler=fehler)
    netz = dict(hinweis="KI-generiert (pm/plan/wissensnetz.py). Phasen rekonstruiert (aus BEFUNDE, ERINNERUNGEN, Git), Dauern der Zukunft sind Annahmen.",
                projektdauer_AT=ende, start_zukunft=PF.START, phasen=phasen, vorgaenge=vorgaenge, anforderungen=anf,
                befunde=[dict(id=f"B-{i:03d}", titel=bef.get(i, "?"), phase=(zuordnung.get(i) or [None])[0]) for i in range(1, BEFUND_MAX + 1)],
                entscheidungen=ent, dateien=sorted(dateien.values(), key=lambda x: x["pfad"]), pruefung=pruef)
    (HIER / "wissensnetz.json").write_text(json.dumps(netz, ensure_ascii=False, indent=1))
    # --- Anforderungsverfolgung
    bt = {b["id"]: b for b in netz["befunde"]}
    z = ["| Dok.-Nr. | FUS-DOC-03 | Version | 0.1 | Status | Entwurf |\n|---|---|---|---|---|---|\n"
         "| Titel | Anforderungsverfolgung (erzeugt aus dem Netzplan, rekonstruiert) | Ersteller | Claude Sonnet (KI) im Auftrag von Claude Opus, pm/plan/wissensnetz.py | Prüfer | – (Mensch offen) |\n\n"
         "> **KI-generiert, nicht von Hand bearbeiten:** `python3 pm/plan/wissensnetz.py` schreibt diese Datei neu. Die Zuordnung der Phasen ist eine "
         "Rekonstruktion (pm/plan/historie.json), Entwurf, nicht vom Autor freigegeben. „Status Lastenheft“ ist die Angabe aus docs/projekt/01_lastenheft.md, "
         "keine Prüfung.\n\n"
         "| REQ | Anforderung | Phasen (rekonstruiert) | Vorgänge (Zukunft) | Befunde | Status Lastenheft | Vorgänge fertig/offen |\n|---|---|---|---|---|---|---|\n"]
    V = {v["id"]: v for v in vorgaenge}
    for a in anf:
        vs = [V[i]["status"] for i in a["vorgaenge"]]; vf = f"{vs.count('fertig')}/{vs.count('offen')}" if vs else "–"
        bs = kompakt([int(b[2:]) for b in a["befunde"]]) if a["befunde"] else "–"
        z.append(f"| {a['id']} | {a['text'][:80].replace('|', '/')} | {', '.join(a['phasen']) or '–'} | {', '.join(a['vorgaenge']) or '–'} | {bs} | {a['status_lastenheft'].replace('|', '/') or '–'} | {vf} |\n")
    z.append(f"\n---\n*KI-generiert. Erzeugt aus pm/plan/wissensnetz.json. Befunde: {len(zuordnung)} von {BEFUND_MAX} einer Phase zugeordnet, fehlend: {len(fehlend)}. Prüffehler: {len(fehler)}.*\n")
    (ROOT / "docs/projekt/03_anforderungsverfolgung.md").write_text("".join(z))
    for skript in ("wissensnetz_ansicht.py", "wissensnetz_obsidian.py"):
        r = subprocess.run([sys.executable, str(HIER / skript)], capture_output=True, text=True)
        print(r.stdout.strip()); 
        if r.returncode: print("FEHLER", skript, r.stderr[-800:])
    print(f"{len(phasen)} Phasen, {len(vorgaenge)} Vorgänge (fertig {sum(v['status'] == 'fertig' for v in vorgaenge)}, offen {sum(v['status'] == 'offen' for v in vorgaenge)}); "
          f"Anforderungen {len(req)}, ohne Knoten: {pruef['req_ohne_knoten'] or 'keine'}; Befunde zugeordnet {len(zuordnung)}/{BEFUND_MAX}, fehlend: {fehlend or 'keine'}, "
          f"doppelt: {doppelt or 'keine'}; Prüffehler: {fehler or 'keine'}")


if __name__ == "__main__":
    main()
