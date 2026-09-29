"""Reimport final GLB for hash-linked views at shipped scale and hunch."""

import hashlib
import os
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

rank = os.environ.get("RANK", "L8")
path = Path(f"models/pitborn-{rank}.glb")
output = Path(f"previews/{rank}")
output.mkdir(parents=True, exist_ok=True)
model_hash = hashlib.sha256(path.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
for track in rig.animation_data.nla_tracks:
    track.mute = True
meshes = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    visible = any(
        not m.use_nodes
        or m.node_tree.nodes.get("Principled BSDF").inputs["Alpha"].default_value > 0
        for m in obj.data.materials
    )
    if visible:
        meshes.append(obj)
roots = [o for o in bpy.context.scene.objects if o.parent is None]
scale = bpy.data.objects.new("Review scale 1.13", None)
bpy.context.collection.objects.link(scale)
for obj in roots:
    obj.parent = scale
scale.scale = (1.13, 1.13, 1.13)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16
scene.render.threads_mode = "FIXED"
scene.render.threads = 8
scene.render.resolution_x = 375
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world = bpy.data.worlds.new("Neutral studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
    0.18,
    0.18,
    0.18,
    1,
)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
for xyz, power, size in [
    ((-3, -4, 5), 650, 3),
    ((3, -2, 3), 250, 3),
    ((1, 2, 4), 450, 2),
]:
    bpy.ops.object.light_add(type="AREA", location=xyz)
    lamp = bpy.context.object
    lamp.data.energy = power
    lamp.data.size = size
    lamp.rotation_euler = (
        (Vector((0, 0, 1.1)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
    )
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = "ORTHO"
scene.camera = camera
receipts = []
for view, clip, fraction in [
    ("front", "Armed", 0.35),
    ("back", "Armed", 0.35),
    ("left", "Armed", 0.35),
    ("right", "Armed", 0.35),
    ("head", "Armed", 0.35),
    ("attack", "Attack", 0.5),
    ("heavy", "Heavy", 0.5),
    ("guard", "Guard", 0.5),
    ("kick", "Kick", 0.5),
    ("fight", "Armed", 0.35),
]:
    action = bpy.data.actions.get(clip)
    assert action, clip
    rig.animation_data.action = action
    if action.slots:
        rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(
        round(
            action.frame_range[0]
            + fraction * (action.frame_range[1] - action.frame_range[0])
        )
    )
    for name, angle in [
        ("spine_02", 7),
        ("spine_03", 7),
        ("neck_01", -7),
        ("Head", -6),
    ]:
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        from mathutils import Quaternion

        bone.rotation_quaternion = bone.rotation_quaternion @ Quaternion(
            (1, 0, 0), math.radians(angle)
        )
    bpy.context.view_layer.update()
    points = []
    graph = bpy.context.evaluated_depsgraph_get()
    for obj in meshes:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        points.extend(evaluated.matrix_world @ v.co for v in mesh.vertices)
        evaluated.to_mesh_clear()
    p = np.array([list(v) for v in points])
    low, high = p.min(0), p.max(0)
    centre = Vector((low + high) / 2)
    direction = {
        "back": Vector((0, 6, 0)),
        "left": Vector((6, 0, 0)),
        "right": Vector((-6, 0, 0)),
    }.get(view, Vector((0, -6, 0)))
    camera.location = centre + direction
    camera.rotation_euler = (
        (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    bpy.context.view_layer.update()
    transform = np.array(camera.matrix_world.inverted())
    projected = np.c_[p, np.ones(len(p))] @ transform.T
    width, height = np.ptp(projected[:, :2], axis=0)
    camera.data.ortho_scale = max(height, width * 600 / 375) * 1.15
    measured = None
    if view == "head":
        focus = rig.matrix_world @ rig.pose.bones["Head"].matrix.translation
        focus.z += 0.08
        camera.location = focus + Vector((0, -6, 0))
        camera.rotation_euler = (
            (focus - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.ortho_scale = 0.7
    elif view == "fight":
        camera.data.ortho_scale = float(height * 600 / 110)
        measured = float(height / camera.data.ortho_scale * 600)
        assert abs(measured - 110) < 0.01
    target = output / f"{rank}-{view}.png"
    scene.render.filepath = str(target.resolve())
    bpy.ops.render.render(write_still=True)
    receipts.append(
        {
            "file": target.name,
            "image_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "model_sha256": model_hash,
            "clip": clip,
            "frame": scene.frame_current,
            "camera": list(camera.location),
            "ortho_scale": camera.data.ortho_scale,
            "figure_height_px": measured,
            "scale": 1.13,
            "hunch_degrees": {"spine_02": 7, "spine_03": 7, "neck_01": -7, "Head": -6},
        }
    )
(output / "render-receipts.json").write_text(json.dumps(receipts, indent=2))
