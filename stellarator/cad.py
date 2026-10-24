"""cad.py — Wickelpakete als echte CAD-Volumen (gmsh/OpenCASCADE), STEP, Elmer-Netz.

PicoGK-unabhaengiger Geometrieweg. Je Spule wird das Rechteckprofil (breite entlang n,
hoehe entlang b aus spulen.rahmen) an jedem Filamentpunkt platziert und in ZWEI Haelften
geloftet (ThruSections, ruled = stueckweise eben), die dann verschmolzen werden.
Nicht robust (B-015): ein einziger geschlossener Loft, Sweep (addPipe), glatter Loft
(selbstschneidende Oberflaechennetze).

STEP (wickelpaket/baue_step) nur fuer CAD-Weitergabe: langsam (ruled, ~640 Flaechen je Spule).
Elmer-Netz OHNE CAD-Kern aus eigenem Dreiecksnetz (rohr_netz -> elmer_netz), Physical Groups
  Body 1..n = Spulen (Reihenfolge der Liste), Body n+1 = Luft, Boundary 1 = Aussenrand.
Ausgabe gmsh-2.2-.msh -> `ElmerGrid 14 2` -> Elmer-Netzordner.
"""
from __future__ import annotations
import subprocess, time
from pathlib import Path
import numpy as np
import gmsh
from . import spulen as sp


