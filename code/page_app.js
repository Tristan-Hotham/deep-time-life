/* Life on the moving map: page script. R (results.json) and SITE (site.json) are embedded by 05_build_site.py;
   coastlines (data/coast/<age>.json), fossil frames (data/frames/<age>.json), names and places are loaded as needed. */
const fmt = n => n == null || n === "" ? "n/a" : Math.round(n).toLocaleString("en-GB");
const f1 = n => (Math.round(n * 10) / 10).toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const tip = document.getElementById("tip");
function showTip(h, x, y) { tip.innerHTML = h; tip.style.display = "block"; const w = tip.offsetWidth; x = Math.max(w / 2 + 8, Math.min(innerWidth - w / 2 - 8, x)); tip.style.left = x + scrollX + "px"; tip.style.top = y + scrollY + "px"; }
function hideTip() { tip.style.display = "none"; }
document.addEventListener("scroll", hideTip, { passive: true });
const NS = "http://www.w3.org/2000/svg";
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
const lbl = (svg, x, y, s, cls = "lab", anchor = "start") => { const t = el("text", { x, y, class: cls, "text-anchor": anchor }, svg); t.textContent = s; return t; };
const redraws = [];
function resp(box, render) { let last = 0; const go = force => { const w = Math.max(280, Math.round(box.clientWidth)); if (!force && Math.abs(w - last) < 4) return; last = w; box.innerHTML = ""; render(w, w < 560); }; new ResizeObserver(() => go()).observe(box); go(); redraws.push(() => go(true)); }
const isDark = () => { const r = document.documentElement; return r.dataset.theme ? r.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches; };
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const ma = a => a === 0 ? "Today" : `${fmt(a)} million years ago`;
const maShort = a => a === 0 ? "Today" : `${fmt(a)} Ma`;

/* ---------- groups, periods ---------- */
const GROUPS = SITE.groups.map(([k, short, name, c], i) => ({ k, short, name, c, i }));
const GI = {}; GROUPS.forEach(g => GI[g.k] = g);
const ORDER = SITE.order.map(k => GI[k]);
const PERIODS = SITE.periods.map(([name, ab, old, young, c]) => ({ name, ab, old, young, c }));
const ERAS = SITE.eras.map(([name, old, young, c]) => ({ name, old, young, c }));
const EXT = SITE.ext.map(([k, name, age]) => ({ k, name, age }));
const EXTAGE = new Set(EXT.map(e => e.age));
const periodOf = a => PERIODS.find(p => a <= p.old && a >= p.young) || (a > 538.8 ? { name: "Ediacaran", ab: "E" } : PERIODS[PERIODS.length - 1]);
const eraOf = a => ERAS.find(p => a <= p.old && a >= p.young) || { name: "Proterozoic" };
const AGES = SITE.ages.slice().sort((a, b) => a - b);
const AGESD = AGES.slice().reverse();
const nearestAge = a => AGES.reduce((b, x) => Math.abs(x - a) < Math.abs(b - a) || (Math.abs(x - a) === Math.abs(b - a) && x % 10 === 0) ? x : b, AGES[0]);
const PAN = {}; SITE.pangaea.forEach(([a, p]) => PAN[a] = p);
const EXTNOTE = { eor: "Ice sheets spread over Gondwana, sea levels fell and the warm shallow seas emptied.", lde: "A long series of crises in the seas; the armoured fish dwindled and were gone soon after.",
  epe: "The Great Dying: vast eruptions in Siberia heated the planet and stripped the seas of oxygen. The last trilobites vanish.", etr: "Volcanism as Pangaea began to split; it cleared the way for the dinosaurs.",
  ecr: "An asteroid struck Chicxulub in Mexico: the non-bird dinosaurs, pterosaurs, plesiosaurs, mosasaurs and ammonites all vanish." };

/* hero mark: a tiny globe with dots */
(function () {
  const g = document.getElementById("heroMark");
  el("circle", { cx: 60, cy: 60, r: 52, fill: "var(--sea)", stroke: "currentColor", "stroke-width": 3 }, g);
  el("path", { d: "M34 30 C48 20 70 22 82 34 C92 44 96 62 88 76 C80 90 60 96 46 88 C36 82 40 70 34 62 C28 54 22 40 34 30Z", fill: "var(--land)", stroke: "var(--landedge)", "stroke-width": 2 }, g);
  [["the", 52, 46, 6], ["sau", 66, 60, 5], ["orn", 58, 72, 5], ["amm", 86, 30, 4], ["tri", 26, 70, 4], ["mam", 74, 80, 4]].forEach(([k, x, y, r]) => el("circle", { cx: x, cy: y, r, fill: GI[k].c, stroke: "#fff", "stroke-width": 1.2 }, g));
})();

/* ---------- state ---------- */
const LYDEF = { pos: "ancient", land: true, grat: true, lat: true, labels: true, size: 1, on: GROUPS.map(g => g.k) };
const LY = JSON.parse(JSON.stringify(LYDEF));
try { const s = JSON.parse(localStorage.getItem("dtl_layers") || "{}"); Object.assign(LY, s); if (!Array.isArray(LY.on)) LY.on = LYDEF.on.slice(); } catch (e) {}
const saveLY = () => { try { localStorage.setItem("dtl_layers", JSON.stringify(LY)); } catch (e) {} };
const ON = () => new Set(LY.on);
const S = { age: 66, sel: null, nid: null, playing: false, morph: 0 };
const cache = { coast: {}, frame: {} };
let NAMES = null, PLACES = null, namesP = null;
function loadNames() { if (!namesP) namesP = Promise.all([fetch("data/names.json").then(r => r.json()), fetch("data/places.json").then(r => r.json())]).then(([n, p]) => { NAMES = n; PLACES = p; }); return namesP; }
function getCoast(a) { if (!cache.coast[a]) cache.coast[a] = fetch(`data/coast/${a}.json`).then(r => r.json()).then(f => { rewind(f); return f; }); return cache.coast[a]; }
function getFrame(a) { if (!cache.frame[a]) cache.frame[a] = fetch(`data/frames/${a}.json`).then(r => r.json()); return cache.frame[a]; }
/* d3-geo wants clockwise outer rings; if a ring covers more than half the sphere it is the wrong way round */
function rewind(f) { const g = f.geometry; g.coordinates = g.coordinates.map(poly => { const t = { type: "Polygon", coordinates: poly }; if (d3.geoArea(t) > 2 * Math.PI) return poly.map(r => r.slice().reverse()); return poly; }); }

