"""30-calendar-day movement forecast for a PSX equity.

Method (deliberately transparent, no third-party dependencies):

1. **Return pool** - the trailing 250 daily log returns are used as the
   empirical innovation distribution (captures fat tails and the stock's own
   event history far better than a normal assumption).
2. **Volatility scaling** - current EWMA(0.94) volatility is compared with the
   pool's unconditional volatility and the resampled innovations are scaled by
   that ratio (clipped to [0.6, 1.6]) so a forecast made in a quiet regime does
   not inherit crash-era standard deviations.
3. **Block bootstrap** - innovations are resampled in blocks of five sessions,
   preserving short-horizon autocorrelation and volatility clustering, and
   stacked into ``horizon``-session paths.
4. **Drift** - three documented regimes are produced: a martingale baseline
   (zero drift), a mean-reversion regime that pulls part-way toward the
   200-day moving average, and a catalyst overlay that expresses the
   event calendar (Q3 results and the SBP policy decision on 2026-10-26,
   the Government of Punjab capital tranche) as an explicit, auditable tilt.
5. **Aggregation** - 60,000 paths give the terminal distribution, quantile
   bands, first-passage probabilities and a risk budget.

The output is a probability *distribution*, not a point oracle: the report
quotes the median, the 80% interval and the probability of the directional
calls, and states the triggers that would invalidate them.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Sequence

from . import indicators as ind

DEFAULT_PATHS = 60_000
DEFAULT_BLOCK = 5
DEFAULT_HORIZON = 21  # trading sessions between 2026-10-07 and 2026-11-06

# Reference levels the headline distribution is quoted against.  The Bank of
# Punjab's book is the default so the original report reproduces bit-for-bit;
# other names pass their own set (see psx.profiles.Profile.thresholds).
BOP_THRESHOLDS = {
    "33.70 (200-DMA / prior support turned resistance)": 33.70,
    "34.46 (Jul-2026 swing close)": 34.46,
    "36.40 (GoPb issue price net of the 5% premium)": 36.40,
    "38.20 (GoPb equity-injection floor)": 38.20,
    "44.17 (all-time high, Jan-2026)": 44.17,
    "27.00 (May/Jun-2026 base)": 27.00,
    "24.26 (52-week low area)": 24.26,
}


@dataclass
class ForecastConfig:
    horizon_sessions: int = DEFAULT_HORIZON
    paths: int = DEFAULT_PATHS
    block: int = DEFAULT_BLOCK
    pool_window: int = 250
    # Known cash distributions inside the window: ((session index, PKR per share), ...).
    # Session 1 is the first trading day after ``as_of``.  The drop is applied to
    # every simulated path at that close, exactly as the exchange prints it.
    cash_drops: tuple = ()
    # Pull only a small fraction of the gap to the 200-DMA: at a one-month
    # horizon the mean-reversion signal is real but weak, and theta=1 (a full
    # snap-back) would have produced a nearly 14% one-month drift, which is not
    # defensible. theta=0.15 contributes roughly +2% over the window.
    # Long-run anchor for the mean-reversion leg.  ``None`` uses the 200-day
    # moving average of the series itself; names whose daily history is shorter
    # than 200 sessions pass a proxy (see psx.profiles / psx.analysts).
    ma_anchor: float | None = None
    mean_reversion_theta: float = 0.15
    catalyst_drift_annual: float = 0.04  # documented overlay, see reports/
    # Headline distribution = weighted mixture of the three regimes. Weights are
    # analyst judgement and are stated explicitly so they can be scored later.
    regime_weights: dict = field(
        default_factory=lambda: {"martingale": 0.35, "mean_reversion": 0.50, "catalyst": 0.15}
    )
    seed: int = 20261007


@dataclass
class ForecastResult:
    spot: float
    as_of: str
    horizon_sessions: int
    horizon_end: str
    daily_vol: float
    annual_vol: float
    regimes: dict = field(default_factory=dict)
    quantiles: dict = field(default_factory=dict)
    prob_up: float = 0.0
    prob_down: float = 0.0
    prob_above: dict = field(default_factory=dict)
    prob_below: dict = field(default_factory=dict)
    expected_price: float = 0.0
    expected_return: float = 0.0
    cvar_5: float = 0.0
    var_5: float = 0.0
    path_bands: dict = field(default_factory=dict)
    # Probability the path TOUCHES a threshold at any point in the window
    # (keyed like prob_above/prob_below).  prob_above/below describe the close
    # on the horizon date; these describe the journey.
    # Cash distributions inside the window: what was paid, and how the
    # probability of a *positive total return* differs from P(price higher).
    dividend_total: float = 0.0
    prob_up_total_return: float = 0.0
    touch_above: dict = field(default_factory=dict)
    touch_below: dict = field(default_factory=dict)
    terminal_sorted: list = field(default_factory=list)
    path_minima: list = field(default_factory=list)
    path_maxima: list = field(default_factory=list)
    distribution: list = field(default_factory=list)  # (price, probability) histogram


def _pool(closes: Sequence[float], window: int) -> list[float]:
    rets = ind.log_returns(closes[-(window + 1):])
    if len(rets) < 60:
        rets = ind.log_returns(closes)
    mu = sum(rets) / len(rets)
    return [r - mu for r in rets]


def _daily_vol(closes: Sequence[float]) -> float:
    vol = ind.ewma_vol(closes, annualize=False)
    if vol is None:
        rets = ind.log_returns(closes)
        vol = (sum(r * r for r in rets) / max(1, len(rets))) ** 0.5
    return vol


def _drift_for_regime(regime: str, closes: Sequence[float], cfg: ForecastConfig) -> float:
    """Daily log drift for a named regime."""
    if regime == "martingale":
        return 0.0
    if regime == "mean_reversion":
        ma200 = cfg.ma_anchor or ind.sma(closes, 200)
        if ma200 is None or closes[-1] <= 0:
            return 0.0
        gap = math.log(ma200 / closes[-1])
        # pull only a fraction of the gap, spread smoothly over the horizon
        return cfg.mean_reversion_theta * gap / cfg.horizon_sessions
    if regime == "catalyst":
        base = _drift_for_regime("mean_reversion", closes, cfg)
        return base + cfg.catalyst_drift_annual / ind.TRADING_DAYS
    raise ValueError(f"unknown regime {regime!r}")


def _simulate(
    closes: Sequence[float],
    cfg: ForecastConfig,
    regime: str,
    rng: random.Random,
    *,
    extremes: bool = False,
):
    """Terminal prices for one regime.

    With ``extremes=True`` each element becomes ``(terminal, path_min, path_max)``
    so the caller can price path touches.  The random draws are identical either
    way, so headline numbers do not move.
    """
    pool = _pool(closes, cfg.pool_window)
    if not pool:
        raise ValueError("not enough history to build a return pool")
    pool_vol = (sum(r * r for r in pool) / len(pool)) ** 0.5
    now_vol = _daily_vol(closes)
    scale = 1.0 if pool_vol == 0 else max(0.6, min(1.6, now_vol / pool_vol))
    drift = _drift_for_regime(regime, closes, cfg)

    drops = {int(i): float(a) for i, a in getattr(cfg, "cash_drops", ()) or ()}
    out = []
    span = cfg.horizon_sessions
    nb = len(pool)
    for _ in range(cfg.paths):
        log_p = 0.0
        remaining = span
        lo, hi = 0.0, 0.0
        session = 0
        while remaining > 0:
            take = min(cfg.block, remaining)
            start = rng.randrange(nb)
            for k in range(take):
                session += 1
                log_p += pool[(start + k) % nb] * scale + drift
                if session in drops and closes[-1] > 0:
                    log_p += math.log(max(0.01, 1.0 - drops[session] / closes[-1]))
                if log_p < lo:
                    lo = log_p
                elif log_p > hi:
                    hi = log_p
            remaining -= take
        terminal = closes[-1] * math.exp(log_p)
        if extremes:
            out.append((terminal, closes[-1] * math.exp(lo), closes[-1] * math.exp(hi)))
        else:
            out.append(terminal)
    return out


def _stats(prices: list[float], spot: float) -> dict:
    qs = {f"p{q}": ind.quantile(prices, q / 100.0) for q in (5, 10, 25, 50, 75, 90, 95)}
    rets = sorted(p / spot - 1.0 for p in prices)
    n = len(rets)
    var5 = rets[max(0, int(0.05 * n) - 1)]
    cvar5 = sum(rets[: max(1, int(0.05 * n))]) / max(1, int(0.05 * n))
    return {
        "quantiles": qs,
        "expected_price": sum(prices) / n,
        "prob_up": sum(1 for p in prices if p > spot) / n,
        "var_5": var5,
        "cvar_5": cvar5,
    }


def forecast(
    closes: Sequence[float],
    as_of: str,
    horizon_end: str,
    cfg: ForecastConfig | None = None,
    thresholds: dict | None = None,
) -> ForecastResult:
    """Run the Monte-Carlo forecast and package the headline statistics."""
    cfg = cfg or ForecastConfig()
    rng = random.Random(cfg.seed)
    spot = closes[-1]
    daily_vol = _daily_vol(closes)

    regimes = {}
    extremes = {}
    for regime in ("martingale", "mean_reversion", "catalyst"):
        paths = _simulate(closes, cfg, regime, rng, extremes=True)
        prices = [t for t, _, _ in paths]
        extremes[regime] = paths
        regimes[regime] = _stats(prices, spot)
        regimes[regime]["prices"] = prices  # kept for path bands / histogram

    # Headline = weighted mixture across regimes (weights are documented
    # judgement, not fitted). Paths are combined in proportion.
    weights = cfg.regime_weights
    total_w = sum(weights.values()) or 1.0
    mixed: list[float] = []
    mixed_min: list[float] = []
    mixed_max: list[float] = []
    for regime, weight in weights.items():
        regime_prices = regimes[regime]["prices"]
        take = int(round(len(regime_prices) * weight / total_w))
        mixed.extend(regime_prices[:take])
        mixed_min.extend(t for _, t, _ in extremes[regime][:take])
        mixed_max.extend(t for _, _, t in extremes[regime][:take])
    headline = _stats(mixed, spot)
    headline["prices"] = mixed
    prices = mixed

    thresholds = dict(thresholds) if thresholds is not None else dict(BOP_THRESHOLDS)
    prob_above = {k: sum(1 for p in prices if p >= v) / len(prices) for k, v in thresholds.items()}
    prob_below = {k: sum(1 for p in prices if p <= v) / len(prices) for k, v in thresholds.items()}
    touch_above = {k: sum(1 for m in mixed_max if m >= v) / len(mixed_max) for k, v in thresholds.items()}
    touch_below = {k: sum(1 for m in mixed_min if m <= v) / len(mixed_min) for k, v in thresholds.items()}

    # quantile path bands: re-run a light simulation that records intermediate steps
    bands = _path_bands(closes, cfg, rng)

    # terminal histogram for the report chart
    lo, hi = min(prices), max(prices)
    bins = 40
    width = (hi - lo) / bins if hi > lo else 1.0
    counts = [0] * bins
    for p in prices:
        idx = min(bins - 1, max(0, int((p - lo) / width)))
        counts[idx] += 1
    total = sum(counts)
    histogram = [
        {"price": round(lo + (i + 0.5) * width, 2), "prob": counts[i] / total} for i in range(bins)
    ]

    result = ForecastResult(
        spot=spot,
        as_of=as_of,
        horizon_sessions=cfg.horizon_sessions,
        horizon_end=horizon_end,
        daily_vol=daily_vol,
        annual_vol=daily_vol * math.sqrt(ind.TRADING_DAYS),
        regimes={k: {kk: vv for kk, vv in v.items() if kk != "prices"} for k, v in regimes.items()},
        quantiles=headline["quantiles"],
        prob_up=headline["prob_up"],
        prob_down=1.0 - headline["prob_up"],
        prob_above=prob_above,
        prob_below=prob_below,
        expected_price=headline["expected_price"],
        expected_return=headline["expected_price"] / spot - 1.0,
        cvar_5=headline["cvar_5"],
        var_5=headline["var_5"],
        path_bands=bands,
        dividend_total=sum(float(a) for _, a in (cfg.cash_drops or ())),
        prob_up_total_return=(sum(1 for p in prices
                                  if p > spot - sum(float(a) for _, a in (cfg.cash_drops or ())))
                              / len(prices)),
        touch_above=touch_above,
        touch_below=touch_below,
        terminal_sorted=sorted(prices),
        path_minima=mixed_min,
        path_maxima=mixed_max,
        distribution=histogram,
    )
    return result


def prob_close_below(f: ForecastResult, level: float) -> float:
    """P(the price finishes at or below ``level`` on the horizon date)."""
    import bisect

    if not getattr(f, "terminal_sorted", None):
        return 0.0
    return bisect.bisect_right(f.terminal_sorted, level) / len(f.terminal_sorted)


def prob_close_above(f: ForecastResult, level: float) -> float:
    import bisect

    if not getattr(f, "terminal_sorted", None):
        return 0.0
    return 1.0 - bisect.bisect_left(f.terminal_sorted, level) / len(f.terminal_sorted)


def touch_probability(f: ForecastResult, level: float) -> tuple[float, float]:
    """(P(path ever trades at or below ``level``), P(path ever trades at or above))."""
    if not f.path_minima:
        return 0.0, 0.0
    below = sum(1 for m in f.path_minima if m <= level) / len(f.path_minima)
    above = sum(1 for m in f.path_maxima if m >= level) / len(f.path_maxima)
    return below, above


def _path_bands(closes: Sequence[float], cfg: ForecastConfig, rng: random.Random) -> dict:
    """Median and 10/90 path of the terminal process (for the fan chart)."""
    paths = 8_000
    pool, span = _pool(closes, cfg.pool_window), cfg.horizon_sessions
    pool_vol = (sum(r * r for r in pool) / len(pool)) ** 0.5
    scale = max(0.6, min(1.6, _daily_vol(closes) / pool_vol)) if pool_vol else 1.0
    drift = _drift_for_regime("catalyst", closes, cfg)
    drops = {int(i): float(a) for i, a in getattr(cfg, "cash_drops", ()) or ()}
    nb = len(pool)
    steps = [[closes[-1]] for _ in range(paths)]
    for i in range(paths):
        log_p = 0.0
        remaining = span
        session = 0
        while remaining > 0:
            take = min(cfg.block, remaining)
            start = rng.randrange(nb)
            for k in range(take):
                session += 1
                log_p += pool[(start + k) % nb] * scale + drift
                if session in drops and closes[-1] > 0:
                    log_p += math.log(max(0.01, 1.0 - drops[session] / closes[-1]))
                steps[i].append(closes[-1] * math.exp(log_p))
            remaining -= take
    bands = {}
    for step in range(span + 1):
        col = [row[step] for row in steps if len(row) > step]
        bands[step] = {
            "p10": ind.quantile(col, 0.10),
            "p50": ind.quantile(col, 0.50),
            "p90": ind.quantile(col, 0.90),
        }
    return bands


# --------------------------------------------------------------------------- #
# scenario book (qualitative overlay, probabilities are analyst-judgement)
# --------------------------------------------------------------------------- #
def scenarios(spot: float, spec: Sequence[dict] | None = None) -> list[dict]:
    """Event-weighted scenarios for the 30-day window.

    Probabilities are the analyst committee's judgement (see reports/ for the
    reasoning) and are intentionally explicit so they can be scored later.
    ``spec`` overrides the default (Bank of Punjab) book with a per-name one,
    each item carrying ``name``/``probability``/``range``/``midpoint``/``triggers``.
    """
    if spec is not None:
        return [
            {
                "name": s["name"],
                "probability": s["probability"],
                "target_range": tuple(s["range"]),
                "midpoint": s["midpoint"],
                "return_pct": s["midpoint"] / spot - 1.0,
                "triggers": list(s["triggers"]),
            }
            for s in spec
        ]
    return [
        {
            "name": "Bull - pre-positioning into the GoPb issue and a clean Q3",
            "probability": 0.27,
            "target_range": (32.50, 36.50),
            "midpoint": 34.40,
            "return_pct": 34.40 / spot - 1.0,
            "triggers": [
                "Q3-2026 PAT >= Rs 5.0bn with flat-to-improving provisions",
                "SBP holds at 11.5% on 26 Oct or signals a peak in the hiking cycle",
                "KSE-100 reclaims 175,000 and foreign/insurance flows return to banks",
                "Confirmation that the first GoPb tranche (Rs 15-20bn) is on track for Dec-2026",
            ],
        },
        {
            "name": "Base - basing between support and the falling 50-DMA",
            "probability": 0.46,
            "target_range": (28.00, 32.50),
            "midpoint": 30.40,
            "return_pct": 30.40 / spot - 1.0,
            "triggers": [
                "Q3 PAT in the Rs 4.0-5.0bn range; no negative surprise on NPLs",
                "MPC holds with a neutral statement; KIBOR stays flat",
                "KSE-100 range-bound 160,000-172,000 as the political standoff drags on",
                "28.55 (Oct-2026 low) holds on a weekly close",
            ],
        },
        {
            "name": "Bear - political risk premium plus a hawkish MPC",
            "probability": 0.27,
            "target_range": (24.00, 28.00),
            "midpoint": 26.60,
            "return_pct": 26.60 / spot - 1.0,
            "triggers": [
                "SBP hikes 100bp to 12.5% on 26 Oct or the statement turns explicitly hawkish",
                "Q3 provisions spike / Punjab-scheme asset-quality noise",
                "KSE-100 breaks 160,000; long march escalates into a constitutional crisis",
                "GoPb tranche slips past 31 Dec 2026, reviving dilution and capital concerns",
            ],
        },
    ]
