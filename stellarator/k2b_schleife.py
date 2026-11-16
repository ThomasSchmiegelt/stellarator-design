"""k2b_schleife.py -- K2b: Stufe 0 korrigiert mit den echten Spulen (Schleife Stufe 0 -> K2 P1+P3 -> f_I, k_B -> Stufe 0).

KI-generiert (Claude Sonnet 5.5, 2026-11-13). Auftrag sim/kette_dk8/AUFTRAG_K2b.md, Erwartung sim/kette_dk8/ERWARTUNG_K2b.md (nicht aendern).

Je Form und Runde n:
  1. invers/stufe0_bilanz.py mit f_I, k_B (Start 1,0 / 2,0 = B-078; DK8s6qwo: 1,164 / 3,31 aus K2)  -> R0, B0, I, Wickelpaket
  2. stellarator/k2_volle_groesse.py (P1 + P3) in dieser Groesse -> B0 Achse, Leiterfeld der staerksten Spule, Energie
  3. f_I neu = f_I * B0_bilanz / B0_Achse;  k_B neu = B_leiter_max / B0_Achse
  Abbruch, wenn |R0_n - R0_(n-1)| < 0,2 m (ab Runde 2) oder nach 6 Runden. Jede Runde: sim/kette_k2b/<id8>[/j25]/runde_<n>.json (vorhandene werden uebersprungen).
Variante j 25 A/mm2 (Annahme): Start mit f_I/k_B der j40-Kette.
'Nicht machbar' bis R0 30 m: Runde wird so vermerkt; Diagnose mit Raster bis 45 m (--R0_max 45) als eigene, gekennzeichnete Spur.

Aufruf (Scope):  sim/kette_k2b/lauf.sh
"""
import json
import subprocess
import sys
import time
from pathlib import Path

P = Path(__file__).resolve().parents[1]
PY = str(P / ".venv-opt/bin/python")
IDS = {  # id8 -> voll-ID (Top 10, sim/kette_top10/lauf.sh)
    "DK8s6qwo": "DK8s6qwoUCsuCu2yoa7qLvx", "DfXvrph2": "DfXvrph2UUfBKosQAFp5Neg", "DZrUR4dA": "DZrUR4dAT8H3EQvsN4XPRnL",
    "DBszvkku": "DBszvkkuakgEnxjeyETHVvx", "D799qKH8": "D799qKH8hvx6XZZv5p4FLJi", "DmC2qkhi": "DmC2qkhi8xDvETNDhUWhxW8",
    "DGozX5fj": "DGozX5fjoFJFphR569er9t5", "DHTy2o9U": "DHTy2o9U3AYN8UeD63VPmnH", "DGMtrTL2": "DGMtrTL2XJAnFGr7cmWNsfQ",
    "DDWJg4NB": "DDWJg4NBD6KwNGM8KNLJrys"}
J25 = ["DK8s6qwo", "DZrUR4dA", "DGozX5fj"]
MAXR, TOL = 6, 0.2


def jetzt():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def kurz(i8):
    return "dk8" if i8 == "DK8s6qwo" else i8.lower()


def vorher(i8):
    n = "dk8_1GW" if i8 == "DK8s6qwo" else f"{i8.lower()}_1GW"
    b = json.loads((P / "sim/invers" / n / "bilanz.json").read_text())
    return b["auslegung"]["HTS"], str(Path("sim/invers") / n / "bilanz.json")


def lauf(cmd):
    r = subprocess.run(cmd, cwd=P, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-800:], r.stderr[-800:], flush=True)
    return r


