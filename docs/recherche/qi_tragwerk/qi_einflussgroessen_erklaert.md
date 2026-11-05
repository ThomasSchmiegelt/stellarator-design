# Was beeinflusst QI? Erklärt für Maschinentechniker (2026-11-05)

Stand: erste Fassung. Jede Aussage ist als **belegt** (selbst gemessen oder im Paketcode gelesen), **Folgerung** (aus dem Aufbau abgeleitet) oder **offen** gekennzeichnet. Die Formelanalyse im engeren Sinn (Empfindlichkeit der Boozer-Terme) steht noch aus.

## 1. Worum geht es?
Ein Stellarator hält das heiße Gas (Plasma) allein mit einem verdrillten Magnetfeld. Geladene Teilchen laufen auf schraubenförmigen Bahnen entlang der Feldlinien. Wo das Feld stärker oder schwächer wird, werden manche Teilchen wie eine Kugel in einer Schale hin- und hergeschoben. **QI** (quasi-isodynamisch) ist eine Zahl dafür, wie gut dieses Bild gelingt: Im Idealfall hat die Feldstärke entlang jeder Feldlinie in jeder Wiederholung des Rings genau **eine saubere Mulde**, auf allen Linien gleich. Dann driften die Teilchen nicht aus dem Plasma weg. Kleiner QI-Wert = gut.
Bild für die Mechanik: Es ist ein **Rundlauf- oder Welligkeitsmaß**. Man legt die gemessene Kurve neben die ideale Kurve und summiert die quadrierten Abweichungen.

## 2. Wie wird QI gerechnet? (belegt, Paketcode)
1. Eine Rechnung (VMEC++) bestimmt aus der **Form der äußeren Plasmaoberfläche** das Magnetfeld im Inneren.
2. Das Feld wird in ein Koordinatensystem umgerechnet, in dem die Feldstärke als Summe von Cosinus-Wellen vorliegt (wie eine Fourier-Zerlegung eines Schwingungssignals).
3. Entlang von 75 Feldlinien wird die Feldstärke auf 0 bis 1 normiert. Dann wird die Kurve zur idealen Mulde umgebaut und mit dem Original verglichen.
4. QI ist die Summe der Quadrate aller Abweichungen.
Wichtig: Im Paket wird nur die **äußerste Fläche** bewertet, und die **Spulen kommen gar nicht vor**. Nur die Plasmaform zählt.

## 3. Die Einflussgrößen in Alltagsworten

| Größe | Bild aus der Technik | Wirkung auf QI | Status |
|---|---|---|---|
| **Periodenzahl (nfp)** | Zähnezahl eines Zahnrads: wie oft sich das Muster auf dem Ring wiederholt | wenige Perioden (im Median 2) sind am besten | belegt (Datensatz) |
| **Aspektverhältnis** | Schlankheit eines Rings: Ringdurchmesser zu Rohrquerschnitt | zu klein oder zu groß ist ungünstig; Wirkung wechselt bei etwa 10 das Vorzeichen | belegt (Datensatz); Ursache offen |
| **Elongation** | Wie oval der Rohrquerschnitt ist | stark oval macht die Mulde schwerer sauber zu halten | belegt (Zusammenhang), Mechanismus Folgerung |
| **Dreieckigkeit** | Ob der Querschnitt eher D-förmig ist | wirkt auf die Lage der Mulde in der Periode | Folgerung |
| **Rotationstransformation (iota)** | Gewindesteigung: wie oft die Feldlinie beim Umlauf um den Ring um das Rohr herumläuft | bestimmt, welche Linien man abtastet; für die Wertung Betrag mindestens 0,25 je Periode | belegt (Paket) |
| **Spiegelverhältnis** | Verengung einer Düse: Verhältnis von stärkstem zu schwächstem Feld | wichtigste Größe im gemeinsamen Modell; zu groß zerstört die einfache Mulde | belegt (Datensatzmodell) |
| **Vakuummulde** | Kugel in der Schale statt auf der Kuppe | nötig für Stabilität, trennt „gut“ von „unbrauchbar“ | belegt (Paket-Aufgabe 3) |
| **Flusskompression** | Wie stark sich die Flächen an ungünstigen Stellen zusammendrängen | Nebenbedingung der Aufgabe 3 | belegt (Paket) |
| **Verwindung der Magnetachse** | Wie stark die Mittellinie des Plasmas wie eine Schraubenfeder gedreht ist | wirkt auf iota und Mulde | Folgerung |

## 4. Wie wirken die Größen zusammen?
- **Belegt:** Im Datensatz (rund 158 000 gültige Formen) sind die Paarwechselwirkungen schwach (H-Maß höchstens 0,06). Es ist also eher eine Summe vieler kleiner Beiträge als eine einzige Schalterstellung.
- **Belegt:** Gute Formen liegen in einem Bereich, nicht an einem Punkt (Korridor). Aus den Koeffizienten allein lässt sich der Kasten nicht gut bestimmen (Reinheit 2,3 %), aus den Kennzahlen besser (23 % bzw. 40 %).
- **Belegt:** Die weite Suche im Surrogat scheitert, weil die übrigen Koeffizienten nicht mehr zu den bewegten passen. Kleine Schritte funktionieren.

## 5. Spulen und Strom
- **Belegt:** QI im Paket kennt keine Spulen und keinen Strom.
- **Folgerung:** Die Spulen müssen die Form erzeugen. Weichen sie ab, weicht das echte Feld vom gedachten ab. Alle Ströme gemeinsam zu skalieren ändert die Stärke, nicht die Form, und damit nicht QI. Das **Verhältnis** der Ströme ändert die Form (wie Zusatzspulen bei W7-X).
- **Offen:** Wie stark kleine Verschiebungen und Verdrehungen QI treiben. Das wird in Schritt 2 gerechnet.

## 6. Was noch fehlt
- Messung, welche Cosinus-Terme des Feldes QI bestimmen (Schritt 1 und Formelanalyse).
- Ob sich Fehler von innen nach außen aufaddieren (Schritt 1, mehrere Flächen).
- Einfluss der Spulenlage und der Ströme (Schritte 2 und 3).
