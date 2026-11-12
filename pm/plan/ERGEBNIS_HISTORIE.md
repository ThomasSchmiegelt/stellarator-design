# Ergebnis: Vergangenheit rekonstruieren und Wissensnetz (2026-11-12)

> **KI-generiert** (Claude Sonnet im Auftrag von Claude Opus). Alles ist Rekonstruktion aus BEFUNDE.md, ERINNERUNGEN.md und Git; nicht vom Autor freigegeben.

## Was getan wurde
- `pm/plan/historie.json`: 13 Phasen H01 bis H13 mit Datum, Befunden, Commits (höchstens 8), Dateien (alle mit Dateisystem geprüft, 0 fehlend), REQ, Beteiligten, Ergebnis und Beleg; dazu 15 Entscheidungen mit Datum und Fundstelle.
- `pm/plan/wissensnetz.py` (mit `wissensnetz_ansicht.py`, `wissensnetz_obsidian.py`, `zeitleiste.py`): erzeugt `wissensnetz.json`, `docs/projekt/03_anforderungsverfolgung.md`, `pm/plan/wissensnetz.html`, `pm/plan/zeitleiste.png`, Obsidian-Notizen unter `wissen/` (Marker `wissen/.erzeugt`, Einstieg `wissen/Start.md`). Vorlage Batterie nur gelesen.
- Bilder selbst angesehen: `zeitleiste.png` (Read) und `wissensnetz.html` (Chromium-Screenshot, Phase H07 gewählt). Beides lesbar, Farben und Legende stimmen.

## Zählung
- Phasen 13, Vorgänge der Zukunft 19 (fertig 1: D1, offen 18), Anforderungen 23 (alle mit Phase oder Vorgang), Entscheidungen 15, Dateiknoten 125.
- Befunde B-001…B-076: 76 von 76 genau einer Phase zugeordnet, fehlend: keine, doppelt: keine.
- Obsidian: 272 Notizen (Phase 13, Vorgang 19, Anforderung 23, Befund 76, Entscheidung 15, Datei 125, Start 1), 974 Links geprüft, 0 fehlende Ziele.

## Abweichungen vom Vorschlag und Begründung
- **H01 bis B-016** statt B-014: B-015 und B-016 (Elmer-Magnetostatik, 70-Spulen-Lauf gegen Biot-Savart) sind Validierung und tragen das Datum 2026-10-24.
- **B-026 in H03** (Torus mit Schichten, Gehäuse-Anschauung), **B-027 und B-029 in H06** (Surrogat, Variantenbericht).
- **H04, H05, H13 ohne eigene B-Nummer:** zwischen B-027 (2026-10-25) und B-028 (2026-11-03) gibt es keine Befunde; Belege dort sind Commits und ERINNERUNGEN-Abschnitte. Sie sind im Feld `beleg` genannt.
- **B-065 (autoresearch) in H11, B-057 in H08** (Datum 2026-11-06, später durch B-061 widerlegt, vermerkt). B-072 (Satteldach, 2026-11-11) in H10, B-073 bis B-076 in H12.
- **Phasen überlappen** (z. B. H04, H05, H06, H13); eine Vorgängerbeziehung zwischen Phasen ist nicht belegt und nicht eingezeichnet. Nur Zukunftsvorgänge haben Pfeile.
- Zukunft „fertig“ nur wenn Ausgabedatei existiert: nur für D1 sind Ausgabedateien festgelegt (historie.json, zeitleiste.png, wissensnetz.py, Lastenheft). Für alle anderen Vorgänge ist kein Ausgabepfad belegt, sie stehen auf „offen“.
- Obsidian-Skript ändert anders als die Batterie-Vorlage weder `.gitignore` noch legt es `.obsidian/` an.

## Ausgabe der Läufe (Stand 2026-11-12)
`python3 pm/plan/plan_fusion.py`
```
KI-generiert. Vergangenheit: 13 Phasen (rekonstruiert). Zukunft: 14.75 Arbeitstage (Annahme), Start 2026-11-13.
Kritischer Pfad: D1 -> K0 -> K1 -> K2 -> K5 -> K6 -> K7 -> K10 -> K11 -> V2 -> V3 -> B2
```
`python3 pm/plan/wissensnetz.py`
```
geschrieben: pm/plan/wissensnetz.html
Obsidian-Notizen: {'Phase': 13, 'Vorgang': 19, 'Anforderung': 23, 'Befund': 76, 'Entscheidung': 15, 'Datei': 125, 'Start': 1} gesamt 272
Links geprüft: 974; fehlende Ziele: 0
13 Phasen, 19 Vorgänge (fertig 1, offen 18); Anforderungen 23, ohne Knoten: keine; Befunde zugeordnet 76/76, fehlend: keine, doppelt: keine; Prüffehler: keine
```

## Offene Fragen
1. **Wer in H01 bis H03, H05:** Es war „Claude Code“ ohne Modellangabe; die Rollenliste kennt das nicht. Eingetragen sind nur belegte Rollen (Mensch, Hermes, PI, Maschine). Modell bitte benennen, falls bekannt.
2. **Commits vor 2026-10-24:** Git beginnt erst am 24.10. (5ceeb3d, 66 Dateien); die Phasen H01 und der Beginn 22.10. stützen sich nur auf BEFUNDE/ERINNERUNGEN.
3. **H13 und die Vortragsseite:** Das Artefakt (V4 bis V22) ist nicht im Repo; Beleg nur ERINNERUNGEN. Commits für B-072, B-073 und Satteldach: nur im Sammelcommit c036704 gefunden (`git log -S"B-072"`).
4. **H07 ist groß** (B-028, B-030 bis B-051, 2026-11-03/04); eine Teilung (Tragwerk QI gegen Plasmadaten) wäre möglich, ist aber nicht durch Daten getrennt, da alles am 04.11. liegt.
5. **Ausgabepfade der Zukunft:** Für K0 bis B2 fehlen festgelegte Ausgabedateien; erst dann kann „fertig“ automatisch gesetzt werden.
6. **Protokoll KI-Einsatz** (`docs/projekt/08_ki_einsatz_protokoll.md`): ich habe diese Arbeit dort nicht eingetragen (nicht im Auftrag).
7. Nichts committet, gepusht oder gelöscht; eigene Zwischendatei (Builder) liegt nur im Scratchpad.

*KI-generiert (Claude Sonnet), 2026-11-12.*
