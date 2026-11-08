# BEFUNDE — fusion (Stellarator)

> Chronologisches Befund-Log. Format: **Beobachtung, Messung, Fundstelle, Status**
> Eintrag oben = neuer. Status: ✅ gesichert · ⏸ blockiert · ⚠ zu prüfen

---

## B-066 Spulen glätten (Fourier-Ordnung kappen) entfernt die „8er“ nicht und kostet Faktor 10 im Feldfehler (2026-11-08, Opus) ⚠
- **Herkunft:** DATJ5FC, DATENSATZ-Form unverändert, mit EIGENEN Spulen d100_n5_lr_s56 (5 Grundspulen, Ordnung 7).
- Feldfehler nach Ordnung: 7: 1,05e-3; 6: 1,01e-2; 5: 1,55e-2; 4: 1,75e-2; 3: 3,7e-2; 2: 7,4e-2.
- Biegeradius im Original 0,85–0,89 m, also genau an der Krümmungsgrenze. Durch das Kappen wird er nicht besser, sondern teils viel schlechter (bis 0,07 m).
- **Die „8er“ sind Seiten-Achter:** In der Ansicht auf die Spulenebene gibt es keine Kreuzung. In der Seitenansicht kreuzt sich jede Grundspule 1–3 Mal: verdrehte Sattelspulen, 4,5–6,9 m aus der Ebene. Das bleibt bis Ordnung 2. Keine Selbstberührung (Abstand ≥ 1,9 m).
- **Folge:** Glätten nach der Rechnung hilft nicht. Die Baubarkeit muss in die Optimierung, mit einem Strafterm für Seiten-Achter oder Höhe aus der Ebene. Das passt zur Spulensprache-Idee: ebene Wörter statt verdrehter.
- Skript stellarator/spulen_glaetten.py (Baubarkeitsmaß), Bild docs/recherche/spulen_suche/glaettung/kappen.png.

## B-065 autoresearch-Pilot (Sonnet-Ralph-Schleife) an der Plasmaform: f 1,72 → 0,60, nur Koeffizientenschritte, Prüfbuch fängt 5 Schönmeldungen (2026-11-08, Opus + Sonnet) ⚠
- **Herkunft:** Start Kandidat 3 halb, EIGENE Form (aus Datensatzform Do3Qy). Vergleich DATJ5FC, DATENSATZ-Form unverändert, ziel 0,400.
- **Lauf:** 86 echte Runden (15:10–16:35), 50 Versuche, 25 behalten. ziel 1,723 → 0,606, f 0,599, QI 4,7e-5 → 7,0e-4; nicht zulässig (iota_rand 0,57). Bester Stand a0dcb7e, gegengerechnet exakt gleich.
- **Gegen Erwartung F-291:** f im erwarteten Bereich. QI schlechter als erwartet. Keine Fälle ohne Gleichgewicht (erwartet 10–30 %). 5 KORREKTUREN statt 0: 2 schlechtere Stände und 3 Gleichstände wollte der Agent behalten.
- **Deutung:** Der Agent macht nur Einzelkoeffizienten-Schritte, also ist die (1+1)-Evolutionsstrategie billiger. Die Sperre über das Prüfbuch ist nötig. Nach der Nutzungsgrenze lief die Schleife über 3000 Runden leer: Leerlauf-Erkennung fehlt.
- Bericht: docs/recherche/autoresearch_pilot/bericht.md, Bild verlauf.png. Nächstes Mal mit PI (lokal).

## B-064 Vergleich K3 halb (eigen) gegen DATJ5FC (Datensatz): DATJ5FC −26 % Kraft, −19 % Spannung, aber 6-mal schlechteres Plasma und zu wenig Platz (2026-11-08, Opus + Sonnet) ⚠

Bericht docs/recherche/spulen_suche/vergleich/vergleich_bericht.md, Protokoll F-281 bis F-290. Skripte `sim/kette_k3/lauf_datj.sh`, `lauf_vergleich_fem.sh`, `stellarator/satz_nach_kopplung.py`, `vergleich_kuehlung.py`, `vergleich_bilder.py`; `kopplung.py` Option `strom_je_spule` (vorher ein Strom für alle Spulen, bei ungleichen Strömen falsche Kräfte).
Gleiche Grenzen (a = 1,80 m, d100, _lr, _s56). DATJ5FC n5: Feldfehler 1,05e-3 (K3 2,1e-4), Abstand 0,99 a (bindend; K3 1,18 a), QI frei 48000 3,02e-4, Verlust 1,065 (K3 1,07), knapp unter Task-3-Grenze; n6: Verlust 1,14, QI 3,24e-4 darüber. Nettokraft max 934 gegen 1261 MN. FEM Wände wie 0012, Runde 0: 1160 gegen 1427 MPa; wand_adapt schwingt bei beiden (nicht konvergiert). Hülle 1,28 m (unter 1,5) gegen 1,50 m. Kühlung: Wandlast 1,32 gegen 1,44 MW/m²; Bleidruckverlust entscheidet Isolierung und Kanalrichtung, nicht die Form.
Erwartungen verfehlt: Verlust (erwartet 1,2 bis 1,6) und Spannung (erwartet deutlich niedriger). Elmer braucht bis 20 GB; FEM n6 OOM bei 24 GB.

---

## B-063 Spulen im Schnitt: Kandidat 3 holt weit aus, DATJ5FC wirkt am einfachsten, Vergleich aber unfair (2026-11-08, Opus) ⚠

Bild docs/recherche/spulen_suche/kreis/schnitt_spulen.png, Skript `stellarator/kreis_schnitt_spulen.py`, Bericht kreis_bericht.md Abschnitt „Spulen im Schnitt“. Fünf Basisspulen je Satz, seitlich auf (R, z) projiziert, um den Plasmaschnitt am mittleren φ der Spule.
K3 halb, Durchlauf 1 (Feldfehler 2,1e-4): Spulen bis z ≈ 1,2 R0, Knicke und Schlaufen. DjLe3eL6 + A085 (6,6e-4): kompakt, kleine Schlaufen. DATJ5FC Plan B d085_n5 (5,1e-3): glatt und kompakt.
Nutzer hält K3 für schwer baubar, DATJ5F für einfacher; das Bild stützt das. Vorbehalt: DATJ5FC ist eine unveränderte Datensatzform (nicht unsere), und ihr Satz hat einen 25-mal größeren Feldfehler, die alte Längenregel und keine Bauraumgrenzen. Fairer Vergleich: Stage 2 d100_n5_lr_s56 auf DATJ5FC, freie Grenze 48000, Kräfte (kraft_analyse für nfp 4 verallgemeinern). Noch nicht gerechnet.

---

## B-062 Kreis, Durchläufe 1 und 2: Spulen im Bauraum, Verlust 1,07; Abflachung senkt die Spitzenkraft 19 %, Ursache nicht belegt (2026-11-07, Opus) ⚠

Bericht docs/recherche/spulen_suche/kreis_bericht.md, Protokoll F-273 bis F-278. Skripte `sim/kette_k3/lauf_kreis1.sh`, `lauf_kreis2.sh`, `stellarator/kreis_kraft.py`, `stellarator/kreis_bilder.py`; `k3_spulen.py` Variante `_s<NN>`. Annahmen a = 1,80 m, B0 6,5 T, 1,3 m Freiraum, Paket 1,0 m.
Durchlauf 1 (K3 halb, d100_n10_lr_s56): Feldfehler 2,10e-4, Abstand 1,18 a, Spule–Spule 0,56 a, Biegeradius 0,50 a, keine Durchdringung, Rohr–Plasma 1,70 m, frei 48000: 5,14e-5 (fsqr 4,0e-14), Verlust 1,07, Nettokraft bis 1261 MN.
Durchlauf 2 (k3_wild_91_misch, Elongation 6,33, QI fest 1,12e-4): Feldfehler 1,79e-4, Abstand 1,31 a, frei 12000: 1,17e-4 (fsqr 8,3e-14, vorläufig), Verlust 1,04, Nettokraft bis 1021 MN, Summe 4411 gegen 4361 MN, Längensumme gleich (Grenze bindend). Grün gegen Blau im Bild: d085_n10_lr hat an derselben Form 1635 MN. Abflachung als Ursache nicht belegt.
Lange Läufe: Proxima 1,53, A085 1,29, K3 1,07. Strom 48000: Basis 0,000681, i_opt 0,000443, p008 0,000431 (fsqr 1,0e-14), Spiegel 0,359 -> 0,375/0,376. Offen: Kraft als Ziel von Stage 2 (LpCurveForce), Plasmadruck, FEM, Kühlung, Streuung von Stage 2.

## B-061 Prüfung der Sonnet-Arbeit vom 6./7. November: B-057 widerlegt, Verlustfaktor unbelastet, f falsch gelesen (2026-11-07, Opus) ⚠

Anlass: Nutzer „überprüf auch, was Sonnet gemacht hat“. Geprüft an den Rohdaten. Erwartung/Ergebnis F-272, F-273.
**B-057 falsch.** Die neun Fälle (i_p008_b056, i_p037, i_w588_u50, i_w470_u50, i_p008_t0.25/0.5/0.75 …) liefen ohne nzeta 48, ftol, niter und `trotzdem`, die alle früheren Fälle hatten. Mit denselben Einstellungen wie i_opt: j_p008 QI 0,000397, j_p037 0,000407 (i_opt 0,000415, Basis k_n3000 0,000579, fsqr 1,1e-10). Damit ist B-056 auf dieser Stufe bestätigt (Weg ii 0,000392, 1,3 % Abstand). j_w588/j_w470 brechen auch richtig eingestellt ab (Jacobian): 0,00019 ist nicht erreichbar. Die Halbierung war sinnvoll gedacht, maß aber nur den Fehlaufruf; die „Erwartung Kante in der Mitte“ im Nachtrag stand vorher nirgends.
**„Konvergiert“ stimmte nicht.** Bis 12000 Schritte erreichte kein Lauf ftol 1e-14 (fsqr 2e-13 bis 2e-10, `trotzdem`). Mit 48000 Schritten (Nachtrag F-275): Proxima 0,000681 (fsqr 1,0e-14, Verlust 1,53), A085 0,000575 (1,0e-14, 1,29), K3 d085_n10_lr 5,13e-5 (3,9e-14, 1,07, fällt noch). QI hängt an der Schrittzahl: Proxima 0,000579 → 0,000671, A085 0,000451 → 0,000558, K3 lr 5,61e-5 → 5,45e-5. Verlustfaktoren aus B-059/B-060 sind Zwischenstände. Lange Läufe siehe F-272.
**f ist Summe der Quadrate** (qi_filter_suche.py Zeile 11). Zulässig heißt f ≤ 5e-4 (5 Bedingungen je 0,01). Die Bezeichnung „Verletzungssumme“ und der Vergleich von f = 0,0114 mit 0,01 waren falsch und ließen das Ziel näher wirken. Beste Matrixprobe: f 0,0224, größte Verletzung 0,12. K3 halb selbst: größte Verletzung rund 0,8.
**Empfindlichkeit:** 18 von 27 ±0,2-sd-Paaren sind nach beiden Seiten schlechter; das Vorzeichen der Balken ist keine Richtung. Korrigiert in qi_experiment_bericht.md.
**Strom gegen Spiegel:** ±5 %: Korrelation log QI / Spiegel −0,81; 262 von 292 besseren Proben haben schlechteres Spiegelverhältnis.
**Kein Vergleich K3 gegen Proxima:** Feldfehler 2,15e-4 (K3) und 2,4e-3 (Proxima, DjLe3eL6) gehören zu verschiedenen Formen. d085_n10_lr hält Spule–Spule nur 0,30 a, die Rohre durchdringen sich. Die Aussage „Technik kostet 15 bis 25 %“ gilt für einen Satz, der nicht in den Bauraum passt.
**Bauraum:** Abbruchgrenze 0,72 a (1,3 m) wurde an der Spulenmittellinie gemessen, die 1,3 m gelten aber zwischen Plasma und Spule. Rohr–Plasma: d085_n10 0,95 m (zu wenig), d085_n10_lr 1,76 m (durchdringt sich). Kein Satz hält beides.
**Druck:** Alle Rechnungen laufen praktisch ohne Plasmadruck (pres_scale 1,0 Pa, curtor 0). Das war in B-058 offen.
**Kette:** Tragwerk lief für DPrcxq66 (B-040 bis B-049), nicht für Proxima-DjLe3eL6 allein; `kopplung.py` nimmt mit plasma.json fremde Formen. Kühlung ist die Gefäßwand, nicht das Spulenpaket, und `gyroid_gefaess.randflaeche` ist fest auf die QA-Form qa_nfp2_A45 verdrahtet: Sie kennt kein QI-Plasma.
**Protokoll:** Nummer F-253 doppelt vergeben (2026-11-05 und 2026-11-06); Experimentmatrix hatte keinen eigenen Befund (nachgeholt hier); B-057 stand am Dateiende.
Bestätigt: Zahlen der Matrix-Tabellen, Repo-Name ema-motor-analysis (gibt es, öffentlich), 832 Proben, Faktor 1,29/1,50 (Proxima).

## B-060 Kette K3 komplett: eigene Spulen für K3 halb (Feldfehler 2,1e-4), PicoGK-Rohre, freie Grenze Verlustfaktor 1,14 bis 1,17 – K3 halb bleibt mit Spulen das beste Plasma (2026-11-07, Sonnet-Agent) ✅ (Rand ⚠)

Erwartungen F-262, F-265 bis F-268, Ergebnisse F-267/F-269. Skripte `stellarator/k3_spulen.py` (Stage 2 beliebige Form, zwei_ringe-Ansatz; Varianten `_w` fortsetzen, `_o<N>` Fourier-Ordnung, `_k<NN>` Biegeradius, `_lr` Längenregel wie zwei_ringe), `stellarator/k3_rohr.py`, `stellarator/kette_k3_bilder.py`; Läufe `sim/kette_k3/` (lauf_stage2*.sh, lauf_teil2…5.sh, lauf_frei_k3.sh), Ergebnisse `sim/kette_k3/stage2/` (Spulen satz_<fall>/, freie Grenze satz_<fall>/frei/faelle/), Plan B `sim/kette_k3/planb/`, Kontrolle `sim/kette_k3/kontrolle_dje/`.
Stage 2 K3 halb (Form form_k3_f0.5.json, nfp 2, 2 Runden à 2000 Schritte, Feldfehler auf Prüfrand 128 × 64, Abstand fein):

| Fall | Spulen | Längenregel | Feldfehler mittel / max | Abstand (a) | Spule–Spule (a) | Zeit |
|---|---|---|---|---|---|---|
| d085_n8 (+ _w, 2 weitere Runden) | 32 | 1,25 × Start | 8,0e-3 / 5,0e-2 | 0,78 | 0,76 | 7 + 12 min |
| d072_n10 | 40 | 1,25 × Start | 4,35e-3 / 2,9e-2 | 0,62 (< 0,72) | 0,66 | 17 min |
| d085_n10 | 40 | 1,25 × Start | 2,80e-3 / 1,8e-2 | 0,79 | 0,56 | 19 min |
| **d085_n10_lr** | 40 | 24,9 a je Spule (zwei_ringe) | **2,15e-4 / 1,7e-3** | **1,22** | 0,30 (Grenze) | 11 min |
| Plan B DATJ5FC d085_n5 | 40 | 1,25 × Start | 5,0e-3 / 3,1e-2 | 0,82 | 0,59 | 10 min |
| Kontrolle DjLe3eL6 d085_n5 | 40 | 1,25 × Start | 4,36e-3 (Runde 1) | 0,81 | 0,69 | 8 min |
| Kontrolle DjLe3eL6 d085_n5_lr | 40 | zwei_ringe | 9,0e-4 (2 Runden) | 0,83 | 0,30 | 15 min |

Ursache der schlechten ersten Läufe (gemessen): meine Längengrenze 1,25 × Startlänge war bindend (K3 172,4 a bei Grenze 172,3 a; DjLe3eL6 88,9 a statt 124,5 a bei zwei_ringe). Mit der Regel aus zwei_ringe (Summe 249 a, an der Grenze) erreicht K3 halb 2,15e-4. Die Kontrolle trifft A085 (6,6e-4) mit 9,0e-4 nur in der Größenordnung (Faktor 1,36). Spulen: 27 bis 55 m lang, Biegeradius und Spule–Spule an ihren Grenzen, stark gewunden und weit ausladend (bis etwa 10 m über der Mittelebene, Bild kette_k3/schnitt_K3_d085_n10_lr.png).
PicoGK (d085_n10_lr): 10 Rohre geschlossen (0 offene Kanten), Durchmesser 0,851 bis 0,854 m, 86 s; Rohre durchdringen sich (0,81 m³, Spule–Spule 0,54 m < 0,85 m); Rohr–Plasma ≥ 1,76 m (0,98 a); Glättung Feldfehler +0,05 %. d085_n10: Durchdringung 0, Rohr–Plasma 0,95 m, Glättung +0,01 %.
Freie Grenze K3 (nzeta 100, 3000 Schritte, fest 4,79e-5): d085_n10_lr QI Rand 5,61e-5 → **Verlustfaktor 1,17**, s = 0,5 1,26, innen 0,96 bis 1,30; d085_n10 (2,8e-3) 6,37e-5 → 1,33, s = 0,5 1,56. Randabweichung beider Sätze 0,018/0,019 a mittel, 0,16 a max, Elongation 7,15 → 6,8 bei beiden (Verdacht: Rechengrenze, nicht Spulen). Gegenprobe 12000 Schritte d085_n10_lr: QI 5,45e-5 → **1,14**, s = 0,5 1,17, Randabweichung 0,014/0,13 a, Elongation 6,92 – längere Rechnung verkleinert Abweichung und Verlust (bei DjLe3eL6 umgekehrt, 1,01 → 1,25). iota/Spiegel ±1 %.
Belegt: Die ganze Kette Plasmaform → Spulen → Rohr (PicoGK, STL) → freie Grenze → Verlustfaktor läuft für unser eigenes Plasma. Mit Spulen QI 5,6e-5 bis 6,4e-5 gegen DjLe3eL6 mit A085 4,5e-4 bis 5,6e-4 (Faktor 8). Folgerung: QI des Plasmas taugt als Auswahlmaß, der Spulenverlust (1,2 bis 1,6) ist kleiner als der Formvorteil. QI nach Glättung (d085_n10_lr, 3000): Rand +0,02 %, s = 0,5 −0,4 %. Offen: Baubarkeit der Spulen (Länge, Windungen, Durchdringung bei Rohr 0,85 m → Spule–Spule-Grenze ≥ 0,5 a nötig), Kräfte/Spannungen, Plan B mit Längenregel nicht gerechnet. Bericht docs/recherche/spulen_suche/kette_k3.md.

