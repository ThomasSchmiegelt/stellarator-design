# Spulensaetze-Scan: CoilStellaration (eval-part-0.parquet)

> **Korrektur (Claude, 2026-11-04):** Die Tabellen unten zählen mit dem MAXIMUM des Feldfehlers. Unsere Grenze (`feld_Bn`)
> und Proximas Vergleichswert sind aber der MITTELWERT. Richtig gezählt (DESC, N = 8058, Mittelwert, Biegeradius ≥ 0,3/0,5/0,6/0,7/0,8/1,0 a):
> Bn < 1e-3: 116/11/3/0/0/0; Bn < 3e-3: 1203/182/44/0/0/0; Bn < 5e-3: 1758/280/68/2/0/0.
> Die alte Aussage (keiner mit Bn < 3e-3 und ≥ 0,7 a) gilt also weiter; „0 Sätze ab 0,5 a“ gilt nicht.
> Satz 2 (DRb36s…): Bn 9,34e-4, 0,57 a. Satz 1 (DnFia…): Bn 8,17e-4, 0,24 a.
> Kandidat für kürzere Spulen: DoUj68WAHwAjWuncNwwFZHN (nfp 3, 6 je Halbperiode, Bn 1,84e-3, 0,64 a, längste Spule 23,4 a).

Quelle: `sim/rohdaten/coilstellaration/results/eval-part-0.parquet`, rein lesend, Skript nicht im Repo. Zahlen aus dem Skript.

## Schritt 1: Datensatz und Spalten

- Zeilen gesamt: **13299** (eine Zeile je Spulensatz, Spalte `desc_coilset_id` eindeutig bis auf fehlende Werte). Zeilen mit DESC-Metriken: **8058**. Mit REGCOIL-Metriken: **8860**.
- Die Kontrollzahl 8058 entspricht exakt den Zeilen mit DESC-Metriken. Die Kontrolle bezieht sich daher auf die DESC-Spalten.
- Einheiten: Alle Laengen-, Abstands- und Krümmungsspalten mit `normalized_` sind auf den kleinen Plasmaradius a bezogen. Geprueft: `normalized = Roh-Wert / minor_radius` ist in jeder Zeile exakt erfuellt (Verhaeltnis 1,0).
- Biegeradius/a wird aus der maximalen normierten Krümmung gerechnet: `Biegeradius/a = 1 / normalized_coil_curvatures/max` (Gleichung `kappa_max*a` geprueft, Verhaeltnis 1,0).
- Kräfte: In der Datei gibt es **keine Kraft-Spalte** (kein Lorentz-/Stuetzkraft-Feld). Nur Stroeme (`coil_currents`) und Verknuepfungszahlen (`coil_linking_numbers`). Kräfte sind nicht auswertbar.
- Feldfehler: `normalized_field_error` (min/mean/max/std). Unklar bleibt, ob dies das Verhaeltnis B·n/|B| ist, das im Bericht als "Bn" gemeint ist. Gezaehlt wird mit dem Maximum (`max`) ueber die Oberflaeche.
- Spulenzahl: `n_coils_per_half_period` (pro Halbperiode, nicht Gesamtzahl). Ob die Gesamtzahl daraus folgt, ist im Schema nicht belegt, daher nicht umgerechnet.

Spalten fuer die Auswertung (Name -> Bedeutung):

| Groesse | Spalte(n) | Hinweis |
|---|---|---|
| Feldfehler | `desc_metrics/normalized_field_error/{min,mean,max,std}`, `regcoil_metrics/normalized_field_error/{min,mean,max,std}` | unbekannt ob Bn-Definition; max verwendet |
| kleinster Biegeradius | abgeleitet: `1/desc_metrics/normalized_coil_curvatures/max` | normiert auf a |
| max. Krümmung | `desc_metrics/normalized_coil_curvatures/max`, `desc_metrics/coil_curvatures/max` (absolut), `regcoil_metrics/normalized_coil_curvatures/max` | normiert auf a |
| Spulenzahl | `reqs/n_coils_per_half_period`, `desc_metrics/n_coils_per_half_period`, `regcoil_metrics/n_coils_per_half_period` | pro Halbperiode |
| Spule-Spule-Abstand | `desc_metrics/normalized_coil_to_coil_min_distances/min`, `regcoil_metrics/normalized_coil_to_coil_min_distances/min` | minimaler Abstand, auf a |
| Spule-Plasma-Abstand | `desc_metrics/normalized_coil_to_plasma_min_distances/min`, `regcoil_metrics/normalized_coil_to_plasma_min_distances/min` | minimaler Abstand, auf a |
| Spulenlaenge | `desc_metrics/normalized_coil_lengths/{mean,max}`, `regcoil_metrics/normalized_coil_lengths/mean` | auf a |
| Kräfte | keine Spalte vorhanden | nicht auswertbar |

