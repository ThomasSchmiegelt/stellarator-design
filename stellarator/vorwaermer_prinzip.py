"""vorwaermer_prinzip.py — Prinzipskizze des Divertor-Vorwärmers (für Nicht-Fachleute), DE und EN.

  .venv/bin/python -m stellarator.vorwaermer_prinzip

Zahlen aus der Wärmebilanz und stellarator/vorwaermer.py: Divertor 305 MW, Wasser 130 -> 136 °C bei 5 MPa,
Kondensator 24,7 mbar (20,9 °C), Kondensat 1820 kg/s, Erwärmung um 39,8 K, Obergrenze 73,3 MW statt 0,35 x 305 = 107 MW.
"""
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
WARM, KALT, DAMPF, ANZAPF, TEXT = "#d1495b", "#2a78d6", "#8a8a8a", "#eda100", "#2b2b2b"

T = {
    "de": dict(titel="Divertor-Vorwärmer: Abwärme des Divertors ersetzt Anzapfdampf der Turbine",
               dampferz="Dampferzeuger\n(Wärme aus dem Blanket,\nca. 300 °C)", turbine="Dampfturbine", gen="Generator",
               kond="Kondensator\n21 °C, 24,7 mbar", vw="Vorwärmer\n(Gyroid/Diamond)\n305 MW", weitere="weitere\nVorwärmer",
               div="Divertor\n(Auspuff des Plasmas,\nbis 10 MW/m²)", dampf="Frischdampf", kondensat="Kondensat 21 °C",
               vorgew="ca. 61 °C", divw="136 °C", divk="130 °C", anz="Anzapfdampf: wird eingespart\nund leistet in der Turbine weiter Arbeit",
               strom="bis +73 MW Strom", fuss="Die Wärme des Divertors ist zu kalt, um Dampf zu erzeugen. Sie wärmt stattdessen das kalte Kondensat vor.\n"
               "Dafür muss der Turbine weniger Dampf abgezweigt werden; dieser Dampf erzeugt bis zum Kondensator zusätzlich Strom.",
               trenn="getrennte Kreisläufe,\nWärme geht durch die Stahlwand"),
    "en": dict(titel="Divertor preheater: divertor waste heat replaces turbine bleed steam",
               dampferz="Steam generator\n(heat from the blanket,\nabout 300 °C)", turbine="Steam turbine", gen="Generator",
               kond="Condenser\n21 °C, 24.7 mbar", vw="Preheater\n(gyroid/diamond)\n305 MW", weitere="further\npreheaters",
               div="Divertor\n(exhaust of the plasma,\nup to 10 MW/m²)", dampf="Live steam", kondensat="Condensate 21 °C",
               vorgew="about 61 °C", divw="136 °C", divk="130 °C", anz="Bleed steam: saved,\nkeeps doing work in the turbine",
               strom="up to +73 MW electricity", fuss="The divertor heat is too cold to raise steam. Instead it preheats the cold condensate.\n"
               "Less steam then has to be bled from the turbine; that steam produces extra electricity on its way to the condenser.",
               trenn="separate loops,\nheat passes through the steel wall"),
}


def kasten(ax, x, y, w, h, text, farbe, fs=9.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=farbe, ec=TEXT, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=TEXT)


def pfeil(ax, p, q, farbe, text=None, off=(0, 0.12), ls="-", lw=2.4, fs=8.5, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=farbe, lw=lw, ls=ls))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha=ha, va="center", fontsize=fs, color=farbe)


def bild(sprache):
    s = T[sprache]
    fig, ax = plt.subplots(figsize=(13, 7.2), dpi=130)
    ax.set_xlim(0, 13); ax.set_ylim(-1.0, 7.2); ax.axis("off")
    ax.text(6.5, 6.95, s["titel"], ha="center", fontsize=13, color=TEXT, weight="bold")
    # obere Reihe: Dampferzeuger -> Turbine -> Generator
    kasten(ax, 0.4, 4.6, 2.4, 1.4, s["dampferz"], "#f6dada")
    ax.add_patch(Polygon([[4.6, 4.7], [4.6, 5.9], [7.4, 6.3], [7.4, 4.3]], closed=True, fc="#e7e7e7", ec=TEXT, lw=1.1))
    ax.text(6.0, 5.3, s["turbine"], ha="center", va="center", fontsize=10, color=TEXT)
    kasten(ax, 8.4, 4.9, 1.8, 0.8, s["gen"], "#dff0e3")
    ax.plot([7.4, 8.4], [5.3, 5.3], color=TEXT, lw=3)
    pfeil(ax, (10.2, 5.3), (11.2, 5.3), "#1baf7a")
    ax.text(11.3, 5.3, s["strom"], ha="left", va="center", fontsize=9.5, color="#1baf7a")
    pfeil(ax, (2.8, 5.3), (4.6, 5.3), DAMPF, s["dampf"], off=(0, 0.25))
    # Kondensator
    kasten(ax, 6.6, 2.5, 2.2, 1.0, s["kond"], "#dbe8f7")
    pfeil(ax, (7.2, 4.4), (7.6, 3.5), DAMPF)
    # Anzapfung (gestrichelt, eingespart)
    pfeil(ax, (5.6, 4.55), (4.6, 3.55), ANZAPF, ls="--", lw=2)
    ax.text(3.25, 4.15, s["anz"], ha="center", va="center", fontsize=8.5, color="#a26f00")
    # untere Reihe: Kondensat -> Vorwärmer -> weitere Vorwärmer -> Dampferzeuger
    kasten(ax, 3.6, 2.4, 2.0, 1.2, s["vw"], "#efe6f7")
    kasten(ax, 0.6, 2.55, 1.6, 0.9, s["weitere"], "#eef3fb")
    pfeil(ax, (6.6, 3.0), (5.6, 3.0), KALT, s["kondensat"], off=(0.0, -0.25))
    pfeil(ax, (3.6, 3.0), (2.2, 3.0), "#7a5bd1", s["vorgew"], off=(0, 0.25))
    pfeil(ax, (1.4, 3.45), (1.4, 4.6), KALT)
    # Divertor-Kreis
    kasten(ax, 3.4, 0.35, 2.4, 1.1, s["div"], "#fbe3d6", fs=9)
    pfeil(ax, (5.2, 1.45), (5.2, 2.4), WARM, s["divw"], off=(0.42, 0))
    pfeil(ax, (4.0, 2.4), (4.0, 1.45), KALT, s["divk"], off=(-0.42, 0))
    ax.text(7.6, 1.6, s["trenn"], ha="center", va="center", fontsize=8.5, color=TEXT, style="italic")
    ax.plot([5.65, 6.5], [2.55, 1.85], color=TEXT, lw=0.6)
    ax.text(6.5, -0.9, s["fuss"], ha="center", va="bottom", fontsize=8.8, color=TEXT)
    fig.text(0.99, 0.005, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7, color="#52514e", ha="right")
    name = "vorwaermer_prinzip.png" if sprache == "de" else "vorwaermer_prinzip_en.png"
    fig.savefig(ROOT / "docs" / "bilder" / name, bbox_inches="tight"); plt.close(fig)
    shutil.copy(ROOT / "docs" / "bilder" / name, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return ROOT / "docs" / "bilder" / name


if __name__ == "__main__":
    for s in ("de", "en"):
        print(bild(s))
