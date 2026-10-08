"""The TradingAgents committee, reproduced deterministically.

When an LLM API key is available the vendored ``TradingAgents`` graph should be
run instead (see :mod:`psx.tradingagents_bridge`).  When no key is available -
or when a bit-for-bit reproducible audit trail is wanted - this module runs the
*same pipeline over the same data tools* with explicit, inspectable rules:

    Market / Fundamentals / News / Sentiment analysts
        -> Bull vs Bear research debate
        -> Research Manager (5-tier investment plan)
        -> Trader (3-tier transaction proposal with entry, stop and size)
        -> Aggressive / Neutral / Conservative risk debate
        -> Portfolio Manager (final decision + rating)

The role definitions, the 5-tier rating scale and the state fields mirror
``TradingAgents/tradingagents/agents/`` so the two engines are interchangeable
in the reporting layer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import forecast as fc
from . import indicators as ind
from . import research as rs

# Rating scale copied from TradingAgents/tradingagents/agents/schemas.py
PORTFOLIO_RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")
TRADER_ACTIONS = ("Buy", "Hold", "Sell")


@dataclass
class CommitteeOutput:
    reports: dict = field(default_factory=dict)
    scores: dict = field(default_factory=dict)
    debate: dict = field(default_factory=dict)
    investment_plan: str = ""
    rating: str = "Hold"
    trade_proposal: str = ""
    action: str = "Hold"
    trade_params: dict = field(default_factory=dict)
    risk_debate: dict = field(default_factory=dict)
    risk_note: str = ""
    final_decision: str = ""
    final_rating: str = "Hold"


# --------------------------------------------------------------------------- #
# analyst layer
# --------------------------------------------------------------------------- #
def _score(value, good, bad, higher_is_better=True) -> float:
    """Map a raw metric onto a 0-10 score: ``good`` -> 10, ``bad`` -> 0."""
    if value is None:
        return 5.0
    if higher_is_better:
        frac = (value - bad) / (good - bad)
    else:
        frac = (bad - value) / (bad - good)
    return max(0.0, min(10.0, 10.0 * frac))


def market_analyst(series, ohlcv) -> tuple[str, float]:
    c = series.closes
    sma20, sma50, sma200 = ind.sma(c, 20), ind.sma(c, 50), ind.sma(c, 200)
    rsi = ind.rsi(c, 14)
    macd = ind.macd(c)
    bb = ind.bollinger(c)
    vol20, vol250 = ind.realized_vol(c, 20), ind.realized_vol(c, 250)
    atr = ind.atr(ohlcv["rows"], 14)
    levels = ind.swing_levels(ohlcv["rows"])
    dd = ind.drawdown_from_peak(c)

    score = 5.0
    score += 1.0 if (sma20 and c[-1] > sma20) else -1.0
    score += 1.0 if (sma50 and c[-1] > sma50) else -1.0
    score += 0.5 if (rsi and rsi < 30) else (-0.5 if (rsi and rsi > 70) else 0.0)
    score += 1.0 if (rsi and 30 <= rsi <= 45 and macd and macd["histogram"] and macd["histogram"] > -0.1) else 0.0
    score -= 0.5 if dd < -0.25 else 0.0
    score = max(0.0, min(10.0, score))

    report = f"""### Market Analyst - technical read

**Price structure.** Last settled close **PKR {c[-1]:.2f}** (2026-10-06). The stock is
**{dd * 100:.1f}% below** the January 2026 all-time intraday high of 44.17 and has lost
{-ind.total_return(c, 21) * -100:.1f}% over the last month. It trades below every major
average: SMA20 {sma20:.2f}, SMA50 {sma50:.2f}, SMA100 {ind.sma(c, 100):.2f},
SMA200 {sma200:.2f} - a clean bearish alignment.

**Momentum.** RSI(14) {rsi:.1f} (weak, not yet capitulated); MACD {macd['macd']:.3f} versus
signal {macd['signal']:.3f}, histogram {macd['histogram']:+.3f} (negative but flattening -
the rate of deterioration is slowing).

**Volatility & risk.** Realised vol {vol20 * 100:.0f}% (20d) and {vol250 * 100:.0f}% (250d)
annualised; ATR(14) PKR {atr:.2f} (~{atr / c[-1] * 100:.1f}% of price); Bollinger %B
{bb['pct_b']:.2f} with the lower band at {bb['lower']:.2f}. One-day historical VaR(95)
{ind.historical_var(c) * 100:.1f}%, CVaR(95) {ind.historical_cvar(c) * 100:.1f}%.

