"""gehaeuse_netz.py — Spulengehaeuse fuer die Rechnung OHNE CAD-Kern (Weg von B-015) -> Elmer-Spannung.

  .venv/bin/python -m stellarator.gehaeuse_netz stellarator/faelle/w7x_standard.json
      [--wand_innen 0.05 --wand_seite 0.05 --t_min 0.05 --t_max 0.15] [--h 0.06] [--name X] [--nur_netz]

Rechenweg parallel zum FreeCAD-Modell (stellarator/gehaeuse.py = parametrisches Add-on fuer Ansicht/CAD).
Je Spule zwei Rechteckrohre als eigene Dreiecksnetze entlang der EXAKTEN Bahn (Profil an jedem
Bahnpunkt, keine Loft-Abweichung, keine Booleschen Operationen):
  innen = Wickelpaket (br x ho, mittig auf dem Filament), aussen = Gehaeuse.
Wandstaerken je Bahnpunkt nach derselben Logik wie das CAD-Modell: aussen t_min..t_max nach |I t x B|,
seitlich wand_seite, innen wand_innen, jeweils <= halber freier Spalt zur Nachbarspule (gehaeuse.freiraum)
-> keine Kollisionen per Konstruktion. gmsh: Body 1..n Wickelpakete, n+1 Stahl (Gehaeuse = Raum
zwischen den Rohren, konform ueber das gemeinsame Wickelpaket-Netz), n+2 Luft, Boundary 1 Quader.
Lagerung: jedes Gehaeuse an einem Flecken der Aussenseite eingespannt (Anbindung an den Tragring,
r_lager um den Bahnpunkt mit groesstem Radius) — ohne Verbinder sind die Gehaeuse sonst frei.
Ausgabe sim/stellarator/gehaeuse_netz/<fall>/: Elmer-Netz, case.sif, ergebnis.json, Bild.
"""
from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path
import numpy as np
import gmsh

from . import spulen as sp, elmer, struktur, cad
from .gehaeuse import kraft_je_laenge, freiraum
from .lauf import PROJEKT


def rohr(P, n, b, rechteck, h) -> tuple[np.ndarray, np.ndarray]:
    """Geschlossenes Rechteckrohr mit veraenderlichem Querschnitt.
    rechteck (N, 4): n_min, n_max, b_min, b_max je Bahnpunkt im Rahmen (n, b). Normalen nach aussen."""
    N = len(P)
    breite = (rechteck[:, 1] - rechteck[:, 0]).max(); hoehe = (rechteck[:, 3] - rechteck[:, 2]).max()
    nb, nh = max(2, int(np.ceil(breite / h))), max(2, int(np.ceil(hoehe / h)))
    # Umfangsparameter: Seite k, Anteil u (gegen den Uhrzeigersinn wie cad.rohr_netz)
    seiten = [(k, u) for k, m in enumerate((nb, nh, nb, nh)) for u in np.linspace(0, 1, m, endpoint=False)]
    R = len(seiten)
    n0, n1, b0, b1 = (rechteck[:, i][:, None] for i in range(4))
    ecken = [(n0, b0), (n1, b0), (n1, b1), (n0, b1)]
    rn = np.hstack([ecken[k][0] + u * (ecken[(k + 1) % 4][0] - ecken[k][0]) for k, u in seiten])   # (N, R)
    rb = np.hstack([ecken[k][1] + u * (ecken[(k + 1) % 4][1] - ecken[k][1]) for k, u in seiten])
    knoten = (P[:, None] + rn[..., None] * n[:, None] + rb[..., None] * b[:, None]).reshape(-1, 3)
    i, r = np.meshgrid(np.arange(N), np.arange(R), indexing="ij")
    j, w = (i + 1) % N, (r + 1) % R
    a_, b_, c_, d_ = i * R + r, j * R + r, j * R + w, i * R + w
    dreiecke = np.concatenate([np.stack([a_, b_, c_], -1).reshape(-1, 3), np.stack([a_, c_, d_], -1).reshape(-1, 3)])
    Q = knoten[dreiecke]
    vol = np.einsum("ij,ij->i", Q[:, 0], np.cross(Q[:, 1], Q[:, 2])).sum() / 6
    return knoten, (dreiecke if vol > 0 else dreiecke[:, ::-1])


