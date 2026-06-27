
# n8n Workflow: AI Content Automation

**Side project exploring n8n automation capabilities**

A webhook-driven n8n workflow that triggers Flask backend content generation and schedules multi-platform distribution automatically. Built out of curiosity to learn n8n's workflow automation features.

---

## What It Does

1. **Webhook receives blog post** (title + content)
2. **Triggers Flask backend** (`POST /api/generate`)
3. **AI generates platform variations** (Twitter, LinkedIn, Telegram, Email)
4. **Schedules posts** automatically across platforms
5. **No manual intervention** — fully automated flow

---

## Workflow Overview

```
Webhook Trigger
    ↓
Call Flask Backend (/api/generate)
    ↓
Parse Response (extract posts by platform)
    ↓
├─→ Post to Twitter
├─→ Post to Telegram
├─→ Send Email
└─→ Save to Schedule
```

---

## Setup

### 1. Import Workflow

1. Open n8n (cloud or self-hosted)
2. Click **"Workflows"** → **"Create New"**
3. Click menu (...) → **"Import from JSON"**
4. Paste JSON from `/n8n_workflows/content_distribution_workflow.json`
5. Click **"Import"**

### 2. Configure Webhook Trigger

1. Click **"New Blog Post"** (webhook node)
2. Copy the test URL displayed
3. n8n generates unique webhook URL for your workflow

### 3. Set Backend URL

In **"Call Flask Backend"** node:
- Change URL to your Flask server:
  - Local: `http://localhost:5000/api/generate`
  - Cloud: `https://your-deployed-app.com/api/generate`
  - ngrok: `https://your-ngrok-url.ngrok-free.dev/api/generate`

### 4. Add Platform Credentials (Optional)

For live posting, add authentication:
- **Twitter node:** Connect Twitter OAuth credentials
- **Telegram node:** Add Bot Token
- **Email node:** Add Gmail credentials

Without credentials, workflow still runs in **dry-run mode** (shows what would be posted).

### 5. Activate Workflow

Click **"Activate"** button (top right)

---

## Usage

### Send Content to Webhook

**PowerShell:**
```powershell
Invoke-WebRequest -Uri "YOUR_WEBHOOK_URL" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"title":"My Post","content":"Blog content here..."}' `
  -UseBasicParsing
```

**Linux/Mac (curl):**
```bash
curl -X POST YOUR_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"title":"My Post","content":"Blog content here..."}'
```

### Check Execution

1. Go to **"Executions"** tab
2. See real-time logs of:
   - Webhook received ✓
   - Flask called ✓
   - Posts generated ✓
   - Platforms posted ✓

---

## Workflow JSON Structure

```json
{
  "name": "AI Content Automation",
  "nodes": [
    {
      "id": "webhook-trigger",
      "name": "New Blog Post",
      "type": "webhook"
    },
    {
      "id": "call-flask-backend",
      "name": "Call Flask Backend",
      "type": "httpRequest",
      "url": "http://localhost:5000/api/generate"
    },
    {
      "id": "parse-response",
      "name": "Parse Response",
      "type": "code"
    },
    {
      "id": "post-twitter",
      "name": "Post to Twitter",
      "type": "twitter"
    },
    {
      "id": "post-telegram",
      "name": "Post to Telegram",
      "type": "telegram"
    }
  ]
}
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| **"Bad request" from Flask** | Check Flask is running on correct URL |
| **Webhook not receiving data** | Verify webhook URL is correct in your HTTP call |
| **Posts not posting** | Ensure platform credentials are configured |
| **"No matching data" in n8n** | Check body parameters match Flask expectations |

---

## Why n8n?

- **No-code automation** — Visual workflow builder
- **Webhook triggers** — Event-driven architecture
- **100+ integrations** — Connect to any API
- **Free tier** — 14-day trial, self-hosted free
- **Learning playground** — Explore workflow automation concepts

---

## Extensibility

This workflow can easily add:
- **Scheduling nodes** — Post at specific times
- **Conditional logic** — Different content per platform
- **Database logging** — Track all posts
- **Slack notifications** — Alert on completion
- **Additional platforms** — Reddit, Discord, etc.

---

## Files

- `content_distribution_workflow.json` — Complete workflow (importable)
- `README.md` — Main system documentation
- `.env.example` — Backend configuration

---

**Version:** 1.0.0 | Built to explore n8n automation | June 2026
