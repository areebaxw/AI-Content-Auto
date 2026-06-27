# AI Content Automation System

A portfolio-ready Flask application that turns one long-form blog post into platform-specific content for Twitter, LinkedIn, Telegram, Email, and Instagram, then stores, edits, schedules, and distributes it through a local SQLite workflow.

## What It Does
- Accepts pasted blog content or `.txt` uploads
- Generates tailored content variations with Ollama or HuggingFace
- Saves campaigns and generated posts in SQLite
- Schedules posts with APScheduler
- Posts immediately or on a schedule to supported channels
- Falls back to dry-run mode when platform credentials are missing

## Tech Stack
- Python 3.9+
- Flask
- SQLite
- Ollama or HuggingFace Transformers
- APScheduler
- Tweepy, python-telegram-bot, SMTP email delivery
- HTML, CSS, and vanilla JavaScript frontend

## Project Structure
```
content-automation-system/
├── backend/
├── frontend/
├── n8n_workflows/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start
1. Create a virtual environment and install dependencies:

```bash
pip install -r backend/requirements.txt
```

2. Copy the environment template:

```bash
copy .env.example .env
```

3. Start Ollama if you want local AI generation:

```bash
ollama serve
ollama pull mistral
```

4. Run the Flask app:

```bash
python backend/main.py
```

5. Open `http://localhost:5000`

## Environment Variables
See [`.env.example`](.env.example) for the full list of configuration values.

## API Endpoints
- `POST /api/generate` - generate post variations from blog content
- `POST /api/schedule` - schedule an existing generated post
- `POST /api/post-now` - publish immediately to a platform
- `GET /api/history` - return campaigns and schedules
- `GET` or `POST /api/settings` - inspect or save local preferences

## n8n Workflow
A sample workflow export is included in [n8n_workflows/content_distribution_workflow.json](n8n_workflows/content_distribution_workflow.json) and can be adapted for a webhook-driven pipeline.

## Notes
- LinkedIn, Twitter, Telegram, and Email integrations degrade gracefully into dry-run mode when credentials are not present.
- Instagram is stored as a draft output by default because public posting automation is more restricted.
- The app is designed to be demo-friendly for portfolio use even without live API keys.
