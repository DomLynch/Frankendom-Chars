"""Render the verified repaired model without reconstructing or refitting it."""

import os
import bpy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

repo = "Domlynch/frankendom-pitborn-l1-20260930"
root = Path("/tmp/pitborn-L1-final")
root.mkdir(exist_ok=True)
os.chdir(root)
snapshot_download(
    repo,
    repo_type="dataset",
    revision=os.environ["INPUT_REVISION"],
    local_dir=root,
    allow_patterns=["source/*.py", "source/pitborn.glb", "models/pitborn-L1.glb"],
)
os.environ["RANK"] = "L1"
Path("checks").mkdir(exist_ok=True)
subprocess.run(
    [sys.executable, "source/check_candidate.py", "models/pitborn-L1.glb"], check=True
)
subprocess.run([sys.executable, "source/render_rank.py"], check=True)

scene_path = Path("source/pitborn-L1-final.blend")
model_hash = hashlib.sha256(Path("models/pitborn-L1.glb").read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(scene_path.resolve()))
assert bpy.context.scene["authoritative_glb_sha256"] == model_hash
Path("checks/final-scene.json").write_text(
    json.dumps(
        {
            "model_sha256": model_hash,
            "scene_sha256": hashlib.sha256(scene_path.read_bytes()).hexdigest(),
            "embedded_model_hash_verified": True,
        },
        indent=2,
    )
)
api = HfApi()
for folder, patterns in [
    ("source", ["pitborn-L1-final.blend"]),
    ("checks", None),
    ("previews", None),
]:
    api.upload_folder(
        repo_id=repo,
        repo_type="dataset",
        folder_path=folder,
        path_in_repo=folder,
        allow_patterns=patterns,
    )
print("FINAL_L1_RENDERED", flush=True)
