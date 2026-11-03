# Review-Paket Festigkeit – Entwurf (Stand 2026-11-03)

> **Status: Entwurf.** Gliederung und Fakten stehen, Plan-Punkt 1 (Verbinder als Platte oder Stege) ist gerechnet
> und eingetragen. Als Nächstes entsteht die fertige Fassung (5–10 Seiten, DE + EN, mit Bildern, PDF).
> Zielgruppe: Festigkeitsfachleute (FEM, Regelwerk) ohne Fusionshintergrund. Privates Hobbyprojekt, nicht kommerziell.

## 1 Worum es geht (½ Seite)

Ein Stellarator hält ein heißes Plasma mit supraleitenden Spulen in einem verdrillten Magnetfeld. Die Spulen tragen
Ströme von rund 20 MA und erfahren Lorentzkräfte von 100–150 MN/m (bis 1,1 GN Nettokraft je Spule zur Anlagenmitte).
Gesucht ist ein Tragwerk aus Spulengehäusen, Verbindern und Lagern, das diese Kräfte aufnimmt.
Entwurf: 1 GW netto, großer Radius R₀ = 10,4 m, B₀ = 6,5 T, Hochtemperatur-Supraleiter (REBCO), Betrieb bei ~4–20 K.

## 2 Modell (1 Seite)

- **Geometrie:** Spulenmittellinien aus der Optimierung (simsopt), je Spule ein Hex-Netz entlang der Bahn
  (Standard 64 Stationen bei 24 Spulen), Querschnitt 2 Wandzellen + Verguss + 4 Wickelpaketzellen je Richtung.
- **Werkstoffe:** Gehäuse 1.4429 (X2CrNiMoN17-13-3, 316LN), E = 200 GPa; Wickelpaket homogenisiert (Werte aus
  `struktur.WP`); Verguss Quarzsand-Epoxid 2 cm, E = 10 GPa; Verbinder Stahl, E als Stellgröße 20–200 GPa.
- **Last:** Lorentzkraftdichte f = J × B aus allen Spulen (Biot-Savart), nur Magnetbetrieb.
- **Lager:** Flecken auf der Gehäuseaußenseite (am größten/kleinsten Radius), **starr eingespannt**.
- **Löser:** Elmer, linear-elastisch, lineare Hexaeder mit 8 Knoten (Elmer-Typ 808), MUMPS.
- **Kette:** Plasma → Spulen → Package → Festigkeit → Temperatur in 1–3 min je Entwurf; 200-Punkte-Entwurfsstudie.

## 2a Wie das Tragwerk entstanden ist (1 Seite)

Die Stützstruktur wurde nicht vorgegeben, sondern aus der Kraftanalyse abgeleitet. Anstoß war die Vorgabe des
Projektleiters (2026-11-02): erst verstehen, wie die Kraft entsteht, dann das Tragwerk ändern.

1. **Kraft entlang der Spule.** Für jede Spule wurde die Lorentzkraft je Meter berechnet (Feld aller anderen
   Spulen + Eigenfeld). Ergebnis: 50–140 MN/m; die Summe je Spule zeigt mit bis zu 1,1 GN **nach innen zur
   Anlagenmitte** (Zentrierkraft).
2. **Seil oder Balken.** Ein gekrümmtes Stück trägt Querlast als Zug (Seilformel T = f_N/κ); ein gerades Stück kann
   das nicht und wird gebogen. Die größte Last (~130 MN/m) sitzt ausgerechnet auf dem fast geraden **inneren
   Schenkel** (κ < 0,08 1/m über ~7 m).
3. **Handrechnung.** Balken auf zwei Stützen, q ≈ 130 MN/m, l ≈ 7 m: M = q l²/8 ≈ 800 MNm; Hohlquerschnitt
   H = 1,36 m, h = 0,755 m → W ≈ 0,38 m³ → σ_B ≈ 2100 MPa. FEM mit dem damaligen Modell: 2129 MPa. Die Spannung kam
   also aus der Biegung des inneren Schenkels.
4. **Fehler im Ausgangsmodell.** Jede Spule war nur an ihrer **äußersten** Stelle gelagert, die Kraft zieht aber
   nach innen: Balken auf der falschen Seite gestützt.
5. **Vorbilder.** Tokamak: D-förmige Spulen, der gerade Schenkel liegt flächig an einem Stützzylinder bzw. ist
   verkeilt (wird gedrückt, nicht gebogen). ARIES-CS: durchgehende Stahlschale um alle Spulen, die Querlasten von
   Spule zu Spule weitergibt.
6. **Versuche mit denselben 16 Spulen (Tragwerk A–E):**

