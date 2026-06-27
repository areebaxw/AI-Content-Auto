# 🚀 AI Content Automation System

**Transform one blog post into platform-ready content for Twitter, LinkedIn, Telegram, Email, and Instagram — automatically.**

A fully-functional Flask application that generates, edits, schedules, and distributes multi-platform content in seconds. No expensive APIs. No manual posting. One click to everywhere.

---

## ✨ What It Does

1. **Paste or upload a blog post** (500–2000 words)
2. **AI generates variations** for each platform:
   - 5 unique Twitter posts (280 chars)
   - 2 professional LinkedIn posts
   - 3 casual Telegram messages
   - 1 Email (subject + body)
   - 1 Instagram caption with hashtags
3. **Edit** any generated post before publishing
4. **Schedule** for future dates/times
5. **Post immediately** or wait for scheduled time
6. **Track campaigns** and engagement in dashboard

---

## 🎯 Key Features

✅ **Offline AI generation** — Uses local Ollama or HuggingFace (no cloud costs)  
✅ **Multi-platform distribution** — Twitter, LinkedIn, Telegram, Email, Instagram  
✅ **Edit before posting** — Full control over each variation  
✅ **Smart scheduling** — Post when your audience is most active  
✅ **Campaign history** — Keep track of all posts and performance  
✅ **Portfolio-ready** — Clean code, proper error handling, real APIs  
✅ **100% free tier** — All integrations work on free plans  
✅ **n8n integration** — Ready-to-use workflow automation  

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.9+, Flask |
| **AI/ML** | Ollama (mistral) or HuggingFace Transformers |
| **Database** | SQLite |
| **Job Scheduler** | APScheduler |
| **APIs** | Tweepy (Twitter), python-telegram-bot (Telegram), SMTP (Email) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Workflow** | n8n (optional, for webhooks) |
| **Tunneling** | ngrok (for local testing with n8n cloud) |

---

## 📁 Project Structure

```
ai-content-automation/
├── backend/
│   ├── main.py                 # Flask app entry point
│   ├── ai_handler.py           # AI content generation
│   ├── api_handlers.py         # Platform integrations (Twitter, Telegram, Email)
│   ├── database.py             # SQLite operations
│   ├── config.py               # Configuration & environment variables
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── templates/
│   │   ├── index.html          # Main upload & generation page
│   │   ├── dashboard.html      # Campaign history
│   │   └── schedule.html       # Scheduling interface
│   └── static/
│       ├── style.css           # Styling
│       └── script.js           # Frontend logic
├── n8n_workflows/
│   └── content_distribution_workflow.json
├── .env.example                # Environment template
├── docker-compose.yml          # Optional Docker setup
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Git
- (Optional) Docker & Docker Compose

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/yourusername/ai-content-automation.git
cd ai-content-automation
```

**2. Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
```

**3. Install dependencies:**
```bash
pip install -r backend/requirements.txt
```

**4. Set up environment variables:**
```bash
copy .env.example .env            # On Linux/Mac: cp .env.example .env
```

**5. Configure `.env` file:**

Open `.env` and fill in (at minimum):
```bash
# AI Model (choose one)
OLLAMA_URL=http://localhost:11434
# OR
USE_HUGGINGFACE=true

# Twitter (optional, for live posting)
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here
TWITTER_ACCESS_TOKEN=your_token_here
TWITTER_ACCESS_SECRET=your_token_secret_here

# Telegram (optional, for live posting)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here

# Email (optional, for live sending)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_RECIPIENT=recipient@example.com

# Database
DATABASE_URL=sqlite:///content_automation.db
```

**6. Start AI model (if using Ollama):**

Download and run Ollama:
```bash
ollama serve
# In another terminal:
ollama pull mistral
```

**7. Run Flask app:**
```bash
python backend/main.py
```

Visit: **http://localhost:5000**

---

## 📖 Usage

### Generate Content

1. Open http://localhost:5000
2. Paste your blog post in the textarea
3. Click **"Generate Posts"**
4. AI creates 12 variations (5 Twitter, 2 LinkedIn, 3 Telegram, 1 Email, 1 Instagram)
5. Each variation appears organized by platform

### Edit & Schedule

1. Click any post to edit
2. Make changes and save
3. Click **"Schedule"** to pick a date/time
4. Or click **"Post Now"** to publish immediately

### View History

1. Click **"Dashboard"** tab
2. See all campaigns with their status:
   - **Draft** — Not yet posted
   - **Scheduled** — Waiting for scheduled time
   - **Posted** — Live on platform
   - **Failed** — Post attempt failed

---

## 🔌 API Endpoints

All requests expect `Content-Type: application/json`

### `POST /api/generate`
Generate post variations from blog content.

**Request:**
```json
{
  "content": "Your blog post text here...",
  "title": "Blog Post Title"
}
```

**Response:**
```json
{
  "campaign_id": 1,
  "posts": {
    "twitter": ["Post 1", "Post 2", ...],
    "linkedin": ["Post 1", "Post 2"],
    "telegram": ["Message 1", ...],
    "email": {"subject": "...", "body": "..."},
    "instagram": ["Caption with #hashtags"]
  }
}
```

### `POST /api/post-now`
Post immediately to a platform.

**Request:**
```json
{
  "platform": "twitter",
  "content": "The post text",
  "post_id": 1
}
```

**Response:**
```json
{
  "status": "posted",
  "url": "https://twitter.com/username/status/123456789",
  "platform": "twitter"
}
```

### `POST /api/schedule`
Schedule a post for later.

**Request:**
```json
{
  "post_id": 1,
  "platform": "linkedin",
  "scheduled_time": "2026-06-28 10:00:00"
}
```

**Response:**
```json
{
  "status": "scheduled",
  "scheduled_time": "2026-06-28 10:00:00"
}
```

### `GET /api/history`
Retrieve all campaigns and their posts.

**Response:**
```json
{
  "campaigns": [
    {
      "id": 1,
      "title": "Blog Post Title",
      "created_at": "2026-06-27 10:15:00",
      "posts": [...],
      "total_posts": 12
    }
  ]
}
```

---

## 🔐 Environment Variables Reference

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `OLLAMA_URL` | No | `http://localhost:11434` | For local Ollama AI |
| `USE_HUGGINGFACE` | No | `true` | Use HF instead of Ollama |
| `TWITTER_API_KEY` | No | `abc123xyz` | For Twitter posting |
| `TWITTER_API_SECRET` | No | `xyz789abc` | For Twitter posting |
| `TWITTER_ACCESS_TOKEN` | No | `token123` | For Twitter posting |
| `TWITTER_ACCESS_SECRET` | No | `secret456` | For Twitter posting |
| `TELEGRAM_BOT_TOKEN` | No | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` | For Telegram posting |
| `TELEGRAM_CHANNEL_ID` | No | `-1001234567890` | Target Telegram channel |
| `EMAIL_USER` | No | `your@gmail.com` | Gmail SMTP sender |
| `EMAIL_PASSWORD` | No | `app-password-here` | Gmail app password |
| `EMAIL_RECIPIENT` | No | `recipient@email.com` | Email recipient |
| `DATABASE_URL` | No | `sqlite:///content_automation.db` | Local SQLite path |

