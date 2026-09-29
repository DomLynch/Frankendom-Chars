# /// script
# dependencies = ["bpy==5.2.2","requests>=2.32.0","numpy>=2.0"]
# ///
import hashlib, json, math, os
from pathlib import Path

import bpy
import numpy as np
import requests
from mathutils import Vector

PIT_URL="https://raw.githubusercontent.com/DomLynch/RPG-game/codex/01a09a76/task-1/src/assets/pitborn.glb"
DONOR_URL="https://raw.githubusercontent.com/DomLynch/RPG-game/codex/01a09a76/task-1/public/looks/nightborn-L8.glb"
OUT=Path("/tmp/pitborn-L8-donor.glb")
PRE=Path("/tmp/pitborn-L8-donor-front.png")
CONTACT=Path("/tmp/pitborn-L8-donor-contact.png")
REPORT=Path("/tmp/pitborn-L8-donor.json")

def download(url,path):
    r=requests.get(url,timeout=120); r.raise_for_status(); Path(path).write_bytes(r.content)

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def upload(path):
    with open(path,"rb") as f:
        r=requests.post("https://tempfile.org/api/upload/local",
            files={"files":(Path(path).name,f)},data={"expiryHours":"24"},timeout=300)
    r.raise_for_status()
    j=r.json()
    if not j.get("success"): raise RuntimeError(j)
    return j["files"][0]["url"].rstrip("/")+"/download"

pit=Path("/tmp/pitborn.glb")
donor=Path(os.environ.get("PITBORN_L8_DONOR","/tmp/nightborn-L8.glb"))
download(PIT_URL,pit)
if not donor.exists():
    download(DONOR_URL,donor)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(pit))
pit_objs=set(bpy.context.scene.objects)
pit_rig=max((o for o in pit_objs if o.type=="ARMATURE"),key=lambda o:len(o.data.bones))
pit_rig.data.pose_position="REST"
if pit_rig.animation_data:
    pit_rig.animation_data.action=None
    for t in pit_rig.animation_data.nla_tracks: t.mute=True

# Import elite donor overlay.
bpy.ops.import_scene.gltf(filepath=str(donor))
new=[o for o in bpy.context.scene.objects if o not in pit_objs]
donor_rig=max((o for o in new if o.type=="ARMATURE"),key=lambda o:len(o.data.bones))
donor_rig.data.pose_position="REST"
donor_meshes=[o for o in new if o.type=="MESH" and o.name.startswith("L8_")]
if not donor_meshes:
    raise RuntimeError("No L8 donor armour meshes")
print("DONOR_DRAWS",[o.name for o in donor_meshes],flush=True)

# Similarity fit from shared rest skeleton. Both use the same humanoid family;
# solve only uniform scale+translation so weights/bone names remain meaningful.
names=["pelvis","spine_03","Head","hand_l","hand_r","foot_l","foot_r"]
pairs=[]
for name in names:
    pb=pit_rig.data.bones.get(name); db=donor_rig.data.bones.get(name)
    if pb and db:
        pairs.append((pit_rig.matrix_world@pb.head_local,donor_rig.matrix_world@db.head_local))
if len(pairs)<4: raise RuntimeError("Insufficient shared rig landmarks")
P=np.array([list(p) for p,d in pairs]); D=np.array([list(d) for p,d in pairs])
pc=P[0]; dc=D[0]
rat=[]
for p,d in zip(P[1:],D[1:]):
    nd=np.linalg.norm(d-dc); npit=np.linalg.norm(p-pc)
    if nd>1e-6: rat.append(npit/nd)
scale=float(np.median(rat))
translation=Vector(pc)-Vector(dc)*scale
print("FIT_SCALE",scale,"TRANSLATION",list(translation),flush=True)

shared={b.name for b in pit_rig.data.bones}&{b.name for b in donor_rig.data.bones}
for o in donor_meshes:
    mw=o.matrix_world.copy()
    # Bake global donor->Pitborn similarity into object world transform.
    mw.translation = mw.translation*scale + translation
    mw[0][0]*=scale; mw[0][1]*=scale; mw[0][2]*=scale
    mw[1][0]*=scale; mw[1][1]*=scale; mw[1][2]*=scale
    mw[2][0]*=scale; mw[2][1]*=scale; mw[2][2]*=scale
    o.matrix_world=mw
    # Rebind modifier from donor armature to Pitborn.
    for m in list(o.modifiers):
        if m.type=="ARMATURE": m.object=pit_rig
    if not any(m.type=="ARMATURE" for m in o.modifiers):
        m=o.modifiers.new("Pitborn preserved rig","ARMATURE"); m.object=pit_rig
    keep=o.matrix_world.copy()
    o.parent=pit_rig
    o.matrix_world=keep
    o["frankendom_character"]="pitborn"
    o["frankendom_rank"]=8
    # Fail fast if donor references bones Pitborn lacks.
    missing=[g.name for g in o.vertex_groups if g.name not in shared]
    if missing: raise RuntimeError(f"{o.name} missing bones {missing[:10]}")

# Remove donor armature and any donor extras.
for o in list(new):
    if o is donor_rig or (o.type=="MESH" and o not in donor_meshes):
        bpy.data.objects.remove(o,do_unlink=True)
if donor_rig.name in bpy.data.objects:
    bpy.data.objects.remove(donor_rig,do_unlink=True)

