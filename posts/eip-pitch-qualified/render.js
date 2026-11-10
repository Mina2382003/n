// Renders the GEF partner-style flyers. Run: node render.js
const fs = require('fs'), { chromium } = require('playwright');
const posts = {
  personal: { l1: 'Our Founder &amp; CEO', tape: 'Mina Monir', l3: 'is representing' },
  reservya: { l1: 'Proud to be pitching at the', tape: 'Entrepreneurs Investment Program', l3: 'EIP 2026', small: true },
};
const sec = (id, p) => `<section id="${id}">
  <div class="c thin" style="top:150px">${p.l1}</div>
  <div class="c" style="top:226px"><span class="tape"${p.small ? ' style="font-size:44px;padding-top:12px;padding-bottom:16px"' : ''}>${p.tape}</span></div>
  <div class="c thin" style="top:325px">${p.l3}</div>
  <div class="c big" style="top:505px">RESERVYA</div>
  <div class="c ar" style="top:640px">ريزيرفيا</div>
</section>`;
(async () => {
  const html = fs.readFileSync(__dirname + '/flyer.html', 'utf8').replace('<!-- POSTS -->', Object.entries(posts).map(([k, v]) => sec(k, v)).join('\n'));
  fs.writeFileSync(__dirname + '/flyer.built.html', html);
  const b = await chromium.launch(), pg = await b.newPage({ viewport: { width: 1206, height: 1497 } });
  await pg.goto('file://' + __dirname + '/flyer.built.html'); await pg.waitForTimeout(2000);
  for (const id of Object.keys(posts)) await (await pg.$('#' + id)).screenshot({ path: `${__dirname}/${id}.png` });
  await b.close();
})();
