"""Block textures and a small software renderer for the profile's voxel art.

Everything is procedural and deterministic: each 16x16 texture is drawn from a
fixed palette with a seeded RNG, so a rebuild with the same data produces the
same bytes. Faces are mapped onto any parallelogram with an affine transform
and nearest-neighbour sampling, which keeps the pixels crisp at any size.

Rasters are rendered at 2x and embedded into the SVG panels as PNG, so text,
labels and motion stay vector on top of a bitmap world.
"""
import base64
import io
import random
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

T = 16


# --------------------------------------------------------------------- textures
def _rng(name):
    return random.Random(zlib.crc32(name.encode()))


def _pick(rng, pal, weights=None):
    return rng.choices(pal, weights=weights)[0]


def _noise(name, pal, weights=None):
    rng = _rng(name)
    a = np.zeros((T, T, 3), np.uint8)
    for y in range(T):
        for x in range(T):
            a[y, x] = _pick(rng, pal, weights)
    return a


GRASS = [(95, 159, 53), (108, 173, 61), (84, 143, 46), (121, 185, 72), (74, 128, 40)]
DIRT = [(134, 96, 67), (121, 85, 58), (150, 108, 77), (104, 73, 50), (166, 124, 92)]
STONE = [(127, 127, 127), (116, 116, 116), (137, 137, 137), (104, 104, 104), (146, 146, 146)]


def grass_top():
    return _noise("grass_top", GRASS, [5, 4, 4, 2, 2])


def dirt():
    return _noise("dirt", DIRT, [5, 4, 3, 2, 1])


def grass_side():
    a = dirt().copy()
    rng = _rng("grass_side")
    for x in range(T):
        depth = 3 + (rng.random() < .55) + (rng.random() < .25) + (rng.random() < .1)
        for y in range(depth):
            a[y, x] = _pick(rng, GRASS, [5, 4, 4, 2, 2])
    return a


def stone():
    a = _noise("stone", STONE, [5, 4, 3, 2, 1])
    rng = _rng("stone-cracks")
    for _ in range(5):                                   # short darker streaks
        x, y = rng.randrange(T), rng.randrange(T)
        for k in range(rng.randrange(2, 4)):
            if 0 <= x + k < T:
                a[y, x + k] = (96, 96, 96)
    return a


def cobble():
    a = _noise("cobble", [(122, 122, 122), (110, 110, 110), (134, 134, 134), (95, 95, 95)])
    rng = _rng("cobble-mortar")
    for _ in range(26):
        a[rng.randrange(T), rng.randrange(T)] = (72, 72, 72)
    return a


def planks():
    rng = _rng("planks")
    a = np.zeros((T, T, 3), np.uint8)
    pal = [(162, 130, 78), (152, 121, 72), (171, 139, 85), (143, 113, 66)]
    for y in range(T):
        for x in range(T):
            a[y, x] = _pick(rng, pal, [5, 3, 2, 1])
    for row in range(4):
        y = row * 4 + 3
        a[y, :] = (104, 83, 50)
        seam = (row * 7 + 3) % T
        a[row * 4:row * 4 + 3, seam] = (118, 94, 56)
    return a


def log_side():
    rng = _rng("log_side")
    pal = [(104, 83, 51), (88, 70, 42), (117, 94, 58), (76, 60, 36)]
    a = np.zeros((T, T, 3), np.uint8)
    for x in range(T):
        base = _pick(rng, pal)
        for y in range(T):
            a[y, x] = base if rng.random() > .25 else _pick(rng, pal)
    return a


def log_top():
    a = np.zeros((T, T, 3), np.uint8)
    for y in range(T):
        for x in range(T):
            r = max(abs(x - 7.5), abs(y - 7.5))
            a[y, x] = (104, 83, 51) if r > 6.5 else ((176, 145, 90) if int(r) % 2 else (156, 125, 76))
    return a


def leaves():
    a = _noise("leaves", [(58, 120, 36), (48, 102, 29), (72, 138, 46), (36, 80, 22)], [4, 4, 2, 2])
    rng = _rng("leaves-holes")
    for _ in range(18):
        a[rng.randrange(T), rng.randrange(T)] = (22, 48, 14)
    return a


def ore(name, colour):
    a = stone().copy()
    rng = _rng(name)
    c = np.array(colour)
    for _ in range(4):
        cx, cy = rng.randrange(2, 13), rng.randrange(2, 13)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)):
            if rng.random() < .8:
                k = rng.choice((.75, 1.0, 1.0, 1.25))
                a[cy + dy, cx + dx] = np.clip(c * k, 0, 255)
    return a


