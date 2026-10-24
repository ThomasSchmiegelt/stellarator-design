"""Biot-Savart-Pruefung: Elmer 2D-planarer gerader Draht (mgdyn2D_steady_wire).

Geometrie: Draht R=1e-3 m (homogetre Stromdichte, I=1 A), Luftspalt bis 5e-3 m.
Exakt:  innen  H=I*r/(2*pi*R^2)   |   aussen H=I/(2*pi*r)   (B=mu0*H)
Quelle: f.dat (SaveLine-Schnitt ueber x-Achse, Spalte 3=x[m], Spalte 12=H_y[A/m]).
"""
import math
import sys

MU0 = 4.0 * math.pi * 1e-7
I = 1.0           # A   (Body Force: Current Density = -distribute 1.0)
R = 1.0e-3        # m   (Draht-Radius)
DATENPFAD = "f.dat"
SICHER = 5.0      # 5 %: mittlere relative Abweichung (Prozent)
RANDKNOTEN = 1.0e-3  # letzte aeussere Stuetze (Dirichlet-BC-Artefakt) wird aus Max-Metrik rausgenommen


def hinnerr(r):
    return I * r / (2.0 * math.pi * R * R)


def hausser(r):
    return I / (2.0 * math.pi * r)


def main():
    punkte = []
    with open(DATENPFAD) as f:
        for zeile in f:
            p = zeile.split()
            if len(p) < 12:
                continue
            try:
                x = float(p[3])
                hy = float(p[11])
            except ValueError:
                continue
            r = abs(x)
            if r > 1.0e-12:
                punkte.append((r, abs(hy)))
    punkte.sort() if punkte else None
    innere = [p for p in punkte if p[0] <= 1.02 * R]
    auesere = [p for p in punkte if p[0] > 1.02 * R]

    def durchschnitte(punkte, exact):
        if not punkte:
            return None
        return sum(h / exact(r) for r, h in punkte) / len(punkte)

    d_inn = durchschnitte(innere, hinnerr)
    d_aus = durchschnitte(auesere, hausser)
    if d_inn is None or d_aus is None:
        print("FEHLER: keine Punkte in f.dat gelesen")
        return 1

    fehler = max(abs(d_inn - 1.0), abs(d_aus - 1.0)) * 100.0
    # Punktweises Maximum ohne den aeussersten Randknoten (Dirichlet-BC-Artefakt)
    maxp = max(abs(h/e - 1.0) for r, h in auesere
               for e in [ hausser(r)] if r <= 4.8e-3) * 100.0
    bestanden = fehler < SICHER

    print("=" * 78)
    print("VALIDIERUNG: Elmer 2D-planarer gerader Draht vs. Biot-Savart")
    print("=" * 78)
    print(f"Strom I = {I:.1f} A (distribute), Draht-Radius R = {R*1e3:.1f} mm")
    print(f"Knoten: gesamt {len(punkte)}, innere {len(innere)}, aeussere {len(auesere)}")
    print()
    print("Tabelle (aussenbereich, Biot-Savart H = I/(2*pi*r)):")
    print(f"{'r [mm]':>8} {'H_Elmer [A/m]':>14} {'H_exakt [A/m]':>14} {'rel. Abw.':>10}")
    for r, h in auesere[:: max(1, len(auesere) // 12)]:
        exact = hausser(r)
        print(f"{r*1e3:8.2f} {h:14.4f} {exact:14.4f} {100*(h/exact-1):+9.2f} %")
    print(f"{'r [mm]':>8} (innere Stuetzen)")
    for r, h in innere:
        exact = hinnerr(r)
        print(f"{r*1e3:8.3f} {h:14.4f} {exact:14.4f} {100*(h/exact-1):+9.2f} %")
    print()
    print(f"Schnitt innere H/Hexakt : {d_inn:.5f}  ({100*(d_inn-1):+.2f} %)")
    print(f"Schnitt aeussere H/Hexakt: {d_aus:.5f}  ({100*(d_aus-1):+.2f} %)")
    print(f"Max. Abweich. ohne Randknoten (r<=4.8mm): {maxp:.2f} %")
    print(f"Schnittwert-Abweichung: {fehler:.2f} %  (Schwelle {SICHER:.0f} %)")
    print()
    print("ERGEBNIS: " + ("BESTANDEN" if bestanden else "NICHT BESTANDEN"))
    return 0 if bestanden else 2


if __name__ == "__main__":
    sys.exit(main())
