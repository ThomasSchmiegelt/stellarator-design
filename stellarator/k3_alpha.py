"""k3_alpha.py -- K3: Alphateilchen (3,5 MeV) im Spulenfeld des Kandidaten in voller Groesse.  KI-generiert (Claude Sonnet 5.5, 2026-11-13).
Erwartung: sim/kandidat/erwartung/K3.md (nicht aendern). Eingabe: sim/kandidat/kandidat.json.
Aufruf (Projektordner):  .venv-opt/bin/python -m stellarator.k3_alpha [--test] [--n 400] [--tmax 0.2] [--proc 6] [--ohne-vmec] [--ohne-bahnen] [--weiter]
Verfahren: Fuehrungszentrumsbahnen wie stellarator/alpha_bahnen.py (stossfrei, gc_vac), Spulen = biot_savart aus kandidat.json, Plasmarand s = 1 aus dem wout.
Start: s = 0,25 und 0,5, Winkel theta, phi gleichverteilt, v_par/v gleichverteilt (Erwartung K3). Groesse: R0, B0 aus kandidat.json (rho_L/a ueber v_u wie alpha_bahnen).
Zweiter Lauf im VMEC-Feld (Boozer, stellarator/alpha_form.py) mit gleichen Zahlen: Vergleich "Spulenfeld gegen VMEC-Feld" (Erwartung +-50 %).
Ausgabe: sim/kandidat/K3/ (--test: sim/kandidat/K3/test/): spulen.npz, vmec.npz (je Zwischenstand, --weiter setzt fort), auswertung.json, lastkarte_alpha.npz, bilder/, ERGEBNIS.md erst am Ende."""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--test", action="store_true"); ap.add_argument("--n", type=int, default=None); ap.add_argument("--tmax", type=float, default=None)
ap.add_argument("--proc", type=int, default=None); ap.add_argument("--stueck", type=int, default=None); ap.add_argument("--saat", type=int, default=20261113)
ap.add_argument("--ohne-vmec", action="store_true"); ap.add_argument("--ohne-bahnen", action="store_true"); ap.add_argument("--weiter", action="store_true")
ap.add_argument("--h", type=float, default=0.02, help="Gitterweite Randklassifikator (Einheitsgeometrie). Speicher je Prozess: h 0,02 etwa 1,6 GB, 0,016 etwa 3 GB, 0,012 etwa 7 GB (gemessen, Form ist hoch: Z bis 0,81)")
A = ap.parse_args()
if A.n is None: A.n = 6 if A.test else 400
if A.tmax is None: A.tmax = 0.002 if A.test else 0.2
if A.proc is None: A.proc = 2 if A.test else 4
if A.stueck is None: A.stueck = 3 if A.test else 20
K = json.loads((P / "sim/kandidat/kandidat.json").read_text())
P1 = json.loads((P / K["k2"] / "P1.json").read_text())
OUT = P / "sim/kandidat/K3" / ("test" if A.test else "lauf"); OUT.mkdir(parents=True, exist_ok=True)
os.environ.update(ALPHA_SPULEN=str(P / K["biot_savart"]), ALPHA_WOUT=str(Path(K["wout"]).expanduser()), ALPHA_STUFE0=str(P / P1["quellen"]["bilanz"]),
                  ALPHA_AUS=str(OUT), ALPHA_R0U=repr(P1["R0_klein_wout_m_je_einheit"]), ALPHA_R0=repr(K["R0_m"]), ALPHA_B0=repr(K["B0_T"]),
                  ALPHA_AUTO_GRENZEN="1", ALPHA_H=repr(A.h), OMP_NUM_THREADS="1", JAX_PLATFORMS="cpu")
sys.path.insert(0, str(P))
import stellarator.alpha_bahnen as ab        # noqa: E402  (liest die Umgebungsvariablen)
S_LISTE = (0.25, 0.5)
now = lambda: time.strftime("%F %T")


