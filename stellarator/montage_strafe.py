"""Montagestrafe für Stage 2 (Nutzerregel 2026-11-08: Bahnen dürfen sich nicht überlappen).

Rücklauf: Eine montagegerechte Spule läuft in der Abwicklung (poloidaler Winkel theta um die Plasmaachse) einmal herum,
ohne zurückzulaufen. Strafe je Grundspule: P = sum_i max(0, eps - s * dtheta_i)^2, s = Umlaufrichtung,
eps = Mindestfortschritt je Kurvenpunkt (Anteil am mittleren Schritt 2 pi / nq). P = 0 heißt kein Rücklauf mit Reserve.
Achse aus den m=0-Randkoeffizienten (wie spulen_montage.achse). Ableitung mit jax, Rückführung über dgamma_by_dcoeff_vjp.
"""
import json

import numpy as np
import jax
import jax.numpy as jnp
from simsopt._core.optimizable import Optimizable
from simsopt._core.derivative import derivative_dec

jax.config.update("jax_enable_x64", True)


def achse_koef(boundary):
    b = json.loads(open(boundary).read()); rc = np.asarray(b["r_cos"]); zs = np.asarray(b["z_sin"]); nt = rc.shape[1] // 2
    return rc[0].copy(), zs[0].copy(), np.arange(-nt, nt + 1), int(b["n_field_periods"])


def _theta(g, rc0, zs0, n, nfp):
    ph = jnp.arctan2(g[:, 1], g[:, 0]); R = jnp.sqrt(g[:, 0] ** 2 + g[:, 1] ** 2)
    arg = -n[None, :] * nfp * ph[:, None]
    Ra = jnp.sum(rc0[None, :] * jnp.cos(arg), 1); Za = jnp.sum(zs0[None, :] * jnp.sin(arg), 1)
    return jnp.arctan2(g[:, 2] - Za, R - Ra)


def _schritte(g, rc0, zs0, n, nfp):
    th = _theta(g, rc0, zs0, n, nfp)
    d = jnp.diff(jnp.concatenate([th, th[:1]]))
    return (d + jnp.pi) % (2 * jnp.pi) - jnp.pi


def ruecklauf_zahl(gamma, boundary):
    """Zahl der Umkehrungen (wie spulen_montage, aber auf den Kurvenpunkten): 0 = montagegerecht."""
    rc0, zs0, n, nfp = achse_koef(boundary)
    d = np.asarray(_schritte(jnp.asarray(gamma), jnp.asarray(rc0), jnp.asarray(zs0), jnp.asarray(n), nfp))
    d = d[np.abs(d) > 1e-12]; s = np.sign(d)
    return int(np.sum(s[1:] != s[:-1]) + (s[0] != s[-1])) // 2


class RuecklaufStrafe(Optimizable):
    def __init__(self, curve, boundary, eps_anteil=0.2):
        self.curve = curve
        rc0, zs0, n, nfp = achse_koef(boundary); eps = eps_anteil * 2 * np.pi / len(curve.quadpoints)
        rc0, zs0, n = jnp.asarray(rc0), jnp.asarray(zs0), jnp.asarray(n)

        def f(g):
            d = _schritte(g, rc0, zs0, n, nfp)
            s = jax.lax.stop_gradient(jnp.sign(jnp.sum(d)))
            return jnp.sum(jnp.maximum(0.0, eps - s * d) ** 2)
        self._J = jax.jit(f); self._dJ = jax.jit(jax.grad(f))
        Optimizable.__init__(self, depends_on=[curve])

    def J(self):
        return float(self._J(jnp.asarray(self.curve.gamma())))

    @derivative_dec
    def dJ(self):
        return self.curve.dgamma_by_dcoeff_vjp(np.asarray(self._dJ(jnp.asarray(self.curve.gamma()))))

    return_fn_map = {"J": J, "dJ": dJ}
