import os
import zipfile
import io
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.image_generator import generate_news_card, OUTPUT_DIR
from app.database import get_article_by_id, get_all_settings
from app.video_generator import generate_news_video

router = APIRouter(prefix="/api/cards", tags=["cards"])

class CardGenerateRequest(BaseModel):
    article: Optional[Dict[str, Any]] = None
    article_id: Optional[str] = None
    theme: Optional[str] = "breaking_red"
    aspect_ratio: Optional[str] = "1:1"
    page_name: Optional[str] = None
    page_handle: Optional[str] = None
    category_tag: Optional[str] = None
    custom_image_url: Optional[str] = None
    title_override: Optional[str] = None
    summary_override: Optional[str] = None

class BulkCardGenerateRequest(BaseModel):
    article_ids: List[str]
    theme: Optional[str] = "breaking_red"
    aspect_ratio: Optional[str] = "1:1"
    page_name: Optional[str] = None
    page_handle: Optional[str] = None

@router.post("/generate")
def generate_card(req: CardGenerateRequest):
    settings = get_all_settings()
    
    # Resolve article
    art = req.article
    if not art and req.article_id:
        art = get_article_by_id(req.article_id)
        
    if not art:
        raise HTTPException(status_code=400, detail="Article or article_id is required.")

    # Apply overrides if provided
    prepared_article = dict(art)
    if req.title_override:
        prepared_article["title"] = req.title_override
    if req.summary_override:
        prepared_article["summary"] = req.summary_override
        
    options = {
        "theme": req.theme or settings.get("default_theme", "breaking_red"),
        "aspect_ratio": req.aspect_ratio or settings.get("default_aspect_ratio", "1:1"),
        "page_name": req.page_name or settings.get("page_name", "PAK NEWS 24/7"),
        "page_handle": req.page_handle or settings.get("page_handle", "@PakNewsOfficial"),
        "category_tag": req.category_tag,
        "custom_image_url": req.custom_image_url
    }
    
    result = generate_news_card(prepared_article, options)
    return {"success": True, "card": result}

@router.post("/bulk-generate")
def bulk_generate(req: BulkCardGenerateRequest):
    settings = get_all_settings()
    theme = req.theme or settings.get("default_theme", "breaking_red")
    aspect_ratio = req.aspect_ratio or settings.get("default_aspect_ratio", "1:1")
    page_name = req.page_name or settings.get("page_name", "PAK NEWS 24/7")
    page_handle = req.page_handle or settings.get("page_handle", "@PakNewsOfficial")

    generated_cards = []
    for art_id in req.article_ids:
        art = get_article_by_id(art_id)
        if art:
            options = {
                "theme": theme,
                "aspect_ratio": aspect_ratio,
                "page_name": page_name,
                "page_handle": page_handle
            }
            try:
                card_res = generate_news_card(art, options)
                generated_cards.append({
                    "article_id": art_id,
                    "title": art["title"],
                    "card": card_res
                })
            except Exception as e:
                print(f"Error bulk generating card for {art_id}: {e}")

    return {
        "success": True,
        "total_requested": len(req.article_ids),
        "total_generated": len(generated_cards),
        "cards": generated_cards
    }

class DownloadZipRequest(BaseModel):
    filenames: List[str]

