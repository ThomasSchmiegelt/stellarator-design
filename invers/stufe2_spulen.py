"""stufe2_spulen.py — Stufe 2 (invers): Welche Spulen erzeugen das Zielfeld? (simsopt Stage-2)

Laeuft in .venv-opt. Ziel: B·n = 0 auf der Plasma-Randflaeche aus Stufe 1 (Vakuumfeld), mit
technischen Grenzen: Gesamtlaenge, Spule-Spule-Abstand, Spule-Plasma-Abstand, Kruemmung,
mittlere quadratische Kruemmung. Basisspulen je halber Feldperiode, Rest per Symmetrie
(nfp x Stellarator-Symmetrie). Ein Basisstrom ist fest (sonst Loesung "alle Stroeme 0");
Groesse/B0 werden in Stufe 3 durch Skalierung gesetzt.

  .venv-opt/bin/python invers/stufe2_spulen.py --wout sim/invers/<fall>/wout_<fall>.nc --name <fall>_spulen
      [--n_spulen 4 --ordnung 6 --laenge_max 18 --abstand_ss 0.1 --abstand_sp 0.3 --kruemmung_max 5
       --maxiter 400]

Ausgabe sim/invers/<name>/: spulen.json (Austauschformat fuer .venv-Pipeline: alle Spulen als
Punkte + Strom, nfp, Basisanzahl), biot_savart.json (simsopt), stufe2.json (Kennzahlen),
stufe2_spulen.png.
"""
from __future__ import annotations
import argparse, json, os, time
# simsopt braucht keine GPU; JAX darf sie nicht belegen (nur EIN JAX-GPU-Prozess, sonst
# CUDA_ERROR_NO_DEVICE beim zweiten -> DESC faellt auf CPU zurueck)
os.environ.setdefault("JAX_PLATFORMS", "cpu")
from pathlib import Path
import numpy as np

PROJEKT = Path(__file__).resolve().parents[1]


