# Tragwerkskonzept stark verdrillter Spulen (Recherche Sonnet)

Stand: Entwurf, wird nach jeder Quelle ergänzt. Nur belegte Aussagen; Nicht-Gefundenes ist markiert.

## Quellenprotokoll
### Q1 Bosch 2005, W7-X Folien (lokal gelesen)
URL: https://ncsx.pppl.gov/NCSX_Engineering/StellaratorInfo/W7-X/050921_StephanBosch.pdf (H.-S. Bosch, "WENDELSTEIN 7-X Overview and Status of Construction", PPPL 23.9.2005)
- "Welded construction in 10 half-modules, supports the whole magnets system"
- "The coils are fixed to the central support structure by Central Support Elements (CSE) and interlinked by Narrow Support Elements (NSE) Lateral Support Elements (LSE)"
- "Central Supports long extensions for coil fixation large forces and moments a bolted solution was found"
- "Narrow Supports on inner side sliding connection forces up to 1.5 MN contact must allow sliding (<5 mm) and tilting (<1o). Al-bronce pad with MoS2 layer"
- "Lateral Supports on outer side Rigid (bolted/welded) connection"

### Q2 Fu & Kaptanoglu, arXiv 2607.05749 "Towards joint optimization of stellarator coils and support structures" (lokal gelesen)
URL: https://arxiv.org/pdf/2607.05749
- "In all existing stellarator devices, the support structures are placed by hand after coil optimization as a post-processing"
- "There are two main types of stellarator coil support structures: shell-type and cage-type. In a shell-type support structure, the coils are embedded in a rigid shell ... Notable devices with shell-type support include LHD [30] and the canceled NCSX [31]. In a cage-type support structure, the coils are attached to support frames with a discrete set of clamps ... Notable devices with cage-type support include W7-X [7], HSX [32], and CFQS [8, 9]. While no systematic comparison exists, it is believed that a shell-type support can offer greater structural strength at the cost of fabrication complexity. In comparison, a cage-type support offers better plasma access and simpler construction at the cost of high load concentration"
- "The true W7-X support structure consists of 3 types of support elements that link each coil to the Central Support Structure and adjacent coils [7]."
- "A true W7-X coil consists of an Nb-Ti winding pack surrounded by a 316LN stainless steel support case."
- Ergebnis (W7-X-Spulen, vereinfachtes Modell mit nur 2 Klemmen je Spule): "Compared to the baseline, cases A and C reduce sigma_v by over 2x by optimizing the locations of the support clamps." und "case C outperforms the rest, offering nearly 2.4x reductions in both RMS sigma_v and u over the baseline."
- "typical Lorentz force density is ~100 MN/m3" gegenueber Gravitation ~80 kN/m3.
Begriffe: Shell-Typ = Spulen in einer durchgehenden steifen Schale; Cage-Typ = Spulen an einzelnen Klemmen/Rahmen. von Mises = Vergleichsspannung (ein Zahlenwert fuer die Materialbeanspruchung).


### Q3 W7-X IAEA-Vortrag 2004 (lokal gelesen, Folien)
URL: https://www.ipfn.tecnico.ulisboa.pt/cfn/20IAEAConf/presentations/T5/4T/FT_3_5/Talk_FT_3_5.pdf (Wagner et al., "Physics, Technologies and Status of the W7-X", IAEA 2004; Autorenzeile in der Textextraktion nicht eindeutig)
- "Components: non-planar coils NbTi CiC-conductor. Embedding: quartz sand and epoxy. Welded casing made out of cast-steel"
- "Coil support: to central ring ... Connection is screwed using ~ 400 mm long rods in the form of a matrix of screws (up to 3x3)"
- "Lateral support elements ... Torsion and bending moments up to 130 or 230 MNmm, respectively ... Only welded connections within modules"
- "Narrow support elements ... Forces up to 1.5 MN are transmitted. The contact zones must allow sliding (< 2mm) and tilting (<0.5 deg). Central element: AL-bronce pad with a MoS2 layer"
Hinweis: Bosch 2005 nennt "<5 mm" und "<1 deg", Wagner 2004 "<2 mm" und "<0.5 deg" - Widerspruch zwischen Quellen (Entwurfsstand), beide wiedergegeben.
Begriffe: CiC = Kabel-in-Rohr-Leiter; Narrow support = schmaler Stuetzblock zwischen benachbarten Spulen auf der Innenseite (Hochfeldseite); lateral = seitlicher Stuetzer aussen. MNmm laut Folie (Einheitenangabe uebernommen, unklar ob MNmm oder MNm).

