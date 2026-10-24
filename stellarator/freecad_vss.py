"""freecad_vss.py — "Variable Section Sweep" (wie Creo VSS) als parametrisches FreeCAD-Modell.

Laeuft IN FreeCAD (freecadcmd), nicht im Projekt-venv:
  VSS_EINGABE=<vss_eingabe.json> ~/Applications/FreeCAD_1.1.4.AppImage freecadcmd stellarator/freecad_vss.py
Die Eingabe schreibt stellarator/gehaeuse.py (Masse in mm).

Aufbau je Basisspule (alles im Modellbaum editierbar):
  Innenkurve_<s>   Draft-BSpline, geschlossen, durch die Punkte der Gehaeuse-INNENSEITE (plasmaseitig).
                   Alles waechst von hier nach aussen -> keine Ueberschneidung auf der Plasmaseite.
  G_<s>_<j>        m Skizzen, angehaengt an die Innenkurve (NormalToEdge, MapPathParameter),
                   Rechteck: Tiefe (nach aussen) x Breite, Masse per Ausdruck aus Tabelle "Parameter".
  W_<s>_<j>        Skizzen des Wickelpakets (Abstand wand_innen von der Innenkurve).
  Loft_G/Loft_W    Part::Loft (geschlossen, Volumen) durch die Skizzen.
  Gehaeuse_<s>     Part::Cut Loft_G - Loft_W.
Die uebrigen Spulen sind Draft-Klone (Drehung um z, Stellaratorsymmetrie) -> folgen den Basisspulen.
Tabelle "Parameter": wand_innen, wand_seite, wp_breite, wp_hoehe, t_min, t_max und f_<k>_<j>
(Kraftfaktor 0..1 je Station): Tiefe = wand_innen + wp_breite + t_min + (t_max - t_min) * f.
Ausgabe: <ausgabe>/gehaeuse.FCStd, gehaeuse.step, gehaeuse_<i>.stl, wp_<i>.stl, pruefung.json.
"""
import json, math, os
import FreeCAD as App
import Part, Sketcher, Draft, Mesh, MeshPart, Import

V = App.Vector
E = json.load(open(os.environ["VSS_EINGABE"]))
AUS = E["ausgabe"]; os.makedirs(AUS, exist_ok=True)
doc = App.newDocument("Gehaeuse")

# ---------------------------------------------------------------- Parametertabelle
tab = doc.addObject("Spreadsheet::Sheet", "Parameter")
zeile = 1
def param(alias, wert, einheit="mm", text=""):
    global zeile
    tab.set(f"A{zeile}", text or alias); tab.set(f"B{zeile}", f"{wert} {einheit}".strip()); tab.setAlias(f"B{zeile}", alias)
    zeile += 1
for k, w in E["parameter"].items():
    param(k, w)
for k, b in enumerate(E["basis"]):
    for j, st in enumerate(b["stationen"]):
        param(f"f_{k}_{j}", round(st["f"], 3), "", f"Kraftfaktor {b['name']} Station {j}")
doc.recompute()


def rechteck(sk, x0, tiefe_ausdruck, breite_ausdruck, x0_ausdruck=None):
    """Rechteck x in [x0, x0+tiefe], y symmetrisch; voll bestimmt, Masse per Ausdruck."""
    p = [V(x0, -1, 0), V(x0 + 1, -1, 0), V(x0 + 1, 1, 0), V(x0, 1, 0)]
    for i in range(4):
        sk.addGeometry(Part.LineSegment(p[i], p[(i + 1) % 4]), False)
    c = [Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1) for i in range(4)]
    c += [Sketcher.Constraint("Horizontal", 0), Sketcher.Constraint("Horizontal", 2),
          Sketcher.Constraint("Vertical", 1),                           # linke Kante folgt aus Symmetric
          Sketcher.Constraint("Symmetric", 0, 1, 2, 2, -1)]            # symmetrisch zur x-Achse
    for x in c:
        sk.addConstraint(x)
    if x0_ausdruck is None:
        sk.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, -2))  # Innenseite auf der Kurve
    else:
        i = sk.addConstraint(Sketcher.Constraint("DistanceX", -1, 1, 0, 1, x0)); sk.renameConstraint(i, "Versatz")
        sk.setExpression("Constraints.Versatz", x0_ausdruck)
    i = sk.addConstraint(Sketcher.Constraint("Distance", 0, 1.0)); sk.renameConstraint(i, "Tiefe")
    i = sk.addConstraint(Sketcher.Constraint("Distance", 3, 2.0)); sk.renameConstraint(i, "Breite")
    sk.setExpression("Constraints.Tiefe", tiefe_ausdruck)
    sk.setExpression("Constraints.Breite", breite_ausdruck)


