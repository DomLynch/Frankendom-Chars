import bpy, math, os, json, hashlib
from mathutils import Vector

SRC="/tmp/pitborn.glb"
OUT="characters/pitborn/models/pitborn-L8.glb"
PRE="characters/pitborn/previews"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
os.makedirs(PRE, exist_ok=True)

# Clean and import the immutable shipped Pitborn.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
armatures=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"]
if not armatures:
    raise RuntimeError("Pitborn import has no armature")
arm=armatures[0]

# Keep a record of the imported animation contract before adding armour.
source_actions=sorted({a.name for a in bpy.data.actions})
source_bones=[b.name for b in arm.data.bones]

def mat(name, color, metallic=0.0, rough=0.5):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*color,1)
    bsdf.inputs["Metallic"].default_value=metallic
    bsdf.inputs["Roughness"].default_value=rough
    return m

STEEL=mat("Pitborn L8 Blackened Steel",(0.022,0.028,0.032),0.92,0.27)
EDGE=mat("Pitborn L8 Worn Iron Edge",(0.10,0.085,0.065),0.82,0.40)
RUBY=mat("Pitborn L8 Ruby",(0.23,0.004,0.012),0.28,0.16)
DARK=mat("Pitborn L8 Visor",(0.004,0.005,0.006),0.15,0.18)
LEATHER=mat("Pitborn L8 Leather",(0.075,0.038,0.018),0.0,0.72)

# Geometry bounds -> scale independent of the source's absolute units.
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
pts=[]
for o in meshes:
    for c in o.bound_box:
        pts.append(o.matrix_world @ Vector(c))
lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
H=max(hi.z-lo.z,1e-6)
S=H/2.18

def find_bone(*candidates):
    lower={b.name.lower():b.name for b in arm.data.bones}
    for c in candidates:
        if c.lower() in lower: return lower[c.lower()]
    for c in candidates:
        cc=c.lower()
        for b in arm.data.bones:
            if cc in b.name.lower(): return b.name
    return None

def bone_segment(name):
    b=arm.data.bones[name]
    return arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local

def parent_bone(obj,bone):
    mw=obj.matrix_world.copy()
    obj.parent=arm
    obj.parent_type="BONE"
    obj.parent_bone=bone
    obj.matrix_world=mw

def bevel(obj, amount):
    mod=obj.modifiers.new("forged bevel","BEVEL")
    mod.width=amount
    mod.segments=2
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    try: bpy.ops.object.modifier_apply(modifier=mod.name)
    except: pass
    obj.select_set(False)

def add_box(name,loc,dims,material,bone=None,rot=(0,0,0),bev=0.018):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev: bevel(o,bev*S)
    o.data.materials.append(material)
    if bone: parent_bone(o,bone)
    return o

def add_uv(name,loc,scale,material,bone=None,seg=24,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    if bone: parent_bone(o,bone)
    return o

def add_segment(name,bone,radius,material,scale_xy=(1,1),trim=0.84):
    a,b=bone_segment(bone); v=b-a; L=v.length
    if L<1e-4: return None
    mid=(a+b)/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius*S, depth=L*trim, location=mid)
    o=bpy.context.object; o.name=name
    o.rotation_mode="QUATERNION"
    o.rotation_quaternion=Vector((0,0,1)).rotation_difference(v.normalized())
    o.scale.x*=scale_xy[0]; o.scale.y*=scale_xy[1]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel(o,0.012*S)
    o.data.materials.append(material); parent_bone(o,bone)
    return o

def gem(name,loc,bone=None,size=0.035):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=size*S,location=loc)
    o=bpy.context.object; o.name=name; o.scale=(0.65,0.35,1.25)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(RUBY)
    if bone: parent_bone(o,bone)
    return o

head=find_bone("Head")
neck=find_bone("neck_01","neck")
chest=find_bone("spine_03","chest")
mid=find_bone("spine_02","spine")
pelvis=find_bone("pelvis","hips")
if not all([head,chest,mid,pelvis]):
    raise RuntimeError("Missing core Pitborn bones: "+repr((head,chest,mid,pelvis)))

hc=sum(bone_segment(head),Vector())/2
cc=sum(bone_segment(chest),Vector())/2
mc=sum(bone_segment(mid),Vector())/2
pc=sum(bone_segment(pelvis),Vector())/2

# Brutal L8 torso: layered forged plates rather than knight-clean plate.
add_box("L8_Breastplate",cc,(0.76*S,0.36*S,0.48*S),STEEL,chest,bev=.025)
add_box("L8_AbPlate",mc,(0.63*S,0.32*S,0.30*S),STEEL,mid,bev=.022)
add_box("L8_WarBelt",pc+Vector((0,0,0.10*S)),(0.68*S,0.38*S,0.12*S),EDGE,pelvis,bev=.016)
gem("L8_ChestRuby",cc+Vector((0,-0.205*S,0.05*S)),chest,.045)

# Layered skirt/thigh apron.
for x in (-0.23,0,0.23):
    add_box(f"L8_Skirt_{x:+.2f}",pc+Vector((x*S,-0.03*S,-0.24*S)),
            (0.22*S,0.24*S,0.38*S),STEEL,pelvis,rot=(math.radians(4),0,math.radians(-x*10)),bev=.018)

