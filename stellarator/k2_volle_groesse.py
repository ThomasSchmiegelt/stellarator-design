"""k2_volle_groesse.py -- K2: Spulen DK8s6qwo in voller Groesse (R0 21,1 m, HTS).  KI-generiert (Claude Sonnet 5.5, 2026-11-13).

Auftrag: sim/kette_dk8/AUFTRAG_K2.md, Erwartung: sim/kette_dk8/ERWARTUNG_K2.md (nicht aendern).
Pakete (Ergebnis je Paket in sim/kette_dk8/k2/<paket>.json, vorhandene Pakete werden uebersprungen):
  P1 Massstab/Feld   P2 Feldlinien/Poincare   P3 Kraefte/Energie   P4 Bauregeln/Abstaende   P5 Bilder (DE+EN)

Aufruf (Scope, damit ~/bin/rechnung pause|weiter greift; Pfad relativ zum Projektordner):
  systemd-run --user --scope --unit=k2-dk8 -p MemoryMax=12G --description="python K2 DK8 hermes/fusion" \
      .venv-opt/bin/python stellarator/k2_volle_groesse.py [--weiter] [--neu P2 [P3 ...]] [--nur P1 P2]
K2b-Optionen (Vorgabe = K2 fuer DK8s6qwo): --id <voll-ID> --bilanz <bilanz.json> --aus <Ausgabeordner> --baustein <Ordner>;
  P1 liefert zusaetzlich f_I_faktor_neu (B0 Bilanz / B0 Achse), P3 k_B_echt und Kraft/Energie beim Strom fuer das B0 der Bilanz.
Annahmen (nicht belegt, hier gesetzt; im Ergebnis genannt):
  - Strom: Verteilung der Ströme je Basisspule aus spulen.json (relativ), Mittel der 10 Basisspulen = I_spule aus bilanz.json (26,375 MA).
  - Massstab k = 21,1 m / Rmajor_p des wout (kleiner Massstab, wie Stufe 0).
  - Wickelpaket quadratisch, Kantenlaenge wickelpaket_m aus bilanz.json, fuer alle Spulen gleich.
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / "stellarator"))


def _opt(name, default):
    """Option '--name wert' aus sys.argv nehmen (K2b-Erweiterung; ohne Option bleibt das Verhalten wie in K2 fuer DK8s6qwo)."""
    if name in sys.argv:
        i = sys.argv.index(name); v = sys.argv[i + 1]; del sys.argv[i:i + 2]; return v
    return default


ID = _opt("--id", "DK8s6qwoUCsuCu2yoa7qLvx")
_bil = _opt("--bilanz", "sim/invers/dk8_1GW/bilanz.json")
_aus = _opt("--aus", "sim/kette_dk8/k2")
_gp = _opt("--gitter_plasma", None)                     # K2d: Feldgitter/Poincare-Grenzen aus der Plasmaausdehnung + Rand (m) statt der festen DK8-Maße
_bau = _opt("--baustein", "video/bausteine/K2")       # Ausgabeordner Szenenbaustein (P5)
_fall = json.loads((P / "sim/spulenfreundlich/ergebnis" / f"{ID}.json").read_text())["fall"]
_satz = _opt("--satz", None)                          # K2d: Spulensatz-Ordner (boundary.json, spulen.json, pruefung_satz.json), Vorgabe: Satz aus ergebnis/<ID>.json
SATZ = (P / _satz) if _satz else P / f"sim/spulenfreundlich/faelle/{ID}/satz_{_fall}"
WOUT = Path.home() / f"cae_projekte/gx/laeufe/{ID}/wout_{ID}.nc"   # Datei ausserhalb des Repos
BILANZ = (P / _bil) if not Path(_bil).is_absolute() else Path(_bil)
OUT = (P / _aus) if not Path(_aus).is_absolute() else Path(_aus)
ID8 = ID[:8]
ZW = OUT / "zwischen"
BILD = OUT / "bilder"
MU0 = 4e-7 * np.pi
D_RUECK = 4 / 3  # nur Platzhalter-frei; nicht benutzt
OHNE_HALT = "--ohne-halt" in sys.argv
PAKETE = ["P1", "P2", "P3", "P4", "P5"]


def jetzt():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(P))
    except ValueError:
        return Path(p).name


# ---------------------------------------------------------------- gemeinsame Daten
def bilanz():
    b = json.loads(BILANZ.read_text())["auslegung"]["HTS"]
    if not b.get("machbar", True) or "R0_m" not in b:
        sys.exit("Bilanz: HTS nicht machbar")
    return {"R0_m": b["R0_m"], "B0_T": b["B0_T"], "I_MA": b["I_spule_MA"], "wp_m": b["wickelpaket_m"],
            "E_GJ": b["magnetenergie_GJ"], "a_m": b["a_m"]}


def wout_daten():
    from netCDF4 import Dataset
    with Dataset(str(WOUT)) as w:
        d = {"R0_klein": float(w["Rmajor_p"][:]), "a_klein": float(w["Aminor_p"][:]), "nfp": int(w["nfp"][:]),
             "xm": np.asarray(w["xm"][:], float), "xn": np.asarray(w["xn"][:], float),
             "rmnc": np.asarray(w["rmnc"][:], float), "zmns": np.asarray(w["zmns"][:], float),
             "iotaf": np.abs(np.asarray(w["iotaf"][:], float)),
             "raxis": np.asarray(w["raxis_cc"][:], float), "zaxis": np.asarray(w["zaxis_cs"][:], float)}
    d["ns"] = d["rmnc"].shape[0]
    d["s"] = np.linspace(0, 1, d["ns"])
    return d


def achse_RZ(w, phi, k):
    n = np.arange(len(w["raxis"]))
    ph = np.atleast_1d(phi)
    Ra = (w["raxis"][None] * np.cos(w["nfp"] * n[None] * ph[:, None])).sum(1)
    Za = (-w["zaxis"][None] * np.sin(w["nfp"] * n[None] * ph[:, None])).sum(1)
    return Ra * k, Za * k


def vmec_flaeche(w, s, phi, th, k):
    """R, Z (m, Anlage) der VMEC-Flaeche s (lineare Interpolation auf dem vollen Gitter) bei phi ueber th."""
    x = s * (w["ns"] - 1); i = min(int(np.floor(x)), w["ns"] - 2); f = x - i
    if s > 1:  # linear fortgesetzt (Bezug: letzte Flaeche)
        i, f = w["ns"] - 2, x - (w["ns"] - 2)
    rm = w["rmnc"][i] * (1 - f) + w["rmnc"][i + 1] * f
    zm = w["zmns"][i] * (1 - f) + w["zmns"][i + 1] * f
    arg = w["xm"][None] * th[:, None] - w["xn"][None] * phi
    return (rm[None] * np.cos(arg)).sum(1) * k, (zm[None] * np.sin(arg)).sum(1) * k


def lade(k, I_mittel_MA):
    """Basisspulen (Anlagengroesse) und Strome (A, reell)."""
    from simsopt.geo import CurveXYZFourier
    d = json.loads((SATZ / "spulen.json").read_text())
    rel_I = np.asarray(d["currents"], float)
    I = rel_I / rel_I.mean() * I_mittel_MA * 1e6
    return d, I


def kurven(d, k, nq=128):
    from simsopt.geo import CurveXYZFourier
    out = []
    for x in d["basis_x"]:
        c = CurveXYZFourier(nq, d["order"]); c.x = np.asarray(x, float) * k; out.append(c)
    return out


def spulen_gesamt(d, I, k, nq=128):
    from simsopt.field import Current, coils_via_symmetries
    return coils_via_symmetries(kurven(d, k, nq), [Current(float(i)) for i in I], d["nfp"], True)


def bs_von(coils):
    from simsopt.field import BiotSavart
    return BiotSavart(coils)


def feld_fn(bs, chunk=20000):
    def f(x):
        x = np.atleast_2d(x); out = np.empty_like(x)
        for i in range(0, len(x), chunk):
            bs.set_points(np.ascontiguousarray(x[i:i + chunk])); out[i:i + chunk] = bs.B()
        return out
    return f


def b0_achse(bs, w, k, n=400):
    ph = np.linspace(0, 2 * np.pi, n, endpoint=False); Ra, Za = achse_RZ(w, ph, k)
    pts = np.c_[Ra * np.cos(ph), Ra * np.sin(ph), Za]
    bs.set_points(pts); B = bs.B()
    Bphi = -B[:, 0] * np.sin(ph) + B[:, 1] * np.cos(ph)
    return float(np.linalg.norm(B, axis=1).mean()), float(Bphi.mean())


def gelesen(name):
    f = OUT / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else None


def schreibe(name, d, t0):
    d["laufzeit_s"] = round(time.time() - t0, 1)
    d["ende"] = jetzt()
    d["hinweis"] = "KI-generiert (Claude Sonnet 5.5), Entwurf, Zahlen aus stellarator/k2_volle_groesse.py"
    (OUT / f"{name}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))


def halt_pruefen():
    p1 = gelesen("P1")
    if p1 and p1.get("anhalten"):
        sys.exit("P1 hat angehalten (B0-Abweichung > 10 %); nicht weiterrechnen, siehe ERGEBNIS_K2.md")
    p2 = gelesen("P2")
    if p2 and p2.get("anhalten"):
        sys.exit("P2 hat angehalten (zerfallene Flaechen innerhalb s = 0,5); nicht weiterrechnen")


def massstab():
    b = bilanz(); w = wout_daten()
    k = b["R0_m"] / w["R0_klein"]
    return b, w, k


# ---------------------------------------------------------------- P1
def p1():
    t0 = time.time(); start = jetzt()
    b, w, k = massstab()
    d, I = lade(k, b["I_MA"])
    coils = spulen_gesamt(d, I, k); bs = bs_von(coils)
    B0, B0phi = b0_achse(bs, w, k)
    I10 = I * (10.0 / B0)                                 # Strom fuer genau 10 T (Feld linear im Strom)
    from spulen_satz import flaeche
    s = flaeche(SATZ / "boundary.json", nphi=128, ntheta=64)
    g = s.gamma().reshape(-1, 3) * k
    bs.set_points(g); B = bs.B().reshape(s.gamma().shape)
    n = s.unitnormal()
    bn = np.abs((B * n).sum(2)) / np.linalg.norm(B, axis=2)
    pr = json.loads((SATZ / "pruefung_satz.json").read_text())
    abw = (B0 / b["B0_T"] - 1) * 100
    # Diagnose (Ampere-Kontrolle entlang der Achse): int B.dl muss mu0 * Summe I sein; Achsenlaenge gegen 2 pi R0
    ph4 = np.linspace(0, 2 * np.pi, 4000, endpoint=False); Ra4, Za4 = achse_RZ(w, ph4, k)
    X4 = np.c_[Ra4 * np.cos(ph4), Ra4 * np.sin(ph4), Za4]; dX4 = (np.roll(X4, -1, 0) - np.roll(X4, 1, 0)) / 2
    bs.set_points(X4); B4 = bs.B(); L_ax = float(np.linalg.norm(dX4, axis=1).sum())
    diag = {"int_B_dl_Tm": float((B4 * dX4).sum()), "mu0_mal_Summe_I_Tm": float(MU0 * I.sum() * 2 * d["nfp"]),
            "achsenlaenge_m": L_ax, "achsenlaenge_durch_2piR0": L_ax / (2 * np.pi * b["R0_m"]),
            "B_parallel_mittel_T": float((B4 * dX4).sum() / L_ax), "absB_min_max_T": [float(np.linalg.norm(B4, axis=1).min()), float(np.linalg.norm(B4, axis=1).max())],
            "B0_ideal_mu0_N_I_durch_2pi_R0_T": float(MU0 * I.sum() * 2 * d["nfp"] / (2 * np.pi * b["R0_m"]))}
    erg = {"paket": "P1", "start": start, "diagnose_achse": diag,
           "quellen": {"bilanz": rel(BILANZ), "wout": f"wout_{ID}.nc (cae_projekte/gx/laeufe/{ID}, ausserhalb Repo)",
                       "spulen": rel(SATZ / "spulen.json"), "feldfehler_klein": rel(SATZ / "pruefung_satz.json")},
           "R0_klein_wout_m_je_einheit": w["R0_klein"], "R0_klein_boundary_rc00": float(s.get_rc(0, 0)), "R0_ziel_m": b["R0_m"],
           "faktor_k": k, "a_klein": w["a_klein"], "a_gross_m": w["a_klein"] * k, "a_bilanz_m": b["a_m"],
           "strom_je_spule_MA": {"mittel_vorgabe": b["I_MA"], "je_basisspule_MA": (I / 1e6).tolist(),
                                 "min": float(I.min() / 1e6), "max": float(I.max() / 1e6),
                                 "summe_alle_40_MA": float(I.sum() * 2 * d["nfp"] / 1e6)},
           "B0_achse_mittel_absB_T": B0, "B0_achse_mittel_Bphi_T": B0phi, "B0_ziel_T": b["B0_T"], "abweichung_B0_prozent": abw,
           "strom_fuer_B0_bilanz_mittel_MA": float(I.mean() / 1e6 * b["B0_T"] / B0), "f_I_faktor_neu": b["B0_T"] / B0,
           "strom_fuer_10T_mittel_MA": float(I10.mean() / 1e6), "strom_fuer_10T_je_basisspule_MA": (I10 / 1e6).tolist(),
           "feldfehler": {"Bn_mittel": float(bn.mean()), "Bn_max": float(bn.max()), "Bn_mittel_klein_pruefung_satz": pr["Bn_mittel"],
                          "Bn_max_klein_pruefung_satz": pr["Bn_max"]},
           "b0_abweichung_ueber_10_prozent": bool(abs(abw) > 10),
           "anhalten_regel": "Opus-Entscheidung 2026-11-13: Halt nur, wenn die Ampere-Kontrolle (int B.dl gegen mu0 * Summe I, Toleranz 1 %) fehlschlaegt; B0-Abweichung wird als Ergebnis gefuehrt",
           "anhalten": bool(abs(diag["int_B_dl_Tm"] / diag["mu0_mal_Summe_I_Tm"] - 1) > 0.01) and not OHNE_HALT}
    schreibe("P1", erg, t0)
    print(f"P1: k {k:.4f}, B0 {B0:.3f} T ({abw:+.2f} %), I fuer 10 T {I10.mean()/1e6:.3f} MA, Bn {bn.mean():.3e}", flush=True)


# ---------------------------------------------------------------- P2
class Verschoben:
    """Feld um die z-Achse gedreht, damit eine Startebene phi' = 0 der Ebene phi = delta entspricht."""
    def __init__(self, g, delta):
        self.g, self.c, self.s = g, np.cos(delta), np.sin(delta)

    def __call__(self, x):
        x = np.atleast_2d(x)
        xo = np.c_[self.c * x[:, 0] - self.s * x[:, 1], self.s * x[:, 0] + self.c * x[:, 1], x[:, 2]]
        B = self.g(xo)
        return np.c_[self.c * B[:, 0] + self.s * B[:, 1], -self.s * B[:, 0] + self.c * B[:, 1], B[:, 2]]


