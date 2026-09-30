"""Verify recruit evidence without running Blender or paid cloud work."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path


root = Path(__file__).resolve().parents[2] / "characters/shieldmaiden/l1-20260930"
manifest = json.loads((root / "manifest.json").read_text())
preservation = json.loads((root / "preservation.json").read_text())
motion = json.loads((root / "motion.json").read_text())
receipts = json.loads((root / "render-receipts.json").read_text())
assert manifest["model_sha256"] == preservation["sha256"] == motion["sha256"]
assert manifest["source_sha256"] == preservation["originalSha256"]
for key in [
    "originalBinaryPrefixUnchanged",
    "originalNodesExact",
    "originalSkinsExact",
    "originalAnimationsExact",
]:
    assert preservation[key]
assert preservation["clips"] == 25 and preservation["sourceJoints"] == 65
assert motion["maxLongStretchedEdgeOccurrences"] == 0
samples = defaultdict(lambda: defaultdict(set))
for sample in motion["samples"]:
    assert sample["longStretchedEdgeOccurrences"] == 0
    samples[(sample["node"], sample["primitive"])][sample["clip"]].add(sample["time"])
assert samples
for clips in samples.values():
    assert set(clips) == {"Armed", "Attack", "Heavy", "Guard", "Kick", "Roll"}
    assert all(len(times) == 9 for times in clips.values())
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
assert len(receipts) == 10
assert {r["file"] for r in receipts} == {f"L1-{view}.png" for view in views}
for receipt in receipts:
    assert receipt["model_sha256"] == manifest["model_sha256"]
    assert (
        hashlib.sha256((root / receipt["file"]).read_bytes()).hexdigest()
        == receipt["image_sha256"]
    )
    if receipt["file"] == "L1-fight.png":
        assert abs(receipt["figure_height_px"] - 110) < 0.01
assert manifest["scene_embedded_model_sha256"] == manifest["model_sha256"]
assert manifest["format_errors_match_original"]
print(
    "PASS: Shieldmaiden L1 original rig/clips, 54 poses, ten hash-linked views and scene receipt"
)
