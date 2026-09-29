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
    path=OUT/Path(name).name
    req=urllib.request.Request(hf_hub_url(REPO,name,repo_type='dataset',revision=revision),headers={'Authorization':'Bearer '+get_token()})
    with urllib.request.urlopen(req,timeout=90) as f:path.write_bytes(f.read())
    return str(path)


import types,sys
packing=types.ModuleType("pack_preserved");sys.modules["pack_preserved"]=packing
exec('"""Rebind fitted new armour into immutable original GLB; preserve original rig bytes."""\nimport copy, hashlib, json, struct, sys\nfrom pathlib import Path\nimport numpy as np\n\ndef read(path):\n    b=Path(path).read_bytes();n=struct.unpack_from(\'<I\',b,12)[0]\n    return json.loads(b[20:20+n]),b[28+n:]\ndef arr(g,b,i):\n    a=g[\'accessors\'][i];v=g[\'bufferViews\'][a[\'bufferView\']]\n    dtype=np.dtype({5126:\'<f4\',5125:\'<u4\',5123:\'<u2\',5121:\'u1\'}[a[\'componentType\']]);w={\'SCALAR\':1,\'VEC2\':2,\'VEC3\':3,\'VEC4\':4,\'MAT4\':16}[a[\'type\']]\n    return np.ndarray((a[\'count\'],w),dtype=dtype,buffer=b,offset=v.get(\'byteOffset\',0)+a.get(\'byteOffset\',0),strides=(v.get(\'byteStride\',w*dtype.itemsize),dtype.itemsize))\ndef worlds(g):\n    parents={c:i for i,n in enumerate(g[\'nodes\']) for c in n.get(\'children\',[])};cache={}\n    def world(i):\n        if i in cache:return cache[i]\n        n=g[\'nodes\'][i]\n        if \'matrix\' in n:m=np.array(n[\'matrix\']).reshape(4,4).T\n        else:\n            x,y,z,w=n.get(\'rotation\',[0,0,0,1]);m=np.eye(4)\n            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get(\'scale\',[1,1,1]));m[:3,3]=n.get(\'translation\',[0,0,0])\n        cache[i]=world(parents[i])@m if i in parents else m;return cache[i]\n    return [world(i) for i in range(len(g[\'nodes\']))]\ndef write(path,g,b):\n    b=bytes(b)+b\'\\0\'*((-len(b))%4);g[\'buffers\']=[{\'byteLength\':len(b)}];j=json.dumps(g,separators=(\',\',\':\')).encode();j+=b\' \'*((-len(j))%4)\n    Path(path).write_bytes(struct.pack(\'<III\',0x46546c67,2,28+len(j)+len(b))+struct.pack(\'<II\',len(j),0x4e4f534a)+j+struct.pack(\'<II\',len(b),0x004e4942)+b)\n\ndef pack(original,fitted,dest):\n    g,b=read(original);d,db=read(fitted);out=copy.deepcopy(g);binary=bytearray(b)\n    og=worlds(g);dg=worlds(d);names={n.get(\'name\'):i for i,n in enumerate(g[\'nodes\']) if n.get(\'name\')}\n    source_node=next((i,n) for i,n in enumerate(d[\'nodes\']) if n.get(\'name\')==\'Knight_L8_Armour\')\n    di,dn=source_node;skin=d[\'skins\'][dn[\'skin\']];delta=0\n    # Blender has baked global scale and its bind-pose correction into exported\n    # mesh coordinates. Rebind only NEW geometry to the immutable source skin.\n    # Copying exported inverse binds or rest transforms would change the rig.\n    for joint in skin[\'joints\']:\n        assert d[\'nodes\'][joint][\'name\'] in names\n    body_i=next(i for i,n in enumerate(g[\'nodes\']) if n.get(\'name\')==\'CreatureBody\')\n    bind_to_source=np.linalg.inv(og[body_i])\n    src_skin=g[\'skins\'][0]\n    original_joint_order={g[\'nodes\'][j][\'name\']:k for k,j in enumerate(src_skin[\'joints\'])}\n    joint_remap=np.array([original_joint_order[d[\'nodes\'][j][\'name\']] for j in skin[\'joints\']],dtype=np.uint16)\n    # New attribute buffers are transformed below; original binary stays exact.\n    maps={key:{} for key in [\'bufferViews\',\'accessors\',\'images\',\'samplers\',\'textures\',\'materials\',\'meshes\']}\n    def add(kind,i):\n        if i in maps[kind]:return maps[kind][i]\n        value=copy.deepcopy(d[kind][i])\n        if kind==\'bufferViews\':\n            off=value.get(\'byteOffset\',0);binary.extend(b\'\\0\'*((-len(binary))%4));value[\'byteOffset\']=len(binary);value[\'buffer\']=0;binary.extend(db[off:off+value[\'byteLength\']])\n        elif kind==\'accessors\':\n            assert \'sparse\' not in value\n            value[\'bufferView\']=add(\'bufferViews\',value[\'bufferView\'])\n        elif kind==\'images\':\n            assert \'bufferView\' in value;value[\'bufferView\']=add(\'bufferViews\',value[\'bufferView\'])\n        elif kind==\'textures\':\n            if \'source\' in value:value[\'source\']=add(\'images\',value[\'source\'])\n            if \'sampler\' in value:value[\'sampler\']=add(\'samplers\',value[\'sampler\'])\n            for ext in value.get(\'extensions\',{}).values():\n                if \'source\' in ext:ext[\'source\']=add(\'images\',ext[\'source\'])\n        elif kind==\'materials\':\n            def textures(node):\n                if isinstance(node,dict):\n                    for k,v in node.items():\n                        if k.endswith(\'Texture\') and isinstance(v,dict) and \'index\' in v:v[\'index\']=add(\'textures\',v[\'index\'])\n                        else:textures(v)\n            textures(value)\n        elif kind==\'meshes\':\n            for p in value[\'primitives\']:\n                p[\'attributes\']={k:add(\'accessors\',v) for k,v in p[\'attributes\'].items()}\n                if \'indices\' in p:p[\'indices\']=add(\'accessors\',p[\'indices\'])\n                if \'material\' in p:p[\'material\']=add(\'materials\',p[\'material\'])\n                assert not p.get(\'targets\');assert not p.get(\'extensions\')\n        out.setdefault(kind,[]);idx=len(out[kind]);out[kind].append(value);maps[kind][i]=idx;return idx\n    mesh_idx=add(\'meshes\',dn[\'mesh\'])\n    for prim in out[\'meshes\'][mesh_idx][\'primitives\']:\n        attrs=prim[\'attributes\']\n        # Copy out before extending the bytearray: numpy views must not alias it.\n        for key in [\'POSITION\',\'NORMAL\',\'JOINTS_0\']:\n            if key not in attrs:continue\n            ai=attrs[key];data=arr(out,binary,ai).copy()\n            if key==\'POSITION\':\n                data=(np.c_[data,np.ones(len(data))]@bind_to_source.T)[:,:3].astype(\'<f4\')\n                out[\'accessors\'][ai][\'min\']=data.min(0).tolist();out[\'accessors\'][ai][\'max\']=data.max(0).tolist()\n            elif key==\'NORMAL\':\n                data=data@np.linalg.inv(bind_to_source[:3,:3]);data/=np.maximum(np.linalg.norm(data,axis=1,keepdims=True),1e-12);data=data.astype(\'<f4\')\n            else:data=joint_remap[data].astype(\'<u2\');out[\'accessors\'][ai][\'componentType\']=5123\n            binary.extend(b\'\\0\'*((-len(binary))%4));vi=len(out[\'bufferViews\']);out[\'bufferViews\'].append({\'buffer\':0,\'byteOffset\':len(binary),\'byteLength\':data.nbytes,\'target\':34962});binary.extend(data.tobytes());out[\'accessors\'][ai][\'bufferView\']=vi;out[\'accessors\'][ai][\'byteOffset\']=0\n    node={\'name\':\'Knight_L8_Armour\',\'mesh\':mesh_idx,\'skin\':0,\'matrix\':og[body_i].T.flatten().tolist()}\n    node_idx=len(out[\'nodes\']);out[\'nodes\'].append(node);out[\'scenes\'][out.get(\'scene\',0)][\'nodes\'].append(node_idx)\n    invisible={\'name\':\'Original armour retained beneath candidate\',\'alphaMode\':\'BLEND\',\'pbrMetallicRoughness\':{\'baseColorFactor\':[1,1,1,0],\'metallicFactor\':0,\'roughnessFactor\':1}}\n    mi=len(out[\'materials\']);out[\'materials\'].append(invisible)\n    body=next(n for n in out[\'nodes\'] if n.get(\'name\')==\'CreatureBody\')\n    for prim in out[\'meshes\'][body[\'mesh\']][\'primitives\']:prim[\'material\']=mi\n    for key in [\'extensionsUsed\',\'extensionsRequired\']:\n        if key in d:out[key]=sorted(set(out.get(key,[]))|set(d[key]))\n    assert out[\'animations\']==g[\'animations\'];assert bytes(binary[:len(b)])==b\n    write(dest,out,binary)\n    receipt={\'originalSha256\':hashlib.sha256(Path(original).read_bytes()).hexdigest(),\'sha256\':hashlib.sha256(Path(dest).read_bytes()).hexdigest(),\'originalBinaryPrefixUnchanged\':True,\'originalAnimationsExact\':True,\'originalNodesExact\':out[\'nodes\'][:len(g[\'nodes\'])]==g[\'nodes\'],\'binding\':\'New geometry transformed into original mesh bind coordinates; original skin reused exactly\',\'clips\':len(g[\'animations\']),\'sourceJoints\':len(src_skin[\'joints\']),\'scope\':\'Original rig, meshes, weapons and animations preserved; original armour transparent under new candidate.\'}\n    Path(str(dest)+\'.preservation.json\').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))\nif __name__==\'__main__\':pack(*sys.argv[1:4])\n',packing.__dict__)
path=Path(download("ladder/L2/knight-L2-final.glb"))
d,db=packing.read(path)
node=next(n for n in d["nodes"] if n.get("name")=="Knight_L2_Armour")
mat=d["materials"][d["meshes"][node["mesh"]]["primitives"][0]["material"]]
mat["pbrMetallicRoughness"]["baseColorFactor"]=[.9,.58,.28,1]
mat["pbrMetallicRoughness"]["roughnessFactor"]=1
packing.write(path,d,db)
PREFIX="ladder/L2-warm";label="L2";filename=path.name;receipts=[]
api.upload_file(path_or_fileobj=str(path),path_in_repo=PREFIX+"/"+filename,repo_id=REPO,repo_type="dataset")
sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(path))
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
for track in rig.animation_data.nla_tracks:
    track.mute = True
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.cycles.transparent_max_bounces = 64
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
    camera.data.ortho_scale = 2.55
    bpy.context.view_layer.update()
    projected_height = None
    if view == "fight":
        import numpy as np
        from bpy_extras.object_utils import world_to_camera_view
        armour=bpy.data.objects["Knight_L2_Armour"]
        evaluated=armour.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=evaluated.to_mesh()
        coords=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',coords)
        coords=coords.reshape(-1,3)
        transform=np.array(camera.matrix_world.inverted() @ evaluated.matrix_world)
        projected=np.c_[coords,np.ones(len(coords))] @ transform.T
        height=float(np.ptp(projected[:,1]));evaluated.to_mesh_clear()
        camera.data.ortho_scale=height*600/110
        bpy.context.view_layer.update()
        # Blender fits the orthographic scale to the longer portrait dimension.
        low=world_to_camera_view(scene,camera,camera.matrix_world @ Vector((0,float(projected[:,1].min()),-6)))
        high=world_to_camera_view(scene,camera,camera.matrix_world @ Vector((0,float(projected[:,1].max()),-6)))
        projected_height=abs(high.y-low.y)*600
        assert abs(projected_height-110)<.01,projected_height
    output = OUT / f"{label}-{view}.png"
    scene.render.filepath = str(output)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    api.upload_file(
        path_or_fileobj=str(output),
        path_in_repo=PREFIX + "/" + output.name,
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
            "projectedArmourHeightPx": projected_height,
            "imageSha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "scope": "CPU studio render; not gameplay or physical phone performance",
        }
    )
    print("CAPTURED", output.name, flush=True)

(OUT/'render-receipt.json').write_text(json.dumps(receipts,indent=2))
api.upload_file(path_or_fileobj=str(OUT/'render-receipt.json'),path_in_repo=PREFIX+'/render-receipt.json',repo_id=REPO,repo_type='dataset')
print('RANK_COMPLETE',label,flush=True)

import os
os._exit(0)
