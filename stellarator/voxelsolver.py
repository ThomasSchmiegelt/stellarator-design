"""voxelsolver.py — Magnetostatik auf dem Voxelgitter per FFT-Faltung (Hockney-Verfahren).

Gleichung (Luft/nichtmagnetisch, Coulomb-Eichung):  laplace A = -mu0 J
Freiraumloesung:  A(x) = mu0/4pi * int J(x')/|x-x'| dV'   -> diskret als Faltung mit der
Greenfunktion G = 1/(4 pi r) auf dem doppelt gepolsterten Gitter (keine Periodizitaet,
keine Randbedingung noetig). Selbstzelle: Zellmittel von 1/r ueber den Wuerfel,
int_[-1/2,1/2]^3 dV/r = 2.3800772 -> G(0) = 2.3800772/(4 pi h).
B = rot A mit zentralen Differenzen.

Stromdichte aus der Voxelbelegung: jede Zelle mit Volumenanteil w>0 gehoert zum naechsten
Filamentpunkt (Spule c, Tangente t). J = I_c * t * w * L_c / (sum_c(w) * h^3), damit int J dV
je Spule das Strommoment I_c * Laenge exakt traegt, unabhaengig von der Diskretisierung.
"""
from __future__ import annotations
import time
import numpy as np
from scipy import fft, ndimage
from .spulen import Spule, MU0
from .picogk_bruecke import Gitter, zuordnung

C_WUERFEL = 2.3800772


def stromdichte(spulen: list[Spule], gitter: Gitter, idx: np.ndarray, w: np.ndarray):
    """J (Nzellen,3) [A/m^2] und Spulenindex je Zelle; w = Volumenanteil."""
    x = gitter.punkte(idx)
    sid, pid, _ = zuordnung(spulen, x)
    tang = [s.tangenten() for s in spulen]
    t = np.array([tang[s][p] for s, p in zip(sid, pid)])
    N = np.bincount(sid, weights=w, minlength=len(spulen))
    L = np.array([s.laenge() for s in spulen])
    I = np.array([s.strom for s in spulen])
    with np.errstate(divide="ignore", invalid="ignore"):
        fak = np.where(N > 0, I * L / (N * gitter.h ** 3), 0.0)
    return t * (w * fak[sid])[:, None], sid


class VoxelFeld:
    """Loest A und B auf dem Gitter; Auswertung an beliebigen Punkten (trilinear/kubisch)."""

    def __init__(self, gitter: Gitter, idx: np.ndarray, J: np.ndarray, log=print):
        self.g = gitter
        n = np.array(gitter.n); m = 2 * n
        t0 = time.time()
        # Greenfunktion mit Wrap-around-Abstaenden auf dem gepolsterten Gitter
        ax = [np.minimum(np.arange(k), k - np.arange(k)) * gitter.h for k in m]
        r2 = ax[0][:, None, None] ** 2 + ax[1][None, :, None] ** 2 + ax[2][None, None, :] ** 2
        with np.errstate(divide="ignore"):
            G = (1.0 / (4 * np.pi * np.sqrt(r2))).astype(np.float32)
        G[0, 0, 0] = C_WUERFEL / (4 * np.pi * gitter.h)
        del r2
        Gh = fft.rfftn(G, workers=-1); del G
        self.A = np.empty((3, *n), np.float32)
        for c in range(3):
            Jc = np.zeros(m, np.float32)
            Jc[np.unravel_index(idx, gitter.n)] = J[:, c]
            Ac = fft.irfftn(fft.rfftn(Jc, workers=-1) * Gh, s=tuple(m), workers=-1)
            self.A[c] = MU0 * gitter.h ** 3 * Ac[: n[0], : n[1], : n[2]]
        del Gh
        d = [np.gradient(self.A[c], gitter.h) for c in range(3)]   # d[c][k] = dA_c/dx_k
        self.B = np.stack([d[2][1] - d[1][2], d[0][2] - d[2][0], d[1][0] - d[0][1]])
        self.t_loes = time.time() - t0
        log(f"  Voxelsolver: Gitter {tuple(n)} (FFT {tuple(m)}), {self.t_loes:.1f} s")

    def __call__(self, x, ordnung=1):
        k = ((np.atleast_2d(x) - self.g.ursprung) / self.g.h).T
        return np.column_stack([ndimage.map_coordinates(self.B[c], k, order=ordnung, mode="nearest")
                                for c in range(3)])
