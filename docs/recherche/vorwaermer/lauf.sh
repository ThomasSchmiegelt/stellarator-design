#!/bin/bash
# Schritt 2 (Literatur) fuer den Divertor-Vorwaermer: ein Thema je PI-Aufruf (frischer Kontext), Datei = Gedaechtnis.
# Ergebnis je Thema in zeilen/NN.md (Tabellenzeilen), Abrufe in recherche_ablage/ (nicht im Repo). Am Ende ergebnis.md + Pruefung.
cd "$(dirname "$0")"; mkdir -p zeilen
THEMEN=("EU-DEMO Divertor: Kühlwasser der Plasma-Wandelemente (PFC) und des Kassettenkörpers – Eintrittstemperatur, Austrittstemperatur, Druck"
        "ITER Divertor: Kühlwasser – Eintrittstemperatur, Austrittstemperatur, Druck"
        "Wendelstein 7-X Divertor: Kühlwasser – Eintrittstemperatur, Austrittstemperatur, Druck, Durchfluss"
        "Druckwasserreaktor (Konvoi, EPR oder WWER-1000) Sekundärkreis: Speisewassertemperatur vor dem Dampferzeuger, Frischdampfdruck und -temperatur, Kondensatordruck oder -temperatur"
        "Druckwasserreaktor-Turbinenanlage: Speisewasser-Vorwärmung – Anzahl Niederdruck- und Hochdruck-Vorwärmer, Temperaturen nach den Vorwärmstufen, Bauart der Vorwärmer")
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
und eindeutig zur Größe gehören (Eintritt nicht mit Austritt verwechseln). Nicht gefundenes: Wert nicht gefunden.
Danach: python3 ~/.hermes/skills/cae/web-recherche/pruefe.py zeilen/$n.md und Fehler beheben, bis 0 Fehler." \
    > zeilen/$n.log 2>&1
  echo "ENDE $n rc=$? $(date +%H:%M:%S)"
done
{ echo "# Vorwärmer: Divertor-Kühlwasser und Speisewasser (PI, qwen-gross, nur mit Belegen)"; echo
  echo "| Thema | Größe | Wert | Einheit | Belege |"; echo "|---|---|---|---|---|"
  for f in zeilen/*.md; do grep '^| ' "$f" | grep -v '^| Thema' | grep -v '^|---'; done; } > ergebnis.md
{ echo; echo '```'; python3 ~/.hermes/skills/cae/web-recherche/pruefe.py ergebnis.md; echo '```'; } > pruefung.txt 2>&1
cat pruefung.txt >> ergebnis.md
echo "PI_FERTIG $(date +%H:%M:%S)"
