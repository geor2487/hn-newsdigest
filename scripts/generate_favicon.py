#!/usr/bin/env python3
"""Generate favicon.ico for HN Digest."""

from PIL import Image, ImageDraw, ImageFont
import os
import math

def draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    r = radius
    # Corners
    draw.pieslice([x0, y0, x0 + 2*r, y0 + 2*r], 180, 270, fill=fill)
    draw.pieslice([x1 - 2*r, y0, x1, y0 + 2*r], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2*r, x0 + 2*r, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2*r, y1 - 2*r, x1, y1], 0, 90, fill=fill)
    # Rectangles to fill gaps
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x0 + r, y1 - r], fill=fill)
    draw.rectangle([x1 - r, y0 + r, x1, y1 - r], fill=fill)


def create_icon(size):
    """Create a single icon image at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background - dark with rounded corners
    bg_color = (8, 8, 14, 255)  # --bg: #08080e
    radius = max(size // 5, 2)
    draw_rounded_rect(draw, (0, 0, size - 1, size - 1), radius, bg_color)

    # Draw the triangle (▲) in accent color
    accent = (255, 102, 51, 255)  # --accent: #ff6633

    # Triangle geometry - centered, with good proportions
    margin = size * 0.18
    top_y = size * 0.18
    bottom_y = size * 0.82
    cx = size / 2

    # Triangle points
    tri_width = size - 2 * margin
    points = [
        (cx, top_y),                          # top center
        (cx - tri_width / 2, bottom_y),       # bottom left
        (cx + tri_width / 2, bottom_y),       # bottom right
    ]

    # Draw filled triangle
    draw.polygon(points, fill=accent)

    # For larger sizes, add a subtle inner cutout to make it look like the HN logo
    if size >= 32:
        # Inner triangle (hollow effect)
        inner_margin = size * 0.12
        inner_top_y = top_y + inner_margin * 1.8
        inner_bottom_y = bottom_y - inner_margin * 0.8
        inner_width = tri_width * 0.45

        inner_points = [
            (cx, inner_top_y),
            (cx - inner_width / 2, inner_bottom_y),
            (cx + inner_width / 2, inner_bottom_y),
        ]
        draw.polygon(inner_points, fill=bg_color)

    return img


def main():
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

    # Generate multiple sizes for .ico
    sizes = [16, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]

    # Save as .ico (multi-resolution)
    ico_path = os.path.join(docs_dir, "favicon.ico")
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Generated: {ico_path}")

    # Also save a 180x180 PNG for apple-touch-icon
    apple_icon = create_icon(180)
    apple_path = os.path.join(docs_dir, "apple-touch-icon.png")
    apple_icon.save(apple_path, format="PNG")
    print(f"Generated: {apple_path}")

    # Save a 192x192 PNG for PWA / Android
    pwa_icon = create_icon(192)
    pwa_path = os.path.join(docs_dir, "icon-192.png")
    pwa_icon.save(pwa_path, format="PNG")
    print(f"Generated: {pwa_path}")

    # Save a 512x512 PNG for PWA
    pwa_icon_lg = create_icon(512)
    pwa_lg_path = os.path.join(docs_dir, "icon-512.png")
    pwa_icon_lg.save(pwa_lg_path, format="PNG")
    print(f"Generated: {pwa_lg_path}")


if __name__ == "__main__":
    main()
