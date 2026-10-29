# Pitching When the First Reader Is an AI: Playbook

Source material: Vera Futorjanski, *How to Pitch to Investors* (Veritas Ventures, Global Entrepreneurship Festival,
EIP Investment Readiness Training, 18 slides). Plus research on how VC firms use AI in 2026 (sources at the end).

---

## Part 1: The training, distilled

### The 16 slides at a glance

| # | Slide | The point | What the investor is thinking |
|---|-------|-----------|-------------------------------|
| 3 | Know who you're pitching | **Research** the right investors. **Segment** them by ticket size and type. **Life hack:** practise on investors you don't actually want. | "Why are you in my inbox? Do you fit my thesis?" |
| 4 | Come prepared | One-story **deck** with simple slides. **Rehearse** several versions. **Know your numbers** cold. | "Can this founder answer without looking?" |
| 5 | Always be fundraising | Not always asking for money. Always keeping the relationship going. | "I've been watching them for 6 months and they did what they said." |
| 6 | The golden rule | **Clear, simple, memorable messages.** | "Can I repeat this to my partners in one sentence?" |
| 7 | Your story | Sell an **opportunity**, not a product. Make it **personal** (why you, why now). **Capture the imagination.** | "What does the world look like if this works?" |
| 8 | 01 Introduction | Catchy opener. Win the first **30 seconds**. | "Interesting name, but I don't get what it is. Why are you doing this?" |
| 9 | 02 Problem | The opportunity nobody else sees. Why it matters. **Market size and growth.** | "Is this a real pain for a lot of people? How big can it get?" |
| 10 | 03 Solution | **Value proposition** (what changes for the customer), **product** (show it, keep it simple), **business model** (how you make money). | "Surely others are working on this. How are you unique?" |
| 11 | 04 Why you | Extraordinary team, uniquely qualified, track record. | "Do you have the experience, and are you obsessed?" |
| 12 | 05 Differentiation | What sets you apart, **use visuals**. **Never say there is no competition.** | "Now show me metrics, engagement, revenue. (There are always competitors.)" |
| 13 | 06 Plans & success | **Done / Doing / Next.** | "Dream plus roadmap. You'll deploy money to raise value and cut risk. I love KPIs and unit economics." |
| 14 | 07 Financial summary | Historicals + 3-year projections, amount raised, pre-money & terms, **use of funds as a % pie**. | "I'll test every figure. Can you explain each one without looking?" |
| 15 | Powerful language | hope→**will**, think→**are convinced**, might be→**will be**, interest from <industry>→interest from **<named company>** | Confidence and specificity read as credibility. |
| 16 | Negotiation | Negotiate as if you have nothing to lose, but don't show you need the money. | Leverage comes from alternatives. |

### The five ideas underneath everything

1. **Fit beats quality.** A great deck sent to the wrong fund is a rejection. (Slide 3)
2. **Every slide answers an objection.** The "Investor mind" boxes are the real script. Each slide exists to kill the
   doubt in that box before the next slide.
3. **Specific beats impressive.** "Interest from Carrefour" beats "interest from retail". "We will" beats "we hope".
4. **Numbers are a test of the founder, not just the business.** Hesitation on a metric costs more than a weak metric.
5. **Relationship over transaction.** Investors invest in lines, not dots: they want to see a trajectory over time.

Here is why this matters for AI: **an AI screener asks the same questions as the "Investor mind" boxes**, just faster
and more literally. Answer them explicitly in the deck and you serve both readers at once.

---

## Part 2: Do VCs use AI to pick deals? (research)

### What is actually happening (2026)

- **Sourcing and tracking are heavily AI-driven.** EQT's *Motherbrain* (since 2016) tracks 15M+ companies using public
  signals (hiring, LinkedIn, app rankings, web traffic, funding) and is credited with sourcing deals worth over $100M of
  EQT Ventures' capital. SignalFire, Correlation Ventures and others run their own models. Harmonic, Specter and Affinity
  sell these signals to everyone else.
