"""Offline publication integrity checks; no generation, remote writes or billing."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET = re.compile(rb'(?:hf_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')


def main():
    catalog = json.loads((ROOT / 'catalog.json').read_text())
    assert {c['id'] for c in catalog['characters']} == {'witch', 'knight', 'dwarf', 'nightborn', 'plaguedoctor'}
    archives = {a['name']: a for a in catalog['archives']}
    assert len(archives) == 6
    count = previews = 0
    for case in catalog['characters']:
        assert json.loads((ROOT / 'characters' / case['id'] / 'manifest.json').read_text()) == case
        assert [m['rank'] for m in case['models']] == list(range(2, 11))
        for model in case['models']:
            assert model['archive'] in archives
            assert re.fullmatch('[a-f0-9]{64}', model['sha256'])
            assert model['bytes'] > 0 and model['joints'] > 0 and model['animations'] > 0
            assert model['previewEvidence']
            for capture in model['previewEvidence']:
                image = ROOT / capture['path']
                assert hashlib.sha256(image.read_bytes()).hexdigest() == capture['sha256'], image
                previews += 1
            count += 1
    assert count == 45
    for archive in archives.values():
        assert re.fullmatch('[a-f0-9]{64}', archive['sha256'])
        assert archive['url'].endswith('/' + archive['name'])
        assert archive['crcVerified'] is True
    handover = (ROOT / 'docs/GPT-WEB-HANDOVER.md').read_text()
    assert [int(x) for x in re.findall(r'^(\d+)\. ', handover, re.M)] == list(range(1, 31))
    own_docs = [ROOT / 'README.md', *ROOT.glob('docs/*.md'), *ROOT.glob('characters/*/README.md')]
    for doc in own_docs:
        for target in re.findall(r'\]\(([^)]+)\)|(?:src|href)="([^"]+)"', doc.read_text()):
            link = target[0] or target[1]
            if '://' not in link and not link.startswith('#'):
                assert (doc.parent / link.split('#')[0]).exists(), f'Broken link: {doc} -> {link}'
    scripts = 0
    for path in ROOT.rglob('*'):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(p in {'.git', '.codegraph', '.semble', '__pycache__', 'downloads', 'work'} for p in rel.parts):
            continue
        if path.suffix in {'.md', '.json', '.py', '.cjs', '.js', '.yml', '.yaml', '.txt', '.toml', '.sh'}:
            data = path.read_bytes()
            assert not SECRET.search(data), f'Potential credential in {rel}'
            if path.suffix == '.py':
                ast.parse(data, filename=str(rel))
                scripts += 1
    print(f'PASS: {count} models, {previews} previews, 6 archive receipts, 30 handover points; links/credential scan/{scripts} Python syntax checks')


if __name__ == '__main__':
    main()
