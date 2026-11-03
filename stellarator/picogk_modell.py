"""picogk_modell.py — komplettes 3D-Modell eines Entwurfs (gekoppelte Studie) in PicoGK.

  .venv/bin/python -m stellarator.picogk_modell bauen  --von doe1/0169 [--voxel 40] [--name 0169]
  .venv/bin/python -m stellarator.picogk_modell bilder --name 0169
  .venv/bin/python -m stellarator.picogk_modell alle   [--voxel 40]       # alle zulaessigen + Vergleichsentwuerfe
  .venv/bin/python -m stellarator.picogk_modell vergleich                 # Tabelle + Bild aller Modelle

Ablauf: Python liest das FE-Modell des Entwurfs (struktur.vtu: Knoten der Spulenrohre in fester Reihenfolge
(Station, a, c)) und gibt PicoGK nur Geometriedaten: je Station die Rechtecke von Gehaeuse-Aussenkontur,
Verguss-Aussenkontur und Wickelpaket, die Verbinder-Oberflaechen, den Plasmarand (VMEC) und die Lagerorte.
PicoGK (picogk/StellaratorModell) baut daraus die Koerper (Netz -> Voxel, Boolesche Differenz fuer Gehaeuse und
Verguss, Offsets des Plasmas fuer die Package-Schichten, Lattice-Staebe + Zylinder fuer die Lager), prueft
Ueberschneidungen und schreibt STL. Python dezimiert die Netze, rechnet Volumina (gegen das FE-Modell) und rendert.

Ablage: sim/kopplung/modell3d/<name>/ (auftrag.json, *.stl dezimiert, pruefung.json, Bilder)
Package-Schichten (Annahme, Groessenordnung ARIES-CS, kopplung.ANNAHMEN package_min_m = 1,0 m):
  Erstwand + Blanket 0-0,55 m, Abschirmung 0,55-0,88 m, Vakuumgefaess 0,88-1,00 m ab Plasmarand.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KOP = ROOT / "sim" / "kopplung"
AUS = KOP / "modell3d"
APP = ROOT / "picogk" / "StellaratorModell"
BIN = APP / "bin" / "Release" / "net9.0" / "StellaratorModell"
PACKAGE = [("erstwand_blanket", 550.0), ("abschirmung", 880.0), ("vakuumgefaess", 1000.0)]
TEILE = ["plasma", "package_erstwand_blanket", "package_abschirmung", "package_vakuumgefaess",
         "wickelpaket", "verguss", "gehaeuse", "verbinder", "lager"]
PRUEF = ["pruefung_gehaeuse_ueberschneidung", "pruefung_package_ueberschneidung", "pruefung_verbinder_im_wickelpaket"]
FARBEN = {"plasma": "#e87ba4", "package_erstwand_blanket": "#eda100", "package_abschirmung": "#1baf7a",
          "package_vakuumgefaess": "#9aa0a6", "wickelpaket": "#eb6834", "verguss": "#6250d6",
          "gehaeuse": "#2a78d6", "verbinder": "#0b3d91", "lager": "#52514e"}
NAME = "Thomas Schmiegelt"


def ring_volumen(E: np.ndarray) -> float:
    """Vorzeichenbehaftetes Volumen des geschlossenen Rohrs aus Stationsrechtecken E (N, 4, 3), Dreiecke wie in C#."""
    N = len(E); v = 0.0
    for i in range(N):
        j = (i + 1) % N
        for e in range(4):
            f = (e + 1) % 4
            for a, b, c in ((E[i, e], E[j, e], E[j, f]), (E[i, e], E[j, f], E[i, f])):
                v += np.dot(a, np.cross(b, c)) / 6
    return float(v)


def flaeche_stl(pfad: Path, P: np.ndarray, T: np.ndarray) -> None:
    import pyvista as pv
    pv.PolyData(P, np.c_[np.full(len(T), 3), T].ravel()).save(pfad, binary=True)