- **First-pass deck reading is increasingly automated.** An Affinity survey reports 85% of private-capital firms use AI
  for daily tasks and 82% for sourcing research. Tools such as Affinity extraction, Kruncher, V7, or simply Claude/GPT
  with a firm-specific prompt pull the facts out of the deck, score them against the fund's thesis, and write a memo.
- **Humans still decide.** Some practitioners think production-grade AI deck triage is rarer than the hype suggests.
  The realistic model: **AI decides who gets a human's attention, and humans decide who gets money.**
- **Public analyzers show you the rubric.** SaaStr.ai (traction score with growth at 55/100 points, deck quality
  benchmarked against funded decks), 1752vc, Unbiased Ventures/DeckAnalyst (7 VC dimensions). They all converge on
  the same dimensions: market, problem, traction, team, business model, competition, financials and ask, clarity.
- **Hidden-text tricks are detected.** Research on resume screening found about 1% of PDFs contain hidden prompt
  injections (white text, tiny fonts) and built detectors for them. PhantomLint and similar tools scan documents for
  exactly this. **Never put hidden instructions in a deck.** It is deception, it gets flagged, and it ends the
  relationship permanently, because VCs share notes.

### How an AI screener reads your deck (the pipeline)

```
PDF/DocSend  ->  text + OCR extraction  ->  field extraction  ->  thesis filter  ->  scoring rubric  ->  memo + rank
                 (images with text      (sector, stage, geo,   (hard no's:       (team, market,      (human reads
                  may be missed)         ARR, growth, raise,    wrong stage,      traction, moat,     top X%)
                                         team, competitors)     wrong geo)        clarity, risks)
     +  external enrichment: LinkedIn, website, Crunchbase, hiring, traffic, app reviews, news, GitHub
```

Two consequences follow:
- **If a fact lives only inside an image, the AI may not see it.** Put key numbers in real text as well.
- **The AI cross-checks you against the internet.** A claim your LinkedIn, website or traffic contradicts is a red flag.

### Scenarios on five levels

| Level | Who / setup | What the AI does | What decides your fate | Your move |
|-------|-------------|------------------|------------------------|-----------|
| **L0: no AI** | Angel, small syndicate | Nothing. Human reads on a phone | First 30 seconds, warm intro | Slide 8 rules: a hook and one clear sentence |
| **L1: AI assistant** | Associate pastes deck into ChatGPT/Claude: "summarise and list risks" | Summary + risk list the partner reads *instead of* the deck | Whether the summary sounds fundable, and which risks it lists | Write the summary yourself (slide 2 TL;DR). Pre-answer the obvious risks |
| **L2: CRM extraction** | Affinity / Kruncher / Attio auto-parse inbound | Fills fields: stage, sector, ARR, growth, raise, location | Missing or ambiguous fields mean you drop out of filters | Label numbers plainly: "ARR: $420K (Sep 2026)". Same terms as the fund's site |
| **L3: thesis scoring** | Custom rubric, deck scored 1-10 per dimension, top 10-20% to humans | Scores team, market, traction, moat, clarity; compares with past winners | Thesis fit + evidence density per dimension | Map one slide to each dimension. Evidence, not adjectives |
| **L4: signal-first** | Motherbrain-style. Deck is secondary; your digital footprint is scored continuously | Tracks hiring, traffic, reviews, downloads, founder history over time | Momentum *trend*, consistency between deck and world | "Always be fundraising": public, steady signals for 6-12 months before the raise |
| **L5: agentic diligence** | AI agent researches the market, calls APIs, checks references, models financials | Verifies claims, builds a competitor map, stress-tests projections | Whether the claims survive verification | Data room ready, every number sourced, competitor list more honest than theirs |

### The judgement

