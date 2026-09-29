"""Download checksum-pinned release bundles; no credentials or paid calls needed."""
import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def extract_verified(archive, expected_sha, destination):
    """Reject tampered archives and escaping paths before writing any member."""
    if sha256(archive) != expected_sha:
        raise ValueError('Archive checksum mismatch')
    destination = Path(destination).resolve()
    with ZipFile(archive) as bundle:
        for item in bundle.infolist():
            member = Path(item.filename)
            if member.is_absolute() or '..' in member.parts or '\\' in item.filename:
                raise ValueError('Unsafe archive member')
            if not (destination / member).resolve().is_relative_to(destination):
                raise ValueError('Archive member escapes destination')
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Archive symlinks are unsupported')
        bundle.extractall(destination)


def main():
    catalog = json.loads((ROOT / 'catalog.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('character', choices=[c['id'] for c in catalog['characters']])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--downloads', type=Path, default=ROOT / 'downloads')
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('--output must be absent or empty; preserve existing work')
    case = next(c for c in catalog['characters'] if c['id'] == args.character)
    wanted = [case['archive']]
    if args.character == 'witch':
        wanted.append('witch-ranks-sources.zip')
    args.downloads.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='character-download-', dir=args.output.parent) as temp:
        stage = Path(temp)
        for name in wanted:
            receipt = next(a for a in catalog['archives'] if a['name'] == name)
            cached = args.downloads / name
            if not cached.exists():
                partial = stage / (name + '.download')
                with urllib.request.urlopen(receipt['url'], timeout=120) as source:
                    with partial.open('wb') as dest:
                        shutil.copyfileobj(source, dest)
                if sha256(partial) != receipt['sha256']:
                    raise ValueError('Downloaded archive checksum mismatch')
                shutil.move(partial, cached)
            extract_verified(cached, receipt['sha256'], stage / 'unpacked')
        workspace = stage / 'unpacked' / case['archiveRoot']
        for model in case['models']:
            path = stage / 'unpacked' / model['member']
            if sha256(path) != model['sha256']:
                raise ValueError(f"Model checksum mismatch: L{model['rank']}")
        shutil.copytree(stage / 'unpacked', args.output, dirs_exist_ok=True)
        print('Verified 9 models. Workspace:', args.output / case['archiveRoot'])


if __name__ == '__main__':
    main()