## B-059 Kette K3, Schritt 1: eigene Spulen (A085) durch die freie Grenze – Verlustfaktor 1,01 bis 1,25 statt 1,30 bis 1,50 mit Proxima; PicoGK-Rohr kostet nichts (2026-11-07, Sonnet-Agent) ✅

Erwartung F-261 (Schritt 1) und F-263 (Rohr, an A085 erprobt). Werkzeug: `stellarator/spulen_satz.py` (simsopt-JSON -> Satz-Ordner boundary.json + spulen.json, Längenfaktor), `stellarator/qi_spulen.py` liest mit `QI_SATZ=<Ordner>` eigene Sätze (ohne Variable unverändert Proxima; Ergebnisse in `<Ordner>/frei/`), `stellarator/k3_rohr.py` + PicoGK-Konsolen-App `picogk/SpulenRohr` (Balkenkette mit Kreisquerschnitt, Voxel 25 mm, Glättung TripleOffset 100 mm, STL je Spule). Läufe `sim/kette_k3/lauf_schritt1.sh`, `slot.sh` (2 Plätze, Scope 6 GB).
Brücke: A085-Spulen von 1,699-fachem Maßstab auf Datensatzmaßstab umgerechnet, Feldfehler mittel 6,5978e-4 = zwei_ringe 6,5978e-4 (gleich auf 5 Stellen), max 5,74e-3 (gleich). Abstand Spule–Plasma auf feinem Rand 0,83 a (zwei_ringe auf gröberem Rand 0,85 a).
Freie Grenze (Einstellungen wie k_n3000 aus B-053: nzeta 48, 3000 Schritte, Ergebnis auch ohne Toleranz; fsqr 1,7e-10): QI Rand 0,00045117 gegen fest 0,00044558 (nzeta 48) → **Verlustfaktor 1,013** (Proxima-Spulen gleiche Einstellung 0,000579 → 1,30). Je Fläche frei/fest 0,93 bis 1,015 (innen s = 0,7 bis 0,8 sogar 7 % besser). Randabweichung mittel 0,010 a, max 0,066 a (Proxima 0,0125 a mittel). iota Rand/nfp 0,0904 → 0,0968 (+7 %), Spiegel 0,357 → 0,359, Elongation 6,50 → 6,23. Gegenprobe 12000 Schritte (fsqr 3,8e-12, 274 s): QI Rand 0,000558 → **Verlustfaktor 1,25** (Proxima 12000: 1,50); s = 0,5 frei/fest 1,011 (3000) bzw. 1,004 (12000), also innen stabil, Randwert wie in B-053 nicht selbstkonvergent. A085 ist bei beiden Rechenlängen 17 bis 22 % besser als Proxima.
PicoGK (A085, 5 Basisspulen, 45 s für alle): alle Rohre geschlossen (0 offene Kanten, mannigfaltig), Durchmesser 0,851 bis 0,855 m (Soll 0,852, ANNAHME flächengleich zum Wickelpaket 0,7552 m, a = 1,80 m), Volumen −0,14 % gegen π r² L. Glättung verschiebt die zurückgewonnene Mittellinie um 0,2 bis 0,5 mm (max 1,7 mm; vor der Glättung schon 0,2 bis 0,4 mm Messfehler des Kreisausgleichs), Feldfehler +0,015 % durch die Glättung. Rohre durchdringen sich: Vereinigung 0,92 m³ kleiner als die Summe (Spule–Spule 0,30 a = 0,54 m < 0,85 m Rohr). Kleinster Abstand Rohroberfläche–Plasma 1,05 m (0,58 a, S3).
Belegt: Die Kette Spulen-JSON → Feldtabelle → VMEC++ free-boundary → QI läuft mit eigenen Spulen; kleinerer Feldfehler B·n gibt kleineren QI-Verlust (−17 bis −22 % gegen Proxima). Folgerung: Ein Teil des Verlusts mit Proxima (B-053) lag am Spulensatz; der Rest (Randwert wächst mit der Rechenlänge, innen nicht) ist eine Eigenschaft der freien Grenze am Rand und macht den Verlustfaktor am Rand auf etwa ±10 % unsicher. Für Vergleiche immer dieselbe Einstellung nehmen und s = 0,5 mitmelden. A085-Spulen sind stark verschlungen (Schleifen, Bild kette_k3/rohr_A085.png) – rechnerisch gut, baulich fragwürdig. Nebenbefund (nicht nachgerechnet): Die nicht konvergierten Fälle aus B-057 (i_p008_*, i_p037, i_w*) liefen ohne die Sondereinstellungen (nzeta 48, ftol, niter, trotzdem), mit denen alle konvergierten i_-Fälle gerechnet wurden; das Scheitern kann daran liegen statt am Strom.
Erwartung F-261: (a) getroffen (fest = frühere fest_nz48 bitgleich), (b) getroffen (exakt), (c) getroffen mit Spanne 1,013 (3000) bis 1,25 (12000), kleiner als mit Proxima bei gleicher Einstellung; s = 0,5 innerhalb ±5 % getroffen. F-263 an A085: (a)–(f) getroffen (Glättung praktisch verlustfrei, Durchdringung > 0). Bericht docs/recherche/spulen_suche/kette_k3.md.


## B-058 Machbarkeit Plasmaform → Spulenform: Werkzeuge vorhanden, K3 halb als bestes Plasma, Spulen dafür vermutlich nah (2026-11-07, Agent, nur Recherche) ⚠

Werkzeuge (Import-Test): .venv-opt simsopt 1.11.1 + DESC 0.17.3 (REGCOIL-artig `solve_regularized_surface_current`, `to_CoilSet`), .venv-constellaration VMEC++ 0.4.11 + simsopt 1.8.1 (DESC-Import scheitert, jax 0.5.3). Kein REGCOIL/FOCUS, simsopt ohne Strombelag-Modul. Lizenzen MIT (simsopt, DESC, VMEC++, constellaration, CoilStellaration); REGCOIL/FOCUS nicht geprüft. Nichts installiert.
Im Projekt vorhanden: invers/stufe2_spulen.py (QA gut, QI gescheitert, B-028); stellarator/zwei_ringe.py A085 DjLe3eL6 Feldfehler mittel 6,6e-4, max 5,7e-3, 0,85 a, 587 s (Proxima-Satz 2,4e-3); qi_spulen.py free-boundary, Verlustfaktor DjLe3eL6 mit Proxima-Spulen 1,29 (3000 Schritte) bis 1,50 (12000). Lücke: qi_spulen.py liest fest den Proxima-Ordner; Brücke für eigene Spulen fehlt.
Rangliste (158 685 Datensatz + 284 eigene Proben, docs/recherche/spulen_suche/rangliste.json): Platz 1–10 alle K3/Do3-Proben, QI 3,66e-5 bis 4,60e-5, nfp 2, Elongation 7,15–7,56, Spiegel 0,42–0,48, iota/nfp 0,08–0,10, L_∇B 3,8–4,3 (Datensatz-Median 4,97). Bester Datensatz Do3Qy 6,15e-5 (L_∇B 4,02), Platz 2 DfnbHvbg… 6,67e-5 mit Elongation 5,54. Kompromiss (QI ≤ 0,000336 = beste 0,1 %, größtes L_∇B): DATJ5FCamJ3… nfp 4, QI 2,81e-4, L_∇B 7,14, Elongation 5,74 (DjLe3eL6: 7,05 / 6,50). Keine Proxima-Spulen für die Kandidaten in der lokalen CoilStellaration-Eval-Teilmenge (711 Ränder); Trainingsteil nicht geprüft.
Empfehlung: K3 halb als bestes Plasma; Schritt 0 Kettenprüfung mit eigenen A085-Spulen; Plan B DATJ5FC…. Aufwand 4–7 h Rechenzeit, 1–2 Arbeitstage. Abbruch: Feldfehler > 3e-3 nach 2 Runden in allen 9 Stage-2-Läufen oder Abstand < 0,72 a; freie Grenze höchstens 2 Varianten; Verlustfaktor > 3 melden und stoppen. Risiken: freie Grenze (B-057), nahe Spulen bei L_∇B ≈ 4, Spulenwelligkeit bei sehr kleinem QI, Proben nur einmal gerechnet. Nebenbefund: beste Probe = K3 halb, A ×1,05 mit nachgeführter Achse (−23 %, eine Rechnung). Erwartung F-257/F-258/F-259, Ergebnis F-260. Bericht docs/recherche/spulen_suche/spulen_machbarkeit.md.

## B-056 Strom-Optimum aus B-053 ist nicht global (2026-11-06, aus Demonstrator-Bau)

Unter den 150 Strom-Proben im geprüften Bereich ±5 % (Matrix Stufe 5, sim/qi_flaeche/experiment/strom) liegt eine zufällige Probe bei QI 0,000392 am Rand, kleiner als das L-BFGS-B-Optimum aus B-053 (0,000408). Das Optimum von B-053 war also ein lokales; die Zufallsprobe liegt nach Weg (ii) (Störungsmodell) um etwa 4 % darunter. Nicht geprüft: Gegenprobe mit freier Grenze (Weg i), Spiegelverhältnis und iota dieser Probe, ob die Probe die Nebenbedingungen verletzt. Das quadratische Modell an den 150 Proben hat bei Weglassen einer Probe typisch 3,2 % Fehler, schlimmstenfalls 14 %. Quelle: Bericht des Demonstrator-Agenten; die Zahl 0,000392 habe ich nicht selbst nachgerechnet.

## B-055 QI und Verdrillung: großer Durchmesser hilft nicht, Krümmungsstetigkeit nicht, zu viel Drehung des Querschnitts schadet (2026-11-05, Opus-Agent) ✅

Nutzer-Hypothese: lokaler QI hängt mit der Verdrillung zusammen, großer Durchmesser gibt mehr Raum, krümmungsstetiger ist besser. Skript stellarator/qi_verdrillung.py, Ergebnisse sim/qi_flaeche/verdrillung/, Bericht docs/recherche/qi_tragwerk/qi_verdrillung.md (+ Ordner qi_verdrillung/). Erwartung F-247, Ergebnis F-250.
Maßstab: QI maßstabsfrei (Form ×2 bitgenau, ×1,7 auf 7 Stellen gleich, alle Kennzahlen ebenso) -> "groß" nur als Aspektverhältnis.
Kausal (VMEC++ hohe Genauigkeit, nur R00 × 0,8…1,5, Querschnitt fest): Do3Qy QI ×1,0 0,0000615; ×0,9 0,000200; ×1,1 0,000175; ×0,8 0,000784; ×1,2 0,000275; ×1,35 0,000556; ×1,5 0,000909 (A 5,9…11,2). DjLe3eL6 ×1,0 0,000448; ×0,9 0,000786; ×1,1 0,000511; ×1,2 0,000541; ×1,35 0,000576; ×1,5 0,000587 (A 8,7…14,4); ×0,8 VMEC++ konvergiert nicht. Original jeweils optimal; iota/Spiegel/Elongation ändern sich nur wenig, Vakuummulde etwas besser bei größerem R.
Datensatz (158 685, analytische Maße aus r_cos/z_sin): Drehung des Querschnitts je Periode ρ +0,42 (nfp 2–5 +0,43…+0,55, A-Klassen +0,40…+0,52; ohne iota +0,28, ohne alle Kennzahlen +0,19); gestuft: netto 0 / π / 2π je Periode: Median QI 0,0157 / 0,0112 / 0,0296, beste 1 %: 487 / 1071 / 14. Torsion der Mittellinie ρ ≈ 0. Krümmungsänderung −0,14 (umgekehrt zur Hypothese, über Elongation). Mittlere Hautkrümmung × a +0,53. R²: Kennzahlen 0,897, + Maße 0,925 (+0,029), Maße allein + nfp + A 0,880, nur nfp + A 0,291.
Lokal (4 Formen, Rand): punktweise |ρ| ≤ 0,25, Vorzeichen wechselnd; je 2° bis 0,93, aber reine Cosinus-Welle ebenso bis 0,95 (Stellarator-Symmetrie), Vorzeichen wechselnd -> kein Beleg. QI-Fehler liegt in Streifen entlang der Feldlinien, nicht auf den Kanten.
Literatur (arXiv-Volltext gelesen): Plunk, Landreman & Helander 2019 (JPP 85): Achsenkrümmung muss an den Extremen von B null sein; unsere guten Formen zeigen das.
Urteil: teilweise (zu viel Querschnittsdrehung schadet); "großer Durchmesser hilft" und "krümmungsstetiger ist besser" nicht bestätigt. Offen: Neuoptimierung bei großem A; Skalierung mit nachgeführter Achsenwellung.

## B-044 Stufe 18: DPr x1,6 mit freien Verbindern und gedünnter Plasmaseite (2026-11-04)

Gesamtmodell (Mittel über alle Spulen), MPa; Grenzen Annahmen:

| Variante | Stahl p99 | Dehnung WP | Hülle | Verbinder | verletzt |
|---|---|---|---|---|---|
| x1,6, huelle_min 1,5, Standardnetz (Pkt 8) | 384 | 0,26 % | 1,56 m | 284/344 | – |
| x1,6, Netz x2, freie Verbinder (Pkt 9) | 447 | 0,32 % | 1,55 m | 260/332 | Dehnung |
| x1,6, Abkühlen B (Pkt 10) | 409 | 0,33 % | 1,56 m | 284/344 | Dehnung |
| x1,3, Netz x1,5 (Pkt 11) | 424 | 0,23 % | 1,57 m | 268/318 | Durchdringung |

Submodell heißeste Spule Pkt 9: 527 MPa (Stufe 1 ohne Rand 532). Erwartung F-224: Standardnetz 380–400 getroffen (384); Netz x2 380–430 verfehlt (447, +16 %); Abkühlen B Dehnung 0,31–0,34 getroffen (0,33); x1,3 440–520 knapp verfehlt (424, besser), dort Durchdringung als neues Problem; Submodell 580–620 verfehlt (527, besser). Fazit: Netzabhängigkeit klein (+16 % bei doppelter Stationszahl), Dehnung des Wickelpakets liegt bei Netz x2 und Abkühlen B an der Grenze. Nach dem Nutzermaßstab (heißeste Spule, B-043) liegt DPr x1,6 bei 527 bis 602 MPa, also über 500; Wandanpassung je Spule läuft (Opus-Agent).

## B-054 Wirkungskarte Spulen → lokales QI: Spulen wirken über den Strom an den Muldenflanken, nicht über die Nähe; hellste Flecken sind Formflecken (2026-11-05, Opus-Agent) ✅

Nutzer-Beobachtung: QI auf der Fläche sichtbar, Zusammenhang mit den Spulen und ihrer Position vermutet. Skripte stellarator/qi_wirkung.py (rechnen | geometrie | auswertung | opt), stellarator/qi_wirkung_bilder.py (bilder | html); Ergebnisse sim/qi_wirkung/ (42 Fälle als npz, auswertung.json, zerlegung.json, flecken_art.json, opt.json; Gegenprobe Weg i sim/qi_spulen/faelle/w_flecken_opt.json); Bericht docs/recherche/qi_tragwerk/qi_wirkungskarte.md (+ Ordner qi_wirkungskarte/, interaktiv wirkungskarte_3d.html).
Verfahren: Weg (ii) aus B-053, lokaler QI wie qi_3d auf Gitter 72 × 90 je Periode, Rand und s = 0,5; je Gruppe Strom ±5 % und Lage ±5 mm (r, t, z); Abstand je Gruppe (8 Kopien), Spulenspur, nächste Stelle, Krümmungsstelle; Naht φ_B = 0 ± 3° ausgeblendet. Prüfstein: 0,00055442 / 0,00044754 (offiziell), S2 −5 % +6,9 %, S5 senkrecht ±2,4 % wie B-053.
Gemessen (Rand): Wirkungsmaximum aller fünf Gruppen bei φ_B 71° (spiegelbildlich 19°), engste Stellen 4° (S1), 12°, 20°, 54°, 38° (S5). Rang |Wirkung| gegen 1/Abstand: S1 +0,45, S2 +0,40, S3 +0,24, S4 −0,35, S5 −0,51 (s = 0,5: +0,38/+0,35/+0,50/0,00/−0,26); Lage 5 mm: S1 +0,58, S2 +0,48 (Streifen neben der Spur), S5 −0,58. Wirkung auf q folgt dem vorhandenen Fehler (Rang gegen |r0| 0,73 bis 0,92); mit Restfehler r statt q gleiches Bild. Abstandsmodell Zusatzfehler ~ Σ a_g d_g^−p: Anpassung 0,19, Block-CV −0,36 (s = 0,5: 0,06/−0,20); mit den fünf Stromwirkungskarten als Merkmal: 0,69/0,46 (innen 0,10/−0,66). Hellste 2 %: 100 % auch ohne Spulen unter den hellsten 10 % (Formflecken), mit Spulen dort 13 % schwächer; Median 20° neben der nächsten Spulenstelle (zufällig 48°). Breite Flecken (32 % der schlechtesten 5 %) erzeugen die Spulen (ohne Spulen −57 %).
Trimmung schlechteste 5 % (L-BFGS-B, ±5 %): S2 = S3 = S4 = 1,05, S5 0,95 (Ecke, 10 Auswertungen): Flecken −38 % (B-053-Optimum −26 %), breite −73 %, scharfe −27 %; QI Rand −26 % (ii), −24 % (i: 0,000579 → 0,000438), s = 0,5 −24 %; Spiegel 0,359 → 0,371, iota/nfp 0,0963 → 0,0991 (i).
Erwartung F-248: (a) Nähe > 0,3 je Gruppe verfehlt (2 von 5, S5 umgekehrt), (b) Abstandsmodell 30 bis 60 % verfehlt (keine Vorhersagekraft), (c) helle Flecken versetzt/Formeffekt getroffen. Offen: Optimum an der Schranke (Weg ii nur ±5 % geprüft), andere Spulensätze, Einzelspulen.

## B-053 QI und Spulen: Spulenfehler kostet am Rand +24 %, Strom von S5 ist der stärkste Hebel, Spulenfeld hat Inseln am Rand (2026-11-05, Opus-Agent) ✅

