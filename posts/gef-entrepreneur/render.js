// Renders poster.html to mina-monir-entrepreneur.png. Run: node render.js
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(), pg = await b.newPage({ viewport: { width: 1174, height: 1494 }, deviceScaleFactor: 1 });
  await pg.goto('file://' + __dirname + '/poster.html'); await pg.waitForTimeout(2000);
  await (await pg.$('#poster')).screenshot({ path: __dirname + '/mina-monir-entrepreneur.png' });
  await b.close();
})();
