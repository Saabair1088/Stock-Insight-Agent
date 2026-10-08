"""Bridge between the PSX layer and the vendored TradingAgents framework.

`TradingAgents <https://github.com/TauricResearch/TradingAgents>`_ (v0.6.0,
Apache-2.0) is vendored at ``TradingAgents/``.  This module is the glue that
lets the framework analyse PSX names such as ``BOP.KA`` without any of the
framework's default assumptions getting in the way:

* :func:`build_config` produces a TradingAgents config that points the data
  vendors, results directory and (optionally) the LLM provider at this project.
* :func:`register_psx_vendor` installs a ``psx`` data vendor into the
  framework's router.  It serves prices, indicators, fundamentals and news
  from the validated local snapshot + curated evidence base, so the analyst
  tool calls work on a workstation with no network access.
* :class:`OfflineLLM` is a deterministic, key-less stand-in *chat model*.  It
  satisfies the small interface the framework's nodes use (``invoke``,
  ``bind_tools``, ``with_structured_output``) and returns the stage outputs of
  the deterministic committee in :mod:`psx.agents`, so the *real* LangGraph
  pipeline -- analyst tool loops included -- executes end to end and writes
  its own ``complete_report.md`` / ``complete_report.html``.

With an API key present (``OPENAI_API_KEY``, ``ANTHROPIC_API_KEY``,
``GOOGLE_API_KEY``, ``GROQ_API_KEY``, ...), :func:`run_framework` runs the same
graph with real model reasoning instead.

Nothing here imports the framework at module load time: the module stays
stdlib-only so the default pipeline in :mod:`psx.report` keeps working on
plain ``python3``.
"""

from __future__ import annotations

import datetime as _dt
import importlib
import os
import sys
from typing import Any

from . import agents as _agents, data as _data, indicators as _ind, market_data as _md, \
    profiles as _profiles, research as _rs

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADINGAGENTS_DIR = os.path.join(REPO_ROOT, "TradingAgents")
FRAMEWORK_RESULTS_DIR = os.path.join(REPO_ROOT, "reports", "framework")
FRAMEWORK_CACHE_DIR = os.path.join(REPO_ROOT, "data", "psx", "framework_cache")
FRAMEWORK_MEMORY = os.path.join(FRAMEWORK_RESULTS_DIR, "memory", "trading_memory.md")

FRAMEWORK_VENDOR = "psx"
TICKER = "BOP.KA"
PSX_ALIASES = {"BOP", "BOP.KA", "BOP.PSX", "BOPKA"}

ANALYSTS = ("market", "social", "news", "fundamentals")

#: Environment variables the framework's LLM clients read, most preferred first.
LLM_KEY_ENV = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "XAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "MISTRAL_API_KEY",
    "OPENROUTER_API_KEY",
)


# --------------------------------------------------------------------------- #
# framework discovery
# --------------------------------------------------------------------------- #
def ensure_framework_on_path() -> str:
    """Prepend the vendored framework to ``sys.path``; return the directory."""
    if not os.path.isdir(TRADINGAGENTS_DIR):
        raise FileNotFoundError(
            f"vendored TradingAgents not found at {TRADINGAGENTS_DIR}; "
            "restore it with: git clone --depth 1 "
            "https://github.com/TauricResearch/TradingAgents.git TradingAgents"
        )
    if TRADINGAGENTS_DIR not in sys.path:
        sys.path.insert(0, TRADINGAGENTS_DIR)
    return TRADINGAGENTS_DIR


def available_llm_keys() -> dict[str, str]:
    """Provider -> env var, for every configured LLM key found in the environment."""
    return {env: os.environ[env] for env in LLM_KEY_ENV if os.environ.get(env)}


