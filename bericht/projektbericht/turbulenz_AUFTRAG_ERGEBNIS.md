# Ergebnis Auftrag Kapitel Turbulenz (KI-generiert, Claude Sonnet, 2026-11-12 09:10)

## Dateien
- neu: bericht/projektbericht/turbulenz_de.tex, turbulenz_en.tex (Abschnitt 19, \label{sec:turbulenz})
- neu: bilder/gx_w7x_benchmark.png, gx_alle_formen.png, gx_paarvergleich_kriterien.png (Kopien; Bildtext deutsch, EN-Bildunterschrift nennt das)
- neu: sim/gx_pilot/gx_alle_formen.png
- geändert: stellarator/gx_vergleich.py (Option --alle), projektbericht.tex und project_report_en.tex (\input nach spulen_kette), beide PDFs gebaut ohne Fehler
- nicht committet, laufende Rechnungen nicht angefasst

## Spearman
`~/cae_projekte/gx/deps/venv/bin/python -m stellarator.gx_vergleich --alle`
-> `15 Formen, Spearman 0.5892857142857142 p 0.020794358483161635` (DfXvrph2 noch nicht in gx_werte.json; GX läuft). Ohne DK8s6qwo (14 Formen) 0,56, Quelle ERWARTUNG.md.

## Zahlenquellen
- GX-Werte, Fehler (Tabelle, auf 2 Stellen angezeigt): sim/gx_pilot/gx_werte.json; Ersatzmaß (2 Stellen): cae_projekte/gx/laeufe/<id>/ergebnis_vmec.json
- W7-X 5,95 ± 0,03 / 5,99 ± 0,05, Band 4,9-9,1, -15 %, ntheta 48 statt 128, 96x96 statt 64x192: BEFUNDE B-074, ERGEBNIS.md, ERWARTUNG.md
- DZrUR4dA 8,07 (fix aspect), Faktor 1,68 / 1,27 / 1,32, shat 1,31, 0,8 Umläufe, Zeiten 12-25 min: B-074
- Absturz 16:16, 6 von 11, bei t=25 verloren: runde2.log, ERINNERUNGEN.md; 3D 1,6-6,8 m falsch, 0,47 x 0,42 m, rho_i 3,2 mm, 10 keV, 5 T: ERGEBNIS.md
- Paarvergleich (alle 10 auf Front, beste je Kriterium, 0,64, 6 von 7, DZrUR4dA 0,44 Platz 7, QI-Rang 10): formen_vergleich.json, paarvergleich_kriterien.json, paarvergleich_kriterien.png
- Fläche s = 0,64 ~ 80 % Radius: eigene Rechnung sqrt(0,64), keine Quelldatei (Erklärung, ggf. streichen)

## Abweichung von ERWARTUNG.md
Dort: DNghq7U6 (6,97) liege über „einer“ Form mit Ersatz >= 1,6. Aus den Daten: über zwei (D799qKH8 6,36 und DmC2qkhi 6,94). Kapitel nennt zwei.

## Offen
- DfXvrph2: GX läuft; danach Spearman (16 Formen), Tabelle, Bild, Paarvergleich neu (--alle, formen_vergleich.py, paarvergleich_bild.py).
- Bilder deutsch beschriftet, keine EN-Fassungen.
- Gleiche Gewichte = Platzhalter, Nutzerurteil steht aus.
- Bild paarvergleich im Bericht klein; bei Bedarf Querformat.
