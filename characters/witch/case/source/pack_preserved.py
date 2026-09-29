"""Rebind fitted new armour into immutable original GLB; preserve original rig bytes."""
import copy, hashlib, json, struct, sys
from pathlib import Path
import numpy as np

def read(path):
    b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0]
    return json.loads(b[20:20+n]),b[28+n:]
def arr(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
    dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    return np.ndarray((a['count'],w),dtype=dtype,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',w*dtype.itemsize),dtype.itemsize))
def worlds(g):
    parents={c:i for i,n in enumerate(g['nodes']) for c in n.get('children',[])};cache={}
    def world(i):
        if i in cache:return cache[i]
        n=g['nodes'][i]
        if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
        cache[i]=world(parents[i])@m if i in parents else m;return cache[i]
    return [world(i) for i in range(len(g['nodes']))]
def write(path,g,b):
    b=bytes(b)+b'\0'*((-len(b))%4);g['buffers']=[{'byteLength':len(b)}];j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
    Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)

def pack(original,fitted,dest):
    g,b=read(original);d,db=read(fitted);out=copy.deepcopy(g);binary=bytearray(b)
    og=worlds(g);dg=worlds(d);names={n.get('name'):i for i,n in enumerate(g['nodes']) if n.get('name')}
    source_node=next((i,n) for i,n in enumerate(d['nodes']) if n.get('name','').endswith('_Armour'))
    di,dn=source_node;skin=d['skins'][dn['skin']];delta=0
    # Blender has baked global scale and its bind-pose correction into exported
    # mesh coordinates. Rebind only NEW geometry to the immutable source skin.
    # Copying exported inverse binds or rest transforms would change the rig.
    for joint in skin['joints']:
        assert d['nodes'][joint]['name'] in names
    body_i=next(i for i,n in enumerate(g['nodes']) if n.get('name')=='CreatureBody')
    bind_to_source=np.linalg.inv(og[body_i])
    src_skin=g['skins'][0]
    original_joint_order={g['nodes'][j]['name']:k for k,j in enumerate(src_skin['joints'])}
    joint_remap=np.array([original_joint_order[d['nodes'][j]['name']] for j in skin['joints']],dtype=np.uint16)
    # New attribute buffers are transformed below; original binary stays exact.
    maps={key:{} for key in ['bufferViews','accessors','images','samplers','textures','materials','meshes']}
    def add(kind,i):
        if i in maps[kind]:return maps[kind][i]
        value=copy.deepcopy(d[kind][i])
        if kind=='bufferViews':
            off=value.get('byteOffset',0);binary.extend(b'\0'*((-len(binary))%4));value['byteOffset']=len(binary);value['buffer']=0;binary.extend(db[off:off+value['byteLength']])
        elif kind=='accessors':
            assert 'sparse' not in value
            value['bufferView']=add('bufferViews',value['bufferView'])
        elif kind=='images':
            assert 'bufferView' in value;value['bufferView']=add('bufferViews',value['bufferView'])
        elif kind=='textures':
            if 'source' in value:value['source']=add('images',value['source'])
            if 'sampler' in value:value['sampler']=add('samplers',value['sampler'])
            for ext in value.get('extensions',{}).values():
                if 'source' in ext:ext['source']=add('images',ext['source'])
        elif kind=='materials':
            def textures(node):
                if isinstance(node,dict):
                    for k,v in node.items():
                        if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:v['index']=add('textures',v['index'])
                        else:textures(v)
            textures(value)
        elif kind=='meshes':
            for p in value['primitives']:
                p['attributes']={k:add('accessors',v) for k,v in p['attributes'].items()}
                if 'indices' in p:p['indices']=add('accessors',p['indices'])
                if 'material' in p:p['material']=add('materials',p['material'])
                assert not p.get('targets');assert not p.get('extensions')
        out.setdefault(kind,[]);idx=len(out[kind]);out[kind].append(value);maps[kind][i]=idx;return idx
    mesh_idx=add('meshes',dn['mesh'])
    for prim in out['meshes'][mesh_idx]['primitives']:
        attrs=prim['attributes']
        # Copy out before extending the bytearray: numpy views must not alias it.
        for key in ['POSITION','NORMAL','JOINTS_0']:
            if key not in attrs:continue
            ai=attrs[key];data=arr(out,binary,ai).copy()
            if key=='POSITION':
                data=(np.c_[data,np.ones(len(data))]@bind_to_source.T)[:,:3].astype('<f4')
                out['accessors'][ai]['min']=data.min(0).tolist();out['accessors'][ai]['max']=data.max(0).tolist()
            elif key=='NORMAL':
                data=data@np.linalg.inv(bind_to_source[:3,:3]);data/=np.maximum(np.linalg.norm(data,axis=1,keepdims=True),1e-12);data=data.astype('<f4')
            else:data=joint_remap[data].astype('<u2');out['accessors'][ai]['componentType']=5123
            binary.extend(b'\0'*((-len(binary))%4));vi=len(out['bufferViews']);out['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':data.nbytes,'target':34962});binary.extend(data.tobytes());out['accessors'][ai]['bufferView']=vi;out['accessors'][ai]['byteOffset']=0
    node={'name':dn['name'],'mesh':mesh_idx,'skin':0,'matrix':og[body_i].T.flatten().tolist()}
    node_idx=len(out['nodes']);out['nodes'].append(node);out['scenes'][out.get('scene',0)]['nodes'].append(node_idx)
    invisible={'name':'Original armour retained beneath candidate','alphaMode':'BLEND','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,0],'metallicFactor':0,'roughnessFactor':1}}
    mi=len(out['materials']);out['materials'].append(invisible)
    body=next(n for n in out['nodes'] if n.get('name')=='CreatureBody')
    for prim in out['meshes'][body['mesh']]['primitives']:prim['material']=mi
    for key in ['extensionsUsed','extensionsRequired']:
        if key in d:out[key]=sorted(set(out.get(key,[]))|set(d[key]))
    assert out['animations']==g['animations'];assert bytes(binary[:len(b)])==b
    write(dest,out,binary)
    receipt={'originalSha256':hashlib.sha256(Path(original).read_bytes()).hexdigest(),'sha256':hashlib.sha256(Path(dest).read_bytes()).hexdigest(),'originalBinaryPrefixUnchanged':True,'originalAnimationsExact':True,'originalNodesExact':out['nodes'][:len(g['nodes'])]==g['nodes'],'binding':'New geometry transformed into original mesh bind coordinates; original skin reused exactly','clips':len(g['animations']),'sourceJoints':len(src_skin['joints']),'scope':'Original rig, meshes, weapons and animations preserved; original armour transparent under new candidate.'}
    Path(str(dest)+'.preservation.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
if __name__=='__main__':pack(*sys.argv[1:4])