def framework_status() -> dict[str, Any]:
    """Whether the framework can be imported, and what an LLM run would need."""
    status: dict[str, Any] = {
        "vendored_dir": TRADINGAGENTS_DIR,
        "vendored": os.path.isdir(TRADINGAGENTS_DIR),
        "importable": False,
        "version": None,
        "llm_keys": sorted(available_llm_keys()),
        "offline_engine": True,
    }
    if not status["vendored"]:
        return status
    try:
        ensure_framework_on_path()
        ta = importlib.import_module("tradingagents")
        status["importable"] = True
        status["version"] = getattr(ta, "__version__", None)
    except Exception as exc:  # noqa: BLE001 - report, don't crash
        status["error"] = f"{type(exc).__name__}: {exc}"
    return status


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
def build_config(
    *,
    llm_provider: str | None = None,
    deep_model: str | None = None,
    quick_model: str | None = None,
    temperature: float | None = 0.2,
    results_dir: str = FRAMEWORK_RESULTS_DIR,
    cache_dir: str = FRAMEWORK_CACHE_DIR,
    **overrides: Any,
) -> dict:
    """A TradingAgents config tuned for PSX runs.

    Falls back to defaults for anything not supplied; ``llm_provider`` and the
    model names only matter for live (API-key) runs.
    """
    from tradingagents.default_config import DEFAULT_CONFIG

    config = dict(DEFAULT_CONFIG)
    config.update(
        {
            "results_dir": results_dir,
            "data_cache_dir": cache_dir,
            "memory_log_path": os.path.join(results_dir, "memory", "trading_memory.md"),
            "output_language": "English",
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1,
            "max_tool_rounds": 4,
            "temperature": temperature,
        }
    )
    if llm_provider:
        config["llm_provider"] = llm_provider
    if deep_model:
        config["deep_think_llm"] = deep_model
    if quick_model:
        config["quick_think_llm"] = quick_model
    # Every category this deployment can serve comes from the local PSX vendor.
    config["data_vendors"] = {
        "core_stock_apis": FRAMEWORK_VENDOR,
        "technical_indicators": FRAMEWORK_VENDOR,
        "fundamental_data": FRAMEWORK_VENDOR,
        "news_data": FRAMEWORK_VENDOR,
        "macro_data": FRAMEWORK_VENDOR,
        "prediction_markets": FRAMEWORK_VENDOR,
    }
    config.update(overrides)
    return config


# --------------------------------------------------------------------------- #
# PSX data vendor (serves the framework's tool calls from local data)
# --------------------------------------------------------------------------- #
def _canonical(symbol: str) -> str:
    """Canonical Yahoo-style symbol for any PSX name this vendor covers."""
    key = str(symbol).strip().upper().replace("-", ".")
    if key in PSX_ALIASES:
        return TICKER
    try:
        return _profiles.get(key).symbol
    except KeyError:
        raise _NoMarketData(
            symbol, detail="this deployment's PSX vendor covers "
            + ", ".join(sorted({TICKER, *[p.symbol for p in _profiles.PROFILES.values()]}))
        ) from None


def _load_psx(symbol: str | None = None):
    """Snapshot series + OHLCV window for one name, cached per process."""
    canonical = _canonical(symbol) if symbol else TICKER
    cache = getattr(_load_psx, "_cache", {})
    if canonical not in cache:
        if canonical == TICKER:
            cache[canonical] = (_data.load_snapshot(), _data.load_ohlcv_3mo())
        else:
            profile = _profiles.get(canonical)
            cache[canonical] = (_md.load_series(profile), _md.load_ohlcv(profile))
    _load_psx._cache = cache  # type: ignore[attr-defined]
    return cache[canonical]


# --------------------------------------------------------------------------- #
# per-name evidence base (BOP keeps its curated psx.research content; other
# names serve the equivalent structure from psx.profiles)
# --------------------------------------------------------------------------- #
def _slug(text: str, index: int) -> str:
    head = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in text.lower().split(".")[0])
    return f"{'-'.join(filter(None, head.split('-')))[:48] or 'item'}-{index}"


def _macro_key(text: str) -> str:
    t = text.lower()
    if "policy rate" in t or "sbp" in t or "monetary" in t or "mpc" in t:
        return "policy_rate"
    if "inflation" in t or "cpi" in t:
        return "inflation"
    if "kibor" in t or "t-bill" in t or "tbill" in t or "yield" in t:
        return "rates_market"
    if "reserve" in t:
        return "reserves"
    return "macro"


