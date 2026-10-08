"""Generic, profile-driven PSX committee (analysts -> debate -> trader -> risk -> PM).

The Bank of Punjab keeps its original hand-written committee in
:mod:`psx.agents` so that report reproduces bit-for-bit.  This module runs the
*same pipeline over the same data tools* for any other name, with every number
and every sentence drawn from a :class:`psx.profiles.Profile` and from the
analytics computed on that name's own series.  The output type is the same
:class:`psx.agents.CommitteeOutput`, so the report writer and the
TradingAgents bridge consume both interchangeably.
"""

from __future__ import annotations

import json
import math
import os
from typing import Sequence

from . import forecast as fc
from . import indicators as ind
from .agents import CommitteeOutput, _score
from .profiles import Profile

# Analyst weights and rating thresholds are identical to psx.agents so the two
# engines stay interchangeable.
SCORE_WEIGHTS = {"market": 0.20, "fundamentals": 0.30, "news": 0.25, "sentiment": 0.25}


def _fmt(value, nd: int = 2, suffix: str = "", na: str = "n/a") -> str:
    return na if value is None else f"{value:,.{nd}f}{suffix}"


# --------------------------------------------------------------------------- #
# analytics shared by the committee and the writer
# --------------------------------------------------------------------------- #
def direction_prob(f: fc.ForecastResult) -> float:
    """The probability the *holder* is up: cash received counts as return.

    With no distribution inside the window this is simply P(price higher).
    """
    return f.prob_up_total_return if f.dividend_total else f.prob_up


def total_return(f: fc.ForecastResult) -> float:
    """Expected total return: price change plus cash received, over spot."""
    return f.expected_price / f.spot - 1.0 + f.dividend_total / f.spot


def scenario_spec_from_model(profile: Profile, f: fc.ForecastResult) -> list[dict]:
    """Keep the committee's names, probabilities and triggers; take the levels
    from the model.  Bull = the 85th percentile path, bear = the 15th, and the
    ranges are the 5-35 / 30-70 / 65-95 percentile bands, so the book is a
    direct read of the distribution rather than a second opinion about levels.
    """
    q = f.quantiles
    bands = {
        "bull": (q["p75"], q["p95"], q["p90"], "model 90th percentile"),
        "base": (q["p25"], q["p75"], q["p50"], "model median"),
        "bear": (q["p5"], q["p25"], q["p10"], "model 10th percentile"),
    }
    spec = []
    for item in profile.scenarios:
        name = item["name"]
        key = "bull" if "bull" in name.lower() else "bear" if "bear" in name.lower() else "base"
        lo, hi, mid, basis = bands[key]
        spec.append({
            "name": name,
            "probability": item["probability"],
            "range": (round(lo, 2), round(hi, 2)),
            "midpoint": round(mid, 2),
            "basis": basis,
            "triggers": list(item.get("triggers", [])),
        })
    return spec


def long_run_reference(profile: Profile) -> tuple[float | None, str]:
    """A disclosed proxy for the 200-day average when the daily history is short.

    The five-year monthly series supports a 10-month average, which behaves
    like a 200-session average (10 x ~20 sessions).  The current month is
    excluded so the reference does not move with a part-formed bar.
    """
    if not profile.long_arc_path or not os.path.exists(profile.long_arc_path):
        # No long price arc for this name: fall back to the disclosed long-run
        # centre in the profile's level map (e.g. the mid-point of the 52-week
        # range), labelled so the reader knows it is a proxy.
        fallback = (profile.levels or {}).get("long_ma")
        if fallback:
            return float(fallback), "mid-point of the 52-week range (long-run proxy)"
        return None, ""
    with open(profile.long_arc_path, encoding="utf-8") as fh:
        raw = json.load(fh)
    closes = [float(c) for c in raw["closes"]][:-1]  # drop the part-formed month
    if len(closes) < 10:
        return None, ""
    window = closes[-10:]
    return sum(window) / len(window), "10-month average (200-day proxy)"


