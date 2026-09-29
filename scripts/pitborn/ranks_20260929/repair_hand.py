"""Stabilize reconstructed right-hand surfaces; blend at the wrist, preserve rig."""

import sys
import numpy as np
from pack_preserved import read, arr, write

src, dst = sys.argv[1:3]
g, b = read(src)
n = next(n for n in g["nodes"] if n.get("name", "").endswith("_Armour"))
a = g["meshes"][n["mesh"]]["primitives"][0]["attributes"]
p = arr(g, b, a["POSITION"])
j = arr(g, b, a["JOINTS_0"]).copy()
w = arr(g, b, a["WEIGHTS_0"]).copy()
skin = g["skins"][n["skin"]]
hand = next(
    k for k, i in enumerate(skin["joints"]) if g["nodes"][i]["name"] == "hand_r"
)
selected = np.flatnonzero(p[:, 0] < -0.67)
for i in selected:
    t = float(np.clip((-p[i, 0] - 0.67) / 0.065, 0, 1))
    t = t * t * (3 - 2 * t)
    d = {int(k): float(v) * (1 - t) for k, v in zip(j[i], w[i])}
    d[hand] = d.get(hand, 0) + t
    best = sorted(d.items(), key=lambda x: x[1], reverse=True)[:4]
    while len(best) < 4:
        best.append((0, 0))
    j[i] = [x[0] for x in best]
    w[i] = [x[1] for x in best]
    w[i] /= w[i].sum()
out = bytearray(b)
for key, data, component in [
    ("JOINTS_0", j.astype("<u2"), 5123),
    ("WEIGHTS_0", w.astype("<f4"), 5126),
]:
    out.extend(b"\0" * (-len(out) % 4))
    vi = len(g["bufferViews"])
    g["bufferViews"].append(
        {
            "buffer": 0,
            "byteOffset": len(out),
            "byteLength": data.nbytes,
            "target": 34962,
        }
    )
    out.extend(data.tobytes())
    g["accessors"][a[key]].update(bufferView=vi, byteOffset=0, componentType=component)
write(dst, g, out)
print("stabilized hand vertices", len(selected))
