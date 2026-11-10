# ── shared setup, styles, helpers, Assumptions, Countries, FX ──
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

OUT = "/home/user/n/vc-pitch/Reservya_Financial_Model_PreSeed_V2.xlsx"
F = "Arial"
def fnt(color=None, bold=False, italic=False, size=10): return Font(name=F, color=color, bold=bold, italic=italic, size=size)
BLUE, BLACK, GREEN = "0000FF", "000000", "008000"
HFILL = PatternFill("solid", fgColor="1A2420"); SFILL = PatternFill("solid", fgColor="EAE3D6")
YFILL = PatternFill("solid", fgColor="FFFF00"); TFILL = PatternFill("solid", fgColor="E1EFE6"); RFILL = PatternFill("solid", fgColor="F6E4D8")
thin = Side(style="thin", color="999999"); TOP = Border(top=thin); DTOP = Border(top=thin, bottom=Side(style="double", color="333333"))
EGP = '#,##0;(#,##0);"-"'; EGP1 = '#,##0.0;(#,##0.0);"-"'; PCT = '0.0%;(0.0%);"-"'; X = '0.0"x";(0.0"x");"-"'
NUM = '#,##0;(#,##0);"-"'; USD = '"$"#,##0;("$"#,##0);"-"'; GEN = "General"; DEC2 = '#,##0.00;(#,##0.00);"-"'
YEARS = [2027, 2028, 2029, 2030, 2031]; YC = ["C", "D", "E", "F", "G"]
CTRY = ["EG", "SA", "AE", "JO", "MA"]; CNAME = {"EG": "Egypt", "SA": "Saudi Arabia", "AE": "UAE", "JO": "Jordan", "MA": "Morocco"}
SC = {"Downside": "C", "Base": "D", "Upside": "E"}

wb = Workbook(); wb.remove(wb.active)

def new_sheet(name, title, subtitle, widths):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    for i, w in enumerate(widths): ws.column_dimensions[L(i + 1)].width = w
    ws["A1"] = title; ws["A1"].font = fnt("1A2420", True, size=14)
    ws["A2"] = subtitle; ws["A2"].font = fnt("5A675F", italic=True, size=9)
    return ws
def hdr(ws, r, cells, start=1):
    for i, v in enumerate(cells):
        c = ws.cell(r, start + i, v); c.font = fnt("FFFFFF", True); c.fill = HFILL
        c.alignment = Alignment(horizontal="left" if i in (0, 1) or i == len(cells) - 1 else "right", wrap_text=True)
def sec(ws, r, text, n=9):
    for c in range(1, n + 1): ws.cell(r, c).fill = SFILL
    ws.cell(r, 1, text).font = fnt(bold=True)
def put(ws, r, c, v, fmt=GEN, color=BLACK, bold=False, fill=None, italic=False):
    cell = ws.cell(r, c, v); cell.number_format = fmt; cell.font = fnt(color, bold, italic)
    if fill: cell.fill = fill
    return cell
def note(ws, r, c, text): ws.cell(r, c, text).font = fnt("5A675F", italic=True, size=9); ws.cell(r, c).alignment = Alignment(wrap_text=False)

def tf(fmt): return "0.00" if fmt == GEN else fmt.split(";")[0].replace('"', '""')
A = {}      # key -> absolute address of scalar input (e.g. Assumptions!$C$7)
AR = {}     # key -> (sheet, row) for by-year rows (C..G) or by-scenario rows (C..E)
REG = []    # assumption register: (key/label, value-desc, source, confidence, status)

# ───────────── ASSUMPTIONS ─────────────
a = new_sheet("Assumptions", "Assumptions & Scenario Controls",
              "Blue = input · Yellow = key assumption · All amounts EGP unless stated · Inputs are management assumptions unless a source is given.",
              (54, 12, 15, 15, 15, 15, 15, 16, 70))
r = 4; sec(a, r, "SCENARIO CONTROLS — change these three cells to switch the whole model")
def scalar(key, label, unit, val, fmt, src, conf="Medium", status="Management assumption — unverified", key_ass=False, regname=None):
    global r
    r += 1
    a.cell(r, 1, label).font = fnt(); a.cell(r, 2, unit).font = fnt("5A675F", size=9)
    put(a, r, 3, val, fmt, BLUE, fill=YFILL if key_ass else None)
    note(a, r, 9, src)
    A[key] = f"Assumptions!$C${r}"
    REG.append((regname or label, f"=Assumptions!C{r}", fmt, src, conf, status))
scalar("scen", "Operating scenario (1 = Downside, 2 = Base / management plan, 3 = Upside)", "1–3", 2, GEN, "Drives all statements, dashboard and summary.", "—", "Control", True)
scalar("commsel", "Commission scenario (1 = 4%, 2 = 5.5% reference, 3 = 7%, 4 = tier-weighted mix)", "1–4", 4, GEN, "Tier mix is the default base; with the default mix it equals 5.5%.", "—", "Control", True)
scalar("fundsel", "Funding scenario (1 = A $100K, 2 = B $150K, 3 = C $250K)", "1–3", 3, GEN, "Selected raise flows into the cash flow and balance sheet.", "—", "Control", True)
dv = DataValidation(type="whole", operator="between", formula1="1", formula2="3"); a.add_data_validation(dv); dv.add(A["scen"].split("!")[1].replace("$", ""))
dv2 = DataValidation(type="whole", operator="between", formula1="1", formula2="4"); a.add_data_validation(dv2); dv2.add(A["commsel"].split("!")[1].replace("$", ""))
dv3 = DataValidation(type="whole", operator="between", formula1="1", formula2="3"); a.add_data_validation(dv3); dv3.add(A["fundsel"].split("!")[1].replace("$", ""))
r += 1; A["scen_name"] = f"Assumptions!$C${r+1}"
r += 1; a.cell(r, 1, "Selected operating scenario"); put(a, r, 3, f'=CHOOSE({A["scen"]},"Downside","Base","Upside")', GEN, bold=True)
r += 1; A["comm_name"] = f"Assumptions!$C${r}"; a.cell(r, 1, "Selected commission case")
put(a, r, 3, f'=CHOOSE({A["commsel"]},"Conservative 4%","Reference 5.5%","Upper 7%","Tier-weighted mix")', GEN, bold=True)

def byscen(key, label, unit, vals, fmt, src, conf="Low", status="Management assumption — unverified"):
    global r
    r += 1
    a.cell(r, 1, label).font = fnt(); a.cell(r, 2, unit).font = fnt("5A675F", size=9)
    for i, v in enumerate(vals): put(a, r, 3 + i, v, fmt, BLUE, fill=YFILL if i == 1 else None)
    note(a, r, 9, src); AR[key] = r
    REG.append((label + " (Down / Base / Up)", f'=TEXT(Assumptions!C{r},"{tf(fmt)}")&" / "&TEXT(Assumptions!D{r},"{tf(fmt)}")&" / "&TEXT(Assumptions!E{r},"{tf(fmt)}")', GEN, src, conf, status))
r += 2; hdr(a, r, ["Operating scenario drivers", "Unit", "Downside", "Base", "Upside", "", "", "", "Source / rationale"])
byscen("ach", "Restaurant targets achieved", "% of plan", [0.60, 1.00, 1.15], PCT, "Base = management targets (200/600/1,200/2,000/3,000). Downside/upside are sensitivities, not forecasts.", "Low")
byscen("bills", "Completed online bills per fully-ramped transacting restaurant", "per month", [90, 125, 150], NUM, "Management input: 125 bills/month (≈4 a day). Unverified by live data.", "Low")
byscen("activ", "Live restaurants that actively transact", "%", [0.80, 0.90, 0.95], PCT, "Share of live venues using online booking/pre-order/payment in a month.", "Low")
byscen("churn", "Monthly restaurant churn", "% / month", [0.025, 0.015, 0.010], PCT, "No retention history yet. 1.5%/month ≈ 17% a year.", "Low")
byscen("billx", "Average-bill multiplier", "x", [0.90, 1.00, 1.05], DEC2, "Applied to country average bills.", "Medium")
byscen("mktx", "Marketing-package adoption multiplier", "x", [0.50, 1.00, 1.50], DEC2, "Applied to adoption rates below.", "Low")
byscen("sponx", "Brand-sponsorship volume multiplier", "x", [0.50, 1.00, 1.50], DEC2, "Applied to projected campaigns.", "Low")
byscen("exitx", "Illustrative 2031 exit value", "x revenue", [1.0, 3.0, 5.0], X, "Illustrative only; not a valuation of the company.", "Low")
byscen("prob", "Probability weight (risk-adjusted valuation)", "%", [0.30, 0.50, 0.20], PCT, "Judgement for the First Chicago method; must total 100%.", "Low")

def byyear(key, label, unit, vals, fmt, src, conf="Low", status="Management assumption — unverified", key_ass=False):
    global r
    r += 1
    a.cell(r, 1, label).font = fnt(); a.cell(r, 2, unit).font = fnt("5A675F", size=9)
    for i, v in enumerate(vals):
        put(a, r, 3 + i, v, fmt, BLUE if not (isinstance(v, str) and v.startswith("=")) else BLACK, fill=YFILL if key_ass else None)
    note(a, r, 9, src); AR[key] = r
    REG.append((label, f'=TEXT(Assumptions!C{r},"{tf(fmt)}")&" → "&TEXT(Assumptions!G{r},"{tf(fmt)}")', GEN, src, conf, status))
r += 2; sec(a, r, "COMMISSION — revenue = eligible completed GMV × realised weighted-average commission")
scalar("c_cons", "Conservative commission rate", "%", 0.04, PCT, "Bottom of the stated 4–7% commercial range.", "High", "Company pricing")
scalar("c_ref", "Reference commission rate (midpoint)", "%", 0.055, PCT, "Midpoint of 4–7% — a modelling reference, not a realised rate.", "Medium", "Derived")
scalar("c_up", "Upper commission rate", "%", 0.07, PCT, "Top of the stated range.", "High", "Company pricing")
r += 1; a.cell(r + 1, 1, "Commission by restaurant tier").font = fnt(bold=True); r += 1
hdr(a, r + 1, ["Tier", "", "Share of GMV", "Rate", "", "", "", "", "Rationale"]); r += 1
TIERS = [("Premium / high-volume venues", 0.30, 0.04), ("Mid-size restaurants", 0.40, 0.055), ("Small / independent venues", 0.30, 0.07)]
t0 = r + 1
for name, sh, rt in TIERS:
    r += 1; a.cell(r, 1, name); put(a, r, 3, sh, PCT, BLUE); put(a, r, 4, rt, PCT, BLUE)
    note(a, r, 9, "Higher-volume venues negotiate lower rates (Feature Guide: 2–4% big names, 4–7% small & mid).")
t1 = r
r += 1; a.cell(r, 1, "Tier-weighted average commission").font = fnt(bold=True)
put(a, r, 3, f"=SUM(C{t0}:C{t1})", PCT); put(a, r, 4, f"=SUMPRODUCT(C{t0}:C{t1},D{t0}:D{t1})", PCT, bold=True)
note(a, r, 9, "Share column must total 100% (see Checks).")
A["tier_share_sum"] = f"Assumptions!$C${r}"; A["c_tier"] = f"Assumptions!$D${r}"
r += 1; A["c_eff"] = f"Assumptions!$D${r}"; a.cell(r, 1, "Commission rate used in the model").font = fnt(bold=True)
put(a, r, 4, f'=CHOOSE({A["commsel"]},{A["c_cons"]},{A["c_ref"]},{A["c_up"]},{A["c_tier"]})', PCT, bold=True, fill=TFILL)
scalar("refund", "Refunds & cancellations (share of completed GMV)", "%", 0.05, PCT, "No commission on refunded or cancelled bills. Assumption pending live data.", "Low")
r += 1; hdr(a, r, ["", "Unit"] + [str(y) for y in YEARS] + ["", "Source / rationale"])
byyear("waive", "Commission waived (launch incentives, free trials)", "% of commission", [0.10, 0.05, 0.05, 0.05, 0.05], PCT, "Launch promotions in year one, then steady-state incentives.")
scalar("r1", "Ramp: share of full volume in a restaurant's first live month", "%", 0.40, PCT, "Activation ramp.", "Low")
scalar("r2", "Ramp: share of full volume in second live month", "%", 0.70, PCT, "Full volume from month three.", "Low")
note(a, r + 1, 1, "Onboarding lag: restaurants are signed one month before going live (fixed structure in the engine).")
r += 2; sec(a, r, "SUBSCRIPTIONS — plan mix applied to live restaurants (EGP list prices; other countries via price index)")
r += 1; hdr(a, r, ["", "Unit"] + [str(y) for y in YEARS] + ["", "Source / rationale"])
byyear("p_free", "Commission-only plan (no monthly fee)", "% of live", [0.30, 0.25, 0.20, 0.20, 0.20], PCT, "Feature Guide Tier 3: commission only, zero upfront.")
byyear("p_single", "Single Feature plan — EGP 2,000 / month", "% of live", [0.30, 0.30, 0.30, 0.28, 0.25], PCT, "Feature Guide Tier 1.")
byyear("p_full", "Full Features plan — EGP 5,000 / month", "% of live", [0.30, 0.35, 0.38, 0.40, 0.42], PCT, "Feature Guide Tier 2. Mix shift = upgrades.")
byyear("p_multi", "Multi-venue plan — EGP 3,000 per branch / month", "% of live", [0.10, 0.10, 0.12, 0.12, 0.13], PCT, "Packages PDF: restaurant groups, 3+ locations.")
r += 1; a.cell(r, 1, "Plan mix total (must be 100%)").font = fnt(italic=True)
for i in range(5): put(a, r, 3 + i, f"=SUM({YC[i]}{AR['p_free']}:{YC[i]}{AR['p_multi']})", PCT)
AR["p_sum"] = r
scalar("pr_single", "Single Feature list price", "EGP / month", 2000, EGP, "Feature Guide pricing.", "High", "Company pricing")
scalar("pr_full", "Full Features list price", "EGP / month", 5000, EGP, "Feature Guide pricing.", "High", "Company pricing")
scalar("pr_multi", "Multi-venue price per branch", "EGP / month", 3000, EGP, "Packages PDF pricing.", "High", "Company pricing")
scalar("pr_inc", "Annual list-price increase (from 2028)", "% / year", 0.10, PCT, "Inflation pass-through in EGP.", "Medium")
scalar("collect", "Collection rate on billed subscriptions & packages", "%", 0.97, PCT, "Uncollected share is written off as bad debt.", "Medium")
scalar("payfee", "Payment fees on Reservya's own collections", "% of collected", 0.025, PCT, "Fees on guests' bills are passed through to restaurants (Feature Guide).", "Medium")

r += 2; sec(a, r, "RESTAURANT MARKETING & IN-APP ADVERTISING")
r += 1; hdr(a, r, ["", "Unit"] + [str(y) for y in YEARS] + ["", "Source / rationale"])
byyear("m_b", "Bronze package adoption — EGP 5,000 / month", "% of live", [0.08, 0.09, 0.10, 0.11, 0.12], PCT, "Packages PDF price. Adoption is an assumption.")
byyear("m_s", "Silver package adoption — EGP 15,000 / month", "% of live", [0.03, 0.035, 0.04, 0.045, 0.05], PCT, "Packages PDF price.")
byyear("m_g", "Gold package adoption — EGP 25,000 / month", "% of live", [0.01, 0.012, 0.014, 0.016, 0.018], PCT, "Packages PDF price.")
byyear("m_one", "One-time campaigns bought per year", "% of live", [0.15, 0.18, 0.20, 0.22, 0.25], PCT, "Seasonal / event promotions, featured placements.")
scalar("pr_b", "Bronze package price", "EGP / month", 5000, EGP, "Packages PDF.", "High", "Company pricing")
scalar("pr_s", "Silver package price", "EGP / month", 15000, EGP, "Packages PDF.", "High", "Company pricing")
scalar("pr_g", "Gold package price", "EGP / month", 25000, EGP, "Packages PDF.", "High", "Company pricing")
scalar("pr_one", "Average one-time campaign price", "EGP", 7500, EGP, "Assumption.", "Low")
scalar("m_cost", "Delivery cost of marketing revenue (creative, account management)", "% of revenue", 0.30, PCT, "Media bought for restaurants (e.g. Instagram collab ads funded from their transactions) is passed through — Reservya acts as agent, so it is excluded from revenue and cost (net presentation, IFRS 15 principal/agent).", "Medium")

r += 2; sec(a, r, "BRAND SPONSORSHIPS & STRATEGIC PARTNERSHIPS")
r += 1; hdr(a, r, ["", "Unit"] + [str(y) for y in YEARS] + ["", "Source / rationale"])
byyear("s_signed", "Signed sponsorship contracts (verified)", "# campaigns", [0, 0, 0, 0, 0], NUM, "None signed today. Enter only executed contracts.", "High", "Verified: none")
byyear("s_pipe", "Pipeline opportunities (not in revenue)", "# campaigns", [0, 0, 0, 0, 0], NUM, "Tracked separately; excluded from revenue until signed.", "—", "Memo")
byyear("s_new", "Projected new campaigns sold", "# / year", [2, 6, 12, 20, 30], NUM, "Banks, payment providers, telecoms, beverage and lifestyle brands.")
byyear("s_acv", "Average contract value", "EGP", [250000, 333000, 417000, 500000, 600000], EGP, "Assumption; no signed reference contract yet.")
scalar("s_dur", "Campaign duration (revenue recognised evenly)", "months", 3, NUM, "Revenue over the service-delivery period, not at signing (IFRS 15).", "Medium")
scalar("s_ren", "Renewal probability at campaign end", "%", 0.30, PCT, "Assumption.", "Low")
scalar("s_cost", "Sponsorship delivery cost", "% of revenue", 0.20, PCT, "Content, placements, activation.", "Medium")

r += 2; sec(a, r, "OPERATING COSTS")
r += 1; hdr(a, r, ["", "Unit"] + [str(y) for y in YEARS] + ["", "Source / rationale"])
byyear("host_fix", "Hosting & infrastructure — fixed", "EGP / month", [40000, 80000, 150000, 250000, 350000], EGP, "Cloud, monitoring, security. Assumption.")
byyear("brand", "Brand & consumer marketing (non-acquisition)", "% of revenue", [0.08, 0.18, 0.20, 0.20, 0.18], PCT, "Diner-side demand generation (app installs, social, influencers, events). Scales with revenue. Excluded from restaurant CAC.")
byyear("ga", "General & administration (office, software, travel)", "EGP / month", [120000, 500000, 1600000, 3200000, 5500000], EGP, "Office, software, travel, insurance, country offices from 2029. Assumption.")
byyear("legal", "Legal, audit & compliance", "EGP / year", [300000, 500000, 900000, 1200000, 1500000], EGP, "Includes data-protection compliance (Egypt Law 151/2020).")
scalar("host_var", "Hosting cost per live restaurant", "EGP / month", 150, EGP, "Assumption.", "Medium")
scalar("msg", "Messaging cost per completed bill (WhatsApp / SMS)", "EGP", 1.5, DEC2, "Twilio / WhatsApp Business notifications. Assumption.", "Medium")
scalar("cons_share", "Share of Egypt restaurants signed by hospitality consultants", "%", 0.40, PCT, "Operating-partner model (pitch deck).", "Medium")
scalar("cons_fee", "Consultant fee per restaurant signed", "EGP", 10000, EGP, "≈10% commission model; one-off per signing. Assumption.", "Low")
scalar("perf", "Restaurant-acquisition marketing per new restaurant", "EGP", 8000, EGP, "B2B campaigns, events, collateral.", "Low")
scalar("capdev", "Share of engineering & product salaries capitalised (IAS 38)", "%", 0.20, PCT, "Only for new features meeting IAS 38 criteria with timesheets. Set 0% if not documented.", "Low", "Requires accounting sign-off")
scalar("laptop", "Equipment per new hire", "EGP", 45000, EGP, "Laptop & devices.", "Medium")
scalar("dev_capex", "Devices given to each new restaurant (capex)", "EGP", 0, EGP, "Set >0 if tablets are supplied and owned by Reservya.", "Medium")
scalar("life_eq", "Equipment useful life", "months", 36, NUM, "Straight line.", "High", "Policy")
scalar("life_sw", "Capitalised software useful life", "months", 36, NUM, "Straight line from month after capitalisation.", "High", "Policy")
scalar("int_rate", "Interest income on cash", "% / year", 0.0, PCT, "Conservatively excluded.", "High", "Policy")

r += 2; sec(a, r, "HEADCOUNT — year-end heads per function and monthly loaded cost (EGP, 2027 level)")
r += 1; hdr(a, r, ["Function", "Opening (Dec 2026)"] + [str(y) for y in YEARS] + ["Monthly cost 2027", "Notes"])
FUNCS = [("eng", "Engineering", 4, [5, 12, 22, 32, 42], 45000), ("prod", "Product & design", 1, [1, 3, 6, 9, 12], 40000),
         ("sales", "Sales & business development", 2, [3, 10, 22, 36, 50], 25000), ("supp", "Onboarding & customer support", 2, [3, 12, 30, 55, 85], 15000),
         ("mkt", "Marketing & creative", 1, [2, 5, 10, 16, 22], 25000), ("adm", "Management & administration", 2, [2, 6, 12, 20, 30], 40000)]
HC = {}
for k, name, op, yrs, sal in FUNCS:
    r += 1; a.cell(r, 1, name); put(a, r, 2, op, NUM, BLUE)
    for i, v in enumerate(yrs): put(a, r, 3 + i, v, NUM, BLUE)
    put(a, r, 8, sal, EGP, BLUE); HC[k] = r
note(a, r, 9, "Opening team of 12 (company figure). Hiring plan and salaries are assumptions.")
r += 1; a.cell(r, 1, "Total headcount").font = fnt(bold=True)
for cidx in range(2, 8): put(a, r, cidx, f"=SUM({L(cidx)}{HC['eng']}:{L(cidx)}{HC['adm']})", NUM, bold=True)
AR["hc_tot"] = r
scalar("raise", "Annual salary increase", "% / year", 0.10, PCT, "EGP inflation.", "Medium")

r += 2; sec(a, r, "TAX, WORKING CAPITAL, CASH")
scalar("tax", "Corporate income tax rate (applied to consolidated profit)", "%", 0.225, PCT, "Egypt standard rate (PwC Tax Summaries). Conservative: Gulf rates are lower.", "High", "Public source")
scalar("taxmonth", "Month annual tax is paid (following year)", "month #", 4, NUM, "Egypt returns and payment due by 30 April.", "High", "Public source")
scalar("taxloss", "Tax losses carried forward at 31 Dec 2026", "EGP", 0, EGP, "Only if pre-2027 costs were booked in the company and are deductible. To confirm with tax adviser.", "Low", "To confirm")
scalar("d_comm", "Collection days — commission (settled by payment provider)", "days", 7, NUM, "Kashier settlement. Assumption.", "Medium")
scalar("d_sub", "Collection days — subscriptions & packages", "days", 15, NUM, "Assumption.", "Medium")
scalar("d_spon", "Collection days — sponsorships", "days", 60, NUM, "Corporate payment terms.", "Medium")
scalar("d_ap", "Supplier payment days", "days", 30, NUM, "Assumption.", "Medium")
scalar("minbuf", "Minimum cash buffer (shortfall flag below this)", "EGP", 1000000, EGP, "Risk policy.", "—", "Policy")

r += 2; sec(a, r, "FUNDING")
scalar("premoney", "Pre-money valuation — negotiation target", "USD", 1250000, USD, "Management target from the company's valuation calculator (range $875K–$2.0M). Not an independent fair value.", "Low", "Management target", True)
r += 1; hdr(a, r, ["Funding scenario", "", "A", "B", "C", "", "", "", "Notes"])
r += 1; a.cell(r, 1, "Total raise"); a.cell(r, 2, "USD").font = fnt("5A675F", size=9)
for i, v in enumerate([100000, 150000, 250000]): put(a, r, 3 + i, v, USD, BLUE, fill=YFILL)
note(a, r, 9, "Target investors write $100K–$150K tickets; C would need two investors."); AR["raise"] = r
r += 1; a.cell(r, 1, "Number of investors"); a.cell(r, 2, "#").font = fnt("5A675F", size=9)
for i, v in enumerate([1, 1, 2]): put(a, r, 3 + i, v, NUM, BLUE)
AR["n_inv"] = r
r += 1; A["raise_sel"] = f"Assumptions!$C${r}"; a.cell(r, 1, "Selected raise").font = fnt(bold=True)
put(a, r, 3, f"=INDEX(C{AR['raise']}:E{AR['raise']},{A['fundsel']})", USD, bold=True, fill=TFILL)
scalar("pool", "Employee option pool (% of post-money, created before the round)", "%", 0.10, PCT, "Typical pre-seed practice; dilutes founders, not new investors.", "Medium", "Market practice")
scalar("safe_disc", "SAFE discount to next round price (if SAFE used)", "%", 0.20, PCT, "Standard post-money SAFE terms (Y Combinator).", "Medium", "Market practice")
r += 1; hdr(a, r, ["Future rounds (illustrative, not in cash flow)", "Year", "Amount (USD)", "Pre-money (USD)", "", "", "", "", "Notes"])
r += 1; a.cell(r, 1, "Seed round"); put(a, r, 2, 2028, GEN, BLUE); put(a, r, 3, 1500000, USD, BLUE); put(a, r, 4, 8000000, USD, BLUE); AR["seed"] = r
note(a, r, 9, "Illustrative assumption used only for dilution and returns.")
r += 1; a.cell(r, 1, "Series A"); put(a, r, 2, 2030, GEN, BLUE); put(a, r, 3, 6000000, USD, BLUE); put(a, r, 4, 30000000, USD, BLUE); AR["seriesA"] = r
note(a, r, 9, "Illustrative assumption used only for dilution and returns.")
r += 1; hdr(a, r, ["", "Unit"] + [str(y) for y in YEARS] + ["", "Notes"])
byyear("addfin", "Additional financing included in cash flow (received in January)", "EGP", [0, 0, 0, 0, 0], EGP, "Leave at 0 unless a further round is committed.", "—", "Policy")
scalar("stress_days", "Stress test: extra collection delay on all revenue", "days", 30, NUM, "Used only in the downside liquidity stress (Funding Scenarios, Checks). Does not change the plan.", "—", "Policy")

r += 2; sec(a, r, "CURRENT TRACTION — ACTUALS (company-reported; enter only figures you can document)")
r += 1; hdr(a, r, ["Metric", "Unit", "Value", "", "", "", "", "As of", "Evidence required"])
TRX = {}
for k, lab, unit, val, fmt_, asof, ev in [
    ("tested", "Venues tested in real service", "#", 22, NUM, "Oct-2026", "List of venues, dates, test reports"),
    ("launch", "Public launch date (iOS, Android, web)", "date", "15-May-2026", GEN, "May-2026", "App-store listing history"),
    ("invested", "Founder investment to date", "EGP", "='Opening BS'!B5", EGP, "Oct-2026", "Bank statements, invoices"),
    ("live", "Live restaurants (verified count)", "#", None, NUM, "", "Signed agreements + dashboard export — leave blank until documented"),
    ("paying", "Restaurants paying a subscription", "#", None, NUM, "", "Invoices / payment records"),
    ("bills", "Completed online bills — latest full month", "#", None, NUM, "", "Kashier settlement report"),
    ("gmv", "Completed GMV — latest full month", "EGP", None, EGP, "", "Kashier settlement report"),
    ("rate", "Average commission actually charged", "%", None, PCT, "", "Signed restaurant contracts")]:
    r += 1; a.cell(r, 1, lab); a.cell(r, 2, unit).font = fnt("5A675F", size=9)
    put(a, r, 3, val, fmt_, GREEN if isinstance(val, str) and val.startswith("=") else BLUE)
    a.cell(r, 8, asof); note(a, r, 9, ev); TRX[k] = f"Assumptions!$C${r}"
