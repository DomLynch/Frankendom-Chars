"""Package only selected candidates and their reproducible evidence."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
validation = json.loads((ROOT / "validation.json").read_text())
rows = validation["models"]
manifest = {
    "status": "review candidates; visual acceptance open",
    "originalUnchanged": True,
    "ranks": [],
}
table = ["| Rank | GLB MB | Triangles* | SHA256 |", "|---|---:|---:|---|"]
for row in rows:
    rank = row["rank"]
    folder = "proof-v3" if rank == 10 else f"ladder/L{rank}"
    donor = f"src/assets/source/creatures/plaguedoctor-L{rank}-donor.glb"
    entry = dict(row)
    entry["file"] = f"models/plaguedoctor-L{rank}.glb"
    entry["reference"] = f"source/L{rank}-reference.png"
    entry["donor"] = donor
    entry["donorSha256"] = hashlib.sha256((ROOT / donor).read_bytes()).hexdigest()
    entry["settingsReceipt"] = donor.replace(".glb", ".trellis.json")
    entry["buildReceipt"] = f"{folder}/L{rank}-build.json"
    entry["renderReceipt"] = f"{folder}/render-receipt.json"
    manifest["ranks"].append(entry)
    table.append(
        f"| L{rank} | {row['bytes'] / 1e6:.2f} | {row['trianglesIncludingPreservedHiddenOriginal']:,} | `{row['sha256']}` |"
    )
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2))
text = (
    """# Plague Doctor L2–L10 review pack — 28 September 2026

Nine isolated rigged candidates, with a distinct gold L10 boss. Original game assets remain untouched. **Visual acceptance remains open; these files are not production-certified.**

Open [the review gallery](review/index.html) for actual exported-file front/back, attack, guard, kick and fight-size images. The PNGs are studio renders of the hash-matched GLBs, not reference-art substitutes.

## Direction and construction
L2 leather; L3 bone/hide; L4 copper; L5 bronze; L6 iron; L7 steel; L8 black steel/ruby; L9 emerald; L10 gold. Upper ranks use different closed helmet geometry: L8 short swept horns, L9 taller side fins, L10 three-pronged crown with broader decorated shoulders. Reconstructed armour covers the limbs; original weighted hand shells supply the gloves.

All nine saved donors were reconstructed with Hugging Face TRELLIS.2 at 1024 / 100,000 target triangles / 2048 textures, seeds 280902–280910. Each actual reconstruction succeeded on its first call. Higher settings were authorized but not needed for this candidate pass. Final fitting/export/rendering used Blender 4.5.3 on bounded Hugging Face CPU jobs because the shared Mac deploy guard was active. Actual billed dollars were not measured.

The original complete body/face geometry and vertex weights are retained but hidden beneath the new reconstructed clothed surface. Original rig, bone names, weapons and animation names remain. Visible anatomy therefore comes partly from the fitted donor; this is not a claim of pixel-identical original facial appearance. Donor fingertips were replaced by original weighted glove geometry, using the donor atlas. New armour weights are interpolated from the original surface; the original weights were not replaced. Armour is currently combined, not packaged into the game's six loot carriers.

## Verification
All nine final candidates pass Khronos validation with zero errors and three skinned-mesh hierarchy warnings each. Original 65 joint names and 25 animation names remain; geometry is finite and new weights normalized. In-Blender before/after hashes verify original mesh positions and weights unchanged. The final GLBs carry exact original animation sampler payloads and joint rest transforms, restored after export shortened Draw. Five sampled times in each of all 25 clips match original joint world positions within 0.000000052 scene units. Continuous collision clearance remains untested.

54 captures match their exact model hashes: front/back Armed 0.35s, Heavy 0.45s, Guard 0.4s, Kick 0.4s, and a reduced fight-size Armed view. Studio viewport is 375×600. The reduced view approximates a small fight character; it is not an actual arena screenshot, measured game camera or physical-phone performance test.

## Remaining defects / acceptance gaps
- Reconstructed coat hems and inner/rear surfaces remain rough, with thin/open fragments visible in close-ups; the sampled kick can expose those surfaces.
- Lower-rank leather and metal colours are subdued under the matched studio light; material richness is below the reference artwork. L8 ruby readability needs refinement.
- Glove/cuff transitions and shoulder/armpit contact need close-up cleanup and continuous-animation testing. Sampled grip is improved, not a complete weapon-contact certification.
- Loot-slot/carrier separation, helmet removal/finisher behaviour, actual arena views, physical-phone performance and all-frame collision clearance remain unvalidated.
- These are full-detail review files with hidden original geometry. Size/triangle optimization must follow visual acceptance, not be mistaken for current mobile readiness.

## Exact files
*Triangle counts sum unique mesh primitives, including the preserved hidden original; they are not GPU draw-call or per-instance counts. Sizes use decimal MB. Exact byte counts, donor hashes and receipt paths are in [manifest.json](manifest.json).

"""
    + "\n".join(table)
    + """

## Reproduction and provenance
Selected fitting `.blend` scenes (before final binary animation restoration/coat repair), final GLBs, all nine unmodified donors, final design PNGs, generation/build/render receipts and standalone source scripts are included. Reproduce final animation restoration using preserve_clips.py after export; L8 additionally uses smooth_coat.py. Historical failed/rejected fits are excluded from the ZIP and remain in the working artifact folder. The original L1 snapshot and original-source receipt are included for comparison. The carrier source was extracted read-only from saved revision c97ce967 because this checkout lacked the file. No game code, asset replacement, commit, PR or deployment was performed.

Private remote persistence: `Domlynch/frankendom-plaguedoctor-pilot-20260928`. Check individual job receipts for bounded timeouts and build ownership. Source scripts assume the documented environment and credentials; no credentials are packaged.
"""
)
(ROOT / "HANDOFF.md").write_text(text)
files = [
    ROOT / name
    for name in [
        "HANDOFF.md",
        "manifest.json",
        "validation.json",
        "format-validation.json",
        "animation-validation.json",
        "coat-repair.json",
        "RANK-DIRECTION.md",
    ]
]
files += [ROOT / f"models/plaguedoctor-L{rank}.glb" for rank in range(1, 11)]
for rank in range(2, 11):
    folder = ROOT / ("proof-v3" if rank == 10 else f"ladder/L{rank}")
    files += [
        folder / f"L{rank}-build.json",
        folder / "render-receipt.json",
        folder / f"plaguedoctor-L{rank}.blend",
    ]
    files += sorted((folder / "renders").glob(f"L{rank}-*.png"))
    files += [ROOT / f"source/L{rank}-reference.png"]
files += sorted((ROOT / "src/assets/source/creatures").glob("*"))
files += sorted((ROOT / "review").glob("*"))
files += sorted((ROOT / "source").glob("*.py"))
files += [ROOT / "source/format_check.cjs", ROOT / "source/originals.json"]
files += sorted(ROOT.glob("job-*.json"))
archive = ROOT / "plaguedoctor-L2-L10-review.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=4) as package:
    for path in sorted(set(files)):
        assert path.is_file(), path
        package.write(path, path.relative_to(ROOT))
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
    for row in rows:
        name = f"models/plaguedoctor-L{row['rank']}.glb"
        assert hashlib.sha256(package.read(name)).hexdigest() == row["sha256"]
print(
    json.dumps(
        {
            "archive": str(archive),
            "bytes": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "integrity": "passed",
        }
    )
)
