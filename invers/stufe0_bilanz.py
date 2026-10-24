"""stufe0_bilanz.py — Stufe 0 (invers): Wie gross muss die Anlage fuer P_netz sein? -> R0, B0.

0-D-Leistungsbilanz eines D-T-Stellarator-Kraftwerks (Systemcode im Kleinen). Aus der
Netzleistung folgt die Fusionsleistung; ein Raster ueber (R0, B0, T0) sucht fuer jeden Leiter
(Nb3Sn, HTS) die kleinste Anlage, die alle Grenzen einhaelt:

  Neutronen-Wandlast   P_n / S_plasma           <= wandlast_max   (Blanket-Lebensdauer)
  Plasmadruck          <beta>                   <= beta_max       (Gleichgewicht/Stabilitaet)
  Dichte               n / n_Sudo               <= sudo_max       (Strahlungskollaps)
  Einschluss           tau_E,noetig / tau_ISS04 <= H_max          (Zuendung ohne Fremdheizung)
  Leiterfeld           k_B * B0                 <= B_leiter_max   (Supraleiter)
  Spule-Plasma         d_noetig <= (d/R0)_Stufe2 * R0              (Blanket + Abschirmung)

Die Plasmaform kommt aus Stufe 1 (massstabsfrei: V/R0^3, S/R0^2, iota(2/3)); ohne --form ein
Torus mit Seitenverhaeltnis --aspekt. Physik bewusst einfach: Bosch-Hale-Reaktivitaet,
Parabelprofile, Bremsstrahlung (keine Zyklotronstrahlung), ISS04-Skalierung, Sudo-Grenze.
Ergebnis ist eine Groessenordnung (+-30 %), kein Kraftwerksentwurf.

  .venv-opt/bin/python invers/stufe0_bilanz.py --name qa_nfp2_1GW --form sim/invers/qa_nfp2
      [--P_netz 1000 --spulen sim/invers/qa_nfp2_spulen/spulen.json --fall_vorlage stellarator/faelle/qa_nfp2.json]

Ausgabe sim/invers/<name>/: bilanz.json (Annahmen, Auslegungspunkte je Leiter, Grenzen-Auslastung,
Empfehlung fuer Stufe 2), bilanz_R0_B0.png; mit --fall_vorlage je Leiter eine Falldatei
stellarator/faelle/<name>_<leiter>.json (R0, B0, Wickelpaket aus Stromdichte) fuer Stufe 3.
"""
from __future__ import annotations
import argparse, copy, json
from pathlib import Path
import numpy as np

PROJEKT = Path(__file__).resolve().parents[1]
MU0 = 4e-7 * np.pi
KEV = 1.602176634e-16             # J
E_FUS = 17.59e3 * KEV             # J je D-T-Reaktion
F_ALPHA = 3.52 / 17.59

LEITER = {   # max. Feld am Leiter (mit Reserve), technische Stromdichte im Wickelpaket
    "Nb3Sn": {"B_max_T": 12.0, "j_A_m2": 15e6, "bemerkung": "erprobt (ITER-TF 11,8 T); j niedrig, sonst dominiert das Eigenfeld des Wickelpakets"},
    "HTS":   {"B_max_T": 20.0, "j_A_m2": 40e6, "bemerkung": "REBCO, kompakter, junge Technik"},
}


def sigma_v(T):
    """D-T-Reaktivitaet <sigma v> [m^3/s], Bosch & Hale 1992, T in keV (0,2..100)."""
    T = np.asarray(T, float)
    BG, mrc2 = 34.3827, 1124656.0
    C = (1.17302e-9, 1.51361e-2, 7.51886e-2, 4.60643e-3, 1.35e-2, -1.0675e-4, 1.366e-5)
    th = T / (1 - T * (C[1] + T * (C[3] + T * C[5])) / (1 + T * (C[2] + T * (C[4] + T * C[6]))))
    xi = (BG ** 2 / (4 * th)) ** (1 / 3)
    return 1e-6 * C[0] * th * np.sqrt(xi / (mrc2 * T ** 3)) * np.exp(-3 * xi)


