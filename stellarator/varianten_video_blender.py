"""varianten_video_blender.py — Video aller Entwurfsvarianten (Blender Cycles, GPU), Bild fuer Bild, pausier-/fortsetzbar.

  blender -b -P stellarator/varianten_video_blender.py -- --test                 # Probebilder je Abschnitt
  blender -b -P stellarator/varianten_video_blender.py -- --von 0 --bis 2040     # Film; vorhandene Bilder uebersprungen
  (Daten vorher: .venv/bin/python -m stellarator.varianten_video_daten; Schnitt: stellarator/varianten_video_schnitt.py)

Ablauf (30 Bilder/s, 84 s):
  P  0-8 s    PicoGK-Vorspann: Entwurf 0169 entsteht als Voxelfeld (0,3-m-Wuerfel, stilisiert, Schicht fuer Schicht
              von unten), ab 4 s Ueberblendung in das echte PicoGK-Netz (80-mm-Voxel, glatte Flaeche); in der
              Magnetfeldszene, wenn die Gehaeuse glasig sind, Wechsel auf die exakte Flaeche des Rechenmodells (Gehaeuse, Verbinder, Wickelpaket aus
              struktur.vtu; Plasma, Package, Lager aus PicoGK) - die PicoGK-Netze (80 mm, 150 k Dreiecke) sind fuer
              Nahaufnahmen zu grob
  M  8-16 s   Magnetfeld von 0169: Gehaeuse werden glasig, berechnete Feldlinien wachsen, Plasmarand faerbt sich
              nach |B| (Biot-Savart, echte Stroeme; Daten stellarator/varianten_video_rechnung.py), dann zurueck
  F 16-24 s   Festigkeit von 0169: Gehaeuse leicht transparent, von-Mises-Spannung aus Elmer erscheint auf derselben
              Flaeche, Verformung 150-fach ueberhoeht ein- und ausgeblendet, dann zurueck
  A 24-34 s   die "wilden" Varianten: 15 Entwuerfe mit der kleinsten Reserve, je 0,67 s, Kamera kreist
  B 34-58 s   alle geometrisch darstellbaren Entwuerfe im Feld; die unzulaessigen versinken der Reihe nach
              (schlechteste zuerst, knapp verfehlte zuletzt); uebrig bleiben die zulaessigen
  C 58-66 s   die zulaessigen ruecken in eine Reihe
  D 66-84 s   der empfohlene Entwurf 0169 im Treppenschnitt (Plasma, Erstwand+Blanket, Abschirmung, Vakuumgefaess,
              Wickelpaket, Gehaeuse, Verbinder, Lager), Kamera kreist
Farben: Gehaeuse blau = zulaessig, gelb = knapp verfehlt, rot = deutlich verfehlt. Im Bild steht nur der Name
(setzt der Schnitt); Erklaerungen im Begleittext.
"""
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ORDNER = ROOT / "sim" / "video_varianten"
NETZE = ORDNER / "netze"
BILDER = ORDNER / "bilder"
FPS = 30
P0, M0, F0, A0, B0, C0, D0, ENDE = 0, 8 * FPS, 16 * FPS, 24 * FPS, 34 * FPS, 58 * FPS, 66 * FPS, 84 * FPS
UEBERHOEHUNG = 150.0              # Verformung in der Festigkeitsszene
B_SKALA = (5.5, 7.5)              # |B| auf dem Plasmarand [T] -> Farbe
VM_SKALA = (0.0, 600.0)           # von Mises [MPa] -> Farbe
WILD_DAUER = 20
ABSTAND = 42.0                    # Rasterabstand im Feld [m]
BODEN_Z = -11.0
N_SCHICHT = 48                    # Voxelschichten im Vorspann

FARBE = {"zulaessig": ((0.165, 0.47, 0.84), (0.07, 0.22, 0.5)),       # Gehaeuse, Verbinder
         "knapp": ((0.93, 0.63, 0.0), (0.6, 0.38, 0.0)),
         "ausfall": ((0.80, 0.25, 0.17), (0.5, 0.13, 0.08))}
