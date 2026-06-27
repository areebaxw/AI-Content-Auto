from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import requests

try:
    from .config import settings
except ImportError:  # pragma: no cover - script execution fallback
    from config import settings

PLATFORM_SPECS = {
    "twitter": {"count": 5, "max_chars": 280, "tone": "engaging, concise, click-worthy"},
    "linkedin": {"count": 2, "max_chars": 1300, "tone": "professional, insightful, credibility-building"},
    "telegram": {"count": 3, "max_chars": 500, "tone": "casual, emoji-friendly, community-first"},
    "instagram": {"count": 1, "max_chars": 2200, "tone": "trend-aware, visual, hashtag-rich"},
}


def _clean_json_response(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Model did not return valid JSON")
    return json.loads(match.group(0))


def _fallback_posts(original_content: str) -> Dict[str, Any]:
    summary = " ".join(original_content.split())[:220]
    return {
        "twitter": [
            f"{summary[:240]} #AI #ContentMarketing",
            f"Turn one blog post into multiple platform-ready assets with AI. {summary[:180]}",
            f"Repurpose content faster, publish smarter, and stay consistent. {summary[:170]}",
            f"Multi-platform distribution can be simple when the workflow is automated. {summary[:160]}",
            f"From blog to feed in one pass. {summary[:180]}",
        ],
        "linkedin": [
            f"{summary} This workflow turns long-form content into a distribution system that saves time and keeps messaging consistent.",
            f"A single article can power Twitter, LinkedIn, Telegram, email, and Instagram if the generation pipeline is structured well. {summary}",
        ],
        "telegram": [
            f"{summary} 🚀",
            f"New content repurposing flow is ready for testing. ⚙️✨",
            f"Automate the boring parts and focus on strategy. 🤖",
        ],
        "email": {
            "subject": f"New content automation workflow: {summary[:55]}",
            "body": f"Here is the distilled version of the blog post:\n\n{summary}\n\nUse the dashboard to edit, schedule, and distribute it across channels.",
        },
        "instagram": [
            f"{summary} #contentcreation #automation #AI #marketing #creator",
        ],
    }


def _generate_prompt(platform: str, count: int, original_content: str) -> str:
    spec = PLATFORM_SPECS.get(platform, {})
    return f"""You are a social media expert.
Take this blog content and create {count} {platform} posts that are:
- Engaging and click-worthy
- On-brand and professional
- Use relevant hashtags only when appropriate for the platform
- Respect a maximum length of {spec.get('max_chars', 500)} characters per item
- Match this tone: {spec.get('tone', 'clear, helpful')}

Blog content:
{original_content}

Return only valid JSON with this shape:
{{
  "{platform}": ["post 1", "post 2"]
}}
"""


def generate_with_ollama(original_content: str) -> Dict[str, Any]:
    payload = {
        "model": settings.ollama_model,
        "prompt": (
            "You are a social media expert. Turn the blog content into structured platform posts. "
            "Return only valid JSON with keys twitter, linkedin, telegram, email, instagram. "
            "Twitter should contain exactly 5 items. LinkedIn exactly 2. Telegram exactly 3. Instagram exactly 1. "
            "Email must be an object with subject and body. Keep each item platform-appropriate.\n\n"
            f"Blog content:\n{original_content}"
        ),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": settings.generation_temperature,
            "num_predict": settings.generation_max_tokens,
        },
    }
    response = requests.post(f"{settings.ollama_url}/api/generate", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    raw_text = data.get("response", "{}")
    return _clean_json_response(raw_text)


def generate_with_huggingface(original_content: str) -> Dict[str, Any]:
    try:
        from transformers import pipeline
    except ImportError:
        return _fallback_posts(original_content)

    summarizer = pipeline("summarization", model=settings.hf_model)
    summary = summarizer(original_content, max_length=150, min_length=60, do_sample=False)[0]["summary_text"]
    return {
        "twitter": [
            f"{summary[:240]} #AI #automation",
            f"{summary[:235]} #contentmarketing",
            f"{summary[:230]} #productivity",
            f"{summary[:225]} #socialmedia",
            f"{summary[:220]} #marketing",
        ],
        "linkedin": [
            f"{summary}",
            f"This content automation workflow turns one blog post into a multi-channel distribution engine. {summary}",
        ],
        "telegram": [
            f"{summary[:200]} 🚀",
            f"Content repurposing is now automated. ✨",
            f"Scheduling, posting, and tracking in one dashboard. 🤖",
        ],
        "email": {
            "subject": f"Content automation update: {summary[:60]}",
            "body": summary,
        },
        "instagram": [f"{summary[:180]} #automation #creator #socialmedia #ai"],
    }


def generate_posts(original_content: str) -> Dict[str, Any]:
    provider = settings.ai_provider.lower()
    if provider == "ollama":
        try:
            return generate_with_ollama(original_content)
        except Exception:
            return _fallback_posts(original_content)
    return generate_with_huggingface(original_content)
