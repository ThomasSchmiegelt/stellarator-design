# ANALYSE-001 — Stellarator: Funktion, Aufbau, Physik

**Stand:** 2026-10-22 · **Recherche-Basis:** arXiv (keyless), Wikipedia/FusionWiki,
IPP, FtI TOFE-Slides, HuggingFace; Elmer-Modelle-Manual (lokal /tmp/elmerdoc).
**Zweck:** Grundlage für die Modellierungs- und Simulationsentscheidungen in fusion.

---

## 1. Funktion: Warum Stellarator?

Ein Stellarator ist ein toroidal geschlossenes Plasmagefäß, in dem das Magnetfeld
**vollständig durch externe Spulen** erzeugt wird — im Gegensatz zum Tokamak, wo
ein großer Strom im Plasma selbst (Plasmaplasma ~2–8 MA, z. B. ITER) den
Toroidalfeldanteil liefert.

**Konsequenzen:**

| Eigenschaft | Tokamak | Stellarator |
|---|---|---|
| Plasmaplasma-Strom | groß, instabil (DIs, RWM) | 0 oder klein → **intrinsisch stabil** |
| Gleichgewicht | stationäres, aber Drift-Instabilitäten | **stationär** (steady state) |
| Magnetfeld | axisymmetrisch + helical (Sattelfeld) | **frei 3D-optimierbar** |
| Neoklassik-Transport | stark (Ripple) | **optimierbar** (Quasi-Omnigenität) |
| Komplexität | Plasma-Pulsations-System | **Spulen-System** (50+20 3D-Spulen) |

Kernidee: Die helikale Verformung des Feldes **compensationslos** das
Drift-Instabilitätsproblem löst; W7-X optimiert das Feld zusätzlich, um den
neoklassikanischen Transport zu minimieren.

## 2. Aufbaumodell: W7-X als Referenz

### 2.1 Hauptparameter (W7-X, IPP Greifswald)
| Größe | Wert |
|---|---|
| Typ | 5-Feldperioden, quasi-isodynamisch (Helias-Familie) |
| Hauptradius R0 | 5,5 m |
| Minor radius a | 0,53 m |
| Plasma-Volumen V | 30 m³ |
| Feld auf Achse B0 | 2,5 T (Design) / 3 T (max) |
| Rotationsverformung iota/2pi | 5/6 (Achse) bis 5/4 (Rand) — keine Resonanz |
| Spulen | **50 nichtplanare (5 Unikate, je 10 Kopien) + 20 planare (2 Unikate, je 10)** |
| Supraleiter | NbTi, 17,8 kA, 6,8 T am Spulenrand |
| Ports | 254 |
| Heizleistung | ≈ 50 MW (NBI + ICR + ECR) |
| Gehäuse | 16 m Durchmesser, 4,5 m Höhe, 725 t |
| Divertor | **Island-Divertor** (keine zentrale Spule wie im Tokamak) |

### 2.2 Spulensystem
- **5 nichtplanare (3D)-Spulen**, jede in **poloidale und toroidale Richtung**
  gewellt (typisch ~5 m hoch, 12 m Umfang) — diese erzeugen die **helikale
  Verdrehung** des Feldes und gleichzeitig die Quasi-Omnigenitäts-Vorspannung.
- **2 planare Spulen** (toroidale Ringform) — liefern das **Toroidalfeld**,
  fein-tunnerbar auf die Rotationsverformung.
- **2 Korrekturspulen-Systeme** (10 + 10 Windungen) — kompensieren
  Fehlerfeld-Abweichungen (ziel ∆B/B < 2 × 10^-4).
- **Für die Simulation:** Jede Spule ist ein mehrwindinger filarischer Leiter
  (typ. 1–3 Leiterschichten). In Elmer: als **Body-Force (J = I/A)** oder
  analytisch (Biot-Savart) — vgl. ANALYSE-002 (Validierung).

### 2.3 Magnetische Achse und Fluxflächen
- Die Plasmasäule liegt auf der **magnetischen Achse** — eine **geschlossene,
  3D-komplexe Kurve** (keine Kreisform), ohne Plasmaplasma-Stromdichte.
- Fluxflächen sind **verschachtelte 3D-Tori** (kein Kreis-Schnitt), beschrieben
  durch die **VMEC**-Gleichungen (Helikal-Mod-Expansion) oder **NCSX**
  (Finite-Elemente).
