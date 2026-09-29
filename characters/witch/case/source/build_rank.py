"""Run the reviewed Witch sequence locally or in a bounded CPU job."""

from pathlib import Path
import subprocess
import sys
import os

rank = int(sys.argv[1])
label = f"L{rank}"
R = Path.cwd()
py = sys.executable
bl = os.environ.get("WITCH_BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
assert (R / f"src/assets/source/creatures/witch-{label}-donor.glb").exists()


def run(cmd, log):
    with (R / "checks" / log).open("w") as f:
        subprocess.run(cmd, check=True, stdout=f, stderr=subprocess.STDOUT)


def blender(script, extra=[]):
    return (
        [py, script] + extra
        if bl == "bpy"
        else [bl, "-b", "-t", "2", "--python", script] + extra
    )


for name in ["build_pilot", "reweight_pilot"]:
    s = (R / f"source/{name}.py").read_text().replace("L8", label)
    if rank <= 3 and name == "build_pilot":
        s = s.replace(
            "assert all(before[o.name]==sig(o) for o in original)",
            "for mat in donor.data.materials:\n for node in mat.node_tree.nodes:\n  if node.type=='BSDF_PRINCIPLED':\n   for link in list(node.inputs['Metallic'].links):mat.node_tree.links.remove(link)\n   node.inputs['Metallic'].default_value=0\nassert all(before[o.name]==sig(o) for o in original)",
        )
    target = R / f"source/{name}-{label}.py"
    target.write_text(s)
    run(blender(str(target)), f"{name}-{label}.log")
run(
    [
        py,
        "source/pack_preserved.py",
        "source/original.glb",
        f"source/pilot/witch-{label}-v2.glb",
        f"models/witch-{label}-packed.glb",
    ],
    f"{label}-pack.log",
)
run(
    [
        py,
        "source/smooth_weights.py",
        f"models/witch-{label}-packed.glb",
        f"models/witch-{label}-smooth.glb",
        "100",
    ],
    f"{label}-smooth.log",
)
run(
    [
        py,
        "source/align_grip.py",
        f"models/witch-{label}-smooth.glb",
        f"models/witch-{label}.glb",
    ],
    f"{label}-grip.log",
)
run(
    [
        py,
        "source/articulate_hands.py",
        f"models/witch-{label}.glb",
        f"models/witch-{label}.glb",
    ],
    f"{label}-fingers.log",
)
if rank <= 7:
    run(
        [
            py,
            "source/preserve_face.py",
            f"models/witch-{label}.glb",
            f"models/witch-{label}.glb",
        ],
        f"{label}-face.log",
    )
    run(
        [
            py,
            "source/close_cowl.py",
            f"models/witch-{label}.glb",
            f"models/witch-{label}.glb",
        ],
        f"{label}-cowl.log",
    )
if rank == 8:
    run(
        [
            py,
            "source/finish_palette.py",
            f"models/witch-{label}.glb",
            f"models/witch-{label}.glb",
        ],
        f"{label}-palette.log",
    )
run(
    [py, "source/check_candidate.py", f"models/witch-{label}.glb"], f"{label}-check.log"
)
if os.environ.get("WITCH_SKIP_RENDER") != "1":
    run(blender("source/render_candidate.py", ["--", label]), f"{label}-render.log")
print("RANK_BUILT", rank, flush=True)
