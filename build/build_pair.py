"""
build_pair.py
Builds the 178 First Ave / 115 Avenue A neighbourhood model from NYC Open Data
layers already pulled to disk (plan/*.geojson, plan/trees.json).
Adapted from the 247 Nostrand build: same layers, same palette, two sites.
Run inside Blender in stages: exec(open(...).read()); then stage_massing(), etc.
"""
import bpy, bmesh, json, math, os
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

DATA_DIR = "/private/tmp/claude-501/-Users-michaelweinfeld-Documents-2026-PJ-O-Rourke/d1d61da0-193d-4943-a4c8-c877f4d696c5/scratchpad/ev/plan"
OUT_DIR  = "/Users/michaelweinfeld/Documents/2026/PJ O'Rourke/east-village-178-115"
SITE_LAT, SITE_LON = 40.7277, -73.9837
SITES = {"1004380008": ("SITE_178_FIRST_AVE", "PJ_YELLOW"), "1004350035": ("SITE_115_AVENUE_A", "PJ_ORANGE")}
FT = 0.3048; H_FALLBACK = 9.0; COLLECTION = "EAST_VILLAGE_PAIR"
PALETTE = {"PJ_INK": "0C0C0C", "PJ_CEMENT": "9B9B95", "PJ_CREAM": "F3EFE4", "PJ_YELLOW": "F6C500", "PJ_OLIVE": "5F6B3C", "PJ_ORANGE": "F0611F"}
COSL = math.cos(math.radians(SITE_LAT))

def proj(lon, lat): return ((lon - SITE_LON) * 111320.0 * COSL, (lat - SITE_LAT) * 110540.0)
def hex_to_linear(h):
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0; out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)
def make_materials():
    for name, hexc in PALETTE.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        if b: b.inputs["Base Color"].default_value = hex_to_linear(hexc); b.inputs["Roughness"].default_value = 0.95
        m.diffuse_color = hex_to_linear(hexc)
def load(key):
    return json.load(open(os.path.join(DATA_DIR, key + ".geojson")))["features"]
def rings(geom):
    t = geom.get("type"); c = geom.get("coordinates", [])
    if t == "Polygon": return [c[0]] if c else []
    if t == "MultiPolygon": return [p[0] for p in c if p]
    return []
def contours(geom):
    t = geom.get("type"); c = geom.get("coordinates", [])
    src = [c] if t == "Polygon" else (c if t == "MultiPolygon" else [])
    for poly in src:
        out = []
        for ring in poly:
            pts = [proj(a, b) for a, b in ring]; cl = []
            for p in pts:
                if not cl or abs(p[0]-cl[-1][0]) > 1e-7 or abs(p[1]-cl[-1][1]) > 1e-7: cl.append(p)
            if len(cl) > 2 and abs(cl[0][0]-cl[-1][0]) < 1e-7 and abs(cl[0][1]-cl[-1][1]) < 1e-7: cl = cl[:-1]
            if len(cl) >= 3: out.append(cl)
        if out: yield out
def get_collection():
    old = bpy.data.collections.get(COLLECTION)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(COLLECTION); bpy.context.scene.collection.children.link(col); return col
def col(): return bpy.data.collections.get(COLLECTION) or get_collection()

def extrude_ring(bm, xy, z0, z1):
    cl = []
    for p in xy:
        if not cl or abs(p[0]-cl[-1][0]) > 1e-6 or abs(p[1]-cl[-1][1]) > 1e-6: cl.append(p)
    if len(cl) > 2 and abs(cl[0][0]-cl[-1][0]) < 1e-6 and abs(cl[0][1]-cl[-1][1]) < 1e-6: cl = cl[:-1]
    if len(cl) < 3: return False
    vs = [bm.verts.new((p[0], p[1], z0)) for p in cl]
    try: face = bm.faces.new(vs)
    except ValueError: return False
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)])
    return True