def _profile_evidence(profile) -> dict[str, Any]:
    def items(records, prefix: str):
        out = []
        for i, rec in enumerate(records):
            fact = rec.get("fact") or rec.get("detail") or rec.get("headline", "")
            out.append({
                "key": _slug(fact, i),
                "headline": (rec.get("headline") or fact.split(". ")[0])[:110],
                "detail": fact,
                "source": rec.get("source", f"{prefix} evidence base"),
                "date": rec.get("date", profile.as_of),
                "direction": rec.get("direction", "neutral"),
            })
        return out

    macro = []
    for i, m in enumerate(profile.macro):
        macro.append({
            "key": _macro_key(m["headline"] + " " + m["detail"]),
            "headline": m["headline"],
            "detail": m["detail"],
            "source": "curated macro evidence base",
            "date": profile.as_of,
            "direction": m.get("direction", "neutral"),
        })
    return {
        "subject": {
            "name": profile.name,
            "ticker_psx": profile.ticker,
            "ticker_yahoo": profile.symbol,
            "isin": profile.quote.get("isin", "n/a"),
            "sector": profile.sector,
            "shares_outstanding": profile.shares_out,
        },
        "company": items(profile.company, "company"),
        "sector": items(profile.sector_facts, "sector"),
        "macro": macro,
        "scorecard": {s["dimension"].lower().replace(" ", "_"): [s["score"], s["comment"]]
                      for s in profile.scorecard},
        "events": profile.events,
        "risks": profile.risks,
    }


def _evidence(symbol: str) -> dict[str, Any]:
    canonical = _canonical(symbol)
    if canonical == TICKER:
        return {
            "subject": _rs.SUBJECT, "company": _rs.COMPANY, "sector": _rs.SECTOR,
            "macro": _rs.MACRO, "scorecard": _rs.SCORECARD, "events": _rs.EVENTS,
            "risks": _rs.RISKS,
        }
    return _profile_evidence(_profiles.get(canonical))


class _NoMarketData(Exception):
    """Local stand-in for ``tradingagents.dataflows.errors.NoMarketDataError``.

    Converted at the boundary so this module imports even when the framework
    (and its pydantic-based error types) is unavailable.
    """

    def __init__(self, symbol: str, detail: str = ""):
        self.symbol = symbol
        self.detail = detail
        super().__init__(f"No market data for {symbol!r}: {detail}".rstrip(": "))


def _raise_no_data(symbol: str, detail: str = ""):
    """Raise the framework's own error type when it is importable."""
    try:
        from tradingagents.dataflows.errors import NoMarketDataError

        raise NoMarketDataError(symbol, detail=detail)
    except ImportError:  # pragma: no cover - framework not on path
        raise _NoMarketData(symbol, detail) from None


def _stock_data(symbol: str, start_date: str, end_date: str) -> str:
    """CSV-style daily rows for a PSX name, served from the validated snapshots."""
    symbol = _canonical(symbol)
    series, ohlcv = _load_psx(symbol)
    name = _evidence(symbol)["subject"]["name"]
    rows = [
        (d, c)
        for d, c in zip(series.dates, series.closes)
        if start_date <= d <= end_date
    ]
    if not rows:
        _raise_no_data(symbol, f"no sessions between {start_date} and {end_date}")
    lines = [
        f"# {symbol} ({name}, PSX, PKR) - {len(rows)} sessions "
        f"{rows[0][0]}..{rows[-1][0]}",
        f"# Source: {series.source}.",
        "Date,Close",
    ]
    lines += [f"{d},{c:.2f}" for d, c in rows]
    detail = [r for r in ohlcv["rows"] if start_date <= r["date"] <= end_date]
    if detail:
        lines += [
            "",
            f"# OHLCV detail for the {len(detail)} most recent sessions",
            "Date,Open,High,Low,Close,Volume",
        ]
        lines += [
            f"{r['date']},{r['open']:.2f},{r['high']:.2f},{r['low']:.2f},"
            f"{r['close']:.2f},{int(r['volume'])}"
            for r in detail
        ]
    return "\n".join(lines)


def _indicator_series(dates: list[str], closes: list[float], rows: list[dict],
                      indicator: str) -> list[tuple[str, float]]:
    """Point-in-time (date, value) pairs for one indicator, using psx.indicators."""
    ind = indicator.lower().strip()
    n = len(closes)

    def walk(compute, warmup: int, key: str | None = None):
        out: list[tuple[str, float]] = []
        for i in range(warmup - 1, n):
            value = compute(closes[: i + 1])
            if value is None:
                continue
            if key is not None:
                value = value.get(key) if isinstance(value, dict) else value
            if value is not None:
                out.append((dates[i], float(value)))
        return out

    if ind in ("close_10_ema", "close_20_ema", "close_50_ema"):
        window = int(ind.split("_")[1])
        series = _ind.ema_series(closes, window)
        return list(zip(dates[window - 1:], series))
    if ind.endswith("_sma"):
        window = int(ind.split("_")[1])
        return [(dates[i], _ind.sma(closes[: i + 1], window))  # type: ignore[misc]
                for i in range(window - 1, n) if _ind.sma(closes[: i + 1], window) is not None]
    if ind == "rsi":
        return walk(lambda c: _ind.rsi(c, 14), 15)
    if ind in ("macd", "macds", "macdh"):
        return walk(_ind.macd, 35, {"macd": "macd", "macds": "signal", "macdh": "histogram"}[ind])
    if ind in ("boll", "boll_ub", "boll_lb"):
        key = {"boll": "mid", "boll_ub": "upper", "boll_lb": "lower"}[ind]
        return walk(lambda c: _ind.bollinger(c, 20), 20, key)
    if ind == "atr":
        sub_rows = [r for r in rows if r["date"] <= dates[-1]]
        pairs = [(r["date"], _ind.atr(sub_rows[: i + 1], 14))
                 for i, r in enumerate(sub_rows) if i >= 14]
        return [(d, v) for d, v in pairs if v is not None]
    _raise_no_data(TICKER, f"indicator {indicator!r} is not served by the PSX vendor")


