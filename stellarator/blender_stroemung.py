"""blender_stroemung.py — Stroemung im Kuehlsegment als Animation (Teilchenschweife aus stroemung_animation.py).

  blender -b -P stellarator/blender_stroemung.py -- <segment-ordner> [--von 0] [--bis 359] [--proben 32] [--engine EEVEE]
                                                     [--durchsichtig | --gyroid]

Untere Haelfte des Segments (animation/stahl_unten.stl, Schnittflaeche animation/schnitt.stl orange), Blick schraeg
von oben auf den Schnitt. Mit --durchsichtig: ganzes Segment (animation/stahl_ganz.stl) im Roentgenblick, nur die
schraeg gesehenen Flaechen schimmern, die Stroemung im Inneren ist sichtbar; Kamera schraeg von aussen oben. Teilchenschweife leuchten, Farbe nach Geschwindigkeit (log, blau langsam -> gelb schnell).
Mit --gyroid: untere Haelfte undurchsichtig ohne Innenhaut (animation_gyroid/stahl_unten.stl, Schnitt orange), obere
Haelfte im Roentgenblick; die Kamera faehrt von der Gesamtansicht nah an die Gyroid-Filamente der Schnittflaeche heran.
Bilder nach animation/bilder/0000.png (--gyroid: animation_gyroid/bilder); Film mit ffmpeg.
"""
import json, math, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

arg = sys.argv[sys.argv.index("--") + 1:]
O = Path(arg[0]); A = O / "animation"
opt = lambda k, d: type(d)(arg[arg.index(k) + 1]) if k in arg else d
von, bis, proben, engine = opt("--von", 0), opt("--bis", 10**6), opt("--proben", 32), opt("--engine", "EEVEE")
aufl = opt("--breite", 1920); gyroid = "--gyroid" in arg; durchsichtig = "--durchsichtig" in arg or gyroid
AB = O / "animation_gyroid" if gyroid else A
alle = sorted(A.glob("bild_*.npz")); bilder = alle[von:bis + 1]
lage = json.loads((O / "auslegung.json").read_text())["lage"]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, farbe, metall=0.0, rau=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*farbe, 1); b.inputs["Metallic"].default_value = metall
    b.inputs["Roughness"].default_value = rau
    return m


def lade(datei, name, m):
    bpy.ops.wm.stl_import(filepath=str(datei), global_scale=0.001)
    o = bpy.context.selected_objects[0]; o.name = name
    o.data.materials.clear(); o.data.materials.append(m)
    return o


def roentgen(z_min=None):
    """Durchsichtiger Stahl: fast unsichtbar von vorn, an streifend gesehenen Flaechen hellgrau schimmernd.
    z_min: unterhalb ganz unsichtbar (dort liegt das undurchsichtige Teil)."""
    m = bpy.data.materials.new("Roentgen"); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
    lw = t.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    rp = t.nodes.new("ShaderNodeMapRange"); rp.inputs["To Min"].default_value = 0.04; rp.inputs["To Max"].default_value = 0.45
    tr = t.nodes.new("ShaderNodeBsdfTransparent"); em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.6, 0.68, 0.8, 1); em.inputs["Strength"].default_value = 0.6
    mx = t.nodes.new("ShaderNodeMixShader"); o = t.nodes.new("ShaderNodeOutputMaterial")
    t.links.new(lw.outputs["Facing"], rp.inputs["Value"]); fac = rp.outputs["Result"]
    if z_min is not None:
        ge = t.nodes.new("ShaderNodeNewGeometry"); sz = t.nodes.new("ShaderNodeSeparateXYZ")
        gt = t.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = z_min
        mu = t.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"
        t.links.new(ge.outputs["Position"], sz.inputs[0]); t.links.new(sz.outputs["Z"], gt.inputs[0])
        t.links.new(fac, mu.inputs[0]); t.links.new(gt.outputs[0], mu.inputs[1]); fac = mu.outputs[0]
    t.links.new(fac, mx.inputs["Fac"])
    t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(em.outputs[0], mx.inputs[2]); t.links.new(mx.outputs[0], o.inputs["Surface"])
    m.blend_method = "BLEND"; m.shadow_method = "NONE"; m.show_transparent_back = False; m.use_backface_culling = False
    return m