note(a, r + 1, 1, "Actuals are separate from the forecast. Blank = not yet documented; the model then shows 'evidence pending', never a made-up figure.")

# ───────────── FX ─────────────
fx = new_sheet("FX", "Exchange-Rate Schedule", "Editable. EGP per USD by year; other currencies per USD (pegs and assumptions).", (40, 12, 14, 14, 14, 14, 14, 60))
hdr(fx, 4, ["", "Unit"] + [str(y) for y in YEARS] + ["Source / status"])
fx.cell(5, 1, "EGP per USD"); fx.cell(5, 2, "EGP")
for i, v in enumerate([50, 50, 50, 50, 50]): put(fx, 5, 3 + i, v, DEC2, BLUE, fill=YFILL)
note(fx, 5, 8, "Flat at 50 for comparability with the deck. Update to the current rate and a depreciation path before sharing.")
A["fx_row"] = 5
FXL = {"SA": ("SAR", 3.75, "Fixed peg."), "AE": ("AED", 3.6725, "Fixed peg."), "JO": ("JOD", 0.709, "Fixed peg."), "MA": ("MAD", 10.0, "Floating; approximate — verify.")}
fx.cell(7, 1, "Other currencies per USD").font = fnt(bold=True)
FXR = {}
rr = 8
for k, (cur, v, s) in FXL.items():
    fx.cell(rr, 1, f"{cur} per USD ({CNAME[k]})"); fx.cell(rr, 2, cur)
    put(fx, rr, 3, v, '#,##0.0000', BLUE); note(fx, rr, 8, s); FXR[k] = rr; rr += 1
fx.cell(rr + 1, 1, "Convert local amounts to EGP: local ÷ (local per USD) × EGP per USD for the year.").font = fnt("5A675F", italic=True, size=9)

# ───────────── COUNTRIES ─────────────
co = new_sheet("Countries", "Country Assumptions", "Egypt is the launch market; the regional plan is a management scenario. Economics are not assumed uniform.", (48, 12, 15, 15, 15, 15, 15, 70))
hdr(co, 4, ["Parameter", "Unit"] + [CNAME[c] for c in CTRY] + ["Source / confidence"])
CP = {}
params = [
 ("cur", "Currency", "", ["EGP", "SAR", "AED", "JOD", "MAD"], GEN, "—"),
 ("launch", "Launch year", "year", [2027, 2029, 2029, 2030, 2031], GEN, "Management plan (pitch deck)."),
 ("open", "Live restaurants at 31 Dec 2026", "#", [0, 0, 0, 0, 0], NUM, "Enter the actual number of live paying partners (not verified — left at 0)."),
 ("bill", "Average completed bill, 2027 level (local currency)", "local", [3000, 280, 300, 35, 450], NUM, "Egypt: ≈3 guests × EGP 1,000 (management). Others: assumptions — low confidence, verify with pilots."),
 ("billg", "Average-bill growth", "% / year", [0.07, 0.03, 0.03, 0.03, 0.03], PCT, "Local price inflation. Assumption."),
 ("pidx", "Subscription & package price index (EGP-equivalent, Egypt = 1)", "x", [1.0, 2.0, 2.0, 1.2, 1.0], DEC2, "Gulf priced higher in EGP terms. Assumption."),
 ("partner", "Operating-partner revenue share", "% of revenue", [0, 0.18, 0.18, 0.15, 0.15], PCT, "Pitch deck: 15–20% operating partners; 18% master partners."),
 ("launchc", "One-time country launch cost", "EGP", [0, 3000000, 3000000, 1500000, 1500000], EGP, "Legal set-up, launch events, partner onboarding. Assumption."),
 ("onb", "Onboarding cost per new restaurant", "EGP", [3000, 6000, 6000, 4000, 4000], EGP, "Training, set-up, materials. Assumption."),
 ("consult", "Hospitality consultants used (1 = yes)", "flag", [1, 0, 0, 0, 0], GEN, "Egypt direct model; partners sell abroad."),
 ("cit", "Statutory corporate tax rate (information)", "%", [0.225, 0.20, 0.09, 0.20, 0.20], PCT, "Information only — verify (UAE 9% above AED 375K; KSA 20% for foreign-owned; Morocco progressive). Model applies Egypt rate to all profit (conservative)."),
 ("vat", "VAT rate (information)", "%", [0.14, 0.15, 0.05, 0.16, 0.20], PCT, "Revenue is modelled excluding VAT; VAT is a pass-through."),
]
rr = 5
for k, name, unit, vals, fmt, s in params:
    co.cell(rr, 1, name); co.cell(rr, 2, unit).font = fnt("5A675F", size=9)
    for i, v in enumerate(vals): put(co, rr, 3 + i, v, fmt, BLUE)
    note(co, rr, 8, s); CP[k] = rr; rr += 1
rr += 1; co.cell(rr, 1, "Year-end live restaurants by country (base plan)").font = fnt(bold=True); rr += 1
hdr(co, rr, ["Country", ""] + [str(y) for y in YEARS] + ["Notes"])
CT = {}
targets = {"EG": [200, 600, 950, 1300, 1650], "SA": [0, 0, 150, 300, 500], "AE": [0, 0, 100, 250, 400], "JO": [0, 0, 0, 150, 250], "MA": [0, 0, 0, 0, 200]}
for c in CTRY:
    rr += 1; co.cell(rr, 1, CNAME[c])
    for i, v in enumerate(targets[c]): put(co, rr, 3 + i, v, NUM, BLUE)
    CT[c] = rr
rr += 1; co.cell(rr, 1, "Total (must equal management target)").font = fnt(bold=True)
for i in range(5): put(co, rr, 3 + i, f"=SUM({YC[i]}{CT['EG']}:{YC[i]}{CT['MA']})", NUM, bold=True)
CT["tot"] = rr
rr += 1; co.cell(rr, 1, "Management target — total restaurants").font = fnt(bold=True)
for i, v in enumerate([200, 600, 1200, 2000, 3000]): put(co, rr, 3 + i, v, NUM, BLUE, fill=YFILL)
note(co, rr, 8, "Management targets — preserved unchanged.")
CT["mgmt"] = rr
# ───────────── OPENING BALANCE SHEET & FOUNDER RECONCILIATION ─────────────
ob = new_sheet("Opening BS", "Founder Investment Reconciliation & Opening Balance Sheet (31 Dec 2026)",
               "Reconciles the EGP 2.7M founder investment to its uses. Figures are management estimates until matched to bank statements and the company ledger.",
               (52, 16, 16, 18, 16, 70, 18, 18))
r = 4; sec(ob, r, "A. Sources — founder funding", 6)
r += 1; ob.cell(r, 1, "Total founder contributions to date"); put(ob, r, 2, 2700000, EGP, BLUE, fill=YFILL)
note(ob, r, 6, "Company figure (financial sheet 'Investment to date'). To reconcile to bank statements."); OB = {"contrib": r}
r += 1; ob.cell(r, 1, "Share recorded as equity (rest = shareholder loan)"); put(ob, r, 2, 1.0, PCT, BLUE, fill=YFILL)
note(ob, r, 6, "Assumed 100% equity. If any amount was lent by founders, enter the loan share — it becomes a liability."); OB["eqshare"] = r
r += 2; sec(ob, r, "B. Uses — how the money was spent (company 'Investment to date' table)", 6)
r += 1; hdr(ob, r, ["Category", "Amount (EGP)", "Capitalised (EGP)", "Expensed (EGP)", "Treatment", "Basis / documents needed", "Documented (EGP)", "Evidence gap (EGP)"])
USES = [("Software development (2 years)", 1650000, "Midpoint of EGP 1.5–1.8M in the company sheet. Expensed: IAS 38 forbids retroactive capitalisation without contemporaneous evidence that development criteria were met."),
        ("Operations & infrastructure", 600000, "Servers, security, compliance, integrations (Orascom, Kashier, Stripe)."),
        ("Team & salaries", 300000, "Core product, operations, support."),
        ("Testing & market validation", 75000, "Midpoint of EGP 50–100K; 5 venues + El Gouna beta."),
        ("Other / unclassified — needs documentation", 75000, "Difference between the stated EGP 2.7M total and the itemised ranges. Must be traced to invoices.")]
u0 = r + 1
for name, amt, basis in USES:
    r += 1; ob.cell(r, 1, name); put(ob, r, 2, amt, EGP, BLUE); put(ob, r, 3, 0, EGP, BLUE)
    put(ob, r, 4, f"=B{r}-C{r}", EGP); put(ob, r, 5, f'=IF(C{r}>0,"Partly capitalised","Expensed")', GEN); note(ob, r, 6, basis)
    put(ob, r, 7, 0, EGP, BLUE); put(ob, r, 8, f"=B{r}-G{r}", EGP)
u1 = r
r += 1; ob.cell(r, 1, "Equipment purchased (computers, devices)"); put(ob, r, 2, 0, EGP, BLUE); put(ob, r, 3, f"=B{r}", EGP); put(ob, r, 4, 0, EGP)
put(ob, r, 5, "Capitalised", GEN); note(ob, r, 6, "Enter cost of owned equipment with invoices. Not itemised in company records yet."); OB["equip"] = r
put(ob, r, 7, 0, EGP, BLUE); put(ob, r, 8, f"=B{r}-G{r}", EGP)
r += 1; ob.cell(r, 1, "Cash remaining at 31 Dec 2026"); put(ob, r, 2, 0, EGP, BLUE, fill=YFILL); put(ob, r, 3, "", GEN); put(ob, r, 4, "", GEN)
note(ob, r, 6, "Enter the actual bank balance."); OB["cash"] = r
put(ob, r, 7, 0, EGP, BLUE); put(ob, r, 8, f"=B{r}-G{r}", EGP)
r += 1; ob.cell(r, 1, "Total uses").font = fnt(bold=True)
put(ob, r, 2, f"=SUM(B{u0}:B{OB['cash']})", EGP, bold=True); put(ob, r, 3, f"=SUM(C{u0}:C{OB['equip']})", EGP, bold=True); put(ob, r, 4, f"=SUM(D{u0}:D{u1})", EGP, bold=True)
put(ob, r, 7, f"=SUM(G{u0}:G{OB['cash']})", EGP, bold=True); put(ob, r, 8, f"=SUM(H{u0}:H{OB['cash']})", EGP, bold=True)
OB["uses"] = r; OB["u0"] = u0; OB["u1"] = u1
note(ob, r + 1, 7, "Documented = matched to bank statements, invoices or payroll. Gap must reach 0 before closing.")
r += 1; ob.cell(r, 1, "Unreconciled difference (sources − uses, must be 0)").font = fnt(bold=True)
put(ob, r, 2, f"=B{OB['contrib']}-B{OB['uses']}", EGP, bold=True, fill=TFILL); OB["var"] = r
r += 2; sec(ob, r, "C. Opening balance sheet at 31 Dec 2026 (EGP)", 6)
def obl(key, label, f, bold=False, border=None, n=None):
    global r
    r += 1; ob.cell(r, 1, label).font = fnt(bold=bold); c = put(ob, r, 2, f, EGP, bold=bold)
    if border: c.border = border
    if n: note(ob, r, 6, n)
    OB[key] = r
obl("b_cash", "Cash", f"=B{OB['cash']}")
obl("b_ar", "Accounts receivable", 0, n="Enter if any invoices are outstanding.")
ob.cell(r, 2).font = fnt(BLUE)
obl("b_eqc", "Equipment at cost", f"=C{OB['equip']}")
obl("b_eqd", "Less: accumulated depreciation", 0, n="Enter actual accumulated depreciation.")
ob.cell(r, 2).font = fnt(BLUE)
obl("b_swc", "Capitalised software at cost", f"=SUM(C{u0}:C{u1})", n="0 unless supported by IAS 38 documentation.")
obl("b_swa", "Less: accumulated amortisation", 0); ob.cell(r, 2).font = fnt(BLUE)
obl("b_ta", "Total assets", f"=B{OB['b_cash']}+B{OB['b_ar']}+B{OB['b_eqc']}-B{OB['b_eqd']}+B{OB['b_swc']}-B{OB['b_swa']}", True, TOP)
obl("b_ap", "Accounts payable", 0, n="Enter unpaid supplier invoices."); ob.cell(r, 2).font = fnt(BLUE)
obl("b_sl", "Shareholder loans", f"=B{OB['contrib']}*(1-B{OB['eqshare']})")
obl("b_tl", "Total liabilities", f"=B{OB['b_ap']}+B{OB['b_sl']}", True, TOP)
obl("b_pic", "Paid-in capital", f"=B{OB['contrib']}*B{OB['eqshare']}")
obl("b_re", "Accumulated deficit (expensed build costs)", f"=-D{OB['uses']}-B{OB['b_eqd']}-B{OB['b_swa']}-B{OB['b_ap']}+B{OB['b_ar']}",
    n="Equals −(expensed costs) − depreciation − amortisation ± working capital. Derived from section B, not a plug.")
obl("b_te", "Total equity", f"=B{OB['b_pic']}+B{OB['b_re']}", True, TOP)
obl("b_tle", "Total liabilities & equity", f"=B{OB['b_tl']}+B{OB['b_te']}", True, DTOP)
obl("b_chk", "Balance check (must be 0)", f"=ROUND(B{OB['b_ta']}-B{OB['b_tle']},0)", True)
ob.cell(OB["b_chk"], 2).fill = TFILL
r += 1; ob.cell(r, 1, "Remaining useful life of opening equipment (months)"); put(ob, r, 2, 24, NUM, BLUE); OB["eq_life"] = r
r += 1; ob.cell(r, 1, "Remaining useful life of opening capitalised software (months)"); put(ob, r, 2, 36, NUM, BLUE); OB["sw_life"] = r
OBS = lambda k: f"'Opening BS'!$B${OB[k]}"

# ───────────── ENGINE BUILDER ─────────────
NM = 60
def mc(m): return L(3 + m)          # m=0 -> C (Dec 2026), m=1 -> D ...
FIRST, LAST = mc(1), mc(NM)
def yi(c): return f"{c}$8"           # year index (1..5) in row 8
def AY(key, c): return f"INDEX(Assumptions!$C${AR[key]}:$G${AR[key]},{yi(c)})"
def CPv(param, ctry): return f"Countries!${L(3 + CTRY.index(ctry))}${CP[param]}"

