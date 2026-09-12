"""Evaluation endpoint: WER/CER on a reference/hypothesis pair (RQ-62)."""
from __future__ import annotations

from fastapi import APIRouter

from ..schemas import EvaluateOut, EvaluateRequest

router = APIRouter(prefix="/evaluate", tags=["evaluate"])


@router.post("", response_model=EvaluateOut)
def evaluate(payload: EvaluateRequest) -> EvaluateOut:
    import jiwer  # imported lazily

    wer = float(jiwer.wer(payload.reference, payload.hypothesis))
    cer = float(jiwer.cer(payload.reference, payload.hypothesis))
    return EvaluateOut(wer=round(wer, 4), cer=round(cer, 4), language=payload.language)
