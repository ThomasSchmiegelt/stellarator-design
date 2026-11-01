"""tauscher_surrogat.py — mehrstufiges Surrogat Nu, f (Re, Pr, Zelle a) fuer Gyroid und Diamond aus den FluidX3D-Laeufen.

  .venv/bin/python -m stellarator.tauscher_surrogat

Daten: alle sim/tauscher/cfd/*_qu*/ergebnis.json (Waermequelle ~ u_z, TRT). Wand t = 0,5 mm fest.
Zielgroessen werden auf Renon & Jeanningros (2024) bezogen, damit der GP nur die Abweichung lernt:
    y_Nu = ln(Nu / Nu_Renon(Re, Pr)),  y_f = ln(f / f_Renon(Re))
Eingaenge: x = (ln Re, Pr, a [mm]), je Bauart ein Modell.

Stufe 1 (grob, n48, 15 Punkte je Bauart): GP mit ARD-RBF + Rauschen  ->  y48(x).
Gitterfehler: Kontrollpunkte n96 geben d96 = y96 - y48(x), als Gerade in ln Re (4 Punkte je Bauart). Die Reihe
n48/n96/n144 bei Re 3000 ist nicht asymptotisch (Schritt 96->144 groesser als nach p erwartet), daher zwei Stufen:
  n144: y48 + k144 d96(x),  k144 = d144/d96 bei Re 3000 (gerechnet, obere Schranke fuer Nu)
  inf:  y48 + kinf d96(x),  d_inf = d144 + (d144 - d96)/(1,5^p - 1), p = 1,33 (Plattentest), geschaetzt
Das ist ein Co-Kriging nach Kennedy & O'Hagan (2000) mit rho = 1 in der logarithmischen Groesse.
Ausgaben: stellarator/daten/tauscher_surrogat.json, docs/bilder/tauscher_surrogat(_en).png.
"""
import json
import shutil
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel

ROOT = Path(__file__).resolve().parents[1]
CFD = ROOT / "sim" / "tauscher" / "cfd"
DATEN = ROOT / "stellarator" / "daten"
BILDER = ROOT / "docs" / "bilder"
TYPEN = ("gyroid", "diamond")
A_STD = dict(gyroid=4.33, diamond=5.37)


def renon(re, pr):
    return 0.2644 * re ** 0.69 * pr ** (1 / 3), 1.850 * re ** -0.17


def laden():
    zeilen = []
    for p in sorted(CFD.glob("*_qu*/ergebnis.json")):
        e = json.loads(p.read_text())
        if e["typ"] not in TYPEN:
            continue
        nr, fr = renon(e["Re"], e["Pr"])
        zeilen.append(dict(name=p.parent.name, typ=e["typ"], n=e["n_dh"], Re=e["Re"], Pr=e["Pr"], a=e["P"]["a"],
                           phi=e["phi"], d_h=e["d_h"], Nu=e["Nu"], f=e["f"], yN=np.log(e["Nu"] / nr), yf=np.log(e["f"] / fr)))
    return zeilen


def x_von(re, pr, a):
    return np.column_stack([np.log(np.atleast_1d(re)), np.broadcast_to(pr, np.shape(np.atleast_1d(re))),
                            np.broadcast_to(a, np.shape(np.atleast_1d(re)))])


def gp_fit(X, y):
    k = C(0.05, (1e-4, 10)) * RBF([1.0, 0.5, 1.0], [(0.05, 50), (0.05, 50), (0.1, 50)]) + WhiteKernel(1e-4, (1e-7, 1e-2))
    g = GaussianProcessRegressor(k, normalize_y=True, n_restarts_optimizer=8, random_state=0)
    return g.fit(X, y)


def ordnung(d96, d144):
    """p aus d96/d144 = (48^-p - 96^-p)/(48^-p - 144^-p)."""
    r = d96 / d144
    g = lambda p: (48 ** -p - 96 ** -p) / (48 ** -p - 144 ** -p) - r
    try:
        return brentq(g, 0.2, 6)
    except ValueError:
        return np.nan


