# Variantenfilm – alle Entwürfe der Studie doe1 / *All designs of study doe1*

Film: [varianten.mp4](varianten.mp4) · 84 s · 1920×1080 · 30 Bilder/s · Blender Cycles (GPU)

## Deutsch

**Worum es geht.** Die Entwurfsstudie doe1 hat 200 Stellarator-Entwürfe gerechnet (Plasma → Spulen → Package →
Festigkeit → Temperatur). 188 davon lassen sich bauen, ohne dass sich die Spulengehäuse durchdringen. Der Film zeigt
alle 188 und am Schluss die sieben, die alle Grenzen einhalten.

| Zeit | Was man sieht | Lesehilfe |
|---|---|---|
| 0–8 s | Der empfohlene Entwurf 0169 entsteht aus Würfeln, Schicht für Schicht von unten (0–4 s). Dann wird daraus eine glatte Fläche (ab 4 s). | PicoGK baut Geometrie aus einem Voxelraster auf statt aus Flächen wie ein CAD-Programm. Die Würfel sind **stilisiert und bewusst grob** (0,3 m, damit man sie bei einer 27 m großen Anlage sieht). PicoGK selbst rechnet bei uns mit 80 mm und zeigt keine Klötzchen: Jeder Voxel speichert den Abstand zur Oberfläche, daraus entsteht eine glatte Fläche. Ab 4 s sieht man genau dieses echte PicoGK-Netz, glatt, aber leicht wellig. In der nächsten Szene, wenn die Gehäuse glasig sind, wechselt der Film unbemerkt auf die exakte Fläche des Rechenmodells. Grau = Gehäuse, dunkler = Verbinder, rosa = Plasma. |
| 8–16 s | **Magnetfeld.** Die Gehäuse werden glasig, das Plasma durchsichtig. Weiße Feldlinien wachsen und winden sich um die Anlage. Dann färbt sich der Plasmarand. | Die Feldlinien sind berechnet: Biot-Savart aus den 24 Spulenbahnen mit dem echten Strom (14,7 MA je Spule), verfolgt über 168 m (2,5 Umläufe). Farbe des Plasmarands = Feldstärke \|B\| von 5,5 T (dunkelviolett) über Rot und Orange bis 7,5 T (hellgelb). Innen (zur Anlagenmitte) ist das Feld stärker. Kontrolle: auf der Achse 6,7 T, Auslegung 6,5 T. |
| 16–24 s | **Festigkeit.** Die Gehäuse werden leicht durchsichtig, dann erscheint die Spannung als Farbe; das Tragwerk verformt sich und federt zurück. | Von-Mises-Spannung aus der Elmer-Rechnung, auf derselben Fläche: dunkelblau 0 MPa, über Hellblau, Grün und Gelb bis Rot bei 600 MPa (Grenze 500 MPa). Die hellen Stellen liegen an den geraden Innenschenkeln, wo die Spulen gebogen werden. Verformung 150-fach überhöht (echt höchstens 19 mm). |
| 24–34 s | 15 „wilde“ Entwürfe, je 0,67 s | Die 15 Entwürfe, die am weitesten von den Grenzen entfernt sind, z. B. 0002 mit σ99 = 4721 MPa im Stahl (Grenze 500 MPa) oder 0121, das die Grenze der Neutronenbelastung (Fluenz) am weitesten verfehlt. Die Studie probiert bewusst auch Extreme aus. |
| 34–58 s | Alle 188 Entwürfe in einem Feld. Die unzulässigen versinken nacheinander, die schlechtesten zuerst. | Übrig bleiben die zulässigen. Gelbe versinken zuletzt: Sie haben eine Grenze nur knapp verfehlt. |
| 58–66 s | Die sieben zulässigen rücken in eine Reihe. | Reihenfolge nach Reserve: 0061, 0169, 0093, 0008, 0014, 0017, 0157. |
| 66–84 s | 0169 im Treppenschnitt, die Kamera kreist. | Von innen nach außen: Plasma (rosa), Erstwand + Blanket (gelb), Abschirmung (grün), Vakuumgefäß (hellgrau), Wickelpaket (orange), Gehäuse (blau), Verbinder (dunkelblau), Lager (fast schwarz). |

**Farbcode der Gehäuse:** blau = zulässig (alle acht Grenzen eingehalten), gelb = knapp verfehlt (kleinste Reserve
besser als −15 %), rot = deutlich verfehlt.

**Woher die Formen kommen.** Nichts im Film ist gezeichnet oder von einer Bild-KI erzeugt. Spulen, Gehäuse, Verbinder
und Wickelpaket sind die exakten Oberflächen des Festigkeitsmodells (dasselbe Netz, das Elmer rechnet). Plasma,
Package und Lager stammen aus den PicoGK-Modellen (80-mm-Voxel) und sind deshalb aus der Nähe leicht gerieft.

