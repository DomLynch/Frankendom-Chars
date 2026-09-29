#!/usr/bin/env python3
import argparse, hashlib, json, shutil, time
from pathlib import Path
from gradio_client import Client, handle_file

ap=argparse.ArgumentParser()
ap.add_argument("--image",required=True)
ap.add_argument("--prompt",required=True)
ap.add_argument("--out",required=True)
ap.add_argument("--seed",type=int,default=290926)
ap.add_argument("--guidance",type=float,default=2.8)
ap.add_argument("--steps",type=int,default=30)
a=ap.parse_args()
text=Path(a.prompt).read_text().strip()
client=Client("black-forest-labs/FLUX.1-Kontext-Dev", verbose=False)
t=time.time()
res=client.predict(input_image=handle_file(a.image),prompt=text,seed=a.seed,randomize_seed=False,guidance_scale=a.guidance,steps=a.steps,api_name="/infer")
p=res[0] if isinstance(res,(tuple,list)) else res
p=p.get("path") if isinstance(p,dict) else p
out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,out)
rec={"space":"black-forest-labs/FLUX.1-Kontext-Dev","source":a.image,"source_sha256":hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),"prompt":text,"seed":a.seed,"guidance":a.guidance,"steps":a.steps,"seconds":round(time.time()-t,1),"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"bytes":out.stat().st_size}
out.with_suffix(".kontext.json").write_text(json.dumps(rec,indent=2)+"\n")
print(json.dumps(rec))
