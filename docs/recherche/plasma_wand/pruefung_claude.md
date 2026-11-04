# Prüfung der PI-Werte durch Claude (2026-11-04, Sonnet)

PI-Test: 25 Belege im Wortlaut bestätigt. Inhaltlich:

| Wert | Urteil |
|---|---|
| HELIAS 5-B: Blanket + Abschirmung zwischen Plasma und Spulen 1,3 m (KIT) | brauchbar, Zahl steht wörtlich im Zitat |
| Goodman et al. 2025 (QI-Kraftwerk): c/a 0,868 bis 0,992, a = 1,91 m; W7-X c/a ~0,55 | W7-X-Wert wörtlich belegt; die c/a-Spanne stammt aus einer Tabellenzeile, deren Spaltenzuordnung PI gedeutet hat, mit Vorsicht verwenden |
| ARIES-CS „minimaler Abstand 0,63 m“ | nicht brauchbar: Zitat nennt nur die radiale Dicke eines Blanketmoduls, nicht den Abstand Plasma–Spule |
| ARC Inboard-Wand 0,095 m | Summe aus vier Teildicken, von PI addiert; nur Gefäßwand, kein Abstand Plasma–Spule |
| EU-DEMO Pionierreaktor: Blanket 0,53 m, Abschirmung 0,25 m | wörtlich belegt, Tokamak, Summe 0,78 m (Rechnung von Claude) |
| Definitionen LCFS, Scrape-off-Layer, Spalt bis erste Wand | brauchbar (en.wikipedia, OSTI), Lehrbuchniveau |
| Nicht gefunden | W7-X Abstand Plasma–Wand und Plasma–Spule, Stellaris, ARIES-CS Abschirmung, Kachel- und Toleranzwerte |

Einordnung zu unserer Kette: Unsere Annahme package_min_m = 1,0 m liegt unter dem einzigen belegten Stellarator-Kraftwerkswert
(HELIAS 5-B: 1,3 m Blanket + Abschirmung). Unsere Hülle (Plasma bis Gehäuse-Innenseite) ist ein vergleichbarer Abstand.
Sätze mit Hülle unter 1,3 m (DYU ×1,45: 1,27 m) liegen knapp darunter. Der Abstand Spule–Plasma unserer Sätze (0,85 bis 1,15 a) liegt im Bereich
von Goodman et al. (0,87 bis 0,99 a), W7-X liegt bei 0,55 a.