Wunsch des Nutzers: Zusammenhang QI und Spulen (Strom je Spule zuerst, dann Lage, Karte mit QI und Spulen; nachgereicht 3D-Fläche mit QI-Farbe und Spulen). Form DjLe3eL6 mit Proxima-Spulensatz (5 Basisspulen, nfp 4, 40 Spulen). Skripte stellarator/qi_spulen.py (Werkzeug, Strom, Lage, Feldlinien, Karte), stellarator/qi_3d.py (3D); Ergebnisse sim/qi_spulen/, sim/qi_flaeche/karte3d/; Bericht docs/recherche/qi_tragwerk/qi_spulen.md (+ Ordner qi_spulen/, interaktiv qi_3d_dje.html).
Werkzeug: (i) VMEC++ free-boundary (vmecpp 0.4.11, Feldtabelle je Spulengruppe für 1 A selbst mit simsopt, forward_model unverändert, nur run_vmec getauscht; Gegenprobe ohne Spulen = offizieller QI exakt). Braucht nzeta 48 statt 24 (10 Spulen je Periode), Randwert nicht selbstkonvergent (3000/12000 Schritte: 0,000579/0,000671; innen stabil). Ursache gemessen per Feldlinien des reinen Spulenfelds: Inselketten bei iota 4/9 und 8/19, stochastischer Saum an der Soll-Grenze, letzte geschlossene Fläche außen bis 0,07 a innen, Innenspitze bei 45° nicht gefüllt. (ii) Störungsmodell: |B| der Spulen auf den Boozer-Flächen der offiziellen Rechnung, Paketfunktion qi; mit VMEC-|B| exakt offizieller QI; 8 s je Stromkombination.
Prüfstein: QI am Rand mit Spulen 0,000554 (ii) bzw. 0,00058 bis 0,00067 (i) statt 0,000448 (+24 bis +50 %); s = 0,5 −0,4 bis +2 %. Feldstärke der Spulen auf dem Rand 0,19 % Streuung gegen das Soll-Feld, Querfeld 0,24 %.
Strom (ii, Rand): alle gemeinsam ±5 % keine Änderung (< 1e-8; (i) mit Fluss mit gleich auf 5 Stellen). Je Gruppe ±5 %: S1 +12,8/−11,3 %, S2 +6,9/−7,1 %, S3 +8,5/−10,8 %, S4 +4,8/−9,8 %, S5 −24,6/+23,5 % (Ableitung je 1 %: S5 +8,8 %, S4 −3,0, S3 −2,7, S1 −2,4, S2 −1,4). Gegenprobe (i): S5 −5 % −27 % (ii −25), S5 +5 % +23 % (+24), S1 +5 % −11 % (−11); iota Rand ±2 %, Spiegel ±3 %. Optimum mit Schranken ±5 % (S2 1,05, S3 1,015, S4 0,98, S5 0,95): Rand 0,000408 (−27 %), (i) 0,000415 (−28 %), Spiegel 0,359 → 0,376. Ohne Schranken läuft die Suche zu Faktoren 2,2 und negativen Strömen (unbrauchbar).
Lage (ii, 5 mm Anlage, je Gruppe, ±): höchstens 2,7 % (S5 senkrecht), S1 1,0 % (Drehung um r), S3 0,45, S2 0,38, S4 0,30 %; linear. 5 mm an S5 ≈ 0,3 % Strom an S5.
Zusammenhang (Hinweis, eine Form): lokaler QI gegen Spulenabstand −0,24, ohne Spulen aber −0,32 (Formeffekt); Zusatzfehler durch Spulen je 2° gegen kleinsten Abstand −0,45, punktweise 0,05; Krümmung ≤ 0,10. Zusatzfehler sitzt bei S1/S2 (0,85 a), Stellhebel S5.
3D: lokaler QI = r²·N auf Boozer-(theta, phi), Flächenmittel = QI der Fläche (0,1 bis 2,7 %), Symmetrie q(θ,φ) = q(−θ,−φ) auf 0,1 bis 2,9 %, Periodizität nfp sichtbar; dje (mit Spulen), Do3Qy und K3 (ohne Spulensatz). Helle Naht bei φ = 0 mod 90° = Fensterende des QI-Verfahrens.
Erwartung F-245: QI-Faktor 2 getroffen, Randabweichung ≤ 4 % a verfehlt (bis 10 %), alle-gemeinsam getroffen, fester Fluss +10 % verfehlt, Größenordnung je Gruppe getroffen, stärkste Spule S1 verfehlt (S5), Optimierung −10 bis −30 % getroffen. Offen: Rand in (i) konvergent machen, Inseln mit optimierten Strömen, Einzelspulen (nfp 1), Lage mit (i) gegenprüfen.

## B-052 QI-Karte über 14 Flächen im Plasma: Fehler wächst nach außen, keine Aufsummierung; eine Form innen schlechter als am Rand (2026-11-05, Opus-Agent) ✅

Wunsch des Nutzers: QI für jeden Punkt im Plasma, ob sich Fehler aufaddieren. Skript stellarator/qi_karte.py (eins <form> | bilder), Lauf sim/qi_flaeche/karte/lauf.sh, Ergebnisse sim/qi_flaeche/karte/<form>.npz/.json, Bilder und Bericht docs/recherche/qi_tragwerk/qi_karte.md (+ Ordner qi_karte/). Verfahren: forward_model default_high_fidelity, auf demselben Gleichgewicht booz_xform für s = 0,02 … 1,0 (14 Flächen, je nächste VMEC-Fläche, Rand = 0,995) und quasi_isodynamicity_residual je Fläche einzeln, Residuen (75 Feldlinien × 2000 Winkel) behalten. Prüfstein: Summe der Quadrate am Rand = offizieller QI exakt (rel. Abw. 0) bei allen 4 Formen, auch eigene Boozer-Rechnung nur [1.0]; gegen Datensatz D8ZNt2 6 Stellen, Do3Qy 4 Stellen (0,00006147057 statt 0,00006146820). Fehler „Minimum of B is at the boundary“ trat nirgends auf (bis s = 0,015).

| Form | QI s=0,015 | s=0,1 | s=0,5 | s=0,7 | Rand | Volumenmittel/Rand |
|---|---|---|---|---|---|---|
| Do3Qy | 0,0000025 | 0,0000126 | 0,0000239 | 0,0000293 | 0,0000615 | 0,45 |
| K3 halb | 0,0000026 | 0,0000128 | 0,0000224 | 0,0000238 | 0,0000472 | 0,49 |
| D8ZNt2 | 0,000064 | 0,000341 | 0,001082 | 0,001355 | 0,001781 | 0,58 |
| DjLe3eL6 | 0,000029 | 0,000158 | 0,000622 | 0,000725 (Max.) | 0,000448 | 1,10 |

Gemessen: Bei 3 von 4 Formen wächst QI monoton (K3 fast monoton) von der Achse (20–30× kleiner, etwa ∝ s) zum Rand; der Rand ist die schlechteste Fläche, der offizielle Wert also eine sichere Obergrenze. DjLe3eL6: Maximum innen bei s ≈ 0,7, 1,62× der Randwert; s = 0,4 bis 0,9 alle schlechter als der Rand (offizielle Kennzahl unterschätzt). Reihenfolge der Formen auf jeder Fläche gleich (Do3Qy/K3 7- bis 57-mal besser); K3 ab s = 0,2 überall besser als Do3Qy (bis −31 % bei s = 0,9). Fehler sitzt an den Muldenflanken (Winkel 0,2–0,3 und 0,7–0,8), außen zusätzlich an einzelnen Feldlinien. Hypothese Nutzer: Aufaddieren im Sinne von Weiterreichen nach außen gibt es nicht (jede Fläche wird für sich bewertet); versteckter innerer Fehler größer als am Rand: teilweise bestätigt (1 von 4, nicht bei den besten). Erwartung F-243: Rand nicht am größten verfehlt (1 von 4), innen schlechter verfehlt (innen besser und glatter), keine Aufsummierung getroffen, Prüfstein ≥ 5 Stellen getroffen (exakt). Nebenbefund: qi.py legt die 75 Feldlinien mit linspace inkl. Endpunkt fest, Feldlinie 0 = 74 (doppelt gezählt). Offen: Ursache des Buckels bei DjLe3eL6 (iota 0,51 → 0,36, rationale Fläche?), Bahnrechnung, Volumen-QI als Zusatzbedingung der Suche, Gültigkeit für den ganzen Datensatz.

## B-051 Weg A (Datensatz gefiltert) und Weg B (lokale VMEC++-Suche) zur offiziellen Wertung > 0 (2026-11-04, Opus-Agent) ⚠ B läuft

Echte Schwellen (constellaration/problems.py, installiertes Paket) weichen von der Vorgabe ab: keine Aufgabe hat QI ≤ 0,001. Aufgabe 3 (MHDStableQIStellarator): iota Rand/nfp (Betrag) ≥ 0,25, log10 QI ≤ −3,5 (QI ≤ 0,00032), Spiegelverhältnis Rand ≤ 0,25, Flusskompression ≤ 0,9, Vakuummulde ≥ 0; keine Elongations- und keine A-Grenze. Aufgabe 2 (SimpleToBuildQIStellarator): A ≤ 10, iota ≥ 0,25, log10 QI ≤ −4 (QI ≤ 0,0001), Spiegel ≤ 0,2, Elongation ≤ 5; keine Vakuummulde, keine Flusskompression. Zulässig = jede normierte Verletzung ≤ 0,01 (also QI ≤ 0,00034 bzw. 0,00011, Vakuummulde ≥ −0,001). Die Vorgabe mischt beide Aufgaben. Wertung > 0 heißt in Aufgabe 3: zulässig (Hypervolumen (1+L)(20−A) > 0).
Schritt A gemessen (182 222 Zeilen, 158 685 mit QI): Regel des Nutzers 138 (iota mit Vorzeichen), mit Betrag wie das Paket 145; Aufgabe 3 ohne QI 166, mit QI 0; Aufgabe 2 ohne QI 786, mit QI 0. QI der 138: Minimum 0,00178 (D8ZNt2qFQLQQxMVitWaeCid, nfp 2), Median 0,0237; Platz 2 bis 5 nur 0,0066 bis 0,0082. Knappste Bedingung unter den 138: iota (kleinster Rest 0,0002) vor Spiegelverhältnis (0,0005) und Vakuummulde (0,0023); im Median sind Spiegel und Vakuummulde (je 0,11) am knappsten, Elongation am weitesten (0,30). Bindend bleibt QI: die beste Form verletzt log10 QI um 21 % (Grenze 1 %). Datei sim/qi_flaeche/filter138.json.
Schritt B (läuft seit 20:34): Startformen = 5 Datenformen mit kleinster amtlicher Verletzungssumme f (Abweichung vom Plan, Platz 2–5 der 138 lägen bei Faktor 20 über der Grenze): D8ZNt2 (QI 0,00178), DkPMhh (0,00163), DLQih3 (0,00168), D3uBG7 (0,00105), D4m6LX (0,00296). (1+1)-Evolutionsstrategie in 9 Koeffizienten, Schritt 0,02–0,3 sd, höchstens 40 VMEC++-Rechnungen je Start. Ergebnis offen; Bericht docs/recherche/qi_tragwerk/opus_filter_suche.md, Skript stellarator/qi_filter_suche.py.

## B-050 Gegenrechnung der Surrogat-Kandidaten mit VMEC++ (2026-11-04, Opus-Agent)

QI rechnet nur ConstellarationSettings.default_high_fidelity() (skip_qi liefert qi = None); Nachrechnung DjLe3eL6 0,00044754 und DPrcxq66 0,00079324 gleich dem Datensatz auf sechs Stellen; 70 bis 155 s je Form. Weite Suche (1,5 Standardabweichungen): 0 von 10 Kandidaten rechenbar. Kleine Schritte (höchstens 0,3): 9 von 10 rechenbar, alle QI unter 0,00045, aber 6 von 9 schlechter als ihre Startform, nur 3 besser (−2, −5, −12 %); Surrogat bei 4 von 9 um mehr als Faktor 2 falsch. Einzige eigene Form: Kandidat 3 (nfp 2, Startform Do3Qy…) auf halbem Schritt, QI 0,0000472 gegen 0,0000615 der besten Datensatzform (−23 %), Aspektverhältnis 7,39, Elongation 7,15, Spiegelverhältnis Rand 0,45, Rotationstransformation Rand je Periode 0,088; Datei sim/qi_flaeche/gegenrechnung_klein/form_k3_f0.5.json; kleine Abwandlung einer Datenform. Offizielle Wertung (lokal, nichts eingereicht): alle Formen 0, auch die eigene und die Datensatzformen DjLe3eL6/DPrcxq66, wegen Spiegelverhältnis (0,35 bis 0,54 statt höchstens 0,2 bis 0,25), Rotationstransformation (0,07 bis 0,21 statt mindestens 0,25), Vakuum-Well, Flusskompression, Elongation; QI nur Nebenbedingung. Konsequenz: Die Güte ‚QI höchstens 0,001‘ (B-047) ist nicht die Güte der Rangliste; unsere Sätze für die Tragwerkskette sind QI-gut, aber nicht rangtauglich. Nebenbefund: Mit OMP_NUM_THREADS=1 läuft die Surrogatsuche in 1 statt 13 Minuten. Bericht docs/recherche/qi_tragwerk/opus_gegenrechnung.md. Nicht geprüft: andere VMEC-Auflösung, Spulen für die neue Form.
**Berichtigung 2026-11-05 (B-051):** Die hier genannten Schwellen (Spiegelverhältnis 0,2/0,25, iota 0,25 …) und die Grenze QI 0,001 stammen aus dem Gedächtnis; maßgeblich sind die Werte aus B-051 (QI höchstens 0,00032 bzw. 0,0001, Betrag von iota). Der Wert 0 der offiziellen Wertung bleibt richtig, die genannten Verletzungen sind in Größenordnung zu prüfen.

## B-049 Absicherung DPrcxq66, Punkt 12: Absprungbasis nach Richtwerten (2026-11-04)

DPr x1,6, huelle_min 1,5, Lückenmodus, Wände je Spule (Punkt 12). Spannung = p99 der heißesten Spule ohne Randzone, MPa; Richtwerte 500 MPa und 0,3 % Dehnung:

| Variante | heißeste Spule | Stufe | Gesamt p99 | Dehnung WP | Hülle | Auslenkung |
|---|---|---|---|---|---|---|
| Standardnetz (Pkt 12) | 446 (Spule 11) | unter 500 | 362 | 0,25 % | 1,51 m | 42 mm |
| Netz x1,5, freie Verbinder (Pkt 14) | 432 (Spule 20) | unter 500 | 392 | 0,27 % | 1,51 m | 48 mm |
| Netz x2, freie Verbinder (Pkt 13) | 531 (Spule 12) | 500 bis 800 | 396 | 0,29 % | 1,50 m | 62 mm |
| Abkühlen B (Pkt 15) | 447 (Spule 11) | unter 500 | 386 | 0,31 % | 1,51 m | 42 mm |
| Wandziel 500 (Pkt 16) | 446 (Spule 11) | unter 500 | 364 | 0,24 % | 1,56 m | 40 mm |
| Wandziel 480 (Pkt 17) | 462 (Spule 18) | unter 500 | 386 | 0,28 % | 1,55 m | 46 mm |

Wandfaktoren: Ziel 450 gibt 1,30 an zwei Spulen (Pkt 12), Ziel 500 gibt 1,17 (Pkt 16), Ziel 480 gibt 1,22 (Pkt 17). Der Wert der heißesten Spule bleibt bei 446 MPa, weil sie bei Spule 11 liegt und die Anpassung hier nicht verändert wird; Punkt 12 war also dicker als nötig, Punkt 16 ist die schlankere Variante (Netz x2 und Abkühlen dafür nicht gerechnet). Submodell Spule 11 (Punkt 12): F1 446 (= Gesamtmodell), F2 474, F4 461 (Wandänderung höchstens 20 %): Streuung höchstens 6 %, Submodell vertrauenswürdig. Spitzenwerte (Stahl max ohne Rand) liegen bei 1145 bis 1823 MPa; sie sind netzabhängig und nicht Maßstab. Einordnung: Alle Richtwerte werden gehalten bis auf Netz x2 (531 MPa) und Abkühlen B (Dehnung 0,31 %), die knapp darüber liegen. Das gilt für die Annahmen (500 MPa, 0,3 %, Schrumpfwerte A/B/C), unter denen Abkühlen und Dehnung nur Spanne sind. Erwartung F-228/F-229 überwiegend getroffen (Abweichung: Wandziel 500 und 480 Spulenwert 446/462 statt 480 bis 530). DPr Punkt 12 gilt damit als Absprungbasis nach Richtwerten (vorläufig, Entscheidung der KI; Nutzer kann ändern).

## B-048 Formkoeffizienten -> QI (2026-11-04)

Aus Feldperioden und je 45 Koeffizienten für r_cos und z_sin (Tabelle 5 x 9) sagt ein Gradient-Boosting-Modell log10(QI) mit R² = 0,91 voraus (zurückgehaltene Daten, 158 685 Plasmen). Wichtigste Eingaben (Verlust an R²): r_cos[1,-2] 0,19, z_sin[1,0] 0,19, r_cos[1,1] 0,18, r_cos[0,1] 0,17, r_cos[1,-1] 0,13, Feldperioden 0,09. Ein Kasten auf den fünf wichtigsten Koeffizienten (5. bis 95. Perzentil der guten): Reinheit 2,3 % bei Abdeckung 63 % (Grundrate 1,5 %); bester Bereich des Baums (Tiefe 5): 5 % (483 gut von 9050). Erwartung F-233: R² getroffen und übertroffen; Kasten verfehlt (2,3 statt 5 bis 15 %); wichtige Moden m = 0 und 1 getroffen, nahe n = 0 nicht. Folge: für den Entwurf neuer Formen ist das Modell brauchbar, Bereichsangaben für Koeffizienten nicht. Grenzen: nur im Bereich der Daten gültig (Datenpunkte stammen aus Optimierungen), Indexkonvention n nicht geprüft, QI ist nur das Maß der Feldform. Skript stellarator/qi_koeffizienten.py, Datei docs/recherche/qi_tragwerk/qi_koeffizienten.md.

## B-047 Parameterkorridor für ein optimales Plasma (2026-11-04)

