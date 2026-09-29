"""Validate committed Shieldmaiden delivery evidence without cloud calls."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path


root = Path(__file__).resolve().parents[2] / "characters/shieldmaiden/ranks-20260929"
manifest = json.loads((root / "manifest.json").read_text())
assert {row["rank"] for row in manifest["ranks"]} == {
    f"L{rank}" for rank in range(2, 11)
}
assert len(manifest["ranks"]) == 9
views = {
    "front",
    "back",
    "left",
    "right",
    "head",
    "attack",
    "heavy",
    "guard",
    "kick",
    "fight",
}
clips = {"Armed", "Attack", "Heavy", "Guard", "Kick", "Roll"}
for row in manifest["ranks"]:
    folder = root / row["rank"]
    motion = json.loads((folder / "motion.json").read_text())
    preservation = json.loads((folder / "preservation.json").read_text())
    receipts = json.loads((folder / "render-receipts.json").read_text())
    assert motion["sha256"] == preservation["sha256"] == row["sha256"]
    assert preservation["originalSha256"] == manifest["source_sha256"]
    for field in [
        "originalBinaryPrefixUnchanged",
        "originalNodesExact",
        "originalSkinsExact",
        "originalAnimationsExact",
    ]:
        assert preservation[field], (row["rank"], field)
    assert preservation["clips"] == 25 and preservation["sourceJoints"] == 65
    assert motion["maxLongStretchedEdgeOccurrences"] == 0
    samples = defaultdict(lambda: defaultdict(set))
    for sample in motion["samples"]:
        assert sample["longStretchedEdgeOccurrences"] == 0
        samples[(sample["node"], sample["primitive"])][sample["clip"]].add(
            sample["time"]
        )
    assert samples
    for sampled_clips in samples.values():
        assert set(sampled_clips) == clips
        assert all(len(times) == 9 for times in sampled_clips.values())
    assert len(receipts) == 10
    assert {receipt["file"] for receipt in receipts} == {
        f"{row['rank']}-{view}.png" for view in views
    }
    for receipt in receipts:
        assert receipt["model_sha256"] == row["sha256"]
        assert (
            hashlib.sha256((folder / receipt["file"]).read_bytes()).hexdigest()
            == receipt["image_sha256"]
        )
        if receipt["file"].endswith("-fight.png"):
            assert abs(receipt["figure_height_px"] - 110) < 0.01
    assert len(row["scene_sha256"]) == 64
print(
    "PASS: nine Shieldmaiden candidates, exact source preservation, 54 poses each, 90 hash-linked views"
)
