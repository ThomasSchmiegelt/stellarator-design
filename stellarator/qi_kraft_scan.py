"""qi_kraft_scan.py — Nettokraft je Spule für CoilStellaration-Sätze (der Datensatz enthält keine Kräfte).

  sim/qi_feld/kraft_scan.sh   # lädt fehlende Teile, dann -> docs/recherche/qi_tragwerk/kraft_scan.csv (fortlaufend, Wiederaufnahme)

Auswahl: DESC-Metriken, mittlerer Feldfehler <= 3e-3, Biegeradius >= 0,5 a. Kraft: F_k = I_k * Summe dl x B der ANDEREN Spulen
(Eigenkraft einer geschlossenen Schleife ist netto null). Bezugsgröße f = F mu0 / (B0^2 a^2), dimensionslos, B0 = Feld auf der Achse.
Damit sind Sätze verschieden großer Anlagen vergleichbar; kontrolliert an DRb36s... (Typen 31, 223, 641, 1170, 338, 112 MN).
"""
import csv
import glob
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "sim" / "rohdaten" / "coilstellaration"
AUS = ROOT / "docs" / "recherche" / "qi_tragwerk" / "kraft_scan.csv"
M = "desc_metrics/"
MU0 = 4e-7 * np.pi


def kraefte(c):
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from simsopt.geo import CurveXYZFourier
    N = 7; basis = []
    for i in range(len(c["currents"])):
        k = CurveXYZFourier(200, N); dofs = []
        for xyz in ("coil_x_n", "coil_y_n", "coil_z_n"):
            a = np.asarray(c[xyz][i], float)
            dofs.append(a[N])
            for n in range(1, N + 1):
                dofs += [a[N - n], a[N + n]]
        k.x = np.asarray(dofs); basis.append(k)
    sp = coils_via_symmetries(basis, [Current(float(x)) for x in c["currents"]], int(c["n_field_periods"]), True)
    F = []
    for k in range(len(basis)):
        bs = BiotSavart([s for j, s in enumerate(sp) if j != k])
        g = sp[k].curve.gamma(); dl = sp[k].curve.gammadash() / len(g)
        bs.set_points(np.ascontiguousarray(g))
        F.append(np.linalg.norm(float(sp[k].current.get_value()) * np.cross(dl, bs.B()).sum(0)))
    return np.asarray(F)


def main():
    sp = ["desc_coilset_id", "boundary.n_field_periods", "reqs/n_coils_per_half_period", M + "normalized_field_error/mean",
          M + "normalized_coil_curvatures/max", M + "normalized_coil_to_coil_min_distances/min", M + "normalized_coil_lengths/max",
          M + "on_axis_average_magnetic_field", M + "minor_radius"]
    t = pq.read_table(D / "results" / "eval-part-0.parquet", columns=sp).to_pandas().dropna()
    t["r"] = 1 / t[M + "normalized_coil_curvatures/max"]; t["bn"] = t[M + "normalized_field_error/mean"]
    w = t[(t.bn <= 3e-3) & (t.r >= 0.5)]
    w = w.set_index("desc_coilset_id")
    fertig = set()
    if AUS.exists():
        fertig = {z["id"] for z in csv.DictReader(AUS.open())}
    neu = not AUS.exists()
    with AUS.open("a", newline="") as f:
        o = csv.writer(f)
        if neu:
            o.writerow(["id", "nfp", "je_halbperiode", "bn", "biegeradius_a", "spule_spule_a", "laenge_max_a", "f_max", "f_mittel", "max_durch_mittel", "F_einheit_N"])
        ids = [i for i in list(w.index) + ["DRb36sGpjMdfrbfZz8vRqew"] if i not in fertig]
        print(len(ids), "Sätze offen", flush=True)
        for teil in sorted(glob.glob(str(D / "coilsets" / "part-*.parquet"))):
            q = pq.read_table(teil, columns=["id", "json"], filters=[("id", "in", ids)])
            for i, js in zip(q.column("id").to_pylist(), q.column("json").to_pylist()):
                c = json.loads(js); F = kraefte(c)
                r = t[t.desc_coilset_id == i].iloc[0]
                n = F * MU0 / (r[M + "on_axis_average_magnetic_field"] ** 2 * r[M + "minor_radius"] ** 2)
                o.writerow([i, int(r["boundary.n_field_periods"]), int(r["reqs/n_coils_per_half_period"]), f"{r.bn:.3e}", f"{r.r:.3f}",
                            f"{r[M + 'normalized_coil_to_coil_min_distances/min']:.3f}", f"{r[M + 'normalized_coil_lengths/max']:.2f}",
                            f"{n.max():.3f}", f"{n.mean():.3f}", f"{n.max() / n.mean():.2f}", " ".join(f"{x:.3e}" for x in F)])
                f.flush(); print(i, f"f_max {n.max():.2f}", flush=True)
    print("FERTIG kraft_scan", flush=True)


if __name__ == "__main__":
    main()