SCHNITTFARBE = {"plasma": (0.91, 0.48, 0.64), "package_erstwand_blanket": (0.93, 0.63, 0.0),
                "package_abschirmung": (0.106, 0.686, 0.478), "package_vakuumgefaess": (0.62, 0.63, 0.65),
                "wickelpaket": (0.92, 0.41, 0.2), "gehaeuse": (0.165, 0.47, 0.84), "verbinder": (0.07, 0.22, 0.5),
                "lager": (0.06, 0.06, 0.065)}
VOXELFARBE = {"gehaeuse": (0.55, 0.62, 0.72), "verbinder": (0.36, 0.42, 0.52), "plasma": (0.91, 0.48, 0.64)}


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    d = dict(test="--test" in a, von=0, bis=ENDE, breite=1920, hoehe=1080, samples=192)
    for k in ("von", "bis", "breite", "hoehe", "samples"):
        if f"--{k}" in a:
            d[k] = int(a[a.index(f"--{k}") + 1])
    return d


def glatt(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- Materialien
def mat(name, farbe, metall=0.15, rau=0.55, leucht=0.0, alpha=1.0, lack=0.08):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*farbe, 1)
    b.inputs["Metallic"].default_value = metall; b.inputs["Roughness"].default_value = rau
    b.inputs["Coat Weight"].default_value = lack; b.inputs["Coat Roughness"].default_value = 0.2
    if leucht:
        b.inputs["Emission Color"].default_value = (*farbe, 1); b.inputs["Emission Strength"].default_value = leucht
    m.blend_method = "BLEND"
    b.inputs["Alpha"].default_value = alpha
    return m


def alpha(m, a):
    m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = a


def netz_objekt(name, v, f, material, eltern=None, glatt_schatten=True):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v)); me.vertices.foreach_set("co", v.ravel())
    k = f.shape[1]
    me.loops.add(f.size); me.loops.foreach_set("vertex_index", f.ravel())
    me.polygons.add(len(f)); me.polygons.foreach_set("loop_start", np.arange(0, f.size, k))
    me.polygons.foreach_set("loop_total", np.full(len(f), k))
    me.update(); me.validate()
    me.polygons.foreach_set("use_smooth", np.full(len(f), glatt_schatten))
    if glatt_schatten:                                   # Kanten > 35 Grad hart (ausgeduennte Netze sonst wellig)
        me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(50)
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(material)
    bpy.context.scene.collection.objects.link(ob)
    if eltern is not None:
        ob.parent = eltern
    return ob


def leer(name):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    return e


def modell(name, datei, mats):
    """Alle Teile einer npz-Datei unter einem Leerobjekt; mats: Teil -> Material."""
    d = np.load(datei); e = leer(name); kinder = []
    for t, m in mats.items():
        if f"{t}_v" in d:
            kinder.append(netz_objekt(f"{name}_{t}", d[f"{t}_v"], d[f"{t}_f"], m, e))
    return e, kinder


def wuerfel(idx, h, luecke=0.05):
    """Wuerfel je Voxel (Gitterindex idx, Kante h, kleiner Spalt), als ein Netz aus Vierecken."""
    c = (idx.astype(np.float32) + 0.5) * h; a = 0.5 * h * (1 - luecke)
    ecken = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                      [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], np.float32) * a
    v = (c[:, None, :] + ecken[None]).reshape(-1, 3)
    q = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    f = (np.arange(len(c))[:, None, None] * 8 + q[None]).reshape(-1, 4)
    return v, f.astype(np.int32)


def zeige(kinder, an):
    for k in kinder:
        k.hide_render = not an


