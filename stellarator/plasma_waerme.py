"""plasma_waerme.py — Woher kommt die Wärme? Fusion im Plasma der 1-GW-Auslegung (HTS, Stufe 0) nachgerechnet.

  .venv/bin/python -m stellarator.plasma_waerme

Schritte (alle Zahlen werden hier gerechnet, Ausgabe stellarator/daten/plasma_waerme.json, Bild docs/bilder/plasma_waerme*.png):
 1. Massendefekt D + T -> He-4 + n  (Atommassen AME2020), Aufteilung der Energie nach Impulserhaltung.
 2. Coulombwall und Tunneleffekt: Gamow-Fenster bei T0 = 14 keV.
 3. Reaktivität <sigma v> (Bosch & Hale 1992, wie Stufe 0) und Zündbedingung (Lawson, n T tau_E).
 4. Leistungsdichte über dem Radius mit den Profilen der Stufe 0 (n ~ (1-rho²)^0,5, T ~ 1-rho²), Summe = P_fus.
 5. Wege der Energie: Neutron (ungeladen, verlässt das Plasma), Alpha (geladen, Larmorradius, Abbremsung an
    Elektronen und Ionen), Plasmabilanz P_alpha = W/tau_E + P_brems.
"""
import json
import shutil
from pathlib import Path

import numpy as np
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parents[1]
STUFE0 = ROOT / "sim" / "invers" / "qa_nfp2_A45_1GW" / "bilanz.json"
U_MEV = 931.49410242               # MeV je u
M = dict(n=1.00866491595, D=2.01410177812, T=3.01604928132, He4=4.00260325413)   # Atommassen [u], AME2020
E_CH, EPS0, ME, MP = 1.602176634e-19, 8.8541878128e-12, 9.1093837015e-31, 1.67262192369e-27
KEV = 1e3 * E_CH
BG = 34.3827                        # Gamow-Konstante D-T [sqrt(keV)], Bosch & Hale
M_ALPHA = 6.644657e-27; M_N = 1.674927e-27


def sigma_v(T):
    from invers.stufe0_bilanz import sigma_v as sv
    return sv(T)


