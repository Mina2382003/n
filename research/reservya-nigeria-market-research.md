# Reservya in Nigeria: Market Research

*Prepared November 2026. Figures come from public sources linked at the end. Market-size numbers are paid-report estimates, not official statistics, so treat them as directional.*

## 1. Summary

Nigeria is a big, growing hospitality market and a hard one to win. The opportunity is real. Foodservice is worth about $11–12B and growing about 12% a year. Lagos has a strong nightlife and premium-dining scene, and the December diaspora season brings a large, predictable peak in demand. Digital payments are now normal.

Two things make it tough:

1. **The in-venue software layer is being taken by funded local players.** In March 2026 Moniepoint, Nigeria's biggest merchant-payments company, bought Orda, the leading restaurant OS. Chowdeck, the leading food-delivery app, bought Mira in 2025. Reservya should not compete with them as a POS or operations tool.
2. **The diner-side reservation apps exist but are small.** Reisty, Dinesurf, MyNexTable and TableLynk are all early stage. Nobody owns guest discovery, booking and loyalty for premium restaurants and lounges yet. That gap is where Reservya fits.

**Recommendation:** Enter Lagos only (Lekki, Victoria Island, Ikoyi), with a narrow wedge: **paid table reservations for premium restaurants and lounges**. That means deposits and minimum-spend tables paid through Paystack, Flutterwave or bank transfer, plus a guest CRM and repeat-visit tools. Launch around **Detty December**, and plan to integrate with Moniebook and Paystack rather than replace them. Run a low-cost pilot first (Section 8) before committing a team.

## 2. What Reservya brings

Based on the company's own materials:

- **B2B:** a dashboard for restaurants, bars and lounges to manage reservations and guest relationships.
- **B2C:** an app where guests discover and book dining and nightlife.
- **Track record:** Reservya started with venues in El Gouna, Egypt, and is expanding to Cairo and Alexandria.

Egypt and Nigeria share several traits, so the playbook should transfer reasonably well: venues take bookings over WhatsApp and Instagram today, a nightlife and lounge culture drives table demand, a tourist season creates a seasonal peak, and the currency has been volatile. The big difference is scale. Lagos alone has a population of about 15–20M+, and its premium segment is much larger than El Gouna's.

## 3. Market size and demand

| Indicator | Figure | Source |
|---|---|---|
| Nigeria foodservice market, 2025 | ~$11.1B (Mordor); ~$11.2B (Bonafide) | Mordor Intelligence, Bonafide |
| 2026 estimate | ~$12.4B | Mordor (2026 edition) |
| 2030 forecast | ~$19.3B, ~11.7% CAGR | Mordor Intelligence |
| Independent (non-chain) outlets | ~71% of market | Mordor Intelligence |
| Quick-service restaurants | ~56% of market | Mordor Intelligence |
| Detty December 2025 spend (Lagos, 55 days) | ₦396.5B, ~55% from diaspora, nearly half in hospitality | MO Africa report via BusinessDay / Nairametrics |
| Top diaspora source market | USA (overtook UK in 2025) | Nairametrics |

**What this means for Reservya:**

- The total market is dominated by quick-service food (Chicken Republic, Kilimanjaro, etc.), which doesn't need reservations. **Reservya's addressable slice is the full-service and premium share:** sit-down restaurants, lounges, rooftop bars, beach clubs, and brunch spots. These are concentrated in Lagos (Lekki, VI, Ikoyi), then Abuja (Wuse, Maitama), then Port Harcourt.
- Most outlets are independent. That's good for Reservya: independents need a cheap, ready-made tool, and they aren't locked into an enterprise system.
- **Detty December is the single biggest demand event.** Diaspora visitors paying in dollars and pounds book lounge tables, brunches and dinners. Many are used to OpenTable or Resy abroad and are comfortable paying a deposit online. This is the natural launch window.

*Bottom-up sizing to validate in the pilot (my assumption, not sourced):* if Lagos has roughly 800–1,500 venues that take table bookings, at ₦50k–150k a month each, the B2B subscription pool is about ₦0.5–2.7B a year (~$0.35–1.9M). Deposit and booking commissions would come on top. The B2B pool alone is a modest prize, so the business case relies on transaction revenue and later expansion to Abuja and other cities.

## 4. Competitive landscape

