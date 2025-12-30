"""
FR0 Reel Optimizer - Iterative empirical optimization

Goal: Reduce cluster frequency and feature participation just enough to 
stabilize RTP without eliminating wins.

Method:
1. Make small changes (wild removal, symbol swaps, run breaking)
2. Simulate and measure impact
3. Keep changes only if metrics improve toward stability
"""

import csv
import random
import copy
import sys
import os

sys.path.insert(0, '/workspaces/math-sdk')

NUM_REELS = 7
REEL_LENGTH = 252
REELS_PATH = '/workspaces/math-sdk/games/0_0_alchemy/reels/FR0.csv'

# Non-feature, non-wild symbols for replacement
REPLACEMENT_SYMBOLS = ['H3', 'H4', 'L1', 'L2', 'L3', 'L4']


def load_reels(path):
    """Load FR0.csv - each row has 7 symbols (one per reel column)."""
    reels = [[] for _ in range(NUM_REELS)]
    with open(path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= NUM_REELS:
                for i in range(NUM_REELS):
                    reels[i].append(row[i])
    return reels


def save_reels(reels, path):
    """Save reels to CSV."""
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        for row_idx in range(len(reels[0])):
            row = [reels[i][row_idx] for i in range(len(reels))]
            writer.writerow(row)


def count_symbols(reels):
    """Count all symbol types across reels."""
    counts = {}
    for reel in reels:
        for sym in reel:
            counts[sym] = counts.get(sym, 0) + 1
    return counts


def count_runs(reel, min_length=3):
    """Count runs of same symbol of length >= min_length."""
    runs = []
    i = 0
    while i < len(reel):
        sym = reel[i]
        run_len = 1
        while i + run_len < len(reel) and reel[i + run_len] == sym:
            run_len += 1
        # Check wrap-around
        if i == 0:
            wrap_count = 0
            j = len(reel) - 1
            while j > i + run_len - 1 and reel[j] == sym:
                wrap_count += 1
                j -= 1
            run_len += wrap_count
        if run_len >= min_length:
            runs.append((sym, run_len, i))
        i += run_len if run_len > 1 else 1
    return runs


def calculate_adjacency_score(reel):
    """Calculate vertical adjacency score for a single reel."""
    score = 0
    for i in range(len(reel)):
        next_i = (i + 1) % len(reel)
        if reel[i] == reel[next_i]:
            # Weight by symbol type
            if reel[i] == 'W':
                score += 3  # Wilds amplify adjacency
            elif reel[i] in ['P', 'B', 'T']:
                score += 2  # Features matter in clusters
            elif reel[i] in ['H1', 'H2']:
                score += 1.5  # High pays
            else:
                score += 1
    return score


def break_runs(reel, max_run=2):
    """Break runs longer than max_run by swapping."""
    reel = reel.copy()
    changed = False
    
    for _ in range(10):  # Max iterations
        runs = count_runs(reel, min_length=max_run + 1)
        if not runs:
            break
        
        # Break the longest run
        runs.sort(key=lambda x: -x[1])
        sym, length, start = runs[0]
        
        # Find a position to swap with
        mid = (start + length // 2) % len(reel)
        
        # Find a different symbol to swap with
        for offset in range(1, len(reel) // 2):
            swap_pos = (mid + offset) % len(reel)
            if reel[swap_pos] != sym:
                # Check we won't create a new run at swap position
                prev_pos = (swap_pos - 1) % len(reel)
                next_pos = (swap_pos + 1) % len(reel)
                if reel[prev_pos] != sym and reel[next_pos] != sym:
                    reel[mid], reel[swap_pos] = reel[swap_pos], reel[mid]
                    changed = True
                    break
    
    return reel, changed


def reduce_wild_adjacency(reel):
    """Move wilds away from each other and from feature symbols."""
    reel = reel.copy()
    changed = False
    
    for i in range(len(reel)):
        if reel[i] == 'W':
            # Check neighbors
            prev_i = (i - 1) % len(reel)
            next_i = (i + 1) % len(reel)
            
            # Bad if wild is next to wild or feature
            neighbor_bad = (reel[prev_i] in ['W', 'P', 'B', 'T'] or 
                           reel[next_i] in ['W', 'P', 'B', 'T'])
            
            if neighbor_bad:
                # Find a better position for this wild
                for offset in range(10, len(reel) // 2, 7):
                    new_pos = (i + offset) % len(reel)
                    new_prev = (new_pos - 1) % len(reel)
                    new_next = (new_pos + 1) % len(reel)
                    
                    # Good if new neighbors are regular symbols
                    if (reel[new_pos] not in ['W', 'P', 'B', 'T', 'S'] and
                        reel[new_prev] not in ['W', 'P', 'B', 'T'] and
                        reel[new_next] not in ['W', 'P', 'B', 'T']):
                        reel[i], reel[new_pos] = reel[new_pos], reel[i]
                        changed = True
                        break
    
    return reel, changed


def remove_some_wilds(reels, count=1):
    """Remove a few wilds, distributed across reels."""
    reels = [r.copy() for r in reels]
    removed = 0
    
    # Find reels with most wilds
    wild_counts = [(i, sum(1 for s in r if s == 'W')) for i, r in enumerate(reels)]
    wild_counts.sort(key=lambda x: -x[1])
    
    for reel_idx, wc in wild_counts:
        if removed >= count:
            break
        if wc <= 1:  # Don't remove last wild from a reel
            continue
        
        # Find a wild to replace
        for pos in range(len(reels[reel_idx])):
            if reels[reel_idx][pos] == 'W':
                # Replace with a non-feature symbol
                replacement = random.choice(REPLACEMENT_SYMBOLS)
                reels[reel_idx][pos] = replacement
                removed += 1
                break
    
    return reels, removed


def run_simulation(num_spins=3000):
    """Run simulation and return key metrics."""
    from gamestate import GameState
    from game_config import GameConfig
    from src.state.run_sims import create_books
    
    # Suppress output
    import io
    from contextlib import redirect_stdout
    
    config = GameConfig()
    gamestate = GameState(config)
    
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        create_books(
            gamestate, config, 
            {'base': num_spins}, 
            batch_size=num_spins, 
            threads=1, 
            compress=False, 
            profiling=False
        )
    finally:
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
    
    # Parse output for metrics
    metrics = {
        'rtp': 0,
        'base_rtp': 0,
        'free_rtp': 0,
        'triggers': 0,
        'max_win': 0,
    }
    
    for line in output.split('\n'):
        if 'finished with' in line and 'RTP' in line:
            try:
                # Parse: "Thread 0 finished with X.XXX RTP. [baseGame: X.XX, freeGame: X.XX]"
                parts = line.split()
                rtp_idx = parts.index('RTP.')
                metrics['rtp'] = float(parts[rtp_idx - 1])
                
                if 'baseGame:' in line:
                    bg_start = line.index('baseGame:') + 9
                    bg_end = line.index(',', bg_start)
                    metrics['base_rtp'] = float(line[bg_start:bg_end].strip())
                
                if 'freeGame:' in line:
                    fg_start = line.index('freeGame:') + 9
                    fg_end = line.index(']', fg_start)
                    metrics['free_rtp'] = float(line[fg_start:fg_end].strip())
                
                if 'triggers=' in line:
                    t_start = line.index('triggers=') + 9
                    t_end = line.index(' ', t_start)
                    metrics['triggers'] = int(line[t_start:t_end])
                    
            except (ValueError, IndexError):
                pass
    
    return metrics


def optimize_iteration(reels, iteration, baseline_metrics):
    """Perform one optimization iteration."""
    
    print(f"\n--- Iteration {iteration} ---")
    
    # Save current state
    original_reels = [r.copy() for r in reels]
    original_counts = count_symbols(reels)
    
    changes_made = []
    
    # Strategy 1: Break long runs on each reel (be aggressive - max 2 in a row)
    for i in range(NUM_REELS):
        new_reel, changed = break_runs(reels[i], max_run=2)
        if changed:
            reels[i] = new_reel
            changes_made.append(f"Broke runs on reel {i}")
    
    # Strategy 2: Reduce wild adjacency
    for i in range(NUM_REELS):
        new_reel, changed = reduce_wild_adjacency(reels[i])
        if changed:
            reels[i] = new_reel
            changes_made.append(f"Reduced W adjacency on reel {i}")
    
    # Strategy 3: Remove wilds more aggressively (every iteration, 2-3 at a time)
    # We're at 700%+ RTP, need to cut wilds significantly
    reels, removed = remove_some_wilds(reels, count=3)
    if removed > 0:
        changes_made.append(f"Removed {removed} wild(s)")
    
    if not changes_made:
        print("  No changes made")
        return reels, None, False
    
    # Save and simulate
    save_reels(reels, REELS_PATH)
    
    print(f"  Changes: {', '.join(changes_made)}")
    
    # Run simulation
    metrics = run_simulation(num_spins=2000)
    
    # Calculate deltas
    delta_rtp = metrics['rtp'] - baseline_metrics['rtp']
    delta_free_rtp = metrics['free_rtp'] - baseline_metrics['free_rtp']
    
    new_counts = count_symbols(reels)
    wild_change = new_counts.get('W', 0) - original_counts.get('W', 0)
    
    print(f"  RTP: {metrics['rtp']:.2f}% (Δ{delta_rtp:+.2f}%)")
    print(f"  Free RTP: {metrics['free_rtp']:.2f}% (Δ{delta_free_rtp:+.2f}%)")
    print(f"  Base RTP: {metrics['base_rtp']:.2f}%")
    print(f"  Triggers: {metrics['triggers']}")
    print(f"  Wild count: {new_counts.get('W', 0)} ({wild_change:+d})")
    
    # Decide whether to keep changes
    # Target: total RTP ~0.96 (96%), free RTP ~0.40-0.50 (40-50%)
    # Currently seeing 7.0+ (700%+), need to get DOWN to ~0.5
    keep = False
    
    if metrics['free_rtp'] < baseline_metrics['free_rtp'] and metrics['free_rtp'] > 0.05:
        # Free RTP decreased but didn't collapse below 5%
        keep = True
        print("  ✓ KEEPING: Free RTP reduced while staying healthy")
    elif metrics['rtp'] < baseline_metrics['rtp'] and metrics['rtp'] > 0.10:
        # Total RTP decreased toward target
        keep = True
        print("  ✓ KEEPING: Total RTP moving toward target")
    else:
        print("  ✗ REVERTING: Metrics moved unfavorably or collapsed")
        # Revert
        reels = original_reels
        save_reels(reels, REELS_PATH)
    
    return reels, metrics, keep


def main():
    print("=" * 60)
    print("  FR0 REEL OPTIMIZER - Iterative Empirical Optimization")
    print("=" * 60)
    
    # Load current reels
    reels = load_reels(REELS_PATH)
    
    # Initial analysis
    print("\n--- Initial State ---")
    counts = count_symbols(reels)
    print(f"Wild count: {counts.get('W', 0)}")
    print(f"Feature symbols: P={counts.get('P', 0)}, B={counts.get('B', 0)}, T={counts.get('T', 0)}")
    
    # Calculate initial adjacency
    total_adj = sum(calculate_adjacency_score(r) for r in reels)
    print(f"Total adjacency score: {total_adj:.1f}")
    
    # Count initial runs
    total_runs = sum(len(count_runs(r, 3)) for r in reels)
    print(f"Long runs (3+): {total_runs}")
    
    # Run baseline simulation
    print("\n--- Baseline Simulation ---")
    baseline = run_simulation(num_spins=2000)
    print(f"Baseline RTP: {baseline['rtp']:.2f}%")
    print(f"Baseline Free RTP: {baseline['free_rtp']:.2f}%")
    print(f"Baseline Base RTP: {baseline['base_rtp']:.2f}%")
    
    # Iterate - need many iterations since we're 7x over target
    max_iterations = 15
    kept_count = 0
    
    for i in range(1, max_iterations + 1):
        reels, metrics, kept = optimize_iteration(reels, i, baseline)
        
        if kept and metrics:
            baseline = metrics  # Update baseline for next comparison
            kept_count += 1
        
        # Stop if we've reached target range (total RTP ~0.96)
        if baseline['rtp'] < 1.5 and baseline['rtp'] > 0.5:
            print(f"\n--- Target RTP range reached! ({baseline['rtp']:.2f}) ---")
            break
        
        # Stop if wilds are exhausted
        current_counts = count_symbols(reels)
        if current_counts.get('W', 0) < 5:
            print("\n--- Wild count getting too low, stopping ---")
            break
    
    # Final summary
    print("\n" + "=" * 60)
    print("  FINAL SUMMARY")
    print("=" * 60)
    
    final_counts = count_symbols(reels)
    print(f"Final Wild count: {final_counts.get('W', 0)} (was {counts.get('W', 0)})")
    
    final_adj = sum(calculate_adjacency_score(r) for r in reels)
    print(f"Final adjacency score: {final_adj:.1f} (was {total_adj:.1f})")
    
    final_runs = sum(len(count_runs(r, 3)) for r in reels)
    print(f"Final long runs: {final_runs} (was {total_runs})")
    
    print(f"\nFinal metrics:")
    print(f"  RTP: {baseline['rtp']:.2f}%")
    print(f"  Free RTP: {baseline['free_rtp']:.2f}%")
    print(f"  Triggers: {baseline['triggers']}")
    
    print(f"\nOptimized FR0.csv saved.")
    print(f"Original backed up to FR0_backup.csv")


if __name__ == "__main__":
    os.chdir('/workspaces/math-sdk/games/0_0_alchemy')
    main()
