from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler

try:
    from .ai_handler import generate_posts
    from .api_handlers import post_to_platform
    from .config import settings
    from .database import (
        create_schedule,
        get_app_settings,
        get_due_schedules,
        init_db,
        list_campaigns,
        list_generated_posts,
        list_schedules,
        mark_post_failed,
        mark_post_posted,
        mark_schedule_attempt,
        mark_schedule_posted,
        save_campaign,
        save_generated_posts,
        update_app_setting,
        update_post_content,
    )
except ImportError:  # pragma: no cover - script execution fallback
    from ai_handler import generate_posts
    from api_handlers import post_to_platform
    from config import settings
    from database import (
        create_schedule,
        get_app_settings,
        get_due_schedules,
        init_db,
        list_campaigns,
        list_generated_posts,
        list_schedules,
        mark_post_failed,
        mark_post_posted,
        mark_schedule_attempt,
        mark_schedule_posted,
        save_campaign,
        save_generated_posts,
        update_app_setting,
        update_post_content,
    )

BASE_DIR = Path(__file__).resolve().parent.parent
app = Flask(__name__, template_folder=str(BASE_DIR / "frontend" / "templates"), static_folder=str(BASE_DIR / "frontend" / "static"))
app.config["SECRET_KEY"] = settings.secret_key
scheduler = BackgroundScheduler(timezone=settings.timezone)
_runtime_initialized = False


def bootstrap() -> None:
    global _runtime_initialized
    if _runtime_initialized:
        return
    init_db()
    if not scheduler.running:
        scheduler.add_job(check_scheduled_posts, "interval", minutes=1, id="scheduled-post-poller", replace_existing=True)
        scheduler.start()
    _runtime_initialized = True


@app.teardown_appcontext
def shutdown_scheduler(exception: BaseException | None = None) -> None:
    pass


def _extract_content_from_request() -> Dict[str, Any]:
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        return {
            "title": payload.get("title") or "Untitled Campaign",
            "content": payload.get("content") or payload.get("text") or "",
        }

    title = request.form.get("title") or "Untitled Campaign"
    content = request.form.get("content") or ""
    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        title = Path(uploaded_file.filename).stem
    return {"title": title, "content": content}


def check_scheduled_posts() -> None:
    now_iso = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    due_items = get_due_schedules(now_iso)
    for item in due_items:
        schedule_id = item["schedule_id"]
        post_id = item["post_id"]
        platform = item["platform"]
        content = item["edited_content"] or item["generated_content"]
        mark_schedule_attempt(schedule_id, "processing")
        try:
            if platform == "email" and item["edited_content"]:
                try:
                    parsed = json.loads(item["edited_content"])
                    content = parsed
                except json.JSONDecodeError:
                    content = {"subject": "Campaign update", "body": item["edited_content"]}
            result = post_to_platform(platform, content)
            if result.get("status") == "posted":
                mark_schedule_posted(schedule_id, post_id, result.get("post_url") or "")
            else:
                mark_post_failed(post_id, result.get("message") or "Scheduled post failed")
                mark_schedule_attempt(schedule_id, "failed")
        except Exception as exc:
            mark_post_failed(post_id, str(exc))
            mark_schedule_attempt(schedule_id, "failed")


bootstrap()


@app.route("/")
def index() -> str:
    return render_template("index.html", settings=settings, app_settings=get_app_settings())


@app.route("/dashboard")
def dashboard() -> str:
    return render_template("dashboard.html", campaigns=list_campaigns(), schedules=list_schedules(), settings=settings)


@app.route("/schedule")
def schedule_page() -> str:
    campaigns = list_campaigns()
    return render_template("schedule.html", campaigns=campaigns, settings=settings)


@app.route("/settings")
def settings_page() -> str:
    return render_template("settings.html", settings=settings, app_settings=get_app_settings())


@app.route("/api/generate", methods=["POST"])
def api_generate():
    init_db()
    payload = _extract_content_from_request()
    title = payload["title"].strip() or "Untitled Campaign"
    content = payload["content"].strip()
    if not content:
        return jsonify({"error": "Content is required."}), 400

    campaign_id = save_campaign(title, content)
    posts = generate_posts(content)
    created_posts = save_generated_posts(campaign_id, posts)
    return jsonify({"campaign_id": campaign_id, "title": title, "posts": posts, "saved_posts": created_posts, "generated_posts": created_posts})


@app.route("/api/schedule", methods=["POST"])
def api_schedule():
    data = request.get_json(force=True)
    post_id = int(data["post_id"])
    platform = data["platform"]
    scheduled_time = data["scheduled_time"]
    schedule_id = create_schedule(post_id, platform, scheduled_time)
    return jsonify({"status": "scheduled", "schedule_id": schedule_id})


@app.route("/api/post-now", methods=["POST"])
def api_post_now():
    data = request.get_json(force=True)
    post_id = int(data["post_id"])
    platform = data["platform"]
    content = data.get("content")
    if content is None:
        posts = list_generated_posts(int(data["campaign_id"])) if data.get("campaign_id") else []
        content = next((post["edited_content"] for post in posts if post["id"] == post_id), "")
    result = post_to_platform(platform, content)
    if result.get("status") == "posted":
        mark_post_posted(post_id, result.get("post_url") or "")
    return jsonify(result)


@app.route("/api/history")
def api_history():
    return jsonify({"campaigns": list_campaigns(), "schedules": list_schedules()})


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat(timespec="seconds")})


@app.route("/api/post/<int:post_id>", methods=["PUT"])
def api_update_post(post_id: int):
    data = request.get_json(force=True)
    update_post_content(post_id, data.get("edited_content", ""))
    return jsonify({"status": "updated"})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        return jsonify({"settings": get_app_settings()})

    data = request.get_json(force=True)
    for key, value in data.items():
        update_app_setting(key, str(value))
    return jsonify({"status": "saved"})


if __name__ == "__main__":
    bootstrap()
    app.run(debug=True, port=5000)
