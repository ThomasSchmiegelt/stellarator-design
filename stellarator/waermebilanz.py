"""waermebilanz.py — Waermepfad Plasma -> Erstwand/Blanket/Divertor -> Dampferzeuger -> bestehende DWR-Turbine.

    .venv/bin/python -m stellarator.waermebilanz [--P_netz 1000] [--eta 0.35] [--f_div 0.5] [--div_nutzbar 1]

Entscheidung des Nutzers (2026-10-28): eine bestehende Turbine aus einem Druckwasserreaktor verwenden, den Rest moeglichst
einfach -> alle Kreislaeufe mit Druckwasser wie WWER-1000 (289 -> 319 C, 16 MPa, belegt in docs/recherche/pi/ergebnis.md).
Herleitung (gleiche Kette wie invers/stufe0_bilanz.py, hier aufgeteilt nach Bauteilen):
  (1) P_netz = eta P_th - f_p P_th - P_eigen            ->  P_th = (P_netz + P_eigen) / (eta - f_p)
  (2) P_th   = P_fus ((1 - f_a) M + f_a),  f_a = 3,52/17,59 (Alpha-Anteil der D-T-Fusion), M Vervielfachung im Blanket
  (3) Blanket   P_bl  = (1 - f_a) M P_fus                 (Neutronen, Volumenwaerme)
  (4) Erstwand  P_ew  = (1 - f_div) f_a P_fus,  q_ew = P_ew / S   (Strahlung des Plasmas)
  (5) Divertor  P_div = f_div f_a P_fus,  A_div = P_div / q_div  (Teilchen entlang der Feldlinien)
  (6) Massenstrom m = P / (c_p dT), Volumenstrom V = m / rho
  (7) Turbine  P_brutto = eta P_th;  Vergleich mit Isar 2 (Konvoi) und WWER-1000
Die Divertor-Waerme faellt bei niedriger Temperatur an (Kupferlegierung, W7-X-Bauart); --div_nutzbar 1: voll ueber die
Speisewasser-Vorwaermung genutzt, 0: verloren (dann steigt P_fus). Ausgabe sim/waermebilanz/: bilanz.json, bilanz.png.
"""
import argparse, json
import numpy as np

from .lauf import PROJEKT

WURZEL = PROJEKT / "sim" / "waermebilanz"
F_ALPHA = 3.52 / 17.59
# Druckwasser bei ~304 C / 16 MPa (Mittel 289-319 C): c_p, rho aus stellarator/erstwand_kanal.py (300 C)
CP, RHO = 5380.0, 732.0
# belegte Vergleichsanlagen (docs/recherche/pi/ergebnis.md und Ablage): thermisch, elektrisch brutto/netto [MW]
REFERENZ = {"Isar 2 (Konvoi)": {"P_th": 3950, "P_brutto": 1485, "P_netto": 1410,
                                "quelle": "https://de.wikipedia.org/wiki/Konvoi_(Kernkraftwerk)"},
            "WWER-1000": {"P_th": 3000, "eta_netto": 0.317, "quelle": "https://en.wikipedia.org/wiki/VVER"}}


def bilanz(a):
    k = (1 - F_ALPHA) * a.M + F_ALPHA * (1 - a.f_div * (1 - a.div_nutzbar))   # nutzbare Waerme / P_fus
    P_th = (a.P_netz + a.P_eigen) / (a.eta - a.f_p)
    P_fus = P_th / k
    P_bl, P_ew, P_div = (1 - F_ALPHA) * a.M * P_fus, (1 - a.f_div) * F_ALPHA * P_fus, a.f_div * F_ALPHA * P_fus
    kreis = {}
    for name, P in (("Blanket", P_bl), ("Erstwand", P_ew)):
        m = P * 1e6 / (CP * a.dT)
        kreis[name] = {"P_MW": P, "m_kg_s": m, "V_m3_s": m / RHO}
    erg = {"P_netz_MW": a.P_netz, "P_eigen_MW": a.P_eigen + a.f_p * P_th, "P_th_MW": P_th, "P_fus_MW": P_fus,
           "P_neutronen_MW": (1 - F_ALPHA) * P_fus, "P_alpha_MW": F_ALPHA * P_fus, "P_blanket_MW": P_bl,
           "P_erstwand_MW": P_ew, "P_divertor_MW": P_div, "q_erstwand_MW_m2": P_ew / a.S,
           "q_neutronen_MW_m2": (1 - F_ALPHA) * P_fus / a.S, "A_divertor_min_m2": P_div / a.q_div,
           "P_brutto_MW": a.eta * P_th, "P_abwaerme_MW": (1 - a.eta) * P_th, "kreise": kreis,
           "m_gesamt_kg_s": sum(k_["m_kg_s"] for k_ in kreis.values())}
    r = REFERENZ["Isar 2 (Konvoi)"]
    erg["vergleich"] = {"Isar 2 (Konvoi)": {"eta_brutto": r["P_brutto"] / r["P_th"], "P_th_anteil": P_th / r["P_th"],
                                            "P_brutto_anteil": erg["P_brutto_MW"] / r["P_brutto"]},
                        "WWER-1000": {"P_th_anteil": P_th / REFERENZ["WWER-1000"]["P_th"]}}
    return erg