/* ---------- the map ---------- */
const box = document.getElementById("mapbox"), cv = document.getElementById("mapc"), ctx = cv.getContext("2d");
const proj = d3.geoEqualEarth(); const gpath = d3.geoPath(proj);
let W = 0, H = 0, DPR = 1, T = d3.zoomIdentity;
const P2 = new Map();   // cached Path2D per coast age (cleared on resize)
const GRAT = d3.geoGraticule().step([30, 30])();
let gratP = null, sphereP = null, latP = null;
const LATLINES = { type: "MultiLineString", coordinates: [0, 23.44, -23.44, 66.56, -66.56].map(l => d3.range(-180, 181, 2).map(x => [x, l])) };
let CUR = { age: null, coast: null, frame: null }, PREV = null, NOW = null;   // NOW: coast for 'today' positions
let fade = 1, fadeT = null;
function resize() {
  const r = box.getBoundingClientRect(); W = Math.max(200, r.width); H = Math.max(150, r.height); DPR = Math.min(2, devicePixelRatio || 1);
  cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
  const padTop = W < 600 ? 50 : 70, padBot = W < 600 ? 50 : 56;
  proj.fitExtent([[8, padTop], [W - 8, H - padBot]], { type: "Sphere" });
  P2.clear(); gratP = new Path2D(gpath(GRAT)); sphereP = new Path2D(gpath({ type: "Sphere" })); latP = new Path2D(gpath(LATLINES));
  zoom.translateExtent([[-W * .1, -H * .1], [W * 1.1, H * 1.1]]).extent([[0, 0], [W, H]]);
  if (CUR.frame) project(CUR.frame); if (PREV && PREV.frame) project(PREV.frame);
  draw();
}
function landPath(a, coast) { if (!P2.has(a)) P2.set(a, new Path2D(gpath(coast))); return P2.get(a); }
const pkey = () => proj.scale() + "," + proj.translate().join(",");
function project(fr) { fr.px = fr.cells.map(c => proj([c[1], c[2]])); fr.pt = fr.cells.map(c => proj([c[5], c[6]])); fr.proj = pkey(); }
const rad = n => LY.size * (1.9 + 1.25 * Math.log10(1 + n)) * (W < 600 ? .8 : 1) * Math.pow(T.k, .3);
function drawLand(coast, a, alpha) {
  if (!coast || !LY.land) return;
  ctx.globalAlpha = alpha; const p = landPath(a, coast);
  ctx.fillStyle = css("--land"); ctx.fill(p); ctx.strokeStyle = css("--landedge"); ctx.lineWidth = .8 / T.k; ctx.stroke(p); ctx.globalAlpha = 1;
}
function dotsOf(fr, alpha, morph) {
  if (!fr || !fr.px) return [];
  const on = ON(), out = [];
  for (let i = 0; i < fr.cells.length; i++) {
    const c = fr.cells[i]; if (!on.has(GROUPS[c[0]].k)) continue;
    const a = fr.px[i], b = fr.pt[i]; if (!a || !b) continue;
    const x0 = a[0] + (b[0] - a[0]) * morph, y0 = a[1] + (b[1] - a[1]) * morph;
    out.push({ i, c, x: T.applyX(x0), y: T.applyY(y0), r: rad(c[3]), alpha });
  }
  return out;
}
let DRAWN = [];
function draw() {
  if (!W) return;
  const dark = isDark();
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = css("--bg"); ctx.fillRect(0, 0, W, H);
  ctx.setTransform(DPR * T.k, 0, 0, DPR * T.k, DPR * T.x, DPR * T.y);
  ctx.fillStyle = css("--sea"); ctx.fill(sphereP);
  if (LY.grat) { ctx.strokeStyle = css("--grat"); ctx.lineWidth = .6 / T.k; ctx.stroke(gratP); }
  const m = S.morph;   // 0 = ancient positions, 1 = today's positions
  if (m > 0) {
    if (CUR.coast) drawLand(CUR.coast, CUR.age, 1 - m);
    if (NOW) drawLand(NOW, 0, m);
  } else {
    if (PREV && PREV.coast && fade < 1) drawLand(PREV.coast, PREV.age, 1 - fade);
    if (CUR.coast) drawLand(CUR.coast, CUR.age, PREV && fade < 1 ? fade : 1);
  }
  if (LY.lat) { ctx.setLineDash([4 / T.k, 4 / T.k]); ctx.strokeStyle = dark ? "rgba(140,170,185,.55)" : "rgba(70,110,130,.45)"; ctx.lineWidth = .8 / T.k; ctx.stroke(latP); ctx.setLineDash([]); }
  ctx.strokeStyle = css("--seaedge"); ctx.lineWidth = 1 / T.k; ctx.stroke(sphereP);
  // dots, in screen space
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  const mp = m;
  let ds = [];
  if (PREV && PREV.frame && fade < 1) ds = ds.concat(dotsOf(PREV.frame, 1 - fade, mp));
  ds = ds.concat(dotsOf(CUR.frame, PREV && fade < 1 ? fade : 1, mp));
  const hl = S.nid;
  const edge = dark ? "rgba(20,22,25,.85)" : "rgba(255,255,255,.9)";
  for (const d of ds) {
    ctx.globalAlpha = d.alpha * (hl != null && !d.c[10].includes(hl) ? .28 : .92);
    ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, 2 * Math.PI); ctx.fillStyle = GROUPS[d.c[0]].c; ctx.fill();
    ctx.lineWidth = .7; ctx.strokeStyle = edge; ctx.stroke();
  }
  ctx.globalAlpha = 1;
  if (hl != null) for (const d of ds) if (d.c[10].includes(hl)) { ctx.beginPath(); ctx.arc(d.x, d.y, d.r + 3.5, 0, 2 * Math.PI); ctx.lineWidth = 2; ctx.strokeStyle = css("--fg"); ctx.stroke(); }
  if (S.sel && CUR.frame) { const d = ds.find(d => d.c === S.sel); if (d) { ctx.beginPath(); ctx.arc(d.x, d.y, d.r + 4, 0, 2 * Math.PI); ctx.lineWidth = 2.5; ctx.strokeStyle = css("--hot"); ctx.stroke(); } }
  DRAWN = ds.filter(d => d.alpha > .5);
  // Pangaea label, on the sea when possible
  if (LY.labels && m === 0 && CUR.age != null && PAN[CUR.age] >= 80 && fade >= 1) {
    const lp = proj(SITE.labels[CUR.age]);
    if (lp) { const x = T.applyX(lp[0]), y = T.applyY(lp[1]); ctx.font = `800 ${W < 600 ? 15 : 22}px Fraunces, Georgia, serif`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.lineWidth = 5; ctx.strokeStyle = dark ? "rgba(20,22,25,.8)" : "rgba(255,253,248,.85)"; ctx.strokeText("PANGAEA", x, y); ctx.fillStyle = css("--fg"); ctx.globalAlpha = .82; ctx.fillText("PANGAEA", x, y); ctx.globalAlpha = 1; }
  }
}
const zoom = d3.zoom().scaleExtent([1, 10]).on("zoom", e => { T = e.transform; closePop(false); draw(); });
d3.select(cv).call(zoom).on("dblclick.zoom", null);
document.getElementById("zin").onclick = () => d3.select(cv).transition().duration(250).call(zoom.scaleBy, 1.6);
document.getElementById("zout").onclick = () => d3.select(cv).transition().duration(250).call(zoom.scaleBy, 1 / 1.6);
new ResizeObserver(() => resize()).observe(box);

/* ---------- loading frames, crossfade ---------- */
let reqId = 0;
async function setAge(a, opts = {}) {
  a = nearestAge(a); const id = ++reqId;
  S.age = a; updateControls();
  const [coast, frame] = await Promise.all([getCoast(a), getFrame(a)]);
  if (id !== reqId) return;
  if (!frame.px || frame.proj !== pkey()) project(frame);
  if (CUR.age !== a) { PREV = CUR.age != null ? { ...CUR } : null; CUR = { age: a, coast, frame }; startFade(opts.instant ? 0 : (S.playing ? 380 : 300)); }
  if (S.sel && !frame.cells.includes(S.sel)) { S.sel = null; closePop(false); }
  side(); legend(); draw();
  // prefetch neighbours
  const k = AGESD.indexOf(a); [k + 1, k + 2, k - 1].forEach(j => { if (AGESD[j] != null) { getCoast(AGESD[j]); getFrame(AGESD[j]); } });
}
function startFade(ms) {
  if (fadeT) cancelAnimationFrame(fadeT);
  if (!ms || !PREV) { fade = 1; PREV = null; draw(); return; }
  const t0 = performance.now(); fade = 0;
  const step = t => { fade = Math.min(1, (t - t0) / ms); draw(); if (fade < 1) fadeT = requestAnimationFrame(step); else { PREV = null; draw(); } };
  fadeT = requestAnimationFrame(step);
}
function morphTo(today) {
  LY.pos = today ? "today" : "ancient"; saveLY(); syncPanel();
  const go = () => { const from = S.morph, to = today ? 1 : 0, t0 = performance.now(), ms = 900;
    const step = t => { const p = Math.min(1, (t - t0) / ms); S.morph = from + (to - from) * d3.easeCubicInOut(p); draw(); if (p < 1) requestAnimationFrame(step); else side(); };
    requestAnimationFrame(step); };
  if (today && !NOW) getCoast(0).then(c => { NOW = c; go(); }); else go();
}

