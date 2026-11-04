# Ideen zur Stahlgrenze (500 MPa auf p99) - Entwurf

Stand: 2026-11-04, wird nach jeder Quelle ergänzt. Nur abgerufene Belege; Nicht-Gefundenes ist markiert. Eigene Schlüsse sind als "Schluss von mir" gekennzeichnet.

## (1) Kurzfazit
Stand: Entwurf; 500 MPa auf Stahl-p99 bleibt unverändert, hier stehen nur Wege zu einer sauberen späteren Klärung. Alle Schlüsse sind meine Ableitung aus den Quellen in Abschnitt 4.

1. Die 500 MPa sind rechnerisch 2/3 von 750 MPa (ITER C3) und gelten in der Norm-Logik für die Membranspannung (Mittelwert über die Wanddicke); für Membran plus Biegung erlaubt ITER nach einem EUROfusion-Protokoll das 1,5-Fache (S2, S3), und Spitzen an Kerben werden gar nicht gegen Sm, sondern über Ermüdung und Bruchmechanik bewertet (S1) - ein p99 der gesamten von-Mises-Verteilung vermischt diese Kategorien und ist damit kein Normvergleich.
2. Ein sauberer Nachweis braucht deshalb zusätzliche Auswertung am selben Modell (Spannungslinearisierung an Hotspots, Tresca statt von Mises, Netzkonvergenz, Nahtkarte), nicht eine andere Grenze; die Linearisierung ist an Übergängen und Lagern aber nur eingeschränkt gültig (S3), und die Zahl 1,5 steht uns nur aus einem Sitzungsprotokoll vor (S2), die ITER-Norm selbst ist nicht öffentlich.
3. Werkstoff: Grundmaterial C1/JJ1 (1000 MPa und mehr, S1) hat bei Schweissgut keine Entsprechung, 316L-Schweissgut liegt bei 4 K bei nur 626 bis 663 MPa (S5), KSTAR fordert für Schweissgut 90 % des Grundwerts (S4); Guss wurde bei ITER wegen nicht reparierbarer Poren verworfen (S1) - Nähte und Gussfehler setzen die eigentliche Obergrenze, nicht die Streckgrenze des Blocks.
4. Konstruktiv am wirksamsten und ohne Grenzänderung sind: Stützflecken-Lage optimieren (rund 2,4-fach weniger RMS-Spannung, S9), Spannungsstrafe in der Spulenoptimierung (etwa eine Grössenordnung weniger Maximalspannung, aber schlechtere Feldgüte, S6), Nähte aus den Hochspannungszonen legen, Schmiede- statt Gussstahl, Singularitäten an Punktlagern entschärfen.
5. Offen und nicht beschaffbar waren: ITER-Kriterien (intern), ASME-/RCC-MRx-Normtexte, W7-X-Zykluszahlen und Nahtbewertungen (HTTP 403) und die Stellaris-Veröffentlichung (403); diese Lücken müssen vor einer Grenzdiskussion über Fachleute oder Institutszugang geschlossen werden.

## (2) Ideenliste
Bewertungsskala: Aufwand (klein = Stunden im Postprozess, mittel = Tage Modellarbeit, gross = Wochen/neue Entwurfsschleife); Nutzen und Risiko qualitativ, Begründung als Schluss von mir mit Quellenverweis.

