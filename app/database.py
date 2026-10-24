import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                category TEXT,
                source TEXT,
                title TEXT,
                summary TEXT,
                link TEXT UNIQUE,
                image_url TEXT,
                published_at TEXT,
                fetched_at TEXT,
                status TEXT DEFAULT 'new'
            )
        """)
        
        # Post Queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT,
                title TEXT,
                summary TEXT,
                caption TEXT,
                card_image_path TEXT,
                platform TEXT,
                scheduled_for TEXT,
                status TEXT DEFAULT 'pending',
                response_log TEXT,
                created_at TEXT
            )
        """)
        
        # Post History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                platform TEXT,
                card_image_path TEXT,
                caption TEXT,
                post_id_or_url TEXT,
                status TEXT,
                error_message TEXT,
                published_at TEXT
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Auto-pilot log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                message TEXT,
                status TEXT,
                created_at TEXT
            )
        """)
        
        conn.commit()
        
        # Set default settings if not exists
        default_settings = {
            "page_name": "PAK NEWS 24/7",
            "page_handle": "@PakNewsOfficial",
            "local_city": "Lahore",
            "language": "english",
            "default_theme": "breaking_red",
            "default_aspect_ratio": "1:1",
            "autopilot_enabled": "false",
            "autopilot_interval_hours": "4",
            "autopilot_category": "trending",
            "autopilot_max_posts": "2",
            "fb_page_id": "",
            "fb_access_token": "",
            "webhook_url": "",
            "telegram_bot_token": "",
            "telegram_channel_id": "",
            "simulation_mode": "false",
            "watermark_text": "NEWS DESK",
            "post_interval_minutes": "45",
            "meta_rate_limit_cooldown_until": "",
            "meta_last_app_usage": "{}",
            "meta_last_call_count": "0",
            "meta_consecutive_rate_limits": "0"
        }
        
        for k, v in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        conn.commit()

def get_setting(key, default=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def get_all_settings():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}

def update_settings(settings_dict):
    with get_connection() as conn:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
        conn.commit()

def save_article(article):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO articles 
            (id, category, source, title, summary, link, image_url, published_at, fetched_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article.get("id"),
            article.get("category"),
            article.get("source"),
            article.get("title"),
            article.get("summary"),
            article.get("link"),
            article.get("image_url", ""),
            article.get("published_at", ""),
            datetime.now().isoformat(),
            article.get("status", "new")
        ))
        conn.commit()

def save_articles_batch(articles):
    with get_connection() as conn:
        cursor = conn.cursor()
        for a in articles:
            cursor.execute("""
                INSERT OR IGNORE INTO articles 
                (id, category, source, title, summary, link, image_url, published_at, fetched_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                a.get("id"),
                a.get("category"),
                a.get("source"),
                a.get("title"),
                a.get("summary"),
                a.get("link"),
                a.get("image_url", ""),
                a.get("published_at", ""),
                datetime.now().isoformat(),
                "new"
            ))
        conn.commit()

def get_articles(category=None, search=None, limit=50, offset=0):
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if category and category.lower() != "all":
            query += " AND category = ?"
            params.append(category.lower())
            
        if search:
            query += " AND (title LIKE ? OR summary LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
            
        query += " ORDER BY fetched_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_article_by_id(article_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_to_queue(item):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO post_queue 
            (article_id, title, summary, caption, card_image_path, platform, scheduled_for, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("article_id"),
            item.get("title"),
            item.get("summary"),
            item.get("caption"),
            item.get("card_image_path"),
            item.get("platform", "facebook"),
            item.get("scheduled_for", datetime.now().isoformat()),
            item.get("status", "pending"),
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid

def get_queue(status=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM post_queue WHERE status = ? ORDER BY id DESC", (status,))
        else:
            cursor.execute("SELECT * FROM post_queue ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]

def get_next_queue_item():
    """Fetches the oldest pending item that is ready to be published."""
    now_str = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM post_queue 
            WHERE status = 'pending' AND (scheduled_for IS NULL OR scheduled_for <= ?)
            ORDER BY id ASC LIMIT 1
        """, (now_str,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_queue_item_status(queue_id, status, response_log=None, scheduled_for=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if scheduled_for:
            cursor.execute("""
                UPDATE post_queue 
                SET status = ?, response_log = ?, scheduled_for = ?
                WHERE id = ?
            """, (status, response_log, scheduled_for, queue_id))
        else:
            cursor.execute("""
                UPDATE post_queue 
                SET status = ?, response_log = ?
                WHERE id = ?
            """, (status, response_log, queue_id))
        conn.commit()

def delete_queue_item(queue_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM post_queue WHERE id = ?", (queue_id,))
        conn.commit()

def get_queue_stats():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM post_queue
        """)
        row = cursor.fetchone()
        return {
            "total": row["total"] or 0,
            "pending": row["pending"] or 0,
            "published": row["published"] or 0,
            "failed": row["failed"] or 0
        }


def log_post(title, platform, card_image_path, caption, post_id_or_url, status="success", error_message=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO post_history 
            (title, platform, card_image_path, caption, post_id_or_url, status, error_message, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, platform, card_image_path, caption, post_id_or_url, status, error_message, datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid

def get_history(limit=50):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM post_history ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

def log_scheduler(action, message, status="info"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scheduler_logs (action, message, status, created_at)
            VALUES (?, ?, ?, ?)
        """, (action, message, status, datetime.now().isoformat()))
        conn.commit()

def get_scheduler_logs(limit=30):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scheduler_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

def is_article_posted(link_or_title):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM post_history WHERE title = ?", (link_or_title,))
        row = cursor.fetchone()
        return (row["count"] > 0)
