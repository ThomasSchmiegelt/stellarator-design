"""k4_gx_einordnen.py -- K4: GX-Waermefluss (gyroBohm-Einheiten) in physikalische Einheiten, gegen den aus der Bilanz noetigen Fluss.
KI-generiert (Claude Sonnet 5.5, 2026-11-13).  Erwartung: sim/kandidat/erwartung/K4.md (nicht aendern).  Eingabe: sim/kandidat/kandidat.json.
Aufruf (Projektordner):  ~/cae_projekte/gx/deps/venv/bin/python stellarator/k4_gx_einordnen.py [--test]   (netCDF4 steckt in dieser venv und in .venv-opt)
Rechnung (alle Festlegungen stehen im Ergebnis als Annahme):
  Q_i/Q_GB (GX, Mittel t >= 100, eine Flussroehre s = 0,64, alpha = 0, a/L_T = 3, a/L_n = 1)  aus dem vorhandenen Lauf linked/<ID>.out.nc;
  Q_GB = n_i T_i v_t (rho_i/a)^2, v_t = sqrt(T_i/m_i), rho_i = m_i v_t/(e B_ref), a = Aminor_p * k, B_ref = 2 |phi_edge/2pi|/Aminor_p^2 * (B0 / B_Achse_wout) (wie GX-Geometrie gx_geo_vmec.py);
  Profile der Stufe-0-Bilanz (T = T0 (1-s)^alpha_T, n = n0 (1-s)^alpha_n, s = rho^2), n_i = n_e, T_i = T_e, m_i = 2,5 u (D-T 1:1);
  noetiger Fluss durch die Flaeche s: (F_alpha(s) P_alpha - F_br(s) P_brems) / S(s), F = Anteil der Profilintegrale bis s, S aus dem wout (Quadratur)."""
import json, sys, time
from pathlib import Path
import numpy as np
import netCDF4

P = Path(__file__).resolve().parents[1]
TEST = "--test" in sys.argv
OUT = P / "sim/kandidat/K4" / ("test" if TEST else "lauf"); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(P))
from invers.stufe0_bilanz import sigma_v  # noqa: E402

KEV, E, U = 1.602176634e-16, 1.602176634e-19, 1.66053906660e-27
S_GX = 0.64


def gx_lesen(pfad, ab=100.0):
    d = netCDF4.Dataset(pfad); t = np.array(d["Grids/time"][:]); q = np.array(d["Diagnostics/HeatFlux_st"][:, 0]); m = t >= ab
    bl = [b.mean() for b in np.array_split(q[m], 4)]
    return {"Q_i": float(q[m].mean()), "fehler": float(np.std(bl, ddof=1) / 2), "t_ende": float(t[-1]), "n_punkte": int(m.sum()), "ab": ab}


def flaeche_wout(w, s, nth=240, nph=240):
    ns = int(w["ns"][:]); sf = np.linspace(0, 1, ns); rm = np.array(w["rmnc"][:]); zm = np.array(w["zmns"][:]); xm = np.array(w["xm"][:]); xn = np.array(w["xn"][:]); nfp = int(w["nfp"][:])
    r = np.array([np.interp(s, sf, rm[:, j]) for j in range(rm.shape[1])]); z = np.array([np.interp(s, sf, zm[:, j]) for j in range(zm.shape[1])])
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False); ph = np.linspace(0, 2 * np.pi / nfp, nph, endpoint=False)
    T, Ph = np.meshgrid(th, ph, indexing="ij"); a = xm[:, None, None] * T - xn[:, None, None] * Ph
    R = (r[:, None, None] * np.cos(a)).sum(0); Z = (z[:, None, None] * np.sin(a)).sum(0)
    Rt = (-r[:, None, None] * xm[:, None, None] * np.sin(a)).sum(0); Zt = (z[:, None, None] * xm[:, None, None] * np.cos(a)).sum(0)
    Rp = (r[:, None, None] * xn[:, None, None] * np.sin(a)).sum(0); Zp = (-z[:, None, None] * xn[:, None, None] * np.cos(a)).sum(0)
    # r = (R cos ph, R sin ph, Z); d/dth = (Rt cos, Rt sin, Zt); d/dph = (Rp cos - R sin, Rp sin + R cos, Zp)
    c, sn = np.cos(Ph), np.sin(Ph)
    t1 = np.stack([Rt * c, Rt * sn, Zt]); t2 = np.stack([Rp * c - R * sn, Rp * sn + R * c, Zp])
    dS = np.linalg.norm(np.cross(t1, t2, axis=0), axis=0)
    return float(dS.sum() * (2 * np.pi / nth) * (2 * np.pi / nfp / nph) * nfp)


