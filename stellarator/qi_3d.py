"""QI als Farbe auf der echten 3D-Plasmaflaeche, dazu die Spulen (Wunsch des Nutzers 2026-11-05).

Aufruf (aus ~/hermes/fusion, im Scope):
  systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 --description="hermes python qi_3d dje" \
      env OMP_NUM_THREADS=2 .venv-constellaration/bin/python -m stellarator.qi_3d dje
  ... qi_3d do3 | qi_3d k3          # ohne Spulen (kein Spulensatz vorhanden)

Verfahren:
  1. Gleichgewicht wie offiziell (forward_model, default_high_fidelity); fuer dje das schon gerechnete sim/qi_spulen/wout/fest.nc.
  2. booz_xform fuer die Flaechen S3D; je Flaeche qi.quasi_isodynamicity_residual (Paketfunktion), Residuen r (75 Feldlinien x
     2000 Boozer-Toroidalwinkel; Feldlinie alpha: theta_B = alpha + iota (phi_B - phi_start), wie qi.py).
  3. Lokaler QI-Wert q = r^2 * N (N = 75*2000): das Mittel von q ueber die Flaeche ist genau der QI-Wert der Flaeche
     (die Feldlinienpunkte liegen gleichmaessig in (alpha, phi_B), die Scherung theta_B = alpha + iota phi_B ist flaechentreu).
  4. Abbildung auf ein regelmaessiges Gitter (theta_B, phi_B) ueber den ganzen Torus: phi_B auf eine Periode zurueckfuehren,
     alpha bestimmen, zwischen Feldlinien und Winkeln linear interpolieren. Ort im Raum aus den Boozer-Reihen (R, Z, nu):
     phi_zyl = phi_B + v*nu, v so gewaehlt, dass der Punkt auf der VMEC-Flaeche liegt (Pruefung, Lagefehler wird ausgegeben).
  5. Pruefungen: Gittermittel von q gegen QI der Flaeche; Stellarator-Symmetrie q(theta, phi) = q(-theta, -phi) auf dem Gitter
     (die Feldlinien-Rechnung erzwingt sie nicht, sie ist also ein unabhaengiges Zeichen fuer richtige Winkel und Interpolation).
  Ausgabe: sim/qi_flaeche/karte3d/<form>.npz, <form>.json, qi_3d_<form>.html (plotly, offline, WebGL), Ansichten *.png.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUS = ROOT / "sim" / "qi_flaeche" / "karte3d"
S3D = [0.25, 0.5, 0.75, 1.0]
NTH, NPH_PER = 72, 72          # Gitter je Periode (Anzeige)
FORMEN = {"dje": "DjLe3eL6 (mit Proxima-Spulen)", "do3": "Do3QyJbtRhtGhrTiBSBbyKM (beste Datensatzform)", "k3": "Kandidat 3, halber Schritt (eigene Form)"}


def gleichgewicht(form):
    import vmecpp
    from constellaration.mhd import vmec_utils
    if form == "dje":
        f = ROOT / "sim" / "qi_spulen" / "wout" / "fest.nc"
    else:
        f = AUS / f"wout_{form}.nc"
        if not f.exists():
            from constellaration import forward_model
            from constellaration.geometry import surface_rz_fourier as srf
            sys.path.insert(0, str(ROOT))
            from stellarator.qi_karte import rand
            b, _ = rand(form)
            m, w = forward_model.forward_model(srf.SurfaceRZFourier.model_validate(b), settings=forward_model.ConstellarationSettings.default_high_fidelity())
            AUS.mkdir(parents=True, exist_ok=True); w.save(f); print(form, "QI offiziell", m.qi, flush=True)
    return vmec_utils.vmecppwout_from_wout(vmecpp.VmecWOut.from_wout_file(f))


def rz(rc, zs, xm, xn, th, ze):
    a = np.multiply.outer(th, xm)[:, None, :] - np.multiply.outer(ze, xn)[None, :, :]
    return (np.cos(a) * rc).sum(-1), (np.sin(a) * zs).sum(-1)


def rechnen(form):
    from constellaration.boozer import boozer as bm
    from constellaration.omnigeneity import qi
    from scipy import interpolate
    from scipy.interpolate import RegularGridInterpolator
    sys.path.insert(0, str(ROOT))
    from stellarator.qi_karte import ausschnitt
    w = gleichgewicht(form)
    bz = bm.run_boozer(w, bm.create_boozer_settings_from_equilibrium_resolution(w, bm.BoozerPresetSettings(normalized_toroidal_flux=S3D)))
    qs = qi.QISettings(); nfp = bz.n_field_periods; N = qs.n_field_lines * qs.n_output_toroidal_points
    p0 = np.pi / nfp if bz.bmnc[1, 1] < 0 else 0.0
    phB_l = np.linspace(p0, p0 + 2 * np.pi / nfp, qs.n_output_toroidal_points)
    iota = interpolate.UnivariateSpline(bz.normalized_toroidal_flux, bz.iota, k=1, s=0)(bz.boozer_normalized_toroidal_flux)
    th = np.linspace(0, 2 * np.pi, NTH + 1); ph = np.linspace(0, 2 * np.pi, nfp * NPH_PER + 1)   # geschlossenes Gitter
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    out = {"s": [], "iota": [], "qi_flaeche": [], "qi_gittermittel": [], "symmetrie_rel_abw": [], "nu_lagefehler_m": []}
    X, Q = [], []
    for js in range(bz.n_boozer_flux_surfaces):
        r = qi.quasi_isodynamicity_residual(ausschnitt(bz, js), qs).residuals[0]           # (75, 2000), Summe r^2 = QI
        q = r ** 2 * N
        # Interpolation auf (theta_B, phi_B)
        f = RegularGridInterpolator((np.arange(qs.n_field_lines), phB_l), q)
        phr = p0 + np.mod(PH - p0, 2 * np.pi / nfp)
        al = np.mod(TH - iota[js] * (phr - p0), 2 * np.pi) / (2 * np.pi) * (qs.n_field_lines - 1)
        G = f(np.stack([np.clip(al, 0, qs.n_field_lines - 1), np.clip(phr, phB_l[0], phB_l[-1])], -1))
        # Symmetrie-Pruefung auf dem Gitter: q(theta, phi) = q(-theta, -phi) (Gitter geschlossen, Index i -> NTH - i, k -> Nph - k)
        sym = float(np.abs(G[::-1, ::-1] - G).mean() / G.mean())
        # Ort: Boozer-Reihen
        ang = bz.xm_b[:, None, None] * TH[None] - bz.xn_b[:, None, None] * PH[None]
        R = np.tensordot(bz.rmnc_b[:, js], np.cos(ang), 1); Z = np.tensordot(bz.zmns_b[:, js], np.sin(ang), 1); nu = np.tensordot(bz.numns_b[:, js], np.sin(ang), 1)
        # Vorzeichen von nu: Punkt muss auf der VMEC-Flaeche (naechste Halbgitter-Flaeche) liegen
        iv = int(bz.boozer_flux_surface_indices[js]) + 1; iv = min(iv, w.rmnc.shape[1] - 1)
        tt = np.linspace(0, 2 * np.pi, 2000, endpoint=False); fe = {}
        for v in (-1, 1):
            idx = (slice(None, None, 9), slice(None, None, 37))
            pz = (PH + v * nu)[idx].ravel(); Rr, Zr = R[idx].ravel(), Z[idx].ravel()
            Rv, Zv = rz(w.rmnc[:, iv], w.zmns[:, iv], w.xm, w.xn, tt, pz)
            fe[v] = float(np.max(np.hypot(Rv - Rr[None], Zv - Zr[None]).min(0)))
        v = min(fe, key=fe.get); PZ = PH + v * nu
        X.append(np.stack([R * np.cos(PZ), R * np.sin(PZ), Z], -1)); Q.append(G)
        out["s"].append(float(bz.boozer_normalized_toroidal_flux[js])); out["iota"].append(float(iota[js]))
        out["qi_flaeche"].append(float(q.mean())); out["qi_gittermittel"].append(float(G[:-1, :-1].mean()))
        out["symmetrie_rel_abw"].append(sym); out["nu_lagefehler_m"].append(fe[v]); out["nu_vorzeichen"] = v
        print(form, js, out["s"][-1], "QI", q.mean(), "Gitter", G[:-1, :-1].mean(), "Sym", sym, "Lage", fe, flush=True)
    out.update(form=form, name=FORMEN[form], nfp=int(nfp), phi_start=p0)
    AUS.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(AUS / f"{form}.npz", X=np.array(X), Q=np.array(Q), s=np.array(out["s"]))
    (AUS / f"{form}.json").write_text(json.dumps(out, indent=1))
    return out


def spulen_dje():
    sys.path.insert(0, str(ROOT))
    from stellarator.qi_spulen import basis_kurven, spulen
    k, I, nfp = basis_kurven(nq=160)
    return [(i % len(k), c.curve.gamma()) for i, c in enumerate(spulen(k, I, nfp))]


FARBEN = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def html(form, j, sp):
    import plotly.graph_objects as go
    z = np.load(AUS / f"{form}.npz"); X, Q = z["X"], z["Q"]
    vmax = float(np.percentile(Q[-1], 99))
    fig = go.Figure(); n = len(j["s"])
    for i in range(n):
        x = X[i]
        fig.add_trace(go.Surface(x=x[..., 0].astype(np.float32), y=x[..., 1].astype(np.float32), z=x[..., 2].astype(np.float32),
                                 surfacecolor=np.round(Q[i], 6).astype(np.float32), cmin=0, cmax=vmax, colorscale="Inferno", visible=(i == n - 1),
                                 colorbar=dict(title="lokaler QI-Wert<br>(Mittel = QI der Fläche)", len=0.6),
                                 name=f"s = {j['s'][i]:.2f}", hovertemplate="lokaler QI %{surfacecolor:.2e}<extra></extra>"))
    for ii, (g, gam) in enumerate(sp):
        gg = np.vstack([gam, gam[:1]]).astype(np.float32)
        fig.add_trace(go.Scatter3d(x=gg[:, 0], y=gg[:, 1], z=gg[:, 2], mode="lines", line=dict(color=FARBEN[g], width=6),
                                   name=f"Spule S{g + 1}", legendgroup=f"S{g + 1}", showlegend=ii < 5))
    knoepfe = []
    for i in range(n):
        vis = [k == i for k in range(n)] + [True] * len(sp)
        knoepfe.append(dict(label=f"s = {j['s'][i]:.2f}" + (" (Rand, offiziell)" if i == n - 1 else ""), method="update",
                            args=[{"visible": vis}, {"title": titel(form, j, i)}]))
    fig.update_layout(title=titel(form, j, n - 1), scene=dict(aspectmode="data", xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
                      updatemenus=[dict(buttons=knoepfe, direction="down", x=0.0, y=1.0, xanchor="left")], margin=dict(l=0, r=0, t=60, b=0),
                      legend=dict(x=0.85, y=0.95))
    fig.write_html(AUS / f"qi_3d_{form}.html", include_plotlyjs=True, full_html=True, config={"displaylogo": False})


def titel(form, j, i):
    return (f"{FORMEN[form]}: lokaler QI-Wert auf der Fläche s = {j['s'][i]:.2f} (QI der Fläche {j['qi_flaeche'][i]:.2e}); "
            f"hell = viel Abweichung vom idealen QI-Feld")


def bilder(form, j, sp):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    z = np.load(AUS / f"{form}.npz"); X, Q = z["X"][-1], z["Q"][-1]; vmax = np.percentile(Q, 99)
    nrm = plt.Normalize(0, vmax); fc = plt.cm.inferno(nrm(Q))
    ansichten = (("schraeg", 30, 25), ("draufsicht", 89, -90), ("seitlich", 3, 0))
    for nm, el, az in ansichten:
        fig = plt.figure(figsize=(10, 8)); A = fig.add_subplot(111, projection="3d")
        A.plot_surface(X[..., 0], X[..., 1], X[..., 2], facecolors=fc, rstride=1, cstride=1, linewidth=0, shade=False, antialiased=False)
        for g, gam in sp:
            A.plot(gam[:, 0], gam[:, 1], gam[:, 2], color=FARBEN[g], lw=1.3)
        A.set_box_aspect((np.ptp(X[..., 0]), np.ptp(X[..., 1]), max(np.ptp(X[..., 2]), 0.3 * np.ptp(X[..., 0]))))
        A.view_init(elev=el, azim=az); A.set_axis_off()
        fig.colorbar(plt.cm.ScalarMappable(norm=nrm, cmap="inferno"), ax=A, shrink=0.5, label="lokaler QI-Wert (Mittel über die Fläche = QI)")
        for g in range(5 if sp else 0):
            A.plot([], [], color=FARBEN[g], label=f"Spule S{g + 1} (mit 7 Symmetrie-Kopien)")
        if sp:
            A.legend(loc="upper left", fontsize=8)
        A.set_title(f"{FORMEN[form]}, Plasmarand (QI {j['qi_flaeche'][-1]:.2e}), Ansicht {nm}", fontsize=10)
        fig.savefig(AUS / f"qi_3d_{form}_{nm}.png", dpi=110, bbox_inches="tight"); plt.close(fig)
    # Querschnitte bei drei Toroidalwinkeln: Flaechen s als Ringe, Farbe = lokaler QI-Wert, Spulen-Durchstosspunkte
    Xa, Qa = z["X"], z["Q"]; nfp = j["nfp"]
    fig, ax = plt.subplots(1, 3, figsize=(15, 6), constrained_layout=True)
    for A, pw in zip(ax, (0.0, np.pi / nfp / 2, np.pi / nfp)):
        for i in range(len(j["s"])):
            P = Xa[i]; phz = np.mod(np.arctan2(P[..., 1], P[..., 0]), 2 * np.pi)
            m = np.abs(np.angle(np.exp(1j * (phz - pw)))) < np.pi / nfp / 30
            A.scatter(np.hypot(P[..., 0], P[..., 1])[m], P[..., 2][m], c=Qa[i][m], cmap="inferno", vmin=0, vmax=vmax, s=6)
        for g, gam in sp:
            phz = np.mod(np.arctan2(gam[:, 1], gam[:, 0]), 2 * np.pi); d = np.angle(np.exp(1j * (phz - pw)))
            k = np.where(np.diff(np.sign(d)) != 0)[0]
            for kk in k:
                if abs(d[kk]) < 0.3:
                    A.plot(np.hypot(gam[kk, 0], gam[kk, 1]), gam[kk, 2], "o", color=FARBEN[g], ms=7, mec="k")
        A.set_aspect("equal"); A.set_title(f"Schnitt φ = {np.degrees(pw):.1f}°", fontsize=10); A.set_xlabel("R"); A.set_ylabel("Z")
    fig.colorbar(plt.cm.ScalarMappable(norm=nrm, cmap="inferno"), ax=ax, shrink=0.7, label="lokaler QI-Wert")
    fig.suptitle(f"{FORMEN[form]}: Querschnitte, Ringe = Flächen s = {', '.join(f'{x:.2f}' for x in j['s'])}; Kreise = Spulen-Durchstoßpunkte", fontsize=10)
    fig.savefig(AUS / f"qi_3d_{form}_querschnitt.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    form = sys.argv[1]
    j = json.loads((AUS / f"{form}.json").read_text()) if (AUS / f"{form}.json").exists() else rechnen(form)
    sp = spulen_dje() if form == "dje" else []
    html(form, j, sp); bilder(form, j, sp); print(json.dumps(j, indent=1))
