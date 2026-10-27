"""kuehlung_erstwand.py — Kuehlsegment, Variante "Erstwand-Spalt": Wasser stroemt durch einen schmalen Spalt direkt
hinter der Plasmaseite; der Gyroid-Kern dahinter bleibt geschlossene Tragstruktur (keine Durchstroemung).

    .venv/bin/python -m stellarator.kuehlung_erstwand [--name e1] [--spaltweite 40] [--dT 10] [--n_loch 34]

Grund (Lauf b, kuehlung_segment.py): Bei Durchstroemung des ganzen 0,9-m-Kerns liegt die Geschwindigkeit an der
Plasmaseite bei ~4 cm/s, der Waermeuebergang reicht fuer 0,5 MW/m2 nicht.
Toroidal (von phi0): Stirnplatte | Verteilkammer (Eintrittsrohr) | Lochblech (1 Reihe in Vorkammertiefe) |
Vorkammer (nur vorderer Wandbereich) | Erstwand-Spalt ... | Sammelkammer (Austrittsrohr) | Stirnplatte.
Radial (vom Plasmarand): Spalt zur Wand | Innenhaut | Wasserspalt | Trennblech | Gyroid-Kern (zu) | Aussenhaut.
Ausgabe sim/kuehlung_segment/<name>/ wie kuehlung_segment.py (dort laufen auch kuehlung_cfd und auswerten).
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

from .lauf import PROJEKT
from .gyroid_gefaess import randflaeche, sektor_stl, keil_stl
from .kuehlung_segment import WURZEL, auslegung, rand_bei, schnitt_ebene, bogen_gleich, bauraum, bild
from .speicherwaechter import starte_begrenzt

BIN = PROJEKT / "picogk" / "SegmentErstwand" / "bin" / "Release" / "net9.0" / "SegmentErstwand"


def geometrie(a, o: Path) -> dict:
    X = randflaeche(n_th=192, n_ph=1440)
    sektor_stl(X * 1000, a.phi0 - 3, a.phi1 + 3, o / "plasma.stl")
    km = 0.5 * (a.phi0 + a.phi1)
    R_in = float(np.hypot(*schnitt_ebene(km, a.spalt)[:, :2].T).min())
    R_out = float(np.hypot(*schnitt_ebene(km, a.spalt + a.wand)[:, :2].T).max())
    g = lambda mm, R: np.degrees(mm / 1000 / R)
    e0 = a.phi0 + g(a.stirn, R_in); e1 = a.phi1 - g(a.stirn, R_in)
    p0 = e0 + g(a.kammer_ein, R_out); p1 = p0 + g(a.platte, R_in)
    a0 = e1 - g(a.kammer_aus, R_out)                                    # Beginn Sammelkammer
    v1 = p1 + g(a.vor_laenge, R_out)
    keile = {"segment": (a.phi0, a.phi1), "kin": (e0, p0 + 0.02), "platte": (p0 - 0.02, p1 + 0.02),
             "vor": (p1 - 0.02, v1), "spalt": (p1 - 0.02, a0 + 0.02), "kern": (p1 + g(a.dicht, R_in), a0 - g(a.dicht, R_in)),
             "kaus": (a0, e1)}
    R_max = (float(np.hypot(X[..., 0], X[..., 1]).max()) + a.spalt + a.wand + 1.5) * 1000
    Z_max = (float(np.abs(X[..., 2]).max()) + a.spalt + a.wand + 1.5) * 1000
    for k, (w0, w1) in keile.items():
        keil_stl(w0, w1, R_max, Z_max, o / f"keil_{k}.stl")
    pm = 0.5 * (p0 + p1); e_phi = np.array([-np.sin(np.radians(pm)), np.cos(np.radians(pm)), 0.0])
    loecher = []
    d_je = json.loads(Path(a.loch_d).read_text()) if a.loch_d else [a.d_loch] * a.n_loch    # je Loch abgestuft
    for c, d in zip(bogen_gleich(schnitt_ebene(pm, a.spalt + a.haut_innen + a.loch_tiefe / 1000), a.n_loch), d_je):
        L = (np.radians(p1 - p0 + 0.04) * np.hypot(c[0], c[1]) + 0.06) / 2
        loecher.append([*((c - L * e_phi) * 1000), *((c + L * e_phi) * 1000), d / 2])
    tief = a.wand - a.haut_innen - a.haut_aussen
    rohre, lage = [], {}
    for name, ph, d in (("ein", 0.5 * (e0 + p0), a.d_ein), ("aus", 0.5 * (a0 + e1), a.d_aus)):
        Pa = schnitt_ebene(ph, a.spalt + a.haut_innen + 0.5 * tief); Pb = schnitt_ebene(ph, a.spalt + a.wand + a.rohr_l)
        i = int(np.argmax(np.hypot(Pb[:, 0], Pb[:, 1])))
        n = (Pb[i] - Pa[i]) / np.linalg.norm(Pb[i] - Pa[i])
        rohre.append([*(Pa[i] * 1000), *(Pb[i] * 1000), d / 2, a.rohr_wand])
        lage[name] = {"phi_grad": ph, "innen_m": Pa[i].tolist(), "ende_m": Pb[i].tolist(), "achse": n.tolist(), "d_mm": d}
    mm = lambda m: m * 1000
    d_spalt = a.spalt + a.haut_innen + a.spaltweite / 1000
    auftrag = {"plasma_stl": str(o / "plasma.stl"), "d_innen": mm(a.spalt), "d_aussen": mm(a.spalt + a.wand),
               "d_haut_i": mm(a.spalt + a.haut_innen), "d_haut_a": mm(a.spalt + a.wand - a.haut_aussen),
               "d_spalt": mm(d_spalt), "d_vor": mm(a.spalt + a.haut_innen) + a.vor_tiefe,
               "d_kern": mm(d_spalt) + a.trenn, "d_vor_kern": mm(a.spalt + a.haut_innen) + a.vor_tiefe + a.trenn,
               "zelle": mm(a.zelle), "halbdicke": a.halbdicke, "loecher": loecher, "rohre": rohre, "voxel": a.voxel,
               "ausgabe": str(o)}
    (o / "auftrag.json").write_text(json.dumps(auftrag))
    # "kern" = Auswertebereich fuer kuehlung_cfd.auswerten (hier: Erstwand-Spalt hinter der Vorkammer)
    return {"winkel_grad": {"verteilkammer": (e0, p0), "lochblech": (p0, p1), "vorkammer": (p1, v1),
                            "kern": (v1, a0), "sammelkammer": (a0, e1)},
            "R_innen_m": R_in, "R_aussen_m": R_out, "rohre": lage, "n_loecher": len(loecher), "variante": "erstwand"}


def abstufen(von: str, d_min: float = 45.0, d_max: float = 90.0) -> Path:
    """Neue Lochdurchmesser aus den gemessenen Lochvolumenstroemen eines Laufs: d_neu = d * sqrt(Q_mittel / Q_loch),
    gleiche Gesamtflaeche, begrenzt auf [d_min, d_max]. Schreibt <von>/loch_d_neu.json."""
    o = WURZEL / von
    q = np.array(json.loads((o / "cfd" / "auswertung.json").read_text())["loecher"]["Q_m3_s"])
    d = 2 * np.array(json.loads((o / "auftrag.json").read_text())["loecher"])[:, 6]
    neu = d * np.sqrt(q.mean() / q)
    neu *= np.sqrt((d ** 2).sum() / (neu ** 2).sum())
    for _ in range(5):                                 # Grenzen einhalten, Flaeche nachfuehren
        neu = np.clip(neu, d_min, d_max); neu *= np.sqrt((d ** 2).sum() / (neu ** 2).sum())
    p = o / "loch_d_neu.json"; p.write_text(json.dumps(np.round(neu, 1).tolist()))
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="e1")
    ap.add_argument("--phi0", type=float, default=85.0); ap.add_argument("--phi1", type=float, default=95.0)
    ap.add_argument("--q_MW", type=float, default=0.5); ap.add_argument("--dT", type=float, default=10.0)
    ap.add_argument("--spalt", type=float, default=0.15); ap.add_argument("--wand", type=float, default=0.9)
    ap.add_argument("--haut_innen", type=float, default=0.01, help="Erstwand plasmaseitig [m]")
    ap.add_argument("--haut_aussen", type=float, default=0.04)
    ap.add_argument("--spaltweite", type=float, default=40.0, help="Erstwand-Wasserspalt [mm]")
    ap.add_argument("--trenn", type=float, default=15.0, help="Trennblech Spalt/Kern [mm]")
    ap.add_argument("--vor_tiefe", type=float, default=150.0, help="Vorkammer radial [mm]")
    ap.add_argument("--vor_laenge", type=float, default=150.0, help="Vorkammer toroidal [mm, aussen]")
    ap.add_argument("--loch_tiefe", type=float, default=75.0, help="Lochmitte hinter der Innenhaut [mm]")
    ap.add_argument("--dicht", type=float, default=20.0, help="Abschluss des Kernhohlraums [mm]")
    ap.add_argument("--zelle", type=float, default=0.6); ap.add_argument("--halbdicke", type=float, default=25.0)
    ap.add_argument("--stirn", type=float, default=40.0)
    ap.add_argument("--kammer_ein", type=float, default=480.0); ap.add_argument("--kammer_aus", type=float, default=520.0)
    ap.add_argument("--platte", type=float, default=30.0)
    ap.add_argument("--d_loch", type=float, default=60.0); ap.add_argument("--n_loch", type=int, default=34)
    ap.add_argument("--reihen", type=int, default=1)
    ap.add_argument("--loch_d", default="", help="JSON-Liste der Lochdurchmesser [mm] je Loch (Abstufung)")
    ap.add_argument("--d_ein", type=float, default=350.0); ap.add_argument("--d_aus", type=float, default=400.0)
    ap.add_argument("--rohr_wand", type=float, default=0.015); ap.add_argument("--rohr_l", type=float, default=0.5)
    ap.add_argument("--voxel", type=float, default=10.0)
    ap.add_argument("--max_gb", type=float, default=14.0)
    a = ap.parse_args(argv)
    o = WURZEL / a.name; o.mkdir(parents=True, exist_ok=True)
    if a.loch_d:                       # fuer die Auslegung: Durchmesser gleicher Gesamtflaeche
        d_je = np.array(json.loads(Path(a.loch_d).read_text())); a.n_loch = len(d_je)
        a.d_loch = float(np.sqrt((d_je ** 2).mean()))
    aus = auslegung(a)
    # Spaltgeschwindigkeit und Waermeuebergang (heisses Druckwasser ~300 C: nu 1,2e-7, k 0,56, Pr 0,86)
    U = aus["flaeche_plasmaseite_m2"] / (np.radians(a.phi1 - a.phi0) * 10.4)    # Umfang grob
    v_sp = aus["volumenstrom_m3_s"] / (U * a.spaltweite / 1000)
    Dh = 2 * a.spaltweite / 1000; Re = v_sp * Dh / 1.2e-7
    h = 0.023 * Re ** 0.8 * 0.86 ** 0.4 * 0.56 / Dh
    aus |= {"umfang_m": U, "v_spalt_m_s": v_sp, "Re_spalt_heiss": Re, "h_W_m2K": h, "dT_wand_K": a.q_MW * 1e6 / h}
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in aus.items()}, indent=1), flush=True)
    lage = geometrie(a, o)
    print("Winkel:", {k: [round(float(x), 2) for x in v] for k, v in lage["winkel_grad"].items()}, flush=True)
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
