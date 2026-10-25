"""surrogat.py — Fusions-Surrogat: Geometrie -> Parameter -> Berechnung (Elmer) -> Training -> 3D-Vorhersage.

Zwei Anlagen (stellarator/surrogat_anlagen.json):
  w7x     angelehnt an W7-X, Lastparameter B0 (gerechnet bei 2,5 T, Ergebnis ~ (B0/2,5)^2, linear-elastisch)
  qa_1gw  qa_nfp2_A45 HTS, Lastparameter elektrische Netzleistung P_netz -> Stufe 0 -> R0, B0, Wickelpaket
Rechenmodell: stellarator/hexmodell.py (Hex-Netz fester Topologie, Verguss, Verbinder, J x B per UDF).

Befehle (.venv/bin/python -m stellarator.surrogat ...):
  stufe0  --anlage qa_1gw                 Tabelle P_netz -> R0, B0, Wickelpaket (einmalig)
  probe   --anlage w7x [--nr 0]           eine Probe des DOE rechnen (Test)
  lauf    --anlage beide --stunden 4      AUTONOM: DOE abarbeiten (fortsetzbar), danach trainieren
  pause / weiter --anlage beide           anhalten (laufende Probe rechnet fertig, RAM frei) / fortsetzen
  trainiere --anlage w7x                  GP fuer Kennzahlen + POD/GP fuer Felder, Kreuzvalidierung
  vorhersage --anlage w7x --p wand_innen_m=0.05 ... [--B0 2.5 | --P_netz 1000] [--pruefen]
                                          3D-Feld vorhersagen (VTU + Bild); --pruefen rechnet echt nach
Ablage: sim/surrogat/<anlage>/ (doe.json, proben/NNNN.npz, status.json, lauf.log, modell.pkl, steuerung.json)
steuerung.json (vom Waechter/PI oder Mensch editierbar, wird vor jeder Probe gelesen):
  {"pause": false, "stopp": false, "timeout_min": 40, "loeser": "mumps", "ueberspringen": [nr, ...]}
"""
from __future__ import annotations
import argparse, json, pickle, shutil, subprocess, sys, time, traceback
from argparse import Namespace
from pathlib import Path
import numpy as np

from . import spulen as sp, cad, hexmodell as hm
from .gehaeuse_netz import waende, entflechten
from .lauf import PROJEKT

ANLAGEN = json.loads((Path(__file__).resolve().parent / "surrogat_anlagen.json").read_text())
WURZEL = PROJEKT / "sim" / "surrogat"
STAHL_E, NU = 200e9, 0.3
KENN = ["stahl.vm_max_MPa", "stahl.vm_p99_MPa", "stahl.vm_mittel_MPa", "stahl.masse_t", "u_max_mm",
        "wickelpaket.vm_p99_MPa", "verguss.vm_max_MPa", "verguss.vm_p99_MPa", "verbinder.vm_max_MPa"]
LOG_PARAM = {"E_verguss_GPa", "E_verbinder_GPa"}            # logarithmisch abgetastet


def ordner(anlage: str) -> Path:
    o = WURZEL / anlage; (o / "proben").mkdir(parents=True, exist_ok=True); return o


def log(anlage: str, text: str) -> None:
    z = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{anlage}] {text}"
    print(z, flush=True)
    with open(ordner(anlage) / "lauf.log", "a") as f:
        f.write(z + "\n")


# ------------------------------------------------------------------ Stufe 0: P_netz -> Auslegung
def stufe0_tabelle(anlage: str, werte=None) -> dict:
    cfg = ANLAGEN[anlage]; L = cfg["last"]
    pfad = ordner(anlage) / "stufe0_tabelle.json"
    if pfad.exists():
        return json.loads(pfad.read_text())
    lo, hi = L["bereich"]
    werte = werte or list(np.linspace(lo - 100, hi + 100, 11))
    tab = []
    for P in werte:
        name = f"surrogat_stufe0_{int(P)}"
        r = subprocess.run([sys.executable, "-m", "invers.stufe0_bilanz", "--name", name, "--P_netz", str(P), *L["stufe0"]],
                           cwd=PROJEKT, capture_output=True, text=True, check=True)
        b = json.loads((PROJEKT / "sim" / "invers" / name / "bilanz.json").read_text())
        e = b["auslegung"][L["leiter"]]
        shutil.rmtree(PROJEKT / "sim" / "invers" / name)
        if e.get("machbar"):
            tab.append({"P_netz_MW": P, "R0_m": e["R0_m"], "B0_T": e["B0_T"], "wickelpaket_m": e["wickelpaket_m"],
                        "I_spule_MA": e["I_spule_MA"], "P_fus_MW": b["leistung"]["P_fus_MW"]})
    out = {"leiter": L["leiter"], "tabelle": tab, "hinweis": "Stufe 0 (0-D, +-30 %), lineare Interpolation"}
    pfad.write_text(json.dumps(out, indent=2))
    return out


