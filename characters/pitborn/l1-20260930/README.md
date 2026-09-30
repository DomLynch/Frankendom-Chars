# Pitborn L1 recruit — 30 September 2026

Separate recruit candidate matching the owner-approved L2–L10 direction: patched linen, ragged hems, wrapped shins, worn leather boots/cuffs and one plain shoulder pad. Original face, cap and cleaver retained. Original input and all L2–L10 files are untouched.

Delivery: `work/pitborn-l1-20260930/`. Authoritative model: `models/pitborn-L1.glb`; matching imported final scene: `source/pitborn-L1-final.blend`. `L1-review.jpg` and `previews/L1/` show the actual exported model, including action and 110-pixel fight views. The concept reference is not export evidence.

## Validation

- Original 65-joint skins, 25 animation clips, node transforms, weapon placement and original binary prefix preserved exactly.
- All 54 sampled Armed/Attack/Heavy/Guard/Kick/Roll poses pass the combined long-edge/stretch threshold.
- Original and candidate both have 86 Khronos errors: 85 animation quaternion normalization errors and one indexed semantic-continuity error. No new errors; candidate has 23 warnings versus 26 in the source.
- Final GLB SHA256: `77d0fb2f2f07b54e392d3d2a17d27335902b7c19618aaac88f2e6f5d441c734c`.

The first build identified four stretched edge occurrences during Roll. A broad pelvis-weight repair worsened the result and was rejected. The selected localized repair smooths the back-waist weights while avoiding alternating top-four spine/thigh influences. The first local smoothing attempt opened UV seams; the selected repair groups coincident positions for weight continuity without welding geometry. A small red reconstruction artefact uses neutral linen material. Geometry, UVs and original source data remain unchanged by this repair.

## Limits

The inherited cap/scalp intersection and rough neck joins remain visible in close-up. Reconstructed hands and cloth hems are coarse; dark underarm gaps remain in the attack view. Sampled checks do not prove continuous collision clearance or game/phone performance. These are review assets, not game integration.

## Reproduction

Run `scripts/pitborn/l1_20260930/prepare.py` to stage the existing rank helpers and original input. The bounded `job.py` performs one TRELLIS reconstruction, fitting, preservation packing, smoothing, fragment tethering, original-face retention and regional collar repair. No additional lining tubes are used.

Then run `repair.py` on the saved first export, validate with `source/check_candidate.py`, and use `render_job.py` to regenerate final views and the matching scene. `collect.py` verifies every render/model hash. The final scene is reimported from the final GLB and embeds its authoritative SHA; use the GLB as the authority for exact animation sampler data.

HF Pro account: Domlynch. Reconstruction: shared microsoft/TRELLIS.2, 1024 resolution / 100k target triangles / 2048 textures. Blender: HF cpu-upgrade, 8 vCPU / 32 GB. Initial job `6abc9eb74c46ef19870348e4` saved all outputs but exited nonzero on the first motion result; capture job `6abca0c84c46ef1987034930` exposed the seam issue; final job `6abca1b1031314b696343921` captures the corrected export and reopens the matching scene to verify its model hash. CPU timeouts: 30, 20 and 15 minutes (maximum $0.0325 combined at the verified $0.03/hour rate; shared TRELLIS quota is separate). No paid GPU job or local Metal render was needed.
