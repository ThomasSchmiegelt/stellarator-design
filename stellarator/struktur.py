"""struktur.py — Stuetzstruktur der Spulen: Lorentzkraefte -> Spannungen (ElmerFEM, ein Lauf).

Konzept (v1): durchgehende Stuetzschale aus Stahl, in die alle Wickelpakete eingebettet sind
(Spulen "in Nuten" einer Schale, wie in Kraftwerksstudien vorgeschlagen). Die Schalenmitte ist
die Wicklungsflaeche durch alle Spulenmittellinien (periodischer Spline zwischen den Spulen),
Dicke = Wickelpaketbreite + 2 x Deckung. Ports/Oeffnungen fehlen noch.

Ein Elmer-Lauf: CoilSolver -> WhitneyAV (B in Luft, Schale, Wickelpaket) -> Felder ->
StressSolver mit Volumenlast J x B im Wickelpaket (MATC aus den Knotenfeldern). Lagerung
statisch bestimmt (3-2-1 an drei Schalenknoten): die Lorentzkraefte sind in sich im
Gleichgewicht, die Lagerkraefte muessen ~0 sein (Kontrolle).

    .venv/bin/python -m stellarator.struktur stellarator/faelle/qa_nfp2_1GW_HTS.json
        [--deckung 0.3 --h_wp 0.2 --h_schale 0.35 --h_luft 3 --rand 15] [--nur_netz] [--nur_auswerten]

Voraussetzung: bewerte auf denselben Fall (Kalibrierfaktor aus kennzahlen.json).
Ausgabe sim/stellarator/struktur/<fall>/: netz/, case.sif, erg/struktur_t0001.vtu,
ergebnis.json (Spannungen je Bauteil, Verformung, Kraefte Elmer vs. Biot-Savart, Masse),
struktur.png.
"""
from __future__ import annotations
import argparse, json, re, subprocess, time
from pathlib import Path
import numpy as np
import gmsh

from . import spulen as sp, cad, elmer
from .lauf import PROJEKT

STAHL = {"E_Pa": 200e9, "nu": 0.3, "rho_kg_m3": 7900, "zul_MPa": 667}   # 316LN bei 4 K, 2/3 R_p0,2
WP = {"E_Pa": 100e9, "nu": 0.3, "rho_kg_m3": 7000}                       # verschmiert (Leiter, Cu, Stahl, Isolation)


def wicklungsflaeche(spulen, n_th: int, n_ph: int) -> np.ndarray:
    """Flaeche X(theta, phi) (n_th, n_ph, 3), die alle Spulenmittellinien enthaelt.

    Je Spule: poloidaler Winkel um den Schwerpunkt in (R, Z); R, Z und phi-Abweichung auf ein
    gemeinsames theta-Raster. Zwischen den Spulen periodischer kubischer Spline in phi.
    """
    from scipy.interpolate import CubicSpline
    th = np.linspace(0, 2 * np.pi, n_th, endpoint=False)
    reihen = []
    for s in spulen:
        R, Z = np.hypot(s.punkte[:, 0], s.punkte[:, 1]), s.punkte[:, 2]
        ph = np.arctan2(s.punkte[:, 1], s.punkte[:, 0])
        phc = np.angle(np.exp(1j * ph).mean())
        dph = np.angle(np.exp(1j * (ph - phc)))
        t = np.unwrap(np.arctan2(Z - Z.mean(), R - R.mean()))
        if t[-1] < t[0]:
            t, R, Z, dph = t[::-1], R[::-1], Z[::-1], dph[::-1]
        if np.any(np.diff(t) <= 0):
            raise ValueError(f"{s.name}: poloidaler Winkel nicht monoton, Wicklungsflaeche so nicht moeglich")
        t0 = t[0]; tt = np.r_[t, t0 + 2 * np.pi]
        werte = [np.r_[v, v[0]] for v in (R, Z, dph)]
        x = (th - t0) % (2 * np.pi) + t0
        reihen.append((phc, [CubicSpline(tt, v, bc_type="periodic")(x) for v in werte]))
    reihen.sort(key=lambda r: r[0])
    phc = np.array([r[0] for r in reihen]); phc = np.unwrap(phc)
    W = np.array([np.stack(r[1]) for r in reihen])                         # (n_spulen, 3, n_th)
    ph = np.linspace(phc[0], phc[0] + 2 * np.pi, n_ph, endpoint=False)
    f = CubicSpline(np.r_[phc, phc[0] + 2 * np.pi], np.concatenate([W, W[:1]]), bc_type="periodic", axis=0)(ph)
    R, Z, dph = f[:, 0].T, f[:, 1].T, f[:, 2].T                            # (n_th, n_ph)
    P = ph[None, :] + dph
    return np.stack([R * np.cos(P), R * np.sin(P), Z], -1)


