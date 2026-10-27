"""blei_kanal.py — Erstwand-Kanaele mit fluessigem Blei bzw. Bleilithium statt Wasser: MHD-Druckverlust, Temperaturen.

    .venv/bin/python -m stellarator.blei_kanal [--name b1] [--b 20] [--h 20] [--steg 4] [--haut 5] [--rueck 5]
                                              [--q 0.5] [--T_ein 350] [--dT 150] [--B 6.0] [--steigung 6]
                                              [--ohne_elmer]

Gleicher Aufbau wie stellarator/erstwand_kanal.py (Innenhaut | Kanaele | Rueckwand | trockener Gyroid), Waermelast
q ueber die Plasmaseite des Segments 85-95 Grad. Das Metall bringt die Waerme nach aussen zu einem Dampferzeuger
ausserhalb der Spulen (kein Wasser in der Wand).

Fliesst ein Leiter quer zum Magnetfeld, bremsen ihn die induzierten Stroeme (Lorentzkraft). Grobe Formel fuer
ausgebildete Stroemung in einem Kanal:  dp/dx = sigma * v * B_quer^2 * k_p
  leitende Stahlwaende:      k_p = c / (1 + c),  c = sigma_Wand * t_Wand / (sigma * b/2)   (Wandleitfaehigkeit)
  isolierende Schicht (FCI): k_p = 1 / Ha,       Ha = B_quer * b/2 * sqrt(sigma / mu)      (Hartmann-Zahl)
B_quer = B * sin(alpha), alpha = Winkel zwischen Kanal und Feld. Faelle:
  toroidal  Kanaele laufen toroidal, das Feld ist in einem Stellarator ueberwiegend toroidal; alpha = Steigung
            der Feldlinien (Schaetzung tan(alpha) ~ iota * r / R ~ 0,1 -> 6 Grad, mit --steigung variieren)
  poloidal  Kanaele quer zum Feld, alpha = 90 Grad
  gyroid    Stroemung in alle Richtungen, Mittel sin^2 = 2/3
Nicht enthalten: Zusatzverluste in Kehren, Verteilern und Querschnittsaenderungen (3D-MHD, dort oft der groesste
Anteil), Korrosion, Volumenwaerme aus Neutronen. Waermeuebergang konservativ Nu = 5 (das Feld daempft Turbulenz).
Stoffwerte aus dem Gedaechtnis, nicht an Quellen geprueft. Ausgabe sim/blei/<name>/: auslegung.json, querschnitt.png,
vergleich.png.
"""
import argparse, json
from types import SimpleNamespace
import numpy as np

from .erstwand_kanal import umfang, querschnitt
from .lauf import PROJEKT

WURZEL = PROJEKT / "sim" / "blei"
# rho [kg/m3], cp [J/kgK], k [W/mK], mu [Pa s], sigma [S/m], Schmelzpunkt [C]  (bei etwa 400 C, ungeprueft)
STOFF = {"Blei": dict(rho=10450, cp=147, k=17.0, mu=1.9e-3, sigma=1.0e6, T_schmelz=327),
         "Bleilithium": dict(rho=9700, cp=190, k=14.0, mu=1.4e-3, sigma=7.7e5, T_schmelz=235)}
SIGMA_STAHL = 1.2e6             # ferritisch-martensitischer Stahl bei 400 C [S/m]
NU = 5.0
FAELLE = {"toroidal": None, "poloidal": 1.0, "gyroid": 2 / 3}     # sin^2(alpha); toroidal aus --steigung


def auslegung(a, medium, fall, isoliert):
    s = STOFF[medium]
    U, R = umfang()
    p = (a.b + a.steg) / 1000; n = int(U / p)
    bh, A_k = a.b / 2000, a.b * a.h / 1e6
    d_h = 2 * a.b * a.h / (a.b + a.h) / 1000
    L = R * np.radians(10.0)
    P = a.q * 1e6 * U * L.mean()
    Q = P / (s["rho"] * s["cp"] * a.dT)
    v = Q / (n * A_k)
    sin2 = np.sin(np.radians(a.steigung)) ** 2 if FAELLE[fall] is None else FAELLE[fall]
    Bq = a.B * np.sqrt(sin2)
    ha = Bq * bh * np.sqrt(s["sigma"] / s["mu"])
    c = SIGMA_STAHL * min(a.steg / 2, a.haut) / 1000 / (s["sigma"] * bh)
    k_p = 1 / max(ha, 1.0) if isoliert else c / (1 + c)
    dp_mhd = s["sigma"] * v * Bq ** 2 * k_p * L.max()
    re = s["rho"] * v * d_h / s["mu"]
    f = 64 / re if re < 2300 else 0.316 * re ** -0.25
    dp_reib = f * L.max() / d_h * s["rho"] * v ** 2 / 2
    dp = dp_mhd + dp_reib
    h = NU * s["k"] / d_h
    return {"medium": medium, "fall": fall, "isoliert": isoliert, "kanaele": n, "laenge_m": float(L.max()),
            "waermelast_MW": P / 1e6, "volumenstrom_m3_s": Q, "massenstrom_kg_s": Q * s["rho"], "v_m_s": v,
            "B_quer_T": Bq, "Ha": ha, "c_wand": c, "k_p": k_p, "dp_mhd_kPa": dp_mhd / 1e3, "dp_reib_kPa": dp_reib / 1e3,
            "dp_kPa": dp / 1e3, "pumpleistung_kW": Q * dp / 1e3, "pumpleistung_anteil": Q * dp / P, "h_W_m2K": h,
            "T_aus_C": a.T_ein + a.dT, "abstand_schmelzpunkt_K": a.T_ein - s["T_schmelz"]}


