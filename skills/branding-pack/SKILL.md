---
name: branding-pack
description: Branding Pack (part of Not Another Edit). Walks a creator (usually not technical) through building their OWN video editing style, step by step, so the videos Claude edits for them look like them and not like every other AI edit. A short brief one question at a time (what it's for, who's watching, their brand, reference videos, the AI-edit slop to cut, how things should move, visuals, sound), starting with their brand sheet (colours, fonts and logos on one page they keep, saved as a PNG and a PDF), then rounds of real animated options in their colours and font on a picker page that opens in their browser. They mark Keep, Maybe or Drop with notes, copy their picks and paste them back, until it's locked. Ends with a plain-English STYLE.md in their folder that Claude follows on every edit. Use whenever someone says "/branding-pack", "branding pack", "not another edit", "build my edit style", "build my brand style", "make my brand sheet", "brand guide", "make me a logo", "make my editing style", "deslop my edits", "I want my own edit style", "make my edits not look like AI", pastes picks that start with "Branding Pack picks" (or the older "Not Another Edit picks"), or comes back to carry on their style.
---

# Branding Pack

The person ends up with their own editing style, built from nothing: a picker page in their browser where
they watch real animations in their own colours and font, keep what they love and drop what they don't.
Everything they decide goes into one file, `STYLE.md`, that Claude follows on every edit after that. You
do all the technical work. They watch, click and talk.

**Who you're talking to:** a creator who is usually NOT technical. **You lead.** Short, plain messages,
one question at a time, in chat. At the end of every step, say in one line what happens next. No jargon,
no code on screen, no em dashes. Ask before installing anything. Never ask them to open or edit a file
themselves, except the picker page, which you open for them.

`SK` = this skill's folder. `HOME` = the folder they work in (the one Claude Code was opened in, unless
step 1 makes a `Video Editing` folder). `STYLE` = their style folder, `HOME/My Style` (remembered in
`SK/config.json` as `styleDir`). Every command is
`python3 "SK/scripts/nae.py" <command> "STYLE" ...`. Quote every path: they often have spaces.
Run any command with no arguments to see its usage.

## The folder they work in (setup makes it; they never have to)
`My Style/` (below) · `Raw Clips/<video name>/` (their clips, named PT 1, PT 2...) · `Edits/<video name>/`
(each finished edit) · `References/` (videos they like) · `CLAUDE.md` (a short note so every Claude session
in this folder knows the layout and follows their style). /edit-this-video uses the same folders.

## What the style folder holds
`STYLE.md` (the style: brief, brand, slop we cut, locked, rejected, feedback) · `Brand Sheet/` (their brand
sheet: `<Name> Brand Sheet.png` and `.pdf`, plus `sheet.html`) · `brand.json` (brand basics + `sheet`) · `lines.json`
(their own words used in previews) · `settings.json` (slop rules, ids) · `round.json` (the current round) ·
`locked.json` · `rejected.json` · `page/` (the picker page; `page/custom.js` holds options written just for
them) · `assets/` (their logos in `assets/logos`, face clip, a screenshot, their font) · `references/` · `picks/` · `notes/their-words.md` · `old/`.

## Hard rules
- **Their taste, not ours.** The skill brings no look of its own. Every colour, move, corner and sound comes
  from their brief and their picks. The one thing offered up front is the slop menu
  (`references/slop-menu.md`), and they choose from it themselves. Never say "most creators like" or "I'd go with".
- **Ask, don't add.** Visuals, photos, sound effects, labels: offer each once, in plain words. If they say
  no, leave it out.
- **Their brand from round 1.** Every option is in their colours, font and words. Their brand sits locked at the top of the page.
- **Never break a "Slop we cut" rule.** The helper refuses options that do. Don't force them back in unless
  they ask to drop that rule (then say so in one line and update it with `cut`).
- **Write down their words as they say them.** Everything they say they like or hate goes word for word into
  `notes/their-words.md` under a topic heading with the date. STYLE.md only gets what they've decided.
- **The page only shows what's still in play.** Drops never come back. Keeps stay. Maybes get fixed
  exactly the way the note says, nothing extra.
- **When they name what to keep, that's the decision.** "Just keep CAP3" = `keep-only`. If a sentence could
  mean two things, ask in one line before changing anything.
- **Check before you show.** `round show` must have no warnings before you open the page. Read the warnings
  and fix them. Never say "done" off a guess.
- **Learn from references, don't copy them.** Take what a reference video DOES (timing, how things move,
  where text sits), never its colours, logo or face.
- **Never delete their stuff, never upload it.** Old versions go to `old/` (the helper does this). Their
  clips, brand and picks stay on their computer.

## Workflow (you lead; they only answer)
Rough time: about 30 to 45 minutes for the first sitting, then a few short rounds whenever they like.

### 0. Welcome back? (every run)
If this folder has `My Style/STYLE.md`, or `SK/config.json` has a `styleDir` that exists: run `round "STYLE" show` and `style-md "STYLE" --check`,
then tell them in two lines where they are and what's next. If they pasted picks, go to step 5. Otherwise
start at step 1.

### 1. Setup (about 2 minutes)
Say: "Welcome to Branding Pack. First a quick check that your computer is ready (a few seconds)."
- You need to be able to run commands in a local folder (Claude Code, Local). If you can't: "Open the
  Claude desktop app, click Code, choose Local, pick a folder, then type /branding-pack again." Stop.
- `check`. Python is all you need. ffmpeg is optional (it trims their clip for the previews and studies
  reference videos). If it's missing, say so in one line and carry on; offer it again only if they send a clip.
  On a Mac, if `python3` isn't found, a window may offer to install "developer tools": tell them to click
  Install, wait, and say done.
