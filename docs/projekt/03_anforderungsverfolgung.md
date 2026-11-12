| Dok.-Nr. | FUS-DOC-03 | Version | 0.1 | Status | Entwurf |
|---|---|---|---|---|---|
| Titel | Anforderungsverfolgung (erzeugt aus dem Netzplan, rekonstruiert) | Ersteller | Claude Sonnet (KI) im Auftrag von Claude Opus, pm/plan/wissensnetz.py | Prüfer | – (Mensch offen) |

> **KI-generiert, nicht von Hand bearbeiten:** `python3 pm/plan/wissensnetz.py` schreibt diese Datei neu. Die Zuordnung der Phasen ist eine Rekonstruktion (pm/plan/historie.json), Entwurf, nicht vom Autor freigegeben. „Status Lastenheft“ ist die Angabe aus docs/projekt/01_lastenheft.md, keine Prüfung.

| REQ | Anforderung | Phasen (rekonstruiert) | Vorgänge (Zukunft) | Befunde | Status Lastenheft | Vorgänge fertig/offen |
|---|---|---|---|---|---|---|
| REQ-F01 | Elektrische Nettoleistung ins Netz | H02, H05 | K1 | B-017…B-018 | Ansatz 0-D | 0/1 |
| REQ-F02 | Plasmaform mit gutem Einschluss einzelner Teilchen (quasi-isodynamisch, QI) | H07, H08, H12 | – | B-028, B-030…B-057, B-073…B-076 | erfüllt für Pool | – |
| REQ-F03 | Plasma zuerst: Auswahl nach Plasmagüte; Kollision und Spannung schließen nur Unr | H07 | – | B-028, B-030…B-051 | gilt | – |
| REQ-F04 | Eigene Spulen erzeugen das Plasmafeld | H02, H08, H09, H10 | K2 | B-017…B-018, B-052…B-064, B-066…B-072 | DK8s6qwo 2,0·10⁻⁴ | 0/1 |
| REQ-F05 | Spulen baubar: Biegeradius ≥ 2·d, Bahnen ohne Überlappung (Abwicklung), keine kr | H10, H11 | K2 | B-065…B-072 | DK8s6qwo 0 kreuzend | 0/1 |
| REQ-F06 | Tragwerk: Spannung am p99 der heißesten Spule ohne Randzone | H03, H06, H07 | K8 | B-019…B-051 | offen für DK8s6qwo | 0/1 |
| REQ-F07 | Dehnung im Wickelpaket | H06, H07 | K8 | B-027…B-051 | offen für DK8s6qwo | 0/1 |
| REQ-F08 | Platz zwischen Plasma und Spulen für Wand, Blanket, Abschirmung | H07 | K5 | B-028, B-030…B-051 | offen | 0/1 |
| REQ-F09 | Alphateilchen bleiben lange genug im Plasma | H05 | K3 | – | offen für DK8s6qwo | 0/1 |
| REQ-F10 | Wärmeabfuhr der Erstwand und des Gefäßes; Kühlwasser-Austritt größer als Eintrit | H04, H05 | K6, K7 | – | Segment gerechnet (QA-Form) | 0/2 |
| REQ-F11 | Turbulenter Wärmeverlust als Kriterium der Formwahl | H12 | K4 | B-073…B-076 | 16 Formen gerechnet | 0/1 |
| REQ-F12 | Masse des Tragwerks unwichtig, robusteste Reserve zählt | H06 | – | B-027, B-029 | gilt | – |
| REQ-F13 | Ein Satz, der alle Grenzen zugleich hält („Absprungbasis“) | H07, H12 | K11 | B-028, B-030…B-051, B-073…B-076 | offen; Kandidat DK8s6qwo (B-076) | 0/1 |
| REQ-D01 | Jede Zahl rückverfolgbar (Rechnung mit Datei oder Quelle mit wörtlichem Beleg) | H01, H13 | – | B-001…B-016 | gelebt seit Beginn | – |
| REQ-D02 | Erwartung vor jeder Rechnung, Vergleich danach | H05 | – | – | gelebt seit 2026-10-29 | – |
| REQ-D03 | Herkunft jedes Plasmas nennen: Datensatzform unverändert oder eigene Form (worau | H09 | – | B-058…B-064 | gelebt | – |
| REQ-D04 | Jedes Dokument als KI-generiert gekennzeichnet (Titelkasten und Fußzeile) | H13 | – | – | seit 2026-11-10 | – |
| REQ-D05 | Jede Grafik mit beschriftetem Zielband bzw. Grenze; unbelegt heißt „Annahme“ | H11 | – | B-065 | gelebt | – |
| REQ-D06 | Rechnungen losgelöst und pausierbar, paketweise gespeichert | H11 | – | B-065 | gelebt | – |
| REQ-D07 | Upload nur von Eigenem, nur auf Freigabe; fremde Texte nicht ins Repo | H13 | – | – | gelebt | – |
| REQ-D08 | Netzplan mit Vergangenheit (rekonstruiert) und Zukunft, Wissensnetz verknüpft An | – | D1 | – | neu 2026-11-12 | 1/0 |
| REQ-D09 | Präsentationsvideo zum Gesamtentwurf: Magnetfeld und Teilchenbahnen → Plasma → T | – | V1 | – | neu 2026-11-12 | 0/1 |
| REQ-D10 | Jeder Schritt als Berichtskapitel DE und EN, Prozess-Doku, README | H13 | B1 | – | gelebt | 0/1 |

---
*KI-generiert. Erzeugt aus pm/plan/wissensnetz.json. Befunde: 76 von 76 einer Phase zugeordnet, fehlend: 0. Prüffehler: 0.*
