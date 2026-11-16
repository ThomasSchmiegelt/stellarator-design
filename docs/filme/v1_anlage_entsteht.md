# Video V1 · Die Anlage entsteht (gerenderte Geometrie)

> **KI-generiert** (Claude Sonnet 5.5 und Claude Opus 5.5, 2026-11-15/16) · Status **Entwurf** · Freigabe des Autors für die Veröffentlichung 2026-11-16 („passt so“).
> Datei `docs/filme/v1_anlage_entsteht.mp4`, 70 s, 1920×1080, 30 fps. Im Bild steht nur „Thomas Schmiegelt“ (Ausnahme: Farbleiste in Teil 3).
> Herkunft Plasma: Datensatzform DGozX5fj (ConStellaration), unverändert, auf volle Größe skaliert. Alle Zahlen stehen nur hier, je Zahl mit Quelldatei.

## Ablauf
| Teil | Dauer | Inhalt |
|---|---|---|
| 1 | 16 s | Plasma, Poincaré-Punkte, Teilchenbahnen |
| 2 | 36 s | Würfelaufbau der ganzen Anlage → Würfel lösen sich in die glatten Flächen auf → Schnitt durch die Anlage |
| 3 | 18 s | Festigkeit: Vergleichsspannung auf dem Tragwerk |

## Begleittext
**Teil 1 · Plasma.** Plasmarand der Datensatzform DGozX5fj, unverändert, auf volle Größe skaliert (Faktor k = 28,517; `sim/kandidat/K2e/lauf/C/k2_end/P1.json`). Farbe = Höhe z. Die Punkte sind Poincaré-Punkte der Feldlinien in zwei Ebenen (`sim/kandidat/K2e/lauf/C/baustein_k2/poincare_punkte.vtk`, Farbe = Startfläche s). Danach (zweite Hälfte der Szene) die Bahnen von 12 Alphateilchen (Führungszentrum, Vakuumfeld, aus `sim/kandidat/K3/lauf/lauf_bahnen/bahnen.npz`, erzeugt von `stellarator/alpha_bahnen.py` Funktion `bahnen`, Rechnung K3, nichts neu gerechnet; Einheit m, Punkte je Bahn 1157–2180). Das Feld der Bahnen bleibt in der Datei unbenannt (offen). Die Datei enthält ein Verlustkennzeichen je Bahn: alle 12 Bahnen sind darin „nicht verloren“, deshalb eine Farbe je Bahn (Regenbogen, kein Verlust-/Gefangen-Unterschied); der Verlustanteil 15,0 % (s_Start 0,25, 60 von 400, Spulenfeld) stammt aus `sim/kandidat/K3/ERGEBNIS.md`, nicht aus diesen 12 Bahnen. Die Flächen bleiben geschlossen, Rotationstransformation siehe `sim/kandidat/K2e/lauf/C/k2_end/P2.json`.

**Teil 2 · Die Anlage entsteht.** Die Anlage wird zuerst vollständig und ungeschnitten aus 1057044 Würfeln (Kantenlänge 0,30 m, ganzer Umfang) aufgebaut: Plasma, Erste Wand, Blanket, Abschirmung, Vakuumgefäß, dann die 48 Spulen mit Gehäuse. Aufbau und Dicken: Plasma bis Außenfläche Vakuumgefäß + Spalt 2,03 m (`sim/kandidat/K10/varianten/V1/K10/kollision.json`; kumuliert Erste Wand 0,03 m, Blanket 0,83 m, Abschirmung 1,53 m, Vakuumgefäß 1,83 m). Die Erste Wand (0,03 m) ist dünner als ein Würfel und erscheint daher nicht als eigene Lage; der Spalt bleibt leer. Voxel aus den STL-Schichten, Voxelgröße ist eine Bildwahl (Erwartung 0,3–0,6 m). Danach lösen sich die Würfel in zufälliger Reihenfolge auf; darunter erscheinen die glatten Flächen. Die Würfel gehen in die glatten Flächen derselben STL-Dateien über (`sim/kandidat/K10/varianten/V1/K10/*.stl`), Schnitt bei y = 0, Farben je Schicht wie in K10. Kryostat und Biologischer Schild sind Platzhalter (Annahme, `sim/kandidat/K10/varianten/V1/K10/ERGEBNIS_K10.md`); Kryostat 95,5 m Durchmesser, 74,3 m Höhe (`kollision.json`). Zum Schluss: Eine Schnittebene (y = const) fährt von außen bis zur Mittelebene y = 0 durch Biologischen Schild, Kryostat, Spulengehäuse und Spulen, Vakuumgefäß, Abschirmung, Blanket, Erste Wand bis ins Plasma; Farben je Schicht wie K10. Die Querschnitte der Schichten sind als gefüllte Flächen berechnet (Schnitt der STL-Flächen), Kryostat und Schild sind Platzhalter (siehe oben).

