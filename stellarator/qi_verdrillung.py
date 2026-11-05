"""Nutzer-Hypothese 2026-11-05: Haengt QI mit der Verdrillung / Kruemmung der Plasmaflaeche zusammen, und hilft ein grosser
Durchmesser (mehr Raum fuer die Verdrillung, 'kruemmungsstetiger')?

Aufruf (aus ~/hermes/fusion; Rechnungen im Scope, hoechstens 1 parallel):
  systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 --description="hermes python qi_verdrillung <name>" \
      env OMP_NUM_THREADS=1 .venv-constellaration/bin/python -m stellarator.qi_verdrillung <befehl> ...
Befehle:
  r00 <form> <faktor>     Teil 3: nur R(0,0) mal Faktor (alle anderen Koeffizienten unveraendert), forward_model hohe Genauigkeit
  skal <form> <faktor>    Teil 3 Pruefstein: alle r_cos, z_sin mal Faktor (gleichmaessig groesser) -> QI muss gleich bleiben
  d8z3d                   lokale QI-Karte (qi_3d.rechnen) fuer D8ZNt2 nachholen
  lokal                   Teil 1: Geometrie der Randflaeche gegen lokalen QI (karte3d), Bilder + json
  datensatz               Teil 2: analytische Masse aus den Randkoeffizienten des Datensatzes gegen QI
  r00bilder               Teil 3: Bild und Tabelle aus den fertigen Laeufen
Ergebnisse: sim/qi_flaeche/verdrillung/ (je Lauf eine json, fertige werden uebersprungen); Bericht docs/recherche/qi_tragwerk/qi_verdrillung.md.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUS = ROOT / "sim" / "qi_flaeche" / "verdrillung"
BILD = ROOT / "docs" / "recherche" / "qi_tragwerk" / "qi_verdrillung"
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------- Teil 3: VMEC++-Laeufe
def _lauf(name, b):
    AUS.mkdir(parents=True, exist_ok=True)
    f = AUS / f"{name}.json"
    if f.exists():
        print("fertig, uebersprungen:", name); return
    from constellaration import forward_model
    from constellaration.geometry import surface_rz_fourier as srf
    t0 = time.time(); out = {"name": name, "boundary": b}
    try:
        m, w = forward_model.forward_model(srf.SurfaceRZFourier.model_validate(b), settings=forward_model.ConstellarationSettings.default_high_fidelity())
        out["metriken"] = {k: (float(v) if isinstance(v, (int, float)) else None) for k, v in m.model_dump().items()}
        out["iota_achse"] = float(w.iotaf[0]); out["iota_rand"] = float(w.iotaf[-1]); out["fehler"] = None
        out["rmajor_p"] = float(w.Rmajor_p); out["aminor_p"] = float(w.Aminor_p); out["volume_p"] = float(getattr(w, "volume_p", float("nan")))
    except Exception as e:
        out["fehler"] = f"{type(e).__name__}: {str(e)[:300]}"
    out["sek"] = time.time() - t0
    f.write_text(json.dumps(out, indent=1)); print(json.dumps({k: v for k, v in out.items() if k != "boundary"}), flush=True)


def r00(form, faktor):
    from stellarator.qi_karte import rand
    b, _ = rand(form); b = json.loads(json.dumps(b))
    nt = (len(b["r_cos"][0]) - 1) // 2
    b["r_cos"][0][nt] *= faktor
    _lauf(f"r00_{form}_{faktor:.2f}", b)


def skal(form, faktor):
    from stellarator.qi_karte import rand
    b, _ = rand(form); b = json.loads(json.dumps(b))
    for k in ("r_cos", "z_sin", "r_sin", "z_cos"):
        if b.get(k) is not None:
            b[k] = [[x * faktor for x in z] for z in b[k]]
    _lauf(f"skal_{form}_{faktor:.2f}", b)


def d8z3d():
    from stellarator import qi_3d
    qi_3d.FORMEN["d8z"] = "D8ZNt2qFQLQQxMVitWaeCid (Startform Filter 138)"
    if (qi_3d.AUS / "d8z.json").exists():
        print("fertig"); return
    qi_3d.rechnen("d8z")


# ---------------------------------------------------------------- Geometrie aus Fourier-Reihen
def flaeche(rc, zs, nfp, nth=128, nph=128, ganz=False):
    """R, Z und Ableitungen nach theta (u) und phi (v) analytisch; phi = Zylinderwinkel (VMEC-Randdarstellung).
    rc, zs: Felder (M+1, 2N+1), Index n - N. Gibt dict mit Punkten und Ableitungen auf Gitter (nth, nph) ueber eine Periode."""
    M, K = rc.shape; N = (K - 1) // 2
    m = np.arange(M)[:, None] * np.ones((1, K)); n = (np.arange(K) - N)[None, :] * np.ones((M, 1))
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    ph = np.linspace(0, 2 * np.pi / (1 if ganz else nfp), nph, endpoint=False)
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    A = m.ravel()[None, None] * TH[..., None] - (nfp * n).ravel()[None, None] * PH[..., None]
    c, s = np.cos(A), np.sin(A); a = rc.ravel(); b = zs.ravel(); mm = m.ravel(); nn = nfp * n.ravel()
    d = {"th": th, "ph": ph}
    d["R"] = c @ a; d["Z"] = s @ b
    d["Ru"] = -(s * mm) @ a; d["Rv"] = (s * nn) @ a; d["Zu"] = (c * mm) @ b; d["Zv"] = -(c * nn) @ b
    d["Ruu"] = -(c * mm ** 2) @ a; d["Rvv"] = -(c * nn ** 2) @ a; d["Ruv"] = (c * mm * nn) @ a
    d["Zuu"] = -(s * mm ** 2) @ b; d["Zvv"] = -(s * nn ** 2) @ b; d["Zuv"] = (s * mm * nn) @ b
    return d


def kruemmungen(d):
    """Haupt-, Gauss- und mittlere Kruemmung der Flaeche X(u,v) = (R cos v, R sin v, Z)."""
    R, ph = d["R"], d["ph"][None, :]
    cv, sv = np.cos(ph), np.sin(ph)
    Xu = np.stack([d["Ru"] * cv, d["Ru"] * sv, d["Zu"]], -1)
    Xv = np.stack([d["Rv"] * cv - R * sv, d["Rv"] * sv + R * cv, d["Zv"]], -1)
    Xuu = np.stack([d["Ruu"] * cv, d["Ruu"] * sv, d["Zuu"]], -1)
    Xuv = np.stack([d["Ruv"] * cv - d["Ru"] * sv, d["Ruv"] * sv + d["Ru"] * cv, d["Zuv"]], -1)
    Xvv = np.stack([(d["Rvv"] - R) * cv - 2 * d["Rv"] * sv, (d["Rvv"] - R) * sv + 2 * d["Rv"] * cv, d["Zvv"]], -1)
    nrm = np.cross(Xu, Xv); J = np.linalg.norm(nrm, axis=-1); nh = nrm / J[..., None]
    E, F, G = (Xu * Xu).sum(-1), (Xu * Xv).sum(-1), (Xv * Xv).sum(-1)
    L, Mm, Nn = (Xuu * nh).sum(-1), (Xuv * nh).sum(-1), (Xvv * nh).sum(-1)
    K = (L * Nn - Mm ** 2) / (E * G - F ** 2); H = (E * Nn - 2 * F * Mm + G * L) / (2 * (E * G - F ** 2))
    w = np.sqrt(np.maximum(H ** 2 - K, 0))
    X = np.stack([R * cv, R * sv, d["Z"]], -1)
    # Vorzeichen: Normale nach aussen (weg von der Querschnittsmitte)
    Rc = R.mean(0, keepdims=True); Zc = d["Z"].mean(0, keepdims=True)
    aus = np.sign(((R - Rc) * (nh[..., 0] * cv + nh[..., 1] * sv) + (d["Z"] - Zc) * nh[..., 2]).mean())
    H = -H * aus                                      # konvex (Wulst) = positiv
    return dict(X=X, K=K, H=H, k1=H + w, k2=H - w, kmax=np.maximum(np.abs(H + w), np.abs(H - w)), J=J)


def querschnitt(d):
    """Je Toroidalwinkel: Schwerpunkt (Achsen-Naeherung), Elongation und Winkel der Hauptachse (Traegheitsellipse) des Querschnitts."""
    R, Z, Ru, Zu = d["R"], d["Z"], d["Ru"], d["Zu"]
    dA = 0.5 * (R * Zu - Z * Ru)                       # Flaeche als Summe von Dreiecken (Green), du konstant
    A = dA.sum(0)
    # Schwerpunkt und Momente ueber Randintegrale (Green): Integrale ueber den Querschnitt
    Rc = (R ** 2 * Zu).sum(0) / 2 / (R * Zu).sum(0)
    Zc = -(Z ** 2 * Ru).sum(0) / 2 / (-(Z * Ru)).sum(0)
    x, z = R - Rc, Z - Zc
    I_xx = (-(z ** 3) * Ru / 3).sum(0)                 # Int z^2 dA = -oint z^3/3 dR
    I_zz = (x ** 3 * Zu / 3).sum(0)                     # Int x^2 dA = oint x^3/3 dZ
    I_xz = (x ** 2 * z * Zu / 2).sum(0)                 # Int x z dA = oint x^2 z/2 dZ
    sg = np.sign(I_zz.mean())
    I_xx, I_zz, I_xz = I_xx * sg, I_zz * sg, I_xz * sg
    tr = I_xx + I_zz; df = np.sqrt((I_zz - I_xx) ** 2 + 4 * I_xz ** 2)
    l1, l2 = (tr + df) / 2, (tr - df) / 2
    elong = np.sqrt(l1 / np.maximum(l2, 1e-30))
    winkel = 0.5 * np.arctan2(2 * I_xz, I_zz - I_xx)    # Winkel der Hauptachse gegen R-Richtung
    return dict(Rc=Rc, Zc=Zc, elong=elong, winkel=np.unwrap(2 * winkel) / 2, A=np.abs(A) * (2 * np.pi / R.shape[0]))


def achse_kt(Rc, Zc, ph):
    """Kruemmung und Torsion der Mittellinie (Querschnittsschwerpunkte) ueber spektrale Ableitung (periodisch in phi)."""
    X = np.stack([Rc * np.cos(ph), Rc * np.sin(ph), Zc], -1)
    n = len(ph); k = 1j * np.fft.fftfreq(n, d=1.0 / n)      # ganze Wellenzahlen, ph deckt 0..2pi ohne Endpunkt ab
    def ab(f, o):
        F = np.fft.fft(f, axis=0); return np.real(np.fft.ifft(F * (k[:, None] ** o), axis=0))
    d1, d2, d3 = ab(X, 1), ab(X, 2), ab(X, 3)
    c = np.cross(d1, d2); cn = np.linalg.norm(c, axis=1); v = np.linalg.norm(d1, axis=1)
    kappa = cn / v ** 3; tau = (c * d3).sum(1) / np.maximum(cn ** 2, 1e-30)
    return kappa, tau, v


# ---------------------------------------------------------------- Teil 1: lokal
FORM_NAME = {"do3": "Do3Qy", "k3": "K3 halb", "dje": "DjLe3eL6", "d8z": "D8ZNt2"}


def _rand_arrays(form):
    from stellarator.qi_karte import rand
    b, _ = rand(form)
    return np.array(b["r_cos"], float), np.array(b["z_sin"], float), int(b["n_field_periods"])


def _spearman(a, b):
    from scipy.stats import spearmanr
    ok = np.isfinite(a) & np.isfinite(b)
    return float(spearmanr(a[ok], b[ok])[0])


def _teil(x, y, z):
    """Partielle Rangkorrelation x,y gegeben z."""
    from scipy.stats import rankdata
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    def res(a, b):
        A = np.column_stack([np.ones_like(b), b]); return a - A @ np.linalg.lstsq(A, a, rcond=None)[0]
    ex, ey = res(rx, rz), res(ry, rz)
    return float(np.corrcoef(ex, ey)[0, 1])


def lokal():
    from scipy.spatial import cKDTree
    K3D = ROOT / "sim" / "qi_flaeche" / "karte3d"
    formen = [f for f in ("do3", "k3", "dje", "d8z") if (K3D / f"{f}.npz").exists()]
    erg = {}
    BILD.mkdir(parents=True, exist_ok=True)
    for form in formen:
        z = np.load(K3D / f"{form}.npz"); j = json.loads((K3D / f"{form}.json").read_text())
        Xq, Q = z["X"][-1], z["Q"][-1]                       # Randflaeche (s = 0,995), Boozer-Gitter (73 x nfp*72+1)
        Xq, Q = Xq[:-1, :-1].reshape(-1, 3), Q[:-1, :-1].ravel()
        rc, zs, nfp = _rand_arrays(form)
        d = flaeche(rc, zs, nfp, nth=180, nph=720, ganz=True)
        kr = kruemmungen(d); qs = querschnitt(d)
        kap, tau, v = achse_kt(qs["Rc"], qs["Zc"], d["ph"])
        # Drehrate des Querschnitts je Bogenlaenge der Achse und je Toroidalwinkel
        dwin = np.gradient(qs["winkel"], d["ph"])         # rad je rad Toroidalwinkel
        dwin_s = dwin / v                                 # rad je m Achsenlaenge
        # Kruemmungsstetigkeit: Ableitung von kmax nach Bogenlaenge auf der Flaeche (Betrag des Flaechengradienten)
        km = kr["kmax"]
        gu = np.gradient(km, d["th"], axis=0); gv = np.gradient(km, d["ph"], axis=1)
        Xu_n = np.hypot(d["Ru"], d["Zu"]); Xv_n = np.sqrt(d["Rv"] ** 2 + d["R"] ** 2 + d["Zv"] ** 2)
        dk = np.hypot(gu / Xu_n, gv / Xv_n)
        # Abbildung: lokaler QI-Wert (Boozer-Punkte) auf das Geometriegitter per naechstem Nachbarn im Raum
        baum = cKDTree(Xq); P = kr["X"].reshape(-1, 3); dist, idx = baum.query(P)
        q = Q[idx].reshape(km.shape)
        # Lagefehler: s = 0,995 gegen s = 1 (Abstand ist Massstab fuer die Zuordnung)
        a_min = np.sqrt(qs["A"].mean() / np.pi)
        pw = {"K_gauss": kr["K"], "H_mittel": kr["H"], "k_max": km, "dk_ds": dk}
        # je Toroidalwinkel (2 Grad Faecher) gemittelt
        grad = np.degrees(d["ph"]); fach = (grad // 2).astype(int)
        qf = np.array([q[:, fach == i].mean() for i in range(180)])
        tor = {"Achsenkruemmung": kap, "Achsentorsion": tau, "Drehrate_Querschnitt": np.abs(dwin_s), "Elongation": qs["elong"],
               "k_max_Umfangsmittel": km.mean(0), "dk_ds_Umfangsmittel": dk.mean(0), "K_gauss_Umfangsmittel": kr["K"].mean(0),
               "Drehrate_gewichtet": np.abs(dwin_s) * (qs["elong"] ** 2 - 1) / (qs["elong"] ** 2 + 1), "Torsion_kappa2": kap ** 2 * np.abs(tau),
               "Null_cos_nfp_phi": np.cos(nfp * d["ph"]), "Null_cos_2nfp_phi": np.cos(2 * nfp * d["ph"])}
        torf = {k: np.array([v_[fach == i].mean() for i in range(180)]) for k, v_ in tor.items()}
        e = {"nfp": nfp, "zuordnung_abstand_mittel_m": float(dist.mean()), "zuordnung_abstand_max_m": float(dist.max()), "a_min_m": float(a_min),
             "qi_flaeche_geometrie_gitter": float(np.average(q, weights=kr["J"])), "qi_flaeche_offiziell": j["qi_flaeche"][-1],
             "punktweise": {k: _spearman(v_.ravel(), q.ravel()) for k, v_ in pw.items()},
             "je_2grad": {k: _spearman(v_, qf) for k, v_ in torf.items()},
             "je_2grad_teil_elongation": {k: _teil(v_, qf, torf["Elongation"]) for k, v_ in torf.items() if k != "Elongation"},
             "punktweise_teil_elongation": {k: _teil(v_.ravel(), q.ravel(), np.broadcast_to(qs["elong"][None], km.shape).ravel()) for k, v_ in pw.items()},
             "werte": {"Achsentorsion_mittel_1/m": float(np.mean(tau)), "Achsenkruemmung_mittel_1/m": float(np.mean(kap)),
                       "Drehrate_Integral_rad": float(np.sum(np.abs(np.diff(qs['winkel']))) ), "Drehrate_netto_rad": float(qs["winkel"][-1] - qs["winkel"][0]),
                       "k_max_p99_1/m": float(np.percentile(km, 99)), "k_max_mal_a_p99": float(np.percentile(km, 99) * a_min),
                       "Elongation_max": float(qs["elong"].max()), "R0_m": float(rc[0, (rc.shape[1] - 1) // 2])}}
        erg[form] = e
        np.savez_compressed(AUS / f"lokal_{form}.npz", q=q, qf=qf, **{k: v_ for k, v_ in pw.items()}, **{"t_" + k: v_ for k, v_ in torf.items()},
                            winkel=qs["winkel"], ph=d["ph"], th=d["th"])
        print(form, json.dumps(e, indent=1), flush=True)
    (AUS / "lokal.json").write_text(json.dumps(erg, indent=1))
    lokal_bilder(erg)


def lokal_bilder(erg):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    farbe = {"do3": "#1b6ca8", "k3": "#2a9d8f", "d8z": "#c0392b", "dje": "#8e6c8a"}
    fs = list(erg)
    # Bild 1: je Form Toroidalverlauf (2 Grad): lokaler QI, Drehrate, Achsentorsion, Achsenkruemmung, k_max, Elongation
    gr = ["qf", "t_Drehrate_Querschnitt", "t_Achsentorsion", "t_Achsenkruemmung", "t_k_max_Umfangsmittel", "t_dk_ds_Umfangsmittel", "t_Elongation"]
    tit = ["lokaler QI (Mittel über den Umfang)", "Drehrate des Querschnitts |dψ/ds| (rad/m)", "Torsion der Mittellinie τ (1/m)",
           "Krümmung der Mittellinie κ (1/m)", "größte Flächenkrümmung (Umfangsmittel, 1/m)", "Krümmungsänderung |∇k| (Umfangsmittel, 1/m²)", "Elongation des Querschnitts"]
    fig, ax = plt.subplots(len(gr), 1, figsize=(9, 13), sharex=True, constrained_layout=True)
    for f in fs:
        z = np.load(AUS / f"lokal_{f}.npz"); x = np.arange(180) * 2 + 1
        for a, g in zip(ax, gr):
            y = z[g]
            if g == "qf":
                y = y / y.mean()
            a.plot(x, y, color=farbe[f], lw=1.2, label=f"{FORM_NAME[f]} (nfp {erg[f]['nfp']})")
    for a, t in zip(ax, tit):
        a.set_ylabel(t, fontsize=7); a.grid(alpha=0.3)
    ax[0].set_ylabel("lokaler QI / Flächenmittel", fontsize=7); ax[0].set_yscale("log"); ax[0].legend(fontsize=7, ncol=4)
    ax[-1].set_xlabel("Toroidalwinkel φ (Grad, ganzer Umlauf)")
    fig.suptitle("Verlauf entlang des Rings (je 2°): QI-Fehler und Verdrillungs-/Krümmungsmaße", fontsize=10)
    fig.savefig(BILD / "verlauf_toroidal.png", dpi=110); plt.close(fig)
    # Bild 2: Rangkorrelationen je Form als Balken (je 2 Grad und punktweise)
    for art, schl in (("je_2grad", "je 2° Toroidalwinkel"), ("punktweise", "punktweise auf der Fläche")):
        ks = list(erg[fs[0]][art])
        fig, ax = plt.subplots(figsize=(9, 4.2), constrained_layout=True)
        w = 0.8 / len(fs)
        for i, f in enumerate(fs):
            ax.bar(np.arange(len(ks)) + i * w - 0.4 + w / 2, [erg[f][art][k] for k in ks], w, color=farbe[f], label=FORM_NAME[f])
        ax.axhline(0, color="k", lw=0.8); ax.axhspan(-0.4, 0.4, color="gray", alpha=0.12, label="Erwartung |ρ| < 0,4")
        ax.set_xticks(range(len(ks))); ax.set_xticklabels([{"K_gauss": "Gauß-Krümmung", "H_mittel": "mittlere Krümmung", "k_max": "größte Hauptkrümmung", "dk_ds": "Krümmungsänderung", "Null_cos_nfp_phi": "Vergleich ohne Geometrie:\ncos(nfp·φ)", "Null_cos_2nfp_phi": "Vergleich ohne Geometrie:\ncos(2·nfp·φ)"}.get(k, k.replace("_", " ")) for k in ks], rotation=25, ha="right", fontsize=8)
        ax.set_ylabel("Spearman ρ mit lokalem QI"); ax.set_ylim(-1, 1); ax.legend(fontsize=7, ncol=5)
        ax.set_title(f"Rangkorrelation lokaler QI gegen Geometrie, {schl} (positiv: mehr davon = mehr QI-Fehler)", fontsize=9)
        fig.savefig(BILD / f"korrelation_{art}.png", dpi=110); plt.close(fig)
    # Bild 3: Karten (theta x phi) einer Form: lokaler QI und k_max und dk
    for f in fs:
        z = np.load(AUS / f"lokal_{f}.npz")
        fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True, constrained_layout=True)
        for a, (g, t, cm) in zip(ax, (("q", "lokaler QI-Wert", "inferno"), ("k_max", "größte Hauptkrümmung |k| (1/m)", "viridis"), ("dk_ds", "Krümmungsänderung |∇k| (1/m²)", "viridis"))):
            v = z[g]; im = a.pcolormesh(np.degrees(z["ph"]), np.degrees(z["th"]), v, cmap=cm, vmin=0, vmax=np.percentile(v, 99), shading="auto", rasterized=True)
            fig.colorbar(im, ax=a, label=t); a.set_ylabel("Umfangswinkel θ (Grad)")
        ax[-1].set_xlabel("Toroidalwinkel φ (Grad)")
        fig.suptitle(f"{FORM_NAME[f]}: Randfläche abgewickelt, oben QI-Fehler, darunter Krümmung und Krümmungsänderung", fontsize=10)
        fig.savefig(BILD / f"karte_{f}.png", dpi=100); plt.close(fig)


# ---------------------------------------------------------------- Teil 2: Datensatz
def masse_koeff(rc, zs, nfp, nth=48, nph=48):
    """Verdrillungs- und Kruemmungsmasse einer Form (eine Periode reicht, Massstab = kleiner Radius a)."""
    d = flaeche(rc, zs, nfp, nth=nth, nph=nph, ganz=False)
    kr = kruemmungen(d); qs = querschnitt(d)
    a = np.sqrt(qs["A"].mean() / np.pi); R0 = rc[0, (rc.shape[1] - 1) // 2]
    # Mittellinie ueber den ganzen Umlauf (Periode wiederholen)
    ph = np.linspace(0, 2 * np.pi, nph * nfp, endpoint=False)
    Rc, Zc = np.tile(qs["Rc"], nfp), np.tile(qs["Zc"], nfp)
    kap, tau, v = achse_kt(Rc, Zc, ph)
    w = qs["winkel"]
    # Netto-Drehung je Periode (Ellipsenwinkel ist nur mod pi bestimmt): Periode verlaengern und aufwickeln
    netto = (w[-1] - w[0]) * nph / (nph - 1)
    dwin = np.gradient(np.unwrap(2 * w) / 2, d["ph"])
    km = kr["kmax"]
    gu = np.gradient(km, d["th"], axis=0); gv = np.gradient(km, d["ph"], axis=1)
    Xu_n = np.hypot(d["Ru"], d["Zu"]); Xv_n = np.sqrt(d["Rv"] ** 2 + d["R"] ** 2 + d["Zv"] ** 2)
    dk = np.hypot(gu / Xu_n, gv / Xv_n)
    L = v.mean() * 2 * np.pi                      # Laenge der Mittellinie
    return {
        "achsentorsion_mal_a": float(np.mean(np.abs(tau)) * a),
        "achsentorsion_mal_R0": float(np.mean(np.abs(tau)) * R0),
        "achsenkruemmung_mal_a": float(np.mean(kap) * a),
        "achsenkruemmung_max_mal_R0": float(np.max(kap) * R0),
        "drehrate_integral_je_periode": float(np.sum(np.abs(np.gradient(np.unwrap(2 * w) / 2))) ),   # rad je Periode (Betrag, aufsummiert)
        "drehrate_max_mal_a": float(np.max(np.abs(dwin)) / v.mean() * a),
        "netto_drehung_je_periode": float(abs(netto)),
        "drehrate_gewichtet_je_periode": float(np.sum(np.abs(np.gradient(np.unwrap(2 * w) / 2)) * (qs["elong"] ** 2 - 1) / (qs["elong"] ** 2 + 1))),
        "achsentorsion_median_mal_a": float(np.median(np.abs(tau)) * a),
        "torsion_kappa2_mal_a3": float(np.mean(kap ** 2 * np.abs(tau)) * a ** 3),
        "kmax_mittel_mal_a": float(np.average(km, weights=kr["J"]) * a),
        "kmax_p99_mal_a": float(np.percentile(km, 99) * a),
        "kruemmungsaenderung_mal_a2": float(np.average(dk, weights=kr["J"]) * a ** 2),
        "kruemmungsaenderung_p99_mal_a2": float(np.percentile(dk, 99) * a ** 2),
        "gauss_neg_anteil": float(np.average(kr["K"] < 0, weights=kr["J"])),
        "elong_geo_max": float(qs["elong"].max()),
        "aspekt_geo": float(R0 / a),
        "_L_mal_1/a": float(L / a),
    }


def datensatz():
    import glob
    import pyarrow.parquet as pq
    f_cache = AUS / "datensatz_masse.npz"
    AUS.mkdir(parents=True, exist_ok=True)
    spalten = ["plasma_config_id", "metrics.qi", "boundary.n_field_periods", "boundary.r_cos", "boundary.z_sin", "metrics.aspect_ratio",
               "metrics.max_elongation", "metrics.edge_rotational_transform_over_n_field_periods", "metrics.axis_rotational_transform_over_n_field_periods",
               "metrics.edge_magnetic_mirror_ratio", "metrics.axis_magnetic_mirror_ratio", "metrics.average_triangularity", "metrics.vacuum_well",
               "metrics.minimum_normalized_magnetic_gradient_scale_length"]
    if f_cache.exists():
        print("Masse aus Zwischenspeicher"); z = np.load(f_cache, allow_pickle=True); D = {k: z[k] for k in z.files}
    else:
        D = {k: [] for k in spalten[1:3] + spalten[5:]}; D["masse"] = []; namen = None; t0 = time.time(); n = 0
        for fn in sorted(glob.glob(str(ROOT / "sim/rohdaten/constellaration/train-*.parquet"))):
            pf = pq.ParquetFile(fn)
            for b in pf.iter_batches(batch_size=5000, columns=spalten):
                t = b.to_pydict()
                for i in range(b.num_rows):
                    qi = t["metrics.qi"][i]
                    if qi is None or not np.isfinite(qi) or qi <= 0 or t["boundary.r_cos"][i] is None:
                        continue
                    try:
                        mm = masse_koeff(np.array(t["boundary.r_cos"][i], float), np.array(t["boundary.z_sin"][i], float), int(t["boundary.n_field_periods"][i]))
                    except Exception:
                        continue
                    if namen is None:
                        namen = list(mm)
                    D["masse"].append([mm[k] for k in namen])
                    for k in spalten[1:3] + spalten[5:]:
                        x = t[k][i]; D[k].append(np.nan if x is None else float(x))
                    n += 1
                print(fn[-30:], n, f"{time.time() - t0:.0f} s", flush=True)
        D = {k: np.array(v, float) for k, v in D.items()}; D["namen"] = np.array(namen)
        np.savez_compressed(f_cache, **D)
    auswerten(D)


def auswerten(D):
    from scipy.stats import spearmanr
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    namen = [str(x) for x in D["namen"]]; Mx = D["masse"]; qi = D["metrics.qi"]; nfp = D["boundary.n_field_periods"]; asp = D["metrics.aspect_ratio"]
    y = np.log10(qi)
    kenn = [k for k in D if k.startswith("metrics.") and k != "metrics.qi"]
    Kx = np.column_stack([D[k] for k in kenn])
    ok = np.isfinite(y) & np.isfinite(Mx).all(1) & np.isfinite(Kx).all(1)
    print("gueltig", ok.sum(), "von", len(y))
    sel = [i for i, n in enumerate(namen) if not n.startswith("_")]
    erg = {"n": int(ok.sum()), "namen": [namen[i] for i in sel], "gesamt": {}, "je_nfp": {}, "je_aspekt": {}, "modelle": {}}
    for i in sel:
        erg["gesamt"][namen[i]] = float(spearmanr(Mx[ok, i], y[ok])[0])
    for p in sorted(set(nfp[ok].astype(int))):
        m = ok & (nfp == p)
        if m.sum() > 200:
            erg["je_nfp"][str(p)] = {"n": int(m.sum()), **{namen[i]: float(spearmanr(Mx[m, i], y[m])[0]) for i in sel}}
    klassen = [("<6", 0, 6), ("6-10", 6, 10), ("10-14", 10, 14), (">14", 14, 1e9)]
    for nm, lo, hi in klassen:
        m = ok & (asp >= lo) & (asp < hi)
        if m.sum() > 200:
            erg["je_aspekt"][nm] = {"n": int(m.sum()), **{namen[i]: float(spearmanr(Mx[m, i], y[m])[0]) for i in sel}}
    # Kreuz: Aspektklasse x nfp fuer die zwei wichtigsten Masse
    erg["kenn_zu_massen"] = {namen[i]: {k: float(spearmanr(Mx[ok, i], D[k][ok])[0]) for k in ("metrics.aspect_ratio", "metrics.max_elongation",
                             "metrics.edge_rotational_transform_over_n_field_periods", "metrics.axis_magnetic_mirror_ratio")} for i in sel}
    # Modelle: (A) bekannte Kennzahlen + nfp; (B) A + Masse; (C) nur Masse + nfp + Aspekt
    X_A = np.column_stack([Kx[ok], nfp[ok]]); X_M = Mx[ok][:, sel]; yy = y[ok]
    X_B = np.column_stack([X_A, X_M]); X_C = np.column_stack([X_M, nfp[ok], asp[ok]])
    idx = np.arange(len(yy)); it, iv = train_test_split(idx, test_size=0.2, random_state=0)
    for nm, X in (("A_kennzahlen", X_A), ("B_kennzahlen_plus_masse", X_B), ("C_nur_masse_nfp_aspekt", X_C), ("D_nur_nfp_aspekt", np.column_stack([nfp[ok], asp[ok]]))):
        g = HistGradientBoostingRegressor(max_iter=400, random_state=0).fit(X[it], yy[it])
        erg["modelle"][nm] = float(g.score(X[iv], yy[iv])); print(nm, erg["modelle"][nm], flush=True)
    (AUS / "datensatz.json").write_text(json.dumps(erg, indent=1)); print(json.dumps(erg, indent=1))
    datensatz_bilder(D, ok, erg, sel, namen)


def datensatz_bilder(D, ok, erg, sel, namen):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    BILD.mkdir(parents=True, exist_ok=True)
    y = np.log10(D["metrics.qi"]); Mx = D["masse"]; asp = D["metrics.aspect_ratio"]; nfp = D["boundary.n_field_periods"]
    # Kastenbild: QI in Quintilen von Drehrate-Integral und Kruemmungsaenderung, je Aspektklasse
    zeige = ["drehrate_integral_je_periode", "achsentorsion_mal_a", "kmax_p99_mal_a", "kruemmungsaenderung_mal_a2"]
    tit = {"drehrate_integral_je_periode": "Drehung des Querschnitts je Periode (rad)", "achsentorsion_mal_a": "Torsion der Mittellinie × a",
           "kmax_p99_mal_a": "größte Randkrümmung (p99) × a", "kruemmungsaenderung_mal_a2": "Krümmungsänderung × a²"}
    klassen = [k for k in [("<6", 0, 6), ("6-10", 6, 10), ("10-14", 10, 14), (">14", 14, 1e9)] if k[0] in erg["je_aspekt"]]
    fig, ax = plt.subplots(len(zeige), len(klassen), figsize=(11, 11), sharey=True, constrained_layout=True)
    for r, k in enumerate(zeige):
        i = namen.index(k)
        for c, (nm, lo, hi) in enumerate(klassen):
            m = ok & (asp >= lo) & (asp < hi); a = ax[r, c]
            if m.sum() < 200:
                a.set_visible(False); continue
            x = Mx[m, i]; qu = np.percentile(x, [0, 20, 40, 60, 80, 100])
            grp = [y[m][(x >= qu[j]) & (x <= qu[j + 1])] for j in range(5)]
            a.boxplot(grp, showfliers=False, widths=0.6)
            a.set_xticks(range(1, 6)); a.set_xticklabels([f"{np.median(x[(x >= qu[j]) & (x <= qu[j + 1])]):.2g}" for j in range(5)], fontsize=7)
            a.set_title(f"A {nm} (n={m.sum()}), ρ={erg['je_aspekt'][nm][k]:+.2f}", fontsize=8)
            if c == 0:
                a.set_ylabel("log10(QI)\n(tiefer = besser)", fontsize=8)
            a.set_xlabel(tit[k] + "\n(Fünftel, Zahl = Median)", fontsize=7); a.grid(alpha=0.3)
    fig.suptitle("Datensatz: QI-Fehler je Fünftel des Maßes, getrennt nach Aspektverhältnis-Klasse (Kasten: mittlere Hälfte, Strich: Median)", fontsize=10)
    fig.savefig(BILD / "datensatz_kasten.png", dpi=100); plt.close(fig)
    # Waermebild Spearman (Mass x Gruppe)
    gruppen = [("gesamt", erg["gesamt"])] + [(f"nfp {p}", v) for p, v in erg["je_nfp"].items()] + [(f"A {k}", v) for k, v in erg["je_aspekt"].items()]
    S = np.array([[g[1][namen[i]] for g in gruppen] for i in sel])
    fig, ax = plt.subplots(figsize=(11, 6), constrained_layout=True)
    im = ax.imshow(S, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
    for r in range(S.shape[0]):
        for c in range(S.shape[1]):
            ax.text(c, r, f"{S[r, c]:+.2f}", ha="center", va="center", fontsize=7)
    ax.set_xticks(range(len(gruppen))); ax.set_xticklabels([g[0] for g in gruppen], rotation=30, ha="right", fontsize=8)
    lesbar = {"achsentorsion_mal_a": "Torsion Mittellinie (Mittel) × a", "achsentorsion_mal_R0": "Torsion Mittellinie (Mittel) × R0",
              "achsenkruemmung_mal_a": "Krümmung Mittellinie (Mittel) × a", "achsenkruemmung_max_mal_R0": "Krümmung Mittellinie (max) × R0",
              "drehrate_integral_je_periode": "Drehung Querschnitt je Periode (Summe, rad)", "drehrate_max_mal_a": "größte Drehrate Querschnitt × a",
              "netto_drehung_je_periode": "Netto-Drehung Querschnitt je Periode", "drehrate_gewichtet_je_periode": "Drehung je Periode, mit Ovalität gewichtet",
              "achsentorsion_median_mal_a": "Torsion Mittellinie (Median) × a", "torsion_kappa2_mal_a3": "Torsion × Krümmung² × a³",
              "kmax_mittel_mal_a": "größte Hautkrümmung (Mittel) × a", "kmax_p99_mal_a": "größte Hautkrümmung (p99) × a",
              "kruemmungsaenderung_mal_a2": "Krümmungsänderung (Mittel) × a²", "kruemmungsaenderung_p99_mal_a2": "Krümmungsänderung (p99) × a²",
              "gauss_neg_anteil": "Anteil Sattelfläche (Gauß-Krümmung < 0)", "elong_geo_max": "größte Elongation (geometrisch)", "aspekt_geo": "Aspektverhältnis R00/a"}
    ax.set_yticks(range(len(sel))); ax.set_yticklabels([lesbar.get(namen[i], namen[i]) for i in sel], fontsize=8)
    fig.colorbar(im, label="Spearman ρ mit log10(QI): rot = mehr davon, schlechteres QI")
    ax.set_title("Datensatz: Rangkorrelation der Verdrillungs-/Krümmungsmaße mit dem QI-Fehler", fontsize=10)
    fig.savefig(BILD / "datensatz_korrelation.png", dpi=110); plt.close(fig)


# ---------------------------------------------------------------- Teil 3: Auswertung
def r00bilder():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    BILD.mkdir(parents=True, exist_ok=True)
    zeilen = ["| Form | Faktor R00 | QI | Aspektverhältnis | iota/nfp Rand | Spiegel Rand | max. Elongation | Vakuummulde | Rechenzeit s | Fehler |", "|---|---|---|---|---|---|---|---|---|---|"]
    fig, ax = plt.subplots(2, 3, figsize=(14, 7.5), constrained_layout=True); ax = ax.ravel()
    gr = [("qi", "QI (kleiner = besser)", True), ("edge_rotational_transform_over_n_field_periods", "iota je Periode am Rand", False),
          ("edge_magnetic_mirror_ratio", "Spiegelverhältnis Rand", False), ("max_elongation", "max. Elongation", False), ("vacuum_well", "Vakuummulde (positiv = Mulde)", False)]
    erg = {}
    for form, farbe in (("do3", "#1b6ca8"), ("dje", "#8e6c8a")):
        pts = []
        for f in sorted(AUS.glob(f"r00_{form}_*.json")):
            j = json.loads(f.read_text()); fa = float(f.stem.split("_")[-1]); m = j.get("metriken") or {}
            pts.append((fa, m, j))
            zeilen.append(f"| {FORM_NAME[form]} | {fa:.2f} | " + (f"{m['qi']:.4g} | {m['aspect_ratio']:.2f} | {m['edge_rotational_transform_over_n_field_periods']:.4f} | "
                          f"{m['edge_magnetic_mirror_ratio']:.3f} | {m['max_elongation']:.2f} | {m['vacuum_well']:.4f} | {j['sek']:.0f} | – |" if m else f"– | – | – | – | – | – | {j['sek']:.0f} | {j['fehler'][:60]} |"))
        pts.sort(key=lambda t: t[0]); erg[form] = [(p[0], p[1]) for p in pts]
        P = [p for p in pts if p[1]]
        A = [p[1]["aspect_ratio"] for p in P]
        for a, (k, t, lg) in zip(ax, gr):
            a.plot(A, [p[1][k] for p in P], "o-", color=farbe, label=FORM_NAME[form])
            for p in P:
                a.annotate(f"×{p[0]:.2f}", (p[1]["aspect_ratio"], p[1][k]), fontsize=6, xytext=(3, 3), textcoords="offset points")
            a.set_title(t, fontsize=9); a.set_xlabel("Aspektverhältnis R/a (nur R00 verändert)"); a.grid(alpha=0.3)
            if lg:
                a.set_yscale("log")
        for f in sorted(AUS.glob(f"skal_{form}_*.json")):
            j = json.loads(f.read_text()); m = j.get("metriken") or {}
            b = json.loads((AUS / f"r00_{form}_1.00.json").read_text()).get("metriken") if (AUS / f"r00_{form}_1.00.json").exists() else None
            zeilen.append(f"| {FORM_NAME[form]} | alles ×{f.stem.split('_')[-1]} | " + (f"{m['qi']:.10g} (×1: {b['qi']:.10g}, rel. {abs(m['qi']-b['qi'])/b['qi']:.1e}) | {m['aspect_ratio']:.4f} | "
                          f"{m['edge_rotational_transform_over_n_field_periods']:.6f} | {m['edge_magnetic_mirror_ratio']:.6f} | {m['max_elongation']:.4f} | {m['vacuum_well']:.6f} | {j['sek']:.0f} | – |" if (m and b) else f"– | | | | | | {j['sek']:.0f} | {j.get('fehler')} |"))
    ax[0].axhline(10 ** -3.5, color="gray", ls="--", lw=1); ax[0].text(ax[0].get_xlim()[0], 10 ** -3.5 * 1.1, "Aufgabe 3: 0,00032", fontsize=7, color="gray")
    ax[0].legend(fontsize=8)
    ax[5].axis("off")
    ax[5].text(0, 0.95, "Was wurde gemacht?\nNur der Koeffizient R(0,0) (mittlerer großer Radius)\nwurde mit dem Faktor multipliziert. Querschnittsform,\n"
               "kleiner Radius und Wellung der Achse (alle übrigen\nKoeffizienten) bleiben gleich. Damit wird der Ring\n"
               "dicker/dünner im Verhältnis zum Rohr: das\nAspektverhältnis ändert sich, die Rohrform nicht.\n\nGleichmäßiges Vergrößern (alles ×2 bzw. ×1,7)\nändert QI nicht (Tabelle).\n\nDjLe3eL6 ×0,80: VMEC++ konvergiert nicht\n(kein Punkt).", va="top", fontsize=9)
    fig.suptitle("VMEC++ (Ranglisten-Einstellung): Großer Radius bei festem Querschnitt verändert", fontsize=10)
    fig.savefig(BILD / "r00_reihe.png", dpi=110); plt.close(fig)
    (AUS / "r00_tabelle.md").write_text("\n".join(zeilen) + "\n"); print("\n".join(zeilen))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "r00":
        r00(sys.argv[2], float(sys.argv[3]))
    elif c == "skal":
        skal(sys.argv[2], float(sys.argv[3]))
    else:
        {"d8z3d": d8z3d, "lokal": lokal, "datensatz": datensatz, "r00bilder": r00bilder}[c]()
