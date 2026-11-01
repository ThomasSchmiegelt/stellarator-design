# Gyroid-Wärmetauscher Wasser–Wasser: gemessene Kennzahlen (Schritt 2, Teil 3)

Quelle: S.-H. Oh, J. E. Kim, C. H. Jang, J. Kim, C. Y. Park, K. Park: Multifunctional gradations of TPMS architected heat
exchanger for enhancements in flow and heat exchange performances. Sci. Rep. 15 (2025) 19931, doi:10.1038/s41598-025-04940-2
(frei zugänglich). Versuch: Gyroid, Zelle 10 mm bzw. abgestuft 6–10 mm, Wand ~0,5 mm, gedruckt (PBF), Wasser gegen
Glykol-Wasser, Vergleich mit Korrelationen für Plattenwärmetauscher.

| Größe | Wert | Beleg |
|---|---|---|
| U gleichmäßige Zelle | 1651–2102 W/m²K | Beleg: "For the uniform cell design, U ranges from 1651 to 2102 W/m2 K" (https://www.nature.com/articles/s41598-025-04940-2.pdf) |
| U abgestufte Zelle | 1914–2488 W/m²K | Beleg: "ranging from 1914 to 2488 W/m2 K" (https://www.nature.com/articles/s41598-025-04940-2.pdf) |
| übliche Wasser-Wasser-Tauscher | 850–1700 W/m²K | Beleg: "U values in the range of 850–1700 W/m2K57" (https://www.nature.com/articles/s41598-025-04940-2.pdf) |
| Nu gegen Platte | beide Gyroid-Varianten höher | Beleg: "both TPMS HX designs consistently outperform plate-type HXs58" (https://www.nature.com/articles/s41598-025-04940-2.pdf) |
| j/f^(1/3) gleichmäßig gegen Platte | etwas SCHLECHTER | Beleg: "exhibit slightly lower j/f1/3 ratios than conventional plate-type HXs" (https://www.nature.com/articles/s41598-025-04940-2.pdf) |
| j/f^(1/3) abgestuft | ~28 % besser | Beleg: "outperforming other HXs by approximately 28%" (https://www.nature.com/articles/s41598-025-04940-2.pdf) |
| Wanddicke gedruckt | 0,53 mm | Beleg: "0.533 ± 0.05 mm" (https://www.nature.com/articles/s41598-025-04940-2.pdf) |

**Bedeutung für H1** (Gyroid liefert bei gleicher Pumpleistung mehr Netto-Strom):
- j/f^(1/3) misst Wärmeübergang je Pumpaufwand. Ein **gleichmäßiger** Gyroid ist danach etwas schlechter als eine Platte, erst der **abgestufte** ist besser. H1 gilt also nicht von selbst, die Gestaltung entscheidet.
- Die Messung ist klein (98 × 60 × 44 mm, wenige l/min). Ob sie sich auf einen 305-MW-Vorwärmer übertragen lässt, ist offen.
- Die Arbeit gibt **keine Formeln** für Nu(Re) und f(Re) an, nur Kurven. Für die Auslegung fehlen noch Korrelationen.

**Nicht abrufbar** (Verlag 403 oder Bot-Schutz, nicht umgangen). Diese Volltexte bitte von Hand herunterladen:
1. Gyroid/Diamond-Korrelationen, Int. J. Heat Mass Transfer 2024, doi:10.1016/j.ijheatmasstransfer.2024.126599 (frei, auch auf HAL: cea-04896410)
2. Synthese der TPMS-Korrelationen, Results in Engineering 2026, doi:10.1016/j.rineng.2026.109402 (frei)
3. TPMS-Tauscher für Niedertemperatur-Abwärme, Appl. Therm. Eng. 2022, ScienceDirect S1359431122004033 (frei)
4. TPMS und Nodal Surfaces: Wärmeübergang und Druckverlust, Appl. Therm. Eng. 2022, ScienceDirect S135943112200148X (frei)

## Korrelationen für turbulente Strömung (Übersichtsarbeit 2026)

Quelle: M. Al-Safadi, F. Ejaz, S. Z. Shuja, S. M. Zubair: Quantitative synthesis and correlations of heat transfer and
friction factor in triply periodic minimal surface (TPMS) structures. Results in Engineering 29 (2026) 109402,
doi:10.1016/j.rineng.2026.109402. Die Werte stehen in Tabelle 9. Es sind Anpassungen der Autoren an digitalisierte
Daten aus den Originalarbeiten ("A: Fitted correlations"), also Werte aus zweiter Hand. Volltext vom Nutzer
heruntergeladen, Zitate gegen den PDF-Text geprüft.

Darstellung: Nu = C Re^a Pr^b, f = C_f Re^n.

| Original | Fluid | Korrelation | Gültig | Beleg |
|---|---|---|---|---|
| Li, Li, Yu 2022 (Appl. Therm. Eng. 217, 119198), wassergekühlter TPMS-Tauscher | Wasser | f = 4,106 Re^−0,203; Nu = 0,02 Re^1,02 Pr^0,33 | 10 000 < Re < 30 000 | Beleg: "f = 4.106Re − 0.203" (https://doi.org/10.1016/j.rineng.2026.109402) Beleg: "Nu = 0.02Re 1.02 Pr 0.33" (https://doi.org/10.1016/j.rineng.2026.109402) Beleg: "Heat transfer enhancement of water-cooled" (https://doi.org/10.1016/j.rineng.2026.109402) |
| Liang et al. (IJHMT) | k. A. | f = 0,22 Re^−0,312; Nu = 0,143 Re^0,406 Pr^0,33 | 2300 < Re < 8900 | Beleg: "f = 0.22Re − 0.312" (https://doi.org/10.1016/j.rineng.2026.109402) Beleg: "Nu = 0.143Re 0.406 Pr 0.33" (https://doi.org/10.1016/j.rineng.2026.109402) |
| Li, Yu, Yu 2020, sCO2-Tauscher, heiße Seite | sCO2 | f = 0,22 Re^−0,048; Nu = 0,18 Re^0,717 Pr^0,33 | 2300 < Re < 53 000 | Beleg: "f = 0.22Re − 0.048" (https://doi.org/10.1016/j.rineng.2026.109402) Beleg: "Nu = 0.18Re 0.717 Pr 0.33" (https://doi.org/10.1016/j.rineng.2026.109402) |

**Bewertung:**
- **Streuung:** Die Korrelationen gehen weit auseinander. Bei Re = 10 000 und Pr = 1 ergibt Li 2022 Nu ≈ 240, Liang Nu ≈ 6, Li 2020 Nu ≈ 133. Das ist eine Unsicherheit um eine Größenordnung. Für die Auslegung (Schritt 4) brauchen wir deshalb eine Bandbreite, keinen Einzelwert.
- **Definitionen:** Die Übersicht nennt selbst uneinheitliche Definitionen der hydraulischen Länge als Hauptgrund für unvergleichbare Daten.
- **Fehlende Quelle:** Renon & Jeanningros 2024 (Gyroid und Diamond, 2961 < Re < 18 254, laut Kurzfassung unabhängig von d_h und Porosität) ist kostenpflichtig. Auf HAL (cea-04896410) ist sie frei, aber für automatischen Abruf gesperrt. Sie passt am besten zu unserem Bereich, und der Nutzer könnte sie im Browser laden.

## Hauptquelle für die Auslegung: Renon & Jeanningros (CEA) 2024

C. Renon, X. Jeanningros: A numerical investigation of heat transfer and pressure drop correlations in Gyroid and
Diamond TPMS-based heat exchanger channels. Int. J. Heat Mass Transfer (2024) 126599,
doi:10.1016/j.ijheatmasstransfer.2024.126599. Das Manuskript steht frei auf HAL (cea-04896410), der Nutzer hat es im
Browser geladen. Es ist eine CFD-Arbeit mit 40 Fällen und voll ausgebildeter Strömung. Die Werte gelten für die Diamond-
Struktur, für Gyroid nur eingeschränkt.

| Größe | Wert | Beleg |
|---|---|---|
| Gültigkeit | 2961 < Re < 18 254; 3 < Pr < 5; 0,79 < μ/μ_w < 1,39 | Beleg: "Re < 18254; 3 < Pr < 5), wall boundary conditions (0.79 < μ/μw < 1.39)" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) |
| Wärmeübergang (Gl. 14) | Nu = 0,2644 Re^0,69 Pr^(1/3) (μ/μ_w)^0,20 | Beleg: "Nu=f(Re,Pr1/3,μ/μw) was sought" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) Beleg: "0.2644" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) Beleg: "average relative error of 1.60%" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) |
| Gilt auch für Gyroid | „in geringerem Maß“ | Beleg: "this
equation also appears to be applicable to a lesser extent to TPMS G geometries" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) |
| Reibung, Fanning (Gl. 18, Diamond) | f = 1,850 Re^−0,17 | Beleg: "1.850" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) Beleg: "average relative error of 2.42%" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) |
| Gyroid gegen Diamond | f um 12,3–16,7 % höher | Beleg: "of 12.3% to 16.7% for coefficient f on the configurations studied is observed" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) |
| Folgerung der Autoren | Diamond für Tauscher besser | Beleg: "TPMS D therefore seems preferable for" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) |
| Hydraulischer Durchmesser | d_h = 4 V_f / A (Fluidvolumen / benetzte Fläche) | Beleg: "The hydraulic diameter is defined" (https://doi.org/10.1016/j.ijheatmasstransfer.2024.126599) |

**Abgleich mit der Übersicht 2026:**
- Bei Re = 10 000 und Pr = 1 ergibt Renon Nu ≈ 152. Das liegt zwischen Li 2020 (133) und Li 2022 (240). Liang (≈ 6) fällt heraus; vermutlich ist Re dort anders definiert.
- Für die Auslegung nehmen wir **Renon als Mittelwert**. Die Bandbreite reicht von Li 2020 bis Li 2022. Reibung beim Gyroid: Renon f × 1,15.
- Neuer Befund: **Diamond statt Gyroid**. Bei gleichem Wärmeübergang hat die Diamond-Struktur 12–17 % weniger Reibung. Für dein Kriterium Effizienz ist sie damit die bessere TPMS-Bauart, und in PicoGK lässt sie sich genauso erzeugen.
Prüfung: 23 Belege bestätigt, 0 Fehler (gegen die lokal heruntergeladenen Volltexte; als Quelle steht die DOI).

## Rechte und Zitierweise

Übernommen sind nur Zahlen, Formeln und kurze wörtliche Belegstellen (Zitat nach § 51 UrhG, Quelle nach § 63 UrhG,
unverändert). Abbildungen und Tabellen sind nicht übernommen. Die Volltexte liegen nicht im Repository.

| Quelle | Lizenz (aus dem Volltext geprüft) |
|---|---|
| Oh et al., Sci. Rep. 15 (2025) 19931 | CC BY 4.0 |
| Al-Safadi et al., Results Eng. 29 (2026) 109402 | CC BY-NC 4.0 |
| Renon & Jeanningros 2024, Manuskript auf HAL (cea-04896410) | CC BY-NC-ND 4.0 (HAL-Fassung); Verlagsfassung Int. J. Heat Mass Transfer, Elsevier |
| Li, Li, Yu 2022; Li, Yu, Yu 2020; Liang et al. | nur aus zweiter Hand über Al-Safadi et al. 2026, Tabelle 9, zitiert |
