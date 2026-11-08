"""Abwicklung der Spulen (Montagesicht): toroidaler Winkel phi über poloidalem Winkel theta um die Plasmaachse.
Montagegerecht: jede Linie läuft einmal von unten nach oben ohne Rücklauf und kreuzt keine Nachbarlinie.
Aufruf: python montage_bild.py <bild.png> <name=satz_ordner> ...   (Ausschnitt 0..90 Grad phi)"""
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import lade_satz  # noqa: E402
from spulen_montage import achse, abwicklung  # noqa: E402
from simsopt.field import Current, coils_via_symmetries  # noqa: E402

saetze = [a.split("=", 1) for a in sys.argv[2:]]
fig, axs = plt.subplots(1, len(saetze), figsize=(5.2 * len(saetze), 6), squeeze=False)
for ax, (name, ordner) in zip(axs[0], saetze):
    basis, I, nfp = lade_satz(ordner); A = achse(Path(ordner) / "boundary.json")
    for j, c in enumerate(coils_via_symmetries(basis, [Current(float(x)) for x in I], nfp, True)):
        g = c.curve.gamma(); g = np.vstack([g, g[:1]]); ph, th, r = abwicklung(g, A)
        ph = np.degrees(np.unwrap(ph)); th = np.degrees(np.angle(np.exp(1j * th)))
        if not (-20 < np.mean(ph) % 360 < 110):
            continue
        ph = ph - 360 * np.round((np.mean(ph) - 45) / 360)
        sprung = np.abs(np.diff(th)) > 180; th = th.astype(float); ph = ph.astype(float)
        th = np.insert(th, np.nonzero(sprung)[0] + 1, np.nan); ph = np.insert(ph, np.nonzero(sprung)[0] + 1, np.nan)
        ax.plot(ph, th, color="C3" if r > 0 else "C0", lw=1.3)
    ax.set_xlim(-5, 95); ax.set_ylim(-180, 180); ax.set_xlabel("toroidaler Winkel φ (um die Torusachse), Grad")
    ax.set_ylabel("poloidaler Winkel θ (um das Plasma), Grad"); ax.set_title(name, fontsize=9); ax.grid(alpha=.3)
fig.suptitle("Abwicklung, Ausschnitt 0–90°: blau = ohne Rücklauf, rot = Spule läuft in θ zurück. Plasma DATJ5FC (DATENSATZ-Form, unverändert), EIGENE Spulen", fontsize=10)
fig.tight_layout(); fig.savefig(sys.argv[1], dpi=105)
