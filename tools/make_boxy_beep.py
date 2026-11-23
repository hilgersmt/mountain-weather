#!/usr/bin/env python3
"""Build the animated "beeping boxy" icon shown next to "Served from boxy".

Boxy (the All My Circuits robot) only beeps and boops, so sound waves pulse off
his head in two bursts: a quick 1-2-3 arc ripple (beep), a pause, another (boop).
Output is an animated PNG (full alpha, so it looks clean on light and dark themes).

Needs Pillow (not a site dependency):  python3 -m pip install pillow
Usage:  python3 tools/make_boxy_beep.py [--out static/images/boxy-beep-vN.png] [--preview strip.png]

Cloudflare caches /static/ for hours: write a NEW file name (bump -vN) and update
the <img> in templates/weather.html + templates/map.html instead of overwriting.
"""
import argparse, os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "boxy-1.png")           # 250x388 full-res source

MARGIN_X, MARGIN_TOP = 75, 30        # room for the waves around the figure
HEAD = (123, 42)                     # head centre in source-image pixels
RADII = [80, 104, 128]               # arc radii (source pixels)
ARC_WIDTH = 9
ARC_RGB = (150, 150, 150)            # mid-grey: readable on both themes
ARC_FADE = 45                        # each outer arc is this much more transparent
LEFT_ARC, RIGHT_ARC = (160, 215), (325, 20)   # degrees, tilted slightly up
OUT_HEIGHT = 120                     # px; ~2.5x the 48px display height (retina)
SUPERSAMPLE = 4
# (arcs visible, ms): beep burst, pause, boop burst
SEQUENCE = [(0, 500), (1, 160), (2, 160), (3, 400), (0, 220), (1, 140), (2, 140), (3, 500)]


def frame(boxy, n):
    w, h = boxy.size
    cw, ch = w + 2 * MARGIN_X, h + MARGIN_TOP
    cx, cy = MARGIN_X + HEAD[0], MARGIN_TOP + HEAD[1]
    s = SUPERSAMPLE
    big = Image.new("RGBA", (cw * s, ch * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    for i, r in enumerate(RADII[:n]):
        box = [(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s]
        fill = ARC_RGB + (255 - i * ARC_FADE,)
        d.arc(box, *LEFT_ARC, fill=fill, width=ARC_WIDTH * s)
        d.arc(box, *RIGHT_ARC, fill=fill, width=ARC_WIDTH * s)
    out = big.resize((cw, ch), Image.LANCZOS)
    out.alpha_composite(boxy, (MARGIN_X, MARGIN_TOP))
    return out.resize((round(cw * OUT_HEIGHT / ch), OUT_HEIGHT), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(HERE, "..", "static", "images", "boxy-beep-v1.png"))
    ap.add_argument("--preview", help="also write a frame strip on dark + light backgrounds")
    a = ap.parse_args()
    boxy = Image.open(SRC).convert("RGBA")
    frames = [frame(boxy, n) for n, _ in SEQUENCE]
    frames[0].save(a.out, save_all=True, append_images=frames[1:],
                   duration=[ms for _, ms in SEQUENCE], loop=0, disposal=1, blend=0)
    print(f"{a.out}: {frames[0].size[0]}x{frames[0].size[1]}, {len(frames)} frames")
    if a.preview:
        fw, fh = frames[0].size
        strip = Image.new("RGBA", (fw * len(frames), fh * 2), (30, 38, 56, 255))
        for i, f in enumerate(frames):
            strip.alpha_composite(f, (i * fw, 0))
            light = Image.new("RGBA", f.size, (240, 240, 240, 255)); light.alpha_composite(f)
            strip.alpha_composite(light, (i * fw, fh))
        strip.save(a.preview)


if __name__ == "__main__":
    main()