/* ---------- controls: slider, play, jump, timeline ---------- */
const slider = document.getElementById("slider"), ageLab = document.getElementById("ageLab"), playB = document.getElementById("play");
slider.addEventListener("input", () => { stop(); setAge(540 - +slider.value); });
function updateControls() {
  slider.value = 540 - S.age; ageLab.textContent = maShort(S.age);
  const p = periodOf(S.age), e = EXT.find(x => x.age === S.age), fr = SITE.frames[S.age];
  document.getElementById("mapnote").innerHTML = `<b>${S.age === 0 ? "Today" : fmt(S.age) + " million years ago"}</b>${esc(S.age === 0 ? "Quaternary" : p.name)} · ${esc(eraOf(S.age).name)}${e ? `<br><span class="x">${esc(e.name)} mass extinction</span>` : ""}${LY.pos === "today" ? "<br>Dots at today's positions" : ""}`;
  tlCursor();
}
let playT = null;
function stop() { S.playing = false; clearTimeout(playT); playB.innerHTML = "&#9654; Play"; playB.setAttribute("aria-label", "Play through time"); }
function play() {
  S.playing = true; playB.innerHTML = "&#10074;&#10074; Pause"; playB.setAttribute("aria-label", "Pause");
  if (LY.pos === "today") morphTo(false);
  let k = AGESD.indexOf(S.age); if (k >= AGESD.length - 1) k = -1;
  const tick = async () => { if (!S.playing) return; k++; if (k >= AGESD.length) { stop(); return; }
    await setAge(AGESD[k]); const dwell = EXTAGE.has(AGESD[k]) ? 1700 : AGESD[k] % 10 ? 700 : 900; playT = setTimeout(tick, dwell); };
  tick();
}
playB.onclick = () => S.playing ? stop() : play();
const JUMPS = [[540, "Cambrian start"], [500, "Trilobite seas"], [445, "End-Ordovician", 1], [372, "Late Devonian", 1], [300, "Coal swamps"], [252, "End-Permian", 1], [220, "Pangaea"], [201, "End-Triassic", 1], [150, "Jurassic giants"], [70, "Last dinosaurs"], [66, "End-Cretaceous", 1], [0, "Today"]];
const jr = document.getElementById("jumpRow");
JUMPS.forEach(([a, t, x]) => { const b = document.createElement("button"); b.className = "btn" + (x ? " ex" : ""); b.textContent = `${t} · ${a ? a : "0"}`; b.onclick = () => { stop(); setAge(a); }; jr.appendChild(b); });

/* timeline under the map */
const tlBox = document.getElementById("timeline"); let tlX = null, tlCur = null;
function tlCursor() { if (tlCur && tlX) { const x = tlX(S.age); tlCur.setAttribute("transform", `translate(${x},0)`); } }
resp(tlBox, (w, sm) => {
  const h = 108, m = { l: 6, r: 6 }; const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Geological time scale with the five mass extinctions" }, tlBox);
  const x = d3.scaleLinear().domain([540, 0]).range([m.l, w - m.r]); tlX = x;
  // collections per 5 Myr, as a small area
  const cb = SITE.coll, mx = d3.max(cb), yA = d3.scaleSqrt().domain([0, mx]).range([0, 26]);
  const area = d3.area().x((d, i) => x(i * SITE.binw + SITE.binw / 2)).y0(30).y1(d => 30 - yA(d)).curve(d3.curveStepAfter);
  el("path", { d: area(cb.slice(0, 108)), fill: "var(--muted)", opacity: .35 }, svg);
  lbl(svg, m.l + 2, 9, sm ? "collections" : "fossil collections per 5 million years", "lab s m");
  // eras and periods
  ERAS.forEach(e => { el("rect", { x: x(Math.min(540, e.old)), y: 33, width: x(e.young) - x(Math.min(540, e.old)), height: 15, fill: e.c, stroke: "var(--bg)", "stroke-width": 1 }, svg);
    const t = lbl(svg, (x(Math.min(540, e.old)) + x(e.young)) / 2, 44.5, e.name, "lab s", "middle"); t.style.fill = ("#222"); });
  PERIODS.forEach(p => { const x0 = x(Math.min(540, p.old)), x1 = x(p.young); el("rect", { x: x0, y: 49, width: x1 - x0, height: 20, fill: p.c, stroke: "var(--bg)", "stroke-width": 1 }, svg);
    const wd = x1 - x0, nm = wd > p.name.length * 6.6 + 6 ? p.name : wd > 14 ? p.ab : "";
    if (nm) { const t = lbl(svg, (x0 + x1) / 2, 63, nm, "lab s", "middle"); t.style.fill = (["Triassic", "Ordovician", "Permian"].includes(p.name) ? "#fff" : "#222"); } });
  // extinctions
  EXT.forEach((e, i) => { const xx = x(e.age); el("line", { x1: xx, x2: xx, y1: 2, y2: 70, stroke: "var(--hot)", "stroke-width": 1.4, "stroke-dasharray": "3 2" }, svg);
    el("path", { d: `M${xx - 4},72 L${xx + 4},72 L${xx},79 Z`, fill: "var(--hot)" }, svg); });
  // extinction labels, alternating rows to avoid overlap
  EXT.forEach((e, i) => { const xx = x(e.age); const t = lbl(svg, xx, 90 + (i % 2) * 13, sm ? String(e.age) : `${e.name.replace("End-", "End ")} ${e.age}`, "lab s", "middle"); t.style.fill = "var(--hot)"; });
  // axis ticks
  [500, 400, 300, 200, 100, 0].forEach(a => { if (!sm || a % 200 === 0 || a === 500) { } });
  tlCur = el("g", {}, svg); el("line", { x1: 0, x2: 0, y1: 0, y2: 72, stroke: "var(--fg)", "stroke-width": 2.5 }, tlCur); el("circle", { cx: 0, cy: 30, r: 5, fill: "var(--fg)" }, tlCur);
  tlCursor();
  const setFrom = ev => { const r = svg.getBoundingClientRect(); const px = (ev.clientX - r.left) * w / r.width; stop(); setAge(Math.max(0, Math.min(540, x.invert(px)))); };
  let drag = false;
  svg.addEventListener("pointerdown", ev => { drag = true; svg.setPointerCapture(ev.pointerId); setFrom(ev); });
  svg.addEventListener("pointermove", ev => { if (drag) setFrom(ev); else { const r = svg.getBoundingClientRect(); const a = x.invert((ev.clientX - r.left) * w / r.width); const p = periodOf(a); showTip(`<b>${fmt(Math.max(0, a))} Ma</b> · ${esc(p.name)}`, ev.clientX, r.top + 4); } });
  svg.addEventListener("pointerup", () => { drag = false; }); svg.addEventListener("pointerleave", hideTip);
});

