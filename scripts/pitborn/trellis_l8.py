#!/usr/bin/env python3
import argparse, hashlib, json, os, re, shutil, sys, time
from pathlib import Path

from gradio_client import Client, handle_file
from PIL import Image

ap=argparse.ArgumentParser()
ap.add_argument("--image",required=True)
ap.add_argument("--out",required=True)
ap.add_argument("--receipt",required=True)
ap.add_argument("--seed",type=int,default=290929)
ap.add_argument("--timeout-minutes",type=float,default=30)
a=ap.parse_args()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def make_rgba(src: Path) -> Path:
    im=Image.open(src).convert("RGBA")
    px=im.load(); w,h=im.size
    # TRELLIS matting has been fragile on opaque studio backgrounds.
    # Use the border/corner colour to create a genuine transparent RGBA input.
    samples=[]
    step=max(1,min(w,h)//64)
    for x in range(0,w,step):
        samples.append(px[x,0][:3]); samples.append(px[x,h-1][:3])
    for y in range(0,h,step):
        samples.append(px[0,y][:3]); samples.append(px[w-1,y][:3])
    bg=tuple(sorted(v[i] for v in samples)[len(samples)//2] for i in range(3))
    out=Image.new("RGBA",im.size)
    op=out.load()
    for y in range(h):
        for x in range(w):
            r,g,b,_=px[x,y]
            d=((r-bg[0])**2+(g-bg[1])**2+(b-bg[2])**2)**0.5
            # soft alpha edge: studio bg gone, subject retained
            alpha=0 if d<18 else 255 if d>42 else int((d-18)/24*255)
            op[x,y]=(r,g,b,alpha)
    # Crop transparent margins but leave breathing room.
    box=out.getbbox()
    if box:
        pad=max(8,int(min(w,h)*0.025))
        box=(max(0,box[0]-pad),max(0,box[1]-pad),min(w,box[2]+pad),min(h,box[3]+pad))
        out=out.crop(box)
    dest=src.with_name(src.stem+"-rgba.png")
    out.save(dest)
    return dest

src=Path(a.image)
rgba=make_rgba(src)
deadline=time.time()+a.timeout_minutes*60
attempt=0
receipt={
 "space":"microsoft/TRELLIS.2",
 "image":str(src),"image_sha256":sha(src),
 "transparent_input":str(rgba),"transparent_sha256":sha(rgba),
 "seed":a.seed,"resolution":"1536","faces":500000,"texture":4096,
 "ss_sampling_steps":24,"shape_sampling_steps":24,"texture_sampling_steps":24,
}
try:
    from huggingface_hub import get_token
    token=os.environ.get("HF_TOKEN") or get_token()
except Exception:
    token=os.environ.get("HF_TOKEN")

while True:
    attempt+=1
    t0=time.time()
    try:
        c=Client("microsoft/TRELLIS.2",token=token,verbose=False,
                 httpx_kwargs={"follow_redirects":True,"timeout":90})
        c.httpx_kwargs.pop("follow_redirects",None)
        c.predict(api_name="/start_session")
        try:
            pre=c.predict(input=handle_file(str(rgba)),api_name="/preprocess_image")
            prepath=pre["path"] if isinstance(pre,dict) else pre
            receipt["preprocess_mode"]="space"
        except Exception as exc:
            # Transparent RGBA is already matted. If the Space's preprocessing
            # endpoint is flaky, attempt the generator directly rather than
            # throwing away a valid input.
            print("preprocess failed; direct RGBA fallback:",str(exc)[:300],file=sys.stderr,flush=True)
            prepath=str(rgba)
            receipt["preprocess_mode"]="direct-rgba-fallback"
            receipt["preprocess_error"]=str(exc)[:500]
        receipt["preprocess_seconds"]=round(time.time()-t0,1)
        t1=time.time()
        c.predict(
          image=handle_file(prepath),
          seed=a.seed,
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
          api_name="/image_to_3d"
        )
        receipt["generation_seconds"]=round(time.time()-t1,1)
        t2=time.time()
        glb=c.predict(decimation_target=500000,texture_size=4096,api_name="/extract_glb")
        receipt["extract_seconds"]=round(time.time()-t2,1)
        p=glb[1] if isinstance(glb,(list,tuple)) and len(glb)>1 else glb
        if isinstance(p,dict): p=p["path"]
        out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,out)
        receipt.update(
          attempts=attempt,total_seconds=round(time.time()-t0,1),
          bytes=out.stat().st_size,sha256=sha(out)
        )
        Path(a.receipt).parent.mkdir(parents=True,exist_ok=True)
        Path(a.receipt).write_text(json.dumps(receipt,indent=2)+"\n")
        print(json.dumps(receipt))
        break
    except Exception as exc:
        remaining=deadline-time.time()
        msg=str(exc)
        print(f"attempt {attempt} failed: {msg[:500]}",file=sys.stderr,flush=True)
        if remaining<=0:
            raise
        m=re.search(r"(\d+):(\d+):(\d+)",msg)
        wait=(int(m[1])*3600+int(m[2])*60+int(m[3])) if m else min(45,remaining)
        if "exceeded" in msg.lower() and wait>remaining:
            raise
        time.sleep(min(wait,remaining))
