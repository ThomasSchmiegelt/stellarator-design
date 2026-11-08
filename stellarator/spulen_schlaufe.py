"""„8“ vermeiden mit der CAD-Methode des Nutzers (2026-11-08): Punkte auf der Spule, geschlossener Spline hindurch,
aber in der Schlaufe Punkte weglassen (Modus weglassen) oder lokal ausdünnen (Modus ausduennen, nur jeden 3. Punkt),
wiederholt, bis die Seitenansichten keine Kreuzung mehr zeigen.

Ablauf je Grundspule: 512 Punkte in gleichen Bogenabständen, davon 64 als Stützpunkte (wie CAD-Weg 64, Feldfehler ≈ Original).
Seitenansichten = Projektion auf (Hauptachse 1, Normale) und (Hauptachse 2, Normale) der ORIGINAL-Spule (fester Rahmen).
Je Kreuzung: die kürzere Schlaufe zwischen den beiden kreuzenden Stücken wird bearbeitet.
Aufruf: python spulen_schlaufe.py <satz_ordner> <aus_ordner>
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import feldfehler, flaeche, lade_satz  # noqa: E402
from spulen_glaetten import baubarkeit, A_M  # noqa: E402
from spulen_spline import bogen, als_kurve, NQ  # noqa: E402

N_STUETZ, MIN_STUETZ, MAX_SCHRITTE = 64, 10, 12


def kreuzung(p2):
    """erste Selbstkreuzung eines geschlossenen 2D-Polygons: (i, j) Segmentindizes, sonst None."""
    a, b = p2, np.roll(p2, -1, 0); n = len(p2)
    d = lambda u, v, w: (v[..., 0] - u[..., 0]) * (w[..., 1] - u[..., 1]) - (v[..., 1] - u[..., 1]) * (w[..., 0] - u[..., 0])
    for i in range(n):
        j = np.arange(i + 2, n if i > 0 else n - 1)
        if len(j) == 0:
            continue
        s1 = d(a[i], b[i], a[j]) * d(a[i], b[i], b[j]); s2 = d(a[j], b[j], a[i]) * d(a[j], b[j], b[i])
        h = np.nonzero((s1 < 0) & (s2 < 0))[0]
        if len(h):
            return i, int(j[h[0]])
    return None


def spline(q):
    qz = np.vstack([q, q[:1]]); t = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(qz, axis=0), axis=1))])
    return CubicSpline(t, qz, bc_type="periodic"), t


def bearbeite(p, modus):
    m = p.mean(0); _, _, vt = np.linalg.svd(p - m); ansichten = [vt[[0, 2]], vt[[1, 2]]]
    keep = list(np.linspace(0, len(p), N_STUETZ, endpoint=False).astype(int)); schritte = []
    for _ in range(MAX_SCHRITTE):
        sp, t = spline(p[keep]); u = np.linspace(0, t[-1], NQ, endpoint=False); c = sp(u)
        k = None
        for A in ansichten:
            k = kreuzung((c - m) @ A.T)
            if k:
                break
        if k is None:
            return c, keep, schritte, True
        ta, tb = u[k[0]], u[k[1]]; innen = (t[:-1] > ta) & (t[:-1] < tb)
        if (tb - ta) > t[-1] / 2:
            innen = ~innen                                                # kürzere Schlaufe bearbeiten
        idx = np.nonzero(innen)[0]
        if modus == "ausduennen":
            weg = [i for n_, i in enumerate(idx) if n_ % 3 != 1]
            if len(idx) <= 1:
                weg = list(idx)
        else:
            weg = list(idx)
        anteil = min(tb - ta, t[-1] - (tb - ta)) / t[-1]
        schritte.append({"schlaufe_anteil": float(anteil), "weg": len(weg)})
        if not weg or len(keep) - len(weg) < MIN_STUETZ:
            return c, keep, schritte, False
        keep = [x for n_, x in enumerate(keep) if n_ not in set(weg)]
    sp, t = spline(p[keep]); return sp(np.linspace(0, t[-1], NQ, endpoint=False)), keep, schritte, False


def main(satz, aus):
    satz, aus = Path(satz), Path(aus); aus.mkdir(parents=True, exist_ok=True)
    basis, I, nfp = lade_satz(satz)
    s = flaeche(satz / "boundary.json")
    a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0))))); k = A_M / a
    roh = [bogen(c) for c in basis]
    erg = {"satz": str(satz), "original": {"Bn_mittel": feldfehler(basis, I, nfp, s)[0], "punkte_m": [(p * k).tolist() for p in roh]}, "modi": []}
    for modus in ("weglassen", "ausduennen"):
        res = [bearbeite(p, modus) for p in roh]
        kurven = [als_kurve(r[0]) for r in res]
        bm, bx = feldfehler([x[0] for x in kurven], I, nfp, s)
        abw = [float(np.max(np.min(np.linalg.norm(r[0][:, None] - p[None], axis=2), axis=1))) * k for r, p in zip(res, roh)]
        e = {"modus": modus, "Bn_mittel": bm, "Bn_max": bx, "abweichung_max_m": abw, "frei": [r[3] for r in res],
             "stuetzpunkte": [len(r[1]) for r in res], "schritte": [r[2] for r in res],
             "spulen": [baubarkeit(x[0], k) for x in kurven], "punkte_m": [(r[0] * k).tolist() for r in res],
             "stuetz_m": [(p[r[1]] * k).tolist() for r, p in zip(res, roh)]}
        erg["modi"].append(e)
        print(json.dumps({kk: v for kk, v in e.items() if kk not in ("punkte_m", "stuetz_m")}), flush=True)
    (aus / "schlaufe.json").write_text(json.dumps(erg))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
