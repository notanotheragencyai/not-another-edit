#!/usr/bin/env python3
"""Edit This Video helper. Python 3 standard library; heavy steps run in a private tools folder.

Usage: python3 ete.py <command> ...   (run a command with no arguments to see its usage)

  check                                 what's installed and what's missing
  setup                                 install the speech-to-text and render tools (private folder, asks first)
  new        WORK --raw CLIPS [--style STYLE]   start an edit: put the clips in order (PT 1, PT 2 ... by number)
  transcribe WORK [--prompt "names"] [--model small.en]   every word with its timing, retakes marked
  edl        WORK --auto                draft the cut list (last clean take of every line) for you to check
  cut        WORK [--gap 0.12]          tighten the cut, write the words with their times, make the preview
  fix        WORK INDEX=WORD ...        fix a misheard word (index from words.txt)
  style      WORK                       print the locked style options as ready-to-use JSON
  board      WORK                       check plan.json and build the storyboard page
  review     WORK FILE                  file their pasted storyboard review
  render     WORK [--overlay-fps 30]    build the finished video
  qa         WORK                       check the finished video and make a contact sheet
  feedback   STYLE "their words" "the rule"   add a note to STYLE.md "Feedback from edits"
  open       PATH                       open a page or video
"""
import datetime
import difflib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from fractions import Fraction

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(SK, "engine")
TOOLS = os.path.expanduser("~/.not-another-edit")
VENV = os.path.join(TOOLS, "venv")
NAE_SK = os.path.join(os.path.dirname(SK), "not-another-edit")
OUT_W, OUT_H = 1080, 1920
BUILT_IN_TYPES = {"captions", "title", "keyword", "zoom", "visual", "label", "transition"}
TIMELINE_TYPES = {"captions", "title", "keyword", "visual", "label"}  # what can go on screen in an edit
RENDER_TRANSITIONS = {"cut", "flash", "dip"}


# ---------------------------------------------------------------- helpers
def die(msg):
    print(msg)
    sys.exit(1)


def today():
    return datetime.date.today().isoformat()


def rj(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def wj(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def flags(args, names):
    out, rest, i = {}, [], 0
    switches = {n[:-1] for n in names if n.endswith("!")}
    valued = {n for n in names if not n.endswith("!")}
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a[2:] in switches:
            out[a[2:]] = True
            i += 1
        elif a.startswith("--") and a[2:] in valued:
            if i + 1 >= len(args):
                die(f"{a} needs a value.")
            out[a[2:]] = args[i + 1]
            i += 2
        else:
            rest.append(a)
            i += 1
    return out, rest


def run(cmd, what, quiet=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"{what} failed:\n{(r.stderr or r.stdout)[-1500:]}")
    return r.stdout


def need(tool):
    if not shutil.which(tool):
        die(f"{tool} isn't installed. Run: python3 ete.py check")


def project(work):
    pj = rj(os.path.join(work, "project.json"))
    if not pj:
        die(f'No edit started in "{work}". Start one: python3 ete.py new "{work}" --raw "<clips folder>"')
    return pj


def venv_python():
    """The python that has faster-whisper and playwright: the private one if it exists, else this one."""
    for cand in (os.path.join(VENV, "bin", "python3"), os.path.join(VENV, "Scripts", "python.exe")):
        if os.path.isfile(cand):
            return cand
    return sys.executable


def has_modules(py, mods):
    code = "import importlib.util,sys; sys.exit(0 if all(importlib.util.find_spec(m) for m in %r) else 1)" % (mods,)
    return subprocess.run([py, "-c", code], capture_output=True).returncode == 0


def chrome_path():
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
              "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if os.path.isfile(p):
            return p
    return None


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "stream=index,codec_type,codec_name,width,height,r_frame_rate,color_transfer:stream_side_data=rotation:"
               "format=duration", "-of", "json", path], f"Reading {os.path.basename(path)}")
    d = json.loads(out)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video" and s.get("codec_name") != "mjpeg"), None)
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        die(f"{os.path.basename(path)} has no video in it.")
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    w, h = v["width"], v["height"]
    if abs(rot) in (90, 270):
        w, h = h, w
    return {"file": os.path.basename(path), "width": w, "height": h, "fps": v["r_frame_rate"],
            "duration": float(d["format"]["duration"]), "audio": bool(a),
            "hdr": v.get("color_transfer") in ("arib-std-b67", "smpte2084"), "codec": v["codec_name"]}


