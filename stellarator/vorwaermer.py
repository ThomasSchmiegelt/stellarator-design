"""Divertor-Vorwaermer: welche Bauart holt aus 305 MW Divertorwaerme den meisten Netto-Strom?

Kraftwerksseite: Divertorwasser (EU-DEMO-Targets 130 -> 136 C, 5 MPa) waermt Kondensat vor und spart
Anzapfdampf. Die Mehrleistung ist die Arbeit, die der eingesparte Dampf bis zum Kondensator noch leistet:
    dW = m_k cp dT * (h_A - h_aus) / (h_A - h'_A),   Anzapfdruck p_A = p_s(T + ttd)
Tauscherseite: Gegenstrom, UA = Q / LMTD. Fuer jede Bauart werden hydraulische Durchmesser beider Seiten,
Geschwindigkeit und Annaeherung (136 C - Kondensat aus) abgetastet. Netto = Mehrleistung - Pumpleistung
beider Seiten. Ergebnis: beste Netto-Leistung ueber dem Bauvolumen (Pareto-Front), je Bauart ein Band.

Korrelationen (Belege in docs/recherche/vorwaermer/gyroid_kennzahlen.md):
  Diamond   Renon & Jeanningros 2024: Nu = 0,2644 Re^0,69 Pr^1/3, f_Fanning = 1,850 Re^-0,17
  Gyroid    gleiche Nu, f * 1,145 (12,3-16,7 % hoeher); Band: Li 2020 und Li 2022 (Al-Safadi 2026, Tab. 9)
  abgestuft Gyroid mit j/f^1/3 + 28 % (Oh et al. 2025), hier als Nu * 1,28 bei gleichem f
  Platte    Notbehelf: wie gleichmaessiger Gyroid, Band bis 10 % besser (Oh et al.: Gyroid "slightly lower")
  Rohr      Gnielinski/Petukhov auf beiden Seiten (Mantelseite = Rohrseite: schwaechste Annahme)

Aufruf: .venv/bin/python -m stellarator.vorwaermer [--p_kond 0.0247] [--m_kond 1820]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from CoolProp.CoolProp import PropsSI

AUS = Path(__file__).resolve().parent.parent / "docs" / "bilder"
DATEN = Path(__file__).resolve().parent / "daten"

Q = 305e6                      # Divertorwaerme [W] (Projektbericht, f_div = 0,5)
T_H_EIN, T_H_AUS, P_H = 136.0, 130.0, 5e6       # EU-DEMO-Targets (You et al. 2022)
P_K = 2e6                      # Kondensatdruck in der ND-Vorwaermung [Pa]  ANNAHME
TTD = 3.0                      # Graedigkeit der ND-Vorwaermer [K]           ANNAHME
ETA_HD, ETA_ND = 0.85, 0.88    # isentrope Turbinenwirkungsgrade            ANNAHME
P_FD = 78e5                    # Frischdampf gesaettigt (EPR)
P_ZUE, T_ZUE = 11e5, 270.0     # Wasserabscheider/Zwischenueberhitzer        ANNAHME
ETA_P = 0.80                   # Pumpenwirkungsgrad                         ANNAHME
T_WAND, K_WAND = 0.5e-3, 16.0  # Wand 0,5 mm (gedruckt, Oh et al.), Edelstahl ANNAHME (Festigkeit offen)


# ---------------------------------------------------------------- Kraftwerksseite
def expansion(p_kond):
    """h(p) entlang der Expansionslinie: HD 78 bar -> 11 bar, ZUE auf 270 C, ND -> Kondensator."""
    h0 = PropsSI("H", "P", P_FD, "Q", 1, "Water"); s0 = PropsSI("S", "P", P_FD, "Q", 1, "Water")
    hz = PropsSI("H", "P", P_ZUE, "T", T_ZUE + 273.15, "Water"); sz = PropsSI("S", "P", P_ZUE, "T", T_ZUE + 273.15, "Water")

    def h(p):
        return hz - ETA_ND * (hz - PropsSI("H", "P", p, "S", sz, "Water"))
    return h, h(p_kond)


def mehrleistung_kurve(p_kond, m_k):
    """Kumulierte Mehrleistung W(T) [W] fuer Vorwaermung von T_kond bis T (Tabelle)."""
    h, h_aus = expansion(p_kond)
    T0 = PropsSI("T", "P", p_kond, "Q", 0, "Water") - 273.15
    T = np.linspace(T0, 140.0, 300)
    dw = []
    for t in T:
        pa = PropsSI("P", "T", t + TTD + 273.15, "Q", 0, "Water")
        ha, hf = h(pa), PropsSI("H", "P", pa, "Q", 0, "Water")
        cp = PropsSI("C", "P", P_K, "T", t + 273.15, "Water")
        dw.append(m_k * cp * (ha - h_aus) / (ha - hf))
    W = np.concatenate([[0], np.cumsum(0.5 * (np.array(dw[1:]) + dw[:-1]) * np.diff(T))])
    return T, W, T0


# ---------------------------------------------------------------- Korrelationen
def renon(re, pr):
    return 0.2644 * re ** 0.69 * pr ** (1 / 3), 1.850 * re ** -0.17


def li2020(re, pr):
    return 0.18 * re ** 0.717 * pr ** 0.33, 0.22 * re ** -0.048


def li2022(re, pr):
    return 0.02 * re ** 1.02 * pr ** 0.33, 4.106 * re ** -0.203


def gnielinski(re, pr):
    fd = (0.790 * np.log(re) - 1.64) ** -2
    return (fd / 8) * (re - 1000) * pr / (1 + 12.7 * np.sqrt(fd / 8) * (pr ** (2 / 3) - 1)), fd / 4


def skaliert(basis, k_nu=1.0, k_f=1.0):
    return lambda re, pr: (basis(re, pr)[0] * k_nu, basis(re, pr)[1] * k_f)


GY = 1.145
BAUARTEN = {   # Name: (Re-Bereich, d_h-Bereich [m], {Variante: Korrelation}), erste Variante = Mittelwert
    "Rohrbündel": ((4e3, 1e6), (10e-3, 25e-3), {"Gnielinski": gnielinski}),
    "Platte (Notbehelf)": ((3e3, 1.85e4), (3e-3, 10e-3), {"wie Gyroid": skaliert(renon, 1, GY), "+10 %": skaliert(renon, 1.10, GY)}),
    "Gyroid gleichmäßig": ((3e3, 1.85e4), (2e-3, 15e-3), {"Renon": skaliert(renon, 1, GY), "Li 2020": li2020, "Li 2022": li2022}),
    "Gyroid abgestuft": ((3e3, 1.85e4), (2e-3, 15e-3), {"Renon": skaliert(renon, 1.28, GY), "Li 2020": skaliert(li2020, 1.28),
                                       "Li 2022": skaliert(li2022, 1.28)}),
    "Diamond": ((3e3, 1.85e4), (2e-3, 15e-3), {"Renon": renon, "Li 2020": skaliert(li2020, 1, 1 / GY),
                             "Li 2022": skaliert(li2022, 1, 1 / GY)}),
}


# ---------------------------------------------------------------- Tauscher
def stoff(T, p):
    r = PropsSI("D", "P", p, "T", T + 273.15, "Water"); cp = PropsSI("C", "P", p, "T", T + 273.15, "Water")
    mu = PropsSI("V", "P", p, "T", T + 273.15, "Water"); k = PropsSI("L", "P", p, "T", T + 273.15, "Water")
    return r, cp, mu, k, cp * mu / k


def abtasten(korr, re_ber, d_ber, Tk, Wk, m_k):
    rh, cph, muh, kh, prh = stoff(0.5 * (T_H_EIN + T_H_AUS), P_H)
    m_h = Q / (cph * (T_H_EIN - T_H_AUS))
    cpk = PropsSI("C", "P", P_K, "T", 100 + 273.15, "Water")
    dTk = Q / (m_k * cpk)
    app = np.geomspace(0.3, 25, 40)[:, None, None, None, None]     # Annaeherung warmes Ende [K]
    d_k = np.geomspace(*d_ber, 12)[None, :, None, None, None]      # hydr. Durchmesser Kondensatseite
    r = np.geomspace(0.25, 4, 13)[None, None, :, None, None]       # d_h warm / d_h kalt (warm im d_h-Bereich)
    v_k = np.geomspace(0.1, 4, 24)[None, None, None, :, None]      # Geschwindigkeit Kondensat [m/s]
    n = np.array([1, 2, 3, 4, 6, 8])[None, None, None, None, :]    # Durchgaenge Kondensatseite (Gegenstrom angenaehert)
    T_aus = T_H_EIN - app; T_ein = T_aus - dTk
    rk, _, muk, kk, prk = stoff(float(T_aus.mean() - dTk / 2), P_K)
    dT1, dT2 = app, T_H_AUS - T_ein
    lmtd = (dT2 - dT1) / np.log(dT2 / dT1)
    d_h = r * d_k
    Af_k = m_k / (rk * v_k)
    Af_h = n * Af_k * d_h / d_k        # gemeinsame Wand: V_f = A d_h/4 je Seite; Kondensatweg n-mal so lang
    # ohne Durchgaenge gilt Re_warm/Re_kalt = (m_warm mu_kalt)/(m_kalt mu_warm), unabhaengig von der Geometrie
    v_h = m_h / (rh * Af_h)
    re_k = rk * v_k * d_k / muk; re_h = rh * v_h * d_h / muh
    nu_k, f_k = korr(re_k, prk); nu_h, f_h = korr(re_h, prh)
    U = 1 / (d_k / (nu_k * kk) + T_WAND / K_WAND + d_h / (nu_h * kh))
    A = Q / (U * lmtd)
    L = A * d_k / (4 * Af_k)           # Weglaenge Kondensat; warme Seite L/n
    V = A * (d_k + d_h) / 4 + A * T_WAND
    dp_k = 4 * f_k * L / d_k * rk * v_k ** 2 / 2; dp_h = 4 * f_h * (L / n) / d_h * rh * v_h ** 2 / 2
    P_pump = (dp_k * m_k / rk + dp_h * m_h / rh) / ETA_P
    W = np.interp(T_aus, Tk, Wk) - np.interp(T_ein, Tk, Wk)
    netto = W - P_pump
    netto, W, P_pump, V, dp_k, dp_h, L, app, re_k, re_h, T_ein, d_h, n = np.broadcast_arrays(
        netto, W, P_pump, V, dp_k, dp_h, L, app, re_k, re_h, T_ein, d_h, n)
    ok = ((re_k >= re_ber[0]) & (re_k <= re_ber[1]) & (re_h >= re_ber[0]) & (re_h <= re_ber[1]) & (T_ein > Tk[0])
          & (d_h >= d_ber[0] * 0.999) & (d_h <= d_ber[1] * 1.001))
    return dict(V=V[ok], netto=netto[ok], W=W[ok], P=P_pump[ok], app=app[ok], dpk=dp_k[ok], dph=dp_h[ok], L=L[ok], n=n[ok], rek=re_k[ok], reh=re_h[ok])


def front(res, Vb):
    """Beste Netto-Leistung bis zum Volumen V (monoton steigende Front)."""
    o = np.argsort(res["V"]); best = np.maximum.accumulate(res["netto"][o])
    return np.interp(Vb, res["V"][o], best, left=np.nan), o, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p_kond", type=float, default=0.0247, help="Kondensatordruck [bar]")
    ap.add_argument("--m_kond", type=float, default=1820.0, help="Kondensatstrom [kg/s]")
    ap.add_argument("--bild", default="vorwaermer_netto.png")
    a = ap.parse_args()
    Tk, Wk, T0 = mehrleistung_kurve(a.p_kond * 1e5, a.m_kond)
    cpk = PropsSI("C", "P", P_K, "T", 373.15, "Water")
    dTk = Q / (a.m_kond * cpk)
    W_max = np.interp(T_H_EIN, Tk, Wk) - np.interp(T_H_EIN - dTk, Tk, Wk)
    print(f"Kondensator {a.p_kond*1e3:.1f} mbar ({T0:.1f} C), Kondensat {a.m_kond:.0f} kg/s, Erwaermung {dTk:.1f} K")
    print(f"Obergrenze (Annaeherung 0 K, ohne Pumpen): {W_max/1e6:.1f} MW = {W_max/Q*100:.1f} % von 305 MW")
    Vb = np.geomspace(0.3, 1000, 240)
    erg = {}
    for name, (re_ber, d_ber, var) in BAUARTEN.items():
        erg[name] = {}
        for vn, korr in var.items():
            res = abtasten(korr, re_ber, d_ber, Tk, Wk, a.m_kond)
            f, o, best = front(res, Vb)
            i = np.argmax(res["netto"])
            # Punkt bei 50 m3: bester zulaessiger Entwurf bis 50 m3
            j = np.where(res["V"] <= 50)[0]; j = j[np.argmax(res["netto"][j])] if len(j) else i
            erg[name][vn] = dict(front=f.tolist(), max=float(res["netto"][i] / 1e6), V_max=float(res["V"][i]),
                                 bei50=float(res["netto"][j] / 1e6), app50=float(res["app"][j]),
                                 P50=float(res["P"][j] / 1e6), dpk50=float(res["dpk"][j] / 1e6),
                                 dph50=float(res["dph"][j] / 1e6), L50=float(res["L"][j]), n50=int(res["n"][j]), rek50=float(res["rek"][j]), reh50=float(res["reh"][j]),
                                 **{f"V{q}": float(res["V"][o][np.argmax(best >= q / 100 * W_max)])
                                    if best[-1] >= q / 100 * W_max else None for q in (90, 95, 99)})
            e = erg[name][vn]
            print(f"{name:20s} {vn:11s} max {e['max']:5.1f} MW bei {e['V_max']:6.0f} m3 | bis 50 m3: {e['bei50']:5.1f} MW "
                  f"(Annaeh. {e['app50']:4.1f} K, Pumpen {e['P50']:.2f} MW, dp {e['dpk50']:.2f}/{e['dph50']:.2f} MPa, L {e['L50']:.1f} m, n {e['n50']}, Re {e['rek50']:.0f}/{e['reh50']:.0f})"
                  f" | V fuer 90/95/99 %: " + "/".join(f"{e[k]:.1f}" if e[k] else "-" for k in ("V90", "V95", "V99")))
    DATEN.mkdir(exist_ok=True)
    (DATEN / "vorwaermer.json").write_text(json.dumps(dict(p_kond=a.p_kond, m_kond=a.m_kond, W_max=W_max / 1e6,
                                                           V=Vb.tolist(), erg=erg), indent=1))
    bild(Vb, erg, W_max, a)


def bild(Vb, erg, W_max, a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    farben = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"]
    fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
    ax.axhline(W_max / 1e6, color="#52514e", lw=1, ls="--")
    ax.text(1.1, W_max / 1e6 + 0.3, f"Obergrenze ohne Pumpen, Annäherung 0 K: {W_max/1e6:.1f} MW", color="#52514e", fontsize=9)
    for (name, var), c in zip(erg.items(), farben):
        F = np.array([v["front"] for v in var.values()]) / 1e6
        mitte = F[0]
        ax.plot(Vb, mitte, color=c, lw=2, label=name, ls="--" if "Platte" in name else "-")
        if len(F) > 1:
            ax.fill_between(Vb, np.nanmin(F, 0), np.nanmax(F, 0), color=c, alpha=0.15, lw=0)
    ax.set_xscale("log"); ax.set_xlabel("Bauvolumen des Tauschers [m³]")
    ax.set_ylabel("Netto-Mehrleistung [MW elektrisch]")
    ax.set_title(f"Divertor-Vorwärmer, 305 MW bei 130–136 °C, Kondensator {a.p_kond*1e3:.1f} mbar\n"
                 "Linie: Mittelwert-Korrelation, Band: Streuung der Literatur", fontsize=11)
    lo = min(np.nanmin(np.array(v["front"])) for var in erg.values() for v in var.values()) / 1e6
    ax.set_ylim(max(lo, 0) - 1, W_max / 1e6 + 2)
    ax.grid(True, which="both", color="#e5e4e0", lw=0.6); ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    fig.text(0.01, 0.005, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e")
    fig.tight_layout()
    AUS.mkdir(exist_ok=True); fig.savefig(AUS / a.bild)
    print("Bild:", AUS / a.bild)


if __name__ == "__main__":
    main()
