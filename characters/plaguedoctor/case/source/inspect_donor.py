import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(
    filepath="/Users/domininclynch/Desktop/Business/artifacts/plaguedoctor-ranks/models/plaguedoctor-Donor.glb"
)
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        print(
            "DONOR",
            o.name,
            len(o.data.vertices),
            [
                [
                    min((o.matrix_world @ v.co)[i] for v in o.data.vertices),
                    max((o.matrix_world @ v.co)[i] for v in o.data.vertices),
                ]
                for i in range(3)
            ],
        )
