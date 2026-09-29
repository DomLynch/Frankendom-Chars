"""Independent scene/material checks plus saved-original preservation. Visual coverage remains required."""
from glb_checks import read,arr,ROOT
from pathlib import Path
import sys,json,hashlib,numpy as np
results=[]
for name in sys.argv[1:]:
 p=Path(name);m,b=read(p);label=p.stem.split('-')[-1];active=[]
 def visit(i):
  n=m['nodes'][i]
  if 'mesh'in n:active.append(n)
  for c in n.get('children',[]):visit(c)
 for i in m['scenes'][m.get('scene',0)]['nodes']:visit(i)
 names=[n.get('name','') for n in active];forbidden=[n for n in names if n in ['Face','Photo','PhotoEyes','PhotoTeeth','Skin'] or 'CrownRuby'in n or 'SweptProng'in n or 'OpenCrown'in n];assert not forbidden,forbidden
 expected=[label+'_ClosedHelmet',label+'_CompleteJointCover',label+'_ArmouredArmsAndGauntlets'];assert all(n in names for n in expected)
 mats=[];weights=[]
 for n in active:
  mesh=m['meshes'][n['mesh']]
  for pr in mesh['primitives']:
   mat=m['materials'][pr['material']];mats.append(mat.get('name',''))
   if n.get('name')==label+'_ClosedHelmet':
    assert mat.get('emissiveFactor',[0,0,0])==[0,0,0]
    j=arr(m,b,pr['attributes']['JOINTS_0']);w=arr(m,b,pr['attributes']['WEIGHTS_0']);sk=m['skins'][n['skin']];bones={m['nodes'][sk['joints'][int(k)]]['name'] for k in j[w>0]};assert bones=={'Head'},bones
 assert not any(s in mats for s in ['Face','Photo','PhotoEyes','PhotoTeeth','Oxblood glove leather'])
 results.append({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'activeMeshNames':names,'activeMaterialNames':sorted(set(mats)),'visibleOriginalFaceSkinOrOpenCrowns':forbidden,'helmetBoundToOriginalHeadOnly':True,'requiredCoverageMeshesPresent':True,'limitation':'Scene tests do not replace front/back/side and motion inspection for holes, intersections or skin-like donor textures.'})
(ROOT/'reports/coverage.json').write_text(json.dumps(results,indent=2));print('coverage scene checks',len(results),'passed')
