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
- **Stufe 1 `qa_nfp2` (DESC, GPU)** laeuft losgeloest seit 2026-10-24 13:05: `sim/invers/qa_nfp2/stufe1.log`
  (Fortschritt `[k=1..4]`, Ende `ENDE 0`). Danach (Skill `stellarator-invers`):
  1. Stufe 2: `.venv-opt/bin/python invers/stufe2_spulen.py --wout sim/invers/qa_nfp2/wout_qa_nfp2.nc --name qa_nfp2_spulen`
  2. Falldatei wie `stellarator/faelle/ref_precise_QA.json` mit `datei` = `sim/invers/qa_nfp2_spulen/spulen.json`
  3. `bewerte --bild` + `ansicht`; mit Referenz ref_precise_QA vergleichen (stufe1.json: qs_fehler vs. Referenz).
  Wenn qs_fehler >> 1e-3: Stufe 1 mit mehr maxiter / hoeherem k_max wiederholen.
- Lange Laeufe IMMER losgeloest starten: `setsid nohup bash -c '...' > log 2>&1 < /dev/null &`.

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
- **Sudo** (FreeCAD) — Passwort nötig oder Blender.
- **Disk ~99 %** — bei jeder Installation `df -h /` prüfen.
- **Tavily Rate-Limit** (60 s Pause) — Websuchen einzeln.
