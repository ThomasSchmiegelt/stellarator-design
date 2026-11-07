# Machbarkeit: Von „unserem besten Plasma“ zu eigenen Spulen (2026-11-07)

*English summary at the end.* Ereignisprotokoll F-257 bis F-260, Befund B-058. Nur Recherche und kleine Auswertungen, keine neue VMEC++-Rechnung, nichts installiert.

Kennzeichnung: **belegt** = aus Paketcode, Ergebnisdateien oder gelesener Quelle; **Folgerung** = meine Deutung; **offen / nicht geprüft** = nicht nachgesehen oder nicht gerechnet.

## 0 Worum geht es? (für Nicht-Physiker)

Der Nutzer will einen durchgehenden Prozess:

1. **Bestes Plasma festlegen** – eine Plasmaform (Randfläche) mit sehr kleinem QI.
2. **Spulen dafür finden** – das *Rückwärtsproblem*: Wir kennen die gewünschte Form des Magnetfelds am Plasmarand und suchen Leiterschleifen (Spulen), deren Feld genau diese Form hat. Vergleich aus dem Maschinenbau: Man kennt das Bauteil und sucht die Gussform; die Form ist nicht eindeutig, und manche Bauteile lassen sich gar nicht gießen.
3. **Freie Grenze rechnen** – VMEC++ bekommt nur noch die Spulen und sucht selbst, wo das Plasma sich einstellt (*free-boundary*). Vorher (*fixed-boundary*) war die Randform vorgegeben.
4. **Verlustfaktor messen** – QI(mit Spulen, freie Grenze) / QI(Plasma, feste Grenze). Faktor 1 = die Spulen treffen das Wunschfeld perfekt.
5. Danach Tragwerk und Kühlung mit diesem Spulensatz.

Begriffe:
- **QI (quasi-isodynamisch)**: Maß dafür, wie gut schnelle Teilchen im Feld eingeschlossen bleiben; kleiner ist besser. Kennzahl = Restfehler am Plasmarand.
- **Stage 1 / Stage 2**: In der Fachwelt wird zuerst die Plasmaform optimiert (Stage 1), dann die Spulen dazu (Stage 2). Stage 2 minimiert den **Feldfehler B·n/|B|**: den Anteil des Feldes, der *durch* die gewünschte Randfläche hindurchstößt (soll null sein, das Feld soll an der Fläche entlang laufen).
- **REGCOIL**: schnelles Verfahren, das zuerst einen kontinuierlichen Strombelag auf einer Hüllfläche um das Plasma berechnet (wie ein „verschmierter“ Spulenmantel) und daraus Spulen schneidet. Liefert gute Startspulen.
- **L_∇B (kleinste normierte Gradientenlänge des Feldes)**: auf welcher Strecke sich das Feld am Rand am schnellsten ändert, in Einheiten des kleinen Plasmaradius a. Kleiner Wert = sehr „feine“ Feldstruktur = Spulen müssen nah ans Plasma.
- **iota**: Verdrillung der Feldlinien; **Spiegelverhältnis**: Schwankung der Feldstärke entlang einer Feldlinie; **Vakuummulde**: Maß für MHD-Stabilität (≥ 0 gut); **Elongation**: wie stark der Querschnitt gestreckt ist; **A**: Aspektverhältnis (großer/kleiner Radius); **nfp**: Zahl der gleichen Abschnitte (Feldperioden) im Ring.

## 1 Werkzeuge

### 1.1 Was ist im Projekt schon installiert (belegt, Import-Test 2026-11-07)

| Umgebung | Paket | Version | Import | Rolle im Rückwärtsproblem |
|---|---|---|---|---|
| `.venv-opt` (Python 3.12) | simsopt | 1.11.1 | ok | Stage 2 mit Einzelspulen (CurveXYZFourier, BiotSavart, SquaredFlux, Abstands-/Krümmungsstrafen, LpCurveForce) |
| `.venv-opt` | DESC (desc-opt) | 0.17.3 | ok | enthält `solve_regularized_surface_current` (Docstring: „Runs REGCOIL-like algorithm“) und `FourierCurrentPotentialField.to_CoilSet` (Spulen aus dem Strombelag schneiden), Spulenziele in `desc/objectives/_coils.py` |
| `.venv-opt` | booz_xform | 0.1.0 | – | Boozer-Koordinaten |
| `.venv-opt` | vmecpp | – | **fehlt** | – |
| `.venv-constellaration` (Python 3.10) | vmecpp | 0.4.11 | ok | freie Grenze (schon genutzt in `stellarator/qi_spulen.py`) |
| `.venv-constellaration` | constellaration | 0.2.6 | – | Kennzahlen, QI, Aufgaben |
| `.venv-constellaration` | simsopt | 1.8.1 | ok | Feldtabellen für die freie Grenze |
| `.venv-constellaration` | DESC | 0.17.1 | **Import scheitert** (`jax.tree_util.tree_broadcast` fehlt, jax 0.5.3 zu alt) | nicht nutzbar |
| `.venv` | – | – | – | nur numpy/scipy/netCDF4 |

