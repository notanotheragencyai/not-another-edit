# Running rounds

## Making round 1
- Build it ONLY from their brief: the sections they asked for first, in their colours, font and words.
  `nae.py round "STYLE" first --sections "Captions" "Titles"` (no `--sections` lists what's available).
- It starts from the neutral catalogue and leaves out anything that breaks their slop rules. Then shape it:
  `remove` what doesn't fit the brief, `set` to tune, `add` variations that match what they said and what
  their references do. Three to six options per section.
- **Change one thing per option** (speed, entrance, size, colour, position) so comparing is fair. Same words
  and footage across a section.
- If they said "show me" for movement, give each feel one option in the same section: cut (still), fade or
  rise (smooth), slide or wipe (snappy).
- `note "STYLE" "<Section>" "<what this section is for>"` gives each section a one-line job.
- `round show` must print no warnings. Then `open`.

## When they paste picks
1. Save the pasted text exactly to a file, then `picks "STYLE" "<file>"`. It files everything:
   keeps go to `locked.json` and stay on the page marked Kept, drops leave the page for good and go to
   `rejected.json`, maybes stay with their note shown on the card, and the round number goes up.
   If it warns the picks are from an older round, ask before acting on them.
2. Tell them in a few lines what they kept, what they dropped and any pattern in their notes.
3. Fix every Maybe exactly the way the note says, with `set`. Nothing extra. Read notes on Keeps and
   unrated options too: "keep but slower" is a change request (add a new variation, leave the kept one).
4. Add only what they asked for. A note like "make it blue" is about that option, not the whole section.
5. One or two new variations of each Keep, pushed a little further, so they can find the edge.
6. `changes "STYLE" "<one line per change>"`: they show at the top of the page.
7. Update STYLE.md (see SKILL.md step 5), `round show` with no warnings, `open`.

When a section has one clear keep and they say "go with that": `keep-only "STYLE" "<Section>" <id>`, then
write the section up under Locked.

## Timings and sizes in plain words
- "Slower" usually means about 1.5 to 2 times as long; "a touch quicker" about 0.8 times. Say the numbers
  back ("now 0.5 s instead of 0.3 s"). Entrance speeds live in `library.js`; to change one for a single
  option, write a variation in `custom.js` (see library.md).
- "Bigger" for text: about 15 to 25% larger `size`. Check it still fits inside the safe zone.
- Sizes are on a 1080 x 1920 frame.

## Craft checks (quality, not taste)
- Text that nearly touches the edge or other text looks broken: give it room.
- White text on a white screenshot disappears: if a caption sits over a visual, give it a block or move it.
- A visual that sits small in empty space looks unfinished: size it for the frame.

## If something looks wrong
- A card says "Missing option type": the type isn't in `library.js` or `custom.js`. Fix the name or write it.
- The font looks like Helvetica: the font isn't on Google Fonts or the file didn't load. Use `--font-file`
  with their font file, or pick a Google Font.
- Their clip doesn't play: it's probably a format the browser can't read. With ffmpeg, `face` turns it into
  an mp4. Without it, ask for an mp4.
- They lost their marks: marks are kept in their browser per round until they copy them; the same browser
  on the same page brings them back.
