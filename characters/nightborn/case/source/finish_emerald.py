"""Reconcile L9 body/helmet tint with authored arms; preserve every binary geometry/clip byte."""
from pathlib import Path
import sys,json,struct,hashlib
from glb_checks import read
src=Path(sys.argv[1]);dest=Path(sys.argv[2]);m,b=read(src);before=hashlib.sha256(b).hexdigest();changed={}
selected=set()
for n in m['nodes']:
 if n.get('name') in ['L9_Armour','L9_ClosedHelmet']:
  for pr in m['meshes'][n['mesh']]['primitives']:
   mi=pr['material'];mat=m['materials'][mi];p=mat.get('pbrMetallicRoughness',{})
   if 'baseColorTexture' in p:selected.add(mi)
for i,mat in enumerate(m['materials']):
 p=mat.setdefault('pbrMetallicRoughness',{});name=mat.get('name','')
 if i in selected:p['baseColorFactor']=[.22,.95,.34,1];changed[name]=p['baseColorFactor']
 if name=='L9 articulated armour metal':p['baseColorFactor']=[.022,.045,.028,1];p['roughnessFactor']=.45;changed[name]=p['baseColorFactor']
 if name=='L9 worn plate edges':p['baseColorFactor']=[.05,.085,.065,1];p['roughnessFactor']=.38;changed[name]=p['baseColorFactor']
assert len(selected)==2
j=json.dumps(m,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4);data=struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);assert hashlib.sha256(read(dest)[1]).hexdigest()==before
print(json.dumps({'source':str(src),'output':str(dest),'binaryPayloadUnchanged':True,'materials':changed,'sha256':hashlib.sha256(data).hexdigest()},indent=2))
