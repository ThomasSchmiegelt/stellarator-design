"""dk8_stufe0_eingabe.py -- Eingaben für invers/stufe0_bilanz.py aus einer Datensatzform mit eigenen Spulen (K1, DK8s6qwo).

KI-generiert (Claude Opus, 2026-11-12). Liest das VMEC++-Gleichgewicht (wout aus dem GX-Lauf) und das Ergebnis der festen
Spulenbewertung (sim/spulenfreundlich) und schreibt im Format von Stufe 1/2:
  sim/kette_dk8/stufe1/stufe1.json (+ Verweis auf wout), sim/kette_dk8/stufe2/spulen.json, stufe2.json
Abstände sind in Einheiten des kleinen Radius a gerechnet und hier mit a des Gleichgewichts in Meter umgesetzt.

    .venv-opt/bin/python stellarator/dk8_stufe0_eingabe.py [ID]
"""
import json, sys
from pathlib import Path
import numpy as np
from netCDF4 import Dataset

P = Path(__file__).resolve().parents[1]
ID = sys.argv[1] if len(sys.argv) > 1 else "DK8s6qwoUCsuCu2yoa7qLvx"
WOUT = Path.home() / "cae_projekte/gx/laeufe" / ID / f"wout_{ID}.nc"
ERG = P / "sim/spulenfreundlich/ergebnis" / f"{ID}.json"
O = P / "sim" / ("kette_dk8" if ID.startswith("DK8s6qwo") else f"kette_{ID[:8].lower()}")

with Dataset(str(WOUT)) as w:
    R0, a, V = float(w["Rmajor_p"][:]), float(w["Aminor_p"][:]), float(w["volume_p"][:])
    iota = np.abs(np.asarray(w["iotaf"][:], float)); ns = len(iota)
s = np.linspace(0, 1, ns); rho = np.sqrt(s)
e = json.loads(ERG.read_text())
(O / "stufe1").mkdir(parents=True, exist_ok=True); (O / "stufe2").mkdir(parents=True, exist_ok=True)
ziel = O / "stufe1" / WOUT.name
if not ziel.exists():
    ziel.symlink_to(WOUT)
k = {"aspekt": R0 / a, "volumen_m3": V, "R0_m": R0, "a_m": a, "iota_profil": {"rho": rho.tolist(), "iota": iota.tolist()},
     "quelle": f"Datensatzform {ID} (ConStellaration, unverändert), VMEC++-Gleichgewicht aus GX-Lauf"}
(O / "stufe1" / "stufe1.json").write_text(json.dumps({"hinweis": "KI-generiert, Eingabe für Stufe 0", "kennzahlen": k}, indent=1))
sp = {"hinweis": "KI-generiert; nur Abstände und Anzahl für Stufe 0, Kurven in sim/spulenfreundlich/faelle",
      "R0_m": R0, "abstand_sp_min_m": e["abstand_a"] * a, "spulen": [None] * int(e["n_spulen"])}
(O / "stufe2" / "spulen.json").write_text(json.dumps(sp, indent=1))
(O / "stufe2" / "stufe2.json").write_text(json.dumps({"abstand_ss_min_m": e["spule_spule_a"] * a}, indent=1))
print(f"R0 {R0:.3f} m, a {a:.4f} m, A {R0 / a:.2f}, V {V:.3f} m3, iota(2/3) {np.interp(2 / 3, rho, iota):.3f}, "
      f"d_sp/R0 {e['abstand_a'] * a / R0:.3f}, d_ss/R0 {e['spule_spule_a'] * a / R0:.3f}, Spulen {e['n_spulen']}")
