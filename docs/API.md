# API Reference

Base path: `/api`. All request/response bodies are JSON unless noted.

## Supported Languages

`GET /api/languages`

```json
{
  "languages": [
    {"code": "en", "name": "English"},
    {"code": "hi", "name": "Hindi"},
    {"code": "hi,en", "name": "Hinglish"}
  ],
  "default_mode": "auto",
  "code_switching_default": true
}
```

## Meetings

### Create
`POST /api/meetings`

```json
{"title": "Sprint planning"}
```

### Upload audio
`POST /api/meetings/{meeting_id}/upload` — `multipart/form-data`, field `file`.

### Transcribe
`POST /api/meetings/{meeting_id}/transcribe`

```json
{
  "language_mode": "auto",
  "code_switching": true,
  "use_custom_vocabulary": true
}
```

`language_mode`: `auto` | `manual:<code>` (e.g. `manual:hi`) | `code-switching`.

### Transcript
`GET /api/meetings/{meeting_id}/transcript`

```json
{
  "meeting_language": "hi,en",
  "segments": [
    {
      "id": 1, "start": 64.0, "end": 69.0,
      "speaker": "SPEAKER_00",
      "text": "Kal tak ye complete kar dena.",
      "language": "hi", "language_label": "Hindi",
      "language_confidence": 0.93, "script": "Devanagari",
      "low_confidence": false
    }
  ],
  "language_switches": [{"at_segment": 3, "from": "hi", "to": "en"}]
}
```

Low-confidence segments include `"warning": "Low transcription confidence for this segment."`.

## Notes / Summary / MoM

`POST /api/meetings/{meeting_id}/notes`

```json
{"kind": "summary", "language": "same"}
```

`kind`: `summary` | `notes` | `mom`.
`language`: `same` | `en` | `hi` | any supported code.

`GET /api/meetings/{meeting_id}/notes` — list generated notes.

## Translation (optional, explicit)

`POST /api/meetings/{meeting_id}/translate`

```json
{"target_language": "hi", "source": "transcript"}
```

`source`: `transcript` | `summary`. Returns translated text as a new `translation`
record. The transcript is never modified.

## Vocabulary / Names

| Method | Path | Body |
|--------|------|------|
| GET | `/api/vocabulary` | — |
| POST | `/api/vocabulary` | `{"term":"Argus","language":"en","script":"Latin","category":"project"}` |
| DELETE | `/api/vocabulary/{id}` | — |

`category`: `technical` | `project` | `person`.

## Settings

`GET /api/settings` / `PUT /api/settings`

```json
{
  "language_mode": "auto",
  "code_switching": true,
  "lang_prob_threshold": 0.6,
  "avg_logprob_threshold": -1.0,
  "no_speech_threshold": 0.6,
  "llm_providers": [
    {"name": "deepseek", "base_url": "https://api.deepseek.com", "api_key": "…", "model": "deepseek-chat"}
  ],
  "llm_default_provider": "deepseek"
}
```

## Evaluation

`POST /api/evaluate`

```json
{"reference": "हमें यह कल करना है", "hypothesis": "हमें यह कल करना है", "language": "hi"}
```

Returns `{"wer": 0.0, "cer": 0.0}`.
