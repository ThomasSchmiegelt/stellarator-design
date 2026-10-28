"""haut_festigkeit.py — Haelt die Innenhaut des Kuehlsegments den Kuehlmitteldruck? Elmer, Platte ueber Gyroid-Zellen.

    .venv/bin/python -m stellarator.haut_festigkeit [--zelle 100] [--wand 10] [--dicken 5,10,15] [--n 100] [--streifen]

Modell: Stahlplatte (Innenhaut) der Dicke t ueber 2 x 2 Gyroid-Zellen der Groesse a. Wasserseite oben (z = t), dort
wo die Gyroid-Wand (Dicke w = 2 x halbdicke_vorn) die Haut beruehrt, ist die Platte eingespannt; dazwischen drueckt das
Kuehlmittel mit p nach unten zum Plasma (Vakuum). Wandspur in der Hautebene: |f| / |grad f| < w/2 mit
f = sin X cos Y + sin Y cos Z + sin Z cos X, X = 2 pi x / a (Ebene Z = 0, andere Lagen der Haut mit --phase).
Seiten: Normalverschiebung 0 (Symmetrie). Linear elastisch: gerechnet mit 1 MPa, Spannung waechst proportional mit p.
--streifen: Pruefung mit geraden Lagern im Abstand a/2 - w gegen die Formel sigma = p b^2 / (2 t^2) (beidseitig eingespannt).
Ausgabe sim/haut_festigkeit/: ergebnis.json, haut.png. Naeherungen: Gyroid-Wand starr (Anker gibt nicht nach),
lineare Hexaeder (4 Lagen ueber die Dicke), keine Temperaturspannungen, keine Kerben an den Wandanschluessen.
"""
import argparse, json, shutil, subprocess
from pathlib import Path
import numpy as np

from . import hexmodell as hm
from .lauf import PROJEKT

WURZEL = PROJEKT / "sim" / "haut_festigkeit"
E_STAHL, NU_STAHL = 200e9, 0.3
SIGMA_ZUL = 150e6                    # zulaessige Spannung warmfester Stahl bei 300-500 C, grob [Pa]
DRUECKE = {"Wasser DEMO-WCLL 15,5 MPa": 15.5, "Helium HCPB 8 MPa": 8.0, "Wasser ITER 4 MPa": 4.0, "Blei ~0,5 MPa": 0.5}


def netz(L, t, n, nz=4):
    x = np.linspace(0, L, n + 1); z = np.linspace(0, t, nz + 1)
    I, J, K = np.meshgrid(np.arange(n + 1), np.arange(n + 1), np.arange(nz + 1), indexing="ij")
    X = np.c_[x[I.ravel()], x[J.ravel()], z[K.ravel()]]
    nr = lambda i, j, k: (i * (n + 1) + j) * (nz + 1) + k
    i, j, k = (g.ravel() for g in np.meshgrid(np.arange(n), np.arange(n), np.arange(nz), indexing="ij"))
    hexa = np.stack([nr(i, j, k), nr(i + 1, j, k), nr(i + 1, j + 1, k), nr(i, j + 1, k),
                     nr(i, j, k + 1), nr(i + 1, j, k + 1), nr(i + 1, j + 1, k + 1), nr(i, j + 1, k + 1)], 1)
    return X, hexa


def wandspur(xy, a, w, phase, streifen):
    if streifen:                                               # gerade Lager bei y = 0, a/2, a, ... (Breite w)
        return np.abs((xy[:, 1] + a / 4) % (a / 2) - a / 4) < w / 2
    X, Y, Z = 2 * np.pi * xy[:, 0] / a, 2 * np.pi * xy[:, 1] / a, phase
    f = np.sin(X) * np.cos(Y) + np.sin(Y) * np.cos(Z) + np.sin(Z) * np.cos(X)
    g = np.sqrt((np.cos(X) * np.cos(Y) - np.sin(Z) * np.sin(X)) ** 2 + (np.cos(Y) * np.cos(Z) - np.sin(X) * np.sin(Y)) ** 2
                + (np.cos(Z) * np.cos(X) - np.sin(Y) * np.sin(Z)) ** 2)
    return np.abs(f) / np.maximum(g, 1e-6) * a / (2 * np.pi) < w / 2


