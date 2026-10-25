"""gyroid_gefaess.py — Plasmagefaess mit Gyroid-Kuehlkern (PicoGK) + Spulentorus der 1-GW-Anlage, Gesamtbild.

    .venv/bin/python -m stellarator.gyroid_gefaess [--sektoren 0:360] [--zelle 0.35 --voxel 0.03] [--name gesamt]

Plasmarand: VMEC-Randflaeche (sim/invers/qa_nfp2_A45/wout_*.nc), skaliert auf R0 der 1-GW-Anlage.
PicoGK (picogk/GyroidGefaess) je Sektor: Offset(Plasma, spalt) .. Offset(Plasma, spalt+wand) = Wand,
Innen-/Aussenhaut voll, dazwischen Gyroid-Schale. Sektoren einzeln (Speicher), danach zusammen gezeigt.
Spulen: Hex-Modell der Surrogat-Probe 0 (Stahl, von Mises), optional.
Ausgabe sim/gyroid_gefaess/<name>/: sektor_*/gefaess.stl, plasma.vtp, gesamt.png, ergebnis.json.
Massstab: Gesamtansicht mit groben Zellen (0,3-0,4 m); feiner Ausschnitt ueber --sektoren 0:10 --zelle 0.12.
"""
from __future__ import annotations
import argparse, json, os, subprocess, time
from pathlib import Path
import numpy as np

from .lauf import PROJEKT
from .spulen import schreibe_stl

APP = PROJEKT / "picogk" / "GyroidGefaess"
BIN = APP / "bin" / "Release" / "net9.0" / "GyroidGefaess"
WURZEL = PROJEKT / "sim" / "gyroid_gefaess"
ENV = os.environ | {"DOTNET_ROOT": str(Path.home() / ".dotnet")}


def randflaeche(R0: float = 10.4, n_th: int = 96, n_ph: int = 720) -> np.ndarray:
    """VMEC-Rand X (n_th, n_ph, 3) [m], phi 0..2pi, skaliert auf R0."""
    from netCDF4 import Dataset
    ordner = PROJEKT / "sim" / "invers" / "qa_nfp2_A45"
    R0_s = json.loads((ordner / "stufe1.json").read_text())["kennzahlen"]["R0_m"]
    with Dataset(str(next(ordner.glob("wout_*.nc")))) as w:
        rmnc, zmns, xm, xn = w["rmnc"][-1, :], w["zmns"][-1, :], w["xm"][:], w["xn"][:]
    th, ph = np.meshgrid(np.linspace(0, 2 * np.pi, n_th, endpoint=False), np.linspace(0, 2 * np.pi, n_ph, endpoint=False), indexing="ij")
    arg = xm[:, None, None] * th - xn[:, None, None] * ph
    R = np.einsum("m,mij->ij", rmnc, np.cos(arg)); Z = np.einsum("m,mij->ij", zmns, np.sin(arg))
    return np.stack([R * np.cos(ph), R * np.sin(ph), Z], -1) * (R0 / R0_s)


def sektor_stl(X: np.ndarray, ph0: float, ph1: float, pfad: Path) -> None:
    """Geschlossener Plasma-Sektor phi in [ph0, ph1] (Grad) mit Faecher-Deckeln, in mm."""
    n_ph = X.shape[1]
    idx = np.arange(int(np.floor(ph0 / 360 * n_ph)), int(np.ceil(ph1 / 360 * n_ph)) + 1) % n_ph
    S = X[:, idx]                                               # (n_th, k, 3)
    n_th, k = S.shape[:2]
    tri = []
    for j in range(k - 1):
        for i in range(n_th):
            a, b = S[i, j], S[(i + 1) % n_th, j]
            c, d = S[(i + 1) % n_th, j + 1], S[i, j + 1]
            tri += [(a, b, c), (a, c, d)]
    for j, umk in ((0, False), (k - 1, True)):
        m = S[:, j].mean(0)
        for i in range(n_th):
            t = (m, S[(i + 1) % n_th, j], S[i, j])
            tri.append(t[::-1] if umk else t)
    T = np.array(tri)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    schreibe_stl(pfad, T if vol > 0 else T[:, ::-1])


