"""Pure-stdlib technical and risk indicators (no numpy/pandas required).

Sized for daily equity series in the 250-500 observation range, which is what
30-day movement forecasting needs.  Every function is defensive about short
inputs so the pipeline degrades gracefully instead of raising.
"""

from __future__ import annotations

import math
import statistics as st
from collections.abc import Sequence

TRADING_DAYS = 252


# --------------------------------------------------------------------------- #
# returns / risk
# --------------------------------------------------------------------------- #
def log_returns(closes: Sequence[float]) -> list[float]:
    out = []
    for prev, cur in zip(closes, closes[1:]):
        if prev > 0 and cur > 0:
            out.append(math.log(cur / prev))
    return out


def simple_returns(closes: Sequence[float]) -> list[float]:
    return [cur / prev - 1.0 for prev, cur in zip(closes, closes[1:]) if prev > 0]


def total_return(closes: Sequence[float], lookback: int | None = None) -> float | None:
    if len(closes) < 2:
        return None
    window = closes[-(lookback + 1):] if lookback else closes
    if len(window) < 2 or window[0] <= 0:
        return None
    return window[-1] / window[0] - 1.0


def realized_vol(closes: Sequence[float], window: int = 20, annualize: bool = True) -> float | None:
    rets = log_returns(closes[-(window + 1):])
    if len(rets) < 3:
        return None
    vol = st.pstdev(rets)
    return vol * math.sqrt(TRADING_DAYS) if annualize else vol


def ewma_vol(closes: Sequence[float], lam: float = 0.94, annualize: bool = True) -> float | None:
    """RiskMetrics-style exponentially weighted volatility."""
    rets = log_returns(closes)
    if len(rets) < 20:
        return None
    var = st.pvariance(rets[:20])
    for r in rets[20:]:
        var = lam * var + (1 - lam) * r * r
    vol = math.sqrt(var)
    return vol * math.sqrt(TRADING_DAYS) if annualize else vol


def skewness(values: Sequence[float]) -> float | None:
    if len(values) < 3:
        return None
    mu, sd = st.fmean(values), st.pstdev(values)
    return 0.0 if sd == 0 else sum(((v - mu) / sd) ** 3 for v in values) / len(values)


def excess_kurtosis(values: Sequence[float]) -> float | None:
    if len(values) < 4:
        return None
    mu, sd = st.fmean(values), st.pstdev(values)
    return 0.0 if sd == 0 else sum(((v - mu) / sd) ** 4 for v in values) / len(values) - 3.0


def max_drawdown(closes: Sequence[float]) -> float:
    peak, worst = float("-inf"), 0.0
    for c in closes:
        peak = max(peak, c)
        if peak > 0:
            worst = min(worst, c / peak - 1.0)
    return worst


def drawdown_from_peak(closes: Sequence[float]) -> float:
    if not closes:
        return 0.0
    peak = max(closes)
    return closes[-1] / peak - 1.0 if peak > 0 else 0.0


def historical_var(closes: Sequence[float], level: float = 0.05) -> float | None:
    """One-day historical VaR at ``level`` (positive number = loss magnitude)."""
    rets = sorted(simple_returns(closes))
    if len(rets) < 40:
        return None
    idx = max(0, int(math.floor(level * len(rets))) - 1)
    return -rets[idx]


def historical_cvar(closes: Sequence[float], level: float = 0.05) -> float | None:
    rets = sorted(simple_returns(closes))
    if len(rets) < 40:
        return None
    tail = rets[: max(1, int(math.floor(level * len(rets))))]
    return -st.fmean(tail)


