"""Curated evidence base for The Bank of Punjab (PSX: BOP).

Every item carries the source and the date it was published so the assessment
can be audited and re-scored later.  The research was assembled on 2026-10-07
from public filings, exchange disclosures and press coverage; figures that could
not be corroborated by two independent sources are flagged.

This module is data, not prose: :mod:`psx.report` and :mod:`psx.agents` render
and reason over it.
"""

from __future__ import annotations

AS_OF = "2026-10-07"
SUBJECT = {
    "name": "The Bank of Punjab",
    "ticker_psx": "BOP",
    "ticker_yahoo": "BOP.KA",
    "isin": "PK0045001010",
    "sector": "Commercial Banks",
    "currency": "PKR",
    "shares_outstanding": 3.2716e9,
}

# --------------------------------------------------------------------------- #
# macro
# --------------------------------------------------------------------------- #
MACRO = [
    {
        "key": "policy_rate",
        "headline": "SBP policy rate 11.5%, on hold since the 100bp hike of 27 Apr 2026",
        "detail": (
            "The MPC held on 27 Jul and again on 14 Sep 2026 (7-10 majority). Corridor: "
            "ceiling 12.5%, floor 10.5%. The next decision is 26 Oct 2026 - the same day "
            "BOP is expected to report Q3 results."
        ),
        "source": "pakera.pk SBP calendar; Trading Economics; SBP MPC statements",
        "date": "2026-10-05",
        "direction": "neutral_to_negative",
    },
    {
        "key": "inflation",
        "headline": "CPI 10.26% y/y in Sep 2026 (Aug 11.1%), still above the 5-7% target band",
        "detail": (
            "Sep CPI rose 1.27% m/m with housing/electricity/gas +3.05%. The Jul-Sep average "
            "was 10.20%. FY27 inflation is projected near 7.5% at $80 oil and 8.2% at $100 oil."
        ),
        "source": "pakera.pk; archyde.com (citing Dawn), 2026-10-04",
        "date": "2026-10-05",
        "direction": "negative",
    },
    {
        "key": "rates_market",
        "headline": "Money market prices a hike: 1-year T-bill cut-off up to 12.49%, 12M KIBOR 12.68%",
        "detail": (
            "T-bill cut-offs rose by up to 75bp at the latest auction; on 5 Oct 2026 the 3M/6M/12M "
            "KIBOR offers were 11.97/12.39/12.68%. KIBOR sits above the policy rate, i.e. banks are "
            "not pricing a fast cut."
        ),
        "source": "pakera.pk; Tresmark commentary via archyde.com",
        "date": "2026-10-05",
        "direction": "negative",
    },
    {
        "key": "reserves",
        "headline": "SBP reserves $21.44bn (25 Sep 2026), total liquid $26.77bn, import cover >3 months",
        "detail": (
            "Reserves were lifted by a $3bn international bond issue and continued SBP FX purchases; "
            "the import cover threshold above three months had not been clearly crossed since 2020."
        ),
        "source": "Business Recorder, 2026-10-01; Eurasia Review, 2026-09-18",
        "date": "2026-10-01",
        "direction": "positive",
    },
    {
        "key": "imf_growth",
        "headline": "IMF projects FY27 GDP growth of 3.5% against the government's 4% target",
        "detail": (
            "Private credit grew ~13% y/y in H1-FY26 and LSM expanded 6.44% in Jul-Apr FY26, but the "
            "IMF warns that faster growth through consumption and imports would re-open the "
            "balance-of-payments gap. The rupee has been stable near Rs 277-278/USD; REER rose to "
            "106.15 in May 2026 (98.03 in Jun 2025)."
        ),
        "source": "Business Recorder editorial, 2026-07-16; BOP FX rate sheet, 2026-10-02",
        "date": "2026-07-16",
        "direction": "neutral",
    },
    {
        "key": "politics",
        "headline": "Government-PTI standoff and the long march are the live domestic risk factor",
        "detail": (
            "The KSE-100 fell 2,288 points (-1.36%) on 5 Oct 2026 amid political noise and "
            "speculation about constitutional measures, with oil at $101-103/bbl and renewed "
            "Strait of Hormuz / Red Sea tension adding to risk aversion."
        ),
        "source": "The Express Tribune, 2026-10-06; pakera.pk, 2026-10-05",
        "date": "2026-10-06",
        "direction": "negative",
    },
]