- **Quasi-Isodynamische (QI) Optimierung:** Die Feldstärke B ist auf
  jedem Fluxflächen **unabhängig vom toroidalen Winkel** → der **Ripple-Koeffizient
  ≈ 0**, der Neoklassische Transport (Bootstrap-Strom) ist minimiert. W7-X ist
  der größte QI-Stellarator.

## 3. Physik: Die wichtigsten Mechanismen

### 3.1 Magnetische Schließung
Ohne Plasma-Strom erzeugt die Spulen-Kombination ein **geschlossenes Feld**.
Die Fluxflächen sind in sich geschlossene (3D-komplexe) Kurven.
Die **Rotationsverformung iota(psi)** bestimmt, wie schnell eine Feldlinie
toroidal windet — für W7-X: iota/2pi zwischen 5/6 (achsen-nah) und
5/4 (Rand-nah). **Keine ganzzahlige Resonanz → keine globale Rissigkeit.**

### 3.2 Neoklassischer Transport
- **Ripple:** Das **Toroidalfeld ist ungleichmäßig** (5 Feldperioden,
  2 planare Spulen) → Trapping-Partikel erfahren das **Ripple-Feld**
  B(r,theta,phi) = B0 + Σ B_n,m · exp(i m theta) · exp(i n phi).
- **Quasi-Omnigenität (QI):** Das Feld wird so optimiert, dass der
  **Ripple-Koeffizient ~0** wird → Neoklassischer Transport minimiert.
  W7-X ist das größte QI-Stellarator.
- **Konsequenz für die Simulation:** Das Spulenfeld muss die
  **QI-Kriterien** des Design-Feldes reproduzieren (W7-X: iota-Verlauf
  5/6–5/4, B0 = 2,5 T); Abweichungen des Feldes im Plasma > 10^-3 · B0
  (≈ 2,5 mT) sind kritisch für Resonanzen und neoklassischen Transport.

### 3.3 Fehlerfelder und Resonanzen
- **Spulen-Fehler** (Fertigungstoleranz ~1 mm, Verformungen unter Last)
  erzeugen fehlerhafte Feldkomponenten δB_n,m.
- **Resonante Felder** (n/m = 1/2, 1/3, ...) erzeugen **Rissflächen** (Islands),
  die den Transport verschärfen.
- **Fehlerfeld-Korrekturspulen** (W7-X: 10 + 10) kompensieren
  ∆B/B < 2 × 10^-4.
- **Für Simulation:** Fehlerfelder müssen als zusätzliche Spulen-Geometrie
  oder als Randbedingung (Dirichlet A = 0 + A = A_fehler) eingebracht werden.

### 3.4 Divertor und Rand-Phänomene
- **Island-Divertor:** Statt einer zentralen Spule (Tokamak-Divertor) werden
  die Rand-Fluxflächen auf **Rissflächen** (Islands) gelenkt → Plasma-Abfluss
  (Neutrale, Impuritäten) über die Randscheiben.
- **Kritisch:** Die **Randscheiben** sind 3D-komplex; ein exaktes
  neoklassisches Modell (NCSX + QUIT) ist nötig, um die **Island-Größe**
  und den **Wall-Heat-Flux** vorherzusagen.
- **W7-X-Experiment (2023):** „Drift-driven local transport regime in the
  island divertor" (arXiv:2312.01240) — beobachteter **Drift-Transport**
  der Rissflächen, nicht im einfachen neoklassischen Modell enthalten.

### 3.5 Microturbulenz und Confinement
- **Electrostatic microturbulence:** W7-X-Experiment (arXiv:2312.10221) zeigt
  lokale **gyrokinetic-Simulationen** (GEM, gyokinetik, etc.) der Plasmasäule.
- **Confinement:** W7-X zielt auf **Tokamak-äquivalentes Confinement**
  (q ≈ 1/a) — durch **QI-Feld** und **optimierte Fehlerfelder**.
- **Für die Simulation:** Mikro-Turbulenz ist **außerhalb** des
  Elmer-Scopes; die **Stellarator-Simulations-Pipeline** fokussiert auf
  **Magnetostatik** (Spulenfeld) + **neoklassik-Analyse** (NCSX/VMEC).

## 4. Offene Geometriedatensätze (für die Modellierung)

