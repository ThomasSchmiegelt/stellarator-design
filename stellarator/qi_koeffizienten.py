"""Formkoeffizienten (boundary.r_cos, boundary.z_sin, Feldperioden) -> QI aus dem ConStellaration-Datensatz.

Aufruf: .venv-constellaration/bin/python -m stellarator.qi_koeffizienten
Ergebnis: docs/recherche/qi_tragwerk/qi_koeffizienten.md. Nur Korrelation/Vorhersage im Datensatzbereich.
"""
import glob
import numpy as np
import pyarrow.parquet as pq
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

QI_GUT = 1.0e-3


def laden():
    X, y = [], []
    for f in sorted(glob.glob("sim/rohdaten/constellaration/train-*.parquet")):
        pf = pq.ParquetFile(f)
        for b in pf.iter_batches(batch_size=20000, columns=["metrics.qi", "boundary.n_field_periods", "boundary.r_cos", "boundary.z_sin"]):
            qi = b.column(0).to_numpy(zero_copy_only=False).astype(float)
            nfp = b.column(1).to_numpy(zero_copy_only=False).astype(float)
            rc = [np.asarray(r, float) if r is not None else np.full((5, 9), np.nan) for r in b.column(2).to_pylist()]
            zs = [np.asarray(r, float) if r is not None else np.full((5, 9), np.nan) for r in b.column(3).to_pylist()]
            X.append((nfp, rc, zs)); y.append(qi)
    M = max(a.shape[0] for _, rc, _ in X for a in rc); K = max(a.shape[1] for _, rc, _ in X for a in rc)

    def pad(a):
        o = np.zeros((M, K)); k0 = (K - a.shape[1]) // 2; o[:a.shape[0], k0:k0 + a.shape[1]] = a; return o.ravel()
    Z = np.vstack([np.column_stack([nfp, np.array([pad(a) for a in rc]), np.array([pad(a) for a in zs])]) for nfp, rc, zs in X])
    laden.MK = (M, K)
    return Z, np.concatenate(y)


def main():
    X, qi = laden()
    ok = np.isfinite(qi) & (qi > 0) & np.isfinite(X).all(1)
    X, qi = X[ok], qi[ok]; y = np.log10(qi); gut = qi <= QI_GUT
    n = (X.shape[1] - 1) // 2
    M, K = laden.MK
    namen = ["nfp"] + [f"r_cos[{i // K},{i % K - K // 2}]" for i in range(n)] + [f"z_sin[{i // K},{i % K - K // 2}]" for i in range(n)]
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=0)
    g = HistGradientBoostingRegressor(max_iter=400, random_state=0).fit(Xt, yt)
    r2 = g.score(Xv, yv)
    imp = permutation_importance(g, Xv[:15000], yv[:15000], n_repeats=2, random_state=0)
    o = np.argsort(-imp.importances_mean)
    z = ["# Formkoeffizienten -> QI", "",
         f"{len(y)} Plasmen, {X.shape[1]} Eingaben (Feldperioden, r_cos und z_sin je {n}). Gut = QI <= {QI_GUT:g}: {int(gut.sum())}.", "",
         f"Gradient Boosting auf log10(QI), zurueckgehaltene Daten: R2 = {r2:.2f}.", "",
         "## Wichtigste Eingaben (Verlust an R2 beim Mischen)", "", "| Eingabe | Wichtigkeit |", "|---|---|"]
    for j in o[:12]:
        z.append(f"| {namen[j]} | {imp.importances_mean[j]:.3f} |")
    top = o[:5]
    gut_v = gut
    lo = np.percentile(X[gut][:, top], 5, axis=0); hi = np.percentile(X[gut][:, top], 95, axis=0)
    inn = np.all((X[:, top] >= lo) & (X[:, top] <= hi), axis=1)
    z += ["", "## Kasten auf den fuenf wichtigsten Eingaben (5. bis 95. Perzentil der guten)", "", "| Eingabe | von | bis |", "|---|---|---|"]
    for k, j in enumerate(top):
        z.append(f"| {namen[j]} | {lo[k]:.3g} | {hi[k]:.3g} |")
    z.append(f"\nIm Kasten {int(inn.sum())} Plasmen, davon gut {int((inn & gut).sum())}: Reinheit {100*(inn&gut).sum()/max(inn.sum(),1):.1f} % "
             f"(Grundrate {100*gut.mean():.2f} %), Abdeckung {100*(inn&gut).sum()/gut.sum():.0f} %.")
    b = DecisionTreeClassifier(max_depth=5, min_samples_leaf=50, class_weight={0: 1, 1: 5}, random_state=0).fit(X, gut)
    t = b.tree_
    best = None
    def lauf(k, pf):
        nonlocal best
        if t.children_left[k] == -1:
            m = np.ones(len(X), bool)
            for f, op, v in pf: m &= (X[:, f] <= v) if op == "<=" else (X[:, f] > v)
            if m.sum() and (best is None or gut[m].sum() > best[1]): best = (gut[m].mean(), int(gut[m].sum()), int(m.sum()), pf)
            return
        f, v = t.feature[k], t.threshold[k]
        lauf(t.children_left[k], pf + [(f, "<=", v)]); lauf(t.children_right[k], pf + [(f, ">", v)])
    lauf(0, [])
    z += ["", f"## Bester Bereich des Entscheidungsbaums (Tiefe 5): Reinheit {100*best[0]:.0f} %, {best[1]} gut von {best[2]}", ""]
    z += ["- " + f"{namen[f]} {op} {v:.3g}" for f, op, v in best[3]]
    open("docs/recherche/qi_tragwerk/qi_koeffizienten.md", "w").write("\n".join(z) + "\n"); print("\n".join(z))


if __name__ == "__main__":
    main()
