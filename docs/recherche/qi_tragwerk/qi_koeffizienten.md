# Formkoeffizienten -> QI

158685 Plasmen, 91 Eingaben (Feldperioden, r_cos und z_sin je 45). Gut = QI <= 0.001: 2420.

Gradient Boosting auf log10(QI), zurueckgehaltene Daten: R2 = 0.91.

## Wichtigste Eingaben (Verlust an R2 beim Mischen)

| Eingabe | Wichtigkeit |
|---|---|
| r_cos[1,-2] | 0.194 |
| z_sin[1,0] | 0.194 |
| r_cos[1,1] | 0.184 |
| r_cos[0,1] | 0.169 |
| r_cos[1,-1] | 0.129 |
| nfp | 0.090 |
| r_cos[1,0] | 0.079 |
| z_sin[0,1] | 0.059 |
| z_sin[1,-2] | 0.051 |
| z_sin[1,1] | 0.051 |
| z_sin[2,0] | 0.050 |
| r_cos[0,2] | 0.039 |

## Kasten auf den fuenf wichtigsten Eingaben (5. bis 95. Perzentil der guten)

| Eingabe | von | bis |
|---|---|---|
| r_cos[1,-2] | -0.0269 | 0.0525 |
| z_sin[1,0] | -0.206 | -0.0868 |
| r_cos[1,1] | -0.0531 | 0.0291 |
| r_cos[0,1] | -0.0874 | 0.0921 |
| r_cos[1,-1] | -0.0966 | 0.0248 |

Im Kasten 66676 Plasmen, davon gut 1530: Reinheit 2.3 % (Grundrate 1.53 %), Abdeckung 63 %.

## Bester Bereich des Entscheidungsbaums (Tiefe 5): Reinheit 5 %, 483 gut von 9050

- z_sin[0,1] > -0.178
- r_cos[1,2] > -0.0201
- z_sin[0,1] <= 0.364
- r_cos[1,-1] <= -0.0458
- r_cos[0,3] <= -0.000889