def stage_massing():
    make_materials(); c = get_collection(); feats = load("footprints")
    bases = [float(f["properties"].get("ground_elevation") or 0) for f in feats if f["properties"].get("base_bbl") in SITES]
    base = sum(bases) / len(bases) if bases else 0.0
    bm = bmesh.new(); sbms = {k: bmesh.new() for k in SITES}; n = 0; guessed = 0
    for f in feats:
        p = f["properties"]
        try: h_ft = float(p.get("height_roof") or 0)
        except ValueError: h_ft = 0.0
        h = h_ft * FT
        if h <= 0: h = H_FALLBACK; guessed += 1
        ge = (float(p.get("ground_elevation") or base) - base) * FT
        target = sbms.get(p.get("base_bbl"), bm)
        for ring in rings(f["geometry"]):
            if extrude_ring(target, [proj(a, b) for a, b in ring], ge, ge + h): n += 1
    for b, name, mat in [(bm, "EV_MASSING", "PJ_INK")] + [(sbms[k], SITES[k][0], SITES[k][1]) for k in SITES]:
        bmesh.ops.recalc_face_normals(b, faces=b.faces); me = bpy.data.meshes.new(name); b.to_mesh(me); b.free()
        ob = bpy.data.objects.new(name, me); c.objects.link(ob); ob.data.materials.append(bpy.data.materials[mat])
    return "massing: {} solids, {} without height".format(n, guessed)

def build_flat(key, name, z, mat):
    feats = load(key); verts, faces = [], []
    for f in feats:
        for cont in contours(f["geometry"]):
            vecs = [[Vector((x, y, 0.0)) for (x, y) in ring] for ring in cont]; flat = [v for ring in vecs for v in ring]; b = len(verts)
            try: idx = tessellate_polygon(vecs)
            except Exception: continue
            verts.extend([(v.x, v.y, z) for v in flat]); faces.extend([(b+t[0], b+t[1], b+t[2]) for t in idx])
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); col().objects.link(ob); ob.data.materials.append(bpy.data.materials[mat])
    return "{}: {} tris".format(name, len(faces))
def stage_flat():
    return "; ".join([build_flat("roadbed", "ROADBED", 0.02, "PJ_CEMENT"), build_flat("sidewalk", "SIDEWALK", 0.14, "PJ_CREAM"), build_flat("median", "MEDIAN", 0.18, "PJ_OLIVE")])

def at_fraction(pts, frac):
    segs = [math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1)]; total = sum(segs); want = total * frac; run = 0.0
    for i, s in enumerate(segs):
        if run + s >= want:
            t = (want - run) / s if s else 0.0; a, b = pts[i], pts[i+1]
            return ((a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t), math.atan2(b[1]-a[1], b[0]-a[0]))
        run += s
    return pts[-1], math.atan2(pts[-1][1]-pts[0][1], pts[-1][0]-pts[0][0])
def stage_labels(size=12.0, min_gap=34.0):
    feats = load("centerline"); longest = {}
    for f in feats:
        n = (f["properties"].get("stname_label") or "").strip()
        if not n: continue
        g = f["geometry"]; parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in parts:
            pts = [proj(a, b) for a, b in line]; L = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
            if n not in longest or L > longest[n][0]: longest[n] = (L, pts)
    placed = []
    for name, (L, pts) in sorted(longest.items(), key=lambda kv: -kv[1][0]):
        if L < 40: continue
        spot = None
        for frac in (0.5, 0.3, 0.7, 0.18, 0.82):
            p, ang = at_fraction(pts, frac)
            if all(math.dist(p, q) > min_gap for q in placed): spot = (p, ang); break
        if spot is None: spot = at_fraction(pts, 0.5)
        p, ang = spot
        if ang > math.pi/2: ang -= math.pi
        if ang < -math.pi/2: ang += math.pi
        cu = bpy.data.curves.new("ST_" + name, type='FONT'); cu.body = name; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.size = size; cu.extrude = 0.04; cu.space_character = 1.15
        ob = bpy.data.objects.new("ST_" + name, cu); col().objects.link(ob); ob.location = (p[0], p[1], 0.6); ob.rotation_euler = (0, 0, ang); ob.data.materials.append(bpy.data.materials["PJ_INK"]); placed.append(p)
    return "labels: {}".format(len(placed))

