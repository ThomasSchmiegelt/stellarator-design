"""kreis_kraft.py — Kräfte eines K3-Spulensatzes mit kraft_analyse (Annahmen a = 1,80 m, B0 = 6,5 T).

  .venv-opt/bin/python -m stellarator.kreis_kraft <fall> [<fall> ...]     # sim/kette_k3/stage2/<fall>
Ergebnis sim/kette_k3/stage2/satz_<fall>/kraefte.json.
"""
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

from stellarator import kraft_analyse as ka

ROOT = Path(__file__).resolve().parents[1]
S2 = Path(os.environ.get("K3_AUS", ROOT / "sim" / "kette_k3" / "stage2"))
A_M = 1.80


def lauf(fall):
    o = S2 / f"satz_{fall}"
    shutil.copy(S2 / f"biot_savart_{fall}.json", o / "biot_savart.json")
    a_u = json.loads((o / "pruefung_satz.json").read_text())["a"]
    ka.L = A_M / a_u
    ka.WOUT = Path(os.environ.get("K3_WOUT", ROOT / "sim" / "kette_k3" / "stage2" / "satz_d085_n10_lr" / "frei" / "wout" / "k_n48000.nc"))
    k = ka.kennzahlen(ka.analyse(o))
    k.update(a_m=A_M, L=ka.L, B0_T=ka.B0, R0_m=ka.L * 1.0)
    (o / "kraefte.json").write_text(json.dumps(k, indent=1, ensure_ascii=False))
    print(fall, "L", round(ka.L, 2))
    for z in k["basisspulen"]:
        print({q: z[q] for q in ("spule", "I_MA", "wp_m", "laenge_m", "f_max_MN_m", "quer_anteil", "T_max_MN", "F_integral_MN")}, "Netto", round(float(np.linalg.norm(z["F_netto_MN"]))))


if __name__ == "__main__":
    for f in sys.argv[1:]:
        lauf(f)
