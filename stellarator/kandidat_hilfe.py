"""kandidat_hilfe.py — gemeinsame Kleinteile fuer die Kette-B-Skripte (K7-K10, V0). KI-generiert (Claude Sonnet 5.5, 2026-11-13).
Nur neue Funktionen; keine Aenderung an bestehenden Werkzeugen."""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

PROJEKT = Path(__file__).resolve().parents[1]
KAND = PROJEKT / "sim" / "kandidat"


def kandidat_datei() -> Path:
    """Variantenlauf (Opus-Auftrag 2026-11-15): Umgebungsvariable FUSION_KANDIDAT_DATEI ersetzt sim/kandidat/kandidat.json (Standard unveraendert)."""
    e = os.environ.get("FUSION_KANDIDAT_DATEI")
    return (Path(e) if Path(e).is_absolute() else PROJEKT / e) if e else KAND / "kandidat.json"


def aus_wurzel() -> Path | None:
    """Variantenlauf: FUSION_K_AUS = Ordner, in den K5/K8/K10 schreiben statt nach sim/kandidat/ (Standard: None = unveraendert)."""
    e = os.environ.get("FUSION_K_AUS")
    return (Path(e) if Path(e).is_absolute() else PROJEKT / e) if e else None


def kandidat() -> dict:
    return json.loads(kandidat_datei().read_text())


def pfad(s: str) -> Path:
    """'~/...' aufloesen, sonst relativ zum Projekt."""
    p = Path(s).expanduser()
    return p if p.is_absolute() else PROJEKT / p


def eingabe_oder_abbruch(rel: str, schluessel: list[str], von: str, test: bool, platzhalter: dict | None = None) -> dict:
    """Liest sim/kandidat/<rel> (JSON). Fehlt sie oder fehlen Schluessel: klare Meldung, Rueckgabewert 2.
    Im Test (--test) werden stattdessen die Platzhalterwerte benutzt (und als solche gemeldet)."""
    p = KAND / rel
    if test and platzhalter is not None:
        print(f"[TEST] Platzhalterwerte statt {rel}: {platzhalter}", flush=True)
        return dict(platzhalter)
    if not p.exists():
        print(f"ABBRUCH: Eingabe fehlt: {p.relative_to(PROJEKT)} (kommt aus {von}). Erst {von} rechnen.", file=sys.stderr)
        sys.exit(2)
    d = json.loads(p.read_text())
    fehlt = [k for k in schluessel if k not in d]
    if fehlt:
        print(f"ABBRUCH: {rel} enthaelt nicht {fehlt} (erwartet von {von}).", file=sys.stderr)
        sys.exit(2)
    return d


def ergebnis_halt_pruefen(rel: str, von: str) -> None:
    """ERGEBNIS.md eines Vorgaengers muss da sein und darf nicht mit HALT beginnen."""
    p = KAND / rel
    if not p.exists():
        print(f"ABBRUCH: {rel} fehlt ({von} nicht fertig).", file=sys.stderr); sys.exit(2)
    erste = p.read_text(encoding="utf-8").lstrip().splitlines()[:1]
    if erste and erste[0].startswith("HALT"):
        print(f"ABBRUCH: {rel} meldet {erste[0]}", file=sys.stderr); sys.exit(3)


def gpu_frei(grenze_mib: int = 3000) -> bool:
    try:
        o = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True)
        return int(o.split()[0]) < grenze_mib
    except Exception:
        return False


def gpu_warten(max_min: float = 240, grenze_mib: int = 3000) -> None:
    t0 = time.time()
    while not gpu_frei(grenze_mib):
        if time.time() - t0 > max_min * 60:
            print("ABBRUCH: GPU blieb belegt (nvidia-smi).", file=sys.stderr); sys.exit(4)
        print("GPU belegt, warte 30 s", flush=True); time.sleep(30)


def jetzt() -> str:
    return subprocess.check_output(["date", "+%F %T"], text=True).strip()
