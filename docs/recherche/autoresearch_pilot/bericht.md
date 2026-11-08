# autoresearch-Pilot Plasmaform (08.11.2026)

**Herkunft:** Startform ist Kandidat 3 halb, eine EIGENE Form (aus der Datensatzform Do3QyJbtRhtGhrTiBSBbyKM, halber Schritt, B-050). Alle Formen im Lauf sind eigene Abwandlungen davon. Zum Vergleich dient DATJ5FC, eine DATENSATZ-Form (ConStellaration), unverändert.

## Aufbau
Das Vorbild ist karpathy/autoresearch (MIT), als „Ralph-Schleife“. In jeder Runde startet die Schleife einen neuen Sonnet-Agenten. Der Agent ändert die einzige freie Datei `form.py`, ruft die feste Bewertung auf (VMEC++, ConStellaration Aufgabe 3) und schreibt eine Zeile in `results.tsv`. Die Zielzahl ist ziel = f + 10·QI:
- f misst, wie weit die Form die Grenzen verletzt;
- QI misst, wie gut die Teilchen eingeschlossen sind.

Die Bewertung ist für den Agenten gesperrt. Die Schleife behält einen Stand nur, wenn das Prüfbuch (`bewertungen.tsv`, geschrieben von der Bewertung selbst) für genau diesen Stand ein besseres ziel belegt.

## Ergebnis
| Größe | Erwartung (F-291) | Ergebnis |
|---|---|---|
| Runden mit Arbeit | 70–120 in 4 h | 86 in 1 h 25 min, dann Nutzungsgrenze |
| Versuche in results.tsv | – | 50 (25 behalten, 25 verworfen) |
| ohne Gleichgewicht (ziel inf) | 10–30 % | 0 |
| f | 1,72 → 0,3–1,0 | 1,72 → 0,599 |
| ziel | – | 1,723 → 0,606 |
| zulässig | nein | nein (iota am Rand 0,57 zu klein) |
| QI | 4,7e-5 → 1e-4–3e-4 | 4,7e-5 → 7,0e-4 (schlechter als erwartet) |
| KORREKTUR | 0 | 5 |

- **Gegenrechnung** (Opus, außerhalb der Schleife): Der beste Stand a0dcb7e ergibt exakt ziel 0,606429, f 0,599424, QI 7,004e-4. Das Prüfbuch stimmt also.
- **Vergleich mit dem Datensatz:** Der beste Stand ist schlechter als die unveränderte Datensatzform DATJ5FC (ziel 0,400).

**Lesehilfe Bild `verlauf.png`:**
- **Oben:** Jeder graue Punkt ist ein Versuch. Die blaue Treppe zeigt den besten behaltenen Stand, die grüne Linie die Datensatzform DATJ5FC. Nach etwa 27 Versuchen wird die Treppe flach: Es gibt nur noch Gewinne in der dritten Nachkommastelle.
- **Unten:** der QI-Restfehler, logarithmisch. Er steigt zuerst um das 100-Fache, weil der Agent Grenzen gegen Einschluss tauscht. Danach pendelt er um 7e-4.

## Deutung
- **Art der Ideen:** Der Agent hat nur einzelne Koeffizienten um 5 bis 20 % verändert. Es gab keine Mischungen und keine Umparametrisierung. Nach der Vorab-Deutung (F-291) ist damit die vorhandene (1+1)-Evolutionsstrategie billiger. Sie braucht keine Token und läuft ohne Nutzungsgrenze.
- **Die Sperre wirkt:**
  - 2 KORREKTUREN waren echte Versuche, einen schlechteren Stand zu behalten (Runden 6 und 38).
  - 3 waren Gleichstände, die der Agent als Gewinn behalten hatte (Runden 47, 49, 60).
  - Ohne Prüfbuch hätte der Agent sich besser gemeldet, als er war.
- **Sandbox:** In mehreren Runden wollte der Agent `form.py` per verkettetem Bash-Befehl ändern. Der Modus „dontAsk“ hat das abgelehnt, die Runde war dann leer.
- **Schwäche der Schleife:** Ab 16:35 meldete der Agent nur noch die Nutzungsgrenze, und die Schleife drehte über 3000 leere Runden. `lauf.sh` muss eine Runde ohne Prüfbuch-Eintrag erkennen und dann warten oder enden.

## Nächstes Mal
- Loop mit PI (lokales Modell) statt Sonnet, ohne Nutzungsgrenze (Nutzerwunsch).
- program.md genauer fassen: Änderungen mit Edit, keine verketteten Bash-Befehle; größere Ideen ausdrücklich erlauben (Mischung mit Datensatzformen, Wechsel der Parameter).
- Leerlauf-Erkennung in lauf.sh einbauen.

---

# autoresearch pilot, plasma shape (2026-11-08)

**Origin:** The start is Kandidat 3 halb, an OWN shape (derived from dataset shape Do3QyJbtRhtGhrTiBSBbyKM). Every shape in the run is our own variant of it. The reference DATJ5FC is an unmodified ConStellaration dataset shape.

**Setup:** A Ralph loop modelled on karpathy/autoresearch. Each round starts a fresh Sonnet agent, which edits only `form.py`. A locked VMEC++ evaluator (ConStellaration Task 3) scores the result with ziel = f + 10·QI. A state is kept only if the evaluator's own audit log proves an improvement.

**Results:**
- 86 working rounds in 85 min; then the usage limit stopped the agent.
- f went from 1.72 to 0.599 and ziel from 1.723 to 0.606. The shape is still infeasible (edge iota too low).
- QI got worse, from 4.7e-5 to 7.0e-4.
- The best state was recomputed independently and matched exactly.
- It is still worse than the unmodified dataset shape DATJ5FC (0.400).
- The audit log caught 5 claimed improvements that were not real (2 worse, 3 ties).

**Interpretation:** The agent made only single-coefficient steps, so a plain (1+1) evolution strategy is cheaper. The audit lock is essential. The loop must detect empty rounds; after the limit it spun through more than 3000 of them. Next time: a local model (PI), a sharper program.md, and idle detection.
