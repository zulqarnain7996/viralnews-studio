# 📰 ViralNews Studio - AI & Social Media News Automator

A full-stack, broadcast-grade news aggregation and social media automation application designed for viral news pages (Facebook, TikTok, Instagram, Reels).

---

## ✨ Key Features

1. **Multi-Source News Aggregator**:
   - **🔥 Trending News**: Hot viral stories, top breaking headlines.
   - **🇵🇰 Pakistan News**: National politics, economy, cricket, courts, and current affairs (Google News PK, Dawn News, The Express Tribune, etc.).
   - **📍 Local News**: City-specific news targeting (Lahore, Karachi, Islamabad, Rawalpindi, Peshawar, Quetta, Multan, Faisalabad, etc. with instant city switcher).
   - **🌍 World News**: Global breaking headlines, international affairs, Middle East, technology, and sports.
   - **🔍 Keyword Search**: Real-time topic search for any custom query.

2. **Bulk Selection & Batch Processing**:
   - Checkboxes on every news item with **Select All**, **Select Top 5**, and clear actions.
   - **⚡ Bulk Generate News Graphics**: Render broadcast-quality news graphics for multiple articles in 1 click.
   - **📦 Bulk ZIP Export**: Download all generated cards in a single ZIP file.
   - **🚀 Bulk Social Publish**: Publish selected articles to your Facebook Page and Webhook in batch.

3. **Facebook & TikTok News Page Style Graphic Generator**:
   - **Aspect Ratios**:
     - `1:1 Square (1080x1080)`: Facebook & Instagram feed standard.
     - `9:16 Vertical (1080x1920)`: TikTok, Facebook Reels, Instagram Stories.
   - **Broadcast Themes**:
     - 🔴 **Breaking Red** (High-impact crimson banner with gold accents)
     - ⬛ **Dark Cyber** (Modern noir glassmorphism with neon cyan accents)
     - 🟦 **Royal Blue** (Professional TV news anchor style)
     - 🇵🇰 **Pakistan Emerald** (National green & white flag theme)
   - **Customizable Elements**:
     - Custom Page Name Branding & verified LIVE indicator.
     - Dynamic Category Badges (🔴 BREAKING NEWS, 🇵🇰 PAKISTAN UPDATE, 📍 LOCAL REPORT, etc.).
     - Large bold headline with automatic text wrapping & contrast drop shadow.
     - Story details / bullet points backing card.
     - Source attribution & custom page handle watermark (`Follow @YourHandle`).
     - Real-time live HTML5 Canvas editor (edit text, font size, upload custom photos, or use article image).

4. **Automated Social Media Posting & Auto-Pilot**:
   - **Facebook Page (Meta Graph API)**: Post photo with caption directly to your Facebook Page.
   - **TikTok / Instagram (Webhook Dispatcher)**: Pushes structured payloads with image & captions to Zapier, Make.com, n8n, or Discord webhooks.
   - **Viral Caption & Hashtag Generator**: Automatically writes high-engagement captions with bullets, source credit, and trending hashtags (`#PakistanNews #BreakingNews #UrduNews`).
   - **Daily Auto-Pilot Worker (APScheduler)**:
     - Configurable frequency (Every 1h, 2h, 4h, 6h, 12h, or daily).
     - Target category preference.
     - Deduplication system: remembers previously posted articles and never posts duplicate news!
     - 1-click **"Run Auto-Pilot Now"** manual test button.
   - **Safe Simulation Mode**: Test all posting functions safely without needing live tokens right away.

---

## 🚀 How to Run

### Method 1: 1-Click Launcher (Windows)
Double-click `run.bat` in the project folder.

### Method 2: Python Command Line
```powershell
python run.py
```
The server will start on `http://127.0.0.1:8000` and automatically open your web browser.

---

## ⚙️ Configuration & Social Media Setup

Open the **Settings** tab in the app:
1. **Facebook Page Integration**:
   - Enter your **Facebook Page ID** and **Page Access Token**.
   - Turn off **Simulation Mode** when ready for live publishing.
2. **TikTok / Multi-Platform Webhook**:
   - Paste your webhook URL from **Zapier**, **Make.com**, **n8n**, or **Discord**.
   - Your webhook receives the image file, title, and formatted viral caption.
3. **Branding**:
   - Set your default **Page Name** (e.g. `PAK NEWS 24/7`) and **Handle** (e.g. `@PakNewsOfficial`).
   - Set your preferred default city for local news.
