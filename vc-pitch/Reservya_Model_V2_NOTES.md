# Reservya — Pre-seed financial model V2: review notes

File: `Reservya_Financial_Model_PreSeed_V2.xlsx` (29 sheets, ~33,000 live formulas, 0 errors, all integrity checks pass).
Rebuild: `python3 model_build/build_reservya_model_v2.py`, then recalculate in Excel or LibreOffice.

## How to use
Change three cells on **Assumptions** (yellow): operating scenario (Downside / Base / Upside), commission case (4% / 5.5% / 7% / tier mix), funding scenario (A $100K / B $150K / C $250K). Everything else follows.

## Base case (management targets, tier-mix commission ≈5.5%, funding C)
| | 2027 | 2028 | 2029 | 2030 | 2031 |
|---|---|---|---|---|---|
| Live restaurants (year end) | 200 | 600 | 1,200 | 2,000 | 3,000 |
| Revenue (EGP M) | 22.9 | 106.9 | 280.1 | 560.4 | 951.8 |
| EBITDA (EGP M) | 9.3 | 55.2 | 130.0 | 262.5 | 455.9 |
| EBITDA margin | 41% | 52% | 46% | 47% | 48% |
| Net profit (EGP M) | 7.1 | 42.3 | 99.2 | 200.3 | 348.3 |

At 4% commission: 2027 revenue EGP 18.1M, EBITDA EGP 5.0M (27%).
Downside (60% of targets, 90 bills/month, 2.5% monthly churn): 2027 EBITDA negative.

## What changed from V1
- Revenue built from the restaurant funnel (signed → live → transacting) with ramp-up, activation, churn, refunds and waivers. GMV is shown separately and never as revenue.
- Subscriptions now use the real plan mix (free, EGP 2,000, 5,000, 3,000 per branch) rather than a flat EGP 4,000.
- Opex is built from headcount (16 → 241), CAC, onboarding, brand marketing and country launches, instead of a single total.
- Fully linked monthly engines for three scenarios, plus annual P&L, balance sheet and cash flow, opening balance sheet and the EGP 2.7M reconciliation.
- Funding A/B/C, cap table, use of funds, four valuation methods, commission sensitivity, asset register, assumption register, due-diligence list and checks.

## Analyst flags (read before sharing)
1. Base EBITDA margins (41–52%) are above what investors usually see from marketplaces. They come from low Egyptian salaries plus 125 bills a month per restaurant. Expect pushback, and lead with the downside.
2. LTV/CAC above 30x and payback near one month mean the ARPA assumption is untested, not that the business is proven. Prove bills per restaurant with live data first.
3. Valuation: the four methods put pre-money at $1.21M–$3.70M (median $1.30M), so $1.25M is defensible. The comparables table is empty until verified deals are added.
4. Funding: in the base case the plan needs only about $40K to stay above the EGP 1M buffer. The raise mostly buys speed and safety. Downside with 4% commission and $100K needs about $390K more, so C ($250K) is the safe choice.
5. FX is held flat at EGP 50/USD. Update it before sharing.
6. These V2 numbers differ from the current deck and flashcards, which use V1. Sync them before pitching.

## Inputs to confirm (Low confidence)
Bills per restaurant per month · commission rate actually agreed · plan mix · marketing-package adoption · sponsorship values · churn · founder EGP 2.7M split and equity vs loan · opening cash · IP ownership · Gulf partner share.