Nicht vorhanden (belegt durch Paketliste): eigenständiges REGCOIL, FOCUS. Das pip-Paket simsopt 1.11.1 hat **kein** Strombelag-Modul (`simsopt.field.currentpotential` nicht vorhanden). Folgerung: **Es muss nichts installiert werden.** Der Austausch zwischen den Umgebungen läuft über JSON-Dateien (Spulen als Fourier-Koeffizienten), wie schon in `invers/stufe2_spulen.py` und `stellarator/proxima_spulen.py`.

### 1.2 Was das Projekt damit schon gemacht hat (belegt, Projektdateien)

| Versuch | Werkzeug | Form | Ergebnis |
|---|---|---|---|
| `invers/stufe2_spulen.py`, Fälle `sim/invers/qa_*` | simsopt Stage 2, Start runde Ringe | QA-Plasma nfp 2 | Feldfehler mittel 0,0011 bis 0,0027, Laufzeit 79 bis 213 s – **funktioniert** |
| dasselbe, Fälle `sim/invers/qi_o3_n4 … qi_pruef_d07` | dasselbe | QI-Rand nfp 3 | Feldfehler mittel 0,025 bis 0,18, max. bis 1,0, Spulen fallen ans Plasma – **gescheitert** (B-028). Damals vermutete Ursache: Start mit runden Ringen statt REGCOIL-Strombelag |
| `stellarator/zwei_ringe.py`, Fall A085 (`sim/qi_zwei_ringe/`) | simsopt Stage 2, Start = Randlinie um d nach außen versetzt, Ordnung 7, 5 Spulen je halbe Periode | DjLe3eL6 (QI, nfp 4) | Feldfehler mittel **6,6·10⁻⁴**, max. 5,7·10⁻³, Abstand 0,85 a, Biegeradius ≥ 0,50 a, Spule–Spule ≥ 0,30 a; **587 s**; nicht auskonvergiert (Iterationsgrenze 2000). Proxima-Satz derselben Form zum Vergleich: 2,41·10⁻³ |
| `stellarator/qi_spulen.py` (`sim/qi_spulen/faelle/`) | VMEC++ free-boundary mit Proxima-Spulen | DjLe3eL6 | QI fest 0,000448, frei 0,000579 (3000 Schritte) bzw. 0,000671 (12000) → Verlustfaktor **1,29 bis 1,50**, Rand nicht selbstkonvergent (B-053). Laufzeit 130 bis 410 s je Fall |

**Folgerung:** Das fehlende Glied ist zu großen Teilen schon gebaut: Stage 2 für eine QI-Form funktioniert mit dem besseren Start aus `zwei_ringe.py`, und die freie Grenze mit Spulen gibt es in `qi_spulen.py`. Es fehlt (a) ein Lauf für eine *andere* Form als DjLe3eL6, (b) eine Brücke: `qi_spulen.py` liest fest den Ordner `sim/constellaration/qi/proxima_spulen_dje` (Proxima-Format `coilset.json`), eigene Spulen liegen als simsopt-`biot_savart.json` vor. Das ist ein kleiner Umbau (Quellordner als Argument, Leser für simsopt-JSON), **nicht geprüft**, wie viel Aufwand genau.

### 1.3 Werkzeuge außerhalb (Quellen gelesen)

