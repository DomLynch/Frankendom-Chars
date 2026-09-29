#!/usr/bin/env python3
import argparse, math
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser()
ap.add_argument("--model",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
out=Path(a.out); out.mkdir(parents=True,exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.model)

meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if not meshes: raise RuntimeError("TRELLIS donor contains no mesh")
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
c=(lo+hi)*0.5
H=max(hi.z-lo.z,1e-4)
span=max(hi.x-lo.x,hi.y-lo.y,H)

# Ground and neutral studio.
bpy.ops.mesh.primitive_plane_add(size=span*5,location=(c.x,c.y,lo.z-.008*H))
g=bpy.context.object
m=bpy.data.materials.new("Preview ground"); m.diffuse_color=(.22,.22,.22,1); m.use_nodes=True
bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(.22,.22,.22,1); bs.inputs["Roughness"].default_value=.95
g.data.materials.append(m)
world=bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world=world; world.use_nodes=True
bg=world.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value=(.09,.09,.09,1); bg.inputs["Strength"].default_value=.55

def point(obj,target):
    obj.rotation_euler=(target-obj.location).to_track_quat("-Z","Y").to_euler()
def light(name,loc,energy,size):
    d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size
    o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=loc; point(o,c); return o

light("Key",c+Vector((2.0*H,-2.8*H,1.7*H)),1900,1.5*H)
light("Fill",c+Vector((-2.2*H,-1.0*H,1.1*H)),900,1.5*H)
light("Rim",c+Vector((0,2.6*H,1.8*H)),1600,1.3*H)

cd=bpy.data.cameras.new("Camera"); cam=bpy.data.objects.new("Camera",cd); bpy.context.collection.objects.link(cam); bpy.context.scene.camera=cam
cd.lens=58
scene=bpy.context.scene
try: scene.render.engine="BLENDER_EEVEE_NEXT"
except: scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=900; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
target=c+Vector((0,0,.03*H))
R=2.35*H

views={"front":Vector((0,-R,.05*H)),"back":Vector((0,R,.05*H)),"left":Vector((R,0,.05*H)),"right":Vector((-R,0,.05*H))}
for name,off in views.items():
    cam.location=c+off; point(cam,target); scene.render.filepath=str(out/f"L8-donor-{name}.png"); bpy.ops.render.render(write_still=True)

# Two closer three-quarter views make reconstruction defects obvious.
for name,off in {
    "hero-a":Vector((1.25*R,-1.8*R,.10*H)),
    "hero-b":Vector((-1.25*R,-1.8*R,.10*H)),
}.items():
    cam.location=c+off*.65; point(cam,target); cd.lens=70; scene.render.filepath=str(out/f"L8-donor-{name}.png"); bpy.ops.render.render(write_still=True)
