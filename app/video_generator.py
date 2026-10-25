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
import asyncio
import concurrent.futures
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from datetime import datetime

try:
    import imageio_ffmpeg
    _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    _FFMPEG = "ffmpeg"

try:
    import edge_tts
    _HAS_EDGE_TTS = True
except ImportError:
    _HAS_EDGE_TTS = False

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
AUDIO_DIR  = os.path.join(BASE_DIR, "static", "audio")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

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
    if not url:
        return None
    url = str(url).strip()
    # Support direct base64 data URLs (e.g. from file picker)
    if url.startswith("data:image"):
        img = _decode_base64_image(url)
        return img.convert("RGB") if img else None
    # Support local filesystem paths
    if os.path.exists(url):
        try:
            return Image.open(url).convert("RGB")
        except Exception:
            pass
    if url.startswith("/static/") or url.startswith("static/"):
        rel_p = url.lstrip("/")
        local_p = os.path.join(BASE_DIR, rel_p)
        if os.path.exists(local_p):
            try:
                return Image.open(local_p).convert("RGB")
            except Exception:
                pass
    if not url.startswith("http://") and not url.startswith("https://"):
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

def _ensure_preset_audio_files():
    """Generates the 3 essential broadcast news & trending music beds if missing."""
    breaking_path = os.path.join(AUDIO_DIR, "breaking_news.mp3")
    trending_path = os.path.join(AUDIO_DIR, "trending_viral.mp3")
    tense_path    = os.path.join(AUDIO_DIR, "investigative.mp3")

    if not os.path.exists(breaking_path):
        try:
            cmd = [
                _FFMPEG, "-y",
                "-f", "lavfi", "-i", "sine=f=55:d=30",
                "-f", "lavfi", "-i", "sine=f=110:d=30",
                "-f", "lavfi", "-i", "sine=f=880:d=30",
                "-f", "lavfi", "-i", "anoisesrc=d=30:c=pink:r=44100:a=0.02",
                "-filter_complex",
                "[0:a]tremolo=f=4:d=0.8,lowpass=f=120,volume=0.35[sub];" +
                "[1:a]tremolo=f=8:d=0.7,volume=0.15[mid];" +
                "[2:a]tremolo=f=12:d=0.9,highpass=f=600,volume=0.08[ticker];" +
                "[3:a]bandpass=f=2000:width=500,tremolo=f=16:d=0.9,volume=0.12[snare];" +
                "[sub][mid][ticker][snare]amix=inputs=4:duration=longest[out]",
                "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k", breaking_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except Exception:
            pass

    if not os.path.exists(trending_path):
        try:
            cmd = [
                _FFMPEG, "-y",
                "-f", "lavfi", "-i", "sine=f=60:d=30",
                "-f", "lavfi", "-i", "sine=f=440:d=30",
                "-f", "lavfi", "-i", "anoisesrc=d=30:c=white:r=44100:a=0.03",
                "-filter_complex",
                "[0:a]tremolo=f=4.2:d=0.9,lowpass=f=180,volume=0.40[kick];" +
                "[1:a]tremolo=f=8.4:d=0.8,volume=0.12[lead];" +
                "[2:a]bandpass=f=4000:width=1200,tremolo=f=16.8:d=0.95,volume=0.10[hats];" +
                "[kick][lead][hats]amix=inputs=3:duration=longest[out]",
                "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k", trending_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except Exception:
            pass

    if not os.path.exists(tense_path):
        try:
            cmd = [
                _FFMPEG, "-y",
                "-f", "lavfi", "-i", "sine=f=45:d=30",
                "-f", "lavfi", "-i", "sine=f=150:d=30",
                "-f", "lavfi", "-i", "anoisesrc=d=30:c=pink:r=44100:a=0.015",
                "-filter_complex",
                "[0:a]tremolo=f=1.8:d=0.9,lowpass=f=90,volume=0.45[heart];" +
                "[1:a]tremolo=f=3.6:d=0.6,volume=0.10[drone];" +
                "[2:a]highpass=f=2500,tremolo=f=7.2:d=0.9,volume=0.07[clock];" +
                "[heart][drone][clock]amix=inputs=3:duration=longest[out]",
                "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k", tense_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except Exception:
            pass

def _synthesize_voiceover(text: str, voice_id: str, speed_opt: str, pitch_opt: str, out_path: str) -> bool:
    """
    Synthesize broadcast reporter voiceover using Microsoft Edge Neural TTS with gTTS fallback.
    Delivers natural, human-like news reporter delivery.
    """
    # Map voice aliases to Microsoft Neural voice identifiers
    voice_map = {
        "ur": "ur-PK-AsadNeural",
        "ur_male": "ur-PK-AsadNeural",
        "ur_female": "ur-PK-UzmaNeural",
        "ur-PK-AsadNeural": "ur-PK-AsadNeural",
        "ur-PK-UzmaNeural": "ur-PK-UzmaNeural",
        "ur-IN-SalmanNeural": "ur-IN-SalmanNeural",
        "ur-IN-GulNeural": "ur-IN-GulNeural",
        "en": "en-US-GuyNeural",
        "en_male": "en-US-GuyNeural",
        "en_female": "en-US-JennyNeural",
        "en_uk": "en-GB-RyanNeural",
        "en-US-GuyNeural": "en-US-GuyNeural",
        "en-US-JennyNeural": "en-US-JennyNeural",
        "en-GB-RyanNeural": "en-GB-RyanNeural",
        "en-US-AndrewMultilingualNeural": "en-US-AndrewMultilingualNeural"
    }

    selected_voice = voice_map.get(voice_id)
    if not selected_voice:
        selected_voice = "ur-PK-AsadNeural" if _is_urdu(text) else "en-US-GuyNeural"

    # Speed rate tuning
    rate_map = {
        "news_fast": "+7%",  # Urgent TV news bulletin pace
        "normal": "+2%",     # Standard natural broadcast
        "slow": "-6%"        # Deliberate explanatory
    }
    rate_val = rate_map.get(speed_opt, "+5%")

    # Pitch tuning
    pitch_map = {
        "deep": "-3Hz",      # Deep authoritative resonance
        "normal": "+0Hz",
        "energetic": "+4Hz"  # Urgent Breaking News tone
    }
    pitch_val = pitch_map.get(pitch_opt, "+0Hz")

    # 1. Try Microsoft Edge Neural Voice (Ultra-Realistic)
    if _HAS_EDGE_TTS:
        try:
            async def _edge_worker():
                communicate = edge_tts.Communicate(text, selected_voice, rate=rate_val, pitch=pitch_val)
                await communicate.save(out_path)

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, _edge_worker())
                    future.result(timeout=30)
            else:
                asyncio.run(_edge_worker())

            if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
                return True
        except Exception as e:
            print(f"[VideoGen] EdgeTTS warning: {e}, attempting gTTS fallback...")

    # 2. Fallback to gTTS if EdgeTTS is unreachable
    if _HAS_GTTS:
        try:
            lang = "ur" if _is_urdu(text) else "en"
            tts = gTTS(text=text, lang=lang, slow=(speed_opt == "slow"))
            tts.save(out_path)
            return os.path.exists(out_path) and os.path.getsize(out_path) > 500
        except Exception as ge:
            print(f"[VideoGen] gTTS fallback error: {ge}")

    return False

def _build_python_video_template(template_name, width, height, split_y, title, source, page_name, page_handle, is_urdu):
    master = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(master)
    header_h = int(split_y * 0.22)

    # 1. Header Bar
    if template_name == "combat_steel_war":
        d.rectangle([(0, 0), (width, header_h)], fill=(17, 22, 29, 255))
        d.rectangle([(0, header_h - 4), (width, header_h)], fill=(234, 179, 8, 255))
        d.text((35, header_h - 32), f"⚔️ {page_name}", font=_font(22), fill=(250, 204, 21))
    elif template_name == "viral_neon_cyber":
        d.rectangle([(0, 0), (width, header_h)], fill=(8, 12, 20, 255))
        d.rectangle([(0, header_h - 4), (width, header_h)], fill=(6, 182, 212, 255))
        d.text((35, header_h - 32), f"🔥 {page_name}", font=_font(22), fill=(6, 182, 212))
    elif template_name == "golden_prestige_bulletin":
        d.rectangle([(0, 0), (width, header_h)], fill=(5, 12, 30, 255))
        d.rectangle([(0, header_h - 5), (width, header_h)], fill=(234, 179, 8, 255))
        d.text((35, header_h - 32), f"👑 {page_name}", font=_font(22), fill=(254, 240, 138))
    else:
        d.rectangle([(0, 0), (width, header_h)], fill=(143, 0, 12, 255))
        d.rectangle([(0, header_h - 5), (width, header_h)], fill=(255, 215, 0, 255))
        d.text((35, header_h - 32), f"🛡️ {page_name}", font=_font(22), fill=(255, 255, 255))

    # 2. Lower Third Base Container
    if template_name == "combat_steel_war":
        d.rectangle([(0, split_y), (width, height)], fill=(15, 20, 26, 245))
        d.rectangle([(0, split_y), (width, split_y + 48)], fill=(220, 38, 38, 255))
        d.rectangle([(0, split_y + 46), (width, split_y + 50)], fill=(250, 204, 21, 255))
        tag_text = _shape("⚠️ عسکری و دفاعی اپڈیٹ // COMBAT ALERT") if is_urdu else "⚠️ COMBAT ALERT // WAR BULLETIN"
        d.text((30, split_y + 12), tag_text, font=_font(20, is_urdu), fill=(255, 255, 255))
    elif template_name == "viral_neon_cyber":
        d.rectangle([(0, split_y), (width, height)], fill=(8, 12, 20, 245))
        d.rectangle([(0, split_y), (width, split_y + 6)], fill=(6, 182, 212, 255))
        d.rounded_rectangle([(30, split_y + 16), (220, split_y + 50)], radius=6, fill=(236, 72, 153, 255))
        d.text((44, split_y + 22), "🔥 VIRAL NEWS", font=_font(18), fill=(255, 255, 255))
    elif template_name == "golden_prestige_bulletin":
        d.rectangle([(0, split_y), (width, height)], fill=(5, 12, 30, 245))
        d.rectangle([(0, split_y), (width, split_y + 5)], fill=(234, 179, 8, 255))
        d.rounded_rectangle([(30, split_y + 16), (240, split_y + 52)], radius=4, fill=(15, 23, 42, 255), outline=(234, 179, 8, 255), width=2)
        d.text((44, split_y + 22), "👑 SPECIAL REPORT", font=_font(18), fill=(254, 240, 138))
    else:
        d.rectangle([(0, split_y), (width, height)], fill=(12, 16, 25, 245))
        d.rectangle([(0, split_y), (width, split_y + 52)], fill=(185, 28, 28, 255))
        d.rectangle([(0, split_y + 50), (width, split_y + 54)], fill=(255, 215, 0, 255))
        tag_text = _shape("🚨 بریکنگ نیوز | BREAKING NEWS") if is_urdu else "🚨 BREAKING NEWS"
        d.text((30, split_y + 12), tag_text, font=_font(22, is_urdu), fill=(255, 255, 255))

    # 3. Headline Typography
    lines = _wrap(title, width=28 if is_urdu else 36)[:3]
    h_y = split_y + 80
    font_h = _font(36 if is_urdu else 32, is_urdu)
    text_color = (250, 204, 21) if template_name == "combat_steel_war" else (255, 255, 255)
    for line in lines:
        disp_l = _shape(line) if is_urdu else line
        d.text((35, h_y), disp_l, font=font_h, fill=text_color)
        h_y += 55 if is_urdu else 44

    # 4. Footer Ticker
    d.rectangle([(0, height - 46), (width, height)], fill=(6, 9, 16, 255))
    d.rectangle([(0, height - 46), (width, height - 44)], fill=(234, 179, 8, 255))
    d.text((30, height - 34), f"📢 {source} • {page_handle}", font=_font(16), fill=(148, 163, 184))

    return master

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

    # Ensure preset broadcast audio beds exist
    _ensure_preset_audio_files()

    # Voiceover configuration
    voice_choice = options.get("voice_id") or options.get("voice_lang", "auto")
    mute_voice   = options.get("mute_audio", False) or (voice_choice == "mute")
    voice_speed  = options.get("voice_speed", "news_fast")
    voice_pitch  = options.get("voice_pitch", "normal")
    narr_text    = options.get("narrative_text") or (title if is_urdu else f"{title}. {summary}"[:400])

    art_id       = article.get("id") or datetime.now().strftime("%Y%m%d%H%M%S")
    ts           = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name     = f"video_{art_id}_{aspect_ratio.replace(':', 'x')}_{ts}.mp4"
    out_path     = os.path.join(OUTPUT_DIR, out_name)
    tmp_vid      = os.path.join(OUTPUT_DIR, f"_tmp_v_{art_id}.mp4")
    tmp_audio    = os.path.join(OUTPUT_DIR, f"_tmp_a_{art_id}.mp3")
    tmp_bg_audio = os.path.join(OUTPUT_DIR, f"_tmp_bg_{art_id}.mp3")

    # ── 1. Voiceover (Microsoft Edge Neural Anchor TTS) ─────────────────────
    duration   = 8.0
    has_audio  = False

    if not mute_voice:
        has_audio = _synthesize_voiceover(
            text=narr_text,
            voice_id=voice_choice,
            speed_opt=voice_speed,
            pitch_opt=voice_pitch,
            out_path=tmp_audio
        )
        if has_audio and os.path.exists(tmp_audio):
            duration = _audio_duration(tmp_audio)
            duration = max(6.0, min(30.0, duration))

    fps          = 25
    total_frames = int(duration * fps)

    # ── 2. Background Music Configuration ───────────────────────────────────
    bg_music_choice  = options.get("bg_music", "breaking")
    bg_music_volume  = float(options.get("bg_music_volume", 0.20))
    custom_music_url = options.get("custom_music_url")

    bg_music_file = None
    if bg_music_choice == "breaking":
        bg_music_file = os.path.join(AUDIO_DIR, "breaking_news.mp3")
    elif bg_music_choice == "trending":
        bg_music_file = os.path.join(AUDIO_DIR, "trending_viral.mp3")
    elif bg_music_choice == "tense":
        bg_music_file = os.path.join(AUDIO_DIR, "investigative.mp3")
    elif bg_music_choice == "custom" and custom_music_url:
        try:
            r = requests.get(custom_music_url, timeout=15)
            if r.status_code == 200:
                with open(tmp_bg_audio, "wb") as f_out:
                    f_out.write(r.content)
                bg_music_file = tmp_bg_audio
        except Exception as e:
            print(f"[VideoGen] Custom music download failed: {e}")
            bg_music_file = os.path.join(AUDIO_DIR, "breaking_news.mp3")
    elif bg_music_choice != "none":
        bg_music_file = os.path.join(AUDIO_DIR, "breaking_news.mp3")

    has_bg_audio = bool(bg_music_file and os.path.exists(bg_music_file))

    # ── 3. Prepare Visual Assets (Studio Card & Photo Viewport) ─────────────
    card_data = options.get("card_image_data")
    master_card = _decode_base64_image(card_data)

    video_template = options.get("video_template", "breaking_red_broadcast")

    # If no canvas card provided from client, use dedicated video template
    if not master_card:
        if video_template != "studio_canvas":
            master_card = _build_python_video_template(
                template_name=video_template,
                width=width,
                height=height,
                split_y=split_y,
                title=title,
                source=source,
                page_name=page_name,
                page_handle=page_handle,
                is_urdu=is_urdu
            )
        else:
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

    # If only 1 image provided, generate 4 distinct cinematic angles/crops so scenes change visibly!
    if len(loaded_images) == 1:
        base_img = loaded_images[0]
        bw, bh = base_img.size
        # Shot 1: Wide establishing shot
        shot1 = base_img
        # Shot 2: Close-up center focus
        shot2 = ImageOps.fit(base_img.crop((int(bw * 0.12), int(bh * 0.12), int(bw * 0.88), int(bh * 0.88))), (bw, bh), centering=(0.5, 0.4))
        # Shot 3: Left-side subject focus
        shot3 = ImageOps.fit(base_img.crop((0, 0, int(bw * 0.78), bh)), (bw, bh), centering=(0.25, 0.5))
        # Shot 4: Right-side subject focus
        shot4 = ImageOps.fit(base_img.crop((int(bw * 0.22), 0, bw, bh)), (bw, bh), centering=(0.75, 0.5))
        loaded_images = [shot1, shot2, shot3, shot4]

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

    prev_scene_snapshot = None
    last_scene_idx = -1

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

        # Smooth television crossfade dissolve + broadcast flash transition
        if scene_idx > 0 and t_scene < 0.25 and prev_scene_snapshot:
            alpha = min(1.0, max(0.0, t_scene / 0.25))
            scene_frame = Image.blend(prev_scene_snapshot, scene_frame, alpha)
            flash_a = int((1.0 - alpha) * 100)
            flash = Image.new("RGBA", (viewport_w, viewport_h), (255, 255, 255, flash_a))
            scene_frame = Image.alpha_composite(scene_frame, flash)

        # Update snapshot for next transition
        prev_scene_snapshot = scene_frame.copy()

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

    # ── 5. Audio Mixing: Voiceover + Background Music ───────────────────────
    if has_audio and os.path.exists(tmp_audio) and has_bg_audio and os.path.exists(bg_music_file):
        # Mix voiceover at 100% volume with looped background news bed at user-selected volume
        # We loop and trim the bg track to duration so amix duration=longest runs cleanly without buffer hangs
        merge_cmd = [
            _FFMPEG, "-y",
            "-i", tmp_vid,
            "-i", tmp_audio,
            "-stream_loop", "-1", "-t", str(round(duration, 2)), "-i", bg_music_file,
            "-filter_complex",
            f"[1:a]volume=1.0[voice];[2:a]volume={bg_music_volume}[bg];[voice][bg]amix=inputs=2:duration=longest:dropout_transition=2[aout]",
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
    elif has_bg_audio and os.path.exists(bg_music_file):
        # Voice muted, play background music bed
        merge_cmd = [
            _FFMPEG, "-y",
            "-i", tmp_vid,
            "-stream_loop", "-1", "-t", str(round(duration, 2)), "-i", bg_music_file,
            "-filter_complex", f"[1:a]volume={min(0.65, bg_music_volume * 2.5)}[aout]",
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
