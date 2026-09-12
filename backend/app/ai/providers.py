"""LLM provider abstraction (RQ-59/60/61).

Supports any OpenAI-compatible endpoint. DeepSeek and OpenAI are preconfigured;
users can add a custom endpoint (base URL + key + model) via Settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Setting


class LLMNotConfiguredError(RuntimeError):
    pass


@dataclass
class LLMProvider:
    name: str
    base_url: str
    api_key: str | None
    model: str


PRESET_PROVIDERS: dict[str, dict] = {
    "deepseek": {
        "name": "deepseek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "name": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
}


class LLMClient:
    """Thin wrapper around the OpenAI-compatible chat-completions API."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def complete(self, system: str, user: str, temperature: float = 0.3) -> str:
        if not self.provider.api_key:
            raise LLMNotConfiguredError(
                f"API key is not set for provider '{self.provider.name}'. "
                f"Set {self.provider.name.upper()}_API_KEY or configure it in Settings."
            )
        from openai import OpenAI  # imported lazily

        client = OpenAI(api_key=self.provider.api_key, base_url=self.provider.base_url)
        response = client.chat.completions.create(
            model=self.provider.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()


def providers_from_env() -> list[LLMProvider]:
    """Build the provider list from environment variables."""
    providers: list[LLMProvider] = []
    for preset in PRESET_PROVIDERS.values():
        key = os.environ.get(preset["env_key"])
        providers.append(
            LLMProvider(
                name=preset["name"],
                base_url=preset["base_url"],
                api_key=key,
                model=preset["model"],
            )
        )
    custom_url = os.environ.get("CUSTOM_BASE_URL")
    if custom_url:
        providers.append(
            LLMProvider(
                name="custom",
                base_url=custom_url,
                api_key=os.environ.get("CUSTOM_API_KEY"),
                model=os.environ.get("CUSTOM_MODEL", ""),
            )
        )
    return providers


def _stored(db: Session, key: str, field: str):
    row = db.query(Setting).filter(Setting.key == key).first()
    if row and isinstance(row.value, dict) and field in row.value:
        return row.value[field]
    return None


def load_providers(db: Session) -> list[LLMProvider]:
    stored = _stored(db, "llm_providers", "items")
    if stored:
        return [
            LLMProvider(
                name=p.get("name", ""),
                base_url=p.get("base_url", ""),
                api_key=p.get("api_key"),
                model=p.get("model", ""),
            )
            for p in stored
        ]
    return providers_from_env()


def get_default_provider_name(db: Session) -> str:
    stored = _stored(db, "llm_default_provider", "value")
    return stored or settings.llm_default_provider


def get_llm_client(db: Session) -> LLMClient:
    """Resolve the active provider and return a client for it."""
    providers = load_providers(db)
    default = get_default_provider_name(db)
    provider = next((p for p in providers if p.name == default), None)
    if provider is None and providers:
        provider = providers[0]
    if provider is None:
        raise LLMNotConfiguredError("No LLM provider configured.")
    return LLMClient(provider)
