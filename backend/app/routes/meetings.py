"""Meeting CRUD and audio upload."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..config import settings
from ..db import get_db
from ..models import Meeting
from ..schemas import MeetingCreate, MeetingOut
from sqlalchemy.orm import Session

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("", response_model=MeetingOut)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)) -> Meeting:
    meeting = Meeting(title=payload.title)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/upload")
async def upload_audio(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    os.makedirs(settings.upload_dir, exist_ok=True)
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    dest = Path(settings.upload_dir) / f"{meeting_id}{suffix}"
    dest.write_bytes(await file.read())

    meeting.audio_path = str(dest)
    db.commit()
    return {"meeting_id": meeting_id, "audio_path": str(dest)}
