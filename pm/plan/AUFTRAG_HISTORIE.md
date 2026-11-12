# Auftrag an Sonnet: Vergangenheit rekonstruieren und Wissensnetz (2026-11-12, von Claude Opus)

KI-generiert. Ziel: Das Fusionsprojekt (seit 2026-10-22) bekommt nachträglich einen Netzplan mit Vergangenheit und ein Wissensnetz wie das Batterieprojekt.
Alles ist **Rekonstruktion** und wird so gekennzeichnet. Nichts erfinden: keine Erwartung, keine Freigabe, kein Datum ohne Fundstelle.

## Eingaben (nur lesen)
- `BEFUNDE.md` (B-001 … B-076, Datum im Titel), `ERINNERUNGEN.md` (Datumsabschnitte), `git log --date=short --format="%ad %h %s"`
- `docs/projekt/01_lastenheft.md` (REQ-F01 … F13, REQ-D01 … D10), `docs/plan_offene_punkte.md`, `README.md` (Ergebnisabschnitte)
- Vorlage Wissensnetz: `~/hermes/batterie/pm/plan/wissensnetz.py`, `wissensnetz_ansicht.py`, `wissensnetz_obsidian.py` (nur lesen, nicht ändern)
- Netzplan Zukunft: `pm/plan/plan_fusion.py` (Liste A, nicht ändern außer dem Lesen von historie.json, das schon eingebaut ist)

## Aufgabe 1: `pm/plan/historie.json`
Format: `{"hinweis": "KI-generiert, rekonstruiert ...", "phasen": [ {...}, ... ]}`. Je Phase:
`id` (H01 …), `name`, `von`, `bis` (YYYY-MM-DD, aus Git/BEFUNDE/ERINNERUNGEN belegt), `befunde` (z. B. "B-015…B-019, B-024"), `commits` (Liste Kurz-Hash, höchstens 8 wichtigste),
`dateien` (Hauptskripte/Ergebnisse, die es noch gibt; mit `ls` prüfen), `req` (REQ-IDs aus dem Lastenheft), `wer` (aus: Mensch, Opus, Sonnet, Haiku, PI, Hermes, Maschine; nur wenn belegt),
`ergebnis` (1–2 Sätze, Zahlen nur mit Fundstelle in `beleg`), `beleg`.
Vorschlag für die Phasen (prüfen, Daten belegen, bei Bedarf teilen oder zusammenlegen, Begründung in die Ergebnisdatei):
H01 Werkzeuge und W7-X-Validierung · H02 Inverse Kette, Stufe 0 (1 GW), eigene QA-Form · H03 Gehäuse, Stützschale, FEM · H04 Plasmagefäß Gyroid und Kühlsegment ·
H05 Wärmebilanz, Plasma 0-D, MHD, Alphateilchen · H06 Festigkeit, Varianten, Surrogat, Review-Paket · H07 Wechsel zu QI (ConStellaration), Tragwerk QI, Plasma zuerst ·
H08 QI und Spulen, Wirkungskarte · H09 Eigene Spulen K3, Kreis · H10 Baubare Spulen, Glätten · H11 KI-Schleifen (autoresearch, Ralph-Loop PI, Zufallslauf) ·
H12 Turbulenz GX, Paarvergleich, Zufall gegen PI · H13 Berichte, Vortrag, Videos (laufend).
Außerdem `entscheidungen`: Liste wichtiger Richtungswechsel mit Datum und Fundstelle (z. B. Wechsel QA → QI, „Plasma zuerst“, PicoGK nur Option, Gewichte des Autors), höchstens 15.

## Aufgabe 2: `pm/plan/wissensnetz.py` für Fusion
Nach Vorlage Batterie, angepasst: Knoten = Phasen H.. (erledigt) und Vorgänge der Zukunft (aus plan_fusion.py, Liste A importieren), Anforderungen (aus 01_lastenheft.md parsen),
Befunde (B-nnn aus BEFUNDE.md, Titel), Dateien, Entscheidungen. Status: Phasen „erledigt (rekonstruiert)“, Zukunft „offen“ bzw. „fertig“ nur wenn Ausgabedatei existiert.
Erzeugt: `pm/plan/wissensnetz.json`, `docs/projekt/03_anforderungsverfolgung.md` (REQ → Phasen/Vorgänge → Befunde → Status; Kopf wie im Lastenheft, „KI-generiert, nicht von Hand bearbeiten“),
`pm/plan/wissensnetz.html` (Ansicht wie Batterie, Farben je Art) und Obsidian-Notizen unter `wissen/` (Marker `wissen/.erzeugt`, Einstieg `wissen/Start.md`).
Prüfung im Skript: jede REQ hat mindestens eine Phase oder einen Vorgang; jeder Befund B-001…B-076 hängt an genau einer Phase (fehlende melden).

## Aufgabe 3: `pm/plan/zeitleiste.png`
Gantt-artige Zeitleiste: Phasen H01–H13 als Balken (Datum), danach die Zukunft ab 2026-11-13 in anderer Farbe (Dauern = Annahme, beschriften). Titel mit „KI-generiert“,
Legende „rekonstruiert“ / „geplant (Annahme)“. Bild selbst ansehen.

## Abbruch / Ausgabe
Höchstens ca. 60 min. Ergebnis kurz in `pm/plan/ERGEBNIS_HISTORIE.md`: was getan, Dateien, Zählung (Phasen, Befunde zugeordnet, fehlende), offene Fragen.
Nichts committen, pushen, löschen (außer eigenen Zwischendateien). Keine absoluten Pfade mit /home/… in erzeugte Dokumente schreiben (relative Pfade).
