"""surrogat_auswertung.py — Auswertung der trainierten Surrogate: Lastkurve + Parameterempfindlichkeit (Bild).

    .venv/bin/python -m stellarator.surrogat_auswertung

Je Anlage: Kennzahlen ueber dem Lastparameter (W7-X: B0, 1 GW: P_netz), uebrige Parameter in Bereichsmitte;
Tornado: Aenderung Stahl vm_p99 und u_max, wenn je ein Parameter von unterer zu oberer Bereichsgrenze geht.
Ausgabe sim/surrogat/auswertung.png und auswertung.json. Rechnet nur mit den GP-Modellen (Sekunden).
"""
from __future__ import annotations
import json, pickle
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .surrogat import ANLAGEN, ordner, vorhersage, WURZEL

KURVEN = [("stahl.vm_p99_MPa", "Stahl p99"), ("wickelpaket.vm_p99_MPa", "Wickelpaket p99"),
          ("verguss.vm_p99_MPa", "Verguss p99"), ("verbinder.vm_max_MPa", "Verbinder max")]


def mitte(meta) -> dict:
    p = {}
    for n, (lo, hi) in zip(meta["namen"], meta["bereiche"]):
        p[n] = float(np.sqrt(lo * hi)) if n in meta["log"] else 0.5 * (lo + hi)
    return p


def kenn(anlage, p):
    return {n: d["wert"] for n, d in vorhersage(anlage, p)["kennzahlen"].items()}


def main():
    erg = {}
    fig, ax = plt.subplots(2, 3, figsize=(17, 9.5))
    for z, anlage in enumerate(["w7x", "qa_1gw"]):
        meta = pickle.load(open(ordner(anlage) / "modell.pkl", "rb"))["meta"]
        p0 = mitte(meta); L = ANLAGEN[anlage]["last"]
        if L["art"] == "B0":
            lname, xs = "B0 [T]", np.linspace(*L["bereich"], 13)
            setze = lambda p, x: p | {"B0": x}
        else:
            lname, xs = "P_netz [MW]", np.linspace(*meta["bereiche"][meta["namen"].index("P_netz")], 13)
            setze = lambda p, x: p | {"P_netz": x}
        ks = [kenn(anlage, setze(p0, x)) for x in xs]
        a = ax[z, 0]
        for n, t in KURVEN:
            a.plot(xs, [k[n] for k in ks], "o-", ms=3, label=t)
        a.set_xlabel(lname); a.set_ylabel("von Mises [MPa]"); a.grid(alpha=.3); a.legend(fontsize=8)
        kurz = "W7-X-aehnlich (70 Spulen)" if anlage == "w7x" else "1 GW qa_nfp2_A45 HTS (16 Spulen)"
        a.set_title(f"{kurz}\nSpannung ueber Last", fontsize=10)
        a2 = ax[z, 1]
        a2.plot(xs, [k["u_max_mm"] for k in ks], "o-", ms=3, color="C4")
        a2.set_xlabel(lname); a2.set_ylabel("u_max [mm]"); a2.grid(alpha=.3)
        a2.set_title(f"Verformung\nStahlmasse {ks[len(xs) // 2]['stahl.masse_t']:.0f} t bei Lastmitte", fontsize=10)
        # Tornado
        basis = kenn(anlage, setze(p0, xs[len(xs) // 2]))
        zeilen = []
        for n, (lo, hi) in zip(meta["namen"], meta["bereiche"]):
            if n == "P_netz":
                continue
            klo = kenn(anlage, setze(p0 | {n: lo}, xs[len(xs) // 2])); khi = kenn(anlage, setze(p0 | {n: hi}, xs[len(xs) // 2]))
            zeilen.append((n, 100 * (klo["stahl.vm_p99_MPa"] / basis["stahl.vm_p99_MPa"] - 1),
                           100 * (khi["stahl.vm_p99_MPa"] / basis["stahl.vm_p99_MPa"] - 1)))
        zeilen.sort(key=lambda r: abs(r[2] - r[1]))
        a3 = ax[z, 2]; y = np.arange(len(zeilen))
        a3.barh(y, [r[1] for r in zeilen], color="C0", label="untere Grenze")
        a3.barh(y, [r[2] for r in zeilen], color="C3", alpha=.7, label="obere Grenze")
        a3.set_yticks(y, [r[0] for r in zeilen], fontsize=8); a3.axvline(0, color="k", lw=.8)
        a3.set_xlabel("Aenderung Stahl p99 [%]"); a3.legend(fontsize=8); a3.grid(alpha=.3, axis="x")
        a3.set_title(f"Empfindlichkeit Stahl p99\nBasis {basis['stahl.vm_p99_MPa']:.0f} MPa bei Lastmitte", fontsize=10)
        erg[anlage] = {"mitte": p0, "last": list(map(float, xs)), "kurven": ks, "tornado_proz": zeilen, "basis": basis}
    fig.suptitle("Surrogat (GP, 78 bzw. 79 Proben), uebrige Parameter in Bereichsmitte", fontsize=12, y=0.995)
    fig.tight_layout(); fig.savefig(WURZEL / "auswertung.png", dpi=120)
    (WURZEL / "auswertung.json").write_text(json.dumps(erg, indent=1, default=float))
    for anlage, e in erg.items():
        print(anlage, {n: round(v, 1) for n, v in e["basis"].items()})
        print("  staerkste Hebel:", [(r[0], round(r[1]), round(r[2])) for r in e["tornado_proz"][::-1][:4]])


if __name__ == "__main__":
    main()
