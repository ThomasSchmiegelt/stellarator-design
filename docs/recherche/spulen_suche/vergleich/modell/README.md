# Modell beider Stellaratoren: Gefaess, Plasma, Spulen (3D)

Erzeugt mit `stellarator/modell_bauen.py` (Netze, Pruefung), `stellarator/modell_freecad.py` (FCStd), `stellarator/modell_bilder.py` (Bilder). Kennzahlen: `kennzahlen_k3_halb.json`, `kennzahlen_datj5fc.json`.

## Was modelliert ist
| | Kandidat 3 halb | DATJ5FC |
|---|---|---|
| Form | eigene Form (aus Datensatzform Do3Qy, halber Schritt) | Datensatzform (ConStellaration), unveraendert |
| Feldperioden nfp | 2 | 4 |
| Spulensatz | `sim/kette_k3/stage2/satz_d100_n10_lr_s56` | `sim/kette_k3/datj/satz_d100_n5_lr_s56` |
| Massstab L (m je Einheit) | 13,61 | 16,42 |
| Rohr-Plasma, kuerzester Abstand | 1,705 m | 1,341 m |
| Gefaess aussen - Rohroberflaeche | 1,455 m | 1,091 m |
| Durchdringung Rohr/Gefaess | nein | nein |
| Wasserdicht (Plasma, Gefaess, 40 Rohre) | ja, ja, 40/40 | ja, ja, 40/40 |

## Annahmen (alle angenommen, nicht belegt)
- Anlagenmassstab a = 1,80 m; Rohrdurchmesser 0,852 m (flaechengleich zum quadratischen Wickelpaket 0,7552 m, wie `k3_rohr.py`). Rohr = Kreisquerschnitt um die Spulenmittellinie, keine Wicklungsdetails.
- **Vakuumgefaess/Erstwand ist eine ANNAHME:** innen 0,15 m ueber der Plasmarandflaeche (Spalt wie in `vergleich_kuehlung.py`), Wand 0,10 m, also Schale zwischen 0,15 und 0,25 m Abstand entlang der Flaechennormale. Keine Kuehlkanaele, keine Stutzen, keine Festigkeitsrechnung.
- Plasma = aeusserste Flaeche (LCFS) aus `frei/wout/k_n48000.nc` (freie Grenze mit den Spulen, 48000 Schritte), mal L.
- Die Spulenrohre sind fuer die Dateien auf 30000 Dreiecke je Rohr reduziert (Abweichung zum Original bis 1,8 cm, aus 4 Rohren gemessen); die Abstaende oben sind mit den vollen Netzen (ca. 350000 bis 420000 Dreiecke je Rohr) gerechnet.
- Rohre: STL der Basisspulen einer halben Periode (PicoGK, Millimeter), per Drehung um z (2 pi k/nfp) und Stellaratorsymmetrie (x,y,z) -> (x,-y,-z) auf alle 40 Spulen vervielfaeltigt. Gegenprobe: Volumenschwerpunkt jedes Rohrs gegen den Schwerpunkt der Spulenkurve aus `biot_savart.json` mal L: groesste Abweichung 0,17 cm (K3) und 0,18 cm (DATJ5FC), eineindeutig zugeordnet.
- Offset-Pruefung: alle Punkte der Gefaessflaechen haben vom (dichter gerechneten) Plasmagitter den Abstand 0,150 bzw. 0,250 m (Abweichung unter 1e-12 m); das schliesst Faltungen/Selbstschnitt der Offsetflaeche an engen Stellen aus. Durchdringung: keine von 1,7 Mio. Stichprobenpunkten der Rohroberflaechen liegt in der Gefaesswand oder im Gefaess.

## Lesehilfe zu den Bildern (fuer Maschinenbauer)
Alle Bilder: Parallelprojektion (kein Perspektivverzug), gleicher Massstab fuer beide Anlagen. Orange-rot = Plasma (das Volumen, in dem die Fusion laeuft), grau = Vakuumgefaess (die Wand um das Plasma, duenn), kupfer = Spulenrohre (die Magnete, die das Plasma in Form halten). Bei den Ringbildern sind die Spulen halbtransparent.
- `k3_halb_ring.png`, `datj5fc_ring.png`: Schraegansicht des ganzen Rings. Das Plasma ist ein verdrehter Schlauch, der sich zu einem Ring schliesst (K3: 2 Perioden, DATJ5FC: 4). Die Spulen sind geschlossene Schleifen, die das Plasma umschlingen; sie bilden einen Kafig, wie die Rippen eines Gehaeuses.
- `k3_halb_viertel.png`, `datj5fc_viertel.png`: Ein Viertel des Rings (Quadrant x>0, y>0 von oben gesehen) ist weggeschnitten; Gefaess und Plasma sind mit Schnittflaeche (Deckel) zu sehen, die Spulen im Viertel sind entfernt. Man sieht: Das Plasma liegt innen, das graue Gefaess ist eine duenne Huelle direkt darum, die Spulen liegen weit ausserhalb (Meter, nicht Zentimeter). Die Schnittflaechen sind unregelmaessig, weil der Querschnitt entlang des Rings seine Form aendert (dreieckig bis elliptisch).
- `vergleich_beide.png`: beide Anlagen nebeneinander, gleiche Kamera. DATJ5FC hat die groessere Gesamtgroesse (L 16,4 gegen 13,6 m je Einheit) und ist regelmaessiger (4 gleiche Perioden); K3 ist ein Zweiperiodenring mit staerkerer Verdrehung.
Abstaende im Bild: Rohr-Plasma 1,7 m (K3) und 1,34 m (DATJ5FC), das ist deutlich mehr als die Schlauchdicke (Plasma-Querschnitt ca. 3,6 m Durchmesser).

## FCStd-Dateien oeffnen
Ablage neben den STL: `sim/kette_k3/vergleich/modell/k3_halb/k3_halb.FCStd`, `.../datj5fc/datj5fc.FCStd` (STL zu gross fuer das Repo, daher nicht in docs).
Oeffnen: FreeCAD 1.1 (AppImage `~/Applications/FreeCAD_1.1.4.AppImage`) starten, Datei > Oeffnen. Drei Mesh-Objekte: Plasma, Gefaess, Spulenrohre (Einheit mm, auf Meter umgerechnet: 1000 mm = 1 m). Die Farben (Plasma orange-rot 50 % transparent, Gefaess grau 60 %, Spulen kupfer) sind von Hand in die Datei geschrieben und im Konsolenmodus nicht pruefbar; falls FreeCAD sie nicht uebernimmt, im Baum Objekt waehlen > Eigenschaften > View > Shape Color / Transparency setzen. Die Netze sind Dreiecksnetze (kein Volumenkoerper); fuer CAD-Operationen Mesh > Form aus Netz umwandeln (bei 1,2 Mio. Dreiecken langsam, besser zuerst Netz vereinfachen).
Die STL-Dateien (`plasma.stl`, `gefaess.stl`, `spulen.stl`, Meter) lassen sich auch in Blender, MeshLab oder PicoGK laden.
