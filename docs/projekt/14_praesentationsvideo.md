| Dok.-Nr. | FUS-DOC-14 | Version | 0.2 | Status | Entwurf |
|---|---|---|---|---|---|
| Titel | Präsentationsvideo: Storyboard | Ersteller | Claude Opus (KI) | Prüfer | – (Mensch offen) |

> **KI-generiert.** Plan des Videos. Es entsteht, nachdem DK8s6qwo durch die ganze Kette gerechnet ist (Netzplan Stufe K, Vorgänge V1–V4).

## Vorgabe des Autors (2026-11-12)
„Daraus soll ein Präsentationsvideo entstehen. Beginnen mit Magnetfeld und Teilchenbahnen, Plasma, Temperaturbetrachtung mit Simulation,
Steifigkeit und Dinge, die ich halt vergessen habe, am Ende das komplette Bauteil.“ (Anforderung REQ-D09)

Ergänzung des Autors (2026-11-13): „Denk auch an das Video, also Auslegung, Datensuche, Auswahl, Berechnung, Modell, das ganze Paket auch mit Kühlung und Festigkeit.“
Daraus: zwei Teile. Teil A zeigt den Weg zur Form, Teil B die Anlage. Kühlung (Szene 3) und Festigkeit (Szene 4) sind Pflichtszenen.

## Regeln
- Im Bild steht nur „Thomas Schmiegelt“ unten. Erklärungen gehören in den Begleittext (`video/begleittext_de.md`, `_en.md`), nicht ins Bild.
- Jede Szene zeigt ein gerechnetes Ergebnis für **dieselbe Anlage**: Plasma DK8s6qwo (Datensatzform ConStellaration, unverändert), eigene Spulen, auf 1 GW skaliert.
  Keine Szene mit einer anderen Form, ohne dass der Begleittext es sagt.
- Jede Zahl im Begleittext aus einer Ergebnisdatei (Pfad), Annahmen als Annahme. Zielbänder in den Farbskalen, im Begleittext erklärt.
- Einzelbilder erst nach Freigabe löschen.

## Teil A · Der Weg zur Form
| Nr | Szene | Bild | Quelle | Begleittext |
|---|---|---|---|---|
| A1 | Auslegung | Aufgabe „1 GW ins Netz“ → Leistungsbilanz; Größe gegen Feld (R0–B0-Diagramm), Grenzen als Bänder; Größen der Top 10 als Balken (12,6–21,2 m) | B-077, B-078 (sim/invers/*_1GW/bilanz_R0_B0.png, sim/kette_top10/ERGEBNIS.md); Korrektur Achslänge aus K2 | Was die Größe bestimmt (Einschluss, Leiterfeld), Annahmen von Stufe 0 |
| A2 | Datensuche | Datensatz ConStellaration: Formen als Punkte im Merkmalsraum, Filter QI-Güte → Pool 361 | Video Merkmalsraum (stellarator/loop_evolution.py), B-07x | Herkunft der Formen (Datensatz, unverändert), „Plasma zuerst“ |
| A3 | Auswahl | Spulen je Form, Paarvergleich mit den Gewichten des Autors, Zufall gegen lokalen Agenten, Top 10 → DK8s6qwo | B-075, B-076, B-078 (sim/spulenfreundlich/vergleich) | Wer entscheidet (Autor-Gewichte), was die KI rechnet, Zielkonflikt Spulen gegen Größe |

## Teil B · Die Anlage (Berechnung bis Modell)
| Nr | Szene | Bild | Quelle (Vorgang) | Begleittext |
|---|---|---|---|---|
| 1 | Magnetfeld und Teilchenbahnen | Spulen erscheinen, Feldlinien laufen um, Poincaré-Schnitt baut sich auf; Alphateilchen fliegen, verlorene leuchten auf | K2, K3 | Was ein Stellarator ist, Feldfehler, Alphaverlust |
| 2 | Plasma | Plasmaform mit Feldstärke als Farbe, Querschnitte drehen sich; Turbulenz-Flussröhre (GX) | K1, K4 | Herkunft der Form, QI, Turbulenzvergleich |
| 3 | Temperatur und Kühlung | Wärme vom Plasma zur Wand: Wandlast, Kühlkanäle (FluidX3D-Strömung), Temperaturfeld | K6, K7 | Wärmebilanz bis zur Turbine, Kühlregel 300/400 mm |
| 4 | Festigkeit und Steifigkeit | Lorentzkräfte als Pfeile, Tragwerk verformt sich (überhöht), Spannung als Farbe mit 500-MPa-Band | K8 | p99 heißeste Spule, Richtwert als Annahme |
| 5 | Was man leicht vergisst | Blanket und Abschirmung, Divertor, Kryostat, Zugänge, Montage, Vakuum | K5, K9 | Liste aus Recherche K9, was gerechnet ist und was nur geschätzt |
| 6 | Die komplette Anlage | Rundflug, Explosionsdarstellung, Zusammenfahren aller Schichten | K10 | Hauptmaße, Stand der Nachweise (Anforderungsverfolgung) |

## Szenenbausteine (unterwegs ablegen)
Jeder Vorgang K1–K10 legt sein Szenenmaterial gleich bei der Rechnung ab: `video/bausteine/<Vorgang>/` mit Bilderfolge oder Geometrie (STL/glTF/VTK),
Kamera-Vorschlag und `baustein.md` (Zahlen mit Quelldatei, 2–3 Sätze Begleittext DE/EN). Teil A entsteht aus vorhandenem Material (Vorgang V0).
So muss für das Video nichts nachgerechnet werden.

## Technik
Ergebnisse je Szene als Bilderfolgen (PyVista/ParaView) oder Geometrie (STL/glTF) → Blender (Kamera, Licht, Übergänge) → ffmpeg.
Ausgabe `video/praesentation_DK8s6qwo.mp4`, Begleittext DE/EN. Länge Ziel 5–7 min (Annahme): Teil A ca. 1,5 min, Teil B ca. 4–5 min.

---
*KI-generiert (Claude Opus, 2026-11-12, Version 0.2 2026-11-13). Status Entwurf. Freigabe nur durch den Autor.*