def auslegung(anlage: str, P: float) -> dict:
    tab = stufe0_tabelle(anlage)["tabelle"]
    x = [t["P_netz_MW"] for t in tab]
    return {k: float(np.interp(P, x, [t[k] for t in tab])) for k in tab[0]}


# ------------------------------------------------------------------ eine Probe
def lastwert(anlage: str, p: dict) -> float:
    L = ANLAGEN[anlage]["last"]
    return p.get(L["art"], L.get("ref", 0.5 * sum(L["bereich"])))


def verbinder_plan(anlage: str, n_test: int = 24) -> list[dict]:
    """Feste Verbinderliste je Anlage: nur Verbinder, die in den ersten n_test DOE-Proben alle gueltig sind
    (Wandstaerken verschieben die Seitenflaechen -> sonst wechselt die Topologie von Probe zu Probe)."""
    pfad = ordner(anlage) / "verbinder_plan.json"
    if pfad.exists():
        return json.loads(pfad.read_text())["plan"]
    proben = doe(anlage, 150)[:n_test]
    schluessel = lambda v: tuple(v[x] for x in ("k", "m", "i0", "j0", "fk", "fm", "rs", "rev"))
    gueltig, alle = None, {}
    for p in proben:
        netz = modell(anlage, p, plan=None)[3]
        ok = {schluessel(v) for v in netz.info["verbinder"] if v["ok"]}
        alle |= {schluessel(v): v for v in netz.info["verbinder"]}
        gueltig = ok if gueltig is None else gueltig & ok
    plan = [{k: alle[s][k] for k in ("k", "m", "i0", "j0", "fk", "fm", "rs", "rev")} for s in sorted(gueltig)]
    pfad.write_text(json.dumps({"n_test": n_test, "kandidaten": len(alle), "plan": plan}, indent=1))
    log(anlage, f"Verbinderplan: {len(plan)} von {len(alle)} Verbindern in allen {n_test} Testgeometrien gueltig")
    return plan


def modell(anlage: str, p: dict, plan="auto"):
    """Spulen, Wickelpaket, Waende, Netz fuer Parametersatz p (Last: P_netz bzw. B0 = ref)."""
    cfg = ANLAGEN[anlage]
    fall = json.loads((PROJEKT / cfg["fall"]).read_text()); c = fall["spulen"]
    kz = json.loads((PROJEKT / "sim" / "stellarator" / "bewertung" / fall["name"] / "kennzahlen.json").read_text())
    faktor = kz["strom"]["kalibrierfaktor"]
    info = {}
    if cfg["last"]["art"] == "P_netz":
        a = auslegung(anlage, p["P_netz"])
        R0_ref, B0_ref = c["R0_m"], c["B0_achse_T"]
        c = dict(c, R0_m=a["R0_m"], B0_achse_T=a["B0_T"], wickel_breite_m=a["wickelpaket_m"], wickel_hoehe_m=a["wickelpaket_m"])
        faktor *= (a["B0_T"] / B0_ref) * (a["R0_m"] / R0_ref)      # B ~ I/R  ->  I ~ B0 R0
        info = a
    spulen, _ = sp.lade_spulensatz(c)
    for s in spulen:
        s.strom *= faktor
        s.punkte = cad.neu_abtasten(s.punkte, cfg["stationen"])
    br, ho = c["wickel_breite_m"], c["wickel_hoehe_m"]
    w = Namespace(wand_innen=p["wand_innen_m"], wand_seite=p["wand_seite_m"], t_min=p["t_min_m"],
                  t_max=p["t_min_m"] + p["t_zusatz_m"], spiel=cfg["spiel_m"], wand_min=0.003)
    W = waende(spulen, br, ho, w)
    entflechten(spulen, W, br, ho, max(br, ho) / 3, w.spiel, w.wand_min)
    netz = hm.baue_netz(spulen, br, ho, W, p["verguss_m"], p.get("r_lager_m", cfg["r_lager_m"]), cfg["verbinder_je_paar"],
                        cfg.get("verbinder_halb", 1), plan=verbinder_plan(anlage) if plan == "auto" else plan)
    return spulen, br, ho, netz, info