def _indicators(symbol: str, indicator: str, as_of_date: str, look_back_days: int) -> str:
    symbol = _canonical(symbol)
    series, ohlcv = _load_psx()
    dates, closes = series.dates, series.closes
    if as_of_date < dates[0]:
        _raise_no_data(symbol, f"snapshot starts {dates[0]}")
    cut = len([d for d in dates if d <= as_of_date])
    if cut == 0:
        _raise_no_data(symbol, f"no closes on or before {as_of_date}")
    dates, closes = dates[:cut], closes[:cut]
    pairs = _indicator_series(dates, closes, ohlcv["rows"], indicator)
    window = max(2, int(round(look_back_days * 252 / 365)))
    pairs = pairs[-window:]
    if not pairs:
        _raise_no_data(symbol, f"not enough history for {indicator}")
    body = "\n".join(f"{d},{v:.4f}" for d, v in pairs)
    return (
        f"# {symbol} {indicator} (PKR, computed by the psx.indicators module)\n"
        f"# latest {len(pairs)} sessions through {pairs[-1][0]}\n"
        f"Date,{indicator}\n{body}"
    )


def _research_digest(keys: tuple[str, ...], *, as_of: str | None = None,
                     symbol: str | None = None) -> str:
    blocks: list[str] = []
    ev = _evidence(symbol or TICKER)
    pools = [("COMPANY", ev["company"]), ("SECTOR", ev["sector"]), ("MACRO", ev["macro"])]
    for pool_name, items in pools:
        for item in items:
            if keys and item["key"] not in keys:
                continue
            blocks.append(
                f"- **{item['headline']}** ({item['date']}, {item['source']})\n"
                f"  {item['detail']}"
            )
    return "\n".join(blocks)


def _fundamentals(ticker: str, as_of_date: str | None = None) -> str:
    ticker = _canonical(ticker)
    ev = _evidence(ticker)
    subj = ev["subject"]
    series, _ = _load_psx(ticker)
    spot = series.closes[-1]
    lines = [
        f"# {subj['name']} ({ticker}) - fundamental overview",
        f"PSX ticker: {subj['ticker_psx']} | ISIN: {subj['isin']} | sector: {subj['sector']}",
        f"Shares outstanding: {subj['shares_outstanding'] / 1e9:.4f}bn | "
        f"last close: PKR {spot:.2f} ({series.dates[-1]}) | market cap: ~PKR "
        f"{subj['shares_outstanding'] * spot / 1e9:.1f}bn",
        "",
        "## Curated facts (latest filings and disclosures)",
        _research_digest((), symbol=ticker),
        "",
        "## Scorecard (0-10, from the same evidence base)",
        "\n".join(f"- {k.replace('_', ' ')}: {v[0]}/10 - {v[1]}" for k, v in ev["scorecard"].items()),
        "",
        "NOTE: PSX issuers are not covered by SEC EDGAR or Yahoo financial statements in this "
        "deployment; the facts above come from the company's own disclosures, PSX announcements and "
        "press coverage, each with its date.",
    ]
    return "\n".join(lines)


def _news(ticker: str, start_date: str, end_date: str) -> str:
    ticker = _canonical(ticker)
    blocks = [b for b in _research_digest((), symbol=ticker).split("\n- ") if b]
    return (
        f"# News / disclosure digest for {ticker} and its sector "
        f"({start_date}..{end_date})\n"
        "Curated from exchange filings, the central bank and the press; each item is dated. "
        "Items outside the requested window are still shown when they explain the current "
        "market state.\n\n" + "\n- ".join(blocks)
    )


