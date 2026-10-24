"""stufe1_desc.py — Stufe 1 (invers): Welches Magnetfeld wird gebraucht? -> Plasmaform.

Laeuft in .venv-opt (DESC/JAX, GPU). Optimiert die Randflaeche eines Vakuum-Gleichgewichts
(Druck 0, Netto-Strom 0) auf Quasisymmetrie + Seitenverhaeltnis + mittleres iota, mit
Fortsetzung in den Randmoden (k = 1..k_max), wie im DESC-Beispiel "precise QA".
Formoptimierung ist massstabsfrei (R0 ~ 1 m); Groesse und B0 werden spaeter gewaehlt.

  .venv-opt/bin/python invers/stufe1_desc.py --name qa_nfp2 [--nfp 2 --aspekt 6 --iota 0.42
      --helizitaet 1,0 --M 8 --N 8 --k_max 4 --maxiter 50]

Ausgabe sim/invers/<name>/: gleichgewicht.h5 (DESC), wout_<name>.nc (VMEC-Format fuer simsopt),
stufe1.json (Ziele, Kennzahlen, Vergleich mit DESC-Referenz precise_QA), stufe1_*.png.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np

PROJEKT = Path(__file__).resolve().parents[1]


def kennzahlen(eq, helizitaet) -> dict:
    from desc.grid import LinearGrid
    from desc.objectives import ObjectiveFunction, QuasisymmetryTwoTerm
    rho = np.linspace(0.1, 1.0, 10)
    iota = eq.compute("iota", grid=LinearGrid(rho=rho, M=eq.M_grid, N=eq.N_grid, NFP=eq.NFP))["iota"]
    g = LinearGrid(rho=rho, M=eq.M_grid, N=eq.N_grid, NFP=eq.NFP)
    iota = np.array([iota[g.nodes[:, 0] == r].mean() for r in rho])
    qs = ObjectiveFunction(QuasisymmetryTwoTerm(eq=eq, helicity=helizitaet,
                           grid=LinearGrid(M=eq.M_grid, N=eq.N_grid, NFP=eq.NFP, rho=np.array([0.6, 0.8, 1.0]), sym=True)))
    qs.build(verbose=0)
    d = {k: float(np.asarray(eq.compute(k)[k]).ravel()[0]) for k in ("R0", "a", "R0/a", "V")}
    return {"R0_m": d["R0"], "a_m": d["a"], "aspekt": d["R0/a"], "volumen_m3": d["V"],
            "iota_profil": {"rho": rho.tolist(), "iota": iota.tolist()},
            "iota_achse": float(iota[0]), "iota_rand": float(iota[-1]),
            "qs_fehler": float(np.sum(qs.compute_scaled_error(qs.x(eq)) ** 2))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stufe 1: Plasmaform-Optimierung mit DESC")
    ap.add_argument("--name", default="qa_nfp2")
    ap.add_argument("--nfp", type=int, default=2)
    ap.add_argument("--aspekt", type=float, default=6.0)
    ap.add_argument("--iota", type=float, default=0.42, help="Ziel mittleres iota")
    ap.add_argument("--helizitaet", default="1,0", help="M,N der Quasisymmetrie (1,0 = QA, 1,NFP = QH)")
    ap.add_argument("--M", type=int, default=8)
    ap.add_argument("--N", type=int, default=8)
    ap.add_argument("--k_max", type=int, default=4, help="hoechste freie Randmode")
    ap.add_argument("--maxiter", type=int, default=50)
    ap.add_argument("--cpu_ok", action="store_true", help="ohne GPU weiterrechnen (sonst Abbruch)")
    a = ap.parse_args(argv)

    import jax
    # JAX faellt bei CUDA-Initfehler STILL auf CPU zurueck (passiert, wenn zwei Prozesse
    # gleichzeitig CUDA initialisieren) -> ~10x langsamer. Lieber abbrechen und neu starten.
    if jax.devices()[0].platform != "gpu" and not a.cpu_ok:
        raise SystemExit(f"ABBRUCH: keine GPU ({jax.devices()}); neu starten oder --cpu_ok")
    print("Geraet:", jax.devices(), flush=True)
    from desc.equilibrium import Equilibrium
    from desc.geometry import FourierRZToroidalSurface
    from desc.grid import LinearGrid
    from desc.objectives import (ObjectiveFunction, ForceBalance, FixBoundaryR, FixBoundaryZ, FixPressure,
                                 FixCurrent, FixPsi, AspectRatio, QuasisymmetryTwoTerm, RotationalTransform)
    from desc.optimize import Optimizer
    from desc.vmec import VMECIO
    from desc.examples import get
    from desc.plotting import plot_surfaces, plot_boozer_surface
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

    ordner = PROJEKT / "sim" / "invers" / a.name; ordner.mkdir(parents=True, exist_ok=True)
    hel = tuple(int(x) for x in a.helizitaet.split(","))
    t_start = time.time(); log = []

    # Startflaeche wie DESC-Beispiel "precise QA": Torus R0=1, a=0,125, leichte Helix-Verformung
    surf = FourierRZToroidalSurface(R_lmn=[1.0, 0.125, 0.1], Z_lmn=[-0.125, -0.1],
                                    modes_R=[[0, 0], [1, 0], [0, 1]], modes_Z=[[-1, 0], [0, -1]], NFP=a.nfp)
    eq = Equilibrium(M=a.M, N=a.N, Psi=0.04, surface=surf, NFP=a.nfp, pressure=np.zeros(1), current=np.zeros(1))
    eq.solve(verbose=1, ftol=1e-2, maxiter=100)
    grid = LinearGrid(M=eq.M_grid, N=eq.N_grid, NFP=eq.NFP, rho=np.array([0.6, 0.8, 1.0]), sym=True)
    for k in range(1, a.k_max + 1):
        jax.clear_caches()
        t0 = time.time()
        obj = ObjectiveFunction((QuasisymmetryTwoTerm(eq=eq, helicity=hel, grid=grid),
                                 AspectRatio(eq=eq, target=a.aspekt, weight=1e1),
                                 RotationalTransform(eq=eq, target=a.iota, weight=1e1, loss_function="mean")))
        Rm = np.vstack(([0, 0, 0], eq.surface.R_basis.modes[np.max(np.abs(eq.surface.R_basis.modes), 1) > k, :]))
        Zm = eq.surface.Z_basis.modes[np.max(np.abs(eq.surface.Z_basis.modes), 1) > k, :]
        cons = (ForceBalance(eq=eq), FixBoundaryR(eq=eq, modes=Rm), FixBoundaryZ(eq=eq, modes=Zm),
                FixPressure(eq=eq), FixCurrent(eq=eq), FixPsi(eq=eq))
        eq, _ = eq.optimize(objective=obj, constraints=cons, optimizer=Optimizer("proximal-lsq-exact"),
                            maxiter=a.maxiter, ftol=1e-4, xtol=1e-6, copy=True, verbose=1)
        kz = kennzahlen(eq, hel)
        log.append({"k": k, "t_s": time.time() - t0, **{x: kz[x] for x in ("aspekt", "iota_achse", "iota_rand", "qs_fehler")}})
        print(f"[k={k}] {log[-1]}", flush=True)
        eq.save(ordner / "gleichgewicht.h5")

    erg = {"name": a.name, "ziele": {"nfp": a.nfp, "aspekt": a.aspekt, "iota_mittel": a.iota, "helizitaet": hel},
           "aufloesung": {"M": a.M, "N": a.N, "k_max": a.k_max}, "fortsetzung": log, "kennzahlen": kennzahlen(eq, hel)}
    try:   # Referenz nur, wenn sie zur Zielklasse passt
        if hel == (1, 0) and a.nfp == 2:
            erg["referenz_precise_QA"] = kennzahlen(get("precise_QA"), hel)
    except Exception as e:
        erg["referenz_fehler"] = str(e)
    VMECIO.save(eq, ordner / f"wout_{a.name}.nc", surfs=64, verbose=0)
    fig, ax = plot_surfaces(eq); fig.savefig(ordner / "stufe1_flaechen.png", dpi=110); plt.close(fig)
    fig, ax = plot_boozer_surface(eq); fig.savefig(ordner / "stufe1_boozer.png", dpi=110); plt.close(fig)
    erg["laufzeit_s"] = time.time() - t_start
    (ordner / "stufe1.json").write_text(json.dumps(erg, indent=2))
    print("FERTIG", ordner, json.dumps(erg["kennzahlen"] | {"qs_ref": erg.get("referenz_precise_QA", {}).get("qs_fehler")}))


if __name__ == "__main__":
    main()
