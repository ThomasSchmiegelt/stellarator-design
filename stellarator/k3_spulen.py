"""k3_spulen.py — Stage 2 (Spulen zur Plasmaform) für eine beliebige Form, Ansatz stellarator/zwei_ringe.py verallgemeinert.

  .venv-opt/bin/python -m stellarator.k3_spulen lauf <fall>      # ein Lauf, Ergebnis sim/kette_k3/stage2/<fall>.json
  .venv-opt/bin/python -m stellarator.k3_spulen liste            # Fälle ausgeben
  .venv-opt/bin/python -m stellarator.k3_spulen tabelle          # Übersicht aller fertigen Läufe

Form: Standard K3 halb (sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json, nfp 2), Datensatzmaßstab (R00 ≈ 1).
Unterschiede zu zwei_ringe.py (alles andere gleich: Start an der um d versetzten Randlinie, CurveXYZFourier Ordnung 7,
SquaredFlux "normalized" auf der halben Periode, Strafen Spule–Plasma, Spule–Spule, Krümmung, mittlere quadratische
Krümmung, Länge; Gewichte verzehnfachen sich je Runde bei Verletzung; ein Strom fest, Rest frei):
  - Fläche direkt aus den Randkoeffizienten (kein wout), halbe Periode 64 × 48 Punkte (nfp 2: halbe Periode = 90°,
    doppelt so lang wie bei DjLe3eL6, darum doppelt so viele phi-Punkte), voller Rand 192 × 96 zur Auswertung.
  - Grenze mittlere quadratische Krümmung aus dem Proxima-Satz (C.json) mit (a_C / a)² auf diesen Maßstab umgerechnet.
  - Längengrenze je Ring: 1,25 × Summe der Startkurvenlängen (ANNAHME; zwei_ringe nahm 24,9 a je Spule aus DjLe3eL6,
    für die gestrecktere K3-Form wäre die Startkurve schon fast so lang).
Ergebnis je Lauf: <fall>.json (Kennzahlen), verlauf_<fall>.json (je Runde), biot_savart_<fall>.json (simsopt),
satz_<fall>/ (boundary.json + spulen.json für qi_spulen.py, stellarator/spulen_satz.py), Fertig-Marke <fall>.fertig.
Fertige Läufe werden übersprungen (Neustart setzt fort, ein angefangener Lauf beginnt neu).
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FORM = Path(os.environ.get("K3_FORM", ROOT / "sim" / "qi_flaeche" / "gegenrechnung_klein" / "form_k3_f0.5.json"))
AUS = Path(os.environ.get("K3_AUS", ROOT / "sim" / "kette_k3" / "stage2"))
ORD = 7

# Fall: (Abstand in a, Spulen je halbe Periode); Reihenfolge = Priorität
FAELLE = {"d085_n8": (0.85, 8), "d085_n10": (0.85, 10), "d100_n8": (1.00, 8), "d072_n10": (0.72, 10),
          "d100_n10": (1.00, 10), "d085_n6": (0.85, 6),
          "d085_n5": (0.85, 5)}                                           # Plan B DATJ5FC… (nfp 4) wie A085 bei DjLe3eL6


def flaechen():
    from stellarator.spulen_satz import flaeche
    s_h = flaeche(FORM, nphi=64, ntheta=48, voll=False)
    s_v = flaeche(FORM, nphi=192, ntheta=96)
    s_d = flaeche(FORM, nphi=96, ntheta=48)
    R0 = float(s_v.get_rc(0, 0))
    a = float(np.sqrt(abs(s_v.volume()) / (2 * np.pi ** 2 * R0)))
    return s_h, s_v, s_d, R0, a


def lauf(fall, maxiter=2000, runden=2):
    """fall '<name>_w': setzt den fertigen Lauf <name> (biot_savart_<name>.json) mit weiteren Runden fort."""
    from scipy.optimize import minimize
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from simsopt.field.coil import ScaledCurrent
    from simsopt.geo import CurveLength, CurveCurveDistance, CurveSurfaceDistance, LpCurveCurvature, MeanSquaredCurvature
    from simsopt.objectives import SquaredFlux, QuadraticPenalty, Weight
    from stellarator import zwei_ringe as zr
    AUS.mkdir(parents=True, exist_ok=True)
    if (AUS / f"{fall}.fertig").exists():
        print("fertig, uebersprungen:", fall); return
    weiter = fall.endswith("_w"); kern = fall[:-2] if weiter else fall
    teile = kern.split("_"); kern = "_".join(teile[:2]); rb = 0.5   # Varianten: _o<Ordnung>, _k<Biegeradius in 1/100 a>, _lr
    laenge_ref = False                                            # _lr: Laengengrenze wie zwei_ringe (24,9 a je Spule, Proxima-Satz)
    for t in teile[2:]:
        if t == "lr":
            laenge_ref = True
        elif t.startswith("o"):
            zr.ORD = int(t[1:])
        elif t.startswith("k"):
            rb = int(t[1:]) / 100
    d, n = FAELLE[kern]
    s_h, s_v, s_d, R0, a = flaechen(); nfp = s_v.nfp
    ref = json.loads((ROOT / "sim" / "qi_zwei_ringe" / "C.json").read_text())
    msk_max = ref["msk_max"] * (ref["a_u"] / a) ** 2
    k_max = 1 / (rb * a); ss_min = 0.3 * a
    basis, I0 = [], []
    for i in range(n):
        phi = (i + 0.5) * 2 * np.pi / (2 * nfp * n)
        basis.append(zr.startkurve(s_v, phi, 1.08 * d * a)); I0.append(1e5)
    l_start = float(sum(CurveLength(c).J() for c in basis)); l_max = 1.25 * l_start
    if laenge_ref:                                                # wie zwei_ringe.optimieren: n * (Mittel Proxima-Satz + Umfangszuwachs)
        l_max = float(n * (np.mean(ref["ringe"]["ring0"]["laenge_basis_a"]) + 2 * np.pi * max(d - 0.85, 0)) * a)
    roh = [Current(x / 1e5) for x in I0]
    if weiter:                                                    # Kurven und Stroeme aus dem fertigen Lauf
        from simsopt import load
        alt = load(str(AUS / f"biot_savart_{fall[:-2]}.json")).coils[:n]
        for i, c in enumerate(alt):
            basis[i].x = c.curve.x; roh[i].x = [float(c.current.get_value()) / 1e5]
    roh[0].fix_all()
    cur = [ScaledCurrent(c, 1e5) for c in roh]
    sp = coils_via_symmetries(basis, cur, nfp, True)
    bs = BiotSavart(sp); bs.set_points(s_h.gamma().reshape(-1, 3))
    Jf = SquaredFlux(s_h, bs, definition="normalized")
    kurv = [c.curve for c in sp]
    Jss = CurveCurveDistance(kurv, ss_min, num_basecurves=n)
    Jsp = CurveSurfaceDistance(kurv, s_d, d * a)
    Jl = QuadraticPenalty(sum(CurveLength(c) for c in basis), l_max, "max")
    Jk = [LpCurveCurvature(c, 2, k_max) for c in basis]
    Jm = [QuadraticPenalty(MeanSquaredCurvature(c), msk_max, "max") for c in basis]
    w = {"ss": 1e2, "sp": 1e2, "l": 1e-4, "k": 1e-5, "m": 1e-8}
    verlauf = []; t0 = time.time(); ringe_idx = [list(range(n))]
    for runde in range(runden):
        JF = (Jf + Weight(w["ss"]) * Jss + Weight(w["sp"]) * Jsp + Weight(w["l"]) * Jl
              + Weight(w["k"]) * sum(Jk) + Weight(w["m"]) * sum(Jm))

        def fun(x):
            JF.x = x
            return JF.J(), JF.dJ()
        res = minimize(fun, JF.x, jac=True, method="L-BFGS-B", options={"maxiter": maxiter, "maxcor": 300}, tol=1e-15)
        JF.x = res.x
        e = zr.auswerten(basis, sp, 1, s_v, s_v, a, ringe_idx)       # Abstand auf dem feinen Rand (s_d 96x48 ueberschaetzt ihn)
        verl = {"ss": e["spule_spule_min_a"] < 0.98 * 0.3, "sp": e["ringe"]["ring0"]["abstand_plasma_a"] < 0.98 * d,
                "k": e["biegeradius_min_a"] < 0.98 * rb, "l": float(sum(CurveLength(c).J() for c in basis)) > 1.02 * l_max,
                "m": e["msk_max"] > 1.02 * msk_max}
        zeile = {"runde": runde, "iter": int(res.nit), "meldung": str(res.message), "Jf": float(Jf.J()), "gewichte": dict(w),
                 "verletzt": [k for k, v in verl.items() if v], "zeit_s": time.time() - t0, "Bn_mittel": e["Bn_mittel"],
                 "Bn_max": e["Bn_max"], "spule_spule_min_a": e["spule_spule_min_a"], "biegeradius_min_a": e["biegeradius_min_a"],
                 "abstand_a": e["ringe"]["ring0"]["abstand_plasma_a"]}
        verlauf.append(zeile); (AUS / f"verlauf_{fall}.json").write_text(json.dumps(verlauf, indent=1)); print(json.dumps(zeile), flush=True)
        bs.save(str(AUS / f"biot_savart_{fall}.json"))                 # Zwischenstand je Runde
        if not any(verl.values()) and res.nit < maxiter:            # weiter, solange Grenzen verletzt oder Schrittgrenze erreicht
            break
        for k, v in verl.items():
            if v:
                w[k] *= 10
    e.update(fall=fall, abstand_soll_a=d, spulen_je_halbperiode=n, form=str(FORM.relative_to(ROOT)),
             grenzen={"spule_spule_min_a": 0.3, "biegeradius_min_a": rb, "fourier_ordnung": zr.ORD, "laengenregel": "zwei_ringe" if laenge_ref else "1,25 x Start", "msk_max": msk_max, "laenge_max": l_max, "laenge_start": l_start},
             konvergenz={"runden": len(verlauf), "letzte_meldung": verlauf[-1]["meldung"], "grenzen_verletzt": verlauf[-1]["verletzt"],
                         "iter_letzte": verlauf[-1]["iter"]}, laufzeit_s=time.time() - t0,
             laenge_summe=float(sum(CurveLength(c).J() for c in basis)))
    (AUS / f"{fall}.json").write_text(json.dumps(e, indent=1))
    from stellarator.spulen_satz import export
    export(AUS / f"biot_savart_{fall}.json", FORM, AUS / f"satz_{fall}", 1.0, nb=n)
    (AUS / f"{fall}.fertig").write_text(time.strftime("%F %T"))
    print("FERTIG", fall, json.dumps({k: v for k, v in e.items() if not isinstance(v, (list, dict))}), flush=True)


def tabelle():
    z = ["| Fall | Abstand soll (a) | Spulen/halbe Periode | Feldfehler mittel | max | Abstand (a) | Spule–Spule (a) | Biegeradius (a) | verletzt | Zeit (min) |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for p in sorted(AUS.glob("d*_n*.json")):
        e = json.loads(p.read_text()); f = e["fall"]
        z.append(f"| {f} | {e['abstand_soll_a']} | {e['spulen_je_halbperiode']} | {e['Bn_mittel']:.2e} | {e['Bn_max']:.2e} | "
                 f"{e['ringe']['ring0']['abstand_plasma_a']:.3f} | {e['spule_spule_min_a']:.3f} | {e['biegeradius_min_a']:.3f} | "
                 f"{','.join(e['konvergenz']['grenzen_verletzt']) or '–'} | {e['laufzeit_s'] / 60:.1f} |")
    t = "\n".join(z); (AUS / "tabelle.md").write_text(t + "\n"); print(t)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "lauf":
        lauf(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2000)
    elif c == "liste":
        print("\n".join(list(FAELLE) if len(sys.argv) < 3 else sys.argv[2:]))
    elif c == "tabelle":
        tabelle()
