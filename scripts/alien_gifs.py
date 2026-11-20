"""Draw the alien-cat pixel-art GIFs: assets/alien-snack.gif and assets/alien-dance.gif.

Close-up "meme camera" framing: the heads fill the panel and are cropped at the chest.
Everything is drawn at low resolution (140x96 logical pixels) with aliased shapes,
then scaled up 3x with nearest-neighbour so it stays crisp pixel art.
"""
import math
import pathlib
import random
from PIL import Image, ImageDraw

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "assets"
W, H, SCALE = 140, 96, 3
IX, IY, IW, IH = 3, 11, 133, 81  # panel interior

C = {
    "bg": (7, 7, 10), "panel": (17, 17, 20), "navy": (10, 16, 40), "navy2": (16, 26, 58),
    "yel": (255, 210, 63), "yel_d": (201, 154, 0), "red": (230, 57, 70), "red_d": (157, 28, 38),
    "white": (245, 245, 245), "dim": (138, 138, 143),
    "rim": (58, 120, 44), "gd": (95, 181, 68), "g": (138, 222, 100), "gl": (186, 242, 150),
    "gc": (222, 255, 200), "eye": (12, 30, 16), "eye2": (34, 70, 32), "mouth": (70, 16, 24),
    "blue": (40, 58, 200), "blue_l": (96, 120, 255),
}

FONT = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "C": [".##", "#..", "#..", "#..", ".##"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."], "E": ["###", "#..", "##.", "#..", "###"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "K": ["#.#", "#.#", "##.", "#.#", "#.#"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "P": ["##.", "#.#", "##.", "#..", "#.."], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], " ": ["..", "..", "..", "..", ".."],
}