def rechnen():
    s0 = json.loads(STUFE0.read_text())
    A, H = s0["annahmen"], s0["auslegung"]["HTS"]
    erg = {}
    # 1. Massendefekt
    dm = M["D"] + M["T"] - M["He4"] - M["n"]
    Q = dm * U_MEV
    E_a = Q * M["n"] / (M["n"] + M["He4"]); E_n = Q - E_a
    erg["kern"] = dict(dm_u=dm, Q_MeV=Q, E_alpha_MeV=E_a, E_n_MeV=E_n, anteil_masse=dm / (M["D"] + M["T"]))
    # 2. Coulombwall (Kernradius 1,2 fm A^1/3) und Gamow-Fenster
    r = 1.2e-15 * (2 ** (1 / 3) + 3 ** (1 / 3))
    E_C = E_CH ** 2 / (4 * np.pi * EPS0 * r) / KEV            # keV
    T0 = H["T0_keV"]
    E0 = (BG * T0 / 2) ** (2 / 3)                               # Gamow-Peak [keV]
    dE = 4 / np.sqrt(3) * np.sqrt(E0 * T0)                      # 1/e-Breite
    erg["coulomb"] = dict(r_fm=r * 1e15, E_C_keV=E_C, T0_keV=T0, T0_MK=T0 * KEV / 1.380649e-23 / 1e6,
                          E_gamow_keV=E0, breite_keV=dE, faktor_wall_zu_T=E_C / T0)
    # 3. Reaktivität und Zündung: n T tau_E >= 12 T^2 / (E_alpha <sv>)   (nur Alphaheizung, ohne Strahlung)
    Tg = np.geomspace(2, 200, 400); sv = sigma_v(Tg)
    lawson = 12 * Tg ** 2 / (E_a * 1e3 * sv)                    # keV s m^-3
    i = np.argmin(lawson)
    erg["reaktivitaet"] = dict(sv_T0=float(sigma_v(T0)), T_sv_max=float(Tg[np.argmax(sv)]), sv_max=float(sv.max()),
                               lawson_min=float(lawson[i]), T_lawson_min=float(Tg[i]))
    # 4. Profile (wie Stufe 0)
    rho = np.linspace(0, 1, 2001)[1:-1]; w = 2 * rho * np.gradient(rho)
    pn, pt = (1 - rho ** 2) ** A["alpha_n"], (1 - rho ** 2) ** A["alpha_T"]
    n_m = H["n_m_1e20"] * 1e20; n0 = n_m / (w * pn).sum(); V = H["V_m3"]
    ne = n0 * pn; T = T0 * pt; nD = nT = A["f_DT"] / 2 * ne
    E_fus = Q * 1e3 * KEV
    p = nD * nT * sigma_v(T) * E_fus                             # W/m3
    P = (w * p).sum() * V
    kum = np.cumsum(w * p) * V / P
    erg["profil"] = dict(n0=n0, n_m=n_m, V_m3=V, P_fus_MW=P / 1e6, P_fus_stufe0_MW=s0["leistung"]["P_fus_MW"],
                         p_max_MW_m3=p.max() / 1e6, p_mittel_MW_m3=P / V / 1e6, rho_halb=float(rho[np.searchsorted(kum, 0.5)]),
                         V_anteil_halb=float(rho[np.searchsorted(kum, 0.5)] ** 2), reaktionen_s=P / E_fus,
                         nTtau=float(n0 * T0 * H["tau_E_s"]),
                         T_kg_tag=P / E_fus * M["T"] * 1.66053906660e-27 * 86400,
                         D_kg_tag=P / E_fus * M["D"] * 1.66053906660e-27 * 86400,
                         masse_g_tag=P / 2.99792458e8 ** 2 * 86400 * 1e3)
    # 5. Wege
    v_n = np.sqrt(2 * E_n * 1e3 * KEV / M_N); v_a = np.sqrt(2 * E_a * 1e3 * KEV / M_ALPHA)
    B0 = H["B0_T"]; a = H["a_m"]
    rl = M_ALPHA * v_a / (2 * E_CH * B0)
    lnL = 17.0
    Te = T0 * KEV                                                # zentral
    tau_s = 3 * (2 * np.pi) ** 1.5 * EPS0 ** 2 * M_ALPHA * Te ** 1.5 / (4 * E_CH ** 4 * np.sqrt(ME) * n0 * lnL)
    # kritische Energie: Abbremsung an Elektronen = an Ionen (D, T mit f_DT; Rest vernachlässigt)
    zA = A["f_DT"] * 0.5 * (1 / 2 + 1 / 3)                       # sum n_i Z_i^2 / (n_e A_i)
    E_c = 14.8 * 4 * T0 * zA ** (2 / 3)                          # keV
    x0 = E_a * 1e3 / E_c
    f_ion = quad(lambda x: 1 / (1 + x ** 1.5), 0, x0)[0] / x0
    t_ab = tau_s / 3 * np.log(1 + x0 ** 1.5)                     # Zeit bis zur Thermalisierung
    P_a = s0["leistung"]["P_alpha_MW"]; P_br = H["P_brems_MW"]; W = H["W_plasma_MJ"]; tau = H["tau_E_s"]
    erg["wege"] = dict(v_n_c=v_n / 2.998e8, t_n_ns=a / v_n * 1e9, v_a_c=v_a / 2.998e8, larmor_alpha_cm=rl * 100, a_m=a,
                       tau_s_s=tau_s, E_krit_keV=E_c, anteil_ionen=f_ion, t_abbrems_s=t_ab, P_alpha_MW=P_a,
                       P_transport_MW=W / tau, P_brems_MW=P_br, W_MJ=W, tau_E_s=tau, B0_T=B0,
                       P_n_MW=s0["leistung"]["P_neutronen_MW"], M_blanket=A["M_blanket"],
                       P_blanket_MW=s0["leistung"]["P_neutronen_MW"] * A["M_blanket"])
    return erg, dict(rho=rho, ne=ne, T=T, p=p, kum=kum, Tg=Tg, sv=sv, lawson=lawson)


TXT = dict(
    de=dict(t1="Reaktivität und Zündbedingung", x1="Ionentemperatur T [keV]", y1="⟨σv⟩ [10⁻²² m³/s]",
            y1b="nötiges n·T·τ_E [10²¹ keV s/m³]", t2="Wer fusioniert? Gamow-Fenster bei 14 keV",
            x2="Stoßenergie E [keV]", y2="relativ", maxw="Maxwell-Verteilung e^(−E/kT)", tun="Tunnelwahrscheinlichkeit",
            gam="Produkt: Gamow-Fenster", t3="Wo entsteht die Wärme? Profile über dem kleinen Radius",
            x3="normierter Radius ρ = r/a", p="Leistungsdichte [MW/m³]", kum="Anteil der Fusionsleistung innerhalb ρ",
            t4="Wohin geht die Energie? (MW)", ausl="Auslegung", hier="hier",
            titel="Woher kommt die Wärme? D-T-Fusion im Plasma der 1-GW-Auslegung (HTS, R₀ 10,4 m, B₀ 6,5 T)"),
    en=dict(t1="Reactivity and ignition condition", x1="Ion temperature T [keV]", y1="⟨σv⟩ [10⁻²² m³/s]",
            y1b="required n·T·τ_E [10²¹ keV s/m³]", t2="Who fuses? Gamow window at 14 keV",
            x2="Collision energy E [keV]", y2="relative", maxw="Maxwell distribution e^(−E/kT)", tun="Tunnelling probability",
            gam="Product: Gamow window", t3="Where is the heat produced? Profiles over minor radius",
            x3="normalised radius ρ = r/a", p="Power density [MW/m³]", kum="Share of fusion power inside ρ",
            t4="Where does the energy go? (MW)", ausl="design", hier="here",
            titel="Where does the heat come from? D-T fusion in the plasma of the 1 GW design (HTS, R₀ 10.4 m, B₀ 6.5 T)"))


