# FluidX3D – geänderte Dateien (altered source version)

> **Achtung: Für diesen Ordner gilt NICHT die MIT-Lizenz des Repositorys, sondern die FluidX3D-Lizenz
> ([LICENSE.md](LICENSE.md)).** FluidX3D ist kostenlos nur für nicht kommerzielle Nutzung (Forschung, Lehre,
> privat), der Quelltext ist einsehbar, es ist aber keine Open-Source-Lizenz.
>
> *This folder is NOT under the repository's MIT licence but under the FluidX3D licence (LICENSE.md):
> free for non-commercial use only, source-available, not open source.*

[FluidX3D](https://github.com/ProjectPhysX/FluidX3D) ist ein Lattice-Boltzmann-Strömungslöser für GPUs.
Dieses Projekt hat damit die Strömung im Kühlsegment des Plasmagefäßes gerechnet
(`stellarator/kuehlung_cfd.py`). FluidX3D selbst ist hier **nicht** enthalten. Die Lizenz verlangt, dass geänderte
Quelltexte veröffentlicht werden, wenn Ergebnisse daraus veröffentlicht werden. Deshalb liegen hier die
geänderten Dateien von FluidX3D v3.8 (Commit `50150a7`), jeweils als geänderte Fassung gekennzeichnet:

| Datei | Ersetzt | Änderung |
|---|---|---|
| `setup_kuehlsegment.cpp` | `src/setup.cpp` | Beispiel-Setups ersetzt durch den Fall „Kühlsegment“: Belegung der Gitterzellen aus PicoGK (`.bin`) oder Netz (STL), Ein- und Austritt als TYPE_E, Ausgabe des Strömungsfelds |
| `defines.hpp` (+ `defines.hpp.diff`) | `src/defines.hpp` | `BENCHMARK` aus, `EQUILIBRIUM_BOUNDARIES` und `SUBGRID` an |

### Fall „Tauscher“ (Zwei-Fluid-Wärmetauscher, 2026-10-31)

Für die Strömungs- und Wärmerechnung der Tauschermodule (`stellarator/tauscher_cfd.py`) wurde eine zweite
Arbeitskopie desselben Stands geändert. Die Änderungen am Löser liegen als Diff gegen Commit `50150a7` vor:

| Datei | Ersetzt / ändert | Änderung |
|---|---|---|
| `setup_tauscher.cpp` | `src/setup.cpp` | periodisches Gebiet aus PicoGK-Belegung, Festzellen als `TYPE_S\|TYPE_T` mit T = 0, Volumenkraft f_z, Ausgabe `stat.txt` (mittlere Geschwindigkeit, Mischtemperatur) und `feld.bin` |
| `defines_tauscher.hpp.diff` | `src/defines.hpp` | `FP16S` aus, `TEMPERATURE` an, `UPDATE_FIELDS` an, `EQUILIBRIUM_BOUNDARIES` und `SUBGRID` an |
| `kernel.cpp.diff` | `src/kernel.cpp` | (1) Anti-Bounce-Back der Temperatur-Verteilungen an Festzellen mit `TYPE_T` (Wand genau zwischen Fluid- und Festzelle); (2) turbulente Diffusivität D_t = ν_t/0,85 aus dem Smagorinsky-Modell; (3) Wärmequelle `def_q_T` in jeder Fluidzelle, gleichmäßig oder proportional u_z (`def_q_u0` > 0, Patankar 1977); (4) Auftriebskopplung nur bei `def_beta ≠ 0`; (5) TRT-Stoß (Ginzburg, Λ = 1/4) statt BGK für die Temperatur, weil BGK bei τ nahe 0,5 instabil wurde |
| `lbm.cpp.diff` | `src/lbm.cpp` | Konstanten `def_q_T` und `def_q_u0` aus den Umgebungsvariablen `FX_Q_T` und `FX_Q_U0` |

Hinweis zum Temperaturmodell (D3Q7): Die Schallgeschwindigkeit ist c_s² = 1/4, die tatsächliche Diffusivität also
D = α/2. `tauscher_cfd.py` übergibt deshalb α = 2D.

Verwendung „Tauscher“: FluidX3D v3.8 (Commit `50150a7`) klonen, `setup_tauscher.cpp` als `src/setup.cpp` kopieren,
die Diffs mit `git apply` einspielen, `make Linux` bauen; `stellarator/tauscher_cfd.py` erwartet eine eigene,
getrennte Arbeitskopie (Pfad im Skript).

Verwendung „Kühlsegment“: FluidX3D v3.8 selbst klonen, die beiden Dateien an ihre Stelle kopieren, dann
`stellarator/kuehlung_cfd.py` (erwartet eine eigene Arbeitskopie, Pfad im Skript).

### Fall „MHD“ (Flüssigmetall im Magnetfeld, 2026-11-01)

Eigene, getrennte Arbeitskopie von FluidX3D v3.8 (Commit `50150a7`). Geändert:

| Datei | Änderung |
|---|---|
| `setup_mhd_kanal.cpp` | ersetzt `src/setup.cpp`: Kanal mit Hartmann-Wänden (y, senkrecht zu B), wahlweise mit Seitenwänden (z), x periodisch; Ausgabe Profil und ganzer Querschnitt |
| `mhd_defines.hpp.diff` | `VOLUME_FORCE` und neue Schalter `MHD` und `MHD_POT` an (`MHD_POT` schaltet `UPDATE_FIELDS` ein), `FP16S` und `BENCHMARK` aus |
| `mhd_lbm.hpp.diff` | Puffer `mhd_phi`, `mhd_phi2` für das Potential, zwei Jacobi-Kernel |
| `mhd_lbm.cpp.diff` | `def_mhd_k` (K = σB²/ρ in Gittereinheiten), `def_mhd_b` (Richtung von B), `def_mhd_wand` (0 alle Wände isolierend, 1 Hartmann-Wände ideal leitend) aus `FX_MHD_K`, `FX_MHD_B`, `FX_MHD_WAND`; vor jedem Zeitschritt `FX_MHD_JACOBI` Jacobi-Doppelschritte (nur eine GPU) |
| `mhd_kernel.cpp.diff` | Lorentzkraft in `stream_collide`: lokaler Teil σ(u×B)×B = −Kρu⊥ halbimplizit zur Guo-Kraft, u⊥ = (u*⊥ + F⊥/2ρ)/(1 + K/2); dazu der Potentialteil +Kρ(E×B), E = −∇φ aus Flächenwerten. Neuer Kernel `mhd_jacobi`: ∇·j = 0 als Flächenbilanz je Zelle, j = −∇φ + u×B; isolierende Wand j·n = 0, leitende Wand φ = 0 auf der Wandfläche |

Prüfungen:
- `stellarator/mhd_hartmann.py`: Platten ohne Seitenwände (Potential spielt keine Rolle). Abweichung zur exakten
  Lösung 0,03 % bei Ha = 0, 0,04 % bei Ha = 5, 0,5 % bei Ha = 30 (32 Zellen), etwa zweite Ordnung im Gitter. Die zuerst
  genannten schlechteren Werte (4,3 % bei Ha = 30) kamen aus der Auswertung: Ohne `UPDATE_FIELDS` berechnet
  `update_fields` die Geschwindigkeit ohne die halbe Lorentzkraft. Mit `MHD_POT` ist `UPDATE_FIELDS` an.
- `stellarator/mhd_kanal.py`: quadratischer Kanal mit isolierenden Wänden (Shercliff) und mit leitenden
  Hartmann-Wänden (Hunt), verglichen mit einem eigenen 2D-Löser in der Formulierung mit induziertem Feld. Bei Ha = 10
  fällt der Fehler mit dem Gitter von 0,75 % auf 0,09 % (Shercliff); alle zwölf Fälle bis Ha = 30 liegen unter 1 %.
  Dabei gefunden: Die Potentialkraft muss vor dem halbimpliziten Teil addiert werden, sonst wächst der Fehler bei
  isolierenden Wänden mit Ha (zuerst 36 % bei Ha = 30).

## Quellen / References

Wer Ergebnisse aus FluidX3D veröffentlicht, zitiert laut Lizenz das Repository und diese Arbeiten:

- M. Lehmann: FluidX3D. https://github.com/ProjectPhysX/FluidX3D
- M. Lehmann: [Computational study of microplastic transport at the water-air interface with a memory-optimized lattice Boltzmann method](https://doi.org/10.15495/EPub_UBT_00006977). PhD thesis, University of Bayreuth (2023)
- M. Lehmann: [Esoteric Pull and Esoteric Push: Two Simple In-Place Streaming Schemes for the Lattice Boltzmann Method on GPUs](https://doi.org/10.3390/computation10060092). Computation 10, 92 (2022)
- M. Lehmann, M. Krause, G. Amati, M. Sega, J. Harting, S. Gekle: Accuracy and performance of the lattice Boltzmann method with 64-bit, 32-bit, and customized 16-bit number formats. Phys. Rev. E 106, 015308 (2022)
- M. Lehmann: Combined scientific CFD simulation and interactive raytracing with OpenCL. IWOCL'22: International Workshop on OpenCL, 3, 1–2 (2022)
- M. Lehmann, L. M. Oehlschlägel, F. Häusl, A. Held, S. Gekle: [Ejection of marine microplastics by raindrops: a computational and experimental study](https://doi.org/10.1186/s43591-021-00018-8). Microplastics and Nanoplastics 1, 18 (2021)
- M. Lehmann: [High Performance Free Surface LBM on GPUs](https://doi.org/10.15495/EPub_UBT_00005400). Master's thesis, University of Bayreuth (2019)
- M. Lehmann, S. Gekle: [Analytic Solution to the Piecewise Linear Interface Construction Problem and Its Application in Curvature Calculation for Volume-of-Fluid Simulation Codes](https://doi.org/10.3390/computation10020021). Computation 10, 21 (2022)