def normalen(X) -> np.ndarray:
    """Einheitsnormale der periodischen Gitterflaeche, nach aussen (weg von der Torusseele)."""
    Xt = np.roll(X, -1, 0) - np.roll(X, 1, 0); Xp = np.roll(X, -1, 1) - np.roll(X, 1, 1)
    n = np.cross(Xt, Xp); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    seele = X.mean(0, keepdims=True)                                         # Mittel ueber theta je phi
    if np.mean(np.sum(n * (X - seele), -1)) < 0:
        n = -n
    return n


def torus_netz(X) -> tuple[np.ndarray, np.ndarray]:
    """Periodisches Gitter -> (knoten, dreiecke), geschlossen, Normalen nach aussen."""
    n_th, n_ph = X.shape[:2]
    i, j = np.meshgrid(np.arange(n_th), np.arange(n_ph), indexing="ij")
    a, b, c, d = i * n_ph + j, ((i + 1) % n_th) * n_ph + j, ((i + 1) % n_th) * n_ph + (j + 1) % n_ph, i * n_ph + (j + 1) % n_ph
    tri = np.concatenate([np.stack([a, b, c], -1).reshape(-1, 3), np.stack([a, c, d], -1).reshape(-1, 3)])
    kn = X.reshape(-1, 3); P = kn[tri]
    vol = np.einsum("ij,ij->i", P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6
    return kn, (tri if vol > 0 else tri[:, ::-1])


def deckung(spulen, breite, hoehe, X, n, dicke) -> float:
    """Kleinster Abstand der Wickelpaket-Ecken zur Schalenoberflaeche (normal zur Mittelflaeche)."""
    from scipy.spatial import cKDTree
    baum = cKDTree(X.reshape(-1, 3)); nn = n.reshape(-1, 3); Xf = X.reshape(-1, 3)
    m = np.inf
    for s in spulen:
        ecken = sp.rohr_dreiecke(s, breite, hoehe).reshape(-1, 3)
        _, k = baum.query(ecken)
        m = min(m, dicke / 2 - np.abs(np.sum((ecken - Xf[k]) * nn[k], 1)).max())
    return float(m)


def netz(spulen, breite, hoehe, ordner: Path, dicke: float, rand_m: float, h_wp: float, h_schale: float,
         h_luft: float, dist_max: float) -> dict:
    """Wickelpakete (Body 1..n) in Stuetzschale (n+1), Luft innen (n+2) und aussen (n+3), Quader (Bnd 1).
    Diskrete Flaechen ohne Boolesche Operationen (wie cad.elmer_netz)."""
    ordner.mkdir(parents=True, exist_ok=True)
    umfang_pol = max(np.linalg.norm(np.diff(s.punkte, axis=0), axis=1).sum() for s in spulen)
    R_mittel = np.mean([np.hypot(*s.punkte[:, :2].T).mean() for s in spulen])
    n_th = int(np.ceil(umfang_pol / h_schale)); n_ph = int(np.ceil(2 * np.pi * R_mittel * 1.2 / h_schale))
    X = wicklungsflaeche(spulen, n_th, n_ph); nv = normalen(X)
    dk = deckung(spulen, breite, hoehe, X, nv, dicke)
    if dk < 0.05:
        raise SystemExit(f"ABBRUCH: Wickelpaket ragt aus der Schale (Deckung {dk:.3f} m) -> --deckung erhoehen")
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 1)
    try:
        t0 = time.time(); m = gmsh.model; geo = m.geo
        versatz = [1]

        def diskret(kn, tri):
            f = m.addDiscreteEntity(2)
            m.mesh.addNodes(2, f, np.arange(versatz[0], versatz[0] + len(kn)), kn.ravel())
            m.mesh.addElementsByType(f, 2, [], (tri + versatz[0]).ravel())
            versatz[0] += len(kn)
            return f
        f_wp = [diskret(*cad.rohr_netz(s, breite, hoehe, h_wp)) for s in spulen]
        f_in = diskret(*torus_netz(X - dicke / 2 * nv))
        f_aus = diskret(*torus_netz(X + dicke / 2 * nv))
        P = X.reshape(-1, 3); lo, hi = P.min(0) - rand_m, P.max(0) + rand_m
        pk = [geo.addPoint(x, y, z, h_luft) for z in (lo[2], hi[2]) for y in (lo[1], hi[1]) for x in (lo[0], hi[0])]
        L = lambda a, b: geo.addLine(pk[a], pk[b])
        e = {k: L(*k) for k in [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]}

        def seite(a, b, c, d):
            kanten = [(a, b), (b, c), (c, d), (d, a)]
            return geo.addPlaneSurface([geo.addCurveLoop([e[k] if k in e else -e[k[::-1]] for k in kanten])])
        box = [seite(0, 1, 3, 2), seite(4, 6, 7, 5), seite(0, 4, 5, 1), seite(2, 3, 7, 6), seite(0, 2, 6, 4), seite(1, 5, 7, 3)]
        sl_wp = [geo.addSurfaceLoop([f]) for f in f_wp]
        sl_in, sl_aus = geo.addSurfaceLoop([f_in]), geo.addSurfaceLoop([f_aus])
        v_wp = [geo.addVolume([s_]) for s_ in sl_wp]
        v_schale = geo.addVolume([sl_aus, sl_in] + sl_wp)
        v_innen = geo.addVolume([sl_in])
        v_aussen = geo.addVolume([geo.addSurfaceLoop(box), sl_aus])
        geo.synchronize()
        n = len(spulen)
        for i, v in enumerate(v_wp):
            m.addPhysicalGroup(3, [v], i + 1, name=spulen[i].name)
        m.addPhysicalGroup(3, [v_schale], n + 1, name="schale")
        m.addPhysicalGroup(3, [v_innen], n + 2, name="luft_innen")
        m.addPhysicalGroup(3, [v_aussen], n + 3, name="luft_aussen")
        m.addPhysicalGroup(2, box, 1, name="aussen")
        felder = []
        for fl, h in ((f_wp, h_wp), ([f_in, f_aus], h_schale)):
            f1 = m.mesh.field.add("Distance"); m.mesh.field.setNumbers(f1, "SurfacesList", fl)
            f2 = m.mesh.field.add("Threshold"); m.mesh.field.setNumber(f2, "InField", f1)
            for k, v in {"SizeMin": h, "SizeMax": h_luft, "DistMin": dicke / 2 if h == h_schale else 0.0,
                         "DistMax": dist_max}.items():
                m.mesh.field.setNumber(f2, k, v)
            felder.append(f2)
        fmin = m.mesh.field.add("Min"); m.mesh.field.setNumbers(fmin, "FieldsList", felder)
        m.mesh.field.setAsBackgroundMesh(fmin)
        for k in ("MeshSizeExtendFromBoundary", "MeshSizeFromPoints", "MeshSizeFromCurvature"):
            gmsh.option.setNumber(f"Mesh.{k}", 0)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        m.mesh.generate(3)
        typen, tags, _ = m.mesh.getElements(3)
        n_tet = sum(len(x) for x in tags)
        gmsh.write(str(ordner / "netz.msh"))
        t_netz = time.time() - t0
    finally:
        gmsh.finalize()
    subprocess.run(["ElmerGrid", "14", "2", "netz.msh", "-autoclean"], cwd=ordner, check=True, capture_output=True)
    (ordner / "netz.msh").unlink()
    np.savez_compressed(ordner / "flaeche.npz", X=X, n=nv)
    return {"n_tet": n_tet, "t_netz_s": t_netz, "deckung_min_m": dk, "dicke_m": dicke,
            "schale_n_theta_phi": [n_th, n_ph], "bodies": {"wickelpakete": [1, n], "schale": n + 1,
                                                           "luft_innen": n + 2, "luft_aussen": n + 3}}


