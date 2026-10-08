# Arif Habib Corporation Limited (PSX: AHCL) - deep research and 30-day movement forecast

*Investment companies / conglomerate holding | prices in PKR | report 2026-10-07 | market data through 2026-10-07*

> **30-day movement prediction: close to a coin flip.** PKR 1.25 a share goes ex inside the window, so the printed price carries a known step down; the probability of a **positive total return** (price change plus cash) is **51.2%**, while the probability that the *price* closes above PKR 15.48 on 2026-11-06 is 10.4%. The price median is PKR 14.26 with an 80% band of **PKR 13.15 to PKR 15.50**. Committee verdict:
> **HOLD**, hold proposal, position size
> 5.6% of a
> diversified book, stop PKR 13.57.

> The vendored **TradingAgents** graph was also run end-to-end on this name; its own report tree is written to `reports/framework/AHCL_2026-10-07`.

## 1. Where the stock stands

| Measure | Value |
|---------|-------|
| Last settled close | PKR 15.48 (2026-10-07) |
| 52-week range | PKR 12.16 - PKR 19.33 |
| Market capitalisation | PKR 65.28bn |
| Shares outstanding | 4,217.0mn |
| Price / earnings | 4.21x trailing |
| Price / book | 1.18x (BVPS PKR 13.15) |
| Dividend | PKR 1.25 (8.07% yield, 27% payout) |
| Consensus | no published coverage |
| Beta | 0.41 |
| Free float | 15.0% |

**Recent sessions:** 2026-09-28: 15.84, 2026-09-29: 16.07, 2026-09-30: 16.17, 2026-10-01: 15.79, 2026-10-02: 15.85, 2026-10-05: 15.74, 2026-10-06: 15.69, 2026-10-07: 15.48

**The one-line story.** Arif Habib Group's holding company: a ~34% interest (held with Fatima Fertilizer) in PIA Equity Ltd, the consortium that now owns 100% of Pakistan International Airlines, ~73% of Arif Habib Limited, 86% of Sachal Energy, plus strategic stakes in Fatima Fertilizer, Power Cement, Aisha Steel, Javedan and Pakarab Fertilizers. Fifty sessions of range-trading between 14.90 and 16.60 on thin volume, with the 8.1% dividend date on 20 October the only scheduled event that reliably draws buyers. The 52-week range (12.16-19.33) brackets a stock that spends most of its time in the middle of its own range.

## 2. The 30-day distribution (Monte-Carlo, 22 sessions)

| Statistic | Value |
|-----------|-------|
| Spot (forecast base) | PKR 15.48 |
| P(price higher) | 10.4% |
| P(price lower) | 89.6% |
| Expected price | PKR 14.30 (-7.64%) |
| Median (p50) | PKR 14.26 |
| Interquartile band (p25-p75) | PKR 13.65 - 14.89 |
| 80% interval (p10-p90) | PKR 13.15 - 15.50 |
| 5% VaR / CVaR at the horizon | -16.9% / -19.0% |
| Annualised volatility (EWMA) | 23.8% |
| Horizon | 22 sessions to 2026-11-06 |
| Cash distribution inside the window | PKR 1.25 per share (8.07%) - FY26 dividend, ex-date 2026-10-20 |

![price](chart_price.svg)

**The levels that matter.** The first two columns describe where the price *finishes* on the
horizon date; the last describes the odds it *gets there at any point* on the way:

| Level | P(close at or above on the horizon date) | P(close at or below) | P(the price trades through it at any point) |
|-------|------------------------------------------|----------------------|--------------------------|
| PKR 15.75 (mid-point of the 52-week range) | 6.5% | 93.5% | 50.2% |
| PKR 16.55 (September high) | 1.2% | 98.8% | 8.2% |
| PKR 17.00 (price a year ago) | 0.4% | 99.6% | 2.2% |
| PKR 19.33 (52-week high) | 0.0% | 100.0% | 0.0% |
| PKR 15.00 (round-number support) | 21.7% | 78.3% | 95.8% |
| PKR 14.90 (September base) | 24.8% | 75.2% | 94.3% |
| PKR 13.15 (book value per share) | 90.0% | 10.0% | 15.8% |
| PKR 12.16 (52-week low) | 99.5% | 0.5% | 0.7% |

![distribution](chart_dist.svg)

