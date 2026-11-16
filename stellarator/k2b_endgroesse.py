"""k2b_endgroesse.py -- K2b Schritt 5: K2 komplett (P1-P5) fuer DK8s6qwo in der Endgroesse (letzte Runde der j40-Kette).  KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
import json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
o = P / "sim/kette_k2b/DK8s6qwo/j40"
runden = sorted(o.glob("runde_[0-9].json"))
r = json.loads(runden[-1].read_text()) if runden else {}
if not r.get("machbar") or "k2_ordner" not in r:
    sys.exit("DK8s6qwo: keine machbare Endgroesse, K2 nicht gerechnet")
if r.get("raster_R0_max_m") == 45:
    print("Hinweis: Endgroesse stammt aus der Diagnose mit Raster bis 45 m (nicht machbar bis 30 m)")
bil = r["stufe0_bilanz"]
cmd = [str(P / ".venv-opt/bin/python"), "stellarator/k2_volle_groesse.py", "--id", "DK8s6qwoUCsuCu2yoa7qLvx", "--bilanz", bil,
       "--aus", "sim/kette_dk8/k2_end", "--baustein", "video/bausteine/K2"]
sys.exit(subprocess.run(cmd, cwd=P).returncode)