def rechne(a, t, w, n, phase, streifen, ordner: Path):
    L = 2 * a
    X, hexa = netz(L, t, n)
    tol = 1e-9 * L
    oben = np.all(np.abs(X[hexa[:, 4:8], 2] - t) < tol, axis=1)
    mitte = X[hexa[:, 4:8]].mean(1)[:, :2]
    fest = oben & wandspur(mitte, a, w, phase, streifen)
    flaechen = [(1, fest, [4, 5, 6, 7]), (2, oben & ~fest, [4, 5, 6, 7])]
    for bc, (ach, wert, lok) in enumerate([(0, 0, [0, 3, 7, 4]), (0, L, [1, 2, 6, 5]), (1, 0, [0, 1, 5, 4]), (1, L, [3, 2, 6, 7])], 3):
        flaechen.append((bc, np.all(np.abs(X[hexa[:, lok], ach] - wert) < tol, axis=1), lok))
    rand = [(bc, e, hexa[e, lok]) for bc, sel, lok in flaechen for e in np.where(sel)[0]]
    m = ordner / "netz"; m.mkdir(parents=True, exist_ok=True)
    Nn, E, R = len(X), len(hexa), len(rand)
    (m / "mesh.header").write_text(f"{Nn} {E} {R}\n2\n808 {E}\n404 {R}\n")
    np.savetxt(m / "mesh.nodes", np.c_[np.arange(1, Nn + 1), -np.ones(Nn), X], fmt="%d %d %.9e %.9e %.9e")
    np.savetxt(m / "mesh.elements", np.c_[np.arange(1, E + 1), np.ones(E, int), np.full(E, 808), hexa + 1], fmt="%d")
    np.savetxt(m / "mesh.boundary", np.array([[r + 1, bc, e + 1, 0, 404, *(q + 1)] for r, (bc, e, q) in enumerate(rand)]), fmt="%d")
    sym = "\n".join(f"Boundary Condition {bc}\n  Target Boundaries(1) = {bc}\n  Displacement {1 if bc < 5 else 2} = Real 0.0\nEnd"
                    for bc in (3, 4, 5, 6))
    (ordner / "case.sif").write_text(f"""Header
  Mesh DB "." "netz"
  Results Directory "erg"
End
Simulation
  Coordinate System = "Cartesian 3D"
  Simulation Type = "Steady State"
  Steady State Max Iterations = 1
  Max Output Level = 3
End
Body 1
  Equation = 1
  Material = 1
End
Material 1
  Youngs Modulus = {E_STAHL:.6e}
  Poisson Ratio = {NU_STAHL}
End
Equation 1
  Active Solvers(1) = 1
End
Solver 1
  Equation = "Stress"
  Procedure = "StressSolve" "StressSolver"
  Variable = -dofs 3 "Displacement"
  Displace Mesh = Logical False
  Linear System Solver = "Direct"
  Linear System Direct Method = "MUMPS"
End
Solver 2
  Exec Solver = After All
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = "haut"
  Vtu Format = Logical True
  Binary Output = Logical True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Displacement 1 = Real 0.0
  Displacement 2 = Real 0.0
  Displacement 3 = Real 0.0
End
Boundary Condition 2
  Target Boundaries(1) = 2
  Normal Force = Real -1.0e6
End
{sym}
""")
    with open(ordner / "solve.log", "w") as f:
        subprocess.run(["ElmerSolver", "case.sif"], cwd=ordner, stdout=f, stderr=subprocess.STDOUT, check=True)
    import pyvista as pv
    g = pv.read(sorted((ordner / "erg").glob("haut*.vtu"))[-1])
    U = np.asarray(g.point_data["displacement"], float)
    # von Mises je Element an den 4 oberen und 4 unteren Ecken (Biegespannung sitzt an der Oberflaeche)
    lam, mu = E_STAHL * NU_STAHL / ((1 + NU_STAHL) * (1 - 2 * NU_STAHL)), E_STAHL / (2 * (1 + NU_STAHL))
    vm = np.zeros(E)
    for xi in hm.ECKEN:
        d = hm.dN(xi)
        G = np.einsum("eki,kj->eij", U[hexa], d) @ np.linalg.inv(np.einsum("eki,kj->eij", X[hexa], d))
        ep = 0.5 * (G + G.transpose(0, 2, 1))
        s = 2 * mu * ep + lam * np.trace(ep, axis1=1, axis2=2)[:, None, None] * np.eye(3)
        dev = s - np.trace(s, axis1=1, axis2=2)[:, None, None] * np.eye(3) / 3
        vm = np.maximum(vm, np.sqrt(1.5 * np.einsum("eij,eij->e", dev, dev)))
    innen = np.all((mitte > a / 2) & (mitte < 3 * a / 2), axis=1)          # Randeinfluss der Symmetrie weglassen
    shutil.rmtree(ordner / "netz"); shutil.rmtree(ordner / "erg")
    return {"sigma_max_Pa_je_MPa": float(vm[innen].max()), "durchbiegung_max_m_je_MPa": float(-U[:, 2].min()),
            "anteil_eingespannt": float(fest.sum() / oben.sum()),
            "_karte": (mitte[oben], vm[oben], fest[oben])}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zelle", type=float, default=100.0, help="Gyroid-Zelle vorn [mm]")
    ap.add_argument("--wand", type=float, default=10.0, help="Gyroid-Wanddicke an der Haut [mm]")
    ap.add_argument("--dicken", default="5,10,15", help="Hautdicken [mm]")
    ap.add_argument("--n", type=int, default=100, help="Elemente je Seite")
    ap.add_argument("--phase", type=float, default=0.0, help="Lage der Hautebene in der Zelle [rad]")
    ap.add_argument("--streifen", action="store_true")
    a = ap.parse_args(argv)
    o = WURZEL / ("streifen" if a.streifen else "gyroid"); o.mkdir(parents=True, exist_ok=True)
    zelle, wand = a.zelle / 1000, a.wand / 1000
    erg, karten = {}, {}
    for t_mm in (float(s) for s in a.dicken.split(",")):
        r = rechne(zelle, t_mm / 1000, wand, a.n, a.phase, a.streifen, o / f"t{t_mm:g}")
        karten[t_mm] = r.pop("_karte")
        b = zelle / 2 - wand
        r["formel_streifen_Pa_je_MPa"] = 1e6 * b ** 2 / (2 * (t_mm / 1000) ** 2)
        r["druck_zulaessig_MPa"] = SIGMA_ZUL / r["sigma_max_Pa_je_MPa"]
        r["sigma_MPa"] = {k: p * r["sigma_max_Pa_je_MPa"] / 1e6 for k, p in DRUECKE.items()}
        erg[f"{t_mm:g} mm"] = r
        print(f"t = {t_mm:4.0f} mm: sigma {r['sigma_max_Pa_je_MPa'] / 1e6:7.1f} MPa je MPa Druck (Streifenformel "
              f"{r['formel_streifen_Pa_je_MPa'] / 1e6:6.1f}), zulaessig bis {r['druck_zulaessig_MPa']:5.2f} MPa, "
              f"eingespannt {r['anteil_eingespannt'] * 100:.0f} %", flush=True)
    (o / "ergebnis.json").write_text(json.dumps({"parameter": vars(a), "sigma_zul_MPa": SIGMA_ZUL / 1e6, "faelle": erg},
                                                indent=1, ensure_ascii=False))
    bild(a, erg, karten, o / "haut.png")


