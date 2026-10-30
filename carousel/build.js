// Builds 3 carousels (HTML + PNG per slide) from the content below.
// Run: node build.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const style = fs.readFileSync(path.join(__dirname, 'style.css'), 'utf8');
const fonts = '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Inter:wght@400;500;600;700;800&family=Cairo:wght@400;500;600;700;800&family=El+Messiri:wght@500;600;700&display=swap" rel="stylesheet">';

const top = (n, total) => `<div class="top"><div class="who"><div class="av">MM</div><div><div class="name">Mina Monir</div><div class="handle">@mina_monir8</div></div></div><div class="num">${String(n).padStart(2, '0')} / ${String(total).padStart(2, '0')}</div></div>`;
const bot = (left, last, swipe = 'Swipe →') => last
  ? `<div class="bot"><span>Mina Monir</span><span>@mina_monir8</span></div>`
  : `<div class="bot"><span>${left || '@mina_monir8'}</span><span class="sw">${swipe}</span></div>`;
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

const geo = (ar) => {
  const t = (en, a) => ar ? a : en;
  const S = ar ? 'اسحب →' : undefined, cls = ar ? 'rtl' : '';
  const stats = (rows) => `<div class="stats">${rows.map(([b, en, a]) => `<div class="stat"><b>${b}</b><span class="lbl">${t(en, a)}</span></div>`).join('')}</div>`;
  const tag = (n, en, a) => `<span class="tag">${t(`Fact ${n} · ${en}`, `معلومة ${'١٢٣٤٥٦٧٨٩'[n - 1] || '١٠'} · ${a}`)}</span>`;
  const note = (en, a) => `<div class="pill" style="margin-top:36px">${t(en, a)}</div>`;
  const s = (theme, body, extra = {}) => ({ theme, cls, swipe: S, body, ...extra });
  return [
    s('dark', center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">${t('Geography 101', 'جغرافيا ١٠١')}</span>
      <h1>${t('How well do you <span class="gold">know our planet?</span>', 'إنت <span class="gold">عارف كوكبنا</span> قد إيه؟')}</h1>
      <p class="sub" style="margin-top:44px">${t('10 facts about countries, time zones and the map that most people get wrong.', '١٠ معلومات عن الدول والتوقيتات والخريطة، ناس كتير متعرفهاش.')}</p>`), { foot: t('Save this for later', 'احفظه لبعدين') }),
    s('light', center(`${tag(1, 'The planet', 'الكوكب')}
      <h2 style="margin:40px 0 36px">${t('Our planet <span class="rose">in numbers</span>', 'كوكبنا <span class="rose">بالأرقام</span>')}</h2>
      ${stats([['71%', 'of Earth\'s surface is water', 'من سطح الأرض مية'], ['7', 'continents', 'قارات'], ['5', 'oceans', 'محيطات'], ['40,075 km', 'around the equator', 'طول خط الاستوا']])}`)),
    s('dark', center(`${tag(2, 'Countries', 'الدول')}
      <h2 style="margin:40px 0 36px">${t('How many countries <span class="gold">are there?</span>', 'العالم فيه <span class="gold">كام دولة؟</span>')}</h2>
      ${stats([['193', 'UN member states', 'دولة عضو في الأمم المتحدة'], ['2', 'observer states: Vatican & Palestine', 'دولتين بصفة مراقب: الفاتيكان وفلسطين']])}
      ${note('The newest UN member is South Sudan. It joined in 2011.', 'أحدث دولة انضمت للأمم المتحدة هي جنوب السودان، سنة ٢٠١١.')}`)),
    s('light', center(`${tag(3, 'Time zones', 'التوقيتات')}
      <h2 style="margin:40px 0 36px">${t('Why <span class="rose">24</span> time zones?', 'ليه <span class="rose">٢٤</span> توقيت؟')}</h2>
      ${stats([['360°', 'Earth turns fully in 24 hours', 'الأرض بتلف لفة كاملة في ٢٤ ساعة'], ['15°', '= 1 hour of time', '= ساعة واحدة']])}
      ${note('In reality the world uses about 38 local times, because some places shift by 30 or 45 minutes.', 'بس في الحقيقة العالم بيستخدم حوالي ٣٨ توقيت، لأن في أماكن بتفرق نص ساعة أو ٤٥ دقيقة.')}`)),
    s('dark', center(`${tag(4, 'Time zones', 'التوقيتات')}
      <h2 style="margin:40px 0 30px">${t('Time zones <span class="gold">get weird</span>', 'التوقيتات <span class="gold">ليها حكايات</span>')}</h2>
      ${li('🇫🇷', t('France has the most: 12', 'فرنسا عندها أكبر عدد: ١٢ توقيت'), t('Thanks to its overseas territories', 'بسبب أراضيها اللي برّه أوروبا'))}
      ${li('🇷🇺', t('Russia spans 11', 'روسيا فيها ١١ توقيت'), t('From Europe to the Pacific', 'من أوروبا لحد المحيط الهادي'))}
      ${li('🇨🇳', t('China uses just 1', 'الصين بتستخدم توقيت واحد بس'), t('Even though it\'s as wide as 5', 'رغم إن عرضها يكفي ٥ توقيتات'))}
      ${li('🌏', t('26 hours apart', '٢٦ ساعة فرق'), t('Between UTC+14 (Kiribati) and UTC−12', 'بين UTC+14 (كيريباتي) و UTC−12'))}`)),
    s('light', center(`${tag(5, 'Size', 'المساحة')}
      <h2 style="margin:40px 0 36px">${t('The biggest <span class="rose">and the smallest</span>', 'الأكبر <span class="rose">والأصغر</span>')}</h2>
      <div class="cards">
        <div class="card d"><div class="l">${t('🇷🇺 Russia · biggest country', '🇷🇺 روسيا · أكبر دولة')}</div><div class="m">${t('About 11% of all the land on Earth', 'حوالي ١١٪ من يابس الأرض كله')}</div><div class="big">17.1M km²</div></div>
        <div class="card w"><div class="l">${t('🇻🇦 Vatican City · smallest country', '🇻🇦 الفاتيكان · أصغر دولة')}</div><div class="m">${t('About the size of 60 football pitches', 'قد حوالي ٦٠ ملعب كورة')}</div><div class="big">0.44 km²</div></div>
      </div>`)),
    s('dark', center(`${tag(6, 'People', 'السكان')}
      <h2 style="margin:40px 0 36px">${t('Where <span class="gold">the people</span> are', 'الناس <span class="gold">فين؟</span>')}</h2>
      ${stats([['8B+', 'people on Earth', 'إنسان على الأرض'], [t('India', 'الهند'), 'most populous country, since 2023', 'أكبر دولة في عدد السكان من ٢٠٢٣']])}
      ${note('India passed China in 2023. Each has more than 1.4 billion people.', 'الهند عدّت الصين سنة ٢٠٢٣، والاتنين سكانهم أكتر من ١.٤ مليار.')}`)),
    s('light', center(`${tag(7, 'Extremes', 'أطراف الأرض')}
      <h2 style="margin:40px 0 36px">${t('Highest <span class="rose">vs deepest</span>', 'الأعلى <span class="rose">والأعمق</span>')}</h2>
      ${stats([['8,849 m', 'Mount Everest, the highest point on Earth', 'جبل إيفرست، أعلى نقطة على الأرض'], ['~11,000 m', 'Challenger Deep, Mariana Trench, the deepest point', 'تشالنجر ديب في خندق ماريانا، أعمق نقطة']])}
      ${note('Drop Everest into the trench and its peak would still be about 2 km underwater.', 'لو حطيت إيفرست في الخندق، قمته هتفضل تحت المية بحوالي ٢ كيلو.')}`)),
    s('dark', center(`${tag(8, 'Rivers', 'الأنهار')}
      <h2 style="margin:40px 0 36px">${t('The <span class="gold">Nile</span>', '<span class="gold">النيل</span>')}</h2>
      ${stats([['6,650 km', 'usually ranked the longest river in the world', 'غالباً بيتصنف أطول نهر في العالم'], ['11', 'countries in the Nile basin', 'دولة في حوض النيل']])}
      ${note('It flows north, from the heart of Africa to the Mediterranean. (Some studies give the "longest" title to the Amazon.)', 'بيجري من الجنوب للشمال، من قلب أفريقيا للبحر المتوسط. (في دراسات بتدّي لقب "الأطول" للأمازون.)')}`)),
    s('light', center(`${tag(9, 'Deserts', 'الصحاري')}
      <h2 style="margin:40px 0 36px">${t('The biggest desert <span class="rose">isn\'t hot</span>', 'أكبر صحرا <span class="rose">مش حَر</span>')}</h2>
      ${stats([['9.2M km²', 'the Sahara, the biggest hot desert, nearly the size of the USA', 'الصحرا الكبرى، أكبر صحرا حارة، قد أمريكا تقريباً'], ['14M km²', 'Antarctica, the biggest desert of all', 'أنتاركتيكا، أكبر صحرا في العالم']])}
      ${note('A desert is about how little rain falls, not how hot it is.', 'الصحرا بتتحسب بقلة المطر، مش بدرجة الحرارة.')}`)),
    s('dark', center(`${tag(10, 'Egypt', 'مصر')}
      <h2 style="margin:40px 0 30px">${t('Egypt <span class="gold">on the map</span>', 'مصر <span class="gold">على الخريطة</span>')}</h2>
      ${li('🌍', t('On two continents', 'في قارتين'), t('Africa, and Asia through Sinai', 'أفريقيا، وآسيا عن طريق سينا'))}
      ${li('📐', t('About 1 million km²', 'حوالي مليون كم²'), t('One of the 30 biggest countries in the world', 'من أكبر ٣٠ دولة في العالم'))}
      ${li('🏜️', t('About 95% desert', 'حوالي ٩٥٪ صحرا'), t('Most people live along the Nile and the Delta', 'أغلب الناس عايشين على النيل والدلتا'))}
      ${li('⏰', 'UTC+2', t('And UTC+3 in summer', 'و UTC+3 في الصيف'))}`)),
    s('dark', center(`
      <h1 style="font-size:92px">${t('Which fact <span class="gold">surprised you?</span>', 'أنهي معلومة <span class="gold">فاجئتك؟</span>')}</h1>
      <p class="sub" style="margin:40px 0 60px">${t('Geography isn\'t about memorising maps. It\'s about understanding the world we live and work in.', 'الجغرافيا مش حفظ خرايط. الجغرافيا إنك تفهم العالم اللي بنعيش ونشتغل فيه.')}</p>
      <div class="cta-list" style="display:flex;flex-direction:column;gap:22px;font:600 34px Inter">
        <div>💬 &nbsp;${t('Comment the number of the fact', 'اكتب رقم المعلومة في الكومنتات')}</div>
        <div>🏷️ &nbsp;${t('Tag a friend who loves maps', 'اعمل تاج لصاحبك اللي بيحب الخرايط')}</div>
        <div>➕ &nbsp;${t('Follow', 'تابع')} <span class="gold" dir="ltr">@mina_monir8</span></div>
      </div>`), { last: true }),
  ];
};
const pain = (n, p) => [
  { theme: 'dark', foot: `Restaurant Pain Points · ${n}/5`, body: center(`
    <span class="tag" style="margin-bottom:44px;display:inline-block">Pain point ${n}/5 · ${p.name}</span>
    <h1>${p.hook}</h1>
    <p class="sub" style="margin-top:44px">${p.sub}</p>`) },
  { theme: 'light', foot: p.costFoot, body: center(`
    <span class="tag">What it costs you</span>
    <h2 style="margin:40px 0 36px">${p.costTitle}</h2>
    ${p.cost}`) },
  { theme: 'dark', body: center(`
    <span class="tag">Why it happens</span>
    <h2 style="margin:40px 0 30px">${p.whyTitle}</h2>
    ${p.why.map(([i, t, s]) => li(i, t, s)).join('')}`) },
  { theme: 'light', body: center(`
    <span class="tag">How to fix it</span>
    <h2 style="margin:40px 0 30px">${p.fixTitle}</h2>
    ${p.fix.map(([t, s], i) => li(i + 1, t, s)).join('')}`) },
  { theme: 'dark', body: center(`
    <span class="tag">The number to track</span>
    <h2 style="margin:40px 0 36px">${p.metricTitle}</h2>
    <div class="formula" style="color:var(--cream)">${p.formula}</div>
    <p class="sub" style="margin-top:40px">${p.metricNote}</p>`) },
  { theme: 'dark', last: true, body: cta(p.ctaTitle, p.ctaText, p.comment, 'Save this for your next team meeting') },
];
const pains = [
  { name: 'No-shows', hook: 'A table for 6 at 9 PM. <span class="gold">Nobody shows up.</span>', sub: 'No-shows are the silent profit killer. You held the table, turned guests away, and earned nothing.',
    costTitle: 'Small numbers, <span class="rose">big losses</span>', costFoot: 'Illustrative numbers',
    cost: `<div class="stats"><div class="stat"><b>4</b><span class="lbl">no-show tables a week</span></div><div class="stat"><b>× 1,500</b><span class="lbl">EGP average bill</span></div></div><div class="pill" style="margin-top:30px">= about EGP 24,000 a month in empty tables. And the walk-ins you turned away.</div>`,
    whyTitle: 'Booking is easy. <span class="gold">Cancelling is awkward.</span>',
    why: [['📵', 'No confirmation', 'Guests forget, and nobody reminds them'], ['🔀', 'Multiple bookings', 'They booked 3 places and chose one'], ['🆓', 'No commitment', 'Nothing to lose by not showing up'], ['😶', 'Cancelling feels awkward', 'So they just don\'t come']],
    fixTitle: '5 ways to <span class="rose">cut no-shows</span>',
    fix: [['Confirm twice', 'WhatsApp 24 hours and 2 hours before'], ['Make cancelling easy', 'One tap to cancel beats a ghost'], ['Deposits for big groups', 'And for peak nights'], ['Keep a waitlist', 'Fill the gap fast when someone cancels'], ['Set a 15-minute rule', 'Then release the table']],
    metricTitle: 'Your <span class="gold">no-show rate</span>', formula: 'No-shows ÷ Total bookings × 100', metricNote: 'Track it every week. If it\'s climbing, your confirmation process is broken.',
    ctaTitle: 'How many no-shows <span class="gold">did you have last week?</span>', ctaText: 'You can\'t stop every no-show. But you can stop most of them.', comment: 'Comment your no-show number' },
  { name: 'Empty weekdays', hook: 'Packed on Thursday. <span class="gold">Empty on Monday.</span>', sub: 'Your rent, staff and electricity don\'t take Monday off. Neither should your guests.',
    costTitle: 'Fixed costs <span class="rose">don\'t take days off</span>', costFoot: '',
    cost: `<div class="cards"><div class="card d"><div class="l">Thursday</div><div class="m">Same rent · same staff · same bills</div><div class="big">Full house</div></div><div class="card w"><div class="l">Monday</div><div class="m">Same rent · same staff · same bills</div><div class="big">5 tables</div></div></div>`,
    whyTitle: 'Guests have <span class="gold">no reason</span> to come',
    why: [['📅', 'Same offer every day', 'Nothing makes Monday special'], ['📣', 'Marketing only for weekends', 'Weekdays get forgotten'], ['🏢', 'Ignoring the lunch crowd', 'Offices nearby eat every weekday'], ['🔇', 'Nothing happening', 'No events, no buzz']],
    fixTitle: 'Give them <span class="rose">a reason</span>',
    fix: [['Weekday-only offers', 'Set lunch, early-bird, family night'], ['Run an event', 'Quiz night, live music, game night'], ['Win the business lunch', 'Fast menu for nearby offices'], ['Double loyalty points', 'Only on your quiet days'], ['Promote quiet days, not busy ones', 'Spend ads where tables are empty']],
    metricTitle: 'Covers <span class="gold">by day of week</span>', formula: 'Guests served per day, every week', metricNote: 'Find your weakest day. Make one change. Measure again in 4 weeks.',
    ctaTitle: 'What\'s your <span class="gold">quietest day?</span>', ctaText: 'Every empty weekday table is a cost you\'re already paying. Fill it.', comment: 'Comment your quietest day' },
  { name: 'Staff turnover', hook: 'You trained them for 3 months. <span class="gold">They left in 4.</span>', sub: 'Staff turnover is one of the most expensive problems in hospitality, and one of the least measured.',
    costTitle: 'Every exit <span class="rose">costs you</span>', costFoot: '',
    cost: [['⏳', 'Hiring time', 'Interviews, trials, paperwork'], ['📚', 'Training again', 'Weeks before they\'re fully up to speed'], ['🍽️', 'Service drops', 'Mistakes, slow tables, unhappy guests'], ['👋', 'Regulars notice', 'They miss the faces they knew']].map(([i, t, s]) => li(i, t, s)).join(''),
    whyTitle: 'People don\'t leave jobs. <span class="gold">They leave how it feels.</span>',
    why: [['📆', 'Chaotic schedules', 'Shifts changed at the last minute'], ['🙈', 'No recognition', 'Good work goes unnoticed'], ['🪜', 'No growth path', 'Waiter today, waiter in 5 years'], ['🚪', 'Weak onboarding', 'Thrown in on day one']],
    fixTitle: 'Make them <span class="rose">want to stay</span>',
    fix: [['A real first 2 weeks', 'Buddy, checklist, clear expectations'], ['Publish schedules early', 'At least a week ahead'], ['Recognise wins out loud', 'In the team briefing, every week'], ['Show the path', 'Waiter → captain → supervisor'], ['Ask before they leave', 'Monthly 1:1: "What would make you stay?"']],
    metricTitle: 'Your <span class="gold">turnover rate</span>', formula: 'People who left ÷ Average team size × 100', metricNote: 'Measure it every quarter, per role. Where it\'s highest, start there.',
    ctaTitle: 'How long does your team <span class="gold">usually stay?</span>', ctaText: 'Guests come back for the food. They fall in love with the people.', comment: 'Comment your best retention tip' },
  { name: 'One-time guests', hook: 'They loved the food. <span class="gold">They never came back.</span>', sub: 'Most restaurants spend on bringing new guests in, and almost nothing on bringing them back.',
    costTitle: 'New guests <span class="rose">cost more</span>', costFoot: '',
    cost: `<div class="cards"><div class="card w"><div class="l">Winning a new guest</div><div class="m">Ads, promos, app commissions</div><div class="big">Expensive</div></div><div class="card d"><div class="l">Bringing a guest back</div><div class="m">A message, a reward, a warm welcome</div><div class="big">Cheap</div></div></div>`,
    whyTitle: 'Good food <span class="gold">isn\'t enough</span>',
    why: [['🤷', 'No reason to return', 'Nothing is waiting for them'], ['📵', 'No way to reach them', 'You don\'t have their number'], ['🧠', 'They simply forget', 'Hundreds of other places compete'], ['😐', 'Nobody remembered them', 'Treated like a stranger, again']],
    fixTitle: 'Turn visit 1 into <span class="rose">visit 2</span>',
    fix: [['Collect contacts, with permission', 'At booking, via loyalty or Wi-Fi'], ['Say thank you the next day', 'A short, personal message'], ['Invite them back within 30 days', 'With a reason, not just a discount'], ['Remember them', 'Their name, their table, their favourite dish'], ['Reward the 3rd visit', 'That\'s when a habit starts']],
    metricTitle: 'Your <span class="gold">repeat rate</span>', formula: 'Guests who returned within 60 days ÷ All new guests', metricNote: 'Raise it a little and your revenue grows without spending more on ads.',
    ctaTitle: 'Do you know your <span class="gold">repeat rate?</span>', ctaText: 'Every regular started as a one-time guest. The difference is what you did next.', comment: 'Yes or no: do you track it?' },
  { name: 'Food waste', hook: 'Every kilo in the bin is <span class="gold">profit in the bin.</span>', sub: 'Food waste is one of the easiest costs to cut, because most restaurants never measure it.',
    costTitle: 'You pay for it <span class="rose">three times</span>', costFoot: '',
    cost: [['🛒', 'When you buy it', 'Ingredients you paid full price for'], ['👨‍🍳', 'When you prep it', 'Staff time, gas and electricity'], ['🗑️', 'When you throw it out', 'Zero revenue, plus disposal']].map(([i, t, s]) => li(i, t, s)).join(''),
    whyTitle: 'Where the <span class="gold">waste</span> comes from',
    why: [['📦', 'Over-ordering', 'Buying "just in case"'], ['🔪', 'Over-prepping', 'Same prep on Monday as on Friday'], ['🍽️', 'Plates coming back full', 'Portions too big for your guests'], ['🧊', 'Poor storage', 'Old stock hidden behind new']],
    fixTitle: '5 ways to <span class="rose">waste less</span>',
    fix: [['Weigh waste every day', 'What gets measured gets managed'], ['Prep to your forecast', 'By day of the week, not by habit'], ['First in, first out', 'Label and date everything'], ['Watch the plates', 'Adjust portions guests don\'t finish'], ['Use a daily special', 'Turn extra stock into a best-seller']],
    metricTitle: 'Your <span class="gold">waste %</span>', formula: 'Value of food wasted ÷ Food purchased × 100', metricNote: 'Check it weekly. Every point you cut goes straight to profit.',
    ctaTitle: 'Do you weigh <span class="gold">your waste?</span>', ctaText: 'The cheapest ingredient is the one you didn\'t throw away.', comment: 'Comment your best anti-waste tip' },
];
const countries = [
  { flag: '🇺🇸', name: 'United States', capital: 'Washington, D.C.', pop: '~340 million', lang: 'English', rel: 'Christianity (majority)', gfp: '#1', pass: '~180 visa-free', nb: '2',
    borders: 'Canada · Mexico', meaning: `13 stripes = the 13 original colonies · 50 stars = the 50 states`,
    famous: `<b>Neil Armstrong</b>: first human to walk on the Moon (1969)`, brands: 'Apple · Google · Microsoft · Jeep · Coca-Cola' },
  { flag: '🇷🇺', name: 'Russia', capital: 'Moscow', pop: '~144 million', lang: 'Russian', rel: 'Orthodox Christianity, Islam', gfp: '#2', pass: '~115 visa-free', nb: '14',
    borders: 'Norway · Finland · Estonia · Latvia · Lithuania · Poland · Belarus · Ukraine · Georgia · Azerbaijan · Kazakhstan · China · Mongolia · North Korea',
    meaning: `White, blue, red. No official meaning, often read as honesty, loyalty and courage`,
    famous: `<b>Yuri Gagarin</b>: first human in space (1961)`, brands: 'Gazprom · Lukoil · Kaspersky · Aeroflot · Yandex' },
  { flag: '🇨🇳', name: 'China', capital: 'Beijing', pop: '~1.41 billion', lang: 'Mandarin Chinese', rel: 'Mostly non-religious; Buddhism, folk religion', gfp: '#3', pass: '~80 visa-free', nb: '14',
    borders: 'Russia · Mongolia · North Korea · Vietnam · Laos · Myanmar · India · Bhutan · Nepal · Pakistan · Afghanistan · Tajikistan · Kyrgyzstan · Kazakhstan',
    meaning: `Red = the revolution · big star = the Communist Party · 4 small stars = the people`,
    famous: `<b>Confucius</b>: philosopher whose ideas on ethics shaped Asia for 2,500 years`, brands: 'Huawei · Alibaba · BYD · Lenovo · ByteDance (TikTok)' },
  { flag: '🇮🇳', name: 'India', capital: 'New Delhi', pop: '~1.46 billion', lang: 'Hindi & English (+22 official)', rel: 'Hinduism (~80%), Islam (~14%)', gfp: '#4', pass: '~57 visa-free', nb: '6',
    borders: 'Pakistan · China · Nepal · Bhutan · Bangladesh · Myanmar',
    meaning: `Saffron = courage · white = peace & truth · green = growth · wheel = dharma (24 spokes)`,
    famous: `<b>Mahatma Gandhi</b>: led India to independence (1947) through non-violence`, brands: 'Tata · Reliance · Infosys · Mahindra · Wipro' },
  { flag: '🇪🇬', name: 'Egypt', capital: 'Cairo', pop: '~108 million', lang: 'Arabic', rel: 'Islam (~90%), Christianity (~10%)', gfp: '#19', pass: '~52 visa-free', nb: '4',
    borders: 'Libya · Sudan · Israel · Palestine (Gaza)',
    meaning: `Red = the struggle before 1952 · white = the peaceful 1952 revolution · black = the end of oppression · gold eagle of Saladin`,
    famous: `<b>Naguib Mahfouz</b>: first Arab writer to win the Nobel Prize in Literature (1988)`, brands: 'EgyptAir · Orascom · Elsewedy Electric · CIB · Juhayna' },
];
const globe = `<svg width="300" height="300" viewBox="0 0 300 300" style="flex:none"><circle cx="150" cy="150" r="130" fill="none" stroke="var(--cream)" stroke-width="3"/>
  ${[40, 80, 115].map(rx => `<ellipse cx="150" cy="150" rx="${rx}" ry="130" fill="none" stroke="rgba(243,235,225,.35)" stroke-width="2"/>`).join('')}
  ${[-80, -40, 0, 40, 80].map(y => `<line x1="${150 - Math.sqrt(130 * 130 - y * y)}" y1="${150 + y}" x2="${150 + Math.sqrt(130 * 130 - y * y)}" y2="${150 + y}" stroke="rgba(243,235,225,.35)" stroke-width="2"/>`).join('')}
  <line x1="150" y1="10" x2="150" y2="290" stroke="var(--gold)" stroke-width="6"/><text x="162" y="40" fill="var(--gold)" font-family="Inter" font-weight="800" font-size="26">0°</text></svg>`;
const compass = `<svg width="330" height="345" viewBox="0 0 330 345" style="flex:none"><circle cx="165" cy="175" r="130" fill="none" stroke="var(--cream)" stroke-width="3"/>
  <line x1="165" y1="175" x2="165" y2="35" stroke="var(--cream)" stroke-width="6"/><path d="M155 45 L165 22 L175 45Z" fill="var(--cream)"/>
  <text x="165" y="14" text-anchor="middle" fill="var(--cream)" font-family="Inter" font-weight="800" font-size="22">TRUE N ★</text>
  <g transform="rotate(20 165 175)"><line x1="165" y1="175" x2="165" y2="45" stroke="var(--gold)" stroke-width="6"/><path d="M155 55 L165 32 L175 55Z" fill="var(--gold)"/></g>
  <text x="248" y="60" fill="var(--gold)" font-family="Inter" font-weight="800" font-size="22">MAG N</text>
  <path d="M165 95 A80 80 0 0 1 192 100" fill="none" stroke="var(--gold)" stroke-width="3"/>
  <circle cx="165" cy="175" r="8" fill="var(--cream)"/>
  <text x="165" y="330" text-anchor="middle" fill="var(--cream)" opacity=".7" font-family="Inter" font-weight="600" font-size="20">angle exaggerated</text></svg>`;
const C20 = [
  ['🇺🇸', 'الولايات المتحدة', 'واشنطن', '340 مليون', 'الإنجليزي', 'المسيحية (الأغلبية)', '180', 2, 'كندا · المكسيك', '13 خط = أول 13 مستعمرة · 50 نجمة = الـ 50 ولاية', 'نيل أرمسترونج: أول إنسان يمشي على القمر (1969)', 'Apple · Google · Microsoft · Jeep · Coca-Cola'],
  ['🇷🇺', 'روسيا', 'موسكو', '144 مليون', 'الروسي', 'المسيحية الأرثوذكسية، والإسلام', '115', 14, 'النرويج · فنلندا · إستونيا · لاتفيا · ليتوانيا · بولندا · بيلاروسيا · أوكرانيا · جورجيا · أذربيجان · كازاخستان · الصين · منغوليا · كوريا الشمالية', 'أبيض وأزرق وأحمر. مالوش معنى رسمي، وبيتقال إنه الصدق والولاء والشجاعة', 'يوري جاجارين: أول إنسان يطلع الفضاء (1961)', 'Gazprom · Lukoil · Kaspersky · Aeroflot · Yandex'],
  ['🇨🇳', 'الصين', 'بكين', '1.41 مليار', 'الصيني (الماندرين)', 'أغلبهم بدون دين؛ البوذية والديانات الشعبية', '80', 14, 'روسيا · منغوليا · كوريا الشمالية · فيتنام · لاوس · ميانمار · الهند · بوتان · نيبال · باكستان · أفغانستان · طاجيكستان · قيرغيزستان · كازاخستان', 'الأحمر = الثورة · النجمة الكبيرة = الحزب الشيوعي · 4 نجوم صغيرة = الشعب', 'كونفوشيوس: فيلسوف أفكاره عن الأخلاق شكّلت آسيا 2500 سنة', 'Huawei · Alibaba · BYD · Lenovo · ByteDance (TikTok)'],
  ['🇮🇳', 'الهند', 'نيودلهي', '1.46 مليار', 'الهندي والإنجليزي (+22 لغة رسمية)', 'الهندوسية (80%)، والإسلام (14%)', '57', 6, 'باكستان · الصين · نيبال · بوتان · بنجلاديش · ميانمار', 'البرتقالي = الشجاعة · الأبيض = السلام · الأخضر = النمو · العجلة = القانون (24 شعاع)', 'المهاتما غاندي: قاد الهند للاستقلال (1947) من غير عنف', 'Tata · Reliance · Infosys · Mahindra · Wipro'],
  ['🇰🇷', 'كوريا الجنوبية', 'سول', '51 مليون', 'الكوري', 'أغلبهم بدون دين؛ المسيحية والبوذية', '190', 1, 'كوريا الشمالية', 'الأبيض = السلام · الدايرة = توازن الين واليانج · الـ 4 رموز = السما والأرض والمية والنار', 'الملك سيجونج: اخترع الأبجدية الكورية (1443)', 'Samsung · Hyundai · Kia · LG'],
  ['🇬🇧', 'بريطانيا', 'لندن', '69 مليون', 'الإنجليزي', 'المسيحية، ونسبة كبيرة بدون دين', '186', 1, 'أيرلندا', 'بيجمع 3 صلبان: إنجلترا واسكتلندا وأيرلندا', 'إسحاق نيوتن: اكتشف قوانين الحركة والجاذبية', 'Rolls-Royce · BP · HSBC · Unilever · Land Rover'],
  ['🇫🇷', 'فرنسا', 'باريس', '68 مليون', 'الفرنسي', 'المسيحية (كاثوليك)، وبدون دين، والإسلام', '189', 8, 'بلجيكا · لوكسمبورج · ألمانيا · سويسرا · إيطاليا · موناكو · أندورا · إسبانيا (+ البرازيل وسورينام عن طريق جويانا الفرنسية)', 'الأزرق والأحمر = ألوان باريس · الأبيض = الملكية · ارتبط بالثورة الفرنسية', 'لويس باستير: عمل اللقاحات واخترع البسترة', 'Louis Vuitton · Chanel · Peugeot · L\'Oréal · Airbus'],
  ['🇯🇵', 'اليابان', 'طوكيو', '123 مليون', 'الياباني', 'الشنتو والبوذية', '190', 0, 'مفيش، جزر', 'الدايرة الحمرا = الشمس: "بلد الشمس المشرقة"', 'هاياو ميازاكي: ستوديو جيبلي، وأوسكار عن Spirited Away', 'Toyota · Sony · Nintendo · Honda'],
  ['🇹🇷', 'تركيا', 'أنقرة', '86 مليون', 'التركي', 'الإسلام (99%)', '118', 8, 'اليونان · بلغاريا · جورجيا · أرمينيا · أذربيجان · إيران · العراق · سوريا', 'الهلال والنجمة من التراث العثماني', 'مصطفى كمال أتاتورك: أسس الجمهورية التركية (1923)', 'Turkish Airlines · Beko · Ülker · Koç'],
  ['🇮🇹', 'إيطاليا', 'روما', '59 مليون', 'الإيطالي', 'المسيحية (كاثوليك)', '189', 6, 'فرنسا · سويسرا · النمسا · سلوفينيا · سان مارينو · الفاتيكان', 'مستوحى من علم فرنسا · الشعبي: الأخضر للأمل والأبيض للإيمان والأحمر للمحبة', 'ليوناردو دافنشي: رسم الموناليزا، وفنان ومخترع', 'Ferrari · Fiat · Gucci · Barilla'],
  ['🇧🇷', 'البرازيل', 'برازيليا', '212 مليون', 'البرتغالي', 'المسيحية (كاثوليك وإنجيليين)', '170', 10, 'الأرجنتين · بوليفيا · كولومبيا · جويانا · باراجواي · بيرو · سورينام · أوروجواي · فنزويلا · جويانا الفرنسية', 'الأخضر والأصفر = الغابات والدهب · الكرة الزرقا = سما ريو ليلة 15 نوفمبر 1889', 'بيليه: كسب كاس العالم 3 مرات (1958، 1962، 1970)', 'Embraer · Petrobras · Havaianas · Natura'],
  ['🇵🇰', 'باكستان', 'إسلام آباد', '250 مليون', 'الأردو والإنجليزي', 'الإسلام (96%)', '31', 4, 'الهند · الصين · أفغانستان · إيران', 'الأخضر = المسلمين · الأبيض = الأقليات · الهلال = التقدم · النجمة = النور والعلم', 'ملالا يوسفزاي: أصغر حد ياخد نوبل للسلام (2014)', 'PIA · Shan Foods · HBL'],
  ['🇮🇩', 'إندونيسيا', 'جاكرتا', '285 مليون', 'الإندونيسي', 'الإسلام (87%)، أكبر عدد مسلمين في العالم', '73', 3, 'ماليزيا · بابوا غينيا الجديدة · تيمور الشرقية', 'الأحمر = الشجاعة · الأبيض = النقاء', 'سوكارنو: أول رئيس، وأعلن الاستقلال (1945)', 'Indomie · Garuda Indonesia · Gojek'],
  ['🇩🇪', 'ألمانيا', 'برلين', '84 مليون', 'الألماني', 'المسيحية، ونسبة كبيرة بدون دين', '190', 9, 'الدنمارك · بولندا · التشيك · النمسا · سويسرا · فرنسا · لوكسمبورج · بلجيكا · هولندا', 'أسود وأحمر ودهبي = ألوان حركة الوحدة والديمقراطية في القرن الـ 19', 'ألبرت أينشتاين: صاحب النظرية النسبية', 'Mercedes-Benz · BMW · Volkswagen · Adidas · Siemens'],
  ['🇮🇱', 'إسرائيل', 'القدس (متنازع عليها دولياً)', '10 مليون', 'العبري (والعربي ليه وضع خاص)', 'اليهودية (73%)، والإسلام (18%)', '165', 4, 'مصر · الأردن · سوريا · لبنان (+ الضفة الغربية وغزة)', 'الخطين الأزرق من شال الصلاة اليهودي · ونجمة داوود', 'إسحاق رابين: وقّع اتفاقية أوسلو (1993) وخد نوبل للسلام', 'Teva · Check Point · Mobileye'],
  ['🇮🇷', 'إيران', 'طهران', '92 مليون', 'الفارسي', 'الإسلام (أغلبية شيعية)', '41', 7, 'العراق · تركيا · أرمينيا · أذربيجان · تركمانستان · أفغانستان · باكستان', 'الأخضر = الإسلام · الأبيض = السلام · الأحمر = الشجاعة · "الله أكبر" مكتوبة 22 مرة', 'عمر الخيام: شاعر الرباعيات وعالم رياضيات وفلك', 'Iran Khodro · Saipa · Digikala'],
  ['🇪🇸', 'إسبانيا', 'مدريد', '49 مليون', 'الإسباني (+ لغات إقليمية)', 'المسيحية (كاثوليك)', '190', 5, 'فرنسا · البرتغال · أندورا · المغرب (سبتة ومليلية) · بريطانيا (جبل طارق)', 'الأحمر والدهبي من مملكة أراجون · الشعار فيه أعمدة هرقل و"Plus Ultra"', 'بابلو بيكاسو: من مؤسسين المدرسة التكعيبية', 'Zara · Santander · Telefónica · SEAT'],
  ['🇦🇺', 'أستراليا', 'كانبرا', '27 مليون', 'الإنجليزي', 'المسيحية، ونسبة كبيرة بدون دين', '185', 0, 'مفيش، قارة لوحدها', 'علم بريطانيا = التاريخ · النجمة الكبيرة = الولايات · الصليب الجنوبي = نجوم سماها', 'هوارد فلوري: حوّل البنسلين لدوا، وخد نوبل (1945)', 'Qantas · BHP · Atlassian · Canva'],
  ['🇪🇬', 'مصر', 'القاهرة', '108 مليون', 'العربي', 'الإسلام (90%)، والمسيحية (10%)', '52', 4, 'ليبيا · السودان · فلسطين (غزة) · إسرائيل', 'الأحمر = النضال قبل 1952 · الأبيض = ثورة 1952 السلمية · الأسود = نهاية الظلم · نسر صلاح الدين', 'نجيب محفوظ: أول عربي ياخد نوبل في الأدب (1988)', 'EgyptAir · Orascom · Elsewedy Electric · CIB · Juhayna'],
  ['🇺🇦', 'أوكرانيا', 'كييف', '37 مليون (تقديري)', 'الأوكراني', 'المسيحية الأرثوذكسية', '147', 7, 'روسيا · بيلاروسيا · بولندا · سلوفاكيا · المجر · رومانيا · مولدوفا', 'الأزرق = السما · الأصفر = حقول القمح', 'إيجور سيكورسكي: اتولد في كييف، وعمل أول هليكوبتر بتتصنع بالكمية', 'Antonov · Nova Poshta · Grammarly (أسسها أوكرانيين)'],
];
const ar = (s) => ({ cls: 'rtl', swipe: 'اسحب →', ...s });
const countryAr = (c, i) => {
  const [flag, name, capital, pop, lang, rel, pass, nb, borders, meaning, famous, brands] = c;
  const [who, what] = famous.split(': ');
  return ar({ theme: i % 2 ? 'light' : 'dark', foot: 'أرقام تقريبية · GFP 2025', body: center(`
    <div style="display:flex;align-items:center;gap:26px"><span style="font-size:120px;line-height:1">${flag}</span><div><span class="tag">المركز ${i + 1} عالمياً</span><h2 style="margin-top:8px;font-size:62px">${name}</h2></div></div>
    <div class="facts">
      <div class="fact"><small>العاصمة</small><span>${capital}</span></div>
      <div class="fact"><small>السكان</small><span>حوالي ${pop}</span></div>
      <div class="fact"><small>اللغة</small><span>${lang}</span></div>
      <div class="fact"><small>الديانة</small><span>${rel}</span></div>
      <div class="fact"><small>قوة الجيش (GFP)</small><span>المركز ${i + 1}</span></div>
      <div class="fact"><small>الباسبور</small><span>حوالي ${pass} دولة من غير فيزا</span></div>
    </div>
    <div class="kv">
      <div class="k">الحدود (${nb})</div><div>${borders}</div>
      <div class="k">معنى العلم</div><div>${meaning}</div>
      <div class="k">أشهر شخصية</div><div><b>${who}</b>: ${what}</div>
      <div class="k">شركات</div><div dir="ltr" style="text-align:right">${brands}</div>
    </div>`) });
};
const ctaAr = (title, text, items) => ar({ theme: 'dark', last: true, body: center(`
  <h1 style="font-size:88px">${title}</h1>
  <p class="sub" style="margin:40px 0 60px">${text}</p>
  <div class="ar" style="display:flex;flex-direction:column;gap:22px;font-weight:600;font-size:34px">${items.map(x => `<div>${x}</div>`).join('')}<div>➕ &nbsp;تابع <span class="gold" dir="ltr">@mina_monir8</span></div></div>`) });
const hookAr = (tag, h1, sub) => ar({ theme: 'dark', foot: 'احفظه لبعدين', body: center(`
  <span class="tag" style="margin-bottom:44px;display:inline-block">${tag}</span><h1>${h1}</h1><p class="sub" style="margin-top:44px">${sub}</p>`) });
const worldAr1 = [
  hookAr('العالم في ٣ أجزاء · الجزء ١', 'أقوى <span class="gold">٢٠ دولة</span> في العالم', 'حسب ترتيب Global Firepower 2025: العاصمة، السكان، اللغة، الدين، الحدود، الباسبور، معنى العلم، وأشهر شخصية وشركات.'),
  ar({ theme: 'light', body: center(`
    <span class="tag">قبل ما نبدأ</span>
    <h2 style="margin:40px 0 36px"><span class="rose">الأمم المتحدة</span></h2>
    <div class="stats">
      <div class="stat"><b>1945</b><span class="lbl">اتأسست ٢٤ أكتوبر ١٩٤٥ بعد الحرب العالمية التانية</span></div>
      <div class="stat"><b>51</b><span class="lbl">دولة مؤسسة، ومصر واحدة منهم</span></div>
      <div class="stat"><b>193</b><span class="lbl">دولة عضو النهارده</span></div>
      <div class="stat"><b>6</b><span class="lbl">لغات رسمية، منها العربي</span></div>
    </div>
    <div class="pill" style="margin-top:30px">٥ أعضاء دايمين في مجلس الأمن: أمريكا، روسيا، الصين، بريطانيا، فرنسا. وكلهم في أول ٧ في الترتيب ده.</div>`) }),
  ...C20.slice(0, 10).map((c, i) => countryAr(c, i)),
  ctaAr('كمّل <span class="gold">الجزء ٢</span>', 'من المركز ١١ لـ ٢٠، ومصر فيهم. وفي الجزء ٣: توقيت زولو، والشمال الحقيقي والمغناطيسي.', ['🔖 &nbsp;احفظ الكاروسيل', '💬 &nbsp;توقّع مركز مصر في الكومنتات']),
];
const worldAr2 = [
  hookAr('العالم في ٣ أجزاء · الجزء ٢', 'من المركز <span class="gold">١١ لـ ٢٠</span> 🌍', 'البرازيل، ألمانيا، اليابان… ومصر. كل دولة في صفحة: العاصمة، السكان، الحدود، الباسبور، العلم، وأشهر شخصية وشركات.'),
  ...C20.slice(10).map((c, i) => countryAr(c, i + 10)),
  ar({ theme: 'light', foot: 'أرقام تقريبية · GFP 2025', body: center(`
    <span class="tag">الـ ٢٠ في صفحة واحدة</span>
    <h2 style="margin:16px 0 12px;font-size:60px">الترتيب <span class="rose">كامل</span></h2>
    <div class="t20"><div class="h">#</div><div class="h">الدولة</div><div class="h">السكان</div><div class="h">الحدود</div><div class="h">من غير فيزا</div>
    ${C20.map((c, i) => { const e = c[1] === 'مصر' ? ' class="eg"' : ''; return `<div${e}>${i + 1}</div><div${e}>${c[0]} ${c[1]}</div><div${e}>${c[3].replace(' (تقديري)', '')}</div><div${e}>${c[7]}</div><div${e}>${c[6]}</div>`; }).join('')}</div>`) }),
  ctaAr('أنهي دولة <span class="gold">فاجئتك؟</span>', 'وفي الجزء ٣: إزاي العالم كله بيظبط ساعته، وليه البوصلة مش بتشاور على الشمال الحقيقي.', ['💬 &nbsp;اكتب اسم الدولة في الكومنتات', '🏷️ &nbsp;اعمل تاج لصاحبك اللي بيحب الجغرافيا']),
];
const worldAr3 = [
  hookAr('العالم في ٣ أجزاء · الجزء ٣', 'ساعة واحدة. <span class="gold">شمالين.</span>', 'جرينتش، توقيت زولو، وإزاي تحسب فرق التوقيت بنفسك، وليه البوصلة مش بتشاور على القطب الشمالي الحقيقي.'),
  ar({ theme: 'dark', body: center(`
    <span class="tag">الساعة · ١/٣</span>
    <div style="display:flex;align-items:center;gap:40px;margin:30px 0 20px">${globe}<h2>منين ساعة العالم <span class="gold">بتبدأ؟</span></h2></div>
    ${li('📍', 'جرينتش في لندن: خط طول صفر', 'خط جرينتش، اللي كل التوقيتات بتتحسب منه')}${li('🤝', 'اتفقوا عليه سنة 1884', 'في مؤتمر دولي في واشنطن')}${li('⚛️', 'من GMT لـ UTC', 'النهارده العالم ماشي بـ UTC، بساعات ذرية')}${li('🌐', 'الناحية التانية: خط 180', 'تقريباً مكان خط التاريخ الدولي')}`) }),
  ar({ theme: 'light', body: center(`
    <span class="tag">الساعة · ٢/٣</span>
    <h2 style="margin:40px 0 30px">احسب توقيتك <span class="rose">بنفسك</span></h2>
    <div class="formula" style="direction:rtl">خط الطول ÷ 15 = الفرق عن UTC بالساعات</div>
    <p class="sub" style="margin:24px 0 30px">الأرض بتلف 360 درجة في 24 ساعة، يعني كل 15 درجة = ساعة. الشرق قدّام (+)، والغرب ورا (−).</p>
    <div class="stats">
      <div class="stat"><b>UTC+2</b><span class="lbl">القاهرة: 31 شرق ÷ 15 ≈ 2</span></div>
      <div class="stat"><b>UTC−5</b><span class="lbl">نيويورك: 74 غرب ÷ 15 ≈ 5</span></div>
    </div>
    <div class="pill" style="margin-top:30px">بس الحدود سياسية: الصين عرضها حوالي ٥ توقيتات وبتستخدم توقيت واحد (UTC+8)، والهند بتستخدم UTC+5:30.</div>`) }),
  ar({ theme: 'dark', body: center(`
    <span class="tag">الساعة · ٣/٣</span>
    <h2 style="margin:40px 0 20px">يعني إيه <span class="gold">توقيت زولو؟</span></h2>
    <p class="sub" style="margin-bottom:24px">Z = UTC+0. الطيارين والبحارة والجيوش بيستخدموا ساعة واحدة للكوكب كله، وكل توقيت ليه حرف:</p>
    <div class="zt">
      <div class="l">Z</div><div dir="ltr" style="text-align:right">Zulu</div><div dir="ltr" style="text-align:right">UTC±0</div><div>لندن (شتا)</div>
      <div class="l">B</div><div dir="ltr" style="text-align:right">Bravo</div><div dir="ltr" style="text-align:right">UTC+2</div><div>القاهرة</div>
      <div class="l">C</div><div dir="ltr" style="text-align:right">Charlie</div><div dir="ltr" style="text-align:right">UTC+3</div><div>موسكو · القاهرة (صيف)</div>
      <div class="l">H</div><div dir="ltr" style="text-align:right">Hotel</div><div dir="ltr" style="text-align:right">UTC+8</div><div>بكين</div>
      <div class="l">R</div><div dir="ltr" style="text-align:right">Romeo</div><div dir="ltr" style="text-align:right">UTC−5</div><div>نيويورك (شتا)</div>
      <div class="l">J</div><div dir="ltr" style="text-align:right">Juliet</div><div>—</div><div>"التوقيت المحلي" في أي مكان</div>
    </div>
    <div class="pill" style="margin-top:28px">الساعة 12:00Z = 14:00 في القاهرة (15:00 صيفي) · 15:00 موسكو · 20:00 بكين · 07:00 نيويورك</div>`) }),
  ar({ theme: 'light', body: center(`
    <span class="tag">الشمالين · ١/٣</span>
    <h2 style="margin:40px 0 36px">البوصلة <span class="rose">بتكدب عليك</span> (شوية)</h2>
    <div class="cards">
      <div class="card d"><div class="l">★ الشمال الحقيقي</div><div class="m">القطب الشمالي الجغرافي، مكان ما محور الأرض بيقابل السطح. ثابت، والخرايط مترسومة عليه.</div></div>
      <div class="card w"><div class="l">🧭 الشمال المغناطيسي</div><div class="m">المكان اللي إبرة البوصلة بتشاور عليه. بيتحرك، لأن الحديد السايل جوه قلب الأرض بيتحرك.</div></div>
    </div>
    <div class="pill" style="margin-top:30px">الشمال المغناطيسي اتحرك من شمال كندا ناحية سيبيريا، بسرعة وصلت لحوالي ٥٠ كيلو في السنة.</div>`) }),
  ar({ theme: 'dark', body: center(`
    <span class="tag">الشمالين · ٢/٣</span>
    <div style="display:flex;align-items:center;gap:40px;margin:30px 0 26px">${compass.replace('TRUE N ★', 'الحقيقي ★').replace('x="248" y="60"', 'x="330" y="34" text-anchor="start"').replace('>MAG N<', '>المغناطيسي<').replace('angle exaggerated', 'الزاوية مكبّرة للتوضيح').replaceAll('font-family="Inter"', 'font-family="Cairo"')}<h2>الفرق بينهم اسمه <span class="gold">الانحراف المغناطيسي</span></h2></div>
    <div class="formula" style="color:var(--cream);font-size:32px;direction:rtl">الحقيقي = المغناطيسي + الانحراف لو شرق<br>الحقيقي = المغناطيسي − الانحراف لو غرب</div>
    <div class="pill" style="margin-top:28px">القاهرة حوالي ٥ درجات شرق: البوصلة بتقول 100 درجة ← الاتجاه الحقيقي 105 درجة.</div>`) }),
  ar({ theme: 'light', body: center(`
    <span class="tag">الشمالين · ٣/٣</span>
    <h2 style="margin:40px 0 30px">إمتى <span class="rose">بيتغير؟</span></h2>
    ${li('🔄', 'طول الوقت', 'شوية كل سنة، ومختلف في كل مكان')}${li('🗺️', 'الخرايط بتكتبه', 'الانحراف، وبيتغير قد إيه كل سنة')}${li('🛰️', 'نموذج المغناطيسية العالمي', 'بيتحدث كل ٥ سنين، وآخر نسخة سنة 2025')}${li('📱', 'موبايلك بيحسبها لوحده', 'شغّل "الشمال الحقيقي" في تطبيق البوصلة')}${li('🔎', 'اعرف رقمك', 'دوّر على "NOAA magnetic declination calculator"')}`) }),
  ctaAr('عرفت <span class="gold">الفرق؟</span>', 'ساعة واحدة للعالم كله، وشمالين مش واحد. الجغرافيا أسهل لما تشوفها في صفحة.', ['💬 &nbsp;اكتب في الكومنتات أكتر معلومة فاجئتك', '🔖 &nbsp;احفظ الأجزاء الـ ٣']),
];
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
  '13-google-vs-tripadvisor': (() => {
    const vs = (rows, dark) => `<div class="vs"><div class="h"></div><div class="h ${dark ? 'gold' : 'rose'}">Google</div><div class="h ${dark ? 'gold' : 'rose'}">TripAdvisor</div>` +
      rows.map(([k, g, t]) => `<div class="k">${k}</div><div>${g}</div><div>${t}</div>`).join('') + `</div>`;
    return [
      { theme: 'dark', foot: 'Save this for later', body: center(`
        <span class="tag" style="margin-bottom:44px;display:inline-block">Restaurant Data · Head to head</span>
        <h1>Google reviews <span class="gold">vs</span> TripAdvisor.</h1>
        <p class="sub" style="margin-top:44px">What data each one gives you, what each one brings you, and which your restaurant needs.</p>`) },
      { theme: 'light', body: center(`
        <span class="tag">Round 1 · The audience</span>
        <h2 style="margin:40px 0 40px">Who's <span class="rose">looking at you?</span></h2>
        ${vs([['Who', 'Locals & anyone nearby', 'Tourists & travellers'], ['When', 'Right now: "restaurant near me"', 'Before & during a trip'], ['Where', 'Google Search & Maps', 'TripAdvisor app & site']])}`) },
      { theme: 'dark', body: center(`
        <span class="tag">Round 2 · Review data</span>
        <h2 style="margin:40px 0 40px">What each <span class="gold">review</span> tells you</h2>
        ${vs([['Rating', '1–5 stars', '1–5 bubbles'], ['Details', 'Food, service, atmosphere', 'Food, service, value, atmosphere'], ['Context', 'Dine-in, takeaway or delivery', 'Who they came with: family, couple, business'], ['Reviewer', 'Public name & photos', 'Name & where they\'re from']], true)}`) },
      { theme: 'light', body: center(`
        <span class="tag">Round 3 · Business data</span>
        <h2 style="margin:40px 0 40px">What your <span class="rose">dashboard</span> shows</h2>
        ${vs([['Reach', 'Searches & views on Maps', 'Page views'], ['Actions', 'Calls, directions, website clicks', 'How visitors engage with your page'], ['Search', 'The words people searched to find you', 'Your ranking: "#12 of 800 in Cairo"'], ['Cost', 'Free', 'Free']])}`) },
      { theme: 'dark', body: center(`
        <span class="tag">Round 4 · Benefits</span>
        <h2 style="margin:40px 0 40px">What each one <span class="gold">brings you</span></h2>
        ${vs([['Guests', 'Everyday locals & walk-ins', 'Tourists who don\'t know the area'], ['Trust', 'Star rating right on the map', 'Rankings & Travelers\' Choice badge'], ['Growth', 'Rank higher in Maps', 'Climb your city ranking']], true)}`) },
      { theme: 'light', body: center(`
        <span class="tag">The verdict</span>
        <h2 style="margin:40px 0 36px">You need <span class="rose">both.</span></h2>
        <div class="ratio">
          <div style="background:#fff"><div style="font:800 30px Inter;color:var(--rose)">Google</div><div style="font:600 30px/1.4 Inter;margin-top:14px">Fills your tables every day with locals.</div></div>
          <div style="background:var(--ink);color:var(--cream)"><div style="font:800 30px Inter;color:var(--gold)">TripAdvisor</div><div style="font:600 30px/1.4 Inter;margin-top:14px">Brings the tourists who'd never find you.</div></div>
        </div>
        <div class="pill" style="margin-top:36px">In a tourist area like Downtown, Zamalek or the coast? Give TripAdvisor the same attention as Google.</div>`) },
      { theme: 'dark', last: true, body: cta('Reply on <span class="gold">both.</span> Read <span class="gold">both.</span>',
        'Two platforms, two audiences, twice the data on what your guests think.',
        'Which one gets you more guests: Google or TripAdvisor?', 'Save this comparison') },
    ];
  })(),
  '14-reservya-expansion': [
    { theme: 'dark', foot: 'Restaurant owners, this is for you', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">Reservya · New cities</span>
      <h1>From El Gouna to <span class="gold">Cairo & Alexandria</span> 📍</h1>
      <p class="sub" style="margin-top:44px">Reservya is coming to your city, and we're looking for our first partner venues.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Our story</span>
      <h2 style="margin:40px 0 30px">It started in <span class="rose">El Gouna</span></h2>
      <p class="sub" style="font-size:36px">We built Reservya with restaurants in El Gouna, learning what venues need to bring guests in and keep them coming back.</p>
      <div class="pill" style="margin-top:44px">Now we're bringing it to the two biggest food scenes in Egypt: Cairo and Alexandria.</div>`) },
    { theme: 'dark', body: center(`
      <span class="tag">What Reservya does for you</span>
      <h2 style="margin:40px 0 30px">More guests. <span class="gold">More regulars.</span></h2>
      ${li('🔎', 'Get discovered', 'Guests find you through the whole network, not just your own page')}${li('🔁', 'Turn visitors into regulars', 'Loyalty that carries across every partner venue')}${li('📅', 'Easy bookings', 'Guests reserve in seconds')}${li('📊', 'Know your guests', 'Data on who comes, when and how often')}`) },
    { theme: 'light', body: center(`
      <span class="tag">Why join early</span>
      <h2 style="margin:40px 0 30px">Be one of the <span class="rose">first</span> in your city</h2>
      ${li('⭐', 'Get seen first', 'Early venues are the ones guests discover first')}${li('🤝', 'Work directly with me', 'I\'m personally onboarding our first partners')}${li('🛠️', 'Shape the product', 'Your feedback decides what we build next')}`) },
    { theme: 'dark', body: center(`
      <span class="tag">Who we're looking for</span>
      <h2 style="margin:40px 0 36px">Is this <span class="gold">your venue?</span></h2>
      <div class="chips" style="margin-bottom:40px"><span class="chip" style="background:var(--cream);color:var(--ink)">Restaurants</span><span class="chip" style="background:var(--cream);color:var(--ink)">Cafés</span><span class="chip" style="background:var(--cream);color:var(--ink)">Lounges</span><span class="chip" style="background:var(--cream);color:var(--ink)">Rooftops</span><span class="chip" style="background:var(--cream);color:var(--ink)">Fine dining</span></div>
      <div class="ratio">
        <div style="background:var(--ink2)"><div style="font:800 34px Inter;color:var(--gold)">📍 Cairo</div><div style="font:500 26px/1.4 Inter;margin-top:12px;opacity:.8">Partner spots open</div></div>
        <div style="background:var(--ink2)"><div style="font:800 34px Inter;color:var(--gold)">📍 Alexandria</div><div style="font:500 26px/1.4 Inter;margin-top:12px;opacity:.8">Partner spots open</div></div>
      </div>`) },
    { theme: 'dark', last: true, body: center(`
      <span class="tag" style="margin-bottom:40px;display:inline-block">Let's talk</span>
      <h1 style="font-size:92px">DM me <span class="gold">"PARTNER"</span></h1>
      <p class="sub" style="margin:40px 0 60px">Send your venue name and city. I'll get back to you personally.</p>
      <div style="display:flex;flex-direction:column;gap:22px;font:600 34px Inter">
        <div>🏷️ &nbsp;Tag a restaurant owner in Cairo or Alex</div>
        <div>🔁 &nbsp;Share with someone who runs a venue</div>
        <div>➕ &nbsp;Follow <span class="gold">@mina_monir8</span> for more venue economics</div>
      </div>`) },
  ],
  '15-teamwork': (() => {
    const L = [
      ['T', 'Trust', 'No trust, no team. Everything else is built on it.', ['Transparency', 'Truth', 'Time together', 'Teaching', 'Tolerance'], 'A team is not a group of people who work together. A team is a group of people who trust each other.', 'Simon Sinek'],
      ['E', 'Empathy', 'Understand how your teammates feel, not just what they do.', ['Encouragement', 'Engagement', 'Energy', 'Equality', 'Effort'], 'Alone we can do so little; together we can do so much.', 'Helen Keller'],
      ['A', 'Accountability', 'Everyone owns their part, and owns their mistakes.', ['Alignment', 'Attitude', 'Appreciation', 'Adaptability', 'Ambition'], 'Teamwork is the ability to work together toward a common vision.', 'Andrew Carnegie'],
      ['M', 'Mutual Respect', 'Respect goes both ways, from the CEO to the newest hire.', ['Motivation', 'Mentorship', 'Morale', 'Mission', 'Mindset'], 'The strength of the team is each individual member. The strength of each member is the team.', 'Phil Jackson'],
      ['W', 'Willingness', 'Ready to help, even when it\'s not "your job".', ['Win together', 'Workload sharing', 'Wellbeing', 'Welcome', 'Wisdom'], 'Talent wins games, but teamwork and intelligence win championships.', 'Michael Jordan'],
      ['O', 'Open Communication', 'Say it clearly, say it early, and listen fully.', ['One goal', 'Ownership', 'Optimism', 'Openness to feedback', 'Organization'], 'None of us is as smart as all of us.', 'Ken Blanchard'],
      ['R', 'Respect', 'Respect people\'s time, roles and ideas.', ['Responsibility', 'Reliability', 'Roles', 'Recognition', 'Resilience'], 'Great things in business are never done by one person. They\'re done by a team of people.', 'Steve Jobs'],
      ['K', 'Kindness', 'Small acts of kindness build big teams.', ['Knowledge sharing', 'Keeping promises', 'Keep going', 'Kudos', 'Knowing each other'], 'If you want to go fast, go alone. If you want to go far, go together.', 'African proverb'],
    ];
    const slides = [
      { theme: 'dark', foot: 'Save this for your next team meeting', body: center(`
        <span class="tag" style="margin-bottom:44px;display:inline-block">Team Building</span>
        <h1>8 letters. 48 words. <span class="gold">One team.</span></h1>
        <p class="sub" style="margin-top:44px">Let's break down the word TEAMWORK, letter by letter, to see what really holds a team together.</p>`) },
      { theme: 'light', body: center(`
        <span class="tag">The word</span>
        <h2 style="margin:40px 0 40px">Every letter is <span class="rose">a lesson</span></h2>
        <div class="tiles">${L.map(l => `<span>${l[0]}</span>`).join('')}</div>
        <div class="quote" style="margin-top:60px">"Not finance. Not strategy. Not technology. It is teamwork that remains the ultimate competitive advantage, both because it is so powerful and so rare."<small>Patrick Lencioni</small></div>`) },
    ];
    L.forEach(([ch, word, meaning, words, q, who], i) => {
      const dark = i % 2 === 0;
      slides.push({ theme: dark ? 'dark' : 'light', body: center(`
        <div style="display:flex;align-items:flex-end;gap:30px;margin-bottom:30px"><span class="letter">${ch}</span><span class="tag" style="margin-bottom:10px">Letter ${i + 1} of 8</span></div>
        <h2 style="margin-bottom:18px">${word}</h2>
        <p class="sub" style="margin-bottom:30px">${meaning}</p>
        <div class="chips" style="margin-bottom:46px">${words.map(w => `<span class="chip alt">${w}</span>`).join('')}</div>
        <div class="quote">"${q}"<small>${who}</small></div>`) });
    });
    slides.push({ theme: 'light', body: center(`
      <span class="tag">The full word</span>
      <h2 style="margin:40px 0 24px">This is <span class="rose">TEAMWORK</span></h2>
      ${L.map(([ch, word]) => `<div style="display:flex;align-items:center;gap:30px;padding:12px 0;border-bottom:2px solid #e0d2c4"><span style="font:800 54px/1 'Playfair Display',serif;color:var(--rose);width:56px">${ch}</span><span style="font:700 34px Inter">${word}</span></div>`).join('')}`) });
    slides.push({ theme: 'dark', last: true, body: center(`
      <h1 style="font-size:92px">Which letter does <span class="gold">your team</span> need most?</h1>
      <p class="sub" style="margin:40px 0 60px">Great teams aren't born. They're built, one letter at a time.</p>
      <div style="display:flex;flex-direction:column;gap:22px;font:600 34px Inter">
        <div>💬 &nbsp;Comment the letter your team needs</div>
        <div>🏷️ &nbsp;Tag your teammate</div>
        <div>🔖 &nbsp;Save it for your next team meeting</div>
        <div>➕ &nbsp;Follow <span class="gold">@mina_monir8</span></div>
      </div>`) });
    return slides;
  })(),
  '16-teamwork-ar': (() => {
    const L = [
      ['T', 'Trust', 'الثقة', 'مفيش ثقة يبقى مفيش تيم. كل حاجة تانية مبنية عليها.', [['Transparency', 'شفافية'], ['Truth', 'صدق'], ['Time together', 'وقت سوا'], ['Teaching', 'تعليم'], ['Tolerance', 'تسامح']], 'التيم مش مجموعة ناس بتشتغل مع بعض. التيم مجموعة ناس بتثق في بعض.', 'سايمون سينك'],
      ['E', 'Empathy', 'التعاطف', 'افهم زميلك حاسس بإيه، مش بس بيعمل إيه.', [['Encouragement', 'تشجيع'], ['Engagement', 'مشاركة'], ['Energy', 'طاقة'], ['Equality', 'مساواة'], ['Effort', 'مجهود']], 'لوحدنا نقدر نعمل حاجة صغيرة، ومع بعض نقدر نعمل حاجات كتير.', 'هيلين كيلر'],
      ['A', 'Accountability', 'المسؤولية', 'كل واحد شايل الجزء بتاعه، وبيعترف بغلطه.', [['Alignment', 'نفس الاتجاه'], ['Attitude', 'أسلوب'], ['Appreciation', 'تقدير'], ['Adaptability', 'مرونة'], ['Ambition', 'طموح']], 'التيم ورك هو إننا نقدر نشتغل مع بعض ناحية رؤية واحدة.', 'أندرو كارنيجي'],
      ['M', 'Mutual Respect', 'الاحترام المتبادل', 'الاحترام رايح جاي، من المدير لأحدث واحد في التيم.', [['Motivation', 'تحفيز'], ['Mentorship', 'توجيه'], ['Morale', 'روح معنوية'], ['Mission', 'هدف'], ['Mindset', 'طريقة تفكير']], 'قوة التيم في كل فرد فيه، وقوة كل فرد في التيم.', 'فيل جاكسون'],
      ['W', 'Willingness', 'الاستعداد', 'تبقى جاهز تساعد، حتى لو مش «شغلتك».', [['Win together', 'نكسب سوا'], ['Workload sharing', 'نشيل الشغل سوا'], ['Wellbeing', 'راحة الفريق'], ['Welcome', 'ترحيب'], ['Wisdom', 'حكمة']], 'الموهبة بتكسب ماتشات، لكن التيم ورك والذكاء بيكسبوا بطولات.', 'مايكل جوردان'],
      ['O', 'Open Communication', 'التواصل المفتوح', 'قول الكلام بوضوح، وبدري، واسمع للآخر.', [['One goal', 'هدف واحد'], ['Ownership', 'ملكية'], ['Optimism', 'تفاؤل'], ['Openness to feedback', 'تقبّل الفيدباك'], ['Organization', 'تنظيم']], 'مفيش حد فينا أذكى مننا كلنا مع بعض.', 'كين بلانشارد'],
      ['R', 'Respect', 'الاحترام', 'احترم وقت الناس وأدوارهم وأفكارهم.', [['Responsibility', 'مسؤولية'], ['Reliability', 'تقدر تعتمد عليه'], ['Roles', 'أدوار'], ['Recognition', 'تقدير'], ['Resilience', 'صمود']], 'الحاجات العظيمة في البيزنس عمرها ما بتتعمل بشخص واحد. بتتعمل بتيم.', 'ستيف جوبز'],
      ['K', 'Kindness', 'اللطف', 'الحاجات الصغيرة اللطيفة بتبني تيمات كبيرة.', [['Knowledge sharing', 'مشاركة المعرفة'], ['Keeping promises', 'الالتزام بالوعد'], ['Keep going', 'كمّل'], ['Kudos', 'شكر'], ['Knowing each other', 'نعرف بعض']], 'لو عايز تمشي بسرعة، امشي لوحدك. لو عايز توصل بعيد، امشوا مع بعض.', 'مثل أفريقي'],
    ];
    const S = 'اسحب →';
    const slides = [
      { theme: 'dark', cls: 'rtl', swipe: S, foot: 'احفظه لاجتماع التيم الجاي', body: center(`
        <span class="tag" style="margin-bottom:44px;display:inline-block">تيم بيلدنج</span>
        <h1>٨ حروف. ٤٨ كلمة. <span class="gold">تيم واحد.</span></h1>
        <p class="sub" style="margin-top:44px">تعالوا نفكك كلمة TEAMWORK حرف حرف، ونشوف إيه اللي بيخلّي التيم تيم بجد.</p>`) },
      { theme: 'light', cls: 'rtl', swipe: S, body: center(`
        <span class="tag">الكلمة</span>
        <h2 style="margin:40px 0 40px">كل حرف <span class="rose">درس</span></h2>
        <div class="tiles">${L.map(l => `<span>${l[0]}</span>`).join('')}</div>
        <div class="quote" style="margin-top:60px">«مش الفلوس، ولا الاستراتيجية، ولا التكنولوجيا. الشغل كتيم هو الميزة التنافسية الحقيقية، لأنه قوي جداً ونادر جداً.»<small>باتريك لينسيوني</small></div>`) },
    ];
    L.forEach(([ch, en, ar, meaning, words, q, who], i) => {
      const dark = i % 2 === 0;
      slides.push({ theme: dark ? 'dark' : 'light', cls: 'rtl', swipe: S, body: center(`
        <div style="display:flex;align-items:flex-end;gap:30px;margin-bottom:24px"><span class="letter">${ch}</span><span class="tag" style="margin-bottom:10px">حرف ${'١٢٣٤٥٦٧٨'[i]} من ٨</span></div>
        <h2 style="margin-bottom:6px">${ar}</h2>
        <div class="en" style="font:700 40px 'Playfair Display',serif;opacity:.7;margin-bottom:18px">${en}</div>
        <p class="sub" style="margin-bottom:28px">${meaning}</p>
        <div class="chips" style="margin-bottom:44px">${words.map(([e, a]) => `<span class="chip alt">${a} · <span dir="ltr">${e}</span></span>`).join('')}</div>
        <div class="quote">«${q}»<small>${who}</small></div>`) });
    });
    slides.push({ theme: 'light', cls: 'rtl', swipe: S, body: center(`
      <span class="tag">الكلمة كاملة</span>
      <h2 style="margin:40px 0 24px">ده هو <span class="rose">TEAMWORK</span></h2>
      ${L.map(([ch, en, ar]) => `<div style="display:flex;align-items:center;gap:30px;padding:12px 0;border-bottom:2px solid #e0d2c4"><span style="font:800 54px/1 'Playfair Display',serif;color:var(--rose);width:56px;text-align:center">${ch}</span><span class="ar" style="font-weight:700;font-size:34px">${ar}</span><span style="font:600 26px Inter;opacity:.55;margin-right:auto" dir="ltr">${en}</span></div>`).join('')}`) });
    slides.push({ theme: 'dark', cls: 'rtl', last: true, body: center(`
      <h1 style="font-size:92px">تيمك محتاج <span class="gold">أنهي حرف</span> أكتر؟</h1>
      <p class="sub" style="margin:40px 0 60px">التيمات العظيمة مش بتتولد كده. بتتبني، حرف حرف.</p>
      <div class="ar" style="display:flex;flex-direction:column;gap:22px;font-weight:600;font-size:34px">
        <div>💬 &nbsp;اكتب الحرف اللي تيمك محتاجه في الكومنتات</div>
        <div>🏷️ &nbsp;اعمل تاج لزميلك</div>
        <div>🔖 &nbsp;احفظه لاجتماع التيم الجاي</div>
        <div>➕ &nbsp;تابع <span class="gold" dir="ltr">@mina_monir8</span></div>
      </div>`) });
    return slides;
  })(),
  '17-geography': geo(false),
  '18-geography-ar': geo(true),
  '19-fb-margins-egypt': (() => {
    const split = [['Food & drinks', 30], ['Staff', 28], ['Rent', 10], ['Utilities & running costs', 8], ['Marketing & apps', 7], ['Waste, repairs, licences', 9]];
    const bars = split.map(([k, v]) => `<div class="bar"><span>${k}</span><i style="width:${v * 3}%"></i><b>${v}</b></div>`).join('') +
      `<div class="bar p" style="border-top:3px solid var(--ink);margin-top:10px;padding-top:24px"><span>Profit</span><i style="width:24%"></i><b>8</b></div>`;
    return [
      { theme: 'dark', foot: 'Save this for later', body: center(`
        <span class="tag" style="margin-bottom:44px;display:inline-block">F&B in Egypt</span>
        <h1>A guest pays EGP 100. <span class="gold">How much does the restaurant keep?</span></h1>
        <p class="sub" style="margin-top:44px">Spoiler: usually less than 10. Here's where the rest goes.</p>`) },
      { theme: 'light', body: center(`
        <span class="tag">First, the bill</span>
        <h2 style="margin:40px 0 30px">Not everything on the bill <span class="rose">is revenue</span></h2>
        ${li('🧾', 'Menu price', 'This is what the restaurant actually earns from')}${li('🏛️', '+14% VAT', 'Goes straight to the government')}${li('🤝', '+ Service charge (often 12%)', 'Usually shared with the team')}
        <div class="pill" style="margin-top:36px">On a EGP 1,000 bill, only about EGP 780 is the menu price. That's what pays every cost, and the profit.</div>`) },
      { theme: 'light', foot: 'Illustrative · typical ranges', body: center(`
        <span class="tag">Where EGP 100 goes</span>
        <h2 style="margin:40px 0 30px">The <span class="rose">real split</span></h2>
        ${bars}`) },
      { theme: 'dark', foot: 'Industry rules of thumb', body: center(`
        <span class="tag">The benchmarks</span>
        <h2 style="margin:40px 0 36px">Know <span class="gold">your numbers</span></h2>
        <div class="stats">
          <div class="stat"><b>28–35%</b><span class="lbl">Food cost, as % of sales</span></div>
          <div class="stat"><b>25–35%</b><span class="lbl">Staff cost, as % of sales</span></div>
          <div class="stat"><b>&lt; 65%</b><span class="lbl">Prime cost: food + staff together</span></div>
          <div class="stat"><b>3–10%</b><span class="lbl">Net profit for most restaurants</span></div>
        </div>`) },
      { theme: 'light', body: center(`
        <span class="tag">Not every item is equal</span>
        <h2 style="margin:40px 0 36px">Your drinks <span class="rose">pay the bills</span></h2>
        <div class="cards">
          <div class="card d"><div class="l">☕ Coffee, juices & soft drinks</div><div class="m">Ingredient cost is often 15–25% of the price</div><div class="big">High margin</div></div>
          <div class="card w"><div class="l">🥩 Mains, especially meat & seafood</div><div class="m">Ingredient cost is often 30–40% of the price</div><div class="big">Lower margin</div></div>
        </div>
        <div class="pill" style="margin-top:36px">Many restaurants make more profit on a cappuccino than on a steak.</div>`) },
      { theme: 'dark', body: center(`
        <span class="tag">The Egypt factor</span>
        <h2 style="margin:40px 0 30px">What squeezes margins <span class="gold">here</span></h2>
        ${li('💱', 'Currency swings', 'Imported ingredients and equipment get pricier overnight')}${li('🏢', 'Rent in prime areas', 'New Cairo, Zayed and the North Coast don\'t come cheap')}${li('⚡', 'Rising energy costs', 'Kitchens run on gas and electricity all day')}${li('📱', 'Delivery app commissions', 'Taken from every order')}${li('🔄', 'Staff turnover', 'Every new hire costs time and training')}`) },
      { theme: 'light', body: center(`
        <span class="tag">Protect your margin</span>
        <h2 style="margin:40px 0 30px">6 moves that <span class="rose">add points</span></h2>
        ${li('1', 'Engineer your menu', 'Push high-margin items, rethink low ones')}${li('2', 'Standard recipes & portions', 'Same plate, same cost, every time')}${li('3', 'Track waste weekly', 'What you throw away is pure lost profit')}${li('4', 'Renegotiate suppliers', 'Compare prices every quarter')}${li('5', 'Review prices regularly', 'Small, frequent changes beat one big jump')}${li('6', 'Grow repeat guests', 'Regulars cost less than new guests')}`) },
      { theme: 'dark', last: true, body: cta('Do you know your <span class="gold">real margin?</span>',
        'Revenue looks good on paper. Profit is what\'s left. Know both, every month.',
        'Comment your food cost %', 'Save this for your next P&L review') },
    ];
  })(),
  '20-pain-no-shows': pain(1, pains[0]),
  '21-pain-empty-weekdays': pain(2, pains[1]),
  '22-pain-staff-turnover': pain(3, pains[2]),
  '23-pain-one-time-guests': pain(4, pains[3]),
  '24-pain-food-waste': pain(5, pains[4]),
  '25-the-world': [
    { theme: 'dark', foot: 'Save this for later', body: center(`
      <span class="tag" style="margin-bottom:44px;display:inline-block">The World Explained</span>
      <h1>5 countries. 1 clock. <span class="gold">2 norths.</span></h1>
      <p class="sub" style="margin-top:44px">The UN, five of the world's biggest powers, Zulu time, and why your compass doesn't point to the North Pole.</p>`) },
    { theme: 'light', body: center(`
      <span class="tag">Where it all meets</span>
      <h2 style="margin:40px 0 36px">The <span class="rose">United Nations</span></h2>
      <div class="stats">
        <div class="stat"><b>1945</b><span class="lbl">Founded 24 October 1945, after World War II</span></div>
        <div class="stat"><b>51</b><span class="lbl">Founding members, Egypt among them</span></div>
        <div class="stat"><b>193</b><span class="lbl">Member states today</span></div>
        <div class="stat"><b>6</b><span class="lbl">Official languages, Arabic one of them</span></div>
      </div>
      <div class="pill" style="margin-top:30px">5 permanent Security Council members: USA, Russia, China, UK and France. Three of them are in this carousel.</div>`) },
    ...countries.map((c, i) => ({ theme: i % 2 ? 'light' : 'dark', foot: 'Rounded figures · GFP 2025 · passport approx.', body: center(`
      <div style="display:flex;align-items:center;gap:26px"><span style="font-size:120px;line-height:1">${c.flag}</span><div><span class="tag">Country ${i + 1} of 5</span><h2 style="margin-top:10px;font-size:64px">${c.name}</h2></div></div>
      <div class="facts">
        <div class="fact"><small>Capital</small><span>${c.capital}</span></div>
        <div class="fact"><small>Population</small><span>${c.pop}</span></div>
        <div class="fact"><small>Language</small><span>${c.lang}</span></div>
        <div class="fact"><small>Religion</small><span>${c.rel}</span></div>
        <div class="fact"><small>Global Firepower</small><span>${c.gfp} in the world</span></div>
        <div class="fact"><small>Passport</small><span>${c.pass}</span></div>
      </div>
      <div class="kv">
        <div class="k">Borders (${c.nb})</div><div>${c.borders}</div>
        <div class="k">The flag</div><div>${c.meaning}</div>
        <div class="k">Famous</div><div>${c.famous}</div>
        <div class="k">Brands</div><div>${c.brands}</div>
      </div>`) })),
    { theme: 'light', foot: 'Rounded figures · GFP 2025 · passport approx.', body: center(`
      <span class="tag">Side by side</span>
      <h2 style="margin:40px 0 36px">How they <span class="rose">compare</span></h2>
      <div class="tbl"><div class="h">Country</div><div class="h">Population</div><div class="h">Military</div><div class="h">Borders</div><div class="h">Visa-free</div>
      ${countries.map(c => `<div>${c.flag} ${c.name}</div><div>${c.pop.replace('~', '').replace(' million', 'M').replace(' billion', 'B')}</div><div class="rose">${c.gfp}</div><div>${c.nb}</div><div>${c.pass.replace(' visa-free', '')}</div>`).join('')}</div>
      <div class="pill" style="margin-top:36px">Russia and China have the most neighbours in the world: 14 each.</div>`) },
    { theme: 'dark', body: center(`
      <span class="tag">The clock · 1/3</span>
      <div style="display:flex;align-items:center;gap:40px;margin:30px 0 20px">${globe}<h2>Where the world's clock <span class="gold">starts</span></h2></div>
      ${li('📍', 'Greenwich, London: 0° longitude', 'The Prime Meridian, the line every time zone counts from')}${li('🤝', 'Chosen in 1884', 'By an international conference in Washington, D.C.')}${li('⚛️', 'GMT → UTC', 'Today the world runs on UTC, kept by atomic clocks')}${li('🌐', 'The other side: 180°', 'Roughly where the International Date Line runs')}`) },
    { theme: 'light', body: center(`
      <span class="tag">The clock · 2/3</span>
      <h2 style="margin:40px 0 30px">Work out your time zone <span class="rose">yourself</span></h2>
      <div class="formula">Longitude ÷ 15 = hours from UTC</div>
      <p class="sub" style="margin:24px 0 30px">The Earth turns 360° in 24 hours, so every 15° is one hour. East is ahead (+), west is behind (−).</p>
      <div class="stats">
        <div class="stat"><b>UTC+2</b><span class="lbl">Cairo: 31°E ÷ 15 ≈ 2</span></div>
        <div class="stat"><b>UTC−5</b><span class="lbl">New York: 74°W ÷ 15 ≈ 5</span></div>
      </div>
      <div class="pill" style="margin-top:30px">But borders are political: China spans about 5 zones and uses just one (UTC+8). India uses UTC+5:30.</div>`) },
    { theme: 'dark', body: center(`
      <span class="tag">The clock · 3/3</span>
      <h2 style="margin:40px 0 20px">What is <span class="gold">Zulu time?</span></h2>
      <p class="sub" style="margin-bottom:24px">Z = UTC+0. Pilots, sailors and armies use one clock for the whole planet. Every zone gets a letter:</p>
      <div class="zt">
        <div class="l">Z</div><div>Zulu</div><div>UTC±0</div><div>London (winter)</div>
        <div class="l">B</div><div>Bravo</div><div>UTC+2</div><div>Cairo</div>
        <div class="l">C</div><div>Charlie</div><div>UTC+3</div><div>Moscow · Cairo (summer)</div>
        <div class="l">H</div><div>Hotel</div><div>UTC+8</div><div>Beijing</div>
        <div class="l">R</div><div>Romeo</div><div>UTC−5</div><div>New York (winter)</div>
        <div class="l">J</div><div>Juliet</div><div>—</div><div>"Local time", wherever you are</div>
      </div>
      <div class="pill" style="margin-top:28px">12:00Z = 14:00 Cairo (15:00 in summer) · 15:00 Moscow · 20:00 Beijing · 07:00 New York</div>`) },
    { theme: 'light', body: center(`
      <span class="tag">The 2 norths · 1/3</span>
      <h2 style="margin:40px 0 36px">Your compass <span class="rose">is lying</span> (a little)</h2>
      <div class="cards">
        <div class="card d"><div class="l">★ True North</div><div class="m">The geographic North Pole, where Earth's axis meets the surface. It doesn't move. Maps are drawn to it.</div></div>
        <div class="card w"><div class="l">🧭 Magnetic North</div><div class="m">Where your compass needle points. It moves, because the liquid iron in Earth's outer core keeps shifting.</div></div>
      </div>
      <div class="pill" style="margin-top:30px">Magnetic north has drifted from northern Canada towards Siberia, at up to about 50 km a year.</div>`) },
    { theme: 'dark', body: center(`
      <span class="tag">The 2 norths · 2/3</span>
      <div style="display:flex;align-items:center;gap:40px;margin:30px 0 26px">${compass}<h2>The gap is called <span class="gold">declination</span></h2></div>
      <div class="formula" style="color:var(--cream);font-size:34px">True = Magnetic + East declination<br>True = Magnetic − West declination</div>
      <div class="pill" style="margin-top:28px">Cairo is about 5° East. Compass reads 100° → true bearing is 105°.</div>`) },
    { theme: 'light', body: center(`
      <span class="tag">The 2 norths · 3/3</span>
      <h2 style="margin:40px 0 30px">When does <span class="rose">it change?</span></h2>
      ${li('🔄', 'All the time', 'A small amount every year, different in every place')}${li('🗺️', 'Maps print it', 'The declination, plus how much it changes per year')}${li('🛰️', 'The World Magnetic Model', 'Updated every 5 years. The latest is from 2025')}${li('📱', 'Your phone does the maths', 'Switch on "true north" in the compass app')}${li('🔎', 'Find yours', 'Search "NOAA magnetic declination calculator"')}`) },
    { theme: 'dark', last: true, body: center(`
      <h1 style="font-size:92px">Which country <span class="gold">should be next?</span></h1>
      <p class="sub" style="margin:40px 0 60px">Five countries, one clock, two norths. The world is easier to understand when you see it on one page.</p>
      <div style="display:flex;flex-direction:column;gap:22px;font:600 34px Inter">
        <div>💬 &nbsp;Comment the next country you want</div>
        <div>🔖 &nbsp;Save this for later</div>
        <div>🏷️ &nbsp;Tag a friend who loves geography</div>
        <div>➕ &nbsp;Follow <span class="gold">@mina_monir8</span></div>
      </div>`) },
  ],
  '26-world-ar-part1': worldAr1,
  '27-world-ar-part2': worldAr2,
  '28-world-ar-part3': worldAr3,
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const [name, slides] of Object.entries(carousels)) {
    const dir = path.join(__dirname, name);
    fs.mkdirSync(dir, { recursive: true });
    const html = `<!doctype html><html><head><meta charset="utf-8">${fonts}<style>${style}</style></head><body>` +
      slides.map((s, i) => `<section class="slide ${s.theme} ${s.cls || ''}">${top(i + 1, slides.length)}${s.body}${bot(s.foot, s.last, s.swipe)}</section>`).join('\n') +
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
