"""Rangkorrelation der QI-Güte mit Plasmakennzahlen im ganzen ConStellaration-Datensatz.

Aufruf (nur .venv-constellaration): .venv-constellaration/bin/python -m stellarator.qi_einfluss
Ergebnis: docs/recherche/qi_tragwerk/qi_einfluss.md
Kleinere QI-Güte ist besser. Rangkorrelation positiv: größerer Wert, schlechteres QI.
Nur Korrelation, keine Ursache.
"""
import glob, math
import numpy as np
import pyarrow.parquet as pq

MERKMALE = ["metrics.aspect_ratio", "metrics.max_elongation", "metrics.average_triangularity",
            "metrics.axis_magnetic_mirror_ratio", "metrics.edge_magnetic_mirror_ratio",
            "metrics.edge_rotational_transform_over_n_field_periods",
            "metrics.axis_rotational_transform_over_n_field_periods",
            "metrics.vacuum_well", "metrics.flux_compression_in_regions_of_bad_curvature",
            "metrics.minimum_normalized_magnetic_gradient_scale_length"]


def rang(v):
    o = np.argsort(v, kind="stable"); r = np.empty(len(v)); r[o] = np.arange(len(v)); return r


def main():
    fs = sorted(glob.glob("sim/rohdaten/constellaration/train-*.parquet"))
    cols = ["metrics.qi", "boundary.n_field_periods"] + MERKMALE
    teile = []
    for f in fs:
        pf = pq.ParquetFile(f)
        have = [c for c in cols if c in pf.schema_arrow.names]
        for b in pf.iter_batches(batch_size=20000, columns=have):
            teile.append({c: np.asarray(b.column(c).to_numpy(zero_copy_only=False), dtype=float) for c in have})
    have = teile[0].keys()
    D = {c: np.concatenate([t[c] for t in teile]) for c in have}
    qi = D["metrics.qi"]
    ok = np.isfinite(qi) & (qi > 0)
    z = ["# QI-Güte und Plasmakennzahlen im ganzen Datensatz", "",
         f"Plasmen mit gültigem QI: {int(ok.sum())} von {len(qi)}. Kleineres QI ist besser. "
         "Rangkorrelation mit log10(QI): positiv = größerer Wert, schlechteres QI. Nur Korrelation, keine Ursache.", "",
         "| Merkmal | Rangkorrelation | gültige Werte |", "|---|---|---|"]
    lq = rang(np.log10(qi[ok]))
    for c in have:
        if c in ("metrics.qi",): continue
        m = ok & np.isfinite(D[c])
        a = rang(np.log10(qi[m])); b = rang(D[c][m])
        r = float(np.corrcoef(a, b)[0, 1])
        z.append(f"| {c.replace('metrics.','')} | {r:+.2f} | {int(m.sum())} |")
    if "boundary.n_field_periods" in D:
        z += ["", "| Feldperioden | Anzahl | QI Median | bestes QI |", "|---|---|---|---|"]
        n = D["boundary.n_field_periods"]
        for k in sorted(set(n[ok & np.isfinite(n)])):
            m = ok & (n == k)
            z.append(f"| {int(k)} | {int(m.sum())} | {np.median(qi[m]):.4f} | {qi[m].min():.5f} |")
    open("docs/recherche/qi_tragwerk/qi_einfluss.md", "w").write("\n".join(z) + "\n")
    print("\n".join(z))


if __name__ == "__main__":
    main()
