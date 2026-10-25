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
import base64
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
            os.path.join(FONTS_DIR, "NotoNastaliqUrdu-Bold.ttf"),
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

def _decode_base64_image(data_str):
    """Decodes a base64 Data URL into a PIL RGBA Image."""
    if not data_str or not isinstance(data_str, str):
        return None
    try:
        if "," in data_str:
            data_str = data_str.split(",", 1)[1]
        decoded = base64.b64decode(data_str)
        return Image.open(io.BytesIO(decoded)).convert("RGBA")
    except Exception as e:
        print(f"[VideoGen] Error decoding base64 image: {e}")
        return None

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
            return max(5.0, h * 3600 + mn * 60 + s + 1.2)
    except Exception:
        pass
    return 7.0

def _generate_news_audio_bed(duration: float, out_mp3_path: str):
    """
    Synthesizes a broadcast newsroom ambient background music bed using FFmpeg.
    Creates a deep 65Hz/120Hz pulsing bass + high rhythm ticker pulse, giving that urgent TV newsroom feel.
    """
    try:
        cmd = [
            _FFMPEG, "-y",
            "-f", "lavfi", "-i", f"anoisesrc=d={duration + 1}:c=pink:r=44100:a=0.015",
            "-f", "lavfi", "-i", f"sine=f=120:d={duration + 1}",
            "-filter_complex",
            "[1:a]volume=0.20,lowpass=f=240,tremolo=f=4:d=0.75[bass];[0:a][bass]amix=inputs=2:duration=first[out]",
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            out_mp3_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        return os.path.exists(out_mp3_path)
    except Exception as e:
        print(f"[VideoGen] Audio bed synthesis warning: {e}")
        return False

# ── Core Generator ───────────────────────────────────────────────────────────

def generate_news_video(article: dict, options: dict = None) -> dict:
    """
    Generate an advanced broadcast-quality news MP4 clip.
    Features:
      • 3 Ratios: 9:16 (TikTok/Reels), 1:1 (Square Feed), 16:9 (YouTube/Landscape)
      • Dynamic multi-camera scene cuts changing every 2.5 seconds
      • 100% Studio-accurate text & graphics directly from the Studio Canvas
      • Multi-image slideshow support with smooth camera movements
      • Background newsroom music bed mixed with realistic voiceover
      • Adaptive brand pill ("Zulqarnain Combat Updates" fits perfectly)
    """
    if options is None:
        options = {}

    aspect_ratio = options.get("aspect_ratio", "9:16")
    if aspect_ratio == "1:1":
        width, height = 1080, 1080
        split_y = int(height * 0.52)
    elif aspect_ratio == "16:9":
        width, height = 1920, 1080
        split_y = int(height * 0.58)
    else:  # default 9:16
        width, height = 1080, 1920
        split_y = int(height * 0.52)

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

    art_id      = article.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name    = f"video_{art_id}_{aspect_ratio.replace(':', 'x')}_{ts}.mp4"
    out_path    = os.path.join(OUTPUT_DIR, out_name)
    tmp_vid     = os.path.join(OUTPUT_DIR, f"_tmp_v_{art_id}.mp4")
    tmp_audio   = os.path.join(OUTPUT_DIR, f"_tmp_a_{art_id}.mp3")
    tmp_bg_audio = os.path.join(OUTPUT_DIR, f"_tmp_bg_{art_id}.mp3")

    # ── 1. Voiceover (TTS) ──────────────────────────────────────────────────
    duration   = 8.0
    has_audio  = False

    if not mute_audio and _HAS_GTTS:
        try:
            clean_tts_lang = "ur" if "ur" in tts_lang else "en"
            tts = gTTS(text=narr_text, lang=clean_tts_lang, slow=slow_speed)
            tts.save(tmp_audio)
            has_audio = True
            duration  = _audio_duration(tmp_audio)
            duration  = max(6.0, min(30.0, duration))
        except Exception as e:
            print(f"[VideoGen] TTS warning: {e}")

    fps          = 25
    total_frames = int(duration * fps)

    # ── 2. Background Newsroom Audio Bed ────────────────────────────────────
    has_bg_audio = _generate_news_audio_bed(duration, tmp_bg_audio)

    # ── 3. Prepare Visual Assets (Studio Card & Photo Viewport) ─────────────
    card_data = options.get("card_image_data")
    master_card = _decode_base64_image(card_data)

    # If no canvas card provided, generate one from image_generator
    if not master_card:
        try:
            from app.image_generator import generate_news_card
            card_res = generate_news_card(article, {
                "theme": "turkiye_urdu_split",
                "aspect_ratio": "1:1" if aspect_ratio == "1:1" else ("16:9" if aspect_ratio == "16:9" else "9:16"),
                "page_name": page_name,
                "page_handle": page_handle,
                "custom_image_url": options.get("custom_image_url")
            })
            if card_res and os.path.exists(card_res.get("file_path", "")):
                master_card = Image.open(card_res["file_path"]).convert("RGBA")
        except Exception as e:
            print(f"[VideoGen] Fallback master card error: {e}")

    if master_card:
        master_card = master_card.resize((width, height), Image.Resampling.LANCZOS)

    # Extract lower-third graphic strap and header from master card
    lower_third_overlay = None
    header_overlay = None
    if master_card:
        lower_third_overlay = master_card.crop((0, split_y, width, height))
        header_overlay = master_card.crop((0, 0, width, int(split_y * 0.22)))

    # Load news photos for the dynamic video viewport
    raw_img_urls = options.get("image_urls") or []
    single_img_url = options.get("custom_image_url") or article.get("image_url", "")
    if not raw_img_urls and single_img_url:
        raw_img_urls = [single_img_url]

    loaded_images = []
    for u in raw_img_urls:
        fetched = _fetch(u)
        if fetched:
            loaded_images.append(fetched)

    if not loaded_images and master_card:
        # Extract top photo from master card as base image
        loaded_images = [master_card.crop((0, 0, width, split_y)).convert("RGB")]
    elif not loaded_images:
        loaded_images = [Image.new("RGB", (width, split_y), (15, 18, 25))]

    num_images = len(loaded_images)
    scene_interval = float(options.get("scene_interval", 2.5))  # Cut every 2.5 seconds!

    # ── 4. Render Frames → rawvideo pipe to temp MP4 ─────────────────────────
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
        cur_sec = f / fps
        t = f / max(total_frames - 1, 1)

        # ── Scene Switcher: Changes scene every 2.5 seconds ─────────────────
        scene_idx = int(cur_sec / scene_interval)
        t_scene   = (cur_sec % scene_interval) / scene_interval  # 0.0 to 1.0 within scene

        # Select image for this scene
        img_idx = (scene_idx) % num_images
        curr_img = loaded_images[img_idx]

        # Dynamic Camera Movement for this scene
        # Scene 0: Smooth push-in zoom
        # Scene 1: Subject crop with slow pan right
        # Scene 2: Wide cinematic view with slow zoom out
        # Scene 3: Dramatic push-in from top angle
        motion_style = scene_idx % 4

        viewport_w = width
        viewport_h = split_y

        if motion_style == 0:
            zoom = 1.00 + t_scene * 0.12
            zw, zh = int(viewport_w * zoom), int(viewport_h * zoom)
            bg_r = ImageOps.fit(curr_img, (zw, zh), centering=(0.5, 0.4))
            cx = (zw - viewport_w) // 2
            cy = (zh - viewport_h) // 2
            scene_frame = bg_r.crop((cx, cy, cx + viewport_w, cy + viewport_h)).convert("RGBA")
        elif motion_style == 1:
            zoom = 1.15
            zw, zh = int(viewport_w * zoom), int(viewport_h * zoom)
            bg_r = ImageOps.fit(curr_img, (zw, zh), centering=(0.5, 0.35))
            pan_x = int((t_scene - 0.5) * (zw - viewport_w) * 0.6)
            cx = max(0, min(zw - viewport_w, ((zw - viewport_w) // 2) + pan_x))
            cy = (zh - viewport_h) // 2
            scene_frame = bg_r.crop((cx, cy, cx + viewport_w, cy + viewport_h)).convert("RGBA")
        elif motion_style == 2:
            zoom = 1.14 - t_scene * 0.10
            zw, zh = int(viewport_w * zoom), int(viewport_h * zoom)
            bg_r = ImageOps.fit(curr_img, (zw, zh), centering=(0.5, 0.45))
            cx = (zw - viewport_w) // 2
            cy = (zh - viewport_h) // 2
            scene_frame = bg_r.crop((cx, cy, cx + viewport_w, cy + viewport_h)).convert("RGBA")
        else:
            zoom = 1.02 + t_scene * 0.14
            zw, zh = int(viewport_w * zoom), int(viewport_h * zoom)
            bg_r = ImageOps.fit(curr_img, (zw, zh), centering=(0.5, 0.25))
            cx = (zw - viewport_w) // 2
            cy = (zh - viewport_h) // 2
            scene_frame = bg_r.crop((cx, cy, cx + viewport_w, cy + viewport_h)).convert("RGBA")

        # Smooth cut transition between scenes
        if t_scene < 0.15 and scene_idx > 0:
            # Subtle flash / blend on scene change
            blend_a = int((1.0 - (t_scene / 0.15)) * 60)
            flash = Image.new("RGBA", (viewport_w, viewport_h), (255, 255, 255, blend_a))
            scene_frame = Image.alpha_composite(scene_frame, flash)

        # ── Base Canvas Assembly ────────────────────────────────────────────
        frame = Image.new("RGBA", (width, height), (10, 12, 18, 255))
        frame.paste(scene_frame, (0, 0))

        # Viewport bottom vignette shadow seam
        v_shadow = Image.new("RGBA", (width, 24), (0, 0, 0, 0))
        vs_draw  = ImageDraw.Draw(v_shadow)
        for i in range(24):
            vs_draw.line([(0, i), (width, i)], fill=(0, 0, 0, int(220 * (i / 24))))
        frame.paste(v_shadow, (0, split_y - 24), mask=v_shadow)

        # ── Paste Studio-Accurate Lower Third Strap (100% Perfect Text) ────
        if lower_third_overlay:
            frame.paste(lower_third_overlay, (0, split_y))
        else:
            # Fallback lower-third if no master card
            fb_draw = ImageDraw.Draw(frame)
            fb_draw.rectangle([(0, split_y), (width, height)], fill=(165, 0, 10))

        # ── Paste Studio Header Bar & Brand Pill ────────────────────────────
        if header_overlay:
            frame.paste(header_overlay, (0, 0), mask=header_overlay)

        # ── Pulsing LIVE Badge (Top-Right) ──────────────────────────────────
        d = ImageDraw.Draw(frame)
        pulse = 0.55 + 0.45 * math.sin(f * 0.4)
        live_r = int(200 + 55 * pulse)
        live_w, live_h = 100, 44
        live_x = width - live_w - 25
        live_y = 25
        d.rounded_rectangle([(live_x, live_y), (live_x + live_w, live_y + live_h)], radius=6, fill=(live_r, 0, 0), outline=(255, 255, 255), width=2)
        font_live = _font(20)
        d.text((live_x + 18, live_y + 11), "🔴 LIVE", font=font_live, fill=(255, 255, 255))

        # ── Razor Accent Line Along Split ───────────────────────────────────
        d.rectangle([(0, split_y - 2), (width, split_y + 1)], fill=(255, 215, 0))

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

    # ── 5. Audio Mixing: Voiceover + Background Newsroom Music ───────────────
    if has_audio and os.path.exists(tmp_audio) and has_bg_audio and os.path.exists(tmp_bg_audio):
        # Mix voiceover at 100% volume with background news bed at 20% volume
        # tmp_bg_audio is generated for the full duration, so amix duration=longest plays bg until video ends
        merge_cmd = [
            _FFMPEG, "-y",
            "-i", tmp_vid,
            "-i", tmp_audio,
            "-i", tmp_bg_audio,
            "-filter_complex",
            "[1:a]volume=1.0[voice];[2:a]volume=0.20[bg];[voice][bg]amix=inputs=2:duration=longest:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            out_path
        ]
        subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif has_audio and os.path.exists(tmp_audio):
        merge_cmd = [
            _FFMPEG, "-y",
            "-i", tmp_vid,
            "-i", tmp_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            out_path
        ]
        subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif has_bg_audio and os.path.exists(tmp_bg_audio):
        # Mute voiceover, play broadcast music bed at 60%
        merge_cmd = [
            _FFMPEG, "-y",
            "-i", tmp_vid,
            "-i", tmp_bg_audio,
            "-filter_complex", "[1:a]volume=0.60[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            out_path
        ]
        subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif os.path.exists(tmp_vid):
        import shutil
        shutil.move(tmp_vid, out_path)

    # ── 6. Cleanup Temp Files ───────────────────────────────────────────────
    for f_rm in [tmp_vid, tmp_audio, tmp_bg_audio]:
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
