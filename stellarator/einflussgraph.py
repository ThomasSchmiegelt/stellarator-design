"""einflussgraph.py — Leistungsfluss vom Plasma ins Netz (Sankey-Bild) mit Stellgrößen, für Bericht und README.

  .venv/bin/python -m stellarator.einflussgraph

Zahlen aus der Wärmebilanz (Bericht, Abschnitt Herleitung der Wärmebilanz und Divertor-Vorwärmer). Bandbreite
proportional zur Leistung in MW. Ausgabe docs/bilder/einflussgraph.png (DE) und einflussgraph_en.png (EN),
Kopien nach bericht/projektbericht/bilder/.
"""
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MPath

ROOT = Path(__file__).resolve().parents[1]
FARBE = dict(nuk="#7b4fb0", heiss="#d0612b", lau="#c99a2e", strom="#1f7fb8", verlust="#9aa5a0")

# id, Spalte, Leistung MW, Typ, Name DE, Name EN, Stellgrößen DE, EN
KNOTEN = [
    ("plasma", 0, 3053, "nuk", "Fusionsplasma D-T", "Fusion plasma D-T", "f_α = 0,20", "f_α = 0.20"),
    ("gain", 1, 365, "nuk", "Kernreaktionen\nim Blanket", "Nuclear reactions\nin the blanket", "M = 1,15", "M = 1.15"),
    ("neutron", 1, 2443, "nuk", "Neutronen 14,1 MeV", "Neutrons 14.1 MeV", "", ""),
    ("alpha", 1, 610, "nuk", "Alphas 3,5 MeV", "Alphas 3.5 MeV", "", ""),
    ("blanket", 2, 2808, "heiss", "Blanket", "Blanket", "", ""),
    ("wand", 2, 305, "heiss", "Erste Wand", "First wall", "0,25 MW/m², 1230 m²", "0.25 MW/m², 1230 m²"),
    ("div", 2, 305, "lau", "Divertor", "Divertor", "≤ 10 MW/m², ≥ 31 m²", "≤ 10 MW/m², ≥ 31 m²"),
    ("kb", 3, 2808, "heiss", "Primärkreis Blanket", "Primary loop blanket", "≈ 300 °C, 17 400 kg/s", "≈ 300 °C, 17,400 kg/s"),
    ("kw", 3, 305, "heiss", "Primärkreis Wand", "Primary loop wall", "1890 kg/s", "1890 kg/s"),
    ("kd", 3, 305, "lau", "Divertorkreis", "Divertor loop", "130 → 136 °C, 5 MPa", "130 → 136 °C, 5 MPa"),
    ("dez", 4, 3113, "heiss", "Dampferzeuger", "Steam generators", "78 bar Sattdampf", "78 bar saturated steam"),
    ("vw", 4, 305, "lau", "Vorwärmer (Gyroid)", "Preheater (gyroid)", "≤ 73 MW Strom statt 107", "≤ 73 MW power, not 107"),
    ("turb", 5, 3418, "heiss", "Dampfturbine", "Steam turbine", "η = 0,35", "η = 0.35"),
    ("gen", 6, 1197, "strom", "Generator (brutto)", "Generator (gross)", "", ""),
    ("kond", 6, 2221, "verlust", "Kondensator", "Condenser", "24,7 mbar", "24.7 mbar"),
    ("netz", 7, 1000, "strom", "Netzanschluss", "Grid connection", "netto", "net"),
    ("pumpe", 7, 137, "strom", "Kühlmittelpumpen", "Coolant pumps", "0,04 · P_th", "0.04 · P_th"),
    ("eigen", 7, 60, "strom", "Übriger Eigenbedarf", "Other house load", "", ""),
]
FLUSS = [("plasma", "neutron", 2443, "nuk"), ("plasma", "alpha", 610, "nuk"), ("neutron", "blanket", 2443, "nuk"),
         ("gain", "blanket", 365, "nuk"), ("alpha", "wand", 305, "nuk"), ("alpha", "div", 305, "nuk"),
         ("blanket", "kb", 2808, "heiss"), ("wand", "kw", 305, "heiss"), ("div", "kd", 305, "lau"),
         ("kb", "dez", 2808, "heiss"), ("kw", "dez", 305, "heiss"), ("kd", "vw", 305, "lau"),
         ("dez", "turb", 3113, "heiss"), ("vw", "turb", 305, "lau"), ("turb", "gen", 1197, "strom"),
         ("turb", "kond", 2221, "verlust"), ("gen", "netz", 1000, "strom"), ("gen", "pumpe", 137, "strom"),
         ("gen", "eigen", 60, "strom")]
