# Rebuild order

Selected exports are in ../../models. The .blend and matching raw .glb in each rank folder are fitted intermediates, BEFORE the mandatory post-export steps. Do not deliver them as final.

Runtime: Python 3.11 / python:3.11-bookworm, with exact tested packages in requirements.txt. Container tag was recorded; image digest was not pinned. TRELLIS service revision, settings, seed, timings and donor hash are in reconstruction.json; source generation used 1536 resolution, 200000 target triangles, 2048 maps and 36 steps per stage after the L8 comparison.

L2–L7/L9/L10: the rank-specific build script contains fitting → raw export → immutable-original packing → 320 iterations of new-armour weight smoothing → exact source gloves with rank material → final reimport/render. L2 includes the accepted warm-brown material correction. L6/L7 use continuous arm displacement and consolidate new torso influences before smoothing. Original low-saturation L2 and rejected underarm fits are excluded.

L8: use pilot_v6_pipeline.py for the selected fitted scene/export; pack_preserved.py on original.glb and that raw export; smooth_weights.py with 320; then exact_gloves.py. The latter retains original hand positions, weights and material with the L8 colour multiplier. Render with render-L8-final.py. The packed/smoothed buffers remain embedded by design, so file size is higher than an optimized game asset.

All scripts use a private task Hub repository for persistence. Credentials are read from the environment or authenticated SDK and are not included. Existing donors require no reconstruction call. For an offline rebuild, substitute the local original/donor paths and omit Hub upload steps. The original 37 animation definitions, timing/accessor bytes, nodes and skin are copied exactly rather than accepted from Blender re-export.

The original body is retained with an alpha-zero material beneath the new surface. Cycles captures require transparent_max_bounces=64. This workaround is a studio setting, not a runtime performance certification. Original maul and source hands are retained. Six-slot carrier assembly is not included.

Final captures were regenerated consistently on local Blender 5.2.1 LTS build9e2066aef7ef, CPU two threads, after the deployment reservation ended. Use render_final_local.py from the parent artifact workspace, or update its models/review paths to this unpacked folder. This render-only step does not export or change any GLB. All 63 final image receipts record the renderer and final model/image hashes. The fitting runtime remains the recorded Blender4.5.3 requirements above.

Remote persistence recovery: prefer upload_folder/create_commit with a batch of artifacts, not one commit per PNG. The two repaired models and scenes had already persisted before the task hit the repository's hourly commit limit; their final renders were safely completed locally. No additional reconstruction or token changes were needed.
