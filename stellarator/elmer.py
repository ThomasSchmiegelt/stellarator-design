"""elmer.py — Magnetostatik der Wickelpakete mit ElmerFEM (3D, Kantenelemente).

Kette: cad.elmer_netz (gmsh -> ElmerGrid) -> case.sif -> ElmerSolver -> feld_t0001.vtu.
Stromverteilung je Wickelpaket: CoilSolver (geschlossene Spule, Component je Spule,
Desired Current Density = Ampere-Windungen / Querschnitt), dann WhitneyAVSolver und
MagnetoDynamicsCalcFields. Randbedingung AV=0 am Luftquader (rand_m >= 5 m, B-015).
Validierung gegen Biot-Savart (Mehrfilament 5x5): vergleiche().

Aufruf:
    .venv/bin/python -m stellarator.elmer <ordner> [--spulen 1] [--h_spule 0.03] [--h_luft 0.6]
"""
from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path
import numpy as np
from . import spulen as sp, cad

KOPF = """Header
  Mesh DB "." "netz"
  Results Directory "erg"
End
Simulation
  Coordinate System = Cartesian
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Output Intervals(1) = 1
End
Constants
  Permeability of Vacuum = 1.2566370614e-6
End
Material 1
  Relative Permeability = 1.0
  Electric Conductivity = 1.0
End
Equation 1
  Active Solvers(3) = 1 2 3
End
Equation 2
  Active Solvers(2) = 2 3
End
Solver 1
  Equation = "CoilSolver"
  Procedure = "CoilSolver" "CoilSolver"
  Linear System Solver = "Iterative"
  Linear System Iterative Method = "CG"
  Linear System Preconditioning = ILU0
  Linear System Max Iterations = 5000
  Linear System Convergence Tolerance = 1e-8
  Linear System Abort Not Converged = False
  Normalize Coil Current = Logical True
  Calculate Elemental Fields = Logical True
  Narrow Interface = Logical True
End
Solver 2
  Equation = "MGDynamics"
  Procedure = "MagnetoDynamics" "WhitneyAVSolver"
  Fix Input Current Density = Logical True
  ! Jfix-Hilfsproblem ist reines Neumann-Problem (singulaer): BiCGStabl+ILU divergiert
  ! bei 70 Spulen (Residuum 1e19), CG konvergiert (B-015)
  Jfix: Linear System Solver = "Iterative"
  Jfix: Linear System Iterative Method = "CG"
  Jfix: Linear System Preconditioning = None
  Jfix: Linear System Max Iterations = 10000
  Jfix: Linear System Convergence Tolerance = 1e-8
  Jfix: Linear System Abort Not Converged = False
  Jfix: Linear System Residual Output = 500
  Linear System Solver = "Iterative"
  Linear System Iterative Method = "BiCGStabl"
  BiCGStabl Polynomial Degree = 4
  Linear System Preconditioning = None
  Linear System Max Iterations = 5000
  Linear System Convergence Tolerance = 1e-8
  Linear System Residual Output = 200
End
Solver 3
  Equation = "MGDynamicsCalc"
  Procedure = "MagnetoDynamics" "MagnetoDynamicsCalcFields"
  Potential Variable = String "AV"
  Calculate Magnetic Field Strength = Logical True
  Calculate Nodal Fields = Logical True
  Calculate Elemental Fields = Logical True
  Linear System Solver = "Iterative"
  Linear System Iterative Method = "CG"
  Linear System Preconditioning = ILU0
  Linear System Max Iterations = 2000
  Linear System Convergence Tolerance = 1e-10
End
Solver 4
  Exec Solver = After All
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = "feld"
  Vtu Format = Logical True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  AV {e} = Real 0.0
End
"""


KB_PRO_TET = 3.5   # gemessener Elmer-Spitzenbedarf je Tetraeder (B-015)
NORMAL_VZ = -1.0   # Konvention Coil Normal <-> Stromrichtung, per Test bestimmt (B-016)


