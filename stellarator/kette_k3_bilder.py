"""kette_k3_bilder.py — Bilder für den Bericht docs/recherche/spulen_suche/kette_k3.md.

  .venv-opt/bin/python -m stellarator.kette_k3_bilder profil                 # QI je Fläche: fest / frei (A085, Proxima, K3)
  .venv-opt/bin/python -m stellarator.kette_k3_bilder rohr <satz> <name>     # 3D-Bild Rohre + Plasma (pyvista, offscreen)
  .venv-opt/bin/python -m stellarator.kette_k3_bilder schnitt <satz> <name> [<phi_grad>]  # Schnitt R-Z: Plasma + Rohre
  .venv-opt/bin/python -m stellarator.kette_k3_bilder stage2                 # Feldfehler / Abstand der Stage-2-Läufe
Ausgabe: docs/recherche/spulen_suche/kette_k3/<name>.png
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BILD = ROOT / "docs" / "recherche" / "spulen_suche" / "kette_k3"
K = ROOT / "sim" / "kette_k3"


def profil():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    reihen = [("DjLe3eL6 fest (ohne Spulen)", ROOT / "sim/qi_spulen/faelle/fest_nz48.json", "k", "-"),
              ("DjLe3eL6 frei, Proxima-Spulen, 3000 Schritte", ROOT / "sim/qi_spulen/faelle/k_n3000.json", "#c0392b", "--"),
              ("DjLe3eL6 frei, Proxima-Spulen, 12000 Schritte", ROOT / "sim/qi_spulen/faelle/k_n12000.json", "#c0392b", ":"),
              ("DjLe3eL6 frei, eigene Spulen A085, 3000", K / "satz_A085/frei/faelle/k_n3000.json", "#1b6ca8", "--"),
              ("DjLe3eL6 frei, eigene Spulen A085, 12000", K / "satz_A085/frei/faelle/k_n12000.json", "#1b6ca8", ":"),
              ("DjLe3eL6 frei, A085 nach PicoGK-Glättung", K / "satz_A085_glatt/frei/faelle/k_n3000.json", "#2a9d8f", "-.")]
    for p in sorted(K.glob("stage2/satz_*/frei/faelle/fest_nz*.json")):
        reihen.append((f"K3 halb fest (ohne Spulen)", p, "#6a4c93", "-"))
        break
    farbe = {"d085_n10": "#f4a261", "d085_n10_lr": "#e76f51", "d085_n10_lr_glatt": "#9b2226", "d085_n8": "#e9c46a"}
    for p in sorted(K.glob("stage2/satz_*/frei/faelle/k_n*.json")):
        satz = p.parts[-4][5:]
        reihen.append((f"K3 halb frei, eigene Spulen {satz}, {p.stem[3:]}", p, farbe.get(satz, "#e76f51"), ":" if "12000" in p.stem else "--"))
    fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    for lab, p, c, ls in reihen:
        if not p.exists():
            continue
        j = json.loads(p.read_text())
        if "qi_flaeche" not in j:
            continue
        ax.semilogy(j["s_qi"], j["qi_flaeche"], ls, color=c, marker=".", label=f"{lab}: Rand {j['qi']:.2e}")
    ax.set_xlabel("Fläche im Plasma s (0 = Achse, 1 = Rand)"); ax.set_ylabel("QI-Fehler der Fläche (kleiner = besser)")
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=7)
    ax.set_title("QI je Fläche: Wunschplasma (fest) gegen Plasma aus dem Spulenfeld (freie Grenze)", fontsize=10)
    BILD.mkdir(parents=True, exist_ok=True); fig.savefig(BILD / "qi_profil.png", dpi=120); plt.close(fig)


def _plasma(satz, L, nphi=360, ntheta=90):
    from stellarator.spulen_satz import flaeche
    s = flaeche(Path(satz) / "boundary.json", nphi=nphi, ntheta=ntheta)
    return s.gamma() * L


def rohr(satz, name):
    import pyvista as pv
    from simsopt.field import Current, coils_via_symmetries
    from stellarator.k3_rohr import massstab
    from stellarator.spulen_satz import lade_satz
    pv.OFF_SCREEN = True
    satz = (ROOT / satz).resolve(); L, a, _ = massstab(satz)
    G = _plasma(satz, L)
    grid = pv.StructuredGrid(G[..., 0], G[..., 1], G[..., 2])
    m = pv.read(str(satz / "rohr" / "alle_glatt.stl")).decimate(0.9)
    m.points /= 1000.0
    p = pv.Plotter(off_screen=True, window_size=(1600, 1100)); p.set_background("white")
    p.add_mesh(grid, color="#f4a261", opacity=0.55, smooth_shading=True)
    p.add_mesh(m, color="#4a6fa5", smooth_shading=True)
    basis, I, nfp = lade_satz(satz)
    for c in coils_via_symmetries(basis, [Current(1.0)] * len(basis), nfp, True)[len(basis):]:
        g = c.curve.gamma() * L; p.add_mesh(pv.lines_from_points(np.vstack([g, g[:1]])), color="#555555", line_width=2)
    p.camera_position = "iso"; p.camera.elevation = 25; p.camera.zoom(1.3)
    p.add_text(f"{name}: Rohre (blau, geglättet, d = 0,85 m) einer halben Periode, übrige Spulen als Mittellinie (grau), Plasma orange",
               font_size=10, color="black")
    BILD.mkdir(parents=True, exist_ok=True); p.screenshot(str(BILD / f"rohr_{name}.png")); p.close()


def schnitt(satz, name, phi_grad=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pyvista as pv
    from stellarator.k3_rohr import massstab, D_ROHR
    satz = (ROOT / satz).resolve(); L, a, _ = massstab(satz)
    m = pv.read(str(satz / "rohr" / "S1_glatt.stl"))
    for f in sorted((satz / "rohr").glob("S*_glatt.stl"))[1:]:
        m = m.merge(pv.read(str(f)))
    if phi_grad is None:                                   # Schnitt durch die Mitte der ersten Spule
        from stellarator.spulen_satz import lade_satz
        b, _, _ = lade_satz(satz); c0 = b[0].gamma().mean(0); phi_grad = float(np.degrees(np.arctan2(c0[1], c0[0])))
    ph = np.radians(phi_grad); nrm = (-np.sin(ph), np.cos(ph), 0.0)
    sl = m.slice(normal=nrm, origin=(0, 0, 0)); P = np.asarray(sl.points) / 1000.0
    P = P[(P[:, 0] * np.cos(ph) + P[:, 1] * np.sin(ph)) > 0]
    from stellarator.spulen_satz import flaeche
    import json as _j
    nfp = int(_j.loads((satz / "boundary.json").read_text())["n_field_periods"])
    s = flaeche(satz / "boundary.json", nphi=1, ntheta=400)
    from simsopt.geo import SurfaceRZFourier
    s1 = SurfaceRZFourier(nfp=s.nfp, stellsym=True, mpol=s.mpol, ntor=s.ntor, quadpoints_phi=[ph / (2 * np.pi)],
                          quadpoints_theta=np.linspace(0, 1, 400)); s1.x = s.x
    g = s1.gamma()[0] * L
    fig, ax = plt.subplots(figsize=(7, 8), constrained_layout=True)
    ax.plot(np.hypot(g[:, 0], g[:, 1]), g[:, 2], "-", color="#e76f51", lw=2, label="Plasmarand (Wunschform)")
    ax.plot(np.hypot(P[:, 0], P[:, 1]), P[:, 2], ".", ms=1.5, color="#1d3557", label="Rohr-Oberfläche (PicoGK, geglättet)")
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.set_xlabel("Abstand von der Maschinenachse R (m)"); ax.set_ylabel("Höhe Z (m)")
    ax.legend(fontsize=8, loc="upper right")
    ax.set_title(f"{name}: Schnitt bei φ = {phi_grad:.1f}° (Rohr d = {D_ROHR:.2f} m, Annahme)", fontsize=10)
    fig.savefig(BILD / f"schnitt_{name}.png", dpi=120); plt.close(fig)


def stage2():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    E = [json.loads(p.read_text()) for p in sorted((K / "stage2").glob("d*_n*.json"))]
    E += [dict(json.loads(p.read_text()), planb=True) for p in sorted((K / "planb" / "stage2").glob("d*_n*.json"))]
    for e, ordner in zip(E, [K / "stage2"] * len(E)):
        q = (K / ("planb/stage2" if e.get("planb") else "stage2") / f"satz_{e['fall']}" / "pruefung_satz.json")
        if q.exists():                                            # Abstand einheitlich auf dem Rand 128 x 64 (spulen_satz.pruefe)
            e["ringe"]["ring0"]["abstand_plasma_a"] = json.loads(q.read_text())["abstand_plasma_a"]
    if not E:
        return
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    for e in E:
        c = {0.72: "#2a9d8f", 0.85: "#1b6ca8", 1.0: "#6a4c93"}.get(e["abstand_soll_a"], "k")
        mk = "s" if e.get("planb") else "o"; e["fall"] = ("Plan B " if e.get("planb") else "K3 ") + e["fall"]
        ax[0].semilogy(e["spulen_je_halbperiode"], e["Bn_mittel"], mk, color=c, ms=8)
        ax[0].annotate(e["fall"], (e["spulen_je_halbperiode"], e["Bn_mittel"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
        ax[1].semilogy(e["ringe"]["ring0"]["abstand_plasma_a"], e["Bn_mittel"], mk, color=c, ms=8)
        ax[1].annotate(e["fall"], (e["ringe"]["ring0"]["abstand_plasma_a"], e["Bn_mittel"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
    for A in ax:
        A.axhline(3e-3, color="#c0392b", ls="--", lw=1); A.axhline(6.6e-4, color="gray", ls=":", lw=1); A.grid(alpha=0.3)
        A.set_ylabel("Feldfehler mittel |B·n|/|B|")
    ax[0].text(ax[0].get_xlim()[0], 3.1e-3, " Abbruchgrenze 3e-3", color="#c0392b", fontsize=7)
    ax[0].text(ax[0].get_xlim()[0], 6.8e-4, " DjLe3eL6 A085 (6,6e-4)", color="gray", fontsize=7)
    ax[1].axvline(0.72, color="#c0392b", ls="--", lw=1)
    ax[0].set_xlabel("Spulen je halbe Periode"); ax[1].set_xlabel("erreichter Abstand Spule–Plasma (in a)")
    fig.suptitle("Stage 2: wie gut treffen die Spulen die Wunschform? (Kreis = K3 halb, Quadrat = Plan B DATJ5FC…)", fontsize=10)
    fig.savefig(BILD / "stage2.png", dpi=120); plt.close(fig)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "profil":
        profil()
    elif c == "rohr":
        rohr(sys.argv[2], sys.argv[3])
    elif c == "schnitt":
        schnitt(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else None)
    elif c == "stage2":
        stage2()
