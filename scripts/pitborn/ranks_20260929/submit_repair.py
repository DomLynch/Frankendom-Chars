import sys
import json
from pathlib import Path
from huggingface_hub import HfApi, get_token

api = HfApi()
repo = "Domlynch/frankendom-pitborn-ranks-20260929"
root = Path(__file__).resolve().parent.parent
c = api.upload_folder(
    repo_id=repo,
    repo_type="dataset",
    folder_path=root / "source",
    path_in_repo="source",
    allow_patterns=["*.py"],
)
bootstrap = (
    Path(root / "source/prior_job.txt")
    .read_text()
    .split("from huggingface_hub import HfApi,hf_hub_download")[0]
)
bootstrap += """from huggingface_hub import hf_hub_download
p=hf_hub_download('Domlynch/frankendom-pitborn-ranks-20260929','source/repair_job.py',repo_type='dataset',revision=os.environ['INPUT_REVISION'])
subprocess.run([sys.executable,p],check=True)
"""
j = api.run_job(
    image="python:3.13-slim-bookworm",
    command=["python", "-c", bootstrap],
    flavor="cpu-upgrade",
    timeout="20m",
    secrets={"HF_TOKEN": get_token()},
    env={
        "RANKS": ",".join(sys.argv[1:]),
        "INPUT_REVISION": c.oid,
        "HF_HUB_DISABLE_PROGRESS_BARS": "1",
    },
)
row = {"ranks": sys.argv[1:], "id": j.id, "revision": c.oid, "max_cpu_cost_usd": 0.01}
print(json.dumps(row), flush=True)
with (root / "checks/repair-jobs.jsonl").open("a") as f:
    f.write(json.dumps(row) + "\n")
