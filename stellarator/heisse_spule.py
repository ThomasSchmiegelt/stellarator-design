"""heisse_spule.py — neuer Spannungsmassstab (F-225, B-043) aus vorhandenem struktur.vtu nachrechnen, ohne Elmer.

  .venv/bin/python -m stellarator.heisse_spule qi_proxima_dpr 2 8 9     # -> sim/qi_feld/heisse_spule.json (ergänzt)

Massstab: p99 der heißesten Spule ohne 0,5-m-Randzone um Verbinder und Lager (submodell.p99_ohne_rand_je_spule).
Das Netz wird in einem Zwischenordner neu gebaut (struktur_netz schreibt Plan-Dateien); Punktordner und ergebnis.json
bleiben unberührt. Prüfung: Knotenzahl und Lage müssen zu struktur.vtu passen.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

from . import hexmodell as hm, kopplung as kp
from .submodell import p99_ohne_rand_je_spule

ROOT = Path(__file__).resolve().parents[1]
ZIEL = ROOT / "sim" / "qi_feld" / "heisse_spule.json"


def nachrechnen(studie: str, nr: int) -> dict:
    import pyvista as pv
    po = kp.ordner(studie) / "punkte" / f"{nr:04d}"
    kp.plasma_laden(kp.ordner(studie))
    p = json.loads((po / "param.json").read_text()); geo = json.loads((po / "geometrie.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for f in ("spulen.json", "plasma_rand.npy", "wand_je_spule.json"):
            if (po / f).exists():
                shutil.copy(po / f, t / f)
        netz, *_ = kp.struktur_netz(p, t, geo)
    g = pv.read(po / "struktur.vtu")
    if g.n_points != len(netz.X) or np.abs(np.asarray(g.points) - netz.X).max() > 1e-4:
        raise RuntimeError(f"{studie}/{nr}: Netz passt nicht zu struktur.vtu")
    vm = np.asarray(g.cell_data["vonmises_MPa"]); V = hm.elementvolumen(netz.X, netz.hexa)
    je = p99_ohne_rand_je_spule(netz, vm, V, int(p.get("verbinder_halb", kp.FEST["verbinder_halb"])))
    k = int(np.argmax(je["p99_ohne_rand"])); v = je["p99_ohne_rand"][k]
    e = json.loads((po / "ergebnis.json").read_text())
    return {"studie": studie, "nr": nr, "heiss_spule": k, "heiss_p99_ohne_rand_MPa": v,
            "stahl_p99_alle_MPa": e["struktur"]["stahl"]["vm_p99_MPa"], "stufe": kp.stahl_stufe(v),
            "abstand_500_MPa": 500.0 - v, "abstand_800_MPa": 800.0 - v,
            "je_spule_p99_MPa": je["p99"], "je_spule_p99_ohne_rand_MPa": je["p99_ohne_rand"]}


def main():
    studie, nummern = sys.argv[1], [int(x) for x in sys.argv[2:]]
    alt = json.loads(ZIEL.read_text()) if ZIEL.exists() else {}
    for nr in nummern:
        r = nachrechnen(studie, nr); alt[f"{studie}/{nr:04d}"] = r
        print(f"{studie}/{nr:04d}: heißeste Spule {r['heiss_spule']} {r['heiss_p99_ohne_rand_MPa']:.0f} MPa "
              f"({r['stufe']}), alle Spulen {r['stahl_p99_alle_MPa']:.0f} MPa", flush=True)
    ZIEL.write_text(json.dumps(alt, indent=1))


if __name__ == "__main__":
    main()
