"""spulen.py — W7-X-Spulensatz aus Fourier-Daten, Symmetrie, Wickelpaket-Geometrie.

Quelle der Filamente: daten/W7-X.dat (s. daten/QUELLE.md). Einheiten: SI (m, A).
Ein Spulensatz ist eine Liste von Spule-Objekten (geschlossenes Polygon + Strom
in Ampere-Windungen). Wickelpakete werden als rechteckiges Rohr um das Filament
trianguliert (Normalen nach aussen) und als binaeres STL in mm geschrieben.
"""
from __future__ import annotations
import struct
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

DATEN = Path(__file__).resolve().parent / "daten"
BASIS_NAMEN = ["NPC1", "NPC2", "NPC3", "NPC4", "NPC5", "PCA", "PCB"]

# Magnetische Achse W7-X Standardkonfiguration (simsopt zoo.py, nfp=5)
ACHSE_CR = [5.56069066955626, 0.370739830964738, 0.0161526928867275,
            0.0011820724983052, 3.43773868380292e-06, -4.71423775536881e-05,
            -6.23133271265022e-05, 2.06622580616597e-06, -0.000113256675159501,
            5.0296895894932e-07, 7.02308687052046e-05, 5.13479338167885e-05,
            1.90731007856885e-05]
ACHSE_SZ = [0, -0.308156954586225, -0.0186374002410851,
            -0.000261743895528833, 5.78207516751575e-05, -0.000129121205314107,
            3.08849630026052e-05, 1.95450172782866e-05, -8.32136392792337e-05,
            6.19785500011441e-05, 1.36521157246782e-05, -1.46281683516623e-05,
            -1.5142136543872e-06]


@dataclass
class Spule:
    name: str          # z.B. "NPC3_p2_f" (Typ, Periode, f=gespiegelt)
    typ: str           # Basistyp NPC1..5, PCA, PCB
    punkte: np.ndarray # (N,3) geschlossenes Polygon, letzter != erster Punkt
    strom: float       # Ampere-Windungen (Vorzeichen inkl. Symmetrie-Flip)
    meta: dict = field(default_factory=dict)

    def tangenten(self) -> np.ndarray:
        """Einheitstangenten (zentrale Differenzen, periodisch)."""
        d = np.roll(self.punkte, -1, 0) - np.roll(self.punkte, 1, 0)
        return d / np.linalg.norm(d, axis=1, keepdims=True)

    def laenge(self) -> float:
        return float(np.sum(np.linalg.norm(np.roll(self.punkte, -1, 0) - self.punkte, axis=1)))


