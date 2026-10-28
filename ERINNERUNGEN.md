# ERINNERUNGEN — fusion (Stellarator)

> Kontext, Entscheidungen, nächste Schritte. Bei jeder Sitzung aktualisieren.
> Details: forschung/ANALYSE-*.md, BEFUNDE.md.

## Kontext
- **Ziel:** Kernfusion Stellarator (W7-X-ähnlich): Forschung, Modellierung, Simulation.
- **Abgrenzung:** eigenständiges Projekt neben ~/hermes/wasserstoff (BZ + Antrieb),
  dessen Doku-Konvention (ERINNERUNGEN/BEFUNDE/forschung/rechen) wir übernehmen.
- **ElmerFEM 9.0** installiert (apt PPA elmer-csc-ubuntu, Build 2026-10-09).
- Doku-Sprache: Deutsch.

## Entscheidungen (Datum)
- 2026-10-22 · Projekt `~/hermes/fusion` nach wasserstoff-Vorlage angelegt.
- 2026-10-22 · ElmerFEM 9.0 installiert und verifiziert (dpkg, ElmerGrid, .so-Check
  StatMagSolve/MagnetoDynamics/MUMPS).
- 2026-10-22 · **Validierungspfad:** gerader Draht, Biot-Savart exakt vs. FEM.
  2D-Planar (A_z, Strom senkrecht zur Ebene) → exakt B_theta = mu0*I/(2 pi r),
  kein Randfehler. 3D-Variante: Endeffekte, exakte endliche-Draht-Formel.
- 2026-10-22 · **FreeCAD IST INSTALLIERT** (Korrektur zu B-004):
  `~/freecad_1.1_quellcode` (pixi-Build 1.1.1, headless verifiziert:
  `pixi run --manifest-path pixi.toml -- build/release/bin/FreeCADCmd -c …`).
  `/opt/freecad-1.1` ist 1.2 mit Visualisierungs-Bug → 1.1.1 Build nutzen.
  Blender 4.0.2 bleibt als Fallback.
- 2026-10-22 · **Workflow-Referenz gefunden:** `~/ai-workspace/cae_orchestrator`
  (`elmer_runner.py`, `freecad_runner.py`, `ema_axial_em3d.py`) = bewährte
  3D-Magnetostatik-Pipeline: gmsh-Python → .msh → ElmerGrid 14 2 →
  WhitneyAVSolver + MUMPS Direkt + Body-Force (Magnetization/Current) +
  Periodic BC mit Lagrange. Dieses Muster übernehmen.
- 2026-10-22 · Recherche abgeschlossen → forschung/ANALYSE-001 (W7-X-Spezifikation,
  50 nichtplanare + 20 planare Spulen, quasi-isodynamisch, neoklassischer Transport,
  ConStellaration-Datensatz, Elmer-Solver-Wahl MagnetoDynamics2D/StatMagSolve).
- 2026-10-23 · **2D-PLANAR-VALIDIERUNG ABGESCHLOSSEN** (s. BEFUNDE B-008):
  Elmer-Referenzfall mgdyn2D_steady_wire 1:1 lokal (TEST.PASSED, 3.1e-10),
  Biot-Savart-Abz. ≤ 2 % (Randknoten = BC-Artefakt). Bewährte Kette:
  natives ElmerGrid-`.grd` (radial) → `ElmerGrid 1 2` → `ElmerSolver` mit
  `Equation "MGDynamics2D"`, `Variable "Az"`, Strom per `Current Density =
  -distribute <I>` (A) im Wire-Body + 2. Solver MagnetoDynamicsCalcFields,
  BC: Az=0 am Außenrand. Reproduzierbar: `sim/pipeline/gerader_draht/
  run_validierung.sh`; Ergebnis: `sim/pipeline/gerader_draht/validiert/
  ergebnis.png`. **Nächster Schritt: FreeCAD-Modellierung (W7-X-Spule) →
  3D-Spulenfeld.**

- 2026-10-23 · **PARAMETRISCHE GENERIERUNG ABGESCHLOSSEN** (s. BEFUNDE B-009):
  W7-X-analoges 70-Spulensystem (50 NP + 20 P, 5 Feldperioden, R0=5.5 m)
  parametrisch generiert (thin-wire Biot-Savart), Kalibrierung auf B_Achse=2.5 T:
  I=1.24 MA/Schleife → 10.4 kA/Wicklung (Ref. IPP 17.8 kA — Größenordnung ✓).
  `geo/parametrische_generierung.py` (+ w7x_gen/: PARAMETER.json, feld_verteilung.png,
  spulen.obj 15840 Knoten, 5-Fach-Symmetrie sichtbar).
  Offene Frage #1 damit beantwortet. **Nächster Schritt: Übernahme in 3D-Sim,
  evtl. Vergleich mit offenen W7-X-Daten (ConStellaration/alphastell).**

- 2026-10-23 · **STROMABWEICHUNG QUANTIFIZIERT + 3D-RENDERING + BERICHT**
  (s. BEFUNDE B-010, ANALYSE-002): Frische Verrechnung: Modell 1.244 MA/Spule
  (thin wire) vs real 108x17.8 kA = 1.92 MA → **Modell = 0.65x real
  (Faktor ~1.5x)**; Ältere "2.9x"-Angabe durch 19.15-kA-Vorlauf ersetzt.
  3D-Renderings: `bericht/bilder/` (spulen_iso/oblick/seitl, matplotlib 3D,
  Major-Radius-Coloring). PDF-Bericht: `bericht/bericht.pdf` (LaTeX,
  Titel/Abstract/Parameter/Vergleich/Limitationen/Literatur).
  Centerline-Verifikation (p10): Blockiert — STELLOPT/simsopt/DESC-GitHub-
  Pfade 404/leer (mehrere Versuche 2026-10-23); User-Entscheidung ausstehend:
  eigene Datenquelle nennen oder Befund B-010 so stehen lassen.

- 2026-10-23 · **NEUE PIPELINE MIT REALEN W7-X-SPULEN** (Claude Code; s. BEFUNDE B-011..B-014,
  Bericht v0.2 `bericht/bericht.pdf`, v0.1 archiviert unter `bericht/v0.1/`):
  - Altes parametrisches Modell ist keine Stellarator-Topologie (B-011) → ersetzt.
  - Reale Filamente aus simsopt-Wheel (`stellarator/daten/W7-X.dat`, Quelle in QUELLE.md).
  - Paket `stellarator/` (spulen, picogk_bruecke, voxelsolver, feldlinien, lauf).
    Orchestrator-CLI: `.venv/bin/python -m stellarator.lauf stellarator/faelle/w7x_standard.json [--schritte ..] [--setze a.b=x --name ..] [--bericht]`.
  - PicoGK headless-App `picogk/StellaratorVoxel/` (eigene Voxelgroesse, kein Viewer).
  - Eigener FFT-Voxelsolver (Hockney) statt Elmer fuer das Luftfeld; validiert.
  - Ergebnis: 12,18 kA/Wdg fuer <B_Achse>=2,5 T; iota 0,86..0,94 + 5/5-Inseln.
  - Hermes-Skills neu: `cae/stellarator-pipeline`, `cae/picogk-voxel`;
    Korrekturblock in `cae-ingenieurs-doku/references/w7x-eckdaten.md`.
  - venv: numba installiert (Biot-Savart 100k Punkte/s).

