import bpy,bmesh,json,hashlib,os,math
from pathlib import Path
from urllib.request import Request,urlopen
from huggingface_hub import HfApi,get_token,hf_hub_url
from mathutils import Vector
from mathutils.bvhtree import BVHTree
REPO='Domlynch/frankendom-nightborn-ranks-20260928';R=Path('/tmp/nightborn-pilot');R.mkdir(exist_ok=True);api=HfApi();rev=api.repo_info(REPO,repo_type='dataset').sha
for name in ['original.glb','L5-donor.glb']:
 with urlopen(Request(hf_hub_url(REPO,name,repo_type='dataset',revision=rev),headers={'Authorization':'Bearer '+get_token()}),timeout=90) as f:(R/name).write_bytes(f.read())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'original.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
for t in rig.animation_data.nla_tracks:t.mute=True
rig.animation_data.action=None
original=[o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.vertices)>50]
def signature(o):return hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices]).encode()).hexdigest()
before={o.name:signature(o) for o in original};body=bpy.data.objects['Skin'];body.data.calc_loop_triangles();pts=[body.matrix_world@v.co for v in body.data.vertices];faces=[tuple(t.vertices) for t in body.data.loop_triangles];bvh=BVHTree.FromPolygons(pts,faces,all_triangles=True);groups={g.index:g.name for g in body.vertex_groups}
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'L5-donor.glb'));donor=next(o for o in bpy.context.scene.objects if o not in existing and o.type=='MESH');donor.name='L5_Armour'
world_points=[donor.matrix_world@v.co for v in donor.data.vertices]
zmin=min(p.z for p in world_points)
import statistics
armheight=statistics.median(p.z for p in world_points if .28<abs(p.x)<.38)-zmin
scale=1.90*.7818291/armheight
assert 1.6<scale<2.3, ('unexpected reference proportions',scale)
print('CALIBRATED SCALE',scale,flush=True)
def remap(v,xs,ys):
 for i in range(len(xs)-1):
  if v<=xs[i+1]:return ys[i]+(v-xs[i])/(xs[i+1]-xs[i])*(ys[i+1]-ys[i])
 return ys[-1]+v-xs[-1]
for v in donor.data.vertices:
 p=donor.matrix_world@v.co;p*=scale;p.z-=zmin*scale
 p.z=remap(p.z,[0,.54,.98,1.51,1.62,1.902],[.025,.542,.971,1.455,1.565,1.915]);p.y+=.025
 arm_blend=max(0,min(1,(abs(p.x)-.20)/.15));p.y+=.040*arm_blend;p.z+=.024*arm_blend
 v.co=p