TEXT = dict(
    de=dict(spalten=["Quelle", "Teilchen", "Bauteil", "Kühlkreis", "Wärmeübertragung", "Turbine", "Wandlung", "Ausgang"],
            titel="Vom Plasma ins Netz: Leistungsfluss des 1-GW-Stellarators (MW, Bandbreite ∝ Leistung)",
            fuss="Grundfall der Wärmebilanz: P_th = (1000 + 60)/(0,35 − 0,04) = 3419 MW. Divertorwärme bringt als Vorwärmung "
                 "höchstens 73 MW statt 107 MW → P_fus ≈ 3140 statt 3053 MW.",
            legende=["Kernenergie", "Wärme ≈ 300 °C", "Wärme 130–136 °C", "Strom", "Abwärme"], tz=lambda v: f"{v:,}".replace(",", " ")),
    en=dict(spalten=["Source", "Particles", "Component", "Coolant loop", "Heat transfer", "Turbine", "Conversion", "Output"],
            titel="From plasma to grid: power flow of the 1 GW stellarator (MW, band width ∝ power)",
            fuss="Base case of the heat balance: P_th = (1000 + 60)/(0.35 − 0.04) = 3419 MW. As preheating, divertor heat "
                 "yields at most 73 MW instead of 107 MW → P_fus ≈ 3140 instead of 3053 MW.",
            legende=["Nuclear energy", "Heat ≈ 300 °C", "Heat 130–136 °C", "Electricity", "Waste heat"], tz=lambda v: f"{v:,}"),
)


def zeichne(sprache):
    T = TEXT[sprache]
    W, H, k, gap, top, NW = 1500.0, 640.0, 0.095, 62.0, 70.0, 14.0
    colx = lambda c: 30 + c * (W - 260) / 7
    K = {n[0]: dict(id=n[0], c=n[1], mw=n[2], typ=n[3], name=n[4] if sprache == "de" else n[5],
                    stell=n[6] if sprache == "de" else n[7], inn=[], out=[]) for n in KNOTEN}
    LL = []
    for a, b, v, typ in FLUSS:
        l = dict(a=K[a], b=K[b], v=v, typ=typ); K[a]["out"].append(l); K[b]["inn"].append(l); LL.append(l)
    for c in range(8):
        col = [n for n in K.values() if n["c"] == c]
        for n in col:
            n["h"] = max(6, k * max(n["mw"], sum(l["v"] for l in n["inn"]), sum(l["v"] for l in n["out"])))
        tot = sum(n["h"] for n in col) + gap * (len(col) - 1)
        y = top + (H - top - 40 - tot) / 2
        for n in col:
            n["x"], n["y"] = colx(c), y; y += n["h"] + gap
    for n in K.values():
        y = n["y"]
        for l in sorted(n["out"], key=lambda l: l["b"]["y"]):
            l["y0"] = y; y += l["v"] * k
        y = n["y"]
        for l in sorted(n["inn"], key=lambda l: l["a"]["y"]):
            l["y1"] = y; y += l["v"] * k
    fig, ax = plt.subplots(figsize=(15, 7.4), dpi=150)
    ax.set_xlim(0, W); ax.set_ylim(H + 20, -10); ax.axis("off")
    for l in LL:
        x0, x1, w = l["a"]["x"] + NW, l["b"]["x"], l["v"] * k
        m = (x0 + x1) / 2
        v = [(x0, l["y0"]), (m, l["y0"]), (m, l["y1"]), (x1, l["y1"]), (x1, l["y1"] + w), (m, l["y1"] + w),
             (m, l["y0"] + w), (x0, l["y0"] + w), (x0, l["y0"])]
        codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO, MPath.CURVE4, MPath.CURVE4,
                 MPath.CURVE4, MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(v, codes), fc=FARBE[l["typ"]], ec="none", alpha=0.38))
    halo = dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.85)
    for n in K.values():
        ax.add_patch(Rectangle((n["x"], n["y"]), NW, n["h"], fc=FARBE[n["typ"]], ec="none"))
        wert = ("+ " if n["id"] == "gain" else "") + T["tz"](n["mw"]) + " MW"
        zeilen = n["name"].count("\n")
        ax.text(n["x"], n["y"] - 6, f"{n['name']}\n{wert}", fontsize=9.5, va="bottom", ha="left", bbox=halo,
                linespacing=1.15)
        if n["stell"]:
            ax.text(n["x"], n["y"] + n["h"] + 5, n["stell"], fontsize=8.3, va="top", ha="left", color="#4a5651",
                    style="italic", bbox=halo)
    for c, s in enumerate(T["spalten"]):
        ax.text(colx(c), 22, s.upper(), fontsize=8.5, color="#5b6762", family="monospace")
    ax.set_title(T["titel"], fontsize=13, loc="left", pad=6)
    for i, (lab, f) in enumerate(zip(T["legende"], ["nuk", "heiss", "lau", "strom", "verlust"])):
        ax.add_patch(Rectangle((30 + i * 190, H + 2), 22, 9, fc=FARBE[f], ec="none", alpha=0.8))
        ax.text(58 + i * 190, H + 7, lab, fontsize=9, va="center")
    fig.text(0.013, 0.012, T["fuss"], fontsize=8.5, color="#4a5651")
    fig.text(0.987, 0.012, "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell", fontsize=7.5, color="#7a8681", ha="right")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.94, bottom=0.05)
    name = "einflussgraph.png" if sprache == "de" else "einflussgraph_en.png"
    out = ROOT / "docs" / "bilder" / name
    fig.savefig(out); plt.close(fig)
    shutil.copy(out, ROOT / "bericht" / "projektbericht" / "bilder" / name)
    return out


if __name__ == "__main__":
    for s in ("de", "en"):
        print(zeichne(s))