def rampe_mat(name, attr, stopps, grund, leucht=0.0, rau=0.5, grund2=None, attr2=None):
    """Material mit stufenloser Mischung (Knoten "mischung") von der Grundfarbe zur Farbrampe ueber ein Knotenattribut
    (0..1). grund2/attr2: zweite Grundfarbe je Knoten (z. B. Verbinder dunkler). Alpha steuerbar wie mat()."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = rau; b.inputs["Metallic"].default_value = 0.15
    b.inputs["Coat Weight"].default_value = 0.08
    at = N.new("ShaderNodeAttribute"); at.attribute_name = attr
    rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position, el[0].color = stopps[0][0], (*stopps[0][1], 1)
    el[1].position, el[1].color = stopps[-1][0], (*stopps[-1][1], 1)
    for pos, c in stopps[1:-1]:
        e = el.new(pos); e.color = (*c, 1)
    L.new(at.outputs["Fac"], rp.inputs[0])
    g = N.new("ShaderNodeMixRGB"); g.inputs["Color1"].default_value = (*grund, 1); g.inputs["Fac"].default_value = 0.0
    g.inputs["Color2"].default_value = (*(grund2 or grund), 1)
    if attr2:
        a2 = N.new("ShaderNodeAttribute"); a2.attribute_name = attr2; L.new(a2.outputs["Fac"], g.inputs["Fac"])
    mi = N.new("ShaderNodeMixRGB"); mi.name = "mischung"; mi.inputs["Fac"].default_value = 0.0
    L.new(g.outputs["Color"], mi.inputs["Color1"]); L.new(rp.outputs[0], mi.inputs["Color2"])
    L.new(mi.outputs["Color"], b.inputs["Base Color"])
    if leucht:
        L.new(mi.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = leucht
    m.blend_method = "BLEND"
    return m


def mischung(m, x):
    m.node_tree.nodes["mischung"].inputs["Fac"].default_value = x


def attribut(ob, name, werte):
    a = ob.data.attributes.new(name, "FLOAT", "POINT"); a.data.foreach_set("value", np.asarray(werte, np.float32))


def kurve(name, pts, material, dicke):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    sp.points.foreach_set("co", np.c_[pts, np.ones(len(pts))].astype(np.float32).ravel())
    cu.bevel_depth = dicke; cu.bevel_resolution = 3; cu.bevel_factor_mapping_end = "SPLINE"
    ob = bpy.data.objects.new(name, cu); ob.data.materials.append(material)
    bpy.context.scene.collection.objects.link(ob)
    return ob


INFERNO = [(0.0, (0.02, 0.01, 0.12)), (0.3, (0.33, 0.06, 0.43)), (0.55, (0.73, 0.21, 0.33)),
           (0.8, (0.98, 0.55, 0.04)), (1.0, (0.99, 0.95, 0.55))]
TURBO = [(0.0, (0.03, 0.08, 0.40)), (0.15, (0.12, 0.38, 0.92)), (0.35, (0.10, 0.80, 0.80)),
         (0.55, (0.45, 0.98, 0.32)), (0.72, (0.96, 0.78, 0.14)), (0.87, (0.98, 0.40, 0.07)), (1.0, (0.60, 0.05, 0.02))]


# ---------------------------------------------------------------- Szene
def welt(sc):
    """Dunkler Verlauf hinter dem Modell (nur fuer die Kamera), schwaches kuehles Umgebungslicht."""
    w = bpy.data.worlds.new("welt"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; N = nt.nodes; L = nt.links
    N.clear()
    aus = N.new("ShaderNodeOutputWorld")
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Window"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); L.new(sep.outputs["Y"], ramp.inputs[0])
    ramp.color_ramp.elements[0].color = (0.006, 0.007, 0.010, 1); ramp.color_ramp.elements[1].color = (0.040, 0.050, 0.068, 1)
    bg_kam = N.new("ShaderNodeBackground"); L.new(ramp.outputs[0], bg_kam.inputs[0])
    bg_licht = N.new("ShaderNodeBackground"); bg_licht.inputs[0].default_value = (0.05, 0.06, 0.08, 1)
    bg_licht.inputs[1].default_value = 0.6
    lp = N.new("ShaderNodeLightPath"); mix = N.new("ShaderNodeMixShader")
    L.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); L.new(bg_licht.outputs[0], mix.inputs[1])
    L.new(bg_kam.outputs[0], mix.inputs[2]); L.new(mix.outputs[0], aus.inputs[0])


def sonne(sc, name, energie, winkel, rot, farbe=(1, 1, 1)):
    l = bpy.data.lights.new(name, "SUN"); l.energy = energie; l.angle = math.radians(winkel); l.color = farbe
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o)
    o.rotation_euler = tuple(math.radians(x) for x in rot)


def szene(a):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.engine = "CYCLES"
    pr = bpy.context.preferences.addons["cycles"].preferences
    for typ in ("OPTIX", "CUDA"):
        try:
            pr.compute_device_type = typ; pr.get_devices()
            if any(x.type == typ for x in pr.devices):
                break
        except TypeError:
            continue
    for dev in pr.devices:
        dev.use = dev.type in ("OPTIX", "CUDA")
    # Dieses Blender hat keinen Entrauscher -> mehr Samples, adaptiv
    sc.cycles.device = "GPU"; sc.cycles.samples = a["samples"]; sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.015
    sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16; sc.cycles.filter_width = 1.6
    sc.render.resolution_x, sc.render.resolution_y = a["breite"], a["hoehe"]
    sc.render.image_settings.file_format = "PNG"
    vt = [x.identifier for x in type(sc.view_settings).bl_rna.properties["view_transform"].enum_items]
    sc.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast" if "AgX" in vt else "Medium High Contrast"
    except TypeError:
        pass
    welt(sc)
    sonne(sc, "haupt", 3.4, 14, (48, 8, 40), (1.0, 0.97, 0.92))          # weiches Hauptlicht
    sonne(sc, "gegen", 1.8, 8, (62, 0, 215), (0.75, 0.85, 1.0))          # kuehles Gegenlicht (Kanten)
    sonne(sc, "fuell", 0.5, 30, (75, 0, -120))
    bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, BODEN_Z))
    boden = bpy.context.object; boden.data.materials.append(mat("boden", (0.03, 0.033, 0.04), 0.0, 0.62, lack=0.0))
    cam = bpy.data.objects.new("kamera", bpy.data.cameras.new("kamera")); sc.collection.objects.link(cam)
    sc.camera = cam; cam.data.lens = 35; cam.data.clip_end = 5000
    cam.data.dof.aperture_fstop = 4.0

    V = json.loads((ORDNER / "varianten.json").read_text())
    var = {e["nr"]: e for e in V["varianten"]}
    M = {s: (mat(f"geh_{s}", g), mat(f"verb_{s}", v)) for s, (g, v) in FARBE.items()}
    m_plasma = mat("plasma", (0.91, 0.48, 0.64), 0.0, 0.5, leucht=0.45, lack=0.0)
    m_vv = mat("vakuumgefaess", (0.62, 0.63, 0.65), 0.2, 0.4, alpha=0.22, lack=0.0)

    # Vorspann: Voxel + glatte Oberflaeche von 0169
    vd = np.load(NETZE / "0169_voxel.npz"); h = float(vd["h"])
    zmin = min(int(vd[t][:, 2].min()) for t in VOXELFARBE); zmax = max(int(vd[t][:, 2].max()) for t in VOXELFARBE)
    grenzen = np.linspace(zmin, zmax + 1, N_SCHICHT + 1)
    vmat = {t: mat(f"vox_{t}", c, 0.0, 0.55, leucht=0.3 if t == "plasma" else 0.0, lack=0.1) for t, c in VOXELFARBE.items()}
    schichten = []                                                   # je Schicht die Objekte aller Teile
    for s in range(N_SCHICHT):
        obs = []
        for t in VOXELFARBE:
            idx = vd[t]; sel = idx[(idx[:, 2] >= grenzen[s]) & (idx[:, 2] < grenzen[s + 1])]
            if len(sel):
                v, f = wuerfel(sel, h); obs.append(netz_objekt(f"vox_{t}_{s}", v, f, vmat[t], glatt_schatten=False))
        schichten.append(obs)
    gmat = {"gehaeuse": mat("g_geh", FARBE["zulaessig"][0]), "verbinder": mat("g_verb", FARBE["zulaessig"][1]),
            "plasma": mat("g_plasma", (0.91, 0.48, 0.64), 0.0, 0.5, leucht=0.45, lack=0.0)}
    _, glatt_k = modell("g0169", NETZE / "0169_glatt.npz", gmat)
    pmat = {"gehaeuse": mat("p_geh", FARBE["zulaessig"][0]), "verbinder": mat("p_verb", FARBE["zulaessig"][1]),
            "plasma": mat("p_plasma", (0.91, 0.48, 0.64), 0.0, 0.5, leucht=0.45, lack=0.0)}
    _, pgk_k = modell("p0169", NETZE / "0169_picogk.npz", pmat)       # echtes PicoGK-Netz (80 mm)
    pgk = {k.name.split("_", 1)[1]: k for k in pgk_k}

    # Rechenszenen (M, F): Feldlinien, Plasmarand nach |B|, Stahl nach von Mises mit Verformung
    rd = np.load(NETZE / "0169_rechnung.npz"); gd = np.load(NETZE / "0169_glatt.npz")
    m_linie = mat("feldlinie", (0.55, 0.88, 1.0), 0.0, 0.4, leucht=6.0, lack=0.0)
    linien = [kurve(f"feldlinie_{i}", p, m_linie, 0.10) for i, p in enumerate(rd["feldlinien"])]
    m_pB = rampe_mat("plasma_B", "B", INFERNO, (0.91, 0.48, 0.64), leucht=0.6)
    pB = netz_objekt("plasma_B", gd["plasma_v"], gd["plasma_f"], m_pB)
    attribut(pB, "B", np.clip((rd["plasma_B"] - B_SKALA[0]) / (B_SKALA[1] - B_SKALA[0]), 0, 1))
    m_vm = rampe_mat("stahl_vm", "vm", TURBO, FARBE["zulaessig"][0], leucht=0.25, rau=0.6, grund2=FARBE["zulaessig"][1], attr2="verb")
    m_vm.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.0
    st = netz_objekt("stahl_vm", rd["stahl_v"], rd["stahl_f"], m_vm)
    attribut(st, "vm", np.clip((rd["stahl_vm"] - VM_SKALA[0]) / (VM_SKALA[1] - VM_SKALA[0]), 0, 1))
    attribut(st, "verb", rd["stahl_verb"])
    st.shape_key_add(name="Basis"); kv = st.shape_key_add(name="verformt", from_mix=False)
    kv.data.foreach_set("co", (rd["stahl_v"] + UEBERHOEHUNG * rd["stahl_u"]).astype(np.float32).ravel())
    gk = {k.name.split("_", 1)[1]: k for k in glatt_k}                  # gehaeuse, verbinder, plasma
    rechnung = dict(linien=linien, m_linie=m_linie, pB=pB, m_pB=m_pB, st=st, m_vm=m_vm, kv=kv, gk=gk)

    # Feld aller Entwuerfe (B, C)
    nrs = sorted(var); n = len(nrs); sp = int(math.ceil(math.sqrt(n)))
    feld = {}
    for i, nr in enumerate(nrs):
        s = var[nr]["status"]
        e, k = modell(f"r{nr}", NETZE / f"{nr}_raster.npz", {"gehaeuse": M[s][0], "verbinder": M[s][1], "plasma": m_plasma})
        x = (i % sp - (sp - 1) / 2) * ABSTAND; y = (i // sp - (sp - 1) / 2) * ABSTAND
        feld[nr] = (e, k, Vector((x, y, 0)))
    weg = sorted([nr for nr in nrs if var[nr]["status"] != "zulaessig"], key=lambda nr: var[nr]["robust"])
    zul = [nr for nr in V["zulaessig"] if nr in feld]
    # Wilde (A)
    wild = []
    for nr in V["wild"]:
        e, k = modell(f"w{nr}", NETZE / f"{nr}_voll.npz", {"gehaeuse": M["ausfall"][0], "verbinder": M["ausfall"][1],
                                                          "plasma": m_plasma, "package_vakuumgefaess": m_vv})
        wild.append((e, k))
    # 0169 im Treppenschnitt (D)
    sm = {t: mat(f"s_{t}", c, 0.0 if t in ("plasma", "lager") or t.startswith("package") else 0.25, 0.5,
                 leucht=0.45 if t == "plasma" else 0.0) for t, c in SCHNITTFARBE.items()}
    _, k169 = modell("s0169", NETZE / "0169_schnitt.npz", sm)
    return dict(sc=sc, cam=cam, feld=feld, weg=weg, zul=zul, wild=wild, k169=k169, sp=sp,
                schichten=schichten, vmat=vmat, glatt=glatt_k, gmat=gmat, R=rechnung, pgk=pgk, pmat=pmat)


def kamera(cam, ziel, az_grad, el_grad, dist, schaerfe=False):
    az, el = math.radians(az_grad), math.radians(el_grad)
    pos = Vector(ziel) + dist * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    cam.location = pos
    cam.rotation_euler = (Vector(ziel) - pos).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.use_dof = schaerfe; cam.data.dof.focus_distance = dist


def zustand(S, fr):
    feld, cam = S["feld"], S["cam"]
    for (_, k, _) in feld.values(): zeige(k, False)
    for _, k in S["wild"]: zeige(k, False)
    zeige(S["k169"], False); zeige(S["glatt"], False)
    for obs in S["schichten"]: zeige(obs, False)
    R = S["R"]; zeige(R["linien"] + [R["pB"], R["st"]], False)
    for m in S["gmat"].values(): alpha(m, 1.0)
    zeige(S["pgk"].values(), False)
    for m in S["pmat"].values(): alpha(m, 1.0)
    if fr < M0:                                                      # P: PicoGK-Vorspann
        aufbau = 4.0 * FPS; ueber = (4.0 * FPS, 5.0 * FPS)
        n = int(math.ceil(len(S["schichten"]) * glatt(fr / aufbau))) if fr < aufbau else len(S["schichten"])
        u = glatt((fr - ueber[0]) / (ueber[1] - ueber[0]))
        if u < 1:
            for obs in S["schichten"][:n]: zeige(obs, True)
            for m in S["vmat"].values(): alpha(m, 1 - u)
        if u > 0:                                                    # echtes PicoGK-Netz
            zeige(S["pgk"].values(), True)
            for m in S["pmat"].values(): alpha(m, u)
        kamera(cam, (0, 0, -1.0), -130 + 80 * fr / M0, 30 - 6 * fr / M0, 60 - 8 * glatt(fr / M0), schaerfe=True)
        return
    if fr < F0:                                                      # M: Magnetfeld
        t = (fr - M0) / FPS; u = (fr - M0) / (F0 - M0)
        glas = glatt(t / 1.2) * (1 - glatt((t - 6.8) / 1.2))           # Gehaeuse glasig
        pl = glatt((t - 0.8) / 1.2) * (1 - glatt((t - 6.6) / 1.2))     # Plasma durchsichtig
        fb = glatt((t - 4.3) / 1.5) * (1 - glatt((t - 6.4) / 1.2))     # Plasmarand nach |B|
        zeige(S["glatt"], True); zeige([R["gk"]["plasma"]], False); zeige([R["pB"]], True)
        alpha(S["gmat"]["gehaeuse"], 1 - 0.85 * glas); alpha(S["gmat"]["verbinder"], 1 - 0.85 * glas)
        if t < 1.2:                                                  # noch PicoGK-Netz; Wechsel, wenn glasig
            zeige([R["gk"]["gehaeuse"], R["gk"]["verbinder"]], False); zeige([S["pgk"]["gehaeuse"], S["pgk"]["verbinder"]], True)
            alpha(S["pmat"]["gehaeuse"], 1 - 0.85 * glas); alpha(S["pmat"]["verbinder"], 1 - 0.85 * glas)
        alpha(R["m_pB"], 1 - 0.82 * pl + 0.72 * pl * fb); mischung(R["m_pB"], fb)
        for i, ob in enumerate(R["linien"]):
            w = glatt((t - 1.0 - 0.3 * i) / 2.6)
            ob.data.bevel_factor_end = max(w, 1e-3); ob.hide_render = w <= 0.002 or glas <= 0.01
        alpha(R["m_linie"], glas)
        kamera(cam, (0, 0, -1.0), -50 + 60 * u, 24, 52 - 8 * math.sin(math.pi * u), schaerfe=True)
        return
    if fr < A0:                                                      # F: Festigkeit
        t = (fr - F0) / FPS; u = (fr - F0) / (A0 - F0)
        leicht = glatt(t / 1.0) * (1 - glatt((t - 6.6) / 1.2))          # leicht transparent
        rech = glatt((t - 1.0) / 1.5) * (1 - glatt((t - 5.9) / 1.0))    # Spannung erscheint
        zeige(S["glatt"], True)
        a = 1 - 0.7 * leicht * (1 - rech)
        if 1.0 < t < 6.9:                                            # Rechenflaeche statt Gehaeuse (gleiche Geometrie)
            zeige([R["gk"]["gehaeuse"], R["gk"]["verbinder"]], False); zeige([R["st"]], True)
            alpha(R["m_vm"], a); mischung(R["m_vm"], rech)
            R["kv"].value = glatt((t - 2.8) / 1.6) * (1 - glatt((t - 4.9) / 1.2))
        else:
            alpha(S["gmat"]["gehaeuse"], a); alpha(S["gmat"]["verbinder"], a)
        kamera(cam, (0, 0, -1.0), 10 + 60 * u, 24, 52 - 6 * math.sin(math.pi * u), schaerfe=True)
        return
    if fr < B0:                                                      # A: wilde Varianten
        i = min((fr - A0) // WILD_DAUER, len(S["wild"]) - 1)
        zeige(S["wild"][i][1], True)
        kamera(cam, (0, 0, -1.5), -60 + 360 * (fr - A0) / 900, 28, 68, schaerfe=True)
        return
    if fr < D0:                                                      # B + C: Feld
        fenster = (B0 + 4 * FPS, C0 - 4 * FPS)                       # Versinken 22-38 s
        dauer = 24; n = len(S["weg"])
        for j, nr in enumerate(S["weg"]):
            e, k, p0 = feld[nr]
            start = fenster[0] + (fenster[1] - fenster[0] - dauer) * j / max(n - 1, 1)
            p = glatt((fr - start) / dauer)
            if p >= 1:
                continue
            zeige(k, True); e.scale = (max(1 - p, 1e-3),) * 3; e.location = p0 + Vector((0, 0, -9 * p))
        reihe = glatt((fr - C0) / (6 * FPS))
        for k_, nr in enumerate(S["zul"]):
            e, k, p0 = feld[nr]
            ziel = Vector(((k_ - (len(S["zul"]) - 1) / 2) * ABSTAND, 0, 0))
            zeige(k, True); e.scale = (1, 1, 1); e.location = p0.lerp(ziel, reihe)
        halb = (S["sp"] - 1) / 2 * ABSTAND; dist_b = 2.3 * halb + 120
        if fr < C0:
            u = (fr - B0) / (C0 - B0)
            kamera(cam, (0, 0, 0), -110 + 40 * u, 38 - 6 * glatt(u), dist_b * (1.25 - 0.25 * glatt(u)))
        else:
            u = glatt((fr - C0) / (D0 - C0)); nz = len(S["zul"])
            kamera(cam, (0, 0, 0), -70, 32 - 10 * u, dist_b * (1 - u) + (nz * ABSTAND * 0.95 + 30) * u)
        return
    zeige(S["k169"], True)                                           # D: 0169 im Schnitt
    u = (fr - D0) / (ENDE - D0)
    kamera(cam, (0, 0, -1.0), -150 + 110 * u, 34 - 6 * u, 55 - 8 * glatt(u), schaerfe=True)


def main():
    a = args(); BILDER.mkdir(parents=True, exist_ok=True)
    S = szene(a)
    if a["test"]:
        rahmen = [135, 160, 225, M0 + 10, M0 + 50]
        ziel = ORDNER / "test"; ziel.mkdir(exist_ok=True)
    else:
        rahmen = range(a["von"], min(a["bis"], ENDE)); ziel = BILDER
    for fr in rahmen:
        pfad = ziel / f"{fr:05d}.png"
        if pfad.exists() and not a["test"]:
            continue
        t0 = time.time(); zustand(S, fr)
        S["sc"].render.filepath = str(pfad); bpy.ops.render.render(write_still=True)
        print(f"BILD {fr} {time.time() - t0:.1f} s", flush=True)


main()
