# Product Requirements Document (PRD)
## Multilingual & Code-Switching Support for Meeting Transcription

| Field | Value |
|-------|-------|
| Document | PRD — Multilingual & Code-Switching Support |
| Product | Meeting Transcription & Notes Platform |
| Version | 1.0 |
| Status | Approved for implementation |
| Date | 2026-09-12 |
| Scope | Requirements 51–66 (standalone; sections 1–50 out of scope) |

---

## 1. Overview

Meeting transcription is a **core requirement** of the platform. The system MUST be
multilingual from day one — it must NOT be designed as English-only.

The platform records, transcribes, summarizes, and produces Minutes-of-Meeting (MoM)
from spoken meetings. This PRD defines how the system behaves when meetings contain
one language, multiple languages, or **code-switching** (speakers switching languages
mid-sentence).

### 1.1 Guiding principle

> **TRANSCRIBE WHAT WAS ACTUALLY SPOKEN.**

The default and only correct default behavior is to preserve the original
multilingual speech exactly as it was spoken. The system must never:

- auto-translate mixed-language speech into English;
- auto-convert Hindi speech into English;
- auto-convert regional-language speech into Hindi.

---

## 2. Requirements

### 2.1 RQ-51 — Multilingual Transcription (CORE)

The system MUST support as many languages as the selected speech-to-text (STT) model
reliably supports.

**Supported language set (must include, at minimum):**

| Code | Language | Code | Language |
|------|----------|------|----------|
| en | English | ta | Tamil |
| hi | Hindi | te | Telugu |
| hi,en | Hinglish (code-switched) | kn | Kannada |
| ur | Urdu | ml | Malayalam |
| bn | Bengali | or | Odia |
| gu | Gujarati | as | Assamese |
| mr | Marathi | ne | Nepali |
| pa | Punjabi | … | any other language the STT model supports |

**Acceptance criteria**
- A recording in any listed language is transcribed in that language.
- Additional STT-model languages can be enabled without code changes (data-driven list).

---

### 2.2 RQ-52 — Code-Switching / Mixed Language

The system MUST support conversations where speakers switch languages **within the
same sentence, paragraph, or meeting**.

Examples the system must handle correctly:

| Pattern | Example |
|---------|---------|
| Hindi + English | "Aaj hum API ko deploy karenge, but production mein directly nahi." |
| Gujarati + English | "Aaje database migration karvani chhe, but first testing complete karo." |
| Tamil + English | "Innaiku deployment pannalaam, but first staging check pannunga." |
| Telugu + English | "Ivala API deploy cheddam, but first testing complete cheyyali." |
| Bengali + English | "Aajke deployment korbo, but age staging test korte hobe." |
| Marathi + English | "Aaj deployment karu, but production la direct nahi." |
| Punjabi + English | "Ajj deployment karange, but pehla staging test karo." |

**Rules**
1. Preserve the original mixed-language speech in the transcript.
2. Do NOT auto-translate mixed-language speech.
3. Do NOT auto-convert regional-language speech into Hindi.

**Acceptance criteria**
- Mixed sentences appear verbatim in the transcript, with both languages retained.

---

### 2.3 RQ-53 — Language Detection

The system MUST detect language automatically at three levels where practical:

1. **Meeting level** — the dominant language(s) of the whole meeting.
2. **Speaker level** — the dominant language(s) per speaker.
3. **Segment level** — the language of each transcribed segment.

**Example output**

> Meeting language: **Hindi + English**
>
> `[00:01:04] Speaker 1 [Hindi]:` "Kal tak ye complete kar dena."
> `[00:01:09] Speaker 2 [English]:` "I will finish it today."
> `[00:01:15] Speaker 1 [Hinglish]:` "Okay, then production mein deploy kar dena."

**Rules**
- Detected language is stored as metadata on the meeting, speaker, and segment.
- Segment-level language is authoritative for display; meeting/speaker levels are
  aggregates of the segment-level values.

**Acceptance criteria**
- Every transcript row carries a language label and a confidence score.

---

### 2.4 RQ-54 — Language Switch Detection

The system MUST detect language switches **inside** a conversation and must not
incorrectly classify the whole conversation as a single language.

**Example**

> `[00:02:15] Speaker 1 [Hindi]` "Humne ye feature kal test kiya tha"
> `[00:02:19] Speaker 1 [English]` "but the API response was incorrect."

**Rules**
- A "switch" is recorded when the detected language set changes between consecutive
  segments of the same speaker or across the meeting.
- Switch events are stored as metadata and surfaced in the UI.

**Acceptance criteria**
- Consecutive segments with different languages produce a recorded switch event.
- A meeting containing one Hindi sentence and one English sentence is labeled
  `hi,en` — NOT `hi` and NOT `en`.

---