## Schritt 2: Anzahl Saetze (Bn-Schwelle x Biegeradius/a)

Bedingung: `fe_max < Schwelle` und `Biegeradius/a >= Schwelle`. Basis: DESC-Saetze (N = 8058).

| Bn < | Biegeradius >= 0,3 a | >= 0,5 a | >= 0,7 a | >= 1,0 a |
|---|---|---|---|---|
| 3e-03 | 3 | 0 | 0 | 0 |
| 5e-03 | 36 | 2 | 0 | 0 |
| 1e-02 | 293 | 43 | 0 | 0 |

Gegenprobe mit REGCOIL-Feldfehler (N = 8860):

| Bn < | >= 0,3 a | >= 0,5 a | >= 0,7 a | >= 1,0 a |
|---|---|---|---|---|
| 3e-03 | 0 | 0 | 0 | 0 |
| 5e-03 | 0 | 0 | 0 | 0 |
| 1e-02 | 0 | 0 | 0 | 0 |

Kontrolle (fruehere Angabe: keiner mit Bn < 3e-3 und Biegeradius >= 0,7 a): Zaehlung hier = **0**. Stimmt ueberein.

Maximaler Biegeradius/a im Datensatz (DESC): **0.9267**. Minimaler normierter Krümmungswert: **1.0791**.

## Schritt 3: Pareto-Front (kleiner Feldfehler, grosser Biegeradius)

Pareto-Front (DESC, nicht dominiert): **10** Saetze. Die Front hat weniger als 20 Mitglieder, daher werden alle ausgegeben (nach aufsteigendem Feldfehler). Die Angabe 20 aus der Aufgabe kann nicht erfuellt werden. Spalten: alle Groessen aus Schritt 1, auf a normiert.

