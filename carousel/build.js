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
const img = (name, pos) => `<img src="img/${name}.jpg" style="object-position:${pos}">`;
const bg = (name, pos) => `<img class="photo" src="img/${name}.jpg" style="object-position:${pos}"><div class="shade"></div>`;
const bottom = html => `<div style="margin-top:auto;position:relative">${html}</div>`;
// Nested-ellipse "journey" diagram: every stage shares the left edge, each ring wraps the one before.
const journey = (stages) => {
  const L = 90, CY = 470, rings = [[160, 230], [270, 300], [370, 350], [450, 390]];
  const edge = (i, dy, side) => { const [rx, ry] = rings[i]; const k = Math.sqrt(Math.max(0, 1 - (dy / ry) ** 2)); return L + rx + side * rx * k; };
  let s = `<svg width="1080" height="830" viewBox="0 60 1080 830" style="margin:0 -90px;display:block">`;
  rings.forEach(([rx, ry], i) => {
    s += `<ellipse cx="${L + rx}" cy="${CY}" rx="${rx}" ry="${ry}" fill="none" stroke="${i === 3 ? 'var(--gold)' : 'rgba(243,235,225,.85)'}" stroke-width="${i === 3 ? 4 : 2.5}"/>`;
  });
  s += `<line x1="${L}" y1="${CY}" x2="1035" y2="${CY}" stroke="var(--cream)" stroke-width="3"/><circle cx="${L}" cy="${CY}" r="11" fill="var(--cream)"/><path d="M1030 ${CY - 12} L1052 ${CY} L1030 ${CY + 12}Z" fill="var(--cream)"/>`;
  const centers = [250, 520, 730, 910];
  stages.forEach((st, i) => {
    const w = st.label.length * 30 + 20;
    s += `<rect x="${centers[i] - w / 2}" y="${CY - 30}" width="${w}" height="60" fill="var(--ink)"/>`;
    s += `<text x="${centers[i]}" y="${CY + 16}" text-anchor="middle" font-family="Inter" font-weight="800" font-size="40" fill="var(--gold)">${st.label}</text>`;
    const dys = i === 0 ? [-160, -80, 70, 150] : i === 3 ? [-195, -100, 85, 175] : [-215, -110, 85, 190];
    st.items.forEach((lines, j) => {
      const dy = dys[j];
      const x = i === 0 ? edge(0, dy, -1) + 30 : edge(i - 1, dy, 1) + 22;
      s += `<circle cx="${x}" cy="${CY + dy - 7}" r="5" fill="var(--gold)"/>`;
      s += `<text x="${x + 16}" y="${CY + dy}" font-family="Inter" font-weight="500" font-size="23" fill="var(--cream)">` +
        lines.map((t, k) => `<tspan x="${x + 16}" dy="${k ? 28 : 0}">${t}</tspan>`).join('') + `</text>`;
    });
  });
  return s + `</svg>`;
};
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
  '5-hace-expo': [
    { theme: 'dark', foot: 'Event diary', body: `${bg('badge', '50% 40%')}` + bottom(`
      <span class="tag" style="margin-bottom:36px;display:inline-block">Event diary · HACE Hotel Expo</span>
      <h1>A day at <span class="gold">HACE Hotel Expo</span> ☕</h1>
      <p class="sub" style="margin-top:30px">The coffee, the tech and the ideas worth stealing for your venue.</p>`) },
    { theme: 'dark', body: `${bg('arrival', '70% 30%')}` + bottom(`
      <span class="tag">Arrival</span>
      <h2 style="margin:34px 0 24px">Hotels, restaurants, cafés, <span class="gold">and everyone who supplies them.</span></h2>
      <p class="sub">One hall, a full day, and a lot of espresso.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Coffee pick #1</span>
      <div class="pic" style="height:640px;margin:34px 0 36px">${img('kimbo', '50% 50%')}</div>
      <h2><span class="rose">Kimbo</span>, il caffè di Napoli</h2>
      <p class="sub" style="margin-top:20px">Italian espresso brand from Naples. My cappuccino of the day came in this cup.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Coffee pick #2</span>
      <div class="pic" style="height:640px;margin:34px 0 36px">${img('frusta', '50% 30%')}</div>
      <h2><span class="rose">Frusta</span> coffee machines</h2>
      <p class="sub" style="margin-top:20px">Compact espresso machines with one simple promise: quality coffee at the press of a button.</p>`) },
    { theme: 'dark', body: `${bg('barista', '50% 40%')}` + bottom(`
      <span class="tag">Don't miss</span>
      <h2 style="margin:34px 0 24px">The <span class="gold">Barista Clash</span> competition</h2>
      <p class="sub">Baristas going head to head, right at the hall entrance. Coffee is a craft, and the crowd shows it.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Beyond coffee</span>
      <h2 style="margin:34px 0 40px">What else <span class="rose">caught my eye</span></h2>
      <div style="display:flex;gap:22px">
        <div style="flex:1"><div class="pic" style="height:500px">${img('unox', '30% 50%')}</div><p class="cap">UNOX live oven demo</p></div>
        <div style="flex:1"><div class="pic" style="height:500px">${img('robot', '50% 50%')}</div><p class="cap">Serving robots</p></div>
        <div style="flex:1"><div class="pic" style="height:500px">${img('dreem', '35% 50%')}</div><p class="cap">Dreem Food Services</p></div>
      </div>`) },
    { theme: 'dark', last: true, body: cta('Great coffee is now <span class="gold">a selling point.</span>',
      'From Kimbo in the cup to Frusta on the counter, guests notice what you serve. And kitchens are getting smarter, fast.',
      'Which one would you put in your venue?', 'Save this for your next café upgrade') },
  ],
  '6-hiring-sales': [
    { theme: 'dark', foot: 'Share with someone job hunting', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Now hiring · Reservya</span>
      <h1>We're hiring <span class="gold">sales</span> in Alexandria & Cairo 📍</h1>
      <p class="sub" style="margin-top:44px">Looking for a job in hospitality in Egypt? Swipe. This might be your next step.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Who we are</span>
      <h2 style="margin:40px 0 30px">What is <span class="rose">Reservya?</span></h2>
      <p class="sub" style="font-size:36px">A network that helps restaurants, cafés and venues get discovered by more guests and turn them into regulars.</p>
      <div class="pill" style="margin-top:44px">I'm Mina, CEO of Reservya. I'm building the sales team myself.</div>`) },
    { theme: 'dark', body: center(`
      <span class="tag">The role</span>
      <h2 style="margin:40px 0 30px">Sales Executive</h2>
      <p class="sub" style="margin-bottom:24px">You'll be the face of Reservya to venue owners in your city.</p>
      ${li('🤝', 'Meet restaurant & café owners', 'Visit venues and build real relationships')}${li('📱', 'Show them Reservya', 'Explain how the network brings them more guests')}${li('✍️', 'Sign new partners', 'And help them succeed after they join')}${li('📈', 'Grow your city', 'Help build our network in Alex or Cairo')}`) },
    { theme: 'light', body: center(`
      <span class="tag">Where</span>
      <h2 style="margin:40px 0 44px">Two cities, <span class="rose">open now</span></h2>
      <div class="cards">
        <div class="card d"><div class="l">📍 Alexandria</div><div class="m">Sales Executive · Field sales</div></div>
        <div class="card w"><div class="l">📍 Cairo</div><div class="m">Sales Executive · Field sales</div></div>
      </div>
      <p class="sub" style="margin-top:40px;font-size:30px">Live in or near the city you apply for.</p>`) },
    { theme: 'dark', body: center(`
      <span class="tag">Who we're looking for</span>
      <h2 style="margin:40px 0 30px">You might be a fit if you…</h2>
      ${li('☕', 'Love hospitality', 'You notice what makes a great restaurant great')}${li('🗣️', 'Talk easily with people', 'Confident in Arabic, English is a plus')}${li('🚀', 'Drive yourself', 'You don\'t wait to be told what to do next')}${li('🎯', 'Like targets', 'Sales or F&B experience is a plus, not a must')}`) },
    { theme: 'light', body: center(`
      <span class="tag">What you get</span>
      <h2 style="margin:40px 0 30px">More than <span class="rose">a job title</span></h2>
      ${li('🧠', 'Learn hospitality from the inside', 'How venues really make money')}${li('👋', 'Work directly with me', 'Not five layers away from decisions')}${li('🌐', 'Build your network', 'Venue owners across your whole city')}${li('🌱', 'Grow with us', 'Join early and grow as the team grows')}`) },
    { theme: 'light', body: center(`
      <span class="tag">Not for you? Still useful</span>
      <h2 style="margin:40px 0 30px">4 tips to land <span class="rose">any hospitality job</span> in Egypt</h2>
      ${li('1', 'Know the venues', 'Visit them. Mention one by name in your interview')}${li('2', 'Show numbers', '"Served 200 covers a night" beats "hard worker"')}${li('3', 'Clean up your profiles', 'Recruiters check LinkedIn and Instagram')}${li('4', 'Follow up in 48 hours', 'A short, polite message gets you remembered')}`) },
    { theme: 'dark', last: true, body: center(`
      <span class="tag" style="margin-bottom:40px;display:inline-block">How to apply</span>
      <h1 style="font-size:96px">DM me <span class="gold">"SALES"</span> + your city 📩</h1>
      <p class="sub" style="margin:40px 0 60px">I'll reply with the next steps. Alexandria or Cairo.</p>
      <div style="display:flex;flex-direction:column;gap:22px;font:600 34px Inter">
        <div>🔁 &nbsp;Share this with someone looking for work</div>
        <div>🏷️ &nbsp;Tag a friend who'd be great at this</div>
        <div>➕ &nbsp;Follow <span class="gold">@mina_monir8</span> for hospitality careers</div>
      </div>`) },
  ],
  '7-hiring-short': [
    { theme: 'dark', foot: 'Share with someone job hunting', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Now hiring · Reservya</span>
      <h1>We're hiring <span class="gold">sales</span> in Alexandria & Cairo 📍</h1>
      <p class="sub" style="margin-top:44px">Looking for a job in hospitality in Egypt? Swipe.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">The role · Sales Executive</span>
      <h2 style="margin:40px 0 30px">Be the face of <span class="rose">Reservya</span> in your city</h2>
      ${li('🤝', 'Meet restaurant & café owners')}${li('📱', 'Show them how Reservya brings more guests')}${li('✍️', 'Sign new partner venues')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">You might be a fit if you…</span>
      <h2 style="margin:40px 0 30px">Love hospitality and <span class="gold">love people</span></h2>
      ${li('🗣️', 'Talk easily with people', 'Arabic, English is a plus')}${li('🚀', 'Drive yourself')}${li('🎯', 'Like targets', 'Sales or F&B experience is a plus, not a must')}`) },
    { theme: 'dark', last: true, body: center(`
      <span class="tag" style="margin-bottom:40px;display:inline-block">How to apply</span>
      <h1 style="font-size:96px">DM me <span class="gold">"SALES"</span> + your city 📩</h1>
      <p class="sub" style="margin:40px 0 60px">Alexandria or Cairo. I'll reply with the next steps.</p>
      <div style="display:flex;flex-direction:column;gap:22px;font:600 34px Inter">
        <div>🔁 &nbsp;Share this with someone looking for work</div>
        <div>➕ &nbsp;Follow <span class="gold">@mina_monir8</span> for hospitality careers</div>
      </div>`) },
  ],
  '8-data-journey': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Data · 4 levels</span>
      <h1>Your restaurant is <span class="gold">sitting on data.</span><br>Are you using it?</h1>
      <p class="sub" style="margin-top:44px">The 4 levels every restaurant goes through, from the first booking to real growth.</p>`) },
    { theme: 'dark', body: `
      <div style="text-align:center;margin-top:40px">
        <div style="font:800 64px/1.05 Inter;letter-spacing:-1px"><span class="gold">THE RESTAURANT</span> DATA JOURNEY</div>
        <div style="font:400 30px Inter;letter-spacing:6px;margin-top:16px;opacity:.9">FROM FIRST BOOKING TO GROWTH</div>
      </div>
      <div style="margin-top:30px">${journey([
        { label: 'TRACK', items: [['Log every', 'booking'], ['Capture guest', 'contacts (opt-in)'], ['Record sales', 'by dish'], ['Read every', 'review']] },
        { label: 'LEARN', items: [['Peak & quiet', 'hours'], ['Best & worst', 'dishes'], ['New vs repeat', 'guests'], ['No-show', 'rate']] },
        { label: 'ACT', items: [['Fill quiet', 'hours'], ['Fix the', 'menu'], ['Staff to', 'demand'], ['Reply to', 'reviews']] },
        { label: 'GROW', items: [['Win back', 'regulars'], ['Loyalty', 'rewards'], ['Smarter', 'ads'], ['Know', 'your LTV']] },
      ])}</div>` },
    { theme: 'light', body: `<div class="huge" style="opacity:.18">01</div>` + center(`
      <span class="tag">Level 1 · Track</span>
      <h2 style="margin:40px 0 30px">You can't fix what you <span class="rose">don't measure</span></h2>
      ${li('📅', 'Every booking & walk-in', 'Date, time, party size')}${li('📲', 'Guest contacts, with permission', 'Via bookings, loyalty or Wi-Fi sign-ups')}${li('🧾', 'Sales by dish & by shift', 'Straight from your POS')}${li('⭐', 'Reviews & no-shows', 'Every one, every week')}`) },
    { theme: 'light', body: `<div class="huge" style="opacity:.18">02</div>` + center(`
      <span class="tag">Level 2 · Learn</span>
      <h2 style="margin:40px 0 30px">Turn records into <span class="rose">answers</span></h2>
      ${li('⏰', 'When are we full, and when empty?', 'Your peak and dead hours')}${li('🍽️', 'Which dishes make money?', 'And which just take up menu space')}${li('🔁', 'How many guests come back?', 'New vs repeat, month by month')}${li('💬', 'What do reviews keep saying?', 'The praise and the complaints')}`) },
    { theme: 'dark', body: `<div class="huge" style="opacity:.22">03</div>` + center(`
      <span class="tag">Level 3 · Act</span>
      <h2 style="margin:40px 0 30px">One insight, <span class="gold">one change</span></h2>
      ${li('📉', 'Quiet Tuesday?', 'Run a weekday offer')}${li('💸', 'Low-margin dish?', 'Reprice it or cut it')}${li('👥', 'Packed Friday?', 'Add staff to that shift')}${li('🔁', 'Same complaint 3 times?', 'Train the team on it this week')}`) },
    { theme: 'dark', body: `<div class="huge" style="opacity:.22">04</div>` + center(`
      <span class="tag">Level 4 · Grow</span>
      <h2 style="margin:40px 0 30px">Data that <span class="gold">brings guests back</span></h2>
      ${li('👋', 'Win back lapsed regulars', 'A message to guests who opted in')}${li('🎂', 'Loyalty & birthday rewards', 'Give regulars a reason to return')}${li('🎯', 'Ads aimed at your real guests', 'Families, date nights, business lunches')}${li('📊', 'Track CAC & LTV monthly', 'Know what each guest costs and is worth')}`) },
    { theme: 'dark', last: true, body: cta('Which level is <span class="gold">your restaurant</span> at?',
      'Most venues stop at level 1: the data is there, but nobody reads it. The money is in levels 3 and 4.',
      'Comment 1, 2, 3 or 4', 'Save this as your roadmap') },
  ],
  '9-restaurant-types': (() => {
    const types = [
      ['Fine Dining', 'The full experience. Chef-led menus, premium ingredients, white-glove service.', '$$$$', '2–3 hours', 'Table service, often tasting menus', 'Average check & reservation fill rate'],
      ['Casual Dining', 'Sit-down meals at mid-range prices. Relaxed, family and friends friendly.', '$$–$$$', '45–90 min', 'Table service, full menu', 'Table turnover per shift'],
      ['Fast Casual', 'Better quality than fast food, no table service. Order at the counter, eat fresh.', '$$', '20–40 min', 'Counter order, food brought or picked up', 'Orders per hour at peak'],
      ['Fast Food (QSR)', 'Quick Service Restaurant. Standard menu, high volume, speed above all. The closest thing to FMCG in food.', '$', 'Under 15 min', 'Counter, drive-thru, delivery', 'Speed of service & daily volume'],
      ['Café', 'Coffee first, food second. A place people come back to again and again.', '$–$$', '30 min to hours', 'Counter or light table service', 'Repeat visits per guest'],
      ['Cloud Kitchen', 'Delivery only. No dining room, just a kitchen and the apps.', '$–$$', 'Delivery only', 'Delivery apps & own ordering', 'App rating & commission per order'],
    ];
    const slides = [
      { theme: 'dark', foot: 'Save this for later', body: center(`
        <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant 101</span>
        <h1>Not every restaurant <span class="gold">plays the same game.</span></h1>
        <p class="sub" style="margin-top:44px">6 types of restaurants, how each one works, and the one number each should watch.</p>`) },
      { theme: 'light', body: center(`
        <span class="tag">At a glance</span>
        <h2 style="margin:40px 0 36px">From <span class="rose">$ to $$$$</span></h2>
        <div style="display:flex;justify-content:space-between;font:800 22px Inter;letter-spacing:2px;opacity:.55;padding-bottom:12px;border-bottom:3px solid var(--ink)"><span>TYPE</span><span style="display:flex;gap:40px"><span style="width:150px;text-align:right">PRICE</span><span style="width:250px;text-align:right">TIME AT TABLE</span></span></div>
        ${types.map(t => `<div style="display:flex;justify-content:space-between;align-items:center;padding:24px 0;border-bottom:2px solid #e0d2c4;font:700 32px Inter"><span>${t[0]}</span><span style="display:flex;gap:40px;font-weight:600"><span class="rose" style="width:150px;text-align:right">${t[2]}</span><span style="width:250px;text-align:right;opacity:.75">${t[3]}</span></span></div>`).join('')}`) },
    ];
    types.forEach((t, i) => {
      const dark = i % 2 === 1;
      slides.push({ theme: dark ? 'dark' : 'light', body: `<div class="huge" style="opacity:${dark ? .22 : .18}">0${i + 1}</div>` + center(`
        <span class="tag">Type ${i + 1} of 6</span>
        <h2 style="margin:40px 0 24px">${t[0]}</h2>
        <p class="sub" style="margin-bottom:24px">${t[1]}</p>
        ${li('💰', 'Price: ' + t[2])}${li('⏱️', 'Time at table: ' + t[3])}${li('🍽️', t[4])}
        <div class="pill" style="margin-top:36px">📊 Number to watch: ${t[5]}</div>`) });
    });
    slides.push({ theme: 'dark', last: true, body: cta('Which type <span class="gold">do you run?</span>',
      'Every type wins differently. Copy the playbook of the wrong type and you\'ll chase the wrong numbers.',
      'Comment your restaurant type', 'Save this for your next concept') });
    return slides;
  })(),
  '10-aggregator-negotiation': [
    { theme: 'dark', foot: 'Save this before your next meeting', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant × Aggregators</span>
      <h1>Asking for <span class="gold">0% commission?</span><br>Here's why it's a no.</h1>
      <p class="sub" style="margin-top:44px">How aggregators actually work, and how to negotiate a deal that makes sense for both sides.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">How it works</span>
      <h2 style="margin:40px 0 30px">Follow the <span class="rose">money</span></h2>
      ${li('1', 'The guest pays the aggregator', 'By card, wallet or app')}${li('2', 'The bank takes its fee first', 'Every single transaction has a processing cost')}${li('3', 'The aggregator takes its commission', 'This pays for everything that brought you the guest')}${li('4', 'You get your payout', 'On a set cycle: weekly, bi-weekly or monthly')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">Where the commission goes</span>
      <h2 style="margin:40px 0 30px">It's not <span class="gold">pure profit</span></h2>
      ${li('🏦', 'Bank & payment fees', 'Paid on every order, no matter what')}${li('📣', 'Marketing', 'Ads and promos that bring guests to you')}${li('📱', 'Tech & the app', 'Developers, servers, maintenance')}${li('🎧', 'Customer support', 'Handling complaints, refunds and cancellations')}`) },
    { theme: 'light', foot: 'Illustrative numbers', body: center(`
      <span class="tag">Why 0% is impossible</span>
      <h2 style="margin:40px 0 36px">At 0%, they <span class="rose">pay to serve you</span></h2>
      <div class="cards">
        <div class="card w"><div class="l">Guest pays</div><div class="big" style="margin-top:4px">EGP 500</div></div>
        <div class="card d"><div class="l">Bank fee (e.g. 2.5%)</div><div class="m">Taken before anyone else is paid</div><div class="big">− EGP 12.5</div></div>
      </div>
      <div class="pill" style="margin-top:36px">At 0% commission, the aggregator loses money on every order you get. No business signs that deal.</div>`) },
    { theme: 'dark', body: center(`
      <span class="tag">Before the meeting</span>
      <h2 style="margin:40px 0 30px">Know <span class="gold">your numbers</span> first</h2>
      ${li('🧾', 'Average order & margin per dish', 'So you know the commission you can afford')}${li('💸', 'Your CAC on your own', 'What a new guest costs you without them')}${li('📈', 'The volume they can bring', 'Ask for real numbers from your area')}${li('📄', 'The contract terms', 'Exclusivity, payout cycle, refunds, price rules')}`) },
    { theme: 'light', body: center(`
      <span class="tag">What you CAN negotiate</span>
      <h2 style="margin:40px 0 30px">Ask for value, <span class="rose">not zero</span></h2>
      ${li('📊', 'Tiered commission', 'A lower rate once you hit agreed volumes')}${li('🚀', 'A launch period', 'A reduced rate for your first months')}${li('⭐', 'Visibility', 'Featured placement, banners, co-funded promos')}${li('⏱️', 'Faster payouts', 'Cash flow matters as much as the rate')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">How to negotiate</span>
      <h2 style="margin:40px 0 30px">Give something, <span class="gold">get something</span></h2>
      ${li('1', 'Bring data, not feelings', '"Our average order is X, we can do Y orders a month"')}${li('2', 'Offer something in return', 'Exclusivity in your area, a volume commitment, promos')}${li('3', 'Get it in writing', 'Rates, tiers, payout dates, who pays refunds')}${li('4', 'Review every 3–6 months', 'Your numbers change, so should your deal')}`) },
    { theme: 'light', body: center(`
      <span class="tag">Mistakes to avoid</span>
      <h2 style="margin:40px 0 30px">Don't <span class="rose">lose the deal</span> before it starts</h2>
      ${li('✕', 'Opening with "0% or nothing"', 'It ends the conversation, not the cost')}${li('✕', 'Signing exclusivity for free', 'It\'s your strongest card. Trade it')}${li('✕', 'Ignoring the small print', 'Promo costs, refunds and extra fees add up')}${li('✕', 'Not tracking results', 'If you don\'t measure orders, you can\'t renegotiate')}`) },
    { theme: 'dark', last: true, body: cta('Negotiate for <span class="gold">value,</span> not zero.',
      'The best deals are the ones where both sides make money. That\'s the deal that lasts.',
      'Comment your biggest aggregator question', 'Save this before your next meeting') },
  ],
  '11-loyalty-data': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Data</span>
      <h1>A loyalty card isn't a discount. <span class="gold">It's a data machine.</span></h1>
      <p class="sub" style="margin-top:44px">Here's what one card can tell you about your guests.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Who they are</span>
      <h2 style="margin:40px 0 30px">Know your <span class="rose">guests by name</span></h2>
      ${li('👤', 'Name & phone number', 'Collected with their permission')}${li('🎂', 'Birthday', 'The easiest reason to invite them back')}${li('📍', 'Area they live in', 'Where your guests actually come from')}${li('🔎', 'How they found you', 'Which channel really brings guests')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">How they behave</span>
      <h2 style="margin:40px 0 30px">Know what they <span class="gold">do</span></h2>
      ${li('🔁', 'How often they visit', 'Your real regulars vs one-timers')}${li('🍽️', 'What they order & spend', 'Favourite dishes and average check')}${li('📅', 'When they come', 'Their favourite days and times')}${li('⏳', 'When they last visited', 'Spot who\'s slipping away early')}`) },
    { theme: 'light', body: center(`
      <span class="tag">Use it</span>
      <h2 style="margin:40px 0 30px">Turn the data into <span class="rose">visits</span></h2>
      ${li('🎂', 'Send birthday offers', 'Personal, timely, almost always used')}${li('👋', 'Win back quiet guests', 'Not seen in 30 days? Send them a reason')}${li('⭐', 'Reward your top 20%', 'They bring most of your revenue')}${li('📊', 'Plan menu & staff', 'Based on what regulars actually do')}`) },
    { theme: 'dark', last: true, body: cta('Stop giving discounts. <span class="gold">Start collecting data.</span>',
      'Every stamp is a data point. Every data point is a reason to bring a guest back.',
      'Do you run a loyalty program? Yes or no', 'Save this for your next loyalty launch') },
  ],
  '12-tripadvisor': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Marketing</span>
      <h1>Tourists are looking for a place to eat. <span class="gold">Can they find you?</span></h1>
      <p class="sub" style="margin-top:44px">What TripAdvisor tells you about your guests, and why your restaurant should be on it.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">The data · Part 1</span>
      <h2 style="margin:40px 0 30px">What every <span class="rose">review</span> tells you</h2>
      ${li('⭐', 'Overall rating & written review', 'What guests loved, and what they didn\'t')}${li('🍽️', 'Food, service, value, atmosphere', 'See exactly which part needs work')}${li('👨‍👩‍👧', 'Who they came with', 'Families, couples, friends, business')}${li('🌍', 'Where reviewers are from', 'Tourists vs locals, and which countries')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">The data · Part 2</span>
      <h2 style="margin:40px 0 30px">What your <span class="gold">listing</span> tells you</h2>
      ${li('🏆', 'Your ranking in your city', '"#12 of 800 restaurants in Cairo"')}${li('👀', 'How many people view your page', 'From the free owner dashboard')}${li('📷', 'Guest photos', 'What people actually share about you')}${li('🔍', 'Your competitors\' reviews', 'Learn from what guests say about them')}`) },
    { theme: 'light', body: center(`
      <span class="tag">The benefits</span>
      <h2 style="margin:40px 0 30px">Why it's <span class="rose">worth it</span></h2>
      ${li('✈️', 'Reach tourists & travellers', 'People who don\'t know your area yet')}${li('🤝', 'Build trust before they visit', 'Reviews from strangers sell better than ads')}${li('📈', 'Climb your city ranking', 'More good reviews, more visibility')}${li('🏅', 'Earn the Travelers\' Choice badge', 'For consistently great reviews')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">How to start</span>
      <h2 style="margin:40px 0 30px">4 steps, <span class="gold">this week</span></h2>
      ${li('1', 'Claim your listing', 'It\'s free')}${li('2', 'Add photos, menu & hours', 'A complete page gets more clicks')}${li('3', 'Ask happy guests to review', 'A card on the table or a QR code')}${li('4', 'Reply to every review', 'Good or bad. Future guests read your replies')}`) },
    { theme: 'dark', last: true, body: cta('Get found by <span class="gold">every tourist</span> in town.',
      'Google brings the locals. TripAdvisor brings the travellers. A good restaurant needs both.',
      'Is your restaurant on TripAdvisor? Yes or no', 'Save this for your setup') },
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
    await page.evaluate(() => Promise.all([...document.images].map(i => i.decode())));
    await page.evaluate(() => document.fonts.ready);
    const els = await page.$$('.slide');
    for (let i = 0; i < els.length; i++)
      await els[i].screenshot({ path: path.join(dir, `slide-${String(i + 1).padStart(2, '0')}.png`) });
  }
  await browser.close();
})();