/* ---------- layers panel ---------- */
const lyrBtn = document.getElementById("lyrBtn"), lyrPanel = document.getElementById("lyrPanel");
lyrBtn.onclick = () => { const o = lyrPanel.hidden; lyrPanel.hidden = !o; lyrBtn.setAttribute("aria-expanded", o); };
["click", "dblclick", "mousedown", "touchstart", "wheel", "pointerdown"].forEach(t => document.getElementById("mapctl").addEventListener(t, e => e.stopPropagation(), { passive: true }));
function buildPanel() {
  const cnt = CUR.frame ? CUR.frame.byg : GROUPS.map(() => 0);
  lyrPanel.innerHTML = `
  <div class="row"><label class="b">Positions</label><div class="seg" id="posSeg"><button data-p="ancient">Where they lived</button><button data-p="today">Where found today</button></div></div>
  <div class="hd">Background</div>
  <div class="row"><label><input type="checkbox" data-k="land"> Continents of the time</label></div>
  <div class="row"><label><input type="checkbox" data-k="grat"> Grid, every 30 degrees</label></div>
  <div class="row"><label><input type="checkbox" data-k="lat"> Equator, tropics, polar circles</label></div>
  <div class="row"><label><input type="checkbox" data-k="labels"> Pangaea label</label></div>
  <div class="row"><label class="b">Dot size</label><div class="sub"><input type="range" data-k="size" min="0.5" max="2.2" step="0.1" aria-label="Dot size"></div></div>
  <div class="hd">Animal groups <span style="text-transform:none;letter-spacing:0">(finds in this frame)</span></div>
  <div class="row"><button class="mini" id="gAll">All</button><button class="mini" id="gNone">None</button><button class="mini" id="gDino">Dinosaurs only</button><button class="mini" id="gSea">Sea reptiles</button></div>
  <div class="gl">${ORDER.map(g => `<label><input type="checkbox" data-g="${g.k}"><span class="sw" style="background:${g.c}"></span>${esc(g.short)}<small>${fmt(cnt[g.i])}</small></label>`).join("")}</div>
  <button class="mini" id="lyReset">Reset layers</button>`;
  lyrPanel.querySelectorAll("[data-k]").forEach(i => i.addEventListener(i.type === "range" ? "input" : "change", () => { LY[i.dataset.k] = i.type === "checkbox" ? i.checked : +i.value; saveLY(); draw(); }));
  lyrPanel.querySelectorAll("[data-g]").forEach(i => i.addEventListener("change", () => { const s = ON(); i.checked ? s.add(i.dataset.g) : s.delete(i.dataset.g); LY.on = [...s]; saveLY(); draw(); side(); legend(); }));
  lyrPanel.querySelectorAll("#posSeg button").forEach(b => b.onclick = () => { const t = b.dataset.p === "today"; if ((LY.pos === "today") !== t) morphTo(t); });
  const setOn = a => { LY.on = a; saveLY(); syncPanel(); draw(); side(); legend(); };
  lyrPanel.querySelector("#gAll").onclick = () => setOn(GROUPS.map(g => g.k));
  lyrPanel.querySelector("#gNone").onclick = () => setOn([]);
  lyrPanel.querySelector("#gDino").onclick = () => setOn(["the", "sau", "orn", "din"]);
  lyrPanel.querySelector("#gSea").onclick = () => setOn(["ich", "ple", "mos"]);
  lyrPanel.querySelector("#lyReset").onclick = () => { Object.assign(LY, JSON.parse(JSON.stringify(LYDEF))); saveLY(); S.morph = 0; syncPanel(); draw(); side(); legend(); };
  syncPanel();
}
function syncPanel() {
  if (!lyrPanel.firstElementChild) return;
  lyrPanel.querySelectorAll("[data-k]").forEach(i => { if (i.type === "checkbox") i.checked = !!LY[i.dataset.k]; else i.value = LY[i.dataset.k]; });
  const on = ON(); lyrPanel.querySelectorAll("[data-g]").forEach(i => i.checked = on.has(i.dataset.g));
  lyrPanel.querySelectorAll("#posSeg button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.p === LY.pos)));
  const cnt = CUR.frame ? CUR.frame.byg : null; if (cnt) lyrPanel.querySelectorAll(".gl label").forEach((l, j) => { l.querySelector("small").textContent = fmt(cnt[ORDER[j].i]); });
  updateControls();
}

/* ---------- legend under the map: groups present in this frame ---------- */
function legend() {
  const lg = document.getElementById("legend"); if (!CUR.frame) return; const on = ON();
  lg.innerHTML = ORDER.filter(g => CUR.frame.byg[g.i] > 0).map(g => `<span style="opacity:${on.has(g.k) ? 1 : .4}"><i style="background:${g.c}"></i>${esc(g.short)}</span>`).join("") || "<span>No finds of these groups in this frame.</span>";
  syncPanel();
}

/* ---------- side panel ---------- */
function side() {
  const sd = document.getElementById("side"); if (!CUR.frame) return; const fr = CUR.frame, on = ON(), a = CUR.age;
  const e = EXT.find(x => x.age === a), p = periodOf(a), win = fr.win;
  const rows = ORDER.filter(g => fr.byg[g.i] > 0).sort((x, y) => fr.byg[y.i] - fr.byg[x.i]); const mx = d3.max(rows, g => fr.byg[g.i]) || 1;
  let h = `<h4>This frame</h4><div class="big">${a === 0 ? "Today" : fmt(a) + " million years ago"}</div><p class="sub">${esc(a === 0 ? "Quaternary" : p.name)}, ${esc(eraOf(a).name)} era. Fossils dated ${a === 0 ? "within the last 5 million years" : `${fmt(win[1])} to ${fmt(win[0])} million years ago`}: <b>${fmt(fr.n)}</b> occurrences in ${fmt(fr.nc)} collections.</p>`;
  if (e) h += `<p class="sub" style="color:var(--hot)"><b>${esc(e.name)} mass extinction.</b> ${esc(EXTNOTE[e.k])} The frame shows the 10 million years before it.</p>`;
  h += `<p class="sub">Largest land mass: <b>${f1(PAN[a])}%</b> of all land${PAN[a] >= 80 ? " (Pangaea)" : ""}.</p>`;
  if (S.nid != null && NAMES) { const n = NAMES[S.nid]; const here = fr.cells.filter(c => c[10].includes(S.nid)).length;
    h += `<h4>Highlighted</h4><p><span class="sw" style="background:${GROUPS[n[1]].c}"></span><b>${esc(n[0])}</b>, ${esc(GROUPS[n[1]].short.toLowerCase())}. ${fmt(n[2])} occurrences, ${n[3] === n[4] ? `dated about ${f1(n[3])}` : `dated ${f1(n[3])} to ${f1(n[4])}`} million years ago (midpoints). ${here ? `Ringed in ${here} square${here > 1 ? "s" : ""} in this frame.` : "None in this frame."} <button class="go" id="clrHl">Clear</button></p>`; }
  h += `<h4>Finds by group (click to show or hide)</h4><table>${rows.map(g => `<tr class="gr${on.has(g.k) ? "" : " off"}" data-g="${g.k}"><td><span class="sw" style="background:${g.c}"></span>${esc(g.short)}</td><td class="bar"><i style="width:${Math.max(2, 100 * fr.byg[g.i] / mx)}%;background:${g.c}"></i></td><td class="num">${fmt(fr.byg[g.i])}</td></tr>`).join("")}</table>`;
  if (!rows.length) h += `<p class="sub">No finds of these groups in this frame: the first trilobites appear around 520 million years ago.</p>`;
  h += `<p class="sub">Counts are fossil occurrences in the Paleobiology Database, not numbers of animals; they follow where rock of this age is exposed and who has looked.</p>`;
  sd.innerHTML = h;
  sd.querySelectorAll("tr.gr").forEach(tr => tr.onclick = () => { const s = ON(), k = tr.dataset.g; s.has(k) ? s.delete(k) : s.add(k); LY.on = [...s]; saveLY(); draw(); side(); legend(); });
  const c = sd.querySelector("#clrHl"); if (c) c.onclick = () => { S.nid = null; draw(); side(); };
}

/* ---------- clicking dots ---------- */
const pop = document.getElementById("pop");
function hit(ev) { const r = cv.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top; let best = null, bd = 1e9;
  for (const d of DRAWN) { const dd = Math.hypot(d.x - x, d.y - y); if (dd <= d.r + 4 && dd / (d.r + 2) < bd) { bd = dd / (d.r + 2); best = d; } } return best; }
cv.addEventListener("mousemove", ev => { const d = hit(ev); cv.classList.toggle("hand", !!d); });
cv.addEventListener("click", async ev => { const d = hit(ev); if (!d) { closePop(true); return; } await loadNames(); openPop(d); });
const ll = (lat, lng) => `${f1(Math.abs(lat))}&deg;&nbsp;${lat >= 0 ? "N" : "S"}, ${f1(Math.abs(lng))}&deg;&nbsp;${lng >= 0 ? "E" : "W"}`;
function openPop(d) {
  const c = d.c, g = GROUPS[c[0]]; S.sel = c;
  const names = c[10].map(i => NAMES[i]), gen = names.filter(n => n[5] === 1), oth = names.filter(n => n[5] !== 1);
  const link = n => `<a href="https://paleobiodb.org/classic/checkTaxonInfo?taxon_name=${encodeURIComponent(n[0])}" target="_blank" rel="noopener">${esc(n[0])}</a>`;
  const nshow = W < 600 ? 5 : 10;
  const show = gen.slice(0, nshow).map(link).join(", ") + (gen.length > nshow ? ` and ${gen.length - nshow} more` : "");
  pop.innerHTML = `<button class="cl" aria-label="Close">&times;</button><h5><span class="sw" style="background:${g.c}"></span>${esc(g.name)}</h5>
  <p>${fmt(c[3])} occurrence${c[3] > 1 ? "s" : ""} in ${fmt(c[4])} collection${c[4] > 1 ? "s" : ""}, dated ${c[8] === c[9] ? `about ${f1(c[8])}` : `${f1(c[9])} to ${f1(c[8])}`} million years ago <span class="m">(collection midpoints)</span>.</p>
  <p><b>Then:</b> ${ll(c[2], c[1])} <span class="m">(palaeo-position)</span><br><b>Today:</b> ${esc(PLACES[c[7]])} <span class="m">(${ll(c[6], c[5])})</span></p>
  ${gen.length ? `<p class="tx"><b>Genera:</b> ${show}</p>` : ""}${oth.length ? `<p class="tx m">Also identified only as: ${oth.slice(0, 5).map(n => esc(n[0])).join(", ")}${oth.length > 5 ? "..." : ""}</p>` : ""}
  <p><button class="btn" id="popWhere">${LY.pos === "today" ? "Back to where it lived" : "Where is this today?"}</button></p>`;
  const r = box.getBoundingClientRect(); pop.style.display = "block";
  const pw = pop.offsetWidth, ph = pop.offsetHeight; let x = d.x + 14, y = d.y - ph / 2;
  if (x + pw > r.width - 8) x = d.x - pw - 14; if (x < 8) x = Math.max(8, (r.width - pw) / 2);
  y = Math.max(6, Math.min(r.height - ph - 56, y));
  pop.style.left = x + "px"; pop.style.top = y + "px";
  pop.querySelector(".cl").onclick = () => closePop(true);
  pop.querySelector("#popWhere").onclick = () => { closePop(false); morphTo(LY.pos !== "today"); };
  draw();
}
function closePop(clear) { pop.style.display = "none"; if (clear) { S.sel = null; draw(); } }
["click", "mousedown", "wheel", "pointerdown", "touchstart", "dblclick"].forEach(t => pop.addEventListener(t, e => e.stopPropagation(), { passive: true }));

/* ---------- search ---------- */
const q = document.getElementById("q"), sug = document.getElementById("sug"); let sugI = -1, sugL = [];
q.addEventListener("focus", loadNames, { once: true });
q.addEventListener("input", async () => { await loadNames(); const v = q.value.trim().toLowerCase(); if (v.length < 2) { sug.style.display = "none"; return; }
  sugL = []; for (let i = 0; i < NAMES.length && sugL.length < 12; i++) { const n = NAMES[i]; if (n[5] === 1 && n[0].toLowerCase().startsWith(v)) sugL.push(i); }
  if (sugL.length < 12) for (let i = 0; i < NAMES.length && sugL.length < 12; i++) { const n = NAMES[i]; if (n[5] === 1 && !sugL.includes(i) && n[0].toLowerCase().includes(v)) sugL.push(i); }
  sugI = -1; sug.innerHTML = sugL.map((i, j) => { const n = NAMES[i]; return `<li role="option" data-i="${i}"><span class="sw" style="background:${GROUPS[n[1]].c}"></span>${esc(n[0])} <span>${esc(GROUPS[n[1]].short.toLowerCase())}, ${fmt(n[2])} finds, ${f1(n[3])} Ma${n[4] !== n[3] ? " to " + f1(n[4]) : ""}</span></li>`; }).join("") || "<li><span>No genus of that name in these groups</span></li>";
  sug.style.display = "block"; sug.querySelectorAll("li[data-i]").forEach(li => li.onclick = () => pick(+li.dataset.i)); });
q.addEventListener("keydown", e => { const lis = sug.querySelectorAll("li[data-i]"); if (!lis.length) return;
  if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); sugI = (sugI + (e.key === "ArrowDown" ? 1 : -1) + lis.length) % lis.length; lis.forEach((l, j) => l.setAttribute("aria-selected", j === sugI)); }
  else if (e.key === "Enter") { e.preventDefault(); pick(+lis[Math.max(0, sugI)].dataset.i); } else if (e.key === "Escape") sug.style.display = "none"; });
