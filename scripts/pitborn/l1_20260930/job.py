"""One bounded L1 job; recoverable outputs are persisted before renders."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download, hf_hub_download

repo = "Domlynch/frankendom-pitborn-l1-20260930"
api = HfApi()
root = Path("/tmp/pitborn-L1")
root.mkdir(exist_ok=True)
os.chdir(root)
os.environ["RANK"] = "L1"
snapshot_download(
    repo,
    repo_type="dataset",
    revision=os.environ["INPUT_REVISION"],
    allow_patterns=["source/*", "references/*"],
    local_dir=root,
)
for folder in ["models", "donors", "checks", "previews"]:
    Path(folder).mkdir(exist_ok=True)


def run(*args, check=True):
    return subprocess.run([sys.executable, *args], check=check)


def save(folder, patterns=None):
    api.upload_folder(
        repo_id=repo,
        repo_type="dataset",
        folder_path=folder,
        path_in_repo=folder,
        allow_patterns=patterns,
    )


run("source/reconstruct.py")
shutil.copy2(
    hf_hub_download(repo, "donors/L1.glb", repo_type="dataset"), "donors/L1.glb"
)
run("source/fit_rank.py")
save("source", ["*.blend", "*fitted.glb"])
run(
    "source/pack_preserved.py",
    "source/pitborn.glb",
    "source/L1-fitted.glb",
    "models/raw.glb",
)
run("source/smooth_weights.py", "models/raw.glb", "models/smooth.glb", "100")
run("source/tether_fragments.py", "models/smooth.glb", "models/tethered.glb")
run("source/preserve_face.py", "models/tethered.glb", "models/faced.glb")
run("source/repair_collar.py", "models/faced.glb", "models/pitborn-L1.glb")
result = run("source/check_candidate.py", "models/pitborn-L1.glb", check=False)
save("models", ["pitborn-L1.glb*"])
save("checks")
run("source/render_rank.py")
save("source", ["pitborn-L1-final.blend"])
save("previews")
print("L1_FINISHED CHECK_EXIT", result.returncode, flush=True)
raise SystemExit(result.returncode)
