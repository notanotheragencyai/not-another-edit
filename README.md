# Not Another Edit

Build your own video editing style with Claude, step by step, so your edits look like you and not like every other AI edit.

You answer a few quick questions. Claude then shows you real animated options in your own colours and font: captions, titles, key words, zooms, visuals, labels and transitions. You mark each one **Keep**, **Maybe** or **Drop**, and Claude builds the next round from your picks until it's right. Everything you decide is saved in one plain-English file, `STYLE.md`, that Claude follows every time it edits a video for you.

Made by [Not Another Agency.AI](https://notanotheragency.ai).

## How it works

1. **A short brief.** One question at a time: what the videos are for, who's watching, your brand (send your website and Claude reads your colours and font, or start from scratch), 2 to 5 videos you love and what you love about them, how things should move, and whether you want visuals and sound effects.
2. **Cut the slop.** A menu of the dead giveaways that make an edit look AI-made: emojis, everything popping in, rounded corners, a sound on every graphic, the "Claude look", out-of-sync lips and dead space. Pick which ones you never want. Claude never shows you an option that breaks them.
3. **Rounds on your style page.** Your page opens in your browser. Every option plays as a real animation in your brand (on your own face if you send a short clip). Mark Keep, Maybe or Drop, add a note like "slower" or "bigger", press **Copy my picks** and paste them into Claude. Drops never come back, keeps stay, maybes get fixed exactly the way you asked.
4. **Your style, saved.** When you're happy, Claude writes it all into `STYLE.md` and tells every future Claude session in that folder to follow it. Every note you give on an edit gets added, so each edit gets closer to you.

It starts blank. There's no built-in look: everything comes from your answers and your picks.

## Install

You don't need to know any code.

1. **Open Claude Code.** Download the Claude desktop app from [claude.ai/download](https://claude.ai/download) and sign in (Claude Code needs a paid plan). Click the **Code** tab, choose **Local**, and pick a folder for your videos (make a new one called "My videos" if you like).
2. **Paste this into the box at the bottom and press Enter:**

   ```
   Install the not-another-edit skill from https://github.com/notanotheragencyai/not-another-edit
   ```

   Claude may ask permission to run a few things. Say yes.
3. **Start a new chat** (so Claude sees the new skill), type `/not-another-edit` and press Enter. Claude takes it from there, one question at a time.

To update later, paste the same line again. Your style stays where it is.

## For Claude: how to install

When the user asks you to install or update this skill:

1. Clone the repo into a fresh temporary folder:
   `DIR="$(mktemp -d)" && git clone --depth 1 https://github.com/notanotheragencyai/not-another-edit "$DIR/not-another-edit"`
   (On a Mac without git, a window offers to install the developer tools: tell the user to click Install, wait, and say done.)
2. Run `bash "$DIR/not-another-edit/install.sh"`. It copies the skill into `~/.claude/skills/not-another-edit`, moves any older copy to `~/.claude/skills-backup/` instead of deleting it, and keeps the user's saved style folder setting.
   On Windows, copy `skills/not-another-edit` into `%USERPROFILE%\.claude\skills\` instead.
3. Tell the user in plain English: it's installed, start a new chat, then type `/not-another-edit`.

Don't change the user's settings or install anything else. The skill checks the computer itself on first run.

## What you need

- Claude Code (the Code tab in the Claude desktop app, on a paid Claude plan)
- Python 3 (already on most Macs; if not, the Mac offers to install it the first time)
- A web browser
- Optional: [ffmpeg](https://ffmpeg.org), so the options can play on your own face and Claude can study the videos you love. The skill tells you how to add it if you want it.

Nothing is uploaded anywhere. Your style page is a file on your computer, and your clips, brand and picks stay with you.

## Where things live

- The skill: `~/.claude/skills/not-another-edit`
- Your style: the folder you pick, inside the folder you opened Claude Code in (suggested: `my-style`). Inside: `STYLE.md`, your brand, your rounds, your picks, your page and your own words in `notes/`.

## If something goes wrong

- **The page opens but nothing moves:** refresh it. If a card shows a red message, copy it and paste it into Claude.
- **Your font looks wrong:** tell Claude. Free Google Fonts work straight away; for your own font, send Claude the font file.
- **Your clip doesn't play:** an `.mp4` from your phone works best, or install ffmpeg and Claude converts it for you.
- **Anything else:** copy the confusing text, paste it into Claude and ask what it means.