def bild(erg, d, sprache):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    T_ = TXT[sprache]; de = sprache == "de"
    fz = lambda v, n=0: (f"{v:,.{n}f}".replace(",", " ").replace(".", ",") if de else f"{v:,.{n}f}")
    c1, c2, c3, c4, gr = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#52514e"
    fig, ax = plt.subplots(2, 2, figsize=(14, 9.5), dpi=130)
    T0 = erg["coulomb"]["T0_keV"]
    # (a)
    a = ax[0, 0]
    a.plot(d["Tg"], d["sv"] / 1e-22, color=c1, lw=2); a.set_xscale("log")
    a.set_xlabel(T_["x1"]); a.set_ylabel(T_["y1"], color=c1); a.set_title(T_["t1"], fontsize=11)
    b = a.twinx(); b.plot(d["Tg"], d["lawson"] / 1e21, color=c2, lw=2); b.set_yscale("log"); b.set_ylim(1, 100)
    b.set_ylabel(T_["y1b"], color=c2)
    a.axvline(T0, color=gr, ls="--", lw=1)
    a.text(T0 * 1.06, 0.3, f"T₀ = {fz(T0)} keV ({T_['ausl']})", color=gr, fontsize=8.5)
    r = erg["reaktivitaet"]
    b.annotate(f"Min. {fz(r['lawson_min']/1e21,1)}·10²¹\nbei {fz(r['T_lawson_min'])} keV" if de else
               f"min. {r['lawson_min']/1e21:.1f}·10²¹\nat {r['T_lawson_min']:.0f} keV",
               (r["T_lawson_min"], r["lawson_min"] / 1e21), (35, 30), fontsize=8.5, color=c2,
               arrowprops=dict(arrowstyle="->", color=c2, lw=0.8))
    nt = erg["profil"]["nTtau"]
    b.scatter([T0], [nt / 1e21], color=c2, edgecolor="k", zorder=5, s=40)
    b.annotate((f"Auslegung n₀T₀τ_E = {fz(nt/1e21,1)}·10²¹" if de else f"design n₀T₀τ_E = {nt/1e21:.1f}·10²¹"),
               (T0, nt / 1e21), (3, 40), fontsize=8.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    # (b)
    a = ax[0, 1]; E = np.linspace(0.5, 150, 600)
    mw = np.exp(-E / T0); tu = np.exp(-BG / np.sqrt(E)); g = mw * tu
    a.plot(E, mw, color=c1, lw=1.6, label=T_["maxw"]); a.plot(E, tu / tu.max(), color=c2, lw=1.6, label=T_["tun"])
    a.fill_between(E, g / g.max(), color=c3, alpha=0.35, label=T_["gam"])
    E0 = erg["coulomb"]["E_gamow_keV"]
    a.axvline(E0, color=c3, ls="--", lw=1)
    a.text(E0 + 2, 0.9, f"E₀ ≈ {fz(E0)} keV", color=c3, fontsize=9)
    a.text(68, 0.70, (f"Coulombwall ≈ {fz(erg['coulomb']['E_C_keV'])} keV\n= {fz(erg['coulomb']['faktor_wall_zu_T'])} × kT₀"
                      if de else f"Coulomb barrier ≈ {erg['coulomb']['E_C_keV']:.0f} keV\n= {erg['coulomb']['faktor_wall_zu_T']:.0f} × kT₀"),
           fontsize=9, color=gr)
    a.set_xlabel(T_["x2"]); a.set_ylabel(T_["y2"]); a.set_title(T_["t2"], fontsize=11); a.set_ylim(0, 1.05)
    a.legend(frameon=False, fontsize=8.5, loc="center right", bbox_to_anchor=(1.0, 0.42))
    # (c)
    a = ax[1, 0]
    a.plot(d["rho"], d["p"] / 1e6, color=c2, lw=2, label=T_["p"])
    a.set_xlabel(T_["x3"]); a.set_ylabel(T_["p"], color=c2); a.set_title(T_["t3"], fontsize=11)
    b = a.twinx()
    b.plot(d["rho"], d["T"], color=c1, lw=1.4, ls="--", label="T [keV]")
    b.plot(d["rho"], d["ne"] / 1e19, color=c4, lw=1.4, ls=":", label="n_e [10¹⁹ m⁻³]")
    b.set_ylim(0, 33); a.set_ylim(0, 13); b.set_ylabel("T [keV], n_e [10¹⁹ m⁻³]")
    b.legend(frameon=False, fontsize=8, loc="lower left")
    rh = erg["profil"]["rho_halb"]
    a.axvline(rh, color=c3, ls="--", lw=0.8)
    a.text(rh + 0.02, erg["profil"]["p_max_MW_m3"] * 0.92,
           (f"Hälfte der Leistung innerhalb ρ = {fz(rh,2)}\n(nur {fz(100*rh**2)} % des Volumens)" if de else
            f"half the power inside ρ = {rh:.2f}\n(only {100*rh**2:.0f} % of the volume)"), fontsize=8.5, color=c3)
    r90 = float(d["rho"][np.searchsorted(d["kum"], 0.9)])
    a.axvline(r90, color=c3, ls=":", lw=0.8)
    a.text(r90 + 0.02, erg["profil"]["p_max_MW_m3"] * 0.72, (f"90 % innerhalb ρ = {fz(r90,2)}" if de else f"90 % inside ρ = {r90:.2f}"),
           fontsize=8.5, color=c3)
    # (d) Energieflüsse als Balken
    a = ax[1, 1]; wg = erg["wege"]
    zeilen = [((("Fusion D-T" if de else "Fusion D-T"), erg["profil"]["P_fus_stufe0_MW"], gr, 0)),
              (("Neutronen 14,1 MeV → Blanket" if de else "Neutrons 14.1 MeV → blanket"), wg["P_n_MW"], c4, 0),
              (("Blanket mit Kernreaktionen (× 1,15)" if de else "Blanket incl. nuclear reactions (× 1.15)"), wg["P_blanket_MW"], c4, 0),
              (("Alphas 3,5 MeV → heizen das Plasma" if de else "Alphas 3.5 MeV → heat the plasma"), wg["P_alpha_MW"], c2, 0),
              (("  davon an Ionen" if de else "  of which to ions"), wg["P_alpha_MW"] * wg["anteil_ionen"], c2, 1),
              (("  davon an Elektronen" if de else "  of which to electrons"), wg["P_alpha_MW"] * (1 - wg["anteil_ionen"]), c2, 1),
              (("Plasma verlässt: Transport (W/τ_E)" if de else "Plasma loses: transport (W/τ_E)"), wg["P_transport_MW"], c1, 0),
              (("Plasma verlässt: Bremsstrahlung" if de else "Plasma loses: bremsstrahlung"), wg["P_brems_MW"], c3, 0)]
    y = np.arange(len(zeilen))[::-1]
    for yy, (lab, v, c, ein) in zip(y, zeilen):
        a.barh(yy, v, color=c, alpha=0.55 if ein else 0.85, height=0.62)
        a.text(v + 40, yy, fz(v), va="center", fontsize=9)
        a.text(-60, yy, lab, va="center", ha="right", fontsize=9)
    a.set_yticks([]); a.set_xlim(0, 3700); a.set_title(T_["t4"], fontsize=11)
    a.spines[["top", "right", "left"]].set_visible(False)
    for q in (ax[0, 0], ax[0, 1], ax[1, 0]):
        q.grid(True, which="both", color="#e5e4e0", lw=0.6); q.spines[["top"]].set_visible(False)
    fig.suptitle(T_["titel"], fontsize=12.5, x=0.01, ha="left")
    fig.text(0.99, 0.005, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color=gr, ha="right")
    fig.tight_layout(rect=(0, 0.01, 1, 0.96))
    fig.subplots_adjust(wspace=0.55)
    name = "plasma_waerme.png" if de else "plasma_waerme_en.png"
    out = ROOT / "docs" / "bilder" / name
    fig.savefig(out); plt.close(fig)
    shutil.copy(out, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return out


def main():
    erg, d = rechnen()
    for k, v in erg.items():
        print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})
    (ROOT / "stellarator" / "daten" / "plasma_waerme.json").write_text(json.dumps(erg, indent=1, default=float))
    for s in ("de", "en"):
        print(bild(erg, d, s))


if __name__ == "__main__":
    main()
