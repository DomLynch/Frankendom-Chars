# Pitborn L2-L10 — Codex handoff

Updated: 2026-09-29

## Scope / repository boundary

- **Authoritative game source (READ ONLY):** `DomLynch/RPG-game`
- **All character work / output:** `DomLynch/Frankendom-Chars`
- Active branch: `pitborn-l2-l10`
- Do **not** modify `RPG-game` while doing this character-art task.
- Preserve existing Pitborn L1 unchanged.

## Goal

Build Pitborn ranks L2-L10, but prove **L8 first** before batching.

Pitborn identity: existing orc-blooded pit brute, not a generic knight. Preserve the shipped body proportions, 65-bone rig, hunch, animation set and cleaver placement.

Elite brief:
- L8 = blackened steel + small deep-ruby accents, full arms/thighs, closed brutal gladiator visor.
- L9 = emerald/dark steel, distinct horned/executioner silhouette.
- L10 = full gold, boss-tier infernal crown/closed helmet.
- L8/L9/L10 must be clearly different geometry/silhouettes, not recolours.

Full ladder palette:
- L2 leather brown
- L3 bone/hide
- L4 copper
- L5 bronze
- L6 iron
- L7 steel
- L8 blackened steel/ruby
- L9 emerald
- L10 gold

## Locked Pitborn source

From `DomLynch/RPG-game`:

- `src/assets/pitborn.glb`
  - bytes: 6,046,748
  - sha256: `f202ebf6d119c08f37259965d1e34f4d5debc253631a765834693286461de86a`
  - Git blob: `9d8108a8192ea3f8cbab1393ad4ea40641e21e1e`
- `src/assets/source/parts/body_pitborn.glb`
- `src/assets/source/parts/level1_pitborn.glb`
- cleaver source in RPG repo (see `source-lock.json`)
- current rank/legend images under `public/legends/pitborn-*.webp`

Builder contract from the game:
- scale = **1.13**
- hunch:
  - spine_02 +7°
  - spine_03 +7°
  - neck_01 -7°
  - Head -6°
- weapon = **cleaver**
- shared humanoid rig = 65 bones

See `characters/pitborn/source-lock.json`.

## What was completed

### 1) Source lock + project notes

Committed:
- `characters/pitborn/README.md`
- `characters/pitborn/BUILD_STATE.md`
- `characters/pitborn/L8-ACCEPTANCE.md`
- `characters/pitborn/source-lock.json`

### 2) Fast TRELLIS L8 review donor — REAL GLB

Successful authenticated HF Pro TRELLIS run:
- generation: 47.8 s
- extraction: 36.1 s
- resolution: 1024
- samplers: 12 steps
- output target: 100k faces
- texture: 2048
- seed: 290929

Saved model:
- `characters/pitborn/fast-L8/pitborn-L8-trellis-review.glb`
- size: 5,597,688 bytes

Exact-model previews:
- `characters/pitborn/fast-L8/previews/L8-donor-front.png`
- `characters/pitborn/fast-L8/previews/L8-donor-back.png`
- `characters/pitborn/fast-L8/previews/L8-donor-left.png`
- `characters/pitborn/fast-L8/previews/L8-donor-right.png`
- `characters/pitborn/fast-L8/previews/L8-donor-hero-a.png`
- `characters/pitborn/fast-L8/previews/L8-donor-hero-b.png`

Receipt:
- `characters/pitborn/fast-L8/receipt.json`
- checksums: `characters/pitborn/fast-L8/SHA256SUMS`

### 3) First rigged procedural pilot — technically useful, visually rejected

There is an earlier rigged/exported L8 proof under:
- `characters/pitborn/generated/`

It preserved:
- 65 joint names
- 25 animation clips by name

But animation-value comparison was not byte/exact-equivalent on many clips after Blender re-export, so `pilot_acceptance_pass=false` in:
- `characters/pitborn/generated/reports/L8-validation.json`

Its visual armour was crude/blocky and should **not** be used as the final art direction.

### 4) Concept/reference work

