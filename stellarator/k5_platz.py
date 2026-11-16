"""k5_platz.py -- K5: freier Platz zwischen Plasmarand und Innenkante des Wickelpakets ueber die ganze Oberflaeche.
KI-generiert (Claude Sonnet 5.5, 2026-11-13).  Erwartung: sim/kandidat/erwartung/K5.md (nicht aendern).  Eingabe: sim/kandidat/kandidat.json.
Aufruf (Projektordner):  .venv-opt/bin/python -m stellarator.k5_platz [--test]
Verfahren: Plasmarand (s = 1, boundary.json des Spulensatzes, Datensatzform unveraendert) und alle Spulen (Symmetriekopien, Mittellinie) in Anlagengroesse (Faktor k aus K2 P1.json);
je Randpunkt kuerzester Abstand zur Spulenmittellinie d_c; freier Platz = d_c - wickelpaket_m/2 (Erwartung K5; konservativ zusaetzlich d_c - wickelpaket_m/sqrt(2), Halbdiagonale).
Gegen den Aufbau (Annahmen aus der Erwartung K5, hier nicht belegt): Summe 1,73-2,13 m; Grenzen der Deutung 1,7 m (Kollision) und 2,1 m (Torfrage erfuellt) wie in der Erwartung."""
import json, sys, time
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1]
TEST = "--test" in sys.argv
import os
_AUS = os.environ.get("FUSION_K_AUS")      # Variantenlauf (Opus 2026-11-15): Ausgabe nach <FUSION_K_AUS>/K5 statt sim/kandidat/K5, Standard unveraendert
K5DIR = (P / _AUS / "K5") if _AUS else P / "sim/kandidat/K5"
_KD = os.environ.get("FUSION_KANDIDAT_DATEI"); KDATEI = (Path(_KD) if Path(_KD).is_absolute() else P / _KD) if _KD else P / "sim/kandidat/kandidat.json"
OUT = K5DIR / ("test" if TEST else "lauf"); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(P / "stellarator")); sys.path.insert(0, str(P))
AUFBAU = [("Erste Wand", 0.03, 0.03), ("Blanket", 0.6, 0.8), ("Abschirmung", 0.5, 0.7), ("Vakuumgefäß", 0.3, 0.3), ("Spalte/Toleranzen", 0.2, 0.2), ("Gehäuse", 0.1, 0.1)]


def main():
    from scipy.spatial import cKDTree
    from simsopt.geo import CurveXYZFourier
    from simsopt.field import Current, coils_via_symmetries
    from spulen_satz import flaeche
    t0 = time.strftime("%F %T"); K = json.loads(KDATEI.read_text())
    P1 = json.loads((P / K["k2"] / "P1.json").read_text()); k = P1["faktor_k"]; wp = K["wickelpaket_m"]
    satz = P / K["spulensatz"]; d = json.loads((satz / "spulen.json").read_text())
    nq = 256 if TEST else 1024; nphi, nth = (64, 32) if TEST else (192, 96)
    basis = []
    for x in d["basis_x"]:
        c = CurveXYZFourier(nq, d["order"]); c.x = np.asarray(x, float) * k; basis.append(c)
    coils = coils_via_symmetries(basis, [Current(1.0)] * len(basis), d["nfp"], True)
    pts = np.concatenate([c.curve.gamma() for c in coils]); tree = cKDTree(pts)
    s = flaeche(satz / "boundary.json", nphi=nphi, ntheta=nth); G = s.gamma() * k            # (nphi, ntheta, 3)
    dc, _ = tree.query(G.reshape(-1, 3)); dc = dc.reshape(G.shape[:2])
    frei = dc - wp / 2; frei2 = dc - wp / np.sqrt(2)
    nfp = d["nfp"]; ph = np.arctan2(G[..., 1], G[..., 0])
    flaeche_el = np.linalg.norm(np.cross(np.gradient(G, axis=0), np.gradient(G, axis=1)), axis=-1); w = flaeche_el / flaeche_el.sum()
    anteil = lambda x, g: float(w[x < g].sum())
    i = np.unravel_index(np.argmin(frei), frei.shape)
    erg = {"start": t0, "test": TEST, "k": k, "wickelpaket_m": wp, "n_spulen": len(coils), "abtastung": f"{nq} Punkte je Spule, Rand {nphi} x {nth}",
           "abstand_mitte_min_m": float(dc.min()), "frei_min_m": float(frei.min()), "frei_mittel_m": float((frei * w).sum()), "frei_max_m": float(frei.max()),
           "frei_min_halbdiagonale_m": float(frei2.min()), "stelle_min": {"phi_grad": float(np.degrees(ph[i])), "theta_index": int(i[1]), "xyz_m": G[i].tolist()},
           "anteil_flaeche_unter_m": {g: anteil(frei, g) for g in (1.7, 2.1, 3.0)}, "anteil_flaeche_unter_m_halbdiagonale": {g: anteil(frei2, g) for g in (1.7, 2.1, 3.0)},
           "aufbau": [{"teil": n, "min_m": a, "max_m": b} for n, a, b in AUFBAU], "aufbau_summe_m": [sum(a for _, a, _ in AUFBAU), sum(b for _, _, b in AUFBAU)],
           "grenzen_erwartung_m": {"kollision_unter": 1.7, "erfuellt_ab": 2.1}, "quelle_K2": (K["k2"] + "/P4.json"), "ende": time.strftime("%F %T")}
    erg["reserve_min_m"] = erg["frei_min_m"] - 2.1
    ej = {"hinweis": "KI-generiert (Claude Sonnet 5.5); Schnittstelle fuer K7/K10", "abstand_frei_min_m": erg["frei_min_m"],
          "aufbau_m": [{"name": n, "dicke_m": b, "dicke_min_m": a_, "dicke_max_m": b, "art": "Annahme (Werte aus erwartung/K5.md, nicht belegt; dicke_m = Obergrenze)"} for n, a_, b in AUFBAU],
          "aufbau_summe_m": erg["aufbau_summe_m"], "quelle": "sim/kandidat/K5/" + ("test/" if TEST else "lauf/") + "auswertung.json"}
    ej["aufbau_m"][4]["name"] = "Spalt"
    (OUT.parent / "ergebnis.json" if not TEST else OUT / "ergebnis.json").write_text(json.dumps(ej, indent=1, ensure_ascii=False))
    (OUT / "auswertung.json").write_text(json.dumps(erg, indent=1)); np.savez(OUT / "karte.npz", frei=frei, phi=ph, G=G)
    bilder(OUT, frei, G, nfp, erg)
    vtk(OUT if (TEST or _AUS) else P / "video/bausteine/K5", G, frei)
    from stellarator.k5_bericht import schreibe
    schreibe(OUT, TEST, erg); print(json.dumps({x: erg[x] for x in ("frei_min_m", "frei_mittel_m", "anteil_flaeche_unter_m")}), flush=True)


