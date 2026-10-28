#!/bin/bash
# Eine Anlage je PI-Aufruf (frischer Kontext, qwen-gross hat nur 64k Token). Ergebnis je Anlage in zeilen/NN.md,
# Abrufe gemeinsam in recherche_ablage/. Am Ende ergebnis.md zusammensetzen und pruefen.
cd "$(dirname "$0")"; mkdir -p zeilen
ANLAGEN=("Druckwasserreaktor EPR" "WWER-1000" "BREST-OD-300 (Blei)" "ALFRED (Blei)" "Superphénix (Natrium)"
         "HTR-PM (Helium)" "ITER Erstwand/Blanket-Kühlwasser" "EU-DEMO WCLL-Blanket (Wasser)"
         "EU-DEMO HCPB-Blanket (Helium)" "Wendelstein 7-X Divertor-Kühlwasser")
for i in "${!ANLAGEN[@]}"; do
  n=$(printf %02d $((i+1))); a="${ANLAGEN[$i]}"
  [ -s zeilen/$n.md ] && continue
  echo "START $n $a $(date +%H:%M:%S)"
  timeout 1200 ~/.npm-global/bin/pi -p --provider ollama --model qwen-gross:latest \
    --skill ~/.hermes/skills/cae/web-recherche --no-session \
    "Recherche für genau EINE Anlage: $a. Lies zuerst ~/.hermes/skills/cae/web-recherche/SKILL.md und halte dich streng daran.
Gesucht: Kühlmittel, Eintrittstemperatur, Austrittstemperatur, Druck im Primärkreis.
Höchstens 4 Abrufe mit abruf.py (Ablage ./recherche_ablage, schon geholte Seiten kommen sofort aus dem Speicher).
Schreibe das Ergebnis als GENAU EINE Markdown-Tabellenzeile in die Datei zeilen/$n.md, Spalten:
| Anlage | Kühlmittel | Eintritt °C | Austritt °C | Druck MPa | Belege |
Jeder Zahlenwert braucht in der Spalte Belege einen Beleg der Form Beleg: \"wörtliches Zitat\" (URL). Nicht gefundenes: nicht gefunden.
Danach: python3 ~/.hermes/skills/cae/web-recherche/pruefe.py zeilen/$n.md und Fehler beheben, bis 0 Fehler." \
    > zeilen/$n.log 2>&1
  echo "ENDE $n rc=$? $(date +%H:%M:%S)"
done
{ echo "# Kühlmitteltemperaturen und Drücke (PI, qwen-gross, nur mit Belegen)"; echo
  echo "| Anlage | Kühlmittel | Eintritt °C | Austritt °C | Druck MPa | Belege |"; echo "|---|---|---|---|---|---|"
  for f in zeilen/*.md; do grep '^| ' "$f" | grep -v '^| Anlage' | head -1; done; } > ergebnis.md
{ echo; echo '```'; python3 ~/.hermes/skills/cae/web-recherche/pruefe.py ergebnis.md; echo '```'; } > pruefung.txt 2>&1
cat pruefung.txt >> ergebnis.md
echo "PI_FERTIG $(date +%H:%M:%S)"