Gut = QI höchstens 0,001: 2420 von 158 685 Plasmen (1,53 %). Kasten aus den Bereichen der guten Plasmen (5. bis 95. Perzentil): Aspektverhältnis 7,6 bis 9,7; Elongation 5,35 bis 7,45; Dreieckigkeit −0,62 bis 0,27; Spiegelverhältnis Achse 0,27 bis 0,40, Rand 0,30 bis 0,43; Rotationstransformation je Periode Rand 0,07 bis 0,25, Achse 0,10 bis 0,28; Vakuum-Well −0,145 bis −0,01; kleinste Gradientenlänge 2,4 bis 8,3. Im Kasten 4824 Plasmen, davon 1123 gut: Reinheit 23 % (Grundrate 1,5 %), Abdeckung 46 %. Entscheidungsbaum (zeigt die Wechselwirkung): bester Bereich Reinheit 40 % (740 gut von 1857, 31 % der guten): Elongation über 6,06, Spiegelverhältnis Rand höchstens 0,43, Spiegelverhältnis Achse über 0,325, Aspektverhältnis höchstens 9,09, Rotationstransformation Rand höchstens 0,256. Erwartung F-231 getroffen (Kasten besser als erwartet: 23 % statt 3 bis 15 %; Baum 40 % Reinheit bei 31 % Abdeckung). Lage unserer Sätze: DjLe3eL6, DYU und DPrcxq66 liegen in allen Bereichen des Kastens; DSD und DGHe48vB knapp außerhalb (Spiegelverhältnis Rand, Aspektverhältnis/Dreieckigkeit); DP9, D5W/DHV, D56, DRD liegen in mehreren Merkmalen außerhalb. Grenzen: Die Kennzahlen sind Messgrößen der Feldform, keine Entwurfsparameter; ein Korridor in den Randparametern selbst fehlt. Reinheit 23 bis 40 % heißt: auch im Korridor sind drei von fünf Plasmen nicht gut. Skript stellarator/qi_korridor.py, Datei docs/recherche/qi_tragwerk/qi_korridor.md.
**Berichtigung 2026-11-05 (B-051):** Die Grenze 0,001 ist eine Arbeitsgrenze dieses Korridors, keine offizielle. Offiziell gilt Aufgabe 3 QI höchstens 0,00032, Aufgabe 2 höchstens 0,0001 (installiertes Paket). „Gut“ im Sinn der Rangliste ist also deutlich strenger.

## B-046 Wände je Spule: heißeste Spule hält den Richtwert (2026-11-04, Opus-Agent)

Bewertung umgestellt auf die heißeste Spule ohne 0,5-m-Randzone (stahl_heiss), Stufen unter 500 / 500 bis 800 / über 800 MPa. Nachgerechnet (heisse_spule.py, ohne Elmer): DPr x1,6 Punkt 2 und 8: 585 MPa (Spule 18), Punkt 9 (Netz x2): 532 MPa (Spule 5). Punkt 12 = Punkt 8 mit wand_adapt: nach einer Runde nur Spulen 4 und 18 um den Faktor 1,3 dicker; heißeste Spule jetzt Spule 11 mit 446 MPa (vorher 585), Spule 18 fällt auf 287 MPa, Gesamtwert 362 MPa, Hülle 1,514 m (huelle_min 1,5), Dehnung 0,25 %, Fluenz 1,6e17, Auslenkung 42 mm, 282/344 Verbinder, Stahl +3 % (41 019 t). Submodell F4: Spule 11 461 MPa. Grenzen: Wand im Submodell bis -36 % verändert; Faktor p99/450 setzt vermutlich zu viel Wand an (nicht geprüft); Netz x2 und Abkühlen für Punkt 12 noch offen (Stufe 19). Datei docs/recherche/qi_tragwerk/opus_heissespule.md.

## B-045 500 MPa ist Richtwert, keine feste Grenze (Nutzer 2026-11-04)

Die Wertung „Grenze eingehalten oder nicht“ gilt ab jetzt nur als „hält den Richtwert 500 MPa“. Spannungen werden als Zahl genannt und in Stufen eingeordnet: unter 500 MPa; 500 bis 800 MPa (Stellaris: Membran unter 660, von-Mises-Ersatz unter 800, Gehäuse unter 700, Quelle Lion et al. 2025); über 800 MPa. Gleiches gilt sinngemäß für die Wickelpaket-Dehnung 0,3 % (Annahme). Frühere Ziel-Aussagen (B-040, B-042, B-044) lesen als „hält die Richtwerte“. Damit liegt DPr x1,6 an der heißesten Spule (527 bis 602 MPa) in der mittleren Stufe, nicht im Ausfall.

## B-043 Spannungsmaßstab: heißeste Spule entscheidet (Nutzerentscheidung 2026-11-04)

Maßgebend ist ab jetzt der p99 der am stärksten belasteten Spule (ohne 0,5-m-Randzone, Bestätigung per Submodell F4); der Wert über alle Spulen läuft nur mit. Grenze 500 MPa bleibt Annahme. Stand nach neuem Maßstab: DPr x1,6 602 MPa (Standardnetz, Submodell) bzw. 585 MPa (Stufe 1 ohne Rand, nachgerechnet, zuerst fälschlich 568), über der Grenze; 0169 normal 434 (Spule 8), 0169 dünn 509, D56 566, DP9 673 (Submodell, B-030). Damit ist der in B-040 und B-042 gemeldete Zielzustand nach altem Maßstab erreicht, nach neuem nicht. Nächster Schritt: Wanddicke je Spule an die Last anpassen.

## B-042 Netzabhängigkeit geklärt: Verbinderplan und Seitenwand, nicht das Netz (2026-11-04, Opus-Agent)

(1) Hülle: Die 1,56 m (B-040) waren Zufall des Entflechtens, das an Spule 6 die Seitenwand (0,80 m) auf 0,19 m kürzte, ohne dass eine Durchdringung vorlag. Volle Seitenwand: Hülle 1,17 bis 1,19 m (unter HELIAS 1,3 m, Fluenz um 4e18). (2) Das Durchfallen im feineren Netz (B-041) kam vom festen Plan: 38 von 284 Verbindern fielen durch, die größte Lücke wuchs von 3,9 auf 15,2 m (Spule mit u 146 mm, p99 1806 MPa). Kontrolle mit freien Verbindern, Netz x1,5, huelle_min_m 1,5 (neue Option: dünnt die Plasmaseite der Wand gezielt bis zur Grenze, 32 Stationen um höchstens 0,31 m): Stahl p99 386 MPa, Auslenkung 35 mm, Dehnung 0,26 %, Hülle 1,551 m, Fluenz 1,1e17, alle Grenzen erfüllt (Annahmen). Hinweise: Das Netz x1,5 ergibt wegen der Krümmungsabtastung nur etwa x1,25 Stationen; verbinder_halb 3 macht Verbinder etwa 20 % breiter. Für Netzstudien Verbinder frei setzen. B-040 gilt nur mit gezielt gedünnter Seitenwand (Entwurfsentscheidung). Berichtigt: B-041-Aussage, DPr falle im feinen Netz durch, war ein Verfahrensfehler (fester Plan). Datei: docs/recherche/qi_tragwerk/opus_huelle_netz.md. Prüfläufe in Stufe 18.

## B-041 Stufe 17: DPrcxq66 hält die Absicherung nicht, Kraftmaßstab des Scans stimmt nicht, zwei Ringe (2026-11-04)

**Absicherung DPrcxq66 (Gesamtmodell, MPa; Grenzen Annahmen):**

| Variante | Stahl p99 | Dehnung WP | Hülle | Fluenz | alle Grenzen |
|---|---|---|---|---|---|
| Wände ×1,6, Netz ×1 (Pkt 2) | 384 | 0,26 % | 1,56 m | 1,1e17 | ja |
| ×1,6, Abkühlen A | 386 | 0,28 % | 1,56 m | 1,1e17 | ja |
| ×1,6, Abkühlen B (Wickelpaket 0,4 %, Verguss 0,6 %) | 409 | 0,33 % | 1,56 m | 1,1e17 | nein (Dehnung) |
| ×1,6, Abkühlen C (Verguss 1,16 %) | 399 | 0,26 % | 1,56 m | 1,1e17 | ja (Verguss p99 191) |
| ×1,6, Netz ×1,5, fester Plan (Pkt 3) | 580 | 0,35 % | 1,19 m | 4,3e18 | nein (Stahl, Dehnung, Fluenz) |
| ×1,3, Netz ×1,5, fester Plan (Pkt 7) | 650 | 0,34 % | 1,33 m | 1,0e18 | nein (Stahl, Dehnung, Durchdringung) |

Submodell heißeste Spule: Pkt 2 602 MPa, Abkühlen B 601 MPa.

Erwartung F-222: Abkühlen getroffen (Stahl höchstens +9 %, B Dehnung an der Grenze: 0,33). Feineres Netz verfehlt: +51 % statt +10 bis 30 %. Das Ziel-Ergebnis B-040 gilt damit nur für das Standardnetz; im feineren Netz scheitert DPrcxq66 an Stahl, Dehnung und Fluenz. Auffällig: Die Hülle sinkt beim feineren Netz von 1,56 auf 1,19 m (Ursache offen; Hüllenmaß sollte netzunabhängig sein) und kann die Fluenz allein erklären. Absprungbasis damit noch nicht festgeschrieben.

**Kraftmaßstab des Scans (Nebenbefund des Opus-Agenten, von Sonnet gegen die Kette gelesen):** Kette in MN je f des Scans: DjLe3eL6 41, DYU 39, DSD 26, DP9 33, DPrcxq66 13,7, DGHe48vB 13,6. Der Scan teilt durch das DESC-Feld B0; das Spulenfeld auf der Achse weicht je Satz verschieden ab (bei DjLe3eL6 Faktor 2,5). Die Rangfolge nach Scan-Kraft stimmt nicht. Wirkliche Kräfte (Kette): DjLe3eL6 564, DYU 695, DPrcxq66 792, DGHe48vB 665, DSD 1099, DP9 340 MN. „3 bis 10-mal mehr Kraft bei mehr Abstand“ (F-215, B-038) war daher falsch; DPrcxq66 hat nur 1,4-mal die Kraft von DjLe3eL6.

**Zwei Spulenringe (Nutzeridee F-221, Opus-Vortest, kein Optimierer ist konvergiert, alle stoppten am Iterationslimit):** Einring 0,85 a gegen 1,3 a: Kraft +53 %. Innenring (1 bis 7 MA) holt davon nichts zurück (B +7,5 %, B8 −3,8 %). Feldfehler mittel sinkt mit Innenring um Faktor 2,4, maximal um 1,6 (Erwartung Faktor 2: im Mittel getroffen, im Maximum nicht; Kraft sinkt nicht: verfehlt). Σ|I| ist in allen Fällen 580 MA (Durchflutungsgesetz). Einschränkung: Optimierer ohne Kraftziel, Vergleich mit Proxima-Satz nicht gleichwertig. Nächster Test: Kraftziel (LpCurveForce) und Bn ≤ 3e-3 festhalten. Datei docs/recherche/qi_tragwerk/zwei_ringe.md.

Nachtrag B-039 (Toleranz, Randschicht, Wärmelast, F-230): W7-X Spulenfertigungstoleranz bis 3 mm (nicht-planar) und 5 mm (planar); gemessene Strike-Line-Breite am Divertor 2 bis 4 cm; maximale Divertor-Wärmelast 3 bis 4 MW/m². Verworfen: Simulationswert 1 bis 5 cm (Zitat sagt 1 bis 2 cm). Nicht gefunden: Kacheldicke, Abstand Kachel zur LCFS. Einordnung (Vermutung): Die Posten der Abstandsbilanz Formtoleranz und Randschicht liegen bei Millimetern bis wenigen Zentimetern; unser Spaltposten 0,10 m ist dafür großzügig, der Abstand wird von Blanket und Abschirmung bestimmt, nicht von Toleranz oder Randschicht.

## B-040 Erster Satz erfüllt alle Grenzen im Gesamtmodell: DPrcxq66 (2026-11-04)

Gesamtmodell, Lückenmodus, Hüllenfreiraum; Grenzen sind Annahmen (Stahl p99 500 MPa, Wickelpaket-Dehnung 0,3 %, Fluenz 3e18, Package 1,0 m):

| Variante | Stahl p99 | Dehnung WP | Hülle | Fluenz | Kernheizung W/m³ | alle Grenzen |
|---|---|---|---|---|---|---|
| DPrcxq66 (nfp 2, QI 0,00079), Wände ×1,3 | 453 MPa | 0,27 % | 1,32 m | 1,1e18 | – | ja |
| DPrcxq66, Wände ×1,6 | 384 MPa | 0,26 % | 1,56 m | 1,1e17 | 13 | ja |
| DGHe48vB (QI 0,00116), Wände ×1,3 | 483 MPa | 0,34 % | 1,35 m | 7,9e17 | – | nein (Dehnung) |
| DYU ×1,45, Lager 3,6 m, 20 Verbinder je Paar | 500 MPa | 0,30 % | 1,27 m | 9,7e17 | – | nein (knapp) |

Kraft DPrcxq66 792 MN je Spule (Wände ändern sie nicht), größte Lücke ohne Verbinder 3,9 m, Verbinder 284 von 344. Erwartung F-219 getroffen (DPr ×1,3: 453 gegen 460–520, ×1,6: 384 gegen 400–450, beide etwas besser; DGH Dehnung 0,34 statt 0,30–0,33 knapp verfehlt).

Was die Aussage trägt und was nicht: Gesamtmodell-p99 über alle Spulen, Hüllenmaß ganze Gehäuseseiten, 500 MPa und 0,3 % nur angenommen. Das Submodell der heißesten Spule gibt 605 MPa (×1,3) und 602 MPa (×1,6) und liegt damit über 500. Abkühlen und feineres Netz für DPr sind in Stufe 17 in Arbeit. Plasma: QI 0,00079 ist rund 8-mal besser als DP9 (0,0068), aber schlechter als DjLe3eL6 und DYU (0,00045); nfp 2. Hülle 1,32 m (×1,3) liegt knapp über dem belegten HELIAS-Wert 1,3 m (B-039).

## B-039 Plasma-Wand-Abstand: was belegt ist (2026-11-04)

PI-Suche (25 Belege im Wortlaut bestätigt, von Claude inhaltlich gelesen): HELIAS 5-B braucht 1,3 m Blanket + Abschirmung zwischen Plasma und Spulen (KIT); W7-X Abstand Spule–Plasma c/a ~0,55; QI-Kraftwerk (Goodman 2025) c/a 0,87 bis 0,99 (Tabellenzuordnung durch PI gedeutet); EU-DEMO-Pionierreaktor innen 0,53 m Blanket + 0,25 m Abschirmung. Definition: LCFS = äußerste geschlossene Flussfläche, davor die Randschicht (SOL) mit offenen Feldlinien bis zur Wand; Plasma–Spule = Plasma–Wand + Gefäß + Blanket + Abschirmung + Spalt. Nicht gefunden: Kachel- und Toleranzwerte, W7-X Abstand, Stellaris. Verworfen: ARIES-CS 0,63 m (Blanketmodul, kein Abstand). Folge: package_min 1,0 m liegt unter HELIAS 1,3 m; Sätze mit Hülle unter 1,3 m (DYU x1,45: 1,27 m) knapp. Datei: docs/recherche/plasma_wand/pruefung_claude.md. Drei weitere PI-Themen (Toleranz, Randschichtbreite, Kacheldicke) laufen.

## B-038 Stufe 15: Platz für die Abschirmung gewonnen, Festigkeit nicht (2026-11-04)

Gesamtmodell, Lückenmodus, Hüllenfreiraum; MPa; 500 MPa und 0,3 % Dehnung nur Annahmen:

| Satz | QI | Kraft MN | Stahl p99 | WP-Dehnung | Hülle m | Fluenz n/cm² | verletzt |
|---|---|---|---|---|---|---|---|
| DYU ×1 (Referenz, Pkt 21) | 0,00045 | 695 | 417 | 0,23 % | 0,81 | 2,1e20 | Package, Kernheizung, Fluenz |
| DYU ×1,45, Wände ×1,45 | 0,00045 | 1458 | 627 | 0,38 % | 1,27 | 9,7e17 | Stahl, Dehnung |
| DSD ×1,12 | 0,00058 | 1377 | 791 | 0,54 % | 1,20 | 3,1e18 | Stahl, Dehnung, Fluenz, Durchdringung |
| DPrcxq66 (nfp 2) ×1 | 0,00079 | 792 | 562 | 0,32 % | 1,46 | 2,7e17 | Stahl, Dehnung |
| DGHe48vB (nfp 2) ×1 | 0,00116 | 665 | 538 | 0,36 % | 1,52 | 1,4e17 | Stahl, Dehnung |

Submodell heißeste Spule (p99 ohne Randzone): DYU ×1,45 794, DSD 1692, DPrcxq66 1066; DGHe48vB fehlgeschlagen (43 negative Elemente nach 6 Reparaturrunden).

Erwartung F-215: Hülle getroffen (DYU 1,27 statt 1,2–1,3; DPr 1,46 statt 1,3–1,6; DGH 1,52 gegen Schätzung 1,28, also Schätzung 0,24 m zu klein). Fluenz, Package, Kernheizung bei DYU ×1,45, DPr, DGH erfüllt. Verfehlt: Stahl DYU ×1,45 627 statt 410–480; die Spannung bleibt beim Hochskalieren nicht gleich (Kraft wuchs wie erwartet ×2,1, Spannung ×1,5). Vermutung, nicht geprüft: Lager (r_lager 2,5 m), Verbinder je Paar und weitere Referenzmaße wurden nicht mitskaliert. Besser als erwartet: DPr 562 statt über 700. Damit liegt der Engpass jetzt bei Festigkeit, nicht beim Platz. Nächste Läufe: dickere Wände bei DPr/DGH, Lager und Verbinder mitskalieren bei DYU. Hinweis: Das Submodell der heißesten Spule liegt 1,3- bis 1,9-mal über dem Gesamtmodell-p99; welcher der beiden Maßstäbe gelten soll, ist weiter Nutzerentscheidung.

## B-037 Stufe 14: Lückenmodus bei allen Plasma-zuerst-Sätzen (2026-11-04)

Gesamtmodell / Submodell (heißeste Spule, F4, p99 ohne Randzone), MPa, 500 MPa nur Annahme:

| Satz | QI | Stahl p99 | Submodell | Auslenkung | Hülle | Fluenz n/cm² | Kernheizung | Grenzen |
|---|---|---|---|---|---|---|---|---|
| DjLe3eL6, Wände Lauf 4 (Pkt 3) | 0,00045 | 444 | – (Lauf fehlt) | 62 mm | 0,48 m | 5,5e21 | verletzt | Stahl, Dehnung ok; Package, Kernheizung, Fluenz verletzt |
| DjLe3eL6, 0169-Wände (Pkt 2) | 0,00045 | 405 | 416 | 42 mm | 0,47 m | – | verletzt | wie oben |
| DYUDcSV7 (Pkt 21) | 0,00045 | 417 | 456 | 32 mm | 0,81 m | 2,1e20 | ok | Stahl, Dehnung ok; Package, Fluenz verletzt |
| DSD3rR5F (Pkt 1) | 0,00058 | 713 | 1459 | 119 mm | 1,09 m | 1,2e19 | ok | Stahl, Dehnung, Package, Fluenz verletzt |