def compute_analytics(profile: Profile, series, ohlcv) -> dict:
    c = series.closes
    rows = ohlcv["rows"]
    spot = c[-1]
    sma20, sma50, sma100, sma200 = (ind.sma(c, n) for n in (20, 50, 100, 200))
    rsi = ind.rsi(c, 14)
    macd = ind.macd(c)
    bb = ind.bollinger(c)
    atr = ind.atr(rows, 14)
    vol20, vol250 = ind.realized_vol(c, 20), ind.realized_vol(c, 250)
    ewma = ind.ewma_vol(c)
    swings = ind.swing_levels(rows)
    recent_lows = [r["low"] for r in rows[-20:]] or [spot]
    recent_highs = [r["high"] for r in rows[-20:]] or [spot]

    long_ma, long_ma_label = long_run_reference(profile)
    if sma200 is None:
        sma200 = long_ma  # proxy, labelled as such wherever it is quoted
    score = 5.0
    score += 1.0 if (sma20 and spot > sma20) else -1.0
    score += 1.0 if (sma50 and spot > sma50) else -1.0
    score += 1.0 if (sma200 and spot > sma200) else -1.0
    score += 0.5 if (rsi and rsi < 30) else (-0.5 if (rsi and rsi > 70) else 0.0)
    score += 1.0 if (rsi and 30 <= rsi <= 45 and macd and macd["histogram"] and macd["histogram"] > -0.1) else 0.0
    dd = ind.drawdown_from_peak(c)
    score -= 0.5 if dd < -0.25 else 0.0
    score += 0.5 if (vol20 and vol250 and vol20 < vol250) else 0.0
    tech_score = max(0.0, min(10.0, score))

    vols = [r["volume"] for r in rows[-20:] if r.get("volume")]
    all_vols = [r["volume"] for r in rows if r.get("volume")]
    support = min(profile.anchor("support", min(recent_lows)), min(recent_lows))
    resistance = max(profile.anchor("resistance", max(recent_highs)), max(recent_highs)) \
        if profile.anchor("resistance") else max(recent_highs)
    return {
        "spot": spot,
        "sessions": len(c),
        "closes": c,
        "dates": series.dates,
        "sma20": sma20, "sma50": sma50, "sma100": sma100, "sma200": sma200,
        "sma200_is_proxy": ind.sma(c, 200) is None and sma200 is not None,
        "sma200_label": long_ma_label or "200-day average",
        "ema12": ind.ema(c, 12), "ema26": ind.ema(c, 26), "rsi": rsi, "macd": macd,
        "bollinger": bb, "atr": atr,
        "vol20": vol20, "vol250": vol250, "ewma_vol": ewma,
        "drawdown": dd, "max_drawdown": ind.max_drawdown(c),
        "r5": ind.total_return(c, 5), "r21": ind.total_return(c, 21),
        "r63": ind.total_return(c, 63), "r126": ind.total_return(c, 126),
        "r252": ind.total_return(c, 252),
        "swings": swings,
        "support": support, "resistance": resistance,
        "avg_vol20": (sum(vols) / len(vols)) if vols else None,
        "avg_vol_all": (sum(all_vols) / len(all_vols)) if all_vols else None,
        "tech_score": tech_score,
        "skew": ind.skewness(ind.log_returns(c)),
        "kurtosis": ind.excess_kurtosis(ind.log_returns(c)),
        "var5_hist": ind.historical_var(c, 0.05),
    }


