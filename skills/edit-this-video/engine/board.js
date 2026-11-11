/* Edit This Video: the storyboard page.
 * Every beat plays from the rough cut with its captions and graphics drawn by the same code as the final
 * render. They approve or change each beat (and pick A/B/C where there's a choice), then copy their review
 * and paste it into Claude. Nothing is uploaded; nothing renders until they approve.
 */
(function () {
  const D = window.ETE;
  const TL = window.ETE_TL;
  const W = TL.W, H = TL.H;
  const brand = Object.assign({ name: "", paper: "#ffffff", ink: "#111111", accent: "#ffffff", font: "Helvetica Neue" }, D.brand || {});
  const { stack } = TL.loadBrand(brand);
  const base = { brand, lines: D.lines || {}, font: stack };
  const $ = (s, r) => (r || document).querySelector(s);
  const el = (tag, cls, parent, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  const fmt = (t) => `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, "0")}`;

  // ---------- marks ----------
  const KEY = `ete:${D.title}:round:${D.round}`;
  let marks = {};
  try { marks = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { marks = {}; }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(marks)); } catch (e) { /* private mode */ } updateBar(); };

  // ---------- header ----------
  const app = $("#app");
  const head = el("header", "head", app);
  el("div", "wordmark", head, "Edit This Video");
  el("h1", null, head, `Storyboard · round ${D.round}`);
  el("p", "sub", head, `${D.title} · ${fmt(D.duration)} · ${D.beats.length} beats`);
  el("p", "how", head, "Each card plays one beat of your video with its captions and graphics. Tap a card to watch it big with sound. Approve it, or press Change and say what you want. Where there are options (A, B, C), pick one. Then press Copy my review and paste it into Claude. Nothing gets built until you approve.");
  const all = el("button", "playall", head, "▶  Watch the whole thing");
  all.addEventListener("click", () => openBig(null));

  // ---------- previews ----------
  const players = [];
  function makePlayer(parent, start, end, variant, opts) {
    opts = opts || {};
    const box = el("div", "stage", parent);
    const canvas = el("div", "canvas", box);
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    canvas.style.fontFamily = stack;
    const bg = el("div", "bg", canvas);
    const v = el("video", null, bg);
    v.src = D.proxy; v.muted = !opts.sound; v.playsInline = true; v.preload = "auto";
    v.setAttribute("playsinline", "");
    if (!opts.sound) v.setAttribute("muted", "");
    const layer = el("div", "layer", canvas);
    const P = { box, canvas, bg, v, layer, start, end, variant, visible: true, stage: null, error: null };
    try { P.stage = TL.createStage(layer, variant.items, base); }
    catch (e) { P.error = String(e.message || e); el("div", "err", box, P.error); }
    const fit = () => { canvas.style.transform = `scale(${box.clientWidth / W})`; };
    new ResizeObserver(fit).observe(box); fit();
    v.addEventListener("loadedmetadata", () => { v.currentTime = start; v.play().catch(() => {}); });
    io.observe(box);
    box.__p = P;
    players.push(P);
    return P;
  }
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    const P = e.target.__p; if (!P) return;
    P.visible = e.isIntersecting;
    if (P.visible) P.v.play().catch(() => {}); else P.v.pause();
  }), { rootMargin: "100px" });

  function tick() {
    for (const P of players) {
      if (!P.visible || P.error) continue;
      const t = P.v.currentTime;
      if (t >= P.end - 0.02 || t < P.start - 0.25) { P.v.currentTime = P.start; continue; }
      P.stage.renderAt(t);
      P.bg.style.transform = `scale(${TL.zoomAt(P.variant.zooms, t)})`;
    }
    requestAnimationFrame(tick);
  }

  // ---------- beats ----------
  const grid = el("section", "grid", app);
  D.beats.forEach((b) => {
    const m = marks[b.id] || (marks[b.id] = { v: b.status === "approved" ? "approve" : null, note: "", pick: b.pick });
    const card = el("article", "card" + (b.status === "approved" ? " was-ok" : ""), grid);
    const top = el("div", "meta", card);
    el("span", "bid", top, b.id);
    el("span", "time", top, `${fmt(b.start)}–${fmt(b.end)}`);
    if (b.status === "approved") el("span", "tag", top, "Approved");
    if (b.status === "change") el("span", "tag change", top, "Changed from your note");
    const holder = el("div", "holder", card);
    let P = null;
    const show = (key) => {
      holder.innerHTML = "";
      if (P) { const i = players.indexOf(P); if (i >= 0) players.splice(i, 1); }
      P = makePlayer(holder, b.start, b.end, b.variants[key] || b.variants["-"]);
      P.box.addEventListener("click", () => openBig(b, key));
      list(key);
    };
    if (b.options.length) {
      const tabs = el("div", "tabs", card);
      b.options.forEach((k) => {
        const t = el("button", "tab" + (m.pick === k ? " on" : ""), tabs, k);
        t.title = b.variants[k].label || "";
        t.addEventListener("click", () => {
          m.pick = k; save();
          tabs.querySelectorAll(".tab").forEach((x) => x.classList.toggle("on", x === t));
          show(k);
        });
      });
      tabs.after(holder);
    }
    el("p", "say", card, b.say ? `“${b.say}”` : "");
    const onscreen = el("ul", "onscreen", card);
    function list(key) {
      onscreen.innerHTML = "";
      const v = b.variants[key] || b.variants["-"];
      if (v.label) el("li", "optlabel", onscreen, `Option ${key}: ${v.label}`);
      const seen = new Set();
      v.items.filter((it) => it.beat === b.id || it.beat === "*").forEach((it) => { const s = it.label || it.type; if (!seen.has(s)) { seen.add(s); el("li", null, onscreen, s); } });
      v.zooms.filter((z) => z.beat === b.id).forEach((z) => el("li", null, onscreen, z.kind === "push" ? "slow push in" : `punch in (${z.amount}x)`));
    }
    if (b.note) el("p", "fix", card, `Your note: “${b.note}”`);
    const row = el("div", "verdicts", card);
    [["approve", "Approve"], ["change", "Change"]].forEach(([v, label]) => {
      const btn = el("button", "v v-" + v + (m.v === v ? " on" : ""), row, label);
      btn.addEventListener("click", () => {
        m.v = m.v === v ? null : v;
        row.querySelectorAll(".v").forEach((x) => x.classList.remove("on"));
        if (m.v) btn.classList.add("on");
        note.classList.toggle("need", m.v === "change");
        save();
      });
    });
    const note = el("textarea", "note" + (m.v === "change" ? " need" : ""), card);
    note.placeholder = "What should change? (e.g. bigger title, no zoom here)";
    note.rows = 2; note.value = m.note || "";
    note.addEventListener("input", () => { m.note = note.value; save(); });
    show(m.pick || b.pick);
  });

  const overall = el("section", "overall", app);
  el("h2", null, overall, "Anything else?");
  const ov = el("textarea", "note big", overall);
  ov.placeholder = "Overall thoughts (optional): pacing, music, anything.";
  ov.rows = 3; ov.value = marks.__overall || "";
  ov.addEventListener("input", () => { marks.__overall = ov.value; save(); });

  // ---------- copy bar ----------
  const bar = el("div", "bar", document.body);
  const count = el("span", "count", bar);
  const okAll = el("button", "ghost", bar, "Approve all");
  const copyBtn = el("button", "copy", bar, "Copy my review");
  const out = el("textarea", "out", document.body);
  out.readOnly = true;
  okAll.addEventListener("click", () => {
    D.beats.forEach((b) => { const m = marks[b.id]; if (m && m.v !== "change") m.v = "approve"; });
    document.querySelectorAll(".card").forEach((c) => {
      const btns = c.querySelectorAll(".v");
      if (!btns[1].classList.contains("on")) { btns[0].classList.add("on"); }
    });
    save();
  });
  function reviewText() {
    const rows = [`Edit This Video storyboard · round ${D.round}`];
    D.beats.forEach((b) => {
      const m = marks[b.id]; if (!m) return;
      const note = (m.note || "").trim().replace(/\s+/g, " ");
      const picked = b.options.length && m.pick && m.pick !== b.pick;
      if (m.v === "change") rows.push(`${b.id} ${picked ? "pick " + m.pick : "change"}: ${note || "(no note)"}`);
      else if (m.v === "approve") rows.push(b.options.length ? `${b.id} pick ${m.pick}` + (note ? `: ${note}` : "") : `${b.id} approve` + (note ? `: ${note}` : ""));
      else if (note) rows.push(`${b.id} change: ${note}`);
    });
    if ((marks.__overall || "").trim()) rows.push(`Overall: ${marks.__overall.trim().replace(/\s+/g, " ")}`);
    return rows.join("\n");
  }
  function updateBar() {
    const n = D.beats.filter((b) => marks[b.id] && marks[b.id].v === "approve").length;
    const c = D.beats.filter((b) => marks[b.id] && marks[b.id].v === "change").length;
    count.textContent = `${n} of ${D.beats.length} approved · ${c} to change`;
  }
  copyBtn.addEventListener("click", async () => {
    const text = reviewText();
    out.value = text;
    let ok = false;
    try { await navigator.clipboard.writeText(text); ok = true; } catch (e) { /* fall back */ }
    if (!ok) { out.classList.add("show"); out.focus(); out.select(); try { ok = document.execCommand("copy"); } catch (e) { ok = false; } }
    copyBtn.textContent = ok ? "Copied. Paste it into Claude." : "Select the text below and copy it";
    if (!ok) out.classList.add("show");
    setTimeout(() => { copyBtn.textContent = "Copy my review"; }, 4000);
  });
  updateBar();

  // ---------- big view (with sound) ----------
  const modal = el("div", "modal", document.body);
  let bigP = null;
  modal.addEventListener("click", (e) => { if (e.target === modal) closeBig(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeBig(); });
  function openBig(b, key) {
    modal.innerHTML = "";
    const box = el("div", "modal-box", modal);
    const variant = b ? (b.variants[key] || b.variants["-"]) : { items: D.timeline.items, zooms: D.timeline.zooms };
    bigP = makePlayer(box, b ? b.start : 0, b ? b.end : D.duration, variant, { sound: true });
    bigP.box.addEventListener("click", closeBig);
    el("p", "modal-label", box, b ? `${b.id} · tap the video or press Esc to close` : "The whole video · tap or press Esc to close");
    modal.classList.add("show");
    players.forEach((P) => { if (P !== bigP) P.v.pause(); });
  }
  function closeBig() {
    if (!modal.classList.contains("show")) return;
    modal.classList.remove("show");
    if (bigP) { bigP.v.pause(); const i = players.indexOf(bigP); if (i >= 0) players.splice(i, 1); bigP = null; }
    modal.innerHTML = "";
    players.forEach((P) => { if (P.visible) P.v.play().catch(() => {}); });
  }

  window.pageReady = true;
  window.eteReviewText = reviewText;
  requestAnimationFrame(tick);
})();
