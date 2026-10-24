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
    Generate a short 9:16 animated news MP4.

    Returns dict:
        filename, file_path, web_url, duration, width, height
    """
    if options is None:
        options = {}

    width, height = 1080, 1920  # 9:16 vertical (TikTok / Reels)

    title       = article.get("title", "Breaking News") or "Breaking News"
    summary     = article.get("summary", "") or ""
    source      = article.get("source", "NEWS") or "NEWS"
    img_url     = options.get("custom_image_url") or article.get("image_url", "")
    page_name   = options.get("page_name", "PAK NEWS 24/7")
    page_handle = options.get("page_handle", "@PakNewsOfficial")
    is_urdu     = _is_urdu(title)
    tts_lang    = "ur" if is_urdu else "en"

    art_id    = article.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name  = f"short_{art_id}_{ts}.mp4"
    out_path  = os.path.join(OUTPUT_DIR, out_name)
    tmp_vid   = os.path.join(OUTPUT_DIR, f"_tmp_v_{art_id}.mp4")
    tmp_audio = os.path.join(OUTPUT_DIR, f"_tmp_a_{art_id}.mp3")

    # ── 1. TTS Voiceover ────────────────────────────────────────────────────
    duration   = 8.0
    has_audio  = False
    narr_text  = title if is_urdu else f"{title}. {summary}"[:400]

    if _HAS_GTTS:
        try:
            tts = gTTS(text=narr_text, lang=tts_lang, slow=False)
            tts.save(tmp_audio)
            has_audio = True
            duration  = _audio_duration(tmp_audio)
            duration  = max(6.0, min(20.0, duration))
        except Exception as e:
            print(f"[VideoGen] TTS warning: {e}")

    fps          = 25
    total_frames = int(duration * fps)

    # ── 2. Prepare Assets ────────────────────────────────────────────────────
    base_img = _fetch(img_url)
    if not base_img:
        base_img = Image.new("RGB", (width, height), (15, 18, 25))

    banner_color = (200, 20, 40)
    accent_color = (255, 220, 0)
    header_h     = 90

    tag_text = "بریکنگ نیوز" if is_urdu else "⚡ BREAKING NEWS"

    font_brand    = _font(34, urdu=_is_urdu(page_name))
    font_headline = _font(44, urdu=is_urdu)
    font_tag      = _font(26, urdu=is_urdu)
    font_meta     = _font(22)
    font_footer   = _font(24)

    headline_lines = [_shape(l) for l in _wrap(title, 34 if is_urdu else 24)][:4]
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

        # Ken Burns zoom: 1.00 → 1.12
        zoom = 1.0 + t * 0.12
        zw, zh = int(width * zoom), int(height * zoom)
        bg_r = base_img.resize((zw, zh), Image.Resampling.BILINEAR)
        cx   = (zw - width) // 2
        cy   = (zh - height) // 2
        bg_c = bg_r.crop((cx, cy, cx + width, cy + height)).convert("RGBA")
        frame.paste(bg_c, (0, 0))

        # Gradient overlay
        ov = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        # Top dark strip
        for row in range(130):
            a = int(210 * (1 - row / 130))
            od.line([(0, row), (width, row)], fill=(0, 0, 0, a))
        # Bottom heavy gradient
        b0 = int(height * 0.40)
        for row in range(b0, height):
            pct = (row - b0) / (height - b0)
            a   = int(255 * min(1.0, pct ** 1.2))
            od.line([(0, row), (width, row)], fill=(8, 10, 16, a))
        frame = Image.alpha_composite(frame, ov)
        d = ImageDraw.Draw(frame)

        # ── Header bar ──────────────────────────────────────────────────────
        d.rectangle([(0, 0), (width, header_h)], fill=banner_color)
        d.rectangle([(0, header_h), (width, header_h + 6)], fill=accent_color)
        d.text((26, 22), shaped_page, font=font_brand, fill=(255, 255, 255))

        # Pulsing LIVE badge
        pulse = 0.55 + 0.45 * math.sin(f * 0.35)
        live_r = int(200 + 55 * pulse)
        d.rectangle([(width - 110, 18), (width - 18, 70)],
                    fill=(live_r, 0, 0), outline=(255, 255, 255), width=2)
        d.text((width - 95, 30), "LIVE", font=font_meta, fill=(255, 255, 255))

        # ── Tag badge ───────────────────────────────────────────────────────
        tag_y = header_h + 24
        tag_sh = _shape(tag_text)
        tb = font_tag.getbbox(tag_sh)
        tw = tb[2] - tb[0] + 40
        th = max(44, tb[3] - tb[1] + 16)
        d.rectangle([(22, tag_y), (22 + tw, tag_y + th)],
                    fill=(170, 0, 20), outline=accent_color, width=2)
        d.text((38, tag_y + 8), tag_sh, font=font_tag, fill=(255, 255, 255))

        # ── Lower-third animated card ────────────────────────────────────────
        box_h  = 350
        box_y0 = height - box_h - 90
        # Slide-up during first 20 frames
        slide  = max(0, int((20 - f) * 10)) if f < 20 else 0

        bov = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bd  = ImageDraw.Draw(bov)
        bd.rectangle(
            [(24, box_y0 + slide), (width - 24, box_y0 + box_h + slide)],
            fill=(12, 14, 20, 240), outline=accent_color, width=3
        )
        frame = Image.alpha_composite(frame, bov)
        d = ImageDraw.Draw(frame)

        cur_y = box_y0 + 28 + slide
        step  = 70

        if is_urdu:
            # Accent right bar
            bar_x = width - 48
            d.rectangle([(bar_x, cur_y), (bar_x + 8, cur_y + len(headline_lines) * step)],
                        fill=accent_color)
            for line in headline_lines:
                lb  = font_headline.getbbox(line)
                lw2 = lb[2] - lb[0]
                lx  = bar_x - 24 - lw2
                # High-contrast shadow
                for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)]:
                    d.text((lx + ox, cur_y + oy), line, font=font_headline, fill=(0, 0, 0))
                d.text((lx, cur_y),          line, font=font_headline, fill=(255, 235, 50))
                cur_y += step
        else:
            # Accent left bar
            d.rectangle([(40, cur_y), (48, cur_y + len(headline_lines) * step)],
                        fill=accent_color)
            for line in headline_lines:
                for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)]:
                    d.text((64 + ox, cur_y + oy), line, font=font_headline, fill=(0, 0, 0))
                d.text((64, cur_y),          line, font=font_headline, fill=(255, 255, 255))
                cur_y += step

        # ── Footer bar ──────────────────────────────────────────────────────
        foot_y = height - 72
        d.rectangle([(0, foot_y), (width, height)], fill=banner_color)
        d.text((26, foot_y + 20), f"SOURCE: {source.upper()}", font=font_footer, fill=(255, 255, 255))
        handle_sh = _shape(page_handle)
        hb = font_footer.getbbox(handle_sh)
        hx = width - (hb[2] - hb[0]) - 26
        d.text((hx, foot_y + 20), handle_sh, font=font_footer, fill=accent_color)

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
