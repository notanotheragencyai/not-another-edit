/* Edit This Video: timeline.
 * Puts style options (from the Not Another Edit library) on an edit's timeline, in seconds, and draws any
 * moment of it. The storyboard page and the final render both use this, so what they approve is what renders.
 */
(function () {
  const LIB = window.NAE_LIB;
  const W = window.NAE_W || 1080, H = window.NAE_H || 1920;

  function colorOf(name, brand) {
    return ({ ink: brand.ink, paper: brand.paper, accent: brand.accent, white: "#ffffff", black: "#000000" })[name] || name || "#ffffff";
  }

  // Load their font, then resolve. Returns the CSS font stack to use everywhere.
  function loadBrand(brand) {
    const stack = `'${brand.font}', 'Helvetica Neue', Helvetica, Arial, sans-serif`;
    const head = document.head;
    if (brand.fontFile) {
      const s = document.createElement("style");
      s.textContent = `@font-face{font-family:'${brand.font}';src:url('${brand.fontFile}');font-weight:100 900;font-display:block;}`;
      head.appendChild(s);
    } else if (brand.fontSource === "google" && brand.font) {
      const l = document.createElement("link");
      l.rel = "stylesheet";
      l.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(brand.font)}:wght@400;500;600;700;800;900&display=block`;
      head.appendChild(l);
    }
    const loads = [400, 500, 600, 700, 800, 900].map((w) => document.fonts.load(`${w} 40px '${brand.font}'`).catch(() => null));
    const ready = Promise.race([Promise.all(loads), new Promise((r) => setTimeout(r, 8000))]).then(() => document.fonts.ready);
    return { stack, ready };
  }

  // items: [{type, params, at, dur, words?}] (seconds). base: {brand, lines, font}
  function createStage(root, items, base) {
    const parts = items.map((it) => {
      const layer = document.createElement("div");
      layer.style.cssText = "position:absolute;inset:0;display:none;";
      root.appendChild(layer);
      if (it.type === "flash" || it.type === "dip") {
        layer.style.background = colorOf((it.params || {}).color, base.brand);
        return { it, layer, fx: true };
      }
      const def = LIB[it.type];
      if (!def) throw new Error(`Missing option type "${it.type}"`);
      const p = Object.assign({}, it.params, { in: 0, out: Math.round(it.dur * 1000) });
      const ctx = Object.assign({}, base, { edit: true, words: it.words || null });
      const nodes = def.build(layer, p, ctx) || {};
      return { it, layer, def, p, ctx, nodes };
    });
    function renderAt(t) {
      let any = false;
      for (const x of parts) {
        const local = (t - x.it.at) * 1000, len = x.it.dur * 1000;
        const on = t >= 0 && local >= 0 && local <= len + 40;
        x.layer.style.display = on ? "block" : "none";
        if (!on) continue;
        any = true;
        if (x.fx) {
          const half = len / 2;
          x.layer.style.opacity = String(Math.max(0, 1 - Math.abs(local - half) / half));
        } else {
          x.def.frame(local, x.nodes, x.p, x.ctx);
        }
      }
      return any;
    }
    return { renderAt };
  }

  // How far the shot is zoomed in at time t.
  function zoomAt(zooms, t) {
    for (const z of zooms || []) {
      if (t >= z.at && t < z.at + z.dur) {
        if (z.kind === "punch") return z.amount;
        const k = Math.min(1, Math.max(0, (t - z.at) / ((z.ms || 1400) / 1000)));
        return 1 + (z.amount - 1) * (1 - Math.pow(1 - k, 3));
      }
    }
    return 1;
  }

  window.ETE_TL = { createStage, zoomAt, loadBrand, W, H };
})();
