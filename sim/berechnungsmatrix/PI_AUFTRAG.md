# Auftrag fuer PI (lokales Modell) - Berechnungsmatrix abarbeiten (2026-11-05)

Du bist nur Betreiber, nicht Rechner: Die Rechnungen machen die Skripte, du startest sie, schaust auf den Stand und berichtest. Erfinde nie Zahlen.

1. Start (einmal): `cd ~/hermes/fusion && bash start_berechnungsmatrix.sh` (startet losgeloest und kehrt zurueck; laeuft es schon, meldet es das).
2. Stand pruefen (jederzeit, billig): `bash start_berechnungsmatrix.sh --status`; Verlauf mit Uhrzeit: `tail -20 sim/berechnungsmatrix/zwischenstand.txt`.
   Fertig ist alles, wenn dort 'MATRIX FERTIG' steht (Dauer etwa 9 bis 14 Stunden; davon Experimentstufen 4 bis 7 etwa 3 bis 4 Stunden bei 4 parallel).
   Die Matrix hat ~510 Zeilen; `--status` zeigt dann nur laufende Jobs und die Summe je Stufe (ganze Liste in sim/berechnungsmatrix/status.md).
3. Haengt nichts? Wenn seit mehr als 2 Stunden kein neuer Eintrag in zwischenstand.txt steht UND `~/bin/rechnung` keine laufende Rechnung zeigt: `bash start_berechnungsmatrix.sh` erneut starten (setzt fort, fertige Jobs werden uebersprungen).
4. Pausieren (z. B. wenn der Rechner gebraucht wird): `~/bin/rechnung pause`, fortsetzen: `~/bin/rechnung weiter`.
5. Nach 'MATRIX FERTIG': Ergebnisse stehen in
   - docs/recherche/qi_tragwerk/opus_filter_suche_tabelle.md (Suche mit 120 Versuchen je Startform),
   - docs/recherche/qi_tragwerk/qi_profil_serie.md (QI-Profil von 120 Datensatzformen),
   - sim/qi_flaeche/verdrillung/r00_tabelle.md und Bild (Radius-Reihen),
   - docs/recherche/qi_tragwerk/qi_experiment.md mit Bildern im Ordner qi_experiment/ (Experimentmatrix, Stufen 4 bis 7),
   - sim/qi_flaeche/experiment/alle_proben.csv (jede Probe eine Zeile: Koeffizienten, Kennzahlen, Verletzungen, Fehlertext; Lerndaten),
   - Einzelergebnisse sim/qi_flaeche/experiment/{form,strom,datensatz}/*.json (je Probe eine Datei, Feld 'grund' sagt warum).
   Optional `bash sim/berechnungsmatrix/pi_zusammenfassung.sh` (liest diese Dateien, schreibt sim/berechnungsmatrix/zusammenfassung_pi.md; Zahlen werden automatisch gegen die Quelle geprueft).
6. Regeln: Nichts loeschen, nichts pushen, nichts hochladen. Gedaechtnis ist die Datei: ERINNERUNGEN.md (Uebergabezeile mit echter Uhrzeit `date` anfuegen), nicht der Chatverlauf.
7. Was die Ergebnisse beantworten: (a) Wird mit mehr Budget eine Form zulaessig (Aufgabe 3)? Siehe Spalten 'P3 zul.' in der Suchtabelle. (b) Ist der Rand im Datensatz die schlechteste Flaeche (Profil-Serie)? (c) Liegt das QI-Optimum wirklich beim Originalradius (Radius-Reihe um 1,0 mit 0,95/1,05)? (d) Experimentmatrix (qi_experiment.md): Wie viel Anteil der wilden Proben ist rechenbar (Abschnitt 1, Zeilen 'wild')? Ist Zufall je besser als vernuenftig (Spalte 'besser als Basis', vernunft gegen wild)? Wie linear ist QI in den Stroemen (Abschnitt 6, R2 im geprueften Bereich +-5 % gegen +-20/+-50 %; ausserhalb +-5 % ist das Werkzeug nicht geprueft)? Ist irgendeine Probe zulaessig (Abschnitt 4, 'Zulaessige Proben')? Abschnitt 7 vergleicht automatisch mit der Erwartung F-252.
   Die Deutung macht der Mensch oder ein staerkeres Modell - nicht raten.
8. Experimentmatrix neu erzeugen (nur wenn ausdruecklich verlangt): `.venv-constellaration/bin/python sim/berechnungsmatrix/erzeuge_matrix.py` (handgeschriebene Zeilen bleiben, gleiche Datei bei gleichem Skript). Fertige Proben werden nie neu gerechnet. Auswertung jederzeit einzeln: `.venv-constellaration/bin/python -m stellarator.qi_experiment auswertung` (billig, auch mit Teilergebnissen).

## Erweiterung 2026-11-05 (grosszuegige Matrix, Nutzer erst am 2026-11-06 gegen 17:00 wieder da)
Matrix etwa 1700 Zeilen: Strom-Proben 850 (150 vernuenftig, 700 wild), Formproben 432 (256 vernuenftig, 176 wild), Datensatzproben 400. Geschaetzte Dauer nach Ende der Suche (Stufe 3): 10 bis 13 Stunden (Schaetzung, +-50 %). Die Auswertung (Stufe 8) laeuft erst am Ende. Ist die Matrix am 2026-11-06 um 17 Uhr noch nicht fertig, Auswertung von Hand: cd ~/hermes/fusion && .venv-constellaration/bin/python -m stellarator.qi_experiment auswertung (liest die fertigen Proben); ebenso qi_filter_suche auswertung und qi_profil_serie auswertung. Fortsetzen: ./start_berechnungsmatrix.sh.
