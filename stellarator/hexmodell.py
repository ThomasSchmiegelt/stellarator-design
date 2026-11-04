"""hexmodell.py — Spulengehaeuse als strukturiertes Hexaedernetz mit FESTER Topologie (Surrogat-Rechenmodell).

Je Spule ein Rohr aus Hexaedern entlang der Bahn (N Stationen, fest je Anlage). Querschnitt als
Tensorgitter in (n, b): Wand | Verguss | Wickelpaket | Verguss | Wand. Wandstaerken je Station aus
gehaeuse_netz.waende/entflechten (kollisionsfrei), der Verguss nimmt min(verguss, Wand/2) von der Wand
(wie torus3d). Verbinder: Hexaeder-Loft zwischen gegenueberliegenden Seitenflaechen benachbarter
Gehaeuse (konform, teilt die Knoten beider Gehaeuse). Lagerung: eingespannter Flecken der Aussenseite
am Bahnpunkt mit groesstem Radius (wie gehaeuse_netz).

Last: J x B im Wickelpaket aus Biot-Savart mit nf x nf Teilfilamenten je Spule (Knoten liegen nie auf
einem Filament), als Kraftdichte je Knoten in kraft.dat -> Fortran-UDF elmer_udf/lorentz.f90.
Elmer rechnet nur StressSolve (keine Luft, kein Magnetfeld-FEM) -> gleiche Knoten/Elemente fuer
alle Parameter einer Anlage, nur Koordinaten und Materialwerte aendern sich.

Bodies: 1 Wickelpaket, 2 Verguss, 3 Stahlgehaeuse, 4 Verbinder. Boundary 1 = Lagerflecken.
Auswertung in Python: Dehnung/Spannung im Elementmittelpunkt aus den Elmer-Verschiebungen
(je Element eigenes Material, keine Mittelung ueber Materialgrenzen).

    .venv/bin/python -m stellarator.hexmodell w7x [--stationen 64] [--name test]   (Einzellauf, s. surrogat.py)
"""
from __future__ import annotations
import json, subprocess, time
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

from . import spulen as sp, cad
from .lauf import PROJEKT

LAGER_ORT = "aussen"                                # Lagerflecken, siehe baue_netz
QUER = {"n_wand": 2, "n_verguss": 1, "n_wp": 4}      # Zellen je Schicht quer (je Richtung)
# Verbinderanordnung (Plan Punkt 1, F-149): "standard" wie doe1 (Abstand nur auf Spule k, Nachbarn koennen sich
# beruehren/ueberlappen), "getrennt" (Mindestabstand 2*halb+2 Stationen auf beiden Spulen -> einzelne Stege),
# "platte" (lueckenlos aneinander ueber den ganzen seitlichen Bereich, gemeinsame Knoten -> durchgehende Platte),
# "luecken" (wie "standard", danach Verbinder ergaenzen, bis keine Strecke ohne Verbinder/Lager laenger als
# LUECKE_MAX ist; SEITLICH_MIN wird dafuer stufenweise gelockert und je Verbinder ausgewiesen, B-034)
VERB_MODUS = "standard"
LUECKE_MAX = 4.0                                    # m, nur VERB_MODUS "luecken"
MAT_NAMEN = {1: "wickelpaket", 2: "verguss", 3: "stahl", 4: "verbinder"}
UDF_QUELLE = Path(__file__).resolve().parent / "elmer_udf" / "lorentz.f90"
UDF_ORDNER = PROJEKT / "sim" / "surrogat" / "udf"
# Ableitungen der 8 Formfunktionen (Hex, Elmer-Reihenfolge) nach (xi, eta, zeta)
ECKEN = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                  [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)


def dN(xi) -> np.ndarray:
    """(8, 3) Ableitungen dN_k/dxi_j an der Stelle xi."""
    f = 1 + ECKEN * np.asarray(xi, float)                   # (8, 3)
    return np.stack([ECKEN[:, j] * np.prod(np.delete(f, j, 1), 1) for j in range(3)], 1) / 8


@dataclass
class HexNetz:
    X: np.ndarray                    # (Nn, 3) Knoten
    hexa: np.ndarray                 # (E, 8) Knotenindizes (0-basiert, Elmer-Reihenfolge 808)
    mat: np.ndarray                  # (E,) Body 1..4
    spule: np.ndarray                # (E,) Spulenindex, -1 = Verbinder
    lager: np.ndarray                # (L, 5) Elternelement, 4 Knoten der Lagerflaechen
    wp_knoten: list = field(default_factory=list)   # je Spule (N, nq+1, nq+1) Knotenindizes Wickelpaket
    stationen_t: list = field(default_factory=list) # je Spule (N, 3) Tangenten
    info: dict = field(default_factory=dict)


def _teilung(grenzen: np.ndarray, zellen: list[int]) -> np.ndarray:
    """grenzen (N, 6) -> Knotenkoordinaten (N, sum(zellen)+1), jede Schicht gleichmaessig unterteilt."""
    teile = [grenzen[:, :1]]
    for s, m in enumerate(zellen):
        u = np.arange(1, m + 1) / m
        teile.append(grenzen[:, s:s + 1] + u * (grenzen[:, s + 1:s + 2] - grenzen[:, s:s + 1]))
    return np.hstack(teile)


