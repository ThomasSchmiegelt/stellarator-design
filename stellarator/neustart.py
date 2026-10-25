"""neustart.py — Wiederaufnahme nach Absturz (Claude-Sitzung, Rechner, Prozesse). Mehrfach aufrufbar, aendert
nur, was fehlt.

    .venv/bin/python -m stellarator.neustart [--nur_pruefen]

Soll-Zustand: sim/surrogat/auftrag.json  {"anlagen": "beide", "ende": "YYYY-MM-DD HH:MM", "n": 150}
  (Zielende des Surrogat-Laufs; bei Pausen/Verlaengerung hier anpassen).
Schritte:
  1. verwaiste ElmerSolver unter sim/ (Elternprozess weg) beenden
  2. Surrogat: Waechter laeuft -> nichts; sonst Restzeit > 10 min -> Waechter mit Restzeit starten
     (fertige Proben bleiben); Zeit um und kein modell.pkl -> Training je Anlage
  3. Nacharbeiten, nur wenn kein Surrogat-Lauf aktiv und genug RAM: fehlende Gitterzellen (gitterzelle.py)
  4. Stand nach sim/neustart_stand.md (fuer Claude / Hermes / PI) und auf die Konsole
"""
from __future__ import annotations
import argparse, json, os, signal, subprocess, sys, time
from pathlib import Path

from .lauf import PROJEKT

SIM = PROJEKT / "sim"
SUR = SIM / "surrogat"
PY = str(PROJEKT / ".venv" / "bin" / "python")


def prozesse(muster: str) -> list[int]:
    r = subprocess.run(["pgrep", "-f", muster], capture_output=True, text=True)
    return [int(x) for x in r.stdout.split()]


def ram_frei() -> float:
    return {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}["MemAvailable"]


def starte(args: list[str], log: Path) -> int:
    p = subprocess.Popen([PY, "-m", *args], cwd=PROJEKT, stdout=open(log, "a"), stderr=subprocess.STDOUT,
                         start_new_session=True)
    return p.pid


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur_pruefen", action="store_true", help="nichts starten/beenden, nur Stand zeigen")
    a = ap.parse_args(argv)
    zeilen = [f"# Neustart-Stand {time.strftime('%Y-%m-%d %H:%M')}", ""]
    tun = lambda t: zeilen.append(("(nur pruefen) " if a.nur_pruefen else "") + t)

    # 1. verwaiste Elmer-Prozesse
    for pid in prozesse("[E]lmerSolver"):
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
            ppid = int(open(f"/proc/{pid}/stat").read().split(")")[1].split()[1])
        except OSError:
            continue
        eltern_da = ppid > 1 and os.path.exists(f"/proc/{ppid}") and "python" in open(f"/proc/{ppid}/cmdline").read()
        if cwd.startswith(str(SIM)) and not eltern_da:
            tun(f"- verwaister ElmerSolver {pid} in {cwd} -> beendet")
            if not a.nur_pruefen:
                os.kill(pid, signal.SIGTERM)

    # 2. Surrogat
    auftrag = json.loads((SUR / "auftrag.json").read_text()) if (SUR / "auftrag.json").exists() else None
    waechter = prozesse("[s]tellarator.surrogat_waechter")
    lauf = prozesse("[s]tellarator.surrogat lauf")
    anlagen = ["w7x", "qa_1gw"] if not auftrag or auftrag["anlagen"] == "beide" else [auftrag["anlagen"]]
    for x in anlagen:
        n = len(list((SUR / x / "proben").glob("*.npz"))) if (SUR / x / "proben").exists() else 0
        st = json.loads((SUR / x / "status.json").read_text()) if (SUR / x / "status.json").exists() else {}
        zeilen.append(f"- {x}: {n} Proben, Zustand {st.get('zustand', '?')}, Fehler {st.get('fehler_nr', [])}, "
                      f"Modell {'ja' if (SUR / x / 'modell.pkl').exists() else 'nein'}")
    if waechter or lauf:
        zeilen.append(f"- Surrogat laeuft (Waechter {waechter}, Lauf {lauf}) -> nichts zu tun")
    elif auftrag:
        rest_h = (time.mktime(time.strptime(auftrag["ende"], "%Y-%m-%d %H:%M")) - time.time()) / 3600
        if rest_h > 1 / 6:
            tun(f"- Surrogat-Waechter neu gestartet, Restzeit {rest_h:.2f} h (Ziel {auftrag['ende']})")
            if not a.nur_pruefen:
                starte(["stellarator.surrogat_waechter", "--anlage", auftrag["anlagen"], "--stunden", f"{rest_h:.2f}",
                        "--n", str(auftrag.get("n", 150))], SUR / "waechter.out")
                waechter = [0]
        else:
            for x in anlagen:
                if not (SUR / x / "modell.pkl").exists() and len(list((SUR / x / "proben").glob("*.npz"))) >= 12:
                    tun(f"- Zeit um, Modell fehlt -> Training {x}")
                    if not a.nur_pruefen:
                        subprocess.run([PY, "-m", "stellarator.surrogat", "trainiere", "--anlage", x], cwd=PROJEKT,
                                       stdout=open(SUR / x / "training.out", "a"), stderr=subprocess.STDOUT)
    else:
        zeilen.append("- kein sim/surrogat/auftrag.json -> Surrogat nicht automatisch gestartet")

    # 3. Nacharbeiten: Gitterzellen
    from .gitterzelle import DICKEN, WURZEL as GZ
    fehlt = [f"{art}_{d:.2f}" for art, ds in DICKEN.items() for d in ds if not (GZ / f"{art}_{d:.2f}" / "ergebnis_fem.json").exists()]
    if fehlt:
        if waechter or lauf or prozesse("[s]tellarator.surrogat lauf"):
            zeilen.append(f"- Gitterzellen offen {fehlt} -> warten, bis der Surrogat-Lauf fertig ist (RAM)")
        elif prozesse("[s]tellarator.gitterzelle"):
            zeilen.append("- Gitterzellen laufen bereits")
        elif ram_frei() < 12:
            zeilen.append(f"- Gitterzellen offen, aber nur {ram_frei():.0f} GB RAM frei -> spaeter")
        else:
            tun(f"- Gitterzellen gestartet: {fehlt}")
            if not a.nur_pruefen:
                starte(["stellarator.gitterzelle"], GZ / "lauf.log")
    else:
        zeilen.append("- Gitterzellen vollstaendig (sim/gitterzelle/kennlinie.json)")

    zeilen += ["", f"RAM frei {ram_frei():.1f} GB", "",
               "Weiter (Claude/Hermes/PI): ERINNERUNGEN.md (letzte Eintraege), Skill stellarator-surrogat,",
               "Logs sim/surrogat/*/lauf.log, sim/surrogat/pi_waechter.log, sim/gitterzelle/lauf.log."]
    text = "\n".join(zeilen) + "\n"
    (SIM / "neustart_stand.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
