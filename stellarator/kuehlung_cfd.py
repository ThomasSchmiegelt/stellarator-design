"""kuehlung_cfd.py — Stroemung im Kuehlsegment (kuehlung_segment.py) mit FluidX3D (Lattice-Boltzmann, GPU).

    .venv/bin/python -m stellarator.kuehlung_cfd --name a [--dx 12] [--t_phys 60] [--probe]

FluidX3D (https://github.com/ProjectPhysX/FluidX3D) steht unter einer eigenen,
nicht-kommerziellen Lizenz, nicht MIT. Es wird NICHT mitgeliefert: Arbeitskopie v3.8 in ~/fluidx3d_stellarator.
Geaendert werden dort nur src/setup.cpp (aus fluidx3d/setup_kuehlsegment.cpp) und Schalter in src/defines.hpp.

Ablauf: Wasserraum-STL in Gitterkoordinaten umrechnen, Fall-Datei schreiben, FluidX3D bauen und unter dem
Speicherwaechter rechnen (GPU nur nach Freigabe durch den User, sie gehoert Hermes).
Einheiten: dx [mm] Gitterweite; u_lat Gittergeschwindigkeit im Eintrittsrohr; dt = dx u_lat / v_ein;
Viskositaet Wasser 1e-6 m2/s, LES-Turbulenzmodell (SUBGRID) haelt die Rechnung stabil.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess
from pathlib import Path
import numpy as np

from .lauf import PROJEKT
from .kuehlung_segment import WURZEL
from .speicherwaechter import starte_begrenzt

FX = Path.home() / "fluidx3d_stellarator"
SETUP = PROJEKT / "fluidx3d" / "setup_kuehlsegment.cpp"
NU = 1e-6
SCHALTER = {"BENCHMARK": False, "EQUILIBRIUM_BOUNDARIES": True, "SUBGRID": True, "FP16S": True}


def vorbereiten(o: Path, a) -> dict:
    import pyvista as pv
    au = json.loads((o / "auslegung.json").read_text())
    dx = a.dx / 1000
    c = o / "cfd"; c.mkdir(exist_ok=True)
    bel = o / "wasser_belegung.bin"
    if bel.exists():
        # Belegung direkt aus PicoGK (Gitterzelle = PicoGK-Voxel). FluidX3D-Voxelisierung des Netzes kippte einzelne
        # Lagen (Strahlparitaet an fast waagerechten Flaechen) -> Sperrschicht im Kuehlband, f6-f9
        kopf = np.fromfile(bel, np.int32, 6); o_mm = np.fromfile(bel, np.float32, 4, offset=24)
        if abs(o_mm[3] - a.dx) > 1e-3:
            raise SystemExit(f"Gitterweite {a.dx} mm muss der PicoGK-Voxelgroesse {o_mm[3]} mm entsprechen")
        nx, ny, nz = kopf[3:]
        B = np.fromfile(bel, np.uint8, offset=40).reshape(nz, ny, nx)
        pad = 3
        N = np.array([nx, ny, nz]) + 2 * pad
        lo = o_mm[:3].astype(float) / 1000 - pad * dx
        G = np.zeros((N[2], N[1], N[0]), np.uint8); G[pad:-pad, pad:-pad, pad:-pad] = B
        G.tofile(c / "belegung.bin"); quelle = str(c / "belegung.bin")
    else:
        w = pv.read(o / "wasser.stl").scale(1e-3)                      # m
        lo = np.array(w.bounds[0::2]) - 3 * dx
        N = np.ceil((np.array(w.bounds[1::2]) + 3 * dx - lo) / dx).astype(int)
        w.points = (w.points - lo) / dx
        w.save(c / "wasser_gitter.stl", binary=True); quelle = str(c / "wasser_gitter.stl")
    v_ein = au["auslegung"]["v_ein_m_s"]; v_aus = au["auslegung"]["v_aus_m_s"]
    dt = dx * a.u_lat / v_ein
    schritte = int(round(a.t_phys / dt / a.stat)) * a.stat
    rohre = {}
    for k in ("ein", "aus"):
        r = au["lage"]["rohre"][k]
        rohre[k] = {"ende": ((np.array(r["ende_m"]) - lo) / dx).tolist(), "achse": r["achse"], "r": r["d_mm"] / 2000 / dx}
    fall = {"dx_m": dx, "dt_s": dt, "N": N.tolist(), "ursprung_m": lo.tolist(), "nu_lat": NU * dt / dx ** 2,
            "u_ein_lat": a.u_lat, "u_aus_lat": a.u_lat * v_aus / v_ein, "schritte": schritte, "t_phys_s": schritte * dt,
            "v_ein_m_s": v_ein, "v_aus_m_s": v_aus, "rohre": rohre, "zellen": int(np.prod(N)),
            "vram_gb_schaetzung": float(np.prod(N)) * 55 / 1e9}
    zeilen = [quelle, str(c), *map(str, N), f"{fall['nu_lat']:.6e}", str(a.u_lat),
              f"{fall['u_aus_lat']:.6f}", "1.0", str(schritte), str(a.stat), str(max(schritte // 2, a.stat))]
    for k in ("ein", "aus"):
        zeilen += [f"{v:.4f}" for v in rohre[k]["ende"]] + [f"{v:.6f}" for v in rohre[k]["achse"]] + [f"{rohre[k]['r']:.4f}"]
    (c / "fall.txt").write_text(" ".join(zeilen) + "\n")
    (c / "fall.json").write_text(json.dumps(fall, indent=1))
    return fall


def bauen() -> None:
    """setup.cpp und Schalter in die Arbeitskopie, kompilieren (ohne Grafik)."""
    shutil.copy(SETUP, FX / "src" / "setup.cpp")
    d = (FX / "src" / "defines.hpp").read_text().splitlines()
    for i, z in enumerate(d):
        for k, an in SCHALTER.items():
            if z.lstrip("/").startswith(f"#define {k} ") or z.lstrip("/") == f"#define {k}":
                d[i] = ("" if an else "//") + z.lstrip("/")
    (FX / "src" / "defines.hpp").write_text("\n".join(d) + "\n")
    r = subprocess.run(["make", "Linux", f"-j{4}"], cwd=FX, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])


def rechnen(o: Path, fall: dict, max_gb: float) -> dict:
    c = o / "cfd"
    for f in c.glob("feld_*.bin"):
        f.unlink()
    return starte_begrenzt([str(FX / "bin" / "FluidX3D")], c / "fluidx3d.log", max_gb, cwd=str(FX),
                           env={"KUEHL_FALL": str(c / "fall.txt")}, timeout_s=6 * 3600)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="a")
    ap.add_argument("--dx", type=float, default=12.0, help="Gitterweite [mm]")
    ap.add_argument("--u_lat", type=float, default=0.1, help="Gittergeschwindigkeit im Eintrittsrohr")
    ap.add_argument("--t_phys", type=float, default=60.0, help="physikalische Zeit [s]")
    ap.add_argument("--stat", type=int, default=2000, help="Schritte zwischen Messungen")
    ap.add_argument("--probe", action="store_true", help="nur kurzer Probelauf (2 Messungen)")
    ap.add_argument("--max_gb", type=float, default=8.0)
    a = ap.parse_args(argv)
    o = WURZEL / a.name
    if a.probe:
        a.t_phys = 0
    fall = vorbereiten(o, a)
    if a.probe:
        fall["schritte"] = 2 * a.stat
        t = (o / "cfd" / "fall.txt").read_text().split()
        t[9], t[11] = str(2 * a.stat), str(2 * a.stat)
        (o / "cfd" / "fall.txt").write_text(" ".join(t) + "\n")
    print(json.dumps({k: v for k, v in fall.items() if k != "rohre"}, indent=1), flush=True)
    bauen()
    r = rechnen(o, fall, a.max_gb)
    print(r)
    print((o / "cfd" / "stat.txt").read_text()[-1500:] if (o / "cfd" / "stat.txt").exists() else "keine stat.txt")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------------------------- Auswertung
def lese_feld(o: Path, datei: Path | None = None) -> dict:
    """Letztes feld_*.bin: Wasserzellen mit Lage [m], Geschwindigkeit [m/s], Druck relativ zum Austritt [Pa]."""
    c = o / "cfd"; f = json.loads((c / "fall.json").read_text())
    datei = datei or max(c.glob("feld_*.bin"), key=lambda p: int(p.stem.split("_")[1]))
    with open(datei, "rb") as h:
        M = int(np.frombuffer(h.read(8), np.uint64)[0])
        idx = np.frombuffer(h.read(4 * M), np.uint32).astype(np.int64)
        fl = np.frombuffer(h.read(M), np.uint8)
        w = np.frombuffer(h.read(16 * M), np.float32).reshape(M, 4)
    Nx, Ny, Nz = f["N"]; dx, dt = f["dx_m"], f["dt_s"]
    ijk = np.stack([idx % Nx, (idx // Nx) % Ny, idx // (Nx * Ny)], 1)
    c_si = dx / dt
    return {"fall": f, "ijk": ijk, "x": np.array(f["ursprung_m"]) + ijk * dx, "flag": fl,
            "u": w[:, :3].astype(np.float64) * c_si, "p": (w[:, 3].astype(np.float64) - 1.0) / 3.0 * 1000.0 * c_si ** 2,
            "t_s": int(datei.stem.split("_")[1]) * dt, "datei": datei.name}


def auswerten(o: Path) -> dict:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    F = lese_feld(o); f = F["fall"]; x, u, p = F["x"], F["u"], F["p"]
    au = json.loads((o / "auslegung.json").read_text()); auf = json.loads((o / "auftrag.json").read_text())
    dx = f["dx_m"]; dA = dx * dx; phi = np.degrees(np.arctan2(x[:, 1], x[:, 0]))
    erg = {"t_phys_s": F["t_s"], "feld": F["datei"]}
    # 1) Bohrungen: Volumenstrom je Loch (Zellen im Lochzylinder, Mittelebene der Platte)
    from scipy.spatial import cKDTree
    L = np.array(auf["loecher"]).reshape(-1, 7) if auf.get("mit_platte", True) else np.zeros((0, 7))
    A, B, r = L[:, :3] / 1000, L[:, 3:6] / 1000, L[:, 6] / 1000
    baum = cKDTree(x) if len(L) else None
    q_loch = []
    for a_, b_, rr in zip(A, B, r):
        m, e = (a_ + b_) / 2, (b_ - a_) / np.linalg.norm(b_ - a_)
        ids = np.array(baum.query_ball_point(m, rr + 2 * dx))
        if len(ids) == 0:
            q_loch.append(0.0); continue
        d = x[ids] - m; t = d @ e; rad = np.linalg.norm(d - t[:, None] * e, axis=1)
        sel = ids[(np.abs(t) < 0.6 * dx) & (rad < rr + 0.5 * dx)]
        q_loch.append(float((u[sel] @ e).sum() * dA * (dx / max(dx, 1e-9))))   # eine Zellschicht
    q_loch = np.array(q_loch)
    Q_soll = au["auslegung"]["volumenstrom_m3_s"]
    if len(q_loch):
      erg["loecher"] = {"Q_m3_s": q_loch.tolist(), "summe_m3_s": float(q_loch.sum()), "soll_m3_s": Q_soll,
                        "max_min": float(q_loch.max() / max(q_loch.min(), 1e-12)),
                        "streuung_rel": float(q_loch.std() / q_loch.mean())}
    # 2) Gyroid-Kern: Durchfluss in Toroidalrichtung ueber dem Umfang (Schnitt in Kernmitte, 24 Sektoren)
    k0, k1 = au["lage"]["winkel_grad"]["kern"]; km = 0.5 * (k0 + k1)
    from .kuehlung_segment import rand_bei
    kanten = np.linspace(-180, 180, 25)

    R_x = np.hypot(x[:, 0], x[:, 1])
    G = au["lage"].get("kern_geraden_m")          # schraege Kernebenen (Draufsicht-Geraden L1, L2)

    def ebene(s_):
        """Schnittebene: alte Variante phi = s_ (Grad), schraeg s_ in [0, 1] zwischen L1 (0) und L2 (1).
        Rueckgabe Punkt, Normale (xy) in Stroemungsrichtung, Winkel fuer den Querschnittsmittelpunkt."""
        if G is None:
            return np.zeros(2), np.array([-np.sin(np.radians(s_)), np.cos(np.radians(s_))]), s_
        L1a, L1b, L2a, L2b = map(np.array, G)
        A, B = (1 - s_) * L1a + s_ * L2a, (1 - s_) * L1b + s_ * L2b
        t = (B - A) / np.linalg.norm(B - A); n = np.array([-t[1], t[0]])
        n = n if n @ (L2a - L1a) > 0 else -n
        M = (A + B) / 2
        return A, n, float(np.degrees(np.arctan2(M[1], M[0])))

    def umfang(s_):
        """Durchfluss durch die Kernebene s_ je 15-Grad-Sektor des Querschnitts."""
        P0, n, ph = ebene(s_)
        sel = np.abs((x[:, :2] - P0) @ n) < 0.5 * dx
        if G is not None:
            sel &= (R_x > au["lage"]["R_band_m"][0] - 0.1) & (R_x < au["lage"]["R_band_m"][1] + 0.1)
        Xr, _ = rand_bei(ph); c = Xr.mean(0)
        t = np.degrees(np.arctan2(x[sel, 2] - c[2], R_x[sel] - np.hypot(c[0], c[1])))
        e = np.r_[n, 0.0]
        q = np.array([(u[sel][(t >= a0) & (t < a1)] @ e).sum() * dA for a0, a1 in zip(kanten[:-1], kanten[1:])])
        return q, x[sel], u[sel], t, e

    s_m, s_e, s_a = (0.5, 0.15, 0.85) if G is not None else (km, k0 + 0.3, k1 - 0.3)
    q_um, xs, us, th, e_phi = umfang(s_m)
    Xm, Nm = rand_bei(km)
    if not len(q_loch):          # ohne Lochblech: Verteilung am Kerneintritt und -austritt dazu
        erg["umfang_eintritt_m3_s"] = umfang(s_e)[0].tolist(); erg["umfang_austritt_m3_s"] = umfang(s_a)[0].tolist()
    erstwand = au["lage"].get("variante") == "erstwand"
    if erstwand:   # Waermeuebergang je Sektor: v = Q / Spaltquerschnitt, Dittus-Boelter heisses Druckwasser (~300 C)
        A_um = np.array([((th >= a0) & (th < a1)).sum() * dA for a0, a1 in zip(kanten[:-1], kanten[1:])])
        v_um = q_um / np.maximum(A_um, 1e-9)
        Dh = 2 * au["parameter"]["spaltweite"] / 1000
        h_um = 0.023 * (np.abs(v_um) * Dh / 1.2e-7) ** 0.8 * 0.86 ** 0.4 * 0.56 / Dh
        erg["waerme"] = {"v_spalt_m_s": v_um.tolist(), "h_W_m2K": h_um.tolist(),
                         "dT_wand_K": (au["parameter"]["q_MW"] * 1e6 / np.maximum(h_um, 1.0)).tolist()}
    erg["kern_umfang"] = {"Q_m3_s": q_um.tolist(), "summe_m3_s": float(q_um.sum()), "streuung_rel": float(q_um.std() / q_um.mean()),
                          "v_mittel_m_s": float(np.abs(us @ e_phi).mean()), "v_max_m_s": float(np.linalg.norm(us, axis=1).max())}
    # 3) Plasmaseite: Geschwindigkeit in den ersten 3 Zellen an der Innenhaut im Kern
    if G is None:
        imk = (phi >= k0) & (phi <= k1)
    else:   # zwischen den beiden schraegen Ebenen
        P1, n1, _ = ebene(0.0); P2, n2, _ = ebene(1.0)
        imk = ((x[:, :2] - P1) @ n1 > 2 * dx) & ((x[:, :2] - P2) @ n2 < -2 * dx) & (R_x > au["lage"]["R_band_m"][0] - 0.1)
    tiefe = au["parameter"]["spalt"] + au["parameter"]["haut_innen"]
    S = np.vstack([X_ + tiefe * N_ for X_, N_ in (rand_bei(w) for w in np.arange(k0 - 6, k1 + 6, 0.1))])
    d_haut, _ = cKDTree(S).query(x[imk])
    nah = d_haut < 3 * dx
    sv = au["parameter"].get("schicht", 0.0)
    if sv > 0:   # Anteil des Durchflusses in der feinen Schicht vorn (Kernmitte)
        d_s, _ = cKDTree(S).query(xs)
        erg["schicht_vorn"] = {"Q_m3_s": float((us[d_s < sv] @ e_phi).sum() * dA), "anteil": float((us[d_s < sv] @ e_phi).sum() * dA / q_um.sum()),
                               "v_mittel_m_s": float((us[d_s < sv] @ e_phi).mean())}
    erg["plasmaseite"] = {"v_mittel_m_s": float(np.linalg.norm(u[imk][nah], axis=1).mean()),
                          "v_p10_m_s": float(np.percentile(np.linalg.norm(u[imk][nah], axis=1), 10))}
    # 4) Druckverlust: Mittel in den Rohren 15 Zellen vor dem Ende
    st = np.loadtxt(o / "cfd" / "stat.txt")
    c_si = f["dx_m"] / f["dt_s"]
    dp = (st[:, 2] - st[:, 4]) / 3 * 1000 * c_si ** 2
    erg["druckverlust_kPa"] = float(dp[-1] / 1e3)
    erg["v_ein_m_s"] = float(st[-1, 1] * c_si); erg["v_aus_m_s"] = float(st[-1, 3] * c_si)
    (o / "cfd" / "auswertung.json").write_text(json.dumps(erg, indent=1))
    # Bilder
    fig, ax = plt.subplots(2, 2, figsize=(15, 9))
    t = st[:, 0] * f["dt_s"]
    ax[0, 0].plot(t, dp / 1e3); ax[0, 0].set_xlabel("Zeit [s]"); ax[0, 0].set_ylabel("Druckverlust Ein-Aus [kPa]")
    ax[0, 0].set_title("Verlauf (Messquerschnitte in den Rohren)"); ax[0, 0].grid(alpha=.3)
    mitte = 0.5 * (kanten[:-1] + kanten[1:])
    if len(q_loch):
        ax[0, 1].bar(range(1, len(q_loch) + 1), q_loch * 1000, color="#2a7fd4")
        ax[0, 1].axhline(Q_soll / len(q_loch) * 1000, color="k", ls="--", label="gleichmaessig")
        ax[0, 1].set_xlabel("Bohrung (Umfang, aussen beginnend)"); ax[0, 1].set_ylabel("Volumenstrom [l/s]")
        ax[0, 1].set_title(f"Lochblech: Streuung {erg['loecher']['streuung_rel']:.0%}, max/min {erg['loecher']['max_min']:.1f}")
    else:
        for q, f, n in ((erg["umfang_eintritt_m3_s"], "#2a7fd4", "Kerneintritt"), (erg["umfang_austritt_m3_s"], "#c0392b", "Kernaustritt")):
            q = np.array(q); ax[0, 1].plot(mitte, q * 1000, ".-", color=f, label=f"{n}: Streuung {q.std() / q.mean():.0%}")
        ax[0, 1].axhline(Q_soll / 24 * 1000, color="k", ls="--", label="gleichmaessig")
        ax[0, 1].set_xlabel("Umfangswinkel [Grad] (0 = aussen, 90 = oben)"); ax[0, 1].set_ylabel("Durchfluss [l/s]")
        ax[0, 1].set_title("Ringkammer -> Filamente: Verteilung ueber den Umfang")
    ax[0, 1].legend()
    ax[1, 0].bar(mitte, q_um * 1000, width=13, color="#e8a33a")
    ax[1, 0].set_xlabel("Umfangswinkel im Querschnitt [Grad] (0 = aussen, 90 = oben)"); ax[1, 0].set_ylabel("Durchfluss [l/s]")
    ax[1, 0].set_title(f"{'Erstwand-Spalt' if erstwand else 'Gyroid-Kern'} (Mitte {km:.1f} Grad): "
                       f"Streuung {erg['kern_umfang']['streuung_rel']:.0%}")
    if erstwand:
        a2 = ax[1, 0].twinx(); a2.plot(mitte, erg["waerme"]["dT_wand_K"], "r.-")
        a2.set_ylabel("Wand ueber Wasser [K] (Dittus-Boelter)", color="r"); a2.set_ylim(bottom=0)
    ax[1, 1].scatter((xs[:, :2] @ np.array([np.cos(np.radians(km)), np.sin(np.radians(km))])), xs[:, 2],
                     c=np.abs(us @ e_phi), s=1, cmap="viridis", vmax=np.percentile(np.abs(us @ e_phi), 99))
    ax[1, 1].set_aspect("equal"); ax[1, 1].set_xlabel("R [m]"); ax[1, 1].set_ylabel("z [m]")
    ax[1, 1].set_title("Querschnitt Kernmitte: |u_toroidal| (Farbe)")
    fig.suptitle(f"Kuehlsegment {o.name} 85-95 Grad, FluidX3D, t = {F['t_s']:.0f} s: Soll {Q_soll*1000:.0f} l/s, "
                 f"Druckverlust {erg['druckverlust_kPa']:.1f} kPa", fontsize=13)
    fig.tight_layout(); fig.savefig(o / "cfd" / "auswertung.png", dpi=110); plt.close(fig)
    return erg


def durchgaengig(o: Path) -> dict:
    """Pruefung nach dem Probelauf: haengen Ein- und Austritt im Gitter zusammen (6er-Nachbarschaft, streng),
    und wie viele Gitterzellen hat jede Bohrung des Lochblechs in Plattenmitte? Fehler 2026-10-26: Lochmitten
    lagen neben der Platte (Toroidalanteil der Normalen), nur 3 von 12 Loechern offen."""
    from scipy import ndimage
    from scipy.spatial import cKDTree
    F = lese_feld(o); f = F["fall"]; Nx, Ny, Nz = f["N"]
    occ = np.zeros((Nz, Ny, Nx), bool); i, j, k = F["ijk"].T; occ[k, j, i] = True
    lab, _ = ndimage.label(occ); del occ
    q = lambda r: np.round(np.array(r["ende"]) - 4 * np.array(r["achse"])).astype(int)
    le, la = [int(lab[p[2], p[1], p[0]]) for p in (q(f["rohre"]["ein"]), q(f["rohre"]["aus"]))]
    x, dx = F["x"], f["dx_m"]
    p0, p1 = json.loads((o / "auslegung.json").read_text())["lage"]["winkel_grad"]["lochblech"]; pm = 0.5 * (p0 + p1)
    e = np.array([-np.sin(np.radians(pm)), np.cos(np.radians(pm)), 0]); s = np.abs(x @ e) < 0.5 * dx
    L = np.array(json.loads((o / "auftrag.json").read_text())["loecher"]).reshape(-1, 7)
    if not len(L) or not json.loads((o / "auftrag.json").read_text()).get("mit_platte", True):
        return {"durchgaengig": le == la > 0, "ohne_lochblech": True}
    c = (L[:, :3] + L[:, 3:6]) / 2000; r = L[:, 6] / 1000
    d, ii = cKDTree(c).query(x[s]); im = d < r[ii] + dx
    erg = {"durchgaengig": le == la > 0, "zellen_je_loch": np.bincount(ii[im], minlength=len(c)).tolist(),
           "leck_zellen_platte": int((~im).sum())}
    erg["alle_loecher_offen"] = min(erg["zellen_je_loch"]) > 0.5 * np.pi * (r.min() / dx) ** 2
    return erg
