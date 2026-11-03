# Kühlsegment des Plasmagefäßes – wie die Berechnung abläuft

Diese Notiz beschreibt, wie das durchströmte Kühlsegment (10° des Plasmagefäßes, 85–95°) entstanden ist und berechnet
wird. Im Mittelpunkt steht die Zusammenarbeit zwischen Nutzer (Konstrukteur) und KI-Assistent (Claude Code):
Der Nutzer gibt Ziel, Konstruktionsidee und Korrekturen vor. Der Assistent setzt sie in Geometrie, Rechnung und
Bilder um und legt die Ergebnisse so vor, dass der Mensch sie beurteilen kann.

> Hobbyprojekt, aus Neugier entstanden. Die Zahlen sind grobe Abschätzungen. Sie ersetzen keine Auslegung.

## 1. Die Werkzeugkette

| Schritt | Werkzeug | Datei | Ergebnis |
|---|---|---|---|
| Auslegung | Python | `stellarator/kuehlung_segment.py` (`auslegung`) | Wärmelast, Massenstrom, Rohrdurchmesser |
| Geometrie | PicoGK (Voxel, C#) | `picogk/SegmentKuehlung`, gesteuert von `kuehlung_segment.py` | `stahl.stl`, `wasser.stl` |
| Kontrollbilder | PyVista | `kuehlung_segment.py` (`bild`), `stellarator/draufsicht.py`, `stellarator/modell_ansicht.py` | Standbilder, interaktives 3D-Fenster |
| Strömung | FluidX3D (Lattice-Boltzmann, GPU) | `stellarator/kuehlung_cfd.py`, geänderte Fassung von `setup.cpp` in `fluidx3d/` | Geschwindigkeits- und Druckfeld |
| Prüfung | Python/SciPy | `kuehlung_cfd.durchgaengig` | Wasserweg vom Einlass bis zum Auslass zusammenhängend? |
| Auswertung | Python/Matplotlib | `kuehlung_cfd.auswerten` | `auswertung.png/json`: Druckverlust, Verteilung, Geschwindigkeit an der Plasmaseite |
| Animation | Python + Blender (EEVEE) | `stellarator/stroemung_animation.py`, `stellarator/blender_stroemung.py`, `picogk/StlSchnitt` | Teilchenschweife durch das berechnete Feld, Film |

FluidX3D ist **nicht** Open Source im Sinne der MIT-Lizenz dieses Repos. Die Lizenz ist
„source-available, nur nicht kommerziell“. Die geänderten Dateien liegen getrennt in `fluidx3d/`, mit der
Originallizenz und dem Hinweis „geänderte Fassung“. Bei Veröffentlichung von Ergebnissen werden das FluidX3D-Repository
und die dort genannten Arbeiten zitiert.

## 2. Ablauf einer Schleife

```
 Nutzer: Idee / Skizze / Korrektur
        │
        ▼
 Assistent: Parameter festlegen ──► Geometrie (PicoGK) ──► Bild + 3D-Fenster öffnen
        │                                                        │
        │                                Nutzer prüft die Geometrie ◄┘
        │                                    │ passt nicht → zurück zur Idee
        ▼                                    ▼ passt
 Probelauf FluidX3D (wenige Schritte) ──► Durchgängigkeit prüfen
        │
        ▼
 Volle Rechnung (8-mm-Gitter, 40 s physikalische Zeit, ~15 min auf der GPU, losgelöst mit Speicherwächter)
        │
        ▼
 Auswertung + Bild öffnen ──► Assistent fasst zusammen, vergleicht mit den Vorgängern, nennt Grenzen
        │
        ▼
 Nutzer entscheidet die nächste Änderung
```

Feste Regeln dabei:
- **Bilder statt Zahlenkolonnen.** Jedes Ergebnis wird als Bild oder 3D-Fenster geöffnet. Der Nutzer beurteilt die
  Geometrie mit dem Auge, nicht anhand einer Beschreibung.
- **Erst die Geometrie zeigen, dann rechnen.** Ein Strömungslauf dauert rund 15 Minuten, ein Geometriebau mit
  8-mm-Voxeln ebenso. Ein Missverständnis in der Form kostet also eine halbe Stunde. Deshalb wird eine neue Form
  zuerst grob gebaut (12 mm, ~5 min) und gezeigt.
- **Ressourcen beachten.** Die GPU gehört eigentlich einem anderen Agenten (Hermes) und wurde für diese Arbeit
  freigegeben. Vor jedem Lauf werden GPU, RAM und Plattenplatz geprüft, lange Läufe laufen unter einem
  Speicherwächter. Aufgeräumt wird nur nach Rückfrage.
- **Ehrlich berichten.** Jedes Ergebnis wird mit seinen Grenzen genannt, zum Beispiel „Durchfluss ~7 % unter Soll
  (Randbedingung)“ oder „Wärmeübergang grob, ohne Rippenwirkung“.

## 3. Wie die Varianten entstanden sind (Verlauf der Zusammenarbeit)

| Variante | Anstoß | Was gebaut wurde | Ergebnis |
|---|---|---|---|
| a | Nutzer: Segment kühlen, Verteilkanal auf einer Seite, Austritt auf der anderen, Kreisrohre, gleichmäßig verteilen, in den Bauraum passen. Rückfragen zu Segment, Verteilprinzip, Durchfluss und GPU beantwortet. | Kammer + Lochblech, Gyroid-Kern 0,9 m | Lauf instabil, Rückströmung |
| b | **Nutzer: „vielleicht ist es nicht durchgängig“** – Treffer: Die Bohrungen lagen wegen der verdrillten Fläche neben der Platte und waren im Gitter zu. | Bohrungen in der richtigen Ebene, 8-mm-Gitter, Durchgängigkeitsprüfung eingeführt | Strahlen durch den Kern, Plasmaseite 4 cm/s |
| e1, e2 | Nutzer: „erst bessere Auslegung“ | Spalt hinter der Erstwand, abgestufte Bohrungen | Spalt 0,43 m/s, aber Lochblech |
| f1 | **Nutzer: „das Wasser soll durch die Filamentstrukturen fließen“**, Ringkammern flächig offen, keine Bohrungen | Ringkammern ohne Lochblech | Rückströmung vor dem Einlass, Streuung 141 % |
| f2 | Nutzer wählt aus drei Vorschlägen „Gyroid zur Plasmaseite feiner“ | Abgestufter Gyroid: vorn fein, hinten dicht | Streuung 40 %, Plasmaseite ~10 cm/s |
| f3 | Nutzer: Eintritt um 180° drehen, nach innen | Eintritt innen, Kammern als Keile | **Nutzer: „erst aufrufen, die Kommunikation über Geometrie gestaltet sich schwierig“** |
| f4 | **Nutzer schickt ein Bildschirmfoto mit zwei roten Linien** | Kern zwischen zwei schrägen Ebenen, Kammern laufen keilförmig aus (Z-Verteiler) | Nutzer: „ja genau so“ |
| f5 | Nutzer: plasmaseitig mehr Wasser, außen weniger | Außenschicht dichter | Streuung 20 %, Plasmaseite 13,7 cm/s, außen praktisch zu |
| f6 | Nutzer: vordere Schicht dünner, Strömung als Film | Vorne 0,12 m, Zelle 0,12 m | Plasmaseite 20 cm/s, aber Streuung 47 %: innen doppelt (Kern innen 0,4 m statt 1,33 m lang), bei ±52° Kanäle unterbrochen (Schicht nur 1 Zelle dick); Film in Blender |
| f7 | Nutzer: „setze den nächsten Schritt um“, Film durchsichtig | Vorne 0,13 m, Zelle 0,10 m (1,3 Zellen), Wand vorn innen dicker (Halbdicke 7,2 mm bei R 5,2 m → 5 mm ab R 7,3 m) | Schlechter: innen zu (Wand zu dick, Drosselung reagiert sehr steil), ±52° weiter fast null, 42 kPa. Vermutete Ursache für ±52°: Grenze der feinen Schicht zu kurz (stellte sich in f8 als falsch heraus) |
| f8 | (Assistent: Fehler aus f7 beheben) | Grenze der feinen Schicht als exakte Versatzfläche aus Python; Wand vorn sanft abgestuft 6,2 → 5,0 mm | ±52° unverändert null, innen zu stark gedrosselt. Echte Ursache: Die Innenhaut (PicoGK-Offset 180 mm) ist an der Schulter ~50 mm zu dick und verengt das Band |
| f9 | (Assistent) | Alle Wandflächen als exakte Versatzflächen; Wand vorn innen 5,35–5,75 mm | ±52° weiter null, innen jetzt zu offen. Eigentliche Ursache gefunden: FluidX3D wandelt das Wassernetz an fast waagerechten Flächen falsch in Gitterzellen um, eine ganze Lage wird Stahl und sperrt das Band (betraf f6–f9) |
| f10 | Nutzer: „führe den nächsten Schritt aus“ | wie f9, Gitterzellen direkt aus PicoGK statt aus dem Netz | Einbrüche weg, Druckverlust 22,6 kPa (f9 37,8), Streuung 36 %, 288 l/s; innen zu viel, oben/unten zu wenig |
| f11 | (Assistent) | Wand vorn nachgestellt: innen 5,8 mm, oben/unten 4,9 mm, außen 5,2 mm | **Streuung 8 %** (10,3–13,9 l/s je Sektor), 22,0 kPa, 288 l/s, Plasmaseite 10 cm/s; Film mit durchsichtigem Bauteil |

Was sich daraus gelernt hat:
1. **Der Nutzer findet Fehler, die die Rechnung nicht zeigt.** Die nicht durchgängigen Bohrungen (a/b) fielen durch
   den Hinweis des Nutzers auf, nicht durch ein Fehlerprotokoll. Seitdem prüft der Ablauf die Durchgängigkeit
   automatisch.
2. **Konstruktionsideen kommen vom Menschen.** Durchströmte Filamente statt Lochblech, der Eintritt innen und die
   schrägen Kammergrenzen (Z-Verteiler) waren Vorgaben des Nutzers. Der Assistent hat sie umgesetzt und
   nachgerechnet. Die beste Verteilung (f5) entstand aus der Skizze des Nutzers.
3. **Geometrie lässt sich schlecht mit Worten beschreiben.** „180° drehen“ ließ mehrere Deutungen zu (f3). Eine Skizze
   im Bildschirmfoto (f4) hat das Missverständnis sofort gelöst. Seitdem gilt: Bei Formänderungen zuerst ein grobes
   Modell zeigen, gern aus der Blickrichtung der Skizze (`draufsicht.py`).
4. **Rückfragen nur, wo die Entscheidung beim Nutzer liegt.** Gefragt wurde zum Beispiel nach Segmentlage,
   Verteilprinzip, GPU-Nutzung, Lizenz und Aufräumen. Technische Einzelheiten wie Gitterweite, Zellgröße und
   Porosität legt der Assistent selbst fest und nennt sie.
5. **Vorschläge machen, nicht entscheiden.** Nach jeder Rechnung nennt der Assistent zwei bis drei mögliche
   nächste Schritte. Der Nutzer wählt aus („mach 2“) oder bringt eine eigene Idee ein.
6. **Einem merkwürdigen Ergebnis nachgehen, bevor man daran dreht.** Die Einbrüche bei ±52° (f6–f9) sahen nach einem
   Konstruktionsproblem aus. Drei Vermutungen (Schichtdicke, Lage zum Gyroid, PicoGK-Offset) erwiesen sich als falsch,
   zwei Zwischenbefunde waren eigene Messfehler. Die Ursache war die Umwandlung des Wassernetzes in Gitterzellen in
   FluidX3D: eine ganze Lage wurde zu Stahl. Seit f10 kommen die Gitterzellen direkt aus PicoGK und werden gegen das
   Netz geprüft. Die Zahlen von f6 bis f9 sind dadurch verfälscht; erst nach der Korrektur ließ sich die Verteilung
   in einem Schritt auf 8 % Streuung abgleichen (f11).

## 4. Skizzen als Eingabe

Skizzen sind eine vollwertige Eingabe, gleichrangig mit Text. Für Geometrie sind sie oft die bessere Sprache.

So läuft es ab:
1. **Der Nutzer zeichnet in ein Bildschirmfoto.** Grundlage ist ein Bild des Assistenten oder ein Blick aus dem
   3D-Fenster. Darauf zeichnet der Nutzer zum Beispiel Linien, Pfeile oder Flächen in Rot und hängt das Bild an die
   Nachricht, gern mit einem kurzen Satz dazu („die Gyroide zwischen den roten Linien, beachte Winkel und
   Orientierung“).
2. **Der Assistent liest die Skizze.** Er klärt die Blickrichtung („von oben, außen links, Torusmitte rechts“), wo
   jede Linie beginnt und endet (Ecke, Stutzen, Stirnplatte) und welche Winkel und Breiten sie ungefähr hat. Daraus
   werden Parameter. Bei f4 wurden die roten Linien zu zwei senkrechten Ebenen, die Endpunkte zu `kammer_ein`
   (Breite innen) und `kammer_aus` (Breite außen).
3. **Der Assistent antwortet im selben Bild.** Das neue Modell wird aus **derselben Blickrichtung** gerendert wie die
   Skizze (`stellarator/draufsicht.py`). So kann der Nutzer Skizze und Modell direkt nebeneinander vergleichen.
4. **Der Nutzer bestätigt oder zeichnet nach.** Erst nach „ja genau so“ wird fein gebaut und gerechnet.

**Skizzen-Werkzeug** (`stellarator/skizze.py` + `skizze.html`): Das Werkzeug läuft lokal im Browser
(`.venv/bin/python -m stellarator.skizze`, dann http://127.0.0.1:8765).
- Modell wählen, drehen, auf vorbereitete Ansichten springen (Oben, Außen, Innen, Schräg).
- Mit `Z` in den Zeichenmodus wechseln und farbige Linien direkt aufs Bauteil ziehen. Jede Linie bekommt eine Nummer,
  auf die sich der Text beziehen kann.
- Text dazuschreiben und „An Claude senden“ drücken.

Gespeichert wird unter `sim/skizzen/<zeit>/`:
- `skizze.png`: das Bild mit den Linien
- `skizze.json`: Text, Kamera und jede Linie als Bildpunkte **und** als 3D-Punkte auf dem Bauteil (x, y, z, R, φ)

Der Assistent muss die Skizze also nicht schätzen, er kennt die Punkte genau. Während der Sitzung wartet ein Wächter
auf `sim/skizzen/neu.txt` und meldet neue Skizzen sofort.

Eine allgemeine Fassung für beliebige STL-Modelle und jede KI steht als eigenes Repo bereit:
[sketch-to-prompt](https://github.com/ThomasSchmiegelt/sketch-to-prompt). Sie schreibt zusätzlich eine `prompt.md`
zum Einfügen in einen KI-Chat.

Erfahrungen:
- Eine Skizze hat das Missverständnis aus f3 auf Anhieb gelöst. Zwei Textrunden hatten das nicht geschafft.
- Neigung, Endpunkte und welche Seite breit oder spitz ist, gehen aus einer Skizze eindeutig hervor. In Worten bleibt
  das leicht mehrdeutig.
- Skizzen bleiben als Quelle erhalten. In der Variantentabelle steht, welche Variante aus welcher Skizze entstand.

## 5. Befehle (Beispiel f6)

```bash
# Geometrie (PicoGK), Kern zwischen schraegen Ebenen, Eintritt innen, abgestufter Gyroid
.venv/bin/python -m stellarator.kuehlung_segment --name f6 --ohne_platte --ein_innen --schraeg --dT 10 \
    --d_ein 300 --d_aus 400 --kammer_ein 420 --kammer_aus 600 \
    --schicht 0.12 --zelle_vorn 0.12 --halbdicke_vorn 6 --zelle 0.3 --halbdicke 43 --voxel 8
.venv/bin/python -m stellarator.draufsicht f6              # Bild von oben zum Abgleich mit der Skizze
.venv/bin/python -m stellarator.modell_ansicht f6          # interaktiv (s = Stahl ein/aus)

# Stroemung (FluidX3D): Probelauf, Durchgaengigkeit, volle Rechnung, Auswertung
.venv/bin/python -m stellarator.kuehlung_cfd --name f6 --dx 8 --probe --stat 10
.venv/bin/python -c "from stellarator.kuehlung_cfd import durchgaengig, WURZEL; print(durchgaengig(WURZEL/'f6'))"
.venv/bin/python -m stellarator.kuehlung_cfd --name f6 --dx 8 --t_phys 40 --stat 4000
.venv/bin/python -c "from stellarator.kuehlung_cfd import auswerten, WURZEL; auswerten(WURZEL/'f6')"

# Animation: Teilchen durch das Feld, Stahl unten aufgeschnitten und ohne Innenhaut, Blender-Bilder, Film
.venv/bin/python -m stellarator.stroemung_animation --name f6
picogk/StlSchnitt/bin/Release/net9.0/StlSchnitt sim/kuehlung_segment/f6/stahl.stl 12 0 \
    sim/kuehlung_segment/f6/animation/stahl_unten.stl sim/kuehlung_segment/f6/animation/schnitt.stl \
    sim/kuehlung_segment/f6/plasma.stl 180
blender -b -P stellarator/blender_stroemung.py -- sim/kuehlung_segment/f6
```

Ab f11:
- Film mit durchsichtigem Bauteil: `--durchsichtig`.
- Kamerafahrt in die Gyroid-Filamente: `--gyroid`.
  - Dafür die untere Hälfte mit 6-mm-Voxeln schneiden. Die Innenhaut wird über die exakte Fläche
    `flaeche_haut_innen.stl` + 12 mm abgenommen.
  - Ablage in `animation_gyroid/`.
- Grobe Wärmeabschätzung: `.venv/bin/python -m stellarator.kuehlung_waerme --name f11`.
- Gesamtbild mit den Erkenntnissen: `.venv/bin/python -m stellarator.gesamtbild_kuehlung`.

## 6. Grenzen der Rechnung

- Das Lattice-Boltzmann-Gitter hat 8 mm. Feine Gyroid-Kanäle (< 40 mm) sind nur mit wenigen Zellen aufgelöst,
  sehr dichte Schichten schließen sich im Gitter ganz.
- Gerechnet wird kaltes Wasser ohne Wärme. Der Wärmeübergang ist mit Dittus-Boelter für heißes Druckwasser grob
  geschätzt, ohne die Rippenwirkung der Filamente.
- Die Animation zeigt Teilchen im **stationären** Endfeld, nicht die zeitliche Entwicklung. Die Zeit im Film ist
  gerafft.

## 7. Was die Strömungsrechnung für die Kühlung bedeutet (Stand f11)

Die Verteilung über den Umfang ist gelöst (8 % Streuung). Die Kühlung der Plasmaseite reicht aber noch nicht.
Grobe 1D-Abschätzung bei 0,5 MW/m², Druckwasser 300 °C:

| Engstelle | Temperaturabfall |
|---|---|
| Innenhaut 30 mm (Stahl, k = 25 W/mK) | 600 K |
| Innenhaut 5 mm | 100 K |
| Übergang ans Wasser bei 0,10 m/s (f11), ohne/mit Rippenwirkung | 415 K / 210 K |
| Übergang bei feinen Kanälen 10 mm und 1 m/s | 48 K |

Auf 10 % der Plasmaseite liegt die Geschwindigkeit unter 1 mm/s.

Vorschläge, ungefähr nach Wirkung geordnet:
1. Innenhaut 3–5 mm.
2. Plasmaseite schneller durchströmen: dünnere vordere Schicht oder eigener Erstwand-Kreislauf mit ~1 m/s.
3. Totwasser lokalisieren und beseitigen.
4. Mit Drosseln abgleichen statt mit der Wanddicke. Diese reagiert sehr steil: ±0,1 mm ergibt etwa ±13 % Durchfluss.
5. Wärme gekoppelt rechnen.
6. Gitterstudie mit 4–6 mm.
7. Durchfluss auf Soll bringen (288 statt 319 l/s, Ursache Randbedingung).

## 8. Nächste Schleife: doppeltes Filament, Bauraum, Flüssigblei (2026-10-27)

So lief der Austausch zwischen Nutzer und KI:

| Nutzer | KI |
|---|---|
| „Die Schnitte durch das Fluid sind nicht so toll“ – Wunsch nach einem Werkzeug mit „Senden und nächster Schnitt“ / „Senden und beenden“ | Browser-Werkzeug `stellarator/schnitt_werkzeug.py` (Ebene φ, z oder gezogene Linie; Größe, Stromlinien, Ausschnitt), Skill `stroemung-schnitte` |
| Wasser höchstens 150 °C, Eintritt 60 °C; doppeltes Filament (innen Kühlung, außen Steifigkeit); darf nicht mit den Spulen kollidieren | `erstwand_kanal.py`: parallel siedet es, also 3 Kanäle in Reihe; n5: 6×6 mm, 49 kPa, Stahl ≤ 300 °C, Kanalwand 202 °C < 212 °C. `gefaess_abstand.py`: mindestens 1,25 m zu den Gehäusen, Wand braucht 1,10 m |
| (Bild zeigen) | Wandstück in PicoGK (`picogk/WandStueck`) und Blender, beschriftet |
| „Gyroid im Gyroid“: plasmanah flüssiges Blei, das an Wasser abgibt | `blei_kanal.py`: Blei erstarrt am Wasser, Leck gefährlich, MHD bremst quer zum Feld. Toroidale Kanäle 247 kPa, Gyroid 14 MPa. Vorschlag: Blei toroidal, Dampferzeuger außerhalb der Spulen, Stahl ≤ 537 °C (b5) |
| Namen auf das Bild, aber „©“ wirkt gewerblich; FluidX3D nennen, ohne den Autor im Fließtext | Zeile „privates Hobbyprojekt, nicht kommerziell“ + „Strömung: FluidX3D“; Autorennamen nur noch dort, wo die Lizenz sie verlangt (Lizenzdatei, Kopfzeilen, Pflicht-Zitate) |

Was dabei auffiel:
- Die Ideen kamen auch hier vom Nutzer. Die KI hat sie durchgerechnet und die Grenzen benannt. Beim Blei war
  die Antwort „ja, aber anders“: Der Gyroid passt nicht zum Flüssigmetall, die Grundidee schon.
- Eine Sitzung ist mitten in der Arbeit abgestürzt. Weitergearbeitet wurde mit „mach weiter“; die Übergabe
  stand in der Zusammenfassung und in `ERINNERUNGEN.md`.
- Ein bequemer Schritt ging fast schief: Ein Bild im Bericht wurde überschrieben, bevor nachgesehen wurde, was
  darin war. Es war zum Glück dasselbe Bild. Die Regel „erst ansehen, dann überschreiben“ gilt auch für Bilder.

## 9. Bewerten, Festigkeit, Recherche und Wärmebilanz (2026-10-28)

| Nutzer | KI |
|---|---|
| f12: Wand 5 mm, Austritt größer; „nach dem Lauf alles beenden“ | f12 lief über Nacht, die Auswertung fehlte (lief nicht automatisch) und wurde nachgeholt: 11 % Streuung, 19,4 kPa, Wand 100 K statt 600 K |
| Hermes recherchiert schlecht („ne 5“), PI soll es mit Scraping-Fähigkeit versuchen | Skill `web-recherche` (suche/abruf/pruefe.py): nur offizielle Schnittstellen, jeder Wert mit wörtlichem Zitat, Prüfprogramm |
| „So viel kann der sich gar nicht merken“ | Umbau auf eine Anlage je PI-Aufruf, Datei als Gedächtnis: 29 Belege, 0 Fehler; zwei Deutungsfehler beim Gegenlesen gefunden |
| Vorgehen per Paarvergleich festlegen, auch für Optimierungsschleifen; Urteile zu 6 Kriterienpaaren | `varianten_vergleich.py`: Pareto + AHP; Gewichte Temperatur 0,61, Druckverlust 0,23; Rang f12 vor f5 |
| „Die Wandung des Druckraums muss entsprechend gestaltet sein“ | `haut_festigkeit.py` (Elmer): 5-mm-Haut hält nur ~3,8 MPa; Hochdruckwasser nur in kleinen Kanälen |
| Bestehende AKW-Turbine verwenden, Rest möglichst einfach | Druckwasser wie WWER-1000; Erstwandkanäle nachgerechnet (Stahl 441 °C); `waermebilanz.py`: 3053 MW Fusion, eine Turbine der Konvoi-Klasse reicht |
| Dokumentieren, im Bericht mit Herleitung | Kapitel „Kühlmittel, Festigkeit und Wärmebilanz“ in beiden Berichten |
| „Das Kühlsystem ist noch nicht fertig, oder?“ – ja, weiter, Dokumentation erweitern | Offene Teile nach Wärmemenge geordnet (Blanket 82 %); zuerst das größte Risiko geprüft: Leitungen durch die Spulenspalte (`rohr_durchfuehrung.py`) – passen reichlich (11 nötig, ~410 möglich bei 0,8 m) |
| Lädt das WCLL-PDF herunter (Verlag sperrte den automatischen Abruf) | 13 Werte wörtlich belegt; Abgleich: Druckwasser bestätigt, PbLi als Brutstoff, Wandlast doppelt so hoch wie DEMO |
| „Eines der großen Probleme ist wahrscheinlich, dass der Gyroid punktuell aufliegt“ | Als offener Punkt aufgenommen (Kerben an den Anschlusslinien, Ermüdung); Abschätzung im Chat |
| Flächige Auflage an der Haut, Stränge nicht zu dicht (Wasser) und dick genug (Wärme), nach außen verästelt und dünn | Regeln aus Überschlag: Stützabstand ≤ 20 mm bei 16 MPa; Rippen wirken nur 3–15 mm tief; Stahlquerschnitt überall ≥ 11 %; Hautlage braucht eigene Zuführung |
| „Baue es mal, mich interessiert wie es aussieht“; testen auf Durchströmung und Festigkeit | `picogk/GradientWand`: 4 Lagen (Zelle 20/40/80/160 mm), überblendete Gyroid-Felder, Ausrundung 1,5 mm; Bilder in Blender; Wasserraum für den Test mit ausgegeben |
| „Wie bekommen wir die Wärme in die Breite und leiten den Wärmefluss nach außen?“ – erst pushen, dann Wärmetest | Überschlag (Ausbreitungslänge, Rippentiefe) im Chat, dann `gradient_waerme.py`: Elmer an 1,4 Mio. Voxeln, 5 Fälle. Stahl gibt 95 % in 5 mm ab, nur Kupfer bringt Wärme in die Tiefe. Zwei Gegenproben (Kupfer, h doppelt) von der KI ergänzt, damit der Hebel sichtbar wird |

Was dabei auffiel:
- Der Paarvergleich hat sofort etwas gezeigt: f11 war auf ein Ziel optimiert, das der Nutzer gering gewichtet.
- Die Festigkeitsfrage des Nutzers hat eine ganze Linie (Wasser im Gyroid) beendet. Ohne sie wäre f13 gerechnet worden.
- Lokale Agenten taugen für Recherche nur in kleinen Stücken mit maschineller Prüfung; die Deutung muss trotzdem
  jemand gegenlesen.
- Die Entscheidung für eine vorhandene Turbine hat mehr vereinfacht als jede Rechnung: Druck, Temperatur und
  Kühlmittel stehen damit fest.
- Die Rückfrage des Nutzers („noch nicht fertig, oder?“) war berechtigt: Die Wärmebilanz hatte das Blanket nur als
  Zahl geführt. Erst die Liste nach Wärmemenge zeigte, wo das eigentliche Kühlsystem liegt.
- Die Sorge über den 0,58-m-Spalt war zu pessimistisch; sie galt nur innen. Rechnen statt schätzen hat sich gelohnt.

## 10. Divertor-Vorwärmer als Zwei-Fluid-Tauscher (2026-10-31)

| Nutzer | KI |
|---|---|
| Gyroid lieber als Zwei-Fluid-Tauscher, Kondensator-Abwärme „verrückt“, der Reihe nach Richtung Forschung | Fahrplan: Frage, Literatur, Validierung, Bandbreiten, Review-Paket, Fachleute, Versuch; Start mit dem Divertor-Vorwärmer |
| „Effizienz ist für mich wichtiger, danach ist der Vorwärmer auszuwählen“ | Frage und Maß: Netto = Mehrleistung der Turbine − Pumpleistung; H1: TPMS gewinnt bei gleichem Pumpaufwand |
| Lädt gesperrte Volltexte von Hand herunter (Renon, Übersicht 2026) | 23 + 13 + 9 Belege wörtlich geprüft; PI fand zum Divertor nichts, die KIT-Kopie fand Claude |
| „Nimm den Notbehelf“ (Platte ohne eigene Korrelation) | Platte = gleichmäßiger Gyroid mit Band bis +10 %, abgestuft +28 %, Rohr nach Gnielinski |
| Englische Wikipedia ist bei Technik oft besser | EPR gegengeprüft: 77,2 bar am Eintritt; Kreislaufdaten stehen nur in der deutschen Fassung |
| Rechtlich korrekt zitieren | Lizenzen aus den Volltexten geprüft (CC BY, CC BY-NC, CC BY-NC-ND, KIT ohne CC) und in die Belegdateien geschrieben; Hinweis zu §§ 51, 63 UrhG in beiden Berichten |
| Fragt, ob der kompakteste Tauscher auch der effizienteste ist | Nur bei knappem Bauraum: Ab ~30 m³ liefern alle Bauarten dasselbe |

Was dabei auffiel:
- Das Ergebnis widerspricht der Erwartung beider Seiten: Nach Wirkungsgrad lässt sich die Bauart nicht wählen, die
  Unterschiede liegen im Volumen. Gewählt wird also nach anderen Kriterien.
- Die Rechnung hat eine ältere Vereinfachung aufgedeckt: Die Wärmebilanz zählte die Divertorwärme mit vollem
  Wirkungsgrad.
- Ein Modellfehler (gleiche Re auf beiden Seiten unmöglich) zeigte sich erst, als eine Empfindlichkeitsrechnung keine
  gültigen Punkte mehr fand. Daraus wurde ein Befund: Das Verhältnis 7:1 der Massenströme verlangt mehrere Durchgänge.

## 11. Leistungsfluss, Bauteile und Strömungsrechnung der Tauscher (2026-10-31)

**Anstoß durch den Nutzer.** Drei Wünsche kamen nacheinander: die Module „mal bauen“, sie mit FluidX3D gegeneinander
rechnen (Platten lieber in FreeCAD) und die Rechnung als Video zeigen. Dann kam eine neue Frage: ein Wissens- oder
Einflussgraph vom Plasma bis dorthin, wo der Strom das Kraftwerk verlässt. Der Nutzer wollte ihn in der Doku sehen,
dazu eine Erklärung jedes Bauteils („Divertor, was macht der, wozu wird der gebraucht“). Diese Arbeit schlug er vor,
an ein kleineres Modell (Sonnet) auszulagern.

**Arbeitsteilung.** Claude baute den Graphen zuerst als interaktive Webseite und dann als Bild für den Bericht. Ein
Sonnet-Teilagent schrieb die 13 Bauteiltexte (DE, EN, Markdown) mit abgerufenen Quellen, bevorzugt englische
Wikipedia. Claude prüfte danach jede Projektzahl der Texte gegen den Bericht. Eine Aussage ohne Beleg wurde
gestrichen: dass Transformatorverluste „im Eigenbedarf stecken“. Der Teilagent hatte selbst offene Punkte gemeldet,
zum Beispiel dass keine Quelle ausdrücklich sagt, der Divertor pumpe Helium ab.

**Strömungsrechnung.** OpenFOAM schafft der Rechner nach Aussage des Nutzers nicht; deshalb FluidX3D. Der Weg dahin
hatte mehrere Fehlschläge:
- Ein- und Auslass bei Re 3000 sind im Lattice-Boltzmann-Verfahren nicht machbar (über 25 % Dichteunterschied).
  Deshalb wurde auf ein periodisches Gebiet umgestellt.
- Das Temperaturmodell hat eine andere Schallgeschwindigkeit. Die Diffusivität ist halb so groß wie angenommen;
  ein Diffusionstest belegte das.
- Die Wand lag eine Zelle zu tief, das ergab Nu dreimal zu hoch. Abhilfe brachte ein Anti-Bounce-Back an Festzellen.
- Die Temperatur wurde bei Re 3000 instabil. Abhilfe brachte eine turbulente Diffusivität aus dem LES-Modell.
- Ergebnis: Der laminare Prüffall stimmt. Die Hydraulik des Gyroids liegt im Literaturband, der Wärmeübergang noch
  etwa doppelt zu hoch. Die feinste Rechnung divergierte. Das ist offen und steht so im Bericht.

**Ressourcen.** Der FreeCAD-Bau der Chevron-Platten brauchte zu viel Arbeitsspeicher und endete ohne STL. Er muss
sparsamer neu gebaut werden.

**Nachtrag: Instabilität gefunden und Bauarten verglichen.** Der Nutzer gab die drei offenen Posten frei
(„ja mach die drei posten“) und wollte danach den Bericht vervollständigt haben. Die Spur zur Ursache:
- Die feinste Rechnung war nicht langsam weggelaufen, sondern in wenigen hundert Schritten explodiert. Das wies auf
  den BGK-Stoß nahe τ = 0,5 hin, nicht auf einen Fehler in Geometrie oder Quelle.
- Der TRT-Stoß lief stabil. Er senkte Nu auch auf dem groben Gitter um etwa 25 %. Der alte Wert war also schon vor dem
  Absturz verfälscht.
- Danach prüfte Claude, ob die Korrelation (Renon) Geschwindigkeit, d_h und Reibung gleich definiert. Das tut sie.
  Übrig blieb ein Unterschied in der Randbedingung: Eine gleichmäßige Wärmequelle hebt Nu. Die Quelle ∝ u_z (Patankar
  1977) hat im Plattenkanal einen exakten Prüfwert. Damit ließ sich zeigen, dass der Rest ein Gitterfehler ist.
- Die Reihe mit sechs Läufen lief in gut 40 Minuten. Gyroid und Diamond sind gleich gut, Chevron etwa 15 % schlechter.
  Nu liegt bei 96 Zellen noch 1,5-fach über der Korrelation, geschätzt etwa 1,2-fach bei unendlich feinem Gitter.

Gelernt: Ein Prüffall mit exakter Lösung je Randbedingung ist mehr wert als ein Vergleich mit streuenden
Korrelationen. Jeder Schritt (Wand, Diffusivität, Stoß, Quelle) wurde erst daran bestätigt.

## 12. Surrogat aus 40 Strömungsrechnungen und die Frage der Stufung (2026-11-01)

**Anstoß durch den Nutzer.** Er fragte: „würde eine dritte gitterstufe das surrogat besser machen“ und danach, was man
mit dem Surrogat anfangen könne. Claude schlug ein mehrstufiges Surrogat vor: wenige feine Läufe für den Gitterfehler,
viele grobe für die Fläche. Der Nutzer gab es mit Auflagen frei: „führe es so aus, das ich es pausieren kann.
monitoring mach mit sonnet. schreib auch das ereignissprotokoll mit.“

**Umsetzung.**
- Eine Auftragsliste mit Runner und Steuerskript: `pause`, `sofort` (hält die GPU an), `weiter`, `stop`, `abbruch`,
  `start`. Fertige Aufträge werden beim Neustart übersprungen.
- Ein Sonnet-Teilagent prüfte etwa alle fünf Minuten Speicher, Platte, GPU und Divergenz. Er durfte nur pausieren.
  Er lief zweimal je 40 Runden und musste nie eingreifen.

**Überraschung.** Die dritte Gitterstufe passte nicht zur Ordnung aus dem Plattentest. Der Schritt 96→144 war größer
als erwartet, keine positive Konvergenzordnung erklärt die drei Werte. Die Schätzung von gestern (Nu etwa 1,2-mal
Renon) war deshalb zu hoch; extrapoliert liegt Nu bei Renon. Für die Reibung ging die Extrapolation sogar ins
Unphysikalische. Claude hat deshalb zwei obere Stufen eingeführt: gerechnet (n144) und geschätzt (Gitter → ∞). Der
Abstand zwischen beiden dient als Unsicherheit, statt eine Zahl vorzutäuschen.

**Antwort auf die Ausgangsfrage.** Die Stufung bringt im Divertor-Vorwärmer nichts. Ein Segmentmodell mit freier Zelle
je Segment wählt überall die kleinste Zelle. Der Literaturfaktor 1,28 für die Stufung entspricht hier ungefähr dem
Abstand zwischen der Korrelation und dem gerechneten Surrogat. Eine erste Fassung des Vergleichs war unfair: Die
Literaturkurve stammte aus einem anderen Modell mit anderem Zellbereich. Claude hat sie im selben Segmentmodell
neu gerechnet.

Gelernt: Eine dritte Gitterstufe lohnt sich gerade dann, wenn sie die Schätzung aus zweien widerlegt. Eine
Optimierung, deren Bestwert am Rand des erlaubten Bereichs liegt, beantwortet vor allem die Frage nach dem Rand.

## 13. Plasma: Woher kommt die Wärme? (2026-11-01)

**Anstoß durch den Nutzer.** Nach dem Push des Surrogats kam der Wunsch: „danach plasma also woher kommt die wärme
und wie entsteht sie“. Während der Arbeit kamen zwei Ergänzungen: das Ereignisprotokoll mitschreiben und die README
und die Kurzbeschreibung auf GitHub ergänzen.

**Vorgehen.** Claude hat keine neue Physik eingeführt, sondern die Zahlen der eigenen Stufe-0-Auslegung von unten her
nachgerechnet:
- Massendefekt mit Atommassen, Coulombwall, Gamow-Fenster, Lawson-Minimum.
- Leistungsdichte mit denselben Profilen wie Stufe 0. Die Summe trifft die 3053 MW auf 0,1 % und bestätigt so die
  Kette.
- Fremde Fakten (Li-6-Reaktion, Heizung von W7-X) wurden in der englischen Wikipedia abgerufen und wörtlich geprüft,
  Fachartikel per Crossref.

**Befund, der zurückwirkt.** Die Plasmabilanz (611 MW Alphaheizung = 482 MW Transport + 129 MW Strahlung) zeigt, dass
die frühere Annahme „Hälfte auf den Divertor“ nur mit zusätzlicher Abstrahlung am Rand gilt. Das geht als offene
Aufgabe in die Divertor-Auslegung. Damit stellt die Rechnung eine frühere eigene Annahme in Frage, statt sie nur
zu erklären.


## 14. Bilder für Nicht-Physiker erklären (2026-11-01)

Der Nutzer bat darum, alle Bilder im Bericht so zu erklären, dass auch Nicht-Physiker sie verstehen. Die KI hat
dazu alle 41 Abbildungen noch einmal angesehen und unter jede einen kurzen Absatz „So liest man das Bild“ gesetzt,
auf Deutsch und auf Englisch. Er sagt, was zu sehen ist (Achsen, Farben, Linien in Alltagssprache), worauf man
achten soll und was daraus folgt. Fachwörter wie Vergleichsspannung, Poincaré-Schnitt oder Reynolds-Zahl werden
dort in einem Halbsatz erklärt. Das gilt ab jetzt als feste Regel für jedes neue Bild. Die Bildunterschriften
allein waren für Fachleute geschrieben; erst der Nutzer machte die Leserschaft ohne Physikstudium zum Maßstab.

## 15. Flüssigmetall im Magnetfeld, Stufe 2, und der Divertor-Vorwärmer in Alltagssprache (2026-11-01)

Nach dem Push des Plasma-Teils bat der Nutzer um Stufe 2 der MHD-Rechnung. Die KI baute in die eigene FluidX3D-Kopie
einen Löser für das elektrische Potential ein (Jacobi-Schritte auf der GPU, Strombilanz über die Zellflächen). Zur
Prüfung entstand ein unabhängiger 2D-Löser in einer anderen Formulierung (induziertes Feld statt Potential). Drei
Fehler zeigten sich erst durch Prüfen:

1. Im Vergleichslöser fehlte in der Randbehandlung ein Term. Das fiel am bekannten Wert für den quadratischen Kanal
   ohne Feld auf (f·Re = 14,23).
2. Bei isolierenden Wänden wuchs der Fehler mit Ha bis 36 %. Ursache war die Reihenfolge der Kräfte im Kernel. Im
   Kern des Kanals heben sich zwei große Kräfte fast auf, deshalb verstärkt sich jeder kleine Widerspruch. Nach dem
   Tausch liegen alle zwölf Fälle unter 1 %.
3. Beim Nachrechnen der schon veröffentlichten Stufe 1 waren die Werte plötzlich zehnmal besser. Die alte Ausgabe
   hatte die halbe Lorentzkraft nicht enthalten, der Löser selbst war richtig. Die KI hat das offen korrigiert, statt
   die neuen Zahlen still einzusetzen.

Die Vergleichsrechnung bestätigt auch die frühere Faustformel für Blei (k_p gegen 1/Ha bei isolierenden Wänden).

Während der Rechnung fragte der Nutzer, wie der Divertor-Vorwärmer eigentlich funktioniert; das sei nicht
angekommen. Die KI erklärte ihn ohne Formeln: zu kalte Divertorwärme, Kondensat vorwärmen, Anzapfdampf sparen, dazu
ein Vergleich aus dem Alltag. Der Nutzer wollte das im Bericht haben. Dazu kam die Bitte, Begriffe wie „leitende
Hartmann-Wände“ zu erklären. Daraus wurden eine Prinzipskizze mit Lesehilfe vor den Formeln, ein Begriffskasten im
MHD-Kapitel und eine feste Regel: erst die Funktion in Alltagssprache, dann die Formel. Wieder war es der Nutzer als
Leser, der den Maßstab für Verständlichkeit setzte.

## 16. Alphateilchen im Feld der Spulen (2026-11-01)

Der Lauf mit 1000 Alphas (Variante A der „dynamischen Simulation mit dem Magnetfeld“) ist ausgewertet. 16,6 % gehen
verloren, fast nur gefangene Teilchen und langsam, nicht in den ersten Umläufen. Mit der Abbremsung gewichtet sind
das 11,6 % der Alphaenergie, also 71 MW. Die Treffer am Plasmarand sind gebündelt: im heißesten Feld etwa
2,4 MW/m², fast das Fünffache der Wandauslegung.

Damit stellt die Rechnung eine stillschweigende Annahme der Plasma-Bilanz in Frage: dass alle Alphas ihre Energie im
Plasma abgeben. Die Ursache ist offen. Die Plasmaform ist sehr genau quasisymmetrisch, die Spulen treffen sie aber nur
auf etwa 0,3 % genau. Der nächste Schritt trennt beides.

Zum Prozess: Das erste Video zeigte alle Bahnen gleichzeitig und war für Laien unlesbar. Nach der neuen Regel
(Bilder für Nicht-Physiker) entstand ein Standbild mit genau drei Bahnen (umlaufend, gefangen, verloren). Im Video
zieht jede Bahn nur einen kurzen Schweif hinter sich her. Eine erste Bildbeschreibung behauptete mehr, als die Daten
zeigen (eine Wellenlinie als „letzter Umkehrpunkt“). Diese Deutung wurde gestrichen.

## 17. Vorher und nachher: Woher kommen die Alpha-Verluste? (2026-11-01)

Zwei Hinweise des Nutzers haben diesen Schritt geprägt.

**„Hast du dir die Bilder angeguckt? Kann das sein?“** Bis dahin wurden Bilder für den Nutzer geöffnet, aber von der
KI nicht selbst geprüft. Beim Nachsehen fielen zwei Dinge auf: Bahnen schienen außerhalb des Plasmas zu laufen, und
eine verlorene Bahn machte kurz vor dem Ende eine Spirale. Beides wurde nachgerechnet statt hingenommen. Ein Test
„liegt der Punkt im Querschnitt des Randes?“ für alle Bahnpunkte zeigte: Keine Bahn liegt außerhalb, der Eindruck
entsteht durch die Schrägansicht. Die Spirale ist echt: Das Alpha bleibt in einem kleinen Feldtal hängen, pendelt
dort kurz hin und her und driftet dabei nach außen. Das war der erste Hinweis auf die Ursache. Seitdem gilt:
**jedes Bild selbst ansehen und bewerten**, bevor es in den Bericht geht. Beim Vergleichsbild unten hat das gleich
dreimal geholfen: Balken mit drei verschiedenen Einheiten auf einer Achse, eine abgeschnittene Beschriftung und ein
deutsches Wort im englischen Bild wurden so gefunden.

**„Zuerst eine Erwartungshaltung definieren und dann mit dem Ergebnis vergleichen.“** Vor dem Kontrolllauf wurde im
Ereignisprotokoll festgelegt, was herauskommen sollte und wie jedes Ergebnis zu deuten wäre: Die Form allein sollte
unter 1 % verlieren (Landreman & Paul fanden für „precise QA“ keine Verluste). Unter 2 % hieße: Die Spulen sind die
Hauptursache; über 10 % hieße: Die Form selbst oder ein Rechenfehler. So kann man sich das Ergebnis hinterher nicht
zurechtlegen.

**Vorher – nachher.** Dieselben 1000 Alphas (gleiche Verteilung der Geburtsorte und Richtungen) wurden einmal im
Feld der Spulen und einmal im Feld der Plasmaform allein gerechnet:

| | Feld der 16 Spulen (vorher) | Feld der Form allein |
|---|---|---|
| verloren | 16,6 % ± 1,2 % | 0,3 % ± 0,2 % |
| davon gefangene | 95 % | 1 von 3 |
| Heizleistung verloren | 71 MW | 1,8 MW |

Die Erwartung ist bestätigt. Rund 98 % der Verluste kommen von der Ungenauigkeit der Spulen, nicht von der Form. Das
ist zugleich die Ausgangslage („vorher“) für den nächsten Schritt: Spulen nachoptimieren und dieselbe Rechnung
wiederholen („nachher“).

Technisch: Das Feld der Form wurde mit `booz_xform` in Boozer-Koordinaten umgerechnet. Zwei Stolpersteine in simsopt
(die VMEC-Anbindung wird nur mit mpi4py geladen; ein Hilfsobjekt wurde von Python zu früh aufgeräumt, dann fehlte eine
Feldgröße) kosteten Zeit, sind aber im Skript kommentiert. Der Lauf dauerte 27 Minuten.

## 18. Ein Film vom Plasma: realistischer, ehrlich, und Bild für Bild geprüft (2026-11-02)

Der Nutzer wünschte ein Video des „Plasmastroms“ mit höherem Realismus. Statt zu raten, fragte die KI nach: was zeigen
(Wahl: Plasma und strömende Teilchen) und wie realistisch leuchten (Wahl: physikalisch ehrlich). Ehrlich heißt hier:
Der 150 Millionen Grad heiße Kern sendet kaum sichtbares Licht; sichtbar leuchtet der kühlere Rand, vor allem
Wasserstoff, und das wirkt rosa. Die Teilchen sind zur Veranschaulichung vergrößert und etwa 50 000-fach verlangsamt;
das steht im Film.

Werkzeug ist Blender (Cycles auf der Grafikkarte). Alle Formen stammen aus den eigenen Rechnungen: Plasmarand aus dem
Gleichgewicht, 16 Spulen aus Stufe 2, die Teilchenbahnen sind Feldlinien im Feld dieser Spulen. Vor dem Rendern wurde
eine Erwartung festgelegt und gegen die Daten geprüft (Form, Verdrillung iota ≈ 0,42, Abstand Spulen–Plasma). Dabei
zeigte sich zweimal, dass nicht die Daten, sondern die eigene Kontrolle oder Erwartung falsch war – auch das gehört
ins Protokoll.

Die Regel „jedes Bild selbst ansehen“ fand vor dem Endlauf vier Fehler. Der lehrreichste: Die Innenansicht war
gleichmäßig rosa, auch bei viel weniger Belichtung. Messen statt raten ergab, dass die Flächen der leuchtenden
Randschicht verkehrt herum orientiert waren; Blender ließ deshalb den Kern und den Außenraum leuchten statt der dünnen
Schicht dazwischen. Nach dem Umdrehen entstand das erwartete Bild: heller Rand, dunkler Kern, Kacheln der Wand.

Während der Arbeit kam der Wunsch, den Film als **Rauszoomen** zu bauen: erst im Plasma (Detail), dann hinaus durch
den aufgeschnittenen Teil des Gefäßes bis zur Gesamtansicht. Die Kamerafahrt wurde entsprechend umgedreht. Jedes Bild
wird einzeln gespeichert; das Rendern lässt sich jederzeit anhalten (`~/bin/rechnung pause`) und nach einem Abbruch
fortsetzen.


## 19. Festigkeit: vom Killer zum ersten haltbaren Entwurf (2026-11-02)

**Anstoß durch den Nutzer.** Die Frage war, die offenen Punkte anzugehen, vor allem die Festigkeit, und dabei zu
überlegen, was kleinere Modelle übernehmen können. Auf die Rückfrage der KI, ob zuerst Wände, Spulen oder Plasma
optimiert werden sollen, kam die entscheidende Antwort: *„Wand, Spulen und Festigkeit sind ein Thema, das gehört
zusammen. Auch das Plasma gehört dazu … das ist auch cool für ein Surrogat.“* Später ergänzte der Nutzer das Package
und ein 3D-Modell als Ziel. Als der erste Testpunkt 2129 MPa zeigte, lenkte der Nutzer um: *„2000 MPa ist ein Killer,
auch 500 MPa ist viel. Vielleicht brauchen wir mehr Spulen, oder wir müssen verstehen, wie die Kraft entsteht.“*
Statt sofort viele Varianten zu rechnen, wurde daraufhin zuerst die Ursache gesucht. Das war der Wendepunkt.

**Arbeitsteilung.** Opus plante, legte vor jeder Rechnung eine Erwartung fest (Ereignisprotokoll F-112 bis F-125),
schrieb die Kopplung und bewertete. Sonnet recherchierte Grenzwerte mit Crossref-Prüfung (Opus prüfte eine
Stichprobe nach) und baute das Kraftziel in die Spulenoptimierung ein (Opus prüfte die Zahlen in den Ergebnisdateien
nach). Haiku erkundete die Schnittstellen des Festigkeitsmodells und übersetzte das Berichtskapitel.

**Was die Ursache war.** Die Kraftanalyse zeigte: Die größte Last sitzt auf dem fast geraden inneren Schenkel jeder
Spule, und ein gerades Stück kann eine Querlast nur durch Biegung tragen. Eine Handrechnung als Balken traf die FEM
(2100 gegen 2129 MPa). Zugleich zog jede Spule mit über 1 GN zur Anlagenmitte, war im Modell aber außen gelagert.
Tokamaks lösen genau das mit der D-Form und einem Stützzylinder innen. Daraus folgten die Versuche: Lager innen,
dann innen und außen, dann mehr und steifere Verbinder, dann dickere Wände: 2129 → 481 MPa.

**Was schiefging und was daraus wurde.**
- Das Feld am Leiter kam zuerst mit 6,4 T statt etwa 15 T heraus: auf der Mittellinie gemessen, wo sich das Eigenfeld
  aufhebt. Die Abweichung von der Erwartung fiel sofort auf.
- In der ersten Kraftgrafik sprangen die Anteile künstlich: Das Bezugssystem der Krümmung kippt an geraden Stücken.
  Beim Ansehen des Bildes erkannt, auf ein stabiles Bezugssystem umgestellt.
- Der Maßstab des alten Festigkeitsmodells war um 3 % zu groß, beim Bau der Kette entdeckt.
- Der erste Start der Entwurfsstudie brach nach 3 Minuten ab (Speicher bei 24 Spulen). Die Überwachung meldete das
  30 Minuten lang nicht, weil sie nur Logzeilen beobachtete. Seitdem überwacht sie auch das Prozessende, und jeder
  Entwurf läuft in einem eigenen Speicherrahmen. Der Ausweichlöser war zu langsam; stattdessen bleibt das Netz bei mehr
  Spulen gleich groß.

**Stand.** Drei Entwürfe halten alle Grenzen ein (20–24 Spulen, 22,6–28 kt Stahl). Sie gelten erst nach Nachrechnung
mit feinem Netz und nachgiebigem Stützzylinder. Bericht: Abschnitt „Festigkeit“ (DE/EN).

## 20. Auswertung der Entwurfsstudie, 3D-Modelle in PicoGK und zwei Listen (2026-11-03)

**Was der Nutzer wollte.** Am Vorabend hatte der Nutzer drei Dinge für den nächsten Tag notieren lassen: den
robustesten statt des leichtesten Entwurf (*„Das Gewicht ist nicht so wichtig. Es ist ja ein Gebäude.“*), genau zu
wissen, *welcher Stahl* verwendet wird (*„p99 Stahl kenne ich nicht“*, dazu ein Link auf eine Festigkeitstabelle),
und ein 3D-Modell komplett in PicoGK. Am Morgen kam der Auftrag: *„Starte die Auswertung, baue auch die
unterschiedlichen Modelle, auch die 3D-Modelle … erzeuge einen weiteren sehr ausführlichen Bericht, der sämtliche
Varianten darstellt und vergleicht.“* Kurz darauf schärfte der Nutzer nach: *„zwei Listen, eine mit den besten für
den Bericht, vielleicht auch Modelle, die knapp an der Grenze liegen, und einen Bericht mit allen, die geometrisch
darstellbar sind“*, und gab eine zweite Platte für Unbenutztes frei.

**Wie die Frage des Nutzers die Darstellung veränderte.** „p99“ war eine interne Abkürzung. Die Frage zwang dazu,
den Werkstoff sauber herzuleiten: 1.4429 (X2CrNiMoN17-13-3, AISI 316LN), Raumtemperatur aus der Tabelle des
Nutzers (Rp0,2 295 MPa), bei 4 K aus einer geprüften Messung (1070 MPa), Grenze 500 MPa als 2/3 der garantierten
4-K-Streckgrenze. Der Begriff heißt jetzt σ99 (99-%-Spannung), und zusätzlich werden Spannungskategorien
(Membran, Membran+Biegung, Spitze) ausgewiesen, wie Regelwerke sie verlangen.

**Was die Prüfung der eigenen Zahlen ergab.** Vor jeder Rechnung stand eine Erwartung im Ereignisprotokoll
(F-136, F-139, F-142). Drei davon wurden widerlegt, und gerade daraus kam das meiste Verständnis:
- Die Netzstudie sollte die Spannung um 5–25 % erhöhen; gemessen wurden 34–58 %. Ursache: Die Spitzen sitzen an den
  Verbinderanschlüssen und werden mit jeder Verfeinerung schärfer. Nur 0169 blieb stabil, er ist deshalb der
  empfohlene Entwurf.
- Beim ersten Versuch der Netzstudie wurden die Verbinder unbemerkt kürzer, weil ihre Länge in Stationen gezählt
  wird. Derselbe Effekt hatte elf Entwürfe der Studie mit gröberem Netz zu günstig gemacht. Sie wurden
  nachgerechnet, zwei fielen heraus. Der Ausweichweg „gröberes Netz“ wurde aus der Kette entfernt.
- Die Nutzer-Idee „bestimmte Bereiche schwächen“ wurde zuerst in der einfachsten Form geprüft (alle Verbinder
  weicher). Die Spannung stieg. Daraus wurde klar, dass die Verbinder der Entlastungsweg sind; die Idee muss örtlich
  wirken (weiche Enden, steifer Kern).

**3D in PicoGK.** Python übergibt nur Zahlen (Querschnitte, Plasmarand, Lagerorte); PicoGK baut alle Körper und
prüft Überschneidungen. Zwei Fehler auf dem Weg: Die Nachbearbeitung der 13-Millionen-Dreieck-Netze in Python wurde
vom Speicherwächter beendet, also rechnet PicoGK die Volumina selbst und exportiert nur ein grobes Bildnetz. Die
ersten Bilder zeigten flimmernde Schichtgrenzen und verdeckte Spulen; jetzt wird jede Schicht unter einem anderen
Winkel aufgeschnitten, und der Stützring ist vorne offen.

**Was organisatorisch schiefging.** Zweimal beendete ein Abbruchbefehl die eigene Shell, weil das Suchmuster auch
den eigenen Befehlstext traf. Ein Rechenlauf wurde versehentlich doppelt in denselben Ordner gestartet und nach
1,5 Minuten bemerkt. Weil Elmer und PicoGK zusammen den Speicher sprengen konnten, wartet der Katalog jetzt, bis die
Festigkeitsrechnungen fertig sind.

**Ergebnis.** Liste 1 (7 zulässige, 5 knapp verfehlte, 2 durch die Nachrechnung herausgefallene und zwei
Tragwerksversuche) steht im Projektbericht und mit Steckbriefen im neuen Variantenbericht; Liste 2 (alle geometrisch
darstellbaren Entwürfe) als Katalog im Anhang des Variantenberichts.