document.addEventListener("click", e => { if (!e.target.closest(".searchbox")) sug.style.display = "none"; });
async function pick(i) { await loadNames(); const n = NAMES[i]; q.value = n[0]; sug.style.display = "none"; S.nid = i; stop();
  const g = GROUPS[n[1]]; if (!ON().has(g.k)) { LY.on.push(g.k); saveLY(); }
  // the frame (of those whose window covers the genus) with the most squares holding it
  const cand = AGES.filter(a => { const w = SITE.frames[a].win; return w[0] <= n[3] && w[1] > n[4]; });
  let best = nearestAge((n[3] + n[4]) / 2), bn = -1;
  for (const a of cand.slice(0, 8)) { const fr = await getFrame(a); const k = fr.cells.filter(c => c[10].includes(i)).length; if (k > bn) { bn = k; best = a; } }
  await setAge(best); document.getElementById("atlas").scrollIntoView({ behavior: "smooth", block: "start" }); }
window.searchFor = async s => { await loadNames(); q.value = s; q.dispatchEvent(new Event("input")); };
window.pickName = async s => { await loadNames(); const i = NAMES.findIndex(n => n[0] === s); if (i >= 0) await pick(i); };

/* ---------- charts ---------- */
const BW = SITE.binw, NB = SITE.bins;
function timeAxis(svg, x, y0, w, sm, opts = {}) {
  // period band and ticks
  PERIODS.forEach(p => { const x0 = x(Math.min(x.domain()[0], p.old)), x1 = x(Math.max(x.domain()[1], p.young)); if (x1 <= x0) return;
    el("rect", { x: x0, y: y0, width: x1 - x0, height: 14, fill: p.c, stroke: "var(--bg)", "stroke-width": 1 }, svg);
    const wd = x1 - x0, nm = wd > p.name.length * 6.3 + 4 ? p.name : wd > 13 ? p.ab : ""; if (nm) { const t = lbl(svg, (x0 + x1) / 2, y0 + 10.5, nm, "lab s", "middle"); t.style.fill = (["Triassic", "Ordovician", "Permian"].includes(p.name) ? "#fff" : "#222"); t.style.fontSize = "10px"; } });
  const ticks = opts.ticks || (sm ? [500, 400, 300, 200, 100, 0] : [500, 450, 400, 350, 300, 250, 200, 150, 100, 50, 0]);
  ticks.filter(a => a <= x.domain()[0] && a >= x.domain()[1]).forEach(a => { el("line", { x1: x(a), x2: x(a), y1: y0 + 14, y2: y0 + 18, stroke: "var(--muted)" }, svg); lbl(svg, x(a), y0 + 29, a ? String(a) : "0 Ma", "lab s m", "middle"); });
}
function extLines(svg, x, y0, y1) { EXT.forEach(e => { if (e.age > x.domain()[0] || e.age < x.domain()[1]) return; el("line", { x1: x(e.age), x2: x(e.age), y1: y0, y2: y1, stroke: "var(--hot)", "stroke-width": 1.2, "stroke-dasharray": "3 3", opacity: .8 }, svg); }); }
const jumpMap = a => { stop(); setAge(a); document.getElementById("atlas").scrollIntoView({ behavior: "smooth", block: "start" }); };

/* Pangaea index */
resp(document.getElementById("panChart"), (w, sm) => {
  const h = sm ? 250 : 290, m = { l: 40, r: 12, t: 16, b: 46 }; const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Line chart of the share of land in the largest land mass from 540 million years ago to today, above 85 per cent from 270 to 180 million years ago" }, document.getElementById("panChart"));
  const x = d3.scaleLinear().domain([540, 0]).range([m.l, w - m.r]), y = d3.scaleLinear().domain([0, 100]).range([h - m.b, m.t]);
  [0, 25, 50, 75, 100].forEach(v => { el("line", { x1: m.l, x2: w - m.r, y1: y(v), y2: y(v), stroke: "var(--rule)" }, svg); lbl(svg, m.l - 6, y(v) + 4, v + "%", "lab s m", "end"); });
  el("rect", { x: x(R.pangaea.first_over_85), y: m.t, width: x(R.pangaea.last_over_85) - x(R.pangaea.first_over_85), height: h - m.b - m.t, fill: "var(--gold)", opacity: .13 }, svg);
  lbl(svg, (x(R.pangaea.first_over_85) + x(R.pangaea.last_over_85)) / 2, m.t + 12, "Pangaea", "lab b", "middle");
  extLines(svg, x, m.t, h - m.b);
  const data = SITE.pangaea.slice().sort((a, b) => b[0] - a[0]);
  el("path", { d: d3.area().x(d => x(d[0])).y0(y(0)).y1(d => y(d[1]))(data), fill: "var(--cool)", opacity: .14 }, svg);
  el("path", { d: d3.line().x(d => x(d[0])).y(d => y(d[1]))(data), fill: "none", stroke: "var(--cool)", "stroke-width": 2.4 }, svg);
  const pk = data.find(d => d[0] === R.pangaea.peak_age); el("circle", { cx: x(pk[0]), cy: y(pk[1]), r: 4, fill: "var(--cool)" }, svg);
  lbl(svg, x(pk[0]) + 8, y(pk[1]) + 16, `${f1(pk[1])}% at ${pk[0]} Ma`, "lab s b", "start");
  const td = data[data.length - 1]; el("circle", { cx: x(0), cy: y(td[1]), r: 4, fill: "var(--cool)" }, svg); lbl(svg, x(0) - 6, y(td[1]) - 9, `today ${f1(td[1])}%`, "lab s b", "end");
  timeAxis(svg, x, h - m.b + 2, w, sm);
  const hov = el("line", { y1: m.t, y2: h - m.b, stroke: "var(--fg)", opacity: 0 }, svg);
  el("rect", { x: m.l, y: m.t, width: w - m.l - m.r, height: h - m.b - m.t, fill: "transparent", style: "cursor:pointer" }, svg).addEventListener("pointermove", ev => {
    const r = svg.getBoundingClientRect(); const a = nearestAge(x.invert((ev.clientX - r.left) * w / r.width)); hov.setAttribute("x1", x(a)); hov.setAttribute("x2", x(a)); hov.setAttribute("opacity", .4);
    showTip(`<b>${maShort(a)}</b> · ${esc(periodOf(a).name)}<br>Largest land mass: ${f1(PAN[a])}% of land`, ev.clientX, r.top + y(PAN[a]) * r.height / h); });
  svg.lastChild.addEventListener("pointerleave", () => { hideTip(); hov.setAttribute("opacity", 0); });
  svg.lastChild.addEventListener("click", ev => { const r = svg.getBoundingClientRect(); jumpMap(nearestAge(x.invert((ev.clientX - r.left) * w / r.width))); });
});

