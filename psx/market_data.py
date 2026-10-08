"""Profile-aware loaders for the validated PSX snapshots under ``data/psx/``.

The Bank of Punjab's original snapshot loader lives in :mod:`psx.data`; this
module resolves a :class:`psx.profiles.Profile` to its own files and returns
the same :class:`psx.data.Series` / OHLCV shapes, so every downstream module
(indicators, forecast, committee, report) is agnostic about the name.
"""

from __future__ import annotations

import json
import os

from . import data as _data
from .profiles import Profile


def load_series(profile: Profile) -> _data.Series:
    """Daily close series for ``profile`` (ascending by date, settled rows only)."""
    if profile.closes_path and os.path.exists(profile.closes_path):
        with open(profile.closes_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        dates = list(raw["dates"])
        closes = [float(c) for c in raw["closes"] if c is not None]
        dates = dates[: len(closes)]
        source = raw.get("source", profile.symbol)
    else:
        rows = load_ohlcv(profile)["rows"]
        dates = [r["date"] for r in rows]
        closes = [r["close"] for r in rows]
        source = f"{profile.symbol} daily closes derived from {os.path.basename(profile.ohlcv_path)}"
    if len(dates) != len(closes) or not closes:
        raise ValueError(f"{profile.symbol}: malformed close series ({len(dates)} dates, {len(closes)} closes)")
    if dates != sorted(dates):
        raise ValueError(f"{profile.symbol}: close series is not ascending by date")
    return _data.Series(
        symbol=profile.symbol,
        dates=dates,
        closes=closes,
        source=source,
        caveats=list(profile.data_caveats),
    )


def load_ohlcv(profile: Profile) -> dict:
    """Daily OHLCV rows, oldest first, with any null rows dropped."""
    with open(profile.ohlcv_path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rows = []
    for row in reversed(raw["rows"]):
        close = row.get("close")
        if close is None:
            continue
        rows.append({
            "date": row["date"],
            "open": float(row.get("open") if row.get("open") is not None else close),
            "high": float(row.get("high") if row.get("high") is not None else close),
            "low": float(row.get("low") if row.get("low") is not None else close),
            "close": float(close),
            "volume": float(row.get("volume") or 0.0),
        })
    if not rows:
        raise ValueError(f"{profile.symbol}: no usable OHLCV rows in {profile.ohlcv_path}")
    if rows[-1]["date"] != profile.spot_date:
        raise ValueError(
            f"{profile.symbol}: OHLCV window ends {rows[-1]['date']}, expected the spot date "
            f"{profile.spot_date} - refresh the snapshot in data/psx/"
        )
    return {"symbol": profile.symbol, "rows": rows, "window": f"{rows[0]['date']}..{rows[-1]['date']}"}
