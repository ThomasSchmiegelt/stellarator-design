"""plasma_video_blender.py — realistisches Plasmavideo mit Blender Cycles (GPU), Bild fuer Bild, pausier- und fortsetzbar.

  blender -b -P stellarator/plasma_video_blender.py -- --test            # 4 Probebilder (Zeit messen, ansehen)
  blender -b -P stellarator/plasma_video_blender.py -- --von 0 --bis 600  # Film; vorhandene Bilder werden uebersprungen
  (Daten vorher: .venv-opt/bin/python -m stellarator.plasma_video_daten)

Leuchten "physikalisch ehrlich": Der heisse Kern (14 keV) sendet kaum sichtbares Licht; sichtbar leuchtet der kuehlere
Rand, vor allem Wasserstoff (Balmer-Linien H-alpha rot, H-beta blaugruen -> rosa). Deshalb leuchtet hier nur die Schicht
zwischen s = 0,85 und s = 1, der Kern gar nicht. Die Teilchen (Ionen) sind zur Veranschaulichung stark
vergroessert und rund 50 000-fach verlangsamt: echte Deuterium-Ionen (14 keV, 1,2e6 m/s) umrunden den Ring in rund
60 Mikrosekunden; Elektronen sind noch 60-mal schneller. Die Geschwindigkeiten im Film sind nicht massstaeblich.
"""
import math
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORDNER = ROOT / "sim" / "video_plasma"
BILDER = ORDNER / "bilder"
FPS, SEK = 30, 20
NFR = FPS * SEK

ROSA = (1.0, 0.28, 0.55, 1.0)
TEILCHEN = (0.75, 0.92, 1.0, 1.0)
import os
BELICHT = float(os.environ.get("BELICHT", "0"))
BELICHT_INNEN = float(os.environ.get("BELICHT_INNEN", "-1.3"))
LEUCHT = 0.35          # Volumen-Leuchtstaerke der Randschicht [W/m^3 in Blender-Einheiten]


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    d = dict(test="--test" in a, von=0, bis=NFR, breite=1280, hoehe=720, samples=96)
    for k in ("von", "bis", "breite", "hoehe", "samples"):
        if f"--{k}" in a:
            d[k] = int(a[a.index(f"--{k}") + 1])
    return d


# ---------- Geometrie ----------
def gitter_mesh(name, p, nphi, nth, umdrehen=False, phi_maske=None):
    p = p.reshape(nphi, nth, 3)
    verts = p.reshape(-1, 3).tolist(); faces = []
    for i in range(nphi):
        if phi_maske is not None and not (phi_maske[i] and phi_maske[(i + 1) % nphi]):
            continue
        for j in range(nth):
            a, b = i * nth + j, i * nth + (j + 1) % nth
            c, d = ((i + 1) % nphi) * nth + (j + 1) % nth, ((i + 1) % nphi) * nth + j
            faces.append((a, d, c, b) if umdrehen else (a, b, c, d))
    m = bpy.data.meshes.new(name); m.from_pydata(verts, [], faces); m.update()
    for poly in m.polygons:
        poly.use_smooth = True
    return m


def schale(name, aussen, innen, nphi, nth):
    """Geschlossene Doppelschale (aussen nach aussen, innen nach innen orientiert) = Volumen dazwischen."""
    # Eckenreihenfolge (a,b,c,d) ergibt Normalen nach INNEN (geprueft) -> aussen umdrehen, innen so lassen
    m1 = gitter_mesh(name + "_a", aussen, nphi, nth, umdrehen=True); m2 = gitter_mesh(name + "_i", innen, nphi, nth)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(m1); bm.from_mesh(m2)
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free()
    return m


def spule_mesh(name, rahmen, b):
    g, n, w = rahmen[:, 0], rahmen[:, 1], rahmen[:, 2]; h = b / 2; N = len(g)
    ecken = [g + h * n + h * w, g - h * n + h * w, g - h * n - h * w, g + h * n - h * w]
    verts = np.stack(ecken, 1).reshape(-1, 3).tolist(); faces = []
    for i in range(N):
        k = (i + 1) % N
        for e in range(4):
            f = (e + 1) % 4
            faces.append((i * 4 + e, k * 4 + e, k * 4 + f, i * 4 + f))
    m = bpy.data.meshes.new(name); m.from_pydata(verts, [], faces); m.update()
    return m                                              # eckig lassen (Wickelpaket mit Gehaeuse)


def objekt(name, mesh, mat):
    o = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat); return o


# ---------- Materialien ----------
def mat_volumen(name, farbe, staerke):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = farbe; em.inputs["Strength"].default_value = staerke
    nt.links.new(em.outputs[0], out.inputs["Volume"]); return m


