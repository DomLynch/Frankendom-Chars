"""Stage one L1 build using the existing, preserved-rig rank pipeline."""

from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[3]
work = root / "work/pitborn-l1-20260930"
source = work / "source"
source.mkdir(parents=True, exist_ok=True)
helpers = root / "scripts/pitborn/ranks_20260929"
for name in [
    "reconstruct.py",
    "fit_rank.py",
    "pack_preserved.py",
    "motion_math.py",
    "smooth_weights.py",
    "tether_fragments.py",
    "preserve_face.py",
    "repair_collar.py",
    "check_candidate.py",
    "render_rank.py",
]:
    text = (helpers / name).read_text()
    text = text.replace(
        "Domlynch/frankendom-pitborn-ranks-20260929",
        "Domlynch/frankendom-pitborn-l1-20260930",
    )
    if name == "render_rank.py":
        marker = (
            'rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")'
        )
        text = text.replace(
            marker,
            """bpy.context.scene["authoritative_glb_sha256"] = model_hash
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(Path("source/pitborn-L1-final.blend").resolve()))
"""
            + marker,
        )
    (source / name).write_text(text)
shutil.copy2(
    root / "work/pitborn-20260929/delivery/source/pitborn.glb", source / "pitborn.glb"
)
shutil.copy2(Path(__file__).with_name("job.py"), source / "job.py")