### Q4 ARIES-CS Wang 2005 (lokal gelesen)
URL: https://aries.pppl.gov/MEETINGS/0509/Wang-Magnet.pdf (X.R. Wang, ARIES-Treffen 2005, Folien)
- "How can the coil system be supported to react the centering force pulling the coil radially towards the center of torus? (up to 350 MN for SPPS stellerator)"
- "Three kinds of forces acting on the coils: Large centering forces pulling each coil towards the center of the torus; Out-of plane forces acting between neighboring coils inside a field period; Weight of the cold coil system"
- "Proposed Solution: Arrangement of All Coils of One Field-Period on a Supporting Tube ... All out-of-plane forces are reacted inside the field-period of the supporting tube. The centering forces are reacted by a strong bucking cylinder ring in the center of the torus. Weight of the cold supporting tube has to be transferred to foundation by ~3 long legs each field-period."
- Tabelle Nettokraefte je Spule (ein Feldperiode, 6 Spulen): M1 Fr -76.7 MN; M2 Fr -222.9 MN, Fz 101.9 MN; M3 Fr 125.6 MN, Fz 125.1 MN; "Sum of all 6 coils -348 [MN] 0 0". (Vorzeichen/Koordinaten wie auf Folie; Fr radial, Ftheta toroidal, Fz vertikal.)
- "net centering force with a magnitude of 348 MN"; Pressung auf Bucking-Zylinder "about ~3 MPa" (Kontaktflaeche "S=117.5 m2 for one field-period"); "maximum stress intensity of the bucking cylinder, ~35.4 MPa, is far less than the design stress of 466 MPa"
- "The analysis confirms that the transfer of the centering forces between coil supporting tube and bucking cylinder is not possible between 'cold' and warm element (Contact pressure of ~3 MPa by far too high for any thermal insulator). The entire support structure has to be operated at cryogenic temperature."
- Werkstoff: "316 SS cold worked ... Design stress 446 MPa at 473 K" (Folie nennt an anderer Stelle 466; Widerspruch auf der Folie).
Begriffe: Bucking cylinder = dicker Stahlring in der Torusmitte, der die nach innen ziehende Zentrierkraft aufnimmt. Strongback = Ruecken-/Traegerstruktur.

### Q5 ARIES-CS Wang 2006 (lokal gelesen)
URL: https://aries.pppl.gov/MEETINGS/0604/Wang-Magnet.pdf (X.R. Wang, ARIES-Treffen April 2006)
- "the thickness of the coil tube and strong-back were initially decided to be 0.35 m for the inter-coil structure, and 0.65 m for the strong-back"
- "There are three segments of the coil supporting tube (one segment per field-period) bolted together to make a continuous structure ring."
- "The modular coils are assumed to be tied together with the grooves in the coil supporting tube."
- Werkstoff "Incoloy 908 ... Yield strength 1227 MPa at 4 K ... Design stress 818 MPa at 4 K"; "The design stress is taken as 2/3 of the yield strength at 4 K."
- "maximum displacement of 2.0 cm at the outboard of the coil supporting tube"; "The Max. Von Mises stress of 652 MPa is found at inboard side of the coil supporting tube. The Max. stress occurs locally at very small region only. Most regions ... are in a low stress level."; Spulen "Max. Von Mises Stress: 277 MPa"; Scherspannung Isolation lokal bis ~112 MPa, "Most of the coils are below 30 MPa". Schalenmodell 536 MPa / 2,08 cm, Volumenmodell 652 MPa / 2,0 cm.
- Randbedingung: "Two nodes located at bottom side of the coil tube are constrained to simulate the constraints from the machine support structure."

### Q6 ARIES-CS Waganer 2005 (lokal gelesen)
URL: https://aries.pppl.gov/MEETINGS/0511/Waganer.pdf
- "The structure resisting the radial loads is 45-55 cm thick to resist the JxB forces that are significantly greater than NCSX"
- "Use of a Grooved Continuous Shell Is a Good Approach: One piece construction, efficient load transfer, and minimal distortion are good attributes. However, assumption of uniform thickness shell is too massive and not an efficient structure"
- "Rib-Stiffened Inter-Coil Structure ... Ribs help transfer loads between thicker main coil structures ... Continuous inter-coil can be thinner without buckling"
- "Suggest aligning the continuous coil structure with the coils to eliminate overturning moments"
- Masse/Kosten Strongback+Schale: "Total 3.5 [Mkg]", "These costs represent 18% of the total Reactor System costs." (Einheit Mkg wie auf Folie.)

