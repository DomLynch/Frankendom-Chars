from pathlib import Path
import bpy
import hashlib
import json
from mathutils import Vector
import sys

label = sys.argv[sys.argv.index("--") + 1]
OUT = Path("review") / label
OUT.mkdir(exist_ok=True, parents=True)
filename = f"witch-{label}.glb"
path = Path("models") / filename
receipts = []
sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(path))
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
for track in rig.animation_data.nla_tracks:
    track.mute = True
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.cycles.transparent_max_bounces = 64
scene.render.threads_mode = "FIXED"
scene.render.threads = 2
scene.render.resolution_x = 375
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new("Neutral studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
    0.18,
    0.18,
    0.18,
    1,
)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
target = Vector((0, 0, 1.03))
bpy.ops.object.camera_add(location=(0, -6, 1.1))
camera = bpy.context.object
camera.data.type = "ORTHO"
camera.data.ortho_scale = 2.55
scene.camera = camera
for xyz, power, size in [
    ((-3, -4, 5), 650, 3),
    ((3, -2, 3), 220, 3),
    ((1, 2, 4), 450, 2),
]:
    bpy.ops.object.light_add(type="AREA", location=xyz)
    light = bpy.context.object
    light.data.energy = power
    light.data.size = size
    light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
for view, clip, time in [
    ("front", "Trident_Idle", 0.35),
    ("back", "Trident_Idle", 0.35),
    ("side", "Trident_Idle", 0.35),
    ("attack", "Trident_High", 0.45),
    ("guard", "Trident_Guard", 0.4),
    ("kick", "Kick", 0.4),
    ("fight", "Trident_Idle", 0.35),
    ("head", "Trident_Idle", 0.35),
    ("high-rear", "Trident_Idle", 0.35),
]:
    action = bpy.data.actions.get(clip) or bpy.data.actions.get(
        clip.replace("Maul_", "")
    )
    assert action, clip
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(round(time * scene.render.fps))
    camera.location = (
        (6, 0, 1.1) if view == "side" else (0, 6 if view == "back" else -6, 1.1)
    )
    camera.rotation_euler = (
        (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.ortho_scale = 2.55
    if view == "head":
        focus = rig.matrix_world @ rig.pose.bones["Head"].matrix.translation
        focus.z += 0.10
        camera.location = (focus.x, -6, focus.z)
        camera.rotation_euler = (
            (focus - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.ortho_scale = 0.80
    elif view == "high-rear":
        camera.location = (2.8, 5, 3.2)
        camera.rotation_euler = (
            (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
    bpy.context.view_layer.update()
    projected_height = None
    if view == "fight":
        import numpy as np
        from bpy_extras.object_utils import world_to_camera_view

        points = []
        for armour in bpy.data.objects:
            if armour.type != "MESH" or not (
                armour.name.endswith("_Armour") or armour.name == "CreatureBody"
            ):
                continue
            evaluated = armour.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            visible = []
            for mat in mesh.materials:
                bsdf = next(
                    (n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"),
                    None,
                )
                visible.append(bsdf is None or bsdf.inputs["Alpha"].default_value > 0)
            used = sorted(
                {
                    i
                    for poly in mesh.polygons
                    if visible[poly.material_index]
                    for i in poly.vertices
                }
            )
            coords = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
            mesh.vertices.foreach_get("co", coords)
            coords = coords.reshape(-1, 3)[used]
            transform = np.array(
                camera.matrix_world.inverted() @ evaluated.matrix_world
            )
            points.append(np.c_[coords, np.ones(len(coords))] @ transform.T)
            evaluated.to_mesh_clear()
        projected = np.concatenate(points)
        height = float(np.ptp(projected[:, 1]))
        camera.data.ortho_scale = height * 600 / 110
        bpy.context.view_layer.update()
        # Blender fits the orthographic scale to the longer portrait dimension.
        low = world_to_camera_view(
            scene,
            camera,
            camera.matrix_world @ Vector((0, float(projected[:, 1].min()), -6)),
        )
        high = world_to_camera_view(
            scene,
            camera,
            camera.matrix_world @ Vector((0, float(projected[:, 1].max()), -6)),
        )
        projected_height = abs(high.y - low.y) * 600
        assert abs(projected_height - 110) < 0.01, projected_height
    output = OUT / f"{label}-{view}.png"
    scene.render.filepath = str(output)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    receipts.append(
        {
            "model": filename,
            "sha256": sha,
            "image": output.name,
            "clip": clip,
            "frame": scene.frame_current,
            "camera": list(camera.location),
            "orthoScale": camera.data.ortho_scale,
            "viewport": [375, 600],
            "renderer": bpy.app.version_string,
            "engine": "Cycles CPU",
            "projectedArmourHeightPx": projected_height,
            "imageSha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "scope": "CPU studio render; not gameplay or physical phone performance",
        }
    )
    print("CAPTURED", output.name, flush=True)
(OUT / "render-receipt.json").write_text(json.dumps(receipts, indent=2))
