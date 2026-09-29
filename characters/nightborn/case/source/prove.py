from pathlib import Path
from huggingface_hub import HfApi,CommitOperationAdd
import sys,subprocess,shutil,json
R=Path(__file__).resolve().parents[1];version=sys.argv[1];ranks=list(map(int,sys.argv[2:]));files=[]
for rank in ranks:
 p=R/f'models/{version}/nightborn-L{rank}.glb';p.parent.mkdir(exist_ok=True)
 if not p.exists():
  shutil.copy2(R/f'review/covered-r2/{version}/L{rank}/{p.name}',p)
  subprocess.run([sys.executable,str(R/'source/preserve_clips.py'),str(p)],check=True)
 files.append(str(p))
subprocess.run([sys.executable,str(R/'source/validate.py'),*files],check=True)
subprocess.run([sys.executable,str(R/'source/check_coverage.py'),*files],check=True)
repo='Domlynch/frankendom-nightborn-delivery-20260928';prefix=f'covered-r2/{version}-proof'
HfApi().create_commit(repo_id=repo,repo_type='dataset',operations=[CommitOperationAdd(path_in_repo=prefix+'/'+Path(p).name,path_or_fileobj=p) for p in files],commit_message=f'Preserved-clips Nightborn {version} proof inputs')
s=(R/'source/batched_upload.py').read_text()+'\n'+(R/'source/render_final.py').read_text().replace('RANKS=[8]',f'RANKS={ranks!r}').replace('covered-r2/final',prefix)
name='render-'+version+'-'+ '-'.join(map(str,ranks))+'.py';(R/'source'/name).write_text(s)
subprocess.run([sys.executable,str(R/'source/submit.py'),name],check=True)
