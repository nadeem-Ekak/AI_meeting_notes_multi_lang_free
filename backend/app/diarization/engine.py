"""Speaker diarization (optional pyannote.audio with single-speaker fallback)."""
from __future__ import annotations

import os


class DiarizationEngine:
    """Assign a speaker label to each segment."""

    def assign(self, audio_path: str, segments: list[object]) -> list[str | None]:
        raise NotImplementedError


class SingleSpeakerDiarizer(DiarizationEngine):
    """Fallback: every segment belongs to one speaker."""

    def assign(self, audio_path: str, segments: list[object]) -> list[str | None]:
        return ["SPEAKER_00"] * len(segments)


class PyannoteDiarizer(DiarizationEngine):
    """Map pyannote speaker turns onto segments by temporal overlap."""

    def __init__(self, token: str | None = None) -> None:
        token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        if not token:
            raise RuntimeError(
                "pyannote.audio requires a Hugging Face token (HF_TOKEN)."
            )
        from pyannote.audio import Pipeline  # imported lazily

        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=token
        )

    def assign(self, audio_path: str, segments: list[object]) -> list[str | None]:
        diarization = self.pipeline(audio_path)
        labels: list[str | None] = []
        for seg in segments:
            start = float(getattr(seg, "start"))
            end = float(getattr(seg, "end"))
            best_label: str | None = None
            best_overlap = 0.0
            for turn, _speaker, label in diarization.itertracks(yield_label=True):
                overlap = min(end, turn.end) - max(start, turn.start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_label = label
            labels.append(best_label or "SPEAKER_00")
        return labels


def get_diarizer() -> DiarizationEngine:
    """Factory: pyannote when configured and installed, otherwise single-speaker."""
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if token:
        try:
            return PyannoteDiarizer(token)
        except Exception:  # pragma: no cover - optional dependency missing
            pass
    return SingleSpeakerDiarizer()
