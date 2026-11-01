"""vorwaermer_stufung.py — lohnt sich eine Zellstufung im Divertor-Vorwaermer? Mit dem CFD-Surrogat statt Literatur.

  .venv/bin/python -m stellarator.vorwaermer_stufung

Modell: Gegenstrom-Zwei-Fluid-TPMS (Gyroid oder Diamond, Wand 0,5 mm), beide Kanalnetze teilen die Zelle, also
gleiches d_h auf beiden Seiten. Laengs des Wegs N = 8 Segmente gleicher Waermeleistung Q/N. Je Segment lokale
Temperaturen, Stoffwerte, Pr und LMTD; Nu und f aus stellarator.tauscher_surrogat (Stufe n144, Nu wahlweise inf).
  gleichmaessig: eine Zelle a fuer alle Segmente
  abgestuft:     je Segment eigene Zelle a_i (Lagrange: min P_i + lam V_i je Segment, lam abgetastet)
Ausserdem frei: Annaeherung am warmen Ende, Kondensatgeschwindigkeit, Durchgaenge der warmen Seite (wie vorwaermer.py).
Netto = Turbinen-Mehrleistung(Annaeherung) - Pumpleistung beider Seiten. Ergebnis: Front Netto ueber Bauvolumen.
Zelle und d_h: d_h(a) aus tauscher_cfd.glatt_kennwerte (t = 0,5 mm), Zellbereich wie im Surrogat (LHS 0,75-1,6 a_std).
"""
import json
import shutil
from pathlib import Path

import numpy as np
from CoolProp.CoolProp import PropsSI

from stellarator import vorwaermer as VW
from stellarator.tauscher_cfd import glatt_kennwerte
from stellarator.tauscher_surrogat import A_STD, Surrogat, laden

ROOT = Path(__file__).resolve().parents[1]
N_SEG = 8


