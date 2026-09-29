"""Seat a dark cloth inner cowl beneath the retained face and new outer hood."""

import sys
import numpy as np
from pack_preserved import read, worlds, write

g, raw = read(sys.argv[1])
b = bytearray(raw)
ni = next(i for i, n in enumerate(g["nodes"]) if n.get("name") == "CreatureBody")
matrix = worlds(g)[ni]
names = [g["nodes"][i]["name"] for i in g["skins"][0]["joints"]]
angles = np.linspace(0, np.pi * 2, 32, endpoint=False)
levels = [
    (1.39, 0.115, 0.115),
    (1.43, 0.10, 0.10),
    (1.47, 0.09, 0.085),
    (1.51, 0.075, 0.072),
    (1.535, 0.06, 0.06),
]
world = np.array(
    [
        [np.cos(a) * rx, y, -0.015 + np.sin(a) * rz]
        for y, rx, rz in levels
        for a in angles
    ]
)
p = (np.c_[world, np.ones(len(world))] @ np.linalg.inv(matrix).T)[:, :3].astype("<f4")
tri = []
for row in range(len(levels) - 1):
    for k in range(32):
        a = row * 32 + k
        c = row * 32 + (k + 1) % 32
        tri.extend([[a, c, c + 32], [a, c + 32, a + 32]])
tri = np.asarray(tri, dtype="<u4")
normal = np.zeros_like(p)
face_normal = np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]])
for k in range(3):
    np.add.at(normal, tri[:, k], face_normal)
normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
j = np.zeros((len(p), 4), dtype="<u2")
w = np.zeros((len(p), 4), dtype="<f4")
j[:, 0] = names.index("neck_01")
j[:, 1] = names.index("Head")
t = np.clip((world[:, 1] - 1.43) / 0.105, 0, 1)
w[:, 1] = t * 0.9
w[:, 0] = 1 - w[:, 1]
j[w == 0] = 0


def attribute(data, kind, component, target):
    b.extend(b"\0" * (-len(b) % 4))
    vi = len(g["bufferViews"])
    g["bufferViews"].append(
        {"buffer": 0, "byteOffset": len(b), "byteLength": data.nbytes, "target": target}
    )
    b.extend(data.tobytes())
    ai = len(g["accessors"])
    value = {
        "bufferView": vi,
        "componentType": component,
        "count": len(data),
        "type": kind,
    }
    if kind == "VEC3":
        value.update(min=data.min(0).tolist(), max=data.max(0).tolist())
    g["accessors"].append(value)
    return ai


attrs = {
    "POSITION": attribute(p, "VEC3", 5126, 34962),
    "NORMAL": attribute(normal, "VEC3", 5126, 34962),
    "JOINTS_0": attribute(j, "VEC4", 5123, 34962),
    "WEIGHTS_0": attribute(w, "VEC4", 5126, 34962),
}
indices = attribute(tri.reshape(-1), "SCALAR", 5125, 34963)
mi = len(g["materials"])
g["materials"].append(
    {
        "name": "Witch dark inner cowl",
        "doubleSided": True,
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.012, 0.014, 0.011, 1],
            "metallicFactor": 0,
            "roughnessFactor": 0.95,
        },
    }
)
prims = g["meshes"][g["nodes"][ni]["mesh"]]["primitives"]
prims[:] = [pr for pr in prims if not pr.get("extras", {}).get("witchNewCowl")]
prims.append(
    {
        "attributes": attrs,
        "indices": indices,
        "material": mi,
        "extras": {"witchNewCowl": True},
    }
)
write(sys.argv[2], g, b)