Useful files:
- `characters/pitborn/generated/donor/Pitborn-source-exact.png`
- `characters/pitborn/generated/donor/L8-reference.png`
- `characters/pitborn/generated/donor/L8-reference-v2.png`
- prompts in `characters/pitborn/prompts/`

The current fast TRELLIS donor derived from `L8-reference-v2.png`.

## Why the current L8 donor is NOT final

The actual TRELLIS donor renders show:
- face still too open
- upper arms exposed
- thighs exposed
- armour too clean / knight-like
- blackened-steel + ruby read is weak
- not enough crude pit-forged asymmetry / bone-trophy identity

Do not call it production-ready.

## Failed / abandoned routes

### Shared TRELLIS Space
The Microsoft `microsoft/TRELLIS.2` Space intermittently returned 502s on upload/queue endpoints. Authenticated HF Pro worked eventually and produced the fast review donor.

### Direct GPU job
A dedicated A100 job was tested but cancelled because the user explicitly wanted the cheap 32 GB CPU box for orchestration and the shared GPU-backed Space for TRELLIS.

### Nightborn donor transplant
A fast alternative attempted to reuse the existing Nightborn L8 elite armour as a donor and fit it to Pitborn.

Script:
- `scripts/pitborn/build_l8_from_nightborn.py`

Workflow:
- `.github/workflows/pitborn-l8-donorbuild.yml`

Initial failure:
- Blender Python could not import the Nightborn donor due missing Meshopt decoder:
  `libbf_intern_meshopt_bridge.so`

Patch applied:
- workflow now tries to decompress the Nightborn donor with `@gltf-transform/cli` before Blender import
- script accepts `PITBORN_L8_DONOR`

This path was still in progress when the task was stopped. Treat it as experimental, not approved.

## Recommended next step in Codex

Do **one L8 only** until it passes.

Fastest sensible route:

1. Start from the real Pitborn source GLB.
2. Preserve the existing Pitborn body, armature, cleaver and animation data.
3. Build/fix an L8 armour donor with:
   - truly closed helmet
   - full upper-arm shells
   - full thigh shells/tassets
   - blackened forged steel
   - restrained ruby
   - asymmetry + old bone/tusk trophies
   - no long cloth skirt
   - no paladin/knight cleanliness
4. Prefer reusing/fixing a saved donor over another full TRELLIS reconstruction if possible.
5. If using TRELLIS again, first generate a corrected reference that explicitly closes the face and covers arms/thighs, then run the fast 1024/100k/2048 review pass.
6. Fit/rebind donor to the existing Pitborn rig **without replacing the rig**.
7. Export one candidate: `pitborn-L8.glb`.
8. Reimport that exact exported GLB and render:
   - front
   - back
   - left/right
   - head closeup
   - Armed / Heavy / Guard / Kick
   - ~375 px and ~110 px fight-scale
9. Validate:
   - same skeleton hierarchy/joint names
   - same inverse-bind intent
   - same animation names, durations, key times/values/interpolation as source
   - cleaver placement unchanged
   - no armour detachment/clipping in key poses
10. Only after L8 approval, batch L2-L7 + L9-L10.

## Important quality rule

Do not confuse:
- concept/reference image
- raw TRELLIS donor
- fitted rigged candidate
- final production GLB

The user specifically wants **actual exported-model previews**, not concept images presented as if they were the final model.

## Useful scripts

- `scripts/pitborn/trellis_fast_review.py`
- `scripts/pitborn/trellis_pro.py`
- `scripts/pitborn/render_trellis_donor.py`
- `scripts/pitborn/build_l8.py`
- `scripts/pitborn/validate_l8.py`
- `scripts/pitborn/build_l8_from_nightborn.py`

Also inspect the existing Nightborn/Knight/Dwarf character-case scripts in this repository for proven rig-preservation, helmet and coverage patterns.

## Compute/auth notes

Hugging Face:
- account: `Domlynch`
- Pro: yes
- `cpu-upgrade` was used as the cheap ~32 GB orchestration box
- TRELLIS generation was run through the official Microsoft Space using the authenticated Pro token
- never print/store tokens in repo

## Stop state

User cancelled this attempt and will continue in Codex.

Do not resume background work from this chat. No further automation should be active.
