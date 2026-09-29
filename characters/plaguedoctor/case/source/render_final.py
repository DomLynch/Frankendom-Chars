"""Capture final GLBs after exact original animation restoration."""

import json
import sys
from pathlib import Path
from huggingface_hub import HfApi, get_token

ROOT = Path(__file__).resolve().parents[1]
REPO = "Domlynch/frankendom-plaguedoctor-pilot-20260928"
ranks = [int(value) for value in sys.argv[1:]] or list(range(2, 11))
prefix = "final-renders" if len(ranks) > 1 else "final-L8"
api = HfApi()
api.upload_folder(
    folder_path=str(ROOT / "models"),
    path_in_repo="final",
    repo_id=REPO,
    repo_type="dataset",
    allow_patterns=[f"plaguedoctor-L{r}.glb" for r in ranks],
)
code = (
    (ROOT / "source/render_remote.py")
    .read_text()
    .replace(
        '[("original", "original.glb"), ("L10", "proof-v2.glb")]',
        repr([(f"L{r}", f"final/plaguedoctor-L{r}.glb") for r in ranks]),
    )
    .replace("proof-v2/", prefix + "/")
)
command = (
    "apt-get update -qq && apt-get install -y -qq libgl1 libxrender1 libxi6 libxkbcommon0 libsm6 libgomp1 >/dev/null && pip install -q bpy==4.5.3 huggingface_hub && python - <<'PYJOB'\n"
    + code
    + "\nPYJOB"
)
job = api.run_job(
    image="python:3.11-bookworm",
    command=["bash", "-lc", command],
    flavor="cpu-upgrade",
    timeout="20m",
    secrets={"HF_TOKEN": get_token()},
    env={"HF_HUB_DISABLE_XET": "1", "HF_HUB_DISABLE_PROGRESS_BARS": "1"},
)
receipt = {
    "id": job.id,
    "url": job.url,
    "timeout": 1200,
    "scope": "54 reimported final GLB views with original animation payloads",
}
(ROOT / f"job-{prefix}.json").write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
