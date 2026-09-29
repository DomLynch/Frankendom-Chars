"""Dwarf-specific L8 fit; preserve donor texture and original rig/face/hands."""
from pathlib import Path
import json,hashlib,os,sys,urllib.request
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from huggingface_hub import HfApi,get_token,hf_hub_url

REPO='Domlynch/frankendom-dwarf-ranks-20260928'
R=Path('/tmp/dwarf-fit');R.mkdir(exist_ok=True)
api=HfApi();revision=api.repo_info(REPO,repo_type='dataset').sha

def download(name):
    path=R/name
    req=urllib.request.Request(hf_hub_url(REPO,name,repo_type='dataset',revision=revision),headers={'Authorization':'Bearer '+get_token()})
    with urllib.request.urlopen(req,timeout=90) as response:path.write_bytes(response.read())
    return path

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(download('original.glb')))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
for t in rig.animation_data.nla_tracks:t.mute=True
rig.animation_data.action=None
original=[o for o in bpy.context.scene.objects if o.type=='MESH'];body=bpy.data.objects['CreatureBody']
def signature(o):
    return hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices]).encode()).hexdigest()
before={o.name:signature(o) for o in original}
body.data.calc_loop_triangles();points=[body.matrix_world@v.co for v in body.data.vertices];faces=[tuple(f.vertices) for f in body.data.loop_triangles];bvh=BVHTree.FromPolygons(points,faces,all_triangles=True)
groups={g.index:g.name for g in body.vertex_groups}
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(download('L8-detail-donor.glb')));raw=next(o for o in bpy.context.scene.objects if o not in existing and o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT');raw.select_set(True);bpy.context.view_layer.objects.active=raw;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
lo=min(v.co.z for v in raw.data.vertices)
for v in raw.data.vertices:v.co=Vector((v.co.x*1.32,v.co.y*1.44,(v.co.z-lo)*1.44+.025))
raw.name='L8_Armour'
for v in raw.data.vertices:
    if abs(v.co.x)<.23 and v.co.z>1.24:
        t=float(np.clip((v.co.z-1.24)/.085,0,1));v.co.z+=.035*t*t*(3-2*t)
material=raw.data.materials[0];shader=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');image=shader.inputs['Base Color'].links[0].from_node.image
pixels=np.asarray(image.pixels[:]).reshape(image.size[1],image.size[0],4);uv=raw.data.uv_layers.active.data
remove=[]
for f in raw.data.polygons:
    c=sum((raw.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
    uvp=sum((uv[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
    color=pixels[min(image.size[1]-1,max(0,int(uvp.y*image.size[1]))),min(image.size[0]-1,max(0,int(uvp.x*image.size[0])))][:3]
    red,green,blue=color
    skin=red>green*1.16 and red<green*1.65 and green>blue*1.06 and green<blue*1.55 and red>.32 and green>.20
    # Only remove demonstrated skin regions, not brown armour over the torso.
    head_window=abs(c.x)<.155 and c.z>1.025 and c.z<1.31 and c.y<-.055
    head_skin=abs(c.x)<.175 and c.z>1.16 and skin
    hand=abs(c.x)>.365 and c.z<.77
    bare_arm=abs(c.x)>.245 and .825<c.z<1.07 and skin
    rear_hair=abs(c.x)<.13 and c.y>.015 and 1.16<c.z<1.315
    if head_window or head_skin or rear_hair or hand or bare_arm:remove.append(f.index)
bm=bmesh.new();bm.from_mesh(raw.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(raw.data);bm.free()

def weights(co):
    hit=bvh.find_nearest(co);ids=faces[hit[2]];a,b,c=[points[i] for i in ids];e0=b-a;e1=c-a;e2=hit[0]-a
    d00=e0.dot(e0);d01=e0.dot(e1);d11=e1.dot(e1);d20=e2.dot(e0);d21=e2.dot(e1);den=d00*d11-d01*d01
    u=(d11*d20-d01*d21)/den if abs(den)>1e-12 else 0;v=(d00*d21-d01*d20)/den if abs(den)>1e-12 else 0
    ws={}
    for idx,f in zip(ids,[max(0,1-u-v),max(0,u),max(0,v)]):
        for g in body.data.vertices[idx].groups:ws[groups[g.group]]=ws.get(groups[g.group],0)+g.weight*f
    # Continuous head blend does not sever collar weights at a slot boundary.
    t=np.clip((co.z-1.18)/.14,0,1)*np.clip((.23-abs(co.x))/.05,0,1);t=float(t*t*(3-2*t))
    ws={n:w*(1-t) for n,w in ws.items()};ws['Head']=ws.get('Head',0)+t
    # Preserve continuous tassets at centre: upper skirt follows pelvis, transition to each thigh at lower hem.
    if .50<co.z<.76 and abs(co.x)<.235:
        t=float(np.clip((co.z-.50)/.16,0,1));t=t*t*(3-2*t)
        ws={n:w*(1-t) for n,w in ws.items()};ws['pelvis']=ws.get('pelvis',0)+t
    ws=dict(sorted(ws.items(),key=lambda q:q[1],reverse=True)[:4]);total=sum(ws.values());assert total>0
    return {n:w/total for n,w in ws.items() if w>0}

for v in raw.data.vertices:
    for name,w in weights(v.co).items():(raw.vertex_groups.get(name) or raw.vertex_groups.new(name=name)).add([v.index],w,'REPLACE')
mod=raw.modifiers.new('Original Dwarf armature','ARMATURE');mod.object=rig;mw=raw.matrix_world.copy();raw.parent=rig;raw.matrix_world=mw
shader.inputs['Emission Strength'].default_value=0
# Glove coverage is derived from the actual hands; original finger weights and contact remain.
glove=body.copy();glove.data=body.data.copy();glove.name='L8_Gloves';bpy.context.collection.objects.link(glove)
handgroups={g.index for g in glove.vertex_groups if any(x in g.name for x in ['hand_','thumb_','index_','middle_','pinky_','ring_'])}
keep=[]
for f in glove.data.polygons:
    influence=sum(sum(g.weight for g in glove.data.vertices[i].groups if g.group in handgroups) for i in f.vertices)/len(f.vertices)
    centre=sum((glove.matrix_world@glove.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
    keep.append(influence>.72 or (abs(centre.x)>.337 and centre.z<.80))
bm=bmesh.new();bm.from_mesh(glove.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep[f.index]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(glove.data);bm.free()
for v in glove.data.vertices:v.co+=v.normal*.0025
leather=glove.data.materials[0].copy();leather.name='Dwarf oxblood leather gloves';bs=next(n for n in leather.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
# Use original textured colour detail, confined to new glove shells.
for link in list(bs.inputs['Metallic'].links):leather.node_tree.links.remove(link)
bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.74
if bs.inputs['Base Color'].links:
    src=bs.inputs['Base Color'].links[0].from_socket;mix=leather.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.18,.075,.045,1);leather.node_tree.links.new(src,mix.inputs[1]);leather.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
glove.data.materials.clear();glove.data.materials.append(leather)
assert all(signature(o)==before[o.name] for o in original)
# Save editable source before export; assembly merge preserves exact original animations.
bpy.ops.wm.save_as_mainfile(filepath=str(R/'L8-fit.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,raw,glove]:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'L8-addon.glb'),export_format='GLB',use_selection=True,export_animations=False,export_tangents=True)
report={'originalSignatures':before,'originalVerticesWeightsUnchanged':True,'donorDeletedFaces':len(remove),'newTriangles':sum(len(f.vertices)-2 for o in [raw,glove] for f in o.data.polygons),'scale':[1.32,1.44,1.44],'scope':'unaccepted first fit; original visible face/hands; donor wardrobe replaces visible clothed surfaces'}
(R/'fit-report.json').write_text(json.dumps(report,indent=2))
for f in ['L8-fit.blend','L8-addon.glb','fit-report.json']:api.upload_file(path_or_fileobj=str(R/f),path_in_repo='pilot-detail/'+f,repo_id=REPO,repo_type='dataset')
print('FIT_SAVED',json.dumps(report),flush=True)
os._exit(0)
