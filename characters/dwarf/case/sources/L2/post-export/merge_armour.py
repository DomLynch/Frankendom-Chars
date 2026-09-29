"""Append Blender-fitted armour while retaining exact source rig/clip/mesh buffers."""
import copy
import json
import struct
from pathlib import Path
import numpy as np
from PIL import Image
import io


def read(path):
    b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0]
    return json.loads(b[20:20+n]),b[28+n:]


def write(path,j,b):
    b=bytes(b)+b'\0'*(-len(b)%4);j['buffers']=[{'byteLength':len(b)}]
    s=json.dumps(j,separators=(',',':')).encode();s+=b' '*(-len(s)%4)
    Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(s)+len(b))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(b),0x004e4942)+b)


def worlds(j):
    def local(n):
        if 'matrix' in n:return np.array(n['matrix']).reshape(4,4).T
        x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
        m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
    parents={c:i for i,n in enumerate(j['nodes']) for c in n.get('children',[])};cache={}
    def visit(i):
        if i not in cache:cache[i]=(visit(parents[i]) if i in parents else np.eye(4))@local(j['nodes'][i])
        return cache[i]
    return {i:visit(i) for i in range(len(j['nodes']))}


def merge(original,addon,dest):
    rank=Path(dest).stem.rsplit('-',1)[-1]
    assert rank in [f'L{i}' for i in range(2,11)],rank
    j,b=read(original);a,ab=read(addon);b=bytearray(b);original_animation=copy.deepcopy(j['animations']);ow=worlds(j);aw=worlds(a)
    names={n.get('name'):i for i,n in enumerate(j['nodes']) if n.get('name')};memo={};errors=[]
    body_node=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='CreatureBody')
    source_skin=j['skins'][j['nodes'][body_node]['skin']];ac=j['accessors'][source_skin['inverseBindMatrices']];bv=j['bufferViews'][ac['bufferView']]
    source_ibm=np.frombuffer(bytes(b),dtype='<f4',offset=bv.get('byteOffset',0)+ac.get('byteOffset',0),count=ac['count']*16).reshape(-1,4,4).transpose(0,2,1)
    source_bind={n:ow[body_node]@np.linalg.inv(m) for n,m in zip(source_skin['joints'],source_ibm)}
    world_ibm={n:m@np.linalg.inv(ow[body_node]) for n,m in zip(source_skin['joints'],source_ibm)}
    def add(kind,index):
        key=(kind,index)
        if key in memo:return memo[key]
        value=copy.deepcopy(a[kind][index])
        if kind=='images':
            av=a['bufferViews'][value['bufferView']];start=av.get('byteOffset',0);payload=ab[start:start+av['byteLength']]
            for old,existing in enumerate(j.get('images',[])):
                if existing.get('mimeType')!=value.get('mimeType') or 'bufferView' not in existing:continue
                bv=j['bufferViews'][existing['bufferView']];lo=bv.get('byteOffset',0)
                if bytes(b[lo:lo+bv['byteLength']])==payload:memo[key]=old;return old
        idx=len(j.setdefault(kind,[]));memo[key]=idx;j[kind].append(value)
        if kind=='bufferViews':
            start=value.get('byteOffset',0);b.extend(b'\0'*(-len(b)%4));value['buffer']=0;value['byteOffset']=len(b);b.extend(ab[start:start+value['byteLength']])
        elif kind=='accessors':
            assert 'sparse' not in value
            value['bufferView']=add('bufferViews',value['bufferView'])
        elif kind=='images':value['bufferView']=add('bufferViews',value['bufferView'])
        elif kind=='textures':
            if 'source' in value:value['source']=add('images',value['source'])
            if 'sampler' in value:value['sampler']=add('samplers',value['sampler'])
            for ext,info in value.get('extensions',{}).items():
                assert ext in ['EXT_texture_webp','KHR_texture_basisu'],ext
                info['source']=add('images',info['source'])
        elif kind=='materials':
            if value.get('name')=='Dwarf oxblood leather gloves':value['pbrMetallicRoughness'].pop('metallicRoughnessTexture',None)
            def textures(obj):
                for k,v in obj.items():
                    if isinstance(v,dict):
                        if k.endswith('Texture') and 'index' in v:v['index']=add('textures',v['index'])
                        else:textures(v)
            textures(value)
            if value.get("name")=="Dwarf oxblood leather gloves":
                value["pbrMetallicRoughness"]["baseColorFactor"]=[.18,.075,.045,1]
                value["pbrMetallicRoughness"]["roughnessFactor"]=.74
                source_material=j["materials"][j["meshes"][j["nodes"][body_node]["mesh"]]["primitives"][0]["material"]]
                value["pbrMetallicRoughness"]["metallicRoughnessTexture"]=copy.deepcopy(source_material["pbrMetallicRoughness"]["metallicRoughnessTexture"])
        elif kind=='meshes':
            for p in value['primitives']:
                p['attributes']={k:add('accessors',v) for k,v in p['attributes'].items()}
                for field,typ in [('indices','accessors'),('material','materials')]:
                    if field in p:p[field]=add(typ,p[field])
                assert not p.get('targets') and not p.get('extensions')
        elif kind=='skins':
            joints=[]
            for old in value['joints']:
                name=a['nodes'][old]['name'];new=names[name];err=float(np.max(np.abs(source_bind[new][:3,3]-aw[old][:3,3])));errors.append(err)
                assert err<2e-5,(name,err)
                joints.append(new)
            ac=a['accessors'][value['inverseBindMatrices']];bv=a['bufferViews'][ac['bufferView']]
            ibm=np.frombuffer(ab,dtype='<f4',offset=bv.get('byteOffset',0)+ac.get('byteOffset',0),count=ac['count']*16).reshape(-1,4,4).transpose(0,2,1)
            # Blender changes bone axes on import. New mesh positions already bind in world space.
            # Require that fact numerically, then bind new vertices directly to ORIGINAL bone axes.
            bind_error=max(float(np.max(np.abs(aw[node]@matrix-np.eye(4)))) for node,matrix in zip(value['joints'],ibm))
            assert bind_error<2e-5,('Addon not world-space bound',bind_error)
            corrected=np.array([world_ibm[node].T for node in joints],dtype='<f4').tobytes()
            b.extend(b'\0'*(-len(b)%4));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(corrected)});b.extend(corrected)
            ai=len(j['accessors']);j['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(joints),'type':'MAT4'})
            value['joints']=joints;value['inverseBindMatrices']=ai;value.pop('skeleton',None)
        return idx
    selected=[]
    for i,n in enumerate(a['nodes']):
        if 'mesh' not in n or not n.get('name','').startswith(rank+'_'):continue
        node={'name':n['name'],'mesh':add('meshes',n['mesh']),'matrix':np.eye(4).T.reshape(-1).tolist()}
        if 'skin' in n:node['skin']=add('skins',n['skin'])
        selected.append(node['name']);j['scenes'][j.get('scene',0)]['nodes'].append(len(j['nodes']));j['nodes'].append(node)
    assert selected,'No fitted armour meshes'
    # Original helmet data remains in the file, but is excluded from the active scene.
    hidden=[i for i,n in enumerate(j['nodes']) if n.get('name') in ['Steel.Helmet','Antique brass.Helmet']]
    for n in j['nodes']:
        if 'children' in n:n['children']=[i for i in n['children'] if i not in hidden]
    for ext in a.get('extensionsUsed',[]):
        if ext not in j.setdefault('extensionsUsed',[]):j['extensionsUsed'].append(ext)
    # Keep original visible face/beard and exposed limb skin. Old embedded kit stays
    # byte-preserved in its original mesh, but is not drawn through the new armour.
    source_bytes=read(original)[1]
    def original_array(index):
        ac=j['accessors'][index];bv=j['bufferViews'][ac['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[ac['componentType']]);width={'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}[ac['type']]
        return np.ndarray((ac['count'],width),dtype=dt,buffer=source_bytes,offset=bv.get('byteOffset',0)+ac.get('byteOffset',0),strides=(bv.get('byteStride',width*dt.itemsize),dt.itemsize))
    visible=copy.deepcopy(j['meshes'][j['nodes'][body_node]['mesh']]);visible['name']='Original Dwarf visible skin';hidden_faces=0;kept_faces=0
    for primitive in visible['primitives']:
        attrs=primitive['attributes'];pos=original_array(attrs['POSITION']);points=(ow[body_node]@np.c_[pos,np.ones(len(pos))].T).T[:,:3];indices=original_array(primitive['indices']).reshape(-1,3);centres=points[indices].mean(1)
        tex=j['textures'][j['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorTexture']['index']];im=j['images'][tex.get('source',tex.get('extensions',{}).get('EXT_texture_webp',{}).get('source'))];bv=j['bufferViews'][im['bufferView']];imdata=Image.open(io.BytesIO(source_bytes[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])).convert('RGB');pixels=np.asarray(imdata)/255;uv=original_array(attrs['TEXCOORD_0'])[indices].mean(1)
        # glTF images use top-left UV origin. Pixel colours only select original exposed skin.
        colors=pixels[np.clip((uv[:,1]*imdata.height).astype(int),0,imdata.height-1),np.clip((uv[:,0]*imdata.width).astype(int),0,imdata.width-1)]
        skin=(colors[:,0]>colors[:,1]*1.075)&(colors[:,1]>colors[:,2]*1.025)
        x=np.abs(centres[:,0]);height=centres[:,1]
        head=(x<.17)&(height>1.025)
        biceps=(x>.18)&(x<.36)&(height>.80)&(height<1.16)&skin
        thighs=(x>.045)&(x<.235)&(height>.37)&(height<.68)&skin
        keep=head|biceps|thighs
        kept_faces+=int(keep.sum());hidden_faces+=int((~keep).sum());payload=np.asarray(indices[keep],dtype='<u4').tobytes();b.extend(b'\0'*(-len(b)%4));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload),'target':34963});b.extend(payload);ai=len(j['accessors']);j['accessors'].append({'bufferView':vi,'componentType':5125,'count':int(keep.sum())*3,'type':'SCALAR'});primitive['indices']=ai
    j['nodes'][body_node]['mesh']=len(j['meshes']);j['meshes'].append(visible)
    tangent_repairs=0
    def vector_accessor(index,width):
        ac=j['accessors'][index];bv=j['bufferViews'][ac['bufferView']]
        return np.ndarray((ac['count'],width),dtype='<f4',buffer=b,offset=bv.get('byteOffset',0)+ac.get('byteOffset',0),strides=(bv.get('byteStride',width*4),4))
    for node in j['nodes']:
        if node.get('name') not in selected:continue
        for primitive in j['meshes'][node['mesh']]['primitives']:
            attrs=primitive['attributes']
            if 'TANGENT' not in attrs:continue
            t=vector_accessor(attrs['TANGENT'],4);normal=vector_accessor(attrs['NORMAL'],3);length=np.linalg.norm(t[:,:3],axis=1)
            for index in np.where(length<1e-8)[0]:
                axis=np.eye(3)[np.argmin(np.abs(normal[index]))];v=np.cross(normal[index],axis);v/=np.linalg.norm(v);t[index,:3]=v;t[index,3]=1;tangent_repairs+=1
            lengths=np.linalg.norm(t[:,:3],axis=1);t[:,:3]/=lengths[:,None]
    assert j['animations']==original_animation
    write(dest,j,b)
    return {'originalBodyFacesVisible':kept_faces,'originalBodyFacesHidden':hidden_faces,'repairedZeroTangents':tangent_repairs,'appended':selected,'maxJointRestPositionError':max(errors),'newArmourReboundToOriginalAxes':True,'originalAnimationsExact':True,'originalBinaryPrefixExact':bytes(b[:len(read(original)[1])])==read(original)[1],'hiddenOriginalHelmetNodes':hidden}

if __name__=='__main__':
    import sys
    print(json.dumps(merge(*sys.argv[1:4]),indent=2))
