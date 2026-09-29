"""Seat L8 joint lining against measured inner armour bounds."""

import sys
import numpy as np
from pack_preserved import read, arr, worlds, write

src, dst = sys.argv[1:3]
g, b = read(src)
idx = next(
    i for i, n in enumerate(g["nodes"]) if n.get("name") == "Fitted joint sleeves"
)
p = g["meshes"][g["nodes"][idx]["mesh"]]["primitives"][0]
ai = p["attributes"]["POSITION"]
v = arr(g, b, ai)
m = worlds(g)[idx]
w = (np.c_[v, np.ones(len(v))] @ m.T)[:, :3]
x = abs(w[:, 0])
a = np.arctan2(w[:, 2] + 0.075, w[:, 1] - 1.62)
knots = [0.185, 0.25, 0.35, 0.47, 0.55, 0.70]
cy = np.interp(x, knots, [1.62, 1.635, 1.635, 1.61, 1.60, 1.60])
cz = np.interp(x, knots, [-0.06, -0.07, -0.09, -0.105, -0.10, -0.06])
ry = np.interp(x, knots, [0.095, 0.086, 0.065, 0.058, 0.082, 0.055])
rz = np.interp(x, knots, [0.15, 0.14, 0.105, 0.085, 0.09, 0.06])
w[:, 1] = cy + ry * np.cos(a)
w[:, 2] = cz + rz * np.sin(a)
v = ((np.c_[w, np.ones(len(w))] @ np.linalg.inv(m).T)[:, :3]).astype("<f4")
out = bytearray(b)
out.extend(b"\0" * (-len(out) % 4))
vi = len(g["bufferViews"])
g["bufferViews"].append(
    {"buffer": 0, "byteOffset": len(out), "byteLength": v.nbytes, "target": 34962}
)
out.extend(v.tobytes())
g["accessors"][ai].update(
    bufferView=vi, byteOffset=0, min=v.min(0).tolist(), max=v.max(0).tolist()
)
write(dst, g, out)
