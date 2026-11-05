"""Bilder und interaktive Seite zur Wirkungskarte (stellarator/qi_wirkung.py). Aufruf: python -m stellarator.qi_wirkung bilder | html."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stellarator.qi_wirkung import AUS, NAHT_GRAD, geometrie, lade, maske, wirkung  # noqa: E402

BILD = ROOT / "docs" / "recherche" / "qi_tragwerk" / "qi_wirkungskarte"
FARBEN = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]       # wie qi_3d.py / qi_spulen.py


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _spur(A, G, js, g, alle=False):
    """Spulenspur (plasmanah < 1,6 a) und Marken: Stern = naechste Stelle zur Flaeche, Dreieck = staerkste Kruemmung."""
    for gg, p, t, d in G[f"spur{js}"]:
        if gg != g and not alle:
            continue
        p = np.where(d < 1.6, p.astype(float), np.nan); t = np.where(d < 1.6, t.astype(float), np.nan)
        spr = np.r_[False, (np.abs(np.diff(p)) > 20) | (np.abs(np.diff(t)) > 90)]; p[spr] = np.nan
        A.plot(p, t, "-", color=FARBEN[int(gg)], lw=1.4 if gg == g else 0.7, alpha=1 if gg == g else 0.5)
    for gg, p, t, d in G[f"naechst{js}"]:
        if int(gg) == g or alle:
            A.plot(p, t, "*", ms=13, mfc=FARBEN[int(gg)], mec="k", mew=0.8)
    for gg, p, t, k, d in G[f"kruemm{js}"]:
        if int(gg) == g or alle:
            A.plot(p, t, "^", ms=8, mfc="white", mec=FARBEN[int(gg)], mew=1.6)


def _naht(A, G):
    p0 = np.degrees(float(G["p0"])); per = 360 / int(G["nfp"])
    for x0, x1 in ((p0, p0 + NAHT_GRAD), (p0 + per - NAHT_GRAD, p0 + per)):
        A.axvspan(x0, x1, color="0.75", alpha=0.8, lw=0, hatch="//")


def abwicklung(G, js, W, titel_s, qi0):
    plt = _plt(); p0 = np.degrees(float(G["p0"])); per = 360 / int(G["nfp"])
    ph = np.degrees(G["PH"]); th = np.degrees(G["TH"]); mk = maske(G)
    b, fe = lade("basis"), lade("fest"); delta = (b[f"q{js}"].astype(float) - fe[f"q{js}"]) / qi0
    fig, ax = plt.subplots(2, 3, figsize=(16, 9.5), constrained_layout=True)
    lim = np.percentile(np.abs(W[:, mk]), 99)
    for g in range(5):
        A = ax.flat[g]
        im = A.pcolormesh(ph, th, W[g], cmap="RdBu_r", vmin=-lim, vmax=lim, shading="nearest", rasterized=True)
        _naht(A, G); _spur(A, G, js, g)
        A.set_title(f"S{g + 1}: lokale QI-Änderung je +1 % Strom (rot = schlechter)", fontsize=10)
    fig.colorbar(im, ax=ax[:, :2], shrink=0.6, label="Änderung lokaler QI je +1 % Strom\n(in Einheiten des Flächen-QI)")
    A = ax.flat[5]; lz = np.percentile(np.abs(delta[mk]), 99)
    im2 = A.pcolormesh(ph, th, delta, cmap="PuOr_r", vmin=-lz, vmax=lz, shading="nearest", rasterized=True)
    _naht(A, G); _spur(A, G, js, -1, alle=True)
    A.set_title("Zusatzfehler durch die Spulen (mit − ohne Spulen); alle Spulen", fontsize=10)
    fig.colorbar(im2, ax=A, shrink=0.8, label="Zusatzfehler (Einheiten Flächen-QI)")
    for A in ax.flat:
        A.set_xlim(p0, p0 + per); A.set_ylim(0, 360); A.set_xlabel("Toroidalwinkel φ_B (Grad, eine Periode)"); A.set_ylabel("Poloidalwinkel θ_B (Grad)")
    fig.suptitle(f"DjLe3eL6, {titel_s}: Wirkungskarten je Spulengruppe. Linie = Spule (wo näher als 1,6 a), ★ = nächste Stelle zur Fläche, "
                 f"△ = stärkste Krümmung, grau schraffiert = Naht des QI-Verfahrens", fontsize=11)
    return fig


def streubild(G, js, W, E):
    plt = _plt(); a = float(G["a"]); mk = maske(G); d = G[f"d{js}"] / a; ph = np.mod(np.degrees(G["PH"] - G["p0"]), 360 / int(G["nfp"]))
    fig, ax = plt.subplots(1, 5, figsize=(18, 4.2), sharey=True, constrained_layout=True)
    for g in range(5):
        A = ax[g]; e = E["gruppen"][f"S{g + 1}"]
        sc = A.scatter(d[g][mk], np.abs(W[g][mk]), c=ph[mk], cmap="twilight", s=2, rasterized=True, vmin=0, vmax=90)
        # Median je Abstandsklasse
        kl = np.linspace(d[g][mk].min(), np.percentile(d[g][mk], 99), 15); m = 0.5 * (kl[1:] + kl[:-1]); ix = np.digitize(d[g][mk], kl) - 1
        med = [np.median(np.abs(W[g][mk])[ix == k]) if (ix == k).sum() > 10 else np.nan for k in range(len(m))]
        A.plot(m, med, "-", color="k", lw=2, label="Median je Abstandsklasse")
        A.set_yscale("log"); A.set_ylim(1e-4, None); A.grid(alpha=0.3)
        A.set_title(f"S{g + 1}: Rang ρ(|W|, 1/d) = {e['spearman_absW_inv_abstand']:+.2f}", fontsize=10, color=FARBEN[g])
        A.set_xlabel("Abstand zur Spulengruppe (kleine Radien a)")
    ax[0].set_ylabel("|lokale QI-Änderung| je 1 % Strom\n(Einheiten Flächen-QI)"); ax[0].legend(fontsize=8, loc="lower left")
    fig.colorbar(sc, ax=ax, shrink=0.8, label="Toroidalwinkel φ_B in der Periode (Grad)")
    return fig


def profil(G, js, W, qi0):
    """Theta-gemittelte |Wirkung| je Toroidalwinkel und kleinster Abstand je Gruppe (zwei getrennte Felder, je eine Achse)."""
    plt = _plt(); a = float(G["a"]); phg = np.degrees(G["PH"][0]); ok = maske(G)[0]; d = G[f"d{js}"] / a
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True, constrained_layout=True)
    for g in range(5):
        pr = np.abs(W[g]).mean(0); pr[~ok] = np.nan
        ax[0].plot(phg, pr, color=FARBEN[g], lw=2, label=f"S{g + 1}")
        dm = d[g].min(0); ax[1].plot(phg, dm, color=FARBEN[g], lw=2)
        i = np.nanargmax(pr); ax[0].plot(phg[i], pr[i], "o", color=FARBEN[g], mec="k")
        j = np.argmin(np.where(ok, dm, np.inf)); ax[1].plot(phg[j], dm[j], "o", color=FARBEN[g], mec="k")
    for A in ax:
        _naht(A, G); A.grid(alpha=0.3)
    ax[0].set_ylabel("|Wirkung| gemittelt über θ\n(je 1 % Strom, Einheiten Flächen-QI)"); ax[0].legend(ncol=5, fontsize=9)
    ax[1].set_ylabel("kleinster Abstand Spule–Fläche (a)"); ax[1].set_xlabel("Toroidalwinkel φ_B (Grad, eine Periode)")
    ax[0].set_title("Oben: wo jede Gruppe wirkt (Punkt = Maximum). Unten: wo sie der Fläche am nächsten ist (Punkt = Minimum)", fontsize=10)
    return fig


def drei_d(G, js, W, g=4):
    plt = _plt(); from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    from scipy.interpolate import RegularGridInterpolator
    Xv = G[f"Xv{js}"]; THv, PHv = G["THv"], G["PHv"]; p0 = float(G["p0"]); per = 2 * np.pi / int(G["nfp"])
    # Wirkung (eine Periode, Gitter) auf den ganzen Torus: periodisch in phi_B, Gitter in theta geschlossen
    th = G["TH"][:, 0]; ph = G["PH"][0]
    Wz = np.vstack([W[g], W[g][:1]]); thz = np.r_[th, 2 * np.pi]
    Wz = np.hstack([Wz[:, -1:], Wz, Wz[:, :1]]); phz = np.r_[ph[0] - (ph[1] - ph[0]), ph, ph[-1] + (ph[1] - ph[0])]
    f = RegularGridInterpolator((thz, phz), Wz)
    F = f(np.stack([np.mod(THv, 2 * np.pi), p0 + np.mod(PHv - p0, per)], -1))
    phd = np.degrees(np.mod(PHv - p0, per)); naht = (phd < NAHT_GRAD) | (phd > np.degrees(per) - NAHT_GRAD)
    lim = np.percentile(np.abs(W[g]), 99); nrm = plt.Normalize(-lim, lim); fc = plt.cm.RdBu_r(nrm(F)); fc[naht] = [0.7, 0.7, 0.7, 1]
    out = []
    for nm, el, az in (("schraeg", 30, 25), ("draufsicht", 89, -90)):
        fig = plt.figure(figsize=(10, 8)); A = fig.add_subplot(111, projection="3d")
        A.plot_surface(Xv[..., 0], Xv[..., 1], Xv[..., 2], facecolors=fc, rstride=1, cstride=1, linewidth=0, shade=False, antialiased=False)
        for gg, gam in G["spulen"]:
            gg = int(gg); A.plot(gam[:, 0], gam[:, 1], gam[:, 2], color=FARBEN[gg] if gg == g else "0.55", lw=3.0 if gg == g else 0.6)
        A.set_box_aspect((np.ptp(Xv[..., 0]), np.ptp(Xv[..., 1]), max(np.ptp(Xv[..., 2]), 0.3 * np.ptp(Xv[..., 0])))); A.view_init(elev=el, azim=az); A.set_axis_off()
        fig.colorbar(plt.cm.ScalarMappable(norm=nrm, cmap="RdBu_r"), ax=A, shrink=0.5, label=f"lokale QI-Änderung je +1 % Strom an S{g + 1}\n(Einheiten Flächen-QI; rot = schlechter, blau = besser)")
        A.plot([], [], color=FARBEN[g], lw=3, label=f"Spulengruppe S{g + 1} (8 Spulen)"); A.plot([], [], color="0.55", lw=0.6, label="übrige Spulen")
        A.legend(loc="upper left", fontsize=8)
        A.set_title(f"DjLe3eL6, Fläche s = {float(G['s'][js]):.2f}: Wirkung von S{g + 1} auf den lokalen QI (grau = Naht des QI-Verfahrens)", fontsize=10)
        out.append((nm, fig))
    return out


def lagekarte(G, js, WL, art, qi0):
    plt = _plt(); p0 = np.degrees(float(G["p0"])); per = 360 / int(G["nfp"]); ph = np.degrees(G["PH"]); th = np.degrees(G["TH"]); mk = maske(G)
    fig, ax = plt.subplots(1, 5, figsize=(19, 4.3), sharey=True, constrained_layout=True); lim = np.percentile(np.abs(WL[:, mk]), 99)
    name = {"r": "radial", "t": "toroidal", "z": "senkrecht"}
    for g in range(5):
        A = ax[g]; im = A.pcolormesh(ph, th, WL[g], cmap="RdBu_r", vmin=-lim, vmax=lim, shading="nearest", rasterized=True)
        _naht(A, G); _spur(A, G, js, g); A.set_xlim(p0, p0 + per); A.set_ylim(0, 360)
        A.set_title(f"S{g + 1}, {name[art[g]]} (stärkste Richtung)", fontsize=10); A.set_xlabel("φ_B (Grad)")
    ax[0].set_ylabel("θ_B (Grad)")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Änderung lokaler QI je 1 mm\n(Einheiten Flächen-QI)")
    fig.suptitle("Lage-Wirkungskarten: Verschiebung der Spulengruppe um 1 mm (Anlagenmaßstab; aus ±5 mm)", fontsize=11)
    return fig


def opt_bild(G, qi0):
    plt = _plt(); f = AUS / "opt_karte.npz"
    if not f.exists():
        return None
    o = np.load(f); og = np.load(AUS / "opt_karte_global.npz"); E = json.loads((AUS / "opt.json").read_text())
    qb = lade("basis")["q1"].astype(float); p0 = np.degrees(float(G["p0"])); per = 360 / int(G["nfp"]); ph = np.degrees(G["PH"]); th = np.degrees(G["TH"])
    vmax = np.percentile(qb, 99) / qi0
    fig, ax = plt.subplots(1, 3, figsize=(17, 4.8), sharey=True, constrained_layout=True)
    for A, q, t in ((ax[0], qb, "Grundzustand (Ströme wie Proxima)"), (ax[1], og["q"], f"globales Optimum B-053 {np.round(E['global_B053']['faktoren'], 3).tolist()}"),
                    (ax[2], o["q"], f"Flecken-Optimum {np.round(E['flecken_opt']['faktoren'], 3).tolist()}")):
        im = A.pcolormesh(ph, th, q / qi0, cmap="inferno", vmin=0, vmax=vmax, shading="nearest", rasterized=True)
        A.contour(ph, th, o["maske_flecken"].astype(float), levels=[0.5], colors="cyan", linewidths=0.8)
        _naht(A, G); A.set_xlim(p0, p0 + per); A.set_title(t, fontsize=9); A.set_xlabel("φ_B (Grad)")
    ax[0].set_ylabel("θ_B (Grad)")
    fig.colorbar(im, ax=ax, shrink=0.8, label="lokaler QI (Einheiten Flächen-QI Grundzustand)")
    fig.suptitle("Rand: gezielte Stromtrimmung der schlechtesten 5 % (cyan umrandet), Schranken ±5 %", fontsize=11)
    return fig


def bilder():
    BILD.mkdir(parents=True, exist_ok=True); G = geometrie(); E = json.loads((AUS / "auswertung.json").read_text())
    plt = _plt()
    for js, s in enumerate(G["s"]):
        W, WL, art, qi0 = wirkung(js); tag = "rand" if js == len(G["s"]) - 1 else "s05"; ts = "Rand" if tag == "rand" else f"Fläche s = {float(s):.2f}"
        Es = E["flaechen"][f"s{float(s):.3f}"]
        abwicklung(G, js, W, ts, qi0).savefig(BILD / f"abwicklung_{tag}.png", dpi=100); plt.close("all")
        streubild(G, js, W, Es).savefig(BILD / f"streubild_{tag}.png", dpi=100); plt.close("all")
        profil(G, js, W, qi0).savefig(BILD / f"profil_{tag}.png", dpi=100); plt.close("all")
        lagekarte(G, js, WL, art, qi0).savefig(BILD / f"lage_{tag}.png", dpi=100); plt.close("all")
        if tag == "rand":
            for nm, fig in drei_d(G, js, W, 4):
                fig.savefig(BILD / f"wirkung3d_S5_{nm}.png", dpi=105, bbox_inches="tight")
            plt.close("all")
            fig = opt_bild(G, qi0)
            if fig:
                fig.savefig(BILD / "flecken_opt.png", dpi=100); plt.close("all")
    print("Bilder in", BILD)


def html():
    """Eine interaktive Seite: Rand mit Wirkungskarte je Gruppe (Auswahl), Spulen der gewaehlten Gruppe dick.
    plotly.min.js einmal im Bildordner (include_plotlyjs='directory'), nicht in die Seite kopiert."""
    import plotly.graph_objects as go
    from scipy.interpolate import RegularGridInterpolator
    G = geometrie(); js = len(G["s"]) - 1; W, _, _, qi0 = wirkung(js)
    b, fe = lade("basis"), lade("fest"); delta = (b[f"q{js}"].astype(float) - fe[f"q{js}"]) / qi0
    Xv = G[f"Xv{js}"][:, ::2]; THv, PHv = G["THv"][:, ::2], G["PHv"][:, ::2]; p0 = float(G["p0"]); per = 2 * np.pi / int(G["nfp"])
    th = G["TH"][:, 0]; ph = G["PH"][0]

    def torus(K):
        Kz = np.vstack([K, K[:1]]); Kz = np.hstack([Kz[:, -1:], Kz, Kz[:, :1]])
        f = RegularGridInterpolator((np.r_[th, 2 * np.pi], np.r_[ph[0] - (ph[1] - ph[0]), ph, ph[-1] + (ph[1] - ph[0])]), Kz)
        return f(np.stack([np.mod(THv, 2 * np.pi), p0 + np.mod(PHv - p0, per)], -1))
    karten = [(f"Wirkung S{g + 1} je +1 % Strom", torus(W[g]), np.percentile(np.abs(W[g]), 99), g) for g in range(5)]
    karten.append(("Zusatzfehler durch alle Spulen", torus(delta), np.percentile(np.abs(delta), 99), -1))
    fig = go.Figure(); n = len(karten)
    for i, (nm, F, lim, g) in enumerate(karten):
        fig.add_trace(go.Surface(x=Xv[..., 0].astype(np.float32), y=Xv[..., 1].astype(np.float32), z=Xv[..., 2].astype(np.float32),
                                 surfacecolor=np.round(F, 4).astype(np.float32), cmin=-lim, cmax=lim, colorscale="RdBu_r" if g >= 0 else "PuOr_r",
                                 visible=(i == 4), name=nm, colorbar=dict(title="Einheiten<br>Flächen-QI", len=0.6),
                                 hovertemplate=nm + ": %{surfacecolor:.3f}<extra></extra>"))
    sp = G["spulen"]
    for ii, (gg, gam) in enumerate(sp):
        gg = int(gg); P = np.vstack([gam, gam[:1]])[::3].astype(np.float32)
        fig.add_trace(go.Scatter3d(x=P[:, 0], y=P[:, 1], z=P[:, 2], mode="lines", line=dict(color=FARBEN[gg], width=8 if gg == 4 else 2),
                                   name=f"Spule S{gg + 1}", legendgroup=f"S{gg + 1}", showlegend=ii % 8 == 0 and ii < 40 and True))
    knoepfe = []
    for i, (nm, _, _, g) in enumerate(karten):
        vis = [k == i for k in range(n)] + [True] * len(sp)
        breite = [None] * n + [(8 if (int(gg) == g) else 2) if g >= 0 else 4 for gg, _ in sp]
        knoepfe.append(dict(label=nm, method="update", args=[{"visible": vis, "line.width": breite}, {"title": f"DjLe3eL6, Rand: {nm} (rot = schlechter, blau = besser)"}]))
    fig.update_layout(title="DjLe3eL6, Rand: Wirkung S5 je +1 % Strom (rot = schlechter, blau = besser)",
                      scene=dict(aspectmode="data", xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
                      updatemenus=[dict(buttons=knoepfe, direction="down", x=0.0, y=1.0, xanchor="left")], margin=dict(l=0, r=0, t=60, b=0))
    BILD.mkdir(parents=True, exist_ok=True)
    fig.write_html(BILD / "wirkungskarte_3d.html", include_plotlyjs="directory", full_html=True, config={"displaylogo": False})
    print("HTML", BILD / "wirkungskarte_3d.html")
