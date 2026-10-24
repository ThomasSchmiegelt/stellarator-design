"""aufbau.py — Spulengehaeuse schrittweise aufbauen, je neue Spule auf Kollision pruefen, Bildfolge + Video.

  .venv/bin/python -m stellarator.aufbau stellarator/faelle/w7x_standard.json [--start 12] [--fps 4]

Voraussetzung: stellarator.gehaeuse auf denselben Fall (gehaeuse.FCStd, STL, vss_eingabe.json).
Reihenfolge (Idee User): zuerst --start Spulen mit gleichem Winkelabstand (12 -> ~30 Grad), dann
die Luecken halbieren (immer die groesste Luecke, mittlere Spule), bis alle stehen.
Kollisionspruefung in FreeCAD (stellarator/freecad_aufbau.py), Bilder mit pyvista aus den STL:
grau = gesetzt, orange = neue Spule, rot = neue Spule mit Kollision, blau = Verbinder.
Ausgabe sim/stellarator/gehaeuse/<fall>/aufbau/: aufbau.json, bild_XXX.png, aufbau.mp4.
"""
from __future__ import annotations
import argparse, json, os, subprocess
from pathlib import Path
import numpy as np

from .gehaeuse import FREECAD
from .lauf import PROJEKT

SKRIPT = Path(__file__).with_name("freecad_aufbau.py")
REPARATUR = Path(__file__).with_name("freecad_reparatur.py")


