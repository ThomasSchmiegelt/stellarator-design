"""qi_guete.py — QI-Güte eines Datensatz-Randes (forward_model mit QI-Rechnung), damit niedrige Spulenkraft nicht mit schlechtem Plasma erkauft wird.

  .venv-constellaration/bin/python -m stellarator.qi_guete <fall> ...   # "" = Satz 1; schreibt qi_guete.json in den Fallordner
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    from constellaration import forward_model
    from constellaration.geometry import surface_rz_fourier as srf
    for fall in sys.argv[1:]:
        o = ROOT / "sim" / "constellaration" / "qi" / f"proxima_spulen_{fall}"
        b = srf.SurfaceRZFourier.model_validate(json.loads((o / "boundary.json").read_text()))
        m, _ = forward_model.forward_model(b, settings=forward_model.ConstellarationSettings.default_high_fidelity())
        k = {a: (float(v) if isinstance(v, (int, float)) else None) for a, v in m.model_dump().items()}
        (o / "qi_guete.json").write_text(json.dumps(k, indent=1)); print(fall, k, flush=True)


if __name__ == "__main__":
    main()
