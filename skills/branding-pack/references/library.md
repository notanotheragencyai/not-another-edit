# The option types

Every option on the page is one of these types with its own params. Everything is drawn on a 1080 x 1920
frame. Colour params take `ink`, `paper`, `accent` (their brand), `white` or `black`. Entrances:
`cut` (appears), `fade`, `rise` (fades up from a little lower), `slide`, `wipe` (reveals left to right),
`type` (titles only, letter by letter) and `pop` (scales in with a bounce: this is the "pop" slop rule).
Any `radius` above 0 breaks the "corners" rule; `italicWord` and the `tiny` label break "claude-look".

| Type | Section | Params |
|---|---|---|
| `captions` | Captions | `words` 1-4 at a time · `y` 0-1 from the top · `size` px · `weight` 400-900 · `case` none/upper · `color` · `box` none/ink/paper/accent · `radius` · `highlight` none/accent (longest word in accent) · `entrance` cut/fade/rise/pop · `shadow` true/false |
| `title` | Titles | `size` · `weight` · `align` center/left · `y` · `color` · `box` · `radius` · `entrance` cut/fade/rise/pop/wipe/type · `case` · `italicWord` |
| `keyword` | Key words | `style` color/underline/box/outline/plain · `size` · `weight` · `y` · `entrance` · `case` |
| `zoom` | Zooms | `kind` none/punch/push · `amount` e.g. 1.15 · `ms` push length · `caption` true/false |
| `visual` | Visuals | `layout` card/split/full/corner · `radius` · `shadow` · `border` none/ink/paper/accent/white · `entrance` cut/fade/rise/slide/pop · `caption` |
| `label` | Labels | `style` bar/box/plain/tiny · `position` bottom-left/top-left · `radius` · `entrance` |
| `transition` | Transitions | `kind` cut/fade/slide/whip/flash · `ms` · `flash` white/accent/black |

The words come from `lines.json` (`captions`, `title`, `hero`, `label`), set with `brand --lines`.
Visual options show their screenshot if one was added with `visual`, otherwise a plain placeholder.

## Writing your own option
When they want something the types can't do ("the words should slide up from behind a line", "the title
types out in my accent colour then the box drops in"), write it in `STYLE/page/custom.js`, then add it:

```js
NAE_LIB.slide_from_line = {
  dur: 4000,                       // loop length in ms
  build(layer, p, ctx) {           // make the elements once; ctx has brand, lines, font, visual, bg
    const wrap = document.createElement("div");
    wrap.style.cssText = `position:absolute;left:8%;right:8%;top:${(p.y ?? 0.62) * 100}%;overflow:hidden;`;
    const text = document.createElement("div");
    text.textContent = ctx.lines.hero || "Clean";
    text.style.cssText = `font:800 ${p.size || 120}px/1 ${ctx.font};color:${ctx.brand.accent};`;
    wrap.appendChild(text); layer.appendChild(wrap);
    return { text };
  },
  frame(t, n, p, ctx) {            // called every frame with t = ms into the loop; set styles from t only
    const k = Math.min(1, Math.max(0, (t - 600) / 400));
    n.text.style.transform = `translateY(${(1 - k) * 100}%)`;
  },
};
```
```
python3 "SK/scripts/nae.py" round "STYLE" add "Key words" slide_from_line '{"size": 130}' "Slides up from behind a line"
```
Rules for custom options: draw only from `t` (so scrubbing works), stay inside the frame, use their brand
colours and font from `ctx`, and never break a "Slop we cut" rule.
