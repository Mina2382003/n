// Builds 4 rate-card designs (HTML + PNG each) and one combined PDF.
// Run: node build.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const me = {
  name: 'Mina Monir',
  first: 'Mina', last: 'Monir',
  handle: '@mina_monir8',
  role: 'UGC Creator · Founder, Reservya',
  niche: 'Hospitality · F&B · Business',
  platforms: 'Instagram + TikTok',
  contact: 'DM @mina_monir8 on Instagram',
};

const packages = [
  { n: '01', title: 'Product Review', price: '10,000', items: ['1 Reel (Instagram + TikTok)', '4+ Stories'] },
  { n: '02', title: 'Event Attendance + Coverage', price: '15,000', items: ['1 Reel (Instagram + TikTok)', '4+ Stories'] },
  { n: '03', title: 'Event Coverage + Product Review', price: '20,000', items: ['2 Reels: review + event recap (Instagram + TikTok)', '4+ Stories'], best: true },
];

const why = ['Founder voice: real business, real audience', 'Arabic & English content', 'Scroll-stopping hooks, edited in-house'];

const fonts = '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,500;1,600&family=Inter:wght@400;500;600;700;800;900&family=Archivo+Black&display=swap" rel="stylesheet">';
const base = `*{box-sizing:border-box;margin:0;padding:0}body{background:#111}.card{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:Inter,sans-serif}`;

// 1. Signature: brand burgundy + gold, photo panel on the right.
const signature = () => `
<style>
:root{--ink:#2a1013;--ink2:#3a181c;--cream:#f3ebe1;--gold:#d9a64e;--pink:#e2bcbd;--rose:#7a2e33}
.card{background:var(--ink);color:var(--cream)}
.ph{position:absolute;right:0;top:0;width:430px;height:100%;object-fit:cover;object-position:52% 30%}
.ph-fade{position:absolute;right:0;top:0;width:430px;height:100%;background:linear-gradient(90deg,var(--ink) 0%,rgba(42,16,19,.15) 35%,rgba(42,16,19,0) 60%)}
.in{position:absolute;left:80px;top:80px;width:620px;bottom:80px;display:flex;flex-direction:column}
.kick{font:800 18px Inter;letter-spacing:5px;color:var(--gold);text-transform:uppercase}
h1{font:800 104px/0.95 'Playfair Display',serif;margin-top:22px}
h1 i{font-weight:600;color:var(--gold)}
.role{font:500 24px Inter;opacity:.75;margin-top:22px}
.tag{display:inline-block;margin-top:22px;padding:10px 20px;border:2px solid var(--gold);border-radius:40px;font:700 17px Inter;letter-spacing:2px;color:var(--gold);align-self:flex-start;text-transform:uppercase}
.list{margin-top:48px;display:flex;flex-direction:column;gap:20px}
.pk{background:var(--ink2);border-radius:22px;padding:28px 32px;border:1.5px solid rgba(217,166,78,.25);position:relative}
.pk.best{border:2.5px solid var(--gold)}
.pk .best-tag{position:absolute;top:-15px;right:24px;background:var(--gold);color:var(--ink);font:800 14px Inter;letter-spacing:2px;padding:6px 14px;border-radius:20px}
.pk .t{display:flex;justify-content:space-between;align-items:baseline;gap:16px}
.pk .nm{font:700 27px Inter}
.pk .pr{font:800 34px Inter;color:var(--gold);white-space:nowrap}.pk .pr small{font:700 16px Inter;opacity:.8;margin-left:6px}
.pk ul{list-style:none;margin-top:12px;font:500 19px/1.6 Inter;opacity:.75}
.pk li:before{content:'— ';color:var(--gold)}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font:600 19px Inter}
.foot .c{color:var(--gold)}.foot .s{opacity:.55;font-weight:500}
</style>
<div class="card">
<img class="ph" src="img/mina-black.jpg"><div class="ph-fade"></div>
<div class="in">
  <div class="kick">UGC Rate Card · 2026</div>
  <h1>${me.first}<br><i>${me.last}</i></h1>
  <div class="role">${me.role}</div>
  <div class="tag">${me.niche}</div>
  <div class="list">${packages.map(p => `
    <div class="pk${p.best ? ' best' : ''}">${p.best ? '<span class="best-tag">BEST VALUE</span>' : ''}
      <div class="t"><span class="nm">${p.title}</span><span class="pr">${p.price}<small>EGP</small></span></div>
      <ul>${p.items.map(i => `<li>${i}</li>`).join('')}</ul>
    </div>`).join('')}
  </div>
  <div class="foot"><div><div class="s">Let's work together</div><div class="c" style="margin-top:6px">${me.contact}</div></div></div>
</div>
</div>`;

