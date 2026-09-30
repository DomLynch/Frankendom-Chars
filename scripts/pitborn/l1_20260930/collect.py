"""Download immutable L1 outputs and build an actual-export review sheet."""

import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[3]
work = root / "work/pitborn-l1-20260930"
repo = "Domlynch/frankendom-pitborn-l1-20260930"
revision = HfApi().repo_info(repo, repo_type="dataset").sha
snapshot_download(
    repo,
    repo_type="dataset",
    revision=revision,
    allow_patterns=["models/*", "checks/*", "previews/*", "source/*", "donors/*"],
    local_dir=work,
)
(work / "download.json").write_text(
    json.dumps({"repo": repo, "revision": revision}, indent=2)
)
model = work / "models/pitborn-L1.glb"
sha = hashlib.sha256(model.read_bytes()).hexdigest()
receipts = json.loads((work / "previews/L1/render-receipts.json").read_text())
for receipt in receipts:
    assert receipt["model_sha256"] == sha
    image = work / "previews/L1" / receipt["file"]
    assert hashlib.sha256(image.read_bytes()).hexdigest() == receipt["image_sha256"]
canvas = Image.new("RGB", (1500, 1280), "#252525")
draw = ImageDraw.Draw(canvas)
views = ["front", "back", "left", "right", "head", "attack", "guard", "kick"]
for i, view in enumerate(views):
    image = Image.open(work / f"previews/L1/L1-{view}.png").convert("RGB")
    x, y = (i % 4) * 375, (i // 4) * 640
    canvas.paste(image, (x, y + 30))
    draw.text((x + 12, y + 10), view, fill="white")
canvas.save(work / "L1-review.jpg", quality=92)
print("COLLECTED", sha, len(receipts), "views")
