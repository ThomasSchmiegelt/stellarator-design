"""proxima_spulen.py — Proximas fertigen QI-Spulensatz (CoilStellaration) in unsere Kette geben (Tragwerk, Package).

  .venv-constellaration/bin/python -m stellarator.proxima_spulen vmec    # Rand skalieren, VMEC++ -> wout
  .venv-opt/bin/python -m stellarator.proxima_spulen spulen              # Kurven einlesen, Kontrolle Bn, Kettendateien
  .venv/bin/python -m stellarator.kopplung punkt --studie qi_proxima --nr 0 --p ...   # Tragwerk/Package/Supraleiter

Quellen (beide MIT, huggingface.co/datasets/proxima-fusion/...): Spulensatz DnFiaMhotvUCEFyC7wg9opq aus
coilstellaration (coilsets/part-4.parquet), Rand D9xMKRF5avCa4rJkPgYQmeB aus constellaration (data/train-00001).
Kurvenformat: coil_x_n/coil_y_n/coil_z_n je Basisspule 15 Zahlen = Moden n = -7..7 (Annahme wie DESC
FourierXYZCurve: n >= 0 Kosinus, n < 0 Sinus der Ordnung |n|); Kontrolle über den Feldfehler auf dem Rand.
Maßstab: Rand und Spulen mit f = (V_0169 / V_rand)^(1/3) in Einheitslänge vergrößert (wie constellaration_bruecke),
L wie 0169 -> gleiches Plasmavolumen (1096 m3). Ströme mit f skaliert (B ~ I/L); die Kette kalibriert ohnehin auf 6,5 T.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FALL = sys.argv[2] if len(sys.argv) > 2 else ""                  # "" = erster Satz (DnFia..., Ordner proxima_spulen)
O = ROOT / "sim" / "constellaration" / "qi" / ("proxima_spulen" + (f"_{FALL}" if FALL else ""))
STUDIE = ROOT / "sim" / "kopplung" / ("qi_proxima" + (f"_{FALL}" if FALL else ""))
DATEN = ROOT / "sim" / "rohdaten"   # Rohdaten (coilstellaration/, constellaration/); hier Verweis auf 2. Platte


def holen():
    """holen <fall> <coilset_id> <boundary_id> <coilsets/part-N.parquet>: Spulensatz + Rand aus den Parquet-Dateien."""
    import pyarrow.parquet as pq
    cid, bid, teil = sys.argv[3], sys.argv[4], sys.argv[5]
    O.mkdir(parents=True, exist_ok=True)
    t = pq.read_table(DATEN / "coilstellaration" / teil, filters=[("id", "=", cid)])
    (O / "coilset.json").write_text(t.column("json")[0].as_py())
    for f in sorted((DATEN / "constellaration").glob("train-*.parquet")):
        t = pq.read_table(f, columns=["plasma_config_id", "boundary.json"], filters=[("plasma_config_id", "=", bid)])
        if t.num_rows:
            (O / "boundary.json").write_text(t.column("boundary.json")[0].as_py()); break
    else:
        raise SystemExit(f"Rand {bid} nicht gefunden")
    (O / "quelle.json").write_text(json.dumps({"coilset": cid, "boundary": bid}))
WOUT0 = ROOT / "sim" / "invers" / "qa_nfp2_A45" / "wout_qa_nfp2_A45.nc"


def volumen(w):
    from scipy.io import netcdf_file
    with netcdf_file(str(w), "r", mmap=False) as f:
        return float(f.variables["volume_p"][()])


def vmec():
    from constellaration import forward_model
    from constellaration.geometry import surface_rz_fourier as srf
    b = json.loads((O / "boundary.json").read_text())
    settings = forward_model.ConstellarationSettings.default_high_fidelity_skip_qi()
    m, w = forward_model.forward_model(srf.SurfaceRZFourier.model_validate(b), settings=settings)
    w.save(O / "wout_roh.nc")
    f = (volumen(WOUT0) / volumen(O / "wout_roh.nc")) ** (1 / 3)
    for k in ("r_cos", "z_sin", "r_sin", "z_cos"):
        if b.get(k) is not None:
            b[k] = (np.asarray(b[k]) * f).tolist()
    m2, w2 = forward_model.forward_model(srf.SurfaceRZFourier.model_validate(b), settings=settings)
    w2.save(O / "wout_skaliert.nc")
    k = {kk: (float(v) if isinstance(v, (int, float, np.floating)) else None) for kk, v in m2.model_dump().items()}
    (O / "skalierung.json").write_text(json.dumps({"faktor": f, "kenngroessen": k}, indent=1)); print(f, k)


def kurven(f, vorzeichen=1):
    """Basisspulen als simsopt CurveXYZFourier (Ordnung 7), mit f skaliert. vorzeichen: Sinusglieder +/-."""
    from simsopt.geo import CurveXYZFourier
    c = json.loads((O / "coilset.json").read_text()); N = 7
    out = []
    for i in range(len(c["currents"])):
        k = CurveXYZFourier(200, N)
        dofs = []
        for xyz in ("coil_x_n", "coil_y_n", "coil_z_n"):
            a = np.asarray(c[xyz][i]) * f
            dofs.append(a[N])                                     # n = 0
            for n in range(1, N + 1):
                dofs += [vorzeichen * a[N - n], a[N + n]]         # simsopt: xs(n), xc(n)
        k.x = np.asarray(dofs, float); out.append(k)
    return out, [I * f for I in c["currents"]], int(c["n_field_periods"])


def spulen():
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from simsopt.geo import SurfaceRZFourier, CurveCurveDistance, CurveSurfaceDistance
    sys.path.insert(0, str(ROOT))
    from invers.stufe2_spulen import plasma_rand
    f = json.loads((O / "skalierung.json").read_text())["faktor"]
    w = O / "wout_skaliert.nc"
    s = SurfaceRZFourier.from_wout(str(w), range="full torus", nphi=128, ntheta=64)
    best = None
    for vz in (1, -1):                                            # Konvention prüfen, nicht raten
        basis, I, nfp = kurven(f, vz)
        sp = coils_via_symmetries(basis, [Current(x) for x in I], nfp, True)
        bs = BiotSavart(sp); bs.set_points(s.gamma().reshape(-1, 3))
        B = bs.B().reshape(s.gamma().shape); n = s.unitnormal()
        Bn = np.abs((B * n).sum(2)) / np.linalg.norm(B, axis=2)
        print(f"Sinus-Vorzeichen {vz:+d}: Bn mittel {Bn.mean():.2e}, max {Bn.max():.2e}", flush=True)
        if best is None or Bn.mean() < best[0]:
            best = (Bn.mean(), Bn.max(), vz, basis, I, nfp, sp, bs)
    bn, bnmax, vz, basis, I, nfp, sp, bs = best
    kurv = [c.curve for c in sp]
    d_sp = CurveSurfaceDistance(kurv, s, 0.0).shortest_distance()
    d_ss = CurveCurveDistance(kurv, 0.0, num_basecurves=len(basis)).shortest_distance()
    kr = max(float(np.max(c.kappa())) for c in basis)
    po = STUDIE / "punkte" / "0000"; po.mkdir(parents=True, exist_ok=True)
    q = json.loads((O / "quelle.json").read_text())["coilset"] if (O / "quelle.json").exists() else "DnFiaMhotvUCEFyC7wg9opq"
    s2 = {"quelle": f"Proxima CoilStellaration {q}", "sinus_vorzeichen": vz, "nfp": nfp,
          "n_basis": len(basis), "n_spulen": len(sp), "Bn_rel_mittel": float(bn), "Bn_rel_max": float(bnmax),
          "laenge_basis_m": [float(np.sum(np.linalg.norm(c.gammadash(), axis=1)) / len(c.quadpoints)) for c in basis],
          "abstand_ss_min_m": float(d_ss), "abstand_sp_min_m": float(d_sp), "kruemmung_max_1_m": kr,
          "biegeradius_min_m": 1 / kr, "stroeme_basis_A": I}
    s2["laenge_summe_m"] = float(sum(s2["laenge_basis_m"]))
    (po / "stufe2.json").write_text(json.dumps(s2, indent=1))
    bs.save(str(po / "biot_savart.json"))
    R0 = float(s.get_rc(0, 0))
    aus = {"quelle": "proxima", "wout": str(w), "nfp": nfp, "stellsym": True, "n_basis": len(basis), "R0_m": R0,
           "einheit": "m", "plasma_rand": plasma_rand(s, w), "abstand_sp_min_m": float(d_sp),
           "spulen": [{"name": f"S{i % len(basis) + 1}_k{i // len(basis)}", "typ": f"S{i % len(basis) + 1}",
                       "punkte_m": c.curve.gamma().tolist(), "strom_A": float(c.current.get_value())}
                      for i, c in enumerate(sp)]}
    (po / "spulen.json").write_text(json.dumps(aus))
    sys.path.insert(0, str(ROOT))
    from stellarator import kopplung as k
    (STUDIE / "plasma.json").write_text(json.dumps({"wout": str(w.relative_to(ROOT)), "L": k.L, "nfp": nfp}, indent=1))
    a_u = np.sqrt(volumen(w) / (2 * np.pi ** 2 * R0))
    print(json.dumps({kk: v for kk, v in s2.items() if not isinstance(v, list)}, indent=1))
    print(f"Anlage: R {R0 * k.L:.2f} m, a {a_u * k.L:.2f} m, Abstand Spule-Plasma {d_sp * k.L:.2f} m = {d_sp / a_u:.2f} a, "
          f"Biegeradius {k.L / kr:.2f} m, Spule-Spule {d_ss * k.L:.2f} m")


if __name__ == "__main__":
    {"holen": holen, "vmec": vmec, "spulen": spulen}[sys.argv[1]]()