def daten(von: str):
    import pyvista as pv
    st, nr = von.split("/"); po = KOP / st / "punkte" / nr
    e = json.loads((po / "ergebnis.json").read_text()); p = e["param"]
    g = pv.read(po / "struktur.vtu")
    spule = np.asarray(g.cell_data["spule"]); n_sp = int(spule.max() + 1)
    nw, nwp = int(p.get("n_wand", 2)), int(p.get("n_wp", 4)); A = 2 * nw + 2 + nwp
    N = e["struktur"].get("stationen")            # Tragwerksversuche (test) speichern es nicht -> aus dem Netz
    N = int(N) if N else int(round(np.sum(spule == 0) / A ** 2))
    X = np.asarray(g.points, float)
    K = X[: n_sp * N * (A + 1) ** 2].reshape(n_sp, N, A + 1, A + 1, 3)
    grenzen = [(0, A), (nw, A - nw), (nw + 1, A - nw - 1)]
    E = np.empty((n_sp, N, 3, 4, 3))
    for l, (lo, hi) in enumerate(grenzen):
        E[:, :, l] = np.stack([K[:, :, lo, lo], K[:, :, hi, lo], K[:, :, hi, hi], K[:, :, lo, hi]], 2)
    if ring_volumen(E[0, :, 0]) < 0:                     # Umlaufsinn so, dass Normalen nach aussen zeigen
        E = E[:, :, :, ::-1]
    return e, p, g, E, K, A, N, n_sp


