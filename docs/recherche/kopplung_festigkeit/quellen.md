# Literaturwerte für die gekoppelte Studie Spulenform – Festigkeit – Temperatur

Stand: 2026-11-02. Entwurf: quasi-axialsymmetrischer Stellarator, R0 = 10,4 m, B0 = 6,5 T, 16 REBCO-Spulen, ~15 T am Leiter, bis ~1200 MN je Spule, Gehäuse 316LN bei 4 K (bisher 667 MPa = 2/3 Rp0,2 angenommen).

Statuskonvention:
- **geprüft** = DOI über Crossref abgefragt, Titel/Autoren/Jahr/Journal stimmen; der Zahlenwert wurde zusätzlich im Volltext (PDF) gelesen.
- **ungeprüft** = Zahl stammt aus einem Volltext ohne DOI/Crossref-Treffer (z. B. Bericht, Folien, arXiv-Vorabdruck) oder nur aus Suchmaschinen-Auszug; vor Zitat im Bericht nachprüfen.
- Alle Folgerungen für das Modell sind meine Einordnung, keine Aussage der Quellen.

---

## 1. Zulässige Spannung Spulengehäuse (316LN bei 4 K)

| Größe | Wert | Bedingung | Quelle | Status |
|---|---|---|---|---|
| ITER-Kriterium Strukturen | Sm = 2/3 · Sy (Sy bei Betriebstemperatur); Schrauben SmB = 1/2 · Sy | „Allowable stress based only on yield strength at operating temperature“; ITER Magnet SDC (intern, v2.0 von 2012) | Lee et al., IAEA-Folien 2025 [L1] | ungeprüft (Folien, kein DOI) |
| Garantierte Streckgrenze 4 K, ITER-Güte C1 (höchste) | > 1000 MPa (Anteil 25 % der 207 t) | ITER-TF-Struktur, 316LN-Güten C1/C2/C3 | Mitchell et al., IAEA-FEC-Beitrag IT/1-4 [M2] | ungeprüft (Jahrgang nicht verifiziert) |
| Garantierte Streckgrenze 4 K, Güte C3 (niedrigste) | > 750 MPa (45 % der Masse) | wie oben | [M2] | ungeprüft |
| Streckgrenze C1 bzw. Ziel 1990 | 1000 MPa bzw. 1200 MPa; Bruchzähigkeit 180 bzw. 200 MPa·m^0,5 | hochfester Stahl der ITER-TF-Struktur (Nase) | Mitchell, CAS 2024 [M1] | ungeprüft (arXiv 2608.27230, ohne DOI) |
| Rp0,2 316LN bei 4 K, ARC-Annahme | 1050 MPa; berechnete max. von-Mises 660 MPa (= 65 %) im Stützzylinder, 500 MPa in der TF-Struktur | Kryo-Temperatur, FEM Homogenisierung | Sorbom et al., ARC [S1] | geprüft |
| Rp0,2 / Rm 316LN bei 4,2 K (Laborwerte) | ca. 1045 / 1528 MPa bzw. verbessert 1204 / 1642 MPa, Bruchdehnung 33–34 % | nur aus Suchauszug zu Sas, Weiss, Jung | siehe Hinweis | ungeprüft (Originalquelle nicht gelesen) |
| Nitronic 50 vs. 316LN | N50 „generell höhere Streckgrenze, aber geringere Bruchzähigkeit“; in ITER nur für CS-Zugplatten; 316LN wegen Schmieden/Schweißen bevorzugt | Trend, keine Einzelwerte | [M1] | ungeprüft |
| Membran + Biegung | 1,5 Sm (ASME-Konvention); bei kryogenen Magneten ist die Spannungslinearisierung/Trennung primär-sekundär weniger belastbar | 4 K: Spitzen werden weniger durch Plastizität abgebaut, Bruch (Risswachstum, Ermüdung) dominiert gegenüber Fließen | [M1] (qualitativ); 1,5-Faktor nur aus ASME-Konvention/Suchauszug MIT 1983 | ungeprüft |
| JK2LB / JJ1 | im ITER nur JJ1 in der hochbelasteten TF-„Nase“ eingesetzt; keine Zahlen belegt | – | [M1] | **nicht gefunden** (keine Rp0,2-Werte) |

