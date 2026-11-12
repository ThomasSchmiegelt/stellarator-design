| Dok.-Nr. | FUS-DOC-14 | Version | 0.1 | Status | Entwurf |
|---|---|---|---|---|---|
| Titel | Präsentationsvideo: Storyboard | Ersteller | Claude Opus (KI) | Prüfer | – (Mensch offen) |

> **KI-generiert.** Plan des Videos. Es entsteht, nachdem DK8s6qwo durch die ganze Kette gerechnet ist (Netzplan Stufe K, Vorgänge V1–V4).

## Vorgabe des Autors (2026-11-12)
„Daraus soll ein Präsentationsvideo entstehen. Beginnen mit Magnetfeld und Teilchenbahnen, Plasma, Temperaturbetrachtung mit Simulation,
Steifigkeit und Dinge, die ich halt vergessen habe, am Ende das komplette Bauteil.“ (Anforderung REQ-D09)

## Regeln
- Im Bild steht nur „Thomas Schmiegelt“ unten. Erklärungen gehören in den Begleittext (`video/begleittext_de.md`, `_en.md`), nicht ins Bild.
- Jede Szene zeigt ein gerechnetes Ergebnis für **dieselbe Anlage**: Plasma DK8s6qwo (Datensatzform ConStellaration, unverändert), eigene Spulen, auf 1 GW skaliert.
  Keine Szene mit einer anderen Form, ohne dass der Begleittext es sagt.
- Jede Zahl im Begleittext aus einer Ergebnisdatei (Pfad), Annahmen als Annahme. Zielbänder in den Farbskalen, im Begleittext erklärt.
- Einzelbilder erst nach Freigabe löschen.

## Szenen
| Nr | Szene | Bild | Quelle (Vorgang) | Begleittext |
|---|---|---|---|---|
| 1 | Magnetfeld und Teilchenbahnen | Spulen erscheinen, Feldlinien laufen um, Poincaré-Schnitt baut sich auf; Alphateilchen fliegen, verlorene leuchten auf | K2, K3 | Was ein Stellarator ist, Feldfehler, Alphaverlust |
| 2 | Plasma | Plasmaform mit Feldstärke als Farbe, Querschnitte drehen sich; Turbulenz-Flussröhre (GX) | K1, K4 | Herkunft der Form, QI, Turbulenzvergleich |
| 3 | Temperatur | Wärme vom Plasma zur Wand: Wandlast, Kühlkanäle (FluidX3D-Strömung), Temperaturfeld | K6, K7 | Wärmebilanz bis zur Turbine, Kühlregel 300/400 mm |
| 4 | Steifigkeit | Lorentzkräfte als Pfeile, Tragwerk verformt sich (überhöht), Spannung als Farbe mit 500-MPa-Band | K8 | p99 heißeste Spule, Richtwert als Annahme |
| 5 | Was man leicht vergisst | Blanket und Abschirmung, Divertor, Kryostat, Zugänge, Montage, Vakuum | K5, K9 | Liste aus Recherche K9, was gerechnet ist und was nur geschätzt |
| 6 | Die komplette Anlage | Rundflug, Explosionsdarstellung, Zusammenfahren aller Schichten | K10 | Hauptmaße, Stand der Nachweise (Anforderungsverfolgung) |

## Technik
Ergebnisse je Szene als Bilderfolgen (PyVista/ParaView) oder Geometrie (STL/glTF) → Blender (Kamera, Licht, Übergänge) → ffmpeg.
Ausgabe `video/praesentation_DK8s6qwo.mp4`, Begleittext DE/EN. Länge Ziel 3–5 min (Annahme).

---
*KI-generiert (Claude Opus, 2026-11-12). Status Entwurf. Freigabe nur durch den Autor.*
