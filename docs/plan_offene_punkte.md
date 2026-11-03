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
| 1 | ~~Verbinder von 0169: Platte oder Stege?~~ erledigt | prüft die Vermutung aus F-145 | 1 Tag | Stege netzstabil (+1 %), Platte nicht (+47 %), Vermutung widerlegt |
| 2 | Örtlich schwächen (Idee des Nutzers) | erste, globale Form ging nach hinten los | 2 Tage | weiche Enden, steifer Kern, Spitzen −30 % (Ziel) |
| 3 | Netzkonvergenz am Anschluss, Ausrundung | Spitzen wachsen mit dem Netz | 1–2 Tage | belastbarer Höchstwert statt σ99 allein |
| 4 | Abkühlung, Eigengewicht, Stützzylinder/Tragring als Bauteil, Keil + Gehäuse aus einem Stück | Modell bisher nur Magnetkraft, Lager starr | 3–4 Tage | Lastfälle wie im Regelwerk, Lager als Bauteil |
| 5 | Review-Paket Festigkeit | Stand ist gut genug für Fachleute | 1 Tag | 5–10 Seiten mit konkreten Fragen an die Festigkeitsleute |
| 6 | Alphas: Spulen von 0169, dann Spulen mit Alpha-Ziel nachoptimieren, Stöße | Spulen haben sich geändert; 16,6 % Verlust kommt von den Spulen | 3–4 Tage | Verluste für den empfohlenen Entwurf, Spulen mit weniger Verlust, Bahnen mit Abbremsung |
| 7 | Erstwand-Kühlung gekoppelt | Wärme und Festigkeit der Haut zusammen | 3 Tage | Haut, Kanäle, Temperatur und Spannung in einer Rechnung |
| 8 | Gyroid-Tauscher: Kondensator-Abwärme | Wunsch des Nutzers, Plan vom 2026-10-28 | 2–3 Tage | ehrliche Antwort, ob sich das lohnt (Carnot ~6 %) |
| 9 | Plasma 1-D, Linien- und Zyklotronstrahlung, Divertorlast, Blanket-Dicke aus Neutronik | genauere Stufe 0 | 1–2 Wochen | Profile statt Mittelwerte, Divertorlast mit Randstrahlung, Blanket-Dicke begründet statt angenommen |
| 10 | MHD: Mehrgitter, leitende Wände, Spulenfeld | Flüssigmetall-Option offen halten | 1 Woche | realistische Hartmann-Zahlen |
| 12 | Verguss im 3D-Modell sichtbar | in der Rechnung schon drin (2 cm), im Voxelmodell bei 80 mm nicht | 0,5 Tag | Schnittmodell 0169 mit Voxeln ≤ 8 mm nur im Ausschnitt |
| 11 | Studien-Runner | Ersatzmodell-Vorschläge waren der Anfang | 2 Tage | Agent wählt Ziele, Optimierer rechnet, Mensch entscheidet |

## Abgleich mit der README-Checkliste (2026-11-03)

| offener Punkt im README | im Plan |
|---|---|
| Plasma: Transport radial (1-D), Linien- und Zyklotronstrahlung, Divertorlast mit Randstrahlung | 9 |
| MHD: Mehrgitter für reale Ha, endlich leitende Stahlwände, Spulenfeld B(x) | 10 |
| Alphas: Spulen mit Alpha-Ziel nachoptimieren und Vergleich wiederholen, Stöße | 6 |
| Erstwand-Kühlung: dünne Innenhaut, schnelle Kanäle, Wärme gekoppelt rechnen | 7 |
| Variantenvideo | 0 |
| Verbinder von 0169: Platte gegen Stege | 1 |
| Örtlich schwächen | 2 |
| Netzkonvergenz und Ausrundung | 3 |
| Abkühlspannung, Eigengewicht, nachgiebiger Stützzylinder | 4 |
| Review-Paket Festigkeit | 5 |
| Verbinder und Tragring im Rechenweg; Keil und Gehäuse aus einem Stück | 4 (Verbinder sind seit doe1 im Rechenweg; offen: Tragring, Keil) |
| Stufe 0 genauer: Divertor-Wärmelast, Zyklotronstrahlung, Blanket-Dicke aus Neutronik | 9 |
| Studien-Runner | 11 |
| Verguss in der Geometrie (Rechnung erledigt) | 12 |
| Allgemeiner Weg STL → STEP | zurückgestellt |

