from pathlib import Path
from huggingface_hub import HfApi,CommitOperationAdd
import subprocess,sys,json,shutil,hashlib
r=Path(__file__).resolve().parents[1];ranks=list(map(int,sys.argv[1:]));api=HfApi();files=[]
for rank in ranks:
 p=r/f'models/nightborn-L{rank}.glb'
 if rank!=8 and not p.exists():
  folder=r/f'review/{"ladder" if rank==9 else "corrected"}/L{rank}'
  d=json.loads((folder/'deformation.json').read_text());assert len(d)==6 and all(x['bad_edges']==0 for x in d),(rank,d)
  shutil.copy2(folder/p.name,p);subprocess.run([sys.executable,str(r/'source/preserve_clips.py'),str(p)],check=True)
 files.append(str(p))
subprocess.run([sys.executable,str(r/'source/validate.py'),*files],check=True)
api.create_commit(repo_id='Domlynch/frankendom-nightborn-delivery-20260928',repo_type='dataset',operations=[CommitOperationAdd(path_in_repo='final/'+p.name,path_or_fileobj=str(p)) for p in map(Path,files)],commit_message='Save selected final Nightborn GLBs')
name='render-final-'+ '-'.join(map(str,ranks))+'.py';s=(r/'source/batched_upload.py').read_text()+'\n'+(r/'source/render_final.py').read_text().replace('RANKS=[8]',f'RANKS={ranks!r}').replace('frankendom-nightborn-ranks-20260928','frankendom-nightborn-delivery-20260928').replace('os._exit(0)','_flush_uploads();os._exit(0)');(r/'source'/name).write_text(s)
subprocess.run([sys.executable,str(r/'source/submit.py'),name],check=True)
