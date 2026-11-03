"""constellaration_bewertung.py — eigenes Plasma mit dem Bewertungsprogramm der ConStellaration Challenge pruefen.

  .venv-constellaration/bin/python stellarator/constellaration_bewertung.py [wout.nc]
  -> sim/constellaration/bewertung_<name>.json

Benutzt das Paket constellaration 0.2.6 (Proxima Fusion, Stand der Rangliste) in eigener Umgebung (Python 3.10).
Randflaeche aus der VMEC-Ausgabe (rmnc/zmns der aeussersten Flaeche), Aufgaben 1 (geometrisch) und 2 (QI, einfach
zu bauen); dazu alle Kenngroessen des Vorwaertsmodells.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.io import netcdf_file

ROOT = Path(__file__).resolve().parents[1]


def rand_aus_wout(pfad):
    from constellaration.geometry import surface_rz_fourier as srf
    f = netcdf_file(pfad, "r", mmap=False)
    xm = f.variables["xm"][:].astype(int); nfp = int(f.variables["nfp"][()]); xn = (f.variables["xn"][:] // nfp).astype(int)
    rc = f.variables["rmnc"][-1]; zs = f.variables["zmns"][-1]
    M, N = xm.max(), np.abs(xn).max()
    r_cos = np.zeros((M + 1, 2 * N + 1)); z_sin = np.zeros_like(r_cos)
    for m, n, a, b in zip(xm, xn, rc, zs):
        r_cos[m, n + N] = a; z_sin[m, n + N] = b
    return srf.SurfaceRZFourier(r_cos=r_cos, z_sin=z_sin, n_field_periods=nfp, is_stellarator_symmetric=True)


def main():
    from constellaration import problems, forward_model
    wout = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "sim/invers/qa_nfp2_A45/wout_qa_nfp2_A45.nc")
    rand = rand_aus_wout(wout)
    erg = {"wout": wout.name}
    for name, P in (("1_geometrisch", problems.GeometricalProblem()), ("2_einfach_QI", problems.SimpleToBuildQIStellarator())):
        try:
            e = P.evaluate(rand); erg[name] = e.model_dump(); print(name, e, flush=True)
        except ValueError as x:                                       # z. B. QA-Feld: QI-Abweichung nicht definiert
            erg[name] = {"fehler": str(x), "score": 0.0}; print(name, "nicht bewertbar:", x, flush=True)
    m, _ = forward_model.forward_model(rand, settings=forward_model.ConstellarationSettings.default_high_fidelity_skip_qi())
    erg["kenngroessen"] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else None) for k, v in m.model_dump().items()}
    print(json.dumps(erg["kenngroessen"], indent=1), flush=True)
    aus = ROOT / "sim" / "constellaration" / f"bewertung_{wout.stem}.json"; aus.write_text(json.dumps(erg, indent=1))
    print(aus)


if __name__ == "__main__":
    main()
