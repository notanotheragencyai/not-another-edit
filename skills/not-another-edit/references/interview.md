# The brief

One question per message. Wait for the answer before the next one. If an answer is vague ("clean",
"modern", "like that guy"), follow up once: "What does clean look like to you? Name a video, or tell me what
you'd see on screen." Plain words, no em dashes. If they already answered something earlier, don't ask again.

**Start from nothing.** Don't suggest a taste. Where a question lists choices, list them evenly and let them
pick. Their answers are the only source of the style.

## The questions, in order

**1. What's it for?** "What's this style for: your own videos, a brand, a client? And what do you want the
editing to do for your videos?"

**2. Where and what shape?** "Where do these videos go, and what shape are they? Vertical (Reels, TikTok,
Shorts), wide (YouTube) or square?"

**3. Who's watching?** "Who's watching, and what should they feel in the first second?"

**4. Their brand.** "Do you already have a brand (colours, a font, a website or a logo), or are we starting
from scratch? Both are fine."
- They have one: "Send me your website, or a screenshot of your logo or a post you like the look of, and
  I'll take your colours and font from it." Read the site or image yourself, say the colours (as hex codes)
  and font back in plain words, and confirm.
- From scratch: ask what colours they're drawn to, or a mood ("warm and earthy", "black and electric"). Offer
  three small palettes that fit THEIR answer, one line each (background, text, one accent). They pick.
- Font: "Do you use a font? If not, I'll show you a few side by side." Fonts that are free on Google Fonts
  work straight away (`--font-source google`). A font file they own works too (`--font-file`). A paid font
  needs a licence to use in public videos: say so once.
- Then `brand` and read out the contrast line in plain words. Don't block on it: they decide.

**5. References.** "Send me 2 to 5 videos whose editing you love (files are best; Instagram links often
won't download). For each one, tell me what you love about it, even just 'clean text' or 'the way logos
come in'." For each one: "What's the moment in this one you'd steal?"

**6. The slop menu, then "never".** Run `slop-menu.md` exactly. Then: "Anything else you never want to see
in your edits?" Their answer goes straight into STYLE.md under "Also never:", in their words.

**7. How should things move?** "How should things move: still and calm, snappy, smooth, energetic, or
'show me'?" "Show me" = round 1 has one option of each feel for the same moment.

**8. Visuals on screen.** "Do you want things on screen while you talk, like screenshots of what you're
talking about, app logos or real photos? Or just you and your words?" If yes: "What's one website or tool
you talk about a lot?" (Take a screenshot of it if you can, or ask them for one, and add it with `visual`.)
If no: leave Visuals out of every round. They can ask later.

**9. Sound effects.** "Do you want sound effects in your edits? If yes, how should they feel: barely there,
noticeable, or punchy? And do you have your own folder of sounds?" Write the answer into STYLE.md "Sound".
The page doesn't play sounds; sounds get picked by ear on real edits.

**10. What first?** "What should we build first: captions, titles, key words, zooms, visuals, labels or
transitions? Or should I pick?" If they say pick, choose two or three from their brief and say why in one line.

**11. Their face (optional).** "Last one: want the options to play on your own face? Send me a 5 to 10
second clip of you talking to camera. Totally optional." Never use someone else's face.

## Then: the brief back to them
Write the answers into STYLE.md "The brief" (one bullet each, their words). Read it back in five lines and
wait for their OK before round 1. Change anything they correct.

## Their words in the previews
Don't ask for this. Build `--lines` for `brand` from what you know about their content, in their voice:
`{"captions": "one sentence of 10 to 14 words they might say", "title": ["hook line one", "line two"],
"hero": "one short word", "label": "Their name · what they do"}`. Keep "hero" to one word under about 8
letters so it fits big on screen.