def runde(i8, tag, n, f_I, k_B, ext):
    """Eine Runde; liefert das Ergebnis (dict)."""
    t0 = time.time(); start = jetzt()
    k = kurz(i8); o = P / "sim/kette_k2b" / i8 / tag
    name = f"{i8.lower()}_1GW{'' if tag == 'j40' else '_' + tag}_k{n}{'_ext' if ext else ''}"
    j = "25e6" if tag == "j25" else "40e6"
    cmd = [PY, "invers/stufe0_bilanz.py", "--name", name, "--form", f"sim/kette_{k}/stufe1", "--spulen", f"sim/kette_{k}/stufe2/spulen.json",
           "--f_I", f"{f_I}", "--k_B", f"HTS={k_B},Nb3Sn={k_B}", "--j_HTS", j]
    if ext:
        cmd += ["--R0_max", "45"]
    lauf(cmd)
    bf = P / "sim/invers" / name / "bilanz.json"
    h = json.loads(bf.read_text())["auslegung"]["HTS"]
    erg = {"form": i8, "variante": tag, "runde": n, "start": start, "f_I_eingabe": f_I, "k_B_eingabe": k_B, "j_HTS_A_m2": float(j),
           "raster_R0_max_m": 45 if ext else 30, "stufe0_bilanz": f"sim/invers/{name}/bilanz.json"}
    if not h.get("machbar"):
        erg["machbar"] = False
        erg["ende"] = jetzt(); erg["laufzeit_s"] = round(time.time() - t0, 1)
        return erg
    erg.update({"machbar": True, "R0_m": h["R0_m"], "B0_T": h["B0_T"], "I_spule_MA": h["I_spule_MA"], "wickelpaket_m": h["wickelpaket_m"],
                "energie_stufe0_GJ": h["magnetenergie_GJ"], "begrenzt_durch": h["begrenzt_durch"], "auslastung": h["auslastung"],
                "spalt_schaetzung_m": h["spalt_schaetzung_m"]})
    aus = o / f"k2_runde_{n}"
    r = lauf([PY, "stellarator/k2_volle_groesse.py", "--id", IDS[i8], "--bilanz", bf.relative_to(P).as_posix(), "--aus", aus.relative_to(P).as_posix(),
              "--nur", "P1", "P3"])
    p1f, p3f = aus / "P1.json", aus / "P3.json"
    if not (p1f.exists() and p3f.exists()):
        erg["k2_fehler"] = (r.stdout + r.stderr)[-400:]
        erg["ende"] = jetzt(); erg["laufzeit_s"] = round(time.time() - t0, 1)
        return erg
    p1, p3 = json.loads(p1f.read_text()), json.loads(p3f.read_text())
    fI = p1["f_I_faktor_neu"]; lf = p3["leiterfeld"]
    erg.update({"k2_ordner": aus.relative_to(P).as_posix(), "B0_achse_K2_T": p1["B0_achse_mittel_absB_T"], "abweichung_B0_prozent": p1["abweichung_B0_prozent"],
                "ampere_kontrolle": p1["diagnose_achse"]["int_B_dl_Tm"] / p1["diagnose_achse"]["mu0_mal_Summe_I_Tm"],
                "B_leiter_max_K2_T": lf["B_leiter_max_T"], "spule_staerkste": lf["spule_max"], "k_B_echt": lf["k_B_echt"],
                "f_I_neu": f_I * fI, "k_B_neu": lf["k_B_echt"],
                "I_max_spule_bei_B0_bilanz_MA": p1["strom_fuer_B0_bilanz_mittel_MA"] * p1["strom_je_spule_MA"]["max"] / p1["strom_je_spule_MA"]["mittel_vorgabe"],
                "I_mittel_bei_B0_bilanz_MA": p1["strom_fuer_B0_bilanz_mittel_MA"],
                "B_leiter_bei_B0_bilanz_T": lf["B_leiter_bei_B0_bilanz_T"],
                "energie_K2_bei_B0_bilanz_GJ": p3["energie_bei_B0_bilanz_GJ"], "f_max_bei_B0_bilanz_MN_m": p3["kraft_bei_B0_bilanz_f_max_MN_m"],
                "feldfehler_Bn_mittel": p1["feldfehler"]["Bn_mittel"]})
    erg["ende"] = jetzt(); erg["laufzeit_s"] = round(time.time() - t0, 1)
    erg["hinweis"] = "KI-generiert (Claude Sonnet 5.5), Entwurf, stellarator/k2b_schleife.py"
    return erg


def kette(i8, tag, f_I, k_B):
    o = P / "sim/kette_k2b" / i8 / tag; o.mkdir(parents=True, exist_ok=True)
    prev = None; ext = False; res = None
    for n in range(1, MAXR + 1):
        rf = o / f"runde_{n}.json"
        if rf.exists():
            res = json.loads(rf.read_text()); print(f"{i8} {tag} Runde {n}: vorhanden", flush=True)
        else:
            print(f"{i8} {tag} Runde {n}: Start {jetzt()} f_I {f_I:.4f} k_B {k_B:.3f}", flush=True)
            res = runde(i8, tag, n, f_I, k_B, ext)
            if not res["machbar"] and not ext:           # Diagnose: Raster bis 45 m, ersetzt das Ergebnis nicht, wird gekennzeichnet
                res["nicht_machbar_bis_30_m"] = True
                (o / f"runde_{n}_ohne_ext.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
                ext = True
                res = runde(i8, tag, n, f_I, k_B, True); res["nicht_machbar_bis_30_m"] = True
            rf.write_text(json.dumps(res, indent=1, ensure_ascii=False))
        ext = ext or res.get("raster_R0_max_m") == 45
        if not res.get("machbar") or "f_I_neu" not in res:
            res["abbruch"] = "nicht machbar oder K2-Fehler"; rf.write_text(json.dumps(res, indent=1, ensure_ascii=False)); return res
        d = None if prev is None else res["R0_m"] - prev
        res["dR0_zur_vorrunde_m"] = d
        if d is not None and abs(d) < TOL:
            res["konvergiert"] = True; rf.write_text(json.dumps(res, indent=1, ensure_ascii=False)); return res
        rf.write_text(json.dumps(res, indent=1, ensure_ascii=False))
        prev = res["R0_m"]; f_I, k_B = res["f_I_neu"], res["k_B_neu"]
    res["konvergiert"] = False
    (o / f"runde_{MAXR}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


def main():
    ids = sys.argv[1:] or list(IDS)
    start_vals = {}
    for i8 in ids:
        f0, k0 = (1.164, 3.31) if i8 == "DK8s6qwo" else (1.0, 2.0)
        r = kette(i8, "j40", f0, k0); start_vals[i8] = r
        print(f"{i8} j40 fertig {jetzt()}: R0 {r.get('R0_m')} konvergiert {r.get('konvergiert')}", flush=True)
    for i8 in [x for x in J25 if x in ids]:
        r = start_vals[i8]
        f1, k1 = r.get("f_I_neu", 1.0), r.get("k_B_neu", 2.0)
        r2 = kette(i8, "j25", f1, k1)
        print(f"{i8} j25 fertig {jetzt()}: R0 {r2.get('R0_m')} konvergiert {r2.get('konvergiert')}", flush=True)


if __name__ == "__main__":
    main()
