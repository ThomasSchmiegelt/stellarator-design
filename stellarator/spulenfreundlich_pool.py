"""Kandidatenpool fuer die Suche nach einer spulenfreundlichen Datensatzform (2026-11-09, Plan Spulenwolke/Weg 1).
Regel des Nutzers "Plasma zuerst": Pool = Datensatzformen mit gutem QI (<= QI_MAX), nfp 2..5, sortiert nach QI.
Ausgabe sim/spulenfreundlich/pool.tsv (id, nfp, qi, A, elong, iota, spiegel, LgradB) + boundary/<id>.json (unveraendert).
Aufruf: .venv-constellaration/bin/python -m stellarator.spulenfreundlich_pool [QI_MAX=0.0005]"""
import glob, json, sys
from pathlib import Path
import numpy as np, pyarrow as pa, pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[1]; O = ROOT / "sim/spulenfreundlich"
QI_MAX = float(sys.argv[1]) if len(sys.argv) > 1 else 5e-4
S = ["plasma_config_id", "metrics.qi", "boundary.n_field_periods", "metrics.aspect_ratio", "metrics.max_elongation",
     "metrics.edge_rotational_transform_over_n_field_periods", "metrics.edge_magnetic_mirror_ratio",
     "metrics.minimum_normalized_magnetic_gradient_scale_length", "boundary.json"]
t = pa.concat_tables([pq.read_table(f, columns=S) for f in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet")))])
d = {k: t.column(k).to_pylist() for k in S}
qi = np.array([np.nan if v is None else v for v in d["metrics.qi"]], float)
nfp = np.array([0 if v is None else v for v in d["boundary.n_field_periods"]])
ok = np.isfinite(qi) & (qi <= QI_MAX) & (nfp >= 2) & (nfp <= 5)
idx = np.where(ok)[0]; idx = idx[np.argsort(qi[idx])]
(O / "boundary").mkdir(parents=True, exist_ok=True)
z = ["id\tnfp\tqi\tA\telong\tiota\tspiegel\tLgradB"]; gesehen = set()
for i in idx:
    pid = d["plasma_config_id"][i]
    if pid in gesehen: continue
    gesehen.add(pid)
    (O / "boundary" / f"{pid}.json").write_text(d["boundary.json"][i])
    f = lambda k: d[k][i] if d[k][i] is not None else float("nan")
    z.append(f"{pid}\t{nfp[i]}\t{qi[i]:.3e}\t{f('metrics.aspect_ratio'):.2f}\t{f('metrics.max_elongation'):.2f}\t"
             f"{f('metrics.edge_rotational_transform_over_n_field_periods'):.3f}\t{f('metrics.edge_magnetic_mirror_ratio'):.3f}\t"
             f"{f('metrics.minimum_normalized_magnetic_gradient_scale_length'):.3f}")
(O / "pool.tsv").write_text("\n".join(z) + "\n")
print(len(z) - 1, "Formen; nfp:", {int(k): int((nfp[idx] == k).sum()) for k in range(2, 6)})
