# Stock Insight Agent — PSX deep research & 30-day movement forecasts

A deep-research assessment and 30-day movement forecast for three Pakistan Stock
Exchange names, built on top of a vendored copy of the
[`TradingAgents`](https://github.com/TauricResearch/TradingAgents) multi-agent
framework (v0.6.0, Apache-2.0):

| Name | Ticker | Report (markdown) | Plain-language companion | Call, in one line |
|------|--------|-------------------|--------------------------|-------------------|
| The Bank of Punjab | `BOP.KA` | [`reports/BOP_research_2026-10-07.md`](reports/BOP_research_2026-10-07.md) | [`reports/BOP_explained_simply.md`](reports/BOP_explained_simply.md) | 21 sessions to 2026-11-06: P(up) 54%, median 29.99, 80% band 27.06–33.81, **Hold**, stop 27.31. |
| Pakistan State Oil | `PSO.KA` | [`reports/PSO_research_2026-10-07.md`](reports/PSO_research_2026-10-07.md) | [`reports/PSO_explained_simply.md`](reports/PSO_explained_simply.md) | 22 sessions to 2026-11-06: P(positive total return) 56%, price median 348.58, 80% band 323.60–373.54, **Hold**, stop 321.98. |
| Arif Habib Corporation | `AHCL` | [`reports/AHCL_research_2026-10-07.md`](reports/AHCL_research_2026-10-07.md) | [`reports/AHCL_explained_simply.md`](reports/AHCL_explained_simply.md) | 22 sessions to 2026-11-06: P(positive total return) 51%, price median 14.26, 80% band 13.15–15.50, **Hold**, stop 13.57. |

Each bundle contains the report (`.md` + a self-contained `.html` with inline SVG
charts), the forecast JSON, two SVG charts, and the framework's own report tree
under `reports/framework/<TICKER>_<date>/`.

> **Why PSO and AHCL show two probabilities.** Both go ex-dividend inside the
> window (20 Oct 2026: Rs 10.00 for PSO, Rs 1.25 for AHCL — 2.8% and 8.1% of the
> price). The model applies the dividend as the step down the exchange prints,
> so the *price* distribution is lower while the *shareholder's* outcome adds
> the cash back. Both numbers are reported everywhere, and the total-return one
> is the decision number.

---

## Quick start

```bash
# 1. Reproduce any report bundle with nothing but stock Python 3.11+ (stdlib only)
python3 scripts/run_bop_assessment.py                  # BOP (its original runner)
python3 scripts/run_psx_assessment.py --symbol PSO     # profile-driven runner
python3 scripts/run_psx_assessment.py --symbol AHCL

# 2. Re-validate every price artifact against its independent anchors
python3 scripts/validate_data.py
python3 scripts/ingest_psx_data.py      # re-parse data/raw/* into data/psx/*

# 3. Also run the real TradingAgents LangGraph pipeline end-to-end.
#    Without an LLM key it uses the deterministic stand-in model; with a key it
#    runs live. Both modes need the framework dependencies in .venv:
python3 -m venv .venv && .venv/bin/pip install -e ./TradingAgents matplotlib
python3 scripts/run_psx_assessment.py --symbol PSO --framework   # offline graph run
OPENAI_API_KEY=... python3 scripts/run_psx_assessment.py --symbol PSO --framework --mode live
```

## What's in the box

| Path | What it is |
|------|------------|
| `psx/profiles.py` | **The per-name layer.** Everything name-specific lives here: identity, quote/valuation block, the curated evidence base (company, sector, macro), events, risks, bull/bear cases, falsification triggers, forecast thresholds, scenario book, evidence caveats, sources — plus the price-artifact paths. A new PSX name is a new profile. |
| `psx/data.py` | Snapshot access for the name with a hand-built Yahoo feed (`BOP.KA`): validated series + short OHLCV window. |
| `psx/market_data.py` | Profile-driven loaders: canonical close series and OHLCV window for any registered name, with validation (ascending dates, spot-date match). |
| `psx/indicators.py` | Pure-stdlib technical & risk indicators (returns, vol, RSI, MACD, Bollinger, ATR, VaR/CVaR, swings). |
| `psx/forecast.py` | The Monte-Carlo movement forecast: block-bootstrapped returns, EWMA volatility scaling, three drift regimes, **known cash distributions applied as ex-date steps**, path-touch probabilities, quantiles, VaR/CVaR. Seeded and reproducible. |
| `psx/analysts.py` | The committee for any profile: market / fundamentals / news / sentiment analysts → bull-vs-bear debate → research manager → trader → risk debate → portfolio manager, with model-derived scenario levels and a student-t(4) robustness cross-check for short histories. |
| `psx/agents.py`, `psx/research.py` | BOP's original hand-built committee and its curated evidence base (kept exactly as delivered). |
| `psx/writer.py` | Ticker-agnostic report writer: markdown, self-contained HTML, forecast JSON, inline SVG charts, `{TICKER}_*` filenames. |
| `psx/report.py` | The original BOP renderer (markdown/HTML/SVG), now parameterised by floor/book/anchor/title. |
| `psx/tradingagents_bridge.py` | Bridge to the vendored framework: config builder, a `psx` data vendor serving the framework's tools from local validated data for **any registered ticker**, and an offline stand-in chat model so the graph runs without an API key. |
| `scripts/run_bop_assessment.py` | BOP's one-shot runner (kept bit-for-bit reproducible). |
| `scripts/run_psx_assessment.py` | Profile-driven runner for any other name, `--framework` optional. |
| `scripts/ingest_psx_data.py`, `scripts/validate_data.py` | The data pipeline: parse `data/raw/*` captures into canonical `data/psx/*` artifacts with cross-checks, and re-validate every artifact. |
| `TradingAgents/` | Vendored framework source (unmodified). |
| `data/raw/` | Verbatim price captures (Yahoo spark JSON, exchange tables) exactly as fetched. |
| `data/psx/` | Canonical validated artifacts: daily closes, OHLCV windows, weekly/monthly aggregates. |
| `reports/` | Delivered reports, forecast JSONs, charts, plain-language companions, framework trees. |

## Data provenance

The sandbox that assembled this dataset has no general HTTP egress, so every
price series was fetched through a text channel and then **cross-validated by
timestamp** (never by index) against independent anchors before use:

* **BOP** — Yahoo Finance daily JSON (2-year), anchored on the PSX data portal
  and TradingView prints.
* **PSO** — Yahoo `spark` daily/weekly/monthly (192 YTD sessions, 105 weekly
  bars, 60 monthly bars), extended to the 7 Oct close from the stockanalysis.com
  6-month table and cross-checked against sarmaaya.pk's 8 Oct previous close.
* **AHCL** — **Yahoo has no feed for this ticker** (verified). The daily history
  is the 50-session exchange table (28 Jul → 7 Oct 2026) from stockanalysis.com,
  cross-checked against sarmaaya.pk and investing.com snapshots; the model
  therefore reports a short-history robustness band (student-t) next to the
  bootstrap interval.

Known caveats are encoded in the data files and in each profile's
`data_caveats`: Yahoo's chunked responses sometimes repeat or pad values (the
canonical series joins on timestamp and drops holiday padding), the stockanalysis
"6M" tables are the last 50 sessions only, and the AHCL pool is 50 sessions.

