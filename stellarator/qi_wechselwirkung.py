"""Wechselwirkung der Formparameter im Surrogat (A), Kennzahlen untereinander (C), Suche nach besseren Formen.

Aufruf: .venv-constellaration/bin/python -m stellarator.qi_wechselwirkung
Ergebnis: docs/recherche/qi_tragwerk/qi_wechselwirkung.md, sim/qi_flaeche/kandidaten.json (fuer die Gegenrechnung mit VMEC++).
Nur im Datenbereich gueltig. Surrogat = Gradient Boosting auf log10(QI).
"""
import glob
import json
import numpy as np
import pyarrow.parquet as pq
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

from stellarator.qi_koeffizienten import laden

METR = ["metrics.aspect_ratio", "metrics.max_elongation", "metrics.average_triangularity", "metrics.axis_magnetic_mirror_ratio",
        "metrics.edge_magnetic_mirror_ratio", "metrics.edge_rotational_transform_over_n_field_periods",
        "metrics.axis_rotational_transform_over_n_field_periods", "metrics.vacuum_well",
        "metrics.flux_compression_in_regions_of_bad_curvature", "metrics.minimum_normalized_magnetic_gradient_scale_length"]


def rang(v):
    o = np.argsort(v, kind="stable"); r = np.empty(len(v)); r[o] = np.arange(len(v)); return r


def kennzahlen_untereinander(z):
    A = []
    for f in sorted(glob.glob("sim/rohdaten/constellaration/train-*.parquet")):
        t = pq.read_table(f, columns=METR)
        A.append(np.column_stack([t.column(c).to_numpy(zero_copy_only=False).astype(float) for c in METR]))
    A = np.vstack(A); A = A[np.isfinite(A).all(1)]
    nm = [c.replace("metrics.", "") for c in METR]
    R = np.array([rang(A[:, i]) for i in range(A.shape[1])]); C = np.corrcoef(R)
    z += ["", "## C: Kennzahlen untereinander (Rangkorrelation, nur Paare mit Betrag ueber 0,5)", "", "| Kennzahl A | Kennzahl B | Rangkorrelation |", "|---|---|---|"]
    paare = [(abs(C[i, j]), i, j) for i in range(len(nm)) for j in range(i + 1, len(nm)) if abs(C[i, j]) > 0.5]
    for _, i, j in sorted(paare, reverse=True):
        z.append(f"| {nm[i]} | {nm[j]} | {C[i, j]:+.2f} |")
    if not paare:
        z.append("| (keine) | | |")


def pd_paar(g, Xb, j, k, gj, gk):
    out = np.empty((len(gj), len(gk)))
    for a, vj in enumerate(gj):
        for b, vk in enumerate(gk):
            Xt = Xb.copy(); Xt[:, j] = vj; Xt[:, k] = vk; out[a, b] = g.predict(Xt).mean()
    return out


def hmass(g, Xb, j, k, q=7):
    gj = np.percentile(Xb[:, j], np.linspace(5, 95, q)); gk = np.percentile(Xb[:, k], np.linspace(5, 95, q))
    P = pd_paar(g, Xb, j, k, gj, gk)
    pj = P.mean(1, keepdims=True); pk = P.mean(0, keepdims=True); m = P.mean()
    rest = P - pj - pk + m
    return float(rest.var() / max(P.var(), 1e-12)), float(P.max() - P.min())


