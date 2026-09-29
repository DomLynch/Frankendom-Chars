"""Create the review archive and verify every archived file hash and CRC."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = sorted(p for p in ROOT.rglob("*") if p.is_file() and not any(x in {"rebuilt", "__pycache__", ".DS_Store"} for x in p.relative_to(ROOT).parts) and p.name != "checksums.json")
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
manifest = ROOT / "checksums.json"
manifest.write_text(json.dumps(hashes, indent=2))
files.append(manifest)
archive = ROOT.parent / "dwarf-L2-L10-helmet-coverage-candidates.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
    for path in files:
        z.write(path, "delivery/" + str(path.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
    assert len(z.infolist()) == len(files)
    for name, expected in hashes.items():
        digest = hashlib.sha256()
        with z.open("delivery/" + name) as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        assert digest.hexdigest() == expected, name
    assert json.loads(z.read("delivery/checksums.json")) == hashes
digest = hashlib.sha256()
with archive.open("rb") as stream:
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
receipt = dict(archive=archive.name, bytes=archive.stat().st_size, sha256=digest.hexdigest(), members=len(files), allFileHashesVerified=True, fullReadCRCVerified=True)
(ROOT.parent / "delivery-final-archive-verification.json").write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt), flush=True)
