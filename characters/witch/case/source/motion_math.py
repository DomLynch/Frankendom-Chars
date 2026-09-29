"""Compare exported joint world positions over all clips against original."""

import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    d = path.read_bytes()
    n = struct.unpack_from("<I", d, 12)[0]
    return json.loads(d[20 : 20 + n]), d[28 + n :]


def arr(m, b, i):
    a = m["accessors"][i]
    v = m["bufferViews"][a["bufferView"]]
    dt = np.dtype({5126: "<f4", 5123: "<u2", 5125: "<u4"}[a["componentType"]])
    w = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
    return np.ndarray(
        (a["count"], w),
        dtype=dt,
        buffer=b,
        offset=v.get("byteOffset", 0) + a.get("byteOffset", 0),
        strides=(v.get("byteStride", w * dt.itemsize), dt.itemsize),
    )


def joint_matrices(m, b, clip, t):
    nodes = m["nodes"]
    values = {}
    a = next(a for a in m["animations"] if a["name"] == clip)
    for c in a["channels"]:
        s = a["samplers"][c["sampler"]]
        ts = arr(m, b, s["input"])[:, 0]
        vs = arr(m, b, s["output"])
        j = int(np.searchsorted(ts, t))
        lo = max(0, j - 1)
        hi = min(len(ts) - 1, j)
        f = 0 if lo == hi else float(np.clip((t - ts[lo]) / (ts[hi] - ts[lo]), 0, 1))
        u = vs[lo].astype(float)
        v = vs[hi].astype(float)
        path = c["target"]["path"]
        if path == "rotation":
            dot = np.dot(u, v)
            if dot < 0:
                v = -v
                dot = -dot
            if dot < 0.9995:
                angle = np.arccos(np.clip(dot, -1, 1))
                value = (np.sin((1 - f) * angle) * u + np.sin(f * angle) * v) / np.sin(
                    angle
                )
            else:
                value = (1 - f) * u + f * v
            value /= np.linalg.norm(value)
        else:
            value = (1 - f) * u + f * v
        values[(c["target"]["node"], path)] = value
    parents = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
    cache = {}

    def world(i):
        if i in cache:
            return cache[i]
        n = nodes[i]
        if "matrix" in n:
            local = np.array(n["matrix"]).reshape(4, 4).T
        else:
            x, y, z, w = values.get((i, "rotation"), n.get("rotation", [0, 0, 0, 1]))
            local = np.eye(4)
            local[:3, :3] = np.array(
                [
                    [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
                ]
            ) @ np.diag(values.get((i, "scale"), n.get("scale", [1, 1, 1])))
            local[:3, 3] = values.get(
                (i, "translation"), n.get("translation", [0, 0, 0])
            )
        cache[i] = world(parents[i]) @ local if i in parents else local
        return cache[i]

    return {nodes[i]["name"]: world(i) for i in m["skins"][0]["joints"]}



