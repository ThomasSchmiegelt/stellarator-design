"""doe_auswertung.py — Auswertung der gekoppelten Entwurfsstudie doe1 (+ Netzstudie, Ersatzmodell-Vorschlaege).

  .venv/bin/python -m stellarator.doe_auswertung tabelle        # Reserven, Rangliste -> daten/doe1_auswertung.json, .csv
  .venv/bin/python -m stellarator.doe_auswertung ersatz         # Gauss-Prozess je Kenngroesse, Kreuzvalidierung, Sensitivitaet
  .venv/bin/python -m stellarator.doe_auswertung vorschlag      # Ersatzmodell-Optimum (robust) -> sim/kopplung/ersatz1/doe.json
  .venv/bin/python -m stellarator.doe_auswertung kategorien     # Spannungskategorien Pm, Pm+Pb, Spitze (Linearisierung)
  .venv/bin/python -m stellarator.doe_auswertung bilder         # alle Bilder DE/EN
  .venv/bin/python -m stellarator.doe_auswertung alles

Begriffe
  Reserve r einer Grenze: r = 1 - Wert/Grenze (Obergrenzen) bzw. Wert/Grenze - 1 (Untergrenzen). r = 0,3 heisst
  30 % Abstand zur Grenze. Robustheit eines Entwurfs = kleinste Reserve ueber alle Grenzen (Nutzerziel F-130).
  sigma_99 (bisher "p99"): Vergleichsspannung, die in 99 % des Stahlvolumens nicht ueberschritten wird.
  Spannungskategorien (ITER-/ASME-Logik): je Wandschnitt quer zur Wanddicke Mittelwert des Spannungstensors =
  Membran Pm, linearer Anteil = Biegung Pb; Spitze = groesster Elementwert. Grenzen Pm <= Sm, Pm+Pb <= 1,5 Sm,
  Sm = 2/3 Rp0,2(4 K) (Werkstoff 316LN, siehe Bericht sec:stahl).
"""
from __future__ import annotations
import csv, json, shutil, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KOP = ROOT / "sim" / "kopplung"
DATEN = ROOT / "daten"
ZIEL = [ROOT / "docs" / "bilder", ROOT / "bericht" / "projektbericht" / "bilder"]
NAME = "Thomas Schmiegelt"
FARBE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
SPULENFARBE = {16: FARBE[0], 20: FARBE[1], 24: FARBE[2]}
SM = {"C3": 500.0, "C1": 667.0}           # Sm = 2/3 Rp0,2(4 K): Rp0,2 >= 750 (C3) bzw. >= 1000 MPa (C1), ITER

# Grenzen: name -> (Wertfunktion, Grenze, "max"|"min", Einheit, DE, EN)
GRENZEN = {
    "stahl":  (lambda e: e["struktur"]["stahl"]["vm_p99_MPa"], 500.0, "max", "MPa", "Stahl σ99", "steel σ99"),
    "dehn":   (lambda e: e["bewertung"]["dehnung_wp"] * 100, 0.3, "max", "%", "Dehnung Wickelpaket", "winding-pack strain"),
    "pack":   (lambda e: e["package"]["abschirmung_m"], 1.0, "min", "m", "Platz Package", "package space"),
    "kern":   (lambda e: e["package"]["kernheizung_wp_W_m3"], 2000.0, "max", "W/m³", "Kernheizung", "nuclear heating"),
    "fluenz": (lambda e: e["package"]["fluenz_n_cm2"], 3e18, "max", "n/cm²", "Neutronenfluenz", "neutron fluence"),
    "ausl":   (lambda e: e["package"]["auslastung"], 0.7, "max", "–", "Auslastung Supraleiter", "SC utilisation"),
    "marge":  (lambda e: e["package"]["marge_K"], 5.0, "min", "K", "Temperaturmarge", "temperature margin"),
    "Bn":     (lambda e: e["spulen"]["Bn_rel_mittel"] * 1e3, 3.0, "max", "‰", "Feldfehler B·n", "field error B·n"),
}
PARAM_NAMEN = {  # DE, EN
    "abstand_sp": ("Abstand Spule–Plasma", "coil–plasma distance"), "n_basis": ("Spulen je halbe Periode", "coils per half period"),
    "laenge_je": ("Länge je Spule", "length per coil"), "kraft_gewicht": ("Kraftziel", "force weight"),
    "wand_innen_m": ("Wand innen", "inner wall"), "wand_seite_m": ("Seitenwand", "side wall"),
    "t_min_m": ("Außenwand min.", "outer wall min."), "t_zusatz_m": ("Außenwand Zusatz", "outer wall extra"),
    "E_verbinder_GPa": ("Verbindersteifigkeit", "connector stiffness"), "verbinder_je_paar": ("Verbinder je Paar", "connectors per pair"),
    "r_lager_m": ("Lagerradius", "bearing radius"),
}
P = list(PARAM_NAMEN)


def lade(studie: str) -> dict[str, dict]:
    return {f.parent.name: json.loads(f.read_text()) for f in sorted((KOP / studie / "punkte").glob("*/ergebnis.json"))}


