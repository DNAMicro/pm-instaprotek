#!/usr/bin/env python3
"""
Build the finished landing-pages video INSIDE Synthesia, so it lives in the
Synthesia library and can be edited in the Synthesia editor.

How it works:
  1. Cuts Videos/Landingpages.mp4 into one slice per narration segment with
     ffmpeg, re-encoded with light cleanup and NO audio track, so the original
     voice cannot come through. (Synthesia ignores videoSettings.trim and
     volume, so slicing and muting happen here instead.)
  2. Uploads each slice once as a Synthesia asset (cached in
     synthesia_full_video.json; a slice is re-uploaded only if its times change).
  3. Makes one scene per segment: the slice as background, kept at full length
     (extend_content), a voice-only avatar so nothing covers the landing pages,
     and the narration text from narration_script.json.

Reads the API key from ../synthesia-credentials.json and never prints it.

Usage (from the pm-instaprotek folder):
  python Videos/synthesia_full_video.py --dry-run         # show the scene plan, send nothing
  python Videos/synthesia_full_video.py --test --scenes 3 # free watermarked test of the first 3 scenes
  python Videos/synthesia_full_video.py                   # real video, all scenes (uses credits)
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

from synthesia_narration import STOCK_AVATAR, call, download, load_key_and_avatar

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Landingpages.mp4")
SCRIPT = os.path.join(HERE, "narration_script.json")
STATE = os.path.join(HERE, "synthesia_full_video.json")
SLICES = os.path.join(HERE, "slices")
UPLOAD = "https://upload.api.synthesia.io/v2/assets"
CLEANUP = "deblock=filter=weak:block=8,hqdn3d=1.0:1.0:3:3,unsharp=5:5:0.5:3:3:0.0,format=yuv420p"
START, END = 2.6, 90.4   # drop only the black screens at the start and end
TITLE = "Landing Pages - instaProtek partner tour"


def load_state():
    if os.path.exists(STATE):
        with open(STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    hits = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages",
                                  "Gyan.FFmpeg*", "ffmpeg-*", "bin", "ffmpeg.exe"))
    if hits:
        return hits[0]
    sys.exit("ffmpeg not found. Install it with: winget install Gyan.FFmpeg")


def scene_windows(segments):
    """(t0, t1) per segment; a scene runs until the next segment starts, or until
    its own scene_end when set (the footage after that is cut)."""
    out = []
    for i, s in enumerate(segments):
        t0 = START if i == 0 else s["start_sec"]
        t1 = segments[i + 1]["start_sec"] if i + 1 < len(segments) else END
        out.append((round(t0, 2), round(s.get("scene_end", t1), 2)))
    return out


def upload_slices(key, state, segments):
    ff = ffmpeg_exe()
    os.makedirs(SLICES, exist_ok=True)
    cache = state.setdefault("slices", {})
    ids = []
    for s, (t0, t1) in zip(segments, scene_windows(segments)):
        tag = f"{t0:.2f}-{t1:.2f}"
        hit = cache.get(s["id"])
        if hit and hit.get("window") == tag:
            ids.append(hit["asset_id"])
            continue
        dest = os.path.join(SLICES, s["id"] + ".mp4")
        r = subprocess.run([ff, "-v", "error", "-y", "-ss", f"{t0}", "-to", f"{t1}", "-i", SRC,
                            "-an", "-vf", CLEANUP, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                            "-r", "25", "-movflags", "+faststart", dest],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if r.returncode != 0:
            sys.exit(f"ffmpeg failed on {s['id']}: {r.stderr[-500:]}")
        with open(dest, "rb") as f:
            data = f.read()
        req = urllib.request.Request(UPLOAD, data=data, method="POST",
                                     headers={"Authorization": key, "Content-Type": "video/mp4"})
        with urllib.request.urlopen(req, timeout=600) as resp:
            asset = json.loads(resp.read().decode("utf-8"))
        cache[s["id"]] = {"asset_id": asset["id"], "window": tag}
        save_state(state)
        ids.append(asset["id"])
        print(f"  uploaded {s['id']:18s} {tag}s")
    return ids


def build_scenes(asset_ids, segments):
    return [{
        "scriptText": s["script"],
        "avatar": STOCK_AVATAR,
        "avatarSettings": {"style": "voiceOnly"},
        "background": aid,
        "backgroundSettings": {
            "videoSettings": {
                # keep the whole slice on screen even when the line is shorter
                "longBackgroundContentMatchMode": "extend_content",
                "shortBackgroundContentMatchMode": "freeze",
            }
        },
    } for s, aid in zip(segments, asset_ids)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="free watermarked test video")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scenes", type=int, default=0, help="only the first N scenes (for testing)")
    args = ap.parse_args()

    with open(SCRIPT, "r", encoding="utf-8") as f:
        segments = sorted(json.load(f)["segments"], key=lambda s: s["start_sec"])

    if args.dry_run:
        for s, (t0, t1) in zip(segments, scene_windows(segments)):
            print(f"  {s['id']:18s} {t0:6.2f} -> {t1:6.2f}s")
        print("Dry run only - nothing sent.")
        return

    key, _ = load_key_and_avatar()
    state = load_state()
    scenes = build_scenes(upload_slices(key, state, segments), segments)
    if args.scenes:
        scenes = scenes[:args.scenes]

    run = "test" if args.test else "final"
    body = {
        "test": args.test,
        "title": TITLE + (" (test)" if args.test else ""),
        "visibility": "private",
        "aspectRatio": "16:9",
        "input": scenes,
    }
    code, resp = call(key, "POST", "/v2/videos", body)
    if code not in (200, 201) or "id" not in resp:
        sys.exit(f"Synthesia refused the video ({code}): {json.dumps(resp)[:800]}")
    vid = resp["id"]
    state[run] = {"video_id": vid, "scenes": len(scenes)}
    save_state(state)
    print(f"Submitted {len(scenes)} scene(s) as video {vid}")

    started = time.time()
    while time.time() - started < 60 * 60:
        code, resp = call(key, "GET", f"/v2/videos/{vid}")
        if code == 404:
            sys.exit("Video was rejected or deleted in Synthesia (404). Check it in the Synthesia app.")
        status = resp.get("status")
        if status == "complete" and resp.get("download"):
            dest = os.path.join(HERE, f"Landingpages_synthesia{'_test' if args.test else ''}.mp4")
            download(resp["download"], dest)
            state[run].update({"status": status, "duration": resp.get("duration"), "file": os.path.basename(dest)})
            save_state(state)
            print(f"Done: {dest} ({resp.get('duration')})")
            return
        if status in ("failed", "rejected", "deleted"):
            state[run]["status"] = status
            save_state(state)
            sys.exit(f"Synthesia reports the video as {status}.")
        print(f"  {status}...")
        time.sleep(30)
    sys.exit("Still rendering after 60 minutes; rerun later to check.")


if __name__ == "__main__":
    main()
