"""alpha_form.py — dieselben Alphas im Feld der Plasmaform allein (ohne Spulenfehler), zur Ursachentrennung.

  .venv-opt/bin/python -m stellarator.alpha_form rechnen --n 1000 --tmax 0.2 --proc 7
  .venv/bin/python -m stellarator.alpha_form vergleich        # Bild + daten/alpha_vergleich.json

Feld: das VMEC-Gleichgewicht der Stufe 1 (wout_qa_nfp2_A45.nc), mit booz_xform in Boozer-Koordinaten umgerechnet
(simsopt BoozerRadialInterpolant, enforce_vacuum: G konstant, I = 0) und als InterpolatedBoozerField gerechnet.
Bahnen: Fuehrungszentrum, stossfrei, mode gc_vac (trace_particles_boozer), verloren bei s = 1.
Das ist der Weg von Landreman & Paul (2022) fuer "precise QA".

Skalierung und Startverteilung wie in alpha_bahnen.py: rho_L/a = 0,018 ueber v_u = v * B_u / (B0 * L),
t_phys = t_u * B_u / B0; Geburtsprofil in s wie die Fusionsleistung, Winkel gleichverteilt im Volumen
(Boozer-Jacobi-Determinante ~ 1/B^2, Verwerfung), v_par/v gleichverteilt, gleicher Zufallsstartwert.
Unterschied zum Spulenlauf: nur das Feld. Ausgabe sim/alpha/<name>/ergebnis.npz (Spalten wie beim Spulenlauf,
Orte hier als (s, theta, zeta) statt x, y, z).
"""
import argparse
import json
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import time
from pathlib import Path

import numpy as np

from stellarator.alpha_bahnen import WOUT, STUFE0, AUS, B0, L

_F = {}


def feld():
    if "f" in _F:
        return _F
    from simsopt.mhd.vmec import Vmec
    from simsopt.mhd.boozer import Boozer
    import simsopt.field.boozermagneticfield as bmf
    bmf.Vmec, bmf.Boozer = Vmec, Boozer            # simsopt importiert beide nur, wenn mpi4py vorhanden ist
    from simsopt.field import BoozerRadialInterpolant, InterpolatedBoozerField
    v = Vmec(str(WOUT), verbose=False)
    nfp = v.wout.nfp
    bri = BoozerRadialInterpolant(v, order=3, mpol=24, ntor=24, enforce_vacuum=True)
    f = InterpolatedBoozerField(bri, 3, [0, 1, 32], [0, np.pi, 32], [0, 2 * np.pi / nfp, 32],
                                extrapolate=True, nfp=nfp, stellsym=True)
    # Achsfeld der Form (Einheitsgroesse)
    th, ze = np.meshgrid(np.linspace(0, 2 * np.pi, 40), np.linspace(0, 2 * np.pi / nfp, 40))
    p = np.column_stack([np.full(th.size, 1e-3), th.ravel(), ze.ravel()])
    f.set_points(p); Bu = float(f.modB().mean())
    _F.update(f=f, bri=bri, vmec=v, Bu=Bu, nfp=nfp)      # bri festhalten: sonst raeumt Python es weg und G fehlt
    return _F


def teilchen_u(Bu):
    from simsopt.util.constants import ALPHA_PARTICLE_MASS as M, ALPHA_PARTICLE_CHARGE as Q, FUSION_ALPHA_PARTICLE_ENERGY as E
    vr = Bu / (B0 * L)
    return M, Q, E * vr ** 2, np.sqrt(2 * E / M) * vr, Bu / B0


