"""loop_evolution.py — Wie hat sich der Ralph-Loop (sim/spulenfreundlich, 9.11.2026) entwickelt? (Nutzerwunsch 2026-11-09)

  .venv-constellaration/bin/python stellarator/loop_evolution.py bild    -> docs/recherche/spulen_suche/loop_evolution.png
  .venv-constellaration/bin/python stellarator/loop_evolution.py video   -> docs/recherche/spulen_suche/loop_evolution.mp4
Reihenfolge = Reihenfolge der WAHL (verlauf.log: PRUEFSTEIN / PI waehlt / ERSATZ), Ergebnis aus results.tsv.
Video: im Bild nur Achsen, Rundenzähler und "Thomas Schmiegelt" (Vorgabe des Autors); Erklärung im Begleittext.
"""
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

ZIEL = 2.512e-3   # Zielbereich Feldfehler <= Bezug DATJ5FC (B-071) -- ANNAHME, keine physikalische Grenze (Nutzer 2026-11-10)
ZTXT = "Zielbereich ≤ 2,5e-3 (Annahme: Bezug DATJ5FC)"


def zielband(a, unten=1e-5):
    a.axhspan(unten, ZIEL, color="#2ca02c", alpha=.10, zorder=0, label=ZTXT)
    a.axhline(ZIEL, c="#2ca02c", lw=1, ls="--", zorder=1)


ROOT = Path(__file__).resolve().parents[1]; S = ROOT / "sim/spulenfreundlich"; O = ROOT / "docs/recherche/spulen_suche"


def daten():
    pool = pd.read_csv(S / "pool.tsv", sep="\t"); pool["rang"] = np.arange(1, len(pool) + 1)
    res = pd.read_csv(S / "results.tsv", sep="\t").drop_duplicates("id", keep="last")  # Wiederholung nach Abbruch: letzte Zeile gilt
    z = []
    for l in (S / "verlauf.log").read_text(errors="replace").splitlines():
        m = re.search(r"Runde (\d+) (PRUEFSTEIN (\S+)|PI waehlt (\S+?):|ERSATZ: .*nehme (\S+))", l)
        if m:
            z.append((int(m.group(1)), m.group(3) or m.group(4) or m.group(5),
                      "Prüfstein" if m.group(3) else ("PI" if m.group(4) else "Ersatz")))
    w = pd.DataFrame(z, columns=["runde", "id", "art"]).drop_duplicates("id")
    d = w.merge(pool, on="id").merge(res[["id", "ziel_Bn_mittel", "regeln_ok", "kreuzend"]], on="id", how="left")
    d = d[np.isfinite(d.ziel_Bn_mittel)].sort_values("runde").reset_index(drop=True)
    d["nr"] = np.arange(1, len(d) + 1)
    return pool, d


