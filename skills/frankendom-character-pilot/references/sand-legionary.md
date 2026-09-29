# Sand Legionary: original visual result, 2026-09-26

Historical snapshot as of 2026-09-26. Checks, defects and approval statements below describe that revision; consult current project state and owner feedback before treating them as current status.

## Evidence and locations
Pilot root: `/Users/domininclynch/Desktop/Business/artifacts/sand-legionary-pilot`.
Selected GLB: `review/sand-legionary-review.glb`, SHA256 `e47ed74ad46cbb9f1b9dc44cc9fe984c0438bb7bd4a8bade84366416921075fe`, 95,392 triangles, 11 meshes, 11,121,072 bytes (10.61 MiB). Verify the hash before treating a future file as the same revision.
Source scene: `source/review-assembly.blend`. Fitting pieces: `review/pieces/`. Owner feedback record: `review/OWNER-FEEDBACK.md`. Handover ZIP is about 81.7 MiB because it contains source, both candidates, textures and receipts; this is not runtime download size.

## What made the selected version
- Original reference images → TRELLIS.2 textured reconstruction through an authenticated Hugging Face Space → Blender 5.2.1 processing → actual GLB viewed in Three.js.
- Earlier pilot notes record character/shield seeds 260926/260927 and Space revision `ebf60b20fc5a4607f90a1c11c0aab0ceeda5429d`; these are historical provenance, not independently reverified provider receipts. Recover original service logs before promising exact reproducibility. Do not invent API parameters from seeds alone.
- `source/preserve_surface.py` reuses the segmentation prefix of `source/prepare.py`, splits faces into helmet, crest, body, arms, gloves, greaves, boots and exposed skin, preserving the source surface and UVs. It writes `source/surface-preserved.blend`. This script runs a render as well as saving a scene.
- `source/assemble_review.py` loads that scene, trims the old crest and adds a narrow ridged burgundy fan, imports the repaired scutum and full gladius, then exports selected meshes to the review GLB and saves the assembly scene. **Do not rerun in place:** it overwrites the approved files and contains the still-unresolved crest placement.
- Original UV/material detail survived because the final selected path preserved the donor, rather than replacing it with aggressively remeshed or projected geometry.
- `source/package_review.py` extracts compact per-node GLBs. `source/verify_handover.cjs` checks their geometry/UV buffers match the selected assembly and validates GLB format. Body includes cuirass + skirt; paired limbs share a file; base-body is exposed skin only. Crest and crest-fan coexist in this revision.

## Tools that did NOT earn credit for this result
Pixelmator did not produce the selected appearance. Its later controlled colour trial used the correct atlas but was rejected by the owner. ArmorPaint/Material Maker exploration and alternative remeshing/baking branches should not be credited as part of the selected result without tracing a contribution in its actual materials. `preserve_build.py` is an alternate attempted pipeline, not the final `preserve_surface.py` path.

## Actual checks and limitations
`node source/verify_review.mjs`, `node source/check_review_browser.cjs`, and `node source/verify_handover.cjs` passed for the reviewed snapshot. The browser gate uses local Three.js, 375×667, software WebGL and a projected 110px fight figure. These are studio views, not arena or hardware-performance receipts.
At this snapshot, the owner's complaint that the red crest crosses the face was open. Geometry was unchanged by Pixelmator, so compare both crest meshes in the original too. A correction requires front/side/hero/fight evidence; these historical green gates do not close it.

At this snapshot, the original production brief was incomplete: seam topology failed, with no complete neutral body or finished helmet-off face, no rig/binding or verified grips, and no physical-phone performance. The shared 2048px WebP atlas differed from the requested core-only 1024/512 PBR sets. Higher triangle count was explicitly allowed by the owner, but that did not establish a runtime budget.

`notes.md` at the pilot root contains earlier intended pipeline claims that do not all describe the approved review assembly. Prefer actual GLB inventory, scripts, receipts and OWNER-FEEDBACK over that older prose.
