"""gesamtbild_kuehlung.py — Gesamtbild der 1-GW-Anlage um die Erkenntnisse aus dem Kuehlsegment erweitern.

    .venv/bin/python -m stellarator.gesamtbild_kuehlung [--alt f10] [--neu f11]

Oben das Blender-Gesamtbild (docs/bilder/gyroid_gefaess_1GW_gesamt.jpg), darunter drei Felder:
Gyroid-Filamente mit Stroemung (Bild aus dem Film), Durchfluss je Umfangssektor alt/neu, Erkenntnisse in Zahlen.
Ausgabe docs/bilder/gyroid_gefaess_1GW_gesamt_kuehlung.jpg.
"""
import argparse, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from .kuehlung_segment import WURZEL

PROJEKT = Path(__file__).resolve().parents[1]
HG, FELD, TEXT, TEXT2, LINIE = "#363a46", "#2b2f3a", "#f2f3f5", "#b9bdc7", "#5a5f6d"
FARBE_ALT, FARBE_NEU = "#8a8f9c", "#3fb8c9"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--alt", default="f10"); ap.add_argument("--neu", default="f11")
    a = ap.parse_args(argv)
    lies = lambda n, d: json.loads((WURZEL / n / d).read_text())
    alt, neu = lies(a.alt, "cfd/auswertung.json"), lies(a.neu, "cfd/auswertung.json")
    w = lies(a.neu, "waerme.json")
    oben = Image.open(PROJEKT / "docs/bilder/gyroid_gefaess_1GW_gesamt.jpg")
    nah = Image.open(WURZEL / a.neu / "animation_gyroid/bilder/0359.png").convert("RGB")
    B, H = oben.size; h_unten = int(B * 0.36)

    fig = plt.figure(figsize=(B / 100, (H + h_unten) / 100), dpi=100, facecolor=HG)
    fig.figimage(np.asarray(oben), 0, h_unten)
    fu = h_unten / (H + h_unten)   # Hoehenanteil des unteren Bereichs
    fig.patches.append(matplotlib.patches.Rectangle((0, 0), 1, fu, transform=fig.transFigure, color=FELD, zorder=-1))
    fig.text(0.02, fu - 0.012, f"Kühlung des Plasmagefäßes: Segment 85–95° durchströmt (FluidX3D, Variante {a.neu})",
             color=TEXT, fontsize=26, weight="bold", va="top")

    # 1) Gyroid-Filamente
    ax = fig.add_axes([0.02, 0.025, 0.33, fu - 0.06]); ax.imshow(nah); ax.axis("off")
    ax.set_title("Gyroid-Filamente an der Plasmaseite (Innenhaut abgenommen)\nmit Wasserbahnen (Farbe = Geschwindigkeit)",
                 color=TEXT2, fontsize=15, loc="left")

    # 2) Durchfluss je Sektor
    ax = fig.add_axes([0.41, 0.06, 0.26, fu - 0.11], facecolor=FELD)
    qa, qn = (np.array(d["kern_umfang"]["Q_m3_s"]) * 1000 for d in (alt, neu))
    x = (np.arange(len(qa)) + 0.5) * 360 / len(qa) - 180
    bw = 360 / len(qa) / 2 - 1
    ax.bar(x - bw / 2 - 0.5, qa, bw, color=FARBE_ALT, label=f"{a.alt}: Streuung {alt['kern_umfang']['streuung_rel']*100:.0f} %")
    ax.bar(x + bw / 2 + 0.5, qn, bw, color=FARBE_NEU, label=f"{a.neu}: Streuung {neu['kern_umfang']['streuung_rel']*100:.0f} %")
    ax.axhline(qn.mean(), color=TEXT2, lw=1, ls="--")
    ax.set_xlim(-180, 180); ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_xticklabels(["innen", "unten", "außen", "oben", "innen"])
    ax.set_ylabel("Durchfluss je Sektor [l/s]", color=TEXT2, fontsize=15)
    ax.set_title("Durchfluss über den Umfang:\nFilament-Wanddicke nach Radius abgestimmt",
                 color=TEXT2, fontsize=15, loc="left")
    ax.tick_params(colors=TEXT2, labelsize=14)
    for s in ax.spines.values():
        s.set_color(LINIE)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=LINIE, lw=0.5, alpha=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, labelcolor=TEXT, fontsize=14, loc="upper center", ncol=2)
    ax.set_ylim(0, max(qa.max(), qn.max()) * 1.18)

    # 3) Erkenntnisse
    haut = w["dT_haut_K"]; ue = {z["fall"]: z for z in w["uebergang"]}
    zeilen = [("Erreicht", TEXT, True),
              (f"Streuung {alt['kern_umfang']['streuung_rel']*100:.0f} % → {neu['kern_umfang']['streuung_rel']*100:.0f} %, "
               f"Δp {neu['druckverlust_kPa']:.0f} kPa, {neu['kern_umfang']['summe_m3_s']*1000:.0f} l/s", TEXT2, False),
              ("Gitterfehler gefunden: Zellen jetzt direkt aus PicoGK", TEXT2, False),
              ("Reicht noch nicht (Wärme grob, 0,5 MW/m²)", TEXT, True),
              (f"Innenhaut 30 mm: {haut['30 mm']:.0f} K Temperaturabfall", TEXT2, False),
              (f"Wasser an der Plasmaseite {neu['plasmaseite']['v_mittel_m_s']:.2f} m/s: ".replace(".", ",") +
               f"h ≈ {ue['Plasmaseite Mittel']['h_W_m2K']:.0f} W/m²K", TEXT2, False),
              (f"10 % der Plasmaseite fast stehendes Wasser", TEXT2, False),
              ("Vorschläge", TEXT, True),
              (f"Innenhaut 3–5 mm ({haut['5 mm']:.0f} K bei 5 mm)", TEXT2, False),
              ("eigene feine Kanäle an der Plasmaseite, ~1 m/s", TEXT2, False),
              ("Wärme mitrechnen, Gitter verfeinern", TEXT2, False)]
    y = fu - 0.06
    for t, c, fett in zeilen:
        if fett and y < fu - 0.07:
            y -= 0.008
        fig.text(0.70, y, t, color=c, fontsize=19 if fett else 16, weight="bold" if fett else "normal", va="top")
        y -= 0.019
    fig.text(0.70, 0.012, "Hobbyprojekt · grobe Abschätzungen, keine Auslegung", color=TEXT2, fontsize=13, style="italic")
    fig.text(0.02, 0.022, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", color=TEXT, fontsize=19, weight="bold")
    fig.text(0.02, 0.009, "Strömung: FluidX3D (Dr. Moritz Lehmann, nicht-kommerzielle Lizenz) · github.com/ThomasSchmiegelt/stellarator-design", color=TEXT2, fontsize=15)
    ziel = PROJEKT / "docs/bilder/gyroid_gefaess_1GW_gesamt_kuehlung.jpg"
    fig.savefig(ziel, dpi=100, facecolor=HG, pil_kwargs={"quality": 90})
    print(ziel)


if __name__ == "__main__":
    main()
