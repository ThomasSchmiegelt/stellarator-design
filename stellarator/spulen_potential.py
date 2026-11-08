"""Erst die perfekte Bahn, dann Spulen (Nutzeridee 2026-11-08), nach dem REGCOIL-Prinzip (Landreman 2017), eigene Umsetzung:

1. Wickelfläche = Plasmarand um dist nach außen versetzt (simsopt extend_via_normal), ganzer Torus.
2. Stromfunktion Phi(theta, phi) = G*phi + sum s_mn sin(m theta - n nfp phi)  (stellaratorsymmetrisch),
   Flächenstrom K = n x grad Phi. G = gesamter poloidaler Strom (aus dem Vergleichssatz, Summe der Spulenströme).
   s_mn aus kleinsten Quadraten: Normalfeld auf dem Plasma (halbe Periode) + lambda * Flächenstromquadrat (Glätte).
3. Spulen = Höhenlinien von Phi bei G*(k+0.5)/N. Höhenlinien kreuzen sich nie. Ist dPhi/dphi > 0 überall, ist jede
   Höhenlinie eine Funktion phi(theta): einmal herum, kein Rücklauf -> montagegerecht per Konstruktion.
4. Grundspulen (erste halbe Periode) als CurveXYZFourier Ordnung 7 -> satz-Ordner (spulen.json + boundary.json),
   prüfbar mit spulen_satz.pruefe / spulen_montage, Warmstart für k3_spulen (_v).

Aufruf: python spulen_potential.py <boundary.json> <vergleichssatz_ordner> <aus_ordner> <n_je_halbperiode> [dist_in_a]
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import flaeche, lade_satz, feldfehler  # noqa: E402

MPOL, NTOR = 10, 10
ORD = int(os.environ.get("POT_ORD", "16"))


def basis_mn():
    return [(m, n) for m in range(MPOL + 1) for n in range(-NTOR, NTOR + 1) if not (m == 0 and n <= 0)]


def wickelflaeche(boundary, dist, nfp, mpol=int(os.environ.get("WS_MN", "12")), ntor=int(os.environ.get("WS_MN", "12"))):
    """Plasmarand um dist entlang der AUSSEN-Normale versetzen und als SurfaceRZFourier (mpol, ntor) anpassen.
    (extend_via_normal ging hier nach innen: Normale der Randfläche zeigt nach innen, und Ordnung 4 war zu grob.)"""
    from simsopt.geo import SurfaceRZFourier
    from scipy.spatial import cKDTree
    s0 = flaeche(boundary, nphi=48 * nfp, ntheta=64, voll=True)
    g0 = s0.gamma(); n0 = s0.unitnormal()
    if np.mean(np.sum((g0 - g0.reshape(-1, 3).mean(0)) * n0, axis=2)) < 0:
        n0 = -n0
    ziel = g0 + dist * n0
    ws = SurfaceRZFourier(nfp=nfp, stellsym=True, mpol=mpol, ntor=ntor, quadpoints_phi=s0.quadpoints_phi, quadpoints_theta=s0.quadpoints_theta)
    ws.least_squares_fit(ziel)
    d = cKDTree(g0.reshape(-1, 3)).query(ws.gamma().reshape(-1, 3))[0]
    print(json.dumps({"wickelflaeche_abstand_min_rel": float(d.min() / dist), "max_rel": float(d.max() / dist),
                      "anpassfehler_rel": float(np.abs(ws.gamma() - ziel).max() / dist)}), flush=True)
    return ws


def main(boundary, vergleich, aus, n, dist_a=1.1):
    aus = Path(aus); aus.mkdir(parents=True, exist_ok=True)
    nfp = int(json.loads(Path(boundary).read_text())["n_field_periods"])
    s_p = flaeche(boundary, nphi=32, ntheta=32, voll=False)
    a = float(np.sqrt(abs(s_p.volume()) / (2 * np.pi ** 2 * float(s_p.get_rc(0, 0)))))
    ws = wickelflaeche(boundary, dist_a * a, nfp)
    r = ws.gamma().reshape(-1, 3); rp = ws.gammadash1().reshape(-1, 3); rt = ws.gammadash2().reshape(-1, 3)
    Nn = np.linalg.norm(np.cross(rp, rt), axis=1); nb = len(r); dw = 1.0 / nb
    ph = np.repeat(ws.quadpoints_phi, len(ws.quadpoints_theta)); th = np.tile(ws.quadpoints_theta, len(ws.quadpoints_phi))
    mn = basis_mn(); J = len(mn)
    Kj = np.empty((J, nb, 3))
    for j, (m, nn) in enumerate(mn):
        c = np.cos(2 * np.pi * (m * th - nn * nfp * ph))
        Kj[j] = (-2 * np.pi * nn * nfp * c)[:, None] * rt - (2 * np.pi * m * c)[:, None] * rp
    _, I0, _ = lade_satz(vergleich); G = float(np.abs(I0).sum() * 2 * nfp)
    KG = G * rt
    x = s_p.gamma().reshape(-1, 3); nx = s_p.unitnormal().reshape(-1, 3)
    wa = np.linalg.norm(s_p.normal().reshape(-1, 3), axis=1); wa = wa / wa.sum()
    A = np.zeros((len(x), J)); bG = np.zeros(len(x)); BG = np.zeros((len(x), 3))
    Kf = Kj.reshape(J, -1); KGf = KG.reshape(-1)
    for i0 in range(0, len(x), 64):
        R = x[i0:i0 + 64, None, :] - r[None]; d3 = np.linalg.norm(R, axis=2) ** 3
        W = np.cross(R, nx[i0:i0 + 64, None, :]) / d3[..., None] * 1e-7 * dw
        Wf = W.reshape(W.shape[0], -1); A[i0:i0 + 64] = Wf @ Kf.T; bG[i0:i0 + 64] = Wf @ KGf
        BG[i0:i0 + 64] = 1e-7 * dw * np.sum(np.cross(KG[None], R) / d3[..., None], axis=1)
    Kr = Kf.reshape(J, nb, 3) * np.sqrt(dw / Nn)[None, :, None]; KGr = KG * np.sqrt(dw / Nn)[:, None]
    AtA = A.T @ (wa[:, None] * A); Atb = A.T @ (wa * bG)
    RtR = Kr.reshape(J, -1) @ Kr.reshape(J, -1).T; Rtb = Kr.reshape(J, -1) @ KGr.reshape(-1)
    skala = np.trace(AtA) / np.trace(RtR)
    erg = {"boundary": str(boundary), "G": G, "dist_a": dist_a, "n_je_halbperiode": n, "laeufe": []}
    tg = np.linspace(0, 1, 256, endpoint=False); pg = np.linspace(-0.5, 1.5, 8193)
    T, P = np.meshgrid(tg, pg, indexing="ij")
    from simsopt.geo import CurveXYZFourier
    from spulen_montage import pruefe as montage
    for lam in [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1]:
        sv = np.linalg.solve(AtA + lam * skala * RtR, -(Atb + lam * skala * Rtb))
        bn = bG + A @ sv
        Phi = G * P + sum(sv[j] * np.sin(2 * np.pi * (m * T - nn * nfp * P)) for j, (m, nn) in enumerate(mn))
        dPhi = G + sum(sv[j] * (-2 * np.pi * nn * nfp) * np.cos(2 * np.pi * (m * T - nn * nfp * P)) for j, (m, nn) in enumerate(mn))
        rand = float(dPhi.min() / G)
        zeile = {"lambda": lam, "Bn_rel_flaechenstrom": float(np.sum(wa * np.abs(bn)) / np.sum(wa * np.linalg.norm(BG, axis=1))),
                 "dPhi_dphi_min_rel": rand}
        if rand > 0:
            basis = []
            for k in range(n):
                c = G * (k + 0.5) / (2 * nfp * n)
                phk = np.array([np.interp(c, Phi[i], pg) for i in range(len(tg))])
                Rr = sum(ws.get_rc(m, nn) * np.cos(2 * np.pi * (m * tg - nn * nfp * phk)) for m in range(ws.mpol + 1) for nn in range(-ws.ntor, ws.ntor + 1) if not (m == 0 and nn < 0))
                Zz = sum(ws.get_zs(m, nn) * np.sin(2 * np.pi * (m * tg - nn * nfp * phk)) for m in range(ws.mpol + 1) for nn in range(-ws.ntor, ws.ntor + 1) if not (m == 0 and nn < 0))
                g = np.column_stack([Rr * np.cos(2 * np.pi * phk), Rr * np.sin(2 * np.pi * phk), Zz])
                M = [np.ones_like(tg)]
                for o in range(1, ORD + 1):
                    M += [np.sin(2 * np.pi * o * tg), np.cos(2 * np.pi * o * tg)]
                M = np.array(M).T
                cu = CurveXYZFourier(128, ORD); cu.x = np.concatenate([np.linalg.lstsq(M, g[:, q], rcond=None)[0] for q in range(3)])
                zeile.setdefault("fit_max_a", 0.0)
                gu = CurveXYZFourier(256, ORD); gu.x = cu.x
                zeile["fit_max_a"] = max(zeile["fit_max_a"], float(np.abs(gu.gamma() - g).max()) / a)
                basis.append(cu)
            I = [G / (2 * nfp * n)] * n
            o = aus / f"lam{lam:.0e}"; o.mkdir(exist_ok=True)
            (o / "spulen.json").write_text(json.dumps({"format": "simsopt_basis", "nfp": nfp, "stellsym": True, "order": ORD, "nq": 128,
                "basis_x": [c.x.tolist() for c in basis], "currents": I, "faktor": 1.0, "quelle": "spulen_potential (Höhenlinien)"}, indent=1))
            (o / "boundary.json").write_text(Path(boundary).read_text())
            # Gegenprobe: Feld der Flächenstromschicht gegen Feld der geschnittenen Spulen an den Plasmapunkten
            Kt = KG + np.tensordot(sv, Kj, axes=1); BF = np.zeros_like(x)
            for i0 in range(0, len(x), 64):
                R = x[i0:i0 + 64, None, :] - r[None]; d3 = np.linalg.norm(R, axis=2) ** 3
                BF[i0:i0 + 64] = 1e-7 * dw * np.sum(np.cross(Kt[None], R) / d3[..., None], axis=1)
            from simsopt.field import BiotSavart, Current, coils_via_symmetries
            bs = BiotSavart(coils_via_symmetries(basis, [Current(i) for i in I], nfp, True)); bs.set_points(x)
            BC = bs.B()
            zeile["Bn_rel_FS_voll"] = float(np.sum(wa * np.abs(np.sum(BF * nx, 1)) / np.linalg.norm(BF, axis=1)))
            zeile["Bn_rel_spulen_hier"] = float(np.sum(wa * np.abs(np.sum(BC * nx, 1)) / np.linalg.norm(BC, axis=1)))
            zeile["B_spulen_durch_FS"] = float(np.median(np.linalg.norm(BC, axis=1) / np.linalg.norm(BF, axis=1)))
            zeile["winkel_BC_BF_grad_median"] = float(np.degrees(np.median(np.arccos(np.clip(np.sum(BC * BF, 1) / np.linalg.norm(BC, axis=1) / np.linalg.norm(BF, axis=1), -1, 1)))))
            zeile.update(montage(o))
        erg["laeufe"].append(zeile); print(json.dumps(zeile), flush=True)
    (aus / "potential.json").write_text(json.dumps(erg, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), float(sys.argv[5]) if len(sys.argv) > 5 else 1.1)
