"""The voice loop for the portfolio chatbot: the browser records, the server transcribes, answers from
profile.json, and speaks. Spec section 4, "the loop". Adapted from the course's examples/voice-loop/server.py
until the FastAPI chatbot exists; `answer()` moves there unchanged.

    export OPENROUTER_API_KEY=...
    python3 server.py                 # then open http://localhost:8000

GET  /            the page: hold-to-talk (stops at 30 s), a file picker, a text box.
POST /api/voice   body = audio bytes, Content-Type names the format. Transcribe, answer, speak; JSON back
                  with transcript, answer, MP3 as base64, and the three costs. The browser never sees the key.
POST /api/ask     body = the question as text; the same answer() without transcription or speech.
"""
import base64
import json
import os
import pathlib
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from openrouter import OpenRouter

from check import for_speech
from speak import DEFAULT_MODEL as TTS_MODEL
from speak import DEFAULT_VOICE as TTS_VOICE
from speak import speak
from transcribe import DEFAULT_MODEL as STT_MODEL
from transcribe import transcribe

HERE = pathlib.Path(__file__).parent
KEY = os.environ.get("OPENROUTER_API_KEY") or sys.exit("OPENROUTER_API_KEY is not set; the server needs it.")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "minimax/minimax-m3")
MAX_BODY = 10_000_000                                          # behavior 9: 10 MB cap on what a visitor can send
PAGE = (HERE / "index.html").read_bytes()
PROFILE = json.loads((HERE.parent / "profile.json").read_text())
FORMATS = {"audio/webm": "webm", "audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/wav": "wav", "audio/ogg": "ogg",
           "audio/x-wav": "wav", "audio/wave": "wav", "audio/mp4": "m4a", "audio/x-m4a": "m4a", "audio/flac": "flac"}

SYSTEM = """You answer a visitor's questions about one person, from the profile below and nothing else.
Rules: shipped work is in "projects" and "shipped_skills"; "learning_goals" are things the person is learning,
not things they have shipped; anything in "not_yet" is something the person has deliberately not done, and you
say so plainly with the reason. If the profile does not cover the question, say that you don't know rather than
guessing. Never claim experience the profile does not record. Answer in at most three spoken sentences: this
answer will be read aloud, so no lists, no markdown, no URLs.

PROFILE:
""" + json.dumps(PROFILE, indent=1)

client = OpenRouter(api_key=KEY)


def answer(question: str) -> tuple[str, float | None]:
    """The chatbot's answer function; the typed path and the voice path both call it (behaviors 5, 7).
    max_tokens counts minimax-m3's hidden reasoning too, so it is generous."""
    c = client.chat.send(model=CHAT_MODEL, max_tokens=1500,
                         messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}])
    text = for_speech(c.choices[0].message.content or "")
    if not text:                                    # an empty answer is a failed answer, said so, not spoken
        text = f"I couldn't put an answer together (the model stopped: {c.choices[0].finish_reason}). Please ask again."
    return text, getattr(c.usage, "cost", None)


def voice_turn(audio: bytes, fmt: str) -> dict:
    """The loop, once: hear, think, speak, with each step's cost and seconds for CHECKS.md.
    A failed speech call still returns the transcript and the answer, with the error."""
    t0 = time.time()
    heard = transcribe(client, audio, fmt, STT_MODEL)
    question = (heard["text"] or "").strip()
    if not question:                                # behavior 1: no chat or speech call on an empty transcript
        return {"transcript": "", "answer": "I didn't catch that.", "audio_b64": None,
                "cost": {"stt": heard["cost"], "chat": 0, "tts": 0}, "seconds": {"stt": heard["seconds"]}}
    t1 = time.time()
    reply, chat_cost = answer(question)
    t2 = time.time()
    audio_b64, tts_cost, tts_error = None, 0, None
    out = HERE / "last-answer.mp3"
    try:
        spoken = speak(client, reply, out, TTS_MODEL, TTS_VOICE)
        audio_b64, tts_cost = base64.b64encode(out.read_bytes()).decode(), spoken["cost"]
    except Exception as e:  # noqa: BLE001  (the provider's message, without the key)
        tts_error = str(e)[:300]
    seconds = {"stt": round(t1 - t0, 1), "chat": round(t2 - t1, 1), "tts": round(time.time() - t2, 1)}
    print(f"turn: stt {seconds['stt']}s ${heard['cost']}  chat {seconds['chat']}s ${chat_cost}  "
          f"tts {seconds['tts']}s ${tts_cost}" + (f"  TTS FAILED: {tts_error}" if tts_error else ""), flush=True)
    return {"transcript": question, "answer": reply, "audio_b64": audio_b64, "tts_error": tts_error,
            "cost": {"stt": heard["cost"], "chat": chat_cost, "tts": tts_cost}, "seconds": seconds,
            "models": {"stt": STT_MODEL, "chat": CHAT_MODEL, "tts": f"{TTS_MODEL} / {TTS_VOICE}"}}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.reply(405, {"error": "POST only"})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY:
            return self.reply(413, {"error": f"recording too large ({length} bytes; limit {MAX_BODY})"})
        body = self.rfile.read(length)
        try:
            if self.path == "/api/voice":
                ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
                fmt = FORMATS.get(ctype)
                if not fmt:
                    return self.reply(415, {"error": f"unsupported audio type {ctype!r}; send one of {sorted(FORMATS)}"})
                return self.reply(200, voice_turn(body, fmt))
            if self.path == "/api/ask":
                question = body.decode(errors="replace")[:2000]
                reply, cost = answer(question)
                return self.reply(200, {"transcript": question, "answer": reply, "audio_b64": None,
                                        "cost": {"stt": 0, "chat": cost, "tts": 0}})
            self.reply(404, {"error": "not found"})
        except Exception as e:  # noqa: BLE001  (the provider's message goes back, never the key)
            traceback.print_exc()
            self.reply(502, {"error": str(e)[:500]})

    def reply(self, status: int, data: dict):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    print(f"http://localhost:8000  (stt {STT_MODEL}, chat {CHAT_MODEL}, tts {TTS_MODEL}/{TTS_VOICE})")
    try:
        ThreadingHTTPServer(("localhost", 8000), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
