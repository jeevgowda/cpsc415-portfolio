"""No-key tests for the transcript checker (spec section 4, behaviors 1, 3, 4, 5).

    python3 -m pytest voice/tests/test_check.py -v     # from the repository root; well under a second
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check import compare, for_speech, wer, words

SAID = "I am Jeevan Gowda and I built Campus Events Navigator for CPSC 415."   # 13 words


def test_words_ignore_case_and_punctuation():
    assert words("Hello, World!  It's 415.") == ["hello", "world", "it's", "415"]


def test_perfect_transcript_scores_zero():
    assert wer(SAID, SAID) == 0.0
    assert wer(SAID, "i am jeevan gowda, and i built campus events navigator for cpsc 415") == 0.0


def test_one_substitution_in_thirteen_words():
    got = SAID.replace("Gowda", "Gouda")
    assert abs(wer(SAID, got) - 1 / 13) < 1e-9


def test_empty_transcript_is_a_failed_transcript_not_a_crash():
    assert wer(SAID, "") == 1.0
    assert wer(SAID, None) == 1.0
    result = compare(SAID, None, must_contain=["Gowda"])
    assert not result["ok"] and result["empty"] and result["wer"] == 1.0


def test_names_that_must_survive_are_checked_separately():
    got = SAID.replace("Gowda", "Gouda")
    result = compare(SAID, got, must_contain=["Gowda", "415"])
    assert result["wer"] <= 0.15                      # the rate alone would have passed
    assert result["missing"] == ["Gowda"]
    assert not result["ok"]


def test_small_drift_within_tolerance_is_ok():
    got = SAID.replace(" for CPSC 415", " for CPSC 415 then")   # one inserted word
    result = compare(SAID, got, must_contain=["Gowda", "415"], max_wer=0.15)
    assert result["ok"] and result["wer"] == round(1 / 13, 3)


def test_number_read_as_words_is_a_miss():
    got = SAID.replace("415", "four fifteen")
    assert compare(SAID, got, must_contain=["415"])["missing"] == ["415"]


def test_must_contain_ignores_spacing_and_case():
    got = "campus events navigator for cpsc415 by jeevan gowda"
    assert compare("x", got, must_contain=["Campus Events Navigator", "CPSC 415"], max_wer=9)["missing"] == []


def test_spoken_answer_is_at_most_three_sentences():
    text = "One. Two is here! Three? Four should go. Five too."
    assert for_speech(text) == "One. Two is here! Three?"


def test_spoken_answer_has_no_markdown():
    text = "**Yes.** I shipped `FastAPI` in [Campus Events Navigator](https://x.y).\n- Docker\n# Done"
    spoken = for_speech(text)
    for mark in ("*", "`", "[", "](", "http", "#", "- "):
        assert mark not in spoken, spoken
    assert spoken.startswith("Yes. I shipped FastAPI in Campus Events Navigator.")
