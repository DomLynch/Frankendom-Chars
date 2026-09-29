import hashlib, json, math, os
from pathlib import Path

import bpy
import numpy as np
import requests
from mathutils import Vector

PIT_URL = "https://raw.githubusercontent.com/DomLynch/RPG-game/codex/01a09a76/task-1/src/assets/pitborn.glb"
OUT = Path("/tmp/pitborn-L8-donor.glb")
REPORT = Path("/tmp/pitborn-L8-donor.json")

def download(url, path):
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    Path(path).write_bytes(r.content)

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

pit = Path("/tmp/pitborn.glb")
donor = Path(os.environ["PITBORN_L8_DONOR"])
download(PIT_URL, pit)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(pit))
pit_objs = set(bpy.context.scene.objects)
pit_rig = max((o for o in pit_objs if o.type == "ARMATURE"), key=lambda o: len(o.data.bones))
pit_rig.data.pose_position = "REST"
if pit_rig.animation_data:
    pit_rig.animation_data.action = None
    for track in pit_rig.animation_data.nla_tracks:
        track.mute = True

bpy.ops.import_scene.gltf(filepath=str(donor))
new = [o for o in bpy.context.scene.objects if o not in pit_objs]
donor_rig = max((o for o in new if o.type == "ARMATURE"), key=lambda o: len(o.data.bones))
donor_rig.data.pose_position = "REST"
donor_meshes = [o for o in new if o.type == "MESH" and o.name.startswith("L8_")]
if not donor_meshes:
    raise RuntimeError("No L8 donor armour meshes")

names = ["pelvis", "spine_03", "Head", "hand_l", "hand_r", "foot_l", "foot_r"]
pairs = []
for name in names:
    pb = pit_rig.data.bones.get(name)
    db = donor_rig.data.bones.get(name)
    if pb and db:
        pairs.append((pit_rig.matrix_world @ pb.head_local, donor_rig.matrix_world @ db.head_local))
if len(pairs) < 4:
    raise RuntimeError("Insufficient shared rig landmarks")

P = np.array([list(p) for p, _ in pairs])
D = np.array([list(d) for _, d in pairs])
pc, dc = P[0], D[0]
ratios = []
for p, d in zip(P[1:], D[1:]):
    nd = np.linalg.norm(d - dc)
    npit = np.linalg.norm(p - pc)
    if nd > 1e-6:
        ratios.append(npit / nd)
scale = float(np.median(ratios))
translation = Vector(pc) - Vector(dc) * scale

shared = {b.name for b in pit_rig.data.bones} & {b.name for b in donor_rig.data.bones}
for o in donor_meshes:
    mw = o.matrix_world.copy()
    mw.translation = mw.translation * scale + translation
    for r in range(3):
        for col in range(3):
            mw[r][col] *= scale
    o.matrix_world = mw
    for m in list(o.modifiers):
        if m.type == "ARMATURE":
            m.object = pit_rig
    if not any(m.type == "ARMATURE" for m in o.modifiers):
        m = o.modifiers.new("Pitborn preserved rig", "ARMATURE")
        m.object = pit_rig
    keep = o.matrix_world.copy()
    o.parent = pit_rig
    o.matrix_world = keep
    o["frankendom_character"] = "pitborn"
    o["frankendom_rank"] = 8
    missing = [g.name for g in o.vertex_groups if g.name not in shared]
    if missing:
        raise RuntimeError(f"{o.name} missing bones {missing[:10]}")

for o in list(new):
    if o == donor_rig or (o.type == "MESH" and o not in donor_meshes):
        bpy.data.objects.remove(o, do_unlink=True)

for o in pit_objs:
    if o.type == "MESH" and o.name and any(k in o.name.lower() for k in ["helmet", "cap"]):
        o.hide_render = True

