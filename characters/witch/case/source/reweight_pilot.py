"""Correct measured Witch donor arm alignment and continuous anatomical weights."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='source/pilot/witch-L8.blend')
d=bpy.data.objects['Witch_L8_Armour'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
# Remove earlier field: the original Witch cloak is not an anatomical weight donor.
d.vertex_groups.clear()
for b in rig.data.bones:d.vertex_groups.new(name=b.name)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return float(t*t*(3-2*t))
for v in d.data.vertices:
 x,y,z=v.co;ax=abs(x);side='l' if x>0 else 'r';sign=1 if x>0 else -1
 # Arms are separated from the robe in this donor. Blend horizontal correction
 # from shoulder to wrist; no global body enlargement or skeleton edits.
 boundary=.235 if z>1.26 else .27
 arm=smooth(boundary-.025,boundary+.025,ax)*smooth(.76,.84,z)*(1-smooth(1.43,1.53,z))
 dx=.11*(1-smooth(.93,1.48,z));v.co.x-=sign*dx*arm
 x,y,z=v.co;ax=abs(x)
 torso={}
 if z>1.45:
  h=smooth(1.46,1.59,z);torso={'spine_03':1-h,'Head':h}
 elif z>1.03:
  vals=[(1.03,'pelvis'),(1.17,'spine_02'),(1.30,'spine_03'),(1.46,'spine_03')]
  k=min(2,max(0,int(np.searchsorted([a[0] for a in vals],z))-1));t=smooth(vals[k][0],vals[k+1][0],z);torso={vals[k][1]:1-t};torso[vals[k+1][1]]=torso.get(vals[k+1][1],0)+t
 else:
  # Smooth mix across cloth/plate zones avoids the earlier hard threshold seams.
  cloth=max(smooth(.105,.16,abs(y)),1-smooth(.035,.075,ax),smooth(.18,.235,ax))*smooth(.22,.35,z)
  leg=.55*(1-smooth(.50,1.02,z));lr=smooth(-.12,.12,x)
  torso={'pelvis':cloth*(1-leg),'thigh_l':cloth*leg*lr,'thigh_r':cloth*leg*(1-lr)}
  pel=smooth(.90,1.04,z);calf=1-smooth(.48,.62,z);foot=1-smooth(.08,.19,z)
  for n,w in {'pelvis':pel,'thigh_'+side:(1-pel)*(1-calf),'calf_'+side:(1-pel)*calf*(1-foot),'foot_'+side:(1-pel)*calf*foot}.items():torso[n]=torso.get(n,0)+(1-cloth)*w
 # Analytic arm chain follows measured shoulder1.413 elbow1.179 wrist0.952.
 low=1-smooth(1.13,1.23,z);hand=1-smooth(.92,1.00,z)
 aw={'upperarm_'+side:1-low,'lowerarm_'+side:low*(1-hand),'hand_'+side:low*hand}
 weights={n:w*(1-arm) for n,w in torso.items()}
 for n,w in aw.items():weights[n]=weights.get(n,0)+arm*w
 weights=sorted([(n,w) for n,w in weights.items() if w>1e-7],key=lambda q:q[1],reverse=True)[:4];total=sum(w for _,w in weights)
 for n,w in weights:d.vertex_groups[n].add([v.index],w/total,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath='source/pilot/witch-L8-v2.blend')
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,d]:o.select_set(True)
bpy.ops.export_scene.gltf(filepath='source/pilot/witch-L8-v2.glb',export_format='GLB',use_selection=True,export_animations=False,export_tangents=False)
