"""surrogat_waechter.py — Ueberwacht den autonomen Surrogat-Lauf und bindet PI (lokales LLM) als Aufsicht ein.

    setsid nohup .venv/bin/python -m stellarator.surrogat_waechter --anlage beide --stunden 4 \
        > sim/surrogat/waechter.out 2>&1 &

Aufgaben:
  1. startet stellarator.surrogat lauf (falls nicht laeuft) und startet ihn neu, wenn er abstuerzt,
     solange Zeitbudget uebrig ist (der Lauf ist fortsetzbar, fertige Proben bleiben).
  2. alle --intervall Minuten: PI (pi -p, Ollama lokal, keine Cloud-Tokens) bekommt Status, Log-Ende und
     Fehler. PI bewertet und darf NUR die Steuerdateien sim/surrogat/<anlage>/steuerung.json aendern
     (pause, stopp, timeout_min, loeser, ueberspringen, notiz). Code und Proben bleiben unangetastet.
  3. Protokoll: sim/surrogat/pi_waechter.log (Antworten von PI), sim/surrogat/waechter.log.
Ohne PI (--ohne_pi) laeuft nur Punkt 1.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path

from .lauf import PROJEKT

WURZEL = PROJEKT / "sim" / "surrogat"

AUFTRAG = """Du bist die Aufsicht ueber einen autonomen FEM-Rechenlauf (Elmer, Surrogatmodell fuer Stellarator-Spulen).
Chef ist Claude, du ueberwachst und korrigierst nur ueber Steuerdateien. Arbeitsverzeichnis: {projekt}
Pruefe den Stand unten. Erlaubte Eingriffe (nur wenn noetig, sonst nichts aendern):
  Datei {wurzel}/<anlage>/steuerung.json (JSON) mit Feldern
    "pause": true/false, "stopp": true/false, "timeout_min": Zahl, "loeser": "iterativ"|"mumps",
    "ueberspringen": [Probennummern], "notiz": "kurze Begruendung"
Regeln: KEINE anderen Dateien aendern, keinen Code aendern, nichts loeschen, keine Prozesse beenden.
Typische Faelle: dieselbe Probe scheitert wiederholt -> ueberspringen; Laufzeiten nahe timeout -> timeout_min
erhoehen; Loeser konvergiert nicht -> loeser "mumps"; Arbeitsspeicher knapp -> pause.
Antworte am Ende mit 3-6 Zeilen: ZUSTAND (ok/warnung/fehler), BEOBACHTUNG, EINGRIFF (oder 'keiner').

