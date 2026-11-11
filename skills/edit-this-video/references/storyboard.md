# plan.json: the storyboard

You write `WORK/plan.json` after `cut`. All times are in seconds on the finished video (the times in
`words.txt`). `board` checks it and builds the storyboard page; `render` builds exactly the same thing.

```json
{
  "title": "Dead giveaways",
  "round": 1,
  "captions": { "params": { "...": "their locked captions params, copied from `ete.py style`" } },
  "beats": [
    {
      "id": "B1", "start": 0.0, "end": 3.99,
      "say": "I've been video editing for years and these are the dead giveaways...",
      "status": "new",
      "overlays": [
        { "type": "title", "params": { "...": "locked title params" }, "lines": ["Dead giveaways", "of a Claude edit"],
          "at": 0.0, "dur": 3.6, "label": "hook title" }
      ],
      "transition_out": { "kind": "flash", "ms": 160, "color": "white" },
      "options": {
        "A": { "label": "title only" },
        "B": { "label": "title + name tag",
               "overlays": [ { "type": "label", "params": { "...": "locked label params" },
                               "text": "Alex · Not Another Agency.AI", "at": 0.4, "dur": 3.0, "label": "name tag" } ] }
      },
      "pick": "A"
    },
    {
      "id": "B2", "start": 3.99, "end": 5.40, "say": "They get more niche as we go.",
      "zoom": { "kind": "punch", "amount": 1.15 }
    }
  ]
}
```

## Beats
- `id` B1, B2... in order. `start`/`end` cover the video with no gaps: each beat starts where the last ended,
  the first at 0, the last ends at the video's length. Cut beats at the start of a word.
- One beat = one idea (a point in a list, the hook, the call to action). Usually 3 to 10 seconds.
- `say` = the words in that beat (from words.txt), so they can read along.
- `status`: leave as `review` sets it ("new", "approved", "change"). `note` holds their last note.
- `captions: false` turns captions off for that beat (they also switch off under a full-screen visual).

## On screen (`overlays`)
Each overlay is one option type from their style, with their locked params:

| type | extra fields | what it is |
|---|---|---|
| `title` | `lines`: 1 or 2 short lines | a title line at the top. Keep each line under about 16 characters at size 96 |
| `keyword` | `word`: one word | one important word, big, while they say it. Time `at` to the word in words.txt |
| `label` | `text`: "Name · what they do" | a name tag or small label |
| `visual` | `src`: "assets/file.png" (a REAL image in WORK/assets) | a screenshot, logo or photo |
| any custom type | whatever its params need | options written in their style's custom.js |

`at` (default: the beat's start) and `dur` (default: to the beat's end) place it. `label` is how it's
described on the storyboard card, in plain words ("key word: Emojis"). Params come from `ete.py style`
(copy them exactly); change a param only when the beat needs it (a `y` to move a title clear of a visual),
never into something their slop rules cut.

## Zooms
`"zoom": { "kind": "punch", "amount": 1.15 }` jumps in for the beat (or from `at` for `dur`).
`"kind": "push", "amount": 1.1, "ms": 2000` eases in slowly. Use their locked zoom if they have one.

## Transitions
`"transition_out"` on the beat that ends: `cut` (default), `flash` (a quick colour flash, `ms` about 120 to
200) or `dip` (a quick dip to a colour, `ms` about 300 to 500). Their locked transition if they have one;
only those three render.

## Sound effects
Only if their STYLE.md "Sound" section says so, and only with real files they gave you:
`"sfx": [ { "file": "assets/sfx/hit.wav", "at": 12.3, "gain": -12 } ]` on the beat. If they cut "a sound on
every graphic", only the moments that matter get one.

## Options (A, B, C)
Put 2 or 3 options on the beats that matter most: the hook, the big moment, the call to action. Each option
adds its own `overlays` / `zoom` / `transition_out` on top of the beat's shared ones, and has a plain `label`
("DESLOP as a big key word"). `pick` is the one shown first; their review sets it. Don't put options on
every beat: it turns a review into homework.
