"""
Reel Placement Optimizer for FR0

Goal: Arrange symbols so that:
1. Winning clusters are harder to form naturally
2. Wilds/features often land in isolated positions (no adjacent matches)
3. Transforms often result in symbols that don't connect

Strategy:
- Analyze 7-symbol windows (what appears on screen)
- Place high-value symbols and wilds away from each other vertically
- Create "dead zones" where wilds are surrounded by mixed symbols
- Ensure features land in positions less likely to create connections
"""

import csv
import random
from collections import defaultdict
from typing import List, Dict, Tuple

NUM_REELS = 7
REEL_LENGTH = 252
NUM_ROWS = 7

CLUSTER_SYMBOLS = ['H1', 'H2', 'H3', 'H4', 'L1', 'L2', 'L3', 'L4', 'W']
HIGH_VALUE = ['H1', 'H2', 'W']
FEATURES = ['P', 'B', 'T']


def load_reels(path: str) -> List[List[str]]:
    """Load reels from CSV - each column is a reel."""
    reels = [[] for _ in range(NUM_REELS)]
    with open(path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= NUM_REELS:
                for i in range(NUM_REELS):
                    reels[i].append(row[i])
    return reels


def save_reels(reels: List[List[str]], path: str):
    """Save reels to CSV."""
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        for row_idx in range(len(reels[0])):
            row = [reels[i][row_idx] for i in range(len(reels))]
            writer.writerow(row)


def get_window(reel: List[str], start: int) -> List[str]:
    """Get 7 consecutive symbols from a reel (with wrap-around)."""
    return [reel[(start + i) % len(reel)] for i in range(NUM_ROWS)]


def count_adjacency_in_window(window: List[str]) -> Dict[str, int]:
    """Count vertical adjacency pairs in a 7-symbol window."""
    pairs = defaultdict(int)
    for i in range(len(window) - 1):
        if window[i] == window[i + 1]:
            pairs[window[i]] += 1
        # Also count wild adjacency to any symbol
        if window[i] == 'W' or window[i + 1] == 'W':
            if window[i] != window[i + 1]:
                pairs['W_adj'] += 1
    return pairs


def analyze_reel_windows(reel: List[str]) -> Dict:
    """Analyze all possible windows on a reel."""
    stats = {
        'total_windows': len(reel),
        'windows_with_pairs': 0,
        'high_value_pairs': 0,
        'wild_adjacent_to_symbol': 0,
        'feature_isolated': 0,
        'feature_with_matches': 0,
    }
    
    for start in range(len(reel)):
        window = get_window(reel, start)
        pairs = count_adjacency_in_window(window)
        
        if sum(pairs.values()) > 0:
            stats['windows_with_pairs'] += 1
        
        for sym in HIGH_VALUE:
            stats['high_value_pairs'] += pairs.get(sym, 0)
        
        stats['wild_adjacent_to_symbol'] += pairs.get('W_adj', 0)
        
        # Check if features are isolated (no matching neighbors)
        for i, sym in enumerate(window):
            if sym in FEATURES:
                neighbors = []
                if i > 0:
                    neighbors.append(window[i-1])
                if i < len(window) - 1:
                    neighbors.append(window[i+1])
                
                # Feature is "good" if neighbors are all different from each other
                if len(neighbors) == 2 and neighbors[0] != neighbors[1]:
                    stats['feature_isolated'] += 1
                else:
                    stats['feature_with_matches'] += 1
    
    return stats


def find_bad_patterns(reel: List[str]) -> List[Tuple[int, str]]:
    """Find positions with problematic patterns (runs, wild clusters)."""
    bad_positions = []
    
    for i in range(len(reel)):
        sym = reel[i]
        prev_sym = reel[(i - 1) % len(reel)]
        next_sym = reel[(i + 1) % len(reel)]
        
        # Run of 3+ same symbol
        if sym == prev_sym == next_sym:
            bad_positions.append((i, 'run_of_3'))
        
        # Wild next to wild
        if sym == 'W' and (prev_sym == 'W' or next_sym == 'W'):
            bad_positions.append((i, 'wild_cluster'))
        
        # Wild next to high-value
        if sym == 'W' and (prev_sym in ['H1', 'H2'] or next_sym in ['H1', 'H2']):
            bad_positions.append((i, 'wild_high_value'))
        
        # Feature next to matching symbols
        if sym in FEATURES:
            if prev_sym == next_sym and prev_sym in CLUSTER_SYMBOLS:
                bad_positions.append((i, 'feature_between_matches'))
    
    return bad_positions


def find_good_swap_target(reel: List[str], pos: int, avoid_symbols: List[str]) -> int:
    """Find a position to swap with that won't create new problems."""
    current_sym = reel[pos]
    
    # Look for positions where:
    # 1. The symbol there is different
    # 2. Neighbors are different from current symbol
    # 3. Won't create a new run
    
    candidates = []
    for i in range(len(reel)):
        if i == pos:
            continue
        
        target_sym = reel[i]
        if target_sym == current_sym:
            continue
        if target_sym in avoid_symbols:
            continue
        
        # Check if swapping would be safe
        prev_i = (i - 1) % len(reel)
        next_i = (i + 1) % len(reel)
        
        # After swap, current_sym would be at position i
        # Check it won't create a run there
        if reel[prev_i] != current_sym and reel[next_i] != current_sym:
            # Also check the original position won't become a run
            prev_pos = (pos - 1) % len(reel)
            next_pos = (pos + 1) % len(reel)
            if reel[prev_pos] != target_sym and reel[next_pos] != target_sym:
                candidates.append(i)
    
    if candidates:
        return random.choice(candidates)
    return -1


def break_bad_patterns(reel: List[str], max_swaps: int = 50) -> Tuple[List[str], int]:
    """Break problematic patterns by swapping symbols."""
    reel = reel.copy()
    swaps_made = 0
    
    for _ in range(max_swaps):
        bad = find_bad_patterns(reel)
        if not bad:
            break
        
        # Pick a random bad position
        pos, pattern_type = random.choice(bad)
        
        # Find a good swap target
        avoid = ['W', 'P', 'B', 'T', 'S'] if reel[pos] in CLUSTER_SYMBOLS else []
        target = find_good_swap_target(reel, pos, avoid)
        
        if target >= 0:
            reel[pos], reel[target] = reel[target], reel[pos]
            swaps_made += 1
    
    return reel, swaps_made


def isolate_wilds(reel: List[str]) -> Tuple[List[str], int]:
    """Move wilds away from high-value symbols and other wilds."""
    reel = reel.copy()
    moves = 0
    
    wild_positions = [i for i, s in enumerate(reel) if s == 'W']
    
    for w_pos in wild_positions:
        prev_sym = reel[(w_pos - 1) % len(reel)]
        next_sym = reel[(w_pos + 1) % len(reel)]
        
        # Bad if wild is near another wild or H1/H2
        bad_neighbors = prev_sym in ['W', 'H1', 'H2'] or next_sym in ['W', 'H1', 'H2']
        
        if bad_neighbors:
            # Find a better position - surrounded by low-value or mixed symbols
            for offset in range(10, len(reel) // 2, 7):
                new_pos = (w_pos + offset) % len(reel)
                new_prev = reel[(new_pos - 1) % len(reel)]
                new_next = reel[(new_pos + 1) % len(reel)]
                
                # Good if surrounded by low-value symbols that are different
                if (new_prev not in ['W', 'H1', 'H2', 'P', 'B', 'T', 'S'] and
                    new_next not in ['W', 'H1', 'H2', 'P', 'B', 'T', 'S'] and
                    new_prev != new_next and
                    reel[new_pos] not in ['W', 'P', 'B', 'T', 'S']):
                    reel[w_pos], reel[new_pos] = reel[new_pos], reel[w_pos]
                    moves += 1
                    break
    
    return reel, moves


def isolate_features(reel: List[str]) -> Tuple[List[str], int]:
    """Move feature symbols to positions where they're less likely to create wins."""
    reel = reel.copy()
    moves = 0
    
    feature_positions = [i for i, s in enumerate(reel) if s in FEATURES]
    
    for f_pos in feature_positions:
        prev_sym = reel[(f_pos - 1) % len(reel)]
        next_sym = reel[(f_pos + 1) % len(reel)]
        
        # Bad if feature is between matching symbols (would create connection when activated)
        if prev_sym == next_sym and prev_sym in CLUSTER_SYMBOLS:
            # Find position with mismatched neighbors
            for offset in range(5, len(reel) // 2, 5):
                new_pos = (f_pos + offset) % len(reel)
                new_prev = reel[(new_pos - 1) % len(reel)]
                new_next = reel[(new_pos + 1) % len(reel)]
                
                # Good if neighbors are different symbols
                if (new_prev != new_next and
                    reel[new_pos] not in ['W', 'P', 'B', 'T', 'S']):
                    reel[f_pos], reel[new_pos] = reel[new_pos], reel[f_pos]
                    moves += 1
                    break
    
    return reel, moves


def disperse_high_value(reel: List[str]) -> Tuple[List[str], int]:
    """Spread H1 and H2 symbols apart to reduce large cluster potential."""
    reel = reel.copy()
    moves = 0
    
    for sym in ['H1', 'H2']:
        positions = [i for i, s in enumerate(reel) if s == sym]
        
        for i, pos in enumerate(positions[:-1]):
            next_pos = positions[i + 1]
            gap = (next_pos - pos) % len(reel)
            
            # If gap is too small (symbols too close), try to spread
            if gap < 5:
                # Find a position further away
                ideal_gap = len(reel) // len(positions)
                target_pos = (pos + ideal_gap) % len(reel)
                
                # Find nearest swappable position
                for offset in range(-3, 4):
                    check_pos = (target_pos + offset) % len(reel)
                    if (reel[check_pos] not in ['W', 'P', 'B', 'T', 'S', 'H1', 'H2'] and
                        check_pos != pos):
                        reel[next_pos], reel[check_pos] = reel[check_pos], reel[next_pos]
                        moves += 1
                        break
    
    return reel, moves


def calculate_cluster_potential(reels: List[List[str]], num_samples: int = 5000) -> Dict:
    """Estimate cluster formation rate through sampling."""
    stats = {
        'samples': num_samples,
        'with_clusters': 0,
        'total_cluster_cells': 0,
        'wild_in_cluster': 0,
        'feature_created_connection': 0,
    }
    
    for _ in range(num_samples):
        # Random stop positions
        positions = [random.randint(0, REEL_LENGTH - 1) for _ in range(NUM_REELS)]
        
        # Build grid
        grid = []
        for reel_idx in range(NUM_REELS):
            col = get_window(reels[reel_idx], positions[reel_idx])
            grid.append(col)
        
        # Simple cluster check - look for 5+ adjacent same symbols
        # (This is a simplified approximation)
        has_cluster = False
        for row in range(NUM_ROWS):
            for reel in range(NUM_REELS - 4):
                # Check horizontal run of 5
                symbols = [grid[reel + i][row] for i in range(5)]
                base_sym = symbols[0] if symbols[0] != 'W' else symbols[1] if len(symbols) > 1 else None
                if base_sym and all(s == base_sym or s == 'W' for s in symbols):
                    has_cluster = True
                    if 'W' in symbols:
                        stats['wild_in_cluster'] += 1
                    break
            if has_cluster:
                break
        
        # Check vertical runs too
        if not has_cluster:
            for reel in range(NUM_REELS):
                for row in range(NUM_ROWS - 4):
                    symbols = [grid[reel][row + i] for i in range(5)]
                    base_sym = symbols[0] if symbols[0] != 'W' else symbols[1] if len(symbols) > 1 else None
                    if base_sym and all(s == base_sym or s == 'W' for s in symbols):
                        has_cluster = True
                        if 'W' in symbols:
                            stats['wild_in_cluster'] += 1
                        break
                if has_cluster:
                    break
        
        if has_cluster:
            stats['with_clusters'] += 1
    
    stats['cluster_rate'] = stats['with_clusters'] / num_samples
    return stats


def optimize_reel(reel: List[str], reel_idx: int) -> List[str]:
    """Apply all optimizations to a single reel."""
    print(f"  Reel {reel_idx + 1}:", end=" ")
    
    total_changes = 0
    
    # Step 1: Break runs and bad patterns
    reel, changes = break_bad_patterns(reel, max_swaps=30)
    total_changes += changes
    print(f"patterns={changes}", end=" ")
    
    # Step 2: Isolate wilds
    reel, changes = isolate_wilds(reel)
    total_changes += changes
    print(f"wilds={changes}", end=" ")
    
    # Step 3: Isolate features
    reel, changes = isolate_features(reel)
    total_changes += changes
    print(f"features={changes}", end=" ")
    
    # Step 4: Disperse high-value
    reel, changes = disperse_high_value(reel)
    total_changes += changes
    print(f"highval={changes}", end=" ")
    
    print(f"(total={total_changes})")
    return reel


def main():
    import os
    import sys
    os.chdir('/workspaces/math-sdk/games/0_0_alchemy')
    
    # Allow specifying which reel file to optimize
    reel_file = sys.argv[1] if len(sys.argv) > 1 else 'FR0'
    
    print("=" * 60)
    print(f"  {reel_file} REEL PLACEMENT OPTIMIZER")
    print("=" * 60)
    
    # Backup
    import shutil
    shutil.copy(f'reels/{reel_file}.csv', f'reels/{reel_file}_backup.csv')
    print(f"\nBacked up {reel_file}.csv -> {reel_file}_backup.csv")
    
    # Load
    reels = load_reels(f'reels/{reel_file}.csv')
    print(f"Loaded {len(reels)} reels with {len(reels[0])} symbols each")
    
    # Analyze before
    print("\n--- BEFORE OPTIMIZATION ---")
    before_stats = calculate_cluster_potential(reels)
    print(f"Cluster rate: {before_stats['cluster_rate']*100:.2f}%")
    print(f"Wilds in clusters: {before_stats['wild_in_cluster']}")
    
    for i, reel in enumerate(reels):
        stats = analyze_reel_windows(reel)
        bad = find_bad_patterns(reel)
        print(f"  Reel {i+1}: {stats['high_value_pairs']} high-val pairs, {len(bad)} bad patterns")
    
    # Optimize each reel
    print("\n--- OPTIMIZING ---")
    for i in range(NUM_REELS):
        reels[i] = optimize_reel(reels[i], i)
    
    # Analyze after
    print("\n--- AFTER OPTIMIZATION ---")
    after_stats = calculate_cluster_potential(reels)
    print(f"Cluster rate: {after_stats['cluster_rate']*100:.2f}%")
    print(f"Wilds in clusters: {after_stats['wild_in_cluster']}")
    
    for i, reel in enumerate(reels):
        stats = analyze_reel_windows(reel)
        bad = find_bad_patterns(reel)
        print(f"  Reel {i+1}: {stats['high_value_pairs']} high-val pairs, {len(bad)} bad patterns")
    
    # Save
    save_reels(reels, f'reels/{reel_file}.csv')
    print(f"\nSaved optimized {reel_file}.csv")
    
    # Summary
    print("\n--- SUMMARY ---")
    delta = after_stats['cluster_rate'] - before_stats['cluster_rate']
    print(f"Cluster rate: {before_stats['cluster_rate']*100:.2f}% -> {after_stats['cluster_rate']*100:.2f}% ({delta*100:+.2f}%)")
    wild_delta = after_stats['wild_in_cluster'] - before_stats['wild_in_cluster']
    print(f"Wilds in clusters: {before_stats['wild_in_cluster']} -> {after_stats['wild_in_cluster']} ({wild_delta:+d})")


if __name__ == "__main__":
    main()
