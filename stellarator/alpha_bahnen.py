"""alpha_bahnen.py — Bahnen der Fusions-Alphas (3,5 MeV) im Feld der eigenen Spulen (1-GW-Auslegung, HTS).

  .venv-opt/bin/python -m stellarator.alpha_bahnen rechnen --n 1000 --tmax 0.2 --proc 7
  .venv-opt/bin/python -m stellarator.alpha_bahnen bahnen --k 12          # wenige Bahnen mit vollem Weg (Video)
  .venv-opt/bin/python -m stellarator.alpha_bahnen auswerten

Physik: Fuehrungszentrum im Vakuumfeld (simsopt, mode gc_vac, C++), stossfrei. Das Feld kommt aus den Spulen der
Stufe 2 (sim/invers/qa_nfp2_A45_spulen_mittel/biot_savart.json), die Plasmaform aus Stufe 1 (wout). Ein Alpha gilt als
verloren, sobald sein Fuehrungszentrum die letzte geschlossene Flaeche (VMEC-Rand, s = 1) verlaesst. Gerechnet wird bis
zur Abbremszeit (0,2 s, siehe plasma_waerme.py): was bis dahin nicht verloren ist, hat seine Energie abgegeben.

Skalierung: Spulen und Form liegen bei R0 = 1,03 m. Stossfreie Fuehrungszentrumsbahnen haengen nur von rho_L/a ab.
Statt die Spulen zu vergroessern, wird in der Einheitsgeometrie mit v_u = v * B_u / (B0 * L) gerechnet
(L = 10,4/1,029, B0 = 6,5 T, B_u = Achsfeld der Einheitsspulen). Dann ist rho_L/a = 0,018 wie in der Anlage, und
t_phys = t_u * B_u / B0. Orte werden fuer die Ausgabe mit L auf die Anlage hochgerechnet.

Startorte: Geburtsprofil wie die Fusionsleistung (n ~ (1-rho^2)^0,5, T ~ 1-rho^2, Bosch-Hale), Winkel gleichverteilt
im Volumen (Verwerfung nach der Jacobi-Determinante aus dem wout), Richtung isotrop (v_par/v gleichverteilt).
Ausgabe sim/alpha/<name>/: ergebnis.npz, bahnen.npz; Bilder docs/bilder/alpha_*.png.
"""
import argparse
import json
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")       # simsopt nutzt OpenMP; je Prozess ein Faden
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPULEN = ROOT / "sim" / "invers" / "qa_nfp2_A45_spulen_mittel" / "biot_savart.json"
WOUT = ROOT / "sim" / "invers" / "qa_nfp2_A45" / "wout_qa_nfp2_A45.nc"
STUFE0 = ROOT / "sim" / "invers" / "qa_nfp2_A45_1GW" / "bilanz.json"
AUS = ROOT / "sim" / "alpha"
R0_U = 1.0294040771781494
R0, B0 = 10.4, 6.5
L = R0 / R0_U

_F = {}


def wout():
    from netCDF4 import Dataset
    with Dataset(str(WOUT)) as w:
        d = {k: np.array(w[k][:]) for k in ("rmnc", "zmns", "gmnc", "xm", "xn", "xm_nyq", "xn_nyq", "raxis_cc", "zaxis_cs")}
        d["nfp"] = int(w["nfp"][:]); d["ns"] = int(w["ns"][:])
    return d


def achsfeld(bs, w):
    phi = np.linspace(0, 2 * np.pi, 400, endpoint=False); n = w["nfp"]
    R = sum(w["raxis_cc"][k] * np.cos(k * n * phi) for k in range(len(w["raxis_cc"])))
    Z = -sum(w["zaxis_cs"][k] * np.sin(k * n * phi) for k in range(len(w["zaxis_cs"])))
    bs.set_points(np.column_stack([R * np.cos(phi), R * np.sin(phi), Z]))
    return float(np.linalg.norm(bs.B(), axis=1).mean())


def feld():
    """Interpoliertes Spulenfeld + Randklassifikator (je Prozess einmal)."""
    if "f" in _F:
        return _F
    from simsopt import load
    from simsopt.field import InterpolatedField
    from simsopt.field.tracing import SurfaceClassifier
    from simsopt.geo import SurfaceRZFourier
    w = wout(); bs = load(str(SPULEN)); Bu = achsfeld(bs, w)
    f = InterpolatedField(bs, 4, [0.45, 1.45, 50], [0, 2 * np.pi / w["nfp"], 48], [0.0, 0.55, 30], True,
                          nfp=w["nfp"], stellsym=True)
    rand = SurfaceRZFourier.from_wout(str(WOUT), s=1.0, range="full torus", nphi=64, ntheta=32)
    # Klassifikator: h = 0,02 (Einheitsgeometrie); h = 0,01 belegt etwa 9 GB je Prozess
    _F.update(f=f, sc=SurfaceClassifier(rand, h=0.02, p=2), Bu=Bu, w=w, rand=rand)
    return _F


