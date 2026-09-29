from pathlib import Path
import sys,subprocess
r=Path(__file__).resolve().parents[1];ranks=list(map(int,sys.argv[1:]));blocks=[];render=(r/'source/pilot_v8_job.py').read_text().split('a=api;out=R\n')[1]
for rank in ranks:
 s=(r/f'source/build-L{rank}.py').read_text().replace('hand=smooth(.63,.67,ax)','hand=smooth(.55,.68,ax)')
 if rank==7:
  s=s.replace('near=(strength',"strength=np.maximum(strength,np.clip((coords[:,2]-.08)/.08,0,1)*np.clip((.32-coords[:,2])/.10,0,1)*np.clip((np.abs(coords[:,0])-.10)/.04,0,1)*.48)\nnear=(strength")
 if rank==2:s=s.replace('*np.clip((np.abs(coords[:,1])-.045)/.045,0,1)','')
 s=s.replace(f'ladder/L{rank}/',f'corrected/L{rank}/').replace('os._exit(0)','');(r/f'source/corrected-L{rank}.py').write_text(s)
 capture=render.replace('L8',f'L{rank}').replace('pilot-v8/',f'corrected/L{rank}/').replace('os._exit(0)','');blocks.extend([s,'a=api;out=R\n'+capture])
name='corrected-'+ '-'.join(map(str,ranks))+'.py';code='\n'.join(blocks)+'\nos._exit(0)\n';compile(code,name,'exec');(r/'source'/name).write_text(code)
subprocess.run([sys.executable,str(r/'source/submit.py'),name],check=True)
