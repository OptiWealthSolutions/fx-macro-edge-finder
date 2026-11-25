"""
Edge Finder v2.1 — Sanitized Demonstrative Architecture.

Illustrates:
  - Cross-sectional normalization across G10 currencies
  - Separation of Strategic vs. Tactical macro pillars
  - Walk-forward Ridge shrinkage with embargo and weight constraints
  - Non-overlapping Spearman IC, Newey-West HAC t-stat, and circular placebo tests

[REDACTED / SIMPLIFIED]:
  Proprietary pillar formulas, lag tables, shrinkage anchors, risk-budgeting caps,
  conviction scaling constants, and production block selections are omitted.
"""
from __future__ import annotations

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd

from .synthetic_data import (
    ALL_PAIRS,
    EST_CCYS,
    OFFICIAL_PAIRS,
    TRADE_CCYS,
    SyntheticFXPanel,
)


@dataclass(frozen=True)
class EdgeFinderConfig:
    """Generic placeholder configuration for the Edge Finder v2.1 demo pipeline."""

    horizon_steps: int = 20
    embargo_steps: int = 20
    rebalance_step: int = 20
    warmup_steps: int = 300
    min_train_obs: int = 15
    xs_clip: float = 3.0
    xs_min_currencies: int = 5
    ridge_reg_strength: float = 100.0
    prior_weight: float = 0.04
    max_block_share: float = 0.35
    vol_halflife: int = 20
    n_placebo_draws: int = 100
    seed: int = 101


def xs_zscore(df: pd.DataFrame, clip: float = 3.0, min_ccy: int = 5) -> pd.DataFrame:
    """Cross-sectional z-score across currencies per step, clipped to [-clip, +clip]."""
    n_valid = df.notna().sum(axis=1)
    z = df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0.0, np.nan), axis=0)
    return z.clip(-clip, clip).where(n_valid >= min_ccy, np.nan)


def _walk_forward_ridge_weights(
    blocks: dict[str, pd.DataFrame],
    target_ccy: pd.DataFrame,
    cfg: EdgeFinderConfig,
) -> pd.DataFrame:
    """
    [SIMPLIFIED WALK-FORWARD SKELETON]:
    Expanding-window Ridge regression shrunk toward a uniform positive prior,
    with strict embargo (`embargo_steps`) between training targets and evaluation step.
    """
    names = list(blocks.keys())
    n_blocks = len(names)
    idx = target_ccy.index
    eval_points = np.arange(cfg.warmup_steps, len(idx), cfg.rebalance_step)

    # Stack normalized block matrices (T x C x K)
    stacked = np.stack([blocks[k][list(EST_CCYS)].to_numpy(dtype=float) for k in names], axis=-1)
    y_mat = target_ccy[list(EST_CCYS)].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        y_xs = y_mat - np.nanmean(y_mat, axis=1, keepdims=True)

    weight_rows = []
    weight_steps = []

    for t_eval in eval_points:
        train_cutoff = t_eval - cfg.embargo_steps
        if train_cutoff <= 40:
            continue
        sample_steps = np.arange(20, train_cutoff, cfg.horizon_steps)
        X_list, y_list = [], []
        for s in sample_steps:
            xs = stacked[s]
            ys = y_xs[s]
            valid = np.all(np.isfinite(xs), axis=1) & np.isfinite(ys)
            if valid.sum() >= cfg.xs_min_currencies:
                X_list.append(xs[valid])
                y_list.append(ys[valid])

        if len(X_list) < cfg.min_train_obs:
            beta = np.full(n_blocks, 1.0 / n_blocks, dtype=float)
        else:
            X = np.vstack(X_list)
            y = np.concatenate(y_list)
            # Generic textbook Ridge shrunk toward uniform positive prior
            prior = np.full(n_blocks, cfg.prior_weight * max(float(np.std(y)), 1e-4))
            lam = cfg.ridge_reg_strength
            xtx = X.T @ X + lam * np.eye(n_blocks)
            xty = X.T @ y + lam * prior
            beta = np.linalg.solve(xtx, xty)
            beta = np.clip(beta, 0.0, None)
            if beta.sum() > 0:
                beta = beta / beta.sum()
                beta = np.minimum(beta, cfg.max_block_share)
                beta = beta / beta.sum()
            else:
                beta = np.full(n_blocks, 1.0 / n_blocks, dtype=float)

        weight_rows.append(beta)
        weight_steps.append(int(idx[t_eval]))

    if not weight_rows:
        w_df = pd.DataFrame(
            np.full((len(idx), n_blocks), 1.0 / n_blocks),
            index=idx,
            columns=names,
        )
    else:
        w_sparse = pd.DataFrame(weight_rows, index=weight_steps, columns=names)
        # Fill pre-warmup steps causally with uniform prior (never bfill from future fit)
        w_df = w_sparse.reindex(idx).ffill().fillna(1.0 / n_blocks)
    return w_df


