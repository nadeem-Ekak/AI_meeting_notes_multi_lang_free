"""Transcription orchestration: STT → diarization → language pipeline → storage."""
from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy.orm import Session

from ..config import settings
from ..diarization.engine import DiarizationEngine
from ..models import Meeting, Segment, Speaker, Vocabulary
from ..stt import language as lang
from ..stt import vocab as vocab_mod
from ..stt.engine import TranscriptionEngine


class TranscriptionService:
    def __init__(
        self,
        engine: TranscriptionEngine | None = None,
        diarizer: DiarizationEngine | None = None,
    ) -> None:
        self._engine = engine
        self._diarizer = diarizer

    @property
    def engine(self) -> TranscriptionEngine:
        if self._engine is None:
            from ..stt.engine import FasterWhisperEngine

            self._engine = FasterWhisperEngine()
        return self._engine

    @property
    def diarizer(self) -> DiarizationEngine:
        if self._diarizer is None:
            from ..diarization.engine import get_diarizer

            self._diarizer = get_diarizer()
        return self._diarizer

    def transcribe_meeting(
        self,
        db: Session,
        meeting_id: int,
        audio_path: str,
        language_mode: str = "auto",
        code_switching: bool = True,
        use_custom_vocabulary: bool = True,
    ) -> None:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            raise ValueError(f"Meeting {meeting_id} not found.")

        vocab_entries = db.query(Vocabulary).all() if use_custom_vocabulary else []
        initial_prompt = vocab_mod.build_initial_prompt(vocab_entries)
        hotwords = vocab_mod.build_hotwords(vocab_entries)

        stt_segments = self.engine.transcribe(
            audio_path,
            language_mode=language_mode,
            hotwords=hotwords or None,
            initial_prompt=initial_prompt or None,
        )

        speaker_labels = self.diarizer.assign(audio_path, stt_segments)

        # Language metadata computed from acoustic LID (never from script alone).
        carriers = [
            SimpleNamespace(language=seg.language, speaker=label)
            for seg, label in zip(stt_segments, speaker_labels)
        ]
        meeting_language = lang.detect_meeting_language(carriers)
        speaker_languages = lang.detect_speaker_language(carriers)

        # Speakers
        speaker_map: dict[str, Speaker] = {}
        for label in dict.fromkeys(speaker_labels):
            speaker = (
                db.query(Speaker)
                .filter(Speaker.meeting_id == meeting_id, Speaker.label == label)
                .first()
            )
            if speaker is None:
                speaker = Speaker(meeting_id=meeting_id, label=label)
                db.add(speaker)
                db.flush()
            speaker_map[label] = speaker

        # Replace previous segments.
        db.query(Segment).filter(Segment.meeting_id == meeting_id).delete()
        db.flush()

        for seg, label in zip(stt_segments, speaker_labels):
            text = vocab_mod.apply_vocab(seg.text, vocab_entries)
            db.add(
                Segment(
                    meeting_id=meeting_id,
                    speaker_id=speaker_map[label].id,
                    start=seg.start,
                    end=seg.end,
                    text=text,
                    language=seg.language,
                    language_confidence=seg.language_probability,
                    script=lang.detect_script(text),
                    avg_logprob=seg.avg_logprob,
                    no_speech_prob=seg.no_speech_prob,
                    low_confidence=lang.is_low_confidence(
                        seg,
                        settings.lang_prob_threshold,
                        settings.avg_logprob_threshold,
                        settings.no_speech_threshold,
                    ),
                )
            )
        db.flush()

        for label, code in speaker_languages.items():
            speaker_map[label].dominant_language = code

        meeting.meeting_language = meeting_language
        meeting.status = "transcribed"
        meeting.audio_path = audio_path
        if stt_segments:
            meeting.duration = max(seg.end for seg in stt_segments)

        db.commit()


def transcript_as_text(db: Session, meeting_id: int) -> str:
    """Render the transcript with timestamps, speaker and language tags (RQ-53)."""
    segments = (
        db.query(Segment)
        .filter(Segment.meeting_id == meeting_id)
        .order_by(Segment.start)
        .all()
    )
    speaker_labels = {
        s.id: s.label
        for s in db.query(Speaker).filter(Speaker.meeting_id == meeting_id).all()
    }
    lines: list[str] = []
    for seg in segments:
        label = speaker_labels.get(seg.speaker_id, "Speaker")
        lang_label = lang.language_label(seg.language) or "Unknown"
        lines.append(f'[{_ts(seg.start)}] {label} [{lang_label}]: "{seg.text}"')
    return "\n".join(lines)


def _ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
