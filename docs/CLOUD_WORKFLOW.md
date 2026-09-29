# Cloud character workflow

## What runs where

Reference artwork supplies design intent. **TRELLIS.2 runs GPU image-to-3D reconstruction** and produces an unrigged textured donor. **Blender runs fitting, export and review**, on a local machine or a bounded Hugging Face CPU Job using `bpy`. The original character supplies the rig, weapon and retained animation data. Reconstruction does not automatically produce a finished rigged character.

This repository needs neither the full game nor its deployment credentials. `catalog.json` and the GitHub Release hold the inputs. Historical private HF datasets named in case scripts belong to the original tasks; use your own writable private destination.

## 1. Download one complete case

Python 3.11+ is enough to download and verify packages; no model libraries are needed for this step:

```bash
python3 scripts/fetch_assets.py witch --output work/witch
```

Witch combines its review and source ZIPs into one workspace. Other archives retain their documented enclosing directory (the downloader prints it). The tool refuses a non-empty output directory. `catalog.json` records exact archive and selected-model SHA256 values. The normal GitHub source ZIP does not include the large release archives.

## 2. Reconstruct only when a new donor is required

For repairs, first use the saved donors. For new shapes, inspect the [official TRELLIS.2 Space](https://huggingface.co/spaces/microsoft/TRELLIS.2) and [upstream project](https://github.com/microsoft/TRELLIS.2) for current API, licence and settings. The saved client `characters/witch/case/source/reconstruct.py` documents the working session sequence: start session → preprocess → image-to-3D → GLB extraction.

Install the appropriate `gradio_client`/`huggingface_hub` versions and authenticate with `hf auth login` in your execution environment. Verify the current Space API before executing the archived client; its service dependencies can change. It reads stored authentication or `HF_TOKEN`, never a committed token. Start at 1024 / 100,000 triangles / 2048 textures. Knight's selected case instead used 1536 / 200,000 / 2048 after a visible-detail comparison.

A genuine transparent RGBA input helped the Witch avoid failing background matting. Redirect handling needed adjustment in that recorded client. Treat these as dated recovery evidence, not a guarantee that today's Space API is identical. A 502 or preprocessing failure alone does not show the account is on a free plan. Bound retries and retain successful donors.

## 3. Fit one assembly type

Read the downloaded case's handoff and source order. Inspect the body/mesh bind pose and source inverse binds; default node transforms can represent a different pose. Fit the saved donor to that character's measured anatomy. Preserve useful UVs/surfaces, exact original rig/animation payloads and working original weights. Repair only demonstrated failures.

For Witch, run from the downloaded workspace with the recorded bpy-compatible environment:

```bash
mkdir -p models checks review
WITCH_BLENDER=bpy python source/build_rank.py 10
```

This is a character-specific recipe using its saved inputs, not an automatic converter for every character. Nightborn/Plague Doctor require post-export animation restoration; Knight has its own packing/glove sequence; Dwarf has a targeted rebuild driver. `characters/*/case` preserves those recipes for inspection. Some historical scripts have local paths and task dataset names that must be adapted in a fresh environment. Earlier `.blend` scenes may precede repairs.

## 4. Run Blender on bounded HF CPU compute

Consult the current [Hugging Face Jobs guide](https://huggingface.co/docs/huggingface_hub/guides/jobs) and [Jobs pricing](https://huggingface.co/docs/hub/jobs-pricing). Check account access and available credit; this repo records no current billing balance or guaranteed price. Use a timeout, a specific input revision and secret injection. If your assistant has an HF Jobs connector, use its supported job interface; the SDK example is also available for a Python-capable environment.

`examples/submit_witch_review.py` renders an **existing** Witch candidate with the saved renderer. It does not create a new character or modify the model. Upload your chosen GLB to your own input dataset first, and create a private writable output dataset. Then, after authorizing the bounded paid run:

```bash
python -m pip install huggingface_hub==1.31.0
hf auth login
python examples/submit_witch_review.py \
  --input-dataset YOUR_ACCOUNT/character-inputs \
  --input-revision INPUT_COMMIT_SHA \
  --model-file models/witch-L10.glb \
  --output-dataset YOUR_ACCOUNT/character-results \
  --code-revision FRANKENDOM_CHARS_COMMIT_SHA \
  --rank 10
```

Replace both revision placeholders with full commit SHAs. The example uses Python 3.13 / bpy 5.2.2 on `cpu-upgrade`, capped at 30 minutes. It verifies a job-credential upload/download round trip before rendering, uploads the images with hash receipts, and prints the job ID/URL/output prefix. Inspect the job until terminal and verify persisted images before reporting completion. No token is printed. Docker tag and apt dependencies are not digest-locked; rebuilding requires renewed environment checks.

This extracted wrapper was syntax/help checked during publication; **no new paid job was run to test it**. The underlying fitting/render recipe has saved successful job receipts. Actual billed cost was not independently measured.

## 5. Validate and deliver

Use the character skill's preservation, deformation and visual checks. Verify every visible skinned primitive, including retained head/linings. Match captures to the final GLB hash. A later edit invalidates the older images. Check one retained-face assembly separately from a closed helmet, then each changed rank. Save donors and final models before expensive renders, and upload at recoverable boundaries.

Do not report source scenes, studio captures, preserved clip names or a packaged ZIP as game-ready completion. Report remaining shape/material defects, inherited format errors, slot/carrier/finisher gaps and unmeasured phone performance. No generation, Hub mutation or paid job runs in repository CI.