| | Tragwerk | σ99 | Verformung | Stahl |
|---|---|---|---|---|
| A | Lager außen (Ausgang), 6 Verbinder je Paar | 2129 MPa | 399 mm | 15,6 kt |
| B | Lager innen (Fläche zur Anlagenmitte) | 1454 MPa (−32 %) | 273 mm | 15,6 kt |
| C | innen und außen | 1372 MPa | 226 mm | 15,6 kt |
| D | + 12 Verbinder je Paar, 200 GPa (freie Biegelänge kürzer, M ∝ l²) | 947 MPa | 107 mm | 23,1 kt |
| E | + dickste Wände (größeres W) | 481 MPa | 41 mm | 37,0 kt |

   Erwartung vor dem Versuch B war −30 bis −50 %; gemessen −32 %. Seitdem ist „innen und außen“ Standard, und
   Verbinderzahl/-steifigkeit, Wanddicken und Lagerradius sind Stellgrößen der Entwurfsstudie.
7. **Was davon schematisch ist.** Im Rechenmodell sind die Lager **starr eingespannte Flecken** auf der Gehäuse-
   oberfläche (entspricht einem unendlich steifen Stützzylinder, optimistisch). Stäbe, innerer Stützzylinder und
   äußerer Ring im 3D-Modell sind nur Veranschaulichung, wohin die Lagerkräfte gehen; sie sind weder berechnet noch
   ausgelegt.
8. **Verbinderplatten.** Beim empfohlenen Entwurf 0169 liegen die 13 Verbinder je Paar so dicht, dass sie sich
   berühren oder überlappen – praktisch eine durchgehende Platte. Das war ein Nebeneffekt der Netzregeln, keine
   Absicht. Ob „Schale statt Stege“ der Grund für seine Netzstabilität ist, wurde nachgerechnet: nein (siehe 4).

## 3 Bewertung und Grenzen (1 Seite)

| Größe | Grenze | Herkunft |
|---|---|---|
| σ99 im Gehäusestahl (99-%-Wert der von-Mises-Spannung über das Stahlvolumen) | 500 MPa | S_m = ⅔ R_p0,2 bei 4 K, ITER-Güte C3 (R_p0,2 ≥ 750 MPa) |
| Membranspannung P_m je Wandschnitt | S_m = 500 MPa | Linearisierung über die Wanddicke |
| P_m + P_b | 1,5 S_m = 750 MPa | wie oben |
| Dehnung Wickelpaket | 0,3 % | REBCO irreversibel ab 0,45–0,72 % |

Werkstoffwerte: RT R_p0,2 295 / R_m 580 MPa (Tabellenwert); 4,2 K lösungsgeglüht 1070 / 1543 MPa (Fedoriková 2023);
mit hohem N > 1000 MPa in dicken Blechen (Sakurai 2024).

## 4 Ergebnisse (2 Seiten)

- 200 Entwürfe gerechnet, **7 zulässig** (bereinigt). Empfohlen: **0169** – 24 Spulen, 13 Verbinder je Paar
  (183 GPa), 28 kt Stahl, σ99 308 MPa (Standardnetz) / 319 MPa (1,5× Stationen).
- **Netzstudie:** Feinere Wände ändern kaum etwas; 1,5× Stationen entlang der Spule heben σ99 bei vier von fünf
  Kandidaten um 34–58 %, bei 0169 nur um 4 %.
- **Ort der Spitzen:** 77–100 % der 200 höchstbelasteten Elemente liegen < 1 m von einem Verbinderanschluss
  (scharfkantiger Steifigkeitssprung, Höchstwerte wachsen mit jeder Verfeinerung).
- **Kategorien:** In 99 % der Wandschnitte bleibt P_m bei den besten Entwürfen < 400 MPa; der Höchstwert von P_m liegt
  an der Einzelspitze am Verbinderende (örtliche Membranspannung P_L).
- **Weichere Verbinder** (alle gleichmäßig) erhöhen σ99 (+16 % bei 50 GPa): Die Verbinder sind Entlastungsweg.
- **Befund vom 2026-11-03:** In 0169 berühren oder überlappen sich benachbarte Verbinder, das Modell ist dort fast
  eine durchgehende Platte (Überlappungen doppelt gezählt). Nachgerechnet mit drei Verbinder-Modi:

