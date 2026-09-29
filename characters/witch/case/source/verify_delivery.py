"""Verify selected model/image receipts and build the review manifest/gallery."""

import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from PIL import Image
from pack_preserved import read

root = Path.cwd()
palette = [
    "Brown leather",
    "Bone & hide",
    "Copper",
    "Bronze",
    "Iron",
    "Steel",
    "Blackened steel & ruby",
    "Emerald",
    "Full gold",
]
original, original_binary = read("source/original.glb")
original_report = json.loads(Path("source/original.glb.validation.json").read_text())
original_errors = Counter(
    x["code"] for x in original_report["issues"]["messages"] if x["severity"] == 0
)
rows = []
for rank in range(2, 11):
    label = f"L{rank}"
    path = Path(f"models/witch-{label}.glb")
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    g, binary = read(path)
    assert binary[: len(original_binary)] == original_binary
    assert g["nodes"][: len(original["nodes"])] == original["nodes"]
    assert g["skins"] == original["skins"] and g["animations"] == original["animations"]
    motion = json.loads(Path(f"checks/witch-{label}-motion.json").read_text())
    assert motion["sha256"] == sha and motion["maxLongStretchedEdgeOccurrences"] == 0
    receipt = json.loads(Path(f"review/{label}/render-receipt.json").read_text())
    assert len(receipt) == 9
    for capture in receipt:
        assert capture["sha256"] == sha
        image = Path(f"review/{label}") / capture["image"]
        assert hashlib.sha256(image.read_bytes()).hexdigest() == capture["imageSha256"]
        assert Image.open(image).size == (375, 600)
        if capture["projectedArmourHeightPx"] is not None:
            assert abs(capture["projectedArmourHeightPx"] - 110) < 0.01
    report = json.loads(Path(str(path) + ".validation.json").read_text())
    errors = Counter(
        x["code"] for x in report["issues"]["messages"] if x["severity"] == 0
    )
    assert errors == original_errors
    all_triangles = sum(
        g["accessors"][p["indices"]]["count"] // 3
        for mesh in g["meshes"]
        for p in mesh["primitives"]
        if "indices" in p
    )
    reachable = set()
    pending = list(g["scenes"][g.get("scene", 0)]["nodes"])
    while pending:
        index = pending.pop()
        if index in reachable:
            continue
        reachable.add(index)
        pending.extend(g["nodes"][index].get("children", []))
    scene_triangles = 0
    material_visible = 0
    mesh_instances = 0
    hidden_original = 0
    for index in reachable:
        node = g["nodes"][index]
        if "mesh" not in node:
            continue
        mesh_instances += 1
        for prim in g["meshes"][node["mesh"]]["primitives"]:
            count = g["accessors"][prim["indices"]]["count"] // 3
            scene_triangles += count
            material = g["materials"][prim["material"]]
            alpha = material.get("pbrMetallicRoughness", {}).get(
                "baseColorFactor", [1, 1, 1, 1]
            )[3]
            if alpha > 0:
                material_visible += count
            elif node.get("name") == "CreatureBody":
                hidden_original += count
    texture_sizes = []
    for image in g["images"]:
        bv = g["bufferViews"][image["bufferView"]]
        payload = binary[
            bv.get("byteOffset", 0) : bv.get("byteOffset", 0) + bv["byteLength"]
        ]
        texture_sizes.append(
            {
                "mimeType": image["mimeType"],
                "dimensions": list(Image.open(io.BytesIO(payload)).size),
            }
        )
    rows.append(
        {
            "rank": label,
            "palette": palette[rank - 2],
            "model": str(path),
            "sha256": sha,
            "bytes": len(data),
            "storedTriangles": all_triangles,
            "storedMeshCount": len(g["meshes"]),
            "storedMaterialCount": len(g["materials"]),
            "sceneMeshInstances": mesh_instances,
            "sceneTriangleInstances": scene_triangles,
            "materialVisibleTriangleInstances": material_visible,
            "hiddenOriginalBodyTriangles": hidden_original,
            "drawCallsAndDevicePerformance": "not measured; material visibility is not a draw-cost measurement",
            "textures": texture_sizes,
            "joints": len(g["skins"][0]["joints"]),
            "clips": len(g["animations"]),
            "poseSamples": len(motion["samples"]),
            "severeStretchOccurrences": 0,
            "verifiedImages": 9,
            "formatErrorsInherited": report["issues"]["numErrors"],
            "newFormatErrors": 0,
            "formatWarnings": report["issues"]["numWarnings"],
            "acceptance": "isolated review candidate; game integration pending",
        }
    )
