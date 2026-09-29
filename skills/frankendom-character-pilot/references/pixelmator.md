# Optional Pixelmator texture trials

Pixelmator Pro 3.8 AppleScript was tested locally. It is background GUI automation, not true headless operation. `open -g` avoids intentionally taking focus; a graphical login session is still needed. Blender `-b` is genuinely headless.

Reliable pattern in pilot `pixelmator/run-parts.py`:
- Copy each input to a unique UUID filename. Open with LaunchServices `open -g -a 'Pixelmator Pro' <file>`.
- Wait with a bounded deadline; resolve full filename for native `.pxd`, otherwise stem. Capture document ID and check actual dimensions.
- Address that ID for every edit/export. Never rely on `front document`: asynchronous opening previously selected the wrong document and exported a 1021×1403 image instead of 1024×1024.
- Duplicate the image layer and lock the reference layer. Apply only an intentional editable-layer change. Export PXD before downsampling. Export PNG sizes serially, reopen PXD and verify layers/dimensions.
- Validate UV-mask alpha where used, pixel change when intended, and unchanged source GLB hash. Close only task-owned documents.

Timeouts (-1712), title reuse such as `skin-base 2`, and `.pxd` title matching were distinct failure causes. Busy CPU/swap can contribute but was not a complete diagnosis.

Four earlier face/hands/feet/weapon masters were verified but use a different fitting body and team longsword UVs. They are not automatically compatible with the approved hero or gladius, and they are not new anatomical geometry.

`pixelmator/finish-hero.py` instead extracted the approved hero atlas and applied brightness +5, saturation +6, contrast -4, exporting 2048/1024/512 PNG and a two-layer PXD. Geometry and UVs stayed identical. Owner preferred original; these settings are an example of a rejected trial, not a recommended preset.

The trial GLB grew from 10.61 to 16.83 MiB because a PNG was appended while retaining original binary texture data. A promoted asset should be repacked to remove unused payload and assessed for codec/resolution; do not call that growth improved geometry or detail.
