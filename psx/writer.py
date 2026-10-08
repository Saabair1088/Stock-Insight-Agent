"""Profile-driven report writer (markdown, HTML, forecast JSON, SVG charts).

Renders the same deliverable set as the Bank of Punjab report - deep research
plus a 30-day movement forecast - for any name in :mod:`psx.profiles`, from the
committee in :mod:`psx.analysts` and the distribution from
:mod:`psx.forecast`.  Charts reuse the SVG builders in :mod:`psx.report` with
per-name reference marks.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from . import forecast as fc
from . import report as rp
from .profiles import Profile

REPORTS_DIR = rp.REPORTS_DIR


def _fmt(value, nd: int = 2, suffix: str = "", na: str = "n/a") -> str:
    return na if value is None else f"{value:,.{nd}f}{suffix}"


def _pct(value, nd: int = 1, na: str = "n/a") -> str:
    return na if value is None else f"{value * 100:+.{nd}f}%"


def _snapshot_table(profile: Profile, a: dict) -> str:
    q = profile.quote
    rows = [
        ("Last settled close", f"PKR {a['spot']:,.2f} ({profile.spot_date})"),
        ("52-week range", f"PKR {q.get('week52_low', float('nan')):,.2f} - "
                          f"PKR {q.get('week52_high', float('nan')):,.2f}"),
        ("Market capitalisation", f"PKR {profile.shares_out * a['spot'] / 1e9:,.2f}bn"),
        ("Shares outstanding", f"{profile.shares_out / 1e6:,.1f}mn"),
        ("Price / earnings", f"{q['pe']:.2f}x trailing" + (
            f" ({q['pe_forward']:.2f}x forward)" if q.get("pe_forward") else "") if q.get("pe") else "n/a"),
        ("Price / book", f"{a['spot'] / q['bvps']:.2f}x (BVPS PKR {q['bvps']:,.2f})"
         if q.get("bvps") else "n/a"),
        ("Dividend", f"PKR {q['dividend']:,.2f} ({q['dividend'] / a['spot'] * 100:.2f}% yield, "
                     f"{q.get('payout', 0) * 100:.0f}% payout)" if q.get("dividend") else "n/a"),
        ("Consensus", f"{q.get('consensus')} - target PKR {q['target']:,.2f} "
                      f"({q['target'] / a['spot'] - 1:+.0%}, {q.get('analysts', 0)} analysts)"
         if q.get("target") else "no published coverage"),
        ("Beta", f"{q['beta']:.2f}" if q.get("beta") else "n/a"),
        ("Free float", f"{q['float_pct'] * 100:.1f}%" if q.get("float_pct") else "n/a"),
    ]
    body = "\n".join(f"| {k} | {v} |" for k, v in rows)
    return f"| Measure | Value |\n|---------|-------|\n{body}"


def _path_extremes(f: fc.ForecastResult) -> dict:
    """Where the journey can plausibly go, independent of where it finishes."""
    if not f.path_minima:
        return {}
    out = {}
    for side, values in (("path_low", f.path_minima), ("path_high", f.path_maxima)):
        ordered = sorted(values)
        n = len(ordered)
        for q in (5, 25, 50, 75, 95):
            out[f"{side}_p{q}"] = round(ordered[min(n - 1, int(q / 100 * n))], 2)
    return out


def _regime_blurb(profile: Profile, analytics: dict) -> str:
    """Describe the drift mixture in plain words, using the actual weights."""
    w = profile.regime_weights or {}
    mart = w.get("martingale", 0.35)
    rev = w.get("mean_reversion", 0.45)
    cat = w.get("catalyst", 0.15)
    anchor = analytics.get("sma200")
    anchor_txt = f"PKR {anchor:,.2f}" if anchor else "the long-run average"
    return (
        f"a zero-drift martingale leg for the bulk of the variance ({mart:.0%}), "
        f"a pull toward {anchor_txt} that fades as the horizon stretches ({rev:.0%}), and a small "
        f"catalyst overlay for the event calendar inside the window ({cat:.0%})"
    )


def _anchor_line(analytics: dict) -> str:
    if analytics.get("sma200"):
        label = analytics.get("sma200_label") if analytics.get("sma200_is_proxy") else "the 200-day average"
        return f"PKR {analytics['sma200']:,.2f} ({label})"
    return "the long-run average (not enough history to compute one, so the leg is switched off)"


def _dividend_block(profile: Profile, f: fc.ForecastResult) -> tuple[str, str]:
    """Row for the quantile table and the paragraph that keeps the two
    probabilities apart when cash goes ex inside the window."""
    if not f.dividend_total:
        return "", ""
    label = "; ".join(e["label"] if isinstance(e, dict) else str(e) for e in profile.cash_events)
    pct = f.dividend_total / f.spot
    row = (f"\n| Cash distribution inside the window | PKR {f.dividend_total:,.2f} per share "
           f"({pct:.2%}) - {label} |")
    para = (
        f"\n**Two probabilities, one window.** PKR {f.dividend_total:,.2f} a share goes ex inside "
        f"this window ({label}), so the printed price falls by about {pct:.1%} on that day with no "
        f"change in value received. The distribution above is a *price* distribution, which is what "
        f"stops, targets and level probabilities refer to: P(price higher on {f.horizon_end}) is "
        f"**{f.prob_up:.1%}** and the median is "
        f"PKR {f.quantiles['p50']:,.2f}. Once the cash is counted, the probability of a positive "
        f"*total return* is **{f.prob_up_total_return:.1%}** - that is the number to compare against "
        f"a deposit or a T-bill.\n")
    return row, para


def _distribution_tables(profile: Profile, f: fc.ForecastResult,
                         dividend_row: str = "") -> tuple[str, str]:
    quant = f"""| Statistic | Value |
