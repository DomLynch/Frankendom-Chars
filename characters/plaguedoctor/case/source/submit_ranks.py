"""Submit bounded remote fitting and exported-file captures for ready donors."""

import json
import sys
from pathlib import Path

from huggingface_hub import HfApi, get_token

ROOT = Path(__file__).resolve().parents[1]
REPO = "Domlynch/frankendom-plaguedoctor-pilot-20260928"
RANKS = [int(value) for value in sys.argv[1:]]
SCALES = {2: 1.84, 3: 1.84, 4: 1.84, 5: 1.84, 6: 1.84, 7: 1.87, 8: 1.94, 9: 1.98}
api = HfApi()
blocks = []
for rank in RANKS:
    label = f"L{rank}"
    donor = ROOT / f"src/assets/source/creatures/plaguedoctor-{label}-donor.glb"
    assert donor.exists(), donor
    api.upload_file(
        path_or_fileobj=str(donor),
        path_in_repo=f"{label}-donor.glb",
        repo_id=REPO,
        repo_type="dataset",
    )
    build = (ROOT / "source/build_v3.py").read_text()
    if rank <= 3:
        build = build.replace(
            "for m in donor.data.materials:",
            "for mat in donor.data.materials:\n"
            '    shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")\n'
            '    for link in list(shader.inputs["Metallic"].links):\n'
            "        mat.node_tree.links.remove(link)\n"
            '    shader.inputs["Metallic"].default_value = 0\n'
            "for m in donor.data.materials:",
        )
    build = (
        build.replace("L10", label)
        .replace("scale = 2.03", f"scale = {SCALES[rank]}")
        .replace("proof-v3/", f"ladder/{label}/")
        .replace("os._exit(0)", "")
    )
    render = (ROOT / "source/render_remote.py").read_text()
    render = render.replace(
        '[("original", "original.glb"), ("L10", "proof-v2.glb")]', '[("L10", "unused")]'
    )
    render = render.replace(
        "with urllib.request.urlopen(request, timeout=90) as response:\n        path.write_bytes(response.read())",
        'path.write_bytes(Path("/tmp/plague/plaguedoctor-L10.glb").read_bytes())',
    )
    render = (
        render.replace("L10", label)
        .replace("proof-v2/", f"ladder/{label}/")
        .replace("os._exit(0)", "")
    )
    blocks.extend([build, render])
code = "\n".join(blocks) + '\nprint("BATCH_COMPLETE",flush=True)\nos._exit(0)\n'
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
    "ranks": RANKS,
    "timeout": 1200,
    "scales": {rank: SCALES[rank] for rank in RANKS},
    "scope": "Candidate fitting and six reimported GLB captures each; visual review required",
}
(ROOT / f"job-ranks-{'-'.join(map(str, RANKS))}.json").write_text(
    json.dumps(receipt, indent=2)
)
print(json.dumps(receipt), flush=True)
