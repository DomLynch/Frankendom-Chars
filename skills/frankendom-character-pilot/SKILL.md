---
name: frankendom-character-pilot
description: Build and review original Frankendom-style character assets from image references using reconstruction, Blender surface-preserving assembly and real GLB camera checks. Use for character or armour pilots and preserving an approved sculpt during fitting; not a claim of production readiness.
---

# Frankendom character builds

Default workflow: approved brief → reference art → saved reconstruction → Blender fitting → exported-model pilot → remaining ranks → verified delivery. Preserve the selected appearance and original rig. Apply the owner's latest character-specific decisions; this skill does not impose one face rule on every character.

For weapon shapes and rank variants, read [weapon-specific workflow](references/weapon-shapes.md); use the active weapon brief for dimensions, budgets and material ownership.

## 1. Lock the brief and originals

Record the character/asset ID, requested ranks, source revision/hash, proportions, silhouette, weapon identity, grip and weapon-side clearance. Keep originals and approved ranks immutable; work in separate named candidates.

For corrections, preserve accepted parts and repair only the failed requirement. Reuse saved assets; reopen broader reconstruction only when a demonstrated defect requires it.

Make a rank coverage matrix: face/hair, neck, upper/lower arms, hands, thighs/lower legs and feet; record required coverage, helmet height and distinct elite structures. Resolve it from the current brief and approved decisions, not another character's defaults. A reviewer's suggestion does not override owner approval. Update the matrix when scope changes, including added ranks.

Preserve the approved palette:

| Rank | Look |
|---|---|
| L1 | Rags, muted earth tones |
| L2 | Brown leather |
| L3 | Bone and hide |
| L4 | Copper |
| L5 | Bronze |
| L6 | Iron |
| L7 | Steel |
| L8 | Blackened steel and ruby |
| L9 | Emerald |
| L10 | Full gold |

L8–L10 require different, identity-appropriate headgear structures, not recolours. Dark clothing must not turn every armour rank charcoal. Judge the assembled ladder under identical neutral lighting. Preserve explicit character exceptions; dated examples are in the troubleshooting reference, not a substitute for the current brief.

## 2. Prepare references and reconstruction

Generate original reference art when needed; label it separately from actual 3D evidence. Record reference, generator/service revision, seed, settings, output hashes, scale and transforms. Verify current service capabilities and licence before a new reconstruction run.

For comparable rank donors, start with **1024 reconstruction, 100,000 target triangles and 2048 textures**. These are demonstrated starting settings, not a game budget or a quality guarantee. Higher resolution does not establish anatomy, finger separation, clearance, topology or animation readiness. Reuse saved textured donors for fitting/material repairs; reconstruct again only for required new forms or a demonstrated source defect. Keep paid retries within existing authorization and out of automatic checks.

Inspect donor front/side/rear, especially thin crests, hands, feet and weapons. Preserve it before modification. Use Pixelmator only for a specific texture/decal defect on the correct UV atlas; see [texture trials](references/pixelmator.md). For the original Sand Legionary recipe, read [its dated case record](references/sand-legionary.md).

## 3. Fit geometry, coverage and materials

Fit scale/orientation to the game convention. Preserve selected outer surfaces and UVs; spatial cuts are only initial separation, and broad remeshing/projection can destroy approved detail. Repair failed accessories individually and inspect seating, silhouette and collisions against this character's actual body.

Distinguish the mesh bind pose from the default node pose before deriving anatomy for fitting or weight transfer. They can differ. Compare joint locations derived from the inverse-bind matrices with the mesh in a common coordinate frame, accounting for mesh/root transforms; do not assume default node transforms describe the unposed fingers or limbs.

Missing hands, sleeves or feet require geometry, not weight transfer. Where suitable, derive local coverings from original rigged anatomy, preserving finger weights. Fit coverings to observed gaps: full-body linings can protrude through good armour. Use deliberate cuffs/collars and joint overlap rather than exposed raw cut edges. Skin patches alone are not a complete fitting body/head. Disclose when reconstructed surfaces replace the visible original, even if original geometry remains stored.

When retaining an original face inside reconstructed headwear, remove the donor face from the visible opening and exclude unwanted original outer headwear. Inspect for duplicate facial fragments and old hood protrusion in front/head and side/rear views. A height-only cut does not reliably separate face, hood and lining; retain the approved face attributes/weights and fit its surrounding coverage deliberately.

Preserve working original weights. Across shared slot boundaries, keep position/weight continuity and blend adjustments into the neck rather than moving collar vertices rigidly with a helmet. Benchmark new transfer methods against the unchanged baseline. Closest-triangle barycentric transfer is a useful candidate, but cloth between opposing limbs can still acquire discontinuous weights.

