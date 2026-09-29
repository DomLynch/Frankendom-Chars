# /// script
# dependencies = ["gradio_client==2.7.1","huggingface_hub>=1.33.0","Pillow>=12.0","requests>=2.32.0"]
# ///
import base64, json, os, time, traceback
from pathlib import Path
import requests
from gradio_client import Client
from PIL import Image

TOKEN=os.environ["HF_TOKEN"]
SRC_URL="https://raw.githubusercontent.com/DomLynch/Frankendom-Chars/pitborn-l2-l10/characters/pitborn/generated/donor/L8-reference-v2.png"

def stage(path):
    with open(path,"rb") as f:
        r=requests.post("https://tempfile.org/api/upload/local",
            files={"files":(Path(path).name,f)},data={"expiryHours":"24"},timeout=300)
    r.raise_for_status(); j=r.json()
    if not j.get("success"): raise RuntimeError(j)
    return j["files"][0]["url"].rstrip("/")+"/download"

def first_path(x):
    if isinstance(x,str) and Path(x).exists(): return x
    if isinstance(x,dict):
        p=x.get("path")
        if p and Path(p).exists(): return p
    if isinstance(x,(list,tuple)):
        for item in reversed(x):
            p=first_path(item)
            if p: return p
    return None

src=Path("/tmp/L8-reference-v2.png")
r=requests.get(SRC_URL,timeout=60); r.raise_for_status(); src.write_bytes(r.content)
im=Image.open(src).convert("RGBA")
px=im.load(); w,h=im.size
samples=[]; step=max(1,min(w,h)//64)
for x in range(0,w,step): samples += [px[x,0][:3],px[x,h-1][:3]]
for y in range(0,h,step): samples += [px[0,y][:3],px[w-1,y][:3]]
bg=tuple(sorted(v[i] for v in samples)[len(samples)//2] for i in range(3))
out=Image.new("RGBA",im.size); op=out.load()
for y in range(h):
    for x in range(w):
        rr,gg,bb,_=px[x,y]
        d=((rr-bg[0])**2+(gg-bg[1])**2+(bb-bg[2])**2)**0.5
        aa=0 if d<16 else 255 if d>38 else int((d-16)/22*255)
        op[x,y]=(rr,gg,bb,aa)
box=out.getbbox()
if box:
    pad=max(8,int(min(w,h)*.025))
    box=(max(0,box[0]-pad),max(0,box[1]-pad),min(w,box[2]+pad),min(h,box[3]+pad))
    out=out.crop(box)
rgba=Path("/tmp/L8-reference-v2-rgba.png"); out.save(rgba)
data_url="data:image/png;base64,"+base64.b64encode(rgba.read_bytes()).decode("ascii")
filedata={"path":None,"url":data_url,"size":rgba.stat().st_size,"orig_name":rgba.name,
          "mime_type":"image/png","is_stream":False,"meta":{"_type":"gradio.FileData"}}
print("RGBA_READY",out.size,rgba.stat().st_size,flush=True)

deadline=time.time()+18*60
client=None
attempt=0
while time.time()<deadline and client is None:
    attempt+=1
    try:
        c=Client("microsoft/TRELLIS.2",token=TOKEN,verbose=False,
                 httpx_kwargs={"follow_redirects":True,"timeout":90})
        c.httpx_kwargs.pop("follow_redirects",None)
        c.predict(api_name="/start_session")
        print("AUTH_SESSION_OK",attempt,flush=True)
        t=time.time()
        c.predict(image=filedata,seed=290929,resolution="1536",
            ss_guidance_strength=7.5,ss_guidance_rescale=0.7,ss_sampling_steps=24,ss_rescale_t=5.0,
            shape_slat_guidance_strength=7.5,shape_slat_guidance_rescale=0.5,shape_slat_sampling_steps=24,shape_slat_rescale_t=3.0,
            tex_slat_guidance_strength=1.0,tex_slat_guidance_rescale=0.0,tex_slat_sampling_steps=24,tex_slat_rescale_t=3.0,
            api_name="/image_to_3d")
        print("GEN_OK_SECONDS",round(time.time()-t,1),flush=True)
        client=c
    except Exception as e:
        print("GEN_ATTEMPT_FAIL",attempt,repr(e),flush=True)
        traceback.print_exc()
        if "ZeroGPU quota" in str(e): raise
        time.sleep(15)
if client is None: raise RuntimeError("generation deadline reached")

fallbacks=[(500000,4096),(500000,2048),(300000,4096),(300000,2048)]
errors=[]
for faces,tex in fallbacks:
    try:
        t=time.time()
        res=client.predict(decimation_target=faces,texture_size=tex,api_name="/extract_glb")
        print("EXTRACT_RESULT",faces,tex,json.dumps(res,default=str)[:1200],flush=True)
        p=first_path(res)
        if not p: raise RuntimeError("extract returned no downloaded GLB")
        staged=stage(p)
        rec={"source":SRC_URL,"seed":290929,"resolution":"1536","steps":24,
             "faces":faces,"texture":tex,"staged_model":staged,"bytes":Path(p).stat().st_size}
        rp=Path("/tmp/L8-trellis-stage.json"); rp.write_text(json.dumps(rec,indent=2))
        print("EXTRACT_OK_SECONDS",round(time.time()-t,1),"BYTES",Path(p).stat().st_size,flush=True)
        print("STAGE_MODEL",staged,flush=True)
        print("STAGE_REPORT",stage(rp),flush=True)
        raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as e:
        errors.append([faces,tex,repr(e)])
        print("EXTRACT_FALLBACK_FAIL",faces,tex,repr(e),flush=True)
        traceback.print_exc()
        time.sleep(5)
raise RuntimeError("all extraction settings failed: "+json.dumps(errors))