def part_number(name):
    m = re.search(r"(?:^|[^a-z])(?:pt|part)[\s._-]*0*(\d+)", name, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else None


def natural_key(name):
    n = part_number(name)
    return (0, n, name.lower()) if n is not None else (1, 0, name.lower())


def find_style(pj=None):
    if pj and pj.get("style") and os.path.isfile(os.path.join(pj["style"], "STYLE.md")):
        return pj["style"]
    cfg = rj(os.path.join(NAE_SK, "config.json"), {})
    if cfg.get("styleDir") and os.path.isfile(os.path.join(cfg["styleDir"], "STYLE.md")):
        return cfg["styleDir"]
    return None


# ---------------------------------------------------------------- check / setup
def cmd_check(args):
    print("Edit This Video: checking this computer\n")
    rows, ready = [], True
    for tool, why, fix in (
            ("ffmpeg", "cuts and builds the video", "brew install ffmpeg"),
            ("ffprobe", "reads your clips (comes with ffmpeg)", "brew install ffmpeg")):
        ok = bool(shutil.which(tool))
        ready &= ok
        rows.append((tool, ok, why, fix))
    py = venv_python()
    fw = has_modules(py, ["faster_whisper"])
    pw = has_modules(py, ["playwright"])
    ch = chrome_path()
    rows.append(("speech-to-text", fw, "hears every word, picks takes, writes captions", "python3 ete.py setup"))
    rows.append(("renderer", pw, "draws your captions and graphics onto the video", "python3 ete.py setup"))
    rows.append(("Chrome", bool(ch), "the renderer uses it (or its own copy after setup)", "https://www.google.com/chrome"))
    ready &= fw and pw
    for tool, ok, why, fix in rows:
        print(f"  {tool:<15} {'found  ' if ok else 'MISSING'}  {why}" + ("" if ok else f"   fix: {fix}"))
    nae = os.path.isfile(os.path.join(NAE_SK, "page", "library.js"))
    print(f"  {'Not Another Edit':<15} {'found  ' if nae else 'MISSING'}  your style's look comes from it"
          + ("" if nae else "   fix: install the not-another-edit skill"))
    ready &= nae
    if not shutil.which("ffmpeg") and sys.platform == "darwin":
        print("\n  ffmpeg: install Homebrew from https://brew.sh first if 'brew' isn't found, then: brew install ffmpeg")
    print("\nREADY" if ready else "\nNOT READY")


def cmd_setup(args):
    os.makedirs(TOOLS, exist_ok=True)
    if not os.path.isdir(VENV):
        print("Making a private tools folder (~/.not-another-edit)...")
        run([sys.executable, "-m", "venv", VENV], "Making the tools folder")
    py = venv_python()
    print("Installing speech-to-text and the renderer (a few minutes, one time)...")
    run([py, "-m", "pip", "install", "--quiet", "--upgrade", "pip"], "Updating pip")
    run([py, "-m", "pip", "install", "--quiet", "faster-whisper", "playwright", "numpy"], "Installing tools")
    if not chrome_path():
        print("No Chrome found, so getting the renderer its own browser...")
        run([py, "-m", "playwright", "install", "chromium"], "Installing the browser")
    print("Done. The speech model downloads the first time you transcribe (about 500 MB, one time).")


# ---------------------------------------------------------------- new / transcribe / takes
def cmd_new(args):
    f, rest = flags(args, ["raw", "style"])
    if len(rest) != 1 or "raw" not in f:
        die('Usage: ete.py new "<edit folder>" --raw "<clips folder>" [--style "<style folder>"]')
    need("ffprobe")
    work, raw = os.path.abspath(rest[0]), os.path.abspath(os.path.expanduser(f["raw"]))
    if not os.path.isdir(raw):
        die(f'No folder at "{raw}".')
    exts = (".mp4", ".mov", ".m4v", ".mkv")
    names = [n for n in os.listdir(raw) if n.lower().endswith(exts) and not n.startswith(".")]
    if not names:
        die(f"No video clips in {raw}.")
    names.sort(key=natural_key)
    clips = [probe(os.path.join(raw, n)) for n in names]
    fps_set = {c["fps"] for c in clips}
    os.makedirs(work, exist_ok=True)
    style = os.path.abspath(f["style"]) if f.get("style") else find_style()
    pj = {"raw": raw, "clips": clips, "fps": clips[0]["fps"], "style": style, "created": today(),
          "name": os.path.basename(work)}
    wj(os.path.join(work, "project.json"), pj)
    total = sum(c["duration"] for c in clips)
    print(f"Edit folder: {work}\nClips, in this order ({total:.0f} s of footage):")
    for c in clips:
        print(f"  {c['file']:<20} {c['duration']:5.1f} s  {c['width']}x{c['height']}  {float(Fraction(c['fps'])):.2f} fps"
              + ("  (no sound!)" if not c["audio"] else "") + ("  HDR" if c["hdr"] else ""))
    if len(fps_set) > 1:
        print(f"WARNING: the clips don't share one frame rate ({', '.join(sorted(fps_set))}). The edit uses "
              f"{clips[0]['fps']} (the first clip's); say so to them.")
    if any(c["hdr"] for c in clips):
        print("NOTE: some clips are HDR. The edit converts them to normal (SDR) colour for Instagram.")
    print(f"Style: {style or 'none found yet (suggest /not-another-edit first, or edit without one)'}")


def cmd_transcribe(args):
    f, rest = flags(args, ["prompt", "model"])
    if len(rest) != 1:
        die('Usage: ete.py transcribe WORK [--prompt "names, the comment keyword"] [--model small.en]')
    work = os.path.abspath(rest[0])
    pj = project(work)
    need("ffmpeg")
    py = venv_python()
    if not has_modules(py, ["faster_whisper", "numpy"]):
        die("Speech-to-text isn't installed yet. Ask them, then run: python3 ete.py setup")
    jobs = [{"path": os.path.join(pj["raw"], c["file"]), "out": os.path.join(work, "transcripts", c["file"] + ".json")}
            for c in pj["clips"]]
    wj(os.path.join(work, "transcripts", "_jobs.json"), {"model": f.get("model", "small.en"),
                                                         "prompt": f.get("prompt", ""), "jobs": jobs})
    r = subprocess.run([py, os.path.join(SK, "scripts", "transcribe_worker.py"), os.path.join(work, "transcripts", "_jobs.json")])
    if r.returncode != 0:
        die("Transcribing failed (see above).")
    write_transcript(work, pj)


def segments_for(words, gap=0.7):
    segs, cur = [], []
    for w in words:
        if cur and w["start"] - cur[-1]["end"] > gap:
            segs.append(cur)
            cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    return segs


def norm(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).split()


def all_segments(work, pj):
    out = []
    for c in pj["clips"]:
        words = rj(os.path.join(work, "transcripts", c["file"] + ".json"), [])
        for s in segments_for(words):
            out.append({"clip": c["file"], "in": s[0]["start"], "out": s[-1]["end"],
                        "text": " ".join(w["word"] for w in s), "words": s})
    # A segment that's said again shortly after is a retake: keep the last one.
    for i, s in enumerate(out):
        a = norm(s["text"])
        for j in range(i + 1, min(i + 4, len(out))):
            b = norm(out[j]["text"])
            if len(a) >= 2 and a[:2] == b[:2] and difflib.SequenceMatcher(None, a, b).ratio() >= 0.5:
                s["retake_of_later"] = j
                break
    return out


def write_transcript(work, pj):
    segs = all_segments(work, pj)
    lines = ["Every line, in clip order. [RETAKE] = said again later, so the later one is probably the keeper.", ""]
    clip = None
    for i, s in enumerate(segs):
        if s["clip"] != clip:
            clip = s["clip"]
            lines.append(f"## {clip}")
        tag = "  [RETAKE]" if "retake_of_later" in s else ""
        lines.append(f"  S{i + 1:<3} {s['in']:6.2f}-{s['out']:6.2f}  {s['text']}{tag}")
    with open(os.path.join(work, "transcript.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nSaved: {os.path.join(work, 'transcript.txt')}")


def cmd_edl(args):
    f, rest = flags(args, ["auto!"])
    if len(rest) != 1 or not f.get("auto"):
        die('Usage: ete.py edl WORK --auto   (then read edl.json and change anything that isn\'t right)')
    work = os.path.abspath(rest[0])
    pj = project(work)
    segs = all_segments(work, pj)
    pieces = []
    for s in segs:
        if "retake_of_later" in s:
            continue
        if pieces and pieces[-1]["clip"] == s["clip"] and s["in"] - pieces[-1]["out"] < 2.0:
            pieces[-1]["out"] = s["out"]
            pieces[-1]["text"] += " " + s["text"]
        else:
            pieces.append({"clip": s["clip"], "in": round(s["in"], 3), "out": round(s["out"], 3), "text": s["text"]})
    wj(os.path.join(work, "edl.json"), {"pieces": pieces})
    print(f"Draft cut list: {len(pieces)} pieces (retakes left out). Check it against the script:")
    for i, p in enumerate(pieces):
        print(f"  {i + 1:>2}. {p['clip']:<14} {p['in']:6.2f}-{p['out']:6.2f}  {p['text']}")
    print(f"\nSaved: {os.path.join(work, 'edl.json')}. Edit it if a take or a line is wrong, then run cut.")


# ---------------------------------------------------------------- cut
def snap(t, fps, up=False):
    k = t * fps
    return (math.ceil(k - 1e-6) if up else math.floor(k + 1e-6)) / fps


def cmd_cut(args):
    f, rest = flags(args, ["gap", "pad-in", "pad-out", "no-proxy!"])
    if len(rest) != 1:
        die('Usage: ete.py cut WORK [--gap 0.12]   (silences longer than this are cut out)')
    work = os.path.abspath(rest[0])
    pj = project(work)
    edl = rj(os.path.join(work, "edl.json"))
    if not edl:
        die("No edl.json yet. Run: ete.py edl WORK --auto, then check it.")
    fps = float(Fraction(pj["fps"]))
    style = find_style(pj)
    default_gap = 0.12
    if style:
        cut = (rj(os.path.join(style, "settings.json"), {}) or {}).get("cut", [])
        default_gap = 0.12 if "deadspace" in cut else 0.35
    gap = float(f.get("gap", default_gap))
    pad_in, pad_out = float(f.get("pad-in", 0.05)), float(f.get("pad-out", 0.07))
    split_at = max(gap, pad_in + pad_out + 0.02)
    clipinfo = {c["file"]: c for c in pj["clips"]}
    spans = []
    for piece in edl["pieces"]:
        clip = piece["clip"]
        dur = clipinfo[clip]["duration"]
        words = [w for w in rj(os.path.join(work, "transcripts", clip + ".json"), [])
                 if w["end"] > piece["in"] - 0.02 and w["start"] < piece["out"] + 0.02]
        quiet = (rj(os.path.join(work, "transcripts", clip + ".silence.json"), {}) or {}).get("silences")
        a, b = max(0.0, piece["in"] - pad_in), min(dur, piece["out"] + pad_out)
        if quiet is not None:
            # Use the sound itself: trim quiet edges, then cut every quiet stretch longer than the gap.
            keep = [[a, b]]
            for s0, s1 in quiet:
                nxt = []
                for x0, x1 in keep:
                    if s1 <= x0 or s0 >= x1:
                        nxt.append([x0, x1])
                        continue
                    lead, trail = s0 <= x0 + 0.01, s1 >= x1 - 0.01
                    if lead and trail:
                        continue  # all quiet
                    if lead:
                        nxt.append([max(x0, s1 - pad_in), x1])
                    elif trail:
                        nxt.append([x0, min(x1, s0 + pad_out)])
                    elif s1 - s0 > gap and (s1 - pad_in) - (s0 + pad_out) > 0.03:
                        nxt += [[x0, s0 + pad_out], [s1 - pad_in, x1]]
                    else:
                        nxt.append([x0, x1])
                keep = nxt
        else:
            # No sound map: fall back to the gaps between words.
            keep, cur = [], None
            for w in words:
                if cur and w["start"] - cur[1] > split_at:
                    keep.append([cur[0], cur[1] + pad_out])
                    cur = None
                cur = [cur[0] if cur else max(a, w["start"] - pad_in), w["end"]]
            if cur:
                keep.append([cur[0], min(b, cur[1] + pad_out)])
            keep = keep or [[a, b]]
        keep = [k for k in keep if k[1] - k[0] > 0.05]
        for x0, x1 in keep:
            spans.append({"clip": clip, "in": x0, "out": x1, "words": []})
        # every word goes with the span it sits in (or the nearest one)
        mine = spans[len(spans) - len(keep):]
        for w in words:
            mid = (w["start"] + w["end"]) / 2
            best = min(mine, key=lambda s: 0 if s["in"] <= mid <= s["out"] else min(abs(mid - s["in"]), abs(mid - s["out"])), default=None)
            if best is not None:
                best["words"].append(dict(w, start=min(max(w["start"], best["in"]), best["out"]),
                                          end=min(max(w["end"], best["in"]), best["out"])))
    # snap to the source frame grid so sound and picture stay locked together
    out_t, pieces, out_words = 0.0, [], []
    for s in spans:
        a, b = snap(max(0, s["in"]), fps), snap(s["out"], fps, up=True)
        if pieces and pieces[-1]["clip"] == s["clip"] and a <= pieces[-1]["out"] + 0.5 / fps:
            prev = pieces[-1]
            prev_dur = prev["out"] - prev["in"]
            prev["out"] = max(prev["out"], b)
            out_t += (prev["out"] - prev["in"]) - prev_dur
            base = prev["at"] - prev["in"]
        else:
            if b - a < 1.5 / fps:
                continue
            pieces.append({"clip": s["clip"], "in": round(a, 6), "out": round(b, 6), "at": round(out_t, 6)})
            out_t += b - a
            base = pieces[-1]["at"] - a
        for w in s["words"]:
            out_words.append({"start": round(max(0.0, w["start"] + base), 3), "end": round(w["end"] + base, 3),
                              "word": w["word"]})
    out_words.sort(key=lambda w: w["start"])
    wj(os.path.join(work, "cut.json"), {"fps": pj["fps"], "gap": gap, "duration": round(out_t, 3), "pieces": pieces})
    wj(os.path.join(work, "words.json"), out_words)
    write_words_txt(work, out_words)
    print(f"Cut: {len(pieces)} pieces, {out_t:.1f} s long (silences over {gap} s removed).")
    if not f.get("no-proxy"):
        make_proxy(work, pj, pieces)
    print(f"Words with times: {os.path.join(work, 'words.txt')}")


def write_words_txt(work, words):
    lines, line = [], []
    for i, w in enumerate(words):
        line.append(f"{i}:{w['word']}")
        if len(line) == 10 or w["word"].endswith((".", "?", "!")):
            lines.append(f"{words[i - len(line) + 1]['start']:7.2f}  " + " ".join(line))
            line = []
    if line:
        lines.append(f"{words[len(words) - len(line)]['start']:7.2f}  " + " ".join(line))
    with open(os.path.join(work, "words.txt"), "w", encoding="utf-8") as fh:
        fh.write("Start time, then index:word. Fix a misheard word with: ete.py fix WORK 12=Word\n" + "\n".join(lines) + "\n")


def video_chain(pj, extra=""):
    """Crop to 9:16 (centre), optional zoom, scale to 1080x1920."""
    hdr = any(c.get("hdr") for c in pj["clips"])
    tone = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p," if hdr else "")
    crop = "crop='trunc(min(iw,ih*9/16)/2)*2':'trunc(min(ih,iw*16/9)/2)*2'"
    return f"{tone}{crop}{(',' + extra) if extra else ''}"


def make_proxy(work, pj, pieces):
    need("ffmpeg")
    tmp = os.path.join(work, "render", "proxy")
    os.makedirs(tmp, exist_ok=True)
    listing = []
    print("Making the preview video for the storyboard...")
    for i, p in enumerate(pieces):
        out = os.path.join(tmp, f"p{i:03d}.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{p['in']:.6f}", "-t", f"{p['out'] - p['in']:.6f}",
             "-i", os.path.join(pj["raw"], p["clip"]), "-map", "0:v:0", "-map", "0:a:0?",
             "-vf", video_chain(pj, "scale=540:960,fps=30"), "-af", "aresample=48000",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "96k", "-ac", "2", out], f"Preview piece {i + 1}")
        listing.append(f"file '{out}'")
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        fh.write("\n".join(listing) + "\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
         "-movflags", "+faststart", os.path.join(work, "proxy.mp4")], "Joining the preview")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Preview: {os.path.join(work, 'proxy.mp4')}")