def lagerknoten(ordner: Path, body_schale: int) -> list[int]:
    """Drei Schalenknoten fuer statisch bestimmte Lagerung: phi = 0 (fest), pi (y, z), pi/2 (z)."""
    kn = np.loadtxt(ordner / "netz" / "mesh.nodes")                         # id, part, x, y, z
    ids = set()
    with open(ordner / "netz" / "mesh.elements") as f:
        for z in f:
            w = z.split()
            if int(w[1]) == body_schale:
                ids.update(map(int, w[3:]))
    sel = kn[np.isin(kn[:, 0].astype(int), list(ids))]
    ph = np.arctan2(sel[:, 3], sel[:, 2]); R = np.hypot(sel[:, 2], sel[:, 3])
    out = []
    for ziel in (0.0, np.pi, np.pi / 2):                                    # aeusserster Knoten nahe phi
        d = np.abs(np.angle(np.exp(1j * (ph - ziel))))
        kand = np.where(d < d.min() + 0.01)[0]
        out.append(int(sel[kand[np.argmax(R[kand])], 0]))
    return out


def schreibe_sif(spulen, breite, hoehe, ordner: Path, lager: list[int]) -> None:
    n = len(spulen)
    loeser = re.search(r"(Solver 1\n.*?)Solver 4\n", elmer.KOPF, re.S).group(1)
    kopf = elmer.KOPF.split("Material 1")[0]
    jxb = {1: ('"CoilCurrent 2", "CoilCurrent 3", "Magnetic Flux Density 2", "Magnetic Flux Density 3"', "tx(0)*tx(3)-tx(1)*tx(2)"),
           2: ('"CoilCurrent 3", "CoilCurrent 1", "Magnetic Flux Density 1", "Magnetic Flux Density 3"', "tx(0)*tx(2)-tx(1)*tx(3)"),
           3: ('"CoilCurrent 1", "CoilCurrent 2", "Magnetic Flux Density 1", "Magnetic Flux Density 2"', "tx(0)*tx(3)-tx(1)*tx(2)")}
    last = "".join(f'  Stress Bodyforce {i} = Variable {v}\n    Real MATC "{f}"\n' for i, (v, f) in jxb.items())
    S = [kopf,
         f"Material 1\n  Name = \"wickelpaket\"\n  Relative Permeability = 1.0\n  Electric Conductivity = 1.0\n"
         f"  Youngs Modulus = {WP['E_Pa']:.4e}\n  Poisson Ratio = {WP['nu']}\n  Density = {WP['rho_kg_m3']}\nEnd\n",
         f"Material 2\n  Name = \"stahl\"\n  Relative Permeability = 1.0\n  Electric Conductivity = 1.0\n"
         f"  Youngs Modulus = {STAHL['E_Pa']:.4e}\n  Poisson Ratio = {STAHL['nu']}\n  Density = {STAHL['rho_kg_m3']}\nEnd\n",
         "Material 3\n  Name = \"luft\"\n  Relative Permeability = 1.0\n  Electric Conductivity = 1.0\nEnd\n",
         "Equation 1\n  Active Solvers(4) = 1 2 3 4\nEnd\nEquation 2\n  Active Solvers(3) = 2 3 4\nEnd\n"
         "Equation 3\n  Active Solvers(2) = 2 3\nEnd\n",
         loeser,
         """Solver 4
  Equation = "Stress"
  Procedure = "StressSolve" "StressSolver"
  Variable = -dofs 3 "Displacement"
  Calculate Stresses = Logical True
  Displace Mesh = Logical False
  Linear System Solver = "Iterative"
  Linear System Iterative Method = "GCR"
  Linear System GCR Restart = 200
  Linear System Preconditioning = ILU1
  Linear System Max Iterations = 5000
  Linear System Convergence Tolerance = 1e-8
  Linear System Abort Not Converged = False
  Linear System Residual Output = 100
End
Solver 5
  Exec Solver = After All
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = "struktur"
  Vtu Format = Logical True
  Save Geometry Ids = Logical True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  AV {e} = Real 0.0
End
"""]
    S += elmer.spulen_bloecke(spulen, breite, hoehe, gleichung=1, gleichung_stromlos=1, material=1, kraft_zusatz=last)
    S.append(f'Body {n + 1}\n  Name = "schale"\n  Equation = 2\n  Material = 2\nEnd\n')
    S.append(f'Body {n + 2}\n  Name = "luft_innen"\n  Equation = 3\n  Material = 3\nEnd\n')
    S.append(f'Body {n + 3}\n  Name = "luft_aussen"\n  Equation = 3\n  Material = 3\nEnd\n')
    for k, (knoten, fest) in enumerate(zip(lager, ((1, 2, 3), (2, 3), (3,))), 2):
        S.append(f"Boundary Condition {k}\n  Target Nodes(1) = {knoten}\n"
                 + "".join(f"  Displacement {c} = Real 0.0\n" for c in fest) + "End\n")
    (ordner / "case.sif").write_text("".join(S))


