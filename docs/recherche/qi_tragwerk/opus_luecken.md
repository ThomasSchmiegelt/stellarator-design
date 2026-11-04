# Verbinder nach Lücken setzen (Opus, 2026-11-04): `verb_modus=luecken`

Anlass: B-034. Die Auslenkung der QI-Sätze (dje 241 mm) sitzt in langen Strecken ohne Verbinder und Lager
(dje Spule 8: 17,4 m). Auftrag: neue Ortswahl, die solche Strecken bis auf einen Grenzwert schließt.

## Erwartung (vorher festgelegt, vom Auftraggeber)

u_max unter 100 mm, Stahl p99 unter 500 MPa (500 MPa nur Annahme, F-201), Hülle bleibt 0,47 m.

## Änderung am Code

`stellarator/hexmodell.py`
- Neuer Modus `VERB_MODUS = "luecken"` (Namensreihe standard/getrennt/platte), Grenzwert `LUECKE_MAX` (Standard 4,0 m).
- Ablauf: zuerst Kandidaten wie im Modus `standard` (Nachbarspulen, Querbedingung `SEITLICH_MIN`, nächster Abstand).
  Dann `_luecken_fuellen` (Greedy): je Spule die Strecken zwischen gestützten Stationen messen
  (gestützt = Station mit Verbinderknoten i0/j0 ± verbinder_halb oder mit Lagerfläche), Bogenlänge entlang der Bahn.
  Die größte Strecke über dem Grenzwert zuerst. Darin wird der Kandidat genommen, der die Strecke am gleichmäßigsten
  teilt (bei Gleichstand der kürzere). Kandidat = Station der Spule + nächster Punkt einer der beiden toroidalen Nachbarspulen.
- Lockerung, im Ergebnis ausgewiesen: Querbedingung erst mit `SEITLICH_MIN` (0,8), dann in Stufen 0,7 … 0,0.
  Je Stufe zuerst Kandidaten, deren Fläche auf der Gegenspule frei ist, dann solche, die dort einen vorhandenen
  Verbinder überlappen (gemeinsame Knoten; im Modus `standard` ebenfalls möglich). Je Kandidat probiert:
  Gegenstation nächster Punkt, dann ±1, ±2 Stationen; Seitenflächen erst wie `_seite`, dann bis zu zwei weitere
  zugewandte Paare; Zuordnung der Gegenfläche (rs, rev) alle vier. Genommen wird der erste ohne umgestülpte Elemente
  (gleiche Prüfung wie im Netzaufbau, `_verbinder_ok`). rs/rev werden festgeschrieben, damit der Netzaufbau dieselbe
  Topologie baut. Findet sich keiner, bleibt die Strecke offen und wird übersprungen.
- Je ergänztem Verbinder in `verbinder_plan.json`: `ergaenzt`, `seitlich_stufe`, `ueberlappt`.
- Der Netzaufbau eines Verbinders steht jetzt in `_verbinder_flaechen` (unverändert herausgelöst).
- Mit festem Plan (`plan_von`) wird nichts ergänzt.

`stellarator/kopplung.py`: Parameter `luecke_max_m` (Standard 4,0). Nur bei `verb_modus=luecken` stehen in
`ergebnis.json` unter `struktur`: `luecke_max_m` (größte Restlücke des Satzes), `verbinder_ergaenzt` und `luecken`
(Lücke vorher, Spulen über der Grenze, Zahl je Lockerungsstufe, Zahl überlappend, längster ergänzter Verbinder, je Spule).

## Prüfung 1: bestehendes Verhalten unverändert

Netz ohne Elmer neu gebaut, in einer Kopie außerhalb von sim/ (sim/ dabei nicht verändert):

| Fall | Vergleich | Ergebnis |
|---|---|---|
| gegenprobe_0169_duenn 0010, ohne Option | gegen struktur.vtu | Knoten 201 916, Elemente 176 960 gleich, Koordinaten Abweichung 0,0 m, Hexaeder und Material gleich |
| dito | neuer gegen alten Code | Netz (X, Hexaeder, Material, Spule, Lager), info, verbinder_plan.json bytegleich |
| qi_proxima_dje 0000 (innenkontur, Reparatur) | gegen struktur.vtu | gleich bis 3,6e-15 m |
| dito | neuer gegen alten Code | Netz, info, verbinder_plan.json, biegegrenze.json, reparatur.json bytegleich |
| 0169 dünn, `verb_modus=platte` und `getrennt` | neuer gegen alten Code | bytegleich |
| dje 0000 mit `plan_von=qi_proxima_dje/0000` | neuer gegen alten Code | bytegleich |