# --------------------------------------------------------------------------- #
# analyst layer
# --------------------------------------------------------------------------- #
def market_analyst(profile: Profile, a: dict, series) -> tuple[str, float]:
    spot = a["spot"]
    ma_state = []
    for label, ma in (("20-day", a["sma20"]), ("50-day", a["sma50"]),
                      ("100-day", a["sma100"]),
                      (a["sma200_label"] if a["sma200_is_proxy"] else "200-day", a["sma200"])):
        if ma is None:
            ma_state.append(f"**{label} n/a** (not enough history)")
        else:
            ma_state.append(f"**{label}** PKR {ma:,.2f} ({'above' if spot > ma else 'below'})")
    hist = ", ".join(f"{d}: {c:,.2f}" for d, c in list(zip(a["dates"], a["closes"]))[-5:])
    report = f"""### Market Analyst - trend, momentum and levels

**Where the tape is.** {profile.notes.get('market', '')}

| Measure | Value | Reading |
|---------|-------|---------|
| Spot (last settled session) | PKR {spot:,.2f} | {profile.spot_date} |
| Trend vs moving averages | {' / '.join(ma_state)} | {'uptrend' if (a['sma50'] and spot > a['sma50'] and a['sma200'] and spot > a['sma200']) else 'mixed' if (a['sma50'] and spot > a['sma50']) else 'down'} |
| RSI(14) | {_fmt(a['rsi'], 1)} | {'oversold' if a['rsi'] and a['rsi'] < 30 else 'overbought' if a['rsi'] and a['rsi'] > 70 else 'neutral'} |
| MACD / signal / histogram | {_fmt(a['macd']['macd'], 3)} / {_fmt(a['macd']['signal'], 3)} / {_fmt(a['macd']['histogram'], 3)} | {'positive' if a['macd']['histogram'] > 0 else 'negative'} momentum |
| ATR(14) | PKR {_fmt(a['atr'])} ({_fmt((a['atr'] / spot * 100) if a['atr'] else None, 1, '%')} of price) | daily swing budget |
| Annualised vol 20d / 250d | {_fmt((a['vol20'] or 0) * 100, 1, '%')} / {_fmt((a['vol250'] or 0) * 100, 1, '%')} | {'calming' if (a['vol20'] and a['vol250'] and a['vol20'] < a['vol250']) else 'elevated'} |
| Drawdown from peak | {a['drawdown'] * 100:.1f}% (max {a['max_drawdown'] * 100:.1f}%) | {'deep' if a['drawdown'] < -0.2 else 'moderate'} |
| Support / resistance (20d + anchors) | PKR {a['support']:,.2f} / PKR {a['resistance']:,.2f} | {profile.levels.get('support_label', '')} / {profile.levels.get('resistance_label', '')} |
| Last five sessions | {hist} | |

**Score: {a['tech_score']:.1f}/10** - {'price above the short averages in a repaired trend' if a['sma50'] and spot > a['sma50'] else 'price below the key averages, trend still down'} with
momentum {'turning up' if a['macd']['histogram'] > -0.05 else 'still negative'} and volatility
{'below' if (a['vol20'] and a['vol250'] and a['vol20'] < a['vol250']) else 'above'} its one-year average.
"""
    return report, a["tech_score"]


def fundamentals_analyst(profile: Profile, series, f: fc.ForecastResult) -> tuple[str, float]:
    spot = series.closes[-1]
    quote = profile.quote
    comps = profile.score_components
    total_w = sum(c["weight"] for c in comps) or 1.0
    score = 0.0
    rows = []
    for comp in comps:
        s = _score(comp["value"], good=comp["good"], bad=comp["bad"],
                   higher_is_better=comp["higher_is_better"])
        score += s * comp["weight"]
        rows.append((comp["name"], comp["value"], s))
    score = max(0.0, min(10.0, score / total_w))

    mcap = profile.shares_out * spot
    table = "\n".join(
        f"| {name} | {value:,.2f} | {s:.1f}/10 |" for name, value, s in rows
    )
    facts = "\n".join(f"- {item['fact']} *({item['source']}, {item['date']})*"
                      for item in profile.company[:4])
    report = f"""### Fundamentals Analyst - valuation and earnings

**Where it stands.** {profile.business}

**Valuation.** At PKR {spot:,.2f} the market capitalisation is ~PKR {mcap / 1e9:,.1f}bn
({profile.shares_out / 1e6:,.1f}mn shares outstanding).
{_valuation_line(profile, spot)}

**Scorecard (0-10 per dimension, weighted {', '.join(f'{c["weight"]:.0%}' for c in comps)}):**

| Dimension | Input | Score |
|-----------|-------|-------|
{table}

**Composite fundamentals score: {score:.2f}/10.** {profile.notes.get('fundamentals', '')}

**What the latest filings say.**
{facts}
"""
    return report, score