- Set up their folder. If Claude Code is open in their home folder, Desktop, Documents or Downloads, or a
  folder already full of unrelated files, don't set up there: say "I'll make a folder called Video Editing
  here to keep all of this together" and run `setup "./Video Editing"`. Otherwise `setup "."`. Then say in
  one short list what each folder is for (the helper prints it): My Style (your style), Raw Clips (put each
  video's clips in its own folder here, named PT 1, PT 2...), Edits (finished videos land here), References
  (videos you like). If you made a Video Editing folder, add: "Next time, open that folder in Claude Code."
- `open "STYLE"`: their page opens on an example round in placeholder colours. Say: "That's your style page. It's showing an example for now: tap
  one to see it big. Next I'll ask you a few quick questions so your first real round is made for you."

### 2. The brief, one question at a time (about 10 minutes). Read `references/interview.md` first.
What it's for, their brand (this is where their brand sheet gets made: `references/brand-sheet.md`), where
it's posted (the shape follows from it), who's watching, 2 to 5 videos they love and
why, the slop menu, anything else they never want, how things should move, visuals, sound effects, what to
build first, and a short clip of them talking (optional). Write it into STYLE.md "The brief" in their words,
read it back in five lines, and wait for their OK. Then save what you learned:
- `brand "STYLE" --name ... --paper ... --ink ... --accent ... --font ... [--font-source google]` and
  `--lines '{...}'` (see interview.md). Read the contrast line back in plain words; they decide.
- `cut "STYLE" <the slop they picked>`.
- `face "STYLE" "<clip>"` if they sent one. `visual "STYLE" "<screenshot>"` if they have one to show.

### 3. References (optional, about 5 minutes)
If they sent video files and ffmpeg is installed: `frames "STYLE" "<file>"` for each, then look at the
contact sheet and stills yourself. Links: ask them to save the video and send the file (Instagram usually
blocks downloads). No ffmpeg or no files: work from what they said they love. Tell them in under 80 words
what their references have in common and which of those round 1 tries. Add it to STYLE.md "Open questions"
if anything is unclear.

### 4. Round 1. Read `references/rounds.md` and `references/library.md`.
Build round 1 from their brief only: `round "STYLE" first --sections "<what they want first>"` (two or three
sections is plenty for a first round). It starts from neutral options and leaves out anything that breaks
their slop rules. Then shape it to the brief: `remove` what doesn't fit, `set` to tune, `add` variations
that follow what they said and what the references do. Three to six options per section, one change per
option. Give each section a one-line job with `note`. `round show` with no warnings, then `open "STYLE"`:
"Round 1 is open in your browser. Every option is a real animation in your colours: tap one to see it big.
Mark Keep, Maybe or Drop and leave a note on anything close ('slower', 'bigger'). Then press Copy my picks
at the bottom and paste them here."

### 5. Their picks, and every round after
When they paste text starting "Branding Pack picks" (or "Not Another Edit picks"): save it exactly to a file (e.g. `STYLE/picks/latest.txt`)
and run `picks "STYLE" "<that file>"`. It files keeps, maybes, drops and notes, and moves to the next round.
Then:
1. Tell them in a few lines what they kept, what they dropped, and any pattern in their notes.
2. Fix every Maybe exactly the way its note says (`set`), nothing extra. A note on a Keep ("keep but
   slower") is a change request too: make a new variation with `add` and leave the kept one as it is.
3. Push the keeps a little further with one or two new variations each. Add new sections they asked for.
4. Write the change lines (`changes "STYLE" "Captions: CAP4 now fades in 0.3 s slower, like you asked" ...`).
5. Update STYLE.md: when a section is settled (one clear keep, or they say "go with that": `keep-only`),
   write it under "Locked" as a `### <Section>` heading with rules someone else could follow: sizes,
   colours, timings in seconds, where it sits, when to use it, what never to do. Add drops' reasons
   under Rejected (the list updates itself; add the why in their words if they gave one).
6. `round show` with no warnings, `open "STYLE"`, and say what to look at.
Repeat until nothing is on Maybe. If they tell you things in chat instead of copying picks, act on the
chat with `set`, `remove` and `keep-only`.

### 6. Finish
Turn `notes/their-words.md` into a short numbered list of plain preferences (one line each) and ask which
ones go into STYLE.md. Fill the "Visuals and photos" and "Sound" sections from their brief (or delete the
heading if they didn't want them). Run `style-md "STYLE" --check` until nothing important is open. Then
`finish "STYLE"`: it updates the note in `CLAUDE.md` so every future Claude session there reads STYLE.md
before editing. Say: "Your style is done and saved in My Style, next to your brand sheet. To edit a video: put its clips in Raw Clips
in a folder named after the video, start a new chat in this folder and type /edit-this-video. I follow your
style on every edit. Every note you give me on an edit gets added to it, so each
edit gets closer to you."

### 7. When they edit a video with it
Read `references/editing.md`. Short version: read all of STYLE.md first, keep every "Slop we cut" rule,
design each moment inside the locked look rather than repeating the same layout, and turn every note they
give into a dated line under "Feedback from edits".

## Files
`scripts/nae.py` (everything: check, setup, init, brand, sheet, logo, face, visual, frames, cut, round, picks, style-md, finish, open) ·
`page/` (the picker page: `index.html`, `app.js`, `library.js` with the option types, `style.css`, `custom.js`) ·
`catalogue.json` (the neutral starting options) · `templates/STYLE.md` · `templates/sheet/` (the brand sheet page) · `templates/logo/` (the starter logo) ·
`references/`: interview.md, brand-sheet.md, slop-menu.md, rounds.md, library.md, editing.md.