ENG = {}   # scenario -> (sheet name, row dict)
def build_engine(scn):
    sname = f"Engine_{scn}"; sc = SC[scn]
    ws = wb.create_sheet(sname); ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 46; ws.column_dimensions["B"].width = 10
    for m in range(0, NM + 1): ws.column_dimensions[mc(m)].width = 12
    ws["A1"] = f"Monthly Engine — {scn} scenario"; ws["A1"].font = fnt("1A2420", True, size=14)
    ws["A2"] = "EGP. Column C = opening position (31 Dec 2026). Each column is one month. Annual sheets read from here."; ws["A2"].font = fnt("5A675F", italic=True, size=9)
    labels = {3: "Period code", 4: "Year", 5: "Month of year", 6: "Month index", 7: "Month", 8: "Year index"}
    for rr_, lab in labels.items(): ws.cell(rr_, 1, lab).font = fnt("5A675F", size=9)
    for m in range(0, NM + 1):
        c = mc(m); y = 2026 + (m + 11) // 12 if m > 0 else 2026; mo = ((m - 1) % 12) + 1 if m > 0 else 12
        put(ws, 3, 3 + m, y * 100 + mo, GEN); put(ws, 4, 3 + m, y, GEN); put(ws, 5, 3 + m, mo, GEN); put(ws, 6, 3 + m, m, GEN)
        put(ws, 7, 3 + m, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][mo - 1] + "-" + str(y)[2:], GEN, bold=True)
        put(ws, 8, 3 + m, y - 2026, GEN)
        ws.cell(7, 3 + m).fill = HFILL; ws.cell(7, 3 + m).font = fnt("FFFFFF", True)
    ws.cell(7, 1).fill = HFILL; ws.cell(7, 2).fill = HFILL
    ws.freeze_panes = "D9"
    R = {}; st = {"r": 9}
    def S(text):
        st["r"] += 1; rr_ = st["r"]
        for cc in range(1, 3 + NM + 1): ws.cell(rr_, cc).fill = SFILL
        ws.cell(rr_, 1, text).font = fnt(bold=True)
    def row(key, label, unit, fn, m0=None, fmt=EGP, bold=False, color=BLACK, border=None):
        st["r"] += 1; rr_ = st["r"]; R[key] = rr_
        ws.cell(rr_, 1, label).font = fnt(bold=bold); ws.cell(rr_, 2, unit).font = fnt("5A675F", size=9)
        if m0 is not None:
            c0 = put(ws, rr_, 3, m0, fmt, GREEN if isinstance(m0, str) and "!" in m0 else BLACK, bold)
        for m in range(1, NM + 1):
            c, p = mc(m), mc(m - 1); n = mc(min(m + 1, NM))
            v = fn(c, p, n, m)
            cell = put(ws, rr_, 3 + m, v, fmt, color, bold)
            if border: cell.border = border
        return rr_
    def rf(k, c): return f"{c}{R[k]}"
    rows = lambda keys, c: "+".join(rf(k, c) for k in keys)

    S("RESTAURANT FUNNEL")
    for ct in CTRY:
        cc_ = CPv
        tgt = f"Countries!$C${CT[ct]}:$G${CT[ct]}"
        ach = f"Assumptions!${sc}${AR['ach']}"
        def target(c, p, n, m, ct=ct, tgt=tgt, ach=ach):
            prev = f"IF({yi(c)}=1,{CPv('open', ct)},INDEX({tgt},{yi(c)}-1)*{ach})"
            cur = f"INDEX({tgt},{yi(c)})*{ach}"
            return f"=ROUND({prev}+({cur}-{prev})*{c}$5/12,0)"
        row(f"live_{ct}", f"Live restaurants — {CNAME[ct]}", "#", target, m0=f"={CPv('open', ct)}", fmt=NUM)
        row(f"churn_{ct}", f"  Churned — {CNAME[ct]}", "#", lambda c, p, n, m, ct=ct: f"={p}{R['live_'+ct]}*Assumptions!${sc}${AR['churn']}", fmt=EGP1)
        row(f"new_{ct}", f"  New live — {CNAME[ct]}", "#", lambda c, p, n, m, ct=ct: f"=MAX(0,{c}{R['live_'+ct]}-{p}{R['live_'+ct]}+{c}{R['churn_'+ct]})", m0=0, fmt=EGP1)
        row(f"sign_{ct}", f"  Signed (go live next month) — {CNAME[ct]}", "#", lambda c, p, n, m, ct=ct: f"={n}{R['new_'+ct]}" if m < NM else f"={c}{R['new_'+ct]}", fmt=EGP1)
        row(f"trx_{ct}", f"  Transacting (ramp-adjusted) — {CNAME[ct]}", "#",
            lambda c, p, n, m, ct=ct: f"=MAX(0,({c}{R['live_'+ct]}-{c}{R['new_'+ct]}*(1-{A['r1']})-{p}{R['new_'+ct]}*(1-{A['r2']})))*Assumptions!${sc}${AR['activ']}", fmt=EGP1)
    row("live", "Live restaurants — total", "#", lambda c, p, n, m: "=" + rows([f"live_{x}" for x in CTRY], c), m0="=" + rows([f"live_{x}" for x in CTRY], "C"), fmt=NUM, bold=True)
    row("new", "New live restaurants — total", "#", lambda c, p, n, m: "=" + rows([f"new_{x}" for x in CTRY], c), m0=0, fmt=EGP1, bold=True)
    row("churned", "Churned restaurants — total", "#", lambda c, p, n, m: "=" + rows([f"churn_{x}" for x in CTRY], c), fmt=EGP1)
    row("signed", "Signed restaurants — total", "#", lambda c, p, n, m: "=" + rows([f"sign_{x}" for x in CTRY], c), fmt=EGP1)
    row("trx", "Transacting restaurants — total", "#", lambda c, p, n, m: "=" + rows([f"trx_{x}" for x in CTRY], c), fmt=EGP1, bold=True)
    row("paying", "Paying subscribers (live × paid-plan share)", "#", lambda c, p, n, m: f"={c}{R['live']}*(1-{AY('p_free', c)})", fmt=EGP1)

    S("TRANSACTIONS & COMMISSION")
    for ct in CTRY:
        def bill(c, p, n, m, ct=ct):
            base = f"{CPv('bill', ct)}*(1+{CPv('billg', ct)})^({yi(c)}-1)*Assumptions!${sc}${AR['billx']}"
            if ct == "EG": return "=" + base
            return f"={base}/FX!$C${FXR[ct]}*INDEX(FX!$C$5:$G$5,{yi(c)})"
        row(f"bill_{ct}", f"Average bill in EGP — {CNAME[ct]}", "EGP", bill, fmt=EGP)
        row(f"bills_{ct}", f"  Completed bills — {CNAME[ct]}", "#", lambda c, p, n, m, ct=ct: f"={c}{R['trx_'+ct]}*Assumptions!${sc}${AR['bills']}", fmt=NUM)
        row(f"gmv_{ct}", f"  Completed GMV — {CNAME[ct]}", "EGP", lambda c, p, n, m, ct=ct: f"={c}{R['bills_'+ct]}*{c}{R['bill_'+ct]}", fmt=EGP)
        row(f"comm_{ct}", f"  Commission revenue — {CNAME[ct]}", "EGP",
            lambda c, p, n, m, ct=ct: f"={c}{R['gmv_'+ct]}*(1-{A['refund']})*{A['c_eff']}*(1-{AY('waive', c)})", fmt=EGP)
    row("bills", "Completed bills — total", "#", lambda c, p, n, m: "=" + rows([f"bills_{x}" for x in CTRY], c), fmt=NUM, bold=True)
    row("gmv", "Completed GMV — total (restaurants' money, not revenue)", "EGP", lambda c, p, n, m: "=" + rows([f"gmv_{x}" for x in CTRY], c), bold=True)
    row("refunds", "Less: refunds & cancellations", "EGP", lambda c, p, n, m: f"=-{c}{R['gmv']}*{A['refund']}")
    row("egmv", "Eligible completed GMV", "EGP", lambda c, p, n, m: f"={c}{R['gmv']}+{c}{R['refunds']}", bold=True)
    row("comm_gross", "Gross commission (eligible GMV × rate)", "EGP", lambda c, p, n, m: "=SUMPRODUCT(" + f"{c}{R['gmv_EG']}" + ")*0+" + "+".join(f"{c}{R['gmv_'+x]}" for x in CTRY) + f"*0+{c}{R['egmv']}*{A['c_eff']}")
    row("waived", "Less: waived commission & incentives", "EGP", lambda c, p, n, m: f"=-{c}{R['comm_gross']}*{AY('waive', c)}")
    row("comm", "Commission revenue — total", "EGP", lambda c, p, n, m: "=" + rows([f"comm_{x}" for x in CTRY], c), bold=True)

    S("SUBSCRIPTIONS")
    arpa = lambda c: (f"({AY('p_single', c)}*{A['pr_single']}+{AY('p_full', c)}*{A['pr_full']}+{AY('p_multi', c)}*{A['pr_multi']})"
                      f"*(1+{A['pr_inc']})^({yi(c)}-1)")
    row("arpa", "Subscription revenue per live restaurant (Egypt prices)", "EGP / mo", lambda c, p, n, m: "=" + arpa(c), fmt=EGP)
    for ct in CTRY:
        row(f"sub_{ct}", f"  Subscriptions — {CNAME[ct]}", "EGP", lambda c, p, n, m, ct=ct: f"={c}{R['live_'+ct]}*{c}{R['arpa']}*{CPv('pidx', ct)}")
    row("sub", "Subscription revenue — total", "EGP", lambda c, p, n, m: "=" + rows([f"sub_{x}" for x in CTRY], c), bold=True)

    S("RESTAURANT MARKETING & ADVERTISING")
    mrec = lambda c: (f"({AY('m_b', c)}*{A['pr_b']}+{AY('m_s', c)}*{A['pr_s']}+{AY('m_g', c)}*{A['pr_g']})*Assumptions!${sc}${AR['mktx']}*(1+{A['pr_inc']})^({yi(c)}-1)")
    mone = lambda c: f"{AY('m_one', c)}*{A['pr_one']}/12*Assumptions!${sc}${AR['mktx']}*(1+{A['pr_inc']})^({yi(c)}-1)"
    row("mrec_pr", "Recurring packages per live restaurant", "EGP / mo", lambda c, p, n, m: "=" + mrec(c))
    row("mone_pr", "One-time campaigns per live restaurant", "EGP / mo", lambda c, p, n, m: "=" + mone(c))
    for ct in CTRY:
        row(f"mrec_{ct}", f"  Recurring packages — {CNAME[ct]}", "EGP", lambda c, p, n, m, ct=ct: f"={c}{R['live_'+ct]}*{c}{R['mrec_pr']}*{CPv('pidx', ct)}")
        row(f"mone_{ct}", f"  One-time campaigns — {CNAME[ct]}", "EGP", lambda c, p, n, m, ct=ct: f"={c}{R['live_'+ct]}*{c}{R['mone_pr']}*{CPv('pidx', ct)}")
    row("mrec", "Recurring marketing packages — total", "EGP", lambda c, p, n, m: "=" + rows([f"mrec_{x}" for x in CTRY], c), bold=True)
    row("mone", "One-time campaigns — total", "EGP", lambda c, p, n, m: "=" + rows([f"mone_{x}" for x in CTRY], c), bold=True)

    S("BRAND SPONSORSHIPS")
    row("sp_new", "New campaigns started (projected + signed)", "#", lambda c, p, n, m: f"=({AY('s_new', c)}*Assumptions!${sc}${AR['sponx']}+{AY('s_signed', c)})/12", fmt=DEC2)
    row("sp_ren", "Renewed campaigns started", "#", lambda c, p, n, m: f"=IF({c}$6>{A['s_dur']},INDEX(${FIRST}{{SPST}}:${LAST}{{SPST}},{c}$6-{A['s_dur']})*{A['s_ren']},0)", fmt=DEC2)
    row("sp_st", "Total campaigns started", "#", lambda c, p, n, m: f"={c}{R['sp_new']}+{c}{R['sp_ren']}", fmt=DEC2)
    row("sp_act", "Active campaigns", "#", lambda c, p, n, m: f"=SUMPRODUCT((${FIRST}$6:${LAST}$6>{c}$6-{A['s_dur']})*(${FIRST}$6:${LAST}$6<={c}$6)*${FIRST}{R['sp_st']}:${LAST}{R['sp_st']})", fmt=DEC2)
    row("spon", "Sponsorship revenue (recognised over campaign)", "EGP", lambda c, p, n, m: f"={c}{R['sp_act']}*{AY('s_acv', c)}/{A['s_dur']}", bold=True)
    for m in range(1, NM + 1):
        cell = ws.cell(R["sp_ren"], 3 + m); cell.value = cell.value.replace("{SPST}", str(R["sp_st"]))

    S("REVENUE")
    for ct in CTRY:
        row(f"rev_{ct}", f"Revenue — {CNAME[ct]}", "EGP", lambda c, p, n, m, ct=ct: f"={c}{R['comm_'+ct]}+{c}{R['sub_'+ct]}+{c}{R['mrec_'+ct]}+{c}{R['mone_'+ct]}")
    row("rev", "TOTAL REVENUE", "EGP", lambda c, p, n, m: f"={c}{R['comm']}+{c}{R['sub']}+{c}{R['mrec']}+{c}{R['mone']}+{c}{R['spon']}", bold=True, border=TOP)

    S("DIRECT COSTS (COST OF REVENUE)")
    row("c_host", "Hosting & infrastructure", "EGP", lambda c, p, n, m: f"={AY('host_fix', c)}+{c}{R['live']}*{A['host_var']}")
    row("c_msg", "Messaging (WhatsApp / SMS)", "EGP", lambda c, p, n, m: f"={c}{R['bills']}*{A['msg']}")
    row("c_pay", "Payment fees on subscription & package collections", "EGP", lambda c, p, n, m: f"=({c}{R['sub']}+{c}{R['mrec']}+{c}{R['mone']})*{A['collect']}*{A['payfee']}")
    row("c_mkt", "Marketing delivery (creative, account management)", "EGP", lambda c, p, n, m: f"=({c}{R['mrec']}+{c}{R['mone']})*{A['m_cost']}")
    row("c_spon", "Sponsorship delivery", "EGP", lambda c, p, n, m: f"={c}{R['spon']}*{A['s_cost']}")
    row("c_part", "Operating-partner revenue share", "EGP", lambda c, p, n, m: "=" + "+".join(f"{c}{R['rev_'+x]}*{CPv('partner', x)}" for x in CTRY))
    row("cogs", "Total direct costs", "EGP", lambda c, p, n, m: f"=SUM({c}{R['c_host']}:{c}{R['c_part']})", bold=True, border=TOP)
    row("gp", "GROSS PROFIT", "EGP", lambda c, p, n, m: f"={c}{R['rev']}-{c}{R['cogs']}", bold=True)

    S("HEADCOUNT")
    for k, name, *_ in FUNCS:
        hr_ = HC[k]
        def hc(c, p, n, m, hr_=hr_):
            prev = f"IF({yi(c)}=1,Assumptions!$B${hr_},INDEX(Assumptions!$C${hr_}:$G${hr_},{yi(c)}-1))"
            cur = f"INDEX(Assumptions!$C${hr_}:$G${hr_},{yi(c)})"
            return f"=ROUND({prev}+({cur}-{prev})*{c}$5/12,0)"
        row(f"hc_{k}", f"Heads — {name}", "#", hc, m0=f"=Assumptions!$B${hr_}", fmt=NUM)
    row("hc", "Total headcount", "#", lambda c, p, n, m: "=" + rows([f"hc_{k}" for k, *_ in FUNCS], c), m0="=" + rows([f"hc_{k}" for k, *_ in FUNCS], "C"), fmt=NUM, bold=True)
    row("hires", "New hires", "#", lambda c, p, n, m: f"=MAX(0,{c}{R['hc']}-{p}{R['hc']})", fmt=NUM)

    S("OPERATING EXPENSES")
    for k, name, *_ in FUNCS:
        row(f"sal_{k}", f"Salaries — {name}", "EGP", lambda c, p, n, m, k=k: f"={c}{R['hc_'+k]}*Assumptions!$H${HC[k]}*(1+{A['raise']})^({yi(c)}-1)")
    row("o_cons", "Hospitality-consultant fees (restaurant acquisition)", "EGP", lambda c, p, n, m: f"={c}{R['new_EG']}*{A['cons_share']}*{A['cons_fee']}*{CPv('consult','EG')}")
    row("o_onb", "Restaurant onboarding", "EGP", lambda c, p, n, m: "=" + "+".join(f"{c}{R['new_'+x]}*{CPv('onb', x)}" for x in CTRY))
    row("o_perf", "Restaurant-acquisition marketing", "EGP", lambda c, p, n, m: f"={c}{R['new']}*{A['perf']}")
    row("o_brand", "Brand & consumer marketing (non-acquisition)", "EGP", lambda c, p, n, m: f"={c}{R['rev']}*{AY('brand', c)}")
    row("o_ga", "General & administration", "EGP", lambda c, p, n, m: f"={AY('ga', c)}")
    row("o_legal", "Legal, audit & compliance", "EGP", lambda c, p, n, m: f"={AY('legal', c)}/12")
    row("o_launch", "Country launch costs", "EGP", lambda c, p, n, m: "=" + "+".join(f"IF(AND({c}$4={CPv('launch', x)},{c}$5=1),{CPv('launchc', x)},0)" for x in CTRY))
    row("o_bad", "Bad debt (uncollected subscriptions & packages)", "EGP", lambda c, p, n, m: f"=({c}{R['sub']}+{c}{R['mrec']}+{c}{R['mone']})*(1-{A['collect']})")
    row("o_cap", "Less: development costs capitalised (IAS 38)", "EGP", lambda c, p, n, m: f"=-({c}{R['sal_eng']}+{c}{R['sal_prod']})*{A['capdev']}")
    row("opex", "Total operating expenses", "EGP", lambda c, p, n, m: f"=SUM({c}{R['sal_eng']}:{c}{R['o_cap']})", bold=True, border=TOP)
    row("ebitda", "EBITDA", "EGP", lambda c, p, n, m: f"={c}{R['gp']}-{c}{R['opex']}", bold=True, border=TOP)
    row("pos", "EBITDA positive (1 = yes)", "flag", lambda c, p, n, m: f"=IF({c}{R['ebitda']}>0,1,0)", fmt=GEN)

    S("DEPRECIATION, AMORTISATION, TAX")
    row("capex", "Equipment capex", "EGP", lambda c, p, n, m: f"={c}{R['hires']}*{A['laptop']}+{c}{R['new']}*{A['dev_capex']}")
    row("capsw", "Capitalised development", "EGP", lambda c, p, n, m: f"=-{c}{R['o_cap']}")
    row("dep", "Depreciation", "EGP", lambda c, p, n, m: f"=SUMPRODUCT((${FIRST}$6:${LAST}$6>{c}$6-{A['life_eq']})*(${FIRST}$6:${LAST}$6<={c}$6)*${FIRST}{R['capex']}:${LAST}{R['capex']})/{A['life_eq']}"
        f"+IF({c}$6<={OBS('eq_life')},({OBS('b_eqc')}-{OBS('b_eqd')})/{OBS('eq_life')},0)")
    row("amort", "Amortisation of capitalised software", "EGP", lambda c, p, n, m: f"=SUMPRODUCT((${FIRST}$6:${LAST}$6>{c}$6-1-{A['life_sw']})*(${FIRST}$6:${LAST}$6<={c}$6-1)*${FIRST}{R['capsw']}:${LAST}{R['capsw']})/{A['life_sw']}"
        f"+IF({c}$6<={OBS('sw_life')},({OBS('b_swc')}-{OBS('b_swa')})/{OBS('sw_life')},0)")
    row("ebit", "Operating profit (EBIT)", "EGP", lambda c, p, n, m: f"={c}{R['ebitda']}-{c}{R['dep']}-{c}{R['amort']}", bold=True)
    row("int", "Interest income", "EGP", lambda c, p, n, m: f"=MAX(0,{p}{{CASH}})*{A['int_rate']}/12")
    row("pbt", "Profit before tax", "EGP", lambda c, p, n, m: f"={c}{R['ebit']}+{c}{R['int']}", bold=True)
    row("pbt_y", "Annual profit before tax (December only)", "EGP", lambda c, p, n, m: f"=IF({c}$5=12,SUMIF(${FIRST}$4:${LAST}$4,{c}$4,${FIRST}{R['pbt']}:${LAST}{R['pbt']}),0)")
    row("lcf", "Tax losses carried forward (closing)", "EGP", lambda c, p, n, m: f"=IF({c}$5=12,MAX(0,{p}{{LCF}}-{c}{R['pbt_y']}),{p}{{LCF}})", m0=f"={A['taxloss']}")
    row("tax", "Corporate income tax expense (booked in December)", "EGP", lambda c, p, n, m: f"=IF({c}$5=12,MAX(0,{c}{R['pbt_y']}-{p}{R['lcf']})*{A['tax']},0)")
    row("ni", "NET PROFIT", "EGP", lambda c, p, n, m: f"={c}{R['pbt']}-{c}{R['tax']}", bold=True, border=DTOP)

    S("WORKING CAPITAL & TAX PAYABLE")
    row("ar", "Accounts receivable", "EGP", lambda c, p, n, m: f"={c}{R['comm']}*{A['d_comm']}/30+({c}{R['sub']}+{c}{R['mrec']}+{c}{R['mone']})*{A['collect']}*{A['d_sub']}/30+{c}{R['spon']}*{A['d_spon']}/30", m0=f"={OBS('b_ar')}")
    row("ap", "Accounts payable", "EGP", lambda c, p, n, m: f"=({c}{R['cogs']}+{c}{R['o_cons']}+{c}{R['o_onb']}+{c}{R['o_perf']}+{c}{R['o_brand']}+{c}{R['o_ga']}+{c}{R['o_legal']}+{c}{R['o_launch']})*{A['d_ap']}/30", m0=f"={OBS('b_ap')}")
    row("taxpaid", "Tax paid", "EGP", lambda c, p, n, m: f"=IF({c}$5={A['taxmonth']},{p}{{TAXP}},0)")
    row("taxp", "Tax payable", "EGP", lambda c, p, n, m: f"={p}{{TAXP}}+{c}{R['tax']}-{c}{R['taxpaid']}", m0=0)

    S("CASH FLOW")
    row("cf_ni", "Net profit", "EGP", lambda c, p, n, m: f"={c}{R['ni']}")
    row("cf_da", "Add: depreciation & amortisation", "EGP", lambda c, p, n, m: f"={c}{R['dep']}+{c}{R['amort']}")
    row("cf_ar", "(Increase) / decrease in receivables", "EGP", lambda c, p, n, m: f"=-({c}{R['ar']}-{p}{R['ar']})")
    row("cf_ap", "Increase / (decrease) in payables", "EGP", lambda c, p, n, m: f"={c}{R['ap']}-{p}{R['ap']}")
    row("cf_tax", "Increase / (decrease) in tax payable", "EGP", lambda c, p, n, m: f"={c}{R['taxp']}-{p}{R['taxp']}")
    row("cfo", "Cash from operating activities", "EGP", lambda c, p, n, m: f"=SUM({c}{R['cf_ni']}:{c}{R['cf_tax']})", bold=True, border=TOP)
    row("cf_capex", "Equipment capex", "EGP", lambda c, p, n, m: f"=-{c}{R['capex']}")
    row("cf_capsw", "Capitalised development", "EGP", lambda c, p, n, m: f"=-{c}{R['capsw']}")
    row("cfi", "Cash from investing activities", "EGP", lambda c, p, n, m: f"={c}{R['cf_capex']}+{c}{R['cf_capsw']}", bold=True, border=TOP)
    row("cf_eq", "Equity raised (selected funding scenario)", "EGP", lambda c, p, n, m: f"=IF({c}$6=1,{A['raise_sel']}*INDEX(FX!$C$5:$G$5,1),0)")
    row("cf_add", "Additional financing", "EGP", lambda c, p, n, m: f"=IF({c}$5=1,{AY('addfin', c)},0)")
    row("cff", "Cash from financing activities", "EGP", lambda c, p, n, m: f"={c}{R['cf_eq']}+{c}{R['cf_add']}", bold=True, border=TOP)
    row("netcf", "Net change in cash", "EGP", lambda c, p, n, m: f"={c}{R['cfo']}+{c}{R['cfi']}+{c}{R['cff']}", bold=True)
    row("cash", "Closing cash", "EGP", lambda c, p, n, m: f"={p}{{CASH}}+{c}{R['netcf']}", m0=f"={OBS('b_cash')}", bold=True, border=DTOP)
    row("precash", "Cash before any new financing (opening + cumulative operating & investing)", "EGP", lambda c, p, n, m: f"={p}{{PRE}}+{c}{R['cfo']}+{c}{R['cfi']}", m0=f"={OBS('b_cash')}")
    row("flag", "Funding shortfall flag (cash below buffer)", "", lambda c, p, n, m: f'=IF({c}{R["cash"]}<{A["minbuf"]},"SHORTFALL","ok")', fmt=GEN)
    row("burn", "Monthly net burn (negative operating + investing cash flow)", "EGP", lambda c, p, n, m: f"=MAX(0,-({c}{R['cfo']}+{c}{R['cfi']}))")

    S("BALANCE SHEET")
    row("bs_cash", "Cash", "EGP", lambda c, p, n, m: f"={c}{R['cash']}", m0=f"=C{R['cash']}")
    row("bs_ar", "Accounts receivable", "EGP", lambda c, p, n, m: f"={c}{R['ar']}", m0=f"=C{R['ar']}")
    row("bs_eq", "Equipment, net", "EGP", lambda c, p, n, m: f"={p}{{BSEQ}}+{c}{R['capex']}-{c}{R['dep']}", m0=f"={OBS('b_eqc')}-{OBS('b_eqd')}")
    row("bs_sw", "Capitalised software, net", "EGP", lambda c, p, n, m: f"={p}{{BSSW}}+{c}{R['capsw']}-{c}{R['amort']}", m0=f"={OBS('b_swc')}-{OBS('b_swa')}")
    row("bs_ta", "Total assets", "EGP", lambda c, p, n, m: f"=SUM({c}{R['bs_cash']}:{c}{R['bs_sw']})", m0=f"=SUM(C{R['bs_cash']}:C{R['bs_sw']})", bold=True, border=TOP)
    row("bs_ap", "Accounts payable", "EGP", lambda c, p, n, m: f"={c}{R['ap']}", m0=f"=C{R['ap']}")
    row("bs_tax", "Tax payable", "EGP", lambda c, p, n, m: f"={c}{R['taxp']}", m0=f"=C{R['taxp']}")
    row("bs_sl", "Shareholder loans", "EGP", lambda c, p, n, m: f"={p}{{BSSL}}", m0=f"={OBS('b_sl')}")
    row("bs_tl", "Total liabilities", "EGP", lambda c, p, n, m: f"=SUM({c}{R['bs_ap']}:{c}{R['bs_sl']})", m0=f"=SUM(C{R['bs_ap']}:C{R['bs_sl']})", bold=True, border=TOP)
    row("bs_pic", "Paid-in capital", "EGP", lambda c, p, n, m: f"={p}{{BSPIC}}+{c}{R['cf_eq']}+{c}{R['cf_add']}", m0=f"={OBS('b_pic')}")
    row("bs_re", "Retained earnings", "EGP", lambda c, p, n, m: f"={p}{{BSRE}}+{c}{R['ni']}", m0=f"={OBS('b_re')}")
    row("bs_te", "Total equity", "EGP", lambda c, p, n, m: f"={c}{R['bs_pic']}+{c}{R['bs_re']}", m0=f"=C{R['bs_pic']}+C{R['bs_re']}", bold=True, border=TOP)
    row("bs_tle", "Total liabilities & equity", "EGP", lambda c, p, n, m: f"={c}{R['bs_tl']}+{c}{R['bs_te']}", m0=f"=C{R['bs_tl']}+C{R['bs_te']}", bold=True, border=DTOP)
    row("bs_chk", "Balance check (must be 0)", "EGP", lambda c, p, n, m: f"=ROUND({c}{R['bs_ta']}-{c}{R['bs_tle']},0)", m0=f"=ROUND(C{R['bs_ta']}-C{R['bs_tle']},0)", bold=True)

    # resolve self-references
    subs = {"CASH": R["cash"], "LCF": R["lcf"], "TAXP": R["taxp"], "PRE": R["precash"], "BSEQ": R["bs_eq"], "BSSW": R["bs_sw"],
            "BSSL": R["bs_sl"], "BSPIC": R["bs_pic"], "BSRE": R["bs_re"]}
    for row_ in ws.iter_rows(min_row=9, max_row=st["r"], min_col=3, max_col=3 + NM):
        for cell in row_:
            if isinstance(cell.value, str) and "{" in cell.value:
                v = cell.value
                for k_, n_ in subs.items(): v = v.replace("{" + k_ + "}", str(n_))
                cell.value = v
    # simplify gross-commission row formula
    for m in range(1, NM + 1):
        c = mc(m); ws.cell(R["comm_gross"], 3 + m).value = f"={c}{R['egmv']}*{A['c_eff']}"
    for rr_ in (R["bs_chk"],):
        for m in range(0, NM + 1): ws.cell(rr_, 3 + m).fill = TFILL
    ENG[scn] = (sname, R)
for s in ["Downside", "Base", "Upside"]:
    build_engine(s)
# ───────────── selected-scenario helpers ─────────────
ENGL = [ENG[s] for s in ["Downside", "Base", "Upside"]]
def SY(key, yc):
    return "CHOOSE(" + A["scen"] + "," + ",".join(f"SUMIF({sn}!${FIRST}$4:${LAST}$4,{yc}$3,{sn}!${FIRST}${R[key]}:${LAST}${R[key]})" for sn, R in ENGL) + ")"
def EY(key, yc):
    return "CHOOSE(" + A["scen"] + "," + ",".join(f"INDEX({sn}!${FIRST}${R[key]}:${LAST}${R[key]},MATCH({yc}$3*100+12,{sn}!${FIRST}$3:${LAST}$3,0))" for sn, R in ENGL) + ")"
def OY(key):
    return "CHOOSE(" + A["scen"] + "," + ",".join(f"{sn}!$C${R[key]}" for sn, R in ENGL) + ")"
def MS(key, m):   # selected scenario, month m
    return "CHOOSE(" + A["scen"] + "," + ",".join(f"{sn}!{mc(m)}${R[key]}" for sn, R in ENGL) + ")"
def SYS(scn, key, yc):
    sn, R = ENG[scn]; return f"SUMIF({sn}!${FIRST}$4:${LAST}$4,{yc}$3,{sn}!${FIRST}${R[key]}:${LAST}${R[key]})"
def EYS(scn, key, yc):
    sn, R = ENG[scn]; return f"INDEX({sn}!${FIRST}${R[key]}:${LAST}${R[key]},MATCH({yc}$3*100+12,{sn}!${FIRST}$3:${LAST}$3,0))"
def SEL(rowkey):   # pick scenario column from Assumptions by-scen row
    return f"INDEX(Assumptions!$C${AR[rowkey]}:$E${AR[rowkey]},{A['scen']})"
FXY = lambda yc: f"FX!{yc}$5"

def ann_sheet(name, title, sub, opening=False):
    ws = new_sheet(name, title, sub, (50, 12, 16, 16, 16, 16, 16, 16, 62) if opening else (50, 12, 16, 16, 16, 16, 16, 62))
    off = 1 if opening else 0
    for i, y in enumerate(YEARS): put(ws, 3, 3 + off + i, y, GEN, "999999")
    ws.cell(3, 1, "Year (number, used by formulas)").font = fnt("999999", size=8)
    head = ["", "Unit"] + (["Opening"] if opening else []) + [str(y) for y in YEARS] + ["Notes"]
    hdr(ws, 4, head); ws.freeze_panes = "C5"
    return ws
class Rows:
    def __init__(self, ws, opening=False): self.ws, self.r, self.R, self.off = ws, 4, {}, (1 if opening else 0)
    def sec(self, t): self.r += 1; sec(self.ws, self.r, t, 8 + self.off)
    def blank(self): self.r += 1
    def add(self, key, label, unit, fn, fmt=EGP, bold=False, color=BLACK, note_=None, border=None, opening=None, fill=None):
        self.r += 1; r_ = self.r; self.R[key] = r_
        self.ws.cell(r_, 1, label).font = fnt(bold=bold); self.ws.cell(r_, 2, unit).font = fnt("5A675F", size=9)
        if opening is not None: put(self.ws, r_, 3, opening, fmt, color, bold)
        for i, yc in enumerate(YC):
            col = L(3 + self.off + i)
            c = put(self.ws, r_, 3 + self.off + i, fn(col, i), fmt, color, bold, fill=fill)
            if border: c.border = border
        if note_: note(self.ws, r_, 8 + self.off, note_)
        return r_

# ───────────── REVENUE & MONETIZATION ─────────────
rv = ann_sheet("Revenue & Monetization", "Revenue & Monetization Model", "Selected operating scenario. GMV is restaurants' money; Reservya revenue is commission, subscriptions, marketing and sponsorships.")
X_ = Rows(rv)
X_.sec("Restaurant funnel")
X_.add("signed", "Restaurants signed", "#", lambda c, i: f"={SY('signed', c)}", NUM, color=GREEN)
X_.add("newlive", "Restaurants going live (onboarded)", "#", lambda c, i: f"={SY('new', c)}", NUM, color=GREEN)
X_.add("churned", "Restaurants churned", "#", lambda c, i: f"={SY('churned', c)}", NUM, color=GREEN)
X_.add("live", "Live restaurants at year end", "#", lambda c, i: f"={EY('live', c)}", NUM, True, GREEN, "Base = management targets 200 / 600 / 1,200 / 2,000 / 3,000.")
X_.add("avglive", "Average live restaurants during the year", "#", lambda c, i: f"={SY('live', c)}/12", NUM, color=GREEN, note_="Revenue is earned on the average, not the year-end count.")
X_.add("avgtrx", "Average transacting restaurants (ramp & activity adjusted)", "#", lambda c, i: f"={SY('trx', c)}/12", NUM, color=GREEN)
X_.add("payingend", "Paying subscribers at year end", "#", lambda c, i: f"={EY('paying', c)}", NUM, color=GREEN)
X_.sec("Transactions & commission")
X_.add("bills", "Completed online bills", "#", lambda c, i: f"={SY('bills', c)}", NUM, color=GREEN)
X_.add("gmv", "Completed GMV (platform volume — not Reservya revenue)", "EGP", lambda c, i: f"={SY('gmv', c)}", color=GREEN)
X_.add("refunds", "Less: refunds & cancellations", "EGP", lambda c, i: f"={SY('refunds', c)}", color=GREEN)
X_.add("egmv", "Eligible completed GMV", "EGP", lambda c, i: f"={SY('egmv', c)}", bold=True, color=GREEN)
X_.add("cgross", "Gross commission", "EGP", lambda c, i: f"={SY('comm_gross', c)}", color=GREEN)
X_.add("waived", "Less: waived commission & incentives", "EGP", lambda c, i: f"={SY('waived', c)}", color=GREEN)
X_.add("comm", "Commission revenue", "EGP", lambda c, i: f"={SY('comm', c)}", bold=True, color=GREEN)
X_.add("ratecheck", "Realised commission on eligible GMV", "%", lambda c, i: f"=IFERROR({c}{X_.R['comm']}/{c}{X_.R['egmv']},0)", PCT)
X_.sec("Subscriptions (core recurring revenue)")
for k, lab in [("p_free", "Commission-only (no fee)"), ("p_single", "Single Feature (EGP 2,000)"), ("p_full", "Full Features (EGP 5,000)"), ("p_multi", "Multi-venue per branch (EGP 3,000)")]:
    X_.add("cnt_" + k, f"Restaurants on {lab} at year end", "#", lambda c, i, k=k: f"={c}{X_.R['live']}*Assumptions!{c}{AR[k]}", NUM)
X_.add("newpay", "New paying subscribers", "#", lambda c, i: f"={c}{X_.R['newlive']}*(1-Assumptions!{c}{AR['p_free']})", NUM)
X_.add("churnpay", "Paying subscribers churned", "#", lambda c, i: f"={c}{X_.R['churned']}*(1-Assumptions!{c}{AR['p_free']})", NUM)
X_.add("arpa", "Subscription revenue per live restaurant (Egypt prices)", "EGP / mo", lambda c, i: f"={SY('arpa', c)}/12", EGP, color=GREEN, note_="Plan mix × list prices × annual price increase.")
X_.add("mix", "ARPA change from plan mix (upgrades net of downgrades)", "%", lambda c, i: "=0" if i == 0 else f"=IFERROR({c}{X_.R['arpa']}/({L(2+i)}{X_.R['arpa']}*(1+{A['pr_inc']}))-1,0)", PCT, note_="Excludes list-price increases.")
X_.add("mrr", "Subscription MRR (December)", "EGP", lambda c, i: f"={EY('sub', c)}", color=GREEN)
X_.add("arr", "Subscription ARR (December MRR × 12)", "EGP", lambda c, i: f"={c}{X_.R['mrr']}*12", bold=True)
X_.add("subrev", "Subscription revenue billed", "EGP", lambda c, i: f"={SY('sub', c)}", bold=True, color=GREEN)
X_.add("subcoll", "Collected", "EGP", lambda c, i: f"={c}{X_.R['subrev']}*{A['collect']}")
X_.add("renew", "Annual restaurant retention (renewal rate)", "%", lambda c, i: f"=(1-{SEL('churn')})^12", PCT, note_="1 − churn, compounded over 12 months.")
X_.sec("Restaurant marketing & in-app advertising")
for k, lab, pk in [("m_b", "Bronze (EGP 5,000 / mo)", "pr_b"), ("m_s", "Silver (EGP 15,000 / mo)", "pr_s"), ("m_g", "Gold (EGP 25,000 / mo)", "pr_g")]:
    X_.add("ad_" + k, f"Adoption — {lab}", "% of live", lambda c, i, k=k: f"=Assumptions!{c}{AR[k]}*{SEL('mktx')}", PCT)
    X_.add("pk_" + k, f"Active {lab.split(' ')[0]} packages at year end", "#", lambda c, i, k=k: f"={c}{X_.R['live']}*{c}{X_.R['ad_'+k]}", NUM)
X_.add("mrec", "Recurring package revenue", "EGP", lambda c, i: f"={SY('mrec', c)}", color=GREEN, note_="Sponsored listings, featured placement, banners, push campaigns, social packages.")
X_.add("mone", "One-time campaign revenue", "EGP", lambda c, i: f"={SY('mone', c)}", color=GREEN, note_="Seasonal campaigns, event promotions, sponsored collections.")
X_.add("mtot", "Total restaurant marketing revenue", "EGP", lambda c, i: f"={c}{X_.R['mrec']}+{c}{X_.R['mone']}", bold=True)
X_.add("mcost", "Delivery cost (creative, account management)", "EGP", lambda c, i: f"={SY('c_mkt', c)}", color=GREEN, note_="Third-party media bought for restaurants is passed through (agent) — net presentation.")
X_.sec("Brand sponsorships")
X_.add("s_signed", "Signed contracts (verified)", "#", lambda c, i: f"=Assumptions!{c}{AR['s_signed']}", NUM, color=GREEN)
X_.add("s_pipe", "Pipeline (memo — not in revenue)", "#", lambda c, i: f"=Assumptions!{c}{AR['s_pipe']}", NUM, color=GREEN)
X_.add("s_proj", "Projected new campaigns", "#", lambda c, i: f"=Assumptions!{c}{AR['s_new']}*{SEL('sponx')}", NUM)
X_.add("s_st", "Campaigns started (incl. renewals)", "#", lambda c, i: f"={SY('sp_st', c)}", EGP1, color=GREEN)
X_.add("s_rev", "Sponsorship revenue (recognised over delivery)", "EGP", lambda c, i: f"={SY('spon', c)}", bold=True, color=GREEN)
X_.add("s_cost", "Delivery cost", "EGP", lambda c, i: f"={SY('c_spon', c)}", color=GREEN)
X_.sec("Revenue summary")
X_.add("t_comm", "Commission", "EGP", lambda c, i: f"={c}{X_.R['comm']}")
X_.add("t_sub", "Subscriptions", "EGP", lambda c, i: f"={c}{X_.R['subrev']}")
X_.add("t_mkt", "Restaurant marketing", "EGP", lambda c, i: f"={c}{X_.R['mtot']}")
X_.add("t_spon", "Brand sponsorships", "EGP", lambda c, i: f"={c}{X_.R['s_rev']}")
X_.add("t_rev", "Total revenue", "EGP", lambda c, i: f"=SUM({c}{X_.R['t_comm']}:{c}{X_.R['t_spon']})", bold=True, border=DTOP)
X_.add("take", "Take rate (total revenue ÷ completed GMV)", "%", lambda c, i: f"=IFERROR({c}{X_.R['t_rev']}/{c}{X_.R['gmv']},0)", PCT)
X_.add("rpr", "Average revenue per live restaurant", "EGP / mo", lambda c, i: f"=IFERROR(({c}{X_.R['t_rev']}-{c}{X_.R['t_spon']})/{c}{X_.R['avglive']}/12,0)", EGP, True, note_="Excludes brand sponsorships.")
X_.sec("Gross margin by revenue stream")
part = lambda c: f"{SY('c_part', c)}*{{S}}/({c}{X_.R['t_rev']}-{c}{X_.R['t_spon']})"
X_.add("gm_comm", "Commission gross profit", "EGP", lambda c, i: f"={c}{X_.R['comm']}-{SY('c_msg', c)}-IFERROR(" + part(c).replace("{S}", f"{c}{X_.R['comm']}") + ",0)")
X_.add("gm_sub", "Subscription gross profit", "EGP", lambda c, i: f"={c}{X_.R['subrev']}-{SY('c_host', c)}-IFERROR({SY('c_pay', c)}*{c}{X_.R['subrev']}/({c}{X_.R['subrev']}+{c}{X_.R['mtot']}),0)-IFERROR(" + part(c).replace("{S}", f"{c}{X_.R['subrev']}") + ",0)")
X_.add("gm_mkt", "Marketing gross profit", "EGP", lambda c, i: f"={c}{X_.R['mtot']}-{c}{X_.R['mcost']}-IFERROR({SY('c_pay', c)}*{c}{X_.R['mtot']}/({c}{X_.R['subrev']}+{c}{X_.R['mtot']}),0)-IFERROR(" + part(c).replace("{S}", f"{c}{X_.R['mtot']}") + ",0)")
X_.add("gm_spon", "Sponsorship gross profit", "EGP", lambda c, i: f"={c}{X_.R['s_rev']}-{c}{X_.R['s_cost']}")
X_.add("gm_tot", "Total gross profit", "EGP", lambda c, i: f"=SUM({c}{X_.R['gm_comm']}:{c}{X_.R['gm_spon']})", bold=True, border=TOP)
for k, base in [("gmp_comm", "comm"), ("gmp_sub", "subrev"), ("gmp_mkt", "mtot"), ("gmp_spon", "s_rev")]:
    X_.add(k, "Gross margin — " + {"comm": "commission", "subrev": "subscriptions", "mtot": "marketing", "s_rev": "sponsorships"}[base], "%",
           lambda c, i, k=k, base=base: f"=IFERROR({c}{X_.R['gm_'+k.split('_')[1]]}/{c}{X_.R[base]},0)", PCT)