if gyroid:
    lade(A / "stahl_ganz.stl", "Stahl", roentgen(z_min=0.005))
    lade(AB / "stahl_unten.stl", "Stahl unten", mat("Stahl", (0.55, 0.58, 0.62), metall=0.8, rau=0.35))
    lade(AB / "schnitt.stl", "Schnitt", mat("Schnitt", (0.9, 0.45, 0.12), metall=0.2, rau=0.6))
elif durchsichtig:
    lade(A / "stahl_ganz.stl", "Stahl", roentgen())
else:
    lade(A / "stahl_unten.stl", "Stahl", mat("Stahl", (0.55, 0.58, 0.62), metall=0.8, rau=0.4))
    lade(A / "schnitt.stl", "Schnitt", mat("Schnitt", (0.9, 0.45, 0.12), metall=0.2, rau=0.6))

# Teilchen: Material leuchtet nach Attribut "farbe" (0..1) ueber eine Farbskala
mt = bpy.data.materials.new("Teilchen"); mt.use_nodes = True; nt = mt.node_tree
nt.nodes.clear()
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "farbe"
cr = nt.nodes.new("ShaderNodeValToRGB"); el = cr.color_ramp.elements
el[0].color = (0.05, 0.25, 1.0, 1); el[1].color = (1.0, 0.95, 0.2, 1)
for pos, c in ((0.35, (0.0, 0.85, 0.9, 1)), (0.65, (0.2, 1.0, 0.3, 1))):
    e = el.new(pos); e.color = c
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 0.9 if durchsichtig else 1.8
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(at.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])

me = bpy.data.meshes.new("Schweife"); ob = bpy.data.objects.new("Schweife", me); sc.collection.objects.link(ob)
me.materials.append(mt)
# Geometrieknoten: Kanten -> Kurven -> Roehrchen
gn = bpy.data.node_groups.new("Roehrchen", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
ein = gn.nodes.new("NodeGroupInput"); aus = gn.nodes.new("NodeGroupOutput")
m2c = gn.nodes.new("GeometryNodeMeshToCurve"); kr = gn.nodes.new("GeometryNodeCurvePrimitiveCircle")
kr.inputs["Resolution"].default_value = 5; kr.inputs["Radius"].default_value = 0.005 if durchsichtig else 0.008
c2m = gn.nodes.new("GeometryNodeCurveToMesh"); sm = gn.nodes.new("GeometryNodeSetMaterial")
sm.inputs["Material"].default_value = mt
gn.links.new(ein.outputs[0], m2c.inputs["Mesh"]); gn.links.new(m2c.outputs["Curve"], c2m.inputs["Curve"])
gn.links.new(kr.outputs["Curve"], c2m.inputs["Profile Curve"]); gn.links.new(c2m.outputs["Mesh"], sm.inputs["Geometry"])
gn.links.new(sm.outputs["Geometry"], aus.inputs[0])
mod = ob.modifiers.new("Roehrchen", "NODES"); mod.node_group = gn

# Licht, Welt, Kamera: schraeg von oben auf die Schnittflaeche, aussen links / Torusmitte rechts wie in der Draufsicht
c = np.array([np.array(lage["rohre"][k]["ende_m"]) for k in ("ein", "aus")]).mean(0); c[2] = -0.8
e_r = c * np.array([1, 1, 0]) / np.hypot(c[0], c[1]); e_phi = np.cross([0, 0, 1], e_r)
for name, ort, staerke in (("Sonne", e_phi * 0.5 + e_r * 0.3 + [0, 0, 1.2], 2.5), ("Fuell", -e_phi + [0, 0, 0.3], 0.6)):
    l = bpy.data.lights.new(name, "SUN"); l.energy = staerke
    lo = bpy.data.objects.new(name, l); sc.collection.objects.link(lo)
    lo.rotation_euler = (-Vector(ort)).to_track_quat("-Z", "Y").to_euler()
welt = bpy.data.worlds.new("Welt"); sc.world = welt; welt.use_nodes = True
welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.022, 0.03, 1)
cam = bpy.data.cameras.new("Kamera"); cam.lens = 32; cam.clip_start = 0.1; cam.clip_end = 200
co = bpy.data.objects.new("Kamera", cam); sc.collection.objects.link(co); sc.camera = co
pos = c - 4.5 * e_phi + [0, 0, 9.5] if not durchsichtig else c - 9.0 * e_phi + 3.5 * e_r + [0, 0, 7.5]
if durchsichtig:
    c[2] = 0.0
