"""submodell.py — Stufe 2 der Festigkeit: einzelne Spule fein rechnen (Submodell-Technik, Nutzeridee 2026-11-04).

  .venv/bin/python -m stellarator.submodell <studie> <nr> [--spule K] [--fein F] [--n_wand W] [--n_wp Q] [--n_verguss V]

Stufe 1 ist der vorhandene Punkt (struktur.vtu). Ohne --spule wird die Spule mit dem höchsten Stahl-p99 genommen.
Die Spule wird einzeln vernetzt: Stationen x F (Spline durch die Bahn), Zellen über die Wand frei wählbar. Last: J x B mit dem
Feld aller Spulen. Rand: an den Verbinderflächen die Verschiebung aus Stufe 1 (je Knoten interpoliert), an den Lagern null.
Trick: Die Randverschiebung steht in derselben Knotentabelle kraft.dat wie die Last; Wickelpaket- und Randknoten sind getrennt.
Kontrolle: F = 1 mit gleicher Querteilung muss Stufe 1 auf dieser Spule treffen.
Ergebnis: sim/submodell/<studie>_<nr>_s<K>_F<F>_w<W>_q<Q>/ (ergebnis.json, struktur.vtu).
"""
import argparse
import copy
import json
import shutil
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline, RegularGridInterpolator
from scipy.spatial import cKDTree

from . import hexmodell as hm, kopplung as kp, spulen as sp

ROOT = Path(__file__).resolve().parents[1]
RAND_M = 0.5        # Elemente näher als das an einer Randfläche zählen nicht in "ohne Rand" (Saint-Venant)


def p99(v, V):
    o = np.argsort(v); c = np.cumsum(V[o]) / V.sum()
    return float(v[o][min(np.searchsorted(c, 0.99), len(v) - 1)])


def verfeinern(s, w, F):
    """Spule und Wände auf N*F Stationen; Station i alt = Station i*F neu."""
    N = len(s.punkte); t = np.arange(N + 1)
    q = np.arange(N * F) / F
    s2 = copy.copy(s)
    s2.punkte = CubicSpline(t, np.vstack([s.punkte, s.punkte[:1]]), bc_type="periodic")(q) if F > 1 else s.punkte.copy()
    w2 = {k: np.interp(q, t, np.r_[v, v[0]]) for k, v in w.items()}
    return s2, w2