def schreibe_sif(spulen, breite, hoehe, pfad: Path) -> None:
    """case.sif: Body i = Spule i (Component k, Body Force k), Body n+1 = Luft.
    Stromlose Spulen (z.B. PCA/PCB im Standardfall) bekommen keine Component (J=0 stoert
    die CoilSolver-Normierung) und nur die Luft-Gleichung."""
    n = len(spulen)
    S = [KOPF]
    k = 0
    for i, s in enumerate(spulen, 1):
        if s.strom == 0:
            S.append(f'Body {i}\n  Name = "{s.name}"\n  Equation = 2\n  Material = 1\nEnd\n')
            continue
        k += 1
        # CoilSolver ignoriert das Vorzeichen von J und waehlt die Richtung selbst (B-016):
        # Richtung ueber Coil Normal = Flaechenvektor des orientierten Filaments x sign(I)
        J = abs(s.strom) / (breite * hoehe)
        c = s.punkte.mean(0)
        A = 0.5 * np.cross(s.punkte - c, np.roll(s.punkte, -1, 0) - c).sum(0)
        nrm = np.sign(s.strom) * NORMAL_VZ * A / np.linalg.norm(A)
        S.append(f'Body {i}\n  Name = "{s.name}"\n  Equation = 1\n  Material = 1\n'
                 f'  Body Force = {k}\nEnd\n')
        S.append(f'Component {k}\n  Name = "{s.name}"\n  Master Bodies(1) = {i}\n'
                 f'  Coil Type = "test"\n  Desired Current Density = Real {J:.6e}\n'
                 f'  Coil Center(3) = Real {c[0]:.6f} {c[1]:.6f} {c[2]:.6f}\n'
                 f'  Coil Normal(3) = Real {nrm[0]:.6f} {nrm[1]:.6f} {nrm[2]:.6f}\n'
                 f'  Coil Closed = Logical True\nEnd\n')   # "unlisted keyword"-Warnung, wird aber benoetigt
        S.append(f'Body Force {k}\n' + "".join(
            f'  Current Density {c} = Equals "CoilCurrent e {c}"\n' for c in (1, 2, 3)) + "End\n")
    S.append(f'Body {n + 1}\n  Name = "luft"\n  Equation = 2\n  Material = 1\nEnd\n')
    pfad.write_text("".join(S))


def _filamente(spulen, breite, hoehe):
    """Biot-Savart-Segmente: je stromfuehrendem Wickelpaket 5x5 Filamente."""
    fil = []
    for s in spulen:
        if s.strom == 0:
            continue
        t, n, b = sp.rahmen(s)
        for a in np.linspace(-0.4, 0.4, 5):
            for c in np.linspace(-0.4, 0.4, 5):
                fil.append(sp.Spule("f", s.typ, s.punkte + a * breite * n + c * hoehe * b, s.strom / 25))
    return sp.segmente(fil)


