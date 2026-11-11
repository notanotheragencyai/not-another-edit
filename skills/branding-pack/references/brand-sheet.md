# The brand sheet

One page with their brand on it: colours (with HEX, RGB and CMYK), fonts in use, logos on dark and light,
their brand mark, tagline, website and the year they started. It's saved as a PNG and a PDF in
`My Style/Brand Sheet/`, theirs to keep and share. STYLE.md lists the same colours, fonts and logo files, so
every edit uses the exact brand.

## Gather it (one message at a time, during brief question 2)
1. **Start from what exists.** "Do you already have a brand guide or brand sheet? Send it (a screenshot or a
   PDF is fine). If not, send your website, or just tell me your colours and font. Starting from scratch is
   fine too."
   - A sheet, guide or screenshot: read it yourself. Take every colour as a hex code with its name, role and
     what it's used for, every font with its role, the tagline, the website and the year.
   - A website: read it. Take the colours (hex), fonts, name and tagline.
   - From scratch: offer three small palettes that fit what they say they're drawn to (one line each). They
     pick. Then fonts: "Do you use a font? If not, I'll suggest a few free ones."
   Say back what you found in a few short lines (name, colours with hex codes, fonts) and confirm.
2. **Fill the gaps in one message** (they can skip any): "For your sheet: your logo files (a version for dark
   backgrounds and one for light, if you have both), your brand mark or icon if you have one, a tagline, your
   website, and the year you started."
   - Logos: run `open "STYLE" folder` and say "Drop your logo files into this folder and tell me when they're
     in." Then list the folder and pass the files with `--logo-dark`, `--logo-light`, `--mark`. PNG with a
     clear background or SVG works best. Never make a logo up, and never use one from somewhere else.
3. **Name and explain every colour.** If a colour has no name, suggest one (they can change it). Give each a
   role (Primary, Accent, Neutral, Text, Background) and a short "use" line: where it goes. Use their words
   where they gave them. Up to 8 cards fit (colours plus a gradient if they use one); fonts: up to 3.
4. Write `STYLE/notes/sheet.json` (below) and run `sheet "STYLE" --data "STYLE/notes/sheet.json"` plus any
   logo flags. Then `open "STYLE" sheet` and say: "That's your brand sheet, saved in My Style, Brand Sheet,
   as a PNG and a PDF. It's yours to keep and share, and I follow it on every edit. Anything to change?"
   Change what they ask (edit sheet.json, run `sheet` again; older versions move to `old/`).
5. Keep the style page in step: `brand "STYLE" --name ... --paper <light> --ink <dark> --accent <primary>
   --font <body font> --font-source google|system` (plus `--lines`), same colours as the sheet.

## sheet.json
Only `name` and `colors` matter much. Leave out anything they didn't give.
```json
{
  "name": "Not Another Agency.AI",
  "title": ["Not Another", "Agency.AI"],
  "tagline": "Your brand. Your content. Elevated.",
  "website": "notanotheragency.ai",
  "est": "2021",
  "colors": [
    {"role": "Primary", "name": "Signal Orange", "hex": "#EF5023", "use": "Logo, headlines, highlights, calls to action."},
    {"role": "Neutral", "name": "Ink", "hex": "#151515", "use": "Primary background for pages and video."},
    {"role": "Neutral", "name": "Cream", "hex": "#F4EFE9", "use": "Light backgrounds, worksheets and print."}
  ],
  "gradient": {"name": "Brand gradient", "stops": ["#F5A54A", "#EF5023", "#9A3615"], "use": "Feature cards and hero moments."},
  "fonts": [
    {"name": "Inter Display", "family": "Inter", "weight": 900, "kind": "headline", "role": "Black · Headlines",
     "source": "google", "sample": ["Build your", "business."]},
    {"name": "Inter", "family": "Inter", "weight": 400, "kind": "body", "role": "Regular · Body & UI",
     "source": "google", "sample": "**Clear, practical and direct.** Used for body copy, labels and captions."},
    {"name": "Lora", "family": "Lora", "weight": 400, "italic": true, "kind": "accent", "role": "Italic · Quotes & accents",
     "source": "google", "sample": ["Your brand. Your content.", "Elevated."]}
  ],
  "mark": {"note": "Gradient icon for covers, openers and accents."}
}
```
- `title`: the big name in the header, one or two lines (the second line is in the primary colour). Leave it
  out and the name is split for you.
- `primary`, `dark`, `light` (hex): which colours lead. Leave them out: primary = the colour with role
  "Primary" (or their accent), dark = the darkest colour, light = the lightest.
- `fonts`: `kind` is `headline`, `body` or `accent`. `family` is the font's real name to load. `source` is
  `google` (free Google Fonts, loads by itself), `system` (installed on their computer) or `file` (add
  `"file": "/path/to/font.otf"`; it's copied into `assets/fonts`). In `sample`, a list is lines (the last one
  goes in the primary colour) and `**bold**` works.
- Optional: `eyebrow` (default "Brand proof sheet"), `subtitle`, `date` (default today), `note` (the line
  under the colours), `headings` (e.g. `{"colors": ["Brand", "colours"]}` for their spelling).

## Rules
- It's their brand. Never invent a logo, a colour they didn't approve, or a fake year or tagline.
- Paid fonts need their own file and licence. Free Google Fonts are fine.
- Chrome saves the PNG and PDF. Without Chrome, open `Brand Sheet/sheet.html` and save it as a PDF from the
  browser (File, Print, Save as PDF, Background graphics on).
