"""Verify committed Pitborn candidate evidence; no cloud calls or paid work."""

import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2] / "characters/pitborn/ranks-20260929"
manifest = json.loads((root / "manifest.json").read_text())
assert {r["rank"] for r in manifest["ranks"]} == {f"L{i}" for i in range(2, 11)}
for row in manifest["ranks"]:
    folder = root / row["rank"]
    motion = json.loads((folder / "motion.json").read_text())
    preservation = json.loads((folder / "preservation.json").read_text())
    receipts = json.loads((folder / "render-receipts.json").read_text())
    assert motion["sha256"] == preservation["sha256"] == row["sha256"]
    assert motion["maxLongStretchedEdgeOccurrences"] == 0
    assert (
        preservation["originalAnimationsExact"] and preservation["originalSkinsExact"]
    )
    assert preservation["clips"] == 25 and preservation["sourceJoints"] == 65
    assert len(receipts) == 10
    for image in receipts:
        assert image["model_sha256"] == row["sha256"]
        assert (
            hashlib.sha256((folder / image["file"]).read_bytes()).hexdigest()
            == image["image_sha256"]
        )
print(
    "PASS: Pitborn L2-L10 preservation/deformation receipts and 90 model-linked previews"
)
