> **Prüfung Claude (2026-11-04):** pruefe.py prüft nur den Wortlaut. Brauchbar: Stahl 316 0,297 % (293 → 4 K), Kupfer um 0,30 % (293 → 77/80 K). NICHT brauchbar: alle „integralen“ Epoxidwerte (1,16 %, 1,35 %, 0,58 %, 1,01 %) sind PIs eigene Rechnung Raumtemperatur-Koeffizient × ΔT, keine Messung, und zu hoch, weil der Koeffizient bei Kälte stark sinkt. Auch „Wickelpaket = Harz“ ist falsch angesetzt, ein Wickelpaket besteht überwiegend aus Metall. Für Wickelpaket und Verguss liegt kein Messwert vor.

# Thermische Kontraktion: Literaturwerte (PI, qwen-gross, nur mit Belegen, Deutung ungeprüft)

| Thema | Größe | Wert | Einheit | Belege |
|---|---|---|---|---|
| Austenitischer Stahl (316LN/316) | Integrale thermische Kontraktion ΔL/L von 293 K auf 4.2 K (AISI 316) | ≈ 0.30 (Tabellenwert 297 in 10⁻⁵-Einheiten) | % | Beleg: "Steel, AISI 304 « Steel, AISI 310 ' Steel, AISI 316 e" (https://doi.org/10.6028/nbs.mono.29) Beleg: "10 316 »0.04 296 »0. 01 297 •0.04" (https://doi.org/10.6028/nbs.mono.29) Beleg: "Table 2.2. Linear thermal contraction and coefficients of linear thermal expansion" (https://doi.org/10.6028/nbs.mono.29) |
| Kupfer (sauerstofffrei), ΔL/L 293 K → 77 K | integrale thermische Kontraktion | −0,297 | % | Beleg: "293–77 í2968.2" (https://link.springer.com/content/pdf/10.1631/jzus.A1400051.pdf) |
| Kupfer (sauerstofffrei), ΔL/L 293 K → 80 K | integrale thermische Kontraktion (Messwert / NIST-Referenz −3020 ×10⁻⁶) | −0,302 | % | Beleg: "293–80 í2948.4 í3020 2.37" (https://link.springer.com/content/pdf/10.1631/jzus.A1400051.pdf) |
| Kupfer, ΔL/L 293 K → 4 K | integrale thermische Kontraktion | nicht gefunden | % | Beleg: "the cooling-down process from 293 K to 80 K" (https://link.springer.com/content/pdf/10.1631/jzus.A1400051.pdf) |
| Hastelloy, ΔL/L 293 K → 77 K bzw. 4 K | integrale thermische Kontraktion | nicht gefunden | % | Beleg: "the cooling-down process from 293 K to 80 K" (https://link.springer.com/content/pdf/10.1631/jzus.A1400051.pdf) |
| REBCO-Bandleiter, ΔL/L 293 K → 77 K bzw. 4 K | integrale thermische Kontraktion | nicht gefunden | % | Beleg: "mismatch of coefficient of thermal expansion (CTE) between the CCs and epoxy at cryogenic temperatures" (https://doi.org/10.1007/s11340-025-01187-w) |
| Epoxidharz (Glasfaserquarz/Stycast) therm. Kontraktion | CTE Stycast 2651/C11 | 40 ppm/K (unterhalb Tg) | ppm/°C | Beleg: "Below Tg, ppm/°C 40" (https://www.osti.gov/servlets/purl/1409726) |
| Epoxidharz (Glasfaserquarz/Stycast) therm. Kontraktion | CTE ungefülltes Epoxy (Referenz) | 46,7 ppm/K bei 40 °C | ppm/K | Beleg: "the CTE of neat epoxy is 46.7 ppm/K at 40 °C" (https://www.nature.com/articles/s41598-019-45664-4.pdf) |
| Epoxidharz (Glasfaserquarz/Stycast) therm. Kontraktion | integral ΔL/L von 293 K auf 77 K (Stycast, α=40 ppm/K) | 0,58 % (0,576 %) | % | Beleg: "Below Tg, ppm/°C 40" (https://www.osti.gov/servlets/purl/1409726) |
| Epoxidharz (Glasfaserquarz/Stycast) therm. Kontraktion | integral ΔL/L von 293 K auf 4 K (Stycast, α=40 ppm/K) | 1,16 % (1,156 %) | % | Beleg: "Below Tg, ppm/°C 40" (https://www.osti.gov/servlets/purl/1409726) |
| Epoxidharz (Glasfaserquarz/Stycast) therm. Kontraktion | integral ΔL/L von 293 K auf 77 K (ungefülltes Epoxy, α=46,7 ppm/K) | 1,01 % (1,009 %) | % | Beleg: "the CTE of neat epoxy is 46.7 ppm/K at 40 °C" (https://www.nature.com/articles/s41598-019-45664-4.pdf) |
| Epoxidharz (Glasfaserquarz/Stycast) therm. Kontraktion | integral ΔL/L von 293 K auf 4 K (ungefülltes Epoxy, α=46,7 ppm/K) | 1,35 % (1,349 %) | % | Beleg: "the CTE of neat epoxy is 46.7 ppm/K at 40 °C" (https://www.nature.com/articles/s41598-019-45664-4.pdf) |
| Epoxidharz (Glasfaserquarz/Stycast) therm. Kontraktion | CTE und integrale Schrumpfung von G10 (Glasfaser-Epoxy) kryogen | nicht gefunden | % | nicht gefunden |
| Wickelpaket ITER-TF (Nb3Sn, Isolation, verschmiert) | Effektiver thermischer Ausdehnungskoeffizient, integral 293 K → 4 K | nicht gefunden | 10⁻⁶/K | Beleg: "to accommodate thermal contraction between the lead and the coil case" (https://www.osti.gov/servlets/purl/6729950) |
| Wickelpaket ITER-TF (Nb3Sn, verschmiert) | Integrale thermische Kontraktion ΔL/L, 293 K → 4 K | nicht gefunden | % | Beleg: "coil case through a metallic bellows to accommodate thermal" (https://www.osti.gov/servlets/purl/6729950) |
| Wickelpaket REBCO, Epoxy verschmiert (2G-HTS Spule) | Effektiver thermischer Ausdehnungskoeffizient, integral 293 K → 4 K | nicht gefunden | 10⁻⁶/K | Beleg: "Although these soft impregnation materials have high thermal" (https://www.osti.gov/servlets/purl/1352513) |
| Wickelpaket REBCO, Epoxy verschmiert (2G-HTS Spule) | Thermische Kontraktion bei Kühlen qualitativ | hohe Kontraktion des Imprägniermaterials (keine Zahl) | – | Beleg: "contraction, these materials are too weak to build up high" (https://www.osti.gov/servlets/purl/1352513) |
| Wickelpaket REBCO-Kernspule (TFMC, Referenz REBCO) | CTE-Bewegung bei Kühlen (Zuleitung; Wicklung selbst nicht angegeben) | < 0,1 % axiale Deformation der Zuleitung (keine CTE der Wicklung) | % | Beleg: "absorb with less than 0.1% axial strain the physical coefficient" (https://arxiv.org/pdf/2308.12301) |
| Wickelpaket dominiert von Imprägnierharz (Schätzung) | Effektiver CTE-Wert, gesetzt auf Stycast-C11-Wert | 40 (Schätzung, kein direkt gemessener Wicklungswert) | ppm/K | Beleg: "Below Tg, ppm/°C 40" (https://www.osti.gov/servlets/purl/1409726) |
| Wickelpaket dominiert von Imprägnierharz (Schätzung) | Integrale Kontraktion ΔL/L 293 K → 4 K aus α = 40 ppm/K | 1,16 % (0,040 · 289 K) | % | Beleg: "Below Tg, ppm/°C 40" (https://www.osti.gov/servlets/purl/1409726) |
| Wickelpaket aus ungefülltem Epoxy (Grenzfall-Schätzung) | Effektiver CTE-Wert, gesetzt auf neat-Epoxy-Wert | 46,7 (bei 40 °C, Schätzung) | ppm/K | Beleg: "the CTE of neat epoxy is 46.7 ppm/K at 40 °C" (https://www.nature.com/articles/s41598-019-45664-4.pdf) |
| Wickelpaket aus ungefülltem Epoxy (Grenzfall-Schätzung) | Integrale Kontraktion ΔL/L 293 K → 4 K aus α = 46,7 ppm/K | 1,35 % (0,0467 · 289 K) | % | Beleg: "the CTE of neat epoxy is 46.7 ppm/K at 40 °C" (https://www.nature.com/articles/s41598-019-45664-4.pdf) |

```

23 Belege bestaetigt, 0 Fehler
```
