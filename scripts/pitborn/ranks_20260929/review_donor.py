"""Inspect the saved donor in Blender; render its actual exported surfaces."""

import hashlib
import json
from pathlib import Path

import bpy
import numpy as np
from huggingface_hub import HfApi, hf_hub_download
from mathutils import Vector

REPO = "Domlynch/frankendom-pitborn-ranks-20260929"
api = HfApi()
root = Path("/tmp/pitborn-review")
root.mkdir(exist_ok=True)
path = Path(hf_hub_download(REPO, "donors/L8.glb", repo_type="dataset"))
model_hash = hashlib.sha256(path.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(path))
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
pts = np.array([list(o.matrix_world @ v.co) for o in meshes for v in o.data.vertices])
low, high = pts.min(0), pts.max(0)
height = float(high[2] - low[2])
center = Vector((low + high) / 2)
receipt = {
    "model_sha256": model_hash,
    "bounds": [low.tolist(), high.tolist()],
    "meshes": [o.name for o in meshes],
    "vertices": len(pts),
    "triangles": sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons),
    "blender": bpy.app.version_string,
    "captures": [],
}
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 12
scene.render.threads_mode = "FIXED"
scene.render.threads = 8
scene.render.resolution_x = 512
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world = bpy.data.worlds.new("Neutral studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
    0.16,
    0.16,
    0.16,
    1,
)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
for pos, power in [((-2, -3, 3), 170), ((2, -2, 2), 80), ((1, 3, 3), 130)]:
    bpy.ops.object.light_add(type="AREA", location=center + Vector(pos) * height)
    light = bpy.context.object
    light.data.energy = power * height * height
    light.data.size = 1.5 * height
    light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = "ORTHO"
camera.data.ortho_scale = max(height, float(high[0] - low[0]) * 768 / 512) * 1.12
scene.camera = camera
for name, pos in [
    ("front", (0, -3, 0)),
    ("back", (0, 3, 0)),
    ("left", (3, 0, 0)),
    ("right", (-3, 0, 0)),
]:
    camera.location = center + Vector(pos) * height
    camera.rotation_euler = (
        (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    output = root / f"L8-donor-{name}.png"
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    receipt["captures"].append(
        {
            "file": output.name,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "camera": list(camera.location),
        }
    )
(root / "L8-donor-review.json").write_text(json.dumps(receipt, indent=2))
api.upload_folder(
    repo_id=REPO, repo_type="dataset", folder_path=root, path_in_repo="previews/donor"
)
print("DONOR_REVIEW_SAVED", json.dumps(receipt), flush=True)