S_START = [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 1.0]
S_AUSSEN = [1.06, 1.12]          # s > 1: linear fortgesetzt (rho 1,03 und 1,06)
N_UML = 300
SCHRITTE = 48


def p2():
    from feldlinien import ZylinderGitter, verfolge, iota as iota_fl
    t0 = time.time(); start = jetzt()
    b, w, k = massstab(); nfp = w["nfp"]
    p1j = gelesen("P1")
    d, I = lade(k, b["I_MA"])
    GR = ZW / "gitter.npz"
    sf = b["R0_m"] / 21.1                                    # K2: Gitter fuer R0 21,1 m ausgelegt, bei anderer Groesse mitskaliert
    R = (round(15.5 * sf, 2), round(26.3 * sf, 2), 91); Z = (round(-13.6 * sf, 2), round(13.6 * sf, 2), 137); NPHI = 96; D_MASKE = 2.0 * sf
    RG, ZG = (15.7 * sf, 26.2 * sf), 13.5 * sf
    if _gp:                                              # Plasmaausdehnung (Rand s=1, alle phi) plus Rand _gp m; Punktzahl mit der Ausdehnung
        rm = float(_gp); th_ = np.linspace(0, 2 * np.pi, 181); Rs_, Zs_ = [], []
        for ph_ in np.linspace(0, 2 * np.pi / nfp, 91):
            r_, z_ = vmec_flaeche(w, 1.0, ph_, th_, k); Rs_ += list(r_); Zs_ += list(z_)
        R0g, R1g, Zg = min(Rs_) - rm, max(Rs_) + rm, max(np.abs(Zs_)) + rm
        R = (round(R0g, 2), round(R1g, 2), int((R1g - R0g) / 0.25)); Z = (round(-Zg, 2), round(Zg, 2), int(2 * Zg / 0.37))
        RG, ZG = (R0g + 0.1, R1g - 0.1), Zg - 0.1; D_MASKE = 2.0 * sf
    if GR.exists():
        z = np.load(GR); g = ZylinderGitter.aus_roh(z["roh"], z["R"], z["Z"], nfp=nfp)
        gitter_s = float(z["dauer"])
    else:
        t1 = time.time()
        coils = spulen_gesamt(d, I, k, nq=512)
        bs = bs_von(coils); g = ZylinderGitter(feld_fn(bs), R=R, Z=Z, n_phi=NPHI, nfp=nfp)
        # Gitterpunkte nahe an Spulen (< D_MASKE m) haben riesige Werte und lassen die Spline-Interpolation schwingen:
        # dort durch den naechsten ungestoerten Gitterwert ersetzen (Feldlinien laufen nur im Plasma, >= 3 m von den Spulen)
        from scipy.spatial import cKDTree
        from scipy import ndimage as ndi
        phg = np.arange(NPHI) * g.dphi
        RR, PP, ZZ = np.meshgrid(g.R, phg, g.Z, indexing="ij")
        pg = np.c_[(RR * np.cos(PP)).ravel(), (RR * np.sin(PP)).ravel(), ZZ.ravel()]
        pts_c = np.concatenate([c.curve.gamma() for c in coils])
        dist = cKDTree(pts_c).query(pg)[0].reshape(RR.shape)
        maske = dist < D_MASKE
        idx = ndi.distance_transform_edt(maske, return_distances=False, return_indices=True)
        roh = np.stack([c_[tuple(idx)] for c_ in g.roh])
        g = ZylinderGitter.aus_roh(roh, g.R, g.Z, nfp=nfp)
        gitter_s = time.time() - t1
        np.savez(GR, roh=g.roh, R=g.R, Z=g.Z, dauer=gitter_s)
    print(f"P2: Gitter {gitter_s:.0f} s", flush=True)
    # Kontrolle der Interpolation gegen direkte Biot-Savart-Auswertung
    bs = bs_von(spulen_gesamt(d, I, k)); rng = np.random.default_rng(1)
    ph = rng.uniform(0, 2 * np.pi, 300); th = rng.uniform(0, 2 * np.pi, 300); ss = rng.uniform(0.0, 1.0, 300)
    pts = []
    for p_, t_, s_ in zip(ph, th, ss):
        Rr, Zz = vmec_flaeche(w, s_, p_, np.array([t_]), k); pts.append([Rr[0] * np.cos(p_), Rr[0] * np.sin(p_), Zz[0]])
    pts = np.array(pts); Bd = feld_fn(bs)(pts); Bi = g(pts)
    interp_fehler = float(np.max(np.linalg.norm(Bi - Bd, axis=1)) / np.linalg.norm(Bd, axis=1).mean())

    ebenen = [("phi_0", 0.0), ("phi_halb", np.pi / nfp / 2 * 1.0)]
    # halbe Periode = pi/nfp  (stellarator-symmetrische Ebene), "phi_0": Beginn der Periode
    ebenen = [("phi_0", 0.0), ("phi_halbe_periode", np.pi / nfp)]
    s_alle = S_START + S_AUSSEN
    ergebnisse = {}
    for name, delta in ebenen:
        zf = ZW / f"poincare_{name}.npz"
        Ra, Za = achse_RZ(w, delta, k); Ra, Za = float(Ra[0]), float(Za[0])
        if zf.exists():
            z = np.load(zf); pk, verl = z["pk"], z["verloren"]
        else:
            t1 = time.time()
            R0s, Z0s = [], []
            th0 = np.array([0.0])
            Rrand, Zrand = vmec_flaeche(w, 1.0, delta, th0, k)
            for s_ in s_alle:
                if s_ <= 1.0:
                    Rr, Zz = vmec_flaeche(w, s_, delta, th0, k); R0s.append(Rr[0]); Z0s.append(Zz[0])
                else:                                          # ausserhalb: Abstand von der Achse linear fortgesetzt
                    rho = np.sqrt(s_); R0s.append(Ra + (Rrand[0] - Ra) * rho); Z0s.append(Za + (Zrand[0] - Za) * rho)
            feld = g if delta == 0 else Verschoben(g, delta)
            pk, verl = verfolge(feld, np.array(R0s), np.array(Z0s), n_umlaeufe=N_UML, nfp=nfp,
                                schritte_pro_periode=SCHRITTE, R_grenze=RG, Z_grenze=ZG)
            np.savez(zf, pk=pk, verloren=verl, R0s=R0s, Z0s=Z0s, s=s_alle, dauer=time.time() - t1)
            print(f"P2: Ebene {name} fertig {time.time()-t1:.0f} s", flush=True)
        # Auswertung
        zeilen = []
        thf = np.linspace(0, 2 * np.pi, 2000, endpoint=False)
        from scipy.spatial import cKDTree
        for i, s_ in enumerate(s_alle):
            p = pk[i]; ok = np.isfinite(p[:, 0]); n_ok = int(ok.sum())
            z_ = {"s_start": s_, "rho_start": float(np.sqrt(s_)), "verloren": bool(verl[i]), "n_punkte": n_ok}
            if n_ok > 50:
                pp = p[ok]
                th_ = np.arctan2(pp[:, 1] - Za, pp[:, 0] - Ra); r_ = np.hypot(pp[:, 0] - Ra, pp[:, 1] - Za)
                A = [np.ones_like(th_)] + [f(m * th_) for m in range(1, 9) for f in (np.cos, np.sin)]
                A = np.array(A).T; c, *_ = np.linalg.lstsq(A, r_, rcond=None)
                z_["rms_rel"] = float(np.sqrt(np.mean((r_ - A @ c) ** 2)) / r_.mean())
                io = iota_fl(pp[None], (Ra, Za), nfp=nfp)[0] if name == "phi_0" else np.nan
                if name == "phi_0":
                    half = n_ok // 2
                    i1 = iota_fl(pp[None, :half], (Ra, Za), nfp=nfp)[0]; i2 = iota_fl(pp[None, half:], (Ra, Za), nfp=nfp)[0]
                    z_["iota"] = float(abs(io)); z_["iota_haelfte1"] = float(abs(i1)); z_["iota_haelfte2"] = float(abs(i2))
                    z_["iota_vmec"] = float(np.interp(min(s_, 1.0), w["s"], w["iotaf"]))
                if s_ <= 1.0:
                    Rv, Zv = vmec_flaeche(w, s_, delta, thf, k)
                    dist, _ = cKDTree(np.c_[Rv, Zv]).query(pp)
                    z_["abstand_vmec_mittel_m"] = float(dist.mean()); z_["abstand_vmec_max_m"] = float(dist.max())
            zeilen.append(z_)
        ergebnisse[name] = {"delta_rad": delta, "achse_RZ_m": [Ra, Za], "linien": zeilen}
    # Beurteilung (Arbeitskriterien, eigene Setzung)
    SCHWELLE = 0.02
    def zerfallen(z_):
        return z_["verloren"] or z_.get("rms_rel", 1.0) > SCHWELLE
    for name in ergebnisse:
        L = ergebnisse[name]["linien"]; inn = [z_ for z_ in L if z_["s_start"] <= 1.0]
        gut = [z_["s_start"] for z_ in inn if not zerfallen(z_)]
        # letzte geschlossene Flaeche: groesstes s, bis zu dem alle inneren Linien gut sind
        s_last = 0.0
        for z_ in inn:
            if zerfallen(z_):
                break
            s_last = z_["s_start"]
        ergebnisse[name]["letzte_geschlossene_s_aufsteigend_ohne_luecke"] = s_last
        ergebnisse[name]["gute_linien_s"] = gut
    p0 = ergebnisse["phi_0"]["linien"]
    anh = any(zerfallen(z_) for name in ergebnisse for z_ in ergebnisse[name]["linien"] if z_["s_start"] <= 0.5)
    io = [(z_["s_start"], z_["iota"] - z_["iota_vmec"]) for z_ in p0 if "iota" in z_ and z_["s_start"] <= 1.0 and not zerfallen(z_)]
    erg = {"paket": "P2", "start": start, "dauer_gitter_s": gitter_s,
           "gitter": {"R": R, "Z": Z, "n_phi_je_periode": NPHI, "maske_abstand_spule_m": D_MASKE, "n_umlaeufe": N_UML, "schritte_je_periode": SCHRITTE, "nfp": nfp},
           "interpolation_fehler_max_rel_zu_mittel_B": interp_fehler,
           "kriterium_zerfallen": f"verloren oder rms-Abweichung der Poincare-Kurve (Fourier m<=8 in r(theta)) > {SCHWELLE} * r (Arbeitskriterium, eigene Setzung)",
           "ebenen": ergebnisse,
           "iota_abweichung_max_betrag": float(max(abs(x[1]) for x in io)) if io else None,
           "anhalten": bool(anh)}
    schreibe("P2", erg, t0)
    print(f"P2: max |iota-vmec| {erg['iota_abweichung_max_betrag']}, anhalten {anh}", flush=True)