def reihenfolge(phi: np.ndarray, start: int) -> list[int]:
    """Indizes: start Spulen gleichmaessig ueber den Umfang, dann Luecken halbieren (groesste zuerst)."""
    ordn = list(np.argsort(phi)); N = len(ordn)
    pos = sorted({int(round(x)) % N for x in np.linspace(0, N, start, endpoint=False)})
    folge = list(pos)
    while len(pos) < N:
        luecken = [((pos[(i + 1) % len(pos)] - pos[i]) % N or N, i) for i in range(len(pos))]
        g, i = max(luecken)
        neu = (pos[i] + g // 2) % N
        pos = sorted(pos + [neu]); folge.append(neu)
    return [int(ordn[p]) for p in folge]


def bilder(ordner: Path, namen: list[str], verb_namen: list[str], erg: dict, titel: str, fps: int) -> Path:
    import pyvista as pv
    quelle = ordner.parent
    geh = {n: pv.read(quelle / f"gehaeuse_{i:02d}.stl") for i, n in enumerate(namen)}
    verb = {n: pv.read(quelle / f"verbinder_{i:02d}.stl") for i, n in enumerate(verb_namen)
            if (quelle / f"verbinder_{i:02d}.stl").exists()}
    alle = pv.MultiBlock(list(geh.values())); b = alle.bounds; r = max(abs(x) for x in b)
    gesetzt, vgesetzt = [], []
    for s in erg["schritte"]:
        pl = pv.Plotter(off_screen=True, window_size=(1280, 720)); pl.set_background("white")
        for n in gesetzt:
            pl.add_mesh(geh[n], color="#8a9bb0", smooth_shading=True)
        for v in vgesetzt:
            pl.add_mesh(verb[v], color="#3a73a6")
        farbe = "#d62728" if s["kollisionen"] else "#ff8c1a"
        pl.add_mesh(geh[s["spule"]], color=farbe, smooth_shading=True)
        for v in s["neue_verbinder"]:
            if v in verb:
                pl.add_mesh(verb[v], color="#ff8c1a")
        gesetzt.append(s["spule"]); vgesetzt += [v for v in s["neue_verbinder"] if v in verb]
        n_k = sum(len(x["kollisionen"]) for x in erg["schritte"][:s["schritt"]])
        pl.add_text(f"{titel}   Schritt {s['schritt']}/{len(erg['schritte'])}: Spule {s['spule']}, "
                    f"+{len(s['neue_verbinder'])} Verbinder   |   Kollisionen bisher: {n_k}",
                    font_size=11, color="black")
        pl.camera_position = [(1.9 * r, -1.9 * r, 1.5 * r), (0, 0, 0), (0, 0, 1)]
        pl.reset_camera_clipping_range()
        pl.screenshot(ordner / f"bild_{s['schritt']:03d}.png"); pl.close()
    video = ordner / "aufbau.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(ordner / "bild_%03d.png"),
                    "-vf", "tpad=stop_mode=clone:stop_duration=3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(video)], check=True)
    return video


def main(argv=None):
    ap = argparse.ArgumentParser(description="Schrittweiser Aufbau mit Kollisionspruefung + Video")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--start", type=int, default=12, help="Spulen im ersten Schritt (gleicher Winkelabstand)")
    ap.add_argument("--fps", type=int, default=4)
    ap.add_argument("--nur_bilder", action="store_true")
    ap.add_argument("--reparieren", action="store_true", help="Kollisionen ueber die Parametertabelle beheben -> korrektur.json")
    ap.add_argument("--wand_min", type=float, default=0.005)
    ap.add_argument("--max_iter", type=int, default=6)
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text())
    quelle = PROJEKT / "sim" / "stellarator" / "gehaeuse" / fall["name"]
    E = json.loads((quelle / "vss_eingabe.json").read_text())
    namen = E["spulen_namen"]
    from . import spulen as sp
    spulen, _ = sp.lade_spulensatz(fall["spulen"])
    phi = np.array([np.arctan2(s.punkte[:, 1].mean(), s.punkte[:, 0].mean()) for s in spulen]) % (2 * np.pi)
    folge = [namen[i] for i in reihenfolge(phi, a.start)]
    verb = [{"name": v["name"], "a": namen[v["a"]], "b": namen[v["b"]]} for v in E.get("verbinder", [])]
    verb += [{"name": v["name"], "a": v["a"], "b": v["b"]} for v in E.get("verbinder_klone", [])]
    ordner = quelle / "aufbau"; ordner.mkdir(exist_ok=True)
    if not a.nur_bilder and not a.reparieren:
        p = ordner / "aufbau_eingabe.json"
        p.write_text(json.dumps({"fcstd": str(quelle / "gehaeuse.FCStd"), "reihenfolge": folge,
                                 "verbinder": verb, "ausgabe": str(ordner)}))
        r = subprocess.run([str(FREECAD), "freecadcmd", str(SKRIPT)], env={**os.environ, "VSS_AUFBAU": str(p)},
                           capture_output=True, text=True)
        if "AUFBAU_FERTIG" not in r.stdout:
            print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit("FreeCAD-Aufbau fehlgeschlagen")
    if a.reparieren:
        p = ordner / "reparatur_eingabe.json"
        p.write_text(json.dumps({"fcstd": str(quelle / "gehaeuse.FCStd"), "vss_eingabe": str(quelle / "vss_eingabe.json"),
                                 "reihenfolge": folge, "ausgabe": str(ordner), "wand_min_mm": a.wand_min * 1e3,
                                 "faktor": 0.6, "max_iter": a.max_iter}))
        r = subprocess.run([str(FREECAD), "freecadcmd", str(REPARATUR)], env={**os.environ, "VSS_REPARATUR": str(p)},
                           capture_output=True, text=True)
        print("\n".join(z for z in r.stdout.splitlines() if z.startswith("REPARATUR")))
        if "REPARATUR_FERTIG" not in r.stdout:
            print(r.stdout[-2000:], r.stderr[-2000:]); raise SystemExit("FreeCAD-Reparatur fehlgeschlagen")
        print(f"NEU BAUEN: stellarator.gehaeuse <fall> <gleiche Optionen> --korrektur {ordner / 'korrektur.json'}, "
              "danach aufbau erneut (Pruefung + Video)")
        return
    erg = json.loads((ordner / "aufbau.json").read_text())
    for s in erg["schritte"]:
        if s["kollisionen"]:
            print(f"KOLLISION Schritt {s['schritt']} {s['spule']}: {s['kollisionen'][:3]}")
    video = bilder(ordner, namen, [v["name"] for v in verb], erg, fall["name"], a.fps)
    print("FERTIG", erg["n_kollisionen"], "Kollisionen", video)


if __name__ == "__main__":
    main()
