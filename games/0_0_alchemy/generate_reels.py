"""
Reel generator for Alchemy game.
7 reels x 7 rows cluster game with tumbling mechanics.

Symbols:
- H1, H2, H3, H4: High pay symbols
- L1, L2, L3, L4: Low pay symbols  
- W: Wild (substitutes for all except scatter)
- S: Scatter (4+ triggers freespins in base, 3+ in freegame)
- P: Potion (adds 1-5 wilds when tumbles end)
- B: Bomb (explodes in radius, boosts grid multipliers when tumbles end)
- T: Transform (upgrades random low-pay symbol type to H1)

Cluster wins require 5+ adjacent matching symbols.
Feature symbols (P, B, T) trigger their effects after all tumbles end.
They can create new wins which trigger more tumbles.

OPTIMIZATION: Uses dispersed symbol placement instead of random shuffle.
This makes cluster formation harder by spreading identical symbols evenly
across each reel strip, reducing the probability of adjacent matches.
"""

import csv
import random
import os
from collections import defaultdict

# Configuration
NUM_REELS = 7
REEL_LENGTH = 252  # Match existing reel length
OUTPUT_DIR = "/workspaces/math-sdk/games/0_0_alchemy/reels"

# Dispersion strength: 0.0 = fully random, 1.0 = fully dispersed
# 0.5 is a good middle ground for balanced RTP
DISPERSION_STRENGTH = 0.5


def create_dispersed_strip(counts: dict, reel_length: int, dispersion: float = None) -> list:
    """
    Create a reel strip with partial symbol dispersion.
    
    dispersion parameter (0.0 to 1.0):
    - 0.0 = fully random (original behavior)
    - 0.5 = half dispersed, half random (balanced)
    - 1.0 = fully dispersed (hardest clusters)
    """
    if dispersion is None:
        dispersion = DISPERSION_STRENGTH
    
    # Build the full symbol list
    all_symbols = []
    for symbol, count in counts.items():
        all_symbols.extend([symbol] * count)
    
    # If no dispersion, just shuffle
    if dispersion <= 0:
        random.shuffle(all_symbols)
        return all_symbols[:reel_length]
    
    # Split symbols: some get dispersed, some get shuffled
    # Higher dispersion = more symbols get dispersed placement
    dispersed_portion = int(len(all_symbols) * dispersion)
    
    strip = [''] * reel_length
    available = set(range(reel_length))
    
    # Sort symbols by count (disperse rare symbols first)
    sorted_symbols = sorted(counts.items(), key=lambda x: x[1])
    
    symbols_placed = 0
    for symbol, count in sorted_symbols:
        if count == 0:
            continue
        
        # How many of this symbol to disperse vs random
        to_disperse = int(count * dispersion)
        to_random = count - to_disperse
        
        if to_disperse > 0 and available:
            # Calculate ideal spacing for dispersed symbols
            ideal_spacing = reel_length / to_disperse if to_disperse > 0 else reel_length
            offset = random.randint(0, max(1, int(ideal_spacing) - 1))
            
            for i in range(to_disperse):
                if not available:
                    break
                target = int(offset + i * ideal_spacing) % reel_length
                
                # Find nearest available position
                best_pos = min(available, key=lambda p: min(abs(p - target), reel_length - abs(p - target)))
                strip[best_pos] = symbol
                available.discard(best_pos)
                symbols_placed += 1
        
        # Remaining symbols will be placed randomly later
        for _ in range(to_random):
            if available:
                pos = random.choice(list(available))
                strip[pos] = symbol
                available.discard(pos)
                symbols_placed += 1
    
    # Fill any gaps
    for i, sym in enumerate(strip):
        if sym == '':
            strip[i] = 'L4'
    
    return strip


