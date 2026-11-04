# Gegenrechnung der Surrogat-Kandidaten mit VMEC++ (Opus-Agent, 2026-11-04)

Auftrag (F-238): Gibt es eine **eigene** Plasmaform, also eine im Surrogat gefundene, mit dem echten Rechner VMEC++ bestätigte Form, die im ConStellaration-Datensatz nicht vorkommt? Nichts hochgeladen, nichts gesendet, nichts committet.

Skript: `stellarator/qi_gegenrechnung.py` (Suche, Einzelrechnung, Auswertung), Lauf: `sim/qi_flaeche/lauf_gegenrechnung.sh`, Linienprüfung: `sim/qi_flaeche/gegenrechnung_klein/linie.py`. Ergebnisse je Form: `sim/qi_flaeche/gegenrechnung*/<nr>.json`, Tabellen: `opus_gegenrechnung_tabelle.md` (bereinigte Suche) und `opus_gegenrechnung_tabelle_klein.md` (kleine Schritte).

## Kurzfassung

- **Gemessen:** Die Suche genau nach Auftrag (ganze, feste Feldperioden, Abstand zu den Daten bis 1,5 Standardabweichungen) liefert 10 Kandidaten mit vorhergesagtem QI 0,00004 bis 0,00025. **Keiner davon lässt sich mit VMEC++ rechnen** (10 von 10 brechen in den ersten Iterationen ab: „initial boundary is poorly shaped“).
- **Gemessen:** Mit kleinen Schritten (höchstens 0,3 Standardabweichungen von einer Datenform, Plan aus der DEUTUNG von F-237) rechnen 9 von 10 durch; alle 9 haben QI unter 0,00045. Aber 6 von 9 sind **schlechter als ihre eigene Startform**, nur 3 sind etwas besser (−2 %, −5 %, −12 %).
- **Gemessen, das einzig Eigene:** Kandidat 3 (Start = beste Datenform `Do3QyJbtRhtGhrTiBSBbyKM`, QI 0,0000615) auf halbem Schritt: **QI 0,0000472**, rund 23 % niedriger als die beste der 158 685 Datensatzformen. Die Linie Start → Kandidat ist glatt (0,0000615 → 0,0000472 → 0,0000583 → 0,0000681 bei 0 / 0,5 / 1 / 1,5 Schritt), also ein echter Effekt der Formänderung und kein Rechenrauschen. Die Form kommt im Datensatz nicht vor (Abstand 0,14 Standardabweichungen zur nächsten Form, nämlich ihrer Startform).
- **Aber:** Sie ist eine kleine Abwandlung der besten Datenform (nur die zehn wichtigsten Koeffizienten leicht verschoben, alle anderen gleich), und **nach der offiziellen Wertung ist sie wie alle anderen unzulässig** (Wert 0 in allen drei Aufgaben), weil Spiegelverhältnis, Rotationstransformation, Vakuummulde und Flusskompression die Nebenbedingungen verfehlen. DjLe3eL6 und DPrcxq66 bekommen ebenfalls 0.

## 1 Welche Einstellung QI wirklich rechnet

`ConstellarationSettings.default_high_fidelity_skip_qi()` setzt `boozer_preset_settings=None` und `qi_settings=None`; dann liefert `forward_model` `qi = None`. QI liefert **`ConstellarationSettings.default_high_fidelity()`** (VMEC++ hohe Genauigkeit: 99 Flussflächen, Kraft-Toleranz 1e-15, bis 40 000 Iterationen; danach Boozer-Transformation am Rand und `qi.quasi_isodynamicity_residual`, QI = Summe der Residuenquadrate). Dieselbe Einstellung benutzt die offizielle Wertung (`problems.py`, `SingleObjectiveProblem.evaluate` mit `_does_it_require_qi = True` und `MHDStableQIStellarator.evaluate`).

Prüfung (gemessen): DjLe3eL6-Rand und DPrcxq66-Rand nachgerechnet, QI 0,00044754 und 0,00079324, Datensatz 0,00044754 und 0,00079324 (gleich auf 6 Stellen). Die Datensatz-QI ist also mit genau dieser Einstellung berechnet, und unsere Rechnung ist mit ihr vergleichbar. Zeit je Form: 70 bis 155 s (ein Rechenkern je Form, VMEC++ hier einkernig), 4 Formen parallel. Rechenzeit insgesamt etwa 15 Minuten Wanduhr, Grenze 60 Minuten eingehalten.

## 2 Surrogat und Suche