| Nr | Idee | Aufwand | Nutzen | Risiko |
|---|---|---|---|---|
| 1 | Spannungslinearisierung an den Hotspots (Membran, Biegung, Spitze getrennt) als Zusatzbericht neben dem p99 | klein bis mittel | Zeigt, ob der p99 aus Biegung/Spitzen oder aus echter Membranspannung kommt; 500 MPa gegen Membran, 1,5 x gegen Membran+Biegung als getrennte Zeilen (S2, S3) | Linearisierung an Übergängen, Lagern, Ecken nicht zulässig (S3); die Zahl 1,5 nur aus Protokoll (S2); darf nicht als Freigabe missverstanden werden |
| 2 | Tresca-Vergleichsspannung (Hauptspannungsdifferenz) zusätzlich zu von Mises ausgeben | klein | ITER und Referenzrechnungen nutzen Tresca (S2); Tresca ist nie kleiner als von Mises, also ehrlicher gegenüber den ITER-Zahlen | Zahlen steigen; Rechenschritt trivial, aber Ergebnis kann unbequem sein |
| 3 | Netzkonvergenz und Lagersingularitäten prüfen: p99 und Maximum bei zwei bis drei Netzfeinheiten; Randbedingungen von Punkt- auf Flächenlager | mittel | Trennt Modellartefakte von echten Spannungen; Kaptanoglu/Gil nennen genau dieses Problem (S6) | Mehr Rechenzeit/Speicher, während FE-Rechnungen laufen; Flächenlager müssen realistisch gewählt werden, sonst Schönrechnen |
| 4 | Stützflecken-/Klemmenlage optimieren statt von Hand setzen | mittel | rund 2,4-fach weniger RMS-Spannung bei W7-X-Modell mit 2 Klemmen je Spule (S9) | Optimierung kann Zielwert (RMS) senken, aber Spitzen lassen; Zielfunktion auf p99/Maximum erweitern |
| 5 | Spannungsstrafe oder Kraftgrenze in der Spulenoptimierung | gross | etwa eine Grössenordnung weniger Maximalspannung im Proof-of-Concept (S6) | Feldgüte (QI-Güte) sinkt; Ergebnis stammt aus Vereinfachtem Modell ohne reale Stütze (S6) |
| 6 | Rippen und dickere Zwischenspulen-Struktur in den Zonen mit Kippkräften | mittel | Aus ARIES-CS/Waganer; in EUROfusion-Protokoll wird 20 cm Zwischenspulenstruktur als Steifigkeitsgrenze diskutiert (S2, S9) | Platz für Ports und Kühlung; Masse ist laut Projektvorgabe unwichtig |
| 7 | Nähte aus den Hochspannungszonen legen; Teilung des Gehäuses dort, wo Spannung klein ist | mittel | Mitchell: alle drei Spannungsspitzen am ITER-Gehäuse lagen an Fertigungsnähten (S1); Schweissgut hat bei 4 K nur 626 bis 663 MPa (S5) | Verändert Fertigungsfolge und Zugänglichkeit (ITER-Erfahrung mit Teilpenetrationsnähten, S1) |
| 8 | Schmiedestahl oder gewalzte Platte statt Guss | klein (Entscheidung) bis gross | ITER verwarf Guss wegen Poren, die nicht reparierbar waren (S1); W7-X nutzt Stahlguss laut Konzept Q3 | Schmiedeteile in Stellarator-Form schwer (Mitchell: Platten haben konstante Dicke, S1) |
| 9 | Höhere Güte nur lokal (C1/JJ1) in Hotspots, Rest C3 | mittel | ITER setzt JJ1 nur im hochbelasteten Nasenbereich ein (S1) | Ist eine Änderung der lokalen Grenze (667 MPa für C1); nur mit Zeugnis- und Nahtnachweis; getrennt entscheiden, nicht zum Retten eines Ergebnisses |
| 10 | Bruchmechanische (defektbasierte) Bewertung der Nähte statt Spannungsgrenze | gross | ITER bewertet defektbasiert mit Ermüdungslebensdauer (60 000 Zyklen mit Faktor 2 in S1); bei wenigen Stellarator-Zyklen könnte die zulässige Fehlergrösse grösser werden (Schluss von mir) | Braucht Prüfbarkeit der Nähte, Eigenspannungen, Materialdaten bei 20-30 K; Norm intern; nur mit Fachleuten |
| 11 | Vorspannung (Precompression) zur Reduktion der Zugspannungen/Lastbereiche | gross | ITER nutzt Vorspannringe aus Glasfaser, die bei 4,2 K Radiallast halten (S1) | Neue Bauteile, Kriechen/Langzeit; fürs Stellarator-Modell ohne Referenz |
| 12 | Wicklungspaket und Gehäuse mit Spalt und Gleiten (Kontakt) modellieren statt Verbund | mittel | ITER: Spalt öffnet sich, Wicklung rutscht teils (S1); NCSX-Rechnung erlaubt Gleiten (konzept Q12) | Kann Spannung im Gehäuse erhöhen oder senken; realistischer, nicht automatisch niedriger |
| 13 | Ermüdung statt statische Spitzengrenze für Spitzen: Spannungsschwingbreiten je Lastfall | mittel | Stellarator ohne Disruptionen: Lastfolge vermutlich wenige, planbare Zyklen; Disruptionslast war bei einer Tokamak-Prüfung als Hauptlast genannt (S2, indirekt) | Zykluszahl für Zielanlage nicht belegt (W7-X-Quelle gesperrt); Eigenschaften der Naht gehen ein |
| 14 | Lastniveau und Kraftdefinition gegenprüfen (Kraft je Spule, Biot-Savart-Quelle) | klein | Aus konzept_sonnet: 1200 MN je Spule deutlich über ARIES-Werten | Bereits erfasst |

