"""Videos aus den fertigen QI-Karten (nur Darstellung, keine neue Physik). Nutzt die Daten aus stellarator/qi_karte.py.

Aufruf (hoechstens 1 Prozess, im Scope):
  systemd-run --user --scope -q -p MemoryMax=4G -p MemorySwapMax=0 --description="hermes python qi_video" \
     .venv-constellaration/bin/python -m stellarator.qi_video [alle|do3|k3|d8z|dje|vergleich]
Je Video: frames/<name>/ (PNG) -> <name>.mp4 (h264, 1280x720, 24 fps). Zwischen den gerechneten Flaechen wird linear
in s interpoliert (die Residuen R, vorzeichenbehaftet). Skala = die von uebersicht_s_winkel.png (LogNorm, magma).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

from stellarator.qi_karte import AUS, FORMEN

OUT = AUS / "video"
KURZ = {"do3": "Do3Qy", "k3": "K3 halb", "d8z": "D8ZNt2", "dje": "DjLe3eL6"}
FARBE = {"do3": "#1b6ca8", "k3": "#2a9d8f", "d8z": "#c0392b", "dje": "#8e6c8a"}
FPS, SEK, NF = 24, 15, 24 * 15
import os
if os.environ.get('QIV_TEST'): NF = 6
NSI = 200  # feine s-Stuetzstellen fuer die interpolierte Kurve
D = {f: (json.loads((AUS / f"{f}.json").read_text()), np.load(AUS / f"{f}.npz")) for f in FORMEN}
_alle = np.concatenate([z["je_winkel"].ravel() for _, z in D.values()])
NORM = LogNorm(max(_alle.max() * 1e-5, _alle[_alle > 0].min()), _alle.max())  # wie uebersicht_s_winkel.png
NL = D["do3"][1]["residuen"].shape[1]  # 75 Feldlinien
S_FEIN = np.linspace(0.015306122448979591, 0.9948979591836734, NSI)


def dichte(f):
    """R auf feinem s-Gitter (linear interpoliert), Beitrag R^2*NL (gleiche Einheit wie je_winkel = Summe ueber Feldlinien)."""
    z = D[f][1]; s = z["s"]; R = z["residuen"].astype(float)
    i = np.clip(np.searchsorted(s, S_FEIN) - 1, 0, len(s) - 2); w = (S_FEIN - s[i]) / (s[i + 1] - s[i])
    Rf = R[i] * (1 - w)[:, None, None] + R[i + 1] * w[:, None, None]
    return Rf ** 2 * NL


def wasserzeichen(fig):
    fig.text(0.5, 0.008, "Thomas Schmiegelt", ha="center", va="bottom", fontsize=8, color="0.45")


def fig_neu():
    return plt.figure(figsize=(12.8, 7.2), dpi=100)


def speichern(fig, ordner, k):
    fig.savefig(ordner / f"{k:04d}.png", dpi=100)


def grenzen(ax):
    ax.axhline(3.2e-4, color="gray", ls="--", lw=1); ax.axhline(1e-4, color="gray", ls=":", lw=1)
    ax.text(0.02, 3.2e-4 * 1.12, "Aufgabe 3: 0,00032", fontsize=8, color="gray"); ax.text(0.02, 1e-4 * 1.12, "Aufgabe 2: 0,0001", fontsize=8, color="gray")


def qi_kurve(f, Q):
    z = D[f][1]
    return z["s"], z["qi_flaeche"]


def video(name, formen, modus):
    """modus 's' (Durchfahrt in s) oder 'phi' (entlang einer Periode)."""
    ordner = OUT / "frames" / name; ordner.mkdir(parents=True, exist_ok=True)
    B = {f: dichte(f) for f in formen}
    n = len(formen)
    fig = fig_neu()
    if n == 1:
        axs = [fig.add_axes([0.07, 0.14, 0.38, 0.72])]; cax = fig.add_axes([0.51, 0.14, 0.015, 0.72]); axr = fig.add_axes([0.63, 0.14, 0.34, 0.72])
    else:
        axs = [fig.add_axes([0.06 + 0.255 * (k % 2), 0.55 - 0.42 * (k // 2) + 0.0, 0.215, 0.34]) for k in range(4)]
        cax = fig.add_axes([0.575, 0.14, 0.012, 0.72]); axr = fig.add_axes([0.71, 0.14, 0.27, 0.72])
    ims, pts, vl = {}, {}, {}
    for ax, f in zip(axs, formen):
        z = D[f][1]; j = D[f][0]
        if modus == "s":
            x = (z["phi"] - z["phi"][0]) * j["nfp"] / (2 * np.pi); xl = "Toroidalwinkel (1 = Periode)"; yl = "Feldlinie Nr."
            ims[f] = ax.pcolormesh(x, np.arange(NL), np.maximum(B[f][0], NORM.vmin), norm=NORM, cmap="magma", shading="auto", rasterized=True)
        else:
            xl = "Feldlinie Nr."; yl = "Fläche s (0 Mitte, 1 Rand)"
            ims[f] = ax.pcolormesh(np.arange(NL), S_FEIN, np.maximum(B[f][:, :, 0], NORM.vmin), norm=NORM, cmap="magma", shading="auto", rasterized=True)
        if n == 1 or ax in axs[2:]:
            ax.set_xlabel(xl)
        if n == 1 or axs.index(ax) % 2 == 0:
            ax.set_ylabel(yl)
        ax.tick_params(labelsize=8)
    cb = fig.colorbar(ims[formen[0]], cax=cax); cb.set_label("QI-Beitrag (hell = viel Fehler)", fontsize=8); cb.ax.tick_params(labelsize=7); cb.ax.yaxis.set_label_position("left")
    # rechtes Diagramm
    if modus == "s":
        for f in formen:
            z = D[f][1]; q = B[f].sum((1, 2)) / NL
            axr.semilogy(S_FEIN, q, color=FARBE[f], lw=1.5, label=KURZ[f]); axr.semilogy(z["s"], z["qi_flaeche"], "o", color=FARBE[f], ms=3.5)
            pts[f], = axr.plot([], [], "o", color=FARBE[f], ms=9, mec="k")
        grenzen(axr); axr.set_xlabel("Fläche s (0 Mitte, 1 Rand)"); axr.set_ylabel("QI der Fläche (kleiner = besser)"); axr.set_xlim(0, 1)
        axr.set_ylim(1e-6, 4e-3)
        axr.legend(fontsize=8, loc="lower right"); axr.grid(alpha=0.3, which="both"); axr.set_title("QI(s), Punkte = gerechnete Flächen", fontsize=10)
    else:
        for f in formen:
            z = D[f][1]; j = D[f][0]; x = (z["phi"] - z["phi"][0]) * j["nfp"] / (2 * np.pi)
            axr.semilogy(x, z["je_winkel"].sum(0), color=FARBE[f], lw=1.2, label=KURZ[f])
            vl[f], = axr.plot([], [], "o", color=FARBE[f], ms=9, mec="k")
        axr.set_xlabel("Toroidalwinkel (1 = Periode)"); axr.set_ylabel("QI-Beitrag (Summe über s und Feldlinien)")
        axr.set_xlim(0, 1); axr.legend(fontsize=8, loc="lower right"); axr.grid(alpha=0.3, which="both"); axr.set_title("Beitrag je Toroidalwinkel", fontsize=10)
    tit = fig.text(0.5, 0.95, "", ha="center", fontsize=12)
    wasserzeichen(fig)
    for k in range(NF):
        t = k / (NF - 1)
        if modus == "s":
            si = int(round(t * (NSI - 1)))
            for ax, f in zip(axs, formen):
                ims[f].set_array(np.maximum(B[f][si], NORM.vmin).ravel()); ax.set_title(f"{KURZ[f]}: s = {S_FEIN[si]:.2f}", fontsize=10 if n == 1 else 9)
                pts[f].set_data([S_FEIN[si]], [B[f][si].sum() / NL])
            tit.set_text("QI-Karte, Durchfahrt von innen nach außen" if n > 1 else f"{D[formen[0]][0]['name']}: Durchfahrt von innen nach außen")
        else:
            for ax, f in zip(axs, formen):
                z = D[f][1]; pi = int(round(t * (z["phi"].size - 1)))
                ims[f].set_array(np.maximum(B[f][:, :, pi], NORM.vmin).ravel()); ax.set_title(f"{KURZ[f]}: Toroidalwinkel {t:.2f}", fontsize=10 if n == 1 else 9)
                vl[f].set_data([t], [z["je_winkel"].sum(0)[pi]])
            tit.set_text("QI-Karte, Durchfahrt entlang einer Feldperiode" if n > 1 else f"{D[formen[0]][0]['name']}: Durchfahrt entlang einer Feldperiode")
        speichern(fig, ordner, k)
    plt.close(fig)
    mp4 = OUT / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(ordner / "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(mp4)], check=True)
    print("fertig", mp4, flush=True)


if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "alle"
    jobs = []
    for f in FORMEN:
        if w in ("alle", f):
            jobs += [(f"{f}_durchfahrt_s", [f], "s"), (f"{f}_durchfahrt_periode", [f], "phi")]
    if w in ("alle", "vergleich"):
        jobs += [("vergleich_durchfahrt_s", list(FORMEN), "s"), ("vergleich_durchfahrt_periode", list(FORMEN), "phi")]
    for a in jobs:
        video(*a)