def create_base_reel(reel_idx):
    """
    BR0: Base Game Reel
    - Scatters distributed for near-miss excitement (3 scatters common, 4+ rare)
    - No wilds in base game
    - Feature symbols (P, B, T) appear rarely in base - maybe 1 per spin on average
    - Balanced symbol distribution for cluster formation
    """
    # Base symbol counts per reel - targeting 1 in ~203 spins for bonus trigger
    # Configuration [8,7,6,4,4,2,2] gives ~1 in 203 trigger rate
    # Left-weighted distribution with scatters on all reels for unpredictability
    scatter_counts = [8, 7, 6, 4, 4, 2, 2]  # Total 33 scatters across all 7 reels
    
    # Feature symbols - sparse in base game
    # We want features to trigger occasionally, not every spin
    potion_counts = [0, 1, 1, 1, 1, 1, 0]     # 5 potions total
    bomb_counts = [0, 1, 1, 1, 1, 1, 0]        # 5 bombs total
    transform_counts = [0, 1, 1, 1, 1, 1, 0]   # 5 transforms total
    
    counts = {
        'S': scatter_counts[reel_idx],
        'P': potion_counts[reel_idx],
        'B': bomb_counts[reel_idx],
        'T': transform_counts[reel_idx],
        'H1': 20,
        'H2': 22,
        'H3': 24,
        'H4': 26,
        'L1': 28,
        'L2': 30,
        'L3': 32,
        'L4': 34,
    }
    
    # Adjust to fill reel length
    total = sum(counts.values())
    remaining = REEL_LENGTH - total
    counts['L4'] += remaining
    
    # Use dispersed placement instead of random shuffle for harder cluster formation
    strip = create_dispersed_strip(counts, REEL_LENGTH)
    return strip


def create_freespin_reel(reel_idx):
    """
    FR0: Free Spin Reel
    - Reduced wilds to control RTP
    - Scatters for retriggers (3+ needed)
    - Feature symbols for excitement
    - Uses partial dispersion for balanced cluster formation
    """
    # Significantly reduced wilds - main RTP lever
    wild_counts = [1, 2, 3, 3, 3, 2, 1]  # Total 15 wilds (was 40)
    scatter_counts = [2, 2, 2, 2, 2, 2, 2]  # Consistent for retriggers
    
    # Feature symbols - keep them active but not overwhelming
    potion_counts = [0, 1, 1, 1, 1, 1, 0]     # Total 5 potions (reduced)
    bomb_counts = [0, 1, 1, 1, 1, 1, 0]        # Total 5 bombs (reduced)
    transform_counts = [0, 1, 1, 1, 1, 1, 0]   # Total 5 transforms (reduced)
    
    counts = {
        'S': scatter_counts[reel_idx],
        'W': wild_counts[reel_idx],
        'P': potion_counts[reel_idx],
        'B': bomb_counts[reel_idx],
        'T': transform_counts[reel_idx],
        'H1': 20,
        'H2': 22,
        'H3': 24,
        'H4': 26,
        'L1': 28,
        'L2': 30,
        'L3': 32,
        'L4': 36,
    }
    
    # Adjust to fill reel length
    total = sum(counts.values())
    remaining = REEL_LENGTH - total
    if remaining > 0:
        counts['L4'] += remaining
    elif remaining < 0:
        counts['L4'] = max(0, counts['L4'] + remaining)
    
    # Use moderate dispersion (0.4) - balanced cluster formation
    strip = create_dispersed_strip(counts, REEL_LENGTH, dispersion=0.4)
    return strip


