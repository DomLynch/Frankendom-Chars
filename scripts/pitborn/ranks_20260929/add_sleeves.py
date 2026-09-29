"""Fit local dark under-sleeves to original bind-arm dimensions and joints."""

import sys
import json
import numpy as np
from pack_preserved import read, worlds, write

src, dst = sys.argv[1:3]
g, binary = read(src)
original, _ = read("source/pitborn.glb")
out = bytearray(binary)
idx = next(i for i, n in enumerate(original["nodes"]) if n.get("name") == "Skin")
node = original["nodes"][idx]
skin = original["skins"][node["skin"]]
names = {original["nodes"][j]["name"]: k for k, j in enumerate(skin["joints"])}
transform = worlds(original)[idx]
positions = []
normals = []
joints = []
weights = []
triangles = []
for sign, side in [(1, "l"), (-1, "r")]:
    start = len(positions)
    for i, x in enumerate(np.linspace(0.185, 0.70, 16)):
        radius = float(
            np.interp(x, [0.185, 0.25, 0.47, 0.70], [0.072, 0.082, 0.064, 0.050])
        )
        blend = float(np.clip((x - 0.39) / 0.16, 0, 1))
        blend = blend * blend * (3 - 2 * blend)
        for j in range(20):
            a = j * 2 * np.pi / 20
            positions.append(
                [sign * x, 1.62 + radius * np.cos(a), -0.075 + radius * np.sin(a)]
            )
            normals.append([0, np.cos(a), np.sin(a)])
            joints.append([names["upperarm_" + side], names["lowerarm_" + side], 0, 0])
            weights.append([1 - blend, blend, 0, 0])
            if i:
                p = start + i * 20 + j
                q = start + i * 20 + (j + 1) % 20
                triangles.extend([[p - 20, q - 20, q], [p - 20, q, p]])
pos = (np.c_[positions, np.ones(len(positions))] @ np.linalg.inv(transform).T)[:, :3]


def accessor(data, kind, component, target):
    data = np.asarray(data, dtype={5126: "<f4", 5123: "<u2", 5125: "<u4"}[component])
    out.extend(b"\0" * (-len(out) % 4))
    vi = len(g["bufferViews"])
    g["bufferViews"].append(
        {
            "buffer": 0,
            "byteOffset": len(out),
            "byteLength": data.nbytes,
            "target": target,
        }
    )
    out.extend(data.tobytes())
    ai = len(g["accessors"])
    a = {"bufferView": vi, "componentType": component, "count": len(data), "type": kind}
    if kind == "VEC3":
        a["min"] = data.min(0).tolist()
        a["max"] = data.max(0).tolist()
    g["accessors"].append(a)
    return ai


attrs = {
    key: accessor(data, kind, component, 34962)
    for key, data, kind, component in [
        ("POSITION", pos, "VEC3", 5126),
        ("NORMAL", normals, "VEC3", 5126),
        ("JOINTS_0", joints, "VEC4", 5123),
        ("WEIGHTS_0", weights, "VEC4", 5126),
    ]
}
mi = len(g["materials"])
g["materials"].append(
    {
        "name": "Fitted dark leather joint sleeves",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.025, 0.018, 0.012, 1],
            "metallicFactor": 0,
            "roughnessFactor": 0.9,
        },
        "doubleSided": True,
    }
)
mesh = len(g["meshes"])
g["meshes"].append(
    {
        "primitives": [
            {
                "attributes": attrs,
                "indices": accessor(
                    np.asarray(triangles).ravel(), "SCALAR", 5125, 34963
                ),
                "material": mi,
            }
        ]
    }
)
ni = len(g["nodes"])
g["nodes"].append(
    {
        "name": "Fitted joint sleeves",
        "mesh": mesh,
        "skin": node["skin"],
        "matrix": transform.T.flatten().tolist(),
    }
)
g["scenes"][g.get("scene", 0)]["nodes"].append(ni)
write(dst, g, out)
print(json.dumps({"sleeveTriangles": len(triangles)}))
