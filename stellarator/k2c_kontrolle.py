"""k2c_kontrolle.py -- K2c Schritt 2: K2 P1+P3 in der vom Modell gefundenen Groesse/Stromdichte, Leiterfeld K2 gegen Modell.
KI-generiert (Claude Sonnet 5.5, 2026-11-13). Aufruf: k2c_kontrolle.py <ID8> <j_A_mm2>"""
import json, subprocess, sys
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / "stellarator"))
from k2b_schleife import IDS
i8, jA = sys.argv[1], sys.argv[2]
k = "dk8" if i8 == "DK8s6qwo" else i8.lower()
o = P / "sim/kette_k2c" / i8 / f"kontrolle_j{jA}"; o.mkdir(parents=True, exist_ok=True)
mod = json.loads((P / "sim/kette_k2c" / i8 / "spulenmodell.json").read_text())
st = json.loads((P / "sim/kette_k2c" / i8 / "stufe0_modell.json").read_text())["auslegung_modell"]["HTS"][jA]
b = json.loads((P / st_b).read_text()) if (st_b := json.loads((P / "sim/kette_k2c" / i8 / "stufe0_modell.json").read_text())["bilanz"]) else None
j = float(jA) * 1e6
wp = float(np.sqrt(st["I_mittel_MA"] * 1e6 / j))
h = b["auslegung"].setdefault("HTS", {})
h.update({"machbar": True, "R0_m": st["R0_m"], "B0_T": st["B0_T"], "I_spule_MA": st["I_mittel_MA"], "wickelpaket_m": wp,
          "magnetenergie_GJ": st["energie_GJ"], "a_m": st["R0_m"] / b["form"]["aspekt"], "B_leiter_T": st["leiterfeld_T"]})
b["annahmen"]["k_B"]["HTS"] = st["leiterfeld_T"] / st["B0_T"]
bf = o / "bilanz_kontrolle.json"; bf.write_text(json.dumps(b, indent=1, default=float))
r = subprocess.run([str(P / ".venv-opt/bin/python"), "stellarator/k2_volle_groesse.py", "--id", IDS[i8], "--bilanz", bf.relative_to(P).as_posix(),
                    "--aus", (o / "k2").relative_to(P).as_posix(), "--nur", "P1", "P3"], cwd=P, capture_output=True, text=True)
p1 = json.loads((o / "k2/P1.json").read_text()); p3 = json.loads((o / "k2/P3.json").read_text())
B0a = p1["B0_achse_mittel_absB_T"]; f = p1["f_I_faktor_neu"]
# Modell mit gleichem Wickelpaket wie K2 (einheitlich sqrt(I_mittel/j)) und mit je-Spule-Paket
Im = st["I_mittel_MA"] * 1e6; Ii = np.array(mod["r_i"]) * Im; ai = np.array(mod["a_i"]); B0 = st["B0_T"]
BL_gleich = float(np.max(ai * B0 + 2e-7 * Ii / (wp / 2)))
BL_je = float(np.max(ai * B0 + 2e-7 * Ii / (np.sqrt(Ii / j) / 2)))
K2 = p3["leiterfeld"]["B_leiter_bei_B0_bilanz_T"]
erg = {"form": i8, "j_A_mm2": float(jA), "R0_m": st["R0_m"], "B0_bilanz_T": B0, "B0_achse_K2_T": B0a, "abweichung_B0_prozent": p1["abweichung_B0_prozent"],
       "wp_K2_m": wp, "leiterfeld_K2_T": K2, "leiterfeld_K2_spule": p3["leiterfeld"]["spule_max"],
       "leiterfeld_modell_je_spule_paket_T": BL_je, "leiterfeld_modell_gleiches_paket_wie_K2_T": BL_gleich,
       "abw_modell_je_spule_gegen_K2_prozent": (BL_je / K2 - 1) * 100, "abw_modell_gleiches_paket_gegen_K2_prozent": (BL_gleich / K2 - 1) * 100,
       "energie_K2_GJ": p3["energie_bei_B0_bilanz_GJ"], "energie_modell_GJ": st["energie_GJ"], "abw_energie_prozent": (st["energie_GJ"] / p3["energie_bei_B0_bilanz_GJ"] - 1) * 100,
       "I_max_K2_MA": p1["strom_fuer_B0_bilanz_mittel_MA"] * p1["strom_je_spule_MA"]["max"] / p1["strom_je_spule_MA"]["mittel_vorgabe"], "I_max_modell_MA": st["I_max_MA"],
       "f_max_K2_MN_m": p3["kraft_bei_B0_bilanz_f_max_MN_m"], "ampere_kontrolle": p1["diagnose_achse"]["int_B_dl_Tm"] / p1["diagnose_achse"]["mu0_mal_Summe_I_Tm"],
       "K2_Ausgabe_Ende": (r.stdout + r.stderr)[-200:]}
(o / "kontrolle.json").write_text(json.dumps(erg, indent=1)); print(json.dumps(erg, indent=1))
