from pathlib import Path
import sys
import subprocess
import json

R = Path(__file__).resolve().parents[1]
results = []

for rank in [int(x) for x in sys.argv[1:]]:
    name = f"plaguedoctor-L{rank}-donor"
    out = R / f"src/assets/source/creatures/{name}.glb"
    if out.exists():
        continue
    with (R / f"source/L{rank}-reconstruct.log").open("w") as log:
        result = subprocess.run(
            [
                "/Users/domininclynch/.venvs/face/bin/python",
                "/Users/domininclynch/Desktop/Business/frankendom/scripts/character/trellis2.py",
                "--image",
                str(R / f"source/L{rank}-reference.png"),
                "--name",
                name,
                "--seed",
                str(280900 + rank),
                "--resolution",
                "1024",
                "--faces",
                "100000",
                "--texture",
                "2048",
                "--timeout-minutes",
                "0",
            ],
            cwd=R,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    results.append(
        {"rank": rank, "exit": result.returncode, "outputExists": out.exists()}
    )
    print(results[-1], flush=True)
    (R / "generation-batch.json").write_text(json.dumps(results, indent=2))
    if result.returncode:
        break
