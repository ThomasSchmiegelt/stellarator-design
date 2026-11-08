# Plan: Festigkeit (FEM) und Kühlung für den Vergleich K3 halb gegen DATJ5FC

Stand 2026-11-08, Prüfung und Plan, keine langen Rechnungen. Kennzeichnung jeder Zahl: **[G]** gemessen (Ergebnisdatei oder eigener Kurztest heute), **[C]** aus Code gelesen, **[S]** geschätzt, **[A]** Annahme.
Grundannahmen des Vergleichs (Vorgabe): a = 1,80 m, B0 = 6,5 T, Wickelpaket ca. 0,76 m, Rohr 0,85 m. Grenze 500 MPa ist nur eine Annahme (B-045). Wertung am p99 der heißesten Spule ohne 0,5-m-Randzone (B-043, B-046).

## 0. Die beiden Plasmen und ihre Herkunft

| | Kandidat 3 halb (K3) | DATJ5FC |
|---|---|---|
| Herkunft | **Eigene Form**: halber Schritt aus der Datensatzform Do3Qy, Datei `sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json` (B-060-Vorläufer, Gegenrechnung klein) | **Datensatzform, unverändert** (ConStellaration), Datei `sim/kette_k3/planb/boundary_DATJ5FC.json` |
| nfp | 2 [G] | 4 [G] |
| Spulensatz | `sim/kette_k3/stage2/satz_d100_n10_lr_s56` (10 Basisspulen, 40 Spulen, Feldfehler 2,1e-4, frei 48000 mit fsqr 4,0e-14) [G] | entsteht in `sim/kette_k3/datj/satz_d100_n5_lr_s56` (5 Basis, 40 Spulen) und `..._n6_lr_s56` (6 Basis, 48 Spulen); noch nicht fertig |
| R0 bei a = 1,80 m | 13,59 m [G, heute aus der Form gerechnet] | 16,42 m [G] |
| Plasma-Oberfläche bei a = 1,80 m | 1707 m² (Formkoeffizienten) bzw. 1693 m² (freie Grenze) [G] | 1851 m² [G] |
| Plasma-Volumen | 869 m³ [G] | 1050 m³ [G] |

Wichtig für Fairness: Bei gleichem a und B0 hat DATJ5FC 21 % mehr Volumen und 8 % mehr Fläche; die Kette nimmt aber für beide die gleiche Fusionsleistung (3053 MW, fest im Code, Stufe 0 des QA-Entwurfs) [C]. Das ist eine Annahme, nicht die wirkliche Leistung der Form.

## 1. Tragwerks-/FEM-Kette (Elmer)

### 1.1 Wie sie für DPrcxq66 lief
- Treiber: `stellarator/kopplung.py` (Befehl `punkt`, Funktion `rechne_punkt`). Ablauf [C]: `schritt_spulen` (Stufe 2, wird übersprungen, wenn `stufe2.json` im Punktordner liegt) -> `geometrie` (Unterprozess in `.venv-opt`, simsopt: Plasmarand, Fläche, Achsenfeld, Strom-Kalibrierung auf B0) -> `schritt_struktur` (Hex-Netz `hexmodell.py`, Gehäusewände `gehaeuse_netz.py`, Elmer mit MUMPS direkt, von Mises, p99 je Spule ohne Randzone in `submodell.py`) -> `schritt_package` (Hülle Plasma-Gehäuse, Abschirmung, Kernheizung, Fluenz, REBCO-Auslastung, Temperaturmarge) -> `bewerten`.
- Aufruf der Läufe [C, Skripte `sim/qi_feld/kette*.sh`]: `.venv/bin/python -m stellarator.kopplung punkt --studie <s> --nr <n> --von <s>/0000 --p <Basis aus param.json> abtastung=kruemmung biegung=innenkontur loeser=mumps <Zusatz>`, in `systemd-run --user --scope -p MemoryMax=26G -p MemorySwapMax=0`.
- Eingaben: `sim/kopplung/<studie>/plasma.json` (Felder `wout`, `L`, `nfp`), Punktordner mit `spulen.json` (Format "punkte_m", alle Spulen in Einheitsgeometrie, mit `R0_m`, `plasma_rand`), `biot_savart.json`, `stufe2.json`, `geometrie.json`, `plasma_rand.npy`.
- Der Stand, der als "DPrcxq66 hält" gilt, ist Punkt `qi_proxima_dpr/0012` (Wände ×1,6, `huelle_min_m=1.5`, `wand_adapt=1`; Parameter in dessen `param.json`) [G]: heißeste Spule (Nr. 11) p99 ohne Rand 446 MPa, Hülle (Plasma-Gehäuse) in der Endrunde 1,51 bis 1,56 m, 28 Spulen, 54 Stationen je Spule [G].
- Laufzeit [G aus `ergebnis.json` und `lauf.log`]: Struktur-Schritt je Netz 50 bis 110 s (Elmer-Anteil 40 bis 65 s); `wand_adapt` 2 bis 4 Runden = 100 s bis 420 s; ein Lauf mit Netz ×1,5 bis ×2 bis ca. 430 s.
- RAM: **nicht gemessen** (kein Spitzenwert in den Protokollen). Die Skripte setzen MemoryMax 11 GB (Standard in `kopplung.lauf`, zweiter Versuch 22 GB), die Ketten 20 bis 26 GB [C]. Schätzung: Standardnetz um 6 bis 12 GB [S], Netz ×2 mehr.

