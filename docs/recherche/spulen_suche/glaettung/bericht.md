# Spulen glätten (08.11.2026)

**Herkunft:** Das Plasma ist DATJ5FC, eine DATENSATZ-Form (ConStellaration), unverändert. Die Spulen sind EIGENE Spulen (d100_n5_lr_s56, Stage 2): 5 Grundspulen, Fourier-Ordnung 7.

**Frage (Nutzeridee):** Kann man die Spulen nach der Berechnung glätten, damit die „8er“ verschwinden?

**Vorgehen:** Jede Spule ist eine Summe von Wellen (Fourier-Reihe bis Ordnung 7). Glätten heißt hier, die kurzen Wellen abzuschneiden: Ordnung 7 → 6 → … → 2. Für jede Stufe wird gemessen:
- der Feldfehler (wie gut das Spulenfeld an der Plasmaoberfläche anliegt; kleiner ist besser);
- der kleinste Biegeradius;
- die Zahl der Selbstkreuzungen, in der Draufsicht auf die Spulenebene und in den Seitenansichten.

| Ordnung | 7 (Original) | 6 | 5 | 4 | 3 | 2 |
|---|---|---|---|---|---|---|
| Feldfehler | 1,05e-3 | 1,01e-2 | 1,55e-2 | 1,75e-2 | 3,7e-2 | 7,4e-2 |
| Seiten-Achter je Grundspule | 1,3,2,2,2 | 1,3,2,1,2 | 1,3,2,2,3 | 1,3,2,1,2 | 1,3,1,1,3 | 1,2,1,1,2 |
| kleinster Biegeradius, m | 0,85 | 0,07 | 0,19 | 0,07 | 0,05 | 0,12 |

**Lesehilfe `kappen.png`:**
- Jede Spalte ist eine Grundspule.
- **Oben:** der Blick senkrecht auf die Ebene, in der die Spule am ehesten liegt. Hier kreuzt sich keine Spule.
- **Unten:** die Seitenansicht. Hier sieht man die „8“: Die Spule ist in sich verdreht wie ein verdrillter Gummiring.
- Schwarz ist das Original, rot Ordnung 6, blau Ordnung 5. Die 8 bleibt in allen Stufen.

**Ergebnis:**
- Glätten entfernt die 8er nicht. Sie sind eine große Form, keine kleine Welle.
- Schon der erste Schritt verschlechtert den Feldfehler um das Zehnfache.
- Der Biegeradius wird durch das Kappen nicht besser, sondern an einzelnen Stellen viel kleiner.

**Folge:** Baubarkeit muss in die Optimierung selbst, als Strafterm gegen Höhe aus der Ebene oder gegen Seiten-Achter. Dazu passt die Idee „Spulen = Wörter“: ein Wortschatz aus ebenen, baubaren Spulen.

---

# Smoothing the coils (2026-11-08)

**Origin:** The plasma is DATJ5FC, an unmodified ConStellaration dataset shape. The coils are our OWN Stage 2 coils, d100_n5_lr_s56.

**Method:** We truncated the Fourier order of the coils from 7 down to 2.

**Results:**
- The field error rises tenfold already at order 6.
- The minimum bend radius does not improve; at some points it gets much smaller.
- The "figure-eights" appear only in the side view: the coils are twisted saddle coils, 4.5–6.9 m out of plane. They survive all truncation levels.

**Conclusion:** Smoothing after the fact does not help. Buildability has to be a penalty inside the coil optimisation.
