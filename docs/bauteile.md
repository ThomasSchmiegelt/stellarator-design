# Die Bauteile der Kraftwerkskette

Verständliche Erklärungen der Bauteile eines 1-GW-Stellarator-Kraftwerks, vom Plasma bis ins Netz. Allgemeines Fachwissen ist mit Quellen belegt (Stand der Abrufe: 2026-10-31). Zahlen mit dem Hinweis „Projekt" sind Annahmen oder Ergebnisse dieser Auslegung (siehe Projektbericht, Abschnitte Wärmebilanz und Divertor-Vorwärmer). Eine englische Fassung steht im Bericht (`components_en.tex`).

## Die Bauteile der Kette

Dieser Abschnitt erklärt die Bauteile vom Plasma bis ins Netz in einfachen Worten. Allgemeines Fachwissen ist belegt; Zahlen mit dem Hinweis „Projekt“ sind Annahmen oder Ergebnisse dieser Auslegung.

### 1. Fusionsplasma und Magnetspulen.
 Im Plasma verschmelzen Deuterium und Tritium (D-T) bei rund 150 Millionen °C [1]. So heißes Gas berührt keine Wand. Magnetfelder halten es in der Schwebe. Ein Stellarator formt dieses Feld allein mit verdrehten Außenspulen und treibt keinen Strom durch das Plasma. Er läuft daher von Natur aus im Dauerbetrieb, braucht aber stärkere Magnete als ein Tokamak [2]. Große Anlagen wie Wendelstein 7-X nutzen supraleitende Spulen, die flüssiges Helium auf etwa 4 K kühlt [3]. Dafür braucht es eine Kälteanlage. Projekt: Das Plasma liefert $P_{fus} = 3053 MW$ (mit Vorwärmer-Korrektur etwa 3140 MW). Offen: die Kräfte zwischen den Spulen sind etwa 1000-mal so groß wie bei W7-X, und die Stützstruktur ist noch nicht gelöst.

### 2. Neutronen und Alphateilchen.
 Jede D-T-Fusion setzt 17,6 MeV frei. Etwa 80% trägt das Neutron, den Rest das Heliumkern-Teilchen (Alpha) [4,5]. Das Neutron hat keine Ladung. Es verlässt das Magnetfeld und gibt seine Energie in der Wand und im Blanket ab. Das Alphateilchen bleibt im Plasma und heizt es [6]. Projekt: $f_\alpha = 0{,}2$ (genau $3{,}52/17{,}59$). Annahme: Die Alpha-Leistung verlässt das Plasma je zur Hälfte als Strahlung auf die Erstwand und als Teilchenstrom auf den Divertor ($f_{div} = 0{,}5$). Offen ist diese Aufteilung; sie hängt vom realen Plasma ab.

### 3. Erste Wand.
 Die erste Wand ist die Verkleidung, die dem Plasma zugewandt ist. Sie schützt die Spulen und fängt Wärme und Strahlung ab [7]. Bei ITER sitzt sie auf abnehmbaren Paneelen, und der Panzer wechselt von Beryllium zu Wolfram [8]. Wolfram hat den höchsten Schmelzpunkt aller Metalle, wird aber spröde [7]. Projekt: Die Wand fängt 305 MW Strahlung auf. Das sind 0,25 MW/m² auf 1230 m². Die Kühlkanäle sind für 0,5 MW/m² ausgelegt, also mit Faktor 2 Reserve. Das Kühlwasser (1890 kg/s) erwärmt sich um 30 K. Offen: Neutronenschäden am Wandmaterial; sie sind hier nicht untersucht.

### 4. Blanket.
 Das Blanket sitzt hinter der ersten Wand. Es hat drei Aufgaben: Es bremst die Neutronen ab und wandelt ihre Energie in Wärme. Es erbrütet Tritium, indem Neutronen auf Lithium treffen. Es schirmt die Spulen ab [9,8]. Tritium kommt in der Natur kaum vor; nur das Blanket kann es liefern [9]. Blei oder Beryllium vermehren die Neutronen (Multiplikation) [9]. Projekt: $M = 1{,}15$ (Annahme). Das Blanket führt 2808 MW ab, mit 17400 kg/s Druckwasser bei etwa 300 °C und $\Delta T = 30 K$. Das EU-DEMO-Konzept WCLL (Wasser, Blei-Lithium) zielt auf diese Bedingungen [10]. Offen: Kann das Blanket zugleich 2,8 GW abführen und genug Tritium erbrüten?

