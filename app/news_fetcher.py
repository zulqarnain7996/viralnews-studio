import hashlib
import re
import html
import urllib.parse
from datetime import datetime
import concurrent.futures
import feedparser
import requests
from bs4 import BeautifulSoup
from app.database import save_articles_batch, get_setting

# Curated topic-specific editorial backdrops from high-resolution news archives
TOPIC_BACKDROPS = {
    "military": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1080&auto=format&fit=crop&q=80",  # Security vehicle
        "https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=1080&auto=format&fit=crop&q=80",  # Defense forces aircraft
        "https://images.unsplash.com/photo-1590247813693-5541d1c609fd?w=1080&auto=format&fit=crop&q=80",  # Defense command
    ],
    "politics": [
        "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=1080&auto=format&fit=crop&q=80",  # Parliament & dome
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1080&auto=format&fit=crop&q=80",  # Press conference podium
        "https://images.unsplash.com/photo-1575320181282-9afab399332c?w=1080&auto=format&fit=crop&q=80",  # Government cabinet table
    ],
    "court": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&auto=format&fit=crop&q=80",  # Scales of justice & law
        "https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=1080&auto=format&fit=crop&q=80",  # Courtroom gavel
    ],
    "sports": [
        "https://images.unsplash.com/photo-1531415074868-83633dd5e45c?w=1080&auto=format&fit=crop&q=80",  # Cricket stadium under lights
        "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=1080&auto=format&fit=crop&q=80",  # Sports turf & pitch
    ],
    "economy": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080&auto=format&fit=crop&q=80",  # Financial charts
        "https://images.unsplash.com/photo-1610375461246-83df859d849d?w=1080&auto=format&fit=crop&q=80",  # Gold bullion bars
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=1080&auto=format&fit=crop&q=80",  # Currency & money
    ],
    "aviation": [
        "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1080&auto=format&fit=crop&q=80",  # Passenger aircraft
        "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=1080&auto=format&fit=crop&q=80",  # Airport tarmac
    ],
    "disaster": [
        "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?w=1080&auto=format&fit=crop&q=80",  # Heavy storm / weather
        "https://images.unsplash.com/photo-1547683905-f686c993aae5?w=1080&auto=format&fit=crop&q=80",  # Emergency rescue
    ],
    "world": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&auto=format&fit=crop&q=80",  # World satellite / globe
        "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=1080&auto=format&fit=crop&q=80",  # International summit
    ],
    "pakistan": [
        "https://images.unsplash.com/photo-1588691090382-747209ee6e06?w=1080&auto=format&fit=crop&q=80",  # Minar-e-Pakistan / Lahore
        "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?w=1080&auto=format&fit=crop&q=80",  # City skyline
    ],
    "breaking": [
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1080&auto=format&fit=crop&q=80",  # News studio / press
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=1080&auto=format&fit=crop&q=80",  # Daily news desk
    ]
}

DIVERSE_BACKDROPS = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1588691090382-747209ee6e06?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1531415074868-83633dd5e45c?w=1080&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=1080&auto=format&fit=crop&q=80"
]

CITY_URDU_MAP = {
    "lahore": "لاہور",
    "karachi": "کراچی",
    "islamabad": "اسلام آباد",
    "rawalpindi": "راولپنڈی",
    "peshawar": "پشاور",
    "quetta": "کوئٹہ",
    "multan": "ملتان",
    "faisalabad": "فیصل آباد",
    "sialkot": "سیالکوٹ",
    "gujranwala": "گوجرانوالہ"
}

def clean_html(raw_html):
    if not raw_html:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    # Unescape HTML entities like &nbsp;, &amp;, &quot;, &#39;
    clean = html.unescape(clean)
    clean = clean.replace('\xa0', ' ')
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

def extract_source_and_title(title):
    source = "News Desk"
    clean_title = clean_html(title)
    if " - " in clean_title:
        parts = clean_title.rsplit(" - ", 1)
        clean_title = parts[0].strip()
        source = parts[1].strip()
    elif " | " in clean_title:
        parts = clean_title.rsplit(" | ", 1)
        clean_title = parts[0].strip()
        source = parts[1].strip()
    return clean_title, source