1. **Assume L1-L3 for every fund in 2026**, and L4 for big multi-stage funds (EQT, a16z, SignalFire, Sequoia,
   Accel, Lightspeed). Even "no AI" funds have an associate who pastes your deck into an assistant.
2. **The AI is not the decision-maker. It is the gatekeeper and the first narrator.** Its summary frames how the partner
   reads you. Your job is to make sure the summary *it* writes matches the one *you* would write.
3. **The things that please the AI are the same things that please the partner:** clarity, specificity, evidence,
   honest competition, clean numbers. There is no trade-off. Gaming tricks (keyword stuffing, hidden text, inflated
   claims) fail at L3+ because they get cross-checked, and at the human stage because they read as fake.
4. **The biggest controllable lever is consistency.** Deck, website, LinkedIn, Crunchbase and the founders' own words
   must tell the same story with the same numbers.

### Execution plan (8 weeks before sending a single deck)

| Week | Action | Output |
|------|--------|--------|
| 1 | **Investor research and segmentation (slide 3).** 60-100 funds: thesis, stage, ticket, geo, recent deals, partner who covers your sector. Note whether they run a known AI platform | Spreadsheet: Tier A (dream, 15), Tier B (good fit, 30), Tier C (practice, 20) |
| 1-2 | **Footprint audit (L4).** Align website, LinkedIn (every founder), Crunchbase/Dealroom, app store, GitHub. Same one-liner, same numbers, same dates | Consistency checklist, all green |
| 2-3 | **Rebuild the deck** to the structure in Part 3. Text-extractable PDF. TL;DR slide | Deck v1 |
| 3 | **Run the AI committee (Part 4)** on deck v1 with 3+ different models | Scores + objection list |
| 3-4 | **Fix and re-run** until every dimension is 8+/10 and no model misreads a key fact | Deck v2, v3 |
| 4 | **Data room**: financial model, cap table, customer contracts/LOIs, metrics dashboard, team bios, IP | Data room index |
| 4-5 | **Humanize pass (Part 6)**: founder voice, real anecdotes, no generic phrasing | Deck final + 3 email variants |
| 5 | **Practice round on Tier C** ("life hack" slide). Log every question asked | Q&A bank, objections ranked by frequency |
| 6 | Update deck and defense from Tier C feedback. **Start Tier B** | Meetings |
| 7-8 | **Tier A**, ideally by warm intro, with momentum ("we're in conversations with X funds, closing in Y weeks"). Monthly update emails to everyone who said "too early" | Term sheets |

---

## Part 3: The deck structure both the AI and the partner want

12-14 slides. Each one answers an "Investor mind" box, and each maps to a scoring dimension.

| # | Slide | Must contain (in real text, not only images) | Scoring dimension |
|---|-------|----------------------------------------------|-------------------|
| 1 | **Title** | Company, **one-line description in plain words** ("X helps Y do Z"), stage, raise, location | Extraction |
| 2 | **TL;DR** | 5 bullets: problem, solution, traction number, team edge, ask. *This is what L1 summaries copy* | Clarity |
| 3 | **Problem** | Who hurts, how often, what it costs them today. One customer quote with name/role | Problem |
| 4 | **Why now** | The shift (tech, regulation, behaviour) that makes this possible now and not 5 years ago | Timing |
| 5 | **Solution / product** | Screenshot + "before → after" for the customer. 3 lines max | Solution |
| 6 | **Traction** | One chart, axes labelled, dates, **growth rate written as a number** (e.g. "+18% MoM, 9 months"). Retention, pilots, LOIs with named companies | Traction (biggest weight) |
| 7 | **Market** | Bottom-up TAM/SAM/SOM (number of customers × price), source cited | Market |
| 8 | **Business model** | Pricing, ACV, gross margin, CAC, LTV, payback | Unit economics |
| 9 | **Competition** | 2×2 or table with **named** competitors, honest strengths, your edge. Never "no competition" | Moat |
| 10 | **Team** | Why *these* people: past exits, domain years, unfair insight. Photos + LinkedIn handles | Team |
| 11 | **Done / Doing / Next** | Milestones met (with dates), current focus, next 18 months tied to KPIs | Execution |
| 12 | **Financials** | Historicals + 3-year projection, key assumptions stated | Financials |
| 13 | **The ask** | Amount, instrument (SAFE/equity), **use of funds as % pie**, the milestone this money buys | Ask |
| 14 | **Vision close** | The future you are building in one sentence + contact | Memorability |

