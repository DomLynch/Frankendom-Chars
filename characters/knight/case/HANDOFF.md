# Knight L2–L10 — isolated candidate delivery

Nine separate fitted rank candidates, built with TRELLIS.2 and Blender from the approved Knight. Closed angular helmets, lean underlying body proportions, original maul, 65-joint rig and all 37 original clips are preserved. L1 and game assets were not replaced.

Open `index.html` to compare every rank in front, back, side, attack, guard, kick and fight views. `models/` contains the selected GLBs. `source/` contains the immutable originals, references, untouched donors, editable fitting scenes, reconstruction receipts and ordered repair scripts. Raw fitting GLBs and scenes are labelled intermediates; use the selected models for review.

## Coverage

| Rank | Material and construction | Selected GLB | Seven views |
|---|---|---|---|
| L2 | Warm brown leather, strapped chest and stitched panels | Complete | Complete |
| L3 | Bone and hide, ribbed chest and narrow tassets | Complete | Complete |
| L4 | Hammered copper, horizontal chest fastenings | Complete | Complete |
| L5 | Aged bronze, chevron plates and layered shoulders | Complete | Complete |
| L6 | Iron, utilitarian plate, repaired underarm transition | Complete | Complete |
| L7 | Steel, fluted chest, stepped shoulders and closed sallet | Complete | Complete |
| L8 | Blackened steel and ruby, compact crown ridges | Complete | Complete |
| L9 | Emerald armour with swept helmet fins | Complete | Complete |
| L10 | Full gold, sun breastplate and tall open-point crown over closed helm | Complete | Complete |

Helmet, Body, Arms, Gloves, Greaves and Boots are visually represented at every rank. They are combined review models, not six independently takeable carrier exports.

## Verified evidence

- Source body/carrier/reference copied read-only from trunk `9ac3a41a38942204c03165757935054e0b882a70`; exact hashes in `source/originals.json`. The local game checkout remains `829dfdf8`, with its pre-existing two untracked gesture files untouched.
- Original binary prefix, original accessors, node transforms/hierarchy, skin/inverse binds and animation definitions remain exact in every candidate. This preserves clip times, durations, joint rotations and positions, rather than only the clip names. Original body geometry remains underneath an alpha-zero material; the visible armour surface is new.
- Nine finite-geometry/normalized-weight checks pass. Each final file has a SHA256, byte size, triangle counts, mesh/material counts and texture formats/dimensions in `manifest.json`. Totals include hidden original geometry and retained intermediate buffers. These 25–37 MB candidates are not optimized game budgets or measured draw costs.
- All 252 samples across Armed, Maul_Heavy, Maul_Guard and Kick have zero qualifying severe stretched-edge occurrences (edge >0.12 m and >3× rest length). Samples include endpoints and intermediate times. This is not continuous collision or finisher clearance.
- 63 final exported-file captures, each bound to the exact model and image hash. All use Blender 5.2.1 LTS, Cycles CPU, 32 samples, identical lights/pose times, 375×600 viewport and 64 transparent bounces. Fight captures measure 110 pixels of armour height. These are studio approximations, not arena or physical-phone proof.
- Full untruncated Khronos validation reports zero introduced errors. The original has 95 malformed-quaternion errors in Death_QuietOne; all nine candidates retain the identical error list. Warnings, including unused zero-weight joint indices, are retained in the complete reports. This is not a zero-error/zero-warning source asset.

## Selected process and repairs

L8 was proven before batching. Its initial 1024/100k/2048 donor lost visible surface detail; one controlled 1536/200k/2048 comparison was selected. The other eight selected donors each succeeded on their first reconstruction call at the higher setting. No donor regeneration was used to repair fitting. L7's reference was refined before reconstruction so steel has a structural step above iron.

The selected process fits the saved surface, transfers regional weights, retains exact source hands, packs only new geometry into the immutable original, and smooths demonstrated weight discontinuities. L6/L7 additionally use a continuous arm-position transition and consolidate new torso influences to resolve their underarm failures. L2 received a warm-brown material correction after neutral-light review.

MCP write preflight returned403; the SDK credential passed local and remote persistence checks. Bounded HF CPU jobs produced the models. The last two jobs reached the hourly repository-commit limit after saving their repaired models/scenes and partial images. Those saved assets were recovered without refitting. After the Mac deployment reservation cleared, final captures ran locally on two CPU threads. All owned remote jobs are terminal; `checks/jobs-final.json` records completed/error status. Billed dollars were not measured.

## Remaining defects and next owner

Fine reconstructed surfaces soften around some shoulder/elbow folds, and cuff/hand transitions retain the lower-detail original hand shapes. L6 keeps a dark donor-material shoulder scuff; a neutral-material diagnostic confirmed surface geometry exists there. These are visible finish limitations of the candidate pack, not a claim of flawless production art.

The character integration owner still needs six-slot separation and carrier mapping, helmet-removal/finisher behaviour, continuous weapon/armour clearance, actual arena camera checks and physical-phone performance. The inherited Death_QuietOne data defect needs a separately reviewed animation repair before production acceptance. No game replacement, commit, merge or deployment was performed by this task.

Rebuild order and tested dependency versions: `source/SOURCE_ORDER.md` and `source/requirements.txt`. Working originals remain unchanged; rejected trials are excluded from this archive. Selected source snapshots are included for reproducibility.
