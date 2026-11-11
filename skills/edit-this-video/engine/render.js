/* Edit This Video: draws the whole edit's captions and graphics, one frame at a time, for the final render. */
(function () {
  const D = window.ETE;
  const brand = Object.assign({ name: "", paper: "#ffffff", ink: "#111111", accent: "#ffffff", font: "Helvetica Neue" }, D.brand || {});
  const { stack, ready } = ETE_TL.loadBrand(brand);
  const root = document.getElementById("stage");
  root.style.fontFamily = stack;
  const stage = ETE_TL.createStage(root, D.timeline.items, { brand, lines: D.lines || {}, font: stack });
  window.renderAt = (t) => stage.renderAt(t);
  ready.then(() => { stage.renderAt(-1); window.renderReady = true; });
})();
