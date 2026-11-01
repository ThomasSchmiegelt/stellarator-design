"""tauscher_video.py — Teilchenbahnen durch das FluidX3D-Feld einer Tauscherseite (tauscher_cfd.py) fuer ein Video.

  .venv/bin/python -m stellarator.tauscher_video --fall gyroid_re3000_n48_z10 [--teilchen 6000] [--bilder 240] [--kacheln 3]

Das Endfeld (feld.bin) liegt auf dem Gitter; das Rechengebiet ist in allen Richtungen periodisch und wird fuer das
Bild quer kacheln x kacheln und laengs kacheln_z mal aneinandergelegt. Teilchen werden mit RK2 mitgefuehrt
(Zwischenschritte <= 0,5 Zelle) und tragen die Temperatur der Zelle, bezogen auf die Mischtemperatur (Wand = 0).
Ausgabe <fall>/video/bild_0000.npz (Schweife xyz [mm], theta), wand.stl (Tauscherwand [mm], ganz) und
wand_schnitt.stl (vordere Kachelreihe weggeschnitten), info.json.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from .tauscher_cfd import SIM


def lese(o):
    w = open(o / "fall.txt").read().split()
    Nx, Ny, Nz = (int(v) for v in w[2:5])
    f = open(o / "feld.bin", "rb"); M = int(np.frombuffer(f.read(8), np.uint64)[0])
    idx = np.frombuffer(f.read(4 * M), np.uint32); v = np.frombuffer(f.read(20 * M), np.float32).reshape(-1, 5)
    U = np.zeros((Nx * Ny * Nz, 3), np.float32); th = np.zeros(Nx * Ny * Nz, np.float32)
    U[idx] = v[:, :3]; th[idx] = v[:, 4]
    occ = np.fromfile(o / "geometrie.bin", np.uint8).reshape(Nz, Ny, Nx)
    return Nx, Ny, Nz, U.reshape(Nz, Ny, Nx, 3), th.reshape(Nz, Ny, Nx), occ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fall", required=True)
    ap.add_argument("--teilchen", type=int, default=6000)
    ap.add_argument("--bilder", type=int, default=240)
    ap.add_argument("--kacheln", type=int, default=3)
    ap.add_argument("--kacheln_z", type=int, default=3)
    ap.add_argument("--schweif", type=int, default=8)
    ap.add_argument("--schritte_bild", type=float, default=40.0, help="Gitterzeitschritte je Bild")
    a = ap.parse_args()
    o = SIM / a.fall; aus = o / "video"; aus.mkdir(exist_ok=True)
    for p in aus.glob("bild_*.npz"):
        p.unlink()
    erg = json.loads((o / "ergebnis.json").read_text())
    Nx, Ny, Nz, U, th, occ = lese(o)
    dx = erg["d_h"] / erg["n_dh"]
    K = a.kacheln
    rng = np.random.default_rng(1)

    KZ = a.kacheln_z
    box = np.array([Nx * K, Ny * K, Nz * KZ], float)
    tm = float((U[..., 2] * th).sum() / U[..., 2].sum())          # Mischtemperatur
    th = th / tm

    def feld(p):
        i = np.floor(p).astype(int)
        x, y, z = i[:, 0] % Nx, i[:, 1] % Ny, i[:, 2] % Nz
        return U[z, y, x], th[z, y, x], occ[z, y, x]

    def neu(n):
        p = rng.uniform(0, 1, (n, 3)) * box
        _, _, oc = feld(p)
        while (oc == 0).any():
            p[oc == 0] = rng.uniform(0, 1, (int((oc == 0).sum()), 3)) * box
            _, _, oc = feld(p)
        return p

    P = neu(a.teilchen)
    hist = [P.copy()] * a.schweif
    umax = float(np.abs(U).max())
    n_sub = max(1, int(np.ceil(a.schritte_bild * umax / 0.5)))
    h = a.schritte_bild / n_sub
    alter = rng.integers(0, 200, a.teilchen)
    for b in range(a.bilder + 60):
        for _ in range(n_sub):
            u1, _, _ = feld(P); u2, _, _ = feld(P + 0.5 * h * u1)
            P = P + h * u2
        u, t, oc = feld(P)
        alter += 1
        raus = (P < 0).any(1) | (P >= box).any(1)
        P = np.mod(P, box)                                         # periodisch in der Anzeige
        tot = (oc == 0) | (np.linalg.norm(u, axis=1) < 1e-5) | (alter > 400)
        if tot.any():
            P[tot] = neu(int(tot.sum())); alter[tot] = 0
        neu_s = tot | raus
        for k in range(len(hist)):
            hist[k][neu_s] = P[neu_s]
        hist = hist[1:] + [P.copy()]
        if b >= 60:
            S = np.stack(hist, 1) * dx                     # [n, schweif, 3] in mm
            _, t, _ = feld(P)
            np.savez_compressed(aus / f"bild_{b - 60:04d}.npz", xyz=S.astype(np.float32), theta=t.astype(np.float32))
    # Tauscherwand als Netz (Marching Cubes auf der Belegung, gekachelt), in mm
    import pyvista as pv
    fest = np.tile((occ == 0).astype(np.float32), (KZ, K, K))
    fest = np.pad(fest, ((0, 0), (1, 1), (1, 1)), mode="edge")
    g = pv.ImageData(dimensions=(fest.shape[2], fest.shape[1], fest.shape[0]), spacing=(dx, dx, dx), origin=(-dx, -dx, 0))
    g.point_data["f"] = fest.ravel(order="C")
    m = g.contour([0.5], scalars="f").smooth_taubin(n_iter=30).clip_box([0, Nx * K * dx, 0, Ny * K * dx, 0, Nz * KZ * dx], invert=False)
    m.extract_surface().save(aus / "wand.stl")
    m.clip_box([0, Nx * K * dx, 0, Ny * dx, 0, Nz * KZ * dx], invert=True).extract_surface().save(aus / "wand_schnitt.stl")
    info = dict(fall=a.fall, dx_mm=dx, gebiet_mm=[Nx * K * dx, Ny * K * dx, Nz * KZ * dx], bilder=a.bilder,
                Re=erg["Re"], Nu=erg["Nu"], f=erg["f"], typ=erg["typ"])
    (aus / "info.json").write_text(json.dumps(info, indent=1))
    print("VIDEO_DATEN_FERTIG", json.dumps(info))


if __name__ == "__main__":
    main()
