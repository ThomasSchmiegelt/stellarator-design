"""gx_vergleich.py -- GX-Wärmefluss der Pool-Formen gegen den ConStellaration-Turbulenz-Ersatzwert (B-073).

KI-generiert (Claude Opus, 2026-11-11). Erwartung: sim/gx_pilot/ERWARTUNG.md.

  ~/cae_projekte/gx/deps/venv/bin/python -m stellarator.gx_vergleich [--ab 100]

Links: Zeitverläufe Q_i (Lauf 2, boundary = "linked"). Rechts: Mittel Q_i über Ersatzwert, Lauf 1 ("fix aspect") hohl.
Ausgabe: sim/gx_pilot/formen_vergleich.png und .json.

  ... -m stellarator.gx_vergleich --alle
Streubild GX gegen Ersatzwert für ALLE Formen aus sim/gx_pilot/gx_werte.json (ohne w7x), Spearman im Titel.
Ausgabe: sim/gx_pilot/gx_alle_formen.png
"""
import json, sys
from pathlib import Path
import numpy as np
import netCDF4
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
L = Path.home() / "cae_projekte/gx/laeufe"
FORMEN = ["DZrUR4dAT8H3EQvsN4XPRnL", "DmC2qkhi8xDvETNDhUWhxW8", "DWzEhBMG385dMkAnPFyzPvC"]
FARBE = {"w7x": "0.4", FORMEN[0]: "#c0392b", FORMEN[1]: "#e67e22", FORMEN[2]: "#2471a3"}
GRENZE = 0.9   # ConStellaration-Benchmark: flux_compression_in_regions_of_bad_curvature <= 0.9


def lesen(ordner, ab):
    f = next(Path(ordner).glob("*.out.nc"), None)
    if f is None:
        return None
    d = netCDF4.Dataset(f)
    t = np.array(d["Grids/time"][:]); q = np.array(d["Diagnostics/HeatFlux_st"][:, 0])
    m = t >= ab
    if not m.any() or not np.isfinite(q[m]).all():
        return {"t": t, "q": q, "mittel": None, "fehler": None}
    bl = [b.mean() for b in np.array_split(q[m], 4)]
    return {"t": t, "q": q, "mittel": float(q[m].mean()), "fehler": float(np.std(bl, ddof=1) / 2)}


def alle():
    from scipy.stats import spearmanr
    w = json.loads((ROOT / "sim" / "gx_pilot" / "gx_werte.json").read_text())["werte"]
    f = [k for k in w if k != "w7x"]
    ers = np.array([json.loads((L / k / "ergebnis_vmec.json").read_text())["turbulenz_ersatz"] for k in f])
    q = np.array([w[k]["Q_i"] for k in f]); fe = np.array([w[k]["fehler"] for k in f])
    rho, p = spearmanr(ers, q)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axvspan(0.6, GRENZE, color="#d5f5e3", zorder=0)
    ax.text(0.62, 0.3, "Ersatzmaß ≤ 0,9\n(ConStellaration)", fontsize=9, color="#1e8449", va="bottom")
    ax.errorbar(ers, q, yerr=fe, fmt="o", ms=8, color="#2471a3", capsize=3, zorder=3)
    for k, x, y in zip(f, ers, q):
        ax.annotate(k[:8], (x, y), textcoords="offset points", xytext=(7, -12) if k.startswith(("DGozX5fj", "DmC2qkhi")) else (7, 5), fontsize=8)
    if "w7x" in w:
        ax.axhline(w["w7x"]["Q_i"], color="0.4", ls=":", lw=1)
        ax.text(1.95, w["w7x"]["Q_i"], "W7-X (GX, Benchmark)", fontsize=8, va="top", ha="left", color="0.3")
    ax.set_xlim(0.6, 2.6); ax.set_ylim(0, 1.15 * (q + fe).max())
    ax.set_xlabel("Turbulenz-Ersatzmaß (flux compression, bad curvature); kleiner = besser")
    ax.set_ylabel("GX: mittlerer Ionen-Wärmefluss Q_i / Q_GB; kleiner = besser")
    ax.set_title(f"GX gegen Ersatzmaß, {len(f)} Datensatzformen (unverändert): Spearman {rho:.2f}".replace(".", ","), fontsize=11)
    fig.text(0.99, 0.01, "KI-generiert", ha="right", fontsize=8, color="0.4")
    fig.tight_layout()
    aus = ROOT / "sim" / "gx_pilot" / "gx_alle_formen.png"
    fig.savefig(aus, dpi=130)
    print(len(f), "Formen, Spearman", rho, "p", p, "->", aus)