def cmd_fix(args):
    if len(args) < 2:
        die('Usage: ete.py fix WORK 12=DESLOP 40=Pinterest   (only to match what was really said)')
    work = os.path.abspath(args[0])
    words = rj(os.path.join(work, "words.json"))
    if words is None:
        die("Run cut first.")
    for a in args[1:]:
        m = re.match(r"^(\d+)=(.+)$", a)
        if not m or int(m.group(1)) >= len(words):
            die(f'"{a}" should look like 12=Word, with an index from words.txt.')
        i = int(m.group(1))
        print(f"  {i}: {words[i]['word']} -> {m.group(2)}")
        words[i]["word"] = m.group(2)
    wj(os.path.join(work, "words.json"), words)
    write_words_txt(work, words)


# ---------------------------------------------------------------- style
def style_bits(style):
    if not style:
        return {"locked": {}, "cut": [], "brand": {"name": "Plain", "paper": "#FFFFFF", "ink": "#111111",
                                                  "accent": "#FFFFFF", "font": "Helvetica Neue"}, "lines": {}}
    return {"locked": rj(os.path.join(style, "locked.json"), {}) or {},
            "cut": (rj(os.path.join(style, "settings.json"), {}) or {}).get("cut", []),
            "brand": rj(os.path.join(style, "brand.json"), {}) or {},
            "lines": rj(os.path.join(style, "lines.json"), {}) or {}}


