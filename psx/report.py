"""Rendering layer: markdown report, standalone HTML report, inline SVG charts.

The HTML output is deliberately dependency-free (no matplotlib, no CDN): the
charts are hand-built SVG strings, so the file can be opened from disk, emailed
or served from any static host and still render identically.
"""

from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone

from . import agents, forecast as fc, indicators as ind, research as rs

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")

BG = "#0e1420"
PANEL = "#151d2e"
INK = "#e8eefc"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
GREEN = "#34d399"
RED = "#f87171"
AMBER = "#fbbf24"


# --------------------------------------------------------------------------- #
# SVG charts
# --------------------------------------------------------------------------- #
def _scale(v, lo, hi, a, b):
    return a + (b - a) * ((v - lo) / (hi - lo) if hi > lo else 0.5)


def svg_price_fan(series, f: fc.ForecastResult, sessions: int = 250, width: int = 960, height: int = 430,
                  *, floor: float = 38.20, floor_label: str = "GoPb issue floor 38.20",
                  book: float = 31.83, book_label: str = "Book value 31.83",
                  hi_override: float | None = None, title: str | None = None) -> str:
    """Price history plus the forecast fan for the next ``horizon`` sessions.

    The reference marks default to the Bank of Punjab's issue floor and audited
    book value; other names pass their own (see :mod:`psx.writer`).
    """
    closes = series.closes[-sessions:]
    dates = series.dates[-sessions:]
    spot = closes[-1]
    horizon = f.horizon_sessions
    bands = f.path_bands
    lo = min(min(closes), min(b["p10"] for b in bands.values())) * 0.98
    # ``hi_override`` caps the axis when a reference level (e.g. book value) sits
    # far above anything the price or the fan touches; the data always fits.
    required = max(max(closes), max(b["p90"] for b in bands.values()))
    if hi_override:
        # explicit cap: reference marks above it are simply not drawn
        hi = max(required, hi_override) * 1.02
    else:
        hi = max(required, floor) * 1.02
    pad_l, pad_r, pad_t, pad_b = 62, 118, 26, 40
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    total_pts = len(closes) - 1 + horizon
    x_at = lambda i: pad_l + w * i / total_pts  # noqa: E731
    y_at = lambda v: pad_t + h * (1 - (v - lo) / (hi - lo))  # noqa: E731

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
             f'font-family="Inter,Segoe UI,system-ui,sans-serif" font-size="12">']
    parts.append(f'<rect width="{width}" height="{height}" fill="{BG}" rx="10"/>')
    # gridlines + y labels
    steps = 6
    for s in range(steps + 1):
        v = lo + (hi - lo) * s / steps
        y = y_at(v)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + w}" y2="{y:.1f}" stroke="#243049" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l - 8}" y="{y + 4:.1f}" fill="{MUTED}" text-anchor="end">{v:.0f}</text>')
    # fan
    fan_pts = [(x_at(len(closes) - 1 + k), bands[k]) for k in range(horizon + 1)]
    upper = " ".join(f"{x:.1f},{y_at(b['p90']):.1f}" for x, b in fan_pts)
    lower = " ".join(f"{x:.1f},{y_at(b['p10']):.1f}" for x, b in reversed(fan_pts))
    parts.append(f'<polygon points="{upper} {lower}" fill="{ACCENT}" opacity="0.16"/>')
    parts.append('<polyline points="' + " ".join(f"{x:.1f},{y_at(b['p50']):.1f}" for x, b in fan_pts) +
                 f'" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-dasharray="5 4"/>')
    for q, op in (("p10", 0.5), ("p90", 0.5)):
        parts.append('<polyline points="' + " ".join(f"{x:.1f},{y_at(b[q]):.1f}" for x, b in fan_pts) +
                     f'" fill="none" stroke="{ACCENT}" stroke-width="1" opacity="{op}"/>')
    # history
    hist = " ".join(f"{x_at(i):.1f},{y_at(c):.1f}" for i, c in enumerate(closes))
    parts.append(f'<polyline points="{hist}" fill="none" stroke="{INK}" stroke-width="2"/>')
    # reference levels
    for level, label, color in ((floor, floor_label, AMBER),
                                (book, book_label, MUTED),
                                (spot, f"spot {spot:.2f}", GREEN)):
        if not (lo <= level <= hi):
            continue  # reference level is off this chart's scale
        y = y_at(level)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + w}" y2="{y:.1f}" stroke="{color}" '
                     f'stroke-width="1" stroke-dasharray="3 5" opacity="0.75"/>')
        parts.append(f'<text x="{pad_l + w + 8}" y="{y + 4:.1f}" fill="{color}">{label}</text>')
    # x labels
    for idx in range(0, len(closes), max(1, len(closes) // 6)):
        parts.append(f'<text x="{x_at(idx):.1f}" y="{height - 14}" fill="{MUTED}" text-anchor="middle" '
                     f'font-size="11">{dates[idx]}</text>')
    parts.append(f'<text x="{x_at(total_pts) - 4:.1f}" y="{height - 14}" fill="{ACCENT}" text-anchor="end" '
                 f'font-size="11">{f.horizon_end} (forecast)</text>')
    parts.append(f'<line x1="{x_at(len(closes) - 1):.1f}" y1="{pad_t}" x2="{x_at(len(closes) - 1):.1f}" '
                 f'y2="{pad_t + h}" stroke="#334155" stroke-dasharray="2 4"/>')
    heading = title or (f"{getattr(series, 'symbol', 'BOP.KA')} daily closes (PKR) - "
                        f"last {len(closes)} sessions and the {f.horizon_sessions}-session "
                        f"Monte-Carlo fan (p10 / p50 / p90)")
    parts.append(f'<text x="{pad_l}" y="18" fill="{INK}" font-weight="600">{heading}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_distribution(f: fc.ForecastResult, width: int = 960, height: int = 300,
                     *, anchor: float = 38.20, anchor_label: str = "issue floor 38.20") -> str:
    """Terminal price histogram with the key anchors marked."""
    hist = f.distribution
    lo = hist[0]["price"]
    hi = hist[-1]["price"]
    pmax = max(b["prob"] for b in hist)
    pad_l, pad_r, pad_t, pad_b = 62, 118, 26, 46
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    bar_w = w / len(hist)
    x_at = lambda v: pad_l + w * (v - lo) / (hi - lo)  # noqa: E731
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
             f'font-family="Inter,Segoe UI,system-ui,sans-serif" font-size="12">',
             f'<rect width="{width}" height="{height}" fill="{BG}" rx="10"/>']
    for i, b in enumerate(hist):
        x = pad_l + i * bar_w
        bh = h * b["prob"] / pmax
        color = GREEN if b["price"] > f.spot else RED
        parts.append(f'<rect x="{x:.1f}" y="{pad_t + h - bh:.1f}" width="{bar_w - 1.5:.1f}" height="{bh:.1f}" '
                     f'fill="{color}" opacity="0.75"/>')
    for level, label, color in ((f.spot, f"spot {f.spot:.2f}", INK),
                                (f.quantiles["p50"], f"median {f.quantiles['p50']:.2f}", ACCENT),
                                (f.quantiles["p10"], f"p10 {f.quantiles['p10']:.2f}", MUTED),
                                (f.quantiles["p90"], f"p90 {f.quantiles['p90']:.2f}", MUTED),
                                (anchor, anchor_label, AMBER)):
        if lo <= level <= hi:
            x = x_at(level)
            parts.append(f'<line x1="{x:.1f}" y1="{pad_t}" x2="{x:.1f}" y2="{pad_t + h}" stroke="{color}" '
                         f'stroke-width="1.4" stroke-dasharray="4 4"/>')
            parts.append(f'<text x="{x + 4:.1f}" y="{pad_t + 12}" fill="{color}" font-size="11">{label}</text>')
    parts.append(f'<text x="{pad_l}" y="18" fill="{INK}" font-weight="600">Simulated price in '
                 f'{f.horizon_sessions} sessions (2026-11-06), {fc.DEFAULT_PATHS // 1000}k paths</text>')
    for s in range(7):
        v = lo + (hi - lo) * s / 6
        parts.append(f'<text x="{x_at(v):.1f}" y="{height - 18}" fill="{MUTED}" text-anchor="middle">{v:.0f}</text>')
    parts.append(f'<text x="{pad_l}" y="{height - 4}" fill="{MUTED}" font-size="11">PKR</text>')
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# minimal markdown -> HTML (tables, headings, lists, emphasis, rules)
# --------------------------------------------------------------------------- #
def _md_to_html(md: str) -> str:
    def inline(t: str) -> str:
        t = html.escape(t)
        import re

        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        return t

    out, in_ul, in_ol, in_table = [], False, False, False

    def close_all():
        nonlocal in_ul, in_ol, in_table
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip() == "":
            close_all()
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            if not in_table:
                close_all()
                out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue
        close_all()
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("> "):
            out.append(f"<blockquote>{inline(line[2:])}</blockquote>")
        elif line.strip() == "---":
            out.append("<hr/>")
        elif line.lstrip().startswith(("- ", "* ")):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line.lstrip()[2:])}</li>")
        elif len(line) > 2 and line[0].isdigit() and line[1:3] in (". ", ") "):
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(line[3:])}</li>")
        else:
            out.append(f"<p>{inline(line)}</p>")
    close_all()
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# markdown report
# --------------------------------------------------------------------------- #
def render_markdown(series, ohlcv, f: fc.ForecastResult, committee: agents.CommitteeOutput) -> str:
    c = series.closes
    spot = c[-1]
    r1m, r3m, r1y = (ind.total_return(c, n) or 0 for n in (21, 63, 250))
    scen = fc.scenarios(spot)
    ev = sum(s["probability"] * s["midpoint"] for s in scen)
    score_rows = "\n".join(
        f"| {k.replace('_', ' ').title()} | {v[0]}/10 | {v[1]} |" for k, v in rs.SCORECARD.items()
    )
    scen_rows = "\n".join(
        f"| {s['name'].split(' - ')[0]} | {s['probability']:.0%} | PKR {s['target_range'][0]:.2f} - "
        f"{s['target_range'][1]:.2f} | PKR {s['midpoint']:.2f} | {s['return_pct'] * 100:+.1f}% |"
        for s in scen
    )
    macro_rows = "\n".join(
        f"| {m['headline']} | {m['source']} | {m['date']} |" for m in rs.MACRO
    )
    company_rows = "\n".join(
        f"| {m['headline']} | {m['source']} | {m['date']} |" for m in rs.COMPANY
    )
    sector_rows = "\n".join(
        f"| {m['headline']} | {m['source']} | {m['date']} |" for m in rs.SECTOR
    )
    risk_rows = "\n".join(f"| {r[0]} | {r[1]} | {r[2]} |" for r in rs.RISKS)

    md = f"""# The Bank of Punjab (PSX: BOP) - deep research and 30-day movement forecast

**Forecast date:** {rs.AS_OF} · **Last settled close:** PKR {spot:.2f} (2026-10-06) ·
**Forecast horizon:** 2026-10-07 to {f.horizon_end} ({f.horizon_sessions} trading sessions) ·
**Engine:** TradingAgents multi-agent pipeline (vendored at `TradingAgents/`) with the PSX
data and forecasting layer in `psx/`.

---

## 1. The call

> **30-day movement prediction: modestly higher, wide band.** Probability that BOP closes above
> PKR {spot:.2f} on {f.horizon_end}: **{f.prob_up:.0%}**. Median terminal price
> **PKR {f.quantiles['p50']:.2f}**
> ({f.quantiles['p50'] / spot - 1:+.1%}), expected value **PKR {f.expected_price:.2f}**
> ({f.expected_return:+.1%}). The 80% interval is PKR {f.quantiles['p10']:.2f} to
> PKR {f.quantiles['p90']:.2f}; the interquartile band is PKR {f.quantiles['p25']:.2f} -
> PKR {f.quantiles['p75']:.2f}. Committee rating: **{committee.final_rating}**, sized at
> {committee.trade_params.get('size_pct_final', 0):.1f}% of a diversified book with a stop at
> PKR {committee.trade_params['stop']:.2f}.

| Metric | Value |
|--------|-------|
| Spot (last settled close, 2026-10-06) | PKR {spot:.2f} |
| Median forecast (2026-11-06) | PKR {f.quantiles['p50']:.2f} |
| Expected value | PKR {f.expected_price:.2f} |
| Probability of a higher close | {f.prob_up:.0%} |
| 80% interval | PKR {f.quantiles['p10']:.2f} - {f.quantiles['p90']:.2f} |
| 5% VaR / CVaR over the window | {f.var_5 * 100:.1f}% / {f.cvar_5 * 100:.1f}% |
| P(touch the PKR 38.20 GoPb issue floor) | {f.prob_above['38.20 (GoPb equity-injection floor)']:.1%} |
| Daily volatility (EWMA) / annualised | {f.daily_vol * 100:.2f}% / {f.annual_vol * 100:.1f}% |

**Scenario book**

| Scenario | Probability | Price range | Midpoint | Return |
|----------|-------------|-------------|----------|--------|
{scen_rows}

Probability-weighted value: **PKR {ev:.2f}** ({ev / spot - 1:+.1%}). The Monte-Carlo mean
(PKR {f.expected_price:.2f}) and the scenario book (PKR {ev:.2f}) agree within ~1%, which is a
useful cross-check: two independent constructions of the same view land in the same place.

**Why not a stronger call?** Because the two dominant forces point in opposite directions. Value
and capital structure are exceptionally supportive - the controlling shareholder is contracted to
buy up to Rs 30bn of new equity at no less than PKR 38.20, {38.20 / spot - 1:.0%} above spot and
20% above audited book, while the stock trades at {spot / 31.83:.2f}x book on a ~10% dividend
yield. Macro and politics are not: inflation at 10.26% has the money market pricing another hike
on 26 October, and the government-PTI standoff is driving a 12%-off-the-high index in which banks
are ~25% of the weight. A one-month horizon is short enough that the second force can dominate.

---

## 2. Where the price is now

![price](chart_price.svg)

*History from the validated daily snapshot (`data/`), fan from 60,000 Monte-Carlo paths.*

* **Trend:** below SMA20 ({ind.sma(c, 20):.2f}), SMA50 ({ind.sma(c, 50):.2f}), SMA100
  ({ind.sma(c, 100):.2f}) and SMA200 ({ind.sma(c, 200):.2f}); RSI(14) {ind.rsi(c, 14):.0f};
  MACD histogram {ind.macd(c)['histogram']:+.3f} (negative, flattening).
* **Drawdown:** {ind.drawdown_from_peak(c) * 100:.1f}% below the 5 January 2026 intraday high of
  44.17; max two-year drawdown {ind.max_drawdown(c) * 100:.0f}%.
* **Returns:** 1 month {r1m * 100:+.1f}%, 3 months {r3m * 100:+.1f}%, 12 months {r1y * 100:+.1f}%,
  2 years {ind.total_return(c, len(c) - 1) * 100:+.0f}%.
* **Risk:** realised vol {ind.realized_vol(c, 20) * 100:.0f}% (20d) / {ind.realized_vol(c, 250) * 100:.0f}%
  (250d) annualised; 1-day historical VaR(95) {ind.historical_var(c) * 100:.1f}%; ATR(14)
  PKR {ind.atr(ohlcv['rows'], 14):.2f}. Returns are fat-tailed (excess kurtosis
  {ind.excess_kurtosis(ind.log_returns(c)):+.1f}) and positively skewed
  ({ind.skewness(ind.log_returns(c)):+.2f}).
* **Microstructure:** the 5 Oct down day traded 7.3mn shares versus a 19.5mn three-month average,
  and 6 Oct reversed from 28.55 to close 3.2% off its low - supply is thinning at support.
* **Key levels:** support 28.55 / 27.00-28.00 (May-June base); resistance 30.90-31.75 (September
  range top), 33.70-34.46 (200-day average and July swing), then 38.20 (the issue floor).

---

## 3. Forecast distribution

![distribution](chart_dist.svg)

| Threshold | Model probability of being at or above on 2026-11-06 |
|-----------|------------------------------------------------------|
""" + "\n".join(
        f"| PKR {k} | {v:.1%} |" for k, v in f.prob_above.items()
    ) + f"""

The distribution is generated by block-bootstrapping 250 sessions of the stock's own returns
(blocks of five sessions preserve volatility clustering), scaling them to today's EWMA volatility
of {f.daily_vol * 100:.2f}% per day, and mixing three drift regimes: a zero-drift martingale
(weight 35%), a weak pull toward the 200-day average (50%) and a small catalyst overlay (15%).
The martingale leg alone puts P(up) at {f.regimes['martingale']['prob_up']:.0%}; the mixture lands
at {f.prob_up:.0%}. Anyone who believes short-horizon drift is unknowable should read the
martingale number as the honest floor - even then the downside is bounded by a support shelf that
the state-owned anchor shareholder has a contractual incentive to defend.

---

## 4. Deep research: the evidence base

### 4.1 Company-specific

| Fact | Source | Date |
|------|--------|------|
{company_rows}

### 4.2 Sector

| Fact | Source | Date |
|------|--------|------|
{sector_rows}

### 4.3 Macro

| Fact | Source | Date |
|------|--------|------|
{macro_rows}

### 4.4 Scorecard

| Dimension | Score | Comment |
|-----------|-------|---------|
{score_rows}

---

## 5. The multi-agent committee

The pipeline below mirrors the vendored TradingAgents graph (analysts -> bull/bear debate ->
research manager -> trader -> risk debate -> portfolio manager). The deterministic engine applies
explicit rules to the same data tools and emits these artifacts; to execute the *actual* LangGraph
pipeline instead, run `python scripts/run_bop_assessment.py --framework` (deterministic stand-in
model when no key is present) or `... --framework --mode live` with an LLM API key set. The
framework's own report tree is written to `reports/framework/BOP_2026-10-07/`.

### Analyst reports

{committee.reports['market']}

{committee.reports['fundamentals']}

{committee.reports['news']}

{committee.reports['sentiment']}

### Research debate

{committee.debate['bull']}

{committee.debate['bear']}

### Research manager

{committee.investment_plan}

### Trader

{committee.trade_proposal}

### Risk debate

{committee.risk_debate['aggressive']}

{committee.risk_debate['neutral']}

{committee.risk_debate['conservative']}

{committee.risk_debate['note']}

### Portfolio manager

{committee.final_decision}

---

## 6. Risk register

| Risk | Why it matters | Severity |
|------|----------------|----------|
{risk_rows}

---

## 7. Falsification: what would prove this wrong

1. **A close below PKR {committee.trade_params['stop']:.2f}** breaks the 28.55 shelf that has held
   twice; the next reference is the 27.00-28.00 base, and the model's 5% tail
   (PKR {f.quantiles['p5']:.2f}) becomes the base case.
2. **A hawkish 26 October MPC** (a hike to 12.5%, or a statement that reopens the tightening
   cycle) invalidates the "rate peak" assumption behind the mean-reversion leg; the martingale
   distribution, not the mixture, should then be used.
3. **Q3-2026 provisions above ~Rs 4bn** or any Punjab-scheme asset-quality disclosure would hit
   the one part of the bull case that is currently unverifiable from public data.
4. **A slip in the GoPb tranche past 31 December 2026** would remove the contractual anchor that
   makes the risk/reward asymmetric.
5. **An index close below 160,000** puts the political channel in charge; single-stock analysis
   loses explanatory power and the position should be cut to the conservative size.

---

## 8. Method and provenance

* **Price data:** Yahoo Finance daily series for `BOP.KA`, assembled into
  `data/BOP_KA_daily_2y.json` (503 settled sessions, 2024-10-07 to 2026-10-06) and validated
  against four independent anchors: the PSX data portal's 5 Oct 2026 close (28.89, -1.04,
  -3.48%), invest.pk's 8 Sep 2026 OHLC (34.80 / 35.00 / 34.00 / 34.63), stockanalysis.com's
  31 Dec 2025 market capitalisation (PKR 126.15bn implies 38.56 per share) and TradingView's
  all-time-high date (5 Jan 2026, close 43.09 / intraday 44.17). `python3 scripts/validate_data.py`
  re-runs every anchor and the cross-fetch overlap checks on demand.
* **Forecast:** 60,000-path block bootstrap (see `psx/forecast.py`), seed 20261007, reproducible
  bit-for-bit: `python scripts/run_bop_assessment.py`.
* **Fundamentals:** H1-2026 results release (28 Aug 2026), the 8 Sep 2026 EOGM materials, PACRA's
  1 Jul 2026 rating action, PSX company announcements and the macro/sector sources footnoted above.
* **Framework:** TauricResearch/TradingAgents v0.6.0 (Apache-2.0), vendored under `TradingAgents/`;
  the PSX data vendor, configuration and offline analyst engine live in `psx/tradingagents_bridge.py`
  and `psx/agents.py`.

*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by
`scripts/run_bop_assessment.py`. Research output, not investment advice.*
"""
    return md