Surrogat wie in `qi_wechselwirkung.py` (gleiche Daten, Aufteilung, Modell; gespeichert in `sim/qi_flaeche/surrogat.joblib`): Gradient Boosting auf log10(QI), R² = 0,91, zehn wichtigste Eingaben unverändert (r_cos[1,−2], z_sin[1,0], r_cos[1,1], r_cos[0,1], r_cos[1,−1], nfp, r_cos[1,0], z_sin[0,1], z_sin[1,−2], z_sin[1,1]).

Bereinigung gegenüber `kandidaten.json`: Feldperioden ganzzahlig und fest auf dem Wert der Startform (dort war nfp mitoptimiert, z. B. 4 → 2,34); m = 0, n ≤ 0 gesperrt (Symmetrie, R00 bleibt). 32 Startformen: DjLe3eL6, DPrcxq66, je 10 beste Datenformen mit 2, 3 und 4 Feldperioden. Je Start 1200 Zufallsschritte auf Paaren der neun freien wichtigsten Eingaben, angenommen nur bei kleinerem vorhergesagtem QI. Auswahl: QI-Surrogat < 0,0004, je Feldperiodenzahl bis 3, dann aufgefüllt.

Drei Läufe:

| Lauf | Bedingung | Kandidaten (Surrogat < 0,0004) | VMEC++ rechenbar |
|---|---|---|---|
| 1 (verworfen) | Abstand zu den Daten 0,5 bis 1,5; Fehler: alle 91 Eingaben auf 1. bis 99. Perzentil begrenzt (veränderte auch nicht bewegte Koeffizienten) | 10 | 0 von 10 |
| 2 bereinigt | wie 1, nur bewegte Eingaben begrenzt | 10 (aus 30 von 32 unter 0,0004) | **0 von 10** |
| 3 kleine Schritte | höchstens 0,3 von der Startform, mindestens 0,1 von jeder Datenform, Schrittweite 0,05 statt 0,25 | 10 (aus 10 von 32) | **9 von 10** |

Warum Lauf 2 scheitert (gemessen, Vorversuch mit niedriger Genauigkeit an 4 Kandidaten): nur die zehn Koeffizienten des Kandidaten auf die Startform gesetzt → Abbruch; ein Viertel des Weges → rechenbar, aber QI 2- bis 4-mal schlechter als die Startform; halber Weg → meist Abbruch. Ursache: Das Abstandsmaß aus `qi_wechselwirkung.py` misst nur die zehn wichtigsten Eingaben gegen die **nächste beliebige** Datenform. 1,5 Standardabweichungen sind dort sehr weit: der typische Abstand einer Datenform zu ihrer Nachbarin ist 0,12 (Median), bei den 300 besten 0,48. Die übrigen 81 Koeffizienten bleiben die der Startform und passen dann nicht mehr zu den verschobenen zehn; der Rand ist nicht mehr glatt genug für VMEC++. Dass alle Kandidaten mit 1,21 bis 1,50 genau an die Grenze laufen, zeigt: das Surrogat schiebt immer nach außen, wo es nichts mehr weiß.

## 3 Ergebnis Lauf 3 (gemessen)

| Nr | Startform (QI Datensatz) | nfp | QI Surrogat | QI VMEC++ | gegenüber Start | A | Elong. | iota Rand/nfp | Spiegelv. Rand | Konvergenz |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | DC6MmpQ95cPyHAHaGnQxWme (0,0000825) | 2 | 0,00007 | 0,000226 | +174 % | 7,12 | 6,67 | 0,086 | 0,46 | ja (9340 It.) |
| 1 | D4nHExBzc2ZRLjt6wzZdQWG (0,0000919) | 2 | 0,00011 | 0,000449 | +388 % | 7,13 | 5,72 | 0,103 | 0,44 | ja |
| 2 | D86W4GogPeqZgB6p6dfToQR (0,0000809) | 2 | 0,00013 | 0,000167 | +106 % | 7,78 | 7,02 | 0,127 | 0,45 | ja |
| 3 | Do3QyJbtRhtGhrTiBSBbyKM (0,0000615) | 2 | 0,00015 | 0,0000583 | −5 % | 7,36 | 7,24 | 0,089 | 0,49 | ja |
| 4 | D42HzX6zW4BR6VH6YD5u7Pf (0,0000836) | 2 | 0,00016 | 0,0000923 | +10 % | 7,67 | 7,61 | 0,073 | 0,44 | ja |
| 5 | DC7XrN75xZCVwJKpNhox2RB (0,00009) | 2 | 0,00020 | – | – | – | – | – | – | **nein** („did not converge“, 391 s) |
| 6 | D4Ag3bsDsZhfzAFZJLMKG9a (0,0000977) | 2 | 0,00025 | 0,000147 | +50 % | 8,10 | 5,37 | 0,071 | 0,50 | ja |
| 7 | D4ke3ng2xsoB7n6uDqN7N5W (0,0000983) | 2 | 0,00027 | 0,000239 | +143 % | 6,97 | 5,96 | 0,132 | 0,52 | ja |
| 8 | DZmjKRpcCQozvDG89aumqjA (0,000279) | 4 | 0,00033 | 0,000245 | −12 % | 8,25 | 6,92 | 0,212 | 0,52 | ja |
| 9 | DDWJg4NBD6KwNGM8KNLJrys (0,000120) | 2 | 0,00034 | 0,000118 | −2 % | 7,90 | 6,58 | 0,066 | 0,46 | ja |
| 3, halber Schritt | Do3Qy… (0,0000615) | 2 | – | **0,0000472** | **−23 %** | 7,39 | 7,15 | 0,088 | 0,45 | ja |
| DjLe3eL6 | Datensatzform DLSFENX… | 4 | – | 0,000448 | ±0 | 9,61 | 6,50 | 0,090 | 0,36 | ja |
| DPrcxq66 | Datensatzform DjvSDqf… | 2 | – | 0,000793 | ±0 | 9,37 | 6,37 | 0,111 | 0,35 | ja |

