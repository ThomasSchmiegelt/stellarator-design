"""k6_wandlast.py -- K6: Waermebilanz bis zum Netz und Wandlastkarte (Neutronen, Alpha-Treffer aus K3, Strahlung).
KI-generiert (Claude Sonnet 5.5, 2026-11-13).  Erwartung: sim/kandidat/erwartung/K6.md (nicht aendern).  Eingabe: sim/kandidat/kandidat.json, K3-Ergebnis (lastkarte_alpha.npz, auswertung.json).
Aufruf (Projektordner):  .venv-opt/bin/python -m stellarator.k6_wandlast [--test]      (--test: K3-Testordner, grobe Aufloesung, Ausgabe nach sim/kandidat/K6/test/)
Verfahren:
  Bilanz: stellarator/waermebilanz.bilanz() (ohne dessen Dateiausgabe) mit P_netz aus kandidat.json, S = Plasmarandflaeche aus dem wout (Quadratur), sonst Vorgaben des Werkzeugs (eta 0,35, M 1,15, f_p 0,04, P_eigen 60 MW, f_div 0,5).
  Neutronen: isotrope Quelle ~ n^2 <sigma v>(T) (Stufe-0-Profile) im Plasmavolumen (VMEC-Jacobi), geradlinige Strahlen, Einfall cos zur Wandnormalen (Sichtfaktor-Methode, ohne Streuung, ohne Abschattung durch
  Gegenwand); danach so normiert, dass die Summe ueber die Wand gleich P_neutronen ist (Normierungsfaktor wird gemeldet). Wand = Plasmarandflaeche s = 1 (ANNAHME, Erste Wand liegt real einige dm weiter aussen).
  Strahlung: Bremsstrahlung gleichmaessig (P_br aus Stufe 0 neu gerechnet fuer R0 des Kandidaten). Alpha: P_alpha x Verlustanteil bis t_max (K3, Spulenfeld, ueber beide Startflaechen gemittelt) verteilt nach lastkarte_alpha.npz."""
import json, os, sys, time
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[1]
TEST = "--test" in sys.argv
OUT = P / "sim/kandidat/K6" / ("test" if TEST else "lauf"); OUT.mkdir(parents=True, exist_ok=True)
K3 = P / "sim/kandidat/K3" / ("test" if TEST else "lauf")
sys.path.insert(0, str(P))
K = json.loads((P / "sim/kandidat/kandidat.json").read_text())
os.environ.update(ALPHA_WOUT=str(Path(K["wout"]).expanduser()), ALPHA_SPULEN="-", ALPHA_STUFE0="-", ALPHA_AUS="-", ALPHA_R0U="1", ALPHA_R0="1", ALPHA_B0="1")
import stellarator.alpha_bahnen as ab  # noqa: E402  (nur wout(), vmec_punkt())
from invers.stufe0_bilanz import sigma_v, E_FUS, F_ALPHA  # noqa: E402


def wand(w, nth, nph, k):
    """Plasmarand s = 1: Punkte, Normalen (aussen), Flaechenelemente; Anlagengroesse (m)."""
    xm, xn, nfp = w["xm"], w["xn"], w["nfp"]; r, z = w["rmnc"][-1], w["zmns"][-1]
    th = (np.arange(nth) + .5) / nth * 2 * np.pi; ph = (np.arange(nph) + .5) / nph * 2 * np.pi
    T, Ph = np.meshgrid(th, ph, indexing="ij"); a = xm[:, None, None] * T - xn[:, None, None] * Ph
    R = (r[:, None, None] * np.cos(a)).sum(0); Z = (z[:, None, None] * np.sin(a)).sum(0)
    Rt = (-r[:, None, None] * xm[:, None, None] * np.sin(a)).sum(0); Zt = (z[:, None, None] * xm[:, None, None] * np.cos(a)).sum(0)
    Rp = (r[:, None, None] * xn[:, None, None] * np.sin(a)).sum(0); Zp = (-z[:, None, None] * xn[:, None, None] * np.cos(a)).sum(0)
    c, s = np.cos(Ph), np.sin(Ph); X = np.stack([R * c, R * s, Z], -1)
    t1 = np.stack([Rt * c, Rt * s, Zt], -1); t2 = np.stack([Rp * c - R * s, Rp * s + R * c, Zp], -1)
    n = np.cross(t1, t2); dA = np.linalg.norm(n, axis=-1); n /= dA[..., None]
    mitte = np.stack([np.cos(Ph) * R.mean(), np.sin(Ph) * R.mean(), 0 * Z], -1)          # Kreis um die Hauptachse als grobe Aussenrichtung
    if np.mean(np.sum(n * (X - mitte), -1)) < 0:
        n = -n
    dA = dA * (2 * np.pi / nth) * (2 * np.pi / nph) * k ** 2
    return X * k, n, dA, th, ph


