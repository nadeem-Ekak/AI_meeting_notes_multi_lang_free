"""RQ-66 — Multilingual acceptance gate.

Verifies the pipeline handles realistic multilingual input (English, Hindi, Hinglish,
mixed sentences, multiple speakers, technical vocabulary) and that transcription,
translation, and summary remain SEPARATE operations with the original transcript
preserved verbatim.
"""
from __future__ import annotations

from app.stt.engine import STTSegment


def test_multilingual_acceptance(client, upload_and_transcribe):
    original_texts = [
        "We need to finish this by tomorrow.",
        "कल तक ये complete करना है।",
        "Okay, then production mein deploy kar dena.",
        "Argus aur Pika integration check karo.",
    ]
    meeting_id = upload_and_transcribe(
        [
            STTSegment(0.0, 3.0, original_texts[0], "en", 0.98),
            STTSegment(3.0, 6.0, original_texts[1], "hi", 0.95),
            STTSegment(6.0, 9.0, original_texts[2], "hi", 0.90),
            STTSegment(9.0, 12.0, original_texts[3], "hi", 0.88),
        ]
    )

    # 1) Original meaning preserved — transcript text is verbatim.
    transcript = client.get(f"/api/meetings/{meeting_id}/transcript").json()
    assert transcript["meeting_language"] == "en,hi"
    assert [s["text"] for s in transcript["segments"]] == original_texts

    # 2) Mixed-language metadata present.
    labels = {s["language_label"] for s in transcript["segments"]}
    assert labels == {"English", "Hindi"}

    # 3) SUMMARY is a separate operation and does not touch the transcript.
    summary = client.post(
        f"/api/meetings/{meeting_id}/notes", json={"kind": "summary", "language": "same"}
    ).json()
    assert summary["content"] == "FAKE_RESPONSE"
    after_summary = client.get(f"/api/meetings/{meeting_id}/transcript").json()
    assert [s["text"] for s in after_summary["segments"]] == original_texts

    # 4) TRANSLATION is a separate operation and does not touch the transcript.
    translation = client.post(
        f"/api/meetings/{meeting_id}/translate",
        json={"target_language": "hi", "source": "transcript"},
    ).json()
    assert translation["content"] == "FAKE_RESPONSE"
    after_translate = client.get(f"/api/meetings/{meeting_id}/transcript").json()
    assert [s["text"] for s in after_translate["segments"]] == original_texts

    # 5) Transcription / summary / translation are distinct records.
    notes = client.get(f"/api/meetings/{meeting_id}/notes").json()
    kinds = {n["kind"] for n in notes}
    assert "summary" in kinds
    assert "translation" in kinds
    assert len(notes) == 2  # exactly one summary and one translation