def quantile(values: Sequence[float], q: float) -> float:
    """Linear-interpolated quantile (``q`` in [0, 1])."""
    xs = sorted(values)
    if not xs:
        return float("nan")
    if len(xs) == 1:
        return xs[0]
    pos = q * (len(xs) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


# --------------------------------------------------------------------------- #
# trend / momentum
# --------------------------------------------------------------------------- #
def sma(closes: Sequence[float], window: int) -> float | None:
    if len(closes) < window:
        return None
    return st.fmean(closes[-window:])


def ema_series(closes: Sequence[float], window: int) -> list[float]:
    if len(closes) < window:
        return []
    k = 2.0 / (window + 1)
    out = [st.fmean(closes[:window])]
    for c in closes[window:]:
        out.append(out[-1] + k * (c - out[-1]))
    return out


def ema(closes: Sequence[float], window: int) -> float | None:
    series = ema_series(closes, window)
    return series[-1] if series else None


def rsi(closes: Sequence[float], window: int = 14) -> float | None:
    if len(closes) < window + 1:
        return None
    gains, losses = [], []
    for prev, cur in zip(closes[:-1], closes[1:]):
        delta = cur - prev
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain, avg_loss = st.fmean(gains[:window]), st.fmean(losses[:window])
    for g, l in zip(gains[window:], losses[window:]):  # Wilder smoothing
        avg_gain = (avg_gain * (window - 1) + g) / window
        avg_loss = (avg_loss * (window - 1) + l) / window
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def macd(closes: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9):
    fast_s, slow_s = ema_series(closes, fast), ema_series(closes, slow)
    if not fast_s or not slow_s:
        return None
    offset = len(fast_s) - len(slow_s)
    macd_line = [f - s for f, s in zip(fast_s[offset:], slow_s)]
    if len(macd_line) < signal:
        return None
    signal_line = ema_series(macd_line, signal)
    return {
        "macd": macd_line[-1],
        "signal": signal_line[-1] if signal_line else None,
        "histogram": (macd_line[-1] - signal_line[-1]) if signal_line else None,
    }


def bollinger(closes: Sequence[float], window: int = 20, mult: float = 2.0):
    if len(closes) < window:
        return None
    mid = st.fmean(closes[-window:])
    sd = st.pstdev(closes[-window:])
    return {
        "mid": mid,
        "upper": mid + mult * sd,
        "lower": mid - mult * sd,
        "bandwidth": (2 * mult * sd / mid) if mid else None,
        "pct_b": ((closes[-1] - (mid - mult * sd)) / (2 * mult * sd)) if sd else 0.5,
    }


def true_range(rows: Sequence[dict]) -> list[float]:
    out = []
    for prev, cur in zip(rows, rows[1:]):
        if cur["high"] is None or cur["low"] is None or prev["close"] is None:
            continue
        out.append(
            max(
                cur["high"] - cur["low"],
                abs(cur["high"] - prev["close"]),
                abs(cur["low"] - prev["close"]),
            )
        )
    return out


def atr(rows: Sequence[dict], window: int = 14) -> float | None:
    trs = true_range(rows)
    if len(trs) < window:
        return None
    value = st.fmean(trs[:window])
    for tr in trs[window:]:  # Wilder smoothing
        value = (value * (window - 1) + tr) / window
    return value


def beta(asset_returns: Sequence[float], market_returns: Sequence[float]) -> float | None:
    n = min(len(asset_returns), len(market_returns))
    if n < 30:
        return None
    a, m = asset_returns[-n:], market_returns[-n:]
    ma, mm = st.fmean(a), st.fmean(m)
    cov = sum((x - ma) * (y - mm) for x, y in zip(a, m)) / (n - 1)
    var = sum((y - mm) ** 2 for y in m) / (n - 1)
    return cov / var if var else None


def relative_strength(closes: Sequence[float], lookback: int = 21) -> float | None:
    """Price change over ``lookback`` sessions, in percent."""
    tr = total_return(closes, lookback)
    return None if tr is None else tr * 100.0


# --------------------------------------------------------------------------- #
# support / resistance from the OHLCV snapshot
# --------------------------------------------------------------------------- #
def swing_levels(rows: Sequence[dict], window: int = 5, max_levels: int = 6) -> dict:
    """Fractal swing highs/lows, deduplicated into nearby price clusters."""
    highs, lows = [], []
    for i in range(window, len(rows) - window):
        window_rows = rows[i - window: i + window + 1]
        if rows[i]["high"] == max(r["high"] for r in window_rows):
            highs.append(round(rows[i]["high"], 2))
        if rows[i]["low"] == min(r["low"] for r in window_rows):
            lows.append(round(rows[i]["low"], 2))
    return {"swing_highs": sorted(set(highs)), "swing_lows": sorted(set(lows))}