def _global_news(as_of_date: str, look_back_days: int | None = None, limit: int | None = None,
                 symbol: str | None = None) -> str:
    items = _evidence(symbol or TICKER)["macro"]
    if limit:
        items = items[: int(limit)]
    body = "\n".join(
        f"- **{i['headline']}** ({i['date']}, {i['source']}) - {i['detail']}" for i in items
    )
    return f"# Pakistan macro digest (as of {as_of_date})\n{body}"


def _insider_transactions(ticker: str, as_of_date: str | None = None) -> str:
    _canonical(ticker)
    return (
        "DATA_UNAVAILABLE: no insider-transaction feed for PSX issuers via this vendor. "
        "Report insider activity as unavailable; do not fabricate filings."
    )


def _macro_indicators(indicator: str, curr_date: str, look_back_days: int | None = None,
                      symbol: str | None = None) -> str:
    """Serve the handful of Pakistan macro series the evidence base carries."""
    key_map = {
        "cpi": "inflation",
        "inflation": "inflation",
        "policy_rate": "policy_rate",
        "tbill": "rates_market",
        "kibor": "rates_market",
        "reserves": "reserves",
    }
    key = key_map.get(str(indicator).lower().strip())
    macro = _evidence(symbol or TICKER)["macro"]
    items = [m for m in macro if m["key"] == key] if key else []
    if not items:
        return (
            f"DATA_UNAVAILABLE: the PSX vendor has no FRED-style series for {indicator!r}. "
            "Pakistan macro series carried here: " + ", ".join(sorted(key_map)) + "."
        )
    body = "\n".join(f"- **{i['headline']}** ({i['date']}, {i['source']}) - {i['detail']}" for i in items)
    return f"# Pakistan macro series: {indicator} (as of {curr_date})\n{body}"


def _prediction_markets(topic: str, limit: int | None = None) -> str:
    return (
        "DATA_UNAVAILABLE: prediction-market coverage for Pakistan policy-rate/event contracts "
        "is not available in this deployment. Do not estimate implied probabilities."
    )


def _statement(ticker: str, *args, **kwargs) -> str:
    _canonical(ticker)
    _raise_no_data(
        TICKER,
        "PSX issuers have no SEC EDGAR / Yahoo financial-statement coverage here; use "
        "get_fundamentals, which carries the disclosed figures with dates",
    )


def _n(value, nd: int = 2) -> str:
    return "n/a" if value is None else f"{value:,.{nd}f}"


def _verified_snapshot(symbol: str, curr_date: str, look_back_days: int = 30) -> str:
    """Local replacement for the framework's yfinance-backed snapshot verifier."""
    symbol = _canonical(symbol)
    series, ohlcv = _load_psx(symbol)
    profile = _profiles.get(symbol) if symbol != TICKER else None
    snapshot_file = (os.path.relpath(profile.ohlcv_path, REPO_ROOT) if profile
                     else "data/psx/BOP_KA_daily_3mo.json")
    series_file = (os.path.relpath(profile.closes_path, REPO_ROOT) if profile and profile.closes_path
                   else "data/BOP_KA_daily_2y.json")
    spot = series.closes[-1]
    closes = series.closes
    recent = [
        (d, c)
        for d, c in zip(series.dates, series.closes)
        if d <= curr_date
    ][-max(2, int(look_back_days)):]
    rows = [r for r in ohlcv["rows"] if r["date"] <= curr_date][-5:]
    lines = [
        f"# VERIFIED market snapshot - {symbol} (source of truth)",
        f"as of: last settled session {series.dates[-1]} | close PKR {spot:.2f}",
        f"last five sessions (OHLCV, from {snapshot_file}):",
    ]
    for r in rows:
        lines.append(
            f"  {r['date']}  O {r['open']:.2f}  H {r['high']:.2f}  L {r['low']:.2f}  "
            f"C {r['close']:.2f}  V {int(r['volume']):,}"
        )
    lines += [
        "",
        f"## Indicator values (computed on the validated series {series_file})",
        "  SMA20 " + _n(_ind.sma(closes, 20)) + " | SMA50 " + _n(_ind.sma(closes, 50))
        + " | SMA100 " + _n(_ind.sma(closes, 100)) + " | SMA200 " + _n(_ind.sma(closes, 200)),
        "  EMA12 " + _n(_ind.ema(closes, 12)) + " | EMA26 " + _n(_ind.ema(closes, 26))
        + " | RSI14 " + _n(_ind.rsi(closes, 14), 1),
        f"  MACD {_ind.macd(closes)['macd']:.3f} | signal {_ind.macd(closes)['signal']:.3f} | "
        f"histogram {_ind.macd(closes)['histogram']:.3f}",
        f"  Bollinger(20,2) low {_ind.bollinger(closes)['lower']:.2f} | "
        f"mid {_ind.bollinger(closes)['mid']:.2f} | upper {_ind.bollinger(closes)['upper']:.2f}",
        "  ATR14 " + _n(_ind.atr(ohlcv['rows'], 14)) + " | ann. vol 20d "
        + _n((_ind.realized_vol(closes, 20) or 0) * 100, 1) + "%",
        "",
        "Recent closes: " + ", ".join(f"{d}:{c:.2f}" for d, c in recent[-10:]),
        "",
        "Cite only these numbers for exact price claims.",
    ]
    return "\n".join(lines)