### Direct competitors (diner-side reservations)

| Player | What it is | Status / scale |
|---|---|---|
| **Reisty** | Lagos premium restaurant discovery and booking app | The most visible local brand. Press coverage mentions international expansion plans. No public funding or user numbers found. |
| **Dinesurf** | Pan-African reservation platform, started in Lagos in 2021 | Around 2022: 35 restaurants in Lagos, Abuja and Port Harcourt, 300+ users. Small. |
| **MyNexTable** | "Africa's restaurant discovery and reservation platform" (iOS) | Early. Scale unknown. |
| **TableLynk** | Web listing and booking (Lagos filter) | Very early. Hosted on a free tier. |
| **The real incumbent: WhatsApp, Instagram DMs and phone** | Venues post a WhatsApp number in their bio and take deposits by bank transfer | Universal. Free, familiar, and messy. |

### Adjacent players (could squeeze Reservya or partner with it)

| Player | Relevance |
|---|---|
| **Moniepoint + Orda → "Moniebook for Restaurants"** | Restaurant OS (orders, kitchen, inventory) bundled with Moniepoint terminals. Orda served chains like Eat'N'Go and processed ~5.2M transactions a year. It could add reservations later. **Integrate with it; don't fight it.** |
| **Chowdeck (+ Mira)** | Leading delivery app, now moving into in-store restaurant tech. Owns the consumer food relationship for delivery. |
| **MyFoodTrack, Loystar, Odoo, and others** | Local cloud POS. |
| **AWARI** | Lagos event ticketing and loyalty. Overlaps on nightlife and events. |
| **Global players (OpenTable, SevenRooms, TableCheck)** | Essentially absent from Nigeria's local market. |

**Takeaway:** The main competitor is WhatsApp plus bank transfer, not another app. Reservya has to be clearly easier than that for venues: collect the deposit automatically, cut no-shows, and remember regular guests.

## 5. Customer pain points

**Venues:**
- **No-shows.** Vendor estimates put lost covers at 12–25% in Lagos. The figures are inconsistent and come from software sellers, but every source flags the problem. Deposits are the fix that works.
- **Manual deposits.** Staff check bank-transfer screenshots by hand, and fake "proof of payment" screenshots are a known fraud pattern.
- **No guest data.** Bookings are spread across WhatsApp chats and Instagram DMs, so venues can't see who their VIPs are or bring guests back.
- **Cost pressure.** Food inflation went above 40% at its 2024 peak, so owners will only pay for tools that clearly bring in revenue.

**Guests:**
- Bookings aren't confirmed reliably ("we have no record of your booking").
- They have to DM several venues to find an available table on a Friday night.
- Diaspora visitors want to book and pay before they land, in a familiar way.

## 6. Operating environment

| Factor | Status | Implication |
|---|---|---|
| **Payments** | Paystack (Stripe-owned) and Flutterwave dominate. Fees are about 1.4–1.5% per local transaction. Cards, bank transfer and USSD all work. Paystack also has a virtual terminal. | Build deposits on Paystack first. Support bank transfer with automatic confirmation, because many Nigerians prefer transfer to card. |
| **Smartphones and internet** | 75–85% smartphone ownership or penetration (sources differ). ~157M internet subscriptions (May 2026). Smartphone shipments up 29% in Q3 2025. | The app-first model is fine for the premium audience. Keep a WhatsApp booking channel as a fallback. |
| **Currency** | Naira around ₦1,380–1,450/$ in 2026, more stable than in 2023–24. | Price in naira for venues. Offer USD or card for diaspora guests. Expect FX risk when sending revenue back to Egypt. |
| **Inflation** | Easing. CBN projects ~12.9% for 2026, down from ~21% in 2025. About 15.7% was reported in April 2026. | Owners will be more willing to spend than in 2024, but stay ROI-focused. |
| **Legal and regulatory** | You'll need a local entity registered with the CAC. The NDPA 2023 data-protection law applies to guest data. Collecting payments through Paystack or Flutterwave avoids needing your own payments licence. | Budget for a local entity, a data-protection policy and a local bank account. |
| **Language** | English. | Product and marketing localise easily. The CLAUDE.md "English CTA" rule fits naturally. |

## 7. Positioning and go-to-market

**Positioning:** *"The easiest way for Lagos venues to fill tables, take deposits and bring guests back. Booked in seconds, paid upfront, no more no-shows."*

