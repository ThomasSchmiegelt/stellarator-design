"""gradient_waerme.py — Wie verteilt die abgestufte Gyroid-Wand (picogk/GradientWand) die Waerme in die Breite und Tiefe?

    .venv/bin/python -m stellarator.gradient_waerme [--voxel 0.5] [--L 80] [--tiefe 100] [--h 1e4] [--q 5e5]

Frage des Nutzers (2026-10-28): wie bekommen wir die Waerme in die Breite und leiten den Waermefluss nach aussen?
Modell: Ausschnitt L x L x tiefe der Wand g1 (gleiche Lagen und Ueberblendung wie GradientWand/Program.cs,
Ausrundung 1,5 mm als morphologisches Schliessen), Stahl als Voxel-Hexaeder (Elmer HeatSolve, stationaer).
Plasmaseite z = 0: Waermestrom q (Erstwand), Fall "fleck": Kreis Radius 10 mm in der Mitte mit 2 q.
Benetzte Flaechen: Waermeuebergang h ins Wasser T_w (Druckwasser im Mittel 304 C). Die Treppenflaeche der Voxel ist
groesser als die glatte Flaeche (Faktor |nx| + |ny| + |nz|, Normale aus dem Abstandsfeld), h wird darum je Flaeche
durch diesen Faktor geteilt. Seiten und Schnitt hinten (z = tiefe) adiabat (Struktur periodisch mit 80 mm).
Fall "wolfram": zusaetzlich 3 mm Wolfram vor der Haut (Panzerung wie DEMO), Waermestrom auf die Wolframseite.
Gegenproben mit Fleck: "kupfer" (Haut und Struktur k = 320 wie CuCrZr am Divertor), "h_doppelt" (schnelleres Wasser).
Auswertung: hoechste Temperatur Plasmaseite und benetzte Wand (Siedegrenze 344,8 C bei 16 MPa), abgegebene Waerme je
Tiefe, seitliche Ausbreitung (Waermeabgabe je Spalte x, y gegen Einstrahlung). Ausgabe sim/gradient_waerme/.
Naeherungen: k konstant (Stahl 25, Wolfram 130 W/mK, grobe Werte), h ueberall gleich (keine Stroemungsrechnung),
keine Neutronen-Volumenwaerme, Voxelnetz (Treppen), Seiten adiabat statt periodisch.
"""
import argparse, json, shutil, subprocess
from pathlib import Path
import numpy as np

from .lauf import PROJEKT

WURZEL = PROJEKT / "sim" / "gradient_waerme"
# Lagen wie picogk/GradientWand/Program.cs: Zelle a, Wanddicke t, Lagenende z [mm]
ZELLE, DICKE, ENDE = (20, 40, 80, 160), (2.5, 3.0, 4.5, 8.0), (30, 80, 180, 600)
HAUT, RUND = 5.0, 1.5
K_STAHL, K_WOLFRAM, T_WASSER, T_SIEDEN = 25.0, 130.0, 304.0, 344.8
# Fall: (Fleck, Wolframschicht, k der Struktur W/mK, Faktor auf h)
FAELLE = {"gleich": (False, False, K_STAHL, 1.0), "fleck": (True, False, K_STAHL, 1.0),
          "wolfram": (True, True, K_STAHL, 1.0), "kupfer": (True, False, 320.0, 1.0), "h_doppelt": (True, False, K_STAHL, 2.0)}


TITEL = {"gleich": "Stahl, gleichmäßig", "fleck": "Stahl, Fleck 2 q", "wolfram": "3 mm Wolfram + Stahl, Fleck",
         "kupfer": "Kupferlegierung, Fleck", "h_doppelt": "Stahl, Fleck, h doppelt"}


def lage(X, Y, Z, a, t):
    k = 2 * np.pi / a; x, y, z = X * k, Y * k, Z * k
    g = np.sin(x) * np.cos(y) + np.sin(y) * np.cos(z) + np.sin(z) * np.cos(x)
    return np.abs(g) / (1.5 * k) - t / 2


def glatt(u):
    u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)


