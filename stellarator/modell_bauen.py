"""modell_bauen.py — Stellarator-Modell: Spulenrohre (voller Ring), Plasma-LCFS, Vakuumgefaess (ANNAHME 0,15..0,25 m).
  .venv-opt/bin/python stellarator/modell_bauen.py <name> <satz_ordner> <ausgabe_ordner>
Rohre: PicoGK-STL der Basisspulen einer halben Periode (m), Symmetrie: Drehung 2*pi*k/nfp um z, Stellaratorsymmetrie
(x,y,z)->(x,-y,-z). Pruefung: Schwerpunkt jedes Rohrs gegen Spulenkurve aus biot_savart.json mal L (< 2 cm).
Gefaess: ANNAHME innen 0,15 m ueber Plasma, Wand 0,10 m, entlang der Flaechennormale."""
import json, sys
from pathlib import Path
import numpy as np, pyvista as pv, netCDF4 as nc
from scipy.spatial import cKDTree

SPALT, DICKE = 0.15, 0.10


def lies_stl(p):
    return pv.read(str(p))


def plasma_gitter(wout, L, nfp, nphi_p, nth):
    w = nc.Dataset(wout)
    rm, zs = w["rmnc"][-1].data, w["zmns"][-1].data
    xm, xn = w["xm"][:].data, w["xn"][:].data
    assert int(w["lasym__logical__"][:]) == 0
    N = nphi_p * nfp
    ph = np.arange(N) * 2 * np.pi / N; th = np.arange(nth) * 2 * np.pi / nth
    R = np.empty((N, nth)); Z = np.empty((N, nth))
    for i in range(N):
        arg = xm[None, :] * th[:, None] - xn[None, :] * ph[i]
        R[i] = np.cos(arg) @ rm; Z[i] = np.sin(arg) @ zs
    X = np.stack([R * np.cos(ph)[:, None], R * np.sin(ph)[:, None], Z], -1) * L
    return X, w["Aminor_p"][:].item() * L


def normalen(X):
    dph = (np.roll(X, -1, 0) - np.roll(X, 1, 0)); dth = (np.roll(X, -1, 1) - np.roll(X, 1, 1))
    n = np.cross(dph, dth); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    # nach aussen: Gegen den Kreis um die Achse
    R = np.hypot(X[..., 0], X[..., 1]); Rm = R.mean()
    c = np.stack([X[..., 0] / R * Rm, X[..., 1] / R * Rm, 0 * R], -1)
    if (n * (X - c)).sum() < 0: n = -n
    return n


def torus_netz(X, flip=False):
    N, M, _ = X.shape
    i, j = np.meshgrid(np.arange(N), np.arange(M), indexing="ij")
    a = (i * M + j).ravel(); b = (((i + 1) % N) * M + j).ravel()
    c = (((i + 1) % N) * M + (j + 1) % M).ravel(); d = (i * M + (j + 1) % M).ravel()
    tri = np.concatenate([np.stack([a, b, c], 1), np.stack([a, c, d], 1)])
    if flip: tri = tri[:, ::-1]
    f = np.hstack([np.full((len(tri), 1), 3), tri]).ravel()
    return pv.PolyData(X.reshape(-1, 3).copy(), f)


def orient(m):
    """Normalen nach aussen (positives Volumen)."""
    if m.volume < 0: m = pv.PolyData(m.points, np.hstack([np.full((m.n_cells, 1), 3), m.regular_faces[:, ::-1]]).ravel())
    return m


def dicht(m):
    e = m.extract_feature_edges(boundary_edges=True, non_manifold_edges=True, feature_edges=False, manifold_edges=False)
    return {"offene_oder_nichtmannigfaltige_kanten": int(e.n_cells), "wasserdicht": e.n_cells == 0,
            "volumen_m3": float(abs(m.volume)), "dreiecke": int(m.n_cells)}


