# /// script
# dependencies = ["huggingface_hub==1.33.0", "gradio_client==2.7.1", "Pillow==12.1.1", "requests==2.32.5"]
# ///
"""Bounded shared-Space reconstruction; persist before any fitting/rendering."""

import base64
import hashlib
import json
import os
import time
from pathlib import Path
import requests
from gradio_client import Client
from huggingface_hub import HfApi, hf_hub_download

REPO = "Domlynch/frankendom-pitborn-ranks-20260929"
api = HfApi()
probe = b"pitborn-remote-write-read"
c = api.upload_file(
    path_or_fileobj=probe,
    path_in_repo="checks/sdk-job-probe.txt",
    repo_id=REPO,
    repo_type="dataset",
)
assert (
    Path(
        hf_hub_download(
            REPO, "checks/sdk-job-probe.txt", repo_type="dataset", revision=c.oid
        )
    ).read_bytes()
    == probe
)
print("JOB_STORAGE_PASS", c.oid, flush=True)
rank = os.environ.get("RANK", "L8")
png = Path(
    hf_hub_download(
        REPO,
        f"references/{rank}.png",
        repo_type="dataset",
        revision=os.environ["INPUT_REVISION"],
    )
).read_bytes()
filedata = {
    "path": None,
    "url": "data:image/png;base64," + base64.b64encode(png).decode(),
    "size": len(png),
    "orig_name": rank + ".png",
    "mime_type": "image/png",
    "is_stream": False,
    "meta": {"_type": "gradio.FileData"},
}
space = api.space_info("microsoft/TRELLIS.2")
print("SPACE_REVISION", space.sha, flush=True)
client = Client(
    "microsoft/TRELLIS.2",
    token=os.environ["HF_TOKEN"],
    verbose=False,
    httpx_kwargs={"follow_redirects": True, "timeout": 90},
    download_files=False,
)
client.httpx_kwargs.pop("follow_redirects", None)
client.predict(api_name="/start_session")
params = dict(
    seed=290938,
    resolution="1024",
    ss_guidance_strength=7.5,
    ss_guidance_rescale=0.7,
    ss_sampling_steps=12,
    ss_rescale_t=5.0,
    shape_slat_guidance_strength=7.5,
    shape_slat_guidance_rescale=0.5,
    shape_slat_sampling_steps=12,
    shape_slat_rescale_t=3.0,
    tex_slat_guidance_strength=1.0,
    tex_slat_guidance_rescale=0.0,
    tex_slat_sampling_steps=12,
    tex_slat_rescale_t=3.0,
)
t = time.time()
client.predict(image=filedata, api_name="/image_to_3d", **params)
print("GENERATED_SECONDS", round(time.time() - t, 1), flush=True)
result = client.predict(
    decimation_target=100000, texture_size=2048, api_name="/extract_glb"
)


def urls(value):
    if isinstance(value, str) and value.startswith("http") and ".glb" in value:
        yield value
    elif isinstance(value, dict):
        if value.get("url") and ".glb" in value["url"]:
            yield value["url"]
        else:
            for x in value.values():
                yield from urls(x)
    elif isinstance(value, (tuple, list)):
        for x in value:
            yield from urls(x)


url = next(urls(result))
r = requests.get(url, timeout=120)
r.raise_for_status()
assert r.content[:4] == b"glTF"
model = r.content
api.upload_file(
    path_or_fileobj=model,
    path_in_repo=f"donors/{rank}.glb",
    repo_id=REPO,
    repo_type="dataset",
)
receipt = dict(
    rank=rank,
    model_sha256=hashlib.sha256(model).hexdigest(),
    model_bytes=len(model),
    reference_sha256=hashlib.sha256(png).hexdigest(),
    space_revision=space.sha,
    parameters=params,
    target_triangles=100000,
    texture_size=2048,
    elapsed_seconds=round(time.time() - t, 1),
)
api.upload_file(
    path_or_fileobj=json.dumps(receipt, indent=2).encode(),
    path_in_repo=f"checks/{rank}-reconstruction.json",
    repo_id=REPO,
    repo_type="dataset",
)
print("DONOR_SAVED", json.dumps(receipt), flush=True)
