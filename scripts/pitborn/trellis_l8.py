#!/usr/bin/env python3
import argparse, hashlib, json, shutil, time
from pathlib import Path
from gradio_client import Client, handle_file

ap=argparse.ArgumentParser()
ap.add_argument("--image",required=True)
ap.add_argument("--out",required=True)
ap.add_argument("--receipt",required=True)
ap.add_argument("--seed",type=int,default=290929)
a=ap.parse_args()

c=Client("microsoft/TRELLIS.2",verbose=False)
t0=time.time()
c.predict(api_name="/start_session")
pre=c.predict(input=handle_file(a.image),api_name="/preprocess_image")
prepath=pre["path"] if isinstance(pre,dict) else pre
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
t2=time.time()
glb=c.predict(decimation_target=500000,texture_size=4096,api_name="/extract_glb")
p=glb[1] if isinstance(glb,(list,tuple)) and len(glb)>1 else glb
if isinstance(p,dict): p=p["path"]
out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,out)
rec={
 "space":"microsoft/TRELLIS.2","image":a.image,
 "image_sha256":hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),
 "seed":a.seed,"resolution":"1536","faces":500000,"texture":4096,
 "ss_sampling_steps":24,"shape_sampling_steps":24,"texture_sampling_steps":24,
 "preprocess_seconds":round(t1-t0,1),"generation_seconds":round(t2-t1,1),
 "total_seconds":round(time.time()-t0,1),
 "bytes":out.stat().st_size,"sha256":hashlib.sha256(out.read_bytes()).hexdigest()
}
Path(a.receipt).parent.mkdir(parents=True,exist_ok=True)
Path(a.receipt).write_text(json.dumps(rec,indent=2)+"\n")
print(json.dumps(rec))
