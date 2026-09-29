"""Bounded SDK fallback after MCP OAuth write preflight 403. Secrets never logged."""
from pathlib import Path
import json,sys,urllib.request
from huggingface_hub import HfApi,get_token,hf_hub_url
ROOT=Path(__file__).resolve().parents[1];REPO='Domlynch/frankendom-knight-ranks-20260928';api=HfApi()
mode,label=sys.argv[1:3]
if mode=='submit':
    source=Path(sys.argv[3]).read_text()
    command="apt-get update -qq && apt-get install -y -qq libgl1 libxrender1 libxi6 libxkbcommon0 libsm6 libgomp1 >/dev/null && pip install -q bpy==4.5.3 huggingface_hub numpy scipy pillow && python -u - <<'PYJOB'\n"+source+'\nPYJOB'
    job=api.run_job(image='python:3.11-bookworm',command=['bash','-lc',command],flavor='cpu-upgrade',timeout='20m',secrets={'HF_TOKEN':get_token()},env={'HF_HUB_DISABLE_PROGRESS_BARS':'1'})
    receipt={'id':job.id,'url':job.url,'script':str(Path(sys.argv[3]).resolve()),'timeout':1200}
    (ROOT/'checks'/f'{label}-job.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
elif mode=='download':
    dest=ROOT/sys.argv[3];dest.mkdir(exist_ok=True,parents=True)
    revision=api.repo_info(REPO,repo_type='dataset').sha
    for name in api.list_repo_files(REPO,repo_type='dataset',revision=revision):
        if not name.startswith(label+'/'):continue
        local=dest/Path(name).name
        if local.exists():continue
        req=urllib.request.Request(hf_hub_url(REPO,name,repo_type='dataset',revision=revision),headers={'Authorization':'Bearer '+get_token()})
        with urllib.request.urlopen(req,timeout=90) as response:local.write_bytes(response.read())
    print('Downloaded',label,'to',dest)
elif mode=='status':
    receipt=json.loads((ROOT/'checks'/f'{label}-job.json').read_text());info=api.inspect_job(job_id=receipt['id']);print(info.status.stage)
else:raise ValueError(mode)
