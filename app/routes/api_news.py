from fastapi import APIRouter, Query
from app.news_fetcher import fetch_news_by_category
from app.database import get_articles, get_article_by_id, get_setting

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("")
def list_news(
    category: str = Query("trending", description="Category: local, pakistan, world, trending, or all"),
    city: str = Query(None, description="City for local news (e.g. Lahore, Karachi, Islamabad)"),
    query: str = Query(None, description="Search keyword"),
    language: str = Query("english", description="Language: english or urdu"),
    refresh: bool = Query(False, description="Force refresh from live RSS sources"),
    limit: int = Query(30, ge=1, le=100)
):
    city = city or get_setting("local_city", "Lahore")
    
    # If explicit refresh or search query: always fetch live
    if refresh or query:
        articles = fetch_news_by_category(category=category, city=city, query=query, language=language, limit=limit)
        return {
            "success": True,
            "count": len(articles),
            "category": category,
            "city": city,
            "language": language,
            "articles": articles
        }
    
    # Otherwise try cached from database first for instant loading (matching both category and language)
    cached = get_articles(category=category, language=language, search=query, limit=limit)
    if not cached or len(cached) < 4:
        articles = fetch_news_by_category(category=category, city=city, query=query, language=language, limit=limit)
    else:
        articles = cached
        
    return {
        "success": True,
        "count": len(articles),
        "category": category,
        "city": city,
        "language": language,
        "articles": articles
    }

@router.get("/{article_id}")
def get_single_article(article_id: str):
    art = get_article_by_id(article_id)
    if not art:
        return {"success": False, "error": "Article not found"}
    return {"success": True, "article": art}
