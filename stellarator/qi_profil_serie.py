"""Unbeaufsichtigte Datenerzeugung: QI je Flaeche (Profil von innen nach aussen) fuer viele Datensatzformen.

Zweck: Auswertbare Daten ohne Betreuung erzeugen. Beantwortet u. a.: Ist der Rand im Datensatz die schlechteste Flaeche?
Wie haeufig versteckt sich innen ein groesserer Fehler (wie bei DjLe3eL6)? Hangen Profilform und Kennzahlen zusammen?

  .venv-constellaration/bin/python -m stellarator.qi_profil_serie liste      # Formliste + Rand-Daten (sim/qi_flaeche/profil_serie/liste.json)
  .venv-constellaration/bin/python -m stellarator.qi_profil_serie eins <id>  # eine Form rechnen (fertige werden uebersprungen)
  .venv-constellaration/bin/python -m stellarator.qi_profil_serie auswertung # Tabelle docs/recherche/qi_tragwerk/qi_profil_serie.md
Start der ganzen Kette (losgeloest, pausierbar mit ~/bin/rechnung pause/weiter): sim/qi_flaeche/profil_serie/lauf.sh
Je Form nur eine kleine JSON (kein Residuenfeld), Ergebnis sim/qi_flaeche/profil_serie/<id>.json.
"""
import glob
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUS = ROOT / "sim" / "qi_flaeche" / "profil_serie"
S = [0.02, 0.1, 0.25, 0.5, 0.7, 0.85, 1.0]
N_P3, N_QI = 60, 60


def liste():
    import pyarrow.parquet as pq
    f = json.loads((ROOT / "sim/qi_flaeche/filter138.json").read_text())
    ids = [z["id"] for z in sorted(f["P3_ohne_QI"], key=lambda z: z["qi"])[:N_P3]]
    best = []
    for fn in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet"))):
        t = pq.read_table(fn, columns=["plasma_config_id", "metrics.qi"]).to_pydict()
        best += [(q, i) for i, q in zip(t["plasma_config_id"], t["metrics.qi"]) if q is not None and q > 0]
    best.sort()
    ids += [i for _, i in best[:N_QI]]
    ids = list(dict.fromkeys(ids)); rest = set(ids); out = {}
    for fn in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet"))):
        t = pq.read_table(fn, columns=["plasma_config_id", "boundary.json", "metrics.qi"], filters=[("plasma_config_id", "in", list(rest))]).to_pydict()
        for i, b, q in zip(t["plasma_config_id"], t["boundary.json"], t["metrics.qi"]):
            out[i] = {"boundary": json.loads(b), "qi_daten": q}
    AUS.mkdir(parents=True, exist_ok=True)
    (AUS / "liste.json").write_text(json.dumps({"ids": [i for i in ids if i in out], "formen": out}))
    print(len(out), "Formen")


def eins(fid):
    a = AUS / f"{fid}.json"
    if a.exists():
        print("fertig:", fid); return
    L = json.loads((AUS / "liste.json").read_text())["formen"][fid]
    from constellaration import forward_model
    from constellaration.boozer import boozer as bm
    from constellaration.geometry import surface_rz_fourier as srf
    from constellaration.omnigeneity import qi
    t0 = time.time()
    try:
        m, w = forward_model.forward_model(srf.SurfaceRZFourier.model_validate(L["boundary"]),
                                           settings=forward_model.ConstellarationSettings.default_high_fidelity())
        bz = bm.run_boozer(w, bm.create_boozer_settings_from_equilibrium_resolution(w, bm.BoozerPresetSettings(normalized_toroidal_flux=S)))
        from stellarator.qi_karte import ausschnitt
        qs = qi.QISettings(); q_fl, fehler = [], {}
        for js in range(bz.n_boozer_flux_surfaces):
            try:
                q_fl.append(float(np.sum(qi.quasi_isodynamicity_residual(ausschnitt(bz, js), qs).residuals ** 2)))
            except Exception as e:
                q_fl.append(None); fehler[js] = f"{type(e).__name__}: {str(e)[:100]}"
        j = {"id": fid, "ok": True, "s": [float(x) for x in bz.boozer_normalized_toroidal_flux], "qi_flaeche": q_fl, "fehler": fehler,
             "qi_offiziell": m.qi, "qi_datensatz": L["qi_daten"], "nfp": int(bz.n_field_periods),
             "metriken": {k: (float(v) if isinstance(v, (int, float)) else None) for k, v in m.model_dump().items()}, "sek": time.time() - t0}
    except Exception as e:
        j = {"id": fid, "ok": False, "fehler": f"{type(e).__name__}: {str(e)[:200]}", "sek": time.time() - t0}
    a.write_text(json.dumps(j)); print(fid, j.get("ok"), flush=True)


def auswertung():
    R = [json.loads(p.read_text()) for p in sorted(AUS.glob("*.json")) if p.name != "liste.json"]
    ok = [r for r in R if r.get("ok") and r.get("qi_flaeche") and None not in r["qi_flaeche"]]
    z = [f"# QI-Profil je Flaeche, Serie ({len(ok)} von {len(R)} Formen ausgewertet)", "",
         "Flaechen s = " + ", ".join(str(x) for x in S) + "; QI je Flaeche = Summe der quadrierten Residuen (wie offizielle Kennzahl am Rand).", ""]
    if ok:
        rand = np.array([r["qi_flaeche"][-1] for r in ok]); mx = np.array([max(r["qi_flaeche"]) for r in ok])
        verh = mx / rand; imax = np.array([int(np.argmax(r["qi_flaeche"])) for r in ok])
        abw = np.array([abs(r["qi_flaeche"][-1] - r["qi_offiziell"]) / r["qi_offiziell"] for r in ok if r.get("qi_offiziell")])
        z += [f"- Rand ist die schlechteste Flaeche bei {int((imax == len(S) - 1).sum())} von {len(ok)} Formen.",
              f"- Maximum / Randwert: Median {np.median(verh):.2f}, 90. Perzentil {np.percentile(verh, 90):.2f}, groesster Wert {verh.max():.2f}.",
              f"- Formen mit Maximum innen mehr als 20 % ueber Rand: {int((verh > 1.2).sum())}.",
              f"- Abweichung Randwert (7-Flaechen-Lauf) zu offiziellem QI: Median {np.median(abw):.2e}, max {abw.max():.2e}.", "",
              "| id | nfp | QI Rand | max/Rand | Flaeche des Maximums | " + " | ".join(f"s={x}" for x in S) + " |", "|---|---|---|---|---|" + "---|" * len(S)]
        for r, v, i in sorted(zip(ok, verh, imax), key=lambda t: t[0]["qi_flaeche"][-1]):
            z.append(f"| {r['id']} | {r['nfp']} | {r['qi_flaeche'][-1]:.3e} | {v:.2f} | {S[i]} | " + " | ".join(f"{q:.2e}" for q in r["qi_flaeche"]) + " |")
    bad = [r for r in R if not r.get("ok") or (r.get("qi_flaeche") and None in r["qi_flaeche"])]
    z += ["", f"Nicht vollstaendig ausgewertet: {len(bad)} (VMEC++ oder QI abgebrochen):"] + [f"- {r['id']}: {r.get('fehler')}" for r in bad[:40]]
    p = ROOT / "docs/recherche/qi_tragwerk/qi_profil_serie.md"; p.write_text("\n".join(z) + "\n"); print(p.name, len(ok))


if __name__ == "__main__":
    {"liste": liste, "eins": lambda: eins(sys.argv[2]), "auswertung": auswertung}[sys.argv[1]]()