def cmd_style(args):
    if len(args) != 1:
        die("Usage: ete.py style WORK")
    work = os.path.abspath(args[0])
    pj = project(work)
    style = find_style(pj)
    if not style:
        print("No style yet. Plain captions only (white, three words at a time) unless they build one with /not-another-edit.")
        return
    b = style_bits(style)
    print(f"Style: {style}\nBrand: {json.dumps(b['brand'], ensure_ascii=False)}\nSlop cut: {', '.join(b['cut']) or 'none'}\n")
    for sec, items in b["locked"].items():
        for it in items:
            print(f"{sec} · {it['id']} · {it.get('label', '')}" + (f"  (their note: {it['note']})" if it.get("note") else ""))
            print(f'  {{"type": "{it["type"]}", "params": {json.dumps(it["params"], ensure_ascii=False)}}}')
    print("\nRead STYLE.md in full too: the written rules and 'Feedback from edits' win over this list.")


# ---------------------------------------------------------------- plan -> timeline
def tags_for(params):
    t = set()
    for k, v in (params or {}).items():
        if k == "entrance" and v == "pop":
            t.add("pop")
        if k == "radius" and isinstance(v, (int, float)) and v > 0:
            t.add("corners")
        if k == "italicWord" and v:
            t.add("claude-look")
        if k == "style" and v == "tiny":
            t.add("claude-look")
    return t


def library_paths(style):
    lib = os.path.join(NAE_SK, "page", "library.js")
    if not os.path.isfile(lib) and style and os.path.isfile(os.path.join(style, "page", "library.js")):
        lib = os.path.join(style, "page", "library.js")
    custom = os.path.join(style, "page", "custom.js") if style else None
    return lib, (custom if custom and os.path.isfile(custom) else None)


def known_types(style):
    types = set(BUILT_IN_TYPES)
    _, custom = library_paths(style)
    if custom:
        with open(custom, encoding="utf-8") as fh:
            types |= set(re.findall(r"NAE_LIB\.([A-Za-z_]\w*)\s*=", fh.read()))
    return types


