"""stroemung_animation.py — Teilchenbahnen durch das FluidX3D-Feld eines Kuehlsegments fuer eine Blender-Animation.

    .venv/bin/python -m stellarator.stroemung_animation --name f6 [--teilchen 20000] [--bilder 360] [--dt_bild 0.1]

Das stationaere Endfeld (feld_*.bin) wird auf das Gitter gelegt; Teilchen werden mit RK2 (Zellwert, Zwischenschritte
<= 1 Zelle) mitgefuehrt. Je Teilchen ein kurzer Schweif (letzte Positionen). Teilchen, die das Wasser verlassen,
im Austrittsrohr ankommen oder stehen bleiben, starten neu: ein Teil im Eintrittsrohr, der Rest verteilt im Wasser.
Ausgabe <segment>/animation/bild_0000.npz (Schweif-Punkte xyz [m], Geschwindigkeit [m/s]) + info.json.
Gezeigt werden nur Teilchen unterhalb der Schnitthoehe z_schnitt (die obere Haelfte ist im Bild weggeschnitten).
"""
import argparse, json
from pathlib import Path
import numpy as np
from .kuehlung_cfd import lese_feld
from .kuehlung_segment import WURZEL


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="f6")
    ap.add_argument("--teilchen", type=int, default=20000)
    ap.add_argument("--bilder", type=int, default=360)
    ap.add_argument("--dt_bild", type=float, default=0.1, help="physikalische Zeit je Bild [s]")
    ap.add_argument("--schweif", type=int, default=6, help="Positionen je Schweif")
    ap.add_argument("--anteil_einlass", type=float, default=0.3, help="Anteil der Neustarts im Eintrittsrohr")
    ap.add_argument("--z_schnitt", type=float, default=0.0, help="Schnitthoehe [m]")
    ap.add_argument("--vorlauf", type=int, default=60, help="Bilder vorab rechnen (Einschwingen), nicht gespeichert")
    a = ap.parse_args(argv)
    o = WURZEL / a.name; aus = o / "animation"; aus.mkdir(exist_ok=True)
    for p in aus.glob("bild_*.npz"):
        p.unlink()
    F = lese_feld(o); f = F["fall"]; dx = f["dx_m"]; x0 = np.array(f["ursprung_m"]); N = tuple(f["N"])
    ijk = F["ijk"]
    U = np.zeros(N + (3,), np.float16); U[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = F["u"]
    W = np.zeros(N, bool); W[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = True
    lage = json.loads((o / "auslegung.json").read_text())["lage"]["rohre"]
    rng = np.random.default_rng(1)
    xw = F["x"]; del F

    # Startorte: Eintrittsrohr = Wasserzellen nahe der Rohrachse im ausseren Rohrstueck
    e_ein = np.array(lage["ein"]["achse"]); p_end = np.array(lage["ein"]["ende_m"])
    t = (xw - p_end) @ e_ein                                      # < 0: ins Bauteil hinein
    r = np.linalg.norm((xw - p_end) - t[:, None] * e_ein, axis=1)
    im_einlass = np.where((t > -0.35) & (t < -0.15) & (r < lage["ein"]["d_mm"] / 2000))[0]
    e_aus = np.array(lage["aus"]["achse"]); q_aus = np.array(lage["aus"]["ende_m"])

    def neu(n):
        k = rng.random(n) < a.anteil_einlass
        i = np.where(k, rng.choice(im_einlass, n), rng.integers(0, len(xw), n))
        return xw[i] + (rng.random((n, 3)) - 0.5) * dx

    def geschw(p):
        g = np.floor((p - x0) / dx + 0.5).astype(np.int64)
        ok = np.all((g >= 0) & (g < np.array(N)), axis=1)
        g = np.clip(g, 0, np.array(N) - 1)
        ok &= W[g[:, 0], g[:, 1], g[:, 2]]
        return U[g[:, 0], g[:, 1], g[:, 2]].astype(np.float32), ok

    P = neu(a.teilchen); S = np.repeat(P[:, None], a.schweif, 1); ruhe = np.zeros(a.teilchen, int)
    v_max = float(np.linalg.norm(U.reshape(-1, 3)[::97].astype(np.float32), axis=1).max())
    n_sub = max(1, int(np.ceil(v_max * a.dt_bild / dx)))
    h = a.dt_bild / n_sub
    print(f"Gitter {N}, Wasserzellen {len(xw)}, v_max ~{v_max:.2f} m/s, {n_sub} Zwischenschritte je Bild", flush=True)
    for b in range(-a.vorlauf, a.bilder):
        for _ in range(n_sub):
            v1, ok1 = geschw(P)
            v2, ok2 = geschw(P + 0.5 * h * v1)
            P = np.where((ok1 & ok2)[:, None], P + h * v2, P)
            weg = ~(ok1 & ok2)
            weg |= ((P - q_aus) @ e_aus) > -0.1                   # im Austrittsrohr angekommen
            if weg.any():
                P[weg] = neu(int(weg.sum())); S[weg] = P[weg][:, None]; ruhe[weg] = 0
        v, _ = geschw(P); vb = np.linalg.norm(v, axis=1)
        ruhe = np.where(vb < 2e-3, ruhe + 1, 0)
        steht = ruhe > 30                                          # 3 s Stillstand: Totwasser, neu starten
        if steht.any():
            P[steht] = neu(int(steht.sum())); S[steht] = P[steht][:, None]; ruhe[steht] = 0
        S = np.concatenate([S[:, 1:], P[:, None]], 1)
        if b < 0:
            continue
        sicht = (S[:, :, 2] < a.z_schnitt).all(1)
        np.savez_compressed(aus / f"bild_{b:04d}.npz", s=S[sicht].astype(np.float32), v=vb[sicht].astype(np.float32))
        if b % 30 == 0:
            print(f"Bild {b}/{a.bilder}: sichtbar {sicht.sum()}, v Median {np.median(vb):.3f} m/s", flush=True)
    (aus / "info.json").write_text(json.dumps({**vars(a), "n_sub": n_sub, "v_max": v_max}, indent=1))


if __name__ == "__main__":
    main()
