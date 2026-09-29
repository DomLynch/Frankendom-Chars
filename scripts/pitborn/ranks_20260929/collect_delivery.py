"""Collect saved results in parallel; final revisions override first-pass artifacts."""

import sys
import json
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from huggingface_hub import HfApi, hf_hub_download

repo = "Domlynch/frankendom-pitborn-ranks-20260929"
api = HfApi()
root = Path(__file__).resolve().parent.parent
rev = api.repo_info(repo, repo_type="dataset").sha
files = api.list_repo_files(repo, repo_type="dataset", revision=rev)
selected = {}
for rank in sys.argv[1:]:
    for prefix in [f"batch/{rank}/", f"final/{rank}/"]:
        for p in files:
            if p.startswith(prefix):
                relative = p.removeprefix(prefix)
                if relative.endswith(".blend1"):
                    continue
                selected[relative] = p
    for p in [f"donors/{rank}.glb", f"checks/{rank}-reconstruction.json"]:
        if p in files:
            selected[p] = p
items = sorted(
    selected.items(), key=lambda x: ("previews" not in x[0], "checks" not in x[0], x[0])
)


def fetch(item):
    relative, path = item
    target = root / "delivery" / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    cached = hf_hub_download(repo, path, repo_type="dataset", revision=rev)
    shutil.copy2(cached, target)
    return relative


with ThreadPoolExecutor(8) as pool:
    for n, relative in enumerate(pool.map(fetch, items), 1):
        if n % 10 == 0 or n == len(items):
            print(n, "/", len(items), relative, flush=True)
(root / "delivery/cloud-revision.json").write_text(
    json.dumps({"revision": rev, "files": selected}, indent=2)
)