def starts(rng, w):
    """je Flaeche A.n Startpunkte (x,y,z), Boozer-Start (s,theta,zeta) und v_par/v; gleiche Zufallszahlen fuer beide Felder."""
    xs, stz, lam, sid = [], [], [], []
    for s in S_LISTE:
        th = rng.random(A.n) * 2 * np.pi; ph = rng.random(A.n) * 2 * np.pi; la = rng.uniform(-1, 1, A.n)
        x, _ = ab.vmec_punkt(w, np.full(A.n, s), th, ph)
        xs.append(x); stz.append(np.column_stack([np.full(A.n, s), th, ph])); lam.append(la); sid.append(np.full(A.n, s))
    return np.concatenate(xs), np.concatenate(stz), np.concatenate(lam), np.concatenate(sid)


def lauf_feld(name, arbeit, x0, lam, vu, ft):
    """gleiche Pool-Logik wie alpha_bahnen.rechnen; Zwischenstand je Stueck, --weiter ueberspringt Fertiges."""
    import multiprocessing as mp
    datei = OUT / f"{name}.npz"; teile = []; ab_ = 0
    if A.weiter and datei.exists():
        alt = np.load(datei); ab_ = int(alt["fertig"]); teile = [alt["erg"]]; print(f"{name}: weiter ab {ab_}", flush=True)
    n = len(x0); stuecke = [(x0[i:i + A.stueck], lam[i:i + A.stueck] * vu, A.tmax / ft, min(2e-3, A.tmax) / ft) for i in range(ab_, n, A.stueck)]
    t0 = time.time()
    with mp.get_context("spawn").Pool(A.proc) as p:
        for e in p.imap(arbeit, stuecke):
            teile.append(e); fertig = sum(len(t) for t in teile); verl = int(sum(t[:, 0].sum() for t in teile))
            print(f"{now()} {name} {fertig}/{n}, verloren {verl}, {time.time() - t0:.0f} s", flush=True)
            np.savez(datei, erg=np.concatenate(teile), fertig=fertig, n=n, tmax=A.tmax)
    return np.load(datei)["erg"], time.time() - t0


def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def achse(w, ph):
    nfp = w["nfp"]
    R = sum(w["raxis_cc"][k] * np.cos(k * nfp * ph) for k in range(len(w["raxis_cc"])))
    Z = -sum(w["zaxis_cs"][k] * np.sin(k * nfp * ph) for k in range(len(w["zaxis_cs"])))
    return R, Z


