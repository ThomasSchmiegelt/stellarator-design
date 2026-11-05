# Weg A und B: Datensatz filtern, dann lokale Suche mit VMEC++ (Opus-Agent, 2026-11-04)

Auftrag aus `paarvergleich_plasma.md` (F-240): eine Plasmaform finden, die bei der offiziellen ConStellaration-Wertung mehr als 0 Punkte bekommt, also alle Nebenbedingungen erfüllt, und das mit VMEC++ bestätigt. Erst Weg A (Datensatz filtern), dann Weg B (kleine Schritte mit VMEC++). Nichts hochgeladen, nichts gesendet, nichts committet.

Skript: `stellarator/qi_filter_suche.py`. Lauf: `sim/qi_flaeche/suche_lokal/lauf.sh`. Ergebnis Schritt A: `sim/qi_flaeche/filter138.json`. Ergebnisse Schritt B: eine Datei je Rechnung in `sim/qi_flaeche/suche_lokal/s<k>/NNN.json`, Tabelle `opus_filter_suche_tabelle.md`.

## Lesehilfe für Nicht-Physiker

- **Plasmaform (Rand):** die Form der äußersten Magnetfeldfläche, also die Form des „Schlauchs“, in dem das heiße Gas eingeschlossen ist. Sie wird durch rund 90 Zahlen beschrieben (Fourier-Koeffizienten). Jede Zahl beschreibt, wie stark eine bestimmte Beule oder Verdrehung ausgeprägt ist.
- **VMEC++:** das Rechenprogramm, das zu einer Randform das Magnetfeld im Inneren ausrechnet. Danach kann man die Kennzahlen ablesen. Eine Form braucht hier 70 bis 155 Sekunden.
- **QI (quasi-isodynamisch):** Wie gut das Feld schnelle Teilchen festhält. Kleiner ist besser, 0 wäre ideal. Die Wertung verlangt sehr kleine Werte (siehe unten).
- **iota (Rotationstransformation):** wie stark die Feldlinien sich um den Schlauch winden. Ist der Wert zu klein, schließt das Feld schlecht ein.
- **Spiegelverhältnis:** wie stark die Feldstärke entlang einer Feldlinie schwankt. Starke Schwankung macht Spulen schwer baubar.
- **Vakuummulde:** ein Maß dafür, ob das Plasma gegen einfache Störungen stabil ist. Sie muss mindestens 0 sein.
- **Flusskompression:** wie eng sich die Feldlinien an ungünstig gekrümmten Stellen zusammendrängen. Das dient als Ersatzmaß für Turbulenz.
- **Normierte Verletzung:** wie weit eine Kennzahl über ihrer Grenze liegt, geteilt durch die Grenze. 0,21 heißt 21 % zu weit. Das Paket lässt höchstens 1 % zu.
- **Standardabweichung (sd):** die typische Streuung einer Formzahl über den ganzen Datensatz. „0,3 sd“ ist ein kleiner Schritt im Vergleich zur Vielfalt der Daten.

## 1 Echte Schwellen (aus dem installierten Paket, `problems.py`)

| Aufgabe | Nebenbedingungen (normierte Verletzung ≤ 0,01) | Wertung |
|---|---|---|
| 2 einfach baubar (SimpleToBuildQIStellarator) | A ≤ 10, \|iota Rand/nfp\| ≥ 0,25, log10 QI ≤ −4 (QI ≤ 0,00011 mit Toleranz), Spiegel Rand ≤ 0,2, Elongation ≤ 5 | Gradientenlänge/20 |
| 3 MHD-stabil (MHDStableQIStellarator) | \|iota Rand/nfp\| ≥ 0,25, log10 QI ≤ −3,5 (QI ≤ 0,00034 mit Toleranz), Spiegel Rand ≤ 0,25, Flusskompression ≤ 0,9, Vakuummulde ≥ 0 (normiert mit 0,1, also ≥ −0,001) | Hypervolumen; eine zulässige Form gibt (1+L)·(20−A) > 0 |