def main():
    t0 = time.strftime("%F %T")
    K = json.loads((P / "sim/kandidat/kandidat.json").read_text()); ID = K["id"]
    P1 = json.loads((P / K["k2"] / "P1.json").read_text()); bil = json.loads((P / P1["quellen"]["bilanz"]).read_text())
    A, H = bil["annahmen"], bil["auslegung"]["HTS"]
    gx_ordner = Path.home() / "cae_projekte/gx/laeufe/linked" / ID; gx_datei = gx_ordner / f"{ID}.out.nc"
    if not gx_datei.exists():
        (OUT / "HALT.txt" if TEST else OUT.parent / "ERGEBNIS.md").write_text("HALT: GX-Lauf fehlt (~/cae_projekte/gx/laeufe/linked/<ID>)\n"); print("HALT: GX-Lauf fehlt"); sys.exit(3)
    gx = gx_lesen(gx_datei)
    w = netCDF4.Dataset(str(Path(K["wout"]).expanduser())); k = P1["faktor_k"]
    a_u = float(w["Aminor_p"][:]); phi_edge = float(np.array(w["phi"][:])[-1]) / (2 * np.pi); ns = int(w["ns"][:])
    xm = np.array(w["xm_nyq"][:]); xn = np.array(w["xn_nyq"][:]); b = np.array(w["bmnc"][:]); i00 = int(np.where((xm == 0) & (xn == 0))[0][0])
    B_axis_u = float(2 * b[1, i00] - b[2, i00])                         # lineare Extrapolation der Halbgitterwerte auf s = 0
    Bref_u = 2 * abs(phi_edge) / a_u ** 2                               # wie gx_geo_vmec.py Zeile 550
    a_phys = a_u * k; B_ref = Bref_u * K["B0_T"] / B_axis_u
    # Plasma bei R0 des Kandidaten: die Bilanzdatei traegt die Groesse nur in R0, B0, I (k2d_groesse), nicht n, V, P_brems -> hier wie invers/stufe0_bilanz.raster neu gerechnet
    from invers.stufe0_bilanz import E_FUS, F_ALPHA
    R0, T0 = K["R0_m"], H["T0_keV"]; V = bil["form"]["V_R3"] * R0 ** 3; rho_g = np.linspace(0, 1, 201)[1:-1]; wg = 2 * rho_g * np.gradient(rho_g)
    pn, pt = (1 - rho_g ** 2) ** A["alpha_n"], (1 - rho_g ** 2) ** A["alpha_T"]; Tr = T0 * pt
    I_fus = (wg * pn ** 2 * sigma_v(Tr)).sum(); I_br = (wg * pn ** 2 * np.sqrt(Tr)).sum(); nD = A["f_DT"] / 2
    n0 = float(np.sqrt(K["P_fus_MW"] * 1e6 / (nD ** 2 * E_FUS * I_fus * V))); n_m = n0 * (wg * pn).sum(); P_alpha = F_ALPHA * K["P_fus_MW"]
    P_br = 5.35e-37 * A["Z_eff"] * n0 ** 2 * I_br * V / 1e6
    s = S_GX; T = T0 * (1 - s) ** A["alpha_T"]; n = n0 * (1 - s) ** A["alpha_n"]
    m_i = 2.5 * U; Ti = T * KEV; vt = np.sqrt(Ti / m_i); rho = m_i * vt / (E * B_ref)
    QGB = n * Ti * vt * (rho / a_phys) ** 2                              # W/m^2
    Q_gx = gx["Q_i"] * QGB
    x = np.linspace(0, s, 4001); xa = np.linspace(0, 1, 8001)
    f_a = lambda xx: (1 - xx) ** (2 * A["alpha_n"]) * sigma_v(T0 * (1 - xx) ** A["alpha_T"])
    f_b = lambda xx: (1 - xx) ** (2 * A["alpha_n"]) * np.sqrt(T0 * (1 - xx) ** A["alpha_T"])
    Fa = np.trapezoid(f_a(x), x) / np.trapezoid(f_a(xa[:-1]), xa[:-1]); Fb = np.trapezoid(f_b(x), x) / np.trapezoid(f_b(xa[:-1]), xa[:-1])
    P_in = Fa * P_alpha - Fb * P_br
    S_s = flaeche_wout(w, s) * k ** 2; Q_noetig = P_in * 1e6 / S_s
    erg = {"start": t0, "gx": gx, "gx_datei": gx_datei.relative_to(Path.home()).as_posix(), "annahmen": {"s": s, "n_i = n_e": True, "T_i = T_e": True, "m_i_u": 2.5, "v_t": "sqrt(T/m)", "Q_GB": "n T v_t (rho/a)^2 (GX-Konvention, Paper Mandell 2024, im Code nicht nachgeprueft)",
                                                    "profile": "Stufe 0 (alpha_n, alpha_T)", "noetig": "Alphaleistung minus Bremsstrahlung innerhalb s, durch Flaeche s"},
           "geometrie": {"a_klein_u": a_u, "k": k, "a_m": a_phys, "B_ref_klein_T": Bref_u, "B_achse_wout_T": B_axis_u, "B_ref_phys_T": B_ref, "S_s_m2": S_s, "S_rand_m2": bil["form"]["S_R2"] * R0 ** 2},
           "plasma_bei_s": {"T_keV": T, "n_1e20": n / 1e20, "rho_i_m": rho, "rho_i_durch_a": rho / a_phys},
           "QGB_MW_m2": QGB / 1e6, "Q_GX_ionen_MW_m2": Q_gx / 1e6,
           "bilanz": {"P_alpha_MW": P_alpha, "P_brems_MW": P_br, "n0_1e20": n0 / 1e20, "n_mittel_1e20": n_m / 1e20, "V_m3": V, "R0_m": R0, "T0_keV": T0, "F_alpha_bis_s": Fa, "F_brems_bis_s": Fb, "P_durch_s_MW": P_in, "Q_noetig_MW_m2": Q_noetig / 1e6, "quelle": P1["quellen"]["bilanz"]},
           "verhaeltnis": Q_gx / Q_noetig, "verhaeltnis_bei_50_prozent_ionenanteil": Q_gx / (0.5 * Q_noetig), "H_ISS04": json.loads((P / K.get("groesse", "sim/kette_dgoz/groesse/j15/runden.json")).read_text())["runden"][-1]["stufe0"]["H_ISS04"], "ende": time.strftime("%F %T")}
    (OUT / "auswertung.json").write_text(json.dumps(erg, indent=1))
    from stellarator.k4_bericht import schreibe
    schreibe(OUT, TEST, erg); print(json.dumps({k_: erg[k_] for k_ in ("verhaeltnis", "verhaeltnis_bei_50_prozent_ionenanteil", "Q_GX_ionen_MW_m2")}), flush=True)


if __name__ == "__main__":
    main()
