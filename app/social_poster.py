import os
import time
import json
import requests
import html
from datetime import datetime, timedelta
from app.database import get_setting, update_settings, log_post, log_scheduler, add_to_queue

# In-memory cache for connection test to prevent repeated calls
_fb_connection_cache = {
    "key": None,
    "result": None,
    "timestamp": 0
}

def parse_meta_usage_headers(headers):
    """
    Parses Meta's rate-limiting headers:
    - X-App-Usage: {"call_count": int, "total_cputime": int, "total_time": int}
    - X-Business-Use-Case-Usage
    - X-Page-Usage
    Returns a dict with parsed metrics and max usage percent.
    """
    usage_info = {
        "app_usage": {},
        "max_percent": 0,
        "is_warning": False,
        "is_throttled": False
    }

    app_usage_raw = headers.get("x-app-usage") or headers.get("X-App-Usage")
    if app_usage_raw:
        try:
            data = json.loads(app_usage_raw)
            usage_info["app_usage"] = data
            max_pct = max(data.get("call_count", 0), data.get("total_cputime", 0), data.get("total_time", 0))
            usage_info["max_percent"] = max_pct
            if max_pct >= 85:
                usage_info["is_throttled"] = True
            elif max_pct >= 65:
                usage_info["is_warning"] = True
        except Exception:
            pass

    # Save latest usage stats in database settings
    try:
        update_settings({
            "meta_last_app_usage": json.dumps(usage_info["app_usage"]),
            "meta_last_call_count": str(usage_info["max_percent"]),
            "meta_last_checked": datetime.now().isoformat()
        })
    except Exception:
        pass

    return usage_info

def check_meta_cooldown():
    """Checks if we are currently in an active cooldown window to prevent rate limits."""
    cooldown_until_str = get_setting("meta_rate_limit_cooldown_until", "")
    if cooldown_until_str:
        try:
            cooldown_until = datetime.fromisoformat(cooldown_until_str)
            now = datetime.now()
            if cooldown_until > now:
                remaining_mins = int((cooldown_until - now).total_seconds() / 60) + 1
                return True, remaining_mins
        except Exception:
            pass
    return False, 0

def set_meta_cooldown(minutes=45, reason="Meta rate limit protection"):
    cooldown_until = datetime.now() + timedelta(minutes=minutes)
    update_settings({
        "meta_rate_limit_cooldown_until": cooldown_until.isoformat(),
        "meta_cooldown_reason": reason
    })
    log_scheduler("meta_rate_limit", f"Activated Meta API cooldown for {minutes}m. Reason: {reason}", "warning")

def get_meta_rate_limit_status():
    """Returns real-time Meta API usage status for UI dashboard."""
    in_cooldown, rem_mins = check_meta_cooldown()
    last_usage_str = get_setting("meta_last_app_usage", "{}")
    last_call_count = int(get_setting("meta_last_call_count", "0"))
    last_checked = get_setting("meta_last_checked", "")
    cooldown_reason = get_setting("meta_cooldown_reason", "")
    token_status = get_setting("fb_token_status", "unknown")
    token_error = get_setting("fb_token_error", "")

    try:
        usage_data = json.loads(last_usage_str)
    except Exception:
        usage_data = {}

    if token_status == "expired":
        status_label = "Token Expired"
        status_color = "danger"
    elif token_status == "error":
        status_label = "Auth Error"
        status_color = "danger"
    elif in_cooldown:
        status_label = f"Rate-Limit Cooldown ({rem_mins}m left)"
        status_color = "danger"
    elif last_call_count >= 80:
        status_label = f"High Usage ({last_call_count}%)"
        status_color = "warning"
    elif last_call_count >= 50:
        status_label = f"Moderate ({last_call_count}%)"
        status_color = "info"
    elif token_status == "valid":
        status_label = "Connected / Safe"
        status_color = "success"
    else:
        status_label = "Optimal / Safe"
        status_color = "success"

    return {
        "status_label": status_label,
        "status_color": status_color,
        "token_status": token_status,
        "token_error": token_error,
        "in_cooldown": in_cooldown,
        "cooldown_remaining_mins": rem_mins,
        "cooldown_reason": cooldown_reason,
        "last_call_count": last_call_count,
        "usage_details": usage_data,
        "last_checked": last_checked
    }

