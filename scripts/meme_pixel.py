"""Turn the real alien-cat meme GIFs into pixel-art GIFs inside the galaxy panel frame.

usage: python scripts/meme_pixel.py <cat-eat.gif> <dance.gif>

Each source frame is shrunk to the panel's low-res interior, its colours are reduced to a
small shared palette (no dithering, so it reads as pixel art), then scaled up 3x with
nearest-neighbour and wrapped in the same yellow/red panel used by the other profile cards.
"""
import sys
import pathlib
from PIL import Image, ImageSequence

from alien_gifs import ASSETS, C, IH, IW, SCALE, H, W, frame

NAVY = C["navy"]


def frames_of(path):
    im = Image.open(path)
    out = []
    for f in ImageSequence.Iterator(im):
        out.append((f.convert("RGB"), f.info.get("duration", 100)))
    return out


def fit(src, box_h, crop_top=0, crop_h=None, bg=NAVY, white_to_bg=False):
    """Scale src to box_h tall, optionally crop vertically, centre it on an IW x IH scene."""
    w, h = src.size
    nw = round(w * box_h / h)
    small = src.resize((nw, box_h), Image.LANCZOS)
    if white_to_bg:
        px = small.load()
        for y in range(small.height):
            for x in range(small.width):
                r, g, b = px[x, y]
                if min(r, g, b) > 205 and max(r, g, b) - min(r, g, b) < 22:  # sticker's white background, not pale fur
                    px[x, y] = bg
    crop_h = crop_h or IH
    small = small.crop((0, crop_top, nw, crop_top + crop_h))
    scene = Image.new("RGB", (IW, IH), bg)
    scene.paste(small, ((IW - nw) // 2, (IH - crop_h) // 2))
    return scene


def pixelate(name, label, scenes, durations, colors=22):
    # shared palette from all frames + the panel colours, no dithering
    montage = Image.new("RGB", (IW, IH * len(scenes)))
    for i, s in enumerate(scenes):
        montage.paste(s, (0, i * IH))
    pal_img = montage.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = pal_img.getpalette()[: colors * 3]
    for k in ("bg", "panel", "yel", "red_d", "white", "red"):
        pal += list(C[k])
    pal_ref = Image.new("P", (1, 1))
    pal_ref.putpalette(pal + [0] * (768 - len(pal)))

    out = []
    for s in scenes:
        low = s.quantize(palette=pal_ref, dither=Image.Dither.NONE).convert("RGB")
        full = frame(label, low)
        out.append(full.resize((W * SCALE, H * SCALE), Image.NEAREST)
                   .quantize(palette=pal_ref, dither=Image.Dither.NONE))
    path = ASSETS / name
    out[0].save(path, save_all=True, append_images=out[1:], duration=durations, loop=0,
                disposal=2, optimize=False)
    print("wrote", path, len(out), "frames", path.stat().st_size // 1024, "KB")


def main(cat_path, dance_path):
    cat = frames_of(cat_path)
    pixelate("alien-snack.gif", "SNACK TIME",
             [fit(f, 92, crop_top=6, white_to_bg=True) for f, _ in cat], [d for _, d in cat])
    dance = frames_of(dance_path)
    bg = dance[0][0].getpixel((2, 2))  # match the clip's own dark navy for side padding
    pixelate("alien-dance.gif", "DANCE PARTY",
             [fit(f, IH, bg=bg) for f, _ in dance], [d for _, d in dance])


if __name__ == "__main__":
    main(*sys.argv[1:3])