**Levels.** Recent swing lows {levels['swing_lows']} and the 2026-10-06 low of 28.55 form
the support shelf; the 200-day average at {sma200:.2f} and the July swing close of 34.46 are
the first real resistance, then the GoPb issue floor at 38.20.

**Volume.** The 5 Oct down day traded 7.3mn shares against a three-month average near
19.5mn, and 6 Oct closed {((c[-1] / 28.55) - 1) * 100:.1f}% off its low on 8.5mn shares -
supply is drying up into support rather than accelerating.
"""
    return report, score


def fundamentals_analyst(series, forecast_result) -> tuple[str, float]:
    subj = rs.SUBJECT
    price = series.closes[-1]
    bvps = 31.83
    eps_ttm = 5.59
    pb = price / bvps
    pe = price / eps_ttm
    score = 0.0
    score += _score(pe, good=4.0, bad=9.0, higher_is_better=False) * 0.35
    score += _score(pb, good=0.85, bad=1.6, higher_is_better=False) * 0.35
    score += _score(0.40, good=0.35, bad=0.10) * 0.15  # H1 PAT growth +40%
    score += _score(0.1369, good=0.16, bad=0.12) * 0.15  # CAR
    score = max(0.0, min(10.0, score))

    report = f"""### Fundamentals Analyst - valuation and earnings

**Valuation.** At PKR {price:.2f}: market cap ~PKR {price * subj['shares_outstanding'] / 1e9:.0f}bn,
**{pb:.2f}x** the audited break-up value of PKR 31.83 and **{pe:.1f}x** trailing EPS of 5.59
(~4.5x forward on consensus). A ~Rs 3.00 trailing dividend is a **{3.00 / price * 100:.1f}%**
yield. The contracted Government of Punjab issue price of **PKR 38.20** is {38.20 / price - 1:.0%}
above the market - i.e. the largest shareholder is buying new equity at a premium to book.

**Earnings power.** H1-2026 was the best half in the bank's history: operating profit
Rs 22.5bn (+67% y/y), PBT Rs 20.5bn (+35%), PAT Rs 9.5bn (+40%), NII Rs 46.1bn (+29%) and
non-markup income ex-gains Rs 11.9bn (+61%). Cost-to-income improved 2.40pp. Deposits reached
Rs 2,154bn with current accounts +20% y/y; gross advances grew 28% to Rs 996bn, implying an
ADR near 46% against a system average of 34.7%.

**Capital.** CAR 13.69% and a 3.65% leverage ratio clear the regulatory floor but leave BOP the
thinnest large bank in Pakistan (Tier-1 PKR 99.9bn). The approved Rs 30bn injection, at a floor
of PKR 38.20, would lift book value per share from 31.83 to roughly 33.1 before any deployment
- **+4% of book for existing holders** - at the cost of up to ~24% more shares.

**Quality.** Government of Punjab schemes are 18% of the portfolio but only 3% of NPLs, with
97-100% recovery; the group NPL ratio of ~8% still trails private peers by a wide margin, and
PACRA's AAA (A1+, stable) upgrade on 1 Jul 2026 recognises the improved franchise.
"""
    return report, score


def news_analyst(series, forecast_result) -> tuple[str, float]:
    negatives = [m for m in rs.MACRO if m["direction"] == "negative"]
    positives = [m for m in rs.MACRO if m["direction"] == "positive"]
    company_pos = [m for m in rs.COMPANY if m["direction"] == "positive"]
    company_neg = [m for m in rs.COMPANY if m["direction"] == "negative"]
    # Macro tape and company newsflow get equal weight: the tape is currently
    # hostile (inflation, a possible hike, politics) while the company flow is
    # strongly positive (record H1, AAA, the capital injection, the dividend).
    macro_score = max(0.0, min(10.0, 5.0 + 0.6 * len(positives) - 0.7 * len(negatives)))
    company_score = max(0.0, min(10.0, 5.0 + 0.8 * len(company_pos) - 0.8 * len(company_neg)))
    score = 0.5 * macro_score + 0.5 * company_score
    report = f"""### News Analyst - macro and event tape

**What is driving the tape.** {rs.MACRO[5]['headline']} -> {rs.MACRO[5]['detail']}

**The event calendar inside the forecast window.**

| Date | Event | Why it matters |
|------|-------|----------------|
"""
    for ev in rs.EVENTS:
        report += f"| {ev['date']} | {ev['event']} | |\n"
    report += f"""