### 5. Divertor.
 Der Divertor lenkt Teilchen und Wärme, die aus dem Plasma entweichen, entlang offener Feldlinien auf gesonderte Platten [11]. Er führt Asche und Verunreinigungen ab und hält das Plasma sauber [12]. Die Asche besteht vor allem aus Helium, das die D-T-Fusion erzeugt [4]; Vakuumpumpen saugen es ab. Beim ITER-Divertor liegt die Flächenlast stetig bei etwa 10 MW/m², in langsamen Spitzen bis 20 MW/m² [12]. Projekt: 305 MW auf mindestens 31 m² bei 10 MW/m². Er wird kalt gekühlt (Wasser 130 °C rein, 136 °C raus, 5 MPa), wie beim EU-DEMO [13]. Das Projekt setzt dafür eine Kupferlegierung an. Offen: die Lebensdauer unter dieser Last.
 Beim Stellarator gibt es keine eigene Divertorspule wie beim Tokamak. Wendelstein 7-X nutzt einen Insel-Divertor: Magnetische Inseln, die von selbst an Flächen mit rationaler Verdrillung entstehen, werden von Divertorplatten geschnitten. Die Feldlinien laufen in einer Insel 150 bis 400 m weit, bevor sie auf eine Platte treffen [22]. W7-X hat 10 gleiche Divertoreinheiten (fünffache Symmetrie, je Modul oben und unten) [22]. Die wassergekühlten Platten sind so geformt, dass die Wärmelast örtlich 10 MW/m² nicht überschreitet, die technische Grenze [22]. Geplant sind Entladungen bis 30 min mit 10 MW Dauerheizleistung [22,3]. Gemessen bei W7-X: Auftrefflinie 2 bis 4 cm breit, höchste Divertorlast 3 bis 4 MW/m² (Nachtrag B-039). Offen im Projekt: Lage der Inseln für die eigenen Plasmaformen und die Divertorlast mit Randstrahlung (plan_offene_punkte.md, Punkt 9).

### 6. Primärkühlkreise.
 Die Kühlkreise von Blanket und Wand führen die Wärme heraus. Sie arbeiten mit Druckwasser wie im Druckwasserreaktor. Der hohe Druck hält das Wasser flüssig, obwohl es weit über 100 °C heiß ist [14]. Projekt: etwa 300 °C, $\Delta T = 30 K$, 17400 kg/s durch das Blanket und 1890 kg/s durch die Wand. Der Druck von rund 16 MPa ist eine Annahme. Auch die Wahl dieser Bedingungen ist eine Projekt-Entscheidung: Sie erlaubt eine Turbine aus einem Druckwasserreaktor. Offen: Die Leitungen müssen durch die engen Spulenspalte. Die Rechnung zeigt, dass sie dort reichlich Platz haben (mehr als Faktor 10 Reserve).

### 7. Dampferzeuger.
 Der Dampferzeuger ist ein Wärmetauscher. Heißes Primärwasser fließt durch viele dünne Rohre, außen siedet Wasser des Sekundärkreises zu Dampf [15]. Die Rohrwände trennen die Kreise, sodass Primärwasser nicht in die Turbine gelangt [15,14]. Das Projekt nimmt an, dass das Primärwasser Tritium oder Aktivierung tragen kann. Projekt: Frischdampf mit 78 bar, gesättigt, 2443 kg/s. Das sind die Werte des EPR [16]. Der Dampf ist gesättigt wie im Druckwasserreaktor; dafür setzt das Projekt $\eta = 0{,}35$ an (Annahme). Offen: Tritium kann durch die Rohrwand wandern; das ist nicht untersucht.

### 8. Divertor-Vorwärmer.
 Die Divertorwärme fällt bei nur etwa 130 °C an. Das reicht nicht für Dampf, wohl aber zum Vorwärmen des Speisewassers. Das spart Anzapfdampf, der dann in der Turbine Arbeit leistet. Projekt: Der Gyroid-Tauscher, eine gedruckte Wand mit gewundenen Kanälen, soll die 305 MW übertragen. Ergebnis der Rechnung: Der Vorwärmer bringt höchstens 73 MW Strom, und zwar nur ohne Temperaturannäherung und ohne Pumpen. Zum Vergleich: 107 MW wären 35% von 305 MW. Geht die Wärme ganz verloren, steigt die nötige Fusionsleistung um 10%. Offen: Die Korrelationen stammen aus Versuchen im kleinen Maßstab.

