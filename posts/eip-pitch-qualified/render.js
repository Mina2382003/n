const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  await p.goto('file://' + __dirname + '/posts.html'); await p.waitForTimeout(1500);
  for (const id of ['personal', 'reservya']) await (await p.$('#' + id)).screenshot({ path: `${__dirname}/${id}.png` });
  await b.close();
})();