/* swim lanes */
let laneMode = "own";
document.querySelectorAll("#laneMode .btn").forEach(b => b.onclick = () => { laneMode = b.dataset.m; document.querySelectorAll("#laneMode .btn").forEach(x => x.setAttribute("aria-pressed", String(x === b))); redraws[laneIdx](); });
const laneIdx = redraws.length;
resp(document.getElementById("laneChart"), (w, sm) => {
  const box = document.getElementById("laneChart");
  const lh = sm ? 17 : 20, lw = sm ? 128 : 168, m = { l: lw, r: 10, t: 6, b: 40 };
  const tot = d3.range(NB).map(b => d3.sum(GROUPS, g => SITE.gen[g.k][b]));
  const x = d3.scaleLinear().domain([540, 0]).range([m.l, w - m.r]);
  let h;
  if (laneMode === "own") {
    h = m.t + ORDER.length * lh + m.b; const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Swim-lane chart of genera per group through time, each scaled to its own peak" }, box);
    extLines(svg, x, m.t, h - m.b);
    ORDER.forEach((g, j) => { const y0 = m.t + j * lh, s = SITE.gen[g.k], mx = d3.max(s) || 1;
      el("line", { x1: m.l, x2: w - m.r, y1: y0 + lh - 1, y2: y0 + lh - 1, stroke: "var(--rule)" }, svg);
      const pts = d3.range(NB).map(b => [b * BW + BW / 2, s[b] / mx]);
      el("path", { d: d3.area().x(d => x(d[0])).y0(y0 + lh - 1).y1(d => y0 + lh - 1 - d[1] * (lh - 3)).curve(d3.curveMonotoneX)(pts), fill: g.c, opacity: .9 }, svg);
      const t = lbl(svg, m.l - 6, y0 + lh - 5, sm ? g.short : g.short, "lab s", "end"); t.style.fontSize = sm ? "10px" : "11.5px"; });
    timeAxis(svg, x, h - m.b + 4, w, sm);
    const ov = el("rect", { x: m.l, y: m.t, width: w - m.l - m.r, height: ORDER.length * lh, fill: "transparent" }, svg);
    ov.addEventListener("pointermove", ev => { const r = svg.getBoundingClientRect(); const px = (ev.clientX - r.left) * w / r.width, py = (ev.clientY - r.top) * h / r.height;
      const j = Math.floor((py - m.t) / lh), g = ORDER[j]; if (!g) return; const b = Math.min(NB - 1, Math.max(0, Math.floor(x.invert(px) / BW)));
      showTip(`<b>${esc(g.name)}</b><br>${b * BW + BW} to ${b * BW} Ma: ${fmt(SITE.gen[g.k][b])} genera, ${fmt(SITE.occ[g.k][b])} occurrences`, ev.clientX, ev.clientY - 6); });
    ov.addEventListener("pointerleave", hideTip);
  } else {
    h = sm ? 330 : 400; const mm = { l: 40, r: 10, t: 8, b: 40 }; const xx = d3.scaleLinear().domain([540, 0]).range([mm.l, w - mm.r]); const y = d3.scaleLinear().domain([0, 1]).range([h - mm.b, mm.t]);
    const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Stacked area chart of each group's share of all genera through time" }, box);
    const keys = ORDER.map(g => g.k); const rows = d3.range(NB).map(b => { const o = { a: b * BW + BW / 2 }; keys.forEach(k => o[k] = tot[b] >= 5 ? SITE.gen[k][b] / tot[b] : 0); return o; });
    const st = d3.stack().keys(keys)(rows);
    st.forEach((s, j) => el("path", { d: d3.area().x(d => xx(d.data.a)).y0(d => y(d[0])).y1(d => y(d[1])).curve(d3.curveStepAfter)(s), fill: GI[keys[j]].c }, svg));
    [0, .25, .5, .75, 1].forEach(v => lbl(svg, mm.l - 6, y(v) + 4, Math.round(v * 100) + "%", "lab s m", "end"));
    extLines(svg, xx, mm.t, h - mm.b); timeAxis(svg, xx, h - mm.b + 4, w, sm);
    const ov = el("rect", { x: mm.l, y: mm.t, width: w - mm.l - mm.r, height: h - mm.b - mm.t, fill: "transparent" }, svg);
    ov.addEventListener("pointermove", ev => { const r = svg.getBoundingClientRect(); const px = (ev.clientX - r.left) * w / r.width, py = (ev.clientY - r.top) * h / r.height; const b = Math.min(NB - 1, Math.max(0, Math.floor(xx.invert(px) / BW)));
      const v = y.invert(py); let acc = 0, g = null; for (const k of keys) { acc += rows[b][k]; if (v <= acc) { g = GI[k]; break; } } if (!g || !tot[b]) return;
      showTip(`<b>${esc(g.name)}</b><br>${b * BW + BW} to ${b * BW} Ma: ${fmt(SITE.gen[g.k][b])} of ${fmt(tot[b])} genera (${f1(100 * SITE.gen[g.k][b] / tot[b])}%)`, ev.clientX, ev.clientY - 6); });
    ov.addEventListener("pointerleave", hideTip);
  }
});

