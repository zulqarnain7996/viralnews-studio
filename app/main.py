import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import init_db
from app.scheduler import init_scheduler
from app.routes.api_news import router as news_router
from app.routes.api_cards import router as cards_router
from app.routes.api_social import router as social_router
from app.routes.api_settings import router as settings_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
GENERATED_DIR = os.path.join(BASE_DIR, "data", "generated_cards")
UPLOADS_DIR = os.path.join(BASE_DIR, "data", "uploads")

# Ensure required directories exist
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database and Scheduler
    print("[ViralNews Studio] Starting application...")
    init_db()
    init_scheduler()
    yield
    print("[ViralNews Studio] Shutting down application...")

app = FastAPI(
    title="ViralNews Studio - AI & Social News Automator",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith((".js", ".css", ".html")) or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount static folders
app.mount("/static/generated", StaticFiles(directory=GENERATED_DIR), name="generated_cards")
app.mount("/static/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Jinja2 Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Register API routers
app.include_router(news_router)
app.include_router(cards_router)
app.include_router(social_router)
app.include_router(settings_router)

from fastapi.responses import FileResponse

@app.get("/")
def home(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html", context={"request": request})
    except Exception:
        index_path = os.path.join(TEMPLATES_DIR, "index.html")
        return FileResponse(index_path)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ViralNews Studio"}