def material(p: dict) -> dict:
    from .struktur import WP
    return {1: {"E_Pa": WP["E_Pa"], "nu": WP["nu"]}, 2: {"E_Pa": p["E_verguss_GPa"] * 1e9, "nu": 0.3},
            3: {"E_Pa": STAHL_E, "nu": NU}, 4: {"E_Pa": p["E_verbinder_GPa"] * 1e9, "nu": NU}}


def rechne_probe(anlage: str, p: dict, ziel: Path, timeout_s: float, loeser: str = "mumps", vtu: bool = False) -> dict:
    """Ein FEM-Lauf -> npz (Parameter, Kennzahlen, Felder). Elmer-Rohdaten werden danach geloescht."""
    t0 = time.time(); zeiten = {}
    spulen, br, ho, netz, info = modell(anlage, p); zeiten["netz_s"] = time.time() - t0
    o = ordner(anlage)
    topo = o / "topologie.json"
    t = {"knoten": len(netz.X), "elemente": len(netz.hexa)}          # Lagerflaeche = Randbedingung, nicht Topologie
    if not topo.exists():
        topo.write_text(json.dumps(t))
    gleich = json.loads(topo.read_text()) == t
    schlecht = [v for v in netz.info["verbinder"] if not v["ok"]]
    if schlecht:
        raise RuntimeError(f"{len(schlecht)} Verbinder mit umgestuelpten Elementen (Plan gilt hier nicht)")
    if netz.info["elemente_negativ"]:
        raise RuntimeError(f"{netz.info['elemente_negativ']} Elemente mit negativer Jacobi-Determinante")
    # Last: bei fester Wickelpaket-Geometrie (W7-X) einmal rechnen und zwischenspeichern
    t1 = time.time()
    cache = o / "kraft_cache.npz"
    if ANLAGEN[anlage]["last"]["art"] == "B0" and cache.exists() and gleich:
        z = np.load(cache); f = np.zeros_like(netz.X); f[z["idx"]] = z["f"]; F = z["F"]
    else:
        f, F = hm.lorentzdichte(netz, spulen, br, ho)
        if ANLAGEN[anlage]["last"]["art"] == "B0" and gleich:
            idx = np.where(np.any(f != 0, axis=1))[0]
            np.savez(cache, idx=idx, f=f[idx], F=F)
    zeiten["last_s"] = time.time() - t1
    fall = ziel.with_suffix("")
    if fall.exists():
        shutil.rmtree(fall)
    fall.mkdir(parents=True)
    mat = material(p)
    hm.schreibe_fall(fall, netz, f, mat, loeser)
    zeiten["elmer_s"] = hm.rechne(fall, timeout_s)
    log_kurz = (fall / "solve.log").read_text()[-3000:]
    U = hm.verschiebung(fall, netz)
    vm = hm.spannungen(netz, U, mat)
    k = hm.kennzahlen(netz, U, vm)
    k["kraft_MN_max_je_spule"] = float(np.linalg.norm(F, axis=1).max() / 1e6)
    k["auslegung"] = info
    k["netz"] = {kk: v for kk, v in netz.info.items() if kk != "verbinder"}
    k["zeiten"] = zeiten | {"gesamt_s": time.time() - t0}
    k["topologie_gleich"] = gleich
    if vtu:
        hm.als_vtu(netz, ziel.with_suffix(".vtu"), {"vonmises_MPa": vm / 1e6}, {"verschiebung_m": U})
    np.savez_compressed(ziel, param=json.dumps(p), kenn=json.dumps(k), vm=vm.astype(np.float32),
                        U=U.astype(np.float32), X=netz.X.astype(np.float32) if ANLAGEN[anlage]["last"]["art"] != "B0" else np.zeros(0))
    if "Linear System" in log_kurz and "did not converge" in log_kurz.lower():
        k["warnung"] = "Loeser nicht konvergiert"
    shutil.rmtree(fall)
    return k


