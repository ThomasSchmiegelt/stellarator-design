# Plan für die offenen Punkte (Stand 2026-11-03)

Grundlage: Checkliste im README, ERINNERUNGEN, Ergebnisse der Entwurfsstudie doe1 und der Fahrplan für die Forschung
(Frage → Literatur → Validierung → Unsicherheit → Review-Paket → Fachleute/Gelder → Versuch).
**Herausgenommen auf Wunsch des Nutzers (2026-11-03):** allgemeiner Weg STL → STEP (zurückgestellt, für Rechnungen nicht
nötig).

Jeder Schritt läuft wie bisher: Erwartung vorher ins Ereignisprotokoll, rechnen (pausierbar), Bilder ansehen,
Berichtskapitel DE + EN, README, Prozess-Doku.

## Reihenfolge auf einen Blick

| # | Thema | Warum jetzt | Aufwand | Ergebnis |
|---|---|---|---|---|
| 0 | Katalog fertig, Variantenvideo | läuft schon | 0,5 Tag | Video aller Varianten (Blender), Katalog vollständig |
| 1 | Verbinder von 0169: Platte oder Stege? | prüft die Vermutung aus F-145 | 1 Tag | Entscheidung „durchgehende Schale“ oder „einzelne Verbinder“ |
| 2 | Örtlich schwächen (Idee des Nutzers) | erste, globale Form ging nach hinten los | 2 Tage | weiche Enden, steifer Kern, Spitzen −30 % (Ziel) |
| 3 | Netzkonvergenz am Anschluss, Ausrundung | Spitzen wachsen mit dem Netz | 1–2 Tage | belastbarer Höchstwert statt σ99 allein |
| 4 | Abkühlung, Eigengewicht, nachgiebiger Stützzylinder | Modell bisher nur Magnetkraft, Lager starr | 2–3 Tage | Lastfälle wie im Regelwerk, Lager als Bauteil |
| 5 | Review-Paket Festigkeit | Stand ist gut genug für Fachleute | 1 Tag | 5–10 Seiten mit konkreten Fragen an die Festigkeitsleute |
| 6 | Alphas mit den Spulen von 0169 | Spulen haben sich geändert | 1–2 Tage | Verluste für den empfohlenen Entwurf, ggf. Alpha-Ziel |
| 7 | Erstwand-Kühlung gekoppelt | Wärme und Festigkeit der Haut zusammen | 3 Tage | Haut, Kanäle, Temperatur und Spannung in einer Rechnung |
| 8 | Gyroid-Tauscher: Kondensator-Abwärme | Wunsch des Nutzers, Plan vom 2026-10-28 | 2–3 Tage | ehrliche Antwort, ob sich das lohnt (Carnot ~6 %) |
| 9 | Plasma 1-D, Strahlung, Divertorlast | genauere Stufe 0 | 1 Woche | Profile statt Mittelwerte, Divertorlast mit Randstrahlung |
| 10 | MHD: Mehrgitter, leitende Wände, Spulenfeld | Flüssigmetall-Option offen halten | 1 Woche | realistische Hartmann-Zahlen |
| 11 | Studien-Runner | Ersatzmodell-Vorschläge waren der Anfang | 2 Tage | Agent wählt Ziele, Optimierer rechnet, Mensch entscheidet |

## 0 Katalog und Video (läuft)

- Katalog (Liste 2) baut losgelöst weiter, danach Variantenbericht neu erzeugen und übersetzen.
- Video in Blender: zuerst kurz die „wilden“ Varianten, dann alle, am Schluss die übrig bleibenden zulässigen Entwürfe
  und 0169 im Schnitt. Im Bild nur der Name, Erklärungen im Begleittext.

## 1 Verbinder von 0169: durchgehende Platte oder einzelne Stege?

Frage: Ist 0169 netzstabil, *weil* seine Verbinder zu fast durchgehenden Platten verschmelzen?
Versuch: drei Varianten mit gleichen Spulen – (a) Verbinder überschneidungsfrei (wie die anderen Entwürfe), (b) wie bisher,
(c) bewusst durchgehende Platte zwischen den Spulen. Jede im Standard- und im feinen Netz.
Wenn (c) netzstabil und (a) nicht: Entwurfsregel „Schale statt Stege“ (passt zu ARIES-CS). Kann auch mit Nein ausgehen.

## 2 Örtlich schwächen

Jeder Verbinder wird in drei Körper zerlegt (Ende – Kern – Ende), jeder Körper mit eigener Steifigkeit.
Iteration nach dem Spannungsverhältnis (fully stressed design): E_i ← E_i · (σ_ziel/σ_i)^α.
Erwartung festlegen, bevor gerechnet wird. Gegenprobe: Lastweg bleibt erhalten (Verformung darf nicht stark steigen).

## 3 Netzkonvergenz und Ausrundung

Örtliche Verfeinerung nur an den Anschlüssen (statt überall 1,5-mal mehr Stationen) und eine gerundete Anschlussform.
Ziel: ein Höchstwert, der mit dem Netz nicht mehr wächst. Dann sind die Spannungskategorien auch an den Anschlüssen
belastbar.

## 4 Weitere Lastfälle und Lager als Bauteil

- Abkühlung 293 K → 4 K (Stahl, Wickelpaket und Verguss schrumpfen verschieden).
- Eigengewicht (die Struktur wiegt rund 30 kt).
- Stützzylinder mit eigener Steifigkeit statt starrer Lager; Keil und Gehäuse aus einem Stück prüfen.
- Verguss: in der Rechnung schon enthalten (2 cm, E 10 GPa); im 3D-Modell erst mit Voxeln unter 10 mm sichtbar.

## 5 Review-Paket Festigkeit

5–10 Seiten: Modell, Annahmen, Werkstoff, Grenzen, Netzstudie, offene Fragen (z. B. „Ist σ99 als Bewertungsgröße
vertretbar?“, „Welche Anschlussform würdet ihr wählen?“, „Welche Lastfälle fehlen?“). Für die Festigkeitsleute in der
Firma des Nutzers.

## 6–11 Weitere Themen

Reihenfolge wie in der Tabelle; jedes Thema beginnt mit Frage und Literatur. Details stehen in ERINNERUNGEN und in den
Plänen zum Gyroid-Tauscher und zur Blei-Kühlung.