Erwartung F-209: DjLe3eL6 Gesamtmodell unter 450 getroffen (444), Submodell 500–700 verfehlt nach unten (416 bei Punkt 2, besser); DYU unter 700 getroffen; DSD unter 900 getroffen; Hülle unverändert getroffen. Ergebnis: Das Tragwerk ist für DjLe3eL6 und DYU unter der Annahme lösbar (Lückenmodus entscheidend). Offen ist der Platz: Zulässige Fluenz 3e18 wird um das 4- bis 1800-fache überschritten, die Abschirmung zwischen Plasma und Spule ist bei diesen Plasmen mit 0,5 bis 0,8 m zu dünn (0169: 1,24 m, 3,8e18 knapp darüber). DSD hat den Platz (1,09 m), nicht die Festigkeit. Kein Satz erfüllt derzeit alle Grenzen. Submodell zu Punkt 3 (DjLe3eL6, Wände Lauf 4) fehlt, Kette hat es übersprungen (nicht geklärt).

## B-036 Was das Plasma beeinflusst: Datensatz-Auswertung (2026-11-04)

158 685 von 182 222 Plasmen mit gültigem QI. Rangkorrelation mit log10(QI) (kleiner ist besser): Randwert Rotationstransformation je Periode +0,35, kleinste Gradientenlänge −0,34, Aspektverhältnis −0,31, Elongation −0,30, Vakuum-Well −0,30, Spiegelverhältnis Rand +0,27, Dreieckigkeit +0,22, Feldperioden +0,14. QI-Median nach Perioden: 1: 0,0109, 2: 0,0085, 3: 0,0204, 4: 0,0145, 5: 0,0179; bestes Einzelplasma 2 Perioden (6e-5).

Erwartung F-210 (Aspektverhältnis wie in den 182 Sätzen +0,30) verfehlt: Vorzeichen kehrt sich um. Unter Aspektverhältnis 10 ist größer besser (−0,17 bis −0,34), darüber schlechter (+0,25); unsere 182 Sätze liegen bei 9 bis 11. Auch Perioden: gesamt +0,14, je Periodenzahl −0,14 bis −0,37. Aussage nur: wenige Perioden (2) sind im Median am besten, 3 am schlechtesten. Keine Regel wie „flacher ist besser“. Nur Korrelation, nicht Ursache, nur QI (Feldform), kein Einschluss. Die frühere Aussage „mehr Kraft geht mit besserem QI einher“ (−0,26) gilt nur für die 182 Sätze. Quelle: stellarator/qi_einfluss.py, docs/recherche/qi_tragwerk/qi_einfluss.md. Bericht: Abschnitt „Was das Plasma verbessert oder verschlechtert“ (DE/EN).

Nachtrag B-036 (Wechselwirkung, F-212/F-213): Ein gemeinsames Modell (Gradient Boosting, zurückgehaltene Daten) erklärt die QI-Güte mit R² = 0,90, jede Einzelkorrelation höchstens 0,12. Wichtigkeit: Spiegelverhältnis auf der Achse 1,19 und am Rand 1,00, danach Rotationstransformation am Rand 0,17 und Elongation 0,16, alles andere unter 0,09. Die beiden Spiegelverhältnisse hatten einzeln entgegengesetzte Vorzeichen (−0,21 und +0,27) und verdeckten sich so. Bereiche der besten 1 % (QI höchstens 0,00084), 5. bis 95. Perzentil: Aspektverhältnis 7,5 bis 9,7 (alle 5,3 bis 10,6); Elongation 5,3 bis 7,4; Spiegelverhältnis Achse 0,28 bis 0,40 und Rand 0,31 bis 0,43 (alle 0,12 bis 0,58 und 0,20 bis 0,85); Rotationstransformation Rand 0,07 bis 0,24; Vakuum-Well −0,14 bis −0,01; höchstens 4 Perioden. Erwartung R² über 0,5 getroffen, wichtigstes Merkmal (Rotationstransformation/Gradientenlänge) verfehlt. Grenze: Spiegelverhältnisse sind selbst Messgrößen der Feldform und mit QI eng verwandt, also keine freien Entwurfshebel, und es bleibt Korrelation. Quelle: stellarator/qi_bereiche.py, docs/recherche/qi_tragwerk/qi_bereiche.md.

## B-035 Verbinder nach Lücken: Auslenkung und Spannung fallen stark (2026-11-04)

DjLe3eL6 (QI 0,00045), 0169-Wände, Gesamtmodell, Option `verb_modus=luecken` (Restlücke höchstens 4 m angestrebt, erreicht 4,09 m; 72 Verbinder ergänzt, 40 davon mit gelockerter Querbedingung bis 0,5):

| Größe | vorher (Punkt 0) | mit Lückenmodus (Punkt 2) |
|---|---|---|
| größte Lücke | 17,4 m | 4,09 m |
| Auslenkung | 241 mm | 42,5 mm |
| Stahl p99 | 620 MPa | 405 MPa |
| Wickelpaket p99 | – | 202 MPa |
| Hüllenfreiraum | 0,47 m | 0,47 m |
| Verbinder ok | 228/316 | 300/388 |

Erwartung F-208 getroffen (u < 100 mm, Stahl < 500 MPa, Hülle unverändert). 500 MPa nur Annahme. Verletzt bleiben Package, Kernheizung und Fluenz (Hülle 0,47 m zu eng). Ungeprüft: Schräge Verbinder durch andere Spulen oder Plasma, Durchdringung überlappender Verbinder, Netzabhängigkeit, Submodell. Verbindermasse 11 511 → 15 547 t (Masse unwichtig). Quelle: docs/recherche/qi_tragwerk/opus_luecken.md (Opus-Unteragent, von Sonnet nur gegen ergebnis.json gelesen).

## B-034 Auslenkung der QI-Sätze: Lücke ohne Verbinder (2026-11-04, Opus-Fehlersuche)

190–290 mm sind echte Biegung, keine Starrkörperbewegung (81–88 % bleiben nach Abzug). Ursache laut Opus-Unteragent: lange Strecke ohne Verbinder und Lager (größte Lücke dje 17,4 m, dyu 14,8 m, dsd 11,8–14,4 m, DP9 6,6 m, 0169 1,8–3,1 m; Korrelation u_max zu Lücke hoch ^4: 0,98 dje, 0,96 dyu). Balkenüberschlag 40–210 mm passt. Die Lücke entsteht bei der Ortswahl der Verbinder (Querbedingung + nächster Abstand), nicht durch die verworfenen Verbinder. Vermutung, ungeprüft: Verbinder gezielt in Lücken setzen senkt die Auslenkung deutlich und damit auch die Spannung.

Submodell: Reparaturschleife jetzt gemeinsame Funktion `reparieren` in kopplung.py, Gesamtmodell unverändert (Netz bis 4e-15 m gleich), Kontrolle F=1 392,850 MPa. Submodell-Werte (Opus, Stufe 1 → Submodell F4, MPa): dje 0: 896 → 986, dje 1: 756 → 830, dyu 20: 1454 → 1598. Grenze: Wand örtlich bis 59 % dünner als in Stufe 1, das erhöht die Werte mit. Von mir nur Dateien und Tabelle gegengelesen, nicht nachgerechnet. Bericht: docs/recherche/qi_tragwerk/opus_fehlersuche.md.

## B-033 Stufe 13: Plasma zuerst, erste Tragwerkswerte (2026-11-04)

Gesamtmodell, Hüllenfreiraum, MPa (500 MPa nur Annahme):

| Satz | QI | Stahl p99 | Auslenkung mm | Hülle m | Verbinder ok |
|---|---|---|---|---|---|
| DjLe3eL6 (40 Spulen), 0169-Wände | 0,00045 | 620 | 241 | 0,47 | 228/316 |
| DjLe3eL6, Wände Lauf 4 | 0,00045 | 589 | 206 | 0,48 | 232/316 |
| DYUDcSV7 (32), Wände Lauf 4 | 0,00045 | 887 | 193 | 0,81 | 156/212 |
| DYUDcSV7, 0169-Wände (älter) | 0,00045 | 615 | 79 | – | 168/212 |
| DSD3rR5F (30) | 0,00058 | 1496 | 293 | 1,09 | 114/171 |

Erwartung F-203: Stahl DjLe3eL6 450–650 getroffen; Hülle 0,8–1,1 m verfehlt (0,47 m); DSD über 900 MPa getroffen. Auslenkungen von 200–290 mm sind ungewöhnlich (0169: 19 mm), Ursache offen (Lagerung oder Geometrie, nicht geprüft). Submodelle für DjLe3eL6 und DYU schlugen fehl: 11–20 negative Elemente, das Submodell hat keine Reparaturschleife. Damit noch kein belastbares Urteil über die Sätze.

## B-032 Abkühlen: für den Stahl klein, im Wickelpaket spürbar (2026-11-04)

Spanne als Annahme (Stahl 0,297 % belegt, Wickelpaket und Verguss nicht). Fälle A/B/C gegen ohne Abkühlen, Magnetkraft jeweils dabei, MPa:

| Größe | 0169 ohne | A | B | C | DP9 ohne | A | B | C |
|---|---|---|---|---|---|---|---|---|
| Stahl p99 gesamt | 308 | 310 | 336 | 324 | 383 | 383 | 400 | 397 |
| Stahl p99 heißeste Spule (Submodell F4) | 434 | 429 | 427 | 437 | 673 | 670 | 671 | 682 |
| Wickelpaket p99 | 149 | 161 | 196 | 138 | 234 | 246 | 277 | 226 |
| Wickelpaket Mittel | 62 | 80 | 124 | 55 | 67 | 85 | 129 | 64 |
| Verguss p99 | 88 | 88 | 96 | 155 | 101 | 99 | 105 | 167 |

Stahl gesamt höchstens +9 %, an der heißesten Spule höchstens 2 %. Erwartung F-202 für den Stahl getroffen, für das Wickelpaket zu hoch (B: +47 statt +100 bis +200 MPa). Wahrscheinliche Ursache, nicht geprüft: von Mises zählt allseitigen Zug nicht mit. Ein rundum festgehaltenes Wickelpaket steht unter allseitigem Zug, das Modell weist ihn nicht aus. Überschlag bei voller Behinderung in Fall B: rund 250 MPa. Offen: Hauptspannungen und Haftung an der Grenzfläche prüfen. Grenzen: gleichmäßige Temperatur, fest verklebt, Steifigkeit bei Raumtemperatur.

## B-031 Rangfolge: Plasma zuerst (2026-11-04)

Die Plasmagüte sortiert die Spulensätze, Kollision und Spannung schließen nur Unrealistisches aus (Nutzerentscheidung, weil die 500-MPa-Grenze nur Annahme ist). Neu sortiert: DYUDcSV7 (32 Spulen) und DjLe3eL6 (40 Spulen) teilen dasselbe Plasma mit QI 0,00045, rund 15-mal besser als DP9. DjLe3eL6 hat rechnerisch 24 % weniger Kraft, aber engere Biegung (0,50 a). Tragwerksrechnung läuft (Stufe 13), noch kein Ergebnis.

### B-030 | QI-Tragwerk Proxima-Satz 2: Last statt Netz ist das Problem; 0169 dünn widerlegt (2026-11-04)
- **Befund 1:** Die 1098 MPa von Satz 2 sind kein reines Netzartefakt. Nettokraft der sechs Spulentypen 31, 223, 641, 1170, 338, 112 MN
  (Filament-Nachrechnung bestätigt 1187 MN; alle Spulen gleicher Strom ist nur ±3 % falsch). Die Last sitzt auf wenigen Spulen.
- **Befund 2:** Querbedingung |d·b| > 0,8 war auf 0169 abgestimmt und ließ bei QI nur 204 von 468 Verbindern zu. Neue Optionen `seitlich_min`, `lager_ort=vier`.
  Bester Stand mit 0169-Wänden: Lauf 31 579 MPa, u 93 mm. u = 306 mm war eine einzelne Spule (3), nicht das Gesamttragwerk.
- **Befund 3:** Dicke Wände halten Stahl und Dehnung (Lauf 42: 325 MPa, 0,27 %, u 58 mm), nehmen aber der Abschirmung den Platz
  (Freiraum 1,52 → 0,38 m; Package, Kernheizung, Fluenz fallen durch). Zielkonflikt Tragwerk/Abschirmung. Stufe 5 trennt die Wände.
- **Befund 4 (ZURÜCKGENOMMEN, F-199):** Mit festem Verbinderplan und mitskalierter Verbinderbreite 0169 dünn 426 → 448 MPa, alle Grenzen eingehalten (×2 nicht gerechnet). Ursprünglicher, falscher Text: 0169 mit dünnen Wänden ist NICHT zulässig: 426 → 512 → 591 MPa bei Stationen ×1 / ×1,25 / ×1,5, nicht konvergiert.
  Die Angabe aus B-028/F-181 („426 MPa, alle Grenzen, 3648 t“) gilt nicht. Netzeinfluss Satz 2 bei ×1,25: Lauf 16 +8 % (721 → 779), Lauf 41 −11 % (428 → 380). Lauf 71 +28 % (336 → 429, F-195). Unsicherheit also bis rund 30 %, Richtung offen; feineres Netz ändert auch die Verbinderzahl (355 → 377), ist somit keine reine Netzstudie.
- **Befund 5:** Kraft-Scan (182 Sätze, stellarator/qi_kraft_scan.py): bezogene Höchstkraft 2,5–172, Satz 2 45,8 (Rang 124). Bezugsgröße nur als Rangfolge
  gültig, Absolutwert von Satz 2 wird nicht getroffen. Datensatz enthält keine Kräfte, Proximas Sätze sind also nicht danach ausgesucht.
- **Literatur:** Stellaris (Lion et al. 2025, offener Volltext KIT, im Original gelesen): 100–350 MN je Spule bei 9 T, 15 mm, 316LN Streckgrenze rund 1000 MPa,
  Grenze 800 MPa (von Mises als Näherung), Membran 660 MPa; dicke Gehäuse, 0,7–1 m Platten zwischen den Spulen, innere Stützringe. Unsere Grenze 500 MPa ist strenger.
- **Fehler der Agenten:** Haiku zählte mit Maximum statt Mittelwert des Feldfehlers (korrigiert); PIs Zusammenfassung verwechselte Nummern (gekennzeichnet);
  Sonnet erreichte den Stellaris-Volltext nicht, PI schon. Sonnets und PIs übrige Zitate: pruefe.py 54/54 für PI, inhaltlich nicht gegengelesen.
- **Fundstelle:** sim/qi_feld/ (lokal), docs/recherche/qi_tragwerk/, stellarator/qi_feld_auswertung.py, qi_kraft_scan.py, qi_guete.py. Protokoll F-186 bis F-191.
- **Befund 6 (KORRIGIERT, F-197/F-199):** Alte Freiraummessung nahm nur die Mitte der Innenwand an den Stationen. Neu `freiraum=huelle` (alle vier Seiten, zwischen den Stationen, netzstabil): 0169 normal 1,24 m (Fluenz 3,8e18 > 3e18!), 0169 dünn 1,28 m, DP9 Lauf 4 1,14 m, D56 0,58 m, Satz 2 Lauf 71 0,28 m statt 1,27 m. Alle Freiraumzahlen der Stufen 5–9 und des Variantenberichts sind mit der alten Messung zu günstig. „Seitenwand kostet nichts“ war Artefakt.
- **Befund 7:** Spulenauswahl ist der stärkste Hebel, nötig ist Kraft UND Abstand UND QI-Güte (docs/recherche/qi_tragwerk/kraft_scan_qi.csv):
  D5WFs QI 0,034 (schlechtes Plasma); D56VPJ7 157 MN, 316 MPa, QI 0,0023, aber Spule-Plasma 1,21 m (Abschirmung fällt durch);
  DRDP96E 393 MN, 749 MPa; DYUDcSV7 QI 0,0004, 695 MN, 615 MPa; DP9Xr4m 340 MN, 459 MPa, QI 0,0068.
- **Hinweis zu Befund 8/9:** Mit Hüllenmessung hält DP9 Lauf 4 die Fluenz auch im groben Netz NICHT. Netzänderungen des Gesamtnetzes sind durch Verbinderverlust und -breite vermischt; Spulenspannung über stellarator/submodell.py prüfen.
- **Befund 8:** DP9Xr4m (48 Spulen, nfp 4) Lauf 4 hält im groben Netz ALLE Grenzen (383 MPa, 0,23 %, Freiraum 1,27 m); im Netz ×1,25 Lauf 14: 441 MPa, 0,29 %, aber Freiraum 1,17 m, Fluenz 4,9e18 > 3e18. Kein belastbares Ergebnis. QI-Güte dreimal schlechter als Satz 2.
- **Befund 9:** Der Freiraum wird nur an den Stationen gemessen; feineres Netz senkt ihn um rund 0,10 m. Grobe Package-Werte sind zu günstig. Stahl nicht konvergiert (Änderungen −30 % bis +28 %), Netz und Verbinderplan vermischt.
- **Befund 10 (Submodell, stellarator/submodell.py):** Einzelne Spule, Verschiebungen aus Gesamtmodell. Kontrolle F = 1 exakt. Heißeste Spule, p99 ohne 0,5-m-Randzone, fein: 0169 normal 439 MPa (grob 420), 0169 dünn 495 (509), D56 575 (398), DP9 673 und noch steigend (520). Gesamtnetz reicht für 0169, unterschätzt QI-Biegungen um 29–44 %. Maßstabsfrage offen: p99 aller Spulen gegen p99 heißeste Spule.
- **Hinweis:** Die 500 MPa sind eine unbelegte Annahme (Nutzer, F-201). „Hält/fällt durch“ beim Stahl heißt nur: Vergleich mit dieser Annahme.
- **Offen:** Maßstab der 500-MPa-Grenze; Abkühlspannungen (eingebaut, Werte fehlen); Lager sind starre Flecken, Stützringe/Platten wie Stellaris nicht modelliert; 500-MPa-Grenze (Stellaris 660/800) ist Nutzerentscheidung.
- **Status:** ⚠️ noch kein QI-Satz, der alle Grenzen in beiden Netzen hält.

### B-029 | Variantenbericht-PDF unter 20 MB: Steckbriefe nur noch für die sieben zulässigen, Mosaik als JPG (2026-11-03)
- **Befund:** Beide PDFs hatten 26,7 / 26,6 MB. Fast alles davon sind Bilder: 13 Steckbriefe je ~0,9–1,06 MB
  (Spannungsbild + Treppenschnitt als PNG), Katalog 188 JPG ~14 MB, Mosaik aller 3D-Modelle 5 MB (PNG 2400×3360).
