"""Make tiny reconstructed fittings follow the adjoining armour surface."""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from pack_preserved import arr, read, write

source, destination = sys.argv[1:3]
g, binary = read(source)
node = next(n for n in g["nodes"] if n.get("name", "").endswith("_Armour"))
primitive = g["meshes"][node["mesh"]]["primitives"][0]
attrs = primitive["attributes"]
positions = arr(g, binary, attrs["POSITION"]).copy()
triangles = arr(g, binary, primitive["indices"]).reshape(-1, 3)
joints = arr(g, binary, attrs["JOINTS_0"]).copy()
weights = arr(g, binary, attrs["WEIGHTS_0"]).copy()
_, inverse = np.unique(np.round(positions, 5), axis=0, return_inverse=True)
t = inverse[triangles]
rows = np.r_[t[:, 0], t[:, 1], t[:, 2]]
cols = np.r_[t[:, 1], t[:, 2], t[:, 0]]
_, labels = connected_components(
    coo_matrix(
        (np.ones(len(rows)), (rows, cols)),
        shape=(int(inverse.max() + 1), int(inverse.max() + 1)),
    ),
    directed=False,
)
counts = np.bincount(labels[t[:, 0]])
vertex_labels = labels[inverse]
main = np.flatnonzero(counts[vertex_labels] >= 20)
tree = cKDTree(positions[main])
repairs = []
for label in np.flatnonzero((counts > 0) & (counts < 20)):
    selected = np.flatnonzero(vertex_labels == label)
    centre = positions[selected].mean(0)
    distance, nearest = tree.query(centre)
    # Only repair local fittings; remote components require a separate diagnosis.
    if distance > 0.08:
        continue
    anchor = main[nearest]
    joints[selected] = joints[anchor]
    weights[selected] = weights[anchor]
    repairs.append(
        {
            "component": int(label),
            "faces": int(counts[label]),
            "vertices": len(selected),
            "anchorDistance": float(distance),
        }
    )
out = bytearray(binary)
for key, data in [
    ("JOINTS_0", joints.astype("<u2")),
    ("WEIGHTS_0", weights.astype("<f4")),
]:
    out.extend(b"\0" * (-len(out) % 4))
    view = len(g["bufferViews"])
    g["bufferViews"].append(
        {
            "buffer": 0,
            "byteOffset": len(out),
            "byteLength": data.nbytes,
            "target": 34962,
        }
    )
    out.extend(data.tobytes())
    g["accessors"][attrs[key]].update(
        bufferView=view, byteOffset=0, componentType=5123 if key == "JOINTS_0" else 5126
    )
write(destination, g, out)
Path(destination + ".fragments.json").write_text(json.dumps(repairs, indent=2))
print(
    json.dumps(
        {"repairedComponents": len(repairs), "faces": sum(r["faces"] for r in repairs)}
    )
)
