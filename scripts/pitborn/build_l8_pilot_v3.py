from pathlib import Path

src = Path(__file__).with_name("build_l8_pilot_v2.py").read_text()
src = src.replace('scene.render.engine = "BLENDER_EEVEE_NEXT"', 'scene.render.engine = "BLENDER_EEVEE"')
exec(compile(src, "build_l8_pilot_v2.py", "exec"))
