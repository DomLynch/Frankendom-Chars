"""Contact sheets of actual exported-model captures, without image alteration."""

from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent.parent / "delivery"
review = root / "review"
review.mkdir(exist_ok=True)
for rank in range(2, 11):
    views = [
        "front",
        "back",
        "left",
        "right",
        "head",
        "attack",
        "heavy",
        "guard",
        "kick",
        "fight",
    ]
    sheet = Image.new("RGB", (1875, 1250), "#dddddd")
    draw = ImageDraw.Draw(sheet)
    for i, v in enumerate(views):
        p = root / "previews" / f"L{rank}" / f"L{rank}-{v}.png"
        x = (i % 5) * 375
        y = (i // 5) * 625
        sheet.paste(Image.open(p).convert("RGB"), (x, y + 25))
        draw.text((x + 8, y + 6), p.stem, fill="black")
    sheet.save(review / f"L{rank}-sheet.jpg", quality=90)
ladder = Image.new("RGB", (375 * 9, 625), "#dddddd")
draw = ImageDraw.Draw(ladder)
for i, rank in enumerate(range(2, 11)):
    ladder.paste(
        Image.open(root / "previews" / f"L{rank}" / f"L{rank}-front.png").convert(
            "RGB"
        ),
        (i * 375, 25),
    )
    draw.text((i * 375 + 12, 7), f"Pitborn L{rank}", fill="black")
ladder.save(review / "pitborn-L2-L10.jpg", quality=92)