def geburtsorte(n, rng, f):
    from invers.stufe0_bilanz import sigma_v
    s0 = json.loads(STUFE0.read_text()); A, H = s0["annahmen"], s0["auslegung"]["HTS"]
    rho = np.linspace(1e-3, 0.999, 2000)
    p = ((1 - rho ** 2) ** A["alpha_n"]) ** 2 * sigma_v(H["T0_keV"] * (1 - rho ** 2))
    cdf = np.cumsum(p * 2 * rho); cdf /= cdf[-1]
    out = []; gmax = None
    while sum(len(o) for o in out) < n:
        m = 4 * n
        s = np.interp(rng.random(m), cdf, rho) ** 2
        th = rng.random(m) * 2 * np.pi; ze = rng.random(m) * 2 * np.pi
        stz = np.column_stack([s, th, ze])
        f.set_points(stz); g = 1.0 / f.modB()[:, 0] ** 2
        gmax = gmax or 1.3 * g.max()
        out.append(stz[rng.random(m) * gmax < g])
    return np.concatenate(out)[:n]


def _arbeit(args):
    stz0, vpar, tmax_u, dt_u = args
    from simsopt.field.tracing import trace_particles_boozer, MaxToroidalFluxStoppingCriterion
    F = feld(); M, Q, Eu, vu, ft = teilchen_u(F["Bu"])
    n = len(stz0); erg = np.full((n, 6), np.nan); erg[:, 0] = 0.0
    x, vp = np.array(stz0, float), np.array(vpar, float); aktiv = np.arange(n); t = 0.0
    while t < tmax_u * (1 - 1e-9) and len(aktiv):
        dt = min(dt_u, tmax_u - t)
        res, hits = trace_particles_boozer(F["f"], x[aktiv], vp[aktiv], tmax=dt, mass=M, charge=Q, Ekin=Eu, tol=1e-9,
                                           mode="gc_vac", stopping_criteria=[MaxToroidalFluxStoppingCriterion(1.0)],
                                           forget_exact_path=True)
        bleibt = []
        for j, (r, h) in enumerate(zip(res, hits)):
            i = aktiv[j]
            if len(h) and h[0, 1] < 0:
                erg[i] = [1.0, (t + h[0, 0]) * ft, *h[0, 2:5], h[0, 5] / vu]
            else:
                x[i], vp[i] = r[-1, 1:4], r[-1, 4]; bleibt.append(i)
        aktiv = np.array(bleibt, int); t += dt
    return erg


def rechnen(a):
    import multiprocessing as mp
    F = feld(); M, Q, Eu, vu, ft = teilchen_u(F["Bu"])
    rng = np.random.default_rng(a.saat)
    st = geburtsorte(a.n, rng, F["f"])
    lam = rng.uniform(-1, 1, a.n)
    ordner = AUS / a.name; ordner.mkdir(parents=True, exist_ok=True)
    print(f"Form allein: B_u {F['Bu']:.4f} T, t_phys/t_u {ft:.4f}, {a.n} Alphas, tmax {a.tmax} s, {a.proc} Prozesse",
          flush=True)
    # --weiter: fertige Alphas aus ergebnis.npz uebernehmen (imap haelt die Reihenfolge, gleicher Startwert -> gleiche
    # Startorte), nur den Rest rechnen
    teile, ab = [], 0
    if a.weiter and (ordner / "ergebnis.npz").exists():
        alt = np.load(ordner / "ergebnis.npz")
        ab = int(alt["fertig"]); assert np.allclose(alt["start"], st[:ab]), "Startorte passen nicht zum alten Lauf"
        teile = [alt["erg"]]; print(f"weiter ab Alpha {ab}", flush=True)
    stuecke = [(st[i:i + a.stueck], lam[i:i + a.stueck] * vu, a.tmax / ft, a.dt / ft) for i in range(ab, a.n, a.stueck)]
    t0 = time.time()
    with mp.get_context("spawn").Pool(a.proc) as p:
        for e in p.imap(_arbeit, stuecke):
            teile.append(e)
            fertig = sum(len(t) for t in teile); verl = int(sum(t[:, 0].sum() for t in teile))
            print(f"{time.strftime('%H:%M:%S')} {fertig}/{a.n} fertig, verloren {verl} ({100*verl/fertig:.1f} %), "
                  f"{time.time()-t0:.0f} s", flush=True)
            np.savez(ordner / "ergebnis.npz", start=st[:fertig], lam=lam[:fertig], erg=np.concatenate(teile),
                     tmax=a.tmax, L=L, B0=B0, fertig=fertig, koordinaten="boozer")
    (ordner / "FERTIG").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))


