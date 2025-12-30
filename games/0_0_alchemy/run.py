"""Main file for generating results for sample ways-pay game."""

from gamestate import GameState, sim_stats
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    num_threads = 1  # Single thread for detailed stats tracking
    rust_threads = 20
    batching_size = 1000  # Smaller batches for faster feedback
    compression = True
    profiling = False

    num_sim_args = {
        "base": int(5000),  # 5k spins - quick test
        "bonus": int(100),
    }

    run_conditions = {
        "run_sims": True,
        "run_optimization": False,
        "run_analysis": False,
        "run_format_checks": False,
    }
    target_modes = ["base"]

    config = GameConfig()
    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        # Run base game simulation only
        sim_stats.reset()
        create_books(
            gamestate,
            config,
            {"base": num_sim_args["base"]},
            batching_size,
            num_threads,
            compression,
            profiling,
        )
        sim_stats.print_stats("BASE GAME")

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
