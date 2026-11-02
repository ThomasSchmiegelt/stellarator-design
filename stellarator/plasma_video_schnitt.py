"""plasma_video_schnitt.py — Bildtexte in die gerenderten Bilder setzen und Film DE/EN bauen (ffmpeg).

  .venv/bin/python -m stellarator.plasma_video_schnitt            # -> docs/filme/plasma_flug.mp4 (nur Name, zum Veroeffentlichen)
  .venv/bin/python -m stellarator.plasma_video_schnitt --erklaert # Fassungen mit Bildtexten DE/EN
  .venv/bin/python -m stellarator.plasma_video_schnitt --standbild # Standbilder fuer Bericht/README

Texte wechseln mit der Kamerafahrt: im Plasma (0-6 s), hinaus (6-10 s), Gesamtansicht (10-20 s).
"""
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BILDER = ROOT / "sim" / "video_plasma" / "bilder"
FPS = 30
SCHRIFT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
NAME = "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell"

T = {
    "de": dict(
        titel="Plasma im eigenen Stellarator-Entwurf (1 GW, R₀ = 10,4 m) – berechnete Geometrie, Blender",
        teile=[(0, 6, "Im Plasma: Der heiße Kern (150 Mio. °C) ist fast unsichtbar. Es leuchtet der kühlere Rand –",
                "Wasserstofflicht, deshalb rosa. Ringsum die Erstwand aus Wolframkacheln."),
               (6, 10, "Hinaus durch den aufgeschnittenen Teil des Gefäßes, zwischen den Spulen hindurch.", ""),
               (10, 20.1, "Der ganze Stellarator: 16 Spulen (Stahlgehäuse, 1 m), das Plasma (rosa),",
                "die Erstwand vorne aufgeschnitten. Das Plasma ist zweimal verdreht (zwei Feldperioden).")],
        teilchen="Weiße Striche: geladene Teilchen auf den berechneten Feldlinien – stark vergrößert und rund "
                 "50 000-fach verlangsamt (in Wirklichkeit einmal um den Ring in 60 Mikrosekunden)."),
    "en": dict(
        titel="Plasma in the project's own stellarator design (1 GW, R₀ = 10.4 m) – computed geometry, Blender",
        teile=[(0, 6, "Inside the plasma: the hot core (150 million °C) is almost invisible. The cooler edge glows –",
                "hydrogen light, hence pink. All around, the first wall made of tungsten tiles."),
               (6, 10, "Out through the cut-open part of the vessel, between the coils.", ""),
               (10, 20.1, "The whole stellarator: 16 coils (steel casing, 1 m), the plasma (pink),",
                "the first wall cut open at the front. The plasma is twisted twice (two field periods).")],
        teilchen="White streaks: charged particles on the computed field lines – greatly enlarged and slowed down about "
                 "50,000 times (in reality once around the ring in 60 microseconds)."),
}


def beschriften(im, f, sp):
    s = T[sp]; W, H = im.size; k = W / 1920
    d = ImageDraw.Draw(im, "RGBA")
    ft = ImageFont.truetype(SCHRIFT.format("SemiBold"), int(26 * k))
    fm = ImageFont.truetype(SCHRIFT.format("Regular"), int(24 * k))
    fk = ImageFont.truetype(SCHRIFT.format("Regular"), int(19 * k))
    t = f / FPS
    # Titelzeile oben
    d.rectangle([0, 0, W, int(52 * k)], fill=(0, 0, 0, 120))
    d.text((int(24 * k), int(12 * k)), s["titel"], font=ft, fill=(240, 240, 245, 255))
    # Untertitel je Abschnitt, weich ein- und ausgeblendet
    for a, b, z1, z2 in s["teile"]:
        if a <= t < b:
            alpha = int(255 * min(1, (t - a) / 0.6, (b - t) / 0.6 if b < 20 else 1))
            y = H - int(160 * k)
            d.rectangle([0, y - int(14 * k), W, H], fill=(0, 0, 0, int(alpha * 0.55)))
            d.text((int(24 * k), y), z1, font=fm, fill=(255, 255, 255, alpha))
            if z2:
                d.text((int(24 * k), y + int(34 * k)), z2, font=fm, fill=(255, 255, 255, alpha))
    d.text((int(24 * k), H - int(62 * k)), s["teilchen"], font=fk, fill=(200, 215, 230, 230))
    w = d.textlength(NAME, font=fk)
    d.text((W - w - int(20 * k), H - int(22 * k) - int(4 * k)), NAME, font=fk, fill=(170, 170, 175, 230))
    return im


def nur_name(im):
    """Veroeffentlichungsfassung: nur der Name unten rechts, alle Erklaerungen stehen im Begleittext."""
    W, H = im.size; k = W / 1920; d = ImageDraw.Draw(im, "RGBA")
    f = ImageFont.truetype(SCHRIFT.format("Medium"), int(28 * k)); n = "Thomas Schmiegelt"
    w = d.textlength(n, font=f)
    d.text((W - w - int(32 * k), H - int(56 * k)), n, font=f, fill=(235, 235, 240, 215))
    return im


def film(sp):
    n = len(list(BILDER.glob("f*.png")))
    ziel = ROOT / "docs" / "filme" / {"de": "plasma_flug_erklaert.mp4", "en": "plasma_flug_erklaert_en.mp4",
                                      "name": "plasma_flug.mp4"}[sp]
    W, H = Image.open(BILDER / "f0000.png").size
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ziel)], stdin=subprocess.PIPE)
    for f in range(n):
        im = Image.open(BILDER / f"f{f:04d}.png").convert("RGB")
        im = nur_name(im) if sp == "name" else beschriften(im, f, sp)
        p.stdin.write(np.asarray(im).tobytes())
    p.stdin.close(); p.wait()
    print(ziel, ziel.stat().st_size // 1024, "kB")


def standbilder():
    """Je ein Standbild innen und aussen, DE/EN, fuer Bericht und README."""
    for sp in ("de", "en"):
        for f, name in ((60, "innen"), (590, "aussen")):
            im = beschriften(Image.open(BILDER / f"f{f:04d}.png").convert("RGB"), f, sp)
            n = f"plasma_flug_{name}" + ("_en" if sp == "en" else "") + ".png"
            im.resize((1280, 720), Image.LANCZOS).save(ROOT / "docs" / "bilder" / n)
            shutil.copy(ROOT / "docs" / "bilder" / n, ROOT / "bericht" / "projektbericht" / "bilder" / n)
            print(n)


if __name__ == "__main__":
    if "--standbild" in sys.argv:
        standbilder()
    elif "--erklaert" in sys.argv:
        for sp in ("de", "en"):
            film(sp)
    else:
        film("name")                                     # Veroeffentlichungsfassung