def skizze(name, kurve, u, n, t):
    """Skizze normal zur Kurve bei u (0..1). AttachmentOffset: Skizzen-z immer in Laufrichtung t
    (sonst kehrt sich die Eckenfolge um und der Loft verdreht sich), x-Achse auf n gedreht."""
    sk = doc.addObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(kurve, "Edge1")]; sk.MapMode = "NormalToEdge"; sk.MapPathParameter = u
    sk.recompute()
    R = sk.Placement.Rotation
    xs, ys, zs = (R.multVec(V(*a)) for a in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    flip = zs.dot(V(*t)) < 0
    if flip:
        ys = -ys
    nv = V(*n)
    w = math.degrees(math.atan2(nv.dot(ys), nv.dot(xs)))
    off = App.Rotation(V(0, 0, 1), w)
    if flip:
        off = App.Rotation(V(1, 0, 0), 180).multiply(off)
    sk.AttachmentOffset = App.Placement(V(), off)
    sk.Visibility = False
    return sk


basis_obj = []
for k, b in enumerate(E["basis"]):
    s = b["name"]
    kurve = Draft.make_bspline([V(*p) for p in b["kurve"]], closed=True)
    kurve.Label = f"Innenkurve_{s}"; kurve.Visibility = False
    doc.recompute()
    e = kurve.Shape.Edges[0]; u0, u1 = e.FirstParameter, e.LastParameter
    G, W = [], []
    for j, st in enumerate(b["stationen"]):
        u = (e.Curve.parameter(V(*st["punkt"])) - u0) / (u1 - u0)
        g = skizze(f"G_{s}_{j:02d}", kurve, u, st["n"], st["t"])
        rechteck(g, 0.0, f"Parameter.wand_innen + Parameter.wp_breite + Parameter.t_min + "
                         f"(Parameter.t_max - Parameter.t_min) * Parameter.f_{k}_{j}",
                 "Parameter.wp_hoehe + 2 * Parameter.wand_seite")
        w = skizze(f"W_{s}_{j:02d}", kurve, u, st["n"], st["t"])
        rechteck(w, E["parameter"]["wand_innen"], "Parameter.wp_breite", "Parameter.wp_hoehe",
                 x0_ausdruck="Parameter.wand_innen")
        G.append(g); W.append(w)
    lg = doc.addObject("Part::Loft", f"Loft_G_{s}"); lg.Sections = G; lg.Solid = True; lg.Closed = True; lg.Ruled = False
    lw = doc.addObject("Part::Loft", f"Wickelpaket_{s}"); lw.Sections = W; lw.Solid = True; lw.Closed = True; lw.Ruled = False
    cut = doc.addObject("Part::Cut", f"Gehaeuse_{s}"); cut.Base = lg; cut.Tool = lw
    doc.recompute()
    lw.Visibility = True                      # Cut blendet das Tool aus; Wickelpaket soll sichtbar sein
    basis_obj.append((cut, lw))

# ---------------------------------------------------------------- Klone (Symmetrie)
alle = [(b["name"], *basis_obj[k]) for k, b in enumerate(E["basis"])]
for kl in E["klone"]:
    cut, lw = basis_obj[kl["basis"]]
    M = kl["matrix"]
    pl = App.Placement(App.Matrix(M[0][0], M[0][1], M[0][2], 0, M[1][0], M[1][1], M[1][2], 0,
                                  M[2][0], M[2][1], M[2][2], 0, 0, 0, 0, 1))
    cg = Draft.make_clone(cut); cg.Label = f"Gehaeuse_{kl['name']}"; cg.Placement = pl
    cw = Draft.make_clone(lw); cw.Label = f"Wickelpaket_{kl['name']}"; cw.Placement = pl
    alle.append((kl["name"], cg, cw))
doc.recompute()

# ---------------------------------------------------------------- Pruefung
pr = {"spulen": {}, "ueberlappung": [], "fehler": []}
for k, b in enumerate(E["basis"]):
    cut, lw = basis_obj[k]
    g, w = cut.Shape, lw.Shape
    # Loft weicht zwischen den Stationen von der Spule ab: Spulenmitte muss im Wickelpaket liegen
    rand = Part.Compound(w.Faces)                       # Abstand zur Oberflaeche, nicht zum Volumen
    d = [rand.distToShape(Part.Vertex(V(*p)))[0] if w.isInside(V(*p), 1e-3, True) else -1.0 for p in b["mitte"]]
    innen = [x for x in d if x >= 0]
    pr["spulen"][b["name"]] = {"gehaeuse_gueltig": g.isValid(), "wp_gueltig": w.isValid(),
                               "gehaeuse_m3": g.Volume * 1e-9, "wp_m3": w.Volume * 1e-9,
                               "mitte_im_wp_anteil": len(innen) / len(d),
                               "mitte_rand_abstand_min_mm": min(innen) if innen else None,
                               "mitte_rand_abstand_mm": d,
                               "mitte_rand_abstand_soll_mm": 0.5 * min(E["parameter"]["wp_breite"], E["parameter"]["wp_hoehe"])}
form = [(n, cg.Shape, cw.Shape) for n, cg, cw in alle]
for i in range(len(form)):
    for j in range(i + 1, len(form)):
        a, bsh = form[i][1], form[j][1]
        if not a.BoundBox.intersect(bsh.BoundBox):
            continue
        v = a.common(bsh).Volume * 1e-9
        if v > 1e-6:
            pr["ueberlappung"].append({"a": form[i][0], "b": form[j][0], "volumen_m3": v})
pr["n_spulen"] = len(form)
for k, b in enumerate(E["basis"]):
    for j, st in enumerate(b["stationen"]):
        sk = doc.getObject(f"G_{b['name']}_{j:02d}"); R = sk.Placement.Rotation
        cx, cz = R.multVec(V(1, 0, 0)).dot(V(*st["n"])), R.multVec(V(0, 0, 1)).dot(V(*st["t"]))
        if cx < 0.99 or cz < 0.9:
            pr["fehler"].append(f"{sk.Name}: x.n={cx:.3f} z.t={cz:.3f}")
json.dump(pr, open(os.path.join(AUS, "pruefung.json"), "w"), indent=1)

# ---------------------------------------------------------------- Export
Import.export([o for _, cg, cw in alle for o in (cg, cw)], os.path.join(AUS, "gehaeuse.step"))
for i, (n, sg, sw) in enumerate(form):
    for art, sh in (("gehaeuse", sg), ("wp", sw)):
        MeshPart.meshFromShape(Shape=sh, LinearDeflection=20.0, AngularDeflection=0.3).write(
            os.path.join(AUS, f"{art}_{i:02d}.stl"))
doc.saveAs(os.path.join(AUS, "gehaeuse.FCStd"))
print("VSS_FERTIG", json.dumps({k: v for k, v in pr.items() if k != "spulen"}))