Begriffe: RMS = quadratischer Mittelwert (Mass für die Gesamtbelastung ohne einzelne Spitze). Disruption = plötzlicher Plasmaabbruch, der im Tokamak starke Zusatzkräfte erzeugt. Eigenspannung = Spannung, die vom Schweissen oder Schmieden im Bauteil zurückbleibt.

## (3) Zusätzliche Auswertung im Modell
(Voraussetzung: bestehende Rechnung, keine neue Lösung; nur Postprozess auf vorhandenen Ergebnissen wo möglich.)

1. Vollständiger Spannungstensor je Knoten/Element (nicht nur von Mises), um Tresca, Hauptspannungen und Richtung der grössten Zugspannung zu rechnen.
2. Auswertelinien durch die Wand (Stress Classification Lines) an den 5 bis 10 höchsten p99-Clustern; je Linie Pm, Pb, Peak; Cluster ausserhalb von Lagerflächen, Ecken und Übergängen getrennt kennzeichnen, weil dort die Linearisierung ungültig ist (S3).
3. Verteilung statt Einzelzahl: Anteil des Stahlvolumens über 500, 750 MPa; Grösse und Dicke der zusammenhängenden Überschreitungsgebiete im Verhältnis zur Wanddicke (kleine Spitzen vs durchgehender Querschnitt, Gedanke aus S1: "Minor areas can dominate performance").
4. Netzkonvergenz: p99, Maximum und Anteil über Grenze bei grobem, mittlerem, feinem Netz an den Hotspots; Abstand der Hotspots zu Randbedingungen.
5. Karte der Schweissnähte und Teilungsflächen über dem Spannungsfeld (Abstand Naht zu Hotspot); Nahtzone gegen niedrigere Streckgrenze (626 bis 663 MPa bei 4 K, S5) getrennt auswerten.
6. Temperatur- und Werkstoffdaten: Betriebstemperatur 20 bis 30 K des Gehäuses; Streckgrenze bei dieser Temperatur nachweisen (nicht belegt gefunden; S5 und S7 liefern nur 4 K und 77 K).
7. Spannungsbereich je Lastfall (Min/Max zwischen Kaltstart, Teil- und Volllast), Zykluszahl der Zielanlage festlegen (bisher nicht belegt), damit Ermüdung der Spitzen bewertet werden kann.
8. Kontaktstatus Wicklungspaket/Gehäuse und Lagerflächen (Spalt offen/geschlossen, Gleiten), um zu prüfen, ob Verbundannahme die Spannung verfälscht (S1).
9. Gegenprobe der Lasten: Summe und Netto der Kräfte je Spule, Vergleich mit ARIES-CS und Stellaris-Spannen (konzept_sonnet, Punkt 7).

Reihenfolge-Vorschlag (Schluss von mir): 9, 4, 1+2, 5, dann 7. Eine Grenzdiskussion erst führen, wenn 1 bis 5 vorliegen und Fachleute die ITER-Kriterien eingesehen haben.

## (4) Quellen mit Zitaten

Hinweis: Die PDF-Quellen wurden per Abruf lokal gespeichert und mit pdftotext gelesen; Zitate sind wörtlich aus diesem Text. Zeilenumbrüche entfernt.