def baue(von: str, name: str, voxel: float, voxel_bild: float = 80.0) -> dict:
    import pyvista as pv
    o = AUS / name; o.mkdir(parents=True, exist_ok=True)
    e, p, g, E, K, A, N, n_sp = daten(von)
    (o / "spulen.f32").write_bytes((E * 1000).astype(np.float32).tobytes())
    # Verbinder: Oberflaeche der Verbinderzellen (geteilte Flaechen innen fallen weg)
    verb = g.extract_cells(np.where(np.asarray(g.cell_data["spule"]) == -1)[0])
    vs = verb.extract_surface(algorithm="dataset_surface").triangulate()
    vs.points *= 1000.0; vs.save(o / "verbinder_ein.stl", binary=True)
    # Plasmarand (VMEC s = 1, nphi 200 x ntheta 80, periodisch in beiden Richtungen)
    R = np.load(KOP / von.split("/")[0] / "punkte" / von.split("/")[1] / "plasma_rand.npy").astype(float) * 1000.0
    nph, nth = 200, 80
    i, j = np.meshgrid(np.arange(nph), np.arange(nth), indexing="ij")
    a0 = i * nth + j; a1 = ((i + 1) % nph) * nth + j; a2 = ((i + 1) % nph) * nth + (j + 1) % nth; a3 = i * nth + (j + 1) % nth
    T = np.r_[np.c_[a0.ravel(), a1.ravel(), a2.ravel()], np.c_[a0.ravel(), a2.ravel(), a3.ravel()]]
    if np.einsum("ij,ij->i", R[T[:, 0]], np.cross(R[T[:, 1]], R[T[:, 2]])).sum() < 0:   # Normalen nach aussen
        T = T[:, ::-1]
    flaeche_stl(o / "plasma_ein.stl", R, T)
    # Lager wie hexmodell (LAGER_ORT "beide"): Flecken auf der Aussenseite (a = A) am kleinsten / groessten Bahnradius
    rl = p["r_lager_m"] * 1000; staebe = []; innen_R, aussen_R, zi, za = [], [], [], []
    mitte = E[:, :, 2].mean(2) * 1000                                    # Wickelpaketmitte je Station (mm)
    flaeche = K[:, :, A].mean(2) * 1000                                   # Mitte der Aussenseite a = A
    breite = np.linalg.norm(K[:, :, A, 0] - K[:, :, A, A], axis=-1).mean() * 1000
    for k in range(n_sp):
        Rk = np.hypot(mitte[k, :, 0], mitte[k, :, 1])
        ort = p.get("lager_ort", "aussen")         # ohne Angabe: damaliger Standard von hexmodell (aussen)
        for art, il in [x for x in (("innen", int(np.argmin(Rk))), ("aussen", int(np.argmax(Rk)))) if ort in (x[0], "beide")]:
            d = np.linalg.norm(flaeche[k] - flaeche[k, il], axis=1)
            for ist in np.where(d <= rl)[0] if (d <= rl).sum() >= 2 else np.argsort(d)[:2]:
                staebe.append({"art": art, "k": k, "punkt": flaeche[k, ist]})
            (innen_R if art == "innen" else aussen_R).append(np.hypot(*flaeche[k, il, :2]))
            (zi if art == "innen" else za).append(flaeche[k, il, 2])
    zyl = []                                                             # Stuetzzylinder 0,3 m vor dem naechsten Flecken
    if innen_R:
        Ri = min(innen_R) - 300.0
        zyl.append({"r_innen_mm": Ri - 800, "r_aussen_mm": Ri, "z0_mm": min(zi) - rl, "z1_mm": max(zi) + rl})
    if aussen_R:
        Ra = max(aussen_R) + 300.0
        zyl.append({"r_innen_mm": Ra, "r_aussen_mm": Ra + 800, "z0_mm": min(za) - rl, "z1_mm": max(za) + rl})
    st_json = []
    for s in staebe:
        q = s["punkt"]; r = np.hypot(q[0], q[1]); u = q[:2] / r
        ziel = (Ri - 100) if s["art"] == "innen" else (Ra + 100)
        b = np.r_[u * ziel, q[2]]
        a_ = q - np.r_[u, 0] * (150 if s["art"] == "aussen" else -150)    # leicht in die Wand (wird abgezogen)
        st_json.append({"a": a_.tolist(), "b": b.tolist(), "r_mm": float(0.5 * breite)})
    auftrag = {"voxel_mm": voxel, "ausgabe": str(o / "roh"), "spulen_bin": str(o / "spulen.f32"), "n_spulen": n_sp,
               "n_stationen": N, "verbinder_stl": str(o / "verbinder_ein.stl"), "plasma_stl": str(o / "plasma_ein.stl"),
               "package": [{"name": n, "bis_mm": b} for n, b in PACKAGE],
               "lager": {"staebe": st_json, "zylinder": zyl}, "export": False}
    if not BIN.exists():
        env = os.environ | {"DOTNET_ROOT": str(Path.home() / ".dotnet"), "PATH": f"{Path.home() / '.dotnet'}:{os.environ['PATH']}"}
        subprocess.run(["dotnet", "build", "-c", "Release", "-v", "q"], cwd=APP, env=env, check=True)

    def lauf(vox: float, export: bool, ziel: str) -> tuple[dict, float]:
        (o / f"auftrag_{ziel}.json").write_text(json.dumps(auftrag | {"voxel_mm": vox, "export": export,
                                                                       "ausgabe": str(o / ziel)}, indent=1))
        t0 = time.time()
        r = subprocess.run([str(BIN), str(o / f"auftrag_{ziel}.json")],
                           env=os.environ | {"DOTNET_ROOT": str(Path.home() / ".dotnet")}, capture_output=True, text=True)
        (o / f"picogk_{ziel}.log").write_text(r.stdout + r.stderr)
        if r.returncode != 0:
            raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
        return json.loads((o / ziel / "ergebnis.json").read_text()), time.time() - t0

    # Lauf 1 (Pruefung): Volumina + Ueberschneidungen bei voxel, ohne Netzexport (Volumen rechnet PicoGK aus dem Netz)
    if voxel == voxel_bild:     # Katalog: ein Lauf fuer Pruefung und Bild
        erg2, t_pico = lauf(voxel, True, "bild"); erg1, t_bild = erg2, 0.0
        (o / "pruefung").mkdir(exist_ok=True)
        for t in PRUEF:
            if (o / "bild" / f"{t}.stl").exists(): shutil.copy(o / "bild" / f"{t}.stl", o / "pruefung" / f"{t}.stl")
    else:
        erg1, t_pico = lauf(voxel, False, "pruefung")
        # Lauf 2 (Bild): grob, mit Netzexport; Netze ausduennen (fast_simplification)
        erg2, t_bild = lauf(voxel_bild, True, "bild")
    vol = erg1["volumen_m3"]
    import fast_simplification as fs
    dreiecke = {}
    for t in TEILE:
        m = pv.read(o / "bild" / f"{t}.stl")
        dreiecke[t] = int(m.n_cells)
        if m.n_cells > 150000:
            m = fs.simplify_mesh(m, target_reduction=1 - 150000 / m.n_cells)
        if m.n_cells:
            m.save(o / f"{t}.stl", binary=True)
        else:
            (o / f"{t}.stl").write_bytes(b"")
    for t in PRUEF:   # Pruefkoerper aus Lauf 1 (fein); leer = keine Ueberschneidung
        q = o / "pruefung" / f"{t}.stl"
        if q.exists() and q.stat().st_size > 84:
            shutil.copy(q, o / f"{t}.stl")
    shutil.rmtree(o / "roh", ignore_errors=True); shutil.rmtree(o / "pruefung"); shutil.rmtree(o / "bild")
    (o / "spulen.f32").unlink()
    s = e["struktur"]
    soll = {"wickelpaket": s["wickelpaket"]["volumen_m3"], "verguss": s["verguss"]["volumen_m3"],
            "gehaeuse": s["stahl"]["volumen_m3"], "verbinder": s.get("verbinder", {}).get("volumen_m3", 0)}
    ring = {"wickelpaket": sum(ring_volumen(E[k, :, 2]) for k in range(n_sp)),
            "verguss_aussen": sum(ring_volumen(E[k, :, 1]) for k in range(n_sp)),
            "gehaeuse_aussen": sum(ring_volumen(E[k, :, 0]) for k in range(n_sp))}
    pr = {"von": von, "voxel_mm": voxel, "voxel_bild_mm": voxel_bild, "picogk_s": t_pico, "bild_s": t_bild,
          "volumen_m3": vol, "volumen_bild_m3": erg2["volumen_m3"], "soll_fe_m3": soll,
          "ring_exakt_m3": {"wickelpaket": ring["wickelpaket"], "verguss": ring["verguss_aussen"] - ring["wickelpaket"],
                            "gehaeuse": ring["gehaeuse_aussen"] - ring["verguss_aussen"]},
          "abweichung_zu_fe": {k: vol[k] / soll[k] - 1 for k in soll if soll[k]},
          "dreiecke_bild": dreiecke, "zylinder": zyl, "lagerstaebe": len(st_json), "zeiten_pruefung": erg1["zeiten_s"],
          "param": p, "spulen": n_sp, "stationen": N,
          "geometrisch_ok": bool(vol["pruefung_package_ueberschneidung"] < 0.5 and vol["pruefung_gehaeuse_ueberschneidung"] < 0.5)}
    (o / "pruefung.json").write_text(json.dumps(pr, indent=1, default=float))
    print(name, f"PicoGK {t_pico:.0f} s + Bild {t_bild:.0f} s", {k: round(v, 1) for k, v in vol.items()})
    print("  Abweichung Voxel/FE:", {k: f"{100*v:+.1f} %" for k, v in pr["abweichung_zu_fe"].items()})
    return pr


