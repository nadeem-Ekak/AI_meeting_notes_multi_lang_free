# Benchmark Fixtures

For **real** benchmark and acceptance runs (RQ-62 / RQ-66), place recordings and
reference transcripts here.

## Audio

`tests/fixtures/audio/<category>.wav` — one recording per category.

Categories (single): `en`, `hi`, `gu`, `ta`, `te`, `bn`, `mr`, `pa`, `ml`, `kn`, `ur`.

Categories (mixed): `hi-en`, `gu-en`, `ta-en`, `te-en`, `bn-en`, `mr-en`, `pa-en`.

## Reference transcripts

`tests/fixtures/refs/<category>.txt` — verbatim ground-truth transcript (UTF-8) for
the corresponding audio file.

## Synthetic fixtures (CI)

Run this to generate synthetic TTS audio for reproducibility:

```powershell
python - <<'PY'
import asyncio, edge_tts

async def gen(text, out):
    tts = edge_tts.Communicate(text, voice="en-IN-NeerjaNeural")
    await tts.save(out)

asyncio.run(gen("Aaj hum API ko deploy karenge, but production mein directly nahi.", "hi-en.wav"))
PY
```

Synthetic TTS is a smoke-test aid; final acceptance (RQ-66) should use **real
recordings** with different accents and multiple speakers.
