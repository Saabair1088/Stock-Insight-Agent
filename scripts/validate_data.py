#!/usr/bin/env python3
"""Validate every PSX price artifact in ``data/`` against independent anchors.

The project's price history was assembled by joining several Yahoo Finance
fetches (each of which is reliable only when it comes back in a single
response).  This script re-checks the joins by *timestamp* -- never by index --
and verifies the anchor values that were corroborated against PSX's own data
portal, invest.pk and stockanalysis.com.

    python3 scripts/validate_data.py

Exits non-zero on the first set of failures.  Stdlib only.
"""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

DATA = os.path.join(REPO_ROOT, "data")
DATA_PSX = os.path.join(DATA, "psx")

FAILURES: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("  ok   " if ok else "  FAIL ") + message)
    if not ok:
        FAILURES.append(message)


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def close_map(payload: dict, close_key: str = "close") -> dict[str, float]:
    """timestamp -> close, skipping nulls; asserts strictly increasing stamps."""
    stamps = payload["timestamps"]
    closes = payload.get(close_key) or payload.get("closes")
    assert closes is not None, f"no close/closes array in {payload.get('symbol')}"
    assert len(stamps) == len(closes), f"length mismatch in {payload.get('symbol')}"
    check(stamps == sorted(stamps), f"{payload.get('symbol')}: timestamps strictly increasing")
    check(len(set(stamps)) == len(stamps), f"{payload.get('symbol')}: no duplicate stamps")
    import datetime as dt

    return {
        dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y-%m-%d"): float(c)
        for ts, c in zip(stamps, closes)
        if c is not None
    }


def main() -> int:
    canonical = load(os.path.join(DATA, "BOP_KA_daily_2y.json"))
    spark_1y = load(os.path.join(DATA_PSX, "BOP_KA_daily_1y_closes.json"))
    chart_3mo = load(os.path.join(DATA_PSX, "BOP_KA_daily_3mo.json"))
    chart_6mo = load(os.path.join(DATA_PSX, "BOP_KA_daily_6mo_validation.json"))

    print("== canonical 2-year series ==")
    canon = close_map(canonical)
    check(len(canonical["timestamps"]) == 504, f"canonical rows == 504 (got {len(canonical['timestamps'])})")
    import datetime as dt

    span = [
        dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y-%m-%d")
        for ts in (canonical["timestamps"][0], canonical["timestamps"][-1])
    ]
    check(span[0] == "2024-10-07" and span[1] == "2026-10-07",
          f"canonical spans 2024-10-07..2026-10-07 (got {span[0]}..{span[1]})")
    check(canonical["closes"][-1] is None, "canonical final row (2026-10-07) is null")
    for day, value in (
        ("2025-10-07", 34.46), ("2025-10-08", 33.63), ("2025-12-31", 38.56),
        ("2026-01-05", 43.09), ("2026-09-08", 34.63), ("2026-10-05", 28.89),
        ("2026-10-06", 29.72),
    ):
        got = canon.get(day)
        check(got is not None and abs(got - value) < 0.01,
              f"anchor {day}: {value:.2f} (got {got})")
    check(abs(max(canon.values()) - 43.09) < 0.01,
          f"peak close 43.09 (got {max(canon.values()):.2f})")

    print("== 1-year spark closes vs canonical ==")
    spark = close_map(spark_1y)
    overlap = sorted(set(spark) & set(canon))
    mismatches = [(d, spark[d], canon[d]) for d in overlap if abs(spark[d] - canon[d]) > 0.01]
    check(bool(overlap) and not mismatches,
          f"1y/closes agree on all {len(overlap)} overlapping dates"
          + (f" - first mismatch {mismatches[0]}" if mismatches else ""))

    print("== 3-month OHLCV chart ==")
    rows = [
        (ts, chart_3mo["close"][i])
        for i, ts in enumerate(chart_3mo["timestamps"])
        if chart_3mo["close"][i] is not None
    ]
    check(len(chart_3mo["timestamps"]) == 67, f"3mo bars == 67 (got {len(chart_3mo['timestamps'])})")
    import datetime as dt

    bad_bounds = [
        i for i in range(len(chart_3mo["timestamps"]))
        if chart_3mo["close"][i] is not None
        and not (chart_3mo["low"][i] <= chart_3mo["close"][i] <= chart_3mo["high"][i])
    ]
    check(not bad_bounds, f"3mo OHLC bounds hold ({len(bad_bounds)} violations)")
    chart_3mo_map = {
        dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y-%m-%d"): float(c)
        for ts, c in rows
    }
    overlap = sorted(set(chart_3mo_map) & set(canon))
    mismatches = [(d, chart_3mo_map[d], canon[d]) for d in overlap
                  if abs(chart_3mo_map[d] - canon[d]) > 0.01]
    check(bool(overlap) and not mismatches,
          f"3mo closes agree with canonical on all {len(overlap)} overlapping dates"
          + (f" - first mismatch {mismatches[0]}" if mismatches else ""))

    print("== 6-month validation fetch (known chunking noise) ==")
    chart_6 = close_map(chart_6mo)
    overlap = sorted(set(chart_6) & set(canon))
    mismatches = [(d, chart_6[d], canon[d]) for d in overlap if abs(chart_6[d] - canon[d]) > 0.01]
    # Yahoo's chunked 6mo response duplicated one value; allow the known artifact.
    allowed = {("2026-04-07",)}
    real = [m for m in mismatches if (m[0],) not in allowed]
    check(bool(overlap) and not real,
          f"6mo closes agree with canonical on {len(overlap)} overlapping dates "
          f"({len(mismatches)} known chunk artifacts)")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED")
        return 1
    print("all data checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