### S1 Mitchell, "Large Magnet Structures for Fusion Technology: Lessons from ITER" (CAS-Proceedings 2024, Gauss Fusion, früher ITER) - Volltext gelesen
URL: https://arxiv.org/pdf/2608.27230 (abgerufen)
Begriffe: Streckgrenze Sy = Spannung, ab der Stahl bleibend fliesst. Bruchzähigkeit = Widerstand gegen das Wachsen eines Risses (MPa*Wurzel(m)). LEFM = lineare Bruchmechanik, rechnet aus, ob ein vorhandener Riss wächst. Sm = zulässige "Spannungsintensität" im Regelwerk.
Kriterien und Linearisierung:
- "With cryogenic magnet structures of thickness greater than ~20mm, the failure concern is dominated by fracture toughness and the risk of fast fracture from defects (possibly increased by fatigue)."
- "Fracture toughness is not very sensitive to temperature (and slightly decreases from room temperature with 316LN) but yield stress substantially increases."
- "Fracture depends on peak stress (concentrations, residual etc). Process of stress linearization no longer valid. The fabrication history (creating residual stresses) is important"
- "these are 'linearised', being converted into Membrane and Bending Stresses, Primary and Secondary, and Peak"
- "The combined limits on primary and secondary stresses are a way of saying that 'settlement' (work hardening) will occur over a few load cycles and the peak stresses are reduced (...) and are therefore acceptable"
- "The ITER design criteria for magnets are available only as internal references, [31]."
- "ITER decided (already before 2001) to use a 'defect based' code for the metallic mechanical design criteria on and essentially certify the magnets for a defined fatigue life based on the results of the manufacturing inspections and the structural analysis."
- "the present link between the magnet mechanical design criteria and pressure vessel codes is unhelpful and forces excessive conservatism on the analysis and the criteria." (Meinung des Autors)
- "Yield stress is increased above level of residual fabrication stresses. Limiting of stress peaks through local plasticity is less extensive than at room temperature and above" (bei 4 K gleicht lokales Fliessen Spitzen weniger aus als bei Raumtemperatur)
Werkstoffe:
- "The yield stress requirement now for the highest performance stainless steel in the ITER TF structures (shown as C1) is 1000 MPa and the fracture toughness is 180 MPam1/2, compared to a targeted development activity, in 1990, of 1200 MPa and 200 MPam1/2"
- "By 2008, only JJ1 remained (eventually being used in the highly stressed nose region of the ITER TF coil) and steel properties were at same level as obtainable industrially in the 1980s. ITER designated 3 grades of 316LN for structural material supply, C1, C2 and C3"
- "Nitronic 50 offers a generally higher yield stress but lower fracture toughness which is undesirable except in some specific applications."
- "Incoloy was used for the ITER model coils in the 1990s (and then dropped due to fabrication problems)"; Incoloy 908 "highly sensitive to Stress Accelerated Grain Boundary Oxidation (SAGBO)" (betrifft Leiter-Mäntel mit Nb3Sn-Wärmebehandlung, nicht unbedingt ein Gehäuse ohne diese Behandlung - Schluss von mir)
- JK2LB wurde für die CS-Spulen, ultra-low-carbon 316LN für die dünnen TF-Mäntel verwendet.
Guss gegenüber Schmiedestahl:
- "Casting was rejected because of poor properties (low modulus, low strength) and defects (voids) which were impossible to repair."
- "ITER relies on large amounts of forgings to achieve the best properties from a particular steel."
- Mögliche Alternative: "replacement of forgings by rolled plate, which is less specialised (and has a somewhat lower performance) but more readily available."
Schweissnähte und Ermüdung:
- "Case Stress Concentrations ... All three are coincident with manufacturing welds, and proper structural assessment is based on LEFM and requires calculations (or estimations) of the residual weld stresses."
- "a fatigue assessment according to the FFS LEFM procedure is carried out to provide a value for the maximum initial (t=0) allowable subsurface defect to sustain 60,000 cycles (safety factor of 2 on cycles)."
- "It was found in 2015 that the structure supplier could not (at reasonable cost) achieve full penetration welds in many of the structural attachments, and such welds must be treated as a defect according to the codes."
- "Minor areas can dominate performance, with large volumes not near critical stresses, and critical stresses in local areas well below those achieved in the base material. These areas are typically welds"
Konstruktive Hinweise:
- "A small gap between WP and TF coil case opens ... The peak stresses occur at the point where the straight leg ends and they are sensitive to the minimum wall thickness of the case at this point"
- "the cases contain very large areas of inefficiently used material ... There may be advantages in future devices in eliminating the case and distributing the material into the winding pack"
- "Because of the complex load conditions, efficient structural design is necessary to avoid large material volumes to satisfy the stress limits"
- "in the 'wedged' design the TF coil inner legs touch and support the overturning moment by friction" (Vergleich: ITER nimmt Kippmomente über Reibkontakt der Innenschenkel auf)
- Überlänge für Schweissverzug: "10mm Extra material on: PF interfaces ..." (nur für Fertigung, nicht Spannung)
Lücken: ITER-Kriterien (SDC) selbst nicht öffentlich; keine Zahlen zu Sm im Text.

