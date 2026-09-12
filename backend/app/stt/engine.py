"""Speech-to-text engine abstraction and faster-whisper implementation."""
from __future__ import annotations

from dataclasses import dataclass

from ..config import settings


@dataclass
class STTSegment:
    """One transcribed segment with acoustic language-detection metadata."""

    start: float
    end: float
    text: str
    language: str | None = None
    language_probability: float | None = None
    avg_logprob: float | None = None
    no_speech_prob: float | None = None


class TranscriptionEngine:
    """Abstract interface. Swap implementations for tests or other STT vendors."""

    def transcribe(
        self,
        audio_path: str,
        language_mode: str = "auto",
        hotwords: list[str] | None = None,
        initial_prompt: str | None = None,
    ) -> list[STTSegment]:
        raise NotImplementedError


def _forced_language(language_mode: str) -> str | None:
    """Map `manual:<code>` to a forced language code; None means auto-detect."""
    if language_mode.startswith("manual:"):
        return language_mode.split(":", 1)[1] or None
    return None


class FasterWhisperEngine(TranscriptionEngine):
    """faster-whisper wrapper.

    Language detection comes from Whisper's acoustic LID token. Per-segment language
    is read where the engine exposes it, otherwise it falls back to the
    transcription-level detected language (`info.language`).
    """

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        from faster_whisper import WhisperModel  # imported lazily (heavy dependency)

        self._model = WhisperModel(
            model_size or settings.stt_model,
            device=device or settings.stt_device,
            compute_type=compute_type or settings.stt_compute_type,
        )

    def transcribe(
        self,
        audio_path: str,
        language_mode: str = "auto",
        hotwords: list[str] | None = None,
        initial_prompt: str | None = None,
    ) -> list[STTSegment]:
        kwargs: dict = {
            "language": _forced_language(language_mode),
            "beam_size": 5,
        }
        if hotwords:
            kwargs["hotwords"] = hotwords
        if initial_prompt:
            kwargs["initial_prompt"] = initial_prompt

        segments_iter, info = self._model.transcribe(audio_path, **kwargs)

        results: list[STTSegment] = []
        for seg in segments_iter:
            lang = getattr(seg, "language", None) or info.language
            lang_prob = getattr(seg, "language_probability", None)
            if lang_prob is None:
                lang_prob = info.language_probability
            results.append(
                STTSegment(
                    start=float(seg.start),
                    end=float(seg.end),
                    text=seg.text.strip(),
                    language=lang,
                    language_probability=float(lang_prob) if lang_prob is not None else None,
                    avg_logprob=float(seg.avg_logprob) if seg.avg_logprob is not None else None,
                    no_speech_prob=float(seg.no_speech_prob) if seg.no_speech_prob is not None else None,
                )
            )
        return results


class MockTranscriptionEngine(TranscriptionEngine):
    """Deterministic engine for tests — returns caller-provided segments."""

    def __init__(self, segments: list[STTSegment] | None = None) -> None:
        self.segments = segments or []

    def transcribe(
        self,
        audio_path: str,
        language_mode: str = "auto",
        hotwords: list[str] | None = None,
        initial_prompt: str | None = None,
    ) -> list[STTSegment]:
        return list(self.segments)