### AI-readability rules (the technical layer)

- Export a **text-based PDF** (not scanned images). Test it: copy-paste all text out of it. Whatever doesn't paste, the
  AI may not see.
- **Every chart has a one-line takeaway in text** above it ("Revenue grew 4.2× in 12 months").
- **Label every number:** unit, currency, date, definition. "$38K MRR (Oct 2026)", not "38K".
- **Use the fund's vocabulary.** If their site says "vertical SaaS for logistics", say that, not "supply-chain
  orchestration layer".
- **Same numbers everywhere:** deck, email, website, LinkedIn, data room. Mismatches are the #1 red flag at L3+.
- **File name:** `CompanyName_Seed_2026-10.pdf`. Never `deck_final_v7.pdf`.
- **Under 15 MB, under 20 slides.** Appendix for detail.
- **No hidden text, no instructions to AI, no keyword stuffing.** Detected, and fatal.

### Powerful language, extended (slide 15)

| Instead of | Say |
|------------|-----|
| We hope to reach... | We will reach... by <date> |
| We think the market is... | The market is $X (source) |
| We might be the first... | We are the only ones doing X for Y, because Z |
| Interest from retail | LOI from <Company>, pilot with <Company> |
| Huge market | 42,000 clinics in the EU × €3,600/yr = €151M SAM |
| Revolutionary AI-powered platform | Cuts invoice processing from 6 days to 4 hours |
| Strong team | CTO built <Company>'s payment stack (40M users) |
| Fast growing | +22% MoM for 7 consecutive months |

---

## Part 4: The judgement committee

Run the deck past a panel before any real investor sees it. Each "judge" is one persona. You can run them as separate
prompts in Claude, GPT and Gemini (different models disagree in useful ways), or as people role-playing.

### The seven judges

| Judge | Persona | Main question | Fails you if |
|-------|---------|---------------|--------------|
| **1. The Screener (AI L2-L3)** | Automated thesis filter | "Can I extract stage, sector, traction, raise and team in 10 seconds, and do they match the thesis?" | Any key field missing or ambiguous |
| **2. The Associate** | 26 years old, reads 40 decks/day on a phone | "Can I explain this to my partner in one sentence?" | Can't summarise it after 60 seconds |
| **3. The Market Partner** | Ex-operator in your sector | "Is this a real pain, how big, why now?" | Top-down TAM only, vague customer |
| **4. The Numbers Partner** | Ex-banker | "Do the unit economics and projections hold up?" | Hockey stick with no assumptions, CAC missing |
| **5. The Sceptic** | Has seen 10 failed versions of your idea | "Why didn't the others work, and why will you?" | "No competition", no answer to "why you" |
| **6. The Verifier (AI L5)** | Agent with web access | "Does the outside world confirm the deck?" | LinkedIn, site or traffic contradict a claim |
| **7. The Human-Feel Judge** | Partner allergic to generic copy | "Does this sound like a real founder or like a template?" | Buzzwords, no story, no specifics |

### Scorecard (each judge scores 1-10; pass = average 8+, no dimension under 6)

