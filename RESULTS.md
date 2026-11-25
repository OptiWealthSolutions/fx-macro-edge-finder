# Edge Finder v2.1 — Empirical Validation Results (Anonymized)

> **DISCLAIMER — ANTI-REVERSE-ENGINEERING:** The statistics reported below are extracted from closed Point-in-Time research validations over multi-year G8/G10 FX universes using non-overlapping excess returns (spot + causal carry) and realistic spread assumptions. Exact sample start/end dates, split dates, live timestamps, block-selection files, and calibrated hyperparameters are intentionally omitted. Running `edge_finder_v2/demo.py` executes on stylized synthetic data with generic placeholder transforms and will not reproduce real-world returns.

---

## 1. Multi-Horizon Information Coefficient & Cross-Sectional Validation

Evaluated across the 14 official benchmark FX pairs (non-overlapping Spearman rank IC) and the 8 tradable G8 currencies (daily cross-sectional rank IC with Newey-West HAC standard errors). Window A represents the extended multi-year evaluation sample; Window B represents the stricter recent out-of-sample sub-window.

### A. 21-Day Horizon Evaluation (`h = 21d`)

| Signal Layer | Window A: Pairs IC > 0 | Window A: Mean IC | Window A: Median ICIR | Window B (OOS): Pairs IC > 0 | Window B (OOS): Mean IC | Window B: Median ICIR | Cross-Sectional IC (NW t-stat) |
|---|---:|---:|---:|---:|---:|---:|---|
| **Combined Score (21d model)** | **13 / 14** | **+0.160** | **0.864** | **12 / 14** | **+0.144** | **0.791** | **+0.136 (t = 4.66)** |
| **Strategic Sub-Score (21d model)** | 12 / 14 | +0.098 | 0.335 | 11 / 14 | +0.090 | 0.062 | +0.107 (t = 3.51) |
| **Tactical Sub-Score (21d model)** | 12 / 14 | +0.129 | 0.816 | 10 / 14 | +0.097 | 0.487 | +0.071 (t = 2.63) |
| *Benchmark: Walk-Forward IC (h=21d)* | 9 / 14 | +0.068 | 0.928 | 8 / 14 | +0.015 | 0.399 | +0.040 (t = 1.55) |
| *Benchmark: Walk-Forward Ridge (h=5d)* | 9 / 14 | +0.029 | 0.407 | 8 / 14 | +0.037 | 0.482 | -0.004 (t = -0.17) |

### B. 5-Day Horizon Evaluation (`h = 5d`)

| Signal Layer | Window A: Pairs IC > 0 | Window A: Mean IC | Window A: Median ICIR | Window B (OOS): Pairs IC > 0 | Window B (OOS): Mean IC | Window B: Median ICIR | Cross-Sectional IC (NW t-stat) |
|---|---:|---:|---:|---:|---:|---:|---|
| **Combined Score (5d model)** | **14 / 14** | **+0.083** | **1.217** | **13 / 14** | **+0.070** | **0.814** | **+0.069 (t = 4.51)** |
| **Combined Score (21d model at 5d)** | **14 / 14** | **+0.086** | **1.245** | **13 / 14** | **+0.074** | **0.964** | **+0.075 (t = 4.98)** |
| **Strategic Sub-Score (5d model)** | 12 / 14 | +0.046 | 0.269 | 12 / 14 | +0.049 | 0.287 | +0.053 (t = 3.45) |
| **Tactical Sub-Score (5d model)** | 14 / 14 | +0.068 | 0.908 | 13 / 14 | +0.049 | 0.656 | +0.044 (t = 2.97) |

---

## 2. Pure-PIT Integrity & Grinold Audit (Full 28-Pair G8 Universe)

To verify that performance does not rely on revised macroeconomic data or look-ahead leakage, all revisable national-account series were stripped (`Pure-PIT` reconstruction) and audited across all 28 G8 crosses:

* **Look-Ahead Perturbation Test**: Injecting severe post-cutoff synthetic price/rate shocks (`+35%` FX / `+250 bps` rates) produced a maximum pre-cutoff signal deviation of `<= 2.93e-14` across all blocks and composite outputs (bit-exact causal invariance).
* **Multi-Horizon Grinold Audit (Top-Quartile Gated, Cost- & Carry-Adjusted)**:
  * `h = 1d`: `IC = +0.038`, `IR = 0.217`, `Portfolio Sharpe = 0.838`
  * `h = 5d`: `IC = +0.073`, `IR = 0.166`, `Portfolio Sharpe = 0.850`
  * `h = 21d`: `IC = +0.130` (`85.7%` pairs positive), `IR = 0.145` (`Top-5 IR = 0.330`), `Portfolio Sharpe = 0.850` (threshold-gated: `IR = 0.234`, `Sharpe = 0.968`).
* **Anti-Pattern Discovery (Orthogonalization Proof)**: Isolating legacy technical momentum/trend overlays proved negative out-of-sample IC (`IC = -0.111` / `-0.108`), motivating their removal from active composite weighting and eliminating ~45% signal dilution.

---

## 3. R-Multiple Risk-Adjusted Portfolio Simulation (28 Pairs)

Simulated with causal 5-day Historical VaR stop-losses, sanitized high/low OHLC wicks, causal rate-differential carry, and realistic 1–3 bps round-trip spread tiers:

| Strategy Variant | Trades (N) | Win Rate | Expectancy | Profit Factor | Sharpe | Max Drawdown | SQN | PSR | DSR | Bootstrap p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Pure-PIT Base** | 2,038 | 53.68% | +0.041 R | 1.23 | 0.826 | -18.19 R | 3.12 | 0.966 | 0.563 | 0.0006 |
| **Pure-PIT + Strict Confluence** | 1,373 | 49.02% | +0.049 R | 1.30 | 0.898 | -14.85 R | 3.14 | 0.975 | 0.617 | 0.0008 |
| **Pure-PIT + Confluence + ELSM Filter (All)** | 518 | 50.19% | +0.089 R | 1.56 | 1.070 | -7.93 R | 3.18 | 0.992 | 0.768 | — |
| **Pure-PIT + Confluence + ELSM Filter (Core)** | 835 | 51.50% | +0.084 R | 1.53 | 1.146 | -9.63 R | 3.89 | 0.992 | 0.777 | <0.0001 |

---

## 4. Methodological Caveats & Statistical Governance

* **Multiple-Testing & Design Contamination**: Because architectural choices (such as separating policy rates from inflation pillars in v2.1) were informed by prior empirical diagnostics, deflated Sharpe ratios (`DSR`) and strict forward out-of-sample paper-trading tracking are enforced before allocating live risk capital.
* **Revision Sensitivity**: Stripping revisable macro series (`Pure-PIT`) actually improved cumulative R-multiple expectancy (`+83.68 R` vs. `+73.62 R`), confirming that real-time release discipline outperforms backward-revised macro inputs.