def rechne(S, typ, stufe_nu, Tk, Wk, m_k, literatur=None):
    """literatur: None (Surrogat) oder Faktor k_nu fuer Renon (Gyroid: f * 1,145) im selben Segmentmodell."""
    a_grid = np.geomspace(0.75 * A_STD[typ], 1.6 * A_STD[typ], 14)
    dh = []
    for a in a_grid:
        dh.append(glatt_kennwerte(typ, dict(a=float(a)), 0.5)[2])
    dh = np.array(dh) * 1e-3                                   # m
    cph = PropsSI("C", "P", VW.P_H, "T", 133 + 273.15, "Water")
    m_h = VW.Q / (cph * (VW.T_H_EIN - VW.T_H_AUS))
    cpk = PropsSI("C", "P", VW.P_K, "T", 373.15, "Water")
    dTk = VW.Q / (m_k * cpk)
    app = np.geomspace(0.5, 25, 30)
    v_k = np.geomspace(0.05, 3, 22)
    n_p = np.array([1, 2, 3, 4, 6, 8])
    j = np.arange(N_SEG + 1) / N_SEG
    # Grenztemperaturen je Annaeherung (Index 0 = warmes Ende)
    Th = VW.T_H_EIN - (VW.T_H_EIN - VW.T_H_AUS) * j                          # (N+1)
    Tc = (VW.T_H_EIN - app)[:, None] - dTk * j[None, :]                     # (app, N+1)
    dT = Th[None, :] - Tc
    lmtd = np.where(np.isclose(dT[:, 1:], dT[:, :-1]), dT[:, 1:], (dT[:, :-1] - dT[:, 1:]) / np.log(dT[:, :-1] / dT[:, 1:]))
    Thm = 0.5 * (Th[1:] + Th[:-1]); Tcm = 0.5 * (Tc[:, 1:] + Tc[:, :-1])      # (N), (app, N)
    st = lambda T, p: VW.stoff(float(T), p)
    SH = np.array([st(t, VW.P_H) for t in Thm])                              # (N, 5) r cp mu k pr
    SK = np.array([[st(t, VW.P_K) for t in row] for row in Tcm])             # (app, N, 5)
    # Achsen: app(A) v(V) n(P) a(D) seg(N)
    sh = lambda k: SH[:, k][None, None, None, None, :]
    sk = lambda k: SK[:, :, k][:, None, None, None, :]
    D = dh[None, None, None, :, None]; a5 = a_grid[None, None, None, :, None]
    vk = v_k[None, :, None, None, None]; nn = n_p[None, None, :, None, None]
    Af_k = m_k / (sk(0) * vk)                       # gleiche Kanalnetze -> warme Seite n-mal Querschnitt bei L/n
    Af_h = nn * Af_k
    v_h = m_h / (sh(0) * Af_h)
    re_k = sk(0) * vk * D / sk(2); re_h = sh(0) * v_h * D / sh(2)
    shape = np.broadcast_shapes(re_k.shape, re_h.shape)
    re_k, re_h = np.broadcast_to(re_k, shape), np.broadcast_to(re_h, shape)
    prk, prh = np.broadcast_to(sk(4), shape), np.broadcast_to(sh(4), shape)
    aa = np.broadcast_to(a5, shape)

    def korr(re, pr):
        rc = np.clip(re, 450, 10000)
        if literatur is not None:
            Nu, f = VW.renon(rc, pr)
            return Nu * literatur, f * (VW.GY if typ == "gyroid" else 1.0)
        Nu, f = S(typ, rc.ravel(), pr.ravel(), aa.ravel(), "n144")
        if stufe_nu == "inf":
            Nu = S(typ, rc.ravel(), pr.ravel(), aa.ravel(), "inf")[0]
        return Nu.reshape(shape), f.reshape(shape)

    nu_k, f_k = korr(re_k, prk); nu_h, f_h = korr(re_h, prh)
    ok_re = (re_k >= 450) & (re_k <= 10000) & (re_h >= 450) & (re_h <= 10000)
    U = 1 / (D / (nu_k * sk(3)) + VW.T_WAND / VW.K_WAND + D / (nu_h * sh(3)))
    A = (VW.Q / N_SEG) / (U * lmtd[:, None, None, None, :])
    L = A * D / (4 * Af_k)
    V = A * (2 * D / 4 + VW.T_WAND)
    dp_k = 4 * f_k * L / D * sk(0) * vk ** 2 / 2
    dp_h = 4 * f_h * (L / nn) / D * sh(0) * v_h ** 2 / 2
    P = (dp_k * m_k / sk(0) + dp_h * m_h / sh(0)) / VW.ETA_P
    V = np.where(ok_re, V, np.inf); P = np.where(ok_re, P, np.inf)
    Tein = VW.T_H_EIN - app - dTk
    W = (np.interp(VW.T_H_EIN - app, Tk, Wk) - np.interp(Tein, Tk, Wk)) * (Tein > Tk[0])
    W = W[:, None, None]
    # gleichmaessig: Summe ueber Segmente bei gleicher Zelle -> (A, V, P, D)
    Vg, Pg = V.sum(-1), P.sum(-1)
    gl = dict(V=Vg.ravel(), netto=(W[..., None] - Pg).ravel())
    # abgestuft: je lam je Segment beste Zelle
    lams = np.geomspace(1e1, 1e7, 60)                 # W je m3
    Vs, Ns = [], []
    for lam in lams:
        idx = np.argmin(P + lam * V, axis=3)          # (A, V, P, N)
        Vi = np.take_along_axis(V, idx[:, :, :, None, :], 3)[:, :, :, 0, :].sum(-1)
        Pi = np.take_along_axis(P, idx[:, :, :, None, :], 3)[:, :, :, 0, :].sum(-1)
        Vs.append(Vi.ravel()); Ns.append((W - Pi).ravel())
    ab = dict(V=np.concatenate(Vs), netto=np.concatenate(Ns))
    W_max = float(np.interp(VW.T_H_EIN, Tk, Wk) - np.interp(VW.T_H_EIN - dTk, Tk, Wk))
    return gl, ab, W_max, a_grid, dh


def front(res, Vb):
    m = np.isfinite(res["V"]) & np.isfinite(res["netto"])
    o = np.argsort(res["V"][m]); best = np.maximum.accumulate(res["netto"][m][o])
    return np.interp(Vb, res["V"][m][o], best, left=np.nan)