**Target segments, in order:**
1. **Lounges and rooftop bars** with minimum-spend or bottle-service tables (Lekki, VI). These have the highest booking value and the strongest need for deposits.
2. **Premium sit-down and brunch restaurants** (VI, Ikoyi, Lekki Phase 1). These have high weekend demand.
3. **Beach clubs and event venues** during December.
4. Later: Abuja (Wuse 2, Maitama), then Port Harcourt.

**Product changes needed for Nigeria:**
- Deposits and minimum-spend pre-payment via Paystack, deducted from the bill, with the refund window set by the venue.
- Bank-transfer payments with automatic confirmation, to end fake-screenshot fraud.
- Booking links in WhatsApp and Instagram bios, with confirmations and reminders sent over WhatsApp.
- A diaspora mode: browse and book from abroad, pay in USD or GBP by card.
- An integration roadmap with Moniebook for Restaurants (Moniepoint/Orda) and the common POS systems.

**Pricing hypothesis (test in the pilot):**
- Free tier with a small per-cover or per-deposit fee (for example ₦200–500 per booking, or 2–3% of the deposit).
- Pro tier at about ₦40k–80k a month: guest CRM, campaigns and analytics.
- Avoid USD-priced subscriptions. Venues will resist them.

**Customer acquisition:**
- **Venues:** a local sales lead in Lagos selling face to face. This is the same "be the face of Reservya in your city" model as the Egypt hiring posts. Also partner with Lagos food and nightlife influencers (Zikoko Chopist, Lagos food bloggers, IG nightlife pages).
- **Guests:** "Detty December" campaigns aimed at the US and UK diaspora (IG/TikTok ads geo-targeted to London, Houston, Atlanta, NYC), curated "Where to book this weekend" lists, and launch partnerships with 10–20 well-known venues.
- **Content:** founder-led reels from Lagos venues, which fits the existing reels workflow in this repo.

## 8. Recommended entry plan

| Phase | Timing | Goals | Go/no-go metric |
|---|---|---|---|
| **0. Validation** | 4–6 weeks | Interview 30+ Lagos venue owners and managers, and survey 200+ diners (local and diaspora). Confirm their willingness to pay for deposits. | ≥40% of venues say they'd use paid deposits. ≥10 letters of intent. |
| **1. Pilot** | Dec 2026 – Feb 2027 (Detty December) | 15–25 venues in Lekki/VI. Paystack deposits live. One local sales hire. | ≥1,500 bookings, a no-show rate below 8% on deposit bookings, ≥60% of venues still active after 60 days. |
| **2. Scale Lagos** | 2027 | 150+ venues. Moniebook/POS integration. Paid tier launched. | Positive contribution margin per venue. CAC payback under 6 months. |
| **3. Abuja and beyond** | Late 2027+ | Replicate the playbook. | |

The Detty December 2026 season starts in about 3–4 weeks. That's realistic for a soft launch with a few venues, but not for a full launch. A sensible option is to use December 2026 for validation and on-the-ground interviews, and aim for a full launch in December 2027.

## 9. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Moniepoint/Orda or Chowdeck adds reservations to their bundle | Medium–High | Specialise in nightlife, deposits and guest loyalty. Integrate with them and position Reservya as a partner. |
| Venues won't move off WhatsApp | High | Reservya should work *inside* WhatsApp and Instagram (links, auto-confirmations) instead of trying to replace them. |
| FX and repatriation of revenue | Medium | Keep costs in naira locally. Collect diaspora payments in USD where possible. |
| Seasonality (December spike, then a slowdown) | Medium | Sign venues in December, then keep them with CRM, brunch and weekend campaigns. |
| Operating remotely from Egypt | Medium | Hire a trusted local country lead early, and visit in person during the pilot. |
| Payment fraud and chargebacks | Medium | Use processor-verified payments only, never screenshots. |

## 10. Open questions to answer in validation

1. How many Lagos venues take table bookings today, and how many already ask for deposits?
2. What do they pay now for any software (POS, Instagram ads, influencers)?
3. Reisty's real traction: number of venues, pricing, and what venues dislike about it.
4. Would Moniepoint (Moniebook) or Paystack be open to a partnership or integration?
5. Do diaspora guests actually book before arriving, or only once they're in Lagos?