### 1.2 Was fest verdrahtet ist (nfp, Form, Spulen)
Nach Code lesen und einem Kurztest heute (siehe 1.4):
1. **nfp 2 ist NICHT in Netz, Verbindern, Lagern oder Elmer verdrahtet.** `hexmodell.py`, `gehaeuse_netz.py`, `submodell.py`, `cad.py` enthalten kein nfp [G, grep]. Lagerflecken richten sich nach dem Radius je Spule (`LAGER_ORT`), nicht nach der Periode [C]. nfp wird nur in `geometrie()` aus der wout gelesen [C]. `kraft_analyse.analyse` ist im Arbeitsbaum (noch nicht committet) schon auf `n_basis = n_spulen / (2*nfp)` aus der wout verallgemeinert [G, git diff].
2. **Form/Plasma:** global `WOUT` und `L` in `kopplung.py` zeigen auf `qa_nfp2_A45` mit `L = 10,4 / 1,0294`, werden aber von `plasma_laden()` aus `sim/kopplung/<studie>/plasma.json` überschrieben [C]. Für einen neuen Satz genügt also eine `plasma.json` mit der wout der freien Grenze und `L = 1,8 / a_u` (K3: L = 13,6084 [G, `kraefte.json`]).
3. **Spulenformat:** `struktur_netz` liest `spulen.json` im Format "punkte_m" (Liste `spulen` mit `name`, `typ`, `punkte_m`, `strom_A`, dazu `R0_m`, `plasma_rand`) [C]. Die Kette K3 hat dort `spulen.json` im Format "simsopt_basis" (`basis_x`, `currents`) und `biot_savart.json` [G]. **Umwandler nötig.**
4. **Strom je Spule (echter Fehler für unsere Sätze):** `struktur_netz` setzt für alle Spulen denselben Strom `s.strom = sign * I` [C, Zeile "s.strom = np.sign(s.strom) * I"]. Die K3-Spulen haben aber verschiedene Ströme: 13,6 bis 22,6 MA, Wickelpaket je Spule 0,59 bis 0,76 m [G, `kraefte.json`]. Proxima/DPr-Sätze hatten gleiche Ströme. Ohne Korrektur wäre die Kraft falsch (um bis zu 40 %). `hexmodell.lorentzdichte` und die Stromdichte nehmen `s.strom` je Spule [C], die Änderung ist also klein.
5. Wickelpaket: ein Maß für alle (`br = ho = WP_M*sqrt(I/22,11 MA)`) [C]. Mit dem größten K3-Strom 22,6 MA ergibt das 0,763 m = die Vorgabe 0,76 m [G]. Konservativ für die schwächeren Spulen (zu große Fläche, kleinere Stromdichte).
6. `schritt_package` und `bewerten` benutzen feste Annahmen (P_fus 3053 MW, Spitzenfaktor 2, Abschirmlänge 0,10 m, package_min 1,0 m) und `Bn_rel_mittel` aus `stufe2.json` [C]. Das Gehäuse-Wanddicken-Set (`wand_*`, `t_*`) ist für DPr optimiert (Wände ×1,6, Seite 0,8 m): für K3 mit 1,0 m Spule-Spule-Abstand [G] kommt das nicht ohne Eingriff aus, `entflechten` kürzt Seitenwände.

