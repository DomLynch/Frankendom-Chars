"""Localized recruit cloth weights and neutral material for stray red texels."""

import copy
import io
import json
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix, diags
from PIL import Image
from pack_preserved import read, arr, write

src, dst = sys.argv[1:3]
g, b = read(src)
out = bytearray(b)
n = next(n for n in g["nodes"] if n.get("name") == "Pitborn_L1_Armour")
mesh = g["meshes"][n["mesh"]]
p = mesh["primitives"][0]
v = arr(g, b, p["attributes"]["POSITION"])
joints = arr(g, b, p["attributes"]["JOINTS_0"]).copy()
weights = arr(g, b, p["attributes"]["WEIGHTS_0"]).copy()


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# Back waist cloth: remove opposing thigh influence with a soft local boundary.
f = (
    (1 - smooth(0.09, 0.18, abs(v[:, 0])))
    * smooth(0.90, 0.98, v[:, 1])
    * (1 - smooth(1.12, 1.22, v[:, 1]))
    * (1 - smooth(-0.15, -0.09, v[:, 2]))
)
dense = np.zeros((len(v), 65), dtype=np.float32)
for k in range(4):
    np.add.at(dense, (np.arange(len(v)), joints[:, k]), weights[:, k])
# Keep a consistent four-joint set across this cloth patch; top-four
# truncation had alternated between upper spine and opposing thighs.
dense[:, 2] += dense[:, 3] * f
dense[:, 3] *= 1 - f

# Treat duplicated UV-seam positions as one weight vertex without welding geometry.
_, inv = np.unique(np.round(v, 5), axis=0, return_inverse=True)
count = int(inv.max()) + 1
merged = np.zeros((count, 65), dtype=np.float32)
np.add.at(merged, inv, dense)
merged /= np.bincount(inv)[:, None]
mask_weights = np.zeros(count, dtype=np.float32)
np.add.at(mask_weights, inv, f)
mask_weights /= np.bincount(inv)
triangles = inv[arr(g, b, p["indices"]).reshape(-1, 3)]
edges = np.concatenate(
    [triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]]
)
edges = np.concatenate([edges, edges[:, ::-1]])
a = coo_matrix(
    (np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(count, count)
).tocsr()
a.data[:] = 1
a = diags(1 / np.maximum(np.asarray(a.sum(1)).ravel(), 1)) @ a
for _ in range(100):
    merged = merged * (1 - 0.6 * mask_weights[:, None]) + (a @ merged) * (
        0.6 * mask_weights[:, None]
    )
dense = merged[inv]
order = np.argsort(dense, axis=1)[:, -4:][:, ::-1]
weights = np.take_along_axis(dense, order, axis=1)
weights /= weights.sum(1)[:, None]
joints = order.astype("<u2")
joints[weights == 0] = 0


def attribute(data, typ, component, target=34962):
    data = np.ascontiguousarray(data)
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
    g["accessors"].append(
        {"bufferView": vi, "componentType": component, "count": len(data), "type": typ}
    )
    return ai


p["attributes"]["WEIGHTS_0"] = attribute(weights.astype("<f4"), "VEC4", 5126)
p["attributes"]["JOINTS_0"] = attribute(joints, "VEC4", 5123)
tri = arr(g, b, p["indices"]).reshape(-1, 3)
uv = arr(g, b, p["attributes"]["TEXCOORD_0"])
tex = g["textures"][
    g["materials"][p["material"]]["pbrMetallicRoughness"]["baseColorTexture"]["index"]
]
i = tex.get(
    "source", tex.get("extensions", {}).get("EXT_texture_webp", {}).get("source")
)
view = g["bufferViews"][g["images"][i]["bufferView"]]
start = view.get("byteOffset", 0)
a = np.array(
    Image.open(io.BytesIO(b[start : start + view["byteLength"]])).convert("RGB"),
    dtype=float,
)
pixels = a[
    np.clip((uv[:, 1] * (len(a) - 1)).astype(int), 0, len(a) - 1),
    np.clip((uv[:, 0] * (a.shape[1] - 1)).astype(int), 0, a.shape[1] - 1),
]
red = (
    (pixels[:, 0] > 140)
    & (pixels[:, 0] > pixels[:, 1] * 1.8)
    & (pixels[:, 0] > pixels[:, 2] * 1.8)
)
mask = red[tri].any(1) & (
    v[
        tri,
        :,
    ][..., 1].mean(1)
    > 1.40
)
if mask.any():
    patch = copy.deepcopy(p)
    patch["indices"] = attribute(
        tri[mask].reshape(-1).astype("<u4"), "SCALAR", 5125, 34963
    )
    patch["material"] = len(g["materials"])
    g["materials"].append(
        {
            "name": "L1 neutral linen repair",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.30, 0.23, 0.17, 1],
                "roughnessFactor": 0.95,
                "metallicFactor": 0,
            },
        }
    )
    p["indices"] = attribute(
        tri[~mask].reshape(-1).astype("<u4"), "SCALAR", 5125, 34963
    )
    mesh["primitives"].append(patch)
write(dst, g, out)
Path(dst + ".repair.json").write_text(
    json.dumps(
        {"waistVertices": int((f > 0).sum()), "neutralizedTriangles": int(mask.sum())},
        indent=2,
    )
)
