"""kuehlung_waerme.py — grobe Waermeabschaetzung fuer die Plasmaseite eines Kuehlsegments (1D, ohne Rechnung).

    .venv/bin/python -m stellarator.kuehlung_waerme [--name f11] [--q 0.5]

Temperaturanstieg von der Kuehlwassertemperatur bis zur Plasmaseite der Innenhaut bei der Waermestromdichte q:
  Leitung durch die Innenhaut   dT_haut = q * s / k_stahl
  Uebergang an das Wasser       dT_wasser = q / (h * f_rippe),  h aus Dittus-Boelter mit v aus der FluidX3D-Auswertung
Druckwasser 300 Grad C / 15 MPa. Hydraulischer Durchmesser des Gyroids d_h = 4 eps / (S/V) mit S/V = 2 * 3,09 / a
(beide Seiten der Gyroid-Wand, Zellgroesse a). f_rippe: wirksame Flaechenvergroesserung durch die an die Haut
angebundenen Filamente (grob 1 = ohne, 2 = mit Rippenwirkung). Ergebnis ist eine Groessenordnung, keine Auslegung.
"""
import argparse, json
from .kuehlung_segment import WURZEL

NU, K_W, PR = 1.2e-7, 0.55, 0.9          # Druckwasser 300 C: kin. Viskositaet [m2/s], Waermeleitung [W/mK], Prandtl
K_STAHL = 25.0                            # warmfester Stahl bei 400-500 C [W/mK]


def h_dittus(v, d_h):
    re = v * d_h / NU
    return 0.023 * re ** 0.8 * PR ** 0.4 * K_W / d_h, re


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="f11")
    ap.add_argument("--q", type=float, default=0.5, help="Waermestromdichte [MW/m2]")
    a = ap.parse_args(argv)
    o = WURZEL / a.name
    p = json.loads((o / "auslegung.json").read_text())["parameter"]
    w = json.loads((o / "cfd" / "auswertung.json").read_text())
    q = a.q * 1e6; zelle = p["zelle_vorn"]; eps = 0.82
    d_h = 4 * eps / (2 * 3.09 / zelle)
    zeilen = []
    for name, v in (("Plasmaseite Mittel", w["plasmaseite"]["v_mittel_m_s"]), ("vordere Schicht Mittel", w["schicht_vorn"]["v_mittel_m_s"]),
                    ("Ziel 1 m/s", 1.0)):
        h, re = h_dittus(v, d_h)
        zeilen.append({"fall": name, "v_m_s": v, "Re": re, "h_W_m2K": h,
                       "dT_wasser_ohne_rippe_K": q / h, "dT_wasser_mit_rippe_K": q / (2 * h)})
    # feine Kanaele an der Haut (Vorschlag): 10 mm, 1 m/s
    h, re = h_dittus(1.0, 0.010)
    zeilen.append({"fall": "Vorschlag Kanal 10 mm, 1 m/s", "v_m_s": 1.0, "Re": re, "h_W_m2K": h,
                   "dT_wasser_ohne_rippe_K": q / h, "dT_wasser_mit_rippe_K": q / (2 * h)})
    haut = {f"{s * 1000:.0f} mm": q * s / K_STAHL for s in (p["haut_innen"], 0.010, 0.005, 0.003)}
    erg = {"q_MW_m2": a.q, "d_h_m": d_h, "dT_haut_K": haut, "uebergang": zeilen,
           "v_p10_plasmaseite_m_s": w["plasmaseite"]["v_p10_m_s"]}
    (o / "waerme.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))
    print(f"q = {a.q} MW/m2, d_h Gyroid = {d_h * 1000:.0f} mm")
    for s, dt in haut.items():
        print(f"  Innenhaut {s:>6}: dT Leitung {dt:6.0f} K")
    for z in zeilen:
        print(f"  {z['fall']:<30} v {z['v_m_s']:5.2f} m/s  Re {z['Re']:8.0f}  h {z['h_W_m2K']:6.0f} W/m2K  "
              f"dT {z['dT_wasser_ohne_rippe_K']:5.0f} K (mit Rippen ~{z['dT_wasser_mit_rippe_K']:4.0f} K)")
    print(f"  10 % der Plasmaseite unter {w['plasmaseite']['v_p10_m_s'] * 1000:.1f} mm/s (Totwasser)")


if __name__ == "__main__":
    main()