**Teil 3 · Festigkeit.** Von-Mises-Vergleichsspannung auf dem Tragwerk (Stahlgehäuse und Verbinder), Rechnung K8 Variante V1 (`sim/kopplung/k8_dgoz_v1/punkte/0000/struktur.vtu`, Feld `vonmises_MPa`, Einheit MPa). Das Einwachsen ist eine Darstellung: das gerechnete Feld wird von 0 auf 100 % skaliert, es ist keine zeitliche Rechnung. Farbskala fest 0–800 MPa. Die Marke bei 500 MPa ist eine Annahme (`sim/kopplung/k8_dgoz_v1/punkte/0000/ergebnis.json`, bewertung/annahmen: a: ITER-Kriterium 2/3 Sy, Guete C3 (Sy>750 MPa); C1 waere 667 MPa). Heißeste Spule ohne Randzone: Spule 26, p99 ohne Randzone 479,9 MPa, 20,1 MPa Abstand zu 500 MPa (`ergebnis.json` bewertung/stahl_heiss). Größte Verschiebung 41,2 mm (`ergebnis.json` struktur/u_max_mm); Stahl max 1227 MPa, p99 415 MPa; Verbinder max 826 MPa (dito).

Hinweis: K8 rechnet mit Spulenstrom und Wickelpaket aus K8 (Strom je Spule 26,8 MA, Wickelpaket 0,90 m; `ergebnis.json` struktur), die Spulenrechnung K2e mit mittlerem Strom 23,7 MA und Wickelpaket 1,26 m (`k2_end/P3.json`). Der Unterschied ist nicht aufgelöst.

## Lesehilfe
- **Poincaré-Punkte:** Durchstoßpunkte der Magnetfeldlinien durch eine Ebene. Liegen sie auf geschlossenen Ringen, sind die Feldlinien sauber eingeschlossen.
- **Teilchenbahnen:** Wege schneller Alphateilchen aus der Fusion. Sie sollen im Plasma bleiben und es heizen.
- **Würfel (Voxel):** Die Anlage wird zuerst aus gleich großen Würfeln aufgebaut, so wie ein Rechennetz sie sieht; danach die glatten Konstruktionsflächen.
- **Von-Mises-Spannung:** eine Vergleichszahl für die Belastung des Stahls. Rot ist hoch, Blau niedrig.

## Offen
- Teilchenbahnen: nur 12 Bahnen in der Datei, keine als verloren gekennzeichnet; Feld der Bahnen (Spulen- oder VMEC-Feld) aus der Datei nicht ersichtlich.
- Strom und Wickelpaket: K8 und K2e weichen ab (siehe Teil 3).
- Kryostat und Schild sind Platzhalter ohne Wandstärke.

Skript: `video/bausteine/V1/baue.py` (lokal, nicht im Repo).

---
*KI-generiert (Claude Sonnet 5.5 / Opus 5.5). Status Entwurf.*