def get_hash_id(link_or_title):
    return hashlib.md5(link_or_title.encode('utf-8')).hexdigest()[:12]

def is_urdu_text(text):
    if not text:
        return False
    # Arabic / Urdu Unicode block: \u0600-\u06FF
    return bool(re.search(r'[\u0600-\u06FF]', text))

def _upgrade_image_url(url: str) -> str:
    if not url:
        return url
    # Express News: remove thumbnail dimensions (-600x450, -300x200) to get original uncompressed photo
    if "img.express.pk" in url:
        url = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', url)
    # BBC News: upgrade 240px to 1024px high-res
    if "ichef.bbci.co.uk" in url and "/240/" in url:
        url = url.replace("/240/", "/1024/")
    return url

def get_direct_image(entry):
    """Checks RSS entry for direct image URLs, thumbnails, and enclosures."""
    # 1. media_content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if isinstance(media, dict) and 'url' in media and media['url'].startswith('http'):
                return _upgrade_image_url(media['url'])

    # 2. media_thumbnail (BBC and others)
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if isinstance(media, dict) and 'url' in media and media['url'].startswith('http'):
                return _upgrade_image_url(media['url'])

    # 3. enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if isinstance(enc, dict) and 'href' in enc and enc['href'].startswith('http'):
                return _upgrade_image_url(enc['href'])

    # 4. Summary <img> tag
    raw_summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
    if '<img' in raw_summary:
        match = re.search(r'<img[^>]+src=["\'](http[^"\']+)["\']', raw_summary)
        if match:
            return _upgrade_image_url(match.group(1))

    return None

