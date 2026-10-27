# FluidX3D – geänderte Dateien (altered source version)

> **Achtung: Für diesen Ordner gilt NICHT die MIT-Lizenz des Repositorys, sondern die FluidX3D-Lizenz
> ([LICENSE.md](LICENSE.md)).** FluidX3D ist kostenlos nur für nicht kommerzielle Nutzung (Forschung, Lehre,
> privat), der Quelltext ist einsehbar, es ist aber keine Open-Source-Lizenz.
>
> *This folder is NOT under the repository's MIT licence but under the FluidX3D licence (LICENSE.md):
> free for non-commercial use only, source-available, not open source.*

[FluidX3D](https://github.com/ProjectPhysX/FluidX3D) ist ein Lattice-Boltzmann-Strömungslöser für GPUs von
Dr. Moritz Lehmann. Dieses Projekt hat damit die Strömung im Kühlsegment des Plasmagefäßes gerechnet
(`stellarator/kuehlung_cfd.py`). FluidX3D selbst ist hier **nicht** enthalten. Die Lizenz verlangt, dass geänderte
Quelltexte veröffentlicht werden, wenn Ergebnisse daraus veröffentlicht werden. Deshalb liegen hier die beiden
geänderten Dateien von FluidX3D v3.8 (Commit `50150a7`), jeweils als geänderte Fassung gekennzeichnet:

| Datei | Ersetzt | Änderung |
|---|---|---|
| `setup_kuehlsegment.cpp` | `src/setup.cpp` | Beispiel-Setups ersetzt durch den Fall „Kühlsegment“: Belegung der Gitterzellen aus PicoGK (`.bin`) oder Netz (STL), Ein- und Austritt als TYPE_E, Ausgabe des Strömungsfelds |
| `defines.hpp` (+ `defines.hpp.diff`) | `src/defines.hpp` | `BENCHMARK` aus, `EQUILIBRIUM_BOUNDARIES` und `SUBGRID` an |

Verwendung: FluidX3D v3.8 selbst klonen, die beiden Dateien an ihre Stelle kopieren, dann
`stellarator/kuehlung_cfd.py` (erwartet die Arbeitskopie unter `~/fluidx3d_stellarator`).

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