co.location = Vector(pos.tolist())
co.rotation_euler = (Vector(c.tolist()) - co.location).to_track_quat("-Z", "Y").to_euler()
# Kamera so drehen, dass aussen links liegt (Bildrechte Achse = -e_r)
oben = Vector((-e_phi).tolist()); co.rotation_euler = (Vector(c.tolist()) - co.location).to_track_quat("-Z", "Y").to_euler()
rechts = co.matrix_world.to_3x3() @ Vector((1, 0, 0))
if rechts.dot(Vector((-e_r).tolist())) < 0:
    co.rotation_euler.rotate_axis("Z", math.pi)


def kamera(t):
    """--gyroid: Fahrt von der Gesamtansicht (t=0) in den Ring hinein auf die freigelegte Gyroid-Schicht am Boden
    (Plasmaseite, R 9,3 m), weich ein- und auslaufend."""
    t = min(1.0, max(0.0, (t - 0.15) / 0.6)); s = t * t * (3 - 2 * t)   # 15 % stehen, 60 % fahren, 25 % verweilen
    ziel1 = opt("--ziel_r", 9.3) * e_r + [0, 0, -2.1]
    pos1 = 8.3 * e_r - 2.2 * e_phi + [0, 0, -0.5]
    p = (1 - s) * pos + s * pos1; z = (1 - s) * c + s * ziel1
    co.location = Vector(p.tolist())
    co.rotation_euler = (Vector(z.tolist()) - co.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    if (co.matrix_world.to_3x3() @ Vector((1, 0, 0))).dot(Vector((-e_r).tolist())) < 0:
        co.rotation_euler.rotate_axis("Z", math.pi)

if engine == "EEVEE":
    sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = proben
    sc.eevee.use_bloom = True; sc.eevee.bloom_intensity = 0.02; sc.eevee.use_gtao = True
else:
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = proben; sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = aufl, aufl * 9 // 16
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
(AB / "bilder").mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(AB / "stroemung.blend"))

lo_v, hi_v = math.log10(0.01), math.log10(3.0)
for i, d in enumerate(bilder):
    z = np.load(d); S, v = z["s"], z["v"]
    n, k = S.shape[:2]
    pkt = S.reshape(-1, 3)
    kanten = (np.arange(n)[:, None] * k + np.arange(k - 1)[None]).reshape(-1)
    kanten = np.stack([kanten, kanten + 1], 1)
    me.clear_geometry()
    me.vertices.add(len(pkt)); me.vertices.foreach_set("co", pkt.ravel())
    me.edges.add(len(kanten)); me.edges.foreach_set("vertices", kanten.ravel().astype(np.int32))
    f = np.clip((np.log10(np.maximum(v, 1e-4)) - lo_v) / (hi_v - lo_v), 0, 1)
    att = me.attributes.new("farbe", "FLOAT", "POINT"); att.data.foreach_set("value", np.repeat(f, k).astype(np.float32))
    me.update()
    nr = int(d.stem.split("_")[1])
    if gyroid:
        kamera(nr / max(1, len(alle) - 1)); bpy.context.view_layer.update()
    sc.render.filepath = str(AB / "bilder" / f"{nr:04d}.png")
    bpy.ops.render.render(write_still=True)
    print("BILD", nr, flush=True)
print("BLENDER_FERTIG")