def bild():
    pool, d = daten(); x = d.nr; bn = d.ziel_Bn_mittel
    fig, ax = plt.subplots(2, 2, figsize=(13, 8.5))
    a = ax[0, 0]
    a.scatter(x, bn, s=18, c=np.where(d.nfp == 2, "#1f77b4", np.where(d.nfp == 3, "#2ca02c", "#d62728")), alpha=.75)
    a.step(x, bn.cummin(), where="post", c="k", lw=1.6, label="bester Wert bis hierher")
    zielband(a)
    a.set_yscale("log"); a.set_ylim(1.5e-4, 1.2e-2); a.set_title("(a) Ergebnis je gewählter Form (blau nfp 2, grün 3, rot 4)"); a.set_ylabel("Feldfehler der Spulen")
    a.legend(fontsize=8)
    a = ax[0, 1]
    r = bn.rolling(15, min_periods=15)
    a.fill_between(x, r.quantile(.25), r.quantile(.75), color="#1f77b4", alpha=.2, label="mittlere Hälfte (letzte 15)")
    a.plot(x, r.median(), c="#1f77b4", lw=2, label="Median der letzten 15 Formen")
    zielband(a)
    ok = (d.regeln_ok == True).astype(float).rolling(15, min_periods=15).mean() * 100
    a2 = a.twinx(); a2.plot(x, ok, "--", c="#ff7f0e", label="Regeln eingehalten (%, letzte 15)"); a2.set_ylim(0, 100); a2.set_ylabel("Anteil mit allen Bauregeln (%)")
    a.set_yscale("log"); a.set_ylim(1.5e-4, 1.2e-2); a.set_title("(b) Werden die Wahlen im Mittel besser?"); a.set_ylabel("Feldfehler (Median)")
    h1, l1 = a.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels(); a.legend(h1 + h2, l1 + l2, fontsize=8)
    a = ax[1, 0]
    for c, f, lab in [("elong", "#9467bd", "Elongation"), ("LgradB", "#8c564b", "Gradientenlänge"), ("A", "#17becf", "Aspektverhältnis")]:
        a.plot(x, d[c], ".", c=f, alpha=.5); a.plot(x, d[c].rolling(9, center=True, min_periods=3).median(), c=f, lw=2, label=lab)
    a.plot(x, d.iota * 50, ".", c="#e377c2", alpha=.5); a.plot(x, (d.iota * 50).rolling(9, center=True, min_periods=3).median(), c="#e377c2", lw=2, label="iota × 50")
    a.set_title("(c) Welche Merkmale wählt PI im Lauf der Zeit? (Linie: gleitender Median)"); a.set_xlabel("gewählte Form Nr."); a.legend(fontsize=8, ncol=2)
    a = ax[1, 1]
    a.scatter(x[d.art == "PI"], d.rang[d.art == "PI"], s=18, c="#1f77b4", label="Wahl von PI")
    a.scatter(x[d.art != "PI"], d.rang[d.art != "PI"], s=40, marker="x", c="k", label="Prüfstein / Ersatzwahl")
    a.plot(x, x, c="gray", ls="--", label="feste Regel „nächste nach QI“")
    a.set_title("(d) Wo im Pool (nach QI sortiert, 361) greift PI zu?"); a.set_xlabel("gewählte Form Nr."); a.set_ylabel("Rang im Pool (1 = bestes QI)")
    a.legend(fontsize=8)
    for a in ax[0]:
        a.set_xlabel("gewählte Form Nr.")
    fig.suptitle(f"Ralph-Loop 9.11.2026: lokales Modell PI wählt Datensatzformen, feste Spulenbewertung ({len(d)} Formen)")
    fig.tight_layout(); fig.savefig(O / "loop_evolution.png", dpi=120)
    print("Median erste/letzte 15:", bn[:15].median(), bn[-15:].median(), "Regeln ok erste/letzte 15:",
          (d.regeln_ok[:15] == True).mean(), (d.regeln_ok[-15:] == True).mean(), "nfp2-Anteil erste/letzte 15:",
          (d.nfp[:15] == 2).mean(), (d.nfp[-15:] == 2).mean())


def video():
    import matplotlib.animation as an
    pool, d = daten()
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.scatter(pool.elong, pool.LgradB, s=10, c="#cccccc")
    ax.set_xlabel("Elongation: größte Abplattung des Plasmaquerschnitts"); ax.set_ylabel("kleinste Gradientenlänge (groß = glattes Feld)")
    norm = LogNorm(vmin=2e-4, vmax=5e-3); cmap = plt.get_cmap("viridis_r")
    sc = ax.scatter([], [], s=55, c=[], cmap=cmap, norm=norm, edgecolors="k", linewidths=.4)
    best = ax.scatter([], [], s=260, facecolors="none", edgecolors="red", linewidths=2)
    cb = fig.colorbar(sc, ax=ax); cb.set_label("Feldfehler der Spulen")
    cb.ax.axhspan(2e-4, ZIEL, xmin=0, xmax=.25, color="black", alpha=.85)   # schwarzer Streifen = Zielbereich (Annahme), Erklaerung im Begleittext
    txt = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=13)
    fig.text(0.5, 0.01, "Thomas Schmiegelt", ha="center", fontsize=10)
    fig.tight_layout(rect=(0, 0.03, 1, 1))

    def f(i):
        k = d.iloc[:i + 1]
        sc.set_offsets(np.c_[k.elong, k.LgradB]); sc.set_array(k.ziel_Bn_mittel.values)
        j = k.ziel_Bn_mittel.idxmin(); best.set_offsets([[k.elong[j], k.LgradB[j]]])
        txt.set_text(f"{i + 1}")
        return sc, best, txt
    a = an.FuncAnimation(fig, f, frames=len(d), interval=250, blit=False)
    a.save(O / "loop_evolution.mp4", writer=an.FFMpegWriter(fps=4, bitrate=1800), dpi=110)
    print("Video", O / "loop_evolution.mp4", len(d), "Bilder")


if __name__ == "__main__":
    {"bild": bild, "video": video}[sys.argv[1]]()
