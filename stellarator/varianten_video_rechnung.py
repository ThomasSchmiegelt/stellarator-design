"""varianten_video_rechnung.py — Daten fuer die zwei Rechenszenen des Variantenfilms (Magnetfeld, Festigkeit), 0169.

  .venv/bin/python -m stellarator.varianten_video_rechnung      # -> sim/video_varianten/netze/0169_rechnung.npz

Magnetfeld: Biot-Savart (gerade Segmente, exakte Formel) aus den 24 Spulenmittellinien von 0169 (spulen.json, in
Einheitslaenge) mit dem Laengenmassstab L aus geometrie.json und dem echten Spulenstrom I_MA aus der Auswertung.
Kontrolle: |B| auf der (genaeherten) Achse gegen B_achse aus geometrie.json. Feldlinien: RK4 entlang B/|B| ab
Startpunkten in der Ebene phi = 0 zwischen Achse und Rand. |B| auf jedem Knoten des Plasmarands im Film (0169_glatt).
Festigkeit: Stahloberflaeche (Gehaeuse + Verbinder, Material 3/4) aus struktur.vtu mit von-Mises-Spannung (MPa) und
Verschiebung (m) je Knoten - dieselbe Flaeche, die der Film fuer 0169 zeigt.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PUNKT = ROOT / "sim" / "kopplung" / "netz_normal" / "punkte" / "0169"
NETZE = ROOT / "sim" / "video_varianten" / "netze"
MU0_4PI = 1e-7


def spulen():
    s = json.loads((PUNKT / "spulen.json").read_text()); g = json.loads((PUNKT / "geometrie.json").read_text())
    I = json.loads((ROOT / "daten" / "doe1_auswertung.json").read_text())["zeilen"]["0169"]["I_MA"] * 1e6
    L = g["L"]
    seg0, seg1, strom = [], [], []
    for sp in s["spulen"]:
        p = np.asarray(sp["punkte_m"], float) * L
        q = np.roll(p, -1, axis=0)                                      # geschlossene Kurve
        seg0.append(p); seg1.append(q); strom.append(np.full(len(p), I * np.sign(sp["strom_A"])))
    soll = g["B_achse_einheit_T"] * (I / g["I_einheit_A"]) / L
    return np.vstack(seg0), np.vstack(seg1), np.concatenate(strom), soll, L


def feld(x, a0, a1, I, block=2000):
    """B (T) an Punkten x (N,3) aus geraden Stromsegmenten a0->a1."""
    out = np.zeros_like(x)
    for i in range(0, len(x), block):
        xx = x[i:i + block, None, :]
        a = xx - a0[None]; b = xx - a1[None]
        na = np.linalg.norm(a, axis=2); nb = np.linalg.norm(b, axis=2)
        nenner = na * nb + np.einsum("ijk,ijk->ij", a, b)
        fak = I[None] * (na + nb) / (na * nb * np.maximum(nenner, 1e-12))
        out[i:i + block] = MU0_4PI * np.einsum("ij,ijk->ik", fak, np.cross(a, b))
    return out


def feldlinien(start, a0, a1, I, schritte=1400, h=0.12):
    x = start.copy(); bahn = [x.copy()]
    r = lambda y: (lambda B: B / np.linalg.norm(B, axis=1, keepdims=True))(feld(y, a0, a1, I))
    for _ in range(schritte):
        k1 = r(x); k2 = r(x + 0.5 * h * k1); k3 = r(x + 0.5 * h * k2); k4 = r(x + h * k3)
        x = x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4); bahn.append(x.copy())
    return np.stack(bahn, axis=1)                                       # (Linien, Punkte, 3)


def spannung():
    """Gehaeuse (3) und Verbinder (4) getrennt extrahieren (wie die Filmflaechen), dann zusammenfuegen."""
    import pyvista as pv
    g = pv.read(PUNKT / "struktur.vtu"); mat = np.asarray(g.cell_data["material"])
    V, F, VM, U, VB = [], [], [], [], []; n = 0
    for m_ in (3, 4):
        t = g.extract_cells(np.where(mat == m_)[0]).cell_data_to_point_data(pass_cell_data=False)
        m = t.extract_surface(algorithm="dataset_surface").triangulate().clean()
        V.append(np.asarray(m.points, np.float32)); F.append(m.faces.reshape(-1, 4)[:, 1:] + n); n += m.n_points
        VM.append(np.asarray(m.point_data["vonmises_MPa"], np.float32)); U.append(np.asarray(m.point_data["verschiebung_m"], np.float32))
        VB.append(np.full(m.n_points, float(m_ == 4), np.float32))
    return np.vstack(V), np.vstack(F).astype(np.int32), np.concatenate(VM), np.vstack(U), np.concatenate(VB)


def main():
    a0, a1, I, soll, L = spulen()
    gl = np.load(NETZE / "0169_glatt.npz"); pv_ = gl["plasma_v"].astype(float)
    # Achse genaehert: Mittelpunkt des Plasmaquerschnitts bei phi = 0
    phi = np.arctan2(pv_[:, 1], pv_[:, 0]); sel = np.abs(phi) < 0.02
    R = np.hypot(pv_[sel, 0], pv_[sel, 1]); Z = pv_[sel, 2]
    Rc, Zc = 0.5 * (R.min() + R.max()), 0.5 * (Z.min() + Z.max())
    B_achse = np.linalg.norm(feld(np.array([[Rc, 0, Zc]]), a0, a1, I))[()]
    print(f"Laenge {L:.2f} m, Strom {I[0] / 1e6:.2f} MA, |B| Achse {B_achse:.2f} T (soll {soll:.2f} T, "
          f"{(B_achse / soll - 1) * 100:+.1f} %)", flush=True)
    Brand = np.linalg.norm(feld(pv_, a0, a1, I), axis=1)
    rr = np.hypot(pv_[:, 0], pv_[:, 1])
    print(f"|B| Rand {Brand.min():.2f}-{Brand.max():.2f} T, innen (R<{Rc:.1f}) {Brand[rr < Rc].mean():.2f}, "
          f"aussen {Brand[rr > Rc].mean():.2f} T", flush=True)
    anteil = np.array([0.15, 0.3, 0.45, 0.6, 0.72, 0.84])
    start = np.column_stack([Rc + anteil * (R.max() - Rc), np.zeros(len(anteil)), np.full(len(anteil), Zc)])
    fl = feldlinien(start, a0, a1, I)
    rl = np.hypot(fl[..., 0], fl[..., 1]); umlauf = np.unwrap(np.arctan2(fl[..., 1], fl[..., 0]), axis=1)
    print("Feldlinien: Umlauf", np.round(np.abs(umlauf[:, -1]) / (2 * np.pi), 2), "R", rl.min().round(2), rl.max().round(2), flush=True)
    sv, sf, vm, u, verb = spannung()
    print(f"Stahl: {len(sf)} Dreiecke, von Mises {vm.min():.0f}-{vm.max():.0f} MPa, |u| max {np.linalg.norm(u, axis=1).max() * 1000:.1f} mm")
    np.savez_compressed(NETZE / "0169_rechnung.npz", feldlinien=fl.astype(np.float32), plasma_B=Brand.astype(np.float32),
                        stahl_v=sv, stahl_f=sf, stahl_vm=vm, stahl_u=u, stahl_verb=verb, B_achse=np.float32(B_achse), B_soll=np.float32(soll))


if __name__ == "__main__":
    main()