**Two probabilities, one window.** PKR 1.25 a share goes ex inside this window (FY26 dividend, ex-date 2026-10-20), so the printed price falls by about 8.1% on that day with no change in value received. The distribution above is a *price* distribution, which is what stops, targets and level probabilities refer to: P(price higher on 2026-11-06) is **10.4%** and the median is PKR 14.26. Once the cash is counted, the probability of a positive *total return* is **51.2%** - that is the number to compare against a deposit or a T-bill.

**Method.** 60,000 simulated paths over a trailing empirical return pool (block
bootstrap, blocks of five sessions, so volatility clustering survives) rescaled to today's EWMA
volatility of 1.50% a day, mixed across three documented drift regimes:
a zero-drift martingale leg for the bulk of the variance (40%), a pull toward PKR 15.75 that fades as the horizon stretches (40%), and a small catalyst overlay for the event calendar inside the window (20%).
The output is a *distribution*, not a point forecast - the median, the 80% interval and the stated
triggers are the deliverable. Regime weights
martingale 0.40, mean_reversion 0.40, catalyst 0.20.

**Model robustness (short-history cross-check).** With 50 settled sessions the
empirical pool is thin, so the same EWMA volatility is also run through a
**student-t(4) scaled to the same EWMA volatility** with 20,000 paths (the same cash step applied):
median PKR 14.24, 80% interval
PKR 12.22-PKR 16.55, P(price higher)
22.2%, P(positive total return) 50.4%. That is
consistent with
the headline bootstrap band; where they disagree, the student-t band is the honest one for the
tails because 50 observations cannot describe a fat tail.

## 3. Analyst reports

### Market Analyst - trend, momentum and levels

**Where the tape is.** Fifty sessions of range-trading between 14.90 and 16.60 on thin volume, with the 8.1% dividend date on 20 October the only scheduled event that reliably draws buyers. The 52-week range (12.16-19.33) brackets a stock that spends most of its time in the middle of its own range.

| Measure | Value | Reading |
|---------|-------|---------|
| Spot (last settled session) | PKR 15.48 | 2026-10-07 |
| Trend vs moving averages | **20-day** PKR 15.47 (above) / **50-day** PKR 15.78 (below) / **100-day n/a** (not enough history) / **mid-point of the 52-week range (long-run proxy)** PKR 15.75 (below) | down |
| RSI(14) | 46.9 | neutral |
| MACD / signal / histogram | 0.015 / -0.008 / 0.023 | positive momentum |
| ATR(14) | PKR 0.43 (2.8% of price) | daily swing budget |
| Annualised vol 20d / 250d | 25.5% / 24.7% | elevated |
| Drawdown from peak | -6.1% (max -9.5%) | moderate |
| Support / resistance (20d + anchors) | PKR 14.22 / PKR 16.55 | September 2026 base (14.90-15.10) / September 2026 high |
| Last five sessions | 2026-10-01: 15.79, 2026-10-02: 15.85, 2026-10-05: 15.74, 2026-10-06: 15.69, 2026-10-07: 15.48 | |

**Score: 4.0/10** - price below the key averages, trend still down with
momentum turning up and volatility
above its one-year average.


### Fundamentals Analyst - valuation and earnings

**Where it stands.** Arif Habib Group's holding company: a ~34% interest (held with Fatima Fertilizer) in PIA Equity Ltd, the consortium that now owns 100% of Pakistan International Airlines, ~73% of Arif Habib Limited, 86% of Sachal Energy, plus strategic stakes in Fatima Fertilizer, Power Cement, Aisha Steel, Javedan and Pakarab Fertilizers.

**Valuation.** At PKR 15.48 the market capitalisation is ~PKR 65.3bn
(4,217.0mn shares outstanding).
**4.21x** trailing earnings - **1.18x** book value per share of PKR 13.15 - a PKR 1.25 dividend is a **8.07%** yield - no analyst coverage or published target to anchor the price - beta 0.41.

**Scorecard (0-10 per dimension, weighted 25%, 20%, 25%, 15%, 15%):**

| Dimension | Input | Score |
|-----------|-------|-------|
| Price / earnings (4.2x FY26 consolidated) | 4.21 | 8.0/10 |
| Price / book (1.18x) | 1.18 | 4.2/10 |
| Earnings momentum (FY26 +49.5% but a Q3 loss) | 0.49 | 10.0/10 |
| Dividend yield (8.1%, raised 25% this year) | 0.08 | 8.7/10 |
| Earnings volatility (Q3 mark-to-market loss of Rs 8.4bn) | 0.54 | 1.1/10 |

