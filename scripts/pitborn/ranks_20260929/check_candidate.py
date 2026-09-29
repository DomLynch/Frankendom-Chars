"""Preservation and sampled deformation checks for every added visible surface."""

from pathlib import Path
import sys
import json
import hashlib
import numpy as np
from pack_preserved import read, arr
from motion_math import joint_matrices

path = Path(sys.argv[1])
original, original_binary = read("source/pitborn.glb")
g, b = read(path)
assert g["animations"] == original["animations"]
assert g["skins"] == original["skins"]
assert g["nodes"][: len(original["nodes"])] == original["nodes"]
assert b[: len(original_binary)] == original_binary
Path(str(path) + ".preservation.json").write_text(
    json.dumps(
        {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "originalSha256": hashlib.sha256(
                Path("source/pitborn.glb").read_bytes()
            ).hexdigest(),
            "originalBinaryPrefixUnchanged": True,
            "originalNodesExact": True,
            "originalSkinsExact": True,
            "originalAnimationsExact": True,
            "clips": len(original["animations"]),
            "sourceJoints": len(original["skins"][0]["joints"]),
            "scope": "Post-repair preservation; deformation and visual acceptance are separate.",
        },
        indent=2,
    )
)
skin = g["skins"][9]
ib = arr(g, b, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
poses = []
for clip in ["Armed", "Attack", "Heavy", "Guard", "Kick", "Roll"]:
    animation = next(a for a in g["animations"] if a["name"] == clip)
    duration = max(arr(g, b, s["input"]).max() for s in animation["samplers"])
    for time in np.linspace(0, float(duration), 9):
        matrices = joint_matrices(g, b, clip, time)
        bones = np.stack([matrices[g["nodes"][i]["name"]] for i in skin["joints"]]) @ ib
        poses.append((clip, float(time), bones))
results = []
for node in g["nodes"]:
    name = node.get("name", "")
    if "mesh" not in node or "skin" not in node:
        continue
    for pi, prim in enumerate(g["meshes"][node["mesh"]]["primitives"]):
        material = g["materials"][prim["material"]]
        if (
            material.get("pbrMetallicRoughness", {}).get(
                "baseColorFactor", [1, 1, 1, 1]
            )[3]
            == 0
        ):
            continue
        local_skin = g["skins"][node["skin"]]
        assert local_skin["joints"] == skin["joints"]
        assert np.array_equal(
            arr(g, b, local_skin["inverseBindMatrices"]),
            arr(g, b, skin["inverseBindMatrices"]),
        )
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