**Folgerung für unser Modell:** 667 MPa (= 2/3 · 1000 MPa) ist genau das ITER-Kriterium für die beste Güte C1; für Güte C3 (750 MPa) wären es nur 500 MPa. Als Hauptannahme sinnvoll, aber als „zulässig für Primär-Membran“ zu deuten: Spitzen/Schweißnähte werden im ITER zusätzlich über Bruchmechanik und Ermüdung begrenzt (Risswachstum mit Faktor 2 auf Lastspiele, K_I ≤ 2/3 K_IC). Die Rm-basierte Grenze (1/2 Su o. Ä.) ist im ITER-Kriterium nach Lee nicht Teil der Regel (nur Sy); bei 4 K ist 2/3 Sy ohnehin die strengere Bedingung, da Rm/Rp0,2 ≈ 1,4–1,5.

Hinweis zur Suchauszug-Quelle: Sas, Weiss, Jung (Steel A: 1045/1528 MPa → 1204/1642 MPa) wurde nicht im Original gelesen; nicht zitieren ohne Prüfung.

---

## 2. REBCO: Ic(B, T) für 15–20 K, 10–20 T

| Größe | Wert | Bedingung | Quelle | Status |
|---|---|---|---|---|
| Parametrisierung (Theva APC) | Kc(T,B,θ) = Kc0 · exp(−(T−Tl)/Tch) / [1 + √((k·sin(θ−θ0))² + (cos(θ−θ0))²)·B/Bcc]^b | Kc = kritischer Strom je Bandbreite (A/m); gültig T < Tc = 92 K und B ≥ 10 T; θ = 0: B senkrecht zur Bandfläche | Pardo et al. 2026 [P1], Anhang A, Fit nach Senatore et al. 2024 [P2] | geprüft (DOI Crossref ok; Formel im PDF gelesen) |
| Konstanten | Kc0 = 2,638·10^5 A/m (= 2638 A/cm), Tl = 4,2 K, Tch = 20 K, k = 0,08, b = 1,188, θ0 = 30°, Bcc = 11,44 T | wie oben | [P1] | geprüft |
| Temperaturabhängigkeit | exp(−ΔT/20 K): ca. −4,9 % Ic je K (relativ), im Gültigkeitsbereich der Formel | rein exponentieller Ansatz | [P1] | geprüft (abgeleitet) |
| Beispielwerte (eigene Rechnung, Kc in A/cm Bandbreite, θ = 0 / 30° / 90°) | 20 K, 15 T: 486 / 443 / 655; 20 K, 20 T: 400 / 360 / 565; 30 K, 15 T: 295 / 268 / 397; 4,2 K, 15 T: 1070 / 975 / 1443 | aus der Formel oben berechnet | eigene Rechnung (python) | abgeleitet |
| Fujikura-Band | zweiter, komplexerer Fit (c-Achse/ab-Ebene getrennt) in [P1]; Originalquelle ist eine CERN-interne Note (Fleiter, Ballarino 2014, EDMS 1426239) | – | [P1] | ungeprüft (CERN-Note nicht zugänglich) |
| Datenlage | kaum Messdaten für B ≳ 20 T, T ≲ 30 K, θ ≈ 90°; Hochfeld-/Tieftemperaturparameter oft extrapoliert | – | Suchauszug (arXiv 1512.01930 u. a.) | ungeprüft |

