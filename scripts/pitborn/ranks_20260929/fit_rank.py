"""L8 surface pilot: donor A pose fitted to the original Pitborn bind rig."""

import json
import os
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

rank = os.environ.get("RANK", "L8")
root = Path.cwd()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root / "source/pitborn.glb"))
original = list(bpy.context.scene.objects)
rig = next(o for o in original if o.type == "ARMATURE")
if rig.animation_data:
    rig.animation_data.action = None
    for track in rig.animation_data.nla_tracks:
        track.mute = True
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
rig.data.pose_position = "REST"
bpy.context.view_layer.update()
body = next(o for o in original if o.type == "MESH" and o.name == "Skin")
points = [body.matrix_world @ v.co for v in body.data.vertices]
body.data.calc_loop_triangles()
faces = [tuple(t.vertices) for t in body.data.loop_triangles]
bvh = BVHTree.FromPolygons(points, faces, all_triangles=True)
groups = {g.index: g.name for g in body.vertex_groups}
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(root / f"donors/{rank}.glb"))
donors = [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in donors:
    o.select_set(True)
bpy.context.view_layer.objects.active = donors[0]
bpy.ops.object.join()
donor = bpy.context.object
donor.name = f"Pitborn_{rank}_Armour"
positions = np.array([list(donor.matrix_world @ v.co) for v in donor.data.vertices])
lo, hi = positions.min(0), positions.max(0)
height = hi[2] - lo[2]
normalized = positions / height
normalized[:, 2] -= lo[2] / height
normalized[:, 0] -= (hi[0] + lo[0]) / (2 * height)
normalized[:, 1] -= (hi[1] + lo[1]) / (2 * height)


def joint(name):
    return rig.matrix_world @ rig.data.bones[name].head_local


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def segment_transform(p, start, end, target_start, target_end):
    axis = end - start
    target_axis = target_end - target_start
    t = min(1.0, max(0.0, (p - start).dot(axis) / axis.length_squared))
    nearest = start + axis * t
    rotation = axis.rotation_difference(target_axis)
    cross = rotation @ (p - nearest)
    return target_start + target_axis * t + cross * 1.8, (p - nearest).length


mapped = []
for pos in normalized:
    x, y, z = pos
    side = "l" if x >= 0 else "r"
    sign = 1 if x >= 0 else -1
    # Measured reference landmarks, normalized to donor height; initial fit only.
    zz = float(
        np.interp(
            z,
            [0, 0.10, 0.32, 0.49, 0.63, 0.79, 0.85, 0.94, 1],
            [0, 0.13, 0.62, 1.065, 1.32, 1.62, 1.72, 1.94, 2.06],
        )
    )
    width = float(
        np.interp(
            z,
            [0, 0.32, 0.49, 0.63, 0.79, 0.85, 1],
            [1.7, 1.35, 1.5, 1.55, 1.55, 1.9, 1.9],
        )
    )
    target = Vector((x * width, y * 1.8, zz))
    if z < 0.49:
        # Keep the original narrow leg stance while leaving armour thickness.
        centre = float(np.interp(z, [0, 0.10, 0.32, 0.49], [0.17, 0.15, 0.115, 0.10]))
        leg_x = x * 1.8 + (0.116 - centre * 1.8) * float(np.tanh(x / 0.06))
        blend = 1 - smooth(0.43, 0.49, z)
        target.x = target.x * (1 - blend) + leg_x * blend
    if 0.38 < z < 0.88:
        d = [
            Vector((sign * 0.18, 0, 0.79)),
            Vector((sign * 0.275, 0, 0.66)),
            Vector((sign * 0.355, 0, 0.535)),
            Vector((sign * 0.39, 0, 0.47)),
        ]
        s = [
            joint("upperarm_" + side),
            joint("lowerarm_" + side),
            joint("hand_" + side),
        ]
        s.append(s[-1] + (s[-1] - s[-2]).normalized() * 0.15)
        transformed = [
            segment_transform(Vector(pos), d[i], d[i + 1], s[i], s[i + 1])
            for i in range(3)
        ]
        # Continuous weighting between adjacent segment transforms avoids elbow seams.
        distances = np.array([item[1] for item in transformed])
        factors = np.exp(-(distances - distances.min()) * 90)
        arm = sum(
            (v * float(w) for (v, _), w in zip(transformed, factors)), Vector()
        ) / float(factors.sum())
        boundary = float(
            np.interp(
                z, [0.38, 0.55, 0.64, 0.72, 0.84], [0.29, 0.25, 0.205, 0.165, 0.13]
            )
        )
        blend = smooth(boundary, boundary + 0.045, abs(x)) * (1 - smooth(0.83, 0.88, z))
        target = target.lerp(arm, blend)
    mapped.append(target)
for vertex, position in zip(donor.data.vertices, mapped):
    vertex.co = position
donor.matrix_world.identity()
donor.data.update()
donor.data.normals_split_custom_set([(0, 0, 0)] * len(donor.data.loops))
for name in groups.values():
    donor.vertex_groups.new(name=name)


def weights_at(point):
    hit = bvh.find_nearest(point)
    ids = faces[hit[2]]
    a, b, c = [points[i] for i in ids]
    e0, e1, e2 = b - a, c - a, hit[0] - a
    d00, d01, d11, d20, d21 = e0.dot(e0), e0.dot(e1), e1.dot(e1), e2.dot(e0), e2.dot(e1)
    den = d00 * d11 - d01 * d01
    u = (d11 * d20 - d01 * d21) / den if abs(den) > 1e-12 else 0
    v = (d00 * d21 - d01 * d20) / den if abs(den) > 1e-12 else 0
    weights = {}
    for index, factor in zip(ids, [max(0, 1 - u - v), max(0, u), max(0, v)]):
        for group in body.data.vertices[index].groups:
            name = groups[group.group]
            weights[name] = weights.get(name, 0) + factor * group.weight
    return weights


for vertex in donor.data.vertices:
    weights = weights_at(vertex.co)
    if vertex.co.z > 1.72 and abs(vertex.co.x) < 0.23:
        head = smooth(1.72, 1.80, vertex.co.z)
        weights = {"Head": head, "neck_01": 1 - head}
    best = sorted(
        ((n, w) for n, w in weights.items() if w > 1e-7),
        key=lambda item: item[1],
        reverse=True,
    )[:4]
    total = sum(w for _, w in best)
    assert total > 0
    for name, weight in best:
        donor.vertex_groups[name].add([vertex.index], weight / total, "REPLACE")
modifier = donor.modifiers.new("Original Pitborn rig", "ARMATURE")
modifier.object = rig
world = donor.matrix_world.copy()
donor.parent = rig
donor.matrix_world = world
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
donor.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(root / f"source/pitborn-{rank}-fit.blend"))
bpy.ops.export_scene.gltf(
    filepath=str(root / f"source/{rank}-fitted.glb"),
    export_format="GLB",
    use_selection=True,
    export_animations=False,
    export_tangents=False,
)
(root / f"checks/{rank}-fit.json").write_text(
    json.dumps(
        {
            "donor_bounds": [lo.tolist(), hi.tolist()],
            "original_joints": len(rig.data.bones),
            "vertices": len(mapped),
            "status": "unreviewed surface fit; packing and pose validation required",
        },
        indent=2,
    )
)