def beat_variant(beat, option=None):
    """The overlays, zoom and transition for a beat with one of its options applied."""
    ov = list(beat.get("overlays", []))
    zoom, trans, sfx = beat.get("zoom"), beat.get("transition_out"), list(beat.get("sfx", []))
    opts = beat.get("options") or {}
    key = option or beat.get("pick") or (sorted(opts)[0] if opts else None)
    if key and key in opts:
        o = opts[key]
        ov += o.get("overlays", [])
        zoom = o.get("zoom", zoom)
        trans = o.get("transition_out", trans)
        sfx += o.get("sfx", [])
    return ov, zoom, trans, sfx, key


def overlay_item(o, beat, dur_total):
    at = float(o.get("at", beat["start"]))
    dur = float(o.get("dur", float(beat["end"]) - at))
    params = dict(o.get("params", {}))
    for k in ("lines", "word", "text", "src"):
        if k in o:
            params[k] = o[k]
    return {"type": o["type"], "params": params, "at": round(at, 3), "dur": round(max(0.05, min(dur, dur_total - at)), 3),
            "label": o.get("label") or o["type"], "beat": beat["id"]}


def build_timeline(work, pj, plan, option_override=None):
    """Flatten plan.json into on-screen items, zooms, flashes and sound effects (all in output seconds)."""
    cut = rj(os.path.join(work, "cut.json"))
    words = rj(os.path.join(work, "words.json"), [])
    total = cut["duration"]
    items, zooms, sfx = [], [], []
    no_caps = []
    for beat in plan["beats"]:
        ov, zoom, trans, bsfx, _ = beat_variant(beat, (option_override or {}).get(beat["id"]))
        if beat.get("captions") is False:
            no_caps.append((float(beat["start"]), float(beat["end"])))
        for o in ov:
            if o.get("type") == "zoom":
                zoom = {**(o.get("params") or {}), "at": o.get("at", beat["start"]), "dur": o.get("dur")}
                continue
            items.append(overlay_item(o, beat, total))
            if o.get("captions") is False or (o.get("type") == "visual" and (o.get("params") or {}).get("layout") == "full"):
                it = items[-1]
                no_caps.append((it["at"], it["at"] + it["dur"]))
        if zoom and zoom.get("kind", "punch") != "none":
            at = float(zoom.get("at", beat["start"]))
            dur = float(zoom.get("dur") or (float(beat["end"]) - at))
            zooms.append({"kind": zoom.get("kind", "punch"), "amount": float(zoom.get("amount", 1.15)),
                          "ms": float(zoom.get("ms", 1400)), "at": round(at, 3), "dur": round(dur, 3), "beat": beat["id"]})
        if trans and trans.get("kind", "cut") != "cut":
            ms = float(trans.get("ms", 240 if trans.get("kind") == "flash" else 400))
            items.append({"type": trans["kind"], "params": {"color": trans.get("color", "white" if trans["kind"] == "flash" else "black"), "ms": ms},
                          "at": round(float(beat["end"]) - ms / 2000, 3), "dur": round(ms / 1000, 3),
                          "label": f"{trans['kind']} into the next beat", "beat": beat["id"]})
            # captions stop at a flash or dip, so the last line doesn't hang over the next shot
            no_caps.append((float(beat["end"]) - ms / 2000, float(beat["end"]) + ms / 2000))
        for s in bsfx:
            sfx.append({"file": s["file"], "at": float(s.get("at", beat["start"])), "gain": float(s.get("gain", -10))})
    cap = plan.get("captions")
    if cap:
        # captions run the whole video except where a beat or a full-screen visual turns them off
        windows, start = [], 0.0
        for a, b in sorted(no_caps):
            if a > start:
                windows.append((start, a))
            start = max(start, b)
        if start < total:
            windows.append((start, total))
        for a, b in windows:
            ws = [[round((w["start"] - a) * 1000), round((w["end"] - a) * 1000), w["word"]]
                  for w in words if w["start"] >= a - 0.01 and w["start"] < b]
            if ws:
                items.insert(0, {"type": "captions", "params": cap.get("params", {}), "at": round(a, 3),
                                 "dur": round(b - a, 3), "words": ws, "label": "captions", "beat": "*"})
    return {"duration": total, "items": items, "zooms": zooms, "sfx": sfx}