### Q7 NCSX Heitzenroeder 2007 (lokal gelesen)
URL: https://ncsx.pppl.gov/Reviews/FY08/Const_Oct07/Pres/Heitz_2.pdf (P. Heitzenroeder, "NCSX Construction Feasibility Review", 31.10.2007)
- "Modular coil assembly consists of 3 field periods. It serves as the structural backbone of the machine - the VV, PF, TF, and trim coils are all supported from it." und "Custom shims at flanged joints between adjacent coil winding forms"
- "Shell material: Inconel 625" (Folienangabe, Zusammenhang Kryo-Schale; Zuordnung unsicher, Kontext nicht geprueft)
- "Max. stress is 219 MPa. Allowable = 327 MPa. Factor of Safety (FS) on allowable is 1.5"; "Average stress is <100 MPa."
- "Alumina coated high friction shims used in the outer flange locations to lock coil positions relative to each other." "Type 1 - C-C field assembly bolted joints"; "Type 2 - Low-distortion welded inner leg interfaces used intra-period."
- "The coefficient of friction, mu, required is 0.39 for the C-C interface and ~0.16 elsewhere; measured value is 0.67." "Our design criteria allowable is 2/3 of this, or 0.44."
- "Developing and maintaining adequate clamping force for the friction shims is assured by: Using high strength A286 studs ..." 
Begriffe: Reibschluss = Kraft wird ueber Reibung zwischen verschraubten Flanschen uebertragen, kein Gleiten.

### Q8 Bosch et al., "Preparing the operation of Wendelstein 7-X in the steady-state regime" (lokal gelesen, Volltext)
URL (gespeicherte PDF, abgerufen ueber): https://publikationen.bibliothek.kit.edu/1000160181/152941773 (Bosch, van Eeten, Grulke u. a.; Zeitschrift in der Textextraktion nicht erkennbar)
- "as the coils interact on each other by electromagnetic forces, the coil system has to be strongly supported by different support elements"
- "All superconducting coils are fixed to a central support ring. This structure is made up of ten identical welded segments that are bolted together to form a pentagon-shaped ring of five modules. Each of the 70 coils is fixed radially inwards to the support ring in two points. The magnetic forces acting between the non-planar coils are taken by inter coil support elements. On the inner side of the torus, where the distance between coils is small and accessibility is limited, the so-called narrow support elements are placed. On the outboard side of the torus, the so-called lateral support elements are installed. The planar coils are supported via stainless steel arms, called planar coils support, against the non-planar coils."

### Q9 Kallmeyer u. a., "Mechanical instrumentation of the W7-X cryogenic structure" (SOFT 2010, nur Abstract, lokal gelesen)
URL: https://www.ipfn.tecnico.ulisboa.pt/soft2010_abstractbook/pdf/P4-077.pdf
- (Abstract) "The coils are mechanically supported by a central support ring and inter-coil structure elements which are highly loaded by electromagnetic forces during operation."
- (Abstract) "During high field operation the coils deform, and some bolted flanges are designed to open which is made possible by elastic deformation of long Inconel bolts."

### Q10 Egorov, Bykov, Schauer, "Coil winding pack FE-analysis for a HELIAS reactor" (SOFT 2010, nur Abstract, lokal gelesen)
URL: https://www.ipfn.tecnico.ulisboa.pt/soft2010_abstractbook/pdf/P2-053.pdf
- (Abstract) "The HSR50a modular coil size is very similar to that of the ITER TF coil, but also other mechanical and electromagnetic characteristics are quite similar."
- (Abstract) "Further analyses are required in order to optimize the coils as well as the magnet system support structure."
- Zahlen zu HELIAS-Kraeften/Spannungen: NICHT GEFUNDEN. Die Suchmaschinenzusammenfassung nannte "60 mm" Verformung (Schauer ISHW 2009) - die Quelle (w3.pppl.gov C14_Schauer.pdf) war per Abruf nicht lesbar (HTTP 403), daher NICHT BELEGT. HELIAS 5-B: kein abrufbarer Volltext gefunden.

