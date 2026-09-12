"""Optional translation endpoint — separate from transcription & summary (RQ-60)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import providers
from ..ai import translate as translate_ai
from ..db import get_db
from ..models import Meeting, Note
from ..schemas import TranslateOut, TranslateRequest
from ..services.transcription import transcript_as_text

router = APIRouter(prefix="/meetings", tags=["translate"])


@router.post("/{meeting_id}/translate", response_model=TranslateOut)
def translate_meeting(
    meeting_id: int,
    payload: TranslateRequest,
    db: Session = Depends(get_db),
) -> TranslateOut:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if payload.source == "summary":
        source_note = (
            db.query(Note)
            .filter(Note.meeting_id == meeting_id, Note.kind == "summary")
            .order_by(Note.created_at.desc())
            .first()
        )
        if source_note is None:
            raise HTTPException(status_code=400, detail="Generate a summary first")
        text = source_note.content
        source_language = source_note.language
    else:
        if meeting.status != "transcribed":
            raise HTTPException(status_code=400, detail="Transcribe the meeting first")
        text = transcript_as_text(db, meeting_id)
        source_language = meeting.meeting_language

    client = providers.get_llm_client(db)
    content = translate_ai.translate_text(client, text, payload.target_language, source_language)

    note = Note(
        meeting_id=meeting_id,
        kind="translation",
        language=payload.target_language,
        content=content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return TranslateOut(id=note.id, target_language=payload.target_language, content=content)
