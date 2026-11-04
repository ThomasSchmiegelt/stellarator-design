# Wechselwirkung der Formparameter im Surrogat

Surrogat: Gradient Boosting, R2 = 0.91 (zurueckgehaltene Daten). Zehn wichtigste Eingaben untersucht. Nur im Datenbereich gueltig.

## A1: Einzelwirkung (Teilabhaengigkeit, Aenderung von log10(QI) zwischen 5. und 95. Perzentil des Parameters)

| Parameter | Aenderung log10(QI) | Richtung (QI sinkt bei...) |
|---|---|---|
| r_cos[1,-2] | 0.32 | kleineren Werten (Minimum bei -0.0198) |
| z_sin[1,0] | 0.34 | kleineren Werten (Minimum bei -0.209) |
| r_cos[1,1] | 0.41 | kleineren Werten (Minimum bei -0.0678) |
| r_cos[0,1] | 0.33 | kleineren Werten (Minimum bei -0.0455) |
| r_cos[1,-1] | 0.32 | kleineren Werten (Minimum bei -0.0811) |
| nfp | 0.20 | kleineren Werten (Minimum bei 2) |
| r_cos[1,0] | 0.16 | kleineren Werten (Minimum bei 0.1) |
| z_sin[0,1] | 0.16 | kleineren Werten (Minimum bei -0.264) |
| z_sin[1,-2] | 0.15 | groesseren Werten (Minimum bei 0.0591) |
| z_sin[1,1] | 0.12 | groesseren Werten (Minimum bei 0.0689) |

## A2: Paar-Wechselwirkung (H-Mass: Anteil der gemeinsamen Wirkung, der nicht aus den Einzelwirkungen folgt)

| Paar | H-Mass | Gemeinsame Wirkung (log10 QI) |
|---|---|---|
| z_sin[1,0] + r_cos[1,0] | 0.06 | 0.58 |
| r_cos[0,1] + nfp | 0.05 | 0.52 |
| r_cos[1,-2] + r_cos[0,1] | 0.03 | 0.55 |
| r_cos[1,-1] + nfp | 0.03 | 0.49 |
| r_cos[1,-1] + r_cos[1,0] | 0.03 | 0.43 |
| z_sin[1,0] + r_cos[1,1] | 0.02 | 0.71 |
| r_cos[1,1] + z_sin[0,1] | 0.02 | 0.56 |
| r_cos[1,1] + r_cos[1,0] | 0.01 | 0.59 |
| r_cos[1,-1] + z_sin[1,1] | 0.01 | 0.39 |
| r_cos[1,-2] + z_sin[1,-2] | 0.01 | 0.51 |
| r_cos[0,1] + r_cos[1,-1] | 0.01 | 0.54 |
| r_cos[1,-2] + z_sin[1,0] | 0.01 | 0.65 |

## C: Kennzahlen untereinander (Rangkorrelation, nur Paare mit Betrag ueber 0,5)

| Kennzahl A | Kennzahl B | Rangkorrelation |
|---|---|---|
| axis_magnetic_mirror_ratio | edge_magnetic_mirror_ratio | +0.77 |
| edge_rotational_transform_over_n_field_periods | axis_rotational_transform_over_n_field_periods | +0.75 |
| max_elongation | flux_compression_in_regions_of_bad_curvature | +0.72 |
| aspect_ratio | edge_magnetic_mirror_ratio | -0.61 |
| aspect_ratio | minimum_normalized_magnetic_gradient_scale_length | +0.53 |

## Suche im Surrogat (Schritte auf den stark wechselwirkenden Paaren, Werte innerhalb 1. bis 99. Perzentil der Daten)

| Start | QI Start (Surrogat) | QI gefunden (Surrogat) | Abstand zu den Daten | geaenderte Eingaben (Start -> neu) |
|---|---|---|---|---|
| dje | 0.00182 | 0.00038 | 1.61 | nfp 4->2.34; r_cos[0,1] 0.0466->-0.0497; r_cos[1,-1] -0.0557->-0.106; z_sin[1,0] -0.165->-0.211; r_cos[1,0] 0.0836->0.0532 |
| dpr | 0.00134 | 0.00026 | 2.76 | nfp 2->1.55; r_cos[0,1] 0.0989->-0.0195; r_cos[1,1] -0.00989->-0.117; z_sin[1,0] -0.194->-0.266; r_cos[1,0] 0.0655->0.108 |
| dyu | 0.00182 | 0.00037 | 2.13 | nfp 4->2.43; r_cos[0,1] 0.0466->-0.0441; r_cos[1,0] 0.0836->0.0155; r_cos[1,-1] -0.0557->-0.106; r_cos[1,-2] 0.00592->-0.0376 |
| daten22953 | 0.00018 | 0.00018 | 0.00 |  |
| daten85226 | 0.00078 | 0.00078 | 0.00 |  |
| daten68801 | 0.00018 | 0.00013 | 1.06 | nfp 2->2.37; z_sin[0,1] -0.613->-0.522; r_cos[1,-2] 0.00738->-0.0349; r_cos[0,1] 0.0542->0.0182; z_sin[1,0] -0.0982->-0.119 |

Abstand zu den Daten: kleinster Abstand zu einer Datenform im Raum der zehn wichtigsten Eingaben (in Standardabweichungen); je groesser, desto unsicherer das Surrogat.
