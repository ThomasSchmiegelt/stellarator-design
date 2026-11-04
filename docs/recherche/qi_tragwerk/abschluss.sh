#!/bin/bash
# PI schreibt eine kurze Zusammenfassung, falls Claude nicht mehr da ist. Kennzeichnung: ungeprüft.
cd "$(dirname "$0")/../../.."
[ -s docs/recherche/qi_tragwerk/pi_zusammenfassung.md ] && exit 0
timeout 1200 ~/.npm-global/bin/pi -p --provider ollama --model qwen-gross:latest --no-session \
 "Lies sim/qi_feld/tabelle.md und docs/recherche/qi_tragwerk/ergebnis.md sowie den Eintrag F-186 in ~/hermes/buch/ereignissprotokoll_fusion/ereignisprotokoll.md.
Schreibe docs/recherche/qi_tragwerk/pi_zusammenfassung.md auf Deutsch, höchstens 30 Zeilen, erste Zeile: 'UNGEPRÜFT (PI, ohne Claude)'.
Inhalt: Vergleich Ergebnis gegen Erwartung aus F-186, beste Variante, welche Grenzen verletzt bleiben, offene Fragen.
Verwende NUR Zahlen, die wörtlich in diesen Dateien stehen. Erfinde nichts. Ändere keine anderen Dateien." \
 > docs/recherche/qi_tragwerk/abschluss.log 2>&1
