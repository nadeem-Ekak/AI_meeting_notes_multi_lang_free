"""Integration tests for the API (mocked STT + fake LLM)."""
from __future__ import annotations

from app.stt.engine import STTSegment


def test_create_meeting(client):
    meeting = client.post("/api/meetings", json={"title": "Sprint"}).json()
    assert meeting["title"] == "Sprint"
    assert meeting["status"] == "created"


def test_upload_audio(client, create_meeting):
    res = client.post(
        f"/api/meetings/{create_meeting}/upload",
        files={"file": ("audio.wav", b"fake-audio", "audio/wav")},
    )
    assert res.status_code == 200
    assert "audio_path" in res.json()


def test_transcribe_and_transcript_metadata(client, upload_and_transcribe):
    meeting_id = upload_and_transcribe(
        [
            STTSegment(0.0, 3.0, "We need to finish this by tomorrow.", "en", 0.98),
            STTSegment(3.0, 6.0, "कल तक ये पूरा करना है।", "hi", 0.95),
        ]
    )
    data = client.get(f"/api/meetings/{meeting_id}/transcript").json()
    assert data["meeting_language"] == "en,hi"
    assert len(data["segments"]) == 2
    hindi = data["segments"][1]
    assert hindi["language"] == "hi"
    assert hindi["language_label"] == "Hindi"
    assert hindi["script"] == "Devanagari"
    assert hindi["low_confidence"] is False


def test_language_switch_detection(client, upload_and_transcribe):
    meeting_id = upload_and_transcribe(
        [
            STTSegment(0.0, 2.0, "Humne ye feature kal test kiya tha", "hi", 0.9),
            STTSegment(2.0, 4.0, "but the API response was incorrect.", "en", 0.9),
        ]
    )
    data = client.get(f"/api/meetings/{meeting_id}/transcript").json()
    assert data["language_switches"] == [
        {"at_segment": 1, "from_lang": "hi", "to_lang": "en"}
    ]


def test_low_confidence_warning(client, upload_and_transcribe):
    meeting_id = upload_and_transcribe(
        [STTSegment(0.0, 2.0, "unclear audio", "en", 0.3)]
    )
    data = client.get(f"/api/meetings/{meeting_id}/transcript").json()
    seg = data["segments"][0]
    assert seg["low_confidence"] is True
    assert seg["warning"] == "Low transcription confidence for this segment."


def test_notes_generation_keeps_transcript_unchanged(client, upload_and_transcribe):
    meeting_id = upload_and_transcribe(
        [STTSegment(0.0, 2.0, "Aaj deployment karenge", "hi", 0.9)]
    )
    before = client.get(f"/api/meetings/{meeting_id}/transcript").json()

    note = client.post(
        f"/api/meetings/{meeting_id}/notes", json={"kind": "summary", "language": "same"}
    ).json()
    assert note["content"] == "FAKE_RESPONSE"

    after = client.get(f"/api/meetings/{meeting_id}/transcript").json()
    assert [s["text"] for s in before["segments"]] == [s["text"] for s in after["segments"]]


def test_translate_is_separate_record(client, upload_and_transcribe):
    meeting_id = upload_and_transcribe(
        [STTSegment(0.0, 2.0, "Kal deploy karenge", "hi", 0.9)]
    )
    result = client.post(
        f"/api/meetings/{meeting_id}/translate",
        json={"target_language": "en", "source": "transcript"},
    ).json()
    assert result["content"] == "FAKE_RESPONSE"
    assert result["target_language"] == "en"

    notes = client.get(f"/api/meetings/{meeting_id}/notes").json()
    kinds = [n["kind"] for n in notes]
    assert "translation" in kinds


def test_vocabulary_crud(client):
    created = client.post(
        "/api/vocabulary", json={"term": "Argus", "category": "project"}
    ).json()
    assert created["term"] == "Argus"
    assert created["category"] == "project"

    entries = client.get("/api/vocabulary").json()
    assert any(e["term"] == "Argus" for e in entries)

    assert client.delete(f"/api/vocabulary/{created['id']}").status_code == 200
    assert client.get("/api/vocabulary").json() == []


def test_settings_defaults(client):
    s = client.get("/api/settings").json()
    assert s["language_mode"] == "auto"
    assert s["code_switching"] is True
    assert s["llm_default_provider"] == "deepseek"


def test_languages_endpoint(client):
    data = client.get("/api/languages").json()
    codes = {l["code"] for l in data["languages"]}
    assert {"en", "hi", "hi,en", "ta", "te", "bn"} <= codes


def test_evaluate_endpoint(client):
    res = client.post(
        "/api/evaluate",
        json={"reference": "हमें यह कल करना है", "hypothesis": "हमें यह कल करना है"},
    ).json()
    assert res["wer"] == 0.0
    assert res["cer"] == 0.0
