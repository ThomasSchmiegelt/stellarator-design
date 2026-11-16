"""k2c_modell.py -- K2c: spulenmodell.json je Form aus K2b-P1/P3 (letzte Runde mit K2-Daten). KI-generiert (Claude Sonnet 5.5, 2026-11-13)."""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
IDS = ["DK8s6qwo","DfXvrph2","DZrUR4dA","DBszvkku","D799qKH8","DmC2qkhi","DGozX5fj","DHTy2o9U","DGMtrTL2","DDWJg4NB"]
for i8 in IDS:
    ds = sorted((P/"sim/kette_k2b"/i8/"j40").glob("k2_runde_*"), key=lambda d: int(d.name.split("_")[-1]))
    d = ds[-1]
    p1 = json.loads((d/"P1.json").read_text()); p3 = json.loads((d/"P3.json").read_text())
    B0 = p3["leiterfeld"]["B0_achse_T"]; Im = p3["strom_mittel_MA"]
    sp = p3["spulen_basis"]
    k = "dk8" if i8 == "DK8s6qwo" else i8.lower()
    s2 = json.loads((P/f"sim/kette_{k}/stufe2/spulen.json").read_text())
    st2 = json.loads((P/f"sim/kette_{k}/stufe2/stufe2.json").read_text())
    mod = {"form": i8, "quelle_K2": d.relative_to(P).as_posix(), "R0_ref_m": p1["R0_ziel_m"], "B0_ref_T": B0, "I_mittel_ref_MA": Im,
           "N_ref": 4*len(sp) if len(sp) == 10 else None, "r_i": [x["I_MA"]/Im for x in sp], "a_i": [x["B_fremd_max_T"]/B0 for x in sp],
           "W_ref_GJ": p3["magnetenergie_GJ"], "d_ss_ref_m": st2["abstand_ss_min_m"]/s2["R0_m"]*p1["R0_ziel_m"],
           "d_ss_quelle": f"sim/kette_{k}/stufe2/stufe2.json abstand_ss_min_m {st2['abstand_ss_min_m']} / R0 {s2['R0_m']} * R0_ref",
           "hinweis": "KI-generiert, Entwurf; a_i = B_fremd_max_i / B0_Achse (Biot-Savart der anderen Spulen), unabhaengig von der Runde"}
    o = P/"sim/kette_k2c"/i8; o.mkdir(parents=True, exist_ok=True)
    (o/"spulenmodell.json").write_text(json.dumps(mod, indent=1))
    print(i8, d.name, mod["R0_ref_m"], round(B0,3), round(Im,2), mod["N_ref"], round(mod["d_ss_ref_m"],2), round(max(mod["r_i"]),3))