# ------------------------------------------------------------------ DOE + autonomer Lauf
def doe(anlage: str, n: int, seed: int = 1) -> list[dict]:
    pfad = ordner(anlage) / "doe.json"
    if pfad.exists():
        return json.loads(pfad.read_text())["proben"]
    from scipy.stats import qmc
    cfg = ANLAGEN[anlage]
    namen = list(cfg["parameter"])
    if cfg["last"]["art"] != "B0":
        namen.append(cfg["last"]["art"])
    bereiche = [cfg["parameter"].get(k, cfg["last"]["bereich"]) for k in namen]
    U = qmc.LatinHypercube(d=len(namen), seed=seed).random(n)
    proben = []
    for u in U:
        p = {}
        for k, (lo, hi), x in zip(namen, bereiche, u):
            p[k] = float(np.exp(np.log(lo) + x * np.log(hi / lo)) if k in LOG_PARAM else lo + x * (hi - lo))
        proben.append(p)
    # Probe 0 = Mitte (Referenz, auch fuer Topologie und Kraft-Cache)
    proben.insert(0, {k: float(np.sqrt(lo * hi) if k in LOG_PARAM else 0.5 * (lo + hi)) for k, (lo, hi) in zip(namen, bereiche)})
    pfad.write_text(json.dumps({"namen": namen, "bereiche": bereiche, "log": sorted(LOG_PARAM), "proben": proben}, indent=1))
    return proben


def steuerung(anlage: str) -> dict:
    pfad = ordner(anlage) / "steuerung.json"
    std = {"pause": False, "stopp": False, "timeout_min": 40, "loeser": "mumps", "ueberspringen": [], "notiz": ""}
    if not pfad.exists():
        pfad.write_text(json.dumps(std, indent=1))
    try:
        return std | json.loads(pfad.read_text())
    except Exception:                    # halb geschriebene Datei -> Standard
        return std


def status(anlage: str, **kw) -> dict:
    pfad = ordner(anlage) / "status.json"
    s = json.loads(pfad.read_text()) if pfad.exists() else {}
    s |= kw | {"zeit": time.strftime("%Y-%m-%d %H:%M:%S")}
    pfad.write_text(json.dumps(s, indent=1, ensure_ascii=False))
    return s


RAM_BEDARF_GB = {"w7x": 19.0, "qa_1gw": 6.0}          # MUMPS-Spitze + Reserve (gemessen bis 17,5 / ~4 GB)
PLATTE_MIN_GB = 5.0


def speicher() -> tuple[float, float]:
    """(RAM verfuegbar, Platte frei) in GB."""
    mi = {l.split(":")[0]: int(l.split()[1]) / 1e6 for l in open("/proc/meminfo")}
    return mi["MemAvailable"], shutil.disk_usage(PROJEKT).free / 1e9


