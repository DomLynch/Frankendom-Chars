# Dwarf L2–L10 — targeted elite correction

Open `review/index.html` for actual exported-model views; download individual candidates from `models/`. L1 is an untouched baseline, not a new candidate.

## Scope

L2–L7 are retained byte-for-byte. L8–L10 preserve their existing suits, original skeleton/body data, proportions, warhammer and all 37 clips. The changes close their helmets and add fitted sleeve, thigh and collar coverage:

- L8: closed ram-horn helmet, blackened steel/ruby.
- L9: existing emerald finned helmet with a closed angular visor.
- L10: existing gold crown with an enclosed metal beard-mask.

The old visible face/body surface is hidden for the elites. Original buffers remain in each file. Existing suit positions/weights are retained; local exposed non-metallic limb patches receive opaque armour materials. Saved fitted donor sections supply coverage. The discarded whole-suit rebuilds are not delivered as selected models.

## Evidence and limits

`selected.json` and `manifest.json` identify exact candidate hashes, sizes and active geometry counts. Every image in `reports/render-receipt.json` carries both model and image hashes. The 93 candidate images and 10 baseline images are CPU studio renders, including front/back/side, Heavy, Guard, Kick and fight distance. They do not establish live gameplay or phone performance.

Original joint transforms, binary buffers and animation definitions are exact. All three corrected elites have 185 sampled joint-pose comparisons each. Format checks preserve the original's 88 Death_QuietOne quaternion errors and introduce no additional errors. This is not a clean-format or production approval.

Full visual acceptance remains open: a pale L9 underarm patch is still visible in the side view.

Remaining defects: inherited finger deformation in the existing glove surfaces, coarse reconstructed plate rims and shoulder seams, and localized original armour stretch. New visor/coverage surfaces are simpler than the engraved suit. Continuous collisions, optimized runtime size, six-slot carriers, arena integration and physical-phone validation remain open. No game file was replaced and nothing was deployed.

## Rebuild

Use Python with NumPy 1.26.4 and Pillow 12.3.0. Run `python scripts/rebuild.py L8 L9 L10` for the targeted patches, or provide any lower rank to use its retained original recipe. The driver uses temporary inputs and checks exact output hashes against `selected.json`. See the rebuild receipts for the tested platform and results.

The selected elite recipe is `scripts/patch_existing.py` applied to the immutable inputs in `sources/targeted-input`. The saved L8 reconstructed donor was fitted in Blender; only its helmet and local coverage panels are reused. New L9/L10 face closures are authored around the original head binding. Every final GLB was reimported and rendered in Blender 4.5.3. Original source scenes under `sources/L*/fit-pre-repairs.blend` and the helmet-panel scene are pre-repair provenance, not the authoritative final export.

Verify package receipts with `python scripts/verify_package.py`. For Khronos format comparison, install `gltf-validator` for Node or set `GLTF_VALIDATOR_PATH`, then run `node scripts/validate_format.cjs`. No automatic check invokes paid generation or writes to production.
