"""Generate iOS home-screen icons for the NOMI portal.

Outputs apple-touch-icon.png (180x180), icon-512.png, icon-192.png, and
favicon-32.png — sized for iOS home screen, modern Android web manifest,
and browser tab.

The look matches the portal: dark steel background, gold "NOMI" wordmark,
blood-red accent slash. Designed to read well at the iOS home-screen size.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, sys

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── color palette (matches portal/index.html :root vars) ───────────────────
BG_TOP    = (26, 26, 32)       # #1a1a20
BG_MID    = (16, 16, 18)       # #101012
BG_BOTTOM = (8, 8, 10)         # #08080a
GOLD      = (240, 200, 80)     # #f0c850
GOLD_DARK = (170, 120, 30)
BONE      = (232, 228, 216)    # #e8e4d8
BLOOD     = (224, 20, 42)      # #e0142a
BLOOD_GLOW= (255, 60, 80)
STEEL     = (74, 74, 82)       # #4a4a52


def find_font(size, bold=True):
    """Try to find a heavy display font on the system. Falls back to default."""
    candidates_bold = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/seguibl.ttf",   # Segoe UI Black
        "C:/Windows/Fonts/Bahnschrift.ttf",
    ]
    candidates_regular = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for p in (candidates_bold if bold else candidates_regular):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()


def vertical_gradient(size, top, mid, bottom):
    """Three-stop vertical gradient: top→mid in upper half, mid→bottom below."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        if y < h // 2:
            t = y / (h / 2 - 1) if h > 2 else 0
            r = round(top[0]    * (1-t) + mid[0]    * t)
            g = round(top[1]    * (1-t) + mid[1]    * t)
            b = round(top[2]    * (1-t) + mid[2]    * t)
        else:
            t = (y - h//2) / (h - h//2 - 1) if h > 2 else 0
            r = round(mid[0]    * (1-t) + bottom[0] * t)
            g = round(mid[1]    * (1-t) + bottom[1] * t)
            b = round(mid[2]    * (1-t) + bottom[2] * t)
        px[0, y] = (r, g, b)
    return img.resize((w, h))


def draw_icon(size):
    """Render the NOMI icon at the given square size and return an RGBA Image."""
    s = size
    bg = vertical_gradient((s, s), BG_TOP, BG_MID, BG_BOTTOM).convert("RGBA")

    # ── soft red glow behind everything ──
    glow_layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse(
        [s*0.10, s*0.05, s*0.90, s*0.85],
        fill=(BLOOD[0], BLOOD[1], BLOOD[2], 110),
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=s*0.10))
    bg = Image.alpha_composite(bg, glow_layer)

    # ── inner border ring (subtle steel) ──
    d = ImageDraw.Draw(bg)
    pad = max(2, int(s * 0.045))
    d.rounded_rectangle(
        [pad, pad, s-pad-1, s-pad-1],
        radius=int(s * 0.06),
        outline=(STEEL[0], STEEL[1], STEEL[2], 200),
        width=max(1, int(s * 0.008)),
    )

    # ── decorative tally marks (top corners) ──
    mark_y = int(s * 0.20)
    mark_w = max(1, int(s * 0.018))
    for i in range(3):
        x_l = int(s * 0.13) + i * int(s * 0.038)
        x_r = s - int(s * 0.13) - i * int(s * 0.038)
        d.line([(x_l, mark_y - s*0.04), (x_l, mark_y + s*0.04)],
               fill=(140, 140, 148), width=mark_w)
        d.line([(x_r, mark_y - s*0.04), (x_r, mark_y + s*0.04)],
               fill=(140, 140, 148), width=mark_w)

    # ── main wordmark "NOMI" — heavy condensed feel ──
    word = "NOMI"
    # iterate to find the largest font that fits in ~64% of width with some
    # safety margin (the "M" tends to be wider than textbbox reports for
    # display fonts like Impact). The icon reads better with the wordmark
    # comfortably inside the border ring than maxed out edge-to-edge.
    target_w = s * 0.64
    font_size = int(s * 0.50)
    font = find_font(font_size)
    while font_size > 8:
        bbox = d.textbbox((0, 0), word, font=font, stroke_width=0)
        w = bbox[2] - bbox[0]
        if w <= target_w: break
        font_size -= 2
        font = find_font(font_size)
    bbox = d.textbbox((0, 0), word, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    # vertically center, slight upward bias
    tx = (s - text_w) // 2 - bbox[0]
    ty = (s - text_h) // 2 - bbox[1] - int(s * 0.05)

    # subtle text shadow
    shadow_layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    sd.text((tx + max(1, int(s*0.012)), ty + max(1, int(s*0.012))), word,
            font=font, fill=(0, 0, 0, 200))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=max(1, s*0.012)))
    bg = Image.alpha_composite(bg, shadow_layer)
    d = ImageDraw.Draw(bg)

    # gold gradient text via two passes (cheap fake gradient: draw in dark gold,
    # then upper half overlay in bright gold using a mask)
    d.text((tx, ty), word, font=font, fill=GOLD_DARK)
    # upper-half highlight
    bright_layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bright_layer)
    bd.text((tx, ty), word, font=font, fill=GOLD + (255,))
    mask = Image.new("L", (s, s), 0)
    md = ImageDraw.Draw(mask)
    # gradient mask: solid alpha at top, fading to transparent in lower half
    grad = Image.new("L", (1, s))
    gp = grad.load()
    for y in range(s):
        if y < ty + text_h * 0.55:
            gp[0, y] = 255
        elif y < ty + text_h:
            t = (y - (ty + text_h * 0.55)) / max(1, (text_h * 0.45))
            gp[0, y] = max(0, int(255 * (1 - t)))
        else:
            gp[0, y] = 0
    mask = grad.resize((s, s))
    bright_layer.putalpha(mask)
    bg = Image.alpha_composite(bg, bright_layer)

    # ── blood-red slash underline ──
    d = ImageDraw.Draw(bg)
    bar_y = ty + text_h + int(s * 0.04)
    bar_x1 = int(s * 0.20)
    bar_x2 = s - int(s * 0.20)
    bar_h = max(2, int(s * 0.022))
    # glow behind the bar
    glow_bar = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_bar)
    gd.rounded_rectangle(
        [bar_x1 - 4, bar_y - 4, bar_x2 + 4, bar_y + bar_h + 4],
        radius=bar_h, fill=(BLOOD_GLOW[0], BLOOD_GLOW[1], BLOOD_GLOW[2], 160),
    )
    glow_bar = glow_bar.filter(ImageFilter.GaussianBlur(radius=max(1, s*0.025)))
    bg = Image.alpha_composite(bg, glow_bar)
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle(
        [bar_x1, bar_y, bar_x2, bar_y + bar_h],
        radius=bar_h // 2,
        fill=BLOOD,
    )

    # ── tagline below the slash: spaced "GAMES" reads as a label ──
    tagline = "G A M E S"
    tg_size = max(7, int(s * 0.075))
    tg_font = find_font(tg_size, bold=True)
    tg_bbox = d.textbbox((0, 0), tagline, font=tg_font)
    tg_w = tg_bbox[2] - tg_bbox[0]
    tg_x = (s - tg_w) // 2 - tg_bbox[0]
    tg_y = bar_y + bar_h + int(s * 0.03)
    d.text((tg_x, tg_y), tagline, font=tg_font, fill=(180, 180, 188))

    return bg


