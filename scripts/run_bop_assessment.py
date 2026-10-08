#!/usr/bin/env python3
"""End-to-end BOP (PSX) assessment: data -> forecast -> committee -> reports.

Default path (stock Python 3.11+, no third-party packages)::

    python3 scripts/run_bop_assessment.py

That regenerates ``reports/BOP_research_2026-10-07.{md,html}``,
``reports/BOP_forecast_2026-10-07.json`` and the two SVG charts, bit-for-bit
reproducible (forecast seed 20261007).

To also execute the *vendored TradingAgents graph* -- the real LangGraph
pipeline, including the analysts' tool loops -- add ``--framework``.  With no
LLM API key the graph runs with the deterministic stand-in model
(:class:`psx.tradingagents_bridge.OfflineLLM`); with a key it runs live::

    python3 scripts/run_bop_assessment.py --framework            # offline graph run
    OPENAI_API_KEY=... python3 scripts/run_bop_assessment.py --framework --mode live

Both framework modes need the framework's dependencies, which live in the
repo's ``.venv`` (``python3 -m venv .venv && .venv/bin/pip install -e ./TradingAgents``);
the script re-executes itself under that interpreter automatically.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

AS_OF_DATE = "2026-10-07"
HORIZON_END = "2026-11-06"
VENV_PYTHON = os.path.join(REPO_ROOT, ".venv", "bin", "python")


def _reexec_in_venv_if_needed(argv: list[str]) -> None:
    """Framework modes need the .venv interpreter; hop into it once."""
    if os.environ.get("BOP_REEXEC") == "1":
        return
    if not os.path.exists(VENV_PYTHON):
        return
    try:
        import tradingagents  # noqa: F401

        return  # already running under an interpreter that has the framework
    except Exception:  # noqa: BLE001
        pass
    env = {**os.environ, "BOP_REEXEC": "1"}
    os.execve(VENV_PYTHON, [VENV_PYTHON, os.path.abspath(__file__), *argv], env)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BOP (PSX) research + 30-day forecast")
    parser.add_argument("--framework", action="store_true",
                        help="also run the vendored TradingAgents LangGraph pipeline")
    parser.add_argument("--mode", choices=("auto", "offline", "live"), default="auto",
                        help="framework LLM mode (auto: live when an API key is present)")
    parser.add_argument("--seed", type=int, default=None, help="override the forecast seed")
    parser.add_argument("--paths", type=int, default=None, help="override the Monte-Carlo path count")
    parser.add_argument("--outdir", default=os.path.join(REPO_ROOT, "reports"))
    args = parser.parse_args(argv)

    if args.framework:
        _reexec_in_venv_if_needed(argv if argv is not None else sys.argv[1:])

    from psx import agents, data, forecast as fc, report, research as rs

    series = data.load_series(prefer_live=False)
    ohlcv = data.load_ohlcv_3mo()

    cfg = fc.ForecastConfig()
    if args.seed is not None:
        cfg.seed = args.seed
    if args.paths is not None:
        cfg.paths = args.paths
    f = fc.forecast(series.closes, as_of=series.last_date, horizon_end=HORIZON_END, cfg=cfg)
    committee = agents.run_committee(series, ohlcv, f)
    paths = report.write_outputs(series, ohlcv, f, committee, outdir=args.outdir)

    print(f"BOP (PSX) assessment - as of {rs.AS_OF} (last close {series.spot:.2f}, "
          f"{series.last_date})")
    print(f"  forecast to {HORIZON_END} ({f.horizon_sessions} sessions): "
          f"P(up) {f.prob_up:.0%} | median {f.quantiles['p50']:.2f} | "
          f"EV {f.expected_price:.2f} ({f.expected_return:+.1%}) | "
          f"80% band {f.quantiles['p10']:.2f}-{f.quantiles['p90']:.2f}")
    print(f"  committee: {committee.final_rating} / {committee.action} | "
          f"scores {committee.scores} | size {committee.trade_params.get('size_pct_final')}% | "
          f"stop {committee.trade_params.get('stop')}")
    for label, path in paths.items():
        print(f"  wrote {label}: {os.path.relpath(path, REPO_ROOT)}")

    if args.framework:
        from psx import tradingagents_bridge as tb

        out = tb.run_framework(committee, trade_date=AS_OF_DATE, mode=args.mode)
        print(f"  TradingAgents graph ({out['mode']}): rating {out['rating']} -> "
              f"{os.path.relpath(out['report_path'], REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
