# Hüllenfreiraum und Spannung im feineren Netz: Ursache (DPrcxq66, qi_proxima_dpr 0002 gegen 0003)

Stand 2026-11-04, Opus-Unteragent. Grenzen (Stahl p99 500 MPa, Dehnung 0,3 %, Fluenz 3e18) sind Annahmen.

## Ausgangslage

| Punkt | Netz | Hülle | Stahl p99 | u_max | Verbinder ok |
|---|---|---|---|---|---|
| 0002 | Standard (54 Stationen nominal) | 1,556 m | 384 MPa | 44 mm | 284 / 344 |
| 0003 | stationen_faktor 1,5, verbinder_halb 3, plan_von 0002 | 1,187 m | 580 MPa | 146 mm | 246 / 284 |

## Vorgehen

1. Hülle direkt aus `struktur.vtu` gemessen (kleinster Abstand aller Stahlknoten zum Plasmarand): 0002 1,556 m, 0003 1,206 m (Knoten; zwischen den Stationen 1,187 m). Wickelpaket in beiden 1,93 m vom Plasma. Der Unterschied liegt also in der Stahlwand, nicht in Spulenlage oder Messung.
2. Wände stufenweise nachgebaut (`waende` → `biegegrenze` → `entflechten`, genau wie `kopplung.struktur_netz`) und nach jeder Stufe die Hülle gemessen. Der Nachbau trifft beide Ergebnisse exakt (1,556 / 1,187 m).
3. Eigene feine Durchdringungsprüfung: fremde Gehäuseflächen mit 20 Punkten je Seite und 8 Zwischenringen je Abschnitt abgetastet, gegen das eigene Gehäuserechteck jeder Station (mit und ohne 2 cm Spiel).
4. Netz beider Punkte ohne Elmer gebaut: Restlücken je Spule (wie `verb_modus=luecken`), Stahl p99 und u_max je Spule aus `struktur.vtu`.
5. Vorschlag als Option eingebaut, nur Netzbau geprüft, dann **ein** Elmer-Lauf (im Scope, 65 s).

## (1) Warum ändert sich die Hülle mit der Stationszahl?

**Messung:**

| Stufe | Hülle 0002 | Hülle 0003 |
|---|---|---|
| nach `waende` | 1,174 m | 1,187 m |
| nach `biegegrenze` | 1,174 m | 1,187 m |
| nach `entflechten` | **1,556 m** | 1,187 m |

- Vor `entflechten` ist die Hülle netzstabil (Unterschied 0,013 m). Die Biegegrenze ändert die Hülle in keinem der beiden Netze. Sie kappt in beiden fast gleich viel (312 bzw. 316 Stationen, größte Kappung 0,62 m).
- Die engste Stelle liegt in beiden Netzen am selben Ort: Spule 6 (und ihre Symmetriepartner 13, 20, 27), Bogenlänge etwa 45,8 m, an der Ecke innen/rechts. Dort reicht die **Seitenwand „rechts“ mit voller Stärke 0,80 m (wand_seite)** zum Plasma hin.
- Im Standardnetz hat `entflechten` diese Seitenwand an Station 66 von 0,80 auf 0,19 m gekürzt (an den Nachbarstationen auf 0,08 bis 0,23 m). Dadurch springt die Hülle auf 1,556 m. Im Netz ×1,5 bleibt sie an zwei Stationen (81, 82) bei 0,80 m stehen, links und rechts davon ist sie auf 0,11 bis 0,15 m gekürzt.
- Die feine Prüfung zeigt: Diese Kürzung war **nicht nötig**. Setzt man im Standardnetz die Seitenwand von Spule 6 (65 bis 67) und die Innenwand der Nachbarspule 5 (72 bis 74) zurück auf den Stand vor `entflechten`, dringt kein Gehäuse in ein anderes ein. Die Hülle ist dann 1,174 m. Auch die stehen gebliebenen 0,80 m im feinen Netz sind frei von Durchdringung.