def _valuation_line(profile: Profile, spot: float) -> str:
    q = profile.quote
    bits = []
    if q.get("pe"):
        tail = f"**{q['pe']:.2f}x** trailing earnings"
        if q.get("pe_forward"):
            tail += f" ({q['pe_forward']:.2f}x forward)"
        bits.append(tail)
    if q.get("bvps"):
        bits.append(f"**{spot / q['bvps']:.2f}x** book value per share of PKR {q['bvps']:,.2f}")
    if q.get("dividend"):
        bits.append(f"a PKR {q['dividend']:.2f} dividend is a **{q['dividend'] / spot * 100:.2f}%** yield")
    if q.get("target"):
        bits.append(f"consensus target **PKR {q['target']:,.2f}** ({q['target'] / spot - 1:+.0%}) from "
                    f"{q.get('analysts', 0)} analysts ({q.get('consensus')})")
    else:
        bits.append("no analyst coverage or published target to anchor the price")
    if q.get("beta"):
        bits.append(f"beta {q['beta']:.2f}")
    return " - ".join(bits) + "."


def news_analyst(profile: Profile, series, f: fc.ForecastResult) -> tuple[str, float]:
    company_pos = [x for x in profile.company if x["direction"] == "positive"]
    company_neg = [x for x in profile.company if x["direction"] == "negative"]
    sector_neg = [x for x in profile.sector_facts if x["direction"] == "negative"]
    sector_pos = [x for x in profile.sector_facts if x["direction"] == "positive"]
    macro_pos = [x for x in profile.macro if x["direction"] == "positive"]
    macro_neg = [x for x in profile.macro if x["direction"] == "negative"]
    macro_score = max(0.0, min(10.0, 5.0 + 0.6 * len(macro_pos) - 0.7 * len(macro_neg)))
    company_score = max(0.0, min(10.0, 5.0 + 0.8 * (len(company_pos) + len(sector_pos))
                                - 0.8 * (len(company_neg) + len(sector_neg))))
    score = 0.5 * macro_score + 0.5 * company_score

    event_rows = "\n".join(f"| {e['date']} | {e['event']} | {e['why']} |" for e in profile.events)
    macro_bullets = "\n".join(f"- **{m['headline']}** - {m['detail']}" for m in profile.macro)
    report = f"""### News Analyst - macro and event tape

{profile.notes.get('news', '')}

**The macro tape.**

{macro_bullets}

**The event calendar inside the forecast window (to {f.horizon_end}).**

| Date | Event | Why it matters |
|------|-------|----------------|
{event_rows}

**Score split.** Macro tape {macro_score:.1f}/10, company and sector newsflow
{company_score:.1f}/10 (equal-weighted). Supportive: {macro_pos[0]['headline'] if macro_pos else 'none carried'}.
Hostile: {macro_neg[0]['headline'] if macro_neg else 'none carried'}.
The dominant company-flow {'positive' if len(company_pos) >= len(company_neg) else 'negative'} is
"{company_pos[0]['fact'][:120] if company_pos else company_neg[0]['fact'][:120] if company_neg else 'n/a'}..."
"""
    return report, score


