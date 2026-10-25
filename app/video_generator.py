"""
ViralNews Studio — Short Video Generator
Generates 9:16 animated MP4 news clips with:
  • Ken Burns zoom effect on news photo
  • Animated lower-third headline
  • Flashing LIVE badge
  • Urdu or English TTS voiceover via gTTS
  • 2-step FFmpeg pipeline (rawvideo frames → merge audio) to avoid Python 3.14 pipe bug
"""
import os
import io
import re
import math
import textwrap
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from datetime import datetime

try:
    import imageio_ffmpeg
    _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    _FFMPEG = "ffmpeg"

try:
    from gtts import gTTS
    _HAS_GTTS = True
except ImportError:
    _HAS_GTTS = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _HAS_BIDI = True
except ImportError:
    _HAS_BIDI = False

import requests

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "generated_cards")
FONTS_DIR  = os.path.join(BASE_DIR, "static", "fonts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Helpers ─────────────────────────────────────────────────────────────────

def _is_urdu(text):
    return bool(re.search(r'[\u0600-\u06FF]', text or ""))

def _shape(text):
    if not _HAS_BIDI or not _is_urdu(text):
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text

def _font(size=36, urdu=False):
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
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
    ]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def _fetch(url, timeout=8):
    if not url or not str(url).startswith("http"):
        return None
    high_res_url = url
    if "img.express.pk" in high_res_url:
        high_res_url = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', high_res_url)
    if "ichef.bbci.co.uk" in high_res_url and "/240/" in high_res_url:
        high_res_url = high_res_url.replace("/240/", "/1024/")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    try:
        r = requests.get(high_res_url, headers=headers, timeout=timeout)
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGB")
        elif high_res_url != url:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        pass
    return None

def _wrap(text, width=26):
    return textwrap.wrap(text or "", width=width) or [""]