- 2026-10-24 · **PicoGK nur Option.** Geometrieweg Standard: gmsh/OCC → STEP → Elmer
  (B-015). Rechner 32 GB RAM / 24 GB VRAM. Ziel: Magnetfeld-Sim, Optimierung spaeter
  von Hermes/PI orchestriert (Agent steuert Studien, numerischer Optimierer rechnet).
  Skill `stellarator-pipeline` v0.2 auch fuer PI verlinkt (`~/.pi/agent/skills/`).

## UEBERGABE / laufende Jobs (fuer Hermes, falls Claude-Sitzung endet) — 2026-10-24
- ~~FEM W7-X ueber Rohrnetze~~ FERTIG (B-025: 99 % < 43 MPa, max 110 MPa, 264 t Stahl).
- **Naechste Verbesserungsschleife (User-Wunsch):** Verguss-Schicht (Quarzsand-Epoxid, ~10 mm, E ~10–20 GPa) zwischen
  Wickelpaket und Gehaeuse in FreeCAD + Elmer (Details Skill stellarator-flaechen, Offen).
- **FEM A45 mit Keil** (5. Versuch, ToleranceBoolean 1e-4): Ordner `sim/stellarator/gehaeuse_fem/A45_HTS_keil/`,
  Log `lauf.log`. Fertig bei Zeile `FERTIG`; bei "overlapping facets" siehe Skill stellarator-flaechen
  (naechste Option: Stahl in FreeCAD vereinigen + Refine). Ergebnis mit B-021 (ohne Keil) vergleichen.
- **W7-X-Reparatur** (`stellarator.aufbau stellarator/faelle/w7x_standard.json --reparieren`):
  Ausgabe `sim/stellarator/gehaeuse/w7x_standard/aufbau/{korrektur.json,reparatur.json}`. Danach neu bauen
  (Befehl W7-X im Skill stellarator-flaechen, plus `--korrektur .../korrektur.json`) und `stellarator.aufbau` erneut.
- ~~Elmer 70 Spulen~~ FERTIG 2026-10-24 (B-016: Achse 0,24 % vs. Biot-Savart). Vorgehen bleibt Muster:
  Ordner `sim/stellarator/elmer_w7x_70/`.
  Fertig, wenn `lauf.log` mit `ENDE 0` endet und `ergebnis.json` existiert.
  Pruefen: `tail -5 sim/stellarator/elmer_w7x_70/lauf.log; pgrep -af ElmerSolver`.
  Erwartung: `stromrichtung_falsch` = [] und `fehler_vs_biot_savart.achse.fehler_median`
  im Bereich weniger % (Einzelspule h=0,05: 4–6 %). Wenn nicht: NICHT als Befund uebernehmen.
  Laeuft ElmerSolver nicht mehr, aber `erg/feld_t0001.vtu` existiert und `ergebnis.json` fehlt:
  `.venv/bin/python -m stellarator.elmer sim/stellarator/elmer_w7x_70 --spulen 70 --nur_auswerten`
  (Stroeme kommen dann aus case.sif). Ergebnis in BEFUNDE B-016 nachtragen.
- ~~Standardlauf neu~~ ERLEDIGT 2026-10-24 (13,49 kA). Offen nur noch Bericht-Text v0.3:
  `.venv/bin/python -m stellarator.lauf stellarator/faelle/w7x_standard.json --bericht`,
  Zahlen gegen `sim/stellarator/bewertung/bew_w7x_standard/kennzahlen.json` pruefen
  (13,48 kA/Wdg), Bericht v0.2 → v0.3 nachziehen.
- ~~Stufe 1/2/3 `qa_nfp2`~~ ERLEDIGT 2026-10-24 (B-018): qs 1,3e-5; Spulen Variante `mittel`
  (abstand_sp 0,18) → `invers/beispiele/qa_nfp2/spulen.json`. Keine Jobs laufen.
- **1-GW-Auslegung (User: "Anlage ca. 1 GW Netz")** ERLEDIGT (B-018, Stufe 0 `invers/stufe0_bilanz.py`):
  HTS R0 12,1 m / B0 7,5 T; Nb3Sn R0 22,2 m / B0 4,8 T. Faelle `stellarator/faelle/qa_nfp2_1GW_{HTS,Nb3Sn}.json`.
  Ablauf: Stufe 0 → Falldateien → bewerte (B_max_oberflaeche/B0 = k_B) → Stufe 0 mit neuem
  `--k_B Leiter=..` bis B_Leiter ≤ Grenze (2–3 Iterationen).
- **A=4,5 + Struktur (B-019)** ERLEDIGT bis auf Struktur A=4,5. Keine Jobs laufen.
  Schalenflaechen: durchgehende Schale bleibt ungeloest; **User-Idee umgesetzt (B-020):**
  Spulengehaeuse als Variable Section Sweep in FreeCAD, `.venv/bin/python -m stellarator.gehaeuse <fall> --oeffnen`.
  Gehaeuse verbunden (160 Verbinder, 5 kanonische Paare + Klone, `--verbinder 10`).
  ERLEDIGT (B-021): `stellarator.gehaeuse_fem` (STEP -> gmsh OCC-Fragment -> Elmer) laeuft; Stahl
  viel zu duenn (99 % < 5130 MPa). NAECHSTER SCHRITT: Wandstaerken/Verbinder auslegen (Iteration).
  Ordner `sim/stellarator/gehaeuse_fem/qa_nfp2_A45_1GW_HTS/` (netz.log, solve.log, ergebnis.json).
  Erst `--nur_netz` (Zeile "NETZ" im Log), dann ohne Flag (losgeloest, ~10-30 min). Haengt gmsh
  > 25 min: per PID beenden, h_stahl groesser (0.25-0.3).
  Bericht v0.3: `.venv/bin/python -m stellarator.bericht --version 0.3` (Skill `stellarator-bericht`), lokal.
- Lange Laeufe IMMER losgeloest starten: `setsid nohup bash -c '...' > log 2>&1 < /dev/null &`.

## GitHub (2026-10-24)
Oeffentlich, MIT: https://github.com/ThomasSchmiegelt/stellarator-design (README mit Bildern,
Projektbeschreibung). Seit 2026-10-25 auf User-Wunsch Berichte im Repo: bericht/projektbericht (de/en, Quellen einzeln geprueft) + v0.3; v0.1/v0.2/spulen_recherche bleiben lokal (ungepruefte Zitate). Updates: siehe Skill-Abschnitt GitHub.

## Neue Richtung (User, 2026-10-24): INVERS entwerfen
Frage umdrehen: Welches Magnetfeld wird gebraucht? → welche Geometrie (Spulen) folgt daraus?
User-Wahl: **kompakter Stellarator** (nicht W7-X nachbilden). Installation erlaubt.
- Stufe 1 Zielfeld/Plasmaform: DESC (JAX, GPU) – z.B. quasi-axisymmetrisch (QA), nfp=2.
- Stufe 2 Spulen: simsopt Stage-2 (B·n auf Zielflaeche, Laenge, Kruemmung, Abstaende).
- Stufe 3 Pruefung/Geometrie: vorhandene Kette (bewerte, abstaende, cad, elmer).
- Eigene venv `.venv-opt` (DESC/JAX/simsopt), Austausch ueber JSON-Dateien, damit die
  Bestandspipeline (.venv, numba) nicht gestoert wird.
- Formoptimierung ist massstabsfrei: Groesse R0 und B0 werden danach festgelegt (Stroeme ~ B0*R0).

