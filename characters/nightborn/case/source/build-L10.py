# Inject before build/render scripts. Stage bytes before temporary files are reused.
from huggingface_hub import HfApi,CommitOperationAdd
from pathlib import Path
_DELIVERY='Domlynch/frankendom-nightborn-delivery-20260928'
_pending=[]
def _stage_upload(self,path_or_fileobj,path_in_repo,**kwargs):
 data=Path(path_or_fileobj).read_bytes() if isinstance(path_or_fileobj,(str,Path)) else path_or_fileobj
 _pending.append(CommitOperationAdd(path_in_repo=path_in_repo,path_or_fileobj=data))
HfApi.upload_file=_stage_upload
def _flush_uploads():
 if _pending:
  info=HfApi().create_commit(repo_id=_DELIVERY,repo_type='dataset',operations=list(_pending),commit_message='Persist verified Nightborn output batch')
  print('BATCH_PERSISTED',info.oid,len(_pending),flush=True);_pending.clear()

import bpy,bmesh,os,json,math,hashlib
from pathlib import Path
from urllib.request import Request,urlopen
from huggingface_hub import HfApi,get_token,hf_hub_url
from mathutils import Vector
RANK=10
VERSION='elites-v1'
REPO='Domlynch/frankendom-nightborn-delivery-20260928';api=HfApi();rev=api.repo_info(REPO,repo_type='dataset').sha
R=Path('/tmp/nightborn-covered');R.mkdir(exist_ok=True);label=f'L{RANK}'
for filename in ['original.glb',f'previous-{label}.glb',f'{label}-helmet.glb']:
 with urlopen(Request(hf_hub_url(REPO,'covered-r2/input/'+filename,repo_type='dataset',revision=rev),headers={'Authorization':'Bearer '+get_token()}),timeout=90) as f:(R/filename).write_bytes(f.read())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/f'previous-{label}.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
for track in rig.animation_data.nla_tracks:track.mute=True
rig.animation_data.action=None
removed=[]
# The owner explicitly replaces open faces and crowns in elite ranks only.
for o in list(bpy.context.scene.objects):
 if o.type!='MESH':continue
 if o.name in ['Face','Photo','PhotoEyes','PhotoTeeth'] or (o.name.startswith(label+'_') and o.name!=label+'_Armour'):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
armour=bpy.data.objects[label+'_Armour']
# Preserve the rich body/leg surfaces; replace the failed open-ended forearm pieces.
bm=bmesh.new();bm.from_mesh(armour.data)
cut=[]
for f in bm.faces:
 c=armour.matrix_world@f.calc_center_median()
 if abs(c.x)>.405 and c.z>1.24:cut.append(f)