def main():
    t0 = now(); w = ab.wout(); from simsopt import load
    Bu = ab.achsfeld(load(str(ab.SPULEN)), w); M, Q, Eu, vu, ft = ab.teilchen_u(Bu)
    rho = M * vu / (Q * Bu); a_u = P1["a_klein"]
    print(f"K3 Start {t0}{' (Test)' if A.test else ''}: B_u {Bu:.4f} T, rho_L/a {rho / a_u:.4f}, L {ab.L:.3f}, n je Flaeche {A.n}, tmax {A.tmax} s, {A.proc} Prozesse", flush=True)
    x0, stz, lam, sid = starts(np.random.default_rng(A.saat), w)
    res = {}
    erg_c, dt_c = lauf_feld("spulen", ab._arbeit, x0, lam, vu, ft); res["spulen"] = (erg_c, dt_c)
    if not A.ohne_vmec:
        import stellarator.alpha_form as af
        Fv = af.feld(); _, _, _, vu_v, ft_v = af.teilchen_u(Fv["Bu"])
        erg_v, dt_v = lauf_feld("vmec", af._arbeit, stz, lam, vu_v, ft_v); res["vmec"] = (erg_v, dt_v)
    aus = {"start": t0, "n_je_flaeche": A.n, "tmax_s": A.tmax, "test": A.test, "rho_L_durch_a": rho / a_u, "B_u_T": Bu, "R0_m": K["R0_m"], "B0_T": K["B0_T"], "L": ab.L,
           "klassifikator_h": A.h, "stueck": A.stueck, "felder": {}}
    for name, (erg, dt) in res.items():
        f = {"laufzeit_s": dt, "flaechen": []}
        for s in S_LISTE:
            m = np.isclose(sid, s); v = erg[m, 0] == 1; k = int(v.sum()); lo, hi = wilson(k, int(m.sum()))
            f["flaechen"].append({"s": s, "n": int(m.sum()), "verloren": k, "anteil": k / m.sum(), "ci95": [lo, hi],
                                  "t_verlust_median_s": float(np.median(erg[m, 1][v])) if k else None})
        aus["felder"][name] = f
    # Wandtreffer (nur Spulenfeld) -> Lastkarte (theta um die Achse, phi innerhalb einer Periode), fuer K6/K7
    e = erg_c[erg_c[:, 0] == 1]; nfp = w["nfp"]
    if len(e):
        X = e[:, 2:5]; ph = np.arctan2(X[:, 1], X[:, 0]); Ra, Za = achse(w, ph); Ra, Za = Ra * ab.L, Za * ab.L
        th = np.arctan2(X[:, 2] - Za, np.hypot(X[:, 0], X[:, 1]) - Ra)
        H, pe, te = np.histogram2d(np.mod(ph, 2 * np.pi / nfp), np.mod(th, 2 * np.pi), bins=(24, 24), range=[[0, 2 * np.pi / nfp], [0, 2 * np.pi]])
        np.savez(OUT / "lastkarte_alpha.npz", H=H, phi_kanten=pe, theta_kanten=te, treffer_xyz_m=X, s_start=sid[erg_c[:, 0] == 1], t_s=e[:, 1], nfp=nfp)
        je_phi = H.sum(1); aus["wandtreffer"] = {"n": int(len(e)), "phi_bins_je_periode": 24, "belegte_phi_bins": int((je_phi > 0).sum()),
                                                  "anteil_in_staerksten_3_phi_bins": float(np.sort(je_phi)[-3:].sum() / je_phi.sum()), "quelle": "lastkarte_alpha.npz"}
    (OUT / "auswertung.json").write_text(json.dumps(aus, indent=1, default=float))
    if not A.ohne_bahnen:
        from types import SimpleNamespace
        ab.bahnen(SimpleNamespace(saat=A.saat, k=4 if A.test else 12, tbahn=2e-5 if A.test else 2e-4, name=OUT.name + "_bahnen")); bild_baustein()
    from stellarator.k3_bericht import schreibe
    schreibe(OUT, A.test, aus, t0, now()); print("K3 Ende", now(), flush=True)


def bild_baustein():
    """Bahnen -> VTK (Polylinien + Rand) in video/bausteine/K3/ (Test: im Ausgabeordner)."""
    d = np.load(OUT / (OUT.name + "_bahnen") / "bahnen.npz"); ziel = OUT / "baustein" if A.test else P / "video/bausteine/K3"; ziel.mkdir(parents=True, exist_ok=True)
    pts, lin, verl = [], [], []
    for k in [x for x in d.files if x.startswith("b")]:
        b = d[k]; i0 = len(pts); pts += [tuple(r[1:4]) for r in b]; lin.append(list(range(i0, i0 + len(b))))
    with open(ziel / "alpha_bahnen.vtk", "w") as f:
        f.write("# vtk DataFile Version 3.0\nKI-generiert K3 Alphabahnen (m)\nASCII\nDATASET POLYDATA\n")
        f.write(f"POINTS {len(pts)} float\n" + "\n".join(f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in pts) + "\n")
        f.write(f"LINES {len(lin)} {sum(len(l) + 1 for l in lin)}\n" + "\n".join(str(len(l)) + " " + " ".join(map(str, l)) for l in lin) + "\n")
    np.savez(ziel / "alpha_bahnen_verloren.npz", verloren=d["verloren"], lam=d["lam"])


if __name__ == "__main__":
    main()
