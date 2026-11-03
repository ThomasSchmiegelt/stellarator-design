"""festigkeit_bilder.py — Bilder fuer das Berichtskapitel Festigkeit (Kraftfluss, Tragwerksversuche, DOE-Zwischenstand).

  .venv/bin/python -m stellarator.festigkeit_bilder            # alle Bilder DE/EN nach docs/bilder + bericht/bilder

Quellen: sim/kopplung/test/punkte/000{0..4} (Tragwerksversuche, gleiche 16 Spulen), sim/kopplung/doe1 (DOE).
"""
import json
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "sim" / "kopplung" / "test" / "punkte"
DOE = ROOT / "sim" / "kopplung" / "doe1" / "punkte"
NAME = "Thomas Schmiegelt · privates Hobbyprojekt, nicht kommerziell"
ZIEL = [ROOT / "docs" / "bilder", ROOT / "bericht" / "projektbericht" / "bilder"]

VARIANTEN = [  # Ordner, DE, EN
    ("0000", "Lager außen\n(bisher)", "bearing outside\n(previous)"),
    ("0001", "Lager innen", "bearing inside"),
    ("0002", "innen + außen", "inside + outside"),
    ("0003", "+ 12 steife\nVerbinder je Paar", "+ 12 stiff\nconnectors per pair"),
    ("0004", "+ dickste\nWände", "+ thickest\nwalls"),
]


def speichern(fig, name):
    p = ZIEL[0] / name
    fig.savefig(p, dpi=130)
    shutil.copy(p, ZIEL[1] / name)
    print(p)


def render(ordner: str, datei: Path):
    import pyvista as pv
    pv.OFF_SCREEN = True
    g = pv.read(TEST / ordner / "struktur.vtu")
    s = g.extract_surface(algorithm="dataset_surface")
    p = pv.Plotter(window_size=(1100, 1000))
    p.set_background("white")
    p.add_mesh(s, scalars="vonmises_MPa", clim=[0, 1500], cmap="turbo", show_scalar_bar=False)
    p.camera_position = [(0, -6, 48), (0, 0, 0), (0, 1, 0)]
    p.screenshot(str(datei))


def tragwerk(en: bool):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import cm, colors
    tr = (lambda d, e: e) if en else (lambda d, e: d)
    werte = []
    for o, de, eng in VARIANTEN:
        e = json.loads((TEST / o / "ergebnis.json").read_text()); s = e["struktur"]
        werte.append({"name": eng if en else de, "p99": s["stahl"]["vm_p99_MPa"], "u": s["u_max_mm"],
                      "dehn": 100 * e["bewertung"]["dehnung_wp"],
                      "masse": (s["stahl"]["masse_t"] + s.get("verbinder", {}).get("masse_t", 0)) / 1e3})
    tmp = ROOT / "sim" / "kopplung" / "test"
    for o in ("0000", "0004"):
        if not (tmp / f"render_{o}.png").exists():
            render(o, tmp / f"render_{o}.png")
    fig = plt.figure(figsize=(15, 11))
    gs = fig.add_gridspec(2, 4, height_ratios=[1, 1.6])
    x = np.arange(len(werte)); namen = [w["name"] for w in werte]
    dez = (lambda v, n=0: f"{v:.{n}f}") if en else (lambda v, n=0: f"{v:.{n}f}".replace(".", ","))
    for k, (key, titel, grenze, n) in enumerate([
            ("p99", tr("Spannung im Gehäusestahl 1.4429 (99-%-Wert σ99) [MPa]", "stress in case steel 1.4429 (99 % value σ99) [MPa]"), 500, 0),
            ("u", tr("größte Verformung [mm]", "largest deformation [mm]"), None, 0),
            ("dehn", tr("Dehnung Wickelpaket [%]", "winding-pack strain [%]"), 0.3, 2),
            ("masse", tr("Stahl gesamt (Gehäuse + Verbinder) [1000 t]", "total steel (casing + connectors) [1000 t]"), None, 1)]):
        ax = fig.add_subplot(gs[0, k])
        v = [w[key] for w in werte]
        farbe = ["#c0392b" if (grenze and vv > grenze) else "#2e86c1" for vv in v]
        if grenze is None:
            farbe = ["#7f8c8d"] * len(v)
        ax.bar(x, v, color=farbe)
        for xi, vv in zip(x, v):
            ax.text(xi, vv, dez(vv, n), ha="center", va="bottom", fontsize=8)
        if grenze:
            ax.axhline(grenze, color="k", ls="--", lw=1)
            ax.text(-0.45, grenze, tr("Grenze", "limit"), ha="left", va="bottom", fontsize=8)
        ax.set_xticks(x); ax.set_xticklabels("ABCDE"[:len(x)], fontsize=9)
        ax.set_title(titel, fontsize=9); ax.set_ylim(0, max(v) * 1.12)
    fig.text(0.5, 0.585, "   ·   ".join(f"{c}: {n.replace(chr(10), ' ')}" for c, n in zip("ABCDE", namen)),
             ha="center", fontsize=9)
    for k, (o, t) in enumerate([("0000", tr("A – bisher: Lager außen, 6 Verbinder", "A – previous: bearing outside, 6 connectors")),
                                ("0004", tr("E – innen + außen gelagert, 12 steife Verbinder, dicke Wände",
                                            "E – bearing inside + outside, 12 stiff connectors, thick walls"))]):
        ax = fig.add_subplot(gs[1, 2 * k:2 * k + 2])
        ax.imshow(plt.imread(tmp / f"render_{o}.png")); ax.axis("off"); ax.set_title(t, fontsize=10)
    cax = fig.add_axes([0.35, 0.06, 0.3, 0.013])
    fig.colorbar(cm.ScalarMappable(colors.Normalize(0, 1500), "turbo"), cax=cax, orientation="horizontal",
                 label=tr("Vergleichsspannung [MPa] (Blick von oben)", "von Mises stress [MPa] (view from above)"))
    fig.suptitle(tr("Gleiche 16 Spulen, anderes Tragwerk: wie die Spannung sinkt",
                    "Same 16 coils, different support structure: how the stress drops"))
    fig.text(0.99, 0.005, NAME, ha="right", fontsize=7, color="0.5")
    fig.subplots_adjust(left=0.05, right=0.98, top=0.93, bottom=0.12, hspace=0.25, wspace=0.3)
    speichern(fig, "festigkeit_tragwerk" + ("_en" if en else "") + ".png"); plt.close(fig)


