# Specification: AI-Enabled Profile Site

## 1. Profile Schema (JSON)
The profile data is structured under profile.json with the following schema:

```json
{
  "person": {
    "name": "Jeevan Gowda Kumaraswamy",
    "role": "Computer Science Senior @ Trinity College",
    "bio": "Developer specializing in polyglot backends, microservices, and applied cryptographic systems."
  },
  "projects": [
    {
      "name": "Campus Events Navigator",
      "what_is_this": "A polyglot microservices platform for tracking and discovering campus events.",
      "why_this_choice": "Built to explore Kubernetes orchestration, Python FastAPI, and Spring Boot service integration.",
      "what_breaks": "High latency during initial cold starts when scaling down container pods under low resources.",
      "what_did_i_learn": "Managing inter-service communication via NGINX Ingress and containerized state management using Redis."
    }
  ],
  "shipped_skills": ["Python", "Java", "Docker", "Kubernetes", "Git", "Spring Boot", "FastAPI"],
  "learning_goals": ["Zero-Knowledge Proofs (zk-SNARKs)", "Neo4j Graph Processing"]
}
```

## 2. Not Yet Inventory
Skills and tools deliberately not prioritized at present:

1. C++ Game Engine Development: Prioritized web microservices and cryptographic backend architectures over low-level graphics rendering.
2. Kubernetes Production Cluster Administration: Focused on application-level container orchestration in local homelabs rather than enterprise multi-region cloud ops.
3. Mobile App Development (React Native / Swift): Focused on backend REST API development and browser-based frontends rather than mobile platforms.

## 3. Language & Model Decisions

- Frontend/Backend Stack: Static HTML/CSS frontend with a Python FastAPI serverless backend function.
- Primary Model: anthropic/claude-3.5-haiku via OpenRouter.
- Alternative Model for Comparison: nvidia/nemotron-3-ultra-550b-a55b:free or openai/gpt-4o-mini.

## 4. Week 7: spoken interface

Source: `intent/voice.md`. Code lives in `voice/`. Until the chatbot exists, the answer step is the
course example's (`examples/voice-loop/server.py`), grounded in `profile.json` built from section 1
and section 2 of this spec; it moves into the FastAPI app when that exists.

### Component: transcriber (`voice/transcribe.py`)

- **Language decision:** Python 3.13. The rest of the backend is Python (section 3), the course's
  example and the `openrouter` SDK are Python, and the checker's tests run under pytest.
- **Model decision:** default `openai/whisper-large-v3-turbo`: priced per second of audio
  (about $0.00002 for a 6-second clip), the cheapest serious transcriber. Comparison
  `elevenlabs/scribe-v2`: about 18× the price, and the course rehearsal found it read words
  that Whisper split or dropped. The comparison model is the cross-check, not the default.
- **Request:** `POST /api/v1/audio/transcriptions` through `client.stt.create_transcription`;
  the audio is sent as base64 with its format (`wav`, `mp3`, `m4a`, `webm`, `ogg`, `flac`, `aac`).
- **Records per clip:** the text, the model, the audio seconds and the cost from the reply's
  `usage`, and the wall-clock seconds of the call.
- **Language:** no hint by default (English expected); `--language xx` passes an ISO-639-1 hint.

### Component: speaker (`voice/speak.py`)

- **Language decision:** Python 3.13, the same reasons as the transcriber.
- **Model decision:** default `microsoft/mai-voice-2.1-flash` with the voice
  `en-US-Harper:MAI-Voice-2.1-Flash`: priced per character, under a second per call, and its
  MP3s transcribe correctly. Comparison: the same model with `en-IN-Priya:MAI-Voice-2.1-Flash`,
  a different locale. The comparison checks how each pronounces my name, which is the word most
  likely to be said wrong.
- **Request:** `POST /api/v1/audio/speech` through `client.tts.create_speech`, `response_format`
  `mp3` (or `pcm` framed as WAV when the output name ends in `.wav`).
- **Records per call:** characters of input, bytes of audio, wall-clock seconds, the generation
  id, and the cost. The reply is bytes with no usage object, so the cost is the catalog price per
  character × characters, marked *estimated*. The real bill is the generation record
  (`X-Generation-Id`), which appears about a minute later.

**Approved by:** Jeevan Gowda Kumaraswamy, November 2, 2026

### Component: the loop (`voice/server.py`, `voice/index.html`)

- `POST /api/voice`: the body is the recording, and `Content-Type` names the format. The server
  transcribes, calls **the same `answer()` function** as the typed path (`POST /api/ask`), speaks
  the reply, and returns JSON: transcript, answer, MP3 as base64, and the three costs (stt, chat, tts).
- Chat model for the answer: `minimax/minimax-m3`, the class model the example's answer step uses,
  with `max_tokens` 1500 so its hidden reasoning cannot empty the answer.

### Dependencies

| Package | Reason |
|---|---|
| `openrouter` | The OpenRouter SDK. One key and one client for transcription (`client.stt`), speech (`client.tts`), chat, and generation records. No other provider SDK is needed. |
| `pytest` | Runs the no-key checker tests and the key-gated billed eval. Development only. |
| `ruff` | Linter; its findings are recorded in `voice/CHECKS.md`. Development only. |
| `playwright` | The browser check (`voice/test_browser.py`): drives the page and asserts the key never reaches the browser. Development only. |

### Behaviors

1. **An empty transcript is a failed transcript, not a crash.** The checker scores `None` or
   `""` as word error rate 1.0 and reports `empty: true` and `ok: false` without raising. The
   server answers "I didn't catch that" and makes no chat or speech call.
2. **A reply that is not audio is an error, never saved as audio.** If the speech reply's
   `Content-Type` does not start with `audio/`, the speaker raises with the provider's message
   and writes no file. The server still returns the transcript and the answer, with the error.
3. **Word error rate, with a stated tolerance.** Expected text, written by a person before the
   model hears the clip, is compared in code: word-level edit distance (insert, delete,
   substitute) divided by the number of expected words, after lower-casing and removing
   punctuation. A clip passes at **≤ 0.15**. A clip may raise its own tolerance in `expected.json`
   only with a `note` that says why.
4. **The words that must survive.** Each clip lists `must_contain` words: my name (Jeevan, Gowda,
   Kumaraswamy, as said), project names (Campus Events Navigator), and numbers (415). Every
   missing word is reported by name, and the clip fails even if the rate is within tolerance.
   Spacing and case do not count ("CPSC415" = "CPSC 415"); a number read as words
   ("four fifteen") is a miss.
5. **The spoken answer is at most three sentences, with no markdown.** The system prompt asks for
   it, and code enforces it before the speech call: `for_speech()` strips markdown (`*`, `#`,
   backticks, list bullets, links) and keeps at most the first three sentences.
6. **The key stays on the server; the browser sends only audio.** The server reads
   `OPENROUTER_API_KEY` from the environment at startup. The page sends the recording to
   `/api/voice` with no `Authorization` header and never contacts the provider. No key or
   `.env` file is in the repository.
7. **The answer is grounded.** The spoken answer follows the same system prompt as the typed one:
   shipped work only, "not yet" said plainly, "I don't know" for anything the profile does not cover.
8. **The visitor sees what was heard.** The page shows "You said: <transcript>" above the answer.
9. **Input is capped.** The server reads at most 10 MB of body and answers 415 to a content type
   it does not map to a format. The page stops recording at 30 seconds.
10. **Every billed call records its cost.** Transcription: audio seconds and cost from the reply.
    Speech: characters, bytes, and estimated cost. Chat: `usage.cost`. The loop returns all three.