**Folgerung für unser Modell:** Die Formel erlaubt eine Temperaturmarge: Ic(T) fällt um rund 5 % je K, bei 15 T sinkt Ic von 20 K auf 30 K auf etwa 61 % des 20-K-Wertes. Sie gilt für ein bestimmtes Band (Theva APC) und ist ein Platzhalter, bis ein Hersteller-Datenblatt für das tatsächliche Band vorliegt. Die Dehnung ist hier nicht enthalten (siehe 3).

---

## 3. REBCO: Dehnungsempfindlichkeit von Ic

| Größe | Wert | Bedingung | Quelle | Status |
|---|---|---|---|---|
| Irreversible Zugdehnung | 0,45 % (SuperOx) bis 0,72 % (Bruker HTS); SuperPower und SuNAM 0,66–0,69 %; Fujikura 0,55–0,58 % bzw. SuperOx 0,47–0,49 % (Delamination, stufenförmiger Übergang) | 77 K Eigenfeld; irreversible Grenzen bei 4,2 K / 19 T identisch | Barth et al. 2015 [B1] | geprüft |
| Reversibler Bereich | unterhalb 0,4 % Dehnung keine erkennbaren Unterschiede zwischen den Herstellern; der reversible Ic-Verlust ist bei tiefer Temperatur und hohem Feld deutlich kleiner als bei 77 K | wie oben | [B1] | geprüft |
| Irreversible Spannung | 740–840 MPa bei 4,2 K, 19 T (alle Hersteller); bei 77 K ca. 660–700 MPa | auf das ganze Band bezogen | [B1] | geprüft |
| E-Modul der Bänder | 149–186 GPa; Streckgrenze bei 4,2 K ca. 10 % höher als bei 77 K | – | [B1] | geprüft |
| Hinweis ARC | „5 % Ic-Abfall bei 0,4 % Dehnung“; ARC-Auslegung hielt Leiterdehnung < 0,2 % (halbe Grenze) | zitiert aus Ref. [78] der ARC-Arbeit, nicht selbst geprüft | Sorbom et al. [S1] | geprüft (Aussage in [S1]); zugrundeliegende Messung ungeprüft |
| Spannungsempfindlichkeit quer | Querzug (c-Achse) nur < 30 MPa, Delaminationsgefahr | Einleitungstext von [B1] | [B1] | geprüft (als Aussage in [B1]) |

**Folgerung für unser Modell:** 0,4 % Zugdehnung im Band ist eine vernünftige, konservative Obergrenze (Barth: irreversibel erst ab 0,45–0,72 %); eine Auslegung auf 0,2 % wie bei ARC hat Faktor 2 Reserve. Die Dehnung im Band folgt aus dem Wickelpaket-Modell, nicht aus der Gehäusespannung direkt; mit E(Band) ≈ 150–185 GPa entspricht 0,4 % ungefähr 600–750 MPa im Band, aber das Band teilt sich die Last mit Kupfer und Stahl. Querzug (Delamination) ist die eigentlich kritische Last.

---

## 4. Kernheizung, Abschirmung, Fluenzgrenze

