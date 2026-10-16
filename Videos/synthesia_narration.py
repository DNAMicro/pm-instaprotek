#!/usr/bin/env python3
"""
Generate the voiceover clips for Videos/Landingpages.mp4 with Synthesia.

Run this ON YOUR PC (it needs normal internet access to api.synthesia.io).
It reads the API key from ../synthesia-credentials.json and never prints it.
Each segment in narration_script.json becomes one short Synthesia video; the
clips are downloaded to Videos/narration/<segment id>.mp4. Afterwards the
audio is extracted from those clips and laid over the original recording.

Usage (from the pm-instaprotek folder):
  python Videos/synthesia_narration.py --dry-run          # show what would be sent, spend nothing
  python Videos/synthesia_narration.py --test --only A_intro   # free watermarked trial of one clip
  python Videos/synthesia_narration.py                    # real run, all segments (uses credits)

Options:
  --avatar ID   override the avatar (default: Synthesia stock avatar "Anna",
                anna_costume1_cameraA; pass "saved" to use defaultAvatar from the
                credentials file instead)
  --voice ID    override the voice with a Synthesia voice ID (default: the avatar's own voice)
  --only A,B    only these segment ids
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CREDS = os.path.join(ROOT, "synthesia-credentials.json")
SCRIPT = os.path.join(HERE, "narration_script.json")
OUT = os.path.join(HERE, "narration")
MANIFEST = os.path.join(OUT, "manifest.json")
API = "https://api.synthesia.io"
STOCK_AVATAR = "anna_costume1_cameraA"  # Anna, US English - the voice Sarah approved


def load_key_and_avatar():
    with open(CREDS, "r", encoding="utf-8") as f:
        d = json.load(f)
    s = d["services"]["synthesia"]
    key = s.get("apiKey", "")
    if not key or key.startswith("REPLACE"):
        sys.exit("synthesia-credentials.json still has the placeholder API key.")
    return key, s.get("defaultAvatar", "")


def call(key, method, path, body=None, tries=5):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Authorization": key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(tries):
        req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode("utf-8")
                return r.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            if e.code == 429 and attempt < tries - 1:
                wait = int(e.headers.get("RateLimit-Reset", "10") or 10) + 1
                print(f"  rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, {"raw": raw[:300]}
    return 0, {}


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="free watermarked test videos")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--avatar", default="")
    ap.add_argument("--voice", default="")
    args = ap.parse_args()

    key, default_avatar = load_key_and_avatar()
    if args.avatar == "saved":
        avatar = default_avatar
    else:
        avatar = args.avatar or STOCK_AVATAR
    if not avatar:
        sys.exit("No avatar: pass --avatar <id>.")

    with open(SCRIPT, "r", encoding="utf-8") as f:
        segments = json.load(f)["segments"]
    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        segments = [s for s in segments if s["id"] in wanted]
    if not segments:
        sys.exit("No segments selected.")

    os.makedirs(OUT, exist_ok=True)
    manifest = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    print(f"{len(segments)} segment(s), test={args.test}, avatar={avatar[:12]}...")
    if args.dry_run:
        for s in segments:
            print(f"  {s['id']:18s} start {s['start_sec']:6.2f}s  {len(s['script'])} chars")
        print("Dry run only - nothing sent.")
        return

    code, credits = call(key, "GET", "/v2/billing/credits")
    if code == 200:
        print("Credit balance:", credits)

    # 1) submit every segment
    for s in segments:
        sid = s["id"]
        entry = manifest.get(sid, {})
        if entry.get("video_id") and entry.get("test") == args.test:
            print(f"  {sid}: already submitted ({entry['video_id'][:8]}...)")
            continue
        scene = {
            "scriptText": s["script"],
            "avatar": avatar,
            "background": "green_screen",
        }
        if args.voice:
            scene["avatarSettings"] = {"voice": args.voice}
        body = {
            "test": args.test,
            "title": f"Landingpages narration - {sid}",
            "visibility": "private",
            "aspectRatio": "16:9",
            "input": [scene],
        }
        code, resp = call(key, "POST", "/v2/videos", body)
        if code not in (200, 201) or "id" not in resp:
            print(f"  {sid}: FAILED to submit ({code}) {json.dumps(resp)[:300]}")
            manifest[sid] = {"error": f"submit {code}", "test": args.test}
        else:
            print(f"  {sid}: submitted {resp['id']}")
            manifest[sid] = {"video_id": resp["id"], "test": args.test, "start_sec": s["start_sec"]}
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        time.sleep(1.2)

    # 2) poll until every submitted segment is done
    pending = {sid: m for sid, m in manifest.items()
               if m.get("video_id") and not m.get("file") and sid in {s["id"] for s in segments}}
    started = time.time()
    while pending and time.time() - started < 45 * 60:
        for sid in list(pending):
            code, resp = call(key, "GET", f"/v2/videos/{pending[sid]['video_id']}")
            status = resp.get("status") if code == 200 else f"http {code}"
            if status == "complete" and resp.get("download"):
                dest = os.path.join(OUT, f"{sid}.mp4")
                download(resp["download"], dest)
                manifest[sid]["file"] = os.path.basename(dest)
                manifest[sid]["duration"] = resp.get("duration")
                print(f"  {sid}: downloaded ({resp.get('duration')}s)")
                del pending[sid]
            elif status in ("failed", "rejected", "deleted") or code == 404:
                # Synthesia removes rejected videos, so a 404 here means it was rejected
                manifest[sid]["error"] = status if code == 200 else "rejected or deleted (404)"
                print(f"  {sid}: {manifest[sid]['error']} - check the video in Synthesia, "
                      "shorten or reword the script, then rerun with --only " + sid)
                del pending[sid]
            with open(MANIFEST, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        if pending:
            print(f"  waiting on {len(pending)} clip(s)...")
            time.sleep(20)

    ok = [sid for sid, m in manifest.items() if m.get("file")]
    bad = [sid for sid, m in manifest.items() if m.get("error")]
    print(f"Done. {len(ok)} downloaded, {len(bad)} problem(s): {bad}")
    sys.exit(1 if bad or pending else 0)


if __name__ == "__main__":
    main()
