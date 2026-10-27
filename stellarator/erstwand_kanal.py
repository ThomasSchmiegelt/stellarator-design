"""erstwand_kanal.py — Erstwand-Kanaele fuer das Kuehlsegment: Auslegung (1D) und Temperaturfeld im Querschnitt (Elmer).

    .venv/bin/python -m stellarator.erstwand_kanal [--name k1] [--b 10] [--h 10] [--steg 4] [--haut 5] [--rueck 5]
                                                  [--q 0.5] [--dT 10] [--T_ein 290] [--druck 15.5]
                                                  [--durchgaenge 1] [--drossel] [--ohne_elmer]

Aufbau von der Plasmaseite nach aussen: Innenhaut (haut) | Kanaele b x h, getrennt durch Stege (steg) | Rueckwand
(rueck) | Gyroid-Kern (traegt nur). Die Kanaele laufen toroidal ueber das Segment (85-95 Grad) von der Verteil- zur
Sammelkammer; Laenge = R * 10 Grad, Anzahl = Umfang des Querschnitts / Teilung (b + steg).

1D: Stoffwerte von Wasser bei mittlerer Wassertemperatur, Siedetemperatur aus dem Druck; --durchgaenge: so viele
benachbarte Kanaele in Reihe (Kehre an der Stirnseite), hoehere Geschwindigkeit bei kleinem Massenstrom; Massenstrom aus q * Flaeche / (cp dT); alle
Kanaele mit gleichem Druckverlust (parallel) -> v je Laenge; Waermeuebergang Gnielinski, Reibung Petukhov.
2D (Elmer, HeatSolve): halbe Teilung (Steg-Mitte bis Kanal-Mitte, Symmetrie), Plasmaseite Waermestrom q, Kanalwand
Waermeuebergang h bei Wasser-Austrittstemperatur, Rueckseite adiabat (konservativ). Ergebnis: hoechste
Stahltemperatur und hoechste Temperatur der Kanalwand (Vergleich mit Siedetemperatur 345 Grad C).
Ausgabe sim/erstwand/<name>/: auslegung.json, querschnitt.png. Grob, ohne Volumenwaerme aus Neutronen.
"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np

from .kuehlung_segment import rand_bei
from .lauf import PROJEKT

WURZEL = PROJEKT / "sim" / "erstwand"
# Wasser fluessig (Druckeinfluss auf die Stoffwerte vernachlaessigt): T [C], rho, cp, mu, k
STOFF = np.array([[40, 992.2, 4179, 6.53e-4, 0.631], [60, 983.2, 4185, 4.67e-4, 0.654], [100, 958.4, 4216, 2.82e-4, 0.679],
                  [150, 917.0, 4310, 1.83e-4, 0.682], [200, 865.0, 4497, 1.35e-4, 0.665], [250, 799.0, 4870, 1.06e-4, 0.618],
                  [300, 732.0, 5380, 9.1e-5, 0.570]])
SIEDE = np.array([[0.5, 151.8], [1.0, 179.9], [1.5, 198.3], [2.0, 212.4], [3.0, 233.9], [5.0, 263.9], [10.0, 311.0],
                  [15.5, 344.8]])          # Saettigung: Druck [MPa], Temperatur [C]
K_STAHL = 25.0                  # warmfester Stahl [W/mK]
RHO = CP = MU = K_W = PR = None


def stoffwerte(T):
    global RHO, CP, MU, K_W, PR
    RHO, CP, MU, K_W = (float(np.interp(T, STOFF[:, 0], STOFF[:, i])) for i in range(1, 5))
    PR = CP * MU / K_W


def gnielinski(re):
    f = (0.790 * np.log(re) - 1.64) ** -2
    return (f / 8) * (re - 1000) * PR / (1 + 12.7 * np.sqrt(f / 8) * (PR ** (2 / 3) - 1)), f


def umfang(spalt=0.15, phi=90.0):
    X, N = rand_bei(phi, n_th=1440)
    Y = X + spalt * N
    return float(np.linalg.norm(np.diff(np.vstack([Y, Y[:1]]), axis=0), axis=1).sum()), np.hypot(Y[:, 0], Y[:, 1])


def t_siede(a):
    return float(np.interp(a.druck, SIEDE[:, 0], SIEDE[:, 1]))


def auslegung(a):
    stoffwerte(a.T_ein + a.dT / 2)
    U, R = umfang()
    p = (a.b + a.steg) / 1000; n = int(U / p)
    A_k = a.b * a.h / 1e6; d_h = 2 * a.b * a.h / (a.b + a.h) / 1000
    L1 = R * np.radians(10.0)                      # Segmentbreite je Lage am Umfang
    P = a.q * 1e6 * U * L1.mean()                  # Waermelast (Plasmaseite) [W]
    m = P / (CP * a.dT); Q = m / RHO
    nd = int(a.durchgaenge); n //= nd; L = L1 * nd  # nd benachbarte Kanaele in Reihe (Kehre an der Stirnseite)
    # gleicher Druckverlust in allen Kanaelen: v ~ L^-1/2 (f fast konstant), Summe = Q
    # ohne Drossel: gleicher Druckverlust -> v ~ L^-1/2; mit Drossel (--drossel): gleiche Erwaermung -> v ~ L
    w = L if a.drossel else L ** -0.5; v = Q / (n * A_k) * w / w.mean()
    re = RHO * v * d_h / MU; nu, f = gnielinski(re)
    h = nu * K_W / d_h
    dp = f * L / d_h * RHO * v ** 2 / 2
    dp_ges = dp.max() if a.drossel else dp.mean()       # mit Drossel: kuerzere Kanaele bekommen den Rest als Blende
    # Erwaermung je Kanal: Waerme q * p * L auf m_k = rho v A
    dT_k = a.q * 1e6 * p * nd * L1 / (RHO * v * A_k * CP)
    return {"umfang_m": U, "teilung_m": p, "kanaele": n, "laenge_m": [float(L.min()), float(L.max())],
            "waermelast_MW": P / 1e6, "massenstrom_kg_s": m, "volumenstrom_m3_s": Q,
            "v_m_s": [float(v.min()), float(v.mean()), float(v.max())], "Re_min": float(re.min()),
            "h_W_m2K": [float(h.min()), float(h.mean())], "dp_kPa": float(dp_ges / 1e3),
            "dT_kanal_K": [float(dT_k.min()), float(dT_k.max())], "d_h_m": d_h,
            "stoffwerte": {"T_C": a.T_ein + a.dT / 2, "rho": RHO, "cp": CP, "mu": MU, "k": K_W, "Pr": PR},
            "siedetemperatur_C": t_siede(a), "durchgaenge": nd}


SIF = """Header
  Mesh DB "." "netz"
