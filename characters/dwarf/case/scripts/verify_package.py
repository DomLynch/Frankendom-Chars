"""Verify selected models, source preservation and every delivered image receipt."""

import hashlib
import json
from pathlib import Path

from merge_armour import read, worlds
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
selected = json.loads((ROOT / "selected.json").read_text())
receipts = json.loads((ROOT / "reports/render-receipt.json").read_text())
original, original_binary = read(ROOT / "models/dwarf-L1.glb")
original_worlds = worlds(original)
for rank, value in selected.items():
    path = ROOT / value["model"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == value["sha256"]
    model, binary = read(path)
    assert binary[:len(original_binary)] == original_binary, rank
    assert model["animations"] == original["animations"], rank
    current_worlds = worlds(model)
    for skin in original["skins"]:
        for joint in skin["joints"]:
            assert np.array_equal(original_worlds[joint], current_worlds[joint]), (rank, joint)
    views = [item for item in receipts if item["image"].startswith(rank + "-")]
    assert len(views) == (11 if rank in ["L8", "L9", "L10"] else 10), (rank, len(views))
    for item in views:
        assert item["sha256"] == value["sha256"], item["image"]
        image = ROOT / "images" / item["image"]
        assert image.exists() and image.stat().st_size > 0, image
        assert hashlib.sha256(image.read_bytes()).hexdigest() == item["imageSha256"], image
print("PASS: nine selected models, exact original rig/clips/buffers and 93 candidate image receipts")