// 2. Editorial: cream magazine layout, big serif, photo masthead.
const editorial = () => `
<style>
:root{--ink:#2a1013;--cream:#f3ebe1;--gold:#b8862f;--rose:#7a2e33;--line:rgba(42,16,19,.18)}
.card{background:var(--cream);color:var(--ink)}
.top{position:absolute;left:0;right:0;top:0;height:470px;overflow:hidden}
.top img{width:100%;height:100%;object-fit:cover;object-position:50% 8%}
.top:after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(42,16,19,0) 70%,rgba(42,16,19,.35) 100%)}
.mast{position:absolute;left:70px;right:70px;top:505px;z-index:2;color:var(--ink);display:flex;justify-content:space-between;align-items:flex-end}
.mast .k{font:700 17px Inter;letter-spacing:5px;text-transform:uppercase;color:var(--gold)}
.mast h1{font:800 88px/1 'Playfair Display',serif;margin-top:8px}
.mast .h{font:600 22px Inter;text-align:right;line-height:1.5}
.mast .h span{display:block;opacity:.6;font-weight:500;font-size:19px}
.body{position:absolute;left:70px;right:70px;top:650px;bottom:60px;display:flex;flex-direction:column}
.intro{font:500 italic 30px/1.35 'Playfair Display',serif;color:var(--rose)}
.rows{margin-top:30px;border-top:2px solid var(--ink)}
.row{display:grid;grid-template-columns:80px 1fr auto;gap:20px;padding:26px 0;border-bottom:1px solid var(--line);align-items:start}
.row .n{font:700 italic 44px/1 'Playfair Display',serif;color:var(--gold)}
.row .nm{font:700 28px Inter}
.row .d{font:500 19px/1.55 Inter;opacity:.7;margin-top:8px}
.row .pr{font:800 40px 'Playfair Display',serif;text-align:right;white-space:nowrap}
.row .pr small{display:block;font:700 14px Inter;letter-spacing:3px;color:var(--gold)}
.row .star{display:inline-block;margin-left:12px;font:800 13px Inter;letter-spacing:2px;background:var(--rose);color:var(--cream);padding:5px 10px;border-radius:4px;vertical-align:middle}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font:600 19px Inter;padding-top:20px}
.whys{display:flex;flex-wrap:wrap;gap:12px;margin-top:34px}.whys span{font:600 17px Inter;padding:10px 18px;border:1.5px solid var(--ink);border-radius:30px}
.foot .c{background:var(--ink);color:var(--cream);padding:14px 26px;border-radius:40px}
</style>
<div class="card">
<div class="top"><img src="img/mina-white.jpg"></div>
<div class="mast"><div><div class="k">Collaboration Rates</div><h1>${me.name}</h1></div><div class="h">${me.handle}<span>${me.platforms}</span></div></div>
<div class="body">
  <div class="intro">Founder-led content for brands in hospitality, food & business.</div>
  <div class="rows">${packages.map(p => `
    <div class="row"><div class="n">${p.n}</div>
      <div><div class="nm">${p.title}${p.best ? '<span class="star">BEST VALUE</span>' : ''}</div><div class="d">${p.items.join(' · ')}</div></div>
      <div class="pr">${p.price}<small>EGP</small></div></div>`).join('')}
  </div>
  <div class="whys">${why.map(w => `<span>${w}</span>`).join('')}</div>
  <div class="foot"><span style="opacity:.6">Custom packages on request</span><span class="c">${me.contact}</span></div>
</div>
</div>`;

