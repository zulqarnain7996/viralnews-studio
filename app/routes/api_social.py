from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.social_poster import generate_social_caption, post_to_facebook, post_to_webhook
from app.database import get_article_by_id, add_to_queue, get_queue, get_history, log_post
import os

router = APIRouter(prefix="/api/social", tags=["social"])

class CaptionRequest(BaseModel):
    article: Optional[Dict[str, Any]] = None
    article_id: Optional[str] = None
    custom_hashtags: Optional[str] = None

class PostFacebookRequest(BaseModel):
    image_path: str
    caption: str
    test_mode: Optional[bool] = False

class PostWebhookRequest(BaseModel):
    image_path: str
    caption: str
    article: Optional[Dict[str, Any]] = None

class QueueItemRequest(BaseModel):
    article_id: str
    title: str
    summary: str
    caption: str
    card_image_path: str
    platform: Optional[str] = "facebook"
    scheduled_for: Optional[str] = None

class BulkPostRequest(BaseModel):
    items: List[Dict[str, Any]]  # Each dict has image_path, caption, article
    target: str = "facebook"      # "facebook" or "webhook" or "both"

@router.post("/caption")
def make_caption(req: CaptionRequest):
    art = req.article
    if not art and req.article_id:
        art = get_article_by_id(req.article_id)
    if not art:
        raise HTTPException(status_code=400, detail="Article or article_id is required")

    caption = generate_social_caption(art, custom_hashtags=req.custom_hashtags)
    return {"success": True, "caption": caption}

@router.post("/post-facebook")
def post_fb(req: PostFacebookRequest):
    # Resolve relative web URL to local path if needed
    img_path = req.image_path
    if img_path.startswith("/static/generated/"):
        fname = os.path.basename(img_path)
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "generated_cards")
        img_path = os.path.join(base_dir, fname)

    result = post_to_facebook(img_path, req.caption, test_mode=req.test_mode)
    return result

@router.post("/post-webhook")
def post_hook(req: PostWebhookRequest):
    img_path = req.image_path
    if img_path.startswith("/static/generated/"):
        fname = os.path.basename(img_path)
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "generated_cards")
        img_path = os.path.join(base_dir, fname)

    result = post_to_webhook(img_path, req.caption, req.article)
    return result

@router.post("/bulk-post")
def bulk_post(req: BulkPostRequest):
    results = []
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "generated_cards")

    for item in req.items:
        img_path = item.get("image_path", "")
        if img_path.startswith("/static/generated/"):
            img_path = os.path.join(base_dir, os.path.basename(img_path))
        caption = item.get("caption", "")

        res_item = {"image": img_path, "status": "unknown"}
        if req.target in ["facebook", "both"]:
            fb_res = post_to_facebook(img_path, caption)
            res_item["facebook"] = fb_res
        if req.target in ["webhook", "both"]:
            hook_res = post_to_webhook(img_path, caption, item.get("article"))
            res_item["webhook"] = hook_res

        results.append(res_item)

    return {"success": True, "processed": len(results), "results": results}

class TestFbRequest(BaseModel):
    page_id: str
    access_token: str

@router.post("/test-facebook")
def test_fb(req: TestFbRequest):
    from app.social_poster import test_facebook_connection
    return test_facebook_connection(req.page_id, req.access_token, force=True)

class PostTelegramRequest(BaseModel):
    image_path: str
    caption: str

@router.post("/post-telegram")
def post_tg(req: PostTelegramRequest):
    from app.social_poster import post_to_telegram
    img_path = req.image_path
    if img_path.startswith("/static/generated/"):
        fname = os.path.basename(img_path)
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "generated_cards")
        img_path = os.path.join(base_dir, fname)
    return post_to_telegram(img_path, req.caption)

@router.get("/queue")
def list_queue():
    items = get_queue()
    return {"success": True, "queue": items}

@router.post("/queue")
def queue_item(req: QueueItemRequest):
    item_id = add_to_queue(req.dict())
    return {"success": True, "queue_id": item_id}

@router.delete("/queue/{item_id}")
def remove_queue_item(item_id: int):
    from app.database import delete_queue_item
    delete_queue_item(item_id)
    return {"success": True, "deleted": item_id}

@router.get("/rate-limit-status")
def get_rate_limit():
    from app.social_poster import get_meta_rate_limit_status
    from app.database import get_queue_stats
    status = get_meta_rate_limit_status()
    stats = get_queue_stats()
    return {
        "success": True,
        "meta": status,
        "queue_stats": stats
    }

@router.post("/queue/publish-now/{item_id}")
def publish_queue_item_now(item_id: int):
    from app.database import get_queue, update_queue_item_status
    items = get_queue()
    target = next((i for i in items if i["id"] == item_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Queue item not found")

    update_queue_item_status(item_id, "processing")
    res = post_to_facebook(target["card_image_path"], target["caption"])
    if res.get("success") and res.get("mode") == "live":
        update_queue_item_status(item_id, "published", response_log=str(res))
    else:
        update_queue_item_status(item_id, "failed", response_log=str(res))
    return {"success": True, "result": res}

@router.get("/history")
def list_history(limit: int = 50):
    posts = get_history(limit=limit)
    return {"success": True, "history": posts}

