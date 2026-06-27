from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

try:
    import tweepy
except ImportError:  # pragma: no cover
    tweepy = None

try:
    from telegram import Bot
except ImportError:  # pragma: no cover
    Bot = None


@dataclass
class PlatformResult:
    platform: str
    status: str
    external_id: Optional[str] = None
    post_url: Optional[str] = None
    dry_run: bool = False
    message: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "status": self.status,
            "external_id": self.external_id,
            "post_url": self.post_url,
            "dry_run": self.dry_run,
            "message": self.message,
        }


def _dry_run(platform: str, content: str, message: str) -> PlatformResult:
    preview = content[:120].replace("\n", " ")
    return PlatformResult(
        platform=platform,
        status="posted",
        external_id=f"dry-run-{platform}",
        post_url=f"https://example.com/{platform}/preview",
        dry_run=True,
        message=f"{message} Preview: {preview}",
    )


def post_to_twitter(content: str, scheduled_time: Optional[str] = None) -> Dict[str, Any]:
    if not all(
        [
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET"),
        ]
    ) or tweepy is None:
        return _dry_run("twitter", content, "Twitter credentials missing or tweepy unavailable.").as_dict()

    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
    )
    response = client.create_tweet(text=content)
    tweet_id = str(response.data["id"])
    return PlatformResult(
        platform="twitter",
        status="posted",
        external_id=tweet_id,
        post_url=f"https://twitter.com/i/web/status/{tweet_id}",
    ).as_dict()


def post_to_linkedin(content: str, scheduled_time: Optional[str] = None) -> Dict[str, Any]:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return _dry_run("linkedin", content, "LinkedIn token missing.").as_dict()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": os.getenv("LINKEDIN_AUTHOR_URN", "urn:li:person:me"),
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    response = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload, timeout=30)
    if response.ok:
        post_id = response.headers.get("x-restli-id", "linkedin-post")
        return PlatformResult(
            platform="linkedin",
            status="posted",
            external_id=post_id,
            post_url=os.getenv("LINKEDIN_POST_URL", "https://www.linkedin.com/feed/"),
        ).as_dict()
    return PlatformResult(platform="linkedin", status="failed", message=response.text).as_dict()


def post_to_telegram(content: str, scheduled_time: Optional[str] = None) -> Dict[str, Any]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not channel_id or Bot is None:
        return _dry_run("telegram", content, "Telegram credentials missing or python-telegram-bot unavailable.").as_dict()

    bot = Bot(token=token)
    message = bot.send_message(chat_id=channel_id, text=content, parse_mode="HTML")
    return PlatformResult(
        platform="telegram",
        status="posted",
        external_id=str(message.message_id),
        post_url=f"https://t.me/{channel_id.lstrip('@')}",
    ).as_dict()


def send_email(subject: str, body: str, scheduled_time: Optional[str] = None) -> Dict[str, Any]:
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")
    if not sender or not password or not recipient:
        return _dry_run("email", f"{subject}\n\n{body}", "Email credentials missing.").as_dict()

    from email.mime.text import MIMEText
    import smtplib

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, message.as_string())

    return PlatformResult(platform="email", status="posted", external_id=subject).as_dict()


def draft_instagram(content: str, scheduled_time: Optional[str] = None) -> Dict[str, Any]:
    return _dry_run("instagram", content, "Instagram is stored as a draft for manual posting.").as_dict()


def post_to_platform(platform: str, content: Any, scheduled_time: Optional[str] = None) -> Dict[str, Any]:
    handlers = {
        "twitter": post_to_twitter,
        "linkedin": post_to_linkedin,
        "telegram": post_to_telegram,
        "email": send_email,
        "instagram": draft_instagram,
    }
    handler = handlers.get(platform)
    if handler is None:
        return PlatformResult(platform=platform, status="failed", message="Unsupported platform").as_dict()

    if platform == "email":
        if isinstance(content, dict):
            subject = content.get("subject", "Campaign update")
            body = content.get("body", "")
        else:
            subject = "Campaign update"
            body = str(content)
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    subject = parsed.get("subject", subject)
                    body = parsed.get("body", body)
            except Exception:
                pass
        return handler(subject, body, scheduled_time)

    return handler(str(content), scheduled_time)