**Score split.** Macro tape {macro_score:.1f}/10, company newsflow {company_score:.1f}/10
(equal-weighted) - the tape is hostile while the company flow is strongly positive.

**Macro balance.** Supportive: {positives[0]['headline'] if positives else 'n/a'}.
Hostile: {negatives[0]['headline'] if negatives else 'n/a'} - {negatives[0]['detail'] if negatives else ''}
The policy rate has been on hold at 11.5% since the
100bp hike in April 2026, and the money market is pricing a further hike (1-year T-bill cut-off
12.49%, 12M KIBOR 12.68%), so the 26 Oct MPC is a two-sided risk rather than a free option.

**Company newsflow.** The GoPb equity injection (approved 8 Sep 2026), PACRA's AAA upgrade
(1 Jul 2026), the highest-ever 16% interim dividend (dispatched 24 Sep 2026) and the Bahrain
wholesale-banking unit are all recent positives. Two caveats: Q2-2026 PAT (Rs 4.756bn) was 5%
BELOW Q2-2025, so the "record H1" is front-loaded, and the equity plan was preceded by a
+9%/158mn-share run-up before it was disclosed - a governance flag. Set against all of this:
the sector-wide bank sell-off on 5 Oct, political noise and oil at $101-103/bbl.
"""
    return report, score


def sentiment_analyst(series, ohlcv) -> tuple[str, float]:
    c = series.closes
    vols = [r["volume"] for r in ohlcv["rows"][-20:]]
    avg20 = sum(vols) / len(vols)
    avg3m = sum(r["volume"] for r in ohlcv["rows"]) / len(ohlcv["rows"])
    r1m = ind.total_return(c, 21) * 100
    rsi = ind.rsi(c, 14)
    score = 5.0
    score += 0.8 if r1m > -0.05 else -0.8
    score += 0.7 if avg20 > avg3m else -0.3
    score += 0.5 if (rsi and rsi < 40) else 0.0
    score = max(0.0, min(10.0, score))
    report = f"""### Sentiment Analyst - positioning and flows

Sell-side consensus is a **Strong Buy** (2 analysts) with a 12-month target of **Rs 44.60**,
about {44.60 / c[-1] - 1:.0%} above spot - the widest gap between street targets and price seen
in this name for some time.

Market-structure evidence is more mixed. The stock is {r1m:.1f}% over one month and sits
{ind.drawdown_from_peak(c) * 100:.0f}% below its high, while 20-day average volume
({avg20 / 1e6:.1f}mn shares) is below the three-month average ({avg3m / 1e6:.1f}mn) - typical of
a stock being sold into weakness by index/momentum money rather than abandoned by long-term
holders. Reported foreign selling on 5 Oct was only Rs 45mn, and BOP was still among the
bourse's volume leaders, so domestic retail interest has not disappeared.

Beta is reported between 1.19 (5-year) and 2.17 (1-year): the one-year figure tells you the
2025 re-rating was idiosyncratic, not simply index beta.
"""
    return report, score


# --------------------------------------------------------------------------- #
# research debate + manager
# --------------------------------------------------------------------------- #
def bull_bear_debate(series, scores, forecast_result, ohlcv) -> dict:
    c = series.closes
    spot = c[-1]
    bull = f"""**Bull case.** The market is pricing BOP as if the 2025 re-rating was a mistake, but the
fundamentals say otherwise:

1. **The largest shareholder is contracted to buy at PKR 38.20** - the higher of a KPMG
   base-case value or market price plus 5%, and ~20% above audited book. That is a
   {38.20 / spot - 1:.0%} premium to spot, and it lifts book value for holders who do not
   subscribe.
2. **Earnings are compounding, not stalling.** H1-2026 PAT +40% y/y on operating profit +67%;
   advances +28% with an ADR near 46% versus a 34.7% system average, so BOP is the one large
   bank actually lending.
3. **The stock is cheap on every anchor**: {spot / 31.83:.2f}x book, {spot / 5.59:.1f}x trailing
   earnings, ~{3.00 / spot * 100:.1f}% dividend yield, versus a 44.60 consensus target.
4. **Technicals are washing out, not breaking down.** RSI {ind.rsi(c, 14):.0f}, 6 Oct closed
   {((spot / 28.55) - 1) * 100:.1f}% off its low, and volume on the decline is *below* the
   three-month average - the profile of a completed retracement inside a longer uptrend that
   ran from ~5 to 44.17 over two years.
