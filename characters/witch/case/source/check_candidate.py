"""Preservation and sampled deformation checks for every added visible surface."""

from pathlib import Path
import sys
import json
import hashlib
import numpy as np
from pack_preserved import read, arr
from motion_math import joint_matrices

path = Path(sys.argv[1])
original, original_binary = read("source/original.glb")
g, b = read(path)
assert g["animations"] == original["animations"]
assert g["skins"] == original["skins"]
assert g["nodes"][: len(original["nodes"])] == original["nodes"]
assert b[: len(original_binary)] == original_binary
skin = g["skins"][0]
ib = arr(g, b, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
poses = []
for clip in [
    "Trident_Idle",
    "Trident_High",
    "Trident_Guard",
    "Trident_Thrust",
    "Kick",
    "Roll",
]:
    animation = next(a for a in g["animations"] if a["name"] == clip)
    duration = max(arr(g, b, s["input"]).max() for s in animation["samplers"])
    for time in np.linspace(0, float(duration), 9):
        matrices = joint_matrices(g, b, clip, time)
        bones = np.stack([matrices[g["nodes"][i]["name"]] for i in skin["joints"]]) @ ib
        poses.append((clip, float(time), bones))
results = []
for node in g["nodes"]:
    name = node.get("name", "")
    if not (name.endswith("_Armour") or name == "CreatureBody"):
        continue
    for pi, prim in enumerate(g["meshes"][node["mesh"]]["primitives"]):
        if name == "CreatureBody" and pi == 0:
            continue
        a = prim["attributes"]
        tri = arr(g, b, prim["indices"]).reshape(-1, 3)
        used, inverse = np.unique(tri, return_inverse=True)
        tri = inverse.reshape(-1, 3)
        p = arr(g, b, a["POSITION"])[used].astype(float)
        w = arr(g, b, a["WEIGHTS_0"])[used]
        joints = arr(g, b, a["JOINTS_0"])[used]
        assert np.isfinite(p).all() and np.isfinite(w).all()
        assert np.max(abs(w.sum(1) - 1)) < 2e-4
        edges = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
        rest = np.linalg.norm(p[edges[:, 0]] - p[edges[:, 1]], axis=1)
        hp = np.c_[p, np.ones(len(p))]
        for clip, time, bones in poses:
            posed = np.einsum("ni,nijk,nk->nj", w, bones[joints], hp)[:, :3]
            assert np.isfinite(posed).all()
            lengths = np.linalg.norm(posed[edges[:, 0]] - posed[edges[:, 1]], axis=1)
            ratio = lengths / np.maximum(rest, 1e-6)
            bad = (lengths > 0.12) & (ratio > 3)
            results.append(
                {
                    "node": name,
                    "primitive": pi,
                    "clip": clip,
                    "time": time,
                    "longStretchedEdgeOccurrences": int(bad.sum()),
                    "p99Stretch": float(np.quantile(ratio, 0.99)),
                    "worstEdgeMidpoints": p[edges[bad]][:8].mean(1).tolist(),
                }
            )
report = {
    "model": str(path),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "sourceBinaryRigAnimationsPreserved": True,
    "samples": results,
    "maxLongStretchedEdgeOccurrences": max(
        r["longStretchedEdgeOccurrences"] for r in results
    ),
    "status": "sampled deformation measurements; visual acceptance separate",
}
Path(f"checks/{path.stem}-motion.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != "samples"}))
assert report["maxLongStretchedEdgeOccurrences"] == 0