## Sources

- Reservya company listing: [Wuzzuf](https://wuzzuf.net/ar/jobs/careers/reservya-egypt-145889), [Foundit Gulf](https://www.founditgulf.com/job/salesperson-reservya-egypt-49485958)
- Market size: [Mordor Intelligence via MarketResearch.com](https://www.marketresearch.com/Mordor-Intelligence-LLP-v4018/Nigeria-Foodservice-Share-Trends-Statistics-43552511), [Research and Markets](https://www.researchandmarkets.com/reports/5937121/nigeria-foodservice-market-share-analysis), [Bonafide Research](https://www.bonafideresearch.com/product/6310185845/nigeria-food-service-market), [Nexdigm](https://www.nexdigm.com/market-research/report-store/nigeria-foodservice-market/), [Brandcom](https://brandcom.ng/2026/07/10/nigerias-food-service-industry-hits-11-09-billion-as-digital-payments-drive-growth/)
- Competitors: [Tribune on Reisty](https://tribuneonlineng.com/how-reisty-is-redefining-culinary-experience-in-lagos-set-for-intl-expansion), [Dinesurf](https://startup.network/startups/447800.html), [MyNexTable](https://apps.apple.com/us/app/mynextable/id6760480176), [TableLynk](https://tablelynk.onrender.com/en?city=Lagos), [Zikoko](https://www.zikoko.com/chopist/day-in-the-life-of-an-ijgb-in-lagos-on-a-food-adventure/)
- Moniepoint/Orda: [TechCabal](https://techcabal.com/2026/03/23/moniepoint-acquires-orda-merchant-operating-systems/), [Nairametrics](https://nairametrics.com/2026/03/23/moniepoint-acquires-orda-to-deepen-push-into-africas-food-economy/), [BusinessDay](https://businessday.ng/news/article/moniepoint-buys-orda-to-capture-africas-50bn-restaurant-economy/), [Techpoint](https://techpoint.africa/insight/moniepoint-acquires-orda/), [Launch Base Africa](https://launchbaseafrica.com/2026/03/23/moniepoints-ma-spree-moves-into-restaurant-tech/)
- Delivery/funding context: [Chowdeck seed (Nairametrics)](https://nairametrics.com/2024/04/30/nigerian-food-delivery-startup-chowdeck-secures-2-5-million-seed-funding/), [AWARI (Guardian)](https://guardian.ng/?p=2693109)
- Detty December: [BusinessDay](https://businessday.ng/business-economy/article/us-uk-top-lagos-detty-december-arrivals-as-diaspora-spending-hits-n396bn/), [Nairametrics](https://nairametrics.com/2026/03/19/u-s-becomes-top-diaspora-source-for-lagos-detty-december-2025-report/), [Guardian](https://guardian.ng/saturday-magazine/tourist-influx-drive-billions-of-naira-in-lagos-detty-december/), [Cowrywise](https://cowrywise.com/detty-december-2025)
- Payments and POS: [Paystack offline payments (Daba)](https://dabafinance.com/fr/nouvelles/stripeowned-paystack-launches-new-product-for-offline-payments), [Paystack terminal (Techloy)](https://techloy.com/paystack-launches-pos-terminal), [MyFoodTrack (ThisDay)](https://www.thisdaylive.com/2025/12/19/myfoodtrack-introduces-cloud-based-pos-solution-for-nigerian-food-businesses), [Paystack vs Flutterwave fees (index.dev)](https://www.index.dev/skill-vs-skill/payment-processing-paystack-vs-flutterwave-vs-stripe-africa)
- No-shows and deposits (vendor claims): [Kolonell](https://kolonell.com/en/blog/restaurant-reservation-app-no-show-lagos-2026), [Kolonell](https://kolonell.com/en/blog/restaurant-table-reservation-app-lagos-2026)
- Macro: [TechCabal smartphones](https://techcabal.com/2025/11/27/stable-naira-nigeria-smartphone-market-rebound-29-percent/), [Africa.com smartphone ownership](https://africa.com/top-10-news/nigerias-smartphone-ownership-climbs-to-75), [N-Circular 2026 outlook](https://ncircular.org/posts/2026/Jan/19/nigerias-economic-outlook-for-2026-from-stabilization-to-gradual-inclusive-growth)
