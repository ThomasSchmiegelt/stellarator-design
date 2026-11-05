"""Weg A (Datensatz filtern) und Weg B (lokale Suche mit VMEC++) aus paarvergleich_plasma.md (F-240/F-241, B-051).

  .venv-constellaration/bin/python -m stellarator.qi_filter_suche filter          # Schritt A: filter138.json + 5 Startformen
  .venv-constellaration/bin/python -m stellarator.qi_filter_suche suche <k>       # Schritt B: lokale Suche ab Startform k (0..4), --weiter eingebaut
  .venv-constellaration/bin/python -m stellarator.qi_filter_suche eins <ein> <aus> # eine VMEC++-Rechnung (Kindprozess), Rand-JSON -> Ergebnis-JSON
  .venv-constellaration/bin/python -m stellarator.qi_filter_suche auswertung      # Tabelle aller Suchschritte

Schwellen: genau die aus constellaration/problems.py (installiertes Paket), keine eigenen.
Ziel der Suche: Aufgabe 3 (MHDStableQIStellarator) zulaessig, d. h. jede normierte Verletzung <= 0,01 (is_feasible);
dann ist die Wertung (Hypervolumen) > 0. Aufgabe 2 wird je Schritt mitgerechnet und berichtet.
Zielfunktion f = Summe der Quadrate der positiven normierten Verletzungen der Aufgabe 3 (offizielle Normierung,
problems._normalized_constraint_violations). Verfahren: (1+1)-Evolutionsstrategie mit gespiegelten Zufallsrichtungen,
Mustervorstoss nach Erfolg und Schrittweitenanpassung, in den 9 freien wichtigsten Koeffizienten (Surrogat-Rangliste, B-050),
Schrittlaenge 0,02 bis 0,3 Standardabweichungen (Datensatz). Kein Surrogat in der Suche.
Pausierbar: keine Wanduhr-Grenze; Grenze nur Prozess-CPU-Zeit (RLIMIT_CPU) der Einzelrechnung.
"""
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
O = ROOT / "sim" / "qi_flaeche"
S = O / "suche_lokal"
FILTER = O / "filter138.json"
N_START, BUDGET = 5, int(os.environ.get("BUDGET", "40"))
SIG0, SIG_MIN, SIG_MAX = 0.10, 0.02, 0.30
CPU_GRENZE = 3600                       # Sekunden Prozess-CPU-Zeit je Einzelrechnung (Pause zaehlt nicht mit)
SPALTEN = ["plasma_config_id", "metrics.qi", "metrics.aspect_ratio", "metrics.edge_rotational_transform_over_n_field_periods",
           "metrics.edge_magnetic_mirror_ratio", "metrics.flux_compression_in_regions_of_bad_curvature", "metrics.vacuum_well",
           "metrics.max_elongation", "metrics.minimum_normalized_magnetic_gradient_scale_length", "metrics.average_triangularity",
           "boundary.n_field_periods"]


