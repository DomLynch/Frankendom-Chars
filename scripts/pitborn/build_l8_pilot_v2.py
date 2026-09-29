from pathlib import Path
src=Path(__file__).with_name("build_l8_fixed_impl.py").read_text()
exec(compile(src,"build_l8_fixed_impl.py","exec"))
