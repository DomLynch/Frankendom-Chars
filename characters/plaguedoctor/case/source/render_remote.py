"""Reimport exported GLBs and capture matched CPU studio views."""

import hashlib
import json
import os
import urllib.request
from pathlib import Path

import bpy
from mathutils import Vector
from huggingface_hub import HfApi, get_token, hf_hub_url

REPO = "Domlynch/frankendom-plaguedoctor-pilot-20260928"
OUT = Path("/tmp/plague-renders")
OUT.mkdir(exist_ok=True)
api = HfApi()
revision = api.repo_info(REPO, repo_type="dataset").sha
receipts = []
for label, filename in [("original", "original.glb"), ("L10", "proof-v2.glb")]:
    path = OUT / (label + ".glb")
    url = hf_hub_url(REPO, filename, repo_type="dataset", revision=revision)
    request = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + get_token()}
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        path.write_bytes(response.read())
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
    scene.cycles.samples = 12
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8
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
        light.rotation_euler = (
            (target - light.location).to_track_quat("-Z", "Y").to_euler()
        )
    for view, clip, time in [
        ("front", "Armed", 0.35),
        ("back", "Armed", 0.35),
        ("attack", "Heavy", 0.45),
        ("guard", "Guard", 0.4),
        ("kick", "Kick", 0.4),
        ("fight", "Armed", 0.35),
    ]:
        action = bpy.data.actions.get(clip)
        assert action, clip
        rig.animation_data.action = action
        if len(action.slots):
            rig.animation_data.action_slot = action.slots[0]
        scene.frame_set(round(time * scene.render.fps))
        camera.location = (0, 6 if view == "back" else -6, 1.1)
        camera.rotation_euler = (
            (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.ortho_scale = 11.2 if view == "fight" else 2.55
        output = OUT / f"{label}-{view}.png"
        scene.render.filepath = str(output)
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
        api.upload_file(
            path_or_fileobj=str(output),
            path_in_repo="proof-v2/renders/" + output.name,
            repo_id=REPO,
            repo_type="dataset",
        )
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
                "scope": "CPU studio render; not gameplay or physical phone performance",
            }
        )
        print("CAPTURED", output.name, flush=True)
(OUT / "render-receipt.json").write_text(json.dumps(receipts, indent=2))
api.upload_file(
    path_or_fileobj=str(OUT / "render-receipt.json"),
    path_in_repo="proof-v2/render-receipt.json",
    repo_id=REPO,
    repo_type="dataset",
)
print("RENDER_COMPLETE", flush=True)
os._exit(0)
