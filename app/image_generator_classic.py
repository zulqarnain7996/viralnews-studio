"""
Classic 8-Theme Broadcast News Card Generator
Themes: breaking_red, pakistan_green, viral_dark, royal_blue,
        buzz_yellow, editorial_purple, quote_card, urdu_khabarnama
"""
import os
import io
import re
import html
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "fonts")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated_cards")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Helpers ─────────────────────────────────────────────────────────────────

def _is_urdu(text):
    return bool(re.search(r'[\u0600-\u06FF]', text or ""))

def _shape(text):
    if not _is_urdu(text):
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text

def _font(name="arialbd.ttf", size=48, urdu=False):
    if urdu:
        for p in [
            os.path.join(FONTS_DIR, "NotoSansArabic-Bold.ttf"),
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]:
            if os.path.exists(p):
                try: return ImageFont.truetype(p, size)
                except: pass
    for p in [
        os.path.join(r"C:\Windows\Fonts", name),
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def _fetch_img(url, timeout=5):
    if not url or not str(url).startswith("http"):
        return None
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        pass
    return None

def _shadow(draw, xy, text, font, fill=(255,255,255), shadow=(0,0,0), offset=3):
    x, y = xy
    draw.text((x+offset, y+offset), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)

def _wrap(text, width=26):
    return textwrap.wrap(text or "", width=width) or [""]

def _resolve_dims(aspect):
    dims = {
        "1:1":  (1080, 1080),
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "4:5":  (1080, 1350),
    }
    return dims.get(aspect, (1080, 1080))

def _gradient_rect(img, x0, y0, x1, y1, top_color, bot_color):
    """Draw a vertical gradient rectangle onto img."""
    w = x1 - x0
    h = y1 - y0
    grad = Image.new("RGBA", (w, h), top_color)
    d = ImageDraw.Draw(grad)
    tr, tg, tb, ta = top_color if len(top_color)==4 else (*top_color, 255)
    br, bg2, bb, ba = bot_color if len(bot_color)==4 else (*bot_color, 255)
    for row in range(h):
        t = row / max(h-1, 1)
        r = int(tr + (br-tr)*t)
        g = int(tg + (bg2-tg)*t)
        b = int(tb + (bb-tb)*t)
        a = int(ta + (ba-ta)*t)
        d.line([(0, row), (w, row)], fill=(r, g, b, a))
    img.paste(grad, (x0, y0), mask=grad)

# ── Theme Configs ────────────────────────────────────────────────────────────

THEMES = {
    "breaking_red": {
        "bar_color":    (200, 0, 20),
        "accent":       (255, 220, 0),
        "bg_overlay":   (0, 0, 0, 200),
        "tag_text":     "BREAKING NEWS",
        "tag_bg":       (220, 10, 30),
    },
    "pakistan_green": {
        "bar_color":    (0, 100, 30),
        "accent":       (255, 255, 255),
        "bg_overlay":   (0, 30, 0, 200),
        "tag_text":     "PAKISTAN",
        "tag_bg":       (0, 120, 40),
    },
    "viral_dark": {
        "bar_color":    (20, 20, 30),
        "accent":       (0, 230, 255),
        "bg_overlay":   (5, 5, 10, 220),
        "tag_text":     "TRENDING",
        "tag_bg":       (0, 50, 80),
    },
    "royal_blue": {
        "bar_color":    (10, 50, 150),
        "accent":       (255, 200, 0),
        "bg_overlay":   (5, 20, 60, 210),
        "tag_text":     "WORLD NEWS",
        "tag_bg":       (15, 70, 180),
    },
    "buzz_yellow": {
        "bar_color":    (220, 180, 0),
        "accent":       (0, 0, 0),
        "bg_overlay":   (30, 25, 0, 210),
        "tag_text":     "BUZZ",
        "tag_bg":       (200, 160, 0),
    },
    "editorial_purple": {
        "bar_color":    (80, 0, 120),
        "accent":       (255, 180, 255),
        "bg_overlay":   (20, 0, 35, 215),
        "tag_text":     "EDITORIAL",
        "tag_bg":       (100, 10, 150),
    },
    "quote_card": {
        "bar_color":    (30, 30, 40),
        "accent":       (255, 180, 0),
        "bg_overlay":   (0, 0, 0, 230),
        "tag_text":     "QUOTE",
        "tag_bg":       (50, 50, 70),
    },
    "urdu_khabarnama": {
        "bar_color":    (150, 0, 10),
        "accent":       (255, 220, 0),
        "bg_overlay":   (40, 0, 0, 210),
        "tag_text":     "خبرنامہ",
        "tag_bg":       (180, 0, 20),
    },
}

# ── Main Entry ───────────────────────────────────────────────────────────────

def generate_classic_card(article: dict, options: dict) -> dict:
    """Generate a classic broadcast-style news card. Returns dict with filename, web_url etc."""
    theme_key = options.get("theme", "breaking_red")
    if theme_key not in THEMES:
        theme_key = "breaking_red"
    cfg = THEMES[theme_key]

    aspect = options.get("aspect_ratio", "1:1")
    width, height = _resolve_dims(aspect)

    title    = html.unescape(article.get("title", "Latest News") or "Latest News")
    summary  = html.unescape(article.get("summary", "") or "")
    source   = article.get("source", "NEWS") or "NEWS"
    img_url  = options.get("custom_image_url") or article.get("image_url", "")
    page_name   = options.get("page_name", "PAK NEWS 24/7")
    page_handle = options.get("page_handle", "@PakNewsOfficial")
    category    = options.get("category_tag") or article.get("category", cfg["tag_text"])
    is_urdu     = _is_urdu(title)

    bar_color  = cfg["bar_color"]
    accent     = cfg["accent"]
    tag_bg     = cfg["tag_bg"]

    # ── Canvas ──────────────────────────────────────────────────────────────
    card = Image.new("RGBA", (width, height), (10, 10, 15, 255))

    # Background photo
    bg = _fetch_img(img_url)
    if bg:
        bg_fit = ImageOps.fit(bg.convert("RGBA"), (width, height), centering=(0.5, 0.3))
        # Darken & blur bottom half for readability
        blurred = bg_fit.filter(ImageFilter.GaussianBlur(radius=2))
        card.paste(blurred, (0, 0))

    # Heavy gradient overlay — dark at top and very dark at bottom
    _gradient_rect(card, 0, 0, width, height,
                   (0, 0, 0, 80), (0, 0, 0, 240))

    draw = ImageDraw.Draw(card)

    # ── Top Header Bar ───────────────────────────────────────────────────────
    header_h = max(80, int(height * 0.07))
    draw.rectangle([(0, 0), (width, header_h)], fill=bar_color)
    # Accent underline
    draw.rectangle([(0, header_h), (width, header_h + 5)], fill=accent)

    # Page name / branding
    font_brand = _font("arialbd.ttf", int(header_h * 0.42), urdu=_is_urdu(page_name))
    draw.text((22, int(header_h * 0.22)), _shape(page_name), font=font_brand, fill=(255, 255, 255))

    # LIVE badge (top right)
    live_w, live_h = 90, 40
    lx = width - live_w - 20
    ly = (header_h - live_h) // 2
    draw.rectangle([(lx, ly), (lx + live_w, ly + live_h)], fill=(220, 0, 0), outline=(255,255,255), width=2)
    font_live = _font("arialbd.ttf", 22)
    draw.text((lx + 18, ly + 9), "LIVE", font=font_live, fill=(255, 255, 255))

    # Date/time top-right below LIVE
    font_date = _font("arial.ttf", 20)
    date_str = datetime.now().strftime("%d %b %Y  %H:%M")
    draw.text((width - 230, header_h + 10), date_str, font=font_date, fill=(200, 200, 200))

    # ── Breaking Tag ─────────────────────────────────────────────────────────
    tag_y = header_h + 30
    tag_font = _font("arialbd.ttf", 26, urdu=_is_urdu(str(category)))
    tag_text = _shape(str(category).upper())
    t_bbox = tag_font.getbbox(tag_text)
    tag_pad = 20
    tag_w = (t_bbox[2] - t_bbox[0]) + tag_pad * 2
    draw.rectangle([(22, tag_y), (22 + tag_w, tag_y + 46)], fill=tag_bg, outline=accent, width=2)
    draw.text((22 + tag_pad, tag_y + 8), tag_text, font=tag_font, fill=(255, 255, 255))

    # Source badge
    src_x = 22 + tag_w + 16
    font_src = _font("arial.ttf", 20)
    draw.text((src_x, tag_y + 13), f"● {source.upper()}", font=font_src, fill=accent)

    # ── Headline Lower-Third ─────────────────────────────────────────────────
    box_margin = 20
    box_h_ratio = 0.33 if not summary else 0.40
    box_h = int(height * box_h_ratio)
    box_y = height - box_h - 60

    # Semi-transparent box
    box_img = Image.new("RGBA", (width - box_margin*2, box_h), (10, 10, 15, 220))
    card.paste(box_img, (box_margin, box_y), mask=box_img)
    draw = ImageDraw.Draw(card)

    # Accent left (or right for Urdu) bar
    if is_urdu:
        draw.rectangle([(width - box_margin - 8, box_y), (width - box_margin, box_y + box_h)], fill=accent)
    else:
        draw.rectangle([(box_margin, box_y), (box_margin + 8, box_y + box_h)], fill=accent)

    # Headline text
    headline_size = max(38, int(height * 0.048))
    font_headline = _font("arialbd.ttf", headline_size, urdu=is_urdu)
    wrap_w = 32 if is_urdu else 24
    lines = _wrap(title, wrap_w)[:3]

    cur_y = box_y + 18
    line_gap = headline_size + 14
    for line in lines:
        shaped = _shape(line)
        b = font_headline.getbbox(shaped)
        lw = b[2] - b[0]
        if is_urdu:
            lx = width - box_margin - 20 - lw
        else:
            lx = box_margin + 22
        # Shadow
        draw.text((lx + 2, cur_y + 2), shaped, font=font_headline, fill=(0, 0, 0))
        draw.text((lx, cur_y), shaped, font=font_headline, fill=(255, 255, 255))
        cur_y += line_gap

    # Summary (smaller, below headline)
    if summary and (cur_y + 36) < (box_y + box_h - 10):
        font_sum = _font("arial.ttf", max(26, int(height * 0.028)), urdu=is_urdu)
        sum_lines = _wrap(summary, 45 if is_urdu else 38)[:2]
        for sl in sum_lines:
            sh = _shape(sl)
            sb = font_sum.getbbox(sh)
            slw = sb[2] - sb[0]
            sx = width - box_margin - 20 - slw if is_urdu else box_margin + 22
            draw.text((sx, cur_y), sh, font=font_sum, fill=(210, 210, 210))
            cur_y += int(height * 0.033)

    # ── Footer Bottom Bar ────────────────────────────────────────────────────
    footer_y = height - 55
    draw.rectangle([(0, footer_y), (width, height)], fill=bar_color)
    font_footer = _font("arialbd.ttf", 22)
    draw.text((22, footer_y + 16), page_handle, font=font_footer, fill=accent)
    draw.text((width // 2 - 60, footer_y + 16), f"● {source.upper()}", font=font_footer, fill=(255, 255, 255))
    time_str = datetime.now().strftime("%H:%M PKT")
    draw.text((width - 180, footer_y + 16), time_str, font=font_footer, fill=(200, 200, 200))

    # ── Watermark ───────────────────────────────────────────────────────────
    font_wm = _font("arial.ttf", 18)
    wm = _shape(page_name)
    draw.text((width - 240, box_y - 28), wm, font=font_wm, fill=(180, 180, 180))

    # ── Save ─────────────────────────────────────────────────────────────────
    art_id = article.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"news_card_{art_id}_{theme_key}_{aspect.replace(':', 'x')}_{ts}.png"
    file_path = os.path.join(OUTPUT_DIR, filename)
    card.convert("RGB").save(file_path, "PNG")

    return {
        "filename": filename,
        "file_path": file_path,
        "web_url": f"/static/generated/{filename}",
        "width": width,
        "height": height,
    }
