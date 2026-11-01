// QA: serve the folder, open index.html at 1280 px and 390 px, collect console errors, take screenshots, exercise the
// controls. Run: node code/11_qa.js (needs playwright, and d3 7.9.0 from a local npm folder, QA_NODE).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const NM = process.env.QA_NODE || '/tmp/claude-0/node_modules';
const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.csv': 'text/csv', '.js': 'text/javascript' };
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0].split('#')[0])); fs.readFile(f.endsWith('/') ? f + 'index.html' : f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); }).listen(0);
const only = process.argv[2];
(async () => {
  const b = await chromium.launch();
  for (const [w, h, tag] of [[1280, 900, 'desktop'], [390, 844, 'phone']]) {
    if (only && only !== tag) continue;
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: tag === 'phone' ? 2 : 1 });
    const errs = [];
    p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
    await p.route(/googleapis|gstatic/, r => r.abort());
    await p.route(/d3\.min\.js/, r => r.fulfill({ path: NM + '/d3/dist/d3.min.js', contentType: 'text/javascript' }));
    await p.goto(`http://localhost:${srv.address().port}/index.html`, { waitUntil: 'load' });
    await p.waitForTimeout(1500);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_top.png` });
    await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
    for (const a of [500, 300, 252, 200, 150, 66, 0]) {
      await p.evaluate(a => setAge(a), a); await p.waitForTimeout(900);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_map_${a}.png` });
    }
    // click the biggest theropod square at 70 Ma
    await p.evaluate(() => setAge(70)); await p.waitForTimeout(900);
    const pt = await p.evaluate(() => { const d = DRAWN.filter(d => d.c[0] === GI.the.i).sort((a, b) => b.c[3] - a.c[3])[0]; const r = document.getElementById('mapc').getBoundingClientRect(); return d ? [r.left + d.x, r.top + d.y] : null; });
    if (pt) { await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(700); }
    await p.screenshot({ path: `${ROOT}/qa/${tag}_click.png` });
    const popTxt = await p.$eval('#pop', e => e.innerText.slice(0, 200));
    await p.click('#popWhere').catch(() => {}); await p.waitForTimeout(1300);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_today_positions.png` });
    await p.evaluate(() => morphTo(false)); await p.waitForTimeout(1100);
    await p.click('#lyrBtn'); await p.waitForTimeout(300);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_layers.png` });
    await p.click('#lyrBtn');
    await p.evaluate(() => pickName('Tyrannosaurus')); await p.waitForTimeout(1500);
    await p.evaluate(() => document.getElementById('atlas').scrollIntoView()); await p.waitForTimeout(300);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_search.png` });
    await p.evaluate(() => searchFor('Diplo')); await p.waitForTimeout(400);
    const sug = await p.$eval('#sug', e => e.textContent);
    await p.evaluate(() => { document.getElementById('sug').style.display = 'none'; setAge(540); }); await p.waitForTimeout(600);
    await p.click('#play'); await p.waitForTimeout(4000); await p.click('#play');
    const age = await p.$eval('#ageLab', e => e.textContent);
    for (const id of ['panChart', 'laneChart', 'dinoChart', 'miniMaps', 'cosmoChart', 'latChart', 'extCards', 'contChart']) {
      await p.evaluate(id => document.getElementById(id).scrollIntoView({ block: 'center' }), id); await p.waitForTimeout(400);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_${id}.png` });
    }
    await p.evaluate(() => document.querySelector('#laneMode [data-m=share]').click()); await p.waitForTimeout(300);
    await p.evaluate(() => document.getElementById('laneChart').scrollIntoView({ block: 'center' })); await p.waitForTimeout(300);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_laneShare.png` });
    // dark mode
    await p.evaluate(() => document.getElementById('theme').click()); await p.evaluate(() => setAge(200)); await p.waitForTimeout(900);
    await p.evaluate(() => document.getElementById('atlas').scrollIntoView()); await p.waitForTimeout(300);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_dark_map.png` });
    await p.evaluate(() => document.getElementById('theme').click());
    const fsb = await p.$$eval('.mfs-btn', e => e.length);
    await p.click('.mfs-btn'); await p.waitForTimeout(900);
    await p.screenshot({ path: `${ROOT}/qa/${tag}_fullscreen.png` });
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    console.log(tag, 'fullscreen buttons', fsb, 'scrollWidth', sw, 'age after play', age, '| pop:', popTxt.replace(/\n/g, ' / '), '| search:', sug.slice(0, 120));
    console.log(tag, 'errors', errs.filter(e => !/ERR_|net::|Failed to load resource/.test(e)), 'network errors', errs.filter(e => /ERR_|net::|Failed to load resource/.test(e)).length);
    await p.close();
  }
  await b.close(); srv.close();
})();