X_.sec("GMV → commission reconciliation (each step once; no double deduction)")
X_.add("rc_gmv", "1. Completed GMV (restaurants' revenue through Reservya)", "EGP", lambda c, i: f"={c}{X_.R['gmv']}")
X_.add("rc_ref", "2. Less refunds & cancellations (deducted once, here only)", "EGP", lambda c, i: f"={c}{X_.R['refunds']}")
X_.add("rc_cgmv", "3. Commissionable GMV (1 + 2)", "EGP", lambda c, i: f"={c}{X_.R['rc_gmv']}+{c}{X_.R['rc_ref']}", bold=True, border=TOP)
X_.add("rc_rate", "4. × Commission rate used", "%", lambda c, i: f"={A['c_eff']}", PCT, color=GREEN)
X_.add("rc_gc", "5. Gross commission (3 × 4)", "EGP", lambda c, i: f"={c}{X_.R['rc_cgmv']}*{c}{X_.R['rc_rate']}", bold=True)
X_.add("rc_wv", "6. Less waivers & launch incentives", "EGP", lambda c, i: f"={c}{X_.R['waived']}")
X_.add("rc_net", "7. Net commission revenue (5 + 6)", "EGP", lambda c, i: f"={c}{X_.R['rc_gc']}+{c}{X_.R['rc_wv']}", bold=True, border=TOP)
X_.add("rc_chk", "Check: step 7 − commission in income statement (must be 0)", "EGP", lambda c, i: f"=ROUND({c}{X_.R['rc_net']}-{c}{X_.R['comm']},0)")
X_.add("rc_eff", "Net commission ÷ completed GMV", "%", lambda c, i: f"=IFERROR({c}{X_.R['rc_net']}/{c}{X_.R['rc_gmv']},0)", PCT)
X_.add("rc_pay", "Memo: card/bank fees on GMV — passed through to restaurants, not Reservya revenue or cost", "", lambda c, i: "", GEN)
X_.r += 2
_vr = X_.r
hdr(rv, _vr, ["Monetisation stream", "Pricing basis", "Adoption basis", "", "Revenue recognition", "", "Delivery cost", "Cash collection", "Evidence status"])
for k_, row_ in enumerate([
    ("Commission (4–7%)", "Feature Guide range; tier mix 30/40/30", "Bills × transacting restaurants", "", "Net of refunds & waivers, when the bill is completed (agent: GMV is not revenue)", "", "Messaging, hosting share", "Settled by Kashier, ~7 days", "Management forecast — no signed rate schedule"),
    ("Subscriptions", "Feature Guide: 0 / 2,000 / 5,000 / 3,000 per branch", "Plan mix on live restaurants", "", "Monthly, over the service period", "", "Hosting, payment fees", "Billed monthly, 15 days, 97% collected", "Price list documented; adoption forecast"),
    ("Restaurant marketing packages", "Packages PDF: 5K / 15K / 25K a month", "Adoption % of live", "", "Over the package month; Reservya fee only (media is agent pass-through, net)", "", "30% creative & account management", "Billed monthly, 15 days", "Price list documented; adoption forecast"),
    ("One-time campaigns & sponsored placements", "Average EGP 7,500 per campaign", "Campaigns per live restaurant per year", "", "When the campaign runs", "", "30% creative", "15 days", "Management forecast"),
    ("Brand sponsorships", "ACV EGP 250K → 600K", "Projected campaigns; signed = 0", "", "Evenly over the campaign (3 months)", "", "20% delivery", "60 days (corporate terms)", "No signed contracts — forecast only")]):
    for j_, v_ in enumerate(row_):
        if v_:
            c_ = rv.cell(_vr + 1 + k_, 1 + j_, v_); c_.font = fnt(size=9); c_.alignment = Alignment(wrap_text=True, vertical="top")
    rv.row_dimensions[_vr + 1 + k_].height = 40
X_.r = _vr + 6
RVR = X_.R

# ───────────── COUNTRY ECONOMICS ─────────────
ce = ann_sheet("Country Economics", "Country Economics", "Selected scenario. Egypt is run directly; other markets through operating partners. Contribution is before central costs.")
Y_ = Rows(ce)
for ct in CTRY:
    Y_.sec(CNAME[ct] + f" — launch {''}")
    ce.cell(Y_.r, 1, f"{CNAME[ct]}  ·  currency " + ["EGP", "SAR", "AED", "JOD", "MAD"][CTRY.index(ct)])
    Y_.add(f"live_{ct}", "Live restaurants at year end", "#", lambda c, i, ct=ct: f"={EY('live_'+ct, c)}", NUM, color=GREEN)
    Y_.add(f"bill_{ct}", "Average bill (EGP)", "EGP", lambda c, i, ct=ct: f"={SY('bill_'+ct, c)}/12", EGP, color=GREEN)
    Y_.add(f"gmv_{ct}", "Completed GMV", "EGP", lambda c, i, ct=ct: f"={SY('gmv_'+ct, c)}", color=GREEN)
    Y_.add(f"rev_{ct}", "Revenue", "EGP", lambda c, i, ct=ct: f"={SY('rev_'+ct, c)}", bold=True, color=GREEN)
    Y_.add(f"part_{ct}", "Less: operating-partner share", "EGP", lambda c, i, ct=ct: f"=-{c}{Y_.R['rev_'+ct]}*{CPv('partner', ct)}")
    Y_.add(f"onb_{ct}", "Less: onboarding costs", "EGP", lambda c, i, ct=ct: f"=-{SY('new_'+ct, c)}*{CPv('onb', ct)}")
    Y_.add(f"lau_{ct}", "Less: launch cost", "EGP", lambda c, i, ct=ct: f"=-IF({c}$3={CPv('launch', ct)},{CPv('launchc', ct)},0)")
    Y_.add(f"con_{ct}", "Country contribution before central costs", "EGP", lambda c, i, ct=ct: f"=SUM({c}{Y_.R['rev_'+ct]}:{c}{Y_.R['lau_'+ct]})", bold=True, border=TOP)

# ───────────── OPEX & HEADCOUNT ─────────────
oh = ann_sheet("Opex & Headcount", "Operating Expense & Headcount Schedule", "Selected scenario. Salaries are fully loaded. Capitalised development reduces operating expense (IAS 38).")
Z_ = Rows(oh)
Z_.sec("Headcount at year end")
for k, name, *_ in FUNCS:
    Z_.add("hc_" + k, name, "#", lambda c, i, k=k: f"={EY('hc_'+k, c)}", NUM, color=GREEN)
Z_.add("hc", "Total headcount", "#", lambda c, i: f"={EY('hc', c)}", NUM, True, GREEN)
Z_.sec("Direct costs")
for k, lab in [("c_host", "Hosting & infrastructure"), ("c_msg", "Messaging"), ("c_pay", "Payment processing on own collections"), ("c_mkt", "Marketing delivery & creative production"), ("c_spon", "Sponsorship delivery"), ("c_part", "Operating-partner revenue share")]:
    Z_.add(k, lab, "EGP", lambda c, i, k=k: f"={SY(k, c)}", color=GREEN)
Z_.add("cogs", "Total direct costs", "EGP", lambda c, i: f"={SY('cogs', c)}", bold=True, color=GREEN, border=TOP)
Z_.sec("Operating expenses")
OPX = [("sal_eng", "Engineering salaries"), ("sal_prod", "Product & design salaries"), ("sal_sales", "Sales & business development salaries"), ("o_cons", "Hospitality-consultant fees"),
       ("sal_supp", "Onboarding & customer support salaries"), ("o_onb", "Restaurant onboarding"), ("sal_mkt", "Marketing & creative salaries"), ("o_perf", "Restaurant-acquisition marketing"),
       ("o_brand", "Brand, social & performance marketing (consumer)"), ("sal_adm", "Management & administration salaries"), ("o_ga", "General & administration"),
       ("o_legal", "Legal, audit & compliance"), ("o_launch", "Expansion & country launch"), ("o_bad", "Bad debt"), ("o_cap", "Less: capitalised development")]
for k, lab in OPX:
    Z_.add(k, lab, "EGP", lambda c, i, k=k: f"={SY(k, c)}", color=GREEN)
Z_.add("opex", "Total operating expenses", "EGP", lambda c, i: f"={SY('opex', c)}", bold=True, color=GREEN, border=TOP)
Z_.add("opexpct", "Operating expenses as % of revenue", "%", lambda c, i: f"=IFERROR({c}{Z_.R['opex']}/{SY('rev', c)},0)", PCT)
OHR = Z_.R

# ───────────── INCOME STATEMENT ─────────────
inc = ann_sheet("Income Statement", "Projected Income Statement", "Years ending 31 December · EGP · selected operating scenario (see Assumptions).")
I_ = Rows(inc)
I_.sec("Revenue")
for k, lab in [("comm", "Commission"), ("sub", "Subscriptions"), ("mrec", "Restaurant marketing — recurring packages"), ("mone", "Restaurant marketing — one-time campaigns"), ("spon", "Brand sponsorships")]:
    I_.add(k, lab, "EGP", lambda c, i, k=k: f"={SY(k, c)}", color=GREEN)
I_.add("rev", "Total revenue", "EGP", lambda c, i: f"=SUM({c}{I_.R['comm']}:{c}{I_.R['spon']})", bold=True, border=TOP)
I_.add("growth", "Revenue growth", "%", lambda c, i: "=0" if i == 0 else f"=IFERROR({c}{I_.R['rev']}/{L(2+i)}{I_.R['rev']}-1,0)", PCT)
I_.add("cogs", "Direct costs", "EGP", lambda c, i: f"=-{SY('cogs', c)}", color=GREEN)
I_.add("gp", "Gross profit", "EGP", lambda c, i: f"={c}{I_.R['rev']}+{c}{I_.R['cogs']}", bold=True, border=TOP)
I_.add("gm", "Gross margin", "%", lambda c, i: f"=IFERROR({c}{I_.R['gp']}/{c}{I_.R['rev']},0)", PCT)
I_.sec("Operating expenses")
GRP = [("x_tech", "Technology & product development", ["sal_eng", "sal_prod"]), ("x_sales", "Sales & business development", ["sal_sales", "o_cons"]),
       ("x_onb", "Restaurant onboarding & support", ["sal_supp", "o_onb"]), ("x_mkt", "Marketing", ["sal_mkt", "o_perf", "o_brand"]),
       ("x_adm", "Administration & management", ["sal_adm", "o_ga"]), ("x_legal", "Legal & compliance", ["o_legal"]), ("x_exp", "Expansion & country launch", ["o_launch"]),
       ("x_bad", "Bad debt", ["o_bad"]), ("x_cap", "Capitalised development (IAS 38)", ["o_cap"])]
for k, lab, keys in GRP:
    I_.add(k, lab, "EGP", lambda c, i, keys=keys: "=-(" + "+".join(f"'Opex & Headcount'!{c}{OHR[x]}" for x in keys) + ")", color=GREEN)
I_.add("opex", "Total operating expenses", "EGP", lambda c, i: f"=SUM({c}{I_.R['x_tech']}:{c}{I_.R['x_cap']})", bold=True, border=TOP)
I_.add("ebitda", "EBITDA", "EGP", lambda c, i: f"={c}{I_.R['gp']}+{c}{I_.R['opex']}", bold=True, border=TOP, note_="Earnings before interest, tax, depreciation and amortisation.")
I_.add("em", "EBITDA margin", "%", lambda c, i: f"=IFERROR({c}{I_.R['ebitda']}/{c}{I_.R['rev']},0)", PCT)
I_.add("dep", "Depreciation", "EGP", lambda c, i: f"=-{SY('dep', c)}", color=GREEN)
I_.add("amort", "Amortisation of capitalised software", "EGP", lambda c, i: f"=-{SY('amort', c)}", color=GREEN)
I_.add("ebit", "Operating profit (EBIT)", "EGP", lambda c, i: f"={c}{I_.R['ebitda']}+{c}{I_.R['dep']}+{c}{I_.R['amort']}", bold=True, border=TOP)
I_.add("int", "Interest income", "EGP", lambda c, i: f"={SY('int', c)}", color=GREEN)
I_.add("pbt", "Profit before tax", "EGP", lambda c, i: f"={c}{I_.R['ebit']}+{c}{I_.R['int']}", bold=True, border=TOP)
I_.add("tax", "Corporate income tax", "EGP", lambda c, i: f"=-{SY('tax', c)}", color=GREEN, note_="22.5% after tax losses carried forward.")
I_.add("ni", "Net profit", "EGP", lambda c, i: f"={c}{I_.R['pbt']}+{c}{I_.R['tax']}", bold=True, border=DTOP)
I_.add("nm", "Net margin", "%", lambda c, i: f"=IFERROR({c}{I_.R['ni']}/{c}{I_.R['rev']},0)", PCT)
I_.blank()
I_.add("rev_usd", "Total revenue (USD)", "USD", lambda c, i: f"={c}{I_.R['rev']}/{FXY(c)}", USD)
I_.add("ebitda_usd", "EBITDA (USD)", "USD", lambda c, i: f"={c}{I_.R['ebitda']}/{FXY(c)}", USD)
I_.add("ni_usd", "Net profit (USD)", "USD", lambda c, i: f"={c}{I_.R['ni']}/{FXY(c)}", USD)
ISR = I_.R

# ───────────── BALANCE SHEET ─────────────
bs = ann_sheet("Balance Sheet", "Projected Balance Sheet", "As at 31 December · EGP · selected scenario. Opening = 31 Dec 2026 (Opening BS sheet).", opening=True)
B_ = Rows(bs, opening=True)
B_.sec("Assets")
for k, lab in [("bs_cash", "Cash"), ("bs_ar", "Accounts receivable"), ("bs_eq", "Equipment, net"), ("bs_sw", "Capitalised software, net")]:
    B_.add(k, lab, "EGP", lambda c, i, k=k: f"={EY(k, c)}", color=GREEN, opening=f"={OY(k)}")
B_.add("ta", "Total assets", "EGP", lambda c, i: f"=SUM({c}{B_.R['bs_cash']}:{c}{B_.R['bs_sw']})", bold=True, border=TOP, opening=f"=SUM(C{B_.R['bs_cash']}:C{B_.R['bs_sw']})")
B_.sec("Liabilities")
for k, lab in [("bs_ap", "Accounts payable"), ("bs_tax", "Corporate tax payable"), ("bs_sl", "Shareholder loans")]:
    B_.add(k, lab, "EGP", lambda c, i, k=k: f"={EY(k, c)}", color=GREEN, opening=f"={OY(k)}")
B_.add("tl", "Total liabilities", "EGP", lambda c, i: f"=SUM({c}{B_.R['bs_ap']}:{c}{B_.R['bs_sl']})", bold=True, border=TOP, opening=f"=SUM(C{B_.R['bs_ap']}:C{B_.R['bs_sl']})")
B_.sec("Equity")
for k, lab in [("bs_pic", "Paid-in capital"), ("bs_re", "Retained earnings")]:
    B_.add(k, lab, "EGP", lambda c, i, k=k: f"={EY(k, c)}", color=GREEN, opening=f"={OY(k)}")
B_.add("te", "Total equity", "EGP", lambda c, i: f"={c}{B_.R['bs_pic']}+{c}{B_.R['bs_re']}", bold=True, border=TOP, opening=f"=C{B_.R['bs_pic']}+C{B_.R['bs_re']}")
B_.add("tle", "Total liabilities & equity", "EGP", lambda c, i: f"={c}{B_.R['tl']}+{c}{B_.R['te']}", bold=True, border=DTOP, opening=f"=C{B_.R['tl']}+C{B_.R['te']}")
B_.blank()
B_.add("chk", "Balance check (must be 0)", "EGP", lambda c, i: f"=ROUND({c}{B_.R['ta']}-{c}{B_.R['tle']},0)", bold=True, opening=f"=ROUND(C{B_.R['ta']}-C{B_.R['tle']},0)", fill=TFILL)
BSR = B_.R

# ───────────── CASH FLOW ─────────────
cf = ann_sheet("Cash Flow", "Projected Cash Flow Statement", "Years ending 31 December · EGP · indirect method · selected scenario.")
C_ = Rows(cf)
C_.sec("Operating activities")
for k, lab in [("cf_ni", "Net profit"), ("cf_da", "Depreciation & amortisation"), ("cf_ar", "Change in receivables"), ("cf_ap", "Change in payables"), ("cf_tax", "Change in tax payable (tax expense less tax paid)")]:
    C_.add(k, lab, "EGP", lambda c, i, k=k: f"={SY(k, c)}", color=GREEN)
C_.add("cfo", "Cash from operating activities", "EGP", lambda c, i: f"=SUM({c}{C_.R['cf_ni']}:{c}{C_.R['cf_tax']})", bold=True, border=TOP)
C_.add("taxpaid", "Memo: corporate tax actually paid", "EGP", lambda c, i: f"={SY('taxpaid', c)}", color=GREEN, note_="Annual tax is paid in April of the following year.")
C_.sec("Investing activities")
C_.add("cf_capex", "Equipment capex", "EGP", lambda c, i: f"={SY('cf_capex', c)}", color=GREEN)
C_.add("cf_capsw", "Capitalised development", "EGP", lambda c, i: f"={SY('cf_capsw', c)}", color=GREEN)
C_.add("cfi", "Cash from investing activities", "EGP", lambda c, i: f"={c}{C_.R['cf_capex']}+{c}{C_.R['cf_capsw']}", bold=True, border=TOP)
C_.sec("Financing activities")
C_.add("cf_eq", "Equity raised", "EGP", lambda c, i: f"={SY('cf_eq', c)}", color=GREEN)
C_.add("cf_add", "Additional financing", "EGP", lambda c, i: f"={SY('cf_add', c)}", color=GREEN)
C_.add("cff", "Cash from financing activities", "EGP", lambda c, i: f"={c}{C_.R['cf_eq']}+{c}{C_.R['cf_add']}", bold=True, border=TOP)
C_.blank()
C_.add("net", "Net change in cash", "EGP", lambda c, i: f"={c}{C_.R['cfo']}+{c}{C_.R['cfi']}+{c}{C_.R['cff']}", bold=True)
C_.add("open", "Opening cash", "EGP", lambda c, i: f"='Balance Sheet'!{L(3+i)}{BSR['bs_cash']}", color=GREEN)
C_.add("close", "Closing cash", "EGP", lambda c, i: f"={c}{C_.R['open']}+{c}{C_.R['net']}", bold=True, border=DTOP)
C_.add("chk", "Check: closing cash − balance sheet cash (must be 0)", "EGP", lambda c, i: f"=ROUND({c}{C_.R['close']}-'Balance Sheet'!{L(4+i)}{BSR['bs_cash']},0)", fill=TFILL)
C_.add("fcf", "Free cash flow (operating + investing)", "EGP", lambda c, i: f"={c}{C_.R['cfo']}+{c}{C_.R['cfi']}", bold=True)
CFR = C_.R

# ═════════════ PART 4 — runway, unit economics, funding, cap table, valuation, sensitivities, registers, checks, dashboard ═════════════
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.worksheet.datavalidation import DataValidation
def ER(scn, key):   # full 60-month range of an engine row
    sn, R = ENG[scn]; return f"{sn}!${FIRST}${R[key]}:${LAST}${R[key]}"
def SELR(key):      # selected-scenario MIN/aggregations need CHOOSE over ranges
    return lambda fn: "CHOOSE(" + A["scen"] + "," + ",".join(f"{fn}({ER(s, key)})" for s in ["Downside", "Base", "Upside"]) + ")"
LBL = f"Engine_Base!${FIRST}$7:${LAST}$7"
FX27 = "FX!$C$5"
ISn, BSn, CFn, RVn, OHn = "'Income Statement'", "'Balance Sheet'", "'Cash Flow'", "'Revenue & Monetization'", "'Opex & Headcount'"
def lbl_row(ws, r, label, unit="", bold=False):
    ws.cell(r, 1, label).font = fnt(bold=bold); ws.cell(r, 2, unit).font = fnt("5A675F", size=9)

# ───────────── MONTHLY CASH & RUNWAY ─────────────
mr = new_sheet("Monthly Cash & Runway", "Monthly Cash & Runway (60 months)", "Selected operating & funding scenario. First 24 months shaded. SHORTFALL = cash below the minimum buffer.", (12, 12, 14, 15, 15, 15, 15, 15, 15, 15, 16, 16, 12))
r = 4; sec(mr, r, "RUNWAY SUMMARY", 13)
MRS = {}
def ms_line(key, label, f, fmt=EGP, unit="EGP"):
    global r
    r += 1; mr.cell(r, 1, label).font = fnt(); mr.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    mr.cell(r, 5, unit).font = fnt("5A675F", size=9); put(mr, r, 6, f, fmt, bold=True); MRS[key] = f"'Monthly Cash & Runway'!$F${r}"
T0 = 18; T1 = T0 + NM   # table rows (header at T0)
colmap = {"m": 1, "lab": 2, "live": 3, "rev": 4, "cogs": 5, "opex": 6, "ebitda": 7, "cfo": 8, "cfi": 9, "cff": 10, "cash": 11, "precash": 12, "flag": 13}
def tcol(k): return L(colmap[k])
ms_line("mincash", "Lowest month-end cash (after funding)", f"=MIN({tcol('cash')}{T0+1}:{tcol('cash')}{T1})")
ms_line("minmonth", "Month of lowest cash", f"=INDEX({tcol('lab')}{T0+1}:{tcol('lab')}{T1},MATCH({MRS['mincash'].split('!')[1]},{tcol('cash')}{T0+1}:{tcol('cash')}{T1},0))", GEN, "")
ms_line("minpre", "Lowest cash before any new financing", f"=MIN({tcol('precash')}{T0+1}:{tcol('precash')}{T1})")
ms_line("peak", "Peak funding need to stay above buffer (no raise)", f"=MAX(0,{A['minbuf']}-{MRS['minpre'].split('!')[1]})")
ms_line("peakusd", "Peak funding need (USD at 2027 FX)", f"={MRS['peak'].split('!')[1]}/{FX27}", USD, "USD")
ms_line("short", "Months with SHORTFALL flag", f'=COUNTIF({tcol("flag")}{T0+1}:{tcol("flag")}{T1},"SHORTFALL")', NUM, "months")
ms_line("be", "First month EBITDA-positive", f'=IFERROR(INDEX({LBL},MATCH(1,CHOOSE({A["scen"]},{ER("Downside","pos")},{ER("Base","pos")},{ER("Upside","pos")}),0)),"Not within 60 months")', GEN, "")
ms_line("neg", "Months with negative operating + investing cash flow", f'=COUNTIF({tcol("cfo")}{T0+1}:{tcol("cfo")}{T1},"<0")', NUM, "months")
ms_line("cash24", "Cash at month 24 (Dec 2028)", f"={tcol('cash')}{T0+24}")
note(mr, r + 1, 1, "Funding scenario changes cash only; it does not change the operating plan. Use 'Funding Scenarios' to compare A / B / C side by side.")
hdr(mr, T0, ["Month #", "Month", "Live rest.", "Revenue", "Direct costs", "Opex", "EBITDA", "Operating CF", "Investing CF", "Financing CF", "Closing cash", "Cash pre-financing", "Flag"])
for m in range(1, NM + 1):
    rr = T0 + m
    put(mr, rr, 1, m, GEN); put(mr, rr, 2, f"=Engine_Base!{mc(m)}$7", GEN, GREEN)
    for k in ["live", "rev", "cogs", "opex", "ebitda", "cfo", "cfi", "cff", "cash", "precash"]:
        f = MS(k, m)
        if k in ("cogs", "opex"): f = "-" + f
        put(mr, rr, colmap[k], "=" + f, NUM if k == "live" else EGP, GREEN, bold=(k == "cash"))
    put(mr, rr, 13, f'=IF({tcol("cash")}{rr}<{A["minbuf"]},"SHORTFALL","ok")', GEN)
    if m <= 24:
        for cc in range(1, 14): mr.cell(rr, cc).fill = TFILL
mr.conditional_formatting.add(f"M{T0+1}:M{T1}", __import__("openpyxl").formatting.rule.CellIsRule(operator="equal", formula=['"SHORTFALL"'], fill=RFILL, font=fnt("B00020", True)))
mr.freeze_panes = f"C{T0+1}"
# fix the 'be' formula (remove helper artefact)
for row_ in mr.iter_rows(min_row=5, max_row=16, min_col=6, max_col=6):
    for c in row_:
        if isinstance(c.value, str) and "MATCH(1," in c.value:
            c.value = f'=IFERROR(INDEX({LBL},MATCH(1,CHOOSE({A["scen"]},{ER("Downside","pos")},{ER("Base","pos")},{ER("Upside","pos")}),0)),"Not within 60 months")'