bmesh.ops.delete(bm,geom=cut,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(armour.data);bm.free()
# Local ankle smoothing addresses the observed boot seam during quarter-cycle Kick.
# Position-welded adjacency leaves geometry/UVs unchanged and normalizes four influences.
import numpy as np
coords=np.array([list(armour.matrix_world@v.co) for v in armour.data.vertices]);ng=len(armour.vertex_groups);wmat=np.zeros((len(coords),ng))
for v in armour.data.vertices:
 for g in v.groups:wmat[v.index,g.group]=g.weight
unique,mapping=np.unique(np.round(coords,5),axis=0,return_inverse=True);counts=np.bincount(mapping);wm=np.zeros((len(unique),ng));np.add.at(wm,mapping,wmat);wm/=counts[:,None]
edges=np.unique(np.sort(mapping[np.array([list(e.vertices) for e in armour.data.edges])],axis=1),axis=0);strength=np.clip((unique[:,2]-.08)/.08,0,1)*np.clip((.32-unique[:,2])/.10,0,1)*np.clip((np.abs(unique[:,0])-.10)/.04,0,1)*.48
waist=np.clip((.10-np.abs(unique[:,0]))/.06,0,1)*np.clip((unique[:,2]-.82)/.07,0,1)*np.clip((1.03-unique[:,2])/.07,0,1)*np.clip((.105-np.abs(unique[:,1]))/.05,0,1)*.55
strength=np.maximum(strength,waist)
near=(strength[edges[:,0]]>0)|(strength[edges[:,1]]>0);edges=edges[near];degree=np.bincount(edges.ravel(),minlength=len(wm));active=np.where(strength>0)[0]
for iteration in range(30):
 sums=np.zeros_like(wm);np.add.at(sums,edges[:,0],wm[edges[:,1]]);np.add.at(sums,edges[:,1],wm[edges[:,0]]);average=sums/np.maximum(degree[:,None],1);wm[active]=wm[active]*(1-strength[active,None])+average[active]*strength[active,None]
vertices=np.where(strength[mapping]>0)[0]
for g in armour.vertex_groups:g.remove(vertices.tolist())
for i in vertices:
 row=wm[mapping[i]];ids=np.argsort(row)[-4:];total=row[ids].sum()
 for k in ids:
  if row[k]>1e-7:armour.vertex_groups[int(k)].add([int(i)],float(row[k]/total),'REPLACE')
print('ANKLE_AND_WAIST_PATCH',len(vertices),flush=True)

def material(name,col,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*col,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough;return m
colour={8:(.055,.047,.050),9:(.028,.125,.065),10:(.55,.31,.065)}[RANK]
metal=material(label+' articulated armour metal',colour,.82,.34)
edge=material(label+' worn plate edges',tuple(min(.7,c*1.6+.035) for c in colour),.85,.31)
lining=material(label+' fully enclosed armour joint lining',(.012,.014,.017),.30,.62)
# Dark/green/gold metal covers the upper-arm transition rather than flesh-like donor tint.
armour.data.materials.append(metal);mi=len(armour.data.materials)-1
for f in armour.data.polygons:
 c=armour.matrix_world@f.center
 if .23<abs(c.x)<.41 and 1.25<c.z<1.455:f.material_index=mi
# Obtain exact original body weights; preserve the main rig and every source clip.
existing=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(R/'original.glb'));imported=[o for o in bpy.context.scene.objects if o not in existing];src=next(o for o in imported if o.type=='MESH' and o.name.startswith('Skin'));src_rig=next(o for o in imported if o.type=='ARMATURE');src_rig.data.pose_position='REST'
for t in src_rig.animation_data.nla_tracks:t.mute=True
src_rig.animation_data.action=None
source_signature=hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in src.data.vertices]).encode()).hexdigest()
def bind(o,bone=None):
 if bone:
  o.vertex_groups.clear();o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
 o.modifiers.clear();mod=o.modifiers.new('Preserved Nightborn rig','ARMATURE');mod.object=rig;mw=o.matrix_world.copy();o.parent=rig;o.matrix_world=mw