- **Maßnahme (Nutzer: „einige Varianten entfernen, so dass er unter 20 MB kommt … und zwar das PDF“):** Steckbriefe von
  0063, 0136, V3, V1, E_test, A_test entfernt (nur noch 0061, 0169, 0093, 0008, 0014, 0017, 0157) → 20,97 MB, noch zu
  groß. Zusätzlich Mosaik als JPG (Qualität 88) statt PNG: 5,05 → 1,02 MB, sichtbar gleich (Seite 15 geprüft).
- **Ergebnis:** DE 16,9 MB, EN 16,9 MB, je 75 Seiten, keine offenen Verweise. Zahlen der entfernten Entwürfe stehen weiter
  in Tabellen, Mosaik und Katalog; Einleitung von Abschnitt 11 sagt das.
- **Lehre:** Große Rasterbilder ohne Transparenz im Bericht als JPG ablegen; ein Steckbrief kostet ~1 MB.
- **Fundstelle:** stellarator/variantenbericht.py (STECKBRIEFE, montage), bericht/variantenbericht/*.tex.
- **Status:** ✅ erledigt.

### B-028 | ConStellaration/CoilStellaration (Proxima) an unsere Kette angebunden – QI-Grenzen der Kette (2026-11-03)
- **Beobachtung:** Unser QA-Plasma (nfp 2, A 4,5) ist in Proximas Benchmark unzulässig (Aufgabe 1: A 4,5 > 4,
  Dreieckigkeit +0,06, ι/nfp 0,21) bzw. nicht bewertbar (Aufgabe 2 verlangt QI). Drei zulässige Ranglisten-Ränder
  (nfp 3/4/2, Wertung 0,681/0,488/0,330) mit VMEC++ exakt nachgerechnet.
- **Unsere Spulenstufe (invers/stufe2_spulen.py) kann QI nicht:** Bn 0,02–0,19 (Grenze 3e-3), Spulen fallen ans Plasma.
  Geprüft und ausgeschlossen: Einheiten (Rand auf Volumen von 0169 skaliert), Abstand (0,7 a), Fourier-Ordnung (3/4),
  Proxima-Vorgaben (30 Spulen, Ordnung 7, Krümmung·a ≤ 3,5). Ursache nach Ausschluss: Start mit runden Ringen statt
  REGCOIL-Hüllflächenstrom (Proxima: REGCOIL → DESC).
- **Proximas Spulen in unserer Kette:** Feldfehler nachgerechnet 8,17e-4 / 9,34e-4 = Proxima. In 8058 Sätzen keiner mit
  Feldfehler < 3e-3 UND Biegeradius ≥ 0,7 a. Satz 2 (36 Spulen, Biegeradius 1,0 m) mit dünnem Gehäuse: σ99 1358 MPa,
  u 650 mm, Kraft je Spule 1187 MN (0169: 500 MN). Gegenprobe 0169 dünn: 426 MPa, alle Grenzen ok, 3648 t Stahl. **(Widerlegt, siehe B-030: Netzeffekt, 512–591 MPa im feineren Netz.)**
- **Korrektur (F-176):** Das Hex-Netz scheitert/verfälscht bei engen Biegungen, weil es nur 52 Stationen je Spule hat
  (0,8–1,7 m Abstand, Querschnitt dreht bis 73° je Station, Bahn bis 0,8 m daneben) – nicht wegen der Wandtiefe
  (zuerst falsch addiert: beide Seiten statt nur der Seite innen in der Kurve). Abhilfe 1: Abtastung nach Krümmung
  (`abtastung=kruemmung`, ≤ 10° je Station); Abhilfe 2 (Nutzeridee): Voxel-Gehäuse, dann Tetraedernetz.
- **Feinlauf (F-179):** Satz 2 mit `abtastung=kruemmung` (≈ 92 Stationen je Spule): Netz ok, σ99 2202 MPa, u 1083 mm –
  die grobe Abtastung hatte die Spannung unterschätzt. Satz 1 fein: 5370 umgestülpte Elemente, weil die Wand innen in der
  Kurve (0,63 m) tiefer ist als der echte Biegeradius (0,40 m). Aussage: unser für 0169 ausgelegtes Tragwerk
  (Einzelgehäuse, Verbinder, zwei Lager je Spule) trägt Proximas QI-Spulen nicht; eigenes QI-Tragwerk nötig.
- **Innenkontur (Nutzeridee, F-180/181):** `biegung=innenkontur` (gehaeuse_netz.biegegrenze) kappt die Wand innen in der
  Kurve, Material auf die Gegenseite. 0169 unverändert (305 statt 308 MPa). Satz 1: an 120/3120 Stationen ist schon das
  Wickelpaket zu breit für den Biegeradius → nicht baubar. Satz 2 (0169-Wände): bis auf 6–12 Elemente an einer Stelle
  netzbar; Rest-Ursache offen (Rahmenverdrillung? Entflechten?).
- **Stetig + Reparatur (F-182/183, Nutzerhinweis Spline-Startpunkte):** Kappung je Seite als Rampenhülle (4 Stationen);
  Restfehler lag am Start-/Endpunkt der Spulenkurve → Reparaturschleife (Wände dort weich −20 %, neu bauen) → 0 Fehler.
  Satz 2 mit 0169-Wänden: σ99 1098 MPa, u 306 mm, WP 494 MPa, 24 911 t Stahl → Faktor 2,2 über der Grenze.
- **Voxel als FE-Netz zu groß:** 0,1-m-Voxel ≈ 1,7 Mio. Elemente (×5 gegenüber feinem Hex-Netz) → MUMPS > 32 GB.
- **Grenze unabhängig vom Gehäuse:** Das Wickelpaket (0,71 m) muss sich biegen lassen; bei 0,40 m Biegeradius liegt die
  innerste Windung ≈ 5 cm vom Krümmungsmittelpunkt.
- **Messung:** sim/constellaration/ (bewertung_*.json, qi/*/bewertung.json, skaliert.json), sim/kopplung/qi_*/,
  gegenprobe_0169_duenn/; Bilder docs/bilder/qa_qi_vergleich.png, qa_qi_proxima_spulen.png.
- **Fundstelle:** Ereignisprotokoll (Buch) F-162 bis F-177; Daten huggingface.co/datasets/proxima-fusion/
  constellaration, constellaration-bench-results, coilstellaration (MIT); constellaration 0.2.6.
- **Status:** ✅ Bewertung/Einlesen gesichert · ⚠ Festigkeit QI unsicher (Netzauflösung, Lager nicht nachoptimiert) ·
  ⚠ 0169 dünn erst nach Netzprüfung glauben.

### B-027 | Surrogat-Rechenmodell: Hex-Netz fester Topologie, J x B per UDF, Elmer MUMPS (2026-10-25)
- **Beobachtung:** `stellarator/hexmodell.py` baut Wickelpaket, Verguss, Stahlgehaeuse und Verbinder
  als strukturiertes Hex-Netz direkt im Elmer-Format (kein gmsh, keine Luft). W7-X: 545 000 Knoten,
  1-GW-Anlage (qa_nfp2_A45 HTS): 191 000 Knoten. Lorentzkraft aus Biot-Savart (4x4 Teilfilamente)
  als Knotenlast ueber Fortran-UDF `elmer_udf/lorentz.f90` (prueft die Knotenreihenfolge).
  Nettokraft NPC3 2,36 MN (bewerte 2,39 MN, -1,3 %). Laufzeit je Probe: W7-X ~95 s, 1 GW ~45 s.
- **Loeser:** CG/ILU0 konvergiert nicht (Residuum steigt), MUMPS direkt geht (W7-X ~10 GB RAM).
- **Ergebnis Referenzprobe W7-X** (Waende 5/5/6–13,5 cm, ein Lagerflecken r = 0,25 m):
  Stahl von Mises p99 470 MPa, max 1490 MPa, u_max 30 mm. Handrechnung (Kastenquerschnitt,
  2,4 MN, Einspannung an einem Flecken) gibt dieselbe Groessenordnung (~1000 MPa, cm).
  **Widerspruch offen:** das Tet-Modell aus gehaeuse_netz (B-025) gab 110 MPa / 0,76 mm bei
  aehnlichen Waenden — dort Lagerung/Last pruefen.
- **1-GW-Anlage:** 1,2 GN Nettokraft je Spule; selbst mit 3-m-Lager und doppelten Waenden
  ~1 GPa (p99), 19 cm Verformung -> Einzelgehaeuse mit punktuellen Verbindern reichen nicht,
  durchgehende Stuetzstruktur noetig (Modellaussage, linear-elastisch).
- **Fehler unterwegs:** Jacobi-Pruefung hob das Vorzeichen doppelt auf -> umgestuelpte Verbinder
  unentdeckt (negatives Volumen). Behoben; Verbinder nur zwischen echten Seitennachbarn.
- **Status:** ✅ Modell laeuft; DOE/Training laufen autonom (`surrogat_waechter`, PI-Aufsicht).
- **Surrogat fertig (2026-10-25 16:27):** W7-X 78, 1 GW 79 Proben; GP + POD, 5-fach-Kreuzvalidierung:
  Stahl p99 R2 0,992/0,981, Masse 0,996/0,998, u_max 0,984/0,981; Maxima einzelner Elemente nur R2 0,4-0,7 (~15 %).
  Gegenprobe 1 GW (1000 MW, Waende 0,5/0,3 m, Lager 3,5 m): p99 -0,9 %, Masse +0,6 %, u_max -3,1 %, Maxima -15..-17 %.
  Hebel W7-X: Seitenwand (+50/-20 %), Innenwand; 1 GW: Innenwand, Seitenwand, E_Verbinder. 1 GW p99 3,1-3,7 GPa
  ueber den ganzen Bereich -> durchgehende Stuetzstruktur noetig. `rechne_probe` Standard jetzt MUMPS (iterativ hing
  bei --pruefen). Auswertung `stellarator/surrogat_auswertung.py`, Bericht `bericht/surrogat/surrogat_bericht.pdf`.

### B-026 | 3D-Anschauungsmodelle: Torus mit Schichten, CICC-Leiter, Blender-Render (2026-10-25)
- **torus3d.py:** W7-X-artiger Torus, 70 Spulen mit Gehaeuse, Verguss, Grundisolierung, 108 Leitern je Spule
  (Windungsisolation, Al-Mantel, Kabel), eindeutige Farben; Bilder w7x_torus3d_{schnitt,sektor,detail,geschlossen}.png,
  glTF torus3d.glb (169 MB) fuer Blender.
- **leiter3d.py:** CICC-Leiterstueck (Al 16 mm, 243 Straenge verdrillt, Bohrung r 5,60 mm aus 37 % Hohlraum),
  Strang 12-fach vergroessert mit NbTi-Filamenten (symbolisch). Strom: NbTi; Cu nur Stabilisator; Al/He stromlos.
- **blender_szene.py (Blender 4.0, Cycles CPU):** Fallstricke: Paket ohne OpenImageDenoise -> Denoiser aus;
  glTF-Farben kommen als sRGB-Werte -> linearisieren; Import liegt um 90 Grad um z gedreht -> Wurzel zurueckdrehen;
  weisser Hintergrund + Sonne 2-3 ueberstrahlt Metallflaechen -> Sonne 1,0, Alu metallisch 0,7/Rauheit 0,55, AgX.
  Flacher Torus fuellt Bounding-Kugel schlecht -> --zoom 1.9. Render Leiter ~1 min, Torus wenige Minuten.
- Status: ✅ Bilder in docs/bilder (w7x_leiter3d*.png, w7x_torus3d_blender.png); .blend in sim/ (nicht im Repo).

### B-025 | W7-X-Gehaeuse kollisionsfrei: CAD mit Nachbarschnitt, Rechnung ueber Rohrnetze (2026-10-24)
- **Ursache der Restkollisionen:** nicht die Wandstaerke (echter WP-Spalt NPC5<->NPC5 108 mm, NPC5<->PCB 130 mm),
  sondern (a) Loft-Ausbeulung zwischen den Stationen und (b) die ECKEN der Gehaeuse: freiraum prueft nur
  geradeaus (seitlich / aussen), schraeg stehende Nachbarn greifen ueber die Ecke.
- **CAD (Add-on, Idee User):** jedes Basisgehaeuse minus Aussenkoerper der Nachbarn (+ nachbar_spiel, Part::Offset;
  bei NPC scheitert der Offset -> ohne Spiel). Aufbau 70/70 Spulen + Verbinder: **0 Kollisionen** (vorher 100).
  Rest: NPC1 <-> NPC1_f reicht bis ins eigene Wickelpaket (Gehaeuse dort stellenweise offen).
- **Rechenweg (Idee User: "den funktionierenden Weg von heute morgen parallel"):** `stellarator/gehaeuse_netz.py`,
  zwei Rechteckrohre je Spule als eigene Dreiecksnetze auf der exakten Bahn (wie cad.elmer_netz, B-015), keine
  Booleschen Operationen. Wandstaerken: Kraft + freiraum + `entflechten` (Oberflaechenpunkte fremder Gehaeuse inkl.
  Zwischenringe gegen das eigene Rechteck, Wand mit dem kleinsten Verlust zurueck, Nachbarstationen mit).
  W7-X: Entflechtung 4980 -> 40 -> 0 Punkte, pyvista-Kollisionstest 0 Kontakte. Waende min 3 mm (wand_min), Spiel 10 mm.
- **FEM W7-X (Rohrnetz-Weg):** 3,02 Mio Tets, Netz 78 s, Elmer 55 min (~14 GB inkl. Swap). Stahl 33,4 m^3 = 264 t.
  Kraft je Spule Elmer 2,42 MN vs Biot-Savart 2,39 MN (NPC3, +1 %). Planare Spulen stromlos (Standard) -> 0 MPa.
  Gehaeuse von Mises: Mittel 11 MPa, 99 % < 43 MPa, max 110 MPa; Wickelpakete max 69 MPa; Verformung < 1 mm.
  -> weit unter 667 MPa. Einschraenkung: je Gehaeuse eingespannter Flecken statt Verbindern/Tragring,
  Verguss nicht modelliert, Waende stellenweise nur 3 mm. Bild docs/bilder/struktur_w7x_gehaeuse_netz.png.
- **Status:** ✅ Kette laeuft durch (CAD-Add-on + Rechenweg).

### B-024 | Keil auf der Torus-Innenseite: CAD geht, Vernetzung scheitert -> vorerst ohne Keil (2026-10-24)
- **Beobachtung:** Keil (Bachmann-Gewoelbe) in FreeCAD gueltig, trifft kein Wickelpaket. In gmsh aber
  "Invalid boundary mesh (overlapping facets)" (5 Versuche: AngleToleranceFacetOverlap, healShapes,
  occ.fuse des Stahls, ToleranceBoolean 1e-4). Ursache: Keil- und Gehaeuseschnitt am selben Wickelpaket ->
  deckungsgleiche Flaechen; OCC-Fuse in FreeCAD ergibt ebenfalls einen ungueltigen Koerper.
- **Versuch 6:** Keil mit Wickelpaket + 5 mm Versatz geschnitten (ueberlappt die Gehaeusewand, Idee User):
  3 von 16 Keilpaaren scheitern im CAD, gmsh haengt > 60 min in Fuse/Fragment (ohne Keil 6,6 min) -> abgebrochen.
- **Entscheidung (User):** Keil raus, `--keil` Standard 0. Code (Versatz-Schnitt, Fallback) bleibt als Option.
- **Status:** ⏸ blockiert (Idee fuer spaeter: Keil und Gehaeuse in EINEM Loft/Sweep bauen statt nachtraeglich vereinigen).

### B-023 | arXiv-Literatur: HTS-Dehnung, Fertigungstoleranzen (2026-10-24)
- **Beobachtung:** CSX (Schmeling 2025), Gil 2025 (Toleranzen), Canis (Nash 2025), Details ANALYSE-003.
  REBCO leidet unter Torsion und Biegung ueber die harte Achse; W7-X-Toleranz 2 mm lokal.
- **Vergleich:** Unser Loft (40 Skizzen) weicht 15 mm (A45) bzw. bis 19 mm (W7-X-Modell) von der Bahn ab ->
  fuer Spannungen ok, fuer Fertigung nicht.
- **Status:** ⚠ Offen: Pruefgroesse HTS-Dehnung (Torsion/hard-way je Spule), Toleranzstudie +-2 mm mit bewerte.

### B-022 | Literatur des Users: DEMO-Spulenregeln und W7-X-Einschluss (2026-10-24)
- **Beobachtung:** Von 33 PDFs sind 4 fuer das Projekt relevant (Details `forschung/ANALYSE-003-literatur-spulenstruktur.md`).
  Bachmann et al. 2024 (EU-DEMO, kleines A): TF-Innenschenkel als Keil/Gewoelbe, von Mises <= 660 MPa,
  Seitenwand 100 mm, Wickelpaket traegt ~65 MPa, J_eng-Formeln fuer LTS/HTS.
- **Messung/Vergleich:** J_eng nach Bachmann: Nb3Sn bei 10,9 T ~32 A/mm^2 (wir: 15, konservativ),
  HTS bei 14,7 T ~27 A/mm^2 (wir: 40, optimistisch -> WP ~1,5x groesser). W7-X (Grulke 2026):
  Einschluss bis 30-40 % ueber ISS04 (H <= 1,3 gedeckt), <beta> max. 2,8 % (unsere Grenze 5 % ist Annahme).
- **Status:** ⚠ Tokamak-Regeln nur als Anhalt; Keil innen + J_eng-Option noch umzusetzen.

### B-021 | Gehaeuse + Verbinder in Elmer: Kette laeuft, Stahl viel zu duenn (2026-10-24)
- **Beobachtung:** Erste gekoppelte Rechnung (Magnetfeld -> J x B -> Spannung) fuer die
  FreeCAD-Gehaeuse (B-020) mit 160 Verbindern. Kette STEP -> gmsh (OCC-Fragment) -> Elmer funktioniert.
- **Messung (qa_nfp2_A45_1GW_HTS, Wand innen/seitlich 0,1 m, aussen 0,15-0,5 m, Verbinder 0,6x0,6 m):**
  Netz 1,53 Mio Tets (h_stahl 0,25, h_wp 0,35; Geometrie 6,6 min, gesamt 7,5 min), Elmer 19 min, ~7 GB.
  Stahl 652 m^3 = 5,1 kt. von Mises Stahl: Mittel 1153 MPa, 99 % < 5130 MPa (zulaessig ~667);
  Wickelpakete Mittel 686, 99 % < 2363 MPa; Verformung bis 0,65 m. Hotspots auf der Torus-Innenseite
  und an den Verbinder-Anschluessen. Kraft Elmer vs Biot-Savart je Spule +9 % (S1 1307 vs 1196 MN;
  A6 mit feinerem Netz +2,9 %); Summe aller Kraefte 19 MN (~0, Gleichgewicht ok).
  Feines Netz (h_stahl 0,2): 2,79 Mio Tets, ~12,7 GB -> mit laufendem Hermes zu knapp (jetzt --mit_swap).
