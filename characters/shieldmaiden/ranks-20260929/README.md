# Shieldmaiden L2–L10 — candidate delivery, 29 September 2026

**Built 9 / technically validated 9 / visually accepted as candidates 3 / packaged 9.**
L8–L10 pass this exported-view review. L2–L7 are included for review, with the defects below; the complete ladder is **not AAA-approved**. No catalog promotion or game integration is claimed.

## Design and evidence

Nine individual GLBs, nine matching editable final Blender scenes, nine donors, nine references, 90 actual exported-model captures, a ladder comparison, scripts and validation receipts are included. Each scene was saved after reimporting its final GLB; its embedded `source_glb_sha256` matches the delivered model. `manifest.json` and `SHA256SUMS` identify exact bytes.

Palette: brown leather, bone/hide, copper, bronze, iron, steel, blackened steel/ruby, emerald, full gold. L8 has a ram-horn closed visor and squared layered plates; L9 has antlers and pointed leaf plates; L10 has a winged gold helm and ornate fluted armour. All three elites have covered upper/lower arms, hands and full thighs, with distinct geometry visible at the measured 110-pixel fight view.

All ranks preserve the original binary prefix, node hierarchy, skins/inverse binds, weapon placement and all 25 animation clips, including their actual samplers and values. The original has 65 joints per skin. Every visible skinned primitive passes endpoints/intermediate samples across Armed, Attack, Heavy, Guard, Kick and Roll: 54 poses per rank, zero edges exceeding the existing combined 0.12-metre/3x-stretch limit. This does not prove continuous collision clearance.

Khronos validation contains exactly the same 95 animation-quaternion errors as the unchanged source, compared by code, message and pointer. Each candidate adds one skinned-node local-transform warning. These are not clean-format or mobile-optimized assets. Construction buffers and hidden source meshes are retained deliberately.

## Remaining defects and rejected work

- L2–L7: the original reconstructed face/hair has visible close-up cracks and coarse surfaces. An untouched-original Armed capture reproduces the facial cracks. The earlier missing-face-layer hypothesis was rejected after source comparison.
- L2: a conspicuous reconstructed neck/braid remnant remains behind the collar. L3–L7 have rough/open rear neckline transitions. These block visual acceptance of the lower set under the brief.
- L8–L10: close plate edges and original glove geometry remain coarse. Elite coverage and silhouette pass the inspected views, but artist approval, game lighting and full-motion clipping remain untested.
- Wide collar, broad neckline cuts, and the later face/neck refinement were rejected. Their models are excluded. No repeated reconstruction was used for fitting defects.
- Identical apparent elite forehead cracks were Blender shadows from fully transparent original objects. Corrected captures explicitly exclude only zero-alpha objects and allow sufficient transparent ray depth. Delivered geometry is unchanged by that rendering correction.

## Reproduction and handoff

Use `source/requirements-cloud.txt` (Python 3.13, bpy 5.2.2). From a working directory containing `source/original.glb` and `donors/Lx.glb`, set `RANK=Lx`. Run: `fit_rank.py`, `pack_preserved.py source/original.glb source/Lx-fitted.glb models/shieldmaiden-Lx.glb`, then `skin_anatomy.py`, `smooth_weights.py` with 30 iterations, `retain_face.py` for L2–L7, `retain_hands.py`, `finish_armour.py`, `finish_materials.py`, `check_candidate.py`, and `render_rank.py`. Repair scripts take input/output GLB paths. `fit_job.py` contains the exact orchestration and `checks/jobs.jsonl` records immutable cloud revisions. Re-rendering requires no TRELLIS call.

HF Pro shared TRELLIS.2 generated each donor once. Blender ran on bounded cpu-upgrade jobs: 8 vCPU/32 GB at $0.03/hour, not per day. No dedicated GPU was purchased. The original/L1 and game files were not modified.

Next artist action: repair the lower neck/head transition against the supplied original comparison; preserve the accepted elite surfaces. Do not treat sampled pose checks as game, finisher/carrier, performance-budget or physical-phone acceptance.