PLAN_STRENG = True   # True: Verbinder aus dem Plan auch bei schlechter Jacobi-Determinante behalten (Surrogat); False: dann weglassen
SEITLICH_MIN = 0.8   # Verbinder nur, wo Verbindungslinie/Tangenten so gut quer liegen; 0.8 passt zu 0169, QI-Spulen sind verdrillter


def baue_netz(spulen, br: float, ho: float, W: list[dict], verguss: float, r_lager: float,
              verbinder_je_paar: int = 2, verb_halb: int = 1, verb_lagen: int = 2, q: dict = QUER,
              plan: list | None = None) -> HexNetz:
    """plan: feste Verbinderliste (aus info["verbinder"] eines frueheren Aufrufs) -> gleiche Topologie."""
    nw, nv, nq = q["n_wand"], q["n_verguss"], q["n_wp"]
    zellen = [nw, nv, nq, nv, nw]
    A = sum(zellen)                                       # Zellen je Querrichtung
    w0 = nw + nv                                          # erster Wickelpaket-Index
    # Material je Querschnittszelle (a, c): Bereich 0..4 je Richtung
    bereich = np.repeat(np.arange(5), zellen)
    ba, bc = np.meshgrid(bereich, bereich, indexing="ij")
    mat_q = np.where((ba == 2) & (bc == 2), 1, np.where((ba >= 1) & (ba <= 3) & (bc >= 1) & (bc <= 3), 2, 3))

    X, hexa, mat, spule, lager, wp_kn, tang, gitter = [], [], [], [], [], [], [], []
    lager_st = []                                         # je Spule: Stationen mit Lagerflaechen (nur "luecken")
    versatz = 0
    for k, (s, w) in enumerate(zip(spulen, W)):
        N = len(s.punkte)
        t, n, b = sp.rahmen(s)
        v = {q_: np.minimum(verguss, 0.5 * w[q_]) for q_ in ("innen", "aussen", "links", "rechts")}
        gn = np.c_[-br / 2 - w["innen"], -br / 2 - v["innen"], np.full(N, -br / 2), np.full(N, br / 2),
                   br / 2 + v["aussen"], br / 2 + w["aussen"]]
        gb = np.c_[-ho / 2 - w["links"], -ho / 2 - v["links"], np.full(N, -ho / 2), np.full(N, ho / 2),
                   ho / 2 + v["rechts"], ho / 2 + w["rechts"]]
        un, ub = _teilung(gn, zellen), _teilung(gb, zellen)              # (N, A+1)
        Xk = (s.punkte[:, None, None] + un[:, :, None, None] * n[:, None, None]
              + ub[:, None, :, None] * b[:, None, None])                 # (N, A+1, A+1, 3)
        idx = versatz + np.arange(N * (A + 1) ** 2).reshape(N, A + 1, A + 1)
        i, a, c = np.meshgrid(np.arange(N), np.arange(A), np.arange(A), indexing="ij")
        j = (i + 1) % N
        h = np.stack([idx[i, a, c], idx[i, a + 1, c], idx[i, a + 1, c + 1], idx[i, a, c + 1],
                      idx[j, a, c], idx[j, a + 1, c], idx[j, a + 1, c + 1], idx[j, a, c + 1]], -1)
        X.append(Xk.reshape(-1, 3)); hexa.append(h.reshape(-1, 8))
        mat.append(np.broadcast_to(mat_q, (N, A, A)).ravel()); spule.append(np.full(N * A * A, k))
        wp_kn.append(idx[:, w0:w0 + nq + 1, w0:w0 + nq + 1]); tang.append(t)
        gitter.append((idx, Xk, t, n, b))
        # Lagerflecken: Aussenseite (a = A, vom Spulenschwerpunkt weg) um den Bahnpunkt mit groesstem Radius
        # (LAGER_ORT "aussen", Standard), kleinstem Radius ("innen": Flaeche zeigt zur Torusachse, nimmt die
        # Zentrierkraft auf wie ein Stuetzzylinder) oder beiden ("beide").
        Rk = np.hypot(s.punkte[:, 0], s.punkte[:, 1])
        orte = {"aussen": [np.argmax(Rk)], "innen": [np.argmin(Rk)], "beide": [np.argmax(Rk), np.argmin(Rk)],
                "vier": [np.argmax(Rk), np.argmin(Rk), np.argmax(s.punkte[:, 2]), np.argmin(s.punkte[:, 2])]}[LAGER_ORT]
        ii, cc = np.meshgrid(np.arange(N), np.arange(A), indexing="ij")
        jj = (ii + 1) % N
        q4 = np.stack([idx[ii, A, cc], idx[jj, A, cc], idx[jj, A, cc + 1], idx[ii, A, cc + 1]], -1).reshape(-1, 4)
        eltern = (len(np.concatenate(spule)) - N * A * A) + (ii * A * A + (A - 1) * A + cc).ravel()
        mitte = Xk.reshape(-1, 3)[q4 - versatz].mean(1)
        lager_st.append(np.zeros(N, bool))
        for il in orte:
            p_l = s.punkte[il] + n[il] * (br / 2 + w["aussen"][il])
            d = np.linalg.norm(mitte - p_l, axis=1)
            wahl = np.where(d <= r_lager)[0]
            if len(wahl) < 2:
                wahl = np.argsort(d)[:2]
            lager.append(np.c_[eltern[wahl], q4[wahl]])
            lager_st[-1][wahl // A] = True
        versatz += N * (A + 1) ** 2

    # Verbinder zwischen toroidal benachbarten Gehaeusen
    n_sp = len(spulen)
    phi = np.array([np.arctan2(*s.punkte.mean(0)[[1, 0]]) for s in spulen])
    folge = np.argsort(phi)
    X_neu, verb, verb_info, auftraege = [], [], [], []
    n_kn = versatz
    for p in range(n_sp if (verbinder_je_paar and plan is None) else 0):
        k, m = int(folge[p]), int(folge[(p + 1) % n_sp])
        idk, Xk_, tk, nk, bk = gitter[k]
        idm, Xm_, tm, nm, bm = gitter[m]
        Pk, Pm = spulen[k].punkte, spulen[m].punkte
        D = np.linalg.norm(Pk[:, None] - Pm[None], axis=2)
        jn = D.argmin(1); dk = D.min(1)
        N = len(Pk)
        # nur echte Seitennachbarn: Verbindungslinie quer (b) zu beiden Spulen, Bahnen parallel
        dv = (Pm[jn] - Pk) / dk[:, None]
        seitlich = ((np.abs(np.sum(dv * bk, 1)) > SEITLICH_MIN) & (np.abs(np.sum(dv * bm[jn], 1)) > SEITLICH_MIN)
                    & (np.abs(np.sum(tk * tm[jn], 1)) > SEITLICH_MIN))
        orte = []
        abst = lambda a, b, n_: np.abs(((a - b + n_ // 2) % n_) - n_ // 2)
        if VERB_MODUS == "platte":                       # jede (2*halb)-te seitliche Station
            for i in np.where(seitlich)[0]:
                if i % (2 * verb_halb) == 0 and all(abst(jn[i], jn[i0], len(Pm)) >= 2 * verb_halb for i0 in orte):
                    orte.append(int(i))
        else:
            d_min = N // (verbinder_je_paar + 1)
            if VERB_MODUS == "getrennt":
                d_min = max(d_min, 2 * verb_halb + 2)
            for _ in range(verbinder_je_paar):
                frei = seitlich.copy()
                for i0 in orte:
                    frei &= abst(np.arange(N), i0, N) >= d_min
                    if VERB_MODUS == "getrennt":         # auch auf der Gegenspule Abstand halten
                        frei &= abst(jn, jn[i0], len(Pm)) >= d_min
                if frei.any():
                    orte.append(int(np.where(frei, dk, np.inf).argmin()))
        for i0 in orte:
            j0 = int(jn[i0])
            d = (Pm[j0] - Pk[i0]) / np.linalg.norm(Pm[j0] - Pk[i0])
            auftraege.append({"k": k, "m": m, "i0": i0, "j0": j0, "fk": _seite(d, nk[i0], bk[i0]),
                              "fm": _seite(-d, nm[j0], bm[j0]), "abstand_achse_m": float(dk[i0])})
    luecken_vorher = None
    if VERB_MODUS == "luecken" and plan is None:
        auftraege, luecken_vorher = _luecken_fuellen(spulen, gitter, folge, auftraege, lager_st, A, verb_halb,
                                                     verb_lagen, LUECKE_MAX)
    for v in (plan if plan is not None else auftraege):
        k, m, i0, j0, fk, fm = (v[x] for x in ("k", "m", "i0", "j0", "fk", "fm"))
        si, F0, X0, F1, X1, rs, rev = _verbinder_flaechen(v, gitter, spulen, A, verb_halb)
        lagen = [F0]
        for l in range(1, verb_lagen):
            lam = l / verb_lagen
            Xl = ((1 - lam) * X0 + lam * X1).reshape(-1, 3)
            lagen.append(n_kn + np.arange(len(Xl)).reshape(F0.shape)); X_neu.append(Xl); n_kn += len(Xl)
        lagen.append(F1)
        el = []
        for l in range(verb_lagen):
            u, o = lagen[l], lagen[l + 1]
            for s_ in range(len(si) - 1):
                for a_ in range(A):
                    el.append([u[s_, a_], u[s_ + 1, a_], u[s_ + 1, a_ + 1], u[s_, a_ + 1],
                               o[s_, a_], o[s_ + 1, a_], o[s_ + 1, a_ + 1], o[s_, a_ + 1]])
        verb.append(np.array(el)); verb_info.append({"k": k, "m": m, "i0": int(i0), "j0": int(j0), "fk": fk,
                                                     "fm": fm, "rs": int(rs), "rev": bool(rev)})
        for x in ("ergaenzt", "seitlich_stufe", "ueberlappt"):                       # nur "luecken"
            if x in v:
                verb_info[-1][x] = v[x]
    Xall = np.vstack(X + X_neu)
    if VERB_MODUS == "platte" and X_neu:                 # deckungsgleiche Zwischenknoten benachbarter Verbinder vereinen
        _, erst, zu = np.unique(np.round(Xall, 6), axis=0, return_index=True, return_inverse=True)
        ziel = erst[zu.ravel()]
        ziel[:versatz] = np.arange(versatz)               # Spulenknoten bleiben (eigene Knoten je Spule)
        verb = [ziel[e] for e in verb]
    hx = [np.vstack(hexa)]; mt = [np.concatenate(mat)]; spl = [np.concatenate(spule)]
    ok_verb = []
    for e, inf in zip(verb, verb_info):
        jm = _jacobi_min(Xall, e)
        if np.all(jm < 0):                                             # Umlaufsinn umdrehen
            e = e[:, [4, 5, 6, 7, 0, 1, 2, 3]]; jm = _jacobi_min(Xall, e)
        inf["jacobi_min"] = float(jm.min()); inf["laenge_m"] = float(np.linalg.norm(
            Xall[e[:, 4:]].mean(1) - Xall[e[:, :4]].mean(1), axis=1).mean())
        inf["ok"] = bool(np.all(jm > 0))
        if inf["ok"] or (plan is not None and PLAN_STRENG):            # mit Plan: feste Topologie
            hx.append(e); mt.append(np.full(len(e), 4)); spl.append(np.full(len(e), -1))
        ok_verb.append(inf)
    netz = HexNetz(Xall, np.vstack(hx), np.concatenate(mt), np.concatenate(spl), np.vstack(lager), wp_kn, tang,
                   info={"querschnitt": q, "zellen_quer": A, "stationen": [len(s.punkte) for s in spulen],
                         "verbinder": ok_verb})
    # unbenutzte Verbinder-Zwischenknoten (verworfene Verbinder) bleiben im Netz -> Elmer stoert das nicht,
    # aber freie Knoten ohne Steifigkeit: hier entfernen
    benutzt = np.zeros(len(Xall), bool); benutzt[netz.hexa.ravel()] = True
    if not benutzt.all():
        neu = np.cumsum(benutzt) - 1
        netz.X = Xall[benutzt]; netz.hexa = neu[netz.hexa]; netz.lager[:, 1:] = neu[netz.lager[:, 1:]]
        netz.wp_knoten = [neu[x] for x in netz.wp_knoten]
    jm = _jacobi_min(netz.X, netz.hexa)
    netz.info |= {"knoten": len(netz.X), "elemente": len(netz.hexa), "jacobi_min_rel": float(jm.min()),
                  "elemente_negativ": int((jm <= 0).sum()), "lagerflaechen": len(netz.lager),
                  "verbinder_ok": int(sum(v["ok"] for v in ok_verb)), "verbinder_gesamt": len(ok_verb)}
    if luecken_vorher is not None:
        st = _stuetzung(spulen, [v for v in ok_verb if v["ok"]], lager_st, verb_halb)
        je = [max(l for *_, l in _luecken(_bogen(s.punkte), g)) for s, g in zip(spulen, st)]
        erg = [v for v in ok_verb if v.get("ergaenzt")]
        stufen = sorted({v["seitlich_stufe"] for v in erg}, reverse=True)
        netz.info["luecken"] = {
            "grenze_m": LUECKE_MAX, "luecke_max_m": float(max(je)), "luecke_max_vorher_m": luecken_vorher,
            "spulen_ueber_grenze": int(sum(l > LUECKE_MAX for l in je)), "ergaenzt": len(erg),
            "ergaenzt_ok": int(sum(v["ok"] for v in erg)),
            "ergaenzt_gelockert": int(sum(v["seitlich_stufe"] < SEITLICH_MIN for v in erg)),
            "ergaenzt_ueberlappend": int(sum(v["ueberlappt"] for v in erg)),
            "ergaenzt_je_stufe": {f"{s:.1f}": int(sum(v["seitlich_stufe"] == s for v in erg)) for s in stufen},
            "ergaenzt_laenge_max_m": float(max((v["laenge_m"] for v in erg), default=0.0)),
            "seitlich_min": SEITLICH_MIN, "je_spule_m": [float(l) for l in je]}
    return netz


def _verbinder_flaechen(v, gitter, spulen, A: int, verb_halb: int):
    """Gegenueberliegende Flaechen eines Verbinders: Stationen si, Knoten/Koordinaten F0/X0 (Spule k), F1/X1 (Spule m)."""
    k, m, i0, j0, fk, fm = (v[x] for x in ("k", "m", "i0", "j0", "fk", "fm"))
    idk, Xk_, tk, nk, bk = gitter[k]
    idm, Xm_, tm, nm, bm = gitter[m]
    N, Nm = len(spulen[k].punkte), len(spulen[m].punkte)
    si = (i0 + np.arange(-verb_halb, verb_halb + 1)) % N
    aa = np.arange(A + 1)
    F0, X0 = _flaeche(idk[si], fk, A), _flaeche(Xk_[si], fk, A)                  # (S+1, A+1)
    # Zuordnung der Gegenflaeche (Stationen / Querindex vor- oder rueckwaerts): aus dem Plan oder
    # die Variante mit den geradesten Verbindungslinien
    best = None
    for rs in ((v["rs"],) if "rs" in v else (1, -1)):
        sj = (j0 + rs * np.arange(-verb_halb, verb_halb + 1)) % Nm
        for rev in ((v["rev"],) if "rev" in v else (False, True)):
            am = aa[::-1] if rev else aa
            X1 = _flaeche(Xm_[sj], fm, A)[:, am]
            L_ = np.linalg.norm(X1 - X0, axis=-1).sum()
            if best is None or L_ < best[0]:
                best = (L_, _flaeche(idm[sj], fm, A)[:, am], X1, rs, rev)
    _, F1, X1, rs, rev = best
    return si, F0, X0, F1, X1, rs, rev


def _verbinder_ok(v, gitter, spulen, A: int, verb_halb: int, verb_lagen: int) -> bool:
    """Wie die Pruefung in baue_netz (alle Jacobi-Determinanten > 0, ggf. Umlaufsinn umgedreht), fuer einen Verbinder allein."""
    si, F0, X0, F1, X1, rs, rev = _verbinder_flaechen(v, gitter, spulen, A, verb_halb)
    S, Aq = F0.shape
    Xl = [(1 - l / verb_lagen) * X0 + l / verb_lagen * X1 for l in range(verb_lagen)] + [X1]
    Xloc = np.concatenate([x.reshape(-1, 3) for x in Xl])
    idx = np.arange(len(Xloc)).reshape(verb_lagen + 1, S, Aq)
    s_, a_ = np.meshgrid(np.arange(S - 1), np.arange(A), indexing="ij")
    el = [np.stack([u[s_, a_], u[s_ + 1, a_], u[s_ + 1, a_ + 1], u[s_, a_ + 1],
                    o[s_, a_], o[s_ + 1, a_], o[s_ + 1, a_ + 1], o[s_, a_ + 1]], -1).reshape(-1, 8)
          for u, o in zip(idx[:-1], idx[1:])]
    e = np.vstack(el)
    jm = _jacobi_min(Xloc, e)
    if np.all(jm < 0):
        jm = _jacobi_min(Xloc, e[:, [4, 5, 6, 7, 0, 1, 2, 3]])
    return bool(np.all(jm > 0))


def _flaechenpaare(d, nk, bk, nm, bm) -> list[tuple[int, int]]:
    """Seitenflaechenpaare (fk, fm), deren Normalen zur jeweils anderen Spule zeigen; zuerst das von _seite."""
    ak = np.array([-(d @ nk), d @ nk, -(d @ bk), d @ bk]); am = np.array([d @ nm, -(d @ nm), d @ bm, -(d @ bm)])
    erst = (int(np.argmax(ak)), int(np.argmax(am)))
    rest = sorted(((-(ak[i] + am[j]), i, j) for i in range(4) for j in range(4) if ak[i] > 0 and am[j] > 0))
    return [erst] + [(i, j) for _, i, j in rest if (i, j) != erst]


def _bogen(P) -> tuple[np.ndarray, float]:
    """Bogenlaenge der geschlossenen Bahn an jeder Station (ab Station 0) und Gesamtlaenge."""
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    return np.r_[0.0, np.cumsum(seg)[:-1]], float(seg.sum())


def _luecken(bogen, gestuetzt) -> list[tuple[int, int, float]]:
    """Strecken zwischen aufeinanderfolgenden gestuetzten Stationen (a, b, Bogenlaenge a -> b), ringfoermig."""
    s, ges = bogen
    g = np.where(gestuetzt)[0]
    if len(g) == 0:
        return [(-1, -1, ges)]
    if len(g) == 1:
        return [(int(g[0]), int(g[0]), ges)]
    b = np.roll(g, -1)
    return [(int(x), int(y), float((s[y] - s[x]) % ges)) for x, y in zip(g, b)]


def _stuetzung(spulen, verbinder, lager_st, verb_halb: int) -> list[np.ndarray]:
    """Je Spule: Stationen mit Verbinderknoten (i0/j0 +- verb_halb) oder Lagerflaechen."""
    st = [g.copy() for g in lager_st]
    h = np.arange(-verb_halb, verb_halb + 1)
    for v in verbinder:
        st[v["k"]][(v["i0"] + h) % len(st[v["k"]])] = True
        st[v["m"]][(v["j0"] + h) % len(st[v["m"]])] = True
    return st


def _luecken_fuellen(spulen, gitter, folge, auftraege, lager_st, A: int, verb_halb: int, verb_lagen: int,
                     luecke_max: float, stufen_schritt: float = 0.1, kandidaten_max: int = 40,
                     versatz_j: tuple = (0, 1, -1, 2, -2)):
    """Greedy (B-034): groesste Strecke ohne Verbinder/Lager zuerst. Darin der Kandidat (Station der Spule, naechster
    Punkt einer der beiden toroidalen Nachbarspulen), der die Strecke am gleichmaessigsten teilt (bei Gleichstand der
    kuerzere), zuerst mit SEITLICH_MIN, dann stufenweise gelockert bis 0. Je Stufe zuerst Kandidaten, deren Flaeche
    auf der Gegenspule frei ist, dann solche, die dort einen Verbinder ueberlappen (wie im Modus "standard" erlaubt).
    Je Kandidat probiert: Gegenstation naechster Punkt, dann +-1, +-2 Stationen; Seitenflaechen zuerst die von _seite,
    dann die anderen zugewandten Paare (hoechstens 3); Zuordnung der Gegenflaeche (rs, rev) alle vier. Der erste
    Verbinder ohne umgestuelpte Elemente wird genommen, mit festem rs/rev (gleiche Topologie im Netzaufbau). Rueckgabe: (auftraege + ergaenzte, groesste Luecke vorher in m)."""
    n_sp = len(spulen)
    pos = {int(c): p for p, c in enumerate(folge)}
    nachbarn = [sorted({int(folge[(pos[c] + 1) % n_sp]), int(folge[(pos[c] - 1) % n_sp])} - {c}) for c in range(n_sp)]
    ok = [v for v in auftraege if _verbinder_ok(v, gitter, spulen, A, verb_halb, verb_lagen)]
    h = np.arange(-verb_halb, verb_halb + 1)
    verb_st = _stuetzung(spulen, ok, [np.zeros_like(g) for g in lager_st], verb_halb)
    bogen = [_bogen(s.punkte) for s in spulen]
    stufen = [SEITLICH_MIN] + [x for x in np.round(np.arange(SEITLICH_MIN - stufen_schritt, -1e-9, -stufen_schritt), 6)]
    paar = {}
    for c in range(n_sp):                              # naechster Punkt + Querguete je Station, je Nachbar
        _, _, tc, nc, bc = gitter[c]
        for nb in nachbarn[c]:
            _, _, tn, nn, bn = gitter[nb]
            Pc, Pn = spulen[c].punkte, spulen[nb].punkte
            D = np.linalg.norm(Pc[:, None] - Pn[None], axis=2)
            jn = D.argmin(1); dk = D.min(1)
            dv = (Pn[jn] - Pc) / dk[:, None]
            guete = np.minimum.reduce([np.abs(np.sum(dv * bc, 1)), np.abs(np.sum(dv * bn[jn], 1)),
                                       np.abs(np.sum(tc * tn[jn], 1))])
            paar[c, nb] = (jn, dk, dv, guete)
    vorher = None; neu = []; aufgegeben = set()
    while True:
        st = [v | g for v, g in zip(verb_st, lager_st)]
        alle = [(l, c, a, b) for c in range(n_sp) for a, b, l in _luecken(bogen[c], st[c]) if (c, a, b) not in aufgegeben]
        if vorher is None:
            vorher = float(max((l for l, *_ in alle), default=0.0))
        alle = [x for x in alle if x[0] > luecke_max]
        if not alle:
            break
        l, c, a, b = max(alle)
        N = len(spulen[c].punkte); s, ges = bogen[c]
        n_in = (b - a - 1) % N if a != b else N - 1
        innen = [(a + 1 + t) % N for t in range(verb_halb, n_in - verb_halb)] if a >= 0 else []
        bog = lambda x, y: float((s[y] - s[x]) % ges) if x != y else ges
        gefunden = False
        for stufe in stufen:
            kand = []
            for nb in nachbarn[c]:
                jn, dk, dv, guete = paar[c, nb]
                for i in innen:
                    if not guete[i] > stufe:
                        continue
                    ueber = bool(verb_st[nb][(jn[i] + h) % len(verb_st[nb])].any())
                    teil = max(bog(a, (i - verb_halb) % N), bog((i + verb_halb) % N, b))
                    kand.append((ueber, teil, float(dk[i]), nb, i))
            for ueber, teil, d_, nb, i in sorted(kand)[:kandidaten_max]:
                jn, dk, dv, guete = paar[c, nb]
                Nn = len(spulen[nb].punkte)
                for dj in versatz_j:                     # Gegenstation: naechster Punkt, dann Nachbarstationen
                    j0 = int((jn[i] + dj) % Nn)
                    dd = spulen[nb].punkte[j0] - spulen[c].punkte[i]; d_ = float(np.linalg.norm(dd)); dd = dd / d_
                    for fk, fm in _flaechenpaare(dd, gitter[c][3][i], gitter[c][4][i], gitter[nb][3][j0], gitter[nb][4][j0])[:3]:
                        for rs, rev in ((1, False), (1, True), (-1, False), (-1, True)):
                            v = {"k": c, "m": nb, "i0": int(i), "j0": j0, "fk": fk, "fm": fm, "rs": rs, "rev": rev,
                                 "abstand_achse_m": d_, "ergaenzt": True, "seitlich_stufe": float(stufe),
                                 "ueberlappt": bool(verb_st[nb][(j0 + h) % Nn].any())}
                            if _verbinder_ok(v, gitter, spulen, A, verb_halb, verb_lagen):
                                gefunden = True
                                break
                        if gefunden:
                            break
                    if gefunden:
                        break
                if gefunden:
                    neu.append(v)
                    verb_st[c][(i + h) % N] = True; verb_st[nb][(j0 + h) % Nn] = True
                    break
            if gefunden:
                break
        if not gefunden:
            aufgegeben.add((c, a, b))
    return auftraege + neu, vorher


def _seite(d, n, b) -> int:
    """Seitenflaeche (0: -n innen, 1: +n aussen, 2: -b links, 3: +b rechts), deren Normale am besten nach d zeigt."""
    return int(np.argmax([-(d @ n), d @ n, -(d @ b), d @ b]))


def _flaeche(G, seite: int, A: int):
    """Knotengitter (S, A+1, A+1, ...) -> Seitenflaeche (S, A+1, ...)."""
    return (G[:, 0], G[:, A], G[:, :, 0], G[:, :, A])[seite]


def _jacobi_min(X, hexa) -> np.ndarray:
    """Kleinste Jacobi-Determinante an den 8 Ecken, bezogen auf die Mittelpunkt-Determinante."""
    Xe = X[hexa]
    d0 = np.linalg.det(np.einsum("eki,kj->eij", Xe, dN([0, 0, 0])))
    dm = np.min([np.linalg.det(np.einsum("eki,kj->eij", Xe, dN(x))) for x in ECKEN], axis=0)
    return dm / np.abs(d0)                                  # < 0: Element umgestuelpt


def lorentzdichte(netz: HexNetz, spulen, br: float, ho: float, nf: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Kraftdichte J x B [N/m^3] an allen Knoten (0 ausserhalb der Wickelpakete) und Nettokraft je Spule [N]."""
    nf = nf or QUER["n_wp"]
    u = (np.arange(nf) + 0.5) / nf - 0.5
    A_, B_, I_ = [], [], []
    for s in spulen:
        t, n, b = sp.rahmen(s)
        for ua in u:
            for uc in u:
                P = s.punkte + ua * br * n + uc * ho * b
                A_.append(P); B_.append(np.roll(P, -1, 0)); I_.append(np.full(len(P), s.strom / nf ** 2))
    seg = (np.vstack(A_), np.vstack(B_), np.concatenate(I_))
    idx = np.concatenate([w.ravel() for w in netz.wp_knoten])
    B = sp.biot_savart(netz.X[idx], seg)
    T = np.concatenate([np.broadcast_to(t[:, None, None], w.shape + (3,)).reshape(-1, 3)
                        for t, w in zip(netz.stationen_t, netz.wp_knoten)])
    J = np.concatenate([np.full(w.size, s.strom / (br * ho)) for s, w in zip(spulen, netz.wp_knoten)])
    f = np.zeros_like(netz.X); f[idx] = J[:, None] * np.cross(T, B)
    # Nettokraft je Spule: Elementmittel x Volumen ueber die Wickelpaket-Elemente
    wp = netz.mat == 1
    V = elementvolumen(netz.X, netz.hexa[wp])
    Fe = f[netz.hexa[wp]].mean(1) * V[:, None]
    F = np.array([Fe[netz.spule[wp] == k].sum(0) for k in range(len(spulen))])
    return f, F


def elementvolumen(X, hexa) -> np.ndarray:
    """Volumen je Hexaeder (2x2x2 Gauss)."""
    g = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]) / np.sqrt(3)
    Xe = X[hexa]
    return sum(np.linalg.det(np.einsum("eki,kj->eij", Xe, dN(p))) for p in g)


# ------------------------------------------------------------------ Elmer
def udf() -> Path:
    """lorentz.so (einmal je Quelle uebersetzen)."""
    UDF_ORDNER.mkdir(parents=True, exist_ok=True)
    so = UDF_ORDNER / "lorentz.so"
    if not so.exists() or so.stat().st_mtime < UDF_QUELLE.stat().st_mtime:
        subprocess.run(["elmerf90", "-o", str(so), str(UDF_QUELLE)], cwd=UDF_ORDNER, check=True, capture_output=True)
    return so


def schreibe_fall(ordner: Path, netz: HexNetz, f: np.ndarray, material: dict, loeser: str = "iterativ") -> None:
    """Elmer-Netz (direkt, ohne ElmerGrid), kraft.dat und case.sif.
    material: {1..4: {"E_Pa", "nu"}}."""
    m = ordner / "netz"; m.mkdir(parents=True, exist_ok=True)
    Nn, E, L = len(netz.X), len(netz.hexa), len(netz.lager)
    (m / "mesh.header").write_text(f"{Nn} {E} {L}\n2\n808 {E}\n404 {L}\n")
    ids = np.arange(1, Nn + 1)
    np.savetxt(m / "mesh.nodes", np.c_[ids, -np.ones(Nn), netz.X], fmt="%d %d %.9e %.9e %.9e")
    np.savetxt(m / "mesh.elements", np.c_[np.arange(1, E + 1), netz.mat, np.full(E, 808), netz.hexa + 1], fmt="%d")
    np.savetxt(m / "mesh.boundary", np.c_[np.arange(1, L + 1), np.ones(L, int), netz.lager[:, 0] + 1,
                                          np.zeros(L, int), np.full(L, 404), netz.lager[:, 1:] + 1], fmt="%d")
    with open(ordner / "kraft.dat", "w") as fh:
        fh.write(f"{Nn}\n")
        np.savetxt(fh, np.c_[netz.X, f], fmt="%.9e")
    so = udf()
    ls = {"iterativ": """  Linear System Solver = "Iterative"
  Linear System Iterative Method = "CG"
  Linear System Preconditioning = ILU0
  Linear System Max Iterations = 20000
  Linear System Convergence Tolerance = 1e-8
  Linear System Abort Not Converged = False
  Linear System Residual Output = 200
""", "mumps": """  Linear System Solver = "Direct"
  Linear System Direct Method = "MUMPS"
"""}[loeser]
    S = ["""Header
  Mesh DB "." "netz"
  Results Directory "erg"
End
Simulation
  Coordinate System = "Cartesian 3D"
  Simulation Type = "Steady State"
  Steady State Max Iterations = 1
  Output Intervals = 1
  Max Output Level = 4
End
Constants
End
"""]
    warm = any(m.get("eps_th") for m in material.values())   # Eigendehnung: Temperaturfeld 1, Referenz 0, alpha = eps_th
    if warm:
        S.append("Initial Condition 1\n  Temperature = 1.0\nEnd\n")
    for k, name in MAT_NAMEN.items():
        S.append(f'Body {k}\n  Name = "{name}"\n  Equation = 1\n  Material = {k}\n'
                 + ("  Body Force = 1\n" if k == 1 else "") + ("  Initial Condition = 1\n" if warm else "") + "End\n")
        th = (f'  Heat Expansion Coefficient = {material[k].get("eps_th", 0.0):.9e}\n  Reference Temperature = 0.0\n' if warm else "")
        S.append(f'Material {k}\n  Name = "{name}"\n  Youngs Modulus = {material[k]["E_Pa"]:.6e}\n'
                 f'  Poisson Ratio = {material[k]["nu"]}\n{th}End\n')
    S.append("Body Force 1\n" + "".join(
        f'  Stress Bodyforce {i} = Variable Time\n    Real Procedure "{so}" "kraft_{c}"\n' for i, c in ((1, "x"), (2, "y"), (3, "z")))
        + "End\n")
    S.append(f"""Equation 1
  Active Solvers(1) = 1
End
Solver 1
  Equation = "Stress"
  Procedure = "StressSolve" "StressSolver"
  Variable = -dofs 3 "Displacement"
{'  Exported Variable 1 = -dofs 1 "Temperature"' + chr(10) if warm else ""}  Calculate Stresses = Logical False
  Displace Mesh = Logical False
{ls}End
Solver 2
  Exec Solver = After All
  Procedure = "ResultOutputSolve" "ResultOutputSolver"
  Output File Name = "hex"
  Vtu Format = Logical True
  Binary Output = Logical True
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Displacement 1 = Real 0.0
  Displacement 2 = Real 0.0
  Displacement 3 = Real 0.0
End
""")
    (ordner / "case.sif").write_text("".join(S))


def rechne(ordner: Path, timeout_s: float | None = None) -> float:
    t0 = time.time()
    with open(ordner / "solve.log", "w") as fh:
        subprocess.run(["ElmerSolver", "case.sif"], cwd=ordner, stdout=fh, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout_s)
    return time.time() - t0


def verschiebung(ordner: Path, netz: HexNetz) -> np.ndarray:
    import pyvista as pv
    erg = sorted((ordner / "erg").glob("hex*.vtu"))[-1]
    g = pv.read(erg)
    if len(g.points) != len(netz.X) or np.abs(g.points - netz.X).max() > 1e-5:
        raise RuntimeError("Knotenreihenfolge der Elmer-Ausgabe passt nicht zum Netz")
    return np.asarray(g.point_data["displacement"], float)


def spannungen(netz: HexNetz, U: np.ndarray, material: dict) -> np.ndarray:
    """Von Mises [Pa] im Elementmittelpunkt."""
    d = dN([0, 0, 0])
    J = np.einsum("eki,kj->eij", netz.X[netz.hexa], d)
    G = np.einsum("eki,kj->eij", U[netz.hexa], d) @ np.linalg.inv(J)
    eps = 0.5 * (G + G.transpose(0, 2, 1))
    eps = eps - np.array([material[k].get("eps_th", 0.0) for k in range(1, 5)])[netz.mat - 1][:, None, None] * np.eye(3)
    E = np.array([material[k]["E_Pa"] for k in range(1, 5)])[netz.mat - 1]
    nu = np.array([material[k]["nu"] for k in range(1, 5)])[netz.mat - 1]
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    tr = np.trace(eps, axis1=1, axis2=2)
    sig = 2 * mu[:, None, None] * eps + (lam * tr)[:, None, None] * np.eye(3)
    s = sig - np.trace(sig, axis1=1, axis2=2)[:, None, None] / 3 * np.eye(3)
    return np.sqrt(1.5 * np.einsum("eij,eij->e", s, s))


def kennzahlen(netz: HexNetz, U: np.ndarray, vm: np.ndarray, rho_stahl: float = 7900.0) -> dict:
    V = elementvolumen(netz.X, netz.hexa)
    u = np.linalg.norm(U, axis=1)
    k = {"u_max_mm": float(u.max() * 1e3)}
    for m, name in MAT_NAMEN.items():
        sel = netz.mat == m
        if not sel.any():
            continue
        v = vm[sel] / 1e6
        o = np.argsort(v); cv = np.cumsum(V[sel][o]) / V[sel].sum()
        k[name] = {"vm_max_MPa": float(v.max()), "vm_p99_MPa": float(v[o][np.searchsorted(cv, 0.99)]),
                   "vm_mittel_MPa": float((v * V[sel]).sum() / V[sel].sum()), "volumen_m3": float(V[sel].sum())}
    k["stahl"]["masse_t"] = k["stahl"]["volumen_m3"] * rho_stahl / 1e3
    if "verbinder" in k:
        k["verbinder"]["masse_t"] = k["verbinder"]["volumen_m3"] * rho_stahl / 1e3
    return k


def als_vtu(netz: HexNetz, pfad: Path, felder: dict | None = None, punkte: dict | None = None) -> None:
    import pyvista as pv
    zellen = np.c_[np.full(len(netz.hexa), 8), netz.hexa].ravel()
    g = pv.UnstructuredGrid(zellen, np.full(len(netz.hexa), pv.CellType.HEXAHEDRON, np.uint8), netz.X)
    g.cell_data["material"] = netz.mat; g.cell_data["spule"] = netz.spule
    for k, v in (felder or {}).items():
        g.cell_data[k] = v
    for k, v in (punkte or {}).items():
        g.point_data[k] = v
    g.save(pfad)