def reserven(e: dict) -> dict:
    r = {}
    for k, (f, g, art, *_r) in GRENZEN.items():
        v = f(e)
        r[k] = 1 - v / g if art == "max" else v / g - 1
    return r


def kurz(e: dict) -> dict:
    s, pk = e["struktur"], e["package"]
    r = reserven(e)
    # Tragwerksversuche (Studie test): 16 Spulen, Gesamtlaenge laenge_max statt n_basis/laenge_je
    q = {"n_basis": 4, "laenge_je": e["param"].get("laenge_max", 18.0) / 4, "verbinder_je_paar": 6, **e["param"]}
    e = {**e, "param": q}
    return {"spulen": 4 * int(q["n_basis"]), **{k: q[k] for k in P},
            **{f"wert_{k}": GRENZEN[k][0](e) for k in GRENZEN}, **{f"res_{k}": v for k, v in r.items()},
            "robust": min(r.values()), "engpass": min(r, key=r.get), "alle_ok": e["bewertung"]["alle_ok"],
            "stahl_max_MPa": s["stahl"]["vm_max_MPa"], "stahl_mittel_MPa": s["stahl"]["vm_mittel_MPa"],
            "verb_p99_MPa": s.get("verbinder", {}).get("vm_p99_MPa", 0), "verb_max_MPa": s.get("verbinder", {}).get("vm_max_MPa", 0),
            "u_max_mm": s["u_max_mm"], "masse_gehaeuse_kt": s["stahl"]["masse_t"] / 1e3,
            "masse_verbinder_kt": s.get("verbinder", {}).get("masse_t", 0) / 1e3,
            "masse_kt": (s["stahl"]["masse_t"] + s.get("verbinder", {}).get("masse_t", 0)) / 1e3,
            "I_MA": s["I_spule_MA"], "wickelpaket_m": s.get("wickelpaket_m"), "B_leiter_T": pk["B_leiter_T"],
            "freiraum_min_m": pk["freiraum_min_m"], "kraft_max_MN_m": e["spulen"]["kraft_je_laenge_max_N_m"],
            "verbinder_ok": s["verbinder_ok"], "stationen": s.get("stationen", 96), "loeser": s.get("loeser", "mumps"),
            "durchdringung": s["durchdringung_punkte"]}


