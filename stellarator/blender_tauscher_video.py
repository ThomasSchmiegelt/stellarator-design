"""blender_tauscher_video.py — Video der Teilchenbahnen in einer Tauscherseite (Daten aus tauscher_video.py).

  blender -b -P stellarator/blender_tauscher_video.py -- <fall-ordner> [--von 0] [--bis 9999] [--proben 16] [--breite 1920]

Tauscherwand im Roentgenblick (nur streifend gesehene Flaechen schimmern), vordere Kachelreihe zusaetzlich als
undurchsichtiger Schnitt weggelassen. Schweife leuchten nach Temperatur: rot = heiss (Kernstroemung), blau = Wandtemperatur
(theta 0), Farbskala bis 1,6 x Mischtemperatur. Stroemung von links nach rechts (z quer im Bild). Bilder nach <fall>/video/bilder/0000.png.
"""
import json, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

arg = sys.argv[sys.argv.index("--") + 1:]
O = Path(arg[0]); V = O / "video"
opt = lambda k, d: type(d)(arg[arg.index(k) + 1]) if k in arg else d
von, bis, proben, breite = opt("--von", 0), opt("--bis", 10 ** 6), opt("--proben", 16), opt("--breite", 1920)
info = json.loads((V / "info.json").read_text())
bilder = sorted(V.glob("bild_*.npz"))[von:bis + 1]
(V / "bilder").mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# Roentgen-Material fuer die Wand
m = bpy.data.materials.new("Roentgen"); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
lw = t.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
rp = t.nodes.new("ShaderNodeMapRange"); rp.inputs["To Min"].default_value = 0.03; rp.inputs["To Max"].default_value = 0.5
tr = t.nodes.new("ShaderNodeBsdfTransparent"); em = t.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (0.65, 0.7, 0.8, 1); em.inputs["Strength"].default_value = 0.5
mx = t.nodes.new("ShaderNodeMixShader"); out = t.nodes.new("ShaderNodeOutputMaterial")
t.links.new(lw.outputs["Facing"], rp.inputs["Value"]); t.links.new(rp.outputs["Result"], mx.inputs["Fac"])
t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(em.outputs[0], mx.inputs[2]); t.links.new(mx.outputs[0], out.inputs["Surface"])
m.blend_method = "BLEND"; m.use_backface_culling = False
bpy.ops.wm.stl_import(filepath=str(V / "wand_schnitt.stl"), global_scale=0.001)
wand = bpy.context.selected_objects[0]; wand.data.materials.append(m)

# Schweife als Roehrchen, Farbe nach theta
mt = bpy.data.materials.new("Teilchen"); mt.use_nodes = True; nt = mt.node_tree; nt.nodes.clear()
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "farbe"
cr = nt.nodes.new("ShaderNodeValToRGB"); el = cr.color_ramp.elements
el[0].color = (0.05, 0.3, 1.0, 1); el[1].color = (1.0, 0.15, 0.05, 1)
e = el.new(0.4); e.color = (0.85, 0.85, 0.9, 1)
emt = nt.nodes.new("ShaderNodeEmission"); emt.inputs["Strength"].default_value = 2.0
o2 = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(at.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], emt.inputs["Color"])
nt.links.new(emt.outputs["Emission"], o2.inputs["Surface"])
me = bpy.data.meshes.new("Schweife"); ob = bpy.data.objects.new("Schweife", me); sc.collection.objects.link(ob)
me.materials.append(mt)
gn = bpy.data.node_groups.new("Roehrchen", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
ein = gn.nodes.new("NodeGroupInput"); aus = gn.nodes.new("NodeGroupOutput")
m2c = gn.nodes.new("GeometryNodeMeshToCurve"); kr = gn.nodes.new("GeometryNodeCurvePrimitiveCircle")
kr.inputs["Resolution"].default_value = 5; kr.inputs["Radius"].default_value = 0.000018
c2m = gn.nodes.new("GeometryNodeCurveToMesh"); sm = gn.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = mt
gn.links.new(ein.outputs[0], m2c.inputs["Mesh"]); gn.links.new(m2c.outputs["Curve"], c2m.inputs["Curve"])
gn.links.new(kr.outputs["Curve"], c2m.inputs["Profile Curve"]); gn.links.new(c2m.outputs["Mesh"], sm.inputs["Geometry"])
gn.links.new(sm.outputs["Geometry"], aus.inputs[0])
ob.modifiers.new("Roehrchen", "NODES").node_group = gn

gx, gy, gz = (v / 1000 for v in info["gebiet_mm"])
KQ = round(gx / (info["dx_mm"] / 1000) / 1) and 3                  # Kacheln quer (tauscher_video --kacheln, Standard 3)
c = Vector((gx / 2, gy / 2, gz / 2))
welt = bpy.data.worlds.new("Welt"); sc.world = welt; welt.use_nodes = True
welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.022, 0.03, 1)
cam = bpy.data.cameras.new("Kamera"); cam.lens = 35; cam.clip_start = 0.0005; cam.clip_end = 5
co = bpy.data.objects.new("Kamera", cam); sc.collection.objects.link(co); sc.camera = co
co.location = c + Vector((0.55 * gz, -1.25 * gz, 0.45 * gz))
co.rotation_euler = (c - co.location).to_track_quat("-Z", "X").to_euler()
sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = proben
sc.render.resolution_x, sc.render.resolution_y = breite, breite * 9 // 16
sc.view_settings.view_transform = "Standard"


def setze(datei):
    d = np.load(datei); S = d["xyz"] / 1000.0; th = d["theta"]
    hinten = S[:, -1, 1] >= gy / KQ                                # vordere Kachelreihe ist weggeschnitten
    S, th = S[hinten], th[hinten]
    n, k, _ = S.shape
    me.clear_geometry()
    me.vertices.add(n * k); me.vertices.foreach_set("co", S.reshape(-1).astype(np.float32))
    kan = np.stack([np.arange(k - 1), np.arange(1, k)], 1)[None] + (np.arange(n) * k)[:, None, None]
    me.edges.add(n * (k - 1)); me.edges.foreach_set("vertices", kan.reshape(-1).astype(np.int32))
    a = me.attributes.new("farbe", "FLOAT", "POINT"); a.data.foreach_set("value", np.repeat(np.clip(th / 1.6, 0, 1), k).astype(np.float32))
    me.update()


for i, b in enumerate(bilder):
    setze(b)
    sc.render.filepath = str(V / "bilder" / f"{von + i:04d}.png")
    bpy.ops.render.render(write_still=True)
print("BLENDER_FERTIG")
