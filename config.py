"""Centralized application configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "microsoft/DialoGPT-small")
        self.MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "5"))
        self.MAX_INPUT_LENGTH: int = int(os.getenv("MAX_INPUT_LENGTH", "500"))
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.DEBUG: bool = _get_bool("DEBUG", False)
        self.RATE_LIMIT: str = os.getenv("RATE_LIMIT", "20/minute")
        self.RATE_LIMIT_CHAT: str = os.getenv("RATE_LIMIT_CHAT", "10/minute")
        self.MAX_NEW_TOKENS: int = int(os.getenv("MAX_NEW_TOKENS", "200"))
        self.TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
        self.TOP_P: float = float(os.getenv("TOP_P", "0.9"))
        self.TOP_K: int = int(os.getenv("TOP_K", "50"))
        self.REPETITION_PENALTY: float = float(os.getenv("REPETITION_PENALTY", "1.0"))
        self.MODEL_TIMEOUT: int = int(os.getenv("MODEL_TIMEOUT", "30"))


config = Config()