class Surrogat:
    def __init__(self, zeilen, p=None):
        self.z = zeilen; self.mod = {}; self.p_einzeln = {}
        for typ in TYPEN:
            Z = [z for z in zeilen if z["typ"] == typ]
            lo = [z for z in Z if z["n"] == 48]
            X = np.array([[np.log(z["Re"]), z["Pr"], z["a"]] for z in lo])
            g = {k: gp_fit(X, np.array([z[k] for z in lo])) for k in ("yN", "yf")}
            m = dict(g=g, X48=X)
            for k in ("yN", "yf"):
                d = {}
                for n in (96, 144):
                    for z in [z for z in Z if z["n"] == n]:
                        x = x_von(z["Re"], z["Pr"], z["a"])
                        d.setdefault(n, []).append((z, float(z[k] - g[k].predict(x)[0])))
                m[f"d_{k}"] = d
                # Re-3000-Reihe: n96 ohne Tag (gleiche Parameter wie n144)
                d96 = [v for z, v in d.get(96, []) if "_s" not in z["name"]]
                d144 = [v for z, v in d.get(144, [])]
                self.p_einzeln[(typ, k)] = ordnung(d96[0], d144[0]) if d96 and d144 else np.nan
            self.mod[typ] = m
        # Die Reihe n48/n96/n144 liegt NICHT im asymptotischen Bereich (d96/d144 < ln2/ln3, kein p > 0 loest es).
        # Darum: Stufe n144 = d96(x) * k144 mit k144 = d144/d96 bei Re 3000 (gerechnet, obere Schranke),
        # Stufe inf = Richardson nur ueber den letzten Schritt 96 -> 144 mit p (Platte 1,33): obere Stufe geschaetzt.
        self.p = p if p is not None else 1.33
        for typ in TYPEN:
            m = self.mod[typ]
            for k in ("yN", "yf"):
                d96 = [(z, v) for z, v in m[f"d_{k}"][96]]
                ref96 = [v for z, v in d96 if "_s" not in z["name"]][0]; d144 = m[f"d_{k}"][144][0][1]
                dinf = d144 + (d144 - ref96) / (1.5 ** self.p - 1)
                L = np.array([np.log(z["Re"]) for z, v in d96]); D = np.array([v for z, v in d96])
                A = np.column_stack([np.ones_like(L), L - np.log(3000)])
                c, *_ = np.linalg.lstsq(A, D, rcond=None)
                res = D - A @ c
                m[f"k_{k}"] = dict(c96=c.tolist(), s=float(np.sqrt(np.sum(res ** 2) / max(len(D) - 2, 1))),
                                   k144=float(d144 / ref96), kinf=float(dinf / ref96), d96_ref=float(ref96),
                                   d144=float(d144), dinf=float(dinf), pts=[(float(a), float(b)) for a, b in zip(L, D)])

    def __call__(self, typ, re, pr, a, stufe="inf", std=False):
        """Nu, f (und 1-sigma in ln) fuer Bauart typ; stufe n48, n96, n144 (gerechnet) oder inf (extrapoliert)."""
        m = self.mod[typ]; x = x_von(re, pr, a)
        out = []
        for k in ("yN", "yf"):
            y, s = m["g"][k].predict(x, return_std=True)
            if stufe in ("n96", "n144", "inf"):
                K = m[f"k_{k}"]; c = K["c96"]
                d = c[0] + c[1] * (x[:, 0] - np.log(3000))
                fak = dict(n96=1.0, n144=K["k144"], inf=K["kinf"])[stufe]
                y = y + fak * d
                # Unsicherheit: GP, Rest der Korrekturgeraden, bei inf halber Abstand inf - n144
                zus = 0.5 * abs(K["kinf"] - K["k144"]) * d if stufe == "inf" else 0 * d
                s = np.sqrt(s ** 2 + (fak * K["s"]) ** 2 + zus ** 2)
            out.append((y, s))
        nr, fr = renon(np.asarray(re, float), np.asarray(pr, float))
        Nu, f = nr * np.exp(out[0][0]), fr * np.exp(out[1][0])
        return (Nu, f, out[0][1], out[1][1]) if std else (Nu, f)

    def kreuz(self):
        """Leave-one-out der groben Stufe (Fehler in ln)."""
        erg = {}
        for typ in TYPEN:
            X = self.mod[typ]["X48"]; lo = [z for z in self.z if z["typ"] == typ and z["n"] == 48]
            for k in ("yN", "yf"):
                y = np.array([z[k] for z in lo]); e = []
                for i in range(len(y)):
                    msk = np.arange(len(y)) != i
                    g = gp_fit(X[msk], y[msk]); e.append(float(g.predict(X[i:i + 1])[0] - y[i]))
                erg[(typ, k)] = np.array(e)
        return erg