### 2.5 RQ-55 — Original-Script Preservation

Preserve the script produced by the transcription engine.

| Input | Transcript must remain |
|-------|------------------------|
| Hindi spoken in Hindi | `"हमें इसे कल तक पूरा करना है।"` |
| English | `"We need to finish this by tomorrow."` |
| Mixed | `"हमें API को कल तक deploy करना है।"` |

**Rules**
- Do NOT force every language into Romanized English.
- Where the STT model produces Romanized regional-language text, preserve it rather
  than silently converting it.
- Store a `script` metadata field (e.g. `Devanagari`, `Latin`, `Bengali`, …) computed
  from the transcript text — do not mutate the text itself.

**Acceptance criteria**
- Native-script output and Romanized output are both preserved unchanged.
- The `script` metadata accurately reflects the text.

---

### 2.6 RQ-56 — Romanized Local Languages

The system MUST handle speakers who speak a local language while typing/speaking in
English/Roman text.

| Variant | Example |
|---------|---------|
| Hinglish | "Aaj meeting 4 baje rakhte hain." |
| Romanized Gujarati | "Aaje meeting 4 vagye rakhie." |
| Romanized Tamil | "Innaiku meeting 4 manikku vechukalam." |
| Romanized Telugu | "Ivala meeting 4 ki pettukundam." |

**Rules**
- Romanized regional-language text must NOT be classified as English merely because
  it uses Latin characters.
- Language identification MUST use acoustic/language context (the STT model's
  language-detection signal), not the output script alone.

**Acceptance criteria**
- A Romanized Hinglish segment is labeled `Hinglish`/`hi,en`, not `English`.
- `language` (acoustic) and `script` (text) are stored as separate metadata fields.

---

### 2.7 RQ-57 — Custom Vocabulary by Language

Support multilingual custom vocabulary, including technical/project terms.

**Example entries**

| Language | Terms |
|----------|-------|
| English | FastAPI, PostgreSQL, Flutter |
| Hindi | कर्मचारी |
| Gujarati | કર્મચારી |
| Romanized | karmachari |
| Technical/project | Argus, Pika, Capiche, SCRFD, InsightFace, DeepSort |

**Rules**
- Users can add, edit, and delete custom words/terms.
- Each term carries an optional language, script, and category (`technical`,
  `project`, `person`).
- Terms are injected into the STT pipeline (initial prompt / hot-words) and applied
  as a safe post-processing dictionary.
- Vocabulary is applied per-language where applicable.

**Acceptance criteria**
- Adding a custom term improves its recognition in subsequent transcripts.
- Vocabulary survives restart (persisted).

---

### 2.8 RQ-58 — Names and Proper Nouns

Names must be preserved as accurately as possible.

**Example names**
Nadeem, Neelashi, Amit, Pizza Capiche, Argus, Pika.

**Rules**
- Do NOT translate names.
- Provide an editable vocabulary/person-name dictionary (same mechanism as RQ-57,
  category `person`).
- Names are exempt from any translation step.

**Acceptance criteria**
- A spoken name appears in the transcript as spoken; it is not translated in
  summary/notes/MoM output.

---

### 2.9 RQ-59 — Multilingual AI Notes

The AI notes engine MUST understand multilingual transcripts.

**Example**

> Transcript: "Kal hum deployment karenge, but database migration pehle test karni hai."
>
> Acceptable summary: "Deployment will be done tomorrow after testing the database
> migration."

**Rules**
1. The **original transcript remains unchanged**.
2. The user can choose the notes output language:
   - Same as meeting
   - English
   - Hindi
   - Any user-selected language

**Acceptance criteria**
- Notes can be generated in a language independent of the transcript language.
- Generating notes never mutates the stored transcript.

---

### 2.10 RQ-60 — Translation Must Be Optional

These operations are **separate** and must not be mixed:

| Operation | Question answered |
|-----------|-------------------|
| TRANSCRIPTION | "What was actually said?" |
| TRANSLATION | "What does it mean in another language?" |
| SUMMARY | "What were the important points?" |

**Default deliverable**
1. Original multilingual transcript
2. AI summary

**Optional**
- "Translate transcript" — explicit user action, separate output.

**Acceptance criteria**
- The API exposes three distinct endpoints/actions.
- Translating or summarizing never overwrites the transcript.

---

### 2.11 RQ-61 — Multilingual Summary

If a meeting contains multiple languages, the summary engine must understand **all**
supported languages.

**Example**

> Speaker 1: "Kal deploy karenge."
> Speaker 2: "Okay, but আগে staging test করতে হবে."

The AI must understand the second sentence contains Bengali and correctly capture
the meaning: *deployment is tomorrow, but staging testing must happen first*.

**Rules**
- Never ignore non-English sections when generating summaries/notes/MoM.

