#!/usr/bin/env python3
"""Build the Pitborn L8 blackened-steel pilot around the shipped Pitborn rig.

This is deliberately a rig-preserving armour assembly, not a new character.
Rigid plates are bone-parented with deliberate joint gaps; the source body,
weapon, armature and imported animation actions remain untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--blend", required=True)
    p.add_argument("--previews", required=True)
    p.add_argument("--report", required=True)
    return p.parse_args()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass


def import_glb(path: str):
    bpy.ops.import_scene.gltf(filepath=path, import_pack_images=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if not arms:
        raise RuntimeError("Pitborn import produced no armature")
    arm = max(arms, key=lambda o: len(o.data.bones))
    return arm


def all_mesh_bounds():
    pts = []
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        for p in o.bound_box:
            pts.append(o.matrix_world @ Vector(p))
    if not pts:
        raise RuntimeError("No mesh bounds")
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def bone_world(arm, name: str):
    b = arm.data.bones.get(name)
    if not b:
        raise RuntimeError(f"Missing protected bone {name}")
    return arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local


def mat(name, color, metallic, roughness):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def parent_to_bone(obj, arm, bone):
    world = obj.matrix_world.copy()
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["pitborn_rank"] = 8
    obj["pitborn_slot"] = bone


def bevel(obj, width, segments=3):
    mod = obj.modifiers.new("Forged bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    finally:
        obj.select_set(False)


def cube(name, center, dims, material, arm, bone, rotation=(0, 0, 0), bevel_width=None):
    bpy.ops.mesh.primitive_cube_add(location=center, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width:
        bevel(o, bevel_width)
    o.data.materials.append(material)
    parent_to_bone(o, arm, bone)
    return o


def cylinder(name, a, b, radius, material, arm, bone, vertices=20, taper=1.0):
    vec = b - a
    length = max(vec.length, 0.001)
    mid = (a + b) * 0.5
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius,
        radius2=radius * taper,
        depth=length,
        location=mid,
    )
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(vec.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    parent_to_bone(o, arm, bone)
    bevel(o, radius * 0.09, 2)
    return o


def sphere(name, center, radius, scale, material, arm, bone, subdivisions=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=center)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    parent_to_bone(o, arm, bone)
    bevel(o, radius * 0.025, 2)
    return o


def cone(name, center, radius, depth, direction, material, arm, bone, vertices=16):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=0.02 * radius, depth=depth, location=center)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    parent_to_bone(o, arm, bone)
    return o


def add_ruby(name, center, r, arm, bone, ruby):
    return sphere(name, center, r, (1.0, 0.55, 1.25), ruby, arm, bone, subdivisions=2)


def build_armour(arm):
    lo, hi = all_mesh_bounds()
    H = hi.z - lo.z
    s = H / 2.15 if H > 0 else 1.0

    steel = mat("Pitborn L8 · Blackened Steel", (0.045, 0.052, 0.058), 0.92, 0.31)
    steel2 = mat("Pitborn L8 · Hammered Edge", (0.085, 0.082, 0.078), 0.88, 0.42)
    leather = mat("Pitborn L8 · Dark Pit Leather", (0.10, 0.055, 0.032), 0.05, 0.78)
    ruby = mat("Pitborn L8 · Deep Ruby", (0.22, 0.008, 0.018), 0.02, 0.16)
    bone = mat("Pitborn L8 · Old Bone", (0.28, 0.23, 0.16), 0.0, 0.68)

    pelvis_h, _ = bone_world(arm, "pelvis")
    sp2, _ = bone_world(arm, "spine_02")
    sp3, _ = bone_world(arm, "spine_03")
    neck, _ = bone_world(arm, "neck_01")
    head, head_t = bone_world(arm, "Head")

    # Torso: three articulated plate zones, front + rear, with a leather substrate.
    torso_w = 0.68 * s
    depth = 0.16 * s
    for sign, suffix in [(-1, "Front"), (1, "Rear")]:
        yoff = sign * 0.115 * s
        cube(f"L8_{suffix}_UpperCuirass", sp3 + Vector((0, yoff, 0.01*s)),
             (torso_w, depth, 0.35*s), steel, arm, "spine_03", bevel_width=0.025*s)
        cube(f"L8_{suffix}_MidCuirass", sp2 + Vector((0, yoff, 0.00)),
             (0.61*s, depth*0.92, 0.28*s), steel2, arm, "spine_02", bevel_width=0.022*s)
        cube(f"L8_{suffix}_WaistPlate", pelvis_h + Vector((0, yoff, 0.15*s)),
             (0.56*s, depth*0.86, 0.20*s), steel, arm, "pelvis", bevel_width=0.018*s)
    # Central leather belt and heavy buckle.
    cube("L8_WarBelt", pelvis_h + Vector((0, 0, 0.13*s)), (0.61*s, 0.19*s, 0.11*s),
         leather, arm, "pelvis", bevel_width=0.018*s)
    cube("L8_BeltBuckle", pelvis_h + Vector((0, -0.115*s, 0.13*s)), (0.18*s, 0.045*s, 0.13*s),
         steel2, arm, "pelvis", bevel_width=0.014*s)
    add_ruby("L8_BuckleRuby", pelvis_h + Vector((0, -0.145*s, 0.13*s)), 0.04*s, arm, "pelvis", ruby)

    # Shoulders: broad brutal pauldrons with restrained spikes.
    for side, xsgn in [("L", 1), ("R", -1)]:
        clav = f"clavicle_{side.lower()}"
        upper = f"upperarm_{side.lower()}"
        ch, ct = bone_world(arm, clav)
        uh, ut = bone_world(arm, upper)
        c = (ch + uh) * 0.5 + Vector((xsgn*0.08*s, 0, 0.045*s))
        cube(f"L8_{side}_Pauldron", c, (0.32*s, 0.29*s, 0.20*s), steel, arm, clav,
             rotation=(0, 0, math.radians(8*xsgn)), bevel_width=0.035*s)
        # Outer tooth: arena brutality, not fantasy antlers.
        cone(f"L8_{side}_PauldronSpike", c + Vector((xsgn*0.19*s, 0, 0.025*s)),
             0.055*s, 0.24*s, Vector((xsgn, 0, 0.2)), steel2, arm, clav)
        add_ruby(f"L8_{side}_ShoulderRuby", c + Vector((0, -0.155*s, 0.02*s)), 0.032*s, arm, clav, ruby)

        # Upper arm and forearm: segmented so elbow remains free.
        uh, ut = bone_world(arm, upper)
        cylinder(f"L8_{side}_UpperArmPlate", uh.lerp(ut, 0.16), uh.lerp(ut, 0.74),
                 0.115*s, steel2, arm, upper, taper=0.83)
        low = f"lowerarm_{side.lower()}"
        lh, lt = bone_world(arm, low)
        cylinder(f"L8_{side}_Bracer", lh.lerp(lt, 0.16), lh.lerp(lt, 0.82),
                 0.105*s, steel, arm, low, taper=0.76)
        # Leather articulation ring at elbow.
        cylinder(f"L8_{side}_ElbowLeather", uh.lerp(ut, 0.80), lh.lerp(lt, 0.12),
                 0.102*s, leather, arm, low, vertices=16, taper=0.95)

    # Thighs, knees, greaves. Keep groin/knee/ankle gaps deliberate.
    for side, xsgn in [("L", 1), ("R", -1)]:
        thigh = f"thigh_{side.lower()}"
        calf = f"calf_{side.lower()}"
        th, tt = bone_world(arm, thigh)
        ch, ct = bone_world(arm, calf)
        cylinder(f"L8_{side}_ThighShell", th.lerp(tt, 0.10), th.lerp(tt, 0.66),
                 0.145*s, steel, arm, thigh, taper=0.78)
        cube(f"L8_{side}_KneeCop", tt.lerp(ch, 0.5) + Vector((0, -0.055*s, 0)),
             (0.22*s, 0.16*s, 0.18*s), steel2, arm, calf, bevel_width=0.03*s)
        cylinder(f"L8_{side}_Greave", ch.lerp(ct, 0.14), ch.lerp(ct, 0.80),
                 0.12*s, steel, arm, calf, taper=0.70)
        # Hip tasset offset outward/front/back to create a stronger silhouette.
        cube(f"L8_{side}_Tasset", th + Vector((xsgn*0.11*s, -0.07*s, -0.10*s)),
             (0.22*s, 0.12*s, 0.34*s), steel2, arm, thigh,
             rotation=(0, math.radians(8*xsgn), math.radians(5*xsgn)), bevel_width=0.022*s)

    # Closed L8 gladiator helmet: dome + forged face cage + cheeks + neck guard.
    head_c = head.lerp(head_t, 0.58)
    sphere("L8_ClosedHelmetDome", head_c + Vector((0, 0, 0.055*s)), 0.19*s,
           (1.08, 1.12, 1.22), steel, arm, "Head", subdivisions=3)
    # Front and back masks: mirrored so the proof is robust to source facing convention.
    for ysgn, label in [(-1, "Face"), (1, "Rear")]:
        y = ysgn * 0.19*s
        cube(f"L8_{label}Mask", head_c + Vector((0, y, -0.035*s)),
             (0.34*s, 0.055*s, 0.30*s), steel2, arm, "Head", bevel_width=0.018*s)
        # Horizontal brow and three narrow vertical cage bars create gladiator readability.
        cube(f"L8_{label}Brow", head_c + Vector((0, y*1.13, 0.035*s)),
             (0.38*s, 0.035*s, 0.055*s), steel, arm, "Head", bevel_width=0.01*s)
        for ix in (-0.105, 0, 0.105):
            cube(f"L8_{label}VisorBar_{ix:+.3f}", head_c + Vector((ix*s, y*1.15, -0.005*s)),
                 (0.034*s, 0.035*s, 0.18*s), steel, arm, "Head", bevel_width=0.007*s)
        add_ruby(f"L8_{label}BrowRuby", head_c + Vector((0, y*1.22, 0.075*s)), 0.028*s, arm, "Head", ruby)
    # Cheek flanges and short arena crest.
    for xsgn in (-1, 1):
        cube(f"L8_Cheek_{xsgn:+d}", head_c + Vector((xsgn*0.18*s, -0.03*s, -0.07*s)),
             (0.075*s, 0.31*s, 0.27*s), steel, arm, "Head",
             rotation=(0, math.radians(10*xsgn), 0), bevel_width=0.014*s)
    cube("L8_GladiatorCrest", head_c + Vector((0, 0, 0.225*s)),
         (0.07*s, 0.33*s, 0.13*s), steel2, arm, "Head", bevel_width=0.014*s)
    cube("L8_NeckGuard", neck + Vector((0, 0.055*s, 0.015*s)),
         (0.40*s, 0.30*s, 0.14*s), steel2, arm, "neck_01", bevel_width=0.02*s)

    # Chest ruby bosses + old-bone trophies keep Pitborn identity under elite metal.
    for x in (-0.19, 0.19):
        add_ruby(f"L8_ChestRuby_{x:+.2f}", sp3 + Vector((x*s, -0.205*s, 0.07*s)), 0.038*s, arm, "spine_03", ruby)
        cone(f"L8_BoneTrophy_{x:+.2f}", sp3 + Vector((x*s, -0.22*s, -0.10*s)),
             0.035*s, 0.15*s, Vector((0, 0, -1)), bone, arm, "spine_03")

    return {"scale_unit": s, "bounds_before": [list(lo), list(hi)]}


def set_pose(arm):
    act = bpy.data.actions.get("Armed") or bpy.data.actions.get("Idle")
    if act:
        if not arm.animation_data:
            arm.animation_data_create()
        arm.animation_data.action = act
        try:
            start = int(act.frame_range[0])
            bpy.context.scene.frame_set(start)
        except Exception:
            bpy.context.scene.frame_set(1)


def target_camera(cam, target):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_views(arm, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    set_pose(arm)
    lo, hi = all_mesh_bounds()
    c = (lo + hi) * 0.5
    H = hi.z - lo.z
    maxspan = max(hi.x-lo.x, hi.y-lo.y, H)

    # Ground.
    bpy.ops.mesh.primitive_plane_add(size=maxspan*4, location=(c.x, c.y, lo.z-0.015*H))
    ground = bpy.context.object
    ground.name = "ReviewGround"
    gm = mat("Review ground", (0.08,0.075,0.065), 0.0, 0.92)
    ground.data.materials.append(gm)

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.035,0.035,0.04,1)
    bg.inputs["Strength"].default_value = 0.38

    # Lights.
    def area(name, loc, energy, size):
        data=bpy.data.lights.new(name, "AREA"); data.energy=energy; data.shape="DISK"; data.size=size
        o=bpy.data.objects.new(name, data); bpy.context.collection.objects.link(o); o.location=loc; target_camera(o,c); return o
    area("Key", c+Vector((2.5*H,-3.0*H,2.0*H)), 1700, 2.2*H)
    area("Fill", c+Vector((-2.2*H,-1.2*H,1.3*H)), 900, 1.8*H)
    area("Rim", c+Vector((0,2.7*H,2.2*H)), 1500, 1.5*H)

    cam_data=bpy.data.cameras.new("ReviewCamera"); cam=bpy.data.objects.new("ReviewCamera",cam_data)
    bpy.context.collection.objects.link(cam); bpy.context.scene.camera=cam
    cam_data.lens=62

    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=768; scene.render.resolution_y=768; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False

    views={
      "front": Vector((0,-2.45*H,0.10*H)),
      "back": Vector((0, 2.45*H,0.10*H)),
      "left": Vector((2.45*H,0,0.10*H)),
      "right": Vector((-2.45*H,0,0.10*H)),
    }
    for name,offset in views.items():
        cam.location=c+offset
        target_camera(cam,c+Vector((0,0,0.04*H)))
        scene.render.filepath=str(out_dir/f"L8-{name}.png")
        bpy.ops.render.render(write_still=True)

    # Head closeup from both likely front conventions; reviewer can immediately see orientation.
    head, head_t=bone_world(arm,"Head"); hc=head.lerp(head_t,.55)
    for name,ysgn in [("head-a",-1),("head-b",1)]:
        cam.location=hc+Vector((0,ysgn*0.75*H,0.08*H))
        target_camera(cam,hc)
        cam_data.lens=78
        scene.render.filepath=str(out_dir/f"L8-{name}.png")
        bpy.ops.render.render(write_still=True)


def export_glb(out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    kwargs = dict(filepath=str(out), export_format="GLB", export_animations=True, export_skins=True)
    try:
        bpy.ops.export_scene.gltf(**kwargs, export_animation_mode="ACTIONS", export_force_sampling=False)
    except TypeError:
        bpy.ops.export_scene.gltf(**kwargs)


def main():
    a=parse_args()
    source=Path(a.source); out=Path(a.out); blend=Path(a.blend); previews=Path(a.previews); report=Path(a.report)
    reset_scene()
    arm=import_glb(str(source))
    source_actions=sorted(x.name for x in bpy.data.actions)
    if len(arm.data.bones) != 65:
        raise RuntimeError(f"Expected 65 Pitborn bones, got {len(arm.data.bones)}")
    meta=build_armour(arm)
    set_pose(arm)
    blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    render_views(arm, previews)
    # Do not export review-only floor/lights/camera.
    for o in list(bpy.context.scene.objects):
        if o.name=="ReviewGround" or o.type in {"LIGHT","CAMERA"}:
            bpy.data.objects.remove(o, do_unlink=True)
    export_glb(out)
    payload={
      "source":str(source),"source_sha256":sha256(source),
      "output":str(out),"output_sha256":sha256(out),"output_bytes":out.stat().st_size,
      "armature":arm.name,"bones":len(arm.data.bones),
      "source_actions":source_actions,
      "new_objects":sorted(o.name for o in bpy.context.scene.objects if o.get("pitborn_rank")==8),
      **meta,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload))


if __name__=="__main__":
    main()
