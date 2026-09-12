"""AI notes: summary, bullet notes, and Minutes-of-Meeting (RQ-59/60/61).

The original transcript is never modified. Output language is selectable.
"""
from __future__ import annotations

from ..stt.language import SUPPORTED_LANGUAGES
from .providers import LLMClient

_SYSTEM = (
    "You are a multilingual meeting assistant. You understand English, Hindi, Hinglish, "
    "Urdu, Bengali, Gujarati, Marathi, Punjabi, Tamil, Telugu, Kannada, Malayalam, Odia, "
    "Assamese, Nepali and other languages. "
    "Understand and use ALL languages present in the transcript — never ignore "
    "non-English sections. Never translate personal names or proper nouns. "
    "Never modify or rephrase the original transcript itself."
)


def _target_instruction(language: str | None) -> str:
    if not language or language.lower() == "same":
        return (
            "in the same language(s) as the meeting content. "
            "If the meeting is mixed-language, prefer English."
        )
    if language.lower() in SUPPORTED_LANGUAGES:
        return f"in {SUPPORTED_LANGUAGES[language.lower()]}."
    return f"in {language}."


def generate_summary(client: LLMClient, transcript: str, language: str = "same") -> str:
    user = (
        f"Meeting transcript:\n\n{transcript}\n\n"
        f"Write a concise summary {_target_instruction(language)}"
    )
    return client.complete(_SYSTEM, user)


def generate_notes(client: LLMClient, transcript: str, language: str = "same") -> str:
    user = (
        f"Meeting transcript:\n\n{transcript}\n\n"
        f"Extract the key notes and action items as bullet points "
        f"{_target_instruction(language)}"
    )
    return client.complete(_SYSTEM, user)


def generate_mom(client: LLMClient, transcript: str, language: str = "same") -> str:
    user = (
        f"Meeting transcript:\n\n{transcript}\n\n"
        f"Produce Minutes of Meeting (MoM) with sections: Attendees, Agenda, "
        f"Discussions, Decisions, Action Items (with owners). "
        f"Write it {_target_instruction(language)}"
    )
    return client.complete(_SYSTEM, user)


GENERATORS = {
    "summary": generate_summary,
    "notes": generate_notes,
    "mom": generate_mom,
}