**Acceptance criteria**
- Summary/notes/MoM reflect the meaning of non-English sections.

---

### 2.12 RQ-62 — Accuracy Evaluation by Language

Do NOT claim language support merely because a model lists the language. Support must
be **measured**.

**Metrics**
- WER (Word Error Rate)
- CER (Character Error Rate)
- Language detection accuracy
- Speaker diarization quality (DER)

**Benchmark categories**

| Single language | Mixed language |
|-----------------|----------------|
| English | Hindi + English |
| Hindi | Gujarati + English |
| Hinglish | Tamil + English |
| Gujarati | Telugu + English |
| Tamil | Bengali + English |
| Telugu | Marathi + English |
| Bengali | Punjabi + English |
| Marathi | |
| Punjabi | |
| Malayalam | |
| Kannada | |
| Urdu | |

**Rules**
- Models/configurations are selected based on **measured** performance, not marketing
  claims.

**Acceptance criteria**
- A benchmark script computes and reports WER/CER/LID-accuracy/DER per category.

---

### 2.13 RQ-63 — Multilingual Quality Warning

If the system detects low confidence for a language or mixed-language segment, it
MUST display:

> "Low transcription confidence for this segment."

**Rules**
- Do NOT invent missing words (no hallucination fill).
- Low confidence is derived from STT signals (language probability, average log
  probability, no-speech probability) compared against configurable thresholds.

**Acceptance criteria**
- Low-confidence segments are flagged and surfaced with the warning text.
- The transcript is never padded with invented content.

---

### 2.14 RQ-64 — Language Settings

The user must be able to choose:

**Mode**
- `Auto Detect`
- Manual selection: English, Hindi, Gujarati, Tamil, Telugu, Bengali, Marathi,
  Punjabi, Kannada, Malayalam, Urdu, other supported languages.

**Toggle**
- `Mixed / Code-Switching Mode` (enabled/disabled)

**Recommended default**
- `AUTO` + `CODE-SWITCHING ENABLED`

**Acceptance criteria**
- Settings are persisted and respected by the transcription pipeline.

---

### 2.15 RQ-65 — Database Language Metadata

Store the following metadata fields:

| Field | Example |
|-------|---------|
| `meeting_language` | `"hi,en"` |
| `segment_language` | `"hi"` |
| `segment_language` (mixed) | `"hi,en"` |
| `speaker_language` | `"en"` |
| `language_confidence` | `0.92` |

**Acceptance criteria**
- Every meeting, segment, and speaker record contains the language metadata above.

---

### 2.16 RQ-66 — Multilingual Acceptance Test

The product is **NOT** considered multilingual-ready unless it successfully processes
real recordings containing:

- English
- Hindi
- Hinglish
- at least several regional Indian languages
- mixed-language sentences
- multiple speakers
- technical vocabulary
- different accents

**Rules**
- The system must preserve original meaning.
- The system must distinguish `transcription`, `translation`, and `summary` as
  separate operations.

**Acceptance criteria**
- An automated acceptance suite covers all the above dimensions.
- Transcription, translation, and summary are verified as independent outputs.

---

## 3. Requirements Traceability

| Requirement | Component | Test(s) |
|-------------|-----------|---------|
| RQ-51 | `stt/engine.py`, `routes/languages.py` | unit, integration |
| RQ-52 | `stt/engine.py`, `stt/language.py` | unit, acceptance |
| RQ-53 | `stt/language.py`, `models.py` | unit |
| RQ-54 | `stt/language.py` (`detect_language_switches`) | unit |
| RQ-55 | `stt/language.py` (`detect_script`), transcript route | unit |
| RQ-56 | `stt/language.py` (LID vs script separation) | unit |
| RQ-57 | `stt/vocab.py`, `routes/vocabulary.py` | unit, integration |
| RQ-58 | `stt/vocab.py`, `ai/translate.py` (name exemption) | unit |
| RQ-59 | `ai/notes.py` | integration |
| RQ-60 | `routes/transcript.py`, `routes/notes.py`, `routes/translate.py` | integration, acceptance |
| RQ-61 | `ai/notes.py` | integration, acceptance |
| RQ-62 | `benchmarks/run_benchmarks.py` | benchmark |
| RQ-63 | `stt/language.py` (confidence), transcript route | unit |
| RQ-64 | `routes/settings.py`, `frontend` | integration |
| RQ-65 | `models.py` | unit |
| RQ-66 | `tests/acceptance/` | acceptance |

---

## 4. Non-Goals / Out of Scope

- Requirements 1–50 (handled elsewhere; this PRD is standalone).
- Real-time streaming transcription.
- Native mobile applications.
- Fine-tuning custom STT models beyond Whisper variants.
- Automatic translation of transcripts as a default behavior (translation is optional
  and explicit only).
