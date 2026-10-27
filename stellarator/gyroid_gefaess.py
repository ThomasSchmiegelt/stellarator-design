"""gyroid_gefaess.py — Plasmagefaess mit Gyroid-Kuehlkern (PicoGK) + Spulentorus der 1-GW-Anlage, Gesamtbild.

    .venv/bin/python -m stellarator.gyroid_gefaess [--sektoren 0:360] [--zelle 0.35 --voxel 0.03] [--name gesamt]

Plasmarand: VMEC-Randflaeche (sim/invers/qa_nfp2_A45/wout_*.nc), skaliert auf R0 der 1-GW-Anlage.
PicoGK (picogk/GyroidGefaess) je Sektor: Offset(Plasma, spalt) .. Offset(Plasma, spalt+wand) = Wand,
Innen-/Aussenhaut voll, dazwischen Gyroid-Schale. Sektoren einzeln (Speicher), danach zusammen gezeigt.
Spulen: Hex-Modell der Surrogat-Probe 0 (Stahl, von Mises), optional.
Ausgabe sim/gyroid_gefaess/<name>/: sektor_*/gefaess.stl, plasma.vtp, gesamt.png, ergebnis.json.
Massstab: Gesamtansicht mit groben Zellen (0,3-0,4 m); feiner Ausschnitt ueber --sektoren 0:10 --zelle 0.12.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import numpy as np

from .lauf import PROJEKT
from .spulen import schreibe_stl
from .speicherwaechter import starte_begrenzt

APP = PROJEKT / "picogk" / "GyroidGefaess"
BIN = APP / "bin" / "Release" / "net9.0" / "GyroidGefaess"
WURZEL = PROJEKT / "sim" / "gyroid_gefaess"
ENV = os.environ | {"DOTNET_ROOT": str(Path.home() / ".dotnet")}


def randflaeche(R0: float = 10.4, n_th: int = 96, n_ph: int = 720, phi: np.ndarray | None = None) -> np.ndarray:
    """VMEC-Rand X (n_th, n_ph, 3) [m], phi 0..2pi (oder an den Winkeln phi [rad]), skaliert auf R0."""
    from netCDF4 import Dataset
    ordner = PROJEKT / "sim" / "invers" / "qa_nfp2_A45"
    R0_s = json.loads((ordner / "stufe1.json").read_text())["kennzahlen"]["R0_m"]
    with Dataset(str(next(ordner.glob("wout_*.nc")))) as w:
        rmnc, zmns, xm, xn = w["rmnc"][-1, :], w["zmns"][-1, :], w["xm"][:], w["xn"][:]
    th, ph = np.meshgrid(np.linspace(0, 2 * np.pi, n_th, endpoint=False), np.linspace(0, 2 * np.pi, n_ph, endpoint=False) if phi is None else np.asarray(phi, float),
                         indexing="ij")
    arg = xm[:, None, None] * th - xn[:, None, None] * ph
    R = np.einsum("m,mij->ij", rmnc, np.cos(arg)); Z = np.einsum("m,mij->ij", zmns, np.sin(arg))
    return np.stack([R * np.cos(ph), R * np.sin(ph), Z], -1) * (R0 / R0_s)


def sektor_stl(X: np.ndarray, ph0: float, ph1: float, pfad: Path) -> None:
    """Geschlossener Plasma-Sektor phi in [ph0, ph1] (Grad) mit Faecher-Deckeln, in mm."""
    n_ph = X.shape[1]
    idx = np.arange(int(np.floor(ph0 / 360 * n_ph)), int(np.ceil(ph1 / 360 * n_ph)) + 1) % n_ph
    S = X[:, idx]                                               # (n_th, k, 3)
    n_th, k = S.shape[:2]
    tri = []
    for j in range(k - 1):
        for i in range(n_th):
            a, b = S[i, j], S[(i + 1) % n_th, j]
            c, d = S[(i + 1) % n_th, j + 1], S[i, j + 1]
            tri += [(a, b, c), (a, c, d)]
    for j, umk in ((0, False), (k - 1, True)):
        m = S[:, j].mean(0)
        for i in range(n_th):
            t = (m, S[(i + 1) % n_th, j], S[i, j])
            tri.append(t[::-1] if umk else t)
    T = np.array(tri)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    schreibe_stl(pfad, T if vol > 0 else T[:, ::-1], skala=1.0)          # T ist schon in mm


def keil_stl(ph0: float, ph1: float, R_max: float, Z_max: float, pfad: Path, n: int = 24, z_lo: float | None = None) -> None:
    """Keil phi in [ph0, ph1], 0 <= R <= R_max, z_lo <= Z <= Z_max (Prisma ueber einem Kreissektor), in mm.
    Ohne z_lo symmetrisch |Z| <= Z_max."""
    p = np.radians(np.linspace(ph0, ph1, n))
    ring = np.c_[R_max * np.cos(p), R_max * np.sin(p)]
    poly = np.vstack([[0, 0], ring])                           # Kreissektor
    unten = np.c_[poly, np.full(len(poly), -Z_max if z_lo is None else z_lo)]; oben = np.c_[poly, np.full(len(poly), Z_max)]
    tri = []
    for i in range(1, len(poly) - 1):
        tri += [(unten[0], unten[i + 1], unten[i]), (oben[0], oben[i], oben[i + 1])]
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        tri += [(unten[i], unten[j], oben[j]), (unten[i], oben[j], oben[i])]
    T = np.array(tri)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    schreibe_stl(pfad, T if vol > 0 else T[:, ::-1], skala=1.0)          # T ist schon in mm


def ebenen_keil_stl(ph0: float, ph1: float, R_max: float, Z_max: float, phi_e: float, R_e: float, pfad: Path, n: int = 48) -> None:
    """Keil phi in [ph0, ph1] wie keil_stl, zusaetzlich abgeschnitten durch die senkrechte Ebene
    x.e_r(phi_e) <= R_e (Aussenteil weg), in mm."""
    p = np.radians(np.linspace(ph0, ph1, n))
    poly = np.vstack([[0, 0], np.c_[R_max * np.cos(p), R_max * np.sin(p)]])
    e = np.array([np.cos(np.radians(phi_e)), np.sin(np.radians(phi_e))])
    aus = []                                                     # Sutherland-Hodgman an einer Halbebene
    for i in range(len(poly)):
        P, Q = poly[i], poly[(i + 1) % len(poly)]
        dP, dQ = P @ e - R_e, Q @ e - R_e
        if dP <= 0:
            aus.append(P)
        if dP * dQ < 0:
            aus.append(P + (Q - P) * dP / (dP - dQ))
    poly = np.array(aus)
    unten = np.c_[poly, np.full(len(poly), -Z_max)]; oben = np.c_[poly, np.full(len(poly), Z_max)]
    tri = []
    for i in range(1, len(poly) - 1):
        tri += [(unten[0], unten[i + 1], unten[i]), (oben[0], oben[i], oben[i + 1])]
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        tri += [(unten[i], unten[j], oben[j]), (unten[i], oben[j], oben[i])]
    T = np.array(tri)
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    schreibe_stl(pfad, T if vol > 0 else T[:, ::-1], skala=1.0)


def baue_sektor(X, ph0, ph1, o: Path, a) -> dict:
    o.mkdir(parents=True, exist_ok=True)
    rand = 2.0                                                  # Grad Ueberstand, Keil schneidet sauber
    sektor_stl(X * 1000, ph0 - rand, ph1 + rand, o / "plasma.stl")
    R_max = (np.hypot(X[..., 0], X[..., 1]).max() + a.spalt + a.wand + 0.5) * 1000
    Z_max = (np.abs(X[..., 2]).max() + a.spalt + a.wand + 0.5) * 1000
    if a.ebene:                                                 # senkrechter Schnitt: Aussenteil hinter Ebene phi:R weg
        phi_e, R_e = map(float, a.ebene.split(":"))
        ebenen_keil_stl(ph0, ph1, R_max, Z_max, phi_e, R_e * 1000, o / "keil.stl")
    elif a.z_band:                                                # nur waagrechtes Band z_lo..z_hi (horizontaler Schnitt)
        z_lo, z_hi = (float(v) * 1000 for v in a.z_band.split(":"))
        keil_stl(ph0, ph1, R_max, z_hi, o / "keil.stl", z_lo=z_lo)
    else:
        keil_stl(ph0, ph1, R_max, Z_max, o / "keil.stl")
    auftrag = {"plasma_stl": str(o / "plasma.stl"), "keil_stl": str(o / "keil.stl"), "spalt_mm": a.spalt * 1000,
               "wand_mm": a.wand * 1000, "haut_innen_mm": a.haut_innen * 1000, "haut_aussen_mm": a.haut_aussen * 1000,
               "zelle_mm": a.zelle * 1000, "halbdicke_mm": a.halbdicke * 1000, "voxel_mm": a.voxel * 1000, "ausgabe": str(o)}
    (o / "auftrag.json").write_text(json.dumps(auftrag, indent=1))
    # eigene systemd-Einheit mit Speichergrenze + Waechter (sonst beendet systemd-oomd die ganze Sitzung)
    w = starte_begrenzt([str(BIN), str(o / "auftrag.json")], o / "picogk.log", a.max_gb,
                        env={"DOTNET_ROOT": ENV["DOTNET_ROOT"]})
    if not w["ok"]:
        raise RuntimeError(f"PicoGK abgebrochen: {w['grund']} (Spitze {w['spitze_gb']:.1f} GB), Log {o / 'picogk.log'}")
    e = json.loads((o / "ergebnis.json").read_text()) | {"zeit_s": w["zeit_s"], "spitze_gb": w["spitze_gb"]}
    print(f"Sektor {ph0:.0f}-{ph1:.0f} Grad: Wand {e['volumen_wand_m3']:.1f} m3, Stahlanteil {e['stahlanteil_wand']:.0%}, "
          f"{e['dreiecke']} Dreiecke, {e['zeit_s']:.0f} s, Spitze {w['spitze_gb']:.1f} GB", flush=True)
    return e


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sektoren", default="0:360", help="von:bis Grad")
    ap.add_argument("--teil", type=float, default=30.0, help="Grad je PicoGK-Lauf (Speicher)")
    ap.add_argument("--spalt", type=float, default=0.15)
    ap.add_argument("--wand", type=float, default=0.45)
    ap.add_argument("--haut_innen", type=float, default=0.02)
    ap.add_argument("--haut_aussen", type=float, default=0.03)
    ap.add_argument("--zelle", type=float, default=0.35)
    ap.add_argument("--halbdicke", type=float, default=0.02)
    ap.add_argument("--voxel", type=float, default=0.03)
    ap.add_argument("--z_band", default="", help="nur Band z_lo:z_hi [m] bauen, z.B. -1.0:0 fuer horizontalen Schnitt")
    ap.add_argument("--ebene", default="", help="phi_grad:R_m senkrechte Schnittebene, Aussenteil weg (Segment-Schnitt)")
    ap.add_argument("--name", default="gesamt")
    ap.add_argument("--max_gb", type=float, default=10.0, help="Speichergrenze je PicoGK-Lauf")
    a = ap.parse_args(argv)
    o = WURZEL / a.name
    X = randflaeche()
    lo, hi = map(float, a.sektoren.split(":"))
    grenzen = np.arange(lo, hi + 1e-9, a.teil)
    erg = {"parameter": vars(a), "sektoren": []}
    for ph0, ph1 in zip(grenzen[:-1], grenzen[1:]):
        so = o / f"sektor_{ph0:03.0f}"
        if (so / "gefaess.stl").exists():
            continue
        erg["sektoren"].append({"von": ph0, "bis": ph1} | baue_sektor(X, ph0, ph1, so, a))
    (o / "ergebnis.json").write_text(json.dumps(erg, indent=1, default=str))


if __name__ == "__main__":
    main()


def gesamtbild(name: str = "detail", spulen_vtu: Path | None = None, spalt: float = 0.15, wand: float = 0.45) -> Path:
    """Plasma + glatte Gefaessschale (Rest des Rings) + Gyroid-Detailsektoren + Spulengehaeuse (Surrogat, von Mises).
    Schreibt gesamt.vtm (ParaView) und gesamt_*.png."""
    import pyvista as pv
    o = WURZEL / name
    X = randflaeche()
    n_th, n_ph = X.shape[:2]
    # Flaechennormale aus Ableitungen (nach aussen)
    dth = np.roll(X, -1, 0) - np.roll(X, 1, 0); dph = np.roll(X, -1, 1) - np.roll(X, 1, 1)
    N = np.cross(dph, dth); N /= np.linalg.norm(N, axis=-1, keepdims=True)
    R = np.hypot(X[..., 0], X[..., 1]); Rn = np.hypot((X + N)[..., 0], (X + N)[..., 1])
    if np.mean((X + 0.1 * N)[..., 2] * X[..., 2] + (np.hypot(*(X + 0.1 * N)[..., :2].transpose(2, 0, 1)) - R.mean()) *
               (R - R.mean())) < 0:
        N = -N

    def flaeche(P, ph0, ph1):
        ph = np.degrees(np.arctan2(X[0, :, 1], X[0, :, 0])) % 360
        j = np.where((ph >= ph0) & (ph <= ph1))[0]
        S = P[:, j]; nt, k = S.shape[:2]
        pts = S.reshape(-1, 3)
        q = [[4, i * k + jj, ((i + 1) % nt) * k + jj, ((i + 1) % nt) * k + jj + 1, i * k + jj + 1]
             for i in range(nt) for jj in range(k - 1)]
        return pv.PolyData(pts, np.array(q).ravel())

    lo_d = min(float(p.name.split("_")[1]) for p in o.glob("sektor_*"))
    hi_d = max(float(p.name.split("_")[1]) for p in o.glob("sektor_*")) + json.loads(
        (o / "ergebnis.json").read_text())["parameter"]["teil"]
    teile = {"plasma": flaeche(X, 0, 360),
             "schale_aussen": flaeche(X + (spalt + wand) * N, hi_d, 360 - 1e-6),
             "schale_innen": flaeche(X + spalt * N, hi_d, 360 - 1e-6)}
    gy = [pv.read(p / "gefaess.stl").scale(1e-3) for p in sorted(o.glob("sektor_*")) if (p / "gefaess.stl").exists()]
    teile["gyroid_sektor"] = gy[0].merge(gy[1:]) if len(gy) > 1 else gy[0]
    spulen_vtu = spulen_vtu or PROJEKT / "sim/surrogat/qa_1gw/check_1000MW/vorhersage.vtu"
    if Path(spulen_vtu).exists():
        g = pv.read(spulen_vtu)
        st = g.extract_cells(np.where(g.cell_data["material"] >= 3)[0]).extract_surface()
        c = st.cell_centers().points
        phc = np.degrees(np.arctan2(c[:, 1], c[:, 0])) % 360
        # Spulen ueber dem Detailsektor weglassen, damit er sichtbar bleibt
        sp = st.cell_data["spule"]; weg = set()
        for s in np.unique(sp):
            m = np.degrees(np.angle(np.exp(1j * np.radians(phc[sp == s]))).mean()) % 360 if False else \
                np.degrees(np.angle(np.mean(np.exp(1j * np.radians(phc[sp == s]))))) % 360
            if (m - lo_d + 40) % 360 < (hi_d - lo_d) + 80:
                weg.add(s)
        teile["spulen"] = st.extract_cells(np.where(~np.isin(sp, list(weg)))[0])
        teile["spulen_weg"] = st.extract_cells(np.where(np.isin(sp, list(weg)))[0])
    mb = pv.MultiBlock({k: v for k, v in teile.items()})
    mb.save(o / "gesamt.vtm")
    for ansicht, kam in (("schraeg", None), ("detail", "detail")):
        pl = pv.Plotter(off_screen=True, window_size=(1900, 1200))
        pl.set_background("white")
        pl.add_mesh(teile["plasma"], color="#c050ff", opacity=0.55, smooth_shading=True)
        pl.add_mesh(teile["schale_aussen"], color="#8a949d", opacity=0.6, smooth_shading=True)
        pl.add_mesh(teile["gyroid_sektor"], color="#e8a33a", smooth_shading=True)
        if "spulen" in teile:
            pl.add_mesh(teile["spulen"], scalars="vonmises_MPa", cmap="turbo", clim=[0, 4000],
                        scalar_bar_args={"title": "von Mises Spulengehaeuse [MPa] (Surrogat, 1000 MW)"})
            pl.add_mesh(teile["spulen_weg"], color="#555555", opacity=0.12)
        pl.add_text("1-GW-Entwurf qa_nfp2_A45: Plasma (violett), Gefaess mit Gyroid-Kuehlkern (orange, Sektor), "
                    "Gefaessschale (grau), Spulengehaeuse", font_size=10, color="black")
        if kam:
            ph = np.radians(0.5 * (lo_d + hi_d)); r = 10.4
            pl.camera.focal_point = (r * np.cos(ph), r * np.sin(ph), 0)
            pl.camera.position = (r * np.cos(ph) + 16 * np.cos(ph + 1.1), r * np.sin(ph) + 16 * np.sin(ph + 1.1), 7)
            pl.camera.up = (0, 0, 1)
        else:
            pl.view_isometric(); pl.camera.elevation = 15; pl.camera.zoom(1.25)
        pl.screenshot(o / f"gesamt_{ansicht}.png"); pl.close()
    return o


if __name__ == "__main__" and False:
    pass
