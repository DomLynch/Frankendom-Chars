# /// script
# dependencies = ["gradio_client==2.7.1","huggingface_hub>=1.33.0","Pillow>=12.0","requests>=2.32.0"]
# ///
#!/usr/bin/env python3
import json, os, re, time
from pathlib import Path

import requests
from gradio_client import Client, handle_file
from PIL import Image

TOKEN = os.environ["HF_TOKEN"]
SRC_URL = "https://raw.githubusercontent.com/DomLynch/Frankendom-Chars/pitborn-l2-l10/characters/pitborn/generated/donor/L8-reference-v2.png"

src = Path("/tmp/L8-reference-v2.png")
r = requests.get(SRC_URL, timeout=60)
r.raise_for_status()
src.write_bytes(r.content)

im = Image.open(src).convert("RGBA")
px = im.load()
w, h = im.size
samples = []
step = max(1, min(w, h) // 64)
for x in range(0, w, step):
    samples += [px[x, 0][:3], px[x, h - 1][:3]]
for y in range(0, h, step):
    samples += [px[0, y][:3], px[w - 1, y][:3]]
bg = tuple(sorted(v[i] for v in samples)[len(samples) // 2] for i in range(3))

out = Image.new("RGBA", im.size)
op = out.load()
for y in range(h):
    for x in range(w):
        rr, gg, bb, _ = px[x, y]
        d = ((rr-bg[0])**2 + (gg-bg[1])**2 + (bb-bg[2])**2) ** 0.5
        aa = 0 if d < 16 else 255 if d > 38 else int((d - 16) / 22 * 255)
        op[x, y] = (rr, gg, bb, aa)
box = out.getbbox()
if box:
    pad = max(8, int(min(w, h) * 0.025))
    box = (max(0, box[0]-pad), max(0, box[1]-pad), min(w, box[2]+pad), min(h, box[3]+pad))
    out = out.crop(box)
rgba = Path("/tmp/L8-reference-v2-rgba.png")
out.save(rgba)
print("RGBA_READY", out.size, rgba.stat().st_size, flush=True)

deadline = time.time() + 18 * 60
attempt = 0
while time.time() < deadline:
    attempt += 1
    try:
        c = Client(
            "microsoft/TRELLIS.2",
            token=TOKEN,
            verbose=False,
            httpx_kwargs={"follow_redirects": True, "timeout": 90},
            download_files=False,
        )
        c.httpx_kwargs.pop("follow_redirects", None)
        c.predict(api_name="/start_session")
        print("AUTH_SESSION_OK", attempt, flush=True)
        t = time.time()
        c.predict(
            image=handle_file(str(rgba)),
            seed=290929,
            resolution="1536",
            ss_guidance_strength=7.5,
            ss_guidance_rescale=0.7,
            ss_sampling_steps=24,
            ss_rescale_t=5.0,
            shape_slat_guidance_strength=7.5,
            shape_slat_guidance_rescale=0.5,
            shape_slat_sampling_steps=24,
            shape_slat_rescale_t=3.0,
            tex_slat_guidance_strength=1.0,
            tex_slat_guidance_rescale=0.0,
            tex_slat_sampling_steps=24,
            tex_slat_rescale_t=3.0,
            api_name="/image_to_3d",
        )
        print("GEN_OK_SECONDS", round(time.time() - t, 1), flush=True)
        t = time.time()
        glb = c.predict(decimation_target=500000, texture_size=4096, api_name="/extract_glb")
        print("EXTRACT_OK_SECONDS", round(time.time() - t, 1), flush=True)
        print("TRELLIS_RESULT_JSON", json.dumps(glb, default=str), flush=True)
        break
    except Exception as exc:
        msg = str(exc)
        print("ATTEMPT_FAIL", attempt, msg[:700], flush=True)
        if "ZeroGPU quota" in msg:
            raise
        if time.time() + 15 >= deadline:
            raise
        time.sleep(15)
else:
    raise RuntimeError("TRELLIS deadline reached")
