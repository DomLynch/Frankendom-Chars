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

import bpy,json,hashlib,os
from pathlib import Path
from urllib.request import Request,urlopen
from huggingface_hub import HfApi,get_token,hf_hub_url
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
REPO='Domlynch/frankendom-nightborn-delivery-20260928';api=HfApi();rev=api.repo_info(REPO,repo_type='dataset').sha
R=Path('/tmp/nightborn-final');R.mkdir(exist_ok=True)
RANKS=[3]
for rank in RANKS:
 label=f'L{rank}';path=R/f'nightborn-{label}.glb'
 with urlopen(Request(hf_hub_url(REPO,f'final/nightborn-{label}.glb',repo_type='dataset',revision=rev),headers={'Authorization':'Bearer '+get_token()}),timeout=90) as f:path.write_bytes(f.read())
 sha=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 for t in rig.animation_data.nla_tracks:t.mute=True
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=32;s.render.threads_mode='FIXED';s.render.threads=8;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
 s.world=bpy.data.worlds.new('Neutral studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
 target=Vector((0,0,1.03));bpy.ops.object.camera_add(location=(0,-6,1.1));cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam
 for loc,power,size in [((-3,-4,5),650,3),((3,-2,3),300,3),((1,2,4),450,2)]:
  bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=size;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
 import numpy as np
 armour=bpy.data.objects[label+'_Armour'];rig.data.pose_position='REST';rig.animation_data.action=None;bpy.context.view_layer.update();ev=armour.evaluated_get(bpy.context.evaluated_depsgraph_get());rest=np.array([list(ev.matrix_world@v.co) for v in ev.data.vertices]);edges=np.array([list(e.vertices) for e in ev.data.edges]);restLength=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
 receipts=[]
 for view,clip,time in [('front','Armed',.35),('back','Armed',.35),('side','Armed',.35),('attack','Heavy',.45),('guard','Guard',.4),('kick','Kick',.4),('phone','Armed',.35),('fight','Armed',.35),('rest',None,0),('head','Armed',.35)]:
  rig.data.pose_position='REST' if clip is None else 'POSE';action=bpy.data.actions.get(clip) if clip else None;rig.animation_data.action=action
  if action and len(action.slots):rig.animation_data.action_slot=action.slots[0]
  s.frame_set(round(time*s.render.fps));cam.location=(6,0,1.1) if view=='side' else (0,6 if view=='back' else -6,1.1);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.25 if view=='rest' else 2.5
  s.render.resolution_x=375 if view in ['phone','fight'] else 600;s.render.resolution_y=600 if view in ['phone','fight'] else 900
  if view=='head':
   bpy.context.view_layer.update();ev=bpy.data.objects['Photo'].evaluated_get(bpy.context.evaluated_depsgraph_get());points=[ev.matrix_world@v.co for v in ev.data.vertices];focus=Vector(tuple((min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)));focus.z+=.04;cam.location=(focus.x,-6,focus.z);cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.48;s.render.resolution_x=600;s.render.resolution_y=600
  projected=None
  if view=='fight':
   bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();points=[]
   for o in s.objects:
    if o.type!='MESH' or not o.name.startswith(label+'_'):continue
    ev=o.evaluated_get(dg);points.extend(ev.matrix_world@v.co for v in ev.data.vertices)
   ys=[world_to_camera_view(s,cam,p).y for p in points];current=(max(ys)-min(ys))*s.render.resolution_y;cam.data.ortho_scale*=current/110;bpy.context.view_layer.update();ys=[world_to_camera_view(s,cam,p).y for p in points];projected=(max(ys)-min(ys))*s.render.resolution_y
  deformation=None
  if clip:
   bpy.context.view_layer.update();ev=armour.evaluated_get(bpy.context.evaluated_depsgraph_get());pos=np.array([list(ev.matrix_world@v.co) for v in ev.data.vertices]);posed=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1);ratio=posed/np.maximum(restLength,1e-6);deformation={'longStretchedEdges':int(np.sum((ratio>3)&(posed>.10))),'maxRatio':float(ratio.max()),'threshold':'posed length > 0.10m AND > 3x rest'}
  output=R/f'{label}-{view}.png';s.render.filepath=str(output);bpy.ops.render.render(write_still=True)
  api.upload_file(path_or_fileobj=str(output),path_in_repo=f'final/renders/{output.name}',repo_id=REPO,repo_type='dataset')
  receipts.append({'rank':rank,'model':path.name,'sha256':sha,'image':output.name,'clip':clip,'frame':s.frame_current,'fps':s.render.fps,'camera':list(cam.location),'target':list(focus if view=='head' else target),'cameraRotationEuler':list(cam.rotation_euler),'orthoScale':cam.data.ortho_scale,'viewport':[s.render.resolution_x,s.render.resolution_y],'projectedArmourHeightPx':projected,'deformation':deformation,'scope':'CPU studio approximation, not arena or physical phone performance'})
 out=R/f'{label}-render-receipt.json';out.write_text(json.dumps(receipts,indent=2));api.upload_file(path_or_fileobj=str(out),path_in_repo='final/'+out.name,repo_id=REPO,repo_type='dataset')
 print('FINAL_RENDERED',label,sha,flush=True)
_flush_uploads();os._exit(0)
