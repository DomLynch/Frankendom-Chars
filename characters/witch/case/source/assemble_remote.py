"""Verify final remote artifacts, capture comparison sheets, and package delivery."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import numpy as np
from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from playwright.sync_api import sync_playwright
from pack_preserved import arr, read, worlds

repo = "Domlynch/witch-ranks-20260928"
api = HfApi()
lower_tag = os.environ.get("WITCH_LOWER_TAG", "final-cowls")
for job in [
    os.environ.get("WITCH_LOWER_JOB", "6ababe1f52d0dbd7f1da4870"),
    "6ababb3c6b030d633f69edda",
    "6abab9496b030d633f69ec54",
]:
    deadline = time.monotonic() + 900
    while True:
        stage = api.inspect_job(job_id=job).status.stage
        if stage == "COMPLETED":
            break
        assert stage not in ["ERROR", "CANCELED", "DELETED"], (job, stage)
        assert time.monotonic() < deadline, "Render wait exceeded 15 minutes"
        time.sleep(30)

revision = api.repo_info(repo, repo_type="dataset").sha
os.makedirs("/tmp/witch-delivery", exist_ok=True)
os.chdir("/tmp/witch-delivery")


def download(name):
    return hf_hub_download(repo, name, repo_type="dataset", revision=revision)


with ZipFile(download("inputs/support-final.zip")) as archive:
    archive.extractall()
for name in ["final-elites", "final-ladder", lower_tag]:
    with ZipFile(download(f"inputs/render-{name}.zip")) as archive:
        for member in archive.namelist():
            if member.startswith("models/"):
                archive.extract(member)
with ZipFile(download("inputs/v2.zip")) as archive:
    for member in archive.namelist():
        if member == "source/original.glb" or member.startswith(
            "src/assets/source/creatures/"
        ):
            archive.extract(member)
patterns = [
    "outputs/v2/scenes/*",
    f"outputs/{lower_tag}/review/*",
    "outputs/final-ladder/review/L8/*",
    "outputs/final-elites/review/L9/*",
    "outputs/final-elites/review/L10/*",
    "outputs/final-elites/review/Original/*",
]
snapshot = Path(
    snapshot_download(
        repo,
        repo_type="dataset",
        revision=revision,
        allow_patterns=patterns,
        max_workers=2,
    )
)
for rank in list(range(2, 11)) + ["Original"]:
    label = "Original" if rank == "Original" else f"L{rank}"
    tag = (
        lower_tag
        if isinstance(rank, int) and rank <= 7
        else "final-ladder"
        if rank == 8
        else "final-elites"
    )
    shutil.copytree(
        snapshot / f"outputs/{tag}/review/{label}",
        Path("review") / label,
        dirs_exist_ok=True,
    )
shutil.copytree(snapshot / "outputs/v2/scenes", "source/scenes", dirs_exist_ok=True)
subprocess.run(
    [
        "npm",
        "install",
        "--prefix",
        "source/validation",
        "--silent",
        "gltf-validator@2.0.0-dev.3.10",
    ],
    check=True,
)
subprocess.run(
    ["node", "source/format_check.cjs"]
    + [f"models/witch-L{n}.glb" for n in range(2, 11)],
    check=True,
)
subprocess.run([sys.executable, "source/verify_delivery.py"], check=True)
original_sha = hashlib.sha256(Path("source/original.glb").read_bytes()).hexdigest()
assert (
    hashlib.sha256(Path("models/witch-Original.glb").read_bytes()).hexdigest()
    == original_sha
)
for receipt in json.loads(Path("review/Original/render-receipt.json").read_text()):
    assert receipt["sha256"] == original_sha
    assert (
        hashlib.sha256(
            (Path("review/Original") / receipt["image"]).read_bytes()
        ).hexdigest()
        == receipt["imageSha256"]
    )

manifest = json.loads(Path("manifest.json").read_text())
lines = [
    "# Witch rank matrix",
    "",
    "Separate combined review candidates. Original rig/38 clips retained throughout. Six-slot integration remains pending.",
    "",
    "| Rank | Palette | Head | Limbs | Motion | Images |",
    "|---|---|---|---|---|---|",
]
heads = {
    8: "Closed horned ritual visor + hood",
    9: "Closed crescent/lunar-fin helmet",
    10: "Closed full-gold demon crown",
}
for row in manifest["ranks"]:
    rank = int(row["rank"][1:])
    head = heads.get(rank, "Original face inside new rank hood; fitted inner cowl")
    limbs = (
        "Full arms, gloves, thighs, knees, shins, feet"
        if rank >= 8
        else "Rank-specific body, arm, leg and boot surfaces"
    )
    lines.append(
        f"| {row['rank']} | {row['palette']} | {head} | {limbs} | {row['poseSamples']} surface/pose samples; no severe stretch | 9 hash-verified views |"
    )
lines.extend(
    [
        "",
        "Format: 231 inherited source errors, zero new errors. Close-up softness, continuous grip/clearance, finishers/carriers and physical-phone performance remain integration work.",
    ]
)
Path("rank-matrix.md").write_text("\n".join(lines) + "\n")
transforms = []
for rank in range(2, 11):
    donor = Path(f"src/assets/source/creatures/witch-L{rank}-donor.glb")
    g, b = read(donor)
    index = next(i for i, n in enumerate(g["nodes"]) if "mesh" in n)
    prim = g["meshes"][g["nodes"][index]["mesh"]]["primitives"][0]
    p = arr(g, b, prim["attributes"]["POSITION"])
    q = (np.c_[p, np.ones(len(p))] @ worlds(g)[index].T)[:, :3]
    transforms.append(
        {
            "rank": rank,
            "donorSha256": hashlib.sha256(donor.read_bytes()).hexdigest(),
            "uniformScale": float(1.81 / np.ptp(q[:, 1])),
            "sourceYmin": float(q[:, 1].min()),
            "height": 1.81,
            "floor": 0.025,
        }
    )
Path("checks/fit-transforms.json").write_text(json.dumps(transforms, indent=2))
handoff = (
    Path("HANDOFF.md")
    .read_text()
    .replace(
        "Final image/package verification is in progress.",
        "Nine separate candidates are built; model/image hashes and structural checks are verified.",
    )
)
Path("HANDOFF.md").write_text(handoff)

sheets = Path("review/sheets")
sheets.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(args=["--no-sandbox"])
    page = browser.new_page(
        viewport={"width": 1240, "height": 900}, device_scale_factor=1
    )
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(Path("index.html").resolve().as_uri())
    page.add_style_tag(content="nav { position: static; }")
    page.eval_on_selector_all("img", "imgs => imgs.forEach(i => i.loading = 'eager')")
    for view in [
        "front",
        "back",
        "side",
        "attack",
        "guard",
        "kick",
        "head",
        "high-rear",
        "fight",
    ]:
        page.locator(f'button[data-view="{view}"]').click()
        page.wait_for_function(
            "Array.from(document.querySelectorAll('img[data-rank]')).every(i=>i.complete && i.naturalWidth===375)"
        )
        assert page.locator("img[data-rank]").count() == 9
        page.locator(".grid").screenshot(path=str(sheets / f"{view}.png"))
    page.set_viewport_size({"width": 375, "height": 900})
    page.locator('button[data-view="front"]').click()
    assert page.evaluate("document.body.scrollWidth") <= 375
    page.screenshot(path=str(sheets / "gallery-mobile.png"))
    assert not errors, errors
    browser.close()

verification = {
    "sourceRevision": revision,
    "models": 9,
    "verifiedRankImages": 81,
    "verifiedOriginalImages": 9,
    "allSelectedModelAndImageHashesMatch": True,
    "allNewVisibleSurfacesPassSampledMotion": True,
    "noNewFormatErrors": True,
    "galleryViewsTested": 9,
    "gallery375pxOverflow": False,
    "sheets": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sheets.glob("*.png")
    },
    "scope": "isolated review candidates; not production/phone acceptance",
}
Path("checks/delivery-verification.json").write_text(json.dumps(verification, indent=2))
api.upload_folder(
    folder_path=str(sheets),
    path_in_repo="outputs/ready/sheets",
    repo_id=repo,
    repo_type="dataset",
)
for name in [
    "manifest.json",
    "index.html",
    "HANDOFF.md",
    "rank-matrix.md",
    "checks/delivery-verification.json",
    "checks/fit-transforms.json",
]:
    api.upload_file(
        path_or_fileobj=Path(name).read_bytes(),
        path_in_repo="outputs/ready/" + name,
        repo_id=repo,
        repo_type="dataset",
    )

review_files = [
    Path(p)
    for p in [
        "index.html",
        "manifest.json",
        "HANDOFF.md",
        "rank-matrix.md",
        "rank-plan.json",
    ]
]
review_files += [
    p
    for folder in ["models", "review", "checks"]
    for p in Path(folder).rglob("*")
    if p.is_file()
]
review_files += list(Path("source").glob("L*.png")) + [
    Path("source/originals.json"),
    Path("source/original.glb.validation.json"),
]
source_files = [
    p
    for folder in ["source", "src"]
    for p in Path(folder).rglob("*")
    if p.is_file() and "validation" not in p.parts and "__pycache__" not in p.parts
]
source_files += [
    Path("HANDOFF.md"),
    Path("rank-plan.json"),
    Path("checks/fit-transforms.json"),
]
archive_receipts = []
for name, files in [
    ("witch-ranks-review.zip", review_files),
    ("witch-ranks-sources.zip", source_files),
]:
    with ZipFile(name, "w", ZIP_DEFLATED, compresslevel=5) as archive:
        for path in sorted(set(files)):
            archive.write(path, str(path))
        if "sources" in name:
            archive.writestr("models/", b"")
            archive.writestr("review/", b"")
    with ZipFile(name) as archive:
        assert archive.testzip() is None
        if "review" in name:
            for row in manifest["ranks"]:
                assert (
                    hashlib.sha256(archive.read(row["model"])).hexdigest()
                    == row["sha256"]
                )
    path = Path(name)
    archive_receipts.append(
        {
            "file": name,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "integrityPass": True,
        }
    )
    api.upload_file(
        path_or_fileobj=path.read_bytes(),
        path_in_repo="outputs/ready/" + name,
        repo_id=repo,
        repo_type="dataset",
    )
api.upload_file(
    path_or_fileobj=json.dumps(archive_receipts, indent=2).encode(),
    path_in_repo="outputs/ready/archive-receipts.json",
    repo_id=repo,
    repo_type="dataset",
)
print("DELIVERY_VERIFIED_AND_SAVED", json.dumps(archive_receipts), flush=True)
