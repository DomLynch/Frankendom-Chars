"""Use exact source hand accessors, avoiding Blender bind-pose vertex baking."""
from pathlib import Path
import sys,copy,json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pack_preserved import read,arr,write
source,candidate,dest=sys.argv[1:4];g,b=read(source);d,db=read(candidate);binary=bytearray(db)
body=next(n for n in g['nodes'] if n.get('name')=='CreatureBody');p=g['meshes'][body['mesh']]['primitives'][0];a=p['attributes'];pos=arr(g,b,a['POSITION']);w=arr(g,b,a['WEIGHTS_0']);j=arr(g,b,a['JOINTS_0']);names=[g['nodes'][i]['name'] for i in g['skins'][0]['joints']]
mask=np.array([x.startswith(('hand_','thumb_','index_','middle_','ring_','pinky_')) for x in names]);s=(w*mask[j]).sum(1);tri=arr(g,b,p['indices']).reshape(-1,3);cent=pos[tri].mean(1)
keep=(s[tri].mean(1)>.15)&(cent[:,1]>.70)&(cent[:,1]<1.00)&(abs(cent[:,2])<.145)&(abs(cent[:,0])>.20)
t=tri[keep];_,inv=np.unique(np.round(pos,5),axis=0,return_inverse=True);edges=np.concatenate([inv[t[:,[0,1]]],inv[t[:,[1,2]]],inv[t[:,[2,0]]]]);adj=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(inv.max()+1,inv.max()+1));_,labels=connected_components(adj,directed=False);fl=labels[inv[t[:,0]]]
selected=[];components=[]
for label,count in zip(*np.unique(fl,return_counts=True)):
    verts=pos[np.unique(t[fl==label])];center=verts.mean(0)
    if count>100 and center[2]>.015:selected.append(t[fl==label]);components.append({'triangles':int(count),'center':center.tolist()})
indices=np.concatenate(selected).astype('<u4').ravel();assert len(components)>=2
binary.extend(b'\0'*((-len(binary))%4));vi=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':indices.nbytes,'target':34963});binary.extend(indices.tobytes());ai=len(d['accessors']);d['accessors'].append({'bufferView':vi,'componentType':5125,'count':len(indices),'type':'SCALAR','min':[int(indices.min())],'max':[int(indices.max())]})
hand=copy.deepcopy(p);hand['indices']=ai
mat=copy.deepcopy(g['materials'][p['material']]);mat['name']='Knight exact original gauntlets';mat['pbrMetallicRoughness']['baseColorFactor']=[.5,.5,.52,1];hand['material']=len(d['materials']);d['materials'].append(mat)
node=next(n for n in d['nodes'] if n.get('name')=='Knight_L8_Armour');mesh=d['meshes'][node['mesh']];mesh['primitives']=mesh['primitives'][:1]+[hand]
write(dest,d,binary);Path(str(dest)+'.gloves.json').write_text(json.dumps({'source':source,'exactSourcePositionWeightAccessors':True,'triangles':len(indices)//3,'components':components},indent=2));print('EXACT_HAND_COMPONENTS',len(components),len(indices)//3)
