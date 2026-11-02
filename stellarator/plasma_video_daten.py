"""plasma_video_daten.py — Geometrie fuer das Plasmavideo (Blender): Flussflaechen, Spulen, Gefaess, Feldlinien.

  .venv-opt/bin/python -m stellarator.plasma_video_daten          # -> sim/video_plasma/szene.npz

Alles aus den eigenen Rechnungen, auf Anlagengroesse (R0 = 10,4 m, A = 4,5, HTS):
- Flussflaechen s = 1 (Plasmarand), 0,85 (Innenkante der leuchtenden Randschicht) aus dem VMEC-Gleichgewicht,
- 16 Spulen aus Stufe 2 (Mittellinie + Rahmen fuer einen quadratischen Querschnitt, Wickelpaket 0,76 m + Gehaeuse),
- Erstwand als Flaeche 0,5 m ausserhalb des Plasmarands (Normalenrichtung),
- Feldlinien im Spulenfeld (simsopt compute_fieldlines), Start auf der Aussenseite bei verschiedenen s.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "4")
from pathlib import Path

import numpy as np

from stellarator.alpha_bahnen import WOUT, SPULEN, L, wout, vmec_punkt

AUS = Path(__file__).resolve().parents[1] / "sim" / "video_plasma"
NPHI, NTH = 256, 96


def flaeche(s):
    from simsopt.geo import SurfaceRZFourier
    f = SurfaceRZFourier.from_wout(str(WOUT), s=s, range="full torus", nphi=NPHI, ntheta=NTH)
    return f.gamma() * L, f.unitnormal()


def spulen(breite=1.0):
    from simsopt import load
    bs = load(str(SPULEN)); out = []
    for c in bs.coils:
        g = c.curve.gamma() * L; t = c.curve.gammadash(); t /= np.linalg.norm(t, axis=1)[:, None]
        m = g.mean(0); n = g - m; n -= (n * t).sum(1)[:, None] * t; n /= np.linalg.norm(n, axis=1)[:, None]
        out.append(np.stack([g, n, np.cross(t, n)], 1))          # (N, 3 Vektoren, 3)
    return np.array(out), breite


def feldlinien(n_s=(0.15, 0.4, 0.65, 0.9), n_th=3, laenge_u=220.0):
    from simsopt import load
    from simsopt.field.tracing import compute_fieldlines
    w = wout(); bs = load(str(SPULEN))
    R0, Z0, info = [], [], []
    for s in n_s:
        for th in np.linspace(0, 2 * np.pi, n_th, endpoint=False):
            x, _ = vmec_punkt(w, np.array([s]), np.array([th]), np.array([0.0]))
            R0.append(np.hypot(x[0, 0], x[0, 1])); Z0.append(x[0, 2]); info.append((s, th))
    res, _ = compute_fieldlines(bs, R0, Z0, tmax=laenge_u, tol=1e-9)
    linien = []
    for r in res:
        p = r[:, 1:4] * L
        # gleichmaessig nach Bogenlaenge, 0,25 m Abstand
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        q = np.linspace(0, d[-1], int(d[-1] / 0.25))
        linien.append(np.column_stack([np.interp(q, d, p[:, k]) for k in range(3)]))
    return linien, np.array(info)


def main():
    AUS.mkdir(parents=True, exist_ok=True)
    rand, nrm = flaeche(1.0); innen, _ = flaeche(0.85); kern, _ = flaeche(0.5)
    wand = rand + 0.5 * nrm
    sp, breite = spulen()
    lin, info = feldlinien()
    w = wout()
    np.savez_compressed(AUS / "szene.npz", rand=rand, innen=innen, kern=kern, wand=wand, nphi=NPHI, nth=NTH,
                        spulen=sp, spule_breite=breite, linien_xyz=np.concatenate(lin), linien_n=np.array([len(l) for l in lin]), linien_info=info,
                        R0=10.4, a=2.31, nfp=w["nfp"], achse_raxis=w["raxis_cc"] * L, achse_zaxis=w["zaxis_cs"] * L)
    r = rand.reshape(-1, 3); R = np.hypot(r[:, 0], r[:, 1])
    print("Rand R", R.min().round(2), "...", R.max().round(2), "Z", r[:, 2].min().round(2), r[:, 2].max().round(2))
    print("Spulen", sp.shape, "Feldlinien", len(lin), "Laengen [m]", [round(len(l) * 0.25) for l in lin][:6])
    # iota-Kontrolle: Ring-Umlaeufe vs. poloidale Umlaeufe der ersten Linie (s=0,15)
    for k in (0, 3, 9):
        q = lin[k]; ph = np.unwrap(np.arctan2(q[:, 1], q[:, 0])); Rr = np.hypot(q[:, 0], q[:, 1])
        ax = np.interp(ph, [ph.min(), ph.max()], [0, 0]) + 10.4
        th = np.unwrap(np.arctan2(q[:, 2], Rr - 10.4))
        print(f"  Linie {k} s={info[k,0]}: Ringumlaeufe {abs(ph[-1]-ph[0])/2/np.pi:.2f}, poloidal {abs(th[-1]-th[0])/2/np.pi:.2f}, iota ~ {abs(th[-1]-th[0])/abs(ph[-1]-ph[0]):.3f}")
    # Abstand Spule-Plasma (Kontrolle gegen Erwartung ~0,5 m Spalt + halbe Spulenbreite)
    from scipy.spatial import cKDTree
    d, _ = cKDTree(rand.reshape(-1, 3)).query(sp[:, :, 0].reshape(-1, 3))
    print("min Abstand Spulenmitte-Plasmarand [m]", d.min().round(2))


if __name__ == "__main__":
    main()
