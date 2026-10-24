"""bewerte.py — schnelle Bewertungsfunktion Fall -> Kennzahlen (Optimierungsschnittstelle).

Nur Biot-Savart an den Filamenten (exakt, kein Voxel, kein PicoGK, kein Elmer), damit
Hermes/PI bzw. ein numerischer Optimierer viele Faelle rechnen koennen (~10–20 s je Fall).

  .venv/bin/python -m stellarator.bewerte stellarator/faelle/w7x_standard.json
  .venv/bin/python -m stellarator.bewerte FALL.json --setze spulen.stroeme_Awdg.PCA=200000 --name pca_plus
  .venv/bin/python -m stellarator.bewerte FALL.json --schnell      # weniger Umlaeufe, ohne Spalt

Python:  from stellarator.bewerte import bewerte;  k = bewerte(fall_dict)

Kennzahlen (alle SI): strom (Kalibrierung), achse (Lage per Fixpunkt der Periodenabbildung,
|B| min/max/mittel, Spiegelverhaeltnis), iota (Profil ueber r_eff, Achse, Rand, Abstand zu
iota=1), flussflaechen (r_eff der aeussersten nicht verlorenen Linie), spulen (B_max an der
Wickeloberflaeche, Netto-Lorentzkraft je Typ), geometrie (min. Spalt zwischen Wickelpaketen).
Ausgabe: sim/stellarator/bewertung/<name>/kennzahlen.json (+ poincare.png mit --bild);
letzte stdout-Zeile = kompaktes JSON (fuer Agenten).
"""
from __future__ import annotations
import argparse, copy, json, time, warnings
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from . import spulen as sp, cad
from .feldlinien import ZylinderGitter, verfolge, iota, _rhs
from .lauf import setze, PROJEKT

STANDARD = {"umlaeufe": 80, "n_linien": 12, "dR_max_m": None, "spalt": True}   # dR None -> aus Spulensatz
SCHNELL = {"umlaeufe": 40, "n_linien": 8, "dR_max_m": None, "spalt": False}


def finde_achse(G: ZylinderGitter, start=None, nfp: int = 5) -> tuple[float, float]:
    """Magnetische Achse in phi=0: Fixpunkt (R,Z) der Abbildung ueber eine Feldperiode."""
    if start is None:
        a = sp.achse(np.array([0.0]))[0]
        start = (float(np.hypot(a[0], a[1])), float(a[2]))

    def rest(p):
        pk, lost = verfolge(G, np.array([p[0]]), np.array([p[1]]), n_umlaeufe=1, nfp=nfp,
                            R_grenze=(G.R[0], G.R[-1]), Z_grenze=G.Z[-1])
        return np.array([1.0, 1.0]) if lost[0] else pk[0, 0] - p
    r = least_squares(rest, np.array(start, float), diff_step=1e-4, xtol=1e-7)
    if np.linalg.norm(r.fun) > 1e-4:
        raise RuntimeError(f"kein Fixpunkt (Rest {np.linalg.norm(r.fun):.1e} m)")
    return float(r.x[0]), float(r.x[1])


def achsenkurve(G, Ra: float, Za: float, nfp: int = 5, n: int = 120):
    """Achse ueber eine Feldperiode ab (Ra, Za) bei phi=0 (RK4, jeder Schritt gespeichert)."""
    h = 2 * np.pi / nfp / n
    phi = np.arange(n + 1) * h
    RZ = np.empty((n + 1, 2)); RZ[0] = Ra, Za
    R, Z = np.array([Ra]), np.array([Za])
    for i in range(n):
        f = phi[i]
        k1 = _rhs(G, R, Z, f)
        k2 = _rhs(G, R + h / 2 * k1[0], Z + h / 2 * k1[1], f + h / 2)
        k3 = _rhs(G, R + h / 2 * k2[0], Z + h / 2 * k2[1], f + h / 2)
        k4 = _rhs(G, R + h * k3[0], Z + h * k3[1], f + h)
        R = R + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        Z = Z + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        RZ[i + 1] = R[0], Z[0]
    return phi, RZ


def flussflaeche_intakt(pk: np.ndarray, achse_RZ, tol: float = 0.05) -> np.ndarray:
    """Linie liegt auf einer intakten Flussflaeche um die Achse (B-016).

    Kriterium: poloidaler Winkel laeuft monoton (immer gleiches Vorzeichen je Periode) und der
    Achsabstand r ist eine glatte Funktion des Winkels: Punkte nach Winkel sortiert, mittlerer
    Sprung |dr| relativ zur Spannweite von r < tol. Inselketten (Punkte springen zwischen den
    Aesten) und chaotische Randlinien fallen durch; ihr 'iota um die Achse' ist sinnlos.
    """
    dR, dZ = pk[..., 0] - achse_RZ[0], pk[..., 1] - achse_RZ[1]
    th, r = np.arctan2(dZ, dR), np.hypot(dR, dZ)
    out = np.zeros(len(pk), bool)
    for i in range(len(pk)):
        if not np.isfinite(th[i]).all():
            continue
        d = np.diff(np.unwrap(th[i]))
        if not ((d > 0).all() or (d < 0).all()):
            continue
        rs = r[i][np.argsort(th[i])]
        spann = rs.max() - rs.min()
        out[i] = np.abs(np.diff(rs)).mean() < tol * max(spann, 1e-3)
    return out


