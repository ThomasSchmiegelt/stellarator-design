"""QI-Restfehler als Karte ueber mehrere Flaechen im Plasma (nicht nur am Rand).

Aufruf (aus ~/hermes/fusion, je Form ein eigener Scope, hoechstens 2 parallel):
  systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 --description="hermes python qi_karte do3" \
      env OMP_NUM_THREADS=1 .venv-constellaration/bin/python -m stellarator.qi_karte eins do3
  ... eins k3 | eins d8z | eins dje          # Formen siehe FORMEN
  .venv-constellaration/bin/python -m stellarator.qi_karte bilder         # Bilder + Zusammenfassung aus den fertigen Formen

Ablauf je Form: forward_model mit ConstellarationSettings.default_high_fidelity() (liefert den offiziellen QI am Rand und das
VMEC++-Gleichgewicht); danach auf demselben Gleichgewicht booz_xform fuer alle Flaechen S und je Flaeche
omnigeneity.qi.quasi_isodynamicity_residual (dieselbe Funktion wie das Paket, Residuen behalten statt nur summiert).
Jede Flaeche wird einzeln bewertet (Ausschnitt der Boozer-Ausgabe), damit ein Fehler wie 'Minimum of B is at the boundary'
auf einer inneren Flaeche nicht die anderen verwirft. Pruefstein: Summe der Quadrate an s=1 gegen den offiziellen QI; zusaetzlich
eine eigene Boozer-Rechnung nur mit [1.0] wie im Paket.
Ergebnis: sim/qi_flaeche/karte/<form>.npz (Residuen float32, Summen float64) und <form>.json; fertige Formen werden uebersprungen.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUS = ROOT / "sim" / "qi_flaeche" / "karte"
S = [0.02, 0.05, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0]
FORMEN = {
    "do3": ("Do3QyJbtRhtGhrTiBSBbyKM (beste Datensatzform)", "parquet", "Do3QyJbtRhtGhrTiBSBbyKM"),
    "k3": ("Kandidat 3, halber Schritt (eigene Form)", "datei", "sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json"),
    "d8z": ("D8ZNt2qFQLQQxMVitWaeCid (Startform, Filter 138)", "parquet", "D8ZNt2qFQLQQxMVitWaeCid"),
    "dje": ("DjLe3eL6 (Datensatzform mit Spulen)", "datei", "sim/constellaration/qi/proxima_spulen_dje/boundary.json"),
}


def rand(form):
    _, art, q = FORMEN[form]
    if art == "datei":
        return json.loads((ROOT / q).read_text()), None
    import glob
    import pyarrow.parquet as pq
    for fn in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet"))):
        t = pq.read_table(fn, columns=["plasma_config_id", "boundary.json", "metrics.qi"], filters=[("plasma_config_id", "=", q)])
        if t.num_rows:
            return json.loads(t.column(1)[0].as_py()), float(t.column(2)[0].as_py())
    raise KeyError(q)


def ausschnitt(bz, js):
    """Boozer-Ausgabe nur mit Flaeche js (Spalte js der *_b-Felder); qi.py rechnet jede Flaeche unabhaengig."""
    d = {}
    for k in ("bmnc_b", "bmns_b", "gmnc_b", "gmns_b", "rmnc_b", "rmns_b", "zmnc_b", "zmns_b", "numnc_b", "numns_b"):
        d[k] = getattr(bz, k)[:, [js]]
    d["boozer_normalized_toroidal_flux"] = bz.boozer_normalized_toroidal_flux[[js]]
    d["boozer_flux_surface_indices"] = [bz.boozer_flux_surface_indices[js]]
    return bz.model_copy(update=d)


def eins(form):
    AUS.mkdir(parents=True, exist_ok=True)
    if (AUS / f"{form}.json").exists():
        print("fertig, uebersprungen:", form); return
    from constellaration import forward_model
    from constellaration.boozer import boozer as bm
    from constellaration.geometry import surface_rz_fourier as srf
    from constellaration.omnigeneity import qi
    t0 = time.time(); b, qi_daten = rand(form)
    m, w = forward_model.forward_model(srf.SurfaceRZFourier.model_validate(b),
                                       settings=forward_model.ConstellarationSettings.default_high_fidelity())
    t1 = time.time(); qs = qi.QISettings()
    # Pruefstein 2: wie im Paket nur [1.0]
    bz1 = bm.run_boozer(w, bm.create_boozer_settings_from_equilibrium_resolution(w, bm.BoozerPresetSettings(normalized_toroidal_flux=[1.0])))
    qi_rand_eigen = float(np.sum(qi.quasi_isodynamicity_residual(bz1, qs).residuals ** 2))
    bz = bm.run_boozer(w, bm.create_boozer_settings_from_equilibrium_resolution(w, bm.BoozerPresetSettings(normalized_toroidal_flux=S)))
    ns = bz.n_boozer_flux_surfaces
    R = np.full((ns, qs.n_field_lines, qs.n_output_toroidal_points), np.nan)
    fehler = {}
    for js in range(ns):
        try:
            R[js] = qi.quasi_isodynamicity_residual(ausschnitt(bz, js), qs).residuals[0]
        except Exception as e:
            fehler[js] = f"{type(e).__name__}: {str(e)[:120]}"
        print(form, js, float(bz.boozer_normalized_toroidal_flux[js]), np.nansum(R[js] ** 2) if js not in fehler else fehler[js], flush=True)
    # Toroidalgitter wie qi.py (Startwinkel aus bmnc[1,1])
    nfp = bz.n_field_periods; p0 = np.pi / nfp if bz.bmnc[1, 1] < 0 else 0.0
    phi = np.linspace(p0, p0 + 2 * np.pi / nfp, qs.n_output_toroidal_points)
    from scipy import interpolate
    iota = interpolate.UnivariateSpline(bz.normalized_toroidal_flux, bz.iota, k=1, s=0)(bz.boozer_normalized_toroidal_flux)
    R2 = R ** 2
    q_fl = R2.sum((1, 2))                      # QI je Flaeche (Summe der Quadrate, wie die offizielle Kennzahl je Flaeche)
    q_rand = float(q_fl[-1]) if (ns - 1) not in fehler else None
    np.savez_compressed(AUS / f"{form}.npz", residuen=R.astype(np.float32), s=bz.boozer_normalized_toroidal_flux, phi=phi,
                        qi_flaeche=q_fl, je_feldlinie=R2.sum(2), je_winkel=R2.sum(1), iota=iota)
    ab = lambda a, b_: None if (a is None or b_ is None) else float(abs(a - b_) / abs(b_))
    j = {"form": form, "name": FORMEN[form][0], "nfp": int(nfp), "s_gewuenscht": S, "s": [float(x) for x in bz.boozer_normalized_toroidal_flux],
         "iota": [float(x) for x in iota], "qi_flaeche": [None if i in fehler else float(q_fl[i]) for i in range(ns)], "fehler": fehler,
         "qi_offiziell_forward_model": m.qi, "qi_datensatz": qi_daten, "qi_rand_eigene_boozer_1.0": qi_rand_eigen, "qi_rand_mehrflaechen": q_rand,
         "rel_abw_rand_mehrflaechen_zu_offiziell": ab(q_rand, m.qi), "rel_abw_rand_eigen_zu_offiziell": ab(qi_rand_eigen, m.qi),
         "qi_summe_alle_flaechen": float(np.nansum(q_fl)), "phi_start": p0,
         "metriken": {k: (float(v) if isinstance(v, (int, float)) else None) for k, v in m.model_dump().items()},
         "sek_vmec": t1 - t0, "sek_gesamt": time.time() - t0}
    (AUS / f"{form}.json").write_text(json.dumps(j, indent=1)); print(json.dumps({k: j[k] for k in ("form", "qi_offiziell_forward_model", "qi_rand_mehrflaechen", "rel_abw_rand_mehrflaechen_zu_offiziell", "qi_flaeche")}), flush=True)


def bilder():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm, TwoSlopeNorm
    fs = [f for f in FORMEN if (AUS / f"{f}.json").exists()]
    D = {f: (json.loads((AUS / f"{f}.json").read_text()), np.load(AUS / f"{f}.npz")) for f in fs}
    kurz = {"do3": "Do3Qy", "k3": "K3 halb", "d8z": "D8ZNt2", "dje": "DjLe3eL6"}
    farbe = {"do3": "#1b6ca8", "k3": "#2a9d8f", "d8z": "#c0392b", "dje": "#8e6c8a"}
    for f, (j, z) in D.items():
        R, s, phi = z["residuen"].astype(float), z["s"], z["phi"]
        zeige = [i for i, x in enumerate(s) if np.isfinite(R[i]).all() and min(abs(x - t) for t in (0.1, 0.25, 0.5, 0.75, 1.0)) < 0.02]
        fig, ax = plt.subplots(1, len(zeige), figsize=(3.3 * len(zeige), 3.6), sharey=True, constrained_layout=True)
        ax = np.atleast_1d(ax); v = np.nanmax(np.abs(R[zeige])) * np.sqrt(R.shape[1] * R.shape[2])
        for a, i in zip(ax, zeige):
            # Residuen sind mit 1/sqrt(75*2000) skaliert; fuer die Karte zurueck auf |B|-Einheiten (0 = Mulde, 1 = Spitze)
            im = a.pcolormesh((phi - phi[0]) * j["nfp"] / (2 * np.pi), np.arange(R.shape[1]), R[i] * np.sqrt(R.shape[1] * R.shape[2]),
                              cmap="RdBu_r", norm=TwoSlopeNorm(0, -v, v), shading="auto", rasterized=True)
            a.set_title(f"s = {s[i]:.2f}\nQI Fläche = {np.sum(R[i]**2):.2e}", fontsize=9); a.set_xlabel("Toroidalwinkel (1 = eine Periode)")
        ax[0].set_ylabel("Feldlinie Nr. (0 und 74 identisch)")
        fig.colorbar(im, ax=ax, label="B_QI − B (1 = Muldentiefe)")
        fig.suptitle(f"QI-Restfehler-Karte {kurz[f]} (rot: Feld zu schwach, blau: zu stark gegenüber dem idealen QI-Feld)", fontsize=10)
        fig.savefig(AUS / f"karte_{f}.png", dpi=110); plt.close(fig)
    # Vergleich: QI je Flaeche ueber s
    fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    for f, (j, z) in D.items():
        q = np.array([np.nan if x is None else x for x in j["qi_flaeche"]], float)
        ax.semilogy(j["s"], q, "o-", color=farbe[f], label=f"{kurz[f]} (offiziell {j['qi_offiziell_forward_model']:.2e})")
        ax.semilogy([1.0], [j["qi_offiziell_forward_model"]], "x", color=farbe[f], ms=12, mew=2)
    ax.axhline(10 ** -3.5, color="gray", ls="--", lw=1); ax.text(0.02, 10 ** -3.5 * 1.15, "Grenze Aufgabe 3: 0,00032", fontsize=8, color="gray")
    ax.axhline(1e-4, color="gray", ls=":", lw=1); ax.text(0.02, 1.15e-4, "Grenze Aufgabe 2: 0,0001", fontsize=8, color="gray")
    ax.set_xlabel("Fläche s (normierter Toroidalfluss: 0 = Plasmamitte, 1 = Rand)"); ax.set_ylabel("QI der Fläche (kleiner = besser)")
    ax.set_title("QI-Summe je Fläche; Kreuz = offizieller Wert am Rand"); ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")
    fig.savefig(AUS / "qi_ueber_s.png", dpi=110); plt.close(fig)
    # kumuliert (Aufaddieren von innen nach aussen, flaechengewichtet: Integral ueber s)
    fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    for f, (j, z) in D.items():
        sv = np.array(j["s"]); q = np.array([np.nan if x is None else x for x in j["qi_flaeche"]], float); ok = np.isfinite(q)
        sv, q = sv[ok], q[ok]; kum = np.concatenate([[0], np.cumsum(0.5 * (q[1:] + q[:-1]) * np.diff(sv))]) + q[0] * sv[0]
        ax.plot(sv, kum / sv, "o-", color=farbe[f], label=f"{kurz[f]}: Mittel innen bis s")
        ax.plot(sv, q, ":", color=farbe[f], lw=1)
    ax.set_yscale("log"); ax.set_xlabel("Fläche s"); ax.set_ylabel("QI (Mittel über alle Flächen von 0 bis s; punktiert: Fläche allein)")
    ax.set_title("Addiert sich der Fehler nach außen auf? Volumenmittel bis s"); ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")
    fig.savefig(AUS / "qi_kumuliert.png", dpi=110); plt.close(fig)
    # Beitrag je Feldlinie und je Toroidalwinkel (Rand und Mitte)
    for name, schl, xl in (("feldlinie", "je_feldlinie", "Feldlinie Nr."), ("winkel", "je_winkel", "Toroidalwinkel (1 = eine Periode)")):
        fig, ax = plt.subplots(len(D), 1, figsize=(8, 2.3 * len(D)), sharex=True, constrained_layout=True)
        for a, (f, (j, z)) in zip(np.atleast_1d(ax), D.items()):
            Y = z[schl]; x = np.arange(Y.shape[1]) if name == "feldlinie" else (z["phi"] - z["phi"][0]) * j["nfp"] / (2 * np.pi)
            cm = plt.cm.viridis
            for i, sv in enumerate(z["s"]):
                if np.isfinite(Y[i]).all() and min(abs(sv - t) for t in (0.1, 0.25, 0.5, 0.75, 1.0)) < 0.02:
                    a.semilogy(x, np.maximum(Y[i], 1e-12), color=cm(sv), lw=1, label=f"s={sv:.2f}")
            a.set_ylabel(kurz[f]); a.grid(alpha=0.3); a.set_ylim(bottom=max(1e-10, np.nanmin(Y[np.isfinite(Y)]) + 1e-12))
        np.atleast_1d(ax)[0].legend(fontsize=7, ncol=5); np.atleast_1d(ax)[-1].set_xlabel(xl)
        fig.suptitle(f"Beitrag zum QI je {'Feldlinie' if name == 'feldlinie' else 'Toroidalwinkel'} (Fläche innen dunkel, Rand gelb)", fontsize=10)
        fig.savefig(AUS / f"beitrag_{name}.png", dpi=110); plt.close(fig)
    # Uebersichtskarte s x Toroidalwinkel (ueber Feldlinien summiert) je Form
    fig, ax = plt.subplots(1, len(D), figsize=(3.6 * len(D), 3.6), sharey=True, constrained_layout=True)
    alle = np.concatenate([z["je_winkel"][np.isfinite(z["je_winkel"])] for _, z in D.values()])
    nrm = LogNorm(max(alle.max() * 1e-5, alle[alle > 0].min()), alle.max())
    for a, (f, (j, z)) in zip(np.atleast_1d(ax), D.items()):
        im = a.pcolormesh((z["phi"] - z["phi"][0]) * j["nfp"] / (2 * np.pi), z["s"], np.maximum(z["je_winkel"], nrm.vmin), norm=nrm, cmap="magma", shading="nearest", rasterized=True)
        a.set_title(kurz[f], fontsize=9); a.set_xlabel("Toroidalwinkel (1 = Periode)")
    np.atleast_1d(ax)[0].set_ylabel("Fläche s (0 Mitte, 1 Rand)")
    fig.colorbar(im, ax=ax, label="QI-Beitrag (Summe über Feldlinien)"); fig.suptitle("Wo im Plasma steckt der QI-Fehler? (hell = viel Fehler)", fontsize=10)
    fig.savefig(AUS / "uebersicht_s_winkel.png", dpi=110); plt.close(fig)
    zus = {f: {k: j[k] for k in ("name", "s", "qi_flaeche", "fehler", "qi_offiziell_forward_model", "qi_datensatz", "qi_rand_eigene_boozer_1.0",
                                  "qi_rand_mehrflaechen", "rel_abw_rand_mehrflaechen_zu_offiziell", "rel_abw_rand_eigen_zu_offiziell", "qi_summe_alle_flaechen")}
           for f, (j, _) in D.items()}
    (AUS / "zusammenfassung.json").write_text(json.dumps(zus, indent=1)); print(json.dumps(zus, indent=1))


if __name__ == "__main__":
    {"eins": lambda: eins(sys.argv[2]), "bilder": bilder}[sys.argv[1]]()