**Composite fundamentals score: 6.81/10.** The valuation looks absurdly cheap (4.2x earnings, 1.18x book, 8.1% yield) only if you accept the FY26 consolidated earnings base; the honest way to look at AHCL is as a levered, illiquid sum-of-parts bet on PIA's turnaround and the Pakistani index.

**What the latest filings say.**
- FY26 (year to 30 Jun 2026) consolidated profit attributable to shareholders rose 49.5% to Rs 15.53bn (EPS 3.68 on 4.22bn shares); revenue rose 19.4% to Rs 13.83bn. *(AHCL annual results (PSX) / stockanalysis.com, 2026-09-30)*
- The Arif Habib-led consortium bought 75% of Pakistan International Airlines for Rs 135bn in December 2025 and then the remaining 25%, so PIA Equity Limited - in which AHCL plus Fatima Fertilizer hold 34.1% - owns 100% of the airline. *(Business Recorder / Bloomberg / Dawn, 2026-04-28)*
- Q3 FY26 (Jan-Mar 2026) produced an unconsolidated loss of Rs 8.37bn (EPS -1.99) because of mark-to-market losses on the securities portfolio as the KSE-100 fell. *(AHCL directors' report (PSX document 276323), 2026-04-28)*
- Annual dividend raised 25% to Rs 1.25/share (8.1% yield); ex-date 20 Oct 2026, paid 19 Nov 2026; payout ratio ~27%. *(AHCL board decision / stockanalysis.com, 2026-09-30)*


### News Analyst - macro and event tape

The FY26 results (30 Sep) and the PIA ownership completion dominate the news flow; the operational news that matters - fleet serviceability, route restoration, possible re-listing - arrives in unpredictable bursts.

**The macro tape.**

- **KSE-100 at 169,264.87 (7 Oct)** - 1.4% higher over twelve months but 11.4% below the all-time high of 191,033; the index is the single largest driver of AHCL's mark-to-market earnings.
- **SBP on hold at 11.5%, decision on 26 October** - Rate relief supports the brokerage and real-estate arms; a hawkish surprise would hit both the index and the portfolio.
- **Inflation 10.26% with the PTI standoff live** - Political escalation is the fastest way to a lower index and another mark-to-market quarter.
- **Aviation and fuel economics** - Fuel is an airline's largest cost line and crude was quoted near $101-103/bbl in early October - PIA's turnaround would be easier with softer oil.
- **Fertilizer and cement demand** - AHCL's associate earnings lean on Fatima Fertilizer, Power Cement and Aisha Steel - agriculture and construction activity, both of which track the rate cycle.

**The event calendar inside the forecast window (to 2026-11-06).**

| Date | Event | Why it matters |
|------|-------|----------------|
| 2026-10-20 | Ex-dividend: Rs 1.25/share (8.1% of the price) | The single largest scheduled cash event of the year for AHCL holders; payment 19 Nov. |
| late Oct 2026 | Q1 FY27 results (quarter ended 30 Sep 2026) | The first quarter in which the PIA acquisition is on the books - the market will read it as either turnaround proof or a cash call. |
| 2026-10-26 | SBP monetary policy decision | The KSE-100 - and therefore AHCL's trading book and brokerage volumes - is rate-sensitive. |
| through the window | PIA operational news flow | Fleet serviceability, route restoration and any move toward re-listing are the catalysts that would close the conglomerate discount. |

**Score split.** Macro tape 3.6/10, company and sector newsflow
6.6/10 (equal-weighted). Supportive: none carried.
Hostile: Inflation 10.26% with the PTI standoff live.
The dominant company-flow positive is
"FY26 (year to 30 Jun 2026) consolidated profit attributable to shareholders rose 49.5% to Rs 15.53bn (EPS 3.68 on 4.22bn..."


### Sentiment Analyst - positioning and flows

No broker covers this name in the data set, so there is no consensus estimate or price target to anchor sentiment - flows are set by the shareholder register (15% free float) and by the index.

Market-structure evidence: the stock is -0.3% over one month,
1.9% over three months and -6% below its
high; 20-day average volume (2.58mn shares) is
above the full-window average
(2.51mn). No analyst covers AHCL; the shareholder register (78.8% insider, 15% free float) means there is no consensus anchor and no institutional flow to cushion the price. Treat the 8.1% dividend as the sentiment anchor instead.

**Score: 6.5/10.**


## 4. Bull versus bear debate

**Bull case.**

1. **You are paying 4.2x earnings and 1.18x book for the group that now owns the national airline, the country's leading brokerage and 15% of Fatima Fertilizer** - and it pays an 8.1% dividend, raised 25% this year.
2. **PIA is the largest free option on the Pakistan Stock Exchange.** A 100%-owned national carrier, Rs 125bn of committed capital, a fleet being brought back into service, no layoffs, and management's explicit ambition to re-list the airline once it is profitable.
3. **The operating subsidiaries are compounding:** Arif Habib Limited +20% to Rs 1.18bn with a Rs 12.50 dividend, Sachal Energy paying Rs 1.37bn, Fatima paying Rs 2.29bn - a dividend machine behind an 8% yield.
4. **The Q3 FY26 loss was the index, not the business** (-Rs 8.4bn of mark-to-market on the securities book). The KSE-100 is 11% below its high; a recovery reverses that line item automatically.
5. **The float is tiny (15%) and insiders own ~79%:** there is no forced selling and any incremental institutional interest moves the price sharply.


**Bear case.**

1. **PIA is an unproven, capital-hungry turnaround.** Rs 125bn is the plan, Rs 54bn of liabilities came with the asset, and the first quarter where the airline is consolidated into AHCL's numbers lands inside this forecast window.
2. **The earnings quality is poor:** Q3 FY26 lost Rs 8.4bn on portfolio marks, so the FY26 '+49%' headline is partly a good market quarter rather than operational improvement.
3. **Only 15% free float** means no analyst coverage, no price target, thin liquidity and no index sponsorship - the market can ignore good news for months.
4. **The dividend depends on associates:** if Fatima, AHL or Sachal trim payouts to fund their own plans, the 8.1% yield (the main support under the price) thins out.
5. **Relative performance is poor:** -9.2% over twelve months against an index that is +1.4%, with the 52-week high 20% above the current price.


## 5. Research manager investment plan

### Research Manager - investment plan

**Composite score: 5.74/10** (market 4.0 weighted 20%, fundamentals
6.8 30%, news 5.1 25%, sentiment 6.5 25%).

AHCL is a holding company with one very large, very new, very risky asset and a cash-generative dividend core. The 22-session window contains the dividend and the first PIA-consolidated quarter - two events that can both cut either way.

Over the next 22 sessions the distribution is
close to symmetric:
**P(positive total return) = 51%**
(P(price higher) = 10% after the 8.1% cash step on the ex-date),
median price PKR 14.26, 80% interval
PKR 13.15-PKR 15.50, expected value
PKR 14.30 (-7.6% price, +0.4% total). That distribution is a
"Hold".


## 6. Trader proposal

### Trader - transaction proposal

**Action: Hold (hold / accumulate on weakness).**

| Parameter | Level | Rationale |
|-----------|-------|-----------|
| Entry zone | PKR 14.29 - 15.79 | September 2026 base (14.90-15.10) up to a 2% band above spot |
| Stop | PKR 13.57 | 1.5 x ATR(14) below support; a weekly close below invalidates the thesis |
| Target 1 | PKR 16.55 | September 2026 high |
| Target 2 | PKR 17.00 | strategic anchor |
| Risk/reward | 1.0 : 1 | on a first-target basis |
| Position size | 5.5% of the book | volatility-targeted: a ~24% annualised vol name gets a modest weight |

**Execution notes.** Buy the dividend, keep the position small, and treat the 14.90 base as the line that defines the risk: below it the stock is back to the book value at best. Over the full path to 2026-11-06 the
model puts 35.3% on the price *touching* the PKR 13.57 stop at some point
and 2.2% on it touching PKR 17.00 (target 2); on the horizon date
itself the odds of finishing at or below the stop are
22.1%. The invalidation level for a trend call is a
weekly close through 15.78 (the 50-day), with the 20-day at 15.47.



## 7. Risk review

**Aggressive analyst.** A 24% vol stock with a 51% probability of
being higher in a month is a position to size up, not a watch item. The stop is only
5.0%
below entry, the first target is +7% away and the second is
+10%. Push the position to the top of the size band and use
the scheduled events (2026-10-20, late Oct 2026)
as the trigger for the second tranche.


**Neutral analyst.** The expected return is +0.4% over the
window against a 5% VaR of -16.9% and CVaR of -19.0%: the distribution
rewards patience rather than conviction. That argues for the middle of the size band, staged
entries and no leverage. The biggest avoidable risk is event clustering: the single worst item on
this name's register - "pia becomes a capital sink" - lands inside the window.


**Conservative analyst.** Rs 125bn of committed capital and a Rs 45bn bank guarantee for the government's residual 25%: if the airline's losses outrun the plan, AHCL's balance sheet absorbs it. A
9% peak-to-trough drawdown in the loaded history shows how quickly
the position can move against you. Cap the name at half the vol-targeted size until the first
scheduled event clears, and review immediately if the index loses the level that has defined the
recent range.


The risk team converged on a blended position: aggressive
8.2% / neutral 5.5% /
conservative 2.8%, weighted 30/45/25. Non-negotiables:
no averaging down below PKR 13.57; no more than a third of the position before
the first scheduled event; and a hard review if the broad index breaks its range, because that
would make macro and political risk - not company fundamentals - the binding constraint.


**Risk register** (severity as judged from the evidence base):

| Risk | Why it matters | Severity |
|------|----------------|----------|
| PIA becomes a capital sink | Rs 125bn of committed capital and a Rs 45bn bank guarantee for the government's residual 25%: if the airline's losses outrun the plan, AHCL's balance sheet absorbs it. | high |
| Earnings are mark-to-market | Q3 FY26 lost Rs 8.4bn on index losses; the FY26 'cheap' multiple is flattered by a good market quarter, and the same swing can repeat in reverse. | high |
| 15% free float, 78.8% insider ownership | Thin liquidity means violent moves on small flows, no index-driven sponsorship, and minority investors with little influence over capital allocation. | medium |
| Associate dividend dependence | The 8.1% yield is funded by dividends from Fatima, AHL and Sachal; a cut at any of them breaks the income case. | medium |
| No analyst coverage | There is no consensus estimate or price target to anchor valuation, so the price is set by private-wealth flows and sentiment. | low |
| Political / index risk | AHCL is a high-beta proxy for Pakistani equity sentiment; the political standoff and the 26 Oct MPC both feed directly into its portfolio marks. | high |

## 8. Portfolio manager decision

## Portfolio Manager - final decision

**HOLD** (position size 5.6% of the book, built in thirds, stop
PKR 13.57).

**The one-paragraph version.** Arif Habib Corporation offers a 4.2x multiple, a 1.18x book and an 8.1% dividend on top of a genuine, high-variance option on PIA. For a holder the calculus is simple: you are paid more than 8% cash to own the option. For a 22-session horizon, though, the option's own news flow - and Pakistan's index - dominate, so the position should be sized for a two-sided distribution rather than a trend.

**Explicit 30-day call (forecast made 2026-10-07, horizon 2026-11-06, 22 sessions):**

* Direction: **close to a coin flip** -
  P(total return > 0) 51%; expected price
  PKR 14.30 (-7.6% on the printed price,
  +0.4% once the PKR 1.25 cash is counted).
* Central band: **PKR 13.65 - 14.89** (interquartile), full
  80% interval PKR 13.15 - 15.50.
* Scenario book: Bull 30% (PKR 17.60); Base 45% (PKR 15.70); Bear 25% (PKR 13.40);
  probability-weighted value PKR 15.69.
* Over the full path to 2026-11-06 the model puts
  2.2% on touching PKR 17.00 (target 2)
  and 35.3% on touching the PKR 13.57 stop;
  at the horizon itself the probabilities are
  0.4% and
  0.0%.

**What would change the call.** Re-rate on evidence that the PIA stake is being funded without dilution and that the holding-company discount is closing (a buyback, a special dividend, or a re-rating at Fatima or Power Cement). Cut on a break of the 14.40-14.60 shelf, on any equity issuance that funds PIA at these multiples, or if the FY27 first-quarter earnings show the investment losses are still running.

*This is a research output produced by an automated multi-agent pipeline, not investment advice.
Position sizes assume a diversified book and a 12% volatility budget.*


## 9. Scenario book (judgement, to be scored)

| Scenario | Probability | Range | Midpoint | Triggers |
|----------|-------------|-------|----------|----------|
| Bull - PIA news flow plus a firm index | 30% | PKR 14.89 - PKR 15.89 | PKR 15.50 (+0.1%) | Q1 FY27 without a PIA-related loss surprise and the dividend banked<br>PIA operational milestone (fleet serviceability, route/US clearance)<br>KSE-100 back above 175,000, lifting the securities book<br>SBP hold on 26 Oct with a dovish tilt |
| Base - range-bound around the dividend | 45% | PKR 13.65 - PKR 14.89 | PKR 14.26 (-7.9%) | Q1 FY27 in line, PIA consolidation neutral at the earnings line<br>index range-bound 160,000-172,000<br>the Rs 1.25 dividend captured, no corporate action<br>thin float keeps the tape quiet |
| Bear - PIA losses and a weaker index | 25% | PKR 12.86 - PKR 13.65 | PKR 13.15 (-15.1%) | Q1 FY27 shows PIA losses hitting the group line<br>KSE-100 below 160,000 on political escalation, forcing more mark-to-market losses<br>a capital call or guarantee expansion at PIA Equity<br>an associate dividend cut |

Probability-weighted value: **PKR 14.35** (-7.3% versus spot).

## 10. What would falsify this call

- Q1 FY27 (late October) showing PIA's losses dragging group earnings into a loss would turn the 'optionality' narrative into a funding problem.
- Any equity raise or stake sale at AHCL level to fund the airline would dilute the sum-of-parts case and reset the dividend.
- A cut in the Fatima Fertilizer or AHL dividend would break the 8.1% yield that underpins the current price.
- A KSE-100 close below 160,000 would put the securities book back into mark-to-market losses and remove the earnings base the multiple rests on.
- Conversely, a PIA milestone - the full fleet serviceable, a US/UK route resumption, or a re-listing announcement - would be the event that narrows the conglomerate discount.

## 11. Evidence base

| Date | Scope | Fact | Source | Direction |
|------|-------|------|--------|-----------|
| 2026-09-30 | Company | FY26 (year to 30 Jun 2026) consolidated profit attributable to shareholders rose 49.5% to Rs 15.53bn (EPS 3.68 on 4.22bn shares); revenue rose 19.4% to Rs 13.83bn. | AHCL annual results (PSX) / stockanalysis.com | positive |
| 2026-04-28 | Company | The Arif Habib-led consortium bought 75% of Pakistan International Airlines for Rs 135bn in December 2025 and then the remaining 25%, so PIA Equity Limited - in which AHCL plus Fatima Fertilizer hold 34.1% - owns 100% of the airline. | Business Recorder / Bloomberg / Dawn | positive |
| 2026-04-28 | Company | Q3 FY26 (Jan-Mar 2026) produced an unconsolidated loss of Rs 8.37bn (EPS -1.99) because of mark-to-market losses on the securities portfolio as the KSE-100 fell. | AHCL directors' report (PSX document 276323) | negative |
| 2026-09-30 | Company | Annual dividend raised 25% to Rs 1.25/share (8.1% yield); ex-date 20 Oct 2026, paid 19 Nov 2026; payout ratio ~27%. | AHCL board decision / stockanalysis.com | positive |
| 2026-08-24 | Company | Subsidiary Arif Habib Limited grew profit 20% to Rs 1.177bn (EPS 18.01) in FY26 and paid Rs 12.50/share; dividends received by AHCL include Rs 2.29bn from Fatima Fertilizer and Rs 1.37bn from Sachal Energy in FY25. | AHL FY26 results (PSX); AHCL directors' report | positive |
| 2026-01-12 | Company | The group committed to inject up to Rs 125bn into PIA for fleet restoration and expansion, with 17 of 34 aircraft operational in January and management targeting the full fleet by September 2026; PIA carried ~Rs 54bn of liabilities. | Business Recorder interview with Arif Habib | neutral |
| 2026-10-08 | Sector | Holding-company discount: AHCL's own market capitalisation (Rs 65bn) is below the marked value of its listed holdings and control stakes, a standard feature of Pakistani investment companies. | market data, 2026-10-08 | neutral |
| 2025-12-25 | Sector | PIA's privatisation is the flagship test of Pakistan's IMF-backed reform programme; the airline's turnaround is now a private-sector execution story. | Dawn / Arab News | neutral |
| 2026-04-28 | Sector | AHCL's earnings are levered to the KSE-100 through a marked-to-market securities book: Q3 FY26 showed an Rs 8.4bn swing on an index decline. | AHCL directors' report | negative |
| 2026-10-07 | Macro | KSE-100 at 169,264.87 (7 Oct) - 1.4% higher over twelve months but 11.4% below the all-time high of 191,033; the index is the single largest driver of AHCL's mark-to-market earnings. | -- | neutral |
| 2026-10-07 | Macro | SBP on hold at 11.5%, decision on 26 October - Rate relief supports the brokerage and real-estate arms; a hawkish surprise would hit both the index and the portfolio. | -- | neutral |
| 2026-10-07 | Macro | Inflation 10.26% with the PTI standoff live - Political escalation is the fastest way to a lower index and another mark-to-market quarter. | -- | negative |
| 2026-10-07 | Macro | Aviation and fuel economics - Fuel is an airline's largest cost line and crude was quoted near $101-103/bbl in early October - PIA's turnaround would be easier with softer oil. | -- | negative |
| 2026-10-07 | Macro | Fertilizer and cement demand - AHCL's associate earnings lean on Fatima Fertilizer, Power Cement and Aisha Steel - agriculture and construction activity, both of which track the rate cycle. | -- | neutral |

**Scorecard used by the fundamentals analyst (0-10 per dimension):**

| Dimension | Score | Comment |
|-----------|-------|---------|
| Valuation | 8 | 4.2x FY26 consolidated earnings, 1.18x book and an 8.1% dividend yield - cheap in absolute terms, though the earnings base is unusual. |
| Earnings momentum | 6 | FY26 consolidated profit +49.5%, but the pattern is volatile: a Rs 8.4bn unconsolidated loss in Q3 and a strong Q1. |
| Balance sheet | 5 | A holding company whose main asset (PIA) comes with Rs 54bn of liabilities and a Rs 125bn capital plan; the Rs 45bn guarantee for the government's residual stake is a claim on group liquidity. |
| Franchise | 7 | The Arif Habib brand, the country's flagship brokerage, a 50MW wind asset, a fertilizer stake and now the national airline - one of Pakistan's few true conglomerates. |
| Macro tailwind | 5 | Rate relief and a stable rupee help; 10.3% inflation, high oil and a political standoff do not. |
| Technical | 4 | 8% below the 52-week mid-point and 20% below the high; the stock has been range-bound 14.90-16.60 for three months on thin volume. |
| Sentiment | 5 | No analyst coverage; a retail and high-net-worth favourite that moves with the index rather than with company news. |
| Governance | 6 | Founder-led and professionally staffed, but 78.8% insider ownership, related-party holdings across the group and a very small float concentrate decision-making. |

## 12. Data and method caveats

- The model applies the full dividend as a step down on the ex-date, which is the textbook treatment; PSX high-yield names often give back less than the full amount on the day, so treat the price median as the conservative case and the total-return probability as the decision number.
- Yahoo Finance carries no AHCL feed, so the daily history in this environment is 50 settled sessions (28 Jul - 7 Oct 2026) from stockanalysis.com: single source, verified against sarmaaya.pk (19 Aug close 16.43) and investing.com (18 Sep close 15.10) snapshots and sarmaaya's 8 Oct quote (previous close 15.48).
- With only 50 sessions the volatility estimate carries a wide standard error and the 200-day reference does not exist; the model uses a 50-session mean and the mid-point of the 52-week range (15.75) as the long-run centre instead, and a t-distribution robustness check is reported alongside the bootstrap interval.
- The committee is the deterministic mirror of the TradingAgents pipeline (same roles, same data
  tools, same rating scale); when an LLM key is available the vendored graph can be run instead.
- Probabilities are model output, not promises. The scenario book is analyst judgement and is
  stated so it can be scored later.

## 13. Sources

- AHCL annual and quarterly results (PSX data portal and PSX document 276323 directors' report)
- marketcreener / MarketScreener company profile (shareholders, holdings, PIA timeline), 2026
- Business Recorder: "Arif Habib consortium acquires remaining 25% stake in PIA", 2026-04-28
- Arab News / Dawn / Tribune coverage of the PIA privatisation, 2025-12-24 and 2025-12-30
- stockanalysis.com quote, dividend, history and company pages for PSX:AHCL, 2026-10-08
- sarmaaya.pk/stocks/AHCL (52-week range, free float, market cap), 2026-10-08
- Wikipedia / Grokipedia summaries of Arif Habib Corporation's subsidiary structure, 2026

---

*Research output produced by the Stock Insight / TradingAgents PSX pipeline - not investment
advice. Numbers are traceable to the sources above; the raw price snapshots and the forecast JSON
accompany this report in `reports/`.*
