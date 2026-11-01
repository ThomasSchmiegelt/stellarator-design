# Speisewasser und Turbine eines Druckwasserreaktors (Schritt 2, Teil 2)

Bezugsanlage ist der **EPR**. Die deutsche Wikipedia nennt dafür eine vollständige Tabelle der Turbinendaten (von
Claude gefunden). PI hat die Zahl der Vorwärmstufen und die Bauart beigetragen (zeilen/05.md) sowie den Frischdampfdruck
von EPR und WWER-1000 (zeilen/04.md, WWER-Spalte von Claude nachgeprüft).

| Größe | Wert | Beleg |
|---|---|---|
| Speisewassertemperatur | 230 °C | Beleg: "Speisewassertemperatur | 230 °C" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| Dampftemperatur | 293 °C | Beleg: "Heißdampftemperatur | 293 °C" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| Dampfdruck | 78 bar | Beleg: "Dampfdruck | 78 bar" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| Dampfmassenstrom | 2443 kg/s | Beleg: "Dampfmassenstrom | 2443 kg/s" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| Druck vor der Hochdruckturbine | 75,5 bar | Beleg: "Dampfdruck Hochdruckturbine | 75,5 bar" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| Kondensatordruck | 24,7 mbar | Beleg: "Kondensatordruck | 24,7 mbar" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| Vorwärmstufen | 7 | Beleg: "Speisewasservorwärmer | 7 Stufen" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| elektrische Leistung | 1793 MW | Beleg: "Effektive Leistung | 1793 MW el" (https://de.wikipedia.org/wiki/EPR_%28Kernkraftwerk%29) |
| Bauart geschlossener Vorwärmer | Rohrbündel (Mantel-Rohr) | Beleg: "Closed feedwater heaters are typically shell and tube heat exchangers" (https://en.wikipedia.org/wiki/Feedwater_heater) |

**Einordnung:**
- **Frischdampf:** 293 °C bei 78 bar liegt praktisch auf der Sättigungslinie (CoolProp: 293,2 °C). Der Frischdampf ist also Sattdampf, wie bei Druckwasserreaktoren üblich.
- **Kondensator:** 24,7 mbar (Sättigung ≈ 21 °C) gilt für einen Standort mit kaltem Kühlwasser. Für einen Flussstandort rechnen wir zum Vergleich mit 50 mbar.
- **Vorwärmkette:** Sieben Stufen heizen das Speisewasser von der Kondensattemperatur auf 230 °C. Die Divertor-Targets (130→136 °C) können also nur den unteren Teil davon ersetzen, die Niederdruck-Vorwärmer.

## Gegenprobe englische Wikipedia (2026-10-31)

Quelle: https://en.wikipedia.org/wiki/EPR_(nuclear_reactor). Die englische Seite nennt weniger Kreislaufdaten als die deutsche Tabelle:

- "Thermal output, MW": 4590 (EPR-1750)
- "Efficiency, net %": 36
- "Pressure in the turbine inlet": "77.2 bars (7,720 kPa; 1,120 psi)"

77,2 bar am Turbineneintritt passt zwischen 78 bar Frischdampf und 75,5 bar am Hochdruckteil (deutsche Tabelle). Massenstrom, Speisewassertemperatur, Kondensatordruck und Vorwärmstufen stehen nur in der deutschen Fassung.

## Rechte und Zitierweise

Wikipedia-Texte stehen unter CC BY-SA 4.0. Übernommen sind nur Zahlenwerte (Tatsachen) und kurze wörtliche
Belegstellen mit Link und Abrufdatum 2026-10-31; es wurde kein Artikeltext weiterverwendet.
