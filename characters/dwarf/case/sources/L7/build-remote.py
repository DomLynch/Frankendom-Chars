import sys
from pathlib import Path
H=Path('/tmp/dwarf-helpers');H.mkdir(exist_ok=True)
(H/'merge_armour.py').write_text('"""Append Blender-fitted armour while retaining exact source rig/clip/mesh buffers."""\nimport copy\nimport json\nimport struct\nfrom pathlib import Path\nimport numpy as np\nfrom PIL import Image\nimport io\n\n\ndef read(path):\n    b=Path(path).read_bytes();n=struct.unpack_from(\'<I\',b,12)[0]\n    return json.loads(b[20:20+n]),b[28+n:]\n\n\ndef write(path,j,b):\n    b=bytes(b)+b\'\\0\'*(-len(b)%4);j[\'buffers\']=[{\'byteLength\':len(b)}]\n    s=json.dumps(j,separators=(\',\',\':\')).encode();s+=b\' \'*(-len(s)%4)\n    Path(path).write_bytes(struct.pack(\'<III\',0x46546c67,2,28+len(s)+len(b))+struct.pack(\'<II\',len(s),0x4e4f534a)+s+struct.pack(\'<II\',len(b),0x004e4942)+b)\n\n\ndef worlds(j):\n    def local(n):\n        if \'matrix\' in n:return np.array(n[\'matrix\']).reshape(4,4).T\n        x,y,z,w=n.get(\'rotation\',[0,0,0,1]);m=np.eye(4)\n        m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get(\'scale\',[1,1,1]));m[:3,3]=n.get(\'translation\',[0,0,0]);return m\n    parents={c:i for i,n in enumerate(j[\'nodes\']) for c in n.get(\'children\',[])};cache={}\n    def visit(i):\n        if i not in cache:cache[i]=(visit(parents[i]) if i in parents else np.eye(4))@local(j[\'nodes\'][i])\n        return cache[i]\n    return {i:visit(i) for i in range(len(j[\'nodes\']))}\n\n\ndef merge(original,addon,dest):\n    rank=Path(dest).stem.rsplit(\'-\',1)[-1]\n    assert rank in [f\'L{i}\' for i in range(2,11)],rank\n    j,b=read(original);a,ab=read(addon);b=bytearray(b);original_animation=copy.deepcopy(j[\'animations\']);ow=worlds(j);aw=worlds(a)\n    names={n.get(\'name\'):i for i,n in enumerate(j[\'nodes\']) if n.get(\'name\')};memo={};errors=[]\n    body_node=next(i for i,n in enumerate(j[\'nodes\']) if n.get(\'name\')==\'CreatureBody\')\n    source_skin=j[\'skins\'][j[\'nodes\'][body_node][\'skin\']];ac=j[\'accessors\'][source_skin[\'inverseBindMatrices\']];bv=j[\'bufferViews\'][ac[\'bufferView\']]\n    source_ibm=np.frombuffer(bytes(b),dtype=\'<f4\',offset=bv.get(\'byteOffset\',0)+ac.get(\'byteOffset\',0),count=ac[\'count\']*16).reshape(-1,4,4).transpose(0,2,1)\n    source_bind={n:ow[body_node]@np.linalg.inv(m) for n,m in zip(source_skin[\'joints\'],source_ibm)}\n    world_ibm={n:m@np.linalg.inv(ow[body_node]) for n,m in zip(source_skin[\'joints\'],source_ibm)}\n    def add(kind,index):\n        key=(kind,index)\n        if key in memo:return memo[key]\n        value=copy.deepcopy(a[kind][index])\n        if kind==\'images\':\n            av=a[\'bufferViews\'][value[\'bufferView\']];start=av.get(\'byteOffset\',0);payload=ab[start:start+av[\'byteLength\']]\n            for old,existing in enumerate(j.get(\'images\',[])):\n                if existing.get(\'mimeType\')!=value.get(\'mimeType\') or \'bufferView\' not in existing:continue\n                bv=j[\'bufferViews\'][existing[\'bufferView\']];lo=bv.get(\'byteOffset\',0)\n                if bytes(b[lo:lo+bv[\'byteLength\']])==payload:memo[key]=old;return old\n        idx=len(j.setdefault(kind,[]));memo[key]=idx;j[kind].append(value)\n        if kind==\'bufferViews\':\n            start=value.get(\'byteOffset\',0);b.extend(b\'\\0\'*(-len(b)%4));value[\'buffer\']=0;value[\'byteOffset\']=len(b);b.extend(ab[start:start+value[\'byteLength\']])\n        elif kind==\'accessors\':\n            assert \'sparse\' not in value\n            value[\'bufferView\']=add(\'bufferViews\',value[\'bufferView\'])\n        elif kind==\'images\':value[\'bufferView\']=add(\'bufferViews\',value[\'bufferView\'])\n        elif kind==\'textures\':\n            if \'source\' in value:value[\'source\']=add(\'images\',value[\'source\'])\n            if \'sampler\' in value:value[\'sampler\']=add(\'samplers\',value[\'sampler\'])\n            for ext,info in value.get(\'extensions\',{}).items():\n                assert ext in [\'EXT_texture_webp\',\'KHR_texture_basisu\'],ext\n                info[\'source\']=add(\'images\',info[\'source\'])\n        elif kind==\'materials\':\n            if value.get(\'name\')==\'Dwarf oxblood leather gloves\':value[\'pbrMetallicRoughness\'].pop(\'metallicRoughnessTexture\',None)\n            def textures(obj):\n                for k,v in obj.items():\n                    if isinstance(v,dict):\n                        if k.endswith(\'Texture\') and \'index\' in v:v[\'index\']=add(\'textures\',v[\'index\'])\n                        else:textures(v)\n            textures(value)\n            if value.get("name")=="Dwarf oxblood leather gloves":\n                value["pbrMetallicRoughness"]["baseColorFactor"]=[.18,.075,.045,1]\n                value["pbrMetallicRoughness"]["roughnessFactor"]=.74\n                source_material=j["materials"][j["meshes"][j["nodes"][body_node]["mesh"]]["primitives"][0]["material"]]\n                value["pbrMetallicRoughness"]["metallicRoughnessTexture"]=copy.deepcopy(source_material["pbrMetallicRoughness"]["metallicRoughnessTexture"])\n        elif kind==\'meshes\':\n            for p in value[\'primitives\']:\n                p[\'attributes\']={k:add(\'accessors\',v) for k,v in p[\'attributes\'].items()}\n                for field,typ in [(\'indices\',\'accessors\'),(\'material\',\'materials\')]:\n                    if field in p:p[field]=add(typ,p[field])\n                assert not p.get(\'targets\') and not p.get(\'extensions\')\n        elif kind==\'skins\':\n            joints=[]\n            for old in value[\'joints\']:\n                name=a[\'nodes\'][old][\'name\'];new=names[name];err=float(np.max(np.abs(source_bind[new][:3,3]-aw[old][:3,3])));errors.append(err)\n                assert err<2e-5,(name,err)\n                joints.append(new)\n            ac=a[\'accessors\'][value[\'inverseBindMatrices\']];bv=a[\'bufferViews\'][ac[\'bufferView\']]\n            ibm=np.frombuffer(ab,dtype=\'<f4\',offset=bv.get(\'byteOffset\',0)+ac.get(\'byteOffset\',0),count=ac[\'count\']*16).reshape(-1,4,4).transpose(0,2,1)\n            # Blender changes bone axes on import. New mesh positions already bind in world space.\n            # Require that fact numerically, then bind new vertices directly to ORIGINAL bone axes.\n            bind_error=max(float(np.max(np.abs(aw[node]@matrix-np.eye(4)))) for node,matrix in zip(value[\'joints\'],ibm))\n            assert bind_error<2e-5,(\'Addon not world-space bound\',bind_error)\n            corrected=np.array([world_ibm[node].T for node in joints],dtype=\'<f4\').tobytes()\n            b.extend(b\'\\0\'*(-len(b)%4));vi=len(j[\'bufferViews\']);j[\'bufferViews\'].append({\'buffer\':0,\'byteOffset\':len(b),\'byteLength\':len(corrected)});b.extend(corrected)\n            ai=len(j[\'accessors\']);j[\'accessors\'].append({\'bufferView\':vi,\'componentType\':5126,\'count\':len(joints),\'type\':\'MAT4\'})\n            value[\'joints\']=joints;value[\'inverseBindMatrices\']=ai;value.pop(\'skeleton\',None)\n        return idx\n    selected=[]\n    for i,n in enumerate(a[\'nodes\']):\n        if \'mesh\' not in n or not n.get(\'name\',\'\').startswith(rank+\'_\'):continue\n        node={\'name\':n[\'name\'],\'mesh\':add(\'meshes\',n[\'mesh\']),\'matrix\':np.eye(4).T.reshape(-1).tolist()}\n        if \'skin\' in n:node[\'skin\']=add(\'skins\',n[\'skin\'])\n        selected.append(node[\'name\']);j[\'scenes\'][j.get(\'scene\',0)][\'nodes\'].append(len(j[\'nodes\']));j[\'nodes\'].append(node)\n    assert selected,\'No fitted armour meshes\'\n    # Original helmet data remains in the file, but is excluded from the active scene.\n    hidden=[i for i,n in enumerate(j[\'nodes\']) if n.get(\'name\') in [\'Steel.Helmet\',\'Antique brass.Helmet\']]\n    for n in j[\'nodes\']:\n        if \'children\' in n:n[\'children\']=[i for i in n[\'children\'] if i not in hidden]\n    for ext in a.get(\'extensionsUsed\',[]):\n        if ext not in j.setdefault(\'extensionsUsed\',[]):j[\'extensionsUsed\'].append(ext)\n    # Keep original visible face/beard and exposed limb skin. Old embedded kit stays\n    # byte-preserved in its original mesh, but is not drawn through the new armour.\n    source_bytes=read(original)[1]\n    def original_array(index):\n        ac=j[\'accessors\'][index];bv=j[\'bufferViews\'][ac[\'bufferView\']];dt=np.dtype({5126:\'<f4\',5123:\'<u2\',5125:\'<u4\',5121:\'u1\'}[ac[\'componentType\']]);width={\'VEC2\':2,\'VEC3\':3,\'VEC4\':4,\'SCALAR\':1}[ac[\'type\']]\n        return np.ndarray((ac[\'count\'],width),dtype=dt,buffer=source_bytes,offset=bv.get(\'byteOffset\',0)+ac.get(\'byteOffset\',0),strides=(bv.get(\'byteStride\',width*dt.itemsize),dt.itemsize))\n    visible=copy.deepcopy(j[\'meshes\'][j[\'nodes\'][body_node][\'mesh\']]);visible[\'name\']=\'Original Dwarf visible skin\';hidden_faces=0;kept_faces=0\n    for primitive in visible[\'primitives\']:\n        attrs=primitive[\'attributes\'];pos=original_array(attrs[\'POSITION\']);points=(ow[body_node]@np.c_[pos,np.ones(len(pos))].T).T[:,:3];indices=original_array(primitive[\'indices\']).reshape(-1,3);centres=points[indices].mean(1)\n        tex=j[\'textures\'][j[\'materials\'][primitive[\'material\']][\'pbrMetallicRoughness\'][\'baseColorTexture\'][\'index\']];im=j[\'images\'][tex.get(\'source\',tex.get(\'extensions\',{}).get(\'EXT_texture_webp\',{}).get(\'source\'))];bv=j[\'bufferViews\'][im[\'bufferView\']];imdata=Image.open(io.BytesIO(source_bytes[bv.get(\'byteOffset\',0):bv.get(\'byteOffset\',0)+bv[\'byteLength\']])).convert(\'RGB\');pixels=np.asarray(imdata)/255;uv=original_array(attrs[\'TEXCOORD_0\'])[indices].mean(1)\n        # glTF images use top-left UV origin. Pixel colours only select original exposed skin.\n        colors=pixels[np.clip((uv[:,1]*imdata.height).astype(int),0,imdata.height-1),np.clip((uv[:,0]*imdata.width).astype(int),0,imdata.width-1)]\n        skin=(colors[:,0]>colors[:,1]*1.075)&(colors[:,1]>colors[:,2]*1.025)\n        x=np.abs(centres[:,0]);height=centres[:,1]\n        head=(x<.17)&(height>1.025)\n        biceps=(x>.18)&(x<.36)&(height>.80)&(height<1.16)&skin\n        thighs=(x>.045)&(x<.235)&(height>.37)&(height<.68)&skin\n        keep=head|biceps|thighs\n        kept_faces+=int(keep.sum());hidden_faces+=int((~keep).sum());payload=np.asarray(indices[keep],dtype=\'<u4\').tobytes();b.extend(b\'\\0\'*(-len(b)%4));vi=len(j[\'bufferViews\']);j[\'bufferViews\'].append({\'buffer\':0,\'byteOffset\':len(b),\'byteLength\':len(payload),\'target\':34963});b.extend(payload);ai=len(j[\'accessors\']);j[\'accessors\'].append({\'bufferView\':vi,\'componentType\':5125,\'count\':int(keep.sum())*3,\'type\':\'SCALAR\'});primitive[\'indices\']=ai\n    j[\'nodes\'][body_node][\'mesh\']=len(j[\'meshes\']);j[\'meshes\'].append(visible)\n    tangent_repairs=0\n    def vector_accessor(index,width):\n        ac=j[\'accessors\'][index];bv=j[\'bufferViews\'][ac[\'bufferView\']]\n        return np.ndarray((ac[\'count\'],width),dtype=\'<f4\',buffer=b,offset=bv.get(\'byteOffset\',0)+ac.get(\'byteOffset\',0),strides=(bv.get(\'byteStride\',width*4),4))\n    for node in j[\'nodes\']:\n        if node.get(\'name\') not in selected:continue\n        for primitive in j[\'meshes\'][node[\'mesh\']][\'primitives\']:\n            attrs=primitive[\'attributes\']\n            if \'TANGENT\' not in attrs:continue\n            t=vector_accessor(attrs[\'TANGENT\'],4);normal=vector_accessor(attrs[\'NORMAL\'],3);length=np.linalg.norm(t[:,:3],axis=1)\n            for index in np.where(length<1e-8)[0]:\n                axis=np.eye(3)[np.argmin(np.abs(normal[index]))];v=np.cross(normal[index],axis);v/=np.linalg.norm(v);t[index,:3]=v;t[index,3]=1;tangent_repairs+=1\n            lengths=np.linalg.norm(t[:,:3],axis=1);t[:,:3]/=lengths[:,None]\n    assert j[\'animations\']==original_animation\n    write(dest,j,b)\n    return {\'originalBodyFacesVisible\':kept_faces,\'originalBodyFacesHidden\':hidden_faces,\'repairedZeroTangents\':tangent_repairs,\'appended\':selected,\'maxJointRestPositionError\':max(errors),\'newArmourReboundToOriginalAxes\':True,\'originalAnimationsExact\':True,\'originalBinaryPrefixExact\':bytes(b[:len(read(original)[1])])==read(original)[1],\'hiddenOriginalHelmetNodes\':hidden}\n\nif __name__==\'__main__\':\n    import sys\n    print(json.dumps(merge(*sys.argv[1:4]),indent=2))\n')
(H/'repair_weights.py').write_text('"""Measured Dwarf armour weight fields; keep original vertex/animation buffers intact."""\nfrom pathlib import Path\nimport json,sys\nimport numpy as np\nfrom merge_armour import read,write\n\ndef repair(path):\n    path=Path(path);rank=path.stem.rsplit("-",1)[-1];j,data=read(path);b=bytearray(data)\n    def ar(index):\n        a=j[\'accessors\'][index];v=j[\'bufferViews\'][a[\'bufferView\']];dt=np.dtype({5126:\'<f4\',5123:\'<u2\',5125:\'<u4\',5121:\'u1\'}[a[\'componentType\']]);c={\'VEC3\':3,\'VEC4\':4,\'SCALAR\':1}[a[\'type\']];return np.ndarray((a[\'count\'],c),dtype=dt,buffer=b,offset=v.get(\'byteOffset\',0)+a.get(\'byteOffset\',0),strides=(v.get(\'byteStride\',c*dt.itemsize),dt.itemsize))\n    def smooth(v):\n        t=np.clip(v,0,1);return t*t*(3-2*t)\n    node=next(n for n in j[\'nodes\'] if n.get(\'name\')==rank+\'_Armour\');p=j[\'meshes\'][node[\'mesh\']][\'primitives\'][0];a=p[\'attributes\'];v=ar(a[\'POSITION\']);ids=ar(a[\'JOINTS_0\']);old=ar(a[\'WEIGHTS_0\']);names=[j[\'nodes\'][i][\'name\'] for i in j[\'skins\'][node[\'skin\']][\'joints\']];groups={name:i for i,name in enumerate(names)};w=np.zeros((len(v),len(names)))\n    for k in range(4):w[np.arange(len(v)),ids[:,k].astype(int)]+=old[:,k]\n    x,y,z=v.T;ax=np.abs(x)\n    def blend(mask,parts):\n        nonlocal w\n        target=np.zeros_like(w)\n        for name,weight in parts.items():target[:,groups[name]]=weight\n        target/=np.maximum(target.sum(1),1e-12)[:,None]\n        w=w*(1-mask[:,None])+target*mask[:,None]\n    # Tassets: continuous across centre; pelvis carries the central seam, thighs lift side panels.\n    skirt=smooth((y-.400)/.035)*smooth((.805-y)/.06)*smooth((.295-ax)/.045)\n    left=smooth((x+.10)/.20);pelvis=.55+.45*smooth((y-.49)/.24);pelvis=np.maximum(pelvis,.86*(1-smooth(ax/.11)))\n    blend(skirt,{\'pelvis\':pelvis,\'thigh_l\':(1-pelvis)*left,\'thigh_r\':(1-pelvis)*(1-left)})\n    # Shoulder lames follow one shoulder smoothly, excluding neck and opposite arm weights.\n    for side,sign in [(\'l\',1),(\'r\',-1)]:\n        sx=x*sign;mask=smooth((sx-.155)/.065)*smooth((y-.96)/.09)*smooth((1.30-y)/.08);arm=smooth((sx-.20)/.11)\n        blend(mask,{f\'clavicle_{side}\':1-arm,f\'upperarm_{side}\':arm})\n        # Bracers and greaves use their anatomical limb, not a neighbouring skirt/torso triangle.\n        mask=smooth((sx-(.28+.5*(.9-y)))/.04)*smooth((.995-y)/.07)*smooth((y-.70)/.06)\n        blend(mask,{f\'lowerarm_{side}\':np.ones(len(v))})\n        mask=smooth((sx-.04)/.04)*smooth((.455-y)/.075)*smooth((y-.105)/.06)\n        blend(mask,{f\'calf_{side}\':np.ones(len(v))})\n    # Smooth only new armour over its welded surface graph; UV seams share one weight field.\n    unique,inverse=np.unique(np.round(v,5),axis=0,return_inverse=True);count=len(unique)\n    tri=ar(p[\'indices\']).reshape(-1,3).astype(int);tri=inverse[tri]\n    edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);edges=np.unique(np.sort(edges,axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]];edges=np.concatenate([edges,edges[:,::-1]])\n    active=np.where(w.sum(0)>1e-8)[0];counts=np.bincount(inverse,minlength=count);field=np.stack([np.bincount(inverse,weights=w[:,k],minlength=count)/counts for k in active],axis=1);degree=np.maximum(np.bincount(edges[:,0],minlength=count),1)\n    for _ in range(16):\n        average=np.stack([np.bincount(edges[:,0],weights=field[edges[:,1],k],minlength=count)/degree for k in range(len(active))],axis=1)\n        field=.35*field+.65*average\n    w[:]=0;w[:,active]=field[inverse]\n    chosen=np.argsort(w,axis=1)[:,-4:];values=np.take_along_axis(w,chosen,axis=1);values/=values.sum(1)[:,None];chosen[values==0]=0;ids[:]=chosen;old[:]=values\n    assert np.isfinite(old).all() and np.max(np.abs(old.sum(1)-1))<1e-5\n    write(path,j,b)\n    print(json.dumps({\'newArmourVertices\':len(v),\'regions\':[\'tassets\',\'shoulders\',\'bracers\',\'greaves\'],\'originalBuffersTouched\':False}))\n\nif __name__=="__main__":\n    repair(sys.argv[1])\n')
(H/'finish_materials.py').write_text('"""Material-specific finish and weighted leather lining, using saved geometry/textures."""\nfrom pathlib import Path\nimport sys,json,copy,io\nimport numpy as np\nfrom PIL import Image\nfrom merge_armour import read,write,worlds\n\ndef finish(path):\n    path=Path(path);rank=path.stem.rsplit(\'-\',1)[-1];j,original=read(path);b=bytearray(original)\n    def arr(index):\n        a=j[\'accessors\'][index];v=j[\'bufferViews\'][a[\'bufferView\']];dt=np.dtype({5126:\'<f4\',5123:\'<u2\',5125:\'<u4\',5121:\'u1\'}[a[\'componentType\']]);c={\'VEC3\':3,\'VEC4\':4,\'VEC2\':2,\'SCALAR\':1}[a[\'type\']];return np.ndarray((a[\'count\'],c),dtype=dt,buffer=original,offset=v.get(\'byteOffset\',0)+a.get(\'byteOffset\',0),strides=(v.get(\'byteStride\',c*dt.itemsize),dt.itemsize))\n    def texture(index):\n        t=j[\'textures\'][index];image=j[\'images\'][t.get(\'source\',t.get(\'extensions\',{}).get(\'EXT_texture_webp\',{}).get(\'source\'))];v=j[\'bufferViews\'][image[\'bufferView\']];lo=v.get(\'byteOffset\',0);return np.asarray(Image.open(io.BytesIO(original[lo:lo+v[\'byteLength\']])).convert(\'RGB\'))/255\n    def indices(values):\n        payload=np.asarray(values,dtype=\'<u4\').tobytes();b.extend(b\'\\0\'*(-len(b)%4));v=len(j[\'bufferViews\']);j[\'bufferViews\'].append({\'buffer\':0,\'byteOffset\':len(b),\'byteLength\':len(payload),\'target\':34963});b.extend(payload);a=len(j[\'accessors\']);j[\'accessors\'].append({\'bufferView\':v,\'componentType\':5125,\'count\':len(values)*3,\'type\':\'SCALAR\'});return a\n    armour=next(n for n in j[\'nodes\'] if n.get(\'name\')==rank+\'_Armour\');mesh=j[\'meshes\'][armour[\'mesh\']];assert len(mesh[\'primitives\'])==1,\'Apply finish once after a fresh merge/weight repair\'\n    prim=mesh[\'primitives\'][0];mat=j[\'materials\'][prim[\'material\']];faces=arr(prim[\'indices\']).reshape(-1,3);uv=arr(prim[\'attributes\'][\'TEXCOORD_0\'])[faces].mean(1)\n    def sample(pixels):return pixels[np.clip((uv[:,1]*len(pixels)).astype(int),0,len(pixels)-1),np.clip((uv[:,0]*pixels.shape[1]).astype(int),0,pixels.shape[1]-1)]\n    color=sample(texture(mat[\'pbrMetallicRoughness\'][\'baseColorTexture\'][\'index\']));orm=sample(texture(mat[\'pbrMetallicRoughness\'][\'metallicRoughnessTexture\'][\'index\']));red,green,blue=color.T;gem=np.zeros(len(red),dtype=bool);metal=(orm[:,2]>.45)&~gem;leather=~metal&~gem\n    mesh[\'primitives\']=[];counts={}\n    for name,mask,metalness,roughness in [(\'Rank armour finish\',metal,0.76,0.42),(\'Leather and exposed surface\',leather,0,.82),(\'Emerald inset\',gem,.08,.22)]:\n        if not mask.any():continue\n        material=copy.deepcopy(mat);material[\'name\']=rank+\' \'+name;pbr=material[\'pbrMetallicRoughness\'];pbr.pop(\'metallicRoughnessTexture\',None);pbr[\'metallicFactor\']=metalness;pbr[\'roughnessFactor\']=roughness;material[\'emissiveFactor\']=[0,0,0];pbr[\'baseColorFactor\']=[.40,.40,.40,1] if name==\'Blackened forged steel\' else [1,1,1,1];mi=len(j[\'materials\']);j[\'materials\'].append(material);p=copy.deepcopy(prim);p[\'material\']=mi;p[\'indices\']=indices(faces[mask]);mesh[\'primitives\'].append(p);counts[name]=int(mask.sum())\n    # Duplicate only the covered source torso triangles for a continuous leather underlayer.\n    source_mesh=next(m for m in j[\'meshes\'] if m.get(\'name\')==\'geometry_0\');source_prim=source_mesh[\'primitives\'][0]\n    body_index=next(i for i,n in enumerate(j[\'nodes\']) if n.get(\'name\')==\'CreatureBody\');body=j[\'nodes\'][body_index];visible=j[\'meshes\'][body[\'mesh\']][\'primitives\'][0];f=arr(source_prim[\'indices\']).reshape(-1,3);v=arr(source_prim[\'attributes\'][\'POSITION\']);world=worlds(j)[body_index];points=(world@np.c_[v,np.ones(len(v))].T).T[:,:3];c=points[f].mean(1)\n    visible_faces={tuple(face) for face in arr(visible[\'indices\']).reshape(-1,3)};covered=np.array([tuple(face) not in visible_faces for face in f]);mask=covered&(c[:,1]>.66)&(c[:,1]<1.18)&(np.abs(c[:,0])<.20)\n    # The copied lining gets its own smooth torso weights; original source weights stay untouched.\n    joint_names=[j[\'nodes\'][i][\'name\'] for i in j[\'skins\'][body[\'skin\']][\'joints\']];levels=np.array([.77,.91,1.04,1.16]);height=points[:,1];weights=np.zeros((len(v),4),dtype=\'<f4\');joint_ids=np.tile(np.array([joint_names.index(n) for n in [\'pelvis\',\'spine_01\',\'spine_02\',\'spine_03\']],dtype=\'<u2\'),(len(v),1))\n    for vi,h in enumerate(height):\n        upper=int(np.clip(np.searchsorted(levels,h),1,3));lower=upper-1;t=float(np.clip((h-levels[lower])/(levels[upper]-levels[lower]),0,1));t=t*t*(3-2*t);weights[vi,lower]=1-t;weights[vi,upper]=t\n    joint_ids[weights==0]=0\n    def vertex_accessor(values,component):\n        payload=values.tobytes();b.extend(b\'\\0\'*(-len(b)%4));view=len(j[\'bufferViews\']);j[\'bufferViews\'].append({\'buffer\':0,\'byteOffset\':len(b),\'byteLength\':len(payload),\'target\':34962});b.extend(payload);accessor=len(j[\'accessors\']);j[\'accessors\'].append({\'bufferView\':view,\'componentType\':component,\'count\':len(values),\'type\':\'VEC\'+str(values.shape[1]),**({\'min\':values.min(0).tolist(),\'max\':values.max(0).tolist()} if values.shape[1]==3 else {})});return accessor\n    lining_attributes=copy.deepcopy(source_prim[\'attributes\']);lining_points=points.copy();lining_points[:,0]*=.78;lining_points[:,2]*=.72;lining_local=(np.linalg.inv(world)@np.c_[lining_points,np.ones(len(v))].T).T[:,:3].astype(\'<f4\');lining_attributes[\'POSITION\']=vertex_accessor(lining_local,5126);lining_attributes[\'JOINTS_0\']=vertex_accessor(joint_ids,5123);lining_attributes[\'WEIGHTS_0\']=vertex_accessor(weights,5126)\n    lining=copy.deepcopy(j[\'materials\'][source_prim[\'material\']]);lining[\'name\']=rank+\' textured leather under-armour\';lining[\'pbrMetallicRoughness\'][\'baseColorFactor\']=[.10,.055,.03,1];lining[\'pbrMetallicRoughness\'][\'metallicFactor\']=0;lining[\'pbrMetallicRoughness\'][\'roughnessFactor\']=1;mi=len(j[\'materials\']);j[\'materials\'].append(lining);lp=copy.deepcopy(source_prim);lp[\'attributes\']=lining_attributes;lp[\'material\']=mi;lp[\'indices\']=indices(f[mask]);mesh_id=len(j[\'meshes\']);j[\'meshes\'].append({\'name\':rank+\'_Lining\',\'primitives\':[lp]});j[\'scenes\'][j.get(\'scene\',0)][\'nodes\'].append(len(j[\'nodes\']));j[\'nodes\'].append({\'name\':rank+\'_Lining\',\'mesh\':mesh_id,\'skin\':body[\'skin\']})\n    gloves=next(n for n in j[\'nodes\'] if n.get(\'name\')==rank+\'_Gloves\');gp=j[\'meshes\'][gloves[\'mesh\']][\'primitives\'][0];gm=j[\'materials\'][gp[\'material\']][\'pbrMetallicRoughness\'];gm.pop(\'baseColorTexture\',None);gm[\'baseColorFactor\']=[0.55, 0.59, 0.64, 1];gm[\'metallicFactor\']=0.76;gm[\'roughnessFactor\']=0.42\n    write(path,j,b);print(json.dumps({\'materialTriangles\':counts,\'liningTriangles\':int(mask.sum()),\'sourceGeometryAndWeightsUnchanged\':True}))\nif __name__==\'__main__\':finish(sys.argv[1])\n')
sys.path.insert(0,str(H))
"""Dwarf-specific L7 fit; preserve donor texture and original rig/face/hands."""
from pathlib import Path
import json,hashlib,os,sys,urllib.request
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from huggingface_hub import HfApi,get_token,hf_hub_url

