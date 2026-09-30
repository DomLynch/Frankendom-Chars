# Shieldmaiden L1 recruit — 30 September 2026

Separate recruit candidate below the owner-approved L2–L10 ladder: patched flax tunic, cord belt, dark cloth trousers, wraps and plain boots. No cuirass, pauldrons, metal plates or elaborate headgear. Original face/hair, finger articulation, proportions and weapon retained.

The package includes `models/shieldmaiden-L1.glb`, matching final Blender scene, donor/reference, ten final-export views, an L1/L2 comparison, scripts, pinned dependencies and checks. See `manifest.json` for exact model/scene hashes and `SHA256SUMS` for package contents.

**Validation:** source binary prefix, node hierarchy, skins/inverse binds and actual animation data preserved: 65 joints per skin and all 25 clips. Every visible skinned primitive passes 54 Armed/Attack/Heavy/Guard/Kick/Roll samples with zero long stretched edges. Final Blender scene is reopened remotely and its embedded GLB hash checked. All 95 format errors exactly match the locked original; one skinned-node transform warning is added. The current game asset has a different resource hash but identical nodes, skins, inverse-bind values and all clip data; comparison is saved.

**Review limitations:** original reconstructed face/hair remain coarse in close-up, with inherited facial cracks. Collar/cuff transitions and cloth hems are candidate quality. No game, continuous clipping, finisher/carrier or device-performance acceptance is claimed. Original game asset and L2–L10 files were not edited.

**Production path:** one built-in image reference and one authenticated Pro TRELLIS.2 reconstruction at 1024 / 100k target triangles / 2048 textures. The verified Shieldmaiden fitting/preservation pipeline was reused. One local cuff correction removes residual donor hands and extends the original weighted forearm under the sleeve. Rejected first captures are excluded. Remote CPU Blender was sufficient; no local Metal render or dedicated GPU was needed. CPU jobs use 30-minute bounds at $0.03/hour. One render-dispatch import failure was repaired without regenerating geometry.

**Reproduce:** Python 3.13 with `source/requirements-cloud.txt`; set `RANK=L1`. The ordered stages are in `source/job.py`: fitting, source packing, anatomical weights, 30 smoothing iterations, retained face/hands, debris/material finish, preservation/deformation checks, exact-GLB rendering. The included `retain_hands.py` contains the final cuff bounds. `source/render_only.py` reopens the saved scene for hash verification. `source/submit.py` submits bounded paid work explicitly; no cloud calls are part of repository tests. Job IDs and immutable input revisions are in `checks/`.

Stored triangles, active visible triangles/primitives/materials, GLB bytes and texture formats/sizes are recorded separately in `checks/inventory.json`; these are not measured draw calls. Runtime GLB: 26,811,016 bytes; stored triangles: 109,544; visible triangles: 90,938.

Latest repo/local character skills and troubleshooting were read. Three Semble queries and Codegraph MCP localized the existing workflow; only the L1 wrapper/cuff constants and evidence gate changed. Original rank pipeline and unrelated dirty skill/Pitborn files were preserved. Next owner: artist/game integrator, for in-game acceptance of this separate candidate.