# ---------------------------------------------------------------- Tabelle
def tabelle() -> dict:
    E = lade("doe1")
    roh = {nr: kurz(e) | {"quelle": "doe1"} for nr, e in E.items()}
    fehler = sorted(p.parent.name for p in (KOP / "doe1" / "punkte").glob("*/fehler.txt"))
    # Netzstudie (falls vorhanden)
    netz = {}
    for st in ("netz_normal", "netz_s15", "netz_q3"):
        for nr, e in lade(st).items():
            netz.setdefault(nr, {"doe1": roh[nr]})[st] = kurz(e)
    # bereinigt: Punkte, die in doe1 nur mit grobem Netz (laengere Verbinder!) liefen, durch die Nachrechnung mit
    # Standardnetz ersetzen; ohne Nachrechnung weglassen (anderes Modell, F-137)
    zeilen = {}
    for nr, z in roh.items():
        if z["loeser"] == "mumps":
            zeilen[nr] = z
        elif "netz_normal" in netz.get(nr, {}):
            zeilen[nr] = netz[nr]["netz_normal"] | {"quelle": "netz_normal"}
    rang = sorted([nr for nr, z in zeilen.items() if z["alle_ok"]], key=lambda nr: -zeilen[nr]["robust"])
    anteil = {k: float(np.mean([z[f"res_{k}"] >= 0 for z in zeilen.values()])) for k in GRENZEN}
    anteil["durchdringung"] = float(np.mean([z["durchdringung"] == 0 for z in zeilen.values()]))
    spz = {n: {"punkte": sum(z["spulen"] == n for z in zeilen.values()),
               "zulaessig": sum(z["spulen"] == n and z["alle_ok"] for z in zeilen.values()),
               "stahl_ok": sum(z["spulen"] == n and z["res_stahl"] >= 0 for z in zeilen.values()),
               "Bn_ok": sum(z["spulen"] == n and z["res_Bn"] >= 0 for z in zeilen.values())} for n in (16, 20, 24)}
    rang_roh = [nr for nr, z in roh.items() if z["alle_ok"]]
    erg = {"punkte": len(zeilen), "fehler": fehler, "zulaessig": rang, "anteil_erfuellt": anteil, "spulenzahl": spz,
           "zeilen": zeilen, "zeilen_roh": roh, "zulaessig_roh": rang_roh, "netzstudie": netz,
           "grenzen": {k: {"grenze": g[1], "art": g[2], "einheit": g[3], "de": g[4], "en": g[5]} for k, g in GRENZEN.items()}}
    DATEN.mkdir(exist_ok=True)
    (DATEN / "doe1_auswertung.json").write_text(json.dumps(erg, indent=1, default=float))
    with open(DATEN / "doe1_tabelle.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["nr"] + list(next(iter(zeilen.values()))))
        w.writeheader()
        for nr, z in zeilen.items():
            w.writerow({"nr": nr} | z)
    print(f"{len(roh)} Punkte ({len(zeilen)} bereinigt), {len(fehler)} Fehler, zulaessig {len(rang)}: {rang} (roh {rang_roh})")
    print("Anteil erfuellt:", {k: round(v, 3) for k, v in anteil.items()})
    print("Spulenzahl:", spz)
    for nr in rang:
        z = zeilen[nr]
        print(nr, f"robust {z['robust']:.2f} ({z['engpass']})", f"σ99 {z['wert_stahl']:.0f} max {z['stahl_max_MPa']:.0f}",
              f"m {z['masse_kt']:.0f} kt", f"Spulen {z['spulen']}", z["loeser"])
    for nr, d in netz.items():
        print("Netz", nr, {k: round(v["wert_stahl"]) for k, v in d.items()}, {k: round(v["stahl_max_MPa"]) for k, v in d.items()})
    return erg


# ---------------------------------------------------------------- Ersatzmodelle
ZIELE = {  # name: (Funktion auf kurz-Zeile, log?, DE, EN)
    "stahl": (lambda z: z["wert_stahl"], True, "Stahl σ99", "steel σ99"),
    "dehn": (lambda z: z["wert_dehn"], True, "Dehnung Wickelpaket", "winding-pack strain"),
    "Bn": (lambda z: z["wert_Bn"], True, "Feldfehler B·n", "field error B·n"),
    "pack": (lambda z: z["wert_pack"], False, "Platz Package", "package space"),
    "kern": (lambda z: z["wert_kern"], True, "Kernheizung", "nuclear heating"),
    "masse": (lambda z: z["masse_kt"], True, "Stahlmasse", "steel mass"),
}


def _x(zeilen) -> np.ndarray:
    from .kopplung import PARAM
    X = []
    for z in zeilen:
        row = []
        for k in P:
            lo, hi, lg = PARAM[k]
            v = z[k]
            row.append((np.log(v) - np.log(lo)) / (np.log(hi) - np.log(lo)) if lg else (v - lo) / (hi - lo))
        X.append(row)
    return np.array(X)


def _gp():
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, ConstantKernel, WhiteKernel
    k = ConstantKernel(1.0, (1e-2, 1e2)) * Matern(length_scale=np.ones(len(P)), length_scale_bounds=(0.05, 50), nu=2.5) \
        + WhiteKernel(1e-2, (1e-6, 1))
    return GaussianProcessRegressor(k, normalize_y=True, n_restarts_optimizer=3, random_state=1)


def ersatz() -> dict:
    from sklearn.model_selection import KFold
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text())
    zeilen = list(erg["zeilen"].values())
    X = _x(zeilen)
    out = {}
    for name, (f, lg, de, en) in ZIELE.items():
        y = np.array([f(z) for z in zeilen]); y = np.log(y) if lg else y
        vorh = np.zeros_like(y); sd = np.zeros_like(y)
        for tr, te in KFold(5, shuffle=True, random_state=3).split(X):
            m = _gp().fit(X[tr], y[tr]); vorh[te], sd[te] = m.predict(X[te], return_std=True)
        r2 = 1 - np.sum((y - vorh) ** 2) / np.sum((y - y.mean()) ** 2)
        m = _gp().fit(X, y)
        ls = m.kernel_.k1.k2.length_scale
        # Sensitivitaet: Varianzanteil je Stellgroesse ueber Hauptwirkungen (Mittelung des Modells ueber die anderen)
        rng = np.random.default_rng(5); basis = rng.random((400, len(P)))
        var_ges = m.predict(basis).var()
        haupt = []
        for j in range(len(P)):
            gitter = np.linspace(0, 1, 9); mittel = []
            for g in gitter:
                b = basis[:120].copy(); b[:, j] = g; mittel.append(m.predict(b).mean())
            haupt.append(float(np.var(mittel)))
        s = np.array(haupt) / max(var_ges, 1e-12)
        q = np.mean(np.abs(y - vorh) <= 1.96 * sd)                  # Anteil im 95-%-Band (Kalibrierung)
        out[name] = {"log": lg, "R2_kv": float(r2), "laengen": dict(zip(P, map(float, ls))),
                     "haupteffekt": dict(zip(P, map(float, s))), "abdeckung95": float(q),
                     "y": y.tolist(), "vorhersage_kv": vorh.tolist(), "sd_kv": sd.tolist(), "de": de, "en": en,
                     "fehler_rel_median": float(np.median(np.abs(np.exp(vorh - y) - 1))) if lg else float(np.median(np.abs(vorh - y)))}
        print(f"{name:6s} R2(KV) {r2:.3f}  95%-Band {q:.2f}  wichtig:",
              sorted(((round(v, 2), k) for k, v in out[name]["haupteffekt"].items()), reverse=True)[:4])
    (DATEN / "doe1_ersatz.json").write_text(json.dumps(out, indent=1))
    return out


