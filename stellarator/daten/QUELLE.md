# Datenquelle W7-X.dat

- Herkunft: simsopt 1.11.1 (`simsopt/configs/W7-X.dat`, PyPI-Wheel, MIT-Lizenz),
  https://github.com/hiddenSymmetries/simsopt
- Inhalt: Fourier-Koeffizienten (Ordnung 48) der 7 Basis-Spulenfilamente von W7-X
  (5 nichtplanare NPC1..5, 2 planare A/B), CAD-Spulensatz `coils.w7x_v001`
  (J. Geiger, IPP, 2022). Reproduziert die kartesischen Filamentdaten auf ~1e-13 m.
- Format: je Spule 6 Spalten (sin_x, cos_x, sin_y, cos_y, sin_z, cos_z), Zeile m = Mode m.
  Kurvenparameter t in [0,1), Winkel 2*pi*m*t. Einheit: m.
- Symmetrie: nfp=5 Rotation + Stellarator-Symmetrie (Flip (x,-y,-z), Strom * -1) -> 70 Spulen.
- Standardkonfiguration (simsopt): NPC je 15 kA * 108 Windungen, A/B-Spulen 0 A.
- Magnetische Achse (simsopt zoo.py, Standardkonfig.):
  R(phi)=sum cR[n] cos(5 n phi), Z(phi)=sum sZ[n] sin(5 n phi) -> in stellarator/spulen.py.