def register_psx_vendor() -> list[str]:
    """Install the ``psx`` vendor into the framework's router; return its methods."""
    ensure_framework_on_path()
    from tradingagents.dataflows import router as _router

    methods = {
        "get_stock_data": _stock_data,
        "get_indicators": _indicators,
        "get_fundamentals": _fundamentals,
        "get_balance_sheet": _statement,
        "get_cashflow": _statement,
        "get_income_statement": _statement,
        "get_news": _news,
        "get_global_news": _global_news,
        "get_insider_transactions": _insider_transactions,
        "get_macro_indicators": _macro_indicators,
        "get_prediction_markets": _prediction_markets,
    }
    for method, func in methods.items():
        if method in _router.VENDOR_METHODS:
            _router.VENDOR_METHODS[method][FRAMEWORK_VENDOR] = func
    # The ydirect snapshot tool bypasses the router; replace it locally too.
    from tradingagents.agents import tools as _tools

    _tools.build_verified_market_snapshot = _verified_snapshot
    return sorted(methods)


# --------------------------------------------------------------------------- #
# offline chat-model stand-in
# --------------------------------------------------------------------------- #
def _prompt_text(prompt: Any) -> str:
    """Flatten whatever LangChain hands an LLM into one searchable string."""
    if isinstance(prompt, str):
        return prompt
    messages = prompt
    if hasattr(prompt, "to_messages"):
        messages = prompt.to_messages()
    if isinstance(messages, dict):
        messages = [messages]
    if not isinstance(messages, (list, tuple)):
        return str(prompt)
    chunks = []
    for m in messages:
        if isinstance(m, dict):
            chunks.append(str(m.get("content", "")))
        else:
            chunks.append(str(getattr(m, "content", m)))
    return "\n".join(chunks)


_TOOL_ARGS = {
    "get_stock_data": lambda d: {"start_date": _shift(d, -120), "end_date": d},
    "get_indicators": lambda d: {"indicator": "rsi", "curr_date": d, "look_back_days": 60},
    "get_verified_market_snapshot": lambda d: {"curr_date": d, "look_back_days": 30},
    "get_fundamentals": lambda d: {"curr_date": d},
    "get_balance_sheet": lambda d: {"freq": "quarterly", "curr_date": d},
    "get_cashflow": lambda d: {"freq": "quarterly", "curr_date": d},
    "get_income_statement": lambda d: {"freq": "quarterly", "curr_date": d},
    "get_news": lambda d: {"start_date": _shift(d, -21), "end_date": d},
    "get_global_news": lambda d: {"curr_date": d, "look_back_days": 7, "limit": 5},
    "get_macro_indicators": lambda d: {"indicator": "cpi", "curr_date": d, "look_back_days": 365},
    "get_insider_transactions": lambda d: {},
    "get_prediction_markets": lambda d: {"topic": "Pakistan policy rate", "limit": 5},
}


def _shift(date_iso: str, days: int) -> str:
    d = _dt.date.fromisoformat(date_iso) + _dt.timedelta(days=days)
    return d.isoformat()


