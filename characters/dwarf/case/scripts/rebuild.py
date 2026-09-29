"""Rebuild selected candidates from bundled immutable inputs, checking exact hashes."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
selected = json.loads((ROOT / "selected.json").read_text())
ranks = sys.argv[1:] or list(selected)
receipts = []
with tempfile.TemporaryDirectory(prefix="dwarf-rebuild-") as temp:
    work = Path(temp)
    shutil.copytree(ROOT / "sources/targeted-input", work, dirs_exist_ok=True)
    for rank in ranks:
        output = ROOT / "rebuilt" / f"dwarf-{rank}.glb"
        output.parent.mkdir(exist_ok=True)
        if rank in ["L8", "L9", "L10"]:
            command = [sys.executable, str(ROOT / "scripts/patch_existing.py"), rank, "--root", str(work)]
        else:
            command = [sys.executable, str(ROOT / "scripts/rebuild_worker.py"), rank, str(output)]
        subprocess.run(command, check=True, capture_output=True, text=True, env={**os.environ, "OPENBLAS_NUM_THREADS": "1"})
        if rank in ["L8", "L9", "L10"]:
            shutil.copy2(work / f"elite-correction/targeted/{rank}/dwarf-{rank}.glb", output)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        assert digest == selected[rank]["sha256"], (rank, digest, selected[rank]["sha256"])
        receipts.append(dict(rank=rank, sha256=digest, exactHashMatch=True))
        print("EXACT_REBUILD", rank, digest, flush=True)
(ROOT / "reports/rebuild-verification.json").write_text(json.dumps(receipts, indent=2))