def lauf(anlagen: list[str], stunden: float, n: int, min_train: int = 12) -> None:
    ende = time.time() + 3600 * stunden
    listen = {a: doe(a, n) for a in anlagen}
    dauer = {a: [] for a in anlagen}
    fehler = {a: json.loads((ordner(a) / "status.json").read_text()).get("fehler_nr", []) if (ordner(a) / "status.json").exists() else []
              for a in anlagen}
    for a in anlagen:
        log(a, f"START Lauf, Budget {stunden} h, {len(listen[a])} Proben im DOE")
        status(a, zustand="laeuft", pid=__import__("os").getpid(), ende_budget=time.strftime("%H:%M", time.localtime(ende)))
    while True:
        offen = {a: [i for i in range(len(listen[a])) if not (ordner(a) / "proben" / f"{i:04d}.npz").exists()
                     and i not in fehler[a] and i not in steuerung(a)["ueberspringen"]] for a in anlagen}
        aktiv = [a for a in anlagen if offen[a] and not steuerung(a)["stopp"]]
        if not aktiv:
            break
        if all(steuerung(x)["pause"] for x in aktiv):           # Pause: nichts rechnen, Budget verlaengern
            for x in aktiv:
                status(x, zustand="pause")
            t_p = time.time(); time.sleep(20); ende += time.time() - t_p
            continue
        aktiv = [x for x in aktiv if not steuerung(x)["pause"]]
        ram, platte = speicher()
        if platte < PLATTE_MIN_GB:
            for x in anlagen:
                log(x, f"STOPP: Platte nur noch {platte:.1f} GB frei"); status(x, zustand="stopp_platte")
            break
        passt = [x for x in aktiv if RAM_BEDARF_GB.get(x, 8.0) <= ram]
        if not passt:
            for x in aktiv:
                status(x, zustand="wartet_speicher", ram_frei_GB=round(ram, 1))
            log(aktiv[0], f"warte: RAM frei {ram:.1f} GB < Bedarf {min(RAM_BEDARF_GB.get(x, 8.0) for x in aktiv)} GB")
            time.sleep(60); continue
        # abwechselnd: die Anlage mit weniger fertigen Proben zuerst (nur solche, fuer die der RAM reicht)
        a = min(passt, key=lambda x: len(list((ordner(x) / "proben").glob("*.npz"))))
        st = steuerung(a)
        schaetz = np.median(dauer[a]) if dauer[a] else 600
        if time.time() + 1.2 * schaetz > ende:
            for x in anlagen:
                log(x, "Zeitbudget erreicht -> keine neue Probe")
            break
        i = offen[a][0]
        status(a, zustand="rechnet", probe=i, offen=len(offen[a]))
        log(a, f"Probe {i}: {json.dumps(listen[a][i])}")
        t0 = time.time()
        try:
            k = rechne_probe(a, listen[a][i], ordner(a) / "proben" / f"{i:04d}.npz", 60 * st["timeout_min"], st["loeser"])
            dauer[a].append(time.time() - t0)
            log(a, f"Probe {i} fertig {time.time() - t0:.0f} s: Stahl vm_max {k['stahl']['vm_max_MPa']:.0f} MPa, "
                   f"p99 {k['stahl']['vm_p99_MPa']:.0f} MPa, u_max {k['u_max_mm']:.2f} mm, Masse {k['stahl']['masse_t']:.0f} t"
                   + (f" WARNUNG {k['warnung']}" if "warnung" in k else ""))
        except Exception as e:
            fehler[a].append(i)
            log(a, f"Probe {i} FEHLER nach {time.time() - t0:.0f} s: {e!r}")
            (ordner(a) / "fehler.log").open("a").write(f"--- Probe {i}\n{traceback.format_exc()}\n")
            shutil.rmtree((ordner(a) / "proben" / f"{i:04d}"), ignore_errors=True)
        fertig = len(list((ordner(a) / "proben").glob("*.npz")))
        ram, platte = speicher()
        status(a, zustand="laeuft", fertig=fertig, fehler_nr=fehler[a], mittel_s=float(np.mean(dauer[a])) if dauer[a] else None,
               ram_frei_GB=round(ram, 1), platte_frei_GB=round(platte, 1))
    for a in anlagen:
        fertig = len(list((ordner(a) / "proben").glob("*.npz")))
        if fertig >= min_train:
            log(a, f"Training mit {fertig} Proben")
            try:
                v = trainiere(a)
                log(a, f"Training fertig: {json.dumps(v['kennzahlen_r2'])}")
            except Exception as e:
                log(a, f"Training FEHLER: {e!r}")
                (ordner(a) / "fehler.log").open("a").write(f"--- Training\n{traceback.format_exc()}\n")
        else:
            log(a, f"nur {fertig} Proben -> kein Training (min {min_train})")
        status(a, zustand="fertig")


# ------------------------------------------------------------------ Training
def _lade(anlage: str):
    meta = json.loads((ordner(anlage) / "doe.json").read_text())
    P, K, VM, U, nr = [], [], [], [], []
    for f in sorted((ordner(anlage) / "proben").glob("*.npz")):
        z = np.load(f)
        k = json.loads(str(z["kenn"]))
        if not k.get("topologie_gleich", True):
            continue
        p = json.loads(str(z["param"]))
        P.append([p[n] for n in meta["namen"]]); K.append(k); VM.append(z["vm"]); U.append(z["U"]); nr.append(int(f.stem))
    return meta, np.array(P), K, np.array(VM), np.array(U), nr


def _norm(meta, P):
    P = np.atleast_2d(np.asarray(P, float)).copy()
    for j, (n, (lo, hi)) in enumerate(zip(meta["namen"], meta["bereiche"])):
        P[:, j] = (np.log(P[:, j] / lo) / np.log(hi / lo)) if n in meta["log"] else (P[:, j] - lo) / (hi - lo)
    return P