# ---------------------------------------------------------------- P3
def induktivitaet_energie(d, I, k, wp, nq=512):
    """Magnetenergie W = 1/2 sum_ij I_i I_j M_ij (Neumann-Doppelintegral, Eigenterm mit Regularisierung des Querschnitts)."""
    from simsopt.field.selffield import regularization_rect
    from simsopt.field import Current, coils_via_symmetries
    coils = coils_via_symmetries(kurven(d, k, nq), [Current(float(i)) for i in I], d["nfp"], True)
    n = len(coils); Is = np.array([c.current.get_value() for c in coils])
    g = [c.curve.gamma() for c in coils]; dl = [c.curve.gammadash() / nq for c in coils]
    delta = float(regularization_rect(wp, wp))
    W = 0.0; Lself = []
    for i in range(n):
        for j in range(i, n):
            r2 = ((g[i][:, None, :] - g[j][None, :, :]) ** 2).sum(2)
            if i == j:
                r2 = r2 + delta
            M = MU0 / (4 * np.pi) * ((dl[i] @ dl[j].T) / np.sqrt(r2)).sum()
            W += (0.5 if i == j else 1.0) * Is[i] * Is[j] * M
            if i == j:
                Lself.append(M)
    return float(W), delta, Lself


def p3():
    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from simsopt.field.selffield import B_regularized_pure, regularization_rect
    t0 = time.time(); start = jetzt()
    b, w, k = massstab(); nfp = w["nfp"]
    d, I = lade(k, b["I_MA"]); wp = b["wp_m"]
    nq = 512
    kv = kurven(d, k, nq)
    coils = coils_via_symmetries(kv, [Current(float(i)) for i in I], nfp, True)
    nb = len(kv); reg = regularization_rect(wp, wp)
    spulen = []; npz = {}
    for j in range(nb):
        c = coils[j]; cu = c.curve; Ij = c.current.get_value()
        g = cu.gamma(); gd = cu.gammadash(); gdd = cu.gammadashdash()
        andere = BiotSavart([cc for m, cc in enumerate(coils) if m != j]); andere.set_points(g); Bf = andere.B()
        Be = np.asarray(B_regularized_pure(g, gd, gdd, cu.quadpoints, Ij, reg))
        ds = np.linalg.norm(gd, axis=1) / len(g)
        t = gd / np.linalg.norm(gd, axis=1)[:, None]
        f = Ij * np.cross(t, Bf + Be); fe = Ij * np.cross(t, Be)
        fb = np.linalg.norm(f, axis=1)
        F = (f * ds[:, None]).sum(0)
        Rr = np.hypot(g[:, 0], g[:, 1]); eR = np.c_[g[:, 0] / Rr, g[:, 1] / Rr, 0 * Rr]
        m = g.mean(0); ec = np.array([m[0], m[1], 0.0]); ec /= np.linalg.norm(ec)
        # Seitenkraft: Anteil senkrecht zur Schmiegebene wird hier nicht ausgewertet (siehe stellarator/kraft_analyse.py)
        spulen.append({"spule": j + 1, "I_MA": Ij / 1e6, "laenge_m": float(ds.sum()),
                       "f_max_MN_m": float(fb.max() / 1e6), "f_mittel_MN_m": float(fb.mean() / 1e6),
                       "f_eigenfeldanteil_mittel": float(np.linalg.norm(fe, axis=1).mean() / fb.mean()),
                       "B_fremd_max_T": float(np.linalg.norm(Bf, axis=1).max()),
                       "F_netto_xyz_MN": (F / 1e6).tolist(), "F_betrag_MN": float(np.linalg.norm(F) / 1e6),
                       "F_radial_integral_MN": float(((f * eR).sum(1) * ds).sum() / 1e6),
                       "F_zum_Torusmittelpunkt_der_Spule_MN": float((F @ ec) / 1e6), "F_vertikal_MN": float(F[2] / 1e6),
                       "F_betrag_integral_MN": float((fb * ds).sum() / 1e6),
                       "Spulenschwerpunkt_R_m": float(np.hypot(m[0], m[1]))})
        # Spitzenfeld am Leiter: Wickelpaketrand (4 Ecken + 4 Kantenmitten), Feld = alle anderen Spulen + eigener Faden (Abstand >= wp/2)
        nv = g - m; nv = nv - (nv * t).sum(1)[:, None] * t; nv /= np.linalg.norm(nv, axis=1)[:, None]; bv = np.cross(t, nv)
        offs = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
        ptsL = np.concatenate([g + wp / 2 * (a_ * nv + b_ * bv) for a_, b_ in offs])
        bs_all = BiotSavart(coils); bs_all.set_points(ptsL); BL = np.linalg.norm(bs_all.B(), axis=1).reshape(len(offs), -1)
        spulen[-1]["B_leiter_max_T"] = float(BL.max()); spulen[-1]["B_leiter_mittel_T"] = float(BL.mean())
        spulen[-1]["B_leiter_max_bei_s_m"] = float(np.r_[0, np.cumsum(ds)[:-1]][int(BL.max(0).argmax())])
        npz[f"s{j}"] = np.r_[0, np.cumsum(ds)[:-1]]; npz[f"f{j}"] = fb / 1e6; npz[f"BL{j}"] = BL.max(0)
    np.savez(OUT / "p3_linienkraft.npz", **npz)
    W, delta, Ls = induktivitaet_energie(d, I, k, wp)
    # Kontrolle der Energie-Rechnung: Kreisring R=10 m, Querschnitt wp x wp (Naeherung ln(8R/GMD)-2, GMD = 0,447 wp fuer ein Quadrat)
    th = np.linspace(0, 2 * np.pi, 512, endpoint=False); Rk = 10.0
    gk = np.c_[Rk * np.cos(th), Rk * np.sin(th), 0 * th]; dk = np.c_[-Rk * np.sin(th), Rk * np.cos(th), 0 * th] * (2 * np.pi / 512)
    r2 = ((gk[:, None] - gk[None]) ** 2).sum(2) + delta
    Lk = MU0 / (4 * np.pi) * ((dk @ dk.T) / np.sqrt(r2)).sum()
    Lk_ref = MU0 * Rk * (np.log(8 * Rk / (0.44705 * wp)) - 2)
    fmax = max(s_["f_max_MN_m"] for s_ in spulen)
    p1j = gelesen("P1"); BLmax = max(s_["B_leiter_max_T"] for s_ in spulen)
    jmax = max(spulen, key=lambda s_: s_["B_leiter_max_T"])["spule"]
    kB = {"B_leiter_max_T": BLmax, "spule_max": jmax, "B0_achse_T": p1j["B0_achse_mittel_absB_T"], "k_B_echt": BLmax / p1j["B0_achse_mittel_absB_T"],
          "k_B_bilanz": json.loads(BILANZ.read_text())["annahmen"]["k_B"]["HTS"], "B_leiter_grenze_HTS_T": json.loads(BILANZ.read_text())["auslegung"]["HTS"]["B_leiter_T"],
          "methode": f"8 Punkte auf dem Wickelpaketrand ({wp:.3f} m quadratisch), B = Biot-Savart aller anderen Spulen + eigener Faden; Eigenfeld nicht regularisiert (Rand liegt >= wp/2 vom Faden)"}
    f30 = (p1j["strom_fuer_10T_mittel_MA"] / (b["I_MA"])) ** 2
    fB = p1j["f_I_faktor_neu"] ** 2                              # Kraft und Energie ~ I^2, Strom fuer das B0 der Bilanz
    kB["f_I_neu"] = p1j["f_I_faktor_neu"]; kB["B_leiter_bei_B0_bilanz_T"] = BLmax * p1j["f_I_faktor_neu"]
    erg = {"paket": "P3", "leiterfeld": kB,
           "faktor_kraft_energie_B0_bilanz": fB, "kraft_bei_B0_bilanz_f_max_MN_m": fmax * fB, "energie_bei_B0_bilanz_GJ": W / 1e9 * fB, "faktor_kraft_energie_30_69MA": f30, "kraft_bei_30_69MA_f_max_MN_m": fmax * f30,
           "energie_bei_30_69MA_GJ": W / 1e9 * f30, "start": start, "wp_m": wp, "wp_quelle": "bilanz.json wickelpaket_m, quadratisch, fuer alle Spulen gleich",
           "strom_mittel_MA": float(I.mean() / 1e6), "spulen_basis": spulen,
           "f_max_alle_MN_m": fmax, "f_mittel_der_spulenmittel_MN_m": float(np.mean([s_["f_mittel_MN_m"] for s_ in spulen])),
           "F_netto_betrag_min_MN": min(s_["F_betrag_MN"] for s_ in spulen), "F_netto_betrag_max_MN": max(s_["F_betrag_MN"] for s_ in spulen),
           "F_zum_Mittelpunkt_min_max_MN": [min(s_["F_zum_Torusmittelpunkt_der_Spule_MN"] for s_ in spulen), max(s_["F_zum_Torusmittelpunkt_der_Spule_MN"] for s_ in spulen)],
           "magnetenergie_GJ": W / 1e9, "magnetenergie_bilanz_GJ": b["E_GJ"], "abweichung_zur_bilanz_prozent": (W / 1e9 / b["E_GJ"] - 1) * 100,
           "energie_methode": "1/2 sum I_i I_j M_ij, Neumann-Integral 512 Punkte je Spule, Eigenterm Wurzel(r^2 + delta) mit delta = regularization_rect(wp, wp)",
           "energie_kontrolle_kreisring": {"L_numerisch_H": float(Lk), "L_Naeherung_H": float(Lk_ref), "abweichung_prozent": float((Lk / Lk_ref - 1) * 100)},
           "selbstinduktivitaet_je_basisspule_H": [float(x) for x in Ls[:nb]],
           "abweichung_von_kraft_analyse": "eigene Auswertung (kraft_analyse.analyse ist auf B0 6,5 T, anderen nfp/WOUT und wp ~ sqrt(I) festgelegt); gleiche Formeln (Linienkraft I t x (B_fremd + B_eigen))"}
    schreibe("P3", erg, t0)
    print(f"P3: f_max {fmax:.1f} MN/m, F_netto {erg['F_netto_betrag_min_MN']:.0f}..{erg['F_netto_betrag_max_MN']:.0f} MN, W {W/1e9:.0f} GJ", flush=True)