/* dinosaur genera */
resp(document.getElementById("dinoChart"), (w, sm) => {
  const h = sm ? 260 : 300, m = { l: 40, r: sm ? 10 : 110, t: 10, b: 46 }; const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Stacked area chart of dinosaur genera per 5 million years by group from the Triassic to the end of the Cretaceous, with birds as a line" }, document.getElementById("dinoChart"));
  const A = SITE.dino_bins; const keys = ["the", "sau", "orn", "din"];
  const rows = A.map((a, i) => { const o = { a: a + BW / 2 }; keys.forEach(k => o[k] = SITE.dino[k][i]); o.ave = SITE.dino.ave[i]; return o; });
  const x = d3.scaleLinear().domain([240, 60]).range([m.l, w - m.r]); const st = d3.stack().keys(keys)(rows);
  const y = d3.scaleLinear().domain([0, d3.max(rows, r => keys.reduce((s, k) => s + r[k], 0)) * 1.08]).nice().range([h - m.b, m.t]);
  y.ticks(5).forEach(v => { el("line", { x1: m.l, x2: w - m.r, y1: y(v), y2: y(v), stroke: "var(--rule)" }, svg); lbl(svg, m.l - 6, y(v) + 4, v, "lab s m", "end"); });
  extLines(svg, x, m.t, h - m.b);
  st.forEach((s, j) => el("path", { d: d3.area().x(d => x(d.data.a)).y0(d => y(d[0])).y1(d => y(d[1])).curve(d3.curveMonotoneX)(s), fill: GI[keys[j]].c, opacity: .92 }, svg));
  el("path", { d: d3.line().x(d => x(d.a)).y(d => y(d.ave)).curve(d3.curveMonotoneX)(rows), fill: "none", stroke: GI.ave.c, "stroke-width": 2.5, "stroke-dasharray": "5 3" }, svg);
  timeAxis(svg, x, h - m.b + 2, w, sm, { ticks: [240, 200, 160, 120, 80, 60].filter(a => !sm || a % 40 === 0 || a === 60) });
  if (!sm) { // labels at the right of the last full bin
    const i = rows.findIndex(r => r.a === 67.5) >= 0 ? rows.findIndex(r => r.a === 67.5) : 1; let last = -1e9;
    [...keys.map((k, j) => [k, (st[j][i][0] + st[j][i][1]) / 2]), ["ave", rows[i].ave]].sort((p, q) => q[1] - p[1]).forEach(([k, v]) => { let yy = y(v) + 4; if (yy < last + 13) yy = last + 13; last = yy; const t = lbl(svg, w - m.r + 6, yy, GI[k].short, "lab s b"); t.style.fill = (GI[k].c); });
  } else { const lg = document.createElement("div"); lg.className = "legend"; lg.innerHTML = [...keys, "ave"].map(k => `<span><i style="background:${GI[k].c}"></i>${esc(GI[k].short)}</span>`).join(""); document.getElementById("dinoChart").appendChild(lg); }
  const ov = el("rect", { x: m.l, y: m.t, width: w - m.l - m.r, height: h - m.b - m.t, fill: "transparent" }, svg);
  ov.addEventListener("pointermove", ev => { const r = svg.getBoundingClientRect(); const a = x.invert((ev.clientX - r.left) * w / r.width); const i = rows.findIndex(o => Math.abs(o.a - a) <= BW / 2); if (i < 0) return; const o = rows[i];
    showTip(`<b>${o.a + BW / 2} to ${o.a - BW / 2} Ma</b><br>${[...keys, "ave"].map(k => `${esc(GI[k].short)}: ${fmt(o[k])}`).join("<br>")}`, ev.clientX, ev.clientY - 6); });
  ov.addEventListener("pointerleave", hideTip);
});

/* three small dinosaur maps */
(function () {
  const MM = [[210, "Late Triassic", "Pangaea whole"], [150, "Late Jurassic", "the central Atlantic opening"], [70, "Late Cretaceous", "continents apart"]];
  const host = document.getElementById("miniMaps");
  host.innerHTML = MM.map(([a, n, s]) => `<figure><canvas data-a="${a}" width="600" height="320" aria-label="Map of dinosaur finds ${a} million years ago"></canvas><figcaption><b>${a} million years ago</b>, ${n}: ${s}. Largest land mass ${f1(PAN[a])}% of land.</figcaption></figure>`).join("");
  const draw1 = async c => { const a = +c.dataset.a; const [coast, fr] = await Promise.all([getCoast(a), getFrame(a)]); const w = c.clientWidth || 300, hh = Math.round(w * .53), dpr = Math.min(2, devicePixelRatio || 1);
    c.width = w * dpr; c.height = hh * dpr; c.style.height = hh + "px"; const x = c.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0);
    const pj = d3.geoEqualEarth().fitExtent([[4, 4], [w - 4, hh - 4]], { type: "Sphere" }), pt = d3.geoPath(pj, x);
    x.fillStyle = css("--bg"); x.fillRect(0, 0, w, hh); x.beginPath(); pt({ type: "Sphere" }); x.fillStyle = css("--sea"); x.fill();
    x.beginPath(); pt(coast); x.fillStyle = css("--land"); x.fill(); x.strokeStyle = css("--landedge"); x.lineWidth = .6; x.stroke();
    const dk = new Set([0, 1, 2, 3].map(i => GI[["the", "sau", "orn", "din"][i]].i));
    fr.cells.filter(cc => dk.has(cc[0])).forEach(cc => { const p = pj([cc[1], cc[2]]); if (!p) return; x.beginPath(); x.arc(p[0], p[1], (1.5 + 1.1 * Math.log10(1 + cc[3])) * Math.max(.8, w / 380), 0, 2 * Math.PI); x.fillStyle = GROUPS[cc[0]].c; x.globalAlpha = .9; x.fill(); x.globalAlpha = 1; x.lineWidth = .5; x.strokeStyle = "#fff"; x.stroke(); });
    c.onclick = () => { LY.on = ["the", "sau", "orn", "din"]; saveLY(); syncPanel(); jumpMap(a); }; c.style.cursor = "pointer"; };
  const all = () => host.querySelectorAll("canvas").forEach(draw1);
  new ResizeObserver(() => all()).observe(host); redraws.push(all);
  const lg = document.createElement("div"); lg.className = "legend"; lg.innerHTML = ["the", "sau", "orn", "din"].map(k => `<span><i style="background:${GI[k].c}"></i>${esc(GI[k].short)}</span>`).join("") + "<span>Click a map to open it above.</span>"; host.after(lg);
})();

/* genera on several continents */
resp(document.getElementById("cosmoChart"), (w, sm) => {
  const D = SITE.dint, h = sm ? 250 : 260, m = { l: 40, r: 40, t: 18, b: sm ? 58 : 44 }; const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Bar chart of the share of dinosaur genera found on more than one present-day continent, by interval from the Late Triassic to the Late Cretaceous, with the share of land in the largest land mass as a line" }, document.getElementById("cosmoChart"));
  const x = d3.scaleBand().domain(D.map(d => d.name)).range([m.l, w - m.r]).padding(.28), y = d3.scaleLinear().domain([0, 20]).range([h - m.b, m.t]), y2 = d3.scaleLinear().domain([0, 100]).range([h - m.b, m.t]);
  [0, 5, 10, 15, 20].forEach(v => { el("line", { x1: m.l, x2: w - m.r, y1: y(v), y2: y(v), stroke: "var(--rule)" }, svg); lbl(svg, m.l - 6, y(v) + 4, v + "%", "lab s m", "end"); });
  [0, 50, 100].forEach(v => { lbl(svg, w - m.r + 6, y2(v) + 4, v + "%", "lab s", "start").style.fill = "var(--gold)"; });
  D.forEach(d => { const b = el("rect", { x: x(d.name), y: y(d.multi_pct), width: x.bandwidth(), height: y(0) - y(d.multi_pct), fill: GI.sau.c, opacity: .85 }, svg);
    lbl(svg, x(d.name) + x.bandwidth() / 2, y(d.multi_pct) - 5, f1(d.multi_pct) + "%", "lab s b", "middle");
    const parts = d.name.split(" "); lbl(svg, x(d.name) + x.bandwidth() / 2, h - m.b + 15, parts[0], "lab s", "middle"); lbl(svg, x(d.name) + x.bandwidth() / 2, h - m.b + 28, parts[1], "lab s", "middle");
    b.addEventListener("pointermove", ev => showTip(`<b>${esc(d.name)}</b>, ${d.old} to ${d.young} Ma<br>${fmt(d.multi)} of ${fmt(d.genera)} genera on 2 or more continents (${f1(d.multi_pct)}%)<br>Largest land mass at ${d.pangaea_age} Ma: ${f1(d.pangaea_pct)}%<br>${f1(d.na_eu_pct)}% of finds from North America and Europe`, ev.clientX, ev.clientY - 6)); b.addEventListener("pointerleave", hideTip); });
  el("path", { d: d3.line().x(d => x(d.name) + x.bandwidth() / 2).y(d => y2(d.pangaea_pct))(D), fill: "none", stroke: "var(--gold)", "stroke-width": 2.4 }, svg);
  D.forEach(d => el("circle", { cx: x(d.name) + x.bandwidth() / 2, cy: y2(d.pangaea_pct), r: 3.5, fill: "var(--gold)" }, svg));
  const t = lbl(svg, w - m.r - 2, y2(D[0].pangaea_pct) - 2 < m.t + 4 ? m.t + 4 : m.t + 4, "largest land mass", "lab s", "end"); t.style.fill = ("var(--gold)");
});

