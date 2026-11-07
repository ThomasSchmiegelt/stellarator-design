"""spulen_satz.py — eigene Spulensätze (simsopt-JSON) in einen Satz-Ordner für qi_spulen.py (freie Grenze) umschreiben.

  .venv-opt/bin/python -m stellarator.spulen_satz export <biot_savart.json> <boundary.json> <ziel_ordner> [<faktor>]
  .venv-opt/bin/python -m stellarator.spulen_satz pruefe <ziel_ordner>

Satz-Ordner (relativ zum Projekt, z. B. sim/kette_k3/satz_A085):
  boundary.json  Plasmarand im Datensatzmaßstab (constellaration SurfaceRZFourier, wie proxima_spulen_dje/boundary.json)
  spulen.json    {"format": "simsopt_basis", "nfp", "stellsym", "order", "nq", "basis_x": [[dofs CurveXYZFourier]],
                  "currents": [A je Basisspule], "faktor": Längenfaktor, "quelle": ...}
Die Basisspulen sind die ersten nb Spulen des gespeicherten BiotSavart (coils_via_symmetries legt sie zuerst an).
<faktor> skaliert die Länge (Fourier-Koeffizienten sind linear in den Punkten): zwei_ringe.py rechnet im um
1,699 vergrößerten Maßstab (wout_skaliert.nc), qi_spulen.py im Datensatzmaßstab -> faktor = 1/1,699.
Der Strom ist egal: qi_spulen.kalibrierung skaliert alle Ströme gemeinsam auf den offiziellen Toroidalfluss.
qi_spulen.py liest den Satz, wenn QI_SATZ=<ziel_ordner> gesetzt ist.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def flaeche(boundary_json, nphi=128, ntheta=64, voll=True):
    """simsopt-SurfaceRZFourier aus constellaration-boundary.json (r_cos[m, n + ntor], z_sin)."""
    from simsopt.geo import SurfaceRZFourier
    b = json.loads(Path(boundary_json).read_text())
    rc, zs = np.asarray(b["r_cos"]), np.asarray(b["z_sin"]); nt = rc.shape[1] // 2; nfp = int(b["n_field_periods"])
    qp = np.linspace(0, 1 if voll else 1 / (2 * nfp), nphi, endpoint=False)
    s = SurfaceRZFourier(nfp=nfp, stellsym=True, mpol=rc.shape[0] - 1, ntor=nt, quadpoints_phi=qp,
                         quadpoints_theta=np.linspace(0, 1, ntheta, endpoint=False))
    for m in range(rc.shape[0]):
        for n in range(-nt, nt + 1):
            if m == 0 and n < 0:
                continue
            s.set_rc(m, n, float(rc[m, n + nt])); s.set_zs(m, n, float(zs[m, n + nt]))
    return s


def feldfehler(basis, I, nfp, s):
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    bs = BiotSavart(coils_via_symmetries(basis, [Current(float(x)) for x in I], nfp, True))
    bs.set_points(s.gamma().reshape(-1, 3)); B = bs.B().reshape(s.gamma().shape)
    bn = np.abs((B * s.unitnormal()).sum(2)) / np.linalg.norm(B, axis=2)
    return float(bn.mean()), float(bn.max())


def lade_satz(ordner):
    from simsopt.geo import CurveXYZFourier
    d = json.loads((Path(ordner) / "spulen.json").read_text())
    basis = []
    for x in d["basis_x"]:
        c = CurveXYZFourier(d["nq"], d["order"]); c.x = np.asarray(x, float); basis.append(c)
    return basis, np.asarray(d["currents"], float), int(d["nfp"])


def export(bs_json, boundary_json, ziel, faktor=1.0, nb=None):
    from simsopt import load
    ziel = ROOT / ziel if not Path(ziel).is_absolute() else Path(ziel); ziel.mkdir(parents=True, exist_ok=True)
    bs = load(str(bs_json)); sp = bs.coils
    nfp = int(json.loads(Path(boundary_json).read_text())["n_field_periods"])
    nb = nb or len(sp) // (2 * nfp)
    basis_x, I = [], []
    for c in sp[:nb]:
        k = c.curve; I.append(float(c.current.get_value()))
        basis_x.append((np.asarray(k.x) * faktor).tolist())
    k0 = sp[0].curve
    d = {"format": "simsopt_basis", "nfp": nfp, "stellsym": True, "order": int(k0.order), "nq": len(k0.quadpoints),
         "basis_x": basis_x, "currents": I, "faktor": faktor, "quelle": str(Path(bs_json).relative_to(ROOT)) if str(bs_json).startswith(str(ROOT)) else str(bs_json)}
    (ziel / "spulen.json").write_text(json.dumps(d, indent=1))
    if Path(boundary_json).resolve() != (ziel / "boundary.json").resolve():
        shutil.copy(boundary_json, ziel / "boundary.json")
    return pruefe(ziel)


def pruefe(ziel):
    ziel = ROOT / ziel if not Path(ziel).is_absolute() else Path(ziel)
    basis, I, nfp = lade_satz(ziel)
    s = flaeche(ziel / "boundary.json")
    m, x = feldfehler(basis, I, nfp, s)
    from simsopt.field import Current, coils_via_symmetries
    from simsopt.geo import CurveSurfaceDistance, CurveCurveDistance
    sp = coils_via_symmetries(basis, [Current(float(i)) for i in I], nfp, True)
    a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0)))))
    j = {"Bn_mittel": m, "Bn_max": x, "n_basis": len(basis), "n_spulen": len(sp), "a": a,
         "abstand_plasma_a": float(CurveSurfaceDistance([c.curve for c in sp], s, 0.0).shortest_distance()) / a,
         "spule_spule_a": float(CurveCurveDistance([c.curve for c in sp], 0.0, num_basecurves=len(basis)).shortest_distance()) / a}
    (ziel / "pruefung_satz.json").write_text(json.dumps(j, indent=1)); print(json.dumps(j))
    return j


if __name__ == "__main__":
    if sys.argv[1] == "export":
        export(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), sys.argv[4], float(eval(sys.argv[5])) if len(sys.argv) > 5 else 1.0)
    elif sys.argv[1] == "pruefe":
        pruefe(sys.argv[2])
