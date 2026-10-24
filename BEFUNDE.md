# BEFUNDE — fusion (Stellarator)

> Chronologisches Befund-Log. Format: **Beobachtung, Messung, Fundstelle, Status**
> Eintrag oben = neuer. Status: ✅ gesichert · ⏸ blockiert · ⚠ zu prüfen

---


### B-018 | Auslegung auf 1 GW netto: Stufe 0 (Leistungsbilanz) + eigene Form qa_nfp2 (2026-10-24)
- **Beobachtung:** Eigene Plasmaform `qa_nfp2` (DESC, nfp=2, A=6) erreicht qs_fehler 1,3e-5
  (Referenz precise_QA 5,8e-5), iota 0,423→0,415. Spulen (Variante `mittel`, abstand_sp 0,18):
  B·n 0,11 % Mittel / 0,40 % max. Neue Stufe 0 (`invers/stufe0_bilanz.py`) legt R0/B0 aus der
  Netzleistung aus; Stufe 3 in voller Groesse bestaetigt die Auslegung.
- **Messung (1000 MW netto → P_fus 3,05 GW, P_th 3,42 GW, eta 0,35, Eigenbedarf 197 MW):**

  | | HTS (≤ 20 T, j 40 A/mm²) | Nb3Sn (≤ 12 T, j 15 A/mm²) |
  |---|---|---|
  | R0 / a / B0 | 12,1 m / 2,0 m / 7,5 T | 22,2 m / 3,7 m / 4,8 T |
  | begrenzt durch | Einschluss (H_ISS04 1,3) + Wandlast 2,0 MW/m² | Einschluss + Leiterfeld |
  | <β>, n, T0 | 2,5 %, 2,2e20, 14 keV | 2,5 %, 0,9e20, 14 keV |
  | Stufe 3: Strom je Spule | 31,0 MA | 36,4 MA |
  | Stufe 3: B am Leiter (×B0) | 17,7 T (2,36) | 11,6 T (2,41) |
  | Stufe 3: Spalt Wickelpakete | 0,58 m (Paket 0,88 m) | 1,13 m (Paket 1,56 m) |
  | Stufe 3: Netto-Kraft je Spule max. | 2200 MN | 3000 MN |
  | Flussflaechen / iota / Spiegel | 12/12, 0,422→0,411, 0,08 % | gleich (Form skaliert) |

- **Wichtige Lehren:**
  1. Feld am Leiter ist NICHT ~2×B0 pauschal: erste Spulen (abstand_ss 0,10) gaben 3,5×B0 (eng
     beieinanderliegende Wickelpakete). Variante `mittel` (Spulen weiter auseinander) 2,4×B0.
     Spulennaeher ans Plasma (abstand_sp 0,12) ging nicht ohne B·n-Verlust (L14: 0,7 %).
  2. Spulenstrom ist durch Ampere festgelegt (2πR0B0/µ0/N × 1,09), unabhaengig von der Spulenlage.
  3. Bei Nb3Sn dominiert das Eigenfeld des Wickelpakets: mit j=20 A/mm² konvergiert die
     Iteration k_B nicht (B_Leiter bleibt 12,3–12,5 T, egal wie klein B0) → j=15 A/mm².
  4. Kraefte ~1000× W7-X (2 MN): Stuetzstruktur ist das Hauptproblem der Baubarkeit.
  5. Bekannte Studien zum Vergleich (aus dem Gedaechtnis, ungeprueft): HELIAS 5-B R0 ≈ 22 m,
     B0 ≈ 5–6 T (Nb3Sn); Stellaris (HTS) R0 ≈ 12–13 m, B0 ≈ 9 T; ARIES-CS R0 ≈ 8 m (A≈4,5).
     Seitenverhaeltnis-Empfindlichkeit (HTS): A=4 → 9,9 m, A=5 → 11,1 m, A=8 → 15 m.