def sentiment_analyst(profile: Profile, ohlcv, a: dict) -> tuple[str, float]:
    q = profile.quote
    spot = a["spot"]
    score = 5.0
    r1m = a["r21"]
    score += 0.8 if (r1m is not None and r1m > -0.05) else -0.8
    if a["avg_vol20"] and a["avg_vol_all"]:
        score += 0.7 if a["avg_vol20"] > a["avg_vol_all"] else -0.3
    score += 0.5 if (a["rsi"] and a["rsi"] < 40) else 0.0
    score = max(0.0, min(10.0, score))

    if q.get("target"):
        consensus = (f"Sell-side consensus is a **{q.get('consensus')}** ({q.get('analysts', 0)} analysts) "
                     f"with a 12-month target of **PKR {q['target']:,.2f}**, about "
                     f"{q['target'] / spot - 1:+.0%} from spot.")
    else:
        consensus = ("No broker covers this name in the data set, so there is no consensus estimate or "
                     "price target to anchor sentiment - flows are set by the shareholder register "
                     f"({q.get('float_pct', 0):.0%} free float) and by the index.")
    report = f"""### Sentiment Analyst - positioning and flows

{consensus}

Market-structure evidence: the stock is {_fmt((a['r21'] or 0) * 100, 1, '%')} over one month,
{_fmt((a['r63'] or 0) * 100, 1, '%')} over three months and {a['drawdown'] * 100:.0f}% below its
high; 20-day average volume ({_fmt((a['avg_vol20'] or 0) / 1e6, 2)}mn shares) is
{'above' if (a['avg_vol20'] or 0) > (a['avg_vol_all'] or 0) else 'below'} the full-window average
({_fmt((a['avg_vol_all'] or 0) / 1e6, 2)}mn). {profile.notes.get('sentiment', '')}

**Score: {score:.1f}/10.**
"""
    return report, score


# --------------------------------------------------------------------------- #
# research debate + manager
# --------------------------------------------------------------------------- #
def bull_bear_debate(profile: Profile, a: dict, scores: dict, f: fc.ForecastResult) -> dict:
    spot = a["spot"]
    bull_points = "\n".join(f"{i}. {p}" for i, p in enumerate(profile.bull, 1))
    bear_points = "\n".join(f"{i}. {p}" for i, p in enumerate(profile.bear, 1))
    bull = f"""**Bull case.**

{bull_points}
"""
    bear = f"""**Bear case.**

{bear_points}
"""
    return {"bull": bull, "bear": bear}


def research_manager(profile: Profile, scores: dict, f: fc.ForecastResult) -> tuple[str, str]:
    composite = sum(scores[k] * w for k, w in SCORE_WEIGHTS.items())
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
    plan = f"""### Research Manager - investment plan

**Composite score: {composite:.2f}/10** (market {scores['market']:.1f} weighted 20%, fundamentals
{scores['fundamentals']:.1f} 30%, news {scores['news']:.1f} 25%, sentiment {scores['sentiment']:.1f} 25%).

{profile.notes.get('manager', '')}

Over the next {f.horizon_sessions} sessions the distribution is
{'skewed to the upside' if direction_prob(f) > 0.55 else 'skewed to the downside' if direction_prob(f) < 0.45 else 'close to symmetric'}:
**P(positive total return) = {direction_prob(f):.0%}**
(P(price higher) = {f.prob_up:.0%} after the {f.dividend_total / f.spot:.1%} cash step on the ex-date),
median price PKR {f.quantiles['p50']:,.2f}, 80% interval
PKR {f.quantiles['p10']:,.2f}-PKR {f.quantiles['p90']:,.2f}, expected value
PKR {f.expected_price:,.2f} ({f.expected_return * 100:+.1f}% price, {total_return(f) * 100:+.1f}% total). That distribution is a
"{rating}".
"""
    return plan, rating