def _netto_kraefte(spulen) -> np.ndarray:
    """Netto-Lorentzkraft (N) je Spule: I * sum(dl x B_andere) (Eigenfeld netto 0)."""
    F = np.zeros((len(spulen), 3))
    for i, s in enumerate(spulen):
        if s.strom == 0:
            continue
        andere = [q for j, q in enumerate(spulen) if j != i and q.strom != 0]
        P = s.punkte; dl = np.roll(P, -1, 0) - P; mitte = P + dl / 2
        F[i] = s.strom * np.cross(dl, sp.biot_savart(mitte, sp.segmente(andere))).sum(0)
    return F


def bewerte(fall: dict, opt: dict | None = None, ordner: Path | None = None, bild: bool = False) -> dict:
    opt = STANDARD | (opt or {})
    t_start = time.time(); zeiten = {}
    c = fall["spulen"]
    breite, hoehe = c["wickel_breite_m"], c["wickel_hoehe_m"]
    k = {"fall": fall.get("name"), "status": "ok", "optionen": opt}

    # Spulen + Kalibrierung
    t0 = time.time()
    spulen, geo = sp.lade_spulensatz(c)
    nfp = geo["nfp"]
    seg = sp.segmente(spulen)
    feld = lambda x: sp.biot_savart(x, seg)
    G = ZylinderGitter(feld, R=geo["R_gitter"], Z=geo["Z_gitter"], nfp=nfp); zeiten["gitter_s"] = time.time() - t0
    spur = dict(nfp=nfp, R_grenze=geo["R_grenze"], Z_grenze=geo["Z_grenze"])

    # Achse (Feldlinienverlauf haengt nicht vom Gesamtstrom ab -> vor der Kalibrierung)
    t0 = time.time()
    try:
        Ra, Za = finde_achse(G, geo["achse_start"], nfp=nfp)
    except Exception as e:                                   # keine geschlossene Achse
        k.update(status="fehler", fehler=f"Achse nicht gefunden: {e}")
        return k
    phi, RZ = achsenkurve(G, Ra, Za, nfp=nfp)
    xa = np.column_stack([RZ[:, 0] * np.cos(phi), RZ[:, 0] * np.sin(phi), RZ[:, 1]])
    # Kalibrierung auf mittleres |B| der VERFOLGTEN Achse (nicht spulen.achse, B-016)
    faktor = c["B0_achse_T"] / np.linalg.norm(feld(xa), axis=1).mean() if c.get("B0_achse_T") else 1.0
    for s in spulen:
        s.strom *= faktor
    seg = sp.segmente(spulen)
    strom = {s.typ: abs(s.strom) for s in spulen}
    wdg = c.get("windungen", c.get("windungen_npc", 1))
    k["strom"] = {"kalibrierfaktor": faktor, "Awdg_je_typ": strom, "windungen": wdg,
                  "kA_je_windung_max": max(strom.values()) / wdg / 1e3}
    if "NPC1" in strom:
        k["strom"]["kA_je_windung_npc1"] = strom["NPC1"] / wdg / 1e3
    Ba = np.linalg.norm(feld(xa), axis=1)
    k["achse"] = {"R_phi0_m": Ra, "Z_phi0_m": Za, "B_mittel_T": float(Ba.mean()),
                  "B_min_T": float(Ba.min()), "B_max_T": float(Ba.max()),
                  "spiegelverhaeltnis": float((Ba.max() - Ba.min()) / (Ba.max() + Ba.min()))}
    zeiten["achse_s"] = time.time() - t0

    # Feldlinien, iota
    t0 = time.time()
    R0 = Ra + np.linspace(0.0, opt["dR_max_m"] or geo["dR_max_m"], opt["n_linien"] + 1)[1:]
    pk, lost = verfolge(G, R0, np.full_like(R0, Za), n_umlaeufe=opt["umlaeufe"], **spur)
    io = np.abs(iota(pk, (Ra, Za), nfp=nfp))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        r_eff = np.nanmean(np.hypot(pk[..., 0] - Ra, pk[..., 1] - Za), axis=1)
    regulaer = flussflaeche_intakt(pk, (Ra, Za)) & ~lost
    # geschachtelte Flaechen: von der Achse aus bis zur ersten gestoerten Linie
    n_ok = int(np.argmin(regulaer)) if not regulaer.all() else len(regulaer)
    ok = np.zeros_like(regulaer); ok[:n_ok] = True
    k["iota"] = {"profil": [{"R0_m": float(r), "r_eff_m": float(e), "iota": float(i), "verloren": bool(l),
                             "flussflaeche_intakt": bool(g)}
                            for r, e, i, l, g in zip(R0, r_eff, io, lost, regulaer)],
                 "achse": float(io[0]) if ok[0] else None,
                 "rand": float(io[ok][-1]) if ok.any() else None,
                 "min": float(io[ok].min()) if ok.any() else None,
                 "max": float(io[ok].max()) if ok.any() else None,
                 "abstand_zu_1_min": float(np.min(np.abs(io[ok] - 1.0))) if ok.any() else None}
    k["flussflaechen"] = {"r_eff_max_m": float(r_eff[ok].max()) if ok.any() else 0.0,
                          "n_intakt": n_ok, "n_verloren": int(lost.sum()), "n_linien": int(len(R0))}
    zeiten["feldlinien_s"] = time.time() - t0

    # Spulen: B_max an der Wickeloberflaeche, Kraefte
    t0 = time.time()
    tri = np.concatenate([sp.rohr_dreiecke(s, breite, hoehe) for s in spulen if s.strom != 0])
    pts = np.unique(tri.reshape(-1, 3).round(7), axis=0)
    F = _netto_kraefte(spulen)
    typ = {}
    for i, s in enumerate(spulen):
        typ.setdefault(s.typ, []).append(np.linalg.norm(F[i]) / 1e6)
    k["spulen"] = {"B_max_oberflaeche_T": float(np.linalg.norm(feld(pts), axis=1).max()),
                   "F_netto_MN_max_je_typ": {t: float(max(v)) for t, v in typ.items()},
                   "F_summe_MN": float(np.linalg.norm(F.sum(0)) / 1e6)}
    zeiten["spulen_s"] = time.time() - t0

    # Geometrie: Spalt
    if opt["spalt"]:
        t0 = time.time()
        a = cad.abstaende(sp.lade_spulensatz(c, n_punkte=500)[0], breite, hoehe, n_basis=geo["n_basis"])
        k["geometrie"] = {"spalt_min_m": a["spalt_min_m"], "engstes_paar": a["engste"][0][:2],
                          "n_durchdringungen": len(a["durchdringungen"])}
        zeiten["spalt_s"] = time.time() - t0

    zeiten["gesamt_s"] = time.time() - t_start
    k["zeiten"] = zeiten
    if ordner:
        ordner.mkdir(parents=True, exist_ok=True)
        (ordner / "fall.json").write_text(json.dumps(fall, indent=2, ensure_ascii=False))
        (ordner / "kennzahlen.json").write_text(json.dumps(k, indent=2, ensure_ascii=False))
        if bild:
            _bild(pk, lost, io, r_eff, (Ra, Za), k, ordner / "poincare.png")
    return k


