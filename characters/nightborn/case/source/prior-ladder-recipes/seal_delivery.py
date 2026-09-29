from pathlib import Path
import json,hashlib,zipfile,py_compile
from html.parser import HTMLParser
from collections import Counter
R=Path(__file__).resolve().parents[1];D=R/'delivery';manifest=json.loads((D/'manifest.json').read_text());validation=json.loads((D/'reports/validation.json').read_text());formats=json.loads((D/'reports/format-validation.json').read_text());jobs=json.loads((D/'reports/owned-jobs.json').read_text());counts=dict(Counter(x['stage'] for x in jobs));assert not any(x['stage'] in ['RUNNING','PENDING','PAUSED'] for x in jobs)
assert len(manifest)==len(validation)==len(formats)==9 and all(x['errors']==0 for x in formats)
proof=f"Final receipt: **9/9 candidates; 90/90 hash-matched captures; 0 GLB format errors.** 11–16 hierarchy/generated-tangent warnings per file remain. Maximum joint-matrix delta is {max(x['maxJointMatrixDelta'] for x in validation):.5g} across 2,025 sampled poses. All documented final Armed/Heavy/Guard/Kick samples have zero qualifying long stretched edges. Owned HF job states: {counts}; no owned job remains active. Actual charges were not measured.\n"
text=(R/'HANDOFF-DRAFT.md').read_text().replace('## Evidence and limits','## Evidence and limits\n\n'+proof);(D/'HANDOFF.md').write_text(text)
rows=['# Rank completion matrix','','| Rank | Direction | Stored / active triangles | Size | Format | Exact clips | Final captures | Status |','|---|---|---:|---:|---|---|---|---|']
for x in manifest:
 rows.append(f'| L{x["rank"]} | {x["direction"]} | {x["trianglesAllStoredMeshes"]:,} / {x["trianglesActiveMeshInstances"]:,} | {x["bytes"]/1e6:.2f} MB | 0 errors | 25/25 | 10/10 | Review candidate |')
 p=D/x['model'];h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==x['sha256'];assert next(v for v in validation if Path(v['file']).name==p.name)['sha256']==h
 receipts=json.loads((D/f'reports/L{x["rank"]}-render-receipt.json').read_text());assert len(receipts)==10 and all(v['sha256']==h for v in receipts)
rows+=['','Active triangles count mesh instances, not measured runtime draw cost. Body/Arms/Greaves/Boots are combined armour; glove/cuff and crown geometry is separate. No six-slot carrier integration is claimed. Original faceted face, rough cuff/neck junctions and continuous/game/phone proof remain open. See HANDOFF.md.'];(D/'RANK-MATRIX.md').write_text('\n'.join(rows))
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v and not v.startswith(('#','http','data:')):assert (D/'review'/v).resolve().is_file(),v
Links().feed((D/'review/index.html').read_text())
for p in (D/'source').glob('*.py'):compile(p.read_text(),str(p),'exec')
review={'candidateCount':9,'captureCount':90,'modelAndReceiptHashesMatch':True,'allGalleryLocalLinksResolve':True,'sourceScriptsCompile':True,'originalSourceHashUnchanged':json.loads((D/'reports/preservation-final.json').read_text())['sourceBodyUnchanged'],'reviewedSheets':['front-back','elite-heads','phone-ladder','all-rest','all-head','motion-2-4','motion-5-7','motion-8-10'],'lateCorrection':'L3 disconnected waist fragment removed; final ten views regenerated','remainingDefects':['Original face/hair faceting','Rough cuff and neck junctions','Simple authored crown surface detail','No slot/finisher/continuous clearance/arena/physical phone validation'],'acceptance':'Complete isolated review package, not production approval'};(D/'reports/delivery-audit.json').write_text(json.dumps(review,indent=2))
files=sorted(p for p in D.rglob('*') if p.is_file() and p.name!='CHECKSUMS.sha256');hashes={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(D/'CHECKSUMS.sha256').write_text('\n'.join(h+'  '+name for name,h in hashes.items())+'\n')
archive=R/'nightborn-L2-L10-review.zip';tmp=archive.with_suffix('.tmp.zip')
with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,'nightborn-L2-L10/'+str(p.relative_to(D)))
with zipfile.ZipFile(tmp) as z:
 assert z.testzip() is None
 for name,h in hashes.items():assert hashlib.sha256(z.read('nightborn-L2-L10/'+name)).hexdigest()==h,name
 assert len([n for n in z.namelist() if '/models/'in n and n.endswith('.glb')])==9
 assert not any('before-animation' in n or '/pilot-v' in n or '/__pycache__/'in n for n in z.namelist())
tmp.replace(archive);receipt={'archive':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'verifiedFiles':len(hashes)+1,'candidateModels':9,'crcPassed':True,'allContainedFileHashesPassed':True};(R/'reports/archive-integrity.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