def lade_basis(pfad: Path = DATEN / "W7-X.dat", ordnung: int = 48) -> list[np.ndarray]:
    """Fourier-Koeffizienten je Basisspule als Array (ordnung+1, 6)."""
    d = np.loadtxt(pfad, delimiter=",")
    assert d.shape[1] % 6 == 0
    ordnung = min(ordnung, d.shape[0] - 1)
    return [d[: ordnung + 1, 6 * i: 6 * i + 6] for i in range(d.shape[1] // 6)]


def kurve(koef: np.ndarray, n: int) -> np.ndarray:
    """Filament an n aequidistanten Parameterwerten t in [0,1)."""
    t = np.arange(n) / n
    m = np.arange(koef.shape[0])[:, None]
    c, s = np.cos(2 * np.pi * m * t), np.sin(2 * np.pi * m * t)   # (M,n)
    x = koef[:, 1] @ c + koef[:, 0] @ s
    y = koef[:, 3] @ c + koef[:, 2] @ s
    z = koef[:, 5] @ c + koef[:, 4] @ s
    return np.column_stack([x, y, z])


def w7x_spulensatz(stroeme: dict | None = None, n_punkte: int = 160, nfp: int = 5) -> list[Spule]:
    """70 Spulen (7 Basis x 5 Perioden x 2 Spiegelungen).

    stroeme: Ampere-Windungen je Basistyp; Default = simsopt-Standardkonfig.
    (NPC 15 kA x 108 Wdg, PCA/PCB = 0).
    """
    std = {n: 15e3 * 108 for n in BASIS_NAMEN[:5]} | {"PCA": 0.0, "PCB": 0.0}
    stroeme = std | (stroeme or {})
    basis = lade_basis()
    F = np.diag([1.0, -1.0, -1.0])
    out = []
    for k in range(nfp):
        phi = 2 * np.pi * k / nfp
        R = np.array([[np.cos(phi), -np.sin(phi), 0], [np.sin(phi), np.cos(phi), 0], [0, 0, 1]])
        for flip in (False, True):
            for name, koef in zip(BASIS_NAMEN, basis):
                p = kurve(koef, n_punkte) @ R.T
                if flip:
                    p = p @ F.T
                out.append(Spule(f"{name}_p{k}_{'f' if flip else 'n'}", name, p,
                                 -stroeme[name] if flip else stroeme[name],
                                 {"periode": k, "flip": flip}))
    return out


def lade_spulensatz(c: dict, n_punkte: int | None = None) -> tuple[list[Spule], dict]:
    """Spulensatz + Geometrie-Rahmen fuer Feldlinien/Bewertung aus dem Fall-Abschnitt "spulen".

    quelle "w7x" (Standard): reale W7-X-Filamente, Stroeme aus stroeme_Awdg.
    quelle "datei": Austauschformat aus invers/stufe2_spulen.py (spulen.json: punkte_m, strom_A,
      nfp, n_basis, R0_m, plasma_rand). Optional skaliert auf c["R0_m"] (Groesse frei waehlbar,
      Form massstabsfrei) und je Typ mit c["strom_faktoren"]; B0 setzt die Kalibrierung.
    Rahmen: nfp, Zylindergitter (R, Z), Feldlinien-Grenzen, Achsen-Startwert, dR fuer Feldlinien,
    n_basis (Symmetrie-Basisspulen fuer cad.abstaende).
    """
    n_punkte = n_punkte or c.get("n_punkte", 160)
    if c.get("quelle", "w7x") == "w7x":
        a = achse(np.array([0.0]))[0]
        return w7x_spulensatz(c.get("stroeme_Awdg"), n_punkte=n_punkte), {
            "nfp": 5, "R_gitter": (4.3, 7.0, 55), "Z_gitter": (-1.35, 1.35, 55), "R_grenze": (4.0, 7.0),
            "Z_grenze": 1.5, "achse_start": (float(np.hypot(a[0], a[1])), float(a[2])), "dR_max_m": 0.65,
            "n_basis": 7}
    import json
    d = json.loads(Path(c["datei"]).read_text())
    sk = c.get("R0_m", d["R0_m"]) / d["R0_m"]
    fak = c.get("strom_faktoren", {})
    spulen = []
    for q in d["spulen"]:
        P = np.asarray(q["punkte_m"]) * sk
        if n_punkte != len(P):                         # periodischer Spline auf n_punkte
            from scipy.interpolate import CubicSpline
            Q = np.vstack([P, P[:1]]); t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
            P = CubicSpline(t, Q, bc_type="periodic")(np.linspace(0, t[-1], n_punkte, endpoint=False))
        spulen.append(Spule(q["name"], q["typ"], P, q["strom_A"] * fak.get(q["typ"], 1.0)))
    pr = d["plasma_rand"]
    rand = 0.5 * d.get("abstand_sp_min_m", 0.2 * d["R0_m"]) * sk       # Gitter bleibt vor den Spulen
    Rg = (pr["R_min_m"] * sk - rand, pr["R_max_m"] * sk + rand)
    Zg = pr["Z_max_m"] * sk + rand
    return spulen, {"nfp": d["nfp"], "R_gitter": (*Rg, 55), "Z_gitter": (-Zg, Zg, 55), "R_grenze": Rg,
                    "Z_grenze": Zg, "achse_start": (pr["R_achse_phi0_m"] * sk, 0.0),
                    "dR_max_m": 1.15 * (pr["R_aussen_phi0_m"] - pr["R_achse_phi0_m"]) * sk,
                    "n_basis": d["n_basis"], "skala": sk}


def achse(phi: np.ndarray, nfp: int = 5) -> np.ndarray:
    """Magnetische Achse (Standardkonfig.) als (N,3) kartesisch.

    Vorzeichen von Z gegenueber simsopt (zoo.py) umgekehrt: in unserer Spulen-Konvention
    stimmt erst -Z mit der per Feldlinie verfolgten Achse ueberein (0,2 mm, B-016).
    Fuer andere Stroeme verschiebt sich die Achse -> bewerte.finde_achse() nutzen.
    """
    n = np.arange(len(ACHSE_CR))[:, None]
    R = np.asarray(ACHSE_CR) @ np.cos(nfp * n * phi)
    Z = -(np.asarray(ACHSE_SZ) @ np.sin(nfp * n * phi))
    return np.column_stack([R * np.cos(phi), R * np.sin(phi), Z])


# ---------------------------------------------------------------- Biot-Savart
MU0 = 4e-7 * np.pi


def segmente(spulen: list[Spule]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Anfangs-, Endpunkte und Strom aller geraden Filamentsegmente."""
    A = np.vstack([s.punkte for s in spulen])
    B = np.vstack([np.roll(s.punkte, -1, 0) for s in spulen])
    I = np.concatenate([np.full(len(s.punkte), s.strom) for s in spulen])
    return A, B, I


try:
    import numba

    @numba.njit(parallel=True, fastmath=True, cache=True)
    def _bs_kern(x, A, Bp, I, out):
        for k in numba.prange(x.shape[0]):
            bx = by = bz = 0.0
            for m in range(A.shape[0]):
                ax, ay, az = A[m, 0] - x[k, 0], A[m, 1] - x[k, 1], A[m, 2] - x[k, 2]
                cx, cy, cz = Bp[m, 0] - x[k, 0], Bp[m, 1] - x[k, 1], Bp[m, 2] - x[k, 2]
                la = np.sqrt(ax * ax + ay * ay + az * az)
                lb = np.sqrt(cx * cx + cy * cy + cz * cz)
                den = la * lb * (la * lb + ax * cx + ay * cy + az * cz)
                if den < 1e-30:
                    continue
                f = I[m] * (la + lb) / den
                bx += f * (ay * cz - az * cy)
                by += f * (az * cx - ax * cz)
                bz += f * (ax * cy - ay * cx)
            out[k, 0], out[k, 1], out[k, 2] = bx, by, bz
except ImportError:          # Fallback: reines numpy
    _bs_kern = None


def biot_savart(x: np.ndarray, seg, chunk: int = 256) -> np.ndarray:
    """B [T] an Punkten x (N,3); exakte Formel fuer gerade Segmente
    B = mu0 I/4pi * (a x b)(|a|+|b|) / (|a||b|(|a||b| + a.b)), a,b = Enden - x."""
    A, Bp, I = seg
    x = np.ascontiguousarray(np.atleast_2d(np.asarray(x, float)))
    out = np.empty_like(x)
    if _bs_kern is not None:
        _bs_kern(x, A, Bp, I, out)
        return out * MU0 / (4 * np.pi)
    for k in range(0, len(x), chunk):
        p = x[k:k + chunk, None, :]
        a, b = A[None] - p, Bp[None] - p
        la, lb = np.linalg.norm(a, axis=2), np.linalg.norm(b, axis=2)
        den = la * lb * (la * lb + np.einsum("cmi,cmi->cm", a, b))
        f = I * (la + lb) / np.maximum(den, 1e-30)
        out[k:k + chunk] = np.einsum("cm,cmi->ci", f, np.cross(a, b))
    return out * MU0 / (4 * np.pi)


def kalibriere(spulen: list[Spule], B0: float, n_achse: int = 60) -> float:
    """Skaliert alle Stroeme so, dass mittleres |B| auf der Achse = B0. Gibt Faktor zurueck."""
    b = np.linalg.norm(biot_savart(achse(np.linspace(0, 2 * np.pi, n_achse, endpoint=False)),
                                   segmente(spulen)), axis=1).mean()
    f = B0 / b
    for s in spulen:
        s.strom *= f
    return f


# ---------------------------------------------------------- Wickelpaket-Geometrie
def rahmen(s: Spule) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Lokales Dreibein je Punkt: t (Tangente), n (vom Spulenschwerpunkt weg, senkrecht t),
    b = t x n. Fuer modulare Spulen ist n die Richtung 'nach aussen vom Plasma'."""
    t = s.tangenten()
    r = s.punkte - s.punkte.mean(0)
    n = r - np.sum(r * t, 1, keepdims=True) * t
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return t, n, np.cross(t, n)


def rohr_dreiecke(s: Spule, breite: float, hoehe: float) -> np.ndarray:
    """Rechteckrohr (breite entlang n, hoehe entlang b) als Dreiecke (M,3,3), geschlossen."""
    t, n, b = rahmen(s)
    ecken = [(-1, -1), (1, -1), (1, 1), (-1, 1)]          # (n,b)-Vorzeichen, gegen Uhrzeigersinn um t
    P = np.stack([s.punkte + 0.5 * (en * breite * n + eb * hoehe * b) for en, eb in ecken], 1)  # (N,4,3)
    N = len(s.punkte)
    tri = []
    for i in range(N):
        j = (i + 1) % N
        for c in range(4):
            d = (c + 1) % 4
            # Quad (i,c)-(i,d)-(j,d)-(j,c), Normale nach aussen
            tri.append((P[i, c], P[j, c], P[j, d]))
            tri.append((P[i, c], P[j, d], P[i, d]))
    tri = np.asarray(tri)
    # Orientierung pruefen: Volumen (Divergenzsatz) muss positiv sein
    vol = np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6
    return tri if vol > 0 else tri[:, ::-1]


def schreibe_stl(pfad: Path, dreiecke: np.ndarray, skala: float = 1000.0) -> None:
    """Binaeres STL; skala=1000 -> mm."""
    tri = np.asarray(dreiecke, np.float64) * skala
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-30)
    rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, tri
    with open(pfad, "wb") as f:
        f.write(b"stellarator wickelpakete".ljust(80, b" "))
        f.write(struct.pack("<I", len(tri)))
        f.write(rec.tobytes())
