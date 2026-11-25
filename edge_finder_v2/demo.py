"""Executable synthetic demonstration for the sanitized Edge Finder v2.1 pipeline."""
from __future__ import annotations

from .model import EdgeFinderConfig, run_edge_finder_demo
from .synthetic_data import generate_synthetic_fx_panel


def main() -> None:
    print("=== Edge Finder v2.1 Synthetic Architecture Demo (Sanitized Placeholder Mode) ===")
    panel = generate_synthetic_fx_panel(n_steps=2400, seed=101, signal_strength=0.25)
    cfg = EdgeFinderConfig()
    res = run_edge_finder_demo(panel, cfg=cfg)

    xs = res["xs_eval"]
    pl = res["placebo"]
    pt = res["pair_ic_table"]
    pos_pairs = int((pt["IC"] > 0).sum())

    print(f"Steps simulated: {panel.n_steps} | Official pairs evaluated: {len(pt)}")
    print(
        f"Cross-Sectional Rank IC: {xs['xs_ic']:+.4f} (Newey-West t = {xs['nw_t']:+.2f}) | "
        f"Pairs IC > 0: {pos_pairs}/{len(pt)}"
    )
    print(
        f"Circular Placebo Test -> Real Mean IC: {pl['real_mean_ic']:+.4f} vs. "
        f"Placebo Mean: {pl['placebo_mean_ic']:+.4f} (p = {pl['p_value']:.3f})"
    )
    print("\nTop 5 Synthetic Benchmark Pairs:")
    print(pt.sort_values("IC", ascending=False).head(5).to_string(index=False))


if __name__ == "__main__":
    main()