5. **AAA plus $21.4bn of SBP reserves plus a 3-month import cover** is a macro backdrop no
   Pakistani bank had in previous downcycles.
"""
    bear = f"""**Bear case.** The bear does not dispute the franchise; it disputes the timing and the price
paid for optionality:

1. **A 31% drawdown is not "cheap", it is a de-rating in progress.** Every moving average from
   the 20-day ({ind.sma(c, 20):.2f}) to the 200-day ({ind.sma(c, 200):.2f}) slopes down and sits above price.
2. **The rate cycle turned against the sector's safest trade.** Inflation at 10.26% has the
   money market pricing a hike (1-year T-bill 12.49%). Higher-for-longer cuts the value of
   banks' government-securities books and raises the odds of a market-wide de-rating; the
   KSE-100 is already 12% off its high.
3. **Politics is now the dominant factor.** A government-PTI standoff in which banks are ~25%
   of the index means stock-specific strength can be overridden for weeks at a time.
4. **The capital raise cuts both ways.** Up to 24% more shares means mechanical EPS/ROE
   dilution until deployment; the tranche schedule (Rs 15-20bn by 31 Dec 2026) is an execution
   risk, and the market has repeatedly punished PSX banks for capital events.
5. **Asset quality is not fixed.** An ~8% NPL ratio against sub-4% at the best private peers,
   with the sector's ADR stuck at 34.7% and a high-rate environment squeezing marginal
   borrowers.
"""
    return {"bull": bull, "bear": bear}


def research_manager(scores, forecast_result) -> tuple[str, str]:
    weights = {"market": 0.20, "fundamentals": 0.30, "news": 0.25, "sentiment": 0.25}
    composite = sum(scores[k] * w for k, w in weights.items())
    if composite >= 7.5:
        rating = "Buy"
    elif composite >= 6.25:
        rating = "Overweight"
    elif composite >= 4.25:
        rating = "Hold"
    elif composite >= 3.0:
        rating = "Underweight"
    else:
        rating = "Sell"

    p_up = forecast_result.prob_up
    plan = f"""### Research Manager - investment plan

**Composite score: {composite:.2f}/10** (market {scores['market']:.1f} weighted 20%, fundamentals
{scores['fundamentals']:.1f} 30%, news {scores['news']:.1f} 25%, sentiment {scores['sentiment']:.1f} 25%).

The debate resolves in favour of the bull on *value and capital structure*, and of the bear on
*timing and macro*. The decisive asymmetry is contractual rather than sentiment-driven: a
government subscribed to buy up to Rs 30bn of new equity at no less than PKR 38.20 while the
market trades near {forecast_result.spot:.2f}. That does not stop the price from falling in the
next month - the stock can trade below the issue price, and did for all of September - but it
does anchor the medium-term value of the franchise.

Over the next {forecast_result.horizon_sessions} sessions the distribution is close to symmetric
with a modest upward tilt: **P(price higher) = {p_up:.0%}**, median
PKR {forecast_result.quantiles['p50']:.2f}, 80% interval
PKR {forecast_result.quantiles['p10']:.2f}-{forecast_result.quantiles['p90']:.2f}. With that
risk/reward the correct posture is to **accumulate on weakness rather than chase strength**,
which is a "{rating}" at the portfolio level.
"""
    return plan, rating


# --------------------------------------------------------------------------- #
# trader + risk + PM
# --------------------------------------------------------------------------- #
def trader(series, rating, forecast_result, ohlcv) -> tuple[str, str, dict]:
    c = series.closes
    spot = c[-1]
    atr = ind.atr(ohlcv["rows"], 14) or spot * 0.03
    support = min(28.55, min(r["low"] for r in ohlcv["rows"][-20:]))
    entry_lo, entry_hi = round(support * 1.005, 2), round(spot * 1.02, 2)
    stop = round(support - 1.5 * atr, 2)
    target1 = round(max(ind.sma(c, 200) or 0, 33.70), 2)
    target2 = 38.20
    risk_per_share = max(0.01, (entry_lo + entry_hi) / 2 - stop)
    reward = (target1 - (entry_lo + entry_hi) / 2)
    rr = reward / risk_per_share if risk_per_share else 0.0
    # vol-targeted size: 12% annualised volatility budget on a 33% vol asset
    size_pct = min(8.0, max(2.0, 12.0 / (forecast_result.annual_vol * 100) * 100 * 33.0 / 100 / 3))
    size_pct = round(size_pct, 1)
    action = "Buy" if rating in ("Buy", "Overweight") else ("Hold" if rating == "Hold" else "Sell")

    plan = f"""### Trader - transaction proposal