Der alte Code lief dafür aus einer Kopie des Pakets mit der vorherigen hexmodell.py.

## Prüfung 2: neuer Punkt qi_proxima_dje 0002

Spulen und Parameter von qi_proxima_dje/0000 (DjLe3eL6, 40 Spulen, 0169-Wände), Basisparameter wie kette13.sh,
`abtastung=kruemmung biegung=innenkontur loeser=mumps verb_modus=luecken freiraum=huelle n_basis=5`.
Rechenzeit 149 s (davon Elmer 60 s, Netz mit Lückensuche rund 80 s), Scope 20 GB.

| Größe | 0000 (standard) | 0002 (luecken) |
|---|---|---|
| größte Lücke ohne Verbinder/Lager | 17,4 m | **4,09 m** (4 von 40 Spulen knapp über 4,0 m) |
| Verbinder ok / Kandidaten | 228 / 316 | 300 / 388 (72 ergänzt, alle ok) |
| u_max | 241 mm | **42,5 mm** |
| Stahl p99 | 620 MPa | **405 MPa** |
| Stahl max (Einzelwert) | 3830 MPa | 1447 MPa |
| Verbinder p99 | 351 MPa | 297 MPa |
| Wickelpaket p99 / Dehnung | 242 MPa / 0,24 % | 202 MPa / 0,20 % |
| Verbindermasse | 11 511 t | 15 547 t |
| Hülle (Freiraum) | 0,472 m | 0,472 m |
| verletzte Grenzen | Stahl, Package, Kernheizung, Fluenz | Package, Kernheizung, Fluenz |

Die Lückenmessung trifft für 0000 die Zahl der Fehlersuche (17,38 m gegen 17,4 m).

Ergänzte Verbinder: 32 mit voller Querbedingung 0,8, 8 mit 0,7, 8 mit 0,6, 24 mit 0,5 (also 40 gelockert);
64 der 72 teilen ihre Fläche auf der Gegenspule mit einem vorhandenen Verbinder; längster ergänzter Verbinder 3,1 m.

## Vergleich mit der Erwartung

- u_max unter 100 mm: **getroffen** (42,5 mm, Größenordnung DP9 46 mm).
- Stahl p99 unter 500 MPa: **getroffen** (405 MPa; Grenze nur Annahme).
- Hülle 0,47 m: **getroffen** (0,472 m). Das war zu erwarten, die Hülle hängt nur an Spulen und Wänden, nicht an den Verbindern.
- Grenzwert 4,0 m nicht ganz erreicht (4,09 m). Ehrlich: in den 4 Restspulen fand sich kein weiterer Kandidat ohne umgestülpte Elemente.

## Grenzen und Vermutungen

- **Vermutung:** Mit dem Lückenplan ist DjLe3eL6 mechanisch kein Ausreißer mehr; die Rangfolge aus B-033 (Stahl, Auslenkung)
  war vor allem ein Urteil über den Verbinderplan. Für dyu und dsd nicht gerechnet.
- Überlappende Verbinder (64 von 72) teilen Knoten auf der Gegenspule; ihre Volumina können sich dort durchdringen
  (Masse doppelt gezählt, Steifigkeit eher überschätzt). Nicht nachgemessen, wie stark.
- Ob die gelockerten, schräg sitzenden Verbinder (Querbedingung bis 0,5) durch fremde Spulen oder den Plasmaraum laufen,
  ist **nicht geprüft**. Kollisionsprüfung der Verbinder fehlt.
- Netzabhängigkeit nicht geprüft (Netzunsicherheit bisher bis ~30 %, F-195). Submodell für 0002 nicht gerechnet.
- Die Fluenz- und Package-Grenzen bleiben verletzt (Hülle 0,47 m); daran ändern Verbinder nichts.
