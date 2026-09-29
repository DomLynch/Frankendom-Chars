from pathlib import Path
import sys,subprocess,json,hashlib,os
R=Path(__file__).resolve().parents[1];O=R.parent/'nightborn-ranks-20260928/delivery';paths=[O/f'models/nightborn-L{x}.glb' for x in range(2,8)]+[R/'models/pilot-v5/nightborn-L8.glb']+[R/'models/elites-v2/nightborn-L9.glb',R/'models/elites-v1/nightborn-L10.glb']
for name,targets,report in [('validate.py',paths,'validation.json'),('check_coverage.py',paths[-3:],'coverage.json'),('check_deformation.py',paths[-3:],'deformation-expanded.json')]:
 subprocess.run([sys.executable,str(R/'source'/name),*map(str,targets)],check=True);(R/'reports'/('final-'+report)).write_bytes((R/'reports'/report).read_bytes())
env=dict(os.environ,GLTF_VALIDATOR_PATH=str(R.parent/'sand-legionary-pilot/source/validation/node_modules/gltf-validator'));subprocess.run(['node',str(R/'source/format_check.cjs'),*map(str,paths)],env=env,check=True);(R/'reports/final-format-validation.json').write_bytes((R/'reports/format-validation.json').read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R/'reports/lower-ranks-preserved.json').read_text());checks={f'L{k}':sha(O/f'models/nightborn-L{k}.glb')==h for k,h in old.items()};checks['originalSource']=sha(R/'original/nightborn.glb')==sha(R.parent.parent/'frankendom/src/assets/nightborn.glb')=='ffd772602ac354fd1f2e3b29df5bc08937f0f5561804d5512d3fcced48c2a504';assert all(checks.values());(R/'reports/final-preservation.json').write_text(json.dumps({'allUnchanged':True,'checks':checks},indent=2))
assert all(x['worstLongEdgeCount']==0 for x in json.loads((R/'reports/final-deformation-expanded.json').read_text()))
assert all(x['errors']==0 for x in json.loads((R/'reports/final-format-validation.json').read_text()))
print('FINAL ASSET CHECKS PASS')
