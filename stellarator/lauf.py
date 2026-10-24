"""lauf.py — Stellarator-Pipeline, Orchestrator-Schnittstelle (fuer Hermes und von Hand).

  .venv/bin/python -m stellarator.lauf stellarator/faelle/w7x_standard.json
  .venv/bin/python -m stellarator.lauf FALL.json --schritte feld,feldlinien
  .venv/bin/python -m stellarator.lauf FALL.json --setze spulen.B0_achse_T=3.0 --name w7x_3T
  ... --bericht   kopiert die PNG nach bericht/bilder/<name>_*.png

Schritte (Reihenfolge fest, fehlende Vorstufen werden aus dem Ausgabeordner geladen
oder neu gerechnet):
  geometrie     Filamente, Kalibrierung auf B0, Wickelpaket-STL (analytisch)
  voxel         PicoGK: Voxelkoerper, Gehaeuse (Offset), SDF-Abstand -> Volumenanteile
  feld          Voxel-FFT-Solver, Validierung gegen Biot-Savart (Filament, exakt)
  feldlinien    Poincare-Schnitt phi=0, Rotationstransformation iota (beide Felder)
  rueckfuehrung |B| auf der Wickeloberflaeche, Lorentzkraefte je Spule -> VTP/PNG/JSON
Ausgabe: sim/stellarator/<name>/ (ergebnis.json sammelt alle Kennzahlen).
"""
from __future__ import annotations
import argparse, json, time, warnings
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .spulen import w7x_spulensatz, kalibriere, segmente, biot_savart, achse, rohr_dreiecke, schreibe_stl
from .picogk_bruecke import Gitter, voxelisiere
from .voxelsolver import stromdichte, VoxelFeld
from .feldlinien import ZylinderGitter, verfolge, iota

SCHRITTE = ["geometrie", "voxel", "feld", "feldlinien", "rueckfuehrung"]
PROJEKT = Path(__file__).resolve().parents[1]


def setze(fall: dict, zuweisung: str) -> None:
    """'a.b.c=wert' in das verschachtelte dict schreiben (wert als JSON, sonst String)."""
    pfad, wert = zuweisung.split("=", 1)
    try:
        wert = json.loads(wert)
    except json.JSONDecodeError:
        pass
    d = fall
    *kopf, letzter = pfad.split(".")
    for k in kopf:
        d = d.setdefault(k, {})
    d[letzter] = wert