**Deutung (Vermutung, durch die Zahlen gestützt):** `entflechten` prüft fremde Flächenpunkte gegen das Rechteck der eigenen Station in einer Scheibe von ±halbem Stationsabstand und kürzt dann die Stationen i−1, i, i+1. Bei grobem Stationsabstand (0,75 bis 0,9 m an dieser Stelle) und verdrillten QI-Spulen erkennt das Verfahren Eindringen, wo keines ist, und kürzt dazu noch eine breitere Strecke. Welche Wand nachgibt (eigene Seitenwand oder Innenwand des Nachbarn), hängt von Abtastung und Reihenfolge der Spulen ab. Die Hülle von 1,556 m im Standardnetz war damit ein **Zufall des Kürzens**. Die Wände, wie sie parametrisiert sind, ergeben rund 1,17 bis 1,24 m. Bei DP9 lag die engste Stelle offenbar nicht an einer solchen gekürzten Seitenwand, daher dort nur 0,04 m Unterschied.

Weitere Messung: `stationen_faktor 1,5` ergibt wegen der Krümmungsabtastung je Spule nur 1,22- bis 1,32-mal so viele Stationen (z. B. Spule 6: 74 → 90). Der Querschnitt wird nicht feiner (n_wand, n_wp gleich). „Netz ×1,5“ ist also in Wirklichkeit etwa ×1,25 entlang der Spule.

## (2) Höhere Spannung: feineres Netz, dünnere Wand oder verlorene Verbinder?

**Messung:**
- Die Wand ist nicht dünner: Stahlvolumen 5029 gegen 5065 m³, Biegegrenze gleich stark.
- Verbinder: 0003 übernimmt nur die 284 guten Verbinder aus 0002 (plan_von). 38 davon fallen im neuen Netz an der Jacobi-Prüfung durch (PLAN_STRENG=False), 10 davon sind Lückenfüller. Mit einem festen Plan läuft keine Lückenfüllung. Die größte Restlücke steigt von 3,94 auf **15,2 m**.
- Ursache der Ausfälle: verbinder_halb 3 auf ×1,25 Stationen macht die Verbinder etwa 20 % breiter (3/2 · 1/1,25), nicht gleich breit. Mit verbinder_halb 2 überleben 266 statt 246 Verbinder, die größte Lücke bleibt aber bei 10,4 m.
- Je Spule (Lücke m / Stahl p99 MPa / u_max mm, 0002 → 0003):
  - Spule 12/26: 3,8 / 955 / 28 → **15,2 / 1806 / 146** (Ort von u_max)
  - Spule 5/19: 3,9 / 1043 / 45 → 10,7 / 1231 / 71
  - Spule 3/17: 3,4 / 506 / 23 → 8,0 / 1100 / 49
  - Spule 10/24: 3,5 / 499 / 24 → 6,5 / 957 / 37
  - Spulen mit gleicher oder kleinerer Lücke (0, 1, 2, 7, 8, 9): p99 je Spule +3 bis +53 %. Das ist ein Netzeffekt an Spannungsspitzen; im Gesamt-p99 zeigt er sich aber nicht (siehe Elmer-Lauf).
- **Elmer-Kontrolllauf** (`sim/kopplung/qi_proxima_dpr_opus/punkte/0000`): Netz ×1,5 (80 Stationen), Verbinder frei neu gesetzt mit Lückenfüllung (verbinder_halb 2, kein plan_von), Hüllengrenze 1,5 m (siehe unten). Ergebnis: Stahl p99 **386 MPa**, Wickelpaket p99 257 MPa, Verguss 124 MPa, u_max 35 mm, Dehnung WP 0,26 %, größte Lücke 3,77 m, 268 Verbinder, Hülle 1,551 m, Fluenz 1,1e17. **Alle Grenzen erfüllt.**

**Schluss:** Der Anstieg 384 → 580 MPa und 44 → 146 mm kommt von den **verlorenen Verbindern bzw. großen Lücken** im Modus plan_von. Er kommt weder von dünnerer Wand noch vom Netz: Mit gefüllten Lücken liefert das feinere Netz dasselbe Gesamt-p99 (386 gegen 384 MPa). Einschränkung: Im Kontrolllauf sitzen die Verbinder an anderen Orten als in 0002 (nicht „derselbe Ort“ wie in F-197 gedacht), und die Hülle ist durch die Grenze festgelegt. Netzstabil ist also die Kette „gleiche Regeln, feineres Netz“, nicht „gleicher Plan, feineres Netz“.