def mat_metall(name, farbe, rau, metall=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = farbe; b.inputs["Roughness"].default_value = rau
    b.inputs["Metallic"].default_value = metall; return m


def mat_kacheln(name):
    """Erstwand aus Wolframkacheln (ca. 0,5 m): dunkles, raues Metall, Fugen dunkler, leichte Unebenheit."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.55
    tc = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 2.0; br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Color1"].default_value = (0.16, 0.155, 0.15, 1); br.inputs["Color2"].default_value = (0.12, 0.118, 0.115, 1)
    br.inputs["Mortar"].default_value = (0.02, 0.02, 0.02, 1); br.offset = 0.5
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.35
    nt.links.new(br.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_leucht(name, farbe, staerke):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = farbe; em.inputs["Strength"].default_value = staerke
    nt.links.new(em.outputs[0], out.inputs["Surface"]); return m


# ---------- Teilchen als Punktwolke (Geometry Nodes: Mesh to Points, Radius aus Attribut) ----------
def punktwolke(mat):
    m = bpy.data.meshes.new("teilchen"); o = bpy.data.objects.new("teilchen", m)
    bpy.context.scene.collection.objects.link(o)
    ng = bpy.data.node_groups.new("punkte", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput")
    mp = ng.nodes.new("GeometryNodeMeshToPoints"); at = ng.nodes.new("GeometryNodeInputNamedAttribute")
    at.data_type = "FLOAT"; at.inputs["Name"].default_value = "r"
    sm = ng.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = mat
    ng.links.new(gi.outputs[0], mp.inputs["Mesh"]); ng.links.new(at.outputs["Attribute"], mp.inputs["Radius"])
    ng.links.new(mp.outputs[0], sm.inputs["Geometry"]); ng.links.new(sm.outputs[0], go.inputs[0])
    mod = o.modifiers.new("punkte", "NODES"); mod.node_group = ng
    return o


def teilchen_setzen(o, linien, f, kam=None, n_je=40, v=24.0, schweif=60, dschweif=0.035):
    pts, rad = [], []
    for k, L in enumerate(linien):
        n = len(L); laenge = (n - 1) * 0.25
        richt = 1 if k % 2 == 0 else -1                        # Nachbarlinien gegenlaeufig: Ionen und Elektronen
        for j in range(n_je):
            s0 = (j / n_je * laenge + richt * v * f / FPS) % laenge
            for t in range(schweif + 1):
                s = (s0 - richt * t * dschweif) % laenge; x = s / 0.25; i = int(x); u = x - i
                p = L[i] * (1 - u) + L[min(i + 1, n - 1)] * u
                pts.append(p); rad.append(0.03 * (1 - t / (schweif + 1.5)))
    pts = np.array(pts); rad = np.array(rad)
    if kam is not None:                                     # nahe der Kamera verkleinern (scheinbare Groesse begrenzen)
        rad *= np.clip((np.linalg.norm(pts - kam, axis=1) - 1.0) / 3.0, 0.0, 1.0)   # < 1 m ausgeblendet
    m = o.data; m.clear_geometry(); m.from_pydata(pts.tolist(), [], [])
    a = m.attributes.get("r") or m.attributes.new("r", "FLOAT", "POINT")
    a.data.foreach_set("value", np.array(rad, dtype=np.float32)); m.update()


# ---------- Kamera ----------
def glatt(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def achse(phi, d):
    """magnetische Achse (Anlagengroesse) aus der Szene-Datei."""
    return d["achse_R"](phi), d["achse_Z"](phi)


def _achspunkt(ph, d):
    R, Z = achse(ph, d); return np.array([R * math.cos(ph), R * math.sin(ph), Z])


def _aussen(az_grad, abst, hoehe):
    az = math.radians(az_grad); return np.array([abst * math.cos(az), abst * math.sin(az), hoehe])


def kamera_bahn(f, d):
    """Rauszoomen: erst im Plasma (Detail), dann durch den offenen Sektor hinaus, dann Gesamtansicht."""
    t = f / FPS
    # 0-6 s: im Plasma entlang der Achse, von phi 200 nach 10 Grad (geschlossener Teil mit Wand), Blick in Fahrtrichtung
    if t <= 6:
        ph = math.radians(200 - 190 * t / 6.0)
        return _achspunkt(ph, d), _achspunkt(ph - math.radians(25), d)
    p0 = _achspunkt(math.radians(10), d); z0 = _achspunkt(math.radians(-15), d)
    pA = _aussen(0, 24, 11); zA = np.array([-1.0, 0.0, -1.0])
    # 6-10 s: Aufstieg durch den offenen Sektor (Bezier), Blick dreht von voraus auf die Anlagenmitte
    if t <= 10:
        u = glatt((t - 6) / 4.0); k = _aussen(-5, 12.5, 9.0)
        pos = (1 - u) ** 2 * p0 + 2 * u * (1 - u) * k + u ** 2 * pA
        return pos, z0 * (1 - u) + zA * u
    # 10-20 s: zurueckziehen und schwenken, letzte 1,5 s ruhig
    u = glatt((t - 10) / 8.5)
    return _aussen(0 + 55 * u, 24 + 16 * u, 11 + 9 * u), zA


def kamera_setzen(cam, pos, ziel):
    cam.location = pos.tolist()
    rich = ziel - pos
    from mathutils import Vector
    cam.rotation_euler = Vector(rich.tolist()).to_track_quat("-Z", "Y").to_euler()


# ---------- Szene ----------
def szene(a):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    d = dict(np.load(ORDNER / "szene.npz"))
    nphi, nth = int(d["nphi"]), int(d["nth"])
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
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
    sc.cycles.device = "GPU"
    sc.cycles.samples = a["samples"]; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4; sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 1.0
    sc.render.resolution_x, sc.render.resolution_y = a["breite"], a["hoehe"]
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "AgX" if "AgX" in [x.identifier for x in
                                                          type(sc.view_settings).bl_rna.properties["view_transform"].enum_items] else "Filmic"
    # Welt: fast dunkel (Halle)
    w = bpy.data.worlds.new("welt"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.005, 0.007, 1)
    # Plasma: leuchtende Randschicht + schwacher Kern
    objekt("randschicht", schale("randschicht", d["rand"], d["innen"], nphi, nth), mat_volumen("rand_licht", ROSA, LEUCHT))
    # Kern: kein eigenes Volumen (deckungsgleiche Grenze mit der Randschicht verwirrt Cycles; der heisse Kern leuchtet
    # sichtbar ohnehin kaum)
    # Erstwand mit offenem Sektor -70..+70 Grad
    phi = np.linspace(0, 2 * np.pi, nphi, endpoint=False); phi_g = (np.degrees(phi) + 180) % 360 - 180
    objekt("wand", gitter_mesh("wand", d["wand"], nphi, nth, umdrehen=True, phi_maske=np.abs(phi_g) > 70),
           mat_kacheln("wolfram"))
    # Spulen
    mst = mat_metall("stahl", (0.56, 0.57, 0.6, 1), 0.33)
    for i, r in enumerate(d["spulen"] if not os.environ.get("OHNE_SPULEN") else []):
        objekt(f"spule{i}", spule_mesh(f"spule{i}", r, float(d["spule_breite"])), mst)
    # Feldlinien selbst sind unsichtbar; die Teilchen zeichnen sie mit ihren Schweifen nach
    grenzen = np.r_[0, np.cumsum(d["linien_n"])]
    linien = [d["linien_xyz"][grenzen[k]:grenzen[k + 1]] for k in range(len(d["linien_n"]))]
    tl = punktwolke(mat_leucht("teilchen", TEILCHEN, 6.0))
    # schwaches Fuehrungslicht fuer die Spulenform
    li = bpy.data.lights.new("oben", "AREA"); li.energy = 9000; li.size = 30
    lo = bpy.data.objects.new("oben", li); lo.location = (0, 0, 40); sc.collection.objects.link(lo)
    camd = bpy.data.cameras.new("kamera"); camd.lens = 24; camd.clip_start = 0.05; camd.clip_end = 400
    cam = bpy.data.objects.new("kamera", camd); sc.collection.objects.link(cam); sc.camera = cam
    # Achse fuer die Kamera
    ra, za, nfp = d["achse_raxis"], d["achse_zaxis"], int(d["nfp"])
    d["achse_R"] = lambda p: float(sum(ra[j] * math.cos(j * nfp * p) for j in range(len(ra))))
    d["achse_Z"] = lambda p: float(-sum(za[j] * math.sin(j * nfp * p) for j in range(len(za))))
    return d, cam, tl, linien


def main():
    a = args(); BILDER.mkdir(parents=True, exist_ok=True)
    d, cam, tl, linien = szene(a)
    import time
    frames = [int(x) for x in os.environ.get("PROBE", "0,200,400,470,530,595").split(",")] if a["test"] else range(a["von"], a["bis"])
    for f in frames:
        ziel = (ORDNER / "probe" if a["test"] else BILDER) / f"f{f:04d}.png"
        ziel.parent.mkdir(exist_ok=True)
        if ziel.exists() and not a["test"]:
            continue                                     # fortsetzen: fertige Bilder ueberspringen
        t0 = time.time()
        kp, kz = kamera_bahn(f, d)
        teilchen_setzen(tl, linien, f, kam=kp); kamera_setzen(cam, kp, kz)
        # Belichtung wie eine echte Kamera: im Plasma 1,3 Blenden dunkler (Uebergang 12-14 s)
        bpy.context.scene.view_settings.exposure = BELICHT_INNEN * (1 - glatt((f / FPS - 6) / 3.0)) + BELICHT
        bpy.context.scene.render.filepath = str(ziel) + ".tmp.png"
        bpy.ops.render.render(write_still=True)
        Path(str(ziel) + ".tmp.png").rename(ziel)          # erst nach vollstaendigem Schreiben umbenennen
        print(f"BILD {f} {time.time() - t0:.1f} s", flush=True)


main()