def abstand(X, Y, Z):
    """Abstandsfeld GyroidGestuft (Program.cs), vektorisiert."""
    D = [lage(X, Y, Z, a, t).astype(np.float32) for a, t in zip(ZELLE, DICKE)]
    i = np.searchsorted(np.array(ENDE[:-1]), Z, side="left")
    d = np.choose(i, D)
    for j in range(len(ENDE) - 1):                               # Uebergang Lage j -> j+1
        h = 0.75 * ZELLE[j]; s = glatt((Z - (ENDE[j] - h / 2)) / h)
        nach = (i == j) & (s > 0); d[nach] = ((1 - s) * D[j] + s * D[j + 1])[nach]
        vor = (i == j + 1) & (s < 1); d[vor] = ((1 - s) * D[j] + s * d)[vor]
    return d


def geometrie(L, tiefe, dx, n_w):
    from scipy import ndimage
    n, nz = int(round(L / dx)), int(round(tiefe / dx))
    c = (np.arange(n) + 0.5) * dx; cz = (np.arange(nz) + 0.5) * dx
    X, Y, Z = np.meshgrid(c, c, cz, indexing="ij")
    d = abstand(X, Y, Z)
    stahl = (Z < HAUT) | ((Z >= HAUT - 1) & (d <= 0))
    r = int(round(RUND / dx))
    if r > 0:                                                    # Ausrundung: Schliessen, seitlich periodisch
        kugel = np.sum((np.indices((2 * r + 1,) * 3) - r) ** 2, 0) <= r * r
        p = np.pad(stahl, ((r, r), (r, r), (0, 0)), mode="wrap"); p = np.pad(p, ((0, 0), (0, 0), (r, r)), mode="edge")
        stahl = ndimage.binary_closing(p, kugel)[r:-r, r:-r, r:-r]
    g = np.stack(np.gradient(d, dx), -1); g /= np.maximum(np.linalg.norm(g, axis=-1, keepdims=True), 1e-9)
    faktor = np.abs(g).sum(-1); faktor[Z < HAUT] = 1.0          # Hautrueckseite ist eben
    mat = np.zeros((n, n, nz + n_w), np.int8)                    # 0 Wasser, 1 Stahl, 2 Wolfram
    mat[:, :, n_w:][stahl] = 1; mat[:, :, :n_w] = 2
    f = np.ones(mat.shape, np.float32); f[:, :, n_w:] = faktor
    return mat, f


def netz(mat, faktor, dx, n_w, q_karte, h, k_struktur, ordner: Path):
    """Voxel -> Elmer-Netz (808/404). Rand 1: Waermestrom (Unterseite), Rand 10+b: Wasser, Faktorgruppe b."""
    n, _, nz = mat.shape
    I, J, K = np.nonzero(mat)
    nr = lambda i, j, k: (i * (n + 1) + j) * (nz + 1) + k
    hexa = np.stack([nr(I, J, K), nr(I + 1, J, K), nr(I + 1, J + 1, K), nr(I, J + 1, K),
                     nr(I, J, K + 1), nr(I + 1, J, K + 1), nr(I + 1, J + 1, K + 1), nr(I, J + 1, K + 1)], 1)
    ids, hexa = np.unique(hexa, return_inverse=True); hexa = hexa.reshape(-1, 8)
    ii, rest = np.divmod(ids, (n + 1) * (nz + 1)); jj, kk = np.divmod(rest, nz + 1)
    Xk = np.c_[ii * dx, jj * dx, (kk - n_w) * dx] / 1000.0      # m, z = 0 an der Stahlhaut
    lok = {(0, -1): [0, 3, 7, 4], (0, 1): [1, 2, 6, 5], (1, -1): [0, 1, 5, 4], (1, 1): [3, 2, 6, 7],
           (2, -1): [0, 1, 2, 3], (2, 1): [4, 5, 6, 7]}
    pad = np.pad(mat, 1, constant_values=-1)                     # -1 = ausserhalb (adiabat bzw. Unterseite)
    rand, gruppen = [], np.linspace(1, np.sqrt(3), 9)
    for (ach, s), q in lok.items():
        off = [0, 0, 0]; off[ach] = s
        nb = pad[I + 1 + off[0], J + 1 + off[1], K + 1 + off[2]]
        if ach == 2 and s == -1:                                 # Unterseite: Waermestrom
            e = np.where(nb == -1)[0]
            rand.append((np.ones(len(e), int), e, q))
        e = np.where(nb == 0)[0]                                 # Wasser
        if len(e):
            b = np.clip(np.digitize(faktor[I[e], J[e], K[e]], gruppen) - 1, 0, len(gruppen) - 2)
            rand.append((10 + b, e, q))
    bc = np.concatenate([r[0] for r in rand]); el = np.concatenate([r[1] for r in rand])
    fl = np.concatenate([hexa[r[1]][:, r[2]] for r in rand])
    m = ordner / "netz"; m.mkdir(parents=True, exist_ok=True)
    Nn, E, R = len(Xk), len(hexa), len(bc)
    body = np.where(mat[I, J, K] == 2, 2, 1)
    (m / "mesh.header").write_text(f"{Nn} {E} {R}\n2\n808 {E}\n404 {R}\n")
    np.savetxt(m / "mesh.nodes", np.c_[np.arange(1, Nn + 1), -np.ones(Nn), Xk], fmt="%d %d %.7e %.7e %.7e")
    np.savetxt(m / "mesh.elements", np.c_[np.arange(1, E + 1), body, np.full(E, 808), hexa + 1], fmt="%d")
    np.savetxt(m / "mesh.boundary", np.c_[np.arange(1, R + 1), bc, el + 1, np.zeros(R, int), np.full(R, 404), fl + 1],
               fmt="%d")
    # Waermestrom je Unterseiten-Element ueber eine Tabelle: Elmer bekommt q(x, y) als MATC-Funktion
    rbc = "\n".join(f"Boundary Condition {10 + b}\n  Target Boundaries(1) = {10 + b}\n"
                    f"  Heat Transfer Coefficient = Real {h / (0.5 * (gruppen[b] + gruppen[b + 1])):.6e}\n"
                    f"  External Temperature = Real {T_WASSER}\nEnd" for b in np.unique(bc[bc >= 10] - 10))
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
Body 2
  Equation = 1
  Material = 2