Localize faulty influences before smoothing. Position-based adjacency can repair seams across duplicated UV vertices without welding geometry or UVs; constrain it to the affected surface so independent layers/limbs are not joined. Normalize to the runtime influence limit. Spatial bounds and tolerances are model-specific. Compare matched poses after repair.

Audit base colour, emission, roughness, metalness, texture bindings and extensions after fitting/export. Treat metal, skin, leather and stone separately. L8 rubies use deep crimson facets, aged settings and reflected highlights without self-lit emission. Compare authored coverings and reconstructed armour together; reconcile mismatched finishes while retaining surface detail. A material-factor repair may suffice—verify unrelated geometry, texture and animation data stay unchanged.

## 4. Pass the exported pilot before batching

Validate one representative rank for each materially different assembly method before batching that method. A closed-helmet pilot does not validate a retained-face/open-hood assembly; palette-only variants do not require separate method pilots. Apply these independent checks:

- **Preservation:** compare hierarchy, rest transforms, inverse-bind compatibility, original vertex/weight signatures and every clip's names, durations, sampler times/values and interpolation. Compare sampled joint transforms, including endpoints; names alone are insufficient. Restore source animation data only after compatibility checks.
- **Geometry and deformation:** require finite geometry and normalized weights. Check every visible skinned primitive in the final assembly, including retained source geometry and added primitives on an existing node, through intermediate times and endpoints of Armed/Heavy/Guard/Kick or rig equivalents. Do not select only newly named armour meshes; record any intentionally hidden-source exclusions. Localize defects with rest/posed edge coordinates and influences. Use absolute length plus relative stretch at the model's scale; increase sampling around failures. Sampled passes do not establish continuous clearance.
- **Visible quality:** inspect the actual final GLB from front/back/side, hero/high rear and head close-up, plus matched action poses. Inspect collar, shoulders, armpits, wrists, fingers, skirt, knees, soles and feet. Include 375px views and a measured 110px fight figure. Compare coverage, silhouette, palette and assembled materials against the brief.

Use Khronos glTF Validator for format and Blender checks for topology; neither replaces visible inspection. From this skill directory, run `python3 scripts/inspect_glb.py /absolute/path/model.glb` for inventory/hash only. Its stored mesh totals include nodes outside the active scene and are not measured draw costs.

Record explicit pilot acceptance: which observed defects block replication and which limitations fit the requested review milestone. Fix blocking identity, coverage, deformation, palette or finish issues first. Then inspect every remaining rank independently, especially changed elite shapes. Recheck the final appearance after the last repair; a structural pass never overrides the brief.

## 5. Execute and recover reproducibly

Pin tested dependencies. Respect deployment/resource guards; serialize expensive local bakes/browser checks. On Mac, prefer verified Metal browser rendering where available; see the troubleshooting reference for flags and fallback. If the Mac is occupied, use the Hugging Face Jobs skill for already-authorized, bounded remote CPU work with timeout and persisted outputs. Submission is not completion; honour pauses and spending limits.

Before expensive remote work, prove a tiny upload/download round trip using the actual job credential and destination. Persist the exported model before rendering; reimport that local export for same-job captures, then persist images. Batch uploads using immutable bytes or unique staging paths. Transport failures should resume from saved artifacts, not trigger reconstruction.

Build sequence: scene → export → recorded repairs → validation → authoritative model hash → final renders/receipts. Persist each recoverable stage. Include repair scripts or update the scene; label pre-repair scenes. Any later model change invalidates earlier render receipts.

When a result deteriorates, compare donor, fitted export and packed export under matched conditions; repair the first damaged stage. Read [fitting, export and execution troubleshooting](references/export-and-cloth-troubleshooting.md) for weight seams, animation restoration, bulk-normal caching and transport failures. A timeout alone does not diagnose geometry or CPU starvation.

## 6. Deliver with an explicit acceptance level

Deliver selected models, source scenes/donors, reproducible repair order, rank completion matrix, front/back sheets, camera/pose/model-hash receipts, checks and remaining defects. Label rejected alternatives. Record owner, exact inputs/outputs and next validation; monitoring alone is not a repair. Avoid duplicating another owner's work or editing their checkout without coordination.

Report stored versus active triangles/mesh/material counts, runtime GLB bytes, texture formats/resolutions and archive bytes separately. Report measured draw calls/performance only when actually measured.

A review candidate is distinct from production approval. Production additionally needs required slot pieces and closed boundaries, complete fitting body/helmet-off face where specified, pivots/units, verified grips/bindings, continuous clearance, carrier/finisher integration, requested PBR budgets and actual game/phone behavior. Studio captures, desktop emulation and software WebGL do not prove physical-phone performance. Keep outstanding checks assigned and visible.
