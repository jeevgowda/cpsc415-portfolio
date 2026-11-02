# Plan

## Week 7: spoken interface

Implements `spec.md` section 4 ("Week 7: spoken interface") for `intent/voice.md`.

### Files under `voice/`

| File | What it is |
|---|---|
| `check.py` | The checker, plain code with no key: `words`, `wer`, `compare` (behaviors 1, 3, 4) and `for_speech` (behavior 5). |
| `tests/test_check.py` | No-key tests of the checker. Written first and seen to fail. |
| `transcribe.py` | The transcriber: one clip or an `expected.json` set, with `--model`, `--language`, `--out`. |
| `speak.py` | The speaker: text to MP3 (or WAV), refusing non-audio replies (behavior 2). |
| `tests/test_eval.py` | The billed eval, skipped when `OPENROUTER_API_KEY` is not set. |
| `clips/` | My two clips plus `expected.json`, which I write before any model hears them. |
| `clips/course/` | The course's three fixture clips and their `expected.json`, copied unchanged as a baseline no person spoke. |
| `transcripts-whisper.json`, `transcripts-scribe.json` | Both models' output on every clip. |
| `answer-harper.mp3`, `answer-priya.mp3` | The answer to my first clip, spoken twice. |
| `server.py`, `index.html` | The loop: `/api/voice`, `/api/ask`, the recorder page. |
| `test_browser.py` | The Playwright browser check, run with the server up. |
| `CHECKS.md` | Every measured result, by step. |

`profile.json` at the repository root holds my profile (spec sections 1 and 2), and the answer step reads it.

### Order of work

1. Checker: tests first (`tests/test_check.py`), run and see them fail, then write `check.py`,
   run and see them pass, then `ruff check .`. Commit.
2. Transcriber and speaker (`transcribe.py`, `speak.py`) and the key-gated eval
   (`tests/test_eval.py`). Without a key, the eval reports *skipped*.
3. My clips: I record two clips and write `clips/expected.json` **before** transcribing. Then all
   five clips go through Whisper and Scribe once each. Results go in `CHECKS.md`. Commit.
4. The answer to clip 1, spoken with Harper and with Priya. Results go in `CHECKS.md`. Commit.
5. The loop: `server.py` and `index.html`, the browser check, one live microphone turn, and the
   **One turn** section of `CHECKS.md`. Commit, tag `week07-submitted`, push.

### Risks

- **The transcriber changes my name** (for example "Gowda" → "Gouda", "Kumaraswamy" → "Kumara
  Swami"). *What the chatbot does:* it answers the question as heard. A question about "Jeevan
  Gouda" still finds no other person in the profile, so the grounding rule keeps the answer honest,
  but a question that depended on the misheard word may get "I don't know". *Which test notices:*
  `compare()` with `must_contain` reports the missing word by name even when the rate is under
  0.15 (`test_names_that_must_survive_are_checked_separately`). On the live page, the
  "You said:" line shows it to the visitor.
- **Cost of one turn, and a held button.** On the class models, one turn is about $0.004–0.006:
  transcription about $0.00003, chat about $0.0005, speech about $0.003–0.005 (per character of
  the answer). A visitor who holds the button for a minute adds only about $0.0003 of
  transcription, because the answer is still at most three sentences. The real risk is many turns
  in a row, and that is a rate-limit question for the hosting decision. The page stops recording
  at 30 seconds, and the server reads at most 10 MB.
- **A format the model rejects.** The server answers 415 to any content type outside its
  `FORMATS` table. If the provider rejects a format the table allows, the server returns 502 with
  the provider's message (never the key), and the page shows it.
- **MP3 headers with a wrong length** (course setup, section 3): the fixture clips are WAV.
- **A speech reply that is JSON** (wrong voice id): `speak.py` raises and saves nothing (behavior 2).

### Proof

**No-key tests** (`pytest voice/tests/test_check.py`; free, under a second, run on every change):

| Test | Proves |
|---|---|
| perfect transcript scores 0, ignoring case and punctuation | the rate measures words, not formatting |
| one substituted word in thirteen scores 1/13 | the edit-distance arithmetic |
| empty or `None` reply scores 1.0, `ok: false`, `empty: true`, no exception | behavior 1 |
| a missing name is reported even within tolerance | behavior 4 |
| a number read as words is a miss | behavior 4 |
| spacing and case do not count in `must_contain` | behavior 4 |
| `for_speech` keeps at most three sentences and removes markdown | behavior 5 |

**The billed eval** (needs `OPENROUTER_API_KEY`; run by hand, once per step, never in a loop):

| Run | Proves | Cost |
|---|---|---|
| 5 clips (2 mine, 3 course) × Whisper | the default transcriber's WER and missing words per clip | ~$0.0002 |
| 5 clips × Scribe | the cross-check; which model got my name right | ~$0.003 |
| 2 speech calls (Harper, Priya) on one answer | characters, bytes, cost; how each says my name and "CPSC 415" | ~$0.01 |
| `pytest voice/tests/test_eval.py` (5 transcriptions + 1 speech) | the clips pass within tolerance; speech comes back as real MP3 | ~$0.002 |
| browser check (1 turn) + 1 live microphone turn | the loop works; the key never reaches the browser; the per-turn cost | ~$0.01 |

Expected total for Week 7: **under $0.03**.

## Approved by
Jeevan Gowda Kumaraswamy
Date: November 2, 2026
