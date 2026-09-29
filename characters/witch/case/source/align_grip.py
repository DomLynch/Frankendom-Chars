import copy,numpy as np,sys
from pack_preserved import read,arr,write
g,b=read(sys.argv[1]);binary=bytearray(b);n=next(n for n in g['nodes'] if n.get('name','').endswith('_Armour'));a=g['meshes'][n['mesh']]['primitives'][0]['attributes'];p=arr(g,b,a['POSITION']).copy();w=arr(g,b,a['WEIGHTS_0']);j=arr(g,b,a['JOINTS_0']);names=[g['nodes'][i]['name'] for i in g['skins'][0]['joints']]
f=(w*np.isin(j,[names.index('hand_l'),names.index('hand_r')])).sum(1);p[:,0]+=np.sign(p[:,0])*.06*f;p[:,2]-=.065*f
ai=a['POSITION'];ac=g['accessors'][ai];binary.extend(b'\0'*((-len(binary))%4));ac['bufferView']=len(g['bufferViews']);ac['byteOffset']=0;ac['min']=p.min(0).tolist();ac['max']=p.max(0).tolist();g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':p.nbytes,'target':34962});binary.extend(p.tobytes());write(sys.argv[2],g,binary)