def vorschlag(n: int = 4) -> list[dict]:
    """Robustestes Optimum des Ersatzmodells: max_x min_k (Reserve_k - 1 sigma). Kandidaten aus 20000 Zufallspunkten
    + lokale Suche; Vorschlaege mit Mindestabstand im Parameterraum, als DOE-Datei fuer kopplung.lauf."""
    from .kopplung import PARAM
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text())
    zeilen = list(erg["zeilen"].values()); X = _x(zeilen)
    modelle = {}
    for k in ("stahl", "dehn", "pack", "kern", "fluenz", "Bn"):
        lg = k not in ("pack",)
        y = np.array([z[f"wert_{k}"] for z in zeilen]); y = np.log(y) if lg else y
        modelle[k] = (_gp().fit(X, y), lg)

    def robust(U):
        r = []
        for k, (m, lg) in modelle.items():
            mu, sd = m.predict(U, return_std=True)
            g, art = GRENZEN[k][1], GRENZEN[k][2]
            if lg:   # Wert = exp(mu +- sd), vorsichtige Seite
                v = np.exp(mu + sd) if art == "max" else np.exp(mu - sd)
            else:
                v = mu + sd if art == "max" else mu - sd
            r.append(1 - v / g if art == "max" else v / g - 1)
        return np.min(r, axis=0)

    rng = np.random.default_rng(11)
    U = rng.random((20000, len(P)))
    U[:, P.index("n_basis")] = rng.choice([0.5 / 3, 1.5 / 3, 2.5 / 3], len(U))      # 4/5/6 diskret (Bereich 3,5-6,5)
    sc = robust(U)
    gute = U[np.argsort(-sc)[:400]]
    for _ in range(3):                                     # lokale Zufallssuche um die besten
        neu = np.clip(gute + rng.normal(0, 0.05, gute.shape), 0, 1)
        neu[:, P.index("n_basis")] = gute[:, P.index("n_basis")]
        alle = np.vstack([gute, neu]); s = robust(alle)
        gute = alle[np.argsort(-s)[:400]]
    s = robust(gute); wahl = []
    for i in np.argsort(-s):
        if all(np.linalg.norm(gute[i] - gute[j]) > 0.35 for j in wahl):
            wahl.append(i)
        if len(wahl) == n:
            break
    pk = []
    for i in wahl:
        q = {}
        for j, k in enumerate(P):
            lo, hi, lg = PARAM[k]; x = gute[i, j]
            q[k] = float(np.exp(np.log(lo) + x * (np.log(hi) - np.log(lo))) if lg else lo + x * (hi - lo))
        q["n_basis"] = int(round(q["n_basis"])); q["verbinder_je_paar"] = int(round(q["verbinder_je_paar"]))
        q["_robust_ersatz"] = float(s[i])
        pk.append(q)
        print({k: round(v, 3) for k, v in q.items()})
    o = KOP / "ersatz1"; (o / "punkte").mkdir(parents=True, exist_ok=True)
    from .kopplung import FEST
    (o / "doe.json").write_text(json.dumps({"parameter": PARAM, "fest": FEST, "punkte": pk,
                                            "herkunft": "doe_auswertung.vorschlag: max min(Reserve - 1 sigma)"}, indent=1))
    return pk