def scrape_og_image_from_link(link, timeout=3.0):
    """
    Scrapes the publisher's official news image from the article web page (<meta property='og:image'>).
    """
    if not link or not link.startswith("http"):
        return None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(link, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og and og.get("content") and og["content"].startswith("http"):
                return _upgrade_image_url(og["content"])
            tw = soup.find("meta", attrs={"name": "twitter:image"}) or soup.find("meta", property="twitter:image")
            if tw and tw.get("content") and tw["content"].startswith("http"):
                return _upgrade_image_url(tw["content"])
    except Exception:
        pass
    return None

def get_fallback_backdrop(title_str, raw_summary, category):
    """Keyword-based realistic fallback backdrop when no editorial photo is available."""
    text = (title_str + " " + raw_summary).lower()

    if any(k in text for k in ['عاصم منیر', 'فوج', 'آرمی', 'دہشت گرد', 'سکیورٹی', 'پولیس', 'رینجرز', 'ہتھیار', 'آپریشن', 'حملہ', 'شہید', 'کور کمانڈر', 'army', 'military', 'security', 'police', 'terror', 'forces', 'attack', 'defense', 'clash', 'یوکرین', 'فوجی امداد']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["military"])
        return TOPIC_BACKDROPS["military"][idx]

    if any(k in text for k in ['وزیر اعظم', 'شہباز شریف', 'نواز شریف', 'عمران خان', 'پی ٹی آئی', 'ن لیگ', 'پارلیمنٹ', 'قومی اسمبلی', 'سینیٹ', 'کابینہ', 'الیکشن', 'حکومت', 'سیاست', 'صدر', 'pm', 'prime minister', 'parliament', 'assembly', 'pti', 'pmln', 'politics', 'government', 'cabinet', 'senate']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["politics"])
        return TOPIC_BACKDROPS["politics"][idx]

    if any(k in text for k in ['عدالت', 'سپریم کورٹ', 'ہائی کورٹ', 'جج', 'چیف جسٹس', 'سماعت', 'درخواست', 'ضمانت', 'قانون', 'وکلا', 'court', 'judge', 'justice', 'bail', 'lawyer', 'judiciary', 'verdict', 'case']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["court"])
        return TOPIC_BACKDROPS["court"][idx]

    if any(k in text for k in ['کرکٹ', 'میچ', 'پی ایس ایل', 'بابر اعظم', 'شاہین', 'ٹیم', 'اسٹیڈیم', 'ورلڈ کپ', 'cricket', 'psl', 'pcb', 'babar', 'match', 'sports', 'football', 'hockey']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["sports"])
        return TOPIC_BACKDROPS["sports"][idx]

    if any(k in text for k in ['روپیہ', 'ڈالر', 'سونا', 'مہنگائی', 'معیشت', 'اسٹاک مارکیٹ', 'بجٹ', 'بینک', 'آئی ایم ایف', 'قیمت', 'پٹرول', 'تیل', 'سٹیٹ بینک', 'economy', 'rupee', 'dollar', 'gold', 'inflation', 'stock', 'imf', 'petrol', 'currency', 'oil']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["economy"])
        return TOPIC_BACKDROPS["economy"][idx]

    if any(k in text for k in ['پرواز', 'طیارہ', 'ایئرپورٹ', 'مسافر', 'پی آئی اے', 'سعودی عرب جانے والی', 'flight', 'plane', 'airport', 'airline', 'pia', 'aviation']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["aviation"])
        return TOPIC_BACKDROPS["aviation"][idx]

    if any(k in text for k in ['زلزلہ', 'سیلاب', 'بارش', 'موسم', 'طوفان', 'جھٹکے', 'شدت', 'earthquake', 'flood', 'rain', 'storm', 'weather', 'tremor']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["disaster"])
        return TOPIC_BACKDROPS["disaster"][idx]

    if any(k in text for k in ['امریکہ', 'ایران', 'اسرائیل', 'غزہ', 'فلسطین', 'سعودی', 'حوثی', 'چین', 'بھارت', 'مشرق وسطیٰ', 'اقوام متحدہ', 'world', 'gaza', 'palestine', 'iran', 'us', 'usa', 'saudi', 'un', 'china', 'india', 'middle east']):
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS["world"])
        return TOPIC_BACKDROPS["world"][idx]

    if category in TOPIC_BACKDROPS:
        idx = abs(hash(title_str)) % len(TOPIC_BACKDROPS[category])
        return TOPIC_BACKDROPS[category][idx]

    idx = abs(hash(title_str)) % len(DIVERSE_BACKDROPS)
    return DIVERSE_BACKDROPS[idx]

def fetch_feed(feed_url, category="trending", source_override=None, limit=25):
    articles = []
    try:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:limit]:
            title = getattr(entry, 'title', '').strip()
            if not title:
                continue

            clean_title, source = extract_source_and_title(title)
            if source_override:
                source = source_override

            link = getattr(entry, 'link', '')
            summary_raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            summary = clean_html(summary_raw)

            if len(summary) > 280:
                summary = summary[:277] + "..."
            elif not summary:
                summary = clean_title

            published_at = getattr(entry, 'published', '') or datetime.now().strftime("%Y-%m-%d %H:%M")
            direct_img = get_direct_image(entry)

            art_id = get_hash_id(link or title)
            is_urdu = is_urdu_text(clean_title)

            articles.append({
                "id": art_id,
                "category": category,
                "source": source,
                "title": clean_title,
                "summary": summary,
                "link": link,
                "image_url": direct_img,  # will resolve via og:image if None
                "published_at": published_at,
                "language": "urdu" if is_urdu else "english",
                "status": "new"
            })

        # Resolve real editorial images from web links concurrently
        needs_scrape = [a for a in articles if not a["image_url"] and a.get("link")]
        if needs_scrape:
            def resolve_article_image(art):
                scraped = scrape_og_image_from_link(art["link"])
                if scraped:
                    art["image_url"] = scraped
                else:
                    art["image_url"] = get_fallback_backdrop(art["title"], art["summary"], art["category"])
                return art

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                list(executor.map(resolve_article_image, needs_scrape))

        # Ensure all articles have an image
        for a in articles:
            if not a.get("image_url"):
                a["image_url"] = get_fallback_backdrop(a["title"], a["summary"], a["category"])

    except Exception as e:
        print(f"Error fetching feed {feed_url}: {e}")
    return articles