def create_wincap_reel(reel_idx):
    """
    WCAP: Win Cap Reel (high volatility for max wins)
    - Heavy wild concentration
    - More high-pay symbols
    - Many feature symbols for chain reactions
    - Designed for potential 5000x wins
    """
    # Very high wild counts for massive clusters
    wild_counts = [15, 25, 35, 35, 35, 25, 15]
    
    # Moderate feature symbols for wincap
    potion_counts = [2, 3, 4, 4, 4, 3, 2]     # Total 22 potions
    bomb_counts = [2, 2, 3, 3, 3, 2, 2]        # Total 17 bombs
    transform_counts = [2, 2, 3, 3, 3, 2, 2]   # Total 17 transforms
    
    counts = {
        'S': 3,
        'W': wild_counts[reel_idx],
        'P': potion_counts[reel_idx],
        'B': bomb_counts[reel_idx],
        'T': transform_counts[reel_idx],
        'H1': 35,  # Heavy H1 for max wins
        'H2': 30,
        'H3': 25,
        'H4': 20,
        'L1': 20,
        'L2': 22,
        'L3': 24,
        'L4': 26,
    }
    
    # Adjust to fill reel length
    total = sum(counts.values())
    remaining = REEL_LENGTH - total
    if remaining > 0:
        counts['L4'] += remaining
    elif remaining < 0:
        counts['H1'] = max(0, counts['H1'] + remaining)
    
    # WCAP uses random shuffle - we WANT clusters here for big wins
    strip = []
    for sym, count in counts.items():
        strip.extend([sym] * count)
    strip = strip[:REEL_LENGTH]
    random.shuffle(strip)
    return strip


def create_near_miss_base_reel(reel_idx):
    """
    BR0_NM: Enhanced Near Miss Base Reel
    - More scatters but positioned for 3-scatter outcomes
    - Symbol stacking for 4-cluster near misses
    """
    strip = []
    
    # Higher scatter count but uneven distribution
    # Odd reels have more, even reels have fewer = frequent 3-scatter
    scatter_counts = [4, 1, 4, 1, 4, 1, 4]  # Total 19, but rarely 4+ align
    
    counts = {
        'S': scatter_counts[reel_idx],
        'H1': 22,
        'H2': 24,
        'H3': 26,
        'H4': 28,
        'L1': 30,
        'L2': 32,
        'L3': 34,
        'L4': 36,
    }
    
    # Adjust to fill reel length
    total = sum(counts.values())
    remaining = REEL_LENGTH - total
    counts['L4'] += remaining
    
    for sym, count in counts.items():
        strip.extend([sym] * count)
    
    strip = strip[:REEL_LENGTH]
    random.shuffle(strip)
    return strip


def write_reel_file(filename, creator_func):
    """Write reel data to CSV file (7 reels as columns)."""
    reels = [creator_func(i) for i in range(NUM_REELS)]
    
    # Transpose to rows (each row has 7 symbols, one per reel)
    rows = []
    for i in range(REEL_LENGTH):
        row = [reels[j][i] for j in range(NUM_REELS)]
        rows.append(row)
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Generated {filepath}")


def print_symbol_stats(creator_func, name):
    """Print symbol distribution stats for a reel set."""
    print(f"\n=== {name} Symbol Distribution ===")
    total_counts = {}
    
    for reel_idx in range(NUM_REELS):
        reel = creator_func(reel_idx)
        print(f"Reel {reel_idx + 1}: ", end="")
        reel_counts = {}
        for sym in reel:
            reel_counts[sym] = reel_counts.get(sym, 0) + 1
            total_counts[sym] = total_counts.get(sym, 0) + 1
        
        # Show scatter, wild, and feature counts
        s_count = reel_counts.get('S', 0)
        w_count = reel_counts.get('W', 0)
        p_count = reel_counts.get('P', 0)
        b_count = reel_counts.get('B', 0)
        t_count = reel_counts.get('T', 0)
        print(f"S={s_count}, W={w_count}, P={p_count}, B={b_count}, T={t_count}")
    
    print("\nTotal across all reels:")
    for sym in sorted(total_counts.keys()):
        print(f"  {sym}: {total_counts[sym]}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate standard reels
    write_reel_file("BR0.csv", create_base_reel)
    write_reel_file("FR0.csv", create_freespin_reel)
    write_reel_file("WCAP.csv", create_wincap_reel)
    
    # Optionally generate near-miss variant
    # write_reel_file("BR0_NM.csv", create_near_miss_base_reel)
    
    # Print stats
    print_symbol_stats(create_base_reel, "BR0 (Base Game)")
    print_symbol_stats(create_freespin_reel, "FR0 (Free Spins)")
    print_symbol_stats(create_wincap_reel, "WCAP (Win Cap)")