|-----------|-------|
| Spot (forecast base) | PKR {f.spot:,.2f} |
| P(price higher) | {f.prob_up:.1%} |
| P(price lower) | {f.prob_down:.1%} |
| Expected price | PKR {f.expected_price:,.2f} ({f.expected_return * 100:+.2f}%) |
| Median (p50) | PKR {f.quantiles['p50']:,.2f} |
| Interquartile band (p25-p75) | PKR {f.quantiles['p25']:,.2f} - {f.quantiles['p75']:,.2f} |
| 80% interval (p10-p90) | PKR {f.quantiles['p10']:,.2f} - {f.quantiles['p90']:,.2f} |
| 5% VaR / CVaR at the horizon | {f.var_5 * 100:.1f}% / {f.cvar_5 * 100:.1f}% |
| Annualised volatility (EWMA) | {f.annual_vol * 100:.1f}% |
| Horizon | {f.horizon_sessions} sessions to {f.horizon_end} |{dividend_row}"""

    rows = []
    for t in profile.thresholds:
        above = f.prob_above.get(t["label"], 0.0)
        below = f.prob_below.get(t["label"], 0.0)
        touch = (f.touch_above.get(t["label"], 0.0) if t["price"] >= f.spot
                 else f.touch_below.get(t["label"], 0.0))
        rows.append(f"| {t['label']} | {above:.1%} | {below:.1%} | {touch:.1%} |")
    thr = ("| Level | P(close at or above on the horizon date) | P(close at or below) | "
           "P(the price trades through it at any point) |\n"
           "|-------|------------------------------------------|----------------------|"
           "--------------------------|\n" + "\n".join(rows))
    return quant, thr


def render_markdown(profile: Profile, series, ohlcv, f: fc.ForecastResult, committee, analytics: dict,
                    scenarios: list[dict], robustness: dict | None = None,
                    framework_dir: str | None = None) -> str:
    a = analytics
    q = profile.quote
    p_dir = f.prob_up_total_return if f.dividend_total else f.prob_up
    call = ("modestly higher" if p_dir > 0.55 else "close to a coin flip"
            if p_dir >= 0.45 else "modestly lower")
    dividend_row, dividend_para = _dividend_block(profile, f)
    if f.dividend_total:
        banner_prob = (f"PKR {f.dividend_total:,.2f} a share goes ex inside the window, so the "
                       f"printed price carries a known step down; the probability of a **positive "
                       f"total return** (price change plus cash) is **{f.prob_up_total_return:.1%}**, "
                       f"while the probability that the *price* closes above PKR {f.spot:,.2f} on "
                       f"{f.horizon_end} is {f.prob_up:.1%}. The price median is "
                       f"PKR {f.quantiles['p50']:,.2f} with an 80% band of "
                       f"**PKR {f.quantiles['p10']:,.2f} to PKR {f.quantiles['p90']:,.2f}**.")
    else:
        banner_prob = (f"Probability that {profile.ticker} closes above PKR {f.spot:,.2f} on "
                       f"{f.horizon_end} is **{f.prob_up:.1%}**; the median outcome is "
                       f"PKR {f.quantiles['p50']:,.2f} "
                       f"({f.quantiles['p50'] / f.spot - 1:+.2%}) with an 80% band of "
                       f"**PKR {f.quantiles['p10']:,.2f} to PKR {f.quantiles['p90']:,.2f}**.")
    quant_tbl, thr_tbl = _distribution_tables(profile, f, dividend_row)

    evidence = []
    for item in profile.company:
        evidence.append(f"| {item['date']} | Company | {item['fact']} | {item['source']} | {item['direction']} |")
    for item in profile.sector_facts:
        evidence.append(f"| {item['date']} | Sector | {item['fact']} | {item['source']} | {item['direction']} |")
    for item in profile.macro:
        evidence.append(f"| {profile.as_of} | Macro | {item['headline']} - {item['detail']} | -- | {item['direction']} |")
    evidence_tbl = "\n".join(evidence)

    scorecard = "\n".join(f"| {s['dimension']} | {s['score']} | {s['comment']} |" for s in profile.scorecard)
    risk_rows = "\n".join(f"| {r['risk']} | {r['why']} | {r['severity']} |" for r in profile.risks)
    f_regime_paths = sum(len(v) for v in [f.path_minima] or [])
    scenario_rows = "\n".join(
        f"| {s['name']} | {s['probability']:.0%} | PKR {s['target_range'][0]:,.2f} - "
        f"PKR {s['target_range'][1]:,.2f} | PKR {s['midpoint']:,.2f} ({s['return_pct'] * 100:+.1f}%) | "
        + "<br>".join(s["triggers"]) + " |"
        for s in scenarios
    )
    weighted = sum(s["probability"] * s["midpoint"] for s in scenarios)
    recent = ", ".join(f"{d}: {c:,.2f}" for d, c in list(zip(series.dates, series.closes))[-8:])
    caveats = "\n".join(f"- {c}" for c in profile.data_caveats)
    sources = "\n".join(f"- {s}" for s in profile.sources)

    robustness_md = ""
    if robustness:
        robustness_md = f"""