| Werkzeug | Was | Lizenz / Quelle | Stand |
|---|---|---|---|
| simsopt | Stage 2 mit Einzelspulen | MIT (Paket-Metadaten), github.com/hiddenSymmetries/simsopt | installiert |
| DESC | Gleichgewicht, REGCOIL-artiger Strombelag, Spulen-Optimierung | MIT (Paket-Metadaten), github.com/PlasmaControl/DESC | installiert (`.venv-opt`) |
| VMEC++ | Gleichgewicht, freie Grenze | MIT (Paket-Metadaten), github.com/proximafusion/vmecpp | installiert |
| ConStellaration | Datensatz + Kennzahlen | Paket MIT; arXiv:2506.19583 (NeurIPS 2025 Datasets & Benchmarks) | installiert |
| CoilStellaration (Hugging Face proxima-fusion/coilstellaration) | Proxima-Spulensätze zu ConStellaration-Rändern; Spaltennamen zeigen **REGCOIL → DESC** als Verfahren; Anforderungen z. B. Spule–Plasma 0,5 bis 1 (normiert), 4 bis 8 Spulen je halbe Periode, Fourier-Ordnung 7 | MIT (Datensatzseite) | lokal nur Eval-Teil der Ergebnisse + Spulendateien |
| REGCOIL | Strombelag-Verfahren, Landreman, Nucl. Fusion 57, 046003 (2017), arXiv:1609.04378 | Lizenz **nicht geprüft** | nicht installiert; in DESC nachgebaut |
| FOCUS | Spulen als freie Raumkurven ohne Hüllfläche, Zhu et al., Nucl. Fusion 58, 016008 | Lizenz **nicht geprüft**; Fortran | nicht installiert, nicht nötig |
| L_∇B als Abstandsmaß | Kappel, Landreman, Malhotra, arXiv:2309.11342 (PPCF 66, 025018, 2024): L_∇B korreliert mit dem Spule–Plasma-Abstand (REGCOIL, ~40 Konfigurationen). Kappel et al. arXiv:2602.18974 (2026): gilt auch für Einzelspulen, „wenn genug Spulenlänge erlaubt ist“ | Paper gelesen (Zusammenfassung) | Kennzahl ist im Datensatz |
| Geodätische Torsion als Maß für Spulenverbiegung | Pavone, Kwak, Warmer, arXiv:2604.26763 (2026): sagt die Unebenheit der Spulen aus dem Gleichgewicht voraus | Paper (CC BY 4.0), Datensatz/Code laut Seite nicht genannt | nicht im Projekt |

Belegt aus dem Paketcode: `constellaration/problems.py` bewertet in Aufgabe 2 „easier to realize with coils“ über L_∇B; `constellaration/mhd/magnetics_utils.py` normiert L_∇B mit dem kleinen Radius (`Aminor_p`) und verweist auf arXiv:2309.11342.

### 1.4 Empfohlene Werkzeugkette (Folgerung)

1. **Start**: simsopt Stage 2 wie `zwei_ringe.py` (Start an der versetzten Randlinie, Ordnung 7, Strafen für Abstand, Biegeradius, Spule–Spule). Erprobt, ohne neue Software.
   Ausweichweg bei Scheitern: REGCOIL-Start mit DESC (`solve_regularized_surface_current` → `to_CoilSet`), dann Stage 2. Das ist Proximas Weg, im Projekt **noch nie ausgeführt**.
2. **Freie Grenze**: `qi_spulen.py` verallgemeinert (Quellordner, eigene Spulen), Feldtabelle mit nzeta 48, Kalibrierung über den Toroidalfluss.
3. **Verlustfaktor**: QI frei/fest am Rand **und** bei s = 0,5 (der Rand ist bei frei nicht selbstkonvergent, B-053), dazu Randabweichung in a, iota, Spiegelverhältnis.

## 2 Welche Form ist „unser bestes Plasma“?

### 2.1 Vorgeschlagene Kriterien

Reihenfolge nach der Nutzerregel „Plasma zuerst“: QI wählt, die anderen schließen nur Unrealistisches aus.

| Kriterium | Wozu | Vorschlag |
|---|---|---|
| QI am Rand (und Profil innen) | Einschluss | Hauptmaß; Rand ist bei 3 von 4 Formen die schlechteste Fläche (B-052) |
| L_∇B | Spulenabstand (Kappel 2023/2026) | als Ausschluss: nicht unter ~0,25-Quantil des Datensatzes; Vergleich: DjLe3eL6 7,05 (Spulen von Proxima vorhanden) |
| Elongation | Spulen und Gehäuse | Hinweis, kein Ausschluss |
| iota/nfp, Spiegelverhältnis, Vakuummulde | Aufgaben 2/3 der Challenge | nur melden; erfüllt derzeit keine gute Form (B-051) |
| A | Baugröße | melden |
| Komplexität K | Anteil hoher Fourier-Moden | eigenes Maß, siehe unten |
| Mindestabstand Plasma–Spule | Abschirmung (1,3 m ≈ 0,72 a bei a = 1,80 m, `zwei_ringe.md`) | erst nach Stage 2 messbar; vorher nur über L_∇B abschätzbar |

**Komplexität K** (eigene Definition, nicht aus der Literatur): Wurzel der Quadratsumme aller Koeffizienten r_cos, z_sin mit m ≥ 2 oder |n| ≥ 2, geteilt durch die Grundauslenkung √(r_cos[1,0]² + z_sin[1,0]²). Groß = viele feine Wellen in der Fläche. Ob K mit dem Spulenaufwand zusammenhängt, ist **nicht geprüft**.