# ───────────── UNIT ECONOMICS ─────────────
ue = ann_sheet("Unit Economics", "Restaurant Unit Economics", "Selected scenario. CAC covers restaurant acquisition only; diner-side brand marketing is shown separately and excluded.")
U_ = Rows(ue)
U_.sec("Acquisition")
U_.add("new", "New restaurants live", "#", lambda c, i: f"={SY('new', c)}", NUM, color=GREEN)
U_.add("acq_sal", "Sales & BD salaries", "EGP", lambda c, i: f"={SY('sal_sales', c)}", color=GREEN)
U_.add("acq_cons", "Hospitality-consultant fees", "EGP", lambda c, i: f"={SY('o_cons', c)}", color=GREEN)
U_.add("acq_onb", "Onboarding (training, setup)", "EGP", lambda c, i: f"={SY('o_onb', c)}", color=GREEN)
U_.add("acq_mkt", "Restaurant-acquisition marketing", "EGP", lambda c, i: f"={SY('o_perf', c)}", color=GREEN)
U_.add("acq", "Total acquisition spend", "EGP", lambda c, i: f"=SUM({c}{U_.R['acq_sal']}:{c}{U_.R['acq_mkt']})", bold=True, border=TOP)
U_.add("cac", "Restaurant CAC — acquisition only (projected)", "EGP", lambda c, i: f"=IFERROR({c}{U_.R['acq']}/{c}{U_.R['new']},0)", bold=True)
U_.add("brand", "Brand & consumer (diner) marketing", "EGP", lambda c, i: f"={SY('o_brand', c)}", color=GREEN)
U_.add("cac_mp", "Marketplace CAC — incl. diner marketing, per new restaurant (projected)", "EGP", lambda c, i: f"=IFERROR(({c}{U_.R['acq']}+{c}{U_.R['brand']})/{c}{U_.R['new']},0)", bold=True, note_="Two-sided view: a restaurant only stays if diners come, so diner marketing is part of the full cost.")
U_.sec("Revenue & contribution per restaurant (monthly)")
U_.add("avglive", "Average live restaurants", "#", lambda c, i: f"={RVn}!{c}{RVR['avglive']}", NUM, color=GREEN)
U_.add("arpa", "ARPA — revenue per live restaurant (excl. sponsorships)", "EGP / mo", lambda c, i: f"=IFERROR(({SY('rev', c)}-{SY('spon', c)})/{c}{U_.R['avglive']}/12,0)", bold=True)
U_.add("vcost", "Direct cost per restaurant (excl. sponsorship delivery)", "EGP / mo", lambda c, i: f"=IFERROR(({SY('cogs', c)}-{SY('c_spon', c)})/{c}{U_.R['avglive']}/12,0)")
U_.add("supp", "Support & success cost per restaurant", "EGP / mo", lambda c, i: f"=IFERROR({SY('sal_supp', c)}/{c}{U_.R['avglive']}/12,0)")
U_.add("contrib", "Contribution per restaurant", "EGP / mo", lambda c, i: f"={c}{U_.R['arpa']}-{c}{U_.R['vcost']}-{c}{U_.R['supp']}", bold=True, border=TOP)
U_.add("cm", "Contribution margin", "%", lambda c, i: f"=IFERROR({c}{U_.R['contrib']}/{c}{U_.R['arpa']},0)", PCT)
U_.sec("Retention & lifetime value")
U_.add("churn", "Monthly restaurant churn", "%", lambda c, i: f"={SEL('churn')}", PCT, color=GREEN)
U_.add("ret", "Annual restaurant retention", "%", lambda c, i: f"=(1-{c}{U_.R['churn']})^12", PCT)
U_.add("life", "Expected lifetime (1 ÷ churn, capped at 36)", "months", lambda c, i: f"=MIN(36,1/{c}{U_.R['churn']})", NUM)
U_.add("ltv", "LTV — contribution × lifetime, undiscounted (projected)", "EGP", lambda c, i: f"={c}{U_.R['contrib']}*{c}{U_.R['life']}", bold=True)
U_.add("ltvcac", "LTV / restaurant CAC (projected, not historical)", "x", lambda c, i: f"=IFERROR({c}{U_.R['ltv']}/{c}{U_.R['cac']},0)", X, True, note_="Rule of thumb: above 3x is healthy. Untested — no cohort data yet.")
U_.add("ltvcac_mp", "LTV / marketplace CAC (projected, not historical)", "x", lambda c, i: f"=IFERROR({c}{U_.R['ltv']}/{c}{U_.R['cac_mp']},0)", X, True)
U_.add("payback", "Restaurant CAC payback (projected)", "months", lambda c, i: f"=IFERROR({c}{U_.R['cac']}/{c}{U_.R['contrib']},0)", DEC2, note_="Months of contribution to recover CAC.")
U_.add("nrr", "Net revenue retention (approx.)", "%", lambda c, i: "" if i == 0 else f"=IFERROR({c}{U_.R['ret']}*{c}{U_.R['arpa']}/{L(2+i)}{U_.R['arpa']},0)", PCT, note_="Retention × ARPA growth. Approximation; needs cohort data.")
U_.sec("Monetisation & adoption")
U_.add("take", "Take rate (revenue ÷ completed GMV)", "%", lambda c, i: f"={RVn}!{c}{RVR['take']}", PCT, color=GREEN)
U_.add("paysh", "Live restaurants paying a subscription (year end)", "%", lambda c, i: f"=IFERROR({RVn}!{c}{RVR['payingend']}/{RVn}!{c}{RVR['live']},0)", PCT)
U_.add("mktad", "Live restaurants on a marketing package (year end)", "%", lambda c, i: "=0", PCT)
U_.add("gm", "Gross margin — total", "%", lambda c, i: f"={ISn}!{c}{ISR['gm']}", PCT, color=GREEN)
U_.sec("Burn & runway")
U_.add("burn", "Average monthly net burn", "EGP / mo", lambda c, i: f"={SY('burn', c)}/12")
U_.add("spend", "Average monthly gross spend (direct costs + opex + capex)", "EGP / mo", lambda c, i: f"=({SY('cogs', c)}+{SY('opex', c)}+{SY('capex', c)}+{SY('capsw', c)})/12")
U_.add("cashye", "Cash at year end", "EGP", lambda c, i: f"={BSn}!{L(4+i)}{BSR['bs_cash']}", color=GREEN)
U_.add("runway", "Runway at zero revenue (cash ÷ gross spend)", "months", lambda c, i: f"=IFERROR({c}{U_.R['cashye']}/{c}{U_.R['spend']},0)", DEC2, True)
UER = U_.R
# marketing-adoption row: rebuild from revenue sheet package counts
pk = [k for k in RVR if k.startswith("pk_")]
for i, yc in enumerate(YC):
    rows_ = [RVR[k] for k in RVR if k in ("bronze", "silver", "gold")]
ue.cell(UER["mktad"], 1).value = "Live restaurants on a marketing package (year end)"
_rv = wb["Revenue & Monetization"]
pk_rows = [rr for rr in range(5, _rv.max_row + 1) if str(_rv.cell(rr, 1).value or "").startswith("Active ") and "packages at year end" in str(_rv.cell(rr, 1).value)]
for i, yc in enumerate(YC):
    ue.cell(UER["mktad"], 3 + i).value = "=IFERROR((" + "+".join(f"{RVn}!{yc}{p}" for p in pk_rows) + f")/{RVn}!{yc}{RVR['live']},0)"

# ───────────── FUNDING SCENARIOS ─────────────
fs = new_sheet("Funding Scenarios", "Funding Scenarios A / B / C", "Same operating plan in all three; only the cash raised differs. Selected operating scenario + downside shown.", (56, 12, 18, 18, 18, 4, 60))
r = 4; hdr(fs, r, ["", "Unit", "A", "B", "C", "", "Notes"])
FR = {}
def frow(key, label, unit, fn, fmt=USD, bold=False, color=BLACK, n=None, fill=None):
    global r
    r += 1; FR[key] = r; lbl_row(fs, r, label, unit, bold)
    for j in range(3):
        put(fs, r, 3 + j, fn(L(3 + j), j), fmt, color, bold, fill=fill)
    if n: note(fs, r, 7, n)
def fsec(t):
    global r
    r += 1; sec(fs, r, t, 7)
fsec("Round terms")
frow("raise", "Total round size (investment received)", "USD", lambda c, j: f"=Assumptions!{c}{AR['raise']}", color=GREEN, bold=True)
frow("inv", "Number of investors in the round", "#", lambda c, j: f"=Assumptions!{c}{AR['n_inv']}", NUM, color=GREEN)
frow("pre", "Pre-money valuation (negotiation target)", "USD", lambda c, j: f"={A['premoney']}", color=GREEN)
frow("post", "Post-money valuation", "USD", lambda c, j: f"={c}{FR['pre']}+{c}{FR['raise']}", bold=True)
frow("own", "New investors' ownership", "%", lambda c, j: f"={c}{FR['raise']}/{c}{FR['post']}", PCT, True)
frow("pool", "Option pool (post-money)", "%", lambda c, j: f"={A['pool']}", PCT, color=GREEN)
frow("fnd", "Founders' ownership after round", "%", lambda c, j: f"=1-{c}{FR['own']}-{c}{FR['pool']}", PCT, True)
frow("dil", "Founder dilution in this round", "%", lambda c, j: f"=1-{c}{FR['fnd']}", PCT)
frow("perinv", "Individual investor ticket (round ÷ investors)", "USD", lambda c, j: f"={c}{FR['raise']}/{c}{FR['inv']}", n="Target investors write $100K–$150K each; C is two tickets, not one.")
frow("perown", "Ownership per individual investor", "%", lambda c, j: f"={c}{FR['own']}/{c}{FR['inv']}", PCT)
fsec("Cash & runway — selected operating scenario")
frow("egp", "Amount raised in EGP", "EGP", lambda c, j: f"={c}{FR['raise']}*{FX27}", EGP)
frow("open", "Opening cash (31 Dec 2026)", "EGP", lambda c, j: f"={OBS('b_cash')}", EGP, color=GREEN)
frow("avail", "Cash available after the round", "EGP", lambda c, j: f"={c}{FR['open']}+{c}{FR['egp']}", EGP, True)
frow("minpre", "Lowest cash before financing (60 months)", "EGP", lambda c, j: f"={SELR('precash')('MIN')}", EGP, n="Cumulative operating + investing cash flow from opening cash.")
frow("mincash", "Lowest cash after the round", "EGP", lambda c, j: f"={c}{FR['minpre']}+{c}{FR['egp']}", EGP, True)
frow("below", "Months below the minimum buffer", "months", lambda c, j: "=SUMPRODUCT(--(" + f"CHOOSE({A['scen']},{ER('Downside','precash')},{ER('Base','precash')},{ER('Upside','precash')})+{c}{FR['egp']}<{A['minbuf']}))", NUM)
frow("burn12", "Average monthly gross spend, first 12 months", "EGP", lambda c, j: "=(" + "+".join(f"SUM(CHOOSE({A['scen']},{ENG['Downside'][0]}!$D${ENG['Downside'][1][k]}:$O${ENG['Downside'][1][k]},{ENG['Base'][0]}!$D${ENG['Base'][1][k]}:$O${ENG['Base'][1][k]},{ENG['Upside'][0]}!$D${ENG['Upside'][1][k]}:$O${ENG['Upside'][1][k]}))" for k in ["cogs", "opex", "capex", "capsw"]) + ")/12", EGP)
frow("runway0", "Runway with zero revenue", "months", lambda c, j: f"=IFERROR({c}{FR['avail']}/{c}{FR['burn12']},0)", DEC2, True, n="Stress test: months the round alone pays for the 2027 cost base.")
frow("need", "Additional financing needed to hold the buffer", "EGP", lambda c, j: f"=MAX(0,{A['minbuf']}-{c}{FR['mincash']})", EGP, True)
frow("needusd", "Additional financing needed", "USD", lambda c, j: f"={c}{FR['need']}/{FX27}")
fsec("Cash & runway — downside operating scenario (stress)")
frow("d_minpre", "Lowest cash before financing — downside", "EGP", lambda c, j: f"=MIN({ER('Downside','precash')})", EGP)
frow("d_mincash", "Lowest cash after the round — downside", "EGP", lambda c, j: f"={c}{FR['d_minpre']}+{c}{FR['egp']}", EGP, True)
frow("d_below", "Months below buffer — downside", "months", lambda c, j: f"=SUMPRODUCT(--({ER('Downside','precash')}+{c}{FR['egp']}<{A['minbuf']}))", NUM)
frow("d_need", "Additional financing needed — downside", "USD", lambda c, j: f"=MAX(0,{A['minbuf']}-{c}{FR['d_mincash']})/{FX27}", USD, True)
frow("d_stress", "Lowest cash — downside AND collections delayed (stress)", "EGP", lambda c, j: f"=SUMPRODUCT(MIN({ER('Downside','precash')}+{c}{FR['egp']}-{ER('Downside','rev')}*{A['stress_days']}/30))", EGP, True, n="Every customer pays later by the stress delay (Assumptions). Conservative: commission is really settled by Kashier.")
frow("d_sneed", "Additional financing needed — downside + delayed collections", "USD", lambda c, j: f"=MAX(0,{A['minbuf']}-{c}{FR['d_stress']})/{FX27}", USD, True)
fsec("Minimum capital & verdict")
frow("mincap", "Minimum raise to hold buffer — selected scenario", "USD", lambda c, j: f"=MAX(0,{A['minbuf']}-{c}{FR['minpre']})/{FX27}", USD, True)
frow("mincapd", "Minimum raise to hold buffer — downside", "USD", lambda c, j: f"=MAX(0,{A['minbuf']}-{c}{FR['d_minpre']})/{FX27}", USD, True)
frow("verdict", "Funding verdict", "", lambda c, j: f'=IF({c}{FR["d_sneed"]}=0,"Covers plan, downside and late-payment stress",IF({c}{FR["d_need"]}=0,"Covers plan and downside; late-payment stress needs a bridge",IF({c}{FR["need"]}=0,"Covers base plan only; downside needs more","Underfunded")))', GEN, True)
SY27 = lambda key: SY(key, "C").replace("C$3", "2027")
UFN = "'Use of Funds'"
fsec("What each amount pays for (Use of Funds % × 2027 cost schedule)")
frow("f_sales", "Sales & onboarding budget", "EGP", lambda c, j: f"={UFN}!{L(2+j)}5*{c}{FR['egp']}", EGP)
frow("f_rest", "  Restaurants it can acquire at 2027 restaurant CAC", "#", lambda c, j: f"=IFERROR({c}{FR['f_sales']}/'Unit Economics'!$C${UER['cac']},0)", NUM, True)
frow("f_rest_pct", "  Share of the 2027 new-restaurant plan", "%", lambda c, j: f"=IFERROR({c}{FR['f_rest']}/'Unit Economics'!$C${UER['new']},0)", PCT)
frow("f_tech", "Product & engineering budget", "EGP", lambda c, j: f"={UFN}!{L(2+j)}6*{c}{FR['egp']}", EGP)
frow("f_eng", "  Engineer-years it pays for (2027 loaded salary)", "years", lambda c, j: f"=IFERROR({c}{FR['f_tech']}/(Assumptions!$H${HC['eng']}*12),0)", DEC2)
frow("f_mkt", "Marketing & season-launch budget", "EGP", lambda c, j: f"={UFN}!{L(2+j)}7*{c}{FR['egp']}", EGP)
frow("f_mkt_m", "  Months of the 2027 marketing plan it covers", "months", lambda c, j: f"=IFERROR({c}{FR['f_mkt']}/(({SY27('o_brand')}+{SY27('o_perf')})/12),0)", DEC2)
frow("f_ops", "Operations, legal & support budget", "EGP", lambda c, j: f"={UFN}!{L(2+j)}8*{c}{FR['egp']}", EGP)
frow("f_hc", "Headcount the whole round supports for 12 months", "people", lambda c, j: f"=IFERROR({c}{FR['egp']}/(({SY27('sal_eng')}+{SY27('sal_prod')}+{SY27('sal_sales')}+{SY27('sal_supp')}+{SY27('sal_mkt')}+{SY27('sal_adm')})/({SY27('hc')}/12)),0)", DEC2, True, n="Round ÷ average 2027 loaded cost per head. The plan has 16 people by end 2027.")
frow("f_plan", "Share of total 2027 spend (direct costs + opex + capex)", "%", lambda c, j: f"=IFERROR({c}{FR['egp']}/({c}{FR['burn12']}*12),0)", PCT)
fsec("Milestones, purpose and next round (management view — to confirm)")
MIL = ["Restaurant growth paid from revenue; thin margin for error.",
       "Full-year sales capacity for the 200-restaurant target; paid marketing packages launched.",
       "Ramadan & summer launches and Gulf partner groundwork without waiting for revenue."]
r += 1; FR["mil"] = r; lbl_row(fs, r, "Operating milestones funded", "")
for j, t in enumerate(MIL):
    cl = L(3 + j)
    c = put(fs, r, 3 + j, f'="~"&TEXT({cl}{FR["runway0"]},"0.0")&" months of 2027 costs at zero revenue; ~"&TEXT({cl}{FR["f_rest"]},"0")&" restaurants of acquisition capacity. {t}"', GEN)
    c.alignment = Alignment(wrap_text=True, vertical="top")
fs.row_dimensions[r].height = 76
PUR = ["Base case only.", "Buys time and sales capacity: the extra $50K over A is mostly sales & marketing.", "Buys resilience: the extra $150K over A covers the downside and delayed-collection stress without a bridge."]
r += 1; FR["purpose"] = r; lbl_row(fs, r, "Strategic purpose of capital above A", "")
for j, t in enumerate(PUR):
    c = put(fs, r, 3 + j, t, GEN, BLUE); c.alignment = Alignment(wrap_text=True, vertical="top")
fs.row_dimensions[r].height = 52
frow("nextfin", "Expected next financing requirement", "", lambda c, j: f'=IF({c}{FR["d_sneed"]}>0,"Bridge of ~"&TEXT({c}{FR["d_sneed"]},"$#,##0")&" in a downside with late payments; then seed "&Assumptions!$B${AR["seed"]},IF({c}{FR["d_need"]}>0,"Bridge in downside; seed "&Assumptions!$B${AR["seed"]},"No bridge needed; seed "&Assumptions!$B${AR["seed"]}&" (illustrative $"&TEXT(Assumptions!$C${AR["seed"]}/1000000,"0.0")&"M) for Gulf expansion"))', GEN, True)
fsec("Instrument options (illustrative)")
frow("safe_cap", "Post-money SAFE — ownership at valuation cap", "%", lambda c, j: f"={c}{FR['raise']}/{c}{FR['post']}", PCT, n="Cap = post-money above. Converts at the next priced round.")
frow("safe_disc", "SAFE — ownership via discount at seed price", "%", lambda c, j: f"={c}{FR['raise']}/(Assumptions!$D${AR['seed']}*(1-{A['safe_disc']})+{c}{FR['raise']})", PCT, n="Seed pre-money × (1 − discount). Investor gets the better of cap or discount.")
frow("safe_own", "SAFE — ownership on conversion (better of the two)", "%", lambda c, j: f"=MAX({c}{FR['safe_cap']},{c}{FR['safe_disc']})", PCT, True)
note(fs, r + 2, 1, "Convertible notes work like a SAFE plus interest and a maturity date. A priced round needs a shareholders' agreement and company registration of new shares; a SAFE is faster and cheaper at this ticket size.")
FSN = "'Funding Scenarios'"
def FSsel(key): return f"INDEX({FSN}!$C${FR[key]}:$E${FR[key]},{A['fundsel']})"

# ───────────── USE OF FUNDS ─────────────
uf = new_sheet("Use of Funds", "Use of Funds", "Allocation of each funding scenario. Percentages are inputs (blue) and must total 100%.", (44, 12, 12, 12, 16, 16, 16, 18, 50))
hdr(uf, 4, ["Category", "% A", "% B", "% C", "USD A", "USD B", "USD C", "EGP (selected)", "What it pays for"])
UFC = [("Sales & restaurant onboarding", [0.40, 0.38, 0.35], "Sales hires, consultants, onboarding & training"),
       ("Product & engineering", [0.30, 0.25, 0.25], "Feature roadmap, reliability, security"),
       ("Marketing & season launches", [0.15, 0.22, 0.25], "Diner demand, Ramadan/summer launches, content"),
       ("Operations, legal & support", [0.15, 0.15, 0.15], "Support team, legal, accounting, compliance")]
for i, (cat, ps, what) in enumerate(UFC):
    rr = 5 + i; uf.cell(rr, 1, cat)
    for j, p in enumerate(ps): put(uf, rr, 2 + j, p, PCT, BLUE)
    for j in range(3): put(uf, rr, 5 + j, f"={L(2+j)}{rr}*{FSN}!{L(3+j)}${FR['raise']}", USD)
    put(uf, rr, 8, f"=INDEX(B{rr}:D{rr},{A['fundsel']})*{FSsel('egp')}", EGP); note(uf, rr, 9, what)
rt = 5 + len(UFC); uf.cell(rt, 1, "Total").font = fnt(bold=True)
for cc in range(2, 9): put(uf, rt, cc, f"=SUM({L(cc)}5:{L(cc)}{rt-1})", PCT if cc <= 4 else (USD if cc <= 7 else EGP), bold=True).border = TOP
UF_TOT = rt
r = rt + 2; sec(uf, r, "CONTEXT", 9)
r += 1; uf.cell(r, 1, "Selected raise as % of 2027 total spend (direct + opex)"); put(uf, r, 8, f"=IFERROR({FSsel('egp')}/(-{ISn}!C{ISR['cogs']}-{ISn}!C{ISR['opex']}),0)", PCT, bold=True)
note(uf, r, 9, "Revenue funds the rest; the round front-loads hiring before revenue builds.")
r += 1; uf.cell(r, 1, "Months of 2027 spend covered by the selected raise"); put(uf, r, 8, f"=IFERROR({FSsel('egp')}/((-{ISn}!C{ISR['cogs']}-{ISn}!C{ISR['opex']})/12),0)", DEC2, bold=True)

# ───────────── CAP TABLE ─────────────
ctb = new_sheet("Cap Table", "Capitalisation Table (fully diluted, illustrative)", "Selected funding scenario. Seed and Series A terms are illustrative assumptions for dilution only.", (36, 16, 16, 16, 16, 4, 56))
hdr(ctb, 4, ["Holder", "Today", "After pre-seed", "After seed", "After Series A", "", "Notes"])
pre_own = FSsel("own"); pool = A["pool"]
seed_sh = f"(Assumptions!$C${AR['seed']}/(Assumptions!$C${AR['seed']}+Assumptions!$D${AR['seed']}))"
a_sh = f"(Assumptions!$C${AR['seriesA']}/(Assumptions!$C${AR['seriesA']}+Assumptions!$D${AR['seriesA']}))"
CTR = {}
holders = [("fnd", "Founders"), ("pool", "Employee option pool"), ("ps", "Pre-seed investors"), ("seed", "Seed investors"), ("a", "Series A investors")]
for i, (k, h) in enumerate(holders):
    rr = 5 + i; CTR[k] = rr; ctb.cell(rr, 1, h)
put(ctb, CTR["fnd"], 2, 1, PCT); put(ctb, CTR["pool"], 2, 0, PCT); put(ctb, CTR["ps"], 2, 0, PCT); put(ctb, CTR["seed"], 2, 0, PCT); put(ctb, CTR["a"], 2, 0, PCT)
put(ctb, CTR["fnd"], 3, f"=1-{pre_own}-{pool}", PCT); put(ctb, CTR["pool"], 3, f"={pool}", PCT); put(ctb, CTR["ps"], 3, f"={pre_own}", PCT); put(ctb, CTR["seed"], 3, 0, PCT); put(ctb, CTR["a"], 3, 0, PCT)
for k in ["fnd", "pool", "ps"]: put(ctb, CTR[k], 4, f"=C{CTR[k]}*(1-{seed_sh})", PCT)
put(ctb, CTR["seed"], 4, f"={seed_sh}", PCT); put(ctb, CTR["a"], 4, 0, PCT)
for k in ["fnd", "pool", "ps", "seed"]: put(ctb, CTR[k], 5, f"=D{CTR[k]}*(1-{a_sh})", PCT)
put(ctb, CTR["a"], 5, f"={a_sh}", PCT)
rt = 5 + len(holders); ctb.cell(rt, 1, "Total (must be 100%)").font = fnt(bold=True); CTR["tot"] = rt
for cc in range(2, 6): put(ctb, rt, cc, f"=SUM({L(cc)}5:{L(cc)}{rt-1})", PCT, bold=True).border = TOP
r = rt + 2; sec(ctb, r, "ROUND VALUES (USD)", 7)
r += 1; ctb.cell(r, 1, "Post-money valuation"); put(ctb, r, 3, f"={FSsel('post')}", USD, GREEN)
put(ctb, r, 4, f"=Assumptions!$C${AR['seed']}+Assumptions!$D${AR['seed']}", USD); put(ctb, r, 5, f"=Assumptions!$C${AR['seriesA']}+Assumptions!$D${AR['seriesA']}", USD); CTR["postv"] = r
r += 1; ctb.cell(r, 1, "Value of pre-seed stake"); [put(ctb, r, cc, f"={L(cc)}{CTR['ps']}*{L(cc)}{CTR['postv']}", USD) for cc in (3, 4, 5)]; CTR["psv"] = r
r += 1; ctb.cell(r, 1, "Pre-seed paper multiple (ILLUSTRATIVE)"); [put(ctb, r, cc, f"=IFERROR({L(cc)}{CTR['psv']}/{FSsel('raise')},0)", X, bold=True) for cc in (3, 4, 5)]
r += 1; ctb.cell(r, 1, "Value of founders' stake"); [put(ctb, r, cc, f"={L(cc)}{CTR['fnd']}*{L(cc)}{CTR['postv']}", USD) for cc in (3, 4, 5)]
r += 2; sec(ctb, r, "PRE-SEED OWNERSHIP BY FUNDING SCENARIO", 7)
r += 1; hdr(ctb, r, ["", "A", "B", "C"])
for lab, f in [("After pre-seed", lambda c: f"={FSN}!{c}{FR['own']}"), ("After seed", lambda c: f"={FSN}!{c}{FR['own']}*(1-{seed_sh})"), ("After Series A", lambda c: f"={FSN}!{c}{FR['own']}*(1-{seed_sh})*(1-{a_sh})")]:
    r += 1; ctb.cell(r, 1, lab)
    for j in range(3): put(ctb, r, 2 + j, f(L(3 + j)), PCT)
r += 1; ctb.cell(r, 1, "Founders after Series A")
for j in range(3): put(ctb, r, 2 + j, f"={FSN}!{L(3+j)}{FR['fnd']}*(1-{seed_sh})*(1-{a_sh})", PCT)
note(ctb, r + 2, 1, "Option pool assumed created before the pre-seed (dilutes founders only) and not topped up later. Future rounds are illustrative, not commitments.")