def text(d, x, y, s, col):
    for ch in s:
        g = FONT[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == "#":
                    d.point((x + c, y + r), fill=col)
        x += len(g[0]) + 1


def text_w(s):
    return sum(len(FONT[ch][0]) + 1 for ch in s) - 1


def frame(label, scene):
    """Galaxy panel frame around a scene image of size IW x IH."""
    im = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(im)
    tw = text_w(label) + 12
    d.rectangle((4, 12, 138, 94), fill=C["red_d"])
    d.rectangle((4, 4, 4 + tw, 10), fill=C["red_d"])
    d.rectangle((2, 10, 136, 92), fill=C["yel"])
    d.rectangle((2, 2, 2 + tw, 11), fill=C["yel"])
    d.line((2, 10, 136, 10), fill=C["white"])
    d.line((2, 2, 2 + tw, 2), fill=C["white"])
    d.line((2, 2, 2, 92), fill=C["white"])
    im.paste(scene, (IX, IY))
    d.rectangle((3, 3, 1 + tw, 10), fill=C["panel"])
    d.line((7, 4, 7, 8), fill=C["yel"])
    d.line((5, 6, 9, 6), fill=C["yel"])
    text(d, 12, 4, label, C["yel"])
    return im


def fuzz(img, seed, mask_cols=("g", "gl", "gd")):
    """Blotchy dither on the green fur so it reads like the grainy meme filter."""
    rng = random.Random(seed)
    px = img.load()
    cols = {C[k]: k for k in mask_cols}
    up = {"gd": "g", "g": "gl", "gl": "gc"}
    down = {"gl": "g", "g": "gd", "gd": "rim"}
    for y in range(img.height):
        for x in range(img.width):
            p = px[x, y]
            if p[3] and p[:3] in cols:
                r = rng.random()
                k = cols[p[:3]]
                if r < 0.06:
                    px[x, y] = C[up[k]] + (255,)
                elif r < 0.13:
                    px[x, y] = C[down[k]] + (255,)


def stalk(d, x0, y0, x1, y1, knob_r=3, bumps=0):
    d.line((x0, y0, x1, y1), fill=C["rim"], width=5)
    d.line((x0, y0, x1, y1), fill=C["g"], width=3)
    d.line((x0, y0, x1, y1), fill=C["gl"], width=1)
    for i in range(1, bumps + 1):
        t = i / (bumps + 1)
        bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        d.rectangle((bx - 3, by - 1, bx + 3, by + 1), fill=C["g"], outline=C["rim"])
    d.ellipse((x1 - knob_r, y1 - knob_r, x1 + knob_r, y1 + knob_r), fill=C["gl"], outline=C["rim"])


# ---------------------------------------------------------------- snack (close-up cat)

def cat_face(jaw, blink, sway):
    """Big close-up of the alien cat's face, cropped at the chest (like the meme)."""
    im = Image.new("RGBA", (IW, 112), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = IW // 2
    stalk(d, cx - 16, 26, cx - 20 + sway, 2, 4)
    stalk(d, cx + 16, 26, cx + 20 + sway, 2, 4)
    # ears
    d.polygon([(cx - 50, 50), (cx - 44, 12), (cx - 18, 28)], fill=C["g"], outline=C["rim"])
    d.polygon([(cx + 50, 50), (cx + 44, 12), (cx + 18, 28)], fill=C["g"], outline=C["rim"])
    d.polygon([(cx - 43, 36), (cx - 41, 20), (cx - 28, 30)], fill=C["gd"])
    d.polygon([(cx + 43, 36), (cx + 41, 20), (cx + 28, 30)], fill=C["gd"])
    # wide meme-cat head + chest
    d.rounded_rectangle((cx - 56, 24, cx + 56, 120), 24, fill=C["g"], outline=C["rim"])
    d.ellipse((cx - 60, 44, cx - 30, 92), fill=C["g"])
    d.ellipse((cx + 30, 44, cx + 60, 92), fill=C["g"])
    d.arc((cx - 60, 44, cx - 30, 92), 100, 260, fill=C["rim"])
    d.arc((cx + 30, 44, cx + 60, 92), -80, 80, fill=C["rim"])
    # glow: lighter forehead / cheeks
    d.ellipse((cx - 40, 28, cx + 26, 58), fill=C["gl"])
    d.ellipse((cx - 50, 56, cx - 24, 84), fill=C["gl"])
    d.ellipse((cx + 24, 58, cx + 48, 84), fill=C["gl"])
    # darker muzzle / nose bridge, slightly off-centre like the photo
    d.ellipse((cx - 13, 52 + jaw, cx + 15, 82 + jaw), fill=C["gd"])
    d.rectangle((cx - 4, 42, cx + 5, 60), fill=C["gd"])
    fuzz(im, 7)
    d = ImageDraw.Draw(im)
    # eyes: squinty almonds, left one tilted
    if blink:
        d.line((cx - 32, 47, cx - 18, 49), fill=C["eye"], width=2)
        d.line((cx + 16, 49, cx + 30, 46), fill=C["eye"], width=2)
    else:
        d.polygon([(cx - 33, 46), (cx - 27, 42), (cx - 20, 43), (cx - 16, 48), (cx - 23, 51), (cx - 30, 50)], fill=C["eye"])
        d.polygon([(cx + 15, 49), (cx + 20, 44), (cx + 27, 43), (cx + 32, 45), (cx + 28, 50), (cx + 21, 51)], fill=C["eye"])
        d.line((cx - 30, 47, cx - 25, 45), fill=C["eye2"])
        d.line((cx + 20, 47, cx + 25, 46), fill=C["eye2"])
    # nose
    d.rectangle((cx - 2, 61, cx + 3, 63), fill=C["eye2"])
    # mouth + blue snack (moves with the jaw)
    if jaw >= 3:
        d.ellipse((cx - 7, 70, cx + 8, 76 + jaw), fill=C["mouth"])
    else:
        d.line((cx - 6, 72 + jaw, cx + 6, 72 + jaw), fill=C["eye2"])
    sy = 80 + jaw
    d.ellipse((cx - 8, sy - 4, cx + 9, sy + 7), fill=C["blue"])
    d.ellipse((cx - 5, sy - 3, cx + 1, sy + 1), fill=C["blue_l"])
    return im


def snack():
    frames = []
    # chew cycle: (jaw drop, head bob, tilt, blink)
    cycle = [(0, 0, 0), (2, 1, 2), (4, 2, 3), (2, 1, 2), (0, 0, 0), (2, 1, -2), (4, 2, -3), (2, 1, -2)]
    for f in range(16):
        jaw, bob, tilt = cycle[f % 8]
        blink = f in (10, 11)
        sway = (0, 1, 2, 1, 0, -1, -2, -1)[f % 8]
        scene = Image.new("RGBA", (IW, IH), C["navy"] + (255,))
        sd = ImageDraw.Draw(scene)
        for i, (x, y) in enumerate(((8, 8), (120, 12), (14, 60), (124, 66), (100, 4), (30, 20))):
            if (i + f) % 3:
                sd.point((x, y), fill=C["white"] if i % 2 else C["yel"])
        face = cat_face(jaw, blink, sway).rotate(tilt, resample=Image.NEAREST, center=(IW // 2, 110))
        scene.alpha_composite(face.crop((0, 14 - bob, IW, 14 - bob + IH)), (0, 0))
        frames.append(frame("SNACK TIME", scene.convert("RGB")))
    save(frames, "alien-snack.gif", 110)


# ---------------------------------------------------------------- dance (close-up duo)

def dance_cat(mouth):
    im = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stalk(d, 22, 26, 17, 6, 3)
    stalk(d, 40, 24, 44, 4, 3)
    d.polygon([(10, 34), (12, 18), (24, 26)], fill=C["g"], outline=C["rim"])
    d.polygon([(54, 34), (52, 18), (40, 26)], fill=C["g"], outline=C["rim"])
    d.ellipse((6, 20, 58, 70), fill=C["g"], outline=C["rim"])          # round head
    d.ellipse((10, 62, 54, 110), fill=C["g"], outline=C["rim"])        # chest
    d.ellipse((6, 20, 58, 70), fill=C["g"])
    d.arc((6, 20, 58, 70), 200, 340, fill=C["rim"])
    d.ellipse((14, 24, 46, 50), fill=C["gl"])
    d.ellipse((20, 66, 44, 96), fill=C["gl"])
    fuzz(im, 11)
    d = ImageDraw.Draw(im)
    d.ellipse((19, 40, 26, 47), fill=C["eye"])
    d.ellipse((38, 40, 45, 47), fill=C["eye"])
    d.point((21, 42), fill=C["gl"]); d.point((40, 42), fill=C["gl"])
    if mouth:
        d.ellipse((28, 52, 36, 60), fill=C["eye"])
    else:
        d.ellipse((29, 53, 35, 57), fill=C["eye2"])
    return im


def dance_dog(mouth):
    im = Image.new("RGBA", (78, 104), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stalk(d, 26, 28, 24, 4, 3, bumps=2)
    stalk(d, 52, 28, 55, 4, 3, bumps=2)
    d.polygon([(12, 36), (12, 22), (24, 30)], fill=C["g"], outline=C["rim"])
    d.polygon([(66, 36), (66, 22), (54, 30)], fill=C["g"], outline=C["rim"])
    d.polygon([(12, 28), (66, 28), (72, 58), (66, 84), (12, 84), (6, 58)], fill=C["g"], outline=C["rim"])
    d.rounded_rectangle((12, 76, 66, 120), 10, fill=C["g"], outline=C["rim"])
    d.polygon([(13, 29), (65, 29), (71, 58), (65, 83), (13, 83), (7, 58)], fill=C["g"])
    d.ellipse((18, 30, 60, 56), fill=C["gl"])
    d.ellipse((30, 30, 52, 44), fill=C["gc"])
    d.ellipse((24, 82, 54, 104), fill=C["gl"])
    fuzz(im, 23)
    d = ImageDraw.Draw(im)
    d.ellipse((18, 44, 31, 58), fill=C["eye"])
    d.ellipse((47, 44, 60, 58), fill=C["eye"])
    d.point((21, 47), fill=C["eye2"]); d.point((50, 47), fill=C["eye2"])
    if mouth:
        d.ellipse((34, 64, 44, 74), fill=C["eye"])
    else:
        d.ellipse((35, 66, 43, 71), fill=C["eye2"])
    return im


def dance():
    frames = []
    n = 12
    for f in range(n):
        t = 2 * math.pi * f / n
        scene = Image.new("RGBA", (IW, IH), C["navy"] + (255,))
        sd = ImageDraw.Draw(scene)
        for i, (x, y) in enumerate(((6, 6), (64, 4), (126, 8), (70, 30), (4, 50), (128, 44))):
            if (i + f) % 3:
                sd.point((x, y), fill=C["white"] if i % 2 else C["yel"])
        beat = f % 3 == 0
        # side-to-side rocking from the hips, the two in opposite phase
        c_ang, d_ang = 12 * math.sin(t), -9 * math.sin(t)
        c_dx, d_dx = round(5 * math.sin(t)), round(-4 * math.sin(t))
        c_dy = round(-3 * abs(math.sin(2 * t)))
        d_dy = round(-3 * abs(math.cos(2 * t)))
        dog_im = dance_dog(beat).rotate(d_ang, resample=Image.NEAREST, center=(39, 100))
        cat_im = dance_cat(not beat).rotate(c_ang, resample=Image.NEAREST, center=(32, 92))
        scene.alpha_composite(dog_im, (54 + d_dx, 6 + d_dy))
        scene.alpha_composite(cat_im, (10 + c_dx, 20 + c_dy))
        frames.append(frame("DANCE PARTY", scene.convert("RGB")))
    save(frames, "alien-dance.gif", 90)


def save(frames, name, ms):
    pal = Image.new("P", (1, 1))
    flat = [v for col in C.values() for v in col]
    pal.putpalette(flat + [0] * (768 - len(flat)))
    big = [f.resize((W * SCALE, H * SCALE), Image.NEAREST).quantize(palette=pal, dither=Image.Dither.NONE)
           for f in frames]
    out = ASSETS / name
    big[0].save(out, save_all=True, append_images=big[1:], duration=ms, loop=0, disposal=2, optimize=False)
    print("wrote", out, out.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    snack()
    dance()
