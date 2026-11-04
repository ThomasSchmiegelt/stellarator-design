# QI-Güte: Bereiche der besten Plasmen und gemeinsames Modell

158685 Plasmen. Beste 1 % = QI höchstens 0.00084. Nur Korrelation, keine Ursache.

## Bereiche (5. bis 95. Perzentil)

| Merkmal | alle | beste 1 % | beste 10 % |
|---|---|---|---|
| boundary.n_field_periods | 1 bis 5 | 1 bis 4 | 1 bis 5 |
| aspect_ratio | 5.27 bis 10.6 | 7.48 bis 9.67 | 7.88 bis 9.91 |
| max_elongation | 2.3 bis 7.17 | 5.29 bis 7.43 | 2.08 bis 7.37 |
| average_triangularity | -0.547 bis 0.307 | -0.618 bis 0.302 | -0.611 bis 0.242 |
| axis_magnetic_mirror_ratio | 0.121 bis 0.576 | 0.278 bis 0.402 | 0.237 bis 0.472 |
| edge_magnetic_mirror_ratio | 0.197 bis 0.854 | 0.305 bis 0.427 | 0.273 bis 0.556 |
| edge_rotational_transform_over_n_field_periods | -0.0181 bis 0.498 | 0.0681 bis 0.242 | 0.015 bis 0.279 |
| axis_rotational_transform_over_n_field_periods | -0.0173 bis 0.349 | 0.101 bis 0.272 | 0.0152 bis 0.288 |
| vacuum_well | -0.477 bis -0.00245 | -0.142 bis -0.00935 | -0.168 bis -0.00659 |
| flux_compression_in_regions_of_bad_curvature | 0.625 bis 1.79 | 0.875 bis 1.9 | 0.638 bis 1.82 |
| minimum_normalized_magnetic_gradient_scale_length | 1.58 bis 10.2 | 2.29 bis 7.85 | 2.48 bis 10.6 |

## Gemeinsames Modell (Gradient Boosting, zurückgehaltene Daten): R² = 0.90

Wichtigkeit (Verlust an R², wenn das Merkmal gemischt wird):

| Merkmal | Wichtigkeit |
|---|---|
| axis_magnetic_mirror_ratio | 1.188 |
| edge_magnetic_mirror_ratio | 1.004 |
| edge_rotational_transform_over_n_field_periods | 0.166 |
| max_elongation | 0.164 |
| boundary.n_field_periods | 0.089 |
| vacuum_well | 0.086 |
| aspect_ratio | 0.083 |
| minimum_normalized_magnetic_gradient_scale_length | 0.081 |
| flux_compression_in_regions_of_bad_curvature | 0.052 |
| axis_rotational_transform_over_n_field_periods | 0.047 |
| average_triangularity | 0.035 |

Zum Vergleich: bester Einzelwert als R² (Rangkorrelation²) war 0,12.
