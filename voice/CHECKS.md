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

Transcript files: `transcripts-whisper.json`, `transcripts-scribe.json`. One call per clip per model.

| Clip | Model | WER | Missing | Audio s | Cost | Call s |
|---|---|---|---|---|---|---|
| mine-01.m4a (Jeevan / CPSC 415) | whisper-large-v3-turbo | **0.231 FAIL** | — | 8.04 | $0.0000268 | 0.9 |
| mine-01.m4a | scribe-v2 | 0.0 ok | — | 8.02 | $0.000490 | 1.2 |
| mine-02.m4a (Swift) | whisper-large-v3-turbo | 0.125 ok | — | 4.2 | $0.0000140 | 0.6 |
| mine-02.m4a | scribe-v2 | 0.125 ok | — | 4.18 | $0.000256 | 0.6 |
| course/clip-01.wav | whisper-large-v3-turbo | 0.0 ok | — | 6.38 | $0.0000212 | 1.5 |
| course/clip-01.wav | scribe-v2 | 0.0 ok | — | 6.38 | $0.000390 | 0.8 |
| course/clip-02.wav | whisper-large-v3-turbo | 0.188 ok (clip tolerance 0.2) | — | 8.061 | $0.0000268 | 1.4 |
| course/clip-02.wav | scribe-v2 | 0.0 ok | — | 8.062 | $0.000493 | 0.6 |
| course/clip-03.wav | whisper-large-v3-turbo | 0.0 ok | — | 7.708 | $0.0000257 | 0.7 |
| course/clip-03.wav | scribe-v2 | 0.0 ok | — | 7.708 | $0.000471 | 0.6 |

Totals: Whisper $0.00011, Scribe $0.00210 (about 19× Whisper for the same five clips).

**My name and numbers.** Both models wrote "Jeevan Gowda" correctly. Only **Scribe** got the course number
right: Whisper heard "CPSC 415" as "**CBSC** 415" (same result in run 1 and run 2, so it is not a fluke) and
appended "**Thank you.**" to the trailing silence. "415" survived in both, so `must_contain` passed and the
WER tolerance is what failed the clip. I am not raising the tolerance: "CBSC" is a real error in exactly
the word a recruiter would check. Whisper also appended "Music" to course clip 2, the habit the course
notes describe.

**"a mobile app".** Both models heard "shipped **a** mobile app" in my Swift clip, and `expected.json` omits
"a". When two independent transcribers agree on an extra word, the likelier explanation is that I said it
and my expected text is missing it. I left `expected.json` as written (it was committed before the models
heard the clip); the 0.125 is recorded as it scored.

**What I heard when I played each clip** (in my own terminal, not through the agent):
- mine-01: I said "CPSC" clearly, so Whisper's "CBSC" is the model's mistake. I did **not** say "Thank you";
  Whisper invented it from the trailing silence. Scribe's transcript is exactly what I said.
- mine-02: I did say "shipped **a** mobile app". My `expected.json` text is missing the "a", so the 0.125 on
  both models is my transcription error, not theirs. `expected.json` stays as committed; this note is the correction.

**Which model got my name and numbers right:** both got "Jeevan Gowda"; only Scribe got "CPSC 415".

**Billing quirk.** One Whisper call per run was billed as exactly 10.0 s of audio at $0.000111 (run 1: the
4.2 s Swift clip; eval run: course clip 1), about 4× the usual price. Different clips each time, so it looks
like a 10-second minimum on one of the hosts serving the model, not a property of the clip.

### The billed eval (`pytest voice/tests -v -s`)

**15 passed, 1 failed** in 8.5 s: the 10 no-key tests, 4 of 5 clips, and the speech test (87,360 bytes of
real MP3, $0.000735). The failure is `mine-01.m4a` on Whisper (WER 0.231, the CBSC/"Thank you." result
above), and it is left failing on purpose: the eval runs on the class model, and the class model got my
course number wrong. Cost about $0.001.

## The answer, spoken twice

Typed answer to my first clip (`answer-mine-01.json`, `minimax/minimax-m3`, $0.000354, 3.0 s):

> From the Campus Events Navigator project, Jeevan learned how to manage inter-service communication through
> NGINX Ingress and handle containerized state management using Redis. I don't have any record linking this
> project to a CPSC 415 course specifically, so I can't confirm that connection.

It refused to fabricate: the profile does not tie Campus Events Navigator to CPSC 415, and it said so.

