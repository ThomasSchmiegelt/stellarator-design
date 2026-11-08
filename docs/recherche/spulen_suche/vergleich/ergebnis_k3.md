# Ergebnis K3 halb: Festigkeit (FEM) und Kühlung, Stand 2026-11-08 14:17

Kennzeichnung: **[G]** gemessen (Ergebnisdatei, Pfade unten), **[C]** aus Code gelesen, **[S]** geschätzt, **[A]** Annahme.
Grundannahmen wie im Plan (`plan_fem_kuehlung.md`): a = 1,80 m, B0 = 6,5 T, Wickelpaket aus dem Maximalstrom 0,763 m, Stahlgrenze 500 MPa nur Annahme (B-045), Wertung am p99 der heißesten Spule ohne 0,5-m-Randzone. Erwartung vor der Rechnung: Ereignisprotokoll F-283 (13:33, nicht verändert).
Nicht gerechnet: DATJ5FC (Datensatzform, unverändert, nfp 4). Laufskript `sim/kette_k3/lauf_vergleich_fem.sh datj` liegt bereit.

## 0. Herkunft des Plasmas

| | K3 halb |
|---|---|
| Herkunft | **EIGENE Form**, halber Schritt aus der Datensatzform Do3Qy (`sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json`) |
| Spulensatz | `sim/kette_k3/stage2/satz_d100_n10_lr_s56`: 10 Basisspulen, 40 Spulen, nfp 2, Feldfehler Bn 2,1e-4 (Satzprüfung) [G] |
| Plasma für Fläche/Achse | freie Grenze `frei/wout/k_n48000.nc` (VMEC++, 48000 Schritte, fsqr 4,0e-14 laut Plan [G]) |
| Maßstab | L = 1,8 / a_u = 13,6084 (a_u = 0,13227), R0 = 13,6 m [G] |
| Plasmafläche / Volumen | 1693 m² (Netz 1693,3 m², simsopt 1693) / 869 m³ [G] |
| Vorsicht | Die Form hat eine sehr große vertikale Achsenschwankung (zaxis_cs[1] = -0,83 · R0; Rand bei phi = 45 Grad liegt bei Z = 8 bis 13 m) und Spiegelverhältnis 0,45 (B auf der Achse 4,4 bis 11,4 T) [G, aus wout/biot_savart]. Das ist die Form, kein Rechenfehler, aber es prägt die Ergebnisse unten. |

## 1. Werkzeuge (Regressionen)

| Schritt | Ergebnis |
|---|---|
| `stellarator/satz_nach_kopplung.py` (neu) | K3: 40 Spulen, 3 s [G]. Feld der Punktdarstellung (200 Punkte je Spule) gegen simsopt-Feld an 300 Randpunkten: mittlere Abweichung 9,9e-5, max 2,7e-4 (Polygon-Näherung) [G]. Kraft mit `kraft_analyse` auf dem umgewandelten Ordner gegen `kraefte.json` (Durchlauf 1, gleiche wout wie damals): Strom, Kraftintegral, f_max aller 10 Basisspulen identisch (Abweichung 0); mit der eigenen k_n48000-wout max 5,5e-4 [G]. Grenze der Aussage: Der Kraft-Test prüft die Spulenreihenfolge und die Kalibrierung, die Punktdarstellung prüft der Feldtest; FEM-Gesamtkraft siehe 2. |
| `kopplung.py`: Option `strom_je_spule` | Ohne Option unverändert: Regression am Punkt `qi_proxima_dpr/0012` (Parameter und wand_je_spule.json): Netz neu gebaut in 7 s, 249 766 Knoten und 216 160 Elemente, **max. Knotenabweichung gegen struktur.vtu 0,0**, wp und I identisch zu ergebnis.json [G] (billig, kein Elmer). Mit Option: Strom je Spule = |I_k / I_0| · I (Bezug wie `geometrie`), Wickelpaket und `J_op` (`schritt_package`, neuer Parameter `I_max`) aus dem Maximalstrom 22,57 MA. Einziger Eingriff ohne Option-Schalter: `struktur_netz` baut jetzt eine Stromliste statt einer Zuweisung, Werte ohne Option gleich (durch obigen Test belegt). |
| FEM-Kontrolle der Kraft | FEM-Lorentzkraft max. Nettokraft je Spule 1262,8 MN gegen `kraefte.json` (Spule 6) 1261 MN: 0,1 % [G]. Unabhängiger Code (hexmodell.lorentzdichte gegen kraft_analyse). |
| `stellarator/vergleich_kuehlung.py` (neu) | Monkeypatch von `kuehlung_segment.randflaeche` und `blei_kanal.umfang` auf wout und L; Test an der QA-Form: Randfläche identisch (Abweichung 0,0 m), Umfang bei phi = 90 Grad 16,657 m = Original, **alle b1-Werte aus `sim/blei/b1/auslegung.json` identisch** (694 Kanäle, 2,0794 m, 12,64 MW, v 0,1976 m/s, dp_mhd 31,28 kPa, dp 31,83 kPa) [G]. Zusätzlich QA-Fläche 1227,8 m² (waermebilanz: 1230 fest) [G]. Kontrolle DPr 0012: Fläche 1801,4 m² gegen geometrie.json 1801,5 m², Neutronenlast 1,356 gegen 1,36 MW/m² [G]. |

