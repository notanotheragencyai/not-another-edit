/* Not Another Edit: the picker page.
 * Reads window.NAE (written by nae.py into data.js), draws every option as a live preview in the
 * creator's brand, lets them mark Keep / Maybe / Drop with notes, and copies their picks as plain text
 * to paste back into Claude. Opens straight from the file: no server, no account, nothing uploaded.
 */
(function () {
  const D = window.NAE || { brand: {}, lines: {}, round: { n: 0, sections: [] } };
  const LIB = window.NAE_LIB;
  const W = window.NAE_W, H = window.NAE_H;
  const brand = Object.assign({ name: "Your brand", paper: "#ffffff", ink: "#111111", accent: "#888888", font: "Inter" }, D.brand || {});
  const lines = D.lines || {};
  const round = D.round || { n: 0, sections: [] };
  const $ = (sel, root) => (root || document).querySelector(sel);
  const el = (tag, cls, parent, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };

  // ---------- fonts ----------
  const fontStack = `'${brand.font}', 'Helvetica Neue', Helvetica, Arial, sans-serif`;
  if (brand.fontFile) {
    const s = el("style", null, document.head);
    s.textContent = `@font-face{font-family:'${brand.font}';src:url('${brand.fontFile}');font-weight:100 900;font-display:block;}`;
  } else if (brand.fontSource === "google" && brand.font) {
    const l = el("link", null, document.head);
    l.rel = "stylesheet";
    l.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(brand.font)}:wght@400;500;600;700;800;900&display=swap`;
  }

  // ---------- marks (kept in this browser until they copy) ----------
  const KEY = `nae:${brand.name}:round:${round.n}`;
  let marks = {};
  try { marks = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { marks = {}; }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(marks)); } catch (e) { /* private mode */ } updateBar(); };

  // ---------- header ----------
  const app = $("#app");
  const head = el("header", "head", app);
  el("div", "wordmark", head, "Not Another Edit");
  el("h1", null, head, round.example ? "Example round" : `Round ${round.n}`);
  if (round.example) el("p", "banner", head, "This is an example round in placeholder colours. Your real round 1 is built from your answers, in your own brand.");
  const brandRow = el("div", "brand", head);
  el("span", "brand-name", brandRow, brand.name);
  [["Background", brand.paper], ["Text", brand.ink], ["Accent", brand.accent]].forEach(([label, hex]) => {
    const s = el("span", "swatch", brandRow);
    const chip = el("i", null, s); chip.style.background = hex;
    el("span", null, s, `${label} ${hex}`);
  });
  const f = el("span", "swatch", brandRow, `Font: ${brand.font}`);
  f.style.fontFamily = fontStack;
  el("span", "locked", brandRow, "Locked");
  el("p", "how", head, "Watch each option. Tap one to see it big. Mark Keep, Maybe or Drop, and leave a note on anything close (“slower”, “bigger”). When you’re done, press Copy my picks at the bottom and paste them into Claude.");
  if (round.changes && round.changes.length) {
    const c = el("div", "changes", head);
    el("h3", null, c, "What changed since last round");
    const ul = el("ul", null, c);
    round.changes.forEach((x) => el("li", null, ul, x));
  }

  // ---------- previews ----------
  const instances = [];
  function makeStage(parent, opt) {
    const stage = el("div", "stage", parent);
    const canvas = el("div", "canvas", stage);
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    canvas.style.setProperty("--font", fontStack);
    const bg = el("div", "bg", canvas);
    if (D.face) {
      const v = el("video", null, bg);
      v.src = D.face; v.muted = true; v.loop = true; v.autoplay = true; v.playsInline = true;
      v.setAttribute("muted", ""); v.setAttribute("playsinline", "");
      v.play().catch(() => {});
    } else {
      bg.classList.add("placeholder");
      bg.innerHTML = '<svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMax slice"><circle cx="540" cy="760" r="210" fill="#6b6b6b"/><path d="M140 1920 C160 1350 340 1100 540 1100 C740 1100 920 1350 940 1920 Z" fill="#6b6b6b"/></svg>';
    }
    const layer = el("div", "layer", canvas);
    const inst = { stage, canvas, bg, layer, opt, t0: performance.now(), visible: true, paused: false, tFixed: 0, error: null };
    const def = LIB[opt.type];
    if (!def) {
      inst.error = `Missing option type “${opt.type}”`;
      el("div", "err", stage, inst.error);
      return inst;
    }
    inst.def = def;
    inst.ctx = { brand, lines, font: fontStack, visual: D.visual || null, bg };
    try {
      inst.nodes = def.build(layer, opt.params || {}, inst.ctx) || {};
      inst.dur = inst.nodes.dur || def.dur || 4000;
    } catch (e) {
      inst.error = String(e && e.message || e);
      el("div", "err", stage, inst.error);
    }
    const fit = () => { canvas.style.transform = `scale(${stage.clientWidth / W})`; };
    new ResizeObserver(fit).observe(stage); fit();
    io.observe(stage);
    stage.__inst = inst;
    instances.push(inst);
    return inst;
  }
  const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.target.__inst) e.target.__inst.visible = e.isIntersecting; }), { rootMargin: "200px" });

  function tick(now) {
    for (const inst of instances) {
      if (!inst.visible || inst.error || !inst.def) continue;
      const t = inst.paused ? inst.tFixed : (now - inst.t0) % inst.dur;
      try { inst.def.frame(t, inst.nodes, inst.opt.params || {}, inst.ctx); }
      catch (e) { inst.error = String(e && e.message || e); el("div", "err", inst.stage, inst.error); }
      if (inst.scrub && !inst.paused) inst.scrub.value = String(Math.round(t));
    }
    requestAnimationFrame(tick);
  }

  // ---------- cards ----------
  const VERDICTS = [["keep", "Keep"], ["maybe", "Maybe"], ["drop", "Drop"]];
  let optionCount = 0;
  (round.sections || []).forEach((sec) => {
    const s = el("section", "sec", app);
    el("h2", null, s, sec.name);
    if (sec.note) el("p", "sec-note", s, sec.note);
    const grid = el("div", "grid", s);
    (sec.options || []).forEach((opt) => {
      optionCount++;
      const card = el("article", "card" + (opt.state === "kept" ? " kept" : ""), grid);
      card.dataset.id = opt.id;
      const inst = makeStage(card, opt);
      inst.stage.addEventListener("click", () => openBig(opt));
      const ctr = el("div", "ctr", card);
      const play = el("button", "play", ctr, "❚❚");
      play.title = "Pause";
      const scrub = el("input", "scrub", ctr);
      scrub.type = "range"; scrub.min = "0"; scrub.max = String(inst.dur || 4000); scrub.value = "0";
      inst.scrub = scrub;
      play.addEventListener("click", () => {
        inst.paused = !inst.paused;
        if (!inst.paused) inst.t0 = performance.now() - Number(scrub.value);
        else inst.tFixed = Number(scrub.value);
        play.textContent = inst.paused ? "▶" : "❚❚";
      });
      scrub.addEventListener("input", () => { inst.paused = true; inst.tFixed = Number(scrub.value); play.textContent = "▶"; });
      const meta = el("div", "meta", card);
      el("span", "oid", meta, opt.id);
      if (opt.state === "kept") el("span", "tag", meta, "Kept");
      if (opt.state === "maybe") el("span", "tag maybe", meta, "Fixed from your note");
      el("p", "label", card, opt.label || opt.type);
      if (opt.fix) el("p", "fix", card, `Your note: “${opt.fix}”`);
      const m = marks[opt.id] || (marks[opt.id] = { v: opt.state === "kept" ? "keep" : null, note: "" });
      const row = el("div", "verdicts", card);
      VERDICTS.forEach(([v, label]) => {
        const b = el("button", "v v-" + v + (m.v === v ? " on" : ""), row, label);
        b.addEventListener("click", () => {
          m.v = m.v === v ? null : v;
          row.querySelectorAll(".v").forEach((x) => x.classList.remove("on"));
          if (m.v) b.classList.add("on");
          card.classList.toggle("dropped", m.v === "drop");
          save();
        });
      });
      card.classList.toggle("dropped", m.v === "drop");
      const note = el("textarea", "note", card);
      note.placeholder = "Note (optional): slower, bigger…";
      note.rows = 2; note.value = m.note || "";
      note.addEventListener("input", () => { m.note = note.value; save(); });
    });
  });
  if (!optionCount) el("p", "empty", app, "No options on this round yet. Tell Claude what you’d like to see.");

  // ---------- overall note + copy bar ----------
  const overall = el("section", "sec overall", app);
  el("h2", null, overall, "Anything else?");
  const ov = el("textarea", "note big", overall);
  ov.placeholder = "Overall thoughts on this round (optional).";
  ov.rows = 3; ov.value = marks.__overall || "";
  ov.addEventListener("input", () => { marks.__overall = ov.value; save(); });

  const bar = el("div", "bar", document.body);
  const count = el("span", "count", bar);
  const copyBtn = el("button", "copy", bar, "Copy my picks");
  const out = el("textarea", "out", document.body);
  out.readOnly = true;

  function picksText() {
    const rowsOut = [`Not Another Edit picks · round ${round.n}`];
    (round.sections || []).forEach((sec) => (sec.options || []).forEach((opt) => {
      const m = marks[opt.id]; if (!m) return;
      const note = (m.note || "").trim().replace(/\s+/g, " ");
      const wasKept = opt.state === "kept";
      if (wasKept && m.v === "keep" && !note) return;
      if (!m.v && !note) return;
      rowsOut.push(`${opt.id} ${m.v || "note"}${note ? ": " + note : ""}`);
    }));
    if ((marks.__overall || "").trim()) rowsOut.push(`Overall: ${marks.__overall.trim().replace(/\s+/g, " ")}`);
    return rowsOut.join("\n");
  }
  function updateBar() {
    let n = 0, notes = 0;
    Object.entries(marks).forEach(([k, m]) => { if (k === "__overall") return; if (m && m.v) n++; if (m && (m.note || "").trim()) notes++; });
    count.textContent = `${n} marked · ${notes} note${notes === 1 ? "" : "s"}`;
  }
  copyBtn.addEventListener("click", async () => {
    const text = picksText();
    out.value = text;
    let ok = false;
    try { await navigator.clipboard.writeText(text); ok = true; } catch (e) { /* fall back below */ }
    if (!ok) { out.classList.add("show"); out.focus(); out.select(); try { ok = document.execCommand("copy"); } catch (e) { ok = false; } }
    copyBtn.textContent = ok ? "Copied. Paste it into Claude." : "Select the text below and copy it";
    if (!ok) out.classList.add("show");
    setTimeout(() => { copyBtn.textContent = "Copy my picks"; }, 4000);
  });
  updateBar();

  // ---------- big view ----------
  const modal = el("div", "modal", document.body);
  modal.addEventListener("click", closeBig);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeBig(); });
  function openBig(opt) {
    modal.innerHTML = "";
    const box = el("div", "modal-box", modal);
    const inst = makeStage(box, opt);
    inst.big = true;
    el("p", "modal-label", box, `${opt.id} · ${opt.label || opt.type} · tap anywhere to close`);
    modal.classList.add("show");
  }
  function closeBig() {
    if (!modal.classList.contains("show")) return;
    modal.classList.remove("show");
    for (let i = instances.length - 1; i >= 0; i--) if (instances[i].big) instances.splice(i, 1);
    modal.innerHTML = "";
  }

  window.pageReady = true;
  window.naePicksText = picksText;
  requestAnimationFrame(tick);
})();