def _profil(occ, p, n, b, breite, hoehe) -> int:
    q = [occ.addPoint(*(p + 0.5 * (e1 * breite * n + e2 * hoehe * b)))
         for e1, e2 in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    return occ.addWire([occ.addLine(q[k], q[(k + 1) % 4]) for k in range(4)])


def wickelpaket(occ, s: sp.Spule, breite: float, hoehe: float, ruled: bool = True) -> tuple[int, int]:
    """Ein Wickelpaket als OCC-Volumen (dim, tag)."""
    t, n, b = sp.rahmen(s)
    W = [_profil(occ, p, n[i], b[i], breite, hoehe) for i, p in enumerate(s.punkte)]
    N = len(W)
    # Teilungsstellen variieren, falls OCC die Haelften nicht verschmilzt
    for a in (0, N // 8, N // 4, 3 * N // 8):
        ring = W[a:] + W[:a]
        va = [x for x in occ.addThruSections(ring[:N // 2 + 1], makeSolid=True, makeRuled=ruled) if x[0] == 3]
        vb = [x for x in occ.addThruSections(ring[N // 2:] + [ring[0]], makeSolid=True, makeRuled=ruled) if x[0] == 3]
        r, _ = occ.fuse(va, vb)
        if len(r) == 1:
            return r[0]
        occ.remove(r, recursive=True)
    raise RuntimeError(f"Wickelpaket {s.name}: Loft/Fuse fehlgeschlagen")


def ueberlapp(occ, vols, spulen, r_nachbar: float = 3.0) -> list[tuple]:
    """Paarweise Schnittvolumen (m3) benachbarter Spulen; leere Liste = kollisionsfrei."""
    r_nachbar = r_nachbar or max(1.0, 3 * np.hypot(breite, hoehe))
    out = []
    for i in range(len(vols)):
        for j in range(i + 1, len(vols)):
            if baeume[j].query(spulen[i].punkte)[0].min() > r_nachbar:
                continue
            r, _ = occ.intersect([vols[i]], [vols[j]], removeObject=False, removeTool=False)
            if r:
                occ.synchronize()
                out.append((spulen[i].name, spulen[j].name, sum(occ.getMass(*x) for x in r)))
                occ.remove(r, True)
    return out


def _rechteck_abstand(u, v, breite, hoehe):
    """Vorzeichenbehafteter Abstand zum Rechteck |u|<=breite/2, |v|<=hoehe/2 (innen < 0)."""
    du, dv = np.abs(u) - breite / 2, np.abs(v) - hoehe / 2
    aussen = np.hypot(np.maximum(du, 0), np.maximum(dv, 0))
    return np.where((du < 0) & (dv < 0), np.maximum(du, dv), aussen)


def abstaende(spulen, breite, hoehe, r_nachbar: float | None = None, n_rand: int = 6,
              n_basis: int | None = 7) -> dict:
    """Minimaler Spalt (m) zwischen benachbarten Wickelpaketen, ohne CAD (B-015).

    Oberflaechenpunkte von A (Rechteckumfang je Filamentpunkt) werden gegen B geprueft:
    naechster Filamentpunkt von B, Versatz in B's (n, b)-Rahmen, Abstand zum Rechteck.
    Gilt, solange der Biegeradius (>= 0,4 m) groesser als die halbe Diagonale ist.
    spulen fein abtasten (n_punkte ~500 reicht), Spalt < 0 = Durchdringung.
    n_basis: nur Paare mit einer der ersten n_basis Spulen (W7-X-Satz: 7 Basisspulen p0_n;
    die 10 Symmetriekopien bilden jedes Paar darauf ab). None = alle Paare.
    r_nachbar: nur Paare, deren Mittellinien sich naeher kommen (Standard 3 x Diagonale, min. 1 m;
    massstabsunabhaengig, frueher Schwerpunktabstand 3 m -> bei R0 > 10 m keine Paare).
    """
    from scipy.spatial import cKDTree
    s_ = np.linspace(-1, 1, n_rand, endpoint=False)
    rand = np.concatenate([np.c_[np.ones_like(s_), s_], np.c_[-s_, np.ones_like(s_)],
                           np.c_[-np.ones_like(s_), -s_], np.c_[s_, -np.ones_like(s_)]])
    rand = rand * [breite / 2, hoehe / 2]                          # (4*n_rand, 2) in (n, b)
    rahmen = [sp.rahmen(s) for s in spulen]
    oberfl = [(s.punkte[:, None] + rand[:, :1] * n[:, None] + rand[:, 1:] * b[:, None]).reshape(-1, 3)
              for s, (t, n, b) in zip(spulen, rahmen)]
    baeume = [cKDTree(s.punkte) for s in spulen]
    r_nachbar = r_nachbar or max(1.0, 3 * np.hypot(breite, hoehe))
    paare = []
    for i in range(n_basis or len(spulen)):
        for j in range(i + 1, len(spulen)):
            if baeume[j].query(spulen[i].punkte)[0].min() > r_nachbar:
                continue
            spalt = np.inf
            for a, b_ in ((i, j), (j, i)):
                _, k = baeume[b_].query(oberfl[a])
                d = oberfl[a] - spulen[b_].punkte[k]
                _, n, b = rahmen[b_]
                spalt = min(spalt, _rechteck_abstand(np.sum(d * n[k], 1), np.sum(d * b[k], 1),
                                                     breite, hoehe).min())
            paare.append((spulen[i].name, spulen[j].name, float(spalt)))
    paare.sort(key=lambda p: p[2])
    return {"n_paare": len(paare), "spalt_min_m": paare[0][2] if paare else float("inf"), "engste": paare[:5],
            "durchdringungen": [p for p in paare if p[2] < 0]}


def baue_step(spulen, breite, hoehe, pfad: Path, pruefe: bool = False) -> dict:
    """Alle Wickelpakete -> STEP (m). Rueckgabe: Volumen, Ueberlapp, Zeiten."""
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 1)
    try:
        occ = gmsh.model.occ; t0 = time.time()
        vols = [wickelpaket(occ, s, breite, hoehe) for s in spulen]
        occ.synchronize(); t_bau = time.time() - t0
        vol = [occ.getMass(*v) for v in vols]
        soll = [breite * hoehe * s.laenge() for s in spulen]
        t0 = time.time()
        ue = ueberlapp(occ, vols, spulen) if pruefe else None
        occ.synchronize(); gmsh.write(str(pfad))
        return {"datei": str(pfad), "n": len(vols), "volumen_m3": sum(vol),
                "vol_ist_soll_min": min(v / s for v, s in zip(vol, soll)),
                "vol_ist_soll_max": max(v / s for v, s in zip(vol, soll)),
                "ueberlapp": ue, "t_bau_s": t_bau, "t_pruef_s": time.time() - t0}
    finally:
        gmsh.finalize()


def neu_abtasten(P: np.ndarray, N: int) -> np.ndarray:
    """Geschlossenes Polygon auf N Punkte gleicher Bogenlaenge (periodischer kubischer Spline)."""
    from scipy.interpolate import CubicSpline
    Q = np.vstack([P, P[:1]])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    return CubicSpline(s, Q, bc_type="periodic")(np.linspace(0, s[-1], N, endpoint=False))


def rohr_netz(s: sp.Spule, breite: float, hoehe: float, h: float) -> tuple[np.ndarray, np.ndarray]:
    """Wasserdichtes Rechteckrohr mit gemeinsamen Knoten, Kantenlaenge ~h.

    Rueckgabe (knoten (M,3), dreiecke (K,3) Indizes), Normalen nach aussen (wie
    spulen.rohr_dreiecke, aber unterteilt und indiziert -> direkt als gmsh-Flaeche nutzbar).
    """
    N = max(16, int(np.ceil(s.laenge() / h)))
    q = sp.Spule(s.name, s.typ, neu_abtasten(s.punkte, N), s.strom)
    t, n, b = sp.rahmen(q)
    nb, nh = max(2, int(np.ceil(breite / h))), max(2, int(np.ceil(hoehe / h)))
    ecken = np.array([(-1, -1), (1, -1), (1, 1), (-1, 1)]) * [breite / 2, hoehe / 2]
    rand = np.concatenate([ecken[k] + np.linspace(0, 1, m, endpoint=False)[:, None] * (ecken[(k + 1) % 4] - ecken[k])
                           for k, m in enumerate((nb, nh, nb, nh))])            # (R,2) gegen Uhrzeigersinn
    R = len(rand)
    knoten = (q.punkte[:, None] + rand[None, :, :1] * n[:, None] + rand[None, :, 1:] * b[:, None]).reshape(-1, 3)
    i, r = np.meshgrid(np.arange(N), np.arange(R), indexing="ij")
    j, w = (i + 1) % N, (r + 1) % R
    a_, b_, c_, d_ = i * R + r, j * R + r, j * R + w, i * R + w
    dreiecke = np.concatenate([np.stack([a_, b_, c_], -1).reshape(-1, 3), np.stack([a_, c_, d_], -1).reshape(-1, 3)])
    P = knoten[dreiecke]
    vol = np.einsum("ij,ij->i", P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6
    return knoten, (dreiecke if vol > 0 else dreiecke[:, ::-1])


def elmer_netz(spulen, breite, hoehe, ordner: Path, rand_m: float = 5.0,
               h_spule: float = 0.03, h_luft: float = 0.6, dist_max: float = 3.0,
               nur_schaetzen: bool = False) -> dict:
    """Spulen + Luftquader -> ordner/netz.msh -> ElmerGrid -> ordner/netz/ (Elmer-Netz).

    STL-Weg ohne CAD-Kern (B-015): je Spule ein festes Oberflaechennetz (rohr_netz) als
    diskrete gmsh-Flaeche, Spulenvolumen = deren Huelle, Luft = Quader mit Spulen als
    Loechern (konforme Grenzflaechen ohne Boolesche Operationen). Netzweite in der Luft
    waechst von h_spule (an den Spulen) auf h_luft (ab dist_max).
    """
    ordner.mkdir(parents=True, exist_ok=True)
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 1)
    try:
        t0 = time.time(); m = gmsh.model; geo = m.geo
        flaechen, versatz, n_tri = [], 1, 0
        for s in spulen:
            kn, tri = rohr_netz(s, breite, hoehe, h_spule)
            f = m.addDiscreteEntity(2)
            m.mesh.addNodes(2, f, np.arange(versatz, versatz + len(kn)), kn.ravel())
            m.mesh.addElementsByType(f, 2, [], (tri + versatz).ravel())
            versatz += len(kn); n_tri += len(tri); flaechen.append(f)
        P = np.concatenate([s.punkte for s in spulen])
        lo, hi = P.min(0) - rand_m, P.max(0) + rand_m
        pk = [geo.addPoint(x, y, z, h_luft) for z in (lo[2], hi[2]) for y in (lo[1], hi[1]) for x in (lo[0], hi[0])]
        L = lambda a, b: geo.addLine(pk[a], pk[b])
        e = {k: L(*k) for k in [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]}
        def seite(a, b, c, d):
            kanten = [(a, b), (b, c), (c, d), (d, a)]
            return geo.addPlaneSurface([geo.addCurveLoop([e[k] if k in e else -e[k[::-1]] for k in kanten])])
        box = [seite(0, 1, 3, 2), seite(4, 6, 7, 5), seite(0, 4, 5, 1), seite(2, 3, 7, 6), seite(0, 2, 6, 4), seite(1, 5, 7, 3)]
        schalen = [geo.addSurfaceLoop([f]) for f in flaechen]
        vol_spulen = [geo.addVolume([sl]) for sl in schalen]
        vol_luft = geo.addVolume([geo.addSurfaceLoop(box)] + schalen)
        geo.synchronize()
        for i, v in enumerate(vol_spulen):
            m.addPhysicalGroup(3, [v], i + 1, name=spulen[i].name)
        m.addPhysicalGroup(3, [vol_luft], len(spulen) + 1, name="luft")
        m.addPhysicalGroup(2, box, 1, name="aussen")
        f1 = m.mesh.field.add("Distance"); m.mesh.field.setNumbers(f1, "SurfacesList", flaechen)
        f2 = m.mesh.field.add("Threshold"); m.mesh.field.setNumber(f2, "InField", f1)
        for k, v in {"SizeMin": h_spule, "SizeMax": h_luft, "DistMin": 0.0, "DistMax": dist_max}.items():
            m.mesh.field.setNumber(f2, k, v)
        m.mesh.field.setAsBackgroundMesh(f2)
        for k in ("MeshSizeExtendFromBoundary", "MeshSizeFromPoints", "MeshSizeFromCurvature"):
            gmsh.option.setNumber(f"Mesh.{k}", 0)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        t_geo = time.time() - t0
        if nur_schaetzen:
            return {"n_dreiecke_spulen": n_tri, "t_geo_s": t_geo}
        t0 = time.time(); m.mesh.generate(3); t_netz = time.time() - t0
        n_tet = sum(len(x) for x in m.mesh.getElements(3)[1])
        gmsh.write(str(ordner / "netz.msh"))
    finally:
        gmsh.finalize()
    subprocess.run(["ElmerGrid", "14", "2", "netz.msh", "-autoclean"], cwd=ordner,
                   check=True, capture_output=True)
    return {"n_tet": n_tet, "n_dreiecke_spulen": n_tri, "t_netz_s": t_netz, "netz": str(ordner / "netz"),
            "bodies": {s.name: i + 1 for i, s in enumerate(spulen)} | {"luft": len(spulen) + 1}}
