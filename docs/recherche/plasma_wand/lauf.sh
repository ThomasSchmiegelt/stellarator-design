#!/bin/bash
# Literatur Plasma-Wand-Abstand: ein Thema je PI-Aufruf, Datei = Gedaechtnis. Wiederaufnahme: neu starten.
cd "$(dirname "$0")"; mkdir -p zeilen
THEMEN=("W7-X Stellarator: Abstand Plasma zur ersten Wand und Abstand Plasma zu den Spulen in Metern, kleiner Plasmaradius a, Hauptradius R"
        "HELIAS Stellarator-Kraftwerk (HELIAS 5-B oder HELIAS Reaktorstudie): Dicke von Blanket und Abschirmung, Abstand Plasma zur Spule in Metern"
        "ARIES-CS kompakter Stellarator-Reaktor: minimaler Abstand Plasma zur Spule (minimum coil-plasma distance), Dicke von Blanket und Abschirmung in Metern"
        "Stellaris Proxima Fusion oder Stellarator Kraftwerk Entwurf: coil-plasma distance, Abstand Plasma Spule in Metern oder in Einheiten des Plasmaradius"
        "Tokamak Kraftwerk ARC oder SPARC oder EU-DEMO: Dicke des Inboard Blanket und der Abschirmung zwischen Plasma und Toroidalfeldspule in Metern"
        "Definition Plasma-Wand-Abstand: letzte geschlossene Flussflaeche (LCFS), Scrape-off-Layer, Abstand Separatrix zur ersten Wand, Unterschied zu Abstand Plasma zur Spule"
        "Stellarator Spulen: Fertigungs- und Positionstoleranz der Spulen in Millimetern (Wendelstein 7-X coil tolerance) und Abweichung der Plasmaform oder Auswirkung auf Magnetfeld Fehlerfelder"
        "Scrape-off-Layer Breite oder Wärmeflussbreite (heat flux width) in Stellaratoren und Tokamaks in Millimetern oder Zentimetern, W7-X Divertor Abstand der Kacheln zur letzten geschlossenen Flussfläche"
        "W7-X Divertor und Wandkacheln: Dicke der Kacheln (Graphit, Wolfram, Kohlenstoff) in Millimetern und Wärmelast in Megawatt je Quadratmeter")
for i in "${!THEMEN[@]}"; do
  n=$(printf %02d $((i+1))); t="${THEMEN[$i]}"
  [ -s zeilen/$n.md ] && continue
  echo "START $n $(date +%H:%M:%S)"
  timeout 1200 ~/.npm-global/bin/pi -p --provider ollama --model qwen-gross:latest \
    --skill ~/.hermes/skills/cae/web-recherche --no-session \
    "Recherche für genau EIN Thema: $t. Lies zuerst ~/.hermes/skills/cae/web-recherche/SKILL.md und halte dich streng daran.
Höchstens 5 Abrufe mit abruf.py (Ablage ./recherche_ablage). Suche mit suche.py (wiki, osti, openalex, arxiv). Englische Wikipedia bevorzugen.
Schreibe das Ergebnis in die Datei zeilen/$n.md als Markdown-Tabellenzeilen OHNE Kopfzeile, eine Zeile je Größe, Spalten:
| Thema | Größe | Wert | Einheit | Belege |
Jeder Wert braucht in der Spalte Belege einen Beleg der Form Beleg: \"wörtliches Zitat\" (URL). Das Zitat muss die Zahl enthalten
und eindeutig zur Größe gehören. Bei Definitionen steht der Wert als kurzer Satz, das Zitat belegt die Definition. Nicht gefundenes: Wert nicht gefunden.
Danach: python3 ~/.hermes/skills/cae/web-recherche/pruefe.py zeilen/$n.md und Fehler beheben, bis 0 Fehler." \
    > zeilen/$n.log 2>&1
  echo "ENDE $n rc=$? $(date +%H:%M:%S)"
done
{ echo "# Plasma-Wand-Abstand: Literaturwerte (PI, qwen-gross, nur mit Belegen, Deutung ungeprueft)"; echo
  echo "| Thema | Größe | Wert | Einheit | Belege |"; echo "|---|---|---|---|---|"
  for f in zeilen/*.md; do grep '^| ' "$f" | grep -v '^| Thema' | grep -v '^|---'; done; } > ergebnis.md
{ echo; echo '```'; python3 ~/.hermes/skills/cae/web-recherche/pruefe.py ergebnis.md; echo '```'; } > pruefung.txt 2>&1
cat pruefung.txt >> ergebnis.md
echo FERTIG Literatur
