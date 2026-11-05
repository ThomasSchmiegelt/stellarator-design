#!/bin/bash
# start_berechnungsmatrix.sh - arbeitet die Berechnungsmatrix sim/berechnungsmatrix/matrix.tsv ab, ohne Betreuung.
#
#   bash start_berechnungsmatrix.sh            startet losgeloest (setsid nohup) und kehrt sofort zurueck
#   bash start_berechnungsmatrix.sh --vordergrund   laeuft im Vordergrund (fuer Tests)
#   bash start_berechnungsmatrix.sh --status   zeigt Stand (fertig/offen je Job) und beendet
#   bash start_berechnungsmatrix.sh --mit-pi   wie Start, am Ende fasst PI (lokales Modell) die Ergebnisdateien zusammen
#
# Eigenschaften: Neustart setzt fort (fertige Jobs werden uebersprungen, Suche mit --weiter); jeder Job im systemd-Scope
# 'hermes python <id>' mit Speichergrenze, also pausierbar mit ~/bin/rechnung pause / weiter; niedrige Prioritaet (nice 10);
# keine Wanduhr-Grenzen. Stand: sim/berechnungsmatrix/status.md und zwischenstand.txt. Ende: 'MATRIX FERTIG' in zwischenstand.txt.
# Matrix aendern: Zeile in matrix.tsv anfuegen (Format dort erklaert). Jobs, deren Ergebnisdatei schon da ist, laufen nicht erneut.
# Hinweis fuer die Uebernahme (PI/Hermes/jede neue Sitzung): sim/berechnungsmatrix/PI_AUFTRAG.md und ERINNERUNGEN.md lesen.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
M=sim/berechnungsmatrix; PY=.venv-constellaration/bin/python; PAR=${PAR:-4}; MX=${MATRIX_DATEI:-$M/matrix.tsv}
mkdir -p $M/log

status() {
  local units; units=$(systemctl --user list-units --type=scope --no-legend --plain 2>/dev/null)   # einmal lesen (Matrix hat ~500 Zeilen)
  { echo "# Stand Berechnungsmatrix ($(date '+%F %H:%M'))"; echo; echo "| Job | Stufe | Zustand |"; echo "|---|---|---|"
    grep -v '^#' $MX | while IFS='|' read -r id st gb erg cmd; do
      [ -z "$id" ] && continue
      if [ -n "$erg" ] && [ -s "$erg" ]; then z=fertig; elif [ -f $M/log/$id.fertig ]; then z=fertig; \
      elif grep -q "matrix $id\b" <<< "$units"; then z=laeuft; else z=offen; fi
      echo "| $id | $st | $z |"; done; } > $M/status.md
  local summe; summe=$(awk -F'|' 'NR>4 && /^\| /{gsub(/ /,"",$3); a[$3]++; if($4~/fertig/) f[$3]++} END{for(s in a) print "  Stufe " s ": " f[s]+0 "/" a[s]}' $M/status.md | sort -k2,2n)
  { echo; echo "Summe je Stufe (fertig/alle):"; echo "$summe"; } >> $M/status.md
  if [ "${STATUS_KURZ:-1}" = 1 ] && [ "$(wc -l < $M/status.md)" -gt 60 ]; then head -4 $M/status.md; grep "| laeuft |" $M/status.md; sed -n '/^Summe/,$p' $M/status.md; echo "(ganze Liste: $M/status.md)"; else cat $M/status.md; fi; }

if [ "$1" = "--status" ]; then status; exit 0; fi
if [ "$1" != "--vordergrund" ] && [ -z "$MATRIX_INNEN" ]; then
  if pgrep -f "start_berechnungsmatrix.sh" | grep -v "^$$\$" | grep -q .; then echo "Matrix laeuft schon (Status: --status)"; exit 0; fi
  MATRIX_INNEN=1 MIT_PI=$([ "$1" = "--mit-pi" ] && echo 1) setsid nohup nice -n 10 bash "$0" --vordergrund > $M/lauf.log 2>&1 &
  echo "Matrix gestartet. Stand: bash start_berechnungsmatrix.sh --status | Pause: ~/bin/rechnung pause"; exit 0
fi

job() {  # id gb erg cmd
  id=$1; gb=$2; erg=$3; shift 3; cmd="$*"
  { [ -n "$erg" ] && [ -s "$erg" ]; } && { echo "$(date '+%F %T') uebersprungen (fertig) $id" >> $M/zwischenstand.txt; return; }
  [ -f $M/log/$id.fertig ] && return
  echo "$(date '+%F %T') start $id" >> $M/zwischenstand.txt
  case "$cmd" in
    WARTE_AUF*) s=${cmd#WARTE_AUF }
      while pgrep -f "bash $s" >/dev/null; do sleep 120; done          # laeuft schon von frueher: abwarten statt doppelt rechnen
      systemd-run --user --scope -q -p MemoryMax=${gb}G -p MemorySwapMax=0 --description="hermes python matrix $id" bash $s >> $M/log/$id.log 2>&1 ;;
    *) systemd-run --user --scope -q -p MemoryMax=${gb}G -p MemorySwapMax=0 --description="hermes python matrix $id" \
         env OMP_NUM_THREADS=1 bash -c "${cmd//@PY@/$PY}" >> $M/log/$id.log 2>&1 ;;
  esac
  rc=$?; echo "$(date '+%F %T') ende $id rc=$rc" >> $M/zwischenstand.txt
  [ $rc -eq 0 ] && touch $M/log/$id.fertig
}
export -f job; export M PY MX

echo "$(date '+%F %T') MATRIX START (PAR=$PAR)" >> $M/zwischenstand.txt
for st in $(grep -v '^#' $MX | cut -d'|' -f2 | sort -un); do
  echo "$(date '+%F %T') STUFE $st" >> $M/zwischenstand.txt
  grep -v '^#' $MX | awk -F'|' -v s=$st '$2==s' | while IFS='|' read -r id st2 gb erg cmd; do
    echo "$id|$gb|$erg|$cmd"; done | xargs -P $PAR -d '\n' -I{} bash -c 'IFS="|" read -r id gb erg cmd <<< "{}"; job "$id" "$gb" "$erg" $cmd'
  status > /dev/null
done
status > /dev/null
echo "$(date '+%F %T') MATRIX FERTIG" >> $M/zwischenstand.txt
[ -n "$MIT_PI" ] && bash $M/pi_zusammenfassung.sh >> $M/log/pi.log 2>&1