def waende(spulen, br, ho, a) -> list[dict]:
    """Wandstaerken [m] je Bahnpunkt und Spule: innen, aussen, links, rechts (+ Kraftfaktor f)."""
    seg = sp.segmente(spulen)
    f = [kraft_je_laenge(spulen, s, br, ho, seg) for s in spulen]
    fmax = max(x.max() for x in f)
    out = []
    for k, s in enumerate(spulen):
        N = len(s.punkte)
        fs = np.convolve(np.r_[f[k][-4:], f[k], f[k][:4]], np.ones(9) / 9, "valid") / fmax
        fenster = 0.5 * s.laenge() / N + 0.5 * np.hypot(br, ho)
        fr = {q: np.array(v) for q, v in freiraum(spulen, k, range(N), br, ho, a.spiel, fenster, mit_innen=True).items()}
        lauf_min = lambda x: np.min([np.roll(x, d) for d in (-2, -1, 0, 1, 2)], axis=0)   # Sprungstellen absichern
        w = {"aussen": np.minimum(a.t_min + (a.t_max - a.t_min) * fs, lauf_min(fr["aussen"])),
             "innen": np.minimum(a.wand_innen, lauf_min(fr["innen"])),
             "links": np.minimum(a.wand_seite, lauf_min(fr["links"])),
             "rechts": np.minimum(a.wand_seite, lauf_min(fr["rechts"]))}
        out.append({q: np.maximum(a.wand_min, v) for q, v in w.items()} | {"f": fs})
    return out


def rechtecke(s, w, br, ho) -> tuple[np.ndarray, np.ndarray]:
    """(innen, aussen) je Bahnpunkt als n_min, n_max, b_min, b_max."""
    N = len(s.punkte)
    innen = np.c_[np.full(N, -br / 2), np.full(N, br / 2), np.full(N, -ho / 2), np.full(N, ho / 2)]
    return innen, innen + np.c_[-w["innen"], w["aussen"], -w["links"], w["rechts"]]


def entflechten(spulen, W, br, ho, h, spiel, wand_min, runden: int = 6) -> list[int]:
    """Ecken: Oberflaechenpunkte fremder Gehaeuse, die im eigenen Gehaeuse-Rechteck liegen, nimmt die Wand
    zurueck, die dafuer am wenigsten verliert (freiraum prueft nur geradeaus -> Ecken schraeger Nachbarn).
    Rueckgabe: Anzahl eindringender Punkte je Runde (Ziel 0)."""
    from scipy.spatial import cKDTree
    rahmen = [sp.rahmen(s) for s in spulen]
    verlauf = []
    for _ in range(runden):
        kn = []
        for s, (t, n, b), w in zip(spulen, rahmen, W):
            k_ = rohr(s.punkte, n, b, rechtecke(s, w, br, ho)[1], h)[0].reshape(len(s.punkte), -1, 3)
            # Zwischenringe (1/3, 2/3): Kanten schraeg stehender Nachbarrohre kreuzen sonst zwischen den Stationen
            k2 = np.roll(k_, -1, axis=0)
            kn.append(np.concatenate([k_, (2 * k_ + k2) / 3, (k_ + 2 * k2) / 3]).reshape(-1, 3))
        alle = np.vstack(kn); wem = np.repeat(np.arange(len(kn)), [len(x) for x in kn])
        baum = cKDTree(alle)
        r_such = 0.5 * np.hypot(br, ho) + max(max(w[q].max() for q in ("innen", "aussen", "links", "rechts")) for w in W) + spiel
        n_ein = 0
        for k, (s, (t, n, b), w) in enumerate(zip(spulen, rahmen, W)):
            ds = 0.5 * s.laenge() / len(s.punkte)                     # halber Punktabstand entlang der Bahn
            for i, nah in enumerate(baum.query_ball_point(s.punkte, r_such)):
                nah = np.array([j for j in nah if wem[j] != k], dtype=int)
                if not len(nah):
                    continue
                d = alle[nah] - s.punkte[i]
                dt, dn, db = d @ t[i], d @ n[i], d @ b[i]
                g = np.abs(dt) < ds
                dn, db = dn[g], db[g]
                grenze = {"aussen": dn - br / 2 - spiel, "innen": -dn - br / 2 - spiel,
                          "rechts": db - ho / 2 - spiel, "links": -db - ho / 2 - spiel}
                drin = ((dn > -br / 2 - w["innen"][i] - spiel) & (dn < br / 2 + w["aussen"][i] + spiel)
                        & (db > -ho / 2 - w["links"][i] - spiel) & (db < ho / 2 + w["rechts"][i] + spiel))
                for p in np.where(drin)[0]:
                    # Kandidaten: Waende, deren Rueckzug den Punkt frei macht (Grenze >= wand_min)
                    opt = [(w[q][i] - grenze[q][p], q) for q in grenze if grenze[q][p] >= wand_min - 1e-12]
                    if not opt:
                        continue                                        # Punkt im Wickelpaket-Band: nicht loesbar
                    _, q = min(opt)
                    for j in (i - 1, i, i + 1):                       # Nachbarstationen mit: Rohr ist zwischen
                        j %= len(s.punkte)                            # den Stationen linear (keine Zacken)
                        w[q][j] = min(w[q][j], grenze[q][p])
                    n_ein += 1
        verlauf.append(n_ein)
        if n_ein == 0:
            break
    return verlauf


