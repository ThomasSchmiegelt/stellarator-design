"""Experimentmatrix: vernuenftige und wilde Parameterproben fuer Verstaendnis und Daten (Nutzerwunsch 2026-11-05, F-252).

Nutzer (woertlich): 'vielleicht kannst du das so machen, dass es vernunftbasierte Parameter in der Matrix gibt und auch einige
wilde oder zufaellige, einfach um Verstaendnis und Daten zu generieren.' Zweck: Daten und Verstaendnis, nicht das Optimum.

Befehle (aus dem Projektordner; Python = .venv-constellaration/bin/python; Rechnungen im Scope 'hermes python ...'):
  python -m stellarator.qi_experiment vorbereiten      # einmal: sd, freie Koeffizienten, Datensatz-Richtungen, Kreuzungspartner,
                                                       #   Datensatz-Stichprobe -> <aus>/vorbereitung.json, <aus>/datensatz/liste.json
  python -m stellarator.qi_experiment form <name>      # eine Formprobe (VMEC++ hohe Genauigkeit im Kindprozess) -> <aus>/form/<name>.json
  python -m stellarator.qi_experiment strom <name>     # eine Strom-Probe (Weg ii, DjLe3eL6 + Proxima-Spulen)  -> <aus>/strom/<name>.json
  python -m stellarator.qi_experiment datensatz <nr>   # Datensatzform Nr. nr (0..59) der Zufallsstichprobe, QI-Profil wie
                                                       #   qi_profil_serie.eins                              -> <aus>/datensatz/ds_<nr>_s<seed>.json
  python -m stellarator.qi_experiment liste [form|strom|datensatz]   # alle Probennamen (fuer erzeuge_matrix.py)
  python -m stellarator.qi_experiment auswertung       # Tabellen, Bilder, Bericht docs/recherche/qi_tragwerk/qi_experiment.md,
                                                       #   CSV aller Proben <aus>/alle_proben.csv
Ausgabeordner <aus> = sim/qi_flaeche/experiment, fuer Tests ueber Umgebungsvariable EXP_AUS (und EXP_BERICHT fuer den Bericht).
Eigenschaften: jede Probe eine kleine JSON; vorhandene Ergebnisse werden uebersprungen (Neustart setzt fort); keine Wanduhr-Grenze,
nur Prozess-CPU-Zeit (RLIMIT_CPU) je Einzelrechnung; Seeds deterministisch, der Seed steht im Probennamen; Fehlertexte von VMEC++
(nicht konvergiert, 'poorly shaped' usw.) werden als Datum gespeichert.

Modi:
  Formproben (Basisformen do3 = Do3Qy, k3 = Kandidat 3 halber Schritt, dje = DjLe3eL6, d8z = D8ZNt2):
    vernunft: Basis; je einer der 9 wichtigsten Koeffizienten (Surrogat-Rangliste B-050) +-0,2 sd; Aspektverhaeltnis ueber alle
              m=0-Koeffizienten (R00 + Achswellung nachgefuehrt, Querschnitt fest); Richtungen aus einer lokalen linearen Regression
              im Datensatz (4000 naechste Formen gleicher Periodenzahl): Elongation senken, Dreieckigkeit +-, Spiegelverhaeltnis
              senken (0,1/0,3 sd; und 0,2 sd senkrecht zur QI-Richtung), iota anheben; Linearitaet: wichtigster Koeffizient +-0,1/0,3 sd.
    wild:     Gauss-Rauschen 0,5/1/2 sd auf alle 80 freien Koeffizienten, Vorzeichenwechsel eines Koeffizienten, Kreuzung mit einer
              zufaelligen Datenform gleicher Periodenzahl (gleichverteilt je Koeffizient bzw. Mittel), log-gleichverteilte Rauschstaerke.
  Strom-Proben (Faktoren der Gruppen S1..S5): vernunft = +-5 % (gepruefter Bereich von Weg ii) als Latin Hypercube + Richtungen aus
    B-053/B-054; wild = +-20 %, +-50 %, Vorzeichenwechsel einer Gruppe: AUSSERHALB des geprueften Bereichs (nur Daten fuer spaeter).
  Datensatz-Stichprobe: 60 zufaellige Datensatzformen (Seed fest), Rechnung = qi_profil_serie.eins (Profil QI je Flaeche).
Schwellen: constellaration/problems.py (_normalized_constraint_violations, is_feasible), keine eigenen.
"""
import csv
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = Path(os.environ.get("EXP_AUS", ROOT / "sim" / "qi_flaeche" / "experiment"))
BER = Path(os.environ.get("EXP_BERICHT", ROOT / "docs" / "recherche" / "qi_tragwerk"))
sys.path.insert(0, str(ROOT))
SEED0 = 20261105
CPU_GRENZE = 3600                    # s Prozess-CPU-Zeit je VMEC++-Rechnung (Pause zaehlt nicht mit)
CPU_GRENZE_DS = 5400                 # Datensatzprobe: VMEC++ + Boozer + 7 Flaechen
BASEN = ["do3", "k3", "dje", "d8z"]
NAMEN = {"do3": "Do3Qy", "k3": "Kandidat 3 halb", "dje": "DjLe3eL6", "d8z": "D8ZNt2"}
N_DS = 400
K_NACHBARN = 4000
ZIELE = {"spiegel": "edge_magnetic_mirror_ratio", "elongation": "max_elongation", "dreieck": "average_triangularity",
         "iota": "edge_rotational_transform_over_n_field_periods", "log10qi": "qi"}
GRUND_ZIEL = {
    "spiegel": "Spiegelverhaeltnis am Rand ist neben QI die knappste Bedingung (B-051: Aufgabe 3 <= 0,25, Aufgabe 2 <= 0,2; "
               "die Strom-Optimierung B-053/B-054 hob es an)",
    "elongation": "Elongation ist in Aufgabe 2 auf 5 begrenzt; Do3Qy/K3 liegen darueber (B-050)",
    "dreieck": "Dreieckigkeit ist eine klassische Querschnittsgroesse; Wirkung auf QI unbekannt, daher beide Vorzeichen",
    "iota": "Rotationstransformation am Rand je Periode ist die knappste Bedingung der 138 Filterformen (B-051, >= 0,25)",
}


# ---------------------------------------------------------------- Plaene (rein deterministisch, ohne Daten)
def formplan():
    """Liste aller Formproben: dict(name, basis, modus, art, param, prio, seed). prio 1 = vernunft (Stufe frueh), 2 = wild,
    3 = Linearitaet (zuletzt)."""
    P = []
    for fi, b in enumerate(BASEN):
        v = [("vernunft", "basis", {}, 1)]
        for j in range(9):
            for s in (0.2, -0.2, 0.1, -0.1, 0.3, -0.3):
                v.append(("vernunft", "koef", {"j": j, "schritt": s}, 1))
        v += [("vernunft", "aspekt", {"f": 0.95}, 1), ("vernunft", "aspekt", {"f": 1.05}, 1)]
        v += [("vernunft", "richtung", {"ziel": "elongation", "vz": -1, "schritt": 0.2}, 1),
              ("vernunft", "richtung", {"ziel": "dreieck", "vz": 1, "schritt": 0.2}, 1),
              ("vernunft", "richtung", {"ziel": "dreieck", "vz": -1, "schritt": 0.2}, 1),
              ("vernunft", "richtung", {"ziel": "spiegel", "vz": -1, "schritt": 0.1}, 1),
              ("vernunft", "richtung", {"ziel": "spiegel", "vz": -1, "schritt": 0.3}, 1),
              ("vernunft", "richtung_orth", {"ziel": "spiegel", "vz": -1, "schritt": 0.2}, 1),
              ("vernunft", "richtung", {"ziel": "iota", "vz": 1, "schritt": 0.2}, 1)]
        w = [("wild", "gauss", {"sigma": 0.5}, 2)] * 6 + [("wild", "gauss", {"sigma": 1.0}, 2)] * 8 + \
            [("wild", "gauss", {"sigma": 2.0}, 2)] * 5 + [("wild", "vorzeichen", {}, 2)] * 5 + \
            [("wild", "kreuz", {"partner": k}, 2) for k in range(3)] + \
            [("wild", "misch", {"partner": 0, "t": tt}, 2) for tt in (0.25, 0.5, 0.75)] + \
            [("wild", "logskala", {}, 2)] * 10
        lin = [("vernunft", "koef", {"j": 0, "schritt": s}, 3) for s in (0.1, -0.1, 0.3, -0.3)]
        for nr, (modus, art, par, prio) in enumerate(v + w + lin):
            seed = SEED0 + 100 * fi + nr
            P.append({"name": f"{b}_{modus}_{nr:02d}_{art}_s{seed}", "basis": b, "modus": modus, "art": art, "param": par,
                      "prio": prio, "seed": seed})
    return P


B053_GRAD = np.array([-2.4, -1.4, -2.7, -3.0, 8.8])   # % QI je 1 % Strom (B-053, Rand)


