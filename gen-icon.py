"""Generate iOS home-screen / PWA / browser-tab icons for the NOMI portal.

Modern look: vibrant iridescent gradient (purple → pink → orange) background
with a single bold "N" glyph and a glass-highlight specular. Designed to read
well at iOS home-screen size (180 px) and stay recognizable when iOS masks
to the squircle shape.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Iridescent gradient stops (top-left → bottom-right) ──
# Vivid hot-pink / magenta / amber blend — distinct from any single game's
# accent so the portal reads as "the collection" rather than one game.
GRAD_STOPS = [
    (0.00, (255,  86, 162)),   # hot pink
    (0.40, (220,  64, 200)),   # magenta
    (0.75, (138,  77, 230)),   # violet
    (1.00, ( 46,  41, 110)),   # deep indigo
]
# Warm spec highlight tint (top-left of icon)
SPEC_TINT  = (255, 220, 200)
# "N" glyph color
GLYPH_COL  = (255, 255, 255)


def find_font(size):
    """Find the heaviest available sans-serif. Used for the "N" glyph."""
    for p in [
        "C:/Windows/Fonts/seguibl.ttf",   # Segoe UI Black (cleanest modern weight)
        "C:/Windows/Fonts/Bahnschrift.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/impact.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()


def lerp(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def stops_at(t):
    """Sample the GRAD_STOPS palette at parameter t in [0, 1]."""
    if t <= GRAD_STOPS[0][0]: return GRAD_STOPS[0][1]
    if t >= GRAD_STOPS[-1][0]: return GRAD_STOPS[-1][1]
    for i in range(len(GRAD_STOPS) - 1):
        a_t, a_c = GRAD_STOPS[i]
        b_t, b_c = GRAD_STOPS[i + 1]
        if a_t <= t <= b_t:
            local = (t - a_t) / (b_t - a_t) if b_t > a_t else 0
            return lerp(a_c, b_c, local)
    return GRAD_STOPS[-1][1]


def diagonal_gradient(size):
    """Vivid diagonal gradient used as the icon background. Direction is
    top-left → bottom-right; sampling distance is normalized to the image
    diagonal so the fill is independent of resolution."""
    s = size
    img = Image.new("RGB", (s, s))
    px = img.load()
    diag = math.sqrt(2) * (s - 1)
    for y in range(s):
        for x in range(s):
            t = (x + y) / diag if diag > 0 else 0
            px[x, y] = stops_at(t)
    return img


def add_specular(img):
    """Soft elliptical highlight in the upper-left — gives the icon a glassy
    convex feel that flat gradients lack."""
    s = img.size[0]
    spec = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spec)
    # Big soft ellipse offset upper-left
    sd.ellipse(
        [-s*0.35, -s*0.55, s*0.85, s*0.40],
        fill=(SPEC_TINT[0], SPEC_TINT[1], SPEC_TINT[2], 130),
    )
    spec = spec.filter(ImageFilter.GaussianBlur(radius=s*0.10))
    return Image.alpha_composite(img.convert("RGBA"), spec)


def add_inner_vignette(img):
    """Subtle darkening at the bottom-right corner — counterweight to the
    upper-left highlight for added depth."""
    s = img.size[0]
    vig = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    vd.ellipse(
        [s*0.30, s*0.55, s*1.30, s*1.55],
        fill=(0, 0, 0, 120),
    )
    vig = vig.filter(ImageFilter.GaussianBlur(radius=s*0.12))
    return Image.alpha_composite(img.convert("RGBA"), vig)




def draw_n_glyph(img, weight=0.62):
    """Render the "N" centered. Picks the largest font that comfortably fits
    in `weight` of the canvas width so the letter dominates the icon without
    clipping under iOS's squircle mask."""
    s = img.size[0]
    target_w = s * weight
    target_h = s * 0.58
    font_size = int(s * 0.95)
    font = find_font(font_size)
    d = ImageDraw.Draw(img)
    while font_size > 8:
        bbox = d.textbbox((0, 0), "N", font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= target_w and h <= target_h: break
        font_size -= 2
        font = find_font(font_size)
    bbox = d.textbbox((0, 0), "N", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    tx = (s - text_w) // 2 - bbox[0]
    ty = (s - text_h) // 2 - bbox[1] - int(s * 0.04)

    # Soft drop shadow under the glyph for depth
    shadow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    off = max(1, int(s * 0.012))
    sd.text((tx + off, ty + off + int(s * 0.005)), "N",
            font=font, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(1, s * 0.012)))
    img = Image.alpha_composite(img, shadow)

    # Main glyph — pure white for max contrast against the vibrant gradient
    d = ImageDraw.Draw(img)
    d.text((tx, ty), "N", font=font, fill=GLYPH_COL + (255,))

    return img


def draw_icon(size):
    """Full modern icon: gradient + specular + vignette + N glyph."""
    bg = diagonal_gradient(size).convert("RGBA")
    bg = add_specular(bg)
    bg = add_inner_vignette(bg)
    bg = draw_n_glyph(bg)
    return bg


def draw_small_icon(size):
    """Same design at favicon sizes — drop the grain (visible noise at 16 px)
    and skip the highlight pass since it's invisible at this scale."""
    bg = diagonal_gradient(size).convert("RGBA")
    bg = add_specular(bg)
    bg = draw_n_glyph(bg, weight=0.85)
    return bg


def save_opaque(img, path):
    """Apple touch icons must be opaque RGB — Safari has been seen to drop
    RGBA icons silently from the Favorites grid."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(path, format="PNG", optimize=True)


def main():
    big_sizes = [
        ("apple-touch-icon.png", 180),
        ("apple-touch-icon-precomposed.png", 180),
        ("apple-touch-icon-152.png", 152),
        ("apple-touch-icon-167.png", 167),
        ("apple-touch-icon-120.png", 120),
        ("icon-512.png", 512),
        ("icon-192.png", 192),
    ]
    for name, sz in big_sizes:
        img = draw_icon(sz)
        out = os.path.join(OUT_DIR, name)
        save_opaque(img, out)
        print(f"  wrote {name}  ({sz}x{sz}, {os.path.getsize(out)} bytes)")

    small_sizes = [
        ("favicon-48.png", 48),
        ("favicon-32.png", 32),
        ("favicon-16.png", 16),
    ]
    small_imgs = []
    for name, sz in small_sizes:
        img = draw_small_icon(sz)
        out = os.path.join(OUT_DIR, name)
        save_opaque(img, out)
        small_imgs.append((sz, img.convert("RGBA")))
        print(f"  wrote {name}  ({sz}x{sz}, {os.path.getsize(out)} bytes)")

    ico_path = os.path.join(OUT_DIR, "favicon.ico")
    sorted_imgs = sorted(small_imgs, key=lambda x: -x[0])
    primary = sorted_imgs[0][1]
    extras = [img for (_, img) in sorted_imgs[1:]]
    primary.save(
        ico_path, format="ICO",
        sizes=[(s, s) for (s, _) in sorted_imgs],
        append_images=extras,
    )
    print(f"  wrote favicon.ico ({', '.join(f'{s}x{s}' for s, _ in sorted_imgs)}, "
          f"{os.path.getsize(ico_path)} bytes)")


if __name__ == "__main__":
    main()