def is_urdu_str(text):
    if not text:
        return False
    import re
    return bool(re.search(r'[\u0600-\u06FF]', text))

def generate_social_caption(article, platform="facebook", custom_hashtags=None):
    """
    Generates an engaging, high-retention social media caption with emojis,
    bullets, call to action, and targeted hashtags in English or Urdu.
    """
    title = html.unescape(article.get("title", "")).strip().replace('\xa0', ' ')
    summary = html.unescape(article.get("summary", "")).strip().replace('\xa0', ' ')
    source = html.unescape(article.get("source", "News Desk")).strip().replace('\xa0', ' ')
    category = article.get("category", "breaking").lower()
    page_handle = get_setting("page_handle", "@PakNewsOfficial")
    
    is_urdu = is_urdu_str(title)

    if is_urdu:
        if category == "pakistan":
            prefix = "🇵🇰 【 پاکستان کی بڑی خبر 】"
            base_tags = ["#PakistanNews", "#UrduNews", "#Pakistan", "#BreakingNews", "#GeoNews", "#BBCUrdu", "#تازہ_ترین", "#پاکستان"]
        elif category == "local":
            city = get_setting("local_city", "مقامی")
            prefix = f"📍 【 {city} کی خبر 】"
            base_tags = ["#LocalNews", "#UrduNews", "#Pakistan", "#CityUpdates", "#شہر_کی_خبریں"]
        elif category == "world":
            prefix = "🌍 【 عالمی خبریں 】"
            base_tags = ["#WorldNews", "#InternationalNews", "#UrduNews", "#GlobalUpdates", "#دنیا_کی_خبریں"]
        else:
            prefix = "🚨 【 بریکنگ نیوز 】"
            base_tags = ["#BreakingNews", "#UrduNews", "#ViralNews", "#اہم_خبر", "#تازہ_ترین"]

        if custom_hashtags:
            base_tags.extend(custom_hashtags.split())

        caption_lines = [
            f"{prefix}",
            f"📢 {title}",
            "",
            "📌 اہم تفصیلات:",
            f"• {summary}" if summary else f"• {title}",
            "",
            f"📰 ذرائع: {source}",
            f"👉 مزید خبروں اور تازہ ترین اپ ڈیٹس کے لیے فالو کریں {page_handle}",
            "💬 اس خبر پر آپ کی کیا رائے ہے؟ کمنٹس میں ضرور بتائیں 👇",
            "",
            " ".join(base_tags[:8])
        ]
    else:
        # English Caption
        if category == "pakistan":
            prefix = "🇵🇰 【 PAKISTAN UPDATE 】"
            base_tags = ["#PakistanNews", "#Pakistan", "#BreakingNews", "#GeoNews", "#DawnNews", "#ViralPakistan", "#LatestUpdates"]
        elif category == "local":
            city = get_setting("local_city", "Local")
            prefix = f"📍 【 {city.upper()} NEWS 】"
            base_tags = [f"#{city}News", "#LocalNews", "#Pakistan", "#CityUpdates", "#BreakingNews"]
        elif category == "world":
            prefix = "🌍 【 WORLD HEADLINES 】"
            base_tags = ["#WorldNews", "#GlobalHeadlines", "#InternationalNews", "#Breaking", "#DailyNews"]
        elif category == "trending":
            prefix = "🔥 【 TRENDING NOW 】"
            base_tags = ["#TrendingNow", "#ViralNews", "#TopStories", "#PakistanTrends", "#HotNews"]
        else:
            prefix = "🚨 【 BREAKING NEWS 】"
            base_tags = ["#BreakingNews", "#NewsAlert", "#LatestNews", "#HeadlineNews"]

        if custom_hashtags:
            base_tags.extend(custom_hashtags.split())

        caption_lines = [
            f"{prefix}",
            f"📢 {title}",
            "",
            f"📌 Key Highlights:",
            f"• {summary}" if summary else f"• {title}",
            "",
            f"📰 Source: {source}",
            f"👉 Follow {page_handle} for verified 24/7 breaking updates!",
            "💬 What are your thoughts? Drop your comments below 👇",
            "",
            " ".join(base_tags[:8])
        ]

    return "\n".join(caption_lines)