def teilchen_u(Bu):
    from simsopt.util.constants import ALPHA_PARTICLE_MASS as M, ALPHA_PARTICLE_CHARGE as Q, FUSION_ALPHA_PARTICLE_ENERGY as E
    vr = Bu / (B0 * L)
    return M, Q, E * vr ** 2, np.sqrt(2 * E / M) * vr, Bu / B0        # Masse, Ladung, E_u, v_u, t_phys/t_u


def vmec_punkt(w, s, th, ph):
    """Ort und |sqrt(g)| an (s, theta, phi); rmnc/zmns auf vollem, gmnc auf halbem Gitter, linear in s."""
    ns = w["ns"]; sf = np.linspace(0, 1, ns); sh = (np.arange(1, ns) - 0.5) / (ns - 1)
    rm = np.array([np.interp(s, sf, w["rmnc"][:, j]) for j in range(w["rmnc"].shape[1])])
    zm = np.array([np.interp(s, sf, w["zmns"][:, j]) for j in range(w["zmns"].shape[1])])
    gm = np.array([np.interp(s, sh, w["gmnc"][1:, j]) for j in range(w["gmnc"].shape[1])])
    a = np.outer(w["xm"], th) - np.outer(w["xn"], ph)
    R = (rm * np.cos(a)).sum(0); Z = (zm * np.sin(a)).sum(0)
    an = np.outer(w["xm_nyq"], th) - np.outer(w["xn_nyq"], ph)
    g = np.abs((gm * np.cos(an)).sum(0))
    return np.column_stack([R * np.cos(ph), R * np.sin(ph), Z]), g


def geburtsorte(n, rng, w):
    from invers.stufe0_bilanz import sigma_v
    s0 = json.loads(STUFE0.read_text()); A, H = s0["annahmen"], s0["auslegung"]["HTS"]
    rho = np.linspace(1e-3, 0.999, 2000)
    p = ((1 - rho ** 2) ** A["alpha_n"]) ** 2 * sigma_v(H["T0_keV"] * (1 - rho ** 2))     # ~ n^2 <sv>
    # in s = rho^2 ist dV ~ ds -> Dichte in s proportional p; Winkel per Verwerfung nach sqrt(g)
    cdf = np.cumsum(p * 2 * rho); cdf /= cdf[-1]
    out = []; gmax = None
    while sum(len(o) for o in out) < n:
        m = 4 * n
        r = np.interp(rng.random(m), cdf, rho); s = r ** 2
        th = rng.random(m) * 2 * np.pi; ph = rng.random(m) * 2 * np.pi
        x, g = vmec_punkt(w, s, th, ph)
        gmax = gmax or 1.3 * g.max()
        ok = rng.random(m) * gmax < g
        out.append(np.column_stack([x[ok], s[ok], th[ok], ph[ok]]))
    return np.concatenate(out)[:n]


def _arbeit(args):
    """Ein Stueck Alphas bis tmax_u, in Zeitabschnitten: simsopt behaelt sonst den ganzen Weg im Speicher
    (5 Alphas ueber 5 ms = 0,6 GB). Jeder Abschnitt startet am Endzustand (Ort, v_par) des vorigen."""
    x0, vpar, tmax_u, dt_u = args
    from simsopt.field.tracing import trace_particles, LevelsetStoppingCriterion
    F = feld(); M, Q, Eu, vu, ft = teilchen_u(F["Bu"])
    n = len(x0); erg = np.full((n, 6), np.nan); erg[:, 0] = 0.0
    x, vp = np.array(x0, float), np.array(vpar, float); aktiv = np.arange(n); t = 0.0
    while t < tmax_u * (1 - 1e-9) and len(aktiv):
        dt = min(dt_u, tmax_u - t)
        res, hits = trace_particles(F["f"], x[aktiv], vp[aktiv], tmax=dt, mass=M, charge=Q, Ekin=Eu, tol=1e-9,
                                    mode="gc_vac", stopping_criteria=[LevelsetStoppingCriterion(F["sc"].dist)],
                                    forget_exact_path=True)
        bleibt = []
        for j, (r, h) in enumerate(zip(res, hits)):
            i = aktiv[j]
            if len(h) and h[0, 1] < 0:
                erg[i] = [1.0, (t + h[0, 0]) * ft, *(h[0, 2:5] * L), h[0, 5] / vu]
            else:
                x[i], vp[i] = r[-1, 1:4], r[-1, 4]; bleibt.append(i)
        aktiv = np.array(bleibt, int); t += dt
    return erg