| Voice | File | Chars | Bytes | Est. cost | Call s | Audio s | My name | "CPSC 415" | "NGINX", "Redis" |
|---|---|---|---|---|---|---|---|---|---|
| `microsoft/mai-voice-2.1-flash` / `en-US-Harper` | `answer-harper.mp3` | 291 | 391,680 | $0.004365 | 2.1 | 19.6 | fine | fine | fine |
| `microsoft/mai-voice-2.1-flash` / `en-IN-Priya` | `answer-priya.mp3` | 291 | 433,920 | $0.004365 | 1.4 | 21.7 | fine | fine | fine |

Listened to both: each voice said "Jeevan", "CPSC 415", and "NGINX"
acceptably; neither mangled my name. **I prefer Priya (`en-IN-Priya`) for the site.** The spec's default is
still Harper; switching the default voice is a spec change for after Week 7. Same model and price per
character, so the switch costs nothing extra.

Both costs are **estimated** (catalog price per character × 291): the speech reply is audio bytes with no
usage object. The bill is in the generation record named by the `X-Generation-Id` header.

## Browser check

Server started with the key in its environment. The pytest process that drove the browser ran with the
key **unset**. `python3 -m pytest test_browser.py -v -s`: **1 passed in 5.76 s**. It uploaded
`clips/course/clip-02.wav` through the page's file picker.

Before the test: `POST /api/voice` with `Content-Type: text/plain` → **415** with the list of accepted types,
and no model call.

What the page showed:

> You said: Have you ever deployed anything with Kubernetes? Be honest, I'm comparing you with a boot camp graduate. Music
>
> Answer: Yes, Kubernetes is in my shipped skills and I used it as part of my Campus Events Navigator project to
> orchestrate polyglot microservices with NGINX Ingress and Redis-backed state. That said, I'll be straight with
> you: my Kubernetes experience is application-level orchestration in local homelab setups, not enterprise
> production cluster administration across multi-region cloud environments. So compared to someone who's run
> production clusters at scale, there's a real gap there that I haven't closed yet.
>
> [stt $0.00002684313 · chat $0.00038995 · tts $0.007605 · 0.9s + 2s + 1.5s]

The last three assertions, all passed:
1. `all(auth is None for _, auth in requests)`: **no Authorization header left the browser.**
2. `all("openrouter" not in url for url, _ in requests)`: **the browser never called the provider.**
3. `any(url.endswith("/api/voice") for url, _ in requests)`: **it called our server.**

My judgment of the answer: honest. Kubernetes is in `shipped_skills`, and production cluster administration
is in `not_yet`, and it said both. Whisper's trailing "Music" reached the chat model, which ignored it.

## One turn

One question asked by me into the laptop microphone on http://localhost:8000 (Chrome, hold-to-talk, `audio/webm`),
11:39:59 on November 2. I asked: "What skills has Jeevan not learned yet?"

> You said: What skills has **Jamin** not learned yet?
>
> Answer: I don't have information about anyone named Jamin, so I can't speak to their skills. I can only share
> details about Jeevan Gowda Kumaraswamy, if you'd like to ask about them.
>
> [stt $0.00001338327 · chat $0.00024657 · tts $0.00261 · 1.4s + 1s + 0.9s]

| Step | Model | Seconds | Cost |
|---|---|---|---|
| Transcription | `openai/whisper-large-v3-turbo` | 1.4 | $0.0000134 |
| Answer | `minimax/minimax-m3` | 1.0 | $0.000247 |
| Speech | `microsoft/mai-voice-2.1-flash` / `en-US-Harper` | 0.9 | $0.00261 (estimated) |
| **Total** | | **3.3** | **$0.00287** |

**What happened.** Whisper heard my name as "Jamin": live, from a laptop microphone, the misheard-name risk
in `plan.md` happened on the first try. The chatbot did the honest thing: it did not guess that "Jamin" meant
me and said it only knows about Jeevan Gowda Kumaraswamy. Because the page shows "You said:", the visitor can
see the mistake and ask again. Honest, but the visitor got no answer to the question. The two-model comparison
above points at the fix: Scribe got my name and "CPSC 415" right on every clip, at about 19× Whisper's price,
which is still under $0.0005 a clip.

A request at 11:39:46 (a very short press) returned 200 with no `turn:` line in the server log. That is the
empty-transcript path (behavior 1): "I didn't catch that", with no chat or speech call billed.

**For the hosting decision.** One voice turn costs about **$0.003** (this turn, short answer) to **$0.008**
(the browser check's longer answer). Speech is about 90% of it, priced per character of the answer, so the
three-sentence cap is also the cost cap. That is about **$3–8 per 1,000 spoken questions**. A typed question
costs only the chat step, about $0.0003. The deployed version needs a per-visitor rate limit, and the key
lives in the host's environment variables, never in the repository. This number goes into `spec.md` with
`weeks/07/hosting.md` before November 30.