def vergleiche(vtu: Path, spulen, breite, hoehe, rand_m: float, n_max: int = 40000) -> dict:
    """Elmer-B vs. Biot-Savart (5x5 Filamente je Wickelpaket) nach Abstand zur Spule,
    an hoechstens n_max zufaelligen Netzknoten; bei vollem Satz zusaetzlich auf der Achse."""
    import pyvista as pv
    from scipy.spatial import cKDTree
    m = pv.read(vtu)
    x, Bfem = m.points, m.point_data["magnetic flux density"]
    if len(x) > n_max:
        k = np.random.default_rng(0).choice(len(x), n_max, replace=False)
        x, Bfem = x[k], Bfem[k]
    seg = _filamente(spulen, breite, hoehe)
    P = np.concatenate([s.punkte for s in spulen])
    dist, _ = cKDTree(P).query(x)
    innen = np.all((x > P.min(0) - rand_m + 0.3) & (x < P.max(0) + rand_m - 0.3), 1)
    Bbs = sp.biot_savart(x, seg)
    out = {}
    for r0, r1 in [(0.2, 0.4), (0.4, 0.8), (0.8, 1.5)]:
        k = innen & (dist >= r0) & (dist < r1)
        e = np.linalg.norm(Bfem[k] - Bbs[k], axis=1) / np.linalg.norm(Bbs[k], axis=1)
        out[f"{r0}-{r1}m"] = {"n": int(k.sum()), "median": float(np.median(e)),
                              "p90": float(np.percentile(e, 90))}
    if len(spulen) == 70:
        A = sp.achse(np.linspace(0, 2 * np.pi, 200, endpoint=False))
        Bf = np.linalg.norm(pv.PolyData(A).sample(m).point_data["magnetic flux density"], axis=1)
        Bb = np.linalg.norm(sp.biot_savart(A, seg), axis=1)
        out["achse"] = {"B_mittel_fem_T": float(Bf.mean()), "B_mittel_bs_T": float(Bb.mean()),
                        "fehler_median": float(np.median(np.abs(Bf - Bb) / Bb)),
                        "fehler_max": float(np.max(np.abs(Bf - Bb) / Bb))}
    return out


def bild(vtu: Path, spulen, breite, hoehe, pfad: Path) -> None:
    """|B| entlang einer Linie durch die Spulenmitte (senkrecht zur Spulenebene): Elmer vs. BS."""
    import pyvista as pv, matplotlib
    matplotlib.use("Agg"); import matplotlib.pyplot as plt
    m = pv.read(vtu)
    s = spulen[0]; c = s.punkte.mean(0)
    _, _, V = np.linalg.svd(s.punkte - c); ax = V[2]          # Normale der Ausgleichsebene
    u = np.linspace(-3, 3, 301); L = c + u[:, None] * ax
    Bf = np.linalg.norm(pv.PolyData(L).sample(m).point_data["magnetic flux density"], axis=1)
    Bb = np.linalg.norm(sp.biot_savart(L, _filamente(spulen, breite, hoehe)), axis=1)
    fig, a = plt.subplots(figsize=(7, 4))
    a.plot(u, Bb, "k-", label="Biot-Savart (5x5 Filamente)")
    a.plot(u, Bf, "r--", label="ElmerFEM (CoilSolver + WhitneyAV)")
    a.set_xlabel("Abstand von der Spulenmitte entlang der Spulennormalen [m]")
    a.set_ylabel("|B| [T]"); a.grid(alpha=.3); a.legend()
    a.set_title(f"{len(spulen)} Wickelpaket(e), {spulen[0].name} …")
    fig.tight_layout(); fig.savefig(pfad, dpi=130); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Elmer-Magnetostatik der Wickelpakete")
    ap.add_argument("ordner", type=Path)
    ap.add_argument("--spulen", type=int, default=1, help="erste n Spulen des W7-X-Satzes")
    ap.add_argument("--n_punkte", type=int, default=160)
    ap.add_argument("--breite", type=float, default=0.192)
    ap.add_argument("--hoehe", type=float, default=0.160)
    ap.add_argument("--rand", type=float, default=5.0)
    ap.add_argument("--h_spule", type=float, default=0.03)
    ap.add_argument("--h_luft", type=float, default=0.6)
    ap.add_argument("--dist_max", type=float, default=3.0)
    ap.add_argument("--netz_vorhanden", action="store_true", help="vorhandenes ordner/netz nutzen")
    ap.add_argument("--nur_auswerten", action="store_true",
                    help="nur erg/feld_t0001.vtu auswerten (Elmer lief schon, z.B. losgeloest)")
    ap.add_argument("--B0", type=float, help="Stroeme auf mittleres B_Achse kalibrieren (nur --spulen 70)")
    a = ap.parse_args(argv)
    sps = sp.w7x_spulensatz(n_punkte=a.n_punkte)
    if a.B0:
        sp.kalibriere(sps, a.B0)
    sps = sps[:a.spulen]
    erg = {"spulen": [s.name for s in sps], "parameter": vars(a) | {"ordner": str(a.ordner)}}
    if a.nur_auswerten:
        return _auswerten(a, sps, erg)
    if a.netz_vorhanden:
        n_tet = int((a.ordner / "netz" / "mesh.header").read_text().split()[1])
        erg["netz"] = {"n_tet": n_tet, "netz": str(a.ordner / "netz"), "wiederverwendet": True}
    else:
        erg["netz"] = cad.elmer_netz(sps, a.breite, a.hoehe, a.ordner, rand_m=a.rand,
                                     h_spule=a.h_spule, h_luft=a.h_luft, dist_max=a.dist_max)
    schreibe_sif(sps, a.breite, a.hoehe, a.ordner / "case.sif")
    bedarf = erg["netz"]["n_tet"] * KB_PRO_TET / 1e6
    frei = int(next(l for l in open("/proc/meminfo") if l.startswith("MemAvailable")).split()[1]) / 1e6
    erg["ram_schaetzung_GB"] = {"bedarf": bedarf, "frei": frei}
    if bedarf > 0.85 * frei:
        (a.ordner / "ergebnis.json").write_text(json.dumps(erg, indent=2, ensure_ascii=False))
        raise SystemExit(f"ABBRUCH: Elmer braucht ~{bedarf:.1f} GB, frei {frei:.1f} GB -> h_spule groesser waehlen")
    t0 = time.time()
    with open(a.ordner / "solve.log", "w") as f:
        subprocess.run(["ElmerSolver", "case.sif"], cwd=a.ordner, stdout=f, stderr=subprocess.STDOUT, check=True)
    erg["t_elmer_s"] = time.time() - t0
    _auswerten(a, sps, erg)


