"""
Stylized synthetic multi-currency panel generator for Edge Finder v2.1 demonstration.

Creates synthetic G10 currency log-prices, lagged interest rates, macro factor proxies,
and excess returns indexed purely by integer steps `0 .. n_steps - 1` (zero calendar dates).
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

EST_CCYS = ("USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK")
TRADE_CCYS = ("USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD")

OFFICIAL_PAIRS: dict[str, tuple[str, str]] = {
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
    "USDCHF": ("USD", "CHF"),
    "AUDUSD": ("AUD", "USD"),
    "NZDUSD": ("NZD", "USD"),
    "USDCAD": ("USD", "CAD"),
    "EURJPY": ("EUR", "JPY"),
    "GBPJPY": ("GBP", "JPY"),
    "AUDJPY": ("AUD", "JPY"),
    "EURGBP": ("EUR", "GBP"),
    "AUDNZD": ("AUD", "NZD"),
    "EURCHF": ("EUR", "CHF"),
    "CADJPY": ("CAD", "JPY"),
}

QUOTE_ORDER = ("EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "JPY")
ALL_PAIRS: dict[str, tuple[str, str]] = {
    QUOTE_ORDER[i] + QUOTE_ORDER[j]: (QUOTE_ORDER[i], QUOTE_ORDER[j])
    for i in range(len(QUOTE_ORDER))
    for j in range(i + 1, len(QUOTE_ORDER))
}


@dataclass
class SyntheticFXPanel:
    """Synthetic multi-currency panel for demonstrative cross-sectional modeling."""

    lfx: pd.DataFrame
    rate: pd.DataFrame
    strategic_factors: dict[str, pd.DataFrame]
    tactical_factors: dict[str, pd.DataFrame]
    n_steps: int

    def ccy_fwd_excess(self, horizon: int) -> pd.DataFrame:
        """Forward relative excess return per currency against USD numeraire."""
        carry = self.rate.shift(1).sub(self.rate["USD"].shift(1), axis=0) / 100.0 * (horizon / 252.0)
        return (self.lfx.shift(-horizon) - self.lfx) + carry

    def pair_fwd_excess(self, horizon: int, pairs: dict[str, tuple[str, str]] | None = None) -> pd.DataFrame:
        """Forward excess return for each FX pair (base minus quote)."""
        pairs = pairs or ALL_PAIRS
        ccy_ret = self.ccy_fwd_excess(horizon)
        return pd.DataFrame({p: ccy_ret[b] - ccy_ret[q] for p, (b, q) in pairs.items()}, index=self.lfx.index)


def generate_synthetic_fx_panel(
    n_steps: int = 2400,
    seed: int = 101,
    signal_strength: float = 0.22,
) -> SyntheticFXPanel:
    """
    Generate stylized synthetic G10 FX panel with latent strategic and tactical drivers.

    Uses integer business-step index `0 .. n_steps - 1` (no real dates or series).
    """
    rng = np.random.default_rng(seed)
    steps = np.arange(n_steps, dtype=int)
    n_ccy = len(EST_CCYS)

    # Latent slow strategic factor (AR(1) persistence) and faster tactical factor
    f_strat = np.zeros((n_steps, n_ccy), dtype=float)
    f_tact = np.zeros((n_steps, n_ccy), dtype=float)
    for t in range(1, n_steps):
        f_strat[t] = 0.985 * f_strat[t - 1] + rng.normal(0.0, 0.17, size=n_ccy)
        f_tact[t] = 0.900 * f_tact[t - 1] + rng.normal(0.0, 0.43, size=n_ccy)

    # Normalize latent drivers cross-sectionally
    def _xs_norm(arr: np.ndarray) -> np.ndarray:
        mu = arr.mean(axis=1, keepdims=True)
        sd = arr.std(axis=1, keepdims=True)
        return np.divide(arr - mu, np.where(sd > 1e-8, sd, 1.0))

    z_strat = _xs_norm(f_strat)
    z_tact = _xs_norm(f_tact)

    # Observable proxy pillars = latent factor + orthogonal observation noise
    strategic_factors = {
        "S_Policy": pd.DataFrame(
            np.clip(z_strat + rng.normal(0.0, 0.5, size=(n_steps, n_ccy)), -3.0, 3.0),
            index=steps,
            columns=list(EST_CCYS),
        ).shift(1),
        "S_Value": pd.DataFrame(
            np.clip(0.7 * z_strat + rng.normal(0.0, 0.7, size=(n_steps, n_ccy)), -3.0, 3.0),
            index=steps,
            columns=list(EST_CCYS),
        ).shift(1),
        "S_MacroPillar": pd.DataFrame(
            np.clip(0.8 * z_strat + rng.normal(0.0, 0.6, size=(n_steps, n_ccy)), -3.0, 3.0),
            index=steps,
            columns=list(EST_CCYS),
        ).shift(1),
    }

    tactical_factors = {
        "T_RateGap": pd.DataFrame(
            np.clip(z_tact + rng.normal(0.0, 0.55, size=(n_steps, n_ccy)), -3.0, 3.0),
            index=steps,
            columns=list(EST_CCYS),
        ).shift(1),
        "T_Positioning": pd.DataFrame(
            np.clip(0.75 * z_tact + rng.normal(0.0, 0.65, size=(n_steps, n_ccy)), -3.0, 3.0),
            index=steps,
            columns=list(EST_CCYS),
        ).shift(1),
    }

    # Synthetic policy rates (bounded 0..6%) & FX log-prices driven weakly by lagged factors
    rates = np.clip(2.5 + 0.8 * z_strat, 0.0, 6.0)
    daily_vol = 0.0048
    drift = signal_strength * (daily_vol / np.sqrt(20.0)) * (0.6 * np.roll(z_strat, 1, axis=0) + 0.4 * np.roll(z_tact, 1, axis=0))
    drift[0] = 0.0
    shocks = rng.normal(0.0, daily_vol, size=(n_steps, n_ccy))
    ret = drift + shocks
    ret[:, 0] = 0.0  # USD numeraire convention
    lfx = np.cumsum(ret, axis=0)

    return SyntheticFXPanel(
        lfx=pd.DataFrame(lfx, index=steps, columns=list(EST_CCYS)),
        rate=pd.DataFrame(rates, index=steps, columns=list(EST_CCYS)),
        strategic_factors=strategic_factors,
        tactical_factors=tactical_factors,
        n_steps=n_steps,
    )