BESCHRIFTUNG = {"plasma": ("Plasma", "plasma"), "package_erstwand_blanket": ("Erstwand + Blanket", "first wall + blanket"),
                "package_abschirmung": ("Abschirmung", "shield"), "package_vakuumgefaess": ("Vakuumgefäß", "vacuum vessel"),
                "wickelpaket": ("Wickelpaket (Supraleiter)", "winding pack (superconductor)"), "verguss": ("Verguss", "potting"),
                "gehaeuse": ("Spulengehäuse (Stahl)", "coil case (steel)"), "verbinder": ("Verbinder (Stahl)", "connectors (steel)"),
                "lager": ("Lager / Stützring (schematisch)", "bearings / support ring (schematic)")}
# Treppenschnitt: je Schicht ein anderer Keil herausgeschnitten (phi von -90 Grad bis Winkel), damit sich die
# deckungsgleichen Grenzflaechen benachbarter Schichten nicht ueberlagern und jede Schicht sichtbar wird.
KEIL_BIS = {"plasma": None, "package_erstwand_blanket": -40, "package_abschirmung": -25, "package_vakuumgefaess": -10,
            "wickelpaket": 5, "verguss": 5, "gehaeuse": 5, "verbinder": 5, "lager": 40}


def ohne_keil(m, phi_a: float, phi_b: float):
    """Entfernt den Keil phi_a..phi_b (Grad, um die z-Achse) aus dem Netz m."""
    import pyvista as pv
    a, b = np.radians(phi_a), np.radians(phi_b)
    teile = [m.clip(normal=(np.sin(a), -np.cos(a), 0), origin=(0, 0, 0), invert=False),
             m.clip(normal=(-np.sin(b), np.cos(b), 0), origin=(0, 0, 0), invert=False)]
    teile = [t for t in teile if t.n_cells]
    return pv.merge(teile) if teile else None