# --------------------------------------------------------------------------- #
# trader + risk + PM
# --------------------------------------------------------------------------- #
def trader(profile: Profile, series, rating: str, f: fc.ForecastResult, a: dict) -> tuple[str, str, dict]:
    spot = a["spot"]
    atr = a["atr"] or spot * 0.03
    support = a["support"]
    entry_lo, entry_hi = round(support * 1.005, 2), round(spot * 1.02, 2)
    stop = round(support - 1.5 * atr, 2)
    target1 = round(max(a["sma200"] or 0.0, a["resistance"]), 2)
    target2 = profile.anchor("resistance_2", profile.anchor("book", target1 * 1.1))
    risk_per_share = max(0.01, (entry_lo + entry_hi) / 2 - stop)
    rr = (target1 - (entry_lo + entry_hi) / 2) / risk_per_share if risk_per_share else 0.0
    vol_pct = max(1.0, f.annual_vol * 100)
    size_pct = round(min(8.0, max(2.0, 12.0 / vol_pct * 100 * 33.0 / 100 / 3)), 1)
    action = "Buy" if rating in ("Buy", "Overweight") else ("Hold" if rating == "Hold" else "Sell")

    plan = f"""### Trader - transaction proposal

**Action: {action} ({'scaled accumulation' if action == 'Buy' else 'hold / accumulate on weakness' if action == 'Hold' else 'reduce'}).**

| Parameter | Level | Rationale |
|-----------|-------|-----------|
| Entry zone | PKR {entry_lo:,.2f} - {entry_hi:,.2f} | {profile.levels.get('support_label', 'support')} up to a 2% band above spot |
| Stop | PKR {stop:,.2f} | 1.5 x ATR(14) below support; a weekly close below invalidates the thesis |
| Target 1 | PKR {target1:,.2f} | {profile.levels.get('resistance_label', 'first resistance')} |
| Target 2 | PKR {target2:,.2f} | {profile.levels.get('resistance_2_label', 'strategic anchor')} |
| Risk/reward | {rr:.1f} : 1 | on a first-target basis |
| Position size | {size_pct:.1f}% of the book | volatility-targeted: a ~{vol_pct:.0f}% annualised vol name gets a modest weight |

**Execution notes.** {profile.notes.get('trader', '')} Over the full path to {f.horizon_end} the
model puts {_touch_below(f, stop):.1%} on the price *touching* the PKR {stop:,.2f} stop at some point
and {_touch_above(f, target2):.1%} on it touching PKR {target2:,.2f} (target 2); on the horizon date
itself the odds of finishing at or below the stop are
{fc.prob_close_below(f, stop):.1%}. The invalidation level for a trend call is a
weekly close through {_fmt(a['sma50'])} (the 50-day), with the 20-day at {_fmt(a['sma20'])}.
{profile.notes.get('execution', '')}
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


def _touch_above(f: fc.ForecastResult, level: float) -> float:
    return sum(1 for m in f.path_maxima if m >= level) / len(f.path_maxima) if f.path_maxima else 0.0


def _touch_below(f: fc.ForecastResult, level: float) -> float:
    return sum(1 for m in f.path_minima if m <= level) / len(f.path_minima) if f.path_minima else 0.0


def _label_for(profile: Profile, price: float) -> str:
    for t in profile.thresholds:
        if abs(t["price"] - price) < 0.02:
            return t["label"]
    return ""


def risk_debate(profile: Profile, series, f: fc.ForecastResult, trade_params: dict,
                a: dict) -> tuple[dict, float]:
    vol = f.annual_vol * 100
    spot = a["spot"]
    top_risk = profile.risks[0]["risk"] if profile.risks else "event risk"
    aggressive = f"""**Aggressive analyst.** A {vol:.0f}% vol stock with a {direction_prob(f):.0%} probability of
being higher in a month is a position to size up, not a watch item. The stop is only
{(trade_params['entry_zone'][0] - trade_params['stop']) / trade_params['entry_zone'][0] * 100:.1f}%
below entry, the first target is {trade_params['target_1'] / spot - 1:+.0%} away and the second is
{trade_params['target_2'] / spot - 1:+.0%}. Push the position to the top of the size band and use
the scheduled events ({profile.events[0]['date']}, {profile.events[1]['date'] if len(profile.events) > 1 else 'the results date'})
as the trigger for the second tranche.
"""
    neutral = f"""**Neutral analyst.** The expected return is {total_return(f) * 100:+.1f}% over the
