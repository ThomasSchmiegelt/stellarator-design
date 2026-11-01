"""alpha_auswertung.py — Auswertung der Alpha-Bahnen (stellarator/alpha_bahnen.py): Verluste, Energie, Wandlast, Video.

  .venv/bin/python -m stellarator.alpha_auswertung                  # Bilder und Kennzahlen
  .venv-opt/bin/python -m stellarator.alpha_auswertung verlustbahnen # zwei früh verlorene Bahnen mit vollem Weg (simsopt)
  .venv/bin/python -m stellarator.alpha_auswertung video            # Video aus bahnen.npz (+ verlustbahnen.npz)

Energie beim Verlust: Die Bahnen sind stoßfrei gerechnet (konstante Energie). Für die Bilanz wird jedem verlorenen
Alpha die Energie zugeordnet, die es zu diesem Zeitpunkt nach der klassischen Abbremsung (Stix 1972) noch hätte:
    dv/dt = -(v/tau_s) (1 + v_c^3/v^3)  ->  u = (E/E_c)^(3/2),  u(t) = (u0 + 1) exp(-3 t/tau_s) - 1
mit tau_s und E_c aus plasma_waerme.py. Dass sich die Bahn beim Abbremsen und durch Winkelstreuung ändert, ist nicht
enthalten (Grenze, im Bericht genannt).
Wandlast: Verlustorte liegen auf der letzten geschlossenen Fläche (s = 1); sie werden dem nächsten Punkt des Randgitters
(64 x 32) zugeordnet und auf gröbere Felder (16 x 8) zusammengefasst. Die echte Wand liegt weiter außen.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORDNER = ROOT / "sim" / "alpha" / "hts_1gw"
TEXT = "#2b2b2b"


def abbrems():
    w = json.loads((ROOT / "stellarator" / "daten" / "plasma_waerme.json").read_text())["wege"]
    E0 = json.loads((ROOT / "stellarator" / "daten" / "plasma_waerme.json").read_text())["kern"]["E_alpha_MeV"] * 1e3
    return w["tau_s_s"], w["E_krit_keV"], E0, w["P_alpha_MW"]


def energie_anteil(t, tau, Ec, E0):
    u0 = (E0 / Ec) ** 1.5
    u = (u0 + 1) * np.exp(-3 * np.asarray(t) / tau) - 1
    return np.where(u > 0, Ec * np.clip(u, 0, None) ** (2 / 3) / E0, 0.0)


def randflaeche():
    b = np.load(ORDNER / "bahnen.npz")
    r = b["rand"]                                             # (nphi, ntheta, 3), Anlagengröße [m]
    dphi = np.roll(r, -1, 0) - r; dth = np.roll(r, -1, 1) - r
    A = np.linalg.norm(np.cross(dphi, dth), axis=2)          # Fläche je Gitterzelle
    return r, A


def auswerten(name="hts_1gw"):
    from scipy.spatial import cKDTree
    d = np.load(ORDNER / "ergebnis.npz")
    e, st, lam = d["erg"], d["start"], d["lam"]
    N = len(e); tmax = float(d["tmax"])
    v = e[:, 0] == 1
    t = e[v, 1]
    tau, Ec, E0, Pa = abbrems()
    w = energie_anteil(t, tau, Ec, E0)                        # Energieanteil je verlorenem Alpha
    r, A = randflaeche()
    nphi, nth = r.shape[:2]
    baum = cKDTree(r.reshape(-1, 3))
    _, k = baum.query(e[v, 2:5])
    ip, it = np.unravel_index(k, (nphi, nth))
    gp, gt = 16, 8                                            # grobe Felder
    fp, ft = nphi // gp, nth // gt
    Ag = A.reshape(gp, fp, gt, ft).sum(axis=(1, 3))
    Eg = np.zeros((gp, gt)); np.add.at(Eg, (ip // fp, it // ft), w)
    Ng = np.zeros((gp, gt)); np.add.at(Ng, (ip // fp, it // ft), 1)
    q = Pa * Eg / N / Ag                                       # MW/m^2
    P_verl = Pa * w.sum() / N
    # Zeitverlauf
    tt = np.logspace(-5, np.log10(tmax), 300)
    anz = np.array([(t <= x).sum() for x in tt]) / N
    ener = np.array([w[t <= x].sum() for x in tt]) / N
    erg = dict(N=N, verloren=int(v.sum()), anteil=float(v.mean()), energie_anteil=float(w.sum() / N),
               P_alpha_MW=Pa, P_verloren_MW=float(P_verl), q_max_MW_m2=float(q.max()),
               q_mittel_MW_m2=float(P_verl / A.sum()), flaeche_m2=float(A.sum()),
               t_median_ms=float(np.median(t) * 1e3), vor_1ms=int((t < 1e-3).sum()), vor_10ms=int((t < 1e-2).sum()),
               lam_betrag_verloren=float(np.abs(lam[v]).mean()), lam_betrag_alle=float(np.abs(lam).mean()),
               s_verloren=float(st[v, 3].mean()), s_alle=float(st[:, 3].mean()),
               gefangen_anteil_verloren=float((np.abs(lam[v]) < 0.3).mean()),
               fehler_anteil_1sigma=float(np.sqrt(v.mean() * (1 - v.mean()) / N)),
               max_treffer_feld=int(Ng.max()), tau_s=tau, E_krit_keV=Ec)
    (ROOT / "stellarator" / "daten" / "alpha_verluste.json").write_text(json.dumps(erg, indent=1))
    for s in ("de", "en"):
        print(bild(erg, tt, anz, ener, st, lam, v, q, Ng, s))
    return erg


def bild(erg, tt, anz, ener, st, lam, v, q, Ng, sprache):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    de = sprache == "de"
    fig, ax = plt.subplots(2, 2, figsize=(13.5, 9.5), dpi=125)
    a = ax[0, 0]
    a.semilogx(tt * 1e3, 100 * anz, color="#2a78d6", lw=2, label=("Anteil der Alphas" if de else "share of alphas"))
    a.semilogx(tt * 1e3, 100 * ener, color="#eb6834", lw=2, label=("Anteil ihrer Energie" if de else "share of their energy"))
    a.axvline(erg["tau_s"] * 1e3, color="#888", ls=":", lw=1)
    a.text(erg["tau_s"] * 1e3, 1, (" Abbremszeit" if de else " slowing-down time"), color="#666", fontsize=8, rotation=90, va="bottom")
    a.set_xlabel(("Zeit nach der Geburt [ms]" if de else "time after birth [ms]")); a.set_ylabel(("verloren [%]" if de else "lost [%]"))
    a.set_title(("Wie viele Alphas gehen verloren, und wann?" if de else "How many alphas are lost, and when?"), fontsize=10.5)
    a.legend(frameon=False, fontsize=9, loc="upper left")
    a.text(0.98, 0.04, (f"nach 0,2 s: {100*erg['anteil']:.1f} % der Alphas,\n{100*erg['energie_anteil']:.1f} % ihrer Energie = {erg['P_verloren_MW']:.0f} MW"
                        if de else f"after 0.2 s: {100*erg['anteil']:.1f} % of alphas,\n{100*erg['energie_anteil']:.1f} % of their energy = {erg['P_verloren_MW']:.0f} MW"),
           transform=a.transAxes, ha="right", va="bottom", fontsize=9)
    a = ax[0, 1]
    a.scatter(lam[~v], st[~v, 3], s=5, color="#c9c8c4", label=("bleibt im Plasma" if de else "stays confined"))
    a.scatter(lam[v], st[v, 3], s=10, color="#d1495b", label=("verloren" if de else "lost"))
    a.set_xlabel(("Richtung bei der Geburt: v∥/v (0 = quer zum Feld)" if de else "direction at birth: v∥/v (0 = across the field)"))
    a.set_ylabel(("Geburtsort s (0 = Mitte, 1 = Rand)" if de else "birth position s (0 = centre, 1 = edge)"))
    a.set_title(("Wer geht verloren? Fast nur Alphas, die quer zum Feld starten" if de else "Who is lost? Almost only alphas starting across the field"), fontsize=10.5)
    a.legend(frameon=False, fontsize=9, loc="upper right")
    a = ax[1, 0]
    m = a.imshow(q.T, origin="lower", extent=(0, 360, 0, 360), aspect="auto", cmap="inferno")
    fig.colorbar(m, ax=a, label=("Wärmefluss [MW/m²]" if de else "heat flux [MW/m²]"))
    for i in range(Ng.shape[0]):
        for j in range(Ng.shape[1]):
            if Ng[i, j]:
                a.text((i + 0.5) * 360 / Ng.shape[0], (j + 0.5) * 360 / Ng.shape[1], int(Ng[i, j]), ha="center", va="center",
                       fontsize=6.5, color="white" if q[i, j] < 0.6 * q.max() else "black")
    a.set_xlabel(("toroidaler Winkel φ [°] (einmal den Ring entlang)" if de else "toroidal angle φ [°] (once along the ring)"))
    a.set_ylabel(("poloidaler Winkel θ [°] (einmal um den Querschnitt)" if de else "poloidal angle θ [°] (once around the cross-section)"))
    a.set_title(("Wo treffen sie den Plasmarand? (Zahl = Treffer je Feld)" if de else "Where do they hit the plasma edge? (number = hits per tile)"), fontsize=10.5)
    a = ax[1, 1]; a.axis("off")
    zeilen = ([f"Alphas gerechnet: {erg['N']}", f"verloren bis 0,2 s: {erg['verloren']} ({100*erg['anteil']:.1f} ± {100*erg['fehler_anteil_1sigma']:.1f} %)",
               f"davon in der ersten Millisekunde: {erg['vor_1ms']}", f"halbe Verluste bis: {erg['t_median_ms']:.0f} ms",
               f"verlorene Energie: {100*erg['energie_anteil']:.1f} % von {erg['P_alpha_MW']:.0f} MW = {erg['P_verloren_MW']:.0f} MW",
               f"mittlerer Wärmefluss am Rand: {erg['q_mittel_MW_m2']*1e3:.0f} kW/m²", f"größter (16 × 8 Felder): {erg['q_max_MW_m2']:.2f} MW/m²",
               f"Anteil |v∥/v| < 0,3 unter den Verlusten: {100*erg['gefangen_anteil_verloren']:.0f} %"]
              if de else
              [f"alphas computed: {erg['N']}", f"lost by 0.2 s: {erg['verloren']} ({100*erg['anteil']:.1f} ± {100*erg['fehler_anteil_1sigma']:.1f} %)",
               f"of these in the first millisecond: {erg['vor_1ms']}", f"half of the losses by: {erg['t_median_ms']:.0f} ms",
               f"lost energy: {100*erg['energie_anteil']:.1f} % of {erg['P_alpha_MW']:.0f} MW = {erg['P_verloren_MW']:.0f} MW",
               f"mean heat flux at the edge: {erg['q_mittel_MW_m2']*1e3:.0f} kW/m²", f"largest (16 × 8 tiles): {erg['q_max_MW_m2']:.2f} MW/m²",
               f"share with |v∥/v| < 0.3 among losses: {100*erg['gefangen_anteil_verloren']:.0f} %"])
    a.text(0.02, 0.95, ("Kennzahlen" if de else "Key figures"), fontsize=12, weight="bold", va="top", color=TEXT)
    for i, z in enumerate(zeilen):
        a.text(0.02, 0.84 - i * 0.095, z, fontsize=10.5, va="top", color=TEXT)
    for q_ in (ax[0, 0], ax[0, 1]):
        q_.grid(True, which="both", color="#e5e4e0", lw=0.6)
    fig.text(0.99, 0.005, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e", ha="right")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    name = "alpha_verluste.png" if de else "alpha_verluste_en.png"
    fig.savefig(ROOT / "docs" / "bilder" / name); plt.close(fig)
    shutil.copy(ROOT / "docs" / "bilder" / name, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return ROOT / "docs" / "bilder" / name


def verlustbahnen(k=2, tmin=1e-4, tmax_s=1e-3):
    """Zwei früh verlorene Alphas mit vollem Weg nachrechnen (simsopt, .venv-opt)."""
    from simsopt.field.tracing import trace_particles, LevelsetStoppingCriterion
    from stellarator import alpha_bahnen as ab
    d = np.load(ORDNER / "ergebnis.npz"); e = d["erg"]
    kand = np.where((e[:, 0] == 1) & (e[:, 1] > tmin) & (e[:, 1] < tmax_s))[0]
    wahl = kand[np.argsort(e[kand, 1])][[0, len(kand) - 1]][:k]
    F = ab.feld(); M, Q, Eu, vu, ft = ab.teilchen_u(F["Bu"])
    x0 = d["start"][wahl, :3]; vp = d["lam"][wahl] * vu
    res, hits = trace_particles(F["f"], x0, vp, tmax=1.2 * e[wahl, 1].max() / ft, mass=M, charge=Q, Ekin=Eu, tol=1e-9,
                                mode="gc_vac", stopping_criteria=[LevelsetStoppingCriterion(F["sc"].dist)])
    out = {}
    for i, (r_, j) in enumerate(zip(res, wahl)):
        out[f"v{i}"] = np.column_stack([r_[:, 0] * ft, r_[:, 1:4] * ab.L, np.full(len(r_), d["lam"][j])])
        print("Verlustbahn", i, "Index", j, "t_verlust", e[j, 1], "Punkte", len(r_), "Ende t", r_[-1, 0] * ft)
    np.savez(ORDNER / "verlustbahnen.npz", **out)


def _szene(pl, flaeche, linien, text):
    import pyvista as pv
    pl.clear()
    pl.set_background("#1f2329")
    for ring in flaeche:                                     # Plasmarand als Querschnittsringe
        pl.add_mesh(pv.lines_from_points(np.vstack([ring, ring[:1]])), color="#8f7fa8", line_width=1.5)
    for pts, c, kugel in linien:
        if len(pts) > 1:
            pl.add_mesh(pv.lines_from_points(pts), color=c, line_width=3)
        if kugel:
            pl.add_mesh(pv.Sphere(radius=kugel, center=pts[-1]), color=c)
    pl.add_text(text, position="upper_left", font_size=12, color="white")
    pl.add_text("Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", position="lower_right", font_size=8, color="#aaaaaa")


def video(fps=30, sek=20, schweif=0.08):
    import subprocess
    import pyvista as pv
    pv.OFF_SCREEN = True
    b = np.load(ORDNER / "bahnen.npz")
    r = b["rand"]
    lam = b["lam"]
    bahnen = [b[f"b{i}"] for i in range(len(lam))]
    vl = np.load(ORDNER / "verlustbahnen.npz")
    verl = [vl[k] for k in vl.files]
    flaeche = [r[i] for i in range(0, r.shape[0], 4)]          # 16 Querschnitte des Plasmarands
    umlauf = [i for i in np.argsort(-np.abs(lam)) if abs(lam[i]) > 0.5][:2]
    gefangen = [i for i in np.argsort(np.abs(lam)) if abs(lam[i]) < 0.3][:2]
    BL, GE, RO = "#4ea8ff", "#ffd166", "#ff4d4d"
    text = {"de": "Alphateilchen im Feld der eigenen Spulen   blau: umlaufend (entlang des Feldes)   gelb: gefangen (pendelt)   rot: geht verloren",
            "en": "Alpha particles in the field of the own coils   blue: passing (along the field)   yellow: trapped (bounces)   red: lost"}
    cam = [(0, -30, 22), (0, 0, 0), (0, 0, 1)]
    # Standbild: je eine Bahn, voller Weg (umlaufend und gefangen auf 0,05 ms gekürzt, damit man die Form sieht)
    for sp in ("de", "en"):
        pl = pv.Plotter(off_screen=True, window_size=(1600, 900))
        def kurz(bb, t):
            return bb[bb[:, 0] <= t, 1:4]
        _szene(pl, flaeche, [(kurz(bahnen[umlauf[0]], 5e-5), BL, 0.15), (kurz(bahnen[gefangen[0]], 2e-4), GE, 0.15),
                             (verl[0][:, 1:4], RO, 0.45)], text[sp])
        pl.camera_position = cam
        name = "alpha_bahnen_standbild.png" if sp == "de" else "alpha_bahnen_standbild_en.png"
        pl.screenshot(str(ROOT / "docs" / "bilder" / name)); pl.close()
        shutil.copy(ROOT / "docs" / "bilder" / name, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    # Video: Schweif der letzten Wegstücke, alle in derselben Zeit
    frames = fps * sek
    tmp = ORDNER / "video"; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    pl = pv.Plotter(off_screen=True, window_size=(1600, 900))
    zeig = [(bahnen[i], BL) for i in umlauf] + [(bahnen[i], GE) for i in gefangen] + [(v_, RO) for v_ in verl]
    for f in range(frames):
        g = (f + 1) / frames
        linien = []
        for bb, c in zeig:
            n = len(bb)
            if c == RO:                                     # Verlustbahn: endet früher, bleibt dann als Punkt stehen
                e = min(n, max(2, int(g * 1.25 * n)))
            else:
                e = max(2, int(g * n))
            a = max(0, e - max(2, int(schweif * n)))
            linien.append((bb[a:e, 1:4], c, 0.45 if (c == RO and e == n) else 0.15))
        _szene(pl, flaeche, linien, text["de"])
        pl.camera_position = cam
        pl.camera.azimuth = 120 * g
        pl.screenshot(str(tmp / f"f{f:04d}.png"))
    pl.close()
    ziel = ROOT / "docs" / "filme"; ziel.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", str(ziel / "alpha_bahnen.mp4")], check=True)
    shutil.rmtree(tmp)
    return ziel / "alpha_bahnen.mp4"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verlustbahnen":
        verlustbahnen()
    elif len(sys.argv) > 1 and sys.argv[1] == "video":
        print(video())
    else:
        print(json.dumps(auswerten(), indent=1))
