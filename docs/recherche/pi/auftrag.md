# Auftrag: Kühlmitteltemperaturen und Drücke, nur mit Belegen

Lies zuerst den Skill: ~/.hermes/skills/cae/web-recherche/SKILL.md und halte dich streng an seine Regeln.
Arbeitsordner ist dieser Ordner (docs/recherche/pi). Ergebnis in die Datei ergebnis.md hier.

Gesucht je Anlage: Kühlmittel, Eintrittstemperatur, Austrittstemperatur, Druck im Primärkreis.
Anlagen (der Reihe nach, lieber wenige sauber als viele geraten):
1. Druckwasserreaktor (z. B. EPR oder Konvoi)
2. WWER-1000
3. BREST-OD-300 (Blei)
4. ALFRED (Blei)
5. Superphénix (Natrium)
6. HTR-PM (Helium)
7. ITER Erstwand/Blanket-Kühlwasser
8. EU-DEMO WCLL-Blanket (Wasser)
9. EU-DEMO HCPB-Blanket (Helium)
10. Wendelstein 7-X Divertor-Kühlwasser

Vorgehen je Anlage: suche.py -> Wikipedia-Artikel oder Bericht mit abruf.py --suche "inlet,outlet,°C,MPa,bar"
holen -> Werte mit wörtlichem Beleg eintragen. Nicht gefundene Werte: "nicht gefunden".
Zum Schluss pruefe.py ergebnis.md, Fehler beheben bis 0 Fehler, Ausgabe von pruefe.py ans Ende der Datei.