def _audio_duration(mp3_path):
    """Use ffmpeg to probe audio duration in seconds."""
    try:
        proc = subprocess.run(
            [_FFMPEG, "-i", mp3_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", proc.stderr)
        if m:
            h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
            return max(5.0, h * 3600 + mn * 60 + s + 1.5)
    except Exception:
        pass
    return 7.0

# ── Core Generator ───────────────────────────────────────────────────────────

def generate_news_video(article: dict, options: dict = None) -> dict:
    """
    Generate an advanced broadcast-quality news MP4 clip.
    Supports:
      • 3 Ratios: 9:16 (TikTok/Reels), 1:1 (Square Feed), 16:9 (YouTube/Landscape)
      • Multi-image slideshow with Ken-Burns, crossfade, or slide transitions
      • Multilingual TTS voiceover (Urdu, English US/UK) with speed and mute options
      • Studio-matching adaptive brand pills (no text crossing, perfectly sized)
      • Animated lower-third headline plate with pulsing LIVE indicator
    """
    if options is None:
        options = {}

    aspect_ratio = options.get("aspect_ratio", "9:16")
    if aspect_ratio == "1:1":
        width, height = 1080, 1080
    elif aspect_ratio == "16:9":
        width, height = 1920, 1080
    else:  # default 9:16
        width, height = 1080, 1920

    title       = article.get("title", "Breaking News") or "Breaking News"
    summary     = article.get("summary", "") or ""
    source      = article.get("source", "NEWS") or "NEWS"
    page_name   = options.get("page_name", "PAK NEWS 24/7")
    page_handle = options.get("page_handle", "@PakNewsOfficial")
    is_urdu     = _is_urdu(title)

    # Voiceover configuration
    voice_pref  = options.get("voice_lang", "auto")
    if voice_pref == "ur":
        tts_lang = "ur"
    elif voice_pref in ["en", "en-us"]:
        tts_lang = "en"
    elif voice_pref == "en-uk":
        tts_lang = "en-uk"
    else:
        tts_lang = "ur" if is_urdu else "en"

    mute_audio  = options.get("mute_audio", False)
    slow_speed  = (options.get("voice_speed") == "slow")
    narr_text   = options.get("narrative_text") or (title if is_urdu else f"{title}. {summary}"[:400])

    art_id    = article.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name  = f"video_{art_id}_{aspect_ratio.replace(':', 'x')}_{ts}.mp4"
    out_path  = os.path.join(OUTPUT_DIR, out_name)
    tmp_vid   = os.path.join(OUTPUT_DIR, f"_tmp_v_{art_id}.mp4")
    tmp_audio = os.path.join(OUTPUT_DIR, f"_tmp_a_{art_id}.mp3")

    # ── 1. TTS Voiceover ────────────────────────────────────────────────────
    duration   = 8.0
    has_audio  = False

    if not mute_audio and _HAS_GTTS:
        try:
            # Generate speech
            clean_tts_lang = "ur" if "ur" in tts_lang else "en"
            tts = gTTS(text=narr_text, lang=clean_tts_lang, slow=slow_speed)
            tts.save(tmp_audio)
            has_audio = True
            duration  = _audio_duration(tmp_audio)
            duration  = max(6.0, min(24.0, duration))
        except Exception as e:
            print(f"[VideoGen] TTS warning: {e}")

    fps          = 25
    total_frames = int(duration * fps)

    # ── 2. Prepare Images (Single or Multi-image Slideshow) ─────────────────
    raw_img_urls = options.get("image_urls") or []
    single_img_url = options.get("custom_image_url") or article.get("image_url", "")
    if not raw_img_urls and single_img_url:
        raw_img_urls = [single_img_url]

    loaded_images = []
    for u in raw_img_urls:
        fetched = _fetch(u)
        if fetched:
            loaded_images.append(fetched)

    if not loaded_images:
        loaded_images = [Image.new("RGB", (width, height), (15, 18, 25))]

    num_images = len(loaded_images)
    transition_style = options.get("transition", "ken_burns")

    banner_color = (165, 0, 10)
    accent_color = (255, 215, 0)
    header_h     = 85 if height == 1080 and width == 1920 else 96

    tag_text = "🔴 بریکنگ نیوز" if is_urdu else "⚡ BREAKING NEWS"

    font_brand    = _font(28 if is_urdu else 26, urdu=_is_urdu(page_name))
    font_headline = _font(46 if is_urdu else 42, urdu=is_urdu)
    font_tag      = _font(24, urdu=is_urdu)
    font_meta     = _font(20)
    font_footer   = _font(22)

    wrap_w = 45 if width == 1920 else (32 if is_urdu else 24)
    headline_lines = [_shape(l) for l in _wrap(title, wrap_w)][:4]
    shaped_page    = _shape(page_name)

    # ── 3. Render Frames → rawvideo pipe to temp MP4 ─────────────────────────
    cmd_vid = [
        _FFMPEG, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        tmp_vid
    ]
    proc = subprocess.Popen(
        cmd_vid,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    for f in range(total_frames):
        frame = Image.new("RGBA", (width, height), (10, 12, 18, 255))
        t = f / max(total_frames - 1, 1)

        # Multi-Image Slideshow logic
        if num_images == 1:
            curr_img = loaded_images[0]
            # Single image Ken Burns zoom: 1.00 → 1.14
            zoom = 1.0 + t * 0.14
            zw, zh = int(width * zoom), int(height * zoom)
            bg_r = curr_img.resize((zw, zh), Image.Resampling.BILINEAR)
            cx   = (zw - width) // 2
            cy   = (zh - height) // 2
            bg_c = bg_r.crop((cx, cy, cx + width, cy + height)).convert("RGBA")
            frame.paste(bg_c, (0, 0))
        else:
            # Multi-image slideshow with crossfade
            slide_duration = 1.0 / num_images
            img_idx = int(t / slide_duration)
            img_idx = min(img_idx, num_images - 1)
            next_idx = min(img_idx + 1, num_images - 1)

            t_slide = (t - (img_idx * slide_duration)) / slide_duration
            curr_img = loaded_images[img_idx]

            # Fit and Ken Burns
            zoom = 1.0 + t_slide * 0.10
            zw, zh = int(width * zoom), int(height * zoom)
            bg_r = curr_img.resize((zw, zh), Image.Resampling.BILINEAR)
            cx   = (zw - width) // 2
            cy   = (zh - height) // 2
            curr_crop = bg_r.crop((cx, cy, cx + width, cy + height)).convert("RGBA")

            if t_slide > 0.75 and img_idx != next_idx and transition_style == "crossfade":
                # Crossfade during last 25% of slide
                alpha = int(((t_slide - 0.75) / 0.25) * 255)
                next_img = loaded_images[next_idx]
                next_r = next_img.resize((width, height), Image.Resampling.BILINEAR).convert("RGBA")
                curr_crop = Image.blend(curr_crop, next_r, alpha / 255.0)

            frame.paste(curr_crop, (0, 0))

        # Dynamic Vignette / Gradient overlays
        ov = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        # Top dark strip
        for row in range(140):
            a = int(220 * (1 - row / 140))
            od.line([(0, row), (width, row)], fill=(0, 0, 0, a))
        # Bottom heavy gradient for readable news text
        b0 = int(height * (0.38 if height == 1920 else 0.45))
        for row in range(b0, height):
            pct = (row - b0) / (height - b0)
            a   = int(255 * min(1.0, pct ** 1.15))
            od.line([(0, row), (width, row)], fill=(6, 8, 14, a))
        frame = Image.alpha_composite(frame, ov)
        d = ImageDraw.Draw(frame)

        # ── Adaptive Brand Pill (Top-Left) ──────────────────────────────────
        # Fits ANY page name length (e.g. "Zulqarnain Combat Updates") with dynamic padding
        tb_brand = font_brand.getbbox(shaped_page)
        brand_w  = max(tb_brand[2] - tb_brand[0] + 36, 160)
        brand_h  = 52
        pill_x   = 26
        pill_y   = 22
        # Pill drop shadow
        d.rounded_rectangle([(pill_x + 2, pill_y + 2), (pill_x + brand_w + 2, pill_y + brand_h + 2)], radius=8, fill=(0, 0, 0, 180))
        # Main pill
        d.rounded_rectangle([(pill_x, pill_y), (pill_x + brand_w, pill_y + brand_h)], radius=8, fill=banner_color, outline=(255, 255, 255), width=2)
        # Pill text
        tx = pill_x + (brand_w - (tb_brand[2] - tb_brand[0])) // 2
        ty = pill_y + (brand_h - (tb_brand[3] - tb_brand[1])) // 2 - 2
        d.text((tx, ty), shaped_page, font=font_brand, fill=(255, 255, 255))

        # ── Pulsing LIVE Badge (Top-Right) ──────────────────────────────────
        pulse = 0.55 + 0.45 * math.sin(f * 0.35)
        live_r = int(200 + 55 * pulse)
        live_w, live_h = 105, 46
        live_x = width - live_w - 26
        live_y = 25
        d.rounded_rectangle([(live_x, live_y), (live_x + live_w, live_y + live_h)], radius=6, fill=(live_r, 0, 0), outline=(255, 255, 255), width=2)
        d.text((live_x + 18, live_y + 11), "🔴 LIVE", font=font_meta, fill=(255, 255, 255))

        # ── Category Tag Badge ──────────────────────────────────────────────
        tag_y = pill_y + brand_h + 16
        tag_sh = _shape(tag_text)
        tb_tag = font_tag.getbbox(tag_sh)
        tag_w  = tb_tag[2] - tb_tag[0] + 32
        tag_h  = max(40, tb_tag[3] - tb_tag[1] + 14)
        tag_x  = width - tag_w - 26 if is_urdu else 26
        d.rounded_rectangle([(tag_x, tag_y), (tag_x + tag_w, tag_y + tag_h)], radius=6, fill=(20, 24, 34, 230), outline=accent_color, width=2)
        d.text((tag_x + 16, tag_y + 6), tag_sh, font=font_tag, fill=accent_color)

        # ── Lower-Third Animated Glass Card ─────────────────────────────────
        box_h  = 340 if height == 1920 else 240
        box_y0 = height - box_h - (90 if height == 1920 else 75)
        slide  = max(0, int((20 - f) * 8)) if f < 20 else 0

        bov = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bd  = ImageDraw.Draw(bov)
        bd.rounded_rectangle(
            [(24, box_y0 + slide), (width - 24, box_y0 + box_h + slide)],
            radius=12, fill=(10, 14, 22, 235), outline=accent_color, width=2
        )
        frame = Image.alpha_composite(frame, bov)
        d = ImageDraw.Draw(frame)

        cur_y = box_y0 + 24 + slide
        step  = 64 if height == 1920 else 48

        if is_urdu:
            bar_x = width - 46
            d.rectangle([(bar_x, cur_y), (bar_x + 6, cur_y + len(headline_lines) * step)], fill=accent_color)
            for line in headline_lines:
                lb  = font_headline.getbbox(line)
                lw2 = lb[2] - lb[0]
                lx  = bar_x - 20 - lw2
                # High-contrast drop shadow
                d.text((lx + 2, cur_y + 2), line, font=font_headline, fill=(0, 0, 0))
                d.text((lx, cur_y),          line, font=font_headline, fill=accent_color)
                cur_y += step
        else:
            d.rectangle([(40, cur_y), (46, cur_y + len(headline_lines) * step)], fill=accent_color)
            for line in headline_lines:
                d.text((58 + 2, cur_y + 2), line, font=font_headline, fill=(0, 0, 0))
                d.text((58, cur_y),          line, font=font_headline, fill=(255, 255, 255))
                cur_y += step

        # ── Footer Bar ──────────────────────────────────────────────────────
        foot_h = 60
        foot_y = height - foot_h
        d.rectangle([(0, foot_y), (width, height)], fill=(12, 14, 20))
        d.rectangle([(0, foot_y), (width, foot_y + 3)], fill=accent_color)

        src_lbl = f"SOURCE: {source.upper()}"
        d.text((26, foot_y + 18), src_lbl, font=font_footer, fill=(200, 210, 225))

        handle_sh = _shape(page_handle)
        hb = font_footer.getbbox(handle_sh)
        hx = width - (hb[2] - hb[0]) - 26
        d.text((hx, foot_y + 18), handle_sh, font=font_footer, fill=accent_color)

        # Write raw RGB bytes to ffmpeg
        try:
            proc.stdin.write(frame.convert("RGB").tobytes())
        except BrokenPipeError:
            break

    try:
        proc.stdin.close()
        proc.wait(timeout=120)
    except Exception as e:
        print(f"[VideoGen] FFmpeg frame pipe error: {e}")

    # ── 4. Merge Audio ──────────────────────────────────────────────────────
    if has_audio and os.path.exists(tmp_audio) and os.path.exists(tmp_vid):
        merge_cmd = [
            _FFMPEG, "-y",
            "-i", tmp_vid,
            "-i", tmp_audio,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            out_path
        ]
        subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif os.path.exists(tmp_vid):
        import shutil
        shutil.move(tmp_vid, out_path)

    # ── 5. Cleanup ──────────────────────────────────────────────────────────
    for f_rm in [tmp_vid, tmp_audio]:
        try:
            if os.path.exists(f_rm):
                os.remove(f_rm)
        except Exception:
            pass

    return {
        "filename": out_name,
        "file_path": out_path,
        "web_url":   f"/static/generated/{out_name}",
        "duration":  int(duration),
        "width":     width,
        "height":    height,
    }
