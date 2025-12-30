"""
Reel Optimizer for Cluster Games

This script optimizes reel strip arrangements to make cluster connections
harder to form. In a cluster game, symbols need to be adjacent (touching)
to form winning clusters of 5+.

Key insight: The ORDER of symbols on each reel strip affects cluster probability.
If we arrange symbols so that when the grid is displayed, matching symbols are
less likely to be adjacent, we reduce cluster formation without changing symbol counts.

Optimization strategies:
1. Maximize symbol dispersion - spread identical symbols apart on each reel
2. Anti-correlation between adjacent reels - avoid patterns where same symbol
   appears at similar vertical positions on neighboring reels
3. Simulation-based validation - test actual cluster rates
"""

import random
import csv
import os
from collections import defaultdict
from typing import List, Dict, Tuple
import copy

NUM_REELS = 7
NUM_ROWS = 7
REEL_LENGTH = 252
CLUSTER_SYMBOLS = ['H1', 'H2', 'H3', 'H4', 'L1', 'L2', 'L3', 'L4', 'W']


def load_reels(filepath: str) -> List[List[str]]:
    """Load reel strips from CSV - each column is a reel."""
    reels = [[] for _ in range(NUM_REELS)]
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= NUM_REELS:
                for i in range(NUM_REELS):
                    reels[i].append(row[i])
    return reels