def validate_plan(work, pj, plan):
    style = find_style(pj)
    b = style_bits(style)
    types = known_types(style) | {"flash", "dip"}
    cut = set(b["cut"])
    problems, warnings = [], []
    total = rj(os.path.join(work, "cut.json"))["duration"]
    ids = set()
    last_layout, repeats = None, []
    for beat in plan.get("beats", []):
        bid = beat.get("id")
        if not bid or bid in ids:
            problems.append(f"Every beat needs its own id (problem at {bid}).")
        ids.add(bid)
        if not (0 <= float(beat["start"]) < float(beat["end"]) <= total + 0.05):
            problems.append(f"{bid}: start/end must be inside the video (0 to {total:.2f} s).")
        variants = [None] + sorted((beat.get("options") or {}).keys())
        for opt in variants:
            ov, zoom, trans, bsfx, _ = beat_variant(beat, opt)
            for o in ov:
                t = o.get("type")
                if t not in types:
                    problems.append(f"{bid}: \"{t}\" isn't an option type (library.js or custom.js).")
                    continue
                if t in ("transition",):
                    problems.append(f"{bid}: put transitions in transition_out, not overlays.")
                broken = tags_for(o.get("params")) & cut
                if broken:
                    problems.append(f"{bid}: a {t} breaks a slop rule they cut ({', '.join(sorted(broken))}).")
                if t == "visual":
                    src = o.get("src") or (o.get("params") or {}).get("src")
                    if not src:
                        problems.append(f"{bid}: a visual needs a real image (\"src\": \"assets/...\"). Never a stand-in.")
                    elif not os.path.isfile(os.path.join(work, src)):
                        problems.append(f"{bid}: can't find {src} in the edit folder.")
                at = float(o.get("at", beat["start"]))
                if not (float(beat["start"]) - 0.01 <= at <= float(beat["end"])):
                    warnings.append(f"{bid}: a {t} starts outside its beat ({at:.2f} s).")
            if trans and trans.get("kind", "cut") not in RENDER_TRANSITIONS:
                problems.append(f"{bid}: transition \"{trans.get('kind')}\" can't be rendered yet. Use cut, flash or dip.")
            if zoom and zoom.get("kind", "punch") not in ("none", "punch", "push"):
                problems.append(f"{bid}: zoom kind must be none, punch or push.")
            for s in bsfx:
                if not os.path.isfile(s["file"] if os.path.isabs(s["file"]) else os.path.join(work, s["file"])):
                    problems.append(f"{bid}: can't find the sound {s['file']}.")
        layouts = tuple(sorted(o.get("type") + str((o.get("params") or {}).get("layout", "")) for o in beat_variant(beat)[0]))
        if layouts and layouts == last_layout:
            repeats.append(bid)
        last_layout = layouts
    if repeats:
        warnings.append(f"{', '.join(repeats)} repeat the on-screen layout of the beat before. Fine for a numbered "
                        "list; otherwise vary it.")
    if "sfx" in cut:
        n = sum(len(beat_variant(bt)[3]) for bt in plan.get("beats", []))
        if n > max(2, len(plan.get("beats", [])) // 2):
            warnings.append(f"{n} sound effects: they cut 'a sound on every graphic'. Keep only the moments that matter.")
    return problems, warnings


def write_page_data(work, pj, plan, mode):
    style = find_style(pj)
    b = style_bits(style)
    lib, custom = library_paths(style)
    page = os.path.join(work, "page")
    os.makedirs(page, exist_ok=True)
    for name in ("timeline.js", "board.html", "board.js", "board.css", "render.html", "render.js"):
        shutil.copy2(os.path.join(ENGINE, name), os.path.join(page, name))
    shutil.copy2(lib, os.path.join(page, "library.js"))
    if custom:
        shutil.copy2(custom, os.path.join(page, "custom.js"))
    else:
        with open(os.path.join(page, "custom.js"), "w") as fh:
            fh.write("/* no custom options */\n")
    brand = dict(b["brand"])
    if brand.get("fontFile") and style:
        brand["fontFile"] = "file://" + os.path.join(style, brand["fontFile"])
    tl = build_timeline(work, pj, plan)
    beats = []
    for beat in plan["beats"]:
        opts = sorted((beat.get("options") or {}).keys())
        variants = {}
        for key in (opts or [None]):
            t2 = build_timeline(work, pj, plan, {beat["id"]: key} if key else None)
            a, z = float(beat["start"]), float(beat["end"])
            variants[key or "-"] = {
                "label": ((beat.get("options") or {}).get(key) or {}).get("label", "") if key else "",
                "items": [i for i in t2["items"] if i["at"] < z and i["at"] + i["dur"] > a],
                "zooms": [zz for zz in t2["zooms"] if zz["at"] < z and zz["at"] + zz["dur"] > a]}
        beats.append({"id": beat["id"], "start": float(beat["start"]), "end": float(beat["end"]),
                      "say": beat.get("say", ""), "status": beat.get("status", "new"), "note": beat.get("note", ""),
                      "pick": beat.get("pick") or (opts[0] if opts else "-"), "options": opts, "variants": variants})
    for it in tl["items"]:
        if it["type"] == "visual" and it["params"].get("src") and not str(it["params"]["src"]).startswith(("http", "file:", "../")):
            it["params"]["src"] = "../" + it["params"]["src"]
    for bt in beats:
        for v in bt["variants"].values():
            for it in v["items"]:
                if it["type"] == "visual" and it["params"].get("src") and not str(it["params"]["src"]).startswith(("http", "file:", "../")):
                    it["params"]["src"] = "../" + it["params"]["src"]
    data = {"brand": brand, "lines": b["lines"], "round": plan.get("round", 1), "title": plan.get("title", pj["name"]),
            "duration": tl["duration"], "timeline": tl, "beats": beats, "proxy": "../proxy.mp4"}
    with open(os.path.join(page, "data.js"), "w", encoding="utf-8") as fh:
        fh.write("window.ETE = " + json.dumps(data, ensure_ascii=False) + ";\n")
    return os.path.join(page, "board.html" if mode == "board" else "render.html"), tl


def cmd_board(args):
    if len(args) != 1:
        die("Usage: ete.py board WORK   (after writing plan.json)")
    work = os.path.abspath(args[0])
    pj = project(work)
    plan = rj(os.path.join(work, "plan.json"))
    if not plan:
        die("No plan.json yet. Read references/storyboard.md and write it.")
    problems, warnings = validate_plan(work, pj, plan)
    for w in warnings:
        print("WARNING:", w)
    if problems:
        die("Fix these before showing them:\n  " + "\n  ".join(problems))
    page, tl = write_page_data(work, pj, plan, "board")
    n_ok = sum(1 for bt in plan["beats"] if bt.get("status") == "approved")
    print(f"Storyboard round {plan.get('round', 1)}: {len(plan['beats'])} beats ({n_ok} approved), "
          f"{tl['duration']:.1f} s, {len(tl['items'])} things on screen, {len(tl['zooms'])} zooms.\nPage: {page}")


def cmd_review(args):
    if len(args) != 2:
        die('Usage: ete.py review WORK "<file with their pasted review>"')
    work = os.path.abspath(args[0])
    plan = rj(os.path.join(work, "plan.json"))
    with open(os.path.expanduser(args[1]), encoding="utf-8") as fh:
        text = fh.read()
    rnd = plan.get("round", 1)
    os.makedirs(os.path.join(work, "reviews"), exist_ok=True)
    with open(os.path.join(work, "reviews", f"round-{rnd}.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    beats = {b["id"]: b for b in plan["beats"]}
    approved, changes, picks, unknown, overall = [], [], [], [], ""
    for raw in text.splitlines():
        line = raw.strip().lstrip("-• ").strip()
        if not line or line.lower().startswith("edit this video"):
            continue
        if line.lower().startswith("overall:"):
            overall = line.split(":", 1)[1].strip()
            continue
        m = re.match(r"^(B\d+)\s+(approve|change|pick\s+[A-Z])\b\s*:?\s*(.*)$", line, re.I)
        if not m or m.group(1).upper() not in beats:
            unknown.append(line)
            continue
        b = beats[m.group(1).upper()]
        verb, note = m.group(2).lower(), m.group(3).strip()
        if verb.startswith("pick"):
            b["pick"] = verb.split()[-1].upper()
            picks.append((b["id"], b["pick"], note))
            if note:
                b["status"], b["note"] = "change", note
            else:
                b["status"] = "approved"
        elif verb == "approve":
            b["status"], b["note"] = "approved", note
            approved.append(b["id"])
        else:
            b["status"], b["note"] = "change", note
            changes.append((b["id"], note))
    plan["round"] = rnd + 1
    wj(os.path.join(work, "plan.json"), plan)
    print(f"Approved: {', '.join(approved) or 'none'}")
    for bid, k, note in picks:
        print(f"Picked {k} for {bid}" + (f'  ->  "{note}"' if note else ""))
    for bid, note in changes:
        print(f'Change {bid}: "{note}"')
    if overall:
        print(f'Overall: "{overall}"')
    if unknown:
        print("Couldn't match (read these yourself): " + " | ".join(unknown))
    left = [b["id"] for b in plan["beats"] if b.get("status") != "approved"]
    print("Everything is approved. Render it." if not left else f"Still to approve: {', '.join(left)}")


# ---------------------------------------------------------------- render
def zoom_filter(z, piece_at, fps_str, n_frames):
    """Zoom for one sub-piece. Returns a filter string for the 9:16 crop stage (before scaling)."""
    if not z:
        return f"scale={OUT_W}:{OUT_H}:flags=lanczos"
    A = z["amount"]
    if z["kind"] == "punch":
        return (f"crop='trunc(iw/{A}/2)*2':'trunc(ih/{A}/2)*2':'(iw-ow)/2':'(ih-oh)*0.45',"
                f"scale={OUT_W}:{OUT_H}:flags=lanczos")
    d = max(0.1, z["ms"] / 1000)
    fps = float(Fraction(fps_str))
    expr = f"1+({A}-1)*(1-pow(1-min(1,max(0,({piece_at:.6f}+on/{fps:.6f}-{z['at']:.6f})/{d:.6f})),3))"
    return (f"zoompan=z='{expr}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*0.45':d=1:s={OUT_W}x{OUT_H}:fps={fps_str}")


def cmd_render(args):
    f, rest = flags(args, ["overlay-fps", "keep!"])
    if len(rest) != 1:
        die("Usage: ete.py render WORK [--overlay-fps 30]")
    work = os.path.abspath(rest[0])
    pj = project(work)
    need("ffmpeg")
    plan = rj(os.path.join(work, "plan.json"))
    cut = rj(os.path.join(work, "cut.json"))
    if not plan or not cut:
        die("Needs cut.json and an approved plan.json first.")
    problems, warnings = validate_plan(work, pj, plan)
    if problems:
        die("Fix these first:\n  " + "\n  ".join(problems))
    left = [b["id"] for b in plan["beats"] if b.get("status") != "approved"]
    if left:
        print(f"WARNING: not approved yet: {', '.join(left)}. Only render if they said to go ahead.")
    py = venv_python()
    if not has_modules(py, ["playwright"]):
        die("The renderer isn't installed yet. Ask them, then run: python3 ete.py setup")
    fps_str = pj["fps"]
    fps = float(Fraction(fps_str))
    rdir = os.path.join(work, "render")
    os.makedirs(rdir, exist_ok=True)
    page, tl = write_page_data(work, pj, plan, "render")
    wj(os.path.join(rdir, "timeline.json"), tl)

    # 1. picture: each piece at full quality, zoomed where the plan says, at the source frame rate
    print(f"Step 1 of 4: cutting the picture ({len(cut['pieces'])} pieces, {fps:.2f} fps)...")
    subs = []
    for p in cut["pieces"]:
        a, b = p["in"], p["out"]
        o = p["at"]
        bounds = {a, b}
        for z in tl["zooms"]:
            for t in (z["at"], z["at"] + z["dur"]):
                src_t = a + (t - o)
                if a < src_t < b:
                    bounds.add(snap(src_t, fps))
        pts = sorted(bounds)
        for s, e in zip(pts, pts[1:]):
            if e - s < 0.5 / fps:
                continue
            mid_out = o + ((s + e) / 2 - a)
            z = next((z for z in tl["zooms"] if z["at"] <= mid_out < z["at"] + z["dur"]), None)
            subs.append({"clip": p["clip"], "in": s, "out": e, "at": o + (s - a), "zoom": z})
    listing = []
    for i, s in enumerate(subs):
        out = os.path.join(rdir, f"v{i:03d}.mp4")
        n_frames = round((s["out"] - s["in"]) * fps)
        vf = video_chain(pj, zoom_filter(s["zoom"], s["at"], fps_str, n_frames)) + ",format=yuv420p"
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s['in']:.6f}", "-i", os.path.join(pj["raw"], s["clip"]),
             "-frames:v", str(n_frames), "-map", "0:v:0", "-vf", vf, "-r", fps_str, "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out], f"Picture piece {i + 1}")
        listing.append(f"file '{out}'")
    with open(os.path.join(rdir, "video.txt"), "w") as fh:
        fh.write("\n".join(listing) + "\n")
    base = os.path.join(rdir, "base.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(rdir, "video.txt"),
         "-c", "copy", base], "Joining the picture")

    # 2. sound: same pieces, tiny fades so cuts don't click, then loudness for Instagram, then sound effects
    print("Step 2 of 4: cutting the sound...")
    alist = []
    for i, p in enumerate(cut["pieces"]):
        d = p["out"] - p["in"]
        out = os.path.join(rdir, f"a{i:03d}.wav")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{p['in']:.6f}", "-t", f"{d:.6f}", "-i",
             os.path.join(pj["raw"], p["clip"]), "-map", "0:a:0",
             "-af", f"aresample=48000,afade=t=in:d=0.006,afade=t=out:st={max(0, d - 0.008):.6f}:d=0.008,apad=whole_dur={d:.6f}",
             "-ac", "2", "-c:a", "pcm_s16le", out], f"Sound piece {i + 1}")
        alist.append(f"file '{out}'")
    with open(os.path.join(rdir, "audio.txt"), "w") as fh:
        fh.write("\n".join(alist) + "\n")
    voice = os.path.join(rdir, "voice.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(rdir, "audio.txt"),
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000", "-c:a", "pcm_s16le", voice], "Joining the sound")
    audio = voice
    if tl["sfx"]:
        inputs, fl = ["-i", voice], []
        for k, s in enumerate(tl["sfx"]):
            path = s["file"] if os.path.isabs(s["file"]) else os.path.join(work, s["file"])
            inputs += ["-i", path]
            ms = int(round(s["at"] * 1000))
            fl.append(f"[{k + 1}:a]aresample=48000,volume={s['gain']}dB,adelay={ms}|{ms}[s{k}]")
        mix = "".join(f"[s{k}]" for k in range(len(tl["sfx"])))
        fl.append(f"[0:a]{mix}amix=inputs={len(tl['sfx']) + 1}:duration=first:normalize=0[out]")
        audio = os.path.join(rdir, "audio.wav")
        run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fl), "-map", "[out]",
             "-c:a", "pcm_s16le", audio], "Mixing sound effects")

    # 3. graphics: drawn by the same option library as their style page, frame by frame, with see-through background
    ofps = f.get("overlay-fps") or ("30" if fps > 31 else fps_str)
    print(f"Step 3 of 4: drawing captions and graphics ({ofps} fps)...")
    overlay = os.path.join(rdir, "overlay.mov")
    r = subprocess.run([py, os.path.join(SK, "scripts", "render_worker.py"), page, overlay, str(ofps),
                        f"{cut['duration']:.6f}", chrome_path() or ""])
    if r.returncode != 0:
        die("Drawing the graphics failed (see above).")

    # 4. put it together at the source frame rate
    print("Step 4 of 4: putting it together...")
    final = os.path.join(work, f"{pj['name']}.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", overlay, "-i", audio, "-filter_complex",
         "[0:v][1:v]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]", "-map", "[v]", "-map", "2:a",
         "-r", fps_str, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{cut['duration']:.6f}", final], "Final render")
    if not f.get("keep"):
        for name in os.listdir(rdir):
            if re.match(r"^[va]\d{3}\.(mp4|wav)$", name):
                os.remove(os.path.join(rdir, name))
    print(f"Done: {final}")


def cmd_qa(args):
    if len(args) != 1:
        die("Usage: ete.py qa WORK")
    work = os.path.abspath(args[0])
    pj = project(work)
    final = os.path.join(work, f"{pj['name']}.mp4")
    if not os.path.isfile(final):
        die("No finished video yet. Run render.")
    out = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,r_frame_rate,nb_frames,duration:format=duration",
                          "-of", "json", final], "Reading the video"))
    v = next(s for s in out["streams"] if s["codec_type"] == "video")
    a = next((s for s in out["streams"] if s["codec_type"] == "audio"), None)
    cut = rj(os.path.join(work, "cut.json"))
    checks = [
        ("Frame rate matches the footage", v["r_frame_rate"] == pj["fps"], f"{v['r_frame_rate']} vs {pj['fps']}"),
        ("Size is 1080 x 1920", (v["width"], v["height"]) == (OUT_W, OUT_H), f"{v['width']}x{v['height']}"),
        ("Has sound", bool(a), ""),
        ("Length matches the cut", abs(float(out["format"]["duration"]) - cut["duration"]) < 0.1,
         f"{float(out['format']['duration']):.2f} s vs {cut['duration']:.2f} s"),
    ]
    if a:
        checks.append(("Sound and picture end together", abs(float(a.get("duration", 0)) - float(v.get("duration", 0))) < 0.06,
                       f"sound {float(a.get('duration', 0)):.2f} s, picture {float(v.get('duration', 0)):.2f} s"))
    for name, ok, detail in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" ({detail})" if detail else ""))
    plan = rj(os.path.join(work, "plan.json"), {"beats": []})
    qdir = os.path.join(work, "render", "qa")
    os.makedirs(qdir, exist_ok=True)
    frames = []
    for bt in plan["beats"]:
        t = (float(bt["start"]) + float(bt["end"])) / 2
        fp = os.path.join(qdir, f"{bt['id']}.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", final, "-frames:v", "1",
                        "-vf", "scale=270:480", fp], capture_output=True)
        if os.path.isfile(fp):
            frames.append(fp)
    if frames:
        cols = min(6, len(frames))
        sheet = os.path.join(qdir, "sheet.jpg")
        inputs = sum((["-i", fp] for fp in frames), [])
        rows = math.ceil(len(frames) / cols)
        layout = "|".join(f"{(i % cols) * 270}_{(i // cols) * 480}" for i in range(len(frames)))
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
                            f"xstack=inputs={len(frames)}:layout={layout}:fill=black" if len(frames) > 1 else "null",
                            "-frames:v", "1", sheet], capture_output=True, text=True)
        if r.returncode == 0:
            print(f"Contact sheet (one frame from the middle of each beat, in order, {cols} across, {rows} down): {sheet}")
    print(f"Video: {final}")