def resolve_and_save_page_token(page_id: str, access_token: str):
    """
    Ensures the token is a valid Page Access Token with publishing permissions.
    If access_token is a User Access Token, automatically queries Graph API /me/accounts,
    extracts the real Page Access Token for page_id, and updates the database.
    Returns (effective_token, details_dict).
    """
    if not page_id or not access_token:
        return access_token, None

    # Step 1: Check if the token already has direct Page access with can_post permission
    try:
        check_url = f"https://graph.facebook.com/v19.0/{page_id}?fields=id,name,can_post,tasks,category&access_token={access_token}"
        res = requests.get(check_url, timeout=10)
        data = res.json()
        if res.status_code == 200 and data.get("can_post") is True:
            return access_token, data
    except Exception:
        pass

    # Step 2: Query /me/accounts with access_token (in case it is a User Token)
    try:
        accounts_url = f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,access_token,tasks,category&access_token={access_token}"
        res = requests.get(accounts_url, timeout=12)
        data = res.json()
        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            target_str = str(page_id).strip()
            # Try to match by ID or page name
            for page in data["data"]:
                if str(page.get("id")) == target_str or str(page.get("name", "")).lower() == target_str.lower():
                    page_token = page.get("access_token")
                    if page_token:
                        update_settings({"fb_access_token": page_token})
                        if page.get("name"):
                            update_settings({"page_name": page.get("name")})
                        return page_token, page

            # If not exact match, check first available page
            first_page = data["data"][0]
            page_token = first_page.get("access_token")
            if page_token:
                update_settings({
                    "fb_page_id": str(first_page.get("id")),
                    "fb_access_token": page_token
                })
                if first_page.get("name"):
                    update_settings({"page_name": first_page.get("name")})
                return page_token, first_page
    except Exception as e:
        print(f"Error resolving Page Token from /me/accounts: {e}")

    return access_token, None