### 2.2 Erwartung vorher (F-258) und Ergebnis

Erwartung: Platz 1 bis 10 eigene Proben um Do3Qy/K3 halb, alle nfp 2, Spiegel > 0,3, iota/nfp < 0,15, L_∇B unter dem Datensatz-Median, Elongation über 6. **Alles getroffen** (Tabellen unten).

Datengrundlage (belegt): 182 222 Zeilen, 158 685 mit QI; Median L_∇B 4,97, Median Elongation 4,78; QI-Grenze der besten 0,1 %: 0,000336; dazu 284 rechenbare eigene Formproben aus `alle_proben.csv`. Skript: Auswertung im Scope, Ergebnisdatei `rangliste.json` (dieser Ordner).

### 2.3 Die zehn besten Formen nach QI (Datensatz + eigene Proben)

Alle nfp 2. L_∇B-Rang = Anteil der Datensatzformen mit kleinerem L_∇B.

| # | Form | QI | A | Elong. | iota/nfp | Spiegel | Mulde | L_∇B (Rang) | K |
|---|---|---|---|---|---|---|---|---|---|
| 1 | k3_vernunft_56 (K3 halb, A ×1,05 mit nachgeführter Achse, 0,34 sd) | 3,66e-5 | 7,76 | 7,15 | 0,090 | 0,447 | −0,018 | 4,26 (0,39) | 0,36 |
| 2 | k3_vernunft_34 (Koeffizient, 0,1 sd) | 3,71e-5 | 7,52 | 7,23 | 0,093 | 0,462 | −0,020 | 4,10 (0,36) | 0,36 |
| 3 | k3_vernunft_32 (0,2 sd) | 3,80e-5 | 7,66 | 7,36 | 0,099 | 0,478 | −0,018 | 4,22 (0,38) | 0,36 |
| 4 | do3_vernunft_32 (0,2 sd) | 4,10e-5 | 7,69 | 7,36 | 0,099 | 0,433 | −0,017 | 4,28 (0,39) | 0,37 |
| 5 | do3_vernunft_34 (0,1 sd) | 4,20e-5 | 7,56 | 7,27 | 0,094 | 0,418 | −0,018 | 4,15 (0,37) | 0,36 |
| 6 | k3_vernunft_40 | 4,49e-5 | 7,39 | 7,16 | 0,088 | 0,448 | −0,021 | 3,90 (0,34) | 0,35 |
| 7 | k3_vernunft_51 | 4,53e-5 | 7,37 | 7,31 | 0,081 | 0,471 | −0,022 | 3,91 (0,34) | 0,35 |
| 8 | k3_vernunft_28 | 4,58e-5 | 7,46 | 7,56 | 0,095 | 0,472 | −0,019 | 4,01 (0,35) | 0,35 |
| 9 | k3_vernunft_38 | 4,59e-5 | 7,39 | 7,17 | 0,088 | 0,450 | −0,020 | 3,83 (0,33) | 0,35 |
| 10 | k3_vernunft_03 (gleich wie _104, doppelte Probe) | 4,60e-5 | 7,39 | 7,41 | 0,092 | 0,437 | −0,019 | 4,01 (0,35) | 0,35 |
| Bezug | K3 halb (Basis, B-050) | 4,72e-5 | 7,39 | 7,15 | 0,088 | 0,45 | – | – | – |
| Bezug | Do3Qy (bester Datensatz) | 6,15e-5 | 7,43 | 7,20 | 0,089 | 0,405 | −0,020 | 4,02 (0,35) | 0,35 |

Belegt: Alle zehn sind kleine Abwandlungen derselben Familie (Do3Qy → K3 halb), jede nur **einmal** mit VMEC++ gerechnet (Experimentmatrix). Folgerung: Für die Spulenfrage sind das praktisch *eine* Form; die Unterschiede in QI (bis −23 % gegen K3 halb) sind kleiner als der zu erwartende Spulenverlust (DjLe3eL6: +29 bis +50 %).

Nebenbefund (eine Probe, Folgerung): Platz 1 ist „Aspektverhältnis mit nachgeführter Achswelle ×1,05“. B-055 hatte gezeigt, dass *nur* R00 zu ändern QI verschlechtert; mit mitgeführter Achse wird es hier besser (−23 %). Das betrifft die offene Frage „nachgeführtes Rohr“ und sollte mit einer zweiten Rechnung bestätigt werden.

### 2.4 Die zehn besten Datensatzformen