End
Material 1
  Heat Conductivity = Real {k_struktur}
  Density = Real 7800
End
Material 2
  Heat Conductivity = Real {K_WOLFRAM}
  Density = Real 19300
End
Equation 1
  Active Solvers(1) = 1
End
Solver 1
  Equation = "Heat Equation"
  Procedure = "HeatSolve" "HeatSolver"
  Variable = "Temperature"
  Linear System Solver = "Iterative"
  Linear System Iterative Method = "CG"
  Linear System Preconditioning = "ILU0"
  Linear System Max Iterations = 20000
  Linear System Convergence Tolerance = 1.0e-10
  Nonlinear System Max Iterations = 1
End
Solver 2
  Exec Solver = After All
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = "waerme"
  Vtu Format = Logical True
  Binary Output = Logical True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Heat Flux = Variable Coordinate 1, Coordinate 2
    Real MATC "{q_karte}"
End
{rbc}
""")
    return Xk, hexa, bc, fl


def rechne(fall, a, mat, faktor, n_w):
    fleck, _, k_struktur, h_faktor = FAELLE[fall]
    h = a.h * h_faktor
    o = WURZEL / fall; o.mkdir(parents=True, exist_ok=True)
    m = a.L / 2000.0
    q_karte = (f"{a.q:.6e}*(1+((tx(0)-{m})^2+(tx(1)-{m})^2<{0.010 ** 2:.6e}))" if fleck else f"{a.q:.6e}")
    Xk, hexa, bc, fl = netz(mat, faktor, a.voxel, n_w, q_karte, h, k_struktur, o)
    print(f"{fall}: {len(hexa)} Elemente, {len(Xk)} Knoten, {len(bc)} Randflaechen", flush=True)
    with open(o / "solve.log", "w") as f:
        subprocess.run(["ElmerSolver", "case.sif"], cwd=o, stdout=f, stderr=subprocess.STDOUT, check=True)
    import pyvista as pv
    gitter = pv.read(sorted((o / "erg").glob("waerme*.vtu"))[-1])
    T = np.asarray(gitter.point_data["temperature"], float)
    A = (a.voxel / 1000.0) ** 2
    mitte = Xk[fl].mean(1); Tf = T[fl].mean(1)
    nass = bc >= 10
    gruppen = np.linspace(1, np.sqrt(3), 9)
    h_eff = h / (0.5 * (gruppen[bc[nass] - 10] + gruppen[bc[nass] - 9]))
    q_aus = h_eff * (Tf[nass] - T_WASSER) * A                    # W je Flaeche
    unten = bc == 1
    q_ein = a.q * (1 + (fleck & (np.sum((mitte[unten, :2] - m) ** 2, 1) < 0.010 ** 2))) * A
    z0 = mitte[unten, 2].min()
    # Waermeabgabe je Tiefe (ab Stahlhaut) und je Spalte (seitliche Ausbreitung)
    kanten = np.arange(0, a.tiefe + 2.5, 2.5) / 1000.0
    je_tiefe = np.histogram(mitte[nass, 2], kanten, weights=q_aus)[0]
    nb = 40; xy = np.linspace(0, a.L / 1000.0, nb + 1)
    aus_xy = np.histogram2d(mitte[nass, 0], mitte[nass, 1], [xy, xy], weights=q_aus)[0] / (xy[1] - xy[0]) ** 2
    ein_xy = np.histogram2d(mitte[unten, 0], mitte[unten, 1], [xy, xy], weights=q_ein)[0] / (xy[1] - xy[0]) ** 2
    Tu = np.histogram2d(mitte[unten, 0], mitte[unten, 1], [xy, xy], weights=Tf[unten])[0] / \
        np.maximum(np.histogram2d(mitte[unten, 0], mitte[unten, 1], [xy, xy])[0], 1)
    r_fl = np.hypot(mitte[nass, 0] - m, mitte[nass, 1] - m)
    erg = {"elemente": int(len(hexa)), "q_ein_W": float(q_ein.sum()), "q_aus_W": float(q_aus.sum()),
           "T_plasmaseite_max_C": float(Tf[unten].max()), "T_plasmaseite_mittel_C": float(Tf[unten].mean()),
           "T_wand_nass_max_C": float(Tf[nass].max()), "siedereserve_K": float(T_SIEDEN - Tf[nass].max()),
           "anteil_wand_ueber_sieden": float(A * np.sum(Tf[nass] > T_SIEDEN) / (A * nass.sum())),
           "benetzt_m2_je_m2_treppe": float(nass.sum() * A / (a.L / 1000.0) ** 2),
           "benetzt_m2_je_m2_glatt": float(np.sum(A / (0.5 * (gruppen[bc[nass] - 10] + gruppen[bc[nass] - 9])))
                                           / (a.L / 1000.0) ** 2),
           "abgabe_je_tiefe_kumuliert": {f"{k * 1000:.1f} mm": float(v) for k, v in
                                         zip(kanten[1:], np.cumsum(je_tiefe) / q_aus.sum())},
           "z_plasmaseite_mm": float(z0 * 1000)}
    if fleck:                                                     # wie viel Fleck-Waerme geht ausserhalb ab?
        zus = a.q * np.pi * 0.010 ** 2
        erg["fleck"] = {"radius_mm": 10, "zusatz_W": float(zus),
                        **{f"aus_innerhalb_{r}_mm": float(q_aus[r_fl < r / 1000].sum() / q_aus.sum()) for r in (10, 20, 30)}}
    (o / "ergebnis.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))
    schnitt = gitter.slice(normal="y", origin=(m, m, 0.0))
    shutil.rmtree(o / "netz"); shutil.rmtree(o / "erg")
    return erg, {"aus_xy": aus_xy, "ein_xy": ein_xy, "Tu": Tu, "je_tiefe": je_tiefe, "kanten": kanten,
                 "schnitt": (np.asarray(schnitt.points), np.asarray(schnitt.point_data["temperature"]))}


def bild(a, alle, datei):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    nf = len(alle)
    fig, ax = plt.subplots(nf, 4, figsize=(20, 4.6 * nf), squeeze=False)
    ext = [0, a.L, 0, a.L]
    for z, (fall, (e, k)) in enumerate(alle.items()):
        im = ax[z, 0].imshow(k["Tu"].T, origin="lower", extent=ext, cmap="inferno")
        ax[z, 0].set_title(f"{TITEL[fall]}: Temperatur Plasmaseite [°C]\nmax {e['T_plasmaseite_max_C']:.0f} °C")
        fig.colorbar(im, ax=ax[z, 0])
        P, Tp = k["schnitt"]
        sc = ax[z, 1].scatter(P[:, 0] * 1000, P[:, 2] * 1000, c=Tp, s=1, cmap="inferno", vmin=T_WASSER)
        ax[z, 1].set_xlim(0, a.L); ax[z, 1].set_ylim(e["z_plasmaseite_mm"], 60); ax[z, 1].set_aspect("equal")
        ax[z, 1].set_xlabel("x [mm]"); ax[z, 1].set_ylabel("Tiefe z [mm]")
        ax[z, 1].set_title(f"Schnitt y = {a.L / 2:g} mm (Stahl), Wand nass max {e['T_wand_nass_max_C']:.0f} °C\n"
                           f"Siedegrenze {T_SIEDEN} °C")
        fig.colorbar(sc, ax=ax[z, 1])
        mx = max(k["aus_xy"].max(), k["ein_xy"].max()) / 1e6
        im = ax[z, 2].imshow(k["aus_xy"].T / 1e6, origin="lower", extent=ext, cmap="viridis", vmin=0, vmax=mx)
        ax[z, 2].contour(np.linspace(0, a.L, k["ein_xy"].shape[0]), np.linspace(0, a.L, k["ein_xy"].shape[0]),
                         k["ein_xy"].T / 1e6, [1.5 * a.q / 1e6], colors="red", linewidths=1)
        ax[z, 2].set_title("an das Wasser abgegeben je Grundfläche [MW/m²]\n(rot: Fleck mit 2 q)")
        fig.colorbar(im, ax=ax[z, 2])
        mm = k["kanten"][1:] * 1000
        ax[z, 3].plot(mm, np.cumsum(k["je_tiefe"]) / k["je_tiefe"].sum() * 100, "o-")
        ax[z, 3].set_xlabel("Tiefe ab Stahlhaut [mm]"); ax[z, 3].set_ylabel("abgegebene Wärme kumuliert [%]")
        ax[z, 3].grid(alpha=0.3); ax[z, 3].set_xlim(0, 30); ax[z, 3].set_ylim(0, 101)
        ax[z, 3].set_title("Wärmeabgabe nach Tiefe")
    fig.suptitle(f"Abgestufte Gyroid-Wand g1: q = {a.q / 1e6:g} MW/m², h = {a.h:g} W/m²K, Wasser {T_WASSER} °C, "
                 f"Voxel {a.voxel} mm", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(datei, dpi=100); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--voxel", type=float, default=0.5, help="mm")
    ap.add_argument("--L", type=float, default=80.0, help="Ausschnitt seitlich [mm] (Vielfaches von 80)")
    ap.add_argument("--tiefe", type=float, default=100.0, help="mm ab Stahlhaut")
    ap.add_argument("--h", type=float, default=1.0e4, help="Waermeuebergang ins Wasser W/m2K")
    ap.add_argument("--q", type=float, default=5.0e5, help="Waermestrom Plasmaseite W/m2")
    ap.add_argument("--faelle", default="gleich,fleck,wolfram,kupfer,h_doppelt")
    a = ap.parse_args(argv)
    WURZEL.mkdir(parents=True, exist_ok=True)
    alle = {}
    for fall in a.faelle.split(","):
        n_w = int(round(3.0 / a.voxel)) if FAELLE[fall][1] else 0
        mat, faktor = geometrie(a.L, a.tiefe, a.voxel, n_w)
        e, k = rechne(fall, a, mat, faktor, n_w)
        alle[fall] = (e, k)
        print(f"  Plasmaseite max {e['T_plasmaseite_max_C']:.1f} C, Wand nass max {e['T_wand_nass_max_C']:.1f} C "
              f"(Reserve {e['siedereserve_K']:.1f} K), Bilanz {e['q_aus_W']:.0f}/{e['q_ein_W']:.0f} W", flush=True)
    (WURZEL / "ergebnis.json").write_text(json.dumps({"parameter": vars(a), "faelle": {f: e for f, (e, _) in alle.items()}},
                                                     indent=1, ensure_ascii=False))
    bild(a, alle, WURZEL / "waerme.png")


if __name__ == "__main__":
    main()
