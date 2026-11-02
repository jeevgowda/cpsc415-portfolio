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

`expected.json` for my clips: I dictated the text in the session and it was typed into the file verbatim,
then committed (`4dcdbe4`) before any model heard the clips.

### Whisper run 1: my clip files were mislabeled (kept as `transcripts-whisper-run1-mislabeled.json`)

| Clip | Model | WER | Missing | Audio s | Cost | Call s |
|---|---|---|---|---|---|---|
| mine-01.m4a (as labeled) | whisper-large-v3-turbo | 0.923 FAIL | Jeevan, 415 | 10.0 | $0.000111 | 0.8 |
| mine-02.m4a (as labeled) | whisper-large-v3-turbo | 1.75 FAIL | Swift | 8.04 | $0.0000268 | 6.9 |
| course/clip-01.wav | whisper-large-v3-turbo | 0.0 ok | — | 6.38 | $0.0000212 | 2.7 |
| course/clip-02.wav | whisper-large-v3-turbo | 0.188 ok (clip tolerance 0.2) | — | 8.061 | $0.0000268 | 1.6 |
| course/clip-03.wav | whisper-large-v3-turbo | 0.0 ok | — | 7.708 | $0.0000257 | 1.9 |

Total $0.00021. The checker caught a pairing error, not a transcription error: `mine-01.m4a` held the
Swift question and `mine-02.m4a` the CPSC 415 question (the 4.2 s file is the short one). I swapped the
**audio filenames** (`6c15e8b`); `expected.json` was not touched.

Run-1 text scored against the corrected pairing (no new call):
- Jeevan clip: got "Jeevan Gowda, what did you learn building Campus Events Navigator for **CBSC** 415? **Thank you.**"
  WER 0.231, FAIL. Name and "415" survived. "CPSC" was heard as "CBSC", and Whisper appended "Thank you."
  to the trailing silence (the same habit as "Music" on course clip 2).
- Swift clip: got "Have you ever shipped **a** mobile app in Swift?" WER 0.125, ok. The extra "a" is either
  a Whisper insertion or a word I said and left out of `expected.json`; I check this by listening.
- The 4.2 s Swift clip was billed as **10.0 s** of audio at $0.000111, about 4× the per-second price of the
  others. It looks like a 10-second minimum on whichever host served that call.

### Whisper run 2 and Scribe (correct pairing)

_(pending)_

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