def plasma_rand(s_voll, wout) -> dict:
    """Ausdehnung der Randflaeche + Achse/Aussenrand bei phi=0 (Rahmen fuer die Feldlinien in .venv)."""
    from netCDF4 import Dataset
    g = s_voll.gamma(); R = np.hypot(g[..., 0], g[..., 1])
    with Dataset(str(wout)) as w:
        R_achse = float(np.sum(w["raxis_cc"][:]))
    return {"R_min_m": float(R.min()), "R_max_m": float(R.max()), "Z_max_m": float(np.abs(g[..., 2]).max()),
            "R_achse_phi0_m": R_achse, "R_aussen_phi0_m": float(R[0, 0])}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stufe 2: Spulenoptimierung mit simsopt")
    ap.add_argument("--wout", type=Path, required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--n_spulen", type=int, default=4, help="Basisspulen je halber Feldperiode")
    ap.add_argument("--ordnung", type=int, default=6, help="Fourier-Ordnung der Spulenkurven")
    ap.add_argument("--R1", type=float, default=0.5, help="Startradius der Spulen (bei R0~1 m)")
    ap.add_argument("--laenge_max", type=float, default=18.0, help="Summe der Basisspulenlaengen (m)")
    ap.add_argument("--abstand_ss", type=float, default=0.10, help="min. Spule-Spule-Abstand (m, Mittellinie)")
    ap.add_argument("--abstand_sp", type=float, default=0.30, help="min. Spule-Plasma-Abstand (m)")
    ap.add_argument("--kruemmung_max", type=float, default=5.0, help="max. Kruemmung (1/m) -> R_min = 1/k")
    ap.add_argument("--msk_max", type=float, default=5.0, help="max. mittlere quadratische Kruemmung")
    ap.add_argument("--maxiter", type=int, default=400)
    a = ap.parse_args(argv)

    from scipy.optimize import minimize
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from simsopt.geo import (SurfaceRZFourier, create_equally_spaced_curves, CurveLength, CurveCurveDistance,
                             MeanSquaredCurvature, LpCurveCurvature, CurveSurfaceDistance)
    from simsopt.objectives import SquaredFlux, QuadraticPenalty, Weight

    ordner = PROJEKT / "sim" / "invers" / a.name; ordner.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    s = SurfaceRZFourier.from_wout(str(a.wout), range="half period", nphi=32, ntheta=32)
    s_voll = SurfaceRZFourier.from_wout(str(a.wout), range="full torus", nphi=128, ntheta=64)
    R0 = float(s.get_rc(0, 0))
    basis = create_equally_spaced_curves(a.n_spulen, s.nfp, stellsym=True, R0=R0, R1=a.R1, order=a.ordnung)
    stroeme = [Current(1e5) for _ in range(a.n_spulen)]
    stroeme[0].fix_all()
    spulen = coils_via_symmetries(basis, stroeme, s.nfp, True)
    kurven = [c.curve for c in spulen]
    bs = BiotSavart(spulen); bs.set_points(s.gamma().reshape((-1, 3)))

    Jf = SquaredFlux(s, bs)
    Jl = [CurveLength(c) for c in basis]
    Jss = CurveCurveDistance(kurven, a.abstand_ss, num_basecurves=a.n_spulen)
    Jsp = CurveSurfaceDistance(kurven, s, a.abstand_sp)
    Jk = [LpCurveCurvature(c, 2, a.kruemmung_max) for c in basis]
    Jmsk = [MeanSquaredCurvature(c) for c in basis]
    JF = (Jf + Weight(1e-6) * QuadraticPenalty(sum(Jl), a.laenge_max, "max") + Weight(1000) * Jss
          + Weight(10) * Jsp + Weight(1e-6) * sum(Jk)
          + Weight(1e-6) * sum(QuadraticPenalty(J, a.msk_max, "max") for J in Jmsk))
    verlauf = []

    def fun(x):
        JF.x = x
        J, dJ = JF.J(), JF.dJ()
        verlauf.append(float(Jf.J()))
        return J, dJ

    res = minimize(fun, JF.x, jac=True, method="L-BFGS-B",
                   options={"maxiter": a.maxiter, "maxcor": 300}, tol=1e-15)
    # zweiter Durchgang mit staerkerer Laengenstrafe (wie simsopt-Beispiel)
    JF2 = JF + Weight(1e-4) * QuadraticPenalty(sum(Jl), a.laenge_max, "max")

    def fun2(x):
        JF2.x = x
        verlauf.append(float(Jf.J()))
        return JF2.J(), JF2.dJ()
    res2 = minimize(fun2, JF2.x, jac=True, method="L-BFGS-B",
                    options={"maxiter": a.maxiter // 2, "maxcor": 300}, tol=1e-15)

    # Kennzahlen auf der vollen Flaeche
    bs.set_points(s_voll.gamma().reshape((-1, 3)))
    B = bs.B().reshape(s_voll.gamma().shape)
    n = s_voll.unitnormal()
    Bn = np.abs(np.sum(B * n, axis=2)) / np.linalg.norm(B, axis=2)
    kr = [float(np.max(c.kappa())) for c in basis]
    erg = {"name": a.name, "wout": str(a.wout), "parameter": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()},
           "nfp": int(s.nfp), "n_basis": a.n_spulen, "n_spulen": len(spulen),
           "Bn_rel_mittel": float(Bn.mean()), "Bn_rel_max": float(Bn.max()),
           "laenge_basis_m": [float(J.J()) for J in Jl], "laenge_summe_m": float(sum(J.J() for J in Jl)),
           "abstand_ss_min_m": float(Jss.shortest_distance()), "abstand_sp_min_m": float(Jsp.shortest_distance()),
           "kruemmung_max_1_m": max(kr), "biegeradius_min_m": 1 / max(kr),
           "stroeme_basis_A": [float(c.get_value()) for c in stroeme],
           "optimierer": {"iter_1": int(res.nit), "iter_2": int(res2.nit), "meldung": str(res2.message)},
           "squared_flux_verlauf": verlauf[:: max(1, len(verlauf) // 50)],
           "laufzeit_s": time.time() - t_start}
    (ordner / "stufe2.json").write_text(json.dumps(erg, indent=2))
    bs.save(str(ordner / "biot_savart.json"))
    # Austauschformat fuer die Bestandspipeline (.venv)
    aus = {"quelle": "simsopt", "wout": str(a.wout), "nfp": int(s.nfp), "stellsym": True, "n_basis": a.n_spulen,
           "R0_m": R0, "einheit": "m", "plasma_rand": plasma_rand(s_voll, a.wout),
           "abstand_sp_min_m": erg["abstand_sp_min_m"],
           "spulen": [{"name": f"S{i % a.n_spulen + 1}_k{i // a.n_spulen}", "typ": f"S{i % a.n_spulen + 1}",
                       "punkte_m": c.curve.gamma().tolist(), "strom_A": float(c.current.get_value())}
                      for i, c in enumerate(spulen)]}
    (ordner / "spulen.json").write_text(json.dumps(aus))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(12, 5), dpi=110)
        ax = fig.add_subplot(121, projection="3d")
        g = s_voll.gamma()
        ax.plot_surface(g[..., 0], g[..., 1], g[..., 2], color="#9ecae1", alpha=.35, linewidth=0)
        for c in spulen:
            p = c.curve.gamma(); ax.plot(*np.vstack([p, p[:1]]).T, color="#c87533", lw=1.5)
        ax.set_box_aspect((1, 1, .4)); ax.set_axis_off(); ax.set_title(f"{a.name}: {len(spulen)} Spulen")
        ax2 = fig.add_subplot(122)
        im = ax2.imshow(Bn.T, origin="lower", aspect="auto", cmap="magma")
        fig.colorbar(im, ax=ax2, label="|B·n|/|B|"); ax2.set(xlabel="phi-Index", ylabel="theta-Index",
                                                               title=f"Restfehler B·n (Mittel {Bn.mean():.1e})")
        fig.tight_layout(); fig.savefig(ordner / "stufe2_spulen.png"); plt.close(fig)
    except Exception as e:
        print("Bild fehlgeschlagen:", e)
    print("FERTIG", ordner, json.dumps({k: erg[k] for k in ("Bn_rel_mittel", "Bn_rel_max", "laenge_summe_m",
          "abstand_ss_min_m", "abstand_sp_min_m", "biegeradius_min_m", "laufzeit_s")}))


if __name__ == "__main__":
    main()