// 3. Noir: black luxury, gold hairlines, centred pricing table.
const noir = () => `
<style>
:root{--bg:#0d0d0d;--gold:#d9a64e;--txt:#f4efe7;--mut:rgba(244,239,231,.55)}
.card{background:var(--bg);color:var(--txt)}
.frame{position:absolute;inset:36px;border:1px solid rgba(217,166,78,.45)}
.in{position:absolute;inset:90px 96px;display:flex;flex-direction:column;align-items:center;text-align:center}
.av{width:170px;height:170px;border-radius:50%;overflow:hidden;border:3px solid var(--gold)}
.av img{width:100%;height:100%;object-fit:cover;object-position:50% 20%;transform:scale(1.9);transform-origin:50% 14%}
.k{font:600 16px Inter;letter-spacing:8px;color:var(--gold);margin-top:34px;text-transform:uppercase}
h1{font:700 76px/1 'Playfair Display',serif;margin-top:16px;letter-spacing:1px}
.sub{font:500 21px Inter;color:var(--mut);margin-top:14px;letter-spacing:1px}
.rule{width:100%;display:flex;align-items:center;gap:20px;margin:44px 0 10px;color:var(--gold);font:600 15px Inter;letter-spacing:6px}
.rule:before,.rule:after{content:'';flex:1;height:1px;background:rgba(217,166,78,.5)}
.pk{width:100%;display:flex;justify-content:space-between;align-items:center;padding:40px 0;border-bottom:1px solid rgba(244,239,231,.1);text-align:left}
.pk:last-child{border-bottom:0}
.pk .nm{font:600 28px 'Playfair Display',serif}
.pk .nm em{font:700 13px Inter;font-style:normal;letter-spacing:2px;color:var(--bg);background:var(--gold);padding:4px 10px;margin-left:12px;vertical-align:middle}
.pk .d{font:400 18px/1.6 Inter;color:var(--mut);margin-top:6px}
.pk .pr{font:300 46px Inter;letter-spacing:-1px;white-space:nowrap;margin-left:24px}.pk .pr small{font:600 14px Inter;letter-spacing:3px;color:var(--gold);margin-left:8px}
.whys{width:100%;display:flex;flex-direction:column;gap:14px;margin-top:20px;font:500 21px Inter;text-align:left}.whys span{color:var(--gold);margin-right:14px}
.foot{margin-top:auto;font:500 18px Inter;color:var(--mut);letter-spacing:1px}
.foot b{color:var(--gold);font-weight:600}
</style>
<div class="card"><div class="frame"></div>
<div class="in">
  <div class="av"><img src="img/mina-white.jpg"></div>
  <div class="k">UGC · Rate Card</div>
  <h1>${me.name}</h1>
  <div class="sub">${me.role}</div>
  <div class="rule">PACKAGES</div>
  <div style="width:100%">${packages.map(p => `
    <div class="pk"><div><div class="nm">${p.title}${p.best ? '<em>BEST VALUE</em>' : ''}</div><div class="d">${p.items.join(' &nbsp;·&nbsp; ')}</div></div>
    <div class="pr">${p.price}<small>EGP</small></div></div>`).join('')}
  </div>
  <div class="rule">WHY ME</div>
  <div class="whys">${why.map(w => `<div><span>✦</span>${w}</div>`).join('')}</div>
  <div class="foot">${me.platforms} &nbsp;·&nbsp; <b>${me.contact}</b></div>
</div></div>`;

