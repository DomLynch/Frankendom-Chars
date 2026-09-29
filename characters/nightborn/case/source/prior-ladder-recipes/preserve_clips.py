"""Preserve exact original animation samplers and joint rest transforms in exports."""

import copy
import json
import shutil
import sys
from glb_checks import transforms, arr
import numpy as np
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


original, ob = read(ROOT / "original/nightborn.glb")
for arg in sys.argv[1:]:
    path = Path(arg)
    backup = path.with_suffix(".before-animation.glb")
    backup.parent.mkdir(exist_ok=True)
    if backup.exists():
        assert backup.read_bytes()==path.read_bytes(), "Do not apply twice"
    else:
        shutil.copy2(path, backup)
    model, binary = read(path)
    binary = bytearray(binary)
    names = {n.get("name"): i for i, n in enumerate(model["nodes"])}
    # Refuse altered hierarchy or incompatible bind matrices before restoring clips.
    op={c:original['nodes'][i].get('name') for i,n in enumerate(original['nodes']) for c in n.get('children',[])}
    mp={c:model['nodes'][i].get('name') for i,n in enumerate(model['nodes']) for c in n.get('children',[])}
    bones={original['nodes'][i]['name'] for i in original['skins'][0]['joints']}
    for i in original['skins'][0]['joints']:
        n=original['nodes'][i]['name'];assert n in names,n
        if op.get(i) in bones: assert mp.get(names[n])==op[i],('hierarchy',n)
    source_skin=original['skins'][0]; exported_skin=model['skins'][0]
    oi=arr(original,ob,source_skin['inverseBindMatrices']);mi=arr(model,binary,exported_skin['inverseBindMatrices'])
    om={original['nodes'][i]['name']:v for i,v in zip(source_skin['joints'],oi)}
    mm={model['nodes'][i]['name']:v for i,v in zip(exported_skin['joints'],mi)}
    delta=max(float(np.max(np.abs(om[n]-mm[n]))) for n in bones)
    print('inverse-bind maximum delta',delta)
    conversions=[np.linalg.inv(om[n].reshape(4,4).T) @ mm[n].reshape(4,4).T for n in bones]
    variance=max(float(np.max(np.abs(c-conversions[0]))) for c in conversions)
    print('Bind-space conversion variance across every joint',variance)
    assert variance<1e-5, 'Inconsistent skin bind-space conversion'
    for clip in ['Armed','Heavy','Guard','Kick']:
        expected=transforms(original,ob,clip,0); actual=transforms(model,binary,clip,0)
        assert max(float(np.max(np.abs(expected[n]-actual[n]))) for n in expected)<1e-5, 'Skeleton world transforms changed'


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
    "Preserved exact original sampler payloads and joint rest transforms after compatibility checks"
)