def bild(a, e, datei):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(13, 6.5)); ax.axis("off")
    # einfache Flusskette als Balken (Breite ~ Leistung)
    stufen = [("Fusion", [("Neutronen", e["P_neutronen_MW"], "#7f8c8d"), ("Alphas", e["P_alpha_MW"], "#e67e22")]),
              ("Wärme", [("Blanket (inkl. Vervielfachung)", e["P_blanket_MW"], "#2980b9"),
                         ("Erstwand (Strahlung)", e["P_erstwand_MW"], "#c0392b"), ("Divertor", e["P_divertor_MW"], "#8e44ad")]),
              ("Turbine", [("Strom brutto", e["P_brutto_MW"], "#27ae60"), ("Abwärme Kondensator", e["P_abwaerme_MW"], "#bdc3c7")]),
              ("Netz", [("netto ins Netz", e["P_netz_MW"], "#1e8449"), ("Eigenbedarf + Pumpen", e["P_eigen_MW"], "#f1c40f")])]
    skala = 0.8 / max(sum(p for _, p, _ in t) for _, t in stufen)
    for i, (titel, teile) in enumerate(stufen):
        y = 0.92
        ax.text(0.04 + i * 0.25, 0.97, titel, fontsize=13, weight="bold")
        for name, P, farbe in teile:
            h = P * skala
            ax.add_patch(plt.Rectangle((0.04 + i * 0.25, y - h), 0.05, h, color=farbe))
            ax.text(0.10 + i * 0.25, y - h / 2, f"{name}\n{P:,.0f} MW".replace(",", "."), va="center", fontsize=9.5)
            y -= h + 0.01
    ax.set_title(f"Wärmebilanz 1 GW netto mit Druckwasser 289→319 °C (DWR-Turbine), η = {a.eta:.2f}, "
                 f"Divertor {'genutzt' if a.div_nutzbar else 'verloren'}", fontsize=12)
    fig.savefig(datei, dpi=120, bbox_inches="tight"); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k, d, h in (("P_netz", 1000.0, "MW ins Netz"), ("P_eigen", 60.0, "MW Kryo, Anlage, Tritium"),
                    ("eta", 0.35, "Wirkungsgrad brutto"), ("f_p", 0.04, "Pumpleistung / P_th"),
                    ("M", 1.15, "Energievervielfachung Blanket"), ("f_div", 0.5, "Anteil der Alpha-Leistung zum Divertor"),
                    ("div_nutzbar", 1.0, "1 = Divertor-Waerme genutzt, 0 = verloren"), ("S", 1230.0, "Erstwandflaeche m2 (HTS)"),
                    ("q_div", 10.0, "MW/m2 Divertor (W7-X-Bauart)"), ("dT", 30.0, "K Erwaermung Druckwasser")):
        ap.add_argument(f"--{k}", type=float, default=d, help=h)
    a = ap.parse_args(argv)
    e = bilanz(a)
    faelle = {}
    for name, eta, nutz in (("eta 0,35, Divertor genutzt", 0.35, 1.0), ("eta 0,317 (WWER-1000), Divertor genutzt", 0.317, 1.0),
                            ("eta 0,376 (Isar 2), Divertor genutzt", 0.376, 1.0), ("eta 0,35, Divertor verloren", 0.35, 0.0)):
        b = bilanz(argparse.Namespace(**{**vars(a), "eta": eta, "div_nutzbar": nutz}))
        faelle[name] = {k: round(b[k]) for k in ("P_fus_MW", "P_th_MW", "P_brutto_MW")}
    WURZEL.mkdir(parents=True, exist_ok=True)
    (WURZEL / "bilanz.json").write_text(json.dumps({"parameter": vars(a), "bilanz": e, "empfindlichkeit": faelle,
                                                     "referenz": REFERENZ}, indent=1, ensure_ascii=False))
    bild(a, e, WURZEL / "bilanz.png")
    print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in e.items() if k not in ("kreise", "vergleich")},
                     indent=0, ensure_ascii=False))
    for n, k in e["kreise"].items():
        print(f"{n}: {k['P_MW']:.0f} MW, {k['m_kg_s']:.0f} kg/s, {k['V_m3_s']:.1f} m3/s")
    print(json.dumps(e["vergleich"], indent=0)); print(json.dumps(faelle, indent=0, ensure_ascii=False))


if __name__ == "__main__":
    main()