def _wert(k: dict, pfad: str) -> float:
    for t in pfad.split("."):
        k = k.get(t, {}) if isinstance(k, dict) else {}
    return float(k) if not isinstance(k, dict) else np.nan


def _gp(X, y):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel as C
    k = C(1.0) * Matern(length_scale=np.full(X.shape[1], 0.5), length_scale_bounds=(0.05, 20), nu=2.5) + WhiteKernel(1e-4, (1e-8, 1e-1))
    return GaussianProcessRegressor(k, normalize_y=True, n_restarts_optimizer=3, random_state=0).fit(X, y)


def _pod(F, r_max: int = 20, energie: float = 0.999):
    mittel = F.mean(0)
    Uu, s, Vt = np.linalg.svd(F - mittel, full_matrices=False)
    e = np.cumsum(s ** 2) / max((s ** 2).sum(), 1e-300)
    r = int(min(r_max, np.searchsorted(e, energie) + 1, len(s)))
    return mittel, Vt[:r], (F - mittel) @ Vt[:r].T


def trainiere(anlage: str, k_fold: int = 5) -> dict:
    meta, P, K, VM, U, nr = _lade(anlage)
    X = _norm(meta, P)
    Y = np.log(np.array([[_wert(k, n) for n in KENN] for k in K]))          # log: positiv, Faktor-Fehler
    gueltig = [j for j in range(len(KENN)) if np.all(np.isfinite(Y[:, j]))]
    # Kreuzvalidierung (k-fach) fuer die Kennzahlen
    rng = np.random.default_rng(0); teil = rng.permutation(len(X)) % k_fold
    vorh = np.full_like(Y, np.nan)
    for f in range(k_fold):
        tr, te = teil != f, teil == f
        for j in gueltig:
            vorh[te, j] = _gp(X[tr], Y[tr, j]).predict(X[te])
    r2 = {KENN[j]: float(1 - np.sum((vorh[:, j] - Y[:, j]) ** 2) / np.sum((Y[:, j] - Y[:, j].mean()) ** 2)) for j in gueltig}
    fehler_proz = {KENN[j]: float(np.median(np.abs(np.exp(vorh[:, j] - Y[:, j]) - 1)) * 100) for j in gueltig}
    gp_k = {KENN[j]: _gp(X, Y[:, j]) for j in gueltig}
    # Felder: POD + GP je Koeffizient (von Mises je Element, Verschiebung je Knoten)
    felder = {}
    for name, F in (("vm", np.log(np.maximum(VM.astype(float), 1e3))), ("U", U.reshape(len(U), -1).astype(float))):
        mittel, basis, koef = _pod(F)
        felder[name] = {"mittel": mittel.astype(np.float32), "basis": basis.astype(np.float32),
                        "gp": [_gp(X, koef[:, i]) for i in range(len(basis))], "r": len(basis)}
    m = {"anlage": anlage, "meta": meta, "kenn": gp_k, "felder": felder, "n_proben": len(X), "proben_nr": nr,
         "kennzahlen_r2": r2, "kennzahlen_fehler_median_proz": fehler_proz}
    with open(ordner(anlage) / "modell.pkl", "wb") as f:
        pickle.dump(m, f)
    v = {k: m[k] for k in ("anlage", "n_proben", "kennzahlen_r2", "kennzahlen_fehler_median_proz")}
    v["pod_moden"] = {n: felder[n]["r"] for n in felder}
    (ordner(anlage) / "validierung.json").write_text(json.dumps(v, indent=1))
    _bild_validierung(anlage, Y, vorh, gueltig)
    return v


def _bild_validierung(anlage, Y, vorh, gueltig):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, (len(gueltig) + 1) // 2, figsize=(3.2 * ((len(gueltig) + 1) // 2), 6.4))
    for a_, j in zip(ax.ravel(), gueltig):
        y, v = np.exp(Y[:, j]), np.exp(vorh[:, j])
        a_.plot(y, v, "o", ms=3); lo, hi = min(y.min(), v.min()), max(y.max(), v.max())
        a_.plot([lo, hi], [lo, hi], "k-", lw=0.8); a_.set_title(KENN[j], fontsize=8)
        a_.set_xlabel("FEM", fontsize=7); a_.set_ylabel("Surrogat", fontsize=7); a_.tick_params(labelsize=6)
    for a_ in ax.ravel()[len(gueltig):]:
        a_.axis("off")
    fig.suptitle(f"{ANLAGEN[anlage]['titel']}: Kreuzvalidierung ({len(Y)} Proben)", fontsize=9)
    fig.tight_layout(); fig.savefig(ordner(anlage) / "validierung.png", dpi=130); plt.close(fig)