| Dimension | Weight | 10 looks like |
|-----------|--------|---------------|
| Clarity (one-sentence test) | 10% | Anyone can repeat what you do after slide 1 |
| Problem & why now | 10% | Named customer pain, cost quantified, clear trigger |
| Traction | 25% | Growth rate, retention, named customers, dated |
| Market | 10% | Bottom-up, sourced |
| Business model & unit economics | 10% | CAC, LTV, margin, payback stated |
| Competition & moat | 10% | Named competitors, honest, defensible edge |
| Team | 15% | Founder-market fit with proof |
| Financials & ask | 5% | Assumptions, % use of funds, milestone |
| Consistency & verifiability | 5% | Zero contradictions with the public footprint |

### Committee prompt (copy and paste, once per judge)

```
You are [JUDGE NAME]: [PERSONA LINE]. You work at a [STAGE] fund investing [TICKET] in [SECTORS] in [GEOGRAPHY].
You receive 400 decks a month and advance 5%.

Read the attached deck. Do NOT be encouraging. Then answer:
1. In one sentence: what does this company do? (If you can't, say so.)
2. Extract: stage, sector, location, revenue/ARR, growth rate, customers, raise amount, instrument, team background.
   Mark anything missing or ambiguous.
3. Score each dimension 1-10 with a one-line reason: clarity, problem/why now, traction, market,
   business model, competition/moat, team, financials/ask, consistency.
4. Your top 5 objections, ranked by how likely they make you pass.
5. The 10 hardest questions you'd ask in a partner meeting.
6. Decision: ADVANCE / HOLD / PASS, and the single change that would flip it.
7. Quote any sentence that sounds generic, template-like or AI-written.
```

Iterate until three different models, run cold, all return ADVANCE and agree on the one-sentence description.
**If the models describe your company differently, your deck is not clear yet.**

---

## Part 5: Defense plan (making sure they choose us)

### Layer 1: Pre-empt (inside the deck)

Every "Investor mind" box becomes a sentence in the deck that answers it before it's asked:

| Doubt | Pre-emptive line on the slide |
|-------|-------------------------------|
| "I don't understand what it is" | Slide 1 one-liner + slide 2 TL;DR |
| "Is this a real pain for many people?" | Customer quote + "N customers pay €X today to solve this badly" |
| "Surely others are doing this" | Competition table with named players + "why they can't copy us in 12 months" |
| "Can this team do it?" | One proof point per founder that no one else has |
| "Will they deploy money well?" | Done/Doing/Next + use-of-funds % pie tied to a milestone |
| "Are the numbers real?" | Dated, labelled, sourced. Data room link |

### Layer 2: Q&A bank (know your numbers cold)

Build a document with the **50 most likely questions** (from the committee and Tier C meetings), each with a
**15-second answer** and a **2-minute answer**. Every founder rehearses it. Minimum set:

- Numbers: MRR/ARR, growth MoM, burn, runway, CAC, LTV, payback, gross margin, churn/retention, ACV, pipeline.
- "Why hasn't Google / <big player> done this?"
- "What happens if <top competitor> copies you?"
- "What's the biggest risk, and how are you killing it?"
- "Why this valuation?" (comparable rounds, not feelings)
- "What do you do if you don't raise?" (this is your leverage, see slide 16)
- "Who else is in the round?"
- "Why you, why now, why does this matter to you?" (slide 7, personal story, 60 seconds, rehearsed until natural)

### Layer 3: The red-flag kill list

