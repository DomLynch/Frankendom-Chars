from huggingface_hub import HfApi, get_token
from pathlib import Path
import json
import sys

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
bootstrap = bootstrap.replace(
    "'scipy==1.16.3'", "'scipy==1.16.3','gradio_client==2.7.1','requests==2.32.5'"
)
bootstrap += """from huggingface_hub import hf_hub_download
p=hf_hub_download('Domlynch/frankendom-pitborn-ranks-20260929','source/batch_job.py',repo_type='dataset',revision=os.environ['INPUT_REVISION'])
subprocess.run([sys.executable,p],check=True)
"""
for rank in sys.argv[1:]:
    j = api.run_job(
        image="python:3.13-slim-bookworm",
        command=["python", "-c", bootstrap],
        flavor="cpu-upgrade",
        timeout="30m",
        secrets={"HF_TOKEN": get_token()},
        env={
            "RANK": rank,
            "INPUT_REVISION": c.oid,
            "HF_HUB_DISABLE_PROGRESS_BARS": "1",
        },
    )
    row = {"rank": rank, "id": j.id, "revision": c.oid, "max_cpu_cost_usd": 0.015}
    print(json.dumps(row), flush=True)
    with (root / "checks/batch-jobs.jsonl").open("a") as f:
        f.write(json.dumps(row) + "\n")
