"""Rebuild one selected GLB from its saved Blender addon, preserving source animations byte-for-byte."""
from pathlib import Path
import sys,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
rank=sys.argv[1];out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'sources'/rank/'post-export'))
from merge_armour import merge
from repair_weights import repair
from finish_materials import finish
from final_polish import polish
from clean_visible_skin import clean
merge(ROOT/'models/dwarf-L1.glb',ROOT/'sources'/rank/'addon.glb',out)
repair(out);finish(out);polish(out);clean(out)
expected=json.loads((ROOT/'selected.json').read_text())[rank]['sha256'];actual=hashlib.sha256(out.read_bytes()).hexdigest();assert actual==expected,(rank,expected,actual)
print('EXACT_REBUILD',rank,actual)
