"""vergleich_kuehlung.py — Schnellvergleich der Waermeabfuhr (1D-Modell) fuer beliebige Plasmaform (wout) und Massstab L.

  .venv-opt/bin/python -m stellarator.vergleich_kuehlung --name k3_halb --wout <nc> --L 13.6084 [--biot_savart <json>]
        [--P_fus 3053] [--f_div 0.5] [--q 0.5] [--spalt 0.15] [--n_phi 12] [--phi0 ...]
  .venv-opt/bin/python -m stellarator.vergleich_kuehlung --test        # QA-Form gegen bekannte Werte (sim/blei/b1, Segmentstudien)

Die Kuehlmodule (kuehlung_segment, erstwand_kanal, blei_kanal) lesen den Plasmarand fest aus der QA-Form
(gyroid_gefaess.randflaeche). Hier wird randflaeche per Monkeypatch durch eine Version auf der gegebenen wout und L
ersetzt (kein Eingriff in die bestehenden Dateien). Je Toroidalwinkel phi (eine Feldperiode, Stellaratorsymmetrie):
  Umfang U(phi) und Radius R(phi) der Wandflaeche (Plasmarand + spalt), blei_kanal.auslegung (Kanalzahl, Laenge, v, Ha,
  MHD-Druckverlust, Pumpleistung) und, mit --biot_savart, B quer zur toroidalen Stroemung aus den eigenen Spulen
  (Biot-Savart auf der Wandflaeche, Kalibrierung auf B0 wie kraft_analyse.kalibrierung) statt der Annahme 6 Grad / 6 T.
Dazu Flaechen und mittlere Wandlasten (Neutronen 0,8 P_fus / S nach kopplung.schritt_package; Strahlung
(1 - f_div) f_alpha P_fus / S nach waermebilanz). Alle Zahlen sind Modellwerte (1D, ohne Kehren/Verteiler/Neutronik).
"""
from __future__ import annotations
import argparse
import json
from argparse import Namespace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
F_ALPHA = 3.52 / 17.59
B0 = 6.5


def randflaeche_wout(wout: Path, L: float):
    """Ersatz fuer gyroid_gefaess.randflaeche: Rand der wout (letzte Flaeche), Massstab L (Einheit -> m)."""
    from netCDF4 import Dataset
    with Dataset(str(wout)) as w:
        rmnc, zmns, xm, xn = w["rmnc"][-1, :], w["zmns"][-1, :], w["xm"][:], w["xn"][:]

    def randflaeche(R0: float = 10.4, n_th: int = 96, n_ph: int = 720, phi=None) -> np.ndarray:   # R0 wird ignoriert
        th, ph = np.meshgrid(np.linspace(0, 2 * np.pi, n_th, endpoint=False),
                             np.linspace(0, 2 * np.pi, n_ph, endpoint=False) if phi is None else np.asarray(phi, float),
                             indexing="ij")
        arg = xm[:, None, None] * th - xn[:, None, None] * ph
        R = np.einsum("m,mij->ij", rmnc, np.cos(arg)); Z = np.einsum("m,mij->ij", zmns, np.sin(arg))
        return np.stack([R * np.cos(ph), R * np.sin(ph), Z], -1) * L
    return randflaeche


def nfp_aus_wout(wout: Path) -> int:
    from netCDF4 import Dataset
    with Dataset(str(wout)) as w:
        return int(w["nfp"][:])


def flaeche_netz(X: np.ndarray) -> float:
    """Flaeche des (n_th, n_ph, 3) Netzes (ganzer Torus, periodisch), Summe der Parallelogramme."""
    du = np.roll(X, -1, 0) - X; dv = np.roll(X, -1, 1) - X
    return float(np.linalg.norm(np.cross(du, dv), axis=-1).sum())