def form_aus_stufe1(ordner: Path) -> dict:
    """Massstabsfreie Formfaktoren aus stufe1.json + wout (Randflaeche numerisch)."""
    from netCDF4 import Dataset
    s1 = json.loads((ordner / "stufe1.json").read_text())["kennzahlen"]
    wout = next(ordner.glob("wout_*.nc"))
    with Dataset(str(wout)) as w:
        rmnc, zmns = w["rmnc"][-1, :], w["zmns"][-1, :]
        xm, xn = w["xm"][:], w["xn"][:]
    th, ph = np.meshgrid(np.linspace(0, 2 * np.pi, 257)[:-1], np.linspace(0, 2 * np.pi, 513)[:-1], indexing="ij")
    arg = xm[:, None, None] * th - xn[:, None, None] * ph
    R = np.einsum("m,mij->ij", rmnc, np.cos(arg)); Z = np.einsum("m,mij->ij", zmns, np.sin(arg))
    X = np.stack([R * np.cos(ph), R * np.sin(ph), Z], -1)
    dth, dph = 2 * np.pi / th.shape[0], 2 * np.pi / th.shape[1]
    Xt = (np.roll(X, -1, 0) - np.roll(X, 1, 0)) / (2 * dth); Xp = (np.roll(X, -1, 1) - np.roll(X, 1, 1)) / (2 * dph)
    S = np.linalg.norm(np.cross(Xt, Xp), axis=-1).sum() * dth * dph
    pr = s1["iota_profil"]
    R0 = s1["R0_m"]
    return {"quelle": str(ordner), "aspekt": s1["aspekt"], "V_R3": s1["volumen_m3"] / R0 ** 3,
            "S_R2": float(S / R0 ** 2), "iota_23": float(np.interp(2 / 3, pr["rho"], pr["iota"]))}


def form_torus(aspekt: float, iota: float) -> dict:
    return {"quelle": "Torus", "aspekt": aspekt, "V_R3": 2 * np.pi ** 2 / aspekt ** 2,
            "S_R2": 4 * np.pi ** 2 / aspekt, "iota_23": iota}


def bilanz(a, form) -> dict:
    """Leistungskette Netz <- Turbine <- Blanket <- Plasma (gezuendet, ohne Fremdheizung)."""
    k_th = (1 - F_ALPHA) * a.M_blanket + F_ALPHA            # P_th / P_fus
    # P_netz = eta*P_th - f_pumpe*P_th - P_eigen
    P_th = (a.P_netz + a.P_eigen) / (a.eta_th - a.f_pumpe)
    P_fus = P_th / k_th
    return {"P_netz_MW": a.P_netz, "P_fus_MW": P_fus, "P_th_MW": P_th, "P_brutto_MW": a.eta_th * P_th,
            "P_eigen_MW": a.P_eigen + a.f_pumpe * P_th, "P_neutronen_MW": (1 - F_ALPHA) * P_fus,
            "P_alpha_MW": F_ALPHA * P_fus, "Q_kraftwerk": a.eta_th * P_th / (a.P_eigen + a.f_pumpe * P_th)}


