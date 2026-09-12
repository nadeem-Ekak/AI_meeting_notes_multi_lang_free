# Test Plan
## Multilingual Meeting Transcription Platform

## 1. Strategy

Testing follows a pyramid with a strong multilingual/benchmark layer because language
support is a **core requirement** (RQ-51) that must be **measured** (RQ-62), not
assumed.

```
        ┌───────────────┐
        │  Acceptance    │  RQ-66 end-to-end gate
        ├───────────────┤
        │  Benchmarks    │  WER / CER / LID / DER per language
        ├───────────────┤
        │  Integration   │  API endpoints (mocked STT + LLM)
        ├───────────────┤
        │  Unit          │  language / script / vocab / schemas
        └───────────────┘
```

CI runs **without** downloading models or calling external APIs: unit and integration
tests use `MockTranscriptionEngine` and a fake LLM. Benchmark and real-acceptance runs
are executed explicitly with `--engine faster-whisper`.

## 2. Unit Tests (`tests/unit/`)

| File | Covers |
|------|--------|
| `test_language.py` | script detection (Devanagari/Latin/Bengali/…), meeting language aggregation, speaker language, switch detection, confidence flags, `hi,en` → "Hinglish" label |
| `test_vocab.py` | initial-prompt/hot-words building, safe post-processing substitution, name exemption |
| `test_schemas.py` | request/response validation for language metadata |

Key cases (RQ-driven):
- RQ-52/54: mixed sentence preserved verbatim; switch event recorded.
- RQ-55: Devanagari text → `script=Devanagari`, text unchanged.
- RQ-56: Latin-script segment with acoustic LID `hi` → labeled `Hindi`, not English.
- RQ-63: low `language_probability` → `low_confidence=True`.

## 3. Integration Tests (`tests/integration/`)

FastAPI `TestClient` with dependency overrides (fake STT, fake LLM, SQLite in-memory).

- Create meeting, upload audio, transcribe → transcript persisted with language
  metadata (RQ-65).
- GET transcript → contains `[lang]` tags and confidence warnings.
- POST notes with target language `hi` → returns Hindi content; transcript unchanged
  (RQ-59, RQ-60).
- POST translate → separate output; transcript unchanged (RQ-60).
- Vocabulary CRUD → add "Argus"; subsequent transcribe applies it (RQ-57/58).
- Settings: set language mode `auto` + code-switching default (RQ-64).

## 4. Benchmark Suite (`benchmarks/run_benchmarks.py`)

Computes, per category:

- **WER / CER** via `jiwer`.
- **Language detection accuracy** — fraction of segments whose predicted code matches
  reference.
- **Speaker diarization quality (DER)** via `pyannote.metrics` (optional).

**Categories (RQ-62)**

| Single | Mixed |
|--------|-------|
| English, Hindi, Hinglish, Gujarati, Tamil, Telugu, Bengali, Marathi, Punjabi, Malayalam, Kannada, Urdu | Hindi+English, Gujarati+English, Tamil+English, Telugu+English, Bengali+English, Marathi+English, Punjabi+English |

**Inputs**
- Synthetic TTS fixtures (edge-tts) for reproducibility in CI.
- Slot for user-provided **real recordings** (ground truth from `tests/fixtures/`).

**Output**
- Markdown/terminal table of metrics per category; saved under
  `benchmarks/results/`.

## 5. Acceptance Test (RQ-66) (`tests/acceptance/`)

`test_multilingual_acceptance.py` runs the full pipeline on fixture audio and asserts:

1. Realistic multilingual input (English, Hindi, Hinglish, several regional languages,
   mixed sentences, multiple speakers, technical vocabulary, accents) is processed.
2. Original meaning is preserved — transcript text is verbatim.
3. **Transcription**, **translation**, and **summary** are distinct outputs:
   - transcript unchanged after generating notes;
   - translation is a separate record from transcript;
   - summary does not overwrite transcript.

Fixture audio is generated synthetically for CI; a real-recording mode
(`REAL_FIXTURES_DIR` env var) runs against user-provided recordings for the final gate.

## 6. Running Tests

```powershell
cd backend
pip install -r requirements.txt
pytest                              # unit + integration + acceptance (no model/network)
pytest tests/unit -q                # unit only
pytest tests/acceptance -q          # acceptance only
python benchmarks/run_benchmarks.py --engine fake          # harness smoke test
python benchmarks/run_benchmarks.py --engine faster-whisper --categories hi,en,hi-en
```
