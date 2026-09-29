import bpy
import json

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(
    filepath="/Users/domininclynch/Desktop/Business/artifacts/plaguedoctor-ranks/models/plaguedoctor-L1.glb"
)
r = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
out = {}
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        out[o.name] = {
            "bounds": [
                [
                    min((o.matrix_world @ v.co)[i] for v in o.data.vertices),
                    max((o.matrix_world @ v.co)[i] for v in o.data.vertices),
                ]
                for i in range(3)
            ],
            "groups": [g.name for g in o.vertex_groups],
            "visible": not o.hide_render,
        }
print("BASE", json.dumps(out))
print(
    "BONES",
    [
        (b.name, tuple(b.head_local))
        for b in r.data.bones
        if b.name in ["Head", "pelvis", "upperarm_l", "lowerarm_l", "hand_l"]
    ],
)