### 9. Dampfturbine.
 Die Turbine lässt den Dampf in vielen Stufen entspannen und wandelt Druck in Drehung um [17]. Mit Zwischenüberhitzung geht der Dampf nach der Hochdruckstufe zurück in einen Erhitzer und strömt dann weiter. Das bringt mehr Arbeit und weniger Tropfen in den letzten Schaufeln [17]. Projekt: Wärme $P_{th} = 3419 MW$, Wirkungsgrad $\eta = 0{,}35$, also brutto 1197 MW. Vergleich: Isar 2 hatte 3950 MW thermisch und 1485 MW brutto; eine Turbine dieser Klasse reicht. Annahme: Eine solche Turbine ist verfügbar. Offen: ob eine stillgelegte Turbine erhältlich ist.

### 10. Kondensator und Kühlturm.
 Der Kondensator kühlt den Abdampf zu Wasser. Er arbeitet im Unterdruck, damit die Turbine mehr Energie entnimmt [18]. Die frei werdende Wärme muss weg: Ein Nasskühlturm gibt sie ab, indem ein Teil des Wassers verdunstet [19]. Projekt: 2223 MW Abwärme bei 24,7 mbar (20,9 °C). Das ist fast das Doppelte der Strom-Leistung. Das ist bei jedem Dampfkraftwerk so. Offen: Standort und Wasserbedarf des Kühlturms; das Projekt hat sie nicht bestimmt.

### 11. Generator.
 Der Generator wandelt die Drehung der Turbinenwelle in Strom. Er nutzt die elektromagnetische Induktion: Ein bewegtes Magnetfeld erzeugt in Wicklungen eine Spannung [20]. Kraftwerke setzen Synchrongeneratoren ein, die mit dem Netz im Takt laufen müssen [20,17]. Projekt: Er erzeugt brutto 1197 MW Wechselstrom. Davon gehen 197 MW an den Eigenbedarf. Die Bilanz rechnet nur mit dem Gesamtwirkungsgrad $\eta$; ein Generatorwirkungsgrad steht nicht gesondert darin. Offen: Auswahl und Größe.

### 12. Eigenbedarf.
 Die Anlage verbraucht einen Teil ihres Stroms selbst. Projekt: Die Kühlmittelpumpen brauchen 137 MW ($0{,}04 P_{th}$, Annahme). Dazu kommen 60 MW für den übrigen Eigenbedarf: die Kälteanlage der Spulen, die Tritiumanlage und Gebäude. Die Kälteanlage hält die Spulen auf wenigen Kelvin [3]. Die Tritiumanlage soll Tritium aus Blanket und Abgas gewinnen und dem Plasma wieder zuführen (Beschreibung des Projekts, nicht belegt). Der Wert für den Rest ist eine Annahme; für die Erstwandkanäle allein rechnet das Projekt nur mit etwa 8 MW Pumpleistung. Offen: Der Gesamtwert von 197 MW ist nicht aus Einzelteilen aufgebaut.

### 13. Transformator und Netzanschluss.
 Ein Transformator hebt die Generatorspannung an, denn bei hoher Spannung fließt für dieselbe Leistung weniger Strom, und die Leitungen verlieren weniger Wärme [21]. Das Hochspannungsnetz nimmt den Strom dann auf. Projekt: Ins Netz gehen netto 1000 MW. Das ist die Vorgabe, aus der die ganze Kette rückwärts gerechnet wurde. Verluste im Transformator sind in der Bilanz nicht angesetzt. Offen: Netzanschlusspunkt und Auslegung.


