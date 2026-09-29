# Witch L2–L10 — separate review candidates

2026-09-28. Nine separate candidates are built; model/image hashes and structural checks are verified. `manifest.json` and `checks/delivery-verification.json` are the delivery receipts.

## Selection and preservation

Nine combined candidates: `models/witch-L2.glb` through `witch-L10.glb`. Original L1/game assets remain untouched. These are art-review candidates, not a deployed replacement or AAA/production certification.

Palette: brown leather, bone/hide, copper, bronze, iron, steel, blackened steel/ruby, emerald, full gold. L8 uses a closed ritual visor beneath a horned hood; L9 a closed crescent helmet with lunar fins; L10 a full-gold closed demon mask and crown. Elite coverage includes shoulders, upper arms, elbows, forearms, gloves, thighs, knees, shins and boots.

L2–L7 retain original head/face geometry, UVs and weights on the original body node, within the new rank hoods. Reconstructed surfaces replace visible old clothing. The complete original body remains stored with a transparent material; its preservation does not mean that its surface stays visible.

- Original body SHA256: `c99798db5972d37c0540b0b6683aedaf9afaf381cb39d7298818434adf55d45d`, 7,525,672 bytes, revision `829dfdf8e5a151fe6dd3d1c29bf224e15b3d4dec`.
- Original carrier SHA256: `0cb348815c60dd61325244cde3ef4c4344a434609b672b0e96a95b29f4f3fa24`, recovered read-only from saved revision `ed385c6b752af2c0d2912d8addf0953c08dac63c`. Exact paths: `source/originals.json`.
- Every selected GLB preserves the original binary prefix, node hierarchy/rest data, skin/inverse binds, weapons and all 38 animation clips exactly. Source skeleton: 65 joints.
- Every rank is measured at 54 times across Trident_Idle, Trident_High, Trident_Guard, Trident_Thrust, Kick and Roll. Zero severe stretched-edge occurrences at length >0.12m and ratio >3; finite geometry and normalized weights. This is sampled evidence, not continuous clearance certification.
- Nine actual-export captures per rank: front/back/side/attack/guard/kick/head/high-rear/fight. Receipts bind images to final GLB hashes. 375×600 images; fight figure measures 110px, excluding weapon. Matching original-Witch views use the same Trident-family clips and neutral lighting.
- Khronos reports 231 **inherited** errors: 95 non-normalized quaternions and 136 accessor-bound errors. Final candidates must match the original error-code counts, with no new errors. Full reports are included. Two skinned-node/hierarchy warnings remain. This is not a zero-error format claim.

## Reproduction

Run from the package root. Reuse saved donors; do not reconstruct to repair a material or rerender.

`source/build_rank.py N` orchestrates:

1. `build_pilot.py` and `reweight_pilot.py`: fit donor height 1.81m, floor 0.025m, to measured Witch anatomy; apply continuous arm/cloth fields.
2. `pack_preserved.py`: append new geometry to immutable original buffers and reuse original skin/animations.
3. `smooth_weights.py ... 100`: topology/UV-seam continuity, four normalized influences and zeroed unused joint indices.
4. `align_grip.py`, then `articulate_hands.py`: seat gloves and transfer hand influence to original inverse-bind finger capsules. Original clips stay exact.
5. L2–L7: `preserve_face.py` retains only the frontal source face region (1.52–1.66m high, within 0.06m of the centreline, forward of 0.005m) on its original node and opens the reconstructed face area; `close_cowl.py` adds an overlapping inner neck lining. L8: `finish_palette.py` applies the reviewed dark finish, with zero emission.
6. `check_candidate.py`, `format_check.cjs`, `render_candidate.py -- LN`, then `verify_delivery.py`.

The saved lower ranks were recovered from the initial remote pack with `restore_hood.py` before steps 4–5. Exact UV/bind-position matching restores intact hood topology above 1.52m; ambiguous mappings over 0.1mm are rejected. Fresh builds already contain intact hoods and skip this recovery. Initial remote packs remain in the private HF dataset under `outputs/v2/models`.

Remote fitting/rendering: Blender/bpy 5.2.2, Linux, Python 3.13. Initial Mac pilot: Blender 5.2.1. Local repairs/checks: Python 3.12, NumPy 1.26.4, SciPy 1.17.1, Pillow 12.3.0, huggingface-hub 1.31.0. Validator: `gltf-validator@2.0.0-dev.3.10` under `source/validation`, or set `GLTF_VALIDATOR`. Source scenes are labelled **pre-repair**; final GLBs and ordered repair scripts are authoritative.

## Reconstruction and recovery

All nine donors: official `microsoft/TRELLIS.2`, 1024 reconstruction, 100,000 target triangles, 2048 textures, seeds 28092802–28092810. Per-donor `.trellis.json` files record inputs, timings, settings and hashes. Recorded service revision: `ebf60b20fc5a4607f90a1c11c0aab0ceeda5429d`, MIT. Built-in ImageGen supplied reference art, clearly separated from actual-model evidence.

Domlynch Pro authentication was verified. RGBA input bypassed the failed background-removal path. Redirect handling was required for initial Gradio configuration but removed before streamed downloads to avoid duplicate arguments. Bounded retries recovered capacity/HTTP502 failures. The prior no-donor/no-model blocker is superseded.

Deployment guards moved heavy work to bounded HF CPU jobs. A tiny upload/download round trip passed before fitting. MCP OAuth could submit jobs but lacked private-dataset write permission; the existing local SDK credential passed the real persistence check. Results persist privately in `Domlynch/witch-ranks-20260928`. Job receipts list IDs/timeouts; actual billed dollars were not independently verified.

## Remaining defects and next owner

Lower-rank old-hood overlap was repaired by retaining only the frontal original face region and using the rank hood plus inner cowl for surrounding coverage. L7 front/back/high-rear/kick proof passed before replication. Final lower-rank images are generated from repaired model hashes. Close-up inner face framing remains coarse, consistent with the original low-detail face.

- Reconstruction is softer close-up than the concepts; small fittings, horns, fingers and cloth edges are not hand-retopologized production meshes.
- Finger articulation improves the trident grip. Continuous hand/shaft contact, self-collision and cloth clearance across every frame remain integration checks.
- Combined candidates are not six closed-boundary equipment slots. Helmet removal/finishers, carrier compatibility, runtime budgets and physical-phone performance remain unverified.
- The original 231 format errors remain. Repair those in a separate baseline-compatible task; do not silently alter approved clips during import.

Next owner: character/armour integrator. Review the ladder, then verify the real arena camera, continuous trident combat, finishers and target phone. Keep the original until acceptance.

Followed the character-ranks handover, current character-pilot/troubleshooting, ImageGen and HF Jobs skills. Reused the Knight lane's binary-preserving pack/motion approach and the project's TRELLIS client, with Witch-specific fitting/recovery. No canonical asset, game code, PR or deployment changed by this task.