# ───────────── DUE-DILIGENCE / EVIDENCE LIST (data; sheet built later) ─────────────
DDI = [  # (key, item, area, why, priority, linked input / sheet, impact if missing)
 ("reg", "Company registration, articles, shareholder register", "Legal", "Who owns the company today", "High", "Cap Table", "Round cannot close"),
 ("ip", "IP assignment from founders and every developer / contractor", "IP", "The company must own the code it sells", "Critical", "Asset Register A1–A6", "Valuation unsupported; deal blocker"),
 ("repo", "Source-code repositories held in a company account, access list", "IP", "Control of the core asset", "Critical", "Asset Register A6", "Key-person and IP risk"),
 ("dom", "Domain reservya.com and app-store developer accounts in the company's name", "IP", "Control of distribution", "High", "Asset Register A5", "Product can be lost with one person"),
 ("tm", "Trademark filing for Reservya (Egypt, later GCC)", "IP", "Brand protection", "Medium", "Asset Register A4", "Rebrand risk"),
 ("bank", "Bank statements and receipts for the EGP 2.7M invested", "Finance", "Reconciles the opening balance sheet", "Critical", "Opening BS", "Opening equity unsupported"),
 ("loan", "Founder contribution: equity or loan, in writing", "Finance", "Changes balance sheet and cap table", "High", "Opening BS", "Hidden liability"),
 ("sw", "Software spend EGP 1.65M: invoices, payroll, contracts", "Finance", "Historical cost of the technology", "High", "Asset Register reconciliation", "Asset value unsupported"),
 ("ias", "IAS 38 documentation (feasibility, timesheets) for future capitalisation", "Accounting", "Needed before capitalising any development", "Medium", "Assumptions: capitalised share", "Set capitalisation to 0%"),
 ("live", "Live restaurant count at 31 Dec 2026 with signed agreements", "Traction", "Opening restaurants and traction claim", "Critical", "Assumptions: current traction", "Forecast starts from an unproven base"),
 ("bills", "Monthly completed bills per restaurant (Kashier reports) — tests 125/month", "Traction", "Largest revenue driver", "Critical", "Assumptions: bills per restaurant", "−20% bills ≈ −15% revenue"),
 ("activ", "Share of live restaurants transacting each month — tests 90%", "Traction", "Revenue driver", "High", "Assumptions: activation", "Lower commission"),
 ("churn", "Restaurant churn history — tests 1.5% a month", "Traction", "Retention and CAC", "High", "Assumptions: churn", "Higher acquisition cost"),
 ("bill", "Average completed bill — tests EGP 3,000", "Traction", "Revenue driver", "High", "Countries: average bill", "Lower commission"),
 ("rate", "Commission rates in signed restaurant contracts — tests 5.5% tier mix", "Commercial", "Revenue driver", "Critical", "Assumptions: tier mix", "4% case: ≈ −20% revenue"),
 ("conv", "Restaurants on paid plans — tests 70% conversion", "Commercial", "Subscription revenue", "High", "Assumptions: plan mix", "Lower recurring revenue"),
 ("mkt", "Marketing packages sold to date — tests adoption", "Commercial", "Marketing revenue", "Medium", "Assumptions: package adoption", "Lower marketing revenue"),
 ("spon", "Sponsorship LOIs or contracts", "Commercial", "Sponsorship revenue", "Medium", "Assumptions: sponsorships", "Sponsorship revenue falls to 0"),
 ("kash", "Kashier merchant agreement and fee pass-through terms", "Commercial", "Payment flow and costs", "High", "Revenue & Monetization", "Fees may become Reservya's cost"),
 ("cons", "Hospitality-consultant agreements and fee terms", "Commercial", "Acquisition cost", "Medium", "Assumptions: consultant fee", "Higher CAC"),
 ("team", "Team list, roles, contracts, vesting", "People", "Key-person risk and option pool", "High", "Opex & Headcount", "Team claim unsupported"),
 ("pay", "Payroll and supplier costs 2025–2026", "Finance", "Validates the cost base", "Medium", "Opex & Headcount", "Costs may be understated"),
 ("dp", "Data-protection compliance (Law 151/2020), privacy policy", "Legal", "Diner data is a core asset", "Medium", "Asset Register D2", "Regulatory risk"),
 ("tax", "Tax registration, VAT status, losses carried forward", "Tax", "Tax schedule", "Medium", "Assumptions: tax", "Tax timing wrong"),
 ("fx", "EGP/USD rate path agreed with investors", "Finance", "USD figures and the raise in EGP", "Medium", "FX", "USD values misstated"),
 ("prod", "Product demo, app-store ratings, uptime", "Product", "Live-product claim", "High", "Valuation", "Product readiness unsupported"),
 ("comp", "Comparable financings with sources", "Valuation", "Market support for the price", "Medium", "Valuation", "Price rests on methods only"),
 ("gulf", "Gulf operating-partner term sheets", "Expansion", "Revenue share and launch costs", "Low", "Countries", "Expansion timing at risk"),
]
DDROW = {k: 5 + i for i, (k, *_) in enumerate(DDI)}
def DDS(k): return f"'Due Diligence'!$E${DDROW[k]}"
def DDCLOSED(*ks): return "AND(" + ",".join(f'{DDS(k)}="Closed"' for k in ks) + ")"

# ───────────── VALUATION ─────────────
va = new_sheet("Valuation", "Valuation Analysis", "Four methods. Asset-based methods are deliberately not used: an early software company's value is its future cash flows, not its book assets.", (52, 14, 16, 16, 16, 4, 60))
r = 4; VA = {}
def vrow(key, label, unit, f, fmt=USD, bold=False, color=BLACK, n=None, col=3):
    global r
    r += 1; VA[key] = r; lbl_row(va, r, label, unit, bold); put(va, r, col, f, fmt, color, bold, fill=YFILL if color == BLUE else None)
    if n: note(va, r, 7, n)
sec(va, r, "1. VC METHOD (base scenario)", 7)
vrow("rev31", "2031 revenue — base scenario", "USD", f"={SYS('Base','rev','G').replace('G$3','2031')}/FX!$G$5", USD, color=GREEN)
vrow("mult", "Exit multiple (revenue)", "x", f"=Assumptions!$D${AR['exitx']}", X, color=GREEN, n="Base illustrative multiple from Assumptions.")
vrow("exit", "Exit value 2031", "USD", f"=C{VA['rev31']}*C{VA['mult']}", bold=True)
vrow("ret_m", "Target return multiple for a pre-seed investor", "x", 25, X, color=BLUE, n="Pre-seed VCs typically target 20–30x on each winner to cover losses. Judgement.")
vrow("retain", "Ownership retained after seed & Series A", "%", f"=(1-{seed_sh})*(1-{a_sh})", PCT)
vrow("vc_post", "Implied post-money today", "USD", f"=C{VA['exit']}*C{VA['retain']}/C{VA['ret_m']}")
vrow("vc_pre", "Implied pre-money today", "USD", f"=C{VA['vc_post']}-{FSsel('raise')}", USD, True)
r += 1; sec(va, r + 1, "2. FIRST CHICAGO (probability-weighted scenarios)", 7); r += 1
r += 1; hdr(va, r, ["", "Unit", "Downside", "Base", "Upside", "", "Notes"])
r += 1; VA["fc_rev"] = r; lbl_row(va, r, "2031 revenue", "USD")
for j, s in enumerate(["Downside", "Base", "Upside"]): put(va, r, 3 + j, f"={SYS(s,'rev','G').replace('G$3','2031')}/FX!$G$5", USD, GREEN)
r += 1; VA["fc_x"] = r; lbl_row(va, r, "Exit multiple", "x")
for j in range(3): put(va, r, 3 + j, f"=Assumptions!{L(3+j)}{AR['exitx']}", X, GREEN)
r += 1; VA["fc_ev"] = r; lbl_row(va, r, "Exit value", "USD")
for j in range(3): put(va, r, 3 + j, f"={L(3+j)}{VA['fc_rev']}*{L(3+j)}{VA['fc_x']}", USD)
r += 1; VA["fc_p"] = r; lbl_row(va, r, "Probability", "%")
for j in range(3): put(va, r, 3 + j, f"=Assumptions!{L(3+j)}{AR['prob']}", PCT, GREEN)
vrow("fc_w", "Probability-weighted exit value", "USD", f"=SUMPRODUCT(C{VA['fc_ev']}:E{VA['fc_ev']},C{VA['fc_p']}:E{VA['fc_p']})", bold=True)
vrow("fc_irr", "Required annual return (discount rate)", "%", 0.60, PCT, color=BLUE, n="Venture rates for pre-seed risk run 50–70%+. Judgement.")
vrow("fc_yrs", "Years to exit", "years", 5, NUM, color=BLUE)
vrow("fc_post", "Present value × ownership retained = post-money", "USD", f"=C{VA['fc_w']}/(1+C{VA['fc_irr']})^C{VA['fc_yrs']}*C{VA['retain']}")
vrow("fc_pre", "Implied pre-money today", "USD", f"=C{VA['fc_post']}-{FSsel('raise')}", USD, True)
r += 1; sec(va, r + 1, "3. RISK-ADJUSTED MILESTONE METHOD", 7); r += 1
vrow("ms_val", "Pre-money at next milestone (seed round)", "USD", f"=Assumptions!$D${AR['seed']}", USD, color=GREEN, n="Illustrative seed terms from Assumptions.")
vrow("ms_p", "Probability of reaching that milestone", "%", 0.25, PCT, color=BLUE, n="Judgement: 200 live restaurants and proven unit economics by 2028.")
vrow("ms_t", "Years to milestone", "years", 1.5, DEC2, color=BLUE)
vrow("ms_r", "Discount rate", "%", 0.40, PCT, color=BLUE)
vrow("ms_pre", "Implied pre-money today", "USD", f"=C{VA['ms_val']}*C{VA['ms_p']}/(1+C{VA['ms_r']})^C{VA['ms_t']}", USD, True)
r += 1; sec(va, r + 1, "4. MODIFIED BERKUS (qualitative drivers, not assets)", 7); r += 1
r += 1; hdr(va, r, ["Driver", "Max (USD)", "Score", "Value (USD)", "", "", "Evidence to show"])
BK = [("Market gap: dine-in has no platform", 500000, 0.60, "Market sizing sources; diner and restaurant interviews"),
      ("Live product (iOS, Android, web, payments)", 500000, 0.70, "App store links, demo, uptime"),
      ("Team that built and runs it", 500000, 0.50, "CVs, roles, vesting"),
      ("Strategic partners (Kashier, consultants)", 500000, 0.40, "Signed agreements"),
      ("Early restaurant partners (22+ tested)", 500000, 0.30, "Signed restaurant agreements, usage data")]
b0 = r + 1
for d, mx, sc_, ev in BK:
    r += 1; va.cell(r, 1, d); put(va, r, 2, mx, USD, BLUE); put(va, r, 3, sc_, PCT, BLUE); put(va, r, 4, f"=B{r}*C{r}", USD); note(va, r, 7, ev)
vrow("bk_pre", "Berkus pre-money", "USD", f"=SUM(D{b0}:D{r})", USD, True, col=4)
r += 1; sec(va, r + 1, "5. COMPARABLE FINANCINGS — enter verified data only", 7); r += 1
r += 1; hdr(va, r, ["Company", "Country", "Date", "Round", "Pre-money (USD)", "Verified? (Y/N)", "Source & verification", "Counted (USD)"])
c0 = r + 1
for k in range(6):
    r += 1
    for cc in range(1, 6): put(va, r, cc, None, USD if cc == 5 else GEN, BLUE)
    put(va, r, 6, "N", GEN, BLUE); put(va, r, 8, f'=IF(AND(F{r}="Y",ISNUMBER(E{r})),E{r},"")', USD)
    note(va, r, 7, "Count only if verified (MAGNiTT, Crunchbase, press release, term sheet) — set Y.")
c1 = r
va.column_dimensions["H"].width = 16
vrow("cmpn", "Verified comparables counted", "#", f"=COUNT(H{c0}:H{c1})", NUM)
vrow("cmp", "Median of verified comparables", "USD", f'=IF(C{VA["cmpn"]}=0,"n/a",MEDIAN(H{c0}:H{c1}))', USD, True, n="Unverified entries never count as market support.")
r += 1; sec(va, r + 1, "SUMMARY — where the $1.25M target sits against the methods", 7); r += 1
r += 1; hdr(va, r, ["Method", "", "Pre-money (USD)"])
s0 = r + 1
for lab, k in [("VC method", "vc_pre"), ("First Chicago", "fc_pre"), ("Risk-adjusted milestone", "ms_pre"), ("Modified Berkus", "bk_pre")]:
    r += 1; va.cell(r, 1, lab); put(va, r, 3, f"={'D' if k == 'bk_pre' else 'C'}{VA[k]}", USD)
r += 1; va.cell(r, 1, "Comparable financings"); put(va, r, 3, f'=IF(ISNUMBER(C{VA["cmp"]}),C{VA["cmp"]},"n/a")', USD)
s1 = r
vrow("lo", "Low", "USD", f"=MIN(C{s0}:C{s1})"); vrow("med", "Median", "USD", f"=MEDIAN(C{s0}:C{s1})", USD, True); vrow("hi", "High", "USD", f"=MAX(C{s0}:C{s1})")
vrow("tgt", "Management target pre-money", "USD", f"={A['premoney']}", USD, True, GREEN)
vrow("pos", "Position of the target", "", f'="Target = "&TEXT(C{VA["tgt"]}/C{VA["med"]},"0%")&" of the method median; "&IF(AND(C{VA["tgt"]}>=C{VA["lo"]},C{VA["tgt"]}<=C{VA["hi"]}),"inside","outside")&" the range"', GEN, True)
r += 1; sec(va, r + 1, "WHAT HAS TO BE EVIDENCED FOR THE PRICE TO HOLD", 7); r += 1
r += 1; hdr(va, r, ["Value driver", "", "Evidence status", "", "", "", "Evidence (Due Diligence items)"])
ev0 = r + 1
for lab, keys, ev in [("Product readiness (live apps, dashboard, payments)", ["prod"], "Demo, store listings, uptime"),
                      ("Intellectual property owned by the company", ["ip", "repo", "dom"], "IP assignments, repo & domain ownership"),
                      ("Team capability", ["team"], "Roles, contracts, vesting"),
                      ("Documented commercial traction", ["live", "bills", "rate"], "Signed restaurants, Kashier reports, contract rates"),
                      ("Realistic milestone execution", ["bills", "pay"], "Actual volumes and costs vs plan")]:
    r += 1; va.cell(r, 1, lab); put(va, r, 3, f'=IF({DDCLOSED(*keys)},"Evidenced","Open")', GEN, bold=True); note(va, r, 7, ev)
ev1 = r
vrow("evn", "Value drivers evidenced", "of 5", f'=COUNTIF(C{ev0}:C{ev1},"Evidenced")', NUM, True)
vrow("verdict", "Assessment", "", f'=IF(C{VA["evn"]}=5,IF(C{VA["tgt"]}<=C{VA["hi"]},"Supportable: inside the method range and evidenced","Above the method range"),"Not yet supportable: "&(5-C{VA["evn"]})&" of 5 value drivers lack evidence. The methods give a range, not proof.")', GEN, True)
r += 1; sec(va, r + 1, "SENSITIVITY — VC-method pre-money (USD) by exit multiple × target return (ILLUSTRATIVE)", 7); r += 1
r += 1; hdr(va, r, ["Exit multiple ↓ / target return →", "", "15x", "20x", "25x", "30x"])
for mx in [2, 3, 4, 5]:
    r += 1; put(va, r, 1, mx, X)
    for j, tr in enumerate([15, 20, 25, 30]):
        put(va, r, 3 + j, f"=C{VA['rev31']}*A{r}*C{VA['retain']}/{tr}-{FSsel('raise')}", USD)
r += 1; sec(va, r + 1, "TIMING & DILUTION TESTS (ILLUSTRATIVE)", 7); r += 1
vrow("t_early", "VC method if exit happens in 2030 instead of 2031", "USD", f"={SYS('Base','rev','F').replace('F$3','2030')}/FX!$F$5*C{VA['mult']}*C{VA['retain']}/C{VA['ret_m']}-{FSsel('raise')}")
for sp in [5000000, 8000000, 12000000]:
    vrow(f"t_seed{sp}", f"Pre-seed stake after Series A if seed pre-money is ${sp/1e6:.0f}M", "%", f"={FSsel('own')}*(1-Assumptions!$C${AR['seed']}/(Assumptions!$C${AR['seed']}+{sp}))*(1-{a_sh})", PCT)
vrow("t_noA", "Pre-seed stake at exit if Series A is skipped (profitable)", "%", f"={FSsel('own')}*(1-{seed_sh})", PCT)
r += 1; sec(va, r + 1, "ILLUSTRATIVE EXIT OUTCOMES — not a forecast, not a promise of returns", 7); r += 1
r += 1; hdr(va, r, ["", "Unit", "Downside", "Base", "Upside"])
r += 1; lbl_row(va, r, "Exit value 2031", "USD"); [put(va, r, 3 + j, f"={L(3+j)}{VA['fc_ev']}", USD) for j in range(3)]; ev_r = r
r += 1; lbl_row(va, r, "Pre-seed investors' stake after dilution", "%"); [put(va, r, 3 + j, f"={FSsel('own')}*C{VA['retain']}", PCT) for j in range(3)]; st_r = r
r += 1; lbl_row(va, r, "Value of pre-seed stake", "USD"); [put(va, r, 3 + j, f"={L(3+j)}{ev_r}*{L(3+j)}{st_r}", USD) for j in range(3)]; vv = r
r += 1; lbl_row(va, r, "Illustrative multiple on invested capital", "x", True); [put(va, r, 3 + j, f"=IFERROR({L(3+j)}{vv}/{FSsel('raise')},0)", X, bold=True) for j in range(3)]

# ───────────── COMMISSION SENSITIVITY ─────────────
cs = ann_sheet("Commission Sensitivity", "Commission-Rate Sensitivity", "Selected operating scenario. Commission = eligible GMV × rate × (1 − waivers). Costs that move with revenue are flexed; fixed costs held.")
S_ = Rows(cs)
CASES = [("4% conservative", A["c_cons"]), ("5.5% reference (midpoint, unverified)", A["c_ref"]), ("7% upper", A["c_up"]), ("Tier-weighted mix", A["c_tier"])]
S_.sec("Flex factor")
S_.add("k", "EBITDA kept per extra EGP of commission", "%", lambda c, i: f"=1-Assumptions!{c}{AR['brand']}-IFERROR(({SY('c_part', c)}+{SY('o_bad', c)}+{SY('c_pay', c)})/{SY('rev', c)},0)", PCT, note_="1 − brand-marketing % − partner share − bad debt − payment cost (as % of revenue).")
for blk, f in [("Commission revenue", lambda c, rate: f"={ISn}!{c}{ISR['comm']}*{rate}/{A['c_eff']}"),
               ("Total revenue", lambda c, rate: f"={ISn}!{c}{ISR['rev']}+{ISn}!{c}{ISR['comm']}*({rate}/{A['c_eff']}-1)"),
               ("EBITDA", lambda c, rate: f"={ISn}!{c}{ISR['ebitda']}+{ISn}!{c}{ISR['comm']}*({rate}/{A['c_eff']}-1)*{c}{S_.R['k']}"),
               ("EBITDA margin", None),
               ("Closing cash (approx., after 22.5% tax on the change)", lambda c, rate: None)]:
    S_.sec(blk)
    for j, (nm_, rate) in enumerate(CASES):
        key = {"Commission revenue": "cr", "Total revenue": "tr", "EBITDA": "eb", "EBITDA margin": "em"}.get(blk, "cash") + f"_{j}"
        if blk == "EBITDA margin":
            S_.add(key, nm_, "%", lambda c, i, j=j: f"=IFERROR({c}{S_.R[f'eb_{j}']}/{c}{S_.R[f'tr_{j}']},0)", PCT)
        elif blk.startswith("Closing"):
            S_.add(key, nm_, "EGP", lambda c, i, rate=rate: f"={BSn}!{L(4+i)}{BSR['bs_cash']}+SUMPRODUCT(({ISn}!$C${ISR['comm']}:{c}{ISR['comm']})*({rate}/{A['c_eff']}-1)*($C${S_.R['k']}:{c}{S_.R['k']}))*(1-{A['tax']})")
        else:
            S_.add(key, nm_, "EGP", lambda c, i, f=f, rate=rate: f(c, rate))
S_.sec("Two-way: 2031 total revenue by operating scenario × commission rate")
for s in ["Downside", "Base", "Upside"]:
    S_.add(f"tw_{s}", f"{s} — 4% / 5.5% / 7% / tier mix (cols 2027–2030 = cases; 2031 col blank)", "EGP",
           lambda c, i, s=s: (f"={SYS(s,'rev','G')}+{SYS(s,'comm','G')}*({CASES[i][1]}/{A['c_eff']}-1)" if i < 4 else ""))
for i in range(4): cs.cell(S_.r + 1, 3 + i, ["4%", "5.5%", "7%", "Tier mix"][i]).font = fnt("5A675F", italic=True, size=9)
note(cs, S_.r + 2, 1, "Two-way rows: column 2027 = 4%, 2028 = 5.5%, 2029 = 7%, 2030 = tier mix — all values are 2031 revenue. Uses SYS on the year-row of each column, so G$3 is fixed to 2031.")
CSR = S_.R

# ───────────── SCENARIO COMPARISON ─────────────
scs = ann_sheet("Scenarios", "Scenario Comparison", "Downside / Base / Upside side by side, independent of the scenario selector. Downside & upside are sensitivities on the management plan, not forecasts.")
Q_ = Rows(scs)
for title, key, kind, fmt in [("Live restaurants (year end)", "live", "E", NUM), ("Total revenue", "rev", "S", EGP), ("EBITDA", "ebitda", "S", EGP),
                              ("Net profit", "ni", "S", EGP), ("Closing cash", "cash", "E", EGP)]:
    Q_.sec(title)
    for s in ["Downside", "Base", "Upside"]:
        Q_.add(f"{key}_{s}", s, "#" if key == "live" else "EGP", lambda c, i, s=s, key=key, kind=kind: f"={(SYS if kind == 'S' else EYS)(s, key, c)}", fmt, s == "Base")
Q_.sec("EBITDA margin")
for s in ["Downside", "Base", "Upside"]:
    Q_.add(f"em_{s}", s, "%", lambda c, i, s=s: f"=IFERROR({c}{Q_.R['ebitda_'+s]}/{c}{Q_.R['rev_'+s]},0)", PCT)
Q_.sec("Over 60 months")
for s in ["Downside", "Base", "Upside"]:
    Q_.add(f"min_{s}", f"{s} — lowest month-end cash / first EBITDA-positive month", "", lambda c, i, s=s: (f"=MIN({ER(s,'cash')})" if i == 0 else (f'=IFERROR(INDEX({LBL},MATCH(1,{ER(s,"pos")},0)),"none")' if i == 1 else "")), EGP)
    for i in (1,): scs.cell(Q_.R[f"min_{s}"], 4).number_format = GEN
QR = Q_.R

# ───────────── ASSET REGISTER ─────────────
arg = new_sheet("Asset Register", "Asset Register & IP Assessment", "Recognised assets (IAS 16 / IAS 38) are separated from strategic value drivers. No market values are assigned. Ownership is unconfirmed until the evidence column says Closed.",
                (6, 34, 16, 38, 20, 12, 15, 15, 15, 15, 9, 34, 30, 11, 16))
hdr(arg, 4, ["ID", "Asset", "Category", "Description", "Legal owner", "Created", "Historical cost (EGP)", "Recognised cost (EGP)", "Acc. amortisation (EGP)", "NBV (EGP)", "Life (mo)", "Documents needed", "Accounting treatment", "Significance", "Ownership evidence"])
sw_row = None
ob_ws = wb["Opening BS"]
for rr in range(1, ob_ws.max_row + 1):
    if str(ob_ws.cell(rr, 1).value or "").startswith("Software development"): sw_row = rr
ASSETS = [
 ("A1", "Mobile apps (iOS & Android)", "A · Software & IP", "Booking, pre-order, serving-time choice, payment", "Unconfirmed: company vs founder", "2024–2026", f"='Opening BS'!B{sw_row}", f"='Opening BS'!C{sw_row}", f"={OBS('b_swa')}", "Repo history, developer contracts, IP assignment", "Expensed — no retroactive capitalisation (IAS 38)", "High", "ip"),
 ("A2", "Restaurant web dashboard", "A · Software & IP", "Table plan, orders, kitchen timing, analytics", "Unconfirmed", "2024–2026", None, None, None, "Cost included in A1", "Expensed", "High", "ip"),
 ("A3", "Back end, API and database", "A · Software & IP", "Core platform and data model", "Unconfirmed", "2024–2026", None, None, None, "Cost included in A1; hosting account ownership", "Expensed", "High", "ip"),
 ("A4", "Brand: Reservya name & logo", "A · Software & IP", "Trademark — registration status unknown", "Unconfirmed", "—", 0, 0, 0, "Trademark filing (Egypt ITDA; GCC later)", "Not recognised until registered and costs evidenced", "Medium", "tm"),
 ("A5", "Website, domain reservya.com, app-store accounts", "A · Software & IP", "Distribution and digital identity", "Unconfirmed", "—", 0, 0, 0, "Registrar record, Apple / Google developer accounts", "Expensed (immaterial)", "High", "dom"),
 ("A6", "Source code & repositories", "A · Software & IP", "All code, build scripts, infrastructure config", "Unconfirmed", "2024–2026", None, None, None, "Company-owned repo account, access list, licences of third-party code", "Part of A1 cost", "High", "repo"),
 ("A7", "Payment (Kashier) & WhatsApp integrations", "A · Software & IP", "Merchant set-up and messaging integration", "Company (to confirm)", "2026", None, None, None, "Provider agreements", "Expensed", "Medium", "kash"),
 ("B1", "Laptops, devices, office equipment", "B · Physical", "Owned equipment", "Company (to confirm)", "—", f"={OBS('b_eqc')}", f"={OBS('b_eqc')}", f"={OBS('b_eqd')}", "Purchase invoices", "IAS 16, straight line", "Low", "bank"),
 ("C1", "Restaurant partner agreements (22+ venues tested)", "C · Contracts (strategic)", "Number signed and terms to confirm", "Company", "2026", 0, 0, 0, "Signed agreements, usage data", "Not a recognised asset", "High", "live"),
 ("C2", "Hospitality-consultant agreements", "C · Contracts (strategic)", "Sales channel", "Company", "2026", 0, 0, 0, "Signed agreements", "Not a recognised asset", "Medium", "cons"),
 ("D1", "Product know-how & 2-year build experience", "D · Strategic driver", "Team capability", "—", "—", 0, 0, 0, "Team CVs, vesting, IP assignment", "Not recognised", "High", "team"),
 ("D2", "Restaurant & diner data (growing)", "D · Strategic driver", "Booking and spend data; network effects", "Company", "—", 0, 0, 0, "Privacy policy, Law 151/2020 compliance", "Not recognised", "High", "dp"),
]
for i, row_ in enumerate(ASSETS):
    rr = 5 + i
    for j, v in enumerate(row_[:12]):
        col = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 12, 10: 13, 11: 14}[j]
        isnum = col in (7, 8, 9)
        put(arg, rr, col, v if v is not None else 0, EGP if isnum else GEN, GREEN if isinstance(v, str) and v.startswith("=") else BLACK)
        if not isnum: arg.cell(rr, col).alignment = Alignment(wrap_text=True, vertical="top")
    put(arg, rr, 10, f"=H{rr}-I{rr}", EGP); put(arg, rr, 11, f"={A['life_sw']}" if row_[2].startswith("A") else (f"={A['life_eq']}" if row_[2].startswith("B") else "n/a"), GEN)
    put(arg, rr, 15, f'=IF({DDS(row_[12])}="Closed","Closed","Open")', GEN, GREEN, bold=True)
    arg.row_dimensions[rr].height = 30
at = 5 + len(ASSETS); arg.cell(at, 2, "Total recognised assets (NBV)").font = fnt(bold=True)
for cc in (7, 8, 9, 10): put(arg, at, cc, f"=SUM({L(cc)}5:{L(cc)}{at-1})", EGP, bold=True).border = TOP
r = at + 1; arg.cell(r, 2, "Check: NBV = Opening BS non-current assets"); put(arg, r, 10, f"=ROUND(J{at}-({OBS('b_eqc')}-{OBS('b_eqd')}+{OBS('b_swc')}-{OBS('b_swa')}),0)", EGP, bold=True); AREG_CHK = f"'Asset Register'!$J${r}"
r += 1; arg.cell(r, 2, "Software & IP assets with ownership evidence closed"); put(arg, r, 10, f'=COUNTIFS(C5:C{at-1},"A*",O5:O{at-1},"Closed")&" of "&COUNTIF(C5:C{at-1},"A*")', GEN, bold=True); AREG_OWN = f"'Asset Register'!$J${r}"

r += 2; sec(arg, r, "HISTORICAL SOFTWARE SPEND — EGP 1.65M reconciliation", 15)
r += 1; arg.cell(r, 2, "Stated by management (midpoint of EGP 1.5–1.8M)"); put(arg, r, 7, f"='Opening BS'!B{sw_row}", EGP, GREEN); SWR = {"stated": r}
r += 1; arg.cell(r, 2, "Documented by invoices, payroll or contracts"); put(arg, r, 7, f"='Opening BS'!G{sw_row}", EGP, GREEN); SWR["doc"] = r
note(arg, r, 12, "Enter on Opening BS (column G) as documents are matched.")
r += 1; arg.cell(r, 2, "Undocumented").font = fnt(bold=True); put(arg, r, 7, f"=G{SWR['stated']}-G{SWR['doc']}", EGP, bold=True); SWR["gap"] = r
r += 1; arg.cell(r, 2, "Share documented"); put(arg, r, 7, f"=IFERROR(G{SWR['doc']}/G{SWR['stated']},0)", PCT, bold=True); SWR["pct"] = r
SW_DOC = f"'Asset Register'!$G${SWR['pct']}"

