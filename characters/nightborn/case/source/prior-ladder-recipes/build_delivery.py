"""Assemble only selected candidates and exact-hash review evidence; no rejected fits."""
from pathlib import Path
import shutil,json,hashlib,io,sys,html
from PIL import Image,ImageDraw
from glb_checks import read
R=Path(__file__).resolve().parents[1];D=R/'delivery';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(p,relative):
 target=D/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);return target
palette={2:'Brown leather',3:'Bone and hide',4:'Copper',5:'Bronze',6:'Iron',7:'Steel',8:'Blackened steel and ruby',9:'Emerald',10:'Full gold'}
views=['front','back','side','attack','guard','kick','phone','fight','rest','head'];manifest=[]
def image_data(m,b,i):
 x=m['images'][i];v=m['bufferViews'][x['bufferView']];return b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
def image_metric(data):
 im=Image.open(io.BytesIO(data));return {'width':im.width,'height':im.height,'format':im.format,'pixelSha256':hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()}
for rank in range(2,11):
 model=copy(R/f'models/nightborn-L{rank}.glb',f'models/nightborn-L{rank}.glb');m,b=read(model);h=sha(model)
 source=R/('review/pilot-v8' if rank==8 else f'review/ladder/L{rank}' if rank==9 else f'review/corrected/L{rank}')
 copy(source/model.with_suffix('.blend').name,f'sources/L{rank}/nightborn-L{rank}.pre-repair.blend')
 copy(source/'build.json',f'sources/L{rank}/build.json');copy(source/'deformation.json',f'sources/L{rank}/preliminary-deformation.json')
 recipe='build_pilot_v8.py' if rank==8 else 'build-L9.py' if rank==9 else f'corrected-L{rank}.py'
 copy(R/'source'/recipe,f'source/{recipe}')
 copy(R/f'source/L{rank}-reference.png',f'sources/L{rank}/reference.png')
 donor=R/f'src/assets/source/creatures/nightborn-L{rank}-donor.glb';copy(donor,f'sources/L{rank}/donor.glb');copy(donor.with_suffix('.trellis.json'),f'sources/L{rank}/reconstruction.json')
 receipts=json.loads((R/f'review/final/L{rank}-render-receipt.json').read_text());assert len(receipts)==10
 assert {x['image'] for x in receipts}=={f'L{rank}-{v}.png' for v in views}
 assert all(x['sha256']==h for x in receipts)
 for x in receipts:
  assert x.get('deformation') is None or x['deformation']['longStretchedEdges']==0,(rank,x)
  if x['image'].endswith('-fight.png'):assert abs(x['projectedArmourHeightPx']-110)<.01
  copy(R/'review/final/renders'/x['image'],'review/renders/'+x['image'])
 copy(R/f'review/final/L{rank}-render-receipt.json',f'reports/L{rank}-render-receipt.json')
 def meshtris(mesh):return sum(m['accessors'][p['indices']]['count']//3 for p in mesh['primitives'])
 active=[n for n in m['nodes'] if 'mesh'in n];inactive=[n for n in m['nodes'] if 'preservedInactiveMesh'in n.get('extras',{})]
 textures=[dict(index=i,mimeType=x.get('mimeType'),**image_metric(image_data(m,b,i))) for i,x in enumerate(m['images'])]
 dm,db=read(donor);arm=next(x for x in m['meshes'] if x.get('name')=='Mesh_0') if False else m['meshes'][next(n['mesh'] for n in active if n['name']==f'L{rank}_Armour')]
 mat=m['materials'][arm['primitives'][0]['material']];dmat=dm['materials'][dm['meshes'][0]['primitives'][0]['material']]
 def pixels_for(mm,bb,material,key):
  idx=material.get('pbrMetallicRoughness',{}).get(key,{}).get('index')
  if idx is None:return None
  tex=mm['textures'][idx];source=tex.get('source',tex.get('extensions',{}).get('EXT_texture_webp',{}).get('source'));return image_metric(image_data(mm,bb,source))['pixelSha256']
 baseSame=pixels_for(m,b,mat,'baseColorTexture')==pixels_for(dm,db,dmat,'baseColorTexture');assert baseSame
 item={'rank':rank,'direction':palette[rank],'model':str(model.relative_to(D)),'sha256':h,'bytes':model.stat().st_size,'trianglesAllStoredMeshes':sum(map(meshtris,m['meshes'])),'trianglesActiveMeshInstances':sum(meshtris(m['meshes'][n['mesh']]) for n in active),'storedMeshes':len(m['meshes']),'activeMeshInstances':len(active),'activePrimitiveInstances':sum(len(m['meshes'][n['mesh']]['primitives']) for n in active),'storedMaterials':len(m['materials']),'inactiveOriginalNodes':[n['name'] for n in inactive],'animations':len(m['animations']),'joints':len(m['skins'][0]['joints']),'donorSha256':sha(donor),'textures':textures,'armourMaterial':mat,'donorArmourMaterial':dmat,'donorBaseColorPixelsPreserved':baseSame,'metallicRoughnessPixelsPreserved':pixels_for(m,b,mat,'metallicRoughnessTexture')==pixels_for(dm,db,dmat,'metallicRoughnessTexture'),'materialChanges':'Emission disabled; L2/L3 metallic factor forced 0. Authored crown/gloves separate.','renderCount':len(receipts),'status':'isolated review candidate; production integration pending'}
 manifest.append(item)
for p in (R/'original').iterdir():copy(p,'original/'+p.name)
for name in ['validate.py','preserve_clips.py','glb_checks.py','format_check.cjs','render_final.py','batched_upload.py','submit.py','prepare_rank.py','prepare_correction.py','prepare_batch.py','finalize.py','build_delivery.py','seal_delivery.py','remove_l3_fragment.py','export_scene.py','package.json','requirements-build.txt','requirements-checks.txt','trellis2.py']:
 copy(R/'source'/name,'source/'+name)
for p in (R/'reports').glob('*.json'):
 if p.name.startswith('job-') or p.name in ['glove-region-defect.json']:continue
 copy(p,'reports/'+p.name)
for p in (R/'reports/submitted').glob('*.py'):
 if p.name in []:pass
# Final scripts and job receipts identify exact executed versions.
for name in ['render-final-3.py','render-final-3-4-5.py','render-final-6-7-10.py']:copy(R/'source'/name,'source/'+name)
for name in ['persist-corrected-2-3-4.py','persist-corrected-5-6.py','persist-corrected-7-10.py','persist-render-final-2-8-9.py']:
 if (R/'source'/name).exists():copy(R/'source'/name,'source/'+name)
copy(R/'reports/PILOT-ACCEPTANCE.md','reports/PILOT-ACCEPTANCE.md')
(D/'manifest.json').write_text(json.dumps(manifest,indent=2))
# Contact sheets use actual final captures, without generated repainting.
for name,cols,vs,ranks,w,h in [('front-ladder',3,['front'],list(range(2,11)),300,480),('front-back',6,['front','back'],list(range(2,11)),260,420),('elite-heads',3,['head'],[8,9,10],400,445),('phone-ladder',3,['phone'],list(range(2,11)),375,635)]:
 cells=[(rank,v) for rank in ranks for v in vs];rows=(len(cells)+cols-1)//cols;sheet=Image.new('RGB',(cols*w,rows*h),(26,28,30));draw=ImageDraw.Draw(sheet)
 for i,(rank,v) in enumerate(cells):
  im=Image.open(D/f'review/renders/L{rank}-{v}.png');im.thumbnail((w,h-35));x=(i%cols)*w;y=(i//cols)*h;sheet.paste(im,(x+(w-im.width)//2,y+35));draw.text((x+10,y+10),f'L{rank} | {palette[rank]} | {v}',fill='white')
 sheet.save(D/f'review/{name}.jpg',quality=94)
for rank in range(2,11):
 vs=['side','attack','guard','kick','fight'];sheet=Image.new('RGB',(1250,420),(26,28,30));draw=ImageDraw.Draw(sheet)
 for i,v in enumerate(vs):
  im=Image.open(D/f'review/renders/L{rank}-{v}.png');im.thumbnail((250,385));sheet.paste(im,(i*250+(250-im.width)//2,35));draw.text((i*250+10,10),f'L{rank} {v}',fill='white')
 sheet.save(D/f'review/L{rank}-motion.jpg',quality=94)
rows=''.join(f'<tr><td>L{x["rank"]}</td><td>{x["direction"]}</td><td><a href="../{x["model"]}">GLB</a></td><td>{x["bytes"]/1e6:.2f} MB</td><td>{x["trianglesActiveMeshInstances"]:,}</td><td>10</td></tr>' for x in manifest)
cards=''.join(f'<section id="l{x["rank"]}"><h2>L{x["rank"]} · {x["direction"]}</h2><p><a href="../{x["model"]}">Download model</a> · <a href="../reports/L{x["rank"]}-render-receipt.json">Capture receipt</a> · <code>{x["sha256"][:16]}</code></p><div class="grid">'+''.join(f'<figure><a href="renders/L{x["rank"]}-{v}.png"><img loading="lazy" src="renders/L{x["rank"]}-{v}.png" alt="L{x["rank"]} {v}"></a><figcaption>{v}</figcaption></figure>' for v in views)+'</div></section>' for x in manifest)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nightborn · L2–L10 review</title><style>body{background:#151719;color:#e7e5dd;font:16px/1.55 system-ui;margin:0 auto;max-width:1400px;padding:32px}a{color:#cbbb88}h1,h2{letter-spacing:.02em}h1{font-size:40px;margin-bottom:6px}p{max-width:1000px}.tag{color:#cbbb88}table{border-collapse:collapse;width:100%;margin:25px 0}td,th{text-align:left;border-bottom:1px solid #43433e;padding:10px}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}figure{margin:0}img{width:100%;display:block}figcaption{padding:5px;color:#bfc2c4}.hero{max-width:900px}.note{border-left:3px solid #a99260;padding-left:18px}section{border-top:1px solid #43433e;padding-top:25px;margin-top:35px}code{font-size:12px}@media(max-width:750px){body{padding:16px}.grid{grid-template-columns:repeat(2,1fr)}h1{font-size:30px}td,th{padding:5px;font-size:12px}}</style><p class="tag">FRANKENDOM · ISOLATED CHARACTER CANDIDATES · 28 SEPTEMBER 2026</p><h1>Nightborn, ranks L2–L10</h1><p>Nine distinct armour candidates. Original open face, hair, ears, estoc, rig and 25 animation clips retained. Every image below comes from the final exported model identified in its receipt.</p><p class="note">Review candidates only. Original face and hair retain pronounced faceting; armour retains reconstruction roughness. Six-slot carriers, helmet removal/finishers, continuous collision clearance, actual arena behaviour and physical-phone performance remain unproved. The 375px and 110px figure captures are neutral studio approximations.</p><p><a href="../HANDOFF.md">Build notes and limitations</a> · <a href="../manifest.json">Manifest</a> · <a href="front-back.jpg">Full front/back sheet</a> · <a href="elite-heads.jpg">Elite crowns</a> · <a href="phone-ladder.jpg">375px sheet</a></p><img class="hero" src="front-ladder.jpg" alt="Nine final Nightborn rank models"><table><tr><th>Rank</th><th>Material</th><th>Candidate</th><th>Size</th><th>Active triangles</th><th>Views</th></tr>'''+rows+'</table>'+cards+'</html>'
(D/'review/index.html').write_text(page)

r=D/'review'
for ranks in [[2,3,4],[5,6,7],[8,9,10]]:
 sheet=Image.new('RGB',(1250,1260))
 for i,rank in enumerate(ranks):sheet.paste(Image.open(r/f'L{rank}-motion.jpg'),(0,i*420))
 sheet.save(r/f'motion-{ranks[0]}-{ranks[-1]}.jpg',quality=94)
for view in ['rest','head']:
 sheet=Image.new('RGB',(900,990),(26,28,30));draw=ImageDraw.Draw(sheet)
 for i,rank in enumerate(range(2,11)):
  im=Image.open(r/f'renders/L{rank}-{view}.png');im.thumbnail((300,300));x=(i%3)*300;y=(i//3)*330;sheet.paste(im,(x+(300-im.width)//2,y+30));draw.text((x+10,y+10),f'L{rank} {view}',fill='white')
 sheet.save(r/f'all-{view}.jpg',quality=94)

print('PACK_ASSEMBLED',D)