def main():
    S = Surrogat(laden())
    p_kond, m_k = 0.0247, 1820.0
    Tk, Wk, _ = VW.mehrleistung_kurve(p_kond * 1e5, m_k)
    Vb = np.geomspace(0.3, 300, 200)
    erg = {}
    for typ in ("gyroid", "diamond"):
        for st in ("n144", "inf"):
            gl, ab, W_max, a_grid, dh = rechne(S, typ, st, Tk, Wk, m_k)
            fg, fa = front(gl, Vb), front(ab, Vb)
            e = dict(gleich=fg, gestuft=fa)
            for k, f in list(e.items()):
                f = np.nan_to_num(f, nan=-1e12)
                e[k + "_V"] = {q: (float(Vb[np.argmax(f >= q / 100 * W_max)]) if f[-1] >= q / 100 * W_max else None) for q in (90, 95, 99)}
                e[k + "_50"] = float(np.interp(50, Vb, f) / 1e6) if Vb[-1] >= 50 else None
                e[k + "_10"] = float(np.interp(10, Vb, f) / 1e6)
            erg[f"{typ}_{st}"] = e
            print(f"{typ:8s} Nu-Stufe {st:4s}: W_max {W_max/1e6:.1f} MW | bei 10 m3 gleich {e['gleich_10']:.2f} / gestuft {e['gestuft_10']:.2f} MW"
                  f" | bei 50 m3 {e['gleich_50']:.2f} / {e['gestuft_50']:.2f} MW | V fuer 95 %: {e['gleich_V'][95]} / {e['gestuft_V'][95]} m3")
            print(f"           d_h von {dh[0]*1e3:.2f} bis {dh[-1]*1e3:.2f} mm (a {a_grid[0]:.2f}-{a_grid[-1]:.2f} mm)")
    alt = {}
    for nm, k in (("renon", 1.0), ("renon128", 1.28)):
        gl, ab, W_max, a_grid, dh = rechne(S, "gyroid", "n144", Tk, Wk, m_k, literatur=k)
        alt[nm] = front(gl, Vb)
        print(f"Literatur Renon Gyroid, Nu x {k}: " + " ".join(f"V {v}: {np.interp(v, Vb, alt[nm])/1e6:.2f}" for v in (0.6, 1.0, 2.0)))
    for k, e in erg.items():
        print(f"{k:13s} gleich / gestuft: " + " ".join(f"V {v}: {np.interp(v, Vb, e['gleich'])/1e6:.2f}/{np.interp(v, Vb, e['gestuft'])/1e6:.2f}" for v in (0.6, 1.0, 2.0)))
    out = dict(V=Vb.tolist(), W_max=W_max / 1e6,
               erg={k: {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()} for k, v in erg.items()},
               literatur={k: v.tolist() for k, v in alt.items()})
    (VW.DATEN / "vorwaermer_stufung.json").write_text(json.dumps(out, indent=1))
    for s in ("de", "en"):
        print(bild(Vb, erg, W_max, alt, s))


def bild(Vb, erg, W_max, alt, sprache):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    de = sprache == "de"
    fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
    ax.axhline(W_max / 1e6, color="#52514e", lw=1, ls="--")
    ax.text(0.32, W_max / 1e6 + 0.25, (f"Obergrenze ohne Pumpen: {W_max/1e6:.1f} MW" if de else f"Upper limit without pumping: {W_max/1e6:.1f} MW"),
            color="#52514e", fontsize=9)
    farbe = dict(gyroid="#2a78d6", diamond="#eb6834")
    for typ in ("gyroid", "diamond"):
        c = farbe[typ]; e, ei = erg[f"{typ}_n144"], erg[f"{typ}_inf"]
        nm = typ.capitalize()
        ax.plot(Vb, e["gleich"] / 1e6, color=c, lw=2, label=f"{nm} {'gleichmäßig' if de else 'uniform'} (CFD n144)")
        ax.plot(Vb, e["gestuft"] / 1e6, color=c, lw=1.4, ls="--", label=f"{nm} {'abgestuft, 8 Segmente' if de else 'graded, 8 segments'}")
        ax.fill_between(Vb, np.fmin(e["gleich"], ei["gleich"]) / 1e6, np.fmax(e["gleich"], ei["gleich"]) / 1e6, color=c, alpha=0.13, lw=0)
    ax.plot(Vb, alt["renon"] / 1e6, color="#52514e", lw=1, ls=":",
            label=("Gyroid gleichmäßig, Literatur (Renon), gleiches Modell" if de else "Gyroid uniform, literature (Renon), same model"))
    ax.plot(Vb, alt["renon128"] / 1e6, color="#8a8984", lw=1, ls="-.",
            label=("Gyroid abgestuft nach Oh et al. (Nu × 1,28)" if de else "Gyroid graded after Oh et al. (Nu × 1.28)"))
    ax.set_xscale("log"); ax.set_xlim(0.3, 30)
    ax.set_xlabel("Bauvolumen des Tauschers [m³]" if de else "Exchanger volume [m³]")
    ax.set_ylabel("Netto-Mehrleistung [MW elektrisch]" if de else "Net extra power [MW electric]")
    ax.set_ylim(50, W_max / 1e6 + 1.5)
    ax.set_title(("Divertor-Vorwärmer mit CFD-Surrogat: Stufung der Zelle längs des Wegs\n"
                  "Band: Nu gerechnet (n144) bis extrapoliert (Gitter → ∞)") if de else
                 ("Divertor preheater with CFD surrogate: cell grading along the flow path\n"
                  "Band: Nu computed (n144) to extrapolated (grid → ∞)"), fontsize=11)
    ax.grid(True, which="both", color="#e5e4e0", lw=0.6); ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    fig.text(0.01, 0.005, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e")
    fig.tight_layout()
    name = "vorwaermer_stufung.png" if de else "vorwaermer_stufung_en.png"
    fig.savefig(VW.AUS / name); plt.close(fig)
    shutil.copy(VW.AUS / name, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return VW.AUS / name


if __name__ == "__main__":
    main()