def raster(a, form, P_fus_MW):
    """(R0, B0, T0)-Raster -> Grenzen-Auslastung (1 = Grenze). Dichte folgt aus P_fus."""
    R0 = np.arange(3.0, 30.01, 0.1)[:, None, None]
    B0 = np.arange(2.0, 12.01, 0.05)[None, :, None]
    T0 = np.arange(6.0, 40.1, 1.0)[None, None, :]
    rho = np.linspace(0, 1, 201)[1:-1]                       # Volumen ~ rho^2 -> dV = 2 rho drho V
    w = 2 * rho * np.gradient(rho)
    pn, pt = (1 - rho ** 2) ** a.alpha_n, (1 - rho ** 2) ** a.alpha_T
    pn_m, pt_m = (w * pn).sum(), (w * pt).sum()               # Volumenmittel der Profilformen
    T_r = T0[..., None] * pt                                   # (.., .., T, rho)
    I_fus = (w * pn ** 2 * sigma_v(T_r)).sum(-1)               # <n^2 sv>/n0^2
    I_br = (w * pn ** 2 * np.sqrt(T_r)).sum(-1)
    I_p = (w * pn * pt).sum() * T0                             # <n T>/n0 [keV]
    V = form["V_R3"] * R0 ** 3; S = form["S_R2"] * R0 ** 2; am = R0 / form["aspekt"]
    nD = a.f_DT / 2                                            # n_D = n_T = f_DT/2 * n_e
    n0 = np.sqrt(P_fus_MW * 1e6 / (nD ** 2 * E_FUS * I_fus * V))  # zentrale Elektronendichte
    n_m = n0 * pn_m
    p_m = (1 + a.f_ion) * n0 * I_p * KEV
    beta = 2 * MU0 * p_m / B0 ** 2
    P_br = 5.35e-37 * a.Z_eff * n0 ** 2 * I_br * V / 1e6      # MW
    P_heiz = F_ALPHA * P_fus_MW                                # gezuendet: nur Alphas
    W = 1.5 * p_m * V / 1e6                                    # MJ
    tau_noetig = W / np.maximum(P_heiz - P_br, 1e-3)
    tau_iss = (0.134 * am ** 2.28 * R0 ** 0.64 * P_heiz ** -0.61 * (n_m / 1e19) ** 0.54
               * B0 ** 0.84 * form["iota_23"] ** 0.41)
    n_sudo = 0.25e20 * np.sqrt(P_heiz * B0 / (am ** 2 * R0))
    ausl = {"wandlast": np.broadcast_to((1 - F_ALPHA) * P_fus_MW / S / a.wandlast_max, n0.shape),
            "beta": beta / a.beta_max, "dichte_sudo": n_m / n_sudo / a.sudo_max,
            "einschluss_H": np.where(P_heiz > P_br, tau_noetig / tau_iss / a.H_max, 9.9),
            "spule_plasma": np.broadcast_to(a.d_noetig / (form["d_sp_R0"] * R0), n0.shape)}
    gr = {"R0": R0[:, 0, 0], "B0": B0[0, :, 0], "T0": T0[0, 0, :]}
    form_voll = (R0.size, B0.size, T0.size)
    werte = {"n_m_1e20": n_m / 1e20, "T0_keV": np.broadcast_to(T0, n0.shape), "beta_proz": 100 * beta,
             "H_ISS04": tau_noetig / tau_iss, "tau_E_s": tau_noetig, "n_durch_n_Sudo": n_m / n_sudo,
             "wandlast_MW_m2": np.broadcast_to((1 - F_ALPHA) * P_fus_MW / S, n0.shape),
             "P_brems_MW": P_br, "W_plasma_MJ": W, "a_m": np.broadcast_to(am, n0.shape),
             "V_m3": np.broadcast_to(V, n0.shape), "S_m2": np.broadcast_to(S, n0.shape)}
    ausl = {k: np.broadcast_to(v, form_voll) for k, v in ausl.items()}
    werte = {k: np.broadcast_to(v, form_voll) for k, v in werte.items()}
    return gr, ausl, werte


def auslegung(a, form, gr, ausl, werte, k_B: dict):
    """Je Leiter: kleinstes R0, dann kleinstes B0, dann T0 mit groesster Reserve."""
    m = np.maximum.reduce([np.asarray(v) for v in ausl.values()])   # schaerfste Grenze
    erg = {}
    for name, L in LEITER.items():
        kb = k_B[name]
        ok = (m <= 1) & (kb * gr["B0"][None, :, None] <= L["B_max_T"])
        if not ok.any():
            erg[name] = {"machbar": False}; continue
        iR = np.argmax(ok.any((1, 2)))
        iB = np.argmax(ok[iR].any(1))
        iT = np.argmin(np.where(ok[iR, iB], m[iR, iB], 9))
        i = (iR, iB, iT)
        R0, B0 = float(gr["R0"][iR]), float(gr["B0"][iB])
        n_sp = form.get("n_spulen", 16)
        I_spule = a.f_I * 2 * np.pi * R0 * B0 / (MU0 * n_sp)          # Ampere: Poloidalstrom je Spule
        A_wp = I_spule / L["j_A_m2"]
        erg[name] = {"machbar": True, "R0_m": R0, "B0_T": B0, "B_leiter_T": kb * B0, "k_B": kb,
                     **{k: float(np.asarray(v)[i]) for k, v in werte.items()},
                     "auslastung": {k: float(np.asarray(v)[i]) for k, v in ausl.items()}
                     | {"leiterfeld": kb * B0 / L["B_max_T"]},
                     "begrenzt_durch": max(ausl, key=lambda k: float(np.asarray(ausl[k])[i])),
                     "I_spule_MA": I_spule / 1e6, "wickelpaket_m": float(np.sqrt(A_wp)),
                     "magnetenergie_GJ": float(B0 ** 2 / (2 * MU0) * form["V_R3"] * R0 ** 3
                                               * (1 + form["d_sp_R0"] * form["aspekt"]) ** 2 / 1e9),
                     "leiter": L}
        # B0 nicht ausgereizt? zusaetzlich: wie weit liesse sich B0 fuer dieses R0 noch anheben
        erg[name]["B0_max_leiter_T"] = L["B_max_T"] / kb
    return erg, m