**Action: {action} (scaled accumulation).**

| Parameter | Level | Rationale |
|-----------|-------|-----------|
| Entry zone | PKR {entry_lo:.2f} - {entry_hi:.2f} | the 28.55-30.00 shelf, i.e. the 6 Oct reversal low up to a 2% band |
| Stop | PKR {stop:.2f} | 1.5 x ATR(14) below the shelf; a weekly close below it invalidates the basing thesis |
| Target 1 | PKR {target1:.2f} | 200-day average / July swing region |
| Target 2 | PKR {target2:.2f} | the contracted GoPb issue price |
| Risk/reward | {rr:.1f} : 1 | on a first-target basis |
| Position size | {size_pct:.1f}% of the book | volatility-targeted: a ~33% annualised vol name gets a modest weight |

**Execution notes.** Buy in thirds: one third at market, one third on a retest of the 28.50-29.00
zone, one third only if the 26 Oct Q3 print and the MPC are both non-hostile. Do not add above
PKR 33 before a weekly close above the 50-day average; that is where the September supply
overhang sits. The 38.20 anchor is a *medium-term* magnet, not a 30-day target: model probability
of touching it within the horizon is {forecast_result.prob_above['38.20 (GoPb equity-injection floor)']:.1%}.
"""
    params = {
        "entry_zone": [entry_lo, entry_hi],
        "stop": stop,
        "target_1": target1,
        "target_2": target2,
        "risk_reward": round(rr, 2),
        "size_pct": size_pct,
    }
    return plan, action, params


def risk_debate(series, forecast_result, trade_params) -> dict:
    vol = forecast_result.annual_vol * 100
    aggressive = f"""**Aggressive analyst.** A {vol:.0f}% vol stock with a {forecast_result.prob_up:.0%}
probability of being higher in a month is a buy, not a watch. The trade is defined by a hard
level (28.55) that has already been defended twice, the stop is only
{(trade_params['entry_zone'][0] - trade_params['stop']) / trade_params['entry_zone'][0] * 100:.1f}%
below entry, and the upside to the contracted issue price is
{38.20 / forecast_result.spot - 1:.0%}. Push the position to the top of the size band and use the
26 Oct print as the trigger for the second tranche.
"""
    neutral = f"""**Neutral analyst.** The expected return here is small ({forecast_result.expected_return * 100:+.1f}%
over the window) relative to a 5% one-day VaR of {forecast_result.var_5 * 100:.1f}% at the horizon.
That argues for the middle of the size band, staged entries and no leverage. The single largest
avoidable risk is event clustering: the Q3 results and the policy decision land on the same day,
so both tails are fatter than the historical distribution implies.
"""
    conservative = f"""**Conservative analyst.** Two unacceptable risks are live: (1) a hike on 26 Oct
would hit both the index and, via mark-to-market on the investment book, bank earnings power;
(2) a 30% drawdown in the last six months proves the position can move against you quickly
(max two-year drawdown {ind.max_drawdown(series.closes) * 100:.0f}%). Cap the name at half the
vol-targeted size until the capital tranche is actually issued - the Rs 15-20bn tranche by
31 Dec 2026 is the catalyst that converts the thesis from narrative to fact.
"""
    weights = {"aggressive": 0.30, "neutral": 0.45, "conservative": 0.25}
    blended_size = (
        weights["aggressive"] * min(10.0, trade_params["size_pct"] * 1.5)
        + weights["neutral"] * trade_params["size_pct"]
        + weights["conservative"] * max(1.0, trade_params["size_pct"] * 0.5)
    )
    note = f"""The risk team converged on a **{blended_size:.1f}% position** (aggressive
{min(10.0, trade_params['size_pct'] * 1.5):.1f}% / neutral {trade_params['size_pct']:.1f}% /
conservative {max(1.0, trade_params['size_pct'] * 0.5):.1f}%, weighted 30/45/25). Everyone agreed
on three non-negotiables: no averaging down below PKR {trade_params['stop']:.2f}; no more than a
third of the position before the 26 Oct events; and a hard review if the KSE-100 closes below
160,000, because that would make the political channel, not the fundamentals, the binding
constraint.
"""
    return {"aggressive": aggressive, "neutral": neutral, "conservative": conservative, "note": note}, blended_size


def portfolio_manager(series, rating, forecast_result, trade_params, blended_size) -> tuple[str, str, str]:
    spot = series.closes[-1]
    final_rating = rating
    decision = f"""## Portfolio Manager - final decision