# ---------------------------------------------------------------- Spannungskategorien
def kategorien_punkt(ordner: Path) -> dict:
    import pyvista as pv
    from .hexmodell import dN
    from .struktur import WP
    e = json.loads((ordner / "ergebnis.json").read_text()); p = e["param"]
    g = pv.read(ordner / "struktur.vtu")
    X = np.asarray(g.points, float); U = np.asarray(g.point_data["verschiebung_m"], float)
    hexa = g.cells.reshape(-1, 9)[:, 1:]
    mat = np.asarray(g.cell_data["material"]); spule = np.asarray(g.cell_data["spule"])
    E = {1: WP["E_Pa"], 2: e["param"].get("E_verguss", 10e9), 3: 200e9, 4: p["E_verbinder_GPa"] * 1e9}
    nu = {1: WP["nu"], 2: 0.3, 3: 0.3, 4: 0.3}
    d = dN([0, 0, 0])
    J = np.einsum("eki,kj->eij", X[hexa], d)
    G = np.einsum("eki,kj->eij", U[hexa], d) @ np.linalg.inv(J)
    eps = 0.5 * (G + G.transpose(0, 2, 1))
    Ee = np.vectorize(E.get)(mat).astype(float); ne = np.vectorize(nu.get)(mat).astype(float)
    lam, mu = Ee * ne / ((1 + ne) * (1 - 2 * ne)), Ee / (2 * (1 + ne))
    sig = 2 * mu[:, None, None] * eps + (lam * np.trace(eps, axis1=1, axis2=2))[:, None, None] * np.eye(3)

    def vm(s):
        dev = s - np.trace(s, axis1=-2, axis2=-1)[..., None, None] / 3 * np.eye(3)
        return np.sqrt(1.5 * np.einsum("...ij,...ij->...", dev, dev)) / 1e6

    nw, nwp = int(p.get("n_wand", 2)), int(p.get("n_wp", 4))
    A = 2 * nw + 2 + nwp
    z = (np.arange(nw) + 0.5) / nw - 0.5                     # Lage der Zellmitten ueber die Wanddicke (-0,5..0,5)
    Pm, PmPb, ort = [], [], []
    for k in np.unique(spule[spule >= 0]):
        sel = np.where(spule == k)[0]
        N = len(sel) // (A * A)
        S = sig[sel].reshape(N, A, A, 3, 3)                  # (Station, a = n-Richtung, c = b-Richtung)
        linien = {"innen": S[:, :nw, :, :, :].transpose(0, 2, 1, 3, 4),        # (N, A, nw, 3, 3)
                  "aussen": S[:, A - nw:, :, :, :][:, ::-1].transpose(0, 2, 1, 3, 4),
                  "links": S[:, nw:A - nw, :nw], "rechts": S[:, nw:A - nw, A - nw:][:, :, ::-1]}
        for wand, L in linien.items():
            sm = L.mean(2)                                   # Membran
            sb = np.einsum("j,...jab->...ab", z, L) / np.sum(z ** 2) if nw > 1 else 0 * sm   # Steigung je Wanddicke
            pm = vm(sm); pb = np.maximum(vm(sm + 0.5 * sb), vm(sm - 0.5 * sb))
            Pm.append(pm.ravel()); PmPb.append(pb.ravel())
            i, c = np.unravel_index(np.arange(pm.size), pm.shape)
            ort.append(np.c_[np.full(pm.size, k), i, c, np.full(pm.size, list(linien).index(wand))])
    Pm, PmPb, ort = np.concatenate(Pm), np.concatenate(PmPb), np.concatenate(ort)
    v_el = vm(sig)
    st = mat == 3
    # Verbinder: Mittel ueber den Querschnitt je Lage (2 Lagen x 4 Stationen x A Zellen je Verbinder)
    vh = int(p.get("verbinder_halb", 2)); vsel = np.where(spule == -1)[0]; je = 2 * 2 * vh * A
    pm_v = vm(sig[vsel].reshape(-1, 2, 2 * vh * A, 3, 3).mean(2)).ravel() if len(vsel) % je == 0 and len(vsel) else np.array([0.0])
    i_pm = int(np.argmax(Pm)); i_pb = int(np.argmax(PmPb))
    wandname = ["innen", "aussen", "links", "rechts"]
    return {"Pm_max_MPa": float(Pm.max()), "Pm_p99_MPa": float(np.quantile(Pm, 0.99)),
            "PmPb_max_MPa": float(PmPb.max()), "PmPb_p99_MPa": float(np.quantile(PmPb, 0.99)),
            "spitze_max_MPa": float(v_el[st].max()), "sigma99_MPa": e["struktur"]["stahl"]["vm_p99_MPa"],
            "Pm_ort": {"spule": int(ort[i_pm, 0]), "station": int(ort[i_pm, 1]), "wand": wandname[ort[i_pm, 3]]},
            "PmPb_ort": {"spule": int(ort[i_pb, 0]), "station": int(ort[i_pb, 1]), "wand": wandname[ort[i_pb, 3]]},
            "verbinder_Pm_max_MPa": float(pm_v.max()), "verbinder_spitze_MPa": float(v_el[mat == 4].max()) if (mat == 4).any() else 0.0,
            "anteil_linien_Pm_ueber_C3": float(np.mean(Pm > SM["C3"])),
            "anteil_linien_PmPb_ueber_C3": float(np.mean(PmPb > 1.5 * SM["C3"])),
            "linien": int(Pm.size), "n_wand": nw,
            "ok_C3": bool(Pm.max() <= SM["C3"] and PmPb.max() <= 1.5 * SM["C3"]),
            "ok_C1": bool(Pm.max() <= SM["C1"] and PmPb.max() <= 1.5 * SM["C1"])}


def kategorien() -> dict:
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text())
    ordner = {f"doe1/{nr}": KOP / "doe1" / "punkte" / nr for nr in erg["zulaessig"]}
    ordner["test/0004"] = KOP / "test" / "punkte" / "0004"                     # Tragwerksversuch E (dickste Wände)
    for st in ("netz_normal", "netz_s15", "netz_q3", "ersatz1", "ersatz1_s15", "schwaechen"):
        for f in sorted((KOP / st / "punkte").glob("*/ergebnis.json")):
            ordner[f"{st}/{f.parent.name}"] = f.parent
    out = {}
    for name, o in ordner.items():
        if not (o / "struktur.vtu").exists():
            continue
        out[name] = k = kategorien_punkt(o)
        print(f"{name:18s} σ99 {k['sigma99_MPa']:5.0f} | Pm {k['Pm_max_MPa']:5.0f} ({k['Pm_ort']['wand']}) | Pm+Pb {k['PmPb_max_MPa']:5.0f}"
              f" | Spitze {k['spitze_max_MPa']:5.0f} | Verb. Pm {k['verbinder_Pm_max_MPa']:4.0f} | C3 {k['ok_C3']} C1 {k['ok_C1']}")
    (DATEN / "doe1_kategorien.json").write_text(json.dumps(out, indent=1))
    return out


