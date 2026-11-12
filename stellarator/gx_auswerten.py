"""gx_auswerten.py -- Ionen-Wärmefluss aus GX-Ausgaben (*.out.nc) mitteln und zeichnen.

KI-generiert (Claude Opus, 2026-11-11).

  python -m stellarator.gx_auswerten <bild.png> <lauf1.out.nc> [<lauf2.out.nc> ...] [--ab 100] [--bezug 7.0]

Mittel über t >= --ab (Einheiten L_ref/v_t,ref). Unsicherheit: Streuung von 4 Blockmitteln (grob, Flussröhre schwankt).
--bezug: Bezugswert Q_i/Q_GB mit Band ±30 % (Erwartung sim/gx_pilot/ERWARTUNG.md).
Läuft mit ~/cae_projekte/gx/deps/venv/bin/python (netCDF4).
"""
import json, sys
from pathlib import Path
import numpy as np
import netCDF4
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def lesen(pfad):
    d = netCDF4.Dataset(pfad)
    t = np.array(d["Grids/time"][:])
    q = np.array(d["Diagnostics/HeatFlux_st"][:, 0])
    return t, q


def mittel(t, q, ab):
    m = t >= ab
    bl = [b.mean() for b in np.array_split(q[m], 4) if len(b)]
    return float(q[m].mean()), float(np.std(bl, ddof=1) / np.sqrt(len(bl))), int(m.sum())


def main(a):
    ab = float(a[a.index("--ab") + 1]) if "--ab" in a else 100.0
    bezug = float(a[a.index("--bezug") + 1]) if "--bezug" in a else None
    rein = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--ab", "--bezug"))]
    bild, laeufe = Path(rein[0]), rein[1:]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if bezug:
        ax.axhspan(0.7 * bezug, 1.3 * bezug, color="0.85", zorder=0,
                   label=f"Zielband Benchmark {0.7*bezug:.1f}–{1.3*bezug:.1f} (Paper Abb. 7 ±30 %)")
    erg = {}
    for p in laeufe:
        t, q = lesen(p)
        mw, fe, n = mittel(t, q, ab)
        name = Path(p).name.replace(".out.nc", "")
        erg[name] = {"Q_i_mittel": mw, "fehler": fe, "punkte": n, "ab_t": ab, "t_ende": float(t[-1])}
        ax.plot(t, q, label=f"{name}: Mittel {mw:.2f} ± {fe:.2f}")
        ax.hlines(mw, ab, t[-1], linestyles="--", colors=ax.lines[-1].get_color())
    ax.axvline(ab, color="0.5", lw=0.8)
    ax.text(ab, ax.get_ylim()[1] * 0.95, " Mittel ab hier", fontsize=8, va="top")
    ax.set_xlabel("Zeit t (L_ref / v_t,ref)")
    ax.set_ylabel("Ionen-Wärmefluss Q_i / Q_GB")
    ax.set_title("GX, nichtlineare ITG-Turbulenz, eine Flussröhre (KI-generiert)")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(bild, dpi=130)
    bild.with_suffix(".json").write_text(json.dumps(erg, indent=1))
    print(json.dumps(erg, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
