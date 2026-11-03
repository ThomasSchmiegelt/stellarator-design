"""varianten_video_schnitt.py — Variantenfilm aus den Blender-Einzelbildern bauen (ffmpeg).

  .venv/bin/python -m stellarator.varianten_video_schnitt            # -> docs/filme/varianten.mp4 (alle Bilder noetig)
  .venv/bin/python -m stellarator.varianten_video_schnitt --vorschau # nur vorhandene Bilder, Luecken = letztes Bild
                                                                     #    -> sim/video_varianten/vorschau.mp4

Im Bild steht nur der Name unten rechts (Regel fuer Veroeffentlichungen); Erklaerungen, Zeitmarken und Farbcode
stehen im Begleittext docs/filme/varianten.md (DE/EN).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from .plasma_video_schnitt import nur_name

ROOT = Path(__file__).resolve().parents[1]
ORDNER = ROOT / "sim" / "video_varianten"
BILDER = ORDNER / "bilder"
FPS = 30
ENDE = 2520                                   # wie varianten_video_blender.ENDE


def main():
    vorschau = "--vorschau" in sys.argv
    fehlt = [f for f in range(ENDE) if not (BILDER / f"{f:05d}.png").exists()]
    if fehlt and not vorschau:
        sys.exit(f"{len(fehlt)} Bilder fehlen (erstes {fehlt[0]}); --vorschau baut mit Luecken")
    da = sorted(int(p.stem) for p in BILDER.glob("*.png"))
    ziel = ORDNER / "vorschau.mp4" if vorschau else ROOT / "docs" / "filme" / "varianten.mp4"
    W, H = Image.open(BILDER / f"{da[0]:05d}.png").size
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ziel)], stdin=subprocess.PIPE)
    letztes = None
    for f in range(ENDE if not vorschau else da[-1] + 1):
        pfad = BILDER / f"{f:05d}.png"
        if pfad.exists():
            letztes = np.asarray(nur_name(Image.open(pfad).convert("RGB"))).tobytes()
        if letztes is not None:
            p.stdin.write(letztes)
    p.stdin.close(); p.wait()
    print(ziel, ziel.stat().st_size // 1024, "kB", f"({len(fehlt)} Bilder fehlen)" if fehlt else "")


if __name__ == "__main__":
    main()
