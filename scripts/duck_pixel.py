"""Pixelate the dancing-duck GIF and embed it as the STATUS portrait.

usage: python scripts/duck_pixel.py <duck.gif>

Frames are cropped to the duck, shrunk to a low-res sprite, reduced to a few colours,
given a 1px dark outline, scaled up with nearest-neighbour, then embedded (base64) in
assets/status.svg between the PORTRAIT START / END markers.
"""
import base64
import io
import pathlib
import re
import sys
from PIL import Image, ImageFilter, ImageSequence

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATUS = ROOT / "assets" / "status.svg"
SPRITE_H, PX = 74, 2            # sprite height in logical pixels, screen px per logical px
BOX = (44, 58, 172, 172)         # portrait interior x, y, w, h in status.svg
OUTLINE = (58, 40, 18)
START, END = "<!-- PORTRAIT START: dancing duck -->", "<!-- PORTRAIT END -->"


def load(path):
    im = Image.open(path)
    frames = [(f.convert("RGBA"), f.info.get("duration", 100)) for f in ImageSequence.Iterator(im)]
    box = None
    for f, _ in frames:
        b = f.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return [(f.crop(box), d) for f, d in frames]


def sprite(frames):
    w, h = frames[0][0].size
    sw = round(w * SPRITE_H / h)
    smalls = []
    for f, _ in frames:
        # thicken the black line art so eyes, beak and outline survive the shrink
        flat = Image.new("RGB", f.size, (255, 255, 255))
        flat.paste(f.convert("RGB"), (0, 0), f.getchannel("A"))
        flat = flat.filter(ImageFilter.MinFilter(5))
        small = flat.resize((sw, SPRITE_H), Image.BOX).convert("RGBA")
        small.putalpha(f.getchannel("A").resize((sw, SPRITE_H), Image.BOX))
        smalls.append(small)
    # shared palette from the opaque pixels of every frame
    strip = Image.new("RGB", (sw, SPRITE_H * len(smalls)), (255, 255, 255))
    for i, s in enumerate(smalls):
        strip.paste(s.convert("RGB"), (0, i * SPRITE_H), s.getchannel("A"))
    pal = strip.quantize(colors=8, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out = []
    for s in smalls:
        a = s.getchannel("A").point(lambda v: 255 if v > 110 else 0)
        rgb = s.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
        img = Image.new("RGBA", (sw + 2, SPRITE_H + 2), (0, 0, 0, 0))
        img.paste(rgb, (1, 1), a)
        # 1px dark outline around the silhouette, like the original's line art
        src = img.copy().load()
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                if src[x, y][3]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < img.width and 0 <= ny < img.height and src[nx, ny][3]:
                        px[x, y] = OUTLINE + (255,)
                        break
        out.append(img.resize((img.width * PX, img.height * PX), Image.NEAREST))
    return out


def to_gif(frames, durations):
    key = (255, 0, 255)
    pal_frames = []
    for f in frames:
        bg = Image.new("RGB", f.size, key)
        bg.paste(f, (0, 0), f)
        pal_frames.append(bg)
    strip = Image.new("RGB", (frames[0].width, frames[0].height * len(frames)))
    for i, f in enumerate(pal_frames):
        strip.paste(f, (0, i * frames[0].height))
    pal = strip.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    ps = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in pal_frames]
    idx = ps[0].getpalette()[: 16 * 3]
    t = min(range(len(idx) // 3), key=lambda i: sum((idx[i * 3 + k] - key[k]) ** 2 for k in range(3)))
    buf = io.BytesIO()
    ps[0].save(buf, "GIF", save_all=True, append_images=ps[1:], duration=durations, loop=0,
               transparency=t, disposal=2, optimize=False)
    return buf.getvalue()


def main(path):
    frames = load(path)
    big = sprite(frames)
    data = to_gif(big, [d for _, d in frames])
    (ROOT / "assets" / "duck.gif").write_bytes(data)
    w, h = big[0].size
    bx, by, bw, bh = BOX
    x, y = bx + (bw - w) // 2, by + bh - h - 6
    b64 = base64.b64encode(data).decode()
    block = (f'{START}\n  <image x="{x}" y="{y}" width="{w}" height="{h}" '
             f'href="data:image/gif;base64,{b64}"/>\n  {END}')
    svg = STATUS.read_text(encoding="utf-8")
    if START in svg:
        svg = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, svg, flags=re.S)
    else:
        # first run: replace the old astronaut group
        a = svg.index("<!-- PIXEL ASTRONAUT CHARACTER")
        b = svg.index("<!-- Name under portrait -->")
        svg = svg[:a] + block + "\n\n  " + svg[b:]
    STATUS.write_text(svg, encoding="utf-8")
    print(f"duck {w}x{h}px, gif {len(data)//1024} KB, status.svg {STATUS.stat().st_size//1024} KB")


if __name__ == "__main__":
    main(sys.argv[1])
