"""Reimport exported GLBs and capture matched CPU studio views."""

import hashlib
import json
import argparse
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


ROOT = Path("/Users/domininclynch/Desktop/Business/artifacts/dwarf-ranks-20260928")
parser = argparse.ArgumentParser()
parser.add_argument('--ranks', nargs='+', default=['L8'])
parser.add_argument('--folder')
parser.add_argument('--out', default='renders')
parser.add_argument('--views', nargs='+')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT = ROOT / 'elite-correction' / args.out
OUT.mkdir(exist_ok=True)
receipts = []

runtime = {
    "blender": bpy.app.version_string,
    "device": "CPU",
    "threads": 2,
    "cyclesSamples": 32,
}
(OUT / "runtime.json").write_text(json.dumps(runtime, indent=2))
for label in args.ranks:
    filename = "elite-correction/" + (args.folder or label) + "/dwarf-" + label + ".glb"
    path = ROOT / filename
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
    scene.cycles.samples = 32
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
    target = Vector((0, 0, 0.75))
    bpy.ops.object.camera_add(location=(0, -6, 1.1))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.95
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
        ("rest", None, 0),
        ("front", "Warhammer_Idle", 0.35),
        ("side", "Warhammer_Idle", 0.35),
        ("back", "Warhammer_Idle", 0.35),
        ("attack", "Warhammer_Heavy", 0.45),
        ("guard", "Warhammer_Guard", 0.4),
        ("kick", "Kick", 0.4),
        ("fight", "Warhammer_Idle", 0.35),
        ("heavy-start", "Warhammer_Heavy", 0.25),
        ("guard-deep", "Warhammer_Guard", 0.5),
        ("closeup", "Warhammer_Idle", 0.35),
    ]:
        if args.views and view not in args.views:
            continue
        action = bpy.data.actions.get(clip) if clip else None
        assert action or clip is None, clip
        rig.animation_data.action = action
        if action and len(action.slots):
            rig.animation_data.action_slot = action.slots[0]
        scene.frame_set(round(time * scene.render.fps))
        camera.location = (
            (6, 0, 0.9) if view == "side" else (0, 6 if view == "back" else -6, 0.9)
        )
        camera.rotation_euler = (
            (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.ortho_scale = 8.2 if view == "fight" else 1.95
        if view == 'closeup':
            scene.render.resolution_x = 750
            scene.render.resolution_y = 900
            camera.data.ortho_scale = .95
            camera.location = (0,-6,1.25)
            camera.rotation_euler = ((Vector((0,0,1.06))-camera.location).to_track_quat('-Z','Y').to_euler())
        output = OUT / f"{label}-{view}.png"
        scene.render.filepath = str(output)
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
        deps = bpy.context.evaluated_depsgraph_get()
        projected = []
        for o in scene.objects:
            if o.type == "MESH" and (
                o.name.startswith(label + "_") or o.name == "CreatureBody"
            ):
                evaluated = o.evaluated_get(deps)
                projected.extend(
                    world_to_camera_view(
                        scene, camera, evaluated.matrix_world @ Vector(c)
                    ).y
                    * scene.render.resolution_y
                    for c in evaluated.bound_box
                )
        figure_height = max(projected) - min(projected)
        receipts.append(
            {
                "model": filename,
                "sha256": sha,
                "image": output.name,
                "clip": clip,
                "frame": scene.frame_current,
                "camera": list(camera.location),
                "orthoScale": camera.data.ortho_scale,
                "viewport": [scene.render.resolution_x, scene.render.resolution_y],
                "figureHeightPx": figure_height,
                "scope": "CPU studio render; not gameplay or physical phone performance",
            }
        )
        (OUT / "render-receipt.json").write_text(json.dumps(receipts, indent=2))
        print("CAPTURED", output.name, flush=True)
(OUT / "render-receipt.json").write_text(json.dumps(receipts, indent=2))
print("RENDER_COMPLETE", flush=True)