### Q11 Bromberg, NCSX Final Design Review 2004 (lokal gelesen)
URL: https://aries.pppl.gov/MEETINGS/0406/Bromberg.pdf (Folien "Modular Coil Winding Form Design, Analysis, Specification, NCSX, Final Design Review, D. Williamson, May 19-20, 2004")
- "Assumption: 2-T EM loads, coil winding is continuously supported by shell structure" - "Results indicate max displacement of 0.038-in, peak Von Mises stress of 26-ksi (181-MPa) in MCWF"
(0,038 in = ca. 1 mm, Umrechnung von mir.)

### Q12 Freudenberg, NCSX-CALC-14-007 Non-Linear Modular Coil Analysis, 2007 (lokal gelesen)
URL: https://ncsx.pppl.gov/NCSX_Engineering/Analysis_Reports/WBS1_StellaratorCore/WBS14_ModularCoils/NCSX-CALC-14-007_NonLinearModCoilAnalysis/NCSX-CALC-14-007-00-Signed.pdf
- "The modular coils are wound onto stainless steel castings that are then bolted together to form a structural shell."
- Wicklung darf gleiten/abheben: "Contact regions defined in ANSYS allow the winding to slide ..." (Wicklungspaket gegen Gehaeuse, nicht Spule gegen Spule).

### Q13 Gil u. a., arXiv 2507.12681, "Efficient Computation of Stellarator Coils with an Augmented Lagrangian Optimization Method" (lokal gelesen)
URL: https://arxiv.org/pdf/2507.12681
- "it is estimated that the original Stellaris configuration by the start-up Proxima Fusion will have anisotropic deformations in the order of 15 mm, arising from electromagnetic loads [25]." ([25] = Lion u. a., Phys. Rev. Letters 2025)
- "The immense force requirements in this example are not unique to Stellaris, rather, they are emblematic of the inevitable challenges of reactor-scale coil design for stellarators."
- "peak HTS turn linear force on the filamentary coils is of 0.9 MN/m. This value is at the peak material force tolerances and limits the possibility for structural supports."
- Alternative Konfiguration #3: "linear forces on the HTS turns that are 29% lower" (laut Text; Konfiguration in Fig. 5/Tab. IV).
- "final decisions about coil and HTS stack design require full finite-element modeling of the coils and structural supports beyond the scope of this work."
Begriff: HTS = Hochtemperatur-Supraleiter. MN/m = Kraft pro Meter Leiter.