### S2 EUROfusion WP-DTT1-ADC Technical Meeting Physics and Engineering 2019 (Militello) - Sitzungsprotokoll, Volltext gelesen
URL: https://indico.euro-fusion.org/event/1104/contributions/3299/attachments/1368/2694/Summary_of_meeting_Phys_Eng_Garching.pdf (abgerufen; Sekundärquelle, Protokoll, nicht die ITER-Norm)
- "linearize them through the thickness of the component by splitting the actual stress/position function into a peak (maximum), a membrane (average) and a bending component (linear fit corresponding to the equivalent torque)"
- "application of Tresca criterion on the membrane with failure limit of 660 MPa and on the membrane + bending with failure limit of 870 MPa."
- "Therefore, the WP-ADC criterion is more stringent since it is looking only at the peak value and with a lower failure limit."
- "magnet structural design guidelines, which give a Yield Strength of 1000 MPa (2/3 of which gives the membrane limit in our calculations and 1.3*(2/3) gives the membrane plus bending limit according to WP-MAG practice and ITER criteria). The material is an aged variant of the 316LN steel alloy, probably corresponding to FMJJ1 (need to check properly)."
- "After checking the ITER guideline on 'Magnet Structural Design Criteria Part 1: Main Structural Components and Welds' it was found that the linear elastic approach and the membrane/membrane plus bending approach was the selected method ... The only remarkable difference was the design factor in front of the membrane+bending limit, which is 1.5 for ITER and 1.3 for WP-MAG."
- "even at low temperature the structural material retains sufficient plasticity (...) this allows stress linearization and simplifies the analysis"
- Schluss von mir: Nach dieser Quelle gilt bei ITER 2/3 Sy nur für die Membranspannung; Membran plus Biegung darf 1,5 * (2/3 Sy) erreichen. Unsere 500 MPa auf p99 der gesamten von-Mises-Verteilung (inkl. Biegung und Spitzen) ist damit strenger als die Normlogik. Das ist kein Freibrief zum Anheben, sondern zeigt, dass der Vergleichsmassstab (p99 gegen reine Membrangrenze) nicht der Norm entspricht. Offen: ITER-Norm selbst nicht abgerufen; die Zahl 1,5 steht nur in diesem Protokoll.