// 4. Bold: high-energy gold block, chunky type, stacked price tiles.
const bold = () => `
<style>
:root{--y:#f2b73a;--ink:#1a0b0d;--rose:#7a2e33;--cream:#fff8ec}
.card{background:var(--y);color:var(--ink)}
.ph{position:absolute;right:-40px;top:0;width:520px;height:690px;object-fit:cover;object-position:50% 20%;
  -webkit-mask-image:linear-gradient(180deg,#000 75%,transparent 100%)}
.in{position:absolute;inset:70px 70px 60px;display:flex;flex-direction:column}
.chip{align-self:flex-start;background:var(--ink);color:var(--y);font:800 17px Inter;letter-spacing:3px;padding:10px 18px;border-radius:6px}
h1{font:400 128px/0.88 'Archivo Black',Inter,sans-serif;margin-top:30px;letter-spacing:-3px;text-transform:uppercase}
.h{font:800 26px Inter;margin-top:24px}
.n{font:600 21px Inter;margin-top:6px;opacity:.75;max-width:460px}
.tiles{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:18px}
.tile{background:var(--ink);color:var(--cream);border-radius:26px;padding:30px 30px 28px;display:flex;flex-direction:column}
.tile.best{grid-column:1 / -1;background:var(--rose)}
.tile .nm{font:800 25px/1.2 Inter}
.tile ul{list-style:none;font:500 18px/1.55 Inter;opacity:.8;margin-top:10px}
.tile li:before{content:'✓ ';color:var(--y)}
.tile .pr{font:400 52px 'Archivo Black',Inter;color:var(--y);margin-top:auto;padding-top:14px}.tile .pr small{font:800 18px Inter;margin-left:8px}
.tile.best .row{display:flex;justify-content:space-between;align-items:flex-end;gap:20px}
.flag{display:inline-block;background:var(--y);color:var(--ink);font:800 13px Inter;letter-spacing:2px;padding:5px 10px;border-radius:4px;margin-bottom:10px;align-self:flex-start}
.foot{display:flex;justify-content:space-between;font:800 20px Inter;margin-top:22px}
</style>
<div class="card">
<img class="ph" src="img/mina-black.jpg">
<div class="in">
  <div class="chip">UGC RATES · EGP</div>
  <h1>Work<br>with<br>Mina</h1>
  <div class="h">${me.handle}</div>
  <div class="n">${me.role}<br>${me.niche}</div>
  <div class="tiles">${packages.map(p => p.best ? `
    <div class="tile best"><span class="flag">BEST VALUE</span><div class="row"><div><div class="nm">${p.title}</div><ul>${p.items.map(i => `<li>${i}</li>`).join('')}</ul></div>
      <div class="pr" style="padding:0;white-space:nowrap">${p.price}<small>EGP</small></div></div></div>` : `
    <div class="tile"><div class="nm">${p.title}</div><ul>${p.items.map(i => `<li>${i}</li>`).join('')}</ul><div class="pr">${p.price}<small>EGP</small></div></div>`).join('')}
  </div>
  <div class="foot"><span>${me.platforms}</span><span>${me.contact}</span></div>
</div></div>`;

const designs = { '1-signature': signature, '2-editorial': editorial, '3-noir': noir, '4-bold': bold };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  let all = '';
  for (const [name, fn] of Object.entries(designs)) {
    const html = `<!doctype html><html><head><meta charset="utf-8">${fonts}<style>${base}</style></head><body>${fn()}</body></html>`;
    const file = path.join(__dirname, `${name}.html`);
    fs.writeFileSync(file, html);
    await page.goto('file://' + file);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(__dirname, `${name}.png`), clip: { x: 0, y: 0, width: 1080, height: 1350 } });
    all += `<div style="page-break-after:always"><img src="${name}.png" style="width:1080px;height:1350px;display:block"></div>`;
    console.log('built', name);
  }
  const pdfHtml = path.join(__dirname, '.pdf.html');
  fs.writeFileSync(pdfHtml, `<!doctype html><html><head><style>@page{size:1080px 1350px;margin:0}body{margin:0}</style></head><body>${all}</body></html>`);
  await page.goto('file://' + pdfHtml);
  await page.pdf({ path: path.join(__dirname, 'Mina Monir - UGC Rate Cards.pdf'), width: '1080px', height: '1350px', printBackground: true });
  fs.unlinkSync(pdfHtml);
  await browser.close();
})();