def gem_block(name, colour):
    """Emerald / diamond / gold block: bright face, darker frame, bevelled."""
    rng = _rng(name)
    c = np.array(colour, float)
    a = np.zeros((T, T, 3), np.uint8)
    for y in range(T):
        for x in range(T):
            k = .92 + rng.random() * .16
            if x == 0 or y == 0:
                k = 1.25
            elif x == T - 1 or y == T - 1:
                k = .62
            elif x in (1, T - 2) or y in (1, T - 2):
                k = .82
            elif (x + y) % 6 == 0 or abs(x - y) % 6 == 0:
                k = 1.12
            a[y, x] = np.clip(c * k, 0, 255)
    return a


def bedrock():
    return _noise("bedrock", [(85, 85, 85), (52, 52, 52), (30, 30, 30), (110, 110, 110)], [3, 3, 2, 1])


def bookshelf():
    a = planks().copy()
    rng = _rng("books")
    cols = [(150, 40, 40), (40, 80, 150), (60, 120, 50), (160, 120, 40), (110, 60, 130)]
    for shelf in (1, 9):
        x = 1
        while x < 15:
            w = rng.choice((1, 2))
            c = rng.choice(cols)
            a[shelf:shelf + 6, x:x + w] = c
            a[shelf, x:x + w] = np.clip(np.array(c) * 1.3, 0, 255)
            x += w + (rng.random() < .3)
    return a


TEX = {
    "grass_top": grass_top, "grass_side": grass_side, "dirt": dirt, "stone": stone, "cobble": cobble,
    "planks": planks, "log_side": log_side, "log_top": log_top, "leaves": leaves, "bedrock": bedrock,
    "bookshelf": bookshelf,
    "emerald_ore": lambda: ore("emerald_ore", (23, 221, 98)),
    "diamond_ore": lambda: ore("diamond_ore", (93, 236, 245)),
    "gold_ore": lambda: ore("gold_ore", (252, 238, 75)),
    "redstone_ore": lambda: ore("redstone_ore", (255, 30, 30)),
    "lapis_ore": lambda: ore("lapis_ore", (40, 80, 200)),
    "emerald_block": lambda: gem_block("emerald_block", (42, 203, 99)),
    "diamond_block": lambda: gem_block("diamond_block", (98, 219, 214)),
    "gold_block": lambda: gem_block("gold_block", (246, 208, 61)),
}
_cache = {}


def tex(name):
    if name not in _cache:
        _cache[name] = TEX[name]()
    return _cache[name]


# A block is (top, side, bottom-side) texture names.
BLOCKS = {
    "grass": ("grass_top", "grass_side", "dirt"),
    "dirt": ("dirt", "dirt", "dirt"),
    "stone": ("stone", "stone", "stone"),
    "planks": ("planks", "planks", "planks"),
    "log": ("log_top", "log_side", "log_side"),
    "leaves": ("leaves", "leaves", "leaves"),
    "bookshelf": ("planks", "bookshelf", "bookshelf"),
    "emerald_ore": ("emerald_ore", "emerald_ore", "emerald_ore"),
    "diamond_ore": ("diamond_ore",) * 3,
    "gold_ore": ("gold_ore",) * 3,
    "redstone_ore": ("redstone_ore",) * 3,
    "bedrock": ("bedrock",) * 3,
    "emerald_block": ("emerald_block", "emerald_block", "emerald_block"),
    "diamond_block": ("diamond_block", "diamond_block", "diamond_block"),
    "gold_block": ("gold_block", "gold_block", "gold_block"),
}


# ------------------------------------------------------------------- rendering
def shaded(name, k):
    a = tex(name).astype(float) * k
    return np.clip(a, 0, 255).astype(np.uint8)


