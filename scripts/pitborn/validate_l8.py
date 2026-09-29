#!/usr/bin/env python3
"""Structural validation for the Pitborn L8 pilot.

A pilot may be rendered for review while still failing exact animation equivalence;
that failure is recorded explicitly and blocks acceptance/batching.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from pygltflib import GLTF2

COMPONENT = {5120:("b",1),5121:("B",1),5122:("h",2),5123:("H",2),5125:("I",4),5126:("f",4)}
NCOMP = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT2":4,"MAT3":9,"MAT4":16}

def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def glb_bytes(g, path):
    # pygltflib returns the BIN chunk directly for GLB.
    b = g.binary_blob()
    if b is None:
        raise RuntimeError(f"No GLB BIN chunk in {path}")
    return b

def accessor_values(g, blob, idx):
    a=g.accessors[idx]; v=g.bufferViews[a.bufferView]
    fmt,size=COMPONENT[a.componentType]; n=NCOMP[a.type]
    stride=v.byteStride or size*n
    base=(v.byteOffset or 0)+(a.byteOffset or 0)
    rows=[]
    for i in range(a.count):
        off=base+i*stride
        rows.append(struct.unpack_from("<"+fmt*n, blob, off))
    return rows

def joint_names(g):
    out=[]
    for s in g.skins or []:
        out.append([g.nodes[i].name for i in (s.joints or [])])
    return out

def animation_signature(g, path):
    blob=glb_bytes(g,path)
    sig={}
    for a in g.animations or []:
        channels=[]
        for ch in a.channels or []:
            samp=a.samplers[ch.sampler]
            node=g.nodes[ch.target.node].name if ch.target.node is not None else None
            inp=accessor_values(g,blob,samp.input)
            out=accessor_values(g,blob,samp.output)
            channels.append({
              "node":node,"path":ch.target.path,"interpolation":samp.interpolation or "LINEAR",
              "input":inp,"output":out
            })
        sig[a.name]=channels
    return sig

def compare_anim(src,out,tol=1e-6):
    names_src=set(src); names_out=set(out)
    result={"missing":sorted(names_src-names_out),"extra":sorted(names_out-names_src),"per_animation":{}}
    exact=not result["missing"] and not result["extra"]
    for name in sorted(names_src & names_out):
        A=src[name]; B=out[name]
        item={"channel_count_source":len(A),"channel_count_output":len(B),"exact":True,"max_abs":0.0}
        if len(A)!=len(B):
            item["exact"]=False; exact=False
        # Match channels by target rather than exporter order.
        mapA={(c["node"],c["path"]):c for c in A}; mapB={(c["node"],c["path"]):c for c in B}
        if set(mapA)!=set(mapB):
            item["exact"]=False; exact=False
            item["missing_targets"]=sorted(str(x) for x in set(mapA)-set(mapB))
            item["extra_targets"]=sorted(str(x) for x in set(mapB)-set(mapA))
        for key in set(mapA)&set(mapB):
            ca,cb=mapA[key],mapB[key]
            if ca["interpolation"]!=cb["interpolation"] or len(ca["input"])!=len(cb["input"]) or len(ca["output"])!=len(cb["output"]):
                item["exact"]=False; exact=False; continue
            for ra,rb in zip(ca["input"]+ca["output"], cb["input"]+cb["output"]):
                if len(ra)!=len(rb):
                    item["exact"]=False; exact=False; continue
                for x,y in zip(ra,rb):
                    d=abs(float(x)-float(y)); item["max_abs"]=max(item["max_abs"],d)
                    if d>tol: item["exact"]=False; exact=False
        result["per_animation"][name]=item
    result["exact"]=exact
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True); ap.add_argument("--candidate",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    s=GLTF2().load(a.source); c=GLTF2().load(a.candidate)
    sj=joint_names(s); cj=joint_names(c)
    src_anim=animation_signature(s,a.source); out_anim=animation_signature(c,a.candidate)
    anim=compare_anim(src_anim,out_anim)
    source_joint_set=set(x for skin in sj for x in skin if x)
    cand_joint_set=set(x for skin in cj for x in skin if x)
    mats=[m.name for m in c.materials or [] if m.name]
    payload={
      "source":{"sha256":sha256(a.source),"bytes":Path(a.source).stat().st_size,"skins":len(s.skins or []),"animations":len(s.animations or [])},
      "candidate":{"sha256":sha256(a.candidate),"bytes":Path(a.candidate).stat().st_size,"skins":len(c.skins or []),"animations":len(c.animations or []),"materials":mats},
      "rig":{
        "source_joint_names":len(source_joint_set),"candidate_joint_names":len(cand_joint_set),
        "missing_joints":sorted(source_joint_set-cand_joint_set),
        "extra_joints":sorted(cand_joint_set-source_joint_set),
        "preserved": source_joint_set==cand_joint_set
      },
      "animations":anim,
      "l8_materials_present": all(x in mats for x in ["Pitborn L8 · Blackened Steel","Pitborn L8 · Deep Ruby"]),
    }
    payload["pilot_structural_pass"]=payload["rig"]["preserved"] and not anim["missing"] and payload["l8_materials_present"]
    payload["pilot_acceptance_pass"]=payload["pilot_structural_pass"] and anim["exact"]
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload))
    if not payload["pilot_structural_pass"]:
        raise SystemExit(2)

if __name__=="__main__":
    main()
