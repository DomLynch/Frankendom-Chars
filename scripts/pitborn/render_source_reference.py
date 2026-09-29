#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser()
ap.add_argument("--source",required=True)
ap.add_argument("--out",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.source, import_pack_images=True)
arm=max((o for o in bpy.context.scene.objects if o.type=="ARMATURE"), key=lambda o: len(o.data.bones))

# Use the shipped Armed pose to preserve Pitborn's authored hunch/body read.
act=bpy.data.actions.get("Armed") or bpy.data.actions.get("Idle")
if act:
    arm.animation_data_create()
    arm.animation_data.action=act
    bpy.context.scene.frame_set(int(act.frame_range[0]))

# Remove weapon only from the reference image, never from source data.
for o in bpy.context.scene.objects:
    n=o.name.lower()
    if any(k in n for k in ["weapondrawn","sworddrawn","swordsheathed","cleaver"]):
        o.hide_render=True

# Bounds from visible meshes only.
pts=[]
for o in bpy.context.scene.objects:
    if o.type!="MESH" or o.hide_render: continue
    for p in o.bound_box:
        pts.append(o.matrix_world @ Vector(p))
lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
c=(lo+hi)/2
H=hi.z-lo.z

# Neutral studio.
world=bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world=world
world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value=(0.70,0.70,0.70,1)
bg.inputs["Strength"].default_value=0.55

def target(obj,pt):
    obj.rotation_euler=(Vector(pt)-obj.location).to_track_quat("-Z","Y").to_euler()

def area(name,loc,energy,size):
    d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size
    o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=loc; target(o,c); return o

area("Key",c+Vector((2.2*H,-3.2*H,2.0*H)),1800,2.1*H)
area("Fill",c+Vector((-2.0*H,-1.8*H,1.1*H)),900,1.8*H)
area("Rim",c+Vector((0.5*H,2.4*H,2.2*H)),1300,1.5*H)

camd=bpy.data.cameras.new("Camera"); cam=bpy.data.objects.new("Camera",camd)
bpy.context.collection.objects.link(cam); bpy.context.scene.camera=cam
camd.lens=70
# Slight three-quarter while keeping the whole body readable.
cam.location=c+Vector((0.55*H,-2.55*H,0.12*H))
target(cam,c+Vector((0,0,0.03*H)))

sc=bpy.context.scene
sc.render.engine="BLENDER_EEVEE"
sc.render.resolution_x=1024; sc.render.resolution_y=1024; sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.render.film_transparent=False
Path(a.out).parent.mkdir(parents=True,exist_ok=True)
sc.render.filepath=a.out
bpy.ops.render.render(write_still=True)

p=Path(a.out)
rec={"source":a.source,"source_sha256":hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),
     "output":a.out,"output_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size,
     "armature":arm.name,"bones":len(arm.data.bones),"action":act.name if act else None,
     "bounds":[list(lo),list(hi)]}
Path(a.report).parent.mkdir(parents=True,exist_ok=True)
Path(a.report).write_text(json.dumps(rec,indent=2)+"\n")
print(json.dumps(rec))
