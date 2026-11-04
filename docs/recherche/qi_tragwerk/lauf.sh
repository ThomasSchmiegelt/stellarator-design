#!/bin/bash
# Literatur Tragwerk für Stellaratoren: ein Thema je PI-Aufruf (frischer Kontext), Datei = Gedächtnis. Wiederaufnahme: neu starten.
cd "$(dirname "$0")"; mkdir -p zeilen
THEMEN=("Wendelstein 7-X Spulen-Stützstruktur: Kräfte auf die Spulen, zentraler Stützring, Stützelemente (narrow support elements, lateral support elements), Spannungen, Verformung"
        "HELIAS 5-B Stellarator-Reaktor: Spulenkräfte, Stützstruktur, Spulenzahl, Feld am Leiter"
        "NCSX Stellarator: Spulen-Stützstruktur (coil structure), Kräfte, zulässige Spannung"
        "ITER Toroidalfeldspule: Gehäusestahl 316LN, zulässige Spannung, Kräfte je Spule, Verformung"
        "ARIES-CS kompakter Stellarator: Spulenstruktur, Kräfte, Stützrohr, Spannungen"
        "Stellaris Stellarator-Kraftwerk (Proxima Fusion, Lion 2025): Spulenzahl, Kräfte, Spannungen, Stützstruktur")
for i in "${!THEMEN[@]}"; do
  n=$(printf %02d $((i+1))); t="${THEMEN[$i]}"
  [ -s zeilen/$n.md ] && continue
  echo "START $n $(date +%H:%M:%S)"
  timeout 1200 ~/.npm-global/bin/pi -p --provider ollama --model qwen-gross:latest \
    --skill ~/.hermes/skills/cae/web-recherche --no-session \
    "Recherche für genau EIN Thema: $t. Lies zuerst ~/.hermes/skills/cae/web-recherche/SKILL.md und halte dich streng daran.
Höchstens 5 Abrufe mit abruf.py (Ablage ./recherche_ablage). Suche mit suche.py (wiki, osti, openalex, arxiv).
Schreibe das Ergebnis in die Datei zeilen/$n.md als Markdown-Tabellenzeilen OHNE Kopfzeile, eine Zeile je Größe, Spalten:
| Thema | Größe | Wert | Einheit | Belege |
Jeder Wert braucht in der Spalte Belege einen Beleg der Form Beleg: \"wörtliches Zitat\" (URL). Das Zitat muss die Zahl enthalten
und eindeutig zur Größe gehören. Nicht gefundenes: Wert nicht gefunden.
Danach: python3 ~/.hermes/skills/cae/web-recherche/pruefe.py zeilen/$n.md und Fehler beheben, bis 0 Fehler." \
    > zeilen/$n.log 2>&1
  echo "ENDE $n rc=$? $(date +%H:%M:%S)"
done
{ echo "# Tragwerk von Stellaratoren: Literaturwerte (PI, qwen-gross, nur mit Belegen, Deutung ungeprüft)"; echo
  echo "| Thema | Größe | Wert | Einheit | Belege |"; echo "|---|---|---|---|---|"
  for f in zeilen/*.md; do grep '^| ' "$f" | grep -v '^| Thema' | grep -v '^|---'; done; } > ergebnis.md
{ echo; echo '```'; python3 ~/.hermes/skills/cae/web-recherche/pruefe.py ergebnis.md; echo '```'; } > pruefung.txt 2>&1
cat pruefung.txt >> ergebnis.md
echo FERTIG Literatur