# --------------------------------------------------------------------------- #
# sector
# --------------------------------------------------------------------------- #
SECTOR = [
    {
        "key": "deposits",
        "headline": "System deposits Rs 39.24trn (+13.9% y/y) in Aug 2026; advances Rs 13.61trn (+10.7%)",
        "detail": (
            "Investments rose 13.4% y/y to Rs 41.19trn, leaving the investment-to-deposit ratio above "
            "100%. Deposits are compounding at roughly Rs 6bn per day; Topline expects 10-15% deposit "
            "growth in 2026."
        ),
        "source": "Topline Securities via Pro Pakistani 2026-10-05 / 24NewsHD 2026-10-06",
        "date": "2026-10-05",
        "direction": "positive",
    },
    {
        "key": "adr",
        "headline": "System ADR stuck at 34.7% (35.7% a year earlier) - lending is not keeping pace",
        "detail": (
            "A rate-peak/high-rate environment keeps banks parked in government paper. For BOP this is "
            "a relative advantage: management reports gross advances +28% y/y to Rs 996bn in H1-2026; "
            "the implied ADR is ~46%, and scstrade's balance-sheet snapshot independently puts BOP's "
            "ADR at 44.17% with loans above 11% of assets - both well above the system."
        ),
        "source": "Topline Securities; BOP H1-2026 results release",
        "date": "2026-10-05",
        "direction": "neutral",
    },
    {
        "key": "tax",
        "headline": "Bank corporate tax steps down to 42% for TY2027; 10% super tax above Rs 150mn remains",
        "detail": (
            "The 15% ADR-linked additional tax was scrapped by ordinance in Dec 2024 and replaced by a "
            "flat rate: 44% (TY2025) -> 43% (TY2026) -> 42% (TY2027). The Finance Act 2026-27 keeps the "
            "10% super tax on banking-company income above Rs 150mn, so the effective marginal burden "
            "for large banks stays near 50%-plus."
        ),
        "source": "The News / Express Tribune (Dec 2024); pkrevenue.com 2026-07-19; PwC Finance Bill 2026 memo",
        "date": "2026-07-19",
        "direction": "neutral_to_positive",
    },
]

