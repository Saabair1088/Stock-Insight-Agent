"""Price-data access for PSX names.

The sandbox this project was bootstrapped in has no direct HTTP egress, so the
authoritative history is stored as a *snapshot* under ``data/`` and validated
against independent anchors.  When the code runs on a machine with internet
access, :func:`fetch_yahoo_daily` will refresh that snapshot from Yahoo Finance
(``<TICKER>.KA`` for PSX listings) so the models are always trained on the
freshest series available.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
DATA_PSX_DIR = os.path.join(DATA_DIR, "psx")
SNAPSHOT = os.path.join(DATA_DIR, "BOP_KA_daily_2y.json")
# The 3-month OHLCV window was re-fetched on 2026-10-07 into data/psx/ with the
# dividend adjustment documented; the older data/ copy stays as a fallback.
OHLCV_3MO_CANDIDATES = (
    os.path.join(DATA_PSX_DIR, "BOP_KA_daily_3mo.json"),
    os.path.join(DATA_DIR, "BOP_KA_3mo_daily_ohlcv.json"),
)
OHLCV_3MO = OHLCV_3MO_CANDIDATES[0]

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


@dataclass(frozen=True)
class Bar:
    """One daily session (all prices in the listing currency, PKR)."""

    date: str
    close: float


@dataclass
class Series:
    """A dated close series plus provenance."""

    symbol: str
    dates: list[str]
    closes: list[float]
    source: str
    caveats: list[str]

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.closes)

    @property
    def last_date(self) -> str:
        return self.dates[-1]

    @property
    def spot(self) -> float:
        """Most recent *settled* close."""
        return self.closes[-1]


def _ts_to_date(ts: int) -> str:
    return _dt.datetime.fromtimestamp(ts, tz=_dt.timezone.utc).strftime("%Y-%m-%d")


def load_snapshot(path: str = SNAPSHOT) -> Series:
    """Load the validated Yahoo snapshot checked into ``data/``."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    dates = [_ts_to_date(t) for t in raw["timestamps"]]
    closes = [c for c in raw["closes"]]
    # Drop unresolved tail rows (e.g. a session that had not settled).
    while closes and closes[-1] is None:
        closes.pop()
        dates.pop()
    caveat = raw.get("caveat")
    return Series(
        symbol=raw["symbol"],
        dates=dates,
        closes=[float(c) for c in closes],
        source=raw.get("source", "snapshot"),
        caveats=[caveat] if caveat else [],
    )


def load_ohlcv_3mo(path: str | None = None) -> dict:
    """Load the 3-month OHLCV snapshot (used for volume and intraday ranges).

    Prefers the freshest fetch in ``data/psx/`` and falls back to the original
    ``data/`` copy when that file is absent.
    """
    if path is None:
        path = next((p for p in OHLCV_3MO_CANDIDATES if os.path.exists(p)), OHLCV_3MO)
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rows = []
    for idx, ts in enumerate(raw["timestamps"]):
        close = raw["close"][idx]
        if close is None:
            continue
        rows.append(
            {
                "date": _ts_to_date(ts),
                "open": raw["open"][idx],
                "high": raw["high"][idx],
                "low": raw["low"][idx],
                "close": close,
                "volume": raw["volume"][idx] or 0,
            }
        )
    return {"symbol": raw["symbol"], "rows": rows}


def fetch_yahoo_daily(symbol: str = "BOP.KA", rng: str = "1y", timeout: int = 20) -> Series:
    """Refresh a daily close series from Yahoo Finance.

    Requires outbound HTTP access; raises ``OSError`` when unavailable so the
    caller can fall back to the checked-in snapshot.
    """
    query = urllib.parse.urlencode({"range": rng, "interval": "1d"})
    url = YAHOO_CHART.format(symbol=urllib.parse.quote(symbol)) + "?" + query
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (psx-research)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed host
        payload = json.loads(resp.read().decode("utf-8"))
    result = payload["chart"]["result"][0]
    stamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    dates, vals = [], []
    for ts, close in zip(stamps, closes):
        if close is None:
            continue
        dates.append(_ts_to_date(ts))
        vals.append(float(close))
    if not vals:
        raise OSError(f"no data returned for {symbol}")
    return Series(
        symbol=symbol,
        dates=dates,
        closes=vals,
        source=f"Yahoo Finance chart API ({symbol}, range={rng}) fetched {_dt.date.today()}",
        caveats=[],
    )


def load_series(symbol: str = "BOP.KA", prefer_live: bool = True) -> Series:
    """Best available series: live Yahoo pull, else the checked-in snapshot."""
    if prefer_live:
        try:
            live = fetch_yahoo_daily(symbol)
            if len(live) >= 200:
                return live
        except Exception:  # noqa: BLE001 - any network problem falls back
            pass
    return load_snapshot()