def auswerten(ordner: Path, spulen, breite, hoehe, kz: dict) -> dict:
    import pyvista as pv
    m = pv.read(ordner / "erg" / "struktur_t0001.vtu")
    gid = m.cell_data["GeometryIds"]; n = len(spulen)
    vm = m.point_data["vonmises"] / 1e6; u = np.linalg.norm(m.point_data["displacement"], axis=1)
    erg = {}
    for name, sel in (("wickelpakete", gid <= n), ("schale", gid == n + 1)):
        teil = m.extract_cells(np.where(sel)[0])
        v = teil.point_data["vonmises"] / 1e6
        vol = float(teil.compute_cell_sizes(length=False, area=False)["Volume"].sum())
        erg[name] = {"vonmises_max_MPa": float(v.max()), "vonmises_p99_MPa": float(np.percentile(v, 99)),
                     "vonmises_mittel_MPa": float(v.mean()), "volumen_m3": vol,
                     "u_max_m": float(np.linalg.norm(teil.point_data["displacement"], axis=1).max())}
    erg["schale"]["masse_t"] = erg["schale"]["volumen_m3"] * STAHL["rho_kg_m3"] / 1e3
    erg["schale"]["zulaessig_MPa"] = STAHL["zul_MPa"]
    # Lorentzkraft je Spule aus Elmer (J x B, Zellmittel x Volumen) gegen Biot-Savart (bewerte)
    wp = m.extract_cells(np.where(gid <= n)[0]).cell_data_to_point_data()
    c = wp.point_data_to_cell_data()
    f = np.cross(c.cell_data["coilcurrent"], c.cell_data["magnetic flux density"])
    V = c.compute_cell_sizes(length=False, area=False)["Volume"]
    g = c.cell_data["GeometryIds"]
    F = np.array([(f[g == i + 1] * V[g == i + 1, None]).sum(0) for i in range(n)]) / 1e6
    erg["kraft_elmer_MN_je_spule"] = {s.name: float(np.linalg.norm(F[i])) for i, s in enumerate(spulen)}
    erg["kraft_summe_MN"] = float(np.linalg.norm(F.sum(0)))
    erg["kraft_biot_savart_MN_je_typ"] = kz["spulen"]["F_netto_MN_max_je_typ"]
    erg["u_max_m"] = float(u.max()); erg["vonmises_max_MPa"] = float(vm.max())
    return erg


