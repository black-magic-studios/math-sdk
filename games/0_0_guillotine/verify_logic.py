"""Quick verification script for Guillotine guillotine logic."""

import sys
import os
import csv

# Add current directory to path so imports work
sys.path.append(os.getcwd())

try:
    from game_config import GameConfig as Config
    from game_override import GameStateOverride
    # Attempt to import GameState, or mock it if strictly inside SDK structure
    try:
        from gamestate import GameState
    except ImportError:
        class GameState:
            def __init__(self, _config=None):
                self.grid = []
                self.stops = [0] * 5
                self.reels = []  # To be populated
                self.free_spins_remaining = 0
                self.fs_trigger_count = 0
                self.reel_multipliers = [1] * 5
                self.bet = 1.0

except ImportError as e:
    print(f"CRITICAL: Could not import game files. Error: {e}")
    print("Ensure you are running this from /games/0_0_guillotine/ and the files exist.")
    sys.exit(1)

def load_reels_manual(conf):
    """Manually load the newly generated CSVs for the test engine."""
    base_dir = os.path.dirname(__file__)
    reels = {}
    for rtype, fname in [('BASE', 'BR0.csv'), ('FS', 'FR0.csv'), ('FS_CAP', 'FRWCAP.csv')]:
        path = os.path.join(base_dir, 'reels', fname)
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            continue
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Transpose to columns [Reel 0, Reel 1...]
        cols = [[] for _ in range(conf.num_reels)]
        for row in rows:
            for i, sym in enumerate(row):
                cols[i].append(sym.strip())
        reels[rtype] = cols
    return reels

def run_verification():
    """Execute a small battery of guillotine logic checks."""
    print("\n=== GUILLOTINE LOGIC VERIFICATION ===")
    
    # 1. Initialize Game Engine
    config = Config()
    engine = GameStateOverride(config)
    
    # Inject our fresh reels directly into the engine to be safe
    loaded_reels = load_reels_manual(config)
    if 'FS_CAP' not in loaded_reels:
        print("ERROR: Could not load FRWCAP.csv. Cannot test Tier 5.")
        return

    # 2. Test: Tier 5 Bonus (Guaranteed G + Multiply Mode)
    print("\n--- TEST: TIER 5 BONUS (5 Scatters) ---")
    print("Conditions: Guaranteed G per spin, 'MULTIPLY' mode beheads.")
    
    success_count = 0
    num_tests = 100
    
    for i in range(num_tests):
        # Setup State
        state = GameState(config)
        state.free_spins_remaining = 5
        state.fs_trigger_count = 5 # Triggers Tier 5
        
        # Point engine to the Capped Reels for this test
        engine.reels = loaded_reels['FS_CAP']
        
        # SPIN!
        engine.run_spin(state)
        
        # VALIDATION
        # 1. Check Guarantee
        has_g = any('G' in col for col in state.grid)
        # Note: If G dropped, it might be 'W' now. We check if 'W' exists with a multiplier > 1
        has_active_wild = any(m > 1 for m in state.reel_multipliers)
        
        # In our logic, 'G' becomes 'W' immediately.
        # So we check if any reel has a multiplier > 1 (implying a G dropped).
        # OR if a 'G' is visible (jammed, though Tier 5 shouldn't jam).
        
        if has_active_wild or has_g:
            success_count += 1
        else:
            print(f"FAILURE on Spin {i}: No Guillotine effect found!")
            print(f"Grid: {state.grid}")
            print(f"Mults: {state.reel_multipliers}")
            break

    print(f"Guaranteed G Result: {success_count}/{num_tests} spins had a Guillotine.")
    
    # 3. Test: Multiplier Logic (Visual Inspection)
    print("\n--- VISUAL INSPECTION (Single Spin) ---")
    state = GameState(config)
    state.free_spins_remaining = 1
    state.fs_trigger_count = 5
    engine.reels = loaded_reels['FS_CAP']
    
    engine.run_spin(state)
    
    print("Final Grid:")
    max_rows = max(config.num_rows) if isinstance(config.num_rows, list) else config.num_rows
    for row in range(max_rows):
        line = " | ".join(f"{state.grid[c][row]:^4}" for c in range(config.num_reels))
        print(f"  {line}")
    print("-" * 30)
    print(f"Reel Mults: {state.reel_multipliers}")
    
    # Check if calculation makes sense
    for i, m in enumerate(state.reel_multipliers):
        if m > 1:
            print(f"Reel {i+1} Multiplier: x{m} (Valid drop)")

if __name__ == "__main__":
    run_verification()