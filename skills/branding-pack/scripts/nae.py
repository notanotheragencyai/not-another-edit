#!/usr/bin/env python3
"""Branding Pack helper (part of Not Another Edit). Python 3 standard library only (ffmpeg is optional, for clips).

Usage: python3 nae.py <command> ...   (run a command with no arguments to see its usage)

  check                                  what's installed, and whether we're ready
  setup  [FOLDER]                        set up the folder they work in: My Style, Raw Clips, Edits, References, CLAUDE.md
  init   STYLE                           make a style folder (with an example round) and its picker page
  brand  STYLE [--name --paper --ink --accent --font --font-source google|system --font-file F --lines JSON]
  sheet  STYLE [--data FILE] [--logo-dark F] [--logo-light F] [--mark F]   the brand sheet (PNG + PDF in "Brand Sheet")
  logo   STYLE [--text --lines 1|2 --accent last|none|all --upper --font --mark-text]   a starter logo (no logo yet)
  face   STYLE CLIP [--start S] [--seconds N]   their talking clip for the previews (ffmpeg if present)
  visual STYLE IMAGE                     a real screenshot or photo for the visual options
  frames STYLE VIDEO [--every S]         contact sheet + stills of a reference video (needs ffmpeg)
  cut    STYLE ID ... | none             the slop they picked to cut (emoji pop corners sfx claude-look fps deadspace)
  round  STYLE first --sections "Captions" ... [--force]
  round  STYLE add "<Section>" TYPE 'JSON' "<label>" [--force]
  round  STYLE set ID 'JSON' ["<label>"] [--force]
  round  STYLE remove ID ... [--reason "..."]
  round  STYLE keep-only "<Section>" ID ...
  round  STYLE note "<Section>" "<what it's for>"
  round  STYLE changes "<line>" ...
  round  STYLE show
  picks  STYLE FILE                      file their pasted picks and move to the next round
  style-md STYLE [--check]               refresh the automatic parts of STYLE.md (or list what's still open)
  finish STYLE                           point Claude at STYLE.md for every future edit (CLAUDE.md note)
  open   STYLE [page|sheet|folder]       open the style page (default), the brand sheet, or the My Style folder
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(SK, "config.json")
CATALOGUE = os.path.join(SK, "catalogue.json")
PAGE_SRC = os.path.join(SK, "page")
TEMPLATE = os.path.join(SK, "templates", "STYLE.md")
PAGE_FILES = ["index.html", "app.js", "library.js", "style.css"]  # custom.js is theirs: copied once, never overwritten
BUILT_IN_TYPES = {"captions", "title", "keyword", "zoom", "visual", "label", "transition"}

SLOP = {
    "emoji": ("Emojis and stock icons",
              "No emojis or stock icons. When something needs a visual, use a real image: a screenshot, or a photo found on Google or Pinterest."),
    "pop": ("The pop",
            "Nothing bounces or scales onto the screen. Only animate what actually changes; everything else cuts in."),
    "corners": ("Rounded corners", "Square corners on every card, photo and label."),
    "sfx": ("A sound on every graphic", "Sound effects only on the moments that matter, never one on every graphic."),
    "claude-look": ("The Claude look",
                    "Only the brand colours and fonts in this file. No cream background, serif font, one word in italics or tiny labels unless the brand itself uses them."),
    "fps": ("Lips out of sync", "Render at the same frame rate the footage was filmed in. Never lower it."),
    "deadspace": ("Dead space", "Cut every silence longer than 0.12 seconds."),
}
CODES = {"Captions": "CAP", "Titles": "TTL", "Key words": "KEY", "Zooms": "ZM", "Visuals": "VIS",
         "Labels": "LBL", "Transitions": "TRN"}


# ---------------------------------------------------------------- small helpers
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def p(style, *parts):
    return os.path.join(style, *parts)


def need_style(style):
    if not os.path.isfile(p(style, "brand.json")):
        die(f'No style folder at "{style}". Make one first: python3 nae.py init "{style}"')


def parse_json_arg(s, what="params"):
    try:
        v = json.loads(s)
    except json.JSONDecodeError as e:
        die(f"Those {what} aren't valid JSON ({e}). Example: '{{\"words\": 2}}'")
    if not isinstance(v, dict):
        die(f"The {what} must be a JSON object, like '{{\"words\": 2}}'.")
    return v


def flags(args, names):
    """Pull --name value pairs (and bare --switches listed with a trailing '!') out of args."""
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


def tags_for(params):
    """Which slop rules an option would break."""
    t = set()
    for k, v in params.items():
        if k == "entrance" and v == "pop":
            t.add("pop")
        if k == "radius" and isinstance(v, (int, float)) and v > 0:
            t.add("corners")
        if k == "italicWord" and v:
            t.add("claude-look")
        if k == "style" and v == "tiny":
            t.add("claude-look")
    return t


def hex_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        die(f'"#{h}" isn\'t a colour I can read. Use a hex code like #FF4D00.')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def contrast(a, b):
    def lum(c):
        r, g, b_ = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in hex_rgb(c)]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b_
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------------------------------------------------------------- state
def settings(style):
    return rj(p(style, "settings.json"), {"cut": [], "counter": {}, "created": today()})


def save_settings(style, s):
    wj(p(style, "settings.json"), s)


def new_id(style, section):
    s = settings(style)
    code = CODES.get(section) or re.sub(r"[^A-Z]", "", section.upper())[:3] or "OPT"
    n = s["counter"].get(code, 0) + 1
    s["counter"][code] = n
    save_settings(style, s)
    return f"{code}{n}"


def known_types(style):
    types = set(BUILT_IN_TYPES)
    custom = p(style, "page", "custom.js")
    if os.path.isfile(custom):
        with open(custom, encoding="utf-8") as f:
            types |= set(re.findall(r"NAE_LIB\.([A-Za-z_]\w*)\s*=", f.read()))
    return types


def find_option(rnd, oid):
    for sec in rnd["sections"]:
        for opt in sec["options"]:
            if opt["id"] == oid:
                return sec, opt
    return None, None


def write_page(style):
    """Bring the page files up to date and write data.js from the current state."""
    need_style(style)
    os.makedirs(p(style, "page"), exist_ok=True)
    for name in PAGE_FILES:
        shutil.copy2(os.path.join(PAGE_SRC, name), p(style, "page", name))
    if not os.path.isfile(p(style, "page", "custom.js")):
        shutil.copy2(os.path.join(PAGE_SRC, "custom.js"), p(style, "page", "custom.js"))
    brand = rj(p(style, "brand.json"), {})
    data = {
        "brand": dict(brand),
        "lines": rj(p(style, "lines.json"), {}),
        "round": rj(p(style, "round.json"), {"n": 0, "sections": []}),
        "face": None,
        "visual": None,
    }
    for name in sorted(os.listdir(p(style, "assets"))) if os.path.isdir(p(style, "assets")) else []:
        if name.startswith("face.") and data["face"] is None:
            data["face"] = "../assets/" + name
        if name.startswith("visual.") and data["visual"] is None:
            data["visual"] = "../assets/" + name
    if brand.get("fontFile"):
        data["brand"]["fontFile"] = "../" + brand["fontFile"]
    problems = validate(style, data["round"])
    with open(p(style, "page", "data.js"), "w", encoding="utf-8") as f:
        f.write("window.NAE = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    for line in problems:
        print("WARNING:", line)
    return problems


def validate(style, rnd):
    problems, seen = [], set()
    types = known_types(style)
    cut = set(settings(style).get("cut", []))
    for sec in rnd.get("sections", []):
        for opt in sec.get("options", []):
            if opt["id"] in seen:
                problems.append(f"{opt['id']} is on the page twice.")
            seen.add(opt["id"])
            if opt.get("type") not in types:
                problems.append(f"{opt['id']} uses \"{opt.get('type')}\", which isn't in library.js or custom.js.")
            broken = tags_for(opt.get("params", {})) & cut
            if broken:
                problems.append(f"{opt['id']} breaks a rule they cut: {', '.join(SLOP[b][0] for b in sorted(broken))}.")
    return problems


def save_round(style, rnd):
    wj(p(style, "round.json"), rnd)
    write_page(style)
    update_style_md(style, quiet=True)


# ---------------------------------------------------------------- STYLE.md automatic blocks
def block(text, name, body):
    start, end = f"<!-- auto:{name} -->", f"<!-- /auto:{name} -->"
    if start in text and end in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: f"{start}\n{body}\n{end}", text, flags=re.S)
    return text


def update_style_md(style, quiet=False):
    path = p(style, "STYLE.md")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        text = f.read()
    brand = rj(p(style, "brand.json"), {})
    font_line = brand.get("font", "")
    if brand.get("fontFile"):
        font_line += f" (file: {brand['fontFile']})"
    elif brand.get("fontSource") == "google":
        font_line += " (Google Fonts)"
    b = [f"- Name: {brand.get('name', '')}",
         f"- Background: {brand.get('paper', '')} · Text: {brand.get('ink', '')} · Accent: {brand.get('accent', '')}",
         f"- Font: {font_line}"]
    sh = brand.get("sheet") or {}
    for c in sh.get("colors", []):
        b.append(f"- Colour: {c.get('name') or c.get('role', '')} {c['hex']}" + (f" ({c['role']})" if c.get("role") and c.get("name") else "")
                 + (f": {c['use']}" if c.get("use") else ""))
    if (sh.get("gradient") or {}).get("stops"):
        b.append(f"- Gradient: {' > '.join(sh['gradient']['stops'])}" + (f": {sh['gradient']['use']}" if sh["gradient"].get("use") else ""))
    for fo in sh.get("fonts", []):
        b.append(f"- Font ({fo.get('kind') or 'font'}): {fo.get('name') or fo.get('family')}, weight {fo.get('weight', '')}"
                 + (" italic" if fo.get("italic") else "") + (f" · {fo['role']}" if fo.get("role") else ""))
    for key, label in (("onDark", "on dark backgrounds"), ("onLight", "on light backgrounds")):
        if (sh.get("logos") or {}).get(key):
            b.append(f"- Logo {label}: `{sh['logos'][key]}`" + (" (starter logo)" if is_starter(sh["logos"][key]) else ""))
    if (sh.get("mark") or {}).get("file"):
        b.append(f"- Brand mark: `{sh['mark']['file']}`" + (f" ({sh['mark']['note']})" if sh["mark"].get("note") else ""))
    if os.path.isdir(p(style, SHEET_DIR)):
        b.append(f"- Brand sheet: `{SHEET_DIR}/{sheet_base(brand)}.png` (and .pdf). The full brand reference: use these exact "
                 "colours, fonts and logo files.")
    cut = settings(style).get("cut", [])
    c = [f"- **{SLOP[x][0]}.** {SLOP[x][1]}" for x in cut] or ["- (nothing picked yet)"]
    locked = rj(p(style, "locked.json"), {})
    lk = []
    for sec, items in locked.items():
        for it in items:
            note = f" Their note: \"{it['note']}\"." if it.get("note") else ""
            lk.append(f"- {sec} · {it['id']} · {it.get('label', '')} · `{it['type']}` "
                      f"`{json.dumps(it.get('params', {}), ensure_ascii=False)}`{note}")
    lk = lk or ["- (nothing kept yet)"]
    rej = rj(p(style, "rejected.json"), [])
    rr = [f"- {r['section']} · {r['id']} · {r.get('label', '')}" + (f": \"{r['reason']}\"" if r.get("reason") else "")
          for r in rej] or ["- (nothing dropped yet)"]
    for name, lines in (("brand", b), ("cut", c), ("locked", lk), ("rejected", rr)):
        text = block(text, name, "\n".join(lines))
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if not quiet:
        n_kept = sum(len(v) for v in locked.values())
        print(f"Updated STYLE.md ({n_kept} kept, {len(rej)} dropped, {len(cut)} slop rules).")


# ---------------------------------------------------------------- commands
def cmd_check(args):
    print("Branding Pack: checking this computer\n")
    ok = True
    py = sys.version_info
    print(f"  Python      {'found' if py >= (3, 8) else 'TOO OLD'} ({py.major}.{py.minor})   runs the helper")
    if py < (3, 8):
        ok = False
    print(f"  Chrome      {'found' if find_chrome() else 'missing'}   saves your brand sheet as a PNG and PDF (optional; "
          "without it you save the PDF from your browser)")
    for tool, why in (("ffmpeg", "trims your clip for the previews and studies reference videos (optional)"),
                      ("ffprobe", "reads clip sizes (comes with ffmpeg, optional)")):
        print(f"  {tool:<11} {'found' if shutil.which(tool) else 'missing'}   {why}")
    if not shutil.which("ffmpeg"):
        if sys.platform == "darwin":
            print("\n  ffmpeg is optional. To add it later: install Homebrew from https://brew.sh, then in Terminal run: brew install ffmpeg")
        else:
            print("\n  ffmpeg is optional. Install it from https://ffmpeg.org/download.html if you want clip previews.")
    print("\nREADY" if ok else "\nNOT READY: Python 3.8 or newer is needed.")


def cmd_init(args):
    if len(args) != 1:
        die('Usage: nae.py init "<style folder>"   (usually you want: nae.py setup ".")')
    style = os.path.abspath(args[0])
    for d in ("assets", "notes", "picks", "references", "old"):
        os.makedirs(p(style, d), exist_ok=True)
    if not os.path.isfile(p(style, "brand.json")):
        wj(p(style, "brand.json"), {"name": "Example", "paper": "#F2F2F2", "ink": "#151515", "accent": "#7A7A7A",
                                    "font": "Helvetica Neue", "fontSource": "system"})
    if not os.path.isfile(p(style, "lines.json")):
        wj(p(style, "lines.json"), {
            "captions": "This is where your captions show up while you talk to the camera",
            "title": ["Your hook line", "goes right here"], "hero": "Clean", "label": "Your name · What you do"})
    if not os.path.isfile(p(style, "settings.json")):
        save_settings(style, {"cut": [], "counter": {}, "created": today()})
    for name, default in (("locked.json", {}), ("rejected.json", [])):
        if not os.path.isfile(p(style, name)):
            wj(p(style, name), default)
    if not os.path.isfile(p(style, "STYLE.md")):
        shutil.copy2(TEMPLATE, p(style, "STYLE.md"))
    if not os.path.isfile(p(style, "notes", "their-words.md")):
        with open(p(style, "notes", "their-words.md"), "w", encoding="utf-8") as f:
            f.write("# Their words\nEverything they say they like or don't, word for word, dated.\n")
    if not os.path.isfile(p(style, "round.json")):
        cat = rj(CATALOGUE)
        sections = []
        for sec in cat["sections"]:
            if sec["name"] not in ("Captions", "Titles", "Visuals"):
                continue
            opts = []
            for o in sec["options"][:3]:
                opts.append({"id": f"EX{len(opts) + 1}{sec['name'][0]}", "type": sec["type"],
                             "params": {**sec["base"], **o["set"]}, "label": o["label"], "state": "new"})
            sections.append({"name": sec["name"], "note": sec["note"], "options": opts})
        wj(p(style, "round.json"), {"n": 0, "example": True, "changes": [], "sections": sections})
    write_page(style)
    cfg = rj(CONFIG, {})
    cfg["styleDir"] = style
    wj(CONFIG, cfg)
    print(f"Style folder ready: {style}\nPage: {p(style, 'page', 'index.html')}")


def cmd_brand(args):
    if not args:
        die("Usage: nae.py brand STYLE [--name N] [--paper #hex] [--ink #hex] [--accent #hex] [--font NAME] "
            "[--font-source google|system] [--font-file PATH] [--lines '{\"captions\": \"...\", \"title\": [..], "
            "\"hero\": \"Word\", \"label\": \"Name · Role\"}']")
    f, rest = flags(args, ["name", "paper", "ink", "accent", "font", "font-source", "font-file", "lines"])
    style = os.path.abspath(rest[0])
    need_style(style)
    brand = rj(p(style, "brand.json"), {})
    for k in ("name", "paper", "ink", "accent", "font"):
        if k in f:
            if k in ("paper", "ink", "accent"):
                hex_rgb(f[k])
                f[k] = "#" + f[k].lstrip("#").upper()
            brand[k] = f[k]
    if "font-source" in f:
        brand["fontSource"] = f["font-source"]
        brand.pop("fontFile", None)
    if "font-file" in f:
        src = os.path.expanduser(f["font-file"])
        if not os.path.isfile(src):
            die(f'No font file at "{src}".')
        os.makedirs(p(style, "assets", "fonts"), exist_ok=True)
        dst = p(style, "assets", "fonts", os.path.basename(src))
        shutil.copy2(src, dst)
        brand["fontFile"] = "assets/fonts/" + os.path.basename(src)
        brand["fontSource"] = "file"
    wj(p(style, "brand.json"), brand)
    if "lines" in f:
        lines = rj(p(style, "lines.json"), {})
        lines.update(parse_json_arg(f["lines"], "lines"))
        wj(p(style, "lines.json"), lines)
    write_page(style)
    update_style_md(style, quiet=True)
    print(f"Brand saved: {brand.get('name')} · background {brand.get('paper')} · text {brand.get('ink')} · "
          f"accent {brand.get('accent')} · font {brand.get('font')}")
    try:
        c1 = contrast(brand["ink"], brand["paper"])
        c2 = contrast("#FFFFFF", brand["accent"])
        c3 = contrast(brand["paper"], brand["accent"])
        print(f"Contrast: text on background {c1:.1f}:1 · white on accent {c2:.1f}:1 · background colour on accent {c3:.1f}:1 "
              "(4.5 or more reads easily; under 3 is hard to read on a phone)")
    except KeyError:
        pass


def cmd_face(args):
    f, rest = flags(args, ["start", "seconds"])
    if len(rest) != 2:
        die('Usage: nae.py face STYLE "<clip>" [--start 2] [--seconds 8]')
    style, clip = os.path.abspath(rest[0]), os.path.expanduser(rest[1])
    need_style(style)
    if not os.path.isfile(clip):
        die(f'No clip at "{clip}".')
    for old in os.listdir(p(style, "assets")):
        if old.startswith("face."):
            os.replace(p(style, "assets", old), p(style, "old", f"{today()}-{old}"))
    if shutil.which("ffmpeg"):
        out = p(style, "assets", "face.mp4")
        vf = "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=540:960"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(f.get("start", 0)), "-t", str(f.get("seconds", 8)),
               "-i", clip, "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            die("ffmpeg couldn't read that clip:\n" + r.stderr[-800:])
        print(f"Face clip ready (cropped to 9:16, {f.get('seconds', 8)} s, silent): {out}")
    else:
        ext = os.path.splitext(clip)[1].lower() or ".mp4"
        out = p(style, "assets", "face" + ext)
        shutil.copy2(clip, out)
        print(f"Copied the clip as-is (no ffmpeg to trim it): {out}. If it doesn't play on the page, "
              "an .mp4 from a phone works best.")
    write_page(style)


def cmd_visual(args):
    if len(args) != 2:
        die('Usage: nae.py visual STYLE "<screenshot or photo>"')
    style, img = os.path.abspath(args[0]), os.path.expanduser(args[1])
    need_style(style)
    if not os.path.isfile(img):
        die(f'No image at "{img}".')
    for old in os.listdir(p(style, "assets")):
        if old.startswith("visual."):
            os.replace(p(style, "assets", old), p(style, "old", f"{today()}-{old}"))
    out = p(style, "assets", "visual" + (os.path.splitext(img)[1].lower() or ".png"))
    shutil.copy2(img, out)
    write_page(style)
    print(f"Visual ready: {out}")


def cmd_frames(args):
    f, rest = flags(args, ["every"])
    if len(rest) != 2:
        die('Usage: nae.py frames STYLE "<reference video>" [--every 0.5]')
    if not shutil.which("ffmpeg"):
        die("This needs ffmpeg. Without it, ask them to describe what they love about the video in words.")
    style, video = os.path.abspath(rest[0]), os.path.expanduser(rest[1])
    need_style(style)
    if not os.path.isfile(video):
        die(f'No video at "{video}".')
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", os.path.splitext(os.path.basename(video))[0]).strip("-")[:40] or "reference"
    out = p(style, "references", stem)
    os.makedirs(out, exist_ok=True)
    every = float(f.get("every", 0.5))
    sheet = os.path.join(out, "sheet.jpg")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf",
                        f"fps=1/{every},scale=216:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.6,tile=6x6",
                        "-frames:v", "1", sheet], capture_output=True, text=True)
    if r.returncode != 0:  # drawtext needs a font on some systems: try without the timestamps
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf",
                            f"fps=1/{every},scale=216:-2,tile=6x6", "-frames:v", "1", sheet], capture_output=True, text=True)
    if r.returncode != 0:
        die("ffmpeg couldn't read that video:\n" + r.stderr[-800:])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf", "fps=1,scale=540:-2",
                    "-frames:v", "12", os.path.join(out, "still-%02d.jpg")], capture_output=True)
    print(f"Contact sheet (one frame every {every} s, first 18 s): {sheet}\nStills (one a second): {out}/still-*.jpg")


def cmd_cut(args):
    if len(args) < 2:
        die("Usage: nae.py cut STYLE " + " ".join(SLOP) + "   (or: none)\n" +
            "\n".join(f"  {k:<12} {v[0]}" for k, v in SLOP.items()))
    style = os.path.abspath(args[0])
    need_style(style)
    ids = [] if args[1:] == ["none"] else args[1:]
    bad = [x for x in ids if x not in SLOP]
    if bad:
        die(f"Unknown: {', '.join(bad)}. Pick from: {', '.join(SLOP)}")
    s = settings(style)
    s["cut"] = list(dict.fromkeys(ids))
    save_settings(style, s)
    write_page(style)
    update_style_md(style, quiet=True)
    print("Cutting: " + (", ".join(SLOP[x][0] for x in s["cut"]) or "nothing"))


def cmd_round(args):
    if len(args) < 2:
        die(__doc__)
    style, sub, rest = os.path.abspath(args[0]), args[1], args[2:]
    need_style(style)
    rnd = rj(p(style, "round.json"), {"n": 0, "sections": []})
    cut_list = settings(style).get("cut", [])
    cut = set(cut_list)
    f, rest = flags(rest, ["sections!", "force!", "reason"])

    if sub == "first":
        cat = rj(CATALOGUE)
        names = [s["name"] for s in cat["sections"]]
        wanted = [x for x in rest] if f.get("sections") else []
        if not wanted:
            print("Sections you can start from: " + ", ".join(names) +
                  '\nUsage: nae.py round STYLE first --sections "Captions" "Titles"')
            return
        if rnd.get("n", 0) >= 1 and not f.get("force"):
            die("There's already a real round. Use add/set/remove to change it, or --force to start over "
                "(the old round is saved in old/).")
        if os.path.isfile(p(style, "round.json")):
            shutil.copy2(p(style, "round.json"), p(style, "old", f"round-{rnd.get('n', 0)}-{today()}.json"))
        sections, skipped = [], []
        for name in wanted:
            sec = next((s for s in cat["sections"] if s["name"].lower() == name.lower()), None)
            if not sec:
                die(f'No section called "{name}". Pick from: {", ".join(names)} (or add your own later with add).')
            opts = []
            for o in sec["options"]:
                params = {**sec["base"], **o["set"]}
                if tags_for(params) & cut:
                    skipped.append(f"{sec['name']}: {o['label']}")
                    continue
                opts.append({"id": new_id(style, sec["name"]), "type": sec["type"], "params": params,
                             "label": o["label"], "state": "new"})
            sections.append({"name": sec["name"], "note": sec["note"], "options": opts})
        rnd = {"n": 1, "example": False, "changes": [], "sections": sections}
        save_round(style, rnd)
        print(f"Round 1 built: {sum(len(s['options']) for s in sections)} options in {len(sections)} sections.")
        if skipped:
            print("Left out because they break a slop rule: " + "; ".join(skipped))
        cmd_round([style, "show"])
        return

    if sub == "add":
        if len(rest) != 4:
            die('Usage: nae.py round STYLE add "<Section>" TYPE \'{"param": 1}\' "<label>" [--force]')
        name, typ, params, label = rest[0], rest[1], parse_json_arg(rest[2]), rest[3]
        if typ not in known_types(style):
            die(f'"{typ}" isn\'t an option type yet. Built in: {", ".join(sorted(BUILT_IN_TYPES))}. '
                "Write new ones in page/custom.js first.")
        sec = next((s for s in rnd["sections"] if s["name"].lower() == name.lower()), None)
        if not sec:
            cat = rj(CATALOGUE)
            base = next((s for s in cat["sections"] if s["type"] == typ), None)
            sec = {"name": name, "note": base["note"] if base and base["name"] == name else "", "options": []}
            rnd["sections"].append(sec)
            params = {**(base["base"] if base else {}), **params}
        else:
            same = next((o for o in sec["options"] if o["type"] == typ), None)
            if same:
                params = {**same["params"], **params}
        broken = tags_for(params) & cut
        if broken and not f.get("force"):
            die(f"That breaks a rule they cut ({', '.join(SLOP[b][0] for b in broken)}). Not added.")
        oid = new_id(style, sec["name"])
        sec["options"].append({"id": oid, "type": typ, "params": params, "label": label, "state": "new"})
        save_round(style, rnd)
        print(f"Added {oid} to {sec['name']}: {label}")
        return

    if sub == "set":
        if len(rest) not in (2, 3):
            die('Usage: nae.py round STYLE set ID \'{"param": 1}\' ["<new label>"] [--force]')
        sec, opt = find_option(rnd, rest[0])
        if not opt:
            die(f"No option {rest[0]} on this round.")
        params = {**opt["params"], **parse_json_arg(rest[1])}
        broken = tags_for(params) & cut
        if broken and not f.get("force"):
            die(f"That breaks a rule they cut ({', '.join(SLOP[b][0] for b in broken)}). Not changed.")
        before = opt["params"]
        opt["params"] = params
        if len(rest) == 3:
            opt["label"] = rest[2]
        save_round(style, rnd)
        changed = {k: (before.get(k), v) for k, v in params.items() if before.get(k) != v}
        print(f"{opt['id']} updated: " + (", ".join(f"{k} {a} -> {b}" for k, (a, b) in changed.items()) or "no change"))
        return

    if sub == "remove":
        if not rest:
            die('Usage: nae.py round STYLE remove ID ... [--reason "..."]')
        rejected = rj(p(style, "rejected.json"), [])
        for oid in rest:
            sec, opt = find_option(rnd, oid)
            if not opt:
                print(f"No option {oid}; skipped.")
                continue
            sec["options"].remove(opt)
            rejected.append({"id": oid, "section": sec["name"], "label": opt.get("label", ""),
                             "type": opt["type"], "params": opt["params"], "reason": f.get("reason", ""),
                             "round": rnd.get("n", 0), "date": today()})
            drop_locked(style, oid)
            print(f"Removed {oid} ({opt.get('label', '')}).")
        wj(p(style, "rejected.json"), rejected)
        save_round(style, rnd)
        return

    if sub == "keep-only":
        if len(rest) < 2:
            die('Usage: nae.py round STYLE keep-only "<Section>" ID ...')
        name, keep = rest[0], set(rest[1:])
        sec = next((s for s in rnd["sections"] if s["name"].lower() == name.lower()), None)
        if not sec:
            die(f'No section "{name}" on this round.')
        missing = keep - {o["id"] for o in sec["options"]}
        if missing:
            die(f"Not in {sec['name']}: {', '.join(sorted(missing))}")
        rejected = rj(p(style, "rejected.json"), [])
        for opt in list(sec["options"]):
            if opt["id"] in keep:
                opt["state"] = "kept"
                lock(style, sec["name"], opt)
            else:
                sec["options"].remove(opt)
                rejected.append({"id": opt["id"], "section": sec["name"], "label": opt.get("label", ""),
                                 "type": opt["type"], "params": opt["params"],
                                 "reason": f"kept {', '.join(sorted(keep))} instead", "round": rnd.get("n", 0),
                                 "date": today()})
                drop_locked(style, opt["id"])
        wj(p(style, "rejected.json"), rejected)
        save_round(style, rnd)
        print(f"{sec['name']} is now just {', '.join(sorted(keep))}, kept.")
        return

    if sub == "note":
        if len(rest) != 2:
            die('Usage: nae.py round STYLE note "<Section>" "<what this section is for>"')
        sec = next((s for s in rnd["sections"] if s["name"].lower() == rest[0].lower()), None)
        if not sec:
            die(f'No section "{rest[0]}" on this round.')
        sec["note"] = rest[1]
        save_round(style, rnd)
        print(f"Note set for {sec['name']}.")
        return

    if sub == "changes":
        rnd["changes"] = rest
        save_round(style, rnd)
        print(f"{len(rest)} change line(s) set for round {rnd.get('n')}.")
        return

    if sub == "show":
        label = "Example round" if rnd.get("example") else f"Round {rnd.get('n', 0)}"
        print(f"{label}: " + (f"cutting {', '.join(SLOP[c][0] for c in cut_list)}" if cut_list else "no slop rules yet"))
        for sec in rnd["sections"]:
            print(f"\n  {sec['name']}" + (f"  ({sec['note']})" if sec.get("note") else ""))
            for o in sec["options"]:
                state = {"kept": "KEPT ", "maybe": "MAYBE"}.get(o.get("state"), "     ")
                fix = f'   note: "{o["fix"]}"' if o.get("fix") else ""
                print(f"    {state} {o['id']:<6} {o.get('label', '')}{fix}")
        problems = validate(style, rnd)
        for line in problems:
            print("WARNING:", line)
        print(f"\nPage: {p(style, 'page', 'index.html')}")
        return

    die(f'Unknown round command "{sub}".\n' + __doc__)


def lock(style, section, opt, note=None):
    locked = rj(p(style, "locked.json"), {})
    items = [x for x in locked.get(section, []) if x["id"] != opt["id"]]
    items.append({"id": opt["id"], "type": opt["type"], "params": opt["params"], "label": opt.get("label", ""),
                  "note": note or opt.get("fix") or "", "date": today()})
    locked[section] = items
    wj(p(style, "locked.json"), locked)


def drop_locked(style, oid):
    locked = rj(p(style, "locked.json"), {})
    changed = False
    for sec in list(locked):
        before = len(locked[sec])
        locked[sec] = [x for x in locked[sec] if x["id"] != oid]
        changed |= len(locked[sec]) != before
        if not locked[sec]:
            del locked[sec]
    if changed:
        wj(p(style, "locked.json"), locked)


def cmd_picks(args):
    if len(args) != 2:
        die('Usage: nae.py picks STYLE "<file with their pasted picks>"')
    style, src = os.path.abspath(args[0]), os.path.expanduser(args[1])
    need_style(style)
    with open(src, encoding="utf-8") as f:
        text = f.read()
    rnd = rj(p(style, "round.json"))
    n = rnd.get("n", 0)
    m = re.search(r"round\s+(\d+)", text, re.I)
    if m and int(m.group(1)) != n:
        print(f"WARNING: these picks say round {m.group(1)} but the page is on round {n}. "
              "Check with them before acting on old picks.")
    with open(p(style, "picks", f"round-{n}.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    kept, maybe, dropped, notes, unknown, overall = [], [], [], [], [], ""
    rejected = rj(p(style, "rejected.json"), [])
    for raw in text.splitlines():
        line = raw.strip().lstrip("-• ").strip()
        if not line or line.lower().startswith("not another edit"):
            continue
        if line.lower().startswith("overall:"):
            overall = line.split(":", 1)[1].strip()
            continue
        mm = re.match(r"^([A-Za-z]{1,4}\d+[A-Za-z]?)\s+(keep|maybe|drop|note)\b\s*:?\s*(.*)$", line, re.I)
        if not mm:
            unknown.append(line)
            continue
        oid, verdict, note = mm.group(1).upper(), mm.group(2).lower(), mm.group(3).strip()
        sec, opt = find_option(rnd, oid)
        if not opt:
            unknown.append(line)
            continue
        if verdict == "keep":
            opt["state"] = "kept"
            opt["fix"] = note
            lock(style, sec["name"], opt, note)
            kept.append((oid, opt.get("label", ""), note))
        elif verdict == "maybe":
            opt["state"] = "maybe"
            opt["fix"] = note
            maybe.append((oid, opt.get("label", ""), note))
        elif verdict == "drop":
            sec["options"].remove(opt)
            drop_locked(style, oid)
            rejected.append({"id": oid, "section": sec["name"], "label": opt.get("label", ""), "type": opt["type"],
                             "params": opt["params"], "reason": note, "round": n, "date": today()})
            dropped.append((oid, opt.get("label", ""), note))
        else:
            opt["fix"] = note
            notes.append((oid, opt.get("label", ""), note))
    wj(p(style, "rejected.json"), rejected)
    words = [f"\n## Round {n} picks ({today()})"]
    for group, items in (("kept", kept), ("maybe", maybe), ("dropped", dropped), ("note", notes)):
        for oid, label, note in items:
            if note:
                words.append(f"- {oid} ({label}), {group}: \"{note}\"")
    if overall:
        words.append(f"- Overall: \"{overall}\"")
    if len(words) > 1:
        with open(p(style, "notes", "their-words.md"), "a", encoding="utf-8") as f:
            f.write("\n".join(words) + "\n")
    rnd["n"] = n + 1
    rnd["example"] = False
    rnd["changes"] = []
    save_round(style, rnd)

    def show(title, items):
        if items:
            print(f"{title}:")
            for oid, label, note in items:
                print(f"  {oid} {label}" + (f'  ->  "{note}"' if note else ""))
    show("Kept", kept)
    show("Maybe (fix exactly as the note says)", maybe)
    show("Dropped", dropped)
    show("Notes on options they didn't rate", notes)
    if overall:
        print(f'Overall: "{overall}"')
    if unknown:
        print("Couldn't match these lines (read them yourself): " + " | ".join(unknown))
    still = [o["id"] for s in rnd["sections"] for o in s["options"] if o.get("state") == "new" and not o.get("fix")]
    if still:
        print("Not rated yet (still on the page): " + ", ".join(still))
    print(f"\nNow on round {n + 1}. Fix the maybes, add new variations of the keeps, set the change lines, then open the page.")


def cmd_style_md(args):
    f, rest = flags(args, ["check!"])
    if len(rest) != 1:
        die('Usage: nae.py style-md STYLE [--check]')
    style = os.path.abspath(rest[0])
    need_style(style)
    update_style_md(style)
    if f.get("check"):
        with open(p(style, "STYLE.md"), encoding="utf-8") as fh:
            text = fh.read()
        rnd = rj(p(style, "round.json"), {"sections": []})
        open_items = []
        if "(their words go here)" in text:
            open_items.append("The brief isn't written yet.")
        for sec in rnd["sections"]:
            states = [o.get("state") for o in sec["options"]]
            if "maybe" in states:
                open_items.append(f"{sec['name']}: maybes still open.")
            elif "new" in states:
                open_items.append(f"{sec['name']}: options not rated yet.")
            elif states and f"### {sec['name']}" not in text:
                open_items.append(f"{sec['name']}: all kept, but not written up as rules under Locked yet.")
        if not settings(style).get("cut"):
            open_items.append("No slop rules picked yet (ask the slop menu question).")
        print("Open:\n  " + "\n  ".join(open_items) if open_items else "Nothing important is open.")


# ---------------------------------------------------------------- brand sheet
SHEET_DIR = "Brand Sheet"
SHEET_TPL = os.path.join(SK, "templates", "sheet")
FONT_KINDS = ("headline", "body", "accent")


def norm_hex(h):
    r, g, b = hex_rgb(h)
    return "#" + "".join(f"{round(v * 255):02X}" for v in (r, g, b))


def rgb_text(h):
    return ", ".join(str(round(v * 255)) for v in hex_rgb(h))


def cmyk_text(h):
    r, g, b = hex_rgb(h)
    k = 1 - max(r, g, b)
    if k >= 1:
        return "0, 0, 0, 100"
    c, m, y = [(1 - v - k) / (1 - k) for v in (r, g, b)]
    return ", ".join(str(round(x * 100)) for x in (c, m, y, k))


def lum(h):
    r, g, b = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in hex_rgb(h)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def find_chrome():
    cands = []
    if sys.platform == "darwin":
        for app in ("Google Chrome", "Chromium", "Microsoft Edge", "Brave Browser"):
            for base in ("/Applications", os.path.expanduser("~/Applications")):
                cands.append(f"{base}/{app}.app/Contents/MacOS/{app}")
    elif os.name == "nt":
        for base in (os.environ.get("PROGRAMFILES", r"C:\Program Files"),
                     os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), os.environ.get("LOCALAPPDATA", "")):
            cands += [os.path.join(base, r"Google\Chrome\Application\chrome.exe"),
                      os.path.join(base, r"Microsoft\Edge\Application\msedge.exe")]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"):
        if shutil.which(n):
            return shutil.which(n)
    return None


def bring_in(style, src, sub, stem):
    """Copy a logo, mark or font file into STYLE/assets/<sub>/ and return its path relative to STYLE."""
    if not src:
        return None
    full = src if os.path.isabs(src) else p(style, src)
    full = os.path.expanduser(full)
    if not os.path.isfile(full):
        full = os.path.abspath(os.path.expanduser(src))
    if not os.path.isfile(full):
        die(f'No file at "{src}".')
    rel_dir = p(style, "assets", sub)
    if os.path.commonpath([os.path.abspath(full), rel_dir]) == rel_dir:
        return os.path.relpath(full, style).replace(os.sep, "/")
    os.makedirs(rel_dir, exist_ok=True)
    name = (stem + os.path.splitext(full)[1].lower()) if stem else os.path.basename(full)
    shutil.copy2(full, p(rel_dir, name))
    return f"assets/{sub}/{name}"


def split_title(name):
    words = name.split()
    return [" ".join(words[:-1]), words[-1]] if len(words) >= 2 else [name]


def sheet_base(brand):
    name = (brand.get("sheet", {}).get("name") or (brand.get("name") if brand.get("name") != "Example" else "") or "Brand").strip()
    safe = re.sub(r'[\\/:*?"<>|]+', "", name).strip() or "Brand"
    return f"{safe} Brand Sheet"


def sheet_data(style, brand):
    sh = brand.get("sheet", {})
    name = sh.get("name") or (brand.get("name") if brand.get("name") not in (None, "", "Example") else None) or "Your brand"
    colors = []
    for c in sh.get("colors", []):
        hx = norm_hex(c["hex"])
        colors.append({"role": c.get("role", ""), "name": c.get("name", ""), "hex": hx,
                       "rgb": rgb_text(hx), "cmyk": cmyk_text(hx), "use": c.get("use", "")})
    if not colors:
        for role, key, nm in (("Accent", "accent", "Accent"), ("Text", "ink", "Ink"), ("Background", "paper", "Paper")):
            if brand.get(key):
                hx = norm_hex(brand[key])
                colors.append({"role": role, "name": nm, "hex": hx, "rgb": rgb_text(hx), "cmyk": cmyk_text(hx), "use": ""})
    hexes = [c["hex"] for c in colors] or ["#111111", "#FFFFFF"]
    primary = sh.get("primary") or next((c["hex"] for c in colors if "primary" in c["role"].lower()), None) \
        or (norm_hex(brand["accent"]) if brand.get("accent") else hexes[0])
    dark = norm_hex(sh["dark"]) if sh.get("dark") else min(hexes, key=lum)
    light = norm_hex(sh["light"]) if sh.get("light") else max(hexes, key=lum)
    if contrast(dark, light) < 4.5:
        dark, light = ("#111111" if lum(dark) < 0.5 else dark), ("#FFFFFF" if lum(light) >= 0.2 else "#F5F5F5")
    fonts = []
    for i, f in enumerate(sh.get("fonts", [])):
        kind = f.get("kind") or FONT_KINDS[min(i, 2)]
        src = f.get("source") or ("file" if f.get("file") else "google" if brand.get("fontSource") == "google" else "system")
        item = {"name": f.get("name") or f.get("family"), "family": f.get("family") or f.get("name"),
                "weight": int(f.get("weight", 900 if kind == "headline" else 400)), "italic": bool(f.get("italic", kind == "accent")),
                "role": f.get("role", ""), "kind": kind, "source": src, "sample": f.get("sample"), "size": f.get("size")}
        if src == "file" and f.get("file"):
            item["file"] = "../" + f["file"]
        fonts.append(item)
    if not fonts:
        fam = brand.get("font") or "Helvetica Neue"
        src = brand.get("fontSource", "system")
        extra = {"source": src}
        if src == "file" and brand.get("fontFile"):
            extra["file"] = "../" + brand["fontFile"]
        fonts = [{"name": fam, "family": fam, "weight": 900, "italic": False, "role": "Headlines", "kind": "headline",
                  "sample": ["Say it", "bigger."], **extra},
                 {"name": fam, "family": fam, "weight": 400, "italic": False, "role": "Body and captions", "kind": "body",
                  "sample": "**Clear and direct.** Used for body copy, labels, captions and everything in between.", **extra}]
    logos = {k: "../" + v for k, v in (sh.get("logos") or {}).items() if v}
    mark = dict(sh.get("mark") or {})
    if mark.get("file"):
        mark["file"] = "../" + mark["file"]
    d = datetime.date.today()
    return {
        "name": name, "title": sh.get("title") or split_title(name), "titleSize": sh.get("titleSize"),
        "eyebrow": sh.get("eyebrow", "Brand proof sheet"),
        "subtitle": sh.get("subtitle", "Colors, type and logo. The official brand reference."),
        "tagline": sh.get("tagline", ""), "date": sh.get("date") or f"{d:%B} {d.day}, {d.year}",
        "website": sh.get("website", ""), "est": sh.get("est", ""),
        "headings": {"colors": ["Brand", "colors"], "fonts": ["Fonts", "in use"], "logo": ["Logo"], **(sh.get("headings") or {})},
        "note": sh.get("note", "CMYK values are standard conversions from RGB for reference. Ask your printer for a proof "
                               "when exact print color matters."),
        "primary": norm_hex(primary), "dark": dark, "light": light, "ink": dark,
        "colors": colors, "gradient": ({**sh["gradient"], "stops": [norm_hex(s) for s in sh["gradient"]["stops"]]}
                                       if (sh.get("gradient") or {}).get("stops") else None),
        "fonts": fonts, "logos": logos, "mark": mark or None,
    }


def render_sheet(out_dir, base):
    chrome = find_chrome()
    if not chrome:
        return None, None, "no Chrome"
    import pathlib
    import tempfile
    url = pathlib.Path(p(out_dir, "sheet.html")).as_uri()
    png, pdf = p(out_dir, base + ".png"), p(out_dir, base + ".pdf")
    tmp = tempfile.mkdtemp(prefix="branding-pack-")
    common = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
              "--disable-extensions", "--allow-file-access-from-files", f"--user-data-dir={tmp}", "--virtual-time-budget=10000", "--run-all-compositor-stages-before-draw"]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        common.append("--no-sandbox")
    err = ""
    try:
        r = subprocess.run(common + ["--window-size=1275,1650", "--force-device-scale-factor=2", f"--screenshot={png}", url],
                           capture_output=True, text=True, timeout=180)
        err += r.stderr[-400:] if r.returncode else ""
        r = subprocess.run(common + ["--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={pdf}", url],
                           capture_output=True, text=True, timeout=180)
        err += r.stderr[-400:] if r.returncode else ""
    except subprocess.TimeoutExpired:
        err += "Chrome took too long."
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return (png if os.path.isfile(png) else None), (pdf if os.path.isfile(pdf) else None), err


def cmd_sheet(args):
    f, rest = flags(args, ["data", "logo-dark", "logo-light", "mark", "no-render!"])
    if len(rest) != 1:
        die('Usage: nae.py sheet STYLE [--data "<sheet.json>"] [--logo-dark FILE] [--logo-light FILE] [--mark FILE] [--no-render]\n'
            "  (what goes in sheet.json: references/brand-sheet.md)")
    style = os.path.abspath(rest[0])
    need_style(style)
    brand = rj(p(style, "brand.json"), {})
    sh = brand.get("sheet", {})
    if "data" in f:
        new = rj(os.path.expanduser(f["data"]))
        if not isinstance(new, dict):
            die(f'"{f["data"]}" isn\'t a JSON object. See references/brand-sheet.md.')
        sh.update(new)
    logos = dict(sh.get("logos") or {})
    for key, stem, flag in (("onDark", "logo-on-dark", "logo-dark"), ("onLight", "logo-on-light", "logo-light")):
        src = f.get(flag) or logos.get(key)
        if src:
            logos[key] = bring_in(style, src, "logos", stem)
    sh["logos"] = logos
    mark = dict(sh.get("mark") or {})
    if f.get("mark") or mark.get("file"):
        mark["file"] = bring_in(style, f.get("mark") or mark["file"], "logos", "mark")
        sh["mark"] = mark
    for c in sh.get("colors", []):
        if "hex" not in c:
            die(f"Every colour needs a hex code (problem: {c}).")
        c["hex"] = norm_hex(c["hex"])
    for g in (sh.get("gradient") or {}).get("stops", []):
        norm_hex(g)
    for fo in sh.get("fonts", []):
        if fo.get("file"):
            fo["file"] = bring_in(style, fo["file"], "fonts", None)
        if fo.get("kind") and fo["kind"] not in FONT_KINDS:
            die(f'Font kind must be one of {", ".join(FONT_KINDS)} (got "{fo["kind"]}").')
    brand["sheet"] = sh
    # the style page uses the same brand: fill it in while it still has the placeholder
    data = sheet_data(style, brand)
    if brand.get("name", "Example") == "Example":
        brand["name"] = data["name"]
        brand["accent"], brand["ink"], brand["paper"] = data["primary"], data["dark"], data["light"]
        body = next((x for x in data["fonts"] if x["kind"] == "body"), data["fonts"][0])
        brand["font"] = body["family"]
        brand["fontSource"] = body["source"] if body["source"] != "file" else "file"
        if body["source"] == "file":
            brand["fontFile"] = body["file"][3:]
        write_page(style)
    wj(p(style, "brand.json"), brand)
    out = p(style, SHEET_DIR)
    os.makedirs(out, exist_ok=True)
    for name in ("sheet.html", "sheet.css", "sheet.js"):
        shutil.copy2(p(SHEET_TPL, name), p(out, name))
    with open(p(out, "data.js"), "w", encoding="utf-8") as fh:
        fh.write("window.BRAND_SHEET = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    base = sheet_base(brand)
    warnings = []
    n_cards = len(data["colors"]) + (1 if data["gradient"] else 0)
    if n_cards > 8:
        warnings.append(f"{n_cards} colour cards: the sheet fits 8. Drop or merge some.")
    if len(data["fonts"]) > 3:
        warnings.append(f"{len(data['fonts'])} fonts: the sheet fits 3.")
    if not data["logos"]:
        warnings.append("No logo files yet, so the logo tiles show the name as a wordmark.")
    if not sh.get("colors"):
        warnings.append("No named colours yet: the sheet is using the style page's three colours.")
    if not f.get("no-render"):
        stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        for old in os.listdir(out):
            if old.lower().endswith((".png", ".pdf")):
                os.makedirs(p(style, "old"), exist_ok=True)
                shutil.move(p(out, old), p(style, "old", f"{stamp} {old}"))
        png, pdf, err = render_sheet(out, base)
    else:
        png = pdf = None
        err = "skipped"
    update_style_md(style, quiet=True)
    print(f"Brand sheet: {out}")
    if png or pdf:
        print(f"  PNG: {png or 'not made'}\n  PDF: {pdf or 'not made'}")
    elif err == "no Chrome":
        print("  Chrome (or Edge or Brave) isn't installed, so I couldn't save the PNG and PDF. Open sheet.html and use "
              "File > Print > Save as PDF (turn on Background graphics).")
    elif err != "skipped":
        print(f"  Couldn't save the PNG and PDF: {err.strip()[-300:]}")
    print(f"  Page: {p(out, 'sheet.html')}")
    for w in warnings:
        print("  NOTE: " + w)


# ---------------------------------------------------------------- starter logo
LOGO_TPL = os.path.join(SK, "templates", "logo")
STARTER = {"onDark": "starter-logo-on-dark.png", "onLight": "starter-logo-on-light.png", "mark": "starter-mark.png"}
FONT_MIME = {"otf": "font/otf", "ttf": "font/ttf", "woff": "font/woff", "woff2": "font/woff2"}


def initials(name):
    words = [w for w in name.split() if re.search(r"[A-Za-z0-9]", w)]
    return "".join(re.search(r"[A-Za-z0-9]", w).group(0).upper() for w in words[:3]) or "B"


def is_starter(rel):
    return bool(rel) and os.path.basename(rel).startswith("starter-")


def cmd_logo(args):
    import base64
    import html
    import pathlib
    import tempfile
    f, rest = flags(args, ["text", "lines", "accent", "font", "weight", "source", "file", "tracking", "mark-text",
                           "upper!", "italic!", "no-mark!", "replace!"])
    if len(rest) != 1:
        die('Usage: nae.py logo STYLE [--text "Name"] [--lines 1|2] [--accent last|none|all] [--upper]\n'
            "         [--font FAMILY --weight 800 --source google|system|file --file F] [--tracking -0.02]\n"
            '         [--mark-text "AB"] [--no-mark] [--replace]\n'
            "  A starter logo: their name in their brand font and colours (PNG, clear background) for dark and light\n"
            "  backgrounds, plus their initials on a square of their main colour. Then run sheet to show it.")
    style = os.path.abspath(rest[0])
    need_style(style)
    brand = rj(p(style, "brand.json"), {})
    sh = brand.get("sheet", {})
    data = sheet_data(style, brand)
    text = (f.get("text") or ("" if data["name"] == "Your brand" else data["name"])).strip()
    if not text:
        die('What name goes on the logo? Pass --text "Their Name" (or make the brand sheet first).')
    if f.get("upper"):
        text = text.upper()
    # their headline font, unless told otherwise
    head = next((x for x in data["fonts"] if x["kind"] == "headline"), data["fonts"][0])
    own = bool(f.get("font"))
    font = {"family": f.get("font") or head["family"],
            "weight": int(f.get("weight") or (800 if own else head["weight"])),
            "italic": bool(f.get("italic")) or (False if own else bool(head.get("italic"))),
            "source": f.get("source") or (("file" if f.get("file") else "google") if own else head["source"])}
    if font["source"] not in ("google", "system", "file"):
        die("--source is google, system or file.")
    if font["source"] == "file":
        ffile = p(style, bring_in(style, f["file"], "fonts", None)) if f.get("file") else \
            (p(style, head["file"][3:]) if not own and head.get("file") else None)
        if not ffile:
            die("With --source file, pass the font file: --file FILE.")
        with open(ffile, "rb") as fh:
            mime = FONT_MIME.get(os.path.splitext(ffile)[1].lower().lstrip("."), "application/octet-stream")
            font["data"] = f"data:{mime};base64," + base64.b64encode(fh.read()).decode()
    upper = text.upper() == text and any(ch.isalpha() for ch in text)
    tracking = float(f["tracking"]) if f.get("tracking") is not None else (0.04 if upper else -0.02)
    words = text.split()
    nlines = int(f.get("lines") or 1)
    if nlines not in (1, 2):
        die("--lines is 1 or 2.")
    acc = f.get("accent") or ("last" if len(words) >= 2 else "none")
    if acc not in ("last", "none", "all"):
        die("--accent is last, none or all.")
    groups = [words[:-1], words[-1:]] if nlines == 2 and len(words) >= 2 else [words]
    lines, i = [], 0
    for g in groups:
        lines.append([{"t": w, "accent": acc == "all" or (acc == "last" and i + j == len(words) - 1)} for j, w in enumerate(g)])
        i += len(g)
    primary, dark, light = data["primary"], data["dark"], data["light"]
    on_dark_text = light if contrast(light, dark) >= 4.5 else "#FFFFFF"
    # logos are big: the accent colour only has to stand out, not pass body-text contrast
    on_dark = {"text": on_dark_text, "accent": primary if contrast(primary, dark) >= 2 else on_dark_text}
    on_light = {"text": dark, "accent": primary if contrast(primary, light) >= 2 else dark}
    mark = None if f.get("no-mark") else {"text": (f.get("mark-text") or initials(text)).strip(), "bg": primary,
                                          "fg": "#FFFFFF" if contrast("#FFFFFF", primary) >= 3 else dark}
    chrome = find_chrome()
    if not chrome:
        die("The starter logo needs Google Chrome (or Edge or Brave). Install Chrome, then run this again.")
    tmp = tempfile.mkdtemp(prefix="branding-pack-logo-")
    try:
        for n in ("logo.html", "logo.js"):
            shutil.copy2(p(LOGO_TPL, n), p(tmp, n))
        payload = {"text": text, "lines": lines, "font": font, "tracking": tracking, "leading": 0.95 if upper else 1.08, "size": 360,
                   "onDark": on_dark, "onLight": on_light, "mark": mark}
        with open(p(tmp, "data.js"), "w", encoding="utf-8") as fh:
            fh.write("window.LOGO = " + json.dumps(payload, ensure_ascii=False) + ";\n")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               f"--user-data-dir={p(tmp, 'profile')}", "--virtual-time-budget=15000", "--dump-dom",
               pathlib.Path(p(tmp, "logo.html")).as_uri()]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.insert(1, "--no-sandbox")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            die("Chrome took too long to draw the logo. Try again.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    mo = re.search(r"LOGO-RESULT (.*?) LOGO-END", r.stdout, re.S)
    if not mo:
        die("Couldn't draw the logo: " + (r.stderr.strip()[-300:] or "Chrome gave no result."))
    res = json.loads(html.unescape(mo.group(1)))
    if not res.get("ok"):
        die("Couldn't draw the logo: " + res.get("error", "unknown error"))
    ldir = p(style, "assets", "logos")
    os.makedirs(ldir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    saved = {}
    for key, name in STARTER.items():
        if not res.get(key):
            continue
        dest = p(ldir, name)
        if os.path.isfile(dest):
            os.makedirs(p(style, "old"), exist_ok=True)
            shutil.move(dest, p(style, "old", f"{stamp} {name}"))
        with open(dest, "wb") as fh:
            fh.write(base64.b64decode(res[key].split(",", 1)[1]))
        saved[key] = f"assets/logos/{name}"
    # use it on the sheet, unless they already gave their own logo
    logos, kept = dict(sh.get("logos") or {}), []
    for key in ("onDark", "onLight"):
        if key in saved:
            if logos.get(key) and not is_starter(logos[key]) and not f.get("replace"):
                kept.append(key)
            else:
                logos[key] = saved[key]
    sh["logos"] = logos
    if "mark" in saved:
        mk = dict(sh.get("mark") or {})
        if mk.get("file") and not is_starter(mk["file"]) and not f.get("replace"):
            kept.append("mark")
        else:
            mk["file"] = saved["mark"]
            mk.setdefault("note", "Starter mark: your initials on your main colour.")
            sh["mark"] = mk
    sh["starterLogo"] = {"text": text, "font": font["family"], "weight": font["weight"], "lines": nlines,
                         "accent": acc, "mark": mark["text"] if mark else None}
    brand["sheet"] = sh
    wj(p(style, "brand.json"), brand)
    update_style_md(style, quiet=True)
    print(f"Starter logo saved in {ldir}")
    for key, label in (("onDark", "For dark backgrounds"), ("onLight", "For light backgrounds"), ("mark", "Brand mark")):
        if key in saved:
            print(f"  {label}: {p(style, saved[key])}")
    if not res.get("fontLoaded"):
        print(f'  NOTE: the font "{font["family"]}" didn\'t load, so a stand-in font was used. Check the name, or pass '
              "--font with a free Google Font.")
    if kept:
        names = {"onDark": "the logo for dark backgrounds", "onLight": "the logo for light backgrounds", "mark": "the brand mark"}
        print(f"  NOTE: kept their own file for {', '.join(names[k] for k in kept)} on the sheet "
              "(add --replace to use the starter one).")
    print("  Next: run sheet to put it on the brand sheet.")


STYLE_DIRS = ("My Style", "my-style")
WORK_DIRS = (("Raw Clips", "one folder per video with its raw clips, named PT 1, PT 2, PT 3..."),
             ("Edits", "one folder per video with the finished edit"),
             ("References", "videos and screenshots you like, for ideas"))


def style_in(home):
    for d in STYLE_DIRS:
        if os.path.isfile(p(home, d, "STYLE.md")):
            return p(home, d)
    return None


def folder_note(home, style=None):
    """Write (or refresh) the block in home/CLAUDE.md that tells every Claude session how this folder works."""
    lines = ["<!-- not-another-edit:start -->", "## This folder (set up by Not Another Edit)"]
    if style:
        rel = os.path.relpath(p(style, "STYLE.md"), home)
        lines.append(f"- **My edit style:** before you plan or edit any video here, read `{rel}` and follow it. "
                     "When I give notes on an edit, add them to its \"Feedback from edits\" section with the date.")
    lines += ["- `Raw Clips/<video name>/`: the raw clips for each video, filmed in parts named PT 1, PT 2, PT 3... "
              "Join them in number order (PT 2 comes before PT 10). Never change or delete anything in here.",
              "- `Edits/<video name>/`: one folder per video, holding its finished edit.",
              "- `References/`: videos and screenshots I like, for ideas.",
              "- To build or change my style: /branding-pack. To edit a video: /edit-this-video.",
              "<!-- not-another-edit:end -->"]
    block = "\n".join(lines)
    path = os.path.join(home, "CLAUDE.md")
    text = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    if "<!-- not-another-edit:start -->" in text:
        text = re.sub(r"<!-- not-another-edit:start -->.*?<!-- not-another-edit:end -->", lambda m: block, text, flags=re.S)
    else:
        text = (text.rstrip() + "\n\n" if text.strip() else "") + block + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def cmd_setup(args):
    if len(args) > 1:
        die('Usage: nae.py setup ["<folder>"]   (default: the folder Claude Code is open in)')
    home = os.path.abspath(os.path.expanduser(args[0] if args else "."))
    os.makedirs(home, exist_ok=True)
    made = []
    for d, _ in WORK_DIRS:
        if not os.path.isdir(p(home, d)):
            os.makedirs(p(home, d))
            made.append(d)
    style = style_in(home) or p(home, STYLE_DIRS[0])
    if not os.path.isdir(style):
        made.append(os.path.basename(style))
    cmd_init([style])
    note = folder_note(home, style)
    print(f"\nFolders ready in {home}" + (f" (new: {', '.join(made)})" if made else " (all there already)") + ":")
    print(f"  {os.path.basename(style):<12} your style: STYLE.md, your brand, your picks and your style page")
    for d, why in WORK_DIRS:
        print(f"  {d:<12} {why}")
    print(f"  CLAUDE.md    tells every Claude session in this folder how it's laid out ({note})")


def cmd_finish(args):
    if len(args) != 1:
        die('Usage: nae.py finish STYLE')
    style = os.path.abspath(args[0])
    need_style(style)
    home = os.path.dirname(style)
    rel = os.path.relpath(p(style, "STYLE.md"), home)
    path = folder_note(home, style)
    update_style_md(style, quiet=True)
    print(f"Done. {path} now tells Claude to follow {rel} on every edit in this folder.")


def cmd_open(args):
    if len(args) not in (1, 2) or (len(args) == 2 and args[1] not in ("page", "sheet", "folder")):
        die('Usage: nae.py open STYLE [page|sheet|folder]   (page: the style page, the default; sheet: the brand sheet; '
            'folder: the My Style folder, so they can drop logo files in)')
    style = os.path.abspath(args[0])
    need_style(style)
    what = args[1] if len(args) == 2 else "page"
    if what == "page":
        write_page(style)
        page = p(style, "page", "index.html")
    elif what == "sheet":
        out = p(style, SHEET_DIR)
        pngs = [x for x in os.listdir(out) if x.lower().endswith(".png")] if os.path.isdir(out) else []
        page = p(out, pngs[0]) if pngs else p(out, "sheet.html")
        if not os.path.isfile(page):
            die('No brand sheet yet. Make one with: nae.py sheet "STYLE" --data ...')
    else:
        page = style
    opener = {"darwin": ["open"], "win32": ["cmd", "/c", "start", ""]}.get(sys.platform, ["xdg-open"])
    try:
        subprocess.Popen(opener + [page], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Opened {page}")
    except OSError:
        print(f"Open this file in your browser: {page}")


COMMANDS = {"check": cmd_check, "setup": cmd_setup, "init": cmd_init, "brand": cmd_brand, "face": cmd_face, "visual": cmd_visual,
            "frames": cmd_frames, "cut": cmd_cut, "round": cmd_round, "picks": cmd_picks,
            "style-md": cmd_style_md, "finish": cmd_finish, "open": cmd_open, "sheet": cmd_sheet, "logo": cmd_logo}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
