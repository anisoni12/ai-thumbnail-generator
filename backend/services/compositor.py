from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
import io
import re
import random
import math

CANVAS_W = 1280
CANVAS_H = 720

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple:
    try:
        hex_color = hex_color.strip().lstrip("#")
        if len(hex_color) != 6:
            raise ValueError
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (26, 26, 46)

def _blend(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _darken(rgb: tuple, amount: float) -> tuple:
    return _blend(rgb, (0, 0, 0), amount)

def _lighten(rgb: tuple, amount: float) -> tuple:
    return _blend(rgb, (255, 255, 255), amount)

def _luminance(rgb: tuple) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]

def _contrast_color(rgb: tuple) -> tuple:
    return (10, 10, 10) if _luminance(rgb) > 128 else (245, 245, 245)

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    bold_paths = [
        "C:/Windows/Fonts/Impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Oswald-Bold.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    ]
    regular_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ]
    for path in (bold_paths if bold else regular_paths):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _has_real_alpha(img: Image.Image) -> bool:
    if img.mode != "RGBA":
        return False
    alpha = img.split()[-1]
    return alpha.getextrema()[0] < 250

def _topic_tag(prompt_text: str) -> str:
    text = (prompt_text or "").lower()
    keywords = [
        ("react", "REACT"), ("next.js", "NEXT.JS"), ("nextjs", "NEXT.JS"),
        ("node", "NODE.JS"), ("express", "EXPRESS"),
        ("python", "PYTHON"), ("django", "DJANGO"), ("flask", "FLASK"),
        ("fastapi", "FASTAPI"), ("javascript", "JS"), ("typescript", "TS"),
        ("java", "JAVA"), ("spring", "SPRING"), ("golang", "GO"),
        ("rust", "RUST"), ("docker", "DOCKER"), ("kubernetes", "K8S"),
        ("devops", "DEVOPS"), ("aws", "AWS"), ("cloud", "CLOUD"),
        ("ai", "AI"), ("llm", "LLM"), ("ml", "ML"), ("data", "DATA"),
        ("dsa", "DSA"), ("system design", "SYS DESIGN"),
        ("sql", "SQL"), ("mongo", "MONGODB"),
        ("html", "HTML"), ("css", "CSS"), ("tailwind", "TAILWIND"),
        ("hacking", "HACKING"), ("security", "SECURITY"), ("cyber", "CYBER"),
    ]
    for k, label in keywords:
        if k in text:
            return label
    words = re.findall(r"[A-Za-z]+", prompt_text or "")
    if words:
        return words[0].upper()[:10]
    return "TUTORIAL"

def _duration_tag(prompt_text: str) -> str | None:
    if not prompt_text:
        return None
    m = re.search(r"(\d+)\s*(hours?|hrs?|h)\b", prompt_text, re.IGNORECASE)
    if m:
        n = m.group(1)
        return f"{n}HR COURSE" if int(n) != 1 else "1HR COURSE"
    m = re.search(r"(\d+)\s*(minutes?|mins?|m)\b", prompt_text, re.IGNORECASE)
    if m:
        return f"{m.group(1)} MIN"
    return None

def _fit_text_lines(draw, text, max_w, max_h, max_size, min_size, stroke_w=0):
    words = text.split()
    size = max_size
    while size >= min_size:
        font = _load_font(size, bold=True)
        line_h = int(size * 1.15)
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            w = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_w)[2]
            if w <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        total_h = len(lines) * line_h
        widest = max((draw.textbbox((0, 0), l, font=font, stroke_width=stroke_w)[2] for l in lines), default=0)
        if widest <= max_w and total_h <= max_h:
            return lines, size, line_h
        size -= 4
    font = _load_font(min_size, bold=True)
    line_h = int(min_size * 1.15)
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        w = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_w)[2]
        if w <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines, min_size, line_h

def _draw_text_with_shadow(draw, pos, text, font, fill, shadow_offset=(3, 5),
                           shadow_opacity=180, stroke_width=0, stroke_fill=None):
    sx, sy = pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]
    draw.text((sx, sy), text, font=font, fill=(0, 0, 0, shadow_opacity),
              stroke_width=stroke_width, stroke_fill=(0, 0, 0, shadow_opacity))
    draw.text(pos, text, font=font, fill=fill,
              stroke_width=stroke_width, stroke_fill=stroke_fill or (0, 0, 0, 220))