- **Bewertung:** Linear-elastisch, d.h. Spannung ~ 1/Querschnitt: Stahl muss etwa 3-5x mehr werden
  (Groessenordnung 15-25 kt; Vollschale A6: 51 kt bei 99 % < 587 MPa). Wandstaerken/Verbinder
  sind bisher nur geschaetzt, nicht ausgelegt.
- **Fundstelle:** `stellarator/gehaeuse_fem.py`, `sim/stellarator/gehaeuse_fem/qa_nfp2_A45_1GW_HTS/`,
  Bild `docs/bilder/struktur_A45_HTS_gehaeuse.png`.
- **Status:** ✅ Kette. ⚠ Auslegung offen (Wanddicken, Verbinder innen breiter/dichter, Iteration).

### B-020 | Spulengehaeuse als Variable Section Sweep in FreeCAD, parametrisch (2026-10-24)
- **Beobachtung:** Die durchgehende Stuetzschale scheitert bei A=4,5 an der Flaechenkonstruktion
  (B-019). Idee des Users (wie Creo "Variable Section Sweep"): je Spule eine geschlossene 3D-Kurve
  durch Punkte als INNENSEITE des Gehaeuses, Skizzen normal zur Kurve, Loft hindurch. Alles waechst
  nach aussen -> keine Faltung. Umgesetzt in FreeCAD 1.1.4 (AppImage), voll parametrisch
  (Tabelle "Parameter", Skizzenmasse als Ausdruecke, 12 von 16 Spulen als Symmetrie-Klone).
- **Messung (qa_nfp2_A45_1GW_HTS, WP 0,755 m, Wand innen/seitlich 0,1 m, aussen 0,15–0,5 m nach Kraft):**
  16 Gehaeuse gueltig (isValid), 0 Ueberlappungen, je 27–29 m^3, gesamt ~3,6 kt Stahl.
  Abweichung Loft <-> Spule: Spulenmitte 363–372 mm vom WP-Rand (Soll 377,5) bei 40 Stationen;
  bei 20 Stationen bis ~370 mm Abweichung (Mitte am Rand), Kruemmungs-Verteilung hilft nicht.
  Parametertest: t_max 700 mm, wand_seite 150 mm -> Gehaeuse + Klon gueltig, 29,4 -> 41,9 m^3.
- **Fundstelle:** `stellarator/gehaeuse.py`, `stellarator/freecad_vss.py`,
  `sim/stellarator/gehaeuse/qa_nfp2_A45_1GW_HTS/` (gehaeuse.FCStd, .step, pruefung.json),
  Bild `docs/bilder/gehaeuse_A45_HTS.png`.
- **Status:** ✅ Geometrie. ⚠ Offen: Gehaeuse verbinden, STEP -> gmsh -> Elmer-Spannungen.

### B-019 | Kompaktere Form A=4,5 + Stuetzschale in Elmer (Lorentzkraft -> Spannung) (2026-10-24)
- **Beobachtung:** A=4,5 (DESC qs 2,4e-5, Spulen B·n 0,27 %) verkleinert die 1-GW-Anlage deutlich;
  HTS und Nb3Sn werden fast gleich gross. Erste Strukturrechnung (Elmer gekoppelt) fuer A=6 HTS.
- **Messung (1 GW, Stufe 0 iteriert mit Stufe 3):**
  A=4,5 HTS: R0 10,4 m, B0 6,5 T, Leiter 14,7 T, 22,8 MA, Paket 0,76 m, Spalt 0,55 m, F 1196 MN.
  A=4,5 Nb3Sn: R0 12,4 m, B0 5,7 T, Leiter 10,9 T, 23,8 MA, Paket 1,26 m, Spalt 0,19 m, F 1307 MN
  (ohne Spaltbedingung: R0 10,6 m und Pakete durchdringen sich, Spalt -0,03 m).
  Struktur A=6 HTS (Schale 1,48 m, 316LN, Paket verschmiert E=100 GPa, 3-2-1-Lagerung):
  grob 0,69 / mittel 1,45 Mio Tets: Schale 99 % < 588 / 587 MPa, Spitze 831 / 1013 MPa,
  Paket 99 % 398 / 413 MPa, u_max 34 / 36 mm, Masse 50,7 kt. Lorentzkraft Elmer vs Biot-Savart +2,9 %.
  Spitzen auf der Torus-Innenseite (Spulen draengen nach innen), Eckensingularitaet.
- **Fundstelle:** `stellarator/struktur.py`, `sim/stellarator/struktur/qa_nfp2_1GW_HTS_{grob,mittel}/`,
  `invers/stufe0_bilanz.py` (Spaltbedingung), Bericht v0.3 (lokal).
- **Fehler unterwegs:** Elmer-Schluesselwort heisst `Stress Bodyforce i` (nicht Bodyload; wird still
  ignoriert, Verformung 0). Schalenflaechen fuer A=4,5: Faltung/Verdrehung/gmsh-Haenger, siehe
  Skill `stellarator-flaechen` – UNGELOEST, User hat Idee.
- **Status:** ✅ Auslegung A=4,5 gesichert; ✅ Struktur A=6 (99-%-Werte netzkonvergiert);
  ⚠ Struktur A=4,5 offen (Geometrie); ⚠ HTS-Querdruckgrenze gegen ~400 MPa im Paket pruefen.

### B-018 | Auslegung auf 1 GW netto: Stufe 0 (Leistungsbilanz) + eigene Form qa_nfp2 (2026-10-24)
- **Beobachtung:** Eigene Plasmaform `qa_nfp2` (DESC, nfp=2, A=6) erreicht qs_fehler 1,3e-5
  (Referenz precise_QA 5,8e-5), iota 0,423→0,415. Spulen (Variante `mittel`, abstand_sp 0,18):
  B·n 0,11 % Mittel / 0,40 % max. Neue Stufe 0 (`invers/stufe0_bilanz.py`) legt R0/B0 aus der
  Netzleistung aus; Stufe 3 in voller Groesse bestaetigt die Auslegung.
- **Messung (1000 MW netto → P_fus 3,05 GW, P_th 3,42 GW, eta 0,35, Eigenbedarf 197 MW):**

  | | HTS (≤ 20 T, j 40 A/mm²) | Nb3Sn (≤ 12 T, j 15 A/mm²) |
  |---|---|---|
  | R0 / a / B0 | 12,1 m / 2,0 m / 7,5 T | 22,2 m / 3,7 m / 4,8 T |
  | begrenzt durch | Einschluss (H_ISS04 1,3) + Wandlast 2,0 MW/m² | Einschluss + Leiterfeld |
  | <β>, n, T0 | 2,5 %, 2,2e20, 14 keV | 2,5 %, 0,9e20, 14 keV |
  | Stufe 3: Strom je Spule | 31,0 MA | 36,4 MA |
  | Stufe 3: B am Leiter (×B0) | 17,7 T (2,36) | 11,6 T (2,41) |
  | Stufe 3: Spalt Wickelpakete | 0,58 m (Paket 0,88 m) | 1,13 m (Paket 1,56 m) |
  | Stufe 3: Netto-Kraft je Spule max. | 2200 MN | 3000 MN |
  | Flussflaechen / iota / Spiegel | 12/12, 0,422→0,411, 0,08 % | gleich (Form skaliert) |

- **Wichtige Lehren:**
  1. Feld am Leiter ist NICHT ~2×B0 pauschal: erste Spulen (abstand_ss 0,10) gaben 3,5×B0 (eng
     beieinanderliegende Wickelpakete). Variante `mittel` (Spulen weiter auseinander) 2,4×B0.
     Spulennaeher ans Plasma (abstand_sp 0,12) ging nicht ohne B·n-Verlust (L14: 0,7 %).
  2. Spulenstrom ist durch Ampere festgelegt (2πR0B0/µ0/N × 1,09), unabhaengig von der Spulenlage.
  3. Bei Nb3Sn dominiert das Eigenfeld des Wickelpakets: mit j=20 A/mm² konvergiert die
     Iteration k_B nicht (B_Leiter bleibt 12,3–12,5 T, egal wie klein B0) → j=15 A/mm².
  4. Kraefte ~1000× W7-X (2 MN): Stuetzstruktur ist das Hauptproblem der Baubarkeit.
  5. Bekannte Studien zum Vergleich (aus dem Gedaechtnis, ungeprueft): HELIAS 5-B R0 ≈ 22 m,
     B0 ≈ 5–6 T (Nb3Sn); Stellaris (HTS) R0 ≈ 12–13 m, B0 ≈ 9 T; ARIES-CS R0 ≈ 8 m (A≈4,5).
     Seitenverhaeltnis-Empfindlichkeit (HTS): A=4 → 9,9 m, A=5 → 11,1 m, A=8 → 15 m.
- **Fundstelle:** `invers/stufe0_bilanz.py`, `invers/beispiele/qa_nfp2/` (bilanz_1GW.json, spulen.json),
  Faelle `stellarator/faelle/qa_nfp2_1GW_{HTS,Nb3Sn}.json`, Bilder `docs/bilder/qa_1GW_*`.
- **Fix nebenbei:** `cad.abstaende` filterte Nachbarpaare per Schwerpunktabstand 3 m → bei R0 > 10 m
  keine Paare (IndexError). Jetzt Mittellinien-Abstand ≤ 3×Diagonale; W7-X unveraendert 68 mm.
- **Status:** ✅ 0-D-Auslegung (±30 %), Stufe 3 gesichert. ⚠ Physik von Stufe 0 einfach (ISS04,
  Sudo, keine Zyklotronstrahlung, kein Divertor); Kraefte/Struktur offen.

### B-017 | Inverse Kette funktioniert: Zielfeld (DESC) -> Spulen (simsopt) -> Pruefung (2026-10-24)
- **Beobachtung:** Fuer den kompakten QA-Stellarator (nfp=2, A=6, iota 0,42) laeuft die Kette
  Plasmaform → Spulen → Feldlinien/Geometrie durch. Getestet mit der DESC-Referenzform
  precise_QA (Stufe 1 eigener Lauf `qa_nfp2` laeuft noch). Die Spulen aus Stufe 2 erzeugen in der
  unabhaengigen Pruefung (eigener Biot-Savart, Feldlinien) genau das Zielfeld.
- **Messung:** Stufe 2 (simsopt, 16 Spulen, 4 Basis, 213 s CPU): |B·n|/|B| Mittel 0,24 %, max 1,0 %;
  Laenge 18,0 m (4 Basis); Abstand Spule-Spule 0,100 m, Spule-Plasma 0,300 m; Biegeradius min 0,18 m.
  Stufe 3 (`bewerte`, R0 1 m, B0 1 T, 4 s): iota 0,421 → 0,415 (Ziel 0,42), Spiegelverhaeltnis
  0,16 %, 12/12 Linien auf intakten Flaechen bis r_eff 0,28 m, Spalt (0,04-m-Pakete) 29 mm.
  W7-X-Bewertung nach Verallgemeinerung unveraendert (13,48 kA, iota 0,858 → 0,921, 68 mm).
- **Fundstelle:** `invers/stufe1_desc.py`, `invers/stufe2_spulen.py`, `stellarator/spulen.py`
  (`lade_spulensatz`), `stellarator/faelle/ref_precise_QA.json`, `sim/invers/`,
  `sim/stellarator/bewertung/ref_precise_QA/`. Skill `stellarator-invers`.
- **Status:** ✅ Kette verifiziert an Referenz. ⏳ eigene Plasmaform `qa_nfp2` (Stufe 1, GPU).

### B-016 | Achse falsch (Z-Vorzeichen) → Kalibrierung; Elmer-Stromrichtung; Bewertungsfunktion (2026-10-24)
- **Beobachtung:** (1) `spulen.achse()` (simsopt zoo.py) hat in unserer Spulenkonvention das
  falsche Z-Vorzeichen: bei phi=18°/54° 0,62 m neben der echten Achse (nahe Spulen, |B| 2,87
  statt 2,26 T). Mit −Z stimmt sie auf 0,2 mm mit der verfolgten Achse (Fixpunkt der
  Periodenabbildung). Folge: `kalibriere()` skalierte auf ein falsches Mittel → alle bisherigen
  Stromangaben fuer "<B_Achse> = 2,5 T" zu klein. Korrigiert in `spulen.achse`.
  (2) Elmer-CoilSolver ignoriert das Vorzeichen von `Desired Current Density` und waehlt die
  Richtung selbst → 70-Spulen-Lauf: alle 25 gespiegelten Spulen falsch herum (B Achse 1,38 statt
  2,50 T). Abhilfe: `Coil Center`/`Coil Normal` je Component (Flaechenvektor x sign(I) x
  NORMAL_VZ=−1), J positiv; automatische Pruefung `elmer.richtung_pruefen`.
  (3) Neue Bewertungsfunktion `stellarator/bewerte.py` (~10 s/Fall, nur Biot-Savart).
- **Messung:** Standardfall (B0 = 2,5 T Mittel auf verfolgter Achse): **13,48 kA/Wdg** (bisher
  12,18), |B| Achse 2,40/2,50/2,62 T, Spiegelverhaeltnis 0,043, iota 0,858 → 0,921 (intakte
  Flaechen bis r_eff 0,57 m, dann 5/5-Inseln), B_max Wickeloberflaeche 4,52 T, Spalt 68 mm.
  PCA=PCB=+0,2 MA-Wdg: 12,83 kA, iota 0,796 → 0,932 (r_eff 0,76 m). −0,2 MA-Wdg: 14,21 kA,
  iota 0,934 → 1,028 (r_eff 0,60 m). Elmer-Richtungstest 2 Spulen (n/f): beide korrekt.
- **Fundstelle:** `stellarator/spulen.py` (achse), `stellarator/bewerte.py`, `stellarator/elmer.py`,
  `sim/stellarator/bewertung/bew_*/kennzahlen.json` + `poincare.png`.
- **Status:** ✅ Achse/Kalibrierung, Bewertung. ⚠ Bisherige Zahlen in B-012, Bericht v0.2 und
  `sim/stellarator/w7x_standard/ergebnis.json` (12,18 kA; |B| 2,17/2,50/2,87 T) beruhen auf der
  falschen Achse → Standardlauf (`stellarator.lauf`) neu rechnen, Bericht aktualisieren.
  ✅ Elmer 70 Spulen (korrigierte Richtung, 3,28 Mio. Tets, h_spule 0,05, 680 s, 10,4 GB):
  Stromrichtung alle korrekt; |B| Achse Mittel 2,504 T (Elmer) vs. 2,501 T (Biot-Savart),
  Fehler auf der Achse Median 0,24 %, max 1,1 %; nahe Spulen (0,2–0,8 m) Median 4,6–4,8 %
  (wie Einzelspule bei h 0,05). Kalibrierung mit korrigierter Achse bestaetigt (BS 2,501 T).
  `sim/stellarator/elmer_w7x_70/` (ergebnis.json, erg/feld_t0001.vtu, vergleich_linie.png).
  ✅ Standardlauf neu (`stellarator.lauf`, 2026-10-24, 141 s): 13,49 kA/Wdg (bewerte 13,48),
  B(phi=0) 2,618 T, B_max Wickelpaket (Voxel) 4,33 T, Netto-Kraft NPC1 2,05 MN (alt 1,67;
  Faktor (13,49/12,18)^2 = 1,23 ✓), iota 0,858 .. 1,10 unveraendert. Alt gesichert:
  `sim/stellarator/w7x_standard/ergebnis_alt_achse_falsch_20261023.json`. Bericht-Text noch v0.2.

### B-015 | Geometrie ohne PicoGK baubar: CAD (STEP) + Elmer-Magnetostatik verifiziert (2026-10-24)
- **Beobachtung:** Alle 70 Wickelpakete (0,192 x 0,160 m) lassen sich mit gmsh/OpenCASCADE
  als Volumen bauen (STEP), kollisionsfrei, und in Elmer (CoilSolver + WhitneyAVSolver)
  rechnen. Robust NUR: Rechteckprofil je Filamentpunkt, zwei Haelften als ruled-Loft, fuse.
  Nicht robust: Sweep/addPipe (OCC-Fehler bei 1–3 von 7 Basisspulen), geschlossener Loft,
  glatter Loft (Oberflaechennetz selbstschneidend, "PLC Error").
- **Messung:** Volumen ist/soll 0,997–1,004 (7 Basisspulen, 80–200 Punkte). 390 Nachbarpaare
  ohne Ueberlapp; min. Mittellinienabstand 279 mm (Diagonale Wickelpaket 250 mm); min.
  Biegeradius 0,40 m NPC / 0,58 m PC. Elmer 1 NPC vs. Biot-Savart (5x5 Filamente), Median
  0,2–0,4 m Abstand: 6,8 % (44k Tets, Rand 5 m) → 2,7 % (283k, 26 s, 0,95 GB) →
  1,9 % (869k, 98 s, 2,8 GB); Rand 1,5 m: Fernfeld −37 %. RAM ~3,2 KB/Tet.
- **Fundstelle:** `stellarator/cad.py`, `stellarator/elmer.py`,
  `sim/stellarator/w7x_standard/cad/`, `sim/stellarator/elmer_einzelspule/`.
  Schnelle Spaltpruefung ohne CAD (`cad.abstaende`, 1,5 s statt > 45 min OCC-Boolean):
  min. Spalt 68,3 mm (NPC2–NPC3), keine Durchdringung; Kontrolle 0,40x0,30 m → −104 mm,
  erkannt. → Einzelgehaeuse 60 mm/Seite passt nicht (braucht 120 mm).
- **Status:** ✅ gesichert (Einzelspule). Alle 70 Spulen in Elmer: offen (RAM-Abschaetzung noetig).

### B-014 | PicoGK headless: zwei API-Fehler, Umgehung verifiziert (2026-10-23)
- **Beobachtung:** (1) `Voxels.bIsInside` meldet ~50 % der Aussenpunkte nahe der
  Oberflaeche als „innen" (Belegung 52,9 m3 statt 19,3 m3). `ScalarField.bGetValue`
  liefert dagegen korrekte Abstaende mit richtigem Vorzeichen (auch inaktive Voxel).
  (2) `CalculateProperties` nach Boolean: Gehaeuse 51,6 m3, aus dem Netz 33,3 m3.
- **Messung:** SDF-Diagnose an 7108 Punkten; Belegung PicoGK-SDF 154 640 vs.
  analytisch 154 588 Zellen (0,03 %).
- **Fundstelle:** `picogk/StellaratorVoxel/Program.cs` (SDF-Export statt bIsInside),
  `stellarator/picogk_bruecke.py` (`abstand_python` = Gegenprobe), Skill `picogk-voxel`.
