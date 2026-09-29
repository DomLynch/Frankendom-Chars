"""Hide demonstrably dark old-kit fragments in exposed limb regions; keep face and original buffers."""
from pathlib import Path
import sys,json,io
import numpy as np
from PIL import Image
from merge_armour import read,write,worlds
from check_motion import arr

def clean(path):
 path=Path(path);rank=path.stem.rsplit('-',1)[-1];j,data=read(path);b=bytearray(data)
 def indices(faces):
  raw=np.asarray(faces,dtype='<u4').tobytes();b.extend(b'\0'*(-len(b)%4));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(raw),'target':34963});b.extend(raw);ai=len(j['accessors']);j['accessors'].append({'bufferView':vi,'componentType':5125,'count':faces.size,'type':'SCALAR'});return ai
 ni=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='CreatureBody');n=j['nodes'][ni];p=j['meshes'][n['mesh']]['primitives'][0];f=arr(j,data,p['indices']).reshape(-1,3).astype(int);v=arr(j,data,p['attributes']['POSITION']);w=worlds(j)[ni];c=((w@np.c_[v,np.ones(len(v))].T).T[:,:3])[f].mean(1);uv=arr(j,data,p['attributes']['TEXCOORD_0'])[f].mean(1);t=j['textures'][j['materials'][p['material']]['pbrMetallicRoughness']['baseColorTexture']['index']];image=j['images'][t.get('source',t.get('extensions',{}).get('EXT_texture_webp',{}).get('source'))];bv=j['bufferViews'][image['bufferView']];offset=bv.get('byteOffset',0);pixels=np.asarray(Image.open(io.BytesIO(data[offset:offset+bv['byteLength']])).convert('RGB'))/255;color=pixels[np.clip((uv[:,1]*len(pixels)).astype(int),0,len(pixels)-1),np.clip((uv[:,0]*pixels.shape[1]).astype(int),0,pixels.shape[1]-1)]
 ax=np.abs(c[:,0]);y=c[:,1];limb=((ax>.18)&(ax<.36)&(y>.80)&(y<1.16))|((ax>.045)&(ax<.235)&(y>.37)&(y<.68));dark=(color[:,0]<.25)|(color[:,1]<.17);remove=limb&dark;p['indices']=indices(f[~remove]);head_count=0
 if rank=='L2':
  n=next(n for n in j['nodes'] if n.get('name')=='L2_Armour')
  for p in j['meshes'][n['mesh']]['primitives']:
   f=arr(j,data,p['indices']).reshape(-1,3).astype(int);v=arr(j,data,p['attributes']['POSITION']);c=v[f].mean(1);cut=(np.abs(c[:,0])<.17)&(c[:,1]>1.16)&(c[:,1]<1.36)&(c[:,2]>.02);head_count+=int(cut.sum());p['indices']=indices(f[~cut])
 write(path,j,b);print(json.dumps({'rank':rank,'hiddenDarkOldKitTriangles':int(remove.sum()),'L2FaceClearanceTriangles':head_count}))
if __name__=='__main__':clean(sys.argv[1])