def vergleich(erg, datei, a):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4.8))
    namen = [f"{e['fall']}\n{'isoliert' if e['isoliert'] else 'Stahlwand'}" for e in erg if e["medium"] == "Blei"]
    x = np.arange(len(namen))
    for i, (m, farbe) in enumerate((("Blei", "#5a6b8c"), ("Bleilithium", "#c9853a"))):
        w = [e["dp_kPa"] for e in erg if e["medium"] == m]
        bars = ax.bar(x + (i - 0.5) * 0.38, w, 0.38, color=farbe, label=m)
        ax.bar_label(bars, labels=[f"{v:,.0f}".replace(",", ".") for v in w], fontsize=8, padding=2)
    ax.axhline(49, color="#2a9fd6", ls="--", lw=1.2); ax.text(x[-1] + 0.45, 49 * 1.15, "Wasser n5: 49 kPa", ha="right", color="#2a9fd6", fontsize=9)
    ax.set_yscale("log"); ax.set_xticks(x, namen); ax.set_ylabel("Druckverlust im Segment [kPa]")
    ax.set_title(f"Flüssigmetall in Erstwand-Kanälen {a.b:g}×{a.h:g} mm bei {a.B:g} T, {a.T_ein:g} → {a.T_ein + a.dT:g} °C "
                 f"(Feldsteigung toroidal {a.steigung:g}°)\nnur ausgebildete Strömung, ohne Kehren und Verteiler · Stoffwerte ungeprüft",
                 fontsize=10)
    ax.legend(); fig.tight_layout(); fig.savefig(datei, dpi=130); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="b1")
    for k, d in (("b", 20.0), ("h", 20.0), ("steg", 4.0), ("haut", 5.0), ("rueck", 5.0), ("q", 0.5), ("T_ein", 350.0),
                 ("dT", 150.0), ("B", 6.0), ("steigung", 6.0)):
        ap.add_argument(f"--{k}", type=float, default=d)
    ap.add_argument("--ohne_elmer", action="store_true")
    a = ap.parse_args(argv)
    o = WURZEL / a.name; o.mkdir(parents=True, exist_ok=True)
    erg = [auslegung(a, m, f, iso) for m in STOFF for f, iso in
           (("toroidal", False), ("toroidal", True), ("poloidal", False), ("poloidal", True), ("gyroid", False))]
    vergleich(erg, o / "vergleich.png", a)
    aus = {"parameter": vars(a), "faelle": erg}
    if not a.ohne_elmer:
        # Temperatur im Querschnitt mit Blei am Austritt (gleiches h fuer alle Faelle)
        e = erg[0]
        qa = SimpleNamespace(**vars(a), medium="Blei", fall=f"Nu = {NU:g}, h = {e['h_W_m2K']:.0f} W/m²K")
        aus["querschnitt"] = querschnitt(qa, e["h_W_m2K"], e["T_aus_C"], o)
    (o / "auslegung.json").write_text(json.dumps(aus, indent=1, ensure_ascii=False))
    for e in erg:
        print(f"{e['medium']:12s} {e['fall']:9s} {'iso ' if e['isoliert'] else 'Wand'} v={e['v_m_s']:.2f} Ha={e['Ha']:7.0f} "
              f"dp={e['dp_kPa']:9.1f} kPa  Pumpe={e['pumpleistung_kW']:8.1f} kW ({e['pumpleistung_anteil'] * 100:.2f} %)")
    if "querschnitt" in aus:
        print(aus["querschnitt"])


if __name__ == "__main__":
    main()
