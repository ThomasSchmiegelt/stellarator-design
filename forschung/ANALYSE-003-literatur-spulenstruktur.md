# ANALYSE-003 — Literatur des Users zu Spulenaufbau und Stützstruktur (2026-10-24)

Quelle: 33 PDFs, vom User lokal abgelegt (nicht im Repository, nur zitiert). Gelesen: Titel und
Abstract aller Dateien, dazu Volltext-Suche in den vier relevanten Arbeiten.

## Einordnung

| Relevanz | Arbeiten |
|---|---|
| **hoch** (Spulen, Struktur) | Bachmann et al., *Re-design of EU DEMO with a low aspect ratio*, Fusion Eng. Des. 204 (2024) 114518 |
| mittel (Stufe 0) | Grulke et al., *Overview of Wendelstein 7-X high-performance operation*, Nucl. Fusion 66 (2026) 116003; Breuning et al., *Operational planning of magnetic confinement fusion power plants*, Fusion Eng. Des. 222 (2026) 115316; Coleman et al., Nucl. Fusion 65 (2025) 036039 (EU-DEMO-Auslegungspunkt) |
| gering | Solfronk et al. 2026 (ASTRA für Tokamak und Stellarator, Transport) |
| nicht für dieses Projekt | ~25 Arbeiten zur Plasmaphysik am Tokamak ASDEX Upgrade (MHD, ELMs, Flux Pumping, Szenarien, Diagnostik, Echtzeitregelung). Zwei Dateien sind doppelt. |

Hinweis: Fast alles betrifft **Tokamaks**. Stellaratorspulen sind nichtplanar und haben zusätzlich
Kräfte aus der Ebene heraus. Die Regeln unten sind deshalb Anhaltswerte, keine Stellarator-Vorgaben.

## Was wir übernehmen können (Bachmann 2024, Abschnitt 3.9 und Anhang A)

1. **Gewölbe auf der Torus-Innenseite („wedged“):** Die Innenschenkel der TF-Spulen liegen
   keilförmig aneinander und bilden ein Gewölbe. Es trägt die radialen Kräfte als toroidalen Druck.
   → Für uns: Auf der Torus-Innenseite statt einzelner Verbinder einen durchgehenden Keil vorsehen.
   Genau dort liegen in unserer ersten Rechnung die Spannungsspitzen (B-021).
2. **Zulässige Spannung:** von Mises ≤ 660 MPa im Gehäuse („nose“); Stahl mit Streckgrenze
   > 1000 MPa (ITER-Hochfeststahl). Das passt zu unserem Wert von 667 MPa.
3. **Seitenwände des Gehäuses: 100 mm** auf beiden Seiten. Das entspricht unserem Standard `wand_seite 0.1`.
   Der Innenteil („nose“) wird nach den Kräften ausgelegt. Bei uns entspricht das der Außenwand
   mit t_min…t_max.
4. **Lastanteil des Wickelpakets:** im Mittel 65 MPa Zug bzw. Druck, den Rest trägt das Gehäuse.
5. **Stromdichte im Wickelpaket** (DEMO-Größe):
   J_eng,LTS = 47,8 − 1,43·B_max [A/mm², T], gültig für B_max < 15 T;
   J_eng,HTS = 55,8 − 1,92·B_max, gültig für B_max > 15 T.
   Vergleich mit unserer Stufe 0:
   - Nb3Sn bei 10,9 T (A45): Formel ≈ 32 A/mm², wir rechnen mit 15 → **wir sind konservativ** (Wickelpaket zu groß).
   - HTS bei 14,7 T (A45): Formel ≈ 27 A/mm² (knapp außerhalb des Gültigkeitsbereichs), wir rechnen mit 40 →
     **wir sind optimistisch**, das Wickelpaket wäre etwa 1,5-mal so groß.
6. **Maximalfeld:** Faktor 1,08 auf B0·R0/R_i, weil die Spulen ein Polygon bilden. Bei uns
   ersetzt die Biot-Savart-Iteration k_B diese Formel.

## Stufe 0 (Grulke 2026, Breuning 2026)

- W7-X erreicht in den besten Entladungen eine Energieeinschlusszeit, die **30–40 % über ISS04**
  liegt. Unsere Grenze H ≤ 1,3 ist damit durch Messungen gedeckt.
- Das höchste bisher in W7-X erreichte ⟨β⟩ liegt bei **2,8 %** (bei reduziertem Feld), bei hohem Feld bei 1,5 %.
  Unsere Grenze β ≤ 5 % ist also eine Annahme für einen Reaktor, nicht gemessen.
- Breuning 2026 setzt für ein Stellarator-Kraftwerk einen Nettowirkungsgrad von 31,1 % bei Volllast an
  (Tokamak 29,8 %). Wir rechnen mit η_th = 0,35 plus getrenntem Eigenbedarf; das liegt in derselben Größenordnung.

## Konsequenzen / nächste Schritte

- Struktur (Skill `stellarator-flaechen`): auf der Torus-Innenseite ein Keil bzw. Gewölbe statt
  Einzelverbindern; Seitenwand 0,1 m beibehalten; Außenwand iterativ auf ≤ 660 MPa auslegen.
- Stufe 0 (Skill `stellarator-invers`): J_eng nach Bachmann als Option `--j_formel demo`; Empfindlichkeit
  β_max 3 % statt 5 % angeben.
