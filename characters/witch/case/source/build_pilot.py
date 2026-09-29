"""Witch-specific surface fit; original rig stays immutable in final packing."""
from pathlib import Path
import bpy,bmesh,json,hashlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
ROOT=Path.cwd(); OUT=ROOT/'source/pilot';OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'source/original.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');body=bpy.data.objects['CreatureBody']
for tr in rig.animation_data.nla_tracks:tr.mute=True
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
original=[o for o in bpy.context.scene.objects if o.type=='MESH']
def sig(o):return hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices]).encode()).hexdigest()
before={o.name:sig(o) for o in original}
pts=[body.matrix_world@v.co for v in body.data.vertices];body.data.calc_loop_triangles();faces=[tuple(t.vertices) for t in body.data.loop_triangles]
source_groups={g.index:g.name for g in body.vertex_groups}
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'src/assets/source/creatures/witch-L8-donor.glb'))
donor=next(o for o in bpy.context.scene.objects if o not in existing and o.type=='MESH');donor.name='Witch_L8_Armour'
dp=np.array([list(donor.matrix_world@v.co) for v in donor.data.vertices]);lo=dp[:,2].min();scale=1.81/(dp[:,2].max()-lo)
q=dp*scale;q[:,2]=(dp[:,2]-lo)*scale+.025
# Align reconstructed anatomical landmarks with this Witch's measured bind skeleton.
# The peaked helmet extends above the source head; body height remains unchanged.
# Initial fit is judged in actual exported-file poses before any replication.
for v,p in zip(donor.data.vertices,q):v.co=Vector(p)
donor.matrix_world.identity()
arm_names=('upperarm_','lowerarm_','hand_','thumb_','index_','middle_','ring_','pinky_')
def arm_fraction(i):return sum(g.weight for g in body.data.vertices[i].groups if source_groups[g.group].startswith(arm_names))
arm_faces=[f for f in faces if sum(arm_fraction(i) for i in f)/3>.7]
arm_bvh=BVHTree.FromPolygons(pts,arm_faces,all_triangles=True)
for name in source_groups.values():donor.vertex_groups.new(name=name)
def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def bary(hit,fs):
 ids=fs[hit[2]];a,b,c=[pts[i] for i in ids];e0,e1,e2=b-a,c-a,hit[0]-a
 d00,d01,d11,d20,d21=e0.dot(e0),e0.dot(e1),e1.dot(e1),e2.dot(e0),e2.dot(e1);den=d00*d11-d01*d01
 u=(d11*d20-d01*d21)/den if abs(den)>1e-12 else 0;w=(d00*d21-d01*d20)/den if abs(den)>1e-12 else 0;weights={}
 for idx,factor in zip(ids,[max(0,1-u-w),max(0,u),max(0,w)]):
  for g in body.data.vertices[idx].groups:
   n=source_groups[g.group];weights[n]=weights.get(n,0)+g.weight*factor
 return weights
for v in donor.data.vertices:
 x,y,z=v.co;ax=abs(x);side='l' if x>0 else 'r'
 # Pose-independent smooth fields keep nearby robe cloth off hand/calf bones.
 arm_boundary=.20 if z>1.25 else .235
 is_arm=ax>arm_boundary and .76<z<1.5
 if is_arm:
  weights=bary(arm_bvh.find_nearest(v.co),arm_faces)
 elif z>1.48:
  t=smooth(1.48,1.58,z);weights={'neck_01':1-t,'Head':t}
 elif z>1.04:
  zs=[1.04,1.17,1.30,1.46];names=['pelvis','spine_02','spine_03','spine_03'];k=min(2,max(0,int(np.searchsorted(zs,z))-1));t=smooth(zs[k],zs[k+1],z);weights={names[k]:1-t};weights[names[k+1]]=weights.get(names[k+1],0)+t
 else:
  # Front/rear hanging panels have a continuous bilateral thigh field.
  # Limb plates follow the nearest anatomical leg, with smooth knee/ankle joins.
  is_cloth=(abs(y)>.13 and z>.25) or (ax<.052 and z>.3) or (ax>.205 and z>.3)
  if is_cloth:
   leg=.55*(1-smooth(.50,1.02,z));lr=smooth(-.11,.11,x);weights={'pelvis':1-leg,'thigh_l':leg*lr,'thigh_r':leg*(1-lr)}
  else:
   pelvis=smooth(.90,1.04,z);calf=1-smooth(.48,.62,z);foot=1-smooth(.08,.19,z)
   weights={'pelvis':pelvis,'thigh_'+side:(1-pelvis)*(1-calf),'calf_'+side:(1-pelvis)*calf*(1-foot),'foot_'+side:(1-pelvis)*calf*foot}
 ws=sorted([(n,w) for n,w in weights.items() if w>1e-7],key=lambda a:a[1],reverse=True)[:4];total=sum(w for _,w in ws);assert total>0
 for n,w in ws:donor.vertex_groups[n].add([v.index],w/total,'REPLACE')
mod=donor.modifiers.new('Original Witch skeleton','ARMATURE');mod.object=rig;mw=donor.matrix_world.copy();donor.parent=rig;donor.matrix_world=mw
hidden=bpy.data.materials.new('Original retained below candidate');hidden.use_nodes=True;hidden.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=0;hidden.surface_render_method='DITHERED';body.data.materials.clear();body.data.materials.append(hidden)
for mat in donor.data.materials:
 for node in mat.node_tree.nodes:
  if node.type=='BSDF_PRINCIPLED':node.inputs['Emission Strength'].default_value=0
assert all(before[o.name]==sig(o) for o in original)
# Export only the source rig, source attachments/body and new armour; exclude addon helpers.
bpy.ops.object.select_all(action='DESELECT')
for o in original+[rig,donor]:o.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'witch-L8.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'witch-L8.glb'),export_format='GLB',use_selection=True,export_animations=False,export_tangents=False)
(OUT/'build.json').write_text(json.dumps({'scale':float(scale),'originalVertexWeightSignatures':before,'preserved':True,'armFaces':len(arm_faces),'newTriangles':sum(len(f.vertices)-2 for f in donor.data.polygons),'status':'UNREVIEWED pilot; original visible body replaced by donor; pack original binary rig next'},indent=2))