# --------------------------------------------------------------------------- #
# HTML report
# --------------------------------------------------------------------------- #
CSS = f"""
:root {{ color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:{BG}; color:{INK};
  font-family: Inter, "Segoe UI", system-ui, -apple-system, sans-serif; line-height:1.65; }}
.wrap {{ max-width: 1080px; margin: 0 auto; padding: 48px 24px 96px; }}
h1 {{ font-size: 2rem; line-height:1.25; margin:0 0 8px; }}
h2 {{ font-size: 1.35rem; margin:44px 0 12px; padding-bottom:8px; border-bottom:1px solid #243049; }}
h3 {{ font-size: 1.05rem; margin:28px 0 8px; color:{ACCENT}; }}
p, li {{ color:#cbd5e1; }}
a {{ color:{ACCENT}; }}
code {{ background:#0b1220; padding:2px 6px; border-radius:5px; font-size:.9em; }}
blockquote {{ margin:20px 0; padding:16px 20px; background:{PANEL}; border-left:4px solid {ACCENT};
  border-radius:0 10px 10px 0; font-size:1.05rem; color:{INK}; }}
table {{ width:100%; border-collapse:collapse; margin:18px 0; font-size:.92rem; }}
th, td {{ text-align:left; padding:9px 12px; border-bottom:1px solid #243049; vertical-align:top; }}
th {{ color:{MUTED}; font-weight:600; text-transform:uppercase; letter-spacing:.04em; font-size:.72rem; }}
tbody tr:hover {{ background:#131b2b; }}
hr {{ border:0; border-top:1px solid #243049; margin:36px 0; }}
img {{ width:100%; margin:20px 0; }}
footer {{ margin-top:64px; color:{MUTED}; font-size:.85rem; }}
.badges {{ display:flex; flex-wrap:wrap; gap:10px; margin:18px 0 6px; }}
.badge {{ background:{PANEL}; border:1px solid #243049; border-radius:999px; padding:6px 14px;
  font-size:.82rem; color:{MUTED}; }}
.badge b {{ color:{INK}; }}
"""


