"""feldlinien.py — Feldlinienverfolgung, Poincare-Schnitt, Rotationstransformation iota.

Integration in Zylinderkoordinaten mit phi als Zeitvariable:
  dR/dphi = R B_R / B_phi,  dZ/dphi = R B_Z / B_phi   (RK4, feste Schrittweite)
Alle Startpunkte werden gemeinsam (vektorisiert) verfolgt. Das Feld kommt aus einer
beliebigen Funktion feld(x (N,3)) -> B (N,3): Biot-Savart oder Voxel-Solver-Interpolant.
Wegen nfp-Periodizitaet ist jeder Durchgang durch phi = k*2pi/nfp ein Poincare-Punkt
der Ebene phi=0.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage


class ZylinderGitter:
    """B auf einem (R, phi, Z)-Gitter EINER Feldperiode, kubische Spline-Interpolation.

    Zylinderkomponenten (B_R, B_phi, B_Z) sind nfp-periodisch in phi, daher genuegt eine
    Periode; phi wird periodisch um RAND Zellen gepolstert.
    """
    RAND = 4

    def __init__(self, feld, R=(4.3, 7.0, 55), Z=(-1.35, 1.35, 55), n_phi=36, nfp=5):
        self.nfp = nfp
        self.R = np.linspace(*R); self.Z = np.linspace(*Z)
        self.dphi = 2 * np.pi / nfp / n_phi
        phi = np.arange(n_phi) * self.dphi
        RR, PP, ZZ = np.meshgrid(self.R, phi, self.Z, indexing="ij")
        x = np.column_stack([(RR * np.cos(PP)).ravel(), (RR * np.sin(PP)).ravel(), ZZ.ravel()])
        B = feld(x)
        c, s = np.cos(PP.ravel()), np.sin(PP.ravel())
        komp = [B[:, 0] * c + B[:, 1] * s, -B[:, 0] * s + B[:, 1] * c, B[:, 2]]
        self.roh = np.stack([k.reshape(RR.shape) for k in komp])          # (3,nR,nphi,nZ)
        g = np.concatenate([self.roh[:, :, -self.RAND:], self.roh, self.roh[:, :, :self.RAND]], 2)
        self.koef = [ndimage.spline_filter(g[i], order=3, mode="nearest") for i in range(3)]

    @classmethod
    def aus_roh(cls, roh, R, Z, nfp=5):
        """Rekonstruktion aus gespeicherten Rohdaten (npz-Cache)."""
        self = cls.__new__(cls)
        self.nfp, self.R, self.Z, self.roh = nfp, R, Z, roh
        self.dphi = 2 * np.pi / nfp / roh.shape[2]
        g = np.concatenate([roh[:, :, -cls.RAND:], roh, roh[:, :, :cls.RAND]], 2)
        self.koef = [ndimage.spline_filter(g[i], order=3, mode="nearest") for i in range(3)]
        return self

    def __call__(self, x):
        x = np.atleast_2d(x)
        R = np.hypot(x[:, 0], x[:, 1]); phi = np.arctan2(x[:, 1], x[:, 0])
        per = 2 * np.pi / self.nfp
        ip = np.mod(phi, per) / self.dphi + self.RAND
        iR = (R - self.R[0]) / (self.R[1] - self.R[0])
        iZ = (x[:, 2] - self.Z[0]) / (self.Z[1] - self.Z[0])
        k = np.vstack([iR, ip, iZ])
        BR, Bp, BZ = (ndimage.map_coordinates(c, k, order=3, mode="nearest", prefilter=False)
                      for c in self.koef)
        c, s = np.cos(phi), np.sin(phi)
        return np.column_stack([BR * c - Bp * s, BR * s + Bp * c, BZ])


def _rhs(feld, R, Z, phi):
    x = np.column_stack([R * np.cos(phi), R * np.sin(phi), Z])
    B = feld(x)
    c, s = np.cos(phi), np.sin(phi)
    BR = B[:, 0] * c + B[:, 1] * s
    Bp = -B[:, 0] * s + B[:, 1] * c
    BZ = B[:, 2]
    return R * BR / Bp, R * BZ / Bp


def verfolge(feld, R0, Z0, n_umlaeufe: int = 50, nfp: int = 5, schritte_pro_periode: int = 48,
             R_grenze=(4.0, 7.0), Z_grenze=1.5):
    """Verfolgt Feldlinien ab (R0,Z0) bei phi=0.

    Rueckgabe: punkte (n_linien, n_umlaeufe*nfp, 2) mit (R,Z) in der Ebene phi=0 (NaN nach
    Verlust), verloren (bool je Linie).
    """
    R = np.asarray(R0, float).copy(); Z = np.asarray(Z0, float).copy()
    n = len(R); h = 2 * np.pi / nfp / schritte_pro_periode
    pk = np.full((n, n_umlaeufe * nfp, 2), np.nan)
    aktiv = np.ones(n, bool)
    phi = 0.0
    for k in range(n_umlaeufe * nfp):
        for _ in range(schritte_pro_periode):
            i = np.flatnonzero(aktiv)
            if i.size == 0:
                return pk, ~aktiv
            r, z = R[i], Z[i]
            k1 = _rhs(feld, r, z, phi)
            k2 = _rhs(feld, r + h / 2 * k1[0], z + h / 2 * k1[1], phi + h / 2)
            k3 = _rhs(feld, r + h / 2 * k2[0], z + h / 2 * k2[1], phi + h / 2)
            k4 = _rhs(feld, r + h * k3[0], z + h * k3[1], phi + h)
            R[i] = r + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
            Z[i] = z + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
            phi += h
            raus = (R < R_grenze[0]) | (R > R_grenze[1]) | (np.abs(Z) > Z_grenze) | ~np.isfinite(R)
            aktiv &= ~raus
        pk[aktiv, k] = np.column_stack([R[aktiv], Z[aktiv]])
    return pk, ~aktiv


def iota(pk: np.ndarray, achse_RZ: tuple[float, float], nfp: int = 5) -> np.ndarray:
    """Rotationstransformation je Linie aus dem mittleren poloidalen Winkelfortschritt
    um die Achse pro toroidalem Umlauf (Poincare-Punkte im Abstand 2pi/nfp)."""
    th = np.arctan2(pk[..., 1] - achse_RZ[1], pk[..., 0] - achse_RZ[0])
    d = np.diff(np.unwrap(th, axis=1), axis=1)       # pro Periode
    out = np.full(len(d), np.nan)
    ok = np.isfinite(d).any(axis=1)
    out[ok] = np.nanmean(d[ok], axis=1) * nfp / (2 * np.pi)
    return out