**Was nur schematisch ist.** Der Stützzylinder innen und der Ring außen zeigen, wohin die Lagerkräfte gehen. Sie sind
weder berechnet noch ausgelegt; im Rechenmodell sind die Lager starre Flächen.

**Wie der Film entstand.** Der Nutzer gab das Ziel vor („am Schluss die Varianten, die übrig bleiben“, „die wilden kurz
am Anfang“, erst sichtbar PicoGK, dann „schön“; später: je eine Szene, in der das Modell durchsichtig wird und die
Magnetfeld- bzw. Festigkeitsrechnung erscheint). Claude Code schrieb die Skripte, prüfte die Probebilder und verwarf
rund 200 Bilder (schwarze Flecken durch doppelte Voxel, zerknitterte Flächen aus zu groben Netzen). Blender hat
gerendert. Skripte: `stellarator/varianten_video_daten.py`, `varianten_video_rechnung.py` (Feld und Spannung),
`varianten_video_blender.py`, `varianten_video_schnitt.py`.

## English

**What it is about.** Design study doe1 computed 200 stellarator designs (plasma → coils → package → strength →
temperature). 188 of them can be built without the coil casings intersecting. The film shows all 188 and, at the end,
the seven that meet every limit.

| Time | What you see | How to read it |
|---|---|---|
| 0–8 s | The recommended design 0169 is built from cubes, layer by layer from the bottom (0–4 s). Then it becomes a smooth surface (from 4 s). | PicoGK builds geometry from a voxel grid instead of surfaces as in CAD. The cubes are **stylised and deliberately coarse** (0.3 m, so they are visible on a 27 m machine). PicoGK itself works with 80 mm here and shows no blocks: each voxel stores the distance to the surface, from which a smooth surface is formed. From 4 s you see exactly this real PicoGK mesh, smooth but slightly wavy. In the next scene, once the casings are glassy, the film switches unnoticed to the exact surface of the analysis model. Grey = casing, darker = connectors, pink = plasma. |
| 8–16 s | **Magnetic field.** The casings turn glassy, the plasma transparent. White field lines grow and wind around the machine. Then the plasma boundary takes on colour. | The field lines are computed: Biot–Savart from the 24 coil paths with the real current (14.7 MA per coil), traced over 168 m (2.5 turns). Colour of the plasma boundary = field strength \|B\| from 5.5 T (dark violet) via red and orange to 7.5 T (light yellow). The field is stronger on the inside (towards the machine centre). Check: 6.7 T on the axis, design value 6.5 T. |
| 16–24 s | **Strength.** The casings turn slightly transparent, then the stress appears as colour; the structure deforms and springs back. | Von Mises stress from the Elmer computation, on the same surface: dark blue 0 MPa, via light blue, green and yellow to red at 600 MPa (limit 500 MPa). The bright spots are on the straight inner legs, where the coils are bent. Deformation exaggerated 150× (real at most 19 mm). |
| 24–34 s | 15 "wild" designs, 0.67 s each | The 15 designs furthest from the limits, e.g. 0002 with σ99 = 4721 MPa in the steel (limit 500 MPa) or 0121, which misses the neutron load (fluence) limit by the widest margin. The study deliberately tries extremes. |
| 34–58 s | All 188 designs in one field. The inadmissible ones sink one after another, worst first. | The admissible ones remain. Yellow ones sink last: they missed a limit only narrowly. |
| 58–66 s | The seven admissible designs line up. | Ordered by margin: 0061, 0169, 0093, 0008, 0014, 0017, 0157. |
| 66–84 s | 0169 in a stepped cut, camera orbiting. | From inside out: plasma (pink), first wall + blanket (yellow), shield (green), vacuum vessel (light grey), winding pack (orange), casing (blue), connectors (dark blue), bearings (almost black). |

**Casing colour code:** blue = admissible (all eight limits met), yellow = narrowly missed (smallest margin better
than −15 %), red = clearly missed.

**Where the shapes come from.** Nothing in the film is drawn or made by an image AI. Coils, casings, connectors and
winding pack are the exact surfaces of the strength model (the same mesh Elmer computes). Plasma, package and bearings
come from the PicoGK models (80 mm voxels) and therefore look slightly ribbed close up.

**What is only schematic.** The inner support cylinder and the outer ring show where the bearing forces go. They are
neither computed nor designed; in the model the bearings are rigid patches.

**How it was made.** The user set the goal ("at the end the variants that remain", "the wild ones briefly at the
start", first visibly PicoGK, then "beautiful"; later: one scene each in which the model turns transparent and the
magnetic field or strength computation appears). Claude Code wrote the scripts, checked the test frames and discarded
about 200 frames (black spots from duplicate voxels, crumpled surfaces from too-coarse meshes). Blender rendered.