def doe_bild(en: bool):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tr = (lambda d, e: e) if en else (lambda d, e: d)
    P = []
    for f in sorted(DOE.glob("*/ergebnis.json")):
        e = json.loads(f.read_text()); s = e["struktur"]
        P.append((int(e["param"]["n_basis"]) * 4, s["stahl"]["vm_p99_MPa"],
                  (s["stahl"]["masse_t"] + s.get("verbinder", {}).get("masse_t", 0)) / 1e3, e["bewertung"]["alle_ok"],
                  e["param"]["verbinder_je_paar"], e["param"]["E_verbinder_GPa"]))
    if not P:
        return
    P = np.array(P, dtype=float)
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    for n, c in ((16, "C0"), (20, "C1"), (24, "C2")):
        m = P[:, 0] == n
        ax[0].scatter(P[m, 2], P[m, 1], s=28, c=c, label=tr(f"{n} Spulen", f"{n} coils"), alpha=0.8)
    ok = P[:, 3] == 1
    ax[0].scatter(P[ok, 2], P[ok, 1], s=120, facecolors="none", edgecolors="k", lw=1.4,
                  label=tr("alle Grenzen erfüllt", "all limits met"))
    ax[0].axhline(500, color="k", ls="--", lw=1)
    ax[0].set_yscale("log"); ax[0].set_xlabel(tr("Stahl gesamt [1000 t]", "total steel [1000 t]"))
    ax[0].set_ylabel(tr("Spannung Gehäusestahl, 99 %-Wert [MPa]", "casing steel stress, 99th percentile [MPa]"))
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3, which="both")
    sc = ax[1].scatter(P[:, 4], P[:, 1], c=np.log10(P[:, 5]), cmap="viridis", s=30)
    ax[1].scatter(P[ok, 4], P[ok, 1], s=120, facecolors="none", edgecolors="k", lw=1.4)
    ax[1].axhline(500, color="k", ls="--", lw=1); ax[1].set_yscale("log")
    ax[1].set_xlabel(tr("Verbinder je Spulenpaar", "connectors per coil pair"))
    cb = fig.colorbar(sc, ax=ax[1]); cb.set_label(tr("Steifigkeit Verbinder, log10(E / GPa)", "connector stiffness, log10(E / GPa)"))
    ax[1].grid(alpha=0.3, which="both")
    fig.suptitle(tr(f"Entwurfsstudie, Zwischenstand: {len(P)} Entwürfe, davon {int(ok.sum())} zulässig",
                    f"Design study, interim: {len(P)} designs, {int(ok.sum())} of them admissible"))
    fig.text(0.99, 0.005, NAME, ha="right", fontsize=7, color="0.5")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    speichern(fig, "festigkeit_doe" + ("_en" if en else "") + ".png"); plt.close(fig)


if __name__ == "__main__":
    for en in (False, True):
        tragwerk(en); doe_bild(en)
    for n in (16, 20, 24):
        for sfx in ("", "_en"):
            shutil.copy(ROOT / "docs" / "bilder" / f"kraft_analyse_{n}{sfx}.png", ZIEL[1] / f"kraft_analyse_{n}{sfx}.png")
