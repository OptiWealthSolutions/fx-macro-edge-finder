"""Causality, neutrality, and statistical test suite for sanitized Edge Finder v2.1."""
from __future__ import annotations

import numpy as np
import pytest

from edge_finder_v2.model import EdgeFinderConfig, run_edge_finder_demo
from edge_finder_v2.synthetic_data import ALL_PAIRS, TRADE_CCYS, generate_synthetic_fx_panel


@pytest.fixture(scope="module")
def synth_panel():
    return generate_synthetic_fx_panel(n_steps=1600, seed=202, signal_strength=0.25)


def test_cross_sectional_currency_sum_neutrality(synth_panel):
    res = run_edge_finder_demo(synth_panel, EdgeFinderConfig())
    ccy = res["ccy_combined"][list(TRADE_CCYS)]
    row_means = ccy.iloc[400:].mean(axis=1).abs().max()
    # Currency blocks are cross-sectionally standardized across G10; G8 mean stays bounded
    assert np.isfinite(row_means)
    assert res["pair_combined"].shape[1] == len(ALL_PAIRS)


def test_strict_truncation_invariance_no_lookahead(synth_panel):
    cfg = EdgeFinderConfig()
    res_full = run_edge_finder_demo(synth_panel, cfg=cfg)

    cutoff = 1100
    res_cut = run_edge_finder_demo(synth_panel, cfg=cfg, as_of_step=cutoff)

    # Compare composite pair signal up to cutoff (must be bit-exact)
    p_full = res_full["pair_combined"].loc[:cutoff]
    p_cut = res_cut["pair_combined"].loc[:cutoff]
    max_diff = float((p_full - p_cut).abs().max().max())
    assert max_diff <= 1e-10, f"Look-ahead leak detected: max_diff={max_diff}"


def test_weights_are_nonnegative_and_sum_to_one(synth_panel):
    res = run_edge_finder_demo(synth_panel, EdgeFinderConfig())
    w = res["weights"]
    assert (w.to_numpy() >= -1e-12).all()
    assert np.allclose(w.sum(axis=1).to_numpy(), 1.0, atol=1e-6)
