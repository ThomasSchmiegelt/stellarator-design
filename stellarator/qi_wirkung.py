"""Wirkungskarte: ortsaufgeloeste Wirkung jeder Spulengruppe auf den lokalen QI-Wert (DjLe3eL6, Proxima-Spulen).

Nutzer-Beobachtung 2026-11-05: QI ist auf der Flaeche deutlich zu sehen und scheint mit den Spulen zusammenzuhaengen;
Werte mit den Spulen und ihrer Position in Verbindung bringen. Ereignisprotokoll F-248.

Aufruf (aus ~/hermes/fusion, im Scope, hoechstens 1 parallel):
  systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 --description="hermes python qi_wirkung rechnen" \
      env OMP_NUM_THREADS=2 .venv-constellaration/bin/python -m stellarator.qi_wirkung rechnen
  ... qi_wirkung geometrie | auswertung | opt | bilder | html

Verfahren:
  1. Weg (ii) aus stellarator/qi_spulen.py (Modell2): Boozer-Flaechen der offiziellen Rechnung (fest), |B| der Spulen je
     Gruppe (Basisspule + 7 Symmetrie-Kopien) fuer 1 A, Ströme kalibriert; QI mit der Paketfunktion je Flaeche (s = 0,5, Rand).
  2. Lokaler QI-Wert wie stellarator/qi_3d.py: Residuen r (75 Feldlinien x 2000 Winkel), q = r^2 * N, linear auf ein
     regelmaessiges Gitter (theta_B, phi_B) ueber eine Periode interpoliert (Mittel von q = QI der Flaeche).
  3. Faelle: basis, fest (|B| der VMEC-Rechnung = ohne Spulen), je Gruppe Strom x0,95 und x1,05, je Gruppe 5 mm Verschiebung
     (radial r, toroidal t, senkrecht z; +-). Jeder Fall wird sofort als npz gespeichert, Neustart ueberspringt Fertiges.
  4. Geometrie: Ort jedes Gitterpunkts (Boozer-Reihen R, Z, nu), kuerzester Abstand zu jeder Gruppe (8 Kopien), Spulenspur
     und Naechst-/Kruemmungsstellen auf der Abwicklung.
  5. Auswertung: Wirkungskarte W_g = (q(+5 %) - q(-5 %)) / 10 je 1 % Strom, in Einheiten des Flaechen-QI;
     Rangkorrelation |W_g| gegen 1/Abstand; lineares Antwortmodell mit Kreuzvalidierung nach Toroidalwinkel-Bloecken
     (Bloecke in der gefalteten halben Periode, damit Stellarator-Spiegelpunkte nicht in Lern- und Pruefmenge zugleich liegen).
     Naht des QI-Verfahrens (Fensteranfang phi_B = p0, +-3 Grad) wird in allen Statistiken ausgeblendet.
Ergebnis: sim/qi_wirkung/
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUS = ROOT / "sim" / "qi_wirkung"
S_W = (0.5, 1.0)
NTH, NPH = 72, 90            # Analysegitter je Periode: 5 Grad poloidal, 1 Grad toroidal
NAHT_GRAD = 3.0
MM = 5.0


def _modell():
    sys.path.insert(0, str(ROOT))
    from stellarator.qi_spulen import Modell2
    return Modell2(s=S_W)


class Lokal:
    """Lokaler QI-Wert auf dem Gitter fuer ein Modell2 (feste Flaechen)."""

    def __init__(self, M):
        from scipy import interpolate
        from constellaration.omnigeneity import qi
        self.M = M; bz = M.bz; self.qs = qi.QISettings(); self.nfp = bz.n_field_periods
        self.N = self.qs.n_field_lines * self.qs.n_output_toroidal_points
        self.p0 = np.pi / self.nfp if bz.bmnc[1, 1] < 0 else 0.0
        self.phB_l = np.linspace(self.p0, self.p0 + 2 * np.pi / self.nfp, self.qs.n_output_toroidal_points)
        self.iota = interpolate.UnivariateSpline(bz.normalized_toroidal_flux, bz.iota, k=1, s=0)(bz.boozer_normalized_toroidal_flux)
        th = np.linspace(0, 2 * np.pi, NTH, endpoint=False); ph = self.p0 + np.linspace(0, 2 * np.pi / self.nfp, NPH, endpoint=False) + np.pi / self.nfp / NPH
        self.TH, self.PH = np.meshgrid(th, ph, indexing="ij")

    def aufs_gitter(self, werte, js, TH=None, PH=None):
        from scipy.interpolate import RegularGridInterpolator
        TH = self.TH if TH is None else TH; PH = self.PH if PH is None else PH
        f = RegularGridInterpolator((np.arange(self.qs.n_field_lines), self.phB_l), werte)
        phr = self.p0 + np.mod(PH - self.p0, 2 * np.pi / self.nfp)
        al = np.mod(TH - self.iota[js] * (phr - self.p0), 2 * np.pi) / (2 * np.pi) * (self.qs.n_field_lines - 1)
        return f(np.stack([np.clip(al, 0, self.qs.n_field_lines - 1), np.clip(phr, self.phB_l[0], self.phB_l[-1])], -1))

    def bz_mit(self, faktoren=None, Bg=None, vmec_feld=False, flaechen=None):
        M = self.M; I = M.I0 * (np.ones(5) if faktoren is None else np.asarray(faktoren, float)); Bg = M.Bg if Bg is None else Bg
        bm = M.bz.bmnc_b.copy()
        for js in (flaechen if flaechen is not None else range(M.bz.n_boozer_flux_surfaces)):
            modb = M.C @ M.bz.bmnc_b[:, js] if vmec_feld else np.linalg.norm(np.tensordot(I, Bg[js], 1), axis=1)
            bm[:, js] = M.pinv @ modb
        return M.bz.model_copy(update={"bmnc_b": bm})

    def residuen(self, bz2, js):
        from constellaration.omnigeneity import qi
        sys.path.insert(0, str(ROOT))
        from stellarator.qi_karte import ausschnitt
        return qi.quasi_isodynamicity_residual(ausschnitt(bz2, js), self.qs).residuals[0]

    def fall(self, **kw):
        bz2 = self.bz_mit(**kw); out = {}
        for js in range(self.M.bz.n_boozer_flux_surfaces):
            r = self.residuen(bz2, js); q = r ** 2 * self.N
            out[f"q{js}"] = self.aufs_gitter(q, js).astype(np.float32); out[f"r{js}"] = self.aufs_gitter(r * np.sqrt(self.N), js).astype(np.float32)
            out[f"qi{js}"] = float(q.mean())
        return out


def faelle():
    F = {"basis": {}, "fest": {"vmec_feld": True}}
    for g in range(5):
        for f in (0.95, 1.05):
            v = [1.0] * 5; v[g] = f; F[f"I_S{g + 1}_{f}"] = {"faktoren": v}
        for art in ("r", "t", "z"):
            for vz in (1, -1):
                F[f"L_S{g + 1}_d{art}_{'+' if vz > 0 else '-'}{MM:g}mm"] = {"lage": [g, art, vz]}
    return F


def rechnen(nur=None):
    sys.path.insert(0, str(ROOT))
    from stellarator.qi_spulen import MASSSTAB_M, spiegel, verschoben
    (AUS / "faelle").mkdir(parents=True, exist_ok=True)
    F = faelle(); offen = [n for n in F if not (AUS / "faelle" / f"{n}.npz").exists() and (nur is None or n in nur)]
    print("offen:", len(offen), "von", len(F), flush=True)
    if not offen:
        return
    t0 = time.time(); M = _modell(); L = Lokal(M); print("Modell bereit", f"{time.time() - t0:.0f} s", flush=True)
    for n in offen:
        t1 = time.time(); spec = F[n]; extra = {}
        if "lage" in spec:
            from simsopt.field import BiotSavart, Current, coils_via_symmetries
            g, art, vz = spec["lage"]; d = MM / 1000 / MASSSTAB_M; v = [0.0, 0.0, 0.0]; v["rtz".index(art)] = vz * d
            kn = verschoben(M.kurven[g], {"d_rtz": v}); Bg = []
            for js, X in enumerate(M.xyz):
                bs = BiotSavart(coils_via_symmetries([kn], [Current(1.0)], M.nfp, True)); bs.set_points(np.ascontiguousarray(X))
                B = M.Bg[js].copy(); B[g] = bs.B(); Bg.append(B)
            o = L.fall(Bg=Bg); B0 = M.Bg; M.Bg = Bg; extra["spiegel"] = spiegel(M, np.ones(5)); M.Bg = B0
            extra["verschiebung_mm"] = float(np.linalg.norm(kn.gamma() - M.kurven[g].gamma(), axis=1).max() * MASSSTAB_M * 1000)
        else:
            o = L.fall(faktoren=spec.get("faktoren"), vmec_feld=spec.get("vmec_feld", False))
            if not spec.get("vmec_feld"):
                extra["spiegel"] = spiegel(M, spec.get("faktoren", np.ones(5)))
        np.savez_compressed(AUS / "faelle" / f"{n}.npz", **o, spec=json.dumps(spec), extra=json.dumps(extra))
        print(n, [round(o[f"qi{j}"], 8) for j in range(len(S_W))], f"{time.time() - t1:.0f} s", flush=True)
    print("FERTIG rechnen", f"{time.time() - t0:.0f} s", flush=True)


def lade(n):
    z = np.load(AUS / "faelle" / f"{n}.npz"); return z


# ---------------------------------------------------------------- Geometrie
def geometrie():
    """Ort der Gitterpunkte, Abstand zu jeder Gruppe, Spulenspuren und Marken auf der Abwicklung."""
    datei = AUS / "geometrie.npz"
    if datei.exists():
        return dict(np.load(datei, allow_pickle=True))
    sys.path.insert(0, str(ROOT))
    from scipy.spatial import cKDTree
    from simsopt.field import Current, coils_via_symmetries
    from constellaration.geometry import surface_rz_fourier as srf
    from stellarator.qi_spulen import rand
    M = _modell(); L = Lokal(M); bz = M.bz; a = float(srf.evaluate_minor_radius(rand()))

    def ort(js, TH, PH):
        R = np.zeros(TH.shape); Z = np.zeros(TH.shape); nu = np.zeros(TH.shape)
        for i in range(TH.shape[0]):
            ang = bz.xm_b[:, None] * TH[i][None] - bz.xn_b[:, None] * PH[i][None]; c, s = np.cos(ang), np.sin(ang)
            R[i] = bz.rmnc_b[:, js] @ c; Z[i] = bz.zmns_b[:, js] @ s; nu[i] = bz.numns_b[:, js] @ s
        P = PH + M.vz * nu
        return np.stack([R * np.cos(P), R * np.sin(P), Z], -1)
    out = {"a": a, "p0": L.p0, "nfp": L.nfp, "TH": L.TH, "PH": L.PH, "s": np.array([float(x) for x in bz.boozer_normalized_toroidal_flux]),
           "I0": M.I0, "vz": M.vz}
    # ganzer Torus (fuer 3D und Marken)
    thv = np.linspace(0, 2 * np.pi, 73); phv = np.linspace(0, 2 * np.pi, L.nfp * 72 + 1); THv, PHv = np.meshgrid(thv, phv, indexing="ij")
    out["THv"], out["PHv"] = THv, PHv
    gruppen = [np.concatenate([c.curve.gamma() for c in coils_via_symmetries([k], [Current(1.0)], L.nfp, True)]) for k in M.kurven]
    kappa = [np.concatenate([c.curve.kappa() for c in coils_via_symmetries([k], [Current(1.0)], L.nfp, True)]) for k in M.kurven]
    nq = len(M.kurven[0].quadpoints)
    for js in range(len(S_W)):
        X = ort(js, L.TH, L.PH); out[f"X{js}"] = X
        out[f"d{js}"] = np.array([cKDTree(G).query(X.reshape(-1, 3))[0].reshape(X.shape[:2]) for G in gruppen])
        Xv = ort(js, THv, PHv); out[f"Xv{js}"] = Xv
        # Spulenspur und Marken auf der Abwicklung (phi_B mod Periode, theta_B) ueber den ganzen Torus
        baum = cKDTree(Xv.reshape(-1, 3)); phm = np.degrees(np.mod(PHv - L.p0, 2 * np.pi / L.nfp)).ravel() + np.degrees(L.p0); thm = np.degrees(np.mod(THv, 2 * np.pi)).ravel()
        spur, naechst, kruemm = [], [], []
        for g, G in enumerate(gruppen):
            d, i = baum.query(G)
            for c in range(len(G) // nq):
                sl = slice(c * nq, (c + 1) * nq); dd, ii, kk = d[sl], i[sl], kappa[g][sl]
                spur.append([g, phm[ii], thm[ii], dd / a])
                j = int(np.argmin(dd)); naechst.append([g, phm[ii[j]], thm[ii[j]], dd[j] / a])
                # staerkste Kruemmung im plasmanahen Teil (Abstand < 1,6 a)
                nah = dd < 1.6 * a
                if nah.any():
                    jk = int(np.flatnonzero(nah)[np.argmax(kk[nah])]); kruemm.append([g, phm[ii[jk]], thm[ii[jk]], kk[jk] * a, dd[jk] / a])
        out[f"spur{js}"] = np.array(spur, dtype=object); out[f"naechst{js}"] = np.array(naechst); out[f"kruemm{js}"] = np.array(kruemm)
    out["spulen"] = np.array([[g, c.curve.gamma()] for g, k in enumerate(M.kurven) for c in coils_via_symmetries([k], [Current(1.0)], L.nfp, True)], dtype=object)
    np.savez_compressed(datei, **out)
    return dict(np.load(datei, allow_pickle=True))


# ---------------------------------------------------------------- Auswertung
def maske(G):
    ph = np.degrees(G["PH"] - G["p0"]); per = 360 / int(G["nfp"])
    return (ph > NAHT_GRAD) & (ph < per - NAHT_GRAD)


def bloecke(G, n=5):
    """Toroidalwinkel-Bloecke in der gefalteten halben Periode (phi und Spiegelbild per - phi im selben Block)."""
    per = 360 / int(G["nfp"]); ph = np.mod(np.degrees(G["PH"] - G["p0"]), per); f = np.minimum(ph, per - ph)
    return np.minimum((f / (per / 2) * n).astype(int), n - 1)


def wirkung(js):
    """Wirkung je Gruppe je 1 % Strom (Einheit: QI der Flaeche im Grundzustand) und je 1 mm Lage (staerkste Richtung)."""
    b = lade("basis"); qi0 = float(b[f"qi{js}"]); W, WL, WLart = [], [], []
    for g in range(5):
        p, m = lade(f"I_S{g + 1}_1.05"), lade(f"I_S{g + 1}_0.95")
        W.append((p[f"q{js}"].astype(float) - m[f"q{js}"]) / 10 / qi0)
        best = None
        for art in "rtz":
            p, m = lade(f"L_S{g + 1}_d{art}_+{MM:g}mm"), lade(f"L_S{g + 1}_d{art}_-{MM:g}mm")
            w = (p[f"q{js}"].astype(float) - m[f"q{js}"]) / (2 * MM) / qi0
            if best is None or np.abs(w).mean() > np.abs(best[0]).mean():
                best = (w, art)
        WL.append(best[0]); WLart.append(best[1])
    return np.array(W), np.array(WL), WLart, qi0


def r2(y, yh):
    return float(1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def cv_r2(X, y, gruppe):
    """R2 aus Vorhersagen fuer zurueckgehaltene Gruppen (lineare kleinste Quadrate mit Achsenabschnitt)."""
    X1 = np.c_[np.ones(len(y)), X]; yh = np.empty_like(y)
    for k in np.unique(gruppe):
        t = gruppe == k; c = np.linalg.lstsq(X1[~t], y[~t], rcond=None)[0]; yh[t] = X1[t] @ c
    return r2(y, yh)


def auswertung():
    from scipy.stats import spearmanr
    G = geometrie(); a = float(G["a"]); mk = maske(G).ravel(); blk = bloecke(G).ravel()
    rng = np.random.default_rng(1); zufall = rng.integers(0, 5, mk.sum())
    erg = {"maske_anteil": float(mk.mean()), "naht_grad": NAHT_GRAD, "flaechen": {}}
    per = 360 / int(G["nfp"]); phg = np.degrees(G["PH"][0] - G["p0"])
    for js, s in enumerate(G["s"]):
        W, WL, WLart, qi0 = wirkung(js); d = G[f"d{js}"] / a; E = {"s": float(s), "qi_basis": qi0, "gruppen": {}}
        b, fe = lade("basis"), lade("fest"); qb = b[f"q{js}"].astype(float); qf = fe[f"q{js}"].astype(float); delta = (qb - qf) / qi0
        E["qi_fest"] = float(fe[f"qi{js}"]); E["qi_gitter_basis"] = float(qb.mean()); E["qi_gitter_fest"] = float(qf.mean())
        for g in range(5):
            w = W[g].ravel()[mk]; wl = WL[g].ravel()[mk]; dg = d[g].ravel()[mk]
            # theta-gemittelte Wirkung je Toroidalwinkel gegen kleinsten Abstand je Toroidalwinkel
            prof = np.abs(W[g]).mean(0); dmin = d[g].min(0); ok = maske(G)[0]
            # Linearmodell |W_g| ~ a + b d^-p, Block-CV
            cvs = {f"p{p}": cv_r2((dg ** -p)[:, None], np.abs(w), blk[mk]) for p in (1, 3, 6)}
            fit = {f"p{p}": r2(np.abs(w), np.c_[np.ones(len(w)), dg ** -p] @ np.linalg.lstsq(np.c_[np.ones(len(w)), dg ** -p], np.abs(w), rcond=None)[0]) for p in (1, 3, 6)}
            E["gruppen"][f"S{g + 1}"] = {
                "summe_W_mittel": float(W[g].mean()), "betrag_W_mittel": float(np.abs(W[g]).mean()), "W_p99": float(np.percentile(np.abs(W[g]), 99)),
                "anteil_positiv": float((W[g] > 0).mean()),
                "spearman_absW_inv_abstand": float(spearmanr(np.abs(w), 1 / dg)[0]), "spearman_W_inv_abstand": float(spearmanr(w, 1 / dg)[0]),
                "spearman_profil_absW_inv_dmin_je_grad": float(spearmanr(prof[ok], 1 / dmin[ok])[0]),
                "spearman_lage_absW_inv_abstand": float(spearmanr(np.abs(wl), 1 / dg)[0]), "lage_staerkste_richtung": WLart[g],
                "lage_betrag_W_mittel_je_mm": float(np.abs(WL[g]).mean()),
                "phi_max_wirkung_grad": float(phg[ok][np.argmax(prof[ok])]), "phi_min_abstand_grad": float(phg[ok][np.argmin(dmin[ok])]),
                "abstand_min_a": float(d[g].min()), "r2_fit_absW": fit, "r2_blockcv_absW": cvs,
                "anteil_wirkung_naechstes_viertel": float(np.abs(w)[dg <= np.percentile(dg, 25)].sum() / np.abs(w).sum())}
        # Zusatzfehler-Modell: delta ~ c + sum_g a_g d_g^-p
        y = delta.ravel()[mk]; dd = np.array([d[g].ravel()[mk] for g in range(5)]).T; zm = {}
        for p in (1, 3, 6):
            X = dd ** -p; X1 = np.c_[np.ones(len(y)), X]; c = np.linalg.lstsq(X1, y, rcond=None)[0]
            zm[f"p{p}"] = {"r2_fit": r2(y, X1 @ c), "r2_blockcv": cv_r2(X, y, blk[mk]), "r2_zufallcv": cv_r2(X, y, zufall), "a_g": c[1:].tolist()}
        # Gegenprobe: dasselbe mit der Summe der Stromwirkungen (linear, physikalisch statt Abstand)
        Xw = np.array([W[g].ravel()[mk] for g in range(5)]).T
        zm["stromwirkung_als_merkmal"] = {"r2_fit": r2(y, np.c_[np.ones(len(y)), Xw] @ np.linalg.lstsq(np.c_[np.ones(len(y)), Xw], y, rcond=None)[0]),
                                          "r2_blockcv": cv_r2(Xw, y, blk[mk]), "r2_zufallcv": cv_r2(Xw, y, zufall)}
        E["zusatzfehler_modell"] = zm
        E["zusatzfehler"] = {"mittel": float(delta.mean()), "anteil_positiv": float((delta > 0).mean()),
                             "spearman_inv_dmin_alle": float(spearmanr(delta.ravel()[mk], 1 / d.min(0).ravel()[mk])[0])}
        for g in range(5):
            E["zusatzfehler"][f"spearman_inv_d_S{g + 1}"] = float(spearmanr(delta.ravel()[mk], 1 / d[g].ravel()[mk])[0])
        # (c) hellste Flecken: oberste 2 % von q (mit Spulen) - Lage gegen kleinsten Spulenabstand
        dmin_all = d.min(0); ql = qb.ravel()[mk]; hell = ql >= np.percentile(ql, 98); dm = dmin_all.ravel()[mk]
        from scipy.stats import percentileofscore
        nst = G[f"naechst{js}"]
        def winkelabst(ph, th):                                   # Abstand (Grad, Abwicklung) zur naechsten Naechst-Marke
            dp = np.abs(((ph[:, None] - nst[None, :, 1].astype(float)) + per / 2) % per - per / 2)
            dt = np.abs(((th[:, None] - nst[None, :, 2].astype(float)) + 180) % 360 - 180)
            return np.hypot(dp, dt).min(1)
        ph_all = np.degrees(G["PH"]).ravel()[mk]; th_all = np.degrees(G["TH"]).ravel()[mk]
        wa_h = winkelabst(ph_all[hell], th_all[hell]); wa_alle = winkelabst(ph_all, th_all)
        hz = {"abstand_median_hell_a": float(np.median(dm[hell])), "abstand_median_alle_a": float(np.median(dm)),
              "perzentil_abstand_hell": float(percentileofscore(dm, np.median(dm[hell]))),
              "anteil_hell_im_naechsten_zehntel": float((dm[hell] <= np.percentile(dm, 10)).mean()),
              "winkelabstand_zur_naechstmarke_hell_median_grad": float(np.median(wa_h)), "winkelabstand_alle_median_grad": float(np.median(wa_alle)),
              "phi_hellster_punkt_grad": float(ph_all[np.argmax(ql)]), "theta_hellster_punkt_grad": float(th_all[np.argmax(ql)])}
        dl = delta.ravel()[mk]; hz2 = dl >= np.percentile(dl, 98)
        hz.update(zusatz_hell_abstand_median_a=float(np.median(dm[hz2])), zusatz_hell_perzentil_abstand=float(percentileofscore(dm, np.median(dm[hz2]))),
                  zusatz_hell_winkelabstand_median_grad=float(np.median(winkelabst(ph_all[hz2], th_all[hz2]))))
        # Gruppen-spezifisch: am naechsten zur Fleckmitte
        # welche Gruppe hat die naechste Naechst-Marke zu den hellen Flecken
        dpm = np.abs(((ph_all[hell][:, None] - nst[None, :, 1].astype(float)) + per / 2) % per - per / 2)
        dtm = np.abs(((th_all[hell][:, None] - nst[None, :, 2].astype(float)) + 180) % 360 - 180)
        wer = nst[np.argmin(np.hypot(dpm, dtm), 1), 0].astype(int)
        hz["naechste_marke_gruppe_anteile"] = {f"S{g + 1}": float((wer == g).mean()) for g in range(5)}
        hz["naechste_gruppe_abstand_anteile"] = {f"S{g + 1}": float((np.argmin(d[:, :, :].reshape(5, -1)[:, mk][:, hell], 0) == g).mean()) for g in range(5)}
        E["helle_flecken"] = hz
        # Wirkung auf den vorzeichenbehafteten Restfehler (linear im Feld, ohne Verstaerkung durch das Quadrat)
        r0 = b[f"r{js}"].astype(float); E["restfehler"] = {"spearman_absW_q_gegen_abs_r0": {}}
        for g in range(5):
            p, m = lade(f"I_S{g + 1}_1.05"), lade(f"I_S{g + 1}_0.95"); wr = (p[f"r{js}"].astype(float) - m[f"r{js}"]) / 10 / np.sqrt(qi0)
            prof = np.abs(wr).mean(0); ok = maske(G)[0]; dmin = d[g].min(0)
            E["restfehler"][f"S{g + 1}"] = {"spearman_abs_dr_inv_abstand": float(spearmanr(np.abs(wr.ravel()[mk]), 1 / d[g].ravel()[mk])[0]),
                                            "spearman_profil_inv_dmin": float(spearmanr(prof[ok], 1 / dmin[ok])[0]),
                                            "phi_max_grad": float(phg[ok][np.argmax(prof[ok])]), "betrag_mittel": float(np.abs(wr).mean()),
                                            "r2_blockcv_p3": cv_r2((d[g].ravel()[mk] ** -3)[:, None], np.abs(wr.ravel()[mk]), blk[mk])}
            E["restfehler"]["spearman_absW_q_gegen_abs_r0"][f"S{g + 1}"] = float(spearmanr(np.abs(W[g].ravel()[mk]), np.abs(r0.ravel()[mk]))[0])
        erg["flaechen"][f"s{float(s):.3f}"] = E
    # Lineare Ueberlagerung pruefen: Summe der Gruppenwirkungen
    (AUS / "auswertung.json").write_text(json.dumps(erg, indent=1)); print(json.dumps(erg, indent=1))
    return erg


# ---------------------------------------------------------------- gezielte Optimierung der schlechtesten Flecken
def opt():
    datei = AUS / "opt.json"
    E = json.loads(datei.read_text()) if datei.exists() else {}
    sys.path.insert(0, str(ROOT))
    from scipy.optimize import minimize
    from stellarator.qi_spulen import spiegel
    M = _modell(); L = Lokal(M); js = len(S_W) - 1
    qb = lade("basis")[f"q{js}"].astype(float); fl = qb >= np.percentile(qb[maske(geometrie())], 95); fl &= maske(geometrie())

    def bewerte(fk):
        bz2 = L.bz_mit(faktoren=fk, flaechen=[js]); r = L.residuen(bz2, js); q = r ** 2 * L.N; G = L.aufs_gitter(q, js)
        return float(G[fl].mean()), float(q.mean()), G
    if "basis" not in E:
        f, qi_, _ = bewerte(np.ones(5)); E["basis"] = {"faktoren": [1.0] * 5, "flecken": f, "qi_rand": qi_, "spiegel": spiegel(M, np.ones(5))}
        g = [1, 1.05, 1.015, 0.98, 0.95]; f, qi_, _ = bewerte(g); E["global_B053"] = {"faktoren": g, "flecken": f, "qi_rand": qi_, "spiegel": spiegel(M, g)}
        datei.write_text(json.dumps(E, indent=1)); print(E, flush=True)
    if "flecken_opt" not in E:
        verlauf = []

        def ziel(x):
            fk = np.r_[1.0, x]; f, qi_, _ = bewerte(fk); verlauf.append([*map(float, fk), f, qi_]); print("opt", np.round(fk, 4), f, qi_, flush=True)
            return f / E["basis"]["flecken"]
        r = minimize(ziel, np.ones(4), method="L-BFGS-B", bounds=[(0.95, 1.05)] * 4, options=dict(eps=2e-3, maxfun=80))
        fk = np.r_[1.0, r.x]; f, qi_, G = bewerte(fk)
        E["flecken_opt"] = {"faktoren": fk.tolist(), "flecken": f, "qi_rand": qi_, "spiegel": spiegel(M, fk), "nfev": int(r.nfev), "meldung": str(r.message), "verlauf": verlauf}
        np.savez_compressed(AUS / "opt_karte.npz", q=G.astype(np.float32), maske_flecken=fl)
        datei.write_text(json.dumps(E, indent=1))
    # QI auf s = 0,5 fuer die drei Stromsaetze (Preis innen)
    for k in ("basis", "global_B053", "flecken_opt"):
        if "qi_s05" not in E[k]:
            bz2 = L.bz_mit(faktoren=E[k]["faktoren"], flaechen=[0]); r = L.residuen(bz2, 0); E[k]["qi_s05"] = float((r ** 2).sum())
            if k == "global_B053":
                _, _, Gg = bewerte(E[k]["faktoren"]); np.savez_compressed(AUS / "opt_karte_global.npz", q=Gg.astype(np.float32))
    datei.write_text(json.dumps(E, indent=1)); print(json.dumps({k: {kk: v for kk, v in E[k].items() if kk != "verlauf"} for k in E}, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "rechnen":
        rechnen(sys.argv[2:] or None)
    elif c == "geometrie":
        geometrie()
    elif c == "auswertung":
        auswertung()
    elif c == "opt":
        opt()
    elif c == "bilder":
        from stellarator.qi_wirkung_bilder import bilder
        bilder()
    elif c == "html":
        from stellarator.qi_wirkung_bilder import html
        html()
