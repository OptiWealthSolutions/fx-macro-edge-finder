# FX Edge Finder v2.1 — Multi-Horizon Cross-Sectional Macro Engine

> **ANTI-REVERSE-ENGINEERING NOTICE:** This repository showcases the conceptual architecture, Point-in-Time (PIT) governance, walk-forward shrinkage framework, and anti-overfitting statistical validation of Edge Finder v2.1. Exact pillar definitions, lag schedules, shrinkage priors, risk-budgeting caps, nonlinear conviction mappings, and production block selections are intentionally redacted. Executable scripts run strictly on stylized synthetic multi-currency factor panels using generic textbook placeholders. See [DISCLAIMER.md](DISCLAIMER.md).

---

## 1. Conceptual & Macroeconomic Rationale

Systematic discretionary and quantitative FX models frequently fail out-of-sample for three structural reasons:
1. **Factor Double-Counting & Collinearity**: Mixing nominal policy rates, Taylor-rule spreads, inflation prints, and macro composite scores into an unconstrained regression creates severe multicollinearity, causing in-sample weight instability.
2. **Revision & Publication Look-Ahead Bias**: National-account series (GDP, unemployment, CPI) are published with substantial reporting lags and revised retroactively. Treating final-revised series as contemporaneous introduces phantom predictability.
3. **Unconstrained Optimization Overfits Noise**: Standard OLS or unconstrained factor timing overfits transient historical correlations (e.g., flipping signs on value or carry factors across regimes).

**Edge Finder v2.1** resolves these failure modes through a disciplined, protocol-driven architecture:

---

## 2. Architectural Design

```text
  Synthetic Multi-Currency Macro & Market Panel (G10 Estimation -> G8 Tradable)
        │
        ▼
  [1] Pure-PIT Data Alignment & Lag Enforcement
        │  - Strict separation: non-revisable release prints vs. lagged macro series
        │  - Cross-sectional standardization across available currencies
        ▼
  [2] Orthogonal Pillar Construction (Strategic vs. Tactical)
        │  - Strategic Pillars: Monetary Policy, Real Value, Macro Pillars (Inf/Growth/Labor)
        │  - Tactical Pillars: Rate-FX Gap, Positioning, Calendar Seasonality, Risk Fragility
        │  - Strict anti-double-counting separation (v2.0 -> v2.1 refactor)
        ▼
  [3] Walk-Forward Shrinkage & Risk-Budgeted Aggregation
        │  - Expanding training window with mandatory embargo before evaluation step
        │  - Non-overlapping multi-step excess return target (spot + lagged carry)
        │  - L2 shrinkage toward economic prior + non-negativity + covariance risk caps
        ▼
  [4] Multi-Horizon Signal Decomposition & Conviction Scaling
        │  - Currency-level expected excess return -> Pair differential (Base - Quote)
        │  - Volatility-normalized conviction & strategic/tactical agreement flag
        ▼
  [5] Protocol Verification Suite
        │  - Non-overlapping Spearman IC & ICIR per pair
        │  - Daily cross-sectional rank IC with Newey-West HAC t-statistics
        │  - Circular-shift placebo permutation test (null hypothesis rejection)
```

---

## 3. Key Methodological Innovations (v2.0 → v2.1)

* **Decoupling Monetary Policy from Inflation**: In v2.1, policy-rate expectations and inflation pressure are isolated into separate pillars rather than merged inside a composite Taylor gap, eliminating hidden collinearity while preserving both signals under independent risk budgets.
* **Cross-Sectional Common Scale vs. Rolling Time-Series Z-Scores**: Currency fundamentals are evaluated relative to the G10 cross-section using robust scale anchors rather than arbitrary rolling time-series windows on non-stationary levels.
* **Pure-PIT vs. Revised Series Audit**: An automated audit mode strips out revisable national-account series to measure the exact causal alpha attributable solely to real-time release prints and market prices.
* **Circular Placebo Testing**: Because cross-sectional FX signals exhibit autocorrelation, standard t-tests overstate significance. Circularly shifting each pair's signal across random phase offsets tests whether observed IC exceeds structured random alignment.

---

## 4. Documentation & Empirical Results

* **Technical Whitepaper (PDF)**: [docs/Edge_Finder_v2_1_Technical_Documentation.pdf](docs/Edge_Finder_v2_1_Technical_Documentation.pdf)
* **Anonymized Empirical Validation (IS / OOS / R-Multiple / DSR)**: [RESULTS.md](RESULTS.md)
* **IP & Anti-Reverse-Engineering Terms**: [DISCLAIMER.md](DISCLAIMER.md)

---

## 5. Quickstart (Synthetic Environment)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m edge_finder_v2.demo
pytest -v
```
