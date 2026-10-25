"""blender_gesamt.py — Gesamtszene der 1-GW-Anlage (PLY aus gesamtszene.py) in Blender rendern.

  blender -b -P stellarator/blender_gesamt.py -- <ordner> [--proben 48] [--ansicht detail|uebersicht|beide]

Materialien: Spulengehaeuse mit Vertexfarbe = von-Mises-Spannung (turbo), Feldlinien leuchtend mit Vertexfarbe = |B|,
Plasma halbtransparent leuchtend, Gefaessschale halbtransparent grau, Gyroid-Kern Bronze-Metall, Innenhaut Stahl.
Cycles auf der CPU (GPU nutzt Hermes). Ausgabe <ordner>/blender_<ansicht>.png und gesamt.blend.
"""
import math, sys
from pathlib import Path
import bpy
from mathutils import Vector

arg = sys.argv[sys.argv.index("--") + 1:]
O = Path(arg[0])
proben = int(arg[arg.index("--proben") + 1]) if "--proben" in arg else 48
ansicht = arg[arg.index("--ansicht") + 1] if "--ansicht" in arg else "beide"

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, farbe=(0.5, 0.5, 0.5), metall=0.0, rau=0.5, alpha=1.0, leuchten=0.0, vertexfarbe=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*farbe, 1)
    b.inputs["Metallic"].default_value = metall
    b.inputs["Roughness"].default_value = rau
    b.inputs["Alpha"].default_value = alpha
    if vertexfarbe:
        a = nt.nodes.new("ShaderNodeVertexColor"); a.layer_name = "Col"
        nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
        if leuchten:
            nt.links.new(a.outputs["Color"], b.inputs["Emission Color"])
    elif leuchten:
        b.inputs["Emission Color"].default_value = (*farbe, 1)
    if leuchten:
        b.inputs["Emission Strength"].default_value = leuchten
    if alpha < 1:
        m.blend_method = "BLEND"
    return m


MAT = {
    "plasma": mat("Plasma", (0.75, 0.3, 1.0), alpha=0.18, leuchten=1.5, rau=0.3),
    "plasma_teil": mat("Plasma_teil", (0.75, 0.3, 1.0), alpha=0.35, leuchten=2.0, rau=0.3),
    "schale_aussen": mat("Schale", (0.55, 0.58, 0.62), metall=0.6, rau=0.4, alpha=0.30),
    "schale_innen": mat("Schale_i", (0.55, 0.58, 0.62), metall=0.6, rau=0.4, alpha=0.15),
    "gyroid": mat("Gyroid", (0.85, 0.5, 0.18), metall=0.9, rau=0.3),
    "innenhaut": mat("Innenhaut", (0.7, 0.72, 0.75), metall=0.8, rau=0.35),
    "spulen": mat("Spannung", metall=0.3, rau=0.45, vertexfarbe=True),
    "feldlinien": mat("Feld", leuchten=3.0, vertexfarbe=True, rau=0.2),
    "stuetze": mat("Stuetzstruktur", (0.78, 0.8, 0.83), metall=1.0, rau=0.25),
}
for name, m in MAT.items():
    p = O / f"{name}.ply"
    if not p.exists():
        continue
    bpy.ops.wm.ply_import(filepath=str(p))
    o = bpy.context.selected_objects[0]; o.name = name
    o.data.materials.clear(); o.data.materials.append(m)
    if name in ("plasma", "plasma_teil", "gyroid", "schale_aussen", "schale_innen", "innenhaut", "feldlinien", "spulen"):
        for poly in o.data.polygons:
            poly.use_smooth = True
    if name == "spulen":
        o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(35)

sc = bpy.context.scene
for name, ort, staerke in (("Sonne", (0.6, -0.8, 1.2), 2.5), ("Fuell", (-1, 0.6, 0.3), 0.8)):
    l = bpy.data.lights.new(name, "SUN"); l.energy = staerke
    lo = bpy.data.objects.new(name, l); sc.collection.objects.link(lo)
    lo.rotation_euler = (-Vector(ort)).to_track_quat("-Z", "Y").to_euler()
welt = bpy.data.worlds.new("Welt"); sc.world = welt; welt.use_nodes = True
welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.025, 0.04, 1)
welt.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = proben; sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
cam = bpy.data.cameras.new("Kamera"); cam.lens = 35; cam.clip_start = 0.1; cam.clip_end = 500
co = bpy.data.objects.new("Kamera", cam); sc.collection.objects.link(co); sc.camera = co


def blick(pos, ziel):
    co.location = Vector(pos)
    co.rotation_euler = (Vector(ziel) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()


def polar(r, phi_grad, z):
    f = math.radians(phi_grad); return (r * math.cos(f), r * math.sin(f), z)


# Detailsektor 0..40 Grad: 0..20 geschlossen, 20..40 ohne Aussenhaut, Schnittflaeche bei 40 Grad
ansichten = {
    "uebersicht": (polar(40, -15, 32), (0, 0, -2), 35, None),
    "schnitt": (polar(14.5, 62, 4.0), polar(10.4, 40, -0.3), 35, None),      # Blick auf die Schnittflaeche bei 40 Grad
    "gyroid": (polar(19.5, 24, 4.0), polar(11.0, 31, -0.3), 40, None),       # auf die offene Gyroid-Flaeche
}
bpy.ops.wm.save_as_mainfile(filepath=str(O / "gesamt.blend"))
licht = bpy.data.lights.new("Kameralicht", "POINT"); lo = bpy.data.objects.new("Kameralicht", licht)
sc.collection.objects.link(lo)
for k, (pos, ziel, linse, _) in ansichten.items():
    if ansicht not in (k, "alle") and not (ansicht == "beide" and k in ("uebersicht", "schnitt")):
        continue
    blick(pos, ziel); cam.lens = linse
    for n, teil in (("plasma", k == "uebersicht"), ("plasma_teil", k != "uebersicht"), ("feldlinien", k != "schnitt")):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = not teil
    lo.location = Vector(pos) + Vector((0, 0, 2.0))
    licht.energy = 0 if k == "uebersicht" else 6000
    sc.render.filepath = str(O / f"blender_{k}.png")
    bpy.ops.render.render(write_still=True)
    print("BILD", sc.render.filepath, flush=True)
print("BLENDER_FERTIG")