def main():
    X, qi = laden()
    ok = np.isfinite(qi) & (qi > 0) & np.isfinite(X).all(1); X, qi = X[ok], qi[ok]; y = np.log10(qi)
    n = (X.shape[1] - 1) // 2; K = laden.MK[1]
    nm = ["nfp"] + [f"r_cos[{i // K},{i % K - K // 2}]" for i in range(n)] + [f"z_sin[{i // K},{i % K - K // 2}]" for i in range(n)]
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=0)
    g = HistGradientBoostingRegressor(max_iter=400, random_state=0).fit(Xt, yt)
    r2 = g.score(Xv, yv)
    imp = permutation_importance(g, Xv[:15000], yv[:15000], n_repeats=2, random_state=0)
    top = list(np.argsort(-imp.importances_mean)[:10])
    rng = np.random.default_rng(0); Xb = X[rng.choice(len(X), 300, replace=False)]
    z = ["# Wechselwirkung der Formparameter im Surrogat", "", f"Surrogat: Gradient Boosting, R2 = {r2:.2f} (zurueckgehaltene Daten). Zehn wichtigste Eingaben untersucht. Nur im Datenbereich gueltig.", "",
         "## A1: Einzelwirkung (Teilabhaengigkeit, Aenderung von log10(QI) zwischen 5. und 95. Perzentil des Parameters)", "",
         "| Parameter | Aenderung log10(QI) | Richtung (QI sinkt bei...) |", "|---|---|---|"]
    for j in top:
        gr = np.percentile(X[:, j], np.linspace(5, 95, 7)); v = []
        for w in gr:
            Xt2 = Xb.copy(); Xt2[:, j] = w; v.append(g.predict(Xt2).mean())
        v = np.array(v); best = gr[np.argmin(v)]
        z.append(f"| {nm[j]} | {v.max() - v.min():.2f} | {'groesseren' if best > np.median(gr) else 'kleineren'} Werten (Minimum bei {best:.3g}) |")
    z += ["", "## A2: Paar-Wechselwirkung (H-Mass: Anteil der gemeinsamen Wirkung, der nicht aus den Einzelwirkungen folgt)", "",
          "| Paar | H-Mass | Gemeinsame Wirkung (log10 QI) |", "|---|---|---|"]
    res = []
    for a in range(len(top)):
        for b in range(a + 1, len(top)):
            h, sp = hmass(g, Xb, top[a], top[b]); res.append((h, sp, top[a], top[b]))
    for h, sp, a, b in sorted(res, reverse=True)[:12]:
        z.append(f"| {nm[a]} + {nm[b]} | {h:.2f} | {sp:.2f} |")
    kennzahlen_untereinander(z)
    # Suche: von bekannten guten Formen aus, Schritte auf Paaren der wichtigsten Eingaben
    lo = np.percentile(X, 1, axis=0); hi = np.percentile(X, 99, axis=0); sd = X.std(0)
    starts = []
    for fall in ("dje", "dpr", "dyu"):
        try:
            b = json.load(open(f"sim/constellaration/qi/proxima_spulen_{fall}/boundary.json"))
            Mr, Kr = laden.MK
            def pad(a):
                a = np.asarray(a, float); o = np.zeros((Mr, Kr)); k0 = (Kr - a.shape[1]) // 2; o[:a.shape[0], k0:k0 + a.shape[1]] = a; return o.ravel()
            starts.append((fall, np.concatenate([[b["n_field_periods"]], pad(b["r_cos"]), pad(b["z_sin"])])))
        except Exception as e:
            z.append(f"\n(Startform {fall} nicht lesbar: {e})")
    gutidx = np.argsort(y)[:3]
    for i in gutidx: starts.append((f"daten{i}", X[i]))
    pairs = [(top[a], top[b]) for _, _, a, b in [(r[0], r[1], top.index(r[2]), top.index(r[3])) for r in sorted(res, reverse=True)[:6]]]
    kand = []
    for name, x0 in starts:
        best = x0.copy(); fb = g.predict(best[None])[0]
        for it in range(1500):
            j, k = pairs[rng.integers(len(pairs))]
            c = best.copy(); c[j] += rng.normal() * 0.25 * sd[j]; c[k] += rng.normal() * 0.25 * sd[k]
            c = np.clip(c, lo, hi); fc = g.predict(c[None])[0]
            if fc < fb: best, fb = c, fc
        dist = float(np.min(np.linalg.norm((X[:, top] - best[top]) / sd[top], axis=1)))
        kand.append({"start": name, "qi_start": float(10 ** g.predict(x0[None])[0]), "qi_surrogat": float(10 ** fb), "abstand_zu_daten": dist,
                     "nfp": int(best[0]), "r_cos": best[1:1 + n].reshape(laden.MK).tolist(), "z_sin": best[1 + n:].reshape(laden.MK).tolist(),
                     "geaendert": {nm[i]: [float(x0[i]), float(best[i])] for i in np.argsort(-np.abs(best - x0))[:8] if abs(best[i] - x0[i]) > 1e-9}})
    Path = __import__("pathlib").Path
    Path("sim/qi_flaeche").mkdir(exist_ok=True); json.dump(kand, open("sim/qi_flaeche/kandidaten.json", "w"), indent=1)
    z += ["", "## Suche im Surrogat (Schritte auf den stark wechselwirkenden Paaren, Werte innerhalb 1. bis 99. Perzentil der Daten)", "",
          "| Start | QI Start (Surrogat) | QI gefunden (Surrogat) | Abstand zu den Daten | geaenderte Eingaben (Start -> neu) |", "|---|---|---|---|---|"]
    for k in kand:
        z.append(f"| {k['start']} | {k['qi_start']:.5f} | {k['qi_surrogat']:.5f} | {k['abstand_zu_daten']:.2f} | " +
                 "; ".join(f"{a} {v[0]:.3g}->{v[1]:.3g}" for a, v in list(k['geaendert'].items())[:5]) + " |")
    z += ["", "Abstand zu den Daten: kleinster Abstand zu einer Datenform im Raum der zehn wichtigsten Eingaben (in Standardabweichungen); je groesser, desto unsicherer das Surrogat."]
    open("docs/recherche/qi_tragwerk/qi_wechselwirkung.md", "w").write("\n".join(z) + "\n"); print("\n".join(z))


if __name__ == "__main__":
    main()