class Lauf:
    def __init__(self, fall: dict, ordner: Path):
        self.fall, self.ordner = fall, ordner
        ordner.mkdir(parents=True, exist_ok=True)
        (ordner / "fall.json").write_text(json.dumps(fall, indent=2, ensure_ascii=False))
        self.erg_pfad = ordner / "ergebnis.json"
        self.erg = json.loads(self.erg_pfad.read_text()) if self.erg_pfad.exists() else {}
        self.erg["fall"] = fall["name"]
        self.spulen = self.gitter = self.idx = self.anteil = self.V = None

    def log(self, s):
        print(s, flush=True)

    def speichern(self):
        self.erg_pfad.write_text(json.dumps(self.erg, indent=2, ensure_ascii=False))

    # ------------------------------------------------------------------ geometrie
    def geometrie(self, schreiben=True):
        c = self.fall["spulen"]
        self.spulen = w7x_spulensatz(c.get("stroeme_Awdg"), n_punkte=c["n_punkte"])
        faktor = kalibriere(self.spulen, c["B0_achse_T"]) if c.get("B0_achse_T") else 1.0
        self.seg = segmente(self.spulen)
        if not schreiben:
            return
        self.log("[geometrie]")
        npc = [s for s in self.spulen if s.typ.startswith("NPC") and not s.meta["flip"]]
        strom = {s.typ: abs(s.strom) for s in self.spulen}
        Bphi0 = float(np.linalg.norm(biot_savart(achse(np.array([0.0])), self.seg)))
        tri = np.concatenate([rohr_dreiecke(s, c["wickel_breite_m"], c["wickel_hoehe_m"]) for s in self.spulen])
        schreibe_stl(self.ordner / "wickelpaket.stl", tri)
        json.dump({"spulen": [{"name": s.name, "typ": s.typ, "strom_Awdg": s.strom,
                               "punkte_m": s.punkte.round(6).tolist()} for s in self.spulen]},
                  open(self.ordner / "spulen.json", "w"))
        self.erg["geometrie"] = {
            "n_spulen": len(self.spulen), "kalibrierfaktor": faktor,
            "strom_Awdg_je_typ": strom,
            "strom_kA_je_windung_npc": {k: v / c["windungen_npc"] / 1e3 for k, v in strom.items() if k.startswith("NPC")},
            "B_achse_phi0_T": Bphi0,
            "spulenlaenge_m": {s.typ: s.laenge() for s in npc[:5]},
        }
        self.log(f"  {len(self.spulen)} Spulen, Faktor {faktor:.4f}, NPC1 {strom['NPC1']/c['windungen_npc']/1e3:.2f} kA/Wdg, "
                 f"B(phi=0) {Bphi0:.3f} T")
        self.speichern()

    # ---------------------------------------------------------------------- voxel
    def voxel(self, rechnen=True):
        c, s = self.fall["voxel"], self.fall["spulen"]
        self.gitter = Gitter.um(self.spulen, self.fall["solver"]["h_m"], self.fall["solver"]["rand_m"])
        vdir = self.ordner / "voxel"
        npz = vdir / "belegung.npz"
        if not npz.exists() and c.get("von"):        # Belegung eines anderen Falls wiederverwenden
            npz = self.ordner.parent / c["von"] / "voxel" / "belegung.npz"
        if not rechnen and npz.exists():
            d = np.load(npz)
            if np.allclose(d["ursprung"], self.gitter.ursprung) and tuple(d["n"]) == self.gitter.n:
                self.idx, self.anteil = d["idx"], d["anteil"]
                return
        self.log(f"[voxel] modus={c['modus']}")
        r = voxelisiere(self.spulen, self.gitter, vdir, s["wickel_breite_m"], s["wickel_hoehe_m"],
                        voxel_mm=c["voxel_mm"], gehaeuse_mm=c["gehaeuse_mm"], modus=c["modus"], log=self.log)
        self.idx, self.anteil = r.pop("idx"), r.pop("anteil")
        r.pop("volumen_gehaeuse_m3", None)   # PicoGK-Wert nach Boolean unzuverlaessig -> aus Netz
        if c["modus"] == "picogk":
            r |= self._stl_ausduennen(vdir, c.get("stl_ausduennen", 0.95))
        r["volumen_soll_m3"] = sum(sp.laenge() for sp in self.spulen) * s["wickel_breite_m"] * s["wickel_hoehe_m"]
        self.erg["voxel"] = r
        self.log(f"  Volumen: Soll {r['volumen_soll_m3']:.2f} m3, Gitter {r['volumen_gitter_m3']:.2f} m3"
                 + (f", Gehaeuse {r.get('volumen_gehaeuse_netz_m3', 0):.2f} m3" if "volumen_gehaeuse_netz_m3" in r else ""))
        self.speichern()

    def _stl_ausduennen(self, vdir: Path, rate: float) -> dict:
        """PicoGK-STL (Millionen Dreiecke) per Quadric-Dezimierung verkleinern, Rohdatei loeschen."""
        import pyvista as pv
        out = {}
        for roh, ziel, key in [("wickelpaket_voxel.stl", "wickelpaket_picogk.stl", "wickel"),
                               ("gehaeuse_voxel.stl", "gehaeuse_picogk.stl", "gehaeuse")]:
            if not (vdir / roh).exists():
                continue
            t0 = time.time()
            m = pv.read(vdir / roh)
            vol = m.volume / 1e9
            d = m.decimate(rate) if rate > 0 else m
            d.save(vdir / ziel)
            (vdir / roh).unlink()
            out[f"volumen_{key}_netz_m3"] = vol
            out[f"dreiecke_{key}"] = [m.n_cells, d.n_cells]
            self.log(f"  {roh}: {m.n_cells} -> {d.n_cells} Dreiecke ({time.time()-t0:.0f} s)")
        (vdir / "wickelpaket.vdb").unlink(missing_ok=True)
        for f in ("kandidaten.i32", "abstand.f32", "wickelpaket_eingabe.stl"):
            (vdir / f).unlink(missing_ok=True)
        return out

    # ----------------------------------------------------------------------- feld
    def feld(self, schreiben=True):
        J, self.sid = stromdichte(self.spulen, self.gitter, self.idx, self.anteil)
        self.J = J
        self.V = VoxelFeld(self.gitter, self.idx, J, log=self.log if schreiben else (lambda s: None))
        if not schreiben:
            return
        self.log("[feld] Validierung Voxel-FFT gegen Biot-Savart")
        phi = np.linspace(0, 2 * np.pi, 200, endpoint=False)
        X = achse(phi)
        Bv, Bb = self.V(X), biot_savart(X, self.seg)
        e_ax = np.linalg.norm(Bv - Bb, axis=1) / np.linalg.norm(Bb, axis=1)
        # Stichprobe um die Achse (Abstand <= 0.6 m), ausgewertet nach Abstand zum naechsten
        # Filament: nahe der Spule weichen Filament- und Volumenstrom physikalisch ab.
        # Der eigentliche Plasma-Vergleich laeuft auf Flussflaechen im Schritt feldlinien.
        from scipy.spatial import cKDTree
        rng = np.random.default_rng(0)
        ph = rng.random(6000) * 2 * np.pi
        a = achse(ph)
        Ra = np.hypot(a[:, 0], a[:, 1])
        rho, th = 0.6 * np.sqrt(rng.random(6000)), rng.random(6000) * 2 * np.pi
        R, Z = Ra + rho * np.cos(th), a[:, 2] + rho * np.sin(th)
        P = np.column_stack([R * np.cos(ph), R * np.sin(ph), Z])
        Bb_p = biot_savart(P, self.seg)
        e_p = np.linalg.norm(self.V(P) - Bb_p, axis=1) / np.linalg.norm(Bb_p, axis=1)
        d_fil, _ = cKDTree(np.vstack([s.punkte for s in self.spulen])).query(P)
        baender = {}
        for lo, hi in [(0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 9.0)]:
            m = (d_fil >= lo) & (d_fil < hi)
            if m.any():
                baender[f"{lo}-{hi}m"] = {"n": int(m.sum()), "median": float(np.median(e_p[m])),
                                          "p95": float(np.percentile(e_p[m], 95))}
        self.erg["feld"] = {
            "gitter": list(map(int, self.gitter.n)), "h_m": self.gitter.h, "t_loesung_s": self.V.t_loes,
            "fehler_achse_rel": {"median": float(np.median(e_ax)), "max": float(e_ax.max())},
            "fehler_nach_abstand_zum_filament": baender,
            "B_achse_T": {"min": float(np.linalg.norm(Bb, axis=1).min()), "mittel": float(np.linalg.norm(Bb, axis=1).mean()),
                          "max": float(np.linalg.norm(Bb, axis=1).max())},
        }
        fig, ax = plt.subplots(1, 2, figsize=(12, 4), dpi=110)
        ax[0].plot(np.degrees(phi), np.linalg.norm(Bb, axis=1), "k-", lw=2, label="Biot-Savart (Filament)")
        ax[0].plot(np.degrees(phi), np.linalg.norm(Bv, axis=1), "--", color="#d9480f", lw=1.5,
                   label=f"Voxel-FFT h={self.gitter.h*1000:.0f} mm")
        ax[0].set(xlabel="toroidaler Winkel phi [Grad]", ylabel="|B| auf der Achse [T]", title="Feld entlang der magnetischen Achse")
        ax[0].legend(); ax[0].grid(alpha=.3)
        ax[1].semilogy(d_fil, 100 * e_p, ".", ms=2, color="#1c7ed6", alpha=.5)
        ax[1].axvline(0.3, color="grey", ls=":")
        ax[1].set(xlabel="Abstand zum naechsten Spulenfilament [m]", ylabel="rel. Abweichung |B| [%]",
                  title="Voxel-FFT vs. Biot-Savart (6000 Punkte um die Achse)")
        ax[1].grid(alpha=.3, which="both")
        fig.tight_layout(); fig.savefig(self.ordner / "feld_validierung.png"); plt.close(fig)
        f = self.erg["feld"]
        self.log(f"  Achse: max {100*f['fehler_achse_rel']['max']:.2f} %; nach Abstand zum Filament: "
                 + ", ".join(f"{k}: {100*v['median']:.2f}/{100*v['p95']:.2f} %" for k, v in baender.items())
                 + " (Median/p95)")
        self.speichern()

    # ----------------------------------------------------------------- feldlinien
    def feldlinien(self):
        c = self.fall["feldlinien"]
        self.log("[feldlinien]")
        Ra, Za = float(achse(np.array([0.0]))[0, 0]), 0.0
        R0 = Ra + np.linspace(0.0, c["dR_max_m"], c["n_linien"])
        felder = {"Biot-Savart": lambda x: biot_savart(x, self.seg)}
        if self.V is not None:
            felder["Voxel-FFT"] = lambda x: self.V(x, ordnung=3)   # kubisch: etwas glatter fuer die Verfolgung
        res = {}
        fig, ax = plt.subplots(1, len(felder) + 1, figsize=(5.2 * (len(felder) + 1), 5), dpi=110)
        farben = plt.cm.viridis(np.linspace(0, 1, len(R0)))
        for k, (name, f) in enumerate(felder.items()):
            t0 = time.time()
            G = ZylinderGitter(f)
            pk, lost = verfolge(G, R0, np.zeros_like(R0), n_umlaeufe=c["umlaeufe"])
            io = np.abs(iota(pk, (Ra, Za)))
            with warnings.catch_warnings():          # sofort verlorene Linien: nur NaN
                warnings.simplefilter("ignore", RuntimeWarning)
                r_eff = np.nanmean(np.hypot(pk[..., 0] - Ra, pk[..., 1] - Za), axis=1)
            res[name] = {"iota": io.tolist(), "r_eff_m": r_eff.tolist(), "verloren": lost.tolist(),
                         "t_s": time.time() - t0}
            if name == "Biot-Savart" and self.V is not None:
                # Plasma-Vergleich: Punkte geschlossener Flussflaechen (nicht verlorene Linien)
                q = pk[~lost].reshape(-1, 2)
                q = q[np.isfinite(q[:, 0])][:: 5]
                x = np.column_stack([q[:, 0], np.zeros(len(q)), q[:, 1]])
                bb = biot_savart(x, self.seg)
                ef = np.linalg.norm(self.V(x) - bb, axis=1) / np.linalg.norm(bb, axis=1)
                self.erg.setdefault("feld", {})["fehler_flussflaechen_rel"] = {
                    "n": int(len(ef)), "median": float(np.median(ef)), "p95": float(np.percentile(ef, 95)),
                    "max": float(ef.max())}
                self.log(f"  Voxel vs. Biot-Savart auf Flussflaechen: Median {100*np.median(ef):.2f} %, "
                         f"max {100*ef.max():.2f} %")
            for i in range(len(R0)):
                ax[k].plot(pk[i, :, 0], pk[i, :, 1], ".", ms=0.8, color=farben[i])
            ax[k].plot(Ra, Za, "r+", ms=10)
            ax[k].set(aspect="equal", xlabel="R [m]", ylabel="Z [m]", title=f"Poincare phi=0 — {name}")
            ok = ~lost & (r_eff > 0.02)
            ax[-1].plot(r_eff[ok], io[ok], "o-" if k == 0 else "s--", label=name, ms=4)
            self.log(f"  {name}: iota {io[1]:.3f} (innen) .. {np.nanmax(io[ok]):.3f}, verloren {int(lost.sum())}/{len(R0)} "
                     f"({time.time()-t0:.1f} s)")
        ax[-1].axhline(1.0, color="grey", lw=.8, ls=":")
        ax[-1].set(xlabel="mittlerer Abstand zur Achse r_eff [m]", ylabel="iota", title="Rotationstransformation")
        ax[-1].legend(); ax[-1].grid(alpha=.3)
        fig.tight_layout(); fig.savefig(self.ordner / "poincare.png"); plt.close(fig)
        self.erg["feldlinien"] = res
        self.speichern()

    # -------------------------------------------------------------- rueckfuehrung
    def rueckfuehrung(self):
        import pyvista as pv
        self.log("[rueckfuehrung] Feld und Kraefte auf die Spulengeometrie")
        g, h = self.gitter, self.gitter.h
        ijk = np.unravel_index(self.idx, g.n)
        Bvox = np.stack([self.V.B[c][ijk] for c in range(3)], 1).astype(float)
        f = np.cross(self.J, Bvox) * h ** 3                       # N je Zelle
        n = len(self.spulen)
        F = np.stack([np.bincount(self.sid, weights=f[:, c], minlength=n) for c in range(3)], 1)
        innen = self.anteil > 0.5
        Bmax = float(np.linalg.norm(Bvox[innen], axis=1).max())
        # Flaechenmodell: analytisches Rohr, |B| an den Eckpunkten aus dem Voxelfeld
        c = self.fall["spulen"]
        tri = np.concatenate([rohr_dreiecke(s, c["wickel_breite_m"], c["wickel_hoehe_m"]) for s in self.spulen])
        pts, inv = np.unique(tri.reshape(-1, 3).round(7), axis=0, return_inverse=True)
        faces = np.column_stack([np.full(len(tri), 3), inv.reshape(-1, 3)]).ravel()
        mesh = pv.PolyData(pts, faces)
        mesh.point_data["B_T"] = np.linalg.norm(self.V(pts), axis=1)
        sid_tri = np.repeat(np.arange(n), [len(s.punkte) * 8 for s in self.spulen])
        mesh.cell_data["spule"] = sid_tri
        mesh.cell_data["F_netto_MN"] = np.linalg.norm(F, axis=1)[sid_tri] / 1e6
        mesh.save(self.ordner / "spulen_ergebnis.vtp")
        schwer = np.array([s.punkte.mean(0) for s in self.spulen])
        pfeile = pv.PolyData(schwer)
        pfeile["F"] = F / 1e6
        pfeile.save(self.ordner / "spulen_kraefte.vtp")
        # Bilder
        pl = pv.Plotter(off_screen=True, window_size=(1600, 1000))
        pl.add_mesh(mesh, scalars="B_T", cmap="inferno", scalar_bar_args={"title": "|B| Wickeloberflaeche [T]"})
        pl.add_arrows(schwer, F / 1e6, mag=0.6, color="#1c7ed6")
        pl.add_mesh(pv.Spline(achse(np.linspace(0, 2 * np.pi, 400)), 400), color="#2f9e44", line_width=4)
        pl.camera_position = [(14, -14, 11), (0, 0, 0), (0, 0, 1)]
        pl.screenshot(self.ordner / "spulen_B_kraefte.png"); pl.close()
        geh = self.ordner / "voxel" / "gehaeuse_picogk.stl"
        if geh.exists():
            # PicoGK-STL ist in mm; Ausschnitt ~1 Feldperiode um phi=0
            box = (3.5, 8.0, -3.2, 3.2, -2.5, 2.5)
            gm = pv.read(geh).scale(1e-3).clip_box(box, invert=False)
            pl = pv.Plotter(off_screen=True, window_size=(1600, 1000))
            pl.add_mesh(gm, color="#adb5bd", opacity=0.35)
            pl.add_mesh(mesh.clip_box(box, invert=False), scalars="B_T", cmap="inferno",
                        scalar_bar_args={"title": "|B| Wickeloberflaeche [T]"})
            pl.camera_position = [(13, -6, 5), (5.8, 0, 0), (0, 0, 1)]
            pl.reset_camera(); pl.camera.zoom(1.3)
            pl.screenshot(self.ordner / "picogk_gehaeuse.png"); pl.close()
        typ = {}
        for i, s in enumerate(self.spulen):
            typ.setdefault(s.typ, []).append(np.linalg.norm(F[i]) / 1e6)
        self.erg["rueckfuehrung"] = {
            "B_max_wickelpaket_T": Bmax,
            "B_max_oberflaeche_T": float(mesh.point_data["B_T"].max()),
            "B_max_oberflaeche_filament_T": float(np.linalg.norm(biot_savart(pts, self.seg), axis=1).max()),
            "verhaeltnis_Bmax_B0": Bmax / self.fall["spulen"]["B0_achse_T"] if self.fall["spulen"].get("B0_achse_T") else None,
            "F_netto_MN_je_typ": {k: {"mittel": float(np.mean(v)), "max": float(np.max(v))} for k, v in typ.items()},
            "F_summe_alle_MN": (F.sum(0) / 1e6).tolist(),
            "dateien": ["spulen_ergebnis.vtp", "spulen_kraefte.vtp", "spulen_B_kraefte.png"]
                       + (["picogk_gehaeuse.png"] if geh.exists() else []),
        }
        self.log(f"  B_max Wickelpaket {Bmax:.2f} T, Netto-Kraft NPC1 {np.mean(typ['NPC1']):.2f} MN, "
                 f"Summe aller Kraefte {np.linalg.norm(F.sum(0))/1e6:.3f} MN (soll ~0)")
        self.speichern()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stellarator-Pipeline")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--schritte", default=",".join(SCHRITTE))
    ap.add_argument("--setze", action="append", default=[], help="pfad.zum.wert=JSON (mehrfach)")
    ap.add_argument("--name", help="Ausgabename (Default: name aus dem Fall)")
    ap.add_argument("--bericht", action="store_true", help="PNG nach bericht/bilder/<name>_*.png kopieren")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text())
    for z in a.setze:
        setze(fall, z)
    if a.name:
        fall["name"] = a.name
    schritte = [s for s in a.schritte.split(",") if s]
    unbekannt = set(schritte) - set(SCHRITTE)
    if unbekannt:
        ap.error(f"unbekannte Schritte {unbekannt}; erlaubt: {SCHRITTE}")
    L = Lauf(fall, PROJEKT / "sim" / "stellarator" / fall["name"])
    t0 = time.time()
    L.geometrie(schreiben="geometrie" in schritte)
    spaeter = {"feld", "feldlinien", "rueckfuehrung"}
    if "voxel" in schritte or spaeter & set(schritte):
        L.voxel(rechnen="voxel" in schritte)
    if {"feld", "rueckfuehrung"} & set(schritte) or "feldlinien" in schritte:
        L.feld(schreiben="feld" in schritte)
    if "feldlinien" in schritte:
        L.feldlinien()
    if "rueckfuehrung" in schritte:
        L.rueckfuehrung()
    L.erg["laufzeit_s"] = time.time() - t0
    L.speichern()
    if a.bericht:
        import shutil
        ziel = PROJEKT / "bericht" / "bilder"
        ziel.mkdir(parents=True, exist_ok=True)
        for png in sorted(L.ordner.glob("*.png")):
            shutil.copy2(png, ziel / f"{fall['name']}_{png.name}")
        print(f"Bilder -> {ziel}")
    print(f"FERTIG {L.ordner} ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
