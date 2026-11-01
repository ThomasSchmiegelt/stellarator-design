"""tauscher_cfd_bild.py — Bilder fuer den Bericht: Tauschermodule, Stroemungsbild, Validierung/Gitterstudie der FluidX3D-Rechnung.

  .venv/bin/python -m stellarator.tauscher_cfd_bild

Werte aus den Laeufen mit TRT-Temperaturstoss und Quelle ~ u_z (sim/tauscher/cfd/reihe_trt.log). Laminarer Plattenkanal:
exakt f Re = 24, Nu = 10 (gleichmaessige Quelle) bzw. 8,235 (Quelle ~ u, H1).
"""
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim" / "tauscher"
B1, B2 = ROOT / "docs" / "bilder", ROOT / "bericht" / "projektbericht" / "bilder"


def ablegen(name):
    shutil.copy(B1 / name, B2 / name)


def module():
    a = Image.open(SIM / "gyroid_gestuft" / "tauscher.png").convert("RGB")
    b = Image.open(SIM / "diamond_gestuft" / "tauscher.png").convert("RGB")
    h = min(a.height, b.height)
    a, b = (im.resize((im.width * h // im.height, h)) for im in (a, b))
    c = Image.new("RGB", (a.width + b.width, h), "white"); c.paste(a, (0, 0)); c.paste(b, (a.width, 0))
    c.thumbnail((2400, 2400)); c.save(B1 / "tauscher_module.jpg", quality=88); ablegen("tauscher_module.jpg")


def stroemung():
    """Standbilder aller drei Bauarten nebeneinander (Bild 120 der Videos)."""
    ims = [Image.open(SIM / "cfd" / f"{t}_re3000_n48" / "video" / "bilder" / "0120.png").convert("RGB")
           for t in ("gyroid", "diamond", "chevron")]
    ims[0].thumbnail((1800, 1800)); ims[0].save(B1 / "tauscher_stroemung.jpg", quality=88); ablegen("tauscher_stroemung.jpg")
    w = 900; ims = [im.resize((w, im.height * w // im.width)) for im in ims]
    c = Image.new("RGB", (3 * w, ims[0].height), "black")
    for k, im in enumerate(ims):
        c.paste(im, (k * w, 0))
    c.save(B1 / "tauscher_stroemung_drei.jpg", quality=88); ablegen("tauscher_stroemung_drei.jpg")


# Ergebnisse (sim/tauscher/cfd/reihe_trt.log, trt.log, Plattenlaeufe); Nu/Nu_Renon jeweils bei der erreichten Re
GYR_BGK = {48: 193.8 / 75.0}
GYR = {48: 139.8 / 75.0, 96: 102.0 / 68.4}
DIA = {48: 133.4 / 75.4, 96: 100.9 / 70.1}
P_ORD = 1.33                                                   # Konvergenzordnung aus dem Plattenkanal (8,9 -> 8,5, exakt 8,235)


def richardson(d):
    return d[96] - (d[48] - d[96]) / (2 ** P_ORD - 1)


def validierung(sprache):
    de = sprache == "de"
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), dpi=150)
    n = [12, 24, 48]
    ax1.plot(n, [100 * (v / 24 - 1) for v in (29.7, 25.7, 24.7)], "o-", color="#1f7fb8", label="f·Re (exakt 24)" if de else "f·Re (exact 24)")
    ax1.plot([12, 24], [100 * (v / 10 - 1) for v in (10.6, 10.3)], "s--", color="#9aa5a0",
             label="Nu, Quelle gleichmäßig, BGK (exakt 10)" if de else "Nu, uniform source, BGK (exact 10)")
    ax1.plot([24, 48], [100 * (v / 8.235 - 1) for v in (8.9, 8.5)], "s-", color="#d0612b",
             label="Nu, Quelle ∝ u, TRT (exakt 8,235)" if de else "Nu, source ∝ u, TRT (exact 8.235)")
    ax1.axhline(0, color="k", lw=0.8)
    ax1.set_xscale("log", base=2); ax1.set_xticks(n, [str(v) for v in n])
    ax1.set_xlabel("Zellen je Kanalhöhe" if de else "cells per channel height"); ax1.set_ylabel("Abweichung [%]" if de else "deviation [%]")
    ax1.set_title("Laminarer Plattenkanal (Prüffall)" if de else "Laminar plate channel (test case)", loc="left", fontsize=11)
    ax1.legend(fontsize=7.5, loc="upper right"); ax1.grid(alpha=0.3); ax1.set_ylim(-3, 27)
    ax2.plot([48], [GYR_BGK[48]], "x", color="#9aa5a0", ms=8, label="Gyroid, BGK, Quelle gleichmäßig" if de else "Gyroid, BGK, uniform source")
    for d, farbe, name in ((GYR, "#d0612b", "Gyroid"), (DIA, "#1f7fb8", "Diamond")):
        ax2.plot([48, 96], [d[48], d[96]], "o-", color=farbe, label=f"{name}, TRT, " + ("Quelle ∝ u" if de else "source ∝ u"))
        ax2.plot([96, 192], [d[96], richardson(d)], ":", color=farbe)
        ax2.plot([192], [richardson(d)], "o", mfc="none", color=farbe)
    ax2.text(192, richardson(GYR) + 0.12, "Richardson\n(p ≈ 1,3)" if de else "Richardson\n(p ≈ 1.3)", ha="center", fontsize=8)
    ax2.axhline(1, color="#7b4fb0", ls="--", lw=1, label="Renon 2024")
    ax2.axhline(79.2 / 75.0, color="#c99a2e", ls="--", lw=1, label="Li 2022 (Gyroid)")
    ax2.set_xscale("log", base=2); ax2.set_xticks([48, 96, 192], ["48", "96", "→ ∞"]); ax2.set_ylim(0, 2.9)
    ax2.set_xlabel("Zellen je hydraulischem Durchmesser" if de else "cells per hydraulic diameter")
    ax2.set_ylabel("Nu / Nu$_{Renon}$")
    ax2.set_title("Re ≈ 2600–3000, Pr 1,5: Nusselt-Zahl zur Korrelation" if de else "Re ≈ 2600–3000, Pr 1.5: Nusselt number over correlation",
                  loc="left", fontsize=11)
    ax2.legend(fontsize=7.5, loc="lower left"); ax2.grid(alpha=0.3)
    fig.tight_layout()
    name = "tauscher_cfd_pruefung.png" if de else "tauscher_cfd_pruefung_en.png"
    fig.savefig(B1 / name); plt.close(fig); ablegen(name)


if __name__ == "__main__":
    module(); stroemung(); validierung("de"); validierung("en"); print("BILDER_FERTIG")
