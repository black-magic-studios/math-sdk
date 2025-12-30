"""Quick test script with periodic stats output."""

import sys
import time
sys.path.insert(0, '/workspaces/math-sdk/games/0_0_alchemy')
sys.path.insert(0, '/workspaces/math-sdk')

from gamestate import GameState, sim_stats
from game_config import GameConfig
from src.state.run_sims import create_books

def run_quick_test(num_spins=10000, print_every=2000):
    """Run simulation with periodic progress updates."""
    
    config = GameConfig()
    gamestate = GameState(config)
    gamestate.betmode = 'base'
    
    sim_stats.reset()
    start_time = time.time()
    
    print(f"\n=== Running {num_spins:,} spins with updates every {print_every:,} ===\n")
    
    for i in range(num_spins):
        try:
            gamestate.run_spin(sim=i)
        except Exception as e:
            print(f"Error at spin {i}: {e}")
            break
            
        # Print progress periodically
        if (i + 1) % print_every == 0:
            elapsed = time.time() - start_time
            spins_per_sec = (i + 1) / elapsed
            
            # Calculate current RTP
            total_wagered = sim_stats.total_spins * config.stake
            total_won = sim_stats.total_base_win + sim_stats.total_fs_win
            rtp = (total_won / total_wagered * 100) if total_wagered > 0 else 0
            
            trigger_rate = sim_stats.total_spins / max(1, sim_stats.total_freespin_triggers)
            
            print(f"[{i+1:,}/{num_spins:,}] RTP: {rtp:.1f}% | "
                  f"Triggers: {sim_stats.total_freespin_triggers} (1 in {trigger_rate:.0f}) | "
                  f"Features: P={sim_stats.wild_potion_triggers} B={sim_stats.elixir_bomb_triggers} T={sim_stats.symbol_transform_triggers} | "
                  f"{spins_per_sec:.0f} spins/sec")
    
    # Final stats
    elapsed = time.time() - start_time
    print(f"\n=== Completed in {elapsed:.1f} seconds ===")
    sim_stats.print_stats("QUICK TEST")

if __name__ == "__main__":
    # Parse command line args
    num_spins = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print_every = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    run_quick_test(num_spins, print_every)
