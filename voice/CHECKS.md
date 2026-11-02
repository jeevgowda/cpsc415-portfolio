# Week 7 checks: the spoken interface

**Chatbot status.** The portfolio chatbot does not exist yet (the November 2 milestone). The loop here is
the course example's server (`examples/voice-loop/server.py`) adapted to answer from my own
`profile.json` (spec sections 1–2) instead of the example's fictional profile. `answer()` moves into the
FastAPI app unchanged when the chatbot exists, before November 30.

Models: transcription `openai/whisper-large-v3-turbo` (class) vs `elevenlabs/scribe-v2`;
speech `microsoft/mai-voice-2.1-flash` with `en-US-Harper` (class) vs `en-IN-Priya`; chat `minimax/minimax-m3`.

## No-key tests

`pytest voice/tests/test_check.py` before `check.py` existed: collection error,
`ModuleNotFoundError: No module named 'check'` (red, as intended).

First run with `check.py` written: 8 passed, 2 failed. Both failures were the **test's** mistake: the test
sentence "My name is Jeevan Gowda and I built Campus Events Navigator for CPSC 415." has 14 words, not 13,
so 1/14 was compared with 1/13. Fixed the sentence to 13 words ("I am Jeevan Gowda …"), not the code.
Second run: **10 passed in 0.02s**.

`pytest voice/tests` with no key: 10 passed, 4 skipped (the billed eval).

## Linter (`ruff check .`)

| Finding | Where | What I did |
|---|---|---|
| FURB167 `re.M` alias | `voice/check.py` | Changed to `re.MULTILINE`. |
| I001 imports unsorted (×2) | `voice/server.py`, `voice/transcribe.py` | Ruff treated the local modules `check`, `speak`, `transcribe` as third-party. Added `ruff.toml` with `src = ["voice"]`; no code change. |
| PIE810 `startswith` twice | `.claude/hooks/guard.py` | Left as is: the course's guard is copied verbatim. |

## Transcription: per clip, per model

_(pending: needs my clips, `clips/expected.json`, and the key)_

| Clip | Model | WER | Missing | Audio s | Cost | Call s |
|---|---|---|---|---|---|---|

Which model got my name right, and what I heard when I played each clip: _(pending)_

## The answer, spoken twice

_(pending)_

| Voice | Chars | Bytes | Est. cost | Call s | My name | "CPSC 415" | Abbreviations |
|---|---|---|---|---|---|---|---|

## Browser check

_(pending: `python3 -m pytest test_browser.py -v -s` with the server up; the last three assertions)_

## One turn

_(pending: one live microphone question: transcript, answer, three costs, total)_
