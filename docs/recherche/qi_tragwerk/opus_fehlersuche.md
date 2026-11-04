# Fehlersuche Opus (2026-11-04): Auslenkung QI-Sätze und negative Elemente im Submodell

Auftrag: (1) Ursache der Auslenkungen 190–290 mm in den Gesamtmodellen der QI-Sätze (0169 dünn: 19 mm, DP9: 46 mm),
nur mit vorhandenen Dateien. (2) Submodell scheitert an negativen Elementen; Reparatur aus dem Gesamtmodell wiederverwenden.
Keine neuen Gesamtmodell-Läufe. Alle Prüfläufe im Scope (MemoryMax 20 GB), Ausgaben in einer Kopie außerhalb von sim/,
d. h. sim/ wurde von mir nicht verändert.

## 1. Auslenkung: echte Verformung einer langen ungestützten Strecke, keine Starrkörperbewegung

### Geprüft (aus struktur.vtu, je Spule)

**a) Starrkörperanteil.** Je Spule die Verschiebung mit Translation + kleiner Drehung (6 Freiwerte, kleinste Quadrate)
angenähert. Bleibt viel Rest übrig, ist es Verformung.

| Punkt | u_max mm | Spule | Starrkörper-Translation mm | Rest nach Starrkörperabzug mm | Rest/u_max |
|---|---|---|---|---|---|
| dje 0000 | 241 | 8 (18, 28, 38 gleich) | 35 | 197 | 0,82 |
| dje 0001 | 206 | 18 | 31 | 168 | 0,81 |
| dyu 0020 | 193 | 14 | 23 | 171 | 0,88 |
| dsd 0000 | 293 | 3 | 40 | 248 | 0,85 |
| 0169 dünn 0010 | 19 | 8 | 2,5 | 17 | 0,87 |
| dp9 0004 | 46 | 28 | 4,3 | 41 | 0,89 |

Über 80 % der Auslenkung ist Verformung. Starrkörperbewegung scheidet aus. Das passt zum Code: `baue_netz` setzt für
**jede** Spule eigene Lagerflecken (`lager_ort=beide`, r_lager 3,3 m). Lose Spulengruppen ohne Lager gibt es also nicht.

**b) Größte ungestützte Strecke je Spule.** Als gestützt zählen Stationen mit Verbinderknoten und Stationen innerhalb
r_lager um die beiden Lagerpunkte. Gemessen wird die größte Bogenlänge zwischen gestützten Stationen.

| Punkt | größte Lücke (Spule mit u_max) | Lücke Median aller Spulen | Korrelation u_max zu Lücke⁴ über alle Spulen | u_max liegt in der Lücke |
|---|---|---|---|---|
| dje 0000 | **17,4 m** von 56,3 m Bahn | 4,4 m | **0,98** | ja |
| dje 0001 | 17,4 m | 3,5 m | 0,98 | ja |
| dyu 0020 | 14,8 m von 53,2 m | 7,7 m | 0,96 | ja |
| dsd 0000 | 11,8 m (bis 14,4 m bei Spule 17) | 13,2 m | 0,64 | ja |
| 0169 dünn 0010 | 1,8 m (max. 3,1 m) | 0,6 m | 0,42 | nein (gestützt) |
| dp9 0004 | 6,6 m | 2,6 m | 0,61 | ja |

Die Spulen mit kurzen Lücken (1–1,5 m) in denselben QI-Sätzen verschieben sich nur 6–7 mm. Bei dje und dyu erklärt die
Lückenlänge die Auslenkung fast vollständig (r = 0,96–0,98). Die hohe Auslenkung sitzt bei allen vier QI-Punkten auf der
langen Spulenform (102–120 Stationen, 53–66 m Bahn), die bei 0169 nicht vorkommt.

