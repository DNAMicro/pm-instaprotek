#!/usr/bin/env python3
"""
Free (watermarked) Synthesia test that reads several spellings of one word, so
the right pronunciation can be picked by ear before spending credits.

Usage (from the pm-instaprotek folder):
  python Videos/pronunciation_test.py
Writes Videos/pronunciation_test.mp4.
"""
import os
import sys
import time

from synthesia_narration import STOCK_AVATAR, call, download, load_key_and_avatar

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pronunciation_test.mp4")

# instaProtek = "InstaProtect", stress on IN-sta. Each one is read inside the
# exact first sentence of the video, because the sentence changes how it sounds.
VARIANTS = [
    '<sub alias="Insta-protect">instaProtek</sub>',
    '<sub alias="Insta Protect">instaProtek</sub>',
    '<sub alias="InstaProtect">instaProtek</sub>',
    '<sub alias="Instaprotect">instaProtek</sub>',
    '<sub alias="Insta-pro-tect">instaProtek</sub>',
    '<sub alias="Instuh-protect">instaProtek</sub>',
]
SENTENCE = "This is the {} app landing page."
WORDS = ["One", "Two", "Three", "Four", "Five", "Six"]

# Liquipel = "Leekwepel"; read on its own, as in the video
LIQUIPEL = [
    '<sub alias="Leekwepel">Liquipel</sub>',
    '<sub alias="Leek-weh-pel">Liquipel</sub>',
    '<sub alias="Leek-wepple">Liquipel</sub>',
]


def main():
    key, _ = load_key_and_avatar()
    script = " ".join(f"Option {w}. " + SENTENCE.format(v) + " <break time=\"1s\"/>"
                      for w, v in zip(WORDS, VARIANTS))
    script += " " + " ".join(f"Partner option {w}. {v}. <break time=\"1s\"/>"
                             for w, v in zip(WORDS, LIQUIPEL))
    body = {
        "test": True,
        "title": "instaProtek and Liquipel pronunciation options (test)",
        "visibility": "private",
        "aspectRatio": "16:9",
        "input": [{
            "scriptText": script,
            "avatar": STOCK_AVATAR,
            "avatarSettings": {"style": "voiceOnly"},
            "background": "off_white",
        }],
    }
    code, resp = call(key, "POST", "/v2/videos", body)
    if code not in (200, 201) or "id" not in resp:
        sys.exit(f"Synthesia refused it ({code}): {str(resp)[:600]}")
    vid = resp["id"]
    print("Submitted", vid)
    for _ in range(120):
        code, resp = call(key, "GET", f"/v2/videos/{vid}")
        if code == 404 or resp.get("status") in ("failed", "rejected", "deleted"):
            sys.exit(f"Synthesia did not render it: {resp.get('status', code)}")
        if resp.get("status") == "complete" and resp.get("download"):
            download(resp["download"], OUT)
            print("Done:", OUT, resp.get("duration"))
            return
        time.sleep(20)
    sys.exit("Still rendering after 40 minutes.")


if __name__ == "__main__":
    main()