- **Fundstelle:** `invers/stufe0_bilanz.py`, `invers/beispiele/qa_nfp2/` (bilanz_1GW.json, spulen.json),
  Faelle `stellarator/faelle/qa_nfp2_1GW_{HTS,Nb3Sn}.json`, Bilder `docs/bilder/qa_1GW_*`.
- **Fix nebenbei:** `cad.abstaende` filterte Nachbarpaare per Schwerpunktabstand 3 m → bei R0 > 10 m
  keine Paare (IndexError). Jetzt Mittellinien-Abstand ≤ 3×Diagonale; W7-X unveraendert 68 mm.
- **Status:** ✅ 0-D-Auslegung (±30 %), Stufe 3 gesichert. ⚠ Physik von Stufe 0 einfach (ISS04,
  Sudo, keine Zyklotronstrahlung, kein Divertor); Kraefte/Struktur offen.

### B-017 | Inverse Kette funktioniert: Zielfeld (DESC) -> Spulen (simsopt) -> Pruefung (2026-10-24)
- **Beobachtung:** Fuer den kompakten QA-Stellarator (nfp=2, A=6, iota 0,42) laeuft die Kette
  Plasmaform → Spulen → Feldlinien/Geometrie durch. Getestet mit der DESC-Referenzform
  precise_QA (Stufe 1 eigener Lauf `qa_nfp2` laeuft noch). Die Spulen aus Stufe 2 erzeugen in der
  unabhaengigen Pruefung (eigener Biot-Savart, Feldlinien) genau das Zielfeld.
- **Messung:** Stufe 2 (simsopt, 16 Spulen, 4 Basis, 213 s CPU): |B·n|/|B| Mittel 0,24 %, max 1,0 %;
  Laenge 18,0 m (4 Basis); Abstand Spule-Spule 0,100 m, Spule-Plasma 0,300 m; Biegeradius min 0,18 m.
  Stufe 3 (`bewerte`, R0 1 m, B0 1 T, 4 s): iota 0,421 → 0,415 (Ziel 0,42), Spiegelverhaeltnis
  0,16 %, 12/12 Linien auf intakten Flaechen bis r_eff 0,28 m, Spalt (0,04-m-Pakete) 29 mm.
  W7-X-Bewertung nach Verallgemeinerung unveraendert (13,48 kA, iota 0,858 → 0,921, 68 mm).
- **Fundstelle:** `invers/stufe1_desc.py`, `invers/stufe2_spulen.py`, `stellarator/spulen.py`
  (`lade_spulensatz`), `stellarator/faelle/ref_precise_QA.json`, `sim/invers/`,
  `sim/stellarator/bewertung/ref_precise_QA/`. Skill `stellarator-invers`.
- **Status:** ✅ Kette verifiziert an Referenz. ⏳ eigene Plasmaform `qa_nfp2` (Stufe 1, GPU).

### B-016 | Achse falsch (Z-Vorzeichen) → Kalibrierung; Elmer-Stromrichtung; Bewertungsfunktion (2026-10-24)
- **Beobachtung:** (1) `spulen.achse()` (simsopt zoo.py) hat in unserer Spulenkonvention das
  falsche Z-Vorzeichen: bei phi=18°/54° 0,62 m neben der echten Achse (nahe Spulen, |B| 2,87
  statt 2,26 T). Mit −Z stimmt sie auf 0,2 mm mit der verfolgten Achse (Fixpunkt der
  Periodenabbildung). Folge: `kalibriere()` skalierte auf ein falsches Mittel → alle bisherigen
  Stromangaben fuer "<B_Achse> = 2,5 T" zu klein. Korrigiert in `spulen.achse`.
  (2) Elmer-CoilSolver ignoriert das Vorzeichen von `Desired Current Density` und waehlt die
  Richtung selbst → 70-Spulen-Lauf: alle 25 gespiegelten Spulen falsch herum (B Achse 1,38 statt
  2,50 T). Abhilfe: `Coil Center`/`Coil Normal` je Component (Flaechenvektor x sign(I) x
  NORMAL_VZ=−1), J positiv; automatische Pruefung `elmer.richtung_pruefen`.
  (3) Neue Bewertungsfunktion `stellarator/bewerte.py` (~10 s/Fall, nur Biot-Savart).
