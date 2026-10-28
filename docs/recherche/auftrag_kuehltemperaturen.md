# Auftrag an Hermes: Recherche Kühlkreislauf-Temperaturen (2026-10-27)

Ziel: belastbare, zitierte Referenzwerte für das Kühlsystem der Erstwand/des Plasmagefäßes im Projekt
(Stellarator 1 GW, Stahlwand mit Kühlkanälen, Variante Wasser oder Flüssigblei). Ergebnis als Markdown nach
`docs/recherche/kuehlkreislauf_temperaturen.md` (Deutsch).

## Gesucht, je Kühlsystem: Eintritt/Austritt [°C], Druck [MPa], Massen-/Volumenstrom wenn verfügbar, Quelle
1. Druckwasserreaktor (DWR/PWR, auch WWER), primär und sekundär (Dampf), möglichst konkrete Anlage (z. B. Konvoi, EPR, AP1000).
2. Siedewasserreaktor (SWR/BWR).
3. Natrium-Brüter (z. B. Superphénix, BN-600/800, PFBR).
4. Bleigekühlte Reaktoren (ALFRED, BREST-OD-300, MYRRHA), Blei-Bismut.
5. Hochtemperaturreaktor mit Helium (HTR-PM, THTR).
6. Fusion: ITER (Erstwand/Blanket, Divertor, Vakuumgefäß), EU-DEMO-Blankets WCLL, HCPB, DCLL, HCLL; Wendelstein 7-X
   (Divertor/Wandkühlung), ARC/SPARC (FLiBe) falls vorhanden.
7. Werkstoffgrenzen: EUROFER97 (Temperaturfenster unter Bestrahlung, Untergrenze Versprödung, Obergrenze Kriechen),
   Korrosionsgrenze Stahl in Blei/PbLi, Wolfram als Schutzschicht. Stoffwerte flüssiges Blei und Pb-17Li bei 400 °C
   (Dichte, cp, Wärmeleitfähigkeit, Viskosität, elektrische Leitfähigkeit, Schmelzpunkt).

## Wo suchen (gängige Datenbanken/Quellen)
IAEA ARIS (aris.iaea.org), IAEA PRIS, OECD-NEA, EUROfusion scipub (scipub.euro-fusion.org), ITER Organization (iter.org),
OSTI.gov, KIT-Publikationen, arXiv, Google Scholar, ScienceDirect/Fusion Engineering and Design (Abstracts),
NRC (nrc.gov, Design Control Documents), World Nuclear Association, Wikipedia nur als Einstieg.

## Regeln
- Jede Zahl mit Quelle (Titel + URL, möglichst DOI). Primärquelle bevorzugen. Widersprüche nebeneinander nennen.
- Nichts erfinden. Was nicht gefunden wurde, als "nicht gefunden" kennzeichnen.
- Keine PDFs ins Repo legen, nur zitieren. Keine anderen Dateien im Projekt ändern.
- Zum Abgleich: bisherige Werte stehen in ERINNERUNGEN.md (Abschnitt 2026-10-27, Referenz-Kühltemperaturen) — bestätigen oder korrigieren.
- Am Ende: Tabelle "Empfehlung für das Projekt" (Wasser-Variante, Blei-Variante) mit Begründung.