bone_mat = bpy.data.materials.get("BoneWorn") or bpy.data.materials.get("Bone")
if bone_mat is None:
    bone_mat = bpy.data.materials.new("Pitborn old bone")
    bone_mat.diffuse_color = (0.26, 0.20, 0.12, 1)
    bone_mat.use_nodes = True
    bs = bone_mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (0.26, 0.20, 0.12, 1)
    bs.inputs["Roughness"].default_value = 0.78

def bone_world(name, t=0.5):
    b = pit_rig.data.bones[name]
    return (pit_rig.matrix_world @ b.head_local).lerp(pit_rig.matrix_world @ b.tail_local, t)

def parent_bone(obj, bone):
    world = obj.matrix_world.copy()
    obj.parent = pit_rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["frankendom_character"] = "pitborn"
    obj["frankendom_rank"] = 8

for i, (x, ang) in enumerate([(-0.14, -18), (0.15, 22)]):
    c = bone_world("spine_03", 0.55) + Vector((x, -0.20, -0.05))
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.025, radius2=0.008, depth=0.16,
                                   location=c, rotation=(math.radians(90), math.radians(ang), 0))
    o = bpy.context.object
    o.name = f"L8_PitbornBoneTrophy_{i}"
    o.data.materials.append(bone_mat)
    parent_bone(o, "spine_03")

c = bone_world("clavicle_l", 0.7) + Vector((0.11, -0.02, 0.06))
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.035, radius2=0.004, depth=0.20,
                               location=c, rotation=(0, math.radians(70), 0))
sp = bpy.context.object
sp.name = "L8_PitbornLeftPauldronTooth"
sp.data.materials.append(bone_mat)
parent_bone(sp, "clavicle_l")

pit_rig.data.pose_position = "POSE"
if pit_rig.animation_data:
    for track in pit_rig.animation_data.nla_tracks:
        track.mute = False
idle = bpy.data.actions.get("Armed") or bpy.data.actions.get("Idle")
if idle:
    if not pit_rig.animation_data:
        pit_rig.animation_data_create()
    pit_rig.animation_data.action = idle
    bpy.context.scene.frame_set(int(idle.frame_range[0]))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False,
                          export_animations=True, export_skins=True, export_materials="EXPORT")

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo + hi) * 0.5
H = hi.z - lo.z

world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.08, 0.08, 0.09, 1)
bg.inputs["Strength"].default_value = 0.6

def look(o, target):
    o.rotation_euler = (target - o.location).to_track_quat("-Z", "Y").to_euler()

def area(name, pos, energy, size):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.shape = "DISK"
    d.size = size
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = pos
    look(o, center)

area("Key", center + Vector((2 * H, -2.5 * H, 1.8 * H)), 1800, 1.7 * H)
area("Fill", center + Vector((-2 * H, -1.2 * H, 1.0 * H)), 900, 1.4 * H)
area("Rim", center + Vector((0, 2.4 * H, 1.7 * H)), 1500, 1.3 * H)

camd = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", camd)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
camd.lens = 58
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 850
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

for name, off in [
    ("front", Vector((0, -2.4 * H, 0.05 * H))),
    ("right", Vector((-2.4 * H, 0, 0.05 * H))),
    ("back", Vector((0, 2.4 * H, 0.05 * H))),
    ("left", Vector((2.4 * H, 0, 0.05 * H))),
]:
    cam.location = center + off
    look(cam, center + Vector((0, 0, 0.03 * H)))
    p = Path(f"/tmp/pitborn-L8-donor-{name}.png")
    scene.render.filepath = str(p)
    bpy.ops.render.render(write_still=True)

payload = {
    "source_pitborn_sha256": sha(pit),
    "source_donor_sha256": sha(donor),
    "output_sha256": sha(OUT),
    "output_bytes": OUT.stat().st_size,
    "pitborn_bones": len(pit_rig.data.bones),
    "donor_draws": [o.name for o in donor_meshes],
    "fit_scale": scale,
    "action_count": len(bpy.data.actions),
}
REPORT.write_text(json.dumps(payload, indent=2))
print(json.dumps(payload), flush=True)