- **Messung:** Standardfall (B0 = 2,5 T Mittel auf verfolgter Achse): **13,48 kA/Wdg** (bisher
  12,18), |B| Achse 2,40/2,50/2,62 T, Spiegelverhaeltnis 0,043, iota 0,858 → 0,921 (intakte
  Flaechen bis r_eff 0,57 m, dann 5/5-Inseln), B_max Wickeloberflaeche 4,52 T, Spalt 68 mm.
  PCA=PCB=+0,2 MA-Wdg: 12,83 kA, iota 0,796 → 0,932 (r_eff 0,76 m). −0,2 MA-Wdg: 14,21 kA,
  iota 0,934 → 1,028 (r_eff 0,60 m). Elmer-Richtungstest 2 Spulen (n/f): beide korrekt.
- **Fundstelle:** `stellarator/spulen.py` (achse), `stellarator/bewerte.py`, `stellarator/elmer.py`,
  `sim/stellarator/bewertung/bew_*/kennzahlen.json` + `poincare.png`.
- **Status:** ✅ Achse/Kalibrierung, Bewertung. ⚠ Bisherige Zahlen in B-012, Bericht v0.2 und
  `sim/stellarator/w7x_standard/ergebnis.json` (12,18 kA; |B| 2,17/2,50/2,87 T) beruhen auf der
  falschen Achse → Standardlauf (`stellarator.lauf`) neu rechnen, Bericht aktualisieren.
  ✅ Elmer 70 Spulen (korrigierte Richtung, 3,28 Mio. Tets, h_spule 0,05, 680 s, 10,4 GB):
  Stromrichtung alle korrekt; |B| Achse Mittel 2,504 T (Elmer) vs. 2,501 T (Biot-Savart),
  Fehler auf der Achse Median 0,24 %, max 1,1 %; nahe Spulen (0,2–0,8 m) Median 4,6–4,8 %
  (wie Einzelspule bei h 0,05). Kalibrierung mit korrigierter Achse bestaetigt (BS 2,501 T).
  `sim/stellarator/elmer_w7x_70/` (ergebnis.json, erg/feld_t0001.vtu, vergleich_linie.png).
  ✅ Standardlauf neu (`stellarator.lauf`, 2026-10-24, 141 s): 13,49 kA/Wdg (bewerte 13,48),
  B(phi=0) 2,618 T, B_max Wickelpaket (Voxel) 4,33 T, Netto-Kraft NPC1 2,05 MN (alt 1,67;
  Faktor (13,49/12,18)^2 = 1,23 ✓), iota 0,858 .. 1,10 unveraendert. Alt gesichert:
  `sim/stellarator/w7x_standard/ergebnis_alt_achse_falsch_20261023.json`. Bericht-Text noch v0.2.

### B-015 | Geometrie ohne PicoGK baubar: CAD (STEP) + Elmer-Magnetostatik verifiziert (2026-10-24)
- **Beobachtung:** Alle 70 Wickelpakete (0,192 x 0,160 m) lassen sich mit gmsh/OpenCASCADE
  als Volumen bauen (STEP), kollisionsfrei, und in Elmer (CoilSolver + WhitneyAVSolver)
  rechnen. Robust NUR: Rechteckprofil je Filamentpunkt, zwei Haelften als ruled-Loft, fuse.
  Nicht robust: Sweep/addPipe (OCC-Fehler bei 1–3 von 7 Basisspulen), geschlossener Loft,
  glatter Loft (Oberflaechennetz selbstschneidend, "PLC Error").