def test_facebook_connection(page_id, access_token, force=True):
    """
    Tests Facebook Graph API credentials by fetching Page info.
    Cached for 10 minutes to avoid redundant Meta API calls, unless force=True.
    Automatically exchanges User Access Tokens for Page Access Tokens.
    """
    if not page_id or not access_token:
        return {"success": False, "error": "Both Facebook Page ID and Page Access Token are required."}

    # Automatically resolve User Token -> Page Token if needed
    effective_token, page_info = resolve_and_save_page_token(page_id, access_token)
    if effective_token:
        access_token = effective_token

    cache_key = f"{page_id}:{access_token[:10]}"
    now = time.time()
    if not force and _fb_connection_cache["key"] == cache_key and (now - _fb_connection_cache["timestamp"]) < 600:
        cached = dict(_fb_connection_cache["result"])
        cached["cached"] = True
        return cached

    url = f"https://graph.facebook.com/v19.0/{page_id}?fields=id,name,link,category,can_post&access_token={access_token}"
    try:
        res = requests.get(url, timeout=12)
        parse_meta_usage_headers(res.headers)
        data = res.json()
        if res.status_code == 200 and "id" in data:
            update_settings({
                "fb_token_status": "valid",
                "fb_token_error": "",
                "fb_token_last_verified": datetime.now().isoformat()
            })
            result = {
                "success": True,
                "page_name": data.get("name"),
                "page_id": data.get("id"),
                "link": data.get("link"),
                "category": data.get("category"),
                "can_post": data.get("can_post", True),
                "message": f"Successfully connected to Facebook Page: '{data.get('name')}'!"
            }
            _fb_connection_cache["key"] = cache_key
            _fb_connection_cache["result"] = result
            _fb_connection_cache["timestamp"] = now
            return result
        else:
            error_obj = data.get("error", {})
            error_msg = error_obj.get("message", "Invalid Page ID or Access Token")
            error_code = error_obj.get("code")
            is_expired = "expired" in error_msg.lower() or error_code == 190
            status_val = "expired" if is_expired else "error"
            update_settings({
                "fb_token_status": status_val,
                "fb_token_error": error_msg,
                "fb_token_last_verified": datetime.now().isoformat()
            })
            _fb_connection_cache["key"] = None
            return {
                "success": False,
                "is_expired": is_expired,
                "error": error_msg
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def _resolve_clean_title(title, caption):
    """Extracts and normalizes clean headline string without emoji artifacts."""
    if title and str(title).strip():
        t = str(title).strip()
    elif caption and "\n" in caption:
        lines = [l.strip() for l in caption.split("\n") if l.strip()]
        t = lines[1] if len(lines) > 1 else lines[0]
    elif caption:
        t = str(caption)[:80].strip()
    else:
        t = "News Update"
    import re
    cleaned = re.sub(r'^[📢🚨🔥⚔️🇵🇰🌍📍🛡️⚡\s\-–—:]+', '', t).strip()
    return cleaned or t[:80]

def post_to_facebook(image_path, caption, test_mode=False, max_retries=3, title=None):
    """
    Posts image or video + caption to Facebook Page using Meta Graph API.
    Features:
      • Automatic User Token -> Page Token resolution & persistence
      • Automatic Meta Rate-Limit header inspection (X-App-Usage)
      • Active cooldown protection & publishing queue routing
      • Automatic exponential backoff retries for transient failures
    """
    clean_post_title = _resolve_clean_title(title, caption)
    page_id = get_setting("fb_page_id", "").strip()
    access_token = get_setting("fb_access_token", "").strip()
    simulation_mode = get_setting("simulation_mode", "false").lower() == "true" or test_mode

    # Auto-resolve User Token to Page Token if necessary
    effective_token, _ = resolve_and_save_page_token(page_id, access_token)
    if effective_token:
        access_token = effective_token

    # If simulation mode is explicitly enabled
    if simulation_mode:
        mock_id = f"sim_fb_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        log_post(
            title=clean_post_title,
            platform="facebook",
            card_image_path=image_path,
            caption=caption,
            post_id_or_url=f"https://facebook.com/page/posts/{mock_id}",
            status="simulated",
            error_message="Simulation Mode is active in settings"
        )
        return {
            "success": True,
            "mode": "simulated",
            "post_id": mock_id,
            "post_url": f"https://facebook.com/page/posts/{mock_id}",
            "message": "Simulated post! (To post real, enter your Page Token in Settings and turn off Simulation Mode)"
        }

    # Real Posting Validation
    if not page_id or not access_token:
        return {
            "success": False,
            "error": "Facebook Page ID or Access Token is missing! Please enter your Page ID and Token in the Settings tab to post live to your Facebook Page."
        }

    if not os.path.exists(image_path):
        return {"success": False, "error": f"File not found: {image_path}"}

    # 1. Check if Meta is currently in Cooldown (rate limit protection)
    in_cooldown, rem_mins = check_meta_cooldown()
    if in_cooldown:
        scheduled_time = datetime.now() + timedelta(minutes=rem_mins)
        queue_id = add_to_queue({
            "title": caption.split("\n")[1] if "\n" in caption else caption[:60],
            "caption": caption,
            "card_image_path": image_path,
            "platform": "facebook",
            "scheduled_for": scheduled_time.isoformat(),
            "status": "pending"
        })
        log_scheduler("meta_post_queued", f"Post queued (ID #{queue_id}) due to active Meta cooldown ({rem_mins}m remaining).")
        return {
            "success": True,
            "mode": "queued",
            "queue_id": queue_id,
            "scheduled_for": scheduled_time.strftime("%I:%M %p"),
            "message": f"Meta API protection active ({rem_mins}m cooldown). Post queued safely & will publish automatically!"
        }

    is_video = str(image_path).lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
    media_type_label = "VIDEO" if is_video else "PHOTO"

    # Meta Graph API Endpoints
    if is_video:
        url = f"https://graph.facebook.com/v19.0/{page_id}/videos"
        payload = {
            "description": caption,
            "access_token": access_token
        }
    else:
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        payload = {
            "caption": caption,
            "access_token": access_token
        }

    # 2. Exponential Backoff Retry Loop
    for attempt in range(max_retries):
        try:
            with open(image_path, "rb") as media_file:
                files = {"source": media_file}
                response = requests.post(url, data=payload, files=files, timeout=75)
                usage_info = parse_meta_usage_headers(response.headers)
                data = response.json()

                if response.status_code == 200 and "id" in data:
                    # Success
                    post_id = data["id"]
                    post_url = f"https://facebook.com/{post_id}"
                    log_post(
                        title=clean_post_title,
                        platform="facebook",
                        card_image_path=image_path,
                        caption=caption,
                        post_id_or_url=post_url,
                        status="published"
                    )

                    # If usage is high (>80%), activate proactive cooldown for next posts
                    if usage_info["is_throttled"]:
                        set_meta_cooldown(minutes=30, reason=f"Meta App Usage reached {usage_info['max_percent']}%")

                    return {
                        "success": True,
                        "mode": "live",
                        "post_id": post_id,
                        "post_url": post_url,
                        "api_usage": usage_info["app_usage"],
                        "message": f"REAL {media_type_label} PUBLISHED TO FACEBOOK PAGE!"
                    }

                # Check for Meta Rate Limit Errors
                error_obj = data.get("error", {})
                error_code = error_obj.get("code")
                error_subcode = error_obj.get("error_subcode")
                err_msg = error_obj.get("message", response.text)

                is_rate_limit = (
                    response.status_code == 429 
                    or error_code in [4, 17, 32, 613, 80004] 
                    or error_subcode in [2446079]
                    or "request limit reached" in err_msg.lower()
                    or "too many calls" in err_msg.lower()
                )

                if is_rate_limit:
                    # Meta rate limit encountered! Set cooldown and queue the post
                    cooldown_minutes = 45
                    set_meta_cooldown(minutes=cooldown_minutes, reason=f"Meta Error {error_code}: {err_msg}")
                    scheduled_time = datetime.now() + timedelta(minutes=cooldown_minutes)

                    queue_id = add_to_queue({
                        "title": caption.split("\n")[1] if "\n" in caption else caption[:60],
                        "caption": caption,
                        "card_image_path": image_path,
                        "platform": "facebook",
                        "scheduled_for": scheduled_time.isoformat(),
                        "status": "pending"
                    })

                    log_post(
                        title=clean_post_title,
                        platform="facebook",
                        card_image_path=image_path,
                        caption=caption,
                        post_id_or_url="",
                        status="rate_limited",
                        error_message=err_msg
                    )

                    return {
                        "success": True,
                        "mode": "rate_limited_queued",
                        "queue_id": queue_id,
                        "error_code": error_code,
                        "scheduled_for": scheduled_time.strftime("%I:%M %p"),
                        "message": f"Meta rate limit detected ({err_msg}). Post saved to queue and will automatically resume at {scheduled_time.strftime('%I:%M %p')}!"
                    }

                # Transient server error (500, 502, 503, 504) -> retry with exponential backoff
                if response.status_code in [500, 502, 503, 504] and attempt < max_retries - 1:
                    sleep_sec = 2 ** (attempt + 1)
                    time.sleep(sleep_sec)
                    continue

                # Normal error (bad token, invalid permissions, etc.)
                is_expired = "expired" in err_msg.lower() or error_code == 190
                if is_expired:
                    update_settings({
                        "fb_token_status": "expired",
                        "fb_token_error": err_msg,
                        "fb_token_last_verified": datetime.now().isoformat()
                    })
                    _fb_connection_cache["key"] = None

                log_post(
                    title=clean_post_title,
                    platform="facebook",
                    card_image_path=image_path,
                    caption=caption,
                    post_id_or_url="",
                    status="failed",
                    error_message=err_msg
                )
                if is_expired:
                    return {
                        "success": False,
                        "is_expired": True,
                        "error": f"Facebook Token Expired: {err_msg}. Please paste a fresh Page Access Token in Settings."
                    }
                return {"success": False, "error": f"Facebook API Error: {err_msg}"}

        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < max_retries - 1:
                sleep_sec = 2 ** (attempt + 1)
                time.sleep(sleep_sec)
                continue
            return {"success": False, "error": f"Connection error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Maximum retries exceeded."}


