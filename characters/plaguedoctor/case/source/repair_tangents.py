from pathlib import Path
import struct
import json
import numpy as np

R = Path(__file__).resolve().parents[1]
receipts = []
for p in (R / "models").glob("plaguedoctor-L*.glb"):
    if p.stem in ["plaguedoctor-L1"]:
        continue
    data = bytearray(p.read_bytes())
    n = struct.unpack_from("<I", data, 12)[0]
    j = json.loads(data[20 : 20 + n])
    offset = 28 + n
    changed = 0

    def arr(a):
        ac = j["accessors"][a]
        bv = j["bufferViews"][ac["bufferView"]]
        d = {"VEC3": 3, "VEC4": 4}[ac["type"]]
        return np.ndarray(
            (ac["count"], d),
            dtype="<f4",
            buffer=data,
            offset=offset + bv.get("byteOffset", 0) + ac.get("byteOffset", 0),
            strides=(bv.get("byteStride", 4 * d), 4),
        )

    for mesh in j["meshes"]:
        for pr in mesh["primitives"]:
            if "TANGENT" not in pr["attributes"]:
                continue
            t = arr(pr["attributes"]["TANGENT"])
            norm = arr(pr["attributes"]["NORMAL"])
            lengths = np.linalg.norm(t[:, :3], axis=1)
            for i in np.where(lengths < 1e-8)[0]:
                axis = np.eye(3)[np.argmin(abs(norm[i]))]
                v = np.cross(norm[i], axis)
                v /= np.linalg.norm(v)
                t[i, :3] = v
                t[i, 3] = 1
                changed += 1
    if changed:
        p.write_bytes(data)
    receipts.append(
        {
            "file": p.name,
            "degenerateUvTangentsRepaired": changed,
            "method": "Unit vector perpendicular to unchanged normal at zero-length UV tangent; positions and UVs unchanged",
        }
    )
(R / "tangent-repair.json").write_text(json.dumps(receipts, indent=2))
print(json.dumps(receipts))
