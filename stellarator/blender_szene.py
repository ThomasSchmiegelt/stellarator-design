"""blender_szene.py — glTF-Modelle (torus3d / leiter3d) in Blender: Materialien, Licht, Kamera, .blend + Bild.

  blender -b -P stellarator/blender_szene.py -- <modell.glb> <ausgabe.blend> [bild.png] [--proben 64]
        [--blick x y z]   Richtung Mitte -> Kamera in Modellkoordinaten (pyvista, z oben)
        [--zoom 1.0]      >1 naeher heran (flache Modelle wie der Torus fuellen die Kugel schlecht)

Laeuft in Blender (bpy). Farben kommen aus dem glTF (pyvista export_gltf); hier werden sie in
Principled-BSDF-Materialien mit passender Oberflaeche uebersetzt (Metall: Stahl/Alu/Kupfer, sonst matt,
Helium glasartig). Der glTF-Import liefert die Farben als sRGB-Werte -> hier linearisiert; das Modell
wird in die pyvista-Lage (z oben) zurueckgedreht. Render: Cycles auf der CPU (GPU nutzt Hermes),
ohne Denoiser (Blender-Paket ohne OpenImageDenoise).
"""
import math, sys
import bpy
from mathutils import Matrix, Vector

arg = sys.argv[sys.argv.index("--") + 1:]
glb, blend = arg[0], arg[1]
png = arg[2] if len(arg) > 2 and not arg[2].startswith("--") else None
proben = int(arg[arg.index("--proben") + 1]) if "--proben" in arg else 64
blick = Vector(map(float, arg[arg.index("--blick") + 1: arg.index("--blick") + 4])) if "--blick" in arg else Vector((0.55, -0.95, 0.6))
zoom = float(arg[arg.index("--zoom") + 1]) if "--zoom" in arg else 1.0

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objekte = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in bpy.context.scene.objects:                        # Import liefert (x, y) = pyvista (y, -x) -> zurueckdrehen
    if o.parent is None:
        o.matrix_world = Matrix.Rotation(math.pi / 2, 4, "Z") @ o.matrix_world
bpy.context.view_layer.update()


def farbe(mat):
    """Grundfarbe aus dem importierten Material (Principled BSDF) oder grau."""
    if mat and mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                c = n.inputs["Base Color"].default_value
                return tuple(linear(x) for x in c[:3]) + (c[3],)
    return (0.3, 0.3, 0.3, 1.0)


def linear(x):
    """sRGB -> linear (pyvista schreibt die Hex-Farben unveraendert ins glTF)."""
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def art(rgb):
    """Materialart aus der Farbe raten (Farben siehe torus3d.SCHICHTEN / leiter3d.FARBEN)."""
    r, g, b = rgb[:3]
    if abs(r - g) < 0.08 and abs(g - b) < 0.1 and r > 0.15:
        return "metall"                                    # Stahl / Aluminium (grau)
    if r > 0.3 and g < 0.4 * r and b < 0.2 * r:
        return "kupfer"
    if b > 0.6 and g > 0.35 and r < 0.25:
        return "glas"                                      # Helium
    return "matt"


for o in objekte:
    for i, slot in enumerate(o.material_slots):
        rgb = farbe(slot.material)
        m = bpy.data.materials.new(f"{o.name}_{i}"); m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = rgb
        k = art(rgb)
        bsdf.inputs["Metallic"].default_value = {"metall": 0.7, "kupfer": 1.0}.get(k, 0.0)   # Stahl/Alu matt-metallisch
        bsdf.inputs["Roughness"].default_value = {"metall": 0.55, "kupfer": 0.3, "glas": 0.05}.get(k, 0.6)
        if k == "glas":
            bsdf.inputs["Transmission Weight" if "Transmission Weight" in bsdf.inputs else "Transmission"].default_value = 0.9
            bsdf.inputs["Alpha"].default_value = 0.35; m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
        slot.material = m
    for p in o.data.polygons:                              # glatt, Kanten > 40 Grad bleiben scharf
        p.use_smooth = True
    o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(40)

# Kamera auf die Bounding Box aller Objekte
lo = Vector((1e9, 1e9, 1e9)); hi = -lo
for o in objekte:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
mitte = (lo + hi) / 2; groesse = (hi - lo).length
cam = bpy.data.cameras.new("Kamera"); cam.lens = 45
cam.clip_start = groesse * 1e-3; cam.clip_end = groesse * 100
co = bpy.data.objects.new("Kamera", cam); bpy.context.scene.collection.objects.link(co)
abstand = 0.5 * groesse / math.tan(cam.angle_y / 2) * 1.25 / zoom     # Kugel um die Bounding Box passt ins Bild (Hoehe)
co.location = mitte + blick.normalized() * abstand
co.rotation_euler = (mitte - co.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = co
for name, ort, staerke in (("Sonne", (1, -1, 2), 1.0), ("Fuell", (-1, 1, -1), 0.4)):
    l = bpy.data.lights.new(name, "SUN"); l.energy = staerke
    lo_ = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(lo_)
    lo_.rotation_euler = (-Vector(ort)).to_track_quat("-Z", "Y").to_euler()
welt = bpy.data.worlds.new("Welt"); bpy.context.scene.world = welt; welt.use_nodes = True
welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.85, 0.87, 0.9, 1)
welt.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = proben; sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
bpy.ops.wm.save_as_mainfile(filepath=blend)
if png:
    sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
print("BLENDER_FERTIG", blend, png)