# --------------------------------------------------------------------------- #
# company
# --------------------------------------------------------------------------- #
COMPANY = [
    {
        "key": "h1_2026",
        "headline": "Record H1-2026: operating profit Rs 22.5bn (+67%), PBT Rs 20.5bn (+35%), PAT Rs 9.5bn (+40%)",
        "detail": (
            "Net interest income Rs 46.1bn (+29%); non-markup income ex-gains Rs 11.9bn (+61%); "
            "cost-to-income improved 2.40pp. Total assets Rs 2,504bn; deposits Rs 2,154bn with current "
            "deposits +20% y/y (average current deposits +26%); gross advances Rs 996bn (+28%). "
            "CAR 13.69%, leverage ratio 3.65%. Highest-ever interim dividend of 16% (Rs 1.60/share)."
        ),
        "source": "BOP press release via Pro Pakistani / Dawn / The Nation / Khyber News, 2026-08-28/31",
        "date": "2026-08-28",
        "direction": "positive",
    },
    {
        "key": "q2_2026",
        "headline": "Quarterly PAT: Q2-2026 Rs 4.756bn, 5% below Q2-2025 (Rs 5.007bn) as Q1 carried H1 growth",
        "detail": (
            "Q1-2026 was Rs 4.774bn, so the two quarters were almost identical and the +40% H1 "
            "headline is front-loaded: Q2-2025 (Rs 5.007bn) was the strongest quarter of last year "
            "and Q3-2025 (Rs 5.145bn) was higher still. Read the H1 'record' as a level shift, not "
            "as accelerating sequential momentum: the YoY comparison gets harder into Q3 "
            "(results expected 26 Oct 2026)."
        ),
        "source": "PSX company financials (dps.psx.com.pk) via the quarterly PAT series",
        "date": "2026-08-28",
        "direction": "neutral_to_negative",
    },
    {
        "key": "rating",
        "headline": "PACRA upgraded BOP to AAA (long term) with A1+ short term, stable outlook, on 1 Jul 2026",
        "detail": (
            "The first and only provincial bank in Pakistan at the top rating; the agency cited the "
            "stronger deposit franchise (deposits crossed PKR 2trn in 2025) and operating profit before "
            "credit-loss allowance that nearly doubled, +98.5% to Rs 40.7bn in 2025."
        ),
        "source": "PACRA via Profit/Tribune/Mettis Global, 2026-07-01",
        "date": "2026-07-01",
        "direction": "positive",
    },
    {
        "key": "capital_injection",
        "headline": "Shareholders approved up to Rs 30bn of equity from the Government of Punjab at a PKR 38.20 floor",
        "detail": (
            "Issuance price is the HIGHER of PKR 38.20 (KPMG base case, ~20% above the audited break-up "
            "value of PKR 31.83) or market price plus a 5% premium. GoPb's stake would rise from 57.47% "
            "to 65.71%. Phasing: PKR 15-20bn of shares by 31 Dec 2026, the remaining PKR 10-15bn by "
            "30 Jun 2027, subject to SBP/SECP approvals. The bank describes it as growth capital; it is "
            "the lowest-capitalised of Pakistan's ten largest banks (Tier-1 PKR 99.9bn against total "
            "assets of PKR 2,952bn; on a fully-injected basis it would still rank ninth). The dilution "
            "mechanics matter for the next two quarters: up to ~24% more shares would mechanically cut "
            "EPS and ROE until the capital is deployed, while issuing *above* book lifts BVPS for "
            "holders who do not subscribe. At PKR 38.20 the issue is priced at a premium not just to "
            "book but to the market - unusual, since roughly 80% of recent rights issues in Pakistan "
            "have been priced at a discount to the prevailing price."
        ),
        "source": "BOP EOGM disclosure; Daily Times / The Friday Times / Pro Pakistani, 2026-09-08/09",
        "date": "2026-09-08",
        "direction": "positive",
    },
    {
        "key": "disclosure_timing",
        "headline": "The equity plan was preceded by unusual trading: +9% on ~158mn shares in the three sessions to 7 Aug",
        "detail": (
            "The board's 334th emergent meeting on 7 Aug 2026 approved the injection, and PSX was told "
            "three days later (10 Aug). In the run-up, 5-7 Aug volumes reached ~158mn shares - roughly "
            "six times normal, including 66mn on 6 Aug alone - with the price up ~9% and closing at "
            "36.00; on disclosure day the stock was ~35.75 on 9.4mn shares. No finding of wrongdoing "
            "has been published, but the pattern is a governance flag for anyone underwriting the "
            "stock at these levels."
        ),
        "source": "Bloom Pakistan / PSX disclosures, 2026-08-10",
        "date": "2026-08-10",
        "direction": "negative",
    },
    {
        "key": "dividends",
        "headline": "Interim dividend of 16% declared with H1-2026, dispatched 24 Sep 2026; ex-date 10 Sep 2026",
        "detail": (
            "Trailing DPS is ~Rs 3.10 (Rs 1.50 final for CY25, ex 19 Mar 2026, plus the Rs 1.60 "
            "interim, ex 10 Sep 2026) on a Rs 10 face value: a yield near 10.4% at PKR 29.72 and the "
            "highest payout in the bank's history (CY25 total Rs 2.50 versus Rs 1.80 for CY24). BOP "
            "has paid more than PKR 15bn of dividends since 2021 - roughly 45% of earnings - and the "
            "Sep-2026 interim alone was PKR 3bn."
        ),
        "source": "PSX company announcements (dps.psx.com.pk); Profit/Cybernet; stockanalysis.com",
        "date": "2026-09-24",
        "direction": "positive",
    },
    {
        "key": "franchise",
        "headline": "Largest SME, agriculture, low-cost housing and women-entrepreneurship lender; largest card issuer",
        "detail": (
            "Government-of-Punjab schemes total PKR 182bn, about 18% of the portfolio, of which more "
            "than 17% is government-guaranteed; these schemes account for only 3% of non-performing "
            "loans with recovery rates of 97-100%. CEO Zafar Masud's contract was extended by a year "
            "from 16 Apr 2026; the bank is opening a Bahrain wholesale unit."
        ),
        "source": "BOP release; Business Recorder trends; Pro Pakistani 2026-04-14",
        "date": "2026-08-06",
        "direction": "positive",
    },
    {
        "key": "governance_risk",
        "headline": "Majority government ownership is the structural risk: 57.47% Punjab government stake",
        "detail": (
            "The state connection underwrites deposits and guarantees, but it also ties the bank to "
            "provincial fiscal health, administration changes and directed-lending schemes. "
            "Independent analyses put the NPL ratio near 8% versus under 4% at the best private peers."
        ),
        "source": "koalagains.com stock analysis; BOP EOGM materials",
        "date": "2026-09-08",
        "direction": "negative",
    },
]

