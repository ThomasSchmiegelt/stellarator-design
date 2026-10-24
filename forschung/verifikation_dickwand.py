"""Dickwand-Vergleich (B-010): N verschachtelte Leiterschleifen statt
einem thin-wire-Draht, gleiche Lage wie thin-wire-Modell (alle Spulen bei
Toruswinkel 0).  B auf der Achse A=(R0,0,0) (toroidale Richtung y).
dB_y ~ (dz*(R0-x) + dx*z)/r^3, r = (R0-x, 0, -z), Schleife in y=0-Ebene.
Koarse Annahmen: verschachtelte Ellipsen, f in [0.55,1].  50 NPC (108 Win.)
+ 20 PLC (36 Win., R=2.0 m)."""
import numpy as np
import math

R0 = 5
R0 = 5.5
MU0 = 4e-7 * math.pi

def BpA(a0, b0, N, fmin=0.55):
    seg = 800
    t = np.linspace(0.0, 2.0 * math.pi, seg, endpoint=False)
    ct = np.cos(t)
    integ = 0.0
    for f in np.linspace(fmin, 1.0, N):
        rx = R0 - a0 * f * ct
        rz = -b0 * f * np.sin(t)
        r2 = rx * rx + rz * rz
        num = b0 * f * ct * (R0 - a0 * f) - a0 * b0 * f * f
        integ += np.sum(num) / (r2 * np.sqrt(r2))
    return MU0 / (4.0 * math.pi) * integ

# Kontrolle: Kreisschleife R, Punkt auf Achse bei R0
Rc = 1.0
approx = abs(BpA(Rc, Rc, 1))
exact = MU0 * Rc * Rc / (2.0 * (Rc * Rc + R0 * R0) ** 1.5)
print('Ring-Check: %.4g vs %.4g uT/A (Diff %.1f%%)' % (
    approx * 1e6, exact * 1e6, 100 * (abs(approx - exact) / exact)))

# Geometrien (Halbachsen Aussenkontur, N Windungen)
b_npc = BpA(1.75, 1.25, 108)
b_plc = BpA(2.0, 2.0, 36)
b_tot = 50 * b_npc + 20 * b_plc
I_req = 2.5 / b_tot
print('NPC 108 Win: B/A    = %10.4g uT/A' % (b_npc * 1e6))
print('PLC  36 Win: B/A    = %10.4g uT/A' % (b_plc * 1e6))
print('System (70): B/A    = %10.4g uT/A' % (b_tot * 1e6))
print('I fuer 2.5 T : %8.2f kA/Wicklung (dickwand)' % (I_req / 1e3))
print('Thin wire    : %8.2f kA/Wicklung (PARAMETER.json)' % (10.37))
print('W7-X Nenn    :      12.8-14.6 kA/Wicklung (B-005/009)')
