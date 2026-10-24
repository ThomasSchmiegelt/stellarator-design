# stellarator-design

**Stellarator-Entwurf mit offenen Werkzeugen: vom benötigten Magnetfeld zur Spulengeometrie, geprüft mit Feldlinien, FEM und CAD.**

*English summary:* Open-source workflow for stellarator magnet design. Instead of starting from coils, the
design question is inverted: *which magnetic field is needed, and which coil geometry produces it?*
Stage 1 optimizes the plasma boundary (DESC, GPU), stage 2 finds coils that produce that field
(simsopt), stage 3 independently verifies field lines, rotational transform, forces and coil
clearances, builds the winding-pack geometry (STL/STEP) and runs 3-D magnetostatics in ElmerFEM.
Validated on the real Wendelstein 7-X coil set. Documentation is in German.

![W7-X: Feldlinien in den 70 Wickelpaketen](docs/bilder/w7x_feldlinien_3d.png)

---

## Worum geht es?

Ein Stellarator schließt ein heißes Plasma allein mit äußeren, verdrillten Magnetspulen ein. Ob
das gelingt, entscheidet die Form des Magnetfelds, also Flussflächen, Rotationstransformation iota
und Einschlusseigenschaften. Die Spulen sind nur das Mittel dazu. Dieses Projekt baut deshalb
einen durchgehenden, nachvollziehbaren Rechenweg auf:

1. **Welches Magnetfeld wird gebraucht?** Aus physikalischen Zielen wird eine Plasmaform optimiert.
   Ziele sind Quasisymmetrie, Seitenverhältnis und iota.
2. **Welche Spulen erzeugen dieses Feld?** Spulenkurven werden so optimiert, dass das Feld
   tangential zum Plasmarand verläuft (B·n ≈ 0). Dabei gelten technische Grenzen:
   Länge, Krümmung und Abstände.
3. **Stimmt es, und lässt es sich bauen?** Eine unabhängige Prüfung umfasst
   - Biot-Savart, Feldlinien und Poincaré-Schnitte,
   - iota, intakte Flussflächen, Spiegelverhältnis, B_max an den Spulen und Lorentzkräfte,
   - die Spaltprüfung zwischen den Wickelpaketen,
   - die Volumengeometrie (STL/STEP) und die FEM-Magnetostatik in ElmerFEM.

Als Referenz und zur Validierung dient der reale Spulensatz von **Wendelstein 7-X** (70 Spulen).
Erstes Entwurfsziel ist ein **kompakter, quasi-axisymmetrischer Stellarator** mit 2 Feldperioden.

Die Werkzeugkette ist für die Steuerung durch KI-Agenten gebaut (Hermes, PI, Claude Code):
- Jeder Schritt ist ein Kommandozeilenaufruf mit JSON-Ein- und Ausgabe.
- Lange Rechnungen laufen losgelöst.
- Befunde und Übergaben stehen in `BEFUNDE.md` und `ERINNERUNGEN.md`.

> **Hinweis:** Lern- und Forschungsprojekt. Die Ergebnisse sind keine Auslegung einer realen Anlage.
> Querschnitte der Wickelpakete, Supraleiter und Strukturmechanik sind noch nicht ausgelegt.

---

## Ergebnisse

### Kompakter quasi-axisymmetrischer Stellarator (inverse Kette)

Zielform: DESC-Referenz *precise QA* (nfp = 2, Seitenverhältnis 6, iota ≈ 0,42), skaliert auf R0 = 1 m und B0 = 1 T.

| | |
|---|---|
| ![Spulen und Restfehler B·n](docs/bilder/qa_stufe2_spulen.png) | ![Poincaré-Schnitt und iota](docs/bilder/qa_poincare.png) |
| **Stufe 2:** 16 Spulen (4 Basisspulen + Symmetrie), Restfehler \|B·n\|/\|B\| im Mittel 0,24 %, max. 1,0 % | **Stufe 3:** geschachtelte Flussflächen, iota 0,421 → 0,415 (Ziel 0,42) |

![Kompakter QA-Stellarator: Feldlinien und Spulen](docs/bilder/qa_feldlinien_3d.png)

| Kennzahl | Wert |
|---|---|
| Restfehler \|B·n\|/\|B\| auf dem Plasmarand | 0,24 % (Mittel), 1,0 % (max.) |
| iota Achse → Rand (unabhängige Feldlinienrechnung) | 0,421 → 0,415 |
| Spiegelverhältnis auf der Achse | 0,16 % (Kennzeichen der Quasi-Axisymmetrie) |
| Spule–Plasma / Spule–Spule (Mittellinie) | 0,30 m / 0,10 m |
| Gesamtlänge der 4 Basisspulen, kleinster Biegeradius | 18,0 m, 0,18 m |