def netz(spulen, W, br, ho, ordner: Path, h: float, h_luft: float, rand_m: float, dist_max: float) -> dict:
    ordner.mkdir(parents=True, exist_ok=True)
    n = len(spulen)
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 1)
    try:
        t0 = time.time(); m = gmsh.model; geo = m.geo
        versatz, f_wp, f_geh, lager_pkt = 1, [], [], []
        for s, w in zip(spulen, W):
            t, nv, bv = sp.rahmen(s)
            innen, aussen = rechtecke(s, w, br, ho)
            for rechteck, liste in ((innen, f_wp), (aussen, f_geh)):
                kn, tri = rohr(s.punkte, nv, bv, rechteck, h)
                e = m.addDiscreteEntity(2)
                m.mesh.addNodes(2, e, np.arange(versatz, versatz + len(kn)), kn.ravel())
                m.mesh.addElementsByType(e, 2, [], (tri + versatz).ravel())
                versatz += len(kn); liste.append(e)
            # Lagerpunkt: Mitte der Aussenseite am Bahnpunkt mit groesstem Radius (Tragring aussen)
            i = int(np.argmax(np.hypot(s.punkte[:, 0], s.punkte[:, 1])))
            lager_pkt.append(s.punkte[i] + nv[i] * (br / 2 + w["aussen"][i]))
        P = np.concatenate([s.punkte for s in spulen])
        lo, hi = P.min(0) - rand_m, P.max(0) + rand_m
        pk = [geo.addPoint(x, y, z, h_luft) for z in (lo[2], hi[2]) for y in (lo[1], hi[1]) for x in (lo[0], hi[0])]
        L = lambda a_, b_: geo.addLine(pk[a_], pk[b_])
        e = {k: L(*k) for k in [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]}
        def seite(a_, b_, c_, d_):
            kanten = [(a_, b_), (b_, c_), (c_, d_), (d_, a_)]
            return geo.addPlaneSurface([geo.addCurveLoop([e[k] if k in e else -e[k[::-1]] for k in kanten])])
        box = [seite(0, 1, 3, 2), seite(4, 6, 7, 5), seite(0, 4, 5, 1), seite(2, 3, 7, 6), seite(0, 2, 6, 4), seite(1, 5, 7, 3)]
        sl_wp = [geo.addSurfaceLoop([x]) for x in f_wp]
        sl_geh = [geo.addSurfaceLoop([x]) for x in f_geh]
        v_wp = [geo.addVolume([x]) for x in sl_wp]
        v_geh = [geo.addVolume([a_, b_]) for a_, b_ in zip(sl_geh, sl_wp)]        # Gehaeuse = aussen ohne WP
        v_luft = geo.addVolume([geo.addSurfaceLoop(box)] + sl_geh)
        geo.synchronize()
        for i, v in enumerate(v_wp):
            m.addPhysicalGroup(3, [v], i + 1, name=spulen[i].name)
        m.addPhysicalGroup(3, v_geh, n + 1, name="stahl")
        m.addPhysicalGroup(3, [v_luft], n + 2, name="luft")
        m.addPhysicalGroup(2, box, 1, name="aussen")
        f1 = m.mesh.field.add("Distance"); m.mesh.field.setNumbers(f1, "SurfacesList", f_geh)
        f2 = m.mesh.field.add("Threshold"); m.mesh.field.setNumber(f2, "InField", f1)
        for k, v in {"SizeMin": h, "SizeMax": h_luft, "DistMin": 0.0, "DistMax": dist_max}.items():
            m.mesh.field.setNumber(f2, k, v)
        m.mesh.field.setAsBackgroundMesh(f2)
        for k in ("MeshSizeExtendFromBoundary", "MeshSizeFromPoints", "MeshSizeFromCurvature"):
            gmsh.option.setNumber(f"Mesh.{k}", 0)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        t_geo = time.time() - t0
        m.mesh.generate(3)
        n_tet = sum(len(x) for x in m.mesh.getElements(3)[1])
        gmsh.write(str(ordner / "netz.msh"))
        t_netz = time.time() - t0
    finally:
        gmsh.finalize()
    subprocess.run(["ElmerGrid", "14", "2", "netz.msh", "-autoclean"], cwd=ordner, check=True, capture_output=True)
    (ordner / "netz.msh").unlink()
    return {"n_tet": n_tet, "t_geometrie_s": t_geo, "t_netz_s": t_netz,
            "bodies": {"wickelpakete": [1, n], "stahl": n + 1, "luft": n + 2}}, np.array(lager_pkt)


