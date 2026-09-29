from huggingface_hub import HfApi,get_token
from pathlib import Path
import json,sys,hashlib
r=Path(__file__).resolve().parents[1];name=sys.argv[1];code=(r/'source'/name).read_text()
compile(code,name,'exec')
command="apt-get update -qq && apt-get install -y -qq libgl1 libxrender1 libxi6 libxkbcommon0 libsm6 libgomp1 >/dev/null && pip install -q bpy==4.5.3 huggingface_hub==1.8.0 && python - <<'PYJOB'\n"+code+"\nPYJOB"
j=HfApi().run_job(image='python:3.11-bookworm',command=['bash','-lc',command],flavor='cpu-upgrade',timeout='15m',secrets={'HF_TOKEN':get_token()},env={'HF_HUB_DISABLE_XET':'1','HF_HUB_DISABLE_PROGRESS_BARS':'1'})
submitted=r/'reports/submitted';submitted.mkdir(exist_ok=True);(submitted/(j.id+'.py')).write_text(code)
d={'script_sha256':hashlib.sha256(code.encode()).hexdigest(),'id':j.id,'url':j.url,'script':name,'timeout_seconds':900,'hardware':'cpu-upgrade'};(r/'reports'/('job-'+name+'.json')).write_text(json.dumps(d,indent=2));print(json.dumps(d))
