# Pitborn build state

Updated: 2026-09-29

## Repository boundaries

- **Read-only source:** `DomLynch/RPG-game`
- **All new work/delivery:** `DomLynch/Frankendom-Chars`, branch `pitborn-l2-l10`
- No game integration work is part of this task.

## Source discovery complete

Authoritative inputs located in `RPG-game`:

- `src/assets/pitborn.glb` — shipped rigged Pitborn
- `src/assets/source/parts/body_pitborn.glb`
- `src/assets/source/parts/level1_pitborn.glb`
- `src/assets/weapons/cleaver/cleaver.glb`
- Pitborn material maps under `src/assets/source/materials/`
- Pitborn current image references under `public/game/img/`, `public/legends/`, and `public/versus/`

The game builder records Pitborn as a 1.13-scale shared-humanoid rig with a forward hunch and the cleaver. Those transforms are protected.

## Execution

1. Freeze exact source hashes.
2. Inspect shipped GLB hierarchy, skins, animations, weapon node and material ownership.
3. Build one L8 donor/assembly only.
4. Fit L8 to the existing Pitborn rig; no skeleton replacement.
5. Export and reimport L8.
6. Verify rig/animation equivalence and visible coverage/deformation.
7. Only after L8 passes, batch L2–L10.
8. Publish GLBs, source scene, donor, scripts, previews, receipts and defect list here / in a GitHub Release.

## Compute receipts

- HF source-download validation: job `6abb4e6352d0dbd7f1da94c3` — source returned HTTP 200, 6,046,748 bytes; SHA256 recorded in source-lock.
- HF GLB inspection: job `6abb4eaa6b030d633f6a2d90` — inspection workload submitted on `cpu-upgrade`.
- These are validation/inspection jobs only; neither is a claim that an L8 model has been built.

## Acceptance bar

L8 is not accepted from a concept render. Acceptance requires the actual exported GLB, exact source-rig/animation comparison, coverage/deformation review and model-hash-linked captures.
