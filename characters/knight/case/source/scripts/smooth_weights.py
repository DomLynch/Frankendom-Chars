"""Smooth demonstrated discontinuities on the NEW armour mesh, preserving original bytes."""
import sys,json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix,diags
from pack_preserved import read,arr,write
src,dst=sys.argv[1:3];iterations=int(sys.argv[3]) if len(sys.argv)>3 else 80;g,b=read(src);binary=bytearray(b)
node=next(n for n in g['nodes'] if n.get('name')=='Knight_L8_Armour');prim=g['meshes'][node['mesh']]['primitives'][0];attrs=prim['attributes']
p=arr(g,b,attrs['POSITION']);j=arr(g,b,attrs['JOINTS_0']);w=arr(g,b,attrs['WEIGHTS_0']);tri=arr(g,b,prim['indices']).reshape(-1,3)
_,inv=np.unique(np.round(p,5),axis=0,return_inverse=True);n=inv.max()+1;nb=len(g['skins'][0]['joints'])
dense=np.zeros((len(p),nb),np.float32)
for i in range(4):dense[np.arange(len(p)),j[:,i]]+=w[:,i]
weights=np.zeros((n,nb),np.float32);np.add.at(weights,inv,dense);weights/=np.bincount(inv)[:,None]
t=inv[tri];edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);edges=np.concatenate([edges,edges[:,::-1]])
a=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(n,n)).tocsr();a.data[:]=1;a=diags(1/np.maximum(np.asarray(a.sum(1)).ravel(),1))@a
for _ in range(iterations):weights=0.4*weights+0.6*(a@weights)
indices=np.argsort(weights,axis=1)[:,-4:];values=np.take_along_axis(weights,indices,axis=1);values/=values.sum(1,keepdims=True)
for key,data in [('JOINTS_0',indices[inv].astype('<u2')),('WEIGHTS_0',values[inv].astype('<f4'))]:
 ai=attrs[key];binary.extend(b'\0'*((-len(binary))%4));vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':data.nbytes,'target':34962});binary.extend(data.tobytes());g['accessors'][ai]['bufferView']=vi;g['accessors'][ai]['byteOffset']=0;g['accessors'][ai]['componentType']=5123 if key=='JOINTS_0' else 5126
write(dst,g,binary);print(json.dumps({'source':src,'output':dst,'newMeshVertices':len(p),'weldedVertices':int(n),'iterations':iterations,'originalBuffersRetained':True}))