- **Messung:** Volumen ist/soll 0,997–1,004 (7 Basisspulen, 80–200 Punkte). 390 Nachbarpaare
  ohne Ueberlapp; min. Mittellinienabstand 279 mm (Diagonale Wickelpaket 250 mm); min.
  Biegeradius 0,40 m NPC / 0,58 m PC. Elmer 1 NPC vs. Biot-Savart (5x5 Filamente), Median
  0,2–0,4 m Abstand: 6,8 % (44k Tets, Rand 5 m) → 2,7 % (283k, 26 s, 0,95 GB) →
  1,9 % (869k, 98 s, 2,8 GB); Rand 1,5 m: Fernfeld −37 %. RAM ~3,2 KB/Tet.
- **Fundstelle:** `stellarator/cad.py`, `stellarator/elmer.py`,
  `sim/stellarator/w7x_standard/cad/`, `sim/stellarator/elmer_einzelspule/`.
  Schnelle Spaltpruefung ohne CAD (`cad.abstaende`, 1,5 s statt > 45 min OCC-Boolean):
  min. Spalt 68,3 mm (NPC2–NPC3), keine Durchdringung; Kontrolle 0,40x0,30 m → −104 mm,
  erkannt. → Einzelgehaeuse 60 mm/Seite passt nicht (braucht 120 mm).
- **Status:** ✅ gesichert (Einzelspule). Alle 70 Spulen in Elmer: offen (RAM-Abschaetzung noetig).

### B-014 | PicoGK headless: zwei API-Fehler, Umgehung verifiziert (2026-10-23)
- **Beobachtung:** (1) `Voxels.bIsInside` meldet ~50 % der Aussenpunkte nahe der
  Oberflaeche als „innen" (Belegung 52,9 m3 statt 19,3 m3). `ScalarField.bGetValue`
  liefert dagegen korrekte Abstaende mit richtigem Vorzeichen (auch inaktive Voxel).
  (2) `CalculateProperties` nach Boolean: Gehaeuse 51,6 m3, aus dem Netz 33,3 m3.
- **Messung:** SDF-Diagnose an 7108 Punkten; Belegung PicoGK-SDF 154 640 vs.
  analytisch 154 588 Zellen (0,03 %).
- **Fundstelle:** `picogk/StellaratorVoxel/Program.cs` (SDF-Export statt bIsInside),
  `stellarator/picogk_bruecke.py` (`abstand_python` = Gegenprobe), Skill `picogk-voxel`.
- **Status:** ✅ gesichert, umgangen.

### B-013 | Grenzen: Voxelfeld zerstoert Flussflaechen; B_max unterschaetzt (2026-10-23)
- **Beobachtung:** (a) Voxel-FFT-Feld (h=50 mm, Fehler ~0,25 %) ergibt in der
  Feldlinienverfolgung keine geschlossenen Flussflaechen (iota an der Achse stimmt:
  0,864 vs. 0,858). Ursache: kartesisches Gitter bricht die 5-fache/Stellarator-
  Symmetrie → resonantes Fehlerfeld (W7-X-Toleranz dB/B ~1e-4). Kubische statt
  trilineare Interpolation verbessert nur wenig.
  (b) B_max am Wickelpaket 3,91 T (Voxel) / 4,09 T (Filament-BS an der Oberflaeche)
  vs. Literatur 6,7 T @ 3 T ≈ 5,6 T @ 2,5 T.
- **Messung:** `sim/stellarator/w7x_standard/poincare.png`, `ergebnis.json`
  (rueckfuehrung.B_max_*).
- **Fundstelle:** `stellarator/lauf.py` (feldlinien, rueckfuehrung).
- **Status:** ⚠ offen — (a) Flussflaechen nur mit Biot-Savart; Abhilfe:
  Zylindergitter einer Feldperiode. (b) Mehrfilament-Wickelpaket + realer Querschnitt.