def newey_west_tstat(series: pd.Series, lags: int) -> float:
    """Newey-West HAC t-statistic for autocorrelated daily cross-sectional IC."""
    x = series.dropna().to_numpy(dtype=float)
    n = len(x)
    if n < 30:
        return np.nan
    e = x - x.mean()
    gam = np.array([float(np.sum(e[k:] * e[: n - k]) / n) for k in range(lags + 1)])
    bartlett = 1.0 - np.arange(lags + 1) / (lags + 1)
    var = gam[0] + 2.0 * (bartlett[1:] * gam[1:]).sum()
    return float(x.mean() / np.sqrt(var / n)) if var > 0 else np.nan


def cross_sectional_ic(sig_ccy: pd.DataFrame, fwd_ccy: pd.DataFrame, horizon: int) -> dict[str, float]:
    """Daily cross-sectional Spearman rank IC across tradable currencies."""
    s, f = sig_ccy[list(TRADE_CCYS)], fwd_ccy[list(TRADE_CCYS)]
    mask = s.notna() & f.notna()
    ra = s.where(mask).rank(axis=1)
    rb = f.where(mask).rank(axis=1)
    ra = ra.sub(ra.mean(axis=1), axis=0)
    rb = rb.sub(rb.mean(axis=1), axis=0)
    denom = np.sqrt((ra ** 2).sum(axis=1) * (rb ** 2).sum(axis=1))
    ic_daily = ((ra * rb).sum(axis=1) / denom.where(denom > 0))[mask.sum(axis=1) >= 5].dropna()
    return {
        "xs_ic": float(ic_daily.mean()),
        "nw_t": newey_west_tstat(ic_daily, lags=max(horizon - 1, 1)),
    }


