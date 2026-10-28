"""blender_wandstueck.py — Wandstueck mit doppeltem Filament (picogk/WandStueck) in Blender rendern.

  blender -b -P stellarator/blender_wandstueck.py -- <ordner> [--proben 64] [--breite 1920] [--ohne_wasser] [--zoom 1] [--ziel_z 0.5] [--bild wandstueck.png]

Stahl metallisch, Kuehlkanaele (wasser.stl) blau; Blick schraeg von der Plasmaseite (z < 0) auf das Fenster in der
Innenhaut und die Schnittkanten. Bild nach <ordner>/wandstueck.png.
"""
import math, sys
from pathlib import Path
import bpy
from mathutils import Vector

arg = sys.argv[sys.argv.index("--") + 1:]
O = Path(arg[0]); opt = lambda k, d: type(d)(arg[arg.index(k) + 1]) if k in arg else d
proben, breite = opt("--proben", 64), opt("--breite", 1920)
zoom, ziel_z, bildname = opt("--zoom", 1.0), opt("--ziel_z", 0.5), opt("--bild", "wandstueck.png")
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


stahl = lade(O / "stahl.stl", mat("Stahl", (0.62, 0.64, 0.68), 0.85, 0.32))
if "--ohne_wasser" not in arg:
    lade(O / "wasser.stl", mat("Wasser", (0.08, 0.42, 0.95), 0.0, 0.15, emission=0.6))

# Blickpunkt = Mitte des Stuecks, Abstand mit der Tiefe skaliert (450 x 450 x 900 mm: Mitte 0.225/0.225/0.45, Faktor 1.3)
ecken = [stahl.matrix_world @ Vector(e) for e in stahl.bound_box]
c = sum(ecken, Vector()) / 8
z0, z1 = min(e.z for e in ecken), max(e.z for e in ecken); tiefe = z1 - z0
c.z = z0 + ziel_z * tiefe                                       # Blickpunkt in der Tiefe (0 = Haut)
for name, richt, e in (("Sonne", (0.6, -0.8, -0.7), 3.5), ("Fuell", (-0.8, 0.3, -0.2), 1.0), ("Gegen", (0.0, 0.6, 1.0), 1.5)):
    l = bpy.data.lights.new(name, "SUN"); l.energy = e
    lo = bpy.data.objects.new(name, l); sc.collection.objects.link(lo)
    lo.rotation_euler = (-Vector(richt)).to_track_quat("-Z", "Y").to_euler()
welt = bpy.data.worlds.new("Welt"); sc.world = welt; welt.use_nodes = True
welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.13, 0.14, 0.17, 1)
welt.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
cam = bpy.data.cameras.new("Kamera"); cam.lens = 50
co = bpy.data.objects.new("Kamera", cam); sc.collection.objects.link(co); sc.camera = co
co.location = c + 1.3 * tiefe / 0.9 / zoom * Vector((1.55, -1.25, -1.35))
co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()

# Bildpositionen der Schichten fuer die Beschriftung (wandstueck_beschriften.py), Ursprung oben links
import json
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
anker = {"Plasmaseite / Innenhaut 5 mm": (0.12, 0.12, 0.0), "Kühlkanäle 6×6 mm (Wasser 60→150 °C)": (0.36, 0.36, 0.008),
         "Rückwand 5 mm": (0.45, 0.12, 0.0135), "Gyroid trocken (Steifigkeit)": (0.45, 0.15, 0.45),
         "Außenhaut 40 mm": (0.45, 0.15, 0.88)}
pos = {k: (lambda p: (p.x, 1 - p.y))(world_to_camera_view(sc, co, Vector(v))) for k, v in anker.items()}
if "--ohne_wasser" not in arg:                                    # Anker nur fuer das Wandstueck mit Kanaelen
    (O / "anker.json").write_text(json.dumps(pos, ensure_ascii=False, indent=1))

sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = proben
sc.eevee.use_gtao = True; sc.eevee.use_ssr = True
sc.render.resolution_x, sc.render.resolution_y = breite, breite * 9 // 16
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.render.filepath = str(O / bildname)
bpy.ops.render.render(write_still=True)
print("BLENDER_FERTIG")
