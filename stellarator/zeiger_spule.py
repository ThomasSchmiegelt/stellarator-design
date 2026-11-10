"""zeiger_spule.py — Spulenform nach der Nutzeridee "Uhrzeiger" (2026-11-09, F-310).

Idee (Nutzer): Ein Mittelpunkt, durch ihn eine Achse. Ein Zeiger dreht sich wie ein Uhrzeiger um den Mittelpunkt
(Winkel t läuft genau einmal und nur in eine Richtung um), seine Länge r(t) ist veränderlich. Am Zeigerende sitzt eine
Linie parallel zur Achse mit veränderlicher Länge z(t). Der Endpunkt ist die neutrale Faser der Spule:

    lokal:  x = r(t) cos t,  y = r(t) sin t,  z = z(t),   r, z als Fourier-Reihen der Ordnung `order`
    global: Drehung (Quaternion, wie simsopt CurvePlanarFourier) + Verschiebung (Mittelpunkt)

Folge: In der Draufsicht entlang der eigenen Achse ist die Spule sternförmig (Winkel monoton, r > 0), kann sich dort also
nicht kreuzen (keine 8) und nicht zurücklaufen. z(t) = 0 ergibt genau die ebene Spule (CurvePlanarFourier).
Grenze: In SEITENansichten kann eine Wellung z(t) ab Ordnung 2 (Sattel) noch Kreuzungen der Projektion zeigen.

Freiheitsgrade: [rc0..rc_order, rs1..rs_order, zc0..zc_order, zs1..zs_order, q0, qi, qj, qk, X, Y, Z]
Umsetzung als simsopt JaxCurve (Ableitungen automatisch), Vorlage simsopt.geo.curveplanarfourier.jaxplanarcurve_pure.
"""
import numpy as np
import jax.numpy as jnp
from simsopt.geo.curve import JaxCurve


def _fourier(c, order, t):
    j = jnp.arange(1, order + 1)[:, None] * t[None, :]
    return c[0] + jnp.sum(c[1:order + 1, None] * jnp.cos(j) + c[order + 1:2 * order + 1, None] * jnp.sin(j), axis=0)


def zeiger_pure(dofs, quadpoints, order):
    m = 2 * order + 1
    rk, zk, q, c = dofs[:m], dofs[m:2 * m], dofs[2 * m:2 * m + 4], dofs[2 * m + 4:]
    q = q / (jnp.linalg.norm(q) + 1e-12)
    t = 2 * np.pi * quadpoints
    r = _fourier(rk, order, t); z = _fourier(zk, order, t)
    p = jnp.stack([r * jnp.cos(t), r * jnp.sin(t), z], axis=1)
    w, a, b, d = q
    R = jnp.array([[1 - 2 * (b * b + d * d), 2 * (a * b - d * w), 2 * (a * d + b * w)],
                   [2 * (a * b + d * w), 1 - 2 * (a * a + d * d), 2 * (b * d - a * w)],
                   [2 * (a * d - b * w), 2 * (b * d + a * w), 1 - 2 * (a * a + b * b)]])
    return p @ R.T + c[None, :]


class CurveZeiger(JaxCurve):
    def __init__(self, quadpoints, order, dofs=None):
        if isinstance(quadpoints, int):
            quadpoints = np.linspace(0, 1, quadpoints, endpoint=False)
        self.order = order
        n = 2 * (2 * order + 1) + 7
        self.dof_list = np.zeros(n); self.dof_list[2 * (2 * order + 1)] = 1.0
        names = ([f"rc({i})" for i in range(order + 1)] + [f"rs({i})" for i in range(1, order + 1)]
                 + [f"zc({i})" for i in range(order + 1)] + [f"zs({i})" for i in range(1, order + 1)]
                 + ["q0", "qi", "qj", "qk", "X", "Y", "Z"])
        kw = dict(names=names, external_dof_setter=CurveZeiger.set_dofs_impl)
        if dofs is None:
            super().__init__(quadpoints, lambda x, p: zeiger_pure(x, p, order), x0=self.dof_list, **kw)
        else:
            super().__init__(quadpoints, lambda x, p: zeiger_pure(x, p, order), dofs=dofs, **kw)

    def num_dofs(self):
        return 2 * (2 * self.order + 1) + 7

    def get_dofs(self):
        return np.array(self.dof_list)

    def set_dofs_impl(self, dofs):
        self.dof_list = np.array(dofs)