def bild(pfad, gr, ausl, m, erg, k_B, form, a):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    best = np.min(m, axis=2)                                   # bestes T0 je (R0, B0)
    fig, ax = plt.subplots(figsize=(9, 6), dpi=110)
    ax.contourf(gr["B0"], gr["R0"], best <= 1, levels=[0.5, 1.5], colors=["#c7e9c0"])
    farben = {"wandlast": "#d62728", "beta": "#1f77b4", "dichte_sudo": "#9467bd", "einschluss_H": "#ff7f0e",
              "spule_plasma": "#8c564b"}
    namen = {"wandlast": f"Wandlast {a.wandlast_max} MW/m²", "beta": f"<β> {100 * a.beta_max:.0f} %",
             "dichte_sudo": f"Dichte {a.sudo_max}×Sudo", "einschluss_H": f"Einschluss H_ISS04 {a.H_max}",
             "spule_plasma": f"Spule–Plasma {a.d_noetig} m"}
    for k, v in ausl.items():
        z = v.min(2)
        if z.min() < 1 < z.max():
            ax.contour(gr["B0"], gr["R0"], z, levels=[1], colors=farben[k], linewidths=2)
            ax.plot([], [], color=farben[k], lw=2, label=namen[k])
    for name, L in LEITER.items():
        ax.axvline(L["B_max_T"] / k_B[name], color="k", ls="--", lw=1)
        ax.text(L["B_max_T"] / k_B[name], gr["R0"][-1] * 0.97, f" {name}\n B_Leiter≤{L['B_max_T']:.0f} T", va="top", fontsize=8)
        if erg[name].get("machbar"):
            ax.plot(erg[name]["B0_T"], erg[name]["R0_m"], "o", ms=9, color="k")
            ax.annotate(f"{name}: R0={erg[name]['R0_m']:.1f} m, B0={erg[name]['B0_T']:.1f} T",
                        (erg[name]["B0_T"], erg[name]["R0_m"]), xytext=(8, 8), textcoords="offset points", fontsize=9)
    ax.set(xlabel="Feld auf der Achse B0 [T]", ylabel="großer Radius R0 [m]",
           title=f"{a.P_netz:.0f} MW netto, Form {Path(form['quelle']).name} (A={form['aspekt']:.1f}); grün = machbar")
    ax.legend(loc="center right", fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(pfad); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stufe 0: Leistungsbilanz -> R0, B0")
    ap.add_argument("--name", required=True)
    ap.add_argument("--form", type=Path, help="Ordner von Stufe 1 (stufe1.json + wout)")
    ap.add_argument("--aspekt", type=float, default=6.0, help="nur ohne --form (Torus)")
    ap.add_argument("--spulen", type=Path, help="spulen.json aus Stufe 2 -> (d/R0) und Spulenanzahl")
    ap.add_argument("--fall_vorlage", type=Path, help="Falldatei fuer Stufe 3 -> je Leiter skalierte Kopie")
    ap.add_argument("--P_netz", type=float, default=1000.0, help="MW elektrisch ins Netz")
    ap.add_argument("--eta_th", type=float, default=0.35, help="Wirkungsgrad Waerme->Strom")
    ap.add_argument("--M_blanket", type=float, default=1.15, help="Energievervielfachung im Blanket")
    ap.add_argument("--f_pumpe", type=float, default=0.04, help="Pumpleistung / P_th")
    ap.add_argument("--P_eigen", type=float, default=60.0, help="MW Kryo, Anlage, Tritium, Heizung-Bereitschaft")
    ap.add_argument("--wandlast_max", type=float, default=2.0, help="MW/m² Neutronen (Mittel)")
    ap.add_argument("--beta_max", type=float, default=0.05)
    ap.add_argument("--sudo_max", type=float, default=1.5, help="zulaessiges Vielfaches der Sudo-Grenze")
    ap.add_argument("--H_max", type=float, default=1.3, help="zulaessiger Faktor auf ISS04")
    ap.add_argument("--d_noetig", type=float, default=1.3, help="m Blanket+Abschirmung+Behaelter+halbes Wickelpaket")
    ap.add_argument("--k_B", default="2.0", help="B_max am Leiter / B0, Zahl oder je Leiter 'Nb3Sn=2.65,HTS=2.42' "
                    "(W7-X: 1,8; aus Stufe 3 B_max_oberflaeche_T / B0 nachziehen)")
    ap.add_argument("--f_I", type=float, default=1.0, help="Spulenstrom / Ampere-Abschaetzung (aus Stufe 3, qa_nfp2: 1,09)")
    ap.add_argument("--f_DT", type=float, default=0.85, help="Brennstoff-Ionen je Elektron (Rest: He-Asche, Verunreinigung)")
    ap.add_argument("--f_ion", type=float, default=0.9, help="Ionen je Elektron (Druck)")
    ap.add_argument("--Z_eff", type=float, default=1.5)
    ap.add_argument("--alpha_n", type=float, default=0.5, help="Dichteprofil (1-rho²)^alpha")
    ap.add_argument("--alpha_T", type=float, default=1.0, help="Temperaturprofil (1-rho²)^alpha")
    a = ap.parse_args(argv)

    a.k_B = ({n: float(a.k_B) for n in LEITER} if "=" not in a.k_B
             else {n: float(v) for n, v in (x.split("=") for x in a.k_B.split(","))})
    form = form_aus_stufe1(a.form) if a.form else form_torus(a.aspekt, 0.42)
    form["d_sp_R0"] = 0.3
    if a.spulen:
        sp = json.loads(a.spulen.read_text())
        form["d_sp_R0"] = sp["abstand_sp_min_m"] / sp["R0_m"]; form["n_spulen"] = len(sp["spulen"])
    leistung = bilanz(a, form)
    gr, ausl, werte = raster(a, form, leistung["P_fus_MW"])
    erg, m = auslegung(a, form, gr, ausl, werte, a.k_B)
    # Empfehlung fuer Stufe 2: Spule-Plasma-Abstand massstabsfrei (bei R0 der Stufe-1-Form)
    for e in erg.values():
        if e.get("machbar"):
            e["stufe2_abstand_sp_normiert"] = a.d_noetig / e["R0_m"]
    # Seitenverhaeltnis-Empfindlichkeit (Torus-Skalierung der Formfaktoren: S/R² ~ 1/A, V/R³ ~ 1/A²)
    empf = {}
    for A in (4.0, 5.0, 6.0, 8.0):
        f2 = dict(form, aspekt=A, V_R3=form["V_R3"] * (form["aspekt"] / A) ** 2, S_R2=form["S_R2"] * form["aspekt"] / A)
        g2, au2, we2 = raster(a, f2, leistung["P_fus_MW"])
        e2, _ = auslegung(a, f2, g2, au2, we2, a.k_B)
        empf[f"A={A:g}"] = {k: ({"R0_m": v["R0_m"], "B0_T": v["B0_T"], "begrenzt_durch": v["begrenzt_durch"]}
                               if v.get("machbar") else "nicht machbar") for k, v in e2.items()}
    ordner = PROJEKT / "sim" / "invers" / a.name; ordner.mkdir(parents=True, exist_ok=True)
    out = {"name": a.name, "annahmen": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()},
           "form": form, "leistung": leistung, "auslegung": erg, "seitenverhaeltnis_empfindlichkeit": empf,
           "hinweis": "0-D-Abschaetzung (+-30 %). k_B und d/R0 nach Stufe 2/3 nachziehen und neu rechnen."}
    (ordner / "bilanz.json").write_text(json.dumps(out, indent=2, default=float))
    bild(ordner / "bilanz_R0_B0.png", gr, ausl, m, erg, a.k_B, form, a)
    if a.fall_vorlage:
        vor = json.loads(a.fall_vorlage.read_text())
        for name, e in erg.items():
            if not e.get("machbar"):
                continue
            f = copy.deepcopy(vor); c = f["spulen"]
            f["name"] = f"{a.name}_{name}"
            f["beschreibung"] = (f"{vor['name']} ausgelegt auf {a.P_netz:.0f} MW netto mit {name}: "
                                 f"R0 {e['R0_m']:.1f} m, B0 {e['B0_T']:.2f} T (Stufe 0)")
            c["R0_m"] = round(e["R0_m"], 2); c["B0_achse_T"] = round(e["B0_T"], 3)
            c["wickel_breite_m"] = c["wickel_hoehe_m"] = round(e["wickelpaket_m"], 3)
            (PROJEKT / "stellarator" / "faelle" / f"{f['name']}.json").write_text(json.dumps(f, indent=2, ensure_ascii=False))
    kurz = {k: ({x: round(v[x], 3) for x in ("R0_m", "B0_T", "a_m", "n_m_1e20", "T0_keV", "beta_proz", "H_ISS04",
                                            "wandlast_MW_m2", "I_spule_MA", "wickelpaket_m")} | {"begrenzt": v["begrenzt_durch"]}
                if v.get("machbar") else "nicht machbar") for k, v in erg.items()}
    print("FERTIG", ordner, json.dumps({"P_fus_MW": round(leistung["P_fus_MW"]), **kurz}, ensure_ascii=False))
    print("Seitenverhaeltnis:", json.dumps(empf, ensure_ascii=False))


if __name__ == "__main__":
    main()
