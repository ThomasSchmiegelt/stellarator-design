"""kopplung.py — gekoppelte Entwurfsstudie Plasma <-> Spulen <-> Package <-> Festigkeit <-> Temperatur.

Ein Entwurfspunkt (Parameter p) durchlaeuft die Kette:
  1. Spulen     invers/stufe2_spulen.py (.venv-opt): Abstand Spule-Plasma, Spulenlaenge, Kraftziel
                -> Feldgenauigkeit B.n (Ersatz fuer Alpha-Verluste), Kraft je Laenge, Feld am Leiter
  2. Geometrie  (.venv-opt) Plasmarand aus VMEC, Achsenfeld -> Stromkalibrierung auf B0
  3. Struktur   Hex-Modell + Elmer (wie surrogat.py, aber je Punkt eigener Spulensatz, Verbinder ohne festen Plan)
  4. Package    Freiraum Plasmarand -> Gehaeuse-Innenseite rundum; Abschirmung -> Kernheizung + Fluenz im Wickelpaket
  5. Temperatur REBCO Je_c(B, T) (Senatore 2024 / Pardo 2026) -> Auslastung und Temperaturmarge; Dehnung Wickelpaket
Alpha-Verluste: hier nur B.n als Ersatz; volle Bahnrechnung (alpha_bahnen) fuer die besten Entwuerfe.

Massstab: Spulen und VMEC im selben Massstab L = 10,4 / 1,0294 (wie alpha_bahnen, Plasmavideo).
Annahmen mit Status siehe ANNAHMEN und docs/recherche/kopplung_festigkeit/quellen.md.

Befehle (.venv/bin/python -m stellarator.kopplung ...):
  punkt --studie test --nr 0 [--p name=wert ...]   einen Punkt rechnen (Test)
  lauf  --studie doe1 --n 100 [--stunden 10]        DOE abarbeiten; fertige Punkte werden uebersprungen (= --weiter)
  tabelle --studie doe1                             Kennzahlen aller Punkte als Tabelle
Pausieren: ~/bin/rechnung pause | weiter (friert den Scope ein), oder steuerung.json {"stopp": true}.
Ablage: sim/kopplung/<studie>/ (doe.json, lauf.log, punkte/NNNN/{stufe2.json, spulen.json, geometrie.json, ergebnis.json})
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, time, traceback
from argparse import Namespace
from pathlib import Path
import numpy as np

PROJEKT = Path(__file__).resolve().parents[1]
WURZEL = PROJEKT / "sim" / "kopplung"
PY_OPT = PROJEKT / ".venv-opt" / "bin" / "python"
WOUT = PROJEKT / "sim" / "invers" / "qa_nfp2_A45" / "wout_qa_nfp2_A45.nc"
R0, B0, R0_U = 10.4, 6.5, 1.0294040771781494
L = R0 / R0_U
P_FUS_MW = 3053.0                     # Stufe 0 bei 1000 MW netto (sim/surrogat/qa_1gw/stufe0_tabelle.json)
WP_M = 0.7552                         # Wickelpaket quadratisch (Stufe 0)

# ---------------------------------------------------------------- Parameterraum
PARAM = {   # name: (min, max, log)
    "abstand_sp":      (0.12, 0.30, False),   # min. Abstand Spulenmitte-Plasma in Stufe 2 (Einheitsgeometrie, x L = m)
    "n_basis":         (3.5, 6.5, False),     # Basisspulen je halber Periode, gerundet: 4/5/6 -> 16/20/24 Spulen
    "laenge_je":       (3.6, 5.0, False),     # Laenge je Basisspule (Einheitsgeometrie), Summe = n_basis x laenge_je
    "kraft_gewicht":   (0.0, 0.03, False),    # Kraftziel (F-115: >0,03 kostet zu viel Feldgenauigkeit)
    "wand_innen_m":    (0.10, 0.60, False),
    "wand_seite_m":    (0.08, 0.40, False),
    "t_min_m":         (0.15, 0.80, False),
    "t_zusatz_m":      (0.00, 0.60, False),
    "E_verbinder_GPa": (20.0, 200.0, True),
    "verbinder_je_paar": (5.5, 14.49, False), # gerundet
    "r_lager_m":       (1.0, 4.0, False),
}
FEST = {"verguss_m": 0.02, "E_verguss_GPa": 10.0, "verbinder_je_paar": 6, "verbinder_halb": 2,
        "stationen": 96, "spiel_m": 0.02, "lager_ort": "beide"}
REFERENZ = {"abstand_sp": 0.18, "n_basis": 4, "laenge_je": 4.5, "verbinder_je_paar": 12, "kraft_gewicht": 0.0, "wand_innen_m": 0.35, "wand_seite_m": 0.24,
            "t_min_m": 0.45, "t_zusatz_m": 0.3, "E_verbinder_GPa": 50.0, "r_lager_m": 2.5}

# ---------------------------------------------------------------- Annahmen (Status: g = geprueft, a = Annahme)
ANNAHMEN = {
    "sigma_zul_MPa": (500.0, "a: ITER-Kriterium 2/3 Sy, Guete C3 (Sy>750 MPa); C1 waere 667 MPa"),
    "dehnung_zul": (0.003, "g: REBCO irreversibel 0,45-0,72 % (Barth 2015); ARC <0,2 %; hier 0,3 %"),
    "kern_zul_W_m3": (2000.0, "a: ARIES-CS 2 mW/cm3 (ungeprueft); EU-DEMO streng 50 W/m3 (g)"),
    "fluenz_zul_n_cm2": (3e18, "g: ARC (Sorbom 2015), untere Schranke"),
    "lambda_abschirm_m": (0.10, "a: e-Faltlaenge Package-Mischung; W allein 0,061 m (Windsor 2021, g)"),
    "k0_W_m3_je_MW_m2": (1.0e7, "a: Kernheizung direkt hinter der Erstwand je MW/m2 Neutronenwandlast"),
    "fluss_je_MW_m2": (4.4e13, "a: 14-MeV-Neutronen n/cm2/s je MW/m2 (1 MW/m2 = 4,4e13), x3 fuer gestreute schnelle"),
    "spitzenfaktor_wand": (2.0, "a: Spitze/Mittel Neutronenwandlast (ARIES-CS 5,3/2,6)"),
    "betriebsjahre": (20.0, "a: Volllastjahre"),
    "spalte_m": (0.10, "a: Spalte, thermische Abschirmung, Toleranzen, nicht abschirmend"),
    "package_min_m": (1.0, "a: Erstwand + Blanket + Abschirmung + Vakuumgefaess min. (ARIES-CS ~1,0-1,2 m, ungeprueft)"),
    "T_betrieb_K": (20.0, "a: HTS-Betriebstemperatur"),
    "f_sc": (0.30, "a: Anteil Band am Wickelpaketquerschnitt"),
    "t_band_m": (1.0e-4, "a: Banddicke inkl. Kupfer"),
    "auslastung_zul": (0.7, "a: J_op / J_c(B_peak, T_betrieb) hoechstens 70 %"),
    "marge_zul_K": (5.0, "a: Temperaturmarge"),
}
A = {k: v[0] for k, v in ANNAHMEN.items()}


def plasma_laden(studie_ordner: Path) -> None:
    """Fremdes Plasma (z. B. ConStellaration-QI): sim/kopplung/<studie>/plasma.json setzt WOUT und Massstab L.
    Ohne Datei bleibt unser QA-Plasma (qa_nfp2_A45). Siehe stellarator/constellaration_bruecke.py."""
    global WOUT, L
    f = studie_ordner / "plasma.json"
    if f.exists():
        d = json.loads(f.read_text()); WOUT = PROJEKT / d["wout"]; L = float(d["L"])


def ordner(studie: str) -> Path:
    o = WURZEL / studie; (o / "punkte").mkdir(parents=True, exist_ok=True); return o


def log(studie: str, text: str) -> None:
    z = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{studie}] {text}"
    print(z, flush=True)
    with open(ordner(studie) / "lauf.log", "a") as f:
        f.write(z + "\n")


# ---------------------------------------------------------------- 1. Spulen
def schritt_spulen(p: dict, po: Path) -> dict:
    if (po / "stufe2.json").exists():
        return json.loads((po / "stufe2.json").read_text())
    name = f"_kopplung_{po.parent.parent.name}_{po.name}"
    befehl = [str(PY_OPT), "-m", "invers.stufe2_spulen", "--wout", str(WOUT), "--name", name,
              "--n_spulen", str(int(round(p["n_basis"]))), "--ordnung", "6", "--R1", str(p.get("R1", 0.5)),
              "--abstand_ss", str(p.get("abstand_ss", 0.1)),
              "--abstand_sp", str(p["abstand_sp"]), "--laenge_max", str(round(p["n_basis"]) * p["laenge_je"]),
              "--kraft_gewicht", str(p["kraft_gewicht"]), "--maxiter", "400"]
    r = subprocess.run(befehl, cwd=PROJEKT, capture_output=True, text=True, env={"JAX_PLATFORMS": "cpu",
                       "OMP_NUM_THREADS": "4", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())})
    quelle = PROJEKT / "sim" / "invers" / name
    if r.returncode != 0:
        raise RuntimeError("Stufe 2: " + r.stderr[-1500:])
    for f in ("stufe2.json", "spulen.json", "biot_savart.json"):
        shutil.move(quelle / f, po / f)
    shutil.rmtree(quelle, ignore_errors=True)
    return json.loads((po / "stufe2.json").read_text())


# ---------------------------------------------------------------- 2. Geometrie (.venv-opt)
def geometrie(po: Path) -> None:
    """Plasmarand (s = 1) auf Anlagengroesse, Flaeche, Achsenfeld der Einheitsspulen -> Kalibrierung."""
    from simsopt import load
    from simsopt.geo import SurfaceRZFourier
    from scipy.io import netcdf_file
    plasma_laden(po.parent.parent)
    f = SurfaceRZFourier.from_wout(str(WOUT), s=1.0, range="full torus", nphi=200, ntheta=80)
    X = f.gamma() * L
    flaeche = float(f.area() * L ** 2)
    with netcdf_file(str(WOUT), mmap=False) as w:
        rax, zax, nfp = w.variables["raxis_cc"][:].copy(), w.variables["zaxis_cs"][:].copy(), int(w.variables["nfp"].data)
    ph = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    n = np.arange(len(rax))
    Ra = (rax[None] * np.cos(nfp * n[None] * ph[:, None])).sum(1)
    Za = (-zax[None] * np.sin(nfp * n[None] * ph[:, None])).sum(1)     # VMEC: z = sum zs sin(m th - n nfp ph)
    xa = np.c_[Ra * np.cos(ph), Ra * np.sin(ph), Za]                    # Einheitsgeometrie
    bs = load(str(po / "biot_savart.json")); bs.set_points(xa)
    B_achse_u = float(np.linalg.norm(bs.B(), axis=1).mean())
    I_u = abs(bs.coils[0].current.get_value())
    np.save(po / "plasma_rand.npy", X.reshape(-1, 3).astype(np.float32))
    (po / "geometrie.json").write_text(json.dumps({"plasma_flaeche_m2": flaeche, "B_achse_einheit_T": B_achse_u,
                                                   "I_einheit_A": I_u, "L": L}, indent=1))


# ---------------------------------------------------------------- 3. Struktur (wie surrogat.modell/rechne_probe)
def struktur_netz(p: dict, po: Path, geo: dict):
    """Spulen, Waende und Hex-Netz wie in schritt_struktur, ohne Rechnung (Geometriepruefung, Varianten)."""
    from . import spulen as sp, cad, hexmodell as hm
    from .gehaeuse_netz import waende, entflechten
    from .struktur import WP
    d = json.loads((po / "spulen.json").read_text())
    c = {"quelle": "datei", "datei": str(po / "spulen.json"), "R0_m": L * d["R0_m"], "n_punkte": 160}
    spulen, _ = sp.lade_spulensatz(c)
    # Netzgroesse wie bei 16 Spulen halten (MUMPS-Speicher, F-124): Stationen je Spule ~ 16 / Spulenzahl
    stationen = int(2 * round(FEST["stationen"] * 16 / len(spulen) / 2))
    if p.get("loeser") == "mumps_grob":                            # Speicher reicht nicht: Netz 25 % groeber
        stationen = int(2 * round(0.75 * stationen / 2))
    stationen = int(2 * round(p.get("stationen_faktor", 1.0) * stationen / 2))   # Netzstudie (nachrechnung.py)
    hm.QUER["n_wand"] = int(p.get("n_wand", 2)); hm.QUER["n_wp"] = int(p.get("n_wp", 4))
    I = B0 / geo["B_achse_einheit_T"] * geo["I_einheit_A"]           # B ~ I/L: Einheit (R0~1) -> Anlage (x L)
    I *= L
    for s in spulen:
        s.strom = np.sign(s.strom) * I
        if p.get("abtastung") == "kruemmung":                       # dichter an engen Biegungen (F-176)
            s.punkte = cad.neu_abtasten_kruemmung(s.punkte, stationen, np.radians(float(p.get("winkel_max_grad", 10))))
        else:
            s.punkte = cad.neu_abtasten(s.punkte, stationen)
    br = ho = wp = WP_M * np.sqrt(I / 22.11e6)                     # gleiche Stromdichte wie 16 Spulen (Stufe 0)
    w = Namespace(wand_innen=p["wand_innen_m"], wand_seite=p["wand_seite_m"], t_min=p["t_min_m"],
                  t_max=p["t_min_m"] + p["t_zusatz_m"], spiel=FEST["spiel_m"], wand_min=0.003)
    hm.LAGER_ORT = p.get("lager_ort", FEST["lager_ort"])
    hm.VERB_MODUS = p.get("verb_modus", "standard")
    hm.SEITLICH_MIN = float(p.get("seitlich_min", 0.8))
    W = waende(spulen, br, ho, w)
    if p.get("biegung") == "innenkontur":                         # Wand innen in der Kurve kappen (F-180)
        from .gehaeuse_netz import biegegrenze
        W, binfo = biegegrenze(spulen, W, br, ho, float(p.get("biege_grenze", 0.8)))
        (po / "biegegrenze.json").write_text(json.dumps(binfo))
    verlauf = entflechten(spulen, W, br, ho, max(br, ho) / 3, w.spiel, w.wand_min)
    plan = None
    if p.get("plan_von"):                                         # Netzstudie: dieselben Verbinder am selben Ort (F-197)
        hm.PLAN_STRENG = False
        plan = json.loads((ROOT_PUNKT(p["plan_von"]) / "verbinder_plan.json").read_text())
        for v in plan:
            v["i0"] = int(np.linalg.norm(spulen[v["k"]].punkte - np.asarray(v["xk"]), axis=1).argmin())
            v["j0"] = int(np.linalg.norm(spulen[v["m"]].punkte - np.asarray(v["xm"]), axis=1).argmin())
    netz = hm.baue_netz(spulen, br, ho, W, FEST["verguss_m"], p["r_lager_m"], int(p.get("verbinder_je_paar", FEST["verbinder_je_paar"])),
                        int(p.get("verbinder_halb", FEST["verbinder_halb"])), plan=plan)
    runde = 0
    while netz.info["elemente_negativ"] and p.get("biegung") == "innenkontur" and runde < 6:
        # Reparaturschleife (F-182): an den Stationen umgestuelpter Elemente Waende weich um 20 % duennen, neu bauen
        runde += 1
        X, H = np.asarray(netz.X), np.asarray(netz.hexa)
        neg = np.where(hm._jacobi_min(X, H) <= 0)[0]; sid = np.asarray(netz.spule)[neg]
        for kk in np.unique(sid):
            P = spulen[kk].punkte; Nk = len(P)
            for c in X[H[neg[sid == kk]]].mean(1):
                i0 = int(np.argmin(np.linalg.norm(P - c, axis=1)))
                for d_ in range(-3, 4):
                    f_ = 1 - 0.2 * (1 - abs(d_) / 4)
                    for q in ("innen", "aussen", "links", "rechts"):
                        W[kk][q][(i0 + d_) % Nk] *= f_
        netz = hm.baue_netz(spulen, br, ho, W, FEST["verguss_m"], p["r_lager_m"], int(p.get("verbinder_je_paar", FEST["verbinder_je_paar"])),
                            int(p.get("verbinder_halb", FEST["verbinder_halb"])), plan=plan)
        (po / "reparatur.json").write_text(json.dumps({"runden": runde, "negativ": netz.info["elemente_negativ"]}))
    if netz.info["elemente_negativ"]:
        raise RuntimeError(f"{netz.info['elemente_negativ']} Elemente mit negativer Jacobi-Determinante")
    (po / "verbinder_plan.json").write_text(json.dumps([
        v | {"xk": spulen[v["k"]].punkte[v["i0"]].tolist(), "xm": spulen[v["m"]].punkte[v["j0"]].tolist()}
        for v in netz.info["verbinder"] if v["ok"]]))
    return netz, spulen, br, ho, wp, I, stationen, verlauf, W


def werkstoffe(p: dict) -> dict:
    """Werkstoffe je Bereich. Abkuehlen (F-200): schrumpf_* = integrale Kontraktion 293 K -> Betrieb (positiv, z. B. 0.003).
    Die Stahlstruktur schrumpft frei mit (Stuetzen folgen), Spannung entsteht nur aus dem Unterschied zum Stahl:
    Eigendehnung eps_th = -(schrumpf_i - schrumpf_stahl). Stahl und Verbinder bleiben bei null, starre Lager ohne Artefakt."""
    from .struktur import WP
    st = float(p.get("schrumpf_stahl", 0.0))
    th = lambda k: -(float(p[k]) - st) if k in p else 0.0
    return {1: {"E_Pa": WP["E_Pa"], "nu": WP["nu"], "eps_th": th("schrumpf_wp")},
            2: {"E_Pa": FEST["E_verguss_GPa"] * 1e9, "nu": 0.3, "eps_th": th("schrumpf_verguss")},
            3: {"E_Pa": 200e9, "nu": 0.3}, 4: {"E_Pa": p["E_verbinder_GPa"] * 1e9, "nu": 0.3}}


def schritt_struktur(p: dict, po: Path, geo: dict, timeout_s: float = 2400) -> tuple[dict, list, list]:
    from . import hexmodell as hm
    from .struktur import WP
    if p.get("loeser") == "iterativ":
        timeout_s = min(timeout_s, 900)
    netz, spulen, br, ho, wp, I, stationen, verlauf, W = struktur_netz(p, po, geo)
    f, F = hm.lorentzdichte(netz, spulen, br, ho)
    fall = po / "elmer"
    shutil.rmtree(fall, ignore_errors=True); fall.mkdir()
    mat = werkstoffe(p)
    hm.schreibe_fall(fall, netz, f, mat, "iterativ" if p.get("loeser") == "iterativ" else "mumps")
    t = hm.rechne(fall, timeout_s)
    U = hm.verschiebung(fall, netz)
    vm = hm.spannungen(netz, U, mat)
    k = hm.kennzahlen(netz, U, vm)
    k["kraft_MN_max_je_spule"] = float(np.linalg.norm(F, axis=1).max() / 1e6)
    k["I_spule_MA"] = I / 1e6; k["wickelpaket_m"] = wp; k["stationen"] = stationen; k["loeser"] = p.get("loeser", "mumps")
    k["verbinder_ok"] = int(sum(v["ok"] for v in netz.info["verbinder"]))
    k["verbinder_kandidaten"] = len(netz.info["verbinder"])
    k["durchdringung_punkte"] = int(verlauf[-1]) if len(verlauf) else 0
    k["elmer_s"] = t
    hm.als_vtu(netz, po / "struktur.vtu", {"vonmises_MPa": vm / 1e6}, {"verschiebung_m": U})
    shutil.rmtree(fall)
    return k, spulen, W


# ---------------------------------------------------------------- 4. Package + 5. Temperatur
def huelle_abstand(spulen, W, wp: float, baum, teile: int = 4, je_seite: int = 6) -> tuple[np.ndarray, dict]:
    """Abstand Plasma - ganze Gehaeuseaussenflaeche (alle vier Seiten mit Ecken), auch zwischen den Stationen (F-197).
    Die alte Messung nimmt nur die Mitte der Innenwand an den Stationen: Seitenwaende und Ecken fehlen dort."""
    from . import spulen as sp
    u = np.linspace(0, 1, je_seite); f = np.arange(teile) / teile
    alle, seiten = [], {q: np.inf for q in ("innen", "aussen", "links", "rechts")}
    for s, w in zip(spulen, W):
        t, n, b = sp.rahmen(s)
        n0, n1 = -(wp / 2 + w["innen"]), wp / 2 + w["aussen"]
        b0, b1 = -(wp / 2 + w["links"]), wp / 2 + w["rechts"]
        lin = lambda a_, c_: a_[:, None] + (c_ - a_)[:, None] * u[None]
        voll = lambda x: np.broadcast_to(x[:, None], (len(x), je_seite))
        for q, (un, ub) in {"innen": (voll(n0), lin(b0, b1)), "aussen": (voll(n1), lin(b0, b1)),
                            "links": (lin(n0, n1), voll(b0)), "rechts": (lin(n0, n1), voll(b1))}.items():
            X = s.punkte[:, None] + un[..., None] * n[:, None] + ub[..., None] * b[:, None]
            X = (X[:, None] * (1 - f)[None, :, None, None] + np.roll(X, -1, 0)[:, None] * f[None, :, None, None]).reshape(-1, 3)
            d, _ = baum.query(X)
            seiten[q] = min(seiten[q], float(d.min())); alle.append(d)
    return np.concatenate(alle), seiten


def schritt_package(spulen, W, geo: dict, s2: dict, WP_M: float = WP_M, huelle: bool = False) -> dict:
    from scipy.spatial import cKDTree
    from . import spulen as sp
    rand = np.load(geo["_ordner"] / "plasma_rand.npy")
    baum = cKDTree(rand)
    frei = []
    for s, w in zip(spulen, W):
        t, n, b = sp.rahmen(s)
        innen = s.punkte - n * (WP_M / 2 + w["innen"])[:, None]          # Gehaeuse-Innenflaeche (zum Plasma)
        dist, _ = baum.query(innen)
        frei.append(dist)
    frei = np.concatenate(frei)
    g_alt = float(frei.min())
    d_h, seiten = huelle_abstand(spulen, W, WP_M, baum)
    g_min = float(d_h.min()) if huelle else g_alt
    if huelle:
        frei = d_h
    abschirm = max(0.0, g_min - A["spalte_m"])                            # alles ausser Spalten schirmt ab
    gamma_mittel = 0.8 * P_FUS_MW / geo["plasma_flaeche_m2"]              # MW/m2 Neutronenwandlast
    gamma_spitze = A["spitzenfaktor_wand"] * gamma_mittel
    abschw = np.exp(-abschirm / A["lambda_abschirm_m"])
    q_wp = A["k0_W_m3_je_MW_m2"] * gamma_spitze * abschw
    fluenz = 3 * A["fluss_je_MW_m2"] * gamma_spitze * abschw * A["betriebsjahre"] * 3.156e7
    # Supraleiter: Feld am Rand des Wickelpakets (Mitte der 4 Seiten je Station), Filamentmodell aller Spulen.
    # (Auf der Mittellinie hebt sich das Eigenfeld auf -> B_mittellinie aus Stufe 2 unterschaetzt die Spitze.)
    seg = sp.segmente(spulen); Bmax = 0.0
    for s in spulen:
        t, n, b = sp.rahmen(s)
        x = np.vstack([s.punkte + v * WP_M / 2 for v in (n, -n, b, -b)])
        Bmax = max(Bmax, float(np.linalg.norm(sp.biot_savart(x, seg), axis=1).max()))
    B_peak = Bmax
    I = B0 / geo["B_achse_einheit_T"] * geo["I_einheit_A"] * L
    J_op = I / WP_M ** 2

    def Je_c(B, T):      # Senatore 2024 / Pardo 2026, ungünstigster Winkel (theta = 30 grad -> Nenner maximal)
        Kc = 2638e2 * np.exp(-(T - 4.2) / 20.0) / (1 + B / 11.44) ** 1.188      # A/m Bandbreite
        return A["f_sc"] * Kc / A["t_band_m"]
    ausl = J_op / Je_c(B_peak, A["T_betrieb_K"])
    T_cs = 4.2 + 20.0 * np.log(A["f_sc"] * 2638e2 / A["t_band_m"] / (1 + B_peak / 11.44) ** 1.188 / J_op)
    return {"freiraum_alt_m": g_alt, "freiraum_huelle_m": float(d_h.min()), "freiraum_seiten_m": seiten,
            "freiraum_min_m": g_min, "freiraum_p05_m": float(np.quantile(frei, 0.05)),
            "freiraum_median_m": float(np.median(frei)), "abschirmung_m": abschirm,
            "package_passt": bool(abschirm >= A["package_min_m"]),
            "wandlast_mittel_MW_m2": gamma_mittel, "wandlast_spitze_MW_m2": gamma_spitze,
            "kernheizung_wp_W_m3": float(q_wp), "fluenz_n_cm2": float(fluenz),
            "B_leiter_T": float(B_peak), "J_op_MA_m2": J_op / 1e6, "auslastung": float(ausl),
            "T_cs_K": float(T_cs), "marge_K": float(T_cs - A["T_betrieb_K"])}


def bewerten(e: dict) -> dict:
    s, pk = e["struktur"], e["package"]
    dehnung = s["wickelpaket"]["vm_p99_MPa"] * 1e6 / 100e9
    g = {"stahl_p99": s["stahl"]["vm_p99_MPa"] <= A["sigma_zul_MPa"],
         "dehnung_wp": dehnung <= A["dehnung_zul"],
         "package": pk["package_passt"],
         "kernheizung": pk["kernheizung_wp_W_m3"] <= A["kern_zul_W_m3"],
         "fluenz": pk["fluenz_n_cm2"] <= A["fluenz_zul_n_cm2"],
         "auslastung": pk["auslastung"] <= A["auslastung_zul"],
         "marge": pk["marge_K"] >= A["marge_zul_K"],
         "feld_Bn": e["spulen"]["Bn_rel_mittel"] <= 3e-3,
         "durchdringung": s["durchdringung_punkte"] == 0}
    return {"dehnung_wp": dehnung, "grenzen": g, "alle_ok": all(g.values())}


def rechne_punkt(studie: str, nr: int, p: dict) -> dict:
    po = ordner(studie) / "punkte" / f"{nr:04d}"; po.mkdir(parents=True, exist_ok=True)
    plasma_laden(ordner(studie))
    if (po / "ergebnis.json").exists():
        return json.loads((po / "ergebnis.json").read_text())
    p = REFERENZ | {"lager_ort": FEST["lager_ort"]} | p
    (po / "param.json").write_text(json.dumps(p, indent=1))
    z = {}; t0 = time.time()
    s2 = schritt_spulen(p, po); z["spulen_s"] = time.time() - t0
    if not (po / "geometrie.json").exists():
        subprocess.run([str(PY_OPT), "-m", "stellarator.kopplung", "_geometrie", str(po)], cwd=PROJEKT, check=True,
                       env={"OMP_NUM_THREADS": "4", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())})
    geo = json.loads((po / "geometrie.json").read_text()); z["geometrie_s"] = time.time() - t0 - z["spulen_s"]
    t1 = time.time()
    k, spulen, W = schritt_struktur(p, po, geo); z["struktur_s"] = time.time() - t1
    pk = schritt_package(spulen, W, geo | {"_ordner": po}, s2, k["wickelpaket_m"], huelle=p.get("freiraum") == "huelle")
    e = {"param": p, "spulen": {kk: s2[kk] for kk in s2 if kk.startswith(("Bn", "kraft_je", "B_mittel", "laenge", "abstand"))},
         "geometrie": geo, "struktur": k, "package": pk, "zeiten": z | {"gesamt_s": time.time() - t0},
         "annahmen": ANNAHMEN}
    e["bewertung"] = bewerten(e)
    (po / "ergebnis.json").write_text(json.dumps(e, indent=1, default=float))
    return e


# ---------------------------------------------------------------- DOE
def doe(studie: str, n: int, seed: int = 7) -> list[dict]:
    pfad = ordner(studie) / "doe.json"
    if pfad.exists():
        return json.loads(pfad.read_text())["punkte"]
    from scipy.stats import qmc
    namen = list(PARAM)
    u = qmc.LatinHypercube(d=len(namen), seed=seed).random(n)
    pk = []
    for zeile in u:
        q = {}
        for x, k in zip(zeile, namen):
            lo, hi, lg = PARAM[k]
            q[k] = float(np.exp(np.log(lo) + x * (np.log(hi) - np.log(lo))) if lg else lo + x * (hi - lo))
        q["n_basis"] = int(round(q["n_basis"])); q["verbinder_je_paar"] = int(round(q["verbinder_je_paar"]))
        pk.append(q)
    pfad.write_text(json.dumps({"parameter": PARAM, "fest": FEST, "punkte": pk}, indent=1))
    return pk


def punkt_extern(studie: str, nr: int, n: int, speicher: str, loeser: str) -> int:
    """Einen DOE-Punkt in eigenem systemd-Scope rechnen: ein Speicherausreisser (OOM) beendet nur diesen Punkt."""
    befehl = ["systemd-run", "--user", "--scope", "-q", "-p", f"MemoryMax={speicher}", "-p", "MemorySwapMax=0",
              sys.executable, "-m", "stellarator.kopplung", "punkt", "--studie", studie, "--nr", str(nr), "--n", str(n),
              "--doe", "--p", f"loeser={loeser}"]
    with open(ordner(studie) / "punkte_konsole.log", "a") as f:
        return subprocess.run(befehl, cwd=PROJEKT, stdout=f, stderr=subprocess.STDOUT).returncode


def lauf(studie: str, n: int, stunden: float, speicher: str = "11G") -> None:
    o = ordner(studie); ende = time.time() + stunden * 3600
    for nr, p in enumerate(doe(studie, n)):
        st = json.loads((o / "steuerung.json").read_text()) if (o / "steuerung.json").exists() else {}
        if st.get("stopp") or time.time() > ende:
            log(studie, "Stopp (steuerung.json oder Zeit)"); break
        if (o / "punkte" / f"{nr:04d}" / "ergebnis.json").exists() or (o / "punkte" / f"{nr:04d}" / "fehler.txt").exists():
            continue
        t0 = time.time()
        po = o / "punkte" / f"{nr:04d}"
        try:
            # direkter Loeser; bei Speichermangel NICHT mehr groeberes Netz (mumps_grob aenderte die Verbinderlaenge,
            # F-137), sondern zweiter Versuch mit 22 GB
            for loeser, mem in (("mumps", speicher), ("mumps", "22G")):
                shutil.rmtree(po / "elmer", ignore_errors=True)
                rc = punkt_extern(studie, nr, n, mem, loeser)
                if (po / "ergebnis.json").exists():
                    break
                log(studie, f"{nr:04d} {loeser}: Abbruch (Rueckgabe {rc}, 137/OOM = Speicher)")
            if not (po / "ergebnis.json").exists():
                raise RuntimeError("beide Loeser gescheitert")
            e = json.loads((po / "ergebnis.json").read_text())
            b = e["bewertung"]; s = e["struktur"]; pk = e["package"]
            log(studie, f"{nr:04d} ok {time.time()-t0:.0f} s | Bn {e['spulen']['Bn_rel_mittel']:.2e} | p99 {s['stahl']['vm_p99_MPa']:.0f} MPa"
                        f" | frei {pk['freiraum_min_m']:.2f} m | q_wp {pk['kernheizung_wp_W_m3']:.0f} W/m3 | Ausl. {pk['auslastung']:.2f}"
                        f" | alle ok {b['alle_ok']}")
        except Exception as ex:
            (o / "punkte" / f"{nr:04d}" / "fehler.txt").write_text(traceback.format_exc())
            log(studie, f"{nr:04d} FEHLER {time.time()-t0:.0f} s: {ex}")


def ROOT_PUNKT(von: str) -> Path:
    st, nr = von.split("/"); return WURZEL / st / "punkte" / nr


def tabelle(studie: str) -> None:
    for f in sorted((ordner(studie) / "punkte").glob("*/ergebnis.json")):
        e = json.loads(f.read_text()); s = e["struktur"]; pk = e["package"]
        print(f.parent.name, f"Bn {e['spulen']['Bn_rel_mittel']:.2e}", f"p99 {s['stahl']['vm_p99_MPa']:.0f}",
              f"u {s['u_max_mm']:.0f} mm", f"m {s['stahl']['masse_t']:.0f} t", f"frei {pk['freiraum_min_m']:.2f}",
              f"q {pk['kernheizung_wp_W_m3']:.0f}", f"B {pk['B_leiter_T']:.1f} T", f"Ausl {pk['auslastung']:.2f}",
              {k: v for k, v in e["bewertung"]["grenzen"].items() if not v})


def main(argv=None):
    if argv is None and len(sys.argv) > 2 and sys.argv[1] == "_geometrie":
        return geometrie(Path(sys.argv[2]))
    ap = argparse.ArgumentParser(); ap.add_argument("befehl", choices=["punkt", "lauf", "tabelle"])
    ap.add_argument("--studie", default="test"); ap.add_argument("--nr", type=int, default=0)
    ap.add_argument("--n", type=int, default=100); ap.add_argument("--stunden", type=float, default=12)
    ap.add_argument("--p", nargs="*", default=[]); ap.add_argument("--doe", action="store_true")
    ap.add_argument("--speicher", default="11G")
    ap.add_argument("--von", default="", help="studie/NNNN: Spulen und Parameter uebernehmen (Netzstudie)")
    a = ap.parse_args(argv)
    if a.befehl == "punkt":
        p = {k: (v if k in ("lager_ort", "loeser", "verb_modus", "abtastung", "biegung", "plan_von", "freiraum") else float(v)) for k, v in (x.split("=") for x in a.p)}
        if a.von:                                     # Parameter + Spulen eines frueheren Punkts uebernehmen
            q = ROOT_PUNKT(a.von)
            p = json.loads((q / "param.json").read_text()) | p
            po = ordner(a.studie) / "punkte" / f"{a.nr:04d}"; po.mkdir(parents=True, exist_ok=True)
            for f in ("stufe2.json", "spulen.json", "biot_savart.json", "geometrie.json", "plasma_rand.npy"):
                if not (po / f).exists():
                    shutil.copy(q / f, po / f)
        if a.doe:                                     # Punkt aus dem DOE der Studie (vom Lauf aufgerufen)
            p = doe(a.studie, a.n)[a.nr] | p
        e = rechne_punkt(a.studie, a.nr, p)
        print(json.dumps({k: e[k] for k in ("spulen", "package", "bewertung", "zeiten")}, indent=1, default=float))
        s = e["struktur"]
        print("Struktur:", {k: s[k] for k in ("u_max_mm", "kraft_MN_max_je_spule", "I_spule_MA", "verbinder_ok",
                                               "verbinder_kandidaten", "durchdringung_punkte")}, "Stahl", s["stahl"])
    elif a.befehl == "lauf":
        lauf(a.studie, a.n, a.stunden, a.speicher)
    else:
        tabelle(a.studie)


if __name__ == "__main__":
    main()