### 1.3 Nötige Änderungen (konkret)
| Nr | Datei, Funktion | Änderung | Aufwand |
|---|---|---|---|
| A | **neu** `stellarator/satz_nach_kopplung.py` | Aus Satzordner (`biot_savart.json`, `boundary.json`, `pruefung_satz.json`, `frei/wout/k_n48000.nc`) schreiben: `sim/kopplung/<studie>/plasma.json` (`wout` relativ, `L = 1,8/a`, `nfp` aus `boundary.json`), Punktordner `punkte/0000/` mit `spulen.json` (Format punkte_m, `typ` je Basisspule, `R0_m = 1`, `plasma_rand` aus Spulenpunkten), `biot_savart.json` (Kopie), `stufe2.json` (nur `Bn_rel_mittel`, `Bn_rel_max` aus `pruefung_satz.json`, als "aus Satzprüfung" kennzeichnen), `geometrie.json` (Unterprozess `kopplung _geometrie`). Ein Entwurf dieses Umwandlers lief heute in der Sitzung (K3: 40 Spulen, 3 s, 0,7 GB) [G]. | 0,5 h |
| B | `kopplung.py`, `struktur_netz` | Neue Option `strom_je_spule=1`: `s.strom = sign * |I_unit,k| / I_unit,0 * I` (Verhältnis aus `biot_savart.json`, `I` wie bisher aus `geo`); `br = ho = wp` aus dem größten Strom. Ohne Option unverändert (Regression an `qi_proxima_dpr/0012`: Netz byte-gleich, wie in `opus_heissespule.md` für Optionen geprüft). | 0,5 h |
| C | `kopplung.py`, `schritt_package` | `J_op` aus dem größten Strom (`wp`-Maß), nicht aus `I`; sonst gleich. | 0,2 h |
| D | `kopplung.py`, `main` (`punkt`) | `strom_je_spule` in die Liste der Zahlparameter aufnehmen (bisher nur Textschlüssel plus float, geht schon), kein Eingriff nötig, nur Test. | 0 |
| E | `kraft_analyse.py` / `kreis_kraft.py` | Bereits nfp-allgemein (uncommitted). `kreis_kraft.lauf` kopiert `biot_savart_<fall>.json` aus `stage2/`, im `datj`-Ordner liegt es unter `datj/` (Umgebungsvariable `K3_AUS`), das Skript `lauf_datj.sh` setzt das schon [C]. | 0 |

Alle Änderungen sind additiv (Optionen mit Standardwert), bestehende Läufe bleiben reproduzierbar.

### 1.4 Vortest heute (klein, unter 2 GB, in `systemd-run ... MemoryMax=2G`)
K3 halb, Spulensatz d100_n10_lr_s56, Hex-Netz mit den DPr-Parametern von Punkt 0012 (Wand innen 0,32, Seite 0,8, t_min 0,88, Hülle 1,5, Lücken-Modus), nur Netzbau, KEIN Elmer, gleicher Strom für alle Spulen (wie derzeit im Code) [G]:
- `geometrie`: 3,1 s; Plasmafläche 1693 m², Achsenfeld Einheitsgeometrie 0,4966 T, I_einheit 100 kA (aus Spule 0).
- `struktur_netz`: 207 s, Spitzen-RAM 0,54 GB (Prozess), 40 Spulen, 38 Stationen je Spule, 368 800 Elemente, 432 872 Knoten, **0 negative Elemente, 0 Durchdringungspunkte**, Verbinder 320 von 438, Wickelpaket 0,678 m (Strom 17,8 MA aus Spule 0, nicht der Maximalstrom).
- Heißt: Format-Umwandlung und Netzbau gehen für nfp 2 und 40 Spulen; Elmer-Lauf noch nicht versucht. Die Elmer-Größe ist mit 369 k Elementen (DPr: nicht notiert) in der Größenordnung bekannter Läufe [S].
- Der Netzbau braucht für K3 mit 3,5 min deutlich mehr als für DPr (Gesamtlauf DPr 50 bis 110 s inkl. Netz und Elmer [G]); der Grund (40 statt 28 Spulen, Entflechten) ist nicht untersucht.