End
Simulation
  Coordinate System = Cartesian 2D
  Simulation Type = Steady state
  Steady State Max Iterations = 1
  Output Intervals = 1
  Post File = "ergebnis.vtu"
End
Body 1
  Equation = 1
  Material = 1
End
Material 1
  Heat Conductivity = {k}
  Density = 7800.0
End
Equation 1
  Active Solvers(1) = 1
End
Solver 1
  Equation = Heat Equation
  Procedure = "HeatSolve" "HeatSolver"
  Variable = Temperature
  Linear System Solver = Direct
  Linear System Direct Method = UMFPack
  Nonlinear System Max Iterations = 1
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Heat Flux = {q}
End
Boundary Condition 2
  Target Boundaries(1) = 2
  Heat Transfer Coefficient = {h}
  External Temperature = {Tw}
End
"""


def querschnitt(a, h, T_w, o: Path) -> dict:
    """Halbe Teilung mit gmsh vernetzen, Elmer rechnen, Temperaturen auswerten (Einheiten m, Grad C)."""
    import gmsh
    s, b, hk, st, r = (x / 1000 for x in (a.haut, a.b, a.h, a.steg, a.rueck))
    xb = st / 2 + b / 2; yt = r + hk + s
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0); gmsh.model.add("q")
    voll = gmsh.model.occ.addRectangle(0, 0, 0, xb, yt)
    loch = gmsh.model.occ.addRectangle(st / 2, r, 0, b / 2 + 1e-4, hk)
    gmsh.model.occ.cut([(2, voll)], [(2, loch)]); gmsh.model.occ.synchronize()
    oben, kanal = [], []
    for _, t in gmsh.model.getEntities(1):
        x0, y0, _, x1, y1, _ = gmsh.model.getBoundingBox(1, t)
        e = 1e-6                                   # OCC-Huellquader sind etwas aufgeweitet
        if abs(y0 - yt) < e and abs(y1 - yt) < e:
            oben.append(t)
        elif x0 >= st / 2 - e and y0 >= r - e and y1 <= r + hk + e and not (abs(x0 - xb) < e and abs(x1 - xb) < e):
            kanal.append(t)
    gmsh.model.addPhysicalGroup(1, oben, 1); gmsh.model.addPhysicalGroup(1, kanal, 2)
    gmsh.model.addPhysicalGroup(2, [e[1] for e in gmsh.model.getEntities(2)], 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", min(s, b) / 12)
    gmsh.model.mesh.generate(2); gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(o / "netz.msh")); gmsh.finalize()
    subprocess.run(["ElmerGrid", "14", "2", "netz.msh", "-out", "netz"], cwd=o, check=True, capture_output=True)
    (o / "fall.sif").write_text(SIF.format(k=K_STAHL, q=a.q * 1e6, h=h, Tw=T_w))
    subprocess.run(["ElmerSolver", "fall.sif"], cwd=o, check=True, capture_output=True)
    import pyvista as pv
    g = pv.read(str(next((o / "netz").glob("ergebnis*.vtu"))))
    T = g.point_data["temperature"]; P = g.points
    an_kanal = (P[:, 0] >= st / 2 - 1e-7) & (P[:, 1] >= r - 1e-7) & (P[:, 1] <= r + hk + 1e-7)
    an_kanal &= (np.abs(P[:, 0] - st / 2) < 1e-7) | (np.abs(P[:, 1] - r) < 1e-7) | (np.abs(P[:, 1] - r - hk) < 1e-7)
    erg = {"T_max_C": float(T.max()), "T_kanalwand_max_C": float(T[an_kanal].max()), "T_wasser_C": T_w}
    bild(g, a, o / "querschnitt.png", erg, (xb, yt, st, r, hk, b))
    return erg


def bild(g, a, datei, erg, m):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    xb, yt, st, r, hk, b = m
    P = g.points * 1000; zellen = g.cells_dict[5] if 5 in g.cells_dict else g.cells_dict[list(g.cells_dict)[0]]
    T = g.point_data["temperature"]
    # halbe Teilung spiegeln -> ganze Teilung (Steg | Kanal | Steg), dreimal nebeneinander
    pt = 2 * xb * 1000; xs, ys, Ts, ts = [], [], [], []
    for k in range(3):
        for x0 in (P[:, 0] + k * pt, (k + 1) * pt - P[:, 0]):
            ts.append(zellen + sum(len(t) for t in xs)); xs.append(x0); ys.append(P[:, 1]); Ts.append(T)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    tc = ax.tripcolor(mtri.Triangulation(np.concatenate(xs), np.concatenate(ys), np.concatenate(ts)), np.concatenate(Ts),
                      shading="gouraud", cmap="inferno")
    fig.colorbar(tc, ax=ax, label="Temperatur Stahl [°C]", shrink=0.8)
    for k in range(3):
        ax.add_patch(plt.Rectangle((k * pt + st * 500, r * 1000), b * 1000, hk * 1000, color="#7fb8e6"))
        ax.text(k * pt + pt / 2, (r + hk / 2) * 1000, f"{getattr(a, 'medium', 'Wasser')}\n{erg['T_wasser_C']:.0f} °C", ha="center", va="center", fontsize=9)
    for xp in np.linspace(pt * 0.3, pt * 2.7, 5):
        ax.annotate("", xy=(xp, yt * 1000 + 0.2), xytext=(xp, yt * 1000 + 3), arrowprops=dict(arrowstyle="->", color="#c03020"))
    ax.text(1.5 * pt, yt * 1000 + 3.4, f"Wärmestrom vom Plasma {a.q} MW/m²", ha="center", va="bottom", color="#c03020")
    ax.set_aspect("equal"); ax.set_xlabel("mm"); ax.set_ylabel("mm (0 = Rückseite zum Gyroid)")
    ax.set_ylim(-0.5, yt * 1000 + 7)
    ax.set_title(f"Erstwand-Kanäle {a.b:g}×{a.h:g} mm, Steg {a.steg:g} mm, Innenhaut {a.haut:g} mm (Elmer, Stahl k = {K_STAHL:g} W/mK)\n"
                 f"Stahl max {erg['T_max_C']:.0f} °C · Kanalwand max {erg['T_kanalwand_max_C']:.0f} °C "
                 + (f"(Sieden ab {t_siede(a):.0f} °C bei {a.druck:g} MPa)" if hasattr(a, "druck") else f"({a.medium}, {a.fall})")
                 + " · ungünstigster Kanal", fontsize=10)
    fig.tight_layout(); fig.savefig(datei, dpi=130); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="k1")
    for k, d in (("b", 10.0), ("h", 10.0), ("steg", 4.0), ("haut", 5.0), ("rueck", 5.0), ("q", 0.5), ("dT", 10.0), ("T_ein", 290.0),
                 ("druck", 15.5), ("durchgaenge", 1.0)):
        ap.add_argument(f"--{k}", type=float, default=d)
    ap.add_argument("--ohne_elmer", action="store_true")
    ap.add_argument("--drossel", action="store_true", help="Blenden: alle Kanaele gleich erwaermt")
    a = ap.parse_args(argv)
    o = WURZEL / a.name; o.mkdir(parents=True, exist_ok=True)
    e = auslegung(a)
    erg = {"parameter": vars(a), "auslegung": e}
    if not a.ohne_elmer:
        # unguenstigster Kanal: kleinstes h, Wasser am Austritt des am staerksten erwaermten Kanals
        erg["querschnitt"] = querschnitt(a, e["h_W_m2K"][0], a.T_ein + e["dT_kanal_K"][1], o)
    (o / "auslegung.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))
    print(json.dumps(erg, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