=== Stand {zeit} ===
{stand}
"""


def lies(p: Path, n: int = 0) -> str:
    if not p.exists():
        return "(fehlt)"
    t = p.read_text(errors="replace")
    return "\n".join(t.splitlines()[-n:]) if n else t


def stand(anlagen: list[str]) -> str:
    teile = []
    for a in anlagen:
        o = WURZEL / a
        n = len(list((o / "proben").glob("*.npz"))) if (o / "proben").exists() else 0
        teile.append(f"--- Anlage {a}: {n} fertige Proben\nstatus.json: {lies(o / 'status.json')}\n"
                     f"steuerung.json: {lies(o / 'steuerung.json')}\nlauf.log (Ende):\n{lies(o / 'lauf.log', 25)}\n"
                     f"fehler.log (Ende):\n{lies(o / 'fehler.log', 15)}")
    mi = {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}
    import shutil
    teile.append(f"Arbeitsspeicher verfuegbar: {mi['MemAvailable']:.1f} GB (W7-X-Probe braucht ~11 GB), "
                 f"Platte frei: {shutil.disk_usage(PROJEKT).free / 1e9:.1f} GB (Lauf stoppt unter 5 GB)")
    return "\n".join(teile)


def frage_pi(text: str, timeout: int = 900) -> str:
    """Auftrag als Datei uebergeben (lange Texte mit '/' haelt pi sonst fuer einen Pfad)."""
    auftrag = WURZEL / "pi_auftrag.md"
    auftrag.write_text(text)
    r = subprocess.run(["pi", "-p", f"Lies die Datei {auftrag} und folge genau dem Auftrag darin."],
                       cwd=PROJEKT, capture_output=True, text=True, timeout=timeout)
    antwort = r.stdout.split("geladen ===")[-1].strip()
    return antwort if antwort else f"(keine Antwort, rc {r.returncode}: {r.stderr[-300:]})"


def lauf_laeuft() -> bool:
    return subprocess.run(["pgrep", "-f", "[s]tellarator.surrogat lauf"], capture_output=True).returncode == 0


def log(text: str, datei: str = "waechter.log") -> None:
    z = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {text}"
    print(z, flush=True)
    with open(WURZEL / datei, "a") as f:
        f.write(z + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--anlage", default="beide")
    ap.add_argument("--stunden", type=float, default=4.0)
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--intervall", type=float, default=20.0, help="Minuten zwischen PI-Pruefungen")
    ap.add_argument("--ohne_pi", action="store_true")
    a = ap.parse_args(argv)
    WURZEL.mkdir(parents=True, exist_ok=True)
    anlagen = ["w7x", "qa_1gw"] if a.anlage == "beide" else [a.anlage]
    ende = time.time() + 3600 * a.stunden
    lauf, naechste_pruefung, neustarts = None, time.time() + 300, 0
    log(f"Waechter START, Budget {a.stunden} h, Anlagen {anlagen}, PI {'aus' if a.ohne_pi else 'an'}")
    while True:
        st = [json.loads(lies(WURZEL / x / "steuerung.json")) for x in anlagen if (WURZEL / x / "steuerung.json").exists()]
        pause = bool(st) and all(x.get("pause") for x in st)
        if pause:                                   # Pause: Budget mitschieben, PI ruht
            time.sleep(30); ende += 30; naechste_pruefung += 30
            continue
        rest_h = (ende - time.time()) / 3600
        if lauf is not None and lauf.poll() is not None:
            log(f"Lauf beendet mit Code {lauf.returncode}")
        if not lauf_laeuft():                       # auch einen Lauf eines frueheren Waechters erkennen
            fertig = all(json.loads(lies(WURZEL / x / "status.json")).get("zustand") == "fertig"
                         for x in anlagen if (WURZEL / x / "status.json").exists())
            if lauf is not None or fertig:
                if (lauf is not None and lauf.returncode == 0) or fertig or rest_h < 0.25 or neustarts >= 5:
                    break
                neustarts += 1
            log(f"starte Lauf (Rest {rest_h:.2f} h, Neustart {neustarts})")
            lauf = subprocess.Popen([sys.executable, "-m", "stellarator.surrogat", "lauf", "--anlage", a.anlage,
                                     "--stunden", f"{rest_h:.3f}", "--n", str(a.n)], cwd=PROJEKT,
                                    stdout=open(WURZEL / "lauf.out", "a"), stderr=subprocess.STDOUT)
        if not a.ohne_pi and time.time() >= naechste_pruefung:
            naechste_pruefung = time.time() + 60 * a.intervall
            text = AUFTRAG.format(projekt=PROJEKT, wurzel=WURZEL, zeit=time.strftime("%Y-%m-%d %H:%M"), stand=stand(anlagen))
            try:
                log("PI:\n" + frage_pi(text) + "\n", "pi_waechter.log")
            except Exception as e:
                log(f"PI nicht erreichbar: {e!r}", "pi_waechter.log")
        time.sleep(30)
    log("Waechter ENDE")
    if not a.ohne_pi:
        text = AUFTRAG.format(projekt=PROJEKT, wurzel=WURZEL, zeit=time.strftime("%Y-%m-%d %H:%M"), stand=stand(anlagen))
        text += ("\nDer Lauf ist beendet. Aendere nichts mehr. Schreibe stattdessen eine Zusammenfassung fuer Claude "
                 f"(10-15 Zeilen: Proben je Anlage, Fehler, Auffaelligkeiten, Validierung aus {WURZEL}/<anlage>/validierung.json).")
        try:
            (WURZEL / "pi_zusammenfassung.md").write_text(frage_pi(text) + "\n")
        except Exception as e:
            log(f"PI-Zusammenfassung fehlgeschlagen: {e!r}")


if __name__ == "__main__":
    main()
