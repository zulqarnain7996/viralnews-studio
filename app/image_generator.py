import os
import io
import re
import html
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated_cards")
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "fonts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_urdu_str(text):
    if not text:
        return False
    return bool(re.search(r'[\u0600-\u06FF]', text))

def shape_urdu(text):
    if not is_urdu_str(text):
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

def get_font(font_name="impact.ttf", size=48, is_urdu=False):
    """
    Robust multi-platform font loader.
    Prioritizes bundled NotoSansArabic & NotoNastaliqUrdu (which are bundled in the repo),
    ensuring identical typography across Windows and Linux / Render.
    """
    if is_urdu:
        urdu_paths = [
            os.path.join(FONTS_DIR, "NotoSansArabic-Bold.ttf"),
            os.path.join(FONTS_DIR, "NotoNastaliqUrdu-Bold.ttf"),
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\arial.ttf"
        ]
        for p in urdu_paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue

    font_paths = [
        os.path.join(FONTS_DIR, "NotoSansArabic-Bold.ttf"),  # Guaranteed Latin+Urdu glyphs
        os.path.join(r"C:\Windows\Fonts", font_name),
        os.path.join(r"C:\Windows\Fonts", "arialbd.ttf"),
        os.path.join(r"C:\Windows\Fonts", "arial.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def fetch_image_from_url(url, timeout=8):
    if not url or not url.startswith("http"):
        return None
    high_res_url = url
    if "img.express.pk" in high_res_url:
        high_res_url = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', high_res_url)
    if "ichef.bbci.co.uk" in high_res_url and "/240/" in high_res_url:
        high_res_url = high_res_url.replace("/240/", "/1024/")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }
        resp = requests.get(high_res_url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return Image.open(io.BytesIO(resp.content)).convert("RGBA")
        elif high_res_url != url:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        print(f"Error fetching image {url}: {e}")
    return None

def draw_text_with_shadow(draw, position, text, font, fill=(255, 255, 255), shadow_fill=(0, 0, 0), offset=3):
    x, y = position
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill)

def render_circular_avatar(img, size=160, border_color=(255, 255, 255), border_width=4):
    """Crops an image into a smooth circular portrait with border."""
    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)
    
    avatar = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(avatar, (0, 0), mask=mask)
    
    # Draw border
    border_draw = ImageDraw.Draw(output)
    border_draw.ellipse((1, 1, size - 2, size - 2), outline=border_color, width=border_width)
    return output