### 1.5 Laufzeit und RAM je Form (Schätzung)
| Lauf | Dauer | RAM-Grenze im Scope | Status der Zahl |
|---|---|---|---|
| Umwandler A + `geometrie` | unter 1 min | 2 GB (Spitze 0,7 GB) | [G] |
| `struktur_netz` (nur Netz) K3 | 3,5 min | 2 GB (Spitze 0,54 GB) | [G] |
| Netz + Elmer + Auswertung, ein Durchlauf, K3 (40 Spulen) | 5 bis 15 min | 11 GB; 22 GB als zweiter Versuch | [S], von 50 bis 110 s DPr plus längeres Netz |
| `wand_adapt` (bis 4 Runden) K3 | 20 bis 60 min | 11 GB | [S] aus DPr 100 bis 420 s ×3 |
| DATJ5FC n5 (40 Spulen, 38 Stationen) | wie K3 | wie K3 | [S] |
| DATJ5FC n6 (48 Spulen, 32 Stationen) | etwas kürzer als K3 je Netz | wie K3 | [S] |
| Submodell heißeste Spule (optional, `kopplung`-Nachlauf) | je 5 bis 20 min | 26 GB (nicht gleichzeitig mit Stage 2!) | [S], DPr-Kette |

Mit den heutigen zwei Stage-2-Läufen (je 6 GB) bleibt Platz für einen einzelnen FEM-Lauf mit 11 GB; nicht zwei gleichzeitig.

## 2. Kühlung / Wärmeabfuhr

### 2.1 Was der Code rechnet
- `waermebilanz.py` [C]: Bilanz Netz 1000 MW, eta 0,35, M 1,15, f_div 0,5; liefert P_fus, P_Blanket, P_Erstwand = (1-f_div) f_alpha P_fus, mittlere Erstwandlast `q = P_Erstwand / S` mit **fest S = 1230 m²** (Vorgabe Stufe 0 HTS, veraltet; die Fläche der QA-Form 1,0 GW mit R0 10,4 m). Neutronenwandlast `q_n = (1-f_alpha) P_fus / S`.
- `kopplung.schritt_package` [C]: Neutronenwandlast mittel `0,8*3053 MW / Fläche` (Fläche aus der wout), Spitze ×2 [A, ARIES-CS], Abschirmlänge = Hülle - 0,10 m Spalt, Kernheizung im Wickelpaket `1e7 W/m³ je MW/m² * exp(-Abschirmung/0,10 m)`, Fluenz, REBCO-Auslastung. Messwerte DPr 0012: Hülle 1,46 m, Wandlast mittel 1,36 MW/m² (Fläche 1802 m²), Spitze 2,71 MW/m², Kernheizung 32 W/m³, Fluenz 2,7e17 n/cm² (Punkt 0000) [G].
- `kuehlung_segment.py`, `kuehlung_erstwand.py` (Wasser) und `blei_kanal.py` (Flüssigblei/Bleilithium) [C]: Segment 85 bis 95 Grad, Erstwand 0,9 m dick, Spalt Plasma-Wand 0,15 m, Wärmestromdichte `q` 0,5 MW/m² als Auslegungsannahme [A]. Blei: Kanal 20 × 20 mm, Steg 4, Eintritt 350 °C, ΔT 150 K, B 6,0 T, Feldsteigung toroidal 6 Grad [A, Standardwerte]; Größen: Kanalzahl n = Umfang/(b+steg), Länge L = R × 10 Grad, Wärmeleistung P = q U L, Volumenstrom Q = P/(ρ cp ΔT), Geschwindigkeit v = Q/(n A_k) (also v ∝ q L, **unabhängig vom Umfang**), Hartmann-Zahl, `dp_mhd = σ v B_quer² k_p L` (k_p aus Wandleitfähigkeit oder Isolierschicht 1/Ha), `dp_reib`, Pumpleistung, Nu = 5 [A]. Ohne Kehren/Verteiler, Stoffwerte ungeprüft.
- `kuehlung_waerme.py`, `erstwand_kanal.py`: 1D-Wärmeübergang (Dittus-Boelter/Gnielinski), 2D-Querschnitt in Elmer (HeatSolve) je Kanalquerschnitt: Größenordnung Minuten; `gradient_waerme.py` 3D-Ausschnitt 2:20 min je Fall, 2,8 GB [G, `ERINNERUNGEN.md`].
- CFD: `kuehlung_cfd.py` + PicoGK-Segment + FluidX3D (GPU) für 10-Grad-Segmente: Lauf b 8 mm 37 min, 11 GB VRAM [G, ERINNERUNGEN]; hier nicht nötig.