### B-012 | W7-X real: Pipeline Geometrie→PicoGK→Voxelsolver→Feldlinien (2026-10-23)
- **Beobachtung:** Reale W7-X-Filamente (simsopt `W7-X.dat`, CAD-Satz w7x_v001,
  7 Basis → 70 Spulen) liefern die bekannte Physik: bohnenfoermige Flussflaechen,
  iota 0,858 (Achse) … 0,937 (r_eff 0,6 m), 5/5-Inselkette bei iota=1.
  Eigener FFT-Voxelsolver (Hockney) stimmt mit exaktem Biot-Savart ueberein.
- **Messung (w7x_standard, <B_Achse>=2,5 T):** 12,18 kA/Wdg (NPC, 108 Wdg);
  fuer B(phi=0)=2,5 T: 12,9 kA (IAEA ~12,8 kA ✓). |B| Achse 2,17/2,50/2,87 T.
  Voxelsolver vs. BS: Achse max 1,3 %; Flussflaechen Median 0,25 %, max 2,0 %;
  Abstand >0,3 m zum Filament Median 0,25–0,49 %. Loesung 1,4 s (292x296x88).
  Netto-Lorentzkraft NPC1..5: 1,67/1,86/1,91/1,68/1,08 MN; Summe aller 0,05 MN.
  Wickelpaket Soll 19,31 m3, PicoGK-Netz 18,96 m3; Gehaeuse (60 mm) 33,32 m3.
- **Fundstelle:** `stellarator/` (Paket), `stellarator/faelle/w7x_standard.json`,
  `sim/stellarator/w7x_standard/ergebnis.json`, Bericht `bericht/bericht.pdf` (v0.2).
  Start: `.venv/bin/python -m stellarator.lauf stellarator/faelle/w7x_standard.json --bericht`.
- **Status:** ✅ gesichert. Offene Fragen #3/#4 (Elmer-3D-Stromquelle, Mesh) fuer die
  Luftfeldberechnung damit hinfaellig (Biot-Savart exakt, Voxelsolver validiert).

### B-011 | Altes parametrisches Modell ist keine Stellarator-Topologie (2026-10-23)
- **Beobachtung:** In `geo/parametrische_generierung.py` umschliessen 20 von 50
  „NP"-Ellipsen (r0 = 5,05 und 5,95 m, Breite 0,6 m) die Achse R=5,5 m nicht; die
  „P"-Elemente sind horizontale Baender bei z=±0,6 m. Die Strom-Uebereinstimmung
  aus B-009/B-010 (0,90x) ist damit nicht belastbar. Die Annahme „reale Centerlines
  nicht verfuegbar" (B-010) war falsch: simsopt-Wheel (PyPI) enthaelt sie.
- **Messung:** Windungszahl jeder NP-Kurve um (R=5,5, Z=0): 30/50 = 1, 20/50 = 0.
- **Fundstelle:** Pruefskript ad hoc (2026-10-23), `geo/parametrische_generierung.py`.
- **Status:** ✅ gesichert. B-009/B-010 → ueberholt durch B-012; v0.1-Bericht
  archiviert unter `bericht/v0.1/`.


### B-010 | Stromabweichung konsistent + Quellenlage (2026-10-23)
> **Status 2026-10-23: UEBERHOLT** durch B-011 (Modell keine Stellarator-Topologie) und B-012 (reale Filamente).
**Basis:** Ampere-Turns bei B=2.5 T (Modell-Kalibrierpunkt) — nicht Drahtstrom
per se, sondern N·I je Spule.

**Messung (frischer Lauf 2026-10-23, `geo/w7x_gen/PARAMETER.json`):**
- Modell thin wire (N=1, I=1.244 MA je Spule):  **1.24 MA-A-Turns/Spule**
- W7-X-NPC real (N=108, I=12.8 kA bei 2.5 T; IAEA FT2-3): **1.38 MA-A-Turns/Spule**
- **Verhältnis 0.90× — korrekt** (Feld pro Ampere stimmt).
- Drahtstrom-Äquivalent: 1.244 MA/1 Draht vs. 1.244 MA/108 = 11.5 kA vs. real
  12.8 kA → 0.90×.
