"""freecad_reparatur.py — Kollisionen der Gehaeuse ueber die Parametertabelle beheben (laeuft in freecadcmd).

  VSS_REPARATUR=<reparatur_eingabe.json> <FreeCAD.AppImage> freecadcmd stellarator/freecad_reparatur.py

Prinzip (User-Idee "schrittweise aufbauen"): in Aufbau-Reihenfolge behaelt die frueher gesetzte Spule
ihre Waende, die spaeter gesetzte passt sich an. Je Kollision: Schwerpunkt des Ueberlappungsvolumens
-> in das Koordinatensystem der Basisspule (Klon-Placement invertiert) -> naechste Skizze j und Seite
(links/rechts = -b/+b, aussen = +n) -> Tabellenwerte l/r/a_<k>_<j-1..j+1> verkleinern (Faktor),
neu berechnen, erneut pruefen. Bis keine Kollision mehr oder max. Iterationen.
Ausgabe: <ausgabe>/korrektur.json (Alias -> mm), reparatur.json (Protokoll je Iteration).
"""
import json, os
import FreeCAD as App

V = App.Vector
E = json.load(open(os.environ["VSS_REPARATUR"]))
VSS = json.load(open(E["vss_eingabe"]))
doc = App.openDocument(E["fcstd"])
doc.recompute()
tab = doc.getObject("Parameter")
nach_label = {o.Label: o for o in doc.Objects}
folge = E["reihenfolge"]; rang = {n: i for i, n in enumerate(folge)}
basis = {b["name"]: k for k, b in enumerate(VSS["basis"])}
abb = {n: (k, None) for n, k in basis.items()}
for kl in VSS["klone"]:
    abb[kl["name"]] = (kl["basis"], kl["matrix"])
P = VSS["parameter"]
m_st = [len(b["stationen"]) for b in VSS["basis"]]


def wert(alias):
    return float(tab.get(alias).Value) if hasattr(tab.get(alias), "Value") else float(tab.get(alias))


def in_basis(c, name):
    """Punkt c (mm) in das Koordinatensystem der Basisspule von name (Klon: Rotation invertieren)."""
    k, M = abb[name]
    if M is None:
        return k, c
    return k, V(M[0][0] * c.x + M[1][0] * c.y + M[2][0] * c.z,      # M^T c (M orthogonal)
                M[0][1] * c.x + M[1][1] * c.y + M[2][1] * c.z,
                M[0][2] * c.x + M[1][2] * c.y + M[2][2] * c.z)


def ort(k, c):
    """Naechste Station j und Seite ('l', 'r', 'a', 'i') eines Punkts c im Basissystem k."""
    best = None
    for j, st in enumerate(VSS["basis"][k]["stationen"]):
        n, b = V(*st["n"]), V(*st["b"])
        mitte = V(*st["punkt"]) + n * (wert("wand_innen") + 0.5 * P["wp_breite"])
        d = c - mitte
        if best is None or d.Length < best[0]:
            best = (d.Length, j, d.dot(n), d.dot(b))
    _, j, dn, db = best
    if abs(db) / (0.5 * P["wp_hoehe"]) >= abs(dn) / (0.5 * P["wp_breite"]):
        return j, ("r" if db > 0 else "l")
    return j, ("a" if dn > 0 else "i")


protokoll = []
for it in range(E.get("max_iter", 6)):
    geh = {n: nach_label[f"Gehaeuse_{n}"].Shape for n in folge}
    wp = {n: nach_label[f"Wickelpaket_{n}"].Shape for n in folge}
    kolls, aenderung = [], {}
    for ia, a in enumerate(folge):
        for b in folge[ia + 1:]:
            for art, x, y, wer in (("G-G", geh[a], geh[b], b), ("G-WP", geh[a], wp[b], a), ("WP-G", wp[a], geh[b], b)):
                if not x.BoundBox.intersect(y.BoundBox):
                    continue
                s = x.common(y)
                if s.Volume * 1e-6 < E.get("tol_l", 1e-3):
                    continue
                # common() liefert oft ein Compound: volumengewichteter Schwerpunkt der Solids
                sol = s.Solids or [s]
                c = sum((x.CenterOfMass * x.Volume for x in sol), V()) * (1.0 / sum(x.Volume for x in sol))
                k, c = in_basis(c, wer)
                j, seite = ort(k, c)
                kolls.append({"a": a, "b": b, "art": art, "liter": round(s.Volume * 1e-6, 3),
                              "angepasst": wer, "station": j, "seite": seite})
                if seite == "i":
                    continue                     # Innenwand ist nicht je Station parametrisiert
                for dj in (-1, 0, 1):
                    jj = (j + dj) % m_st[k]
                    aenderung[f"{seite}_{k}_{jj}"] = True
    protokoll.append({"iteration": it, "n_kollisionen": len(kolls), "liter": round(sum(x["liter"] for x in kolls), 3),
                      "kollisionen": kolls})
    print(f"REPARATUR it {it}: {len(kolls)} Kollisionen, {len(aenderung)} Tabellenwerte", flush=True)
    if not aenderung:
        break
    for alias in aenderung:
        q, k, j = alias.split("_"); k, j = int(k), int(j)
        if q == "a":
            f = wert(f"f_{k}_{j}")
            soll = wert("t_min") + (wert("t_max") - wert("t_min")) * f
        else:
            soll = wert("wand_seite")
        neu = max(E["wand_min_mm"], E.get("faktor", 0.6) * min(soll, wert(alias)))
        tab.set(alias, f"{neu:.1f} mm")
    doc.recompute()

korr = {}
for k, b in enumerate(VSS["basis"]):
    for j in range(m_st[k]):
        for q in ("l", "r", "a"):
            al = f"{q}_{k}_{j}"
            if tab.getCellFromAlias(al):
                korr[al] = wert(al)
json.dump(korr, open(os.path.join(E["ausgabe"], "korrektur.json"), "w"), indent=0)
json.dump(protokoll, open(os.path.join(E["ausgabe"], "reparatur.json"), "w"), indent=1)
print("REPARATUR_FERTIG", protokoll[-1]["n_kollisionen"])
