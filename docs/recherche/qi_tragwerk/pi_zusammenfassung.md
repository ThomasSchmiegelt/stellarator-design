UNGEPRÜFT (PI, ohne Claude)

> **Hinweis Claude (2026-11-04):** Diese Zusammenfassung entstand mitten im Lauf (Tabelle unvollständig) und ist überholt. Falsch: „9 Studien kein Ergebnis“ (PI verwechselt die Nummern der Studien, Läufe 11–16 haben Ergebnisse) und „Netzstudien gaben kein Ergebnis“ (Lauf 32 und 0169 dünn wurden nachgeholt). Maßgeblich: sim/qi_feld/tabelle.md und Ereignisprotokoll F-188.
# QI-Tragwerk: Ergebnis gegen Erwartung F-186 (alle Zahlen wörtlich aus tabelle.md)
Grenzen: Stahl p99 500 MPa, Dehnung Wickelpaket 0,3 %.
- (1) Regression muss 1098 MPa treffen: erfüllt – Studie 10 p99 = 1098 MPa.
- (2) Lockerere Querbedingung + mehr Verbinder: p99 = 721 MPa (Lauf 16) im erwarteten
  600–800-Bereich; u bleibt 306–309 mm statt <100 mm; 500-MPa-Grenze wie erwartet verfehlt.
- (3) Vier Lagerstellen: p99 fällt von 993 (Querbedingung 0,6) auf 910; Kombi Lauf 16 = 721 MPa.
  Hilfreich, aber die beste Variante ist eine andere.
- Spulen 2, 3, 8, 9 bleiben trotz mehr Verbindern hoch (p99 je Spule 179–1515 MPa bei Lauf 16,
  Regression 291–3720 MPa) → nach Deutung F-186: örtliche Biegung, QI braucht eigenes Tragwerkskonzept.
- F-186: Werte < 500 MPa gelten erst nach Netzstudie – die Netzstudien (Nr 20, 32) gaben „kein Ergebnis".
## Beste Variante
Nr 21 „Bester Stand, dicke Wände": p99 = 496 MPa (einziger Wert <500), u max = 138 mm,
p99 je Spule 163–1423 MPa, Dehnung WP = 0,36 %, Verbinder 340/579, Stahl t = 40662,
Reparaturrunden = 1, „alle Grenzen = nein".
## Verletzte Grenzen / offene Punkte
- Dehnung WP: alle Läufe mit Ergebnis 0,36–0,51 % – keine Variante erfüllt 0,3 % (best 0,36 %, Nr 21).
- 9 Studien „kein Ergebnis" (Nr 11, 12, 13, 17, 20, 22, 30, 31, 32); laut F-187 starben 2 Läufe
  am Speicherlimit 20 GB, „rc 0" im Log war Skriptfehler.
- 0169 dünn: 305 MPa erwartet, 308 MPa erreicht (Feinnetz: kein Ergebnis);
  F-187: im feineren Netz womöglich über 426 MPa, womöglich nicht zulässig – ungeprüft.
## Offene Fragen
1. Warum „alle Grenzen = nein" bei Nr 21 trotz p99 = 496 < 500? (Vermutung: Dehnung 0,36 % > 0,3 %.)
2. Warum 9 „kein Ergebnis" – nur Speicher (20 GB) oder auch Konvergenz?
3. Bestätigt ein stabiles feines Netz den Wert von 496 MPa, wie F-186 für <500 MPa verlangt?
4. Nächstes Schritt: eigenes Tragwerkskonzept (durchgehende Struktur statt Einzelverbinder),
   wie Deutung F-186 und Sonnet-Literatur nahelegen?
