"""Transfer donor hand influence onto the immutable source finger capsules."""

import sys
import numpy as np
from pack_preserved import arr, read, write

g, raw = read(sys.argv[1])
b = bytearray(raw)
n = next(n for n in g["nodes"] if n.get("name", "").endswith("_Armour"))
a = g["meshes"][n["mesh"]]["primitives"][0]["attributes"]
p = arr(g, raw, a["POSITION"]).copy()
w = arr(g, raw, a["WEIGHTS_0"]).copy()
j = arr(g, raw, a["JOINTS_0"]).copy()
skin = g["skins"][0]
names = [g["nodes"][i]["name"] for i in skin["joints"]]
bind = np.linalg.inv(
    arr(g, raw, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
)[:, :3, 3]
dense = np.zeros((len(p), len(names)), dtype=np.float32)
for k in range(4):
    np.add.at(dense, (np.arange(len(p)), j[:, k]), w[:, k])
for side in ["l", "r"]:
    hand = names.index("hand_" + side)
    weight = dense[:, hand].copy()
    use = weight > 0.02
    q = p[use]
    capsules = [(hand, hand, names.index("middle_01_" + side))]
    for finger in ["thumb", "index", "middle", "ring", "pinky"]:
        for k in range(1, 4):
            start = names.index(f"{finger}_{k:02d}_{side}")
            end = names.index(
                f"{finger}_{k + 1:02d}_{side}" if k < 3 else f"{finger}_04_leaf_{side}"
            )
            capsules.append((start, start, end))
    distances = []
    for _, start, end in capsules:
        v = bind[end] - bind[start]
        t = np.clip(((q - bind[start]) @ v) / np.dot(v, v), 0, 1)
        distances.append(np.linalg.norm(q - (bind[start] + t[:, None] * v), axis=1))
    ds = np.stack(distances, axis=1)
    scores = np.exp(-(ds - ds.min(1, keepdims=True)) / 0.007)
    scores /= scores.sum(1, keepdims=True)
    dense[use, hand] = 0
    for k, (joint, _, _) in enumerate(capsules):
        dense[use, joint] += weight[use] * scores[:, k]
order = np.argsort(dense, axis=1)[:, -4:]
values = np.take_along_axis(dense, order, axis=1)
values /= values.sum(1, keepdims=True)
order[values == 0] = 0
for key, data in [
    ("JOINTS_0", order.astype("<u2")),
    ("WEIGHTS_0", values.astype("<f4")),
]:
    b.extend(b"\0" * (-len(b) % 4))
    ac = g["accessors"][a[key]]
    ac["bufferView"] = len(g["bufferViews"])
    ac["byteOffset"] = 0
    ac["componentType"] = 5123 if key == "JOINTS_0" else 5126
    g["bufferViews"].append(
        {"buffer": 0, "byteOffset": len(b), "byteLength": data.nbytes, "target": 34962}
    )
    b.extend(data.tobytes())
write(sys.argv[2], g, b)