### 2.2 Was auf die QA-Form verdrahtet ist
- `gyroid_gefaess.randflaeche()` liest fest `sim/invers/qa_nfp2_A45/wout_*.nc` und `stufe1.json` (R0_m) und skaliert auf R0 = 10,4 m [C]. Das gilt für alles, was `randflaeche` importiert: `kuehlung_segment` (`rand_bei`, `schnitt_ebene`, `auslegung`), `kuehlung_erstwand`, `erstwand_kanal.umfang()`, `blei_kanal` (über `umfang()`), `gefaess_abstand`, `gesamtszene` [C, grep].
- Segmentlage 85 bis 95 Grad und Querschnitt bei φ = 90° (`erstwand_kanal.umfang(phi=90)`) sind fest [C]. Bei nfp 2 ist 90° die halbe Periode, bei nfp 4 die volle Periode: beides ein Symmetrieschnitt, aber kein gemeinsames Vergleichsmaß. Der Querschnitt wechselt längs φ, ein Schnitt reicht nicht für einen fairen Vergleich.
- `waermebilanz.S = 1230` und `plasma_waerme.py` (STUFE0 QA-1GW) sind QA-Werte [C].
- Gute Nachricht: Die Ersatzstelle ist klein. `randflaeche` kann ohne Datei-Eingriff ersetzt werden (Monkeypatch von `kuehlung_segment.randflaeche`, weil `kuehlung_segment` den Namen direkt importiert; `blei_kanal.umfang` kann ebenso ersetzt werden). Dauerhaft besser: optionale Parameter `wout`, `L` in `randflaeche` (Standard unverändert).

### 2.3 Kennzahlen für den fairen Vergleich
Gleiche Definition für beide Plasmen: a = 1,80 m, B0 = 6,5 T, gleiche P_fus (3053 MW, [A], ausdrücklich nennen), gleicher Spalt Plasma-Wand 0,15 m, gleiche Kanalgeometrie, `q` nicht fest 0,5 MW/m², sondern berechnet.