def bild(ordner: Path, n: int, erg: dict) -> None:
    import pyvista as pv
    m = pv.read(ordner / "erg" / "struktur_t0001.vtu")
    gid = m.cell_data["GeometryIds"]
    sch = m.extract_cells(np.where(gid == n + 1)[0]).extract_surface()
    wp = m.extract_cells(np.where(gid <= n)[0]).extract_surface()
    for t in (sch, wp):
        t["vonMises_MPa"] = t.point_data["vonmises"] / 1e6
    halb = sch.clip(normal=(0, -1, 0), origin=(0, 0, 0))
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1000), shape=(1, 2)); pl.set_background("white")
    clim = [0, max(np.percentile(sch["vonMises_MPa"], 99.5), np.percentile(wp["vonMises_MPa"], 99.5))]
    sb = {"title": "von Mises [MPa]", "color": "black"}
    pl.subplot(0, 0)
    pl.add_mesh(halb, scalars="vonMises_MPa", cmap="turbo", clim=clim, scalar_bar_args=sb)
    pl.add_mesh(wp.clip(normal=(0, -1, 0), origin=(0, 0, 0)), scalars="vonMises_MPa", cmap="turbo", clim=clim, show_scalar_bar=False)
    pl.add_text(f"Stuetzschale (Schnitt): max {erg['schale']['vonmises_max_MPa']:.0f} MPa, "
                f"99 % < {erg['schale']['vonmises_p99_MPa']:.0f} MPa", font_size=10, color="black")
    pl.view_isometric(); pl.camera.zoom(1.3)
    pl.subplot(0, 1)
    pl.add_mesh(wp, scalars="vonMises_MPa", cmap="turbo", clim=clim, show_scalar_bar=False)
    pl.add_text(f"Wickelpakete: max {erg['wickelpakete']['vonmises_max_MPa']:.0f} MPa, "
                f"Verformung max {1e3 * erg['u_max_m']:.0f} mm", font_size=10, color="black")
    pl.view_isometric(); pl.camera.zoom(1.3)
    pl.screenshot(ordner / "struktur.png"); pl.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stuetzschale + Wickelpakete: Lorentzkraft -> Spannung (Elmer)")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--deckung", type=float, default=0.3, help="Stahl ueber/unter dem Wickelpaket (m)")
    ap.add_argument("--h_wp", type=float, default=0.2)
    ap.add_argument("--h_schale", type=float, default=0.35)
    ap.add_argument("--h_luft", type=float, default=3.0)
    ap.add_argument("--dist_max", type=float, default=8.0)
    ap.add_argument("--rand", type=float, default=15.0)
    ap.add_argument("--n_punkte", type=int, default=160)
    ap.add_argument("--nur_netz", action="store_true")
    ap.add_argument("--nur_auswerten", action="store_true")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text()); c = fall["spulen"]
    kz_pfad = PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"] / "kennzahlen.json"
    if not kz_pfad.exists():
        raise SystemExit(f"zuerst: .venv/bin/python -m stellarator.bewerte {a.fall}")
    kz = json.loads(kz_pfad.read_text())
    spulen, geo = sp.lade_spulensatz(c, n_punkte=a.n_punkte)
    for s in spulen:
        s.strom *= kz["strom"]["kalibrierfaktor"]
    b, h = c["wickel_breite_m"], c["wickel_hoehe_m"]
    ordner = PROJEKT / "sim" / "stellarator" / "struktur" / fall["name"]; ordner.mkdir(parents=True, exist_ok=True)
    erg_pfad = ordner / "ergebnis.json"
    erg = json.loads(erg_pfad.read_text()) if erg_pfad.exists() else {}
    erg |= {"fall": fall["name"], "parameter": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()},
            "material": {"stahl": STAHL, "wickelpaket": WP}}
    if not a.nur_auswerten:
        erg["netz"] = netz(spulen, b, h, ordner, dicke=b + 2 * a.deckung, rand_m=a.rand, h_wp=a.h_wp,
                           h_schale=a.h_schale, h_luft=a.h_luft, dist_max=a.dist_max)
        lager = lagerknoten(ordner, len(spulen) + 1)
        schreibe_sif(spulen, b, h, ordner, lager)
        erg["lagerknoten"] = lager
        bedarf = erg["netz"]["n_tet"] * elmer.KB_PRO_TET * 1.3 / 1e6        # + Elastizitaet
        frei = int(next(l for l in open("/proc/meminfo") if l.startswith("MemAvailable")).split()[1]) / 1e6
        erg["ram_schaetzung_GB"] = {"bedarf": bedarf, "frei": frei}
        erg_pfad.write_text(json.dumps(erg, indent=2, ensure_ascii=False))
        print("NETZ", json.dumps(erg["netz"]), erg["ram_schaetzung_GB"], flush=True)
        if a.nur_netz:
            return
        if bedarf > 0.85 * frei:
            raise SystemExit(f"ABBRUCH: Elmer braucht ~{bedarf:.1f} GB, frei {frei:.1f} GB -> h_* groesser")
        t0 = time.time()
        with open(ordner / "solve.log", "w") as f:
            subprocess.run(["ElmerSolver", "case.sif"], cwd=ordner, stdout=f, stderr=subprocess.STDOUT, check=True)
        erg["t_elmer_s"] = time.time() - t0
    erg["ergebnis"] = auswerten(ordner, spulen, b, h, kz)
    erg_pfad.write_text(json.dumps(erg, indent=2, ensure_ascii=False))
    bild(ordner, len(spulen), erg["ergebnis"])
    print("FERTIG", ordner, json.dumps({k: erg["ergebnis"][k] for k in ("wickelpakete", "schale", "kraft_summe_MN")}))


if __name__ == "__main__":
    main()