| # | Form (plasma_config_id) | nfp | QI | A | Elong. | iota/nfp | Spiegel | Mulde | L_∇B | K |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Do3QyJbtRhtGhrTiBSBbyKM | 2 | 6,15e-5 | 7,43 | 7,20 | 0,089 | 0,405 | −0,020 | 4,02 | 0,35 |
| 2 | DfnbHvbgKNafhttMEbNvR5k | 2 | 6,67e-5 | 7,66 | 5,54 | 0,077 | 0,329 | −0,015 | 4,64 | 0,29 |
| 3 | D86W4GogPeqZgB6p6dfToQR | 2 | 8,09e-5 | 8,05 | 7,04 | 0,113 | 0,385 | −0,028 | 4,37 | 0,28 |
| 4 | DC6MmpQ95cPyHAHaGnQxWme | 2 | 8,25e-5 | 7,66 | 7,26 | 0,096 | 0,412 | −0,028 | 3,88 | 0,40 |
| 5 | D42HzX6zW4BR6VH6YD5u7Pf | 2 | 8,36e-5 | 7,65 | 6,97 | 0,081 | 0,396 | −0,033 | 4,02 | 0,41 |
| 6 | DC7XrN75xZCVwJKpNhox2RB | 2 | 8,64e-5 | 7,11 | 7,89 | 0,094 | 0,404 | −0,018 | 2,02 | 0,32 |
| 7 | D4nHExBzc2ZRLjt6wzZdQWG | 2 | 9,19e-5 | 7,99 | 7,18 | 0,109 | 0,379 | −0,028 | 3,92 | 0,30 |
| 8 | D4Ag3bsDsZhfzAFZJLMKG9a | 2 | 9,77e-5 | 7,77 | 5,08 | 0,084 | 0,410 | −0,055 | 4,62 | 0,37 |
| 9 | D4ke3ng2xsoB7n6uDqN7N5W | 2 | 9,83e-5 | 7,55 | 7,25 | 0,134 | 0,409 | −0,020 | 3,36 | 0,32 |
| 10 | DDWJg4NBD6KwNGM8KNLJrys | 2 | 1,20e-4 | 8,19 | 7,47 | 0,091 | 0,409 | −0,035 | 4,28 | 0,36 |

Auffällig (belegt): DfnbHvbg… (Platz 2) hat fast gleiches QI wie Do3Qy, aber Elongation 5,54 statt 7,20, Spiegel 0,329 und kleinste Komplexität (0,29) – die „gutmütigere“ nfp-2-Form. DC7XrN75… hat L_∇B 2,02 (Rang 0,08), also vermutlich sehr nahe Spulen.

### 2.5 Kompromiss: QI unter den besten 0,1 %, größtes L_∇B

276 Formen haben QI ≤ 0,000336. Nach L_∇B sortiert (belegt):

| # | Form | nfp | QI | A | Elong. | iota/nfp | Spiegel | Mulde | L_∇B | K |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DATJ5FCamJ3dNpdKmj8QsfL | 4 | 2,81e-4 | 9,05 | 5,74 | 0,133 | 0,289 | −0,037 | 7,14 | 0,24 |
| 2 | DnnFSXEHK6pz5tjXNvz7Nub | 3 | 3,33e-4 | 8,72 | 6,38 | 0,213 | 0,385 | −0,105 | 7,00 | 0,24 |
| 3 | Dm3arSuB7sKt7VegxQZsTAb | 3 | 2,70e-4 | 8,81 | 6,16 | 0,215 | 0,372 | −0,106 | 6,84 | 0,24 |
| 4 | DcpiqqeesoWqJduc4dLzJKy | 3 | 2,44e-4 | 8,49 | 6,82 | 0,216 | 0,412 | −0,109 | 6,68 | 0,24 |
| 5 | DMePmcHKzPzDkcT74jSsiAp | 3 | 3,15e-4 | 8,63 | 6,82 | 0,231 | 0,406 | −0,115 | 6,24 | 0,24 |
| 6 | DGAnUUjfX8pjwjqrNLhHhL4 | 3 | 2,89e-4 | 8,94 | 6,15 | 0,227 | 0,345 | −0,112 | 6,20 | 0,22 |
| 7 | DBJ94qANiHy2auYM2kF5zTK | 3 | 2,28e-4 | 8,60 | 6,67 | 0,233 | 0,407 | −0,125 | 5,99 | 0,28 |
| 8 | DTFHoeHPS5qztv6bKziQrDR | 4 | 3,03e-4 | 8,52 | 5,90 | 0,169 | 0,403 | −0,042 | 5,97 | 0,23 |
| 9 | DNumb98e4jTT49n3bKqVaW5 | 4 | 3,33e-4 | 8,28 | 5,35 | 0,106 | 0,424 | −0,079 | 5,97 | 0,28 |
| 10 | DRtaTSkgyTFkfMkg5FhLSh8 | 2 | 2,42e-4 | 8,96 | 6,02 | 0,111 | 0,395 | −0,118 | 5,94 | 0,37 |
| Bezug | DjLe3eL6 (Proxima-Spulen vorhanden) | 4 | 4,48e-4 | – | 6,50 | – | – | – | 7,05 | – |