# ---------------------------------------------------------------- Bilder
def speichern(fig, name):
    for z in ZIEL:
        z.mkdir(parents=True, exist_ok=True)
    p = ZIEL[0] / name; fig.savefig(p, dpi=130); shutil.copy(p, ZIEL[1] / name); print(p)


def _plt():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6, "axes.axisbelow": True})
    return plt


def bild_uebersicht(en: bool):
    """Streubild: σ99 gegen Stellgroessen, Farbe = Spulenzahl, gefuellt = alle Grenzen erfuellt."""
    plt = _plt()
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text()); Z = erg["zeilen"]
    paare = [("verbinder_je_paar", None), ("E_verbinder_GPa", "log"), ("wand_seite_m", None), ("r_lager_m", None),
             ("abstand_sp", None), ("t_min_m", None)]
    fig, ax = plt.subplots(2, 3, figsize=(10, 6.2), sharey=True)
    for a, (k, sk) in zip(ax.ravel(), paare):
        for n in (16, 20, 24):
            for ok in (False, True):
                zz = [z for z in Z.values() if z["spulen"] == n and z["alle_ok"] == ok]
                a.scatter([z[k] for z in zz], [z["wert_stahl"] for z in zz], s=26 if ok else 14,
                          facecolor=SPULENFARBE[n] if ok else "none", edgecolor=SPULENFARBE[n], lw=1.0,
                          label=(f"{n} {'coils' if en else 'Spulen'}" + (" ✔" if ok else "")) if (a is ax[0, 0] and zz) else None)
        a.axhline(500, color="#52514e", ls="--", lw=1)
        a.set_yscale("log"); a.set_xlabel(PARAM_NAMEN[k][1 if en else 0] + {"verbinder_je_paar": "", "E_verbinder_GPa": " [GPa]"}.get(k, " [m]" if k != "abstand_sp" else " [–]"))
        if sk:
            a.set_xscale("log"); a.set_xticks([20, 50, 100, 200], ["20", "50", "100", "200"]); a.minorticks_off()
    for a in ax[:, 0]:
        a.set_ylabel("steel σ99 [MPa]" if en else "Stahl σ99 [MPa]")
    h, l = ax[0, 0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=8, ncol=6, loc="upper center", bbox_to_anchor=(0.5, 0.955), frameon=False)
    fig.suptitle("Design study doe1: 199 designs, 99-% stress of the coil-case steel against the design variables" if en else
                 "Entwurfsstudie doe1: 199 Entwürfe, 99-%-Spannung im Gehäusestahl gegen die Stellgrößen", fontsize=10)
    fig.text(0.99, 0.005, NAME, ha="right", fontsize=7, color="#52514e")
    fig.tight_layout(rect=(0, 0.02, 1, 0.92))
    speichern(fig, "doe1_uebersicht" + ("_en" if en else "") + ".png"); plt.close(fig)


def bild_reserven(en: bool):
    """Reserven der zulaessigen Entwuerfe je Grenze (Rangliste nach kleinster Reserve)."""
    plt = _plt()
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text()); Z = erg["zeilen"]; rang = erg["zulaessig"]
    keys = list(GRENZEN)
    M = np.array([[min(Z[nr][f"res_{k}"], 1.5) for k in keys] for nr in rang])
    fig, ax = plt.subplots(figsize=(9.5, 0.45 * len(rang) + 1.6))
    im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1.0, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = Z[rang[i]][f"res_{keys[j]}"]
            ax.text(j, i, f"{100*v:.0f} %" if v < 1.5 else f">{150} %", ha="center", va="center", fontsize=7.5,
                    color="white" if M[i, j] > 0.6 else "#0b0b0b", fontweight="bold" if keys[j] == Z[rang[i]]["engpass"] else None)
    ax.set_xticks(range(len(keys)), [GRENZEN[k][5 if en else 4] for k in keys], rotation=25, ha="right")
    ax.set_yticks(range(len(rang)), [f"{nr}  ({Z[nr]['spulen']} {'coils' if en else 'Sp.'}, {Z[nr]['masse_kt']:.0f} kt)" for nr in rang])
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.03, label="reserve to the limit" if en else "Reserve zur Grenze")
    ax.set_title("Admissible designs, ranked by their smallest reserve (bold = bottleneck)" if en else
                 "Zulässige Entwürfe, sortiert nach kleinster Reserve (fett = Engpass)", fontsize=10)
    fig.text(0.99, 0.005, NAME, ha="right", fontsize=7, color="#52514e")
    fig.tight_layout()
    speichern(fig, "doe1_reserven" + ("_en" if en else "") + ".png"); plt.close(fig)