Konvergenz: Restkraft fsqr unter 1e-15 bei allen konvergierten Formen (VMEC++ bricht sonst mit Fehler ab). Surrogatfehler (gemessen/vorhergesagt): Faktor 0,35 bis 4,1; Abweichung größer als Faktor 2 (in beide Richtungen) bei 4 von 9.

Linienprüfung Kandidat 3 (VMEC++ hohe Genauigkeit, Startform gleich gerechnet): Schritt 0 → 0,0000615 (= Datensatz), 0,5 → 0,0000472, 1,0 → 0,0000583, 1,5 → 0,0000681. Das Spiegelverhältnis am Rand steigt dabei stetig: 0,40 → 0,45 → 0,49 → 0,54. QI wird also gegen das Spiegelverhältnis getauscht.

## 4 Neuheit

Abstand zur nächsten Datensatzform (in Standardabweichungen je Koeffizient): Lauf 3 alle 0,29 bis 0,30, sowohl in den zehn wichtigsten Eingaben als auch in allen 91; nächste Form ist jeweils die eigene Startform. Halber Schritt von Kandidat 3: 0,14. **Keine Form kommt im Datensatz vor** (exakter Treffer hätte Abstand 0). Zum Vergleich: Der Median-Abstand zweier benachbarter Datenformen ist 0,12 (zehn Eingaben) bzw. 1,56 (alle 91). Die Kandidaten sind also neu, aber nahe Verwandte einer Datenform: sie liegen in der Nachbarschaft der Startform, nicht in einem unbekannten Gebiet. DjLe3eL6 und DPrcxq66 stehen mit Abstand 0 im Datensatz.

Rang nach QI unter den 158 685 Datensatzformen (Datensatz-Wert): halber Schritt von Kandidat 3 (0,0000472) wäre Platz 1, Kandidat 3 (0,0000583) Platz 1, Kandidat 4 Platz 8, Kandidat 9 Platz 10.

## 5 Offizielle Wertung (lokal, `constellaration.problems`, nichts eingereicht)

Gerechnet mit den Methoden des Pakets (`is_feasible`, `compute_feasibility`, `_score`) auf den hochgenauen Kennzahlen; zulässig heißt: jede normierte Verletzung höchstens 0,01.

| Aufgabe | Ziel | Nebenbedingungen |
|---|---|---|
| 1 GeometricalProblem | kleinste maximale Elongation (Wert 1 − (E−1)/9) | A ≤ 4, mittlere Dreieckigkeit ≤ −0,5, iota Rand/nfp ≥ 0,3; kein QI |
| 2 SimpleToBuildQIStellarator | größte normierte magnetische Gradientenlänge (Wert L/20) | A ≤ 10, iota Rand/nfp ≥ 0,25, log10 QI ≤ −4 (QI ≤ etwa 0,00011), Spiegelverhältnis Rand ≤ 0,2, Elongation ≤ 5 |
| 3 MHDStableQIStellarator | Hypervolumen der Pareto-Front (Gradientenlänge groß, A klein; Bezugspunkt L = −1, A = 20) über eine Menge Formen | iota Rand/nfp ≥ 0,25, log10 QI ≤ −3,5 (QI ≤ etwa 0,00034), Spiegelverhältnis ≤ 0,25, Flusskompression ≤ 0,9, Vakuummulde ≥ 0 |

