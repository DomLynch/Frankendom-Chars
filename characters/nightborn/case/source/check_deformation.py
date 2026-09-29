from glb_checks import read,arr,transforms,ROOT
from pathlib import Path
import numpy as np,json,sys,hashlib
results=[]
for filename in sys.argv[1:]:
 p=Path(filename);m,b=read(p);restm=dict(m);restm['animations']=[{'name':'REST','channels':[],'samplers':[]}];restworld=transforms(restm,b,'REST',0);meshes=[]
 for n in m['nodes']:
  if not n.get('name','').startswith(('L8_','L9_','L10_')) or 'mesh' not in n or 'skin' not in n:continue
  sk=m['skins'][n['skin']];bone_names=[m['nodes'][i]['name'] for i in sk['joints']];ib=arr(m,b,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
  for pr in m['meshes'][n['mesh']]['primitives']:
   at=pr['attributes'];pos=arr(m,b,at['POSITION']);j=arr(m,b,at['JOINTS_0']);w=arr(m,b,at['WEIGHTS_0']);tri=arr(m,b,pr['indices']).reshape(-1,3);edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);hpos=np.column_stack([pos,np.ones(len(pos))])
   def skin(world):
    matrices=np.array([world[name] for name in bone_names])@ib
    return sum(w[:,k,None]*np.einsum('nij,nj->ni',matrices[j[:,k]],hpos) for k in range(4))[:,:3]
   r=skin(restworld);length=np.linalg.norm(r[edges[:,0]]-r[edges[:,1]],axis=1);meshes.append((n['name'],bone_names,ib,hpos,j,w,edges,length,r))
 samples=[]
 for clip,viewtime in [('Armed',8/24),('Heavy',11/24),('Guard',10/24),('Kick',10/24)]:
  a=next(a for a in m['animations'] if a['name']==clip);end=max(float(arr(m,b,s['input'])[-1,0]) for s in a['samplers'])
  for time in sorted(set([viewtime,*np.linspace(0,end,5).tolist()])):
   world=transforms(m,b,clip,time);bad=[];worst=0
   for name,bone_names,ib,hpos,j,w,edges,length,r in meshes:
    matrices=np.array([world[n] for n in bone_names])@ib;posed=sum(w[:,k,None]*np.einsum('nij,nj->ni',matrices[j[:,k]],hpos) for k in range(4))[:,:3];assert np.isfinite(posed).all();pl=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1);ratio=pl/np.maximum(length,1e-6);count=int(np.sum((pl>.10)&(ratio>3)));worst=max(worst,float(ratio.max()))
    if count:
     selected=np.where((pl>.10)&(ratio>3))[0];selected=sorted(selected,key=lambda i:-pl[i])[:3];bad.append({'mesh':name,'edges':count,'top':[{'restGltf':r[edges[i]].tolist(),'length':float(pl[i]),'ratio':float(ratio[i])} for i in selected]})
   samples.append({'clip':clip,'time':float(time),'longStretchedEdges':sum(x['edges'] for x in bad),'badMeshes':bad,'worstRatio':worst})
 result={'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'meshPrimitivesChecked':len(meshes),'threshold':'posed edge > 0.10m AND > 3x rest','samples':samples,'worstLongEdgeCount':max(x['longStretchedEdges'] for x in samples)};results.append(result);print(p.name,'sampled poses',len(samples),'worst long edges',result['worstLongEdgeCount'],flush=True)
(ROOT/'reports/deformation-expanded.json').write_text(json.dumps(results,indent=2))
