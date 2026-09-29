"""Assemble unaltered render pixels into labelled review sheets and HTML."""

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review"
OUT.mkdir(exist_ok=True)
VIEWS = ["front", "back", "attack", "guard", "kick", "fight"]
COLORS = {
    2: "Leather",
    3: "Bone / hide",
    4: "Copper",
    5: "Bronze",
    6: "Iron",
    7: "Steel",
    8: "Black steel / ruby",
    9: "Emerald",
    10: "Gold boss",
}


def folder(rank):
    return ROOT / ("proof-v3" if rank == 10 else f"ladder/L{rank}")


def sheet(ranks, views, name):
    width = 375 * len(views)
    output = Image.new("RGB", (width, 630 * len(ranks)), "#252525")
    draw = ImageDraw.Draw(output)
    for row, rank in enumerate(ranks):
        for col, view in enumerate(views):
            image = Image.open(folder(rank) / f"renders/L{rank}-{view}.png").convert(
                "RGB"
            )
            assert image.size == (375, 600)
            output.paste(image, (col * 375, row * 630 + 30))
            draw.text(
                (col * 375 + 10, row * 630 + 8),
                f"L{rank} {COLORS[rank]} — {view}",
                fill="white",
            )
    output.save(OUT / name)


for start in [2, 5, 8]:
    ranks = list(range(start, start + 3))
    sheet(ranks, ["front", "back"], f"L{start}-L{start + 2}-front-back.jpg")
    sheet(ranks, ["attack", "guard", "kick"], f"L{start}-L{start + 2}-motion.jpg")
sheet(range(2, 11), ["fight"], "fight-size.jpg")
front = Image.new("RGB", (1125, 1890), "#252525")
draw = ImageDraw.Draw(front)
for index, rank in enumerate(range(2, 11)):
    x, y = (index % 3) * 375, (index // 3) * 630
    front.paste(
        Image.open(folder(rank) / f"renders/L{rank}-front.png").convert("RGB"),
        (x, y + 30),
    )
    draw.text((x + 10, y + 8), f"L{rank} {COLORS[rank]}", fill="white")
front.save(OUT / "ladder-front.jpg")
cards = []
for rank in range(2, 11):
    location = folder(rank).relative_to(ROOT)
    images = "".join(
        f'<figure><img src="../{location}/renders/L{rank}-{view}.png"><figcaption>{view}</figcaption></figure>'
        for view in VIEWS
    )
    cards.append(
        f'<section><h2>L{rank} · {COLORS[rank]}</h2><p><a href="../models/plaguedoctor-L{rank}.glb">Exact candidate GLB</a> · <a href="../source/L{rank}-reference.png">Design reference</a></p><div class="views">{images}</div></section>'
    )
html = (
    """<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plague Doctor L2–L10</title><style>body{background:#191919;color:#eee;font:16px system-ui;margin:24px}a{color:#dfbe74}.views{display:flex;overflow:auto;gap:10px}figure{margin:0;flex:0 0 300px}img{width:300px}section{border-top:1px solid #555;padding:12px 0}h1,h2{font-family:Georgia}figcaption{padding:6px}</style><h1>Plague Doctor · L2–L10</h1><p>Actual exported GLBs, matched CPU studio views. Separate candidates; original model untouched. These are phone-size studio captures, not in-game or physical-phone certification.</p><p><a href="../HANDOFF.md">Build receipts and remaining defects</a> · <a href="ladder-front.jpg">Complete front sheet</a></p>"""
    + "".join(cards)
    + "</html>"
)
(OUT / "index.html").write_text(html)
print(json.dumps({"review": str(OUT / "index.html"), "ranks": 9, "views": 54}))