def rechne(wout: Path, L: float, P_fus: float = 3053.0, f_div: float = 0.5, q: float = 0.5, spalt: float = 0.15,
           n_phi: int = 12, biot_savart: Path | None = None, medium: str = "Blei") -> dict:
    from . import kuehlung_segment as ks, blei_kanal as bk, erstwand_kanal as ek
    from .gesamtszene import normalen
    rf = randflaeche_wout(wout, L)
    alt = (ks.randflaeche, bk.umfang)
    ks.randflaeche = rf                                     # Monkeypatch (rand_bei, umfang, blei_kanal.umfang nutzen es)
    try:
        nfp = nfp_aus_wout(wout)
        X = rf(n_th=192, n_ph=1440); N = normalen(X)
        S_plasma = flaeche_netz(X); S_wand = flaeche_netz(X + spalt * N)
        q_n = 0.8 * P_fus / S_plasma                        # wie kopplung.schritt_package (mittlere Neutronenwandlast)
        q_str = (1 - f_div) * F_ALPHA * P_fus / S_plasma    # wie waermebilanz: Strahlung auf die Erstwand
        bs = fak = None
        if biot_savart is not None:
            from simsopt import load
            bs = load(str(biot_savart))
            from scipy.io import netcdf_file
            with netcdf_file(str(wout), mmap=False) as w:
                rax, zax = w.variables["raxis_cc"][:].copy(), w.variables["zaxis_cs"][:].copy()
            ph = np.linspace(0, 2 * np.pi, 400, endpoint=False); n = np.arange(len(rax))
            Ra = (rax[None] * np.cos(nfp * n[None] * ph[:, None])).sum(1); Za = (-zax[None] * np.sin(nfp * n[None] * ph[:, None])).sum(1)
            bs.set_points(np.c_[Ra * np.cos(ph), Ra * np.sin(ph), Za])
            fak = B0 / np.linalg.norm(bs.B(), axis=1).mean()   # B_real = B_Einheit * fak (B ~ I / L, Strom kalibriert)
        zeilen = []
        for phi in np.linspace(0, 360.0 / nfp, n_phi + 1):  # eine Feldperiode inkl. Ende (Symmetrie)
            U, R = ek.umfang(spalt=spalt, phi=float(phi))
            bk.umfang = lambda spalt=spalt, phi=float(phi): ek.umfang(spalt=spalt, phi=phi)   # blei_kanal.auslegung ruft umfang()
            a = Namespace(b=20.0, h=20.0, steg=4.0, haut=5.0, rueck=5.0, q=q, T_ein=350.0, dT=150.0, B=6.0, steigung=6.0)
            z = {"phi_grad": float(phi), "umfang_m": U, "R_mittel_m": float(R.mean()), "R_max_m": float(R.max())}
            if bs is not None:
                ph_ = np.radians([phi - 0.05, phi, phi + 0.05])
                Xs = rf(n_th=720, phi=ph_); Ns = normalen(Xs)[:, 1]; xs = Xs[:, 1] + spalt * Ns
                bs.set_points(xs / L); Bv = bs.B() * fak
                e_phi = np.c_[-xs[:, 1], xs[:, 0], 0 * xs[:, 0]]; e_phi /= np.linalg.norm(e_phi, axis=1)[:, None]
                Bpar = (Bv * e_phi).sum(1); Bq = np.linalg.norm(Bv - Bpar[:, None] * e_phi, axis=1)
                Bb = np.linalg.norm(Bv, axis=1)
                z.update({"B_betrag_mittel_T": float(Bb.mean()), "B_quer_rms_T": float(np.sqrt((Bq ** 2).mean())),
                          "B_quer_p95_T": float(np.quantile(Bq, 0.95)), "B_quer_max_T": float(Bq.max()),
                          "winkel_mittel_grad": float(np.degrees(np.arcsin(np.sqrt((Bq ** 2).mean()) / Bb.mean())))})
            for kennung, a_ in (("annahme_6grad_6T", a),) + ((("aus_spulen", Namespace(**(vars(a) | {
                    "B": z["B_betrag_mittel_T"], "steigung": z["winkel_mittel_grad"]}))),) if bs is not None else ()):
                for iso in (False, True):
                    e = bk.auslegung(a_, medium, "toroidal", iso)
                    z[f"{kennung}_{'isoliert' if iso else 'stahlwand'}"] = {k: e[k] for k in (
                        "kanaele", "laenge_m", "waermelast_MW", "v_m_s", "B_quer_T", "Ha", "dp_mhd_kPa", "dp_reib_kPa", "dp_kPa",
                        "pumpleistung_kW")}
            zeilen.append(z)
    finally:
        ks.randflaeche, bk.umfang = alt
    def agg(schl):
        v = [z[schl[0]][schl[1]] for z in zeilen]
        return {"mittel": float(np.mean(v)), "max": float(np.max(v)), "min": float(np.min(v))}
    kenn = {k: agg((k, "dp_mhd_kPa")) for k in zeilen[0] if isinstance(zeilen[0][k], dict) and "dp_mhd_kPa" in zeilen[0][k]}
    return {"wout": str(wout), "L": L, "nfp": nfp, "P_fus_MW": P_fus, "P_fus_status": "Annahme (kopplung.P_FUS_MW, Stufe 0 QA)",
            "f_div": f_div, "q_Annahme_MW_m2": q, "spalt_m": spalt,
            "flaeche_plasma_m2": S_plasma, "flaeche_wand_offset_m2": S_wand,
            "wandlast_neutronen_mittel_MW_m2": q_n, "wandlast_strahlung_mittel_MW_m2": q_str,
            "q_strahlung_gegen_annahme": q_str / q, "dp_mhd_kPa_je_Variante": kenn, "profil": zeilen}