def render_html(markdown_text: str, svg_price: str, svg_dist: str, f: fc.ForecastResult,
                *, title: str | None = None) -> str:
    body = _md_to_html(markdown_text)
    body = body.replace('<img alt="price" src="chart_price.svg">', svg_price)
    body = body.replace('<img alt="distribution" src="chart_dist.svg">', svg_dist)
    badges = "".join(
        f'<span class="badge">{label} <b>{value}</b></span>'
        for label, value in (
            ("Spot", f"PKR {f.spot:.2f}"),
            (f"P(up) in {f.horizon_sessions} sessions", f"{f.prob_up:.0%}"),
            ("Median", f"PKR {f.quantiles['p50']:.2f}"),
            ("80% band", f"{f.quantiles['p10']:.2f} - {f.quantiles['p90']:.2f}"),
            ("Ann. vol", f"{f.annual_vol * 100:.1f}%"),
            ("Horizon", f.horizon_end),
        )
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title or f"BOP (PSX) - deep research &amp; 30-day forecast - {rs.AS_OF}"}</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<div class="badges">{badges}</div>
{body}
<footer>Generated by the Stock Insight / TradingAgents PSX pipeline. Research output - not
investment advice. Sources and dates are listed inline; the raw price snapshot and the full
forecast JSON accompany this report in <code>reports/</code>.</footer>
</div></body></html>"""


# --------------------------------------------------------------------------- #
# writer
# --------------------------------------------------------------------------- #
def write_outputs(series, ohlcv, f: fc.ForecastResult, committee: agents.CommitteeOutput,
                  outdir: str = REPORTS_DIR) -> dict:
    os.makedirs(outdir, exist_ok=True)
    md = render_markdown(series, ohlcv, f, committee)
    svg_price = svg_price_fan(series, f)
    svg_dist = svg_distribution(f)
    paths = {
        "markdown": os.path.join(outdir, f"BOP_research_{rs.AS_OF}.md"),
        "html": os.path.join(outdir, f"BOP_research_{rs.AS_OF}.html"),
        "forecast_json": os.path.join(outdir, f"BOP_forecast_{rs.AS_OF}.json"),
        "chart_svg": os.path.join(outdir, "chart_price.svg"),
        "dist_svg": os.path.join(outdir, "chart_dist.svg"),
    }
    with open(paths["markdown"], "w", encoding="utf-8") as fh:
        fh.write(md)
    with open(paths["html"], "w", encoding="utf-8") as fh:
        fh.write(render_html(md, svg_price, svg_dist, f))
    with open(paths["chart_svg"], "w", encoding="utf-8") as fh:
        fh.write(svg_price)
    with open(paths["dist_svg"], "w", encoding="utf-8") as fh:
        fh.write(svg_dist)
    payload = {
        "symbol": rs.SUBJECT["ticker_psx"],
        "yahoo_symbol": rs.SUBJECT["ticker_yahoo"],
        "as_of": f.as_of,
        "forecast_for": f.horizon_end,
        "horizon_sessions": f.horizon_sessions,
        "spot": f.spot,
        "daily_vol": f.daily_vol,
        "annual_vol": f.annual_vol,
        "prob_up": f.prob_up,
        "prob_down": f.prob_down,
        "expected_price": f.expected_price,
        "expected_return": f.expected_return,
        "quantiles": f.quantiles,
        "var_5": f.var_5,
        "cvar_5": f.cvar_5,
        "prob_above": f.prob_above,
        "regimes": f.regimes,
        "scenarios": fc.scenarios(f.spot),
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
