"""Repair verified left/right weight discontinuity on the new coat centre only."""

import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "models/plaguedoctor-L8.glb"
data = path.read_bytes()
n = struct.unpack_from("<I", data, 12)[0]
model = json.loads(data[20 : 20 + n])
binary = bytearray(data[28 + n :])


def array(index):
    a = model["accessors"][index]
    v = model["bufferViews"][a["bufferView"]]
    dt = np.dtype({5126: "<f4", 5121: "u1", 5123: "<u2"}[a["componentType"]])
    width = {"VEC3": 3, "VEC4": 4}[a["type"]]
    return np.ndarray(
        (a["count"], width),
        dtype=dt,
        buffer=binary,
        offset=v.get("byteOffset", 0) + a.get("byteOffset", 0),
        strides=(v.get("byteStride", width * dt.itemsize), dt.itemsize),
    )


node = next(node for node in model["nodes"] if node.get("name") == "L8_Armour")
primitive = model["meshes"][node["mesh"]]["primitives"][0]
attrs = primitive["attributes"]
p = array(attrs["POSITION"])
j = array(attrs["JOINTS_0"])
w = array(attrs["WEIGHTS_0"])
names = [model["nodes"][i]["name"] for i in model["skins"][node["skin"]]["joints"]]
indices = {name: i for i, name in enumerate(names)}


def smooth(a, b, v):
    t = float(np.clip((v - a) / (b - a), 0, 1))
    return t * t * (3 - 2 * t)


count = 0
for i, (x, y, z) in enumerate(p):
    blend = (
        (1 - smooth(0.045, 0.16, abs(x)))
        * smooth(0.24, 0.32, y)
        * (1 - smooth(0.80, 0.94, y))
    )
    if blend <= 0.0001:
        continue
    weights = {names[k]: float(value) for k, value in zip(j[i], w[i]) if value > 0}
    mixed = dict(weights)
    left = smooth(-0.16, 0.16, x)
    for base in ["thigh", "calf", "foot", "ball"]:
        a = weights.get(base + "_l", 0)
        b = weights.get(base + "_r", 0)
        total = a + b
        mixed[base + "_l"] = a * (1 - blend) + total * left * blend
        mixed[base + "_r"] = b * (1 - blend) + total * (1 - left) * blend
    # Coat hems need thigh/calf motion, not toe articulation. Fold minor toe weights
    # into the corresponding calf only within the central repair region.
    for side in ["l", "r"]:
        for base in ["ball", "foot"]:
            name = base + "_" + side
            delta = mixed.get(name, 0) * blend
            mixed[name] = mixed.get(name, 0) - delta
            mixed["calf_" + side] = mixed.get("calf_" + side, 0) + delta
    chosen = sorted(mixed.items(), key=lambda item: item[1], reverse=True)[:4]
    total = sum(v for _, v in chosen)
    for k, (name, value) in enumerate(chosen):
        j[i, k] = indices[name]
        w[i, k] = value / total
    count += 1
(ROOT / "pre-animation-repair/L8-before-coat-smoothing.glb").write_bytes(data)
path.write_bytes(data[: 28 + n] + binary)
(ROOT / "coat-repair.json").write_text(
    json.dumps(
        {
            "rank": 8,
            "changedNewArmourVertices": count,
            "cause": "Nearest-surface left/right calf weights jumped across a continuous centre panel; measured edge stretch up to 97.55x in Armed pose.",
            "method": "Smooth bilateral coat-centre weights, no geometry deletion or original mesh edits.",
            "visualAcceptance": "pending",
        },
        indent=2,
    )
)
print("coat vertices smoothed", count)