### S3 Mackenzie (Univ. Strathclyde), "Stress linearization concepts and restrictions in elastic design by analysis", ASME PVP 2017 - Volltext gelesen
URL: https://strathprints.strath.ac.uk/60871/2/Mackenzie_PVP2017_Stress_linearization_concepts_and_restrictions_in_elastic_design_by_analysis.pdf (abgerufen; beschreibt ASME VIII Div. 2, nicht die Norm selbst)
Begriffe: Pm = allgemeine Membranspannung (Mittelwert über die Wanddicke). PL = örtliche Membranspannung an einer Unstetigkeit (Übergang, Ecke), aber ohne scharfe Kerbspitze. Pb = Biegeanteil (linear über die Wand, null im Mittel). Q = Sekundärspannung (aus Zwang, z.B. Wärme- oder Montagedehnung). Peak = Zuschlag durch Kerbe oder lokale Wärme. SCL = "stress classification line", die Linie durch die Wand, entlang der linearisiert wird.
- "The Code limits on General Primary Membrane stress is the allowable stress S of the material. The value of S is generally the lower of the material yield stress divided by 1.5 or the Tensile Strength divided by 2.4. This restricts the allowable value of general primary membrane stress to less than or equal to two-thirds of the material yield stress."
- "Due to the margin between first yield and limit collapse for primary membrane plus bending stress, the stress limit for this category is set at 1.5S. Thus the allowable value of membrane plus bending stress is less than or equal to the material yield stress."
- "Secondary stress Q occurs at structural discontinuities ... Peak stress is defined as an increment of stress added to primary or secondary stress by a stress concentration or local thermal load."
- "In design by analysis, E*epsilon_R is treated as an elastically calculated maximum stress range and limited to twice yield. In terms of the allowable stress S, this corresponds to a limit on the stress range less than or equal to 3S." (Ratcheting = fortschreitendes Aufschaukeln bleibender Dehnung bei Wiederholung)
- "The Code recommendations essentially restrict linearization to regions where a valid bending plane can be identified, excluding regions such as transitions between structural elements where shear and warping are significant in comparison with bending."
- Schluss von mir: ASME VIII-2 trennt also vier Grenzen (Pm <= S, PL und Pm+Pb <= 1,5 S, Q-Bereich <= 3 S, Peak über Ermüdung). Die ITER-Logik (2/3 Sy, 1,5 für Membran+Biegung laut S2) folgt demselben Muster. Ein p99 der von-Mises-Spannung vermischt alle Kategorien und ist daher kein Normvergleich. Nicht abgerufen: ASME-Normtext selbst (kostenpflichtig), RCC-MRx (nicht gefunden, nur von Mitchell erwähnt: "RCC-MRx, 2025 ... ", "RCC-MR is following a similar trend").

### S4 Sa u.a. (KBSI/Doosan), "Mechanical Characteristics of Austenitic Stainless Steel 316LN Weldments at Cryogenic Temperature" (KSTAR, Konferenzbeitrag, Korean Nuclear Society) - Volltext gelesen (2 Seiten)
URL: http://www.kns.org/files/pre_paper/18/434%ec%82%ac%ec%a0%95%ec%9a%b0.pdf (abgerufen über die vom Server genannte Weiterleitung kns.org -> www.kns.org; Datei war PDF, lokal mit pdftotext gelesen)
- "The design criteria of the KSTAR magnet structure follow as[1]; (1) Yield strength: more than 750 MPa for base metal and 90% of base metal for weld metal. (2) Fracture toughness (KIC): more than 150 MPa m1/2 for base metal and 130 MPa m1/2 for weld metal."
- "Fracture toughness decrease linearly from 293 K to 4 K. Results show a peculiarity that GTA weld indicates the highest toughness at low temperature."
- "Figure 5 shows the reverse relation of fracture toughness and yield strength"; "Material containing low nickel like that in this study is less than 200 MPa m1/2."
- "The yield strength and fracture toughness of base metal, auto GTA weld, and EB weld satisfy the structural design criteria."
- Schluss von mir: KSTAR (kleineres supraleitendes Experiment mit 316LN) fordert Schweissgut-Streckgrenze nur 90 % des Grundwerkstoffs, also ca. 675 MPa bei 4 K. Die KSTAR-Grenze entspricht ungefähr ITER C3 (Sy > 750 MPa).

