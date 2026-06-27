from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Content Automation System")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    database_path: str = os.getenv("DATABASE_PATH", os.getenv("DATABASE_URL", "content_automation.db").replace("sqlite:///", ""))
    timezone: str = os.getenv("DEFAULT_TIMEZONE", "UTC")
    ai_provider: str = os.getenv("AI_PROVIDER", "ollama")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "mistral")
    hf_model: str = os.getenv("HF_MODEL", "facebook/bart-large-cnn")
    generation_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    generation_max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "900"))
    enable_twitter: bool = os.getenv("ENABLE_TWITTER", "true").lower() == "true"
    enable_linkedin: bool = os.getenv("ENABLE_LINKEDIN", "true").lower() == "true"
    enable_telegram: bool = os.getenv("ENABLE_TELEGRAM", "true").lower() == "true"
    enable_email: bool = os.getenv("ENABLE_EMAIL", "true").lower() == "true"
    enable_instagram: bool = os.getenv("ENABLE_INSTAGRAM", "true").lower() == "true"


settings = Settings()
