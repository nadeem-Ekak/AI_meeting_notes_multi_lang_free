"""Custom vocabulary & names management (RQ-57/58)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Vocabulary
from ..schemas import VocabularyCreate, VocabularyOut

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("", response_model=list[VocabularyOut])
def list_vocabulary(db: Session = Depends(get_db)) -> list[Vocabulary]:
    return db.query(Vocabulary).order_by(Vocabulary.term).all()


@router.post("", response_model=VocabularyOut)
def create_vocabulary(
    payload: VocabularyCreate, db: Session = Depends(get_db)
) -> Vocabulary:
    entry = Vocabulary(
        term=payload.term,
        language=payload.language,
        script=payload.script,
        category=payload.category,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}")
def delete_vocabulary(entry_id: int, db: Session = Depends(get_db)) -> dict:
    entry = db.get(Vocabulary, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")
    db.delete(entry)
    db.commit()
    return {"deleted": entry_id}