### Wendelstein 7-X (Validierung mit realen Spulen)

| | |
|---|---|
| ![70 Wickelpakete](docs/bilder/w7x_wickelpakete.png) | ![Poincaré W7-X](docs/bilder/w7x_poincare_bewertung.png) |
| 70 Wickelpakete (0,192 × 0,160 m), kollisionsfrei, min. Spalt 68 mm | Bohnenförmige Flussflächen, 5/5-Inselkette bei iota = 1 |

| Kennzahl (Standardkonfiguration, mittleres \|B\| auf der Achse = 2,5 T) | Wert |
|---|---|
| Strom je Windung (NPC, 108 Windungen) | 13,49 kA |
| \|B\| auf der Achse min / Mittel / max | 2,40 / 2,50 / 2,62 T |
| iota Achse → letzte intakte Fläche (r_eff 0,57 m) | 0,858 → 0,921 |
| B_max an der Wickeloberfläche (Filament-Biot-Savart) | 4,52 T |
| Netto-Lorentzkraft NPC1 | 2,05 MN |
| kleinster Spalt zwischen Wickelpaketen | 68 mm (NPC2–NPC3) |

**ElmerFEM gegen Biot-Savart (alle 70 Spulen, 3,28 Mio. Tetraeder):** |B| auf der Achse 2,504 T gegenüber
2,501 T, Abweichung im Median 0,24 % und höchstens 1,1 %. Nahe den Spulen liegt sie bei etwa 5 %, das
entspricht der Netzweite von 5 cm.

| | |
|---|---|
| ![Elmer vs. Biot-Savart](docs/bilder/elmer_70_spulen_vergleich.png) | ![Feld und Kräfte auf den Spulen](docs/bilder/w7x_B_kraefte.png) |

Weitere Bilder: [Voxel-FFT-Solver gegen Biot-Savart](docs/bilder/w7x_voxelsolver_validierung.png),
[Poincaré Biot-Savart/Voxel](docs/bilder/w7x_poincare_biotsavart_voxel.png),
[PicoGK-Gehäuse](docs/bilder/w7x_picogk_gehaeuse.png).

---

## Aufbau

```
stellarator/                 Bestandspipeline (.venv)
  spulen.py                  Spulensätze (W7-X aus Fourier-Daten oder Datei), Biot-Savart (numba),
                             Kalibrierung, Wickelpaket-Netz
  feldlinien.py              Feldlinienverfolgung (RK4 in phi), Poincaré, iota
  bewerte.py                 Bewertungsfunktion Fall → Kennzahlen (~4–10 s), Schnittstelle für Optimierer/Agenten
  ansicht.py                 3D-Feldlinien + Spulen → ParaView (.vtm) und PNG
  cad.py                     Wickelpakete als STL/STEP (gmsh/OpenCASCADE), Spaltprüfung, Elmer-Netz
  elmer.py                   ElmerFEM-Magnetostatik (CoilSolver + WhitneyAV), Vergleich mit Biot-Savart
  lauf.py                    Gesamtpipeline W7-X (Geometrie → PicoGK-Voxel → FFT-Solver → Feldlinien → Kräfte)
  voxelsolver.py, picogk_bruecke.py   FFT-Voxel-Feldlöser, Anbindung an PicoGK
  faelle/*.json              Falldateien (Eingabe)
  daten/W7-X.dat             W7-X-Spulenfilamente (aus simsopt, MIT), siehe daten/QUELLE.md
invers/                      Inverser Entwurf (.venv-opt)
  stufe1_desc.py             Stufe 1: Plasmaform mit DESC (GPU)
  stufe2_spulen.py           Stufe 2: Spulenoptimierung mit simsopt
  beispiele/                 Spulensatz zur Referenzform precise QA (Austauschformat spulen.json)
picogk/StellaratorVoxel/     PicoGK-Headless-App (C#/.NET 9): Voxelkörper, Gehäuse, SDF
sim/pipeline/gerader_draht/  Validierung ElmerFEM gegen analytischen Draht (2D)
forschung/                   Recherche und Analysen
docs/bilder/                 Bilder für dieses README
BEFUNDE.md                   Befund-Log: Beobachtung, Messung, Fundstelle, Status (inkl. gefundener Fehler)
ERINNERUNGEN.md              Entscheidungen, nächste Schritte, Übergabe an Agenten
```

Rechenergebnisse (`sim/stellarator/`, `sim/invers/`) sind nicht im Repository. Sie sind groß und lassen sich reproduzieren.

## Installation

Linux, Python 3.12. Für Stufe 1 ist eine NVIDIA-GPU empfohlen.

```bash
# Bestandspipeline
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# Inverser Entwurf: EIGENE Umgebung (andere numpy/JAX-Versionen)
python3 -m venv .venv-opt && .venv-opt/bin/pip install -r requirements-opt.txt
```

