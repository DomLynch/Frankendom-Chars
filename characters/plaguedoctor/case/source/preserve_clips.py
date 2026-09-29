"""Preserve exact original animation samplers and joint rest transforms in exports."""

import copy
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    data = path.read_bytes()
    n = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20 : 20 + n]), data[28 + n :]


def write(path, model, binary):
    binary += b"\0" * ((-len(binary)) % 4)
    model["buffers"][0]["byteLength"] = len(binary)
    payload = json.dumps(model, separators=(",", ":")).encode()
    payload += b" " * ((-len(payload)) % 4)
    path.write_bytes(
        struct.pack("<III", 0x46546C67, 2, 28 + len(payload) + len(binary))
        + struct.pack("<II", len(payload), 0x4E4F534A)
        + payload
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )


original, ob = read(ROOT / "models/plaguedoctor-L1.glb")
for rank in range(2, 11):
    path = ROOT / f"models/plaguedoctor-L{rank}.glb"
    backup = ROOT / f"pre-animation-repair/plaguedoctor-L{rank}.glb"
    backup.parent.mkdir(exist_ok=True)
    assert not backup.exists(), "Do not apply twice"
    shutil.copy2(path, backup)
    model, binary = read(path)
    binary = bytearray(binary)
    names = {n.get("name"): i for i, n in enumerate(model["nodes"])}
    for i in original["skins"][0]["joints"]:
        source = original["nodes"][i]
        target = model["nodes"][names[source["name"]]]
        for key in ["translation", "rotation", "scale", "matrix"]:
            target.pop(key, None)
            if key in source:
                target[key] = copy.deepcopy(source[key])
    views = {}
    accessors = {}

    def accessor(index):
        if index in accessors:
            return accessors[index]
        a = copy.deepcopy(original["accessors"][index])
        vi = a["bufferView"]
        if vi not in views:
            v = copy.deepcopy(original["bufferViews"][vi])
            start = v.get("byteOffset", 0)
            data = ob[start : start + v["byteLength"]]
            binary.extend(b"\0" * ((-len(binary)) % 4))
            v["byteOffset"] = len(binary)
            v["buffer"] = 0
            binary.extend(data)
            views[vi] = len(model["bufferViews"])
            model["bufferViews"].append(v)
        a["bufferView"] = views[vi]
        accessors[index] = len(model["accessors"])
        model["accessors"].append(a)
        return accessors[index]

    clips = copy.deepcopy(original["animations"])
    for clip in clips:
        for sampler in clip["samplers"]:
            sampler["input"] = accessor(sampler["input"])
            sampler["output"] = accessor(sampler["output"])
        for channel in clip["channels"]:
            channel["target"]["node"] = names[
                original["nodes"][channel["target"]["node"]]["name"]
            ]
    model["animations"] = clips
    write(path, model, bytes(binary))
print(
    "Preserved exact original sampler payloads and rest transforms in nine candidates"
)
