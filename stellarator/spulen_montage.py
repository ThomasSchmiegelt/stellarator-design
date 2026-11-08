"""Bau- und Montagekriterien des Nutzers (2026-11-08) für einen Spulensatz:
  1. Biegeradius >= 2 d (d = Rohrdurchmesser, Annahme 0,85 m wie k3_rohr -> R_min >= 1,7 m)
  2. Bahnen überlappen nicht, geprüft in der Abwicklung: toroidaler Winkel phi über poloidalem Winkel theta um die Achse
     (Achse aus den m=0-Randkoeffizienten). Montagegerecht = jede Spule ist dort eine Linie phi(theta) ohne Rücklauf
     (läuft einmal um, faltet nicht zurück) und liegt ganz zwischen ihren Nachbarn (Abstand in phi > 0 für jedes theta).
     a) ruecklauf: Zahl der Umkehrungen von theta entlang der Spule (0 = montagegerecht)
     b) nachbar_abstand_grad_min: kleinster phi-Abstand zur nächsten Spule über alle theta (< 0 = Bahnen kreuzen sich)
     Zusätzlich zur Info: Seiten-8 (achter_seite) und Winkelbreite.
Alle Spulen (über Symmetrie) werden nach dem Mittelwinkel sortiert, Nachbarn = aufeinanderfolgende.
Aufruf: python spulen_montage.py <name=satz_ordner> ...   (gibt je Satz eine JSON-Zeile aus)
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spulen_satz import flaeche, lade_satz, feldfehler  # noqa: E402
from spulen_glaetten import baubarkeit, A_M  # noqa: E402

D_ROHR = 0.85


def phi_bereich(g):
    mitte = np.arctan2(g[:, 1].mean(), g[:, 0].mean())
    ph = np.angle(np.exp(1j * (np.arctan2(g[:, 1], g[:, 0]) - mitte)))   # relativ zum Mittelwinkel, -pi..pi
    return mitte, mitte + ph.min(), mitte + ph.max()


def achse(boundary):
    b = json.loads(Path(boundary).read_text()); rc, zs = np.asarray(b["r_cos"]), np.asarray(b["z_sin"]); nt = rc.shape[1] // 2
    nfp = int(b["n_field_periods"])
    def f(ph):
        R = sum(rc[0, n + nt] * np.cos(-n * nfp * ph) for n in range(-nt, nt + 1))
        Z = sum(zs[0, n + nt] * np.sin(-n * nfp * ph) for n in range(-nt, nt + 1))
        return R, Z
    return f


def abwicklung(g, ax):
    ph = np.arctan2(g[:, 1], g[:, 0]); R = np.hypot(g[:, 0], g[:, 1]); Ra, Za = ax(ph)
    th = np.unwrap(np.arctan2(g[:, 2] - Za, R - Ra))
    umlauf = np.round((th[-1] - th[0]) / (2 * np.pi)) * 2 * np.pi          # einmal herum: +-2 pi
    d = np.diff(np.concatenate([th, [th[0] + umlauf]])); d = d[np.abs(d) > 1e-9]
    s = np.sign(d); ruecklauf = int(np.sum(s[1:] != s[:-1]) + (s[0] != s[-1])) // 2
    return ph, th, ruecklauf


def pruefe(ordner):
    from simsopt.field import Current, coils_via_symmetries
    basis, I, nfp = lade_satz(ordner)
    s = flaeche(Path(ordner) / "boundary.json")
    a = float(np.sqrt(abs(s.volume()) / (2 * np.pi ** 2 * float(s.get_rc(0, 0))))); k = A_M / a
    b = [baubarkeit(c, k) for c in basis]
    sp = coils_via_symmetries(basis, [Current(float(x)) for x in I], nfp, True)
    ax = achse(Path(ordner) / "boundary.json")
    kurven = []
    for c in sp:                                                          # fein abtasten (periodisch linear), 2048 Punkte
        g = c.curve.gamma(); u = np.linspace(0, len(g), 2048, endpoint=False); gz = np.vstack([g, g[:1]])
        kurven.append(np.column_stack([np.interp(u, np.arange(len(gz)), gz[:, j]) for j in range(3)]))
    ber = sorted(((phi_bereich(g), g) for g in kurven), key=lambda x: x[0][0])
    n = len(ber); breite = [np.degrees(h - l) for (_, l, h), _ in ber]
    tg = np.linspace(-np.pi, np.pi, 361); env = []; rl = []
    for (m, _, _), g in ber:
        ph, th, r = abwicklung(g, ax); rl.append(r)
        ph = m + np.angle(np.exp(1j * (ph - m))); thw = np.angle(np.exp(1j * th))
        lo, hi = np.full(len(tg), np.inf), np.full(len(tg), -np.inf)
        fach = np.clip(np.searchsorted(tg, thw), 0, len(tg) - 1)
        # Hülle je theta-Fach: kleinstes/größtes phi (Fäden zwischen Punkten über Feinabtastung abgedeckt)
        np.minimum.at(lo, fach, ph); np.maximum.at(hi, fach, ph)
        ok = np.isfinite(lo); lo = np.interp(tg, tg[ok], lo[ok]); hi = np.interp(tg, tg[ok], hi[ok])
        env.append((lo, hi))
    ueber = []
    for i in range(n):
        lo2, hi2 = env[(i + 1) % n]; lo1, hi1 = env[i]
        sh = 2 * np.pi if i == n - 1 else 0.0
        ueber.append(np.degrees(np.min(lo2 + sh - hi1)))
    return {"Bn_mittel": feldfehler(basis, I, nfp, s)[0], "n_spulen": n,
            "R_min_m": [round(x["biegeradius_min_m"], 2) for x in b], "R_min_durch_d": round(min(x["biegeradius_min_m"] for x in b) / D_ROHR, 2),
            "achter_seite": [x["achter_seite"] for x in b], "selbstabstand_min_m": round(min(x["selbstabstand_min_m"] for x in b), 2),
            "phi_breite_grad_max": round(max(breite), 1), "teilung_grad": round(360 / n, 1),
            "ruecklauf_max": max(rl), "spulen_mit_ruecklauf": int(sum(r > 0 for r in rl)),
            "nachbar_abstand_grad_min": round(min(ueber), 2), "nachbarpaare_kreuzend": int(sum(u < 0 for u in ueber))}


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        name, ordner = arg.split("=", 1)
        print(json.dumps({"satz": name, **pruefe(ordner)}), flush=True)
