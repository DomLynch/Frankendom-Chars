"""Isolated Knight L8 pilot. Preserve donor surface and source rig; no game writes."""
from pathlib import Path
import bpy, bmesh, hashlib, json, os, urllib.request
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from huggingface_hub import HfApi, get_token, hf_hub_url
REPO='Domlynch/frankendom-knight-ranks-20260928'
OUT=Path('/tmp/knight-pilot');OUT.mkdir(exist_ok=True)
api=HfApi();revision=api.repo_info(REPO,repo_type='dataset').sha

def download(name):
    path=OUT/name
    req=urllib.request.Request(hf_hub_url(REPO,name,repo_type='dataset',revision=revision),headers={'Authorization':'Bearer '+get_token()})
    with urllib.request.urlopen(req,timeout=90) as f:path.write_bytes(f.read())
    return str(path)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=download('original.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
body=bpy.data.objects['CreatureBody']
original=[o for o in bpy.context.scene.objects if o.type=='MESH']
def signature(obj):
    return hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in obj.data.vertices]).encode()).hexdigest()
before={o.name:signature(o) for o in original}
body.data.calc_loop_triangles()
pts=[body.matrix_world@v.co for v in body.data.vertices]
faces=[tuple(t.vertices) for t in body.data.loop_triangles]
bvh=BVHTree.FromPolygons(pts,faces,all_triangles=True)
existing=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=download('L8-detail-donor.glb'))
donor=next(o for o in bpy.context.scene.objects if o not in existing and o.type=='MESH')
donor.name='Knight_L8_Armour'
dp=[donor.matrix_world@v.co for v in donor.data.vertices]
zmin=min(p.z for p in dp);zmax=max(p.z for p in dp)
# The extra crown ridges belong above the preserved head, not in its body scale.
base_min=min(p.z for p in pts);base_max=max(p.z for p in pts)
scale=(base_max-base_min)/(zmax-zmin)*1.035
for v,p in zip(donor.data.vertices,dp):v.co=Vector((p.x*scale,p.y*scale,(p.z-zmin)*scale+base_min))
donor.matrix_world.identity()
# Measured Knight bind-space targets: shoulder (0.225,1.662), elbow
# (0.256,1.348), wrist (0.286,1.043), in Blender world X/Z.
# Move only the donor arms inward; keep torso, head and skirt surfaces.
arm_vertex=set()
for v in donor.data.vertices:
    x,z=abs(v.co.x),v.co.z
    boundary=0.285 if z>1.48 else 0.345
    if x>boundary and 0.72<z<1.78:
        arm_vertex.add(v.index)
        t=max(0,min(1,(1.68-z)/0.65))
        v.co.x-= (1 if v.co.x>0 else -1)*0.14*t
        v.co.z+=0.04*t
source_groups={g.index:g.name for g in body.vertex_groups}
for name in source_groups.values():donor.vertex_groups.new(name=name)
arm_names=('upperarm_','lowerarm_','hand_','thumb_','index_','middle_','ring_','pinky_')
def arm_fraction(index):
    return sum(g.weight for g in body.data.vertices[index].groups if source_groups[g.group].startswith(arm_names))