def stromplan():
    P = []

    def dazu(modus, art, f, grund, seed):
        f = [float(x) for x in f]
        P.append({"name": f"strom_{modus}_{len(P):03d}_{art}_s{seed}", "modus": modus, "art": art, "faktoren": f, "grund": grund,
                  "seed": seed, "ausserhalb_geprueft": bool(max(abs(x - 1) for x in f) > 0.05 + 1e-9)})
    g = B053_GRAD / np.abs(B053_GRAD).max()
    fest = [("basis", [1] * 5, "Bezug (kalibrierte Stroeme)"),
            ("alle1.05", [1.05] * 5, "Pruefstein: alle gemeinsam aendert QI nicht (B-053)"),
            ("b053opt", [1.0, 1.05, 1.0148824699091454, 0.9803192211630806, 0.95], "Optimum B-053 (L-BFGS-B, +-5 %)"),
            ("b054flecken", [1.0, 1.05, 1.05, 1.05, 0.95], "Trimmung schlechteste 5 % (B-054)"),
            ("s5_0.95", [1, 1, 1, 1, 0.95], "staerkster Hebel S5 -5 % (B-053)"),
            ("grad_ab_voll", 1 - 0.05 * g, "gegen die lineare QI-Ableitung je Gruppe (B-053), groesster Schritt 5 %"),
            ("grad_ab_halb", 1 - 0.025 * g, "gegen die Ableitung, halber Schritt (Linearitaet)"),
            ("grad_auf_voll", 1 + 0.05 * g, "mit der Ableitung (Verschlechterung, Linearitaet)")]
    for k, (art, f, gr) in enumerate(fest):
        dazu("vernunft", art, f, gr, SEED0 + 4000 + k)
    n_lhs = 150 - len(fest); rng = np.random.default_rng(SEED0 + 4100)
    L = np.stack([(rng.permutation(n_lhs) + rng.uniform(size=n_lhs)) / n_lhs for _ in range(5)], 1)
    for i in range(n_lhs):
        dazu("vernunft", "lhs", 0.95 + 0.10 * L[i], "Latin Hypercube im geprueften Bereich +-5 %", SEED0 + 4100)
    for art, n in (("u20", 250), ("u50", 250), ("vz", 200)):
        for _ in range(n):
            seed = SEED0 + 5000 + len(P); r = np.random.default_rng(seed)
            if art == "u20":
                f = 1 + r.uniform(-0.2, 0.2, 5); gr = "Zufall +-20 % (ausserhalb geprueft)"
            elif art == "u50":
                f = 1 + r.uniform(-0.5, 0.5, 5); gr = "Zufall +-50 % (ausserhalb geprueft)"
            else:
                f = 1 + r.uniform(-0.2, 0.2, 5); gk = int(r.integers(5)); f[gk] = -f[gk]
                gr = f"Vorzeichenwechsel Gruppe S{gk + 1}, sonst +-20 % (ausserhalb geprueft)"
            dazu("wild", art, f, gr, seed)
    return P


def ds_name(nr):
    return f"ds_{nr:02d}_s{SEED0 + 9000}"


# ---------------------------------------------------------------- Vorbereitung (einmal, liest den Datensatz)
def _pad(a, MK):
    a = np.asarray(a, float); o = np.zeros(MK); k0 = (MK[1] - a.shape[1]) // 2; o[:a.shape[0], k0:k0 + a.shape[1]] = a
    return o


def vektor(b, MK):
    return np.concatenate([[b["n_field_periods"]], _pad(b["r_cos"], MK).ravel(), _pad(b["z_sin"], MK).ravel()])


def rand_aus(x, b, MK):
    M, K = MK; n = M * K; o = {k: v for k, v in b.items() if k not in ("r_cos", "z_sin")}
    o["r_cos"] = np.asarray(x[1:1 + n]).reshape(M, K).tolist(); o["z_sin"] = np.asarray(x[1 + n:1 + 2 * n]).reshape(M, K).tolist()
    return o


def koef_name(j, MK):
    M, K = MK; n = M * K; i = j - 1; art = "r_cos" if i < n else "z_sin"; i %= n
    return f"{art}[{i // K},{i % K - K // 2}]"