## 0 Katalog und Video (läuft)

- Katalog (Liste 2) baut losgelöst weiter, danach Variantenbericht neu erzeugen und übersetzen.
- Video in Blender: zuerst kurz die „wilden“ Varianten, dann alle, am Schluss die übrig bleibenden zulässigen Entwürfe
  und 0169 im Schnitt. Im Bild nur der Name, Erklärungen im Begleittext.

## 1 Verbinder von 0169: durchgehende Platte oder einzelne Stege?

Frage: Ist 0169 netzstabil, *weil* seine Verbinder zu fast durchgehenden Platten verschmelzen?
Versuch: drei Varianten mit gleichen Spulen – (a) Verbinder überschneidungsfrei (wie die anderen Entwürfe), (b) wie bisher,
(c) bewusst durchgehende Platte zwischen den Spulen. Jede im Standard- und im feinen Netz.
Wenn (c) netzstabil und (a) nicht: Entwurfsregel „Schale statt Stege“ (passt zu ARIES-CS). Kann auch mit Nein ausgehen.

**Erledigt 2026-11-03 – Ergebnis: Nein.** σ99 Standard-/Feinnetz: (a) getrennt 387/392 MPa (+1 %), (b) standard
308/319 MPa (+4 %), (c) platte 336/493 MPa (+47 %). Getrennte Stege sind netzstabil, die lückenlose Platte nicht.
Keine Regel „Schale statt Stege“; eine Schale nur mit ausgerundeten Rändern weiter verfolgen (zu Punkt 3). Für 0169 ist
„getrennt“ der ehrlichere Wert (keine Doppelzählung, weiter zulässig). Protokoll F-153, Review-Paket Abschnitt 4.

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
- Tragring/Stützzylinder als eigenes FE-Bauteil zwischen den Lagerflecken (statt starrer Einspannung), Keil und
  Gehäuse als ein Körper (gemeinsame Knoten statt Verbinder) – Vergleich der Spannungen am Lager.
- Verguss: in der Rechnung schon enthalten (2 cm, E 10 GPa); im 3D-Modell → Punkt 12.

## 5 Review-Paket Festigkeit

5–10 Seiten: Modell, Annahmen, Werkstoff, Grenzen, Netzstudie, offene Fragen (z. B. „Ist σ99 als Bewertungsgröße
vertretbar?“, „Welche Anschlussform würdet ihr wählen?“, „Welche Lastfälle fehlen?“). Für die Festigkeitsleute in der
Firma des Nutzers.

## 6 Alphas
Erst die Verluste mit den Spulen von 0169 (die Spulen haben sich seit der Alpha-Rechnung geändert), dann ein
Alpha-Ziel in die Spulenoptimierung (z. B. Verlust schneller Teilchen in einer kurzen Bahnrechnung oder ein
Ersatzmaß wie die Abweichung von der Quasisymmetrie im Spulenfeld), Vergleich wiederholen. Danach Stöße
(Abbremsung an Elektronen/Ionen, Streuung), weil Alphas in Wirklichkeit ~0,5 s bis zur Abbremsung brauchen.

## 9 Stufe 0 genauer
1-D-Transport (Profile), Linien- und Zyklotronstrahlung, Divertorlast mit Randstrahlung; Blanket-Dicke aus einer
einfachen Neutronik (z. B. OpenMC, 1-D-Kugel-/Zylinderschalen) statt angenommen – bestimmt Package und Abstand
Spule–Plasma, also auch die Festigkeit.

## 12 Verguss im 3D-Modell
Nur ein Ausschnitt (eine Spule, ein Segment) mit Voxeln ≤ 8 mm, damit die 2-cm-Schicht sichtbar wird.

## 7, 8, 10, 11 Weitere Themen

Reihenfolge wie in der Tabelle; jedes Thema beginnt mit Frage und Literatur. Details stehen in ERINNERUNGEN und in den
Plänen zum Gyroid-Tauscher und zur Blei-Kühlung.
