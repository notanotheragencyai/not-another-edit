---
name: edit-this-video
description: Edit This Video. Turns a folder of raw talking-head clips (usually filmed in parts named PT 1, PT 2 and so on) into a finished vertical video in the creator's own style from Branding Pack (both are part of Not Another Edit). Joins the parts in order, hears every word, keeps the last clean take of each line, cuts the dead space, then shows a storyboard page first (every beat playing with its captions and graphics, options to pick from, Approve or Change) and only builds the full video once they approve. Renders at the frame rate they filmed in, checks its own render, and saves every note into their STYLE.md so the next edit already knows. Use whenever someone says "/edit-this-video", "edit this video", "edit my video", "edit these clips", "make this into a reel", "storyboard this", drops a folder of clips, pastes text starting "Edit This Video storyboard", or gives notes on an edit this skill made.
---

# Edit This Video

Raw clips in, a finished 1080 x 1920 video out, in their own style. The person is usually not technical.
**You lead.** Short, plain messages, one step at a time, in chat. Say which step you're on in one short line
("Step 3 of 7: finding your best takes"). No jargon, no code on screen, no em dashes. Ask before installing
anything. Never post or upload anything anywhere.

`SK` = this skill's folder. `HOME` = the folder they work in (it has `Raw Clips`, `Edits`, `References`). `STYLE` = their style folder
from Branding Pack, usually `HOME/My Style` (found automatically; it has `STYLE.md`). `WORK` = one folder per video. Every command is `python3 "SK/scripts/ete.py" <command> "WORK" ...`.
Quote every path: they often have spaces. Run a command with no arguments to see its usage.

## The rules that matter most
- **Nothing gets built until they approve the storyboard.** The storyboard page shows every beat playing with
  its real captions and graphics, drawn by the same code as the final render. What they approve is what renders.
- **STYLE.md is guardrails, not a menu.** It fixes the look (brand, locked captions and titles, motion, slop
  they cut). It does not limit what you make. For every line, ask what would explain THAT idea best, then make
  it inside the look. Read `references/creative.md` before planning.
- **"Slop we cut" and "Feedback from edits" win over everything.** The helper refuses options that break a
  slop rule. Feedback from edits is their own corrections: read it newest first and follow it.
- **Real things on screen only.** Real screenshots, real logos, real photos. If a beat needs one you don't
  have, ask them for it or take a real screenshot. Never a stand-in, never an emoji.
- **Their frame rate, always.** The render keeps the frame rate they filmed in. The check (qa) fails if it doesn't.
- **Never touch their raw clips.** Everything is written into WORK. Never delete their files.

## Steps

### 1. Setup check (first time about 5 to 10 minutes, then seconds)
`check`. For anything missing, give the one-line fix in plain words:
- ffmpeg missing on a Mac: they paste into the Terminal app (Command + Space, type Terminal):
  install Homebrew from https://brew.sh if `brew` isn't found, then `brew install ffmpeg`. Their Mac password
  goes in Terminal, never in this chat.
- Speech-to-text or renderer missing: ask "Can I install the free editing tools? One time, about 5 minutes,
  in their own folder." On yes: `setup`. The speech model downloads on the first transcribe (about 500 MB).
- No style yet (`new` says "none found"): "You haven't built your style yet. Want to do that first with
  /branding-pack (about 30 minutes), or should I edit this one with plain captions?" Go with their answer.
- No `Raw Clips` folder where they are (first time without Branding Pack): run `folders "."` (or
  `folders "./Video Editing"` if Claude Code is open in their home folder, Desktop, Documents or Downloads)
  and say: "I've set up your folders. Put this video's clips in Raw Clips, in a folder named after the
  video, with the parts named PT 1, PT 2 and so on. Tell me when they're in."

### 2. Intake (one message)
Ask only what you don't already have:
- The clips folder. Usually `Raw Clips/<date title>/` with parts named PT 1, PT 2... (they're joined in number
  order, so PT 2 comes before PT 10).
- What the video is about, and the script if they have one (if their scripts live in a connected app like
  Notion, offer to read it from there).