# Keep Pitborn face/body/cleaver exactly; hide old headgear only if it collides with closed donor helmet.
for o in pit_objs:
    if o.type=="MESH" and o.name and any(k in o.name.lower() for k in ["helmet","cap"]):
        o.hide_render=True

# Add restrained Pitborn identity cues using his existing bone material where possible.
bone_mat=bpy.data.materials.get("BoneWorn") or bpy.data.materials.get("Bone")
if bone_mat is None:
    bone_mat=bpy.data.materials.new("Pitborn old bone")
    bone_mat.diffuse_color=(0.26,0.20,0.12,1)
    bone_mat.use_nodes=True
    bs=bone_mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(0.26,0.20,0.12,1)
    bs.inputs["Roughness"].default_value=.78

def parent_bone(obj,bone):
    world=obj.matrix_world.copy(); obj.parent=pit_rig; obj.parent_type="BONE"; obj.parent_bone=bone; obj.matrix_world=world
    obj["frankendom_character"]="pitborn"; obj["frankendom_rank"]=8

def bone_world(name,t=.5):
    b=pit_rig.data.bones[name]
    return (pit_rig.matrix_world@b.head_local).lerp(pit_rig.matrix_world@b.tail_local,t)

for i,(x,ang) in enumerate([(-.14,-18),(.15,22)]):
    c=bone_world("spine_03",.55)+Vector((x,-.20,-.05))
    bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=.025,radius2=.008,depth=.16,location=c,
                                    rotation=(math.radians(90),math.radians(ang),0))
    o=bpy.context.object; o.name=f"L8_PitbornBoneTrophy_{i}"; o.data.materials.append(bone_mat); parent_bone(o,"spine_03")

# Asymmetric brutal shoulder tooth: small, not fantasy-huge.
c=bone_world("clavicle_l",.7)+Vector((.11,-.02,.06))
bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=.035,radius2=.004,depth=.20,location=c,
                                rotation=(0,math.radians(70),0))
sp=bpy.context.object; sp.name="L8_PitbornLeftPauldronTooth"; sp.data.materials.append(bone_mat); parent_bone(sp,"clavicle_l")

# Restore pose system for export/render.
pit_rig.data.pose_position="POSE"
if pit_rig.animation_data:
    for t in pit_rig.animation_data.nla_tracks: t.mute=False
idle=bpy.data.actions.get("Armed") or bpy.data.actions.get("Idle")
if idle:
    if not pit_rig.animation_data: pit_rig.animation_data_create()
    pit_rig.animation_data.action=idle
    bpy.context.scene.frame_set(int(idle.frame_range[0]))

# Export candidate.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format="GLB",use_selection=False,
    export_animations=True,export_skins=True,export_materials="EXPORT")

# Studio render from the exact exported scene state.
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH" and not o.hide_render]
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
center=(lo+hi)*.5; H=hi.z-lo.z

world=bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world=world; world.use_nodes=True
bg=world.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value=(.08,.08,.09,1); bg.inputs["Strength"].default_value=.6
def look(o,target):
    o.rotation_euler=(target-o.location).to_track_quat("-Z","Y").to_euler()
def area(name,pos,energy,size):
    d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size
    o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=pos; look(o,center); return o
area("Key",center+Vector((2*H,-2.5*H,1.8*H)),1800,1.7*H)
area("Fill",center+Vector((-2*H,-1.2*H,1.0*H)),900,1.4*H)
area("Rim",center+Vector((0,2.4*H,1.7*H)),1500,1.3*H)
camd=bpy.data.cameras.new("Camera"); cam=bpy.data.objects.new("Camera",camd); bpy.context.collection.objects.link(cam); bpy.context.scene.camera=cam
camd.lens=58
scene=bpy.context.scene
try: scene.render.engine="BLENDER_EEVEE_NEXT"
except: scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=850; scene.render.resolution_y=1100; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"

renders=[]
for name,off in [
    ("front",Vector((0,-2.4*H,.05*H))),
    ("right",Vector((-2.4*H,0,.05*H))),
    ("back",Vector((0,2.4*H,.05*H))),
    ("left",Vector((2.4*H,0,.05*H))),
]:
    cam.location=center+off; look(cam,center+Vector((0,0,.03*H)))
    p=Path(f"/tmp/pitborn-L8-donor-{name}.png"); scene.render.filepath=str(p); bpy.ops.render.render(write_still=True); renders.append(p)
PRE.write_bytes(renders[0].read_bytes())

# Contact sheet via Pillow is unavailable in this bpy-only stage; stage the four views separately.
payload={
 "source_pitborn_sha256":sha(pit),
 "source_donor_sha256":sha(donor),
 "output_sha256":sha(OUT),
 "output_bytes":OUT.stat().st_size,
 "pitborn_bones":len(pit_rig.data.bones),
 "donor_draws":[o.name for o in donor_meshes],
 "fit_scale":scale,
 "action_count":len(bpy.data.actions),
}
REPORT.write_text(json.dumps(payload,indent=2))
print("REPORT",json.dumps(payload),flush=True)
print("STAGE_MODEL",upload(OUT),flush=True)
print("STAGE_REPORT",upload(REPORT),flush=True)
for p in renders:
    print("STAGE_PREVIEW",p.name,upload(p),flush=True)
