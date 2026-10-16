#!/usr/bin/env python3
"""
Build Videos/Landingpages_refined.mp4 = the original screen recording (picture
untouched apart from light cleanup) + the Synthesia narration, with the original
voice removed.

Needs ffmpeg and ffprobe on PATH (Windows: winget install Gyan.FFmpeg).
Run AFTER synthesia_narration.py has downloaded the clips to Videos/narration/.

Usage:
  python Videos/assemble_final.py
Options:
  --narration-dir DIR   where the clips are (default Videos/narration)
  --out FILE            output file (default Videos/Landingpages_refined.mp4)
  --start SEC --end SEC original-timeline window to keep (default 2.6 -> 90.4,
                        which only drops the black screens at the start and end)
  --keep-temp           keep the temporary working files
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Landingpages.mp4")
SCRIPT = os.path.join(HERE, "narration_script.json")
GAP = 0.12          # minimum quiet gap between two narration clips (s)
MAX_TEMPO = 1.12    # never speed a clip up more than this to fit its slot
FADE_IN, FADE_OUT = 0.4, 0.8

TRIM = ("silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB:detection=peak,"
        "areverse")


def run(cmd, capture=False):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit("Command failed:\n  " + " ".join(cmd) + "\n" + r.stderr[-1500:])
    return r


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path])
    return float(r.stdout.strip())


def find_clip(folder, sid):
    for ext in (".mp4", ".wav", ".mp3", ".m4a"):
        p = os.path.join(folder, sid + ext)
        if os.path.exists(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narration-dir", default=os.path.join(HERE, "narration"))
    ap.add_argument("--out", default=os.path.join(HERE, "Landingpages_refined.mp4"))
    ap.add_argument("--start", type=float, default=2.6)
    ap.add_argument("--end", type=float, default=90.4)
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found on PATH. Install ffmpeg (winget install Gyan.FFmpeg) and retry.")

    with open(SCRIPT, "r", encoding="utf-8") as f:
        segs = sorted(json.load(f)["segments"], key=lambda s: s["start_sec"])
    missing = [s["id"] for s in segs if not find_clip(args.narration_dir, s["id"])]
    if missing:
        sys.exit("Missing narration clips for: " + ", ".join(missing))

    length = args.end - args.start
    tmp = tempfile.mkdtemp(prefix="oos_video_")
    try:
        # 1) clean each clip: audio only, mono 48 kHz, silence trimmed at both ends
        clips = []
        for s in segs:
            src = find_clip(args.narration_dir, s["id"])
            wav = os.path.join(tmp, s["id"] + ".wav")
            run(["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "48000", "-af", TRIM, wav])
            clips.append({"id": s["id"], "start": s["start_sec"], "wav": wav, "dur": duration(wav)})

        # 2) fit each clip into its slot (gentle speed-up only if it would collide with the next)
        for i, c in enumerate(clips):
            nxt = clips[i + 1]["start"] if i + 1 < len(clips) else args.end - 0.9
            slot = nxt - GAP - c["start"]
            c["speed"] = 1.0
            if c["dur"] > slot > 0:
                tempo = min(c["dur"] / slot, MAX_TEMPO)
                fast = os.path.join(tmp, c["id"] + "_fast.wav")
                run(["ffmpeg", "-y", "-i", c["wav"], "-af", f"atempo={tempo:.4f}", fast])
                c["wav"], c["dur"], c["speed"] = fast, duration(fast), tempo
            note = ""
            if c["dur"] > slot + 0.05:
                note = "  <-- still overlaps the next clip"
            print(f"  {c['id']:18s} at {c['start']:6.2f}s  {c['dur']:5.2f}s  slot {slot:5.2f}s"
                  f"  speed x{c['speed']:.2f}{note}")

        # 3) lay the clips on a silent timeline
        inputs, parts, labels = [], [], []
        for i, c in enumerate(clips):
            ms = max(0, int(round((c["start"] - args.start) * 1000)))
            inputs += ["-i", c["wav"]]
            parts.append(f"[{i}:a]adelay=delays={ms}:all=1[a{i}]")
            labels.append(f"[a{i}]")
        n = len(clips)
        mix = os.path.join(tmp, "mix.wav")
        graph = ";".join(parts) + ";" + "".join(labels)
        try:
            run(["ffmpeg", "-y", *inputs, "-filter_complex",
                 graph + f"amix=inputs={n}:normalize=0:duration=longest,"
                 f"apad=whole_dur={length:.3f},atrim=0:{length:.3f}[m]",
                 "-map", "[m]", "-ar", "48000", "-ac", "1", mix])
        except SystemExit:
            run(["ffmpeg", "-y", *inputs, "-filter_complex",
                 graph + f"amix=inputs={n}:duration=longest,volume={n},"
                 f"apad=whole_dur={length:.3f},atrim=0:{length:.3f}[m]",
                 "-map", "[m]", "-ar", "48000", "-ac", "1", mix])

        # 4) voice polish + loudness (two-pass EBU R128, -16 LUFS, true peak -1.5 dB)
        polish = "highpass=f=80,acompressor=threshold=-20dB:ratio=2.2:attack=8:release=120:makeup=2"
        probe = run(["ffmpeg", "-hide_banner", "-i", mix, "-af",
                     polish + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                     "-f", "null", "-"])
        m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", probe.stderr, re.S)
        if m:
            j = json.loads(m.group(0))
            ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}"
                  f":measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}"
                  f":offset={j['target_offset']}:linear=true")
        else:
            ln = "loudnorm=I=-16:TP=-1.5:LRA=11"
        final_audio = os.path.join(tmp, "narration_final.wav")
        run(["ffmpeg", "-y", "-i", mix, "-af", polish + "," + ln, "-ar", "48000", "-ac", "2", final_audio])

        # 5) picture: same footage, light cleanup, fades; original audio dropped
        vf = ("deblock=filter=weak:block=8,hqdn3d=1.0:1.0:3:3,unsharp=5:5:0.5:3:3:0.0,"
              f"fade=t=in:st=0:d={FADE_IN},fade=t=out:st={length - FADE_OUT:.3f}:d={FADE_OUT},"
              "format=yuv420p")
        af = f"afade=t=in:st=0:d=0.15,afade=t=out:st={length - FADE_OUT:.3f}:d={FADE_OUT}"
        run(["ffmpeg", "-y", "-ss", f"{args.start}", "-t", f"{length:.3f}", "-i", SRC, "-i", final_audio,
             "-map", "0:v:0", "-map", "1:a:0", "-vf", vf, "-af", af,
             "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-r", "25",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", "-t", f"{length:.3f}", args.out])
        print(f"Done: {args.out}  ({duration(args.out):.1f}s, {os.path.getsize(args.out)/1e6:.1f} MB)")
    finally:
        if args.keep_temp:
            print("Temp files kept in", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