arm_faces=[f for f in faces if sum(arm_fraction(i) for i in f)/3>0.5]
body_faces=[f for f in faces if sum(arm_fraction(i) for i in f)/3<0.05]
arm_bvh=BVHTree.FromPolygons(pts,arm_faces,all_triangles=True)
body_bvh=BVHTree.FromPolygons(pts,body_faces,all_triangles=True)
for v in donor.data.vertices:
    is_arm=v.index in arm_vertex
    active_bvh,active_faces=(arm_bvh,arm_faces) if is_arm else (body_bvh,body_faces)
    hit=active_bvh.find_nearest(v.co);ids=active_faces[hit[2]];a,b,c=[pts[i] for i in ids]
    e0,e1,e2=b-a,c-a,hit[0]-a
    d00,d01,d11,d20,d21=e0.dot(e0),e0.dot(e1),e1.dot(e1),e2.dot(e0),e2.dot(e1)
    den=d00*d11-d01*d01
    u=(d11*d20-d01*d21)/den if abs(den)>1e-12 else 0
    w=(d00*d21-d01*d20)/den if abs(den)>1e-12 else 0
    weights={}
    for idx,factor in zip(ids,[max(0,1-u-w),max(0,u),max(0,w)]):
        for g in body.data.vertices[idx].groups:
            name=source_groups[g.group];weights[name]=weights.get(name,0)+g.weight*factor
    # A short connected tasset skirt cannot follow a nearby wrist or
    # switch abruptly between opposite thighs. Use a continuous local field.
    if not is_arm and 0.79<v.co.z<1.24:
        leg=max(0,min(0.45,(1.15-v.co.z)*1.5))
        side=max(0,min(1,(v.co.x+0.07)/0.14));side=side*side*(3-2*side)
        weights={'pelvis':1-leg,'thigh_l':leg*side,'thigh_r':leg*(1-side)}
    weights=sorted(weights.items(),key=lambda x:x[1],reverse=True)[:4];total=sum(w for _,w in weights)
    assert total>0
    for name,w in weights:
        if w>0:donor.vertex_groups[name].add([v.index],w/total,'REPLACE')
mod=donor.modifiers.new('Preserved Knight rig','ARMATURE');mod.object=rig
mw=donor.matrix_world.copy();donor.parent=rig;donor.matrix_world=mw
# Select connected lower-arm regions, preserving the separate skirt component.
eligible={v.index for v in donor.data.vertices if .72<v.co.z<1.13 and abs(v.co.x)>.20}
neighbors={i:set() for i in eligible}
for edge in donor.data.edges:
    a,b=edge.vertices
    if a in eligible and b in eligible:neighbors[a].add(b);neighbors[b].add(a)
# glTF UV seams can duplicate vertices: unify their connectivity for selection.
coincident={}
for i in eligible:coincident.setdefault(tuple(round(x,5) for x in donor.data.vertices[i].co),[]).append(i)
for group in coincident.values():
    for i in group:neighbors[i].update(group)
seen=set();remove_vertices=set();components=[]
for i in eligible:
    if i in seen:continue
    group=set([i]);stack=[i];seen.add(i)
    while stack:
        for j in neighbors[stack.pop()]:
            if j not in seen:seen.add(j);group.add(j);stack.append(j)
    center=sum((donor.data.vertices[j].co for j in group),Vector())/len(group)
    if abs(center.x)>.265 and any(j in arm_vertex for j in group):remove_vertices.update(group);components.append([len(group),list(center)])
bm=bmesh.new();bm.from_mesh(donor.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index in remove_vertices],context='VERTS');bm.to_mesh(donor.data);bm.free()
gloves=body.copy();gloves.data=body.data.copy();gloves.name='Knight_SourceGloves';bpy.context.collection.objects.link(gloves)
def hand_weight(v):
    return sum(g.weight for g in v.groups if source_groups[g.group].startswith(('hand_','thumb_','index_','middle_','ring_','pinky_')))
