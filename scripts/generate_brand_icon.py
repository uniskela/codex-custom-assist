"""Generate brand images for Home Assistant / HACS.

Writes icon + logo variants under custom_components/codex_custom_assist/brand/
per https://developers.home-assistant.io/docs/core/integration/brand_images/
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "codex_custom_assist"
    / "brand"
)
OUT.mkdir(parents=True, exist_ok=True)

BG = (18, 42, 58, 255)
BG_DARK = (10, 24, 34, 255)
BUBBLE = (236, 244, 248, 255)
ACCENT = (56, 189, 168, 255)
ACCENT_DIM = (90, 140, 155, 255)
DOT = (18, 42, 58, 255)


def _draw_mark(img: Image.Image, *, dark: bool = False) -> None:
    d = ImageDraw.Draw(img)
    size = img.size[0]
    bg = BG_DARK if dark else BG
    margin = max(8, size // 16)
    radius = max(16, size // 5)
    d.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=bg,
    )

    bx0, by0 = int(size * 0.22), int(size * 0.24)
    bx1, by1 = int(size * 0.78), int(size * 0.62)
    br = max(10, size // 12)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=br, fill=BUBBLE)
    tail = [
        (int(size * 0.30), by1 - 2),
        (int(size * 0.28), int(size * 0.74)),
        (int(size * 0.42), by1 - 2),
    ]
    d.polygon(tail, fill=BUBBLE)

    cy = int((by0 + by1) / 2)
    r = max(3, size // 36)
    for frac in (0.38, 0.50, 0.62):
        cx = int(size * frac)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOT)

    width = max(3, size // 28)
    for i, (start, end, color) in enumerate(
        [
            (220, 320, ACCENT_DIM),
            (230, 310, ACCENT),
        ]
    ):
        pad = int(size * (0.10 + 0.04 * i))
        d.arc(
            [bx0 - pad, by0 - pad - size // 30, bx1 + pad, by1 - pad],
            start=start,
            end=end,
            fill=color,
            width=width,
        )


def _icon(size: int, *, dark: bool = False) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    _draw_mark(img, dark=dark)
    return img


def _logo(width: int, height: int, *, dark: bool = False) -> Image.Image:
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bg = BG_DARK if dark else BG
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=height // 5, fill=bg)
    mark = _icon(height, dark=dark).resize((height, height), Image.Resampling.LANCZOS)
    img.alpha_composite(mark, (0, 0))
    x0 = int(height * 0.95)
    y_mid = height // 2
    d.rounded_rectangle(
        [x0, y_mid - height // 5, width - height // 6, y_mid - height // 12],
        radius=4,
        fill=BUBBLE,
    )
    d.rounded_rectangle(
        [x0, y_mid + height // 16, width - height // 3, y_mid + height // 5],
        radius=4,
        fill=ACCENT,
    )
    return img


def main() -> None:
    files = {
        "icon.png": _icon(256),
        "icon@2x.png": _icon(512),
        "dark_icon.png": _icon(256, dark=True),
        "dark_icon@2x.png": _icon(512, dark=True),
        "logo.png": _logo(512, 256),
        "logo@2x.png": _logo(1024, 512),
        "dark_logo.png": _logo(512, 256, dark=True),
        "dark_logo@2x.png": _logo(1024, 512, dark=True),
    }
    for name, image in files.items():
        path = OUT / name
        image.save(path, "PNG")
        print(f"wrote {path} {image.size}")


if __name__ == "__main__":
    main()
