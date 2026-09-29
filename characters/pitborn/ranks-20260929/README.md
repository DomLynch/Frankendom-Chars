# Pitborn L2–L10 — review candidates, 29 September 2026

Nine separate GLBs, 90 actual exported-model captures, nine saved TRELLIS donors, nine Blender fitting scenes, original input, scripts and hash-linked checks. No game changes or integration. Owner visual approval remains open.

Palette: L2 brown leather; L3 bone/hide; L4 copper; L5 bronze; L6 iron; L7 steel; L8 blackened steel/ruby; L9 emerald; L10 full gold. Elite structures are a closed crest visor, closed horned mask and closed infernal crown. L2–L7 retain the original Pitborn face and cap. Original cleaver placement, 65-joint skins and all 25 original animation clips remain exact.

## Evidence

`manifest.json` identifies each final GLB. `previews/L*/render-receipts.json` links each image to that GLB hash. All nine pass 54 sampled Armed/Attack/Heavy/Guard/Kick/Roll poses with zero edges exceeding the combined absolute-length/stretch limits. These samples do not establish continuous collision clearance. Original nodes, skins, animation JSON and original binary prefix are unchanged. Newly reconstructed surfaces replace the visible armour/body; original meshes remain stored and hidden.

Khronos validation reports the same 86 error messages as the original (85 animation quaternion normalization errors and one indexed-semantic continuity error). No new error category was introduced. Added joint-slot zero-weight warnings and skinned-node transform warnings remain; this is not a clean-format or optimized-runtime delivery. Stored original geometry and duplicate construction buffers increase file size.

## Remaining visual limitations

- L2–L7: cap/scalp intersection and rough collar/neck boundaries remain in close views. Original face is retained, but the assembly needs artist polish.
- L8: shoulder plate spacing, broad matte joint lining and a few tiny detached decorative fragments remain visible in close/action views.
- L9: emerald is subdued under neutral lighting; inspect under the intended game lighting.
- All ranks: reconstructed fingers and close plate transitions are coarse. L3/L4 right-hand weighting was locally stabilized; original animation data is intact, but reconstructed finger articulation is simplified.
- No game, finisher/carrier, performance-budget, continuous clipping or physical-phone acceptance is claimed.

## Reproduction and source scenes

Scenes in `source/pitborn-L*-fit.blend` are fitting checkpoints BEFORE GLB packing and subsequent weight/coverage/material repairs. They are not editable equivalents of the final post-repair GLBs. All donors and repair scripts are included.

Run with Blender Python/bpy 5.2.2, numpy 2.4.3, scipy 1.16.3; HF orchestration uses huggingface_hub 1.33.0 and gradio_client 2.7.1. Original source hash and generation parameters are in the checks.

Order: fit_rank → pack_preserved → smooth_weights (100 iterations) → tether_fragments → preserve_face (L2–L7) → add_sleeves → repair_collar (L2–L7) → repair_hand (L3/L4) → refine_sleeves (L8) → L9 material-factor adjustment in repair_job → check_candidate → render_rank. Do not reconstruct again for these saved fitting repairs.

Compute ran on Domlynch Pro, HF cpu-upgrade 8 vCPU/32 GB at $0.03/hour, with bounded jobs and shared microsoft/TRELLIS.2 reconstruction. Local Metal was authorized but not used during the concurrent deployment guard. Job IDs and immutable source revisions are included. No scheduled follow-up was created.