### S5 Weeks, Derimow, Benzing, NIST Technical Note 2229, "Tensile Tests at 77 K and 4 K on 316L Stainless Steel Welded Plates" (2022) - Volltext gelesen
URL: https://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.2229.pdf (abgerufen; PDF lokal gelesen)
Hinweis: 316L (nicht LN), Schweissgut von vier Lieferanten, 4 K.
- Abstract: "Relatively large differences in strength, elongation, and reduction in area were observed between the welds with the strongest two welds (W4 and W2) demonstrating a difference of almost 20 % in ultimate tensile strength at 4 K when compared to the welds with the lowest 4 K tensile strength (W1 and W3)."
- Abstract: "all welds exhibit a rise in yield strength, plus a decrease of total elongation and reduction in area. As expected, serrated yielding was observed in every test conducted at 4 K." (gezackte Fliesskurve bei 4 K)
- Tabelle 4 (Mittelwerte 4 K, Streckgrenze / Zugfestigkeit in MPa): W1 663 / 1171; W2 646 / 1438; W3 626 / 1197; W4 648 / 1534. Bei 77 K: Streckgrenze 544 bis 582 MPa.
- Schluss von mir: Schweissgut dieser 316L-Platten hat bei 4 K nur ca. 626 bis 663 MPa Streckgrenze, deutlich unter den 750 bis 1000 MPa des ITER-Grundwerkstoffs. Nach 2/3-Regel ergäbe das 417 bis 442 MPa; das liegt nahe an unseren 500 MPa und zeigt, dass die Grenze an Nähten niedriger sein kann als im Grundmaterial. 316L ist nicht stickstoffverstärkt; für 316LN-Schweissgut nicht gefunden.

### Nicht abrufbar (Vermerk)
- Fellinger/Bykov/Schauer, Risse in W7-X-Lateralstützen (Fusion Eng. Des. 2013): https://core.ac.uk/download/210814084.pdf -> HTTP 403. Nur Suchmaschinenzusammenfassung: Risse nahe den Schweissnähten zwischen Lateralstütz-Hohlkästen und Spulengehäusen, bewertet mit Paris-Gesetz, Ergebnis laut Zusammenfassung "predefined number of W7-X operation cycles is not jeopardized". NICHT BELEGT.
- Giannella u.a. (W7-X Ermüdung): pure.mpg.de ... Giannella_Fatigue.pdf -> HTTP 403. Bykov_Cyclic.pdf -> HTTP 403. Nicht umgangen.
- ASME VIII-2, ITER SDC, RCC-MRx Normtexte: nicht öffentlich/nicht abgerufen.

### S6 Kaptanoglu & Gil, arXiv 2603.15240, "A proof-of-concept for automated AI-driven stellarator coil optimization with in-the-loop finite-element calculations" (2026) - HTML-Version abgerufen, Auszüge
URL: https://arxiv.org/html/2603.15240v1
- "we construct a novel in-the-loop optimization of Von Mises stresses in the coils"
- Bildunterschrift Abb. 3: "the maximum Von Mises stress is reduced by about an order of magnitude" (bei Zusatz einer Spannungsstrafe in der Spulenoptimierung); Spulenverschiebung laut Abruf-Zusammenfassung von ca. 16 cm auf ca. 1 cm (Zahl nicht wörtlich zitiert, von der Abruf-Zusammenfassung übernommen).
- Strafterm laut Abruf: quadratischer Hinge auf die volumengemittelte von-Mises-Spannung, Schwelle 0,01 GPa. Die Arbeit nennt keine Streckgrenze oder Zulässigkeit.
- "somewhat an artifact" (hohe Spannung im Ausgangsfall; kleine Leiterquerschnitte, 11 m Hauptradius) und Verweis auf "Singular behavior in linear elastic problems": langsame Netzkonvergenz wegen vereinfachter Randbedingungen; realistische Stützstruktur nötig.
- Gleichzeitig: Feldgüte sinkt ("the field accuracy decreases", laut Abruf-Zusammenfassung).
- Begriff: Singularität = Stelle, an der die Spannung im Modell mit feinerem Netz immer weiter wächst (z.B. Punktlager, scharfe Innenecke); der Zahlenwert ist dort netzabhängig und sagt nichts über die echte Spannung.

