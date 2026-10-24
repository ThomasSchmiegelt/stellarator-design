#!/usr/bin/env python3
"""Validierung: Elmer 'gerader Draht' (mgdyn2D_steady_wire) gegen Biot-Savart.

Geometrie (aus wire2d.grd, Koordinaten in mm via Coordinate Scaling 1e-3):
  Draht 0 <= r <= R = 1e-3 m, homogene Stromdichte J, Gesamtstrom I = 1 A (Body Force
  'Current Density = distribute 1.0'; 'distribute' = Gesamtstrom in A, nicht A/m^2).
  Luftspalt R < r <= 5e-3 m, Dirichlet Az = 0 auf Aussenrand.

Exakte Referenz (2D-planar, A_z, Strom in +z):
  innen  (r <= R):  H(r) = I * r / (2 pi R^2)      (linear, gleichmaessige J)
  aussen (r >  R):  H(r) = I / (2 pi r)             (Biot-Savart, B = mu0*H)

liest f.dat (SaveLine-Schnitt), vergleicht H_Elmer(r) mit H_exact(r) und
liefert Tabelle + relative Fehler. Exit 0 wenn Max-Abweichung < Schwelle, sonst 1.
"""
import math
import sys

MU0 = 4.0 * math.pi * 1e-7
I = 1.0          # A  (Body Force: Current Density = distribute 1.0)
R = 1e-3         # m  (Draht-Radius; Coordinate Scaling 1e-3 -> 1.0 im .grd)
TOLERANZ = 0.15  # relative Abweichung, die als "bestanden" gilt (grobem 4/8/8-Netz)


def main(dat: str = "f.dat") -> int:
    rows = []
    with open(dat) as f:
        for line in f:
            p = line.split()
            if len(p) < 12:
                continue
            try:
                x = float(p[3])
                Hy = float(p[11])
            except ValueError:
                continue
            if abs(x) > 1e-12:  # Zentrum überspringen
                rows.append((abs(x), abs(Hy)))
    rows.sort()

    print(f"Elmer vs. Biot-Savart, gerader Draht: I={I} A, R={R*1e3:.1f} mm, n={len(rows)} Punkte")
    print(f"{'r [mm]':>9} {'H_Elmer [A/m]':>13} {'H_exakt [A/m]':>13} {'rel. Fehle...[truncated]