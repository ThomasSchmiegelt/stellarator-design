"""wandstueck_beschriften.py — Schichten im Blender-Bild des Wandstuecks beschriften.

    .venv/bin/python -m stellarator.wandstueck_beschriften sim/wandstueck/d1

Liest <ordner>/wandstueck.png und anker.json (Bildpositionen aus blender_wandstueck.py),
schreibt <ordner>/wandstueck_beschriftet.png.
"""
import json, sys
from pathlib import Path

# Textposition (Anteil Bildbreite/-hoehe) je Anker aus blender_wandstueck.py
ZIEL = {"Plasmaseite / Innenhaut 5 mm": (0.08, 0.84), "Kühlkanäle 6×6 mm (Wasser 60→150 °C)": (0.69, 0.90),
        "Rückwand 5 mm": (0.69, 0.74), "Gyroid trocken (Steifigkeit)": (0.69, 0.42), "Außenhaut 40 mm": (0.69, 0.12)}
UMBRUCH = {"Kühlkanäle 6×6 mm (Wasser 60→150 °C)": "Kühlkanäle 6×6 mm\nWasser 60 → 150 °C"}


def main(argv=None):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    O = Path((argv or sys.argv[1:])[0])
    im = Image.open(O / "wandstueck.png"); W, H = im.size
    A = json.loads((O / "anker.json").read_text())
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(im); ax.axis("off")
    for k, (x, y) in A.items():
        tx, ty = ZIEL[k]
        ax.annotate(UMBRUCH.get(k, k), (x * W, y * H), (tx * W, ty * H), color="#f2f3f5", fontsize=20, weight="bold",
                    va="center", arrowprops=dict(arrowstyle="-", color="#f2f3f5", lw=1.5))
    ax.text(0.02 * W, 0.05 * H, "Doppeltes Filament: innen Kühlung, außen trockener Gyroid für die Steifigkeit",
            color="#f2f3f5", fontsize=24, weight="bold")
    ax.text(0.02 * W, 0.97 * H, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell · Ausschnitt 450×450×900 mm",
            color="#b9bdc7", fontsize=16)
    fig.savefig(O / "wandstueck_beschriftet.png", dpi=100)


if __name__ == "__main__":
    main()
