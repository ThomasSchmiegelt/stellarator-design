"""Parameterkorridor fuer ein 'optimales' Plasma (QI-Guete) aus dem ConStellaration-Datensatz.

Aufruf: .venv-constellaration/bin/python -m stellarator.qi_korridor   (Ergebnis docs/recherche/qi_tragwerk/qi_korridor.md)
Gut = QI <= QI_GUT. Zwei Verfahren: Kasten (5. bis 95. Perzentil der guten Plasmen) und flacher Entscheidungsbaum.
Die Kennzahlen sind Messgroessen der Feldform, keine Entwurfsparameter. Nur Korrelation.
"""
import glob
import numpy as np
import pyarrow.parquet as pq
from sklearn.tree import DecisionTreeClassifier

QI_GUT = 1.0e-3
M = ["boundary.n_field_periods", "metrics.aspect_ratio", "metrics.max_elongation", "metrics.average_triangularity",
     "metrics.axis_magnetic_mirror_ratio", "metrics.edge_magnetic_mirror_ratio",
     "metrics.edge_rotational_transform_over_n_field_periods", "metrics.axis_rotational_transform_over_n_field_periods",
     "metrics.vacuum_well", "metrics.flux_compression_in_regions_of_bad_curvature",
     "metrics.minimum_normalized_magnetic_gradient_scale_length"]


def regeln(baum, namen, X, gut):
    t = baum.tree_; out = []
    def lauf(k, pfad):
        if t.children_left[k] == -1:
            m = np.ones(len(X), bool)
            for f, op, v in pfad:
                m &= (X[:, f] <= v) if op == "<=" else (X[:, f] > v)
            n = int(m.sum())
            if n:
                out.append((gut[m].mean(), int(gut[m].sum()), n, [(namen[f], op, v) for f, op, v in pfad]))
            return
        f, v = t.feature[k], t.threshold[k]
        lauf(t.children_left[k], pfad + [(f, "<=", v)]); lauf(t.children_right[k], pfad + [(f, ">", v)])
    lauf(0, []); return sorted(out, key=lambda r: -r[1])


def main():
    A = []
    for f in sorted(glob.glob("sim/rohdaten/constellaration/train-*.parquet")):
        t = pq.read_table(f, columns=["metrics.qi"] + M)
        A.append(np.column_stack([t.column(c).to_numpy(zero_copy_only=False).astype(float) for c in ["metrics.qi"] + M]))
    A = np.vstack(A); A = A[np.isfinite(A).all(1) & (A[:, 0] > 0)]
    qi, X = A[:, 0], A[:, 1:]; gut = qi <= QI_GUT; nm = [c.replace("metrics.", "").replace("boundary.", "") for c in M]
    z = ["# Parameterkorridor fuer ein optimales Plasma (QI)", "",
         f"{len(qi)} Plasmen, gut = QI <= {QI_GUT:g}: {int(gut.sum())} ({100*gut.mean():.2f} %). Kennzahlen sind Messgroessen, keine Entwurfsparameter. Nur Korrelation.", "",
         "## (a) Kasten aus den guten Plasmen (5. bis 95. Perzentil)", "", "| Merkmal | von | bis | alle (5. bis 95.) |", "|---|---|---|---|"]
    lo = np.percentile(X[gut], 5, axis=0); hi = np.percentile(X[gut], 95, axis=0)
    la = np.percentile(X, 5, axis=0); ha = np.percentile(X, 95, axis=0)
    for j, n in enumerate(nm):
        z.append(f"| {n} | {lo[j]:.3g} | {hi[j]:.3g} | {la[j]:.3g} bis {ha[j]:.3g} |")
    inn = np.all((X >= lo) & (X <= hi), axis=1)
    z += ["", f"Im Kasten: {int(inn.sum())} Plasmen, davon gut {int((inn & gut).sum())}: Reinheit {100*(inn&gut).sum()/max(inn.sum(),1):.1f} %, "
          f"Abdeckung {100*(inn&gut).sum()/gut.sum():.1f} % der guten (Grundrate {100*gut.mean():.2f} %)."]
    for tiefe in (3, 5):
        b = DecisionTreeClassifier(max_depth=tiefe, min_samples_leaf=50, class_weight={0: 1, 1: 5}, random_state=0).fit(X, gut)
        R = regeln(b, nm, X, gut)
        z += ["", f"## (b) Entscheidungsbaum Tiefe {tiefe}: Bereiche mit den meisten guten Plasmen", "",
              "| Reinheit | gut | im Bereich | Bedingungen |", "|---|---|---|---|"]
        for rein, g, n, pf in R[:5]:
            z.append(f"| {100*rein:.0f} % | {g} | {n} | " + "; ".join(f"{a} {op} {v:.3g}" for a, op, v in pf) + " |")
        top = R[:3]
        z.append(f"\nDie drei besten Bereiche zusammen decken {sum(r[1] for r in top)} von {int(gut.sum())} guten Plasmen ab ({100*sum(r[1] for r in top)/gut.sum():.0f} %).")
    open("docs/recherche/qi_tragwerk/qi_korridor.md", "w").write("\n".join(z) + "\n"); print("\n".join(z))


if __name__ == "__main__":
    main()
