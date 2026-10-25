"""gitterzelle.py — Gitter-Einheitszelle (PicoGK) -> effektive Steifigkeit (Elmer) -> Kennlinie Dichte -> E.

Stufe 1 des Stuetzgitters fuer die 1-GW-Variante (Stufe 2: verschmierte Gitterfuellung im Hex-Modell).

    .venv/bin/python -m stellarator.gitterzelle [--arten bcc gyroid] [--zelle_mm 10] [--n_zellen 2] [--n_raster 64]

Je Art und Dicke: PicoGK (picogk/GitterZelle) baut den Zellstapel und tastet den Abstand im Raster ab ->
Voxel-Hexaeder (nur die zusammenhaengende Gitterkomponente) -> Elmer StressSolve, einachsiger Druck:
Symmetrie x=0, y=0, z=0, oben Verschiebung -delta, Seiten x=H, y=H frei. Effektiv:
E* = <sigma_zz> / eps mit <sigma_zz> = Summe(sigma_zz,e V_e) / H^3 (Mittel ueber die ganze Zelle),
nu* aus der Querdehnung der freien Seite. Ausgleich Gibson-Ashby E*/E_s = C rho^n.
Ausgabe sim/gitterzelle/: kennlinie.json, kennlinie.png, je Fall zelle.stl + ergebnis.json.
Naeherungen: Symmetrie- statt periodischer Randbedingungen, Voxel-Treppen an der Oberflaeche.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, time
from pathlib import Path
import numpy as np

from . import hexmodell as hm
from .lauf import PROJEKT

APP = PROJEKT / "picogk" / "GitterZelle"
BIN = APP / "bin" / "Release" / "net9.0" / "GitterZelle"
WURZEL = PROJEKT / "sim" / "gitterzelle"
E_STAHL, NU_STAHL = 200e9, 0.3
DICKEN = {"bcc": [0.5, 0.7, 0.9, 1.2, 1.6, 2.0], "gyroid": [0.25, 0.4, 0.6, 0.8, 0.95]}   # ab ~1,1 mm schliesst sich die Schale
ENV = os.environ | {"DOTNET_ROOT": str(Path.home() / ".dotnet"), "PATH": f"{Path.home() / '.dotnet'}:{os.environ['PATH']}"}


def picogk(art: str, zelle_mm: float, n_zellen: int, dicke_mm: float, n_raster: int, ordner: Path) -> tuple[np.ndarray, dict]:
    if not BIN.exists():
        subprocess.run(["dotnet", "build", "-c", "Release", "-v", "q"], cwd=APP, env=ENV, check=True, capture_output=True)
    ordner.mkdir(parents=True, exist_ok=True)
    auftrag = {"art": art, "zelle_mm": zelle_mm, "n_zellen": n_zellen, "dicke_mm": dicke_mm,
               "voxel_mm": zelle_mm / 100, "n_raster": n_raster, "ausgabe": str(ordner)}
    (ordner / "auftrag.json").write_text(json.dumps(auftrag, indent=1))
    r = subprocess.run([str(BIN), str(ordner / "auftrag.json")], env=ENV, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"PicoGK fehlgeschlagen:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    d = np.fromfile(ordner / "abstand.f32", np.float32).reshape(n_raster, n_raster, n_raster)
    return d <= 0, json.loads((ordner / "ergebnis.json").read_text())


def voxelnetz(fest: np.ndarray, h: float):
    """Feste Voxel (groesste 6-zusammenhaengende Komponente) -> Knoten, Hexaeder (Elmer-Reihenfolge)."""
    from scipy import ndimage
    lab, n = ndimage.label(fest)
    if n > 1:
        groesse = np.bincount(lab.ravel()); groesse[0] = 0
        fest = lab == groesse.argmax()
    n_ = fest.shape[0]
    i, j, k = np.nonzero(fest)
    ecken = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
    flach = lambda a, b, c: (a * (n_ + 1) + b) * (n_ + 1) + c
    hexa_g = np.stack([flach(i + e[0], j + e[1], k + e[2]) for e in ecken], 1)
    benutzt, hexa = np.unique(hexa_g, return_inverse=True)
    hexa = hexa.reshape(-1, 8)
    a = benutzt // ((n_ + 1) ** 2); b = (benutzt // (n_ + 1)) % (n_ + 1); c = benutzt % (n_ + 1)
    X = np.c_[a, b, c] * h
    return X, hexa, fest


def rechne(X, hexa, H: float, ordner: Path, eps: float = 1e-3) -> dict:
    """Einachsiger Druckversuch in Elmer, Rueckgabe E*, nu*."""
    m = ordner / "netz"; m.mkdir(parents=True, exist_ok=True)
    tol = 1e-9 * H
    # Randflaechen: Elementflaechen, deren 4 Knoten alle auf der jeweiligen Ebene liegen
    flaechen = {"x0": (0, [0, 3, 7, 4]), "y0": (1, [0, 1, 5, 4]), "z0": (2, [0, 1, 2, 3]), "zH": (2, [4, 5, 6, 7])}
    rand = []
    for bc, (name, (ach, lok)) in enumerate(flaechen.items(), 1):
        wert = H if name.endswith("H") else 0.0
        sel = np.all(np.abs(X[hexa[:, lok], ach] - wert) < tol, axis=1)
        for e in np.where(sel)[0]:
            rand.append((bc, e, hexa[e, lok]))
    Nn, E, L = len(X), len(hexa), len(rand)
    (m / "mesh.header").write_text(f"{Nn} {E} {L}\n2\n808 {E}\n404 {L}\n")
    np.savetxt(m / "mesh.nodes", np.c_[np.arange(1, Nn + 1), -np.ones(Nn), X], fmt="%d %d %.9e %.9e %.9e")
    np.savetxt(m / "mesh.elements", np.c_[np.arange(1, E + 1), np.ones(E, int), np.full(E, 808), hexa + 1], fmt="%d")
    np.savetxt(m / "mesh.boundary", np.array([[r + 1, bc, e + 1, 0, 404, *(q + 1)] for r, (bc, e, q) in enumerate(rand)]), fmt="%d")
    delta = eps * H
    sif = f"""Header
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
  Output File Name = "zelle"
  Vtu Format = Logical True
  Binary Output = Logical True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Displacement 1 = Real 0.0
