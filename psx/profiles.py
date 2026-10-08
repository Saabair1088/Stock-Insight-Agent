"""Per-ticker profiles: everything the generic engine needs to know about a name.

A :class:`Profile` carries the identity, valuation anchors, price levels,
evidence base (company / sector / macro facts), scorecard inputs, the
scenario book, the forecast thresholds and the role-specific commentary that
the committee and the report writer use.  Adding a new PSX name means adding a
profile here - the engine itself is ticker-agnostic (see ``psx.analysts`` and
``psx.brief``).

Numbers are sourced from the evidence gathered on 2026-10-07/08 and are
recorded with their source in ``Profile.sources``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _p(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


@dataclass(frozen=True)
class Profile:
    # ---- identity ----------------------------------------------------------
    symbol: str                 # Yahoo-style symbol, e.g. "PSO.KA"
    ticker: str                 # PSX ticker, e.g. "PSO"
    name: str
    short_name: str
    sector: str
    business: str               # one-line "what it does"
    as_of: str                  # report date
    spot_date: str              # last settled session
    horizon_end: str
    horizon_sessions: int
    # ---- data --------------------------------------------------------------
    closes_path: str | None     # timestamps + closes
    ohlcv_path: str             # OHLCV rows for volume/ATR/swings
    long_arc_path: str | None = None   # monthly closes (long arc / long-MA proxy)
    long_arc_label: str = ""
    data_caveats: list[str] = field(default_factory=list)
    # ---- valuation / fundamentals -----------------------------------------
    shares_out: float = 0.0
    quote: dict = field(default_factory=dict)       # pe, pb, bvps, dividend, yield, target, beta, ...
    facts: dict = field(default_factory=dict)       # free-form headline numbers used in prose
    score_components: list = field(default_factory=list)
    # ---- price levels ------------------------------------------------------
    levels: dict = field(default_factory=dict)
    # ---- evidence ----------------------------------------------------------
    company: list = field(default_factory=list)     # [{"fact","source","date","direction"}]
    sector_facts: list = field(default_factory=list)
    macro: list = field(default_factory=list)
    events: list = field(default_factory=list)      # [{"date","event","why"}]
    risks: list = field(default_factory=list)       # [{"risk","why","severity","detail"}]
    scorecard: list = field(default_factory=list)   # [{"dimension","score","comment"}]
    falsification: list = field(default_factory=list)
    # ---- forecast configuration -------------------------------------------
    cash_events: list = field(default_factory=list)
    thresholds: list = field(default_factory=list)  # [{"label","price","above"|"below"}]
    scenarios: list = field(default_factory=list)   # [{"name","probability","range","midpoint","triggers"}]
    regime_weights: dict = field(default_factory=dict)
    # ---- committee commentary ---------------------------------------------
    bull: list = field(default_factory=list)
    bear: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)       # market/fundamentals/news/sentiment/manager/trader/risk/pm
    sources: list = field(default_factory=list)

    # ---- helpers -----------------------------------------------------------
    @property
    def spot_label(self) -> str:
        return f"PKR {self.quote.get('spot', 0):.2f}"

    def anchor(self, key: str, default: float = 0.0) -> float:
        return float(self.levels.get(key, default))


# --------------------------------------------------------------------------- #
# PSO - Pakistan State Oil
# --------------------------------------------------------------------------- #
PSO = Profile(
    symbol="PSO.KA",
    ticker="PSO",
    name="Pakistan State Oil Company Limited",
    short_name="Pakistan State Oil",
    sector="Oil & Gas Marketing Companies (OMC)",
    business="Pakistan's largest fuel marketer: petrol, diesel, jet fuel, lubricants, LPG and LNG, "
             "plus a 63.6% stake in Pakistan Refinery Limited.",
    as_of="2026-10-07",
    spot_date="2026-10-07",
    horizon_end="2026-11-06",
    horizon_sessions=22,
    closes_path=_p("data", "psx", "PSO_KA_daily_ytd_closes.json"),
    ohlcv_path=_p("data", "psx", "PSO_KA_daily_6mo.json"),
    long_arc_path=_p("data", "psx", "PSO_KA_monthly_5y.json"),
    long_arc_label="Yahoo monthly, 5 years",
    data_caveats=[
        "The model applies the full dividend as a step down on the ex-date, which is the textbook treatment; PSX high-yield names often give back less than the full amount on the day, so treat the price median as the conservative case and the total-return probability as the decision number.", 
        "Yahoo's PSO feed lags by up to two sessions: the 6-7 Oct 2026 closes are taken from "
        "stockanalysis.com and cross-checked against sarmaaya.pk's 8 Oct quote (previous close 355.86).",
        "The daily series contains a handful of padded rows for PSX holidays (zero-change closes); "
        "they are de-duplicated on ingest and the effect on volatility is negligible.",
        "The long-term moving-average reference is proxied by the 10-month moving average of the "
        "5-year monthly series because the environment's daily history starts in January 2026; the "
        "proxy (PKR ~377) sits within 1.5% of the 200-day average reported by stockanalysis (382.59).",
    ],
    shares_out=469.47e6,
    quote={
        "spot": 355.86,
        "pe": 6.55,
        "pe_forward": 5.97,
        "pb": 0.58,
        "bvps": 592.43,
        "dividend": 10.00,
        "dividend_yield": 0.0281,
        "payout": 0.181,
        "target": 697.00,
        "analysts": 6,
        "consensus": "Strong Buy",
        "beta": 0.46,
        "mcap": 167.07e9,
        "ev": 550.61e9,
        "equity": 290.40e9,
        "net_debt": 371.24e9,
        "roe": 0.1142,
        "roce": 0.329,
        "float_pct": 0.674,
        "week52_low": 320.11,
        "week52_high": 506.75,
        "ytd": -0.254,
    },
    facts={
        "fy26_standalone_pat": 15.07e9,
        "fy26_standalone_eps": 32.10,
        "fy26_consolidated_pat": 25.49e9,
        "fy26_consolidated_eps": 54.29,
        "fy25_eps": 44.54,
        "fy24_eps": 33.79,
        "fy26_revenue": 3.21e12,
        "fy26_gross_profit": 99.9e9,
        "fy26_gross_profit_ex_lng_growth": 0.205,
        "fy26_tax": 40.22e9,
        "fy25_tax": 19.03e9,
        "q4fy26_loss": -23e9,
        "lng_swing": -10.7e9,
        "lng_cargoes_q4": 6,
        "lng_cargoes_q4_prior": 28,
        "receivables": 414.8e9,
        "receivables_prior": 437.5e9,
        "sngpl_receivable_drop": 34.3e9,
        "finance_cost_change": -0.24,
        "white_oil_share": 0.427,
        "jet_fuel_share": 0.99,
        "retail_outlets": 3688,
        "storage_mmt": 1.23,
        "prl_stake": 0.636,
        "gop_direct": 0.2247,
        "gop_effective": 0.51,
    },
    score_components=[
        {"name": "Price / book (0.58x against a 0.9x-2.0x band)", "value": 0.58,
         "good": 0.90, "bad": 2.00, "higher_is_better": False, "weight": 0.30},
        {"name": "Price / earnings (6.6x consolidated, 11.1x standalone)", "value": 6.55,
         "good": 4.0, "bad": 12.0, "higher_is_better": False, "weight": 0.25},
        {"name": "Earnings momentum (FY26 standalone -28% y/y, Q4 loss)", "value": -0.28,
         "good": 0.30, "bad": -0.35, "higher_is_better": True, "weight": 0.20},
        {"name": "Balance sheet (net debt Rs 371bn against Rs 290bn of equity)",
         "value": 371.24 / 290.40, "good": 0.3, "bad": 1.6, "higher_is_better": False, "weight": 0.15},
        {"name": "Shareholder return (2.8% yield, 18% payout, no dilution)",
         "value": 0.028, "good": 0.08, "bad": 0.00, "higher_is_better": True, "weight": 0.10},
    ],
    levels={
        "support": 337.07,
        "support_label": "Feb-Mar 2026 base (337-340)",
        "deeper_support": 320.11,
        "resistance": 382.59,
        "resistance_label": "200-day average",
        "resistance_2": 434.00,
        "book": 592.43,
        "long_ma": 377.0,
        "week52_low": 320.11,
        "week52_high": 506.75,
        "target": 697.00,
    },
    company=[
        {"fact": "FY26 standalone profit fell 28% to Rs 15.07bn (EPS 32.10 from 44.54) after a "
                 "~Rs 23bn net loss in Q4 - inventory losses as fuel prices fell and only 6 LNG "
                 "cargoes versus 28 a year earlier.",
         "source": "BR Research / PSX annual financials", "date": "2026-09-28", "direction": "negative"},
        {"fact": "Group profit attributable to PSO rose 55% to Rs 25.49bn (EPS 54.29); gross profit "
                 "rose 3% to Rs 99.9bn and gross profit excluding LNG rose 20.5% to Rs 81.9bn.",
         "source": "PSO FY26 results / Business Recorder", "date": "2026-09-25", "direction": "positive"},
        {"fact": "Trade receivables fell to Rs 414.8bn from Rs 437.5bn, with SNGPL alone down "
                 "Rs 34.3bn; lower discount rates cut finance costs 24%.",
         "source": "PSO FY26 results release", "date": "2026-09-25", "direction": "positive"},
        {"fact": "Final dividend of Rs 10/share approved for FY26 (ex-date 20 Oct 2026, paid 19 Nov) "
                 "- the fourth consecutive year at Rs 10.",
         "source": "PSO board decision / stockanalysis.com", "date": "2026-09-25", "direction": "positive"},
        {"fact": "White-oil market share slipped to ~42.7% with motor-gasoline volumes down ~5% and "
                 "diesel ~6% y/y as smaller OMCs gained ground.",
         "source": "BR Research", "date": "2026-09-28", "direction": "negative"},
        {"fact": "PSO holds 63.6% of Pakistan Refinery Limited, whose brownfield upgrade will double "
                 "capacity to 100,000 bpd and drop furnace oil; the Faisalabad-Tarujabba white-oil "
                 "pipeline consortium with SOCAR and FWO is at an advanced shareholding stage.",
         "source": "PSO FY26 annual report", "date": "2026-10-05", "direction": "positive"},
    ],
    sector_facts=[
        {"fact": "OMC volumes are shrinking: industry motor-gasoline and diesel sales fell ~5-6% y/y "
                 "in FY26 while PSO lost ~1pp of white-oil share to smaller players.",
         "source": "BR Research", "date": "2026-09-28", "direction": "negative"},
        {"fact": "LNG throughput collapsed - only 6 cargoes were handled in Q4FY26 against 28 a year "
                 "earlier, the single biggest drag on the reported result.",
         "source": "BR Research / PSO FY26 release", "date": "2026-09-28", "direction": "negative"},
        {"fact": "The sector's structural problem is circular debt: PSO's Rs 415bn receivable book is "
                 "mostly owed by state gas and power entities.",
         "source": "PSO FY26 release; Business Recorder", "date": "2026-09-25", "direction": "negative"},
    ],
    macro=[
        {"headline": "SBP on hold at 11.5%", "detail": "No change since the 100bp hike of 27 Apr 2026; "
         "the 26 Oct MPC is the next binary and the money market leans hawkish (12M KIBOR 12.68%).",
         "direction": "neutral"},
        {"headline": "Inflation 10.26% y/y in September", "detail": "Above the 5-7% target band, which "
         "keeps the policy rate high and squeezes fuel demand.", "direction": "negative"},
        {"headline": "Crude has been violent: a Middle-East escalation and the temporary Strait of "
                     "Hormuz closure in Q3FY26, then a retreat that cost PSO its Q4 inventory losses",
         "detail": "Oil was quoted around $101-103/bbl in early October; for an OMC, flat-to-rising "
         "prices are inventory-neutral while sharp falls trigger write-downs.", "direction": "neutral"},
        {"headline": "Reserves $21.44bn with 3+ months of import cover", "detail": "Import cover "
         "removes the 2022-23 style FX-shortage tail risk for a company that imports most of its "
         "product.", "direction": "positive"},
        {"headline": "Politics dominates the index", "detail": "The government-PTI standoff and the "
         "protest marches knocked the KSE-100 12% off its high; energy names are ~25% of index weight.",
         "direction": "negative"},
    ],
    events=[
        {"date": "2026-10-20", "event": "Ex-dividend: Rs 10/share (2.8% of the price)",
         "why": "The stock drops by the dividend mechanically; income buyers step in afterwards, "
                "payment lands 19 Nov."},
        {"date": "late Oct 2026", "event": "Q1 FY27 results (board meeting date to be announced)",
         "why": "First clean read on FY27: whether Q4's inventory loss was a one-off and whether LNG "
                "cargoes have recovered."},
        {"date": "2026-10-26", "event": "SBP monetary policy decision",
         "why": "A hike would pressure demand and index multiples; a hold with a neutral statement is "
                "the base case and would help the whole energy complex."},
        {"date": "through the window", "event": "Circular-debt / pricing news flow",
         "why": "Any settlement that converts receivables into cash or equity is the single largest "
                "possible re-rating trigger."},
    ],
    risks=[
        {"risk": "Q4's Rs 23bn inventory loss was not a one-off", "severity": "high",
         "why": "PSO's marketing book carries large product inventory; another sharp fall in prices, "
                "or another quarter of 6 LNG cargoes, would wipe out the FY27 consensus."},
        {"risk": "Structural volume decline", "severity": "medium",
         "why": "Motor-gasoline -5% and diesel -6% with market share slipping to 42-43% means the core "
                "engine is shrinking even before EV and solar substitution bite."},
        {"risk": "Circular debt", "severity": "high",
         "why": "Rs 415bn of receivables, mostly state-related, fund somebody else's balance sheet; "
                "the effective tax rate of 60% shows how much of the profit is claimed by the fisc."},
        {"risk": "Hawkish SBP surprise on 26 Oct", "severity": "medium",
         "why": "A 100bp hike would hit fuel demand, working-capital costs and the index multiple in "
                "one move."},
        {"risk": "Political escalation", "severity": "high",
         "why": "Energy is a quarter of the index and PSO is its most liquid name; the political "
                "channel can override a 0.58x book value for weeks."},
        {"risk": "LNG take-or-pay exposure", "severity": "medium",
         "why": "Qatar contract obligations run regardless of offtake; if demand stays weak, the LNG "
                "segment keeps leaking."},
    ],
    scorecard=[
        {"dimension": "Valuation", "score": 9,
         "comment": "0.58x book (BVPS 592.43), 6.6x consolidated earnings, 4.7x EV/EBITDA and a 15.3% "
                    "earnings yield: the cheapest large energy balance sheet on the exchange."},
        {"dimension": "Earnings momentum", "score": 3,
         "comment": "FY26 standalone -28% with a Rs 23bn Q4 loss; the group number (+55%) flatters the "
                    "core because it leans on subsidiaries and associates."},
        {"dimension": "Balance sheet", "score": 6,
         "comment": "Rs 290bn of equity against Rs 371bn net debt, and a Rs 415bn receivable book that "
                    "is a claim on the state rather than on customers."},
        {"dimension": "Franchise", "score": 9,
         "comment": "42.7% of white oil, 99% of jet fuel, 3,688 outlets, 1.23mn MT of storage, 63.6% of "
                    "PRL and a pipeline stake - national infrastructure, not just a retailer."},
        {"dimension": "Macro tailwind", "score": 5,
         "comment": "Stable FX and falling finance costs help; 10.3% inflation and a possible hike do not."},
        {"dimension": "Technical", "score": 5,
         "comment": "Above the 50-day (354) but below the 200-day (382.6); the 337-340 base has held "
                    "three times in 2026; RSI 55 is neutral."},
        {"dimension": "Sentiment", "score": 6,
         "comment": "Six analysts at Strong Buy with a Rs 697 target (+96%) against a stock that is "
                    "25% down in a year: positioning is washed out, catalysts are absent."},
        {"dimension": "Governance", "score": 6,
         "comment": "51% state-controlled through direct and indirect holdings; pricing and procurement "
                    "are political, and the government is both the largest shareholder and the largest "
                    "debtor."},
    ],
    falsification=[
        "A weekly close above the 200-day average (PKR ~382.6) would flip the trend and shift the "
        "model's mean-reversion leg from resistance to support.",
        "Q1 FY27 (late October) returning to a net loss, or another quarter of 6-8 LNG cargoes, would "
        "prove the Q4 damage structural rather than a timing artefact.",
        "Announcement of a circular-debt settlement - cash, a Sukuk, or a debt-for-equity swap - is the "
        "one event that would justify re-rating the book value.",
        "A 100bp hike on 26 October combined with a KSE-100 close below 160,000 would hand the tape to "
        "the political channel; the position should be cut to the conservative size.",
        "A crude spike back through $110/bbl would lift working-capital needs and, if it reverses "
        "sharply afterwards, recreate the Q4 inventory-loss setup.",
    ],
    cash_events=[
        {"session": 9, "amount": 10.00, "label": "FY26 final dividend, ex-date 2026-10-20"},
    ],
    thresholds=[
        {"label": "PKR 320.11 (52-week low)", "price": 320.11, "side": "above"},
        {"label": "PKR 337.07 (2026 base)", "price": 337.07, "side": "above"},
        {"label": "PKR 382.59 (200-day average)", "price": 382.59, "side": "above"},
        {"label": "PKR 400.00 (Feb-2026 breakdown)", "price": 400.00, "side": "above"},
        {"label": "PKR 434.00 (April-2026 high)", "price": 434.00, "side": "above"},
        {"label": "PKR 506.75 (52-week high)", "price": 506.75, "side": "above"},
        {"label": "PKR 592.43 (book value per share)", "price": 592.43, "side": "above"},
        {"label": "PKR 337.00 (2026 base, downside)", "price": 337.00, "side": "below"},
        {"label": "PKR 320.11 (52-week low, downside)", "price": 320.11, "side": "below"},
    ],
    scenarios=[
        {"name": "Bull - circular-debt progress and a clean Q1", "probability": 0.25,
         "range": (370.0, 420.0), "midpoint": 395.0,
         "triggers": ["Q1 FY27 profit back above Rs 8bn with no inventory loss",
                      "circular-debt settlement announced or SNGPL receipts accelerate",
                      "SBP holds at 11.5% with a neutral statement on 26 Oct",
                      "LNG throughput recovers toward 10+ cargoes a quarter"]},
        {"name": "Base - grinding sideways above the 2026 base", "probability": 0.50,
         "range": (340.0, 380.0), "midpoint": 360.0,
         "triggers": ["Q1 FY27 in the Rs 4-8bn range; volumes still soft but stabilising",
                      "Rs 10 dividend paid, no new surprises",
                      "KSE-100 range-bound 160,000-172,000 as the political standoff drags",
                      "crude flat, so no new inventory shock"]},
        {"name": "Bear - political risk plus another weak quarter", "probability": 0.25,
         "range": (300.0, 340.0), "midpoint": 322.0,
         "triggers": ["SBP hikes on 26 Oct or the statement re-opens tightening",
                      "Q1 FY27 shows a second consecutive loss / LNG stays at 6 cargoes",
                      "KSE-100 breaks 160,000 on political escalation",
                      "crude falls sharply, forcing another inventory write-down"]},
    ],
    regime_weights={"martingale": 0.35, "mean_reversion": 0.45, "catalyst": 0.20},
    bull=[
        "**Valuation is the anchor.** 0.58x book (BVPS 592.43), 6.6x consolidated earnings, 4.7x "
        "EV/EBITDA and a 15% earnings yield. You are buying the country's fuel logistics network for "
        "less than the value of its inventory, storage and refinery stake.",
        "**The Q4 loss is a trading artefact, not a broken business.** Gross profit excluding LNG still "
        "rose 20.5% to Rs 81.9bn in FY26; the ~Rs 23bn Q4 hit came from marking down inventory as "
        "prices fell, and it reverses when prices stabilise.",
        "**Receivables are finally moving the right way:** Rs 437.5bn to Rs 414.8bn, SNGPL down "
        "Rs 34.3bn, and finance costs down 24% as rates ease. Every rupee collected is a rupee of "
        "book value released.",
        "**Integration optionality:** 63.6% of PRL (upgrading to 100,000 bpd), a stake in the Pak-Arab "
        "pipeline, and the SOCAR/FWO Faisalabad-Tarujabba white-oil pipeline - each one narrows the "
        "gap between a 0.58x book multiple and replacement cost.",
        "**The street is not subtle about it:** six analysts, Strong Buy, Rs 697 target (+96%), and a "
        "dividend that has been Rs 10/share for four years running with an 18% payout ratio.",
    ],
    bear=[
        "**The core is shrinking.** Motor-gasoline volumes -5%, diesel -6%, white-oil share down to "
        "~42.7% as smaller OMCs undercut PSO. A 0.58x book multiple is what a market pays for a "
        "melting franchise, not necessarily a mispricing.",
        "**LNG is a structural leak.** Six cargoes in Q4 against 28 a year earlier and a Rs 10.7bn "
        "annual swing - with take-or-pay obligations that do not care about demand.",
        "**Earnings quality is poor.** FY26 standalone profit fell 28% and the group's +55% came from "
        "subsidiaries and associates; a 60% effective tax rate means the state takes more of the "
        "pre-tax profit than shareholders do.",
        "**Circular debt is the real balance-sheet story:** Rs 415bn owed, largely by government gas "
        "and power entities. PSO is a lender of last resort to the state, and it has been for a decade.",
        "**The chart is still broken.** The stock is 30% below its 52-week high and below its 200-day "
        "average, in a market where politics has been in charge for a quarter - and it is a quarter of "
        "the index.",
    ],
    notes={
        "market": "PSO is rebuilding above its 50-day average while the 200-day sits overhead at "
                  "PKR 382.59 - a classic early-trend-repair pattern after a 30% drawdown from the "
                  "506.75 high. The 337-340 shelf has been defended three times in 2026, and the "
                  "December-February breakdown zone (400-434) is the next real supply area.",
        "fundamentals": "This is a book-value story: 0.58x book against a 6.6x multiple of group "
                        "earnings, but the earnings are lumpy, tax-heavy and hostage to inventory "
                        "timing. The balance-sheet claim on the state (Rs 415bn of receivables) is "
                        "both the reason the multiple is low and the reason it should be.",
        "news": "The FY26 print (25 Sep) was read as 'profit surged 122%' in the headline and '-28%' "
                "in the standalone detail - both true, and the market chose to focus on the second. "
                "The 20 Oct ex-dividend, the 26 Oct MPC and the Q1 FY27 board meeting are the three "
                "scheduled events inside the window.",
        "sentiment": "Consensus is aggressively positive (Strong Buy, Rs 697) while the tape is "
                     "negative (-25% over a year, -30% from the high). That combination usually "
                     "resolves upward only when a catalyst arrives; until then the stock drifts.",
        "manager": "The debate is valuation versus momentum, and the calendar does not settle it. "
                   "Buying a 0.58x book energy name into a dividend date with a Strong Buy consensus "
                   "is a reasonable medium-term position, but the next 22 sessions contain no "
                   "company-specific positive catalyst that is bigger than the political and monetary "
                   "risks.",
        "trader": "Accumulate on weakness, do not chase. The ex-dividend drop creates a mechanical "
                  "entry point around 20 Oct; the 337-340 base, not the 200-day, is the level that "
                  "defines the risk.",
        "risk_aggressive": "0.58x book with a 2.8% dividend and a 96% consensus upside is a bet worth "
                           "making in size; the downside is ring-fenced by the 2026 base at 337.",
        "risk_neutral": "Expected return is modest (+1-2% over the window) against a 5% one-day VaR "
                        "of ~4%: stage the entry and let the dividend date do the work.",
        "risk_conservative": "A second consecutive loss-making quarter or a hawkish MPC on 26 Oct "
                             "would break the base; keep the position at half size until the Q1 print "
                             "clears.",
        "execution": (
            "Add only on weakness toward 337-345 and let the 20 Oct ex-dividend set the second "
            "tranche; do not chase strength into the 382-400 supply shelf before Q1 FY27."
        ),
        "pm_rules": (
            "Re-rate the position to a full Buy on a weekly close above the 200-day reference "
            "(382.59) with Q1 FY27 showing no fresh inventory loss; add on a genuine "
            "circular-debt settlement. Cut to the conservative size on a close below 337 with Q1 "
            "FY27 still loss-making, or if the 26 Oct MPC hikes into a KSE-100 that has lost 160,000."
        ),
        "pm": "Pakistan State Oil is not a company you buy for the next three weeks - it is a "
              "0.58x-book asset with national infrastructure, a 4-in-a-row Rs 10 dividend and a "
              "consensus target nearly double the price. But the 22 sessions to 6 November contain "
              "an ex-dividend date, a monetary policy decision and a first-quarter print, and two of "
              "those three can go against a leveraged marketing book.",
    },
    sources=[
        "PSX data portal company page for PSO (financial results and announcements, retrieved 2026-10-08)",
        "BR Research, \"PSO in FY26 - held back by a weaker last quarter\", 2026-09-28",
        "PSO FY26 results release via Business Recorder, The News and Pro Pakistani, 2026-09-25",
        "PSO FY26 annual report extract (PSX document 284943), 2026-10-05",
        "stockanalysis.com quote, statistics, dividend and history pages for PSX:PSO, 2026-10-08",
        "sarmaaya.pk/stocks/PSO live quote (previous close 355.86), 2026-10-08",
        "Yahoo Finance chart and spark endpoints for PSO.KA (daily, weekly, monthly), 2026-10-08",
    ],
)


# --------------------------------------------------------------------------- #
# AHCL - Arif Habib Corporation
# --------------------------------------------------------------------------- #
AHCL = Profile(
    symbol="AHCL.KA",
    ticker="AHCL",
    name="Arif Habib Corporation Limited",
    short_name="Arif Habib Corporation",
    sector="Investment companies / conglomerate holding",
    business="Arif Habib Group's holding company: a ~34% interest (held with Fatima Fertilizer) in PIA Equity Ltd, the consortium that now owns 100% of Pakistan International Airlines, "
             "~73% of Arif Habib Limited, 86% of Sachal Energy, plus strategic stakes in Fatima "
             "Fertilizer, Power Cement, Aisha Steel, Javedan and Pakarab Fertilizers.",
    as_of="2026-10-07",
    spot_date="2026-10-07",
    horizon_end="2026-11-06",
    horizon_sessions=22,
    closes_path=None,
    ohlcv_path=_p("data", "psx", "AHCL_KA_daily_6mo.json"),
    long_arc_path=None,
    data_caveats=[
        "The model applies the full dividend as a step down on the ex-date, which is the textbook treatment; PSX high-yield names often give back less than the full amount on the day, so treat the price median as the conservative case and the total-return probability as the decision number.", 
        "Yahoo Finance carries no AHCL feed, so the daily history in this environment is 50 settled "
        "sessions (28 Jul - 7 Oct 2026) from stockanalysis.com: single source, verified against "
        "sarmaaya.pk (19 Aug close 16.43) and investing.com (18 Sep close 15.10) snapshots and "
        "sarmaaya's 8 Oct quote (previous close 15.48).",
        "With only 50 sessions the volatility estimate carries a wide standard error and the "
        "200-day reference does not exist; the model uses a 50-session mean and the mid-point of the "
        "52-week range (15.75) as the long-run centre instead, and a t-distribution robustness check "
        "is reported alongside the bootstrap interval.",
    ],
    shares_out=4.21696747e9,
    quote={
        "spot": 15.48,
        "pe": 4.21,
        "pb": 1.18,
        "bvps": 13.15,
        "dividend": 1.25,
        "dividend_yield": 0.0808,
        "payout": 0.271,
        "target": None,
        "analysts": 0,
        "consensus": None,
        "beta": 0.41,
        "mcap": 65.28e9,
        "equity": 55.5e9,
        "float_pct": 0.15,
        "week52_low": 12.16,
        "week52_high": 19.33,
        "ytd": -0.037,
        "year_change": -0.092,
    },
    facts={
        "fy26_revenue": 13.83e9,
        "fy26_revenue_growth": 0.194,
        "fy26_pat": 15.53e9,
        "fy26_pat_growth": 0.495,
        "fy26_eps": 3.68,
        "fy25_eps_consolidated": 2.46,
        "fy25_pat_unconsolidated": 23.78e9,
        "fy25_eps_unconsolidated": 5.64,
        "q3fy26_loss": -8.37e9,
        "q3fy26_eps": -1.99,
        "pia_price": 135e9,
        "pia_valuation": 180e9,
        "pia_capital_plan": 125e9,
        "pia_liabilities": 54e9,
        "pia_fleet": 34,
        "pia_fleet_operational": 17,
        "consortium_ahcl_fatima": 0.341,
        "consortium_ffc": 0.34,
        "ahcl_fatima_stake": 0.1519,
        "ahcl_ahl_stake": 0.7292,
        "ahcl_sachal": 0.8583,
        "ahl_fy26_pat": 1.177e9,
        "ahl_fy26_eps": 18.01,
        "ahl_dividend": 12.50,
        "fatima_dividend_received": 2.288e9,
        "sachal_dividend_received": 1.373e9,
        "psx_ath": 191033.0,
        "kse100": 169264.87,
    },
    score_components=[
        {"name": "Price / earnings (4.2x FY26 consolidated)", "value": 4.21,
         "good": 3.0, "bad": 9.0, "higher_is_better": False, "weight": 0.25},
        {"name": "Price / book (1.18x)", "value": 1.18,
         "good": 0.60, "bad": 1.60, "higher_is_better": False, "weight": 0.20},
        {"name": "Earnings momentum (FY26 +49.5% but a Q3 loss)", "value": 0.495,
         "good": 0.40, "bad": -0.20, "higher_is_better": True, "weight": 0.25},
        {"name": "Dividend yield (8.1%, raised 25% this year)", "value": 0.0808,
         "good": 0.09, "bad": 0.02, "higher_is_better": True, "weight": 0.15},
        {"name": "Earnings volatility (Q3 mark-to-market loss of Rs 8.4bn)",
         "value": 8.37e9 / max(1.0, 15.53e9), "good": 0.05, "bad": 0.60, "higher_is_better": False,
         "weight": 0.15},
    ],
    levels={
        "support": 14.90,
        "support_label": "September 2026 base (14.90-15.10)",
        "deeper_support": 13.15,
        "resistance": 16.55,
        "resistance_label": "September 2026 high",
        "resistance_2": 17.00,
        "book": 13.15,
        "long_ma": 15.75,
        "week52_low": 12.16,
        "week52_high": 19.33,
        "target": None,
    },
    company=[
        {"fact": "FY26 (year to 30 Jun 2026) consolidated profit attributable to shareholders rose "
                 "49.5% to Rs 15.53bn (EPS 3.68 on 4.22bn shares); revenue rose 19.4% to Rs 13.83bn.",
         "source": "AHCL annual results (PSX) / stockanalysis.com", "date": "2026-09-30", "direction": "positive"},
        {"fact": "The Arif Habib-led consortium bought 75% of Pakistan International Airlines for "
                 "Rs 135bn in December 2025 and then the remaining 25%, so PIA Equity Limited - in "
                 "which AHCL plus Fatima Fertilizer hold 34.1% - owns 100% of the airline.",
         "source": "Business Recorder / Bloomberg / Dawn", "date": "2026-04-28", "direction": "positive"},
        {"fact": "Q3 FY26 (Jan-Mar 2026) produced an unconsolidated loss of Rs 8.37bn (EPS -1.99) "
                 "because of mark-to-market losses on the securities portfolio as the KSE-100 fell.",
         "source": "AHCL directors' report (PSX document 276323)", "date": "2026-04-28", "direction": "negative"},
        {"fact": "Annual dividend raised 25% to Rs 1.25/share (8.1% yield); ex-date 20 Oct 2026, "
                 "paid 19 Nov 2026; payout ratio ~27%.",
         "source": "AHCL board decision / stockanalysis.com", "date": "2026-09-30", "direction": "positive"},
        {"fact": "Subsidiary Arif Habib Limited grew profit 20% to Rs 1.177bn (EPS 18.01) in FY26 and "
                 "paid Rs 12.50/share; dividends received by AHCL include Rs 2.29bn from Fatima "
                 "Fertilizer and Rs 1.37bn from Sachal Energy in FY25.",
         "source": "AHL FY26 results (PSX); AHCL directors' report", "date": "2026-08-24", "direction": "positive"},
        {"fact": "The group committed to inject up to Rs 125bn into PIA for fleet restoration and "
                 "expansion, with 17 of 34 aircraft operational in January and management targeting "
                 "the full fleet by September 2026; PIA carried ~Rs 54bn of liabilities.",
         "source": "Business Recorder interview with Arif Habib", "date": "2026-01-12", "direction": "neutral"},
    ],
    sector_facts=[
        {"fact": "Holding-company discount: AHCL's own market capitalisation (Rs 65bn) is below the "
                 "marked value of its listed holdings and control stakes, a standard feature of "
                 "Pakistani investment companies.",
         "source": "market data, 2026-10-08", "date": "2026-10-08", "direction": "neutral"},
        {"fact": "PIA's privatisation is the flagship test of Pakistan's IMF-backed reform programme; "
                 "the airline's turnaround is now a private-sector execution story.",
         "source": "Dawn / Arab News", "date": "2025-12-25", "direction": "neutral"},
        {"fact": "AHCL's earnings are levered to the KSE-100 through a marked-to-market securities "
                 "book: Q3 FY26 showed an Rs 8.4bn swing on an index decline.",
         "source": "AHCL directors' report", "date": "2026-04-28", "direction": "negative"},
    ],
    macro=[
        {"headline": "KSE-100 at 169,264.87 (7 Oct)", "detail": "1.4% higher over twelve months but "
         "11.4% below the all-time high of 191,033; the index is the single largest driver of AHCL's "
         "mark-to-market earnings.", "direction": "neutral"},
        {"headline": "SBP on hold at 11.5%, decision on 26 October", "detail": "Rate relief supports "
         "the brokerage and real-estate arms; a hawkish surprise would hit both the index and the "
         "portfolio.", "direction": "neutral"},
        {"headline": "Inflation 10.26% with the PTI standoff live", "detail": "Political escalation is "
         "the fastest way to a lower index and another mark-to-market quarter.", "direction": "negative"},
        {"headline": "Aviation and fuel economics", "detail": "Fuel is an airline's largest cost line "
         "and crude was quoted near $101-103/bbl in early October - PIA's turnaround would be easier "
         "with softer oil.", "direction": "negative"},
        {"headline": "Fertilizer and cement demand", "detail": "AHCL's associate earnings lean on "
         "Fatima Fertilizer, Power Cement and Aisha Steel - agriculture and construction activity, "
         "both of which track the rate cycle.", "direction": "neutral"},
    ],
    events=[
        {"date": "2026-10-20", "event": "Ex-dividend: Rs 1.25/share (8.1% of the price)",
         "why": "The single largest scheduled cash event of the year for AHCL holders; payment 19 Nov."},
        {"date": "late Oct 2026", "event": "Q1 FY27 results (quarter ended 30 Sep 2026)",
         "why": "The first quarter in which the PIA acquisition is on the books - the market will read "
                "it as either turnaround proof or a cash call."},
        {"date": "2026-10-26", "event": "SBP monetary policy decision",
         "why": "The KSE-100 - and therefore AHCL's trading book and brokerage volumes - is rate-"
                "sensitive."},
        {"date": "through the window", "event": "PIA operational news flow",
         "why": "Fleet serviceability, route restoration and any move toward re-listing are the "
                "catalysts that would close the conglomerate discount."},
    ],
    risks=[
        {"risk": "PIA becomes a capital sink", "severity": "high",
         "why": "Rs 125bn of committed capital and a Rs 45bn bank guarantee for the government's "
                "residual 25%: if the airline's losses outrun the plan, AHCL's balance sheet absorbs it."},
        {"risk": "Earnings are mark-to-market", "severity": "high",
         "why": "Q3 FY26 lost Rs 8.4bn on index losses; the FY26 'cheap' multiple is flattered by a "
                "good market quarter, and the same swing can repeat in reverse."},
        {"risk": "15% free float, 78.8% insider ownership", "severity": "medium",
         "why": "Thin liquidity means violent moves on small flows, no index-driven sponsorship, and "
                "minority investors with little influence over capital allocation."},
        {"risk": "Associate dividend dependence", "severity": "medium",
         "why": "The 8.1% yield is funded by dividends from Fatima, AHL and Sachal; a cut at any of "
                "them breaks the income case."},
        {"risk": "No analyst coverage", "severity": "low",
         "why": "There is no consensus estimate or price target to anchor valuation, so the price is "
                "set by private-wealth flows and sentiment."},
        {"risk": "Political / index risk", "severity": "high",
         "why": "AHCL is a high-beta proxy for Pakistani equity sentiment; the political standoff and "
                "the 26 Oct MPC both feed directly into its portfolio marks."},
    ],
    scorecard=[
        {"dimension": "Valuation", "score": 8,
         "comment": "4.2x FY26 consolidated earnings, 1.18x book and an 8.1% dividend yield - cheap in "
                    "absolute terms, though the earnings base is unusual."},
        {"dimension": "Earnings momentum", "score": 6,
         "comment": "FY26 consolidated profit +49.5%, but the pattern is volatile: a Rs 8.4bn "
                    "unconsolidated loss in Q3 and a strong Q1."},
        {"dimension": "Balance sheet", "score": 5,
         "comment": "A holding company whose main asset (PIA) comes with Rs 54bn of liabilities and a "
                    "Rs 125bn capital plan; the Rs 45bn guarantee for the government's residual stake "
                    "is a claim on group liquidity."},
        {"dimension": "Franchise", "score": 7,
         "comment": "The Arif Habib brand, the country's flagship brokerage, a 50MW wind asset, a "
                    "fertilizer stake and now the national airline - one of Pakistan's few true "
                    "conglomerates."},
        {"dimension": "Macro tailwind", "score": 5,
         "comment": "Rate relief and a stable rupee help; 10.3% inflation, high oil and a political "
                    "standoff do not."},
        {"dimension": "Technical", "score": 4,
         "comment": "8% below the 52-week mid-point and 20% below the high; the stock has been range-"
                    "bound 14.90-16.60 for three months on thin volume."},
        {"dimension": "Sentiment", "score": 5,
         "comment": "No analyst coverage; a retail and high-net-worth favourite that moves with the "
                    "index rather than with company news."},
        {"dimension": "Governance", "score": 6,
         "comment": "Founder-led and professionally staffed, but 78.8% insider ownership, related-party "
                    "holdings across the group and a very small float concentrate decision-making."},
    ],
    falsification=[
        "Q1 FY27 (late October) showing PIA's losses dragging group earnings into a loss would turn "
        "the 'optionality' narrative into a funding problem.",
        "Any equity raise or stake sale at AHCL level to fund the airline would dilute the " 
        "sum-of-parts case and reset the dividend.",
        "A cut in the Fatima Fertilizer or AHL dividend would break the 8.1% yield that underpins the "
        "current price.",
        "A KSE-100 close below 160,000 would put the securities book back into mark-to-market losses "
        "and remove the earnings base the multiple rests on.",
        "Conversely, a PIA milestone - the full fleet serviceable, a US/UK route resumption, or a "
        "re-listing announcement - would be the event that narrows the conglomerate discount.",
    ],
    cash_events=[
        {"session": 9, "amount": 1.25, "label": "FY26 dividend, ex-date 2026-10-20"},
    ],
    thresholds=[
        {"label": "PKR 15.75 (mid-point of the 52-week range)", "price": 15.75, "side": "above"},
        {"label": "PKR 16.55 (September high)", "price": 16.55, "side": "above"},
        {"label": "PKR 17.00 (price a year ago)", "price": 17.00, "side": "above"},
        {"label": "PKR 19.33 (52-week high)", "price": 19.33, "side": "above"},
        {"label": "PKR 15.00 (round-number support)", "price": 15.00, "side": "below"},
        {"label": "PKR 14.90 (September base)", "price": 14.90, "side": "below"},
        {"label": "PKR 13.15 (book value per share)", "price": 13.15, "side": "below"},
        {"label": "PKR 12.16 (52-week low)", "price": 12.16, "side": "below"},
    ],
    scenarios=[
        {"name": "Bull - PIA news flow plus a firm index", "probability": 0.30,
         "range": (16.60, 18.50), "midpoint": 17.60,
         "triggers": ["Q1 FY27 without a PIA-related loss surprise and the dividend banked",
                      "PIA operational milestone (fleet serviceability, route/US clearance)",
                      "KSE-100 back above 175,000, lifting the securities book",
                      "SBP hold on 26 Oct with a dovish tilt"]},
        {"name": "Base - range-bound around the dividend", "probability": 0.45,
         "range": (14.90, 16.60), "midpoint": 15.70,
         "triggers": ["Q1 FY27 in line, PIA consolidation neutral at the earnings line",
                      "index range-bound 160,000-172,000",
                      "the Rs 1.25 dividend captured, no corporate action",
                      "thin float keeps the tape quiet"]},
        {"name": "Bear - PIA losses and a weaker index", "probability": 0.25,
         "range": (12.80, 14.90), "midpoint": 13.40,
         "triggers": ["Q1 FY27 shows PIA losses hitting the group line",
                      "KSE-100 below 160,000 on political escalation, forcing more mark-to-market losses",
                      "a capital call or guarantee expansion at PIA Equity",
                      "an associate dividend cut"]},
    ],
    regime_weights={"martingale": 0.40, "mean_reversion": 0.40, "catalyst": 0.20},
    bull=[
        "**You are paying 4.2x earnings and 1.18x book for the group that now owns the national "
        "airline, the country's leading brokerage and 15% of Fatima Fertilizer** - and it pays an 8.1% "
        "dividend, raised 25% this year.",
        "**PIA is the largest free option on the Pakistan Stock Exchange.** A 100%-owned national "
        "carrier, Rs 125bn of committed capital, a fleet being brought back into service, no layoffs, "
        "and management's explicit ambition to re-list the airline once it is profitable.",
        "**The operating subsidiaries are compounding:** Arif Habib Limited +20% to Rs 1.18bn with a "
        "Rs 12.50 dividend, Sachal Energy paying Rs 1.37bn, Fatima paying Rs 2.29bn - a dividend "
        "machine behind an 8% yield.",
        "**The Q3 FY26 loss was the index, not the business** (-Rs 8.4bn of mark-to-market on the "
        "securities book). The KSE-100 is 11% below its high; a recovery reverses that line item "
        "automatically.",
        "**The float is tiny (15%) and insiders own ~79%:** there is no forced selling and any "
        "incremental institutional interest moves the price sharply.",
    ],
    bear=[
        "**PIA is an unproven, capital-hungry turnaround.** Rs 125bn is the plan, Rs 54bn of "
        "liabilities came with the asset, and the first quarter where the airline is consolidated "
        "into AHCL's numbers lands inside this forecast window.",
        "**The earnings quality is poor:** Q3 FY26 lost Rs 8.4bn on portfolio marks, so the FY26 "
        "'+49%' headline is partly a good market quarter rather than operational improvement.",
        "**Only 15% free float** means no analyst coverage, no price target, thin liquidity and no "
        "index sponsorship - the market can ignore good news for months.",
        "**The dividend depends on associates:** if Fatima, AHL or Sachal trim payouts to fund their "
        "own plans, the 8.1% yield (the main support under the price) thins out.",
        "**Relative performance is poor:** -9.2% over twelve months against an index that is +1.4%, "
        "with the 52-week high 20% above the current price.",
    ],
    notes={
        "market": "Fifty sessions of range-trading between 14.90 and 16.60 on thin volume, with the "
                  "8.1% dividend date on 20 October the only scheduled event that reliably draws "
                  "buyers. The 52-week range (12.16-19.33) brackets a stock that spends most of its "
                  "time in the middle of its own range.",
        "fundamentals": "The valuation looks absurdly cheap (4.2x earnings, 1.18x book, 8.1% yield) "
                        "only if you accept the FY26 consolidated earnings base; the honest way to "
                        "look at AHCL is as a levered, illiquid sum-of-parts bet on PIA's turnaround "
                        "and the Pakistani index.",
        "news": "The FY26 results (30 Sep) and the PIA ownership completion dominate the news flow; "
                "the operational news that matters - fleet serviceability, route restoration, "
                "possible re-listing - arrives in unpredictable bursts.",
        "sentiment": "No analyst covers AHCL; the shareholder register (78.8% insider, 15% free "
                     "float) means there is no consensus anchor and no institutional flow to cushion "
                     "the price. Treat the 8.1% dividend as the sentiment anchor instead.",
        "manager": "AHCL is a holding company with one very large, very new, very risky asset and a "
                   "cash-generative dividend core. The 22-session window contains the dividend and "
                   "the first PIA-consolidated quarter - two events that can both cut either way.",
        "trader": "Buy the dividend, keep the position small, and treat the 14.90 base as the line "
                  "that defines the risk: below it the stock is back to the book value at best.",
        "risk_aggressive": "An 8.1% dividend with a 30% probability of a PIA-driven re-rating is worth "
                           "full weight; the float is tiny and any good news gaps the stock.",
        "risk_neutral": "The expected return is small and the distribution is two-sided: take the "
                        "dividend, stage the entries, and do not size it like a core holding.",
        "risk_conservative": "PIA's first consolidated quarter is an unquantifiable event on top of "
                             "index risk; half the vol-targeted size, and review after the Q1 print.",
        "pm_rules": (
            "Re-rate on evidence that the PIA stake is being funded without dilution and that the "
            "holding-company discount is closing (a buyback, a special dividend, or a re-rating at "
            "Fatima or Power Cement). Cut on a break of the 14.40-14.60 shelf, on any equity "
            "issuance that funds PIA at these multiples, or if the FY27 first-quarter earnings show "
            "the investment losses are still running."
        ),
        "pm": "Arif Habib Corporation offers a 4.2x multiple, a 1.18x book and an 8.1% dividend on top "
              "of a genuine, high-variance option on PIA. For a holder the calculus is simple: you "
              "are paid more than 8% cash to own the option. For a 22-session horizon, though, the "
              "option's own news flow - and Pakistan's index - dominate, so the position should be "
              "sized for a two-sided distribution rather than a trend.",
    },
    sources=[
        "AHCL annual and quarterly results (PSX data portal and PSX document 276323 directors' report)",
        "marketcreener / MarketScreener company profile (shareholders, holdings, PIA timeline), 2026",
        "Business Recorder: \"Arif Habib consortium acquires remaining 25% stake in PIA\", 2026-04-28",
        "Arab News / Dawn / Tribune coverage of the PIA privatisation, 2025-12-24 and 2025-12-30",
        "stockanalysis.com quote, dividend, history and company pages for PSX:AHCL, 2026-10-08",
        "sarmaaya.pk/stocks/AHCL (52-week range, free float, market cap), 2026-10-08",
        "Arab News, Business Recorder, Express Tribune and Pakistan Today coverage of the PIA sale: Rs 135bn for 75% (Dec 2025), Rs 45bn for the remaining 25% (Apr 2026), PIA Equity Ltd vehicle, Rs 125bn injection plan and Rs 54bn of liabilities (Dec 2025 - May 2026)",
        "AHCL FY26 annual results and the Rs 1.25 dividend announcement (PSX announcements, 30 Sep 2026)",
    ],
)


PROFILES = {p.symbol: p for p in (PSO, AHCL)}
ALIASES = {
    "PSO": PSO, "PSO.KA": PSO, "PSO.PSX": PSO,
    "AHCL": AHCL, "AHCL.KA": AHCL, "AHCL.PSX": AHCL,
}


def get(symbol: str) -> Profile:
    try:
        return ALIASES[symbol.strip().upper()]
    except KeyError as exc:  # pragma: no cover
        raise KeyError(f"no profile for {symbol!r}; known: {sorted(PROFILES)}") from exc