def cmd_feedback(args):
    if len(args) != 3:
        die('Usage: ete.py feedback STYLE "their words" "the rule it means"')
    path = os.path.join(os.path.abspath(args[0]), "STYLE.md")
    if not os.path.isfile(path):
        die(f"No STYLE.md in {args[0]}.")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    head = "## Feedback from edits"
    line = f"- {today()}: \"{args[1]}\" → {args[2]}"
    if head not in text:
        text = text.rstrip() + f"\n\n{head}\nNewest first. These are my corrections from real edits and they win over everything above.\n"
    idx = text.index(head)
    nl = text.index("\n", idx)
    after = text[nl + 1:]
    m = re.match(r"(Newest first[^\n]*\n)", after)
    insert_at = nl + 1 + (m.end() if m else 0)
    text = text[:insert_at] + line + "\n" + text[insert_at:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"Added to STYLE.md: {line}")


def cmd_open(args):
    if len(args) != 1:
        die("Usage: ete.py open PATH")
    path = os.path.abspath(args[0])
    opener = {"darwin": ["open"], "win32": ["cmd", "/c", "start", ""]}.get(sys.platform, ["xdg-open"])
    try:
        subprocess.Popen(opener + [path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Opened {path}")
    except OSError:
        print(f"Open this yourself: {path}")


COMMANDS = {"check": cmd_check, "setup": cmd_setup, "new": cmd_new, "transcribe": cmd_transcribe, "edl": cmd_edl,
            "cut": cmd_cut, "fix": cmd_fix, "style": cmd_style, "board": cmd_board, "review": cmd_review,
            "render": cmd_render, "qa": cmd_qa, "feedback": cmd_feedback, "open": cmd_open}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
