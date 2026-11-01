"""blender_tauscher.py — Kernmodul des Gyroid-Vorwaermers (picogk/GyroidTauscher) in Blender rendern.

  blender -b -P stellarator/blender_tauscher.py -- <ordner> [--proben 64] [--breite 1920] [--nur stahl|fluide] [--bild tauscher.png]

Stahl metallisch, Divertorwasser (warm.stl) rot, Kondensat (kalt.stl) blau. Ein Viertel ab 35 % der Laenge ist
weggeschnitten (*_schnitt.stl), damit man die zwei verschlungenen Kanalnetze und die Abstufung der Zellen sieht.
"""
import sys
from pathlib import Path
import bpy
from mathutils import Vector

arg = sys.argv[sys.argv.index("--") + 1:]
O = Path(arg[0]); opt = lambda k, d: type(d)(arg[arg.index(k) + 1]) if k in arg else d
proben, breite, nur, bildname = opt("--proben", 64), opt("--breite", 1920), opt("--nur", "alle"), opt("--bild", "tauscher.png")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, farbe, metall, rau, emission=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*farbe, 1); b.inputs["Metallic"].default_value = metall
    b.inputs["Roughness"].default_value = rau
    if emission:
        b.inputs["Emission Color"].default_value = (*farbe, 1); b.inputs["Emission Strength"].default_value = emission
    return m


def lade(datei, m):
    bpy.ops.wm.stl_import(filepath=str(datei), global_scale=0.001)
    o = bpy.context.selected_objects[0]; o.data.materials.clear(); o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


objs = []
if nur in ("alle", "stahl"):
    objs.append(lade(O / "stahl_schnitt.stl", mat("Stahl", (0.62, 0.64, 0.68), 0.85, 0.32)))
if nur in ("alle", "fluide"):
    objs.append(lade(O / "warm_schnitt.stl", mat("Divertorwasser", (0.92, 0.18, 0.10), 0.0, 0.3, emission=0.35)))
    objs.append(lade(O / "kalt_schnitt.stl", mat("Kondensat", (0.08, 0.42, 0.95), 0.0, 0.3, emission=0.35)))

ecken = [o.matrix_world @ Vector(e) for o in objs for e in o.bound_box]
lo_, hi_ = Vector([min(e[i] for e in ecken) for i in range(3)]), Vector([max(e[i] for e in ecken) for i in range(3)])
c = (lo_ + hi_) / 2; groesse = (hi_ - lo_).length
for name, richt, e in (("Sonne", (0.5, 0.8, -0.6), 3.5), ("Fuell", (-0.8, -0.3, -0.2), 1.0), ("Gegen", (0.0, -0.6, 1.0), 1.5)):
    l = bpy.data.lights.new(name, "SUN"); l.energy = e
    lob = bpy.data.objects.new(name, l); sc.collection.objects.link(lob)
    lob.rotation_euler = (-Vector(richt)).to_track_quat("-Z", "Y").to_euler()
welt = bpy.data.worlds.new("Welt"); sc.world = welt; welt.use_nodes = True
welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.13, 0.14, 0.17, 1)
welt.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
cam = bpy.data.cameras.new("Kamera"); cam.lens = 50
co = bpy.data.objects.new("Kamera", cam); sc.collection.objects.link(co); sc.camera = co
# Blick auf die aufgeschnittene Ecke (x > B/2, y < B/2), schraeg von oben, Laenge z liegt quer im Bild
co.location = c + 2.3 * groesse * Vector((0.62, -0.55, 0.40)).normalized()
co.rotation_euler = (c - co.location).to_track_quat("-Z", "X").to_euler()
sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = proben
sc.eevee.use_gtao = True
sc.render.resolution_x, sc.render.resolution_y = breite, breite * 9 // 16
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.render.filepath = str(O / bildname)
bpy.ops.render.render(write_still=True)
print("BLENDER_FERTIG")
