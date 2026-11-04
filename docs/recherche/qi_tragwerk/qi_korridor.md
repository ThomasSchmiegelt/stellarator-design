# Parameterkorridor fuer ein optimales Plasma (QI)

158685 Plasmen, gut = QI <= 0.001: 2420 (1.53 %). Kennzahlen sind Messgroessen, keine Entwurfsparameter. Nur Korrelation.

## (a) Kasten aus den guten Plasmen (5. bis 95. Perzentil)

| Merkmal | von | bis | alle (5. bis 95.) |
|---|---|---|---|
| n_field_periods | 1 | 5 | 1 bis 5 |
| aspect_ratio | 7.6 | 9.69 | 5.27 bis 10.6 |
| max_elongation | 5.35 | 7.45 | 2.3 bis 7.17 |
| average_triangularity | -0.618 | 0.27 | -0.547 bis 0.307 |
| axis_magnetic_mirror_ratio | 0.274 | 0.403 | 0.121 bis 0.576 |
| edge_magnetic_mirror_ratio | 0.302 | 0.429 | 0.197 bis 0.854 |
| edge_rotational_transform_over_n_field_periods | 0.0695 | 0.247 | -0.0181 bis 0.498 |
| axis_rotational_transform_over_n_field_periods | 0.104 | 0.277 | -0.0173 bis 0.349 |
| vacuum_well | -0.145 | -0.0105 | -0.477 bis -0.00245 |
| flux_compression_in_regions_of_bad_curvature | 0.887 | 1.89 | 0.625 bis 1.79 |
| minimum_normalized_magnetic_gradient_scale_length | 2.36 | 8.33 | 1.58 bis 10.2 |

Im Kasten: 4824 Plasmen, davon gut 1123: Reinheit 23.3 %, Abdeckung 46.4 % der guten (Grundrate 1.53 %).

## (b) Entscheidungsbaum Tiefe 3: Bereiche mit den meisten guten Plasmen

| Reinheit | gut | im Bereich | Bedingungen |
|---|---|---|---|
| 20 % | 1526 | 7822 | max_elongation > 6.06; edge_magnetic_mirror_ratio <= 0.43; axis_magnetic_mirror_ratio > 0.325 |
| 3 % | 400 | 11912 | max_elongation > 6.06; edge_magnetic_mirror_ratio <= 0.43; axis_magnetic_mirror_ratio <= 0.325 |
| 3 % | 227 | 8132 | max_elongation <= 6.06; max_elongation > 5.38; axis_magnetic_mirror_ratio > 0.279 |
| 0 % | 115 | 102290 | max_elongation <= 6.06; max_elongation <= 5.38; edge_magnetic_mirror_ratio <= 0.97 |
| 1 % | 78 | 13979 | max_elongation <= 6.06; max_elongation > 5.38; axis_magnetic_mirror_ratio <= 0.279 |

Die drei besten Bereiche zusammen decken 2153 von 2420 guten Plasmen ab (89 %).

## (b) Entscheidungsbaum Tiefe 5: Bereiche mit den meisten guten Plasmen

| Reinheit | gut | im Bereich | Bedingungen |
|---|---|---|---|
| 40 % | 740 | 1857 | max_elongation > 6.06; edge_magnetic_mirror_ratio <= 0.43; axis_magnetic_mirror_ratio > 0.325; aspect_ratio <= 9.09; edge_rotational_transform_over_n_field_periods <= 0.256 |
| 18 % | 675 | 3741 | max_elongation > 6.06; edge_magnetic_mirror_ratio <= 0.43; axis_magnetic_mirror_ratio > 0.325; aspect_ratio > 9.09; average_triangularity <= -0.113 |
| 13 % | 252 | 1983 | max_elongation > 6.06; edge_magnetic_mirror_ratio <= 0.43; axis_magnetic_mirror_ratio <= 0.325; n_field_periods <= 2.5; edge_rotational_transform_over_n_field_periods <= 0.224 |
| 14 % | 165 | 1209 | max_elongation <= 6.06; max_elongation > 5.38; axis_magnetic_mirror_ratio > 0.279; edge_magnetic_mirror_ratio <= 0.422; aspect_ratio <= 9.37 |
| 4 % | 115 | 3254 | max_elongation > 6.06; edge_magnetic_mirror_ratio <= 0.43; axis_magnetic_mirror_ratio <= 0.325; n_field_periods > 2.5; axis_magnetic_mirror_ratio > 0.289 |

Die drei besten Bereiche zusammen decken 1667 von 2420 guten Plasmen ab (69 %).
