"""freecad_platten.py — Plattenpaket eines Plattenwaermetauschers als FreeCAD-Modell (Vergleich zu Gyroid/Diamond).

Laeuft IN FreeCAD (freecadcmd), nicht im Projekt-venv:
  PLATTEN='{"aus": "sim/tauscher/platten_glatt", "A": 0}' $FREECAD_APPIMAGE freecadcmd stellarator/freecad_platten.py

Platte i liegt bei y_i = i * (spalt + t). Ihre Mittelflaeche ist gewellt (Winkelwellung, "chevron"):
    y = y_i + A sin(2 pi (x cos(beta_i) - z sin(beta_i)) / lam),   beta_i = +beta / -beta abwechselnd,
so dass sich die Wellen benachbarter Platten kreuzen wie im Plattenwaermetauscher. A = 0 ergibt glatte Platten.
Die Dicke t wird senkrecht zur Plattenebene (in y) angetragen, nicht entlang der Flaechennormale (Naeherung).
Warme und kalte Spalte wechseln sich ab; mit spalt = 1 mm ist d_h = 2 mm wie beim Gyroid/Diamond-Modul.
Ausgabe: <aus>/platten.FCStd (Tabelle "Parameter"), platten.step, platten.stl, parameter.json.
"""
import json, math, os
import FreeCAD as App
import Part, Mesh

P = dict(aus="sim/tauscher/platten_glatt", breite=48.0, laenge=96.0, hoehe=48.0, spalt=1.0, t=0.5,
         A=0.0, lam=4.0, beta=60.0, n_x=8)
P.update(json.loads(os.environ.get("PLATTEN", "{}")))
os.makedirs(P["aus"], exist_ok=True)
B, L, H, s, t = P["breite"], P["laenge"], P["hoehe"], P["spalt"], P["t"]
p = s + t
n = int(H // p)                                  # Zahl der Platten im Paket


def flaeche(y0, beta, dy):
    """BSpline-Flaeche der um dy verschobenen gewellten Platte."""
    if P["A"] == 0:
        return None
    lam = P["lam"]; cb, sb = math.cos(math.radians(beta)), math.sin(math.radians(beta))
    wx, wz = lam / max(abs(cb), 1e-6), lam / max(abs(sb), 1e-6)       # Wellenlaenge in x und z
    nx = max(int(B / wx * P["n_x"]) + 1, 4); nz = max(int(L / wz * P["n_x"]) + 1, 4)
    pts = [[App.Vector(B * i / (nx - 1), y0 + dy + P["A"] * math.sin(2 * math.pi * (B * i / (nx - 1) * cb - L * k / (nz - 1) * sb) / lam),
                       L * k / (nz - 1)) for k in range(nz)] for i in range(nx)]
    f = Part.BSplineSurface(); f.interpolate(pts)
    return f.toShape()


def platte(i):
    y0 = t / 2 + i * p
    beta = P["beta"] if i % 2 == 0 else -P["beta"]
    if P["A"] == 0:
        return Part.makeBox(B, t, L, App.Vector(0, y0 - t / 2, 0))
    oben, unten = flaeche(y0, beta, t / 2), flaeche(y0, beta, -t / 2)
    seiten = [Part.makeRuledSurface(eo, eu) for eo, eu in zip(oben.Edges, unten.Edges)]
    return Part.Solid(Part.Shell([oben, unten] + seiten))


doc = App.newDocument("Platten")
tab = doc.addObject("Spreadsheet::Sheet", "Parameter")
for r, (k, v) in enumerate(sorted(P.items()), start=1):
    tab.set(f"A{r}", k); tab.set(f"B{r}", str(v))
teile = []
for i in range(n):
    sol = platte(i)
    o = doc.addObject("Part::Feature", f"Platte_{i:02d}"); o.Shape = sol; teile.append(o)
doc.recompute()
doc.saveAs(os.path.abspath(os.path.join(P["aus"], "platten.FCStd")))
Part.export(teile, os.path.join(P["aus"], "platten.step"))
mesh = Mesh.Mesh()
for o in teile:
    mesh.addFacets(Mesh.Mesh(o.Shape.tessellate(0.02)).Facets)
mesh.write(os.path.join(P["aus"], "platten.stl"))
vol = sum(o.Shape.Volume for o in teile)
erg = dict(P, platten=n, teilung=p, stahlanteil=vol / (B * L * n * p), gueltig=all(o.Shape.isValid() for o in teile))
json.dump(erg, open(os.path.join(P["aus"], "parameter.json"), "w"), indent=1)
print("PLATTEN_FERTIG", json.dumps(erg))
