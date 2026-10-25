"""hexmodell.py — Spulengehaeuse als strukturiertes Hexaedernetz mit FESTER Topologie (Surrogat-Rechenmodell).

Je Spule ein Rohr aus Hexaedern entlang der Bahn (N Stationen, fest je Anlage). Querschnitt als
Tensorgitter in (n, b): Wand | Verguss | Wickelpaket | Verguss | Wand. Wandstaerken je Station aus
gehaeuse_netz.waende/entflechten (kollisionsfrei), der Verguss nimmt min(verguss, Wand/2) von der Wand
(wie torus3d). Verbinder: Hexaeder-Loft zwischen gegenueberliegenden Seitenflaechen benachbarter
Gehaeuse (konform, teilt die Knoten beider Gehaeuse). Lagerung: eingespannter Flecken der Aussenseite
am Bahnpunkt mit groesstem Radius (wie gehaeuse_netz).

Last: J x B im Wickelpaket aus Biot-Savart mit nf x nf Teilfilamenten je Spule (Knoten liegen nie auf
einem Filament), als Kraftdichte je Knoten in kraft.dat -> Fortran-UDF elmer_udf/lorentz.f90.
Elmer rechnet nur StressSolve (keine Luft, kein Magnetfeld-FEM) -> gleiche Knoten/Elemente fuer
alle Parameter einer Anlage, nur Koordinaten und Materialwerte aendern sich.

Bodies: 1 Wickelpaket, 2 Verguss, 3 Stahlgehaeuse, 4 Verbinder. Boundary 1 = Lagerflecken.
Auswertung in Python: Dehnung/Spannung im Elementmittelpunkt aus den Elmer-Verschiebungen
(je Element eigenes Material, keine Mittelung ueber Materialgrenzen).

    .venv/bin/python -m stellarator.hexmodell w7x [--stationen 64] [--name test]   (Einzellauf, s. surrogat.py)
"""
from __future__ import annotations
import json, subprocess, time
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

from . import spulen as sp, cad
from .lauf import PROJEKT

QUER = {"n_wand": 2, "n_verguss": 1, "n_wp": 4}      # Zellen je Schicht quer (je Richtung)
MAT_NAMEN = {1: "wickelpaket", 2: "verguss", 3: "stahl", 4: "verbinder"}
UDF_QUELLE = Path(__file__).resolve().parent / "elmer_udf" / "lorentz.f90"
UDF_ORDNER = PROJEKT / "sim" / "surrogat" / "udf"
# Ableitungen der 8 Formfunktionen (Hex, Elmer-Reihenfolge) nach (xi, eta, zeta)
ECKEN = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                  [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)


def dN(xi) -> np.ndarray:
    """(8, 3) Ableitungen dN_k/dxi_j an der Stelle xi."""
    f = 1 + ECKEN * np.asarray(xi, float)                   # (8, 3)
    return np.stack([ECKEN[:, j] * np.prod(np.delete(f, j, 1), 1) for j in range(3)], 1) / 8


@dataclass
class HexNetz:
    X: np.ndarray                    # (Nn, 3) Knoten
    hexa: np.ndarray                 # (E, 8) Knotenindizes (0-basiert, Elmer-Reihenfolge 808)
    mat: np.ndarray                  # (E,) Body 1..4
    spule: np.ndarray                # (E,) Spulenindex, -1 = Verbinder
    lager: np.ndarray                # (L, 5) Elternelement, 4 Knoten der Lagerflaechen
    wp_knoten: list = field(default_factory=list)   # je Spule (N, nq+1, nq+1) Knotenindizes Wickelpaket
    stationen_t: list = field(default_factory=list) # je Spule (N, 3) Tangenten
    info: dict = field(default_factory=dict)


def _teilung(grenzen: np.ndarray, zellen: list[int]) -> np.ndarray:
    """grenzen (N, 6) -> Knotenkoordinaten (N, sum(zellen)+1), jede Schicht gleichmaessig unterteilt."""
    teile = [grenzen[:, :1]]
    for s, m in enumerate(zellen):
        u = np.arange(1, m + 1) / m
        teile.append(grenzen[:, s:s + 1] + u * (grenzen[:, s + 1:s + 2] - grenzen[:, s:s + 1]))
    return np.hstack(teile)


