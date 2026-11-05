# Paarvergleich: Wege zu einem funktionierenden Plasma (2026-11-04)

**Berichtigung 2026-11-05 (B-051):** Die hier genannte QI-Grenze 0,001 und die Schwellen stammen aus meinem Gedaechtnis und sind falsch. Nach dem installierten Paket (problems.py) gilt: Aufgabe 3 QI <= 0,00032 (zulaessig 0,00034), Aufgabe 2 QI <= 0,0001 (zulaessig 0,00011); iota als Betrag; Elongation/Spiegel nur Aufgabe 2, Vakuummulde/Flusskompression nur Aufgabe 3. Gemessen mit echten Schwellen: ohne QI 166 (Aufgabe 3) bzw. 786 (Aufgabe 2) Formen, mit QI 0. Die Reihenfolge der Wege bleibt, der Abstand zum Ziel ist groesser (bestes QI 0,00178, Faktor 5 ueber Aufgabe 3).

"Funktionierend" heisst hier: offizielle Wertung (ConStellaration) groesser 0, mit VMEC++ bestaetigt.

## Messung (Datensatz, 182 222 Zeilen, ohne VMEC)
Einzeln erfuellt: QI <= 0,001: 2 420 | Spiegelverhaeltnis Rand <= 0,25: 21 709 | iota Rand/nfp >= 0,25: 56 165 | Vakuummulde >= 0: 7 430 | Flusskompression <= 0,9: 37 791 | Elongation <= 5: 88 489.
Alle sechs zusammen: 0. Alle ausser QI: 138. Fehlt eine andere Bedingung statt QI: ebenfalls 0.
Folge: QI ist die bindende Nebenbedingung; die anderen fuenf koennen 138 Formen gemeinsam erfuellen.

## Wege
A Datensatz filtern (die 138) | B kleine Schritte von diesen 138 mit VMEC++ (QI senken) | C Surrogat weit suchen | D VMEC++ direkt mit offizieller Zielfunktion | E W7-X vergroessern | F eigene Form von Hand (QA)

## Paarurteile (Annahme/Urteil, nicht gemessen); Zeile schlaegt Spalte = 1
Kriterien: Chance auf Wert > 0, Rechenkosten, Voraussetzung, Eigenstaendigkeit.
A schlaegt C,D,E,F (billig, Voraussetzung fuer B und D); B schlaegt C,E,F; D schlaegt E,F; C verliert gegen alle (B-050: weite Suche 0 von 10); E schlaegt F (belegt, aber nicht eigen, nicht auf Wertung ausgelegt).
A gegen B: B braucht A -> A zuerst. B gegen D: D startet von der besten Form aus B -> B zuerst.

## Reihenfolge
1 A (Minuten, keine Rechnung) -> 2 B (VMEC++ 70-155 s je Form, kleine Schritte) -> 3 D (nur falls B nicht reicht) -> 4 E (parallel als Vergleichsbasis fuer Tragwerk) -> 5 F -> 6 C (nur noch mit kleinen Schritten als Hilfe).
