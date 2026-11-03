"""review_bilder.py — zwei Bilder fuer das Review-Paket Festigkeit (bericht/review/).

  .venv/bin/python -m stellarator.review_bilder

verbinder_modi(.png/_en.png): sigma99 im Gehaeusestahl fuer drei Verbinder-Modi von 0169, Standard- und Feinnetz
  (Quelle: sim/kopplung/{netz_normal,netz_s15}/punkte/0169 und sim/kopplung/verbinder/punkte/{0001,0002,0011,0012}).
anschluss_spitze(.png/_en.png) [noch nicht lesbar, Spitze liegt verdeckt in der Kerbe; nicht im Paket]: Netz und von-Mises-Spannung am hoechstbelasteten Element von 0169, Standardnetz gegen
  1,5x Stationen (gleiche Stelle, gleiche Farbskala).
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KOP = ROOT / "sim" / "kopplung"
AUS = ROOT / "bericht" / "review" / "bilder"
NAME = "Thomas Schmiegelt"
BLAU, ORANGE = "#2a78d6", "#eb6834"

LAEUFE = {"standard": ("netz_normal/punkte/0169", "netz_s15/punkte/0169"),
          "getrennt": ("verbinder/punkte/0001", "verbinder/punkte/0011"),
          "platte": ("verbinder/punkte/0002", "verbinder/punkte/0012")}
TXT = {"de": {"modi": ["bisher (Überlappung\ndoppelt gezählt)", "getrennte Stege", "durchgehende Platte"],
              "s": "Standardnetz", "f": "1,5× Stationen", "y": "σ99 Gehäusestahl 1.4429 [MPa]",
              "t": "Entwurf 0169: Verbinder als Stege oder als Platte", "g": "Grenze 500 MPa",
              "a": ["Standardnetz", "1,5× Stationen entlang der Spule"], "c": "von-Mises-Spannung [MPa]"},
       "en": {"modi": ["previous (overlap\ncounted twice)", "separate webs", "continuous plate"],
              "s": "standard mesh", "f": "1.5× stations", "y": "σ99 casing steel 1.4429 [MPa]",
              "t": "Design 0169: connectors as webs or as a plate", "g": "limit 500 MPa",
              "a": ["standard mesh", "1.5× stations along the coil"], "c": "von Mises stress [MPa]"}}


def wert(rel):
    return json.loads((KOP / rel / "ergebnis.json").read_text())["struktur"]["stahl"]["vm_p99_MPa"]


def verbinder_modi():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    w = {m: (wert(a), wert(b)) for m, (a, b) in LAEUFE.items()}
    for sp, T in TXT.items():
        fig, ax = plt.subplots(figsize=(8, 4.2), dpi=160)
        x = np.arange(3); b = 0.36
        for k, (lab, col) in enumerate(((T["s"], BLAU), (T["f"], ORANGE))):
            v = [w[m][k] for m in LAEUFE]
            r = ax.bar(x + (k - 0.5) * (b + 0.02), v, b, color=col, label=lab)
            for xi, vi in zip(x + (k - 0.5) * (b + 0.02), v):
                ax.text(xi, vi + 6, f"{vi:.0f}", ha="center", va="bottom", fontsize=9, color="#222")
        for xi, m in zip(x, LAEUFE):
            z = w[m][1] / w[m][0] - 1
            ax.text(xi, max(w[m]) + 40, f"{z * 100:+.0f} %", ha="center", fontsize=10, weight="bold", color="#222")
        ax.axhline(500, ls="--", lw=1, color="#555"); ax.text(-0.55, 505, T["g"], ha="left", va="bottom", fontsize=8, color="#555")
        ax.set_xticks(x, T["modi"]); ax.set_ylabel(T["y"]); ax.set_ylim(0, 600); ax.set_title(T["t"], fontsize=11)
        ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", alpha=0.3); ax.set_axisbelow(True)
        ax.legend(frameon=False, loc="upper left", ncol=2)
        fig.text(0.99, 0.01, NAME, ha="right", fontsize=7, color="#666666")
        fig.tight_layout(); fig.savefig(AUS / f"verbinder_modi{'_en' if sp == 'en' else ''}.png"); plt.close(fig)


def anschluss_spitze():
    import pyvista as pv
    pv.OFF_SCREEN = True
    g0 = pv.read(KOP / LAEUFE["standard"][0] / "struktur.vtu")
    g1 = pv.read(KOP / LAEUFE["standard"][1] / "struktur.vtu")
    def stahl(g):
        return g.extract_cells(np.where(np.isin(np.asarray(g.cell_data["material"]), [3, 4]))[0])
    s0, s1 = stahl(g0), stahl(g1)

    def umgebung(s, r=2.0):
        """Elemente im Umkreis r um das hoechstbelastete Element (jedes Netz an seiner eigenen Spitze)."""
        vm = np.asarray(s.cell_data["vonmises_MPa"]); i = int(np.argmax(vm))
        cc = np.asarray(s.cell_centers().points); c = cc[i]
        return s.extract_cells(np.where(np.linalg.norm(cc - c, axis=1) < r)[0]), c, vm[i]

    U = [umgebung(s0), umgebung(s1)]
    for sp, T in TXT.items():
        pl = pv.Plotter(shape=(1, 2), window_size=(1800, 860), border=False)
        for k, (a, c, m) in enumerate(U):
            n = c - np.asarray(a.points).mean(0); n /= np.linalg.norm(n)       # Spitze zeigt zur Kamera
            pl.subplot(0, k)
            pl.add_mesh(a, scalars="vonmises_MPa", cmap="turbo", clim=(0, 800), show_edges=True, edge_color="#333333",
                        line_width=0.5, show_scalar_bar=(k == 1),
                        scalar_bar_args={"title": T["c"], "vertical": True, "position_x": 0.86, "position_y": 0.2,
                                         "height": 0.6, "width": 0.05, "title_font_size": 16, "label_font_size": 14})
            pl.add_text(f"{T['a'][k]}: max {m:.0f} MPa", font_size=12, position="upper_left")
            pl.set_background("white"); pl.camera_position = [tuple(c + 8.0 * n), tuple(c), (0, 0, 1)]; pl.reset_camera()
        pl.add_text(NAME, font_size=7, position="lower_right", color="#666666")
        pl.screenshot(str(AUS / f"anschluss_spitze{'_en' if sp == 'en' else ''}.png")); pl.close()
    print("Spitzen bei", [np.round(u[1], 2) for u in U], "m")


if __name__ == "__main__":
    AUS.mkdir(parents=True, exist_ok=True)
    verbinder_modi()                      # anschluss_spitze() erst, wenn die Ansicht die Kerbe zeigt
