"""Main file for generating results for Guillotine (ways-pay) game."""

import sys
from pathlib import Path

# Ensure workspace packages (e.g., `optimization_program`) are imported from the
# repo checkout rather than any older installed copies in the venv.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "games" / "0_0_guillotine"))

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    NUM_THREADS = 10
    RUST_THREADS = 20
    BATCHING_SIZE = 50000
    COMPRESSION = True
    PROFILING = False

    # ---------------------------------------------------------
    # Add separate simulation amounts per mode
    # ---------------------------------------------------------
    num_sim_args = {
        "base": int(100000),
        "fs3": int(10000),   # 3-scatter free spins
        "fs4": int(10000),   # 4-scatter upgraded free spins
        "fs5": int(10000),   # 5-scatter super free spins
    }

    run_conditions = {
        "run_sims": True,
        "run_optimization": True,
        "run_analysis": True,
        "run_format_checks": False,
    }

    # ---------------------------------------------------------
    # Modes to target: base + bonuses (3,4,5 scatters)
    # ---------------------------------------------------------
    target_modes = ["base", "fs3", "fs4", "fs5"]

    # ---------------------------------------------------------
    # Initialize config + gamestate
    # ---------------------------------------------------------
    config = GameConfig()
    gamestate = GameState(config)

    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        _optimization_setup_class = OptimizationSetup(config)

    # ---------------------------------------------------------
    # SIMULATION: Create books for all modes
    # ---------------------------------------------------------
    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            BATCHING_SIZE,
            NUM_THREADS,
            COMPRESSION,
            PROFILING,
        )

    # Write out configs
    generate_configs(gamestate)

    # ---------------------------------------------------------
    # OPTIMIZATION: run Rust optimizer across all new modes
    # ---------------------------------------------------------
    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, RUST_THREADS)
        generate_configs(gamestate)

    # ---------------------------------------------------------
    # ANALYSIS: generate stat sheets per mode
    # ---------------------------------------------------------
    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    # ---------------------------------------------------------
    # FORMAT + SANITY CHECKS
    # ---------------------------------------------------------
    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