# Arms and shoulders.
for side in ("l","r"):
    ua=find_bone(f"upperarm_{side}",f"upper_arm_{side}",f"arm_{side}")
    fa=find_bone(f"lowerarm_{side}",f"forearm_{side}",f"lower_arm_{side}")
    hand=find_bone(f"hand_{side}")
    if ua:
        a,_=bone_segment(ua)
        add_uv(f"L8_Pauldron_{side}",a,(0.19*S,0.23*S,0.17*S),STEEL,ua)
        add_segment(f"L8_UpperArm_{side}",ua,.105,STEEL,(1.0,.86),.72)
        gem(f"L8_ShoulderRuby_{side}",a+Vector((0,-0.12*S,0.02*S)),ua,.028)
    if fa: add_segment(f"L8_Vambrace_{side}",fa,.092,STEEL,(1.0,.80),.82)
    if hand:
        h0,h1=bone_segment(hand)
        add_box(f"L8_Gauntlet_{side}",(h0+h1)/2,(0.16*S,0.11*S,0.16*S),EDGE,hand,bev=.014)

# Legs: full thigh + shin coverage.
for side in ("l","r"):
    thigh=find_bone(f"thigh_{side}",f"upleg_{side}",f"upperleg_{side}")
    calf=find_bone(f"calf_{side}",f"shin_{side}",f"lowerleg_{side}")
    foot=find_bone(f"foot_{side}")
    if thigh: add_segment(f"L8_ThighPlate_{side}",thigh,.145,STEEL,(1.0,.78),.78)
    if calf: add_segment(f"L8_Greave_{side}",calf,.125,STEEL,(1.0,.72),.84)
    if foot:
        f0,f1=bone_segment(foot)
        add_box(f"L8_Sabatons_{side}",(f0+f1)/2,(0.20*S,0.32*S,0.13*S),EDGE,foot,bev=.014)

# Closed gladiator helmet. Full dome + brutal visor band + cheek blocks + short crown spikes.
helmet=add_uv("L8_ClosedGladiatorHelmet",hc,(0.205*S,0.18*S,0.235*S),STEEL,head,seg=32,rings=20)
# Dark visor ring reads from either front orientation.
add_box("L8_VisorBand",hc+Vector((0,0,0.025*S)),(0.37*S,0.385*S,0.055*S),DARK,head,bev=.006)
add_box("L8_BrowBlade",hc+Vector((0,0,0.09*S)),(0.40*S,0.37*S,0.045*S),EDGE,head,bev=.006)
gem("L8_HelmRuby",hc+Vector((0,-0.195*S,0.11*S)),head,.032)
for i,x in enumerate((-0.11,0,0.11)):
    bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.035*S,radius2=0,depth=.16*S,
                                    location=hc+Vector((x*S,0,0.29*S+(0.035*S if i==1 else 0))))
    o=bpy.context.object; o.name=f"L8_HelmSpike_{i}"; o.data.materials.append(EDGE); parent_bone(o,head)

# A few crude leather bindings to keep the pit-fighter identity.
add_box("L8_ChestStrap",cc+Vector((0,0,0.01*S)),(.10*S,.39*S,.58*S),LEATHER,chest,rot=(0,math.radians(18),math.radians(28)),bev=.008)
add_box("L8_BeltStrap",pc+Vector((0,0,.08*S)),(.74*S,.40*S,.055*S),LEATHER,pelvis,bev=.008)

# Mark authored objects for audit.
for o in bpy.context.scene.objects:
    if o.name.startswith("L8_"): o["frankendom_rank"]=8

# Export actual pilot GLB with animations.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=OUT,export_format="GLB",use_selection=False,
    export_animations=True,export_skins=True,export_morph=True,export_materials="EXPORT")

# Render four neutral views from the actual assembled scene.
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE_NEXT" if hasattr(bpy.types,"EEVEE_NEXT") else "BLENDER_EEVEE"
scene.render.resolution_x=900; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.world.color=(0.075,0.075,0.075)
# Ground
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,lo.z-.02*S))
ground=bpy.context.object; ground.data.materials.append(mat("Preview Ground",(0.12,0.12,0.12),0,.95))
# Lights
for loc,energy,size in [((3,-4,6),1500,4),((-3,-2,4),900,3),((0,4,5),1100,3)]:
    data=bpy.data.lights.new("PreviewArea","AREA"); data.energy=energy; data.shape="DISK"; data.size=size
    obj=bpy.data.objects.new("PreviewArea",data); scene.collection.objects.link(obj); obj.location=loc
# Camera
camd=bpy.data.cameras.new("PreviewCamera"); cam=bpy.data.objects.new("PreviewCamera",camd); scene.collection.objects.link(cam); scene.camera=cam
target=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z+H*.52))
R=max(H*1.55,4.2*S)
def look(cam,pos,target):
    cam.location=pos
    cam.rotation_euler=(target-pos).to_track_quat("-Z","Y").to_euler()
    camd.lens=58
for label,vec in [("front",(0,-1,0)),("back",(0,1,0)),("left",(-1,0,0)),("right",(1,0,0))]:
    pos=target+Vector(vec)*R+Vector((0,0,H*.03))
    look(cam,pos,target)
    scene.render.filepath=os.path.join(PRE,f"L8-{label}.png")
    bpy.ops.render.render(write_still=True)

# Receipt.
data=open(OUT,"rb").read()
receipt={
 "rank":8,
 "model":"pitborn-L8.glb",
 "bytes":len(data),
 "sha256":hashlib.sha256(data).hexdigest(),
 "source_actions":source_actions,
 "source_bones":len(source_bones),
 "armour_objects":sorted(o.name for o in bpy.context.scene.objects if o.name.startswith("L8_")),
}
open("characters/pitborn/L8-receipt.json","w").write(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(receipt))