def fetch_news_by_category(category="trending", city=None, query=None, language="english", limit=30):
    """
    Fetches categorized news:
    - language: 'english' or 'urdu'
    - local, pakistan, world, trending, or search query
    """
    all_articles = []
    city = city or get_setting("local_city", "Lahore")
    city_lower = city.lower().strip()
    city_urdu = CITY_URDU_MAP.get(city_lower, city)
    
    if query:
        encoded_q = urllib.parse.quote(query)
        lang_param = "ur" if language == "urdu" else "en"
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang_param}-PK&gl=PK&ceid=PK:{lang_param}"
        all_articles.extend(fetch_feed(url, category="search", limit=limit))
    elif language == "urdu":
        # URDU NEWS FEEDS
        if category == "local":
            q = urllib.parse.quote(f"{city_urdu} خبریں")
            url = f"https://news.google.com/rss/search?q={q}&hl=ur&gl=PK&ceid=PK:ur"
            all_articles.extend(fetch_feed(url, category="local", limit=limit))
        elif category == "pakistan":
            all_articles.extend(fetch_feed("https://feeds.bbci.co.uk/urdu/rss.xml", category="pakistan", source_override="BBC Urdu", limit=15))
            all_articles.extend(fetch_feed("https://www.express.pk/feed/", category="pakistan", source_override="Daily Express", limit=15))
            all_articles.extend(fetch_feed("https://urdu.arynews.tv/feed/", category="pakistan", source_override="ARY News", limit=10))
        elif category == "world":
            all_articles.extend(fetch_feed("https://feeds.bbci.co.uk/urdu/world/rss.xml", category="world", source_override="BBC Urdu", limit=15))
            all_articles.extend(fetch_feed("https://news.google.com/rss/headlines/section/topic/WORLD?hl=ur&gl=PK&ceid=PK:ur", category="world", limit=15))
        else: # trending urdu
            all_articles.extend(fetch_feed("https://www.express.pk/feed/", category="trending", source_override="Express News", limit=15))
            all_articles.extend(fetch_feed("https://feeds.bbci.co.uk/urdu/rss.xml", category="trending", source_override="BBC Urdu", limit=15))
            all_articles.extend(fetch_feed("https://news.google.com/rss?hl=ur&gl=PK&ceid=PK:ur", category="trending", limit=10))
    else:
        # ENGLISH NEWS FEEDS
        if category == "local":
            city_query = f"{city} News Pakistan"
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(city_query)}&hl=en-PK&gl=PK&ceid=PK:en"
            all_articles.extend(fetch_feed(url, category="local", limit=limit))
        elif category == "pakistan":
            url1 = "https://news.google.com/rss/headlines/section/topic/NATION?hl=en-PK&gl=PK&ceid=PK:en"
            all_articles.extend(fetch_feed(url1, category="pakistan", limit=15))
            url2 = "https://www.dawn.com/feeds/home/"
            all_articles.extend(fetch_feed(url2, category="pakistan", source_override="Dawn", limit=15))
        elif category == "world":
            url = "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-PK&gl=PK&ceid=PK:en"
            all_articles.extend(fetch_feed(url, category="world", limit=limit))
        else: # trending
            url1 = "https://news.google.com/rss?hl=en-PK&gl=PK&ceid=PK:en"
            all_articles.extend(fetch_feed(url1, category="trending", limit=20))
            url2 = "https://tribune.com.pk/feed/latest"
            all_articles.extend(fetch_feed(url2, category="trending", source_override="Express Tribune", limit=10))

    # Deduplicate by title
    seen_titles = set()
    unique_articles = []
    for art in all_articles:
        norm_title = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF]', '', art['title'].lower())[:40]
        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            unique_articles.append(art)
            
    # Save to database cache
    save_articles_batch(unique_articles)
    return unique_articles[:limit]