- **Die früher genannte ~2.9×-Abweichung** gilt NICHT für das Feld-Budget,
  sondern als **Drahtstrom-Multiplikator**: thin wire muss den vollen 2.5 T
  Feld mit 1 Draht erzeugen → 108× mehr A auf einen Draht; das ist der
  "Strom in der Spule" im thin-wire-Sinn, kein Feld-Fehler.

**Fundstelle:**
- Modell: `geo/w7x_gen/PARAMETER.json` (frisch, 2026-10-23)
- W7-X: skill `cae-ingenieurs-doku`, `references/w7x-eckdaten.md` (IAEA FT2-3,
  Bosch 2005, IPP 2003 als Primärquellen).
- B-009 BEFUNDE.md (thin-wire-Basis).

**Status:** FELD-BUDGET korrekt (0.90×). L/E (15.8 µH/12.2 MJ vs 5.8 H/620 MJ)
IST der N²=108²=1.16e4-Effekt → korrekt (thin-wire-Regel). Centerlines aus
simsopt/DESC/STELLOPT: **nicht verfügbar** (404, 2026-10-23 geprüfte Endpunkte —
s. w7x-eckdaten.md).


### B-009 | Parametrische Generierung: W7-X-analoges Spulensystem (2026-10-23)
> **Status 2026-10-23: UEBERHOLT** durch B-011/B-012.
- **Beobachtung:** Das 70-Spulensystem (50 NP + 20 P, 5 Feldperioden, R0=5.5 m)
  wird parametrisch generiert (thin-wire Biot-Savart), Kalibrierung auf
  B_Achse = 2.5 T. I = 1.24 MA/Schleife; 120 Windungen/Schleife →
  10.4 kA/Wicklung [Referenz IPP: 17.8 kA, 6.8 T am Spulenrand — Größenordnung ✓].
  L/E als thin-wire-Artefakt gekennzeichnet (nahe der Drahtsingularität mesh-abhängig,
  nur Größenordnungs-Vergleich mit W7-X L=5.803 H, E=620 MJ sinnvoll).
- **Messung:** `w7x_gen/PARAMETER.json` (I=1244051 A, B_axis=2.500 T exakt),
  `feld_verteilung.png` (links: axiales Radialprofil, rechts: poloidale Karte φ=0),
  `spulen.obj` (15840 Knoten, 5-Fach-Symmetrie sichtbar, BBox x/y ±6.2 m, z ±0.6 m).
- **Fundstelle:** `geo/parametrische_generierung.py` (246 Zeilen, venv: numpy+matplotlib),
  `geo/w7x_gen/` (PARAMETER.json, feld_verteilung.png, spulen.obj).
  Start: `.venv/bin/python geo/parametrische_generierung.py --out w7x_gen --obj`.