def face(img, o, e1, e2, arr, k=1.0, alpha=255):
    """Map texture arr onto the parallelogram o + u*e1 + v*e2 (u, v in 0..1)."""
    pts = [o, (o[0] + e1[0], o[1] + e1[1]), (o[0] + e1[0] + e2[0], o[1] + e1[1] + e2[1]),
           (o[0] + e2[0], o[1] + e2[1])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = int(np.floor(min(xs))), int(np.floor(min(ys)))
    x1, y1 = int(np.ceil(max(xs))), int(np.ceil(max(ys)))
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    det = e1[0] * e2[1] - e1[1] * e2[0]
    if abs(det) < 1e-6:
        return
    inv = (e2[1] / det, -e2[0] / det, -e1[1] / det, e1[0] / det)
    th, tw = arr.shape[:2]
    # output pixel (x, y) -> texture (u*tw, v*th)
    a = inv[0] * tw
    b = inv[1] * tw
    c = (inv[0] * (x0 + .5 - o[0]) + inv[1] * (y0 + .5 - o[1])) * tw
    d = inv[2] * th
    e = inv[3] * th
    f = (inv[2] * (x0 + .5 - o[0]) + inv[3] * (y0 + .5 - o[1])) * th
    src = Image.fromarray(shade_arr(arr, k))
    patch = src.transform((w, h), Image.AFFINE, (a, b, c, d, e, f),
                          resample=Image.NEAREST)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(p[0] - x0, p[1] - y0) for p in pts], fill=alpha)
    img.paste(patch, (x0, y0), mask)


def shade_arr(arr, k):
    if k == 1.0:
        return arr
    return np.clip(arr.astype(float) * k, 0, 255).astype(np.uint8)


def poly(img, pts, fill):
    """Alpha-blended flat polygon (shadows, glows)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon(pts, fill=fill)
    img.alpha_composite(layer) if img.mode == "RGBA" else img.paste(layer, (0, 0), layer)


class Cam:
    """Oblique camera: ex is one block along +u (right), ey along +v (toward
    the viewer), ez one block up. Visible faces: top, front (+v), right (+u)."""
    LIGHT = {"top": 1.0, "front": .80, "right": .62}

    def __init__(self, ox, oy, ex, ey, ez):
        self.o, self.ex, self.ey, self.ez = (ox, oy), ex, ey, ez

    def p(self, u, v, z=0.0):
        return (self.o[0] + u * self.ex[0] + v * self.ey[0],
                self.o[1] + u * self.ex[1] + v * self.ey[1] - z * self.ez)

    def block(self, img, u, v, z, kind, du=1.0, dv=1.0, dz=1.0, ao=1.0, top=True, faces=("front", "right")):
        topn, siden, lown = BLOCKS[kind]
        side = siden if z >= 0 and kind == "grass" else (lown if kind == "grass" else siden)
        P = self.p
        L = self.LIGHT
        if "front" in faces:
            o = P(u, v + dv, z + dz)
            face(img, o, (self.ex[0] * du, self.ex[1] * du), (0, self.ez * dz), tex(side), L["front"] * ao)
        if "right" in faces:
            o = P(u + du, v + dv, z + dz)
            face(img, o, (-self.ey[0] * dv, -self.ey[1] * dv), (0, self.ez * dz), tex(side), L["right"] * ao)
        if top:
            o = P(u, v, z + dz)
            face(img, o, (self.ex[0] * du, self.ex[1] * du), (self.ey[0] * dv, self.ey[1] * dv), tex(topn),
                 L["top"] * ao)


# ------------------------------------------------------------------- embedding
def png_uri(img, colours=None):
    """PNG data URI. colours quantizes to a palette first: textures use few
    colours, so this keeps a whole world well under a megabyte."""
    if colours:
        rgb = img.convert("RGB") if img.mode != "RGBA" else img
        if img.mode == "RGBA":
            img = img.quantize(colours, method=Image.FASTOCTREE, dither=Image.NONE)
        else:
            img = rgb.quantize(colours, method=Image.MEDIANCUT, dither=Image.NONE)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def image(uri, x, y, w, h, extra=""):
    return (f'<image href="{uri}" x="{x}" y="{y}" width="{w}" height="{h}"'
            f' style="image-rendering:pixelated" preserveAspectRatio="none"{extra}/>')


def tile(name, w, h, scale=4, k=1.0):
    """A texture tiled over w x h pixels at scale px per texel."""
    t = Image.fromarray(shade_arr(tex(name), k)).resize((T * scale, T * scale), Image.NEAREST)
    out = Image.new("RGB", (w, h))
    for y in range(0, h, T * scale):
        for x in range(0, w, T * scale):
            out.paste(t, (x, y))
    return out


def icon(kind, size=64):
    """A single isometric block, for legends and stat rows."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    k = size / 2.05
    cam = Cam(size / 2, 1 + k * .98, (k * .87, k * .5), (-k * .87, k * .5), k * .98)
    cam.block(img, 0, 0, 0, kind)
    return img


def blur(img, r):
    return img.filter(ImageFilter.GaussianBlur(r))