TEXT = dict(
    de=dict(t1="Nu über Re (Pr 1,5, Standardzelle)", t2="f über Re (Linie: n144 ±1σ)", t3="Kreuzprüfung grobe Stufe (n48)",
            xl="Re", g48="Surrogat n48", ginf="Surrogat Gitter → ∞, geschätzt (±1σ)", ren="Renon & Jeanningros 2024", g144="Surrogat n144",
            p48="CFD n48", p96="CFD n96", p144="CFD n144", vorh="vorhergesagt", ber="gerechnet",
            titel="Surrogat für Gyroid- und Diamond-Zellen aus {n} FluidX3D-Läufen (Wand 0,5 mm); f: Extrapolation unsicher, gezeigt n144"),
    en=dict(t1="Nu vs Re (Pr 1.5, standard cell)", t2="f vs Re (line: n144 ±1σ)", t3="Cross-check coarse level (n48)",
            xl="Re", g48="Surrogate n48", ginf="Surrogate grid → ∞, estimated (±1σ)", ren="Renon & Jeanningros 2024", g144="Surrogate n144",
            p48="CFD n48", p96="CFD n96", p144="CFD n144", vorh="predicted", ber="computed",
            titel="Surrogate for gyroid and diamond cells from {n} FluidX3D runs (wall 0.5 mm); f: extrapolation uncertain, n144 shown"))