def main():
    from stellarator.waermebilanz import bilanz
    from argparse import Namespace
    t0 = time.strftime("%F %T"); P1 = json.loads((P / K["k2"] / "P1.json").read_text()); k = P1["faktor_k"]
    bil = json.loads((P / P1["quellen"]["bilanz"]).read_text()); A = bil["annahmen"]
    if not (K3 / "auswertung.json").exists() or not (K3 / "lastkarte_alpha.npz").exists():
        (OUT / "HALT.txt" if TEST else OUT.parent / "ERGEBNIS.md").write_text(f"HALT: K3-Ergebnis fehlt ({K3.relative_to(P)})\n"); print("HALT: K3 fehlt"); sys.exit(3)
    wd = ab.wout(); nth, nph = (24, 48) if TEST else (48, 192); ns, nst, nsp = (6, 12, 24) if TEST else (24, 36, 96)
    X, N, dA, th, ph = wand(wd, nth, nph, k); S = float(dA.sum())
    S_stufe0 = bil["form"]["S_R2"] * K["R0_m"] ** 2; S_ueberschlag = 7.9 * K["R0_m"] ** 2
    a = Namespace(P_netz=K["P_netz_MW"], P_eigen=60.0, eta=0.35, f_p=0.04, M=1.15, f_div=0.5, div_nutzbar=1.0, S=S, q_div=10.0, dT=30.0)
    b = bilanz(a)
    # Stufe-0-Profile fuer R0 des Kandidaten
    T0 = json.loads((P / K.get("groesse", "sim/kette_dgoz/groesse/j15/runden.json")).read_text())["runden"][-1]["stufe0"]["T0_keV"]
    V = bil["form"]["V_R3"] * K["R0_m"] ** 3; rg = np.linspace(0, 1, 201)[1:-1]; wg = 2 * rg * np.gradient(rg); pn, pt = (1 - rg ** 2) ** A["alpha_n"], (1 - rg ** 2) ** A["alpha_T"]
    I_fus = (wg * pn ** 2 * sigma_v(T0 * pt)).sum(); I_br = (wg * pn ** 2 * np.sqrt(T0 * pt)).sum(); nD = A["f_DT"] / 2
    n0 = float(np.sqrt(K["P_fus_MW"] * 1e6 / (nD ** 2 * E_FUS * I_fus * V))); P_br = 5.35e-37 * A["Z_eff"] * n0 ** 2 * I_br * V / 1e6
    # Neutronenquelle: Gitter in (s, theta, phi), Gewicht = n^2 sigma_v * Jacobi
    s_ = (np.arange(ns) + .5) / ns; t_ = (np.arange(nst) + .5) / nst * 2 * np.pi; p_ = (np.arange(nsp) + .5) / nsp * 2 * np.pi
    S3, T3, P3 = np.meshgrid(s_, t_, p_, indexing="ij"); pts, g = ab.vmec_punkt(wd, S3.ravel(), T3.ravel(), P3.ravel()); pts = pts * k
    wq = (1 - S3.ravel()) ** (2 * A["alpha_n"]) * sigma_v(T0 * (1 - S3.ravel()) ** A["alpha_T"]) * g; wq = wq / wq.sum()
    W = X.reshape(-1, 3); Nn = N.reshape(-1, 3); q = np.zeros(len(W))
    for i0 in range(0, len(W), 400):
        d = W[i0:i0 + 400, None, :] - pts[None]; r2 = (d ** 2).sum(-1); cosw = (d * Nn[i0:i0 + 400, None, :]).sum(-1) / np.sqrt(r2)
        q[i0:i0 + 400] = (wq[None] * np.maximum(cosw, 0) / (4 * np.pi * r2)).sum(1)
    sicht = float((q * dA.ravel()).sum())                       # Anteil der Quelle, der ohne Abschattung die Wand trifft (1 = alle; > 1 Mehrfachtreffer an konkaven Stellen)
    qn = q / sicht * b["P_neutronen_MW"]                         # MW/m^2 (normiert auf P_neutronen)
    # Alpha-Treffer aus K3
    aus3 = json.loads((K3 / "auswertung.json").read_text()); lk = np.load(K3 / "lastkarte_alpha.npz")
    anteile = [r["anteil"] for r in aus3["felder"]["spulen"]["flaechen"]]; verlust = float(np.mean(anteile))
    P_alpha_wand = verlust * b["P_alpha_MW"]
    ph_w = np.arctan2(W[:, 1], W[:, 0]); ra = np.hypot(W[:, 0], W[:, 1]); Ra = np.array([sum(wd["raxis_cc"][j] * np.cos(j * wd["nfp"] * x) for j in range(len(wd["raxis_cc"]))) for x in ph_w]) * k
    Za = np.array([-sum(wd["zaxis_cs"][j] * np.sin(j * wd["nfp"] * x) for j in range(len(wd["zaxis_cs"]))) for x in ph_w]) * k
    th_w = np.arctan2(W[:, 2] - Za, ra - Ra)
    H, pe, te = lk["H"], lk["phi_kanten"], lk["theta_kanten"]; nfp = wd["nfp"]
    ib = np.clip(np.digitize(np.mod(ph_w, 2 * np.pi / nfp), pe) - 1, 0, H.shape[0] - 1); jb = np.clip(np.digitize(np.mod(th_w, 2 * np.pi), te) - 1, 0, H.shape[1] - 1)
    f = H[ib, jb].astype(float); f = f / (f * dA.ravel()).sum() if f.sum() > 0 else f
    qa = f * P_alpha_wand                                          # MW/m^2
    qr = np.full(len(W), P_br / S)                                 # Strahlung gleichmaessig
    qe = (qr + qa).reshape(nth, nph); qn2 = qn.reshape(nth, nph)
    erg = {"start": t0, "test": TEST, "R0_m": K["R0_m"], "k": k,
           "bilanz": {k_: b[k_] for k_ in ("P_netz_MW", "P_eigen_MW", "P_th_MW", "P_fus_MW", "P_neutronen_MW", "P_alpha_MW", "P_blanket_MW", "P_erstwand_MW", "P_divertor_MW", "P_brutto_MW", "P_abwaerme_MW")},
           "bilanz_schliessung_prozent": 100 * (b["P_blanket_MW"] + b["P_erstwand_MW"] + b["P_divertor_MW"] - b["P_th_MW"]) / b["P_th_MW"],
           "netto_aus_komponenten_MW": b["P_brutto_MW"] - b["P_eigen_MW"], "P_fus_Stufe0_kandidat_MW": K["P_fus_MW"],
           "flaeche_m2": {"wout_s1_quadratur": S, "stufe0_S_R2": S_stufe0, "ueberschlag_7_9_R0_2": S_ueberschlag},
           "neutronen": {"mittel_MW_m2": float((qn * dA.ravel()).sum() / S), "spitze_MW_m2": float(qn.max()), "p99_MW_m2": float(np.percentile(qn, 99)), "mittel_gleichmaessig_P_n_durch_S": b["P_neutronen_MW"] / S,
                         "sichtfaktor_summe": sicht, "grenze_MW_m2": 2.0, "grenze_art": "Annahme Werkzeug (invers/stufe0_bilanz.py wandlast_max)", "gitter": f"Wand {nth}x{nph}, Quelle {ns}x{nst}x{nsp}"},
           "erste_wand_waerme": {"P_brems_MW": P_br, "q_strahlung_MW_m2": P_br / S, "verlustanteil_alpha_K3": verlust, "P_alpha_wand_MW": P_alpha_wand, "q_alpha_spitze_MW_m2": float(qa.max()),
                                 "q_gesamt_spitze_MW_m2": float(qe.max()), "q_gesamt_mittel_MW_m2": float((qe.ravel() * dA.ravel()).sum() / S), "K3_quelle": K3.relative_to(P).as_posix()},
           "ende": time.strftime("%F %T")}
    ej = {"hinweis": "KI-generiert (Claude Sonnet 5.5); Schnittstelle fuer K7/K10", "erstwand_waermestrom_spitze_MW_m2": erg["erste_wand_waerme"]["q_gesamt_spitze_MW_m2"],
          "erstwand_waermestrom_mittel_MW_m2": erg["erste_wand_waerme"]["q_gesamt_mittel_MW_m2"], "wandlast_neutronen_mittel_MW_m2": erg["neutronen"]["mittel_MW_m2"],
          "wandlast_neutronen_spitze_MW_m2": erg["neutronen"]["spitze_MW_m2"], "P_th_MW": erg["bilanz"]["P_th_MW"], "flaeche_m2": S, "test": TEST}
    (OUT / "ergebnis.json" if TEST else OUT.parent / "ergebnis.json").write_text(json.dumps(ej, indent=1))
    (OUT / "auswertung.json").write_text(json.dumps(erg, indent=1)); np.savez(OUT / "lastkarte_wand.npz", q_neutron=qn2, q_erstewand=qe, th=th, ph=ph, X=X, dA=dA)
    from stellarator.k6_bericht import schreibe
    schreibe(OUT, TEST, erg, qn2, qe, th, ph, X, P if False else (OUT if TEST else P / "video/bausteine/K6")); print(json.dumps({"neutronen": erg["neutronen"]["mittel_MW_m2"], "spitze": erg["neutronen"]["spitze_MW_m2"], "sicht": sicht}), flush=True)


if __name__ == "__main__":
    main()