manifest = {
    "character": "Witch",
    "scope": "L2–L10 separate review candidates",
    "originalSha256": hashlib.sha256(
        Path("source/original.glb").read_bytes()
    ).hexdigest(),
    "ranks": rows,
    "limitations": [
        "Original asset has 231 inherited glTF errors; full reports included.",
        "Continuous animation clearance, finisher/carrier integration, six-slot separation and physical-phone performance remain unverified.",
        "New reconstructed surfaces replace visible original clothing; original source geometry/binary remains stored.",
        "Studio images show actual selected GLBs; reference art is separate.",
    ],
}
Path("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
cards = "".join(
    f'<article><header><h2>{r["rank"]}</h2><span>{r["palette"]}</span></header><a class="preview" href="review/{r["rank"]}/{r["rank"]}-front.png"><img loading="lazy" data-rank="{r["rank"]}" src="review/{r["rank"]}/{r["rank"]}-front.png" alt="Actual {r["rank"]} model, front view"></a><footer><a href="{r["model"]}">Download GLB</a><a href="source/{r["rank"]}-reference.png">Reference art</a></footer></article>'
    for r in rows
)
views = [
    "front",
    "back",
    "side",
    "attack",
    "guard",
    "kick",
    "head",
    "high-rear",
    "fight",
]
buttons = "".join(
    f'<button data-view="{v}" class="{"active" if v == "front" else ""}">{v.replace("-", " ").title()}</button>'
    for v in views
)
html = (
    """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Witch · L2–L10 review</title><style>
*{box-sizing:border-box}body{margin:0;background:#121417;color:#eee;font:15px/1.5 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:34px;margin:0}p{color:#b9c0cb;max-width:850px}nav{position:sticky;top:0;z-index:2;background:#121417ee;padding:16px 0;display:flex;gap:8px;flex-wrap:wrap}button{padding:9px 14px;border:1px solid #414750;border-radius:7px;background:#242830;color:#ddd;cursor:pointer}button.active{background:#a0783e;color:white;border-color:#c6995d}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}article{background:#1c2025;border:1px solid #353a41;border-radius:10px;overflow:hidden}article header{display:flex;align-items:baseline;gap:12px;padding:12px 16px}h2{margin:0;font-size:23px}article span{color:#c9c3b7}.preview{display:block;background:#606060;text-align:center}img{width:100%;max-width:375px;display:block;margin:auto}footer{padding:14px;display:flex;justify-content:space-between}a{color:#ddbd8b}details{margin:28px 0;padding:18px;border:1px solid #414750;border-radius:8px}code{word-break:break-all}.note{font-size:13px;color:#aab0b9} @media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}main{padding:16px}}@media(max-width:500px){.grid{grid-template-columns:1fr}h1{font-size:28px}}</style><main>
<h1>Witch · L2–L10</h1><p>Nine rigged review candidates. L8–L10 use distinct closed helmets and full limb armour. The original rig, weapons and 38 animation clips are preserved.</p><p class="note">Actual exported-model renders · neutral lighting · 375 × 600 images. Fight view measures the visible character at 110 pixels high. Click any image for the full-size file.</p><nav>"""
    + buttons
    + """</nav><section class="grid">"""
    + cards
    + """</section><details><summary>Original Witch — matching pose and lighting</summary><a href="review/Original/Original-front.png"><img src="review/Original/Original-front.png" alt="Original Witch in matching trident pose"></a></details><details><summary>Review status and remaining work</summary><p>These are separate art candidates, not a deployed game replacement. Sampled deformation and preservation checks pass; they do not establish continuous collision clearance or phone performance. The original model's 231 format errors remain inherited. Close-up reconstruction softness and hand/weapon contact still merit integration review.</p><a href="HANDOFF.md">Developer handoff</a> · <a href="manifest.json">Hashes and validation manifest</a> · <a href="rank-matrix.md">Rank coverage matrix</a></details></main><script>
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{const view=button.dataset.view;document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b===button));document.querySelectorAll('img[data-rank]').forEach(img=>{const rank=img.dataset.rank;img.src=`review/${rank}/${rank}-${view}.png`;img.alt=`Actual ${rank} model, ${view} view`;img.parentElement.href=img.src;});}));</script></html>"""
)
Path("index.html").write_text(
    html.replace("source/L8-reference.png", "source/L8-transparent.png")
)
print("VERIFIED", len(rows), "models", sum(r["verifiedImages"] for r in rows), "images")