# ------------------------------------------------------------------ Vorhersage
def vorhersage(anlage: str, p: dict) -> dict:
    with open(ordner(anlage) / "modell.pkl", "rb") as f:
        m = pickle.load(f)
    meta = m["meta"]; L = ANLAGEN[anlage]["last"]
    x = _norm(meta, [[p[n] for n in meta["namen"]]])
    s = (p.get("B0", L["ref"]) / L["ref"]) ** 2 if L["art"] == "B0" else 1.0
    skal = {"stahl.masse_t": 1.0}
    kenn = {}
    for n, gp in m["kenn"].items():
        mu, sd = gp.predict(x, return_std=True)
        f = skal.get(n, s)
        kenn[n] = {"wert": float(np.exp(mu[0]) * f), "unsicher_faktor": float(np.exp(sd[0]))}
    fe = {}
    for n, d in m["felder"].items():
        c = np.array([g.predict(x)[0] for g in d["gp"]])
        fe[n] = d["mittel"] + c @ d["basis"]
    vm = np.exp(fe["vm"]) * s
    U = fe["U"].reshape(-1, 3) * s
    return {"kennzahlen": kenn, "vm": vm, "U": U, "skalierung_last": s}


def vorhersage_3d(anlage: str, p: dict, name: str = "vorhersage", pruefen: bool = False) -> Path:
    """Vorhersage als VTU + Bild; optional echte FEM-Rechnung zum Vergleich."""
    import pyvista as pv
    v = vorhersage(anlage, p)
    _, _, _, netz, _ = modell(anlage, p)
    o = ordner(anlage) / name; o.mkdir(exist_ok=True)
    hm.als_vtu(netz, o / "vorhersage.vtu", {"vonmises_MPa": v["vm"] / 1e6}, {"verschiebung_m": v["U"]})
    erg = {"parameter": p, "kennzahlen_surrogat": v["kennzahlen"]}
    if pruefen:
        k = rechne_probe(anlage, {kk: vv for kk, vv in p.items() if kk != "B0"}, o / "fem.npz", 3600, vtu=True)
        s = v["skalierung_last"]
        erg["kennzahlen_fem"] = {n: _wert(k, n) * (1.0 if n == "stahl.masse_t" else s) for n in KENN}
    (o / "ergebnis.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))
    g = pv.read(o / "vorhersage.vtu")
    stahl = g.extract_cells(np.where(g.cell_data["material"] >= 3)[0])
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1100))
    pl.add_mesh(stahl, scalars="vonmises_MPa", cmap="turbo", show_scalar_bar=True,
                scalar_bar_args={"title": "von Mises Stahl [MPa] (Surrogat)"})
    k = v["kennzahlen"]
    pl.add_text(f"{ANLAGEN[anlage]['titel']}\n" + ", ".join(f"{n.split('.')[0]}={p[n]:.3g}" for n in p)[:200] +
                f"\nStahl vm_max {k['stahl.vm_max_MPa']['wert']:.0f} MPa, Masse {k['stahl.masse_t']['wert']:.0f} t",
                font_size=9)
    pl.view_isometric(); pl.camera.zoom(1.3)
    pl.screenshot(o / "vorhersage.png"); pl.close()
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("befehl", choices=["stufe0", "probe", "lauf", "trainiere", "vorhersage", "pause", "weiter"])
    ap.add_argument("--anlage", default="w7x", help="w7x | qa_1gw | beide")
    ap.add_argument("--nr", type=int, default=0)
    ap.add_argument("--stunden", type=float, default=4.0)
    ap.add_argument("--n", type=int, default=120, help="Proben je Anlage im DOE (nur beim ersten Start)")
    ap.add_argument("--p", nargs="*", default=[], help="name=wert, fehlende = Mitte des Bereichs")
    ap.add_argument("--B0", type=float); ap.add_argument("--P_netz", type=float)
    ap.add_argument("--pruefen", action="store_true")
    ap.add_argument("--name", default="vorhersage")
    a = ap.parse_args(argv)
    anlagen = ["w7x", "qa_1gw"] if a.anlage == "beide" else [a.anlage]
    if a.befehl in ("pause", "weiter"):                  # laufende Probe rechnet fertig, dann Ruhe / weiter
        for x in anlagen:
            st = steuerung(x) | {"pause": a.befehl == "pause"}
            (ordner(x) / "steuerung.json").write_text(json.dumps(st, indent=1))
            print(x, "pause" if st["pause"] else "weiter")
    elif a.befehl == "stufe0":
        print(json.dumps(stufe0_tabelle(anlagen[0]), indent=1))
    elif a.befehl == "probe":
        p = doe(anlagen[0], a.n)[a.nr]
        st = steuerung(anlagen[0])
        k = rechne_probe(anlagen[0], p, ordner(anlagen[0]) / "proben" / f"{a.nr:04d}.npz", 60 * st["timeout_min"], st["loeser"], vtu=True)
        print(json.dumps(k, indent=1))
    elif a.befehl == "lauf":
        lauf(anlagen, a.stunden, a.n)
    elif a.befehl == "trainiere":
        print(json.dumps(trainiere(anlagen[0]), indent=1))
    else:
        meta = json.loads((ordner(anlagen[0]) / "doe.json").read_text())
        p = {n: float(np.sqrt(lo * hi) if n in meta["log"] else 0.5 * (lo + hi)) for n, (lo, hi) in zip(meta["namen"], meta["bereiche"])}
        p |= {k: float(v) for k, v in (x.split("=") for x in a.p)}
        if a.B0:
            p["B0"] = a.B0
        if a.P_netz:
            p["P_netz"] = a.P_netz
        o = vorhersage_3d(anlagen[0], p, a.name, a.pruefen)
        print(o, (o / "ergebnis.json").read_text())


