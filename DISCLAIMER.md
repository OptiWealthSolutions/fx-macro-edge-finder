# Disclaimer & Intellectual Property Notice

## 1. Purpose of This Repository

This repository presents the **conceptual architecture, software engineering standards, Point-in-Time (PIT) causality controls, and empirical validation methodology** behind two quantitative macroeconomic research models (**ELSM** and **Edge Finder v2.1**). It is published solely as a technical portfolio for research and recruitment evaluation.

## 2. Anti-Reverse-Engineering & Redaction Policy

To protect proprietary research edge and prevent unauthorized replication or reverse engineering:
* **No Proprietary Formulas**: Exact nonlinear shock functions, calibrated decay half-lives, composite weighting formulas, shrinkage anchors, covariance risk-cap rules, and production activation thresholds are **omitted or replaced with generic textbook placeholders**.
* **No Production Datasets or Calendars**: No real historical market prices, macroeconomic release archives, broker feeds, or proprietary event taxonomies are included.
* **No Temporal Leakage**: All reported empirical statistics omit calendar start/end dates, split dates, and timestamps.
* **Synthetic Execution Only**: Included Python scripts operate strictly on synthetic stochastic processes (`synthetic_data.py`). Outputs from synthetic runs illustrate pipeline mechanics and causality guarantees—not real-world alpha.

## 3. No Investment Advice

Nothing in this repository, its documentation, or its PDF whitepapers constitutes investment advice, a solicitation, an offer to buy or sell any financial instrument, or a promise of future trading performance. Quantitative strategies carry substantial risk of loss, and historical backtest metrics (even when deflated for multiple testing) do not guarantee future results.

## 4. License & Restrictions

All prose, architectural documentation, and illustrative code in this portfolio are copyright of the author. Unauthorized commercial redistribution, automated scraping for strategy cloning, or representation of the illustrative placeholder code as a live production trading system is prohibited.