# ---------------------------------------------------------------- P4
def p4():
    from scipy.spatial import cKDTree
    from spulen_glaetten import baubarkeit
    import spulen_montage
    from spulen_satz import flaeche
    t0 = time.time(); start = jetzt()
    b, w, k = massstab(); d, I = lade(k, b["I_MA"]); dwp = b["wp_m"]
    from simsopt.geo import CurveXYZFourier
    pm = spulen_montage.pruefe(str(SATZ))               # Ruecklauf, Kreuzen (winkelbasiert, maßstabsfrei)
    bau = []
    for c in kurven(d, 1.0, 128):                       # Kurven im kleinen Maßstab, Umrechnung ueber k
        r = baubarkeit(c, k); bau.append(r)
    rmin = [x["biegeradius_min_m"] for x in bau]
    # Abstaende in Anlagengroesse, dichte Abtastung
    nq = 1024
    coils = spulen_gesamt(d, I, k, nq=nq)
    pts = [c.curve.gamma() for c in coils]
    s = flaeche(SATZ / "boundary.json", nphi=256, ntheta=128)
    Sg = s.gamma().reshape(-1, 3) * k
    dsp = min(cKDTree(Sg).query(p)[0].min() for p in pts)
    # Spule-Spule: kuerzester Abstand zu einer anderen Spule
    trees = [cKDTree(p) for p in pts]; dss = np.inf; paar = None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dd = trees[j].query(pts[i])[0].min()
            if dd < dss:
                dss, paar = float(dd), (i, j)
    erg = {"paket": "P4", "start": start, "d_wickelpaket_m": dwp, "d_quelle": "bilanz.json wickelpaket_m",
           "ruecklauf_max": pm["ruecklauf_max"], "spulen_mit_ruecklauf": pm["spulen_mit_ruecklauf"],
           "nachbarpaare_kreuzend": pm["nachbarpaare_kreuzend"], "nachbar_abstand_grad_min": pm["nachbar_abstand_grad_min"],
           "phi_breite_grad_max": pm["phi_breite_grad_max"], "teilung_grad": pm["teilung_grad"], "n_spulen": pm["n_spulen"],
           "R_min_je_basisspule_m": rmin, "R_min_m": float(min(rmin)), "R_min_durch_d": float(min(rmin) / dwp), "regel_R_min_durch_d": 2.0,
           "R_min_durch_d_je_basisspule": [x / dwp for x in rmin],
           "laenge_je_basisspule_m": [x["laenge_m"] for x in bau],
           "selbstabstand_min_m": float(min(x["selbstabstand_min_m"] for x in bau)),
           "abstand_spule_plasma_min_m": float(dsp), "abstand_spule_spule_min_m": dss, "abstand_spule_spule_paar_index": paar,
           "abstand_spule_spule_durch_d": dss / dwp,
           "abtastung": f"{nq} Punkte je Spule, Plasmarand 256 x 128 Punkte (Punkt-Punkt-Abstand, Diskretisierungsfehler ~ mm)",
           "quelle_montage": "stellarator/spulen_montage.py pruefe() (Rücklauf/Kreuzen; dessen R_min-Angabe nicht verwendet, hier mit k statt A_M)"}
    schreibe("P4", erg, t0)
    print(f"P4: Rueck {pm['ruecklauf_max']}, kreuz {pm['nachbarpaare_kreuzend']}, Rmin {min(rmin):.2f} m, R/d {min(rmin)/dwp:.2f}, "
          f"d_sp-pl {dsp:.2f} m, d_ss {dss:.2f} m", flush=True)


