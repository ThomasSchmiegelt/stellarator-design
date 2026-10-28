# Kühlmitteltemperaturen und Drücke (PI, qwen-gross, nur mit Belegen)

> **Prüfvermerk (Claude, 2026-10-28):** Jede Zeile von PI einzeln recherchiert (eine Anlage je Aufruf, `lauf.sh`),
> alle Zitate maschinell gegen die abgerufenen Seiten geprüft (Ausgabe unten). pruefe.py prüft nur, dass ein Zitat
> in der Quelle steht, nicht ob es richtig gedeutet wurde. Beim Gegenlesen korrigiert:
> - **BREST-OD-300 und ALFRED: Eintritt/Austritt vertauscht.** Die Zitate nennen den Eintritt in den *Dampferzeuger*
>   (= Reaktoraustritt). Richtig: BREST 340 → 540 °C, ALFRED 390 → 520 °C.
> - EPR: Zitat ohne Bezeichnung (nur „295.2 °C“); Zuordnung Ein/Aus aus der Wikipedia-Tabelle von Hand bestätigt.
> - Lücken: EU-DEMO WCLL (Verlagsseiten MDPI/IOP sperren automatische Abrufe mit 403), W7-X Kühlwasser,
>   ITER-Austritt, Superphénix-Eintritt. Lokale PDFs gehen mit `abruf.py file:///pfad/datei.pdf`.

| Anlage | Kühlmittel | Eintritt °C | Austritt °C | Druck MPa | Belege |
|---|---|---|---|---|---|
| EPR (PWR, Framatome/EDF) | Wasser | 295.2 | 320 | 15.5 | Beleg: "Third-generation pressurised water nuclear reactor design" (https://en.wikipedia.org/wiki/EPR_(nuclear_reactor)) \| Beleg: "295.2 °C (563.4 °F)" (https://en.wikipedia.org/wiki/EPR_(nuclear_reactor)) \| Beleg: "320 °C (608 °F)" (https://en.wikipedia.org/wiki/EPR_(nuclear_reactor)) \| Beleg: "155 bars (15,500 kPa; 2,250 psi)" (https://en.wikipedia.org/wiki/EPR_(nuclear_reactor)) |
| WWER-1000 | Wasser | 289 | 319 | 16,0 | Beleg: "Reactor fuel rods are fully immersed in water kept at" (https://en.wikipedia.org/wiki/VVER) Beleg: "core coolant inlet | 250 | 250 | 269 | 289" (https://en.wikipedia.org/wiki/VVER) Beleg: "core coolant outlet | 269 | 275 | 300 | 319" (https://en.wikipedia.org/wiki/VVER) Beleg: "Vapor pressure, in 100 kPa" (https://en.wikipedia.org/wiki/VVER) Beleg: "in the first circuit | 100 | 105 | 125 | 160.0" (https://en.wikipedia.org/wiki/VVER) |
| BREST-OD-300 (LFR, Russland) | Blei | **340** (PI: 540, vertauscht) | **540** (PI: 340) | nicht gefunden | Beleg: "Lead is chosen as a coolant" (https://en.wikipedia.org/wiki/BREST_%28reactor%29) \| Beleg: "540 °C (1,004 °F) on entry in the steam generator" (https://en.wikipedia.org/wiki/BREST_%28reactor%29) \| Beleg: "340 °C (644 °F) on exit of the steam generator" (https://en.wikipedia.org/wiki/BREST_%28reactor%29) |
| ALFRED (LFR, Italien/Rumänien) | Blei | **390** (PI: 520, vertauscht) | **520** (PI: 390) | nicht gefunden | Beleg: "Coolant: Lead" (https://en.wikipedia.org/wiki/ALFRED_%28nuclear_reactor%29) \| Beleg: "520 °C (968 °F) on entry in the steam generator" (https://en.wikipedia.org/wiki/ALFRED_%28nuclear_reactor%29) \| Beleg: "390 °C (734 °F) on exit of the steam generator" (https://en.wikipedia.org/wiki/ALFRED_%28nuclear_reactor%29) \| Hinweis: "Similarly, as with all fast spectrum reactors, the coolant is not pressurized" (https://en.wikipedia.org/wiki/Lead-cooled_fast_reactor) |
| Superphénix (FBR, Creys-Malville, Frankreich) | Natrium | nicht gefunden | 550 | ~0.1 (atmosphärisch) | Beleg: "évacuée avec du sodium liquide" (https://fr.wikipedia.org/wiki/Superph%C3%A9nix) \| Beleg: "du sodium liquide (à 550 °C )" (https://fr.wikipedia.org/wiki/Superph%C3%A9nix) \| Beleg: "un circuit primaire qui fonctionne à la pression atmosphérique" (https://fr.wikipedia.org/wiki/R%C3%A9acteur_rapide_refroidi_au_sodium) |
| HTR-PM (Shidao Bay, China) | Helium | 250 | 750 | 7.0 | Beleg: "employs helium as a coolant" (https://www.osti.gov/servlets/purl/3371688) \| Beleg: "Core inlet temperature C 250.0" (https://www.osti.gov/servlets/purl/3371688) \| Beleg: "Core outlet temperature C 750.0" (https://www.osti.gov/servlets/purl/3371688) \| Beleg: "Core outlet pressure MPa 7.0" (https://www.osti.gov/servlets/purl/3371688) |
| ITER (Erstwand/Blanket, TCWS) | Wasser | 70 | nicht gefunden | 4 | Beleg: "The cooling water—injected at 4 MPa and 70 °C—is designed to remove up to 736 MW" (https://www.iter.org/mach/Blanket); Beleg: "Water will be used to remove heat from the vacuum vessel and its components" (https://www.iter.org/mach/coolingwater) |
| EU-DEMO WCLL-Blanket (Wasser) | Wasser | nicht gefunden | nicht gefunden | nicht gefunden | Beleg: "Water-cooled lithium lead (WCLL)" (https://en.wikipedia.org/wiki/Breeding_blanket) |
| EU-DEMO HCPB-Blanket (Helium) | Helium | 300 | 500 | 8 | Beleg: "extracted by the He primary coolant" (https://publikationen.bibliothek.kit.edu/1000034375/2566134) | Beleg: "The inlet and outlet temperatures of the primary coolant are 300 and 500 °C" (https://publikationen.bibliothek.kit.edu/1000034375/2566134) | Beleg: "Coolant Pressure, Temperature in/out 8 MPa, 300/500 °C" (https://publikationen.bibliothek.kit.edu/1000034375/2566134) |
| Wendelstein 7-X Divertor-Kühlwasser | Wasser | nicht gefunden | nicht gefunden | nicht gefunden | Beleg: "auf wassergekühlten CuCr1Zr-Fingern sind für eine lokale Wärmelast von 10 MW/m² im Langzeitbetrieb ausgelegt" (https://de.wikipedia.org/wiki/Wendelstein_7-X) |

```

29 Belege bestaetigt, 0 Fehler
```