## (3) Vorschlag und Prüfung

**Änderung (eingebaut, Option):** Neuer Parameter `huelle_min_m`. Nach `entflechten` dünnt `kopplung.huelle_grenze` jede Wandseite, deren Außenfläche (gleiche Abtastung wie `huelle_abstand`: vier Seiten mit Ecken, auch zwischen den Stationen) dem Plasma näher kommt als die Grenze. Gedünnt wird an beiden Stationen des Abschnitts um das Defizit, bis zu 20 Runden. Damit ist die Hülle eine Entwurfsvorgabe und nicht mehr Nebenprodukt von `entflechten`. Ohne den Parameter bleibt alles wie bisher: Im Netzbau ohne Option sind `verbinder_plan.json` und `biegegrenze.json` für 0002 und 0003 bytegleich zu den Originalen, die Hülle ist gleich.

**Prüfung (nur Netzbau, keine negativen Elemente):**

| Fall | Hülle | gedünnte Stationen | Verbinder ok | Lücke max |
|---|---|---|---|---|
| Standardnetz, huelle_min 1,5 | 1,556 m (unverändert, nichts gedünnt) | 0 | 284 | 3,94 m |
| Netz ×1,5, plan_von, huelle_min 1,5 | 1,551 m | 32 (max. 0,31 m) | 246 | 15,2 m |
| Netz ×1,5, frei, verbinder_halb 2, huelle_min 1,5 | 1,551 m | 32 | 268 | 3,77 m |

Die Hülle ist damit netzstabil (1,556 gegen 1,551 m). Für die Netzstudie zusätzlich empfohlen: bei geänderter Stationszahl kein plan_von, sondern Verbinder frei mit Lückenfüllung setzen (oder plan_von nur zusammen mit einer Lückenfüllung) und verbinder_halb nach Breite in Metern wählen statt mal 1,5.

**Verworfen:** „Nachwachsen“ (gekürzte Wände nach `entflechten` zurücknehmen, wo fein geprüft frei). Das macht die Hülle ebenfalls nahezu netzstabil (1,238 gegen 1,187 m), füllt aber den Platz zwischen den Gehäusen. Dann fallen Verbinder weg (Standardnetz 232 statt 284, Lücke 12,5 m; Netz ×1,5: 186). Es bestätigt aber: Mit voller Seitenwand liegt die ehrliche Hülle dieser Wände bei rund 1,2 m (Fluenz etwa 2,6e18 bis 4,3e18).

## Folgen für B-040/B-041

- B-040 „DPrcxq66 im Ziel“ hing im Standardnetz an einer zufällig gekürzten Seitenwand. Ohne Hüllengrenze wäre der Satz an der Fluenz knapp (1,24 m) oder darüber (1,19 m).
- Mit `huelle_min_m=1.5` (Seitenwand an 32 Stationen bis 0,31 m dünner) erfüllt DPrcxq66 auch im Netz ×1,5 alle Grenzen (386 MPa, 0,26 %, 1,1e17).
- Nicht geprüft: Abkühlen und Submodell mit Hüllengrenze, Netz ×1,5 im Querschnitt (n_wand, n_wp), Standardnetz mit Hüllengrenze in Elmer (geometrisch identisch zu 0002, daher nicht gerechnet).

## Dateien

- Code: `stellarator/kopplung.py` (Funktion `huelle_grenze`, Option `huelle_min_m` in `struktur_netz`). Nicht committet.
- Lauf: `sim/kopplung/qi_proxima_dpr_opus/punkte/0000` (param.json, ergebnis.json, huelle_grenze.json, struktur.vtu). Aufruf: `kopplung punkt --studie qi_proxima_dpr_opus --nr 0 --von qi_proxima_dpr/0003 --p huelle_min_m=1.5 verbinder_halb=2 plan_von=`
- Diagnoseskripte lagen nur im temporären Ordner (Nachbau der Wandstufen, feine Durchdringungsprüfung, Lücken je Spule).
