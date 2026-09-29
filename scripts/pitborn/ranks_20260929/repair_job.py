"""Repair saved candidates without new reconstruction, then revalidate and render."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

api = HfApi()
repo = "Domlynch/frankendom-pitborn-ranks-20260929"
root = Path("/tmp/pitborn-final")
root.mkdir(exist_ok=True)
os.chdir(root)
sys.path.insert(0, str(root / "source"))
for d in ["source", "models", "checks", "previews"]:
    Path(d).mkdir(exist_ok=True)
for name in [
    "pitborn.glb",
    "repair_collar.py",
    "repair_hand.py",
    "refine_sleeves.py",
    "pack_preserved.py",
    "motion_math.py",
    "check_candidate.py",
    "render_rank.py",
]:
    shutil.copy2(
        hf_hub_download(
            repo,
            "source/" + name,
            repo_type="dataset",
            revision=os.environ["INPUT_REVISION"],
        ),
        "source/" + name,
    )
for rank in os.environ["RANKS"].split(","):
    os.environ["RANK"] = rank
    final = f"models/pitborn-{rank}.glb"
    shutil.copy2(
        hf_hub_download(
            repo, f"batch/{rank}/models/pitborn-{rank}.glb", repo_type="dataset"
        ),
        final,
    )
    if rank in ["L3", "L4"]:
        subprocess.run(
            [sys.executable, "source/repair_hand.py", final, final], check=True
        )
    if int(rank[1:]) < 8:
        subprocess.run(
            [sys.executable, "source/repair_collar.py", final, final], check=True
        )
    elif rank == "L8":
        subprocess.run(
            [sys.executable, "source/refine_sleeves.py", final, final], check=True
        )
    if rank == "L9":
        from pack_preserved import read, write

        g, binary = read(final)
        n = next(n for n in g["nodes"] if n.get("name", "").endswith("_Armour"))
        for primitive in g["meshes"][n["mesh"]]["primitives"]:
            material = g["materials"][primitive["material"]]["pbrMetallicRoughness"]
            material["metallicFactor"] = 0.45
            material["roughnessFactor"] = 0.9
            material["baseColorFactor"] = [0.75, 1, 0.8, 1]
        write(final, g, binary)
    result = subprocess.run([sys.executable, "source/check_candidate.py", final])
    api.upload_folder(
        repo_id=repo,
        repo_type="dataset",
        folder_path="models",
        path_in_repo=f"final/{rank}/models",
        allow_patterns=[f"pitborn-{rank}.glb*"],
    )
    api.upload_folder(
        repo_id=repo,
        repo_type="dataset",
        folder_path="checks",
        path_in_repo=f"final/{rank}/checks",
        allow_patterns=[f"pitborn-{rank}*"],
    )
    subprocess.run([sys.executable, "source/render_rank.py"], check=True)
    api.upload_folder(
        repo_id=repo,
        repo_type="dataset",
        folder_path=f"previews/{rank}",
        path_in_repo=f"final/{rank}/previews/{rank}",
    )
    print("FINAL_FINISHED", rank, "CHECK_EXIT", result.returncode, flush=True)