- The comment keyword, if there's a call to action.
- A target length, if they have one. Otherwise: as tight as the script allows.
Then `new "WORK" --raw "<clips folder>"`. WORK = `HOME/Edits/<the clips folder's name>`
(`Edits/2026-11-11 Test Video`). If there's no `Edits` folder, `folders "HOME"` makes it.
Read the clip order back in one line and confirm.

### 3. Words and takes (about 1 minute per 5 minutes of footage)
1. `transcribe "WORK" --prompt "<names, brand words, the keyword>"`. Read `WORK/transcript.txt`.
2. `edl "WORK" --auto` drafts the cut list: the last clean take of every line, retakes left out. Check it
   against the script and fix `WORK/edl.json` yourself: a line said twice keeps the LAST clean one; a stumble
   mid-line gets trimmed by moving `in` or `out`; a line that's missing gets its piece back.
3. `cut "WORK"`: cuts every silence longer than their dead-space rule (0.12 s if they cut it), snaps every cut
   to a frame so sound and picture stay locked, writes the words with their times, and makes the preview.
4. Read `WORK/words.txt` against what they meant. Fix misheard names: `fix "WORK" 145=Claude` (only ever to
   match what was really said).
Tell them the length and the beats in one line each.

### 4. Plan and storyboard. Read `references/storyboard.md` and `references/creative.md` first.
`style "WORK"` prints their locked options as JSON to copy into the plan. Read STYLE.md in full too. Write
`WORK/plan.json`: the beats, what's on screen in each, zooms, transitions, and 2 or 3 options on the key
moments (the hook, the big reveal, the call to action). Put real visuals in `WORK/assets/`. Then
`board "WORK"`. It must print no problems (fix warnings that matter). Open `WORK/page/board.html`
(`open "WORK/page/board.html"`) and say:
"Your storyboard is open. Each card plays one beat with its captions and graphics: tap one to watch it big with
sound. Approve it, or press Change and say what you want. Pick A, B or C where there's a choice. Then press
Copy my review and paste it here. Nothing gets built until you approve."

### 5. Their review
When they paste text starting "Edit This Video storyboard": save it exactly to `WORK/reviews/latest.txt` and
run `review "WORK" "WORK/reviews/latest.txt"`. Then:
- Change every beat exactly the way its note says, nothing extra. Picks are decisions: keep the picked option.
- If a note is about their style in general ("I never want zooms"), it's feedback: do step 7 for it too.
- `board "WORK"` again, open it, and say what changed in one line per beat.
Repeat until everything is approved. If they say "looks good, build it" in chat, that's approval.

### 6. Build it (a few minutes)
Say roughly how long ("Building your video now, about 5 minutes"). `render "WORK"`, then `qa "WORK"`.
Every line must say OK. Look at the contact sheet yourself (`WORK/render/qa/sheet.jpg`): captions inside the
frame, nothing cut off, the right graphics on the right beats. If anything fails, fix it and render again.
Then `open "WORK/<name>.mp4"` and say: "Your video is ready: <path>. Watch it through and tell me anything you'd change."

### 7. Notes after the edit
Fix every note, render again, and save it so the next edit knows:
`feedback "STYLE" "<their words>" "<the rule it means>"` (for example: "the logos are too small" → "Logos at
least 40% of the frame width"). If a note changes something locked, update the Locked section of STYLE.md too
and say so in one line.

## What it can't do yet (say so plainly if asked)
- Transitions other than a hard cut, a flash or a dip (slides and whips are on the style page but don't render yet).
- Music: they add it themselves, unless they give you a track and ask.
- An editable timeline: this makes a finished video only.

## Files
`scripts/ete.py` (check, setup, folders, new, transcribe, edl, cut, fix, style, board, review, render, qa, feedback, open) ·
`scripts/transcribe_worker.py` (speech-to-text and the silence map) · `scripts/render_worker.py` (draws the
graphics frame by frame) · `engine/` (the storyboard page and the render page; they use Branding Pack's
option library, so the look always matches the style page) · `references/`: storyboard.md, creative.md.
