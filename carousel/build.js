// Builds 3 carousels (HTML + PNG per slide) from the content below.
// Run: node build.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const style = fs.readFileSync(path.join(__dirname, 'style.css'), 'utf8');
const fonts = '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">';

const top = (n, total) => `<div class="top"><div class="who"><div class="av">MM</div><div><div class="name">Mina Monir</div><div class="handle">@mina_monir8</div></div></div><div class="num">${String(n).padStart(2, '0')} / ${String(total).padStart(2, '0')}</div></div>`;
const bot = (left, last) => last
  ? `<div class="bot"><span>Mina Monir</span><span>@mina_monir8</span></div>`
  : `<div class="bot"><span>${left || '@mina_monir8'}</span><span class="sw">Swipe →</span></div>`;
const center = html => `<div style="margin-top:auto;margin-bottom:auto">${html}</div>`;

const row = (label, total) => `<div class="row${total ? ' total' : ''}"><span>${label}</span><span class="blank"></span></div>`;
const li = (icon, title, note) => `<div class="li"><div class="ic">${icon}</div><div>${title}${note ? `<small>${note}</small>` : ''}</div></div>`;
const cta = (title, text, comment, save = 'Save it to run your numbers') => center(`
  <h1 style="font-size:92px">${title}</h1>
  <p class="sub" style="margin:40px 0 60px">${text}</p>
  <div style="display:flex;flex-direction:column;gap:22px;font:600 34px Inter">
    <div>🔖 &nbsp;${save}</div>
    <div>💬 &nbsp;${comment}</div>
    <div>➕ &nbsp;Follow <span class="gold">@mina_monir8</span> for more venue economics</div>
  </div>`);