# --------------------------------------------------------------------------- #
# market / technical
# --------------------------------------------------------------------------- #
MARKET = [
    {
        "key": "index",
        "headline": "KSE-100: 165,867 on 5 Oct (-1.36%), 168,460 on 6 Oct (+1.56%), ~169,150 intraday on 7 Oct",
        "detail": (
            "The index is ~11.8% below its 191,033 all-time high and -2.98% over one month, but +1.4% "
            "over twelve months. Banks led the 5 Oct sell-off, accounting for ~635 of the 2,288 points "
            "lost; BOP was among the volume leaders. Foreign selling was small (Rs 45mn on 5 Oct). "
            "Trading Economics models the index at 160,506 by the end of Q4 2026."
        ),
        "source": "Trading Economics; The Express Tribune 2026-10-06; brecorder",
        "date": "2026-10-07",
        "direction": "negative",
    },
    {
        "key": "consensus",
        "headline": "Consensus is a Strong Buy with a 12-month target of Rs 44.60 (two analysts)",
        "detail": (
            "The target implies ~50% upside from Rs 29.72 and sits at the all-time high. Independent "
            "model-based fair-value work arrives at PKR 39.9-44.2 using peer P/E of ~8x and P/B of 1.5x."
        ),
        "source": "stockanalysis.com; koalagains.com",
        "date": "2026-09-08",
        "direction": "positive",
    },
    {
        "key": "valuation",
        "headline": "At Rs 29.72 the stock trades at ~0.93x audited book (PKR 31.83) and ~5.3x TTM EPS of 5.59",
        "detail": (
            "Market capitalisation is roughly PKR 97bn (3.2716bn shares), versus PKR 126bn at the "
            "end of 2025 after a 256% year. Reported book value per share was 32.77 at 2Q-2026 "
            "(31.83 audited at end-2025), TBVPS 28.63 and ROE 21.07%; the P/E was 7.11x on trailing "
            "earnings at an earlier price and screens near 5.95x on expected earnings. The dividend "
            "yield on a ~Rs 3.10 trailing DPS is ~10.4%. Beta is reported between 1.19 (5-year) and "
            "2.17 (1-year) - the spread itself signals how much of the 2025 re-rating was "
            "index-independent momentum."
        ),
        "source": "stockanalysis.com; scstrade.com; koalagains.com; TradingView",
        "date": "2026-10-07",
        "direction": "positive",
    },
    {
        "key": "history",
        "headline": "Five-year arc: 3.42 trough (mid-2023) -> 5.82 (Oct 2024) -> 44.17 peak (Jan 2026) -> 28.89 today",
        "detail": (
            "Monthly closes tell the re-rating story: the stock spent mid-2023 near 3.4, broke out "
            "through 9-11 in late 2024, and accelerated through 14-15 (mid-2025) to 27.15 (Sep 2025), "
            "34.77 (Oct 2025) and a 38.88 monthly peak before the 44.17 intraday high in January "
            "2026. The correction since has retraced to the 24-31 area - still ~8x the 2023 trough. "
            "For a one-month view this matters mainly as a reminder that the stock's beta to market "
            "sentiment is high in both directions."
        ),
        "source": "Yahoo Finance monthly series (5y chart, fetched 2026-10-07)",
        "date": "2026-10-07",
        "direction": "neutral",
    },
    {
        "key": "technicals",
        "headline": "Price is below every major moving average after a 31% drawdown from the January peak",
        "detail": (
            "20/50/100/200-day levels are ~30.7/32.8/33.7/34.0; RSI(14) ~36; MACD is negative but the "
            "histogram is flattening. The 6 Oct session reversed off 28.55 to close at 29.72, and the "
            "5 Oct low of 28.89 had a -3.48% down day's volume of only 7.3mn shares versus a three-month "
            "average near 19.5mn - the selling is drying up rather than accelerating."
        ),
        "source": "computed from the validated daily OHLCV snapshot in data/",
        "date": "2026-10-06",
        "direction": "neutral",
    },
]