def post_to_telegram(image_path, caption, title=None):
    """
    Posts photo or video + caption directly to a Telegram Channel via Bot API.
    """
    clean_post_title = _resolve_clean_title(title, caption)
    bot_token = get_setting("telegram_bot_token", "").strip()
    channel_id = get_setting("telegram_channel_id", "").strip()

    if not bot_token or not channel_id:
        return {
            "success": False,
            "error": "Telegram Bot Token or Channel ID missing. Add them in Settings tab."
        }

    if not os.path.exists(image_path):
        return {"success": False, "error": "Media file not found"}

    is_video = str(image_path).lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
    endpoint = "sendVideo" if is_video else "sendPhoto"
    param_name = "video" if is_video else "photo"

    url = f"https://api.telegram.org/bot{bot_token}/{endpoint}"
    try:
        with open(image_path, "rb") as media_file:
            files = {param_name: media_file}
            data = {"chat_id": channel_id, "caption": caption[:1024]}
            res = requests.post(url, files=files, data=data, timeout=45)
            res_data = res.json()
            if res.status_code == 200 and res_data.get("ok"):
                log_post(
                    title=clean_post_title,
                    platform="telegram",
                    card_image_path=image_path,
                    caption=caption,
                    post_id_or_url=f"https://t.me/{channel_id.replace('@', '')}",
                    status="published"
                )
                media_label = "Video" if is_video else "Photo"
                return {"success": True, "message": f"{media_label} published live to Telegram Channel!"}
            else:
                err = res_data.get("description", res.text)
                return {"success": False, "error": f"Telegram Error: {err}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def post_to_webhook(image_path, caption, article_data=None, title=None):
    """
    Dispatches news card & caption to webhook (Zapier, Make.com, TikTok webhook, Discord)
    """
    clean_post_title = _resolve_clean_title(title or (article_data.get("title") if isinstance(article_data, dict) else None), caption)
    webhook_url = get_setting("webhook_url", "").strip()

    if not webhook_url:
        return {
            "success": False,
            "error": "Webhook URL is not configured. Please paste your TikTok/Make/Zapier webhook in the Settings tab."
        }

    try:
        filename = os.path.basename(image_path)
        payload = {
            "event": "new_social_post",
            "timestamp": datetime.now().isoformat(),
            "image_filename": filename,
            "image_url": f"/static/generated/{filename}",
            "caption": caption,
            "article": article_data or {}
        }
        res = requests.post(webhook_url, json=payload, timeout=15)
        is_success = res.status_code in [200, 201, 204]
        log_post(
            title=clean_post_title,
            platform="webhook_tiktok",
            card_image_path=image_path,
            caption=caption,
            post_id_or_url=webhook_url,
            status="published" if is_success else "failed"
        )
        return {
            "success": is_success,
            "message": "Dispatched to TikTok/Webhook workflow!" if is_success else f"Webhook responded with {res.status_code}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
