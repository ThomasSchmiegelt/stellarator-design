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
