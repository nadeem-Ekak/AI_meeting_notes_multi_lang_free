# Benchmarks
## Accuracy Evaluation by Language (RQ-62)

Language support is **measured**, never assumed from a model's advertised language
list.

## Metrics

| Metric | Tool | Meaning |
|--------|------|---------|
| WER | `jiwer` | Word Error Rate vs. reference transcript |
| CER | `jiwer` | Character Error Rate vs. reference transcript |
| LID accuracy | in-house | Fraction of segments whose predicted language code matches reference |
| DER | `pyannote.metrics` (optional) | Diarization Error Rate (speaker assignment quality) |

## Categories

**Single language:** English, Hindi, Hinglish, Gujarati, Tamil, Telugu, Bengali,
Marathi, Punjabi, Malayalam, Kannada, Urdu.

**Mixed language:** Hindi+English, Gujarati+English, Tamil+English, Telugu+English,
Bengali+English, Marathi+English, Punjabi+English.

## Fixture Sources

1. **Synthetic TTS** (edge-tts) — generated deterministically for CI reproducibility.
2. **Real recordings** — user-provided, placed in `tests/fixtures/audio/` with a
   reference transcript in `tests/fixtures/refs/`.

## Running

```powershell
python benchmarks/run_benchmarks.py --engine fake
python benchmarks/run_benchmarks.py --engine faster-whisper --categories hi,en,hi-en
```

Output is written to `benchmarks/results/benchmark_report.md`.

## Model Selection Policy

A language is only listed as "supported" in the product UI after its benchmark
WER/CER falls below agreed thresholds in the acceptance gate (RQ-66). Configurations
are chosen from measured results, not marketing claims.