window against a 5% VaR of {f.var_5 * 100:.1f}% and CVaR of {f.cvar_5 * 100:.1f}%: the distribution
rewards patience rather than conviction. That argues for the middle of the size band, staged
entries and no leverage. The biggest avoidable risk is event clustering: the single worst item on
this name's register - "{top_risk.lower()}" - lands inside the window.
"""
    conservative = f"""**Conservative analyst.** {profile.risks[0]['why'] if profile.risks else ''} A
{abs(a['max_drawdown']) * 100:.0f}% peak-to-trough drawdown in the loaded history shows how quickly
the position can move against you. Cap the name at half the vol-targeted size until the first
scheduled event clears, and review immediately if the index loses the level that has defined the
recent range.
"""
    note = f"""The risk team converged on a blended position: aggressive
{min(10.0, trade_params['size_pct'] * 1.5):.1f}% / neutral {trade_params['size_pct']:.1f}% /
conservative {max(1.0, trade_params['size_pct'] * 0.5):.1f}%, weighted 30/45/25. Non-negotiables:
no averaging down below PKR {trade_params['stop']:,.2f}; no more than a third of the position before
the first scheduled event; and a hard review if the broad index breaks its range, because that
would make macro and political risk - not company fundamentals - the binding constraint.
"""
    weights = {"aggressive": 0.30, "neutral": 0.45, "conservative": 0.25}
    blended = (weights["aggressive"] * min(10.0, trade_params["size_pct"] * 1.5)
               + weights["neutral"] * trade_params["size_pct"]
               + weights["conservative"] * max(1.0, trade_params["size_pct"] * 0.5))
    return {"aggressive": aggressive, "neutral": neutral, "conservative": conservative, "note": note}, blended


def portfolio_manager(profile: Profile, a: dict, rating: str, f: fc.ForecastResult,
                      trade_params: dict, blended: float, scenarios: Sequence[dict]) -> tuple[str, str]:
    spot = a["spot"]
    probs = [s["probability"] for s in scenarios] or [0.0]
    weighted_value = sum(s["probability"] * s["midpoint"] for s in scenarios)
    falsification = "\n".join(f"- {item}" for item in profile.falsification)
    decision = f"""## Portfolio Manager - final decision

**{rating.upper()}** (position size {blended:.1f}% of the book, built in thirds, stop
PKR {trade_params['stop']:,.2f}).

**The one-paragraph version.** {profile.notes.get('pm', '')}

**Explicit 30-day call (forecast made {f.as_of}, horizon {f.horizon_end}, {f.horizon_sessions} sessions):**

* Direction: **{'modestly higher' if direction_prob(f) > 0.55 else 'close to a coin flip' if direction_prob(f) >= 0.45 else 'modestly lower'}** -
  P(total return > 0) {direction_prob(f):.0%}; expected price
  PKR {f.expected_price:,.2f} ({f.expected_return * 100:+.1f}% on the printed price,
  {total_return(f) * 100:+.1f}% once the PKR {f.dividend_total:,.2f} cash is counted).
* Central band: **PKR {f.quantiles['p25']:,.2f} - {f.quantiles['p75']:,.2f}** (interquartile), full
  80% interval PKR {f.quantiles['p10']:,.2f} - {f.quantiles['p90']:,.2f}.
* Scenario book: {'; '.join(f"{s['name'].split(' - ')[0].split(' — ')[0]} {s['probability']:.0%} (PKR {s['midpoint']:,.2f})" for s in scenarios)};
  probability-weighted value PKR {weighted_value:,.2f}.
