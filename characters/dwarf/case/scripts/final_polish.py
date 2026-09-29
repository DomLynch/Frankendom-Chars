"""Final, source-preserving visibility and glove material repairs; apply once to selected candidate."""
from pathlib import Path
import sys,copy,json,io
import numpy as np
from PIL import Image
from merge_armour import read,write,worlds

def polish(path):
 path=Path(path);rank=path.stem.rsplit('-',1)[-1];j,source=read(path);b=bytearray(source)
 def arr(index):
  a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]);c={'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']];return np.ndarray((a['count'],c),dtype=dt,buffer=source,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',c*dt.itemsize),dt.itemsize))
 def idx(faces):
  payload=np.asarray(faces,dtype='<u4').tobytes();b.extend(b'\0'*(-len(b)%4));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload),'target':34963});b.extend(payload);ai=len(j['accessors']);j['accessors'].append({'bufferView':vi,'componentType':5125,'count':int(faces.size),'type':'SCALAR'});return ai
 def pixels(ti):
  t=j['textures'][ti];im=j['images'][t.get('source',t.get('extensions',{}).get('EXT_texture_webp',{}).get('source'))];v=j['bufferViews'][im['bufferView']];lo=v.get('byteOffset',0);return np.asarray(Image.open(io.BytesIO(source[lo:lo+v['byteLength']])).convert('RGB'))/255
 body_id=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='CreatureBody');body=j['nodes'][body_id];p=j['meshes'][body['mesh']]['primitives'][0];f=arr(p['indices']).reshape(-1,3);v=arr(p['attributes']['POSITION']);w=worlds(j)[body_id];world=(w@np.c_[v,np.ones(len(v))].T).T[:,:3];c=world[f].mean(1)
 # Preserve face/beard and neck; exclude old exposed upper-back patches below collar.
 remove=(np.abs(c[:,0])<.18)&(c[:,1]>1.025)&(c[:,1]<1.205)&(c[:,2]<.025)
 p['indices']=idx(f[~remove]);back_removed=int(remove.sum());face_removed=0
 lining=next(n for n in j['nodes'] if n.get('name')==rank+'_Lining');lp=j['meshes'][lining['mesh']]['primitives'][0];lf=arr(lp['indices']).reshape(-1,3);combined=np.unique(np.concatenate([lf,f[remove]]),axis=0);lp['indices']=idx(combined)
 if rank!='L8':
  node=next(n for n in j['nodes'] if n.get('name')==rank+'_Armour')
  for p in j['meshes'][node['mesh']]['primitives']:
   f=arr(p['indices']).reshape(-1,3);v=arr(p['attributes']['POSITION']);c=v[f].mean(1);uv=arr(p['attributes']['TEXCOORD_0'])[f].mean(1);mat=j['materials'][p['material']]['pbrMetallicRoughness'];ti=mat['baseColorTexture']['index']
   raw=next(m['pbrMetallicRoughness'] for m in j['materials'] if m.get('pbrMetallicRoughness',{}).get('baseColorTexture',{}).get('index')==ti and 'metallicRoughnessTexture' in m.get('pbrMetallicRoughness',{}))
   def sample(image):return image[np.clip((uv[:,1]*len(image)).astype(int),0,len(image)-1),np.clip((uv[:,0]*image.shape[1]).astype(int),0,image.shape[1]-1)]
   color=sample(pixels(ti));metal=sample(pixels(raw['metallicRoughnessTexture']['index']))[:,2];red,green,blue=color.T
   skin=(red>green*1.16)&(red<green*1.65)&(green>blue*1.06)&(green<blue*1.55)&(red>.32)&(green>.20)
   remove=(np.abs(c[:,0])<.175)&(c[:,1]>1.16)&(c[:,1]<1.355)&(c[:,2]>.02)&skin&(metal<.12)
   p['indices']=idx(f[~remove]);face_removed+=int(remove.sum())
 if rank=='L9':
  armour=next(n for n in j['nodes'] if n.get('name')==rank+'_Armour')
  for primitive in j['meshes'][armour['mesh']]['primitives']:j['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor']=[.5,1,.6,1]
 if rank in ['L4','L5','L6','L7','L9','L10']:
  node=next(n for n in j['nodes'] if n.get('name')==rank+'_Gloves');p=j['meshes'][node['mesh']]['primitives'][0];material=j['materials'][p['material']]['pbrMetallicRoughness'];material.pop('metallicRoughnessTexture',None)
  if rank=='L9':material['baseColorFactor']=[.025,.16,.055,1]
 write(path,j,b)
 report={'rank':rank,'hiddenOldUpperBackFaces':back_removed,'removedLeakedDonorFaceTriangles':face_removed,'originalBinaryAndClipsPreserved':True,'gloveMetalMapCorrected':rank in ['L4','L5','L6','L7','L9','L10']}
 print(json.dumps(report));return report
if __name__=='__main__':polish(sys.argv[1])
