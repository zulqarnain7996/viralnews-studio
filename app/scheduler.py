import os
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import (
    get_setting, log_scheduler, is_article_posted,
    get_next_queue_item, update_queue_item_status, add_to_queue
)
from app.news_fetcher import fetch_news_by_category
from app.image_generator import generate_news_card
from app.social_poster import (
    generate_social_caption, post_to_facebook, post_to_webhook,
    post_to_telegram, check_meta_cooldown
)

scheduler = BackgroundScheduler()

def process_publishing_queue():
    """
    Background worker that runs every 5 minutes.
    Publishes pending items from the database queue whose scheduled time has arrived,
    honoring Meta API rate limits and cooldown protection.
    """
    in_cooldown, rem_mins = check_meta_cooldown()
    if in_cooldown:
        return

    item = get_next_queue_item()
    if not item:
        return

    queue_id = item["id"]
    platform = item.get("platform", "facebook")
    image_path = item.get("card_image_path")
    caption = item.get("caption")

    update_queue_item_status(queue_id, "processing")
    log_scheduler("queue_processing", f"Publishing queued post #{queue_id}: '{item.get('title', '')[:35]}...'")

    try:
        if platform == "facebook":
            res = post_to_facebook(image_path, caption)
            if res.get("success") and res.get("mode") == "live":
                update_queue_item_status(queue_id, "published", response_log=json.dumps(res))
                log_scheduler("queue_success", f"Queued post #{queue_id} published successfully to Facebook Page.")
            elif res.get("mode") in ["queued", "rate_limited_queued"]:
                next_try = (datetime.now() + timedelta(minutes=45)).isoformat()
                update_queue_item_status(queue_id, "pending", response_log=json.dumps(res), scheduled_for=next_try)
            else:
                update_queue_item_status(queue_id, "failed", response_log=json.dumps(res))
        elif platform == "telegram":
            res = post_to_telegram(image_path, caption)
            if res.get("success"):
                update_queue_item_status(queue_id, "published", response_log=json.dumps(res))
            else:
                update_queue_item_status(queue_id, "failed", response_log=json.dumps(res))
    except Exception as e:
        update_queue_item_status(queue_id, "failed", response_log=str(e))
        log_scheduler("queue_error", f"Error publishing queued item #{queue_id}: {str(e)}", "error")

