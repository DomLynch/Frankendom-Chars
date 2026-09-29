"""One bounded rank build; save each recoverable stage before rendering."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

api = HfApi()
repo = "Domlynch/frankendom-pitborn-ranks-20260929"
rank = os.environ["RANK"]
root = Path("/tmp/pitborn-" + rank)
root.mkdir(exist_ok=True)
os.chdir(root)
for x in ["source", "donors", "models", "checks", "previews"]:
    Path(x).mkdir(exist_ok=True)
names = [
    "pitborn.glb",
    "reconstruct.py",
    "fit_rank.py",
    "pack_preserved.py",
    "motion_math.py",
    "smooth_weights.py",
    "tether_fragments.py",
    "preserve_face.py",
    "add_sleeves.py",
    "check_candidate.py",
    "render_rank.py",
]
for name in names:
    shutil.copy2(
        hf_hub_download(
            repo,
            "source/" + name,
            repo_type="dataset",
            revision=os.environ["INPUT_REVISION"],
        ),
        "source/" + name,
    )


def run(*args, check=True):
    return subprocess.run([sys.executable, *args], check=check)


if rank != "L8":
    run("source/reconstruct.py")
    shutil.copy2(
        hf_hub_download(repo, f"donors/{rank}.glb", repo_type="dataset"),
        f"donors/{rank}.glb",
    )
    run("source/fit_rank.py")
    api.upload_folder(
        repo_id=repo,
        repo_type="dataset",
        folder_path="source",
        path_in_repo=f"batch/{rank}/source",
        allow_patterns=["*.blend", f"{rank}-fitted.glb"],
    )
    run(
        "source/pack_preserved.py",
        "source/pitborn.glb",
        f"source/{rank}-fitted.glb",
        "models/raw.glb",
    )
    run("source/smooth_weights.py", "models/raw.glb", "models/smooth.glb", "100")
    run("source/tether_fragments.py", "models/smooth.glb", "models/tethered.glb")
else:
    shutil.copy2(
        hf_hub_download(
            repo, "candidate-r6/models/pitborn-L8.glb", repo_type="dataset"
        ),
        "models/tethered.glb",
    )
if int(rank[1:]) < 8:
    run("source/preserve_face.py", "models/tethered.glb", "models/faced.glb")
    base = "models/faced.glb"
else:
    base = "models/tethered.glb"
final = f"models/pitborn-{rank}.glb"
run("source/add_sleeves.py", base, final)
result = run("source/check_candidate.py", final, check=False)
api.upload_folder(
    repo_id=repo,
    repo_type="dataset",
    folder_path="models",
    path_in_repo=f"batch/{rank}/models",
    allow_patterns=[f"pitborn-{rank}.glb*"],
)
api.upload_folder(
    repo_id=repo,
    repo_type="dataset",
    folder_path="checks",
    path_in_repo=f"batch/{rank}/checks",
)
run("source/render_rank.py")
api.upload_folder(
    repo_id=repo,
    repo_type="dataset",
    folder_path="previews",
    path_in_repo=f"batch/{rank}/previews",
)
print("RANK_FINISHED", rank, "CHECK_EXIT", result.returncode, flush=True)
raise SystemExit(result.returncode)
