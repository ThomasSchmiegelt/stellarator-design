"""Bereinigte Surrogat-Suche (ganze, feste Feldperioden; Abstand zu den Daten begrenzt) und Gegenrechnung mit VMEC++.

  .venv-constellaration/bin/python -m stellarator.qi_gegenrechnung suche          # Surrogat wie qi_wechselwirkung, 10 Kandidaten
  .venv-constellaration/bin/python -m stellarator.qi_gegenrechnung eins <nr>      # VMEC++ + QI fuer einen Kandidaten (nr) oder dje/dpr
  .venv-constellaration/bin/python -m stellarator.qi_gegenrechnung auswertung     # Neuheit, offizielle Wertung, Tabelle

Ergebnis: sim/qi_flaeche/kandidaten_gegenrechnung.json, sim/qi_flaeche/gegenrechnung/<nr>.json,
docs/recherche/qi_tragwerk/opus_gegenrechnung_tabelle[_klein].md (Tabelle fuer den Bericht opus_gegenrechnung.md).
QI wird mit ConstellarationSettings.default_high_fidelity() gerechnet (wie die Wertung der Rangliste, problems.py);
default_high_fidelity_skip_qi() liefert qi = None.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
O = ROOT / "sim" / "qi_flaeche"
# VARIANTE "" = bereinigte Suche (Abstand zu den Daten 0,5 bis 1,5 sd in den zehn wichtigsten Eingaben);
# VARIANTE "klein" = kleine Schritte (hoechstens 0,3 sd von der Startform, mindestens 0,1 sd von jeder Datenform), F-237 DEUTUNG.
VAR = __import__("os").environ.get("VARIANTE", "")
GR = O / ("gegenrechnung" + (f"_{VAR}" if VAR else ""))
KAND = O / ("kandidaten_gegenrechnung" + (f"_{VAR}" if VAR else "") + ".json")
MODELL = O / "surrogat.joblib"
ABST_MAX, ABST_MIN, QI_ZIEL, N_KAND = 1.5, (0.1 if VAR == "klein" else 0.5), 4.0e-4, 10
START_MAX, SCHRITT = (0.3, 0.05) if VAR == "klein" else (np.inf, 0.25)
REF = {"dje": "sim/constellaration/qi/proxima_spulen_dje/boundary.json", "dpr": "sim/constellaration/qi/proxima_spulen_dpr/boundary.json"}
# Nachpruefung Kandidat 3 (klein) auf der Linie Startform -> Kandidat: halber Schritt (f = 0,5), Form aus der Linienrechnung
REF_K3 = "sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json"


def daten():
    from stellarator.qi_koeffizienten import laden
    X, qi = laden()
    ok = np.isfinite(qi) & (qi > 0) & np.isfinite(X).all(1)
    daten.ok = ok
    return X[ok], qi[ok], laden.MK


def ids():
    """plasma_config_id in derselben Reihenfolge wie laden() (gleiche Dateien, gleiche Reihenfolge)."""
    import glob
    import pyarrow.parquet as pq
    a, q = [], []
    for f in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet"))):
        t = pq.read_table(f, columns=["plasma_config_id", "metrics.qi"])
        a += t.column(0).to_pylist(); q.append(t.column(1).to_numpy(zero_copy_only=False).astype(float))
    return np.array(a), np.concatenate(q)


def surrogat(X, y):
    """Wie qi_wechselwirkung.main: gleiche Aufteilung, gleiches Modell, gleiche zehn wichtigste Eingaben. Gespeichert."""
    import joblib
    if MODELL.exists():
        d = joblib.load(MODELL); return d["g"], d["top"], d["r2"]
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import train_test_split
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=0)
    g = HistGradientBoostingRegressor(max_iter=400, random_state=0).fit(Xt, yt)
    r2 = float(g.score(Xv, yv))
    imp = permutation_importance(g, Xv[:15000], yv[:15000], n_repeats=2, random_state=0)
    top = [int(i) for i in np.argsort(-imp.importances_mean)[:10]]
    O.mkdir(exist_ok=True); joblib.dump({"g": g, "top": top, "r2": r2}, MODELL)
    return g, top, r2


def vektor(b, MK):
    M, K = MK

    def pad(a):
        a = np.asarray(a, float); o = np.zeros((M, K)); k0 = (K - a.shape[1]) // 2; o[:a.shape[0], k0:k0 + a.shape[1]] = a; return o.ravel()
    return np.concatenate([[b["n_field_periods"]], pad(b["r_cos"]), pad(b["z_sin"])])


def namen(MK):
    M, K = MK; n = M * K
    return ["nfp"] + [f"r_cos[{i // K},{i % K - K // 2}]" for i in range(n)] + [f"z_sin[{i // K},{i % K - K // 2}]" for i in range(n)]


def suche():
    from scipy.spatial import cKDTree
    X, qi, MK = daten(); y = np.log10(qi); nm = namen(MK)
    g, top, r2 = surrogat(X, y)
    sd = X.std(0); lo = np.percentile(X, 1, axis=0); hi = np.percentile(X, 99, axis=0)
    baum = cKDTree(X[:, top] / sd[top])
    frei = [j for j in top if j != 0]                       # Feldperioden fest (Index 0), nicht mitoptimieren
    K = MK[1]; n = MK[0] * K
    gesperrt = [1 + i for i in range(K // 2 + 1)] + [1 + n + i for i in range(K // 2 + 1)]   # m=0, n<=0 (Symmetrie, R00 bleibt)
    frei = [j for j in frei if j not in gesperrt]
    starts = []
    for f, p in REF.items():
        starts.append((f, vektor(json.loads((ROOT / p).read_text()), MK)))
    for nfp in (2, 3, 4):                                    # die 30 besten Datenformen, je 10 mit 2, 3, 4 Feldperioden
        idx = np.where(X[:, 0] == nfp)[0]; idx = idx[np.argsort(y[idx])[:10]]
        starts += [(f"daten{i}", X[i].copy()) for i in idx]
    rng = np.random.default_rng(1); kand = []
    for name, x0 in starts:
        f0 = g.predict(x0[None])[0]; best = x0.copy(); fb = np.inf; d_b = baum.query(best[top] / sd[top])[0]
        for it in range(1200):
            j, k = rng.choice(frei, 2, replace=False)
            c = best.copy(); c[j] += rng.normal() * SCHRITT * sd[j]; c[k] += rng.normal() * SCHRITT * sd[k]
            c[[j, k]] = np.clip(c[[j, k]], lo[[j, k]], hi[[j, k]])   # nur die bewegten Eingaben begrenzen (Lauf 1: alle -> Fehler)
            d = baum.query(c[top] / sd[top])[0]
            if d > ABST_MAX or np.linalg.norm((c[top] - x0[top]) / sd[top]) > START_MAX:
                continue
            if d < ABST_MIN:                                 # erst aus der Datenform heraus (sonst Kopie)
                if d > d_b and not np.isfinite(fb):
                    best, d_b = c, d
                continue
            fc = g.predict(c[None])[0]
            if fc < fb:
                best, fb, d_b = c, fc, d
        if not np.isfinite(fb):
            continue
        kand.append({"start": name, "qi_start_surrogat": float(10 ** f0), "qi_surrogat": float(10 ** fb), "abstand_top10": float(d_b), "abstand_start_top10": float(np.linalg.norm((best[top] - x0[top]) / sd[top])),
                     "nfp": int(round(best[0])), "r_cos": best[1:1 + n].reshape(MK).tolist(), "z_sin": best[1 + n:].reshape(MK).tolist(),
                     "geaendert": {nm[i]: [float(x0[i]), float(best[i])] for i in np.argsort(-np.abs(best - x0))[:6] if abs(best[i] - x0[i]) > 1e-12}})
        print(name, int(x0[0]), f"{10 ** f0:.5f} -> {10 ** fb:.5f}  Abstand {d_b:.2f}", flush=True)
    gut = sorted([k for k in kand if k["qi_surrogat"] < QI_ZIEL], key=lambda k: k["qi_surrogat"])
    wahl = []
    for nfp in (2, 3, 4):                                    # Vielfalt: erst je Feldperiodenzahl die besten, dann auffuellen
        wahl += [k for k in gut if k["nfp"] == nfp][:3]
    wahl += [k for k in gut if k not in wahl][:N_KAND - len(wahl)]
    wahl = sorted(wahl[:N_KAND], key=lambda k: k["qi_surrogat"])
    for i, k in enumerate(wahl):
        k["nr"] = i
    json.dump({"r2": r2, "top10": [nm[j] for j in top], "alle": kand, "kandidaten": wahl}, open(KAND, "w"), indent=1)
    print(f"{len(gut)} von {len(kand)} unter {QI_ZIEL}; gewaehlt {len(wahl)}")


def rand(nr):
    if nr == "k3halb":
        return json.loads((ROOT / REF_K3).read_text())
    if nr in REF:
        return json.loads((ROOT / REF[nr]).read_text())
    k = json.loads(KAND.read_text())["kandidaten"][int(nr)]
    return {"r_cos": k["r_cos"], "z_sin": k["z_sin"], "r_sin": None, "z_cos": None, "n_field_periods": k["nfp"],
            "n_periodicity": 1, "is_stellarator_symmetric": True}


def eins(nr):
    from constellaration import forward_model
    from constellaration.geometry import surface_rz_fourier as srf
    GR.mkdir(parents=True, exist_ok=True); t0 = time.time(); aus = {"nr": nr}
    try:
        b = srf.SurfaceRZFourier.model_validate(rand(nr))
        m, w = forward_model.forward_model(b, settings=forward_model.ConstellarationSettings.default_high_fidelity())
        aus["metriken"] = {a: (float(v) if isinstance(v, (int, float)) else None) for a, v in m.model_dump().items()}
        aus["konvergiert"] = True                             # forward_model bricht bei nicht konvergiertem VMEC++ mit Fehler ab
        for a in ("fsqr", "fsqz", "fsql", "ier_flag", "ftolv", "niter"):
            if hasattr(w, a):
                v = getattr(w, a); aus[a] = float(v) if np.ndim(v) == 0 else None
    except Exception as e:
        aus["konvergiert"] = False; aus["fehler"] = f"{type(e).__name__}: {str(e)[:300]}"
    aus["sekunden"] = time.time() - t0
    (GR / f"{nr}.json").write_text(json.dumps(aus, indent=1)); print(json.dumps(aus), flush=True)


def wertung(mt):
    """Offizielle Wertung (constellaration.problems) aus den Metriken; Hochfidelitaet wie evaluate()."""
    from constellaration import forward_model, problems
    m = forward_model.ConstellarationMetrics(**mt); out = {}
    for name, P in (("P1_geometrisch", problems.GeometricalProblem), ("P2_einfach_QI", problems.SimpleToBuildQIStellarator)):
        p = P(); ob, _ = p.get_objective(m); ok = p.is_feasible(m)
        out[name] = {"ziel": float(ob), "verletzung": p.compute_feasibility(m), "zulaessig": ok, "wert": float(p._score(m)) if ok else 0.0}
    p = problems.MHDStableQIStellarator(); ok = p.is_feasible(m)
    out["P3_MHD_QI"] = {"ziel": [float(v) for v, _ in p.get_objectives(m)], "verletzung": p.compute_feasibility(m), "zulaessig": ok,
                        "hypervolumen_allein": float(p._score([m]))}
    return out


def auswertung():
    X, qi, MK = daten(); sd = X.std(0); D = json.loads(KAND.read_text()); top = surrogat(X, np.log10(qi))[1]
    pid, _ = ids(); pid = pid[daten.ok] if len(pid) == len(daten.ok) else None   # gleiche Zeilenfolge wie laden()
    from scipy.spatial import cKDTree
    s = np.where(sd > 0, sd, 1.0)
    voll = cKDTree(X / s); t10 = cKDTree(X[:, top] / s[top])
    z = ["| Nr | Start (QI Datensatz) | nfp | QI Surrogat | QI VMEC++ | Faktor | A | Elong. | iota_Rand/nfp | konv. | s | Abstand top10 | Abstand alle 91 | nächste Datenform (QI) | P1 | P2 | P3 zul. |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    zeilen = []
    for k in D["kandidaten"] + [{"nr": "dje", "start": "DjLe3eL6 (Datensatz)", "qi_surrogat": None}, {"nr": "dpr", "start": "DPrcxq66 (Datensatz)", "qi_surrogat": None},
                                    {"nr": "k3halb", "start": "Kandidat 3, halber Schritt", "qi_surrogat": None}]:
        f = GR / f"{k['nr']}.json"
        if not f.exists():
            continue
        r = json.loads(f.read_text()); v = vektor(rand(k["nr"]), MK)
        dv, iv = voll.query(v / s); dt, _ = t10.query(v[top] / s[top])
        r["abstand_alle"] = float(dv); r["abstand_top10"] = float(dt); r["naechste_qi"] = float(qi[iv])
        r["naechste_id"] = str(pid[iv]) if pid is not None else None; r["im_datensatz"] = bool(dv < 1e-6)
        mt = r.get("metriken"); q = mt.get("qi") if mt else None
        if mt:
            r["wertung"] = wertung(mt)
        (GR / f"{k['nr']}.json").write_text(json.dumps(r, indent=1)); zeilen.append((k, r))
        w = r.get("wertung", {})
        st = k["start"]
        if st.startswith("daten"):
            i0 = int(st[5:]); r["start_id"] = str(pid[i0]) if pid is not None else None; r["start_qi_datensatz"] = float(qi[i0])
            st = f"{r['start_id']} ({qi[i0]:.5f})"
        (GR / f"{k['nr']}.json").write_text(json.dumps(r, indent=1))
        fmt = lambda x, p=".5f": "–" if x is None else format(x, p)
        z.append(f"| {k['nr']} | {st} | {rand(k['nr'])['n_field_periods']} | {fmt(k.get('qi_surrogat'))} | {fmt(q)} | "
                 f"{fmt(q / k['qi_surrogat'] if q and k.get('qi_surrogat') else None, '.1f')} | {fmt(mt and mt['aspect_ratio'], '.2f')} | "
                 f"{fmt(mt and mt['max_elongation'], '.2f')} | {fmt(mt and mt['edge_rotational_transform_over_n_field_periods'], '.3f')} | "
                 f"{'ja' if r['konvergiert'] else 'nein'} | {r['sekunden']:.0f} | {dt:.2f} | {dv:.2f} | {r['naechste_id']} ({r['naechste_qi']:.5f}) | "
                 f"{fmt(w.get('P1_geometrisch', {}).get('wert'), '.3f')} | {fmt(w.get('P2_einfach_QI', {}).get('wert'), '.3f')} | "
                 f"{'ja' if w.get('P3_MHD_QI', {}).get('zulaessig') else 'nein'} |")
    gem = [r["metriken"]["qi"] for k, r in zeilen if isinstance(k["nr"], int) and r.get("metriken")]
    z += ["", f"Kandidaten gerechnet: {len([1 for k, _ in zeilen if isinstance(k['nr'], int)])}, konvergiert: {len(gem)}, "
          f"QI < 0,001: {sum(q < 1e-3 for q in gem)}, QI < 0,00045 (besser als DjLe3eL6): {sum(q < 4.5e-4 for q in gem)}."]
    (ROOT / f"docs/recherche/qi_tragwerk/opus_gegenrechnung_tabelle{'_' + VAR if VAR else ''}.md").write_text("\n".join(z) + "\n"); print("\n".join(z))


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "suche":
        suche()
    elif a == "eins":
        for nr in sys.argv[2:]:
            eins(nr if nr in REF or nr == "k3halb" else int(nr))
    elif a == "auswertung":
        auswertung()