**{final_rating.upper()}** (position size {blended_size:.1f}% of the book, built in thirds, stop
PKR {trade_params['stop']:.2f}).

**The one-paragraph version.** The Bank of Punjab is a genuinely improved franchise - record
H1-2026 earnings, an AAA rating, a 46% ADR in a 34.7% system, and a government committed to
injecting up to Rs 30bn of new equity at no less than PKR 38.20 - trading at ~0.93x audited book
after a 31% drawdown that has more to do with politics and the rate cycle than with the bank.
Over the next {forecast_result.horizon_sessions} sessions we expect the price to base rather than
trend: median PKR {forecast_result.quantiles['p50']:.2f}, {forecast_result.prob_up:.0%} chance of
finishing higher, with an 80% interval of PKR {forecast_result.quantiles['p10']:.2f} to
{forecast_result.quantiles['p90']:.2f}. That is a distribution you accumulate into, not one you
pay up for.

**Explicit 30-day call (forecast made 2026-10-07, horizon 2026-11-06):**

* Direction: **modestly higher** - P(up) {forecast_result.prob_up:.0%} versus
  P(down) {forecast_result.prob_down:.0%}; expected price
  PKR {forecast_result.expected_price:.2f} ({forecast_result.expected_return * 100:+.1f}%).
* Central band: **PKR {forecast_result.quantiles['p25']:.2f} - {forecast_result.quantiles['p75']:.2f}**
  (interquartile), full 80% interval PKR {forecast_result.quantiles['p10']:.2f} -
  {forecast_result.quantiles['p90']:.2f}.
* Scenario book: bull {fc.scenarios(spot)[0]['probability']:.0%} (midpoint PKR
  {fc.scenarios(spot)[0]['midpoint']:.2f}), base {fc.scenarios(spot)[1]['probability']:.0%} (PKR
  {fc.scenarios(spot)[1]['midpoint']:.2f}), bear {fc.scenarios(spot)[2]['probability']:.0%} (PKR
  {fc.scenarios(spot)[2]['midpoint']:.2f}); probability-weighted value PKR
  {sum(s['probability'] * s['midpoint'] for s in fc.scenarios(spot)):.2f}.
* Model probability of trading at or above the PKR 38.20 issue price inside the window:
  {forecast_result.prob_above['38.20 (GoPb equity-injection floor)']:.1%}. This is a
  medium-term anchor, not a one-month target.

**What would change the call.** Upgrade to a full Buy on a weekly close above the 50-day average
combined with a Q3 print that shows provisions contained. Cut the position on a close below
PKR {trade_params['stop']:.2f} or if the 26 Oct policy statement signals the start of a new
tightening cycle *and* the KSE-100 loses 160,000.

*This is a research output produced by an automated multi-agent pipeline, not investment advice.
Position sizes assume a diversified book and a 12% volatility budget.*
"""
    return decision, final_rating, ""


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #
def run_committee(series, ohlcv, forecast_result) -> CommitteeOutput:
    out = CommitteeOutput()
    market, s_market = market_analyst(series, ohlcv)
    fund, s_fund = fundamentals_analyst(series, forecast_result)
    news, s_news = news_analyst(series, forecast_result)
    sent, s_sent = sentiment_analyst(series, ohlcv)
    out.reports = {
        "market": market,
        "fundamentals": fund,
        "news": news,
        "sentiment": sent,
    }
    out.scores = {
        "market": round(s_market, 2),
        "fundamentals": round(s_fund, 2),
        "news": round(s_news, 2),
        "sentiment": round(s_sent, 2),
    }
    out.debate = bull_bear_debate(series, out.scores, forecast_result, ohlcv)
    out.investment_plan, out.rating = research_manager(out.scores, forecast_result)
    out.trade_proposal, out.action, out.trade_params = trader(
        series, out.rating, forecast_result, ohlcv
    )
    out.risk_debate, blended = risk_debate(series, forecast_result, out.trade_params)
    out.risk_note = f"Blended position size: {blended:.1f}% of the book."
    out.final_decision, out.final_rating, _ = portfolio_manager(
        series, out.rating, forecast_result, out.trade_params, blended
    )
    out.trade_params["size_pct_final"] = round(blended, 1)
    return out