class OfflineLLM:
    """Deterministic stand-in for a tool-calling chat model.

    It returns the deterministic committee's stage outputs, so a full
    TradingAgents graph run (including the analysts' tool loops) completes
    without an API key.  Interface implemented: ``invoke``, ``bind_tools``,
    ``with_structured_output`` and the ``.content`` / ``.tool_calls`` shape of
    the returned message.
    """

    def __init__(self, committee: _agents.CommitteeOutput, trade_date: str, max_tool_rounds: int = 2):
        self.committee = committee
        self.trade_date = trade_date
        self.max_tool_rounds = max_tool_rounds
        self.tools: dict[str, Any] = {}

    # -- plumbing the framework relies on ---------------------------------- #
    def __call__(self, prompt, *args, **kwargs):
        """Make the stand-in callable so ``prompt | llm`` LangChain pipes accept it."""
        return self.invoke(prompt, *args, **kwargs)

    def bind_tools(self, tools):
        for tool in tools:
            name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
            self.tools[name] = tool
        return self

    def with_structured_output(self, schema, **kwargs):
        return _OfflineStructured(self, schema)

    def invoke(self, prompt, config=None, **kwargs):
        from langchain_core.messages import AIMessage

        text = _prompt_text(prompt)
        if "tool rounds are spent" in text or not self.tools:
            return AIMessage(content=self._report_for(text))
        rounds = self._tool_rounds(prompt)
        if rounds < self.max_tool_rounds:
            call = self._scripted_call(rounds)
            if call:
                return AIMessage(content="", tool_calls=[call])
        return AIMessage(content=self._report_for(text))

    # -- scripted behaviour -------------------------------------------------- #
    @staticmethod
    def _tool_rounds(prompt) -> int:
        messages = prompt.to_messages() if hasattr(prompt, "to_messages") else prompt
        if not isinstance(messages, (list, tuple)):
            return 0
        return sum(1 for m in messages if getattr(m, "tool_calls", None))

    def _scripted_call(self, round_index: int) -> dict | None:
        wanted = [name for name in self.tools if name in _TOOL_ARGS]
        if round_index >= len(wanted):
            return None
        name = wanted[round_index]
        args = _TOOL_ARGS[name](self.trade_date)
        return {"name": name, "args": args, "id": f"offline-{round_index + 1}"}

    _MARKERS = (
        ("You are a Bull Analyst", "bull"),
        ("You are a Bear Analyst", "bear"),
        ("As the Aggressive Risk Analyst", "risk_aggressive"),
        ("As the Conservative Risk Analyst", "risk_conservative"),
        ("As the Neutral Risk Analyst", "risk_neutral"),
        ("You are a trading assistant tasked with analyzing financial markets", "market"),
        ("You are a researcher tasked with analyzing fundamental information", "fundamentals"),
        ("You are a news researcher tasked with analyzing recent news", "news"),
        ("sentiment", "sentiment"),
    )

    def _report_for(self, text: str) -> str:
        c = self.committee
        for marker, key in self._MARKERS:
            if marker.lower() in text.lower():
                if key == "bull":
                    return c.debate["bull"]
                if key == "bear":
                    return c.debate["bear"]
                if key == "risk_aggressive":
                    return c.risk_debate["aggressive"]
                if key == "risk_conservative":
                    return c.risk_debate["conservative"]
                if key == "risk_neutral":
                    return c.risk_debate["neutral"]
                if key in c.reports:
                    return c.reports[key]
        return (
            "Offline mode: this prompt matched no scripted stage, so no model reasoning is "
            "available. Decide from the data already in the state.\n"
        )


def _clean(text: str) -> str:
    """Drop markdown headings so stage outputs read as prose inside a field."""
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    return "\n".join(lines).strip()


def _offline_values(committee: _agents.CommitteeOutput) -> dict[str, Any]:
    tp = committee.trade_params
    entry = tp.get("entry_zone") or [None, None]
    return {
        "rating": committee.final_rating,
        "action": committee.action,
        "rationale": _clean(committee.debate["bull"]) + "\n\n---\n\n" + _clean(committee.debate["bear"]),
        "strategic_actions": _clean(committee.investment_plan),
        "reasoning": _clean(committee.trade_proposal),
        "entry": entry[0],
        "stop": tp.get("stop"),
        "size": f"{tp.get('size_pct_final', tp.get('size_pct', 0)):.1f}% of a diversified equity book",
        "executive_summary": _clean(committee.final_decision),
        "thesis": _clean(committee.investment_plan),
        "target": tp.get("target_2"),
    }


