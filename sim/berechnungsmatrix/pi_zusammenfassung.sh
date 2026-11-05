#!/bin/bash
# PI fasst die Ergebnisdateien zusammen; jede Zahl wird danach gegen die Quelldateien geprueft (ungepruefte Zahlen werden markiert).
cd "$(dirname "$(readlink -f "$0")")/../.." || exit 1
O=sim/berechnungsmatrix/zusammenfassung_pi.md; : > $O
for F in docs/recherche/qi_tragwerk/opus_filter_suche_tabelle.md docs/recherche/qi_tragwerk/qi_profil_serie.md sim/qi_flaeche/verdrillung/r00_tabelle.md docs/recherche/qi_tragwerk/qi_experiment.md; do
  [ -s "$F" ] || { echo "## $F: fehlt" >> $O; continue; }
  T=$(mktemp)
  timeout 1200 ~/.local/bin/pi -p --provider ollama --model qwen-gross:latest --no-session \
    "Lies die Datei $F. Schreibe eine Zusammenfassung in hoechstens 8 Saetzen auf Deutsch fuer einen Maschinentechniker. Verwende NUR Zahlen, die woertlich in der Datei stehen, und nenne keine Deutung, die nicht in der Datei steht. Gib nur den Text aus." > $T 2>&1
  { echo "## $F"; cat $T; echo; } >> $O
  python3 - "$F" "$T" >> $O <<'PY'
import re,sys
quelle=open(sys.argv[1]).read(); text=open(sys.argv[2]).read()
zahlen=set(re.findall(r"\d+[.,]\d+(?:e-?\d+)?|\d{2,}",text))
fehl=[z for z in zahlen if z not in quelle and z.replace(",",".") not in quelle.replace(",",".")]
print("_Pruefung: " + ("alle Zahlen stehen in der Quelle._" if not fehl else "NICHT in der Quelle gefunden: "+", ".join(sorted(fehl))+" (Text nicht verwenden, Quelle lesen)._")+"\n")
PY
  rm -f $T
done
echo "Zusammenfassung von PI (lokales Modell), nur mit Zahlenpruefung, Deutung nicht geprueft." >> $O