def aus_kurve(kurve, order, nq=128):
    """Zeigerspule aus einer beliebigen Startkurve: Achse = Normale der besten Ebene, Mittelpunkt = Schwerpunkt,
    r(t) und z(t) als kleinste Quadrate über dem Zeigerwinkel t (Startkurve muss in der Draufsicht sternförmig sein)."""
    g = kurve.gamma(); m = g.mean(0); _, _, vt = np.linalg.svd(g - m)
    e1, e3 = vt[0], vt[2]; e2 = np.cross(e3, e1); R = np.column_stack([e1, e2, e3])
    w = np.sqrt(max(1e-12, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    q = [w, (R[2, 1] - R[1, 2]) / (4 * w), (R[0, 2] - R[2, 0]) / (4 * w), (R[1, 0] - R[0, 1]) / (4 * w)]
    lok = (g - m) @ R; t = np.arctan2(lok[:, 1], lok[:, 0]); r = np.hypot(lok[:, 0], lok[:, 1])
    M = np.column_stack([np.ones_like(t)] + [np.cos(k * t) for k in range(1, order + 1)] + [np.sin(k * t) for k in range(1, order + 1)])
    kr = np.linalg.lstsq(M, r, rcond=None)[0]; kz = np.linalg.lstsq(M, lok[:, 2], rcond=None)[0]
    c = CurveZeiger(np.linspace(0, 1, nq, endpoint=False), order)
    c.x = np.concatenate([kr, kz, q, m])
    return c


def nach_xyz(c, nq=128):
    """Zeigerspule als CurveXYZFourier (Ordnung order + 1, r·cos t hat Ordnung order + 1) für Export und Prüfwerkzeuge."""
    from simsopt.geo import CurveXYZFourier
    o = c.order + 1; t = np.linspace(0, 1, nq, endpoint=False); g = c.gamma()
    M = [np.ones_like(t)]
    for k in range(1, o + 1):
        M += [np.sin(2 * np.pi * k * t), np.cos(2 * np.pi * k * t)]
    M = np.array(M).T
    x = CurveXYZFourier(nq, o); x.x = np.concatenate([np.linalg.lstsq(M, g[:, j], rcond=None)[0] for j in range(3)])
    return x


def zeiger_pruefung(c, n=2048):
    """Garantie nachprüfen: Zeigerlänge r(t) > 0 überall (dann sternförmig, keine 8 in der Draufsicht)."""
    m = 2 * c.order + 1; t = np.linspace(0, 2 * np.pi, n, endpoint=False); k = np.asarray(c.x[:m])
    r = k[0] + sum(k[i] * np.cos(i * t) + k[c.order + i] * np.sin(i * t) for i in range(1, c.order + 1))
    return float(r.min())


if __name__ == "__main__":                    # Selbsttest: z = 0 muss CurvePlanarFourier exakt treffen, Ableitung gegen Differenz
    from simsopt.geo import CurvePlanarFourier
    o = 3; rng = np.random.default_rng(1)
    p = CurvePlanarFourier(64, o); xp = np.concatenate([[1.0], rng.normal(0, .1, 2 * o), [0.9, 0.2, -0.3, 0.1], [2, 1, .5]]); p.x = xp
    z = CurveZeiger(64, o); z.x = np.concatenate([xp[:2 * o + 1], np.zeros(2 * o + 1), xp[2 * o + 1:]])
    print("eben = CurvePlanarFourier:", float(np.abs(p.gamma() - z.gamma()).max()))
    x = z.x.copy(); x[2 * o + 1:4 * o + 2] = rng.normal(0, .1, 2 * o + 1); z.x = x
    from simsopt.geo import CurveLength
    J = CurveLength(z); d = rng.normal(size=x.size); e = 1e-6
    z.x = x + e * d; jp = J.J(); z.x = x - e * d; jm = J.J(); z.x = x
    print("Ableitung Laenge: rechnet", float(J.dJ() @ d), "Differenz", (jp - jm) / (2 * e))
    print("r_min", zeiger_pruefung(z))