| Modus | σ99 Standardnetz | σ99 1,5× Stationen | Zuwachs | Verformung | Verbinderstahl |
|---|---|---|---|---|---|
| standard (doe1, Überlappung doppelt gezählt) | 308 MPa | 319 MPa | +4 % | 19 mm | 15,2 kt |
| getrennt (Abstand ≥ eine Breite, beide Spulen) | 387 MPa | 392 MPa | +1 % | 27 mm | 11,9 kt |
| platte (lückenlos, gemeinsame Knoten) | 336 MPa | 493 MPa | +47 % | 31 mm | 16,9 kt |

  Erwartet hatten wir das Gegenteil (Platte netzstabil, Stege nicht). Getrennte Stege sind netzstabil, die lückenlose
  Platte nicht. Die Netzstabilität von 0169 kommt also nicht von der Plattenwirkung. Die Spitzen liegen in gut
  geformten Elementen (skalierte Jacobi-Qualität 0,92–0,96), zu 86–96 % im Gehäuse. Auch „getrennt“ bleibt mit
  387 MPa unter 500 MPa zulässig; das ist der ehrlichere Wert für 0169.

## 5 Bekannte Schwächen (½ Seite)

1. Lager starr (Stützzylinder fehlt als Bauteil).
2. Verbinderanschlüsse scharfkantig → netzabhängige Spitzen; Bewertung gilt für Wände, nicht für Anschlüsse.
3. Nur Primärlast: keine Abkühlung (293 → 4 K), kein Eigengewicht, keine Ermüdung, keine Bruchmechanik.
4. Wickelpaket homogenisiert, Verguss ideal verbunden (keine Ablösung).
5. σ99 ist keine Regelwerksgröße, sondern eine Kenngröße für die Entwurfssuche.

## 6 Fragen an die Fachleute (Kern des Pakets)

1. **Bewertungsgröße:** Ist σ99 (99-%-Wert über das Volumen) als Suchkriterium vertretbar, oder sollten wir von
   Anfang an mit linearisierten Kategorien (P_m, P_L, P_b) entlang ausgewählter Schnitte bewerten?
2. **Spitzen am Anschluss:** Die Höchstwerte am Verbinderende wachsen mit dem Netz (Singularität). Wie behandelt ihr
   das üblicherweise – Strukturspannung nach Hot-Spot-Verfahren, Kerbspannung mit Ausrundungsradius, Submodell?
3. **Anschlussform:** Welche Form würdet ihr für einen Stahlverbinder zwischen zwei Gehäusen (Spalt ~0,2–1 m,
   Kräfte ~MN je Verbinder) wählen: Ausrundung, auslaufende Dicke, längere Anschlussfläche, durchgehende Schale?
4. **Platte oder Stege:** Im Modell ist die lückenlose Platte netzempfindlich (+47 %), getrennte Stege sind es nicht
   (+1 %). Ist das ein bekannter Effekt (Steifigkeitssprung am Plattenrand)? Spricht aus eurer Erfahrung etwas gegen
   eine durchgehende Schale (Montage, Wärmedehnung beim Abkühlen, Prüfbarkeit der Schweißnähte)?
5. **Lastfälle:** Welche fehlen in welcher Reihenfolge? (Vorschlag: Abkühlung, Eigengewicht, Schnellabschaltung/Quench,
   zyklische Last für Ermüdung.)
6. **Lagerung:** Wie würdet ihr den Stützzylinder abbilden – als eigenes Bauteil mit Kontakt oder als Feder-
   randbedingung? Welche Steifigkeit wäre realistisch?
7. **Werkstoff bei 4 K:** Reicht ⅔ R_p0,2 (ITER-Magnetkriterien) als Grenze, oder ist bei 4 K Bruchmechanik
   (K_IC, Rissfortschritt) maßgebend?
8. **Netz:** Wir nutzen lineare 8-Knoten-Hexaeder mit nur 2 Zellen über die Wanddicke. Wie stark unterschätzt das die Biegespannung (Schubversteifung)? Lohnen quadratische Elemente (20 Knoten) oder reicht eine dritte Zelle? (Unser Versuch mit 3 Wandzellen änderte σ99 kaum.)

## 7 Anhang (Verweise)

- Projektbericht, Kapitel Festigkeit; Variantenbericht (Steckbriefe aller zulässigen und knappen Entwürfe)
- Quellcode: `stellarator/kopplung.py`, `stellarator/hexmodell.py`, `stellarator/doe_auswertung.py`
- Repository: github.com/ThomasSchmiegelt/stellarator-design (MIT)

**Bilder für die fertige Fassung:** doe1_uebersicht, doe1_netz, doe1_kategorien, stahl_kennwerte,
modell3d_0169_schnitt, festigkeit_tragwerk (Kraftfluss), Netzbild eines Verbinderanschlusses mit Spannungsspitze (neu).
