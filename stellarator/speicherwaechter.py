"""speicherwaechter.py — schwere Rechnungen (PicoGK, Elmer) speichersicher starten.

Hintergrund (2026-10-25): systemd-oomd beendet bei hohem Speicherdruck die *ganze* Terminal-Sitzung
(vte-spawn-*.scope) samt Claude Code; setsid hilft nicht, der Prozess bleibt in derselben cgroup.
Deshalb:
  1. eigene systemd-Einheit (`systemd-run --user`) mit MemoryMax und MemorySwapMax -> bei Ueberlauf beendet der
     Kernel nur diese Einheit, die Sitzung bleibt;
  2. Waechter-Schleife: RSS der Einheit und Speicherdruck (/proc/pressure/memory) jede Sekunde; beendet die
     Einheit frueh (vor oomd), schreibt Grund + Spitzenwert ins Log.

    from .speicherwaechter import starte_begrenzt
    r = starte_begrenzt(["prog", "arg"], log=Path("x.log"), max_gb=10)   # -> dict(ok, grund, spitze_gb, zeit_s)

Direkt: .venv/bin/python -m stellarator.speicherwaechter --max_gb 10 --log x.log -- prog arg ...
"""
from __future__ import annotations
import argparse, os, subprocess, time, uuid
from pathlib import Path

PSI_GRENZE = 30.0          # some avg10 [%]; oomd greift bei 50 % ueber 20 s
RAM_RESERVE_GB = 4.0       # mindestens so viel muss frei bleiben


def ram_frei_gb() -> float:
    return {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}["MemAvailable"]


def psi_avg10() -> float:
    for l in open("/proc/pressure/memory"):
        if l.startswith("some"):
            return float(l.split("avg10=")[1].split()[0])
    return 0.0


def _cgroup_gb(einheit: str) -> float | None:
    r = subprocess.run(["systemctl", "--user", "show", einheit, "-p", "MemoryCurrent", "--value"],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip()) / 1e9
    except ValueError:
        return None


def starte_begrenzt(cmd: list[str], log: Path, max_gb: float, cwd: Path | None = None,
                    env: dict | None = None, timeout_s: float = 4 * 3600) -> dict:
    """cmd in eigener systemd-Einheit mit Speichergrenze ausfuehren und ueberwachen (blockiert bis Ende)."""
    if ram_frei_gb() < max_gb + RAM_RESERVE_GB:
        return {"ok": False, "grund": f"zu wenig RAM frei ({ram_frei_gb():.1f} GB < {max_gb + RAM_RESERVE_GB:.0f} GB)",
                "spitze_gb": 0.0, "zeit_s": 0.0}
    einheit = f"schwer-{uuid.uuid4().hex[:8]}"
    log = Path(log).resolve(); log.parent.mkdir(parents=True, exist_ok=True)
    setz = [f"--setenv={k}={v}" for k, v in (env or {}).items()]
    codedatei = log.with_name(log.name + f".{einheit}.code")
    import shlex
    huelle = ["/bin/sh", "-c", f"{shlex.join(cmd)}; echo $? > {shlex.quote(str(codedatei))}"]
    aufruf = ["systemd-run", "--user", "--quiet", f"--unit={einheit}", "--collect",
              "-p", f"MemoryMax={max_gb:.1f}G", "-p", "MemorySwapMax=0", "-p", f"StandardOutput=append:{log}",
              "-p", f"StandardError=append:{log}", f"--working-directory={cwd or os.getcwd()}", *setz, *huelle]
    with open(log, "a") as f:
        f.write(f"== {time.strftime('%F %T')} Einheit {einheit}, MemoryMax {max_gb:.1f} GB: {' '.join(cmd)}\n")
    subprocess.run(aufruf, check=True)
    t0, spitze, grund = time.time(), 0.0, None
    try:
        while True:
            zustand = subprocess.run(["systemctl", "--user", "is-active", einheit], capture_output=True, text=True).stdout.strip()
            if zustand not in ("active", "activating"):
                break
            gb = _cgroup_gb(einheit) or 0.0
            spitze = max(spitze, gb)
            if gb > 0.95 * max_gb:
                grund = f"Speichergrenze erreicht ({gb:.1f} GB)"
            elif ram_frei_gb() < RAM_RESERVE_GB:
                grund = f"RAM frei nur {ram_frei_gb():.1f} GB"
            elif psi_avg10() > PSI_GRENZE:
                grund = f"Speicherdruck {psi_avg10():.0f} %"
            elif time.time() - t0 > timeout_s:
                grund = "Zeitgrenze"
            if grund:
                subprocess.run(["systemctl", "--user", "kill", "-s", "KILL", einheit], capture_output=True)
                break
            time.sleep(1.0)
    except BaseException:
        subprocess.run(["systemctl", "--user", "kill", "-s", "KILL", einheit], capture_output=True)
        raise
    # Exitcode der Einheit
    time.sleep(0.5)
    code = codedatei.read_text().strip() if codedatei.exists() else None
    codedatei.unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "reset-failed", einheit], capture_output=True)
    ok = grund is None and code == "0"
    if not ok and grund is None:
        grund = f"Exitcode {code}" if code else "abgebrochen ohne Exitcode (Kernel-OOM in der Einheit?)"
    with open(log, "a") as f:
        f.write(f"== Ende: {'ok' if ok else 'ABBRUCH: ' + grund}, Spitze {spitze:.2f} GB, {time.time() - t0:.0f} s\n")
    return {"ok": ok, "grund": grund, "spitze_gb": spitze, "zeit_s": time.time() - t0}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--max_gb", type=float, required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    print(starte_begrenzt(cmd, Path(a.log), a.max_gb))


if __name__ == "__main__":
    main()
