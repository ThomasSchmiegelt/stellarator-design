# Vortest zwei Spulenringe (Nutzeridee F-221), 2026-11-04

Frage: Entkoppelt ein innerer Spulenring mit kleinem Strom den Abstand von der Kraft?
Plasma DjLe3eL6 (QI 0,00045), skaliert auf 1096 m³, a = 1,80 m. Keine Kettenänderung.
Code: `stellarator/zwei_ringe.py`, Ergebnisse `sim/qi_zwei_ringe/<fall>.json`, Verlauf je Runde `verlauf_<fall>.json`,
Startskript `sim/qi_zwei_ringe/lauf.sh`. Ein erster Lauf (Ordner `lauf1/`) ist verworfen: die Ströme bewegten sich
dort nicht (Stromfreiheitsgrade 1e5 gegen Geometrie ~0,1, L-BFGS ohne Skalierung), außerdem eine zu enge Längengrenze.

## Vorgehen

- simsopt Stage-2 (.venv-opt, simsopt 1.11), Ziel normierter Fluss B·n auf der halben Periode, Fourier-Ordnung 7,
  Stellarator-Symmetrie, 4 Feldperioden. Strafen: Spule–Plasma je Ring (1,3 a bzw. 0,85 a), Spule–Spule ≥ 0,3 a
  (alle Spulen, auch zwischen den Ringen), Biegeradius ≥ 0,5 a, mittlere quadratische Krümmung ≤ Wert des
  Proxima-Satzes (20,4), Ringlänge ≤ Proxima-Länge (124,5 a je 5 Spulen) plus 2π(d − 0,85) a je Spule.
  Ein Außenstrom fest, alle anderen frei (Innenströme frei, Start 10 % des Außenstroms).
- Start: Kurven durch die um d entlang der Normale versetzte Randlinie in der Ebene der Spule.
- Je Runde 2000 L-BFGS-Schritte, höchstens 2 Runden (Strafgewicht ×10, falls eine Grenze verletzt).
- Auswertung gleich für alle Fälle: |B·n|/|B| auf dem vollen Rand (128 × 64); Nettokraft je Spule aus allen
  anderen Spulen (wie `qi_kraft_scan.kraefte`); f = F μ0/(B0² a²), B0 = mittleres |B| auf der Achse (Näherung:
  Schwerpunkt des Randquerschnitts), a = √(V/(2π² R0)); MN bei B0 = 6,5 T, a = 1,80 m (1 f = 108,9 MN).
- Zusatzfall A085 (eigener Einring bei 0,85 a) als Kontrolle, was der eigene Optimierer bei Proxima-Abstand leistet.
  Zusatzfall B8: wie B, Innenring 8 statt 5 Spulen je Halbperiode.

## Gemessen

| Fall | Ringe (Abstand) | Spulen | Bn/B mittel | Bn/B max | f max | F max MN | Σ\|I\| MA | Biegeradius min | Spule–Spule min | Runden |
|---|---|---|---|---|---|---|---|---|---|---|
| C Proxima-Satz | 1 (0,86 a) | 40 | 2,41e-3 | 1,71e-2 | 5,37 | 585 | 580 | 0,50 a | 0,67 a | – |
| A085 Kontrolle | 1 (0,85 a) | 40 | 6,6e-4 | 5,7e-3 | 7,78 | 847 | 580 | 0,50 a | 0,30 a | 1 |
| A Einring außen | 1 (1,30 a) | 40 | 1,63e-3 | 1,38e-2 | 11,88 | 1294 | 580 | 0,50 a | 0,30 a | 2 |
| B Zweiring 5+5 | 2 (1,30 / 0,85 a) | 80 | 6,7e-4 | 8,7e-3 | 12,77 | 1391 | 580 | 0,50 a | 0,30 a | 2 |
| B8 Zweiring 5+8 | 2 (1,30 / 0,85 a) | 104 | 8,2e-4 | 1,05e-2 | 11,42 | 1244 | 580 | 0,50 a | 0,30 a | 1 |

Ring für Ring (Ströme der Basisspulen bei 6,5 T):
- B: Außenring 6,7 bis 13,5 MA, größte Kraft 12,77 (1391 MN); Innenring 1,0 bis 7,4 MA, größte Kraft 1,34 (146 MN).
- B8: Außenring 7,5 bis 12,5 MA, 11,42 (1244 MN); Innenring 1,0 bis 5,1 MA, 0,68 (74 MN).
- A: 10,6 bis 18,3 MA. C: 14,2 bis 14,9 MA.

Konvergenz: Keine Optimierung ist konvergiert. Alle Läufe endeten am Iterationslimit (2000 je Runde), der Feldfehler
fiel noch. Alle Grenzen sind im Endstand eingehalten (Abstände je Ring 1,30/0,85 a erreicht, Spule–Spule genau an
der Grenze 0,30 a). B8 hatte nur eine Runde (gleiche Schrittzahl wie B in Runde 1), ist also weniger weit gerechnet als B.