def stage_trees():
    rows = [r for r in json.load(open(os.path.join(DATA_DIR, "trees.json"))) if r.get("status") == "Alive"]
    bm = bmesh.new(); n = 0
    for t in rows:
        try: x, y = proj(float(t["longitude"]), float(t["latitude"])); dbh = float(t.get("tree_dbh") or 6)
        except (TypeError, ValueError, KeyError): continue
        r = max(1.4, min(4.2, 1.2 + dbh * 0.12)); h = max(4.0, min(11.0, 3.5 + dbh * 0.35))
        tb = bmesh.new(); bmesh.ops.create_icosphere(tb, subdivisions=1, radius=1.0); bmesh.ops.scale(tb, vec=(r, r, r * 0.8), verts=tb.verts); bmesh.ops.translate(tb, vec=(x, y, h), verts=tb.verts)
        me = bpy.data.meshes.new("t"); tb.to_mesh(me); tb.free(); bm.from_mesh(me); bpy.data.meshes.remove(me); n += 1
    me = bpy.data.meshes.new("TREES"); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new("TREES", me); col().objects.link(ob); ob.data.materials.append(bpy.data.materials["PJ_OLIVE"])
    return "trees: {}".format(n)

def stage_ground():
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -0.3)); g = bpy.context.active_object; g.name = "GROUND"
    for c in g.users_collection: c.objects.unlink(g)
    col().objects.link(g); g.data.materials.append(bpy.data.materials["PJ_CREAM"]); return "ground"

def stage_cameras():
    sc = bpy.context.scene
    # sun + world
    if not bpy.data.objects.get("SUN"):
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 300)); s = bpy.context.active_object; s.name = "SUN"; s.data.energy = 3.0; s.rotation_euler = (math.radians(50), 0, math.radians(35))
    w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg: bg.inputs[0].default_value = (0.2, 0.2, 0.19, 1); bg.inputs[1].default_value = 1.0
    # plan camera, orthographic, slight grid rotation so avenues run up the page
    for name, loc, rot, ortho in (("CAM_PLAN", (0, 0, 600), (0, 0, math.radians(29)), 620), ("CAM_WIDE", (0, 0, 600), (0, 0, math.radians(29)), 1000)):
        cam = bpy.data.objects.get(name)
        if not cam:
            cd = bpy.data.cameras.new(name); cam = bpy.data.objects.new(name, cd); sc.collection.objects.link(cam)
        cam.location = loc; cam.rotation_euler = rot; cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho; cam.data.clip_end = 2000
    axon = bpy.data.objects.get("CAM_AXON")
    if not axon:
        cd = bpy.data.cameras.new("CAM_AXON"); axon = bpy.data.objects.new("CAM_AXON", cd); sc.collection.objects.link(axon)
    axon.location = (-260, -420, 420); axon.rotation_euler = (math.radians(50), 0, math.radians(-29)); axon.data.type = 'ORTHO'; axon.data.ortho_scale = 760; axon.data.clip_end = 3000
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'SceneEEVEE') and 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    sc.render.resolution_x = 1800; sc.render.resolution_y = 1200; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
    return "cameras: plan, wide, axon; engine " + sc.render.engine

def render(cam_name, filename):
    sc = bpy.context.scene; sc.camera = bpy.data.objects[cam_name]; sc.render.filepath = os.path.join(OUT_DIR, "frames", filename)
    bpy.ops.render.render(write_still=True); return "rendered " + sc.render.filepath

def export_glb(filename="east_village_pair.glb"):
    for o in bpy.data.objects: o.select_set(False)
    names = ["EV_MASSING", "SITE_178_FIRST_AVE", "SITE_115_AVENUE_A", "ROADBED", "SIDEWALK", "MEDIAN", "GROUND", "TREES"] + [o.name for o in bpy.data.objects if o.name.startswith("ST_")]
    for n in names:
        o = bpy.data.objects.get(n)
        if o: o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["EV_MASSING"]
    path = os.path.join(OUT_DIR, "assets", filename); os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6, export_apply=True, export_cameras=False, export_lights=False, export_yup=True)
    return "exported {} {:.0f} KB".format(path, os.path.getsize(path) / 1024)
