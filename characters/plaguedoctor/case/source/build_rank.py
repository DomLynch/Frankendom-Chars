"""Remote first fit: saved donor, preserved original rig and vertex weights."""

from pathlib import Path
import bpy
import hashlib
import json
import os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from huggingface_hub import HfApi, hf_hub_download

REPO = "Domlynch/frankendom-plaguedoctor-pilot-20260928"
R = Path("/tmp/plague")
R.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(
    filepath=hf_hub_download(REPO, "original.glb", repo_type="dataset")
)
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
original = [o for o in bpy.context.scene.objects if o.type == "MESH"]
body = bpy.data.objects["CreatureBody"]


def sig(o):
    return hashlib.sha256(
        repr(
            [
                (tuple(v.co), [(g.group, g.weight) for g in v.groups])
                for v in o.data.vertices
            ]
        ).encode()
    ).hexdigest()


before = {o.name: sig(o) for o in original}
body.data.calc_loop_triangles()
pts = [body.matrix_world @ v.co for v in body.data.vertices]
faces = [tuple(f.vertices) for f in body.data.loop_triangles]
bvh = BVHTree.FromPolygons(pts, faces, all_triangles=True)
source_groups = {g.index: g.name for g in body.vertex_groups}
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(
    filepath=hf_hub_download(REPO, "L10-donor.glb", repo_type="dataset")
)
donor = next(
    o for o in bpy.context.scene.objects if o not in existing and o.type == "MESH"
)
scale = 2.03
zmin = min((donor.matrix_world @ v.co).z for v in donor.data.vertices)
for v in donor.data.vertices:
    p = donor.matrix_world @ v.co
    v.co = Vector((p.x * scale, p.y * scale, (p.z - zmin) * scale + 0.026))
donor.matrix_world.identity()
donor.name = "L10_Armour"
for v in donor.data.vertices:
    hit = bvh.find_nearest(v.co)
    ids = faces[hit[2]]
    a, b, c = [pts[i] for i in ids]
    e0 = b - a
    e1 = c - a
    e2 = hit[0] - a
    d00 = e0.dot(e0)
    d01 = e0.dot(e1)
    d11 = e1.dot(e1)
    d20 = e2.dot(e0)
    d21 = e2.dot(e1)
    den = d00 * d11 - d01 * d01
    u = (d11 * d20 - d01 * d21) / den if abs(den) > 1e-12 else 0
    w = (d00 * d21 - d01 * d20) / den if abs(den) > 1e-12 else 0
    weights = {}
    for idx, factor in zip(ids, [max(0, 1 - u - w), max(0, u), max(0, w)]):
        for g in body.data.vertices[idx].groups:
            name = source_groups[g.group]
            weights[name] = weights.get(name, 0) + g.weight * factor
    t = max(0, min(1, (v.co.z - 1.53) / 0.10)) if abs(v.co.x) < 0.22 else 0
    t = t * t * (3 - 2 * t)
    weights = {n: w * (1 - t) for n, w in weights.items()}
    weights["Head"] = weights.get("Head", 0) + t
    weights = dict(sorted(weights.items(), key=lambda q: q[1], reverse=True)[:4])
    total = sum(weights.values())
    assert total > 0
    for n, w in weights.items():
        if w > 0:
            (donor.vertex_groups.get(n) or donor.vertex_groups.new(name=n)).add(
                [v.index], w / total, "REPLACE"
            )
mod = donor.modifiers.new("Preserved original rig", "ARMATURE")
mod.object = rig
mw = donor.matrix_world.copy()
donor.parent = rig
donor.matrix_world = mw
hidden = bpy.data.materials.new("Original preserved beneath L10")
hidden.use_nodes = True
hidden.node_tree.nodes.get("Principled BSDF").inputs["Alpha"].default_value = 0
hidden.surface_render_method = "DITHERED"
body.data.materials.clear()
body.data.materials.append(hidden)
assert all(before[o.name] == sig(o) for o in original)
for m in donor.data.materials:
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Emission Strength"].default_value = 0
bpy.ops.wm.save_as_mainfile(filepath=str(R / "plaguedoctor-L10.blend"))
bpy.ops.export_scene.gltf(
    filepath=str(R / "plaguedoctor-L10.glb"),
    export_format="GLB",
    use_visible=True,
    export_animations=True,
    export_tangents=True,
)
(R / "L10-build.json").write_text(
    json.dumps(
        {
            "donorScale": scale,
            "originalSignatures": before,
            "retainedVerticesWeightsUnchanged": True,
            "donorTriangles": sum(len(f.vertices) - 2 for f in donor.data.polygons),
            "visibleBodyPolicy": "Complete original face/body geometry and weights retained, hidden beneath reconstructed armour; original rig and weapons retained.",
            "scope": "First fit; visual and motion review required.",
        },
        indent=2,
    )
)
api = HfApi()
for name in ["plaguedoctor-L10.blend", "plaguedoctor-L10.glb", "L10-build.json"]:
    api.upload_file(
        path_or_fileobj=str(R / name),
        path_in_repo="proof-v1/" + name,
        repo_id=REPO,
        repo_type="dataset",
    )
print("L10_EXPORTED_AND_PERSISTED", flush=True)
os._exit(0)
