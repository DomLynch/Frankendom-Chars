"""Check exported first proof against the preserved original GLB."""

import hashlib
import json
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20 : 20 + length]), data[28 + length :]


def array(model, binary, index):
    accessor = model["accessors"][index]
    view = model["bufferViews"][accessor["bufferView"]]
    dtype = np.dtype(
        {5126: "<f4", 5125: "<u4", 5123: "<u2", 5121: "u1"}[accessor["componentType"]]
    )
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[accessor["type"]]
    return np.ndarray(
        (accessor["count"], width),
        dtype=dtype,
        buffer=binary,
        offset=view.get("byteOffset", 0) + accessor.get("byteOffset", 0),
        strides=(view.get("byteStride", width * dtype.itemsize), dtype.itemsize),
    )


receipts = []
for rank in range(2, 11):
    original, _ = read(ROOT / "models/plaguedoctor-L1.glb")
    path = ROOT / f"models/plaguedoctor-L{rank}.glb"
    model, binary = read(path)
    expected_clips = sorted(a["name"] for a in original["animations"])
    actual_clips = sorted(a["name"] for a in model["animations"])
    assert actual_clips == expected_clips, (expected_clips, actual_clips)
    expected_bones = {
        original["nodes"][i]["name"] for i in original["skins"][0]["joints"]
    }
    for skin in model["skins"]:
        assert {model["nodes"][i]["name"] for i in skin["joints"]} == expected_bones
    triangles = 0
    for mesh in model["meshes"]:
        for primitive in mesh["primitives"]:
            attrs = primitive["attributes"]
            assert np.isfinite(array(model, binary, attrs["POSITION"])).all()
            if "WEIGHTS_0" in attrs:
                weights = array(model, binary, attrs["WEIGHTS_0"])
                assert np.isfinite(weights).all() and (weights >= 0).all()
                assert np.allclose(weights.sum(axis=1), 1, atol=0.002)
            triangles += model["accessors"][primitive["indices"]]["count"] // 3
    receipt = {
        "status": "passed",
        "file": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "trianglesIncludingPreservedHiddenOriginal": triangles,
        "jointNames": len(expected_bones),
        "clips": len(actual_clips),
        "scope": "Finite geometry, normalized weights, unchanged joint and clip names. Visual fit acceptance separate.",
    }

    folder = ROOT / ("proof-v3" if rank == 10 else f"ladder/L{rank}")
    images = json.loads((folder / "render-receipt.json").read_text())
    images = [row for row in images if row["image"].startswith(f"L{rank}-")]
    assert len(images) == 6
    assert all(row["sha256"] == receipt["sha256"] for row in images)
    assert all((folder / "renders" / row["image"]).exists() for row in images)
    build = json.loads((folder / f"L{rank}-build.json").read_text())
    assert build["retainedVerticesWeightsUnchanged"]
    receipt["rank"] = rank
    receipt["hashMatchedViews"] = len(images)
    receipts.append(receipt)

original_receipt = json.loads((ROOT / "source/originals.json").read_text())
assert (
    hashlib.sha256(Path(original_receipt["body"]).read_bytes()).hexdigest()
    == original_receipt["sha256"]
)
(ROOT / "validation.json").write_text(
    json.dumps(
        {"status": "passed", "models": receipts, "originalUnchanged": True}, indent=2
    )
)
print(
    "PASS",
    len(receipts),
    "models;",
    sum(r["hashMatchedViews"] for r in receipts),
    "hash-matched captures; original unchanged",
)