def bild(S, kreuz, sprache):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    T = TEXT[sprache]
    farbe = dict(gyroid="#2a78d6", diamond="#eb6834")
    fig, ax = plt.subplots(1, 3, figsize=(15, 5), dpi=130)
    re = np.geomspace(450, 10000, 120)
    for typ in TYPEN:
        c = farbe[typ]; a = A_STD[typ]
        n48, f48 = S(typ, re, 1.5, a, "n48")
        ni, fi, sn, sf = S(typ, re, 1.5, a, "inf", std=True)
        n144, f144 = S(typ, re, 1.5, a, "n144")
        ax[0].plot(re, n144, color=c, ls="--", lw=1.1); ax[1].plot(re, f144, color=c, ls="--", lw=2)
        ax[0].plot(re, n48, color=c, ls=":", lw=1.3)
        ax[0].plot(re, ni, color=c, lw=2, label=f"{typ.capitalize()}")
        ax[0].fill_between(re, ni * np.exp(-sn), ni * np.exp(sn), color=c, alpha=0.15, lw=0)
        ax[1].plot(re, f48, color=c, ls=":", lw=1.3)
        # f: Extrapolation unzuverlaessig (nicht monoton) -> gerechnete Stufe n144 mit Band
        _, f1, _, sf1 = S(typ, re, 1.5, a, "n144", std=True)
        ax[1].fill_between(re, f1 * np.exp(-sf1), f1 * np.exp(sf1), color=c, alpha=0.15, lw=0)
        for z in [z for z in S.z if z["typ"] == typ]:
            # auf Pr 1,5 und Standardzelle umrechnen ueber das Surrogat (nur zur Anzeige)
            mk = {48: "o", 96: "s", 144: "D"}[z["n"]]
            nr, fr = renon(z["Re"], z["Pr"]); nr15, _ = renon(z["Re"], 1.5)
            ax[0].scatter(z["Re"], z["Nu"] / nr * nr15, marker=mk, s=22, color=c, alpha=0.75 if z["n"] == 48 else 1,
                          edgecolor="k" if z["n"] > 48 else "none", lw=0.6, zorder=3)
            ax[1].scatter(z["Re"], z["f"], marker=mk, s=22, color=c, alpha=0.75 if z["n"] == 48 else 1,
                          edgecolor="k" if z["n"] > 48 else "none", lw=0.6, zorder=3)
        e = kreuz[(typ, "yN")]; lo = [z for z in S.z if z["typ"] == typ and z["n"] == 48]
        y = np.array([z["Nu"] for z in lo])
        ax[2].scatter(y, y * np.exp(e), color=c, s=24, label=f"{typ.capitalize()} Nu, RMS {np.sqrt(np.mean(e**2))*100:.1f} %")
    nr, fr = renon(re, 1.5)
    ax[0].plot(re, nr, color="#52514e", ls="--", lw=1.2, label=T["ren"]); ax[1].plot(re, fr, color="#52514e", ls="--", lw=1.2)
    ax[0].plot([], [], color="k", ls=":", label=T["g48"]); ax[0].plot([], [], color="k", ls="--", lw=1.1, label=T["g144"]); ax[0].plot([], [], color="k", lw=2, label=T["ginf"])
    for mk, l in (("o", T["p48"]), ("s", T["p96"]), ("D", T["p144"])):
        ax[0].scatter([], [], marker=mk, color="grey", label=l)
    for a_, t in ((ax[0], T["t1"]), (ax[1], T["t2"])):
        a_.set_xscale("log"); a_.set_yscale("log"); a_.set_xlabel(T["xl"]); a_.set_title(t, fontsize=11)
        a_.grid(True, which="both", color="#e5e4e0", lw=0.6); a_.spines[["top", "right"]].set_visible(False)
    ax[0].set_ylabel("Nu"); ax[1].set_ylabel("f (Fanning)")
    ax[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    lim = [20, 450]; ax[2].plot(lim, lim, color="#52514e", lw=1); ax[2].set_xscale("log"); ax[2].set_yscale("log")
    ax[2].set_xlim(lim); ax[2].set_ylim(lim)
    from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
    for ach in (ax[2].xaxis, ax[2].yaxis):
        ach.set_major_locator(FixedLocator([20, 50, 100, 200, 400])); ach.set_minor_locator(NullLocator())
        ach.set_major_formatter(ScalarFormatter()); ax[2].set_xlabel(T["ber"]); ax[2].set_ylabel(T["vorh"])
    ax[2].set_title(T["t3"], fontsize=11); ax[2].legend(frameon=False, fontsize=8, loc="upper left")
    ax[2].grid(True, which="both", color="#e5e4e0", lw=0.6); ax[2].spines[["top", "right"]].set_visible(False)
    fig.suptitle(T["titel"].format(n=len(S.z)), fontsize=12, x=0.01, ha="left")
    fig.text(0.99, 0.01, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e", ha="right")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    name = "tauscher_surrogat.png" if sprache == "de" else "tauscher_surrogat_en.png"
    fig.savefig(BILDER / name); plt.close(fig)
    shutil.copy(BILDER / name, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return BILDER / name


def main():
    z = laden()
    S = Surrogat(z)
    print(f"{len(z)} Laeufe: " + ", ".join(f"{t} n{n}: {sum(1 for q in z if q['typ']==t and q['n']==n)}" for t in TYPEN for n in (48, 96, 144)))
    print("Ordnung p aus n48/n96/n144 bei Re 3000 (nan = nicht asymptotisch):", {f"{t}/{k}": round(v, 2) for (t, k), v in S.p_einzeln.items()})
    kr = S.kreuz()
    for (t, k), e in kr.items():
        print(f"LOO {t:8s} {k}: RMS {np.sqrt(np.mean(e**2))*100:.1f} %, max {np.max(np.abs(e))*100:.1f} %")
    for t in TYPEN:
        m = S.mod[t]
        for k in ("yN", "yf"):
            c = m[f"k_{k}"]
            print(f"Gitter {t:8s} {k}: d96 {c['d96_ref']:+.3f}  d144 {c['d144']:+.3f}  d_inf {c['dinf']:+.3f} (k144 {c['k144']:.2f}, kinf {c['kinf']:.2f}); "
                  f"d96-Gerade {c['c96'][0]:+.3f} {c['c96'][1]:+.3f}*ln(Re/3000), Rest {c['s']:.3f}")
        print("  Kernel Nu:", m["g"]["yN"].kernel_)
    print("\nPr 1,5, Standardzelle: Nu/Renon und f/Renon je Stufe n48 / n144 / inf (±1 sigma)")
    for t in TYPEN:
        for re in (1000, 3000, 8000):
            nr, fr = renon(re, 1.5); zl = f"  {t:8s} {re:5d}"
            for st in ("n48", "n144", "inf"):
                Nu, f, sn, sf = S(t, re, 1.5, A_STD[t], st, std=True)
                zl += f" | {st:4s} Nu {Nu[0]/nr:4.2f}±{sn[0]*100:3.0f}% f {f[0]/fr:4.2f}±{sf[0]*100:3.0f}%"
            print(zl)
    erg = dict(p_letzter_schritt=S.p, p_einzeln={f"{t}/{k}": (None if not np.isfinite(v) else v) for (t, k), v in S.p_einzeln.items()},
               loo={f"{t}/{k}": float(np.sqrt(np.mean(e ** 2))) for (t, k), e in kr.items()},
               korrektur={t: {k: S.mod[t][f"k_{k}"] for k in ("yN", "yf")} for t in TYPEN},
               laeufe=[{k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in q.items()} for q in z])
    (DATEN / "tauscher_surrogat.json").write_text(json.dumps(erg, indent=1, default=float))
    for s in ("de", "en"):
        print(bild(S, kr, s))
    return S


if __name__ == "__main__":
    main()