def shell(name,predicate,mat,offset):
 o=src.copy();o.data=src.data.copy();o.name=name;bpy.context.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(o.data);faces=[f for f in bm.faces if not predicate(o.matrix_world@f.calc_center_median())];bmesh.ops.delete(bm,geom=faces,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free();o.data.materials.clear();o.data.materials.append(mat)
 normals=[v.normal.copy() for v in o.data.vertices]
 for v,normal in zip(o.data.vertices,normals):v.co+=normal*offset
 for f in o.data.polygons:f.use_smooth=True
 bind(o);print('COVER_SHELL',name,len(o.data.vertices),flush=True);return o
# A continuous fitted gorget hides the helmet/chest join without raw cut-mesh edges.
verts=[];faces=[];N=48
rings=[(1.455,.139,.125),(1.465,.143,.129),(1.479,.137,.120),(1.485,.133,.116),(1.52,.106,.097),(1.555,.091,.088),(1.60,.085,.083)]
for z,rx,ry in rings:
 for j in range(N):
  a=2*math.pi*j/N;verts.append((rx*math.cos(a),-.018+ry*math.sin(a),z))
for k in range(len(rings)-1):
 for j in range(N):faces.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
mesh=bpy.data.meshes.new('Continuous enclosed gorget');mesh.from_pydata(verts,[],faces);under=bpy.data.objects.new(label+'_CompleteJointCover',mesh);bpy.context.collection.objects.link(under);mesh.materials.append(metal);mesh.materials.append(edge)
for f in mesh.polygons:f.use_smooth=True;f.material_index=1 if f.index//N==1 else 0
for name in ['spine_03','neck_01']:under.vertex_groups.new(name=name)
for i,(x,y,z) in enumerate(verts):
 mix=max(0,min(1,(z-1.48)/.08));under.vertex_groups['spine_03'].add([i],1-mix,'REPLACE');under.vertex_groups['neck_01'].add([i],mix,'REPLACE')
bind(under)
arms=shell(label+'_ArmouredArmsAndGauntlets',lambda p:abs(p.x)>.255 and p.z>1.27,metal,.008)
# Articulated arm lames use measured original arm sections, with no hollow cuff opening.
points=[src.matrix_world@v.co for v in src.data.vertices]
for side in [-1,1]:
 for x in [.33,.385,.48,.54,.60,.65]:
  section=[p for p in points if abs(abs(p.x)-x)<.012 and p.z>1.29]
  cy=(min(p.y for p in section)+max(p.y for p in section))/2;cz=(min(p.z for p in section)+max(p.z for p in section))/2;ry=(max(p.y for p in section)-min(p.y for p in section))/2+.012;rz=(max(p.z for p in section)-min(p.z for p in section))/2+.012
  verts=[];faces=[];N=24
  for xx,scale in [(-.012,1),(-.008,1.035),(.008,1.035),(.012,1)]:
   for j in range(N):
    a=2*math.pi*j/N;verts.append((side*(x+xx),cy+ry*scale*math.cos(a),cz+rz*scale*math.sin(a)))
  for k in range(3):
   for j in range(N):faces.append((k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j))
  mesh=bpy.data.meshes.new('Closed-over-sleeve articulated lame');mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new(label+'_ArmLame',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(edge);bone=('upperarm_' if x<.42 else 'lowerarm_' if x<.63 else 'hand_')+('l' if side>0 else 'r');bind(o,bone)
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
# Detailed reconstructed helmet is a complete shell, not a circlet or face repaint.
existing=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(R/f'{label}-helmet.glb'));helmet=next(o for o in bpy.context.scene.objects if o not in existing and o.type=='MESH');helmet.name=label+'_ClosedHelmet'
pts=[helmet.matrix_world@v.co for v in helmet.data.vertices];low=min(p.z for p in pts);high=max(p.z for p in pts);scale=.53/(high-low);cx=(min(p.x for p in pts)+max(p.x for p in pts))/2;cy=(min(p.y for p in pts)+max(p.y for p in pts))/2
for v,p in zip(helmet.data.vertices,pts):v.co=((p.x-cx)*scale,(p.y-cy)*scale-.035,(p.z-low)*scale+1.525)
helmet.matrix_world.identity();bind(helmet,'Head')
for mat in helmet.data.materials:
 for node in mat.node_tree.nodes:
  if node.type=='BSDF_PRINCIPLED':node.inputs['Emission Strength'].default_value=0
# Reject any surviving source face, eyes, hair or old open crown draws.
active=[o.name for o in bpy.context.scene.objects if o.type=='MESH'];assert not any(n in active for n in ['Face','Photo','PhotoEyes','PhotoTeeth']);assert not any('Crown'in n or 'SweptProng'in n for n in active)
rig.data.pose_position='POSE';blend=R/f'nightborn-{label}.blend';output=R/f'nightborn-{label}.glb';bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',export_animations=True,export_tangents=False,use_visible=True)
receipt={'rank':RANK,'version':VERSION,'removedOpenFaceAndCrownMeshes':removed,'activeMeshes':active,'originalSkinWeightSignature':source_signature,'fullCoverageParts':[under.name,arms.name,helmet.name],'helmetScale':scale,'helmetHeight':.53,'helmetBaseZ':1.525,'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in R.glob('*.glb') if p!=output},'candidate':'exported; coverage and motion review required'}
(R/'build.json').write_text(json.dumps(receipt,indent=2))
for p in [blend,output,R/'build.json']:api.upload_file(path_or_fileobj=str(p),path_in_repo=f'covered-r2/{VERSION}/{label}/'+p.name,repo_id=REPO,repo_type='dataset')
print('EXPORTED',label,flush=True)
_flush_uploads();os._exit(0)
