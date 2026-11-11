/* Not Another Edit: option library (shared by Branding Pack and Edit This Video).
 * Every option is drawn on a 1080x1920 canvas and animated frame by frame from a time t (ms),
 * so the page can loop, scrub and show it big without any video files.
 * NAE_LIB[type] = { dur, build(layer, p, ctx) -> nodes, frame(t, nodes, p, ctx) }
 */
(function () {
  const W = 1080, H = 1920;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const easeOut = (k) => 1 - Math.pow(1 - k, 3);
  const backOut = (k) => { const c = 1.7; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
  const el = (tag, css, parent, text) => {
    const n = document.createElement(tag);
    if (css) n.style.cssText = css;
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };

  function color(name, ctx) {
    const b = ctx.brand;
    return ({ ink: b.ink, paper: b.paper, accent: b.accent, white: "#ffffff", black: "#000000", none: "transparent" })[name] || name;
  }

  // How something arrives, e = ms since it should appear. Returns css bits.
  function arrive(kind, e, opts) {
    opts = opts || {};
    if (e < 0) return { opacity: 0, transform: "", clip: "", chars: 0 };
    const out = { opacity: 1, transform: "", clip: "", chars: Infinity };
    if (kind === "fade") {
      out.opacity = clamp(e / 240, 0, 1);
    } else if (kind === "rise") {
      const k = easeOut(clamp(e / 340, 0, 1));
      out.opacity = clamp(e / 200, 0, 1);
      out.transform = `translateY(${(1 - k) * 46}px)`;
    } else if (kind === "pop") {
      const k = clamp(e / 300, 0, 1);
      out.opacity = clamp(e / 100, 0, 1);
      out.transform = `scale(${0.55 + 0.45 * backOut(k)})`;
    } else if (kind === "slide") {
      const k = easeOut(clamp(e / 380, 0, 1));
      out.transform = `translateX(${(1 - k) * (opts.distance || 700)}px)`;
    } else if (kind === "wipe") {
      const k = easeOut(clamp(e / 420, 0, 1));
      out.clip = `inset(0 ${(1 - k) * 100}% 0 0)`;
    } else if (kind === "type") {
      out.chars = Math.floor(e / 42);
    }
    return out;
  }
  function apply(node, a, extraTransform) {
    node.style.opacity = a.opacity;
    node.style.transform = [extraTransform || "", a.transform].join(" ").trim();
    node.style.clipPath = a.clip || "none";
    node.style.webkitClipPath = a.clip || "none";
  }

  function words(ctx) { return String(ctx.lines.captions || "This is how your captions would look on a real video").split(/\s+/).filter(Boolean); }
  function chunks(list, n) { const out = []; for (let i = 0; i < list.length; i += n) out.push(list.slice(i, i + n)); return out; }
  function longestIndex(ws) { let b = 0; ws.forEach((w, i) => { if (w.replace(/\W/g, "").length > ws[b].replace(/\W/g, "").length) b = i; }); return b; }

  // A placeholder "screenshot" so visual options have something to show until they give a real one.
  function placeholderShot(parent, ctx) {
    const box = el("div", "position:absolute;inset:0;background:#f4f4f4;display:flex;flex-direction:column;", parent);
    const bar = el("div", "height:9%;background:#e3e3e3;display:flex;align-items:center;gap:2%;padding:0 4%;", box);
    for (let i = 0; i < 3; i++) el("div", "width:3.2%;aspect-ratio:1;border-radius:50%;background:#c9c9c9;", bar);
    const body = el("div", "flex:1;padding:6% 7%;display:flex;flex-direction:column;gap:5%;", box);
    el("div", "height:9%;width:62%;background:#2b2b2b;", body);
    el("div", "height:5%;width:88%;background:#cfcfcf;", body);
    el("div", "height:5%;width:74%;background:#cfcfcf;", body);
    el("div", `height:24%;width:100%;background:${ctx.brand.accent};opacity:.9;`, body);
    el("div", "height:5%;width:80%;background:#cfcfcf;", body);
    el("div", "position:absolute;right:4%;bottom:4%;font:600 30px/1 system-ui;color:#9a9a9a;", box, "your screenshot here");
    return box;
  }
  function visualContent(parent, ctx, src) {
    src = src || ctx.visual;
    if (src) {
      const img = el("img", "position:absolute;inset:0;width:100%;height:100%;object-fit:cover;", parent);
      img.src = src;
      return img;
    }
    return placeholderShot(parent, ctx);
  }

  const LIB = {};

  /* Captions: words on screen while they talk. */
  LIB.captions = {
    params: { words: "1-4 words at a time", y: "0-1 from the top", size: "px", weight: "400-900", case: "none|upper", color: "ink|paper|accent|white|black", box: "none|ink|paper|accent", radius: "px", highlight: "none|accent", entrance: "cut|fade|rise|pop", shadow: "true|false" },
    build(layer, p, ctx) {
      const n = clamp(p.words || 3, 1, 6);
      let groups = [], times = [], ends = null, acc = 250;
      if (ctx.words && ctx.words.length) {
        // Real edit: group the spoken words, never across a pause, and time each group to the voice.
        ends = [];
        let cur = [], last = null;
        const flush = () => { if (!cur.length) return; groups.push(cur.map((x) => x[2])); times.push(cur[0][0]); ends.push(cur[cur.length - 1][1]); cur = []; };
        ctx.words.forEach((w) => { if (cur.length && (cur.length >= n || w[0] - last > 350)) flush(); cur.push(w); last = w[1]; });
        flush();
        acc = (ends[ends.length - 1] || 0);
      } else {
        const per = 300;
        groups = chunks(words(ctx), n);
        groups.forEach((g) => { times.push(acc); acc += g.length * per + 90; });
      }
      const wrap = el("div", `position:absolute;left:8%;right:8%;top:${(p.y ?? 0.64) * 100}%;display:flex;justify-content:center;transform-origin:50% 50%;`, layer);
      const pill = el("div", "display:inline-block;text-align:center;transform-origin:50% 50%;", wrap);
      return { wrap, pill, groups, times, ends, dur: acc + 500, lastShown: -1 };
    },
    frame(t, n, p, ctx) {
      let i = -1;
      for (let k = 0; k < n.times.length; k++) if (t >= n.times[k]) i = k;
      if (i >= 0 && n.ends && t > n.ends[i] + 400) i = -1; // nothing on screen during a pause
      const pill = n.pill;
      if (i !== n.lastShown) {
        pill.innerHTML = "";
        if (i >= 0) {
          const g = n.groups[i];
          const hi = p.highlight === "accent" ? longestIndex(g) : -1;
          g.forEach((w, k) => {
            const s = el("span", "", pill, (k ? " " : "") + (p.case === "upper" ? w.toUpperCase() : w));
            if (k === hi) s.style.color = color("accent", ctx);
          });
        }
        n.lastShown = i;
      }
      pill.style.font = `${p.weight || 700} ${p.size || 76}px/1.12 ${ctx.font}`;
      pill.style.color = color(p.color || "white", ctx);
      pill.style.background = p.box && p.box !== "none" ? color(p.box, ctx) : "transparent";
      pill.style.padding = p.box && p.box !== "none" ? "14px 30px" : "0";
      pill.style.borderRadius = (p.radius || 0) + "px";
      pill.style.textShadow = p.shadow && (!p.box || p.box === "none") ? "0 4px 22px rgba(0,0,0,.55)" : "none";
      apply(pill, i < 0 ? { opacity: 0 } : arrive(p.entrance || "cut", t - n.times[i]));
    },
  };

  /* Titles: the hook line at the top of the video. */
  LIB.title = {
    params: { size: "px", weight: "400-900", align: "center|left", y: "0-1", color: "ink|paper|accent|white|black", box: "none|ink|paper|accent", radius: "px", entrance: "cut|fade|rise|pop|wipe|type", case: "none|upper", italicWord: "true|false" },
    dur: 4400,
    build(layer, p, ctx) {
      const given = p.lines || ctx.lines.title;
      const lines = (given && given.length ? given : ["Your title", "goes right here"]).slice(0, 2);
      const wrap = el("div", `position:absolute;left:7%;right:7%;top:${(p.y ?? 0.13) * 100}%;display:flex;flex-direction:column;gap:12px;align-items:${p.align === "left" ? "flex-start" : "center"};text-align:${p.align === "left" ? "left" : "center"};`, layer);
      const rows = lines.map((line, i) => {
        const row = el("div", "display:inline-block;", wrap);
        const ws = line.split(" ");
        const last = ws.pop();
        const a = el("span", "", row, (p.case === "upper" ? (ws.join(" ")).toUpperCase() : ws.join(" ")) + (ws.length ? " " : ""));
        const b = el("span", "", row, p.case === "upper" ? last.toUpperCase() : last);
        if (p.italicWord && i === lines.length - 1) { b.style.fontFamily = "Georgia, 'Times New Roman', serif"; b.style.fontStyle = "italic"; b.style.fontWeight = "400"; }
        return { row, a, b, text: line };
      });
      return { wrap, rows };
    },
    frame(t, n, p, ctx) {
      const IN = p.in ?? 300, OUT = p.out ?? 3900;
      const show = t >= IN && t < OUT;
      n.rows.forEach((r, i) => {
        r.row.style.font = `${p.weight || 800} ${p.size || 96}px/1.05 ${ctx.font}`;
        r.row.style.color = color(p.color || "white", ctx);
        r.row.style.background = p.box && p.box !== "none" ? color(p.box, ctx) : "transparent";
        r.row.style.padding = p.box && p.box !== "none" ? "10px 26px" : "0";
        r.row.style.borderRadius = (p.radius || 0) + "px";
        r.row.style.textShadow = (!p.box || p.box === "none") ? "0 4px 24px rgba(0,0,0,.5)" : "none";
        const a = show ? arrive(p.entrance || "cut", t - IN - i * 140) : { opacity: 0 };
        apply(r.row, a);
        if (p.entrance === "type") {
          // Type the line out letter by letter; the last word keeps its own span (for italicWord).
          const full = r.text;
          const c = a.chars === Infinity ? full.length : clamp(a.chars, 0, full.length);
          const split = full.lastIndexOf(" ") + 1; // where the last word starts
          const up = (s) => (p.case === "upper" ? s.toUpperCase() : s);
          r.a.textContent = up(full.slice(0, Math.min(c, split)));
          r.b.textContent = up(c > split ? full.slice(split, c) : "");
        }
      });
    },
  };

  /* Key words: one important word, big, while they say it. */
  LIB.keyword = {
    params: { style: "color|underline|box|outline|plain", size: "px", weight: "400-900", y: "0-1", entrance: "cut|fade|rise|pop", case: "none|upper" },
    dur: 3800,
    build(layer, p, ctx) {
      const word = p.word || ctx.lines.hero || "Clean";
      const wrap = el("div", `position:absolute;left:0;right:0;top:${(p.y ?? 0.42) * 100}%;display:flex;justify-content:center;`, layer);
      const box = el("div", "position:relative;display:inline-block;transform-origin:50% 50%;", wrap);
      const txt = el("span", "position:relative;", box, p.case === "upper" ? word.toUpperCase() : word);
      const bar = el("div", "position:absolute;left:0;bottom:-6px;height:18px;width:100%;transform-origin:0 50%;", box);
      return { box, txt, bar };
    },
    frame(t, n, p, ctx) {
      const IN = p.in ?? 800, OUT = p.out ?? 3100;
      const show = t >= IN && t < OUT;
      const st = p.style || "color";
      n.box.style.font = `${p.weight || 900} ${p.size || 210}px/1 ${ctx.font}`;
      n.txt.style.color = st === "color" ? color("accent", ctx) : st === "box" ? color("paper", ctx) : st === "outline" ? "transparent" : "#ffffff";
      n.txt.style.webkitTextStroke = st === "outline" ? `6px ${color("white", ctx)}` : "0";
      n.box.style.background = st === "box" ? color("accent", ctx) : "transparent";
      n.box.style.padding = st === "box" ? "6px 34px 18px" : "0";
      n.txt.style.textShadow = st === "box" ? "none" : "0 6px 30px rgba(0,0,0,.5)";
      n.bar.style.background = color("accent", ctx);
      n.bar.style.display = st === "underline" ? "block" : "none";
      n.bar.style.transform = `scaleX(${easeOut(clamp((t - IN - 150) / 380, 0, 1))})`;
      apply(n.box, show ? arrive(p.entrance || "cut", t - IN) : { opacity: 0 });
    },
  };

  /* Zooms: how the camera moves in on their face. */
  LIB.zoom = {
    params: { kind: "none|punch|push", amount: "1.05-1.4", ms: "push length in ms", caption: "true|false" },
    dur: 4200,
    build(layer, p, ctx) {
      const cap = el("div", `position:absolute;left:8%;right:8%;top:64%;text-align:center;font:700 72px/1.1 ${ctx.font};color:#fff;text-shadow:0 4px 22px rgba(0,0,0,.55);`, layer);
      const ws = words(ctx);
      cap.textContent = ws.slice(0, 3).join(" ");
      return { cap, ws };
    },
    frame(t, n, p, ctx) {
      let s = 1;
      const a = p.amount || 1.15;
      if (p.kind === "punch") s = t >= 1500 && t < 3600 ? a : 1;
      else if (p.kind === "push") { const k = clamp((t - 1200) / (p.ms || 1400), 0, 1); s = t < 3800 ? 1 + (a - 1) * easeOut(k) : 1; }
      if (ctx.bg) ctx.bg.style.transform = `scale(${s})`;
      n.cap.textContent = (t < 1500 ? n.ws.slice(0, 3) : n.ws.slice(3, 6)).join(" ");
      n.cap.style.display = p.caption === false ? "none" : "block";
    },
  };

  /* Visuals: a screenshot, logo or photo on screen while they talk. */
  LIB.visual = {
    params: { layout: "card|split|full|corner", radius: "px", shadow: "true|false", border: "none|ink|paper|accent|white", entrance: "cut|fade|rise|slide|pop", caption: "true|false" },
    dur: 4200,
    build(layer, p, ctx) {
      const L = p.layout || "card";
      const geo = {
        card: "left:12%;right:12%;top:15%;height:36%;",
        split: "left:0;right:0;top:0;height:50%;",
        full: "left:0;right:0;top:0;bottom:0;",
        corner: "right:6%;top:9%;width:40%;height:17%;",
      }[L];
      const frameEl = el("div", `position:absolute;${geo}overflow:hidden;transform-origin:50% 50%;`, layer);
      visualContent(frameEl, ctx, p.src);
      const cap = el("div", `position:absolute;left:8%;right:8%;top:${L === "split" ? 70 : 64}%;text-align:center;font:700 72px/1.1 ${ctx.font};color:#fff;text-shadow:0 4px 22px rgba(0,0,0,.55);`, layer, words(ctx).slice(0, 3).join(" "));
      return { frameEl, cap, L };
    },
    frame(t, n, p, ctx) {
      const IN = p.in ?? 700, OUT = p.out ?? 3500;
      const show = t >= IN && t < OUT;
      const f = n.frameEl;
      f.style.borderRadius = (p.radius || 0) + "px";
      f.style.boxShadow = p.shadow ? "0 30px 80px rgba(0,0,0,.45), 0 8px 24px rgba(0,0,0,.3)" : "none";
      f.style.outline = p.border && p.border !== "none" ? `6px solid ${color(p.border, ctx)}` : "none";
      f.style.outlineOffset = "-6px";
      apply(f, show ? arrive(p.entrance || "cut", t - IN, { distance: 1100 }) : { opacity: 0 });
      n.cap.style.display = p.caption === false || n.L === "full" || ctx.edit ? "none" : "block";
    },
  };

  /* Labels: a name tag or small label on screen. */
  LIB.label = {
    params: { style: "bar|box|plain|tiny", position: "bottom-left|top-left", radius: "px", entrance: "cut|fade|rise|slide|wipe|pop" },
    dur: 4200,
    build(layer, p, ctx) {
      const [name, role] = String(p.text || ctx.lines.label || "Your name · What you do").split(/\s*·\s*/);
      const pos = p.position === "top-left" ? "top:10%;" : "top:73%;";
      const wrap = el("div", `position:absolute;left:7%;${pos}display:flex;align-items:stretch;gap:20px;transform-origin:0 50%;`, layer);
      const bar = el("div", "width:12px;", wrap);
      const box = el("div", "display:flex;flex-direction:column;gap:8px;", wrap);
      const a = el("div", "", box, name);
      const b = el("div", "", box, role || "");
      return { wrap, bar, box, a, b };
    },
    frame(t, n, p, ctx) {
      const st = p.style || "bar";
      const IN = p.in ?? 600, OUT = p.out ?? 3600;
      const show = t >= IN && t < OUT;
      n.bar.style.display = st === "bar" ? "block" : "none";
      n.bar.style.background = color("accent", ctx);
      n.box.style.background = st === "box" ? color("ink", ctx) : st === "tiny" ? "rgba(255,255,255,.92)" : "transparent";
      n.box.style.padding = st === "box" ? "22px 30px" : st === "tiny" ? "12px 18px" : "0";
      n.box.style.borderRadius = (p.radius || 0) + "px";
      n.a.style.font = st === "tiny" ? `700 26px/1 ${ctx.font}` : `800 58px/1.05 ${ctx.font}`;
      n.a.style.letterSpacing = st === "tiny" ? "0.2em" : "0";
      n.a.style.textTransform = st === "tiny" ? "uppercase" : "none";
      n.a.style.color = st === "box" ? color("paper", ctx) : st === "tiny" ? "#555" : "#fff";
      n.b.style.font = `500 36px/1.1 ${ctx.font}`;
      n.b.style.color = st === "box" ? color("paper", ctx) : "#fff";
      n.b.style.opacity = st === "box" ? ".8" : ".9";
      n.b.style.display = st === "tiny" ? "none" : "block";
      n.wrap.style.textShadow = st === "plain" || st === "bar" ? "0 4px 20px rgba(0,0,0,.55)" : "none";
      apply(n.wrap, show ? arrive(p.entrance || "cut", t - IN, { distance: -500 }) : { opacity: 0 });
    },
  };

  /* Transitions: how one shot changes to the next. */
  LIB.transition = {
    params: { kind: "cut|fade|slide|whip|flash", ms: "length in ms", flash: "white|accent|black" },
    dur: 4400,
    build(layer, p, ctx) {
      const b = el("div", "position:absolute;inset:0;overflow:hidden;", layer);
      visualContent(b, ctx);
      const flash = el("div", "position:absolute;inset:0;pointer-events:none;", layer);
      return { b, flash };
    },
    frame(t, n, p, ctx) {
      const ms = p.ms || 260, k = p.kind || "cut";
      const inAt = 1500, outAt = 3300;
      let o = 0, x = 0, blur = 0, fo = 0;
      const prog = (start) => clamp((t - start) / ms, 0, 1);
      const on = t >= inAt && t < outAt;
      if (k === "cut") o = on ? 1 : 0;
      if (k === "fade") o = t < outAt ? prog(inAt) : 1 - prog(outAt);
      if (k === "slide" || k === "whip") {
        if (t < outAt) { const e = easeOut(prog(inAt)); o = t >= inAt ? 1 : 0; x = (1 - e) * 1080; blur = k === "whip" ? (1 - e) * 40 : 0; }
        else { const e = easeOut(prog(outAt)); o = 1; x = -e * 1080; blur = k === "whip" ? Math.sin(e * Math.PI) * 40 : 0; }
      }
      if (k === "flash") {
        o = on ? 1 : 0;
        const d1 = Math.abs(t - inAt), d2 = Math.abs(t - outAt);
        fo = clamp(1 - Math.min(d1, d2) / (ms / 2), 0, 1);
      }
      n.b.style.opacity = o;
      n.b.style.transform = `translateX(${x}px)`;
      n.b.style.filter = blur ? `blur(${blur}px)` : "none";
      n.flash.style.background = color(p.flash || "white", ctx);
      n.flash.style.opacity = fo;
    },
  };

  window.NAE_LIB = LIB;
  window.NAE_W = W; window.NAE_H = H;
})();
