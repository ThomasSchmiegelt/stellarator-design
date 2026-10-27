"""kuehlung_segment.py — ein 10-Grad-Segment der Gefaesswand (1-GW-Anlage) als Kuehlsegment: Gyroid-Kern,
Eintritt ueber Verteilkammer + Lochblech, Austritt ueber freie Sammelkammer, je ein Kreisrohr nach aussen.

    .venv/bin/python -m stellarator.kuehlung_segment [--name a] [--phi0 85 --phi1 95] [--voxel 12] [--d_loch 50 --n_loch 24]

Auslegung aus der Waermelast: q auf der Plasmaseite (Innenhaut) x Flaeche = P; m = P / (cp dT); Rohre aus v_Rohr.
Geometrie in Toroidalrichtung (von phi0): Stirnplatte | Verteilkammer (Eintrittsrohr) | Lochblech | Beruhigung |
Gyroid-Kern | Beruhigung | Sammelkammer (Austrittsrohr) | Stirnplatte. Rohre gehen aussen (groesstes R) radial ab,
in der Spulenluecke. Bauraumpruefung: Abstand Rohre/Aussenhaut zu Spulengehaeusen und Verbindern (Surrogat 1000 MW).
Ausgabe sim/kuehlung_segment/<name>/: stahl.stl, wasser.stl, auslegung.json, ergebnis.json, segment.png.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

from .lauf import PROJEKT
from .gyroid_gefaess import randflaeche, sektor_stl, keil_stl
from .gesamtszene import normalen
from .speicherwaechter import starte_begrenzt

BIN = PROJEKT / "picogk" / "SegmentKuehlung" / "bin" / "Release" / "net9.0" / "SegmentKuehlung"
WURZEL = PROJEKT / "sim" / "kuehlung_segment"
RHO, CP = 1000.0, 4180.0          # Wasser (kalt gerechnet; bei 300 C: rho ~ 710, cp ~ 5,7 kJ/kgK)


def rand_bei(phi_grad: float, n_th: int = 720, d: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    """Plasmarand X (n_th, 3) und Aussennormale N bei einem Winkel phi [Grad]."""
    ph = np.radians([phi_grad - d, phi_grad, phi_grad + d])
    X = randflaeche(n_th=n_th, phi=ph)
    x, n = X[:, 1], normalen(X)[:, 1]
    if np.einsum("ij,ij->i", n, x - x.mean(0)).mean() < 0:           # Vorzeichen nur an dieser Spalte pruefen
        n = -n
    return x, n


def schnitt_ebene(phi_grad: float, tiefe: float, n_th: int = 720, breite: float = 6.0) -> np.ndarray:
    """Punkte (n_th, 3) der Flaeche 'Plasmarand + tiefe * Normale' in der Ebene phi = phi_grad.
    Die Normale der verdrillten Flaeche hat einen Toroidalanteil: X + t N liegt NICHT in der Ebene von X.
    Deshalb Flaeche ueber phi +- breite auswerten und je theta auf phi_grad interpolieren."""
    ph = np.radians(np.linspace(phi_grad - breite, phi_grad + breite, 121))
    X = randflaeche(n_th=n_th, phi=ph)
    N = normalen(X)
    if np.einsum("ijk,ijk->ij", N, X - X.mean(0, keepdims=True)).mean() < 0:
        N = -N
    P = X + tiefe * N
    w = np.degrees(np.arctan2(P[..., 1], P[..., 0]))              # tatsaechlicher Winkel je Punkt
    R = np.hypot(P[..., 0], P[..., 1]); Z = P[..., 2]
    Rq = np.array([np.interp(phi_grad, w[i], R[i]) for i in range(n_th)])
    Zq = np.array([np.interp(phi_grad, w[i], Z[i]) for i in range(n_th)])
    f = np.radians(phi_grad)
    return np.c_[Rq * np.cos(f), Rq * np.sin(f), Zq]


def bogen_gleich(P: np.ndarray, n: int) -> np.ndarray:
    """n Punkte gleichen Bogenabstands auf der geschlossenen Kurve P (m, 3)."""
    Q = np.vstack([P, P[:1]]); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, s[-1], n, endpoint=False) + s[-1] / (2 * n)
    return np.stack([np.interp(t, s, Q[:, k]) for k in range(3)], 1)


def auslegung(a) -> dict:
    """Waermelast, Massenstrom, Geschwindigkeiten und Druckverlust Lochblech (Schaetzung vor der CFD)."""
    X = randflaeche(n_th=192, n_ph=1440)
    N = normalen(X)
    j = np.where((np.degrees(np.arctan2(X[0, :, 1], X[0, :, 0])) % 360 >= a.phi0) &
                 (np.degrees(np.arctan2(X[0, :, 1], X[0, :, 0])) % 360 <= a.phi1))[0]
    S = (X + a.spalt * N)[:, j]                                       # Innenhaut (plasmaseitig)
    du = np.roll(S, -1, 0) - S; dv = np.diff(S, axis=1)
    A = float(np.linalg.norm(np.cross(du[:, :-1], dv), axis=-1).sum())
    P = a.q_MW * 1e6 * A
    m = P / (CP * a.dT)
    Q = m / RHO
    A_ein, A_aus = np.pi * (a.d_ein / 2000) ** 2, np.pi * (a.d_aus / 2000) ** 2
    A_loch = a.n_loch * a.reihen * np.pi * (a.d_loch / 2000) ** 2
    v_ein, v_aus, v_loch = Q / A_ein, Q / A_aus, Q / A_loch
    zeta = 2.7                                                        # Lochblech duenn, scharfkantig (Idelchik, grob)
    return {"flaeche_plasmaseite_m2": A, "waermelast_MW": P / 1e6, "massenstrom_kg_s": m, "volumenstrom_m3_s": Q,
            "annahmen": {"q_MW_m2": a.q_MW, "dT_K": a.dT, "rho": RHO, "cp": CP, "zeta_loch": zeta},
            "v_ein_m_s": v_ein, "v_aus_m_s": v_aus, "v_loch_m_s": v_loch,
            "dp_lochblech_kPa": zeta * RHO * v_loch ** 2 / 2e3, "staudruck_ein_kPa": RHO * v_ein ** 2 / 2e3,
            "Re_ein": v_ein * a.d_ein / 1000 / 1e-6}


def prisma_stl(poly, Z_max, pfad):
    """Senkrechtes Prisma ueber einem konvexen Polygon (xy, mm), |z| <= Z_max."""
    from .gyroid_gefaess import schreibe_stl
    c = poly.mean(0); n = len(poly)
    u = lambda P: np.r_[P, -Z_max]; ob = lambda P: np.r_[P, Z_max]
    tri = []
    for i in range(n):
        j = (i + 1) % n
        tri += [(u(c), u(poly[j]), u(poly[i])), (ob(c), ob(poly[i]), ob(poly[j])),
                (u(poly[i]), u(poly[j]), ob(poly[j])), (u(poly[i]), ob(poly[j]), ob(poly[i]))]
    T = np.array(tri)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    schreibe_stl(pfad, T if vol > 0 else T[:, ::-1], skala=1.0)


def geometrie(a, o: Path) -> dict:
    """STL-Keile, Lochblech-Bohrungen und Rohre (mm) fuer PicoGK; Rueckgabe: Lage (Winkel, Punkte)."""
    X = randflaeche(n_th=192, n_ph=1440)
    sektor_stl(X * 1000, a.phi0 - 3, a.phi1 + 3, o / "plasma.stl")
    # Versatzflaechen exakt als Plasmarand + Abstand * Normale. PicoGK voxOffset ist an der Schulter der Plasmaform
    # (+-48 Grad) ungenau: Innenhaut dort ~50 mm zu dick, Band verengt -> Stroemungseinbruch (f6-f8)
    N = normalen(X)
    if np.einsum("ijk,ijk->ij", N, X - X.mean(0, keepdims=True)).mean() < 0:
        N = -N
    flaechen = {"spalt": a.spalt, "haut_innen": a.spalt + a.haut_innen, "haut_aussen": a.spalt + a.wand - a.haut_aussen,
                "wand": a.spalt + a.wand}
    if a.schicht > 0:
        flaechen["vorn"] = a.spalt + a.haut_innen + a.schicht
    for k, d in flaechen.items():
        sektor_stl((X + d * N) * 1000, a.phi0 - 3, a.phi1 + 3, o / f"flaeche_{k}.stl")
    Xm, Nm = rand_bei(0.5 * (a.phi0 + a.phi1))
    R_in = float(np.hypot(*(Xm + a.spalt * Nm)[:, :2].T).min())     # kleinster Radius der Wand (innen)
    Xa = Xm + (a.spalt + a.wand) * Nm
    R_out = float(np.hypot(*Xa[:, :2].T).max())                      # Aussenseite, dort gehen die Rohre ab
    g = lambda mm, R: np.degrees(mm / 1000 / R)
    te, tp = a.stirn, a.platte
    e0 = (a.phi0, a.phi0 + g(te, R_in)); e1 = (a.phi1 - g(te, R_in), a.phi1)
    # Eintritt innen (kleinstes R): Kammerbreite an der Aussenhaut innen bemessen, dort sitzt die Bohrung
    R_ein = float(np.hypot(*Xa[:, :2].T).min()) if a.ein_innen else R_out
    p0 = e0[1] + g(a.kammer_ein, R_ein); p1 = p0 + g(tp, R_in)
    k0 = p1 + g(a.ruhe, R_out)
    k1 = e1[0] - g(a.kammer_aus, R_out) - g(a.ruhe, R_out)
    if a.schraeg:
        # Kern zwischen zwei senkrechten Ebenen (Draufsicht: zwei Geraden). Eintrittskammer keilfoermig: innen kammer_ein
        # breit, laeuft zur Aussenseite an der Stirnplatte spitz aus; Sammelkammer umgekehrt (aussen kammer_aus, innen spitz)
        pol = lambda R, ph: np.array([R * np.cos(np.radians(ph)), R * np.sin(np.radians(ph))])
        L1 = (pol(R_out, e0[1]), pol(R_ein, e0[1] + g(a.kammer_ein, R_ein)))
        L2 = (pol(R_out, e1[0] - g(a.kammer_aus, R_out)), pol(R_ein, e1[0]))
        auf = lambda L, t: L[0] + t * (L[1] - L[0])
        quad = np.array([auf(L1, -0.2), auf(L1, 1.3), auf(L2, 1.3), auf(L2, -0.2)])
        winkel = lambda P: float(np.degrees(np.arctan2(P[1], P[0])))
        k0, k1 = winkel(auf(L1, 0.5)), winkel(auf(L2, 0.5))     # Kernmitte (halbe Hoehe der Geraden) fuer die Auswertung
    elif k1 - k0 < 1.0:
        raise SystemExit(f"Kein Platz fuer den Gyroid-Kern ({k1 - k0:.2f} Grad)")
    R_max = (float(np.hypot(X[..., 0], X[..., 1]).max()) + a.spalt + a.wand + 1.5) * 1000
    Z_max = (float(np.abs(X[..., 2]).max()) + a.spalt + a.wand + 1.5) * 1000
    for name, (w0, w1) in {"segment": (a.phi0, a.phi1), "kern": (k0, k1), "ende0": e0, "ende1": e1,
                           "platte": (p0 - 0.02, p1 + 0.02)}.items():
        keil_stl(w0, w1, R_max, Z_max, o / f"keil_{name}.stl")
    if a.schraeg:
        prisma_stl(quad * 1000, Z_max, o / "keil_kern.stl")
    # Bohrungen: in Reihen auf Flaechen konstanter Wandtiefe, gleicher Bogenabstand, Achse = Toroidalrichtung
    pm = 0.5 * (p0 + p1); Xp, Np = rand_bei(pm)
    e_phi = np.array([-np.sin(np.radians(pm)), np.cos(np.radians(pm)), 0.0])
    tief = a.wand - a.haut_innen - a.haut_aussen
    loecher = []
    for f in (np.arange(a.reihen) + 0.5) / a.reihen:
        for c in bogen_gleich(schnitt_ebene(pm, a.spalt + a.haut_innen + f * tief), a.n_loch):
            # Plattendicke waechst mit R (Keil); Bohrung je 30 mm ueber beide Seiten hinaus, sonst nicht durchgehend
            L = (np.radians(p1 - p0 + 0.04) * np.hypot(c[0], c[1]) + 0.06) / 2
            loecher.append([*((c - L * e_phi) * 1000), *((c + L * e_phi) * 1000), a.d_loch / 2])
    # Rohre: aussen (groesstes R), Kammermitte, Achse = Wandnormale; von Wandmitte bis rohr_l ueber die Aussenhaut
    rohre, lage = [], {}
    for name, ph, d in (("ein", e0[1] + g(a.kammer_ein / 2, R_ein), a.d_ein),
                        ("aus", e1[0] - g(a.kammer_aus / 2, R_out), a.d_aus)):
        Pa = schnitt_ebene(ph, a.spalt + a.haut_innen + 0.5 * tief)      # Rohr in der Ebene phi = Kammermitte
        Pb = schnitt_ebene(ph, a.spalt + a.wand + a.rohr_l)
        R_b = np.hypot(Pb[:, 0], Pb[:, 1])
        i = int(np.argmin(R_b) if (name == "ein" and a.ein_innen) else np.argmax(R_b))
        p_a, p_b = Pa[i], Pb[i]
        n = (p_b - p_a) / np.linalg.norm(p_b - p_a)
        rohre.append([*(p_a * 1000), *(p_b * 1000), d / 2, a.rohr_wand])
        lage[name] = {"phi_grad": ph, "innen_m": p_a.tolist(), "ende_m": p_b.tolist(), "achse": n.tolist(), "d_mm": d}
    auftrag = {"plasma_stl": str(o / "plasma.stl"), **{f"keil_{k}": str(o / f"keil_{k}.stl")
               for k in ("segment", "kern", "ende0", "ende1", "platte")},
               "spalt": a.spalt * 1000, "wand": a.wand * 1000, "haut_innen": a.haut_innen * 1000,
               "haut_aussen": a.haut_aussen * 1000, "zelle": a.zelle * 1000, "halbdicke": a.halbdicke,
               "loecher": [] if a.ohne_platte else loecher, "rohre": rohre, "voxel": a.voxel, "ausgabe": str(o),
               "mit_platte": not a.ohne_platte, "schicht": a.schicht * 1000, "zelle_vorn": a.zelle_vorn * 1000,
               "halbdicke_vorn": a.halbdicke_vorn, "vorn_stl": str(o / "flaeche_vorn.stl") if a.schicht > 0 else None,
               "flaechen_stl": {k: str(o / f"flaeche_{k}.stl") for k in ("spalt", "haut_innen", "haut_aussen", "wand")},
               "halbdicke_vorn_R": [[float(r) * 1000, float(t)] for r, t in (z.split(":") for z in a.halbdicke_vorn_R.split(","))]
               if a.halbdicke_vorn_R else None}
    (o / "auftrag.json").write_text(json.dumps(auftrag))
    extra = {"kern_geraden_m": [L1[0].tolist(), L1[1].tolist(), L2[0].tolist(), L2[1].tolist()],
             "R_band_m": [float(np.hypot(*Xa[:, :2].T).min()), R_out]} if a.schraeg else {}
    return {**extra, "winkel_grad": {"ende0": e0, "lochblech": (p0, p1), "kern": (k0, k1), "ende1": e1},
            "R_innen_m": R_in, "R_aussen_m": R_out, "rohre": lage, "n_loecher": len(loecher)}


def bauraum(o: Path, lage: dict, a) -> dict:
    """Kleinster Abstand der Rohre (Mantel) zu Spulengehaeusen und Verbindern."""
    import pyvista as pv
    from scipy.spatial import cKDTree
    g = pv.read(PROJEKT / "sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu")
    erg = {}
    for mat, name in ((3, "spulen"), (4, "verbinder")):
        st = g.extract_cells(np.where(np.round(g.cell_data["material"]) == mat)[0]).extract_surface(algorithm="dataset_surface")
        baum = cKDTree(st.points)
        for k, r in lage["rohre"].items():
            p = np.array(r["innen_m"]) + np.linspace(0, 1, 60)[:, None] * (np.array(r["ende_m"]) - np.array(r["innen_m"]))
            d, _ = baum.query(p)
            erg[f"{k}_{name}_m"] = float(d.min() - (r["d_mm"] / 2000 + a.rohr_wand / 1000))
    return erg


def bild(o: Path, lage: dict) -> Path:
    import pyvista as pv
    s = pv.read(o / "stahl.stl").scale(1e-3); w = pv.read(o / "wasser.stl").scale(1e-3)
    pl = pv.Plotter(off_screen=True, window_size=(2000, 1000), shape=(1, 2)); pl.set_background("white")
    pl.add_mesh(s, color="#b8bec6", opacity=0.35, smooth_shading=True)
    pl.add_mesh(w, color="#2a7fd4", smooth_shading=True)
    pl.add_text("Stahl (halbtransparent) und Wasserraum", font_size=11, color="black")
    pl.subplot(0, 1)
    pl.add_mesh(w, color="#2a7fd4", smooth_shading=True, specular=0.4)
    for k, f in (("ein", "green"), ("aus", "red")):
        pl.add_mesh(pv.Sphere(radius=0.2, center=lage["rohre"][k]["ende_m"]), color=f)
    pl.add_text("Wasserraum: Eintritt gruen, Austritt rot", font_size=11, color="black")
    c = np.array(w.center); e_r = c * np.array([1, 1, 0]) / np.hypot(c[0], c[1])
    for i in (0, 1):
        pl.subplot(0, i)
        pl.camera.focal_point = c.tolist()
        pl.camera.position = (c + 16 * e_r + np.array([0, 0, 7]) + 5 * np.cross([0, 0, 1], e_r)).tolist()
        pl.camera.up = (0, 0, 1)
    p = o / "segment.png"; pl.screenshot(p); pl.close()
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="a")
    ap.add_argument("--phi0", type=float, default=85.0); ap.add_argument("--phi1", type=float, default=95.0)
    ap.add_argument("--q_MW", type=float, default=0.5, help="Waermestromdichte Plasmaseite [MW/m2]")
    ap.add_argument("--dT", type=float, default=30.0, help="Aufheizspanne Wasser [K]")
    ap.add_argument("--spalt", type=float, default=0.15); ap.add_argument("--wand", type=float, default=0.9)
    ap.add_argument("--haut_innen", type=float, default=0.03); ap.add_argument("--haut_aussen", type=float, default=0.04)
    ap.add_argument("--zelle", type=float, default=0.6); ap.add_argument("--halbdicke", type=float, default=25.0, help="mm")
    ap.add_argument("--stirn", type=float, default=40.0, help="Stirnplatte [mm, innen]")
    ap.add_argument("--kammer_ein", type=float, default=380.0, help="Verteilkammer [mm, aussen]")
    ap.add_argument("--kammer_aus", type=float, default=420.0, help="Sammelkammer [mm, aussen]")
    ap.add_argument("--platte", type=float, default=30.0, help="Lochblechdicke [mm, innen]")
    ap.add_argument("--ruhe", type=float, default=80.0, help="freier Abstand Lochblech/Sammelkammer - Gyroid [mm]")
    ap.add_argument("--d_loch", type=float, default=50.0); ap.add_argument("--n_loch", type=int, default=24)
    ap.add_argument("--reihen", type=int, default=1)
    ap.add_argument("--d_ein", type=float, default=200.0); ap.add_argument("--d_aus", type=float, default=250.0)
    ap.add_argument("--rohr_wand", type=float, default=0.012); ap.add_argument("--rohr_l", type=float, default=0.5)
    ap.add_argument("--voxel", type=float, default=12.0, help="mm")
    ap.add_argument("--max_gb", type=float, default=14.0)
    ap.add_argument("--nur_auslegung", action="store_true")
    ap.add_argument("--ohne_platte", action="store_true",
                    help="kein Lochblech: Ringkammern flaechig offen zum Gyroid-Kern (Wasser durch die Filamente)")
    ap.add_argument("--schraeg", action="store_true", help="Kern zwischen schraegen Ebenen, Kammern keilfoermig (mit --ein_innen)")
    ap.add_argument("--ein_innen", action="store_true", help="Eintrittsstutzen innen im Torus (kleinstes R)")
    ap.add_argument("--schicht", type=float, default=0.0, help="abgestufter Kern: Tiefe der feinen Schicht vorn [m]")
    ap.add_argument("--zelle_vorn", type=float, default=0.2); ap.add_argument("--halbdicke_vorn", type=float, default=10.0, help="mm")
    ap.add_argument("--halbdicke_vorn_R", default="", help="Wanddicke vorn ueber dem Radius, z. B. '5.2:6.5,7.3:4.5' (R [m]:Halbdicke [mm])")
    a = ap.parse_args(argv)
    o = WURZEL / a.name; o.mkdir(parents=True, exist_ok=True)
    if a.ohne_platte:
        a.platte = a.ruhe = 0.0                     # Kern beginnt direkt an der Ringkammer
    aus = auslegung(a)
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in aus.items()}, indent=1), flush=True)
    if a.nur_auslegung:
        return
    lage = geometrie(a, o)
    print("Winkel:", {k: [round(x, 2) for x in v] for k, v in lage["winkel_grad"].items()}, "Loecher", lage["n_loecher"], flush=True)
    r = starte_begrenzt([str(BIN), str(o / "auftrag.json")], o / "picogk.log", a.max_gb,
                        env={"DOTNET_ROOT": str(Path.home() / ".dotnet")})
    if not r["ok"]:
        raise SystemExit(f"PicoGK abgebrochen: {r['grund']} (Spitze {r['spitze_gb']:.1f} GB)")
    e = json.loads((o / "ergebnis.json").read_text())
    br = bauraum(o, lage, a)
    (o / "auslegung.json").write_text(json.dumps({"parameter": vars(a), "auslegung": aus, "lage": lage,
                                                  "bauraum_m": br, "picogk": r}, indent=1, default=float))
    print(f"Stahl {e['volumen_stahl_m3']:.2f} m3, Wasser {e['volumen_wasser_m3']:.2f} m3; {r['zeit_s']:.0f} s, "
          f"Spitze {r['spitze_gb']:.1f} GB; Bauraum {br}", flush=True)
    print(bild(o, lage))


if __name__ == "__main__":
    main()
