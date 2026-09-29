# Fitting, export and execution troubleshooting

These dated cases explain the main skill's checks. They record observed outcomes, not current project status or universal repair thresholds. Consult the active brief and project state before continuing a character.

## Coverage, weighting and finish cases — 2026-09-27–28

- **Character decisions differ.** Pitborn's approved masks were retained; Executioner elites required covered biceps, thighs and gloves. Nightborn's corrected L8–L10 brief required closed faces and full limb coverage. Preserve the latest per-character coverage matrix rather than generalizing any example to the whole roster.
- **Pitborn slot continuity.** A rigid Head assignment plus a separate helmet offset also moved collar vertices, tearing them from the body. Closest-triangle barycentric transfer worked better than nearest-vertex assignment in that trial. Blend helmet adjustments into the neck and verify shared positions/weights; this does not prove collision clearance.
- **Goblin transfer regression.** A robust automatic transfer worsened Kick p99 stretch from 1.59x to 2.04x and worst stretch from14x to40x, so it was rejected. Hand-derived shells improved coverage but did not establish sealed wrists or finished glove detail. These are case outcomes, not a universal rejection of automatic weighting.
- **Executioner palette failure.** A reviewed pack passed structural checks while rank colours collapsed to grey and elite hoods looked alike. Structural success did not meet the appearance brief; its later status must be checked in project state.
- **Nightborn local coverage.** Full-body lining obscured chest detail and protruded through boots. Local coverings and a deliberately shaped gorget replaced it; the first cut-mesh neck lining had a visibly jagged boundary. Expanded intermediate-pose checks exposed ankle and waist weight defects missed by the initial captures.
- **Nightborn assembled materials.** Bright green authored arms clashed with a dark reconstructed torso/helmet. A recorded material-factor correction reconciled the final appearance while preserving binary geometry, texture and clip data. Numeric material validity alone had not exposed the mismatch.
- **Ruby emission.** A fitting recipe introduced self-lit ruby dots. Disabling emission removed that error but did not by itself establish convincing gem surfaces; close-up and fight-scale review still mattered.

## Witch face assemblies and bind-pose fitting — 2026-09-28–29

The closed-helmet L8 pilot did not exercise the lower ranks' original-face/new-hood assembly. Retaining the whole original head introduced green hood protrusions; a frontal-only selection removed those protrusions in the reviewed L2–L7 backs, but L4/L5 still had donor facial fragments above the retained face. That partial repair did not establish clean face openings. Test each distinct assembly method before replication, and judge removal of the old hood separately from removal of the donor face.

The initial deformation checker selected new armour and missed the retained head primitive on the original body node. Expanding it to retained head, inner cowl and armour exposed stretching in the old hood fringe. Subsequent repairs passed the expanded check without relaxing its thresholds. Source-byte preservation alone had not established that the retained visible subset worked in the new assembly.

Witch's default node pose and mesh bind pose differed. Finger fitting used joint locations derived from the inverse-bind matrices in the mesh's coordinate frame, rather than default node-world positions. This was a fitting correction, not permission to replace the source rig or animation data; adapt matrix conventions and mesh/root transforms before reusing it.

Evidence: `/Users/domininclynch/Desktop/Business/artifacts/witch-ranks-20260928/FINAL-REVIEW.md`, `source/preserve_face.py`, `source/close_cowl.py`, `source/check_candidate.py`, `source/articulate_hands.py` and the final `review/` captures. These scripts contain Witch-specific bounds and bone names, not universal fitting parameters. The prolonged run also repeated an already-covered workflow error: batching and packaging before visual acceptance. That calls for following the existing acceptance gate, not adding more process.

## Mac browser capture path

Playwright Chromium with `args: ['--use-gl=angle', '--use-angle=metal']` succeeded on the tested Mac and avoided the slow SwiftShader path. Verify one capture on the current host rather than assuming availability. Load the model once and switch cameras; report any software fallback. Respect the current resource guard, and do not treat either backend as physical-phone evidence.

## Animation timing survives names but not necessarily export

The export retained 65 bone names and 25 clip names while shortening Draw from 0.700 to approximately 0.667 seconds. The check happened after batching and required fresh captures for all nine ranks.

Compare source/export clip durations, sampler times and interpolation, plus joint transforms at matched times, including endpoints. Use several samples in every clip; inspect suspect intervals more densely. Position agreement alone does not certify joint orientation, scale, skin deformation or collision clearance.