| Quelle | Typ | Zugang |
|---|---|---|
| **HuggingFace proxima-fusion/constellaration** | 150k+ QI-VMEC-Gleichgewichte, Flussflächen, Benchmark | huggingface.co/datasets/proxima-fusion/constellaration |
| **arXiv:2506.19583** | „ConStellaration: A dataset of QI-like stellarator plasma boundaries..." (NeurIPS 2025) | arxiv.org/abs/2506.19583 |
| **alphastell** (Rust) | VMEC→STEP-Export, Spulengeometrie | github.com/alphastell |
| **W7-X-Daten (IPP)** | 50 nichtplanare + 20 planare Spulen, 3D-Geometrie | IPP Greifswald (Anfrage / Paper) |
| **arXiv:2111.04213** | „Carbon Dioxide, Fusion, and Stellarators" (W7-X-Übersicht) | arxiv.org/abs/2111.04213 |
| **FtI TOFE 2004** | W7-X-Progress, Spulensystem, B-Feld | fti.neep.wisc.edu |
| **Euro-Fusion WPS1PR18** | „Error fields in Wendelstein 7-X stellarator" | scipub.euro-fusion.org |

## 5. Konsequenzen für die fusion-Simulation

### 5.1 Validierungspfad (gerader Draht)
- **Zweck:** Prüfen, dass Elmer + gmsh + mein Script-Setup korrekt arbeitet,
  bevor die 70-Spulen-Stellarator-Sim (schweres Mesh, >10 Mio Elemente)
  gestartet wird.
- **2D-Planar** (empfohlen): Draht (R = 0,02 m) in der xy-Ebene, Strom I in +z.
  Exakte Lösung: B_theta(r) = mu0 · I / (2 pi r), A_z(r) = mu0 · I / (2 pi) · ln(r).
  **Vorteil:** Exakte analytische Referenz, kein Randfehler, kleiner Mesh (RO = 1,2 m).
- **3D-Draht:** L = 4 m, Endeffekte; exakte Formel: Biot-Savart mit endlicher
  Länge (Fresnel-Integrale). **Nachteil:** Endeffekte müssen als Fehler
  in die Validierung eingebracht werden.

### 5.2 Stellarator-Modellierung (nach Validierung)
- **Spulengeometrie:** 10 nichtplanare + 4 planare = 14 Spulen pro Feldperiode;
  x5 Feldperioden = 70 Spulen total. **Oder:** Nur **eine Feldperiode** simulieren
  (periodische Randbedingung) → **14 Spulen**, periodische B-C: A(x+L) = A(x).
- **Mesh:** gmsh 3D-Delaunay (Netgen) oder **transfinite** (Spulen: Hexagone).
  Ziel: >1 Mio Elemente (14 Spulen + Plasma + Air), ~2 GB RAM.
- **Elmer-Setup:**
  - 2D: `MagnetoDynamics2D`, `Equation = MgDyn2D`, Material mu0, J in +z.
  - 3D: `MagnetoDynamics`, `Equation = MgDyn`, **Body-Force J** für jede Spule.
  - **Oder:** `CoilSolver` (analytische Spulenträger, Biot-Savart-Kernel) →
    schneller als Mesh, aber **nur für dünne Spulen** (W7-X-Spulen dicker,
    50–100 mm Leiterschichten).
- **Auswertung:** B-Feld, B(theta, phi, r) auf der mag. Achse, **B-Fehler**
  gegenüber Analytik, **Ripple-Koeffizient** (Fourier n,m = 0,1,2),
  **Neoklassik** (NCSX).

## 6. Zu klären (User)

1. **Modellierer:** FreeCAD (sudo-Passwort) oder Blender (sofort)? → **OFFEN**
2. **Spulengeometrie:** offene W7-X-Daten oder parametrisch generieren? → **OFFEN**
3. **Sim-Scope:** Nur Magnetostatik (Spulenfeld) oder auch Plasma-Physik
   (VMEC, NCSX)? → **OFFEN**
4. **Abschlussformat:** LaTeX-PDF (cae-ingenieurs-doku) oder Markdown? → **OFFEN**

---

**Quellen (Zugang: 2026-10-22):**
- Wikipedia: Wendelstein 7-X
- FusionWiki: W7-X
- FtI TOFE 2004: W7-X Progress (Spulen, B-Feld)
- Euro-Fusion WPS1PR18: Error fields in Wendelstein 7-X
- arXiv: 2506.19583 (ConStellaration), 2111.04213 (W7-X-Überblick),
  2312.01240 (Island-Divertor-Transport), 2312.10221 (Microturbulenz),
  1011.5184 (QI-Neoklassik), 2205.05797 (QI-Optimierung)
- HuggingFace: proxima-fusion/constellaration (QI-Datensatz)
- Elmer Models Manual (Kap. Elektromagnetik, lokal: /tmp/elmerdoc/models.txt)
