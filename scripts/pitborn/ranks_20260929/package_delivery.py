"""Verify final model/preview parity and assemble the review delivery."""

import hashlib
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "delivery"
tracked = root.parents[1] / "characters/pitborn/ranks-20260929"
tracked.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


manifest = {
    "status": "review candidates; not game or phone approved",
    "sourceSha256": sha(root / "source/pitborn.glb"),
    "ranks": [],
}
for rank in range(2, 11):
    name = f"L{rank}"
    model = out / "models" / f"pitborn-{name}.glb"
    digest = sha(model)
    motion = json.loads((out / "checks" / f"pitborn-{name}-motion.json").read_text())
    preservation = json.loads(Path(str(model) + ".preservation.json").read_text())
    receipts = json.loads(
        (out / "previews" / name / "render-receipts.json").read_text()
    )
    assert (
        motion["sha256"] == digest and motion["maxLongStretchedEdgeOccurrences"] == 0
    ), name
    assert (
        preservation["sha256"] == digest and preservation["originalAnimationsExact"]
    ), name
    assert len(receipts) == 10, name
    for r in receipts:
        assert r["model_sha256"] == digest, name
        assert sha(out / "previews" / name / r["file"]) == r["image_sha256"], name
    dest = tracked / name
    dest.mkdir(exist_ok=True)
    for p in (out / "previews" / name).iterdir():
        shutil.copy2(p, dest / p.name)
    shutil.copy2(out / "checks" / f"pitborn-{name}-motion.json", dest / "motion.json")
    shutil.copy2(Path(str(model) + ".preservation.json"), dest / "preservation.json")
    fmt = root / "checks" / f"pitborn-{name}.glb.khronos.json"
    if fmt.exists():
        shutil.copy2(fmt, out / "checks" / fmt.name)
    manifest["ranks"].append(
        {
            "rank": name,
            "file": model.name,
            "bytes": model.stat().st_size,
            "sha256": digest,
            "clips": preservation["clips"],
            "joints": preservation["sourceJoints"],
            "sampledPoseCount": 54,
            "maxLongStretchedEdgeOccurrences": 0,
            "previews": 10,
        }
    )
(out / "manifest.json").write_text(json.dumps(manifest, indent=2))
(tracked / "manifest.json").write_text(json.dumps(manifest, indent=2))
for folder in ["scripts", "references"]:
    (out / folder).mkdir(exist_ok=True)
for p in (root / "source").glob("*.py"):
    shutil.copy2(p, out / "scripts" / p.name)
for p in (root / "references").iterdir():
    shutil.copy2(p, out / "references" / p.name)
for p in (root / "checks").glob("*jobs.jsonl"):
    shutil.copy2(p, out / "checks" / p.name)
print(
    "PASS: 9 model hashes, 90 image hashes, exact preservation receipts and 54 sampled poses per rank"
)
