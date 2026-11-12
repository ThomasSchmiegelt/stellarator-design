| Dok.-Nr. | FUS-DOC-01 | Version | 0.1 | Status | Entwurf |
|---|---|---|---|---|---|
| Titel | Lastenheft (rekonstruiert) | Ersteller | Claude Opus (KI) | Prüfer | – (Mensch offen) |

> **KI-generiert. Nachträglich rekonstruiert (2026-11-12).** Das Projekt lief seit 2026-10-22 ohne Lastenheft. Die Anforderungen unten sind aus
> README, BEFUNDE, ERINNERUNGEN und den Vorgaben des Autors zusammengetragen, jede mit Fundstelle. Wo eine Zahl nur angenommen ist, steht „Annahme“.
> Entwurf, nicht vom Autor freigegeben. Hobby- und Lernprojekt, keine Auslegung einer realen Anlage.

## 1 Anforderungen an die Anlage (Was)
| ID | Anforderung | Wert | Herkunft | Art | Status |
|---|---|---|---|---|---|
| REQ-F01 | Elektrische Nettoleistung ins Netz | 1 GW | README „Worum geht es“, Stufe 0 (B-018) | Ziel | Ansatz 0-D |
| REQ-F02 | Plasmaform mit gutem Einschluss einzelner Teilchen (quasi-isodynamisch, QI) | QI ≤ 5·10⁻⁴ (Pool) | B-028, Auswahl Pool spulenfreundlich | Muss | erfüllt für Pool |
| REQ-F03 | Plasma zuerst: Auswahl nach Plasmagüte; Kollision und Spannung schließen nur Unrealistisches aus | – | Vorgabe Autor, B-031 | Regel | gilt |
| REQ-F04 | Eigene Spulen erzeugen das Plasmafeld | Feldfehler ≤ 2,5·10⁻³ (Annahme: Bezug DATJ5FC) | B-071, loop_evolution.md | Muss | DK8s6qwo 2,0·10⁻⁴ |
| REQ-F05 | Spulen baubar: Biegeradius ≥ 2·d, Bahnen ohne Überlappung (Abwicklung), keine kreuzenden Nachbarspulen | – | Vorgabe Autor (B-070), spulen_montage.py | Muss | DK8s6qwo 0 kreuzend |
| REQ-F06 | Tragwerk: Spannung am p99 der heißesten Spule ohne Randzone | Richtwert 500 MPa (Annahme, nicht belegt) | B-043, B-045 | Muss | offen für DK8s6qwo |
| REQ-F07 | Dehnung im Wickelpaket | 0,3 % (Annahme) | README, B-049 | Muss | offen für DK8s6qwo |
| REQ-F08 | Platz zwischen Plasma und Spulen für Wand, Blanket, Abschirmung | Richtwert ≈ 1,3 m (HELIAS 5-B, B-039); Wert noch zu klären | B-039, Ziel Absprungbasis | Muss | offen |
| REQ-F09 | Alphateilchen bleiben lange genug im Plasma | Verlust und Wandtreffer nennen; Grenze offen | README Alphas | Soll | offen für DK8s6qwo |
| REQ-F10 | Wärmeabfuhr der Erstwand und des Gefäßes; Kühlwasser-Austritt größer als Eintritt | 300 / 400 mm (Vorgabe Autor) | Kühlung-Regeln | Muss | Segment gerechnet (QA-Form) |
| REQ-F11 | Turbulenter Wärmeverlust als Kriterium der Formwahl | Vergleich, kein Grenzwert | B-074 | Soll | 16 Formen gerechnet |
| REQ-F12 | Masse des Tragwerks unwichtig, robusteste Reserve zählt | – | Vorgabe Autor | Regel | gilt |
| REQ-F13 | Ein Satz, der alle Grenzen zugleich hält („Absprungbasis“) | REQ-F02 … F10 zugleich | Vorgabe Autor (Ziel Absprungbasis) | Ziel | offen; Kandidat DK8s6qwo (B-076) |

## 2 Anforderungen an Arbeitsweise und Dokumentation
| ID | Anforderung | Nachweis | Status |
|---|---|---|---|
| REQ-D01 | Jede Zahl rückverfolgbar (Rechnung mit Datei oder Quelle mit wörtlichem Beleg) | BEFUNDE, Prüfskripte | gelebt seit Beginn |
| REQ-D02 | Erwartung vor jeder Rechnung, Vergleich danach | Ereignisprotokoll, ERWARTUNG.md | gelebt seit 2026-10-29 |
| REQ-D03 | Herkunft jedes Plasmas nennen: Datensatzform unverändert oder eigene Form (woraus) | BEFUNDE, Bildunterschriften | gelebt |
| REQ-D04 | Jedes Dokument als KI-generiert gekennzeichnet (Titelkasten und Fußzeile) | Berichte, Vortrag | seit 2026-11-10 |
| REQ-D05 | Jede Grafik mit beschriftetem Zielband bzw. Grenze; unbelegt heißt „Annahme“ | Bilder | gelebt |
| REQ-D06 | Rechnungen losgelöst und pausierbar, paketweise gespeichert | ~/bin/rechnung | gelebt |
| REQ-D07 | Upload nur von Eigenem, nur auf Freigabe; fremde Texte nicht ins Repo | .gitignore, recherche_ablage lokal | gelebt |
| REQ-D08 | Netzplan mit Vergangenheit (rekonstruiert) und Zukunft, Wissensnetz verknüpft Anforderungen, Befunde, Dateien | pm/plan/ | neu 2026-11-12 |
| REQ-D09 | Präsentationsvideo zum Gesamtentwurf: Magnetfeld und Teilchenbahnen → Plasma → Temperatur → Steifigkeit → weitere Bauteile → komplette Anlage | docs/projekt/14_praesentationsvideo.md | neu 2026-11-12 |
| REQ-D10 | Jeder Schritt als Berichtskapitel DE und EN, Prozess-Doku, README | bericht/, README | gelebt |

---
*KI-generiert (Claude Opus, 2026-11-12). Rekonstruiert, Status Entwurf. Freigabe nur durch den Autor.*