## Offene Fragen (warten auf User)
1. ~~Spulengeometrie-Quelle~~ — ERLEDIGT (reale W7-X-Filamente, B-012).
2. ~~Validierungspfad~~ — ERLEDIGT (B-008 2D; B-012 Voxelsolver vs. Biot-Savart).
3. ~~Elmer 3D Stromquelle~~ — fuer das Luftfeld hinfaellig (B-012). Elmer kuenftig fuer
   Struktur (Gehaeusespannungen aus Spulenkraeften) oder Eisen.
4. **Wickelpaket-Querschnitt:** Annahme 0,192 x 0,160 m — reale IPP-Masse vorhanden?
5. **B_max-Luecke (B-013):** Mehrfilament-Modell bauen?
6. **Abschlussformat:** LaTeX-PDF (v0.2 so gebaut) — passt?

## Naechste Schritte
00. (2026-10-24, nach 1-GW-Auslegung) Vorschlaege an User:
   a) Kleineres Seitenverhaeltnis A=4–5 (Stufe 1 neu, `--aspekt 4.5`) → HTS ~10–11 m.
   b) Stuetzstruktur/Kraefte (2–3 GN je Spule!) → Elmer StressSolver.
   c) Stufe 0 verfeinern (Divertor, Zyklotronstrahlung, Blanket-Neutronik).
   User-Entscheidung Leiter (HTS oder Nb3Sn) steht noch aus.
0. ~~Schnelle Bewertungsfunktion~~ ERLEDIGT (B-016, `stellarator/bewerte.py`, ~10 s).
   Naechster Schritt: Studien-Runner (scipy/optuna) ueber `bewerte()`; Ziele/Grenzen mit User klaeren.
0b. Elmer mit allen 70 Spulen: STL-Weg (`cad.elmer_netz`), h_spule 0,05 (~3,5 Mio. Tets, ~12 GB).
0c. **Offen (User, 2026-10-24): allgemeiner Weg STL → STEP** ausdenken (nicht nur fuer
    Spulen). STEP ist fuer Rechnungen nicht noetig, nur fuer CAD-Weitergabe.
1. Parameterstudien ueber Falldatei (PCA/PCB-Stroeme → iota-Variation, Inselposition).
2. Voxelsolver auf Zylindergitter einer Feldperiode (Symmetrie → Flussflaechen, B-013a).
3. Mehrfilament-Wickelpaket fuer B_max (B-013b).
4. Elmer StressSolver: Gehaeuse (PicoGK-STL) mit Kraeften aus `spulen_kraefte.vtp`.

## Blockers
- **Speicherplatz** — vor Installationen und grossen Laeufen freien Platz pruefen.
- **Tavily Rate-Limit** (60 s Pause) — Websuchen einzeln.

- **2026-10-24:** Research-Bericht Magnetspulen (Funktion/Bauweise/Material/Fertigungsverfahren, W7-X, zitiert) als `bericht/spulen_recherche.{tex,pdf}` (3 S., 0 Fehler, visuell gecheckt). Kanäle: write_file/execute_code/terminal-Heredocs >~15 Zeilen = abgeschnitten; **patch ≤~700 Zeichen + kurze printf/sed = zuverlässig.**