def bild_ersatz(en: bool):
    plt = _plt()
    E = json.loads((DATEN / "doe1_ersatz.json").read_text())
    namen = list(E)
    fig = plt.figure(figsize=(11, 6.4))
    for i, n in enumerate(namen):
        a = fig.add_subplot(2, len(namen), i + 1)
        y, v = np.array(E[n]["y"]), np.array(E[n]["vorhersage_kv"])
        if E[n]["log"]:
            y, v = np.exp(y), np.exp(v); a.set_xscale("log"); a.set_yscale("log")
        a.scatter(y, v, s=8, color=FARBE[0], alpha=0.7)
        lo, hi = min(y.min(), v.min()), max(y.max(), v.max()); a.plot([lo, hi], [lo, hi], color="#52514e", lw=0.8)
        a.set_title(f"{E[n]['en' if en else 'de']}\nR² = {E[n]['R2_kv']:.2f}", fontsize=8.5)
        a.set_xlabel("computed" if en else "gerechnet", fontsize=8)
        if i == 0: a.set_ylabel("predicted (cross-val.)" if en else "vorhergesagt (Kreuzval.)", fontsize=8)
        a.tick_params(labelsize=7)
    a = fig.add_subplot(2, 1, 2)
    H = np.array([[E[n]["haupteffekt"][k] for k in P] for n in namen])
    H = H / np.maximum(H.sum(1, keepdims=True), 1e-9)
    w = 0.8 / len(namen)
    for i, n in enumerate(namen):
        a.bar(np.arange(len(P)) + (i - len(namen) / 2 + 0.5) * w, H[i], w * 0.92, color=FARBE[i], label=E[n]["en" if en else "de"])
    a.set_xticks(range(len(P)), [PARAM_NAMEN[k][1 if en else 0] for k in P], rotation=20, ha="right", fontsize=8)
    a.set_ylabel("share of explained variation" if en else "Anteil an der Streuung")
    a.legend(fontsize=7.5, ncol=6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    fig.text(0.99, 0.005, NAME, ha="right", fontsize=7, color="#52514e")
    fig.tight_layout(h_pad=2.5)
    speichern(fig, "doe1_ersatz" + ("_en" if en else "") + ".png"); plt.close(fig)


def bild_kategorien(en: bool):
    """Links Hoechstwerte (Pm, Pm+Pb, Spitze), rechts 99 % der Wandschnitte (Pm, Pm+Pb) – bereinigte Quellen."""
    plt = _plt()
    K = json.loads((DATEN / "doe1_kategorien.json").read_text())
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text())
    namen = [(f"{erg['zeilen'][nr]['quelle']}/{nr}", nr) for nr in erg["zulaessig"]]
    namen += [("ersatz1/0003", "V3"), ("ersatz1/0001", "V1"), ("test/0004", "E (test)")]
    namen = [(q, n) for q, n in namen if q in K]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), sharey=False)
    x = np.arange(len(namen)); w = 0.36
    for a, (k1, k2), titel in zip(ax, (("Pm_max_MPa", "PmPb_max_MPa"), ("Pm_p99_MPa", "PmPb_p99_MPa")),
                                  (("(a) maximum over the whole steel" if en else "(a) Höchstwert im ganzen Stahl"),
                                   ("(b) value met by 99 % of the wall sections" if en else "(b) Wert, den 99 % der Wandschnitte einhalten"))):
        a.bar(x - w / 2, [K[q][k1] for q, _ in namen], w * 0.92, color=FARBE[0], label="membrane Pm" if en else "Membran Pm")
        a.bar(x + w / 2, [K[q][k2] for q, _ in namen], w * 0.92, color=FARBE[1], label="membrane+bending Pm+Pb" if en else "Membran+Biegung Pm+Pb")
        a.axhline(SM["C3"], color="#52514e", ls="--", lw=1); a.axhline(1.5 * SM["C3"], color="#52514e", ls=":", lw=1)
        a.text(len(namen) - 0.45, SM["C3"], "Sm = 500 (Pm)", fontsize=7, va="bottom", ha="right", color="#52514e",
               bbox=dict(facecolor="white", edgecolor="none", pad=1, alpha=0.85))
        a.text(len(namen) - 0.45, 1.5 * SM["C3"], "1.5 Sm = 750 (Pm+Pb)", fontsize=7, va="bottom", ha="right", color="#52514e",
               bbox=dict(facecolor="white", edgecolor="none", pad=1, alpha=0.85))
        a.set_xticks(x, [n for _, n in namen], rotation=30, ha="right", fontsize=8); a.set_ylabel("MPa")
        a.set_title(titel, fontsize=9.5)
    ax[0].plot(x, [K[q]["spitze_max_MPa"] for q, _ in namen], "D", color="#2b2a27", ms=5,
               label="peak (largest element)" if en else "Spitze (größtes Element)")
    ax[0].legend(fontsize=7.5, frameon=False, loc="upper left")
    ax[1].set_ylim(0, 900)
    fig.suptitle("Stress categories (admissible designs, cleaned; surrogate proposals V3, V1; support test E)" if en else
                 "Spannungskategorien (zulässige Entwürfe, bereinigt; Vorschläge V3, V1; Tragwerksversuch E)", fontsize=10)
    fig.text(0.99, 0.005, NAME, ha="right", fontsize=7, color="#52514e")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    speichern(fig, "doe1_kategorien" + ("_en" if en else "") + ".png"); plt.close(fig)


