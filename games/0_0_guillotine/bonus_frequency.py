"""Estimate natural bonus-trigger frequencies for Guillotine.

This script samples *base* boards directly from the configured reel weights without
using `draw_board()` (which, in base mode, re-rolls to avoid 3+ scatters).

It applies the base overlay (SSR_Base: P -> G) and then runs `resolve_guillotines`
so scatter limits (max 1 per reel) match the real game flow prior to checking
scatter-trigger conditions.

Run:
  PYTHONPATH=/workspaces/math-sdk:/workspaces/math-sdk/games/0_0_guillotine \
    /workspaces/math-sdk/.venv/bin/python games/0_0_guillotine/bonus_frequency.py --sims 200000
"""

from __future__ import annotations

import argparse
import random
from collections import Counter

from src.calculations.statistics import get_random_outcome

from game_config import GameConfig
from gamestate import GameState


def apply_overlay_p_to_g(state: GameState) -> None:
    """Apply Guillotine overlay behavior for the current gametype.

    Current Guillotine overlay logic only converts 'P' -> 'G'. Any other symbol
    (e.g., 'X') is treated as transparent.
    """
    mode_cfg = state.get_current_mode_config(state)
    overlay_cfg = mode_cfg.get("overlay_reels", {})
    reels_map = overlay_cfg.get(state.gametype, {})
    if not reels_map:
        return

    reel_name = get_random_outcome(reels_map)
    if not reel_name:
        return

    overlay_strip = state.config.reels.get(reel_name)
    if not overlay_strip:
        return

    stops = [random.randrange(len(overlay_strip[i])) for i in range(state.config.num_reels)]
    for r_idx in range(state.config.num_reels):
        stop = stops[r_idx]
        col_len = len(overlay_strip[r_idx])
        for row in range(state.config.num_rows[r_idx]):
            sym_id = overlay_strip[r_idx][(stop + row) % col_len]
            if sym_id == "P":
                state.board[r_idx][row] = state.create_symbol("G")


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate natural scatter-trigger frequencies.")
    parser.add_argument("--sims", type=int, default=200_000, help="Number of sampled base boards.")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed for reproducibility.")
    args = parser.parse_args()

    random.seed(args.seed)

    config = GameConfig()
    state = GameState(config)

    # Configure state to use base-mode reel selection conditions.
    state.betmode = "base"
    state.criteria = "basegame"
    state.gametype = config.basegame_type

    freespin_threshold = min(config.freespin_triggers[config.basegame_type].keys())

    scatter_counts = Counter()
    trigger_tiers = Counter({"fs3": 0, "fs4": 0, "fs5": 0})

    for _ in range(args.sims):
        state.reset_book()
        state.gametype = config.basegame_type

        # Draw from reel weights without base-mode reroll suppression.
        state.create_board_reelstrips()

        # Apply base overlay (P -> G).
        apply_overlay_p_to_g(state)

        # Match in-game flow: guillotine resolution enforces max 1 scatter per reel
        # and refreshes the special-symbol cache.
        state.resolve_guillotines(mode_cfg=config.bonus_modes["base"])

        scatters = state.count_special_symbols("scatter")
        scatter_counts[scatters] += 1

        if scatters >= freespin_threshold:
            if scatters >= 5:
                trigger_tiers["fs5"] += 1
            elif scatters == 4:
                trigger_tiers["fs4"] += 1
            else:
                trigger_tiers["fs3"] += 1

    total = float(args.sims)
    total_triggers = sum(trigger_tiers.values())

    def pct(n: int) -> float:
        return 100.0 * (n / total) if total else 0.0

    # Print distribution.
    print("\nNatural scatter distribution (after overlay + guillotine resolution):")
    for k in sorted(scatter_counts.keys()):
        print(f"  scatters={k}: {scatter_counts[k]} ({pct(scatter_counts[k]):.4f}%)")

    print("\nNatural feature trigger frequency (base reels):")
    print(f"  any (>= {freespin_threshold} scatters): {total_triggers} ({pct(total_triggers):.6f}%)")
    for tier in ("fs3", "fs4", "fs5"):
        print(f"  {tier}: {trigger_tiers[tier]} ({pct(trigger_tiers[tier]):.6f}%)")

    # Compare to configured betmode costs (cost ≈ 1 / hit-rate when using forced-mode EV scaling).
    costs = {bm.get_name(): bm.get_cost() for bm in config.bet_modes}
    print("\nImplied costs from observed hit-rates (cost ~= 1/p):")
    for tier in ("fs3", "fs4", "fs5"):
        p = trigger_tiers[tier] / total if total else 0.0
        implied = (1.0 / p) if p > 0 else float("inf")
        cfg_cost = float(costs.get(tier, float("nan")))
        print(f"  {tier}: p={p:.10f} implied_cost={implied:.2f} (configured cost={cfg_cost:.2f})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
