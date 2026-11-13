// Branding Pack: draws a starter logo (wordmark for dark and light backgrounds, plus an initials mark) on a
// canvas, then writes the PNGs as data URLs into #out for nae.py to save. Transparent backgrounds, tight crop.
(async () => {
  const D = window.LOGO;
  const out = document.getElementById("out");
  const done = (o) => { out.textContent = "LOGO-RESULT " + JSON.stringify(o) + " LOGO-END"; };
  try {
    const f = D.font;
    const style = f.italic ? "italic" : "normal";
    if (f.source === "google") {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(f.family).replace(/%20/g, "+")}:ital,wght@${f.italic ? 1 : 0},${f.weight}&display=block`;
      await new Promise((res) => { link.onload = res; link.onerror = res; document.head.appendChild(link); });
    } else if (f.source === "file" && f.data) {
      const face = new FontFace(f.family, `url(${f.data})`, { weight: String(f.weight), style });
      document.fonts.add(await face.load());
    }
    const spec = (size, fam = `"${f.family}", "Helvetica Neue", Arial, sans-serif`) => `${style} ${f.weight} ${size}px ${fam}`;
    let loaded = false;
    try { loaded = (await document.fonts.load(spec(100), D.text)).length > 0; } catch (e) { loaded = false; }
    const probe = document.createElement("canvas").getContext("2d");
    const width = (fam) => { probe.font = spec(100, fam); return probe.measureText(D.text + "mwil").width; };
    if (!loaded) loaded = width(`"${f.family}", monospace`) !== width("monospace"); // installed system font

    const setup = (x, size) => { x.font = spec(size); x.letterSpacing = `${D.tracking * size}px`; x.textBaseline = "alphabetic"; };

    // ---------- wordmark: lines of words, each word with its own colour
    const wordmark = (lines, size) => {
      const c = document.createElement("canvas");
      let x = c.getContext("2d");
      setup(x, size);
      const lh = size * D.leading;
      const m = lines.map((words, i) => {
        const mm = x.measureText(words.map((w) => w.t).join(" "));
        const y = i * lh;
        return { words, y, left: -mm.actualBoundingBoxLeft, right: mm.actualBoundingBoxRight,
          top: y - mm.actualBoundingBoxAscent, bottom: y + mm.actualBoundingBoxDescent };
      });
      const pad = Math.round(size * 0.06);
      const L = Math.min(...m.map((r) => r.left)), R = Math.max(...m.map((r) => r.right));
      const T = Math.min(...m.map((r) => r.top)), B = Math.max(...m.map((r) => r.bottom));
      c.width = Math.ceil(R - L + 2 * pad);
      c.height = Math.ceil(B - T + 2 * pad);
      x = c.getContext("2d");
      setup(x, size);
      x.translate(pad - L, pad - T);
      for (const r of m) {
        let px = 0;
        r.words.forEach((w, i) => {
          x.fillStyle = w.c;
          x.fillText(w.t, px, r.y);
          px += x.measureText(w.t + (i < r.words.length - 1 ? " " : "")).width;
        });
      }
      return c.toDataURL("image/png");
    };

    // keep the longest line under ~4000px wide
    probe.font = spec(100);
    probe.letterSpacing = `${D.tracking * 100}px`;
    const widest = Math.max(...D.lines.map((ws) => probe.measureText(ws.map((w) => w.t).join(" ")).width));
    const size = Math.min(D.size, Math.floor((4000 / widest) * 100));
    const paint = (colours) => D.lines.map((ws) => ws.map((w) => ({ t: w.t, c: w.accent ? colours.accent : colours.text })));

    const res = { ok: true, fontLoaded: loaded,
      onDark: wordmark(paint(D.onDark), size), onLight: wordmark(paint(D.onLight), size) };

    // ---------- mark: initials on a square of the primary colour
    if (D.mark) {
      const side = 1000;
      const c = document.createElement("canvas");
      c.width = c.height = side;
      const x = c.getContext("2d");
      x.fillStyle = D.mark.bg;
      x.fillRect(0, 0, side, side);
      setup(x, 100);
      let mm = x.measureText(D.mark.text);
      const w = mm.actualBoundingBoxLeft + mm.actualBoundingBoxRight;
      const h = mm.actualBoundingBoxAscent + mm.actualBoundingBoxDescent;
      const s = 100 * Math.min((side * 0.6) / w, (side * 0.46) / h);
      setup(x, s);
      mm = x.measureText(D.mark.text);
      x.fillStyle = D.mark.fg;
      x.fillText(D.mark.text,
        (side - (mm.actualBoundingBoxLeft + mm.actualBoundingBoxRight)) / 2 + mm.actualBoundingBoxLeft,
        (side - (mm.actualBoundingBoxAscent + mm.actualBoundingBoxDescent)) / 2 + mm.actualBoundingBoxAscent);
      res.mark = c.toDataURL("image/png");
    }
    done(res);
  } catch (e) {
    done({ ok: false, error: String(e && e.message || e) });
  }
})();
