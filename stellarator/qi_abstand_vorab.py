"""Vorabrechnung Platz fuer die Abschirmung (F-215). Reines Rechnen, ohne Elmer.

  python3 -m stellarator.qi_abstand_vorab   -> docs/recherche/qi_tragwerk/abstand_vorab.md

Modell wie kopplung.py: Fluenz ~ Wandlast * exp(-(Huelle-0,1)/0,1); Package braucht Abschirmung >= 1,0 m.
Wandlast ~ P / Plasmaflaeche (P fest: 1 GW netto). Huelle(s) = s * Huelle(1) (Wandstaerken wachsen mit).
Huelle aus Spule-Plasma-Abstand: Huelle ~ Abstand - c mit c = Abstand - Huelle der drei gerechneten Saetze (Schaetzung).
"""
import csv, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
A_REF = 1.80          # a bei Volumen 1096 m3 und Aspektverhaeltnis ~9,6 (a ~ (V/(2 pi^2 AR))^(1/3))
V = 1096.0
LAM, SPALT, PMIN, FLZ = 0.10, 0.10, 1.0, 3.0e18
FL_REF = {  # gerechnete Saetze: Huelle m, Fluenz
    "dje": (0.478, 5.50e21), "dyu": (0.805, 2.08e20), "dsd": (1.087, 1.24e19)}


def fluenz(huelle, s, f0):
    """Fluenz bei Skalierung s (Leistung fest -> Wandlast ~ 1/s^2) aus Referenz (h0, F0) bei s=1."""
    h0, F0 = f0
    return F0 / s ** 2 * math.exp(-(huelle * s - h0) / LAM)


def s_noetig(f0):
    h0 = f0[0]
    s = 1.0
    while s < 6:
        if fluenz(h0, s, f0) <= FLZ and h0 * s - SPALT >= PMIN:
            return s
        s += 0.005
    return float("nan")


def main():
    z = ["# Platz fuer die Abschirmung: Vorabrechnung (Schaetzung, F-215)", "",
         "## Weg 1: Anlage groesser bei gleicher Leistung (1 GW netto), Wandstaerken wachsen mit", "",
         "| Satz | Huelle bei s=1 | Fluenz s=1 | noetiges s | Plasmavolumen | Kraft je Spule |", "|---|---|---|---|---|---|"]
    for k, f0 in FL_REF.items():
        s = s_noetig(f0)
        z.append(f"| {k} | {f0[0]:.2f} m | {f0[1]:.1e} | {s:.2f} | x{s**3:.1f} | x{s**2:.1f} |")
    z += ["", "Kraft je Spule bei gleichem Feld ~ s^2; Spannung bei mitwachsenden Waenden etwa gleich (Schaetzung, ungeprueft).", ""]
    rows = list(csv.DictReader(open(ROOT / "docs/recherche/qi_tragwerk/kraft_scan_qi.csv")))
    c = sum(d - h for d, h in ((0.85 * A_REF, 0.478), (0.94 * A_REF, 0.805), (1.15 * A_REF, 1.087))) / 3
    z += [f"## Weg 2: vorhandene Saetze mit mehr Abstand (Huelle ~ Abstand - {c:.2f} m, Schaetzung)", "",
          "| Satz | nfp | QI | Abstand/a | Abstand m | Huelle geschaetzt | Fluenz geschaetzt | Kraft f_max |", "|---|---|---|---|---|---|---|---|"]
    out = []
    for r in rows:
        try:
            qi, d, fm, ar = float(r["qi"]), float(r["spule_plasma_a"]), float(r["f_max"]), float(r["metrics.aspect_ratio"])
        except ValueError:
            continue
        a = (V / (2 * math.pi ** 2 * ar)) ** (1 / 3)
        h = d * a - c
        fl = FL_REF["dyu"][1] * math.exp(-(h - FL_REF["dyu"][0]) / LAM)
        out.append((qi, r["id"][:8], r["nfp"], d, d * a, h, fl, fm))
    out.sort()
    for qi, i, n, d, dm, h, fl, fm in out:
        if h >= 1.15 and qi < 0.003:
            z.append(f"| {i} | {n} | {qi:.5f} | {d:.2f} | {dm:.2f} | {h:.2f} | {fl:.1e} | {fm:.0f} |")
    z += ["", "Bezug Kraft: DjLe3eL6 13,7, DYU 18,0, DSD 42,5, DP9 10,4 (gleiche dimensionslose Einheit)."]
    p = ROOT / "docs/recherche/qi_tragwerk/abstand_vorab.md"; p.write_text("\n".join(z) + "\n"); print("\n".join(z))


if __name__ == "__main__":
    main()