**Abweichungen von der Vorgabe (gemessen am Quelltext):**
1. Es gibt **keine** Aufgabe mit QI ≤ 0,001. Aufgabe 3 verlangt QI ≤ 0,00032 (mit Toleranz 0,00034), Aufgabe 2 QI ≤ 0,0001.
2. Die sechs Bedingungen der Vorgabe mischen zwei Aufgaben: Elongation ≤ 5 und Spiegel ≤ 0,2 gehören nur zu Aufgabe 2, Vakuummulde und Flusskompression nur zu Aufgabe 3. Aufgabe 3 hat keine Elongationsgrenze.
3. iota wird als **Betrag** gewertet. Die 138 der Vorgabe entstehen mit iota *mit Vorzeichen*. Mit Betrag sind es 145, weil 7 Formen negatives iota haben.
4. Zulässig heißt: jede normierte Verletzung höchstens 0,01, nicht exakt 0.

## 2 Schritt A: Datensatz gefiltert (gemessen, ohne VMEC++)

182 222 Zeilen, davon 158 685 mit QI.

| Menge | ohne QI-Bedingung | mit QI-Bedingung | QI Minimum | QI Median |
|---|---|---|---|---|
| Regel der Vorgabe (iota mit Vorzeichen) | **138** | 0 (QI ≤ 0,001) | **0,00178** | **0,0237** |
| Regel der Vorgabe, iota als Betrag | 145 | – | – | – |
| Aufgabe 3 amtlich | 166 | **0** | 0,00178 | 0,0232 |
| Aufgabe 2 amtlich | 786 | **0** | 0,0046 | 0,0250 |

Beste der 138: `D8ZNt2qFQLQQxMVitWaeCid` (nfp 2, QI 0,00178). Dahinter folgt ein Sprung: Platz 2 bis 5 haben QI 0,0066 bis 0,0082.

**Knappste Bedingung unter den 138** (Rest = Abstand zur Grenze, normiert): Beim kleinsten Rest ist iota am knappsten (0,0002), dann das Spiegelverhältnis (0,0005), die Vakuummulde (0,0023), die Flusskompression (0,013) und die Elongation (0,015). Im Median sind Spiegelverhältnis und Vakuummulde am knappsten (je 0,11), die Elongation hat am meisten Luft (0,30). Bindend bleibt QI: Selbst die beste Form verletzt log10 QI um 21 %, erlaubt ist 1 %. Um zulässig zu werden, muss QI um den Faktor 5 sinken, bei Platz 2 bis 5 um den Faktor 20.

## 3 Schritt B: lokale Suche mit VMEC++ (läuft)

**Abweichung vom Plan bei der Wahl der Startformen:** Platz 2 bis 5 der 138 liegen beim Faktor 20 über der QI-Grenze. Nach der amtlichen Verletzungssumme liegen neun andere Datenformen näher an der Zulässigkeit. Gestartet wird deshalb von den 5 Datenformen mit der kleinsten Summe f der quadrierten positiven Verletzungen (Aufgabe 3). Platz 1 ist dieselbe Form wie in der 138er-Liste.

| k | Startform | nfp | QI (Datensatz) | f | größte Verletzungen |
|---|---|---|---|---|---|
| 0 | D8ZNt2qFQLQQxMVitWaeCid | 2 | 0,00178 | 0,046 | nur QI (0,21) |
| 1 | DkPMhhHs5nka5Zi6Jw5fUph | 3 | 0,00163 | 0,066 | QI 0,20, Spiegel 0,11, Vakuummulde 0,11 |
| 2 | DLQih3TFHPwzHDH6FsQBcrU | 3 | 0,00168 | 0,086 | QI 0,21, Flusskompr. 0,16, Spiegel 0,11 |
| 3 | D3uBG7mHc3wjEEHKqKJY9FA | 3 | 0,00105 | 0,091 | Vakuummulde 0,25, QI 0,15 |
| 4 | D4m6LXvwuxVnb3vNDrJheyY | 3 | 0,00296 | 0,091 | QI 0,28, iota 0,12 |