## Framework integration notes

* `psx.tradingagents_bridge.register_psx_vendor()` installs a `psx` vendor into
  the framework's `VENDOR_METHODS` for prices, indicators, fundamentals, news
  and macro series, and replaces the yfinance-only "verified snapshot" tool.
  PSX issuers have no SEC EDGAR/Yahoo statement coverage, so statement tools
  deliberately return the framework's `NO_DATA_AVAILABLE` sentinel rather than
  invented numbers.
* `OfflineLLM` implements the small interface the framework's nodes use
  (`invoke`, `bind_tools`, `with_structured_output`) and returns the
  deterministic committee's stage outputs, so the **actual LangGraph pipeline**
  — analyst tool loops included — executes with no API key and writes its own
  report tree. Swap in a key and the same graph reasons with a real model.
* Ratings, schemas and state fields follow
  `TradingAgents/tradingagents/agents/schemas.py` exactly
  (`Buy / Overweight / Hold / Underweight / Sell`; `Buy / Hold / Sell` for the
  trader), so the deterministic and LLM engines are interchangeable.

## Reproducibility

* Forecast seed `20261007`, 60,000 paths, block-5 bootstrap, EWMA vol scaling,
  regime weights per profile. Re-running a runner regenerates the forecast JSON,
  report and charts bit-for-bit (BOP's published numbers are byte-identical
  after the parameterisation work).
* All research facts carry a source and a date in the profile's evidence base
  and are reproduced in each report's evidence table.
* Framework runs are logged to `reports/framework/` including the complete
  state JSON of the run.

## Disclaimer

This is research output, not investment advice. Each assessment uses public
sources up to 2026-10-07/08; prices and events after that date are not reflected
(PSX prints from 8 Oct onward are recorded only as post-as-of validation data).
BOP is majority-owned by the Government of Punjab, PSO is a state-linked national
asset and AHCL's largest holding is the privatised national airline — all three
carry political and regulatory risk beyond the usual.