def test_qa() -> dict:
    """QA-Form: Ersatz-randflaeche muss die feste Version reproduzieren, blei_kanal-Ergebnis b1 (phi = 90)."""
    from . import kopplung as kp, gyroid_gefaess as gg, erstwand_kanal as ek, blei_kanal as bk
    wout = kp.WOUT; L = kp.L
    ref = gg.randflaeche(R0=10.4, n_th=96, n_ph=720)
    neu = randflaeche_wout(wout, L)(n_th=96, n_ph=720)
    out = {"randflaeche_max_abw_m": float(np.abs(ref - neu).max())}
    U0, R0_ = ek.umfang(phi=90.0)                                # Original
    r = rechne(wout, L, n_phi=2)                                 # Patch (phi = 0, 90, 180: halbe Periode 90 Grad bei nfp 2)
    p90 = [z for z in r["profil"] if abs(z["phi_grad"] - 90.0) < 1e-9][0]
    out["umfang_phi90_original_m"] = U0; out["umfang_phi90_patch_m"] = p90["umfang_m"]
    b1 = json.loads((ROOT / "sim" / "blei" / "b1" / "auslegung.json").read_text())["faelle"][0]
    mine = p90["annahme_6grad_6T_stahlwand"]
    out["b1_gespeichert"] = {k: b1[k] for k in ("kanaele", "laenge_m", "waermelast_MW", "v_m_s", "dp_mhd_kPa", "dp_kPa")}
    out["patch_phi90"] = {"kanaele": mine["kanaele"], "laenge_m": mine["laenge_m"], "waermelast_MW": mine["waermelast_MW"],
                          "v_m_s": mine["v_m_s"], "dp_mhd_kPa": mine["dp_mhd_kPa"], "dp_kPa": mine["dp_kPa"]}
    out["flaeche_plasma_m2"] = r["flaeche_plasma_m2"]; out["wandlast_neutronen_mittel_MW_m2"] = r["wandlast_neutronen_mittel_MW_m2"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true"); ap.add_argument("--name", default="vergleich")
    ap.add_argument("--wout"); ap.add_argument("--L", type=float); ap.add_argument("--biot_savart")
    ap.add_argument("--P_fus", type=float, default=3053.0); ap.add_argument("--f_div", type=float, default=0.5)
    ap.add_argument("--q", type=float, default=0.5); ap.add_argument("--spalt", type=float, default=0.15)
    ap.add_argument("--n_phi", type=int, default=12); ap.add_argument("--herkunft", default="")
    a = ap.parse_args()
    if a.test:
        print(json.dumps(test_qa(), indent=1)); return
    e = rechne(Path(a.wout).resolve(), a.L, a.P_fus, a.f_div, a.q, a.spalt, a.n_phi,
               Path(a.biot_savart).resolve() if a.biot_savart else None)
    e["herkunft"] = a.herkunft
    o = ROOT / "sim" / "kette_k3" / "vergleich"; o.mkdir(parents=True, exist_ok=True)
    (o / f"kuehlung_{a.name}.json").write_text(json.dumps(e, indent=1))
    print(json.dumps({k: v for k, v in e.items() if k != "profil"}, indent=1))


if __name__ == "__main__":
    main()
