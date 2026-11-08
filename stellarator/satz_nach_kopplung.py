"""satz_nach_kopplung.py — Spulensatz der Kette K3 (simsopt_basis) in die Festigkeitskette (kopplung.py) geben.

  .venv-opt/bin/python -m stellarator.satz_nach_kopplung <satzordner> <studie> [--a 1.8] [--wout <nc>] [--herkunft "text"]

Liest <satzordner>/biot_savart.json (Fallback: ../biot_savart_<fall>.json) und die wout der freien Grenze
(Standard <satzordner>/frei/wout/k_n48000.nc) und schreibt nach sim/kopplung/<studie>/:
  plasma.json                  wout (relativ), L = a / a_u (a_u aus pruefung_satz.json), nfp, herkunft
  punkte/0000/spulen.json      Format punkte_m (Einheitsgeometrie, R0_m = 1, Strom je Spule signiert, Einheitsstrom)
  punkte/0000/biot_savart.json Kopie
  punkte/0000/stufe2.json      nur Feldfehler aus pruefung_satz.json (gekennzeichnet "aus Satzpruefung")
  punkte/0000/geometrie.json   per kopplung _geometrie (Plasmarand, Flaeche, Achsenfeld, Einheitsstrom)
Die Kette setzt den Strom je Spule nur mit der Option strom_je_spule=1 verschieden (kopplung.struktur_netz).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def konvertiere(satz: Path, studie: str, a_m: float = 1.8, wout: Path | None = None, herkunft: str = "") -> Path:
    from simsopt import load
    from simsopt.geo import SurfaceRZFourier
    satz = satz.resolve()
    wout = (Path(wout) if wout else satz / "frei" / "wout" / "k_n48000.nc").resolve()
    bsf = satz / "biot_savart.json"
    if not bsf.exists():
        fall = satz.name.removeprefix("satz_")
        bsf = satz.parent / f"biot_savart_{fall}.json"
    pr = json.loads((satz / "pruefung_satz.json").read_text())
    nfp = int(json.loads((satz / "boundary.json").read_text())["n_field_periods"])
    L = a_m / pr["a"]
    o = ROOT / "sim" / "kopplung" / studie; po = o / "punkte" / "0000"; po.mkdir(parents=True, exist_ok=True)
    bs = load(str(bsf)); coils = bs.coils
    nb = len(coils) // (2 * nfp)                                 # stellsym: 2 * nfp Kopien je Basisspule
    assert nb * 2 * nfp == len(coils), "Spulenzahl passt nicht zu nfp"
    spulen = []
    for i, c in enumerate(coils):
        q = np.linspace(0, 1, 200, endpoint=False)               # dichte Abtastung der Kurve (wie Proxima-Satz: 200)
        P = np.empty((len(q), 3)); c.curve.gamma_impl(P, q)
        spulen.append({"name": f"S{i % nb + 1}_k{i // nb}", "typ": f"S{i % nb + 1}", "punkte_m": P.tolist(),
                       "strom_A": float(c.current.get_value())})
    f = SurfaceRZFourier.from_wout(str(wout), s=1.0, range="full torus", nphi=200, ntheta=80)
    X = f.gamma(); R = np.hypot(X[..., 0], X[..., 1])
    ph0 = f.gamma()[0]                                           # phi = 0: Querschnitt in der xz-Ebene
    Ra = np.hypot(ph0[:, 0], ph0[:, 1])
    rand = {"R_min_m": float(R.min()), "R_max_m": float(R.max()), "Z_max_m": float(np.abs(X[..., 2]).max()),
            "R_achse_phi0_m": float(0.5 * (Ra.min() + Ra.max())), "R_aussen_phi0_m": float(Ra.max())}
    d_sp = float(pr.get("abstand_plasma_a", 0) * pr["a"])
    aus = {"quelle": "kette_k3", "satz": str(satz.relative_to(ROOT)), "wout": str(wout), "nfp": nfp, "stellsym": True,
           "n_basis": nb, "R0_m": 1.0, "einheit": "Einheitsgeometrie", "plasma_rand": rand, "abstand_sp_min_m": d_sp,
           "spulen": spulen}
    (po / "spulen.json").write_text(json.dumps(aus))
    shutil.copy(bsf, po / "biot_savart.json")
    s2 = {"quelle": "aus Satzpruefung (pruefung_satz.json), nicht von stufe2_spulen", "Bn_rel_mittel": pr["Bn_mittel"],
          "Bn_rel_max": pr["Bn_max"], "n_basis": nb, "n_spulen": len(coils)}
    (po / "stufe2.json").write_text(json.dumps(s2, indent=1))
    (o / "plasma.json").write_text(json.dumps({"wout": str(wout.relative_to(ROOT)), "L": L, "nfp": nfp, "a_m": a_m,
                                              "herkunft": herkunft}, indent=1))
    subprocess.run([sys.executable, "-m", "stellarator.kopplung", "_geometrie", str(po)], cwd=ROOT, check=True)
    g = json.loads((po / "geometrie.json").read_text())
    print(f"{studie}: nfp {nfp}, {len(coils)} Spulen ({nb} Basis), L {L:.4f}, Plasmaflaeche {g['plasma_flaeche_m2']:.0f} m2, "
          f"B_achse_einheit {g['B_achse_einheit_T']:.4f} T, I_einheit {g['I_einheit_A']:.3e} A")
    return po


def main():
    a = sys.argv[1:]
    opt = {}
    for k in ("--a", "--wout", "--herkunft"):
        if k in a:
            i = a.index(k); opt[k] = a[i + 1]; del a[i:i + 2]
    konvertiere(Path(a[0]), a[1], float(opt.get("--a", 1.8)), Path(opt["--wout"]) if "--wout" in opt else None,
                opt.get("--herkunft", ""))


if __name__ == "__main__":
    main()