def baue_netz(spulen, br: float, ho: float, W: list[dict], verguss: float, r_lager: float,
              verbinder_je_paar: int = 2, verb_halb: int = 1, verb_lagen: int = 2, q: dict = QUER,
              plan: list | None = None) -> HexNetz:
    """plan: feste Verbinderliste (aus info["verbinder"] eines frueheren Aufrufs) -> gleiche Topologie."""
    nw, nv, nq = q["n_wand"], q["n_verguss"], q["n_wp"]
    zellen = [nw, nv, nq, nv, nw]
    A = sum(zellen)                                       # Zellen je Querrichtung
    w0 = nw + nv                                          # erster Wickelpaket-Index
    # Material je Querschnittszelle (a, c): Bereich 0..4 je Richtung
    bereich = np.repeat(np.arange(5), zellen)
    ba, bc = np.meshgrid(bereich, bereich, indexing="ij")
    mat_q = np.where((ba == 2) & (bc == 2), 1, np.where((ba >= 1) & (ba <= 3) & (bc >= 1) & (bc <= 3), 2, 3))

    X, hexa, mat, spule, lager, wp_kn, tang, gitter = [], [], [], [], [], [], [], []
    versatz = 0
    for k, (s, w) in enumerate(zip(spulen, W)):
        N = len(s.punkte)
        t, n, b = sp.rahmen(s)
        v = {q_: np.minimum(verguss, 0.5 * w[q_]) for q_ in ("innen", "aussen", "links", "rechts")}
        gn = np.c_[-br / 2 - w["innen"], -br / 2 - v["innen"], np.full(N, -br / 2), np.full(N, br / 2),
                   br / 2 + v["aussen"], br / 2 + w["aussen"]]
        gb = np.c_[-ho / 2 - w["links"], -ho / 2 - v["links"], np.full(N, -ho / 2), np.full(N, ho / 2),
                   ho / 2 + v["rechts"], ho / 2 + w["rechts"]]
        un, ub = _teilung(gn, zellen), _teilung(gb, zellen)              # (N, A+1)
        Xk = (s.punkte[:, None, None] + un[:, :, None, None] * n[:, None, None]
              + ub[:, None, :, None] * b[:, None, None])                 # (N, A+1, A+1, 3)
        idx = versatz + np.arange(N * (A + 1) ** 2).reshape(N, A + 1, A + 1)
        i, a, c = np.meshgrid(np.arange(N), np.arange(A), np.arange(A), indexing="ij")
        j = (i + 1) % N
        h = np.stack([idx[i, a, c], idx[i, a + 1, c], idx[i, a + 1, c + 1], idx[i, a, c + 1],
                      idx[j, a, c], idx[j, a + 1, c], idx[j, a + 1, c + 1], idx[j, a, c + 1]], -1)
        X.append(Xk.reshape(-1, 3)); hexa.append(h.reshape(-1, 8))
        mat.append(np.broadcast_to(mat_q, (N, A, A)).ravel()); spule.append(np.full(N * A * A, k))
        wp_kn.append(idx[:, w0:w0 + nq + 1, w0:w0 + nq + 1]); tang.append(t)
        gitter.append((idx, Xk, t, n, b))
        # Lagerflecken: Aussenseite (a = A) um den Bahnpunkt mit groesstem Radius
        il = int(np.argmax(np.hypot(s.punkte[:, 0], s.punkte[:, 1])))
        p_l = s.punkte[il] + n[il] * (br / 2 + w["aussen"][il])
        ii, cc = np.meshgrid(np.arange(N), np.arange(A), indexing="ij")
        jj = (ii + 1) % N
        q4 = np.stack([idx[ii, A, cc], idx[jj, A, cc], idx[jj, A, cc + 1], idx[ii, A, cc + 1]], -1).reshape(-1, 4)
        eltern = (len(np.concatenate(spule)) - N * A * A) + (ii * A * A + (A - 1) * A + cc).ravel()
        mitte = Xk.reshape(-1, 3)[q4 - versatz].mean(1)
        d = np.linalg.norm(mitte - p_l, axis=1)
        wahl = np.where(d <= r_lager)[0]
        if len(wahl) < 2:
            wahl = np.argsort(d)[:2]
        lager.append(np.c_[eltern[wahl], q4[wahl]])
        versatz += N * (A + 1) ** 2

    # Verbinder zwischen toroidal benachbarten Gehaeusen
    n_sp = len(spulen)
    phi = np.array([np.arctan2(*s.punkte.mean(0)[[1, 0]]) for s in spulen])
    folge = np.argsort(phi)
    X_neu, verb, verb_info, auftraege = [], [], [], []
    n_kn = versatz
    for p in range(n_sp if (verbinder_je_paar and plan is None) else 0):
        k, m = int(folge[p]), int(folge[(p + 1) % n_sp])
        idk, Xk_, tk, nk, bk = gitter[k]
        idm, Xm_, tm, nm, bm = gitter[m]
        Pk, Pm = spulen[k].punkte, spulen[m].punkte
        D = np.linalg.norm(Pk[:, None] - Pm[None], axis=2)
        jn = D.argmin(1); dk = D.min(1)
        N = len(Pk)
        # nur echte Seitennachbarn: Verbindungslinie quer (b) zu beiden Spulen, Bahnen parallel
        dv = (Pm[jn] - Pk) / dk[:, None]
        seitlich = ((np.abs(np.sum(dv * bk, 1)) > 0.8) & (np.abs(np.sum(dv * bm[jn], 1)) > 0.8)
                    & (np.abs(np.sum(tk * tm[jn], 1)) > 0.8))
        orte = []
        for _ in range(verbinder_je_paar):
            frei = seitlich.copy()
            for i0 in orte:
                frei &= np.abs(((np.arange(N) - i0 + N // 2) % N) - N // 2) >= N // (verbinder_je_paar + 1)
            if frei.any():
                orte.append(int(np.where(frei, dk, np.inf).argmin()))
        for i0 in orte:
            j0 = int(jn[i0])
            d = (Pm[j0] - Pk[i0]) / np.linalg.norm(Pm[j0] - Pk[i0])
            auftraege.append({"k": k, "m": m, "i0": i0, "j0": j0, "fk": _seite(d, nk[i0], bk[i0]),
                              "fm": _seite(-d, nm[j0], bm[j0]), "abstand_achse_m": float(dk[i0])})
    for v in (plan if plan is not None else auftraege):
        k, m, i0, j0, fk, fm = (v[x] for x in ("k", "m", "i0", "j0", "fk", "fm"))
        idk, Xk_, tk, nk, bk = gitter[k]
        idm, Xm_, tm, nm, bm = gitter[m]
        N, Nm = len(spulen[k].punkte), len(spulen[m].punkte)
        si = (i0 + np.arange(-verb_halb, verb_halb + 1)) % N
        aa = np.arange(A + 1)
        F0, X0 = _flaeche(idk[si], fk, A), _flaeche(Xk_[si], fk, A)                  # (S+1, A+1)
        # Zuordnung der Gegenflaeche (Stationen / Querindex vor- oder rueckwaerts): aus dem Plan oder
        # die Variante mit den geradesten Verbindungslinien
        best = None
        for rs in ((v["rs"],) if "rs" in v else (1, -1)):
            sj = (j0 + rs * np.arange(-verb_halb, verb_halb + 1)) % Nm
            for rev in ((v["rev"],) if "rev" in v else (False, True)):
                am = aa[::-1] if rev else aa
                X1 = _flaeche(Xm_[sj], fm, A)[:, am]
                L_ = np.linalg.norm(X1 - X0, axis=-1).sum()
                if best is None or L_ < best[0]:
                    best = (L_, _flaeche(idm[sj], fm, A)[:, am], X1, rs, rev)
        _, F1, X1, rs, rev = best
        lagen = [F0]
        for l in range(1, verb_lagen):
            lam = l / verb_lagen
            Xl = ((1 - lam) * X0 + lam * X1).reshape(-1, 3)
            lagen.append(n_kn + np.arange(len(Xl)).reshape(F0.shape)); X_neu.append(Xl); n_kn += len(Xl)
        lagen.append(F1)
        el = []
        for l in range(verb_lagen):
            u, o = lagen[l], lagen[l + 1]
            for s_ in range(len(si) - 1):
                for a_ in range(A):
                    el.append([u[s_, a_], u[s_ + 1, a_], u[s_ + 1, a_ + 1], u[s_, a_ + 1],
                               o[s_, a_], o[s_ + 1, a_], o[s_ + 1, a_ + 1], o[s_, a_ + 1]])
        verb.append(np.array(el)); verb_info.append({"k": k, "m": m, "i0": int(i0), "j0": int(j0), "fk": fk,
                                                     "fm": fm, "rs": int(rs), "rev": bool(rev)})
    Xall = np.vstack(X + X_neu)
    hx = [np.vstack(hexa)]; mt = [np.concatenate(mat)]; spl = [np.concatenate(spule)]
    ok_verb = []
    for e, inf in zip(verb, verb_info):
        jm = _jacobi_min(Xall, e)
        if np.all(jm < 0):                                             # Umlaufsinn umdrehen
            e = e[:, [4, 5, 6, 7, 0, 1, 2, 3]]; jm = _jacobi_min(Xall, e)
        inf["jacobi_min"] = float(jm.min()); inf["laenge_m"] = float(np.linalg.norm(
            Xall[e[:, 4:]].mean(1) - Xall[e[:, :4]].mean(1), axis=1).mean())
        inf["ok"] = bool(np.all(jm > 0))
        if inf["ok"] or plan is not None:                              # mit Plan: feste Topologie
            hx.append(e); mt.append(np.full(len(e), 4)); spl.append(np.full(len(e), -1))
        ok_verb.append(inf)
    netz = HexNetz(Xall, np.vstack(hx), np.concatenate(mt), np.concatenate(spl), np.vstack(lager), wp_kn, tang,
                   info={"querschnitt": q, "zellen_quer": A, "stationen": [len(s.punkte) for s in spulen],
                         "verbinder": ok_verb})
    # unbenutzte Verbinder-Zwischenknoten (verworfene Verbinder) bleiben im Netz -> Elmer stoert das nicht,
    # aber freie Knoten ohne Steifigkeit: hier entfernen
    benutzt = np.zeros(len(Xall), bool); benutzt[netz.hexa.ravel()] = True
    if not benutzt.all():
        neu = np.cumsum(benutzt) - 1
        netz.X = Xall[benutzt]; netz.hexa = neu[netz.hexa]; netz.lager[:, 1:] = neu[netz.lager[:, 1:]]
        netz.wp_knoten = [neu[x] for x in netz.wp_knoten]
    jm = _jacobi_min(netz.X, netz.hexa)
    netz.info |= {"knoten": len(netz.X), "elemente": len(netz.hexa), "jacobi_min_rel": float(jm.min()),
                  "elemente_negativ": int((jm <= 0).sum()), "lagerflaechen": len(netz.lager),
                  "verbinder_ok": int(sum(v["ok"] for v in ok_verb)), "verbinder_gesamt": len(ok_verb)}
    return netz


def _seite(d, n, b) -> int:
    """Seitenflaeche (0: -n innen, 1: +n aussen, 2: -b links, 3: +b rechts), deren Normale am besten nach d zeigt."""
    return int(np.argmax([-(d @ n), d @ n, -(d @ b), d @ b]))


def _flaeche(G, seite: int, A: int):
    """Knotengitter (S, A+1, A+1, ...) -> Seitenflaeche (S, A+1, ...)."""
    return (G[:, 0], G[:, A], G[:, :, 0], G[:, :, A])[seite]


def _jacobi_min(X, hexa) -> np.ndarray:
    """Kleinste Jacobi-Determinante an den 8 Ecken, bezogen auf die Mittelpunkt-Determinante."""
    Xe = X[hexa]
    d0 = np.linalg.det(np.einsum("eki,kj->eij", Xe, dN([0, 0, 0])))
    dm = np.min([np.linalg.det(np.einsum("eki,kj->eij", Xe, dN(x))) for x in ECKEN], axis=0)
    return dm / np.abs(d0)                                  # < 0: Element umgestuelpt


def lorentzdichte(netz: HexNetz, spulen, br: float, ho: float, nf: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Kraftdichte J x B [N/m^3] an allen Knoten (0 ausserhalb der Wickelpakete) und Nettokraft je Spule [N]."""
    nf = nf or QUER["n_wp"]
    u = (np.arange(nf) + 0.5) / nf - 0.5
    A_, B_, I_ = [], [], []
    for s in spulen:
        t, n, b = sp.rahmen(s)
        for ua in u:
            for uc in u:
                P = s.punkte + ua * br * n + uc * ho * b
                A_.append(P); B_.append(np.roll(P, -1, 0)); I_.append(np.full(len(P), s.strom / nf ** 2))
    seg = (np.vstack(A_), np.vstack(B_), np.concatenate(I_))
    idx = np.concatenate([w.ravel() for w in netz.wp_knoten])
    B = sp.biot_savart(netz.X[idx], seg)
    T = np.concatenate([np.broadcast_to(t[:, None, None], w.shape + (3,)).reshape(-1, 3)
                        for t, w in zip(netz.stationen_t, netz.wp_knoten)])
    J = np.concatenate([np.full(w.size, s.strom / (br * ho)) for s, w in zip(spulen, netz.wp_knoten)])
    f = np.zeros_like(netz.X); f[idx] = J[:, None] * np.cross(T, B)
    # Nettokraft je Spule: Elementmittel x Volumen ueber die Wickelpaket-Elemente
    wp = netz.mat == 1
    V = elementvolumen(netz.X, netz.hexa[wp])
    Fe = f[netz.hexa[wp]].mean(1) * V[:, None]
    F = np.array([Fe[netz.spule[wp] == k].sum(0) for k in range(len(spulen))])
    return f, F


def elementvolumen(X, hexa) -> np.ndarray:
    """Volumen je Hexaeder (2x2x2 Gauss)."""
    g = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]) / np.sqrt(3)
    Xe = X[hexa]
    return sum(np.linalg.det(np.einsum("eki,kj->eij", Xe, dN(p))) for p in g)


# ------------------------------------------------------------------ Elmer
def udf() -> Path:
    """lorentz.so (einmal je Quelle uebersetzen)."""
    UDF_ORDNER.mkdir(parents=True, exist_ok=True)
    so = UDF_ORDNER / "lorentz.so"
    if not so.exists() or so.stat().st_mtime < UDF_QUELLE.stat().st_mtime:
        subprocess.run(["elmerf90", "-o", str(so), str(UDF_QUELLE)], cwd=UDF_ORDNER, check=True, capture_output=True)
    return so


def schreibe_fall(ordner: Path, netz: HexNetz, f: np.ndarray, material: dict, loeser: str = "iterativ") -> None:
    """Elmer-Netz (direkt, ohne ElmerGrid), kraft.dat und case.sif.
    material: {1..4: {"E_Pa", "nu"}}."""
    m = ordner / "netz"; m.mkdir(parents=True, exist_ok=True)
    Nn, E, L = len(netz.X), len(netz.hexa), len(netz.lager)
    (m / "mesh.header").write_text(f"{Nn} {E} {L}\n2\n808 {E}\n404 {L}\n")
    ids = np.arange(1, Nn + 1)
    np.savetxt(m / "mesh.nodes", np.c_[ids, -np.ones(Nn), netz.X], fmt="%d %d %.9e %.9e %.9e")
    np.savetxt(m / "mesh.elements", np.c_[np.arange(1, E + 1), netz.mat, np.full(E, 808), netz.hexa + 1], fmt="%d")
    np.savetxt(m / "mesh.boundary", np.c_[np.arange(1, L + 1), np.ones(L, int), netz.lager[:, 0] + 1,
                                          np.zeros(L, int), np.full(L, 404), netz.lager[:, 1:] + 1], fmt="%d")
    with open(ordner / "kraft.dat", "w") as fh:
        fh.write(f"{Nn}\n")
        np.savetxt(fh, np.c_[netz.X, f], fmt="%.9e")
    so = udf()
    ls = {"iterativ": """  Linear System Solver = "Iterative"
  Linear System Iterative Method = "CG"
  Linear System Preconditioning = ILU0
  Linear System Max Iterations = 20000
  Linear System Convergence Tolerance = 1e-8
  Linear System Abort Not Converged = False
  Linear System Residual Output = 200
""", "mumps": """  Linear System Solver = "Direct"
  Linear System Direct Method = "MUMPS"
"""}[loeser]
    S = ["""Header
  Mesh DB "." "netz"
  Results Directory "erg"
End
Simulation
  Coordinate System = "Cartesian 3D"
  Simulation Type = "Steady State"
  Steady State Max Iterations = 1
  Output Intervals = 1
  Max Output Level = 4
End
Constants
End
"""]
    for k, name in MAT_NAMEN.items():
        S.append(f'Body {k}\n  Name = "{name}"\n  Equation = 1\n  Material = {k}\n'
                 + ("  Body Force = 1\n" if k == 1 else "") + "End\n")
        S.append(f'Material {k}\n  Name = "{name}"\n  Youngs Modulus = {material[k]["E_Pa"]:.6e}\n'
                 f'  Poisson Ratio = {material[k]["nu"]}\nEnd\n')
    S.append("Body Force 1\n" + "".join(
        f'  Stress Bodyforce {i} = Variable Time\n    Real Procedure "{so}" "kraft_{c}"\n' for i, c in ((1, "x"), (2, "y"), (3, "z")))
        + "End\n")
    S.append(f"""Equation 1
  Active Solvers(1) = 1
End
Solver 1
  Equation = "Stress"
  Procedure = "StressSolve" "StressSolver"
  Variable = -dofs 3 "Displacement"
  Calculate Stresses = Logical False
  Displace Mesh = Logical False
{ls}End
Solver 2
  Exec Solver = After All
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = "hex"
  Vtu Format = Logical True
  Binary Output = Logical True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Displacement 1 = Real 0.0
  Displacement 2 = Real 0.0
  Displacement 3 = Real 0.0
End
""")
    (ordner / "case.sif").write_text("".join(S))


def rechne(ordner: Path, timeout_s: float | None = None) -> float:
    t0 = time.time()
    with open(ordner / "solve.log", "w") as fh:
        subprocess.run(["ElmerSolver", "case.sif"], cwd=ordner, stdout=fh, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout_s)
    return time.time() - t0


def verschiebung(ordner: Path, netz: HexNetz) -> np.ndarray:
    import pyvista as pv
    erg = sorted((ordner / "erg").glob("hex*.vtu"))[-1]
    g = pv.read(erg)
    if len(g.points) != len(netz.X) or np.abs(g.points - netz.X).max() > 1e-5:
        raise RuntimeError("Knotenreihenfolge der Elmer-Ausgabe passt nicht zum Netz")
    return np.asarray(g.point_data["displacement"], float)


def spannungen(netz: HexNetz, U: np.ndarray, material: dict) -> np.ndarray:
    """Von Mises [Pa] im Elementmittelpunkt."""
    d = dN([0, 0, 0])
    J = np.einsum("eki,kj->eij", netz.X[netz.hexa], d)
    G = np.einsum("eki,kj->eij", U[netz.hexa], d) @ np.linalg.inv(J)
    eps = 0.5 * (G + G.transpose(0, 2, 1))
    E = np.array([material[k]["E_Pa"] for k in range(1, 5)])[netz.mat - 1]
    nu = np.array([material[k]["nu"] for k in range(1, 5)])[netz.mat - 1]
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    tr = np.trace(eps, axis1=1, axis2=2)
    sig = 2 * mu[:, None, None] * eps + (lam * tr)[:, None, None] * np.eye(3)
    s = sig - np.trace(sig, axis1=1, axis2=2)[:, None, None] / 3 * np.eye(3)
    return np.sqrt(1.5 * np.einsum("eij,eij->e", s, s))


def kennzahlen(netz: HexNetz, U: np.ndarray, vm: np.ndarray, rho_stahl: float = 7900.0) -> dict:
    V = elementvolumen(netz.X, netz.hexa)
    u = np.linalg.norm(U, axis=1)
    k = {"u_max_mm": float(u.max() * 1e3)}
    for m, name in MAT_NAMEN.items():
        sel = netz.mat == m
        if not sel.any():
            continue
        v = vm[sel] / 1e6
        o = np.argsort(v); cv = np.cumsum(V[sel][o]) / V[sel].sum()
        k[name] = {"vm_max_MPa": float(v.max()), "vm_p99_MPa": float(v[o][np.searchsorted(cv, 0.99)]),
                   "vm_mittel_MPa": float((v * V[sel]).sum() / V[sel].sum()), "volumen_m3": float(V[sel].sum())}
    k["stahl"]["masse_t"] = k["stahl"]["volumen_m3"] * rho_stahl / 1e3
    if "verbinder" in k:
        k["verbinder"]["masse_t"] = k["verbinder"]["volumen_m3"] * rho_stahl / 1e3
    return k


def als_vtu(netz: HexNetz, pfad: Path, felder: dict | None = None, punkte: dict | None = None) -> None:
    import pyvista as pv
    zellen = np.c_[np.full(len(netz.hexa), 8), netz.hexa].ravel()
    g = pv.UnstructuredGrid(zellen, np.full(len(netz.hexa), pv.CellType.HEXAHEDRON, np.uint8), netz.X)
    g.cell_data["material"] = netz.mat; g.cell_data["spule"] = netz.spule
    for k, v in (felder or {}).items():
        g.cell_data[k] = v
    for k, v in (punkte or {}).items():
        g.point_data[k] = v
    g.save(pfad)
