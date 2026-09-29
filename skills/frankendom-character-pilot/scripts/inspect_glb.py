"""Read-only GLB inventory; does not certify topology or appearance."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

def inspect(path):
    b=path.read_bytes()
    magic,version,total=struct.unpack_from('<III',b)
    if magic!=0x46546C67 or version!=2 or total!=len(b):
        raise ValueError('Invalid GLB header or length')
    length,kind=struct.unpack_from('<II',b,12)
    if kind!=0x4E4F534A: raise ValueError('First chunk is not JSON')
    d=json.loads(b[20:20+length]); rows=[]
    for node in d.get('nodes',[]):
        if 'mesh' not in node: continue
        primitives=d['meshes'][node['mesh']]['primitives']; triangles=0
        for p in primitives:
            if p.get('mode',4)!=4: raise ValueError('Non-triangle primitive; count not supported')
            a=d['accessors'][p['indices'] if 'indices' in p else p['attributes']['POSITION']]
            if a['count']%3: raise ValueError('Triangle count not divisible by three')
            triangles+=a['count']//3
        rows.append({'name':node.get('name','unnamed'),'triangles':triangles,'primitives':len(primitives)})
    return {'path':str(path.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'MiB':round(len(b)/1048576,2),'triangles':sum(r['triangles']for r in rows),'meshInstances':len(rows),'basePassPrimitives':sum(r['primitives']for r in rows),'pieces':rows,'imageFormats':[i.get('mimeType','external/unspecified')for i in d.get('images',[])],'extensionsRequired':d.get('extensionsRequired',[]),'scope':'Inventory only; no topology, collision, rigging or performance certification'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('glb',type=Path)
    print(json.dumps(inspect(parser.parse_args().glb),indent=2))
