"""The billed eval: one transcription per clip (mine and the course's), checked in code, and one speech call.
Skipped without a key, so the no-key run stays free. Record the output in CHECKS.md.

    export OPENROUTER_API_KEY=...
    python3 -m pytest voice/tests/test_eval.py -v -s     # about $0.002 on the class models
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check import compare

KEY = os.environ.get("OPENROUTER_API_KEY")
pytestmark = pytest.mark.skipif(not KEY, reason="OPENROUTER_API_KEY not set: the billed eval is skipped")
SETS = [p for p in (ROOT / "clips" / "expected.json", ROOT / "clips" / "course" / "expected.json") if p.exists()]
CLIPS = [(s.parent / e["file"], e) for s in SETS for e in json.loads(s.read_text())]


@pytest.fixture(scope="module")
def client():
    from openrouter import OpenRouter
    return OpenRouter(api_key=KEY)


@pytest.mark.parametrize(("clip", "entry"), CLIPS, ids=[str(c.relative_to(ROOT)) for c, _ in CLIPS])
def test_each_clip_transcribes_within_tolerance(client, clip, entry):
    from transcribe import transcribe_file
    if not clip.exists():
        pytest.skip(f"{clip.name} missing")
    r = transcribe_file(client, clip, language=entry.get("language"))
    verdict = compare(entry["text"], r["text"], entry.get("must_contain"), entry.get("max_wer", 0.15))
    print(f"\n{clip.name}: wer={verdict['wer']} missing={verdict['missing']} ${r['cost']}  got={r['text']!r}")
    assert verdict["ok"], verdict


def test_speech_comes_back_as_audio(client, tmp_path):
    from speak import speak
    info = speak(client, "Jeevan Gowda Kumaraswamy built this for CPSC 415.", tmp_path / "eval.mp3")
    print(f"\nspeech: {info['bytes']} bytes, ${info['cost']}")
    assert info["bytes"] > 2000                              # a JSON error body is a few hundred bytes
    head = (tmp_path / "eval.mp3").read_bytes()[:3]
    assert head.startswith(b"ID3") or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")   # MP3 frame sync or ID3 tag
