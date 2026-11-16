"""k2d_groesse.py -- K2d: Groesse mit dem kreuzungsfreien Spulensatz, kalibriert an K2 (Leiterfeld).  KI-generiert (Claude Sonnet 5.5, 2026-11-13).
Auftrag sim/kette_dgoz/AUFTRAG_K2d.md, Erwartung sim/kette_dgoz/ERWARTUNG_K2d.md (nicht aendern).
Aufruf: k2d_groesse.py <Satz-Ordner rel.> <j_A_mm2> <Ausgabeordner rel.> [max_runden]
Runde 0: K2 P1+P3 in Startgroesse (K2c-Ergebnis) -> Spulenmodell (r_i, a_i, W_ref, d_ss) -> Stufe 0 (--spulenmodell, R0_max 45) -> R0_1.
Runde n>=1: K2 P1+P3 bei R0_n; c = B_leiter_K2 / B_leiter_Modell (gleiche Groesse, gleiches Wickelpaket) -> Stufe 0 mit --k_kal c -> R0_(n+1).
Ende bei |R0_(n+1) - R0_n| < 0,3 m (hoechstens 4 Kalibrierrunden). Vorhandene Rundenergebnisse werden uebersprungen."""
import json, subprocess, sys, time
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
PY = str(P / ".venv-opt/bin/python")
ID = "DGozX5fjoFJFphR569er9t5"
satz, jA, aus = sys.argv[1], sys.argv[2], Path(sys.argv[3]); maxr = int(sys.argv[4]) if len(sys.argv) > 4 else 4; TAG = __import__("os").environ.get("K2D_TAG") or Path(satz).parent.name   # K2e: K2D_TAG trennt die Stufe-0-Ordner mehrerer Varianten (ohne Variable wie bisher)
aus = P / aus; aus.mkdir(parents=True, exist_ok=True)
K2C = json.loads((P / "sim/kette_k2c/DGozX5fj/stufe0_modell.json").read_text())
BASIS = json.loads((P / K2C["bilanz"]).read_text())
start = K2C["auslegung_modell"]["HTS"][jA]
now = lambda: time.strftime("%F %T")
j = float(jA) * 1e6


def k2(R0, B0, I_MA, W_GJ, tag, kB):
    """K2 P1+P3 im Ordner <aus>/<tag>; Bilanzdatei wie k2c_kontrolle."""
    o = aus / tag
    if not (o / "k2/P3.json").exists():
        o.mkdir(parents=True, exist_ok=True)
        b = json.loads(json.dumps(BASIS)); wp = float(np.sqrt(I_MA * 1e6 / j))
        b["auslegung"]["HTS"].update({"machbar": True, "R0_m": R0, "B0_T": B0, "I_spule_MA": I_MA, "wickelpaket_m": wp, "magnetenergie_GJ": W_GJ,
                                      "a_m": R0 / b["form"]["aspekt"], "B_leiter_T": 20.0})   # 20 T = Grenze HTS (Annahme Stufe 0), nur fuer die Grenzlinie im Bild
        b["annahmen"]["k_B"]["HTS"] = kB / B0
        bf = o / "bilanz.json"; bf.write_text(json.dumps(b, indent=1, default=float))
        r = subprocess.run([PY, "stellarator/k2_volle_groesse.py", "--id", ID, "--satz", satz, "--bilanz", bf.relative_to(P).as_posix(),
                            "--aus", (o / "k2").relative_to(P).as_posix(), "--nur", "P1", "P3"], cwd=P, capture_output=True, text=True)
        (o / "k2.log").write_text(r.stdout + r.stderr)
    return json.loads((o / "k2/P1.json").read_text()), json.loads((o / "k2/P3.json").read_text())


def stufe0(name, mod, c):
    r = subprocess.run([PY, "invers/stufe0_bilanz.py", "--name", name, "--form", "sim/kette_dgozx5fj/stufe1", "--spulen", SP0,
                        "--spulenmodell", mod, "--R0_max", "45", "--k_kal", f"{c}"], cwd=P, capture_output=True, text=True)
    d = json.loads((P / "sim/invers" / name / "bilanz.json").read_text())["auslegung_modell"]["HTS"][jA]
    return d, f"sim/invers/{name}/bilanz.json"