r += 2; sec(arg, r, "IAS 38 — can any development cost be capitalised? (answer Yes / No / Unknown)", 15)
IAS = ["Technical feasibility of completing the asset", "Intention to complete and use or sell it", "Ability to use or sell it", "Probable future economic benefits (market exists)",
       "Adequate technical, financial and other resources", "Costs measured reliably (timesheets, invoices)", "Criteria met and documented at the time the cost was incurred (not after)"]
i0 = r + 1
for q in IAS:
    r += 1; arg.cell(r, 2, q); arg.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6); put(arg, r, 7, "Unknown", GEN, BLUE)
i1 = r
dvy = DataValidation(type="list", formula1='"Yes,No,Unknown"'); arg.add_data_validation(dvy); dvy.add(f"G{i0}:G{i1}")
r += 1; arg.cell(r, 2, "Result").font = fnt(bold=True)
put(arg, r, 7, f'=IF(COUNTIF(G{i0}:G{i1},"Yes")=7,"Eligible for future costs only","Not eligible — expense")', GEN, bold=True); IAS_RES = f"'Asset Register'!$G${r}"
note(arg, r, 12, "Even if eligible, historical spend stays expensed: IAS 38 does not allow retroactive capitalisation.")
r += 1; arg.cell(r, 2, "Historical development capitalised on the opening balance sheet"); put(arg, r, 7, f"={OBS('b_swc')}", EGP, GREEN); IAS_CAP = f"'Asset Register'!$G${r}"
r += 2
note(arg, r, 2, "Categories C and D create value for investors but are not balance-sheet assets. Do not present them with a monetary value without an independent valuation.")
note(arg, r + 1, 2, "Founder contributions (EGP 2.7M), shareholder loans, equipment, liabilities and remaining cash are reconciled on the Opening BS sheet.")

# ───────────── ASSUMPTION REGISTER ─────────────
rg = new_sheet("Assumption Register", "Assumption Register & Evidence Status",
               "A formula passing is not evidence. Only inputs backed by a reviewed document may be set to 'Verified'. Status cells (blue) are updated as evidence arrives.",
               (52, 20, 34, 13, 18, 22, 11, 13, 40, 30, 9))
r = 4; sec(rg, r, "PRIORITY ASSUMPTIONS — what happens if each one is wrong (selected scenario, impact vs plan)", 11)
r += 1; hdr(rg, r, ["Assumption", "Plan value", "Stress tested", "", "Δ 2027 revenue", "Δ 2027 EBITDA", "", "Δ 2031 revenue", "Evidence needed", "Evidence status", ""])
CSn = "'Commission Sensitivity'"
k27, k31 = f"{CSn}!$C${CSR['k']}", f"{CSn}!$G${CSR['k']}"
def isv(key, col): return f"{ISn}!{col}{ISR[key]}"
PRI = [
 ("125 completed bills / restaurant / month", f"=TEXT(Assumptions!D{AR['bills']},\"0\")", "−20% bills", lambda col: f"=-0.2*{isv('comm', col)}", "bills"),
 ("90% of live restaurants transact", f"=TEXT(Assumptions!D{AR['activ']},\"0%\")", "80% activation", lambda col: f"=-{isv('comm', col)}*(1-Assumptions!$C${AR['activ']}/Assumptions!$D${AR['activ']})", "activ"),
 ("EGP 3,000 average bill (Egypt)", f"=TEXT(Countries!C{CP['bill']},\"#,##0\")", "−10% bill", lambda col: f"=-0.1*{isv('comm', col)}", "bill"),
 ("5.5% weighted commission (tier mix)", f"=TEXT({A['c_tier']},\"0.0%\")", "4% on all GMV", lambda col: f"={CSn}!{col}{CSR['tr_0']}-{isv('rev', col)}", "rate"),
 ("70% of live restaurants on a paid plan", f"=TEXT(1-Assumptions!C{AR['p_free']},\"0%\")", "+10 pts on free plan", lambda col: f"=-{isv('sub', col)}*0.1/(1-Assumptions!{col}{AR['p_free']})", "conv"),
 ("Marketing-package adoption (Bronze/Silver/Gold)", f"=TEXT(Assumptions!C{AR['m_b']}+Assumptions!C{AR['m_s']}+Assumptions!C{AR['m_g']},\"0%\")&\" of live\"", "Half the adoption", lambda col: f"=-0.5*({isv('mrec', col)}+{isv('mone', col)})", "mkt"),
]
PRI0 = r + 1
for lab, val, test, fn, ddk in PRI:
    r += 1; rg.cell(r, 1, lab); put(rg, r, 2, val, GEN, GREEN); rg.cell(r, 3, test)
    put(rg, r, 5, fn("C"), EGP); put(rg, r, 8, fn("G"), EGP)
    k = k27 if ddk != "mkt" else f"({k27}-{A['m_cost']})"
    put(rg, r, 6, f"=E{r}*{k}", EGP) if ddk != "rate" else put(rg, r, 6, f"={CSn}!C{CSR['eb_0']}-{isv('ebitda', 'C')}", EGP)
    rg.cell(r, 9, [d for d in DDI if d[0] == ddk][0][1]).alignment = Alignment(wrap_text=True)
    put(rg, r, 10, f'=IF({DDS(ddk)}="Closed","Verified","Management forecast")', GEN, GREEN, bold=True)
r += 1; rg.cell(r, 1, "1.5% monthly restaurant churn"); put(rg, r, 2, f"=TEXT(Assumptions!D{AR['churn']},\"0.0%\")", GEN, GREEN); rg.cell(r, 3, "2.5% churn, targets held")
put(rg, r, 5, 0, EGP); put(rg, r, 8, 0, EGP)
put(rg, r, 6, f"=-{RVn}!C{RVR['avglive']}*0.01*12*'Unit Economics'!C{UER['cac']}", EGP)
note(rg, r, 11, "Targets held, so extra churn costs more acquisition, not revenue.")
rg.cell(r, 9, [d for d in DDI if d[0] == "churn"][0][1]).alignment = Alignment(wrap_text=True)
put(rg, r, 10, f'=IF({DDS("churn")}="Closed","Verified","Management forecast")', GEN, GREEN, bold=True)
PRI1 = r
r += 2; sec(rg, r, "FULL REGISTER", 11)
r += 1; hdr(rg, r, ["Assumption", "Value", "Source document", "Evidence date", "Responsible", "Actual vs estimate", "Confidence", "Last validated", "Impact if wrong", "Evidence status", "Material"])
REG0 = r + 1
def classify(lab, status):
    l = lab.lower()
    if status in ("Control", "Policy", "Memo") or "scenario (" in l:
        return ("Model setting", "—", "n/a", "Model control / policy", "No")
    if status == "Company pricing":
        return ("Reservya Feature Guide / Packages PDF", "Undated — confirm version", "Estimate (published price, not contract)", "Documented — not contract-verified", "Yes")
    if status == "Public source":
        return ("PwC Worldwide Tax Summaries / Egyptian tax law", "To re-check at closing", "Public rule", "Public source — re-check", "Yes")
    if status == "Market practice":
        return ("Standard terms (YC post-money SAFE, market practice)", "—", "Market practice", "Market practice — confirm in term sheet", "Yes")
    if status == "Management target":
        return ("Company valuation calculator", "Undated", "Management target", "Management target — not a fair value", "Yes")
    if status == "Verified: none":
        return ("Management statement: none signed", "—", "Reported actual = 0", "Management forecast", "Yes")
    return ("None — management forecast", "—", "Estimate", "Management forecast", "Yes")
def impact(lab):
    l = lab.lower()
    for keys, t in [(("bill", "commission", "refund", "waive", "ramp", "transact", "targets achieved"), "Commission revenue and EBITDA"),
                    (("plan", "price", "subscription", "collection rate"), "Subscription revenue and cash"),
                    (("package", "campaign", "marketing-package", "adoption"), "Marketing revenue"),
                    (("sponsor", "contract value", "renewal"), "Sponsorship revenue"),
                    (("churn",), "Acquisition cost and LTV"),
                    (("salary", "hosting", "marketing", "administration", "legal", "consultant", "onboarding", "equipment", "messaging", "devices", "headcount"), "Operating costs, EBITDA, runway"),
                    (("tax",), "Net profit and cash timing"),
                    (("days", "buffer"), "Cash timing and runway"),
                    (("valuation", "exit", "probability", "pool", "safe", "pre-money"), "Valuation and dilution only"),
                    (("capitalised", "useful life"), "EBITDA vs amortisation split")]:
        if any(k in l for k in keys): return t
    return "See Methodology"
for lab, f, fmt_, src, conf, status in REG:
    r += 1
    srcdoc, edate, ave, est, mat = classify(lab, status)
    rg.cell(r, 1, lab).alignment = Alignment(wrap_text=True); put(rg, r, 2, f, fmt_, GREEN)
    rg.cell(r, 3, srcdoc).alignment = Alignment(wrap_text=True); rg.cell(r, 4, edate)
    put(rg, r, 5, "Founder / CEO (assign)" if mat == "Yes" else "—", GEN, BLUE); rg.cell(r, 6, ave)
    rg.cell(r, 7, conf); put(rg, r, 8, "Not validated" if mat == "Yes" else "—", GEN, BLUE)
    rg.cell(r, 9, impact(lab)); put(rg, r, 10, est, GEN, BLUE); rg.cell(r, 11, mat)
    note(rg, r, 12, src)
    if conf == "Low": rg.cell(r, 7).fill = RFILL
REG1 = r
dvs = DataValidation(type="list", formula1='"Verified,Documented — not contract-verified,Public source — re-check,Market practice — confirm in term sheet,Management target — not a fair value,Management forecast,Verified (none exist),Model control / policy"', allow_blank=True)
rg.add_data_validation(dvs); dvs.add(f"J{REG0}:J{REG1}")
rg.column_dimensions["L"].width = 60
r += 2; sec(rg, r, "EVIDENCE COMPLETENESS", 11)
r += 1; rg.cell(r, 1, "Material assumptions"); put(rg, r, 2, f'=COUNTIF(K{REG0}:K{REG1},"Yes")', NUM); EV_MAT = f"'Assumption Register'!$B${r}"
r += 1; rg.cell(r, 1, "… verified by a reviewed document"); put(rg, r, 2, f'=COUNTIFS(K{REG0}:K{REG1},"Yes",J{REG0}:J{REG1},"Verified*")', NUM); EV_VER = f"'Assumption Register'!$B${r}"
r += 1; rg.cell(r, 1, "… documented or public but not yet verified"); put(rg, r, 2, f'=COUNTIFS(K{REG0}:K{REG1},"Yes",J{REG0}:J{REG1},"Documented*")+COUNTIFS(K{REG0}:K{REG1},"Yes",J{REG0}:J{REG1},"Public*")+COUNTIFS(K{REG0}:K{REG1},"Yes",J{REG0}:J{REG1},"Market*")', NUM); EV_DOC = f"'Assumption Register'!$B${r}"
r += 1; rg.cell(r, 1, "… management forecast or target, no evidence").font = fnt(bold=True); put(rg, r, 2, f"={EV_MAT}-{EV_VER}-{EV_DOC}", NUM, bold=True); EV_UNR = f"'Assumption Register'!$B${r}"
r += 1; rg.cell(r, 1, "Priority assumptions still unverified").font = fnt(bold=True); put(rg, r, 2, f'=COUNTIF(J{PRI0}:J{PRI1},"Management forecast")&" of "&ROWS(J{PRI0}:J{PRI1})', GEN, bold=True); EV_PRI = f"'Assumption Register'!$B${r}"
rg.freeze_panes = "B6"

# ───────────── METHODOLOGY ─────────────
me = new_sheet("Methodology", "Methodology & Notes", "How the model works and the accounting policies behind it.", (120,))
NOTES = [
 ("Structure", "Three 60-month engines (Downside, Base, Upside) calculate every line monthly. Annual statements pull the scenario chosen on Assumptions. All figures are formulas; inputs are blue."),
 ("Restaurant ramp", "Year-end live targets are management's (200 / 600 / 1,200 / 2,000 / 3,000 in Base). Months between are interpolated. New live = change in live + churn. Signing leads going live by one month. New venues ramp: month 1 and 2 transact at reduced rates."),
 ("Average vs year-end", "Revenue is earned on the monthly live count, so annual revenue reflects the average (e.g. ~108 in 2027), not the 200 at year end."),
 ("Commission", "Commission = completed GMV × (1 − refunds) × realised rate × (1 − waivers). GMV is restaurants' money and is never shown as revenue. Rate cases 4% / 5.5% / 7% / tier mix; 5.5% is the midpoint of the 4–7% range, not a verified market rate."),
 ("Subscriptions", "Plans: commission-only (free), Single Feature EGP 2,000, Full Features EGP 5,000, Multi-venue EGP 3,000 per branch. Revenue = paying restaurants × plan price × country price index × annual price increase. Collection rate applied to cash."),
 ("Marketing packages", "Bronze 5K, Silver 15K, Gold 25K a month plus one-time campaigns. Revenue = eligible live restaurants × adoption × price. Media bought on a restaurant's behalf is passed through (agent, IFRS 15) — only Reservya's fee is revenue."),
 ("Sponsorships", "Signed (verified) contracts, pipeline (memo only) and projected campaigns are kept separate. Revenue recognised evenly over the campaign; renewals by probability."),
 ("Costs", "Headcount by function with loaded salaries and 10% annual raise. Brand marketing scales with revenue. Gulf/Jordan/Morocco operating partners take a revenue share; launch costs per country."),
 ("Capitalisation", "Optional share of engineering & product salaries capitalised under IAS 38 (default 20%) — only if criteria are documented. Set to 0% if not. Historical build costs are expensed (no retroactive capitalisation)."),
 ("Tax", "22.5% Egyptian rate applied to consolidated profit (conservative), with loss carry-forward. Accrued in December, paid in April of the next year."),
 ("Working capital", "Receivables by collection days per stream; payables by supplier days. Tax payable on the balance sheet until paid."),
 ("Funding", "Funding scenario adds the raise in January 2027 at the 2027 FX rate. It does not change the operating plan. Future seed & Series A are illustrative and only used for dilution."),
 ("Opening balance sheet", "Founder contribution of EGP 2.7M reconciled to its uses. Treated as equity unless a loan share is entered. Accumulated deficit is derived from expensed costs, not a plug."),
 ("Valuation", "VC method, First Chicago, risk-adjusted milestone and modified Berkus. Comparables only when verified. Exit outcomes are illustrative."),
 ("Limitations", "No live operating history; restaurant volumes, churn, adoption and sponsorship values are unverified. FX held flat at 50 EGP/USD for comparability — update before use. Not audited; not tax or legal advice."),
]
for i, (h, t) in enumerate(NOTES):
    rr = 4 + i * 2; me.cell(rr, 1, h).font = fnt("1A2420", True, size=11); me.cell(rr + 1, 1, t).alignment = Alignment(wrap_text=True, vertical="top"); me.row_dimensions[rr + 1].height = 30

r_me = 4 + len(NOTES) * 2 + 1
sec(me, r_me, "CHANGE LOG — V2.1 investor-readiness corrections (November 2026)", 1)
CHANGES = [
 "Engines audited (all 3 scenarios, 60 months): refunds deducted once; commission = commissionable GMV × rate − waivers; funnel rolls forward exactly; tax carry-forward and April payment confirmed; no circular references. No formula errors found that changed results.",
 "Added GMV → commissionable GMV → gross commission → net commission reconciliation with a zero-difference check (Revenue & Monetization).",
 "Added a monetisation verification table: pricing, adoption basis, revenue recognition (net for agent media), delivery cost, collection timing and evidence status per stream.",
 "Added current-traction actuals (Assumptions) kept separate from the forecast; blank until documented.",
 "Assumption Register rebuilt: source document, evidence date, responsible person, actual vs estimate, confidence, last validation, impact if wrong, evidence status, materiality; priority-assumption impact table.",
 "Asset Register completed: back end, source code, website/domains added; ownership evidence linked to due diligence; EGP 1.65M software reconciliation; IAS 38 eligibility test (historical spend stays expensed).",
 "Opening BS: documented vs stated amounts for each use of the EGP 2.7M; evidence gap shown.",
 "Unit Economics: marketplace CAC (incl. diner marketing) added beside restaurant CAC; LTV/CAC labelled projected.",
 "Funding Scenarios: total round vs individual ticket; what each amount pays for (restaurants, engineer-years, marketing months, headcount); delayed-collection downside stress; purpose of capital above A; next financing requirement.",
 "Valuation: automatic 'defensible' verdict removed. Assessment now requires evidence on 5 value drivers. Comparables count only if marked verified. Exit/return sensitivity and dilution/timing tests added; all returns labelled illustrative.",
 "Checks split into formula integrity (must pass), business warnings, and evidence completeness; investor-readiness score added.",
 "Dashboard: actual vs forecast separated; milestones, valuation assumptions, open due-diligence items and evidence indicator added.",
 "Base-case inputs, restaurant targets, revenue streams, commission range and funding scenarios unchanged.",
]
for i, t in enumerate(CHANGES):
    c = me.cell(r_me + 1 + i, 1, f"{i+1}. {t}"); c.alignment = Alignment(wrap_text=True, vertical="top"); me.row_dimensions[r_me + 1 + i].height = 30
r_me += len(CHANGES) + 2
sec(me, r_me, "OPEN MODELLING & ACCOUNTING ISSUES (documented, not overridden)", 1)
ISSUES = [
 "Tax: 22.5% Egyptian rate applied to consolidated profit. Gulf/Jordan/Morocco rates, withholding tax and transfer pricing are not modelled (Countries shows them for information).",
 "VAT is excluded from revenue as a pass-through; VAT cash timing is not modelled.",
 "Sponsorship revenue uses the contract value of the month the campaign is active; campaigns spanning a year-end use the new year's value (small timing effect).",
 "Subscriptions and marketing packages are billed from the first live month, including the ramp months.",
 "Gulf prices use an EGP-equivalent price index at a flat FX rate; a weaker EGP would raise Gulf revenue in EGP.",
 "Card/bank fees on diners' bills are assumed passed through to restaurants (Feature Guide). If Kashier charges Reservya, they become a direct cost (~2–3% of GMV).",
 "Receivables of churned restaurants are not separately written off beyond the 3% bad-debt allowance.",
 "Signed restaurants are modelled as going live one month later (fixed lag).",
 "Operating plan does not change with the funding scenario; funding only changes cash and dilution.",
]
for i, t in enumerate(ISSUES):
    c = me.cell(r_me + 1 + i, 1, f"• {t}"); c.alignment = Alignment(wrap_text=True, vertical="top"); me.row_dimensions[r_me + 1 + i].height = 28

# ───────────── DUE DILIGENCE / UNRESOLVED EVIDENCE ─────────────
dd = new_sheet("Due Diligence", "Due Diligence & Unresolved Evidence List", "Status stays Open until the document has been reviewed. Set Closed only after review (date it).", (5, 56, 13, 40, 10, 10, 30, 32, 18, 13))
hdr(dd, 4, ["#", "Evidence item", "Area", "Why it matters", "Status", "Priority", "Linked input / sheet", "Impact if missing", "Owner", "Date closed"])
for i, (k, it, ar_, why, pri, link, imp) in enumerate(DDI):
    rr = 5 + i; put(dd, rr, 1, i + 1, GEN); dd.cell(rr, 2, it).alignment = Alignment(wrap_text=True); dd.cell(rr, 3, ar_); dd.cell(rr, 4, why).alignment = Alignment(wrap_text=True)
    put(dd, rr, 5, "Open", GEN, BLUE); dd.cell(rr, 6, pri); dd.cell(rr, 7, link); dd.cell(rr, 8, imp).alignment = Alignment(wrap_text=True)
    put(dd, rr, 9, "Founder / CEO (assign)", GEN, BLUE); put(dd, rr, 10, None, GEN, BLUE)
    if pri == "Critical": dd.cell(rr, 6).fill = RFILL
    dd.row_dimensions[rr].height = 28
DD1 = 5 + len(DDI) - 1
dvd = DataValidation(type="list", formula1='"Open,In progress,Closed"'); dd.add_data_validation(dvd); dvd.add(f"E5:E{DD1}")
rr = DD1 + 2; dd.cell(rr, 2, "Open items").font = fnt(bold=True); put(dd, rr, 5, f'=COUNTIF(E5:E{DD1},"<>Closed")', NUM, bold=True); DD_OPEN = f"'Due Diligence'!$E${rr}"
rr += 1; dd.cell(rr, 2, "Open critical items").font = fnt(bold=True); put(dd, rr, 5, f'=COUNTIFS(E5:E{DD1},"<>Closed",F5:F{DD1},"Critical")', NUM, bold=True); DD_CRIT = f"'Due Diligence'!$E${rr}"
dd.freeze_panes = "C5"

# ───────────── CHECKS ─────────────
ck = new_sheet("Checks", "Model Integrity, Warnings, Evidence & Readiness", "Section 1 must read ALL PASS. Sections 2–3 are business and evidence signals — a formula passing does not validate an assumption.", (74, 22, 14))
CK = []; WARN = []
r = 4; sec(ck, r, "1. FORMULA INTEGRITY (tolerance EGP 1)", 3)
r += 1; hdr(ck, r, ["Check", "Difference", "Status"])
def chk(label, f, kind="tol"):
    global r
    r += 1; ck.cell(r, 1, label); put(ck, r, 2, f, EGP if kind == "tol" else GEN)
    put(ck, r, 3, f'=IF(ABS(B{r})<=1,"PASS","FAIL")' if kind == "tol" else f'=IF(B{r},"PASS","FAIL")', GEN, bold=True); CK.append(r)
def eng_sum(s, expr):  # SUMPRODUCT(ABS(expr)) over months for engine s, expr uses {X} for range of key X
    sn, R = ENG[s]
    import re
    e = re.sub(r"\{(\w+)\}", lambda m_: f"{sn}!${FIRST}${R[m_.group(1)]}:${LAST}${R[m_.group(1)]}", expr)
    return f"=SUMPRODUCT(ABS({e}))"
ck_sub = lambda t: (ck.cell(r + 1, 1, t).__setattr__("font", fnt("1A2420", True)), None)
# H1 opening restaurants vs actual
chk("H1 · Opening live restaurants = verified actual (blank actual = evidence pending, see section 3)", f'=IF(ISNUMBER({TRX["live"]}),SUM(Countries!C{CP["open"]}:G{CP["open"]})-{TRX["live"]},0)')
for s in ["Downside", "Base", "Upside"]:
    sn, R = ENG[s]
    chk(f"H2 · {s}: opening + new − churned = closing live restaurants (60 months)", f"={sn}!$C${R['live']}+SUM({sn}!${FIRST}${R['new']}:${LAST}${R['new']})-SUM({sn}!${FIRST}${R['churned']}:${LAST}${R['churned']})-{sn}!${LAST}${R['live']}")
chk("H2 · Annual funnel: prior year-end + new − churned = year-end (selected)", "=SUMPRODUCT(ABS(" + f"{RVn}!D{RVR['live']}:G{RVR['live']}-{RVn}!C{RVR['live']}:F{RVR['live']}-{RVn}!D{RVR['newlive']}:G{RVR['newlive']}+{RVn}!D{RVR['churned']}:G{RVR['churned']}))+ABS({RVn}!C{RVR['live']}-SUM(Countries!C{CP['open']}:G{CP['open']})-{RVn}!C{RVR['newlive']}+{RVn}!C{RVR['churned']})")
for s in ["Downside", "Base", "Upside"]:
    chk(f"H3 · {s}: commissionable GMV = completed GMV − refunds (refunds deducted once)", eng_sum(s, "{egmv}-{gmv}-{refunds}"))
    chk(f"H3 · {s}: net commission = gross commission − waivers = Σ country commission", eng_sum(s, "{comm}-{comm_gross}-{waived}"))
chk("H3 · GMV → net commission reconciliation ties to income statement (5 years)", f"=SUMPRODUCT(ABS({RVn}!C{RVR['rc_chk']}:G{RVR['rc_chk']}))")
chk("H4 · Commission tier shares total 100%", f"=({A['tier_share_sum']}-1)*1000000")
chk("H5 · Subscription plan mix totals 100% each year", f"=SUMPRODUCT(ABS(Assumptions!C{AR['p_sum']}:G{AR['p_sum']}-1))*1000000")
chk("H5 · Plan shares between 0% and 100%", f"=SUMPRODUCT((Assumptions!C{AR['p_free']}:G{AR['p_multi']}<0)+(Assumptions!C{AR['p_free']}:G{AR['p_multi']}>1))")
chk("H5 · Marketing adoption ≤ 100% of live restaurants in every scenario", f"=MAX(0,SUMPRODUCT(MAX((Assumptions!C{AR['m_b']}:G{AR['m_b']}+Assumptions!C{AR['m_s']}:G{AR['m_s']}+Assumptions!C{AR['m_g']}:G{AR['m_g']})*MAX(Assumptions!C{AR['mktx']}:E{AR['mktx']})))-1)*1000000")
for s in ["Downside", "Base", "Upside"]:
    chk(f"H6 · {s}: marketing delivery cost = cost rate × marketing revenue (net basis)", eng_sum(s, f"{{c_mkt}}-({{mrec}}+{{mone}})*{A['m_cost']}"))
chk("H7 · Founder EGP 2.7M fully reconciled to uses", f"='Opening BS'!B{OB['var']}")
chk("H7 · Documented amounts do not exceed stated amounts", f"=SUMPRODUCT(('Opening BS'!G{OB['u0']}:G{OB['cash']}>'Opening BS'!B{OB['u0']}:B{OB['cash']})*1)")
chk("H7 · Opening balance sheet balances", f"='Opening BS'!B{OB['b_chk']}")
chk("H8 · Historical development capitalised only if IAS 38 test passed", f'=IF({IAS_RES}="Not eligible — expense",{IAS_CAP},0)')
chk("H8 · Asset register NBV = opening balance sheet", f"={AREG_CHK}")
for s in ["Downside", "Base", "Upside"]:
    sn, R = ENG[s]
    chk(f"H8 · {s}: capitalised software NBV never negative; amortisation ≤ cost", f"=SUMPRODUCT(({sn}!$C${R['bs_sw']}:${LAST}${R['bs_sw']}<-1)*1)+MAX(0,SUM({sn}!${FIRST}${R['amort']}:${LAST}${R['amort']})-SUM({sn}!${FIRST}${R['capsw']}:${LAST}${R['capsw']})-{OBS('b_swc')})")
    chk(f"H9 · {s}: tax never negative; tax paid ≤ tax expensed", f"=SUMPRODUCT(({sn}!${FIRST}${R['tax']}:${LAST}${R['tax']}<0)*1)+MAX(0,SUM({sn}!${FIRST}${R['taxpaid']}:${LAST}${R['taxpaid']})-SUM({sn}!${FIRST}${R['tax']}:${LAST}${R['tax']}))")
