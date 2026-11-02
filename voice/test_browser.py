"""A browser-driven check of the voice page. Start server.py first (it needs the key; the browser must not).

  python3 server.py &
  python3 -m pytest test_browser.py -v -s          # from voice/; three billed calls, about half a cent
  CLIP=clips/mine-01.wav python3 -m pytest test_browser.py -v -s

It uploads a clip through the page's file picker (a microphone cannot be scripted reliably), waits for
the answer, and checks what the browser was allowed to see. The last three assertions are the point
(spec behavior 6). Whether the answer is honest is a person's judgment, recorded in CHECKS.md.
Adapted from the course's examples/voice-loop/test_browser.py.
"""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8000"
CLIP = Path(os.environ.get("CLIP", Path(__file__).parent / "clips" / "course" / "clip-02.wav"))   # Kubernetes question


def test_voice_page_answers_and_the_key_never_reaches_the_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not os.environ.get("HEADED"), slow_mo=500 if os.environ.get("HEADED") else 0)
        page = browser.new_page()
        requests = []
        page.on("request", lambda r: requests.append((r.url, r.headers.get("authorization"))))

        page.goto(URL)
        assert "sk-or" not in page.content()
        page.set_input_files("#file", str(CLIP))
        page.click("#send")
        page.wait_for_function("document.querySelector('#out').textContent.includes('Answer:')", timeout=120_000)
        out = page.inner_text("#out")
        has_audio = page.evaluate("!!document.querySelector('#player').src")
        browser.close()

    print("\n" + out)
    answer = out.split("Answer:")[1]
    assert out.startswith("You said:") and len(out.split("Answer:")[0]) > len("You said: "), out   # behavior 8
    assert len(answer.split("[")[0].strip()) > 20, out                 # an answer came back, not the fallback
    assert "speech failed" not in out, out
    assert has_audio                                                   # an MP3 came back
    assert all(auth is None for _, auth in requests)                   # no Authorization header left the browser
    assert all("openrouter" not in url for url, _ in requests)          # the browser never called the provider
    assert any(url.endswith("/api/voice") for url, _ in requests)       # it called our server