def main(a):
    if "--alle" in a:
        return alle()
    ab = float(a[a.index("--ab") + 1]) if "--ab" in a else 100.0
    erg = {}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.5, 1]})
    for id_ in ["w7x"] + FORMEN:
        r2 = lesen(L / "linked" / id_, ab)
        r1 = lesen(L / ("w7x_lang" if id_ == "w7x" else id_), ab)
        ers = None
        if id_ != "w7x":
            ers = json.loads((L / id_ / "ergebnis_vmec.json").read_text())["turbulenz_ersatz"]
        name = "W7-X (Benchmark)" if id_ == "w7x" else id_[:8]
        erg[name] = {"Q_i_linked": r2 and r2["mittel"], "fehler_linked": r2 and r2["fehler"],
                     "Q_i_fix_aspect": r1 and r1["mittel"], "turbulenz_ersatz": ers}
        if r2:
            lab = f"{name}: {r2['mittel']:.2f}" if r2["mittel"] is not None else f"{name}: ungültig (NaN)"
            ax1.plot(r2["t"], r2["q"], color=FARBE[id_], lw=1.2, label=lab)
        if ers is not None:
            for r, voll in ((r2, True), (r1, False)):
                if r and r["mittel"] is not None:
                    ax2.errorbar(ers, r["mittel"], yerr=r["fehler"], fmt="o", ms=9, color=FARBE[id_],
                                 mfc=FARBE[id_] if voll else "white", capsize=3)
            ax2.annotate(name, (ers, (r2 or r1 or {}).get("mittel") or 0), textcoords="offset points", xytext=(8, 6), fontsize=9)
    w = erg["W7-X (Benchmark)"]["Q_i_linked"]
    if w:
        ax2.axhline(w, color="0.4", ls=":", lw=1); ax2.text(0.62, w, " W7-X (GX, linked)", fontsize=8, va="bottom", color="0.3")
    ax1.axvline(ab, color="0.5", lw=0.8); ax1.text(ab, 0.2, " Mittel ab hier", fontsize=8)
    ax1.set_xlabel("Zeit t (L_ref / v_t,ref)"); ax1.set_ylabel("Ionen-Wärmefluss Q_i / Q_GB (kleiner = besser)")
    ax1.set_title("GX-Zeitverläufe, Randbedingung „linked“"); ax1.legend(fontsize=8, loc="upper right")
    ax1.set_ylim(0, None)
    ax2.axvspan(0.6, GRENZE, color="#d5f5e3", zorder=0, label="Zielbereich Ersatzwert ≤ 0,9 (ConStellaration)")
    ax2.set_xlim(0.6, 2.1); ax2.set_ylim(0, 1.15 * max(v["Q_i_linked"] or 0 for v in erg.values()))
    ax2.set_xlabel("Turbulenz-Ersatzwert (flux compression, bad curvature)")
    ax2.set_ylabel("GX: mittlerer Q_i / Q_GB")
    ax2.set_title("Gleiche Reihenfolge? voll = linked, hohl = fix aspect")
    ax2.legend(fontsize=8, loc="lower right")
    fig.suptitle("GX-Pilot: drei Pool-Formen (Datensatzformen unverändert), eine Flussröhre s = 0,64, a/L_T = 3, a/L_n = 1  —  KI-generiert", fontsize=10)
    fig.tight_layout()
    aus = ROOT / "sim" / "gx_pilot" / "formen_vergleich.png"
    fig.savefig(aus, dpi=130)
    aus.with_suffix(".json").write_text(json.dumps(erg, indent=1))
    print(json.dumps(erg, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