| Größe | Wert | Bedingung | Quelle | Status |
|---|---|---|---|---|
| Spitzen-Kernheizung TF-Wicklungspaket, EU-DEMO | < 50 W/m³ (= 0,05 mW/cm³) | Auslegungsgrenze; Lebensdauer 6 Vollleistungsjahre | Čufar et al. 2019 [C1] (Tabelle 1, dort Ref. [8][9]) | geprüft |
| Spitzen-Kernheizung, ARIES-CS | 2 mW/cm³ (= 2 kW/m³) Spitze; schnelle Fluenz (> 0,1 MeV) auf Nb3Sn 1e19 n/cm²; Cu-dpa 6e-3; Dosis Isolator 1e11 rad | 4-K-Magnet, 40 Vollleistungsjahre | El-Guebaly et al., UWFDM-1322 [E2] | ungeprüft (Bericht, DOI nicht verifiziert) |
| Spitzen-Kernheizung, ITER-Entwurfsphase (EDA) | 5 mW/cm³ Spitze; gesamt 55 kW (45 kW physics-Phase); 1e19 n/cm²; 6e-3 dpa; 5e9 rad | historische Grenzen (1991); spätere Werte sind niedriger/abweichend | El-Guebaly, Sawan, UWFDM-872 [E3] | ungeprüft (Bericht) |
| Gesamtheizung Spule, ARIES-CS | Wicklungspaket + Zwischenspulenstruktur ca. 12 kW, entspricht Kryolast ca. 5 MWe; Leistungsdichte im Blanket bis 44 W/cm³ | Stellarator, 2355 MW Fusionsleistung | [E2] | ungeprüft |
| Gesamtheizung Spule, ARC | TF-Spule 0,014 MW (= 14 kW); Neutronenschild 2,8 MW; Gesamtheizung innerer VV 26 MW | MCNP, Tabelle 6, ARC mit FLiBe + TiH2-Schild | [S1] | geprüft |
| Grenzwert Fluenz REBCO | 3e18 n/cm² (> 0,1 MeV) als untere Schranke („kein harter Ausfallwert“), aus Nb3Sn-Daten übernommen; REBCO „mindestens so gut“; ARC erreicht 3e18 nach 9 Vollleistungsjahren | Betriebsgrenze bei ARC ist Magnetspannung, nicht Ic | [S1] | geprüft |
| Messung REBCO | Bei 4,2 K / 15 T verkraften Bänder mit künstlichen Haftzentren ca. 4e22 m⁻² (= 4e18 cm⁻²), ohne solche ca. 6e22 m⁻²; bei 50 K liegt die Ic-Verschlechterung bei ca. 2e22 m⁻²; Verbesserung von Ic (zusätzliche Haftzentren) bis ca. 3e22 m⁻² bei 30 K, 15 T; Tc fällt ca. 2,2 K je 1e22 m⁻² | Bestrahlung bei Raumtemperatur, Messung bei tiefer T, Übertragbarkeit auf Betrieb unsicher | Fischer et al. 2018 [F1]; Zahlen 4e22/6e22 aus Dissertation Fischer 2019 (TU Wien, laut Suchauszug) | [F1] DOI geprüft, Zahlen nur aus Suchauszug: ungeprüft |
| Abschwächung, Wolfram | Leistungsdeposition (Neutronen und Gammas) fällt exponentiell mit Schilddicke, Halbwertsdicke 42,2 mm (e-fach: 60,9 mm); Wolframborid/-carbid ähnlich, W2B5 mit Boranteil bis Faktor ~10 weniger Neutronenfluss | Kugeltokamak, R0 1,4–2,2 m, Schilddicke 253–670 mm, MCNP | Windsor et al. 2021 [W1] | geprüft (DOI, Wert im PDF gelesen) |
| Abschwächung, Stahl/Wasser | **kein belegter Wert gefunden.** Rohabschätzung aus unlesbarer HAPL-Folie: e-fach ca. 5 cm für 14-MeV-Neutronenfluss (50 → 80 cm Stahlschild: 5e8 → 1e6 n/cm²s) | nur Suchauszug | nicht zitierfähig | ungeprüft |
| Wolframcarbid im Stellarator | WC statt Brutstoff/B-Stahl senkt die Gesamtdicke um ca. 30 cm; WC bringt die kompakteste Radialbauweise; Wasser im Vakuumgefäß (optimal 65 % Wasser, 30 % boriertes Stahlfüllmaterial, 5 % Stahlrippen) | ARIES-CS, Fluenzgrenze 1e19 n/cm² | El-Guebaly et al. 2005 [E1] | geprüft |
| Borcarbid (B4C) | keine belegten Abschwächungszahlen gefunden (nur Erwähnung als mögliche Rückschicht 5 cm) | – | – | **nicht gefunden** |