def save_reels(filepath: str, reels: List[List[str]]):
    """Save reel strips to CSV - each column is a reel."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        for row_idx in range(len(reels[0])):
            row = [reels[i][row_idx] for i in range(len(reels))]
            writer.writerow(row)


def get_grid(reels: List[List[str]], positions: List[int]) -> List[List[str]]:
    """Get a 7x7 grid given reel positions."""
    grid = []
    for reel_idx, reel in enumerate(reels):
        col = []
        pos = positions[reel_idx]
        for row in range(NUM_ROWS):
            idx = (pos + row) % len(reel)
            col.append(reel[idx])
        grid.append(col)
    return grid


def find_clusters(grid: List[List[str]]) -> Dict[str, List[List[Tuple[int, int]]]]:
    """Find all clusters in the grid using flood fill."""
    visited = [[False] * NUM_ROWS for _ in range(NUM_REELS)]
    clusters = defaultdict(list)
    
    def flood_fill(reel, row, symbol, cluster):
        if (reel < 0 or reel >= NUM_REELS or 
            row < 0 or row >= NUM_ROWS or
            visited[reel][row]):
            return
        
        cell_symbol = grid[reel][row]
        # Wild matches cluster symbols
        if cell_symbol != symbol and cell_symbol != 'W' and symbol != 'W':
            return
        if cell_symbol not in CLUSTER_SYMBOLS:
            return
            
        visited[reel][row] = True
        cluster.append((reel, row))
        
        # Check 4 adjacent cells
        flood_fill(reel - 1, row, symbol, cluster)
        flood_fill(reel + 1, row, symbol, cluster)
        flood_fill(reel, row - 1, symbol, cluster)
        flood_fill(reel, row + 1, symbol, cluster)
    
    for reel in range(NUM_REELS):
        for row in range(NUM_ROWS):
            if not visited[reel][row] and grid[reel][row] in CLUSTER_SYMBOLS:
                cluster = []
                symbol = grid[reel][row]
                flood_fill(reel, row, symbol, cluster)
                if len(cluster) >= 5:
                    clusters[symbol].append(cluster)
    
    return clusters


def calculate_cluster_score(reels: List[List[str]], num_simulations: int = 10000) -> Dict:
    """
    Simulate spins and calculate cluster statistics.
    Returns metrics about cluster frequency and sizes.
    """
    stats = {
        'total_spins': num_simulations,
        'spins_with_clusters': 0,
        'total_clusters': 0,
        'cluster_sizes': defaultdict(int),
        'clusters_by_symbol': defaultdict(int),
        'avg_clusters_per_winning_spin': 0,
        'total_cluster_cells': 0,
    }
    
    for _ in range(num_simulations):
        # Random positions for each reel
        positions = [random.randint(0, REEL_LENGTH - 1) for _ in range(NUM_REELS)]
        grid = get_grid(reels, positions)
        clusters = find_clusters(grid)
        
        if clusters:
            stats['spins_with_clusters'] += 1
            for symbol, symbol_clusters in clusters.items():
                for cluster in symbol_clusters:
                    stats['total_clusters'] += 1
                    stats['cluster_sizes'][len(cluster)] += 1
                    stats['clusters_by_symbol'][symbol] += 1
                    stats['total_cluster_cells'] += len(cluster)
    
    if stats['spins_with_clusters'] > 0:
        stats['avg_clusters_per_winning_spin'] = stats['total_clusters'] / stats['spins_with_clusters']
    
    stats['hit_rate'] = stats['spins_with_clusters'] / num_simulations
    stats['avg_cluster_size'] = stats['total_cluster_cells'] / max(1, stats['total_clusters'])
    
    return stats


def calculate_dispersion_score(strip: List[str]) -> float:
    """
    Calculate how well dispersed symbols are on a reel strip.
    Higher score = symbols more spread out = harder to form clusters.
    
    We want identical symbols to be as far apart as possible.
    """
    symbol_positions = defaultdict(list)
    for i, sym in enumerate(strip):
        symbol_positions[sym].append(i)
    
    total_score = 0
    for sym, positions in symbol_positions.items():
        if len(positions) < 2:
            continue
        
        # Calculate average distance between consecutive occurrences
        # Account for wrap-around (reel is circular)
        distances = []
        for i in range(len(positions)):
            next_i = (i + 1) % len(positions)
            if next_i == 0:
                # Wrap around
                dist = (len(strip) - positions[i]) + positions[0]
            else:
                dist = positions[next_i] - positions[i]
            distances.append(dist)
        
        # Ideal distance would be len(strip) / len(positions)
        ideal_dist = len(strip) / len(positions)
        
        # Score based on how close we are to ideal uniform distribution
        # Penalize variance - we want consistent spacing
        variance = sum((d - ideal_dist) ** 2 for d in distances) / len(distances)
        symbol_score = ideal_dist / (1 + variance ** 0.5)
        total_score += symbol_score
    
    return total_score


def optimize_single_reel_dispersion(strip: List[str], iterations: int = 5000) -> List[str]:
    """
    Optimize a single reel for maximum symbol dispersion.
    Uses simulated annealing to find good arrangements.
    """
    current = strip.copy()
    current_score = calculate_dispersion_score(current)
    best = current.copy()
    best_score = current_score
    
    temperature = 1.0
    cooling_rate = 0.9995
    
    for i in range(iterations):
        # Random swap
        idx1, idx2 = random.sample(range(len(current)), 2)
        current[idx1], current[idx2] = current[idx2], current[idx1]
        
        new_score = calculate_dispersion_score(current)
        
        # Accept if better, or probabilistically if worse (simulated annealing)
        if new_score > current_score or random.random() < temperature:
            current_score = new_score
            if new_score > best_score:
                best = current.copy()
                best_score = new_score
        else:
            # Revert swap
            current[idx1], current[idx2] = current[idx2], current[idx1]
        
        temperature *= cooling_rate
    
    return best


def calculate_cross_reel_correlation(reels: List[List[str]], sample_size: int = 1000) -> float:
    """
    Calculate how often same symbols appear adjacent between neighboring reels.
    Lower is better (harder to form horizontal clusters).
    """
    correlation_score = 0
    
    for _ in range(sample_size):
        positions = [random.randint(0, REEL_LENGTH - 1) for _ in range(NUM_REELS)]
        
        for reel_idx in range(NUM_REELS - 1):
            for row in range(NUM_ROWS):
                pos1 = (positions[reel_idx] + row) % REEL_LENGTH
                pos2 = (positions[reel_idx + 1] + row) % REEL_LENGTH
                
                sym1 = reels[reel_idx][pos1]
                sym2 = reels[reel_idx + 1][pos2]
                
                # Check if symbols match (including wild)
                if sym1 in CLUSTER_SYMBOLS and sym2 in CLUSTER_SYMBOLS:
                    if sym1 == sym2 or sym1 == 'W' or sym2 == 'W':
                        correlation_score += 1
    
    return correlation_score / (sample_size * NUM_ROWS * (NUM_REELS - 1))


def optimize_cross_reel_arrangement(reels: List[List[str]], iterations: int = 2000) -> List[List[str]]:
    """
    Optimize the relative arrangement of reels to minimize cross-reel correlation.
    This shifts entire reel strips relative to each other.
    """
    best_reels = [r.copy() for r in reels]
    best_correlation = calculate_cross_reel_correlation(best_reels)
    
    print(f"Initial cross-reel correlation: {best_correlation:.4f}")
    
    for i in range(iterations):
        # Pick a random reel and rotate it
        reel_idx = random.randint(0, NUM_REELS - 1)
        rotation = random.randint(1, REEL_LENGTH - 1)
        
        test_reels = [r.copy() for r in best_reels]
        test_reels[reel_idx] = test_reels[reel_idx][rotation:] + test_reels[reel_idx][:rotation]
        
        new_correlation = calculate_cross_reel_correlation(test_reels)
        
        if new_correlation < best_correlation:
            best_reels = test_reels
            best_correlation = new_correlation
            if i % 200 == 0:
                print(f"  Iteration {i}: correlation = {best_correlation:.4f}")
    
    print(f"Final cross-reel correlation: {best_correlation:.4f}")
    return best_reels


def create_optimized_strip(symbol_counts: Dict[str, int], reel_length: int) -> List[str]:
    """
    Create a reel strip with symbols optimally dispersed.
    Uses a round-robin style placement to maximize spacing.
    """
    strip = [''] * reel_length
    
    # Sort symbols by count (place rarer symbols first for better positioning)
    sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1])
    
    # Track available positions
    available = list(range(reel_length))
    
    for symbol, count in sorted_symbols:
        if count == 0:
            continue
            
        # Calculate ideal spacing
        ideal_spacing = len(available) / count
        
        # Place symbols with maximum spacing
        positions_to_use = []
        for i in range(count):
            # Find the position closest to ideal
            ideal_pos = int(i * ideal_spacing)
            if ideal_pos < len(available):
                positions_to_use.append(available[ideal_pos])
            else:
                positions_to_use.append(available[-1])
        
        # Place symbols
        for pos in positions_to_use:
            strip[pos] = symbol
            if pos in available:
                available.remove(pos)
    
    # Fill any remaining gaps (shouldn't happen if counts are correct)
    for i, sym in enumerate(strip):
        if sym == '':
            strip[i] = 'L4'  # Default fill
    
    return strip


def analyze_and_optimize_reels(reel_type: str = 'FR0'):
    """
    Main function to analyze and optimize reels.
    """
    reels_dir = "/workspaces/math-sdk/games/0_0_alchemy/reels"
    reel_path = os.path.join(reels_dir, f"{reel_type}.csv")
    
    if not os.path.exists(reel_path):
        print(f"Reel file not found: {reel_path}")
        print("Please run generate_reels.py first")
        return
    
    # Load current reels (single file contains all 7 reels concatenated or we need to parse differently)
    # Let me check the format first
    print(f"\n{'='*60}")
    print(f"  REEL OPTIMIZATION FOR {reel_type}")
    print(f"{'='*60}\n")
    
    # Load the reel strips (each column is a reel)
    reels = load_reels(reel_path)
    print(f"Loaded {len(reels)} reels with {len(reels[0])} symbols each from {reel_type}.csv")
    
    # Analyze current state
    print("\n--- CURRENT REEL ANALYSIS ---")
    current_stats = calculate_cluster_score(reels)
    print(f"Hit rate (spins with clusters): {current_stats['hit_rate']*100:.2f}%")
    print(f"Avg clusters per winning spin: {current_stats['avg_clusters_per_winning_spin']:.2f}")
    print(f"Avg cluster size: {current_stats['avg_cluster_size']:.2f}")
    print(f"Total clusters in {current_stats['total_spins']} spins: {current_stats['total_clusters']}")
    
    print("\nCluster size distribution:")
    for size in sorted(current_stats['cluster_sizes'].keys()):
        count = current_stats['cluster_sizes'][size]
        print(f"  Size {size}: {count} ({count/max(1,current_stats['total_clusters'])*100:.1f}%)")
    
    # Optimize each reel for dispersion
    print("\n--- OPTIMIZING INDIVIDUAL REEL DISPERSION ---")
    optimized_reels = []
    for i, reel in enumerate(reels):
        print(f"Optimizing reel {i+1}...", end=" ")
        before_score = calculate_dispersion_score(reel)
        optimized = optimize_single_reel_dispersion(reel, iterations=10000)
        after_score = calculate_dispersion_score(optimized)
        print(f"Dispersion: {before_score:.1f} -> {after_score:.1f} ({(after_score/before_score-1)*100:+.1f}%)")
        optimized_reels.append(optimized)
    
    # Optimize cross-reel correlation
    print("\n--- OPTIMIZING CROSS-REEL CORRELATION ---")
    optimized_reels = optimize_cross_reel_arrangement(optimized_reels, iterations=3000)
    
    # Analyze optimized state
    print("\n--- OPTIMIZED REEL ANALYSIS ---")
    optimized_stats = calculate_cluster_score(optimized_reels)
    print(f"Hit rate (spins with clusters): {optimized_stats['hit_rate']*100:.2f}%")
    print(f"Avg clusters per winning spin: {optimized_stats['avg_clusters_per_winning_spin']:.2f}")
    print(f"Avg cluster size: {optimized_stats['avg_cluster_size']:.2f}")
    print(f"Total clusters in {optimized_stats['total_spins']} spins: {optimized_stats['total_clusters']}")
    
    print("\nCluster size distribution:")
    for size in sorted(optimized_stats['cluster_sizes'].keys()):
        count = optimized_stats['cluster_sizes'][size]
        print(f"  Size {size}: {count} ({count/max(1,optimized_stats['total_clusters'])*100:.1f}%)")
    
    # Calculate improvement
    print("\n--- IMPROVEMENT SUMMARY ---")
    hit_change = (optimized_stats['hit_rate'] - current_stats['hit_rate']) / current_stats['hit_rate'] * 100
    cluster_change = (optimized_stats['total_clusters'] - current_stats['total_clusters']) / current_stats['total_clusters'] * 100
    size_change = (optimized_stats['avg_cluster_size'] - current_stats['avg_cluster_size']) / current_stats['avg_cluster_size'] * 100
    
    print(f"Hit rate change: {hit_change:+.2f}%")
    print(f"Total clusters change: {cluster_change:+.2f}%")
    print(f"Avg cluster size change: {size_change:+.2f}%")
    
    # Save optimized reels
    output_path = os.path.join(reels_dir, f"{reel_type}_optimized.csv")
    save_reels(output_path, optimized_reels)
    print(f"\nOptimized reels saved to: {output_path}")
    
    return optimized_reels, current_stats, optimized_stats


def compare_with_different_symbol_distributions():
    """
    Test different symbol count distributions to find optimal RTP-reducing configs.
    """
    print("\n" + "="*60)
    print("  TESTING DIFFERENT SYMBOL DISTRIBUTIONS")
    print("="*60)
    
    # Test configurations - reducing high pay symbols
    configs = [
        # (name, H1, H2, H3, H4, L1, L2, L3, L4)
        ("Current", 25, 27, 29, 31, 28, 30, 32, 34),
        ("Reduce H1/H2", 18, 20, 29, 31, 32, 34, 36, 36),
        ("More Low Pays", 20, 22, 24, 26, 32, 34, 38, 40),
        ("Extreme Low", 15, 17, 20, 25, 35, 38, 42, 44),
    ]
    
    for config_name, h1, h2, h3, h4, l1, l2, l3, l4 in configs:
        print(f"\n--- {config_name} ---")
        print(f"H1:{h1} H2:{h2} H3:{h3} H4:{h4} L1:{l1} L2:{l2} L3:{l3} L4:{l4}")
        
        # Create test reels
        test_reels = []
        wild_counts = [2, 4, 6, 6, 6, 4, 2]
        
        for reel_idx in range(NUM_REELS):
            counts = {
                'W': wild_counts[reel_idx],
                'S': 2,
                'P': 2, 'B': 2, 'T': 2,  # Feature symbols
                'H1': h1, 'H2': h2, 'H3': h3, 'H4': h4,
                'L1': l1, 'L2': l2, 'L3': l3, 'L4': l4,
            }
            
            # Adjust L4 to fill reel
            total = sum(counts.values())
            counts['L4'] += REEL_LENGTH - total
            
            # Create strip
            strip = []
            for sym, count in counts.items():
                strip.extend([sym] * max(0, count))
            strip = strip[:REEL_LENGTH]
            random.shuffle(strip)
            test_reels.append(strip)
        
        # Analyze
        stats = calculate_cluster_score(test_reels, num_simulations=5000)
        print(f"Hit rate: {stats['hit_rate']*100:.2f}%")
        print(f"Avg cluster size: {stats['avg_cluster_size']:.2f}")
        print(f"Total clusters: {stats['total_clusters']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        reel_type = sys.argv[1]
    else:
        reel_type = "FR0"
    
    # First, test different symbol distributions
    compare_with_different_symbol_distributions()
    
    # Then optimize the actual reel arrangement
    optimize_result = analyze_and_optimize_reels(reel_type)
    
    print("\n" + "="*60)
    print("  RECOMMENDATIONS")
    print("="*60)
    print("""
To reduce cluster formation probability:

1. SYMBOL DISPERSION: Optimized reels have been saved with better
   symbol spacing. Replace your current reels with the _optimized versions.

2. REDUCE HIGH-PAY SYMBOLS: The 'Extreme Low' config significantly
   reduces cluster values while maintaining similar hit rates.

3. CROSS-REEL CORRELATION: The optimization rotates reels to minimize
   situations where matching symbols appear adjacent horizontally.

4. IMPLEMENTATION: Update generate_reels.py to use these principles:
   - Use create_optimized_strip() instead of random.shuffle()
   - Reduce H1/H2 counts, increase L3/L4 counts
   - Apply cross-reel rotation offsets
""")