**c) Wo die Verbinder fehlen (dje 0000, Spule 8, Netz neu aufgebaut, identisch mit struktur.vtu bis 4e-15 m).**
Lager bei s = 0,7 m und 33,3 m (je ±3,3 m). 10 Verbinder-Kandidaten, 5 ok, 5 verworfen (negative Jacobi-Determinante,
−0,3 bis −272). Die ok-Verbinder sitzen bei s = 12,0 / 31,4 / 38,7 / 43,0 / 45,9 m. Zwischen s ≈ 13 m und 30 m liegt
**kein einziger Kandidat**. Die verworfenen Verbinder (13,1 / 47,0 / 50,8 / 52,5 / 53,7 m) liegen fast alle im schon gestützten
Bereich. Die Lücke entsteht also durch die **Auswahl der Orte** (Querbedingung `SEITLICH_MIN` + nächster Abstand je Paar),
nicht durch verworfene Verbinder. Die Zahl „Verbinder ok 228/316“ ist deshalb nicht die Ursache; wichtig ist, wo sie sitzen.

**d) Überschlag (nur Größenordnung, Annahmen):** Kastenträger rund 1,4 m × 1,4 m außen, 0,8 m innen,
I ≈ 0,29 m⁴, E = 200 GPa, Streckenlast ≈ 10 MN/m (563 MN auf 56 m, Annahme gleichmäßig). Bei 17,4 m Spannweite:
beidseitig eingespannt rund 40 mm, frei aufgelegt rund 210 mm. Bei 3 m Spannweite (0169) unter 0,1 mm, dort bestimmen
andere Anteile die 19 mm. Größenordnung 200 mm bei 17 m freier Strecke ist also mechanisch plausibel.

### Ergebnis 1

Die 190–290 mm sind **echte Biegeverformung im Modell**, aber eine **Folge der Stützanordnung**: Auf der langen Spulenform
bleibt eine 12–17 m lange Strecke ohne Verbinder und ohne Lager. Kein Starrkörper, keine losen Gruppen, kein Lösungsfehler.
Die Spannungen dieser Spulen (Stahl p99 der Spule 900–1450 MPa) hängen an derselben Lücke. Damit ist die Rangfolge der Sätze
nach Stahl und Auslenkung (B-033) vor allem ein Urteil über den Verbinderplan, nicht über den Spulensatz.

### Nur vermutet (nicht geprüft)

- **Vermutung:** In der Lücke stehen die Nachbarspulen nicht „seitlich“ (Verbindungslinie nicht quer zu b, oder die Bahnen
  laufen auseinander). Dann findet die Querbedingung dort keinen Ort. Nicht nachgemessen, welche der drei Teilbedingungen dort scheitert.
- **Vermutung:** Verbinder nach Lücken setzen (größte ungestützte Bogenlänge zuerst schließen, ggf. mit lockerer Querbedingung
  oder längerem Verbinder) senkt u_max bei dje/dyu in die Größenordnung von DP9. Nicht gerechnet; das steht schon als offener
  Punkt in ERINNERUNGEN („Verbinder nach Lücken statt nach Abstand setzen“).
- Ob eine 17-m-Strecke in einer echten Anlage ungestützt bliebe, ist eine Konstruktionsfrage (Stellaris: Platten 0,7–1 m
  zwischen den Spulen, innere Stützringe, B-030), keine Frage des Spulensatzes.

## 2. Submodell: Reparatur wiederverwendet

### Änderung am Code

- `stellarator/kopplung.py`: Die Reparaturschleife aus `struktur_netz` ist jetzt die Funktion
  `reparieren(netz, spulen, W, bauen, runden_max=6, je_station=False)`. `struktur_netz` ruft sie wie bisher auf
  (nur bei `biegung=innenkontur`, `reparatur.json` wie bisher).
  - `je_station=False` (Gesamtmodell): Verhalten wie vorher, Faktoren multiplizieren sich. Geprüft: dje 0000 und 0001 neu
    vernetzt, Knoten gleich struktur.vtu bis 3,6e-15 m, reparatur.json gleich (1 Runde, 0 negativ), Verbinder 228/316 und 232/316 gleich.
  - Neu: Verbinder-Elemente (spule = −1) werden übersprungen. Vorher hätte ein negatives Verbinder-Element die Wände der
    **letzten** Spule gedünnt (Index −1). Kommt in kopplung praktisch nicht vor, weil solche Verbinder verworfen werden.