def _vertical_gradient(canvas, top_color, bottom_color, alpha_top=255, alpha_bottom=255):
    grad = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grad)
    for y in range(CANVAS_H):
        t = y / CANVAS_H
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        a = int(alpha_top + (alpha_bottom - alpha_top) * t)
        draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b, a))
    canvas.alpha_composite(grad)
    return canvas

def _draw_chip(draw, x, y, text, font, bg_fill, text_fill, radius=12, pad_x=18, pad_h=40):
    tw = draw.textbbox((0, 0), text, font=font)[2]
    th = draw.textbbox((0, 0), text, font=font)[3]
    w = tw + pad_x * 2
    draw.rounded_rectangle([x, y, x + w, y + pad_h], radius=radius, fill=bg_fill)
    draw.text((x + pad_x, y + (pad_h - th) // 2), text, font=font, fill=text_fill)
    return x + w

def _paste_person(canvas, headshot_bytes, x_pos, y_pos, target_h, accent_rgb, flip=False):
    try:
        source = Image.open(io.BytesIO(headshot_bytes)).convert("RGBA")
        source = ImageOps.exif_transpose(source)
        source = ImageEnhance.Contrast(source).enhance(1.15)
        source = ImageEnhance.Sharpness(source).enhance(1.3)
        source = ImageEnhance.Color(source).enhance(1.1)

        is_cutout = _has_real_alpha(source)

        if is_cutout:
            bbox = source.getbbox()
            if bbox:
                source = source.crop(bbox)
            scale = target_h / source.height
            target_w = int(source.width * scale)
            source = source.resize((target_w, target_h), Image.LANCZOS)
            if flip:
                source = ImageOps.mirror(source)

            alpha = source.split()[-1]

            # Deep drop shadow
            shadow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
            shadow_solid = Image.new("RGBA", source.size, (0, 0, 0, 220))
            shadow_solid.putalpha(alpha)
            shadow_layer.paste(shadow_solid, (x_pos + 20, y_pos + 30), shadow_solid)
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(32))
            canvas.alpha_composite(shadow_layer)

            # Accent rim glow
            glow_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
            glow_solid = Image.new("RGBA", source.size, accent_rgb + (160,))
            glow_solid.putalpha(alpha)
            glow_layer.paste(glow_solid, (x_pos - 4, y_pos - 4), glow_solid)
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(22))
            canvas.alpha_composite(glow_layer)

            canvas.alpha_composite(source, dest=(x_pos, y_pos))
        else:
            aspect = source.width / source.height
            tw = int(target_h * aspect)
            source = source.resize((tw, target_h), Image.LANCZOS)
            crop_w = int(target_h * 0.72)
            left = max(0, (tw - crop_w) // 2)
            source = source.crop((left, 0, left + crop_w, target_h))
            tw = source.width
            if flip:
                source = ImageOps.mirror(source)

            glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
            gdraw = ImageDraw.Draw(glow)
            gdraw.rounded_rectangle([x_pos - 20, y_pos - 20, x_pos + tw + 20, y_pos + target_h + 20],
                                     radius=40, fill=accent_rgb + (110,))
            glow = glow.filter(ImageFilter.GaussianBlur(30))
            canvas.alpha_composite(glow)

            mask = Image.new("L", (tw, target_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw - 1, target_h - 1], radius=24, fill=255)
            canvas.paste(source, (x_pos, y_pos), mask)

            border = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
            ImageDraw.Draw(border).rounded_rectangle(
                [x_pos - 4, y_pos - 4, x_pos + tw + 4, y_pos + target_h + 4],
                radius=28, outline=accent_rgb + (255,), width=5)
            canvas.alpha_composite(border)

    except Exception as e:
        print(f"[compositor] paste_person failed: {e}")
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 1 — POWER SPLIT
# ─────────────────────────────────────────────────────────────────────────────
def _template_power_split(headshot_bytes, design, prompt_text):
    bg_color     = design.get("bg_color",     "#0a0a14")
    accent_color = design.get("accent_color", "#00d4ff")
    title        = design.get("title",        "TUTORIAL").strip().upper()
    subtitle     = design.get("subtitle",     "BEGINNER TO ADVANCED").strip().upper()

    bg_rgb     = _hex_to_rgb(bg_color)
    accent_rgb = _hex_to_rgb(accent_color)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), bg_rgb + (255,))
    draw   = ImageDraw.Draw(canvas)

    SPLIT = 600
    poly = [(SPLIT - 100, 0), (CANVAS_W, 0), (CANVAS_W, CANVAS_H), (SPLIT + 60, CANVAS_H)]
    draw.polygon(poly, fill=_darken(accent_rgb, 0.55) + (255,))
    inner_poly = [(SPLIT, 0), (CANVAS_W, 0), (CANVAS_W, CANVAS_H), (SPLIT + 140, CANVAS_H)]
    draw.polygon(inner_poly, fill=accent_rgb + (255,))

    # Vignette right edge
    vig = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vig)
    for i, alpha in enumerate([40, 30, 20, 10]):
        vdraw.rectangle([CANVAS_W - (i+1)*60, 0, CANVAS_W, CANVAS_H], fill=(0, 0, 0, alpha))
    canvas.alpha_composite(vig)

    # Subtle grid on left
    for y in range(0, CANVAS_H, 40):
        draw.line([(0, y), (SPLIT - 60, y)], fill=(255, 255, 255, 8), width=1)

    # Vertical accent rule
    draw.rectangle([56, 70, 60, CANVAS_H - 70], fill=accent_rgb + (200,))

    # Title
    tdraw = ImageDraw.Draw(canvas)
    lines, size, line_h = _fit_text_lines(tdraw, title, 490, 380, 148, 56, stroke_w=3)
    font = _load_font(size, bold=True)
    y = 110
    for line in lines:
        _draw_text_with_shadow(tdraw, (76, y), line, font,
                               fill=(255, 255, 255), shadow_offset=(4, 6),
                               shadow_opacity=160, stroke_width=3, stroke_fill=(0, 0, 0, 200))
        y += line_h

    # Subtitle badge
    sub_font = _load_font(34, bold=True)
    sw = tdraw.textbbox((0, 0), subtitle, font=sub_font)[2]
    pill_w = min(490, sw + 44)
    tdraw.rounded_rectangle([76, y + 24, 76 + pill_w, y + 67], radius=8, fill=accent_rgb + (255,))
    label_color = _contrast_color(accent_rgb)
    tdraw.text((76 + 16, y + 30), subtitle, font=sub_font, fill=label_color)

    # Chips
    chip_font = _load_font(24, bold=True)
    topic    = _topic_tag(prompt_text)
    duration = _duration_tag(prompt_text)
    cx = 76
    cy = CANVAS_H - 76
    rx = _draw_chip(tdraw, cx, cy, topic, chip_font,
                    bg_fill=(255, 255, 255, 220), text_fill=(10, 10, 10), radius=6, pad_h=36)
    if duration:
        _draw_chip(tdraw, rx + 14, cy, duration, chip_font,
                   bg_fill=accent_rgb + (255,), text_fill=label_color, radius=6, pad_h=36)

    if headshot_bytes:
        _paste_person(canvas, headshot_bytes, SPLIT - 30, CANVAS_H - 700, 700, accent_rgb)

    draw.rectangle([0, CANVAS_H - 7, CANVAS_W, CANVAS_H], fill=accent_rgb + (255,))
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 2 — CINEMATIC DARK
# ─────────────────────────────────────────────────────────────────────────────
def _template_cinematic_dark(headshot_bytes, design, prompt_text):
    bg_color     = design.get("bg_color",     "#060612")
    accent_color = design.get("accent_color", "#ff6b35")
    title        = design.get("title",        "TUTORIAL").strip().upper()
    subtitle     = design.get("subtitle",     "BEGINNER TO ADVANCED").strip().upper()

    bg_rgb     = _hex_to_rgb(bg_color)
    accent_rgb = _hex_to_rgb(accent_color)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), bg_rgb + (255,))

    # Atmosphere blobs
    atm = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(atm)
    adraw.ellipse([-200, -200, 900, 900], fill=_blend(accent_rgb, bg_rgb, 0.4) + (90,))
    adraw.ellipse([700, 300, CANVAS_W + 300, CANVAS_H + 300],
                  fill=_blend(accent_rgb, (30, 10, 60), 0.6) + (70,))
    atm = atm.filter(ImageFilter.GaussianBlur(120))
    canvas.alpha_composite(atm)

    # Dot grid
    dots = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ddraw = ImageDraw.Draw(dots)
    for x in range(0, CANVAS_W, 44):
        for y in range(0, CANVAS_H, 44):
            ddraw.ellipse([x-1, y-1, x+1, y+1], fill=(255, 255, 255, 18))
    canvas.alpha_composite(dots)

    if headshot_bytes:
        _paste_person(canvas, headshot_bytes, CANVAS_W - 570, CANVAS_H - 710, 710, accent_rgb, flip=True)

    # Left scrim
    scrim = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    for x in range(680):
        alpha = int(200 * (1 - x / 680) ** 0.6)
        ImageDraw.Draw(scrim).line([(x, 0), (x, CANVAS_H)], fill=(0, 0, 0, alpha))
    canvas.alpha_composite(scrim)

    draw = ImageDraw.Draw(canvas)

    lines, size, line_h = _fit_text_lines(draw, title, 560, 380, 154, 56, stroke_w=3)
    font = _load_font(size, bold=True)
    y = 90

    # Glow layer
    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for line in lines:
        gdraw.text((64, y), line, font=font, fill=accent_rgb + (200,))
        y += line_h
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(glow)

    draw = ImageDraw.Draw(canvas)
    y = 90
    for line in lines:
        _draw_text_with_shadow(draw, (64, y), line, font,
                               fill=(255, 255, 255), shadow_offset=(5, 7),
                               shadow_opacity=200, stroke_width=3, stroke_fill=(0, 0, 0, 220))
        y += line_h

    draw.rectangle([64, y + 16, 64 + 420, y + 20], fill=accent_rgb + (255,))
    sub_font = _load_font(34, bold=True)
    sw = draw.textbbox((0, 0), subtitle, font=sub_font)[2]
    pill_w = min(560, sw + 44)
    draw.rounded_rectangle([64, y + 30, 64 + pill_w, y + 72], radius=8, fill=accent_rgb + (240,))
    draw.text((64 + 16, y + 37), subtitle, font=sub_font, fill=_contrast_color(accent_rgb))

    chip_font = _load_font(24, bold=True)
    topic    = _topic_tag(prompt_text)
    duration = _duration_tag(prompt_text)
    cx = 64
    rx = _draw_chip(draw, cx, CANVAS_H - 72, topic, chip_font,
                    bg_fill=(255, 255, 255, 220), text_fill=(10, 10, 10), radius=6, pad_h=36)
    if duration:
        _draw_chip(draw, rx + 12, CANVAS_H - 72, duration, chip_font,
                   bg_fill=accent_rgb + (255,), text_fill=_contrast_color(accent_rgb),
                   radius=6, pad_h=36)

    draw.rectangle([0, CANVAS_H - 6, CANVAS_W, CANVAS_H], fill=accent_rgb + (255,))
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 3 — BOLD IMPACT
# ─────────────────────────────────────────────────────────────────────────────
def _template_bold_impact(headshot_bytes, design, prompt_text):
    accent_color = design.get("accent_color", "#FFD600")
    title        = design.get("title",        "TUTORIAL").strip().upper()
    subtitle     = design.get("subtitle",     "BEGINNER TO ADVANCED").strip().upper()

    accent_rgb = _hex_to_rgb(accent_color)

    bg_palettes = [
        (accent_rgb, _darken(accent_rgb, 0.55)),
        ((220, 40, 40), (120, 10, 10)),
        ((0, 130, 220), (0, 50, 120)),
        ((30, 180, 80), (10, 80, 30)),
    ]
    top_bg, bot_bg = random.choice(bg_palettes)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), top_bg + (255,))
    _vertical_gradient(canvas, top_bg, bot_bg, alpha_top=0, alpha_bottom=200)

    # Diagonal stripe texture
    stripe = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    sdraw  = ImageDraw.Draw(stripe)
    stripe_dark = _darken(top_bg, 0.18) + (255,)
    for x in range(-300, CANVAS_W + 400, 70):
        sdraw.polygon([(x, 0), (x+35, 0), (x+35+CANVAS_H, CANVAS_H), (x+CANVAS_H, CANVAS_H)],
                      fill=stripe_dark)
    canvas.alpha_composite(stripe)

    # Dark left panel
    dark_panel = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(dark_panel).rectangle([0, 0, 640, CANVAS_H], fill=(8, 8, 12, 236))
    canvas.alpha_composite(dark_panel)

    # Diagonal cut edge
    cut = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(cut).polygon([(600, 0), (660, 0), (580, CANVAS_H), (520, CANVAS_H)],
                                 fill=accent_rgb + (255,))
    canvas.alpha_composite(cut)

    if headshot_bytes:
        _paste_person(canvas, headshot_bytes, 640, CANVAS_H - 700, 700, accent_rgb, flip=True)

    draw = ImageDraw.Draw(canvas)

    lines, size, line_h = _fit_text_lines(draw, title, 530, 380, 148, 52, stroke_w=4)
    font = _load_font(size, bold=True)
    y = 100
    for line in lines:
        _draw_text_with_shadow(draw, (48, y), line, font,
                               fill=accent_rgb, shadow_offset=(4, 6),
                               shadow_opacity=200, stroke_width=4, stroke_fill=(0, 0, 0, 200))
        y += line_h

    sub_font = _load_font(32, bold=True)
    sw = draw.textbbox((0, 0), subtitle, font=sub_font)[2]
    pill_w = min(530, sw + 44)
    draw.rounded_rectangle([48, y + 20, 48 + pill_w, y + 62], radius=8, fill=(255, 255, 255, 240))
    draw.text((48 + 16, y + 26), subtitle, font=sub_font, fill=(12, 12, 18))

    chip_font = _load_font(22, bold=True)
    topic    = _topic_tag(prompt_text)
    duration = _duration_tag(prompt_text)
    cx = 48
    rx = _draw_chip(draw, cx, CANVAS_H - 70, topic, chip_font,
                    bg_fill=accent_rgb + (255,), text_fill=_contrast_color(accent_rgb),
                    radius=6, pad_h=34)
    if duration:
        _draw_chip(draw, rx + 12, CANVAS_H - 70, duration, chip_font,
                   bg_fill=(255, 255, 255, 200), text_fill=(10, 10, 10), radius=6, pad_h=34)

    draw.rectangle([0, CANVAS_H - 7, CANVAS_W, CANVAS_H], fill=accent_rgb + (255,))
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 4 — EDITORIAL MAGAZINE
# ─────────────────────────────────────────────────────────────────────────────
def _template_editorial(headshot_bytes, design, prompt_text):
    accent_color = design.get("accent_color", "#e63946")
    title        = design.get("title",        "TUTORIAL").strip().upper()
    subtitle     = design.get("subtitle",     "BEGINNER TO ADVANCED").strip().upper()

    accent_rgb = _hex_to_rgb(accent_color)

    is_dark  = random.random() > 0.45
    bg_rgb   = (10, 10, 16) if is_dark else (248, 244, 238)
    text_rgb = (240, 236, 228) if is_dark else (16, 12, 10)
    panel_rgb = _blend(bg_rgb, (128, 128, 128), 0.08)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), bg_rgb + (255,))
    draw   = ImageDraw.Draw(canvas)

    # Top accent bar
    draw.rectangle([0, 0, CANVAS_W, 8], fill=accent_rgb + (255,))

    DIV = 720
    draw.rectangle([DIV, 8, DIV + 4, CANVAS_H - 8], fill=accent_rgb + (255,))

    panel = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rectangle([0, 8, DIV - 2, CANVAS_H], fill=panel_rgb + (255,))
    canvas.alpha_composite(panel)

    draw = ImageDraw.Draw(canvas)

    MARGIN = 60
    lines, size, line_h = _fit_text_lines(draw, title, DIV - MARGIN * 2, 390, 136, 48)
    font = _load_font(size, bold=True)
    y = 80
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=text_rgb)
        y += line_h

    draw.rectangle([MARGIN, y + 18, MARGIN + 380, y + 24], fill=accent_rgb + (255,))

    sub_font = _load_font(34, bold=True)
    draw.text((MARGIN, y + 36), subtitle, font=sub_font, fill=accent_rgb)

    chip_font = _load_font(22, bold=True)
    topic    = _topic_tag(prompt_text)
    duration = _duration_tag(prompt_text)
    cy = CANVAS_H - 72
    cx = MARGIN
    rx = _draw_chip(draw, cx, cy, topic, chip_font,
                    bg_fill=accent_rgb + (255,), text_fill=_contrast_color(accent_rgb),
                    radius=6, pad_h=34)
    if duration:
        _draw_chip(draw, rx + 12, cy, duration, chip_font,
                   bg_fill=(180, 180, 180, 200) if is_dark else (60, 60, 60, 220),
                   text_fill=(240, 240, 240), radius=6, pad_h=34)

    if headshot_bytes:
        _paste_person(canvas, headshot_bytes, DIV + 20, CANVAS_H - 690, 690, accent_rgb, flip=True)

    draw.rectangle([0, CANVAS_H - 7, CANVAS_W, CANVAS_H], fill=accent_rgb + (255,))
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 5 — NEON CYBER
# ─────────────────────────────────────────────────────────────────────────────
def _template_neon_cyber(headshot_bytes, design, prompt_text):
    accent_color = design.get("accent_color", "#00ffcc")
    title        = design.get("title",        "TUTORIAL").strip().upper()
    subtitle     = design.get("subtitle",     "BEGINNER TO ADVANCED").strip().upper()

    accent_rgb = _hex_to_rgb(accent_color)
    second_rgb = _blend(accent_rgb, (255, 0, 255), 0.45)
    bg_rgb     = (3, 3, 14)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), bg_rgb + (255,))

    grid = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)
    for x in range(0, CANVAS_W, 50):
        gdraw.line([(x, 0), (x, CANVAS_H)], fill=accent_rgb + (18,), width=1)
    for y in range(0, CANVAS_H, 50):
        gdraw.line([(0, y), (CANVAS_W, y)], fill=accent_rgb + (18,), width=1)
    canvas.alpha_composite(grid)

    horiz = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(horiz).ellipse([-100, 420, CANVAS_W + 100, CANVAS_H + 200], fill=accent_rgb + (50,))
    horiz = horiz.filter(ImageFilter.GaussianBlur(60))
    canvas.alpha_composite(horiz)

    scan = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan)
    for y in range(0, CANVAS_H, 3):
        scan_draw.line([(0, y), (CANVAS_W, y)], fill=(0, 0, 0, 35), width=1)
    canvas.alpha_composite(scan)

    if headshot_bytes:
        _paste_person(canvas, headshot_bytes, 30, CANVAS_H - 700, 700, accent_rgb)

    scrim = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    for x in range(560, CANVAS_W):
        alpha = int(180 * ((x - 560) / (CANVAS_W - 560)) ** 0.5)
        ImageDraw.Draw(scrim).line([(x, 0), (x, CANVAS_H)], fill=(0, 0, 0, alpha))
    canvas.alpha_composite(scrim)

    draw = ImageDraw.Draw(canvas)

    TEXT_X = 630
    lines, size, line_h = _fit_text_lines(draw, title, 590, 380, 148, 52, stroke_w=2)
    font = _load_font(size, bold=True)
    y = 90

    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gdraw2 = ImageDraw.Draw(glow)
    for line in lines:
        gdraw2.text((TEXT_X + 5, y + 4), line, font=font, fill=second_rgb + (130,))
        gdraw2.text((TEXT_X - 5, y - 3), line, font=font, fill=accent_rgb  + (100,))
        y += line_h
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    canvas.alpha_composite(glow)

    draw = ImageDraw.Draw(canvas)
    y = 90
    for line in lines:
        _draw_text_with_shadow(draw, (TEXT_X, y), line, font,
                               fill=(255, 255, 255), shadow_offset=(4, 6),
                               shadow_opacity=200, stroke_width=2, stroke_fill=(0, 0, 0, 200))
        y += line_h

    sub_font = _load_font(32, bold=True)
    sw = draw.textbbox((0, 0), subtitle, font=sub_font)[2]
    box_w = min(590, sw + 44)

    neon_box = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(neon_box).rounded_rectangle(
        [TEXT_X, y + 18, TEXT_X + box_w, y + 62], radius=5,
        outline=accent_rgb + (255,), width=2)
    neon_box = neon_box.filter(ImageFilter.GaussianBlur(4))
    canvas.alpha_composite(neon_box)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([TEXT_X, y + 18, TEXT_X + box_w, y + 62],
                            radius=5, outline=accent_rgb + (255,), width=2)
    draw.text((TEXT_X + 16, y + 24), subtitle, font=sub_font, fill=accent_rgb)

    chip_font = _load_font(22, bold=True)
    topic    = _topic_tag(prompt_text)
    duration = _duration_tag(prompt_text)
    cx = TEXT_X
    rx = _draw_chip(draw, cx, CANVAS_H - 70, topic, chip_font,
                    bg_fill=accent_rgb + (28,), text_fill=accent_rgb, radius=6, pad_h=34)
    draw.rounded_rectangle([cx, CANVAS_H - 70, rx, CANVAS_H - 70 + 34],
                            radius=6, outline=accent_rgb + (200,), width=2)
    if duration:
        rx2 = _draw_chip(draw, rx + 12, CANVAS_H - 70, duration, chip_font,
                         bg_fill=second_rgb + (28,), text_fill=second_rgb, radius=6, pad_h=34)
        draw.rounded_rectangle([rx + 12, CANVAS_H - 70, rx2, CANVAS_H - 70 + 34],
                                radius=6, outline=second_rgb + (180,), width=2)

    neon_bar = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ImageDraw.Draw(neon_bar).rectangle([0, CANVAS_H - 7, CANVAS_W, CANVAS_H], fill=accent_rgb + (255,))
    neon_bar = neon_bar.filter(ImageFilter.GaussianBlur(3))
    canvas.alpha_composite(neon_bar)
    ImageDraw.Draw(canvas).rectangle([0, CANVAS_H - 5, CANVAS_W, CANVAS_H], fill=accent_rgb + (255,))
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE 6 — LAYERED DEPTH
# ─────────────────────────────────────────────────────────────────────────────
def _template_layered_depth(headshot_bytes, design, prompt_text):
    bg_color     = design.get("bg_color",     "#0d0d1a")
    accent_color = design.get("accent_color", "#f72585")
    title        = design.get("title",        "TUTORIAL").strip().upper()
    subtitle     = design.get("subtitle",     "BEGINNER TO ADVANCED").strip().upper()

    bg_rgb     = _hex_to_rgb(bg_color)
    accent_rgb = _hex_to_rgb(accent_color)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), bg_rgb + (255,))

    # Radial spotlight
    spot = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(spot)
    sdraw.ellipse([400, -400, CANVAS_W + 600, 800], fill=_blend(accent_rgb, (60, 20, 80), 0.5) + (80,))
    spot = spot.filter(ImageFilter.GaussianBlur(130))
    canvas.alpha_composite(spot)

    # Subtle texture
    tex = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    for _ in range(1400):
        rx, ry = random.randint(0, CANVAS_W-1), random.randint(0, CANVAS_H-1)
        tex.putpixel((rx, ry), (255, 255, 255, random.randint(8, 22)))
    canvas.alpha_composite(tex)

    # Stacked cards
    CARD_R = 24
    card_base = _blend(bg_rgb, (255, 255, 255), 0.05)
    card_mid  = _blend(bg_rgb, (255, 255, 255), 0.10)
    card_top  = _blend(bg_rgb, (255, 255, 255), 0.17)

    cards = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(cards)
    cdraw.rounded_rectangle([100, 110, 720, 636], radius=CARD_R, fill=card_base + (255,))
    cdraw.rounded_rectangle([ 70,  88, 710, 622], radius=CARD_R, fill=card_mid  + (255,))
    cdraw.rounded_rectangle([ 40,  66, 700, 608], radius=CARD_R, fill=card_top  + (255,))
    cdraw.rounded_rectangle([ 38,  64, 702, 610], radius=CARD_R, outline=accent_rgb + (200,), width=2)
    canvas.alpha_composite(cards)

    draw = ImageDraw.Draw(canvas)

    MARGIN = 72
    lines, size, line_h = _fit_text_lines(draw, title, 580, 360, 140, 50, stroke_w=3)
    font = _load_font(size, bold=True)
    y = 106
    for line in lines:
        _draw_text_with_shadow(draw, (MARGIN, y), line, font,
                               fill=(255, 255, 255), shadow_offset=(4, 5),
                               shadow_opacity=160, stroke_width=3, stroke_fill=(0, 0, 0, 210))
        y += line_h

    sub_font = _load_font(32, bold=True)
    sw = draw.textbbox((0, 0), subtitle, font=sub_font)[2]
    pill_w = min(570, sw + 44)
    draw.rounded_rectangle([MARGIN, y + 20, MARGIN + pill_w, y + 62],
                            radius=10, fill=accent_rgb + (255,))
    draw.text((MARGIN + 16, y + 26), subtitle, font=sub_font, fill=_contrast_color(accent_rgb))

    chip_font = _load_font(22, bold=True)
    topic    = _topic_tag(prompt_text)
    duration = _duration_tag(prompt_text)
    cx = MARGIN
    cy = CANVAS_H - 120
    rx = _draw_chip(draw, cx, cy, topic, chip_font,
                    bg_fill=(255, 220, 0, 255), text_fill=(10, 10, 10), radius=6, pad_h=34)
    if duration:
        _draw_chip(draw, rx + 14, cy, duration, chip_font,
                   bg_fill=(220, 220, 255, 200), text_fill=(10, 10, 30), radius=6, pad_h=34)

    if headshot_bytes:
        _paste_person(canvas, headshot_bytes, CANVAS_W - 610, CANVAS_H - 710, 710, accent_rgb, flip=True)

    draw.rectangle([0, CANVAS_H - 7, CANVAS_W, CANVAS_H], fill=accent_rgb + (255,))
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# ILLUSTRATION WATERMARK
# ─────────────────────────────────────────────────────────────────────────────