Folgerung: DATJ5FC… ist das „DjLe3eL6 mit besserem QI“: gleiches nfp, gleiches L_∇B, 37 % kleineres QI, kleinere Elongation. Die nfp-3-Formen haben iota/nfp 0,21 bis 0,23, nahe an der Grenze 0,25 der Aufgaben, aber Vakuummulde −0,1 (verletzt).

**Fertige Proxima-Spulen für diese Kandidaten?** (Erwartung F-259: 0 bis 2 Treffer.) In der lokalen Eval-Teilmenge von CoilStellaration (13 299 Zeilen, 711 Ränder) ist **keiner** der Kandidaten (Do3Qy, D8ZNt2, die zehn besten, die zehn Kompromissformen). Getroffen. Die Trainings-Ergebnistabelle (253 000 Zeilen laut Datensatzseite) liegt nicht lokal; ob dort Spulen für Do3Qy oder DATJ5FC… stehen, ist **nicht geprüft** (Download nötig, Größe nicht geprüft, Platte fast voll → zweite Platte).

### 2.6 Empfehlung „unser bestes Plasma“ (Folgerung)

- **Für die Kette: K3 halb** (`sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json`, Gleichgewicht `sim/qi_flaeche/karte3d/wout_k3.nc`). Gründe: eigene Form, mehrfach mit VMEC++ bestätigt (Prüfstein 4,718e-5 in der Matrix), bestes QI auf fast allen Flächen (B-052), QI-Profil bekannt. Die besseren Proben (Platz 1 bis 3) sind nur einmal gerechnet; erst bestätigen, dann tauschen.
- **Als Gegenprobe zuerst eine leichte Form**: Die K3-Familie hat L_∇B ≈ 4 (Rang 0,35) und Elongation 7,2; nach Kappel et al. heißt das nähere Spulen als bei DjLe3eL6 (L_∇B 7,05). Die Projektgeschichte zeigt: Stage 2 für schwierige QI-Formen ist schon einmal gescheitert (B-028). Darum Empfehlung: **Schritt 0** = eigene A085-Spulen von DjLe3eL6 durch die freie Grenze (Kettenprüfung, die Spulen liegen schon vor), dann K3 halb.
- **Plan B** bei Scheitern von K3 halb: DATJ5FCamJ3… (nfp 4, L_∇B 7,14, Elongation 5,74) – gleiche Spulenbedingungen wie DjLe3eL6, für die Stage 2 nachweislich geht.

## 3 Aufwand für einen ersten Spulentest an einer Form

Hardware: 32 GB RAM, kein GPU nötig (simsopt und VMEC++ laufen auf CPU; DESC mit `JAX_PLATFORMS=cpu`).

| Schritt | Grundlage der Zeitangabe | Rechenzeit | Arbeitszeit (Code) |
|---|---|---|---|
| 0 Kettenprüfung: A085-Spulen (DjLe3eL6) → freie Grenze | Tabelle + 2 VMEC++-Läufe zu 130–410 s (gemessen, B-053) | ~0,5 h | Brücke simsopt-JSON → `qi_spulen.py`: 1–3 h (Schätzung) |
| 1 Stage 2 für K3 halb, kleine Reihe (Abstand 0,7/0,85/1,0 a × 4/5/6 Spulen je halbe Periode = 9 Läufe) | zwei_ringe: 587–1630 s je Lauf (gemessen) | 2–4 h bei 2 parallel (Scope 12 GB wie zwei_ringe) | Startform aus wout_k3: < 1 h |
| 2 Feldtabelle + freie Grenze für die 1–2 besten Sätze, Selbstkonvergenz (3000/12000 Schritte) | 130–410 s je Lauf (gemessen); Tabellenzeit **nicht gemessen** | 1–2 h | – |
| 3 Auswertung Verlustfaktor, QI-Profil, Bilder | wie qi_karte | < 0,5 h | 1 h |
| Ausweichweg REGCOIL-Start (DESC) | **nicht geprüft** | unbekannt (Literatur: „schnell“) | 0,5–1 Tag Einarbeitung |

**Summe (Folgerung):** etwa **4 bis 7 Stunden Rechenzeit** und **ein bis zwei Arbeitstage** insgesamt, ohne REGCOIL. Speicher: VMEC++ bisher 2,8 GB je Lauf (ERINNERUNGEN 2026-11-04), Stage 2 im 12-GB-Scope; höchstens 2 parallel. Alles pausierbar über das Pause-Werkzeug `rechnung` (Scope).

