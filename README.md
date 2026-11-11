# Not Another Edit

Build your own video editing style with Claude, step by step, then let Claude edit your raw clips in it, so your videos look like you and not like every other AI edit.

Two skills:

- **`/not-another-edit`** builds your style. You answer a few quick questions, then mark real animated options in your own colours and font **Keep**, **Maybe** or **Drop** until it's right. Everything you decide is saved in one plain-English file, `STYLE.md`.
- **`/edit-this-video`** edits your clips in that style. It joins your parts in order, keeps your last clean take of every line, cuts the dead space, shows you a storyboard to approve, then builds the finished video.

Made by [Not Another Agency.AI](https://notanotheragency.ai).

## Part 1: build your style (`/not-another-edit`)

1. **A short brief.** One question at a time: what the videos are for, who's watching, your brand (send your website and Claude reads your colours and font, or start from scratch), 2 to 5 videos you love and what you love about them, how things should move, and whether you want visuals and sound effects.
2. **Cut the slop.** A menu of the dead giveaways that make an edit look AI-made: emojis, everything popping in, rounded corners, a sound on every graphic, the "Claude look", out-of-sync lips and dead space. Pick which ones you never want. Claude never shows you an option that breaks them.
3. **Rounds on your style page.** Your page opens in your browser. Every option plays as a real animation in your brand (on your own face if you send a short clip). Mark Keep, Maybe or Drop, add a note like "slower" or "bigger", press **Copy my picks** and paste them into Claude. Drops never come back, keeps stay, maybes get fixed exactly the way you asked.
4. **Your style, saved.** When you're happy, Claude writes it all into `STYLE.md` and tells every future Claude session in that folder to follow it.

It starts blank. There's no built-in look: everything comes from your answers and your picks.

## Part 2: edit a video with it (`/edit-this-video`)

1. **Film vertically, in as many parts as you like.** Name them `PT 1`, `PT 2`, `PT 3`... and put them in one folder. Flubbed lines are fine: it keeps your last clean take.
2. **Start a new chat and type `/edit-this-video`.** Point it at the folder.
3. **It hears every word.** It joins the parts in order, picks your takes, and cuts every pause your style says to cut.
4. **Storyboard first.** A page opens with every beat of your video playing, with its real captions and graphics in your style, plus a few options on the key moments. **Approve** each beat or press **Change** and say what you want. Nothing gets built until you approve.
5. **Then it builds the video** at the frame rate you filmed in, checks its own render, and opens it for you.
6. **Every note sticks.** Tell it "make the key words bigger" and it fixes it and saves it into your style, so the next edit already knows.

## Install

You don't need to know any code.

1. **Open Claude Code.** Download the Claude desktop app from [claude.ai/download](https://claude.ai/download) and sign in (Claude Code needs a paid plan). Click the **Code** tab, choose **Local**, and pick a folder for your videos (make a new one called "My videos" if you like).
2. **Paste this into the box at the bottom and press Enter:**

   ```
   Install the skills from https://github.com/notanotheragencyai/not-another-edit
   ```

   Claude may ask permission to run a few things. Say yes.
3. **Start a new chat** (so Claude sees the new skills), type `/not-another-edit` and press Enter. Claude takes it from there, one question at a time.
4. When your style is done, start a new chat, type `/edit-this-video` and point it at a folder of clips.

To update later, paste the same line again. Your style and your videos stay where they are.

## For Claude: how to install

When the user asks you to install or update these skills:

1. Clone the repo into a fresh temporary folder:
   `DIR="$(mktemp -d)" && git clone --depth 1 https://github.com/notanotheragencyai/not-another-edit "$DIR/not-another-edit"`
   (On a Mac without git, a window offers to install the developer tools: tell the user to click Install, wait, and say done.)
2. Run `bash "$DIR/not-another-edit/install.sh"` (both skills), or name the ones they asked for: `bash "$DIR/not-another-edit/install.sh" not-another-edit`. It copies them into `~/.claude/skills/`, moves any older copy to `~/.claude/skills-backup/` instead of deleting it, and keeps each skill's saved settings.
   On Windows, copy the folders in `skills/` into `%USERPROFILE%\.claude\skills\` instead.
3. Tell the user in plain English: it's installed, start a new chat, then type `/not-another-edit` to build their style and `/edit-this-video` to edit with it.

Don't change the user's settings or install anything else. Each skill checks the computer itself on first run.

## What you need

- A Mac (Windows and Linux work for the style page; editing is tested on Mac)
- Claude Code (the Code tab in the Claude desktop app, on a paid Claude plan)
- Python 3 (already on most Macs; if not, the Mac offers to install it the first time)
- For editing: [ffmpeg](https://ffmpeg.org) (free; `/edit-this-video` tells you the one line to install it), Google Chrome, and about 2 GB of free space for the speech-to-text and render tools. They're installed into their own folder (`~/.not-another-edit`), never into your Mac's own Python, and only after you say yes.

Nothing is uploaded anywhere. Your style page and storyboard are files on your computer, and your clips, brand and picks stay with you.

## Where things live

- The skills: `~/.claude/skills/not-another-edit` and `~/.claude/skills/edit-this-video`
- Your style: the folder you pick, inside the folder you opened Claude Code in (suggested: `my-style`). Inside: `STYLE.md`, your brand, your rounds, your picks, your page and your own words in `notes/`.
- Your edits: one folder per video (suggested: `Edits/<same name as the clips folder>`), with the storyboard, the plan and the finished `.mp4`.

## If something goes wrong

- **A page opens but nothing moves:** refresh it. If a card shows a red message, copy it and paste it into Claude.
- **Your font looks wrong:** tell Claude. Free Google Fonts work straight away; for your own font, send Claude the font file.
- **"command not found: brew" in Terminal:** install Homebrew from [brew.sh](https://brew.sh), run the "Next steps" lines it prints, then close and reopen Terminal.
- **Anything else:** copy the confusing text, paste it into Claude and ask what it means.
