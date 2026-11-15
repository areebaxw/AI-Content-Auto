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
        "prompt": f"{_instructions()}\n\nBlog content:\n{original_content}",
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


SHARED_INSTRUCTIONS = (
    "You are a social media expert. Turn the blog content into structured platform posts. "
    "Return only valid JSON with keys twitter, linkedin, telegram, email, instagram. "
    "Twitter should contain exactly 5 items. LinkedIn exactly 2. Telegram exactly 3. Instagram exactly 1. "
    "Email must be an object with subject and body. Keep each item platform-appropriate."
)

EXPECTED_KEYS = ("twitter", "linkedin", "telegram", "email", "instagram")


def _instructions() -> str:
    """Shared instructions plus length limits and the optional brand voice from .env."""
    limits = " ".join(
        f"Each {name} item must be at most {spec['max_chars']} characters." for name, spec in PLATFORM_SPECS.items()
    )
    parts = [SHARED_INSTRUCTIONS, limits]
    if settings.brand_voice:
        parts.append(f"Write in this brand voice: {settings.brand_voice}.")
    if settings.brand_audience:
        parts.append(f"The audience is: {settings.brand_audience}.")
    return " ".join(parts)


def _trim(text: str, limit: int) -> str:
    """Cut at a word boundary and end with an ellipsis so the result fits the limit."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut[limit // 2 :]:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:-") + "\u2026"


def enforce_limits(posts: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
    """Make every post fit its platform limit. Returns (posts, number of items trimmed)."""
    trimmed = 0
    cleaned: Dict[str, Any] = {}
    for platform, value in posts.items():
        spec = PLATFORM_SPECS.get(platform)
        if spec is None or platform == "email":
            cleaned[platform] = value
            continue
        items = value if isinstance(value, list) else [value]
        fitted = []
        for item in items:
            text = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
            short = _trim(text.strip(), spec["max_chars"])
            trimmed += short != text.strip()
            fitted.append(short)
        cleaned[platform] = fitted
    return cleaned, trimmed


def _validate_posts(posts: Any) -> Dict[str, Any]:
    """Reject model output that has none of the expected platform keys."""
    if not isinstance(posts, dict) or not any(posts.get(key) for key in EXPECTED_KEYS):
        raise ValueError("Model response did not contain any platform posts")
    return posts


def generate_with_openai(original_content: str) -> Dict[str, Any]:
    """Generate with any OpenAI-compatible chat completions endpoint."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": _instructions()},
            {"role": "user", "content": f"Blog content:\n{original_content}"},
        ],
        "temperature": settings.generation_temperature,
        "max_tokens": settings.generation_max_tokens,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        f"{settings.openai_base_url.rstrip('/')}/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        timeout=120,
    )
    response.raise_for_status()
    raw_text = response.json()["choices"][0]["message"]["content"] or "{}"
    return _clean_json_response(raw_text)


def _generate_raw(original_content: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (posts, meta). meta says which provider ran and whether template fallback was used."""
    provider = settings.ai_provider.lower()
    meta: Dict[str, Any] = {"provider": provider, "fallback_used": False, "fallback_reason": None}

    def _fallback(reason: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        meta["fallback_used"] = True
        meta["fallback_reason"] = reason
        return _fallback_posts(original_content), meta

    if provider == "ollama":
        try:
            return _validate_posts(generate_with_ollama(original_content)), meta
        except requests.exceptions.ConnectionError:
            return _fallback(f"Could not reach Ollama at {settings.ollama_url}. Is it running?")
        except Exception as exc:
            return _fallback(f"Ollama generation failed: {exc}")

    if provider == "openai":
        try:
            return _validate_posts(generate_with_openai(original_content)), meta
        except Exception as exc:
            return _fallback(f"OpenAI-compatible generation failed: {exc}")

    if provider == "huggingface":
        try:
            import transformers  # noqa: F401
        except ImportError:
            return _fallback("transformers is not installed. Run: pip install -r backend/requirements-huggingface.txt")
        try:
            return generate_with_huggingface(original_content), meta
        except Exception as exc:
            return _fallback(f"HuggingFace generation failed: {exc}")

    return _fallback(f"Unknown AI_PROVIDER '{provider}'. Use ollama, openai or huggingface.")


def generate_posts_with_meta(original_content: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (posts, meta). meta: provider, fallback_used, fallback_reason, trimmed."""
    posts, meta = _generate_raw(original_content)
    posts, meta["trimmed"] = enforce_limits(posts)
    return posts, meta


def generate_posts(original_content: str) -> Dict[str, Any]:
    return generate_posts_with_meta(original_content)[0]
