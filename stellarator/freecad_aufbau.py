"""freecad_aufbau.py — schrittweiser Aufbau mit Kollisionspruefung je neuer Spule (laeuft in freecadcmd).

  VSS_AUFBAU=<aufbau_eingabe.json> <FreeCAD.AppImage> freecadcmd stellarator/freecad_aufbau.py

Eingabe (von stellarator/aufbau.py): fcstd, reihenfolge (Spulennamen), verbinder [{name, a, b}], ausgabe.
Je Schritt wird die neue Spule (Gehaeuse + Wickelpaket) gegen alles bereits Gesetzte geprueft,
danach jeder Verbinder, dessen beide Spulen jetzt stehen (gegen alles ausser seinem Paar).
Ergebnis: aufbau.json (je Schritt: Spule, neue Verbinder, Kollisionen mit Volumen in Litern).
"""
import json, os
import FreeCAD as App

E = json.load(open(os.environ["VSS_AUFBAU"]))
doc = App.openDocument(E["fcstd"])
doc.recompute()
nach_label = {o.Label: o for o in doc.Objects}
geh = {n: nach_label[f"Gehaeuse_{n}"].Shape for n in E["reihenfolge"]}
wp = {n: nach_label[f"Wickelpaket_{n}"].Shape for n in E["reihenfolge"]}
verb = {v["name"]: (nach_label[v["name"]].Shape, v["a"], v["b"]) for v in E["verbinder"] if v["name"] in nach_label}


def schnitt_l(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume * 1e-6                  # mm^3 -> Liter


gesetzt, verb_gesetzt, schritte = [], [], []
for k, n in enumerate(E["reihenfolge"]):
    koll = []
    for m in gesetzt:                                  # neues Gehaeuse/WP gegen gesetzte Spulen
        for was, a, b in (("Gehaeuse-Gehaeuse", geh[n], geh[m]), ("Gehaeuse-Wickelpaket", geh[n], wp[m]),
                          ("Wickelpaket-Gehaeuse", wp[n], geh[m])):
            v = schnitt_l(a, b)
            if v > 1e-3:
                koll.append({"mit": m, "art": was, "liter": round(v, 3)})
    for vn in verb_gesetzt:                            # gesetzte Verbinder treffen die neue Spule?
        sh, a, b = verb[vn]
        for was, ziel in (("Verbinder-Gehaeuse", geh[n]), ("Verbinder-Wickelpaket", wp[n])):
            v = schnitt_l(sh, ziel)
            if v > 1e-3 and n not in (a, b):
                koll.append({"mit": vn, "art": was, "liter": round(v, 3)})
    gesetzt.append(n)
    neu = [vn for vn, (_, a, b) in verb.items() if vn not in verb_gesetzt and a in gesetzt and b in gesetzt]
    for vn in neu:                                     # neue Verbinder gegen alle gesetzten Teile ausser Paar
        sh, a, b = verb[vn]
        for m in gesetzt:
            for was, ziel in (("Verbinder-Wickelpaket", wp[m]),) + ((("Verbinder-Gehaeuse", geh[m]),) if m not in (a, b) else ()):
                v = schnitt_l(sh, ziel)
                if v > 1e-3:
                    koll.append({"mit": m, "art": was, "verbinder": vn, "liter": round(v, 3)})
    verb_gesetzt += neu
    schritte.append({"schritt": k + 1, "spule": n, "neue_verbinder": neu, "kollisionen": koll})
    print(f"AUFBAU {k + 1}/{len(E['reihenfolge'])} {n}: {len(neu)} Verbinder, {len(koll)} Kollisionen", flush=True)

json.dump({"schritte": schritte, "n_kollisionen": sum(len(s["kollisionen"]) for s in schritte)},
          open(os.path.join(E["ausgabe"], "aufbau.json"), "w"), indent=1)
print("AUFBAU_FERTIG")