def _etiketten(a, L, x, log=False, abstand=0.045):
    """Direkte Beschriftung am rechten Linienende, senkrecht entzerrt (Abstand als Anteil der Achsenhoehe)."""
    a.figure.canvas.draw()
    y0, y1 = a.get_ylim()
    f = (lambda v: np.log10(v)) if log else (lambda v: v); g = (lambda v: 10 ** v) if log else (lambda v: v)
    h = (f(y1) - f(y0)) * abstand
    L = sorted((f(y), n) for y, n in L); pos = []
    for y, n in L:
        pos.append(max(y, pos[-1] + h) if pos else y)
    for p_, (_, n) in zip(pos, L):
        a.text(x, g(p_), n, fontsize=8, va="center", color="#2b2a27")


def bild_netz(en: bool):
    """(a) grob gerechnete doe1-Punkte -> Standardnetz; (b, c) Kandidaten ueber drei Netze."""
    plt = _plt()
    erg = json.loads((DATEN / "doe1_auswertung.json").read_text()); N = erg["netzstudie"]
    if not N:
        return
    fig, ax = plt.subplots(1, 3, figsize=(11, 4.0), gridspec_kw={"width_ratios": [0.8, 1, 1]})
    # (a) Nachrechnung der grob gerechneten Punkte
    hervor = {"0169": FARBE[0], "0063": FARBE[1], "0136": FARBE[3]}; lab0 = []
    for nr, d in sorted(N.items()):
        if "netz_normal" not in d:
            continue
        y = [d["doe1"]["wert_stahl"], d["netz_normal"]["wert_stahl"]]
        c = hervor.get(nr, "#b9b8b4")
        ax[0].plot([0, 1], y, "-o", color=c, lw=2 if nr in hervor else 1.2, ms=5, zorder=3 if nr in hervor else 2)
        if nr in hervor:
            lab0.append((y[1], nr))
    _etiketten(ax[0], lab0, 1.06)
    ax[0].set_xticks([0, 1], ["coarse (doe1)" if en else "grob (doe1)", "standard" if en else "Standard"], fontsize=8)
    ax[0].set_xlim(-0.2, 1.35); ax[0].set_ylabel("steel σ99 [MPa]" if en else "Stahl σ99 [MPa]")
    ax[0].set_title("(a) coarse-mesh designs recomputed\n(grey: other designs)" if en else
                    "(a) grob gerechnete Entwürfe nachgerechnet\n(grau: übrige Entwürfe)", fontsize=9)
    # (b, c) Kandidaten
    stufen = [("netz_s15", "1.5× stations" if en else "1,5× Stationen"), ("std", "standard" if en else "Standard"),
              ("netz_q3", "fine cross-sec." if en else "Querschnitt fein")]
    kand = [nr for nr, d in sorted(N.items()) if "netz_s15" in d]
    etik = {}
    for i, nr in enumerate(kand):
        d = dict(N[nr]); d["std"] = d.get("netz_normal", d["doe1"])
        xs = [j for j, (s_, _) in enumerate(stufen) if s_ in d]
        for a, k in zip(ax[1:], ("wert_stahl", "stahl_max_MPa")):
            y = [d[stufen[j][0]][k] for j in xs]
            a.plot(xs, y, "-o", color=FARBE[i], lw=2, ms=6, label=nr)
            etik.setdefault(id(a), (a, []))[1].append((y[-1], nr))
    for a, L in etik.values():
        _etiketten(a, L, 2.08, log=a is ax[2])
    for a, t in zip(ax[1:], ("(b) σ99", "(c) largest element" if en else "(c) größtes Element")):
        a.set_xticks(range(3), [s_[1] for s_ in stufen], fontsize=8); a.set_xlim(-0.2, 2.45)
        a.set_title(t + (" – candidates" if en else " – Kandidaten"), fontsize=9); a.set_ylabel("MPa")
    for a in ax:
        a.axhline(500, color="#52514e", ls="--", lw=1)
    ax[2].set_yscale("log"); ax[2].set_yticks([500, 1000, 2000, 5000], ["500", "1000", "2000", "5000"]); ax[2].minorticks_off()
    fig.suptitle("Mesh study: same coils and parameters, different mesh (dashed: 500 MPa)" if en else
                 "Netzstudie: gleiche Spulen und Parameter, anderes Netz (gestrichelt: 500 MPa)", fontsize=10)
    fig.text(0.99, 0.005, NAME, ha="right", fontsize=7, color="#52514e")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    speichern(fig, "doe1_netz" + ("_en" if en else "") + ".png"); plt.close(fig)


def bilder():
    for en in (False, True):
        bild_uebersicht(en); bild_reserven(en)
        if (DATEN / "doe1_ersatz.json").exists(): bild_ersatz(en)
        if (DATEN / "doe1_kategorien.json").exists(): bild_kategorien(en)
        bild_netz(en)


if __name__ == "__main__":
    b = sys.argv[1] if len(sys.argv) > 1 else "alles"
    if b in ("tabelle", "alles"): tabelle()
    if b in ("ersatz", "alles"): ersatz()
    if b == "vorschlag": vorschlag()
    if b in ("kategorien", "alles"): kategorien()
    if b in ("bilder", "alles"): bilder()
