"""Check a transcript, and shape an answer for speech, in plain code. No model, no key.

A transcript is model output. The checks here are the ones a program can make without
hearing the audio (spec section 4, behaviors 1, 3, 4): how far the words drift from what
was said (word error rate), whether the words that must survive did (my name, project
names, numbers), and whether the model returned anything at all. `for_speech` is
behavior 5: at most three sentences, no markdown. Adapted from the course's
examples/voice-loop/check.py.
"""
import re

_WORD = re.compile(r"[a-z0-9']+")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")            # [text](url) -> text
_URL = re.compile(r"https?://\S+")
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)]|#+)\s+", re.MULTILINE)
_SENTENCE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")


def words(text: str | None) -> list[str]:
    """Lower-case words with punctuation removed, so 'Hello, world!' == 'hello world'."""
    return _WORD.findall((text or "").lower().replace("’", "'"))


def wer(expected: str, got: str | None) -> float:
    """Word error rate: edits (insert, delete, substitute) per expected word.
    0.0 is a perfect transcript; empty output scores 1.0."""
    e, g = words(expected), words(got)
    if not e:
        return 0.0 if not g else 1.0
    prev = list(range(len(g) + 1))            # O(n*m) Levenshtein over words; fine for sentences
    for i, ew in enumerate(e, 1):
        cur = [i]
        for j, gw in enumerate(g, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ew != gw)))
        prev = cur
    return prev[-1] / len(e)


def compare(expected: str, got: str | None, must_contain: list[str] | None = None, max_wer: float = 0.15) -> dict:
    """The verdict recorded per clip: the rate, the words that had to survive and did not,
    and ok only when both pass. A missing transcript is a failed transcript, not a crash."""
    heard = "".join(words(got))                 # spacing-insensitive: "CPSC415" still counts as "CPSC 415"
    missing = [w for w in (must_contain or []) if "".join(words(w)) not in heard]
    rate = wer(expected, got)
    return {"ok": rate <= max_wer and not missing and bool(words(got)),
            "wer": round(rate, 3), "missing": missing, "empty": not words(got)}


def for_speech(text: str, max_sentences: int = 3) -> str:
    """What the speaker is allowed to say: markdown, links, and URLs removed, lines joined,
    and at most `max_sentences` sentences. The system prompt asks for this; this enforces it."""
    t = _LINK.sub(r"\1", text or "")
    t = _URL.sub("", t)
    t = _BULLET.sub("", t)
    t = re.sub(r"[*_`#>]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return " ".join(s.strip() for s in _SENTENCE.findall(t)[:max_sentences] if s.strip())
