"""k3_rohr.py — Spulenkurven -> Rohr (Kreisquerschnitt) in PicoGK -> Glättung -> STL -> Prüfung -> geglättete Mittellinie.

  .venv-opt/bin/python -m stellarator.k3_rohr bauen <satz_ordner> [<voxel_mm> [<glaett_mm>]]
  .venv-opt/bin/python -m stellarator.k3_rohr pruefen <satz_ordner>

<satz_ordner> wie stellarator/spulen_satz.py (boundary.json + spulen.json, Datensatzmaßstab). Gebaut werden nur die
Basisspulen einer halben Periode (alle anderen sind Symmetriekopien); Abstand zum Plasma gegen den vollen Rand.
ANNAHMEN (gekennzeichnet): Anlagenmaßstab a = 1,80 m (wie zwei_ringe.py, A_REAL); Rohrdurchmesser = flächengleich zum
quadratischen Wickelpaket 0,7552 m der Kette (kopplung.WP_M, Stufe 0): d = 2 * sqrt(0,7552² / pi) = 0,852 m.
Glättung: PicoGK TripleOffset(g) = erst g nach innen, dann 2 g nach außen, dann g nach innen; nimmt Ecken/Kanten unter g weg
(hier: Facetten der Balkenkette und Kanten an Engstellen), Querschnitt bleibt sonst gleich.
Ausgabe <satz_ordner>/rohr/: auftrag.json, S<i>_glatt.stl, alle_glatt.stl, ergebnis_picogk.json, pruefung_rohr.json,
und <satz_ordner>_glatt/ (spulen.json aus der Mittellinie des geglätteten Rohrs, für Feldfehler/freie Grenze).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
APP = ROOT / "picogk" / "SpulenRohr" / "bin" / "Release" / "net9.0" / "SpulenRohr"
A_REAL = 1.80
WP_M = 0.7552
D_ROHR = 2 * np.sqrt(WP_M ** 2 / np.pi)


def kreis_mitte(W, p, t):
    """Kreismitte der Schnittpunkte W (in der Ebene durch p senkrecht zu t), algebraischer Kreisausgleich (Kasa)."""
    e1 = np.cross(t, [0.0, 0.0, 1.0])
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.cross(t, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1); e2 = np.cross(t, e1)
    u, v = (W - p) @ e1, (W - p) @ e2
    A = np.c_[u, v, np.ones_like(u)]; c = np.linalg.lstsq(A, u ** 2 + v ** 2, rcond=None)[0]
    return p + 0.5 * c[0] * e1 + 0.5 * c[1] * e2


def massstab(ordner):
    from stellarator.spulen_satz import flaeche
    s = flaeche(Path(ordner) / "boundary.json", nphi=128, ntheta=64)
    a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0)))))
    return A_REAL / a, a, s


def bauen(ordner, voxel_mm=25.0, glaett_mm=100.0, nq=400):
    from stellarator.spulen_satz import lade_satz
    from simsopt.geo import CurveXYZFourier
    ordner = (ROOT / ordner).resolve(); O = ordner / "rohr"; O.mkdir(parents=True, exist_ok=True)
    L, a, _ = massstab(ordner)
    basis, I, nfp = lade_satz(ordner)
    sp = []
    for i, c in enumerate(basis):
        k = CurveXYZFourier(nq, c.order); k.x = c.x
        sp.append({"name": f"S{i + 1}", "punkte_mm": (k.gamma() * L * 1000).round(3).tolist()})
    auftrag = {"voxel_mm": voxel_mm, "radius_mm": float(D_ROHR / 2 * 1000), "glaett_mm": glaett_mm, "ausgabe": str(O),
               "roh_export": True, "spulen": sp}
    (O / "auftrag.json").write_text(json.dumps(auftrag))
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"))
    t0 = time.time()
    r = subprocess.run([str(APP), str(O / "auftrag.json")], env=env, capture_output=True, text=True)
    (O / "picogk.log").write_text(r.stdout + r.stderr)
    print("PicoGK rc", r.returncode, f"{time.time() - t0:.0f} s", flush=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-2000:])
    return pruefen(ordner)


def pruefen(ordner, nq=400):
    import pyvista as pv
    from scipy.spatial import cKDTree
    from simsopt.geo import CurveXYZFourier
    from stellarator.spulen_satz import lade_satz, export, pruefe
    ordner = (ROOT / ordner).resolve(); O = ordner / "rohr"
    L, a, s = massstab(ordner)
    basis, I, nfp = lade_satz(ordner)
    # voller Plasmarand fein (m)
    from stellarator.spulen_satz import flaeche
    sf = flaeche(ordner / "boundary.json", nphi=720, ntheta=180); P = sf.gamma().reshape(-1, 3) * L
    baum = cKDTree(P)
    r_soll = D_ROHR / 2
    erg = {"annahmen": {"a_m": A_REAL, "rohr_d_m": D_ROHR, "massstab_m_je_einheit": L}, "spulen": []}
    neu_x = {}
    for i, c in enumerate(basis):
        k = CurveXYZFourier(nq, c.order); k.x = c.x
        g = k.gamma() * L; t = k.gammadash(); t = t / np.linalg.norm(t, axis=1, keepdims=True)
        lang = float(np.sum(np.linalg.norm(np.roll(g, -1, 0) - g, axis=1)))
        e = {"name": f"S{i + 1}", "laenge_m": lang}
        for art in ("roh", "glatt"):
            m = pv.read(str(O / f"S{i + 1}_{art}.stl")).clean()
            V = np.asarray(m.points) / 1000.0
            e[f"{art}_dreiecke"] = int(m.n_cells); e[f"{art}_offene_kanten"] = int(m.n_open_edges)
            e[f"{art}_mannigfaltig"] = bool(m.is_manifold); e[f"{art}_volumen_m3"] = float(abs(m.volume)) * 1e-9
            # Querschnitt je Station: Netzpunkte in einer Scheibe senkrecht zur Mittellinie
            vb = cKDTree(V); h = 0.6 * 0.025 + 0.01; mitte, rad = [], []
            for j in range(len(g)):
                idx = vb.query_ball_point(g[j], 1.6 * r_soll)
                if not idx:
                    mitte.append(g[j]); rad.append([np.nan, np.nan, np.nan]); continue
                W = V[idx]; ax = (W - g[j]) @ t[j]; W = W[np.abs(ax) < h]
                if len(W) < 8:
                    mitte.append(g[j]); rad.append([np.nan, np.nan, np.nan]); continue
                W = W - np.outer((W - g[j]) @ t[j], t[j])                 # in die Schnittebene projizieren
                cm = kreis_mitte(W, g[j], t[j]); rr = np.linalg.norm(W - cm, axis=1); mitte.append(cm); rad.append([rr.mean(), rr.min(), rr.max()])
            mitte = np.array(mitte); rad = np.array(rad)
            ab = np.linalg.norm(mitte - g, axis=1)
            e[f"{art}_mittellinie_versatz_mm"] = {"mittel": float(np.nanmean(ab) * 1000), "max": float(np.nanmax(ab) * 1000)}
            e[f"{art}_durchmesser_m"] = {"mittel": float(2 * np.nanmean(rad[:, 0])), "min": float(2 * np.nanmin(rad[:, 1])),
                                         "max": float(2 * np.nanmax(rad[:, 2]))}
            d_pl = baum.query(V)[0]
            e[f"{art}_abstand_plasma_m"] = float(d_pl.min()); e[f"{art}_abstand_plasma_a"] = float(d_pl.min() / A_REAL)
            if True:
                # neue Mittellinie -> Fourier-Ordnung wie vorher (kleinste Quadrate auf denselben Parameterwerten)
                q = np.asarray(k.quadpoints); M = [np.ones_like(q)]
                for n in range(1, c.order + 1):
                    M += [np.sin(2 * np.pi * n * q), np.cos(2 * np.pi * n * q)]
                M = np.array(M).T
                neu_x.setdefault(art, []).append(np.concatenate([np.linalg.lstsq(M, mitte[:, j] / L, rcond=None)[0] for j in range(3)]).tolist())
        e["abstand_mittellinie_plasma_m"] = float(baum.query(g)[0].min())
        e["volumen_soll_m3"] = float(np.pi * r_soll ** 2 * lang)
        erg["spulen"].append(e); print(json.dumps(e), flush=True)
    m = pv.read(str(O / "alle_glatt.stl")).clean()
    erg["vereinigung"] = {"dreiecke": int(m.n_cells), "offene_kanten": int(m.n_open_edges), "volumen_m3": float(abs(m.volume)) * 1e-9,
                          "summe_einzeln_m3": float(sum(x["glatt_volumen_m3"] for x in erg["spulen"])),
                          "abstand_plasma_m": float(baum.query(np.asarray(m.points) / 1000.0)[0].min())}
    erg["vereinigung"]["ueberlappung_m3"] = erg["vereinigung"]["summe_einzeln_m3"] - erg["vereinigung"]["volumen_m3"]
    # Feldfehler mit geglätteter Mittellinie
    erg["feldfehler_kurve"] = json.loads((ordner / "pruefung_satz.json").read_text()) if (ordner / "pruefung_satz.json").exists() else pruefe(ordner)
    for art in ("roh", "glatt"):                       # roh = Rohr vor der Glaettung (Messfehler des Rueckgewinnens), glatt = nach
        d = json.loads((ordner / "spulen.json").read_text()); d["basis_x"] = neu_x[art]; d["quelle"] = f"Mittellinie des PicoGK-Rohrs ({art})"
        Og = ordner.parent / (ordner.name + "_" + art); Og.mkdir(exist_ok=True)
        (Og / "spulen.json").write_text(json.dumps(d, indent=1)); (Og / "boundary.json").write_text((ordner / "boundary.json").read_text())
        erg[f"feldfehler_{art}"] = pruefe(Og)
    erg["verlust_glaettung_Bn_rel"] = erg["feldfehler_glatt"]["Bn_mittel"] / erg["feldfehler_roh"]["Bn_mittel"] - 1
    erg["verlust_rohr_gesamt_Bn_rel"] = erg["feldfehler_glatt"]["Bn_mittel"] / erg["feldfehler_kurve"]["Bn_mittel"] - 1
    (O / "pruefung_rohr.json").write_text(json.dumps(erg, indent=1))
    print(json.dumps({k: v for k, v in erg.items() if k != "spulen"}, indent=1))
    return erg


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "bauen":
        bauen(sys.argv[2], *(float(x) for x in sys.argv[3:5]))
    elif c == "pruefen":
        pruefen(sys.argv[2])