def _paste_illustration(canvas: Image.Image, illustration_bytes: bytes,
                        layout: str, accent_rgb: tuple,
                        opacity: int = 55) -> Image.Image:
    """Render a topic icon as a large, semi-transparent watermark on the text side."""
    try:
        icon = Image.open(io.BytesIO(illustration_bytes)).convert("RGBA")

        # Size: ~55% of canvas height
        target_size = int(CANVAS_H * 0.55)
        scale = target_size / max(icon.width, icon.height, 1)
        icon = icon.resize((int(icon.width * scale), int(icon.height * scale)), Image.LANCZOS)

        # Position on the text side, vertically centered
        if layout == "headshot_left":
            # Text is on the right → place icon towards right-center
            x = CANVAS_W - icon.width - 120
        else:
            # Text is on the left → place icon towards left-center
            x = 80
        y = (CANVAS_H - icon.height) // 2

        # Build a tinted, translucent layer
        watermark = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

        # Use original alpha channel but clamp max opacity
        alpha = icon.split()[-1]
        alpha = alpha.point(lambda p: min(p, opacity))
        icon.putalpha(alpha)

        watermark.paste(icon, (x, y), icon)
        canvas.alpha_composite(watermark)
    except Exception as e:
        print(f"[compositor] illustration paste failed: {e}")
    return canvas


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATES = [
    _template_power_split,      # 0
    _template_cinematic_dark,   # 1
    _template_bold_impact,      # 2
    _template_editorial,        # 3
    _template_neon_cyber,       # 4
    _template_layered_depth,    # 5
]