def _bild(pk, lost, io, r_eff, achse, k, pfad):
    import matplotlib
    matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 5), dpi=110)
    farben = plt.cm.viridis(np.linspace(0, 1, len(pk)))
    for i in range(len(pk)):
        ax[0].plot(pk[i, :, 0], pk[i, :, 1], ".", ms=1, color=farben[i])
    ax[0].plot(*achse, "r+", ms=10)
    ax[0].set(aspect="equal", xlabel="R [m]", ylabel="Z [m]", title=f"Poincare phi=0 — {k['fall']}")
    ok = ~lost
    ax[1].plot(r_eff[ok], io[ok], "o-", ms=4); ax[1].axhline(1, color="grey", ls=":", lw=.8)
    ax[1].set(xlabel="r_eff [m]", ylabel="iota", title="Rotationstransformation"); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(pfad); plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Schnelle Bewertung eines Stellarator-Falls (Biot-Savart)")
    ap.add_argument("fall", type=Path)
    ap.add_argument("--setze", action="append", default=[], help="pfad.zum.wert=JSON (mehrfach)")
    ap.add_argument("--name")
    ap.add_argument("--schnell", action="store_true", help="40 Umlaeufe, 8 Linien, ohne Spalt")
    ap.add_argument("--bild", action="store_true", help="poincare.png schreiben")
    a = ap.parse_args(argv)
    fall = json.loads(a.fall.read_text())
    for z in a.setze:
        setze(fall, z)
    if a.name:
        fall["name"] = a.name
    k = bewerte(copy.deepcopy(fall), SCHNELL if a.schnell else None,
                PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"], a.bild)
    print(json.dumps(k, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