- **2026-10-25:** 3D-Modelle torus3d/leiter3d + Blender-Render (blender_szene.py, Cycles CPU), Bilder in docs/bilder, Befund B-026. .blend-Dateien in sim/stellarator/{torus3d/w7x_standard,leiter3d}.
- **2026-10-25:** Projektbericht von Anfang an: `bericht/projektbericht/projektbericht.{tex,pdf}` (de, Maschinenbau) und `project_report_en.{tex,pdf}` (en, IT). Alle Zitate gegen Volltext/Crossref/arXiv geprueft; Hermes-Literaturliste der Spulen-Recherche hatte unvollstaendige/falsche Angaben -> vor Veroeffentlichung korrigieren.
- **2026-10-25:** Fusions-Surrogat gebaut (stellarator/hexmodell.py, surrogat.py, surrogat_waechter.py, surrogat_anlagen.json, elmer_udf/lorentz.f90; Skill `stellarator-surrogat`, auch fuer PI verlinkt). **UEBERGABE:** autonomer 4-h-Lauf seit 11:15 (`surrogat_waechter --anlage beide --stunden 4 --n 150`), PI prueft alle 20 min und darf nur `sim/surrogat/<anlage>/steuerung.json` aendern. Danach: `validierung.json/png` ansehen, Vorhersage + `--pruefen`, Bild oeffnen, Befund B-027 ergaenzen. Bei Absturz: denselben Befehl neu starten (fortsetzbar).
- **2026-10-25 (Bericht):** Orchestrierung Claude (Chef) + PI (lokale Aufsicht ueber steuerung.json) + autonomer Lauf ist Berichtsstoff; Ablauf/Fehler stehen in B-027 und sim/surrogat/*.log. User-Pause 12:12–13:22 per sim/surrogat/zeitplan_pause.sh.
- **2026-10-25 (Idee, nur notiert):** PicoGK-Gitter (LEAP71 LatticeLibrary/HelixHeatX) als homogenisierte Stuetzfuellung fuer 1 GW (Einheitszelle -> E-Modul -> Surrogat-Parameter Gitterdichte) und als Gyroid-Waermetauscher im Plasmagefaess. Erst nach Abschluss des Surrogat-Laufs.
- **2026-10-25 15:15 NEUSTART nach Absturz:** `.venv/bin/python -m stellarator.neustart` (Ziel in sim/surrogat/auftrag.json, Stand sim/neustart_stand.md). Offen: qa_1gw Probe 40 nachrechnen (von Claude versehentlich per kill abgebrochen): `.venv/bin/python -m stellarator.surrogat probe --anlage qa_1gw --nr 40` NACH dem Lauf; Gitterzelle gyroid_0.95 nach dem Lauf; danach Stufe 2 (Gyroid-Fuellung im Hex-Modell).
- **2026-10-25 (User, Anforderungen Gitter):** Plasmagefaess/Waermetauscher braucht Oberflaeche + Stroemungsgeschwindigkeit (Wasser sieden), Stuetzstruktur muss Kraefte in allen Komponenten tragen -> Waermetauscher-Kennzahlen (Gyroid S_v ~550 m2/m3, D_h ~5 mm bei 10-mm-Zelle) und voller Steifigkeitstensor/Schub fuer Stuetzgitter.

## 2026-10-25 17:15 Surrogat abgeschlossen, Bericht geschrieben (Claude)
- Lauf fertig 16:27, Training automatisch; qa_1gw Probe 40 nachgerechnet + neu trainiert (79 Proben). Ergebnisse B-027.
- Neu: `stellarator/surrogat_auswertung.py` (Lastkurve + Empfindlichkeit, sim/surrogat/auswertung.png).
- Bericht `bericht/surrogat/surrogat_bericht.{tex,pdf}` (8 S.), Verweis-Kasten im Projektbericht; auf GitHub.
- GyroidGefaess (PicoGK) 2x gestartet -> beide Male Claude-Sitzung abgestuerzt (sim/gyroid_gefaess/PROBLEM.md). Ursache offen.
- Offen: Gitterzelle gyroid_0.95 + kennlinie.json; Plasmagefaess + Torus-Gesamtbild; Stufe 2 Gitterfuellung.
- **2026-10-25 17:40 Absturz-Ursache + Watchdog:** systemd-oomd beendete 2x die ganze Terminal-Sitzung (journalctl: vte-spawn-*.scope oom-kill). Ausloeser: doppelte STL-Skalierung in gyroid_gefaess.py (Plasma 1000x zu gross). Neu `stellarator/speicherwaechter.py`: schwere Programme in eigener `systemd-run --user`-Einheit mit MemoryMax/MemorySwapMax=0, Waechter (RAM-Reserve 4 GB, PSI avg10 > 30 %) beendet frueh. setsid schuetzt NICHT (gleiche cgroup).
- **Gyroid-Plasmagefaess (1 GW):** `python -m stellarator.gyroid_gefaess --sektoren 0:30 --teil 10 --voxel 0.025 --halbdicke 0.015 --zelle 0.40 --name detail`; Wand 0,45 m (Haeute 20/30 mm), Kerndichte 24 %, Stahl 33 % der Wand. Gesamtbild `gesamtbild()` -> sim/gyroid_gefaess/detail/gesamt_{schraeg,detail}.png + gesamt.vtm (ParaView). Offen: Kollisionspruefung Gefaess/Spulen, Stroemung.
- **2026-10-25 abends Gesamtszene + Kuehlsegment:** `python -m stellarator.gesamtszene` (Gyroid-Sektor `sim/gyroid_gefaess/dick`: Wand 0,9 m, Zelle 0,6 m, 0..20 Grad geschlossen, 20..40 ohne Aussenhaut; Spulen mit Spannung, Stuetzstruktur silber getrennt, Feldlinien |B|) -> PLY + `blender -b -P stellarator/blender_gesamt.py -- <abs. Ordner> --ansicht alle` (uebersicht/schnitt/gyroid, CPU, ~3 GB) ueber speicherwaechter; Legende `gesamtszene.legende`. Abstand Plasma->Stahlgehaeuse min 1,25 m.
- **Kuehlsegment:** `python -m stellarator.kuehlsegment` (picogk/KuehlSegment): 1,0 x 0,4 m, Kern 0,2 m, Zelle 100 mm, Kerndichte 24 %, Verteilkammern 60 mm, Rohre D 100 mm; segment.stl + wasser.stl (ein zusammenhaengender Fluidraum) fuer FluidX3D. v_Kern/v_Rohr nur 0,10 -> fuer Sieden mehr Rohre/engere Zellen. FluidX3D liegt in ~/ai-workspace/FluidX3D, braucht GPU (Hermes) -> erst fragen.

## 2026-10-25 abends: Gefaess-Torus allein, geschnitten (Blender)
- stellarator/thorus_schnitt.py + blender_thorus.py: nur Plasmagefaess in Einbaulage auf Hallenboden, ohne Spulen und Verbinder,
  Tortenstueck 40..100 Grad herausgeschnitten; Schnittflaechen orange, Gyroid-Kern (PicoGK dick 0..40 + neu dick2 100..140) sichtbar.
- Bilder sim/thorus_schnitt/blender_uebersicht.png, blender_detail.png; thorus.blend. 64 Proben, 321 s, Spitze 4,7 GB (Waechter 6 GB).
- Horizontaler Schnitt (User-Wunsch): gyroid_gefaess.py --z_band=-1.0:0 --name band (36 x 10 Grad, je ~25 s, 0,5 GB),
  thorus_schnitt.py --horizontal --teile band -> sim/thorus_schnitt/horizontal/blender_*.png (509 s, Spitze 2,5 GB).
- Gemeint war (User): senkrechter Schnitt durch nur EIN Segment. gyroid_gefaess.py --ebene 20:11.1 --sektoren 0:40 --name ebene
  (Keil hinter senkrechter Ebene laengs zum Ring abgeschnitten), thorus_schnitt.py --ebene --teile ebene
  -> sim/thorus_schnitt/ebene/blender_*.png (365 s, Spitze 1,4 GB). Rest des Rings geschlossen, keine Spulen/Verbinder.
- Lieblingsbild des Users: sim/thorus_schnitt/blender_uebersicht.png (Tortenschnitt 40..100). Davon Variante mit Spulen
  (Spannung), Feldlinien, ohne Verbinder: thorus_schnitt.py --spulen -> sim/thorus_schnitt/spulen/thorus_*.png
  (Spulen 2, 3, 15 ueber dem Ausschnitt weggelassen; 495 s, Spitze 5,0 GB).
  Weite Ansicht (ganze Anlage): blender_thorus.py --ansicht weit -> sim/thorus_schnitt/spulen/thorus_weit.png (136 s).
  Frei schwebend ohne Boden: blender_thorus.py --ansicht weit --ohne_boden -> thorus_weit_frei.png (74 s).
  HQ: --proben 1024 --hq (2560x1440, kein OIDN im Ubuntu-Blender, clamp indirect 5) -> thorus_weit_frei_hq.png.
- HQ-Bild in README (docs/bilder/gyroid_gefaess_1GW_gesamt.jpg) und in Surrogat-Bericht (Abb. 6), Projektbericht de/en eingebaut.
- Stand Abend 25.10. (alles gepusht, 2cdf3f8). Naechste Schritte: FluidX3D-Stroemung Kuehlsegment (GPU erst nach
  Freigabe durch User, gehoert Hermes), evtl. Segment mit mehr Einlaessen/feinerer Zelle (v_Kern/v_Rohr 0,10),
  Kollisionspruefung Gefaess/Spulen, Bild evtl. auch in ki_im_maschinenbau.tex.

## 2026-10-26: Kuehlsegment 85..95 Grad durchgerechnet (FluidX3D, GPU freigegeben)
- PicoGK picogk/SegmentKuehlung + stellarator/kuehlung_segment.py: Wand 0,9 m Gyroid (Zelle 0,6 m), Verteilkammer +
  Lochblech (12 x 60 mm), Sammelkammer, Rohre DN200 ein / DN250 aus radial aussen in der Spulenluecke (3,4 m Abstand).
  Auslegung: 0,5 MW/m2 x 26,7 m2 = 13,3 MW, 106 kg/s, dT 30 K.
- FEHLER gefunden (User-Hinweis "vielleicht ist es nicht durchgaengig"): Normale der verdrillten Flaeche hat
  Toroidalanteil -> Lochmitten bis 2,5 Grad neben der Platte, nur 3 von 12 offen. Fix: schnitt_ebene() (Punkte
  in der Ebene phi interpoliert). Ausserdem bei 12 mm Gitter 45-mm-Loecher zu (nur 3,75 Zellen). Jetzt 8 mm.
  kuehlung_cfd.durchgaengig() prueft nach dem Probelauf Zusammenhang + Zellen je Loch.
- FluidX3D: eigene Kopie v3.8 in ~/fluidx3d_stellarator (Hermes-Kopie ~/fluidx3d_cae unberuehrt). Lizenz beachten
  (Memory fluidx3d-lizenz): geaenderte setup.cpp liegt in fluidx3d/ mit LICENSE.md, NICHT MIT; vor Veroeffentlichung fragen.
- Platte fast voll (~9 GB frei): Feldexport nur Wasserzellen (~0,8 GB je Feld bei 8 mm).
- Ergebnis Lauf b (8 mm, 2,1e8 Zellen, 11 GB VRAM, 37 min, 90 s phys., konvergiert ab ~10 s): Druckverlust 15,9 kPa;
  Lochblech Streuung 34 % (max/min 2,8); Gyroid-Kern: 12 Strahlen aus den Loechern laufen durch, dazwischen
  fast Stillstand und Rueckstroemung (Streuung Umfang 163 %); Plasmaseite v ~ 4 cm/s (p10 3 mm/s) -> Waermeuebergang
  viel zu klein fuer 0,5 MW/m2 (h ~ 200-400 W/m2K). Folgerung: eigene schnelle Erstwand-Kanaele noetig.
  Mengenbilanz der Auswertung +-15 % (Loecher 117, Kern 89, Soll 106 l/s). Bild sim/kuehlung_segment/b/cfd/auswertung.png
- Variante e1 "Erstwand-Spalt" (stellarator/kuehlung_erstwand.py, picogk/SegmentErstwand): 40-mm-Spalt hinter 10-mm-
  Erstwand, Gyroid-Kern zu (nur Tragstruktur), dT Wasser 10 K -> 319 kg/s, DN350/DN400, Lochblech 34 x 60 mm.
  FluidX3D 8 mm, 40 s phys., 13 min: Druckverlust 17,7 kPa; Loecher Streuung 31 % (max/min 3,0); Spalt ueberall
  vorwaerts, Streuung 28 %, v 0,30-0,49 m/s (Plasmaseite Mittel 0,43, p10 0,085 m/s, vorher 0,04/0,003);
  Wand ueber Wasser ~130-190 K (Dittus-Boelter heiss, Sektormittel). Bild sim/kuehlung_segment/e1/cfd/auswertung.png
- e2 (Loecher abgestuft 45-73 mm) gebaut + geprueft, aber verworfen: User will KEIN Lochblech.
- Variante f1 (User-Vorgabe): Ringkammern stirnseitig flaechig offen zum Gyroid-Kern, Wasser verteilt sich im Ring,
  fliesst durch die Filamente zum Sammelring und raus. kuehlung_segment.py --ohne_platte (PicoGK mit_platte=false),
  dT 10 K, 319 kg/s, DN350/DN400, kammer_ein 480 / kammer_aus 520. Probelauf durchgaengig. kuehlung_cfd.auswerten
  zeigt ohne Loecher die Umfangsverteilung an Kerneintritt/-austritt. Lauf 8 mm, 40 s phys. gestartet.
- Ergebnis f1 (8 mm, 40 s phys., 164000 Schritte): Druckverlust nur 5,2 kPa (b 15,9 / e1 17,7). Durchfluss gemessen
  ~283 l/s statt 319 (Einlass-Messquerschnitt u 0,089 statt 0,1 Gitter, ~11 % weniger). Verteilung Kerneintritt
  Streuung 141 %: direkt vor dem Einlassrohr (aussen, 0 Grad) Rueckstroemung (-24 l/s), Hauptstrom bei +-45 Grad,
  Innenseite (180 Grad) schwach. Kernmitte 86 %, Kernaustritt 62 % (gleicht sich im Gyroid etwas aus).
  Plasmaseite v Mittel 5 cm/s, p10 4 mm/s -> wie b, viel zu wenig fuer 0,5 MW/m2. Grund: grosser Kernquerschnitt
  (0,9 m dick), Ring ungedrosselt. Ideen: Prallblech vor Einlass im Ring, Gyroid zur Plasmaseite feiner/enger
  (abgestufte Zelle), Kern duenner. Bild sim/kuehlung_segment/f1/cfd/auswertung.png
- Variante f2 = f1 + abgestufter Gyroid (User: "mach 2"): vorn 0,2 m Schicht Zelle 0,2 m / halbdicke 12 mm
  (Porositaet ~0,6), hinten Zelle 0,3 m / halbdicke 40 mm (Porositaet ~0,16, drosselt). PicoGK --schicht/--zelle_vorn/
  --halbdicke_vorn, voxel 8 (924 s, 6,8 GB). Stahl 13,4 m3, Wasser 14,7 m3. FluidX3D 8 mm 40 s:
  Druckverlust 5,9 kPa; Verteilung Kerneintritt 40 % (f1 141 %), Kernmitte 36 %, Austritt 35 %, keine Rueckstroemung
  mehr; vordere Schicht fuehrt 56 % des Durchflusses; Plasmaseite v Mittel 8,6 cm/s (f1 5), p10 0,7 mm/s (Totwasser
  an der Haut). Grob h ~1000 W/m2K ohne Rippenwirkung -> fuer 0,5 MW/m2 noch zu wenig. Bild f2/cfd/auswertung.png
  e2-Ordner geloescht (Platz). Platte ~4 GB frei.
- Aufgeraeumt (User OK): STL- und Feld-Dateien von a, b, e1, f1 geloescht (Auftraege, json, png bleiben; neu erzeugbar
  ueber kuehlung_segment/kuehlung_erstwand + kuehlung_cfd). f2 komplett behalten (fuer Blender). Platte 8,8 GB frei.
- 2026-10-27 Modellaenderung (User-Skizze Draufsicht mit zwei roten Linien): Eintritt innen im Torus (180 Grad gedreht),
  Austritt aussen. f3 = nur Eintritt innen (Keilkammern) -> verworfen. f4: --ein_innen --schraeg: Kern zwischen zwei
  senkrechten schraegen Ebenen; Eintrittskammer innen 420 mm breit, laeuft aussen an Stirnplatte spitz aus;
  Sammelkammer aussen 600 mm, laeuft innen spitz aus (Z-Verteiler). DN300 ein (innen, 0,68 m zur Spule), DN400 aus.
  Abgestufter Gyroid wie f2. Geometrie voxel 12 gebaut; Draufsicht stellarator/draufsicht.py -> f4/draufsicht.png.
  Vor CFD: Geometrie mit 8 mm neu bauen; auswerten() nutzt kern-Winkel = Mitte der Geraden (pruefen).
- auswerten() verallgemeinert (schraege Kernebenen, Plasmahaut ueber alle phi statt nur einer Spalte). f2 neu
  ausgewertet: vordere Schicht 66 % (vorher 56 %), Plasmaseite 9,6 cm/s (vorher 8,6) - alte Zahl war zu grob.
- f5 = f4 + staerkere Abstufung (User: plasmaseitig mehr Wasser, aussen weniger): vorn Zelle 0,2/halbdicke 10
  (Porositaet 0,69, Kanal 78 mm), hinten 0,3/43 (Porositaet ~0,08, Kanal ~40 mm). voxel 8.
- Ergebnis f5 (8 mm, 40 s phys.): Druckverlust 7,9 kPa; Verteilung Kerneintritt 20 %, Mitte 21 %, Austritt 23 %
  (bisher beste); vordere Schicht fuehrt ~100 % (hintere 0,3/43 bei 8-mm-Gitter praktisch zu -> nur Tragstruktur);
  Plasmaseite v Mittel 0,137 m/s (f2 0,096), p10 4,7 mm/s. Grob h ~1450 W/m2K ohne Rippenwirkung -> noch zu wenig
  fuer 0,5 MW/m2. Durchfluss ~299 l/s (Einlass-RB ~7 % unter Soll). Bild f5/cfd/auswertung.png
- Prozessbeschreibung (User-Wunsch, Schwerpunkt Interaktion Nutzer/KI): docs/kuehlsegment_prozess.md - bei neuen
  Varianten Tabelle Abschnitt 3 fortschreiben. Animation: stroemung_animation.py + blender_stroemung.py (EEVEE,
  ~8 s/Bild) + picogk/StlSchnitt (Stahl z<0, ohne Innenhaut: plasma.stl Abstand 180 mm). Test an f5 ok.
- Skizzen-Werkzeug (User-Wunsch): stellarator/skizze.py + skizze.html (three.js 0.160 von unpkg), lokal 127.0.0.1:8765,
  systemd-Unit "skizze". Vorschau-Netze vorschau_stahl/wasser.stl (StlSchnitt voxel 16, ~100 MB). Senden ->
  sim/skizzen/<zeit>/skizze.png + skizze.json (Linien als 3D-Punkte auf Bauteil, R, phi), neu.txt. Nach dem Lesen
  neu.txt loeschen und Waechter neu starten (until [ -f sim/skizzen/neu.txt ]).
- Ergebnis f6 (vorn 0,12 m, Zelle 0,12/6 mm): Druckverlust 16,7 kPa; Plasmaseite v 0,20 m/s (f5 0,137), vordere
  Schicht ~100 %; Verteilung schlechter: Streuung 47 % (Innenseite +-180 Grad bekommt doppelt, Einbrueche bei +-52 Grad).
  Grund vermutlich kuerzerer Weg innen durch die schraegen Ebenen + duenne Schicht staerker gedrosselt. Bild f6/cfd/auswertung.png
- Repo https://github.com/ThomasSchmiegelt/sketch-to-prompt angelegt (oeffentlich, MIT, ~/sketch-to-prompt): allgemeine
  Fassung des Skizzen-Werkzeugs, README de/en, Beispielmodell, Screenshot (headless chromium + swiftshader).
- Stroemungsfilm f6 fertig: sim/kuehlung_segment/f6/animation/stroemung_f6_legende.mp4 (12 s, 360 Bilder EEVEE 32
  Proben, ~10 min Render; 1 s Film = 3 s phys.), Standbild standbild.png. Teilchen-npz geloescht (neu erzeugbar).
- f7 (2026-10-27, User: naechster Schritt + Film durchsichtig): Zelle vorn 0,10/5 mm, Schicht 0,13, Wand vorn ueber R
  abgestuft (neu: halbdicke_vorn_R, Program.cs Gyroid fDicke(R)). Ergebnis schlechter: 42 kPa, Streuung 58 %, innen fast zu
  (t 7,2 mm bei Zelle 0,1 schliesst), +-52 Grad weiter ~0. Ursache +-52: voxPlasma.voxOffset(310 mm) an der Schulter
  ~70 mm zu kurz -> dort dichter hinterer Gyroid im Band (Pruefung: Wasserzellen gegen beide Gyroid-Formeln je Abstand).
  Duenne Schicht ist in jeder Neigung gleich durchlaessig (Widerstandsnetz-Test), Neigung war nicht die Ursache.
- f8: Grenze der feinen Schicht = exaktes Netz (Auftrag vorn_stl), Wand 6,2->5,0 mm. Ergebnis 47,8 kPa, Streuung 48 %,
  +-52 weiter 0 -> Vermutung falsch. Richtige Ursache (Zellen 'Formel Wasser, Gitter Stahl' aufgetragen): INNENHAUT
  (voxOffset 180 mm) an der Schulter R 10-10,8 m ~50 mm zu dick -> Band dort um 1/3 verengt. Eigene Diagnosefehler
  unterwegs: Abstand ohne Vorzeichen zaehlte Plasmainneres mit (Wasseranteil scheinbar 0,37 statt 0,69).
  PicoGK-Gyroid selbst ist exakt (Test picogk/GyroidTest: Wandanteil 0,30-0,32 = Formel 0,30).
- f9: ALLE Versatzflaechen (spalt, haut_innen, haut_aussen, wand, vorn) als exakte Netze flaeche_*.stl (Auftrag
  flaechen_stl); Wand vorn 5,35/5,75/5,75/5,4/5,2/5,0 mm bei R 5,2/5,9/6,6/7,3/9/11 m.
- Skills ergaenzt (User-Wunsch): neu cae/skizze-zu-prompt; fluidx3d-lbm, blender-modell (durchsichtiger Film),
  picogk-voxel (Gyroid, Offset-Fehler), stellarator-surrogat. ~/Downloads/stelerator gibt es nicht mehr (in Skill vermerkt).
- f9 (exakte Flaechen): 37,8 kPa, Streuung 65 %, innen 30 l/s (zu offen), +-52 weiter 0. ECHTE URSACHE +-52 (seit f6):
  FluidX3D voxelize_mesh_on_device kippt einzelne z-Lagen (Strahlparitaet) -> Lage z=1,906 m ganz Stahl statt 58 % Wasser
  quer durchs Band. Beleg: Gitterzellen je z-Lage gegen select_enclosed_points auf wasser_gitter.stl.
- Abhilfe: PicoGK schreibt wasser_belegung.bin (Kopf 6 int + 4 float, dann je z-Schicht x-schnell 1 Byte; GetVoxelSlice,
  ACHTUNG Bildzeile 0 = groesstes y -> fValue(x, nYs-1-y)), kuehlung_cfd macht daraus cfd/belegung.bin (dx = Voxel),
  setup_kuehlsegment.cpp liest .bin statt STL zu voxelisieren. Pruefung gegen STL: 100 % gleich. f10 = f9-Parameter damit.
- f10 Ergebnis: 22,6 kPa, 288 l/s, Streuung 36 %, Einbrueche +-52 weg. Innen 22-24 l/s, oben/unten 7-9, aussen 13-15.
  f11: halbdicke_vorn_R 5.2:5.8,5.9:5.75,6.6:5.45,7.3:5.15,8.0:4.95,9.0:4.9,9.6:4.95,10.3:5.1,11.0:5.2,12.0:5.2
- f11 Ergebnis: Streuung 8 % (beste bisher), 22,0 kPa, 288 l/s, v Plasmaseite 0,10 m/s, Schicht vorn 0,18 m/s Mittel.
  Film durchsichtig: animation/stahl_ganz.stl (StlSchnitt voxel 10, z_max 1e7, ueber starte_begrenzt mit env DOTNET_ROOT).

- Film f11 durchsichtig fertig: sim/kuehlung_segment/f11/animation/stroemung_f11_durchsichtig.mp4 (12 s, 24000 Teilchen,
  EEVEE 32 Proben, ~12 min), standbild.png, legende.png. Einzelbilder bilder/ (1,1 GB) noch da, npz geloescht.
- 2026-10-27 abends (User: Gyroide im Film sehen, Gesamtbild + Bericht mit Erkenntnissen/Vorschlaegen, alles nach
  GitHub, FluidX3D ordentlich zitieren): blender_stroemung.py --gyroid (untere Haelfte undurchsichtig ohne Innenhaut:
  StlSchnitt voxel 6, z 0, flaeche_haut_innen.stl + 12 mm; obere Haelfte Roentgen mit z-Maske; Kamerafahrt 15/60/25 %)
  -> f11/animation_gyroid/. kuehlung_waerme.py (1D: Innenhaut 30 mm = 600 K, v 0,10 m/s -> h 1200, 415 K; 10 % Plasmaseite
  < 1 mm/s). gesamtbild_kuehlung.py -> docs/bilder/gyroid_gefaess_1GW_gesamt_kuehlung.jpg. Projektbericht de/en:
  Abschnitt Kuehlung + FluidX3D und 7 Referenzen + PicoGK + sketch-to-prompt. fluidx3d/ (README, LICENSE, setup, defines
  geaendert) im Repo freigegeben (.gitignore). README Abschnitt Kuehlung, Filme docs/filme/ (komprimiert).
  GyroidTest-STLs nach sim/kuehlung_segment/gyroidtest/ verschoben (nicht ins Repo).
- Gepusht 7d18a78 (User: "alle nach github"). User findet Gyroid-Film super. Zwischendateien der Filme geloescht
  (Einzelbilder, npz, .blend, stahl_ganz/stahl_unten.stl; neu erzeugbar), Filme + Legenden + Standbild bleiben.
- REGEL (User 2026-10-27): Austrittsdurchmesser immer groesser als Eintrittsdurchmesser (f11: d_ein 300, d_aus 400 mm).
- Erstwand-Kanaele (User-Wahl): stellarator/erstwand_kanal.py (1D Gnielinski + Elmer-Querschnitt). k1-k4 bei
  290->300 C/15,5 MPa: 10x10 mm, Steg 4, Haut 5 -> Stahl max ~437 C. User-Vorgabe danach: Wasser max 150 C, Eintritt 60 C
  (dT 90 K -> nur 35 l/s je Segment) -> Kanaele in Reihe (--durchgaenge): n3 6x6 mm, 3 Durchgaenge, 1,5 MPa:
  v 1-2 m/s, 49 kPa, Stahl max 300 C, Kanalwand 202 C (= Sieden 198 C -> Druck auf 2 MPa). Doppeltes Filament
  (innen Kuehlung, aussen Steifigkeit) = dieses Konzept; Kollision mit Spulen noch pruefen (Abstand Plasma->Gehaeuse min 1,25 m).
- Schnitt-Werkzeug (User-Wunsch): stellarator/schnitt_werkzeug.py/.html, Port 8766, Skill cae/stroemung-schnitte.
- Bericht neu gegliedert (User): S.1 Einleitung/Beweggrund, Inhaltsverzeichnis eigene Seite, jedes Kapitel neue
  Seite (titlesec \sectionbreak), Bildpaare untereinander 0,9 Breite statt nebeneinander.

## 2026-10-27 Doppeltes Filament, Abstand, Name im Gesamtbild
- Erstwandkanäle n5 (60→150 °C, 2 MPa): 6×6 mm, 3 Durchgänge, 1–2 m/s, Δp 49 kPa, Stahl ≤ 300 °C, Kanalwand 202 °C (< 212 °C Sieden). stellarator/erstwand_kanal.py
- Abstand Plasmarand → Gehäuse min 1,25 m (Verbinder 1,70 m), Segment 85–95° ≥ 1,88 m; Wand 1,05 m + 5 cm passt überall. stellarator/gefaess_abstand.py
- Wandstück doppeltes Filament: picogk/WandStueck + stellarator/blender_wandstueck.py, Bild sim/wandstueck/d1/wandstueck_beschriftet.png
- Gesamtbild Kühlung: "© Thomas Schmiegelt" + Repo-Link unten links (direkt ins JPG gestempelt, Filmbilder sind gelöscht; Skript angepasst)
- Blei/Bleilithium statt Wasser in den Erstwandkanälen (stellarator/blei_kanal.py, sim/blei/b1..b5), Idee des Users "Gyroid im Gyroid, Blei gibt Wärme an Wasser ab":
  - Wärmetauscher Blei→Wasser IN der Wand verworfen: Blei friert bei 327 °C am 60–150-°C-Wasser fest, Leck Blei/Wasser am Plasma gefährlich. Stattdessen Dampferzeuger außerhalb der Spulen.
  - MHD bei 6 T (dp = σ v B_quer² k_p L): Kanäle toroidal (fast entlang B, Steigung ~6° geschätzt) 247 kPa mit Stahlwand, 27 kPa isoliert; poloidal 21 MPa; Gyroid 14 MPa -> Gyroid für Flüssigmetall ungeeignet.
  - b5 (empfohlen): 10×10 mm, Steg 4, Innenhaut 3 mm, Blei 340→420 °C, 0,87 m/s, 103 l/s, Stahl max 537 °C, Kanalwand 478 °C, Pumpe 0,2 % der Wärme. b1 (20 mm, 350→500 °C): Stahl 711 °C zu heiß.
  - Grob: Nu = 5, keine 3D-MHD in Kehren/Verteilern, Stoffwerte ungeprüft, Korrosionsgrenze Stahl/Blei nicht geprüft.
- Name auf Bildern: "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell" + FluidX3D-Nennung, kein ©-Zeichen (User fand © zu gewerblich).
- 2026-10-27: Für PI zusätzlich verlinkt (~/.pi/agent/skills/ → ~/.hermes/skills/cae/): blender-modell, picogk-voxel, stroemung-schnitte, skizze-zu-prompt. PI hat jetzt alle 11 Projekt-Skills.
- 2026-10-27: Berichte DE/EN um Kapitel 'Doppeltes Filament, Bauraum und Flüssigblei' ergänzt (35/33 S.), Prozess-Doku Abschnitt 8. Autorenname FluidX3D aus Fließtext/Bild entfernt (User-Wunsch), in LICENSE/Kopfzeilen/Zitaten bleibt er (Lizenz).
- 2026-10-27 Referenz-Kühltemperaturen recherchiert:
  - DWR primär ~290–330 °C, 15,5 MPa; sekundär gesättigter Dampf ~6,2 MPa / 275 °C (Wikipedia-Spiegel, tpu.ru).
  - DEMO-WCLL: 295/328 °C, 15,5 MPa (EUROfusion WPPMICP16_15575).
  - DEMO-HCPB: He 8 MPa, 300 → 500/520 °C, EUROFER-Grenze 550 °C (KIT/EUROfusion).
  - DCLL: PbLi 300–550 °C wegen EUROFER (EUROfusion WPBBCP16_15491).
  - ALFRED (Blei): 400 → 480 °C, ~0,1 MPa, Endstufe 520 °C (IAEA ARIS, NEA).
  - ITER-TCWS: bis 126 °C, 4 MPa; Erstwand-Austritt ~110 °C.
  - Konsequenz: 60→150 °C ist ITER-Niveau (Versuchsanlage). Für Strom DWR/WCLL-Werte oder Blei 400→480 °C nehmen. EUROFER unter ~300 °C unter Bestrahlung spröde -> kalte Wasserwand problematisch.
- **UEBERGABE 2026-10-27 19:58:** Hermes recherchiert Kühltemperaturen (Auftrag docs/recherche/auftrag_kuehltemperaturen.md), Ergebnis -> docs/recherche/kuehlkreislauf_temperaturen.md, Log sim/hermes_recherche.log (Ende = Zeile HERMES_FERTIG). Danach prüfen (Quellen stichprobenartig) und dem User zeigen.
- **UEBERGABE 2026-10-27 20:01:** f12 = f11 mit Innenhaut 5 mm, d_aus 500 mm (User). Geometrie läuft (sim/kuehlung_segment/f12.log, Ende GEOM_ENDE). Geometrie fertig (Stahl 16,9 m³, Wasser 12,0 m³). Kette sim/kuehlung_segment/f12_kette.sh wartet auf HERMES_FERTIG + GPU < 3 GB, dann Probe + CFD (Log f12_kette.log, Ende KETTE_ENDE). Danach Auswertung wie f11 (Streuung, Δp, v Plasmaseite, kuehlung_waerme.py).
- 2026-10-27 User: 'nach dem Lauf alles beenden' -> f12_abschluss.sh: nach KETTE_ENDE kuehlung_waerme --name f12 (f12_waerme.log), dann Schnitt-Werkzeug-Server (PID 8869) beenden. Keine weiteren Läufe starten. Auswertung/Bilder beim nächsten Sitzungsbeginn ansehen.
- 2026-10-27 Hermes-Recherche fertig (docs/recherche/kuehlkreislauf_temperaturen.md), aber Spaltreaktor-Teil fehlerhaft/erfundene Links -> Prüfhinweis oben eingefügt; nicht committen, bevor geprüft. Hermes-Websuche lief in Schleife (loop_web_search_cap).

## 2026-10-27 NAECHSTES MAL: Recherche mit PI statt Hermes
- Hermes (qwen3.8:27b lokal) hat die Recherche verhauen (Note 5): Websuche in Schleife, Werte und Links erfunden.
- User will die Recherche naechstes Mal mit PI probieren. Dafuer braucht PI Scraping-Faehigkeit: Seiten wirklich
  abrufen und daraus zitieren (z. B. Skill/Extension mit curl + Text-Extraktion, Quellen-URL bei jedem Wert Pflicht).
- PI laeuft auch auf lokalen Ollama-Modellen (qwen-gross, qwen3.5:9b, ...): Scraping hilft, aber Modell bleibt Engpass.
  Regel fuer die Aufgabe: nur Werte, die woertlich in einer abgerufenen Seite stehen; sonst "nicht gefunden".
- Ausserdem offen: f12 auswerten (CFD fertig 21:10, auswertung.json fehlt, kuehlung_waerme scheiterte).

## 2026-10-28 f12 ausgewertet (Innenhaut 5 mm, d_aus 500 mm)
- auswertung.json fehlte, weil kuehlung_cfd.auswerten() nicht automatisch laeuft -> von Hand:
  `.venv/bin/python -c "from stellarator.kuehlung_cfd import auswerten; from stellarator.kuehlung_segment import WURZEL; auswerten(WURZEL/'f12')"`
  Danach `-m stellarator.kuehlung_waerme --name f12`. (Kette kuenftig mit Auswertung vor kuehlung_waerme!)
- f12 vs f11: Streuung Kern 11 % (8 %), Druckverlust 19,4 kPa (22,0), 289 l/s (288), v_aus 1,49 m/s (2,35),
  v Plasmaseite 0,10 m/s gleich, 10 % Totwasser < 0,7 mm/s. Waerme: Leitung 5 mm = 100 K (statt 600 K bei 30 mm),
  Uebergang bei 0,10 m/s weiter ~410 K -> Engpass ist die Geschwindigkeit an der Plasmaseite, nicht die Wand.
- Bild: sim/kuehlung_segment/f12/cfd/auswertung.png

## 2026-10-28 Skill web-recherche (fuer PI, auch Hermes)
- ~/.hermes/skills/cae/web-recherche/: suche.py (Wikipedia, OSTI, OpenAlex, arXiv; KEINE Suchmaschinen - DuckDuckGo
  sperrt Automaten, nicht umgehen), abruf.py (Seite/PDF -> ./recherche_ablage, --suche, --zeilen), pruefe.py
  (jedes Beleg: "Zitat" (URL) muss im abgerufenen Text stehen, sonst FEHLT/ERFUNDEN?). Link in ~/.pi/agent/skills.
- PI-Lauf: docs/recherche/pi/ (auftrag.md, pi.log, ergebnis.md), Modell qwen-gross ueber Ollama.
- Achtung: `pi` (~/.local/bin/pi) ist ein Startskript, das den Orchestrator auf :5000 startet, auch bei --help.
  Direkt: ~/.npm-global/bin/pi -p --provider ollama --model qwen-gross:latest --skill <ordner> "..."

## 2026-10-28 Paarvergleich der Kuehlvarianten (stellarator/varianten_vergleich.py)
- Idee User: Vorgehen/Optimierungsschleifen per Paarvergleich steuern. Werkzeug: Pareto-Front + AHP-Gewichte + Rang,
  Ausgabe sim/kuehlung_segment/vergleich/. f6-f9 ausgeschlossen (Gitterfehler).
- Urteile des Users (AHP): temperatur>streuung=5, temperatur>druck=5, temperatur>totwasser=5, druck>streuung=3,
  streuung=totwasser, druck>totwasser=5 -> Gewichte Temperatur 0,61, Druck 0,23, Streuung 0,08, Totwasser 0,08, CR 0,10.
- Rang: f12 0,73 > f5 0,69 > f2 0,58 > f11 0,42 > f10 0,38 > f1 0,30. Alle ausser f10 auf der Pareto-Front.
- Hinweis daraus: f5 (zelle_vorn 0,2, Z-Verteiler) hat v Plasmaseite 0,137 m/s und nur 7,9 kPa; mit 5 mm Haut waere
  sein Temperaturanstieg ~475 K < f12 (513 K). Kandidat f13: f12-Haut + groebere vordere Zelle / f5-Verteilung.

## 2026-10-28 Festigkeit der Innenhaut (stellarator/haut_festigkeit.py, Elmer)
- Platte ueber 2x2 Gyroid-Zellen (a 100 mm, Wand 10 mm eingespannt), Druck von der Wasserseite, linear (1 MPa gerechnet).
  Pruefung Streifen: 34,3 vs Formel 32,0 MPa/MPa (t 5 mm). Ergebnis sim/haut_festigkeit/gyroid/ (haut.png).
- sigma je MPa Druck: t 5 mm 39,2 / 10 mm 14,4 / 15 mm 9,3 MPa -> zulaessig (~150 MPa) bis 3,8 / 10,5 / 16 MPa Druck.
- Folge: f12 (5 mm) nur bis ~3,8 MPa -> Blei (drucklos) ok, ITER-Wasser 4 MPa knapp drueber, 15,5 MPa nur mit 15 mm
  Haut oder Druckwasser nur in kleinen Erstwandkanaelen (doppeltes Filament). Temperaturspannungen fehlen noch.
- varianten_vergleich.py: Festigkeit als Ausschluss (--druck). Bei 4 MPa faellt f12 heraus (157 MPa), f5 ok (91).

## 2026-10-28 PI-Recherche fertig (docs/recherche/pi/ergebnis.md)
- Eine Anlage je PI-Aufruf (lauf.sh) klappt: 29 Belege bestaetigt, 0 Fehler, 2-5 min je Anlage.
  Erster Versuch alles in einem Aufruf: 22 Abrufe, nichts geschrieben (Kontext 64k voll) -> abgebrochen.
- Deutungsfehler, die pruefe.py nicht sieht: BREST/ALFRED Ein/Aus vertauscht (Dampferzeuger-Bezug) -> korrigiert.
- Belegt: EPR 295,2/320 °C 15,5 MPa; WWER-1000 289/319 °C 16,0 MPa; BREST 340/540; ALFRED 390/520 drucklos;
  Superphenix Na 550 °C atmosphaerisch; HTR-PM He 250/750 °C 7,0 MPa (OSTI); ITER 70 °C 4 MPa (iter.org);
  DEMO HCPB He 300/500 °C 8 MPa (KIT). Luecken: DEMO WCLL (Verlage 403), W7-X, ITER-Austritt.