def lager_flecken(ordner: Path, body_stahl: int, punkte: np.ndarray, r: float) -> list[list[int]]:
    """Stahlknoten im Umkreis r um jeden Lagerpunkt (je Spule ein eingespannter Flecken)."""
    from scipy.spatial import cKDTree
    kn = np.loadtxt(ordner / "netz" / "mesh.nodes")
    ids = set()
    with open(ordner / "netz" / "mesh.elements") as f:
        for z in f:
            w = z.split()
            if int(w[1]) == body_stahl:
                ids.update(map(int, w[3:]))
    sel = kn[np.isin(kn[:, 0].astype(int), list(ids))]
    baum = cKDTree(sel[:, 2:5])
    out = []
    for p in punkte:
        k = baum.query_ball_point(p, r)
        if len(k) < 3:
            k = list(baum.query(p, 3)[1])
        out.append(sorted(int(sel[i, 0]) for i in k))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gehaeuse ohne CAD-Kern (Rohrnetze) -> Elmer-Spannung")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--wand_innen", type=float, default=0.1)
    ap.add_argument("--wand_seite", type=float, default=0.1)
    ap.add_argument("--t_min", type=float, default=0.15)
    ap.add_argument("--t_max", type=float, default=0.5)
    ap.add_argument("--spiel", type=float, default=0.01)
    ap.add_argument("--wand_min", type=float, default=0.003)
    ap.add_argument("--h", type=float, default=0.06, help="Netzweite an Gehaeuse und Wickelpaket [m]")
    ap.add_argument("--h_luft", type=float, default=1.5)
    ap.add_argument("--dist_max", type=float, default=3.0)
    ap.add_argument("--rand", type=float, default=5.0)
    ap.add_argument("--r_lager", type=float, default=0.25, help="Radius des eingespannten Fleckens je Gehaeuse [m]")
    ap.add_argument("--mit_swap", action="store_true")
    ap.add_argument("--name")
    ap.add_argument("--nur_netz", action="store_true")
    ap.add_argument("--nur_auswerten", action="store_true")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text()); c = fall["spulen"]
    kz_pfad = PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"] / "kennzahlen.json"
    if not kz_pfad.exists():
        raise SystemExit(f"zuerst: .venv/bin/python -m stellarator.bewerte {a.fall}")
    kz = json.loads(kz_pfad.read_text())
    spulen, _ = sp.lade_spulensatz(c)
    for s in spulen:
        s.strom *= kz["strom"]["kalibrierfaktor"]
        s.punkte = cad.neu_abtasten(s.punkte, max(60, int(np.ceil(s.laenge() / a.h))))
    br, ho = c["wickel_breite_m"], c["wickel_hoehe_m"]
    n = len(spulen)
    ordner = PROJEKT / "sim" / "stellarator" / "gehaeuse_netz" / (a.name or fall["name"]); ordner.mkdir(parents=True, exist_ok=True)
    erg_pfad = ordner / "ergebnis.json"
    erg = json.loads(erg_pfad.read_text()) if erg_pfad.exists() else {}
    erg |= {"fall": fall["name"], "parameter": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()},
            "material": {"stahl": struktur.STAHL, "wickelpaket": struktur.WP}}
    if not a.nur_auswerten:
        t0 = time.time()
        W = waende(spulen, br, ho, a)
        erg["waende_mm"] = {q: {"min": float(min(w[q].min() for w in W) * 1e3), "mittel": float(np.mean([w[q].mean() for w in W]) * 1e3),
                                "max": float(max(w[q].max() for w in W) * 1e3)} for q in ("innen", "aussen", "links", "rechts")}
        erg["waende_an_wand_min"] = int(sum((w[q] <= a.wand_min + 1e-9).sum() for w in W for q in ("innen", "aussen", "links", "rechts")))
        erg["entflechten_eindringend_je_runde"] = entflechten(spulen, W, br, ho, a.h, a.spiel, a.wand_min)
        erg["waende_mm"] = {q: {"min": float(min(w[q].min() for w in W) * 1e3), "mittel": float(np.mean([w[q].mean() for w in W]) * 1e3),
                                "max": float(max(w[q].max() for w in W) * 1e3)} for q in ("innen", "aussen", "links", "rechts")}
        print("WAENDE", json.dumps(erg["waende_mm"]), "entflechten", erg["entflechten_eindringend_je_runde"],
              f"{time.time() - t0:.0f}s", flush=True)
        erg["netz"], lp = netz(spulen, W, br, ho, ordner, a.h, a.h_luft, a.rand, a.dist_max)
        flecken = lager_flecken(ordner, n + 1, lp, a.r_lager)
        erg["lager_knoten_je_spule"] = [len(x) for x in flecken]
        struktur.schreibe_sif(spulen, br, ho, ordner, [], luft=("luft",))
        with open(ordner / "case.sif", "a") as f:
            for k, ids in enumerate(flecken, 2):
                f.write(f"Boundary Condition {k}\n  Target Nodes({len(ids)}) = {' '.join(map(str, ids))}\n"
                        "  Displacement 1 = Real 0.0\n  Displacement 2 = Real 0.0\n  Displacement 3 = Real 0.0\nEnd\n")
        bedarf = erg["netz"]["n_tet"] * elmer.KB_PRO_TET * 1.3 / 1e6
        mi = {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}
        frei = mi["MemAvailable"] + (0.5 * mi["SwapFree"] if a.mit_swap else 0.0)
        erg["ram_schaetzung_GB"] = {"bedarf": bedarf, "frei": frei}
        erg_pfad.write_text(json.dumps(erg, indent=2, ensure_ascii=False))
        print("NETZ", json.dumps(erg["netz"]), erg["ram_schaetzung_GB"], flush=True)
        if a.nur_netz:
            return
        if bedarf > 0.85 * frei:
            raise SystemExit(f"ABBRUCH: Elmer braucht ~{bedarf:.1f} GB, frei {frei:.1f} GB -> --h groesser")
        t0 = time.time()
        with open(ordner / "solve.log", "w") as f:
            subprocess.run(["ElmerSolver", "case.sif"], cwd=ordner, stdout=f, stderr=subprocess.STDOUT, check=True)
        erg["t_elmer_s"] = time.time() - t0
    erg["ergebnis"] = struktur.auswerten(ordner, spulen, br, ho, kz)
    erg["ergebnis"]["schale"]["bauteil"] = "Gehaeuse (Rohrnetz, je Spule am Tragring eingespannt)"
    erg_pfad.write_text(json.dumps(erg, indent=2, ensure_ascii=False))
    struktur.bild(ordner, n, erg["ergebnis"], titel="Gehaeuse (Rechenweg ohne CAD)")
    print("FERTIG", ordner, json.dumps({k: erg["ergebnis"][k] for k in ("wickelpakete", "schale", "kraft_summe_MN")}))


if __name__ == "__main__":
    main()