**Model robustness (short-history cross-check).** With {len(series.closes)} settled sessions the
empirical pool is thin, so the same EWMA volatility is also run through a
**{robustness['distribution']}** with {robustness['paths']:,} paths (the same cash step applied):
median PKR {robustness['p50']:,.2f}, 80% interval
PKR {robustness['p10']:,.2f}-PKR {robustness['p90']:,.2f}, P(price higher)
{robustness['prob_up']:.1%}, P(positive total return) {robustness['prob_up_total_return']:.1%}. That is
{'consistent with' if abs(robustness['p50'] - f.quantiles['p50']) / f.spot < 0.03 else 'somewhat different from'}
the headline bootstrap band; where they disagree, the student-t band is the honest one for the
tails because 50 observations cannot describe a fat tail.
"""

    framework_md = ""
    if framework_dir:
        framework_md = (f"\n> The vendored **TradingAgents** graph was also run end-to-end on this "
                        f"name; its own report tree is written to `{framework_dir}`.\n")

    md = f"""# {profile.name} (PSX: {profile.ticker}) - deep research and 30-day movement forecast

*{profile.sector} | prices in PKR | report {profile.as_of} | market data through {profile.spot_date}*

> **30-day movement prediction: {call}.** {banner_prob} Committee verdict:
> **{committee.final_rating.upper()}**, {committee.action.lower()} proposal, position size
> {committee.trade_params.get('size_pct_final', committee.trade_params['size_pct']):.1f}% of a
> diversified book, stop PKR {committee.trade_params['stop']:,.2f}.
{framework_md}
## 1. Where the stock stands

{_snapshot_table(profile, a)}

**Recent sessions:** {recent}

**The one-line story.** {profile.business} {profile.notes.get('market', '')}

## 2. The 30-day distribution (Monte-Carlo, {f.horizon_sessions} sessions)

{quant_tbl}

![price](chart_price.svg)

**The levels that matter.** The first two columns describe where the price *finishes* on the
horizon date; the last describes the odds it *gets there at any point* on the way:

{thr_tbl}

![distribution](chart_dist.svg)
{dividend_para}
**Method.** {f_regime_paths:,} simulated paths over a trailing empirical return pool (block
bootstrap, blocks of five sessions, so volatility clustering survives) rescaled to today's EWMA
volatility of {f.daily_vol * 100:.2f}% a day, mixed across three documented drift regimes:
{_regime_blurb(profile, analytics)}.
The output is a *distribution*, not a point forecast - the median, the 80% interval and the stated
triggers are the deliverable. Regime weights
{', '.join(f"{k} {v:.2f}" for k, v in (profile.regime_weights or {}).items())}.
{robustness_md}
## 3. Analyst reports

{committee.reports['market']}

{committee.reports['fundamentals']}

{committee.reports['news']}

{committee.reports['sentiment']}

## 4. Bull versus bear debate

{committee.debate['bull']}

{committee.debate['bear']}

## 5. Research manager investment plan

{committee.investment_plan}

## 6. Trader proposal

{committee.trade_proposal}

## 7. Risk review

{committee.risk_debate['aggressive']}

{committee.risk_debate['neutral']}

{committee.risk_debate['conservative']}

{committee.risk_debate['note']}

**Risk register** (severity as judged from the evidence base):

| Risk | Why it matters | Severity |
|------|----------------|----------|
{risk_rows}

