# /// script
# dependencies = ["gradio_client==2.7.1","huggingface_hub>=1.33.0","Pillow>=12.0","requests>=2.32.0"]
# ///
import os, json, time, base64, requests
from io import BytesIO
from PIL import Image
from gradio_client import Client

TOKEN = os.environ["HF_TOKEN"]
SRC = "https://raw.githubusercontent.com/DomLynch/Frankendom-Chars/pitborn-l2-l10/characters/pitborn/generated/donor/L8-reference-v2.png"

raw = requests.get(SRC, timeout=60)
raw.raise_for_status()
im = Image.open(BytesIO(raw.content)).convert("RGBA")

# Remove near-uniform grey studio background and crop tightly.
px = im.load()
w, h = im.size
samples = []
step = max(1, min(w, h)//64)
for x in range(0,w,step):
    samples += [px[x,0][:3], px[x,h-1][:3]]
for y in range(0,h,step):
    samples += [px[0,y][:3], px[w-1,y][:3]]
bg = tuple(sorted(v[i] for v in samples)[len(samples)//2] for i in range(3))
out = Image.new("RGBA", im.size)
op = out.load()
for y in range(h):
    for x in range(w):
        r,g,b,_ = px[x,y]
        d = ((r-bg[0])**2 + (g-bg[1])**2 + (b-bg[2])**2) ** 0.5
        a = 0 if d < 16 else 255 if d > 38 else int((d-16)/22*255)
        op[x,y] = (r,g,b,a)
box = out.getbbox()
if box:
    pad = max(8, int(min(w,h)*0.025))
    box = (max(0,box[0]-pad), max(0,box[1]-pad), min(w,box[2]+pad), min(h,box[3]+pad))
    out = out.crop(box)

buf = BytesIO()
out.save(buf, format="PNG")
png = buf.getvalue()
data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
filedata = {
    "path": None,
    "url": data_url,
    "size": len(png),
    "orig_name": "L8-reference-v2-rgba.png",
    "mime_type": "image/png",
    "is_stream": False,
    "meta": {"_type":"gradio.FileData"},
}
print("INPUT_READY", out.size, len(png), flush=True)

c = Client(
    "microsoft/TRELLIS.2",
    token=TOKEN,
    verbose=False,
    httpx_kwargs={"follow_redirects":True,"timeout":90},
    download_files=False,
)
c.httpx_kwargs.pop("follow_redirects", None)
c.predict(api_name="/start_session")
print("SESSION_OK", flush=True)

t=time.time()
c.predict(
    image=filedata,
    seed=290929,
    resolution="1024",
    ss_guidance_strength=7.5,
    ss_guidance_rescale=0.7,
    ss_sampling_steps=12,
    ss_rescale_t=5.0,
    shape_slat_guidance_strength=7.5,
    shape_slat_guidance_rescale=0.5,
    shape_slat_sampling_steps=12,
    shape_slat_rescale_t=3.0,
    tex_slat_guidance_strength=1.0,
    tex_slat_guidance_rescale=0.0,
    tex_slat_sampling_steps=12,
    tex_slat_rescale_t=3.0,
    api_name="/image_to_3d",
)
print("GEN_SECONDS", round(time.time()-t,1), flush=True)

t=time.time()
glb = c.predict(decimation_target=100000, texture_size=2048, api_name="/extract_glb")
print("EXTRACT_SECONDS", round(time.time()-t,1), flush=True)
print("GLB_JSON", json.dumps(glb, default=str), flush=True)
