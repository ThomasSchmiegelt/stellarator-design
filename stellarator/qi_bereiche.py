"""Bereiche der besten Plasmen und gemeinsames Modell (Wechselwirkung der Kennzahlen).

Aufruf: .venv-constellaration/bin/python -m stellarator.qi_bereiche
Ergebnis: docs/recherche/qi_tragwerk/qi_bereiche.md. Nur Korrelation/Vorhersage, keine Ursache.
"""
import glob
import numpy as np
import pyarrow.parquet as pq
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

M = ["boundary.n_field_periods", "metrics.aspect_ratio", "metrics.max_elongation", "metrics.average_triangularity",
     "metrics.axis_magnetic_mirror_ratio", "metrics.edge_magnetic_mirror_ratio",
     "metrics.edge_rotational_transform_over_n_field_periods", "metrics.axis_rotational_transform_over_n_field_periods",
     "metrics.vacuum_well", "metrics.flux_compression_in_regions_of_bad_curvature",
     "metrics.minimum_normalized_magnetic_gradient_scale_length"]


def main():
    A = []
    for f in sorted(glob.glob("sim/rohdaten/constellaration/train-*.parquet")):
        t = pq.read_table(f, columns=["metrics.qi"] + M)
        A.append(np.column_stack([t.column(c).to_numpy(zero_copy_only=False).astype(float) for c in ["metrics.qi"] + M]))
    A = np.vstack(A); A = A[np.isfinite(A).all(1) & (A[:, 0] > 0)]
    y = np.log10(A[:, 0]); X = A[:, 1:]; nm = [c.replace("metrics.", "") for c in M]
    z = ["# QI-Güte: Bereiche der besten Plasmen und gemeinsames Modell", "",
         f"{len(y)} Plasmen. Beste 1 % = QI höchstens {10**np.percentile(y, 1):.5f}. Nur Korrelation, keine Ursache.", "",
         "## Bereiche (5. bis 95. Perzentil)", "", "| Merkmal | alle | beste 1 % | beste 10 % |", "|---|---|---|---|"]
    b1 = y <= np.percentile(y, 1); b10 = y <= np.percentile(y, 10)
    for j, n in enumerate(nm):
        r = lambda m: f"{np.percentile(X[m, j], 5):.3g} bis {np.percentile(X[m, j], 95):.3g}"
        z.append(f"| {n} | {r(np.ones(len(y), bool))} | {r(b1)} | {r(b10)} |")
    Xt, Xv, yt, yv = train_test_split(X, y, test_size=0.2, random_state=0)
    g = HistGradientBoostingRegressor(max_iter=300, random_state=0).fit(Xt, yt)
    r2 = g.score(Xv, yv)
    imp = permutation_importance(g, Xv[:20000], yv[:20000], n_repeats=3, random_state=0)
    z += ["", f"## Gemeinsames Modell (Gradient Boosting, zurückgehaltene Daten): R² = {r2:.2f}", "",
          "Wichtigkeit (Verlust an R², wenn das Merkmal gemischt wird):", "", "| Merkmal | Wichtigkeit |", "|---|---|"]
    for j in np.argsort(-imp.importances_mean):
        z.append(f"| {nm[j]} | {imp.importances_mean[j]:.3f} |")
    # Einzelmerkmal zum Vergleich
    z += ["", "Zum Vergleich: bester Einzelwert als R² (Rangkorrelation²) war 0,12."]
    open("docs/recherche/qi_tragwerk/qi_bereiche.md", "w").write("\n".join(z) + "\n"); print("\n".join(z))


if __name__ == "__main__":
    main()