const carousels = {
  '1-cac': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Economics · Part 1</span>
      <h1>Same budget.<br><span class="gold">32% cheaper</span><br>customers.</h1>
      <p class="sub" style="margin-top:44px">The one number that shows if your marketing money is working.</p>`) },
    { theme: 'light', body: `<div class="huge">01</div>` + center(`
      <span class="tag">The equation · CAC</span>
      <h2 style="margin:40px 0 30px">What does one new customer <span class="rose">actually cost you?</span></h2>
      <div class="formula">CAC = Marketing Spend ÷ New Customers</div>
      <p class="sub" style="margin-top:40px">Customer Acquisition Cost. If you don't know this number, you're guessing with your marketing budget.</p>`) },
    { theme: 'light', foot: 'Hypothetical example', body: `
      <h2 style="margin-top:40px;margin-bottom:44px">Your CAC, <span class="rose">before & after</span></h2>
      <div class="cards">
        <div class="card w"><div class="l">Solo marketing</div><div class="m">Spend: EGP 60,000 · New customers: 150</div><div class="big">EGP 400</div></div>
        <div class="card d"><div class="l">On a shared network</div><div class="m">Spend: EGP 60,000 · New customers: 220<br>(shared discovery)</div><div class="big">EGP 273</div></div>
      </div>
      <div class="pill" style="margin-top:36px">↓ 32% lower CAC. Same spend, more people find you.</div>` },
    { theme: 'dark', body: center(`
      <span class="tag">Worksheet · your turn</span>
      <h2 style="margin:40px 0 50px">Now run <span class="gold">your own</span> CAC</h2>
      ${row('Marketing spend last month (EGP)')}${row('New customers won')}${row('CAC = Spend ÷ Customers', true)}
      <p class="sub" style="margin-top:44px;font-size:28px">📸 Screenshot this and fill it in.</p>`) },
    { theme: 'dark', last: true, body: cta('Stop marketing <span class="gold">alone.</span>',
      'Shared discovery means more people find you for the same spend. Next: what each of those customers is worth.',
      'Comment your CAC') },
  ],
  '2-ltv': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Economics · Part 2</span>
      <h1>Same customer.<br><span class="gold">75% more</span><br>value.</h1>
      <p class="sub" style="margin-top:44px">How much is one customer really worth to your venue? Here's the math.</p>`) },
    { theme: 'light', body: `<div class="huge">02</div>` + center(`
      <span class="tag">The equation · LTV</span>
      <h2 style="margin:40px 0 30px">What is one customer <span class="rose">worth over time?</span></h2>
      <div class="formula" style="font-size:34px">LTV = AOV × Repeat orders/yr × Margin × (Lifespan months ÷ 12)</div>
      <p class="sub" style="margin-top:40px">Lifetime Value. AOV is your average order value. The lever most owners ignore is <b>repeat orders</b>.</p>`) },
    { theme: 'light', foot: 'Hypothetical · 12-month lifespan', body: `
      <h2 style="margin-top:40px;margin-bottom:44px">LTV, with <span class="rose">network loyalty</span></h2>
      <div class="cards">
        <div class="card w"><div class="l">Standalone app</div><div class="m">AOV 300 × 4 repeats/yr × 30% margin</div><div class="big">EGP 360</div></div>
        <div class="card d"><div class="l">On a shared network</div><div class="m">AOV 300 × 7 repeats/yr × 30% margin</div><div class="big">EGP 630</div></div>
      </div>
      <div class="pill" style="margin-top:36px">↑ +75% lifetime value. Loyalty carries across every partner venue.</div>` },
    { theme: 'dark', body: center(`
      <span class="tag">Worksheet · your turn</span>
      <h2 style="margin:40px 0 40px">Now run <span class="gold">your own</span> LTV</h2>
      ${row('Average order value (EGP)')}${row('Repeat orders per year')}${row('Gross margin (%)')}${row('Customer lifespan (months)')}${row('LTV', true)}`) },
    { theme: 'dark', last: true, body: cta('Repeat visits <span class="gold">are the business.</span>',
      'Same order value, same margin. The only thing that changed is how often they come back.',
      'Comment your LTV') },
  ],
  '3-ratio': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Economics · Part 3</span>
      <h1>Is your growth<br><span class="gold">losing you<br>money?</span></h1>
      <p class="sub" style="margin-top:44px">One ratio tells you. Most venue owners have never calculated it.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Quick recap</span>
      <h2 style="margin:40px 0 44px">Two numbers you <span class="rose">need first</span></h2>
      <div class="cards">
        <div class="card w"><div class="l">CAC · what a customer costs</div><div class="m">Marketing Spend ÷ New Customers</div></div>
        <div class="card d"><div class="l">LTV · what a customer is worth</div><div class="m">AOV × Repeats/yr × Margin × (Lifespan ÷ 12)</div></div>
      </div>
      <p class="sub" style="margin-top:40px;font-size:30px">Missed them? Parts 1 & 2 are on my profile.</p>`) },
    { theme: 'light', foot: 'Hypothetical example', body: center(`
      <span class="tag">Put them together</span>
      <h2 style="margin:40px 0 44px">The number that <span class="rose">actually matters</span>: LTV ÷ CAC</h2>
      <div class="ratio">
        <div style="background:#fff"><div style="font:700 28px Inter;color:var(--rose)">Solo</div><div class="v rose">0.9×</div><div style="font:500 26px/1.45 Inter;opacity:.75">360 ÷ 400<br>You lose money on every new customer.</div></div>
        <div style="background:var(--ink);color:var(--cream)"><div style="font:700 28px Inter;color:var(--gold)">Network</div><div class="v gold">2.3×</div><div style="font:500 26px/1.45 Inter;opacity:.75">630 ÷ 273<br>Every EGP 1 spent comes back as EGP 2.3.</div></div>
      </div>`) },
    { theme: 'dark', body: center(`
      <span class="tag">Read your ratio</span>
      <h2 style="margin:40px 0 50px">Where do <span class="gold">you</span> land?</h2>
      <div class="row"><span><b>Below 1×</b></span><span style="opacity:.8">Growth is costing you money</span></div>
      <div class="row"><span><b>1× – 3×</b></span><span style="opacity:.8">Surviving, not scaling</span></div>
      <div class="row total"><span>3× or more</span><span>Healthy. Spend more.</span></div>
      <p class="sub" style="margin-top:44px;font-size:30px">Two levers move it: lower CAC (shared discovery) and higher LTV (repeat visits).</p>`) },
    { theme: 'dark', last: true, body: cta('Stop marketing <span class="gold">alone.</span>',
      'If your LTV:CAC is under 3×, your problem isn\'t the budget. It\'s discovery and repeat visits.',
      'Comment your LTV:CAC ratio') },
  ],
  '4-google-reviews': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Marketing</span>
      <h1>Your Google reviews are a <span class="gold">free customer survey.</span></h1>
      <p class="sub" style="margin-top:44px">What restaurants can learn from them, what they can't, and how to use it.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">What you can see</span>
      <h2 style="margin:40px 0 30px">Every review in your <span class="rose">Google Business Profile</span> shows:</h2>
      ${li('⭐', 'Star rating')}${li('💬', 'Written comment')}${li('📅', 'Date')}${li('📷', 'Photos')}${li('👤', "Reviewer's public name")}`) },
    { theme: 'dark', body: center(`
      <span class="tag">What you can't see</span>
      <h2 style="margin:40px 0 30px">Google <span class="gold">doesn't share</span> reviewers' emails.</h2>
      <p class="sub">So you can't pull emails from reviews to run campaigns. To build a list, ask customers directly and get their permission:</p>
      <div style="margin-top:20px">${li('📲', 'Bookings')}${li('🎁', 'Loyalty programs')}${li('📶', 'Wi-Fi sign-ups')}</div>`) },
    { theme: 'light', body: center(`
      <span class="tag">What the data tells you</span>
      <h2 style="margin:40px 0 36px">Read reviews <span class="rose">like data</span></h2>
      <div class="ratio">
        <div style="background:#fff"><div style="font:700 28px Inter;color:var(--rose)">What they love</div><div style="font:600 30px/1.4 Inter;margin-top:14px">"That pasta is the best in town"</div></div>
        <div style="background:var(--ink);color:var(--cream)"><div style="font:700 28px Inter;color:var(--gold)">What annoys them</div><div style="font:600 30px/1.4 Inter;margin-top:14px">"Waited 40 min for our food"</div></div>
      </div>
      <p style="font:700 28px Inter;margin:40px 0 18px">Repeated words show who your customers are:</p>
      <div class="chips"><span class="chip">family</span><span class="chip">date night</span><span class="chip">business lunch</span></div>
      <p class="sub" style="margin-top:34px;font-size:28px">Busy dates and review languages show who visits, and when.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">How to use it</span>
      <h2 style="margin:40px 0 30px">Turn feedback into <span class="rose">action</span></h2>
      ${li('🍽️', 'Improve food & service', 'Fix what keeps coming up')}${li('🧑‍🍳', 'Train your staff', 'Use real comments as examples')}${li('🔥', 'Highlight popular dishes', 'Put the favourites front and centre')}${li('🎯', 'Aim your ads', 'At the customers who already love you')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">Why it pays off</span>
      <h2 style="margin:40px 0 30px">More reviews + replies = <span class="gold">more bookings</span></h2>
      ${li('1', 'Rank higher', 'In Google Search & Maps')}${li('2', 'Get found more easily', 'By people searching nearby')}${li('3', 'Build trust', 'With customers who\'ve never visited')}${li('4', 'Fill more tables', 'More visibility, more bookings')}`) },
    { theme: 'dark', last: true, body: cta('Reply to <span class="gold">every review.</span>',
      'Good or bad, every reply shows new customers you\'re listening, and helps you rank higher.',
      'Comment the word your reviews mention most', 'Save this for your next review check') },
  ],
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const [name, slides] of Object.entries(carousels)) {
    const dir = path.join(__dirname, name);
    fs.mkdirSync(dir, { recursive: true });
    const html = `<!doctype html><html><head><meta charset="utf-8">${fonts}<style>${style}</style></head><body>` +
      slides.map((s, i) => `<section class="slide ${s.theme}">${top(i + 1, slides.length)}${s.body}${bot(s.foot, s.last)}</section>`).join('\n') +
      '</body></html>';
    const file = path.join(dir, 'carousel.html');
    fs.writeFileSync(file, html);
    await page.goto('file://' + file, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const els = await page.$$('.slide');
    for (let i = 0; i < els.length; i++)
      await els[i].screenshot({ path: path.join(dir, `slide-${String(i + 1).padStart(2, '0')}.png`) });
  }
  await browser.close();
})();