| Kennzahl | Wie | Zeit | Quelle der Zahl |
|---|---|---|---|
| Wandfläche S | Fläche des Randes bei Offset 0,15 m (numpy, aus wout der freien Grenze) | Sekunden | K3 heute 1693/1707 m² [G], DATJ5FC 1851 m² [G] |
| mittlere Neutronenwandlast `0,8·P_fus/S` | Formel aus `kopplung` | Sekunden | K3 1,43 MW/m², DATJ5FC 1,32 MW/m² [G, mit A-Annahme P_fus] |
| mittlere Erstwand-Strahlungslast `(1-f_div) f_α P_fus/S` | `waermebilanz`-Formel mit echtem S | Sekunden | K3 ca. 0,18 MW/m², DATJ5FC ca. 0,165 MW/m² [S, aus Formel]; die Annahme q = 0,5 MW/m² der Segmentstudien liegt 2,7-fach darüber |
| Spitzen-Wärmestromdichte | Verteilungsmaß: Linienquelle entlang der magnetischen Achse (cos/d²) auf der Wandfläche, normiert auf Mittelwert = Spitzenfaktor je Form | Minuten | **Proxy [S]**: gibt nur das Verhältnis Spitze/Mittel, nicht den Absolutwert; der Code nimmt Faktor 2 als Annahme. Echte Verteilung braucht Neutronik (OpenMC/MCNP), nicht im Plan |
| Abstand Wand-Spule (für Blanket) | `schritt_package` (Hülle = Plasma bis Gehäuse-Außenseite, p05, Median); schnelle Vorabschätzung ohne FEM: Spulenmitte-Plasma - Wickelpaket/2 - Wand innen | Sekunden bis Minuten | K3: Spulenmitte-Plasma 1,18 a = 2,13 m [G, `pruefung_satz.json`], abzüglich 0,38 + 0,32 m = ca. 1,43 m [S]; Annahme package_min 1,0 m, HELIAS 1,3 m belegt (B-039) |
| Kernheizung, Fluenz im Wickelpaket | `schritt_package` | im FEM-Lauf enthalten | [C] |
| Kanalzahl, Länge, Geschwindigkeit Blei | `blei_kanal.auslegung` mit Umfang(φ) und R(φ) der eigenen Form | Sekunden | [C] |
| Winkel Feldlinie-Kanal, B_quer | Aus den eigenen Spulen (Biot-Savart auf der Wandfläche, nach Kalibrierung auf 6,5 T wie `kraft_analyse.kalibrierung`) statt der Annahme 6 Grad/6 T: α aus B und toroidaler Richtung, Mittel und p95 von B_quer² | Minuten | neu, [S] |
| Hartmann-Zahl, MHD-Druckverlust toroidale Kanäle, Pumpleistung | `blei_kanal`-Formeln mit B_quer-Verteilung | Sekunden | [C] Formeln, Eingaben Annahmen |
| Rotationstransformation als Gegenprobe für die Feldsteigung | `tan α ≈ ι r/R` aus der wout | Sekunden | K3: Rand je Periode 0,088 [G, B-Befund] |
| Temperaturen Wand, Blei Aus | 1D (`kuehlung_waerme`), `erstwand_kanal` Querschnitt Elmer | Minuten, 1 bis 2 GB | [C]/[S] |

Ehrliche Grenzen: Vergleich gilt nur im Rahmen des 1D-Modells ohne Kehren, Verteiler, Korrosion, Neutronen-Volumenwärme [C, Docstring `blei_kanal`]. Gyroid-Tauscher und toroidale Kanäle sind getrennte Fragen: Gyroid ist für Flüssigblei wegen MHD ungeeignet (Merkpunkt Blei-Kühlung). Elmer/CFD ist nur für das 2D-Temperaturfeld und die Segment-Strömung nötig; für den Formvergleich genügen die Schnellrechnungen.

## 3. Minimaler Plan

### 3.1 Skripte (Datei, Funktion, Änderung)
1. **Neu** `stellarator/satz_nach_kopplung.py` (siehe 1.3 A): `python -m stellarator.satz_nach_kopplung <satzordner> <studie> --a 1.8` -> schreibt `plasma.json`, Punktordner, ruft `_geometrie`. Läuft in `.venv-opt` für simsopt.
2. `stellarator/kopplung.py`:
   - `struktur_netz`: Option `strom_je_spule` (Strom je Spule nach Verhältnis aus `biot_savart.json`, `wp` aus Maximalstrom).
   - `schritt_package`: `J_op` aus dem Maximalstrom.
   - (kein weiterer Eingriff; nfp ist nicht verdrahtet.)
3. **Neu** `stellarator/vergleich_kuehlung.py` (numpy, wout, `.venv-opt`): ersetzt per Monkeypatch `kuehlung_segment.randflaeche` und `blei_kanal.umfang` durch Versionen auf der gewünschten wout und L, rechnet S, Wandlasten, Umfangsprofil, B_quer aus den Spulen (Punkt 2.3), ruft `blei_kanal.auslegung` je φ-Segment auf, schreibt `sim/kette_k3/vergleich/kuehlung_<satz>.json`. Bestehende Dateien bleiben unverändert.
4. Optional (dauerhaft): `gyroid_gefaess.randflaeche(wout=None, L=None)` mit Standard QA; macht den Monkeypatch überflüssig.