def kante(X):
    """Lage 0..1 der Knoten quer über die Fläche (Mittel über die Stationen)."""
    d = np.linalg.norm(np.diff(X, axis=1), axis=2).mean(0)
    return np.r_[0, np.cumsum(d)] / d.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("studie"); ap.add_argument("nr", type=int)
    ap.add_argument("--spule", type=int, default=-1); ap.add_argument("--fein", type=int, default=1)
    ap.add_argument("--n_wand", type=int, default=0); ap.add_argument("--n_wp", type=int, default=0)
    ap.add_argument("--n_verguss", type=int, default=0)
    a = ap.parse_args()
    po = kp.ordner(a.studie) / "punkte" / f"{a.nr:04d}"
    kp.plasma_laden(kp.ordner(a.studie))
    p = json.loads((po / "param.json").read_text()); geo = json.loads((po / "geometrie.json").read_text())
    netz, spulen, br, ho, wp, I, _, _, W = kp.struktur_netz(p, po, geo)

    import pyvista as pv
    g = pv.read(po / "struktur.vtu")
    assert g.n_points == len(netz.X), "Netz stimmt nicht mit struktur.vtu überein"
    U1 = np.asarray(g.point_data["verschiebung_m"]); vm1 = np.asarray(g.cell_data["vonmises_MPa"])
    V1 = hm.elementvolumen(netz.X, netz.hexa)
    stahl = netz.mat == 3
    werte = {int(k): p99(vm1[stahl & (netz.spule == k)], V1[stahl & (netz.spule == k)]) for k in range(len(spulen))}
    k = a.spule if a.spule >= 0 else max(werte, key=werte.get)
    print("Spule", k, "Stufe 1 p99", round(werte[k]), "MPa; höchste fünf", sorted(werte.items(), key=lambda x: -x[1])[:5], flush=True)

    q1 = dict(hm.QUER); A1 = sum([q1["n_wand"], q1["n_verguss"], q1["n_wp"], q1["n_verguss"], q1["n_wand"]])
    q2 = {"n_wand": a.n_wand or q1["n_wand"], "n_verguss": a.n_verguss or q1["n_verguss"], "n_wp": a.n_wp or q1["n_wp"]}
    A2 = sum([q2["n_wand"], q2["n_verguss"], q2["n_wp"], q2["n_verguss"], q2["n_wand"]])
    F = a.fein
    s2, w2 = verfeinern(spulen[k], W[k], F)
    n2 = hm.baue_netz([s2], br, ho, [w2], kp.FEST["verguss_m"], p["r_lager_m"], 0, 1, q=q2)
    if n2.info["elemente_negativ"]:
        raise SystemExit(f"{n2.info['elemente_negativ']} negative Elemente im Submodell")
    N1, N2 = len(spulen[k].punkte), len(s2.punkte)
    versatz = sum(len(s.punkte) * (A1 + 1) ** 2 for s in spulen[:k])
    id1 = versatz + np.arange(N1 * (A1 + 1) ** 2).reshape(N1, A1 + 1, A1 + 1)
    id2 = np.arange(N2 * (A2 + 1) ** 2).reshape(N2, A2 + 1, A2 + 1)
    assert np.allclose(netz.X[id1[:, 0, 0]], netz.X[id1[:, 0, 0]])

    halb = int(p.get("verbinder_halb", kp.FEST["verbinder_halb"]))
    Urand = {}; quads = []; flaechen = 0
    eltern = {}
    for v in netz.info["verbinder"]:
        if not v["ok"] or k not in (v["k"], v["m"]):
            continue
        i0, seite = (v["i0"], v["fk"]) if v["k"] == k else (v["j0"], v["fm"])
        d = np.arange(-halb, halb + 1)
        G1 = hm._flaeche(id1[(i0 + d) % N1], seite, A1)                       # (S+1, A1+1)
        d2 = np.arange(-halb * F, halb * F + 1)
        G2 = hm._flaeche(id2[(i0 * F + d2) % N2], seite, A2)
        u = kante(netz.X[G1]); u2 = kante(n2.X[G2])
        f = RegularGridInterpolator((d.astype(float), u), U1[G1], bounds_error=False, fill_value=None)
        S, T = np.meshgrid(d2 / F, u2, indexing="ij")
        Uk = f(np.c_[S.ravel(), T.ravel()])
        for n_, x in zip(G2.ravel(), Uk):
            Urand[int(n_)] = x
        quads.append(np.stack([G2[:-1, :-1], G2[1:, :-1], G2[1:, 1:], G2[:-1, 1:]], -1).reshape(-1, 4))
        flaechen += 1
    rand_k = np.array(sorted(Urand)); rand_u = np.array([Urand[i] for i in rand_k])
    lager_k = np.unique(n2.lager[:, 1:])
    print("Verbinderflächen", flaechen, "Randknoten", len(rand_k), "Lagerknoten", len(lager_k), flush=True)

    # Eltern der Randvierecke: Element mit allen vier Knoten
    Q = np.vstack(quads) if quads else np.zeros((0, 4), int)
    vor = {}
    for e, h in enumerate(n2.hexa):
        for fl in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            vor[tuple(sorted(h[list(fl)]))] = e
    par = np.array([vor[tuple(sorted(x))] for x in Q], int)
    n2.lager = np.vstack([n2.lager, np.c_[par, Q]]) if len(Q) else n2.lager

    # Last: Feld der anderen Spulen (grob) + eigene Spule (fein)
    def fil(s, nf):
        t, n, b = sp.rahmen(s); u = (np.arange(nf) + 0.5) / nf - 0.5; A_, B_, I_ = [], [], []
        for ua in u:
            for uc in u:
                P = s.punkte + ua * br * n + uc * ho * b
                A_.append(P); B_.append(np.roll(P, -1, 0)); I_.append(np.full(len(P), s.strom / nf ** 2))
        return A_, B_, I_
    A_, B_, I_ = fil(s2, q2["n_wp"])
    for j, s in enumerate(spulen):
        if j != k:
            x = fil(s, 2); A_ += x[0]; B_ += x[1]; I_ += x[2]
    seg = (np.vstack(A_), np.vstack(B_), np.concatenate(I_))
    w = n2.wp_knoten[0]; idx = w.ravel()
    B = sp.biot_savart(n2.X[idx], seg)
    T = np.broadcast_to(n2.stationen_t[0][:, None, None], w.shape + (3,)).reshape(-1, 3)
    f = np.zeros_like(n2.X); f[idx] = spulen[k].strom / (br * ho) * np.cross(T, B)
    wpsel = n2.mat == 1
    Fn = (f[n2.hexa[wpsel]].mean(1) * hm.elementvolumen(n2.X, n2.hexa[wpsel])[:, None]).sum(0)
    assert not (set(rand_k.tolist()) | set(lager_k.tolist())) & set(idx.tolist()), "Randknoten im Wickelpaket"
    tab = f.copy(); tab[lager_k] = 0.0; tab[rand_k] = rand_u

    name = f"{a.studie}_{a.nr:04d}_s{k}_F{F}_w{q2['n_wand']}_q{q2['n_wp']}"
    o = ROOT / "sim" / "submodell" / name; fall = o / "elmer"
    shutil.rmtree(fall, ignore_errors=True); fall.mkdir(parents=True)
    mat = kp.werkstoffe(p)
    hm.schreibe_fall(fall, n2, tab, mat, "mumps")
    so = hm.udf(); c = (fall / "case.sif").read_text()
    for i, ch in ((1, "x"), (2, "y"), (3, "z")):
        c = c.replace(f"  Displacement {i} = Real 0.0\n", f'  Displacement {i} = Variable Time\n    Real Procedure "{so}" "kraft_{ch}"\n')
    (fall / "case.sif").write_text(c)
    print("Knoten", len(n2.X), "Elemente", len(n2.hexa), flush=True)
    t = hm.rechne(fall, 7200)
    U = hm.verschiebung(fall, n2); vm = hm.spannungen(n2, U, mat) / 1e6
    V = hm.elementvolumen(n2.X, n2.hexa); st = n2.mat == 3
    baum = cKDTree(n2.X[np.r_[rand_k, lager_k]])
    dist = baum.query(n2.X[n2.hexa].mean(1))[0]
    innen = st & (dist > RAND_M)
    c1 = stahl & (netz.spule == k)
    b1 = cKDTree(n2.X[np.r_[rand_k, lager_k]]).query(netz.X[netz.hexa[c1]].mean(1))[0] > RAND_M
    wp2 = n2.mat == 1; wp1 = (netz.mat == 1) & (netz.spule == k)
    e = {"studie": a.studie, "nr": a.nr, "spule": k, "fein": F, "quer": q2, "knoten": len(n2.X), "elemente": len(n2.hexa), "elmer_s": t,
         "kraft_netto_MN": float(np.linalg.norm(Fn) / 1e6), "verbinderflaechen": flaechen,
         "stufe1": {"stahl_p99": werte[k], "stahl_p99_ohne_rand": p99(vm1[c1][b1], V1[c1][b1]), "stahl_max": float(vm1[c1].max()),
                    "wp_p99": p99(vm1[wp1], V1[wp1]), "u_max_mm": float(1e3 * np.linalg.norm(U1[np.unique(netz.hexa[c1])], axis=1).max())},
         "submodell": {"stahl_p99": p99(vm[st], V[st]), "stahl_p99_ohne_rand": p99(vm[innen], V[innen]), "stahl_max": float(vm[st].max()),
                       "stahl_max_ohne_rand": float(vm[innen].max()), "wp_p99": p99(vm[wp2], V[wp2]), "u_max_mm": float(1e3 * np.linalg.norm(U, axis=1).max())}}
    (o / "ergebnis.json").write_text(json.dumps(e, indent=1)); print(json.dumps(e, indent=1), flush=True)
    hm.als_vtu(n2, o / "struktur.vtu", {"vonmises_MPa": vm}, {"verschiebung_m": U})
    shutil.rmtree(fall)


if __name__ == "__main__":
    main()