def run_autopilot_cycle(manual_trigger=False):
    """
    Automatic cycle:
    1. Checks if autopilot is enabled (or manual trigger).
    2. Fetches fresh news.
    3. Finds unseen/unposted news.
    4. Automatically generates Facebook/TikTok news cards.
    5. Staggers posts with safe intervals (30-60 mins) to prevent Facebook rate limits.
    6. Logs the execution.
    """
    enabled = get_setting("autopilot_enabled", "false").lower() == "true"
    if not enabled and not manual_trigger:
        return {"status": "skipped", "message": "Auto-Pilot is currently disabled in settings."}

    # Active Hours Window Check (e.g. 06:00 to 23:00)
    if not manual_trigger:
        start_time_str = get_setting("autopilot_start_time", "06:00")
        end_time_str = get_setting("autopilot_end_time", "23:00")
        now_time_str = datetime.now().strftime("%H:%M")
        if start_time_str and end_time_str:
            if start_time_str <= end_time_str:
                if not (start_time_str <= now_time_str <= end_time_str):
                    log_scheduler("auto_pilot_skipped", f"Current time ({now_time_str}) is outside active hours window ({start_time_str} - {end_time_str}).", "info")
                    return {"status": "skipped", "message": f"Outside active hours ({start_time_str} - {end_time_str})."}
            else: # Overnight window (e.g. 22:00 to 06:00)
                if not (now_time_str >= start_time_str or now_time_str <= end_time_str):
                    log_scheduler("auto_pilot_skipped", f"Current time ({now_time_str}) is outside active hours window ({start_time_str} - {end_time_str}).", "info")
                    return {"status": "skipped", "message": f"Outside active hours ({start_time_str} - {end_time_str})."}

    category = get_setting("autopilot_category", "trending")
    max_posts = int(get_setting("autopilot_max_posts", "2"))
    theme = get_setting("autopilot_theme", get_setting("default_theme", "turkiye_urdu_split"))
    aspect_ratio = get_setting("default_aspect_ratio", "1:1")
    page_name = get_setting("page_name", "PAK NEWS 24/7")
    page_handle = get_setting("page_handle", "@PakNewsOfficial")
    local_city = get_setting("local_city", "Lahore")
    language = get_setting("autopilot_language", get_setting("language", "urdu"))
    post_interval_mins = int(get_setting("post_interval_minutes", "45"))

    fb_enabled = get_setting("autopilot_fb", "true").lower() == "true"
    tg_enabled = get_setting("autopilot_tg", "false").lower() == "true"
    webhook_enabled = get_setting("autopilot_webhook", "false").lower() == "true"

    log_scheduler("auto_pilot_start", f"Running cycle for category: {category}, language: {language}, theme: {theme}, max posts: {max_posts}")

    try:
        # Fetch fresh news
        articles = fetch_news_by_category(category=category, city=local_city, language=language, limit=20)
        unposted = []

        for art in articles:
            if not is_article_posted(art["title"]):
                unposted.append(art)
                if len(unposted) >= max_posts:
                    break

        if not unposted:
            log_scheduler("auto_pilot_complete", "No new unposted articles found. Newsroom is up to date.", "info")
            return {"status": "success", "posted_count": 0, "message": "No new unposted articles found."}

        posted_count = 0
        results = []

        for idx, art in enumerate(unposted):
            # 1. Generate News Card Graphic
            options = {
                "theme": theme,
                "aspect_ratio": aspect_ratio,
                "page_name": page_name,
                "page_handle": page_handle
            }
            card_res = generate_news_card(art, options)

            # 2. Generate Caption
            caption = generate_social_caption(art)

            if idx == 0:
                # First post publishes immediately based on enabled platforms
                fb_res = post_to_facebook(card_res["file_path"], caption) if fb_enabled else {"mode": "disabled"}
                if webhook_enabled:
                    post_to_webhook(card_res["file_path"], caption, art)
                if tg_enabled:
                    post_to_telegram(card_res["file_path"], caption)

                posted_count += 1
                results.append({
                    "title": art["title"],
                    "card": card_res["filename"],
                    "fb_status": fb_res.get("mode", "done"),
                    "scheduled_for": "Now"
                })
                log_scheduler("article_published", f"Auto-posted immediately: '{art['title'][:40]}...' via {fb_res.get('mode')}")
            else:
                # Subsequent posts staggered at safe intervals (30-60m)
                stagger_mins = idx * post_interval_mins
                scheduled_time = datetime.now() + timedelta(minutes=stagger_mins)

                queue_id = add_to_queue({
                    "article_id": art.get("id"),
                    "title": art.get("title"),
                    "summary": art.get("summary"),
                    "caption": caption,
                    "card_image_path": card_res["file_path"],
                    "platform": "facebook",
                    "scheduled_for": scheduled_time.isoformat(),
                    "status": "pending"
                })

                posted_count += 1
                results.append({
                    "title": art["title"],
                    "card": card_res["filename"],
                    "fb_status": "queued",
                    "scheduled_for": scheduled_time.strftime("%I:%M %p")
                })
                log_scheduler("article_queued", f"Staggered post #{queue_id} scheduled for {scheduled_time.strftime('%I:%M %p')} ({stagger_mins}m delay to protect Meta limits).")

        log_scheduler("auto_pilot_complete", f"Successfully processed {posted_count} news items (staggered at {post_interval_mins}m intervals).", "success")
        return {
            "status": "success",
            "posted_count": posted_count,
            "items": results
        }
    except Exception as e:
        log_scheduler("auto_pilot_error", str(e), "error")
        return {"status": "error", "message": str(e)}

def keep_alive_ping():
    """
    Pings the server's own public URL (e.g. https://viralnews-studio.onrender.com/health)
    every 8 minutes. Because the request travels through public DNS / Render's edge proxy,
    Render registers active incoming HTTP traffic, resetting the 15-minute inactivity sleep counter
    and keeping the service awake 24/7!
    """
    import requests
    public_url = get_setting("app_public_url", "https://viralnews-studio.onrender.com").rstrip("/")
    try:
        ping_url = f"{public_url}/health"
        res = requests.get(ping_url, timeout=15)
        if res.status_code == 200:
            log_scheduler("keep_alive_ping", f"Self-ping to {ping_url} (HTTP 200) — Server awake 24/7", "info")
    except Exception as e:
        # Ignore network errors on localhost or during startup
        pass

def init_scheduler():
    """Initializes and starts the background scheduler."""
    if not scheduler.running:
        interval_hours = int(get_setting("autopilot_interval_hours", "4"))
        # 1. Main Auto-Pilot Cycle
        scheduler.add_job(
            run_autopilot_cycle,
            'interval',
            hours=interval_hours,
            id='autopilot_job',
            replace_existing=True
        )
        # 2. Queue Publishing Worker (every 5 minutes)
        scheduler.add_job(
            process_publishing_queue,
            'interval',
            minutes=5,
            id='queue_worker_job',
            replace_existing=True
        )
        # 3. 24/7 Keep-Alive Self-Pinger (runs every 8 minutes to prevent Render sleep)
        scheduler.add_job(
            keep_alive_ping,
            'interval',
            minutes=8,
            id='keep_alive_ping_job',
            replace_existing=True
        )
        scheduler.start()
        print(f"[Scheduler] Started background auto-pilot every {interval_hours}h, queue processor every 5m, and keep-alive pinger every 8m.")

def update_scheduler_interval(interval_hours):
    """Updates the execution interval of the running scheduler."""
    if scheduler.running:
        scheduler.reschedule_job(
            'autopilot_job',
            trigger='interval',
            hours=int(interval_hours)
        )