## 2. FEM K3 halb (Elmer, identische Wandparameter wie Punkt 0012)

Parameter: `--von qi_proxima_dpr/0012` (Wände x1,6 = wand_innen 0,32, wand_seite 0,8, t_min 0,88, t_zusatz 0,25; huelle_min_m 1,5; wand_adapt=1 mit Standardwerten Ziel 450, Faktor max 2, 3 Anpassungsrunden; Netz kruemmung/innenkontur/luecken/MUMPS) plus `strom_je_spule=1` [G, param.json]. Ablage `sim/kopplung/k3_halb/punkte/0000/`, Kopien in `sim/kette_k3/vergleich/ergebnis_k3_halb.json`, `wand_je_spule_k3_halb.json`.

Netz: 38 Stationen je Spule, 368 800 Elemente, 432 872 Knoten, 0 negative Elemente, 0 Durchdringungspunkte, Verbinder 316 von 460 [G].

**Hauptzahl (Endrunde 3, gleiches Verfahren wie bei 0012):** heißeste Spule (Nr. 13 = S4, 2. Kopie) p99 ohne Randzone **1294 MPa** [G], Stufe "über 800"; alle Spulen p99 660 MPa; Wickelpaket p99 933 MPa (Dehnung 0,93 % gegen 0,3 % zulässig [A]); u_max 284 mm; Gewicht 51 600 t (egal); Kraft max. je Spule 1263 MN.
**wand_adapt ist NICHT konvergiert** (Grund: Rundenzahl erreicht): heißeste Spule je Runde 1427 (Nr. 35), 701 (Nr. 13), 909 (Nr. 34), 1294 MPa (Nr. 13); mehrere Spulen am Faktorgrenzwert 2,0; die Last wandert zwischen Nachbarn. Der Wert hängt also an der Runde: 701 bis 1427 MPa [G]. Ich nenne 1294 MPa, weil es das Ergebnis des festgelegten Verfahrens ist; die Runde 1 (701 MPa) liegt knapp unter dem Erwartungsband, ist aber kein stabiler Zustand.

Zum Vergleich Punkt 0012 (DPr, 28 Spulen): heißeste Spule 446 MPa, u_max 41,6 mm, Kraft max. 792 MN, Hülle 1,51 m [G].

| K3 halb | Wert [G] |
|---|---|
| Hülle (Plasma bis Gehäuse) | 1,50 m (huelle_min_m greift), Abschirmung 1,40 m, package_min 1,0 m erfüllt |
| Neutronenwandlast mittel/Spitze | 1,442 / 2,885 MW/m² (P_fus 3053 MW [A], Spitzenfaktor 2 [A]) |
| Kernheizung Wickelpaket, Fluenz | 24 W/m³, 2,0e17 n/cm² (Grenzen eingehalten) |
| Feld am Leiter, J_op | 20,1 T, 38,8 MA/m² (0012: 19,4 T, 38,8 MA/m²); Auslastung 0,36, Temperaturmarge 20,4 K |
| Spulenströme | 13,6 bis 22,6 MA je Spule (nicht gleich) |
| Rechenzeit | 4 Runden, je Runde 4 bis 6 min (Netz und Elmer; Elmer-Anteil der letzten Runde 85 s laut ergebnis.json); Gesamtlauf 13:56:10 bis 14:15:06 = 19 min, struktur_s 1134 s [G] |
| Speicher | **11 GB reichten nicht** (Elmer/MUMPS OOM um 13:40), **18 GB reichten nicht** (OOM 13:55, nachdem ein Wächter von mir den Lauf 7 Minuten eingefroren hatte, Elmer-RSS 17,9 GB), **24 GB reichten**: Scope-Spitze 19,7 GB (MemoryCurrent, enthält Cache), Log `speicher_k3.log` [G]. Die Plan-Schätzung 6 bis 12 GB [S] war falsch. Während des Laufs liefen nur die beiden Stage-2/frei-Rechnungen (je unter 1 GB tatsächlich). |

## 3. Kühlung K3 halb (1D-Modell, `vergleich_kuehlung.py`, Datei `kuehlung_k3_halb.json`)