For this compatible skeleton, restoring original animation sampler bytes and joint rest transforms after export fixed the discrepancy. Five sampled times in each of 25 clips then matched original joint world positions within 5.14e-8 scene units. Before reusing that repair, verify unique target-node mapping, hierarchy, coordinate conventions and inverse-bind compatibility. Prefer fixing export settings when sufficient; do not copy this binary repair onto a changed rig without those checks.

## A continuous coat can acquire discontinuous weights

Adjacent L8 coat vertices followed opposite calves. In the Armed sample, 532 edge occurrences exceeded both 0.12 scene units in posed length and 3× their rest length; worst stretch was approximately 97.55×. These were triangle-edge occurrences, not necessarily unique edges. The thresholds and scale describe this diagnosis only.

Local bilateral smoothing on 9,173 new armour vertices reduced qualifying occurrences to 16 and removed the large central slab in matched front/attack/kick renders. Rear puckering remained. A preceding rigid pelvis-weight trial failed to remove the front defect and stiffened the skirt, so it was rejected.

Inspect rest/posed geometry and influences before repair. Use both absolute length and relative stretch to avoid ranking tiny numerical edges as the main defect. Blend the faulty region continuously into working weights, retain the runtime influence limit, and compare identical poses. Do not apply centre-line smoothing to unrelated limb geometry or describe this partial improvement as a universal cloth solver.

## Remote persistence failures are not reconstruction failures

The connector credential could submit work but uploading the result returned 403. A stored credential with suitable write permission worked through the SDK, supplied as a secret. Verify access with the same credential used by the job; local access under a different credential is insufficient. Keep this operational case in the character workflow rather than editing the bundled Hugging Face skill.

Hub downloads also failed on missing `X-Repo-Commit` metadata. An authenticated direct GET to a revision-pinned Hub URL recovered the saved artifact. Validate its expected hash before use, keep credentials out of logs, and retain normal TLS validation. For same-job review, reimport the just-exported local GLB instead of downloading it again. Persist the model before rendering so a render failure can resume from saved work. Bound transport retries; never regenerate geometry to fix an upload/download error.

## Preserve the final build sequence and its acceptance status

The selected GLBs included repairs made after saving the fitting scenes. Deliver those repair steps with their inputs, order and output hashes, or update the editable source so a rebuild includes them. Earlier scenes must be labelled as such. Any later model change invalidates prior model-hash render receipts.

Before repeating a pilot across ranks, distinguish blocking defects from disclosed review limitations. Plague Doctor's rough hems/cuffs and subdued materials carried into the ladder despite structural passes. A review pack may document those limits, but packaging or an arbitrary quality threshold cannot override the user's requested finish. Continuous animation, loot carriers, finishers and actual game/phone checks remain separate acceptance work.

## Cache original normals for bulk offsets

Nightborn's shell-offset loop stalled while reading a live vertex normal after each coordinate mutation. Caching all original normals once before applying offsets resolved the stall. Use this pattern when the operation is defined against the original surface normals; if it intentionally depends on the evolving surface, recompute at deliberate stages instead. A stalled job alone does not prove this diagnosis: locate the slow operation before changing the algorithm or retrying compute.

## Batch persistence with immutable upload contents

Nightborn's per-file Hub uploads hit a commit-rate limit while saving rank captures. Stage related outputs into bounded grouped commits rather than one commit per image. Capture each file's bytes immediately, or use unique immutable staging files, when accumulating upload operations: reused temporary paths can otherwise cause multiple entries to upload the last file written there.

Group persistence by useful recovery boundaries (for example, save the model before its render batch) rather than delaying every artifact until the entire ladder finishes. Respect service limits and bound retries; do not create repositories to evade a quota. Verify remote paths and hashes before treating a grouped upload as successful.

## Local case evidence

Evidence folder: `/Users/domininclynch/Desktop/Business/artifacts/plaguedoctor-ranks/`.

- `HANDOFF.md`, `manifest.json`, `animation-validation.json`, `coat-repair.json` and selected render receipts.
- `source/check_animation.py`, `source/preserve_clips.py` and `source/smooth_coat.py` are case implementations, not generic skill helpers. Adapt their model assumptions before reuse.

Nightborn evidence folder: `/Users/domininclynch/Desktop/Business/artifacts/nightborn-elites-covered-r2/`.

- `NOTES.md`, `reports/PILOT-ACCEPTANCE.md` and `delivery/HANDOFF.md` record rejected fits, selected candidates and remaining limitations.
- `source/build_elite.py`, `source/check_deformation.py`, `source/finish_emerald.py` and `source/batched_upload.py` demonstrate local covering/weight repairs, intermediate-pose checks, material-only correction and immutable grouped uploads. They contain Nightborn-specific paths, bones and spatial assumptions; inspect and adapt them rather than treating them as generic helpers.
