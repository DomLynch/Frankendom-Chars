"""Lower-rank assembly: remove donor head and retain the exact original face."""

import copy
import json
import sys
from pathlib import Path

import numpy as np

from pack_preserved import arr, read, worlds, write

source, destination = sys.argv[1:3]
original, original_binary = read("source/pitborn.glb")
g, binary = read(source)
out = bytearray(binary)
original_world = worlds(original)
names = {n.get("name"): i for i, n in enumerate(g["nodes"])}
armour = g["nodes"][
    next(i for i, n in enumerate(g["nodes"]) if n.get("name", "").endswith("_Armour"))
]
source_world = original_world[names["Skin"]]


def replace_indices(primitive, indices):
    payload = np.asarray(indices, dtype="<u4").tobytes()
    out.extend(b"\0" * (-len(out) % 4))
    view = len(g["bufferViews"])
    g["bufferViews"].append(
        {
            "buffer": 0,
            "byteOffset": len(out),
            "byteLength": len(payload),
            "target": 34963,
        }
    )
    out.extend(payload)
    accessor = len(g["accessors"])
    g["accessors"].append(
        {
            "bufferView": view,
            "componentType": 5125,
            "count": indices.size,
            "type": "SCALAR",
        }
    )
    primitive["indices"] = accessor


removed = 0
for primitive in g["meshes"][armour["mesh"]]["primitives"]:
    p = arr(g, binary, primitive["attributes"]["POSITION"])
    world = (np.c_[p, np.ones(len(p))] @ source_world.T)[:, :3]
    triangles = arr(g, binary, primitive["indices"]).reshape(-1, 3)
    keep = (
        world[
            triangles,
            :,
        ][..., 1].max(1)
        < 1.72
    )
    removed += int((~keep).sum())
    replace_indices(primitive, triangles[keep])

retained = ["Face", "Photo", "PhotoEyes", "PhotoTeeth", "Bone"]
for name in retained:
    index = names[name]
    mesh = g["meshes"][g["nodes"][index]["mesh"]]
    old_mesh = original["meshes"][original["nodes"][index]["mesh"]]
    for primitive, old in zip(mesh["primitives"], old_mesh["primitives"]):
        primitive["material"] = old["material"]

# Keep only the original cap/headband from slots that also contain lower kit.
for name in ["Steel", "Wrap"]:
    index = names[name]
    old_node = original["nodes"][index]
    mesh = copy.deepcopy(original["meshes"][old_node["mesh"]])
    kept = []
    for primitive in mesh["primitives"]:
        p = arr(original, original_binary, primitive["attributes"]["POSITION"])
        world = (np.c_[p, np.ones(len(p))] @ original_world[index].T)[:, :3]
        triangles = arr(original, original_binary, primitive["indices"]).reshape(-1, 3)
        keep = world[triangles][..., 1].min(1) > 1.80
        if not keep.any():
            continue
        replace_indices(primitive, triangles[keep])
        kept.append(primitive)
    if not kept:
        continue
    mesh["primitives"] = kept
    mesh_index = len(g["meshes"])
    g["meshes"].append(mesh)
    node = {
        "name": "OriginalHead_" + name,
        "mesh": mesh_index,
        "skin": old_node["skin"],
        "matrix": original_world[index].T.flatten().tolist(),
    }
    g["scenes"][g.get("scene", 0)]["nodes"].append(len(g["nodes"]))
    g["nodes"].append(node)

assert g["nodes"][: len(original["nodes"])] == original["nodes"]
assert bytes(out[: len(original_binary)]) == original_binary
write(destination, g, out)
Path(destination + ".face.json").write_text(
    json.dumps(
        {
            "originalNodesRetained": retained,
            "donorHeadTrianglesRemoved": removed,
            "status": "requires exported head/front/back/pose inspection",
        },
        indent=2,
    )
)
