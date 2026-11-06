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
0c. **ZURÜCKGESTELLT (User, 2026-11-03): allgemeiner Weg STL → STEP** ausdenken (nicht nur fuer
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

## 2026-10-28 ENTSCHEIDUNG User: bestehende AKW-Turbine verwenden, Rest moeglichst einfach
- Folge: Primaerkreis Druckwasser wie DWR/WWER-1000 (belegt 289 -> 319 °C, 16,0 MPa), Standard-Dampferzeuger + Turbine.
  1 GW netto ~ 1,2-1,3 GWe brutto -> eine grosse DWR-Turbine (WWER-1000-/Konvoi-Klasse).
- Druckwasser nur in kleinen Erstwandkanaelen (doppeltes Filament), Gyroid trocken als Stuetze. Kein Blei, kein Helium.
- Nachgerechnet (erstwand_kanal, 6x6 mm, 3 Durchgaenge, Drossel): w1000 289->319 °C 16 MPa: Stahl max 441 °C,
  Kanalwand 340 °C (Sieden 345 °C, nur 5 K Abstand), dp 232 kPa. w440 269->300 °C 12,5 MPa: Stahl 423 °C,
  Kanalwand 322 °C (Sieden 326 °C). Stahl damit im EUROFER-Fenster 300-550 °C (bei 60-150 °C war er darunter).
- Offen: Blanket (80 % der Leistung als Neutronen) braucht dieselben Bedingungen -> WCLL-artig (Werte noch unbelegt).
- Waermebilanz (stellarator/waermebilanz.py, sim/waermebilanz/): P_th 3419, P_fus 3053, Blanket 2808, Erstwand 305
  (0,25 MW/m2), Divertor 305 (>= 31 m2 bei 10 MW/m2), brutto 1197 MW; Wasser 17400 + 1890 kg/s. Isar 2 (Konvoi):
  3950 MWth/1485 brutto -> eine Turbine reicht; WWER-1000 (3000 MWth) zu klein. Kapitel sec:bilanz/sec:balance in
  beiden Berichten (DE 40 S., EN 38 S.), Prozess-Doku Abschnitt 9. REGEL User: immer im Bericht mit Herleitung dokumentieren.

## 2026-10-28 Kuehlsystem: Leitungen durch die Spulenspalte (stellarator/rohr_durchfuehrung.py)
- User: Kuehlsystem noch nicht fertig -> weiter + Doku erweitern. Offen nach Waermemenge: Blanket 2808 MW (82 %, nicht
  ausgelegt, Tritium), Erstwand 305 (nur Querschnitt; Verteiler, Einbau, CFD fehlen, 5 K bis Sieden), Divertor 305,
  Leitungen, Temperaturspannungen, Sicherheit (16-MPa-Bruch im Vakuum).
- Leitungen geprueft: gerade Rohre entlang der Normalen ab Plasmarand + 1,05 m, 4 m nach aussen, Abstand zu allen
  Spulenteilen des Surrogats minus 0,15 m Waermeschild. Noetig 26,4 m3/s je Richtung: bei 0,8 m / 10 m/s 11 Rohre,
  moeglich ~410 (vorsichtig 0,3 m Schild, 5 m/s: 22 noetig, 340 moeglich). 19 % der Oberflaeche frei fuer 0,8 m.
  Fenster aussen, oben, unten; innen fast zu -> inneres Blanket ueber Sammler oben/unten.
- Doku: Berichte DE (41 S.) / EN (39 S.) Unterabschnitt "Passen die Leitungen...", README, Prozess-Doku Abschnitt 9.
- Naechster Schritt Kuehlsystem: Blanket (82 % der Waerme) - Aufbau mit Druckwasser + Brutstoff.

## 2026-10-28 FluidX3D gesichert
- Private Sicherung ~/sicherung/ (Spiegel FluidX3D.git + bundle, LIESMICH). Lizenz erlaubt Kopie/Aenderung privat.
- User fragt nach Anpassung "hinsichtlich Plasma": Empfehlung FluidX3D bleibt fuer Kuehlmittel; Plasma-Waermelast
  auf den Divertor besser per Feldlinienverfolgung (vorhandene Biot-Savart-Spulen), siehe Antwort im Chat.

## 2026-10-28 WCLL belegt (User lud PDF: ~/Downloads/energies-16-02069-v2-1.pdf)
- docs/recherche/wcll/wcll_werte.md: 13 Belege, 0 Fehler (pruefe.py kann jetzt file://). Wasser 295->328 °C 15,5 MPa,
  zwei Kreise FW/BZ, DWT, EUROFER <= 550 °C, TBR 1,14 (Ziel 1,15), FW 0,32 MW/m2, DEMO 1998 MW / 500 MWe / NWL 1,04.
- Abgleich im Bericht (Unterabschnitt "Blanket: Abgleich mit WCLL", DE 42 / EN 40 S., \cite{arena2023}):
  Druckwasser bestaetigt; PbLi als Brutstoff (nicht Kuehlmittel); unsere NWL 1,99 = 2x DEMO; TBR knapp.
- User-Hinweis: Gyroid liegt punktuell/linienfoermig auf -> Kerben/Ermuedung an den Anschluessen, offen.

## 2026-10-28 IDEE User: gestufte Struktur statt Gyroid mit Linienauflage
- "Auf der Blanketseite flaechige Auflage, dann ist es ein Spiel: Straenge nicht zu dicht (Wasser), dick genug fuer
  Waermeleitung; nach aussen stark veraesteln und duenn."
- Abschaetzung (16 MPa, Haut 5 mm, 150 MPa): Stuetzabstand b <= 20 mm (4 MPa: 39 mm); Rippenwirkung nur 3-15 mm tief
  (2/m, m = sqrt(4h/(k d)), k 25); Zuganker-Querschnitt ueberall >= p/sigma = 11 % (4 MPa 3 %), veraesteln erlaubt.
- Falle: dichte Hautlage hat hohen Widerstand -> Wasser umgeht sie; braucht eigene Zufuehrung (Ringkammer direkt in die Lage).
- Vorschlag: PicoGK-Wandstueck mit abgestufter Zelle/Dicke, Elmer (Haut 16 MPa + Temperatur), FluidX3D (Durchstroemung). Wartet auf User.
- GradientWand g1 gebaut (picogk/GradientWand, sim/gradientwand/g1): 240x240x600 mm, Voxel 1 mm, 43 s, 2 GB RAM;
  Lagen Zelle 20/40/80/160, Dicke 2,5/3/4,5/8, bis 30/80/180/570 mm; Porositaet 0,84. Bilder gesamt.png, haut_nah.png
  (blender_wandstueck.py jetzt mit --ohne_wasser --zoom --ziel_z --bild). STL gross (stahl_ganz 346 MB, wasser 368 MB).
  Doku: Berichte DE 44 / EN 42 S. (Unterabschnitt "Abgestufte Struktur"), README. Naechst: Test Durchstroemung + Festigkeit.
- 2026-10-28 Push 2daa5f8 (WCLL, GradientWand, Berichte). Danach Waermetest stellarator/gradient_waerme.py (Elmer HeatSolve,
  Voxel 0,5 mm, Ausschnitt 80x80x100 mm von g1, 1,4 Mio Elemente, 2:20 min je 3 Faelle, 2,8 GB RAM), q 0,5 MW/m2, h 1e4, 304 C.
  Ergebnis: Stahl gibt 95 % in den ersten 5 mm hinter der Haut ab (Rippe wirkt nur sqrt(kt/2h) ~ 2 mm), Plasmaseite 469 C,
  nasse Wand 364 C > Sieden 344,8 (an den Strangwurzeln). Fleck 2q: 588/399; +3 mm W: 535/377; h doppelt: 559/363;
  Kupferlegierung k 320: 351/340 und nur 62 % in 5 mm (einziger Fall, der Waerme in die Tiefe bringt).
  Doku: Berichte DE 47 / EN 45 S. (Unterabschnitt sec:waermebreite, \cite{bejan1997}), README, Prozess-Doku. NICHT gepusht.
  Naechst moeglich: Blanket-Volumenwaerme mit verzweigten Pfaden, Kupfer-Hautlage, Durchstroemung FluidX3D, Festigkeit.
- 2026-10-28 Nutzer-Idee: Gyroid besser als Zwei-Fluid-Waermetauscher (zwei getrennte Kanalnetze) statt Waermeleiter in der
  Erstwand; Kondensator-Abwaerme (~2200 MW, ~33 C) nutzen, geschlossener Kreislauf. Vorschlaege (Divertor-Vorwaermer
  ~2000 m2/7 m3, Gyroid-Dampferzeuger ~23000 m2/75 m3, Kondensator: Dampf 0,05 bar ~25000 m3/s -> kleine Zellen ersticken,
  Trockenkuehlturm, Tritium-Zwischenkreis) werden AB FREITAG 2026-10-30 gebaut. Erst fragen: Kondensator oder Vorwaermer.
- 2026-10-28 Fahrplan Richtung Forschung (Nutzer: der Reihe nach, Versuch teuer -> Gelder; Firma hat CFD- und
  Festigkeitsleute, vorher guter Stand noetig): Frage/Hypothese -> Literatur mit Messwerten -> Validierung + Netzstudie ->
  Bandbreiten -> Review-Paket mit konkreten Fragen -> Fachleute/Gelder -> Versuch. Erstes Thema: Gyroid-Tauscher ab Fr.
- 2026-10-28 Forschungsthema Mensch+KI (Nutzer: "ernsthaft angehen", "was du weisst, jetzt schon rein"):
  docs/forschung/ereignisprotokoll.md mit Kategorien IN/IK/FK/FA/EN/EK/V/K/R/S, 52 Ereignisse (45 rekonstruiert, 7 live),
  erste Auszaehlung. AB JETZT: in jeder Sitzung Ereignisse live nachtragen (Spalte Erf. = live). README-Absatz ergaenzt.
- 2026-10-29 Ereignisprotokoll erweitert (Nutzer): Projekte EMA (ai-workspace, aus Buch-Zeitleiste + Commit-Texten),
  H2 (wasserstoff LESSONS_LEARNED), Doom, AI_Framework (nur Doku). IDs F-/E-/W-/D-/A-, 94 Ereignisse, neue Spalten
  "Unerw. KI" (–/!/!!) und "Unerw. N" (fuer den Nutzer, leer). 8 Muster als Hypothesen. Nicht gepusht.
- 2026-10-31 Ereignisprotokoll VERSCHOBEN ins Buchprojekt (lokal, nicht im Repo) (Nutzer: gehoert
  nur zum Buch). Aus dem Fusion-Repo entfernt (war nie gepusht), README-Absatz zurueckgenommen. Weiterhin live fuehren, dort.
- 2026-10-31 Weiter mit Gyroid-Zwei-Fluid-Tauscher: Nutzer waehlt DIVERTOR-VORWAERMER als Start (Fahrplan Schritt 1).
- 2026-10-31 Schritt 2 Vorwaermer gestartet: docs/recherche/vorwaermer/lauf.sh (PI, 5 Themen: Divertor EU-DEMO/ITER/W7-X,
  DWR-Speisewasser, Vorwaermkette), Log lauf.log, Ende PI_FERTIG. Teil 3 (Gyroid/Platte/Rohr Nu, f) macht Claude.
  Frage (Nutzer: Effizienz zaehlt): welche Bauart holt den meisten Netto-Strom aus 305 MW Divertor-Waerme.
- 2026-10-31 Nutzer: DANACH dem PLASMA widmen (nach dem Vorwaermer).
- 2026-10-31 FEHLER korrigiert: Siedetemperatur 16 MPa = 347,4 C (nicht 344,8 = 15,5 MPa; SIEDE-Tabelle in erstwand_kanal.py
  endete bei 15,5). Tabelle bis 17 MPa ergaenzt, gradient_waerme neu gerechnet (ueber Sieden 2,7 statt 3,0 %, Kupfer
  Reserve 7,9 K), Berichte/README korrigiert (w1000 Abstand 7 statt 5 K). CoolProp in .venv installiert.
- 2026-10-31 VORWAERMER gerechnet: stellarator/vorwaermer.py (CoolProp-Expansionslinie 78 bar sat, ZUE 11 bar/270 C,
  eta 0,85/0,88 ANNAHMEN; Kondensat 1820 kg/s, 2 MPa; Gegenstrom, Scan Annaeherung/d_h/Verhaeltnis/v/n Durchgaenge,
  Pareto Netto ueber Volumen). Ergebnis: Obergrenze 73,3 MW (24 %), alle Bauarten ab ~30 m3 72,9-73,1 MW -> Wirkungsgrad
  entscheidet NICHT; Volumen 99 %: Gyroid abgestuft ~4, Diamond/Gyroid 4,5-5, Platte 7, Rohr 30 m3. Korrektur Bilanz:
  Divertor zaehlte mit 0,35 -> Pfus ~3140 statt 3053 MW (+3 %, im Bericht als Befund, Tabelle oben NICHT geaendert).
  Re_warm/Re_kalt ~7 geometrieunabhaengig -> n Durchgaenge. 50 mbar: 63,5 MW; 75 % Kondensat: 68,7 MW.
  Rechte: Lizenzen in docs/recherche/vorwaermer/*.md, Zitierhinweis §§ 51/63 UrhG in Berichten. Berichte DE 50/EN 48 S.,
  README, Prozess-Doku Abschnitt 10. NICHT gepusht. Naechst: Kassettenkoerper 180-210 C als hoehere Stufe? danach PLASMA.
- 2026-10-31 Tauscher-CFD (FluidX3D periodisch, Kernel-Mods siehe fluidx3d/*.diff): Gyroid Re~3000 n48: f 0,805, Nu 194;
  n96 (18,5 Mio Zellen): f 0,674 (Re 3224), Temperatur stabil bis ~160k Schritte (T_m 0,51 -> Nu ~150), dann divergiert.
  Nu faellt mit Gitter (194 -> ~150), bleibt ~1,9x Renon (80). Thermik bei n96 instabil -> Ursache klaeren vor Reihe.
  Gyroid-Video fertig: sim/tauscher/cfd/gyroid_re3000_n48/video/gyroid_stroemung.mp4. Chevron-FreeCAD (zu speicherhungrig)
  ohne STL beendet -> sparsamer neu bauen. Einflussgraph Plasma->Netz als Artifact (privat). NICHT dokumentiert/gepusht.
- 2026-10-31 Doku: Leistungsfluss-Bild (stellarator/einflussgraph.py, docs/bilder/einflussgraph*.png) + Bauteiltexte
  (Sonnet-Teilagent, geprueft: bauteile_de.tex/components_en.tex/bauteile_bib.tex, docs/bauteile.md) als Abschnitt
  nach der Waermebilanz; CFD-Kapitel tauscher_cfd_de/en.tex nach dem Vorwaermer (Bilder via tauscher_cfd_bild.py).
  Berichte DE 55/EN 52 S., README, Prozess-Doku Abschnitt 11. Laeuft: video_alle.sh (Diamond, Chevron n48 + Videos).
  Offen: Protokoll-Zeilen im Buch, fluidx3d/README, Helium-Abpumpen belegen. NICHT gepusht.
- 2026-10-31 abends: n96-Instabilitaet = BGK-Temperaturstoss nahe tau 0,5 -> TRT (Ginzburg, Lambda 1/4) im Kernel;
  Quelle wahlweise ~u_z (--quelle u, Patankar 1977; Platte exakt 8,235: 8,9 -> 8,5). Reihe reihe_trt.sh (n48/n96):
  n96 Gyroid f 0,73 Nu 102 j/f^1/3 0,038 | Diamond 0,60/101/0,039 | Chevron 0,86/104/0,033. Nu/Renon 1,8 (n48) ->
  1,5 (n96) -> Richardson ~1,2. BGK ueberschaetzte Nu ~25 %. Berichte DE 56/EN 53 S. aktualisiert (Tabelle, Bilder
  tauscher_cfd_bild.py), README, Prozess-Doku, fluidx3d/README+Diffs. Naechst: n144 (60 Mio Zellen) oder Surrogat;
  gestufte Geometrie rechnen. NICHT gepusht.
- 2026-10-31 Sitzungsende: alles beendet, keine Laeufe aktiv. Videos gesammelt in sim/tauscher/videos/. Morgen:
  Entscheidung n144 / gestufte Geometrie / Surrogat; vor Push picogk/GyroidTauscher auf bin/obj pruefen; Push nur mit OK.
- 2026-11-01: Surrogat-Laeufe gestartet: sim/tauscher/cfd/surrogat/ (auftraege.txt 36 Auftraege, runner.sh,
  steuerung.sh pause|sofort|weiter|stop|abbruch|start|status). Phase A n144 Gyroid/Diamond, B 28 LHS-Punkte n48
  (Re 500-10000, Pr 1,2-2,0, a 0,75-1,6 x Standard), C 6 Kontrollen n96. Monitoring: Sonnet-Teilagent -> monitor.md.
  tauscher_cfd.py hat --tag. Danach: Gitterfehler bestimmen, Co-Kriging-Surrogat, Anwendung Stufung im Vorwaermer.
- 2026-11-01 12:40: Auftragsliste fertig, 36/36 ohne Fehlschlag (Sonnet-Monitor 2x, kein Eingriff).
  n144: Gyroid Nu/Renon 1,36, Diamond 1,30 -> Reihe 48/96/144 NICHT asymptotisch (d96/d144 = 0,58 < ln2/ln3).
  stellarator/tauscher_surrogat.py: GP je Bauart auf ln(Nu/Renon), ln(f/Renon) ueber (ln Re, Pr, a); Gitterkorrektur
  linear in ln Re aus n96, Stufen n144 (gerechnet) und inf (Richardson letzter Schritt, p 1,33). Ergebnis: Nu extrapoliert
  = Renon (0,97-1,14); f-Extrapolation unbrauchbar -> f aus n144. LOO Nu 2,8/0,9 %, f 9,5/1,1 %. Daten daten/tauscher_surrogat.json.
  stellarator/vorwaermer_stufung.py: Segmentmodell 8 Segmente, Zelle je Segment frei -> STUFUNG BRINGT NICHTS, kleinste
  Zelle (a 0,75 a_std, d_h 1,33 mm) gewinnt ueberall, Pumpen < 1 MW; 95 % von 73,3 MW bei 1,3-1,5 m3.
  Oh-Faktor 1,28 = Abstand Renon -> n144. Berichte DE/EN sec:tauschersurrogat / sec:exchangersurrogate (59/55 S.).
  Offen: feinere Zellen als Surrogat-Rand, Wand 0,5 mm gegen 3 MPa, Stufung evtl. Kondensator-Dampfseite. NICHT gepusht.
- 2026-11-01: Surrogat-Doku erweitert (warum, wie GP, mehrstufig) in Berichten + README, gepusht b75ead6/83125cd,
  GitHub-Beschreibung + Themen fluidx3d/cfd/heat-exchanger (20 Themen = Grenze).
  PLASMA: stellarator/plasma_waerme.py (HTS-Auslegung Stufe 0): Q 17,59 MeV, Coulombwall 444 keV, Gamow 39 keV,
  Lawson-Min 2,8e21 bei 13,6 keV, P_fus aus Profilen 3051 MW (Stufe 0: 3053), Haelfte in 14 % Volumen, 0,47 kg T/Tag,
  Alpha Larmor 4,2 cm, tau_s 0,2 s, 80 % an Elektronen; P_alpha 611 = 482 Transport + 129 Brems.
  BEFUND: f_div = 0,5 zu guenstig -> ohne Randstrahlung 482 MW auf Divertor, >= 48 m2 statt 31. Kapitel sec:plasma
  DE/EN (63/59 S.). Plasma-Teil NICHT gepusht. Naechstes: 1-D-Transport, Linien-/Zyklotronstrahlung, Divertor.
- 2026-11-01 16:30: ALPHA-BAHNEN (Variante A der Nutzerfrage „dynamische Simulation mit Magnetfeld“; FluidX3D fuers
  Plasma ungeeignet, B = Flüssigmetall-MHD spaeter). stellarator/alpha_bahnen.py (.venv-opt, simsopt gc_vac):
  Einheitsgeometrie mit v_u = v B_u/(B0 L), rho_L/a 0,018, t_phys = t_u B_u/B0. Hauptlauf losgeloest:
  sim/alpha/hts_1gw/lauf.log (1000 Alphas, 0,2 s, 6 Prozesse, ~4-5 h), Bahnen fuers Video bahnen.log.
  Fallen: SurfaceClassifier h=0.005 haengt (0.01 nehmen); multiprocessing nur mit spawn + OMP_NUM_THREADS=1.
  Offen: alpha_auswertung.py (Verlustanteil ueber t, Energieverlust mit Abbremsung, Trefferkarte Wand), Video, Doku.
- 2026-11-01 17:30: ALPHA-LAUF neu (erster Versuch: systemd-oomd beendete 16:27 ein ganzes Terminalfenster, 14
  Prozesse!). Ursachen: SurfaceClassifier h=0.01 ~9 GB/Prozess -> h=0.02; simsopt behaelt trotz forget_exact_path den
  ganzen Weg -> Zeitabschnitte 2 ms. Jetzt in systemd-run --user --scope MemoryMax=20G (Einheit alpha-hts), 5 Prozesse,
  ~13 GB, ~2 h. Erste 60: ~15 % verloren.
  VARIANTE B vorbereitet: ~/fluidx3d_mhd (sauberer Klon 50150a7), Schalter MHD, Lorentzkraft halbimplizit,
  Hartmann-Pruefung stellarator/mhd_hartmann.py: Ha 0: 0,03 %, Ha 5: 0,1 %, Ha 30/a 32: 4,3 %, Ordnung 2;
  Regel: >= 2 Zellen in der Hartmann-Schicht a/Ha. Diffs fluidx3d/mhd_*. Naechstes B2: Potential phi (Poisson) fuer
  Kanaele mit Seitenwaenden (Shercliff/Hunt), dann PbLi im Spulenfeld (Ha real ~1e4 -> skaliert + Gesetze).

2026-11-01 LESEHILFEN: Alle 41 Berichtsbilder (DE+EN) haben jetzt einen Absatz \lesehilfe{...}
  („So liest man das Bild:“ / „How to read the figure:“), Makro in projektbericht.tex / project_report_en.tex.
  Regel: jedes neue Bild bekommt eine Lesehilfe fuer Nicht-Physiker. siunitx alt: kein \SI{a x b}{..},
  stattdessen $a\times\SI{b}{..}$. PDFs: DE 67, EN 61 Seiten.

2026-11-01 ~18:45 MHD STUFE 2 fertig: Schalter MHD_POT (Potential, Jacobi, FX_MHD_JACOBI=20, FX_MHD_WAND 0/1), Diffs
  fluidx3d/mhd_*.diff (+ mhd_lbm.hpp.diff), setup_mhd_kanal.cpp (ersetzt setup_mhd_hartmann.cpp), Pruefung
  stellarator/mhd_kanal.py gegen eigenen 2D-b-Loeser: 12 Faelle bis Ha 30 < 1 %. Potentialkraft MUSS vor dem
  halbimpliziten Teil stehen. KORREKTUR Stufe 1: alte Werte (4,3 % Ha30) Auswertefehler ohne UPDATE_FIELDS, neu 0,5 %.
  k_p isolierend -> 1/Ha bestaetigt (daten/mhd_kp.json). Kapitel mhd_de/en.tex mit Begriffskasten.
  Vorwaermer-Prinzip (Skizze vorwaermer_prinzip.py) in Bericht DE/EN. Offen: Mehrgitter fuer reale Ha (~600+),
  endlich leitende Wand c, B(x) aus Spulen. Commit lokal, Push wartet auf OK.

2026-11-01 ~18:55 ALPHA AUSGEWERTET: stellarator/alpha_auswertung.py (auswerten | verlustbahnen [.venv-opt] | video).
  1000 Alphas, 16,6 +-1,2 % verloren (95 % gefangen, Median 25 ms), Energie 11,6 % = 71 MW (Stix-Gewichtung),
  Wandtreffer gebuendelt oben, max ~2,4 MW/m2 auf 16x8 Feldern. daten/alpha_verluste.json, Bilder alpha_verluste(_en),
  alpha_bahnen_standbild(_en), Video docs/filme/alpha_bahnen.mp4. Kapitel alpha_de/en.tex. README-Abschnitt.
  Naechstes: Form allein (booz_xform fehlt in .venv-opt) gegen Spulen; Spulen mit Alpha-Ziel; Stoesse.
  README ohne Rechnerangaben (FREECAD_APPIMAGE). Gepusht bis 730f5bf; Alpha-Teil lokal.

## 2026-11-01 abends: Alpha-Ursache getrennt (vorher/nachher)
- Lauf „Form allein“ (stellarator/alpha_form.py, Boozer über booz_xform): 0,3 % Verlust gegen 16,6 % im Spulenfeld →
  ~98 % der Verluste von den Spulen. Erwartung vorher (< 1 %) im Ereignisprotokoll F-105 festgelegt, bestätigt (F-106).
- Bild docs/bilder/alpha_vergleich(_en).png, daten/alpha_vergleich.json; Bericht alpha_de/en.tex „Vorher und nachher“.
- Pausieren: ~/bin/rechnung pause | weiter | (ohne Argument: Zustand). alpha_form.py kann mit --weiter fortsetzen.
- Nächster Schritt: Spulen mit Alpha-Ziel nachoptimieren, dann gleichen Vergleich wiederholen („nachher“).
- Wunsch des Nutzers: Video des Plasmastroms – für 2026-11-02 vereinbart; zuerst klären, was es zeigen soll (Feldlinien, Teilchenbewegung oder elektrischer Strom).
- fef7895 (vorher/nachher) hochgeladen.

## 2026-11-02 Festigkeit gekoppelt (Stand 13:45)
- DOE `sim/kopplung/doe1` läuft (200 Punkte, ~2,5 min/Punkt, Neustart überspringt fertige; Fehler in punkte/NNNN/fehler.txt).
- Nach 17 Punkten 3 zulässig (8, 14, 17). Kapitel festigkeit_de/en.tex als Zwischenstand, nach DOE aktualisieren
  (`.venv/bin/python -m stellarator.festigkeit_bilder` erneuert Bilder).
- Nächste: Ersatzmodell, leichtester zulässiger Entwurf, Nachrechnung feines Netz + elastischer Stützzylinder, Alpha, 3D-Modell FreeCAD.
- Nicht committet: kopplung.py, kraft_analyse.py, festigkeit_bilder.py, hexmodell.py (LAGER_ORT), stufe2_spulen.py, Recherche, Kapitel, Videodateien.

## 2026-11-02 abends: Auswertung doe1 auf morgen verschoben (Nutzerwunsch)
- doe1 endet von selbst nach Punkt 199 (kein Neustart nötig). Zulässig bisher: 8, 14, 17, 61, 63, 93, 136, 157, 169.
- Ziel geändert: robustester statt leichtester Entwurf (Gewicht egal, "Gebäude"); Rangliste nach kleinster Reserve.
- Morgen: Auswertung + Ersatzmodell, Nachrechnung feines Netz (61, 169, 93, 8), Idee Nutzer: Bereiche gezielt schwächen
  für gleichmäßigere Lastverteilung (F-131), dann 3D-Modell. Kapitel/README/Bilder auf Endstand bringen.
- Nutzerwunsch für morgen: 3D-Modell des besten Entwurfs KOMPLETT in PicoGK bauen (Plasma, Package-Schichten,
  Spulen mit Wickelpaket/Gehäuse, Verbinder, Lager/Stützzylinder) – Voxel, Boolesche Vereinigung, STL; zusätzlich zu/statt FreeCAD vergleichen.
- Nutzerwunsch für morgen: genau erklären, WELCHER Stahl (316LN = X2CrNiMoN17-13-3, 1.4429) mit Kennwerten bei 20 °C und 4 K,
  Herleitung der 500-MPa-Grenze; Tabelle des Nutzers: https://www.schweizer-fn.de/festigkeit/festigkeitswerte/stahl/stahl_start.php
  (Raumtemperaturwerte dort mit 4-K-Werten vergleichen). "p99 Stahl" erklären und zusätzlich Maximalwert/Spannungskategorien zeigen;
  im Bericht p99 durch verständlichen Begriff ersetzen.
- Prüfen: kopplung.py, kraft_analyse.py, festigkeit_bilder.py, festigkeit_de.tex wurden außerhalb dieser Sitzung geändert (git diff ansehen).

## 2026-11-03 Auswertung doe1, Ersatzmodell-Vorschläge, PicoGK-3D, Variantenbericht (Claude)
- Ergebnis: 7 zulässig (bereinigt): 0061 0169 0093 0008 0014 0017 0157. **Empfohlen 0169** (24 Spulen, 13 Verbinder/Paar,
  28 kt; σ99 308 → 319 MPa im feinen Netz, Robustheit 0,29). Ersatzmodell-Vorschläge ersatz1: V0/V1/V3 zulässig, V2 nicht;
  V3 im Standardnetz 0,35, im feinen Netz 272 → 394 MPa (0,21) → 0169 bleibt.
- Werkstoff 1.4429/316LN geklärt (stahl_bild.py), p99 → σ99, Spannungskategorien (doe_auswertung kategorien).
- PicoGK-Befund: Verbinder von 0169 durchdringen sich teilweise (FE zählt 13 % doppelt). Vermutung: deshalb netzstabil.
- Skripte: stellarator/doe_auswertung.py (tabelle|ersatz|vorschlag|kategorien|bilder), picogk_modell.py (liste1|katalog|bilder),
  variantenbericht.py (gen/*.tex) → bericht/variantenbericht/ (DE variantenbericht.tex, EN variant_report_en.tex).
- Liste 1 (18 PicoGK-Modelle) fertig. Kühlsegment- und Torus-Schnitt-Rechnungen nach /home/cae/cae_projekte/fusion_sim
  verschoben (Symlinks in sim/). LÄUFT LOSGELÖST: Katalog (Liste 2, ~187 Modelle à 2 min ≈ 6 h,
  Ablage /home/cae/cae_projekte/fusion_katalog3d, Log sim/kopplung/katalog3d_lauf.log, Ende = FERTIG_KATALOG).
  Danach (Hermes oder Claude): `.venv/bin/python -m stellarator.variantenbericht` und in bericht/variantenbericht
  `latexmk -pdf variantenbericht.tex variant_report_en.tex` (Katalogkarten erscheinen dann vollständig). Speicher beobachten.
- Nächste Schritte: 0169 mit überschneidungsfreien Verbindern vs. durchgehender Platte (Vermutung prüfen); weiche
  Verbinderenden (Nutzer-Idee örtlich); Abkühlspannung + Eigengewicht.
- Nicht committet (Freigabe des Nutzers abwarten): alles von heute.

- 2026-11-03: Plan für offene Punkte in docs/plan_offene_punkte.md (STL → STEP auf Wunsch herausgenommen). Nutzer wünscht Variantenvideo (Blender, wilde zuerst, am Schluss die zulässigen).

## Übergabe 2026-11-03 (Claude Code, Kontext läuft aus)
- Variantenfilm FERTIG (docs/filme/varianten.mp4, F-156). Die 2040 Einzelbilder (zweite Platte) erst nach Freigabe löschen.
- Punkt 1 erledigt (F-153): getrennt 387/392, platte 336/493, standard 308/319 MPa. Nächster Schritt: Review-Paket
  docs/review_festigkeit_entwurf.md als fertige Fassung DE/EN mit Bildern (PDF).
- Temp-Ordner sim/_temp_2026-11-03/ (verworfene Bilder, alte PicoGK-voll-Netze): Nutzer fragen, ob löschen.
- Buch: Kapitel 14a fertig bis auf FRAGEN 37 und Lage des Kapitels.

## Übergabe 2026-11-03 abends (Claude Code) — so kann PI/Hermes übernehmen
Stand der Aufträge, der Reihe nach. Ereignisprotokoll (Buch) F-163 bis F-168 enthält Erwartungen und Ergebnisse.

**Laufend (losgelöst, überlebt Sitzungsende):**
1. Video, Rechenszenen: Blender rendert Bilder 240–719 (`sim/video_varianten/lauf.sh`, Fall M_F), ~53 s/Bild,
   Stand 17:45 Bild 429. Danach startet `sim/video_varianten/kette_vorspann.sh` selbst die Bilder 120–276 neu.
   Fertig, wenn in `sim/video_varianten/lauf.log` „FERTIG Vorspann neu“ steht. Bilder:
   /mnt/chaostotal/KI_Werkstatt/cae_projekte/fusion_video_varianten/bilder (2520 Stück, 00000–02519).
   Prüfen: `ls <bilder> | wc -l` muss 2520 sein; `pgrep -af "blender -b"` leer.
   Dann: Probebilder 300, 450, 600 ansehen (Feldlinien sichtbar? Farbskala dunkelblau→rot?), danach
   `.venv/bin/python -m stellarator.varianten_video_schnitt` (→ docs/filme/varianten.mp4, 84 s). Dem Nutzer zeigen,
   ERST nach Freigabe committen. Einzelbilder NICHT löschen (Nutzer: „die anderen noch nicht“).
   Pausieren: `~/bin/rechnung pause` / `~/bin/rechnung weiter`.

**Abgeschlossen, noch nicht committet:** stellarator/varianten_video_rechnung.py, varianten_video_blender.py,
varianten_video_daten.py, varianten_video_schnitt.py, docs/filme/varianten.md, README (84 s),
stellarator/constellaration_bewertung.py, constellaration_bruecke.py, qi_vergleich_bild.py, kopplung.py
(plasma.json-Schalter `plasma_laden`, Parameter R1/abstand_ss), docs/bilder/qa_qi_vergleich.png, .gitignore.

**ConStellaration-Brücke (Option 1), Stand:**
- Umgebung `.venv-constellaration` (constellaration 0.2.6). Ränder: 3 zulässige Einreichungen der Rangliste
  (`sim/constellaration/qi/<name>/`, Nachrechnung trifft Rangliste exakt). Rohdaten auf zweiter Platte
  /mnt/chaostotal/KI_Werkstatt/cae_projekte/constellaration/.
- Ergebnis: Unsere Spulenoptimierung (invers/stufe2_spulen.py) findet für QI keine brauchbaren Spulen
  (Bn 0,02–0,19 statt ≤ 3e-3, Spulen 0,4–0,9 m am Plasma statt 1,99 m, Krümmung über Grenze). Abstand und
  Fourier-Ordnung als Ursache geprüft und ausgeschlossen (F-166, F-168). Vermutung: Strafgewichte gegen Feldziel.
- Nächster Schritt (mit Nutzer abstimmen): Proximas Datensatz „CoilStellaration“ (HF proxima-fusion/coilstellaration,
  MIT) laden, Spulensätze für QI ansehen und gegen unsere Kette vergleichen. Option 3 (ernsthaft mitmachen) offen.

**Am Sitzungsende fragen:** Temp-Ordner sim/_temp_2026-11-03b/ (alte Vorspannbilder, QI-Fehllauf) löschen?
sim/invers/qi_* (Prüfläufe) sind eigene Zwischenstände, dürfen nach Bericht weg.
- 18:15 Nachtrag: Proximas Spulensatz (CoilStellaration DnFiaMhotvUCEFyC7wg9opq, 30 Spulen, nfp 3) eingelesen,
  Kontrolle Feldfehler 8,17e-4 = Proxima 8,2e-4 (F-171). Skript stellarator/proxima_spulen.py (vmec | spulen).
  Läuft: Tragwerk/Package `kopplung punkt --studie qi_proxima --nr 0` (losgelöst), fertig wenn in
  sim/constellaration/bruecke_lauf.log „ENDE qi_proxima 0“ steht; Ergebnis sim/kopplung/qi_proxima/punkte/0000/
  (ergebnis.json oder Fehler im Log). Danach Vergleich mit Erwartung F-171 ins Ereignisprotokoll.
- 18:30 Nachtrag: Proxima-Spulen in unserer Kette erledigt (F-172 bis F-175). Satz 1 (DnFia…): Netz scheitert
  (Biegeradius 0,40 m < Gehäusetiefe 1,29 m). In 8058 Sätzen keiner mit Bn < 3e-3 und Biegeradius ≥ 0,7 a.
  Satz 2 (DRb36s…, Ordner sim/kopplung/qi_proxima_b36): mit dünnem Gehäuse Netz ok, aber σ99 1358 MPa, u 650 mm.
  Gegenprobe 0169 dünn (sim/kopplung/gegenprobe_0169_duenn): 426 MPa, alles ok, 3648 t Stahl (Netzprüfung offen!).
  Bild docs/bilder/qa_qi_proxima_spulen.png. Nichts läuft mehr außer dem Video. Noch nicht committet: proxima_spulen.py,
  qi_vergleich_bild.py (b36), Bild. Offen mit Nutzer: Lager/Verbinder für QI nachoptimieren? Gespräch mit Proxima?
- 18:50 Nachtrag (Nutzer: „erst 1 dann 2“): Läuft `sim/constellaration/feinlauf.sh` (losgelöst): Hex-Netz mit
  krümmungsabhängiger Abtastung (cad.neu_abtasten_kruemmung, Option abtastung=kruemmung), Punkte
  qi_proxima_b36/0001 und qi_proxima/0001. Fertig bei „FERTIG feinlauf“ in sim/constellaration/bruecke_lauf.log.
  Vergleich mit Erwartung F-177 ins Ereignisprotokoll. DANACH Schritt 2: Voxel-Gehäuse (PicoGK) aus den echten
  Spulenbahnen von Satz 2 → Tetraedernetz (gmsh) → Elmer; Erwartung vorher festlegen, Speicher beachten.
- 18:45 Schritt 1 FERTIG (F-179): Satz 2 fein 2202 MPa (grob 1358), Satz 1 fein 5370 umgestülpte Elemente.
  Schritt 2 (Voxel) PLAN: (a) Python: echte Spulenbahn fein (≥ 400 Punkte, ≤ 3° je Segment), je Segment konvexe Hülle
  zweier Rechtecke (WP bzw. Gehäuse außen) → PicoGK (Vorlage picogk/StellaratorModell) vereinigt → keine Umstülpung möglich.
  (b) Voxel direkt als Hex-Elemente nach Elmer (Vorbild stellarator/gradient_waerme.py, 808), 0,1–0,15 m Voxel,
  Lorentzlast im WP über Tangente der nächsten Bahnstelle (UDF lorentz.f90 prüfen). (c) Gegenprobe zuerst an 0169:
  Voxel-Ergebnis gegen Hex-Ergebnis 308 MPa, erst dann Proxima-Satz 2 und 1. Speicher: Voxelzahl vorher abschätzen.
- Stand 18:45: Innenkontur-Läufe fertig (F-181). Nichts läuft außer dem Video. Um 23:30 stoppt der Timer
  hermes-abschalten-2330 alles (sim/abschalten_2330.sh, Log sim/abschalten.log). Offen mit Nutzer: Rest-Umstülpung
  Satz 2 (6–12 Elemente, Spulentyp 2) untersuchen oder QI-Tragwerk eigens auslegen; Voxel-FE zu groß für 32 GB.
  Video: wenn „FERTIG Vorspann neu“ im Log → Probebilder prüfen, Film schneiden, dem Nutzer zeigen.
- 19:10: Satz 2 jetzt rechenbar (F-183): 1098 MPa mit 0169-Wänden. Code: gehaeuse_netz.biegegrenze (stetig),
  Reparaturschleife in kopplung.struktur_netz. Nichts läuft außer Video; Timer 23:30 aktiv.
- Alter Film (68 s, abgenommen) gesichert: sim/video_varianten/varianten_68s_alt.mp4 — Nutzer: „den alten erst einmal nicht löschen“.
- 19:45 Film 84 s geschnitten (docs/filme/varianten.mp4), dem Nutzer gezeigt; Freigabe offen → erst dann README/varianten.md
  committen und pushen (lokal 8 Commits voraus). Alter Film: sim/video_varianten/varianten_68s_alt.mp4.
- 20:00 Variantenbericht-PDF unter 20 MB (B-029, F-185): Steckbriefe nur noch die 7 zulässigen, Mosaik als JPG →
  DE/EN je 16,9 MB. Alte Mosaik-PNGs liegen in sim/_temp_2026-11-03b/ (Sitzungsende fragen). Noch nicht committet.
- KORREKTUR 2026-11-04: Die Zeilen 19:45/20:00 sind überholt. Nutzer hat den Film 84 s freigegeben („der Film ist super“,
  lädt ihn am Wochenende selbst hoch). Film + Bericht sind committet und gepusht (b70c9a4), Repo = origin.
  Versehentlich mitgepusht: bericht/variantenbericht/variantenbericht.zip (nicht von Claude erstellt, Zwischen-PDF 20,97 MB);
  Antwort des Nutzers offen, ob aus dem Repo nehmen. Temp-Ordner sim/_temp_2026-11-03b/: Antwort ebenfalls offen.
  Timer hermes-abschalten-2330 ist abgelaufen. Nutzer 2026-11-04: weiter am QI-Feld, Arbeit auf Claude/Sonnet/Haiku/PI verteilen.
- 2026-11-04 QI-Tragwerk LÄUFT LOSGELÖST (überlebt Claude-Ende): `sim/qi_feld/kette.sh` (FE-Varianten, Stufe 2 wählt selbst den besten Stand)
  und `docs/recherche/qi_tragwerk/lauf.sh` (PI-Literatur). Fertig: „FERTIG qi_feld“ und „FERTIG PI-Abschluss“ in sim/qi_feld/kette.log.
  Ergebnisse: sim/qi_feld/tabelle.md, docs/recherche/qi_tragwerk/ergebnis.md, pi_zusammenfassung.md (ungeprüft). Neustart nach Abbruch: Skripte
  einfach erneut mit setsid nohup starten, Fertiges wird übersprungen. Erwartung: F-186. Danach Pflicht für den Übernehmenden: Tabelle gegen F-186
  vergleichen, BEFUNDE + Skill stellarator-constellaration + Ereignisprotokoll nachtragen. Neue Optionen: seitlich_min, lager_ort=vier.
- 2026-11-04 09:48 Zwischenstand QI (F-187): bester Stand Lauf 16 721 MPa, Grenze 500 nicht erreicht; u 306 mm hängt an EINER schlecht angebundenen Spule (3).
  „rc 0“ in kette.log ist falsch (Skriptfehler), maßgeblich ist ob ergebnis.json existiert bzw. journalctl (OOM bei 20 GB: 0169 dünn fein, Lauf 17).
  `sim/qi_feld/kette3.sh` wartet auf kette.sh und rechnet Stufe 3 mit 25 GB; Ende „FERTIG Stufe 3“. Offen danach: Verbinder nach Lücken statt nach Abstand setzen,
  durchgehende Struktur je Feldperiode testen (docs/recherche/qi_tragwerk/konzept_sonnet.md, Zitate ungeprüft), Kandidat DoUj68… (spulensaetze_scan.md).
- 2026-11-04 09:57 QI-Kette fertig (automatisch): Tabelle sim/qi_feld/tabelle.md, Log sim/qi_feld/kette.log. Noch nicht von Claude geprüft.
- 2026-11-04 10:05 QI-Stufe 3 fertig (automatisch), Tabelle sim/qi_feld/tabelle.md. Noch nicht von Claude geprüft.
- 2026-11-04 10:06 sim/qi_feld/kette4.sh läuft losgelöst (Kombination, F-188), Ende „FERTIG Stufe 4“. 0169 dünn widerlegt: 426→512→591 MPa.
- 2026-11-04 10:10 Kraft-Scan läuft losgelöst: stellarator/qi_kraft_scan.py -> docs/recherche/qi_tragwerk/kraft_scan.csv, Log sim/qi_feld/kraft_scan.log (Ende „FERTIG kraft_scan“, Neustart überspringt Fertiges). Erwartung F-189.
- 2026-11-04 10:13 Stand: Lauf 42 hält Stahl+Dehnung (325 MPa, 0,27 %), aber Abschirmung fällt durch (F-190). sim/qi_feld/kette5.sh wartet auf Stufe 4, trennt die Wände, Ende „FERTIG Stufe 5“. Kraft-Scan neu gestartet (Fehler behoben).
- 2026-11-04 10:12 QI-Stufe 4 fertig (automatisch), Tabelle sim/qi_feld/tabelle.md. Noch nicht von Claude geprüft.
- 2026-11-04 10:16 Kraft-Scan fertig (F-191): docs/recherche/qi_tragwerk/kraft_scan.csv, bester Satz D5WFs… (2,5 gegen 45,8). sim/qi_feld/kette6.sh läuft losgelöst, Ende „FERTIG Stufe 6“.
- 2026-11-04 10:22 QI-Stufe 5 fertig (automatisch), Tabelle sim/qi_feld/tabelle.md. Noch nicht von Claude geprüft.
- 2026-11-04 10:24 QI-Stufe 6 fertig (automatisch): kraftarme Sätze, Tabelle sim/qi_feld/tabelle.md, QI-Güte sim/constellaration/qi/proxima_spulen_{d5w,b36}/qi_guete.json. Noch nicht von Claude geprüft. Erwartung F-191.
- 2026-11-04 10:26 sim/qi_feld/kette7.sh läuft losgelöst, Ende „FERTIG Stufe 7“: Wandkombination Satz 2 + kraftarme Sätze mit guter QI-Güte D56VPJ7…, DRDP96E… (docs/recherche/qi_tragwerk/kraft_scan_qi.csv). Stufe 6 entfallen (Skriptfehler). Erwartung F-193.
- 2026-11-04 10:49 QI-Stufe 7 fertig (automatisch): sim/qi_feld/tabelle.md, QI-Güte sim/constellaration/qi/proxima_spulen_{d56,drd}/qi_guete.json. Noch nicht von Claude geprüft. Erwartung F-193.
- 2026-11-04 10:51 Stand (F-194): D56VPJ7… hält mit 0169-Wänden die ganze Mechanik (157 MN, 316 MPa, 0,17 %, 26 mm, QI wie Satz 2), Package fällt durch (Spule-Plasma 1,21 m, nötig ~1,75 m).
  Satz 2 Lauf 71: nur Dehnung 0,32 %. sim/qi_feld/kette8.sh läuft losgelöst (DP9Xr4m…, DYUDcSV7…, Netzprüfungen), Ende „FERTIG Stufe 8“. Auswahltabelle: docs/recherche/qi_tragwerk/kraft_scan_qi.csv.
- 2026-11-04 11:08 QI-Stufe 8 fertig (automatisch): sim/qi_feld/tabelle.md, QI-Güte sim/constellaration/qi/proxima_spulen_{dp9,dyu}/qi_guete.json. Noch nicht von Claude geprüft. Erwartung F-194.
- 2026-11-04 11:09 Stand (F-195): DP9Xr4m… verletzt nur noch Fluenz (340 MN, 459 MPa, 0,27 %, Freiraum 1,14 m, QI 0,0068). Netzunsicherheit bis ~30 % (Lauf 71 336→429). sim/qi_feld/kette9.sh läuft losgelöst, Ende „FERTIG Stufe 9“.
- 2026-11-04 11:22 QI-Stufe 9 fertig (automatisch): sim/qi_feld/tabelle.md, QI-Güte sim/constellaration/qi/proxima_spulen_{dp9,dyu}/qi_guete.json. Noch nicht von Claude geprüft. Erwartung F-195.
- 2026-11-04 11:23 Stufe 9 fertig und von Claude geprüft (F-196, B-030): DP9 Lauf 4 grob alle Grenzen, Netz ×1,25 (Lauf 14) Fluenz verletzt. Nichts läuft mehr. Keine weitere Stufe ohne Nutzerentscheidung.
  Nächste Schritte zur Wahl: Freiraum stationsunabhängig messen, Netzstudie mit festem Verbinderplan, Stützringe/Platten nach Stellaris modellieren. Offen vom Nutzer: variantenbericht.zip, Temp-Ordner, 500-MPa-Grenze. Änderungen nicht committet.
- 2026-11-04 12:21 Nutzer: Vorschlag ja, 500 MPa bleiben (Ideen sammeln: docs/recherche/qi_tragwerk/ideen_stahlgrenze.md, Sonnet), Commit ja. Zip aus Repo-Stand raus und gepusht, Commit 3d98f31 + spätere NUR lokal (Push nicht beauftragt).
  ACHTUNG (F-197): Freiraum in Stufen 5–9 misst nur die Mitte der Innenwand; Verbinderbreite hängt an den Stationen, also sind alle bisherigen Netzprüfungen vermischt, auch „0169 dünn widerlegt“.
  sim/qi_feld/kette10.sh läuft losgelöst (Hüllenmessung, fester Plan), Ende „FERTIG Stufe 10“, Erwartung F-197.
- 2026-11-04 12:39 Submodell (Nutzeridee, F-198): stellarator/submodell.py, Kontrolle F=1 trifft Gesamtmodell (392,85 gegen 392,86 MPa). sim/qi_feld/kette11.sh wartet auf Stufe 10 und rechnet die Verfeinerungsreihe, Ende „FERTIG Stufe 11“, Tabelle sim/submodell/tabelle.md.
- 2026-11-04 12:42 QI-Stufe 10 fertig (automatisch): sim/qi_feld/tabelle.md. Noch nicht von Claude geprüft. Erwartung F-197.
- 2026-11-04 12:43 Stufe 10 geprüft (F-199): 0169 normal verfehlt mit Hüllenmessung die Fluenz (3,8e18), 0169 dünn hält (448 MPa, 1,28 m). „0169 dünn widerlegt“ zurückgenommen. Variantenbericht (öffentlich) nutzt die alte Messung: Nutzer entscheidet. Stufe 11 läuft.
- 2026-11-04 12:57 Stufe 11 fertig (automatisch): sim/submodell/tabelle.md. Noch nicht von Claude geprüft. Erwartung F-198.
- 2026-11-04 12:58 Stufe 11 geprüft (F-200, Befund 10). Tabelle sim/submodell/tabelle.md. Temperatur: `schrumpf_stahl/_wp/_verguss` in kopplung.werkstoffe, wirkt im Gesamt- und Submodell; Werte fehlen, PI läuft: docs/recherche/schrumpf/lauf.sh, Ergebnis ergebnis.md (gegenlesen!). Danach: Erwartung ins Protokoll, Gesamt + Submodell für 0169 und DP9 rechnen.
- 2026-11-04 13:00 Nutzer: 500 MPa nur angenommen, nicht belegt (F-201). Nicht ändern, aber als Annahme behandeln.
- 2026-11-04 13:10 sim/qi_feld/kette12.sh läuft losgelöst (Abkühlen, Spanne A/B/C als Annahme, F-202), Ende „FERTIG Stufe 12“.
- 2026-11-04 13:14 Rangfolge Nutzer (F-203): Plasma zuerst, Kollision und Spannung schließen nur Unrealistisches aus. sim/qi_feld/kette13.sh wartet auf Stufe 12, rechnet dann DjLe3eL6, DYU, DSD. Ende „FERTIG Stufe 13“.
- 2026-11-04 13:15 Nutzer: Token sparen, Vorschlag Sonnet als Standard, Opus gezielt (F-204, Entscheidung offen). B-031 eingetragen.
- 2026-11-04 13:21 Stufe 12 (Abkühlen) fertig (automatisch). Erwartung F-202. Noch nicht von Claude geprüft.
- 2026-11-04 13:22 Stufe 12 von Claude geprüft: B-032, F-205. Offen: Hauptspannungen und Haftung Wickelpaket. Stufe 13 läuft.
- 2026-11-04 13:35 Nutzer hat auf Sonnet umgestellt (F-206). Sonnet führt; Opus-Unteragent (model=opus) für Deutung Stufe 13 und Hauptspannungsprüfung; Haiku mechanisch; PI Suche. Stufe 13 läuft.
- 2026-11-04 13:36 Stufe 13 (Plasma zuerst: DjLe3eL6, DYU, DSD) fertig (automatisch). Erwartung F-203. Noch nicht von Claude geprüft.
- 2026-11-04 13:36 Stufe 13 fertig, B-033/F-207. Submodelle QI-Sätze scheitern (negative Elemente), Auslenkung 200–290 mm ungeklärt: Opus-Agent beauftragt (Ergebnisdatei docs/recherche/qi_tragwerk/opus_fehlersuche.md).
- 2026-11-04 13:45 Opus-Fehlersuche fertig (B-034, F-208): Lücken ohne Verbinder erklären die Auslenkung; Submodell-Reparatur in kopplung.py/submodell.py (ungeprüft committet: nein). Nächster Hebel: Verbinder nach Lücken setzen.
- 2026-11-04 13:50 Opus-Agent baut verb_modus=luecken (kopplung/hexmodell) und rechnet qi_proxima_dje 2; Bericht docs/recherche/qi_tragwerk/opus_luecken.md. Erwartung F-208. Nicht committet.
- 2026-11-04 14:04 Lückenmodus (B-035, F-209): dje 241→42,5 mm, 620→405 MPa. sim/qi_feld/kette14.sh läuft losgelöst (dje 3, dyu 21, dsd 1 + Submodelle dje 2/3, dyu 21, dsd 1), Ende „FERTIG Stufe 14“. Code (hexmodell/kopplung/submodell) noch nicht committet.
- 2026-11-04 14:15 Plasma-Einflüsse (B-036, F-211): im Gesamtdatensatz kehrt sich das Vorzeichen beim Aspektverhältnis um; Bericht DE/EN neuer Abschnitt qi_einfluss, PDFs gebaut. Stufe 14 läuft weiter. Nicht committet.
- 2026-11-04 14:15 Stufe 14 (Plasma zuerst: DjLe3eL6, DYU, DSD) fertig (automatisch). Erwartung F-209. Noch nicht von Claude geprüft.
- 2026-11-04 14:22 Nachtrag B-036/F-213: gemeinsames Modell R² 0,90, Spiegelverhältnisse wichtigste; Bericht DE/EN ergänzt, PDFs gebaut. Nicht committet.
- 2026-11-04 15:14 Stufe 14 abgeholt (B-037, F-214): dje/dyu Tragwerk ok unter Annahme, Fluenz/Package/Kernheizung verletzt (Hülle zu eng). Submodell dje Punkt 3 fehlt.
- 2026-11-04 15:18 Nutzer: beides (F-215). abstand_vorab.md; sim/qi_feld/kette15.sh läuft losgelöst (dyug x1,45, dsdg x1,12, dpr, dgh), Ende „FERTIG Stufe 15“. proxima_spulen.py: Umgebungsvariable GROESSE neu.
- 2026-11-04 15:21 Nutzer-Ziel: einen Satz ins Ziel bringen (Absprungbasis) + Plasma-Wand-Abstand/Definition (F-216). PI-Suche docs/recherche/plasma_wand/lauf.sh läuft losgelöst, Ende „FERTIG Literatur“. Danach von Claude inhaltlich prüfen.
- 2026-11-04 15:26 Nutzer-Idee Abstandsbilanz: Kachel + Formtoleranz + Regelgüte (F-217). Siebtes PI-Thema (Toleranzen, Randschichtbreite) nach Ende des Laufs nachschieben; dann Abstandsbilanz als Parameterliste in kopplung.py (Spalte, Package) belegen.
- 2026-11-04 15:28 Skill plasma-wand-abstand angelegt (F-218). Nach PI-Suche Zahlen eintragen.
- 2026-11-04 15:56 Stufe 15 (Abstand: dyug, dsdg, dpr, dgh) fertig (automatisch). Erwartung F-215. Noch nicht von Claude geprüft.
- 2026-11-04 15:58 Stufe 15 abgeholt (B-038, F-219): Platz gelöst, Festigkeit offen. sim/qi_feld/kette16.sh läuft losgelöst (dpr x1,3/x1,6, dgh x1,3, dyug Lager/Verbinder), Ende „FERTIG Stufe 16“.
- 2026-11-04 15:58 PI-Abstandssuche geprüft (B-039, F-220, pruefung_claude.md); drei Zusatzthemen laufen (docs/recherche/plasma_wand/lauf.sh). Stufe 16 läuft.
- 2026-11-04 16:08 Stufe 16 (Wände dicker) fertig (automatisch). Erwartung F-219. Noch nicht von Claude geprüft.
- 2026-11-04 16:39 Nutzer-Idee zwei Spulenringe (F-221), nur notiert, Test wartet auf Freigabe. Stufe 16 läuft.
- 2026-11-04 16:55 ERSTER SATZ IM ZIEL (B-040, F-222): DPrcxq66 (sim/kopplung/qi_proxima_dpr Punkte 0001 und 0002) erfüllt im Gesamtmodell alle Grenzen. Stufe 17 (kette17.sh) sichert ab: Netz x1,5, Abkühlen A/B/C, Submodell. Bericht DE/EN Abschnitt „Ein Satz im Ziel“ neu. Zwei-Ringe-Test (F-221) läuft als Opus-Agent, Ergebnis docs/recherche/qi_tragwerk/zwei_ringe.md.
- 2026-11-04 17:18 Stufe 17 (DPr Absicherung) fertig (automatisch). Erwartung F-222. Noch nicht von Claude geprüft.
- 2026-11-04 17:30 Stufe 17 + Zwei-Ringe ausgewertet (B-041, F-223): DPrcxq66 im feinen Netz NICHT im Ziel (580 MPa, Hülle 1,19 m), Scan-Kraft f unzuverlässig (Kette-MN nehmen), zwei Ringe senken Kraft nicht. Bericht-Abschnitt ziel_de/en muss eingeschränkt werden (erledigt). Offen: Ursache der netzabhängigen Hülle (Opus-Agent).
- 2026-11-04 17:50 Opus-Agent klärt Netzabhängigkeit (B-042, F-224): Ursache fester Plan + Zufall des Entflechtens; huelle_min_m neu in kopplung.py (uncommittet). Stufe 18 (kette18.sh) sichert DPr mit freien Verbindern ab. Bericht ziel_de/en noch einmal berichtigen.
- 2026-11-04 18:07 Stufe 18 (DPr freie Verbinder) fertig (automatisch). Erwartung F-224. Noch nicht von Claude geprüft.
- 2026-11-04 18:00 NUTZERENTSCHEIDUNG (F-225, B-043): p99 der heißesten Spule entscheidet (ohne Randzone), Gesamtwert nur Zusatz. Folge: Wände je Spule anpassen (Opus-Agent), Bewertung in ergebnis.json umstellen. Stufe 18 läuft noch (kette18.sh).
- 2026-11-04 18:25 Stufe 18 fertig (B-044, F-226). PI-Abstandssuche fertig (9 Themen), noch von Claude zu prüfen. Opus-Agent arbeitet an Maßstab heißeste Spule + Wände je Spule (Bericht opus_heissespule.md).
- 2026-11-04 18:35 Nutzer: 500 MPa nur Richtwert, keine feste Grenze (F-227, B-045). Ziel-Aussagen als „hält den Richtwert“ lesen. Bericht ziel_de/en bei nächster Überarbeitung anpassen.
- 2026-11-04 18:33 Opus-Agent F-225: Bewertung auf heißeste Spule ohne Randzone umgestellt (kopplung.py, Tabelle, heisse_spule.py), Option wand_adapt/wand_von neu. Punkt 12 (DPr ×1,6, wand_adapt): 585 → 446 MPa nach 1 Runde (Spulen 4/18 ×1,3), Hülle 1,51 m, Submodell Spule 11 461 MPa. Bericht docs/recherche/qi_tragwerk/opus_heissespule.md. Nicht committet; BEFUNDE noch eintragen.
- 2026-11-04 18:55 Opus-Agent fertig (B-046, F-228): DPr x1,6 mit Wänden je Spule (Punkt 12) heißeste Spule 446 MPa. Stufe 19 (kette19.sh) sichert ab: Netz x2, x1,5, Abkühlen B mit wand_von=qi_proxima_dpr/0012, Ende „FERTIG Stufe 19“. Änderungen in kopplung/submodell/qi_feld_auswertung/heisse_spule.py committen.
- 2026-11-04 18:36 Nutzer: alle vier offenen Punkte (F-229): Stufe 19 läuft (Netz, Abkühlen), kette20.sh wartet darauf (Wandziel 500/480, Submodell Spule 11 F1/F2). Achtung: Uhrzeiten der ERINNERUNGEN-Zeilen ab 17:30 teils geschätzt.
- 2026-11-04 18:37 PI-Themen 7 bis 9 geprüft (F-230, B-039-Nachtrag).
- 2026-11-04 18:38 Parameterkorridor optimales Plasma (B-047, F-231/F-232), Skript qi_korridor.py. Bericht-Nachtrag DE/EN. Stufe 19/20 laufen noch.
- 2026-11-04 18:41 Stufe 19 (DPr Wände je Spule) fertig (automatisch). Erwartung F-228. Noch nicht von Claude geprüft.
- 2026-11-04 18:51 Formkoeffizienten -> QI (B-048, F-233/F-234): R² 0,91; Kasten auf Koeffizienten schwach (2,3 %). Nächster Schritt 3: Entwurf im Modell + VMEC++-Nachprüfung (Opus), noch nicht gestartet. Nutzer: immer an Bericht und Ereignisprotokoll denken. Stufe 19/20 laufen.
- 2026-11-04 18:52 Stufe 20 (Überdimensionierung, Submodell-Streuung) fertig (automatisch). Erwartung F-229. Noch nicht von Claude geprüft.
- 2026-11-04 18:53 Stufe 19 und 20 ausgewertet (B-049, F-235): DPr Punkt 12 vorläufig Absprungbasis nach Richtwerten (heißeste Spule 432 bis 531 MPa). Alle vier offenen Punkte erledigt. Offen: Entwurf neuer Formen (Schritt 3), Bericht ziel_de/en auf Endstand gebracht.
- 2026-11-04 19:01 Nutzerfrage Wechselwirkung der Parameter (F-236): Plan A Modell-Wechselwirkung, B VMEC++-Gegenprobe, C Kennzahlen-Rückkopplung. Wartet auf Freigabe.
- 2026-11-04 19:14 Nutzer: Upload nur mit Eigenem (F-238). Plasma: noch nichts Eigenes. Opus-Agent rechnet Surrogat-Kandidaten mit VMEC++ gegen (Bericht docs/recherche/qi_tragwerk/opus_gegenrechnung.md). Nichts hochladen ohne ausdrückliche Freigabe.
- 2026-11-04 19:57 Gegenrechnung fertig (B-050, F-239): eine eigene Form (QI 0,0000472), aber offizielle Wertung 0 für alle Formen. Nicht hochladen. Offen: Formen suchen, die die Nebenbedingungen (Spiegelverhältnis, iota) erfüllen, und Bericht-Abschnitt Gegenrechnung DE/EN.
- 2026-11-04 20:25 Paarvergleich Plasma-Wege (F-240): Reihenfolge A Datensatz filtern (138 Formen ohne QI-Grenze) -> B kleine VMEC++-Schritte -> D direkte Optimierung. Noch nicht gerechnet; wartet auf Freigabe des Nutzers.
- 2026-11-04 20:40 Weg A fertig, Weg B läuft (B-051, F-241, Opus-Agent): echte Schwellen weichen ab (keine Aufgabe mit QI ≤ 0,001; Aufgabe 3 verlangt QI ≤ 0,00034 mit Toleranz). 138 bestätigt (iota mit Vorzeichen; Paket nimmt Betrag: 145). Bestes QI 0,00178. Lokale VMEC++-Suche von 5 Startformen losgelöst gestartet (sim/qi_flaeche/suche_lokal/lauf.sh, Stand in zwischenstand.txt und s<k>/zwischenstand.txt, pausierbar mit ~/bin/rechnung pause/weiter, Neustart setzt fort). Dauer etwa 3 bis 4 h (160 bis 210 s je Rechnung bei 4 parallel, Speicher 2,8 GB je Lauf). Danach: stellarator.qi_filter_suche auswertung, Vergleich mit Erwartung F-241, Bericht opus_filter_suche.md Abschnitt Ergebnis. Nichts committet.
- 2026-11-04 20:55 Auf Wunsch des Nutzers beendet (Suchlaeufe gestoppt, keine Pause). Weiter morgen: cd sim/qi_flaeche/suche_lokal && setsid nohup bash lauf.sh > lauf.log 2>&1 & (setzt fort, fertige Auswertungen bleiben; ggf. halb fertige Einzelrechnungen werden neu gerechnet). Danach auswerten und falsche QI-Schwelle 0,001 in Paarvergleich, B-047, B-050 korrigieren (echt 0,00032 bzw. 0,0001).
- 2026-11-05 07:41 QI-Karte fertig (B-052, F-243/F-244, Opus-Agent): stellarator/qi_karte.py, Ergebnisse sim/qi_flaeche/karte/ (4 Formen, 14 Flächen), Bericht docs/recherche/qi_tragwerk/qi_karte.md mit Bildern in qi_karte/. Randwert = offizieller QI exakt; Fehler wächst bei 3 von 4 Formen nach außen, DjLe3eL6 innen (s≈0,7) 1,6× schlechter als am Rand; keine Aufsummierung. Neustart: sim/qi_flaeche/karte/lauf.sh überspringt Fertiges. Suche suche_lokal unberührt. Nichts committet.
- 2026-11-05 08:10 QI-Videos fertig (F-246, Sonnet-Agent): 10 mp4 + begleittext.md in sim/qi_flaeche/karte/video/, Skript stellarator/qi_video.py (neu), frames/ 468 MB bleibt bis Freigabe. Nichts committet.
- 2026-11-05 08:13 Opus-Agent QI<->Spulen (F-245): Werkzeug stellarator/qi_spulen.py (VMEC++ free-boundary mit Proxima-Spulen DjLe3eL6, Feldtabelle je Spulengruppe selbst gerechnet, sim/qi_spulen/). Fest-Kontrolle trifft offiziellen QI exakt. Free-boundary konvergiert erst mit 48 statt 24 Toroidalpunkten (Spulenwelligkeit); Selbstkonvergenztest läuft (k_n3000/k_n12000). Teil B (Ströme) folgt: sim/qi_spulen/lauf.sh (losgelöst, 2 parallel, überspringt Fertiges). Suche suche_lokal unberührt. Nichts committet.
- 2026-11-05 09:09 UNBEAUFSICHTIGTE SERIE gestartet (token knapp): QI-Profil je Flaeche fuer 120 Datensatzformen (60 beste ohne QI-Grenze nach Aufgabe 3 + 60 beste QI). Skript stellarator/qi_profil_serie.py, Kette sim/qi_flaeche/profil_serie/lauf.sh (2 parallel, nice, setsid; Neustart: cd Projekt && setsid nohup nice -n 15 bash sim/qi_flaeche/profil_serie/lauf.sh > sim/qi_flaeche/profil_serie/lauf.log 2>&1 &). Ende = 'ALLE FERTIG' in zwischenstand.txt, Auswertung automatisch in docs/recherche/qi_tragwerk/qi_profil_serie.md. Zu klaeren danach: Ist der Rand meist die schlechteste Flaeche (bisher 3 von 4)? Erwartung: ja in mindestens 70 %. Dauer geschaetzt 4-6 h. Daneben laufen: Suche (sim/qi_flaeche/suche_lokal, Ende ca. 11-12 Uhr), Opus-Agent Spulen-QI.
- 2026-11-05 09:43 QI<->Spulen fertig (B-053, F-245/F-246, Opus-Agent): stellarator/qi_spulen.py (eins <fall> | modell2 | modell2_strom | modell2_lage | poincare | karte), stellarator/qi_3d.py <dje|do3|k3>; Ergebnisse sim/qi_spulen/, sim/qi_flaeche/karte3d/; Bericht docs/recherche/qi_tragwerk/qi_spulen.md + Ordner qi_spulen/ (interaktiv qi_3d_dje.html). Kern: Spulen kosten am Rand +24 % QI; S5-Strom stärkster Hebel (−5 % → −25 %); Stromverhältnisse ±5 % → −27 %; 5 mm Lage ≤ 2,7 %; Spulenfeld hat Inseln 4/9, 8/19 und stochastischen Rand (free-boundary Randwert daher nicht konvergent). Keine Rechnung läuft mehr von mir. Suche suche_lokal unberührt. Nichts committet, nichts hochgeladen.
- 2026-11-05 09:56 Opus-Agent prüft Nutzer-Hypothese QI <-> Verdrillung/großer Durchmesser (F-247 Erwartung eingetragen). Skript stellarator/qi_verdrillung.py (lokal | datensatz | r00 <form> <f> | skal <form> <f> | d8z3d | r00bilder). Kette LÄUFT LOSGELÖST: sim/qi_flaeche/verdrillung/lauf.sh (1 Rechnung gleichzeitig, Scope 6 GB, pausierbar ~/bin/rechnung, Neustart: cd Projekt/sim/qi_flaeche/verdrillung && setsid nohup bash lauf.sh > lauf.log 2>&1 &; Fertiges wird übersprungen). Reihenfolge: d8z 3D-Karte, R00-Reihe do3/dje (Faktoren 0,8 bis 1,5), alles ×2 (Prüfstein), Datensatzmaße (~40 min), Bild. Stand in zwischenstand.txt. Dauer gesamt etwa 1,5 bis 2 h. Bericht folgt: docs/recherche/qi_tragwerk/qi_verdrillung.md.
- 2026-11-05 10:52 Opus-Agent Wirkungskarte QI <-> Spulenposition (F-248 Erwartung eingetragen). Skript stellarator/qi_wirkung.py (rechnen | geometrie | auswertung | opt | bilder | html), Bilder stellarator/qi_wirkung_bilder.py. Kette LÄUFT LOSGELÖST: sim/qi_wirkung/lauf.sh (1 Scope 6 GB gleichzeitig, pausierbar ~/bin/rechnung, Neustart: cd Projekt && setsid nohup bash sim/qi_wirkung/lauf.sh > sim/qi_wirkung/lauf.log 2>&1 &; Fertiges wird übersprungen). 42 Fälle Weg (ii) je ~6 s, dann Geometrie, Auswertung, Optimierung Flecken; Dauer ~20 min. Prüfstein getroffen (basis 0,00055442, fest 0,00044754 = offiziell). Bericht folgt: docs/recherche/qi_tragwerk/qi_wirkungskarte.md. Suche, Serie, Verdrillung unberührt.
- 2026-11-05 11:05 Wirkungskarte fertig (B-054, F-248/F-249, Opus-Agent): stellarator/qi_wirkung.py + qi_wirkung_bilder.py, Ergebnisse sim/qi_wirkung/ (Ketten lauf.sh, lauf2.sh fertig), Gegenprobe Weg (i) sim/qi_spulen/faelle/w_flecken_opt.json (neu, eigener Name). Bericht docs/recherche/qi_tragwerk/qi_wirkungskarte.md + Ordner qi_wirkungskarte/ (interaktiv wirkungskarte_3d.html, plotly.min.js einmal daneben, 4,8 MB). Kern: Spulen wirken über Strom an den Muldenflanken, nicht über Nähe; hellste Flecken = Form; Trimmung ±5 % Flecken −38 %. Keine Rechnung von mir läuft mehr. Suche/Serie/Verdrillung unberührt. Nichts committet, nichts hochgeladen.
- 2026-11-05 11:15 Verdrillungs-Hypothese fertig (B-055, F-247/F-250, Opus-Agent): stellarator/qi_verdrillung.py, Ergebnisse sim/qi_flaeche/verdrillung/ (r00_*.json, skal_*.json, lokal.json, datensatz.json, datensatz_masse.npz Zwischenspeicher, datensatz_teilkorrelation.json, r00_tabelle.md), Bericht docs/recherche/qi_tragwerk/qi_verdrillung.md + Bilder qi_verdrillung/. Nebenbei: lokale 3D-QI-Karte für D8ZNt2 ergänzt (sim/qi_flaeche/karte3d/d8z.*). Kern: QI maßstabsfrei (×2/×1,7 gleich); nur R00 verändern verschlechtert QI in beiden Richtungen (Original optimal; DjLe3eL6 ×0,8 konvergiert nicht); Querschnittsdrehung je Periode ρ +0,42, Torsion ≈ 0, Krümmungsänderung −0,14. Nichts läuft mehr von dieser Prüfung. Nichts committet. Offen: Neuoptimierung bei großem A.
- 2026-11-05 11:25 Suche Schritt B fertig: 177 Formen gerechnet, keine zulaessig; bestes QI 0,000487, kleinste Verletzung f 0,0122. Tabelle docs/recherche/qi_tragwerk/opus_filter_suche_tabelle.md. Profil-Serie (120 Formen) laeuft weiter, Ende = ALLE FERTIG in sim/qi_flaeche/profil_serie/zwischenstand.txt.
- 2026-11-05 11:47 BERECHNUNGSMATRIX fuer PI angelegt (token knapp): bash start_berechnungsmatrix.sh (startet losgeloest; --status; --mit-pi). Matrix sim/berechnungsmatrix/matrix.tsv (Radius-Reihen, Profil-Serie fertigstellen, Suche auf 120 Versuche je Startform, Auswertungen), Auftrag fuer PI: sim/berechnungsmatrix/PI_AUFTRAG.md. NOCH NICHT GESTARTET (Profil-Serie laeuft noch; Matrix wartet auf sie in Stufe 2). Pausieren: ~/bin/rechnung pause/weiter.
- 2026-11-05 11:57 Absolute Pfade gespeichert: /home/cae/hermes/PFADE_FUSION.md (ausserhalb des Repos, mit lokalen Pfaden). Neustart: cd /home/cae/hermes/fusion && bash start_berechnungsmatrix.sh
- 2026-11-05 12:25 UEBERGABE (Token des Hauptmodells zu 99 % verbraucht): Opus-Agent erweitert die Berechnungsmatrix um vernuenftige + wilde Proben (stellarator/qi_experiment.py, sim/berechnungsmatrix/matrix.tsv, erzeuge_matrix.py). Nach seinem Ende: Matrix NICHT automatisch gestartet. Start nur auf Wunsch des Nutzers: cd /home/cae/hermes/fusion && bash start_berechnungsmatrix.sh. Profil-Serie laeuft weiter (sim/qi_flaeche/profil_serie). Lokal committet bis 96be7f2; danach neue Dateien (Matrix, Pfade-Datei ausserhalb Repo) NICHT committet, nichts gepusht seit 2322ec7. Offen: Entscheidung gezielte Suche (Weg 2), Motorrad-Bilder, Frame-Loeschung sim/qi_flaeche/karte/video/frames (nur nach Freigabe), kalibrierung_v1/v2 in sim/qi_spulen loeschbar (fragen). Pfade: /home/cae/hermes/PFADE_FUSION.md
- 2026-11-05 12:34 EXPERIMENTMATRIX angelegt (F-252, Opus-Agent; Nutzerwunsch vernuenftige + wilde Proben fuer Daten/Verstaendnis): Skript stellarator/qi_experiment.py (vorbereiten | form | strom | datensatz | liste | auswertung), Generator sim/berechnungsmatrix/erzeuge_matrix.py; matrix.tsv jetzt 513 Zeilen: Stufe 4 Vorbereitung (1), 5 Strom-Proben DjLe3eL6 Weg ii (240: 40 im geprueften Bereich +-5 %, 200 wild ausserhalb), 6 vernuenftige Formproben (112 = 4 Basisformen x 28), 7 wilde Formproben (64) abwechselnd mit 60 Datensatzproben + 16 Linearitaetsproben, 8 alle Auswertungen (AUSW_SUCHE/R00/PROFIL von Stufe 4 verschoben, neu AUSW_EXPERIMENT). Ergebnisse spaeter sim/qi_flaeche/experiment/{form,strom,datensatz}/*.json, alle_proben.csv, Bericht docs/recherche/qi_tragwerk/qi_experiment.md. Getestet im Testordner (EXP_AUS), Testdateien entfernt: Strom-Basis 0,00055442 und B-053-Optimum 0,00040751 reproduziert, Formprobe Do3Qy Spiegel-senken 0,1 sd QI 0,000165 (78 s), Kreuzung DjLe3eL6 QI 0,0207, Datensatzprobe QI = Datensatz auf 7e-7 (262 s CPU); Mini-Matrix (MATRIX_DATEI) laeuft, ueberspringt Fertiges. NICHT GESTARTET (Nutzer entscheidet). Experimentstufen ca. 3 bis 3,5 h bei 4 parallel. Nichts committet.
- 2026-11-05 13:15 Matrix-Fehler behoben: Stufe 2 wartete auf sich selbst (pgrep -f traf die eigene Kommandozeile). Profil-Serie war schon fertig (12:36); PROFIL_SERIE als fertig markiert, Muster in start_berechnungsmatrix.sh auf 'bash <skript>' geaendert. Stufe 3 (Suche, Budget 120) laeuft seit 13:15.
- 2026-11-05 13:26 Matrix grosszuegig erweitert (Nutzer erst 2026-11-06 ~17:00 wieder da): 850 Strom-, 432 Form-, 400 Datensatzproben; Dauer nach Stufe 3 etwa 10-13 h (Schaetzung). Auswertung am Ende; bei Zeitmangel von Hand: .venv-constellaration/bin/python -m stellarator.qi_experiment auswertung. Stand: bash start_berechnungsmatrix.sh --status. Nichts gepusht seit a5bfc4e.
- 2026-11-05 13:58 Auf Wunsch des Nutzers: start_berechnungsmatrix.sh ins Repo (.gitignore-Ausnahme), Videobilder sim/qi_flaeche/karte/video/frames (468 MB) geloescht (Videos mp4 bleiben, Bilder mit stellarator/qi_video.py neu erzeugbar), gepusht.
- 2026-11-06 19:04 Demonstrator fuer AI Tinkerers Munich (11.11.2026) fertig: Ordner demonstrator (ausserhalb Repo, offline index.html, 8 Seiten EN/DE/EN+DE), ZIP demonstrator.zip, Bau: demonstrator_src/build.py + docs.py (Quelle lokale Pfade nur dort). Texte: demo_ablauf(.md|_de_en.md), demo_bewerbung(_de_en).md, vorbereitung_checkliste.md. Stand der Zahlen: Matrix-Status 2026-11-06 18:55 (Stufe 7 lief noch). Nichts committet, Matrix unberuehrt.
- 2026-11-06 Befund B-056: Strom-Optimum B-053 nicht global (Zufallsprobe 0,000392 < 0,000408), Gegenprobe Weg i und Nebenbedingungen offen. Demonstrator fertig: /home/cae/hermes/demonstrator/ (ZIP daneben), Frage-und-Antwort-Uebung laeuft im Chat, Frage 1 offen.
- 2026-11-06 19:16 Demonstrator umgebaut zum Werkstatt-Browser (Ursprung E-Maschine -> Stellarator, Originalauszuege aus Protokollen; 9 Seiten); ZIP neu; Texte demo_*_de_en.md, Checkliste angepasst. Nichts committet, Matrix unberuehrt.

- 2026-11-06 20:50 Matrix komplett (Stufe 1–8 fertig). AUSW_EXPERIMENT war abgestürzt (Feld `fehler` in manchen Ergebnisdateien ein dict, `.replace` schlug fehl; Zeile 461 qi_experiment.py auf `str(...)` geändert), von Hand neu gelaufen, Marke gesetzt. Bericht: docs/recherche/qi_tragwerk/qi_experiment.md (Erwartungen 8 von 9 getroffen, verfehlt: wild rechenbar 13 % statt 20–50 %). Wichtigste Zahlen: Strom Weg ii linear nur bis ±5 % (R² LOO 0,966, bei ±50 % 0,225), beste Strom-Probe 0,000192 (±50 %, ungeprüft mit freier Grenze), keine zulässige Form (Aufgabe 2/3: 0). Nächster Schritt: Surrogat + Suche (Opus-Agent), Strom-Ausreißer mit Weg i prüfen.