@router.post("/download-zip")
def download_zip(req: DownloadZipRequest):
    if not req.filenames:
        raise HTTPException(status_code=400, detail="Filenames list cannot be empty")

    zip_filename = f"news_cards_export_{len(req.filenames)}.zip"
    zip_path = os.path.join(OUTPUT_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for fname in req.filenames:
            clean_name = os.path.basename(fname)
            full_path = os.path.join(OUTPUT_DIR, clean_name)
            if os.path.exists(full_path):
                zip_file.write(full_path, arcname=clean_name)

    return FileResponse(zip_path, filename=zip_filename, media_type="application/zip")

class UploadCanvasRequest(BaseModel):
    image_data: str  # Base64 data URL
    title: Optional[str] = "Live News Card"
    filename_prefix: Optional[str] = "studio_canvas"

@router.post("/upload-canvas")
def upload_canvas(req: UploadCanvasRequest):
    """
    Saves a base64 encoded PNG from the HTML5 Live Studio Canvas directly to the server.
    Ensures that the posted card matches what the user previewed with 100% fidelity.
    """
    import base64
    from datetime import datetime

    data_str = req.image_data
    if "base64," in data_str:
        data_str = data_str.split("base64,")[1]

    try:
        raw_bytes = base64.b64decode(data_str)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{req.filename_prefix}_{timestamp}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(raw_bytes)

        return {
            "success": True,
            "filename": filename,
            "file_path": filepath,
            "web_url": f"/static/generated/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save canvas image: {e}")

@router.post("/upload-image")
async def upload_custom_image(file: UploadFile = File(...)):
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    safe_name = f"custom_bg_{os.urandom(4).hex()}{file_ext}"
    dest_path = os.path.join(upload_dir, safe_name)
    
    with open(dest_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    return {
        "success": True,
        "url": f"/static/uploads/{safe_name}",
        "filename": safe_name
    }

@router.get("/proxy-image")
def proxy_image(url: str):
    """
    Proxies external news images (Express News, BBC, Dawn, etc.) to eliminate browser
    CORS restrictions when drawing onto HTML5 Canvas.
    Also automatically upgrades small thumbnails to original high-resolution versions.
    """
    import requests
    import re
    from fastapi.responses import Response

    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid image URL")

    # 1. Upgrade small thumbnails to original full-res versions
    high_res_url = url
    if "img.express.pk" in high_res_url:
        high_res_url = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', high_res_url)
    if "ichef.bbci.co.uk" in high_res_url and "/240/" in high_res_url:
        high_res_url = high_res_url.replace("/240/", "/1024/")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }

    try:
        resp = requests.get(high_res_url, headers=headers, timeout=8)
        if resp.status_code != 200 and high_res_url != url:
            resp = requests.get(url, headers=headers, timeout=8)

        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Cache-Control": "public, max-age=86400"
                }
            )
        else:
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch image")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Video Generation ─────────────────────────────────────────────────────────

class VideoGenerateRequest(BaseModel):
    article:          Optional[Dict[str, Any]] = None
    article_id:       Optional[str] = None
    page_name:        Optional[str] = None
    page_handle:      Optional[str] = None
    custom_image_url: Optional[str] = None
    image_urls:       Optional[List[str]] = None
    card_image_data:  Optional[str] = None
    video_template:   Optional[str] = "breaking_red_broadcast"
    aspect_ratio:     Optional[str] = "9:16"
    voice_lang:       Optional[str] = "auto"
    voice_id:         Optional[str] = None
    voice_speed:      Optional[str] = "news_fast"
    voice_pitch:      Optional[str] = "normal"
    bg_music:         Optional[str] = "breaking"
    bg_music_volume:  Optional[float] = 0.20
    custom_music_url: Optional[str] = None
    transition:       Optional[str] = "ken_burns"
    narrative_text:   Optional[str] = None
    mute_audio:       Optional[bool] = False
    scene_interval:   Optional[float] = 2.5

@router.post("/generate-video")
def generate_video(req: VideoGenerateRequest):
    """Generate an advanced animated MP4 news clip with customizable ratio, multiple images, transitions, and voiceover."""
    settings = get_all_settings()

    art = req.article
    if not art and req.article_id:
        art = get_article_by_id(req.article_id)
    if not art:
        raise HTTPException(status_code=400, detail="Article or article_id is required.")

    options = {
        "page_name":        req.page_name   or settings.get("page_name",   "PAK NEWS 24/7"),
        "page_handle":      req.page_handle or settings.get("page_handle", "@PakNewsOfficial"),
        "custom_image_url": req.custom_image_url,
        "image_urls":       req.image_urls or ([req.custom_image_url] if req.custom_image_url else []),
        "card_image_data":  req.card_image_data,
        "video_template":   req.video_template or "breaking_red_broadcast",
        "aspect_ratio":     req.aspect_ratio or "9:16",
        "voice_lang":       req.voice_lang or "auto",
        "voice_id":         req.voice_id,
        "voice_speed":      req.voice_speed or "news_fast",
        "voice_pitch":      req.voice_pitch or "normal",
        "bg_music":         req.bg_music or "breaking",
        "bg_music_volume":  req.bg_music_volume if req.bg_music_volume is not None else 0.20,
        "custom_music_url": req.custom_music_url,
        "transition":       req.transition or "ken_burns",
        "narrative_text":   req.narrative_text,
        "mute_audio":       bool(req.mute_audio),
        "scene_interval":   req.scene_interval or 2.5
    }

    try:
        result = generate_news_video(art, options)
        return {"success": True, "video": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")
