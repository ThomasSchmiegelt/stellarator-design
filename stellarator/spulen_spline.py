"""Spulen nach der Berechnung glätten: Methodenvergleich entlang der Bogenlänge (nie über räumliche Nähe, damit die Äste
einer „8“ nicht vermischt werden). Anlass: CAD-Methode des Nutzers und seine Methodenliste (2026-11-08).

Jede Grundspule wird zuerst auf 512 Punkte in gleichen Bogenabständen gebracht (Bogenlängen-Parametrisierung), dann:
  cad_N        N Punkte in gleichen Bogenabständen, geschlossener kubischer Interpolationsspline hindurch (Nutzer-CAD-Weg)
  splprep_S    geschlossener Glättungsspline (scipy splprep, per=1), Glättung s = 512 * (S cm / Maßstab)²
  taubin_K     Taubin-λ/μ-Glättung (λ = 0,5, μ = -0,53), K Durchgänge, periodisch
  fourier_M    Tiefpass entlang der Bogenlänge: nur die ersten M Harmonischen behalten
  savgol_W     Savitzky-Golay, Fenster W Punkte (von 512), Polynomgrad 3, periodisch (mode wrap)
Danach Nachbildung als CurveXYZFourier Ordnung 24 für die Feldrechnung (Fehler wird ausgegeben),
Feldfehler (spulen_satz.feldfehler) und Baubarkeit (spulen_glaetten.baubarkeit).
Aufruf: python spulen_spline.py <satz_ordner> <aus_ordner>
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline, splev, splprep
from scipy.signal import savgol_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import feldfehler, flaeche, lade_satz  # noqa: E402
from spulen_glaetten import baubarkeit, A_M  # noqa: E402

ORD_FIT, NQ = 24, 512
METHODEN = ["cad_64", "cad_32", "cad_16", "cad_12", "cad_8",
            "splprep_5", "splprep_20", "splprep_50",
            "taubin_50", "taubin_300", "taubin_2000",
            "fourier_12", "fourier_8", "fourier_5",
            "savgol_31", "savgol_81", "savgol_161"]


def bogen(c, n=NQ):
    from simsopt.geo import CurveXYZFourier
    f = CurveXYZFourier(8192, c.order); f.x = c.x; g = f.gamma()
    ds = np.linalg.norm(np.diff(np.vstack([g, g[:1]]), axis=0), axis=1); s = np.concatenate([[0], np.cumsum(ds)])
    z = np.linspace(0, s[-1], n, endpoint=False)
    return np.column_stack([np.interp(z, s[:-1], g[:, j]) for j in range(3)])


def cad(p, n):
    q = p[np.linspace(0, len(p), n, endpoint=False).astype(int)]
    qz = np.vstack([q, q[:1]]); t = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(qz, axis=0), axis=1))])
    return CubicSpline(t, qz, bc_type="periodic")(np.linspace(0, t[-1], NQ, endpoint=False))


def glaette(p, art, wert, k):
    if art == "cad":
        return cad(p, wert)
    if art == "splprep":
        tck, _ = splprep(p.T, s=len(p) * (wert / 100 / k) ** 2, per=1)
        return np.array(splev(np.linspace(0, 1, NQ, endpoint=False), tck)).T
    if art == "taubin":
        q = p.copy()
        for _ in range(wert):
            for f in (0.5, -0.53):
                q = q + f * (0.5 * (np.roll(q, 1, 0) + np.roll(q, -1, 0)) - q)
        return q
    if art == "fourier":
        F = np.fft.rfft(p, axis=0); F[wert + 1:] = 0
        return np.fft.irfft(F, n=len(p), axis=0)
    if art == "savgol":
        return savgol_filter(p, wert, 3, axis=0, mode="wrap")
    raise ValueError(art)


def als_kurve(q):
    from simsopt.geo import CurveXYZFourier
    u = np.linspace(0, 1, NQ, endpoint=False); M = [np.ones_like(u)]
    for j in range(1, ORD_FIT + 1):
        M += [np.sin(2 * np.pi * j * u), np.cos(2 * np.pi * j * u)]
    M = np.array(M).T
    x = CurveXYZFourier(NQ, ORD_FIT); x.x = np.concatenate([np.linalg.lstsq(M, q[:, j], rcond=None)[0] for j in range(3)])
    return x, float(np.abs(x.gamma() - q).max())


def main(satz, aus):
    satz, aus = Path(satz), Path(aus); aus.mkdir(parents=True, exist_ok=True)
    basis, I, nfp = lade_satz(satz)
    s = flaeche(satz / "boundary.json")
    a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0))))); k = A_M / a
    roh = [bogen(c) for c in basis]
    bm, _ = feldfehler(basis, I, nfp, s)
    erg = {"satz": str(satz), "m_je_einheit": k, "original": {"Bn_mittel": bm, "spulen": [baubarkeit(c, k) for c in basis],
           "punkte_m": [(p * k).tolist() for p in roh]}, "methoden": []}
    print(json.dumps({"original": bm}), flush=True)
    for m in METHODEN:
        art, wert = m.split("_"); wert = int(wert)
        q = [glaette(p, art, wert, k) for p in roh]
        kurven = [als_kurve(x) for x in q]
        bm, bx = feldfehler([x[0] for x in kurven], I, nfp, s)
        abw = max(float(np.max(np.min(np.linalg.norm(x[:, None] - p[None], axis=2), axis=1))) for x, p in zip(q, roh)) * k
        e = {"methode": m, "Bn_mittel": bm, "Bn_max": bx, "nachbildung_max_m": max(x[1] for x in kurven) * k,
             "abweichung_max_m": abw, "spulen": [baubarkeit(x[0], k) for x in kurven], "punkte_m": [(x * k).tolist() for x in q]}
        erg["methoden"].append(e)
        print(json.dumps({kk: v for kk, v in e.items() if kk != "punkte_m"}), flush=True)
    (aus / "spline.json").write_text(json.dumps(erg))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
