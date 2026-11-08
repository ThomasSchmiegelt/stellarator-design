"""Spulen nach der Berechnung glätten (Nutzeridee F-296) und Baubarkeit messen.

Glätten = Fourier-Ordnung der Spulenkurven kappen (Tiefpass): Ordnung 7 (Original) -> 6, 5, 4, 3, 2.
Je Stufe: Feldfehler (wie pruefung_satz) und Baubarkeitswerte je Grundspule:
  - kleinster Biegeradius (1/Krümmung max), m
  - größte Verdrillung (Torsion), 1/m
  - Achter: Selbstkreuzungen der Spule in der Ansicht auf ihre beste Ebene (eine "8" = 1 Kreuzung)
  - Achter Seite: größte Zahl Selbstkreuzungen in den beiden Seitenansichten (Spule in sich verdreht, wie eine 8 von der Seite)
  - Abweichung aus der besten Ebene (Höhe der Spule senkrecht zur Ebene), m
  - kleinster Abstand der Spule zu sich selbst (Punkte mehr als 15 % Umfang auseinander), m
Längen in Metern über a_m = 1,8 m (Annahme wie k3_rohr / Modelle).

Aufruf: python spulen_glaetten.py <satz_ordner> <aus_ordner>
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import feldfehler, flaeche, lade_satz  # noqa: E402

A_M = 1.8


def kappen(x, order, neu):
    """CurveXYZFourier-dofs je Richtung: c0, s1, c1, s2, c2, ... -> nur bis Ordnung neu behalten."""
    x = np.asarray(x, float).reshape(3, 2 * order + 1).copy()
    x[:, 2 * neu + 1:] = 0.0
    return x.ravel()


def kreuzungen_2d(p):
    """Zahl der Selbstkreuzungen eines geschlossenen 2D-Polygons (Segmentpaare, nicht benachbart)."""
    a, b = p, np.roll(p, -1, 0); n = len(p); z = 0
    for i in range(n):
        j = np.arange(i + 2, n if i > 0 else n - 1)
        if len(j) == 0:
            continue
        p1, p2, q1, q2 = a[i], b[i], a[j], b[j]
        d = lambda u, v, w: (v[..., 0] - u[..., 0]) * (w[..., 1] - u[..., 1]) - (v[..., 1] - u[..., 1]) * (w[..., 0] - u[..., 0])
        s1 = d(p1, p2, q1) * d(p1, p2, q2); s2 = d(q1, q2, p1) * d(q1, q2, p2)
        z += int(np.sum((s1 < 0) & (s2 < 0)))
    return z


def baubarkeit(c, m_je_e):
    from simsopt.geo import CurveXYZFourier
    f = CurveXYZFourier(512, c.order); f.x = c.x
    g = f.gamma() * m_je_e
    k = f.kappa() / m_je_e; t = np.abs(f.torsion()) / m_je_e
    mitte = g.mean(0); u, s, vt = np.linalg.svd(g - mitte); n = vt[2]
    hoehe = (g - mitte) @ n; p2 = (g - mitte) @ vt[:2].T
    ds = np.linalg.norm(np.roll(g, -1, 0) - g, axis=1); L = ds.sum(); bogen = np.cumsum(ds)
    D = np.linalg.norm(g[:, None] - g[None], axis=2)
    db = np.abs(bogen[:, None] - bogen[None]); db = np.minimum(db, L - db)
    selbst = float(D[db > 0.15 * L].min())
    eben = (hoehe.max() - hoehe.min()) < 0.01 * np.ptp(p2[:, 0])         # ebene Spule: Seitenansicht ist eine Linie, keine Kreuzung
    seite = [0, 0] if eben else [kreuzungen_2d(((g - mitte) @ vt[[i, 2]].T)[::2]) for i in (0, 1)]
    return {"laenge_m": float(L), "biegeradius_min_m": float(1 / k.max()), "torsion_max_1_m": float(t.max()),
            "achter": kreuzungen_2d(p2[::2]), "achter_seite": max(seite), "aus_ebene_m": float(hoehe.max() - hoehe.min()), "selbstabstand_min_m": selbst}


def main(satz, aus):
    satz, aus = Path(satz), Path(aus); aus.mkdir(parents=True, exist_ok=True)
    basis, I, nfp = lade_satz(satz)
    s = flaeche(satz / "boundary.json")
    a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0))))); m_je_e = A_M / a
    order = basis[0].order; x0 = [np.asarray(c.x).copy() for c in basis]
    erg = {"satz": str(satz), "a_m": A_M, "m_je_einheit": m_je_e, "stufen": []}
    for neu in range(order, 1, -1):
        for c, x in zip(basis, x0):
            c.x = kappen(x, order, neu)
        bm, bx = feldfehler(basis, I, nfp, s)
        e = {"ordnung": neu, "Bn_mittel": bm, "Bn_max": bx, "spulen": [baubarkeit(c, m_je_e) for c in basis],
             "punkte_m": [(c.gamma() * m_je_e).tolist() for c in basis]}
        erg["stufen"].append(e)
        print(json.dumps({k: v for k, v in e.items() if k != "punkte_m"}), flush=True)
    for c, x in zip(basis, x0):
        c.x = x
    (aus / "glaettung.json").write_text(json.dumps(erg))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
