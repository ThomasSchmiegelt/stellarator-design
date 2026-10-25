"""blender_thorus.py — geschnittenes Plasmagefaess (PLY aus thorus_schnitt.py) in Einbaulage rendern.

  blender -b -P stellarator/blender_thorus.py -- <ordner> [--proben 64] [--ansicht uebersicht|detail|alle]

Gefaess Stahl, Schnittflaechen (40 und 100 Grad) orange wie in einer Schnittzeichnung, Plasma leuchtend im Ausschnitt,
Hallenboden als Bezug. Cycles auf der CPU (GPU nutzt Hermes).
"""
import json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

arg = sys.argv[sys.argv.index("--") + 1:]
O = Path(arg[0])
proben = int(arg[arg.index("--proben") + 1]) if "--proben" in arg else 64
ansicht = arg[arg.index("--ansicht") + 1] if "--ansicht" in arg else "alle"
skala = json.loads((O / "skala.json").read_text())

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, farbe=(0.5, 0.5, 0.5), metall=0.0, rau=0.5, alpha=1.0, leuchten=0.0, vertexfarbe=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*farbe, 1)
    b.inputs["Metallic"].default_value = metall
    b.inputs["Roughness"].default_value = rau
    b.inputs["Alpha"].default_value = alpha
    if vertexfarbe:
        v = nt.nodes.new("ShaderNodeVertexColor"); v.layer_name = "Col"
        nt.links.new(v.outputs["Color"], b.inputs["Base Color"])
        if leuchten:
            nt.links.new(v.outputs["Color"], b.inputs["Emission Color"])
    elif leuchten:
        b.inputs["Emission Color"].default_value = (*farbe, 1)
    if leuchten:
        b.inputs["Emission Strength"].default_value = leuchten
    if alpha < 1:
        m.blend_method = "BLEND"
    return m


MAT = {
    "schale_aussen": mat("Schale", (0.62, 0.65, 0.69), metall=0.85, rau=0.35),
    "schale_innen": mat("Schale_i", (0.62, 0.65, 0.69), metall=0.85, rau=0.35),
    "gyroid": mat("Gyroid", (0.62, 0.65, 0.69), metall=0.85, rau=0.35),
    "schnitt": mat("Schnittflaeche", (0.9, 0.45, 0.12), metall=0.3, rau=0.5),
    "spulen": mat("Spannung", metall=0.3, rau=0.45, vertexfarbe=True),
    "feldlinien": mat("Feld", leuchten=3.0, vertexfarbe=True, rau=0.2),
    "plasma_teil": mat("Plasma", (0.75, 0.3, 1.0), alpha=0.3, leuchten=1.5, rau=0.3),
}
for name, m in MAT.items():
    if not (O / f"{name}.ply").exists():
        continue
    bpy.ops.wm.ply_import(filepath=str(O / f"{name}.ply"))
    o = bpy.context.selected_objects[0]; o.name = name
    o.data.materials.clear(); o.data.materials.append(m)
    if name not in ("gyroid", "schnitt"):
        for poly in o.data.polygons:
            poly.use_smooth = True
    if name == "spulen":
        o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(35)

sc = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, skala["z_boden"]))
boden = bpy.context.active_object; boden.name = "Boden"
boden.data.materials.append(mat("Boden", (0.35, 0.36, 0.38), rau=0.8))
for name, ort, staerke in (("Sonne", (0.5, -0.7, 1.3), 3.0), ("Fuell", (-1, 0.6, 0.4), 0.8)):
    l = bpy.data.lights.new(name, "SUN"); l.energy = staerke
    lo = bpy.data.objects.new(name, l); sc.collection.objects.link(lo)
    lo.rotation_euler = (-Vector(ort)).to_track_quat("-Z", "Y").to_euler()
welt = bpy.data.worlds.new("Welt"); sc.world = welt; welt.use_nodes = True
welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.05, 1)

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = proben; sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
cam = bpy.data.cameras.new("Kamera"); cam.clip_start = 0.1; cam.clip_end = 500
co = bpy.data.objects.new("Kamera", cam); sc.collection.objects.link(co); sc.camera = co
licht = bpy.data.lights.new("Kameralicht", "POINT"); lo = bpy.data.objects.new("Kameralicht", licht)
sc.collection.objects.link(lo)


def polar(r, phi_grad, z):
    f = math.radians(phi_grad); return (r * math.cos(f), r * math.sin(f), z)


ansichten = {   # (Kamera, Ziel, Linse, Kameralicht W)
    "uebersicht": (polar(34, 70, 17), polar(2, 70, -1.5), 35, 0),
    "weit": (polar(52, 70, 30), polar(0, 70, -3.0), 35, 0),                 # ganze Anlage samt Spulen
    "detail": (polar(19, 63, 6.0), polar(10.4, 40, -0.5), 40, 6000),     # auf die Schnittflaeche bei 40 Grad
}
ansichten = skala.get("ansichten", ansichten)
bpy.ops.wm.save_as_mainfile(filepath=str(O / "thorus.blend"))
for k, (pos, ziel, linse, w) in ansichten.items():
    if ansicht not in (k, "alle") or (ansicht == "alle" and k == "weit"):
        continue
    co.location = Vector(pos); cam.lens = linse
    co.rotation_euler = (Vector(ziel) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    lo.location = Vector(pos) + Vector((0, 0, 2.0)); licht.energy = w
    sc.render.filepath = str(O / f"blender_{k}.png")
    bpy.ops.render.render(write_still=True)
    print("BILD", sc.render.filepath, flush=True)
print("BLENDER_FERTIG")