### Betrieb: Dauer statt Puls.
 Ein Stellarator braucht keinen großen Plasmastrom, das Magnetfeld kommt allein aus den Spulen [2]. Er kann deshalb dauerhaft laufen. Ein Tokamak wie der europäische Demonstrationsreaktor wäre gepulst: geplant waren 2 h Betrieb und 15 min Pause zum Abpumpen des Gefäßes. Die thermische Trägheit überbrückt die Pause nicht, deshalb braucht er einen Wärmespeicher (etwa 80 % der Leistung ins Netz, 20 % in den Speicher) [23]. Beim Tokamak gibt es außerdem Disruptionen: Bei ITER würde der Plasmastrom von 15 MA in 10 bis 100 ms zusammenbrechen. Das induziert Ströme in den Bauteilen im Gefäß, die mit dem Magnetfeld große Kräfte erzeugen. Beim Stellarator gibt es diese Disruptionen nicht [23]. Regelbar ist die Leistung vor allem durch die Turbine (8 bis 10 min Regelzeit), das Plasma selbst ist in 3 s aus [23]. Projekt: Dauerbetrieb, kein Wärmespeicher für Pulspausen, kein Lastfall Disruption.


## Quellen

1. ITER Organization: What is fusion? \url{https://www.iter.org/sci/whatisfusion}, abgerufen 2026-10-31.
. <https://www.iter.org/sci/whatisfusion>
2. Wikipedia: Stellarator. <https://en.wikipedia.org/wiki/Stellarator>
3. Wikipedia: Wendelstein 7-X. <https://en.wikipedia.org/wiki/Wendelstein_7-X>
4. Wikipedia: Deuterium--tritium fusion. <https://en.wikipedia.org/wiki/Deuterium%E2%80%93tritium_fusion>
5. Wikipedia: Fusion power. <https://en.wikipedia.org/wiki/Fusion_power>
6. Wikipedia: Tokamak. <https://en.wikipedia.org/wiki/Tokamak>
7. Wikipedia: First wall. <https://en.wikipedia.org/wiki/First_wall>
8. ITER Organization: Blanket. <https://www.iter.org/machine/blanket>
9. Wikipedia: Breeding blanket. <https://en.wikipedia.org/wiki/Breeding_blanket>
10. Arena et al. 2023 (WCLL, siehe Bericht)
11. Wikipedia: Divertor. <https://en.wikipedia.org/wiki/Divertor>
12. ITER Organization: Divertor. <https://www.iter.org/machine/divertor>
13. You et al. 2022 (EU-DEMO-Divertor, siehe Literaturverzeichnis des Berichts)
14. Wikipedia: Pressurized water reactor. <https://en.wikipedia.org/wiki/Pressurized_water_reactor>
15. Wikipedia: Steam generator (nuclear power). <https://en.wikipedia.org/wiki/Steam_generator_(nuclear_power)>
16. Wikipedia: EPR (nuclear reactor)
17. Wikipedia: Steam turbine. <https://en.wikipedia.org/wiki/Steam_turbine>
18. Wikipedia: Surface condenser. <https://en.wikipedia.org/wiki/Surface_condenser>
19. Wikipedia: Cooling tower. <https://en.wikipedia.org/wiki/Cooling_tower>
20. Wikipedia: Electric generator. <https://en.wikipedia.org/wiki/Electric_generator>
21. Wikipedia: Transformer. <https://en.wikipedia.org/wiki/Transformer>
22. Endler, M. et al.: Managing leading edges during assembly of the Wendelstein 7-X divertor. EUROfusion-Vorabdruck WPS1-PR(18) 20457 (2018), eingereicht bei Plasma Physics and Controlled Fusion. <https://scipub.euro-fusion.org/wp-content/uploads/eurofusion/WPS1PR18_20457_submitted.pdf>, abgerufen 2026-11-11.
23. Videowissen: Interview auf dem ITER-Gelände mit einem Fusionsforscher aus Garching (Zuschauerfragen). Mündliche Aussage, maschinelles Transkript vom Nutzer bereitgestellt; Auswertung docs/recherche/video_iter_interview.md.

## Rechte und Zitierweise

- Wikipedia-Artikel (Quellen mit „Wikipedia"): Lizenz CC BY-SA 4.0. Hier stehen nur eigene Formulierungen und Fakten, keine Textübernahmen; die Quelle ist jeweils angegeben.
- ITER Organization (iter.org): Der Text ist urheberrechtlich geschützt. Es werden nur Fakten in eigenen Worten wiedergegeben und mit Quelle genannt (Zitatrecht §§ 51, 63 UrhG).
- Arena et al. 2023 (Energies, MDPI): offen zugänglich unter CC BY 4.0; You et al. 2022: siehe Literaturverzeichnis des Berichts, nur Fakten übernommen.
- Dieser Text steht wie das Repository unter der MIT-Lizenz.