Σ|I| ist in allen Fällen 580 MA: alle Ströme haben dasselbe Vorzeichen, und die Summe der Ströme, die die Achse
umschließen, legt nach dem Durchflutungsgesetz das Feld auf der Achse fest (2π R B0/μ0). Diese Spalte trennt die
Fälle also nicht; ein Innenring spart keine Amperewindungen, er verteilt sie nur um.

## Vergleich mit der Erwartung (vorab festgelegt)

- „B senkt den Feldfehler gegenüber A mindestens um Faktor 2“: im Mittel getroffen (A/B = 2,4; A/B8 = 2,0),
  im Maximum nicht (1,6 bzw. 1,3).
- „Die größte Kraft sinkt nur wenig (unter 30 %)“: verfehlt in der Richtung. Sie sinkt nicht: B +7,5 % gegenüber A,
  B8 −3,8 %. Die Innenspulen selbst tragen wenig (146 bzw. 74 MN), die Außenspulen bleiben bei 1240 bis 1390 MN.
- „Schafft A den Feldfehler 3e-3 nicht, ist das ein Befund“: kein Befund, A erreicht 1,63e-3 bei 1,3 a.
  Einschränkung: mit Spule–Spule 0,3 a statt 0,67 a beim Proxima-Satz.

## Bewertung

Gemessen:
- Der Innenring senkt den Feldfehler (Faktor 2 bis 2,4 im Mittel), aber nicht die Kraft der Außenspulen.
  Ohne Innenring kostet der größere Abstand (0,85 → 1,30 a) im eigenen Optimierer +53 % Kraft (7,78 → 11,88);
  der Innenring holt davon nichts zurück. Abstand und Kraft sind damit nicht entkoppelt, nur Abstand und Feldfehler.
- Der Feldfehler war bei 1,3 a mit einem Ring gar nicht der Engpass (1,6e-3, unter 3e-3).
- Gegenüber dem Proxima-Satz C hat schon die Kontrolle A085 bei gleichem Abstand 45 % mehr Kraft, aber einen
  3,6-mal kleineren Feldfehler. Die Optimierung tauscht hier Kraft gegen Feldgüte (kein Kraftziel, Spule–Spule nur 0,3 a).
  Ein direkter Vergleich A/B mit C ist darum nicht gleichwertig; nur A, A085, B, B8 haben dieselben Grenzen.

Vermutet (nicht gerechnet):
- Die Kraft der Außenspulen folgt aus dem Hauptfeld, das sie tragen müssen (alle Ströme gleichsinnig, 580 MA
  insgesamt). Ein Innenring mit kleinem Strom ändert das nicht. Abhilfe müsste aus einem Kraftziel in der
  Optimierung kommen (LpCurveForce gibt es in invers/stufe2_spulen.py) oder aus größerem Spule–Spule-Abstand.
- Mit einem Kraftziel könnte der gewonnene Feldfehler-Spielraum des Innenrings in weniger Kraft getauscht werden;
  das ist der eigentlich interessante nächste Test (A und B mit gleichem Kraftgewicht, Feldfehler ≤ 3e-3 halten).
- Die Innenspulen liegen bei 0,85 a, also unter 1,3 m Abschirmung (0,72 a). Für sie gilt dieselbe Fluenzfrage wie für
  den heutigen Satz; die Idee hilft dem Platzproblem nur, wenn der Innenring die Strahlung verträgt
  (z. B. normalleitend statt supraleitend). Nicht geprüft.
- Kräfte zwischen den Ringen (Innenring gegen Außenring) sind in den Nettokräften enthalten, aber nicht getrennt
  ausgewiesen; Tragwerk für zwei Ringe nicht betrachtet.

## Nebenbefund (zu prüfen)

Für denselben Satz DjLe3eL6 gibt `docs/recherche/qi_tragwerk/kraft_scan.csv` f max = 13,66, hier 5,37 (Faktor 2,54,
Kraftverhältnis der fünf Spulen identisch). Ursache: der Scan teilt durch B0 aus den DESC-Metriken (0,994 T in der
Rohgeometrie), das Spulenfeld auf der Achse ist aber 1,58 T (Durchflutungsgesetz-Kontrolle: 1,63 T); 1,58²/0,994² = 2,53.
Die Kette rechnet für diesen Satz 563,5 MN (sim/kopplung/qi_proxima_dje, Punkt 2), hier 585 MN: passt zu f = 5,37,
nicht zu 13,66. Die f-Werte des Scans sind also für diesen Satz um 2,5 zu hoch. Ob der Faktor für alle Sätze gleich ist
(dann blieben Rangfolgen gültig), ist nicht geprüft; Aussagen wie „3 bis 10 mal mehr Kraft“ (F-215) sollten mit
Spulenfeld-B0 nachgerechnet werden.
