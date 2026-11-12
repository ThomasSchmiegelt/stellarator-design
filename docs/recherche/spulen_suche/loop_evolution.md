# Evolution des Ralph-Loops vom 9.11.2026 (Begleittext)

Lokales Modell PI (qwen-gross über ollama) wählt je Runde eine Datensatzform (ConStellaration, unverändert, QI ≤ 5e-4).
Eine feste Bewertung rechnet dazu eigene Spulen (Ordnung 4, Biegeradius ≥ 2·d, Montagestrafe, etwa 40 Spulen). Endstand: 100 Formen (7:37–21:12, Ende per STOP), 97 gültige PI-Wahlen, 2 Ersatzwahlen, Prüfstein.
Skript: `stellarator/loop_evolution.py bild|video`.

## Bild `loop_evolution.png`, Lesehilfe
- **(a)** Jeder Punkt ist eine gewählte Form. Nach oben ist der Feldfehler ihrer Spulen aufgetragen (kleiner = einfachere Spulen),
  die schwarze Treppe ist der beste Wert bis dahin. Der Bestwert fällt in drei Sprüngen von 2,51e-3 (Prüfstein) auf 2,40e-4.
- **(b)** Werden die Wahlen **im Mittel** besser? Kaum. Der Median der letzten 15 Formen pendelt zwischen 6e-4 und 1,1e-3
  (erste 15: 9,5e-4, letzte 15: 9,2e-4; beim Zwischenstand 91 waren es noch 6,7e-4). Der Anteil mit allen Bauregeln bleibt bei 50–80 % (erste 15: 67 %, letzte 15: 53 %). PI findet die guten Formen
  durch Breite, nicht dadurch, dass jede Wahl besser wird.
- **(c)** Was wählt PI? Die Gradientenlänge der Wahlen fällt von etwa 5,5 auf 4. PI gibt seine Anfangshypothese
  („große Gradientenlänge = einfache Spulen“) auf, sobald die Ergebnisse dagegen sprechen. Die Elongation (Abplattung des Querschnitts) steigt leicht
  (6,4 → 7,2), passend zur Rangkorrelation (ρ −0,44, F-311-Zwischenauswertung). Ab Form 45 wählt PI wieder höheres iota.
  Der Anteil nfp 2 steigt von 73 % (erste 15) auf 87 % (letzte 15; Zwischenstand 91: 93 %).
- **(d)** Wo im nach QI sortierten Pool greift PI zu? Nicht der Reihe nach (gestrichelt wäre die feste Ersatzregel),
  sondern über die ersten 150 Ränge verteilt. Das ist erkunden und ausnutzen zugleich. Die drei Kreuze sind der Prüfstein
  und die zwei Ersatzwahlen.

## Video `loop_evolution.mp4` (50 s, 4 Bilder/s, erweitert 12.11.2026), Lesehilfe
Grau sind alle 361 Formen im Pool (ConStellaration, unverändert, QI ≤ 5e-4, nfp 2–5), nach Elongation (größte Abplattung des Querschnitts, rechts) und kleinster Gradientenlänge (oben; groß = glattes Feld, nach Kappel, Landreman & Malhotra 2024 der Grund, warum manche Plasmen nahe Spulen brauchen). Beide Werte stammen aus dem Datensatz. Nacheinander erscheinen die von PI
gewählten Formen, die Farbe zeigt den Feldfehler der Spulen (gelb = einfache Spulen, dunkel = schwierige). Der rote Ring
markiert die bisher beste Form, die Zahl oben links ist die Nummer der Wahl. Man sieht, wie sich die Wahl nach anfänglicher
Streuung in der Wolke bei Elongation um 7 und Gradientenlänge um 4 sammelt, und dort liegen die gelben Punkte.
Teil 2 (ab „PI 100 · Zufall …“): Die 261 übrigen Formen erscheinen als Quadrate, drei je Bild, in der Reihenfolge der Zufallsrechnung (Startwert 20261110), gleiche Bewertung. Der rote Ring gilt über beide Teile: Er springt zu DZrUR4dA (1,56e-4, Elongation 6,1), knapp neben der Häufung. Die Gegend stimmte: 30 der 36 Formen mit Feldfehler unter 4e-4 liegen bei Elongation 6,5–7,6. Innerhalb dieser Gegend wählte PI nicht besser als der Zufall (B-075). Am Ende 3 s Standbild.
Im Bild steht nur der Name des Autors, die Erklärung steht hier.

## Ehrliche Einordnung
Nachtrag 12.11.2026: Der Vergleichslauf liegt vor (B-075, `stellarator/zufall_gegen_pi.py`). PI schlägt im Median 94 % zufälliger Gruppen, aber nur wegen der Vorliebe für nfp 2; innerhalb nfp 2 wie Zufall, der PI-Bestwert schlägt nur 14 %. Die fünf besten Formen stammen aus der Zufallsreihe. Belegt ist: Die Breite der Suche hat den Bestwert gegenüber dem Bezug um den Faktor 10 verbessert, und
PI hat seine Wahl sichtbar nach den Ergebnissen verschoben.