End
Boundary Condition 2
  Target Boundaries(1) = 2
  Displacement 2 = Real 0.0
End
Boundary Condition 3
  Target Boundaries(1) = 3
  Displacement 3 = Real 0.0
End
Boundary Condition 4
  Target Boundaries(1) = 4
  Displacement 3 = Real {-delta:.9e}
End
"""
    (ordner / "case.sif").write_text(sif)
    mi = {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}
    bedarf = 1e-4 * len(hexa)                                  # gemessen ~10 GB je 1e5 Elemente (MUMPS)
    if bedarf > 0.7 * mi["MemAvailable"]:
        raise RuntimeError(f"Elmer braucht ~{bedarf:.0f} GB, frei {mi['MemAvailable']:.0f} GB -> spaeter rechnen")
    t0 = time.time()
    with open(ordner / "solve.log", "w") as f:
        p = subprocess.Popen(["ElmerSolver", "case.sif"], cwd=ordner, stdout=f, stderr=subprocess.STDOUT)
        try:
            if p.wait() != 0:
                raise subprocess.CalledProcessError(p.returncode, "ElmerSolver")
        finally:
            if p.poll() is None:                               # Abbruch von aussen: Elmer nicht verwaist lassen
                p.kill()
    t_elmer = time.time() - t0
    import pyvista as pv
    g = pv.read(sorted((ordner / "erg").glob("zelle*.vtu"))[-1])
    if np.abs(g.points - X).max() > 1e-6 * H:
        raise RuntimeError("Knotenreihenfolge der Elmer-Ausgabe passt nicht")
    U = np.asarray(g.point_data["displacement"], float)
    d = hm.dN([0, 0, 0])
    J = np.einsum("eki,kj->eij", X[hexa], d)
    G = np.einsum("eki,kj->eij", U[hexa], d) @ np.linalg.inv(J)
    epsil = 0.5 * (G + G.transpose(0, 2, 1))
    lam, mu = E_STAHL * NU_STAHL / ((1 + NU_STAHL) * (1 - 2 * NU_STAHL)), E_STAHL / (2 * (1 + NU_STAHL))
    sig_zz = 2 * mu * epsil[:, 2, 2] + lam * np.trace(epsil, axis1=1, axis2=2)
    V = hm.elementvolumen(X, hexa)
    s_mittel = (sig_zz * V).sum() / H ** 3
    seite = np.abs(X[:, 0] - H) < tol
    quer = U[seite, 0].mean() / H if seite.any() else np.nan
    shutil.rmtree(ordner / "netz"); shutil.rmtree(ordner / "erg")
    return {"E_eff_Pa": float(-s_mittel / eps), "nu_eff": float(-quer / -eps) if np.isfinite(quer) else None,
            "knoten": int(Nn), "elemente": int(E), "t_elmer_s": t_elmer}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arten", nargs="*", default=["bcc", "gyroid"])
    ap.add_argument("--zelle_mm", type=float, default=10.0)
    ap.add_argument("--n_zellen", type=int, default=2)
    ap.add_argument("--n_raster", type=int, default=64)
    a = ap.parse_args(argv)
    import signal, sys
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))     # kill -> finally beendet auch Elmer
    WURZEL.mkdir(parents=True, exist_ok=True)
    H = a.zelle_mm * a.n_zellen / 1000
    erg = {"zelle_mm": a.zelle_mm, "n_zellen": a.n_zellen, "n_raster": a.n_raster, "E_s_Pa": E_STAHL, "arten": {}}
    for art in a.arten:
        reihe = []
        for dk in DICKEN[art]:
            o = WURZEL / f"{art}_{dk:.2f}"
            if (o / "ergebnis_fem.json").exists():                 # schon gerechnet (Neustart)
                reihe.append(json.loads((o / "ergebnis_fem.json").read_text())); continue
            fest, info = picogk(art, a.zelle_mm, a.n_zellen, dk, a.n_raster, o)
            X, hexa, fest = voxelnetz(fest, H / a.n_raster)
            r = rechne(X, hexa, H, o)
            r |= {"dicke_mm": dk, "rho_picogk": info["volumenanteil"], "rho_voxel": float(fest.mean())}
            (o / "ergebnis_fem.json").write_text(json.dumps(r, indent=1))
            print(f"{art} dicke {dk} mm: rho {r['rho_voxel']:.3f}, E*/Es {r['E_eff_Pa'] / E_STAHL:.4f}, "
                  f"nu* {r['nu_eff']:.3f}, {r['elemente']} Elemente, {r['t_elmer_s']:.0f} s", flush=True)
            reihe.append(r)
        rho = np.array([r["rho_voxel"] for r in reihe]); e = np.array([r["E_eff_Pa"] / E_STAHL for r in reihe])
        n_, lnC = np.polyfit(np.log(rho), np.log(e), 1)
        erg["arten"][art] = {"proben": reihe, "gibson_ashby": {"C": float(np.exp(lnC)), "n": float(n_)}}
        print(f"{art}: E*/Es = {np.exp(lnC):.3f} rho^{n_:.2f}", flush=True)
    (WURZEL / "kennlinie.json").write_text(json.dumps(erg, indent=1))
    bild(erg)


def bild(erg: dict) -> None:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    r = np.linspace(0.05, 0.7, 100)
    for (art, d), f in zip(erg["arten"].items(), ("C0", "C1")):
        rho = [p["rho_voxel"] for p in d["proben"]]; e = [p["E_eff_Pa"] / 1e9 for p in d["proben"]]
        ga = d["gibson_ashby"]
        ax.plot(rho, e, "o", color=f, label=f"{art} (Elmer)")
        ax.plot(r, ga["C"] * r ** ga["n"] * erg["E_s_Pa"] / 1e9, "-", color=f, lw=1,
                label=f"{art}: E*/E_s = {ga['C']:.2f} rho^{ga['n']:.2f}")
    ax.set_xlabel("Volumenanteil Stahl rho [-]"); ax.set_ylabel("effektiver E-Modul [GPa]")
    ax.set_title("Gitter-Einheitszelle (PicoGK + Elmer), Stahl E_s = 200 GPa", fontsize=10)
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(WURZEL / "kennlinie.png", dpi=140); plt.close(fig)


if __name__ == "__main__":
    main()


def bild_zellen(arten=("gyroid", "bcc")) -> Path:
    """Galerie der PicoGK-Zellen (STL) je Art und Dicke, beschriftet mit Dichte und E*/E_s."""
    import pyvista as pv
    faelle = [(art, o) for art in arten for o in sorted(WURZEL.glob(f"{art}_*")) if (o / "zelle.stl").exists()]
    spalten = max(sum(1 for a, _ in faelle if a == art) for art in arten)
    pl = pv.Plotter(off_screen=True, shape=(len(arten), spalten), window_size=(380 * spalten, 400 * len(arten)), border=False)
    for z, art in enumerate(arten):
        for s, (_, o) in enumerate([f for f in faelle if f[0] == art]):
            pl.subplot(z, s)
            m = pv.read(o / "zelle.stl").decimate(0.9)
            pl.add_mesh(m, color="#b8bcc4" if art == "bcc" else "#d9a05b", smooth_shading=True, specular=0.4)
            fem = o / "ergebnis_fem.json"
            r = json.loads(fem.read_text()) if fem.exists() else {}
            txt = f"{art} {o.name.split('_')[1]} mm"
            if r:
                txt += f"\nrho {r['rho_voxel']:.2f}  E*/Es {r['E_eff_Pa'] / E_STAHL:.3f}"
            pl.add_text(txt, font_size=9)
            pl.view_isometric(); pl.camera.zoom(1.15)
    pfad = WURZEL / "zellen_galerie.png"
    pl.screenshot(pfad); pl.close()
    return pfad