def stroeme_aus_sif(pfad: Path) -> dict:
    """Ampere-Windungen je Spulenname, wie sie im case.sif stehen (J * Querschnitt folgt im Aufrufer)."""
    import re
    return {m.group(1): float(m.group(2)) for m in re.finditer(
        r'Component \d+\n  Name = "([^"]+)"\n.*?Desired Current Density = Real ([-0-9.eE+]+)', pfad.read_text(), re.S)}


def richtung_pruefen(vtu: Path, spulen) -> list[str]:
    """Spulen, deren Elmer-Stromdichte (CoilCurrent) gegen die Filamentrichtung x sign(I) laeuft."""
    import pyvista as pv
    from scipy.spatial import cKDTree
    m = pv.read(vtu)
    J, baum = m.point_data["coilcurrent"], cKDTree(m.points)
    falsch = []
    for s in spulen:
        if s.strom == 0:
            continue
        _, k = baum.query(s.punkte[::4])
        if np.sign(np.median(np.sum(J[k] * s.tangenten()[::4], 1))) != np.sign(s.strom):
            falsch.append(s.name)
    return falsch


def _auswerten(a, sps, erg):
    if a.nur_auswerten:   # Stroeme exakt wie im gerechneten Fall (Kalibrierung kann sich geaendert haben)
        J = stroeme_aus_sif(a.ordner / "case.sif")
        for s in sps:
            s.strom = J.get(s.name, 0.0) * a.breite * a.hoehe
        erg["stroeme_aus"] = "case.sif"
    vtu = a.ordner / "erg" / "feld_t0001.vtu"
    erg["stromrichtung_falsch"] = richtung_pruefen(vtu, sps)
    erg["fehler_vs_biot_savart"] = vergleiche(vtu, sps, a.breite, a.hoehe, a.rand)
    bild(vtu, sps, a.breite, a.hoehe, a.ordner / "vergleich_linie.png")
    (a.ordner / "ergebnis.json").write_text(json.dumps(erg, indent=2, ensure_ascii=False))
    print(json.dumps(erg["fehler_vs_biot_savart"], indent=1))
    print("FERTIG", a.ordner)


if __name__ == "__main__":
    main()
