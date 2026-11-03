"""review_bilder.py — Bilder fuer das Review-Paket Festigkeit (bericht/review/).

  .venv/bin/python -m stellarator.review_bilder

verbinder_modi(.png/_en.png): sigma99 im Gehaeusestahl fuer drei Verbinder-Modi von 0169, Standard- und Feinnetz
  (Quelle: sim/kopplung/{netz_normal,netz_s15}/punkte/0169 und sim/kopplung/verbinder/punkte/{0001,0002,0011,0012}).
anschluss_spitze(.png/_en.png) [noch nicht lesbar, Spitze liegt verdeckt in der Kerbe; nicht im Paket]: Netz und von-Mises-Spannung am hoechstbelasteten Element von 0169, Standardnetz gegen
  1,5x Stationen (gleiche Stelle, gleiche Farbskala).
ablauf(.png/_en.png): automatische Kette der Entwurfsstudie doe1 mit Stueckzahlen und Ausscheidungsgruenden
  (daten/doe1_auswertung.json, Laufzeit aus sim/kopplung/doe1/lauf.log).
galerie(.png/_en.png): 16 verworfene Entwuerfe, gleichmaessig ueber die Rangfolge verteilt (PicoGK-Katalogbilder aus
  bericht/variantenbericht/bilder/katalog), je Nummer, sigma99 und Grund des Ausscheidens.
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


GRUND = {"stahl": ("Stahlspannung", "steel stress"), "dehn": ("Dehnung Supraleiter", "superconductor strain"),
         "fluenz": ("Neutronenbelastung", "neutron fluence"), "Bn": ("Feldfehler", "field error"),
         "pack": ("Platz für Package", "package space"), "kern": ("Kernheizung", "nuclear heating"),
         "ausl": ("Auslastung Leiter", "conductor load"), "marge": ("Temperaturmarge", "temperature margin")}


def doe():
    E = json.loads((ROOT / "daten" / "doe1_auswertung.json").read_text())
    return E, E["zeilen"]


def ablauf():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    from collections import Counter
    E, Z = doe()
    n_plan = len(Z) + len(E["fehler"]); n_ger = len(Z)
    bau = [z for z in Z.values() if z["durchdringung"] == 0]
    weg = [z for z in bau if not z["alle_ok"]]
    knapp = sum(z["robust"] > -0.15 for z in weg); zul = len(E["zulaessig"])
    gr = Counter(z["engpass"] for z in weg)
    for sp in ("de", "en"):
        en = sp == "en"; t = lambda d, e: e if en else d
        fig = plt.figure(figsize=(12, 6.2), dpi=150)
        ax = fig.add_axes([0, 0.52, 1, 0.42]); ax.set_xlim(0, 12); ax.set_ylim(0, 2.4); ax.axis("off")
        kette = [(t("Parameter", "parameters"), t("Latin Hypercube,\n11 Stellgrößen", "Latin hypercube,\n11 variables")),
                 (t("Spulen", "coils"), "simsopt"), ("Package", t("Platz, Abschirmung", "space, shielding")),
                 (t("Festigkeit", "strength"), "Elmer FEM"), (t("Temperatur", "temperature"), t("Kernheizung, Marge", "nuclear heating, margin")),
                 (t("Bewertung", "assessment"), t("8 Grenzen", "8 limits")), (t("3D-Modell", "3D model"), t("PicoGK, Durchdringung", "PicoGK, intersection"))]
        w = 1.42
        for i, (a, b) in enumerate(kette):
            x = 0.25 + i * 1.66
            ax.add_patch(FancyBboxPatch((x, 0.75), w, 1.0, boxstyle="round,pad=0.04", fc="#e8f0fb", ec=BLAU, lw=1.4))
            ax.text(x + w / 2, 1.42, a, ha="center", va="center", fontsize=11, weight="bold", color="#1a1a1a")
            ax.text(x + w / 2, 1.0, b, ha="center", va="center", fontsize=8.5, color="#333")
            if i < len(kette) - 1:
                ax.annotate("", (x + w + 0.22, 1.25), (x + w + 0.03, 1.25), arrowprops=dict(arrowstyle="->", lw=1.4, color="#555"))
        ax.text(6, 2.2, t("Automatische Kette je Entwurf: 1–3 min, ohne Eingriff", "Automatic chain per design: 1–3 min, unattended"),
                ha="center", fontsize=12.5, weight="bold")
        ax.text(6, 0.35, t("Die KI schrieb die Kette und startete sie; 200 Entwürfe liefen am 2.11.2026 in 8,5 h durch "
                           "(12:28–20:57). Ziel und Richtung gab der Mensch vor.",
                           "The AI wrote and started the chain; 200 designs ran through on 2 Nov 2026 in 8.5 h "
                           "(12:28–20:57). Goal and direction came from the human."), ha="center", fontsize=9, color="#333")
        # Trichter
        bx = fig.add_axes([0.2, 0.08, 0.3, 0.38])
        stufen = [(t("geplant", "planned"), n_plan), (t("gerechnet", "computed"), n_ger),
                  (t("baubar (keine Durchdringung)", "buildable (no intersection)"), len(bau)),
                  (t("knapp oder zulässig", "narrow or admissible"), knapp + zul), (t("zulässig", "admissible"), zul)]
        farben = ["#9aa5b1", "#9aa5b1", "#9aa5b1", "#e9a800", BLAU]
        y = np.arange(len(stufen))[::-1]
        bx.barh(y, [v for _, v in stufen], color=farben, height=0.62)
        for yi, (lab, v) in zip(y, stufen):
            bx.text(v + 3, yi, f"{v}", va="center", fontsize=10, weight="bold")
        bx.set_yticks(y, [l for l, _ in stufen], fontsize=9.5); bx.set_xlim(0, 235)
        bx.spines[["top", "right"]].set_visible(False); bx.set_xlabel(t("Entwürfe", "designs"))
        bx.set_title(t("Was übrig bleibt", "What remains"), fontsize=11)
        # Gruende
        gx = fig.add_axes([0.62, 0.08, 0.34, 0.38])
        g = gr.most_common()
        yy = np.arange(len(g))[::-1]
        gx.barh(yy, [v for _, v in g], color="#c9452c", height=0.62)
        for yi, (k, v) in zip(yy, g):
            gx.text(v + 1.5, yi, f"{v}", va="center", fontsize=10, weight="bold")
        gx.set_yticks(yy, [GRUND[k][en] for k, _ in g], fontsize=9.5); gx.set_xlim(0, 120)
        gx.spines[["top", "right"]].set_visible(False); gx.set_xlabel(t("Entwürfe", "designs"))
        gx.set_title(t(f"Woran die {len(weg)} verworfenen scheitern\n(kleinste Reserve)",
                       f"Why the {len(weg)} rejected fail\n(smallest margin)"), fontsize=11)
        fig.text(0.99, 0.01, NAME, ha="right", fontsize=7, color="#666666")
        fig.savefig(AUS / f"ablauf{'_en' if en else ''}.png"); plt.close(fig)
    print("Kette:", n_plan, n_ger, len(bau), knapp + zul, zul, dict(gr))


def galerie(n=16):
    from PIL import Image, ImageDraw, ImageFont
    E, Z = doe()
    weg = sorted([nr for nr, z in Z.items() if z["durchdringung"] == 0 and not z["alle_ok"]], key=lambda nr: Z[nr]["robust"])
    wahl = [weg[int(round(i))] for i in np.linspace(0, len(weg) - 1, n)]
    kat = ROOT / "bericht" / "variantenbericht" / "bilder" / "katalog"
    fp = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    f1, f2 = ImageFont.truetype(fp, 22), ImageFont.truetype(fp.replace("Sans.ttf", "Sans-Bold.ttf"), 24)
    for sp in ("de", "en"):
        en = sp == "en"; W, H, kopf = 640, 392, 70; sp_n = 4
        bild = Image.new("RGB", (sp_n * W, (n // sp_n) * (H + kopf)), "white"); d = ImageDraw.Draw(bild)
        for k, nr in enumerate(wahl):
            z = Z[nr]; x, y = (k % sp_n) * W, (k // sp_n) * (H + kopf)
            q = kat / f"{nr}{'_en' if en and (kat / f'{nr}_en.jpg').exists() else ''}.jpg"
            bild.paste(Image.open(q).convert("RGB"), (x, y + kopf))
            farbe = (233, 168, 0) if z["robust"] > -0.15 else (201, 69, 44)
            d.rectangle([x + 3, y + 3, x + W - 4, y + H + kopf - 4], outline=farbe, width=5)
            d.text((x + 16, y + 10), f"{nr} · {z['spulen']} {'coils' if en else 'Spulen'} · σ99 {z['wert_stahl']:.0f} MPa", font=f2, fill=(20, 20, 20))
            d.text((x + 16, y + 40), f"{'fails' if en else 'scheitert'}: {GRUND[z['engpass']][en]} · {'margin' if en else 'Reserve'} {z['robust'] * 100:.0f} %",
                   font=f1, fill=farbe)
        bild = bild.resize((bild.width // 2, bild.height // 2), Image.LANCZOS)
        bild.save(AUS / f"galerie{'_en' if en else ''}.png", optimize=True)
    print("Galerie:", wahl)


def filmbild(fr=900):
    """Ein Bild aus dem Variantenfilm (Feld, die verworfenen versinken), mit Namen wie im Film."""
    from PIL import Image
    from .plasma_video_schnitt import nur_name
    q = ROOT / "sim" / "video_varianten" / "bilder" / f"{fr:05d}.png"
    nur_name(Image.open(q).convert("RGB")).resize((1280, 720), Image.LANCZOS).save(AUS / "film_feld.jpg", quality=88)


if __name__ == "__main__":
    AUS.mkdir(parents=True, exist_ok=True)
    verbinder_modi(); ablauf(); galerie(); filmbild()                      # anschluss_spitze() erst, wenn die Ansicht die Kerbe zeigt