donor.matrix_world.identity()
# Remove reconstructed head and hands. Keep authentic face; gloves use original finger weights.
remove=[]
for f in donor.data.polygons:
 c=sum((donor.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
 remove.append(c.z>1.652 or (abs(c.x)>.660 and c.z>1.32))
bm=bmesh.new();bm.from_mesh(donor.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if remove[f.index]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(donor.data);bm.free()
bm=bmesh.new();bm.from_mesh(donor.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
seen=set();discard=[]
for v in list(bm.verts):
 if v in seen:continue
 todo=[v];component=[];seen.add(v)
 while todo:
  q=todo.pop();component.append(q)
  for e in q.link_edges:
   other=e.other_vert(q)
   if other not in seen:seen.add(other);todo.append(other)
 if len(component)<40 and max(v.co.z for v in component)<.12:discard.extend(component)
bmesh.ops.delete(bm,geom=discard,context='VERTS')
bm.to_mesh(donor.data);bm.free()

for v in donor.data.vertices:
 hit=bvh.find_nearest(v.co);ids=faces[hit[2]];a,b,c=[pts[i] for i in ids];e0=b-a;e1=c-a;e2=hit[0]-a;d00=e0.dot(e0);d01=e0.dot(e1);d11=e1.dot(e1);den=d00*d11-d01*d01;u=(d11*e2.dot(e0)-d01*e2.dot(e1))/den if abs(den)>1e-12 else 0;w=(d00*e2.dot(e1)-d01*e2.dot(e0))/den if abs(den)>1e-12 else 0
 weights={}
 for idx,factor in zip(ids,[max(0,1-u-w),max(0,u),max(0,w)]):
  for g in body.data.vertices[idx].groups:weights[groups[g.group]]=weights.get(groups[g.group],0)+factor*g.weight
 # Short central waist tassets follow pelvis rather than opposite legs.
 if .72<v.co.z<1.02:
  tx=max(0,min(1,(.095-abs(v.co.x))/.045));ty=max(0,min(1,(abs(v.co.y)-.075)/.045));t=tx*tx*(3-2*tx)*ty*ty*(3-2*ty)
  weights={n:w*(1-t) for n,w in weights.items()};weights['pelvis']=weights.get('pelvis',0)+t

 if abs(v.co.x)>.12 and v.co.z>1.24:
  ax=abs(v.co.x);side='l' if v.co.x>0 else 'r'
  def smooth(a,b,x):
   t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
  clav=smooth(.12,.23,ax);upper=smooth(.16,.40,ax);fore=smooth(.38,.48,ax);hand=smooth(.55,.68,ax)
  stable={'spine_03':1-clav,'clavicle_'+side:clav*(1-upper),'upperarm_'+side:upper*(1-fore),'lowerarm_'+side:fore*(1-hand),'hand_'+side:hand}
  strength=smooth(1.24,1.36,v.co.z)
  weights={n:w*(1-strength) for n,w in weights.items()}
  for n,w in stable.items():weights[n]=weights.get(n,0)+w*strength
 weights=dict(sorted(weights.items(),key=lambda q:q[1],reverse=True)[:4]);total=sum(weights.values());assert total>0
 for n,w in weights.items():
  if w>0:(donor.vertex_groups.get(n) or donor.vertex_groups.new(name=n)).add([v.index],w/total,'REPLACE')
# Smooth only the demonstrated central cloth transition over welded adjacency.
import numpy as np
ng=len(donor.vertex_groups);wmat=np.zeros((len(donor.data.vertices),ng));coords=np.array([tuple(v.co) for v in donor.data.vertices])
for v in donor.data.vertices:
 for g in v.groups:wmat[v.index,g.group]=g.weight
edges=np.array([tuple(e.vertices) for e in donor.data.edges]);strength=np.clip((.17-np.abs(coords[:,0]))/.06,0,1)*np.clip((np.abs(coords[:,1])-.045)/.045,0,1)*np.clip((coords[:,2]-.60)/.10,0,1)*np.clip((1.04-coords[:,2])/.08,0,1)*.48
near=(strength[edges[:,0]]>0)|(strength[edges[:,1]]>0);edges=edges[near];degree=np.bincount(edges.ravel(),minlength=len(wmat));active=np.where(strength>0)[0]
for iteration in range(30):
 sums=np.zeros_like(wmat);np.add.at(sums,edges[:,0],wmat[edges[:,1]]);np.add.at(sums,edges[:,1],wmat[edges[:,0]]);average=sums/np.maximum(degree[:,None],1);wmat[active]=wmat[active]*(1-strength[active,None])+average[active]*strength[active,None]
for g in donor.vertex_groups:g.remove(active.tolist())
for i in active:
 row=wmat[i];ids=np.argsort(row)[-4:];total=row[ids].sum()
 for k in ids:
  if row[k]>1e-7:donor.vertex_groups[int(k)].add([int(i)],float(row[k]/total),'REPLACE')

def bind(o,bone=None):
 if bone:o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
 mod=o.modifiers.new('Original rig','ARMATURE');mod.object=rig;mw=o.matrix_world.copy();o.parent=rig;o.matrix_world=mw
bind(donor)
# Original colour/weight payloads kept; obsolete kit hidden in candidate.
hidden=bpy.data.materials.new('Preserved original hidden under new armour');hidden.use_nodes=True;hidden.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=0;hidden.surface_render_method='DITHERED'
for o in original:
 if o.name in ['Face','Photo','PhotoEyes','PhotoTeeth'] or o.name.startswith('WeaponDrawn'):continue
 o.data.materials.clear();o.data.materials.append(hidden)
def material(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough;return m
steel=material('L5 crown metal',(0.35, 0.22, 0.067),0.8,0.42);ruby=material('Deep crimson faceted ruby',(.19,.006,.014),.22,.20);leather=material('Oxblood glove leather',(.018,.004,.006),0,.65)
# Close-fitting hand shells retain every original finger influence.
glove=body.copy();glove.data=body.data.copy();glove.name='L5_FittedGloves';bpy.context.collection.objects.link(glove)
def hw(v):return sum(g.weight for g in v.groups if groups[g.group].startswith(('hand_','thumb_','index_','middle_','ring_','pinky_')))
keep=[all(abs((glove.matrix_world@glove.data.vertices[i].co).x)>.595 and 1.34<(glove.matrix_world@glove.data.vertices[i].co).z<1.62 for i in f.vertices) for f in glove.data.polygons];bm=bmesh.new();bm.from_mesh(glove.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep[f.index]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(glove.data);bm.free();glove.data.materials.clear();glove.data.materials.append(leather)
for v in glove.data.vertices:v.co+=v.normal*.004
# Tailored articulated wrist cuffs, bound at the original measured wrists.
for side,bone in [(-1,'hand_r'),(1,'hand_l')]:
 center=rig.matrix_world@rig.data.bones[bone].head_local
 verts=[];faces2=[];N=32
 for offset,rad in [(-.070,.055),(-.035,.047),(.017,.035)]:
  for i in range(N):
   a=2*math.pi*i/N;verts.append((center.x+side*offset,center.y+rad*math.sin(a),center.z+rad*math.cos(a)))
 for layer in range(2):
  for i in range(N):j=(i+1)%N;faces2.append((layer*N+i,layer*N+j,(layer+1)*N+j,(layer+1)*N+i))
 me=bpy.data.meshes.new('Tailored cuff');me.from_pydata(verts,[],faces2);o=bpy.data.objects.new('L5_WristCuff',me);bpy.context.collection.objects.link(o);o.data.materials.append(leather);bind(o,bone)
# Authored open crown, seated to original head, independent of generated face.
verts=[];fs=[];N=64
for z,rx,ry in [(1.795,.119,.130),(1.817,.120,.131),(1.795,.112,.123),(1.817,.113,.124)]:
 for i in range(N):
  a=2*math.pi*i/N;verts.append((rx*math.cos(a),-.05+ry*math.sin(a),z))
for i in range(N):
 j=(i+1)%N
 for a,b in [(0,1),(1,3),(3,2),(2,0)]:fs.append((a*N+i,a*N+j,b*N+j,b*N+i))
mesh=bpy.data.meshes.new('L5 crown ring');mesh.from_pydata(verts,[],fs);o=bpy.data.objects.new('L5_OpenCrown',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(steel);bind(o,'Head')
# Rank 5: distinct open crown geometry, no face cover.
for i in range(5):
 a=math.pi+(i+1)*math.pi/(5+1)
 x=.120*math.cos(a);y=-.05+.132*math.sin(a)
 height=0.035*(.65+.35*(1-abs(x)/.12))
 width=0.011
 verts=[(x-width,y-.008,1.808),(x+width,y-.008,1.808),(x+width,y+.006,1.812),(x-width,y+.006,1.812),(x*1.1,y+0,1.812+height)]
 me=bpy.data.meshes.new('Crown leaf');me.from_pydata(verts,[],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)]);o=bpy.data.objects.new('L5_CrownLeaf',me);bpy.context.collection.objects.link(o);o.data.materials.append(steel);bind(o,'Head')
for m in donor.data.materials:
 for n in m.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':n.inputs['Emission Strength'].default_value=0
assert all(before[o.name]==signature(o) for o in original)
rig.data.pose_position='POSE'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'nightborn-L5.blend'))
bpy.ops.export_scene.gltf(filepath=str(R/'nightborn-L5.glb'),export_format='GLB',use_visible=True,export_animations=True,export_tangents=False)
# Alpha-zero retained originals can still produce import/render artifacts. Keep their
# mesh data in the GLB but remove scene mesh references, consistently across renderers.
import struct
p=R/'nightborn-L5.glb';data=p.read_bytes();jn=struct.unpack_from('<I',data,12)[0];model=json.loads(data[20:20+jn]);binary=data[28+jn:];deactivated=[]
for node in model['nodes']:
 if node.get('name') in [o.name for o in original if o.data.materials[0]==hidden] and 'mesh' in node:
  node.setdefault('extras',{})['preservedInactiveMesh']=node.pop('mesh');node.pop('skin',None);deactivated.append(node['name'])
payload=json.dumps(model,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4);p.write_bytes(struct.pack('<III',0x46546c67,2,28+len(payload)+len(binary))+struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary)
print('DEACTIVATED ORIGINAL DRAWS',deactivated,flush=True)

(R/'build.json').write_text(json.dumps({'source_signatures':before,'unchanged_original_vertices_weights':True,'donor_scale':scale,'face':'original Photo/Face/Eyes/Teeth retained visibly','hidden_originals':[o.name for o in original if o.data.materials[0]==hidden],'candidate':'first fit, visual acceptance pending'},indent=2))
for name in ['nightborn-L5.blend','nightborn-L5.glb','build.json']:api.upload_file(path_or_fileobj=str(R/name),path_in_repo='corrected/L5/'+name,repo_id=REPO,repo_type='dataset')
print('PILOT_EXPORTED',flush=True);