class _OfflineStructured:
    """``llm.with_structured_output(schema)`` stand-in: returns typed instances."""

    def __init__(self, llm: OfflineLLM, schema):
        self.llm = llm
        self.schema = schema

    def invoke(self, prompt, config=None, **kwargs):
        from tradingagents.agents import schemas as S

        vals = _offline_values(self.llm.committee)
        name = getattr(self.schema, "__name__", "")
        if self.schema is S.ResearchPlan:
            return S.ResearchPlan(
                recommendation=S.PortfolioRating(vals["rating"]),
                rationale=vals["rationale"],
                strategic_actions=vals["strategic_actions"],
            )
        if self.schema is S.TraderProposal:
            return S.TraderProposal(
                action=S.TraderAction(vals["action"]),
                reasoning=vals["reasoning"],
                entry_price=vals["entry"],
                stop_loss=vals["stop"],
                position_sizing=vals["size"],
            )
        if self.schema is S.PortfolioDecision:
            return S.PortfolioDecision(
                rating=S.PortfolioRating(vals["rating"]),
                executive_summary=vals["executive_summary"],
                investment_thesis=vals["thesis"],
                price_target=vals["target"],
                time_horizon="1 month (to 2026-11-06)",
            )
        if self.schema is S.SentimentReport:
            score = float(self.llm.committee.scores.get("sentiment", 5.0))
            band = ("Bullish" if score >= 6.5 else "Mildly Bullish" if score >= 5.5
                    else "Mixed" if score >= 4.5 else "Mildly Bearish" if score >= 3.5 else "Bearish")
            return S.SentimentReport(
                overall_band=S.SentimentBand(band),
                overall_score=score,
                confidence="medium",
                narrative=self.llm.committee.reports.get(
                    "sentiment", "No sentiment evidence available offline."),
            )
        raise NotImplementedError(f"offline structured output for {name} is not scripted")


# --------------------------------------------------------------------------- #
# running the framework
# --------------------------------------------------------------------------- #
def run_framework(
    committee: _agents.CommitteeOutput,
    *,
    ticker: str = TICKER,
    trade_date: str | None = None,
    mode: str = "auto",
    config: dict | None = None,
    selected_analysts: tuple[str, ...] = ANALYSTS,
    debug: bool = False,
    results_dir: str = FRAMEWORK_RESULTS_DIR,
) -> dict[str, Any]:
    """Execute the vendored TradingAgents graph and write its reports.

    ``mode`` is ``"offline"`` (deterministic stand-in LLM), ``"live"`` (real
    provider, needs an API key) or ``"auto"`` (live when a key is present,
    else offline).  Returns where the framework wrote its own report tree.
    """
    ensure_framework_on_path()
    trade_date = trade_date or _dt.date.today().isoformat()
    register_psx_vendor()

    tg = importlib.import_module("tradingagents.graph.trading_graph")
    keys = available_llm_keys()
    use_offline = mode == "offline" or (mode == "auto" and not keys)
    if mode == "live" and not keys:
        raise RuntimeError(
            "mode='live' needs one of: " + ", ".join(LLM_KEY_ENV) + " - set a key or use "
            "mode='offline' / mode='auto'."
        )

    cfg = config or build_config(results_dir=results_dir)
    shim = OfflineLLM(committee, trade_date)
    if use_offline:
        class _StubClient:
            def __init__(self, llm):
                self._llm = llm

            def get_llm(self):
                return self._llm

        tg.create_tier_client = lambda *a, **kw: _StubClient(shim)  # type: ignore[assignment]
        # yfinance identity lookup is pointless offline (and would hang on DNS):
        tg.resolve_instrument_identity = lambda ticker, *a, **kw: {}  # type: ignore[assignment]
        cfg = {**cfg, "llm_provider": "offline", "deep_think_llm": "psx-deterministic",
               "quick_think_llm": "psx-deterministic"}

    graph = tg.TradingAgentsGraph(
        selected_analysts=selected_analysts, debug=debug, config=cfg, callbacks=[]
    )
    state, decision = graph.propagate(ticker, trade_date)
    trade_ticker = str(ticker).upper().replace(".KA", "").replace(".PSX", "").replace(".", "_")
    save_path = os.path.join(results_dir, f"{trade_ticker}_{trade_date}")
    report_path = graph.save_reports(state, ticker, save_path=save_path, html=True)
    return {
        "mode": "offline" if use_offline else "live",
        "decision": decision,
        "rating": state.get("final_rating"),
        "report_path": str(report_path),
        "run_dir": save_path,
        "analysts": list(selected_analysts),
    }
