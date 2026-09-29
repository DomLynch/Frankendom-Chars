from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];D=R/'delivery';manifest=json.loads((D/'manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert len(manifest)==9
for row in manifest:
 p=D/row['model'];assert sha(p)==row['sha256'];receipt=json.loads((D/f'reports/L{row["rank"]}-render-receipt.json').read_text());assert len(receipt)==10 and all(x['sha256']==row['sha256'] for x in receipt)
checks=json.loads((D/'reports/final-validation.json').read_text());formats=json.loads((D/'reports/final-format-validation.json').read_text());deform=json.loads((D/'reports/final-deformation-expanded.json').read_text());coverage=json.loads((D/'reports/final-coverage.json').read_text())
assert len(checks)==len(formats)==9 and all(x['errors']==0 for x in formats)
assert len(deform)==3 and all(x['worstLongEdgeCount']==0 for x in deform)
assert len(coverage)==3
for x in deform:assert x['sha256']==next(y['sha256'] for y in manifest if Path(y['model']).name==Path(x['file']).name)
assert json.loads((D/'reports/final-preservation.json').read_text())['allUnchanged']
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v and not v.startswith(('#','http','data:')):assert (D/'review'/v).resolve().is_file(),v
Links().feed((D/'review/index.html').read_text())
for p in (D/'source').glob('*.py'):compile(p.read_text(),str(p),'exec')
files=sorted(p for p in D.rglob('*') if p.is_file() and p.name!='CHECKSUMS.sha256');hashes={str(p.relative_to(D)):sha(p) for p in files};(D/'CHECKSUMS.sha256').write_text('\n'.join(h+'  '+n for n,h in hashes.items())+'\n')
archive=R/'nightborn-L2-L10-covered-review.zip';tmp=archive.with_suffix('.tmp.zip')
with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,'nightborn-L2-L10/'+str(p.relative_to(D)))
with zipfile.ZipFile(tmp) as z:
 assert z.testzip() is None
 for n,h in hashes.items():assert hashlib.sha256(z.read('nightborn-L2-L10/'+n)).hexdigest()==h
 assert len([n for n in z.namelist() if '/models/' in n and n.endswith('.glb')])==9
 members=len(z.namelist())
tmp.replace(archive);result={'archive':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size,'members':members,'crcPassed':True,'allContainedFileHashesPassed':True,'models':9,'captures':90};(R/'reports/archive-integrity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