**Verfahren:** Die Zielfunktion ist f, die Summe der Quadrate der positiven normierten Verletzungen von Aufgabe 3. Die Normierung stammt aus dem Paket selbst (`_normalized_constraint_violations`). Das Ziel ist erreicht, wenn `is_feasible` gilt; dann ist die Wertung > 0. Aufgabe 2 wird bei jeder Rechnung mitgewertet.

Suchverfahren ist eine (1+1)-Evolutionsstrategie. Sie zieht eine zufällige Richtung in den 9 freien wichtigsten Formzahlen (Rangliste aus B-048/B-050; Feldperioden und die gesperrten m = 0-Koeffizienten bleiben fest). Bei einem Fehlschlag probiert sie zuerst die Gegenrichtung. Nach einem Erfolg geht sie in derselben Richtung weiter und vergrößert den Schritt um den Faktor 1,5. Nach zwei Fehlschlägen verkleinert sie den Schritt um den Faktor 0,6. Die Schrittlänge liegt zwischen 0,02 und 0,3 sd und beginnt bei 0,1 sd. Jede Startform bekommt höchstens 40 Rechnungen. Die Suche hält an, sobald eine Form zulässig ist. Eine Form, die VMEC++ nicht rechnen kann, zählt als Fehlschlag.

**Rechentechnik:** Es laufen 4 Startformen gleichzeitig, jede in einem eigenen Speicherbereich mit höchstens 6 GB, die fünfte danach. Jede VMEC++-Rechnung läuft als eigener Kindprozess. Die Rechenzeit ist nur über die CPU-Zeit des Prozesses begrenzt (1 h), nicht über die Uhr. Deshalb geht beim Anhalten nichts kaputt. Jede Rechnung wird sofort als Datei gespeichert. Ein Neustart rechnet die Folge nach und überspringt alles Fertige; die Folge ist durch einen festen Zufallsstartwert bestimmt.

**Erwartung (vor dem Lauf, Ereignisprotokoll F-241):**
- Nutzer: Das beste QI der 138 liegt bei 0,002 bis 0,01. Gemessen wurde 0,00178, also knapp besser. Höchstens 1 von 5 Startformen erreicht QI ≤ 0,001 bei erfüllten Nebenbedingungen.
- KI: Gegen die echte Grenze (QI ≤ 0,00034) wird in 40 Rechnungen keine Startform zulässig (0 von 5). f sinkt bei der besten Startform um 30 bis 60 %, das beste QI liegt dann bei 0,0007 bis 0,0012. 10 bis 25 % der Versuchsformen rechnet VMEC++ nicht.
- Deutung vorab: 0 von 5 hieße, dass Zufallsschritte zu langsam sind und Weg D (Gradientenverfahren mit der offiziellen Zielfunktion) nötig wird. 1 von 5 oder mehr ergäbe eine Absprungbasis mit Wertung > 0.

## 4 Ergebnis Schritt B

Noch offen. Die Auswertung folgt nach dem Ende des Laufs (`qi_filter_suche auswertung`), danach der Vergleich mit der Erwartung.

Zwischenstand 20:38 (gemessen): Die ersten drei Startformen geben mit VMEC++ dieselben Kennzahlen wie der Datensatz, auf etwa 7 Stellen genau (QI 0,0017814 / 0,0016254 / 0,0016806). Eine Rechnung dauert bei 4 gleichzeitigen Läufen 160 bis 210 s, die Speicherspitze liegt bei 2,8 GB je Lauf. Geschätzte Gesamtdauer: 3 bis 4 Stunden (Starts 0 bis 3 je etwa 2 h, Start 4 danach), kürzer, wenn eine Form vorher zulässig wird.

## 5 Gemessen und angenommen getrennt

Gemessen: Schwellen aus dem Quelltext, alle Zählungen und QI-Werte aus Schritt A (Datensatzwerte, die mit derselben Einstellung wie die Wertung berechnet sind, B-050).
Angenommen: dass die 9 vom Surrogat gewählten Formzahlen auch für die Nebenbedingungen die wirksamen sind (für QI global gemessen, für diese Startformen nicht geprüft); dass 40 Rechnungen je Startform für eine Aussage reichen.
