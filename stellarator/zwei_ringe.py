"""zwei_ringe.py — Vortest Nutzeridee F-221: zwei Spulenringe (innen + außen) gegen einen Ring, Plasma DjLe3eL6.

  .venv-opt/bin/python -m stellarator.zwei_ringe C            # Referenz: vorhandener Proxima-Satz (Einring ~0,85 a)
  .venv-opt/bin/python -m stellarator.zwei_ringe A085         # Kontrolle des Optimierers: eigener Einring bei 0,85 a
  .venv-opt/bin/python -m stellarator.zwei_ringe A            # Einring weit außen (1,3 a), 5 Spulen je Halbperiode
  .venv-opt/bin/python -m stellarator.zwei_ringe B            # Außenring 1,3 a + Innenring 0,85 a, Innenströme frei
  .venv-opt/bin/python -m stellarator.zwei_ringe B8           # wie B, Innenring 8 Spulen je Halbperiode

Keine Kettenänderung: liest nur sim/constellaration/qi/proxima_spulen_dje, schreibt sim/qi_zwei_ringe/<fall>.json
(+ verlauf_<fall>.json je Runde). Einheitsgeometrie wie proxima_spulen (R0 ~ 1,03, L = kopplung.L).

Optimierung: simsopt Stage-2, Ziel SquaredFlux "normalized" (stromskalenfrei) auf der halben Periode, Strafen für
Spule-Plasma-Abstand je Ring, Spule-Spule-Abstand (alle Spulen, auch zwischen den Ringen), Krümmung, mittlere
quadratische Krümmung, Ringlänge. Strafgewichte werden in Runden verzehnfacht, solange eine Grenze verletzt ist.
Ein Außenstrom ist fest (Maßstab), alle anderen frei. Start: Kurven an die um d entlang der Normale versetzte
Randfläche in der Ebene phi_i angepasst (Fourier-Ordnung 7 glättet Spitzen).

Auswertung (alle Fälle gleich): |B·n|/|B| mittel/max auf dem vollen Rand (128 x 64 wie proxima_spulen), Nettokraft je
Basisspule aus allen anderen Spulen (wie qi_kraft_scan.kraefte), f = F mu0/(B0^2 a^2) mit B0 = mittleres |B| auf
der Achse (Näherung: Schwerpunkt des Randquerschnitts je phi) und a = sqrt(V/(2 pi^2 R0)); Umrechnung auf B0 = 6,5 T,
a = 1,80 m: F = f * B0^2 a^2 / mu0, I = I_u * (6,5/B0_u) * (1,80/a_u).
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
Q = ROOT / "sim" / "constellaration" / "qi" / "proxima_spulen_dje"
AUS = ROOT / "sim" / "qi_zwei_ringe"
MU0 = 4e-7 * np.pi
B0_REAL, A_REAL = 6.5, 1.80
ORD = 7

FAELLE = {  # Ringe: (Abstand in a, Spulen je Halbperiode, Startstrom relativ)
    "A085": [(0.85, 5, 1.0)],
    "A": [(1.30, 5, 1.0)],
    "B": [(1.30, 5, 1.0), (0.85, 5, 0.1)],
    "B8": [(1.30, 5, 1.0), (0.85, 8, 0.1)],
}


def flaechen():
    from simsopt.geo import SurfaceRZFourier
    w = str(Q / "wout_skaliert.nc")
    s_h = SurfaceRZFourier.from_wout(w, range="half period", nphi=32, ntheta=32)
    s_v = SurfaceRZFourier.from_wout(w, range="full torus", nphi=128, ntheta=64)
    s_d = SurfaceRZFourier.from_wout(w, range="full torus", nphi=64, ntheta=32)   # für Abstandsstrafen
    R0 = float(s_v.get_rc(0, 0))
    a = float(np.sqrt(abs(s_v.volume()) / (2 * np.pi ** 2 * R0)))
    return s_h, s_v, s_d, R0, a


def achse(s_v):
    g = s_v.gamma()                                    # (nphi, ntheta, 3)
    return np.ascontiguousarray(g.mean(axis=1))        # Schwerpunkt je phi (Näherung der Achse)


def startkurve(s_v, phi, d, nq=128):
    """Kurve (Ordnung 7) durch die um d entlang der Normale versetzte Randlinie bei phi."""
    from simsopt.geo import SurfaceRZFourier, CurveXYZFourier
    t = np.linspace(0, 1, nq, endpoint=False)
    s1 = SurfaceRZFourier(nfp=s_v.nfp, stellsym=s_v.stellsym, mpol=s_v.mpol, ntor=s_v.ntor,
                          quadpoints_phi=[phi / (2 * np.pi)], quadpoints_theta=t)
    s1.x = s_v.x
    g = s1.gamma()[0]; n = s1.unitnormal()[0]
    if np.mean(np.sum((g - g.mean(0)) * n, axis=1)) < 0:
        n = -n                                         # Normale nach außen
    p = g + d * n
    M = [np.ones_like(t)]
    for k in range(1, ORD + 1):
        M += [np.sin(2 * np.pi * k * t), np.cos(2 * np.pi * k * t)]
    M = np.array(M).T
    dofs = np.concatenate([np.linalg.lstsq(M, p[:, j], rcond=None)[0] for j in range(3)])
    c = CurveXYZFourier(128, ORD); c.x = dofs
    return c


def auswerten(basis, sp, nring, s_v, s_d, a, ringe_idx):
    """Kennzahlen; ringe_idx: Liste der Basis-Indizes je Ring."""
    from simsopt.field import BiotSavart
    from simsopt.geo import CurveSurfaceDistance, CurveCurveDistance, MeanSquaredCurvature
    bs = BiotSavart(sp)
    bs.set_points(s_v.gamma().reshape(-1, 3))
    B = bs.B().reshape(s_v.gamma().shape); n = s_v.unitnormal()
    Bn = np.abs((B * n).sum(2)) / np.linalg.norm(B, axis=2)
    bs.set_points(achse(s_v)); B0 = float(np.linalg.norm(bs.B(), axis=1).mean())
    nb = len(basis)
    F = []
    for k in range(nb):
        o = BiotSavart([x for j, x in enumerate(sp) if j != k])
        g = sp[k].curve.gamma(); dl = sp[k].curve.gammadash() / len(g)
        o.set_points(np.ascontiguousarray(g))
        F.append(float(np.linalg.norm(float(sp[k].current.get_value()) * np.cross(dl, o.B()).sum(0))))
    F = np.asarray(F)
    f = F * MU0 / (B0 ** 2 * a ** 2)
    i_fak = (B0_REAL / B0) * (A_REAL / a)
    I = np.array([float(sp[k].current.get_value()) for k in range(nb)])
    kurv = [c.curve for c in sp]
    ring = {}
    for r, idx in enumerate(ringe_idx):
        sym = [sp[j].curve for j in range(len(sp)) if (j % nb) in idx]
        ring[f"ring{r}"] = {
            "basis_idx": idx,
            "abstand_plasma_a": float(CurveSurfaceDistance(sym, s_d, 0.0).shortest_distance()) / a,
            "f_max": float(f[idx].max()), "F_max_MN": float(f[idx].max() * B0_REAL ** 2 * A_REAL ** 2 / MU0 / 1e6),
            "I_basis_MA": (I[idx] * i_fak / 1e6).tolist(),
            "biegeradius_min_a": float(1 / max(np.max(basis[i].kappa()) for i in idx)) / a,
            "laenge_basis_a": [float(np.mean(np.linalg.norm(basis[i].gammadash(), axis=1))) / a for i in idx],
        }
    d_ss = float(CurveCurveDistance(kurv, 0.0, num_basecurves=nb).shortest_distance())
    return {"Bn_mittel": float(Bn.mean()), "Bn_max": float(Bn.max()), "B0_achse_u_T": B0, "a_u": a,
            "f_max": float(f.max()), "F_max_MN": float(f.max() * B0_REAL ** 2 * A_REAL ** 2 / MU0 / 1e6),
            "f_je_basis": f.tolist(),
            "summe_I_alle_MA": float(np.abs(I).sum() * len(sp) / nb * i_fak / 1e6),
            "biegeradius_min_a": float(1 / max(np.max(c.kappa()) for c in basis)) / a,
            "spule_spule_min_a": d_ss / a, "n_spulen": len(sp), "n_basis": nb,
            "msk_max": float(max(MeanSquaredCurvature(c).J() for c in basis)), "ringe": ring}


def referenz():
    sys.path.insert(0, str(ROOT))
    from simsopt.field import Current, coils_via_symmetries
    from stellarator import proxima_spulen as ps
    ps.O = Q
    s_h, s_v, s_d, R0, a = flaechen()
    fak = json.loads((Q / "skalierung.json").read_text())["faktor"]
    basis, I, nfp = ps.kurven(fak, -1)                  # Vorzeichen -1 laut stufe2.json des Satzes
    sp = coils_via_symmetries(basis, [Current(x) for x in I], nfp, True)
    return auswerten(basis, sp, 1, s_v, s_d, a, [list(range(len(basis)))])


def optimieren(fall, maxiter=2000, runden=2):
    from scipy.optimize import minimize
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from simsopt.field.coil import ScaledCurrent
    from simsopt.geo import (CurveLength, CurveCurveDistance, CurveSurfaceDistance, LpCurveCurvature,
                             MeanSquaredCurvature)
    from simsopt.objectives import SquaredFlux, QuadraticPenalty, Weight
    s_h, s_v, s_d, R0, a = flaechen()
    nfp = s_v.nfp
    ref = json.loads((AUS / "C.json").read_text()) if (AUS / "C.json").exists() else None
    msk_max = ref["msk_max"] if ref else 200.0
    k_max = 1 / (0.5 * a)                               # Biegeradius >= 0,5 a (wie qi_kraft_scan-Auswahl)
    ss_min = 0.3 * a                                    # Spule-Spule (Mittellinie) >= 0,3 a, auch zwischen Ringen
    basis, I0, ringe_idx, d_ring, l_max = [], [], [], [], []
    for r, (d, n, i_rel) in enumerate(FAELLE[fall]):
        idx = []
        for i in range(n):
            phi = (i + 0.5) * 2 * np.pi / (2 * nfp * n)
            c = startkurve(s_v, phi, 1.08 * d * a)
            idx.append(len(basis)); basis.append(c); I0.append(1e5 * i_rel)
        ringe_idx.append(idx); d_ring.append(d * a)
        # Laengengrenze wie der Proxima-Satz (Summe 124,5 a je 5 Spulen) plus Umfangszuwachs 2 pi (d - 0,85) a je Spule
        l_ref = (ref["ringe"]["ring0"]["laenge_basis_a"] if ref else [24.9] * 5)
        l_max.append(float(n * (np.mean(l_ref) + 2 * np.pi * max(d - 0.85, 0)) * a))
    roh = [Current(x / 1e5) for x in I0]; roh[0].fix_all()
    cur = [ScaledCurrent(c, 1e5) for c in roh]          # Stromfreiheitsgrade ~1 (sonst bewegt L-BFGS die Stroeme nicht)
    sp = coils_via_symmetries(basis, cur, nfp, True)
    nb = len(basis)
    bs = BiotSavart(sp); bs.set_points(s_h.gamma().reshape(-1, 3))
    Jf = SquaredFlux(s_h, bs, definition="normalized")
    kurv = [c.curve for c in sp]
    Jss = CurveCurveDistance(kurv, ss_min, num_basecurves=nb)
    Jsp = [CurveSurfaceDistance([sp[j].curve for j in range(len(sp)) if (j % nb) in idx], s_d, d)
           for idx, d in zip(ringe_idx, d_ring)]
    Jl = [QuadraticPenalty(sum(CurveLength(basis[i]) for i in idx), lm, "max") for idx, lm in zip(ringe_idx, l_max)]
    Jk = [LpCurveCurvature(c, 2, k_max) for c in basis]
    Jm = [QuadraticPenalty(MeanSquaredCurvature(c), msk_max, "max") for c in basis]
    w = {"ss": 1e2, "sp": 1e2, "l": 1e-4, "k": 1e-5, "m": 1e-8}
    verlauf = []
    t0 = time.time()
    for runde in range(runden):
        JF = (Jf + Weight(w["ss"]) * Jss + Weight(w["sp"]) * sum(Jsp) + Weight(w["l"]) * sum(Jl)
              + Weight(w["k"]) * sum(Jk) + Weight(w["m"]) * sum(Jm))

        def fun(x):
            JF.x = x
            return JF.J(), JF.dJ()
        res = minimize(fun, JF.x, jac=True, method="L-BFGS-B", options={"maxiter": maxiter, "maxcor": 300}, tol=1e-15)
        JF.x = res.x
        e = auswerten(basis, sp, len(ringe_idx), s_v, s_d, a, ringe_idx)
        verl = {"ss": e["spule_spule_min_a"] < 0.98 * ss_min / a,
                "sp": any(e["ringe"][f"ring{r}"]["abstand_plasma_a"] < 0.98 * d / a for r, d in enumerate(d_ring)),
                "k": e["biegeradius_min_a"] < 0.98 * 0.5,
                "l": any(sum(CurveLength(basis[i]).J() for i in idx) > 1.02 * lm for idx, lm in zip(ringe_idx, l_max)),
                "m": e["msk_max"] > 1.02 * msk_max}
        zeile = {"runde": runde, "iter": int(res.nit), "meldung": str(res.message), "Jf": float(Jf.J()),
                 "gewichte": dict(w), "verletzt": [k for k, v in verl.items() if v], "zeit_s": time.time() - t0,
                 "Bn_mittel": e["Bn_mittel"], "Bn_max": e["Bn_max"], "f_max": e["f_max"],
                 "spule_spule_min_a": e["spule_spule_min_a"], "biegeradius_min_a": e["biegeradius_min_a"],
                 "abstand_a": [e["ringe"][k]["abstand_plasma_a"] for k in e["ringe"]]}
        verlauf.append(zeile)
        (AUS / f"verlauf_{fall}.json").write_text(json.dumps(verlauf, indent=1))
        print(json.dumps(zeile), flush=True)
        if not any(verl.values()):
            break
        for k, v in verl.items():
            if v:
                w[k] *= 10
    e["fall"] = fall; e["ringe_soll_a"] = [d for d, _, _ in FAELLE[fall]]
    e["grenzen"] = {"spule_spule_min_a": ss_min / a, "biegeradius_min_a": 0.5, "msk_max": msk_max,
                    "laenge_max_u": l_max}
    e["konvergenz"] = {"runden": len(verlauf), "letzte_meldung": verlauf[-1]["meldung"],
                       "grenzen_verletzt": verlauf[-1]["verletzt"], "iter_letzte": verlauf[-1]["iter"]}
    e["laufzeit_s"] = time.time() - t0
    bs.save(str(AUS / f"biot_savart_{fall}.json"))
    return e


def nachauswerten(fall):
    """Kennzahlen aus gespeichertem biot_savart_<fall>.json (falls der Lauf beim Schreiben abbrach)."""
    from simsopt import load
    s_h, s_v, s_d, R0, a = flaechen()
    sp = load(str(AUS / f"biot_savart_{fall}.json")).coils
    ringe_idx, k = [], 0
    for d, n, _ in FAELLE[fall]:
        ringe_idx.append(list(range(k, k + n))); k += n
    basis = [c.curve for c in sp[:k]]
    e = auswerten(basis, sp, len(ringe_idx), s_v, s_d, a, ringe_idx)
    v = json.loads((AUS / f"verlauf_{fall}.json").read_text())
    e["fall"] = fall; e["ringe_soll_a"] = [d for d, _, _ in FAELLE[fall]]
    e["konvergenz"] = {"runden": len(v), "letzte_meldung": v[-1]["meldung"], "grenzen_verletzt": v[-1]["verletzt"],
                       "iter_letzte": v[-1]["iter"]}
    e["nachausgewertet"] = True
    return e


if __name__ == "__main__":
    fall = sys.argv[1]
    if fall == "nach":
        AUS.mkdir(parents=True, exist_ok=True); f2 = sys.argv[2]
        (AUS / f"{f2}.json").write_text(json.dumps(nachauswerten(f2), indent=1)); print("FERTIG nach", f2); sys.exit()
    AUS.mkdir(parents=True, exist_ok=True)
    erg = referenz() if fall == "C" else optimieren(fall, int(sys.argv[2]) if len(sys.argv) > 2 else 1500)
    (AUS / f"{fall}.json").write_text(json.dumps(erg, indent=1))
    print("FERTIG", fall, json.dumps({k: v for k, v in erg.items() if not isinstance(v, (list, dict))}), flush=True)