REPO='Domlynch/frankendom-dwarf-ranks-20260928'
R=Path('/tmp/dwarf-fit');R.mkdir(exist_ok=True)
api=HfApi();revision=api.repo_info(REPO,repo_type='dataset').sha

def download(name):
    path=R/name
    req=urllib.request.Request(hf_hub_url(REPO,name,repo_type='dataset',revision=revision),headers={'Authorization':'Bearer '+get_token()})
    with urllib.request.urlopen(req,timeout=90) as response:path.write_bytes(response.read())
    return path

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(download('original.glb')))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
for t in rig.animation_data.nla_tracks:t.mute=True
rig.animation_data.action=None
original=[o for o in bpy.context.scene.objects if o.type=='MESH'];body=bpy.data.objects['CreatureBody']
def signature(o):
    return hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices]).encode()).hexdigest()
before={o.name:signature(o) for o in original}
body.data.calc_loop_triangles();points=[body.matrix_world@v.co for v in body.data.vertices];faces=[tuple(f.vertices) for f in body.data.loop_triangles];bvh=BVHTree.FromPolygons(points,faces,all_triangles=True)
groups={g.index:g.name for g in body.vertex_groups}
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(download('L7-donor.glb')));raw=next(o for o in bpy.context.scene.objects if o not in existing and o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT');raw.select_set(True);bpy.context.view_layer.objects.active=raw;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
lo=min(v.co.z for v in raw.data.vertices)
for v in raw.data.vertices:v.co=Vector((v.co.x*1.32,v.co.y*1.44,(v.co.z-lo)*1.44+.025))
raw.name='L7_Armour'
for v in raw.data.vertices:
    if abs(v.co.x)<.23 and v.co.z>1.24:
        t=float(np.clip((v.co.z-1.24)/.085,0,1));v.co.z+=.035*t*t*(3-2*t)
material=raw.data.materials[0];shader=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');image=shader.inputs['Base Color'].links[0].from_node.image
pixels=np.asarray(image.pixels[:]).reshape(image.size[1],image.size[0],4);uv=raw.data.uv_layers.active.data
remove=[]
for f in raw.data.polygons:
    c=sum((raw.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
    uvp=sum((uv[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
    color=pixels[min(image.size[1]-1,max(0,int(uvp.y*image.size[1]))),min(image.size[0]-1,max(0,int(uvp.x*image.size[0])))][:3]
    red,green,blue=color
    skin=red>green*1.16 and red<green*1.65 and green>blue*1.06 and green<blue*1.55 and red>.32 and green>.20
    # Only remove demonstrated skin regions, not brown armour over the torso.
    head_window=abs(c.x)<.155 and c.z>1.025 and c.z<1.31 and c.y<-.055
    head_skin=abs(c.x)<.175 and c.z>1.16 and skin
    hand=abs(c.x)>.365 and c.z<.77
    bare_arm=abs(c.x)>.245 and .825<c.z<1.07 and skin
    rear_hair=abs(c.x)<.13 and c.y>.015 and 1.16<c.z<1.315
    if head_window or head_skin or rear_hair or hand or bare_arm:remove.append(f.index)
bm=bmesh.new();bm.from_mesh(raw.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(raw.data);bm.free()

def weights(co):
    hit=bvh.find_nearest(co);ids=faces[hit[2]];a,b,c=[points[i] for i in ids];e0=b-a;e1=c-a;e2=hit[0]-a
    d00=e0.dot(e0);d01=e0.dot(e1);d11=e1.dot(e1);d20=e2.dot(e0);d21=e2.dot(e1);den=d00*d11-d01*d01
    u=(d11*d20-d01*d21)/den if abs(den)>1e-12 else 0;v=(d00*d21-d01*d20)/den if abs(den)>1e-12 else 0
    ws={}
    for idx,f in zip(ids,[max(0,1-u-v),max(0,u),max(0,v)]):
        for g in body.data.vertices[idx].groups:ws[groups[g.group]]=ws.get(groups[g.group],0)+g.weight*f
    # Continuous head blend does not sever collar weights at a slot boundary.
    t=np.clip((co.z-1.18)/.14,0,1)*np.clip((.23-abs(co.x))/.05,0,1);t=float(t*t*(3-2*t))
    ws={n:w*(1-t) for n,w in ws.items()};ws['Head']=ws.get('Head',0)+t
    # Preserve continuous tassets at centre: upper skirt follows pelvis, transition to each thigh at lower hem.
    if .50<co.z<.76 and abs(co.x)<.235:
        t=float(np.clip((co.z-.50)/.16,0,1));t=t*t*(3-2*t)
        ws={n:w*(1-t) for n,w in ws.items()};ws['pelvis']=ws.get('pelvis',0)+t
    ws=dict(sorted(ws.items(),key=lambda q:q[1],reverse=True)[:4]);total=sum(ws.values());assert total>0
    return {n:w/total for n,w in ws.items() if w>0}

for v in raw.data.vertices:
    for name,w in weights(v.co).items():(raw.vertex_groups.get(name) or raw.vertex_groups.new(name=name)).add([v.index],w,'REPLACE')
mod=raw.modifiers.new('Original Dwarf armature','ARMATURE');mod.object=rig;mw=raw.matrix_world.copy();raw.parent=rig;raw.matrix_world=mw
shader.inputs['Emission Strength'].default_value=0
# Glove coverage is derived from the actual hands; original finger weights and contact remain.
glove=body.copy();glove.data=body.data.copy();glove.name='L7_Gloves';bpy.context.collection.objects.link(glove)
handgroups={g.index for g in glove.vertex_groups if any(x in g.name for x in ['hand_','thumb_','index_','middle_','pinky_','ring_'])}
keep=[]
for f in glove.data.polygons:
    influence=sum(sum(g.weight for g in glove.data.vertices[i].groups if g.group in handgroups) for i in f.vertices)/len(f.vertices)
    centre=sum((glove.matrix_world@glove.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
    keep.append(influence>.72 or (abs(centre.x)>.337 and centre.z<.80))
bm=bmesh.new();bm.from_mesh(glove.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if not keep[f.index]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(glove.data);bm.free()
for v in glove.data.vertices:v.co+=v.normal*.0025
leather=glove.data.materials[0].copy();leather.name='Dwarf oxblood leather gloves';bs=next(n for n in leather.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
# Use original textured colour detail, confined to new glove shells.
for link in list(bs.inputs['Metallic'].links):leather.node_tree.links.remove(link)
bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.74
if bs.inputs['Base Color'].links:
    src=bs.inputs['Base Color'].links[0].from_socket;mix=leather.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.18,.075,.045,1);leather.node_tree.links.new(src,mix.inputs[1]);leather.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
glove.data.materials.clear();glove.data.materials.append(leather)
assert all(signature(o)==before[o.name] for o in original)
# Save editable source before export; assembly merge preserves exact original animations.
bpy.ops.wm.save_as_mainfile(filepath=str(R/'L7-fit.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,raw,glove]:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'L7-addon.glb'),export_format='GLB',use_selection=True,export_animations=False,export_tangents=True)
report={'originalSignatures':before,'originalVerticesWeightsUnchanged':True,'donorDeletedFaces':len(remove),'newTriangles':sum(len(f.vertices)-2 for o in [raw,glove] for f in o.data.polygons),'scale':[1.32,1.44,1.44],'scope':'unaccepted first fit; original visible face/hands; donor wardrobe replaces visible clothed surfaces'}
(R/'fit-report.json').write_text(json.dumps(report,indent=2))
for f in ['L7-fit.blend','L7-addon.glb','fit-report.json']:api.upload_file(path_or_fileobj=str(R/f),path_in_repo='ranks/L7/'+f,repo_id=REPO,repo_type='dataset')
print('FIT_SAVED',json.dumps(report),flush=True)


from merge_armour import merge
from repair_weights import repair
from finish_materials import finish
final=R/'dwarf-L7.glb'
report=merge(R/'original.glb',R/'L7-addon.glb',final)
repair(final)
finish(final)
assert final.exists()
api.upload_file(path_or_fileobj=str(final),path_in_repo='ranks/L7/dwarf-L7.glb',repo_id=REPO,repo_type='dataset')
api.upload_file(path_or_fileobj=json.dumps(report).encode(),path_in_repo='ranks/L7/merge-report.json',repo_id=REPO,repo_type='dataset')
print('FINAL_MODEL_PERSISTED',hashlib.sha256(final.read_bytes()).hexdigest(),flush=True)
"""Reimport exported GLBs and capture matched CPU studio views."""

import hashlib
import json
import os
import urllib.request
from pathlib import Path

import bpy
from mathutils import Vector
from huggingface_hub import HfApi, get_token, hf_hub_url

REPO = "Domlynch/frankendom-dwarf-ranks-20260928"
OUT = Path("/tmp/dwarf-renders")
OUT.mkdir(exist_ok=True)
api = HfApi()
revision = api.repo_info(REPO, repo_type="dataset").sha
receipts = []
from bpy_extras.object_utils import world_to_camera_view
import importlib.metadata
runtime={p:importlib.metadata.version(p) for p in ["bpy","huggingface_hub","numpy"]}
api.upload_file(path_or_fileobj=json.dumps(runtime).encode(),path_in_repo="ranks/L7/runtime.json",repo_id=REPO,repo_type="dataset")
for label, filename in [("L7", "ranks/L7/dwarf-L7.glb")]:
    path = Path('/tmp/dwarf-fit/dwarf-L7.glb')
    sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(path))
    rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8
    scene.render.resolution_x = 375
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new("Neutral studio")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
        0.18,
        0.18,
        0.18,
        1,
    )
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    target = Vector((0, 0, 0.75))
    bpy.ops.object.camera_add(location=(0, -6, 1.1))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.95
    scene.camera = camera
    for xyz, power, size in [
        ((-3, -4, 5), 650, 3),
        ((3, -2, 3), 220, 3),
        ((1, 2, 4), 450, 2),
    ]:
        bpy.ops.object.light_add(type="AREA", location=xyz)
        light = bpy.context.object
        light.data.energy = power
        light.data.size = size
        light.rotation_euler = (
            (target - light.location).to_track_quat("-Z", "Y").to_euler()
        )
    for view, clip, time in [
        ("rest", None, 0),
        ("front", "Warhammer_Idle", 0.35),
        ("side", "Warhammer_Idle", 0.35),
        ("back", "Warhammer_Idle", 0.35),
        ("attack", "Warhammer_Heavy", 0.45),
        ("guard", "Warhammer_Guard", 0.4),
        ("kick", "Kick", 0.4),
        ("fight", "Warhammer_Idle", 0.35),
    ]:
        action = bpy.data.actions.get(clip) if clip else None
        assert action or clip is None, clip
        rig.animation_data.action = action
        if action and len(action.slots):
            rig.animation_data.action_slot = action.slots[0]
        scene.frame_set(round(time * scene.render.fps))
        camera.location = (6, 0, 0.9) if view == "side" else (0, 6 if view == "back" else -6, 0.9)
        camera.rotation_euler = (
            (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        )
        camera.data.ortho_scale = 8.2 if view == "fight" else 1.95
        output = OUT / f"{label}-{view}.png"
        scene.render.filepath = str(output)
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
        api.upload_file(
            path_or_fileobj=str(output),
            path_in_repo="ranks/L7/renders/" + output.name,
            repo_id=REPO,
            repo_type="dataset",
        )
        deps=bpy.context.evaluated_depsgraph_get()
        projected=[]
        for o in scene.objects:
            if o.type=="MESH" and (o.name.startswith("L7_") or o.name=="CreatureBody"):
                evaluated=o.evaluated_get(deps)
                projected.extend(world_to_camera_view(scene,camera,evaluated.matrix_world@Vector(c)).y*600 for c in evaluated.bound_box)
        figure_height=max(projected)-min(projected)
        receipts.append(
            {
                "model": filename,
                "sha256": sha,
                "image": output.name,
                "clip": clip,
                "frame": scene.frame_current,
                "camera": list(camera.location),
                "orthoScale": camera.data.ortho_scale,
                "viewport": [375, 600],
                "figureHeightPx": figure_height,
                "scope": "CPU studio render; not gameplay or physical phone performance",
            }
        )
        print("CAPTURED", output.name, flush=True)
(OUT / "render-receipt.json").write_text(json.dumps(receipts, indent=2))
api.upload_file(
    path_or_fileobj=str(OUT / "render-receipt.json"),
    path_in_repo="ranks/L7/render-receipt.json",
    repo_id=REPO,
    repo_type="dataset",
)
print("RENDER_COMPLETE", flush=True)
os._exit(0)