- **Status:** ✅ gesichert · Spulengeometrie-Frage (Offene Fragen #1) damit
  beantwortet: parametrisch generiert als W7-X-analoges Referenzsystem.
  Nächster Schritt: Vergleich mit offenen W7-X-Daten (ConStellaration/alphastell)
  oder direkte Übernahme dieser Parametrisierung in die 3D-Sim.

### B-008 | 2D-Validierung ERFOLGREICH — Elmer vs. Biot-Savart (2026-10-23)
- **Beobachtung:** Elmer 2D-planare Magnetostatik (gerader Draht) ist VERIFIZIERT.
  Offizieller Elmer-Referenztestfall `mgdyn2D_steady_wire` läuft 1:1 lokal:
  `ElmerGrid 1 2 wire2d.grd` (natives strukturiertes revolutioniertes Grid,
  radial) → `ElmerSolver case.sif` → **TEST.PASSED**, relative Abweichung zur
  Elmer-Referenznorm **3.1e-10**. Eigenständige Biot-Savart-Prüfung an `f.dat`
  (R=1 mm, I=1 A, Außenrand 5 mm, Az=0 BC):
  - Innerhalb Draht: H(r) linear, Mittelabweichung **+0.09 %**
  - Außerhalb: H(r)=I/(2πr), Mittelabweichung **+2.09 %** (typisch ≤ 2 %)
  - Max-Abweichung +13.5 % liegt NUR am Randknoten r=5 mm (Az dort per
    Dirichlet fixiert → erwartetes BC-Artefakt, aus Auswertung ausgeschlossen).
  **Root Cause der 22.10.-Fehlschläge (A_z ≡ 0):** (a) gmsh-CLI MSH 4.1 →
  ElmerGrid "non-conforming" + Body-Renummerierung; (b) SIF-Syntax falsch:
  `Equation "MGDynamics2D"` (nicht "MgDyn2D"), `Variable "Az"` (nicht
  "Potential"), Strom als **`Body Force → Current Density = -distribute <I>`**
  in A (gesamter Strom wird auf den Körper verteilt) statt rohem A/m²,
  plus 2. Solver `MagnetoDynamicsCalcFields` für B/H/J; (c) natives
  ElmerGrid-`.grd` liest ElmerGrid zuverlässig → gmsh-MSH-Thema umgangen.
- **Messung:** `solve.log`: "Relative Error to reference norm: 3.097e-10",
  "ELMER SOLVER FINISHED"; Zahlen-Tabelle + Diagramm `ergebnis.png`.
- **Fundstelle:** `sim/pipeline/gerader_draht/validiert/`
  (case.sif, wire2d.grd, f.dat, plot_ergebnis.py, ergebnis.png,
  solve.log, TEST.PASSED); Original: `sim/pipeline/gerader_draht/reference/`.
  Reproduzierbar: `sim/pipeline/gerader_draht/run_validierung.sh`.
- **Status:** ✅ gesichert · Validierungspfads-Frage (Offene Fragen #2)
  damit beantwortet: 2D-Pipeline ist verifiziert und bereit.

### B-007 | FreeCAD + Workflow-Referenz gefunden (2026-10-22)
- **Beobachtung:** FreeCAD 1.1.1 headless funktioniert:
  `cd ~/freecad_1.1_quellcode && ~/.pixi/bin/pixi run --manifest-path pixi.toml -- build/release/bin/FreeCADCmd -c …`
  (Test: Part.makeCircle OK). `/opt/freecad-1.1` ist 1.2 mit Visualisierungs-Bug.
  `~/ai-workspace/cae_orchestrator` enthält die bewährte Elmer-3D-Magnetostatik-Pipeline
  (`ema_axial_em3d.py`: WhitneyAVSolver+MUMPS-Direkt, Body-Force, Periodic BC+Lagrange;
  `elmer_runner.py`: ElmerGrid 14 2, ElmerSolver; `freecad_runner.py`: PATH-Venv-Falle =
  venv-bin aus PATH streichen, sonst 0-Knoten-Mesh ohne Warnung).
- **Messung:** FreeCADCmd -c Test; sed ema_axial_em3d.py.
- **Fundstelle:** ~/freecad_1.1_quellcode, ~/ai-workspace/cae_orchestrator.
- **Status:** ✅ gesichert · B-004 damit aufgelöst (kein Sudo mehr nötig).

### B-006 | Elmer-Doku: 2D-Planar, 3D-Solver (2026-10-22)
- **Beobachtung:** Elmer 9.0 MagnetoDynamics: 2D Axisymmetric → MagnetoDynamics2D
  (Equation = MgDyn2D), 3D → MagnetoDynamics (Equation = MgDyn), A-Feld via
  WhitneyAVSolver, Strom als Body-Force `Current` (J = A/m^2), Material:
  `Magnetic Permeability` + `Electric Conductivity`.
- **Messung:** ElmerModelsManual (Kap. Elektromagnetik, Zeilen 7372–9941),
  ElmerSolverManual.
- **Fundstelle:** `/tmp/elmerdoc/models.txt`, `/tmp/elmerdoc/sol.txt`.
- **Status:** ✅ gesichert.

### B-005 | Recherche: W7-X-Spezifikation, offene Daten (2026-10-22)
- **Beobachtung:** W7-X (IPP Greifswald): 50 nichtplanare (5 Unikate x 10) +
  20 planare Spulen (2 Unikate x 10), R0=5.5 m, a=0.53 m, V=30 m^3, B0=2.5 T,
  iota/2pi=5/6 bis 5/4, NbTi @ 17.8 kA, B=6.8 T am Spulenrand, 254 Ports,
  16 m Durchmesser, 4.5 m hoch, 725 t. Offene Daten: ConStellaration HF
  (proximafusion, 150k+ QI-Equilibria), alphastell (VMEC zu STEP).
- **Messung:** web_search (Wikipedia, FusionWiki, FtI TOFE 2004, HuggingFace).
- **Fundstelle:** forschung/ANALYSE-001 (dort komplett).
- **Status:** ✅ gesichert.

### B-004 | FreeCAD: sudo-Blockade + Disk knapp (2026-10-22)
- **Beobachtung:** `sudo -n true` → SUDO: password needed; `apt-get install
  freecad` → „Unable to fetch"...; Disk 49 G frei (~99 % belegt). Blender 4.0.2
  vorhanden (kein Sudo nötig).
- **Messung:** `df -h /` = 49 G frei; `which blender` → /usr/bin/blender;
  `apt-cache policy freecad` → 1.0.2 (installierbar, Sudo nötig).
- **Fundstelle:** Shell-Aufrufe am 2026-10-22.
- **Status:** ✅ AUFGELOST (2026-10-22, s. B-007: FreeCAD 1.1.1 unter
  ~/freecad_1.1_quellcode per pixi-Build vorhanden, headless verifiziert).

### B-003 | gmsh-Versionen, Python-API-Einschränkungen (2026-10-22)
- **Beobachtung:** System-gmsh 4.12.1 (CLI mit OCC-Booleschen OK); venv-gmsh
  4.15.1 (Python): API teils anders — `gmsh.model.occ.cut` statt difference,
  `gmsh.model.occ.add_cylinder` 9-Parameter.
- **Messung:** `gmsh -version`; Python-Import gmsh + API-Liste.
- **Fundstelle:** Terminal-Abfragen am 2026-10-22.
- **Status:** ✅ geklärt (CLI bevorzugt).

### B-002 | ElmerFEM 9.0 installiert, verifiziert (2026-10-22)
- **Beobachtung:** `elmerfem-csc 9.0-0ppa0-202610092044~b17662e9b~ubuntu24.04.1`;
  ElmerGrid vorhanden; .so: StatMagSolve, MagnetoDynamics, MagnetoDynamics2D,
  libelmersolver (MUMPS gelinkt).
- **Messung:** `dpkg -l elmerfem-csc`; `ls /usr/share/elmersolver/lib/`;
  `strings libelmersolver.so | grep MUMPS`.
- **Fundstelle:** apt PPA elmer-csc-ubuntu (Build 2026-10-09).
- **Status:** ✅ installiert.

### B-001 | Projektstruktur fusion/ angelegt (2026-10-22)
- **Beobachtung:** `~/hermes/fusion` nach wasserstoff-Vorlage:
  ERINNERUNGEN.md, BEFUNDE.md, forschung/ (research_stack.py, ANALYSE-001,
  references/), geo/, cad/, sim/pipeline/gerader_draht/, rechen/, bericht/,
  .venv/ (numpy scipy meshio gmsh pyvista).
- **Messung:** `find ~/hermes/fusion -maxdepth 3`.
- **Fundstelle:** Shell-Aufrufe am 2026-10-22.
- **Status:** ✅ gebaut.

---
Neue Einträge: oben. Status-Legende wie oben.