# Source hands form separate components from skirt patches sharing hand weights.
# Select by both original influence and connected anatomical surface.
base_keep=[]
for f in gloves.data.polygons:
    center=sum((gloves.matrix_world@gloves.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
    base_keep.append(sum(hand_weight(gloves.data.vertices[i]) for i in f.vertices)/len(f.vertices)>.3 and .82<center.z<1.16 and abs(center.x)>.2 and abs(center.y)<.16)
vertex_faces={}
for f in gloves.data.polygons:
    if base_keep[f.index]:
        for i in f.vertices:vertex_faces.setdefault(tuple(round(x,5) for x in gloves.data.vertices[i].co),set()).add(f.index)
adj={f.index:set() for f in gloves.data.polygons if base_keep[f.index]}
for group in vertex_faces.values():
    for i in group:adj[i].update(group)
seen=set();selected=set();hand_components=[]
for i in adj:
    if i in seen:continue
    group={i};stack=[i];seen.add(i)
    while stack:
        for j in adj[stack.pop()]:
            if j not in seen:seen.add(j);group.add(j);stack.append(j)
    verts={i for j in group for i in gloves.data.polygons[j].vertices}
    center=sum((gloves.matrix_world@gloves.data.vertices[i].co for i in verts),Vector())/len(verts)
    if len(group)>100 and center.y<-.015:selected.update(group);hand_components.append([len(group),list(center)])
keep=[f.index in selected for f in gloves.data.polygons]
assert len(hand_components)>=2,hand_components
print('SOURCE_HAND_COMPONENTS',json.dumps(hand_components),flush=True)
bm=bmesh.new();bm.from_mesh(gloves.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep[f.index]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(gloves.data);bm.free()
# Existing weighted gauntlets, preserved at their working position and shape.
bpy.ops.object.select_all(action='DESELECT');donor.select_set(True);gloves.select_set(True);bpy.context.view_layer.objects.active=donor;bpy.ops.object.join()
print('GLOVE_COMPONENT_REPLACEMENT',json.dumps(components),flush=True)
hidden=bpy.data.materials.new('Original retained under candidate armour');hidden.use_nodes=True
hidden.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=0
hidden.surface_render_method='DITHERED';body.data.materials.clear();body.data.materials.append(hidden)
for mat in donor.data.materials:
    for node in mat.node_tree.nodes:
        if node.type=='BSDF_PRINCIPLED':node.inputs['Emission Strength'].default_value=0
assert all(before[o.name]==signature(o) for o in original)
(OUT/'build.json').write_text(json.dumps({'scale':scale,'sourceRevision':revision,'bodyBounds':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],'originalVertexWeightSignatures':before,'retainedOriginalVerticesWeights':True,'visibleSurface':'New donor hides original armour; original rig and maul retained','newTriangles':sum(len(f.vertices)-2 for f in donor.data.polygons),'status':'Pilot awaiting exported-file review'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'knight-L8.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'knight-L8.glb'),export_format='GLB',use_visible=True,export_animations=True,export_tangents=False)
for name in ['knight-L8.glb','knight-L8.blend','build.json']:
    api.upload_file(path_or_fileobj=str(OUT/name),path_in_repo='pilot-v6/'+name,repo_id=REPO,repo_type='dataset')
print('PILOT_SAVED',flush=True)


import types,sys
packing=types.ModuleType("pack_preserved")
sys.modules["pack_preserved"]=packing
exec('"""Rebind fitted new armour into immutable original GLB; preserve original rig bytes."""\nimport copy, hashlib, json, struct, sys\nfrom pathlib import Path\nimport numpy as np\n\ndef read(path):\n    b=Path(path).read_bytes();n=struct.unpack_from(\'<I\',b,12)[0]\n    return json.loads(b[20:20+n]),b[28+n:]\ndef arr(g,b,i):\n    a=g[\'accessors\'][i];v=g[\'bufferViews\'][a[\'bufferView\']]\n    dtype=np.dtype({5126:\'<f4\',5125:\'<u4\',5123:\'<u2\',5121:\'u1\'}[a[\'componentType\']]);w={\'SCALAR\':1,\'VEC2\':2,\'VEC3\':3,\'VEC4\':4,\'MAT4\':16}[a[\'type\']]\n    return np.ndarray((a[\'count\'],w),dtype=dtype,buffer=b,offset=v.get(\'byteOffset\',0)+a.get(\'byteOffset\',0),strides=(v.get(\'byteStride\',w*dtype.itemsize),dtype.itemsize))\ndef worlds(g):\n    parents={c:i for i,n in enumerate(g[\'nodes\']) for c in n.get(\'children\',[])};cache={}\n    def world(i):\n        if i in cache:return cache[i]\n        n=g[\'nodes\'][i]\n        if \'matrix\' in n:m=np.array(n[\'matrix\']).reshape(4,4).T\n        else:\n            x,y,z,w=n.get(\'rotation\',[0,0,0,1]);m=np.eye(4)\n            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get(\'scale\',[1,1,1]));m[:3,3]=n.get(\'translation\',[0,0,0])\n        cache[i]=world(parents[i])@m if i in parents else m;return cache[i]\n    return [world(i) for i in range(len(g[\'nodes\']))]\ndef write(path,g,b):\n    b=bytes(b)+b\'\\0\'*((-len(b))%4);g[\'buffers\']=[{\'byteLength\':len(b)}];j=json.dumps(g,separators=(\',\',\':\')).encode();j+=b\' \'*((-len(j))%4)\n    Path(path).write_bytes(struct.pack(\'<III\',0x46546c67,2,28+len(j)+len(b))+struct.pack(\'<II\',len(j),0x4e4f534a)+j+struct.pack(\'<II\',len(b),0x004e4942)+b)\n\ndef pack(original,fitted,dest):\n    g,b=read(original);d,db=read(fitted);out=copy.deepcopy(g);binary=bytearray(b)\n    og=worlds(g);dg=worlds(d);names={n.get(\'name\'):i for i,n in enumerate(g[\'nodes\']) if n.get(\'name\')}\n    source_node=next((i,n) for i,n in enumerate(d[\'nodes\']) if n.get(\'name\')==\'Knight_L8_Armour\')\n    di,dn=source_node;skin=d[\'skins\'][dn[\'skin\']];delta=0\n    # Blender has baked global scale and its bind-pose correction into exported\n    # mesh coordinates. Rebind only NEW geometry to the immutable source skin.\n    # Copying exported inverse binds or rest transforms would change the rig.\n    for joint in skin[\'joints\']:\n        assert d[\'nodes\'][joint][\'name\'] in names\n    body_i=next(i for i,n in enumerate(g[\'nodes\']) if n.get(\'name\')==\'CreatureBody\')\n    bind_to_source=np.linalg.inv(og[body_i])\n    src_skin=g[\'skins\'][0]\n    original_joint_order={g[\'nodes\'][j][\'name\']:k for k,j in enumerate(src_skin[\'joints\'])}\n    joint_remap=np.array([original_joint_order[d[\'nodes\'][j][\'name\']] for j in skin[\'joints\']],dtype=np.uint16)\n    # New attribute buffers are transformed below; original binary stays exact.\n    maps={key:{} for key in [\'bufferViews\',\'accessors\',\'images\',\'samplers\',\'textures\',\'materials\',\'meshes\']}\n    def add(kind,i):\n        if i in maps[kind]:return maps[kind][i]\n        value=copy.deepcopy(d[kind][i])\n        if kind==\'bufferViews\':\n            off=value.get(\'byteOffset\',0);binary.extend(b\'\\0\'*((-len(binary))%4));value[\'byteOffset\']=len(binary);value[\'buffer\']=0;binary.extend(db[off:off+value[\'byteLength\']])\n        elif kind==\'accessors\':\n            assert \'sparse\' not in value\n            value[\'bufferView\']=add(\'bufferViews\',value[\'bufferView\'])\n        elif kind==\'images\':\n            assert \'bufferView\' in value;value[\'bufferView\']=add(\'bufferViews\',value[\'bufferView\'])\n        elif kind==\'textures\':\n            if \'source\' in value:value[\'source\']=add(\'images\',value[\'source\'])\n            if \'sampler\' in value:value[\'sampler\']=add(\'samplers\',value[\'sampler\'])\n            for ext in value.get(\'extensions\',{}).values():\n                if \'source\' in ext:ext[\'source\']=add(\'images\',ext[\'source\'])\n        elif kind==\'materials\':\n            def textures(node):\n                if isinstance(node,dict):\n                    for k,v in node.items():\n                        if k.endswith(\'Texture\') and isinstance(v,dict) and \'index\' in v:v[\'index\']=add(\'textures\',v[\'index\'])\n                        else:textures(v)\n            textures(value)\n        elif kind==\'meshes\':\n            for p in value[\'primitives\']:\n                p[\'attributes\']={k:add(\'accessors\',v) for k,v in p[\'attributes\'].items()}\n                if \'indices\' in p:p[\'indices\']=add(\'accessors\',p[\'indices\'])\n                if \'material\' in p:p[\'material\']=add(\'materials\',p[\'material\'])\n                assert not p.get(\'targets\');assert not p.get(\'extensions\')\n        out.setdefault(kind,[]);idx=len(out[kind]);out[kind].append(value);maps[kind][i]=idx;return idx\n    mesh_idx=add(\'meshes\',dn[\'mesh\'])\n    for prim in out[\'meshes\'][mesh_idx][\'primitives\']:\n        attrs=prim[\'attributes\']\n        # Copy out before extending the bytearray: numpy views must not alias it.\n        for key in [\'POSITION\',\'NORMAL\',\'JOINTS_0\']:\n            if key not in attrs:continue\n            ai=attrs[key];data=arr(out,binary,ai).copy()\n            if key==\'POSITION\':\n                data=(np.c_[data,np.ones(len(data))]@bind_to_source.T)[:,:3].astype(\'<f4\')\n                out[\'accessors\'][ai][\'min\']=data.min(0).tolist();out[\'accessors\'][ai][\'max\']=data.max(0).tolist()\n            elif key==\'NORMAL\':\n                data=data@np.linalg.inv(bind_to_source[:3,:3]);data/=np.maximum(np.linalg.norm(data,axis=1,keepdims=True),1e-12);data=data.astype(\'<f4\')\n            else:data=joint_remap[data].astype(\'<u2\');out[\'accessors\'][ai][\'componentType\']=5123\n            binary.extend(b\'\\0\'*((-len(binary))%4));vi=len(out[\'bufferViews\']);out[\'bufferViews\'].append({\'buffer\':0,\'byteOffset\':len(binary),\'byteLength\':data.nbytes,\'target\':34962});binary.extend(data.tobytes());out[\'accessors\'][ai][\'bufferView\']=vi;out[\'accessors\'][ai][\'byteOffset\']=0\n    node={\'name\':\'Knight_L8_Armour\',\'mesh\':mesh_idx,\'skin\':0,\'matrix\':og[body_i].T.flatten().tolist()}\n    node_idx=len(out[\'nodes\']);out[\'nodes\'].append(node);out[\'scenes\'][out.get(\'scene\',0)][\'nodes\'].append(node_idx)\n    invisible={\'name\':\'Original armour retained beneath candidate\',\'alphaMode\':\'BLEND\',\'pbrMetallicRoughness\':{\'baseColorFactor\':[1,1,1,0],\'metallicFactor\':0,\'roughnessFactor\':1}}\n    mi=len(out[\'materials\']);out[\'materials\'].append(invisible)\n    body=next(n for n in out[\'nodes\'] if n.get(\'name\')==\'CreatureBody\')\n    for prim in out[\'meshes\'][body[\'mesh\']][\'primitives\']:prim[\'material\']=mi\n    for key in [\'extensionsUsed\',\'extensionsRequired\']:\n        if key in d:out[key]=sorted(set(out.get(key,[]))|set(d[key]))\n    assert out[\'animations\']==g[\'animations\'];assert bytes(binary[:len(b)])==b\n    write(dest,out,binary)\n    receipt={\'originalSha256\':hashlib.sha256(Path(original).read_bytes()).hexdigest(),\'sha256\':hashlib.sha256(Path(dest).read_bytes()).hexdigest(),\'originalBinaryPrefixUnchanged\':True,\'originalAnimationsExact\':True,\'originalNodesExact\':out[\'nodes\'][:len(g[\'nodes\'])]==g[\'nodes\'],\'binding\':\'New geometry transformed into original mesh bind coordinates; original skin reused exactly\',\'clips\':len(g[\'animations\']),\'sourceJoints\':len(src_skin[\'joints\']),\'scope\':\'Original rig, meshes, weapons and animations preserved; original armour transparent under new candidate.\'}\n    Path(str(dest)+\'.preservation.json\').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))\nif __name__==\'__main__\':pack(*sys.argv[1:4])\n',packing.__dict__)
packing.pack("/tmp/knight-pilot/original.glb","/tmp/knight-pilot/knight-L8.glb","/tmp/knight-pilot/packed.glb")
sys.argv=["smooth","/tmp/knight-pilot/packed.glb","/tmp/knight-pilot/knight-L8-v6-final.glb","320"]
exec('"""Smooth demonstrated discontinuities on the NEW armour mesh, preserving original bytes."""\nimport sys,json\nfrom pathlib import Path\nimport numpy as np\nfrom scipy.sparse import coo_matrix,diags\nfrom pack_preserved import read,arr,write\nsrc,dst=sys.argv[1:3];iterations=int(sys.argv[3]) if len(sys.argv)>3 else 80;g,b=read(src);binary=bytearray(b)\nnode=next(n for n in g[\'nodes\'] if n.get(\'name\')==\'Knight_L8_Armour\');prim=g[\'meshes\'][node[\'mesh\']][\'primitives\'][0];attrs=prim[\'attributes\']\np=arr(g,b,attrs[\'POSITION\']);j=arr(g,b,attrs[\'JOINTS_0\']);w=arr(g,b,attrs[\'WEIGHTS_0\']);tri=arr(g,b,prim[\'indices\']).reshape(-1,3)\n_,inv=np.unique(np.round(p,5),axis=0,return_inverse=True);n=inv.max()+1;nb=len(g[\'skins\'][0][\'joints\'])\ndense=np.zeros((len(p),nb),np.float32)\nfor i in range(4):dense[np.arange(len(p)),j[:,i]]+=w[:,i]\nweights=np.zeros((n,nb),np.float32);np.add.at(weights,inv,dense);weights/=np.bincount(inv)[:,None]\nt=inv[tri];edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);edges=np.concatenate([edges,edges[:,::-1]])\na=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(n,n)).tocsr();a.data[:]=1;a=diags(1/np.maximum(np.asarray(a.sum(1)).ravel(),1))@a\nfor _ in range(iterations):weights=0.4*weights+0.6*(a@weights)\nindices=np.argsort(weights,axis=1)[:,-4:];values=np.take_along_axis(weights,indices,axis=1);values/=values.sum(1,keepdims=True)\nfor key,data in [(\'JOINTS_0\',indices[inv].astype(\'<u2\')),(\'WEIGHTS_0\',values[inv].astype(\'<f4\'))]:\n ai=attrs[key];binary.extend(b\'\\0\'*((-len(binary))%4));vi=len(g[\'bufferViews\']);g[\'bufferViews\'].append({\'buffer\':0,\'byteOffset\':len(binary),\'byteLength\':data.nbytes,\'target\':34962});binary.extend(data.tobytes());g[\'accessors\'][ai][\'bufferView\']=vi;g[\'accessors\'][ai][\'byteOffset\']=0;g[\'accessors\'][ai][\'componentType\']=5123 if key==\'JOINTS_0\' else 5126\nwrite(dst,g,binary);print(json.dumps({\'source\':src,\'output\':dst,\'newMeshVertices\':len(p),\'weldedVertices\':int(n),\'iterations\':iterations,\'originalBuffersRetained\':True}))\n', {"__name__":"smoothing"})
api.upload_file(path_or_fileobj="/tmp/knight-pilot/knight-L8-v6-final.glb",path_in_repo="knight-L8-v6-final.glb",repo_id=REPO,repo_type="dataset")
"""Reimport exported GLBs and capture matched CPU studio views."""

import hashlib
import json
import os
import urllib.request
from pathlib import Path

import bpy
from mathutils import Vector
from huggingface_hub import HfApi, get_token, hf_hub_url

REPO = "Domlynch/frankendom-knight-ranks-20260928"
OUT = Path("/tmp/knight-renders")
OUT.mkdir(exist_ok=True)
api = HfApi()
api.upload_file(path_or_fileobj=b"sdk-remote-roundtrip", path_in_repo="sdk-remote-preflight.txt", repo_id=REPO, repo_type="dataset")
req=urllib.request.Request(hf_hub_url(REPO,"sdk-remote-preflight.txt",repo_type="dataset"),headers={"Authorization":"Bearer "+get_token()})
with urllib.request.urlopen(req,timeout=40) as f: assert f.read()==b"sdk-remote-roundtrip"
print("SDK_REMOTE_PERSISTENCE_PASS",flush=True)
revision = api.repo_info(REPO, repo_type="dataset").sha
receipts = []
for label, filename in [("L8", "knight-L8-v6-final.glb")]:
    path = OUT / (label + ".glb")
    url = hf_hub_url(REPO, filename, repo_type="dataset", revision=revision)
    request = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + get_token()}
    )
    path.write_bytes(Path("/tmp/knight-pilot/knight-L8-v6-final.glb").read_bytes())
    sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(path))
    rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    print("MODEL_INVENTORY",json.dumps({o.name:{"bounds":[[min((o.matrix_world@v.co)[i] for v in o.data.vertices),max((o.matrix_world@v.co)[i] for v in o.data.vertices)] for i in range(3)],"groups":[g.name for g in o.vertex_groups]} for o in bpy.context.scene.objects if o.type=="MESH"}),flush=True)
    print("CLIPS",[a.name for a in bpy.data.actions],flush=True)
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8
    scene.render.resolution_x = 375
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new("Neutral studio")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
        0.18,
        0.18,
        0.18,
        1,
    )
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    target = Vector((0, 0, 1.03))
    bpy.ops.object.camera_add(location=(0, -6, 1.1))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.55
    scene.camera = camera
    for xyz, power, size in [
        ((-3, -4, 5), 650, 3),
        ((3, -2, 3), 220, 3),
        ((1, 2, 4), 450, 2),
    ]:
        bpy.ops.object.light_add(type="AREA", location=xyz)
        light = bpy.context.object
        light.data.energy = power
        light.data.size = size
        light.rotation_euler = (
            (target - light.location).to_track_quat("-Z", "Y").to_euler()
        )
    for view, clip, time in [
        ("front", "Armed", 0.35),
        ("back", "Armed", 0.35),
        ("side", "Armed", 0.35),
        ("attack", "Maul_Heavy", 0.45),
        ("guard", "Maul_Guard", 0.4),
        ("kick", "Kick", 0.4),
        ("fight", "Armed", 0.35),
    ]:
        action = bpy.data.actions.get(clip) or bpy.data.actions.get(clip.replace("Maul_", ""))
        assert action, clip
        rig.animation_data.action = action
        if len(action.slots):
            rig.animation_data.action_slot = action.slots[0]
        scene.frame_set(round(time * scene.render.fps))
        camera.location = (6, 0, 1.1) if view == "side" else (0, 6 if view == "back" else -6, 1.1)
        camera.rotation_euler = (
            (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.ortho_scale = 11.2 if view == "fight" else 2.55
        output = OUT / f"{label}-{view}.png"
        scene.render.filepath = str(output)
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
        api.upload_file(
            path_or_fileobj=str(output),
            path_in_repo="pilot-v6-final/renders/" + output.name,
            repo_id=REPO,
            repo_type="dataset",
        )
        receipts.append(
            {
                "model": filename,
                "sha256": sha,
                "image": output.name,
                "clip": clip,
                "frame": scene.frame_current,
                "camera": list(camera.location),
                "orthoScale": camera.data.ortho_scale,
                "viewport": [375, 600],
                "scope": "CPU studio render; not gameplay or physical phone performance",
            }
        )
        print("CAPTURED", output.name, flush=True)
(OUT / "render-receipt.json").write_text(json.dumps(receipts, indent=2))
api.upload_file(
    path_or_fileobj=str(OUT / "render-receipt.json"),
    path_in_repo="pilot-v6-final/render-receipt.json",
    repo_id=REPO,
    repo_type="dataset",
)
print("RENDER_COMPLETE", flush=True)
os._exit(0)

print("BASELINE_COMPLETE",flush=True)
os._exit(0)
