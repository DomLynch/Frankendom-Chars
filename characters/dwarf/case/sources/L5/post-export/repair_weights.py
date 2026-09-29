"""Measured Dwarf armour weight fields; keep original vertex/animation buffers intact."""
from pathlib import Path
import json,sys
import numpy as np
from merge_armour import read,write

def repair(path):
    path=Path(path);rank=path.stem.rsplit("-",1)[-1];j,data=read(path);b=bytearray(data)
    def ar(index):
        a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]);c={'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']];return np.ndarray((a['count'],c),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',c*dt.itemsize),dt.itemsize))
    def smooth(v):
        t=np.clip(v,0,1);return t*t*(3-2*t)
    node=next(n for n in j['nodes'] if n.get('name')==rank+'_Armour');p=j['meshes'][node['mesh']]['primitives'][0];a=p['attributes'];v=ar(a['POSITION']);ids=ar(a['JOINTS_0']);old=ar(a['WEIGHTS_0']);names=[j['nodes'][i]['name'] for i in j['skins'][node['skin']]['joints']];groups={name:i for i,name in enumerate(names)};w=np.zeros((len(v),len(names)))
    for k in range(4):w[np.arange(len(v)),ids[:,k].astype(int)]+=old[:,k]
    x,y,z=v.T;ax=np.abs(x)
    def blend(mask,parts):
        nonlocal w
        target=np.zeros_like(w)
        for name,weight in parts.items():target[:,groups[name]]=weight
        target/=np.maximum(target.sum(1),1e-12)[:,None]
        w=w*(1-mask[:,None])+target*mask[:,None]
    # Tassets: continuous across centre; pelvis carries the central seam, thighs lift side panels.
    skirt=smooth((y-.400)/.035)*smooth((.805-y)/.06)*smooth((.295-ax)/.045)
    left=smooth((x+.10)/.20);pelvis=.55+.45*smooth((y-.49)/.24);pelvis=np.maximum(pelvis,.86*(1-smooth(ax/.11)))
    blend(skirt,{'pelvis':pelvis,'thigh_l':(1-pelvis)*left,'thigh_r':(1-pelvis)*(1-left)})
    # Shoulder lames follow one shoulder smoothly, excluding neck and opposite arm weights.
    for side,sign in [('l',1),('r',-1)]:
        sx=x*sign;mask=smooth((sx-.155)/.065)*smooth((y-.96)/.09)*smooth((1.30-y)/.08);arm=smooth((sx-.20)/.11)
        blend(mask,{f'clavicle_{side}':1-arm,f'upperarm_{side}':arm})
        # Bracers and greaves use their anatomical limb, not a neighbouring skirt/torso triangle.
        mask=smooth((sx-(.28+.5*(.9-y)))/.04)*smooth((.995-y)/.07)*smooth((y-.70)/.06)
        blend(mask,{f'lowerarm_{side}':np.ones(len(v))})
        mask=smooth((sx-.04)/.04)*smooth((.455-y)/.075)*smooth((y-.105)/.06)
        blend(mask,{f'calf_{side}':np.ones(len(v))})
    # Smooth only new armour over its welded surface graph; UV seams share one weight field.
    unique,inverse=np.unique(np.round(v,5),axis=0,return_inverse=True);count=len(unique)
    tri=ar(p['indices']).reshape(-1,3).astype(int);tri=inverse[tri]
    edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);edges=np.unique(np.sort(edges,axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]];edges=np.concatenate([edges,edges[:,::-1]])
    active=np.where(w.sum(0)>1e-8)[0];counts=np.bincount(inverse,minlength=count);field=np.stack([np.bincount(inverse,weights=w[:,k],minlength=count)/counts for k in active],axis=1);degree=np.maximum(np.bincount(edges[:,0],minlength=count),1)
    for _ in range(16):
        average=np.stack([np.bincount(edges[:,0],weights=field[edges[:,1],k],minlength=count)/degree for k in range(len(active))],axis=1)
        field=.35*field+.65*average
    w[:]=0;w[:,active]=field[inverse]
    chosen=np.argsort(w,axis=1)[:,-4:];values=np.take_along_axis(w,chosen,axis=1);values/=values.sum(1)[:,None];chosen[values==0]=0;ids[:]=chosen;old[:]=values
    assert np.isfinite(old).all() and np.max(np.abs(old.sum(1)-1))<1e-5
    write(path,j,b)
    print(json.dumps({'newArmourVertices':len(v),'regions':['tassets','shoulders','bracers','greaves'],'originalBuffersTouched':False}))

if __name__=="__main__":
    repair(sys.argv[1])