def bild(a, erg, karten, datei):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t0 = min(karten); xy, vm, fest = karten[t0]
    p0 = 15.5
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    sc = ax[0].scatter(xy[:, 0] * 1000, xy[:, 1] * 1000, c=vm * p0 / 1e6, s=6, marker="s", cmap="inferno")
    ax[0].scatter(xy[fest, 0] * 1000, xy[fest, 1] * 1000, c="#2a9fd6", s=6, marker="s")
    ax[0].set_aspect("equal"); ax[0].set_xlabel("x [mm]"); ax[0].set_ylabel("y [mm]")
    ax[0].set_title(f"Haut {t0:g} mm bei {p0} MPa: Vergleichsspannung [MPa]\nblau = Gyroid-Wand (eingespannt)")
    fig.colorbar(sc, ax=ax[0])
    namen = list(DRUECKE); x = np.arange(len(namen))
    for i, (k, r) in enumerate(erg.items()):
        w = [r["sigma_MPa"][n] for n in namen]
        bars = ax[1].bar(x + (i - (len(erg) - 1) / 2) * 0.8 / len(erg), w, 0.8 / len(erg), label=f"Haut {k}")
        ax[1].bar_label(bars, labels=[f"{v:.0f}" for v in w], fontsize=8)
    ax[1].axhline(SIGMA_ZUL / 1e6, color="red", ls="--"); ax[1].text(x[-1] + 0.4, SIGMA_ZUL / 1e6 * 1.1, "zulässig ~150 MPa",
                                                                       ha="right", color="red")
    ax[1].set_yscale("log"); ax[1].set_xticks(x, [n.replace(" ", "\n", 1) for n in namen])
    ax[1].set_ylabel("max. Vergleichsspannung [MPa]"); ax[1].legend()
    ax[1].set_title(f"Gyroid-Zelle {a.zelle:g} mm, Wand {a.wand:g} mm" + (" (Prüffall Streifen)" if a.streifen else ""))
    fig.tight_layout(); fig.savefig(datei, dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