chk("H9 · Tax rate within 0–50% and all FX rates positive", f"=AND({A['tax']}>=0,{A['tax']}<=0.5,MIN(FX!C5:G5)>0,MIN(FX!C{min(FXR.values())}:C{max(FXR.values())})>0)", "bool")
for s in ["Downside", "Base", "Upside"]:
    sn, R = ENG[s]
    chk(f"H10 · {s}: equity inflow = selected round × 2027 FX; paid-in capital rolls forward", f"=SUM({sn}!${FIRST}${R['cf_eq']}:${LAST}${R['cf_eq']})-{A['raise_sel']}*FX!$C$5+{sn}!${LAST}${R['bs_pic']}-{OBS('b_pic')}-SUM({sn}!${FIRST}${R['cf_eq']}:${LAST}${R['cf_eq']})-SUM({sn}!${FIRST}${R['cf_add']}:${LAST}${R['cf_add']})")
chk("H10 · Cap table totals 100% at every stage", f"=SUMPRODUCT(ABS('Cap Table'!B{CTR['tot']}:E{CTR['tot']}-1))*1000000")
chk("H10 · Investor ownership = round ÷ post-money (A, B, C)", f"=SUMPRODUCT(ABS({FSN}!C{FR['own']}:E{FR['own']}-{FSN}!C{FR['raise']}:E{FR['raise']}/{FSN}!C{FR['post']}:E{FR['post']}))*1000000")
chk("H10 · Use of funds totals 100% (A, B, C)", f"=SUMPRODUCT(ABS('Use of Funds'!B{UF_TOT}:D{UF_TOT}-1))*1000000")
for s in ["Downside", "Base", "Upside"]:
    sn, R = ENG[s]
    chk(f"H12 · {s}: balance sheet balances every month", f"=SUMPRODUCT(ABS({sn}!$C${R['bs_chk']}:${LAST}${R['bs_chk']}))")
    chk(f"H12 · {s}: cash-flow closing cash = balance-sheet cash every month", eng_sum(s, "{cash}-{bs_cash}"))
chk("H12 · Annual balance sheet balances (opening + 5 years)", f"=SUMPRODUCT(ABS({BSn}!C{BSR['chk']}:H{BSR['chk']}))")
chk("H12 · Annual cash flow ties to balance-sheet cash (5 years)", f"=SUMPRODUCT(ABS({CFn}!C{CFR['chk']}:G{CFR['chk']}))")
chk("H12 · Retained earnings roll forward = opening + net profit (5 years)", f"={BSn}!H{BSR['bs_re']}-{BSn}!C{BSR['bs_re']}-SUM({ISn}!C{ISR['ni']}:G{ISR['ni']})")
chk("H12 · Revenue by stream = income-statement revenue (5 years)", f"=SUMPRODUCT(ABS({RVn}!C{RVR['t_rev']}:G{RVR['t_rev']}-{ISn}!C{ISR['rev']}:G{ISR['rev']}))")
chk("H12 · Gross profit by stream = income-statement gross profit (5 years)", f"=SUMPRODUCT(ABS({ISn}!C{ISR['gp']}:G{ISR['gp']}-({RVn}!C{RVR['gm_comm']}:G{RVR['gm_comm']}+{RVn}!C{RVR['gm_sub']}:G{RVR['gm_sub']}+{RVn}!C{RVR['gm_mkt']}:G{RVR['gm_mkt']}+{RVn}!C{RVR['gm_spon']}:G{RVR['gm_spon']})))")
chk("H12 · Net profit: income statement = monthly engine (5 years, selected)", "=" + "+".join(f"ABS({ISn}!{yc}{ISR['ni']}-{SY('ni', yc).replace(yc+'$3', str(YEARS[i]))})" for i, yc in enumerate(YC)))
chk("Country targets total = management targets", f"=SUMPRODUCT(ABS(Countries!C{CT['tot']}:G{CT['tot']}-Countries!C{CT['mgmt']}:G{CT['mgmt']}))")
chk("Valuation probabilities total 100%", f"=(SUM(Assumptions!C{AR['prob']}:E{AR['prob']})-1)*1000000")
CK0, CK1 = CK[0], CK[-1]
r += 2; ck.cell(r, 1, "FORMULA INTEGRITY STATUS").font = fnt(bold=True, size=12)
put(ck, r, 3, f'=IF(COUNTIF(C{CK0}:C{CK1},"FAIL")=0,"ALL PASS","FAIL")', GEN, bold=True, fill=TFILL); CK_ALL = f"Checks!$C${r}"
put(ck, r, 2, f'=COUNTIF(C{CK0}:C{CK1},"PASS")&" of "&ROWS(C{CK0}:C{CK1})&" pass"', GEN)

r += 2; sec(ck, r, "2. BUSINESS WARNINGS (not formula errors — they describe risk in the chosen scenario)", 3)
r += 1; hdr(ck, r, ["Warning", "Value", "Status"])
def warn(label, f, ok, fmt_=EGP):
    global r
    r += 1; ck.cell(r, 1, label); put(ck, r, 2, f, fmt_); put(ck, r, 3, f'=IF({ok.replace("X", f"B{r}")},"OK","WARNING")', GEN, bold=True); WARN.append(r)
warn("Selected scenario: months below the minimum cash buffer", f"={MRS['short']}", "X=0", NUM)
warn("H11 · Downside + delayed collections: lowest cash with selected round (EGP)", f"={FSsel('d_stress')}", f"X>={A['minbuf']}")
warn("Downside: lowest cash with selected round (EGP)", f"={FSsel('d_mincash')}", f"X>={A['minbuf']}")
warn("EBITDA margin 2031 above 40% in selected scenario (investors will challenge)", f"={ISn}!G{ISR['em']}", "X<=0.4", PCT)
warn("Restaurant LTV/CAC above 10x (projected — needs cohort evidence)", f"='Unit Economics'!C{UER['ltvcac']}", "X<=10", X)
WARN_ALL = f'COUNTIF(C{WARN[0]}:C{WARN[-1]},"WARNING")'

r += 2; sec(ck, r, "3. EVIDENCE COMPLETENESS (separate from formula integrity)", 3)
r += 1; hdr(ck, r, ["Evidence area", "Status", "Resolved?"])
EVR = []
def ev(label, f, ok):
    global r
    r += 1; ck.cell(r, 1, label); put(ck, r, 2, f, GEN); put(ck, r, 3, f'=IF({ok},"Resolved","UNRESOLVED")', GEN, bold=True); EVR.append(r)
ev("Material assumptions verified by documents", f'={EV_VER}&" of "&{EV_MAT}', f"{EV_VER}={EV_MAT}")
ev("Priority assumptions (bills, activation, churn, commission, bill, conversion, adoption) unverified", f"={EV_PRI}", f'LEFT({EV_PRI},1)="0"')
ev("Current live restaurants documented (H1)", f'=IF(ISNUMBER({TRX["live"]}),"Entered","Not entered")', f"ISNUMBER({TRX['live']})")
ev("Founder EGP 2.7M documented", f"=TEXT('Opening BS'!G{OB['uses']}/'Opening BS'!B{OB['contrib']},\"0%\")", f"'Opening BS'!H{OB['uses']}=0")
ev("Historical software spend EGP 1.65M documented", f'=TEXT({SW_DOC},"0%")', f"{SW_DOC}=1")
ev("IAS 38 eligibility determined", f"={IAS_RES}", f'COUNTIF(\'Asset Register\'!G{i0}:G{i1},"Unknown")=0')
ev("Software & IP ownership evidence closed", f"={AREG_OWN}", f'LEFT({AREG_OWN},FIND(" ",{AREG_OWN})-1)=MID({AREG_OWN},FIND("of ",{AREG_OWN})+3,9)')
ev("Commission tier mix matched to signed contracts", f'={DDS("rate")}', f'{DDS("rate")}="Closed"')
ev("Verified comparable financings", f"=Valuation!C{VA['cmpn']}", f"Valuation!C{VA['cmpn']}>0")
ev("Due-diligence items open (critical)", f'={DD_OPEN}&" ("&{DD_CRIT}&" critical)"', f"{DD_OPEN}=0")
r += 2; ck.cell(r, 1, "EVIDENCE STATUS").font = fnt(bold=True, size=12)
put(ck, r, 3, f'=IF(COUNTIF(C{EVR[0]}:C{EVR[-1]},"UNRESOLVED")=0,"COMPLETE","INCOMPLETE")', GEN, bold=True, fill=RFILL); EV_ALL = f"Checks!$C${r}"
put(ck, r, 2, f'=COUNTIF(C{EVR[0]}:C{EVR[-1]},"UNRESOLVED")&" of "&ROWS(C{EVR[0]}:C{EVR[-1]})&" unresolved"', GEN)

r += 2; sec(ck, r, "4. INVESTOR-READINESS ASSESSMENT (scores update as evidence is closed)", 3)
r += 1; hdr(ck, r, ["Dimension (weight)", "Score / 10", "Weight"])
SC_ = []
def sc(label, f, w):
    global r
    r += 1; ck.cell(r, 1, label); put(ck, r, 2, f, '0.0'); put(ck, r, 3, w, PCT, BLUE); SC_.append(r)
sc("Formula integrity, linkage and reconciliations", f'=IF({CK_ALL}="ALL PASS",10,3)', 0.20)
sc("Scenario, sensitivity and stress coverage (judgement)", 9, 0.10)
sc("Assumption evidence (verified = 1, documented = 0.5)", f"=IFERROR(10*({EV_VER}+0.5*{EV_DOC})/{EV_MAT},0)", 0.25)
sc("Historical capital, IP and asset documentation", f"=10*(0.4*'Opening BS'!G{OB['uses']}/'Opening BS'!B{OB['contrib']}+0.3*{SW_DOC}+0.3*COUNTIFS('Asset Register'!C5:C{at-1},\"A*\",'Asset Register'!O5:O{at-1},\"Closed\")/COUNTIF('Asset Register'!C5:C{at-1},\"A*\"))", 0.15)
sc("Valuation support (methods + evidenced value drivers + comparables)", f"=MIN(10,4+Valuation!C{VA['evn']}+IF(Valuation!C{VA['cmpn']}>0,1,0))", 0.10)
sc("Funding clarity and use of funds (judgement)", 9, 0.10)
sc("Disclosure and transparency (judgement)", 9, 0.10)
r += 1; ck.cell(r, 1, "Overall investor readiness").font = fnt(bold=True, size=12)
put(ck, r, 2, f"=SUMPRODUCT(B{SC_[0]}:B{SC_[-1]},C{SC_[0]}:C{SC_[-1]})", '0.0" / 10"', bold=True, fill=TFILL); RDY = f"Checks!$B${r}"
put(ck, r, 3, f"=SUM(C{SC_[0]}:C{SC_[-1]})", PCT)
r += 1; ck.cell(r, 1, "Model mechanics only (integrity, coverage, funding, disclosure)"); put(ck, r, 2, f"=(B{SC_[0]}*0.2+B{SC_[1]}*0.1+B{SC_[5]}*0.1+B{SC_[6]}*0.1)/0.5", '0.0" / 10"', bold=True); RDY_M = f"Checks!$B${r}"
r += 1; ck.cell(r, 1, "Score if every evidence item is closed and assumptions verified"); put(ck, r, 2, f"=(10*0.2+9*0.1+10*0.25+10*0.15+10*0.1+9*0.1+9*0.1)", '0.0" / 10"')
note(ck, r + 1, 1, "The 9/10 target is reachable only by closing evidence items — not by changing formulas or assumptions.")

# ───────────── DASHBOARD ─────────────
db = new_sheet("Dashboard", "Reservya — Investor Dashboard", "ACTUAL figures (company-reported, with evidence status) are kept apart from FORECAST figures (model). Follows the selectors on Assumptions.", (44, 16, 16, 16, 16, 16, 3, 34, 30))
put(db, 3, 1, f'="Operating: "&{A["scen_name"]}&"  ·  Commission: "&{A["comm_name"]}&"  ·  Funding: "&CHOOSE({A["fundsel"]},"A","B","C")&"  ·  Formula checks: "&{CK_ALL}&"  ·  Evidence: "&{EV_ALL}&"  ·  Readiness: "&TEXT({RDY},"0.0")&"/10"', GEN, bold=True)
r = 5; sec(db, r, "ACTUAL — current traction (company-reported)", 6)
r += 1; hdr(db, r, ["Metric", "Value", "Evidence status"])
for k, lab, fmt_, stat in [("tested", "Venues tested in real service", NUM, f'=IF({DDS("live")}="Closed","Documented","Reported — documents pending")'),
                           ("launch", "Public launch", GEN, f'=IF({DDS("prod")}="Closed","Documented","Reported — documents pending")'),
                           ("invested", "Founder investment to date (EGP)", EGP, f"=TEXT('Opening BS'!G{OB['uses']}/'Opening BS'!B{OB['contrib']},\"0%\")&\" documented\""),
                           ("live", "Live restaurants (verified)", NUM, f'=IF(ISNUMBER({TRX["live"]}),"Entered — check source","Not yet documented")'),
                           ("paying", "Paying restaurants", NUM, f'=IF(ISNUMBER({TRX["paying"]}),"Entered — check source","Not yet documented")'),
                           ("bills", "Completed bills, latest month", NUM, f'=IF(ISNUMBER({TRX["bills"]}),"Entered — check source","Not yet documented")'),
                           ("rate", "Average commission charged", PCT, f'=IF(ISNUMBER({TRX["rate"]}),"Entered — check source","Not yet documented")')]:
    r += 1; db.cell(r, 1, lab); put(db, r, 2, f'=IF(ISBLANK({TRX[k]}),"—",{TRX[k]})', fmt_, GREEN); put(db, r, 3, stat, GEN, GREEN)
r += 2; sec(db, r, "FORECAST — selected scenario (model output, not results)", 6)
r += 1; hdr(db, r, ["", "2027", "2028", "2029", "2030", "2031"])
DBR = {}
UEN = "'Unit Economics'"
FLINES = [("Live restaurants (year end)", RVn, RVR["live"], NUM), ("New restaurants live", RVn, RVR["newlive"], NUM), ("Restaurants churned", RVn, RVR["churned"], NUM),
          ("Average transacting restaurants", RVn, RVR["avgtrx"], NUM), ("Completed online bills", RVn, RVR["bills"], NUM), ("Completed GMV (EGP)", RVn, RVR["gmv"], EGP),
          ("Revenue — commission", ISn, ISR["comm"], EGP), ("Revenue — subscriptions", ISn, ISR["sub"], EGP), ("Revenue — restaurant marketing", RVn, RVR["mtot"], EGP),
          ("Revenue — brand sponsorships", ISn, ISR["spon"], EGP), ("Total revenue (EGP)", ISn, ISR["rev"], EGP), ("Total revenue (USD)", ISn, ISR["rev_usd"], USD),
          ("Gross margin", ISn, ISR["gm"], PCT), ("Contribution margin per restaurant", UEN, UER["cm"], PCT), ("EBITDA (EGP)", ISn, ISR["ebitda"], EGP),
          ("EBITDA margin", ISn, ISR["em"], PCT), ("Net profit (EGP)", ISn, ISR["ni"], EGP), ("Closing cash (EGP)", BSn, BSR["bs_cash"], EGP),
          ("Headcount (year end)", OHn, OHR.get("hc", 12), NUM), ("Restaurant CAC (EGP, projected)", UEN, UER["cac"], EGP),
          ("Marketplace CAC (EGP, projected)", UEN, UER["cac_mp"], EGP), ("LTV / restaurant CAC (projected)", UEN, UER["ltvcac"], X)]
for lab, sh, row_, fmt_ in FLINES:
    r += 1; db.cell(r, 1, lab).font = fnt(bold=lab.startswith("Total revenue (EGP)") or lab.startswith("EBITDA (")); DBR[lab] = r
    for j in range(5):
        col = L(4 + j) if sh == BSn else L(3 + j)
        put(db, r, 2 + j, f"={sh}!{col}{row_}", fmt_, GREEN)
F_END = r
kp = 6
db.cell(5, 8, "FUNDING, VALUATION & DILIGENCE").font = fnt("FFFFFF", True); db.cell(5, 8).fill = HFILL; db.cell(5, 9).fill = HFILL
KPIS = [("Round (USD) / investors", f'=TEXT({FSsel("raise")},"$#,##0")&" / "&{FSsel("inv")}', GEN), ("Individual ticket (USD)", f"={FSsel('perinv')}", USD),
        ("Pre-money (management proposal)", f"={A['premoney']}", USD), ("Post-money (USD)", f"={FSsel('post')}", USD),
        ("Investor ownership (round)", f"={FSsel('own')}", PCT), ("Lowest cash, 60 months (EGP)", f"={MRS['mincash']}", EGP),
        ("Lowest cash — downside + late payments", f"={FSsel('d_stress')}", EGP), ("First EBITDA-positive month (forecast)", f"={MRS['be']}", GEN),
        ("Milestones funded", f"={FSsel('mil')}", GEN), ("Next financing", f"={FSsel('nextfin')}", GEN),
        ("Valuation methods — range (USD)", f'=TEXT(Valuation!C{VA["lo"]},"$#,##0")&" – "&TEXT(Valuation!C{VA["hi"]},"$#,##0")', GEN),
        ("Valuation assumptions", f'="Exit "&TEXT(Valuation!C{VA["mult"]},"0.0")&"x 2031 revenue; target return "&TEXT(Valuation!C{VA["ret_m"]},"0")&"x; seed $"&TEXT(Assumptions!D{AR["seed"]}/1000000,"0")&"M pre (illustrative)"', GEN),
        ("Valuation assessment", f"=Valuation!C{VA['verdict']}", GEN),
        ("Open due-diligence items (critical)", f'={DD_OPEN}&" ("&{DD_CRIT}&" critical)"', GEN),
        ("Material assumptions verified", f'={EV_VER}&" of "&{EV_MAT}', GEN),
        ("Investor-readiness score", f"={RDY}", '0.0" / 10"')]
LONG = [k for k in KPIS if k[0] in ("Milestones funded", "Next financing", "Valuation assessment", "Valuation assumptions")]
KPIS = [k for k in KPIS if k not in LONG]
for i, (lab, f, fmt_) in enumerate(KPIS):
    rr = kp + i; db.cell(rr, 8, lab); c = put(db, rr, 9, f, fmt_, GREEN, bold=True); c.alignment = Alignment(horizontal="right")
r = F_END + 2; sec(db, r, "WHAT THE ROUND FUNDS & HOW THE PRICE IS SUPPORTED", 9)
for lab, f, fmt_ in LONG:
    r += 1; db.cell(r, 1, lab).alignment = Alignment(vertical="top"); c = put(db, r, 2, f, fmt_, GREEN, bold=True)
    db.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9); c.alignment = Alignment(wrap_text=True, vertical="top"); db.row_dimensions[r].height = 30
F_END = r
ch = BarChart(); ch.type = "col"; ch.grouping = "stacked"; ch.overlap = 100; ch.title = "Forecast revenue by stream (EGP)"; ch.height = 7.5; ch.width = 16
data = Reference(wb["Income Statement"], min_col=2, max_col=7, min_row=ISR["comm"], max_row=ISR["spon"])
ch.add_data(data, from_rows=True, titles_from_data=False)
from openpyxl.chart.series import SeriesLabel
from openpyxl.chart.data_source import StrRef
for k_, s_ in enumerate(ch.series): s_.tx = SeriesLabel(strRef=StrRef(f"'Income Statement'!$A${ISR['comm'] + k_}"))
ch.set_categories(Reference(wb["Income Statement"], min_col=3, max_col=7, min_row=4))
for s_ in ch.series:
    s_.val.numRef.f = s_.val.numRef.f.replace("$B$", "$C$")
db.add_chart(ch, f"A{F_END + 3}")
lc = LineChart(); lc.title = "Forecast month-end cash, 60 months (EGP)"; lc.height = 7.5; lc.width = 16
lc.add_data(Reference(wb["Monthly Cash & Runway"], min_col=11, min_row=T0, max_row=T1), titles_from_data=True)
lc.set_categories(Reference(wb["Monthly Cash & Runway"], min_col=2, min_row=T0 + 1, max_row=T1))
db.add_chart(lc, f"E{F_END + 3}")

# ───────────── INVESTMENT SUMMARY ─────────────
smy = new_sheet("Investment Summary", "Reservya — One-Page Investment Summary", "All numbers live from the model. Selected scenario shown.", (46, 18, 18, 18, 18, 18))
r = 4
def sline(label, f, fmt_=GEN, bold=False):
    global r
    r += 1; smy.cell(r, 1, label).font = fnt(bold=bold); put(smy, r, 2, f, fmt_, GREEN, bold)
sec(smy, r, "THE COMPANY", 6)
for t in ["Reservya lets diners book a table, pre-order food and choose the minute it is served, and pay — before they arrive.",
          "Restaurants run the whole night from one dashboard: one subscription instead of 5–7 systems. Delivery is left to delivery apps.",
          "Company-reported (documents pending): live since 15 May 2026 on iOS, Android and web; 22+ venues tested; 2 years of build; EGP 2.7M invested by the founders."]:
    r += 1; smy.cell(r, 1, t)
r += 1; sec(smy, r + 1, "THE ASK", 6); r += 1
sline("Round size (USD)", f"={FSsel('raise')}", USD, True); sline("Investors / individual ticket", f'={FSsel("inv")}&" × "&TEXT({FSsel("perinv")},"$#,##0")'); sline("Pre-money — management proposal (USD)", f"={A['premoney']}", USD); sline("Post-money (USD)", f"={FSsel('post')}", USD)
sline("Investor ownership", f"={FSsel('own')}", PCT, True); sline("Valuation methods — range (USD)", f'=TEXT(Valuation!C{VA["lo"]},"$#,##0")&" – "&TEXT(Valuation!C{VA["hi"]},"$#,##0")&"  (median "&TEXT(Valuation!C{VA["med"]},"$#,##0")&")"')
sline("Valuation assessment", f"=Valuation!C{VA['verdict']}")
sline("What the round pays for", f"={FSsel('mil')}")
r += 1; sec(smy, r + 1, "THE PLAN — FORECAST, selected scenario (not results)", 6); r += 1
r += 1; hdr(smy, r, ["", "2027", "2028", "2029", "2030", "2031"])
for lab in ["Live restaurants (year end)", "Total revenue (USD)", "EBITDA margin", "Net profit (EGP)", "Closing cash (EGP)"]:
    r += 1; smy.cell(r, 1, lab)
    for j in range(5): put(smy, r, 2 + j, f"=Dashboard!{L(2+j)}{DBR[lab]}", db.cell(DBR[lab], 2).number_format, GREEN)
r += 1; sec(smy, r + 1, "RISKS & WHAT WE STILL NEED TO PROVE", 6); r += 1
for t in ["No operating history: bills per restaurant, churn and package adoption are assumptions until live data exists.",
          "Commission rate (4–7%) not yet confirmed restaurant by restaurant; each point moves revenue materially (see Commission Sensitivity).",
          "Gulf expansion depends on operating partners not yet signed.",
          "IP ownership and the EGP 2.7M contribution need documents before closing (see Due Diligence)."]:
    r += 1; smy.cell(r, 1, "• " + t)
r += 1; sline("Lowest cash in 60 months (EGP)", f"={MRS['mincash']}", EGP); sline("Downside: extra funding needed (USD)", f"={FSsel('d_need')}", USD); sline("Formula integrity", f"={CK_ALL}", GEN, True); sline("Evidence status", f'={EV_ALL}&" — "&{EV_VER}&" of "&{EV_MAT}&" material assumptions verified; "&{DD_OPEN}&" diligence items open"', GEN, True)

# ───────────── COVER ─────────────
cv = wb.create_sheet("Cover", 0); cv.sheet_view.showGridLines = False
cv.column_dimensions["A"].width = 4; cv.column_dimensions["B"].width = 38; cv.column_dimensions["C"].width = 90
cv["B2"] = "Reservya"; cv["B2"].font = fnt("1A2420", True, size=24)
cv["B3"] = "Integrated pre-seed financial model · 2027–2031 · EGP (USD where stated)"; cv["B3"].font = fnt("5A675F", size=11)
cv["B4"] = "Version 2.1 · November 2026 · projections, not audited · assumptions not yet evidence-verified"; cv["B4"].font = fnt("5A675F", italic=True, size=9)
cv["B6"] = "Model status"; cv["C6"] = f'="Formula checks: "&{CK_ALL}&" · Evidence: "&{EV_ALL}&" · Readiness "&TEXT({RDY},"0.0")&"/10"'; cv["C6"].font = fnt(GREEN, True)
cv["B7"] = "Selected scenarios"; cv["C7"] = f'={A["scen_name"]}&" operating · "&{A["comm_name"]}&" · funding "&CHOOSE({A["fundsel"]},"A ($100K)","B ($150K)","C ($250K)")'; cv["C7"].font = fnt(GREEN)
cv["B9"] = "Colour code"; cv["B9"].font = fnt(bold=True)
for i, (t, c_) in enumerate([("Blue text — input you can change", BLUE), ("Black text — formula on the same sheet", BLACK), ("Green text — link to another sheet", GREEN)]):
    cv.cell(10 + i, 2, t).font = fnt(c_)
cv["B13"] = "Yellow fill — key assumption"; cv["B13"].fill = YFILL
cv["B15"] = "Contents"; cv["B15"].font = fnt(bold=True)
CONTENTS = [("Dashboard", "KPIs and charts"), ("Investment Summary", "One-page summary for investors"), ("Assumptions", "All inputs and the three scenario selectors"),
            ("FX", "Exchange rates"), ("Countries", "Egypt, KSA, UAE, Jordan, Morocco assumptions & targets"), ("Opening BS", "Founder EGP 2.7M reconciliation and opening balance sheet"),
            ("Revenue & Monetization", "GMV, commission, subscriptions, marketing, sponsorships"), ("Country Economics", "Revenue and restaurants by country"),
            ("Opex & Headcount", "Team and cost schedule"), ("Income Statement", "Annual P&L"), ("Balance Sheet", "Annual balance sheet"), ("Cash Flow", "Annual cash flow"),
            ("Monthly Cash & Runway", "60-month cash, burn, shortfall flags"), ("Unit Economics", "CAC, LTV, payback, ARPA, NRR"), ("Funding Scenarios", "A / B / C compared"),
            ("Use of Funds", "Allocation per scenario"), ("Cap Table", "Ownership through seed and Series A"), ("Valuation", "Four methods and the verdict on $1.25M"),
            ("Commission Sensitivity", "4% / 5.5% / 7% / tier mix"), ("Scenarios", "Downside / Base / Upside"), ("Asset Register", "Software, IP, equipment, strategic assets"),
            ("Assumption Register", "Source, confidence, verification"), ("Methodology", "How it works"), ("Due Diligence", "Documents investors will ask for"), ("Checks", "Integrity checks"),
            ("Engine_Base", "Monthly engine (also Engine_Downside, Engine_Upside)")]
for i, (s_, d_) in enumerate(CONTENTS):
    c = cv.cell(16 + i, 2, s_); c.hyperlink = f"#'{s_}'!A1"; c.font = fnt("0563C1"); cv.cell(16 + i, 3, d_)
cv.cell(16 + len(CONTENTS) + 1, 2, "Important").font = fnt(bold=True)
cv.cell(16 + len(CONTENTS) + 2, 2, "Forward-looking projections built on management assumptions. No historical traction, contracts or values beyond those stated by the company are included. Verify inputs marked Low confidence before relying on them.").font = fnt("5A675F", italic=True, size=9)

# ───────────── ORDER & SAVE ─────────────
ORDER = ["Cover", "Dashboard", "Investment Summary", "Assumptions", "FX", "Countries", "Opening BS", "Revenue & Monetization", "Country Economics", "Opex & Headcount",
         "Income Statement", "Balance Sheet", "Cash Flow", "Monthly Cash & Runway", "Unit Economics", "Funding Scenarios", "Use of Funds", "Cap Table", "Valuation",
         "Commission Sensitivity", "Scenarios", "Asset Register", "Assumption Register", "Methodology", "Due Diligence", "Checks", "Engine_Base", "Engine_Downside", "Engine_Upside"]
wb._sheets = [wb[n] for n in ORDER]
wb.active = 0
wb.save(OUT); print("saved", OUT)