runden = []
R0, B0, I_MA, W, kB = start["R0_m"], start["B0_T"], start["I_mittel_MA"], start["energie_GJ"], start["leiterfeld_T"]
t0 = now()
p1, p3 = k2(R0, B0, I_MA, W, "start", kB)
B0a = p1["B0_achse_mittel_absB_T"]; Bm = p3["leiterfeld"]["B0_achse_T"]; Im = p3["strom_mittel_MA"]
sp = p3["spulen_basis"]
s2 = json.loads(((P / satz).parent / (Path(satz).name[5:] + ".json")).read_text())
R0u = json.loads((P / "sim/kette_dgozx5fj/stufe2/spulen.json").read_text())["R0_m"]   # wie K2c (Form DGozX5fj, Datensatzmassstab)
st2 = aus.parent / "stufe2"; st2.mkdir(exist_ok=True)           # Eingabe fuer Stufe 0 (Abstaende, Anzahl), wie stellarator/dk8_stufe0_eingabe.py
(st2 / "spulen.json").write_text(json.dumps({"hinweis": "KI-generiert; nur Abstaende und Anzahl fuer Stufe 0", "R0_m": R0u,
    "abstand_sp_min_m": s2["ringe"]["ring0"]["abstand_plasma_a"] * s2["a_u"], "spulen": [None] * int(s2["n_spulen"])}, indent=1))
(st2 / "stufe2.json").write_text(json.dumps({"abstand_ss_min_m": s2["spule_spule_min_a"] * s2["a_u"]}, indent=1))
SP0 = (st2 / "spulen.json").relative_to(P).as_posix()
mod = {"form": "DGozX5fj", "satz": satz, "quelle_K2": (aus / "start/k2").relative_to(P).as_posix(), "R0_ref_m": p1["R0_ziel_m"], "B0_ref_T": Bm, "I_mittel_ref_MA": Im,
       "N_ref": 4 * len(sp), "r_i": [x["I_MA"] / Im for x in sp], "a_i": [x["B_fremd_max_T"] / Bm for x in sp], "W_ref_GJ": p3["magnetenergie_GJ"],
       "d_ss_ref_m": s2["spule_spule_min_a"] * s2["a_u"] / R0u * p1["R0_ziel_m"],
       "d_ss_quelle": "k3-Falldatei spule_spule_min_a * a_u / R0_m (K2c, 0,9678) * R0_ref", "hinweis": "KI-generiert, Entwurf; wie k2c_modell.py"}
(aus / "spulenmodell.json").write_text(json.dumps(mod, indent=1)); modp = (aus / "spulenmodell.json").relative_to(P).as_posix()
c = 1.0
for n in range(maxr + 1):
    ts = now()
    if n > 0:
        p1, p3 = k2(R0, B0, I_MA, W, f"runde{n}", kB)
        Kk = p3["leiterfeld"]["B_leiter_bei_B0_bilanz_T"]
        wp = float(np.sqrt(I_MA * 1e6 / j)); Imean = I_MA * 1e6; Ii = np.array(mod["r_i"]) * Imean; ai = np.array(mod["a_i"])
        BLm = float(np.max(ai * B0 + 2e-7 * Ii / (np.sqrt(Ii / j) / 2)))      # Modell ohne c, je Spule eigenes Paket (wie Stufe 0)
        c = Kk / BLm
    else:
        Kk = None; BLm = None
    d, bil = stufe0(f"dgozx5fj_k2d_{TAG}_j{jA}_r{n}", modp, c)
    rec = {"runde": n, "j_A_mm2": float(jA), "R0_in_m": R0, "B0_in_T": B0, "c_k_kal": c, "B_leiter_K2_T": Kk, "B_leiter_Modell_ohne_c_T": BLm,
           "B0_achse_K2_T": p1["B0_achse_mittel_absB_T"], "f_I_neu": p1["f_I_faktor_neu"], "energie_K2_bei_B0_GJ": p3["energie_bei_B0_bilanz_GJ"],
           "f_max_K2_MN_m": p3["kraft_bei_B0_bilanz_f_max_MN_m"], "stufe0": d, "stufe0_bilanz": bil, "start": ts, "ende": now()}
    runden.append(rec)
    print(json.dumps({k: rec[k] for k in ("runde", "R0_in_m", "c_k_kal", "B_leiter_K2_T", "B_leiter_Modell_ohne_c_T")}), "->", d.get("R0_m"), d.get("machbar"), flush=True)
    (aus / "runden.json").write_text(json.dumps({"start": t0, "runden": runden}, indent=1, default=float))
    if not d.get("machbar"):
        break
    if abs(d["R0_m"] - R0) < 0.3 and n > 0:
        break
    R0, B0, I_MA, W, kB = d["R0_m"], d["B0_T"], d["I_mittel_MA"], d["energie_GJ"], d["leiterfeld_T"]
print("ENDE", now())