def rechnen(a):
    import multiprocessing as mp
    from simsopt import load
    w = wout(); Bu = achsfeld(load(str(SPULEN)), w); F = dict(Bu=Bu, w=w)
    M, Q, Eu, vu, ft = teilchen_u(Bu)
    rng = np.random.default_rng(a.saat)
    st = geburtsorte(a.n, rng, w)
    lam = rng.uniform(-1, 1, a.n)
    ordner = AUS / a.name; ordner.mkdir(parents=True, exist_ok=True)
    print(f"B_u {F['Bu']:.4f} T, rho_L/a {M * vu / (Q * F['Bu']) / 0.22876:.4f}, t_phys/t_u {ft:.4f}, {a.n} Alphas, "
          f"tmax {a.tmax} s, {a.proc} Prozesse", flush=True)
    stuecke = [(st[i:i + a.stueck, :3], lam[i:i + a.stueck] * vu, a.tmax / ft, a.dt / ft) for i in range(0, a.n, a.stueck)]
    t0 = time.time(); teile = []
    with mp.get_context("spawn").Pool(a.proc) as p:          # fork nach OpenMP-Start blockiert
        for k, e in enumerate(p.imap(_arbeit, stuecke)):
            teile.append(e)
            fertig = sum(len(t) for t in teile); verl = int(sum(t[:, 0].sum() for t in teile))
            print(f"{time.strftime('%H:%M:%S')} {fertig}/{a.n} fertig, verloren {verl} ({100*verl/fertig:.1f} %), "
                  f"{time.time()-t0:.0f} s", flush=True)
            np.savez(ordner / "ergebnis.npz", start=st[:fertig], lam=lam[:fertig], erg=np.concatenate(teile),
                     tmax=a.tmax, L=L, B0=B0, fertig=fertig)
    (ordner / "FERTIG").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))


def bahnen(a):
    """Wenige Alphas mit vollem Weg fuer Bilder und Video (kurze Zeit)."""
    from simsopt.field.tracing import trace_particles, LevelsetStoppingCriterion
    F = feld(); M, Q, Eu, vu, ft = teilchen_u(F["Bu"])
    rng = np.random.default_rng(a.saat + 1)
    st = geburtsorte(a.k, rng, F["w"])
    lam = np.linspace(-0.95, 0.95, a.k); rng.shuffle(lam)
    res, hits = trace_particles(F["f"], st[:, :3], lam * vu, tmax=a.tbahn / ft, mass=M, charge=Q, Ekin=Eu, tol=1e-9,
                                mode="gc_vac", stopping_criteria=[LevelsetStoppingCriterion(F["sc"].dist)])
    ordner = AUS / a.name; ordner.mkdir(parents=True, exist_ok=True)
    d = {f"b{i}": np.column_stack([r[:, 0] * ft, r[:, 1:4] * L, r[:, 4] / vu]) for i, r in enumerate(res)}
    rand = F["rand"].gamma() * L
    np.savez(ordner / "bahnen.npz", lam=lam, rand=rand, verloren=np.array([len(h) > 0 and h[0, 1] < 0 for h in hits]), **d)
    print("Bahnen:", {k: len(v) for k, v in d.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("was", choices=["rechnen", "bahnen", "auswerten"])
    ap.add_argument("--name", default="hts_1gw")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--tmax", type=float, default=0.2)
    ap.add_argument("--proc", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--stueck", type=int, default=20)
    ap.add_argument("--saat", type=int, default=20261101)
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--tbahn", type=float, default=2e-4)
    ap.add_argument("--dt", type=float, default=2e-3, help="Zeitabschnitt [s] (Speicher)")
    a = ap.parse_args()
    if a.was == "rechnen":
        rechnen(a)
    elif a.was == "bahnen":
        bahnen(a)
    else:
        from stellarator.alpha_auswertung import auswerten
        auswerten(a.name)


if __name__ == "__main__":
    main()
