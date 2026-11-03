"""stahl_bild.py — Werkstoff der Spulengehaeuse: 1.4429 / X2CrNiMoN17-13-3 (AISI 316LN), Kennwerte RT und 4 K.

  .venv/bin/python -m stellarator.stahl_bild        -> docs/bilder/stahl_kennwerte(_en).png, daten/stahl_kennwerte.json

Quellen (Status):
  [RF]  Roloff/Matek ueber schweizer-fn.de (Tabelle des Nutzers), 1.4429 lösungsgeglüht, DIN EN 10088: Rp0,2 295, Rm 580 MPa
  [FE]  Fedorikova et al., Materials 16 (2023) 6473, doi:10.3390/ma16196473 (geprueft): 316LN-IG lösungsgeglüht,
        N 0,13 %: 293 K 325/641, 77 K 790/1282, 4,2 K 1070/1543 MPa (Rp0,2/Rm)
  [SA]  Sakurai, Umezawa, Ono, IOP Conf. Ser. MSE 1302 (2024) 012002, doi:10.1088/1757-899X/1302/1/012002 (geprueft):
        Rp0,2(4,2 K) steigt mit C+N; Dickbleche mit >= 1000 MPa hergestellt; ITER-Dickblech ~1080 MPa
  [M2]  ITER-TF-Struktur Guete C1 >= 1000 MPa, C3 >= 750 MPa bei 4 K (Mitchell et al., IAEA, ungeprueft)
  [S1]  Sorbom et al., ARC (2015): Annahme 1050 MPa bei 4 K (geprueft)
Regel: Sm = 2/3 Rp0,2 (ITER-Magnet-Kriterium nach Lee et al., ungeprueft); ASME-III-Form min(2/3 Rp0,2, 1/3 Rm) als Vergleich.
"""
import json, shutil
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ZIEL = [ROOT / "docs" / "bilder", ROOT / "bericht" / "projektbericht" / "bilder"]
WERTE = [  # Kennung, T [K], Rp0,2, Rm, Quelle, DE, EN
    ("RT_tabelle", 293, 295, 580, "RF", "1.4429 Raumtemp.\n(Tabelle, Roloff/Matek)", "1.4429 room temp.\n(table, Roloff/Matek)"),
    ("RT_messung", 293, 325, 641, "FE", "316LN 293 K\n(Messung)", "316LN 293 K\n(measured)"),
    ("77K", 77, 790, 1282, "FE", "316LN 77 K\n(Messung)", "316LN 77 K\n(measured)"),
    ("4K_messung", 4.2, 1070, 1543, "FE", "316LN 4,2 K\n(Messung)", "316LN 4.2 K\n(measured)"),
    ("4K_C3", 4.2, 750, None, "M2", "ITER Güte C3\n(Mindestwert 4 K)", "ITER grade C3\n(minimum 4 K)"),
    ("4K_C1", 4.2, 1000, None, "M2", "ITER Güte C1\n(Mindestwert 4 K)", "ITER grade C1\n(minimum 4 K)"),
]


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    daten = []
    for k, T, rp, rm, q, de, en in WERTE:
        sm = 2 / 3 * rp; asme = min(sm, rm / 3) if rm else None
        daten.append({"kennung": k, "T_K": T, "Rp02_MPa": rp, "Rm_MPa": rm, "quelle": q, "Sm_2_3_Rp_MPa": sm, "Sm_ASME_MPa": asme})
    (ROOT / "daten" / "stahl_kennwerte.json").write_text(json.dumps(daten, indent=1))
    for en in (False, True):
        plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
        fig, ax = plt.subplots(figsize=(10, 4.6))
        x = np.arange(len(WERTE)); w = 0.27
        rp = [d["Rp02_MPa"] for d in daten]; rm = [d["Rm_MPa"] or 0 for d in daten]; sm = [d["Sm_2_3_Rp_MPa"] for d in daten]
        b1 = ax.bar(x - w, rp, w * 0.92, color="#2a78d6", label="yield strength Rp0.2" if en else "Streckgrenze Rp0,2")
        b2 = ax.bar(x, rm, w * 0.92, color="#1baf7a", label="tensile strength Rm" if en else "Zugfestigkeit Rm")
        b3 = ax.bar(x + w, sm, w * 0.92, color="#eda100", label="allowable Sm = 2/3 Rp0.2" if en else "zulässig Sm = 2/3 Rp0,2")
        for bars in (b1, b2, b3):
            for r in bars:
                if r.get_height() > 0:
                    ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 15, f"{r.get_height():.0f}", ha="center", fontsize=7)
        ax.axhline(500, color="#52514e", ls="--", lw=1)
        ax.text(-0.45, 470, "limit used: 500 MPa" if en else "verwendete Grenze: 500 MPa", ha="left", va="top", fontsize=8)
        ax.set_xticks(x, [w_[6] if en else w_[5] for w_ in WERTE], fontsize=8)
        ax.set_ylabel("MPa"); ax.set_ylim(0, 1750); ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
        ax.set_title("Coil-case steel 1.4429 / X2CrNiMoN17-13-3 (AISI 316LN): strength at room temperature and at 4 K" if en else
                     "Gehäusestahl 1.4429 / X2CrNiMoN17-13-3 (AISI 316LN): Festigkeit bei Raumtemperatur und bei 4 K", fontsize=10)
        fig.text(0.99, 0.01, "Thomas Schmiegelt", ha="right", fontsize=7, color="#52514e")
        fig.tight_layout()
        name = "stahl_kennwerte" + ("_en" if en else "") + ".png"
        fig.savefig(ZIEL[0] / name, dpi=130); shutil.copy(ZIEL[0] / name, ZIEL[1] / name); print(ZIEL[0] / name)
        plt.close(fig)


if __name__ == "__main__":
    main()
