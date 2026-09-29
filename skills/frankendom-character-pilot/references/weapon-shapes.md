# Weapon shapes and rank variants

Use alongside the main skill's preservation, exported-model review and acceptance checks; those checks are not repeated here.

- Reconcile the latest brief against the shipped weapon's measured local-space bounds, contact zone and grip positions. Record discrepancies; do not silently change combat reach. Keep dimensions and budget exceptions in the project brief.
- Establish rank differences through silhouette and construction before adding engraving. Translate the concept's defining shapes into a quick exported-mesh preview before detailed finishing. Follow the weapon brief's rank grouping and material ownership rather than inheriting character-specific headgear or palette requirements.
- After reflecting or reshaping boolean operands, recalculate normals. Avoid redundant coincident cuts; check topology after each major assembly so defects can be traced to the responsible operation.
- Check exported vertex ratio and UV overlap together. Automatic packing can satisfy one and fail the other; tune against both checks rather than copying fixed settings. State whether overlap testing is sampled or analytic.
- Run geometry, format and UV checks, and inspect their results, before expensive rendering. Use one diagnostic view while iterating; produce the full capture set once checks pass. Stop an obsolete render batch when a required repair changes its input.
- Benchmark one frame on the chosen render backend. Bound stalled GPU compilation and retain a verified CPU fallback; a working browser Metal path does not establish that Blender Cycles Metal is ready.

## Maul case — 2026-09-28

The v2 pilot exposed three reusable failure modes: transformed cutters needed corrected normals; repeating a through-cut produced nonmanifold edges; one xatlas layout passed the vertex cap but left 12 overlapping pixel-centre samples. A different chart setting removed those samples while reducing the exported ratio. These outcomes do not make that setting a universal preset.

Local evidence: `/Users/domininclynch/Desktop/Business/artifacts/weapon-variants-20260928/maul-v2/`. Consult `NOTES.md` and `receipts/` for outcomes, and `source/verify.py`, `source/uv_audit.py` and `source/xatlas_uv.py` for implementations. They contain maul-specific assumptions; adapt them to the current brief rather than copying their bounds or budgets unchanged.