Fix every one of these before sending:
- [ ] "No competition" or "first mover" as the moat
- [ ] Top-down TAM ("1% of a $50B market")
- [ ] Projections with no stated assumptions
- [ ] Numbers that differ between slides, website or email
- [ ] Founders' LinkedIn not matching titles or dates in the deck
- [ ] Unlabelled chart axes, metrics with no date
- [ ] "We hope / we think / we might"
- [ ] Generic buzzwords: revolutionary, disruptive, seamless, cutting-edge, leverage, synergy, game-changer, AI-powered
      (unless it's literally the product)
- [ ] Raising "to grow": no milestone tied to the money
- [ ] Desperation signals: "closing this week", "urgent", discount offers

### Layer 4: Signals (L4 defense, "always be fundraising")

What signal-scoring platforms watch, and what to keep moving for 6-12 months before and during the raise:
- **Hiring:** job posts and team growth on LinkedIn (even 1-2 posts show momentum).
- **Product:** release notes or changelog, app updates, reviews, GitHub activity if relevant.
- **Traffic and demand:** website traffic trend, waitlist, social following growth in the right audience.
- **Credibility:** press, awards, accelerators, named partnerships, founders speaking at events (like this festival).
- **Monthly investor update email** to every fund you've met: 3 wins, 1 challenge, KPIs, 1 ask. This is the "line
  not a dot" that slide 5 describes.

### Layer 5: The meeting and the negotiation

- **First 30 seconds** (slide 8): open with the customer's pain in one concrete story, then the one-liner.
- **Show the product live or in a 60-second video.** "Show it. Keep it simple."
- **End every meeting with a next step and a date.**
- **Negotiate from alternatives** (slide 16): run the process in parallel, compress meetings into 2-3 weeks so term
  sheets land together, never reveal runway pressure, know your walk-away terms before the first call.
- **Follow up within 24 hours** with a short email: the 3 things they asked about, answered.

---

## Part 6: Humanizing (no "AI feel" anywhere)

What actually makes a deck feel "made by AI" isn't a detector score. It's **genericness**: it could describe any
startup. Partners and AI judges both notice it. The fix is never to disguise AI text. **Replace it with things only you
could write.** Content built on your real data and your real voice is human by definition and passes any review,
because there is nothing to catch.

### The AI-tell checklist (remove all of these)

| AI tell | Example | Human version |
|---------|---------|---------------|
| Buzzword stacks | "A revolutionary, AI-powered platform that seamlessly empowers..." | "Clinics book 30% more appointments because patients can rebook on WhatsApp" |
| Rule of three, everywhere | "Fast, simple, and secure." | Say the one that matters, with a number |
| Balanced "not only X but also Y" | "Not just a tool, but a movement" | Delete it |
| Abstract nouns | "Unlocking value, driving synergy" | A verb, a person, a number |
| Perfect symmetry | Every bullet the same length and rhythm | Vary it. Some bullets are 3 words |
| Em-dash chains and colon headlines | "Our Vision — Redefining the Future of..." | "Where this goes" |
| No names | "Leading retailers" | "Spinneys and Carrefour Egypt" |
| No dates | "Recently grew rapidly" | "Went from 12 to 87 clinics between March and September" |
| Vague founder story | "Passionate about solving this problem" | "I spent 3 years running my mother's pharmacy in Alexandria and lost €40K to expired stock" |
| Safe, hedged claims | "We believe we may be able to..." | "We will" (slide 15) |
| Stock imagery | Handshake, globe, lightbulb | Your product screenshot, your team, your customer |

### The humanize method

1. **Talk it, don't write it.** Each founder records themselves explaining each slide to a friend, unscripted, for
   2 minutes. Transcribe the recording. Your real sentences come from there, with your words, rhythm and opinions.
2. **One story per section.** A real customer, a real moment, a real mistake. Investors remember stories (slide 7:
   "make it personal").
3. **Add one opinion they might disagree with.** "Everyone in this space sells to hospitals. That's why they're
   slow. We sell to the nurses." Templates never take a position.
4. **Keep small imperfections of voice.** Contractions (we're, don't), short sentences, a dry line of humour where it
   fits. Not typos.
5. **Specific > polished.** If a sentence could appear in another company's deck unchanged, rewrite it.
6. **The read-aloud test.** Read every slide out loud. If you'd never say it that way to an investor across a table,
   change it.
7. **The swap test.** Replace your company name with a competitor's. If the slide still works, it's generic.
8. **The cold-reader test.** Give it to someone outside the industry. If they can repeat your one-liner and remember
   one story, you're done.

### Emails, too

Cold or intro email, under 120 words, written by the founder:

```
Subject: <Company>: <traction number> in <timeframe>, raising <amount> <stage>

Hi <Name>,

<One line on why them: a specific deal or post of theirs that connects to you.>

We <do X for Y>. Since <month> we've gone from <A> to <B> (<named customer> is one of them).

I started this after <one-sentence personal reason>.

Raising <amount> to <specific milestone>. Deck attached, 12 slides.

Worth 20 minutes next week?

<Name>, <title>
<phone>
```

---

## Part 7: Final pre-send checklist

- [ ] Fund is in Tier A/B and matches stage, sector, ticket, geo
- [ ] One-liner identical across deck, email, website, LinkedIn
- [ ] PDF text is copy-pasteable; every chart has a text takeaway
- [ ] Every number labelled (unit, date) and consistent everywhere
- [ ] Named competitors, named customers/LOIs
- [ ] Bottom-up market size with a source
- [ ] Done / Doing / Next with dates
- [ ] Use of funds as a % pie tied to a milestone
- [ ] Three AI models, run cold, return ADVANCE and agree on the one-liner
- [ ] Zero buzzwords from the kill list; passes the read-aloud and swap tests
- [ ] No hidden text, no prompts aimed at AI readers
- [ ] Q&A bank rehearsed; every founder can state every key metric without looking
- [ ] Data room ready before the first meeting
- [ ] Practised on at least 3 Tier C investors first

---

## Sources

- [AI for Pitch Deck Analysis: A Guide for VC Teams (2026), V7 Labs](https://www.v7labs.com/blog/ai-pitch-deck-analysis)
- [AI in Venture Capital: How Investors Use AI for Deal Evaluation in 2026, SeedForge](https://seedforge.com/blog/ai-in-venture-capital-deal-evaluation-2026)
- [AI Pitch Deck Screening: What VCs Are Actually Doing, Capitaly](https://capitaly.substack.com/p/ai-pitch-deck-screening-what-vcs)
- [Pitching AI in 2026: What VCs Really Want, Gatekeep](https://gatekeep.vc/blog/pitching-ai-in-2026-what-vcs-really-want-and-how-to-stand-out)
- [How EQT uses AI to see the startup world differently, tech.eu (Nov 2025)](https://tech.eu/2025/11/20/how-eqt-uses-ai-to-see-the-startup-world-differently/)
- [How Venture Capital Funds Leverage AI and Big Data, VC Cafe](https://www.vccafe.com/how-venture-capital-funds-leverage-ai-and-big-data/)
- [Venture Investors Turn To AI To Find Deals, Crunchbase News](https://news.crunchbase.com/venture/venture-investors-ai-deal-sourcing/)
- [SignalFire vs Rebel Fund vs InReach: AI deal-sourcing platforms](https://www.rebelfund.vc/blog-posts/signalfire-vs-rebel-fund-vs-inreach-2025-ai-deal-sourcing-platforms)
- [4,000 pitch decks later: what the SaaStr AI VC analyzer does](https://www.saastr.com/4000-pitch-decks-later-what-the-saastr-ai-vc-analyzer-actually-does-and-what-its-taught-us-about-fundraising-in-2026/)
- [1752vc launches free AI pitch deck analyzer](https://www.wboc.com/online_features/press_releases/1752vc-launches-free-ai-pitch-deck-analyzer-to-democratize-access-to-investor-grade-feedback/article_e5b77def-36e3-513f-ab7b-02d29c052a13.html)
- [Unbiased Ventures DeckAnalyst](https://ai.g2.com/marketplace/tools/unbiased-ventures)
- [Measuring Real-World Prompt Injection Attacks in LLM-based Resume Screening (arXiv)](https://arxiv.org/html/2605.28999v1)
- [PhantomLint: detecting hidden LLM prompts in documents (arXiv 2508.17884)](https://web3.arxiv.org/abs/2508.17884)

Note: the adoption figures come from vendor and blog sources and were not independently verified.