def bilder(OUT, frei, G, nfp, e):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    (OUT / "bilder").mkdir(exist_ok=True); n = frei.shape[0] // nfp
    T = {"de": ("Freier Platz Plasmarand bis Wickelpaket-Innenkante (eine Feldperiode)", "toroidaler Winkel φ (Grad)", "poloidaler Index θ", "frei (m)", "1,7 m: Kollision (Erwartung)", "2,1 m: Aufbau erfüllt (Erwartung)", "KI-generiert (Claude Sonnet 5.5), Entwurf"),
         "en": ("Free space plasma edge to winding-pack inner edge (one field period)", "toroidal angle φ (deg)", "poloidal index θ", "free (m)", "1.7 m: collision (expectation)", "2.1 m: build-up satisfied (expectation)", "AI-generated (Claude Sonnet 5.5), draft")}
    ph = np.degrees(np.arctan2(G[:n, 0, 1], G[:n, 0, 0])) % 360; ex = [0, 360 / nfp, 0, frei.shape[1]]
    for sp, (t, xl, yl, cb, l1, l2, fu) in T.items():
        fig, ax = plt.subplots(figsize=(8, 4.5)); im = ax.imshow(frei[:n].T, origin="lower", aspect="auto", extent=ex, cmap="viridis", vmin=0)
        c = ax.contour(np.linspace(0, 360 / nfp, n, endpoint=False), np.arange(frei.shape[1]), frei[:n].T, levels=[1.7, 2.1, 3.0], colors=["r", "orange", "w"], linewidths=1)
        ax.clabel(c, fmt={1.7: "1,7 m" if sp == "de" else "1.7 m", 2.1: "2,1 m" if sp == "de" else "2.1 m", 3.0: "3 m"}, fontsize=7)
        cbar = fig.colorbar(im, label=cb)
        for v_, c_ in ((1.7, "r"), (2.1, "orange"), (3.0, "k")): cbar.ax.axhline(v_, color=c_, lw=2)
        ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title(t, fontsize=9)
        ax.text(0.01, 0.02, f"min {e['frei_min_m']:.2f} m | {l1} | {l2}", transform=ax.transAxes, color="w", fontsize=7)
        fig.text(.5, .005, fu, ha="center", fontsize=7); fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(OUT / "bilder" / f"k5_platz_{sp}.png", dpi=110); plt.close(fig)


def vtk(ziel, G, frei):
    ziel = Path(ziel); ziel.mkdir(parents=True, exist_ok=True); nphi, nth = frei.shape
    pts = np.concatenate([G.reshape(-1, 3), G[:1].reshape(-1, 3)]); sk = np.concatenate([frei.reshape(-1), frei[:1].reshape(-1)])
    polys = []
    for i in range(nphi):
        for j in range(nth):
            a, b = i * nth + j, i * nth + (j + 1) % nth; c, d = (i + 1) * nth + (j + 1) % nth, (i + 1) * nth + j
            polys.append((a, b, c, d))
    with open(ziel / "plasma_platz.vtk", "w") as f:
        f.write("# vtk DataFile Version 3.0\nKI-generiert K5, Plasmarand mit freiem Platz (m)\nASCII\nDATASET POLYDATA\n")
        f.write(f"POINTS {len(pts)} float\n"); np.savetxt(f, pts, fmt="%.4f")
        f.write(f"POLYGONS {len(polys)} {5 * len(polys)}\n"); [f.write("4 " + " ".join(map(str, q)) + "\n") for q in polys]
        f.write(f"POINT_DATA {len(pts)}\nSCALARS frei_m float 1\nLOOKUP_TABLE default\n"); np.savetxt(f, sk, fmt="%.4f")


if __name__ == "__main__":
    main()