- **Status:** ✅ gesichert, umgangen.

### B-013 | Grenzen: Voxelfeld zerstoert Flussflaechen; B_max unterschaetzt (2026-10-23)
- **Beobachtung:** (a) Voxel-FFT-Feld (h=50 mm, Fehler ~0,25 %) ergibt in der
  Feldlinienverfolgung keine geschlossenen Flussflaechen (iota an der Achse stimmt:
  0,864 vs. 0,858). Ursache: kartesisches Gitter bricht die 5-fache/Stellarator-
  Symmetrie → resonantes Fehlerfeld (W7-X-Toleranz dB/B ~1e-4). Kubische statt
  trilineare Interpolation verbessert nur wenig.
  (b) B_max am Wickelpaket 3,91 T (Voxel) / 4,09 T (Filament-BS an der Oberflaeche)
  vs. Literatur 6,7 T @ 3 T ≈ 5,6 T @ 2,5 T.
- **Messung:** `sim/stellarator/w7x_standard/poincare.png`, `ergebnis.json`
  (rueckfuehrung.B_max_*).
- **Fundstelle:** `stellarator/lauf.py` (feldlinien, rueckfuehrung).
- **Status:** ⚠ offen — (a) Flussflaechen nur mit Biot-Savart; Abhilfe:
  Zylindergitter einer Feldperiode. (b) Mehrfilament-Wickelpaket + realer Querschnitt.

### B-012 | W7-X real: Pipeline Geometrie→PicoGK→Voxelsolver→Feldlinien (2026-10-23)
- **Beobachtung:** Reale W7-X-Filamente (simsopt `W7-X.dat`, CAD-Satz w7x_v001,
  7 Basis → 70 Spulen) liefern die bekannte Physik: bohnenfoermige Flussflaechen,
  iota 0,858 (Achse) … 0,937 (r_eff 0,6 m), 5/5-Inselkette bei iota=1.
  Eigener FFT-Voxelsolver (Hockney) stimmt mit exaktem Biot-Savart ueberein.
- **Messung (w7x_standard, <B_Achse>=2,5 T):** 12,18 kA/Wdg (NPC, 108 Wdg);
  fuer B(phi=0)=2,5 T: 12,9 kA (IAEA ~12,8 kA ✓). |B| Achse 2,17/2,50/2,87 T.
  Voxelsolver vs. BS: Achse max 1,3 %; Flussflaechen Median 0,25 %, max 2,0 %;
  Abstand >0,3 m zum Filament Median 0,25–0,49 %. Loesung 1,4 s (292x296x88).
  Netto-Lorentzkraft NPC1..5: 1,67/1,86/1,91/1,68/1,08 MN; Summe aller 0,05 MN.
  Wickelpaket Soll 19,31 m3, PicoGK-Netz 18,96 m3; Gehaeuse (60 mm) 33,32 m3.
- **Fundstelle:** `stellarator/` (Paket), `stellarator/faelle/w7x_standard.json`,
  `sim/stellarator/w7x_standard/ergebnis.json`, Bericht `bericht/bericht.pdf` (v0.2).
  Start: `.venv/bin/python -m stellarator.lauf stellarator/faelle/w7x_standard.json --bericht`.
- **Status:** ✅ gesichert. Offene Fragen #3/#4 (Elmer-3D-Stromquelle, Mesh) fuer die
  Luftfeldberechnung damit hinfaellig (Biot-Savart exakt, Voxelsolver validiert).

### B-011 | Altes parametrisches Modell ist keine Stellarator-Topologie (2026-10-23)
- **Beobachtung:** In `geo/parametrische_generierung.py` umschliessen 20 von 50
  „NP"-Ellipsen (r0 = 5,05 und 5,95 m, Breite 0,6 m) die Achse R=5,5 m nicht; die
  „P"-Elemente sind horizontale Baender bei z=±0,6 m. Die Strom-Uebereinstimmung
  aus B-009/B-010 (0,90x) ist damit nicht belastbar. Die Annahme „reale Centerlines
  nicht verfuegbar" (B-010) war falsch: simsopt-Wheel (PyPI) enthaelt sie.
- **Messung:** Windungszahl jeder NP-Kurve um (R=5,5, Z=0): 30/50 = 1, 20/50 = 0.
- **Fundstelle:** Pruefskript ad hoc (2026-10-23), `geo/parametrische_generierung.py`.
- **Status:** ✅ gesichert. B-009/B-010 → ueberholt durch B-012; v0.1-Bericht
  archiviert unter `bericht/v0.1/`.


### B-010 | Stromabweichung konsistent + Quellenlage (2026-10-23)
> **Status 2026-10-23: UEBERHOLT** durch B-011 (Modell keine Stellarator-Topologie) und B-012 (reale Filamente).
**Basis:** Ampere-Turns bei B=2.5 T (Modell-Kalibrierpunkt) — nicht Drahtstrom
per se, sondern N·I je Spule.

**Messung (frischer Lauf 2026-10-23, `geo/w7x_gen/PARAMETER.json`):**
- Modell thin wire (N=1, I=1.244 MA je Spule):  **1.24 MA-A-Turns/Spule**
- W7-X-NPC real (N=108, I=12.8 kA bei 2.5 T; IAEA FT2-3): **1.38 MA-A-Turns/Spule**
- **Verhältnis 0.90× — korrekt** (Feld pro Ampere stimmt).
- Drahtstrom-Äquivalent: 1.244 MA/1 Draht vs. 1.244 MA/108 = 11.5 kA vs. real
  12.8 kA → 0.90×.
- **Die früher genannte ~2.9×-Abweichung** gilt NICHT für das Feld-Budget,
  sondern als **Drahtstrom-Multiplikator**: thin wire muss den vollen 2.5 T
  Feld mit 1 Draht erzeugen → 108× mehr A auf einen Draht; das ist der
  "Strom in der Spule" im thin-wire-Sinn, kein Feld-Fehler.

**Fundstelle:**
- Modell: `geo/w7x_gen/PARAMETER.json` (frisch, 2026-10-23)
- W7-X: skill `cae-ingenieurs-doku`, `references/w7x-eckdaten.md` (IAEA FT2-3,
  Bosch 2005, IPP 2003 als Primärquellen).
- B-009 BEFUNDE.md (thin-wire-Basis).

**Status:** FELD-BUDGET korrekt (0.90×). L/E (15.8 µH/12.2 MJ vs 5.8 H/620 MJ)
IST der N²=108²=1.16e4-Effekt → korrekt (thin-wire-Regel). Centerlines aus
simsopt/DESC/STELLOPT: **nicht verfügbar** (404, 2026-10-23 geprüfte Endpunkte —
s. w7x-eckdaten.md).


### B-009 | Parametrische Generierung: W7-X-analoges Spulensystem (2026-10-23)
> **Status 2026-10-23: UEBERHOLT** durch B-011/B-012.
- **Beobachtung:** Das 70-Spulensystem (50 NP + 20 P, 5 Feldperioden, R0=5.5 m)
  wird parametrisch generiert (thin-wire Biot-Savart), Kalibrierung auf
  B_Achse = 2.5 T. I = 1.24 MA/Schleife; 120 Windungen/Schleife →
  10.4 kA/Wicklung [Referenz IPP: 17.8 kA, 6.8 T am Spulenrand — Größenordnung ✓].
  L/E als thin-wire-Artefakt gekennzeichnet (nahe der Drahtsingularität mesh-abhängig,
  nur Größenordnungs-Vergleich mit W7-X L=5.803 H, E=620 MJ sinnvoll).
- **Messung:** `w7x_gen/PARAMETER.json` (I=1244051 A, B_axis=2.500 T exakt),
  `feld_verteilung.png` (links: axiales Radialprofil, rechts: poloidale Karte φ=0),
  `spulen.obj` (15840 Knoten, 5-Fach-Symmetrie sichtbar, BBox x/y ±6.2 m, z ±0.6 m).
- **Fundstelle:** `geo/parametrische_generierung.py` (246 Zeilen, venv: numpy+matplotlib),
  `geo/w7x_gen/` (PARAMETER.json, feld_verteilung.png, spulen.obj).
  Start: `.venv/bin/python geo/parametrische_generierung.py --out w7x_gen --obj`.
- **Status:** ✅ gesichert · Spulengeometrie-Frage (Offene Fragen #1) damit
  beantwortet: parametrisch generiert als W7-X-analoges Referenzsystem.
  Nächster Schritt: Vergleich mit offenen W7-X-Daten (ConStellaration/alphastell)
  oder direkte Übernahme dieser Parametrisierung in die 3D-Sim.

### B-008 | 2D-Validierung ERFOLGREICH — Elmer vs. Biot-Savart (2026-10-23)
- **Beobachtung:** Elmer 2D-planare Magnetostatik (gerader Draht) ist VERIFIZIERT.
  Offizieller Elmer-Referenztestfall `mgdyn2D_steady_wire` läuft 1:1 lokal:
  `ElmerGrid 1 2 wire2d.grd` (natives strukturiertes revolutioniertes Grid,
  radial) → `ElmerSolver case.sif` → **TEST.PASSED**, relative Abweichung zur
  Elmer-Referenznorm **3.1e-10**. Eigenständige Biot-Savart-Prüfung an `f.dat`
  (R=1 mm, I=1 A, Außenrand 5 mm, Az=0 BC):
  - Innerhalb Draht: H(r) linear, Mittelabweichung **+0.09 %**
  - Außerhalb: H(r)=I/(2πr), Mittelabweichung **+2.09 %** (typisch ≤ 2 %)
  - Max-Abweichung +13.5 % liegt NUR am Randknoten r=5 mm (Az dort per
    Dirichlet fixiert → erwartetes BC-Artefakt, aus Auswertung ausgeschlossen).
  **Root Cause der 22.10.-Fehlschläge (A_z ≡ 0):** (a) gmsh-CLI MSH 4.1 →
  ElmerGrid "non-conforming" + Body-Renummerierung; (b) SIF-Syntax falsch:
  `Equation "MGDynamics2D"` (nicht "MgDyn2D"), `Variable "Az"` (nicht
  "Potential"), Strom als **`Body Force → Current Density = -distribute <I>`**
  in A (gesamter Strom wird auf den Körper verteilt) statt rohem A/m²,
  plus 2. Solver `MagnetoDynamicsCalcFields` für B/H/J; (c) natives
  ElmerGrid-`.grd` liest ElmerGrid zuverlässig → gmsh-MSH-Thema umgangen.
- **Messung:** `solve.log`: "Relative Error to reference norm: 3.097e-10",
  "ELMER SOLVER FINISHED"; Zahlen-Tabelle + Diagramm `ergebnis.png`.
- **Fundstelle:** `sim/pipeline/gerader_draht/validiert/`
  (case.sif, wire2d.grd, f.dat, plot_ergebnis.py, ergebnis.png,
  solve.log, TEST.PASSED); Original: `sim/pipeline/gerader_draht/reference/`.
  Reproduzierbar: `sim/pipeline/gerader_draht/run_validierung.sh`.
- **Status:** ✅ gesichert · Validierungspfads-Frage (Offene Fragen #2)
  damit beantwortet: 2D-Pipeline ist verifiziert und bereit.

### B-007 | FreeCAD + Workflow-Referenz gefunden (2026-10-22)
- **Beobachtung:** FreeCAD 1.1.1 headless funktioniert:
  `cd ~/freecad_1.1_quellcode && ~/.pixi/bin/pixi run --manifest-path pixi.toml -- build/release/bin/FreeCADCmd -c …`
  (Test: Part.makeCircle OK). `/opt/freecad-1.1` ist 1.2 mit Visualisierungs-Bug.
  `~/ai-workspace/cae_orchestrator` enthält die bewährte Elmer-3D-Magnetostatik-Pipeline
  (`ema_axial_em3d.py`: WhitneyAVSolver+MUMPS-Direkt, Body-Force, Periodic BC+Lagrange;
  `elmer_runner.py`: ElmerGrid 14 2, ElmerSolver; `freecad_runner.py`: PATH-Venv-Falle =
  venv-bin aus PATH streichen, sonst 0-Knoten-Mesh ohne Warnung).
- **Messung:** FreeCADCmd -c Test; sed ema_axial_em3d.py.
- **Fundstelle:** ~/freecad_1.1_quellcode, ~/ai-workspace/cae_orchestrator.
- **Status:** ✅ gesichert · B-004 damit aufgelöst.

### B-006 | Elmer-Doku: 2D-Planar, 3D-Solver (2026-10-22)
- **Beobachtung:** Elmer 9.0 MagnetoDynamics: 2D Axisymmetric → MagnetoDynamics2D
  (Equation = MgDyn2D), 3D → MagnetoDynamics (Equation = MgDyn), A-Feld via
  WhitneyAVSolver, Strom als Body-Force `Current` (J = A/m^2), Material:
  `Magnetic Permeability` + `Electric Conductivity`.
- **Messung:** ElmerModelsManual (Kap. Elektromagnetik, Zeilen 7372–9941),
  ElmerSolverManual.
- **Fundstelle:** `/tmp/elmerdoc/models.txt`, `/tmp/elmerdoc/sol.txt`.
- **Status:** ✅ gesichert.

### B-005 | Recherche: W7-X-Spezifikation, offene Daten (2026-10-22)
- **Beobachtung:** W7-X (IPP Greifswald): 50 nichtplanare (5 Unikate x 10) +
  20 planare Spulen (2 Unikate x 10), R0=5.5 m, a=0.53 m, V=30 m^3, B0=2.5 T,
  iota/2pi=5/6 bis 5/4, NbTi @ 17.8 kA, B=6.8 T am Spulenrand, 254 Ports,
  16 m Durchmesser, 4.5 m hoch, 725 t. Offene Daten: ConStellaration HF
  (proximafusion, 150k+ QI-Equilibria), alphastell (VMEC zu STEP).
- **Messung:** web_search (Wikipedia, FusionWiki, FtI TOFE 2004, HuggingFace).
- **Fundstelle:** forschung/ANALYSE-001 (dort komplett).
- **Status:** ✅ gesichert.

### B-004 | FreeCAD: Installation ueber Paketquelle nicht moeglich (2026-10-22)
- **Beobachtung:** FreeCAD liess sich nicht ueber die Paketverwaltung installieren; Blender war vorhanden.
- **Status:** ✅ AUFGELOST (2026-10-22, s. B-007: FreeCAD 1.1.1 aus dem Quellcode gebaut,
  headless verifiziert). Seit 2026-10-24 zusaetzlich FreeCAD 1.1.4 als AppImage (B-020).

### B-003 | gmsh-Versionen, Python-API-Einschränkungen (2026-10-22)
- **Beobachtung:** System-gmsh 4.12.1 (CLI mit OCC-Booleschen OK); venv-gmsh
  4.15.1 (Python): API teils anders — `gmsh.model.occ.cut` statt difference,
  `gmsh.model.occ.add_cylinder` 9-Parameter.
- **Messung:** `gmsh -version`; Python-Import gmsh + API-Liste.
- **Fundstelle:** Terminal-Abfragen am 2026-10-22.
- **Status:** ✅ geklärt (CLI bevorzugt).

### B-002 | ElmerFEM 9.0 installiert, verifiziert (2026-10-22)
- **Beobachtung:** `elmerfem-csc 9.0-0ppa0-202610092044~b17662e9b~ubuntu24.04.1`;
  ElmerGrid vorhanden; .so: StatMagSolve, MagnetoDynamics, MagnetoDynamics2D,
  libelmersolver (MUMPS gelinkt).
- **Messung:** `dpkg -l elmerfem-csc`; `ls /usr/share/elmersolver/lib/`;
  `strings libelmersolver.so | grep MUMPS`.
- **Fundstelle:** apt PPA elmer-csc-ubuntu (Build 2026-10-09).
- **Status:** ✅ installiert.

### B-001 | Projektstruktur fusion/ angelegt (2026-10-22)
- **Beobachtung:** `~/hermes/fusion` nach wasserstoff-Vorlage:
  ERINNERUNGEN.md, BEFUNDE.md, forschung/ (research_stack.py, ANALYSE-001,
  references/), geo/, cad/, sim/pipeline/gerader_draht/, rechen/, bericht/,
  .venv/ (numpy scipy meshio gmsh pyvista).
- **Messung:** `find ~/hermes/fusion -maxdepth 3`.
- **Fundstelle:** Shell-Aufrufe am 2026-10-22.
- **Status:** ✅ gebaut.

---
Neue Einträge: oben. Status-Legende wie oben.
## B-057 Gegenprüfung der Strom-Ausreißer mit freier Grenze: keine konvergiert (2026-11-06) ❌ WIDERLEGT durch B-061: falsch aufgerufen

Erwartung F-254 (vorher): 008 und 037 frei bei 0,00040–0,00043, die ±50-%-Fälle über 0,0005 oder nicht konvergent. Ergebnis (VMEC++ free-boundary, Standardeinstellungen, `sim/qi_spulen/faelle/i_p008_b056, i_p037, i_w588_u50, i_w470_u50`): **alle vier nicht konvergiert** ("did not converge"; bei den ±50-%-Fällen JACOBIAN_75_TIMES_BAD). Erwartung also nur halb getroffen: für die ±50-%-Fälle ja, für die beiden ±5-%-Proben nein (ich hatte Konvergenz erwartet, weil i_opt am Rand von ±5 % konvergierte). Folge: Der Wert 0,000392 (B-056) und die Wegs-ii-Werte 0,00019 sind **nicht bestätigt**; belegt bleibt nur i_opt frei 0,000415. Nicht geprüft: ob andere Solver-Einstellungen (ftol, niter, nvacskip) Konvergenz bringen. Nutzerhinweis: Fehlerort durch fortgesetztes Halbieren eingrenzen (Strecke Basis → Probe 008, Fälle i_p008_t0.25/0.5/0.75, Lauf angestoßen 21:20).

B-057 Nachtrag (2026-11-07 08:26, Halbierung Basis → Probe 008): t = 0,25 / 0,5 / 0,75 **alle nicht konvergiert** (Läufe 21:19–21:31). Schon bei t = 0,25 (Stromfaktoren höchstens 1,2 % von der Basis) bricht die freie Grenze mit Standardeinstellungen ab. Erwartung "Kante irgendwo in der Mitte" verfehlt: Das Scheitern hängt nicht an der Stromgröße, sondern an der Rechnung (Einstellungen/Empfindlichkeit); auch die Basis selbst (`basis_ftol1e-15_nicht_konvergiert`) konvergierte nur mit Sonderzuständen. Nächste Halbierung: t = 0,125 und 0,06; zusätzlich Basis mit denselben Einstellungen wie die konvergierten i_-Fälle neu rechnen.
