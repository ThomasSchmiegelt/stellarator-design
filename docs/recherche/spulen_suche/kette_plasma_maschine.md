# Von der Plasmaform zur Maschine: die Kette und ihre Lücken (2026-11-07)

![Kette](kette_plasma_maschine.png)

**Lesehilfe.** Jeder Kasten ist ein Glied der Kette, die Pfeile zeigen die Richtung: aus der Plasmaform folgt das Feld, aus den Spulen die Bauteile. Der Rahmen zeigt den Stand: blau = belegt (gerechnet und geprüft), orange = teilweise (nur in einem Bereich oder nur für einen Fall), rot = fehlt. Die Wertung der Challenge misst nur die Glieder 1 und 2 (Plasmaform und QI), die Spulen kommen darin nicht vor.

| Glied | Stand | Beleg / Lücke |
|---|---|---|
| 1 Plasmaform | belegt | Koeffizienten der Fläche, Datensatz und eigene Proben |
| 2 Feld, iota, QI | belegt | VMEC++ rechnet aus der Form (B-050 bis B-056) |
| 3 Spulenform | **fehlt** | Rückwärtsproblem Fläche → Spulen; nur für DjLe3eL6 gibt es einen Spulensatz (Machbarkeit wird geprüft) |
| 4 Ströme S1–S5 | teilweise | Verhältnis ändert QI; lineares Modell nur bis ±5 % (qi_experiment_bericht.md) |
| 5 Freie Grenze | teilweise | konvergiert nur mit Sonderzuständen; Gegenprüfung der Ausreißer scheiterte (B-057) |
| 6 Tragwerk, Spannung | teilweise | nur für den vorhandenen Spulensatz (nicht neu geprüft) |
| 7 Kühlung, Verguss | teilweise | Kühlsegment bearbeitet, Verguss geplant (nicht neu geprüft) |

**Kernaussage.** Es gibt keine durchgehende Verbindung von der Plasmaform zu den Bauteilen. Wir wissen, dass die Ströme QI über das Verhältnis der Gruppen steuern, nicht über Nähe oder Lage der Spulen (B-053, B-054). Eine Regel, wie sich die Spulenform bei geänderter Plasmaform ändert, haben wir nicht.

**English summary.** The chain from plasma shape to a built machine has seven links. The challenge score only covers links 1–2 (shape and QI). Link 3 (coil shape from plasma shape, an inverse problem) is missing; links 4–7 exist only partially or for one coil set. We found that currents (ratios between coil groups), not coil proximity, steer QI.
