# Heißeste Spule als Maßstab und Wände je Spule (F-225, Opus-Agent, 2026-11-04)

Auftrag: (1) Bewertung in `stellarator/kopplung.py` auf den p99 der heißesten Spule ohne 0,5-m-Randzone umstellen
(Nutzerentscheidung F-225, B-043), (2) Option `wand_adapt`, die die Wanddicke je Spule an die Last anpasst.
500 MPa ist ein Richtwert (Annahme, keine harte Grenze, Nutzerhinweis); ausgegeben werden immer die Zahl, der Abstand
zu 500 und zu 800 MPa und eine Stufe („unter 500“, „500 bis 800“, „über 800“).

## Was geändert wurde (Code)

- `stellarator/submodell.py`: neue Funktion `p99_ohne_rand_je_spule(netz, vm, V, halb)`. Sie rechnet je Spule im
  Gesamtmodell (Stufe 1) den Stahl-p99 und den Stahl-p99 ohne Elemente, deren Mitte näher als 0,5 m an den eigenen
  Verbinderflächen (Stationen i0 ± verbinder_halb) oder Lagerflächen liegt – dieselbe Regel wie `stufe1.stahl_p99_ohne_rand`
  im Submodell. `main()` des Submodells ist unverändert.
- `stellarator/kopplung.py`:
  - `schritt_struktur` schreibt `struktur.stahl_je_spule` (p99 und p99 ohne Rand je Spule) und `struktur.stahl_heiss`
    (Index, Wert).
  - `bewerten`: Grenze `stahl_p99` bezieht sich auf die heißeste Spule ohne Rand (alte Ergebnisse ohne diesen Wert:
    alter Maßstab, gekennzeichnet in `stahl_massstab`). Neu in `bewertung`: `stahl_p99_alle` (alter Wert über alle
    Spulen), `stahl_heiss` {spule, MPa, abstand_500_MPa, abstand_800_MPa, stufe}. `alle_ok` bleibt und bedeutet
    „alle Richtwerte eingehalten“.
  - Option `wand_adapt=1` (dazu `wand_ziel_MPa` 450, `wand_fak_max` 2, `wand_runden` 3): Runde 0 mit unveränderten
    Wänden; danach Faktor der Spule k × max(1, p99_k / 450), höchstens 2 gesamt, höchstens 3 Anpassungsrunden; Stopp,
    sobald die heißeste Spule ≤ 500 MPa. Der Faktor wirkt auf alle vier Wandseiten direkt nach `waende()`; danach laufen
    Biegegrenze, Entflechten und Hüllengrenze (`huelle_min_m`) wie bisher, d. h. die Plasmaseite wird bei Bedarf wieder
    gekappt. Ablage `wand_je_spule.json` im Punktordner (Faktoren des letzten Laufs = `struktur.vtu`, dazu alle Runden mit
    p99 je Spule, Hülle, Verbinder, Lücke, Durchdringung). Hülle unter `huelle_min_m` wird je Runde gemeldet
    (`huelle_unter_min`, Log).
  - Option `wand_von=<studie>/<NNNN>`: liest die Faktoren aus deren `wand_je_spule.json` (reproduzierbarer Lauf).
- `stellarator/qi_feld_auswertung.py`: Spalten „heißeste Spule MPa“ (mit Spulennummer) und „Stufe“; die Grenzenspalte
  heißt „alle Richtwerte (heißeste Spule)“ und nutzt den neuen Wert; fehlt er, steht „alt: ja/nein“.
- `stellarator/heisse_spule.py` (neu): bestimmt den neuen Maßstab ohne Elmer aus vorhandenem `struktur.vtu`
  (Netz wird im Zwischenordner nachgebaut, Punktordner bleiben unberührt) → `sim/qi_feld/heisse_spule.json`.
- `sim/qi_feld/varianten.txt`: Zeile `qi_proxima_dpr|12|opus|…wand_adapt=1` (Stufe „opus“, keine Kette greift sie auf).

## Gemessen

**Unverändertes Verhalten ohne neue Optionen** (Punkt 8 im Zwischenordner nachgebaut): `verbinder_plan.json`,
`biegegrenze.json`, `huelle_grenze.json` byte-gleich, Knoten und Elemente gleich `struktur.vtu`. Ebenso mit
`wand_adapt` in Runde 0 (Faktoren null) und mit Faktoren alle 1,0 (Netz-Arrays byte-gleich).
**Reproduzierbarkeit**: `wand_von=qi_proxima_dpr/0012` ergibt dasselbe Netz und dieselben Plan-Dateien wie Punkt 12.

**Nachgerechnet aus vorhandenen Ergebnissen (Stufe 1, ohne Rand):**

| Punkt | heißeste Spule | MPa | Stufe | alle Spulen (alt) |
|---|---|---|---|---|
| dpr 2 (×1,6) | 18 (gleich 4, Symmetrie) | 585 | 500 bis 800 | 384 |
| dpr 8 (×1,6, huelle_min 1,5) | 18 | 585 | 500 bis 800 | 384 |
| dpr 9 (Netz ×2, freie Verbinder) | 5 | 532 | 500 bis 800 | 447 |

Punkt 9 trifft den Submodell-Wert `stufe1.stahl_p99_ohne_rand` exakt (532,48). Punkt 2: hier 585, im Submodell-Ergebnis
568 (B-043). Ursache: Das Submodell von Punkt 2 hatte eine Reparaturrunde (Wand an 7 Stationen um 20 % gedünnt); seine
Randknoten liegen dadurch etwas anders, sodass andere Elemente in die 0,5-m-Zone fallen. Der saubere Stufe-1-Wert ist 585.

