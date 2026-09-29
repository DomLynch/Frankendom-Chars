"""Read-only preservation and asset inventory for the nine selected candidates."""
from pathlib import Path
import hashlib
import io
import json
import sys

import numpy as np
from PIL import Image
from pack_preserved import read, arr

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'delivery'
g, binary = read(ROOT / 'source/original.glb')
reports = []
motion = {r['rank']: r for r in json.loads((ROOT / 'checks/motion.json').read_text())}
for rank in range(2, 11):
    path = ROOT / f'models/knight-L{rank}.glb'
    d, db = read(path)
    assert db[:len(binary)] == binary
    assert d['animations'] == g['animations']
    assert d['nodes'][:len(g['nodes'])] == g['nodes']
    assert d['skins'] == g['skins']
    assert d['accessors'][:len(g['accessors'])] == g['accessors']
    counts = []
    for mesh in d['meshes']:
        triangles = 0
        for p in mesh['primitives']:
            a = p['attributes']
            pos = arr(d, db, a['POSITION'])
            assert np.isfinite(pos).all()
            triangles += len(arr(d, db, p['indices'])) // 3 if 'indices' in p else len(pos) // 3
            if 'WEIGHTS_0' in a:
                w = arr(d, db, a['WEIGHTS_0'])
                assert (w >= 0).all() and np.isfinite(w).all()
                assert np.max(np.abs(w.sum(1) - 1)) < 2e-4
                assert arr(d, db, a['JOINTS_0']).max() < len(d['skins'][0]['joints'])
        counts.append(triangles)
    textures = []
    for im in d.get('images', []):
        v = d['bufferViews'][im['bufferView']]
        off = v.get('byteOffset', 0)
        with Image.open(io.BytesIO(db[off:off + v['byteLength']])) as img:
            textures.append({'size': list(img.size), 'format': img.format})
    assert any(x['size'] == [2048, 2048] for x in textures)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    assert motion[rank]['sha256'] == sha
    assert motion[rank]['maxLongStretchedEdgeOccurrences'] == 0
    captures = json.loads((ROOT / f'review/L{rank}/render-receipt.json').read_text())
    assert len(captures) == 7
    for c in captures:
        assert c['sha256'] == sha
        image = ROOT / f'review/L{rank}' / c['image']
        assert hashlib.sha256(image.read_bytes()).hexdigest() == c['imageSha256']
    fight = next(c for c in captures if c['image'].endswith('-fight.png'))
    assert abs(fight['projectedArmourHeightPx'] - 110) < .01
    node = next(n for n in d['nodes'] if n.get('name') == f'Knight_L{rank}_Armour')
    armour = d['meshes'][node['mesh']]
    mats = [d['materials'][p['material']] for p in armour['primitives']]
    assert all(not any(m.get('emissiveFactor', [0, 0, 0])) for m in mats)
    source_donor = ROOT / f'source/L{rank}/donor.glb'
    donor, _ = read(source_donor)
    pbr = mats[0].get('pbrMetallicRoughness', {})
    source_pbr = donor['materials'][0].get('pbrMetallicRoughness', {})
    if rank not in [2, 3]:
        defaults = {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 1, 'roughnessFactor': 1}
        for key in ['baseColorFactor', 'metallicFactor', 'roughnessFactor']:
            assert pbr.get(key, defaults[key]) == source_pbr.get(key, defaults[key]), (rank, key, pbr.get(key), source_pbr.get(key))
    reports.append({
        'rank': rank, 'file': str(path.relative_to(ROOT)), 'sha256': sha,
        'bytes': path.stat().st_size, 'uniqueMeshTriangles': sum(counts),
        'newArmourTrianglesIncludingSourceGloves': counts[node['mesh']],
        'meshCount': len(d['meshes']), 'materialCount': len(d['materials']),
        'textures': textures, 'clips': len(d['animations']), 'joints': len(d['skins'][0]['joints']),
        'originalBinaryNodesSkinAccessorsAnimationsExact': True,
        'normalizedWeightsFiniteGeometry': True, 'hashMatchedCaptures': len(captures),
        'fightArmourHeightPx': fight['projectedArmourHeightPx'],
        'materialScalarComparison': 'PASS; L2/L3 forced nonmetal; source gloves rank tinted',
        'countsScope': 'Unique mesh totals include retained alpha-zero original body. GPU draw costs unmeasured.',
    })
(ROOT / 'manifest.json').write_text(json.dumps(reports, indent=2))
print(json.dumps({'ranks': len(reports), 'images': sum(r['hashMatchedCaptures'] for r in reports), 'preservation': 'PASS'}))