| Kennzahl | K3 halb [G, Modell] |
|---|---|
| Fläche Plasma / Wand bei Offset 0,15 m | 1693 / 1814 m² |
| Neutronenwandlast mittel (0,8 P_fus / S) | 1,442 MW/m² (DPr 0012: 1,356) |
| Strahlungslast mittel ((1 - f_div) f_alpha P_fus / S, f_div 0,5) | 0,180 MW/m² = 0,36 x der Annahme q = 0,5 MW/m² der Segmentstudien |
| Umfang Wandquerschnitt (13 Winkel einer Feldperiode, Enden doppelt) | 11,2 bis 19,1 m, Mittel 15,5 m; R mittel 12,6 bis 14,1 m |
| Blei, toroidale Kanäle 20 x 20 mm, q = 0,5 [A], Standardannahme 6 Grad / 6 T | Kanäle 465 bis 796, v 0,31 m/s, dp_MHD Stahlwand 56 bis 73 kPa (Mittel 65), isolierte Wand 2,0 bis 2,6 kPa; QA bei phi 90: 31,3 kPa [G] |
| Blei, B quer aus den eigenen Spulen (Wandfläche, auf 6,5 T kalibriert, quer zur toroidalen Richtung) | |B| 4,4 bis 11,3 T (Mittel 6,9), B_quer rms 0,76 bis 10,1 T (Mittel 4,7), mittlerer Winkel 8 bis 63 Grad (Mittel 43); dp_MHD Stahlwand 106 bis 14 500 kPa (Mittel 4730), isoliert 3 bis 32 kPa (Mittel 17); Pumpleistung Stahlwand im Mittel 300 kW, isoliert 1,3 kW |

Deutung (vorsichtig): Bei dieser Form ist die Annahme "Feld fast toroidal, 6 Grad" nicht erfüllt, weil die Achse stark vertikal schwingt; toroidal geführte Kanäle laufen großenteils quer zum Feld. Die großen Druckverluste sind ein Modellwert für eine ungeeignete Kanalrichtung, nicht für die beste Kanalführung (Kanäle entlang der Feldlinie wurden nicht gerechnet). Der Absolutwert ist 1D, ohne Kehren, Verteiler, Korrosion, Neutronik; Stoffwerte ungeprüft [C]. Nur das Verhältnis zu DATJ5FC wird aussagekräftig, sobald dessen Satz gerechnet ist.

## 4. Vergleich mit der Erwartung F-283

| Erwartung (F-283, vor der Rechnung) | Messung |
|---|---|
| K3 halb p99 heißeste Spule 400 bis 900 MPa | **1294 MPa (Endrunde), Spanne der Runden 701 bis 1427**: über der Erwartung; nicht konvergiert |
| Hülle halten | 1,50 m erreicht [G] |
| Wandfläche 1707 m², Last 1,43 MW/m² | 1693 m² (freie Grenze; 1707 war Formkoeffizienten-Fläche), 1,442 MW/m² [G] |
| MHD-Druckverlust Blei DATJ5FC innerhalb +-30 % gleich | offen (DATJ5FC nicht gerechnet) |
| DATJ5FC 250 bis 600 MPa, niedriger als K3 | offen |

Deutung (Opus entscheidet): K3 liegt mit diesen Wänden über 500 MPa und auch über 800 MPa; die Wandanpassung (Faktor max 2) reicht nicht. Der Bruch der Erwartung passt zu den Kräften von Durchlauf 1 (größte Nettokraft je Spule 1263 MN gegen 792 MN bei 0012 [G]; Ursache nicht untersucht). Zu prüfen laut F-283: ob dickere Wände (Faktor über 2, Gewicht egal) reichen; das wurde nicht versucht.

## 5. Offen / Hinweise

- `lauf_vergleich_fem.sh datj` rechnet DATJ5FC n5 und n6 nacheinander mit denselben Parametern und `FEM_MEM=24G` (Vorgabe 11 GB reichte bei K3 nicht; n5 hat 40 Spulen wie K3, n6 48 Spulen, also eher mehr). Er wartet auf 16 GB frei. Voraussetzung: `satz_*/frei/wout/k_n48000.nc`, `pruefung_satz.json`, `boundary.json`.
- Beobachtet: Die Stage-2-Läufe DATJ5FC n5/n6 liefen um 13:45 in `k3_spulen.py` Zeile 130 mit `ValueError ... not in the subpath` (relative K3_FORM-Pfad bei `FORM.relative_to(ROOT)`); danach stehen Satzordner und `.fertig`-Dateien da. Ich habe die Datei nicht angefasst.
- Das Wächter-Einfrieren (13:47:33 bis 13:55:22) kostete 8 Minuten, ist im Speicherlog vermerkt und ohne Einfluss auf das Ergebnis des 24-GB-Laufs.
- Dateien: `stellarator/satz_nach_kopplung.py`, `stellarator/vergleich_kuehlung.py` (neu), `stellarator/kopplung.py` (Option), `sim/kette_k3/lauf_vergleich_fem.sh`, `sim/kette_k3/vergleich/` (Ergebnisse, Regressionstexte und -skripte, Logs). Nichts committet, nichts in Protokoll oder BEFUNDE.