Systemwerkzeuge:
- **ElmerFEM 9.0** (Ubuntu-PPA `elmer-csc-ubuntu`), für `stellarator.elmer`,
- **ParaView** zum Ansehen,
- optional **PicoGK** mit .NET 9, für `stellarator.lauf` im Voxelmodus.

Referenzrechner: 32 GB RAM, RTX 3090 (24 GB).

## Schnellstart

```bash
# W7-X bewerten (Feldlinien, iota, Kräfte, Spalt) – ~10 s
.venv/bin/python -m stellarator.bewerte stellarator/faelle/w7x_standard.json --bild
# Variante: Planarspulen bestromen
.venv/bin/python -m stellarator.bewerte stellarator/faelle/w7x_standard.json --name pc_plus --bild \
    --setze spulen.stroeme_Awdg.PCA=200000 --setze spulen.stroeme_Awdg.PCB=200000
# 3D-Feldlinien ansehen
.venv/bin/python -m stellarator.ansicht stellarator/faelle/w7x_standard.json --oeffnen

# Inverse Kette: kompakter QA-Stellarator
.venv-opt/bin/python invers/stufe1_desc.py --name qa_nfp2                     # Plasmaform (GPU, ~20–40 min)
.venv-opt/bin/python invers/stufe2_spulen.py --wout sim/invers/qa_nfp2/wout_qa_nfp2.nc --name qa_nfp2_spulen
.venv/bin/python -m stellarator.bewerte stellarator/faelle/ref_precise_QA.json --bild   # Prüfung des mitgelieferten Beispiel-Spulensatzes

# FEM: ElmerFEM mit allen 70 W7-X-Spulen (~12 min, ~10 GB RAM)
.venv/bin/python -m stellarator.elmer sim/stellarator/elmer_w7x_70 --spulen 70 --B0 2.5 --h_spule 0.05 --h_luft 0.8
```

## Validierung und gefundene Fehler

Das Projekt dokumentiert offen, was geprüft wurde und was sich als falsch herausgestellt hat (`BEFUNDE.md`):

- **Analytisch:** ElmerFEM gegen den geraden Draht (2D). Der Elmer-Referenzfall läuft durch (TEST.PASSED), Abweichung ≤ 2 %.
- **Voxel-FFT-Solver gegen Biot-Savart:** auf den Flussflächen Median 0,25 %.
- **ElmerFEM 3D gegen Biot-Savart:** Einzelspule mit Netzkonvergenz 7 % → 2,8 % → 1,9 %. Alle 70 Spulen: 0,24 % auf der Achse.
- **B-011:** Ein früheres parametrisches Modell war keine Stellarator-Topologie. Es wurde verworfen und durch die realen W7-X-Filamente ersetzt.
- **B-016:** Die übernommene Referenzachse hatte in Z das falsche Vorzeichen. Dadurch war die Stromkalibrierung um 10 % zu niedrig (12,18 statt 13,49 kA). Die Achse wird jetzt als Fixpunkt der Feldlinienabbildung bestimmt.
- **B-016:** Der Elmer-CoilSolver ignoriert das Vorzeichen der Stromvorgabe. Mittelpunkt und Normale je Spule werden deshalb jetzt explizit vorgegeben, und die Stromrichtung wird automatisch geprüft.

## Stand und nächste Schritte

- [x] W7-X: Geometrie, Feld, Feldlinien, Kräfte, Spalt, CAD/STL, ElmerFEM (70 Spulen)
- [x] Bewertungsfunktion als Optimierungsschnittstelle
- [x] Inverse Kette Plasmaform → Spulen → Prüfung (an der Referenz precise QA verifiziert)
- [ ] Eigene Plasmaform optimieren (Stufe 1 `qa_nfp2`), Spulen dazu
- [ ] Größe (R0) und Feld (B0) festlegen, Wickelpakete und Stromdichte auslegen
- [ ] Studien-Runner (Agent wählt Ziele, numerischer Optimierer rechnet)
- [ ] Gehäuse und Stützstruktur, Spannungen in Elmer aus den Lorentzkräften
- [ ] Allgemeiner Weg STL → STEP

## Quellen und Danksagung

- W7-X-Spulenfilamente und Referenzachse: [simsopt](https://github.com/hiddenSymmetries/simsopt) (MIT), Spulensatz `w7x_v001` (IPP).
- Plasmaform-Optimierung: [DESC](https://github.com/PlasmaControl/DESC). Spulenoptimierung: simsopt.
- FEM: [ElmerFEM](https://www.elmerfem.org). Netze/CAD: [gmsh](https://gmsh.info). Voxel: [PicoGK](https://github.com/leap71/PicoGK).

## Lizenz

[MIT](LICENSE) © 2026 Thomas Schmiegelt
