from pathlib import Path
from huggingface_hub import HfApi
import subprocess,sys
R=Path(__file__).resolve().parents[1];ranks=list(map(int,sys.argv[1:]));api=HfApi();blocks=[]
render=(R/'source/pilot_v8_job.py').read_text().split('a=api;out=R\n')[1]
for rank in ranks:
 donor=R/f'src/assets/source/creatures/nightborn-L{rank}-donor.glb';assert donor.exists()
 api.upload_file(path_or_fileobj=str(donor),path_in_repo=f'L{rank}-donor.glb',repo_id='Domlynch/frankendom-nightborn-ranks-20260928',repo_type='dataset')
 subprocess.run([sys.executable,str(R/'source/prepare_rank.py'),str(rank)],check=True)
 code=(R/f'source/build-L{rank}.py').read_text().replace('os._exit(0)','')
 capture=render.replace('L8',f'L{rank}').replace('pilot-v8/',f'ladder/L{rank}/').replace('os._exit(0)','')
 blocks.extend([code,'a=api;out=R\n'+capture])
name='batch-'+ '-'.join(map(str,ranks))+'.py';code='\n'.join(blocks)+'\nos._exit(0)\n';compile(code,name,'exec');(R/'source'/name).write_text(code);print('READY',name,flush=True)
subprocess.run([sys.executable,str(R/'source/submit.py'),name],check=True)