def keil_stl(ph0: float, ph1: float, R_max: float, Z_max: float, pfad: Path, n: int = 24) -> None:
    """Keil phi in [ph0, ph1], 0 <= R <= R_max, |Z| <= Z_max (Prisma ueber einem Kreissektor), in mm."""
    p = np.radians(np.linspace(ph0, ph1, n))
    ring = np.c_[R_max * np.cos(p), R_max * np.sin(p)]
    poly = np.vstack([[0, 0], ring])                           # Kreissektor
    unten = np.c_[poly, np.full(len(poly), -Z_max)]; oben = np.c_[poly, np.full(len(poly), Z_max)]
    tri = []
    for i in range(1, len(poly) - 1):
        tri += [(unten[0], unten[i + 1], unten[i]), (oben[0], oben[i], oben[i + 1])]
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        tri += [(unten[i], unten[j], oben[j]), (unten[i], oben[j], oben[i])]
    T = np.array(tri)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    schreibe_stl(pfad, T if vol > 0 else T[:, ::-1])


def baue_sektor(X, ph0, ph1, o: Path, a) -> dict:
    o.mkdir(parents=True, exist_ok=True)
    rand = 2.0                                                  # Grad Ueberstand, Keil schneidet sauber
    sektor_stl(X * 1000, ph0 - rand, ph1 + rand, o / "plasma.stl")
    R_max = (np.hypot(X[..., 0], X[..., 1]).max() + a.spalt + a.wand + 0.5) * 1000
    Z_max = (np.abs(X[..., 2]).max() + a.spalt + a.wand + 0.5) * 1000
    keil_stl(ph0, ph1, R_max, Z_max, o / "keil.stl")
    auftrag = {"plasma_stl": str(o / "plasma.stl"), "keil_stl": str(o / "keil.stl"), "spalt_mm": a.spalt * 1000,
               "wand_mm": a.wand * 1000, "haut_innen_mm": a.haut_innen * 1000, "haut_aussen_mm": a.haut_aussen * 1000,
               "zelle_mm": a.zelle * 1000, "halbdicke_mm": a.halbdicke * 1000, "voxel_mm": a.voxel * 1000, "ausgabe": str(o)}
    (o / "auftrag.json").write_text(json.dumps(auftrag, indent=1))
    t0 = time.time()
    r = subprocess.run([str(BIN), str(o / "auftrag.json")], env=ENV, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"PicoGK fehlgeschlagen:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    e = json.loads((o / "ergebnis.json").read_text()) | {"zeit_s": time.time() - t0}
    print(f"Sektor {ph0:.0f}-{ph1:.0f} Grad: Wand {e['volumen_wand_m3']:.1f} m3, Stahlanteil {e['stahlanteil_wand']:.0%}, "
          f"{e['dreiecke']} Dreiecke, {e['zeit_s']:.0f} s", flush=True)
    return e


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sektoren", default="0:360", help="von:bis Grad")
    ap.add_argument("--teil", type=float, default=30.0, help="Grad je PicoGK-Lauf (Speicher)")
    ap.add_argument("--spalt", type=float, default=0.15)
    ap.add_argument("--wand", type=float, default=0.45)
    ap.add_argument("--haut_innen", type=float, default=0.02)
    ap.add_argument("--haut_aussen", type=float, default=0.03)
    ap.add_argument("--zelle", type=float, default=0.35)
    ap.add_argument("--halbdicke", type=float, default=0.02)
    ap.add_argument("--voxel", type=float, default=0.03)
    ap.add_argument("--name", default="gesamt")
    ap.add_argument("--ram_min", type=float, default=8.0)
    a = ap.parse_args(argv)
    o = WURZEL / a.name
    X = randflaeche()
    lo, hi = map(float, a.sektoren.split(":"))
    grenzen = np.arange(lo, hi + 1e-9, a.teil)
    erg = {"parameter": vars(a), "sektoren": []}
    for ph0, ph1 in zip(grenzen[:-1], grenzen[1:]):
        so = o / f"sektor_{ph0:03.0f}"
        if (so / "gefaess.stl").exists():
            continue
        mi = {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}
        if mi["MemAvailable"] < a.ram_min:
            raise SystemExit(f"nur {mi['MemAvailable']:.1f} GB RAM frei -> abgebrochen (spaeter fortsetzen)")
        erg["sektoren"].append({"von": ph0, "bis": ph1} | baue_sektor(X, ph0, ph1, so, a))
    (o / "ergebnis.json").write_text(json.dumps(erg, indent=1, default=str))


if __name__ == "__main__":
    main()
