"""Strafe auf das Stromverhaeltnis I_max/I_mittel der Basisspulen (K2e).  KI-generiert (Claude Sonnet 5.5, 2026-11-13).
J = sum_i max(0, |I_i|/mean|I| - q)^2 ueber die Basisstroeme (simsopt-Current-Objekte, x = I/1e5). Nur mit Option _i<q*100> in k3_spulen aktiv."""
import numpy as np
from simsopt._core.optimizable import Optimizable
from simsopt._core.derivative import Derivative, derivative_dec


class StromVerhaeltnis(Optimizable):
    def __init__(self, ströme, q):
        self.cur = list(ströme); self.q = float(q)
        Optimizable.__init__(self, depends_on=self.cur)

    def _I(self):
        return np.array([abs(float(c.get_value())) for c in self.cur])

    def verhaeltnis(self):
        I = self._I(); return float(I.max() / I.mean())

    def J(self):
        I = self._I(); r = I / I.mean()
        return float(np.sum(np.maximum(0.0, r - self.q) ** 2))

    @derivative_dec
    def dJ(self):
        I = self._I(); m = I.mean(); n = len(I); r = I / m; v = np.maximum(0.0, r - self.q)
        # dJ/dI_k = 2 v_k / m - 2 sum_j v_j I_j / (n m^2)
        g = 2 * v / m - 2 * np.sum(v * I) / (n * m * m)
        sg = np.array([np.sign(float(c.get_value())) or 1.0 for c in self.cur])
        return Derivative({c: np.array([g[k] * sg[k]]) for k, c in enumerate(self.cur)})

    return_fn_map = {"J": J, "dJ": dJ}
