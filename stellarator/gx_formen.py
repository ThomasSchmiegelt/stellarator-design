"""gx_formen.py -- GX-Läufe für Pool-Formen vorbereiten: Gleichgewicht (VMEC++ über ConStellaration forward_model,
default_high_fidelity) als wout schreiben und GX-Eingabe aus dem W7-X-Benchmark ableiten (gleiche Gradienten,
Auflösung, Fläche s = 0,64, Feldlinie alpha = 0).

KI-generiert (Claude Opus, 2026-11-11). Erwartung: sim/gx_pilot/ERWARTUNG.md.

  .venv-constellaration/bin/python -m stellarator.gx_formen DZrUR4dAT8H3EQvsN4XPRnL [weitere IDs] [--tmax 1000]
  ~/cae_projekte/gx/deps/venv/bin/python -m stellarator.gx_formen sammeln   -> sim/gx_pilot/gx_werte.json

Herkunft der Formen: Randflächen aus sim/spulenfreundlich/boundary/<id>.json (ConStellaration-Datensatz, unverändert).
Ausgabe: ~/cae_projekte/gx/laeufe/<id>/ (wout_<id>.nc, ergebnis_vmec.json), GX-Eingabe laeufe/linked/<id>/<id>.in.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAEUFE = Path.home() / "cae_projekte/gx/laeufe"
VORLAGE = LAEUFE / "w7x_benchmark" / "w7x_adiabatic_electrons.in"


def eingabe(id_, tmax):
    t = VORLAGE.read_text()
    t = t.replace('vmec_file = "wout_w7x.nc"', f'vmec_file = "wout_{id_}.nc"')
    t = re.sub(r"^ t_max = [0-9.]+", f" t_max = {tmax:.1f}", t, flags=re.M)
    t = re.sub(r"^ fields = true", " fields = false", t, flags=re.M)
    t = re.sub(r"^ moments = true", " moments = false", t, flags=re.M)
    assert f"wout_{id_}.nc" in t
    return f"# KI-generiert: aus benchmarks/nonlinear/w7x/w7x_adiabatic_electrons.in, nur vmec_file, t_max, fields/moments geändert\n" + t


def vorbereiten(id_, tmax):
    from constellaration import forward_model
    from constellaration.geometry import surface_rz_fourier as srf
    aus = LAEUFE / id_
    aus.mkdir(parents=True, exist_ok=True)
    w = aus / f"wout_{id_}.nc"
    if not w.exists():
        b = json.loads((ROOT / "sim" / "spulenfreundlich" / "boundary" / f"{id_}.json").read_text())
        m, wout = forward_model.forward_model(srf.SurfaceRZFourier.model_validate(b),
                                              settings=forward_model.ConstellarationSettings.default_high_fidelity())
        wout.save(w)
        info = {"id": id_, "qi": m.qi,
                "turbulenz_ersatz": m.flux_compression_in_regions_of_bad_curvature,
                "aspect_ratio": m.aspect_ratio, "iota_rand": m.edge_rotational_transform_over_n_field_periods}
        (aus / "ergebnis_vmec.json").write_text(json.dumps(info, indent=1, default=float))
        print(json.dumps(info, default=float), flush=True)
    z = LAEUFE / "linked" / id_                      # B-074: für Formvergleiche immer boundary = "linked"
    z.mkdir(parents=True, exist_ok=True)
    if not (z / w.name).exists():
        (z / w.name).symlink_to(w)
    (z / f"{id_}.in").write_text(eingabe(id_, tmax).replace('boundary = "fix aspect"', 'boundary = "linked"'))
    assert 'boundary = "linked"' in (z / f"{id_}.in").read_text()
    print("fertig", z, flush=True)


def sammeln(ab=100.0):
    """Mittel Q_i/Q_GB (t >= ab) aller fertigen linked-Läufe -> sim/gx_pilot/gx_werte.json (für formen_vergleich.py)."""
    import numpy as np, netCDF4
    werte, ungueltig = {}, {}
    for o in sorted((LAEUFE / "linked").iterdir()):
        f = o / f"{o.name}.out.nc"
        if not f.exists() or "End time" not in (o / "gx.log").read_text(errors="replace"):
            continue
        d = netCDF4.Dataset(f); t = np.array(d["Grids/time"][:]); q = np.array(d["Diagnostics/HeatFlux_st"][:, 0])
        m = t >= ab
        if m.sum() < 20 or not np.isfinite(q[m]).all():
            ungueltig[o.name] = "NaN oder zu kurz"; continue
        bl = [b.mean() for b in np.array_split(q[m], 4)]
        werte[o.name] = {"Q_i": round(float(q[m].mean()), 3), "fehler": round(float(np.std(bl, ddof=1) / 2), 3), "t_ende": round(float(t[-1]))}
    aus = ROOT / "sim" / "gx_pilot" / "gx_werte.json"
    aus.write_text(json.dumps({"hinweis": "KI-generiert; GX nichtlinear, adiabatische Elektronen, s=0,64, alpha=0, a/L_T=3, a/L_n=1, boundary linked, Mittel t>=%g" % ab,
                               "werte": werte, "ungueltig": ungueltig}, indent=1))
    print(f"{len(werte)} Werte, {len(ungueltig)} ungültig -> {aus}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["sammeln"]:
        sammeln(); sys.exit()
    tmax = float(a[a.index("--tmax") + 1]) if "--tmax" in a else 1000.0
    for x in [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--tmax")]:
        vorbereiten(x, tmax)