### 3.1 Abbruchkriterien (Vorschlag)

Vorher festlegen, dann nicht nachträglich verschieben:

1. **Stage 2 (Spulen gut genug?)**: Feldfehler mittel ≤ 1·10⁻³ (A085 erreichte 6,6·10⁻⁴; Proxima-Satz DjLe3eL6 2,4·10⁻³; Projektgrenze B-028: 3·10⁻³), Spule–Plasma ≥ 0,72 a (≈ 1,3 m Abschirmung bei a = 1,80 m), Biegeradius ≥ 0,5 a, Spule–Spule ≥ 0,3 a.
   **Abbruch**, wenn nach 2 Runden à 2000 Schritten in allen 9 Läufen der Feldfehler mittel > 3·10⁻³ bleibt oder der Abstand nur unter 0,72 a erreicht wird → K3 halb gilt als „mit Einzelspulen dieses Typs nicht baubar“; weiter mit REGCOIL-Start oder Plan B.
2. **Freie Grenze**: höchstens 2 Einstellungsvarianten (nzeta 48; Schrittzahl 3000/12000). **Abbruch**, wenn beide nicht konvergieren (Fehlerbild B-057) – dann Halbierungsmethode auf der Strecke „Spulenfeld → Sollfeld“ statt weiterer Varianten.
3. **Verlustfaktor**: < 1,5 gut, 1,5 bis 3 brauchbar (Stromtrimmung S-Gruppen wie B-053/B-054 versuchen), > 3 → **Ergebnis melden, nicht weiter optimieren**: dann ist „QI des Plasmas“ als Auswahlmaß für diese Form wertlos und Plasma und Spulen müssen gemeinsam optimiert werden (Single-Stage, großer Schritt, eigene Entscheidung).
4. **Zeit**: höchstens 1 Tag Rechenzeit für Schritt 1 bis 3.

## 4 Was wir nicht wissen, was scheitern kann (ehrlich)

1. **Stage 2 für die K3-Familie kann scheitern.** Belegt: Der erste QI-Versuch (nfp 3) scheiterte (Feldfehler bis 0,18). Belegt: Der verbesserte Start klappte bei DjLe3eL6 (L_∇B 7,05). K3 halb hat L_∇B ≈ 4 und Elongation 7,2 – nach Kappel et al. braucht so ein Feld nähere Spulen. Ob 0,72 a erreichbar ist, ist offen.
2. **Die freie Grenze ist unser schwächstes Glied.** Belegt: Auch bei DjLe3eL6 ist der Randwert nicht selbstkonvergent (0,000579 vs. 0,000671), Basis-Neurechnung mit anderen Einstellungen nicht konvergent, und schon 1,2 % Stromänderung brachte Abbrüche (B-057). Folgerung: Der Verlustfaktor ist derzeit auf etwa ±15 % unsicher; bei einer neuen Form vielleicht gar nicht messbar.
3. **Verlustfaktor bei sehr guten Formen.** Folgerung: Der Spulenfehler (Welligkeit zwischen Einzelspulen) ist ein Absolutbetrag. Bei QI 4,7e-5 kann derselbe Absolutfehler einen viel größeren *Faktor* ergeben als bei DjLe3eL6 (4,5e-4). Der Strom-„Boden“ bei etwa 3·10⁻⁴ (qi_experiment_bericht.md, Weg ii) deutet an, dass Spulen QI nicht beliebig klein machen; ob das für andere Formen gilt, ist offen. Möglicher Ausgang: Mit Spulen sind K3 halb und DATJ5FC… gleich gut.
4. **Inseln und Rand.** Belegt bei DjLe3eL6: Inselketten 4/9, 8/19 und stochastischer Saum. Für K3 halb (iota am Rand ≈ 2 × 0,088 = 0,18) ist nicht geprüft, welche rationalen Flächen nahe liegen.
5. **Die Rangliste ist QI-zentriert und keine Form erfüllt Aufgabe 2/3** (B-051). „Bestes Plasma“ heißt also „bestes QI“, nicht „zulässig“. Das Spiegelverhältnis 0,45 und iota 0,09 bleiben verletzt.
6. **Eigene Proben einmal gerechnet.** Platz 1 bis 10 sind Einzelrechnungen; Platz 1 ist mit 0,34 sd am weitesten weg.
7. **DESC/REGCOIL im Projekt ungeprüft.** Import geht nur in `.venv-opt`, in `.venv-constellaration` scheitert DESC. Ob `solve_regularized_surface_current` mit unseren Rändern läuft, wie lange und mit wie viel Speicher: nicht geprüft.
8. **Maßstab.** Stage 2 rechnet in Datensatzeinheiten (R ≈ 1); Kräfte und Spannungen gelten erst nach Skalierung (Stufe 3, Faktor 17,16 m in `qi_spulen.py`). Abstand in a ist maßstabsfrei, Kraft nicht (B-041/Nebenbefund `zwei_ringe.md`).
9. **β = 0 (Vakuum).** Ob die Datensatz-QI und unsere Rechnungen bei Plasmadruck null gelten und wie sich das bei Betrieb ändert, habe ich hier nicht nachgesehen (nicht geprüft).
10. **Komplexitätsmaß K** ist eine eigene, ungeprüfte Definition.

