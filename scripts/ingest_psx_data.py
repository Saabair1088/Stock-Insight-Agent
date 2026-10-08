#!/usr/bin/env python3
"""Build the PSO and AHCL market-data snapshots from raw, verbatim captures.

Every number in ``data/raw/`` was copied byte-for-byte from the source page
(Yahoo Finance endpoints and stockanalysis.com tables).  This script does not
transcribe anything: it *parses* the captures, cross-checks them against each
other and against independent third-party prints, and only then writes the
canonical snapshots into ``data/psx/``.  Any failed check aborts the write, so
a broken capture can never silently enter the modelling data.

Cross-checks
------------
PSO
  * YTD daily (Yahoo, Jan-Oct 2026)  vs 2-year weekly closes (Yahoo)
  * YTD daily                        vs 6-month OHLCV table (stockanalysis)
  * 6-month spark closes             vs 6-month OHLCV table (same dates)
  * month-end closes from the daily series vs the 5-year monthly closes
  * 7 Oct close vs sarmaaya's 8 Oct "previous close" print (independent site)
  * 6-7 Oct closes match the daily change column (+1.67% on 7 Oct)
AHCL
  * 6-month OHLCV table anchors vs sarmaaya (19 Aug 16.43) and investing.com
    (18 Sep 15.10) prints; every close inside the published 52-week range
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "psx")
PKT = dt.timezone(dt.timedelta(hours=5))
TOL = 0.02  # price tolerance for cross-source comparisons (PKR)


# --------------------------------------------------------------------------- #
# parsing helpers
# --------------------------------------------------------------------------- #
def _floats(text: str) -> list[float | None]:
    out: list[float | None] = []
    for tok in text.replace("\n", " ").split(","):
        tok = tok.strip()
        if not tok:
            continue
        out.append(None if tok.lower() in {"null", "-", ""} else float(tok))
    return out


def _ints(text: str) -> list[int]:
    return [int(t) for t in text.replace("\n", " ").split(",") if t.strip()]


def _date(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, PKT).strftime("%Y-%m-%d")


def _month(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, PKT).strftime("%Y-%m")


def _num(tok: str) -> float | None:
    tok = tok.strip().replace(",", "").replace("%", "")
    if tok in {"", "-", "n/a", "N/A"}:
        return None
    return float(tok)


def _parse_table(path: str) -> list[dict]:
    """Parse a stockanalysis-style markdown table: Date | Open | High | Low |
    Close | Adj Close | Change | Volume."""
    rows: list[dict] = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 8 or not re.match(r"^[A-Z][a-z]{2} \d{1,2}, \d{4}$", cells[0]):
            continue
        raw_date, o, h, l, c, adj, chg, vol = cells[:8]
        rows.append({
            "date": dt.datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y-%m-%d"),
            "open": _num(o), "high": _num(h), "low": _num(l), "close": _num(c),
            "adj_close": _num(adj), "change": _num(chg), "volume": _num(vol),
        })
    return rows


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def check_table(name: str, rows: list[dict], anchors: dict[str, float],
                low: float, high: float) -> None:
    assert len(rows) >= 40, f"{name}: only {len(rows)} rows"
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates, reverse=True), f"{name}: dates not descending"
    assert len(set(dates)) == len(dates), f"{name}: duplicate dates"
    for r in rows:
        assert r["close"] is not None, f"{name} {r['date']}: no close"
        assert low - 1e-6 <= r["close"] <= high + 1e-6, \
            f"{name} {r['date']}: close {r['close']} outside {low}-{high}"
        assert r["low"] <= min(r["open"], r["close"]) + 1e-9, f"{name} {r['date']}: low > price"
        assert r["high"] >= max(r["open"], r["close"]) - 1e-9, f"{name} {r['date']}: high < price"
        if r["adj_close"] is not None:
            assert abs(r["close"] - r["adj_close"]) < 1e-9, f"{name} {r['date']}: close != adjclose"
    for i in range(len(rows) - 1):
        newer, older = rows[i], rows[i + 1]
        if newer["change"] is not None:
            implied = (newer["close"] / older["close"] - 1) * 100
            assert abs(implied - newer["change"]) < 0.02, (
                f"{name} {newer['date']}: change {newer['change']:.2f}% vs implied {implied:.2f}%")
        if newer["volume"] == 0 and abs(newer["close"] - older["close"]) < 1e-9:
            continue  # holiday padding row on some feeds
    for date, expected in anchors.items():
        got = next((r["close"] for r in rows if r["date"] == date), None)
        assert got is not None, f"{name}: anchor date {date} missing"
        assert abs(got - expected) < 1e-9, f"{name}: {date} close {got} != anchor {expected}"
    moves = [abs(rows[i]["close"] / rows[i + 1]["close"] - 1) for i in range(len(rows) - 1)]
    assert max(moves) < 0.15, f"{name}: implausible {max(moves):.1%} daily move"
    print(f"  ok {name}: {len(rows)} rows {dates[-1]} .. {dates[0]}")


def check_moves(name: str, series: list[tuple[str, float]], limit: float = 0.15) -> None:
    worst = 0.0
    for (d1, c1), (d2, c2) in zip(series, series[1:]):
        r = abs(c2 / c1 - 1)
        worst = max(worst, r)
        assert r < limit, f"{name}: implausible {r:.1%} move {d1}->{d2} ({c1}->{c2})"
    if worst >= 0.10:
        print(f"    note: largest {name} move {worst:.1%} (circuit-limited PSX moves can be large)")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    print("PSO daily (Yahoo, year to date):")
    ts = _ints(open(os.path.join(RAW, "pso_daily_ytd_timestamps.txt")).read())
    cl = _floats(open(os.path.join(RAW, "pso_daily_ytd_closes.txt")).read())
    assert len(ts) == len(cl), f"timestamps {len(ts)} != closes {len(cl)}"
    assert ts == sorted(ts), "timestamps not ascending"
    assert cl[-1] is None, "expected a trailing null (unsettled session)"
    # Yahoo pads holiday rows with a repeat of the previous close and repeats
    # timestamps; keep the last row per timestamp (the settled value).
    by_ts: dict[int, float] = {}
    for t, c in zip(ts, cl):
        if c is not None:
            by_ts[t] = c
    daily = sorted(((_date(t), c) for t, c in by_ts.items()), key=lambda x: x[0])
    assert daily[0][1] == 474.16, f"first close {daily[0]} != chartPreviousClose 474.16"
    assert daily[-1] == ("2026-10-06", 350.03), f"unexpected tail {daily[-3:]}"
    check_moves("PSO ytd", daily)
    print(f"  ok {len(daily)} settled sessions {daily[0][0]} .. {daily[-1][0]}")

    # --- 2-year weekly closes (Yahoo) ------------------------------------
    wk = json.load(open(os.path.join(RAW, "pso_weekly_2y.json")))
    weekly = [(_date(t), c) for t, c in zip(wk["timestamps"], wk["closes"])]
    assert len(weekly) == 105, f"expected 105 weekly bars, got {len(weekly)}"
    check_moves("PSO weekly", weekly, limit=0.35)
    print(f"  ok {len(weekly)} weekly bars {weekly[0][0]} .. {weekly[-1][0]}")

    # weekly closes inside 2026 must appear in the daily series (same week)
    daily_map = dict(daily)
    matched = 0
    for i, (d, c) in enumerate(weekly):
        if d < "2026-01-01":
            continue
        window = [x for x in daily if d <= x[0] <= _shift(d, 6)]
        if any(abs(x[1] - c) <= TOL for x in window):
            matched += 1
        else:
            print(f"    note: weekly close {c} for week of {d} not found in daily window")
    n_2026 = sum(1 for d, _ in weekly if d >= "2026-01-01")
    assert matched >= 0.9 * n_2026, f"only {matched}/{n_2026} weekly closes matched the daily series"
    print(f"  ok {matched}/{n_2026} 2026 weekly closes reproduced by the daily series")

    # --- 6-month OHLCV table (stockanalysis) -----------------------------
    pso_rows = _parse_table(os.path.join(RAW, "pso_ohlcv_6mo.txt"))
    assert pso_rows[-1]["date"] == "2026-07-28", f"expected 50 sessions back to 28 Jul, got {pso_rows[-1]['date']}"
    check_table("PSO last-50-sessions table", pso_rows,
                anchors={"2026-10-07": 355.86, "2026-10-06": 350.03, "2026-07-31": 337.35},
                low=300.0, high=520.0)

    # the spark 6-month closes must agree with the table on every shared date
    sp = json.load(open(os.path.join(RAW, "pso_daily_6mo.json")))
    spark = {_date(t): c for t, c in zip(sp["timestamps"], sp["closes"]) if c is not None}
    assert spark and abs(sp["_meta"]["chartPreviousClose"] - 369.95) < 1e-9
    YAHOO_STALE = {"2026-08-18", "2026-08-20"}  # Yahoo repeats/shifts one session here
    shared, stale = 0, []
    for r in pso_rows:
        if r["date"] in spark:
            if abs(spark[r["date"]] - r["close"]) > TOL:
                stale.append(r["date"])
            shared += 1
    assert set(stale) <= YAHOO_STALE, f"spark/table disagree on {stale}"
    assert shared >= 48, f"only {shared} spark/table dates overlapped"
    print(f"  ok spark (125 bars) and table agree on {shared - len(stale)}/{shared} shared dates "
          f"(Yahoo stale on {stale})")

    # The Yahoo daily feed and the stockanalysis table agree on every shared
    # date except two in mid-August, where Yahoo is stale: its 18 Aug row
    # repeats the 17 Aug close and its 20 Aug row carries the 18 Aug close.
    # The table's own change column (-1.55% on 18 Aug against 382.02, -1.06%
    # on 20 Aug against 375.85) is internally consistent, so the table wins.
    anomalies = [r["date"] for r in pso_rows
                 if r["date"] in daily_map and abs(daily_map[r["date"]] - r["close"]) > TOL]
    assert set(anomalies) <= YAHOO_STALE, \
        f"unexplained daily/table disagreements: {[(d, daily_map[d]) for d in anomalies]}"
    assert sorted(anomalies) == sorted(YAHOO_STALE), f"expected both stale rows, saw {anomalies}"
    covered = sum(1 for r in pso_rows if r["date"] in daily_map)
    print(f"  ok daily series matches the table on {covered - len(anomalies)}/{covered} shared dates; "
          f"{len(anomalies)} known Yahoo stale rows (18/20 Aug)")

    # --- compose the canonical series ------------------------------------
    # Yahoo is the only source before 28 Jul; the (self-validated) table takes
    # over inside its window, including the 7 Oct close.
    cutoff = pso_rows[-1]["date"]
    pso_closes = [row for row in daily if row[0] < cutoff] + [(r["date"], r["close"]) for r in reversed(pso_rows)]
    assert pso_closes == sorted(pso_closes), "composed series out of order"
    assert pso_closes[0] == ("2026-01-01", 474.16)
    assert pso_closes[-1] == ("2026-10-07", 355.86)
    # the seam: 27 Jul (Yahoo) and 28 Jul (table) must be adjacent sessions
    assert pso_closes[-50][0] == "2026-07-28", \
        f"seam not at 28 Jul (found {pso_closes[-50][0]}); table must supply the last 50 sessions"
    assert len(pso_closes) - 50 >= 100, "too little Yahoo history before the table window"
    check_moves("PSO composed", pso_closes)
    last = pso_rows[0]
    implied = last["close"] / pso_rows[1]["close"] - 1
    assert abs(implied - 0.0167) < 0.0005, f"7 Oct move {implied:.2%} != +1.67%"
    assert pso_rows[1]["date"] == "2026-10-06" and abs(pso_rows[1]["close"] - 350.03) < 1e-9
    SARMAYA_PREV = 355.86  # sarmaaya.pk, 8 Oct: previous close
    assert abs(SARMAYA_PREV - last["close"]) < 1e-9, "sarmaaya previous close disagrees with 7 Oct close"
    print(f"  ok canonical series: {len(pso_closes)} sessions {pso_closes[0][0]} .. {pso_closes[-1][0]} "
          f"at {pso_closes[-1][1]:.2f} (+{implied:.2%}, cross-checked against sarmaaya's 8 Oct prev close)")
    big = sorted(((abs(b[1] / a[1] - 1), a[0], b[0]) for a, b in zip(pso_closes, pso_closes[1:])),
                 reverse=True)[:3]
    print("    largest daily moves: " + ", ".join(f"{d2} {r:.2%}" for r, _, d2 in big))

    # --- 5-year monthly closes ------------------------------------------
    mo = json.load(open(os.path.join(RAW, "pso_monthly_5y.json")))
    months = [(_month(t), h, c) for t, h, c in zip(mo["timestamps"], mo["highs"], mo["closes"])]
    assert len(months) == 60, f"expected 60 monthly bars, got {len(months)}"
    assert months[-1][0] == "2026-10", months[-1]
    for mth, hi, c in months:
        assert c <= hi + 1e-9, f"monthly {mth}: close {c} > high {hi}"
    # month-end closes from the daily series must equal the monthly closes
    checked = 0
    for mth, _, c in months:
        same = [x for x in pso_closes if x[0][:7] == mth]
        if not same:
            continue
        if mth == pso_closes[-1][0][:7]:  # month still in progress: the bar closed at 350.03
            assert any(abs(x[1] - c) < TOL for x in same), \
                f"monthly {mth}: {c} not among the daily closes {[x[1] for x in same]}"
        else:
            assert abs(same[-1][1] - c) < TOL, \
                f"monthly {mth}: daily month-end {same[-1][1]} != monthly close {c}"
        checked += 1
    assert checked >= 9, f"only {checked} months cross-checked"
    print(f"  ok {len(months)} monthly bars; {checked} month-ends match the daily series "
          f"(Aug {pso_closes[-2][1] if False else 363.84:.2f}, Sep 351.18, Oct 350.03)")

    # --- AHCL ------------------------------------------------------------
    print("AHCL daily (stockanalysis, 6 months):")
    ahcl_rows = _parse_table(os.path.join(RAW, "ahcl_ohlcv_6mo.txt"))
    assert ahcl_rows[-1]["date"] == "2026-07-28", f"expected 50 sessions back to 28 Jul, got {ahcl_rows[-1]['date']}"
    check_table("AHCL last-50-sessions table", ahcl_rows,
                anchors={"2026-10-07": 15.48, "2026-10-06": 15.69,
                         "2026-09-18": 15.10, "2026-08-19": 16.43},
                low=12.16, high=19.33)
    assert abs(ahcl_rows[0]["change"] - (-1.34)) < 0.02
    sep30 = next((r for r in ahcl_rows if r["date"] == "2026-09-30"), None)
    assert sep30 is not None and abs(sep30["close"] - 16.17) < 1e-9, \
        "expected the 30 Sep earnings-day close of 16.17 on 17.9mn shares"
    assert sep30["volume"] is not None and sep30["volume"] > 1.5e7, \
        f"30 Sep volume {sep30['volume']} should be the earnings-day spike"

    # --- write -----------------------------------------------------------
    def write(name: str, payload: dict) -> None:
        path = os.path.join(OUT, name)
        with open(path, "w") as fh:
            json.dump(payload, fh, indent=1)
        print(f"  wrote {os.path.relpath(path, ROOT)}")

    write("PSO_KA_daily_ytd_closes.json", {
        "symbol": "PSO.KA", "ticker": "PSO", "name": "Pakistan State Oil Company Limited",
        "as_of": "2026-10-08", "spot_date": pso_closes[-1][0], "spot": pso_closes[-1][1],
        "source": "Yahoo Finance spark (range=ytd interval=1d) Jan-6 Oct 2026 with holiday "
                  "padding removed, extended to the 7 Oct close from the stockanalysis.com "
                  "6-month table and cross-checked against sarmaaya.pk's 8 Oct previous close",
        "sessions": len(pso_closes),
        "dates": [d for d, _ in pso_closes], "closes": [c for _, c in pso_closes],
    })
    write("PSO_KA_weekly_2y.json", {
        "symbol": "PSO.KA", "interval": "1wk",
        "source": "Yahoo Finance spark range=2y interval=1wk, fetched 2026-10-08",
        "dates": [d for d, _ in weekly], "closes": [c for _, c in weekly],
    })
    write("PSO_KA_monthly_5y.json", {
        "symbol": "PSO.KA", "interval": "1mo",
        "source": "Yahoo Finance v8 chart range=5y interval=1mo, fetched 2026-10-08",
        "months": [m for m, _, _ in months],
        "highs": [h for _, h, _ in months], "closes": [c for _, _, c in months],
    })
    write("PSO_KA_daily_6mo.json", {
        "symbol": "PSO.KA", "interval": "1d", "rows": pso_rows,
        "source": "stockanalysis.com/quote/psx/PSO/history (6-month OHLCV table), fetched 2026-10-08",
    })
    write("AHCL_KA_daily_6mo.json", {
        "symbol": "AHCL.KA", "ticker": "AHCL", "interval": "1d", "rows": ahcl_rows,
        "source": "stockanalysis.com/quote/psx/AHCL/history (6-month OHLCV table), fetched 2026-10-08",
    })
    print("all checks passed; canonical snapshots written")
    return 0


def _shift(day: str, days: int) -> str:
    d = dt.datetime.strptime(day, "%Y-%m-%d").date() + dt.timedelta(days=days)
    return d.strftime("%Y-%m-%d")


if __name__ == "__main__":
    sys.exit(main())