def draw_small_icon(size):
    """Single-letter "N" mark for browser tabs / favicons where the wordmark
    becomes illegible. Same color story (steel + gold + blood)."""
    s = size
    bg = vertical_gradient((s, s), BG_TOP, BG_MID, BG_BOTTOM).convert("RGBA")
    d = ImageDraw.Draw(bg)

    # blood corner accent
    pts = [(0, int(s*0.65)), (int(s*0.35), s), (0, s)]
    d.polygon(pts, fill=BLOOD)

    # giant "N" — gold
    letter = "N"
    font_size = int(s * 0.95)
    font = find_font(font_size)
    bbox = d.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    tx = (s - text_w) // 2 - bbox[0]
    ty = (s - text_h) // 2 - bbox[1] - int(s * 0.05)
    d.text((tx, ty), letter, font=font, fill=GOLD)
    return bg


def save_opaque(img, path):
    """Save as opaque RGB. Apple recommends touch-icons have no transparency
    — Safari has been seen to skip RGBA icons in the Favorites grid."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(path, format="PNG", optimize=True)


def main():
    # iOS home screen + PWA — full wordmark.
    # 152/167/180 cover historical iOS targets (iPhone, iPad, iPad Pro).
    # Older iOS Safari falls back through these by size, so providing a few
    # sizes (and the precomposed variant) maximizes the chance Safari picks
    # one up across versions.
    big_sizes = [
        ("apple-touch-icon.png", 180),              # iOS modern + default
        ("apple-touch-icon-precomposed.png", 180),  # Pre-iOS-7 fallback name
        ("apple-touch-icon-152.png", 152),          # iPad
        ("apple-touch-icon-167.png", 167),          # iPad Pro
        ("apple-touch-icon-120.png", 120),          # iPhone @3x for older iOS
        ("icon-512.png", 512),                       # PWA / large
        ("icon-192.png", 192),                       # PWA / Android standard
    ]
    for name, sz in big_sizes:
        img = draw_icon(sz)
        out = os.path.join(OUT_DIR, name)
        save_opaque(img, out)
        print(f"  wrote {name}  ({sz}x{sz}, {os.path.getsize(out)} bytes)")

    # Browser-tab favicons — single "N" reads at small sizes
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

    # Multi-resolution favicon.ico — iOS Safari's Start Page "Favorites"
    # iconography fetcher tries /favicon.ico first; a 404 here makes it
    # mark the site as iconless and fall back to a letter avatar.
    ico_path = os.path.join(OUT_DIR, "favicon.ico")
    sorted_imgs = sorted(small_imgs, key=lambda x: -x[0])  # largest first
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
