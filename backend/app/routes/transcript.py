"""Transcription endpoints: run pipeline and read the language-tagged transcript."""
from __future__ import annotations

from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Meeting, Segment, Speaker
from ..schemas import (
    LanguageSwitch,
    SegmentOut,
    TranscriptOut,
    TranscribeRequest,
)
from ..stt import language as lang

router = APIRouter(prefix="/meetings", tags=["transcript"])

_LOW_CONFIDENCE_WARNING = "Low transcription confidence for this segment."


@router.post("/{meeting_id}/transcribe")
def transcribe_meeting(
    meeting_id: int,
    payload: TranscribeRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not meeting.audio_path:
        raise HTTPException(status_code=400, detail="Upload audio before transcribing")

    service = request.app.state.transcription_service
    service.transcribe_meeting(
        db,
        meeting_id,
        meeting.audio_path,
        language_mode=payload.language_mode,
        code_switching=payload.code_switching,
        use_custom_vocabulary=payload.use_custom_vocabulary,
    )
    return {"meeting_id": meeting_id, "status": "transcribed"}


@router.get("/{meeting_id}/transcript", response_model=TranscriptOut)
def get_transcript(meeting_id: int, db: Session = Depends(get_db)) -> TranscriptOut:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

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

    carriers = [SimpleNamespace(language=s.language) for s in segments]
    switches = [
        LanguageSwitch(
            at_segment=sw["at_segment"],
            from_lang=sw["from_lang"],
            to_lang=sw["to_lang"],
        )
        for sw in lang.detect_language_switches(carriers)
    ]

    segment_out = [
        SegmentOut(
            id=s.id,
            start=s.start,
            end=s.end,
            speaker=speaker_labels.get(s.speaker_id, "Speaker"),
            text=s.text,
            language=s.language,
            language_label=lang.language_label(s.language),
            language_confidence=s.language_confidence,
            script=s.script,
            low_confidence=s.low_confidence,
            warning=_LOW_CONFIDENCE_WARNING if s.low_confidence else None,
        )
        for s in segments
    ]

    return TranscriptOut(
        meeting_id=meeting_id,
        meeting_language=meeting.meeting_language,
        segments=segment_out,
        language_switches=switches,
    )
