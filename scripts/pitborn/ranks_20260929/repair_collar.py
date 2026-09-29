"""Restore donor shoulder plates mistakenly removed by a global head-height cut."""

import sys
import numpy as np
from pack_preserved import read, arr, worlds, write

src, dst = sys.argv[1:3]
g, b = read(src)
o, _ = read("source/pitborn.glb")
ni = next(i for i, n in enumerate(g["nodes"]) if n.get("name", "").endswith("_Armour"))
p = g["meshes"][g["nodes"][ni]["mesh"]]["primitives"][0]
v = arr(g, b, p["attributes"]["POSITION"])
w = (np.c_[v, np.ones(len(v))] @ worlds(g)[ni].T)[:, :3]
ai = next(
    i
    for i in range(len(o["accessors"]), len(g["accessors"]))
    if g["accessors"][i]["type"] == "SCALAR"
    and g["accessors"][i]["componentType"] in [5123, 5125]
    and g["bufferViews"][g["accessors"][i]["bufferView"]].get("target") == 34963
)
t = arr(g, b, ai).reshape(-1, 3)
q = w[t]
# Keep shoulder geometry outside the head region; remove the complete donor head.
head = (q[..., 1].max(1) > 1.72) & (
    (abs(q[..., 0]).min(1) < 0.15) | (q[..., 1].max(1) > 1.82)
)
t = t[~head].astype("<u4")
out = bytearray(b)
out.extend(b"\0" * (-len(out) % 4))
vi = len(g["bufferViews"])
g["bufferViews"].append(
    {"buffer": 0, "byteOffset": len(out), "byteLength": t.nbytes, "target": 34963}
)
out.extend(t.tobytes())
p["indices"] = len(g["accessors"])
g["accessors"].append(
    {"bufferView": vi, "componentType": 5125, "count": t.size, "type": "SCALAR"}
)
write(dst, g, out)
print("restored shoulder triangles", len(t))