| # | id (desc_coilset_id) | Spulen/Halbperiode (reqs / desc / regcoil) | Bn max (DESC) | Bn min | Bn mean | Bn std | Bn max (REGCOIL) | Bn mean (REGCOIL) | Biegeradius/a | kappa_max*a (DESC) | kappa_max*a abs (DESC) | kappa_max*a (REGCOIL) | Spule-Spule min/a (DESC) | Spule-Spule min/a (REGCOIL) | Spule-Plasma min/a (DESC) | Spule-Plasma min/a (REGCOIL) | Laenge mean/a (DESC) | Laenge max/a (DESC) | Laenge mean/a (REGCOIL) | Strom mean (DESC) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | D4DGEa8PkefxmMXbE8kKcY6 | 7 / 7 / 7 | 2.700e-03 | 2.035e-08 | 2.780e-04 | 2.846e-04 | 0.081981 | 0.022514 | 0.4659 | 2.1462 | 20.9243 | 1.6769 | 0.4025 | 0.4630 | 0.8487 | 0.9432 | 17.6654 | 21.8865 | 15.0111 | 129001.0591 |
| 2 | DSxxrQzcJphinWcwYFuk7Vm | 6 / 6 / 6 | 3.573e-03 | 5.069e-08 | 7.666e-04 | 6.301e-04 | 0.161801 | 0.031109 | 0.5891 | 1.6974 | 16.3672 | 1.8589 | 0.5880 | 0.6900 | 0.9806 | 0.9304 | 31.0457 | 41.2204 | 15.3001 | 297889.6867 |
| 3 | DRDP96EXYQJP8h5rrfC9wY9 | 5 / 5 / 5 | 5.765e-03 | 3.049e-09 | 8.581e-04 | 7.448e-04 | 0.111812 | 0.025381 | 0.6290 | 1.5897 | 14.5697 | 2.0495 | 0.5758 | 0.5890 | 0.7470 | 0.8543 | 21.7400 | 29.9963 | 15.6178 | 160566.0673 |
| 4 | Dk5gWvZ8naPnCu7mL5V6F9L | 4 / 4 / 4 | 8.438e-03 | 6.816e-08 | 1.253e-03 | 1.143e-03 | 0.140763 | 0.035961 | 0.6429 | 1.5553 | 15.6146 | 2.1058 | 0.5032 | 1.0534 | 1.0396 | 0.9684 | 33.6242 | 43.1490 | 15.6595 | 252733.4829 |
| 5 | Dea4YempJrbMtgbt6xa5mwT | 4 / 4 / 4 | 0.017206 | 5.422e-07 | 3.366e-03 | 3.012e-03 | 0.130554 | 0.032183 | 0.6534 | 1.5305 | 15.0950 | 2.4427 | 0.6788 | 0.7017 | 0.8210 | 0.8285 | 23.1361 | 29.0244 | 14.9204 | 178538.0641 |
| 6 | DMaaMjXHqewbrCX5ZEDdfeN | 6 / 6 / 6 | 0.022863 | 1.721e-07 | 4.340e-03 | 3.554e-03 | 0.091610 | 0.020132 | 0.7165 | 1.3957 | 14.0497 | 1.9789 | 0.6558 | 0.7394 | 0.9458 | 0.6570 | 17.2711 | 18.7473 | 13.4134 | 143823.8337 |
| 7 | DQPBorbeaXBmGwWopt9RnwX | 7 / 7 / 7 | 0.065587 | 9.627e-09 | 4.306e-03 | 5.179e-03 | 0.168389 | 0.044175 | 0.7255 | 1.3784 | 13.4258 | 2.7131 | 0.7173 | 0.7864 | 0.8830 | 0.5056 | 17.0022 | 20.0567 | 12.4244 | 162104.4419 |
| 8 | DSkCNduLUiWk4UtcyT3zXpQ | 5 / 5 / 5 | 0.066849 | 1.066e-07 | 8.780e-03 | 8.673e-03 | 0.274524 | 0.099342 | 0.7718 | 1.2956 | 12.5742 | 2.9502 | 0.9886 | 1.1586 | 0.7518 | 0.4779 | 17.4850 | 19.3341 | 11.4979 | 246709.2927 |
| 9 | D6YtXmPAbL2t2fdEmgd7GkR | 5 / 5 / 5 | 0.085942 | 9.250e-08 | 0.017289 | 0.014610 | 0.482944 | 0.178548 | 0.8487 | 1.1782 | 11.2295 | 6.0142 | 1.5778 | 1.9153 | 1.0861 | 0.5449 | 27.2058 | 36.0021 | 12.5456 | 650544.1548 |
| 10 | DC2gcPkEABVgmPY7FExWPqU | 4 / 4 / 4 | 0.148986 | 4.624e-06 | 0.033112 | 0.030282 | 0.508462 | 0.141746 | 0.9267 | 1.0791 | 8.6540 | 23.6887 | 1.3738 | 1.5909 | 1.0866 | 0.6132 | 33.2899 | 40.4868 | 11.6658 | 367582.0319 |

Hinweis: Kräfte sind nicht in der Datei. Die Ausgabe enthaelt die verfuegbaren Groessen.

## Schritt 4: Bekannte Saetze

| id | Spulen/Halbperiode (reqs) | Bn max (DESC) | Biegeradius/a | kappa_max*a (DESC) | erfuellte Bn-Schwellen | erfuellte Radius-Schwellen | auf Pareto-Front | Anzahl Saetze, die beide Kriterien dominieren (besser in Bn und Radius) |
|---|---|---|---|---|---|---|---|---|
| DRb36sGpjMdfrbfZz8vRqew | 6 | 0.005822 | 0.5677 | 1.7616 | <1e-02 | >=0.3, >=0.5 | nein | 2 |
| DnFiaMhotvUCEFyC7wg9opq | 5 | 0.004380 | 0.2418 | 4.1364 | <5e-03, <1e-02 | keine | nein | 33 |