def vergleich():
    """Spulenfeld gegen Form allein: Zahlen (daten/alpha_vergleich.json) und Bild DE/EN. Laeuft in .venv."""
    import shutil
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from stellarator.alpha_auswertung import abbrems, energie_anteil
    root = Path(__file__).resolve().parents[1]
    tau, Ec, E0, Pa = abbrems()
    laeufe = {"spulen": AUS / "hts_1gw" / "ergebnis.npz", "form": AUS / "form_allein" / "ergebnis.npz"}
    z = {}
    for k, p in laeufe.items():
        d = np.load(p); e = d["erg"]; lam = d["lam"]; n = len(e); v = e[:, 0] == 1; t = e[v, 1]
        ef = float(energie_anteil(t, tau, Ec, E0).sum() / n)
        z[k] = dict(n=n, verloren=int(v.sum()), anteil=float(v.mean()), fehler=float(np.sqrt(v.mean() * (1 - v.mean()) / n)),
                    prompt_1ms=int((t < 1e-3).sum()), gefangen_anteil=float((np.abs(lam[v]) < 0.3).mean()) if v.any() else 0.0,
                    energie_anteil=ef, energie_MW=ef * Pa, t=np.sort(t).tolist())
    z["spulen_anteil_an_verlust"] = 1 - z["form"]["anteil"] / z["spulen"]["anteil"]
    aus = {k: ({kk: vv for kk, vv in v.items() if kk != "t"} if isinstance(v, dict) else v) for k, v in z.items()}
    aus["erwartung_vorher"] = "Form allein < 1 % (Landreman & Paul 2022: precise QA ohne Verluste in 0,2 s)"
    (root / "stellarator" / "daten" / "alpha_vergleich.json").write_text(json.dumps(aus, indent=1, ensure_ascii=False))
    T = {"de": dict(titel="Woher kommen die Alpha-Verluste? Feld der Spulen gegen Feld der Plasmaform allein",
                    spulen="Feld der 16 Spulen", form="Feld der Plasmaform allein (ohne Spulenfehler)",
                    x="Zeit nach der Geburt [ms]", y="verloren [%]", erw="Erwartung vorher: Form allein < 1 %",
                    b1="verloren", b2="davon in der 1. ms", b3="Heizleistung verloren", b4="davon gefangene",
                    von="von", k1="Spulen", k2="Form allein", ktitel="Kennzahlen (je 1000 Alphas, bis 0,2 s)",
                    fazit="Ergebnis: Die Form hält die Alphas (0,3 %, nur außen geborene, sofort).\n"
                          "Die Verluste von 16,6 % entstehen durch die Ungenauigkeit der Spulen (≈ 98 %)."),
         "en": dict(titel="Where do the alpha losses come from? Coil field versus field of the plasma shape alone",
                    spulen="field of the 16 coils", form="field of the plasma shape alone (no coil errors)",
                    x="time after birth [ms]", y="lost [%]", erw="expectation beforehand: shape alone < 1 %",
                    b1="lost", b2="of which in 1st ms", b3="heating power lost", b4="of which trapped",
                    von="of", k1="coils", k2="shape alone", ktitel="Key figures (per 1000 alphas, up to 0.2 s)",
                    fazit="Result: the shape confines the alphas (0.3 %, only those born far out, immediately).\n"
                          "The 16.6 % losses come from the inaccuracy of the coils (≈ 98 %).")}
    farbe = {"spulen": "#d1495b", "form": "#2a78d6"}
    for sp, s in T.items():
        fig, ax = plt.subplots(1, 2, figsize=(14, 5.6), dpi=120, gridspec_kw=dict(width_ratios=[1.6, 1]))
        tt = np.logspace(-2, np.log10(200), 400)
        for k in ("spulen", "form"):
            t = np.array(z[k]["t"]) * 1e3
            ax[0].plot(tt, [100 * (t <= x).sum() / z[k]["n"] for x in tt], color=farbe[k], lw=2.4, label=s[k])
        ax[0].axhline(1.0, color="#777", ls="--", lw=1); ax[0].text(0.012, 1.4, s["erw"], fontsize=9, color="#555")
        ax[0].set_xscale("log"); ax[0].set_xlabel(s["x"]); ax[0].set_ylabel(s["y"]); ax[0].grid(alpha=0.3, which="both")
        ax[0].legend(loc="upper left"); ax[0].set_title(s["titel"], fontsize=11)
        ax[1].axis("off")
        zeilen = [(s["b1"], *(f"{100*z[k]['anteil']:.1f} ± {100*z[k]['fehler']:.1f} %" for k in ("spulen", "form"))),
                  (s["b2"], *(f"{z[k]['prompt_1ms']} {s['von']} 1000" for k in ("spulen", "form"))),
                  (s["b4"], *(f"{100*z[k]['gefangen_anteil']:.0f} %" for k in ("spulen", "form"))),
                  (s["b3"], *(f"{z[k]['energie_MW']:.0f} MW" if z[k]['energie_MW'] >= 10 else f"{z[k]['energie_MW']:.1f} MW"
                              for k in ("spulen", "form")))]
        if sp == "de":
            zeilen = [(r[0], *(x.replace(".", ",") for x in r[1:])) for r in zeilen]
        tab = ax[1].table(cellText=[list(r) for r in zeilen], colLabels=["", s["k1"], s["k2"]], loc="center",
                          cellLoc="center", colWidths=[0.46, 0.27, 0.27])
        tab.auto_set_font_size(False); tab.set_fontsize(10); tab.scale(1, 2.2)
        for (r, c), zelle in tab.get_celld().items():
            zelle.set_edgecolor("#cccccc")
            if r == 0 and c > 0:
                zelle.set_text_props(color="white", weight="bold"); zelle.set_facecolor(farbe["spulen" if c == 1 else "form"])
            if c == 0:
                zelle.set_text_props(ha="left"); zelle.PAD = 0.04
        ax[1].set_title(s["ktitel"], fontsize=11)
        fig.text(0.5, -0.04, s["fazit"], ha="center", fontsize=10.5, color="#2b2b2b")
        fig.text(0.99, -0.08, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e", ha="right")
        name = "alpha_vergleich.png" if sp == "de" else "alpha_vergleich_en.png"
        fig.savefig(root / "docs" / "bilder" / name, bbox_inches="tight"); plt.close(fig)
        shutil.copy(root / "docs" / "bilder" / name, root / "bericht" / "projektbericht" / "bilder" / name)
    print(json.dumps(aus, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("was", choices=["rechnen", "test", "vergleich"])
    ap.add_argument("--name", default="form_allein")
    ap.add_argument("--weiter", action="store_true", help="abgebrochenen Lauf fortsetzen")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--tmax", type=float, default=0.2)
    ap.add_argument("--proc", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--stueck", type=int, default=20)
    ap.add_argument("--saat", type=int, default=20261101)
    ap.add_argument("--dt", type=float, default=2e-3)
    a = ap.parse_args()
    if a.was == "test":
        t0 = time.time(); F = feld(); M, Q, Eu, vu, ft = teilchen_u(F["Bu"])
        print(f"Feld {time.time()-t0:.0f} s, B_u {F['Bu']:.4f}, t_phys/t_u {ft:.4f}")
        rng = np.random.default_rng(1); st = geburtsorte(8, rng, F["f"])
        t0 = time.time(); e = _arbeit((st, rng.uniform(-1, 1, 8) * vu, 2e-3 / ft, 2e-3 / ft))
        print(f"8 Alphas bis 2 ms: {time.time()-t0:.0f} s, verloren {int(e[:, 0].sum())}")
    elif a.was == "vergleich":
        vergleich()
    else:
        rechnen(a)


if __name__ == "__main__":
    main()
