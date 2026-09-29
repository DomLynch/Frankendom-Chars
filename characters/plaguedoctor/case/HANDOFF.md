# Plague Doctor L2–L10 review pack — 28 September 2026

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

| Rank | GLB MB | Triangles* | SHA256 |
|---|---:|---:|---|
| L2 | 13.71 | 142,412 | `a45a553e7cafbb1e5c53e517941923fd82b5eb366510946f5318fb4cc415755b` |
| L3 | 15.12 | 144,801 | `16f9803e79ce433d6dc20873b8b530b723a7dbf4420da5eb803d86636b5bdd96` |
| L4 | 12.46 | 141,893 | `438fe87506f7ec977638e659a87e8427ca297355c398c7a4f79f43d4d9fae46b` |
| L5 | 12.41 | 143,648 | `5eff8e71a0ebe46d7f1726d0866ad5f9b8bcbaf14c6fcc23125a4ddf2bd7f8e4` |
| L6 | 12.97 | 144,944 | `0c6ea065759b90dba837ad9ec6ddb1801f6d300510ece3d0f46b87b7cca45e96` |
| L7 | 12.65 | 144,576 | `c925171606ecc31b5f11eaf553d7546ab63b85a6a51cb87876dc909a4e35f2c4` |
| L8 | 13.23 | 141,768 | `8d5ebd8109a2a1154a403161d32e07fd286967a8eecd346c081a0d8c2816701c` |
| L9 | 13.40 | 143,478 | `7ae7001079d4c299aea6d42cff80ccf89b379c193c4e45be765be81f24230229` |
| L10 | 14.80 | 144,946 | `7e3563c4ff9b7bf69b563c49613dd3a7b583e1cdb92b298aae478c80c1863ff2` |

## Reproduction and provenance
Selected fitting `.blend` scenes (before final binary animation restoration/coat repair), final GLBs, all nine unmodified donors, final design PNGs, generation/build/render receipts and standalone source scripts are included. Reproduce final animation restoration using preserve_clips.py after export; L8 additionally uses smooth_coat.py. Historical failed/rejected fits are excluded from the ZIP and remain in the working artifact folder. The original L1 snapshot and original-source receipt are included for comparison. The carrier source was extracted read-only from saved revision c97ce967 because this checkout lacked the file. No game code, asset replacement, commit, PR or deployment was performed.

Private remote persistence: `Domlynch/frankendom-plaguedoctor-pilot-20260928`. Check individual job receipts for bounded timeouts and build ownership. Source scripts assume the documented environment and credentials; no credentials are packaged.
