"""Audio in, text out, through OpenRouter's transcription endpoint (POST /api/v1/audio/transcriptions).

    python3 transcribe.py clips/mine-01.wav                                      # needs OPENROUTER_API_KEY
    python3 transcribe.py clips/mine-01.wav --expect "what I actually said"      # adds the checker's verdict
    python3 transcribe.py --set clips/expected.json clips/course/expected.json --out transcripts-whisper.json
    python3 transcribe.py --set clips/expected.json clips/course/expected.json --model elevenlabs/scribe-v2 --out transcripts-scribe.json

The audio travels as base64 in JSON; the reply is JSON with the text and usage (audio seconds, cost).
Spec section 4, transcriber component. Adapted from the course's examples/voice-loop/transcribe.py.
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

from openrouter import OpenRouter

from check import compare

DEFAULT_MODEL = "openai/whisper-large-v3-turbo"     # priced per second of audio
FORMATS = {".mp3": "mp3", ".wav": "wav", ".m4a": "m4a", ".webm": "webm", ".ogg": "ogg", ".flac": "flac", ".aac": "aac"}


def transcribe(client: OpenRouter, audio: bytes, fmt: str, model: str = DEFAULT_MODEL, language: str | None = None) -> dict:
    """One STT call. Returns the text and what CHECKS.md records: audio seconds, cost, wall-clock seconds."""
    t0 = time.time()
    kwargs = {"language": language} if language else {}
    r = client.stt.create_transcription(model=model, input_audio={"data": base64.b64encode(audio).decode(), "format": fmt}, **kwargs)
    u = r.usage
    return {"text": r.text, "model": model, "audio_seconds": u.seconds if u else None,
            "cost": u.cost if u else None, "seconds": round(time.time() - t0, 1)}


def transcribe_file(client: OpenRouter, path: Path, model: str = DEFAULT_MODEL, language: str | None = None) -> dict:
    fmt = FORMATS.get(path.suffix.lower())
    if not fmt:
        raise ValueError(f"{path}: unknown audio format; one of {sorted(FORMATS)}")
    return transcribe(client, path.read_bytes(), fmt, model, language)


def transcribe_set(client: OpenRouter, expected_path: Path, model: str = DEFAULT_MODEL, language: str | None = None) -> list[dict]:
    """Every clip in one expected.json: transcribe once, check in code, print one line each."""
    results = []
    for entry in json.loads(expected_path.read_text()):
        clip = expected_path.parent / entry["file"]
        r = transcribe_file(client, clip, model, language or entry.get("language"))
        r["file"] = str(clip)
        r["expected"] = entry["text"]
        r["check"] = compare(entry["text"], r["text"], entry.get("must_contain"), entry.get("max_wer", 0.15))
        results.append(r)
        v = r["check"]
        print(f"{clip}: {'ok' if v['ok'] else 'FAIL'}  wer={v['wer']}  missing={v['missing']}  "
              f"{r['audio_seconds']}s audio  ${r['cost']}  {r['seconds']}s\n    got: {r['text']!r}")
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", nargs="?", type=Path)
    ap.add_argument("--set", type=Path, nargs="+", help="one or more expected.json files (file, text, must_contain per clip)")
    ap.add_argument("--expect", help="what was said, for the checker")
    ap.add_argument("--model", default=os.environ.get("STT_MODEL", DEFAULT_MODEL))
    ap.add_argument("--language", help="ISO-639-1 hint, e.g. en, hi, kn; omitted means auto-detect")
    ap.add_argument("--out", type=Path, default=Path("transcripts.json"))
    a = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; nothing was billed.")
    client = OpenRouter(api_key=key)
    if a.set:
        results = [r for s in a.set for r in transcribe_set(client, s, a.model, a.language)]
        a.out.write_text(json.dumps(results, indent=2))
        total = sum(r["cost"] or 0 for r in results)
        print(f"{len(results)} clips, ${total:.5f} total, written to {a.out}")
    elif a.audio:
        r = transcribe_file(client, a.audio, a.model, a.language)
        print(f"{r['text']}\n[{r['model']}  {r['audio_seconds']}s audio  ${r['cost']}  {r['seconds']}s]")
        if a.expect:
            print("check:", compare(a.expect, r["text"]))
    else:
        ap.error("give an audio file or --set expected.json")