def bilder(name: str, en: bool = False, arten=("gesamt", "schnitt")) -> None:
    import pyvista as pv
    pv.OFF_SCREEN = True
    o = AUS / name
    netze = {t: pv.read(o / f"{t}.stl") for t in TEILE if (o / f"{t}.stl").stat().st_size > 0}
    for art in arten:
        pl = pv.Plotter(window_size=(1600, 1100)); pl.set_background("white")
        leg = []
        for t, m in netze.items():
            if art == "gesamt" and t.startswith("package") and t != "package_vakuumgefaess":
                continue
            if art == "gesamt" and t == "lager":          # Ring vorne offen, sonst verdeckt er die Spulen
                m = ohne_keil(m, -150, -10)
                if m is None: continue
            if art == "schnitt" and KEIL_BIS[t] is not None:
                m = ohne_keil(m, -100, KEIL_BIS[t])
                if m is None: continue
            op = 0.35 if (art == "gesamt" and t == "package_vakuumgefaess") else 1.0
            pl.add_mesh(m, color=FARBEN[t], opacity=op, smooth_shading=True, specular=0.15)
            leg.append([BESCHRIFTUNG[t][1 if en else 0], FARBEN[t]])
        pl.add_legend(leg, bcolor=None, border=False, size=(0.2, 0.22), loc="upper left", face="rectangle")
        pl.add_text(NAME, position="lower_right", font_size=9, color="#52514e")
        if art == "schnitt":
            pl.view_vector((np.cos(np.radians(-75)), np.sin(np.radians(-75)), 1.1)); pl.reset_camera(); pl.camera.zoom(1.4)
        else:
            pl.view_vector((0.55, -1.0, 0.62)); pl.reset_camera(); pl.camera.zoom(1.2)
        pl.screenshot(str(o / f"{art}{'_en' if en else ''}.png"))
        pl.close()
    print(o / "gesamt.png", o / "schnitt.png")


KATALOG = Path(os.environ.get("FUSION_KATALOG", ROOT / "sim" / "kopplung" / "katalog3d"))   # Verweis auf zweite Platte


def liste_bericht(n_knapp: int = 5) -> list[tuple[str, str]]:
    """Liste 1: zulaessige (bereinigt) + knapp verfehlte + in doe1 zulaessige, mit Standardnetz herausgefallene +
    Tragwerksversuche A und E."""
    erg = json.loads((ROOT / "daten" / "doe1_auswertung.json").read_text()); Z = erg["zeilen"]
    nah = sorted([nr for nr, z in Z.items() if not z["alle_ok"]], key=lambda nr: -Z[nr]["robust"])[:n_knapp]
    raus = [nr for nr in erg["zulaessig_roh"] if nr not in erg["zulaessig"]]
    out = [(f"{Z[nr]['quelle']}/{nr}", nr) for nr in erg["zulaessig"] + nah + raus]
    return out + [("ersatz1/0003", "V3"), ("ersatz1/0001", "V1"), ("test/0004", "E_test"), ("test/0000", "A_test")]


def liste_katalog() -> list[tuple[str, str]]:
    """Liste 2: alle geometrisch darstellbaren Entwuerfe (keine Durchdringung der Gehaeuse), bereinigt."""
    erg = json.loads((ROOT / "daten" / "doe1_auswertung.json").read_text())
    return [(f"{z['quelle']}/{nr}", nr) for nr, z in erg["zeilen"].items() if z["durchdringung"] == 0]


def main():
    global AUS
    ap = argparse.ArgumentParser(); ap.add_argument("befehl", choices=["bauen", "bilder", "liste1", "katalog"])
    ap.add_argument("--von"); ap.add_argument("--name"); ap.add_argument("--voxel", type=float, default=40.0)
    ap.add_argument("--voxel_bild", type=float, default=80.0)
    a = ap.parse_args()
    if a.befehl == "bauen":
        baue(a.von, a.name or a.von.replace("/", "_"), a.voxel, a.voxel_bild)
        for en in (False, True): bilder(a.name or a.von.replace("/", "_"), en)
    elif a.befehl == "bilder":
        for en in (False, True): bilder(a.name, en)
    else:
        if a.befehl == "katalog":
            AUS = KATALOG; KATALOG.mkdir(parents=True, exist_ok=True)
            liste = liste_katalog()
        else:
            liste = liste_bericht()
        print(len(liste), "Modelle:", [n for _, n in liste], flush=True)
        for von, name in liste:
            st, nr = von.split("/")
            if (AUS / name / "pruefung.json").exists() or not (KOP / st / "punkte" / nr / "struktur.vtu").exists():
                continue
            try:
                baue(von, name, a.voxel, a.voxel_bild)
                for en in (False, True):
                    bilder(name, en, ("gesamt",) if a.befehl == "katalog" else ("gesamt", "schnitt"))
            except Exception as ex:
                print("FEHLER", name, ex, flush=True)


if __name__ == "__main__":
    main()
