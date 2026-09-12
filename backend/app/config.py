"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class Settings:
    # Speech-to-text
    stt_model: str = field(default_factory=lambda: _env_str("STT_MODEL", "large-v3"))
    stt_device: str = field(default_factory=lambda: _env_str("STT_DEVICE", "cpu"))
    stt_compute_type: str = field(default_factory=lambda: _env_str("STT_COMPUTE_TYPE", "int8"))

    # Database
    database_url: str = field(
        default_factory=lambda: _env_str("DATABASE_URL", "sqlite:///./meeting_notes.db")
    )

    # Confidence thresholds (RQ-63)
    lang_prob_threshold: float = field(
        default_factory=lambda: _env_float("LANG_PROB_THRESHOLD", 0.60)
    )
    avg_logprob_threshold: float = field(
        default_factory=lambda: _env_float("AVG_LOGPROB_THRESHOLD", -1.0)
    )
    no_speech_threshold: float = field(
        default_factory=lambda: _env_float("NO_SPEECH_THRESHOLD", 0.60)
    )

    # Language settings (RQ-64)
    language_mode: str = field(default_factory=lambda: _env_str("LANGUAGE_MODE", "auto"))
    code_switching: bool = field(
        default_factory=lambda: _env_str("CODE_SWITCHING", "1") not in ("0", "false", "False")
    )

    # LLM (RQ-59/60/61)
    llm_default_provider: str = field(
        default_factory=lambda: _env_str("LLM_DEFAULT_PROVIDER", "deepseek")
    )

    upload_dir: str = field(default_factory=lambda: _env_str("UPLOAD_DIR", "./uploads"))


settings = Settings()
