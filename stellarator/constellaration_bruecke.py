"""constellaration_bruecke.py — Brücke ConStellaration -> eigene Kette (Spulen, Tragwerk, Package).

  .venv-constellaration/bin/python -m stellarator.constellaration_bruecke vmec      # Gleichgewichte + Nachbewertung
  .venv-constellaration/bin/python -m stellarator.constellaration_bruecke skalieren # auf Volumen von 0169 (Einheit)
  .venv/bin/python -m stellarator.constellaration_bruecke studien                    # plasma.json je Studie anlegen
  danach je Studie: .venv/bin/python -m stellarator.kopplung punkt --studie qi_<name> --nr 0 --p ...

Quelle der Plasmaränder: zulässige Einreichungen zur Aufgabe "simple_to_build" (QI) der öffentlichen Rangliste
huggingface.co/datasets/proxima-fusion/constellaration-bench-results (MIT). Ausgewählt: beste mit nfp 3, beste mit
nfp 4, beste mit nfp 2 (wie unser QA-Plasma). Einreicher werden nicht genannt, nur Zeitstempel und Wertung.

Schritt "vmec": VMEC++ (forward_model, default_high_fidelity) je Rand -> Kenngrößen, Zulässigkeit und Wertung nach
SimpleToBuildQIStellarator (Kontrolle gegen die Rangliste) und wout_<name>.nc für simsopt/unsere Kette.
Schritt "skalieren": Rand mit f = (V_0169 / V_QI)^(1/3) (Einheitsvolumen) vergrößern und VMEC++ erneut rechnen. Dann
hat das QI-Plasma in Einheitslänge dasselbe Volumen wie unser QA-Plasma, und alle Einstellungen der Spulenoptimierung
(Krümmung, Abstände, Strafgewichte; in Einheitslänge auf 0169 abgestimmt) gelten unverändert. Der erste Versuch ohne
diese Skalierung (R = 1) scheiterte: Spulen fielen ins Plasma, Bn 0,16 (F-165). Kenngrößen sind dimensionslos und
müssen gleich bleiben (Kontrolle).
Schritt "studien": L wie 0169 (gleiches Plasmavolumen -> gleiche Fusionsleistung bei gleichem Beta und Feld, P_FUS
bleibt gültig); Abstände Spule-Plasma und Spule-Spule wie 0169, Spulenlänge mit dem Umfang (a + d) skaliert,
Startradius R1 = a + 1,4 d (ergibt für 0169 die bisherigen 0,5).
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ABLAGE = ROOT / "sim" / "constellaration" / "rangliste"   # heruntergeladene *_results.json (hier Verweis auf 2. Platte)
AUS = ROOT / "sim" / "constellaration" / "qi"
AUSWAHL = {   # name: (Einreichung, nfp)
    "nfp3_s068": "2026-10-30T16-35-21.215245_simple_to_build_results.json",
    "nfp4_s049": "2026-09-10T18-18-08",
    "nfp2_s033": "2026-10-02T20-40-09",
}
REF = ROOT / "sim" / "kopplung" / "netz_normal" / "punkte" / "0169"


def datei(muster):
    return next(p for p in sorted(ABLAGE.glob("*.json")) if p.name.startswith(muster[:19]))


def vmec():
    from constellaration import forward_model, problems
    from constellaration.geometry import surface_rz_fourier as srf
    P = problems.SimpleToBuildQIStellarator()
    for name, muster in AUSWAHL.items():
        o = AUS / name; o.mkdir(parents=True, exist_ok=True)
        if (o / "bewertung.json").exists():
            print(name, "schon da"); continue
        d = json.loads(datei(muster).read_text())
        b = json.loads(d["boundary_json"]); (o / "boundary.json").write_text(json.dumps(b))
        rand = srf.SurfaceRZFourier.model_validate(b)
        m, w = forward_model.forward_model(rand, settings=forward_model.ConstellarationSettings.default_high_fidelity())
        w.save(o / f"wout_{name}.nc")
        e = {"quelle": datei(muster).name, "rangliste": {k: d[k] for k in ("objective", "feasibility", "score")},
             "nachgerechnet": {"objective": P.get_objective(m)[0], "feasibility": float(P.compute_feasibility(m)),
                               "score": float(P._score(m)) if P.is_feasible(m) else 0.0},
             "kenngroessen": {k: (float(v) if isinstance(v, (int, float, np.floating)) else None)
                              for k, v in m.model_dump().items()},
             "nfp": int(rand.n_field_periods)}
        (o / "bewertung.json").write_text(json.dumps(e, indent=1)); print(name, json.dumps(e, indent=1), flush=True)


def skalieren():
    from constellaration import forward_model, problems
    from constellaration.geometry import surface_rz_fourier as srf
    sys.path.insert(0, str(ROOT)); WOUT0 = ROOT / "sim" / "invers" / "qa_nfp2_A45" / "wout_qa_nfp2_A45.nc"
    V0 = volumen_einheit(WOUT0)[0]; P = problems.SimpleToBuildQIStellarator()
    for name in AUSWAHL:
        o = AUS / name
        if (o / "skaliert.json").exists():
            print(name, "schon da"); continue
        f = (V0 / volumen_einheit(o / f"wout_{name}.nc")[0]) ** (1 / 3)
        b = json.loads((o / "boundary.json").read_text())
        for k in ("r_cos", "z_sin", "r_sin", "z_cos"):
            if b.get(k) is not None:
                b[k] = (np.asarray(b[k]) * f).tolist()
        rand = srf.SurfaceRZFourier.model_validate(b)
        m, w = forward_model.forward_model(rand, settings=forward_model.ConstellarationSettings.default_high_fidelity())
        w.save(o / f"wout_{name}_skaliert.nc")
        alt = json.loads((o / "bewertung.json").read_text())["kenngroessen"]
        neu = {k: (float(v) if isinstance(v, (int, float, np.floating)) else None) for k, v in m.model_dump().items()}
        e = {"faktor": f, "score": float(P._score(m)) if P.is_feasible(m) else 0.0, "kenngroessen": neu,
             "abweichung_rel": {k: (neu[k] / alt[k] - 1) for k in neu if neu[k] is not None and alt.get(k)}}
        (o / "skaliert.json").write_text(json.dumps(e, indent=1)); print(name, json.dumps(e, indent=1), flush=True)


def volumen_einheit(wout):
    from scipy.io import netcdf_file
    with netcdf_file(str(wout), "r", mmap=False) as f:
        return float(f.variables["volume_p"][()]), float(f.variables["Rmajor_p"][()]), float(f.variables["Aminor_p"][()]), int(f.variables["nfp"][()])


def studien():
    sys.path.insert(0, str(ROOT))
    from stellarator import kopplung as k
    p0 = json.loads((REF / "param.json").read_text())
    V0, R0u, a0u, _ = volumen_einheit(k.WOUT)
    L0 = k.L; d0 = p0["abstand_sp"] * L0; ss0 = 0.1 * L0
    print(f"0169: V {V0 * L0 ** 3:.0f} m3, R {R0u * L0:.2f} m, a {a0u * L0:.2f} m, d {d0:.2f} m")
    for name in AUSWAHL:
        o = AUS / name; w = o / f"wout_{name}_skaliert.nc"
        V, Ru, au, nfp = volumen_einheit(w)
        L = L0; assert abs(V / V0 - 1) < 0.01, (V, V0)
        n_basis = 24 // (2 * nfp)
        laenge_m = p0["laenge_je"] * L0 * (au * L + d0) / (a0u * L0 + d0)
        q = {"abstand_sp": d0 / L, "abstand_ss": ss0 / L, "laenge_je": laenge_m / L, "n_basis": n_basis,
             "R1": au + 1.4 * d0 / L}
        st = k.WURZEL / f"qi_{name}"; st.mkdir(parents=True, exist_ok=True)
        (st / "plasma.json").write_text(json.dumps({"wout": str(w.relative_to(ROOT)), "L": L, "nfp": nfp,
                                                    "param_umgerechnet": q}, indent=1))
        print(f"{name}: L {L:.2f} m, R {Ru * L:.2f} m, a {au * L:.2f} m, A {Ru / au:.2f}, nfp {nfp}, Spulen {2 * nfp * n_basis}",
              {kk: round(v, 4) for kk, v in q.items()})


if __name__ == "__main__":
    {"vmec": vmec, "skalieren": skalieren, "studien": studien}[sys.argv[1]]()