def compose_thumbnail(
    headshot_bytes: bytes,
    bg_image_bytes: bytes | None,
    design: dict,
    prompt_text: str = "",
    headshot_is_cutout: bool = False,
    illustration_bytes: bytes | None = None,
    template_index: int | None = None,
) -> bytes:
    if template_index is not None and 0 <= template_index < len(TEMPLATES):
        renderer = TEMPLATES[template_index]
    else:
        renderer = random.choice(TEMPLATES)

    canvas = renderer(headshot_bytes, design, prompt_text)

    # Overlay topic illustration as a subtle watermark
    if illustration_bytes:
        layout = design.get("layout", "headshot_right")
        accent_rgb = _hex_to_rgb(design.get("accent_color", "#ffffff"))
        canvas = _paste_illustration(canvas, illustration_bytes, layout, accent_rgb)

    # Blend background photo UNDER template at low opacity (texture only)
    if bg_image_bytes:
        try:
            bg = Image.open(io.BytesIO(bg_image_bytes)).convert("RGBA")
            bg = bg.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)

            bg_rgb_img = bg.convert("RGB")
            bg_rgb_img = ImageEnhance.Color(bg_rgb_img).enhance(0.3)
            bg_rgb_img = ImageEnhance.Brightness(bg_rgb_img).enhance(0.35)
            bg = bg_rgb_img.convert("RGBA")

            canvas_rgba = canvas.convert("RGBA")
            r, g, b, a = canvas_rgba.split()
            a = a.point(lambda p: int(p * 0.92))
            canvas_rgba = Image.merge("RGBA", (r, g, b, a))

            final = Image.alpha_composite(bg, canvas_rgba)
            canvas = final.convert("RGB")
        except Exception as e:
            print(f"[compositor] bg photo blend failed: {e}")
            canvas = canvas.convert("RGB")
    else:
        canvas = canvas.convert("RGB")

    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=93, optimize=True)
    out.seek(0)
    return out.read()


def get_template_count() -> int:
    return len(TEMPLATES)