def vorbereiten():
    import glob
    import pyarrow.parquet as pq
    from stellarator.qi_karte import FORMEN, rand
    from stellarator.qi_koeffizienten import laden
    from stellarator.qi_filter_suche import SPALTEN
    ziel = EXP / "vorbereitung.json"
    if ziel.exists():
        print("vorbereitung.json vorhanden, uebersprungen"); return
    os.chdir(ROOT); t0 = time.time()
    X, qi = laden(); MK = laden.MK
    dateien = sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet")))
    T = {}
    for k in SPALTEN:
        a = []
        for fn in dateien:
            a += pq.read_table(fn, columns=[k]).column(0).to_pylist()
        T[k.split(".")[-1]] = np.array(a) if k == "plasma_config_id" else np.array([np.nan if v is None else v for v in a], float)
    assert len(T["qi"]) == len(X) and np.allclose(np.nan_to_num(T["n_field_periods"]), np.nan_to_num(X[:, 0])), "Zeilenfolge passt nicht"
    ok = np.isfinite(X).all(1); sd = X[ok].std(0)
    K = MK[1]; nn = MK[0] * K
    gesperrt = set([1 + i for i in range(K // 2 + 1)] + [1 + nn + i for i in range(K // 2 + 1)] + [0])
    frei80 = [j for j in range(1, 1 + 2 * nn) if j not in gesperrt and sd[j] > 0]
    st0 = ROOT / "sim/qi_flaeche/suche_lokal/start0.json"
    if st0.exists():
        frei9 = json.loads(st0.read_text())["frei"]
    else:
        import joblib
        top = joblib.load(ROOT / "sim/qi_flaeche/surrogat.joblib")["top"]; frei9 = [int(j) for j in top if j not in gesperrt][:9]
    y = {"spiegel": T["edge_magnetic_mirror_ratio"], "elongation": T["max_elongation"], "dreieck": T["average_triangularity"],
         "iota": np.abs(T["edge_rotational_transform_over_n_field_periods"]), "log10qi": np.log10(np.where(T["qi"] > 0, T["qi"], np.nan))}
    F = np.array(frei80); V = {"MK": list(MK), "sd": sd.tolist(), "frei80": frei80, "frei9": frei9,
                               "frei9_namen": [koef_name(j, MK) for j in frei9], "gesperrt": sorted(gesperrt), "basis": {},
                               "hinweis": "Richtungen: lokale Ridge-Regression in sd-Einheiten ueber die naechsten Datenformen gleicher Periodenzahl; "
                                          "Einheitsvektor ueber die 80 freien Koeffizienten, positives Vorzeichen = Zielgroesse steigt."}
    for fi, b in enumerate(BASEN):
        bd, _ = rand(b); x0 = vektor(bd, MK); nfp = int(bd["n_field_periods"])
        gl = np.where(ok & (X[:, 0] == nfp))[0]
        Z = (X[gl][:, F] - x0[F]) / sd[F]; dist = np.linalg.norm(Z, axis=1); nb = gl[np.argsort(dist)[:K_NACHBARN]]
        Zn = (X[nb][:, F] - x0[F]) / sd[F]; R = {}
        for zn, yy in y.items():
            m = np.isfinite(yy[nb]); A = Zn[m]; t = yy[nb][m]
            Ac = A - A.mean(0); tc = t - t.mean(); lam = 0.01 * np.trace(Ac.T @ Ac) / A.shape[1]
            g = np.linalg.solve(Ac.T @ Ac + lam * np.eye(A.shape[1]), Ac.T @ tc)
            r2 = 1 - np.sum((tc - Ac @ g) ** 2) / np.sum(tc ** 2)
            R[zn] = {"gradient_je_sd": g.tolist(), "norm": float(np.linalg.norm(g)), "einheit": (g / np.linalg.norm(g)).tolist(),
                     "r2_lokal": float(r2), "n": int(m.sum())}
        gs, gq = np.array(R["spiegel"]["gradient_je_sd"]), np.array(R["log10qi"]["gradient_je_sd"])
        o = gs - (gs @ gq) / (gq @ gq) * gq
        R["spiegel_orth_qi"] = {"einheit": (o / np.linalg.norm(o)).tolist(), "norm": float(np.linalg.norm(o)),
                                "hinweis": "Spiegel-Gradient ohne den Anteil entlang des lokalen log10-QI-Gradienten"}
        rng = np.random.default_rng(SEED0 + 700 + fi)
        kand = np.where(ok & (X[:, 0] == nfp) & np.isfinite(T["qi"]) & (T["plasma_config_id"] != FORMEN[b][2]))[0]
        pk = rng.choice(kand, 3, replace=False)
        partner = [{"id": str(T["plasma_config_id"][i]), "qi_daten": float(T["qi"][i]), "x": X[i].tolist()} for i in pk]
        V["basis"][b] = {"x0": x0.tolist(), "nfp": nfp, "nachbarn": K_NACHBARN, "mittlerer_abstand_nachbarn_sd": float(np.median(np.sort(dist)[:K_NACHBARN])),
                         "richtungen": R, "partner": partner}
        print(b, {k: round(v.get("r2_lokal", 0), 3) for k, v in R.items()}, flush=True)
    rng = np.random.default_rng(SEED0 + 9000); idx = rng.choice(len(X), N_DS, replace=False)
    ids = [str(T["plasma_config_id"][i]) for i in idx]; rest = set(ids); formen = {}
    for fn in dateien:
        t = pq.read_table(fn, columns=["plasma_config_id", "boundary.json", "metrics.qi"], filters=[("plasma_config_id", "in", list(rest))]).to_pydict()
        for i, bj, q in zip(t["plasma_config_id"], t["boundary.json"], t["metrics.qi"]):
            formen[i] = {"boundary": json.loads(bj), "qi_daten": q}
    V["stichprobe"] = [{"nr": k, "id": i, "name": ds_name(k), "qi_daten": formen.get(i, {}).get("qi_daten")} for k, i in enumerate(ids)]
    (EXP / "datensatz").mkdir(parents=True, exist_ok=True)
    (EXP / "datensatz" / "liste.json").write_text(json.dumps({"ids": ids, "formen": formen}))
    V["sekunden"] = time.time() - t0
    EXP.mkdir(parents=True, exist_ok=True); ziel.write_text(json.dumps(V)); print("vorbereitung fertig", f"{time.time() - t0:.0f} s")


# ---------------------------------------------------------------- Bewertung nach problems.py
def verletzungen(mt):
    from constellaration import forward_model, problems
    out = {}
    try:
        m = forward_model.ConstellarationMetrics(**{k: mt.get(k) for k in forward_model.ConstellarationMetrics.model_fields})
    except Exception as e:
        return {"verletzung_fehler": f"{type(e).__name__}: {str(e)[:120]}"}
    for k, P in (("P3", problems.MHDStableQIStellarator), ("P2", problems.SimpleToBuildQIStellarator)):
        p = P()
        try:
            v = p._normalized_constraint_violations(m)
            out[f"verletzung_{k}"] = [float(x) for x in v]; out[f"{k}_zulaessig"] = bool(p.is_feasible(m))
            out[f"f_{k}"] = float(np.sum(np.maximum(v, 0) ** 2)); out[f"max_verletzung_{k}"] = float(np.max(v))
        except Exception as e:
            out[f"verletzung_{k}"] = None; out[f"{k}_zulaessig"] = False; out[f"{k}_fehler"] = f"{type(e).__name__}: {str(e)[:120]}"
    return out


def _kind(args, log, cpu):
    c0 = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
    with open(log, "w") as fh:
        p = subprocess.run([sys.executable, "-m", *args], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                           preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu)))
    return p.returncode, resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime - c0


def _log_ende(log, n=1500):
    try:
        return Path(log).read_text(errors="replace")[-n:]
    except Exception:
        return None


# ---------------------------------------------------------------- Formprobe
def form_vektor(spec, V, bd):
    MK = tuple(V["MK"]); sd = np.array(V["sd"]); F = np.array(V["frei80"]); B = V["basis"][spec["basis"]]
    x0 = np.array(B["x0"]); x = x0.copy(); a, p = spec["art"], spec["param"]; rng = np.random.default_rng(spec["seed"]); info = {}
    if a == "basis":
        grund = "Unveraenderte Basisform: Bezugswert und Pruefstein (bekannter QI muss herauskommen)."
    elif a == "koef":
        j = V["frei9"][p["j"]]; x[j] += p["schritt"] * sd[j]; info["koeffizient"] = koef_name(j, MK)
        grund = (f"Einer der 9 wichtigsten Koeffizienten (Surrogat-Rangliste B-050, Platz {p['j'] + 1}: {koef_name(j, MK)}) um "
                 f"{p['schritt']:+.1f} sd: Empfindlichkeit von QI je Standardabweichung (zentrale Differenz bzw. Linearitaet).")
    elif a == "aspekt":
        M, K = MK; n = M * K
        x[1:1 + K] *= p["f"]; x[1 + n:1 + n + K] *= p["f"]
        grund = (f"Aspektverhaeltnis ueber R00 mit nachgefuehrter Achse: alle m=0-Koeffizienten (R00 und Achswellung) x {p['f']}, "
                 "Querschnitt fest. B-055 hatte nur R00 veraendert (Achswellung dann relativ verzerrt); offen war die Skalierung "
                 "mit nachgefuehrter Achsenwellung.")
    elif a in ("richtung", "richtung_orth"):
        R = B["richtungen"]; key = p["ziel"] if a == "richtung" else "spiegel_orth_qi"
        d = np.array(R[key]["einheit"]) * p["vz"]; x[F] += p["schritt"] * d * sd[F]
        g = {z: float(np.array(R[z]["gradient_je_sd"]) @ d * p["schritt"]) for z in ZIELE}
        info["erwartung_linear"] = g; info["r2_lokal"] = {z: R[z]["r2_lokal"] for z in ZIELE}
        grund = (f"Richtung aus dem Datensatz (lokale lineare Regression, {B['nachbarn']} naechste Formen gleicher Periodenzahl): "
                 f"{p['ziel']} {'senken' if p['vz'] < 0 else 'anheben'}, {p['schritt']} sd"
                 + (" senkrecht zur lokalen QI-Richtung (QI linear unveraendert)" if a == "richtung_orth" else "")
                 + ". Grund: " + GRUND_ZIEL[p["ziel"]] + ".")
    elif a == "gauss":
        x[F] += p["sigma"] * rng.normal(size=len(F)) * sd[F]
        grund = f"Zufall (Daten/Verstaendnis): Gauss-Rauschen {p['sigma']} sd auf alle {len(F)} freien Koeffizienten."
    elif a == "logskala":
        s = float(10 ** rng.uniform(np.log10(0.03), np.log10(3.0))); info["sigma"] = s
        x[F] += s * rng.normal(size=len(F)) * sd[F]
        grund = f"Zufall: Gauss-Rauschen mit log-gleichverteilter Staerke (0,03 bis 3 sd), hier {s:.3f} sd."
    elif a == "vorzeichen":
        kand = [j for j in F if abs(x0[j]) > 1e-3]; j = int(rng.choice(kand)); x[j] = -x[j]; info["koeffizient"] = koef_name(j, MK)
        grund = f"Zufall: Vorzeichen des Koeffizienten {koef_name(j, MK)} umgedreht ({x0[j]:+.4f} -> {x[j]:+.4f})."
    elif a in ("kreuz", "misch"):
        pt = B["partner"][p["partner"]]; xp = np.array(pt["x"]); info["partner"] = pt["id"]; info["partner_qi"] = pt["qi_daten"]
        if a == "kreuz":
            m = rng.uniform(size=len(F)) < 0.5; x[F[m]] = xp[F[m]]
            grund = f"Zufall: Kreuzung mit Datenform {pt['id']} (gleiche Periodenzahl), jeder freie Koeffizient mit Wahrscheinlichkeit 0,5 vom Partner."
        else:
            x[F] = (1 - p["t"]) * x0[F] + p["t"] * xp[F]
            grund = f"Zufall: Mittel ({p['t']}) aus Basis und Datenform {pt['id']} (gleiche Periodenzahl)."
    else:
        raise ValueError(a)
    info["abstand_sd"] = float(np.linalg.norm((x - x0)[F] / sd[F]))
    return x, grund, info


def form(name):
    from stellarator.qi_karte import rand
    spec = {p["name"]: p for p in formplan()}[name]
    aus = EXP / "form" / f"{name}.json"
    if aus.exists():
        print("fertig, uebersprungen:", name); return
    V = json.loads((EXP / "vorbereitung.json").read_text()); MK = tuple(V["MK"])
    bd, _ = rand(spec["basis"]); x, grund, info = form_vektor(spec, V, bd); b = rand_aus(x, bd, MK)
    T = EXP / "tmp"; T.mkdir(parents=True, exist_ok=True); ein, tmp, log = T / f"{name}_rand.json", T / f"{name}.tmp", T / f"{name}.log"
    ein.write_text(json.dumps(b))
    rc, cpu = _kind(["stellarator.qi_filter_suche", "eins", str(ein), str(tmp)], log, CPU_GRENZE)
    r = json.loads(tmp.read_text()) if tmp.exists() else {"konvergiert": False, "fehler": f"Kindprozess ohne Ergebnis, Rueckgabe {rc} (CPU-Grenze {CPU_GRENZE} s?)"}
    r.pop("wertung", None); r.pop("P3_wert_allein", None)
    out = {**{k: spec[k] for k in ("name", "basis", "modus", "art", "param", "seed", "prio")}, "typ": "form", "grund": grund, **info,
           "konvergiert": bool(r.get("konvergiert")), "fehler": r.get("fehler"), "metriken": r.get("metriken"),
           "sekunden": r.get("sekunden"), "cpu_s": cpu, "rueckgabe": rc, "rand": {"r_cos": b["r_cos"], "z_sin": b["z_sin"], "n_field_periods": b["n_field_periods"]},
           "uhrzeit": time.strftime("%Y-%m-%d %H:%M:%S")}
    if out["metriken"]:
        out.update(verletzungen(out["metriken"]))
    if not out["konvergiert"]:
        out["log_ende"] = _log_ende(log)
    (EXP / "form").mkdir(parents=True, exist_ok=True); aus.write_text(json.dumps(out, indent=1))
    for f in (ein, tmp, log):                   # eigene Zwischendateien (Inhalt steht in der Ergebnis-JSON)
        if f.exists():
            f.unlink()
    mt = out["metriken"] or {}
    print(name, "konv", out["konvergiert"], "QI", mt.get("qi"), "P3", out.get("P3_zulaessig"), f"{cpu:.0f} s CPU", out["fehler"] or "", flush=True)


# ---------------------------------------------------------------- Strom-Probe (Weg ii)
def strom(name):
    spec = {p["name"]: p for p in stromplan()}[name]
    aus = EXP / "strom" / f"{name}.json"
    if aus.exists():
        print("fertig, uebersprungen:", name); return
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_GRENZE, CPU_GRENZE))
    from stellarator.qi_spulen import Modell2, spiegel
    t0 = time.time(); c0 = resource.getrusage(resource.RUSAGE_SELF).ru_utime; out = {**spec, "typ": "strom", "basisform": "DjLe3eL6 (Proxima-Spulen)"}
    try:
        M = Modell2(); out["sek_modell"] = time.time() - t0; t1 = time.time()
        q, rest = M.qi(spec["faktoren"])
        out.update({"ok": True, "s": [float(v) for v in M.bz.boozer_normalized_toroidal_flux], "qi_flaechen": q, "qi_rand": q[-1],
                    "spiegel_flaechen": spiegel(M, spec["faktoren"]), "refit_rest": rest, "sek_probe": time.time() - t1,
                    "iota_hinweis": "Weg ii haelt die Flaechen und iota der offiziellen Rechnung fest; iota und Form aendern sich im Modell nicht."})
    except Exception as e:
        out.update({"ok": False, "fehler": f"{type(e).__name__}: {str(e)[:300]}"})
    out["cpu_s"] = resource.getrusage(resource.RUSAGE_SELF).ru_utime - c0; out["sekunden"] = time.time() - t0
    out["uhrzeit"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (EXP / "strom").mkdir(parents=True, exist_ok=True); aus.write_text(json.dumps(out, indent=1))
    print(name, out.get("qi_rand"), out.get("fehler", ""), f"{out['sekunden']:.0f} s", flush=True)


# ---------------------------------------------------------------- Datensatz-Stichprobe
def ds_kind(fid):
    import stellarator.qi_profil_serie as PS
    PS.AUS = EXP / "datensatz"; PS.eins(fid)


def datensatz(nr):
    nr = int(nr); name = ds_name(nr); aus = EXP / "datensatz" / f"{name}.json"
    if aus.exists():
        print("fertig, uebersprungen:", name); return
    V = json.loads((EXP / "vorbereitung.json").read_text()); e = V["stichprobe"][nr]; fid = e["id"]
    T = EXP / "tmp"; T.mkdir(parents=True, exist_ok=True); log = T / f"{name}.log"
    rc, cpu = _kind(["stellarator.qi_experiment", "ds_kind", fid], log, CPU_GRENZE_DS)
    zw = EXP / "datensatz" / f"{fid}.json"
    r = json.loads(zw.read_text()) if zw.exists() else {"ok": False, "fehler": f"Kindprozess ohne Ergebnis, Rueckgabe {rc} (CPU-Grenze {CPU_GRENZE_DS} s?)"}
    out = {"name": name, "typ": "datensatz", "modus": "datensatz", "art": "stichprobe", "nr": nr, "id": fid, "seed": SEED0 + 9000,
           "grund": "Zufallsstichprobe des Datensatzes (Seed fest): wie oft rechnet VMEC++ eine beliebige Datenform, trifft es den Datensatzwert, "
                    "wie sieht das QI-Profil aus (Bezug fuer die wilden Proben).",
           "konvergiert": bool(r.get("ok")) or bool(r.get("metriken")), "fehler": r.get("fehler") if not r.get("ok") else (r.get("fehler") or None),
           "metriken": r.get("metriken"), "qi_datensatz": e.get("qi_daten"), "s": r.get("s"), "qi_flaeche": r.get("qi_flaeche"),
           "sekunden": r.get("sek"), "cpu_s": cpu, "rueckgabe": rc, "uhrzeit": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        bd = json.loads((EXP / "datensatz" / "liste.json").read_text())["formen"][fid]["boundary"]
        out["rand"] = {"r_cos": bd["r_cos"], "z_sin": bd["z_sin"], "n_field_periods": bd["n_field_periods"]}
    except Exception:
        pass
    if out["metriken"]:
        out.update(verletzungen(out["metriken"]))
    if not out["konvergiert"]:
        out["log_ende"] = _log_ende(log)
    aus.write_text(json.dumps(out, indent=1))
    if log.exists():
        log.unlink()
    print(name, fid, out["konvergiert"], (out["metriken"] or {}).get("qi"), flush=True)


# ---------------------------------------------------------------- Auswertung
def _lade(ordner, muster="*.json"):
    d = EXP / ordner
    return [json.loads(p.read_text()) for p in sorted(d.glob(muster))] if d.exists() else []


def _pz(x, n=0):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{100 * x:.{n}f} %"


def _g(x, p=".3g"):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else format(x, p)


def _r2(A, y):
    A1 = np.c_[np.ones(len(A)), A]; c, *_ = np.linalg.lstsq(A1, y, rcond=None); res = y - A1 @ c
    return float(1 - res @ res / np.sum((y - y.mean()) ** 2)), c


def _r2_cv(A, y):
    """Leave-one-out R2 des linearen Modells (Hat-Matrix)."""
    A1 = np.c_[np.ones(len(A)), A]; H = A1 @ np.linalg.pinv(A1); res = y - H @ y; loo = res / np.clip(1 - np.diag(H), 1e-9, None)
    return float(1 - loo @ loo / np.sum((y - y.mean()) ** 2))


def auswertung():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FO, ST, DS = _lade("form"), _lade("strom"), _lade("datensatz", "ds_*.json")
    BILD = BER / "qi_experiment"; BILD.mkdir(parents=True, exist_ok=True)
    plan_f, plan_s = formplan(), stromplan()
    qib = {r["basis"]: r["metriken"]["qi"] for r in FO if r["art"] == "basis" and r["konvergiert"] and r["metriken"].get("qi")}
    for r in FO:
        q = (r.get("metriken") or {}).get("qi") if r["konvergiert"] else None
        r["qi"] = q; r["verh"] = q / qib[r["basis"]] if q and r["basis"] in qib else None
    # ---- CSV
    MK = None
    V = json.loads((EXP / "vorbereitung.json").read_text()) if (EXP / "vorbereitung.json").exists() else None
    if V:
        MK = tuple(V["MK"])
    metr = ["qi", "aspect_ratio", "max_elongation", "edge_rotational_transform_over_n_field_periods", "axis_rotational_transform_over_n_field_periods",
            "edge_magnetic_mirror_ratio", "axis_magnetic_mirror_ratio", "average_triangularity", "vacuum_well",
            "flux_compression_in_regions_of_bad_curvature", "minimum_normalized_magnetic_gradient_scale_length"]
    kopf = ["name", "typ", "basis", "modus", "art", "param", "seed", "ausserhalb_geprueft", "abstand_sd", "rechenbar", "qi_basis", "qi_verh_basis"] + \
           [f"m_{k}" for k in metr] + [f"v3_{i}" for i in range(5)] + [f"v2_{i}" for i in range(5)] + \
           ["f_P3", "P3_zulaessig", "P2_zulaessig", "f_S1", "f_S2", "f_S3", "f_S4", "f_S5", "qi_s0.5", "qi_s0.75", "qi_rand_strom",
            "spiegel_rand_strom", "qi_datensatz", "cpu_s", "sekunden", "fehler"]
    if MK:
        kopf += [f"r_cos_{m}_{n - MK[1] // 2}" for m in range(MK[0]) for n in range(MK[1])] + [f"z_sin_{m}_{n - MK[1] // 2}" for m in range(MK[0]) for n in range(MK[1])]
    zeilen = []
    for r in FO + DS + ST:
        mt = r.get("metriken") or {}; z = {k: "" for k in kopf}
        z.update({"name": r["name"], "typ": r["typ"], "basis": r.get("basis", r.get("id", "DjLe3eL6" if r["typ"] == "strom" else "")),
                  "modus": r["modus"], "art": r["art"], "param": json.dumps(r.get("param", "")), "seed": r.get("seed"),
                  "ausserhalb_geprueft": r.get("ausserhalb_geprueft", ""), "abstand_sd": r.get("abstand_sd", ""),
                  "rechenbar": int(bool(r.get("konvergiert", r.get("ok")))), "cpu_s": r.get("cpu_s"), "sekunden": r.get("sekunden"),
                  "fehler": str(r.get("fehler") or "").replace("\n", " ")[:200], "qi_datensatz": r.get("qi_datensatz", "")})
        if r["typ"] == "form":
            z["qi_basis"] = qib.get(r["basis"], ""); z["qi_verh_basis"] = r.get("verh") or ""
        for k in metr:
            z[f"m_{k}"] = mt.get(k, "") if mt.get(k) is not None else ""
        for k, n in (("verletzung_P3", "v3"), ("verletzung_P2", "v2")):
            for i, v in enumerate(r.get(k) or []):
                z[f"{n}_{i}"] = v
        z["f_P3"] = r.get("f_P3", ""); z["P3_zulaessig"] = r.get("P3_zulaessig", ""); z["P2_zulaessig"] = r.get("P2_zulaessig", "")
        if r["typ"] == "strom":
            for i, f in enumerate(r["faktoren"]):
                z[f"f_S{i + 1}"] = f
            if r.get("ok"):
                z["qi_s0.5"], z["qi_s0.75"], z["qi_rand_strom"] = r["qi_flaechen"]; z["spiegel_rand_strom"] = r["spiegel_flaechen"][-1]
        rd = r.get("rand")
        if MK and rd is None and r["typ"] == "datensatz":
            pass
        if MK and rd:
            rc, zs = _pad(rd["r_cos"], MK), _pad(rd["z_sin"], MK)
            for m in range(MK[0]):
                for n in range(MK[1]):
                    z[f"r_cos_{m}_{n - MK[1] // 2}"] = rc[m, n]; z[f"z_sin_{m}_{n - MK[1] // 2}"] = zs[m, n]
        zeilen.append(z)
    with open(EXP / "alle_proben.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=kopf); w.writeheader(); w.writerows(zeilen)

    # ---- Kennzahlen Formproben
    def gruppe(rs):
        n = len(rs); k = [r for r in rs if r["konvergiert"]]; v = [r["verh"] for r in k if r.get("verh")]
        return {"n": n, "rechenbar": len(k) / n if n else None, "n_k": len(k),
                "besser": (np.mean([x < 1 for x in v]) if v else None), "faktor3": (np.mean([1 / 3 <= x <= 3 for x in v]) if v else None),
                "x10": (np.mean([x >= 10 for x in v]) if v else None), "median": (float(np.median(v)) if v else None),
                "bestes": (float(min(v)) if v else None), "p3": sum(bool(r.get("P3_zulaessig")) for r in k), "p2": sum(bool(r.get("P2_zulaessig")) for r in k)}
    nichtbasis = [r for r in FO if r["art"] != "basis"]
    vern = [r for r in nichtbasis if r["modus"] == "vernunft"]; wild = [r for r in nichtbasis if r["modus"] == "wild"]
    wild_gross = [r for r in wild if (r["art"] == "gauss" and r["param"]["sigma"] >= 1) or (r["art"] == "logskala" and r.get("sigma", 0) >= 1)
                  or r["art"] in ("kreuz", "misch")]
    G = {"vernunft": gruppe(vern), "wild": gruppe(wild), "wild >= 1 sd / Kreuzung": gruppe(wild_gross)}
    z = []
    A = z.append
    A("# Experimentmatrix: vernünftige und wilde Proben (automatische Auswertung)")
    A("")
    A(f"Stand {time.strftime('%Y-%m-%d %H:%M')}. Erzeugt von `stellarator/qi_experiment.py auswertung` (Ereignisprotokoll F-252). "
      f"Fertig: {len(FO)} von {len(plan_f)} Formproben, {len(ST)} von {len(plan_s)} Strom-Proben, {len(DS)} von {N_DS} Datensatzproben. "
      "Alle Zahlen stammen aus den Ergebnisdateien; Deutungen sind als Folgerung markiert.")
    A("")
    A("Nutzerwunsch (wörtlich, rechtschreiblich korrigiert): „Vielleicht kannst du das so machen, dass es vernunftbasierte Parameter in der Matrix gibt "
      "und auch einige wilde oder zufällige, einfach um Verständnis und Daten zu generieren.“")
    A("")
    A("## Lesehilfe")
    A("")
    A("- **QI** (Quasi-Isodynamik-Fehler): eine Zahl ohne Einheit, wie weit das Magnetfeld vom idealen Feld abweicht; 0 = ideal, kleiner ist besser. "
      "Aufgabe 3 der Rangliste verlangt QI ≤ 0,00032, Aufgabe 2 QI ≤ 0,0001 (B-051).")
    A("- **Basisform:** eine bekannte gute Plasmaform, von der aus verändert wird: Do3Qy (beste Datensatzform), Kandidat 3 halb (eigene Abwandlung), "
      "DjLe3eL6 (Form mit Spulensatz), D8ZNt2 (Startform der Filtersuche).")
    A("- **Koeffizient:** Die Plasmaoberfläche ist eine Summe von Wellen (Fourier-Reihe, r_cos und z_sin mit Index [m,n]: m Wellen ums Rohr, n Wellen "
      "den Ring entlang je Periode). Ein Koeffizient ist die Amplitude einer Welle.")
    A("- **sd (Standardabweichung):** typische Streuung eines Koeffizienten im Datensatz. 0,2 sd ist eine kleine, 2 sd eine sehr große Änderung.")
    A("- **vernünftig:** begründete Richtung (Grund steht in jeder Ergebnisdatei im Feld `grund`). **wild:** Zufall, nur für Daten und Verständnis.")
    A("- **rechenbar:** VMEC++ (der Gleichgewichtsrechner) liefert ein Ergebnis. Nicht rechenbar ist auch ein Datum (Form physikalisch/numerisch unbrauchbar).")
    A("- **Verhältnis zur Basis:** QI der Probe geteilt durch QI der unveränderten Basisform (gleich gerechnet). < 1 = besser.")
    A("- **zulässig:** jede normierte Verletzung der Aufgabe ≤ 0,01 (constellaration/problems.py), dann ist die Wertung > 0.")
    A("- **Weg ii (Strom-Proben):** Spulenfeld auf den festen Magnetflächen der offiziellen Rechnung; gegen die freie Grenze (Weg i) nur bis ±5 % "
      "Strom geprüft (B-053). Alles darüber ist ausdrücklich **außerhalb des geprüften Bereichs**.")
    A("- **R²:** Anteil der Streuung, den ein Modell erklärt (1 = alles, 0 = nichts, negativ = schlechter als der Mittelwert). "
      "LOO = jede Probe einmal weggelassen und vorhergesagt (ehrlicher als die Anpassung).")
    A("")
    # Tabelle 1: rechenbar je Basis und Modus
    A("## 1 Formproben: Anteil rechenbar, QI gegen die Basis")
    A("")
    A("| Basisform | QI Basis | Modus | Proben | rechenbar | besser als Basis | innerhalb Faktor 3 | ≥ 10× schlechter | Median Verhältnis | bestes Verhältnis | zul. P3 | zul. P2 |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for b in BASEN:
        for mo in ("vernunft", "wild"):
            g = gruppe([r for r in nichtbasis if r["basis"] == b and r["modus"] == mo])
            if g["n"]:
                A(f"| {NAMEN[b]} | {_g(qib.get(b), '.4g')} | {mo} | {g['n']} | {_pz(g['rechenbar'])} | {_pz(g['besser'])} | {_pz(g['faktor3'])} | "
                  f"{_pz(g['x10'])} | {_g(g['median'])} | {_g(g['bestes'])} | {g['p3']} | {g['p2']} |")
    for k, g in G.items():
        if g["n"]:
            A(f"| **alle** | | **{k}** | {g['n']} | {_pz(g['rechenbar'])} | {_pz(g['besser'])} | {_pz(g['faktor3'])} | {_pz(g['x10'])} | "
              f"{_g(g['median'])} | {_g(g['bestes'])} | {g['p3']} | {g['p2']} |")
    A("")
    A("Basis-Pruefstein (unveraenderte Form neu gerechnet): " + ", ".join(
        f"{NAMEN[r['basis']]} {_g((r.get('metriken') or {}).get('qi'), '.6g')}" for r in FO if r["art"] == "basis") + ".")
    A("")
    # Tabelle 2: je Art
    A("### Je Art der Veränderung")
    A("")
    A("| Modus | Art | Proben | rechenbar | besser als Basis | Median Verhältnis | Median Abstand (sd) | typische Fehlermeldung |")
    A("|---|---|---|---|---|---|---|---|")
    arten = sorted({(r["modus"], r["art"] + (f" {r['param']['sigma']}" if r["art"] == "gauss" else "")) for r in nichtbasis})
    for mo, a in arten:
        rs = [r for r in nichtbasis if r["modus"] == mo and (r["art"] + (f" {r['param']['sigma']}" if r["art"] == "gauss" else "")) == a]
        g = gruppe(rs); fe = [r["fehler"] for r in rs if r.get("fehler")]
        from collections import Counter
        typ = Counter([str(f).split(":")[0] + ": " + str(f).split(":")[1][:50] if ":" in str(f) else str(f)[:60] for f in fe]).most_common(1)
        A(f"| {mo} | {a} | {g['n']} | {_pz(g['rechenbar'])} | {_pz(g['besser'])} | {_g(g['median'])} | "
          f"{_g(float(np.median([r['abstand_sd'] for r in rs])), '.2f')} | {(typ[0][0] + f' ({typ[0][1]}×)') if typ else '–'} |")
    A("")
    # Empfindlichkeit
    A("## 2 Empfindlichkeit je Parameter (vernünftige Proben)")
    A("")
    A("Zahl = Änderung von log10(QI) je 1 sd Schritt (zentrale Differenz aus +0,2 und −0,2 sd). +0,30 heißt: 1 sd in Plusrichtung verdoppelt QI; "
      "−0,30 halbiert. Leer = eine der beiden Proben nicht rechenbar.")
    A("")
    if V:
        A("| Koeffizient | " + " | ".join(NAMEN[b] for b in BASEN) + " |")
        A("|---|" + "---|" * len(BASEN))
        emp = {}
        for j, nm in enumerate(V["frei9_namen"]):
            werte = []
            for b in BASEN:
                p = [r for r in FO if r["basis"] == b and r["art"] == "koef" and r["param"]["j"] == j and abs(abs(r["param"]["schritt"]) - 0.2) < 1e-9]
                qp = [r["qi"] for r in p if r["param"]["schritt"] > 0 and r["qi"]]; qm = [r["qi"] for r in p if r["param"]["schritt"] < 0 and r["qi"]]
                e = (np.log10(qp[0]) - np.log10(qm[0])) / 0.4 if qp and qm else None; emp[(b, j)] = e; werte.append(e)
            A(f"| {nm} | " + " | ".join(_g(e, '+.2f') for e in werte) + " |")
        A("")
        A("Linearität (wichtigster Koeffizient " + V["frei9_namen"][0] + "): Verhältnis zur Basis bei −0,3 / −0,2 / −0,1 / +0,1 / +0,2 / +0,3 sd")
        A("")
        A("| Basisform | −0,3 | −0,2 | −0,1 | +0,1 | +0,2 | +0,3 |")
        A("|---|---|---|---|---|---|---|")
        for b in BASEN:
            w = {}
            for r in FO:
                if r["basis"] == b and r["art"] == "koef" and r["param"]["j"] == 0:
                    w[round(r["param"]["schritt"], 2)] = r.get("verh")
            A(f"| {NAMEN[b]} | " + " | ".join(_g(w.get(s)) for s in (-0.3, -0.2, -0.1, 0.1, 0.2, 0.3)) + " |")
        A("")
        # Bild Empfindlichkeit
        fig, ax = plt.subplots(figsize=(9, 4.2)); farben = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]; bw = 0.2
        for k, b in enumerate(BASEN):
            vals = [emp.get((b, j)) for j in range(9)]
            ax.bar(np.arange(9) + (k - 1.5) * bw, [np.nan if v is None else v for v in vals], bw * 0.9, color=farben[k], label=NAMEN[b])
        ax.axhline(0, color="#888", lw=0.8); ax.set_xticks(range(9)); ax.set_xticklabels(V["frei9_namen"], rotation=30, ha="right", fontsize=8)
        ax.set_ylabel("Δ log10(QI) je 1 sd"); ax.set_title("Empfindlichkeit des QI je Koeffizient (zentrale Differenz ±0,2 sd)")
        ax.legend(frameon=False, fontsize=8); ax.grid(axis="y", alpha=0.3); fig.tight_layout(); fig.savefig(BILD / "empfindlichkeit.png", dpi=130); plt.close(fig)
        A("![Empfindlichkeit](qi_experiment/empfindlichkeit.png)")
        A("")
        A("Lesehilfe Bild: je Koeffizient (waagerecht) vier Balken, einer je Basisform. Balken nach oben: Vergrößern des Koeffizienten verschlechtert QI; "
          "nach unten: verbessert. Fehlt ein Balken, war eine Probe nicht rechenbar.")
        A("")
    # Richtungen
    A("## 3 Begründete Richtungen: vorhergesagt (lineares Datensatzmodell) gegen gerechnet")
    A("")
    A("| Basisform | Probe | Abstand (sd) | rechenbar | QI-Verhältnis | Spiegel gerechnet (Basis) | Spiegel linear erwartet Δ | Elong. | Dreieck. | iota/nfp | max. Verl. P3 | zul. P3 |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|")
    basismt = {r["basis"]: r["metriken"] for r in FO if r["art"] == "basis" and r["konvergiert"]}
    for r in FO:
        if r["art"] in ("richtung", "richtung_orth", "aspekt"):
            mt = r.get("metriken") or {}; bm = basismt.get(r["basis"], {})
            lab = r["art"] + " " + " ".join(f"{k}={v}" for k, v in r["param"].items())
            el = (r.get("erwartung_linear") or {}).get("spiegel")
            A(f"| {NAMEN[r['basis']]} | {lab} | {r['abstand_sd']:.2f} | {'ja' if r['konvergiert'] else 'nein'} | {_g(r.get('verh'))} | "
              f"{_g(mt.get('edge_magnetic_mirror_ratio'))} ({_g(bm.get('edge_magnetic_mirror_ratio'))}) | {_g(el, '+.3f')} | {_g(mt.get('max_elongation'))} | "
              f"{_g(mt.get('average_triangularity'))} | {_g(mt.get('edge_rotational_transform_over_n_field_periods'))} | "
              f"{_g(r.get('max_verletzung_P3'), '.3f')} | {'ja' if r.get('P3_zulaessig') else 'nein'} |")
    A("")
    # beste/schlechteste
    A("## 4 Beste und schlechteste gerechnete Formen")
    A("")
    k = [r for r in FO if r.get("qi")]
    A("| Rang | Probe | QI | Verhältnis Basis | A | Spiegel | iota/nfp | f (P3) | zul. P3 | zul. P2 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    srt = sorted(k, key=lambda r: r["qi"])
    for i, r in list(enumerate(srt))[:10] + ([(None, None)] if len(srt) > 15 else []) + list(enumerate(srt))[max(10, len(srt) - 5):]:
        if r is None:
            A("| … | | | | | | | | | |"); continue
        mt = r["metriken"]
        A(f"| {i + 1} | {r['name']} | {mt['qi']:.4g} | {_g(r.get('verh'))} | {_g(mt.get('aspect_ratio'))} | {_g(mt.get('edge_magnetic_mirror_ratio'))} | "
          f"{_g(mt.get('edge_rotational_transform_over_n_field_periods'))} | {_g(r.get('f_P3'), '.4f')} | {'ja' if r.get('P3_zulaessig') else 'nein'} | "
          f"{'ja' if r.get('P2_zulaessig') else 'nein'} |")
    A("")
    kf = sorted([r for r in FO + DS if r.get("f_P3") is not None], key=lambda r: r["f_P3"])[:5]
    A("Kleinste Verletzungssumme f (Aufgabe 3) über alle Form- und Datensatzproben: " +
      "; ".join(f"{r['name']} f = {r['f_P3']:.4f} (max. Verletzung {r.get('max_verletzung_P3', float('nan')):.3f})" for r in kf) + ".")
    A("")
    zul = [r for r in FO + DS if r.get("P3_zulaessig") or r.get("P2_zulaessig")]
    A(f"**Zulässige Proben:** Aufgabe 3: {sum(bool(r.get('P3_zulaessig')) for r in zul)}, Aufgabe 2: {sum(bool(r.get('P2_zulaessig')) for r in zul)}"
      + ((" – " + ", ".join(r["name"] for r in zul)) if zul else " (keine)") + ".")
    A("")
    # Bild Verteilung
    fig, ax = plt.subplots(figsize=(9, 4.2)); farben = {"do3": "#2a78d6", "k3": "#eb6834", "dje": "#1baf7a", "d8z": "#eda100"}
    gr = [("vernunft", ("koef",)), ("vernunft", ("aspekt", "richtung", "richtung_orth")), ("wild", ("gauss", "logskala")),
          ("wild", ("vorzeichen",)), ("wild", ("kreuz", "misch"))]
    labs = ["vernünftig:\nKoeffizient", "vernünftig:\nRichtung/Aspekt", "wild:\nRauschen", "wild:\nVorzeichen", "wild:\nKreuzung"]
    rng = np.random.default_rng(0)
    for gi, (mo, aa) in enumerate(gr):
        for b in BASEN:
            v = [r["verh"] for r in nichtbasis if r["modus"] == mo and r["art"] in aa and r["basis"] == b and r.get("verh")]
            ax.scatter(gi + rng.uniform(-0.25, 0.25, len(v)), v, s=22, color=farben[b], label=NAMEN[b] if gi == 0 else None, edgecolor="white", lw=0.6)
            n_tot = len([r for r in nichtbasis if r["modus"] == mo and r["art"] in aa])
        nk = len([r for r in nichtbasis if r["modus"] == mo and r["art"] in aa and not r["konvergiert"]])
        ax.text(gi, 0.02, f"nicht\nrechenbar: {nk}/{n_tot}", ha="center", va="bottom", fontsize=7, transform=ax.get_xaxis_transform())
    ax.set_yscale("log"); ax.axhline(1, color="#555", lw=0.8, ls="--"); ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs, fontsize=8)
    ax.set_ylabel("QI Probe / QI Basis (log)"); ax.set_title("QI gegen die unveränderte Basisform (unter der Linie = besser)")
    ax.legend(frameon=False, fontsize=8, loc="upper left"); ax.grid(axis="y", alpha=0.3); fig.tight_layout(); fig.savefig(BILD / "verteilung.png", dpi=130); plt.close(fig)
    A("![Verteilung](qi_experiment/verteilung.png)")
    A("")
    A("Lesehilfe Bild: jeder Punkt eine gerechnete Probe, Farbe = Basisform. Senkrecht das QI-Verhältnis zur Basis (logarithmisch: jede Teilung Faktor 10). "
      "Die gestrichelte Linie ist die Basis; Punkte darunter sind besser. Unten steht, wie viele Proben der Gruppe VMEC++ nicht rechnen konnte.")
    A("")
    # rechenbar gegen Abstand
    fig, ax = plt.subplots(figsize=(7, 3.8))
    alle = [r for r in nichtbasis]
    if alle:
        bins = np.array([0, 0.15, 0.25, 0.4, 0.8, 1.5, 3, 100]); mid, frac, nn = [], [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            rs = [r for r in alle if lo <= r["abstand_sd"] < hi]
            if rs:
                mid.append(f"{lo:g}–{hi:g}" if hi < 100 else f"> {lo:g}"); frac.append(np.mean([r["konvergiert"] for r in rs])); nn.append(len(rs))
        ax.bar(range(len(mid)), frac, 0.7, color="#2a78d6")
        for i, (f, n) in enumerate(zip(frac, nn)):
            ax.text(i, f + 0.02, f"{100 * f:.0f} %\n(n={n})", ha="center", fontsize=7)
        ax.set_xticks(range(len(mid))); ax.set_xticklabels(mid, fontsize=8); ax.set_ylim(0, 1.18); ax.set_xlabel("Abstand von der Basis (sd, 80 Koeffizienten)")
        ax.set_ylabel("Anteil rechenbar"); ax.set_title("Wie weit darf man von einer guten Form weg?"); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(BILD / "rechenbar_abstand.png", dpi=130); plt.close(fig)
    A("![Rechenbar gegen Abstand](qi_experiment/rechenbar_abstand.png)")
    A("")
    A("Lesehilfe Bild: Proben nach ihrem Abstand von der Basisform gruppiert (Abstand = Länge der Änderung über alle 80 freien Koeffizienten, in sd). "
      "Balkenhöhe = Anteil, den VMEC++ rechnen konnte.")
    A("")
    # Datensatz
    A("## 5 Datensatz-Zufallsstichprobe")
    A("")
    if DS:
        kd = [r for r in DS if r["konvergiert"] and (r.get("metriken") or {}).get("qi")]
        abw = [abs(r["metriken"]["qi"] - r["qi_datensatz"]) / r["qi_datensatz"] for r in kd if r.get("qi_datensatz")]
        prof = [r for r in kd if r.get("qi_flaeche") and None not in r["qi_flaeche"]]
        randmax = sum(int(np.argmax(r["qi_flaeche"]) == len(r["qi_flaeche"]) - 1) for r in prof)
        ohne = sum(1 for r in DS if r.get("qi_datensatz") is None)
        A(f"- {len(DS)} Formen gerechnet, davon {len(kd)} mit QI ({_pz(len(kd) / len(DS))}); im Datensatz ohne QI-Wert waren {ohne}.")
        if abw:
            A(f"- Nachrechnung gegen den Datensatzwert: Median relative Abweichung {np.median(abw):.2e}, größte {max(abw):.2e}.")
        if prof:
            A(f"- Rand ist die schlechteste Fläche bei {randmax} von {len(prof)} Formen (Vergleich B-052 und Profil-Serie).")
        q = np.array([r["metriken"]["qi"] for r in kd])
        if len(q):
            A(f"- QI der Stichprobe: Median {np.median(q):.3g}, 10.–90. Perzentil {np.percentile(q, 10):.3g} bis {np.percentile(q, 90):.3g} "
              "(Bezug: wie gut ist eine beliebige Datenform gegen die wilden Proben).")
        A(f"- Zulässig nach Aufgabe 3: {sum(bool(r.get('P3_zulaessig')) for r in DS)}, nach Aufgabe 2: {sum(bool(r.get('P2_zulaessig')) for r in DS)}.")
    else:
        A("- noch keine Ergebnisse")
    A("")
    # Strom
    A("## 6 Strom-Proben (DjLe3eL6, Weg ii): wie linear ist QI in den Strömen?")
    A("")
    so = [r for r in ST if r.get("ok")]
    stat = {}
    if so:
        qb = [r["qi_rand"] for r in so if r["art"] == "basis"]; qb = qb[0] if qb else None
        Fm = lambda rs: np.array([r["faktoren"] for r in rs]); Q = lambda rs: np.array([r["qi_rand"] for r in rs])
        ein = [r for r in so if not r["ausserhalb_geprueft"]]; aus_ = [r for r in so if r["ausserhalb_geprueft"]]
        A(f"QI am Rand der Basis (Weg ii): {_g(qb, '.6g')} (B-053: 0,000554). Proben gerechnet: {len(so)} von {len(ST)}; "
          f"im geprüften Bereich ±5 %: {len(ein)}, außerhalb: {len(aus_)}.")
        A("")
        A("| Menge | Proben | R² linear (Anpassung) | R² linear (LOO) | R² log10 (LOO) | R² mit Modell aus ±5 % vorhergesagt | QI < Basis | bestes QI | dazu Faktoren |")
        A("|---|---|---|---|---|---|---|---|---|")
        c_ein = None
        if len(ein) >= 8:
            r2e, c_ein = _r2(Fm(ein), Q(ein))
        mengen = [("±5 % (geprüft)", ein)] + [(n, [r for r in aus_ if r["art"] == a]) for n, a in
                                                 (("±20 % (außerhalb)", "u20"), ("±50 % (außerhalb)", "u50"), ("Vorzeichenwechsel (außerhalb)", "vz"))]
        for n, rs in mengen:
            if len(rs) < 8:
                A(f"| {n} | {len(rs)} | – | – | – | – | – | – | – |"); continue
            r2, _ = _r2(Fm(rs), Q(rs)); cv = _r2_cv(Fm(rs), Q(rs))
            ql = np.log10(np.clip(Q(rs), 1e-12, None)); cvl = _r2_cv(Fm(rs), ql)
            ext = None
            if c_ein is not None:
                pr = np.c_[np.ones(len(rs)), Fm(rs)] @ c_ein; y = Q(rs); ext = float(1 - np.sum((y - pr) ** 2) / np.sum((y - y.mean()) ** 2))
            besser = int(np.sum(Q(rs) < qb)) if qb else None; ib = int(np.argmin(Q(rs)))
            stat[n] = {"r2_loo": cv, "r2": r2, "besser": besser, "n": len(rs)}
            A(f"| {n} | {len(rs)} | {r2:.3f} | {cv:.3f} | {cvl:.3f} | {_g(ext, '.3f')} | {besser} | {Q(rs)[ib]:.4g} | "
              f"{', '.join(f'{x:.3f}' for x in rs[ib]['faktoren'])} |")
        A("")
        if c_ein is not None:
            A("Lineares Modell aus ±5 % (QI = a + Σ b_g · Faktor_g): " + ", ".join(f"b_S{i + 1} = {c_ein[i + 1]:+.3g}" for i in range(5)) +
              f" (a = {c_ein[0]:.3g}). Hinweis: Alle Ströme gemeinsam ändern QI nicht (Skaleninvarianz), daher ist die Summe der b nahe 0 zu erwarten.")
            A("")
        A("Gezielte Richtungen (vernünftig):")
        A("")
        A("| Probe | Grund | Faktoren S1..S5 | QI Rand | gegen Basis | Spiegel Rand |")
        A("|---|---|---|---|---|---|")
        for r in so:
            if r["modus"] == "vernunft" and r["art"] != "lhs":
                A(f"| {r['art']} | {r['grund']} | {', '.join(f'{x:.3f}' for x in r['faktoren'])} | {r['qi_rand']:.5g} | "
                  f"{_g(r['qi_rand'] / qb - 1 if qb else None, '+.1%')} | {r['spiegel_flaechen'][-1]:.4f} |")
        A("")
        fig, ax = plt.subplots(figsize=(6.4, 5))
        if c_ein is not None:
            for n, rs, f_ in (("±5 % (geprüft)", ein, "#2a78d6"), ("±20 %", [r for r in aus_ if r["art"] == "u20"], "#1baf7a"),
                              ("±50 %", [r for r in aus_ if r["art"] == "u50"], "#eda100"), ("Vorzeichenwechsel", [r for r in aus_ if r["art"] == "vz"], "#eb6834")):
                if rs:
                    pr = np.c_[np.ones(len(rs)), Fm(rs)] @ c_ein
                    ax.scatter(np.clip(pr, 1e-6, None), Q(rs), s=18, color=f_, label=n, edgecolor="white", lw=0.5)
            lo_, hi_ = ax.get_xlim(); ax.plot([1e-6, 1], [1e-6, 1], color="#666", lw=0.8, ls="--")
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("QI vorhergesagt (lineares Modell aus ±5 %)"); ax.set_ylabel("QI gerechnet (Weg ii)")
            ax.set_title("Strom-Proben: trägt die Linearität?"); ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.3)
            if qb:
                ax.axhline(qb, color="#999", lw=0.7, ls=":")
        fig.tight_layout(); fig.savefig(BILD / "strom_linear.png", dpi=130); plt.close(fig)
        A("![Strom linear](qi_experiment/strom_linear.png)")
        A("")
        A("Lesehilfe Bild: waagerecht die Vorhersage des einfachen Modells, das nur aus den ±5-%-Proben gelernt wurde, senkrecht der gerechnete Wert. "
          "Liegen die Punkte auf der gestrichelten Linie, ist QI dort linear in den Strömen. Punkte links am Rand: Modell sagt QI ≤ 0 vorher (unmöglich, "
          "die Linearität ist dort gebrochen). Gepunktete Linie: QI der Basis. Außerhalb ±5 % ist schon das Werkzeug (Weg ii) nicht geprüft.")
    else:
        A("- noch keine Ergebnisse")
    A("")
    # Erwartung
    A("## 7 Erwartung F-252 gegen Ergebnis (automatisch verglichen)")
    A("")

    def urteil(x, lo, hi):
        return "–" if x is None else ("getroffen" if lo <= x <= hi else "verfehlt")
    gv, gw = G["vernunft"], G["wild >= 1 sd / Kreuzung"]
    zul3 = sum(bool(r.get("P3_zulaessig")) for r in wild)
    A("| Erwartung (vorher) | gemessen | Urteil |")
    A("|---|---|---|")
    A(f"| vernünftig zu 85–95 % rechenbar | {_pz(gv['rechenbar'])} | {urteil(gv['rechenbar'], 0.85, 0.95)} |")
    A(f"| vernünftig: QI innerhalb Faktor 3 der Basis (Großteil) | {_pz(gv['faktor3'])} der rechenbaren | {urteil(gv['faktor3'], 0.5, 1.0)} |")
    A(f"| vernünftig: 10–30 % besser als die Basis | {_pz(gv['besser'])} | {urteil(gv['besser'], 0.10, 0.30)} |")
    A(f"| wild (≥ 1 sd, Kreuzung) nur 20–50 % rechenbar | {_pz(gw['rechenbar'])} | {urteil(gw['rechenbar'], 0.20, 0.50)} |")
    A(f"| wild: QI meist 10- bis 1000-fach schlechter (Median) | Median {_g(gw['median'])} | {urteil(gw['median'], 10, 1000)} |")
    A(f"| keine wilde Probe zulässig nach Aufgabe 3 | {zul3} | {'–' if not wild else ('getroffen' if zul3 == 0 else 'verfehlt')} |")
    s5, s50 = stat.get("±5 % (geprüft)"), stat.get("±50 % (außerhalb)")
    A(f"| Strom ±5 %: lineares Modell R² > 0,95 | {_g(s5['r2_loo'] if s5 else None, '.3f')} (LOO) | {urteil(s5['r2_loo'] if s5 else None, 0.95, 1.0)} |")
    A(f"| Strom ±50 %: R² deutlich niedriger | {_g(s50['r2_loo'] if s50 else None, '.3f')} (LOO) | "
      f"{'–' if not (s5 and s50) else ('getroffen' if s50['r2_loo'] < s5['r2_loo'] - 0.1 else 'verfehlt')} |")
    A(f"| Strom ±50 %: einzelne Proben mit QI < Basis | {s50['besser'] if s50 else '–'} | {'–' if not s50 else ('getroffen' if s50['besser'] else 'verfehlt')} |")
    A("")
    # belegt/Folgerung/offen
    A("## 8 Belegt, Folgerung, offen")
    A("")
    A("**Belegt** (gemessen, aus den Dateien):")
    A("")
    A(f"- Anteil rechenbar: vernünftig {_pz(gv['rechenbar'])}, wild gesamt {_pz(G['wild']['rechenbar'])}, wild ≥ 1 sd/Kreuzung {_pz(gw['rechenbar'])}.")
    A(f"- Besser als die eigene Basis: vernünftig {_pz(gv['besser'])}, wild {_pz(G['wild']['besser'])} der rechenbaren Proben.")
    A(f"- Zulässige Formen: Aufgabe 3 {sum(bool(r.get('P3_zulaessig')) for r in FO + DS)}, Aufgabe 2 {sum(bool(r.get('P2_zulaessig')) for r in FO + DS)}.")
    if s5:
        A(f"- Strom: lineares Modell im geprüften Bereich R² (LOO) {s5['r2_loo']:.3f}" + (f", bei ±50 % {s50['r2_loo']:.3f}." if s50 else "."))
    A("")
    A("**Folgerung** (Deutung, regelbasiert erzeugt; vom Menschen prüfen):")
    A("")
    if gv["besser"] is not None and G["wild"]["besser"] is not None:
        if G["wild"]["besser"] > gv["besser"]:
            A("- Wilde Proben sind öfter besser als vernünftige: die Umgebung der Basisformen ist kein gutes Suchgebiet (laut Deutung F-252 weiter suchen statt lokal).")
        else:
            A("- Vernünftige Proben sind mindestens so oft besser wie wilde: lokales Suchen um gute Formen bleibt der richtige Weg; Zufall liefert vor allem Daten über die Grenzen der Rechenbarkeit.")
    if s5 and stat.get("±20 % (außerhalb)"):
        if stat["±20 % (außerhalb)"]["r2_loo"] < 0.9:
            A("- Die Linearität bricht schon bei ±20 % ein: Weg ii nicht für Optimierungen über ±5 % nutzen, ohne Gegenprüfung mit freier Grenze (Weg i).")
        else:
            A("- Bis ±20 % bleibt QI annähernd linear in den Strömen (im Modell Weg ii); das Werkzeug selbst ist dort aber nicht geprüft.")
    A("- Die Wirkung einzelner Koeffizienten unterscheidet sich je Basisform (Tabelle Abschnitt 2); eine allgemeine Regel ‚Koeffizient X senken hilft‘ gibt es nur, wenn alle vier Vorzeichen gleich sind.")
    A("")
    A("**Offen:**")
    A("")
    A("- Strom-Proben außerhalb ±5 % mit freier Grenze (Weg i, VMEC++ free-boundary) gegenprüfen; erst dann sind sie physikalisch belastbar.")
    A("- Die CSV `sim/qi_flaeche/experiment/alle_proben.csv` (alle Proben, Koeffizienten, Kennzahlen, Verletzungen, Fehler) als Lerndaten nutzen: "
      "z. B. Klassifikator ‚rechenbar ja/nein‘ und Surrogat nahe der Basisformen.")
    A("- Beste Proben (Abschnitt 4) als Startformen für eine weitere lokale Suche prüfen; Spulen für neue Formen fehlen.")
    A("")
    A("## English summary")
    A("")
    A(f"Experiment matrix requested by the user (reasoned plus wild/random parameter variations, for understanding and data, not for the optimum). "
      f"Shape probes around four base plasmas (Do3Qy, candidate 3 half step, DjLe3eL6, D8ZNt2) were evaluated with VMEC++ at the official high-fidelity "
      f"settings; coil-current probes use the fixed-surface perturbation model (way ii) for DjLe3eL6, validated only within ±5 %. "
      f"Completed: {len(FO)}/{len(plan_f)} shape probes, {len(ST)}/{len(plan_s)} current probes, {len(DS)}/{N_DS} random dataset shapes. "
      f"Computable: reasoned {_pz(gv['rechenbar'])}, wild {_pz(G['wild']['rechenbar'])} (≥ 1 sd or crossover {_pz(gw['rechenbar'])}). "
      f"Better than their base: reasoned {_pz(gv['besser'])}, wild {_pz(G['wild']['besser'])}. "
      f"Feasible for problem 3 (MHD-stable QI): {sum(bool(r.get('P3_zulaessig')) for r in FO + DS)}; problem 2: {sum(bool(r.get('P2_zulaessig')) for r in FO + DS)}. "
      + (f"Linear model QI ~ currents: R² (leave-one-out) {s5['r2_loo']:.3f} within ±5 %" + (f", {s50['r2_loo']:.3f} at ±50 % (outside the validated range)." if s50 else ".") if s5 else "")
      + " All samples, coefficients, metrics, violations and error messages are in sim/qi_flaeche/experiment/alle_proben.csv. Interpretations are rule-generated and need human review.")
    A("")
    (BER / "qi_experiment.md").write_text("\n".join(z) + "\n")
    print("Bericht", BER / "qi_experiment.md", "| Formproben", len(FO), "Strom", len(ST), "Datensatz", len(DS))


def liste(was="alle"):
    if was in ("alle", "form"):
        for p in formplan():
            print("form", p["prio"], p["name"])
    if was in ("alle", "strom"):
        for p in stromplan():
            print("strom", p["modus"], p["name"])
    if was in ("alle", "datensatz"):
        for k in range(N_DS):
            print("datensatz", k, ds_name(k))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "vorbereiten":
        vorbereiten()
    elif c == "form":
        form(sys.argv[2])
    elif c == "strom":
        strom(sys.argv[2])
    elif c == "datensatz":
        datensatz(sys.argv[2])
    elif c == "ds_kind":
        ds_kind(sys.argv[2])
    elif c == "liste":
        liste(sys.argv[2] if len(sys.argv) > 2 else "alle")
    elif c == "auswertung":
        auswertung()
    else:
        raise SystemExit(__doc__)