if __name__ == "__main__":
    main()


def bild_probe(anlage: str, nr: int, ram_min_gb: float = 8.0) -> Path:
    """3D-Bild einer gerechneten Probe: Stahl + Verbinder nach von Mises (nur bei genug freiem RAM)."""
    import pyvista as pv
    ram, _ = speicher()
    if ram < ram_min_gb:
        raise RuntimeError(f"nur {ram:.1f} GB RAM frei -> Bild spaeter")
    z = np.load(ordner(anlage) / "proben" / f"{nr:04d}.npz")
    p = json.loads(str(z["param"])); k = json.loads(str(z["kenn"]))
    _, _, _, netz, _ = modell(anlage, p)
    sel = np.where(netz.mat >= 3)[0]
    zellen = np.c_[np.full(len(sel), 8), netz.hexa[sel]].ravel()
    g = pv.UnstructuredGrid(zellen, np.full(len(sel), pv.CellType.HEXAHEDRON, np.uint8), netz.X)
    g.cell_data["vm"] = z["vm"][sel] / 1e6
    g = g.extract_surface()
    pl = pv.Plotter(off_screen=True, window_size=(1700, 1150))
    pl.add_mesh(g, scalars="vm", cmap="turbo", clim=[0, np.percentile(g.cell_data["vm"], 99)],
                scalar_bar_args={"title": "von Mises Stahl [MPa]"})
    lb = ANLAGEN[anlage]["last"]
    pl.add_text(f"{ANLAGEN[anlage]['titel']} — Probe {nr}\n"
                f"Waende innen {p['wand_innen_m']*100:.0f} / seite {p['wand_seite_m']*100:.0f} / aussen "
                f"{p['t_min_m']*100:.0f}-{(p['t_min_m']+p['t_zusatz_m'])*100:.0f} cm, Verguss {p['verguss_m']*1000:.0f} mm, "
                f"Lager r {p['r_lager_m']:.2f} m" + (f", P_netz {p['P_netz']:.0f} MW" if "P_netz" in p else f", B0 {lb.get('ref')} T") +
                f"\nStahl p99 {k['stahl']['vm_p99_MPa']:.0f} MPa, u_max {k['u_max_mm']:.0f} mm, Masse {k['stahl']['masse_t']:.0f} t",
                font_size=10)
    pl.view_isometric(); pl.camera.elevation = 25; pl.camera.zoom(1.25)
    pfad = ordner(anlage) / f"bild_probe_{nr:04d}.png"
    pl.screenshot(pfad); pl.close()
    return pfad