EVENTS = [
    {"date": "2026-10-26", "event": "BOP Q3-2026 results AND the SBP MPC decision land on the SAME DAY - a double event inside the forecast window"},
    {"date": "2026-11-06", "event": "30-day forecast horizon end"},
    {"date": "2026-12-31", "event": "Deadline for the first GoPb tranche (Rs 15-20bn of shares)"},
]

RISKS = [
    ("Double event on 26 Oct", "Q3 results and the MPC land together: a hawkish hold/hike and a soft Q3 (the Q2-2025 comparison base is high) could compound in one session.", "high"),
    ("Hawkish SBP surprise", "1-year T-bill cut-offs and KIBOR already price a hike; a 100bp move would pressure the index and, near-term, bank multiples.", "high"),
    ("Political escalation", "The government-PTI standoff or constitutional manoeuvring can dominate stock-specific factors in a market where banks are ~25% of the index.", "high"),
    ("Asset quality", "An ~8% NPL ratio leaves BOP more exposed than private peers if Punjab-scheme or SME borrowers deteriorate; the schemes are only 3% of NPLs today.", "medium"),
    ("Dilution optics", "Up to ~24% more shares would mechanically cut EPS/ROE until the capital is deployed; the offset is that issuance above book lifts BVPS, and ~80% of recent rights issues were priced at discounts rather than the PKR 38.20 premium here.", "medium"),
    ("Capital-raise slippage", "Any delay past 31 Dec 2026 in the GoPb tranche would revive capital-adequacy and dilution concerns; SBP and SECP approvals are still pending.", "medium"),
    ("Disclosure timing", "The +9%/158mn-share run-up before the injection was made public is a governance flag that could weigh on how investors price the state's influence.", "low"),
    ("Liquidity/float", "Free float is ~42.5%, so index events and foreign flows can move the stock harder than its fundamentals justify; 1-year beta is reported at 2.17.", "medium"),
]

SCORECARD = {
    "valuation": (8, "0.93x audited book (BVPS 32.77 at 2Q-2026), ~5.3x TTM / ~6x forward earnings, ~10.4% dividend yield versus a 44.60 consensus target and a 38.20 contracted issue price."),
    "earnings_momentum": (7, "H1-2026 PAT +40% y/y and operating profit +67%, but Q2-2026 was 5% BELOW Q2-2025 - the growth is front-loaded and the Q3 comparison is harder."),
    "balance_sheet": (6, "CAR 13.69% is adequate but the thinnest of the large banks (Tier-1 Rs 99.9bn against Rs 2,952bn of assets); the injection fixes that, subject to approvals."),
    "franchise": (7, "PACRA AAA, policy-driven priority-sector dominance, ADR ~44-46% versus 34.7% system, largest card issuer - but concentrated in one province."),
    "macro_tailwind": (5, "Reserves and rating upgrades are supportive; inflation at 10.3% and a possible hike are not."),
    "technical": (4, "Downtrend below all moving averages, but oversold, with the last two sessions showing accumulation-style reversals."),
    "sentiment": (5, "Consensus Strong Buy with a 44.60 target contrasts with a market punished by political risk; flow data show only token foreign selling."),
    "governance": (5, "AAA-rated and professionally run, yet 57.47% government-owned with directed-lending exposure - and the +9% run-up before the injection was disclosed."),
}