- `stellarator/submodell.py`: Statt Abbruch ruft das Submodell `kp.reparieren([s2], [w2], ..., je_station=True)` und
  bricht nur ab, wenn danach noch negative Elemente bleiben. In ergebnis.json steht neu `"reparatur"`:
  negativ vorher/nachher, Runden, größte relative Wandminderung, Zahl geänderter Stationen.
- Warum `je_station=True`: Mit der alten Multiplikation dünnte eine Runde im feinen Netz (16×16 Zellen quer, 4-mal mehr
  Stationen) die Wand an einer Station um **93 %** (dje 0000, 43 negative Elemente). Mit `je_station=True` höchstens 20 % je
  Station und Runde.

### Geprüft (Submodell, F = 4, Wand 4, WP 6, Ausgabe nur in der Kopie)

| Fall | Spule | negativ vorher → nachher | Runden | Wand max. dünner | Stationen geändert | Stahl p99 Stufe 1 → Submodell | u mm |
|---|---|---|---|---|---|---|---|
| dje 0000 | 8 | 43 → 0 | 3 | 49 % | 44 von 408 | 896 → 986 | 241 → 260 |
| dje 0001 | 18 | 20 → 0 | 4 | 59 % | 37 | 756 → 830 | 206 → 220 |
| dyu 0020 | 14 | 11 → 0 | 2 | 36 % | 7 | 1454 → 1598 | 193 → 215 |

**Kontrolle F = 1** (gegenprobe_0169_duenn 20, Spule 8, Wand 2, WP 4): Stufe 1 392,855 MPa, Submodell **392,850 MPa**,
gleich dem alten Ergebnis (392,8504). Keine negativen Elemente, Reparatur greift nicht.

Die betroffenen Spulen sind genau die Lücken-Spulen aus Teil 1 (dje Spule 8/18, dyu Spule 14). Die Submodell-Werte
erben also die Lücke aus Stufe 1; feiner rechnen ändert daran nichts (+10 %).

### Grenzen und offene Punkte

- Die Reparatur macht die Wand im Submodell örtlich bis 59 % dünner als in Stufe 1. An diesen Stationen ist das Submodell
  **nicht mehr dieselbe Geometrie** wie das Gesamtmodell, die Randverschiebungen kommen aber aus dem dickeren Gesamtmodell.
  Bei dje betrifft das rund 10 % der Stationen. Die Werte sind deshalb als Näherung zu lesen.
- **Vermutung:** Die negativen Elemente entstehen in engen Biegungen, wo der Spline mit F = 4 die Bahn enger macht als die
  groben Stationen; dann ist die Innenwand dicker als der örtliche Krümmungsradius. Nicht nachgemessen.
- Nebenwirkung (nicht geändert): `submodell` ruft `kp.struktur_netz` auf und schreibt dabei verbinder_plan.json,
  biegegrenze.json und ggf. reparatur.json im Ordner des Gesamtmodells neu (Zeitstempel 13:35/13:36 nach struktur.vtu 13:30).
  Geprüft für dje 0000 und 0001: Neubau mit dem geänderten Code ergibt dieselben Dateien (reparatur.json und biegegrenze.json
  bytegleich, verbinder_plan.json 228 Einträge, größte Abweichung 6e-16, Rundung). Für dyu/dsd nicht geprüft.
- Die Kette (kette13.sh) wurde nicht neu gestartet; die Submodelle unter sim/submodell/ für dje/dyu fehlen dort weiter.
