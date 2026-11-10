# Reservya pre-seed financial model: V2.1 notes

**File:** `Reservya_Financial_Model_PreSeed_V2.xlsx`. It has the same 29 sheets as before, about 33,600 live formulas and 0 formula errors.
**Rebuild:** run `python3 model_build/build_reservya_model_v2.py`, then recalculate in Excel or LibreOffice.

The scenarios, restaurant targets (200 → 3,000), revenue streams, 4–7% commission range, tier mix, $1.25M pre-money and the A/B/C funding options are all unchanged.

## 1. Investor-readiness assessment (Checks sheet, section 4)

| Dimension | Weight | Score now |
|---|---|---|
| Formula integrity, linkage, reconciliations | 20% | 10 |
| Scenario, sensitivity and stress coverage | 10% | 9 |
| Assumption evidence | 25% | 1.1 (0 of 64 material inputs verified; price lists documented) |
| Historical capital, IP and asset documentation | 15% | 0 |
| Valuation support | 10% | 4 |
| Funding clarity and use of funds | 10% | 9 |
| Disclosure and transparency | 10% | 9 |
| **Overall** | | **5.3 / 10** |

- **Model mechanics alone:** 9.4 / 10.
- **With every evidence item closed:** 9.7 / 10. I tested this by marking all items closed in a copy of the file.
- **Status:** the model is not "fully verified". It cannot reach 9/10 by changing formulas, only by closing the evidence items in section 3.

## 2. Change log

1. **Engines audited** (3 scenarios × 60 months). I found no formula errors that changed results.
   - Refunds are deducted once.
   - Net commission = commissionable GMV × rate − waivers.
   - The restaurant funnel rolls forward exactly.
   - Tax carry-forward and April payment work as intended.
   - There are no circular references.
2. **GMV → commission reconciliation added:** completed GMV → commissionable GMV → gross commission → net commission, with a zero-difference check.
3. **Monetisation verification table added** for every stream: pricing, adoption, revenue recognition (marketing media is booked net, as agent), delivery cost, collection timing and evidence status.
4. **Current-traction actuals added** to Assumptions, kept apart from the forecast. They stay blank until a document supports them.
5. **Assumption Register rebuilt.** Each input now has:
   - source document, evidence date and responsible person
   - actual vs estimate, confidence and last validation
   - impact if wrong, evidence status and materiality

   There is also a priority-impact table: −20% bills cuts 2027 revenue by EGP 3.5M. A 4% commission cuts it by EGP 4.8M.
6. **Asset Register completed.**
   - New rows: back end, source code, website/domains and integrations.
   - Ownership status is linked to Due Diligence.
   - New reconciliation of the EGP 1.65M software spend.
   - New IAS 38 test: historical spend stays expensed.
7. **Opening BS:** documented vs stated amount for every use of the EGP 2.7M, with the evidence gap shown.
8. **Unit Economics:** marketplace CAC (including diner marketing) added beside restaurant CAC. LTV/CAC is labelled projected.
9. **Funding Scenarios:**
   - total round shown separately from the individual ticket
   - what each amount pays for (restaurants, engineer-years, marketing months, headcount)
   - stress test: downside plus 30-day late payments
   - purpose of capital above A, and the next financing need
10. **Valuation:**
    - The automatic "defensible" verdict is removed. The model now says "supportable" only when 5 value drivers are evidenced.
    - Comparables count only if marked verified.
    - Added sensitivity, dilution and exit-timing tests. All returns are labelled illustrative.
11. **Checks sheet** now has four sections:
    - formula integrity (51 checks, all pass, covering H1–H12)
    - business warnings
    - evidence completeness
    - readiness score
12. **Dashboard:** actuals are separated from forecasts. Added milestones funded, valuation assumptions, open diligence items and an evidence indicator.

## 3. Results to know

- **Base case, 2027:** revenue EGP 22.9M and EBITDA EGP 9.3M.
- **Funding:**
  - A ($100K) and B ($150K) cover the plan and the downside. In a downside with late payments they need a bridge of about $145K (A) or $95K (B).
  - C ($250K) covers all of it, with about 10.5 months of 2027 costs at zero revenue.
- **Valuation:** the methods give a range of $1.21M–$3.70M, with a median of $1.30M. The price is **not yet supportable**, because none of the 5 value drivers is evidenced.
- **Warnings:**
  - 2031 EBITDA margin above 40% (47.9%)
  - projected LTV/CAC of 30x

## 4. Unresolved evidence list (Due Diligence sheet: 28 items, 6 critical)

**Critical**
- IP assignments from founders and developers
- Source code held in a company-owned account
- Bank evidence for the EGP 2.7M
- Verified live restaurant count at Dec 2026
- Kashier reports proving bills per restaurant (125/month)
- Commission rates in signed contracts (5.5% tier mix)

**High**
- Company registration and shareholder register
- Domain and app-store accounts in the company's name
- Founder money: equity or loan
- Software spend invoices (EGP 1.65M)
- Activation (90%), churn (1.5%/month) and average bill (EGP 3,000)
- Paid-plan conversion (70%)
- Kashier fee terms
- Team contracts and vesting
- Product demo and uptime

**Medium / Low**
- Trademark
- IAS 38 documentation
- Marketing-package sales
- Sponsorship LOIs
- Consultant agreements
- Payroll 2025–26
- Law 151/2020 data-protection compliance
- Tax and VAT status
- FX path
- Comparable financings
- Gulf partner term sheets

## 5. Open modelling and accounting issues (documented, not overridden)

- Consolidated tax uses the Egyptian 22.5% rate. Gulf taxes and VAT cash timing are not modelled.
- Sponsorship value can be off slightly when a campaign spans a year-end.
- Ramp-month billing applies to subscriptions.
- Gulf prices use an index at a flat EGP 50/USD.
- Card fees are assumed passed through to restaurants. If Kashier charges Reservya instead, that is about 2–3% of GMV.
- Restaurants sign one month before going live (fixed lag).
- The operating plan does not change with the funding size.
