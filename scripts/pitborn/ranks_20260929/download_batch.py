"""Download immutable per-rank outputs, preserving the cloud revision."""

from huggingface_hub import HfApi, hf_hub_download
from pathlib import Path
import shutil
import json
import sys

repo = "Domlynch/frankendom-pitborn-ranks-20260929"
api = HfApi()
root = Path(__file__).resolve().parent.parent
rev = api.repo_info(repo, repo_type="dataset").sha
files = api.list_repo_files(repo, repo_type="dataset", revision=rev)
for rank in sys.argv[1:]:
    prefix = f"batch/{rank}/"
    found = [p for p in files if p.startswith(prefix)]
    for path in found:
        target = root / "delivery" / path.removeprefix(prefix)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            hf_hub_download(repo, path, repo_type="dataset", revision=rev), target
        )
    print(rank, len(found), rev, flush=True)
(root / "checks/download-revision.json").write_text(
    json.dumps({"revision": rev, "ranks": sys.argv[1:]}, indent=2)
)
