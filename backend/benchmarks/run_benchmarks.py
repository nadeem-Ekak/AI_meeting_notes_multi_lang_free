"""Benchmark harness (RQ-62): WER / CER / language-detection accuracy per category.

Two engines:
  --engine fake            Offline demo; reference == hypothesis (scores 0) to prove
                           the harness runs end-to-end without a model.
  --engine faster-whisper  Real run against fixture audio + reference transcripts.

Usage:
    python benchmarks/run_benchmarks.py --engine fake
    python benchmarks/run_benchmarks.py --engine faster-whisper --categories hi,en,hi-en
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.stt import language as lang  # noqa: E402

SINGLE_CATEGORIES: dict[str, str] = {
    "en": "en", "hi": "hi", "gu": "gu", "ta": "ta", "te": "te",
    "bn": "bn", "mr": "mr", "pa": "pa", "ml": "ml", "kn": "kn", "ur": "ur",
}
MIXED_CATEGORIES: dict[str, str] = {
    "hi-en": "hi,en", "gu-en": "gu,en", "ta-en": "ta,en", "te-en": "te,en",
    "bn-en": "bn,en", "mr-en": "mr,en", "pa-en": "pa,en",
}
ALL_CATEGORIES = {**SINGLE_CATEGORIES, **MIXED_CATEGORIES}

SAMPLE_SENTENCES: dict[str, str] = {
    "en": "We will deploy the API tomorrow after testing.",
    "hi": "हम कल API को deploy करेंगे, पहले testing करनी है।",
    "hi-en": "Aaj hum API ko deploy karenge, but production mein directly nahi.",
    "gu-en": "Aaje database migration karvani chhe, but first testing complete karo.",
    "ta-en": "Innaiku deployment pannalaam, but first staging check pannunga.",
    "te-en": "Ivala API deploy cheddam, but first testing complete cheyyali.",
    "bn-en": "Aajke deployment korbo, but age staging test korte hobe.",
    "mr-en": "Aaj deployment karu, but production la direct nahi.",
    "pa-en": "Ajj deployment karange, but pehla staging test karo.",
}


def _codes_equal(detected: str | None, expected: str) -> bool:
    return set(lang.split_codes(detected)) == set(expected.split(","))


def compute_metrics(reference: str, hypothesis: str, expected_lang: str, detected_lang: str | None) -> dict:
    import jiwer

    wer = float(jiwer.wer(reference, hypothesis))
    cer = float(jiwer.cer(reference, hypothesis))
    lid_accuracy = 1.0 if _codes_equal(detected_lang, expected_lang) else 0.0
    return {"wer": round(wer, 4), "cer": round(cer, 4), "lid_accuracy": lid_accuracy}


def run_fake(categories: list[str]) -> list[dict]:
    rows: list[dict] = []
    for cat in categories:
        reference = SAMPLE_SENTENCES.get(cat, f"sample {cat}")
        rows.append(
            {
                "category": cat,
                "expected_language": ALL_CATEGORIES.get(cat, cat),
                **compute_metrics(reference, reference, ALL_CATEGORIES.get(cat, cat), ALL_CATEGORIES.get(cat, cat)),
            }
        )
    return rows


def run_faster_whisper(categories: list[str]) -> list[dict]:
    from app.stt.engine import FasterWhisperEngine

    audio_dir = ROOT / "tests" / "fixtures" / "audio"
    refs_dir = ROOT / "tests" / "fixtures" / "refs"
    engine = FasterWhisperEngine()

    rows: list[dict] = []
    for cat in categories:
        audio_path = audio_dir / f"{cat}.wav"
        ref_path = refs_dir / f"{cat}.txt"
        if not audio_path.exists() or not ref_path.exists():
            rows.append(
                {
                    "category": cat,
                    "expected_language": ALL_CATEGORIES.get(cat, cat),
                    "wer": None,
                    "cer": None,
                    "lid_accuracy": None,
                    "error": f"missing fixture {audio_path.name} or {ref_path.name}",
                }
            )
            continue

        reference = ref_path.read_text(encoding="utf-8").strip()
        segments = engine.transcribe(str(audio_path), language_mode="auto")
        hypothesis = " ".join(s.text for s in segments).strip()
        detected = lang.detect_meeting_language(segments)
        rows.append(
            {
                "category": cat,
                "expected_language": ALL_CATEGORIES.get(cat, cat),
                **compute_metrics(reference, hypothesis, ALL_CATEGORIES.get(cat, cat), detected),
            }
        )
    return rows


def write_report(rows: list[dict], engine: str) -> Path:
    out_dir = ROOT / "benchmarks" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "benchmark_report.md"

    lines = ["# Benchmark Report", "", f"Engine: `{engine}`", "", "| Category | Expected | WER | CER | LID accuracy |", "|---|---|---|---|---|"]
    for row in rows:
        if "error" in row:
            lines.append(f"| {row['category']} | {row['expected_language']} | — | — | — ({row['error']}) |")
        else:
            lines.append(
                f"| {row['category']} | {row['expected_language']} | {row['wer']} | {row['cer']} | {row['lid_accuracy']} |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=["fake", "faster-whisper"], default="fake")
    parser.add_argument("--categories", default=",".join(ALL_CATEGORIES))
    args = parser.parse_args()

    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    rows = run_fake(categories) if args.engine == "fake" else run_faster_whisper(categories)
    report = write_report(rows, args.engine)

    print(f"{'Category':<10} {'WER':>8} {'CER':>8} {'LID':>5}")
    for row in rows:
        if "error" in row:
            print(f"{row['category']:<10} {'—':>8} {'—':>8} {'—':>5}  ({row['error']})")
        else:
            print(f"{row['category']:<10} {row['wer']:>8} {row['cer']:>8} {row['lid_accuracy']:>5}")
    print(f"\nReport written to {report}")


if __name__ == "__main__":
    main()
