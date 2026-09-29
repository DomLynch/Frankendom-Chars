"""Compare exported joint world positions over all clips against original."""

import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    d = path.read_bytes()
    n = struct.unpack_from("<I", d, 12)[0]
    return json.loads(d[20 : 20 + n]), d[28 + n :]


def arr(m, b, i):
    a = m["accessors"][i]
    v = m["bufferViews"][a["bufferView"]]
    dt = np.dtype({5126: "<f4", 5123: "<u2", 5125: "<u4", 5121:"u1"}[a["componentType"]])
    w = {"SCALAR": 1, "VEC2":2, "VEC3": 3, "VEC4": 4, "MAT4":16}[a["type"]]
    return np.ndarray(
        (a["count"], w),
        dtype=dt,
        buffer=b,
        offset=v.get("byteOffset", 0) + a.get("byteOffset", 0),
        strides=(v.get("byteStride", w * dt.itemsize), dt.itemsize),
    )


def positions(m, b, clip, t):
    nodes = m["nodes"]
    values = {}
    a = next(a for a in m["animations"] if a["name"] == clip)
    for c in a["channels"]:
        s = a["samplers"][c["sampler"]]
        ts = arr(m, b, s["input"])[:, 0]
        vs = arr(m, b, s["output"])
        j = int(np.searchsorted(ts, t))
        lo = max(0, j - 1)
        hi = min(len(ts) - 1, j)
        f = 0 if lo == hi else float(np.clip((t - ts[lo]) / (ts[hi] - ts[lo]), 0, 1))
        u = vs[lo].astype(float)
        v = vs[hi].astype(float)
        path = c["target"]["path"]
        if path == "rotation":
            dot = np.dot(u, v)
            if dot < 0:
                v = -v
                dot = -dot
            if dot < 0.9995:
                angle = np.arccos(np.clip(dot, -1, 1))
                value = (np.sin((1 - f) * angle) * u + np.sin(f * angle) * v) / np.sin(
                    angle
                )
            else:
                value = (1 - f) * u + f * v
            value /= np.linalg.norm(value)
        else:
            value = (1 - f) * u + f * v
        values[(c["target"]["node"], path)] = value
    parents = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
    cache = {}

    def world(i):
        if i in cache:
            return cache[i]
        n = nodes[i]
        if "matrix" in n:
            local = np.array(n["matrix"]).reshape(4, 4).T
        else:
            x, y, z, w = values.get((i, "rotation"), n.get("rotation", [0, 0, 0, 1]))
            local = np.eye(4)
            local[:3, :3] = np.array(
                [
                    [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
                ]
            ) @ np.diag(values.get((i, "scale"), n.get("scale", [1, 1, 1])))
            local[:3, 3] = values.get(
                (i, "translation"), n.get("translation", [0, 0, 0])
            )
        cache[i] = world(parents[i]) @ local if i in parents else local
        return cache[i]

    return {nodes[i]["name"]: world(i) for i in m["skins"][0]["joints"]}



def skin_positions(m,b,node,matrices):
    skin=m['skins'][node['skin']];p=m['meshes'][node['mesh']]['primitives'][0];a=p['attributes'];vertices=arr(m,b,a['POSITION']);w=arr(m,b,a['WEIGHTS_0']);ids=arr(m,b,a['JOINTS_0']).astype(int);ibm=arr(m,b,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);transforms=np.array([matrices[m['nodes'][i]['name']]@ib for i,ib in zip(skin['joints'],ibm)]);homogeneous=np.c_[vertices,np.ones(len(vertices))];out=np.zeros((len(vertices),4))
    for influence in range(4):out+=np.einsum('nij,nj->ni',transforms[ids[:,influence]],homogeneous)*w[:,influence,None]
    assert all(part['attributes']==a for part in m['meshes'][node['mesh']]['primitives'])
    return out[:,:3],np.concatenate([arr(m,b,part['indices']).reshape(-1,3).astype(int) for part in m['meshes'][node['mesh']]['primitives']])

if __name__=='__main__':
    import sys
    rank=sys.argv[1];m,b=read(ROOT/f'models/dwarf-{rank}.glb');original,ob=read(ROOT/'models/dwarf-L1.glb');report=[]
    for clip in ['Warhammer_Idle','Warhammer_Heavy','Warhammer_Guard','Kick','Warhammer_Slash','Warhammer_Thrust']:
        anim=next(a for a in m['animations'] if a['name']==clip);end=max(float(arr(m,b,s['input'])[-1,0]) for s in anim['samplers'])
        for f in [0,.25,.5,.75,1]:
            matrices=positions(m,b,clip,end*f);expected=positions(original,ob,clip,end*f);assert all(np.array_equal(matrices[n],expected[n]) for n in expected)
            for node in m['nodes']:
                if not node.get('name','').startswith(rank+'_') or 'mesh' not in node:continue
                v,indices=skin_positions(m,b,node,matrices);assert np.isfinite(v).all();edges=np.concatenate([indices[:,[0,1]],indices[:,[1,2]],indices[:,[2,0]]]);rest=arr(m,b,m['meshes'][node['mesh']]['primitives'][0]['attributes']['POSITION']);restlen=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);length=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1);valid=restlen>1e-5;ratio=length[valid]/restlen[valid]
                report.append({'clip':clip,'fraction':f,'mesh':node['name'],'p99Stretch':float(np.quantile(ratio,.99)),'maxStretch':float(ratio.max()),'longStretchedEdges':int(((length[valid]>.10)&(ratio>3)).sum()),'bounds':[v.min(0).tolist(),v.max(0).tolist()]})
    (ROOT/f'reports/motion-{rank}.json').write_text(json.dumps(report,indent=2));print(json.dumps({'samples':len(report),'maxP99Stretch':max(x['p99Stretch'] for x in report),'worstLongEdges':max(x['longStretchedEdges'] for x in report),'scope':'diagnostics; image review decides clearance'}))