**Folgerung für unser Modell:** Belastbar als Obergrenzen sind (a) Fluenz 3e18 n/cm² (REBCO, konservativ) und (b) Kernheizung je nach Anspruch: 50 W/m³ (EU-DEMO) bis 2 kW/m³ (ARIES-CS-Stellarator, Nb3Sn); Gesamtwärme der Kaltmasse liegt bei 10–15 kW (ARC 14 kW, ARIES-CS ~12 kW). Wegen des Kühlaufwands bei 15–20 K ist die strenge DEMO-Grenze die sichere Seite. Für die Abschirmdicke gilt als Faustwert nur der Wolfram-Wert (Halbwertsdicke ≈ 4 cm, also Faktor 10 je ≈ 14 cm); für Stahl/Wasser müsste eine eigene Transportrechnung (OpenMC/MCNP) oder eine bessere Quelle folgen.

---

## 5. Radialer Aufbau und Wärmeflüsse

| Größe | Wert | Bedingung | Quelle | Status |
|---|---|---|---|---|
| ARIES-CS, Abstand Plasma – Spulenmitte (Δmin) | 130,7 cm im kritischen Bereich (verjüngtes Blanket 25 cm + WC-Schild); nominal Δ ≥ 179 cm (LiPb/He/FS) bzw. ≥ 137 cm (LiPb/SiC-Backup) | Δmin umfasst Randschicht (SOL), Erstwand, Blanket, Schild, Vakuumgefäß, Montagespalte, Spulengehäuse und halbes Wicklungspaket; R0 ≈ 7,75 m | El-Guebaly et al., UWFDM-1322 [E2] | ungeprüft (Bericht) |
| ARIES-CS Komponenten | Erstwand + Brutzone + Rückwand 63 cm (LiPb/He/FS) bzw. 50 cm (LiPb/SiC); Vakuumgefäß 28 cm; Schild 25 cm; Randschicht 5 cm; Divertor 20 cm; Spulengehäuse + Isolation einige cm | – | [E2] | ungeprüft |
| ARIES-CS Auslegung | je +10 cm Δmin: +60 cm Hauptradius; Auswahl Radialaufbau spart 20–90 cm | – | [E2], [E1] | [E1] geprüft (20–90 cm); [E2] ungeprüft |
| ARIES-CS Wärmeflüsse | Erstwand durch Strahlung max. 0,76 / mittel 0,57 MW/m²; Neutronenwandlast max. 5,3 / mittel 2,6 MW/m² (40 Vollleistungsjahre; Fusionsleistung 2355 MW) | 3D-Quellverteilung, 5 cm Randschicht | [E2] | ungeprüft |
| EU-DEMO Blanketraum | 80 cm innen, 130 cm außen für Brutmodule (Brutzone 30–50 cm HCPB; 50–80 cm HCLL/DCLL/WCLL) | Präsentation KIT | Suchauszug (kein Volltext) | ungeprüft; Gesamtaufbau Vakuumgefäß/Schild/TF **nicht gefunden** |
| HELIAS Mittelebene | Innenwand Vakuumgefäß 6 cm Stahl (SS-316), Vakuumgefäß-Schild 20 cm Stahl/Wasser (60/40), Außenwand 6 cm; Neutronenwandlast ca. 1,4 MW/m²; Gesamtdicke an kritischer Stelle ca. 103 cm; Master-Arbeit (Serpent2): Brutzone 50 cm + Blanketschild 42,5 cm hält schnellen Neutronenfluss < 1e9 cm⁻²s⁻¹ an allen Spulen | Häußler et al. (KIT/IPP) und Masterarbeit Univ. Jyväskylä 2023 | nur Suchauszüge | ungeprüft (Volltexte nicht gelesen) |
| ARC | Neutronenwandlast 2,5 MW/m² (Fusionsleistung 525 MW); Strahlungsheizfluss auf die innere Vakuumwand 0,2 MW/m² (30 % der Plasmaheizleistung); Vakuumgefäß nur ca. 5 cm dick, FLiBe-Immersionsblanket, TiH2-Schild (innen dicker) | Radialaufbau in Zahlen nicht aus dem Text entnommen | [S1] | geprüft (Aussagen im Volltext); Dicken innen/außen **nicht gefunden** |

