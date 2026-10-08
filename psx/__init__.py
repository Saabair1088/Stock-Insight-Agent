"""PSX (Pakistan Stock Exchange) research + forecasting toolkit.

This package layers a Pakistan-market workflow on top of the vendored
``TradingAgents`` multi-agent framework (``../TradingAgents``):

* :mod:`psx.data`        - cached, validated PSX price data (no third-party deps)
* :mod:`psx.indicators`  - pure-stdlib technical / risk indicators
* :mod:`psx.forecast`    - 30-calendar-day Monte-Carlo movement forecast
* :mod:`psx.research`    - curated, source-attributed evidence base
* :mod:`psx.agents`      - the TradingAgents committee (analysts, bull/bear
                           debate, research manager, trader, risk team, PM)
                           reproduced deterministically for key-less runs
* :mod:`psx.report`      - markdown / HTML report rendering
* :mod:`psx.tradingagents_bridge` - wiring for the real TradingAgents graph
                           (config, PSX data vendor shim, offline LLM client)

Everything in the forecasting path runs on the Python standard library so a
report can be regenerated on any machine with stock Python 3.11+.
"""

from __future__ import annotations

__all__ = ["data", "indicators", "forecast", "research", "agents", "report"]

__version__ = "1.0.0"
