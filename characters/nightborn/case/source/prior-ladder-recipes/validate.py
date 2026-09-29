from glb_checks import read,arr,transforms,ROOT
import sys,json,hashlib,numpy as np
original,ob=read(ROOT/'original/nightborn.glb');results=[]
for arg in sys.argv[1:]:
 p=__import__('pathlib').Path(arg);m,b=read(p);assert [a['name'] for a in m['animations']]==[a['name'] for a in original['animations']]
 worst=0;timing_equal=True;samplers_equal=True
 for oa,ma in zip(original['animations'],m['animations']):
  oc={(original['nodes'][c['target']['node']]['name'],c['target']['path']):oa['samplers'][c['sampler']] for c in oa['channels']}
  mc={(m['nodes'][c['target']['node']]['name'],c['target']['path']):ma['samplers'][c['sampler']] for c in ma['channels']}
  assert oc.keys()==mc.keys(),oa['name']
  for key,s in oc.items():
   d=mc[key];timing_equal&=np.array_equal(arr(original,ob,s['input']),arr(m,b,d['input']));samplers_equal&=np.array_equal(arr(original,ob,s['output']),arr(m,b,d['output'])) and s.get('interpolation','LINEAR')==d.get('interpolation','LINEAR')
  end=max(float(arr(original,ob,s['input'])[-1,0]) for s in oa['samplers'])
  for t in np.linspace(0,end,9):
   x=transforms(original,ob,oa['name'],t);y=transforms(m,b,ma['name'],t);worst=max(worst,max(float(np.max(np.abs(x[n]-y[n]))) for n in x))
 tris=0
 for mesh in m['meshes']:
  for pr in mesh['primitives']:
   attrs=pr['attributes'];assert np.isfinite(arr(m,b,attrs['POSITION'])).all()
   if 'WEIGHTS_0'in attrs:
    w=arr(m,b,attrs['WEIGHTS_0']);assert np.isfinite(w).all() and np.min(w)>=0 and np.allclose(w.sum(axis=1),1,atol=.002)
   tris+=m['accessors'][pr['indices']]['count']//3
 result={'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'trianglesIncludingHiddenOriginals':tris,'exactSamplerTimes':bool(timing_equal),'exactSamplerValues':bool(samplers_equal),'maxJointMatrixDelta':worst,'sampleCount':25*9,'status':'passed' if timing_equal and samplers_equal and worst<1e-5 else 'failed'};results.append(result)
print(json.dumps(results,indent=2));(ROOT/'reports/validation.json').write_text(json.dumps(results,indent=2));assert all(r['status']=='passed' for r in results)