/* latitude bands */
let latG = "the";
(function () { const row = document.getElementById("latRow"); ORDER.forEach(g => { const b = document.createElement("button"); b.className = "btn"; b.innerHTML = `<span class="dot" style="background:${g.c}"></span>${esc(g.short)}`; b.setAttribute("aria-pressed", String(g.k === latG)); b.onclick = () => { latG = g.k; row.querySelectorAll(".btn").forEach(x => x.setAttribute("aria-pressed", String(x === b))); redraws[latIdx](); }; row.appendChild(b); }); })();
const latIdx = redraws.length;
resp(document.getElementById("latChart"), (w, sm) => {
  const h = sm ? 280 : 320, m = { l: 44, r: 12, t: 10, b: 46 }; const g = GI[latG], D = SITE.lat[latG] || [];
  const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": `Palaeo-latitude of ${g.short} collections through time` }, document.getElementById("latChart"));
  const x = d3.scaleLinear().domain([540, 0]).range([m.l, w - m.r]), y = d3.scaleLinear().domain([-90, 90]).range([h - m.b, m.t]);
  [[-66.56, "Antarctic Circle"], [-23.44, "Tropic of Capricorn"], [0, "Equator"], [23.44, "Tropic of Cancer"], [66.56, "Arctic Circle"]].forEach(([v, n]) => { el("line", { x1: m.l, x2: w - m.r, y1: y(v), y2: y(v), stroke: v ? "var(--rule)" : "var(--muted)", "stroke-dasharray": v ? "3 3" : "" }, svg); });
  [-90, -60, -30, 0, 30, 60, 90].forEach(v => lbl(svg, m.l - 6, y(v) + 4, v === 0 ? "0" : `${Math.abs(v)}${v > 0 ? "N" : "S"}`, "lab s m", "end"));
  el("rect", { x: m.l, y: y(23.44), width: w - m.l - m.r, height: y(-23.44) - y(23.44), fill: "var(--gold)", opacity: .08 }, svg);
  lbl(svg, w - m.r - 4, y(23.44) + 13, "tropics", "lab s m", "end");
  extLines(svg, x, m.t, h - m.b);
  // continuous segments only (gaps where fewer than 5 collections)
  const segs = []; let cur = []; D.slice().sort((a, b) => b[0] - a[0]).forEach(d => { if (cur.length && Math.abs(cur[cur.length - 1][0] - d[0]) > 10.5) { segs.push(cur); cur = []; } cur.push(d); }); if (cur.length) segs.push(cur);
  segs.forEach(s => { if (s.length === 1) { const d = s[0]; el("line", { x1: x(d[0]), x2: x(d[0]), y1: y(d[1]), y2: y(d[3]), stroke: g.c, "stroke-width": 6, opacity: .3 }, svg); el("circle", { cx: x(d[0]), cy: y(d[2]), r: 3, fill: g.c }, svg); return; }
    el("path", { d: d3.area().x(d => x(d[0])).y0(d => y(d[1])).y1(d => y(d[3])).curve(d3.curveMonotoneX)(s), fill: g.c, opacity: .25 }, svg);
    el("path", { d: d3.line().x(d => x(d[0])).y(d => y(d[2])).curve(d3.curveMonotoneX)(s), fill: "none", stroke: g.c, "stroke-width": 2.4 }, svg); });
  timeAxis(svg, x, h - m.b + 2, w, sm);
  lbl(svg, m.l + 6, m.t + 12, `${g.name}: median ${f1(R.lat[latG])} degrees from the equator`, "lab s b");
  const ov = el("rect", { x: m.l, y: m.t, width: w - m.l - m.r, height: h - m.b - m.t, fill: "transparent" }, svg);
  ov.addEventListener("pointermove", ev => { const r = svg.getBoundingClientRect(); const a = x.invert((ev.clientX - r.left) * w / r.width); const d = D.find(d => Math.abs(d[0] - a) <= 5); if (!d) { hideTip(); return; }
    const L = v => `${Math.abs(v).toFixed(0)}&deg;${v >= 0 ? "N" : "S"}`; showTip(`<b>${esc(g.short)}, ${d[0] + 5} to ${d[0] - 5} Ma</b><br>${fmt(d[4])} collections<br>median ${L(d[2])}, middle 80% ${L(d[1])} to ${L(d[3])}`, ev.clientX, ev.clientY - 6); });
  ov.addEventListener("pointerleave", hideTip);
});

/* extinction cards */
(function () {
  const host = document.getElementById("extCards");
  host.innerHTML = R.extinctions.map(e => { const rows = Object.entries(e.by_group).sort((a, b) => b[1].lost_pct - a[1].lost_pct).slice(0, 6);
    return `<div class="card"><b>${esc(e.name)}</b><span style="color:var(--muted)">${e.age} million years ago</span><div class="big">${Math.round(e.lost_pct)}%<span> of ${fmt(e.standing)} genera last seen</span></div>
    <div class="rows">${rows.map(([k, v]) => `<div class="r"><div><em>${esc(GI[k].short)} <span style="color:var(--muted)">(${v.standing})</span></em><i style="width:${Math.max(2, v.lost_pct)}%;background:${GI[k].c}"></i></div><span>${Math.round(v.lost_pct)}%</span></div>`).join("")}</div>
    <button class="btn" data-a="${e.age}">See it on the map</button></div>`; }).join("");
  host.querySelectorAll("button").forEach(b => b.onclick = () => jumpMap(+b.dataset.a));
})();

/* sampling */
resp(document.getElementById("contChart"), (w, sm) => {
  const D = R.sampling.by_continent.filter(d => d.name !== "Ocean"), bh = 24, m = { l: 112, r: 50, t: 4, b: 4 }, h = m.t + D.length * bh + m.b;
  const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Bar chart of the share of fossil occurrences by present-day continent" }, document.getElementById("contChart"));
  const x = d3.scaleLinear().domain([0, d3.max(D, d => d.pct)]).range([m.l, w - m.r]);
  D.forEach((d, i) => { const y0 = m.t + i * bh; lbl(svg, m.l - 6, y0 + 16, d.name, "lab", "end"); el("rect", { x: m.l, y: y0 + 4, width: x(d.pct) - m.l, height: bh - 8, fill: ["North America", "Europe"].includes(d.name) ? "var(--hot)" : "var(--muted)", opacity: .85 }, svg); lbl(svg, x(d.pct) + 5, y0 + 16, f1(d.pct) + "%", "lab s"); });
});
resp(document.getElementById("naeuChart"), (w, sm) => {
  const h = 230, m = { l: 40, r: 10, t: 10, b: 46 }; const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": "Line chart of the share of occurrences from North America and Europe through time" }, document.getElementById("naeuChart"));
  const x = d3.scaleLinear().domain([540, 0]).range([m.l, w - m.r]), y = d3.scaleLinear().domain([0, 100]).range([h - m.b, m.t]);
  [0, 50, 100].forEach(v => { el("line", { x1: m.l, x2: w - m.r, y1: y(v), y2: y(v), stroke: "var(--rule)" }, svg); lbl(svg, m.l - 6, y(v) + 4, v + "%", "lab s m", "end"); });
  el("line", { x1: m.l, x2: w - m.r, y1: y(R.sampling.na_eu_land_pct), y2: y(R.sampling.na_eu_land_pct), stroke: "var(--muted)", "stroke-dasharray": "4 3" }, svg);
  lbl(svg, w - m.r - 2, y(R.sampling.na_eu_land_pct) + 14, "their share of land", "lab s m", "end");
  const pts = SITE.na_eu_bin.map((v, b) => [b * BW + BW / 2, v]).filter(d => d[1] != null && SITE.coll[(d[0] - BW / 2) / BW] >= 20);
  el("path", { d: d3.line().x(d => x(d[0])).y(d => y(d[1])).curve(d3.curveMonotoneX)(pts), fill: "none", stroke: "var(--hot)", "stroke-width": 2 }, svg);
  timeAxis(svg, x, h - m.b + 2, w, true, { ticks: [500, 300, 100, 0] });
});

/* ---------- theme ---------- */
document.getElementById("theme").onclick = () => { const r = document.documentElement; r.dataset.theme = isDark() ? "light" : "dark"; draw(); redraws.forEach(f => f()); };
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { draw(); redraws.forEach(f => f()); });

/* ---------- start ---------- */
LY.pos = "ancient";
buildPanel(); resize();
getCoast(0).then(c => { NOW = c; });
setAge(250, { instant: true }).then(() => { buildPanel(); });
loadNames();