**Folgerung für unser Modell:** Für einen Stellarator mit Kraftwerksanspruch sind 1,3–1,8 m Abstand Plasma bis Spulenmitte (ARIES-CS) die belegte Größenordnung; bei R0 = 10,4 m sind das ≈ 13–17 % von R0. Davon ist das Spulengehäuse samt halbem Wicklungspaket schon enthalten, der Rest (ca. 0,9–1,3 m) ist die Strecke für Erstwand + Blanket + Schild + Vakuumgefäß. Die Erstwandlast von ca. 0,6–0,8 MW/m² (Strahlung) ist als Wärmeeintrag in die Kühlkette brauchbar.

---

## Literaturliste

Geprüft = Crossref-Abfrage per DOI, Metadaten stimmen.

- [B1] C. Barth, G. Mondonico, C. Senatore: Electro-mechanical properties of REBCO coated conductors from various industrial manufacturers at 77 K, self-field and 4.2 K, 19 T. Supercond. Sci. Technol. 28, 045011 (2015). DOI 10.1088/0953-2048/28/4/045011. **geprüft**; Volltext über arXiv 1502.06713 gelesen.
- [C1] A. Čufar, A. Bruschi, M. Fischer, T. Franke u. a.: Equatorial electron cyclotron port plug neutronic analyses for the EU DEMO. Fusion Eng. Des. 146, 336–340 (2019). DOI 10.1016/j.fusengdes.2018.12.062. **geprüft**; Volltext über EUROfusion-Preprint WPPMI-CPR(18) 20070 gelesen (Grenzwerte in deren Tabelle 1).
- [E1] L. El-Guebaly, R. Raffray, S. Malang, J. Lyon u. a.: Benefits of Radial Build Minimization and Requirements Imposed on ARIES Compact Stellarator Design. Fusion Sci. Technol. 47(3), 432–439 (2005). DOI 10.13182/FST05-A725. **geprüft**; Volltext über UW-Bericht UWFDM-1233 gelesen.
- [E2] L. El-Guebaly, P. Wilson, D. Henderson, M. Sawan u. a.: Overview of ARIES-CS In-Vessel Components: Integration of Nuclear, Economic, and Safety Constraints in Compact Stellarator Design. Univ. Wisconsin Bericht UWFDM-1322, April 2007 (fti.neep.wisc.edu). Kein DOI/Crossref-Treffer gefunden. **ungeprüft**. Gedruckte Fassung vermutlich in Fusion Sci. Technol. 54 (2008); nicht verifiziert.
- [E3] L. A. El-Guebaly, M. E. Sawan: Shielding Considerations for ITER: Current Status and Future Directions. Univ. Wisconsin Bericht UWFDM-872, Dezember 1991. Kein DOI. **ungeprüft**.
- [F1] D. X. Fischer, M. Prokopec, M. Emhofer, M. Eisterer: The effect of fast neutron irradiation on the superconducting properties of REBCO coated conductors with and without artificial pinning centers. Supercond. Sci. Technol. 31, 044006 (2018). DOI 10.1088/1361-6668/aaadf2. **geprüft** (Metadaten); Volltext nicht gelesen, Zahlen nur über Suchauszug zur Dissertation (D. Fischer, TU Wien 2019, DOI 10.34726/hss.2019.27911 – Crossref kennt diesen DOI nicht, **ungeprüft**).
- [L1] A. Lee, V. Barabash, G. Kim, T. Schioler (ITER Org.): ITER's Experience – Codes & Standards for the Engineering of Tokamaks. Folien, IAEA Technical Meeting, 18.11.2025. Kein DOI. **ungeprüft** (Folien gelesen; Folie „Magnets: Examples of Specific SDCs“).
- [M1] N. Mitchell: Large Magnet Structures for Fusion Technology: Lessons from ITER. CERN Accelerator School Proceedings, Sint-Michielsgestel 2024; arXiv 2608.27230. Kein DOI geprüft. **ungeprüft**. Verweist u. a. auf C. T. J. Jong, N. Mitchell, J. Knaster, „ITER Magnet Design Criteria and their Impact on Manufacturing and Assembly“, 22nd IEEE SOFE 2007, DOI 10.1109/FUSION.2007.4337879 (Crossref: Metadaten stimmen – **geprüft** als Existenz; Inhalt/Sm-Definition nicht gelesen).
- [M2] N. Mitchell, D. Bessette, M. Ferrari, M. Huguet, C. Jong, Y. Takahashi, K. Yoshida u. a.: Design of the ITER Magnets to Provide Plasma Operational Flexibility. IAEA Fusion Energy Conference, Beitrag IT/1-4 (www-pub.iaea.org/mtcd/meetings/PDFplus/fusion-20-preprints/IT_1-4.pdf). Kein DOI, Jahr nicht verifiziert. **ungeprüft**.
- [P1] E. Pardo, A. Dadhich, N. Jerance, P. Fazilleau: Screening currents increase thermal quench propagation speed in ultra-high-field REBCO magnets. Results in Engineering 29, 108933 (2026). DOI 10.1016/j.rineng.2025.108933. **geprüft**; Fit-Formel im arXiv-Vorabdruck 2509.06621 (Anhang A) gelesen.
- [P2] C. Senatore, M. Bonura, T. Bagni: REBCO tapes for applications in ultra-high fields: critical current surface and scaling relations. Supercond. Sci. Technol. 37, 115013 (2024). DOI 10.1088/1361-6668/ad7f95. **geprüft** (Existenz/Metadaten); Originalfit nicht selbst gelesen, nur über [P1].
- [S1] B. N. Sorbom, J. Ball, T. R. Palmer, F. J. Mangiarotti u. a.: ARC: A compact, high-field, fusion nuclear science facility and demonstration power plant with demountable magnets. Fusion Eng. Des. 100, 378–405 (2015). DOI 10.1016/j.fusengdes.2015.07.008. **geprüft**; Volltext über arXiv 1409.3540 gelesen.
- [W1] C. G. Windsor, J. O. Astbury, J. Davidson, C. J. R. McFadzean u. a.: Tungsten boride shields in a spherical tokamak fusion power plant. Nucl. Fusion 61, 086018 (2021). DOI 10.1088/1741-4326/ac09ce. **geprüft**; Volltext über arXiv 2104.06886 gelesen. (Anmerkung: Der arXiv-Titel lautet „Tungsten boride shields in a spherical tokamak“; Crossref-Titel mit „fusion power plant“ – derselbe Beitrag.)

## Nicht belegt / offene Punkte

- Rp0,2 und Rm von 316LN, JK2LB, Nitronic 50 bei 4 K als zitierfähige Primärwerte (nur ITER-Mindestwerte und ARC-Wert 1050 MPa belegt).
- Quantitative ITER-Regel für Membran+Biegung (1,5 Sm) und Sm-Definition im Magnet-SDC (nur Folien; SDC selbst nur über ITER Organisation).
- Abschwächungslänge für Stahl/Wasser und für B4C.
- Kernheizungsgrenzen für SPARC; ITER-Endwerte (nur EDA-Werte von 1991).
- Vollständiger EU-DEMO-Radialaufbau (innen/außen) und ARC-Dicken; HELIAS-Spulenabstand.
- Dehnungs-/Temperaturabhängigkeit für das konkrete Band (Herstellerdaten).