def main(name, satz, aus, nphi_p=240, nth=288):
    from simsopt import load
    satz, aus = Path(satz).resolve(), Path(aus).resolve(); aus.mkdir(parents=True, exist_ok=True)
    pr = json.loads((satz / "rohr" / "pruefung_rohr.json").read_text())
    L = pr["annahmen"]["massstab_m_je_einheit"]; a = json.loads((satz / "pruefung_satz.json").read_text())["a"]
    assert abs(L - 1.8 / a) / L < 0.02, (L, 1.8 / a)
    sp = json.loads((satz / "spulen.json").read_text()); nfp = int(sp["nfp"]); nb = len(sp["basis_x"])
    # --- Spulen
    tubes = [lies_stl(satz / "rohr" / f"S{i + 1}_glatt.stl") for i in range(nb)]
    pts0 = tubes[0].points; bm = float(np.abs(pts0).max())
    einh = 1e-3 if bm > 500 else 1.0   # PicoGK-STL in mm (Anlage R ~ 10..30 m) oder m
    for t in tubes: t.points = np.asarray(t.points) * einh
    kzt = {"punkte_boxmax_roh": bm, "einheit_faktor_nach_m": einh}
    bs = load(str(satz / "biot_savart.json")); coils = bs.coils
    curve_c = []
    for c in coils:
        g = c.curve.gamma() * L; seg = np.linalg.norm(np.roll(g, -1, 0) - g, axis=1)
        mid = 0.5 * (g + np.roll(g, -1, 0)); curve_c.append((mid * seg[:, None]).sum(0) / seg.sum())
    curve_c = np.array(curve_c)
    kopien, schwer = [], []
    Fz = np.diag([1., -1, -1])
    for t in tubes:
        P = np.asarray(t.points); F = t.regular_faces
        for flip in (False, True):
            for k in range(nfp):
                ph = 2 * np.pi * k / nfp; Rz = np.array([[np.cos(ph), -np.sin(ph), 0], [np.sin(ph), np.cos(ph), 0], [0, 0, 1]])
                M = Rz @ (Fz if flip else np.eye(3))
                Q = P @ M.T
                F2 = F[:, ::-1] if flip else F   # Spiegelung (det -1) dreht Umlaufsinn nicht, Drehung um x-Achse ist det +1
                F2 = F
                kopien.append((Q, F2))
                schwer.append(Q.mean(0))   # grob; genauer ueber Volumenschwerpunkt unten
    # Volumenschwerpunkt je Kopie
    def vschw(Q, F):
        a_, b_, c_ = Q[F[:, 0]], Q[F[:, 1]], Q[F[:, 2]]
        v = np.einsum("ij,ij->i", a_, np.cross(b_, c_)) / 6.0
        cen = (a_ + b_ + c_) / 4.0
        return (cen * v[:, None]).sum(0) / v.sum()
    sw = np.array([vschw(Q, F) for Q, F in kopien])
    D = np.linalg.norm(sw[:, None, :] - curve_c[None, :, :], axis=2)
    nn = D.argmin(1); dmin = D.min(1)
    ok_eins = len(set(nn.tolist())) == len(kopien) == len(coils)
    print("Schwerpunkt-Abweichung max [cm]:", dmin.max() * 100, "eineindeutig:", ok_eins, "n", len(kopien), len(coils))
    schw_info = {"n_rohre": len(kopien), "n_spulen_bs": len(coils), "eineindeutig": bool(ok_eins),
                 "abw_schwerpunkt_max_cm": float(dmin.max() * 100), "abw_schwerpunkt_mittel_cm": float(dmin.mean() * 100),
                 "stl_box_max_roh": bm, "stl_faktor_nach_m": einh}
    if dmin.max() > 0.02 or not ok_eins:
        (aus / "kennzahlen.json").write_text(json.dumps({"STOPP": schw_info}, indent=1)); print("STOPP"); sys.exit(2)
    # Mesh der Kopien (volle Aufloesung fuer Abstandsmessung), dann reduziert zum Speichern
    full = [pv.PolyData(Q, np.hstack([np.full((len(F), 1), 3), F]).ravel()) for Q, F in kopien]
    print("Orientierung Volumen (erste 4):", [round(m.volume, 2) for m in full[:4]])
    full = [orient(m) for m in full]
    # --- Plasma + Gefaess
    X, a_m = plasma_gitter(satz / "frei" / "wout" / "k_n48000.nc", L, nfp, nphi_p, nth)
    N = normalen(X)
    plasma = orient(torus_netz(X)); gin = orient(torus_netz(X + SPALT * N)); gout = orient(torus_netz(X + (SPALT + DICKE) * N))
    # Gefaess = Schale: aussen nach aussen, innen nach innen (umgedreht)
    gi_flip = pv.PolyData(gin.points, np.hstack([np.full((gin.n_cells, 1), 3), gin.regular_faces[:, ::-1]]).ravel())
    gef = (gout + gi_flip).clean()
    # Offsettreue: Abstand der Offsetpunkte zu einem sehr dichten Plasmagitter
    Xd, _ = plasma_gitter(satz / "frei" / "wout" / "k_n48000.nc", L, nfp, 4 * nphi_p, 2 * nth)
    tr = cKDTree(Xd.reshape(-1, 3))
    d_in = tr.query(gin.points)[0]; d_out = tr.query(gout.points)[0]
    # Selbstdurchdringung: kleinster Kruemmungsradius-Test ueber Offsettreue; Abstand sollte = d (Gitter-Rest < ~1 cm)
    off = {"abstand_innen_min_m": float(d_in.min()), "abstand_innen_max_m": float(d_in.max()),
           "abstand_aussen_min_m": float(d_out.min()), "abstand_aussen_max_m": float(d_out.max()),
           "soll_innen_m": SPALT, "soll_aussen_m": SPALT + DICKE}
    sf = lambda m: int(m.n_cells) and None
    # Rohr-Gefaess
    allp = np.vstack([m.points for m in full]); lab = np.concatenate([np.full(m.n_points, i) for i, m in enumerate(full)])
    ptr = cKDTree(allp)
    dd, ii = ptr.query(gout.points); dd_i, _ = ptr.query(gef.points)
    # Rohr-Plasma
    dp, _ = ptr.query(plasma.points)
    # Durchdringung: Rohrpunkte im Gefaessvolumen (zwischen innen und aussen)?
    sub = allp[::7]
    def drin(m, pts):
        s = pv.PolyData(pts).select_enclosed_points(m, tolerance=0.0, check_surface=False)
        return np.asarray(s["SelectedPoints"]).astype(bool)
    in_aussen = drin(gout, sub); in_innen = drin(gin, sub)
    n_in_wand = int((in_aussen & ~in_innen).sum()); n_in_gef_ges = int(in_aussen.sum())
    # Gefaessumriss gegen Rohrflaeche sicher: Abstand der Oberflaechen ueber Mittellinie
    pruef = {"min_abstand_gefaess_aussen_zu_rohroberflaeche_m": float(dd.min()),
             "min_abstand_gefaess_alle_zu_rohroberflaeche_m": float(dd_i.min()),
             "min_abstand_plasma_zu_rohroberflaeche_m": float(dp.min()),
             "rohrpunkte_in_gefaesswand": n_in_wand, "rohrpunkte_innerhalb_aussenflaeche": n_in_gef_ges,
             "stichprobe_rohrpunkte": int(len(sub)), "durchdringung": bool(n_in_wand > 0 or n_in_gef_ges > 0 or dd.min() <= 0.0)}
    spl = pv.PolyData(); 
    spulen_red = []
    for m in full:
        r = m.decimate(1 - 30000 / m.n_cells) if m.n_cells > 30000 else m
        spulen_red.append(r.clean())
    spulen = spulen_red[0].merge(spulen_red[1:]) if len(spulen_red) > 1 else spulen_red[0]
    # Abweichung der reduzierten Rohre
    dev = max(cKDTree(m.points).query(r.points)[0].max() for m, r in zip(full[:4], spulen_red[:4]))
    kenn = {"name": name, "satz": str(satz), "nfp": nfp, "massstab_m_je_einheit": L, "a_m": a_m,
            "ANNAHME_gefaess": {"innen_ueber_plasma_m": SPALT, "wand_m": DICKE, "aussen_ueber_plasma_m": SPALT + DICKE},
            "rohr_durchmesser_m": pr["annahmen"]["rohr_d_m"], "symmetrie_pruefung": schw_info,
            "offset_pruefung": off, "abstaende_und_durchdringung": pruef,
            "wasserdicht": {"plasma": dicht(plasma), "gefaess": dicht(gef),
                            "rohre_je_rohr": [dicht(m)["wasserdicht"] for m in full].count(True), "rohre_gesamt": len(full)},
            "spulen_stl_reduziert_dreiecke_je_rohr": 30000, "reduktion_max_abw_m_erste4": float(dev),
            "bbox_gefaess_m": [float(x) for x in gef.bounds]}
    for nm, m in (("plasma", plasma), ("gefaess", gef), ("spulen", spulen)):
        m.save(str(aus / f"{nm}.stl"), binary=True)
    (aus / "kennzahlen.json").write_text(json.dumps(kenn, indent=1)); print(json.dumps(kenn, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