def nonoverlap_pair_ic(sig_pair: pd.DataFrame, fwd_pair: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Non-overlapping Spearman rank IC per official pair."""
    rows = []
    for pair in OFFICIAL_PAIRS:
        s = sig_pair[pair].iloc[::horizon]
        r = fwd_pair[pair].iloc[::horizon]
        valid = s.notna() & r.notna()
        s_v, r_v = s[valid], r[valid]
        n = len(s_v)
        if n < 12:
            rows.append({"pair": pair, "IC": np.nan, "t_stat": np.nan, "N": n})
            continue
        ic = float(s_v.rank().corr(r_v.rank()))
        t_val = float(ic * np.sqrt(n - 2) / np.sqrt(max(1.0 - ic ** 2, 1e-12)))
        rows.append({"pair": pair, "IC": ic, "t_stat": t_val, "N": n})
    return pd.DataFrame(rows)


def circular_placebo_test(
    sig_pair: pd.DataFrame,
    fwd_pair: pd.DataFrame,
    horizon: int,
    n_draws: int = 100,
    seed: int = 101,
) -> dict[str, float]:
    """Circular-shift placebo permutation test preserving signal autocorrelation."""
    rng = np.random.default_rng(seed)
    pairs = list(OFFICIAL_PAIRS.keys())
    S = sig_pair[pairs].to_numpy(dtype=float)
    F = fwd_pair[pairs].to_numpy(dtype=float)
    keep = np.arange(0, len(S), horizon)
    Fk = pd.DataFrame(F[keep]).rank()

    def _mean_ic(S_mat: np.ndarray) -> float:
        Sk = pd.DataFrame(S_mat[keep]).rank()
        mask = Sk.notna() & Fk.notna()
        a, b = Sk.where(mask), Fk.where(mask)
        a = a - a.mean()
        b = b - b.mean()
        den = np.sqrt((a ** 2).sum() * (b ** 2).sum())
        return float(((a * b).sum() / den.where(den > 0)).mean())

    real_ic = _mean_ic(S)
    T = len(S)
    rows = np.arange(T)
    min_shift = min(horizon * 6, max(T // 4, 1))
    max_shift = max(T - min_shift, min_shift + 1)
    shifts = rng.integers(min_shift, max_shift, size=(n_draws, len(pairs)))
    draws = np.array(
        [_mean_ic(S[(rows[:, None] - sh[None, :]) % T, np.arange(len(pairs))[None, :]]) for sh in shifts]
    )
    return {
        "real_mean_ic": real_ic,
        "placebo_mean_ic": float(draws.mean()),
        "p_value": float((draws >= real_ic).mean()),
    }


def run_edge_finder_demo(
    panel: SyntheticFXPanel,
    cfg: EdgeFinderConfig | None = None,
    as_of_step: int | None = None,
) -> dict:
    """
    Execute the sanitized Edge Finder v2.1 demonstrative pipeline up to `as_of_step`.

    All pillar normalization, walk-forward Ridge estimation, and pair differentials
    remain strictly causal up to `as_of_step`.
    """
    cfg = cfg or EdgeFinderConfig()
    end_step = panel.n_steps - 1 if as_of_step is None else min(int(as_of_step), panel.n_steps - 1)
    idx = pd.RangeIndex(start=0, stop=end_step + 1, step=1)

    # Truncate panel view strictly at end_step to prove zero look-ahead leakage
    lfx_cut = panel.lfx.loc[idx]
    rate_cut = panel.rate.loc[idx]

    strat_names = list(panel.strategic_factors.keys())
    tact_names = list(panel.tactical_factors.keys())

    blocks: dict[str, pd.DataFrame] = {}
    for k, df in {**panel.strategic_factors, **panel.tactical_factors}.items():
        blocks[k] = xs_zscore(df.loc[idx], clip=cfg.xs_clip, min_ccy=cfg.xs_min_currencies)

    # Causal target restricted strictly inside training cutoff
    carry_cut = rate_cut.shift(1).sub(rate_cut["USD"].shift(1), axis=0) / 100.0 * (cfg.horizon_steps / 252.0)
    fwd_ccy_train = (lfx_cut.shift(-cfg.horizon_steps) - lfx_cut) + carry_cut

    weights_df = _walk_forward_ridge_weights(blocks, fwd_ccy_train, cfg=cfg)

    # Aggregate Strategic, Tactical, and Combined currency scores
    ccy_combined = pd.DataFrame(0.0, index=idx, columns=list(EST_CCYS))
    ccy_strategic = pd.DataFrame(0.0, index=idx, columns=list(EST_CCYS))
    ccy_tactical = pd.DataFrame(0.0, index=idx, columns=list(EST_CCYS))

    for k in blocks:
        contrib = blocks[k].fillna(0.0).mul(weights_df[k], axis=0)
        ccy_combined = ccy_combined + contrib
        if k in strat_names:
            ccy_strategic = ccy_strategic + contrib
        else:
            ccy_tactical = ccy_tactical + contrib

    # Pair differentials (Base - Quote)
    pair_combined = pd.DataFrame(
        {p: ccy_combined[b] - ccy_combined[q] for p, (b, q) in ALL_PAIRS.items()},
        index=idx,
    )
    pair_strategic = pd.DataFrame(
        {p: ccy_strategic[b] - ccy_strategic[q] for p, (b, q) in ALL_PAIRS.items()},
        index=idx,
    )
    pair_tactical = pd.DataFrame(
        {p: ccy_tactical[b] - ccy_tactical[q] for p, (b, q) in ALL_PAIRS.items()},
        index=idx,
    )

    # Generic placeholder volatility-normalized score [-10, +10]
    pair_ret_1 = pd.DataFrame(
        {p: lfx_cut.diff()[b] - lfx_cut.diff()[q] for p, (b, q) in ALL_PAIRS.items()},
        index=idx,
    )
    vol_h = pair_ret_1.ewm(halflife=cfg.vol_halflife, min_periods=20).std().shift(1) * np.sqrt(cfg.horizon_steps)
    conviction = pair_combined / vol_h.replace(0.0, np.nan)
    score_10 = 10.0 * np.tanh(conviction / 5.0)  # Placeholder scaling constant

    # Evaluation on out-of-warmup synthetic window
    eval_start = min(400, max(end_step // 3, 60))
    fwd_pair = panel.pair_fwd_excess(cfg.horizon_steps, ALL_PAIRS).loc[eval_start:end_step]
    fwd_ccy_eval = panel.ccy_fwd_excess(cfg.horizon_steps).loc[eval_start:end_step]

    pair_eval = nonoverlap_pair_ic(pair_combined.loc[eval_start:end_step], fwd_pair, cfg.horizon_steps)
    xs_eval = cross_sectional_ic(ccy_combined.loc[eval_start:end_step], fwd_ccy_eval, cfg.horizon_steps)
    placebo_res = circular_placebo_test(
        pair_combined.loc[eval_start:end_step],
        fwd_pair,
        horizon=cfg.horizon_steps,
        n_draws=cfg.n_placebo_draws,
        seed=cfg.seed,
    )

    return {
        "weights": weights_df,
        "ccy_combined": ccy_combined[list(TRADE_CCYS)],
        "ccy_strategic": ccy_strategic[list(TRADE_CCYS)],
        "ccy_tactical": ccy_tactical[list(TRADE_CCYS)],
        "pair_combined": pair_combined,
        "pair_strategic": pair_strategic,
        "pair_tactical": pair_tactical,
        "score_10": score_10,
        "pair_ic_table": pair_eval,
        "xs_eval": xs_eval,
        "placebo": placebo_res,
        "as_of_step": end_step,
    }
