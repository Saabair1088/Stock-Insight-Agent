#!/usr/bin/env python3
"""End-to-end assessment for a PSX name: data -> forecast -> committee -> reports.

Profile-driven counterpart of ``run_bop_assessment.py``.  The Bank of Punjab has
its own hand-written committee and keeps that exact path; every other name runs
through :mod:`psx.analysts` + :mod:`psx.writer` on the evidence in
:mod:`psx.profiles`.

Stock Python (no third-party packages)::

    python3 scripts/run_psx_assessment.py --symbol PSO
    python3 scripts/run_psx_assessment.py --symbol AHCL

Writes ``reports/{TICKER}_research_{as_of}.{md,html}``,
``reports/{TICKER}_forecast_{as_of}.json`` and two SVG charts.

Add ``--framework`` to also execute the vendored TradingAgents LangGraph
pipeline on the same name (needs the repo ``.venv``; the script re-executes
itself under that interpreter)::

    python3 scripts/run_psx_assessment.py --symbol PSO --framework --mode offline
"""

from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

VENV_PYTHON = os.path.join(REPO_ROOT, ".venv", "bin", "python")
REEXEC_ENV = "PSX_REEXEC"


def _reexec_in_venv_if_needed(argv: list[str]) -> None:
    """Framework modes need the .venv interpreter; hop into it once."""
    if os.environ.get(REEXEC_ENV) == "1":
        return
    if not os.path.exists(VENV_PYTHON):
        return
    try:
        import tradingagents  # noqa: F401

        return
    except Exception:  # noqa: BLE001
        pass
    env = {**os.environ, REEXEC_ENV: "1"}
    os.execve(VENV_PYTHON, [VENV_PYTHON, os.path.abspath(__file__), *argv], env)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PSX research + 30-day movement forecast")
    parser.add_argument("--symbol", required=True, help="PSX ticker, e.g. PSO or AHCL")
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

    from psx import analysts, forecast as fc, market_data, profiles, writer

    profile = profiles.get(args.symbol)
    if profile.symbol == "BOP.KA":
        print("BOP keeps its original runner: python3 scripts/run_bop_assessment.py")
        return 1

    series = market_data.load_series(profile)
    ohlcv = market_data.load_ohlcv(profile)
    cfg = fc.ForecastConfig(
        horizon_sessions=profile.horizon_sessions,
        seed=args.seed if args.seed is not None else 20261007,
        regime_weights=dict(profile.regime_weights) or fc.ForecastConfig().regime_weights,
    )
    if args.paths:
        cfg.paths = args.paths
    long_ma, _ = analysts.long_run_reference(profile)
    if long_ma:
        cfg.ma_anchor = long_ma
    if profile.cash_events:
        cfg.cash_drops = tuple((e["session"], e["amount"]) for e in profile.cash_events)
    thresholds = {t["label"]: t["price"] for t in profile.thresholds}
    f = fc.forecast(series.closes, as_of=profile.as_of, horizon_end=profile.horizon_end,
                    cfg=cfg, thresholds=thresholds)
    committee = analysts.run_committee(profile, series, ohlcv, f)
    analytics = analysts.compute_analytics(profile, series, ohlcv)
    scenarios = fc.scenarios(f.spot, analysts.scenario_spec_from_model(profile, f))
    robustness = (analysts.model_robustness(series.closes, f, cfg.seed)
                  if len(series.closes) < 120 else None)

    framework_dir = None
    if args.framework:
        from psx import tradingagents_bridge as bridge

        result = bridge.run_framework(
            committee, ticker=profile.symbol, trade_date=profile.as_of, mode=args.mode,
            config=bridge.build_config(),
        )
        framework_dir = os.path.relpath(result["run_dir"], REPO_ROOT)
        print(f"framework: {result['mode']} run -> {framework_dir} "
              f"(final rating {result.get('rating')})")

    paths = writer.write_outputs(profile, series, ohlcv, f, committee, analytics, scenarios,
                                 robustness, framework_dir, outdir=args.outdir)

    print(f"{profile.ticker} | {profile.name}")
    print(f"  spot PKR {f.spot:,.2f} ({profile.spot_date}) | P(price up) {f.prob_up:.1%} | "
          f"P(total return > 0) {f.prob_up_total_return:.1%} | median PKR "
          f"{f.quantiles['p50']:,.2f} | p10-p90 "
          f"{f.quantiles['p10']:,.2f}-{f.quantiles['p90']:,.2f}"
          + (f" | cash in window PKR {f.dividend_total:,.2f}" if f.dividend_total else ""))
    print(f"  committee {committee.scores} -> {committee.final_rating} / {committee.action} | "
          f"size {committee.trade_params['size_pct_final']:.1f}% | stop "
          f"{committee.trade_params['stop']:,.2f} | targets {committee.trade_params['target_1']:,.2f} / "
          f"{committee.trade_params['target_2']:,.2f}")
    for key, path in paths.items():
        print(f"  wrote {os.path.relpath(path, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
