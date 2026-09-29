"""Recover intact donor hood topology by exact UV and bind-position matching."""

import sys
import numpy as np
from scipy.spatial import cKDTree
from pack_preserved import arr, read, worlds, write

rank, source, dest = sys.argv[1:]
d, db = read(f"src/assets/source/creatures/witch-L{rank}-donor.glb")
di = next(i for i, n in enumerate(d["nodes"]) if "mesh" in n)
dp = d["meshes"][d["nodes"][di]["mesh"]]["primitives"][0]
p = arr(d, db, dp["attributes"]["POSITION"])
q = (np.c_[p, np.ones(len(p))] @ worlds(d)[di].T)[:, :3]
lo = q[:, 1].min()
scale = 1.81 / np.ptp(q[:, 1])
q *= scale
q[:, 1] += 0.025 - lo * scale
g, raw = read(source)
b = bytearray(raw)
ni = next(i for i, n in enumerate(g["nodes"]) if n.get("name", "").endswith("_Armour"))
prim = g["meshes"][g["nodes"][ni]["mesh"]]["primitives"][0]
matrix = worlds(g)[ni]
pos = arr(g, raw, prim["attributes"]["POSITION"])
uv = arr(d, db, dp["attributes"]["TEXCOORD_0"])
candidate_uv = arr(g, raw, prim["attributes"]["TEXCOORD_0"])
predicted = (np.c_[q, np.ones(len(q))] @ np.linalg.inv(matrix).T)[:, :3]
tree = cKDTree(candidate_uv)
dist, candidates = tree.query(uv, k=12)
score = np.linalg.norm(pos[candidates] - predicted[:, None, :], axis=2)
score[dist > 1e-6] = 1e6
mapping = candidates[np.arange(len(q)), score.argmin(1)]
source_tri = arr(d, db, dp["indices"]).reshape(-1, 3)
head_tri = source_tri[q[source_tri, 1].mean(1) > 1.52]
used = np.unique(head_tri)
for i in used[np.linalg.norm(pos[mapping[used]] - predicted[used], axis=1) > 1e-4]:
    near = np.asarray(tree.query_ball_point(uv[i], 1e-6))
    mapping[i] = near[np.linalg.norm(pos[near] - predicted[i], axis=1).argmin()]
assert np.max(np.linalg.norm(pos[mapping[used]] - predicted[used], axis=1)) < 1e-4
tri = arr(g, raw, prim["indices"]).reshape(-1, 3)
world_pos = (np.c_[pos, np.ones(len(pos))] @ matrix.T)[:, :3]
tri = np.concatenate([tri[world_pos[tri, 1].mean(1) <= 1.52], mapping[head_tri]])
tri = tri[
    (tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) & (tri[:, 0] != tri[:, 2])
]
data = tri.astype("<u4").reshape(-1)
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
prim["indices"] = ai
write(dest, g, b)
print("HOOD_RESTORED", rank, "verified original donor UV/bind mapping")