def generate_news_card(article, options=None):
    """
    Renders a Facebook/TikTok ready news card graphic.
    Supports Turkiye Urdu (Split Red/Yellow), DW Urdu Quote Card, and 8 classic themes.
    """
    options = options or {}
    aspect_ratio = options.get("aspect_ratio", "1:1")
    theme_key = options.get("theme", "turkiye_urdu_split")
    
    page_name = options.get("page_name", "PAK NEWS 24/7").upper()
    page_handle = options.get("page_handle", "@PakNewsOfficial")
    website_url = options.get("website_url", "www.paknews24.com")
    speaker_name = options.get("speaker_name", "بیرسٹر گوہر خان")
    speaker_title = options.get("speaker_title", "چیئرمین، پاکستان تحریک انصاف")
    
    title = html.unescape(article.get("title", "")).strip().replace('\xa0', ' ')
    summary = html.unescape(article.get("summary", "")).strip().replace('\xa0', ' ')
    is_urdu = is_urdu_str(title)

    if aspect_ratio == "9:16":
        width, height = 1080, 1920
    else:
        width, height = 1080, 1080

    card = Image.new("RGBA", (width, height), (15, 17, 23, 255))
    img_url = options.get("custom_image_url") or article.get("image_url")
    bg_img = fetch_image_from_url(img_url)

    # ========================================================
    # TEMPLATE 1: BROADCAST SPLIT & PRO STYLES (Studio Quality)
    # ========================================================
    if theme_key in [
        "turkiye_urdu_split", "combat_steel_war", "breaking_red", "turkiye_emerald_split", 
        "turkiye_dark_split", "neon_cyber_split", "royal_gold_split", "vox_spotlight_dark", 
        "ticker_live_tv", "cinematic_letterbox", "pakistan_green", "viral_dark"
    ]:
        split_y = int(height * 0.52)
        
        # 1. Top Half: Photo with Logo Box or Studio Backdrop
        if bg_img:
            photo_h = split_y
            photo_cropped = ImageOps.fit(bg_img, (width, photo_h), centering=(0.5, 0.5))
            card.paste(photo_cropped, (0, 0))
        else:
            # Energetic broadcast studio backdrop with vignette and grid lines
            grad = Image.new("RGBA", (width, split_y), (25, 30, 44, 255))
            d_grad = ImageDraw.Draw(grad)
            for i in range(split_y):
                t = i / split_y
                r = int(20 + 20 * t)
                g = int(24 + 16 * t)
                b = int(36 + 26 * t)
                d_grad.line([(0, i), (width, i)], fill=(r, g, b, 255))
            # Subtle broadcast studio grid
            for gx in range(0, width, 70):
                d_grad.line([(gx, 0), (gx, split_y)], fill=(255, 255, 255, 14))
            for gy in range(0, split_y, 70):
                d_grad.line([(0, gy), (width, gy)], fill=(255, 255, 255, 14))
            card.paste(grad, (0, 0))

        # Top-left Logo Box - Adaptive Pill
        draw = ImageDraw.Draw(card)
        font_logo = get_font(size=24, is_urdu=is_urdu_str(page_name))
        display_page_name = shape_urdu(page_name)
        text_bbox = font_logo.getbbox(display_page_name)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        logo_box_w = max(text_w + 48, 180)
        logo_box_h = 56
        if theme_key in ["combat_steel_war"]:
            logo_bg = (25, 33, 46)
        elif theme_key in ["neon_cyber_split"]:
            logo_bg = (0, 240, 255)
        elif theme_key in ["royal_gold_split"]:
            logo_bg = (255, 215, 0)
        elif theme_key in ["vox_spotlight_dark"]:
            logo_bg = (204, 255, 0)
        elif theme_key in ["ticker_live_tv", "breaking_red"]:
            logo_bg = (210, 0, 20)
        elif theme_key in ["turkiye_emerald_split", "pakistan_green"]:
            logo_bg = (0, 120, 50)
        else:
            logo_bg = (165, 0, 10)
        
        draw.rounded_rectangle([(25, 25), (25 + logo_box_w, 25 + logo_box_h)], radius=10, fill=logo_bg, outline=(255, 255, 255), width=2)
        logo_text_color = (0, 0, 0) if theme_key in ["neon_cyber_split", "royal_gold_split", "vox_spotlight_dark"] else (255, 255, 255)
        text_x = 25 + (logo_box_w - text_w) // 2
        text_y = 25 + (logo_box_h - text_h) // 2 - 2
        draw.text((text_x, text_y), display_page_name, font=font_logo, fill=logo_text_color)

        # Top-right Alert Strap / Category Pill
        category_name = article.get("category", "breaking").lower()
        if theme_key == "combat_steel_war" or category_name in ["war", "iran_us", "russia_ukraine", "china_india"]:
            strap_text = "⚔️ عسکری اپڈیٹ | DEFENSE ALERT" if is_urdu else "⚔️ DEFENSE UPDATE"
            strap_bg = (200, 25, 35)
        elif category_name == "tech" or theme_key == "neon_cyber_split":
            strap_text = "⚡ ٹیکنالوجی اپڈیٹ | TECH DESK" if is_urdu else "⚡ TECH & AI UPDATE"
            strap_bg = (0, 160, 210)
        elif category_name == "pakistan":
            strap_text = "🇵🇰 پاکستان | PAKISTAN" if is_urdu else "🇵🇰 PAKISTAN ALERT"
            strap_bg = (0, 125, 50)
        elif category_name == "world":
            strap_text = "🌍 عالمی خبریں | WORLD NEWS" if is_urdu else "🌍 WORLD BREAKING"
            strap_bg = (10, 60, 160)
        else:
            strap_text = "🚨 بریکنگ نیوز | BREAKING NEWS" if is_urdu else "🚨 BREAKING NEWS"
            strap_bg = (215, 0, 20)

        font_strap = get_font(size=20, is_urdu=is_urdu_str(strap_text))
        disp_strap = shape_urdu(strap_text)
        s_bbox = font_strap.getbbox(disp_strap)
        sw = s_bbox[2] - s_bbox[0]
        strap_w = sw + 36
        strap_x = width - strap_w - 25
        draw.rounded_rectangle([(strap_x, 25), (strap_x + strap_w, 25 + 56)], radius=10, fill=strap_bg, outline=(255, 255, 255), width=2)
        draw.text((strap_x + 18, 25 + (56 - (s_bbox[3] - s_bbox[1])) // 2 - 2), disp_strap, font=font_strap, fill=(255, 255, 255))

        # 2. Bottom Half: Theme Background
        if theme_key == "combat_steel_war":
            bottom_color_top = (15, 20, 28)
            bottom_color_bot = (8, 12, 18)
        elif theme_key == "breaking_red":
            bottom_color_top = (185, 0, 15)
            bottom_color_bot = (105, 0, 8)
        elif theme_key in ["turkiye_emerald_split", "pakistan_green"]:
            bottom_color_top = (1, 75, 32)
            bottom_color_bot = (0, 45, 18)
        elif theme_key == "neon_cyber_split":
            bottom_color_top = (9, 13, 22)
            bottom_color_bot = (4, 7, 12)
        elif theme_key == "royal_gold_split":
            bottom_color_top = (54, 0, 8)
            bottom_color_bot = (31, 0, 4)
        elif theme_key == "vox_spotlight_dark":
            bottom_color_top = (13, 15, 20)
            bottom_color_bot = (8, 9, 12)
        elif theme_key == "ticker_live_tv":
            bottom_color_top = (11, 18, 32)
            bottom_color_bot = (6, 10, 18)
        elif theme_key == "cinematic_letterbox":
            bottom_color_top = (10, 10, 10)
            bottom_color_bot = (0, 0, 0)
        elif theme_key == "turkiye_dark_split":
            bottom_color_top = (22, 25, 35)
            bottom_color_bot = (10, 12, 16)
        else:
            bottom_color_top = (165, 0, 10)  # Rich broadcast crimson
            bottom_color_bot = (110, 0, 5)

        # Draw smooth vertical gradient in bottom half
        bot_h = height - split_y
        bottom_layer = Image.new("RGBA", (width, bot_h), bottom_color_top)
        d_bot = ImageDraw.Draw(bottom_layer)
        r1, g1, b1 = bottom_color_top
        r2, g2, b2 = bottom_color_bot
        for row in range(bot_h):
            t = row / max(bot_h - 1, 1)
            cr = int(r1 + (r2 - r1) * t)
            cg = int(g1 + (g2 - g1) * t)
            cb = int(b1 + (b2 - b1) * t)
            d_bot.line([(0, row), (width, row)], fill=(cr, cg, cb, 255))
        card.paste(bottom_layer, (0, split_y))
        draw = ImageDraw.Draw(card)

        # Combat steel or breaking accent divider line
        divider_color = (255, 215, 0) if theme_key in ["combat_steel_war", "royal_gold_split"] else ((0, 240, 255) if theme_key == "neon_cyber_split" else (255, 230, 0))
        draw.rectangle([(0, split_y), (width, split_y + 4)], fill=divider_color)

        # Subtle top shadow on split
        for i in range(12):
            draw.line([(0, split_y + 4 + i), (width, split_y + 4 + i)], fill=(0, 0, 0, int(160 * (1 - i / 12))))

        # 3. Headline Text & Summary Bullets
        if theme_key in ["royal_gold_split"]:
            headline_color = (255, 215, 0)
        elif theme_key in ["neon_cyber_split"]:
            headline_color = (0, 240, 255)
        elif theme_key in ["vox_spotlight_dark"]:
            headline_color = (255, 255, 255)
        elif theme_key == "combat_steel_war":
            headline_color = (255, 225, 0)
        elif theme_key != "turkiye_dark_split":
            headline_color = (255, 230, 0)
        else:
            headline_color = (0, 240, 255)

        headline_font_size = 52 if is_urdu else 48
        font_headline = get_font(size=headline_font_size, is_urdu=is_urdu)

        raw_wrapped = textwrap.wrap(title, width=32 if is_urdu else 26)[:3]
        wrapped_lines = [shape_urdu(line) for line in raw_wrapped]

        # Process Summary Highlights (if available)
        font_summary = get_font(size=26, is_urdu=is_urdu)
        sum_lines = []
        if summary:
            clean_sum = summary.replace(title, "").strip()
            # Remove redundant punctuation
            clean_sum = re.sub(r'^[،,؛;\s\-:]+', '', clean_sum).strip()
            if len(clean_sum) > 20:
                raw_sum_wrapped = textwrap.wrap(clean_sum, width=44 if is_urdu else 36)[:2]
                sum_lines = [shape_urdu(l) for l in raw_sum_wrapped]

        text_total_h = len(wrapped_lines) * (headline_font_size + 14) + (len(sum_lines) * 36 + 14 if sum_lines else 0)
        content_space = (height - split_y - 80)
        start_y = split_y + max(16, (content_space - text_total_h) // 2)

        for line in wrapped_lines:
            bbox = font_headline.getbbox(line)
            lw = bbox[2] - bbox[0]
            lx = (width - lw) // 2
            # Dark drop shadow
            draw.text((lx + 3, start_y + 3), line, font=font_headline, fill=(15, 0, 0))
            draw.text((lx, start_y), line, font=font_headline, fill=headline_color)
            start_y += headline_font_size + 14

        # Draw Summary Highlights
        if sum_lines:
            start_y += 10
            for s_line in sum_lines:
                s_bbox = font_summary.getbbox(s_line)
                sw = s_bbox[2] - s_bbox[0]
                sx = (width - sw) // 2
                draw.text((sx + 2, start_y + 2), s_line, font=font_summary, fill=(10, 0, 0))
                draw.text((sx, start_y), s_line, font=font_summary, fill=(245, 245, 250))
                start_y += 34

        # 4. Footer Bar
        footer_y = height - 65
        # Bottom-left: Website badge
        badge_w = 260
        draw.rectangle([(25, footer_y), (25 + badge_w, footer_y + 40)], fill=(255, 255, 255), outline=(200, 200, 200), width=1)
        font_site = get_font("arialbd.ttf", 18)
        draw.text((38, footer_y + 11), f"➤ {website_url}", font=font_site, fill=(180, 0, 20))

        # Bottom-right: Social Handle
        font_social = get_font("arialbd.ttf", 20)
        handle_text = f"𝕏 f 📷  {page_handle.upper()}"
        h_bbox = font_social.getbbox(handle_text)
        hw = h_bbox[2] - h_bbox[0]
        draw.text((width - hw - 30, footer_y + 10), handle_text, font=font_social, fill=(255, 255, 255))

    # ========================================================
    # TEMPLATE 2: DW URDU SKY BLUE QUOTE CARD (Screenshot 2)
    # ========================================================
    elif theme_key in ["dw_quote_blue", "dw_quote_dark", "dw_quote_red"]:
        # 1. Background
        if theme_key == "dw_quote_dark":
            bg_color = (18, 22, 30)
            text_color = (255, 255, 255)
            quote_color = (0, 229, 255)
        elif theme_key == "dw_quote_red":
            bg_color = (180, 10, 25)
            text_color = (255, 255, 255)
            quote_color = (255, 220, 0)
        else: # dw_quote_blue (Screenshot 2 default)
            bg_color = (0, 150, 230)      # Vivid DW Sky Blue
            text_color = (0, 35, 75)       # Deep Navy Blue
            quote_color = (0, 45, 95)

        card.paste(Image.new("RGBA", (width, height), bg_color), (0, 0))
        draw = ImageDraw.Draw(card)

        # 2. Top Rectangular News Photo (~44% of card)
        photo_h = int(height * 0.44)
        if bg_img:
            photo_cropped = ImageOps.fit(bg_img, (width - 40, photo_h), centering=(0.5, 0.5))
            card.paste(photo_cropped, (20, 20))
        else:
            grad = Image.new("RGBA", (width - 40, photo_h), (40, 50, 70, 255))
            card.paste(grad, (20, 20))

        # Top-left Channel Watermark on Photo
        draw = ImageDraw.Draw(card)
        font_wm = get_font("arialbd.ttf", 26)
        draw.rectangle([(35, 35), (95, 75)], fill=(0, 150, 230))
        draw.text((45, 42), "DW", font=font_wm, fill=(255, 255, 255))

        # 3. Overlapping Circular Portrait Avatar (Lower-Left of photo)
        avatar_size = 180
        avatar_x = 55
        avatar_y = 20 + photo_h - (avatar_size // 2)

        # Portrait: use news photo or dedicated portrait fallback
        portrait_src = bg_img or Image.new("RGB", (avatar_size, avatar_size), (80, 90, 110))
        avatar_circ = render_circular_avatar(portrait_src, size=avatar_size, border_color=(255, 255, 255), border_width=4)
        card.paste(avatar_circ, (avatar_x, avatar_y), mask=avatar_circ)
        draw = ImageDraw.Draw(card)

        # 4. Big Right-Hand Quotation Mark ”
        quote_mark_y = 20 + photo_h + 20
        font_qmark = get_font("georgia.ttf", 90)
        draw.text((width - 120, quote_mark_y), "”", font=font_qmark, fill=quote_color)

        # 5. Quote Text
        quote_start_y = quote_mark_y + 60
        font_quote = get_font(size=44, is_urdu=is_urdu)
        
        quote_body = summary if summary else title
        raw_quote_lines = textwrap.wrap(quote_body, width=38 if is_urdu else 30)[:4]
        wrapped_quote = [shape_urdu(line) for line in raw_quote_lines]

        cur_qy = quote_start_y
        for q_line in wrapped_quote:
            bbox = font_quote.getbbox(q_line)
            qw = bbox[2] - bbox[0]
            qx = width - 60 - qw if is_urdu else 60
            draw.text((qx, cur_qy), q_line, font=font_quote, fill=text_color)
            cur_qy += 54

        # 6. Speaker Attribution (Name & Title)
        cur_qy += 20
        font_spk_name = get_font(size=36, is_urdu=True)
        font_spk_title = get_font(size=26, is_urdu=True)
        
        shaped_name = shape_urdu(speaker_name)
        n_bbox = font_spk_name.getbbox(shaped_name)
        nw = n_bbox[2] - n_bbox[0]
        nx = width - 60 - nw if is_urdu else 60
        draw.text((nx, cur_qy), shaped_name, font=font_spk_name, fill=text_color)
        cur_qy += 44

        shaped_stitle = shape_urdu(speaker_title)
        t_bbox = font_spk_title.getbbox(shaped_stitle)
        tw = t_bbox[2] - t_bbox[0]
        tx = width - 60 - tw if is_urdu else 60
        draw.text((tx, cur_qy), shaped_stitle, font=font_spk_title, fill=text_color)

        # 7. Copyright Bottom-Left
        font_copy = get_font("arial.ttf", 16)
        source_name = article.get("source", "Picture Alliance")
        draw.text((30, height - 35), f"© {source_name} / {page_name}", font=font_copy, fill=(230, 240, 255))

    # ========================================================
    # TEMPLATE 3: CLASSIC BROADCAST THEMES (Fallback)
    # ========================================================
    else:
        # Default to previous high-impact broadcast style
        from app.image_generator_classic import generate_classic_card
        return generate_classic_card(article, options)

    # Save to disk
    art_id = article.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"news_card_{art_id}_{theme_key}_{aspect_ratio.replace(':', 'x')}_{timestamp}.png"
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    final_card = card.convert("RGB")
    final_card.save(file_path, "PNG", quality=95)
    
    return {
        "filename": filename,
        "file_path": file_path,
        "web_url": f"/static/generated/{filename}",
        "width": width,
        "height": height
    }
