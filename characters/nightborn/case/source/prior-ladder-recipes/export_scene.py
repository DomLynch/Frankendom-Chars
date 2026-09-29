"""blender -b sources/LX/nightborn-LX.pre-repair.blend --python source/export_scene.py -- models/new.glb sources/LX/build.json"""
import bpy,sys,json,struct
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];p=Path(args[0]);hidden=json.loads(Path(args[1]).read_text())['hidden_originals']
bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_visible=True,export_animations=True,export_tangents=False)
data=p.read_bytes();jn=struct.unpack_from('<I',data,12)[0];model=json.loads(data[20:20+jn]);binary=data[28+jn:]
for node in model['nodes']:
 if node.get('name') in hidden and 'mesh'in node:
  node.setdefault('extras',{})['preservedInactiveMesh']=node.pop('mesh');node.pop('skin',None)
payload=json.dumps(model,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4)
p.write_bytes(struct.pack('<III',0x46546c67,2,28+len(payload)+len(binary))+struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary)
print('Exported. Next run preserve_clips.py, validate.py, format_check.cjs and fresh final renders.')