def tabelle():
    import glob
    import pyarrow as pa
    import pyarrow.parquet as pq
    t = pa.concat_tables([pq.read_table(f, columns=SPALTEN + ["boundary.json"]) for f in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet")))])
    d = {}
    for k in SPALTEN:
        a = t.column(k).to_pylist()
        d[k.split(".")[-1]] = np.array(a) if k == "plasma_config_id" else np.array([np.nan if v is None else v for v in a], float)
    d["boundary_json"] = t.column("boundary.json").to_pylist()
    return d


def verletzungen(d):
    """Normierte Verletzungen wie problems.py (Aufgabe 2 und 3), vektorisiert ueber den Datensatz."""
    io = np.abs(d["edge_rotational_transform_over_n_field_periods"]); lq = np.log10(d["qi"])
    v3 = np.stack([(0.25 - io) / 0.25, (lq + 3.5) / 3.5, (d["edge_magnetic_mirror_ratio"] - 0.25) / 0.25,
                   (d["flux_compression_in_regions_of_bad_curvature"] - 0.9) / 0.9, (0.0 - d["vacuum_well"]) / 0.1], 1)
    v2 = np.stack([(d["aspect_ratio"] - 10) / 10, (0.25 - io) / 0.25, (lq + 4) / 4, (d["edge_magnetic_mirror_ratio"] - 0.2) / 0.2,
                   (d["max_elongation"] - 5) / 5], 1)
    return v3, v2


def filtern():
    from stellarator.qi_koeffizienten import laden
    d = tabelle(); n = len(d["qi"]); v3, v2 = verletzungen(d); TOL = 0.01
    s = d["edge_rotational_transform_over_n_field_periods"]
    with np.errstate(invalid="ignore"):
        # Regel des Nutzers (paarvergleich_plasma.md): iota mit Vorzeichen, ohne Toleranz, Elongation und Vakuummulde gemischt
        nutzer = (s >= 0.25) & (d["edge_magnetic_mirror_ratio"] <= 0.25) & (d["vacuum_well"] >= 0) & \
                 (d["flux_compression_in_regions_of_bad_curvature"] <= 0.9) & (d["max_elongation"] <= 5)
        betrag = (np.abs(s) >= 0.25) & (d["edge_magnetic_mirror_ratio"] <= 0.25) & (d["vacuum_well"] >= 0) & \
                 (d["flux_compression_in_regions_of_bad_curvature"] <= 0.9) & (d["max_elongation"] <= 5)
        p3_ohne = (v3[:, [0, 2, 3, 4]] <= TOL).all(1); p3_alle = (v3 <= TOL).all(1)
        p2_ohne = (v2[:, [0, 1, 3, 4]] <= TOL).all(1); p2_alle = (v2 <= TOL).all(1)
    namen3 = ["iota_rand/nfp>=0,25", "log10QI<=-3,5", "spiegel_rand<=0,25", "flusskompression<=0,9", "vakuummulde>=0"]
    namen2 = ["A<=10", "iota_rand/nfp>=0,25", "log10QI<=-4", "spiegel_rand<=0,2", "elongation<=5"]

    def zeile(i):
        return {"id": str(d["plasma_config_id"][i]), "nfp": int(d["n_field_periods"][i]), "qi": float(d["qi"][i]),
                "A": float(d["aspect_ratio"][i]), "iota_rand_nfp": float(s[i]), "spiegel_rand": float(d["edge_magnetic_mirror_ratio"][i]),
                "flusskompression": float(d["flux_compression_in_regions_of_bad_curvature"][i]), "vakuummulde": float(d["vacuum_well"][i]),
                "elongation": float(d["max_elongation"][i]), "L_grad": float(d["minimum_normalized_magnetic_gradient_scale_length"][i]),
                "verletzung_P3": dict(zip(namen3, np.round(v3[i], 4).tolist())), "verletzung_P2": dict(zip(namen2, np.round(v2[i], 4).tolist())),
                "P3_max_verletzung": float(np.max(np.maximum(v3[i], 0)))}

    def liste(m):
        idx = np.where(m)[0]; return [zeile(i) for i in idx[np.argsort(d["qi"][idx])]]

    def knapp(m, v, nm, spalten):
        """Kleinster Abstand zur Grenze (Rest = -Verletzung) je Bedingung ueber die Menge: Median und Minimum."""
        r = -v[m][:, spalten]
        return {nm[j]: {"min_rest": float(np.min(r[:, k])), "median_rest": float(np.median(r[:, k]))} for k, j in enumerate(spalten)}

    def qi_stat(m):
        q = d["qi"][m]; return {"anzahl": int(m.sum()), "qi_min": float(np.min(q)), "qi_median": float(np.median(q))}
    aus = {
        "hinweis": "Schwellen aus constellaration/problems.py; zulaessig = jede normierte Verletzung <= 0,01. Keine Aufgabe hat QI <= 0,001.",
        "zeilen": n, "qi_endlich": int(np.isfinite(d["qi"]).sum()),
        "zaehlung": {"nutzer_regel_ohne_QI": int(nutzer.sum()), "nutzer_regel_mit_QI<=1e-3": int((nutzer & (d["qi"] <= 1e-3)).sum()),
                     "nutzer_regel_mit_betrag_iota": int(betrag.sum()),
                     "P3_ohne_QI": int(p3_ohne.sum()), "P3_alle": int(p3_alle.sum()), "P2_ohne_QI": int(p2_ohne.sum()), "P2_alle": int(p2_alle.sum())},
        "qi_statistik": {"nutzer_138": qi_stat(nutzer), "P3_ohne_QI": qi_stat(p3_ohne), "P2_ohne_QI": qi_stat(p2_ohne)},
        "knappheit_nutzer_138": knapp(nutzer, v3, namen3, [0, 2, 3, 4]) | {"elongation<=5": {"min_rest": float(np.min(-v2[nutzer][:, 4])), "median_rest": float(np.median(-v2[nutzer][:, 4]))}},
        "knappheit_P3_ohne_QI": knapp(p3_ohne, v3, namen3, [0, 2, 3, 4]),
        "nutzer_138": liste(nutzer), "P3_ohne_QI": liste(p3_ohne),
    }
    FILTER.write_text(json.dumps(aus, indent=1))
    # Startformen: die 5 mit kleinstem QI unter den amtlich (P3) ohne QI zulaessigen Formen
    X, _ = laden(); MK = laden.MK; ok = np.isfinite(X).all(1); sd = X[ok].std(0)
    import joblib
    top = joblib.load(O / "surrogat.joblib")["top"]
    K = MK[1]; nn = MK[0] * K
    gesperrt = set([1 + i for i in range(K // 2 + 1)] + [1 + nn + i for i in range(K // 2 + 1)] + [0])
    frei = [int(j) for j in top if j not in gesperrt]
    S.mkdir(parents=True, exist_ok=True)
    # Startformen nach der Zielfunktion der Suche (f, amtliche Normierung) ueber den ganzen Datensatz, nicht nach QI unter den 138:
    # Platz 2 bis 5 der 138 haben QI 0,0066 bis 0,0082 (f ~ 0,14), neun andere Datenformen liegen naeher an der Zulaessigkeit.
    fd = np.sum(np.maximum(v3, 0) ** 2, 1); fd[~np.isfinite(v3).all(1)] = np.inf
    idx = np.argsort(fd)[:N_START]
    aus["startformen"] = [zeile(i) | {"f": float(fd[i])} for i in idx]
    aus["startformen_regel"] = "kleinste f = Summe (positive normierte Verletzung Aufgabe 3)^2 ueber alle Datenformen"
    FILTER.write_text(json.dumps(aus, indent=1))
    for k, i in enumerate(idx):
        b = json.loads(d["boundary_json"][i])
        assert np.asarray(b["r_cos"]).shape == MK and np.asarray(b["z_sin"]).shape == MK, "Randform nicht in voller Groesse"
        st = {"k": k, "id": str(d["plasma_config_id"][i]), "datensatz": zeile(i), "rand": b, "sd": sd.tolist(), "frei": frei, "MK": list(MK)}
        (S / f"start{k}.json").write_text(json.dumps(st, indent=1))
    print(json.dumps({k: aus[k] for k in ("zaehlung", "qi_statistik", "knappheit_nutzer_138", "knappheit_P3_ohne_QI")}, indent=1))
    print("Startformen:", [str(d["plasma_config_id"][i]) + f" {d['qi'][i]:.5f}" for i in idx])


def eins(ein, aus):
    """Kindprozess: VMEC++ hohe Genauigkeit (mit QI, wie die Wertung), offizielle Verletzungen, Ergebnis-JSON."""
    from constellaration import forward_model, problems
    from constellaration.geometry import surface_rz_fourier as srf
    from stellarator.qi_gegenrechnung import wertung
    t0 = time.time(); r = {"konvergiert": False}
    try:
        b = srf.SurfaceRZFourier.model_validate(json.loads(Path(ein).read_text()))
        m, _ = forward_model.forward_model(b, settings=forward_model.ConstellarationSettings.default_high_fidelity())
        r["metriken"] = {a: (float(v) if isinstance(v, (int, float)) else None) for a, v in m.model_dump().items()}
        r["konvergiert"] = True
        p3 = problems.MHDStableQIStellarator(); v = p3._normalized_constraint_violations(m)
        r["verletzung_P3"] = [float(x) for x in v]; r["P3_zulaessig"] = bool(p3.is_feasible(m))
        r["P3_wert_allein"] = float(p3._score([m])); r["f"] = float(np.sum(np.maximum(v, 0) ** 2))
        r["wertung"] = wertung(r["metriken"])
    except Exception as e:
        r["fehler"] = f"{type(e).__name__}: {str(e)[:300]}"
    r["sekunden"] = time.time() - t0
    Path(aus).write_text(json.dumps(r, indent=1))


def rand_aus(x, st):
    M, K = st["MK"]; n = M * K; b = dict(st["rand"])
    b["r_cos"] = np.asarray(x[1:1 + n]).reshape(M, K).tolist(); b["z_sin"] = np.asarray(x[1 + n:]).reshape(M, K).tolist()
    return b


def suche(k):
    st = json.loads((S / f"start{k}.json").read_text()); D = S / f"s{k}"; D.mkdir(exist_ok=True)
    M, K = st["MK"]; sd = np.array(st["sd"]); frei = np.array(st["frei"])
    x0 = np.concatenate([[st["rand"]["n_field_periods"]], np.ravel(st["rand"]["r_cos"]), np.ravel(st["rand"]["z_sin"])])
    rng = np.random.default_rng(100 + k); zaehler = [0]; log = D / "zwischenstand.txt"

    def notiz(t):
        with open(log, "a") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {t}\n")

    class Ende(Exception):
        pass

    def bewerte(x, art, sigma):
        i = zaehler[0]
        if i >= BUDGET:
            raise Ende()
        zaehler[0] += 1; f = D / f"{i:03d}.json"
        if f.exists():                                       # --weiter: Fertiges ueberspringen (Folge ist deterministisch)
            r = json.loads(f.read_text())
            if np.allclose(r["vektor"], x, rtol=0, atol=1e-14):
                return r
            notiz(f"{i:03d} vorhanden, aber anderer Vektor -> neu")
        ein = D / f"{i:03d}_rand.json"; ein.write_text(json.dumps(rand_aus(x, st)))
        tmp = D / f"{i:03d}.tmp"; c0 = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
        p = subprocess.run([sys.executable, "-m", "stellarator.qi_filter_suche", "eins", str(ein), str(tmp)], cwd=ROOT,
                           preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (CPU_GRENZE, CPU_GRENZE)),
                           stdout=open(D / f"{i:03d}.log", "w"), stderr=subprocess.STDOUT)
        r = json.loads(tmp.read_text()) if tmp.exists() else {"konvergiert": False, "fehler": f"Kindprozess ohne Ergebnis, Rueckgabe {p.returncode}"}
        r.update({"nr": i, "art": art, "sigma": sigma, "vektor": x.tolist(), "cpu_s": resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime - c0,
                  "uhrzeit": time.strftime("%Y-%m-%d %H:%M:%S"), "start_id": st["id"], "schritt_von_start_sd": float(np.linalg.norm((x - x0)[frei] / sd[frei]))})
        if not r.get("konvergiert"):
            r["f"] = None
        f.write_text(json.dumps(r, indent=1))
        if tmp.exists():
            tmp.unlink()                                     # nur die eigene Zwischendatei (Inhalt steht in NNN.json)
        mt = r.get("metriken") or {}
        notiz(f"{i:03d} {art:8s} sigma {sigma:.3f} f {r['f'] if r['f'] is None else format(r['f'], '.5f')} QI {mt.get('qi')} "
              f"P3 zulaessig {r.get('P3_zulaessig')} {r['sekunden']:.0f} s")
        return r

    def wert(r):
        return np.inf if r.get("f") is None else r["f"]
    notiz(f"Start {st['id']} QI_datensatz {st['datensatz']['qi']:.6f}")
    try:
        r = bewerte(x0, "start", 0.0); xb, fb, sig = x0.copy(), wert(r), SIG0
        if r.get("P3_zulaessig"):
            raise Ende()
        while True:
            d = np.zeros_like(x0); u = rng.normal(size=len(frei)); u /= np.linalg.norm(u); d[frei] = u * sd[frei]
            erfolg = False
            for vz in (1, -1):                                # gespiegelte Richtung
                xt = xb + vz * sig * d; r = bewerte(xt, "zufall" if vz > 0 else "spiegel", sig)
                if wert(r) < fb:
                    xb, fb, erfolg = xt, wert(r), True
                    if r.get("P3_zulaessig"):
                        raise Ende()
                    sig = min(1.5 * sig, SIG_MAX)
                    while True:                               # Mustervorstoss in dieselbe Richtung
                        xt = xb + vz * sig * d; r = bewerte(xt, "vorstoss", sig)
                        if wert(r) < fb:
                            xb, fb = xt, wert(r); sig = min(1.5 * sig, SIG_MAX)
                            if r.get("P3_zulaessig"):
                                raise Ende()
                        else:
                            break
                    break
            if not erfolg:
                sig = max(0.6 * sig, SIG_MIN)
    except Ende:
        pass
    notiz(f"ENDE nach {zaehler[0]} Auswertungen, bestes f {fb:.5f}")


def auswertung():
    z = ["| Start | Nr | Art | sigma | Abstand Start (sd) | QI | A | iota/nfp | Spiegel | Flussk. | Vak.-mulde | Elong. | L_grad | f (P3) | max. Verl. P3 | P3 zul. | P2 zul. | s |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in range(N_START):
        for f in sorted((S / f"s{k}").glob("[0-9][0-9][0-9].json")):
            r = json.loads(f.read_text()); m = r.get("metriken") or {}
            g = lambda a, p=".4f": "–" if m.get(a) is None else format(m[a], p)
            v = r.get("verletzung_P3"); w = r.get("wertung", {})
            z.append(f"| {k} | {r['nr']} | {r['art']} | {r['sigma']:.3f} | {r['schritt_von_start_sd']:.2f} | {g('qi', '.6f')} | {g('aspect_ratio', '.2f')} | "
                     f"{g('edge_rotational_transform_over_n_field_periods', '.3f')} | {g('edge_magnetic_mirror_ratio', '.3f')} | "
                     f"{g('flux_compression_in_regions_of_bad_curvature', '.3f')} | {g('vacuum_well', '.4f')} | {g('max_elongation', '.2f')} | "
                     f"{g('minimum_normalized_magnetic_gradient_scale_length', '.3f')} | {'–' if r.get('f') is None else format(r['f'], '.5f')} | "
                     f"{'–' if v is None else format(max(max(v), 0), '.3f')} | {'ja' if r.get('P3_zulaessig') else 'nein'} | "
                     f"{'ja' if w.get('P2_einfach_QI', {}).get('zulaessig') else 'nein'} | {r['sekunden']:.0f} |")
    (ROOT / "docs/recherche/qi_tragwerk/opus_filter_suche_tabelle.md").write_text("\n".join(z) + "\n"); print("\n".join(z))


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "filter":
        filtern()
    elif a == "suche":
        suche(int(sys.argv[2]))
    elif a == "eins":
        eins(sys.argv[2], sys.argv[3])
    elif a == "auswertung":
        auswertung()