**Testlauf Punkt 12** (Basis = Punkt 8: n_basis 7, wand_innen 0,32, t_min 0,88, wand_seite 0,8, freiraum huelle,
verb_modus luecken, huelle_min_m 1,5, dazu wand_adapt=1; Standardnetz, je Runde rund 50 s Elmer):

Erwartung vorher: Runde 0 = 585 MPa (Spulen 4/18); Faktor 1,30 für 4/18; Runde 1 etwa 470–520 MPa; unter 500 nach 1–2
Runden; Hülle hält 1,5 m.

| Runde | Faktoren > 1 | heißeste Spule | MPa | Abstand zu 500 / 800 | alle Spulen | Hülle m | Verbinder | größte Lücke | Stahl t |
|---|---|---|---|---|---|---|---|---|---|
| 0 | – | 18 | 585 | −85 / +215 | 384 | 1,556 | 284/344 | 3,94 m | 39 730 |
| 1 | Spulen 4 und 18 ×1,30 | 11 (gleich 25) | 446 | +54 / +354 | 362 | 1,514 | 282/344 | 3,94 m | 41 019 |

p99 ohne Rand je Spule (Hälfte, Spulen 0–13; 14–27 gleich): Runde 0: 263, 282, 302, 345, **585**, 383, 390, 265, 267,
322, 348, 446, 408, 356. Runde 1: 266, 277, 248, 286, **287**, 378, 395, 265, 268, 322, 348, 446, 409, 368.

- Konvergiert nach einer Anpassungsrunde (Grund „heißeste Spule ≤ Richtwert“). Dicker wurden nur Spulen 4 und 18.
- Die Last wanderte kaum: Nachbarn 3 und 5 sanken (345→286, 383→378), Spule 2 sank (302→248), Spule 13 stieg leicht
  (356→368). Die neue heißeste Spule 11 war schon vorher 446 und blieb gleich.
- Hülle 1,514 m ≥ huelle_min_m 1,5 (Hüllengrenze dünnte 12 Stationen um höchstens 0,052 m), nicht unterschritten.
  Fluenz 1,1e17 → 1,6e17 n/cm² (Richtwert 3e18).
- Verbinder 284 → 282 von 344, größte Lücke unverändert 3,94 m, Durchdringung 0, Auslenkung 44 → 42 mm,
  Dehnung Wickelpaket 0,25 %. Alle Richtwerte eingehalten (alle_ok ja), Stahl Stufe „unter 500“.
- Submodell F4 (fein, 4 Wand-, 6 WP-Zellen) zur Kontrolle: Spule 11 461 MPa ohne Rand (Stufe 1: 449; 1 Reparaturrunde,
  7 Stationen −20 %); Spule 18 273 MPa (2 Reparaturrunden, 8 Stationen bis −36 % Wand, Wert daher eher zu hoch als zu
  niedrig gemessen, nicht geprüft). Zum Vergleich Punkt 2/8 Spule 18 im Submodell: 602 MPa.
- Erwartung: Ziel getroffen (unter 500 nach 1 Runde); die verstärkte Spule fiel mit 287 MPa viel stärker als erwartet
  (470–520), weil die Spannung schneller als linear mit der Wanddicke sinkt; die Hülle hielt wie erwartet.

## Vermutet, nicht geprüft

- Faktor p99/450 ist für Biegung zu grob: Spannung fällt etwa mit der Wanddicke hoch 1 bis 2; ein Faktor
  (p99/450)^0,5 würde Stahl sparen (Spule 4/18 liegen jetzt bei 287 MPa, weit unter dem Ziel). Da die Masse laut Nutzer unwichtig ist,
  ist das nachrangig; die Reserve an Spule 4/18 ist eher ein Vorteil.
- Spulen 11/25 (446) und 12/26 (409) haben keine Reserve gegen das feinere Netz: im Netz ×2 (Punkt 9) wechselte die heißeste
  Spule (5 statt 18) und der Wert änderte sich um 9 %. Ob Punkt 12 im Netz ×2 unter 500 bleibt, ist offen (nächster Lauf: `wand_von=qi_proxima_dpr/0012`
  mit stationen_faktor 2, verbinder_halb 3). Ob die Faktoren bei geänderter Stationenzahl passen, ist unkritisch, sie
  gelten je Spule, nicht je Station.
- Dickere Wände an Spule 4/18 kosten Freiraum zu den Nachbarn; Entflechten fand keine Durchdringung, aber der
  Abstand zwischen den Gehäusen (Spiel) wurde nicht gesondert ausgewertet.
- Das Submodell bleibt durch seine Reparaturrunden unsicher (Wand dort dünner als im Gesamtmodell).

## Dateien

- Code: `stellarator/kopplung.py`, `stellarator/submodell.py`, `stellarator/qi_feld_auswertung.py`,
  `stellarator/heisse_spule.py` (neu); nicht committet.
- Ergebnisse: `sim/kopplung/qi_proxima_dpr/punkte/0012/` (ergebnis.json, wand_je_spule.json, struktur.vtu),
  `sim/submodell/qi_proxima_dpr_0012_s11_F4_w4_q6/`, `sim/submodell/qi_proxima_dpr_0012_s18_F4_w4_q6/`,
  `sim/qi_feld/heisse_spule.json`, `sim/qi_feld/tabelle.md` (neu erzeugt).