* Over the full path to {f.horizon_end} the model puts
  {_touch_above(f, trade_params['target_2']):.1%} on touching PKR {trade_params['target_2']:,.2f} (target 2)
  and {_touch_below(f, trade_params['stop']):.1%} on touching the PKR {trade_params['stop']:,.2f} stop;
  at the horizon itself the probabilities are
  {fc.prob_close_above(f, trade_params['target_2']):.1%} and
  {f.prob_below.get(_label_for(profile, trade_params['stop']), 0.0):.1%}.

**What would change the call.** {profile.notes.get('pm_rules', '')}

*This is a research output produced by an automated multi-agent pipeline, not investment advice.
Position sizes assume a diversified book and a 12% volatility budget.*
"""
    return decision, rating


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #
def run_committee(profile: Profile, series, ohlcv, forecast_result: fc.ForecastResult) -> CommitteeOutput:
    a = compute_analytics(profile, series, ohlcv)
    out = CommitteeOutput()
    market, s_market = market_analyst(profile, a, series)
    fund, s_fund = fundamentals_analyst(profile, series, forecast_result)
    news, s_news = news_analyst(profile, series, forecast_result)
    sent, s_sent = sentiment_analyst(profile, ohlcv, a)
    out.reports = {"market": market, "fundamentals": fund, "news": news, "sentiment": sent}
    out.scores = {k: round(v, 2) for k, v in
                  (("market", s_market), ("fundamentals", s_fund), ("news", s_news), ("sentiment", s_sent))}
    out.debate = bull_bear_debate(profile, a, out.scores, forecast_result)
    out.investment_plan, out.rating = research_manager(profile, out.scores, forecast_result)
    out.trade_proposal, out.action, out.trade_params = trader(
        profile, series, out.rating, forecast_result, a)
    out.risk_debate, blended = risk_debate(profile, series, forecast_result, out.trade_params, a)
    out.risk_note = f"Blended position size: {blended:.1f}% of the book."
    out.final_decision, out.final_rating = portfolio_manager(
        profile, a, out.rating, forecast_result, out.trade_params, blended,
        fc.scenarios(forecast_result.spot, profile.scenarios))
    out.trade_params["size_pct_final"] = round(blended, 1)
    return out


def model_robustness(closes: Sequence[float], f: fc.ForecastResult, seed: int = 20261007) -> dict:
    """Student-t(4) cross-check of the bootstrap for short-history names.

    With ~50 sessions the empirical pool is thin, so the tails are also
    estimated from a scaled t(4) fitted to the same EWMA volatility.  The
    result is reported alongside the bootstrap band, never instead of it.
    """
    import random

    rng = random.Random(seed + 1)
    nu = 4
    paths = 20_000
    sigma = f.daily_vol * math.sqrt(nu / (nu - 2))  # unit-variance student-t
    span = f.horizon_sessions
    step_drop = (f.dividend_total / f.spot) if f.dividend_total else 0.0  # applied at the ex-date
    drop_session = span - 8 if f.dividend_total else 0   # session 9 of 22, i.e. not the last step
    out = []
    for _ in range(paths):
        shock = sum(rng.gauss(0.0, 1.0) for _ in range(span))
        chi = sum(rng.gauss(0.0, 1.0) ** 2 for _ in range(nu))
        price = f.spot * math.exp(sigma * shock / math.sqrt(chi / nu))
        if step_drop:
            price *= (1.0 - step_drop)
        out.append(price)
    return {
        "distribution": f"student-t({nu}) scaled to the same EWMA volatility",
        "p10": ind.quantile(out, 0.10),
        "p50": ind.quantile(out, 0.50),
        "p90": ind.quantile(out, 0.90),
        "prob_up": sum(1 for p in out if p > f.spot) / len(out),
        "prob_up_total_return": sum(1 for p in out if p > f.spot - f.dividend_total) / len(out),
        "dividend_applied": f.dividend_total,
        "paths": paths,
    }
