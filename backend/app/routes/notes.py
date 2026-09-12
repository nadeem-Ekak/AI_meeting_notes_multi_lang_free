"""AI notes / summary / MoM endpoints (RQ-59/60/61)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import notes as notes_ai
from ..ai import providers
from ..db import get_db
from ..models import Meeting, Note
from ..schemas import NotesOut, NotesRequest
from ..services.transcription import transcript_as_text

router = APIRouter(prefix="/meetings", tags=["notes"])


@router.post("/{meeting_id}/notes", response_model=NotesOut)
def create_notes(
    meeting_id: int,
    payload: NotesRequest,
    db: Session = Depends(get_db),
) -> Note:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.status != "transcribed":
        raise HTTPException(status_code=400, detail="Transcribe the meeting first")

    transcript = transcript_as_text(db, meeting_id)
    client = providers.get_llm_client(db)
    generator = notes_ai.GENERATORS[payload.kind]
    content = generator(client, transcript, payload.language)

    note = Note(
        meeting_id=meeting_id,
        kind=payload.kind,
        language=payload.language,
        content=content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{meeting_id}/notes", response_model=list[NotesOut])
def list_notes(meeting_id: int, db: Session = Depends(get_db)) -> list[Note]:
    return (
        db.query(Note)
        .filter(Note.meeting_id == meeting_id)
        .order_by(Note.created_at)
        .all()
    )
