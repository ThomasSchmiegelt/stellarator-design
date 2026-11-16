"""Kreuzungsstrafe fuer Stage 2 (Nutzerregel: Bahnen duerfen sich in der Abwicklung nicht ueberlappen).  KI-generiert (Claude Sonnet 5.5, 2026-11-13).

Abwicklung wie spulen_montage.py: theta um die Plasmaachse (m=0-Randkoeffizienten), phi toroidal. Alle Spulen (ueber Symmetrie)
werden nach dem Mittelwinkel sortiert (fest beim Erzeugen), Nachbarn = aufeinanderfolgende (letzte -> erste um 2 pi versetzt).
Fuer jedes Paar: Abstand D(theta) = phi_rechts(theta) - phi_links(theta) auf einem theta-Raster (NT Punkte, periodisch interpoliert).
Strafe P = sum max(0, eps - D)^2, eps = 2 Grad (ANNAHME). Ableitung mit jax, Rueckfuehrung ueber dgamma_by_dcoeff_vjp.
Eingabe: Liste aller Kurven (Symmetrie-Kopien), die von den Basiskurven abhaengen.
"""
import json
import numpy as np
import jax
import jax.numpy as jnp
from simsopt._core.optimizable import Optimizable
from simsopt._core.derivative import derivative_dec

from stellarator.montage_strafe import achse_koef, _theta

jax.config.update("jax_enable_x64", True)
EPS_GRAD = 2.0
NT = 64


def _phi_von_theta(g, mid, rc0, zs0, n, nfp, tg):
    """phi(theta) einer Kurve auf dem Raster tg (absolut = mid + relativ), periodisch linear interpoliert."""
    th = _theta(g, rc0, zs0, n, nfp)
    d = (jnp.diff(jnp.concatenate([th, th[:1]])) + jnp.pi) % (2 * jnp.pi) - jnp.pi
    s = jax.lax.stop_gradient(jnp.sign(jnp.sum(d)))
    thu = th[0] + jnp.concatenate([jnp.zeros(1), jnp.cumsum(d[:-1])])
    ph = jnp.arctan2(g[:, 1], g[:, 0]); rel = (ph - mid + jnp.pi) % (2 * jnp.pi) - jnp.pi
    xp = s * thu
    xpe = jnp.concatenate([xp - 2 * jnp.pi, xp, xp + 2 * jnp.pi]); fpe = jnp.concatenate([rel, rel, rel])
    if True:                                              # absteigendes xp (s<0 hat xp aufsteigend wegen s*thu); Reihenfolge sichern
        o = jnp.argsort(xpe); xpe, fpe = xpe[o], fpe[o]
    return mid + jnp.interp(s * tg, xpe, fpe)


class KreuzungStrafe(Optimizable):
    def __init__(self, kurven, boundary, eps_grad=EPS_GRAD, nt=NT):
        self.kurven = list(kurven)
        rc0, zs0, n, nfp = achse_koef(boundary); rc0, zs0, n = jnp.asarray(rc0), jnp.asarray(zs0), jnp.asarray(n)
        g0 = [np.asarray(c.gamma()) for c in self.kurven]
        mid = np.array([np.arctan2(g[:, 1].mean(), g[:, 0].mean()) for g in g0])
        self.ordnung = list(np.argsort(mid)); mids = mid[self.ordnung]
        tg = jnp.asarray(np.linspace(-np.pi, np.pi, nt, endpoint=False)); eps = np.radians(eps_grad)
        N = len(g0); idx = self.ordnung; mj = jnp.asarray(mids)

        def f(gs):                                         # gs: (N, nq, 3) in Reihenfolge der Kurvenliste
            ph = jnp.stack([_phi_von_theta(gs[idx[i]], mj[i], rc0, zs0, n, nfp, tg) for i in range(N)])
            P = 0.0
            for i in range(N):
                j = (i + 1) % N; sh = 2 * jnp.pi if i == N - 1 else 0.0
                P = P + jnp.sum(jnp.maximum(0.0, eps - (ph[j] + sh - ph[i])) ** 2)
            return P
        self._f = jax.jit(f); self._df = jax.jit(jax.grad(f))
        Optimizable.__init__(self, depends_on=self.kurven)

    def _g(self):
        return jnp.asarray(np.stack([np.asarray(c.gamma()) for c in self.kurven]))

    def J(self):
        return float(self._f(self._g()))

    @derivative_dec
    def dJ(self):
        dg = np.asarray(self._df(self._g()))
        out = None
        for c, d in zip(self.kurven, dg):
            v = c.dgamma_by_dcoeff_vjp(d)
            out = v if out is None else out + v
        return out

    return_fn_map = {"J": J, "dJ": dJ}