### Q14 Stellaris (Lion u. a., Fusion Eng. Des. 2025) - NICHT im Volltext abrufbar
- URL: https://www.sciencedirect.com/science/article/pii/S0920379625000705 : WebFetch HTTP 403; weiterer Direktabruf wurde vom Sicherheitssystem untersagt und nicht umgangen.
- Einzig abgerufen (Seite scribe.disroot.org/post/2137918, Highlight): "First high-field, modular stellarator support structure design."
- Proxima-Pressemitteilung (https://www.proximafusion.com/press-news/proxima-fusion-and-partners-publish-stellaris-fusion-power-plant-concept-to-bring-limitless-safe-clean-energy-to-the-grid): Stellaris umfasse "support structures that can bear the forces present when operating at full power." (Marketing-Aussage, keine Zahl.)
- Konstruktive Details (Verbinder, Lager, Spannungen) von Stellaris: NICHT GEFUNDEN. Nur die 15 mm (Q13, sekundaer zitiert) und 0,9 MN/m.

### Nicht belegte Suchmaschinen-Hinweise (Pruefen, nicht zitieren)
- Bykov u. a. zu W7-X: "compressive/tensile forces of 4.4/1.8 MN and torsion and bending moments up to 450 kNm" an Verbindungen (nur Zusammenfassung der Suchmaschine; Quelle per Abruf 403).
- Wikipedia (en) Wendelstein 7-X enthaelt keine Angaben zu Stuetzung/Kraeften (abgerufen, nur 50 nichtplanare + 20 planare Spulen).

## (1) Kurzfazit
1. Reale Stellaratoren erreichen Steifigkeit nicht durch einzelne Verbinder, sondern durch eine gemeinsame, dicke, durchgehende Struktur: W7-X einen geschweissten, verschraubten zentralen Stuetzring (Spule an zwei Punkten radial innen befestigt) plus Zwischenspulen-Elemente; NCSX und ARIES-CS eine durchgehende Schale, in die die Spulen eingebettet bzw. eingenutet sind (Q1, Q2, Q5, Q8, Q12).
2. Spule-zu-Spule-Verbindungen sind ueberwiegend fest (W7-X aussen "bolted/welded", NCSX reibschluessig verschraubt bzw. geschweisst, ARIES-CS in einer Nutenschale); gleitend ist bei W7-X nur der schmale Innenstuetzer mit begrenzter Last (bis 1,5 MN, Gleiten wenige mm) (Q1, Q3, Q7).
3. Die Zentrierkraft (Zug zur Torusmitte) wird bei ARIES-CS durch einen dicken Bucking-Zylinder im Torusinneren aufgenommen (348 MN je Feldperiode, ca. 3 MPa Flaechenpressung), die Kippkraefte zwischen Nachbarspulen innerhalb der Feldperiode in der Schale; die gesamte Struktur muss kalt sein (Q4).
4. Die Groessenordnungen der Referenzen (ARIES-CS Struktur bis 652 MPa lokal bei 2 cm Verformung und 818 MPa Designspannung in hochfestem Incoloy 908; NCSX 219 MPa; Stellaris ca. 15 mm Verformung) liegen weit unter unseren 306 mm und p99 1098 MPa bei 500 MPa Grenze, was auf fehlende Steifigkeit (Schale statt einzelner Verbinder), zu schwachen Werkstoff und/oder ein sehr hohes Lastniveau hindeutet (Q5, Q7, Q13; Schluss von mir).
5. Fuer Stellaris selbst fanden wir keine konstruktiven Details (Volltext gesperrt); die Lagerflecken-Positionen sind aber nachweislich optimierbar (ca. 2,4-fach weniger RMS-Spannung, Q2), und niedrigere Spulenkraefte lassen sich schon in der Spulenoptimierung erzwingen (Q13).

## (2) Tabelle je Anlage
| Anlage | Steifigkeitsquelle | Spule-Spule | Lager/Auflager | Groessenordnung | Quelle |
|---|---|---|---|---|---|
| W7-X (70 Spulen, 5 Perioden) | Zentraler Stuetzring, 10 geschweisste Segmente zu 5 Modulen verschraubt; Spulengehaeuse aus Stahlguss geschweisst | Innen "narrow support elements" gleitend (Al-Bronze mit MoS2); aussen "lateral support elements" starr verschraubt/verschweisst; Planarspulen ueber Stahlarme an Nichtplanarspulen | Jede Spule radial innen an 2 Punkten am Ring (verschraubt, ca. 400 mm lange Stangen, Matrix bis 3x3); manche Flansche duerfen elastisch oeffnen (lange Inconel-Bolzen) | Narrow: bis 1,5 MN, Gleiten <2 bis <5 mm; Lateral: Torsions-/Biegemomente 130 bzw. 230 (MNmm lt. Folie). Kraft je Spule: NICHT GEFUNDEN | Q1, Q3, Q8, Q9 |
| HELIAS 5-B / HSR50a | Spulengehaeuse + Zwischenspulen-Struktur (Abstract) | nicht belegt | nicht belegt | Spulengroesse wie ITER-TF-Spule; Zahlen NICHT GEFUNDEN | Q10 (nur Abstract) |
| ARIES-CS (Reaktorstudie, 3 Perioden, 6 Spulen je Periode) | Durchgehende genutete Stuetzschale je Feldperiode, 3 Segmente zu einem Ring verschraubt; Dicke 0,35 m (Zwischenspulen) bzw. 0,65 m (Strongback); spaeter Rippenschale | Spulen in Schalennuten fest "tied"; Kippkraefte innerhalb der Periode von der Schale getragen | Zentrierkraft ueber Bucking-Zylinder in Torusmitte; Gewicht ueber ca. 3 lange Beine je Periode; Randbedingung im Modell: 2 Knoten unten fixiert | Zentrierkraft 348 MN je Periode; Spulen-Netto 77 bis 223 MN radial; Struktur max 652 MPa lokal (Designspannung 818 MPa, Incoloy 908), 2,0 cm Verformung; Spule max 277 MPa; Bucking 35 MPa | Q4, Q5, Q6 |
| NCSX (3 Perioden, 18 Spulen) | Stahlguss-Wickelkoerper zu einer durchgehenden Schale verschraubt; Schale ist "structural backbone" | Aussen verschraubte Flansche mit hochreibenden Aluminiumoxid-Shims (Reibschluss), innen verschweisst; Spacer-Shims an Flanschen | Alle Bauteile (Vakuumgefaess usw.) an der Spulenschale aufgehaengt | Max 219 MPa (zulaessig 327), Mittel <100 MPa; Reibwert erforderl. 0,39, gemessen 0,67; Entwurfslast nur 2 T: ca. 1 mm, 181 MPa | Q7, Q11, Q12 |
| Stellaris (Proxima) | NICHT GEFUNDEN (Volltext gesperrt); Highlight: "First high-field, modular stellarator support structure design." | NICHT GEFUNDEN | NICHT GEFUNDEN | ca. 15 mm anisotrope Verformung (sekundaer), 0,9 MN/m Spitzenkraft je Leiter | Q13, Q14 |

Begriffe: Feldperiode = eine von sich wiederholenden Wiederholeinheiten des Torus (hier 3). Bucking = Gegenhalten durch massiven Ring. Reibschluss = Haftreibung statt Gleiten. Von Mises = Vergleichsspannung. Shim = duenne Einlegeplatte.

## (3) Vorschlaege fuer die naechsten Modelltests
(Einordnung: Schluesse sind meine Ableitung aus den zitierten Quellen, nicht Aussagen der Quellen.)
1. Durchgehende Schale statt Einzelverbinder: Raum zwischen benachbarten Spulen als genutete, durchgehende Zwischenspulen-Schale ausfuellen (Dicke zunaechst 0,35 m, Strongback 0,65 m), je Feldperiode ein Segment, drei Segmente zum Ring verschraubt (fest, ohne Gleiten). Begruendung: ARIES-CS hat so 2 cm Verformung bei 348 MN Zentrierkraft/Periode. Quelle Q5 (Wang 2006), Q12; Fu bestaetigt Schale als steifer (Q2).
2. Rippenversteifte Schale, ausgerichtet an den Aussenebenen-Kraeften der Spulen: Rippen in Hochlastzonen, um Dicke zu sparen und Knicken zu vermeiden. Quelle Q6 (Waganer).
3. Zentraler Lastring: radial innen starren Ring/Zylinder (Bucking bzw. W7-X-Stuetzring) einfuehren, an dem jede Spule an 2 Punkten radial befestigt ist; Zentrierkraft darueber ableiten. Test: Ring im Modell nur radial/axial steif, Lagerflecken an die Spulen-Innenseite. Quelle Q4, Q8.
4. Verbindungsart variieren: innen und aussen fest (Reibschluss oder Schweissung) statt Gleiten; Gleiten nur dort zulassen, wo Kraefte klein sind (W7-X-Narrow bis 1,5 MN, bei uns Verbinderkraefte vermutlich um Groessenordnungen hoeher - zu pruefen). Quelle Q1, Q7 (Reibwert 0,39 erforderlich).
5. Lagerflecken-Positionen optimieren statt von Hand setzen: Zielfunktion RMS-von-Mises und Verformung; Fu fand 2,4-fache Reduktion mit nur 2 Klemmen je Spule. Quelle Q2.
6. Werkstoff: Grenzwert 500 MPa mit ARIES-Wert vergleichen (Designspannung = 2/3 Streckgrenze bei 4 K, 818 MPa fuer Incoloy 908) und 316LN-Gehaeuse (W7-X, Q2). Auswertung zusaetzlich nach lokalem Maximum vs. p99 trennen; ARIES-CS toleriert ein lokales Maximum 652 MPa, wenn der Grossteil niedrig ist. Quelle Q5.
7. Lastniveau gegenpruefen: 1200 MN je Spule ist deutlich ueber den ARIES-CS-Nettokraeften (max 223 MN radial je Spule, 348 MN je Periode); Definition (Summe vs. Netto, Einheiten) und Biot-Savart-Quelle pruefen, bevor Struktur weiter aufgedickt wird. Stellaris-Wert fuer Verformung (15 mm) als Plausibilitaetsziel. Quelle Q4, Q13.
8. Last mit der Spulenoptimierung senken: Kraftgrenze je Leiterlaenge als Nebenbedingung; Variante mit 29 % weniger Kraft bei Stellaris-Geometrie existiert. Quelle Q13.
9. Gesamtstruktur kalt, Gewichtsabtrag ueber lange Beine (ca. 3 je Periode), Randbedingungen nur an wenigen Knoten (ARIES: 2 Knoten unten) statt Vollfixierung. Quelle Q4, Q5.

Offene Luecken: Stellaris-Konstruktion, HELIAS-5B-Zahlen, W7-X Kraft je Spule und Spannungen aus Bykov/Jaksic (alle Zugriffe 403/402 oder nur Abstract). Naechster Schritt: Volltexte ueber Institutszugang oder den User beschaffen.
