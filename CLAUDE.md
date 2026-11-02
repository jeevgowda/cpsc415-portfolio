# CLAUDE.md: portfolio

Jeevan Gowda Kumaraswamy's portfolio site and its grounded chatbot (CPSC 415). The
chain is intent/ → spec.md → plan.md → tests → code; see those files before changing anything.

## Working rules

- No API key, token, or `.env` file is ever committed. The key lives in the
  environment (`OPENROUTER_API_KEY`) on the machine or host that runs the server.
- Every dependency is named in `spec.md` under Dependencies, with its reason,
  before it is installed. `.claude/hooks/guard.py` enforces this.
- Week 7: the spoken interface lives in voice/. Stages assigned: intent, spec,
  plan, tests. Commit to main.
- Transcription and speech calls are billed. One transcription per clip, one
  speech call per answer, never a model call inside a loop of tests. Fixture
  clips are WAV; expected.json is written by a person before the model hears it.
- The spoken answer is the chatbot's answer: the refuse-to-fabricate rule
  applies to what is said aloud exactly as to what is typed.
