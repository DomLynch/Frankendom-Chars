"""Close elite helmets and cover exposed anatomy without replacing existing suits."""

import copy
import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from merge_armour import read, write

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "source"))
from check_motion import arr  # noqa: E402


def patch(rank):
    source = ROOT / f"models/dwarf-{rank}.glb"
    j, original = read(source)
    canonical, cb = read(ROOT / "models/dwarf-L1.glb")
    b = bytearray(original)
    report = {"rank": rank, "inputSha256": hashlib.sha256(source.read_bytes()).hexdigest()}

    def append(values, component, kind, target=34962):
        values = np.asarray(values, dtype={5126: "<f4", 5123: "<u2", 5125: "<u4"}[component])
        b.extend(b"\0" * (-len(b) % 4))
        vi = len(j["bufferViews"])
        j["bufferViews"].append(dict(buffer=0, byteOffset=len(b), byteLength=values.nbytes, target=target))
        b.extend(values.tobytes())
        ai = len(j["accessors"])
        a = dict(bufferView=vi, componentType=component, count=len(values), type=kind)
        if kind == "VEC3":
            a.update(min=values.min(0).tolist(), max=values.max(0).tolist())
        j["accessors"].append(a)
        return ai

    def indices(f):
        return append(np.asarray(f).reshape(-1), 5125, "SCALAR", 34963)

    def node(name, primitives, skin):
        mi = len(j["meshes"])
        j["meshes"].append({"name": rank + "_" + name, "primitives": primitives})
        ni = len(j["nodes"])
        j["nodes"].append({"name": rank + "_" + name, "mesh": mi, "skin": skin})
        j["scenes"][j.get("scene", 0)]["nodes"].append(ni)

    palette = {"L8": [0.075, 0.08, 0.09, 1], "L9": [0.007, 0.045, 0.018, 1], "L10": [0.42, 0.23, 0.04, 1]}
    def material(name, colour, roughness=0.52):
        mi = len(j["materials"])
        j["materials"].append({"name": rank + " " + name, "pbrMetallicRoughness": {"baseColorFactor": colour, "metallicFactor": 0.8, "roughnessFactor": roughness}})
        return mi

    metal = material("closed visor metal", palette[rank])
    trim = material("raised visor edges", [0.28, 0.31, 0.32, 1] if rank != "L10" else [0.8, 0.5, 0.11, 1], 0.44)
    dark = material("recessed sealed visor", [0.007, 0.009, 0.008, 1], 0.8)
    body_id = next(i for i, n in enumerate(canonical["nodes"]) if n.get("name") == "CreatureBody")
    j["nodes"][body_id].pop("mesh", None)
    j["nodes"][body_id].pop("skin", None)
    shellmat = material("coverage armour", palette[rank], 0.58)

    armour = next(n for n in j["nodes"] if n.get("name") == rank + "_Armour")
    # Retained donor anatomy can also carry exposed skin; cover only those local
    # non-metallic triangles, keeping the suit's metal and gemstone primitives.
    parts = j["meshes"][armour["mesh"]]["primitives"]
    additions = []
    for p in parts:
        mat = j["materials"][p["material"]]
        underlayer = "Leather and exposed surface" in mat.get("name", "")
        if not underlayer and (rank != "L9" or "Emerald inset" in mat.get("name", "")):
            continue
        attrs = p["attributes"]
        vv = arr(j, original, attrs["POSITION"])
        ff = arr(j, original, p["indices"]).reshape(-1, 3).astype(int)
        cc = vv[ff].mean(1)
        limbs = ((np.abs(cc[:, 0]) > .20) & (cc[:, 1] > .78) & (cc[:, 1] < 1.25)) | ((np.abs(cc[:, 0]) < .25) & (cc[:, 1] > .35) & (cc[:, 1] < .75))
        # Cover the complete non-metallic limb patches, including dark skin pixels.
        cover = limbs
        if not underlayer:
            uv = arr(j, original, attrs["TEXCOORD_0"])[ff].mean(1)
            tex = j["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]
            image = j["images"][tex.get("source", tex.get("extensions", {}).get("EXT_texture_webp", {}).get("source"))]
            view = j["bufferViews"][image["bufferView"]]
            start = view.get("byteOffset", 0)
            pixels = np.asarray(Image.open(io.BytesIO(original[start:start + view["byteLength"]])).convert("RGB"))
            colour = pixels[np.clip((uv[:, 1] * len(pixels)).astype(int), 0, len(pixels) - 1), np.clip((uv[:, 0] * pixels.shape[1]).astype(int), 0, pixels.shape[1] - 1)] / 255
            red, green, blue = colour.T
            cover = limbs & (red > green * 1.09) & (green > blue * 1.04) & (red > .16) & (green > .08)
        if cover.any():
            p["indices"] = indices(ff[~cover])
            additions.append(dict(attributes=copy.deepcopy(attrs), indices=indices(ff[cover]), material=shellmat))
    parts.extend(additions)
    skin_id = armour["skin"]
    skin = j["skins"][skin_id]
    joint_names = [j["nodes"][i]["name"] for i in skin["joints"]]
    headid = joint_names.index("Head")
    spineid = joint_names.index("spine_03")

    if rank == "L8":
        # Transplant only the already-reconstructed closed horned helmet.
        for p in j["meshes"][armour["mesh"]]["primitives"]:
            vv = arr(j, original, p["attributes"]["POSITION"])
            ff = arr(j, bytes(b), p["indices"]).reshape(-1, 3).astype(int)
            cc = vv[ff].mean(1)
            p["indices"] = indices(ff[~((cc[:, 1] > 1.265) & (np.abs(cc[:, 0]) < 0.20))])
    donor, db = read(ROOT / "elite-correction/L8-detail/dwarf-L8.glb")
    dn = next(n for n in donor["nodes"] if n.get("name") == "L8_Armour")
    memo = {}
    def copy_resource(kind, index):
        key = (kind, index)
        if key in memo:
            return memo[key]
        value = copy.deepcopy(donor[kind][index])
        output = len(j.setdefault(kind, []))
        memo[key] = output
        j[kind].append(value)
        if kind == "bufferViews":
            start = value.get("byteOffset", 0)
            b.extend(b"\0" * (-len(b) % 4))
            value["byteOffset"] = len(b)
            value["buffer"] = 0
            b.extend(db[start:start + value["byteLength"]])
        elif kind in ["accessors", "images"]:
            value["bufferView"] = copy_resource("bufferViews", value["bufferView"])
        elif kind == "textures":
            for key, kind2 in [("source", "images"), ("sampler", "samplers")]:
                if key in value:
                    value[key] = copy_resource(kind2, value[key])
            for ext in value.get("extensions", {}).values():
                if "source" in ext:
                    ext["source"] = copy_resource("images", ext["source"])
        elif kind == "materials":
            def textures(obj):
                for key, val in obj.items():
                    if isinstance(val, dict):
                        if key.endswith("Texture") and "index" in val:
                            val["index"] = copy_resource("textures", val["index"])
                        else:
                            textures(val)
            textures(value)
            if rank in ["L9", "L10"]:
                value["pbrMetallicRoughness"]["baseColorFactor"] = [0.14, 0.65, 0.25, 1] if rank == "L9" else [1, 0.65, 0.16, 1]
                value["emissiveFactor"] = [0, 0, 0]
        return output
    helmet_parts = []
    coverage_parts = []
    for dp in donor["meshes"][dn["mesh"]]["primitives"]:
        vv = arr(donor, db, dp["attributes"]["POSITION"])
        ff = arr(donor, db, dp["indices"]).reshape(-1, 3).astype(int)
        cc = vv[ff].mean(1)
        ax, yy = np.abs(cc[:, 0]), cc[:, 1]
        helmet = (yy > 1.215) & (ax < .245)
        arms = (ax > .205) & (yy > .78) & (yy < 1.165)
        thighs = (ax > .045) & (ax < .25) & (yy > .37) & (yy < .72)
        collar = (ax < .18) & (yy > 1.045) & (yy < 1.235)
        coverage = arms | thighs | collar
        donor_names = [donor["nodes"][i]["name"] for i in donor["skins"][dn["skin"]]["joints"]]
        oldids = arr(donor, db, dp["attributes"]["JOINTS_0"]).astype(int)
        remap = np.array([joint_names.index(name) for name in donor_names])
        attrs = {key: copy_resource("accessors", value) for key, value in dp["attributes"].items()}
        attrs["JOINTS_0"] = append(remap[oldids], 5123, "VEC4")
        if rank == "L8":
            mat = copy_resource("materials", dp["material"])
            helmet_parts.append(dict(attributes=attrs, indices=indices(ff[helmet]), material=mat))
        else:
            mat = copy_resource("materials", dp["material"])
        coverage_parts.append(dict(attributes=attrs, indices=indices(ff[coverage]), material=mat))
    if helmet_parts:
        node("ClosedHelmet", helmet_parts, skin_id)
    node("Coverage", coverage_parts, skin_id)
    report["coverageSource"] = "Saved fitted donor panels: sleeves, thighs and collar only"
    for ext in donor.get("extensionsUsed", []):
        if ext not in j.setdefault("extensionsUsed", []):
            j["extensionsUsed"].append(ext)

    # Structured surfaces are authored around the original head and neck bind coordinates.
    def surface(name, rows, angles, mat, blend=False):
        points = []
        weights = []
        joints = []
        for height, rx, rz, zoffset in rows:
            for angle in angles:
                points.append([rx * np.sin(angle), height, zoffset + rz * np.cos(angle)])
                t = float(np.clip((height - 1.11) / 0.13, 0, 1)) if blend else 1.0
                weights.append([t, 1 - t, 0, 0])
                joints.append([headid if t > 0 else 0, spineid if t < 1 else 0, 0, 0])
        faces = []
        count = len(angles)
        for row in range(len(rows) - 1):
            for col in range(count - 1):
                a = row * count + col
                faces.extend([(a, a + 1, a + count), (a + 1, a + count + 1, a + count)])
        points, faces = np.array(points), np.array(faces)
        n = np.zeros_like(points)
        cross = np.cross(points[faces[:, 1]] - points[faces[:, 0]], points[faces[:, 2]] - points[faces[:, 0]])
        for col in range(3):
            np.add.at(n, faces[:, col], cross)
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        attributes = {"POSITION": append(points, 5126, "VEC3"), "NORMAL": append(n, 5126, "VEC3"), "JOINTS_0": append(joints, 5123, "VEC4"), "WEIGHTS_0": append(weights, 5126, "VEC4")}
        node(name, [dict(attributes=attributes, indices=indices(faces), material=mat)], skin_id)

    surface("SealedGorget", [(1.09, .080, .070, 0), (1.13, .085, .080, .005), (1.19, .085, .088, .015), (1.255, .085, .100, .016)], np.linspace(-np.pi, np.pi, 33), metal, True)
    if rank != "L8":
        # Existing finned/crowned helmet stays intact; new enclosed inner shell and visor fill its opening.
        surface("HelmetLiner", [(1.175, .080, .095, .018), (1.22, .092, .105, .023), (1.29, .094, .11, .024), (1.345, .087, .112, .02), (1.38, .075, .09, .015), (1.405, .001, .001, .015)], np.linspace(-np.pi, np.pi, 25), metal)
        angles = np.linspace(-np.pi / 2, np.pi / 2, 9)
        rows = [(1.18, .060, .12, .025), (1.215, .084, .139, .025), (1.29, .096, .147, .025), (1.32, .088, .145, .025)]
        if rank == "L10":
            rows = [(1.12, .028, .105, .022), (1.17, .066, .137, .025), (1.24, .088, .143, .025), (1.315, .094, .142, .025)]
        surface("WedgeVisor" if rank == "L9" else "MetalBeardMask", rows, angles, metal)
        # Blind, dark backed eye slit, plus raised brows. No visible face behind it.
        surface("SealedEyeSlit", [(1.318, .085, .15, .025), (1.334, .084, .15, .025)], angles, dark)
        surface("VisorBrow", [(1.333, .087, .153, .025), (1.342, .086, .152, .025)], angles, trim)
        # Faceted vertical ribs read as forged runes / a carved metallic beard.
        for index, angle in enumerate(np.linspace(-1.05, 1.05, 7)):
            ribrows = [(h, rx + .002, rz + .004, z) for h, rx, rz, z in rows]
            surface(f"MaskRib{index}", ribrows, [angle - .026, angle, angle + .026], trim)

    dest = ROOT / f"elite-correction/targeted/{rank}/dwarf-{rank}.glb"
    dest.parent.mkdir(parents=True, exist_ok=True)
    write(dest, j, b)
    assert j["animations"] == canonical["animations"]
    assert bytes(b[:len(cb)]) == cb
    report.update(outputSha256=hashlib.sha256(dest.read_bytes()).hexdigest(), originalBinaryExact=True, originalAnimationsExact=True, existingSuitVertexAttributesUnchanged=True, scope="helmet and coverage patch; visual acceptance pending")
    (dest.parent / "patch-receipt.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rank", choices=["L8", "L9", "L10"])
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    if args.root:
        ROOT = args.root.resolve()
    patch(args.rank)
