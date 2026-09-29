"""Bounded rear-coat weight trial; original geometry and weights untouched."""

import json
from pathlib import Path
from huggingface_hub import HfApi, get_token

ROOT = Path(__file__).resolve().parents[1]
code = """
import bpy, os, json
from pathlib import Path
from huggingface_hub import HfApi, get_token, hf_hub_url
import urllib.request
REPO = "Domlynch/frankendom-plaguedoctor-pilot-20260928"
R = Path('/tmp/plague'); R.mkdir(exist_ok=True)
url=hf_hub_url(REPO,'ladder/L8/plaguedoctor-L8.blend',repo_type='dataset',revision=HfApi().repo_info(REPO,repo_type='dataset').sha)
with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+get_token()}),timeout=120) as response:
    (R/'input.blend').write_bytes(response.read())
bpy.ops.wm.open_mainfile(filepath=str(R/'input.blend'))
donor = bpy.data.objects['L8_Armour']
def smooth(a,b,v):
    t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
changed=0
for v in donor.data.vertices:
    x,y,z=v.co
    # Rear skirt is continuous across both legs. Keep its central panel pelvis-led
    # instead of stretching it between independently moving calves.
    t=smooth(.10,.18,y)*(1-smooth(.90,1.08,z))*smooth(.20,.32,z)
    if t <= .0001: continue
    weights={donor.vertex_groups[g.group].name:g.weight*(1-t) for g in v.groups}
    weights['pelvis']=weights.get('pelvis',0)+t
    for g in list(v.groups): donor.vertex_groups[g.group].remove([v.index])
    weights=dict(sorted(weights.items(),key=lambda q:q[1],reverse=True)[:4]);total=sum(weights.values())
    for n,w in weights.items():
        if w>0:(donor.vertex_groups.get(n) or donor.vertex_groups.new(name=n)).add([v.index],w/total,'REPLACE')
    changed+=1
bpy.ops.wm.save_as_mainfile(filepath=str(R/'plaguedoctor-L8.blend'))
bpy.ops.export_scene.gltf(filepath=str(R/'plaguedoctor-L8.glb'),export_format='GLB',use_visible=True,export_animations=True,export_tangents=False)
api=HfApi()
for name in ['plaguedoctor-L8.glb','plaguedoctor-L8.blend']:
    api.upload_file(path_or_fileobj=str(R/name),path_in_repo='repair-L8/'+name,repo_id=REPO,repo_type='dataset')
print('CHANGED_COAT_VERTICES',changed,flush=True)
"""
render = (ROOT / "source/render_remote.py").read_text()
render = render.replace(
    '[("original", "original.glb"), ("L10", "proof-v2.glb")]',
    '[("L8", "repair-L8/plaguedoctor-L8.glb")]',
)
render = render.replace(
    "with urllib.request.urlopen(request, timeout=90) as response:\n        path.write_bytes(response.read())",
    'path.write_bytes(Path("/tmp/plague/plaguedoctor-L8.glb").read_bytes())',
)
render = render.replace("proof-v2/", "repair-L8/")
command = (
    "apt-get update -qq && apt-get install -y -qq libgl1 libxrender1 libxi6 libxkbcommon0 libsm6 libgomp1 >/dev/null && pip install -q bpy==4.5.3 huggingface_hub && python - <<'PYJOB'\n"
    + code
    + "\n"
    + render
    + "\nPYJOB"
)
job = HfApi().run_job(
    image="python:3.11-bookworm",
    command=["bash", "-lc", command],
    flavor="cpu-upgrade",
    timeout="15m",
    secrets={"HF_TOKEN": get_token()},
    env={"HF_HUB_DISABLE_XET": "1", "HF_HUB_DISABLE_PROGRESS_BARS": "1"},
)
receipt = {
    "id": job.id,
    "url": job.url,
    "scope": "L8 rear coat weight trial, six matched exported-file captures",
    "timeout": 900,
}
(ROOT / "job-repair-L8.json").write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
