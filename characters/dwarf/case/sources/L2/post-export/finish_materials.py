"""Material-specific finish and weighted leather lining, using saved geometry/textures."""
from pathlib import Path
import sys,json,copy,io
import numpy as np
from PIL import Image
from merge_armour import read,write,worlds

def finish(path):
    path=Path(path);rank=path.stem.rsplit('-',1)[-1];j,original=read(path);b=bytearray(original)
    def arr(index):
        a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]);c={'VEC3':3,'VEC4':4,'VEC2':2,'SCALAR':1}[a['type']];return np.ndarray((a['count'],c),dtype=dt,buffer=original,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',c*dt.itemsize),dt.itemsize))
    def texture(index):
        t=j['textures'][index];image=j['images'][t.get('source',t.get('extensions',{}).get('EXT_texture_webp',{}).get('source'))];v=j['bufferViews'][image['bufferView']];lo=v.get('byteOffset',0);return np.asarray(Image.open(io.BytesIO(original[lo:lo+v['byteLength']])).convert('RGB'))/255
    def indices(values):
        payload=np.asarray(values,dtype='<u4').tobytes();b.extend(b'\0'*(-len(b)%4));v=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload),'target':34963});b.extend(payload);a=len(j['accessors']);j['accessors'].append({'bufferView':v,'componentType':5125,'count':len(values)*3,'type':'SCALAR'});return a
    armour=next(n for n in j['nodes'] if n.get('name')==rank+'_Armour');mesh=j['meshes'][armour['mesh']];assert len(mesh['primitives'])==1,'Apply finish once after a fresh merge/weight repair'
    prim=mesh['primitives'][0];mat=j['materials'][prim['material']];faces=arr(prim['indices']).reshape(-1,3);uv=arr(prim['attributes']['TEXCOORD_0'])[faces].mean(1)
    def sample(pixels):return pixels[np.clip((uv[:,1]*len(pixels)).astype(int),0,len(pixels)-1),np.clip((uv[:,0]*pixels.shape[1]).astype(int),0,pixels.shape[1]-1)]
    color=sample(texture(mat['pbrMetallicRoughness']['baseColorTexture']['index']));orm=sample(texture(mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']));red,green,blue=color.T;gem=np.zeros(len(red),dtype=bool);metal=(orm[:,2]>.45)&~gem;leather=~metal&~gem
    mesh['primitives']=[];counts={}
    for name,mask,metalness,roughness in [('Rank armour finish',metal,0,0.85),('Leather and exposed surface',leather,0,.82),('Emerald inset',gem,.08,.22)]:
        if not mask.any():continue
        material=copy.deepcopy(mat);material['name']=rank+' '+name;pbr=material['pbrMetallicRoughness'];pbr.pop('metallicRoughnessTexture',None);pbr['metallicFactor']=metalness;pbr['roughnessFactor']=roughness;material['emissiveFactor']=[0,0,0];pbr['baseColorFactor']=[.40,.40,.40,1] if name=='Blackened forged steel' else [1,.50,.22,1];mi=len(j['materials']);j['materials'].append(material);p=copy.deepcopy(prim);p['material']=mi;p['indices']=indices(faces[mask]);mesh['primitives'].append(p);counts[name]=int(mask.sum())
    # Duplicate only the covered source torso triangles for a continuous leather underlayer.
    source_mesh=next(m for m in j['meshes'] if m.get('name')=='geometry_0');source_prim=source_mesh['primitives'][0]
    body_index=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='CreatureBody');body=j['nodes'][body_index];visible=j['meshes'][body['mesh']]['primitives'][0];f=arr(source_prim['indices']).reshape(-1,3);v=arr(source_prim['attributes']['POSITION']);world=worlds(j)[body_index];points=(world@np.c_[v,np.ones(len(v))].T).T[:,:3];c=points[f].mean(1)
    visible_faces={tuple(face) for face in arr(visible['indices']).reshape(-1,3)};covered=np.array([tuple(face) not in visible_faces for face in f]);mask=covered&(c[:,1]>.66)&(c[:,1]<1.18)&(np.abs(c[:,0])<.20)
    # The copied lining gets its own smooth torso weights; original source weights stay untouched.
    joint_names=[j['nodes'][i]['name'] for i in j['skins'][body['skin']]['joints']];levels=np.array([.77,.91,1.04,1.16]);height=points[:,1];weights=np.zeros((len(v),4),dtype='<f4');joint_ids=np.tile(np.array([joint_names.index(n) for n in ['pelvis','spine_01','spine_02','spine_03']],dtype='<u2'),(len(v),1))
    for vi,h in enumerate(height):
        upper=int(np.clip(np.searchsorted(levels,h),1,3));lower=upper-1;t=float(np.clip((h-levels[lower])/(levels[upper]-levels[lower]),0,1));t=t*t*(3-2*t);weights[vi,lower]=1-t;weights[vi,upper]=t
    joint_ids[weights==0]=0
    def vertex_accessor(values,component):
        payload=values.tobytes();b.extend(b'\0'*(-len(b)%4));view=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload),'target':34962});b.extend(payload);accessor=len(j['accessors']);j['accessors'].append({'bufferView':view,'componentType':component,'count':len(values),'type':'VEC'+str(values.shape[1]),**({'min':values.min(0).tolist(),'max':values.max(0).tolist()} if values.shape[1]==3 else {})});return accessor
    lining_attributes=copy.deepcopy(source_prim['attributes']);lining_points=points.copy();lining_points[:,0]*=.78;lining_points[:,2]*=.72;lining_local=(np.linalg.inv(world)@np.c_[lining_points,np.ones(len(v))].T).T[:,:3].astype('<f4');lining_attributes['POSITION']=vertex_accessor(lining_local,5126);lining_attributes['JOINTS_0']=vertex_accessor(joint_ids,5123);lining_attributes['WEIGHTS_0']=vertex_accessor(weights,5126)
    lining=copy.deepcopy(j['materials'][source_prim['material']]);lining['name']=rank+' textured leather under-armour';lining['pbrMetallicRoughness']['baseColorFactor']=[.10,.055,.03,1];lining['pbrMetallicRoughness']['metallicFactor']=0;lining['pbrMetallicRoughness']['roughnessFactor']=1;mi=len(j['materials']);j['materials'].append(lining);lp=copy.deepcopy(source_prim);lp['attributes']=lining_attributes;lp['material']=mi;lp['indices']=indices(f[mask]);mesh_id=len(j['meshes']);j['meshes'].append({'name':rank+'_Lining','primitives':[lp]});j['scenes'][j.get('scene',0)]['nodes'].append(len(j['nodes']));j['nodes'].append({'name':rank+'_Lining','mesh':mesh_id,'skin':body['skin']})
    write(path,j,b);print(json.dumps({'materialTriangles':counts,'liningTriangles':int(mask.sum()),'sourceGeometryAndWeightsUnchanged':True}))
if __name__=='__main__':finish(sys.argv[1])