Ergebnis: **Alle Formen Wert 0 in allen drei Aufgaben** (unzulässig), auch DjLe3eL6 und DPrcxq66. Größte normierte Verletzung (Aufgabe 2 / 3): halber Schritt Kandidat 3 1,24 / 0,80; Lauf-3-Kandidaten 1,18 bis 1,61 / 0,74 bis 1,09; DjLe3eL6 0,78 / 1,13; DPrcxq66 0,75 / 0,61. Hindernisse: Spiegelverhältnis 0,35 bis 0,54 statt höchstens 0,2/0,25; iota Rand/nfp 0,07 bis 0,21 statt mindestens 0,25; Vakuummulde negativ (−0,02 bis −0,11); Flusskompression 0,98 bis 1,9; Elongation 5,4 bis 7,6 statt ≤ 5; für Aufgabe 1 A 7 bis 10 statt ≤ 4. Die QI-Bedingung von Aufgabe 2 erfüllen nur der halbe Schritt (0,0000472), Kandidat 3 und Kandidat 4; die von Aufgabe 3 alle Lauf-3-Formen. QI allein wird in der Rangliste nicht gewertet; es ist nur eine Nebenbedingung. Eine niedrige QI macht eine Form also nicht ranglistenfähig.

## 6 Vergleich mit der ERWARTUNG (F-238)

| Erwartung | Gemessen |
|---|---|
| 2 bis 4 von 10 mit QI < 0,001 | Lauf 2 (Auftrag wörtlich): 0 von 10 (nicht rechenbar). Lauf 3: 9 von 10 |
| höchstens einer besser als DjLe3eL6 (0,00045), etwa 25 % | Lauf 3: 9 von 9 besser als 0,00045, aber nur, weil die Startformen schon 4- bis 7-mal besser als DjLe3eL6 waren; besser als die eigene Startform: 3 von 9 |
| Surrogatfehler größer als Faktor 2 bei mehr als der Hälfte | 4 von 9 (Lauf 3: zweimal zu optimistisch, zweimal zu pessimistisch); in Lauf 2 nicht messbar, das Surrogat sagt dort Formen voraus, die es physikalisch nicht gibt |

Die Erwartung lag beide Male daneben: Mit 1,5 Standardabweichungen viel schlechter (nichts rechenbar), mit kleinen Schritten viel „besser“, aber der Vergleich mit DjLe3eL6 ist dort kein Maß für eigene Leistung, weil die Startformen schon besser waren. Die DEUTUNG von F-237 trifft zu: Suchraum zu weit, nur kleine Schritte von bekannten Formen aus. Das Surrogat ist als Richtungsweiser kaum besser als Zufall: 3 von 9 kleinen Schritten verbesserten.

## 7 Gemessen und vermutet getrennt

Gemessen: alle QI-Werte und Kennzahlen oben (VMEC++ hohe Genauigkeit über `constellaration.forward_model`), Wiedergabe der Datensatzwerte auf 6 Stellen, Abstände, Rang, offizielle Wertung lokal.

Vermutet, nicht geprüft:
- Dass die Verbesserung von 0,0000615 auf 0,0000472 auch bei anderer VMEC++-Auflösung bestehen bleibt (Rechenrauschen ist durch die glatte Linie unwahrscheinlich; Auflösungsabhängigkeit nicht geprüft).
- Dass sich dieselbe Richtung bei anderen Startformen lohnt; bei Kandidat 3 sitzt das Optimum bei etwa halbem Schritt, das Surrogat ist also schon nach 0,15 Standardabweichungen zu weit gegangen.
- Ob die Form mit Spulen baubar ist (kein Spulensatz gerechnet; Spiegelverhältnis 0,45 und Elongation 7,2 sprechen eher für schwierige Spulen).

## 8 Bewertung für den Nutzer

Es gibt jetzt **eine** Form, die streng genommen eigen ist: `sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json` (nfp 2, QI 0,0000472, mit VMEC++ bestätigt, nicht im Datensatz, niedrigere QI als jede Datensatzform). Sie ist aber nur eine kleine Abwandlung der besten Datenform, und sie ist nach der offiziellen Wertung in allen drei Aufgaben unzulässig (Wert 0). Für eine Einreichung taugt sie so nicht. Ein sinnvoller nächster Schritt wäre eine Suche, die die Nebenbedingungen der Aufgabe 2 oder 3 (Spiegelverhältnis, iota, Vakuummulde) mitführt und jede Stufe direkt mit VMEC++ prüft, statt nur QI im Surrogat zu senken. Hochladen oder Senden: nein, nur auf ausdrückliche Freigabe.

## Nebenbefund Rechentechnik

Zwei Surrogat-Suchen gleichzeitig mit voller Thread-Zahl (OpenMP) liefen mehr als 13 Minuten ohne Fortschritt; mit `OMP_NUM_THREADS=1` brauchte jede etwa eine Minute (Einzelvorhersagen, Überbelegung der 8 Kerne).