---

## 🔗 Platform Setup Guides

### Twitter API
1. Go to https://developer.twitter.com/
2. Create a new app
3. Go to "Keys and tokens"
4. Copy API Key, API Secret, Access Token, Access Token Secret
5. Add to `.env` file

### Telegram Bot
1. Open Telegram app
2. Search for **@BotFather**
3. Send `/newbot`
4. Follow prompts (name your bot)
5. Copy the Bot Token
6. Create a channel and add the bot as admin
7. Copy your channel ID (starts with `-100`)
8. Add to `.env` file

### Gmail SMTP
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Google generates an app password (16 characters)
4. Copy this password (NOT your regular Gmail password)
5. Add to `.env` file


## 📦 Deployment Options

### Local Development
```bash
python backend/main.py
```

### Docker (with docker-compose)
```bash
docker-compose up --build
```

### Cloud Deployment (Railway, Render, Heroku)
1. Push to GitHub
2. Connect repository to deployment platform
3. Set environment variables in dashboard
4. Deploy
5. Share the live URL for portfolio/client demos

---

## 🧪 Testing

### Manual Test (with curl/PowerShell)

**Windows PowerShell:**
```powershell
$body = @{
    content = "Python is great for AI and machine learning. Start learning today."
    title = "Python Tips"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/generate" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -UseBasicParsing
```

**Linux/Mac (curl):**
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"content":"Test blog post","title":"Test"}'
```

### Expected Response
```json
{
  "campaign_id": 1,
  "generated_posts": [
    {
      "platform": "twitter",
      "generated_content": "Your AI-generated post...",
      "status": "draft"
    },
    ...
  ]
}
```

---

## 🔄 n8n Workflow Integration

A pre-configured n8n workflow is included in `n8n_workflows/content_distribution_workflow.json`

**To use:**
1. Open n8n cloud (or self-hosted n8n)
2. Create new workflow
3. Import JSON from `n8n_workflows/`
4. Configure webhook trigger
5. Add your Flask backend URL
6. Activate workflow
7. Send POST requests to webhook to trigger automated posting

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Content is required" error in n8n** | Ensure body parameters are set correctly: `content: $json.content`, `title: $json.title` |
| **Ollama connection refused** | Make sure `ollama serve` is running in another terminal |
| **Posts not posting to Twitter** | Check API keys in `.env`, ensure Twitter account has API access |
| **"Bad gateway" from ngrok** | Flask app stopped. Run `python backend/main.py` again |
| **Database locked error** | Close other connections to SQLite; restart Flask |

---

## 📚 Architecture Diagram

```
┌─────────────────────────┐
│   User Interface        │
│  (HTML/JS Frontend)     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   Flask Backend         │
│  (API Endpoints)        │
└──────────┬──────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐   ┌──────────┐
│ Ollama │   │ Database │
│ (AI)   │   │ (SQLite) │
└────────┘   └──────────┘
    │
    └──────────┬──────────────┐
               │              │
        ┌──────▼─────┐  ┌────▼─────┐
        │ Platforms  │  │Scheduler  │
        │ (Twitter,  │  │(APSched)  │
        │  Telegram) │  └──────────┘
        └────────────┘
```

---

## 📈 Performance & Scaling

- **Generation time:** 2-5 seconds per blog post (depends on Ollama/HF model)
- **Database:** SQLite handles up to ~100,000 posts efficiently
- **Concurrent users:** 5-10 with Flask dev server; scale with gunicorn/uWSGI
- **Storage:** ~50MB per 1000 campaigns (including content)

For production:
- Use PostgreSQL instead of SQLite
- Deploy with gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 backend.main:app`
- Add caching layer (Redis)
- Use RQ or Celery for background jobs

---

Version: 1.0.0 | Last updated: June 27, 2026