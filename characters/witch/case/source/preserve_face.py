"""Retain the source Witch face without the old outer hood."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
from pack_preserved import arr, read, worlds, write

source, dest = sys.argv[1:3]
original, ob = read("source/original.glb")
g, raw = read(source)
b = bytearray(raw)
wi = worlds(g)
body_i = next(i for i, n in enumerate(g["nodes"]) if n.get("name") == "CreatureBody")
body = g["nodes"][body_i]
old = original["meshes"][body["mesh"]]["primitives"][0]


def indices(data):
    data = np.asarray(data, dtype="<u4").reshape(-1)
    b.extend(b"\0" * (-len(b) % 4))
    vi = len(g["bufferViews"])
    g["bufferViews"].append(
        {"buffer": 0, "byteOffset": len(b), "byteLength": data.nbytes, "target": 34963}
    )
    b.extend(data.tobytes())
    ai = len(g["accessors"])
    g["accessors"].append(
        {"bufferView": vi, "componentType": 5125, "count": len(data), "type": "SCALAR"}
    )
    return ai


p = arr(original, ob, old["attributes"]["POSITION"])
q = (np.c_[p, np.ones(len(p))] @ wi[body_i].T)[:, :3]
tri = arr(original, ob, old["indices"]).reshape(-1, 3)
# Keep the approved face and its immediate inner framing, not the old outer hood.
# The new rank hood and overlapping inner cowl supply the surrounding surfaces.
c = q[tri].mean(1)
keep = (
    (c[:, 1] > 1.52)
    & (c[:, 1] < 1.66)
    & (np.abs(c[:, 0]) < 0.06)
    & (c[:, 2] > 0.005)
)
face = copy.deepcopy(old)
face["indices"] = indices(tri[keep])
# Keep the retained head on its exact original mesh node and parent hierarchy.
g["meshes"][body["mesh"]]["primitives"] = [
    g["meshes"][body["mesh"]]["primitives"][0],
    face,
]
old_face_nodes = {
    i for i, n in enumerate(g["nodes"]) if n.get("name") == "Witch_OriginalFace"
}
for scene in g["scenes"]:
    scene["nodes"] = [i for i in scene["nodes"] if i not in old_face_nodes]
for index in sorted(old_face_nodes, reverse=True):
    if index == len(g["nodes"]) - 1:
        old_mesh = g["nodes"].pop()["mesh"]
        if old_mesh == len(g["meshes"]) - 1:
            g["meshes"].pop()
removed = 0
for i, node in enumerate(g["nodes"]):
    if not node.get("name", "").endswith("_Armour"):
        continue
    for prim in g["meshes"][node["mesh"]]["primitives"]:
        p = arr(g, b, prim["attributes"]["POSITION"]).copy()
        q = (np.c_[p, np.ones(len(p))] @ wi[i].T)[:, :3]
        tri = arr(g, b, prim["indices"]).reshape(-1, 3).copy()
        c = q[tri].mean(1)
        cut = ((c[:, 0] / 0.065) ** 2 + ((c[:, 1] - 1.59) / 0.08) ** 2 < 1) & (
            c[:, 2] > 0.015
        )
        removed += int(cut.sum())
        prim["indices"] = indices(tri[~cut])
write(dest, g, b)
Path(dest + ".face.json").write_text(
    json.dumps(
        {
            "sourceTrianglesRetained": int(keep.sum()),
            "donorFaceTrianglesRemoved": removed,
            "originalFaceAttributesAndWeightsExact": True,
        },
        indent=2,
    )
)
