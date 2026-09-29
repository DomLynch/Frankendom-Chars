from pathlib import Path
import json,shutil,hashlib,zipfile,io
from PIL import Image,ImageDraw
from glb_checks import read
R=Path(__file__).resolve().parents[1];O=R.parent/'nightborn-ranks-20260928/delivery';D=R/'delivery';D.mkdir(exist_ok=True)
SELECT={8:'pilot-v5',9:'elites-v2',10:'elites-v1'}
VIEWS=['front','back','side','attack','guard','kick','phone','fight','rest','head']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(p,name):
 q=D/name;q.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,q);return q
manifest=[];old=json.loads((O/'manifest.json').read_text())
for rank in range(2,11):
 label=f'L{rank}';base=O if rank<8 else R/f'review/covered-r2/{SELECT[rank]}-proof'
 p=O/f'models/nightborn-{label}.glb' if rank<8 else R/f'models/{SELECT[rank]}/nightborn-{label}.glb'
 model=cp(p,f'models/{p.name}');h=sha(model)
 receipt=O/f'reports/{label}-render-receipt.json' if rank<8 else base/f'{label}-render-receipt.json';rr=json.loads(receipt.read_text());assert len(rr)==10 and all(x['sha256']==h for x in rr);cp(receipt,f'reports/{receipt.name}')
 for view in VIEWS:cp((O/'review/renders' if rank<8 else base/'renders')/f'{label}-{view}.png',f'review/renders/{label}-{view}.png')
 if rank<8:
  shutil.copytree(O/f'sources/{label}',D/f'sources/{label}',dirs_exist_ok=True);item=next(x for x in old if x['rank']==rank);assert item['sha256']==h
 else:
  m,b=read(model);active=[n for n in m['nodes'] if 'mesh' in n]
  def triangles(mesh):return sum(m['accessors'][x['indices']]['count']//3 for x in mesh['primitives'])
  item={'rank':rank,'direction':{8:'Blackened steel/ruby · closed horned helmet',9:'Emerald · closed finned visor',10:'Full gold · enclosed spiked crown'}[rank],'model':f'models/{p.name}','sha256':h,'bytes':p.stat().st_size,'trianglesAllStoredMeshes':sum(map(triangles,m['meshes'])),'trianglesActiveMeshInstances':sum(triangles(m['meshes'][n['mesh']]) for n in active),'joints':len(m['skins'][0]['joints']),'animations':len(m['animations']),'renderCount':10,'status':'isolated review candidate; integration pending'}
  textures=[]
  for i,image in enumerate(m.get('images',[])):
   bv=m['bufferViews'][image['bufferView']];offset=bv.get('byteOffset',0);im=Image.open(io.BytesIO(b[offset:offset+bv['byteLength']]));textures.append({'index':i,'mimeType':image.get('mimeType'),'width':im.width,'height':im.height,'format':im.format})
  item['textures']=textures;item['activeMaterials']=sorted({m['materials'][pr['material']].get('name','') for n in active for pr in m['meshes'][n['mesh']]['primitives']});item['helmetDonorSha256']=sha(R/f'src/assets/source/creatures/nightborn-{label}-helmet.glb')
  source=R/f"review/covered-r2/{'elites-v1' if rank==9 else SELECT[rank]}/{label}"
  cp(source/f'nightborn-{label}.blend',f'sources/{label}/nightborn-{label}.pre-clip-restoration.blend');cp(source/'build.json',f'sources/{label}/build.json')
  cp(R/f'source/{label}-helmet-reference.png',f'sources/{label}/helmet-reference.png')
  for ext in ['glb','trellis.json']:cp(R/f'src/assets/source/creatures/nightborn-{label}-helmet.{ext}',f'sources/{label}/helmet-donor.{ext}')
  cp(R/f'original/previous-{label}.glb',f'sources/{label}/body-build-input.glb')
 manifest.append(item)
for p in (R/'original').glob('nightborn.glb'):cp(p,'original/'+p.name)
for name in ['validate.py','glb_checks.py','check_coverage.py','check_deformation.py','preserve_clips.py','format_check.cjs','render_final.py','batched_upload.py','submit.py','prove.py','trellis2.py','build_elite.py','build-pilot-v5.py','build-L9.py','build-L10.py','package_corrected.py','seal_corrected.py','final_checks.py','finish_emerald.py']:
 cp(R/'source'/name,'source/'+name)
for p in (O/'source').iterdir():
 if p.is_file():cp(p,'source/prior-ladder-recipes/'+p.name)
for p in (R/'reports').glob('final-*.json'):cp(p,'reports/'+p.name)
cp(R/'reports/L9-material-finish.json','reports/L9-material-finish.json')
cp(R/'reports/PILOT-ACCEPTANCE.md','reports/PILOT-ACCEPTANCE.md')
(D/'manifest.json').write_text(json.dumps(manifest,indent=2))
for name,cols,views,ranks,w,h in [('front-ladder',3,['front'],range(2,11),300,480),('front-back',6,['front','back'],range(2,11),260,420),('elite-heads',3,['head'],[8,9,10],400,440),('phone-ladder',3,['phone'],range(2,11),375,635),('elite-motion',5,['front','back','attack','guard','kick'],[8,9,10],250,400)]:
 cells=[(rank,v) for rank in ranks for v in views];im=Image.new('RGB',(cols*w,((len(cells)+cols-1)//cols)*h),(26,28,30));draw=ImageDraw.Draw(im)
 for i,(rank,v) in enumerate(cells):
  p=Image.open(D/f'review/renders/L{rank}-{v}.png');p.thumbnail((w,h-30));x=(i%cols)*w;y=(i//cols)*h;im.paste(p,(x+(w-p.width)//2,y+30));draw.text((x+10,y+8),f'L{rank} / {v}',fill='white')
 im.save(D/f'review/{name}.jpg',quality=94)
page=(O/'review/index.html').read_text()
a=page.index('<h1>');z=page.index('<table>',a)
page=page[:a]+'''<h1>Nightborn L2–L10 · corrected elites</h1><p>L8–L10 now use closed full-face helmets, covered arms and hands, and armoured legs and feet. Distinct horned, finned and crowned helmets. Original skeleton, estoc and all 25 animation clips retained. L2–L7 model bytes are unchanged.</p><p class="note">Isolated review candidates. Reconstruction roughness and fitted joint transitions remain visible. Continuous clearance, equipment-slot/finisher integration, arena behaviour and physical-phone performance remain unproved. Studio 375px and 110px captures are scale checks.</p><p><a href="../HANDOFF.md">Build and remaining defects</a> · <a href="../manifest.json">Manifest</a> · <a href="front-back.jpg">Front/back</a> · <a href="elite-heads.jpg">Closed elite helmets</a> · <a href="elite-motion.jpg">Elite motion</a> · <a href="phone-ladder.jpg">375px</a></p><img class="hero" src="front-ladder.jpg" alt="Corrected Nightborn ladder">'''+page[z:]
# Rebuild rank table/cards so current hashes and counts replace previous elite metadata.
a=page.index('<table>');page=page[:a]+'<table><tr><th>Rank</th><th>Direction</th><th>Model</th><th>Size</th><th>Active triangles</th></tr>'+''.join(f'<tr><td>L{x["rank"]}</td><td>{x["direction"]}</td><td><a href="../{x["model"]}">GLB</a></td><td>{x["bytes"]/1e6:.2f} MB</td><td>{x["trianglesActiveMeshInstances"]:,}</td></tr>' for x in manifest)+'</table>'
for x in manifest:
 rank=x['rank'];page+=f'<section><h2>L{rank} · {x["direction"]}</h2><p><a href="../{x["model"]}">Model</a> · <a href="../reports/L{rank}-render-receipt.json">Exact-model receipt</a> · {x["sha256"][:16]}</p><div class="grid">'+''.join(f'<figure><a href="renders/L{rank}-{v}.png"><img loading="lazy" src="renders/L{rank}-{v}.png" alt="L{rank} {v}"></a><figcaption>{v}</figcaption></figure>' for v in VIEWS)+'</div></section>'
(D/'review/index.html').write_text(page+'</html>')
cp(R/'HANDOFF.md','HANDOFF.md')
rows=['# Corrected rank matrix','','| Rank | Direction | Exact clips | Verified views |','|---|---|---|---|']+[f'| L{x["rank"]} | {x["direction"]} | 25/25 | 10/10 |' for x in manifest];(D/'RANK-MATRIX.md').write_text('\n'.join(rows)+'\n\nL2–L7 are preserved prior candidates. L8–L10 coverage supersedes previous open-face elites. Integration remains pending.\n')
print(D)
