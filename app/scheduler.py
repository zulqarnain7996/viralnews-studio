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
            res = post_to_facebook(image_path, caption, title=item.get("title"))
            if res.get("success") and res.get("mode") == "live":
                update_queue_item_status(queue_id, "published", response_log=json.dumps(res))
                log_scheduler("queue_success", f"Queued post #{queue_id} published successfully to Facebook Page.")
            elif res.get("mode") in ["queued", "rate_limited_queued"]:
                next_try = (datetime.now() + timedelta(minutes=45)).isoformat()
                update_queue_item_status(queue_id, "pending", response_log=json.dumps(res), scheduled_for=next_try)
            else:
                update_queue_item_status(queue_id, "failed", response_log=json.dumps(res))
        elif platform == "telegram":
            res = post_to_telegram(image_path, caption, title=item.get("title"))
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
        from app.database import normalize_news_text

        # Fetch fresh news (supports single category or 'all' round-robin)
        if category == "all":
            articles = []
            for sub_cat in ["trending", "war", "pakistan", "world", "tech"]:
                sub_arts = fetch_news_by_category(category=sub_cat, city=local_city, language=language, limit=6)
                articles.extend(sub_arts)
        else:
            articles = fetch_news_by_category(category=category, city=local_city, language=language, limit=25)

        unposted = []
        selected_titles_norm = []

        for art in articles:
            raw_title = art.get("title", "").strip()
            if not raw_title:
                continue

            # Check exhaustive database history and queue
            if is_article_posted(raw_title, article_id=art.get("id"), link=art.get("link")):
                continue

            norm_t = normalize_news_text(raw_title)
            if len(norm_t) < 10:
                continue

            # Batch deduplication: prevent selecting twin stories from different RSS sources
            is_dup_in_batch = False
            words_new = set(norm_t.split())
            for sel_norm in selected_titles_norm:
                words_sel = set(sel_norm.split())
                if words_new and words_sel:
                    intersection = words_new.intersection(words_sel)
                    sim = len(intersection) / min(len(words_new), len(words_sel))
                    if sim > 0.48 or norm_t[:28] == sel_norm[:28]:
                        is_dup_in_batch = True
                        break

            if is_dup_in_batch:
                continue

            unposted.append(art)
            selected_titles_norm.append(norm_t)
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
                fb_res = post_to_facebook(card_res["file_path"], caption, title=art.get("title")) if fb_enabled else {"mode": "disabled"}
                if webhook_enabled:
                    post_to_webhook(card_res["file_path"], caption, art, title=art.get("title"))
                if tg_enabled:
                    post_to_telegram(card_res["file_path"], caption, title=art.get("title"))

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
    Pings the server's own public URL every 8 minutes via the external public URL.
    This goes through Render's edge proxy/load balancer, registering real HTTP traffic
    that resets the 15-minute inactivity sleep timer.
    Also pings /api/settings to keep the full application stack warm.
    """
    import requests
    public_url = get_setting("app_public_url", "https://viralnews-studio.onrender.com").rstrip("/")
    if not public_url or "localhost" in public_url or "127.0.0.1" in public_url:
        public_url = "https://viralnews-studio.onrender.com"

    # Primary: lightweight /health ping
    try:
        ping_url = f"{public_url}/health"
        res = requests.get(ping_url, timeout=20, headers={"User-Agent": "ViralNewsStudio-KeepAlive/1.0"})
        if res.status_code == 200:
            log_scheduler("keep_alive_ping", f"Self-ping to {ping_url} (HTTP {res.status_code}) — Server awake 24/7", "info")
        else:
            log_scheduler("keep_alive_ping", f"Self-ping to {ping_url} returned HTTP {res.status_code}", "warning")
    except Exception as e:
        log_scheduler("keep_alive_ping", f"Primary ping failed: {e}", "warning")

    # Secondary: heavier GET to keep full app stack warm
    try:
        requests.get(f"{public_url}/api/settings", timeout=15, headers={"User-Agent": "ViralNewsStudio-KeepAlive/1.0"})
    except Exception:
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
        # 3. 24/7 Keep-Alive Self-Pinger (runs every 5 minutes to prevent Render sleep)
        scheduler.add_job(
            keep_alive_ping,
            'interval',
            minutes=5,
            id='keep_alive_ping_job',
            replace_existing=True
        )
        scheduler.start()
        print(f"[Scheduler] Started background auto-pilot every {interval_hours}h, queue processor every 5m, and keep-alive pinger every 5m.")

def update_scheduler_interval(interval_hours):
    """Updates the execution interval of the running scheduler."""
    if scheduler.running:
        try:
            hrs = max(1, int(interval_hours))
            scheduler.reschedule_job(
                'autopilot_job',
                trigger='interval',
                hours=hrs
            )
            log_scheduler("reschedule_success", f"Auto-pilot rescheduled to run every {hrs} hour(s).")
        except Exception as e:
            log_scheduler("reschedule_error", f"Failed to reschedule: {e}", "error")

