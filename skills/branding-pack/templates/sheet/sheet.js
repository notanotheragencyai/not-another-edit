/* Branding Pack: draws the brand sheet from window.BRAND_SHEET (written by nae.py sheet into data.js). */
(function () {
  const D = window.BRAND_SHEET;
  const root = document.getElementById("sheet");
  if (!D) { root.textContent = "No brand data yet."; return; }

  // ---------- colour helpers
  const rgb = (h) => { h = h.replace("#", ""); return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)); };
  const lum = (h) => { const c = rgb(h).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
  const contrast = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const mix = (a, b, t) => { const A = rgb(a), B = rgb(b);
    return "#" + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, "0")).join(""); };
  const rgba = (h, a) => `rgba(${rgb(h).join(",")},${a})`;
  const textOn = (bg) => (contrast("#FFFFFF", bg) >= 3 ? "#FFFFFF" : D.ink); // white reads on bold colours; dark text on pale ones

  // ---------- fonts
  const fonts = D.fonts || [];
  const pick = (kind, fallback) => fonts.find((f) => f.kind === kind) || fallback;
  const display = pick("headline", fonts[0]);
  const body = pick("body", fonts[1] || fonts[0]);
  const accent = pick("accent", Object.assign({}, body, { italic: true }));
  const fam = (f) => `"${f.family}", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif`;
  const head = document.head;
  const faces = new Set();
  const css = [];
  for (const f of fonts.concat([Object.assign({}, body, { weight: 700, italic: false }), Object.assign({}, body, { weight: 400, italic: false })])) {
    const key = `${f.family}|${f.italic ? 1 : 0}|${f.weight}`;
    if (faces.has(key)) continue;
    faces.add(key);
    if (f.source === "google") {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(f.family).replace(/%20/g, "+")}:ital,wght@${f.italic ? 1 : 0},${f.weight}&display=block`;
      head.appendChild(link);
    } else if (f.source === "file" && f.file) {
      css.push(`@font-face{font-family:"${f.family}";src:url("${f.file}");font-weight:${f.weight};font-style:${f.italic ? "italic" : "normal"};}`);
    }
  }
  if (css.length) { const s = document.createElement("style"); s.textContent = css.join("\n"); head.appendChild(s); }

  // ---------- theme
  const st = root.style;
  const vars = {
    "--dark": D.dark, "--light": D.light, "--ink": D.ink, "--primary": D.primary,
    "--primary-glow": rgba(D.primary, 0.55), "--on-dark": contrast(D.light, D.dark) >= 7 ? D.light : "#FFFFFF",
    "--on-primary": textOn(D.primary), "--muted": mix(D.ink, D.light, 0.45), "--line": rgba(D.ink, 0.12),
    "--card": contrast("#FFFFFF", D.light) < 1.04 ? mix(D.light, D.ink, 0.02) : "#FFFFFF",
    "--display-font": fam(display), "--display-weight": display.weight, "--display-style": display.italic ? "italic" : "normal",
    "--body-font": fam(body), "--accent-font": fam(accent), "--accent-style": accent.italic ? "italic" : "normal",
    "--accent-weight": accent.weight,
  };
  for (const k in vars) st.setProperty(k, vars[k]);

  // ---------- tiny DOM helper
  const el = (tag, cls, parent, text) => { const e = document.createElement(tag); if (cls) e.className = cls;
    if (text != null) e.textContent = text; if (parent) parent.appendChild(e); return e; };
  const rich = (parent, text) => { // **bold** only
    String(text).split(/(\*\*[^*]+\*\*)/).forEach((part) => {
      if (/^\*\*[^*]+\*\*$/.test(part)) el("b", null, parent, part.slice(2, -2)); else if (part) parent.appendChild(document.createTextNode(part));
    });
  };
  const heading = (parent, words) => { const h = el("div", "h", parent); const t = el("span", null, h, words[0]);
    if (words[1]) { t.appendChild(document.createTextNode(" ")); el("b", null, t, words[1]); } return h; };

  // ---------- header
  const hd = el("div", "head", root);
  el("div", "glow", hd);
  if (D.mark && D.mark.file && D.mark.inHeader !== false) { const im = el("img", "mark", hd); im.src = D.mark.file; im.alt = ""; }
  el("div", "eyebrow", hd, D.eyebrow);
  const title = el("div", "title", hd);
  (D.title || [D.name]).forEach((line) => el("div", null, title, line));
  if (D.subtitle) el("div", "subtitle", hd, D.subtitle);

  const band = el("div", "band", root);
  el("span", null, band, D.tagline || "");
  el("span", null, band, D.date || "");

  // ---------- colours
  const bd = el("div", "body", root);
  heading(bd, D.headings.colors);
  const cards = el("div", "cards", bd);
  for (const c of D.colors || []) {
    const card = el("div", "card", cards);
    const sw = el("div", "sw", card);
    sw.style.background = c.hex; sw.style.color = textOn(c.hex);
    if (contrast(c.hex, D.light) < 1.15) sw.style.borderBottom = `1px solid ${rgba(D.ink, 0.1)}`;
    el("div", "role", sw, c.role || "");
    el("div", "big", sw, c.hex);
    const info = el("div", "info", card);
    el("div", "name", info, c.name || "");
    const rows = el("div", "rows", info);
    for (const [k, v] of [["Hex", c.hex], ["RGB", c.rgb], ["CMYK", c.cmyk]]) { const r = el("div", "row", rows); el("span", null, r, k); el("span", null, r, v); }
    if (c.use) el("div", "use", info, c.use);
  }
  if (D.gradient && (D.gradient.stops || []).length > 1) {
    const g = D.gradient;
    const card = el("div", "card", cards);
    const sw = el("div", "sw", card);
    sw.style.background = `linear-gradient(135deg, ${g.stops.join(", ")})`;
    sw.style.color = textOn(g.stops[Math.floor(g.stops.length / 2)]);
    el("div", "role", sw, g.label || "Gradient");
    el("div", "big", sw, `${g.stops.length} stops`);
    const info = el("div", "info", card);
    el("div", "name", info, g.name || "Brand gradient");
    const rows = el("div", "rows", info);
    g.stops.forEach((s, i) => { const r = el("div", "row", rows); el("span", null, r, `Stop ${i + 1}`); el("span", null, r, s); });
    if (g.use) el("div", "use", info, g.use);
  }
  if (D.note) el("div", "note", bd, D.note);

  // ---------- fonts + logo
  const lower = el("div", "lower", bd);
  const fl = el("div", "fonts", lower);
  heading(fl, D.headings.fonts);
  for (const f of fonts) {
    const row = el("div", "frow", fl);
    const left = el("div", null, row);
    el("div", "fname", left, f.name || f.family);
    el("div", "frole", left, f.role || "");
    const smp = el("div", "sample" + (f.kind === "headline" ? " headline" : ""), row);
    smp.style.fontFamily = fam(f); smp.style.fontWeight = f.weight; smp.style.fontStyle = f.italic ? "italic" : "normal";
    smp.style.fontSize = (f.size || (f.kind === "headline" ? 46 : f.kind === "accent" ? 30 : 19)) + "px";
    const lines = Array.isArray(f.sample) ? f.sample : [f.sample || "The quick brown fox jumps over the lazy dog."];
    lines.forEach((ln, i) => { const d = el("div", i === lines.length - 1 && lines.length > 1 ? "last" : null, smp); rich(d, ln); });
  }

  const lg = el("div", "logos", lower);
  heading(lg, D.headings.logo);
  const tiles = el("div", "tiles", lg);
  const tile = (cls, src, label) => {
    const t = el("div", "tile " + cls, tiles);
    if (src) { const im = el("img", null, t); im.src = src; im.alt = ""; }
    else { const wm = el("div", "wm", t); (D.title || [D.name]).forEach((l) => el("span", null, wm, l)); }
    el("div", "lab", t, label);
  };
  const L = D.logos || {};
  tile("dark", L.onDark, "On dark");
  tile("lightbg", L.onLight, "On light");
  if (D.mark && D.mark.file) {
    const mr = el("div", "markrow", lg);
    const im = el("img", null, mr); im.src = D.mark.file; im.alt = "";
    const tx = el("div", null, mr);
    el("div", "t", tx, D.mark.title || "Brand mark");
    if (D.mark.note) el("div", "d", tx, D.mark.note);
  }

  // ---------- footer
  const ft = el("div", "foot", root);
  const wm = el("div", "wordmark", ft);
  (D.title || [D.name]).forEach((l, i) => el("span", null, wm, (i ? " " : "") + l));
  el("div", "meta", ft, [D.website, D.est ? `Est. ${D.est}` : ""].filter(Boolean).join(" · "));

  // ---------- fit the big type once the fonts are in
  function fit(node, start, min, maxW) {
    let size = start;
    node.style.fontSize = size + "px";
    const widest = () => node.getBoundingClientRect().width; // .title and .wordmark are max-content wide
    while (size > min && widest() > maxW) { size -= 2; node.style.fontSize = size + "px"; }
  }
  function layout() {
    fit(title, D.titleSize || 86, 44, D.mark && D.mark.file && D.mark.inHeader !== false ? 800 : 1000);
    fit(wm, 28, 16, 700);
    document.querySelectorAll(".sample.headline").forEach((s) => fit(s, parseFloat(s.style.fontSize), 22, 560));
    document.body.dataset.ready = "1";
  }
  const wanted = fonts.map((f) => `${f.italic ? "italic " : ""}${f.weight} 20px "${f.family}"`);
  Promise.race([
    Promise.all(wanted.map((w) => document.fonts.load(w).catch(() => null))).then(() => document.fonts.ready),
    new Promise((r) => setTimeout(r, 4000)),
  ]).then(layout);
})();