### 3.2 Läufe in Reihenfolge
| Schritt | Lauf | Voraussetzung | Dauer | RAM | Status |
|---|---|---|---|---|---|
| 0 | Erwartung vor der Rechnung ins Protokoll (Regel 5): z. B. K3 p99 heißeste Spule 400 bis 600 MPa [S], Hülle 1,3 bis 1,5 m [S] | - | 10 min | - | offen |
| 1 | Umwandler auf K3 (`satz_d100_n10_lr_s56`), Regression: Netzbau mit gleichem Strom reproduziert den Vortest (368 800 Elemente) | Skript 1 | 5 min | 2 GB | Vortest [G] |
| 2 | Regression der Optionsänderung: `qi_proxima_dpr/0012`-Parameter mit `strom_je_spule=0` muss byte-gleiches Netz geben (nur Netzbau, wie `opus_heissespule.md`) | Skript 2 | 5 bis 10 min | 2 GB | offen |
| 3 | Kühlung Schnellvergleich K3 gegen DPr als Test der Pipeline (DPr: bekannt 1802 m², 1,36 MW/m²) | Skript 3 | 10 min | 2 GB | offen |
| 4 | FEM K3 halb: `kopplung punkt --studie k3_halb --nr 0 --p <DPr-0012-Parameter> strom_je_spule=1 wand_adapt=1` in Scope 11 GB | 1, 2, nach den Stage-2-Läufen oder mit 11 GB Reserve | 20 bis 60 min | 11 GB (22 GB als Rückfall) | [S] |
| 5 | Kühlung K3 (Schnellvergleich komplett, inkl. B_quer aus Spulen) | 3 | 10 bis 20 min | 2 GB | [S] |
| 6 | Wenn Stage 2 DATJ5FC fertig (ca. 2 h): Umwandler, dann FEM DATJ5FC n5 und n6 nacheinander mit identischen Parametern; Wände nicht je Form neu optimieren, `wand_adapt` mit gleichen Ziel- und Maximalwerten | `datj/satz_..._n5/6` fertig, freie Grenze 48000 | je 20 bis 60 min | 11 GB | [S] |
| 7 | Kühlung DATJ5FC wie Schritt 5 | 6 | 10 bis 20 min | 2 GB | [S] |
| 8 | Vergleichstabelle (beide Formen, gleiche Spalten), Bericht-Kapitel DE + EN, `BEFUNDE`, Hermes-Skill, Ereignisprotokoll | 4 bis 7 | 1 h | - | - |

Gesamtdauer reine Rechenzeit: ca. 2 bis 4 h [S], wesentlich durch FEM mit `wand_adapt`; ohne `wand_adapt` (ein Durchlauf je Satz) ca. 15 bis 45 min.

### 3.3 Fairness-Regeln und Fallstricke
- Gleiche Wand-Parameter, gleiches Netz (`stationen` skaliert mit Spulenzahl, K3/n5 38, n6 32 [C]), gleiches `huelle_min_m`; sonst misst man die Einstellung, nicht die Form (Regel 4).
- Kraft und Spannung als Zahlen nennen, 500 MPa als Annahme kennzeichnen, immer p99 der heißesten Spule ohne 0,5-m-Randzone.
- Spitzenwerte der Wandlast sind Proxy; keine Aussage "Form X kühlt besser" ohne Neutronik, nur "geometrisch günstigere Verteilung".
- Plasma zuerst: Die Rangfolge ergibt sich aus QI-Güte; Festigkeit und Kühlung schließen nur Unrealistisches aus (Memory plasma-vorrang).
- Der Feldfehler von DATJ5FC wird bei Stage 2 im Bauraum erst bestimmt; K3 hat 2,1e-4 (freie Grenze fsqr 4,0e-14, QI 5,14e-5 [G]); ein Vergleich der Feldfehler ist nur bei gleicher Form und Einstellung zulässig, hier nur als Nebenbedingung berichten.
- Erwartung vor jeder Rechnung ins Protokoll, Zahlen vor dem Schreiben aus Ergebnisdateien holen.
