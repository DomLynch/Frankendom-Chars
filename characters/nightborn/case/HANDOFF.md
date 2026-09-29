# Nightborn L2–L10 — corrected elite coverage

This isolated candidate set supersedes the previous open-face L8–L10. L2–L7 are byte-identical to the earlier delivery. Original source, skeleton, estoc and all25 animation clips remain preserved. No game assets or deployment were changed.

## Elite decisions
- L8: closed blackened-steel/ruby horned helmet.
- L9: closed emerald visor with swept bat-like fins.
- L10: full-gold enclosed helmet with integrated spiked crown.
- All three: no active source face/hair/eyes, covered neck, arms/hands, legs/feet. Existing rich torso/leg armour retained; new fitted arm coverings, original-weight gauntlets and continuous gorget. Helmet bound to original Head bone.

## Rebuild and evidence
Selected Blender scenes are saved before final animation restoration. Run `source/preserve_clips.py` on each fresh export before using it: this restores exact source animation accessor bytes and joint rest transforms, after checking common bind-space conversion. Do not export the scene and assume animation timing is identical. For L9, then run `source/finish_emerald.py input.glb output.glb` to reproduce the final cohesive emerald material factors. This changes only material JSON; binary geometry, textures and clips remain byte-identical.

Build recipes fit the saved helmet donors and previous body candidate inputs; no donor regeneration is required. Source scripts use `original/nightborn.glb`, previous-rank body input and helmet donor uploaded to the documented private delivery dataset. Credentials are supplied via HF secrets, never embedded in sources. Per-rank build receipts and reconstruction metadata identify inputs. Lower-rank source assets are preserved from the previous delivery; their earlier executable recipes are included in `source/prior-ladder-recipes` (historical elite recipes there are context only and do not define current L8–L10).

Each review image comes from the exact final GLB hash in its rank receipt. Front/back/side, Armed, Heavy, Guard, Kick, rest, head close-up,375px and110px fight-scale captures are provided. The three elite models also receive24 sampled motion poses across Armed/Heavy/Guard/Kick, checking every new skinned mesh for edges over0.10m and3x their rest length. This detects major stretches but does not establish continuous collision clearance.

Validation reports distinguish exact clips/joint matrices, scene coverage, deformation, Khronos format, source preservation and archive integrity. Rank matrix and manifest identify each candidate.

## Remaining defects and integration limits
Reconstructed surfaces retain roughness around shoulder, elbow and plate transitions. Original lower-rank face/hair faceting remains unchanged. Metal arm shells and fitted joint transitions are simpler than the reconstructed torso and helmets. These are review candidates, not a production-readiness claim.

Six-slot equipment carriers, helmet removal/finishers, continuous contact/intersection checks, actual arena playback and physical-phone performance remain unvalidated.375px/110px studio captures only establish appearance at those scales. Heavy unoptimized geometry/textures require an integration/performance pass before release.

## Verified asset checks

9/9 GLBs pass Khronos with0 errors;11–16 hierarchy/tangent warnings per model remain. Exact25 original animation clips retained across all9, with maximum joint-matrix difference 5.234019861966033e-08. All3 corrected elites pass24 sampled poses each with0 qualifying stretched edges. Original source andL2–L7 hashes unchanged. These tests do not remove the limits above.
