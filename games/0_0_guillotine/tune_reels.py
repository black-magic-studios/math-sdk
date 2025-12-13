import csv
import random
import os

def generate_reel_strip(length, weights):
    strip = []
    # Create a population list for weighted choice
    population = []
    for sym, weight in weights.items():
        population.extend([sym] * int(weight))
    
    for _ in range(length):
        strip.append(random.choice(population))
    return strip

def save_reels(filename, reels_data):
    # reels_data is list of lists [[r1...], [r2...]]
    # Transpose to rows for CSV format (Reel 1, Reel 2, ...)
    rows = []
    max_len = max(len(r) for r in reels_data)
    for i in range(max_len):
        row = []
        for r in reels_data:
            row.append(r[i % len(r)])
        rows.append(row)
    
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        # NO HEADER for this SDK
        # writer.writerow([f"Reel {i+1}" for i in range(len(reels_data))])
        writer.writerows(rows)

# ---------------------------------------------------------
# FS3 CONFIGURATION (Target: 96x Session Win)
# ---------------------------------------------------------
# Interpolated: G=9% should hit ~96x.
fs3_weights = {
    "H1": 6, "H2": 6, "H3": 6, "H4": 6, "H5": 6,
    "L1": 12, "L2": 12, "L3": 12, "L4": 12, "L5": 12,
    "S": 2, "G": 9
}

# ---------------------------------------------------------
# FS4 CONFIGURATION (Target: 400x Session Win)
# ---------------------------------------------------------
# Interpolated: G=11.5% should hit ~400x.
fs4_weights = {
    "H1": 8, "H2": 8, "H3": 8, "H4": 8, "H5": 8,
    "L1": 10, "L2": 10, "L3": 10, "L4": 10, "L5": 10,
    "S": 2, "G": 11.5
}

# ---------------------------------------------------------
# FS5 CONFIGURATION (Target: 2000x Session Win)
# ---------------------------------------------------------
# Interpolated: G=18.5% should hit ~2000x.
fs5_weights = {
    "H1": 5, "H2": 5, "H3": 5, "H4": 5, "H5": 5,
    "L1": 13, "L2": 13, "L3": 13, "L4": 13, "L5": 13,
    "S": 2, "G": 18.5
}

def generate_and_save(weights, filename):
    reels = []
    for i in range(5):
        reels.append(generate_reel_strip(200, weights))
    save_reels(filename, reels)
    print(f"Generated {filename}")

generate_and_save(fs3_weights, "/workspaces/math-sdk/games/0_0_guillotine/reels/FR0.csv")
generate_and_save(fs4_weights, "/workspaces/math-sdk/games/0_0_guillotine/reels/FR4.csv")
generate_and_save(fs5_weights, "/workspaces/math-sdk/games/0_0_guillotine/reels/FR5.csv")

