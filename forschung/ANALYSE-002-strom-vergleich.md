# ANALYSE-002 Strom-/Induktivitaets-Vergleich (2026-10-23)

**Beobachtung:** Thin-wire-Modell (1 Draht/Spule) vs. reale W7-X-NPC
(108 Windungen, 3,5*2,5*1,5 m). Feld-Energie und Induktivitaet um
Groessenordnungen unters
Groessenordnungen unter: L 15.8 uH vs 5.8 H, E 12.2 MJ vs 620 MJ.

**Messung** (frisch 2026-10-23):
| Groesse | Modell | W7-X NPC | Verh. |
|---|---|---|---|
| Strom/Wickung (bei 2.5 T) | 10.4 kA | 12.8 kA | 0.80x |
| Ampere-Turns/Spule (bei 2.5 T) | 1.244 MA | 108x12.8 kA=1.38 MA | 0.90x |
| Induktivitaet | 15.8 uH/Spule | 5.803 H total | ~3.7e5x |
| Feldenergie | 12.2 MJ | ~620 MJ | ~51x |

**Fundstelle:**
- Modell: geo/w7x_gen/PARAMETER.json (2026-10-23, frisch), geo/parametrische_generierung.py
- W7-X NPC: skill cae-ingenieurs-doku -> references/w7x-eckdaten.md (IAEA CSP FT2-3;
  Bosch 2005; IPP 2003; Nominal NP ~16.5 kA, Betrieb 2.8-3.0 T)
- B-005/B-009/B-010, BEFUNDE.md

**Schlussfolgerung:**
1) Feld-Budget (Ampere-Turns/Spule) stimmt: 0.90x auf 2.5-T-Basis,
   0.80x pro Wickung. Das thin-wire-Modell liefert die korrekte
   Groessenordnung; der scheinbare 'Strom-Fehler' ist ein Framing-Artefakt
   (1 Draht vs. 108 Windungen).
2) L und E sind thin-wire Untergrenzen: Faktor ~3.7e5 (L) bzw. ~50 (E),
   da das Modell kein 108-Windungs-Wickelpaket abbildet. Nur Groessen-
   ordnung, nicht Bemessung (B-009).
3) Exakte Strom/L/E-Bemessung braucht die realen W7-X-Centerlines;
   Quellenlage 2026-10-23: STELLOPT/simsopt/DESC/PubMed-Pfade = 404/leer
   (B-009/p10). Offen.

Status: **abgeschlossen** — konsistent in BEFUNDE B-010, ERINNERUNGEN
und PDF (bericht/bericht.pdf). Kernzahl: 0.90x Ampere-Turns, kein
Zahlenfehler, Modellgeometrie-Limitation.