## 8. Portfolio manager decision

{committee.final_decision}

## 9. Scenario book (judgement, to be scored)

| Scenario | Probability | Range | Midpoint | Triggers |
|----------|-------------|-------|----------|----------|
{scenario_rows}

Probability-weighted value: **PKR {weighted:,.2f}** ({weighted / f.spot - 1:+.1%} versus spot).

## 10. What would falsify this call

{chr(10).join(f'- {x}' for x in profile.falsification)}

## 11. Evidence base

| Date | Scope | Fact | Source | Direction |
|------|-------|------|--------|-----------|
{evidence_tbl}

**Scorecard used by the fundamentals analyst (0-10 per dimension):**

| Dimension | Score | Comment |
|-----------|-------|---------|
{scorecard}

## 12. Data and method caveats

{caveats}
- The committee is the deterministic mirror of the TradingAgents pipeline (same roles, same data
  tools, same rating scale); when an LLM key is available the vendored graph can be run instead.
- Probabilities are model output, not promises. The scenario book is analyst judgement and is
  stated so it can be scored later.

## 13. Sources

{sources}

---

*Research output produced by the Stock Insight / TradingAgents PSX pipeline - not investment
advice. Numbers are traceable to the sources above; the raw price snapshots and the forecast JSON
accompany this report in `reports/`.*
"""
    return md


def write_outputs(profile: Profile, series, ohlcv, f: fc.ForecastResult, committee, analytics: dict,
                  scenarios: list[dict], robustness: dict | None = None,
                  framework_dir: str | None = None, outdir: str = REPORTS_DIR) -> dict:
    os.makedirs(outdir, exist_ok=True)
    ticker = profile.ticker
    as_of = profile.as_of
    floor = profile.anchor("book", profile.anchor("support", f.spot * 0.9))
    floor_label = (f"Book value {floor:,.2f}" if profile.levels.get("book") else "reference level")
    md = render_markdown(profile, series, ohlcv, f, committee, analytics, scenarios, robustness,
                         framework_dir)
    svg_price = rp.svg_price_fan(
        series, f, sessions=min(len(series.closes), 250),
        floor=floor, floor_label=floor_label,
        book=profile.anchor("support", floor), book_label="support "
        f"{profile.anchor('support', floor):,.2f}",
        title=f"{profile.symbol} daily closes (PKR) - last {min(len(series.closes), 250)} sessions "
              f"and the {f.horizon_sessions}-session Monte-Carlo fan (p10 / p50 / p90)",
    )
    svg_dist = rp.svg_distribution(
        f, anchor=floor, anchor_label=floor_label)
    paths = {
        "markdown": os.path.join(outdir, f"{ticker}_research_{as_of}.md"),
        "html": os.path.join(outdir, f"{ticker}_research_{as_of}.html"),
        "forecast_json": os.path.join(outdir, f"{ticker}_forecast_{as_of}.json"),
        "chart_svg": os.path.join(outdir, f"{ticker}_chart_price.svg"),
        "dist_svg": os.path.join(outdir, f"{ticker}_chart_dist.svg"),
    }
    with open(paths["markdown"], "w", encoding="utf-8") as fh:
        fh.write(md)
    with open(paths["html"], "w", encoding="utf-8") as fh:
        fh.write(rp.render_html(md, svg_price, svg_dist, f,
                                title=f"{ticker} (PSX) - deep research &amp; 30-day forecast - {as_of}"))
    with open(paths["chart_svg"], "w", encoding="utf-8") as fh:
        fh.write(svg_price)
    with open(paths["dist_svg"], "w", encoding="utf-8") as fh:
        fh.write(svg_dist)
    payload = {
        "symbol": ticker,
        "yahoo_symbol": profile.symbol,
        "name": profile.name,
        "as_of": f.as_of,
        "forecast_for": f.horizon_end,
        "horizon_sessions": f.horizon_sessions,
        "spot": f.spot,
        "daily_vol": f.daily_vol,
        "annual_vol": f.annual_vol,
        "prob_up": f.prob_up,
        "prob_up_total_return": f.prob_up_total_return,
        "dividend_in_window": f.dividend_total,
        "prob_down": f.prob_down,
        "expected_price": f.expected_price,
        "expected_return": f.expected_return,
        "quantiles": f.quantiles,
        "var_5": f.var_5,
        "cvar_5": f.cvar_5,
        "prob_above": f.prob_above,
        "prob_below": f.prob_below,
        "regimes": f.regimes,
        "path_extremes": _path_extremes(f),
        "robustness": robustness,
        "scenarios": scenarios,
        "committee": {
            "scores": committee.scores,
            "rating": committee.final_rating,
            "action": committee.action,
            "trade_params": committee.trade_params,
        },
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(paths["forecast_json"], "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return paths