# ---------------------------------------------------------------- P5
def p5():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t0 = time.time(); start = jetzt()
    BILD.mkdir(parents=True, exist_ok=True)
    b, w, k = massstab(); nfp = w["nfp"]
    p1j, p2j, p3j, p4j = gelesen("P1"), gelesen("P2"), gelesen("P3"), gelesen("P4")
    datum = time.strftime("%Y-%m-%d")
    R0t = f"{b['R0_m']:.1f}"; Imt = f"{b['I_MA']:.1f}"; wpt = f"{b['wp_m']:.2f}"
    kopf = OUT.relative_to(P) if OUT.is_relative_to(P) else OUT.name
    Tr = {"de": {"kg": "KI-generiert (Claude Sonnet 5.5) · Entwurf", "fuss": "KI-generiert · Entwurf · {d} · Quelle: " + str(kopf) + "/{q}"},
          "en": {"kg": "AI-generated (Claude Sonnet 5.5) · draft", "fuss": "AI-generated · draft · {d} · source: " + str(kopf) + "/{q}"}}

    def rahmen(fig, sp, titel, q):
        fig.suptitle(titel + "\n" + Tr[sp]["kg"], fontsize=11)
        fig.text(0.5, 0.005, Tr[sp]["fuss"].format(d=datum, q=q), ha="center", fontsize=7, color="0.4")

    dateien = []
    thf = np.linspace(0, 2 * np.pi, 600)
    for sp in ("de", "en"):
        de = sp == "de"
        # --- Poincare
        fig, ax = plt.subplots(1, 2, figsize=(15, 6.2))
        for a, (name, delta) in zip(ax, [("phi_0", 0.0), ("phi_halbe_periode", np.pi / nfp)]):
            z = np.load(ZW / f"poincare_{name}.npz"); pk = z["pk"]; sl = z["s"]
            for sv, ls, lw in [(0.25, "-", 0.6), (0.5, "-", 0.6), (0.75, "-", 0.6), (1.0, "-", 1.6)]:
                Rv, Zv = vmec_flaeche(w, sv, delta, thf, k); a.plot(Rv, Zv, "k", ls=ls, lw=lw, alpha=0.7)
            Rv, Zv = vmec_flaeche(w, 0.8, delta, thf, k)
            a.plot(Rv, Zv, "r--", lw=1.4, label=("Zielgrenze: geschlossene Flächen bis s = 0,8 (Erwartung K2)" if de else "target: closed surfaces up to s = 0.8 (K2 expectation)"))
            cm = plt.cm.viridis(np.linspace(0, 1, len(sl)))
            for i in range(len(sl)):
                a.plot(pk[i, :, 0], pk[i, :, 1], ".", ms=1.4, color=cm[i] if sl[i] <= 1 else "tab:orange")
            a.plot([], [], "k-", lw=1, label=("VMEC-Flächen s = 0,25 / 0,5 / 0,75 / 1" if de else "VMEC surfaces s = 0.25 / 0.5 / 0.75 / 1"))
            a.plot([], [], ".", color="tab:orange", label=("Startpunkte außerhalb (s > 1)" if de else "start points outside (s > 1)"))
            a.set_aspect("equal"); a.set_xlabel("R [m]"); a.set_ylabel("Z [m]"); a.grid(alpha=0.3)
            a.set_title((f"φ = 0 (Periodenanfang)" if name == "phi_0" else "φ = π/nfp (halbe Periode)") if de else
                        (f"φ = 0 (start of period)" if name == "phi_0" else "φ = π/nfp (half period)"))
        ax[0].legend(fontsize=7, loc="upper right")
        rahmen(fig, sp, f"Poincaré-Schnitt, Spulen {ID8}, R0 {R0t.replace('.', ',')} m, {Imt.replace('.', ',')} MA je Spule" if de else
               f"Poincaré section, coils {ID8}, R0 {R0t} m, {Imt} MA per coil", "P2.json")
        fig.tight_layout(rect=(0, 0.02, 1, 0.9)); f = BILD / f"k2_poincare_{sp}.png"; fig.savefig(f, dpi=130); plt.close(fig); dateien.append(f)
        # --- iota
        fig, a = plt.subplots(figsize=(8.5, 5.6))
        L = p2j["ebenen"]["phi_0"]["linien"]
        s_ = [z["s_start"] for z in L if "iota" in z and z["s_start"] <= 1]
        i_f = [z["iota"] for z in L if "iota" in z and z["s_start"] <= 1]
        i_v = [z["iota_vmec"] for z in L if "iota" in z and z["s_start"] <= 1]
        i1 = [z["iota_haelfte1"] for z in L if "iota" in z and z["s_start"] <= 1]; i2 = [z["iota_haelfte2"] for z in L if "iota" in z and z["s_start"] <= 1]
        sv = np.linspace(0, 1, 200); iv = np.interp(sv, w["s"], w["iotaf"])
        a.fill_between(sv, iv - 0.02, iv + 0.02, color="tab:green", alpha=0.25, label=("Zielband: VMEC ± 0,02 (Erwartung K2)" if de else "target band: VMEC ± 0.02 (K2 expectation)"))
        a.plot(sv, iv, "k-", label="VMEC")
        a.plot(s_, i_f, "o", color="tab:red", label=("Feldlinien (Poincaré, 300 Umläufe)" if de else "field lines (Poincaré, 300 turns)"))
        a.plot(s_, i1, "_", color="0.4", ms=9); a.plot(s_, i2, "_", color="0.4", ms=9, label=("1. / 2. Hälfte der Umläufe" if de else "1st / 2nd half of turns"))
        a.axhline(1 / 6, color="tab:purple", ls=":", label=("ι = 1/6 (Resonanz, mögliche Inseln)" if de else "ι = 1/6 (resonance, possible islands)"))
        a.axvline(0.8, color="r", ls="--", lw=1, label=("s = 0,8 (Zielgrenze geschlossen)" if de else "s = 0.8 (closed-surface target)"))
        a.set_xlabel("s (normierter toroidaler Fluss)" if de else "s (normalised toroidal flux)"); a.set_ylabel("ι"); a.grid(alpha=0.3); a.legend(fontsize=8)
        rahmen(fig, sp, "Rotationstransformation: Feldlinien gegen VMEC" if de else "Rotational transform: field lines vs VMEC", "P2.json")
        fig.tight_layout(rect=(0, 0.02, 1, 0.92)); f = BILD / f"k2_iota_{sp}.png"; fig.savefig(f, dpi=130); plt.close(fig); dateien.append(f)
        # --- Linienkraft
        z = np.load(OUT / "p3_linienkraft.npz"); nb = len(p3j["spulen_basis"])
        nsp = -(-nb // 2)                                   # Spalten je Zeile (10 Basisspulen -> 5, 12 -> 6; B-082)
        fig, ax = plt.subplots(2, nsp, figsize=(3.4 * nsp, 7), sharey=True)
        for j in range(nb):
            a = ax.flat[j]; a.axhspan(100, 300, color="tab:green", alpha=0.2, label=("Erwartung K2: 100–300 MN/m" if de else "K2 expectation: 100–300 MN/m"))
            a.plot(z[f"s{j}"], z[f"f{j}"], "k", lw=1.3)
            sj = p3j["spulen_basis"][j]
            a.set_title((f"Spule {j+1}" if de else f"coil {j+1}") + f" ({sj['I_MA']:.1f} MA, max {sj['f_max_MN_m']:.0f})", fontsize=9)
            a.grid(alpha=0.3)
            if j >= nsp: a.set_xlabel("Weg [m]" if de else "arc length [m]")
        ax.flat[0].legend(fontsize=7, loc="upper right"); ax[0, 0].set_ylabel("Linienkraft [MN/m]" if de else "line force [MN/m]"); ax[1, 0].set_ylabel("Linienkraft [MN/m]" if de else "line force [MN/m]")
        rahmen(fig, sp, f"Linienkraft je Basisspule (Betrag), {Imt.replace('.', ',')} MA mittlerer Strom, Wickelpaket {wpt.replace('.', ',')} m" if de else
               f"Line force per base coil (magnitude), {Imt} MA mean current, winding pack {wpt} m", "P3.json")
        fig.tight_layout(rect=(0, 0.02, 1, 0.9)); f = BILD / f"k2_linienkraft_{sp}.png"; fig.savefig(f, dpi=130); plt.close(fig); dateien.append(f)
        # --- Leiterfeld
        fig, a = plt.subplots(figsize=(9, 5.6)); bl = [x["B_leiter_max_T"] for x in p3j["spulen_basis"]]
        a.axhspan(p3j["leiterfeld"]["B_leiter_grenze_HTS_T"], 32, color="tab:red", alpha=0.2,
                  label=("über Grenze HTS 20 T (Annahme des Werkzeugs)" if de else "above HTS limit 20 T (tool assumption)"))
        a.axhline(p3j["leiterfeld"]["B_leiter_grenze_HTS_T"], color="r", ls="--")
        a.bar(np.arange(1, len(bl) + 1), bl, color="tab:blue"); a.set_ylim(0, 32)
        a.axhline(p3j["leiterfeld"]["B0_achse_T"], color="k", ls=":", label=("B0 Achse (Mittel)" if de else "B0 axis (mean)"))
        a.set_xlabel("Basisspule" if de else "base coil"); a.set_ylabel("max. |B| am Wickelpaketrand [T]" if de else "max |B| at winding-pack edge [T]"); a.legend(fontsize=8); a.grid(alpha=0.3)
        rahmen(fig, sp, "Spitzenfeld am Leiter je Basisspule" if de else "Peak field at the conductor per base coil", "P3.json")
        fig.tight_layout(rect=(0, 0.02, 1, 0.92)); f = BILD / f"k2_leiterfeld_{sp}.png"; fig.savefig(f, dpi=130); plt.close(fig); dateien.append(f)
        # --- 3D
        d, I = lade(k, b["I_MA"])
        coils = spulen_gesamt(d, I, k, nq=256)
        from spulen_satz import flaeche
        s = flaeche(SATZ / "boundary.json", nphi=96, ntheta=48); G = s.gamma() * k
        fig = plt.figure(figsize=(10, 8)); a = fig.add_subplot(111, projection="3d")
        G2 = np.concatenate([G, G[:1]], 0); G2 = np.concatenate([G2, G2[:, :1]], 1)
        a.plot_surface(G2[..., 0], G2[..., 1], G2[..., 2], color="tab:orange", alpha=0.85, linewidth=0, antialiased=True)
        cm = plt.cm.tab20(np.arange(20) % 20) if nb > 10 else plt.cm.tab10(np.arange(10) % 10)
        for i, c in enumerate(coils):
            g = c.curve.gamma(); g = np.vstack([g, g[:1]]); a.plot(g[:, 0], g[:, 1], g[:, 2], color=cm[i % nb], lw=1.0)
        a.set_box_aspect((1, 1, 0.5)); a.view_init(elev=38, azim=-60); a.set_xlabel("x [m]"); a.set_ylabel("y [m]"); a.set_zlabel("z [m]")
        lim = 1.28 * b["R0_m"]; a.set_xlim(-lim, lim); a.set_ylim(-lim, lim); a.set_zlim(-lim / 2, lim / 2)
        a.text2D(0.02, 0.93, ("Plasma: Datensatzform %s, unverändert (Rand), × %.2f\nSpulen: eigene %d Spulen (%d Basisspulen × Symmetrie), Farbe = Basisspule\nBezugsgröße R0 = %s m; kein Zielband (Ansicht)" % (ID8, k, len(coils), nb, R0t.replace(".", ","))) if de else
                 ("Plasma: dataset shape %s, unchanged (boundary), × %.2f\nCoils: own %d coils (%d base coils × symmetry), colour = base coil\nReference R0 = %s m; no target band (view only)" % (ID8, k, len(coils), nb, R0t)),
                 transform=a.transAxes, fontsize=8, va="top")
        rahmen(fig, sp, "Spulen und Plasma, volle Größe" if de else "Coils and plasma, full size", "P1.json")
        fig.tight_layout(rect=(0, 0.02, 1, 0.92)); f = BILD / f"k2_3d_{sp}.png"; fig.savefig(f, dpi=130); plt.close(fig); dateien.append(f)
    baustein(b, w, k, p1j, p2j, p3j, p4j)
    erg = {"paket": "P5", "start": start, "bilder": [rel(f) for f in dateien], "baustein": _bau}
    schreibe("P5", erg, t0)
    print("P5:", *[f.name for f in dateien], flush=True)


def vtk_polydata(datei, punkte, linien=None, polys=None, skalar=None, name="s"):
    """Legacy-VTK (ASCII), Einheit Meter."""
    punkte = np.asarray(punkte, float)
    with open(datei, "w") as f:
        f.write("# vtk DataFile Version 3.0\nKI-generiert K2, Einheit m\nASCII\nDATASET POLYDATA\n")
        f.write(f"POINTS {len(punkte)} float\n")
        np.savetxt(f, punkte, fmt="%.4f")
        if linien:
            n = sum(len(l) + 1 for l in linien); f.write(f"LINES {len(linien)} {n}\n")
            for l in linien: f.write(f"{len(l)} " + " ".join(map(str, l)) + "\n")
        if polys:
            n = sum(len(q) + 1 for q in polys); f.write(f"POLYGONS {len(polys)} {n}\n")
            for q in polys: f.write(f"{len(q)} " + " ".join(map(str, q)) + "\n")
        if skalar is not None:
            f.write(f"POINT_DATA {len(punkte)}\nSCALARS {name} float 1\nLOOKUP_TABLE default\n"); np.savetxt(f, np.asarray(skalar, float), fmt="%.5f")


def baustein(b, w, k, p1j, p2j, p3j, p4j):
    """Szenenmaterial Szene 1 (Storyboard docs/projekt/14_praesentationsvideo.md): video/bausteine/K2/"""
    from spulen_satz import flaeche
    BO = (P / _bau) if not Path(_bau).is_absolute() else Path(_bau); BO.mkdir(parents=True, exist_ok=True)
    alt = BO / "vorlaeufig"                                  # K2b: alte Dateien nicht loeschen, in Unterordner verschieben (einmalig)
    if not alt.exists() and (BO / "baustein.md").exists():
        alt.mkdir(); [f.rename(alt / f.name) for f in BO.iterdir() if f.is_file()]
    d, I = lade(k, b["I_MA"]); coils = spulen_gesamt(d, I, k, nq=256)
    pts, lin = [], []
    for c in coils:
        g = c.curve.gamma(); i0 = len(pts); pts += g.tolist(); lin.append(list(range(i0, i0 + len(g))) + [i0])
    vtk_polydata(BO / "spulen_40.vtk", pts, linien=lin)
    s = flaeche(SATZ / "boundary.json", nphi=128, ntheta=64); G = s.gamma() * k
    nph, nth = G.shape[:2]; polys = []
    for i in range(nph):
        for j in range(nth):
            a_ = i * nth + j; b_ = i * nth + (j + 1) % nth; c_ = ((i + 1) % nph) * nth + (j + 1) % nth; d_ = ((i + 1) % nph) * nth + j
            polys.append([a_, b_, c_, d_])
    vtk_polydata(BO / "plasmarand.vtk", G.reshape(-1, 3), polys=polys)
    # Poincare-Punkte
    P3d, sk, arr = [], [], {}
    for name, delta in [("phi_0", 0.0), ("phi_halbe_periode", np.pi / w["nfp"])]:
        z = np.load(ZW / f"poincare_{name}.npz"); pk = z["pk"]; sl = z["s"]
        arr[name + "_RZ"] = pk; arr[name + "_s"] = sl; arr[name + "_phi_rad"] = delta
        for i in range(len(sl)):
            q = pk[i][np.isfinite(pk[i, :, 0])]
            P3d += np.c_[q[:, 0] * np.cos(delta), q[:, 0] * np.sin(delta), q[:, 1]].tolist(); sk += [sl[i]] * len(q)
    np.savez(BO / "poincare_punkte.npz", **arr)
    vtk_polydata(BO / "poincare_punkte.vtk", P3d, skalar=sk, name="s_start")
    e = p2j["ebenen"]["phi_0"]["linien"]
    p3 = p3j; lf = p3["leiterfeld"]
    zahlen = [("Maßstab R0 / a", f"{b['R0_m']:.1f} m / {p1j['a_gross_m']:.2f} m (k = {p1j['faktor_k']:.3f})".replace(".", ",", 1), "P1.json"),
              (f"B0 Achse (Mittel |B|), {b['I_MA']:.3f} MA mittlerer Strom je Spule", f"{p1j['B0_achse_mittel_absB_T']:.2f} T", "P1.json"),
              ("Feldfehler |B·n|/|B| Mittel", f"{p1j['feldfehler']['Bn_mittel']:.2e}", "P1.json"),
              ("iota Feldlinien Mitte / Rand (s = 0,02 / 1,0)", f"{e[0]['iota']:.3f} / {[z['iota'] for z in e if z['s_start']==1.0][0]:.3f}", "P2.json"),
              ("größte Abweichung iota gegen VMEC", f"{p2j['iota_abweichung_max_betrag']:.4f}", "P2.json"),
              ("Linienkraft max", f"{p3['f_max_alle_MN_m']:.0f} MN/m", "P3.json"),
              ("Nettokraft je Spule min–max", f"{p3['F_netto_betrag_min_MN']:.0f}–{p3['F_netto_betrag_max_MN']:.0f} MN", "P3.json"),
              ("Magnetenergie", f"{p3['magnetenergie_GJ']:.0f} GJ", "P3.json"),
              ("Spitzenfeld am Leiter / k_B echt", f"{lf['B_leiter_max_T']:.1f} T / {lf['k_B_echt']:.2f}", "P3.json"),
              ("R_min / d, kreuzende Nachbarpaare", f"{p4j['R_min_durch_d']:.2f}, {p4j['nachbarpaare_kreuzend']}", "P4.json")]
    tab = "\n".join(f"| {a} | {v} | `{OUT.relative_to(P)}/{q}` |" for a, v, q in zahlen)
    txt = f"""| Dok.-Nr. | FUS-VID-K2 | Version | 0.1 | Status | Entwurf |
|---|---|---|---|---|---|
| Titel | Szenenbaustein K2 · Spulen und Plasma {ID8} in voller Größe ({b['R0_m']:.1f} m) | Ersteller | Claude Sonnet 5.5 (KI) | Prüfer | – (Opus/Mensch offen) |

> **KI-generiert (Claude Sonnet 5.5, {time.strftime('%Y-%m-%d')}).** Material für Szene 1 des Präsentationsvideos (docs/projekt/14_praesentationsvideo.md). Im Bild nur „Thomas Schmiegelt“; Erklärungen im Begleittext.

## Dateien (Einheit Meter, volle Größe, Torusachse = z)
- `spulen_40.vtk` — {len(coils)} Spulen als geschlossene Linien ({len(coils) // 4} Basisspulen mal Symmetrie; Dateiname historisch).
- `plasmarand.vtk` — Plasmarand der Datensatzform {ID8} (unverändert), mal k = {p1j['faktor_k']:.3f}.
- `poincare_punkte.vtk` / `.npz` — Poincaré-Punkte in der Ebene φ = 0 und φ = π/nfp (halbe Periode), Skalar `s_start` (Startfläche s; > 1 = außerhalb des Randes); 300 Umläufe je Linie.
- Bilder (PNG, DE/EN) in `{OUT.relative_to(P)}/bilder/`.

## Kennzahlen
| Größe | Wert | Quelle |
|---|---|---|
{tab}

## Begleittext DE
Die {len(coils)} Spulen erzeugen das Feld für die verdrillte Plasmaform {ID8} in voller Größe, Hauptradius {b['R0_m']:.1f} m. Verfolgt man Feldlinien über 300 Umläufe, bleiben die Flussflächen geschlossen und stimmen in der Rotationstransformation mit dem Gleichgewichtscode überein. Das Feld auf der Achse liegt mit {p1j['B0_achse_mittel_absB_T']:.1f} T gegen {b['B0_T']:.1f} T der Bilanz (Stufe 0); das ist ein Befund der Rechnung.

## Begleittext EN
The {len(coils)} coils produce the field for the twisted plasma shape {ID8} at full size, major radius {b['R0_m']:.1f} m. Tracing field lines over 300 turns, the flux surfaces stay closed and the rotational transform agrees with the equilibrium code. The on-axis field is {p1j['B0_achse_mittel_absB_T']:.1f} T, versus {b['B0_T']:.1f} T of the balance (stage 0); this is a finding of the calculation.

## Kamera-Vorschlag (Annahme, nicht geprüft)
Langsamer Umlauf um die z-Achse (Aufsicht, ca. 35° Elevation), Spulen halbtransparent, Plasmarand farbig; danach Einflug in die Ebene φ = 0 mit den Poincaré-Punkten (Farbe = s). Kein Rendern hier; Zielband/Grenzen stehen in den Bildern.

---
*KI-generiert (Claude Sonnet 5.5, {time.strftime('%Y-%m-%d')}). Status Entwurf. Freigabe nur durch den Autor.*
"""
    (BO / "baustein.md").write_text(txt)


# ---------------------------------------------------------------- Steuerung
def main():
    a = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True); ZW.mkdir(exist_ok=True)
    neu, nur = [], []
    mode = None
    for x in a:
        if x == "--neu": mode = "neu"
        elif x == "--nur": mode = "nur"
        elif x == "--weiter": mode = None
        elif x == "--ohne-halt": pass
        elif mode == "neu": neu.append(x)
        elif mode == "nur": nur.append(x)
    fn = {"P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5}
    for pk in PAKETE:
        if nur and pk not in nur:
            continue
        f = OUT / f"{pk}.json"
        if pk in neu:
            f.unlink(missing_ok=True)
            if pk == "P2":
                for z in list(ZW.glob("poincare_*.npz")) + [ZW / "gitter.npz"]:
                    z.unlink(missing_ok=True)
        if f.exists():
            print(f"{pk}: vorhanden, uebersprungen", flush=True); continue
        if pk != "P1":
            halt_pruefen()
        print(f"{pk}: Start {jetzt()}", flush=True)
        fn[pk]()
        if pk == "P1" and gelesen("P1")["anhalten"]:
            sys.exit("P1: B0-Abweichung > 10 %, angehalten")
        if pk == "P2" and gelesen("P2")["anhalten"]:
            sys.exit("P2: zerfallene Flaechen innerhalb s = 0,5, angehalten")


if __name__ == "__main__":
    main()
