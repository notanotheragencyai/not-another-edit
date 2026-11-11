# The slop menu

The dead giveaways that make an edit look like Claude made it. It's asked during the brief (question 6),
before "anything else you never want?", so round 1 is built without the ones they pick. It's an offer:
nothing is picked for them.

## How to ask
Say: "Here are the dead giveaways that make an edit look AI-made. They get more niche as you go down. Which
ones do you want cut from your edits for good? Pick any, all or none, and add your own." Then show the list
below in chat, numbered, with the short name and the one-line why.

They answer in words ("1, 3 and 5", "all of them", "none"). Read their picks back once, then:
- Save them: `nae.py cut "STYLE" <ids>`. Each one becomes a hard rule in STYLE.md "Slop we cut".
- Anything they add goes under "Also never:" in STYLE.md, in their words, written so someone else could follow it.
- Lines they didn't pick go into `notes/their-words.md` as "not cut: ...". Don't offer them again.

From then on no round shows an option that breaks one of their picks: the helper refuses it. If they later
want one back, run `cut` again without it and say so in one line.

## The menu

| # | id | Short name | Why it gives you away | The rule that goes into STYLE.md |
|---|---|---|---|---|
| 1 | `emoji` | Emojis and stock icons | A rocket, a fire, a light bulb on every point | No emojis or stock icons. Use a real image: a screenshot, or a photo from Google or Pinterest. |
| 2 | `pop` | The pop | Every word, box and image bounces onto the screen | Nothing bounces or scales in. Only animate what actually changes; everything else cuts in. |
| 3 | `corners` | Rounded corners | Every card, photo and label rounded is the template look | Square corners on every card, photo and label. |
| 4 | `sfx` | A sound on every graphic | Whoosh, pop, ding, whoosh: nothing stands out | Sound effects only on the moments that matter. |
| 5 | `claude-look` | The Claude look | Cream background, a serif font, one word in italics, a tiny label over everything | Only the brand colours and fonts in STYLE.md. If they didn't choose it, it doesn't go in. |
| 6 | `fps` | Lips out of sync | The render lowered the frame rate and the audio slipped | Render at the same frame rate the footage was filmed in. |
| 7 | `deadspace` | Dead space | Little pauses add up and the video drags | Cut every silence longer than 0.12 seconds. |