## 5 Kurzfassung der Empfehlung

- **Werkzeug:** simsopt Stage 2 (Ansatz `stellarator/zwei_ringe.py`, `.venv-opt`) + VMEC++ free-boundary (`stellarator/qi_spulen.py`, verallgemeinert, `.venv-constellaration`); Ausweichweg REGCOIL-Start mit DESC. Keine Installation.
- **Form:** K3 halb als „unser bestes Plasma“; vorher Kettenprüfung mit den vorhandenen A085-Spulen (DjLe3eL6); Plan B DATJ5FCamJ3… (nfp 4, L_∇B 7,14).
- **Aufwand:** 4 bis 7 h Rechenzeit, 1 bis 2 Arbeitstage.
- **Größtes Risiko:** freie Grenze konvergiert nicht verlässlich; K3 halb braucht vermutlich nahe Spulen.

## English summary

**Question.** Can we close the missing link “plasma shape → coil shape” (inverse problem, *stage 2*) so that the chain best plasma → coils → VMEC++ free boundary → loss factor QI(coils)/QI(plasma) → structure/cooling becomes continuous?

**Tools (verified in the installed packages).** simsopt 1.11.1 and DESC 0.17.3 (with a REGCOIL-like surface-current solver and coil cutting) in `.venv-opt`; VMEC++ 0.4.11 and simsopt 1.8.1 in `.venv-constellaration` (DESC import fails there). No standalone REGCOIL or FOCUS; nothing needs installing. Licences: simsopt, DESC, VMEC++, constellaration, CoilStellaration MIT; REGCOIL/FOCUS licences not checked. The project already has (a) a stage-2 script that failed for a QI shape when started from circular coils (B-028) and (b) an improved stage-2 start (`zwei_ringe.py`) that reached a mean normal-field error of 6.6e-4 for DjLe3eL6 in 587 s, plus (c) a free-boundary tool with a measured loss factor of 1.29–1.50 for DjLe3eL6 with Proxima's coils.

**Best plasma.** Top 10 by QI (dataset of 158 685 shapes plus 284 own probes) are all small variations of the Do3Qy/K3-half family (nfp 2, QI 3.7e-5 to 4.6e-5, elongation ~7.2, mirror ratio ~0.45, iota/nfp ~0.09, L_∇B ~4, i.e. below the dataset median 4.97 → coils likely close to the plasma). A compromise list (QI in the best 0.1 %, largest L_∇B) is led by DATJ5FCamJ3… (nfp 4, QI 2.8e-4, L_∇B 7.14), comparable to DjLe3eL6 for which coils exist. None of the candidates has a Proxima coil set in the local CoilStellaration eval subset. Recommendation: K3 half as “our best plasma”, preceded by a chain check with existing own coils for DjLe3eL6; DATJ5FC… as fallback.

**Effort.** About 4–7 h CPU time and 1–2 working days, no GPU, ≤ 2 parallel jobs within memory scopes. Stop criteria: stage 2 mean field error ≤ 1e-3 at coil–plasma distance ≥ 0.72 a (abort if > 3e-3 after 2 rounds in all 9 runs); free boundary at most 2 setting variants; loss factor > 3 → report and stop.

**Risks.** Free-boundary convergence is the weakest link (B-057); stage 2 may fail for the elongated nfp-2 shape; for very good shapes the coil ripple may dominate QI; top probes are single runs; no shape meets the challenge constraints; DESC/REGCOIL untested in the project.

Sources: Kappel, Landreman, Malhotra, arXiv:2309.11342; Kappel et al., arXiv:2602.18974; Landreman, Nucl. Fusion 57 046003 (arXiv:1609.04378); Zhu et al., Nucl. Fusion 58 016008; Pavone, Kwak, Warmer, arXiv:2604.26763; ConStellaration arXiv:2506.19583; Hugging Face dataset proxima-fusion/coilstellaration.