### S7 Fedoriková u.a., "Development of Mechanical Properties of Stainless Steel 316LN-IG after Cryo-Plastic Deformation", Materials 2023, 16(19):6473 - Volltext teilweise abgerufen (Zusammenfassung des Abrufs)
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC10573374/ (abgerufen über die vom Server genannte Weiterleitung)
- Lösungsgeglühter 316LN-IG, Streckgrenze 0,2 %: 293 K 325 MPa; 77 K 790 MPa; 4,2 K 1070 MPa (Tabelle laut Abruf).
- "The strength and plastic properties were increased by a combination of cold and cryo-rolling"; nach 50 % Kaltwalzen bei tiefer Temperatur 4,2 K: "0.2YS = 1804 MPa and UTS = 2081 MPa"; aber "a dramatic reduction in plasticity", Bruchdehnung z.T. nur 2,2 %.
- Bruchzähigkeit: wird in der Arbeit nicht behandelt.
- Schluss von mir: Der Wert 1070 MPa ist ein Laborwert an Blech im Lösungsglühzustand, nicht ein Zeugniswert für Grossschmiedestücke. Kaltverfestigung erhöht die Streckgrenze auf Kosten der Dehnung, ist für geschweisste Grossgehäuse kein Weg.

### S8 QST Japan, indico.cern.ch Beitrag 4426095 (Abstract, 2021) - nur Abstract
URL: https://indico.cern.ch/event/975584/contributions/4426095/
- (Abstract) "QST developed new cryogenic structural material of JJ1 (0.03C-12Cr-12Ni-10Mn-5Mo-0.24N)" (wörtlich, lt. Abruf)
- (Abstract) "High tensile strength and fracture toughness at 4 K are required on structural materials"
- (Abstract) Produktion 2012 bis 2020, über 2000 Lose, mehr als 5000 t, sechs Hersteller (Abruf-Paraphrase, nicht wörtlich). Stichprobenprüfung mit rund 600 Zugversuchen bei 4 K und 77 K.
- Streckgrenz- und Zähigkeitswerte von JJ1 in dieser Quelle: NICHT enthalten. Aus S1: JJ1 nur im hochbelasteten Nasenbereich der ITER-TF-Spulen.
- Hinweis, nicht abgerufen (Seiten repo.qst.go.jp/records/73284 und 73285 lieferten HTTP 503): Die Suchmaschine fasste zusammen, QST habe als 4-K-Ziel Streckgrenze >= 1200 MPa und KIc >= 200 MPa*Wurzel(m) gesetzt. NICHT BELEGT, nur Hinweis.

### S9 Aus konzept_sonnet.md übernommen (dort lokal gelesen)
- Fu & Kaptanoglu, arXiv 2607.05749 (https://arxiv.org/pdf/2607.05749): "Compared to the baseline, cases A and C reduce sigma_v by over 2x by optimizing the locations of the support clamps." und "case C outperforms the rest, offering nearly 2.4x reductions in both RMS sigma_v and u over the baseline." sowie "A true W7-X coil consists of an Nb-Ti winding pack surrounded by a 316LN stainless steel support case."
- Wang, ARIES-CS (https://aries.pppl.gov/MEETINGS/0604/Wang-Magnet.pdf): "The Max. Von Mises stress of 652 MPa is found at inboard side of the coil supporting tube. The Max. stress occurs locally at very small region only." und "The design stress is taken as 2/3 of the yield strength at 4 K."
- Waganer (https://aries.pppl.gov/MEETINGS/0511/Waganer.pdf): "Rib-Stiffened Inter-Coil Structure ... Continuous inter-coil can be thinner without buckling".
- Heitzenroeder NCSX: "Max. stress is 219 MPa. Allowable = 327 MPa. Factor of Safety (FS) on allowable is 1.5".

### Nur Suchmaschinen-Hinweise (NICHT abgerufen, nicht als Beleg zu verwenden)
- W7-X-Betriebsfolge: etwa 1000 Hauptzyklen bei 2,5 T und etwa 100 bei 3 T bei ca. 70 % Entwurfslast (Bykov_Engineering.pdf, HTTP 403). Das wäre für die Ermüdungsfrage zentral; Abruf gesperrt, daher offen.
- FIRE-Entwurfskriterien: Struktur Sm = min(2/3 Sy, 1/2 Zugfestigkeit) (fire.pppl.gov, Host nicht erreichbar).
- Helias-Reaktorstudie rechnet mit 800 MPa Streckgrenze (Suchmaschine; Quelle nicht abgerufen).
- ITER-Lieferstufen "1000, 900, 700 und 500 MPa" für TF-Gehäuse (Suchmaschine, QST-Seite 503).
